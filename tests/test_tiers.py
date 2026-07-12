from provenance_gate.tiers import TIER_AUTHORIZES, Tier


def test_tier_authorization():
    assert TIER_AUTHORIZES[Tier.T1] is True
    assert TIER_AUTHORIZES[Tier.T2] is False
    assert TIER_AUTHORIZES[Tier.T5] is False
