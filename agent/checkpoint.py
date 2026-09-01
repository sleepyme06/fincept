import os
import json

CHECKPOINT_DIR = "checkpoints"
def save_checkpt(state, checkpoint_id):
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    path = f"{CHECKPOINT_DIR}/checkpoint_{checkpoint_id}.json"
    with open(path, "w") as f:
        json.dump(state, f, indent=2)
    return path


def load_checkpt(checkpoint_id):
    path = f"{CHECKPOINT_DIR}/checkpoint_{checkpoint_id}.json"
    if not os.path.exists(path):
        return f"ERROR: no checkpoint found at '{path}'"
    with open(path) as f:
        return json.load(f)