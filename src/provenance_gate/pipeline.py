from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, ClassVar

from provenance_gate.evidence import EvidenceArtifact
from provenance_gate.guards import guard_step, guard_verify

# ---------------------------------------------------------------------------
# Pipeline steps
# ---------------------------------------------------------------------------

class PipelineStep(Enum):
    SPEC = "SPEC"
    PLAN = "PLAN"
    TEST = "TEST"
    BUILD = "BUILD"
    VERIFY = "VERIFY"
    REVIEW = "REVIEW"
    COMMIT = "COMMIT"


# ---------------------------------------------------------------------------
# Violations
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PipelineViolation:
    step: str
    error: str
    details: str

    def to_dict(self) -> dict[str, str]:
        return {
            "step": self.step,
            "error": self.error,
            "details": self.details,
        }


# ---------------------------------------------------------------------------
# Pipeline state machine
# ---------------------------------------------------------------------------

@dataclass
class PipelineState:
    """
    PipelineState tracks the current step and enforces structural governance.

    Rules:
        - Steps must advance in correct order.
        - Evidence tier must satisfy RuleSet requirements.
        - VERIFY must use guard_verify (hallucination defense).
        - Non-VERIFY steps use guard_step.
    """

    current: PipelineStep = PipelineStep.SPEC
    history: list[dict[str, Any]] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Step ordering
    # ------------------------------------------------------------------

    ORDER: ClassVar[list[PipelineStep]] = [
        PipelineStep.SPEC,
        PipelineStep.PLAN,
        PipelineStep.TEST,
        PipelineStep.BUILD,
        PipelineStep.VERIFY,
        PipelineStep.REVIEW,
        PipelineStep.COMMIT,
    ]

    def _next_step(self, step: PipelineStep) -> PipelineStep | None:
        idx = self.ORDER.index(step)
        if idx + 1 < len(self.ORDER):
            return self.ORDER[idx + 1]
        return None

    def _is_valid_transition(self, step: PipelineStep) -> bool:
        expected_next = self._next_step(self.current)
        return expected_next == step

    # ------------------------------------------------------------------
    # Advance
    # ------------------------------------------------------------------

    def advance(
        self,
        step: str,
        evidence: EvidenceArtifact | None,
        *,
        verify_source: str | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """
        Attempt to advance the pipeline to the given step.

        Returns:
            (ok: bool, info: dict)
        """
        try:
            step_enum = PipelineStep(step)
        except Exception:
            violation = PipelineViolation(
                step=step,
                error="INVALID_STEP",
                details=f"Unknown pipeline step: {step}",
            )
            return False, violation.to_dict()

        # Check ordering
        if not self._is_valid_transition(step_enum):
            violation = PipelineViolation(
                step=step,
                error="INVALID_TRANSITION",
                details=f"Cannot transition from {self.current.value} to {step_enum.value}",
            )
            return False, violation.to_dict()

        # VERIFY uses hallucination defense + RuleSet
        if step_enum is PipelineStep.VERIFY:
            ok, info = guard_verify(
                evidence,
                prior_state_validated=True,
            )
            if not ok:
                return False, info

        # Other steps use RuleSet tier validation
        else:
            ok, info = guard_step(step_enum.value, evidence)
            if not ok:
                return False, info

        # All good — advance
        self.current = step_enum
        record = {
            "step": step_enum.value,
            "evidence": evidence.to_dict() if evidence else None,
            "status": "ADVANCED",
        }
        self.history.append(record)

        return True, {
            "status": "ADVANCED",
            "step": step_enum.value,
            "rules": info,
        }

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def can_advance(self, step: str) -> bool:
        try:
            step_enum = PipelineStep(step)
        except Exception:
            return False
        return self._is_valid_transition(step_enum)

    def last(self) -> dict[str, Any] | None:
        return self.history[-1] if self.history else None
