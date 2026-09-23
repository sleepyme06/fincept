# tests/tools_test.py
from agent.tools import read_file, FAKE_FS, was_suggestion_used,record_suggestion_outcome, get_current_cutoff, STATS_PATH
import os
from agent.memory import extract_suggestion
from agent.signals import get_action_key

def test_read_file_suggests_close_match():
    result = read_file("setings.txt")  # typo, close to "notes.txt"
    assert "Error" in result
    assert "notes.txt" in result


def test_read_file_no_suggestion_when_no_match():
    result = read_file("zzzzz_totally_unrelated_xyz")
    assert "Error" in result
    assert "Did you mean" not in result


def test_read_file_still_works_normally():
    assert read_file("notes.txt") == FAKE_FS["./notes.txt"]

def test_read_file_on_directory_returns_clean_error():
    result = read_file("./data")
    assert "directory" in result
    assert "Did you mean" not in result

def test_suggestion_used_when_next_action_matches():
    history = ["read_file:[('path', './notes.txt')]"]
    assert was_suggestion_used("./notes.txt", history) is True


def test_suggestion_not_used_when_next_action_differs():
    history = ["read_file:[('path', './other.txt')]"]
    assert was_suggestion_used("./notes.txt", history) is False


def test_suggestion_not_used_when_history_empty():
    assert was_suggestion_used("./notes.txt", []) is False

def test_suggestion_flow_end_to_end():
    # simulate a failed read_file with a typo
    result = "(fake) Error: no such file './setings.txt'. Did you mean './notes.txt'?"
    suggestion = extract_suggestion(result)
    assert suggestion == "./notes.txt"

    # simulate agent taking the hint on its next action
    action_history = [get_action_key("read_file", {"path": "./notes.txt"})]
    assert was_suggestion_used(suggestion, action_history) is True


def test_suggestion_flow_ignored():
    result = "(fake) Error: no such file './setings.txt'. Did you mean './notes.txt'?"
    suggestion = extract_suggestion(result)

    # agent does something unrelated instead
    action_history = [get_action_key("list_files", {"path": "./"})]
    assert was_suggestion_used(suggestion, action_history) is False

def _cleanup_stats():
    if os.path.exists(STATS_PATH):
        os.remove(STATS_PATH)


def test_cutoff_unchanged_below_threshold():
    _cleanup_stats()
    for _ in range(4):
        record_suggestion_outcome(True)
    assert get_current_cutoff() == 0.4
    _cleanup_stats()


def test_cutoff_loosens_on_high_acceptance():
    _cleanup_stats()
    for _ in range(5):
        record_suggestion_outcome(True)
    assert get_current_cutoff() == 0.35
    _cleanup_stats()


def test_cutoff_tightens_on_low_acceptance():
    _cleanup_stats()
    for _ in range(5):
        record_suggestion_outcome(False)
    assert get_current_cutoff() == 0.45
    _cleanup_stats()


def test_cutoff_respects_bounds():
    _cleanup_stats()
    for _ in range(200):
        record_suggestion_outcome(False)
    assert get_current_cutoff() <= 0.9
    _cleanup_stats()