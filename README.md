# Fincept Agent

A small ReAct-style coding agent that uses Groq tool calls, a fake filesystem, action history, and checkpoints. It is a harness for experimenting with agent recovery; it does not yet execute real shell or disk operations.

## Setup

Create a `.env` file in the repository root with a Groq API key:

```text
GROQ_API_KEY=your-key-here
```

Install dependencies and activate the virtual environment:

```powershell
pip install -r requirements.txt
.\venv\Scripts\Activate.ps1
```

## Run

Run the interactive agent from the repository root:

```powershell
python -m agent.agent
```

Enter a prompt at `you:` and type `quit` or `exit` to stop.

Run the resume test from the repository root:

```powershell
python -m agent.test
```

The resume test loads a saved checkpoint, restores the messages, action history, step number, and fake filesystem, then continues with a new instruction.

## Checkpoints and rewind

After each tool step, the agent saves a JSON checkpoint under `checkpoints/`. A checkpoint contains the conversation messages, fake filesystem state, action history, current step, and failure streak.

The agent can trigger a rewind when it detects repeated actions, repeated failures, high drift, or low confidence. It then tries to load the previous step's checkpoint, restores the saved state, and adds a message asking the model to try a different approach. If that checkpoint does not exist, the rewind is reported and the current run continues.

Run commands from the repository root with `python -m ...` so the package-relative imports work correctly.

