from provenance_gate.capture import TerminalCapture


def test_terminal_capture():
    evidence = TerminalCapture.run(["echo", "hello"])
    assert evidence.exit_code == 0
    assert "hello" in evidence.content
    assert evidence.is_valid()
