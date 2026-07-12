from provenance_gate.capture import TerminalCapture
from provenance_gate.guards import guard_verify


def test_verify_guard_accepts_t1():
    ev = TerminalCapture.run(["echo", "ok"])
    ok, info = guard_verify(ev)
    assert ok
    assert info["status"] == "AUTHORIZED"
