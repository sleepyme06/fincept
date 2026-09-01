def get_action_key(name, args):
    # tool name + args ko ek comparable, hashable string mein convert karo
    return f"{name}:{sorted(args.items())}"


def repetition_score(action_history, window=4):
    if len(action_history) < 2:
        return 0.0

    recent = action_history[-window:]
    repeats = 0
    for i in range(1, len(recent)):
        if recent[i] == recent[i - 1]:
            repeats += 1

    return repeats / (len(recent) - 1)

from sentence_transformers import SentenceTransformer
import numpy as np

# model ek hi baar load hota hai, top-level pe
embed_model = SentenceTransformer("all-MiniLM-L6-v2")


def get_embedding(text):
    return embed_model.encode(text)


def cosine_similarity(vec1, vec2):
    dot = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def drift_score(expected_text, actual_text):
    exp_vec = get_embedding(expected_text)
    act_vec = get_embedding(actual_text)
    similarity = cosine_similarity(exp_vec, act_vec)
    return 1 - similarity   # high similarity = low drift

# ---- 3c: Verifier failure streak ----

def update_failure_streak(current_streak, passed):
    """passed: True/False — verifier ka result is step ke liye"""
    if passed:
        return 0
    return current_streak + 1


# ---- 3d: Confidence signal ----

def confidence_score(client, model, name, args, result):
    resp = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": (
                f"An agent ran: {name}({args}) and got this result:\n{result}\n\n"
                f"On a scale of 1-10, how confident should the agent be that "
                f"this step was correct and moved the task forward? "
                f"Reply with ONLY a single number, nothing else."
            )
        }],
    )
    text = resp.choices[0].message.content.strip()
    try:
        return int(text.split()[0]) / 10   # normalize to 0-1
    except (ValueError, IndexError):
        return 0.5   # fallback agar LLM ne number nahi diya

import csv
import os

LOG_PATH = "signals_log.csv"

def log_signals(step, rep_score, d_score, failure_streak, c_score):
    file_exists = os.path.exists(LOG_PATH)
    with open(LOG_PATH, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["step", "repetition", "drift", "failure_streak", "confidence"])
        writer.writerow([step, rep_score, d_score, failure_streak, c_score])