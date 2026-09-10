import os
import json
from unittest.mock import patch
from agent.checkpoint import CHECKPOINT_DIR, load_checkpt


def make_mock_response(content, tool_calls):
    message = type("MockMsg", (), {"content": content, "tool_calls": tool_calls})()
    choice = type("Choice", (), {"message": message})()
    response = type("MockResp", (), {"choices": [choice]})()
    return response


def make_mock_tool_call(call_id, name, args_dict):
    function = type("Function", (), {"name": name, "arguments": json.dumps(args_dict)})()
    return type("ToolCall", (), {"id": call_id, "type": "function", "function": function})()


@patch("agent.agent.call_llm_with_retry")
def test_resume_starting_step_does_not_overwrite_earlier_checkpoint(mock_llm):
    # write a fake "earlier" checkpoint at step 1, so we can confirm it's untouched
    earlier_checkpoint = {"messages": [], "file_sys": {}, "step": 1,
                           "action_history": [], "failure_streak": 0, "pass_his": []}
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    with open(f"{CHECKPOINT_DIR}/checkpoint_1.json", "w") as f:
        json.dump(earlier_checkpoint, f)

    tool_call = make_mock_tool_call("call_1", "list_files", {"path": "."})
    first_response = make_mock_response(None, [tool_call])
    second_response = make_mock_response("done", None)
    mock_llm.side_effect = [first_response, second_response]

    from agent.agent import run_agent
    message = [{"role": "system", "content": "sys"}]
    action_history = []
    pass_his = []

    reply = run_agent(message, action_history, pass_his, starting_step=2, starting_failure_streak=1)

    assert reply == "done"

    # this run started at step 2, made ONE tool call, so it should have written
    # checkpoint_3.json -- NOT overwritten checkpoint_1.json
    new_checkpoint = load_checkpt(3)
    assert new_checkpoint["step"] == 3

    old_checkpoint = load_checkpt(1)
    assert old_checkpoint["step"] == 1
    assert old_checkpoint == earlier_checkpoint