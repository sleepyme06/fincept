import os
from .utils import DID_YOU_MEAN
import difflib
import re
import json
# ---------------------------------------------------------------------------
# Fully fake, in-memory environment.
# Nothing here ever touches your real disk or runs a real shell command.
# Use this to test your agent loop (tool-calling, message formatting, etc.)
# in isolation.
# ---------------------------------------------------------------------------

# Fake filesystem: path -> file contents (str) or None for a directory marker
FAKE_FS = {
    ".": None,
    "./notes.txt": "This is a dummy file for testing.\n",
    "./data/": None,
    "./data/sample.csv": "id,value\n1,10\n2,20\n",
}
STATS_PATH = "suggestion_stats.json"
DEFAULT_CUTOFF = 0.4

def _load_stats():
    if not os.path.exists(STATS_PATH):
        return {"accepted": 0, "rejected": 0, "cutoff": DEFAULT_CUTOFF}
    with open(STATS_PATH) as f:
        return json.load(f)

def _save_stats(stats):
    with open(STATS_PATH, "w") as f:
        json.dump(stats, f, indent=2)

def record_suggestion_outcome(used):
    stats = _load_stats()
    if used:
        stats["accepted"] += 1
    else:
        stats["rejected"] += 1

    total = stats["accepted"] + stats["rejected"]
    if total >= 5:  # only adjust after enough data
        acceptance_rate = stats["accepted"] / total
        if acceptance_rate < 0.4:
           stats["cutoff"] = round(min(stats["cutoff"] + 0.05, 0.9), 2)  # too many bad suggestions -> stricter
        elif acceptance_rate > 0.8:
            stats["cutoff"] = round(max(stats["cutoff"] - 0.05, 0.2), 2)  # suggestions too rare/good -> loosen a bit

    _save_stats(stats)
    return stats["cutoff"]

def get_current_cutoff():
    return _load_stats()["cutoff"]

def _norm(path):
    path = path.strip()
    if not path.startswith("."):
        path = "./" + path.lstrip("/")
    return path.rstrip("/") or "."


def list_files(path="."):
    path = _norm(path)
    prefix = path if path == "." else path + "/"
    entries = set()
    for p in FAKE_FS:
        if p == path:
            continue
        if path == ".":
            rel = p[2:] if p.startswith("./") else p
        elif p.startswith(prefix):
            rel = p[len(prefix):]
        else:
            continue
        if not rel:
            continue
        top = rel.split("/")[0]
        is_dir = ("/" in rel) or (p.endswith("/"))
        entries.add(top + ("/" if is_dir else ""))
    return "\n".join(sorted(entries)) or "(empty directory)"

def read_file(path):
    path = _norm(path)
    # _norm() strips trailing slashes (at very end of path)before lookup and adding ./ prefix
    if path + "/" in FAKE_FS:
        return f"(fake) Error: '{path}' is a directory, not a file"
    #typo suggestion
    if path not in FAKE_FS or FAKE_FS[path] is None:
        candidates = [p for p in FAKE_FS if FAKE_FS[p] is not None]
        cutoff = get_current_cutoff()
        close = difflib.get_close_matches(path, candidates, n=1, cutoff=cutoff)
        suggestion = f" {DID_YOU_MEAN} '{close[0]}'?" if close else ""
        return f"(fake) Error: no such file '{path}'.{suggestion}"

    return FAKE_FS[path]
"""
read_file("./data") called
_norm("./data") → .strip() → "./data" (already starts with ., no trailing slash to strip) → returns "./data"
Check: "./data" not in FAKE_FS → True — because the actual key stored is "./data/" (with trailing slash), not "./data"
So it falls straight into the error branch, treating a real directory as "not found"
difflib.get_close_matches("./data", candidates) then compares against file paths and picks "./data/sample.csv" as textually similar → misleading suggestion

my sugeestion we can either remnove norm or add / if entere error blovck beofre checking suggestion
"""

def write_file(path, content):
    path = _norm(path)
    FAKE_FS[path] = content
    return f"(fake) Saved {path} ({len(content)} characters) — not written to real disk"


def run_command(command):
    # answer = input(f"  [DUMMY] Simulate running '{command}'? [y/N] ")
    # if answer.strip().lower() != "y":
    #     return "The user declined to run this command."
    # Nothing is actually executed. Return a canned, clearly-labeled fake result
    # so you can verify your loop handles tool output correctly end-to-end.
    return (
        f"(simulated output — command was NOT actually run)\n"
        f"$ {command}\n"
        f"[fake exit code 0]"
    )

def extract_path_from_action(action_str):
    match = re.search(r"'path', '([^']+)'", action_str)
    return match.group(1) if match else None

def was_suggestion_used(suggested_path,action_history):
    if not action_history:
        return False
    last_path=extract_path_from_action(action_history[-1])
    if last_path is None:
        return False
    return _norm(last_path) == _norm(suggested_path)

TOOLS = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
    "run_command": run_command,
}

# TOOL_SCHEMAS unchanged — copy from your original file, or import it from there.
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List the files in a directory. Folders end with /.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory to list, e.g. '.'"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a text file and return its contents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path of the file to read"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or overwrite a text file with the given content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path of the file to write"},
                    "content": {"type": "string", "description": "Full contents of the file"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a shell command and return its output. The user approves it first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to run"},
                },
                "required": ["command"],
            },
        },
    },
]