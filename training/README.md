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
- Pipeline runs