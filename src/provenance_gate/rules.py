from __future__ import annotations

from dataclasses import dataclass

from provenance_gate.tiers import TIER_FROM_STRING, Tier

# ---------------------------------------------------------------------------
# Step → Minimum Tier Requirements
# ---------------------------------------------------------------------------

STEP_REQUIREMENTS: dict[str, Tier] = {
    "SPEC": Tier.T5,
    "PLAN": Tier.T4,
    "TEST": Tier.T4,
    "BUILD": Tier.T1,
    "VERIFY": Tier.T1,
    "REVIEW": Tier.T2,
    "COMMIT": Tier.T1,
    "CAPTURE": Tier.T3,
}

# VERIFY must reference one of these sources
VALID_VERIFY_SOURCES = {
    "test_output",
    "build_output",
    "runtime_capture",
}


# ---------------------------------------------------------------------------
# Rule Violations
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RuleViolation:
    step: str
    provenance_tier: Tier
    required_tier: Tier
    error: str
    details: str | None = None

    def to_dict(self) -> dict[str, str]:
        return {
            "step": self.step,
            "provenance_tier": self.provenance_tier.name,
            "required_tier": self.required_tier.name,
            "error": self.error,
            "details": self.details or "",
        }


# ---------------------------------------------------------------------------
# RuleSet — Core Governance Logic
# ---------------------------------------------------------------------------

class RuleSet:
    """
    RuleSet validates whether a given provenance tier is sufficient
    to authorize a pipeline step.

    This is the core structural governance logic used by PipelineState.
    """

    def validate(
        self,
        step: str,
        provenance_tier: str | Tier,
        *,
        verify_source: str | None = None,
    ) -> tuple[bool, dict[str, str]]:
        """
        Validate whether the provided tier can authorize the given step.

        Returns:
            (ok: bool, info: dict)
        """

        # Normalize tier input
        if isinstance(provenance_tier, str):
            try:
                tier = TIER_FROM_STRING[provenance_tier.upper()]
            except KeyError:
                return False, {
                    "error": "INVALID_TIER",
                    "details": f"Unknown tier: {provenance_tier}",
                }
        else:
            tier = provenance_tier

        # Unknown step
        if step not in STEP_REQUIREMENTS:
            return False, {
                "error": "INVALID_STEP",
                "details": f"Unknown step: {step}",
            }

        required = STEP_REQUIREMENTS[step]

        # VERIFY requires a valid source
        if step == "VERIFY" and verify_source not in VALID_VERIFY_SOURCES:
            return False, {
                "error": "INVALID_VERIFY_SOURCE",
                "details": f"verify_source must be one of {VALID_VERIFY_SOURCES}",
            }

        # Tier insufficient
        if tier.value > required.value:
            violation = RuleViolation(
                step=step,
                provenance_tier=tier,
                required_tier=required,
                error="TIER_INSUFFICIENT_FOR_STEP",
                details=f"{tier.name} cannot authorize {step}; requires {required.name}",
            )
            return False, violation.to_dict()

        # All good
        return True, {
            "step": step,
            "provenance_tier": tier.name,
            "required_tier": required.name,
            "status": "AUTHORIZED",
        }
