from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any

from provenance_gate.tiers import TIER_FROM_STRING, Tier


def _hash_content(content: Any) -> str:
    """
    Compute a stable hash for evidence content.

    For strings/bytes: hash directly.
    For other types: use repr() as a stable, human-auditable view.
    """
    data = content if isinstance(content, bytes) else repr(content).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class EvidenceArtifact:
    """
    EvidenceArtifact represents a single piece of provenance evidence.

    Fields:
        tier: Tier classification (T1-T5)
        source: human-readable source label (e.g., "pytest", "build", "docs")
        content: arbitrary evidence payload (string, dict, etc.)
        timestamp: capture time (epoch seconds)
        hash: SHA-256 hash of content (computed automatically)

    This is the core unit used by RuleSet and PipelineState to reason
    about whether a given step can be authorized.
    """

    tier: Tier
    source: str
    content: Any
    timestamp: float = field(default_factory=time.time)
    hash: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "hash", _hash_content(self.content))

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "tier": self.tier.name,
            "source": self.source,
            "content": self.content,
            "timestamp": self.timestamp,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvidenceArtifact:
        tier_str = data.get("tier")
        if tier_str not in TIER_FROM_STRING:
            raise ValueError(f"Unknown tier: {tier_str}")
        tier = TIER_FROM_STRING[tier_str]
        obj = cls(
            tier=tier,
            source=data.get("source", ""),
            content=data.get("content"),
            timestamp=float(data.get("timestamp", time.time())),
        )
        # trust but verify hash
        if obj.hash != data.get("hash"):
            raise ValueError("EvidenceArtifact hash mismatch on deserialization")
        return obj
