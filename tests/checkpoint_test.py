import copy
from agent.checkpoint import save_checkpt, load_checkpt


def test_saveandload():
    state = {
        "messages": [{"role": "user", "content": "hello"}],
        "file_sys": {"./notes.txt": "hi"},
        "step": 99,
        "action_history": ["read_file:[('path', 'notes.txt')]"],
        "failure_streak": 0,
    }
    save_checkpt(copy.deepcopy(state), 99)
    loaded = load_checkpt(99)

    assert loaded["step"] == 99
    assert loaded["messages"] == state["messages"]
    assert loaded["file_sys"] == state["file_sys"]
    assert loaded["action_history"] == state["action_history"]
    assert loaded["failure_streak"] == 0


def test_loadmissing():
    result = load_checkpt(999999)
    assert isinstance(result, str)
    assert result.startswith("ERROR")