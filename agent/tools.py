import os

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
    if path not in FAKE_FS or FAKE_FS[path] is None:
        return f"(fake) Error: no such file '{path}'"
    return FAKE_FS[path]


def write_file(path, content):
    path = _norm(path)
    FAKE_FS[path] = content
    return f"(fake) Saved {path} ({len(content)} characters) — not written to real disk"


def run_command(command):
    answer = input(f"  [DUMMY] Simulate running '{command}'? [y/N] ")
    if answer.strip().lower() != "y":
        return "The user declined to run this command."
    # Nothing is actually executed. Return a canned, clearly-labeled fake result
    # so you can verify your loop handles tool output correctly end-to-end.
    return (
        f"(simulated output — command was NOT actually run)\n"
        f"$ {command}\n"
        f"[fake exit code 0]"
    )


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