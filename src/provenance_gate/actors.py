from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Actor:
    """
    Actor identity for governed agent actions.

    Each actor has:
        - actor_id: collision-resistant UUID-based identifier
        - role: semantic role (e.g., "orchestrator", "planner", "tester")
        - parent: optional parent actor (lineage)

    Actor lineage is used to attribute governed actions to a concrete chain
    of responsibility. This is essential for structural governance.
    """

    actor_id: str
    role: str
    parent: Actor | None = None

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------

    @classmethod
    def root(cls, role: str) -> Actor:
        """
        Create a root actor with no parent.
        """
        return cls(actor_id=f"{role}-{uuid.uuid4().hex}", role=role, parent=None)

    def spawn(self, role: str) -> Actor:
        """
        Create a child actor whose parent is this actor.
        """
        return Actor(
            actor_id=f"{role}-{uuid.uuid4().hex}",
            role=role,
            parent=self,
        )

    # ------------------------------------------------------------------
    # Lineage
    # ------------------------------------------------------------------

    def lineage(self) -> list[Actor]:
        """
        Return the full lineage from root → self.
        """
        chain: list[Actor] = []
        cur: Actor | None = self
        while cur is not None:
            chain.append(cur)
            cur = cur.parent
        return list(reversed(chain))

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize actor identity. Parent is represented by ID only.
        """
        return {
            "actor_id": self.actor_id,
            "role": self.role,
            "parent_id": self.parent.actor_id if self.parent else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Actor:
        """
        Deserialize an actor WITHOUT reconstructing parent linkage.

        Parent linkage must be restored separately by the caller if needed.
        """
        return cls(
            actor_id=data["actor_id"],
            role=data["role"],
            parent=None,  # caller must re-link lineage if needed
        )

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        parent = self.parent.actor_id if self.parent else "None"
        return f"Actor(id={self.actor_id}, role={self.role}, parent={parent})"

    def __repr__(self) -> str:
        return str(self)
