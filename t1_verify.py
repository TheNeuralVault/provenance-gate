import hashlib
import sys

from provenance_gate import Tier, EvidenceArtifact, PipelineState
from provenance_gate.capture import TerminalCapture, SignedEvidence
from provenance_gate.rules import STEP_REQUIREMENTS

SELF_PATH = __file__
with open(SELF_PATH, "rb") as fh:
    SELF_HASH = hashlib.sha256(fh.read()).hexdigest()

print("SCRIPT_PATH", SELF_PATH)
print("SCRIPT_SHA256", SELF_HASH)

cmd = ["python", "-m", "pytest", "-q", "--co", "-q"]
signed = TerminalCapture.run(cmd, cwd=".")
print("SIGNED_PRESENT", bool(signed.signature))
print("SIGNED_VALID", signed.is_valid())

ev = signed.to_t1_artifact(source="runtime_capture")
print("T1_TIER", ev.tier.name)
print("T1_SOURCE", ev.source)
print("T1_SHA256", ev.hash)

tampered = SignedEvidence(
    content=signed.content + "\nTAMPERED",
    signature=signed.signature,
    command=signed.command,
    exit_code=signed.exit_code,
)
try:
    tampered.to_t1_artifact()
    print("TAMPER_REJECTED", False)
except ValueError as exc:
    print("TAMPER_REJECTED", True)
    print("TAMPER_EXCEPTION", str(exc))

ps = PipelineState()
steps = [
    ("PLAN", Tier.T4, "plan"),
    ("TEST", Tier.T4, "test"),
    ("BUILD", Tier.T1, "build"),
    ("VERIFY", Tier.T1, "verify"),
    ("REVIEW", Tier.T2, "review"),
    ("COMMIT", Tier.T1, "commit"),
]

def make(tier, source):
    if tier == Tier.T1:
        return ev
    return EvidenceArtifact(tier=tier, source=source, content="step-placeholder")

for name, tier, source in steps:
    ok, _info = ps.advance(name, make(tier, source))
    print("STEP", name, "ADVANCED" if ok else "BLOCKED")
