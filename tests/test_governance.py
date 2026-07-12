from provenance_gate.evidence import EvidenceArtifact
from provenance_gate.governance import governed_step
from provenance_gate.pipeline import PipelineState
from provenance_gate.tiers import Tier

pipeline = PipelineState()

@governed_step("PLAN", pipeline)
def plan_step(*, evidence):
    return {"result": "ok"}

def test_governed_step():
    ev = EvidenceArtifact(tier=Tier.T1, source="runtime_capture", content="ok")
    out = plan_step(evidence=ev)
    assert out["result"] == "ok"
    assert out["_governance"]["pipeline"]["status"] == "ADVANCED"
