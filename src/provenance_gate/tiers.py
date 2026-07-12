from __future__ import annotations

from enum import Enum


class Tier(Enum):
    """
    Provenance evidence tiers.

    T1 — VERIFIED
        Real, executed, captured evidence. Only T1 can authorize BUILD, VERIFY, COMMIT.

    T2 — LITERATURE
        External sources, papers, documentation. Supports reasoning but cannot authorize.

    T3 — INFERENCE
        Model-generated reasoning or analysis. Supports planning but cannot authorize.

    T4 — HYPOTHESIS
        Speculative reasoning. Supports PLAN and TEST only.

    T5 — BELIEF
        Initial assumptions. Supports SPEC only.
    """

    T1 = 1
    T2 = 2
    T3 = 3
    T4 = 4
    T5 = 5


TIER_LABELS: dict[Tier, str] = {
    Tier.T1: "VERIFIED",
    Tier.T2: "LITERATURE",
    Tier.T3: "INFERENCE",
    Tier.T4: "HYPOTHESIS",
    Tier.T5: "BELIEF",
}

# Only T1 can authorize BUILD, VERIFY, COMMIT
TIER_AUTHORIZES: dict[Tier, bool] = {
    Tier.T1: True,
    Tier.T2: False,
    Tier.T3: False,
    Tier.T4: False,
    Tier.T5: False,
}

# String → Tier enum mapping
TIER_FROM_STRING: dict[str, Tier] = {
    "T1": Tier.T1,
    "T2": Tier.T2,
    "T3": Tier.T3,
    "T4": Tier.T4,
    "T5": Tier.T5,
}
