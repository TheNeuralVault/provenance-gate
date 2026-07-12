"""Fuzz / property tests for the core RuleSet governance invariant.

The structural governance contract that must hold for ANY (tier, step,
verify_source) input:

  - AUTHORIZED  iff  tier.value <= required_tier.value  (lower tier index ==
    higher assurance; T1 is the strongest and the only one that can authorize
    BUILD/VERIFY/COMMIT).
  - Unknown step            -> rejected with INVALID_STEP, never crashes.
  - Unknown tier string     -> rejected with INVALID_TIER, never crashes.
  - VERIFY with a source not in VALID_VERIFY_SOURCES -> rejected.
  - VERIFY with a valid source and sufficient tier -> authorized.

A deterministic, dependency-free fuzz (no Hypothesis required) runs 500 random
combinations so the invariant is exercised on every local run; CI additionally
runs the Hypothesis-based variant when the ``[dev]`` extra is installed.
"""
from __future__ import annotations

import random

from provenance_gate.rules import STEP_REQUIREMENTS, VALID_VERIFY_SOURCES, RuleSet
from provenance_gate.tiers import TIER_FROM_STRING, Tier

_TIERS = list(Tier)
_STEPS = list(STEP_REQUIREMENTS)


def _check(tier: Tier, step: str, verify_source: str | None) -> bool:
    ok, info = RuleSet().validate(step=step, provenance_tier=tier, verify_source=verify_source)
    required = STEP_REQUIREMENTS[step]
    if step == "VERIFY" and verify_source not in VALID_VERIFY_SOURCES:
        assert ok is False and info["error"] == "INVALID_VERIFY_SOURCE"
        return False
    assert ok == (tier.value <= required.value), (tier, step, verify_source, ok, info)
    return bool(ok)


def test_ruleset_known_steps_invariant() -> None:
    """Exhaustive check over every (tier, step) pair for the governance rule."""
    for step in _STEPS:
        for tier in _TIERS:
            # VERIFY additionally needs a valid source.
            if step == "VERIFY":
                for src in VALID_VERIFY_SOURCES:
                    _check(tier, step, src)
            else:
                _check(tier, step, None)


def test_ruleset_rejects_unknown_step_and_tier() -> None:
    ok, info = RuleSet().validate(step="NOPE", provenance_tier=Tier.T1)
    assert ok is False and info["error"] == "INVALID_STEP"
    ok, info = RuleSet().validate(step="BUILD", provenance_tier="ZZ")
    assert ok is False and info["error"] == "INVALID_TIER"


def test_ruleset_fuzz_deterministic() -> None:
    """500 random combinations must all satisfy the invariant; never raise."""
    rng = random.Random(0x5EED)
    for _ in range(500):
        tier = rng.choice(_TIERS)
        step = rng.choice(_STEPS)
        if step == "VERIFY":
            # mix valid and invalid sources
            src = rng.choice([*list(VALID_VERIFY_SOURCES), "bogus", "another"])
        else:
            src = None
        _check(tier, step, src)
    # sanity: the tier-string round-trip used by the real pipeline works
    for name, t in TIER_FROM_STRING.items():
        assert RuleSet().validate("BUILD", name)[0] == (t.value <= Tier.T1.value)
