from provenance_gate.evidence import EvidenceArtifact
from provenance_gate.pipeline import PipelineState
from provenance_gate.tiers import Tier


def t1():
    return EvidenceArtifact(tier=Tier.T1, source="runtime_capture", content="ok")

def test_pipeline_full_path():
    p = PipelineState()

    assert p.current.value == "SPEC"

    ok, _ = p.advance("PLAN", t1())
    assert ok

    ok, _ = p.advance("TEST", t1())
    assert ok

    ok, _ = p.advance("BUILD", t1())
    assert ok

    ok, _ = p.advance("VERIFY", t1())
    assert ok

    ok, _ = p.advance("REVIEW", t1())
    assert ok

    ok, _ = p.advance("COMMIT", t1())
    assert ok

    assert p.current.value == "COMMIT"
