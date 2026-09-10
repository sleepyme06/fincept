from agent.agent import run_agent, SYSTEM_PROMPT

if __name__ == "__main__":
    message = [{"role": "system", "content": SYSTEM_PROMPT}]
    action_history = []
    pass_his=[]
    print("Mini agent ready. Type 'exit' to quit.")
    while True:
        user = input("you:")
        if user.strip().lower() in ('exit', 'quit'):
            break
        message.append({"role": "user", "content": user})
        reply = run_agent(message, action_history,pass_his)
        print(f"\nAgent: {reply}")