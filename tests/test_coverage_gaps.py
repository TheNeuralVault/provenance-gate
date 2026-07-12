"""Closes the final uncovered core branches.

Targets (verified missing prior to this file via ``pytest --cov --cov-report=term-missing``):
  - guards.py:137   guard_verify returns False when RuleSet rejects the VERIFY source
  - ledger.py:153   AppendOnlyLedger.load rejects a persisted ledger with a replayed nonce
  - pipeline.py:128 VERIFY branch fails when guard_verify rejects the evidence
  - pipeline.py:134 non-VERIFY branch fails when guard_step rejects the evidence tier
  - pipeline.py:160 can_advance returns the valid-transition result for a real step
"""
from __future__ import annotations

import json

import pytest

from provenance_gate.evidence import EvidenceArtifact
from provenance_gate.guards import guard_verify
from provenance_gate.ledger import AppendOnlyLedger, GENESIS_HASH, LedgerEntry
from provenance_gate.pipeline import PipelineState
from provenance_gate.tiers import Tier


def _t1(source: str = "runtime_capture") -> EvidenceArtifact:
    return EvidenceArtifact(tier=Tier.T1, source=source, content="ok")


def test_guard_verify_rejects_invalid_verify_source() -> None:
    # T1 evidence but a source NOT in VALID_VERIFY_SOURCES -> RuleSet fails,
    # hitting guards.py:137 (return False, rule_info).
    ev = EvidenceArtifact(tier=Tier.T1, source="bogus_source", content="ok")
    ok, info = guard_verify(ev, prior_state_validated=True)
    assert ok is False
    assert info["error"] == "INVALID_VERIFY_SOURCE"


def test_pipeline_verify_branch_fails_on_non_t1() -> None:
    # Drive the pipeline to BUILD, then attempt VERIFY with a T4 artifact.
    # guard_verify rejects it -> pipeline.py:128 (return False, info).
    p = PipelineState()
    assert p.advance("PLAN", _t1())[0]
    assert p.advance("TEST", _t1())[0]
    assert p.advance("BUILD", _t1())[0]
    weak = EvidenceArtifact(tier=Tier.T4, source="hypothesis", content="x")
    ok, info = p.advance("VERIFY", weak)
    assert ok is False
    assert info["error"] == "EVIDENCE_NOT_T1"


def test_pipeline_non_verify_branch_fails_on_insufficient_tier() -> None:
    # At PLAN, attempt TEST with a T5 artifact -> guard_step rejects it,
    # hitting pipeline.py:134 (return False, info).
    p = PipelineState()
    assert p.advance("PLAN", _t1())[0]
    weak = EvidenceArtifact(tier=Tier.T5, source="belief", content="x")
    ok, info = p.advance("TEST", weak)
    assert ok is False
    assert info["error"] == "TIER_INSUFFICIENT_FOR_STEP"


def test_pipeline_can_advance_valid_step() -> None:
    # At SPEC, PLAN is the valid next step -> pipeline.py:160
    # (return self._is_valid_transition(step_enum)) is exercised with a hit.
    p = PipelineState()
    assert p.current.value == "SPEC"
    assert p.can_advance("PLAN") is True
    # A step that is not the immediate successor must be rejected.
    assert p.can_advance("TEST") is False


def test_ledger_load_rejects_nonce_replay(tmp_path) -> None:
    # Build a persisted ledger whose two entries share a nonce but are otherwise
    # internally consistent (valid hashes, valid prev_hash chain). Loading it must
    # raise at ledger.py:153 ("Ledger nonce replay detected on load").
    path = tmp_path / "ledger.json"
    e1 = LedgerEntry.create("dup", "actor", "SPEC", {"x": 1}, GENESIS_HASH)
    e2 = LedgerEntry.create("dup", "actor", "PLAN", {"y": 2}, e1.hash)
    path.write_text(
        json.dumps([e1.to_dict(), e2.to_dict()], sort_keys=True),
        encoding="utf-8",
    )
    with pytest.raises(Exception) as exc:
        AppendOnlyLedger(path)
    assert "nonce replay" in str(exc.value)
