from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# ---------------------------------------------------------------------------
# Declarative authority sets
# ---------------------------------------------------------------------------

AUTHORIZED: set[str] = {
    "enforce_pipeline",
    "reject_ambiguous_plans",
    "require_t1_for_build",
    "require_t1_for_verify",
    "require_t1_for_commit",
    "record_ledger_entry",
    "capture_terminal_output",
    "validate_evidence_signature",
    "spawn_child_actor",
    "open_session_scope",
}

NOT_AUTHORIZED: set[str] = {
    "hallucinate_test_results",
    "fabricate_build_output",
    "skip_verify_step",
    "downgrade_tier_for_commit",
    "rewrite_ledger_history",
    "erase_actor_lineage",
}


# ---------------------------------------------------------------------------
# Violations
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AuthorityViolation:
    action: str
    error: str
    details: str

    def to_dict(self) -> dict[str, str]:
        return {
            "action": self.action,
            "error": self.error,
            "details": self.details,
        }


# ---------------------------------------------------------------------------
# Authority model
# ---------------------------------------------------------------------------

class AuthorityModel:
    """
    Simple structural authority model.

    This is intentionally minimal and declarative: it encodes which
    governance actions are allowed vs explicitly forbidden. It is not
    a full RBAC system; it is a structural guardrail.
    """

    def __init__(
        self,
        *,
        allowed: set[str] | None = None,
        forbidden: set[str] | None = None,
    ) -> None:
        self._allowed: set[str] = set(allowed) if allowed is not None else set(AUTHORIZED)
        self._forbidden: set[str] = set(forbidden) if forbidden is not None else set(NOT_AUTHORIZED)

    # ------------------------------------------------------------------
    # Core check
    # ------------------------------------------------------------------

    def check(self, action: str) -> tuple[bool, dict[str, Any]]:
        """
        Check whether the given action is authorized.

        Returns:
            (ok: bool, info: dict)
        """
        if action in self._forbidden:
            violation = AuthorityViolation(
                action=action,
                error="ACTION_EXPLICITLY_FORBIDDEN",
                details=f"Action '{action}' is forbidden by structural authority model.",
            )
            return False, violation.to_dict()

        if action not in self._allowed:
            violation = AuthorityViolation(
                action=action,
                error="ACTION_NOT_DECLARED",
                details=f"Action '{action}' is not declared as authorized.",
            )
            return False, violation.to_dict()

        return True, {
            "action": action,
            "status": "AUTHORIZED",
        }

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def is_authorized(self, action: str) -> bool:
        ok, _ = self.check(action)
        return ok

    def require(self, action: str) -> None:
        """
        Raise if the action is not authorized.
        """
        ok, info = self.check(action)
        if not ok:
            raise PermissionError(f"Authority violation: {info}")
