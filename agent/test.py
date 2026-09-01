from tools import FAKE_FS
from agent import run_agent
from checkpoint import load_checkpt   # jahan bhi tumne save/load functions rakhe hain

checkpoint_id = 2  # jo bhi step tak agent chal chuka tha
state = load_checkpt(checkpoint_id)

# restore conversation history
message = state["messages"]
action_history = state["action_history"]

# restore fake filesystem
FAKE_FS.clear()
FAKE_FS.update(state["file_sys"])

n = state["step"]
print(f"Resumed from step {n}")

# ab agent ko naya instruction do — dekho purani history use karta hai ya nahi
message.append({"role": "user", "content": "ab data/sample.csv padho"})
reply = run_agent(message)
print(f"\nAgent: {reply}")