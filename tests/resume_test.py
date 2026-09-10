from unittest.mock import patch
from agent.tools import FAKE_FS
from agent.checkpoint import save_checkpt, load_checkpt


def test_resumerestores():
    original_fs_snapshot = {"./notes.txt": "original content", "./data/": None}
    state = {
        "messages": [{"role": "system", "content": "sys"}, {"role": "user", "content": "hi"}],
        "file_sys": original_fs_snapshot,
        "step": 2,
        "action_history": ["read_file:[('path', 'notes.txt')]"],
        "failure_streak": 1,
    }
    save_checkpt(state, 2)

    loaded = load_checkpt(2)
    FAKE_FS.clear()
    FAKE_FS.update(loaded["file_sys"])

    assert FAKE_FS == original_fs_snapshot
    assert loaded["step"] == 2
    assert loaded["action_history"] == state["action_history"]


@patch("agent.agent.call_llm_with_retry")
def test_resumestartingstepdoesnotoverwriteearliercheckpoint(mock_llm):
    # simulate: LLM immediately returns no tool_calls, so run_agent exits fast
    mock_response = type("MockResp", (), {})()
    mock_message = type("MockMsg", (), {"content": "done", "tool_calls": None})()
    mock_response.choices = [type("Choice", (), {"message": mock_message})()]
    mock_llm.return_value = mock_response

    from agent.agent import run_agent
    message = [{"role": "system", "content": "sys"}]
    action_history = []

    reply = run_agent(message, action_history, starting_step=2, starting_failure_streak=1)
    assert reply == "done"