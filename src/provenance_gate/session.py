from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from provenance_gate.actors import Actor
from provenance_gate.ledger import AppendOnlyLedger
from provenance_gate.pipeline import PipelineState

if TYPE_CHECKING:
    from provenance_gate.evidence import EvidenceArtifact


class SessionScopeError(RuntimeError):
    pass


@dataclass
class SessionScope:
    """
    SessionScope represents a governed execution context.

    A session binds:
        - an actor (with lineage)
        - a pipeline state machine
        - an optional append-only ledger

    The session enforces:
        - immutable actor identity
        - immutable lineage
        - controlled pipeline advancement
        - structured ledger recording
    """

    actor: Actor
    pipeline: PipelineState = field(default_factory=PipelineState)
    ledger: AppendOnlyLedger | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    @classmethod
    def create(
        cls,
        actor: Actor,
        *,
        ledger: AppendOnlyLedger | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SessionScope:
        return cls(
            actor=actor,
            pipeline=PipelineState(),
            ledger=ledger,
            metadata=metadata or {},
        )

    # ------------------------------------------------------------------
    # Actor lineage
    # ------------------------------------------------------------------

    def lineage(self) -> list[Actor]:
        return self.actor.lineage()

    # ------------------------------------------------------------------
    # Pipeline advancement
    # ------------------------------------------------------------------

    def advance(
        self,
        step: str,
        evidence: EvidenceArtifact | None,
        *,
        verify_source: str | None = None,
        record: bool = True,
    ) -> dict[str, Any]:
        """
        Advance the pipeline and optionally record the transition in the ledger.

        Returns:
            info: dict describing the transition
        """
        ok, info = self.pipeline.advance(
            step=step,
            evidence=evidence,
            verify_source=verify_source,
        )
        if not ok:
            raise SessionScopeError(f"Pipeline advance failed: {info}")

        # Ledger recording
        if record and self.ledger is not None:
            nonce = f"{step}-{self.actor.actor_id}-{len(self.pipeline.history)}"
            payload = {
                "actor": self.actor.to_dict(),
                "step": step,
                "evidence": evidence.to_dict() if evidence else None,
                "metadata": self.metadata,
            }
            self.ledger.append(
                nonce=nonce,
                actor_id=self.actor.actor_id,
                step=step,
                payload=payload,
            )

        return info

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def current_step(self) -> str:
        return self.pipeline.current.value

    def last_record(self) -> dict[str, Any] | None:
        return self.pipeline.last()

    def attach_metadata(self, key: str, value: Any) -> None:
        self.metadata[key] = value

    def require_step(self, step: str) -> None:
        """
        Ensure the session is currently at the given step.
        """
        if self.pipeline.current.value != step:
            raise SessionScopeError(
                f"Session must be at step {step}, but is at {self.pipeline.current.value}"
            )

    def spawn_child(self, role: str) -> SessionScope:
        """
        Create a child session with a child actor.

        Child sessions inherit:
            - ledger
            - metadata (shallow copy)
        """
        child_actor = self.actor.spawn(role)
        return SessionScope.create(
            actor=child_actor,
            ledger=self.ledger,
            metadata=dict(self.metadata),
        )

