# SFT Training Pipeline (Proof-of-Concept)

## What this is
A minimal supervised fine-tuning (SFT) pass on a small open-weight model, using
trajectories collected from the agent's own runs. Explores the paper's A1/A2
"weight-update adaptation" quadrant, as an alternative to the prompt-injection-based
memory/tool adaptation already implemented in `agent/`.

## Files
- `collect_training_data.py` — pulls `(messages)` examples from `checkpoints/*.json`,
  filtered to steps where `pass_his[-1] == True`. Outputs `sft_data.jsonl`.
- `sft_data.jsonl` — collected training examples (currently 7, from demo runs).
- `train_sft.ipynb` — Colab notebook: loads `Qwen2.5-0.5B-Instruct`, applies a LoRA
  adapter, fine-tunes on `sft_data.jsonl`, saves the adapter.

## Current status: proof-of-concept only
- Pipeline runs end-to-end (data → train → inference) without errors.
- **Not enough data yet** — 7 examples is far too few for the model to reliably
  learn the agent's tool-calling pattern. Test generation after training produced
  incoherent/off-topic output (the base model's own behavior dominates).
- Examples were flattened to plain text (`<role>: content`) rather than using a
  proper chat/tool-calling template — faster to get working, but likely limits
  how well the model can learn tool-call structure specifically.

## What's needed to go further
- **More data**: run many more varied agent tasks to collect dozens-hundreds of
  examples, not single digits.
- **Proper chat template**: use the base model's actual tool-calling format
  (or a structured chat template) instead of flattened text, so the model learns
  correct tool-call syntax.
- **Evaluation**: some way to measure if the fine-tuned model is actually better
  than the base model at this task, not just "it runs."
- **Hosting**: to actually replace Groq in `agent/agent.py`, the fine-tuned model
  needs to be served somewhere the agent can call it (e.g. via a local/hosted
  inference endpoint) — not yet done.