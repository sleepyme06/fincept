from agent.agent import run_agent, SYSTEM_PROMPT

# DEMO_PROMPT = (
#     "Read config.txt. If that fails, try reading configuration.txt. "
#     "If that also fails, try settings.txt. If none of those exist, try config.json."
# )
DEMO_PROMPT = (
    "Call read_file('config.txt'). Then call read_file('configuration.txt'). "
    "Then call read_file('notas.txt'). Do not use list_files or any other tool — "
    "only these three read_file calls, in this exact order, without stopping to ask me anything. "
    "After the third call, read whatever file the error message suggests."
)

if __name__ == "__main__":
    print(f"\nTask given to agent:\n  \"{DEMO_PROMPT}\"\n")
    print("None of these files exist in the fake filesystem, so the agent")
    print("will fail repeatedly. Watch for '[rewind] triggered' below --")
    print("that's the cheap-signal trigger firing on failure_streak, and")
    print("the agent's next tool calls should look different afterward.\n")

    message = [{"role": "system", "content": SYSTEM_PROMPT}]
    action_history = []
    pass_his=[]
    message.append({"role": "user", "content": DEMO_PROMPT})

    reply = run_agent(message, action_history,pass_his)
    print(f"\nFinal agent reply:\n{reply}\n")
