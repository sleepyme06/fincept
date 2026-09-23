import json
import os
import re
from .utils import DID_YOU_MEAN

MEMORY_PATH = "memory.json"

def _load():
    if not os.path.exists(MEMORY_PATH):
        return []
    with open(MEMORY_PATH, "r") as f:
        return json.load(f)

def _save(entries):
    with open(MEMORY_PATH, "w") as f:
        json.dump(entries, f, indent=2)

MAX_ENTRIES = 20

def add_reflection(tool_name, args, reason,result=""):
    entries = _load()
    action_key = f"{tool_name}:{sorted(args.items())}"

    entries = [e for e in entries if e["action_key"] != action_key]
    entries.append({
        "action_key": action_key,
        "reason": reason,
        "result":result[:200],
    })

    if len(entries) > MAX_ENTRIES:
        entries = entries[-MAX_ENTRIES:]

    _save(entries)

def extract_suggestion(result):
    match = re.search(rf"no such file.*{DID_YOU_MEAN} '([^']+)'", result)
    return match.group(1) if match else None

# could instead filter to reflections matching the current action/tool being attempted
def get_reflections(limit=5, tool_name=None):
    entries = _load()
    if tool_name:
        matched = [e for e in entries if e["action_key"].startswith(f"{tool_name}:")]
        if matched:
            return matched[-limit:]
    return entries[-limit:]

# Without it: your rewind message only warns the current run — info is lost once the process ends.
# With it: failures persist across runs/tasks, so next time the agent hits a similar action, it sees "this failed before, here's why."