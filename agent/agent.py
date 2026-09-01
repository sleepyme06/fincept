import os
from pathlib import Path
from time import sleep
from dotenv import load_dotenv
from groq import Groq
from tools import TOOLS,TOOL_SCHEMAS,list_files,FAKE_FS
import json
import copy
from checkpoint import save_checkpt,load_checkpt
from signals import get_action_key, repetition_score,drift_score,update_failure_streak, confidence_score,log_signals

load_dotenv()
 
apikey=os.getenv("GROQ_API_KEY")
if not apikey:
    raise ValueError("api key bana le bhaii!!")
 
client=Groq(api_key=apikey)
model="qwen/qwen3.6-27b"

SYSTEM_PROMPT=""""
You are a coding agent running in the user's terminal.

You have four tools available:
- list_files(path)
- read_file(path)
- write_file(path, content)
- run_command(command)

Use them when needed.
"""
n=0
failure_streak = 0   


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
            if not tool_calls:
                item.pop("tool_calls", None)
        safe.append(item)

    return safe

# one run one effective user prompt
def run_agent(message,action_history):
    global n,failure_streak
    while True:

        response= client.chat.completions.create(messages=message,model=model,tools=TOOL_SCHEMAS,tool_choice="auto",)
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
        
        for tool_call in ans.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            action_history.append(get_action_key(name, args))
            score = repetition_score(action_history)
            print(f"[signal] repetition_score = {score:.2f}")

            expected_resp = client.chat.completions.create(
            model=model,
            messages=[{
                "role": "user",
                "content": f"An agent is about to run: {name}({args}). "
                        f"In 1-2 short sentences, describe what the resulting "
                        f"observation/output should look like."
            }],
            )
            expected_text = expected_resp.choices[0].message.content

            result=run_tools(name,args)
            d_score = drift_score(expected_text, result)
            print(f"[signal] drift_score = {d_score:.2f}")

            passed = "ERROR" not in result
            failure_streak = update_failure_streak(failure_streak, passed)
            print(f"[signal] failure_streak = {failure_streak}")

            # 3d
            c_score = confidence_score(client, model, name, args, result)
            print(f"[signal] confidence_score = {c_score:.2f}")

            message.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })
            n+=1
            log_signals(n, score, d_score, failure_streak, c_score)
            state={
                "messages":serialize_messages(message),
                "file_sys":copy.deepcopy(FAKE_FS),
                "step":n,
                "action_history": action_history,
                "failure_streak": failure_streak, 
            }
            save_checkpt(state,n)




if __name__== "__main__":
    message = [{"role": "system", "content": SYSTEM_PROMPT}]
    action_history=[]
    print("Mini agent ready. Type 'exit' to quit.")
    while True:
        user=input("you:")
        if user.strip().lower()in ('exit','quite'):
            break
        message.append({"role": "user", "content": user})
        reply = run_agent(message,action_history)
        print(f"\nAgent: {reply}")