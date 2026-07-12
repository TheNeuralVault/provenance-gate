from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from provenance_gate.capture import SignedEvidence
from provenance_gate.evidence import EvidenceArtifact
from provenance_gate.rules import RuleSet
from provenance_gate.tiers import Tier

# ---------------------------------------------------------------------------
# Hallucination violations
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class HallucinationViolation:
    error: str
    details: str

    def to_dict(self) -> dict[str, str]:
        return {
            "error": self.error,
            "details": self.details,
        }


# ---------------------------------------------------------------------------
# Hallucination defense
# ---------------------------------------------------------------------------

def check_hallucination_defense(
    evidence: EvidenceArtifact | SignedEvidence | None,
    *,
    prior_state_validated: bool = True,
) -> tuple[bool, dict[str, Any]]:
    """
    Core hallucination defense check.

    Requirements:
        - evidence must be present
        - evidence must be T1 (for EvidenceArtifact)
        - SignedEvidence must have a valid signature
        - prior_state_validated must be True (caller must assert)

    This function does NOT trust caller-supplied booleans as T1; it only
    accepts actual captured evidence.
    """
    if not prior_state_validated:
        violation = HallucinationViolation(
            error="PRIOR_STATE_NOT_VALIDATED",
            details="Caller did not validate prior pipeline state before VERIFY.",
        )
        return False, violation.to_dict()

    if evidence is None:
        violation = HallucinationViolation(
            error="NO_EVIDENCE_PROVIDED",
            details="VERIFY requires T1 evidence; none was provided.",
        )
        return False, violation.to_dict()

    # EvidenceArtifact path
    if isinstance(evidence, EvidenceArtifact):
        if evidence.tier is not Tier.T1:
            violation = HallucinationViolation(
                error="EVIDENCE_NOT_T1",
                details=f"VERIFY requires T1 evidence; got {evidence.tier.name}.",
            )
            return False, violation.to_dict()
        return True, {
            "status": "OK",
            "kind": "EvidenceArtifact",
            "tier": evidence.tier.name,
            "source": evidence.source,
        }

    # SignedEvidence path
    if isinstance(evidence, SignedEvidence):
        if not evidence.is_valid():
            violation = HallucinationViolation(
                error="SIGNED_EVIDENCE_INVALID",
                details="SignedEvidence HMAC signature did not verify.",
            )
            return False, violation.to_dict()
        return True, {
            "status": "OK",
            "kind": "SignedEvidence",
            "command": list(evidence.command),
            "exit_code": evidence.exit_code,
        }

    violation = HallucinationViolation(
        error="UNSUPPORTED_EVIDENCE_TYPE",
        details=f"Unsupported evidence type: {type(evidence)!r}",
    )
    return False, violation.to_dict()


# ---------------------------------------------------------------------------
# VERIFY guard
# ---------------------------------------------------------------------------

def guard_verify(
    evidence: EvidenceArtifact | SignedEvidence | None,
    *,
    prior_state_validated: bool = True,
) -> tuple[bool, dict[str, Any]]:
    """
    High-level VERIFY guard.

    Combines:
        - hallucination defense
        - RuleSet tier validation for VERIFY
    """
    ok, info = check_hallucination_defense(
        evidence,
        prior_state_validated=prior_state_validated,
    )
    if not ok:
        return False, info

    # Past hallucination defense, evidence is guaranteed non-None and either a
    # T1 EvidenceArtifact or a valid SignedEvidence. Normalize for RuleSet.
    if isinstance(evidence, SignedEvidence):
        artifact = evidence.to_t1_artifact(source="runtime_capture")
    else:
        assert evidence is not None
        artifact = evidence

    rules = RuleSet()
    ok, rule_info = rules.validate(
        step="VERIFY",
        provenance_tier=artifact.tier,
        verify_source=artifact.source,
    )
    if not ok:
        return False, rule_info

    merged: dict[str, Any] = {
        "status": "AUTHORIZED",
        "hallucination": info,
        "rules": rule_info,
    }
    return True, merged


# ---------------------------------------------------------------------------
# Generic step guard
# ---------------------------------------------------------------------------

def guard_step(
    step: str,
    evidence: EvidenceArtifact | None,
) -> tuple[bool, dict[str, Any]]:
    """
    Generic guard for non-VERIFY steps.

    Uses RuleSet to validate that the evidence tier is sufficient
    for the requested step.
    """
    if evidence is None:
        return False, {
            "error": "NO_EVIDENCE_PROVIDED",
            "details": f"Step {step} requires evidence; none provided.",
        }

    rules = RuleSet()
    ok, info = rules.validate(step=step, provenance_tier=evidence.tier)
    if not ok:
        return False, info

    return True, {
        "status": "AUTHORIZED",
        "rules": info,
    }
