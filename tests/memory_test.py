import os
from agent.memory import add_reflection, get_reflections, MEMORY_PATH


def _cleanup():
    if os.path.exists(MEMORY_PATH):
        os.remove(MEMORY_PATH)


def test_add_and_get_reflection():
    _cleanup()
    add_reflection("read_file", {"path": "settings.txt"}, "failure_streak=3")

    reflections = get_reflections()
    assert len(reflections) == 1
    assert reflections[0]["action_key"] == "read_file:[('path', 'settings.txt')]"
    assert reflections[0]["reason"] == "failure_streak=3"

    _cleanup()


def test_dedupe_same_action():
    _cleanup()
    add_reflection("read_file", {"path": "settings.txt"}, "reason 1")
    add_reflection("read_file", {"path": "settings.txt"}, "reason 2")

    reflections = get_reflections()
    assert len(reflections) == 1
    assert reflections[0]["reason"] == "reason 2"

    _cleanup()


def test_different_actions_both_kept():
    _cleanup()
    add_reflection("read_file", {"path": "settings.txt"}, "reason a")
    add_reflection("read_file", {"path": "config.json"}, "reason b")

    reflections = get_reflections()
    assert len(reflections) == 2

    _cleanup()


def test_limit():
    _cleanup()
    for i in range(10):
        add_reflection("run_command", {"cmd": f"cmd{i}"}, f"reason {i}")

    reflections = get_reflections(limit=3)
    assert len(reflections) == 3
    assert reflections[-1]["reason"] == "reason 9"

    _cleanup()


def test_get_reflections_no_file():
    _cleanup()
    reflections = get_reflections()
    assert reflections == []

def test_filter_by_tool_name():
    _cleanup()
    add_reflection("read_file", {"path": "a.txt"}, "reason a")
    add_reflection("write_file", {"path": "b.txt"}, "reason b")

    reflections = get_reflections(tool_name="read_file")
    assert len(reflections) == 1
    assert reflections[0]["action_key"].startswith("read_file:")

    _cleanup()

def test_curation_caps_size():
    _cleanup()
    for i in range(25):
        add_reflection("read_file", {"path": f"file{i}.txt"}, f"reason {i}")

    reflections = get_reflections(limit=25)
    assert len(reflections) == 20
    assert reflections[0]["action_key"] == "read_file:[('path', 'file5.txt')]"
    assert reflections[-1]["action_key"] == "read_file:[('path', 'file24.txt')]"

    _cleanup()