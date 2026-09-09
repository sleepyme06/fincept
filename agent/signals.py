from .utils import call_llm_with_retry
import re

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

import re

def drift_score(name, args, result):
    if name == "write_file":
        expected_len = len(args.get("content", ""))
        match = re.search(r"\((\d+) characters\)", result)
        if not match:
            # result doesn't match expected format at all -- treat as max drift
            return 1.0
        actual_len = int(match.group(1))
        if expected_len == 0:
            return 0.0 if actual_len == 0 else 1.0
        diff_ratio = abs(expected_len - actual_len) / expected_len
        return min(diff_ratio, 1.0)

    # no ground truth available for other tools so nothing to check
    return 0.0

# ---- 3c: Verifier failure streak ----

def update_failure_streak(current_streak, passed):
    """passed: True/False — verifier ka result is step ke liye"""
    if passed:
        return 0
    return current_streak + 1


# ---- 3d: Confidence signal ----

def confidence_score(failure_streak, repetition_score):
    score = 1.0 - (failure_streak * 0.3) - (repetition_score* 0.1)
    score = max(0.0, min(1.0, score))
    return score

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

def should_rewind(rep_score, drift_score, failure_streak, confidence_score):
    if rep_score >= 0.66:
        return True
    if failure_streak >= 3:
        return True
    # drift akela trigger nahi karega — sirf tab count hoga
    # jab repetition ya confidence bhi already elevated ho
    if drift_score >= 0.7 and (rep_score >= 0.33 or confidence_score <= 0.3):
        return True
    return False