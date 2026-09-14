# tests/tools_test.py
from agent.tools import read_file, FAKE_FS


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