from provenance_gate.rules import RuleSet
from provenance_gate.tiers import Tier


def test_ruleset_build_requires_t1():
    rules = RuleSet()
    ok, info = rules.validate("BUILD", Tier.T1)
    assert ok

    ok, info = rules.validate("BUILD", Tier.T2)
    assert not ok
    assert info["error"] == "TIER_INSUFFICIENT_FOR_STEP"
