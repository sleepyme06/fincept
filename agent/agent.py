import os
from pathlib import Path
from time import sleep
from .utils import call_llm_with_retry
from dotenv import load_dotenv
from groq import Groq,RateLimitError, BadRequestError
from .tools import TOOLS,TOOL_SCHEMAS,list_files,FAKE_FS
import json
import copy
from .checkpoint import save_checkpt,load_checkpt
from .signals import get_action_key, repetition_score,drift_score,update_failure_streak, confidence_score,log_signals,should_rewind

load_dotenv()
 
apikey=os.getenv("GROQ_API_KEY")
if not apikey:
    raise ValueError("api key bana le bhaii!!")
 
client=Groq(api_key=apikey)
model="qwen/qwen3.6-27b"

SYSTEM_PROMPT="""
You are a coding agent running in the user's terminal.

You have four tools available:
- list_files(path)
- read_file(path)
- write_file(path, content)
- run_command(command)

Use them when needed.
"""
 
def run_tools(name,args):
    # grab actual name of tool and parse it from sting to actual fxn
    # name=tool_call.function.name
    # args=json.loads(tool_call.function.arguments)
    print(f"tool:{name}({args})")
    try:
        return str(TOOLS[name](**args))
    except Exception as error:
        return f"ERROR:{error}"

def serialize_messages(message):
    safe = []
    for m in message:
        item = dict(m)
        tool_calls = item.get("tool_calls")
        if tool_calls:
            normalized = []
            for tc in tool_calls:
                if isinstance(tc, dict):
                    fn = tc.get("function") or {}
                    normalized.append({
                        "id": tc.get("id"),
                        "type": tc.get("type"),
                        "function": {
                            "name": fn.get("name"),
                            "arguments": fn.get("arguments"),
                        },
                    })
                else:
                    normalized.append({
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    })
            item["tool_calls"] = normalized
        safe.append(item)

    return safe

MAX_REWINDS = 3
# one run one effective user prompt
def run_agent(message,action_history, starting_step=0, starting_failure_streak=0):
    step_count=starting_step
    failure_streak = starting_failure_streak
    rewind_count = 0
    while True:

        response=call_llm_with_retry(client=client,messages=message,model=model,tools=TOOL_SCHEMAS,tool_choice="auto",)
        ans=response.choices[0].message
        message.append(
            {
                "role": "assistant",
                "content": ans.content,
                **({"tool_calls": ans.tool_calls} if ans.tool_calls else {}),
            }
        )

        # if no tool call just return the message
        if not ans.tool_calls:
            return ans.content
        
        rewound_this_turn = False

        for tool_call in ans.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            action_history.append(get_action_key(name, args))
            score = repetition_score(action_history)
            print(f"[signal] repetition_score = {score:.2f}")

            result=run_tools(name,args)
            d_score = drift_score(name,args,result)
            print(f"[signal] drift_score = {d_score:.2f}")

            passed = "error" not in result.lower()
            failure_streak = update_failure_streak(failure_streak, passed)
            print(f"[signal] failure_streak = {failure_streak}")

            # 3d
            c_score = confidence_score(failure_streak,score)
            print(f"[signal] confidence_score = {c_score:.2f}")

            message.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })
            step_count+=1
            log_signals(step_count, score, d_score, failure_streak, c_score)
            rewind_flag = should_rewind(score, d_score, failure_streak, c_score)
            print(f"[signal] should_rewind = {rewind_flag}")

            state={
                "messages":serialize_messages(message),
                "file_sys":copy.deepcopy(FAKE_FS),
                "step":step_count,
                "action_history": action_history,
                "failure_streak": failure_streak, 
            }
            save_checkpt(state,step_count)
            if rewind_flag:
                if rewind_count >= MAX_REWINDS:
                    print(f"[rewind] limit reached ({MAX_REWINDS}), not rewinding again this task")
                    continue

                rewind_step = step_count - 1
                if rewind_step < 1:
                    print("[rewind] no earlier checkpoint exists, cannot rewind")
                    continue

                restored = load_checkpt(rewind_step)
                if isinstance(restored, str) and restored.startswith("ERROR"):
                    print(f"[rewind] could not load checkpoint {rewind_step}: {restored}")
                    continue

                reason = (
                    f"repetition={score:.2f}, drift={d_score:.2f}, "
                    f"failure_streak={failure_streak}, confidence={c_score:.2f}"
                )
                print(f"[rewind] triggered at step {step_count} -> restoring step {rewind_step}. Reason: {reason}")

                FAKE_FS.clear()
                FAKE_FS.update(restored["file_sys"])

                message.clear()
                message.extend(restored["messages"])
                message.append({
                    "role": "user",
                    "content": (
                        f"Your previous approach (attempting {name}({args})) triggered a "
                        f"rewind due to: {reason}. Try a different approach instead."
                    )
                })

                action_history[:] = restored["action_history"]
                failure_streak = restored["failure_streak"]
                step_count = restored["step"]
                rewind_count += 1

                rewound_this_turn = True
                break

        if rewound_this_turn:
            continue          




# if __name__== "__main__":
#     message = [{"role": "system", "content": SYSTEM_PROMPT}]
#     action_history=[]
#     print("Mini agent ready. Type 'exit' to quit.")
#     while True:
#         user=input("you:")
#         if user.strip().lower()in ('exit','quit'):
#             break
#         message.append({"role": "user", "content": user})
#         reply = run_agent(message,action_history)
#         print(f"\nAgent: {reply}")