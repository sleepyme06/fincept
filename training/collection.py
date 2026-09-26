import json
import os
import glob

CHECKPOINT_DIR = "../checkpoints"
OUTPUT_FILE = "sft_data.jsonl"

def load_checkpoint(path):
    with open(path) as f:
        return json.load(f)

def main():
    files = sorted(
        glob.glob(f"{CHECKPOINT_DIR}/checkpoint_*.json"),
        key=lambda p: int(p.split("_")[-1].split(".")[0])
    )
    print(f"Found {len(files)} checkpoint files: {files}")
    examples = []
    prev_len = 0

    for path in files:
        data = load_checkpoint(path)
        messages = data["messages"]
        pass_his = data.get("pass_his", [])

        # only take steps that succeeded
        if pass_his and not pass_his[-1]:
            prev_len = len(messages)
            continue

        # new messages added since last checkpoint = this step's turn
        new_msgs = messages[prev_len:]
        if len(new_msgs) >= 2:  # need at least assistant + tool msg
            input_msgs = messages[:prev_len] if prev_len > 0 else messages[:1]
            assistant_msg = next((m for m in new_msgs if m["role"] == "assistant"), None)
            if assistant_msg:
                examples.append({
                    "messages": input_msgs + [assistant_msg]
                })

        prev_len = len(messages)

    with open(OUTPUT_FILE, "w") as f:
        for ex in examples:
            f.write(json.dumps(ex) + "\n")

    print(f"Wrote {len(examples)} examples to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()