from provenance_gate.actors import Actor
from provenance_gate.evidence import EvidenceArtifact
from provenance_gate.session import SessionScope
from provenance_gate.tiers import Tier


def t1():
    return EvidenceArtifact(tier=Tier.T1, source="runtime_capture", content="ok")

def test_session_advancement():
    actor = Actor.root("orchestrator")
    session = SessionScope.create(actor)

    session.advance("PLAN", t1())
    session.advance("TEST", t1())
    session.advance("BUILD", t1())
    session.advance("VERIFY", t1())

    assert session.current_step() == "VERIFY"
