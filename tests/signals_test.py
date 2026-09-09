from agent.signals import get_action_key, repetition_score, confidence_score,drift_score

# def test_placeholder():
#     assert True

def test_getactionkey():
    assert get_action_key("read_file", {"path": "notes.txt"}) == get_action_key("read_file", {"path": "notes.txt"})

    assert get_action_key("read_file", {"path": "config.txt"}) != get_action_key("read_file", {"path": "configuration.txt"})

    assert get_action_key("read_file", {"path": "notes.txt"}) != get_action_key("write_file", {"path": "notes.txt"})

    key1 = get_action_key("write_file", {"path": "a.txt", "content": "hi"})
    key2 = get_action_key("write_file", {"content": "hi", "path": "a.txt"})
    assert key1 == key2


def test_repetition():
    assert repetition_score([]) == 0.0

    assert repetition_score(["a"]) == 0.0

    # recent = ["a", "a"], 1 pair checked, 1 repeat -> 1/1 = 1.0
    assert repetition_score(["a", "a"]) == 1.0

    assert repetition_score(["a", "b", "c", "d"]) == 0.0

    # recent = ["a","a","a","a"], 3 pairs checked, 3 repeats -> 3/3 = 1.0
    assert repetition_score(["a", "a", "a", "a"]) == 1.0

    history = [
        get_action_key("read_file", {"path": "config.txt"}),
        get_action_key("read_file", {"path": "configuration.txt"}),
        get_action_key("read_file", {"path": "settings.txt"}),
        get_action_key("read_file", {"path": "config.json"}),
    ]
    # all args differ -> all keys unique -> no adjacent repeats
    assert repetition_score(history) == 0.0

    # 6 items, only last 4 matter (window=4): b,a,a,a -> recent = [b,a,a,a]
    # pairs: (b,a) no, (a,a) yes, (a,a) yes -> 2/3
    history = ["x", "x", "b", "a", "a", "a"]
    assert repetition_score(history) == 2 / 3

def test_confidencescore():
    assert confidence_score(4, 0) == 0.0
    assert confidence_score(1, 1.0) == 0.6


def test_drift():
    args = {"path": "notes.txt", "content": "hello world"}
    result = "(fake) Saved ./notes.txt (11 characters) — not written to real disk"
    assert drift_score("write_file", args, result) == 0.0

    args = {"path": "notes.txt", "content": "hello world"}  # 11 chars
    result = "(fake) Saved ./notes.txt (5 characters) — not written to real disk"
    # diff_ratio = abs(11-5)/11 = 6/11 ≈ 0.545
    assert abs(drift_score("write_file", args, result) - (6/11)) < 1e-6

    args = {"path": "empty.txt", "content": ""}
    result = "(fake) Saved ./empty.txt (0 characters) — not written to real disk"
    assert drift_score("write_file", args, result) == 0.0

    args = {"path": "empty.txt", "content": ""}
    result = "(fake) Saved ./empty.txt (5 characters) — not written to real disk"
    assert drift_score("write_file", args, result) == 1.0

    args = {"path": "notes.txt", "content": "hello"}
    result = "something unexpected with no character count"
    assert drift_score("write_file", args, result) == 1.0

    assert drift_score("read_file", {"path": "notes.txt"}, "some content") == 0.0
    assert drift_score("list_files", {"path": "."}, "a\nb\nc") == 0.0
    assert drift_score("run_command", {"command": "ls"}, "fake output") == 0.0