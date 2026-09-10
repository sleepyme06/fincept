# Fincept Agent

A small ReAct-style coding agent that uses Groq tool calls, a fake filesystem,
action history, checkpoints, and a cheap-signal rewind mechanism. It is a
harness for experimenting with long-horizon agent recovery; it does not
execute real shell or disk operations — all tools operate on an in-memory
fake filesystem (`agent/tools.py`).

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
python run.py
```

Enter a prompt at `you:` and type `quit` or `exit` to stop.

Run the scripted demo (no typing required) that shows a stuck → rewind →
different-attempt sequence end to end:

```powershell
python demo.py
```

Run all unit tests from the repository root:

```powershell
pytest
```

Tests live in `tests/` and cover `get_action_key`, `repetition_score`,
`confidence_score`, `drift_score`, checkpoint save/load, the rewind trigger
rule, and resume state restoration. LLM-dependent code paths are mocked in
tests — no network calls are made during `pytest`.

## Signals

Four cheap, per-step signals are computed after every tool call and logged
to `signals_log.csv`:

- **repetition_score** — fraction of the last 4 actions that repeat the
  immediately preceding action. Pure code, no LLM call.
- **drift_score** — for `write_file`, compares the length of the intended
  content against the length the tool reports saving; returns 0 for every
  other tool, since there is no ground truth available to compare against.
  Pure code, no LLM call.
- **failure_streak** — count of consecutive tool calls whose result
  contains an error string. Pure code, no LLM call.
- **confidence_score** — rule-based, `1.0 - (failure_streak * 0.3) -
  (repetition_score * 0.1)`, clamped to `[0, 1]`. No LLM call.

Only one LLM call is made per tool-calling step (the main tool-selection
call) — all four signals are computed without additional model calls, to
stay within Groq's per-minute request/token limits.

## Checkpoints and rewind

After each tool step, the agent saves a JSON checkpoint under
`checkpoints/`. A checkpoint contains the conversation messages, fake
filesystem state, action history, current step, and failure streak.

`should_rewind()` (in `agent/signals.py`) combines the four signals into a
rewind/continue decision using fixed thresholds — repetition ≥ 0.66,
failure_streak ≥ 3, or elevated drift combined with elevated repetition or
low confidence.

When rewind triggers, the agent loads the checkpoint from last best step if not then one step earlier,
restores the fake filesystem and message history in place, and appends a
message telling the model its previous approach failed and to try
something different. Rewinds are capped at `MAX_REWINDS` per task to avoid
infinite loops. If the target checkpoint doesn't exist, the rewind is
skipped and the run continues without it.

<!-- ## Known limitations

- `drift_score` only detects content-length mismatches on `write_file`; it
  cannot detect reasoning errors on `read_file`/`list_files`/`run_command`
  results, since there's no ground truth to compare against for those tools.
- Rewind currently always targets the checkpoint one step before the
  triggering step, not necessarily the last known-good step before a
  multi-step failure pattern began.
- The rewind trigger is a fixed rule-based threshold; a learned classifier
  (logistic regression on the 4 signals) is planned but not yet trained,
  pending a larger labeled dataset.

## Package structure

Run everything from the repository root using the top-level scripts
(`run.py`, `demo.py`) or `python -m agent.<module>` — never run
`agent/agent.py` directly, since that causes it to be imported twice under
different module names (once as `__main__`, once via the package's
`__init__.py`), which can produce inconsistent shared state. -->
