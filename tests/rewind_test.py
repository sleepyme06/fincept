from agent.signals import should_rewind


def test_rewind():
    assert should_rewind(0.0, 0.0, 0, 1.0) is False

    assert should_rewind(0.7, 0.0, 0, 1.0) is True

    assert should_rewind(0.0, 0.0, 3, 0.1) is True
    
    assert should_rewind(0.0, 0.0, 2, 0.5) is False

    assert should_rewind(0.0, 0.8, 0, 0.2) is True
    # high drift but repetition/confidence not elevated -> should NOT trigger
    assert should_rewind(0.0, 0.8, 0, 0.9) is False