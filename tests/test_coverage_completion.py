"""Coverage-completion tests targeting previously-uncovered lines across
actors, authority, evidence, governance, guards, ledger, pipeline, rules,
session. Every symbol/signature here was verified against the real source.
"""
from __future__ import annotations

import json

import pytest

from provenance_gate.actors import Actor
from provenance_gate.authority import (
    AUTHORIZED,
    NOT_AUTHORIZED,
    AuthorityModel,
    AuthorityViolation,
)
from provenance_gate.capture import SignedEvidence, TerminalCapture, verify_signature
from provenance_gate.evidence import EvidenceArtifact
from provenance_gate.governance import governed_step, requires_authority
from provenance_gate.guards import (
    check_hallucination_defense,
    guard_step,
    guard_verify,
)
from provenance_gate.ledger import (
    GENESIS_HASH,
    AppendOnlyLedger,
    LedgerEntry,
    LedgerIntegrityError,
)
from provenance_gate.pipeline import PipelineState, PipelineStep
from provenance_gate.rules import RuleSet
from provenance_gate.session import SessionScope, SessionScopeError
from provenance_gate.tiers import Tier

# --------------------------------------------------------------------------
# actors
# --------------------------------------------------------------------------

def test_actor_root_spawn_lineage_and_serialization():
    root = Actor.root("lead")
    child = root.spawn("worker")
    grandchild = child.spawn("helper")

    lineage = grandchild.lineage()
    assert [a.role for a in lineage] == ["lead", "worker", "helper"]
    assert root.parent is None

    d = child.to_dict()
    assert d["role"] == "worker"
    assert d["parent_id"] == root.actor_id

    # root serializes parent_id as None
    assert root.to_dict()["parent_id"] is None

    # from_dict drops parent linkage
    restored = Actor.from_dict(child.to_dict())
    assert restored.actor_id == child.actor_id
    assert restored.parent is None

    # __str__/__repr__ cover both parent and no-parent branches
    assert "role=worker" in str(child)
    assert "parent=None" in str(root)
    assert repr(root) == str(root)


# --------------------------------------------------------------------------
# authority
# --------------------------------------------------------------------------

def test_authority_allowed_forbidden_undeclared():
    m = AuthorityModel()
    ok, info = m.check("enforce_pipeline")
    assert ok and info["status"] == "AUTHORIZED"

    ok, info = m.check("rewrite_ledger_history")
    assert not ok and info["error"] == "ACTION_EXPLICITLY_FORBIDDEN"

    ok, info = m.check("no_such_action")
    assert not ok and info["error"] == "ACTION_NOT_DECLARED"

    assert m.is_authorized("enforce_pipeline") is True
    assert m.is_authorized("rewrite_ledger_history") is False


def test_authority_require_raises_and_custom_sets():
    m = AuthorityModel()
    m.require("enforce_pipeline")  # no raise
    with pytest.raises(PermissionError):
        m.require("hallucinate_test_results")

    custom = AuthorityModel(allowed={"x"}, forbidden={"y"})
    assert custom.is_authorized("x") is True
    assert custom.is_authorized("y") is False
    assert custom.is_authorized("enforce_pipeline") is False

    assert "enforce_pipeline" in AUTHORIZED
    assert "rewrite_ledger_history" in NOT_AUTHORIZED


def test_authority_violation_to_dict():
    v = AuthorityViolation(action="a", error="E", details="d")
    assert v.to_dict() == {"action": "a", "error": "E", "details": "d"}


# --------------------------------------------------------------------------
# evidence
# --------------------------------------------------------------------------

def test_evidence_roundtrip_and_hash_checks():
    ev = EvidenceArtifact(tier=Tier.T4, source="hypothesis", content="plan")
    d = ev.to_dict()
    assert d["tier"] == "T4"
    back = EvidenceArtifact.from_dict(d)
    assert back.tier is Tier.T4
    assert back.content == "plan"

    # bytes content path in _hash_content
    b = EvidenceArtifact(tier=Tier.T1, source="runtime_capture", content=b"raw")
    assert b.hash

    # unknown tier
    with pytest.raises(ValueError):
        EvidenceArtifact.from_dict({"tier": "T9", "content": "x", "hash": "h"})

    # hash mismatch
    bad = ev.to_dict()
    bad["hash"] = "deadbeef"
    with pytest.raises(ValueError):
        EvidenceArtifact.from_dict(bad)


# --------------------------------------------------------------------------
# rules
# --------------------------------------------------------------------------

def test_ruleset_all_branches():
    rs = RuleSet()
    # invalid tier string
    ok, info = rs.validate("BUILD", "TZ")
    assert not ok and info["error"] == "INVALID_TIER"
    # invalid step
    ok, info = rs.validate("NOPE", "T1")
    assert not ok and info["error"] == "INVALID_STEP"
    # verify bad source
    ok, info = rs.validate("VERIFY", "T1", verify_source="opinion")
    assert not ok and info["error"] == "INVALID_VERIFY_SOURCE"
    # verify good source
    ok, info = rs.validate("VERIFY", "T1", verify_source="test_output")
    assert ok
    # tier insufficient
    ok, info = rs.validate("BUILD", "T5")
    assert not ok and info["error"] == "TIER_INSUFFICIENT_FOR_STEP"
    # tier enum accepted directly
    ok, info = rs.validate("BUILD", Tier.T1)
    assert ok and info["status"] == "AUTHORIZED"


# --------------------------------------------------------------------------
# guards
# --------------------------------------------------------------------------

def _t1_signed():
    return TerminalCapture.run(["python", "-c", "print('ok')"])


def test_guard_hallucination_paths():
    # prior state not validated
    ok, info = check_hallucination_defense(None, prior_state_validated=False)
    assert not ok and info["error"] == "PRIOR_STATE_NOT_VALIDATED"
    # no evidence
    ok, info = check_hallucination_defense(None)
    assert not ok and info["error"] == "NO_EVIDENCE_PROVIDED"
    # non-T1 artifact
    ev4 = EvidenceArtifact(tier=Tier.T4, source="hypothesis", content="x")
    ok, info = check_hallucination_defense(ev4)
    assert not ok and info["error"] == "EVIDENCE_NOT_T1"
    # T1 artifact ok
    ev1 = EvidenceArtifact(tier=Tier.T1, source="runtime_capture", content="x")
    ok, info = check_hallucination_defense(ev1)
    assert ok and info["kind"] == "EvidenceArtifact"
    # signed evidence valid
    sig = _t1_signed()
    ok, info = check_hallucination_defense(sig)
    assert ok and info["kind"] == "SignedEvidence"
    # signed evidence invalid
    tampered = SignedEvidence(content="x", signature="bad", command=("c",), exit_code=0)
    ok, info = check_hallucination_defense(tampered)
    assert not ok and info["error"] == "SIGNED_EVIDENCE_INVALID"
    # unsupported type
    ok, info = check_hallucination_defense(object())  # type: ignore[arg-type]
    assert not ok and info["error"] == "UNSUPPORTED_EVIDENCE_TYPE"


def test_guard_verify_and_step():
    ev1 = EvidenceArtifact(tier=Tier.T1, source="runtime_capture", content="x")
    ok, info = guard_verify(ev1)
    assert ok and info["status"] == "AUTHORIZED"

    # signed evidence normalized through to_t1_artifact
    ok, info = guard_verify(_t1_signed())
    assert ok

    # verify guard rejects non-T1 up front
    ev4 = EvidenceArtifact(tier=Tier.T4, source="hypothesis", content="x")
    ok, info = guard_verify(ev4)
    assert not ok

    # guard_step: no evidence
    ok, info = guard_step("BUILD", None)
    assert not ok and info["error"] == "NO_EVIDENCE_PROVIDED"
    # guard_step: insufficient tier
    ok, info = guard_step("BUILD", ev4)
    assert not ok
    # guard_step: ok
    ok, info = guard_step("PLAN", ev4)
    assert ok and info["status"] == "AUTHORIZED"


def test_capture_signature_and_grep():
    sig = _t1_signed()
    assert sig.is_valid()
    assert verify_signature(sig.content, sig.signature)
    assert sig.to_dict()["valid"] is True
    art = sig.to_t1_artifact()
    assert art.tier is Tier.T1
    assert TerminalCapture.grep_output(sig, "ok")
    bad = SignedEvidence(content="x", signature="nope", command=("c",), exit_code=1)
    with pytest.raises(ValueError):
        bad.to_t1_artifact()


# --------------------------------------------------------------------------
# pipeline
# --------------------------------------------------------------------------

def test_pipeline_full_and_error_paths():
    p = PipelineState()
    # invalid step name
    ok, info = p.advance("NOPE", None)
    assert not ok and info["error"] == "INVALID_STEP"
    # out-of-order transition (SPEC -> BUILD)
    ok, info = p.advance("BUILD", None)
    assert not ok and info["error"] == "INVALID_TRANSITION"

    # walk the happy path
    t4 = EvidenceArtifact(tier=Tier.T4, source="hypothesis", content="x")
    t1 = EvidenceArtifact(tier=Tier.T1, source="runtime_capture", content="x")
    t2 = EvidenceArtifact(tier=Tier.T2, source="docs", content="x")
    assert p.advance("PLAN", t4)[0]
    assert p.advance("TEST", t4)[0]
    assert p.advance("BUILD", t1)[0]
    assert p.advance("VERIFY", t1)[0]
    assert p.advance("REVIEW", t2)[0]
    assert p.advance("COMMIT", t1)[0]
    assert p.current is PipelineStep.COMMIT
    assert p.last()["step"] == "COMMIT"

    # can_advance false for invalid + no-next
    assert p.can_advance("NOPE") is False
    assert PipelineState()._next_step(PipelineStep.COMMIT) is None

    # empty history last()
    assert PipelineState().last() is None


# --------------------------------------------------------------------------
# ledger
# --------------------------------------------------------------------------

def test_ledger_append_entries_replay_and_persist(tmp_path):
    path = tmp_path / "l.json"
    led = AppendOnlyLedger(persist_path=str(path))
    assert led.last_hash() == GENESIS_HASH
    led.append(nonce="n1", actor_id="a", step="PLAN", payload={"k": 1})
    led.append(nonce="n2", actor_id="a", step="BUILD", payload={"k": 2})
    assert len(led.entries()) == 2
    assert led.last_hash() != GENESIS_HASH

    # nonce replay in-memory
    with pytest.raises(LedgerIntegrityError):
        led.append(nonce="n1", actor_id="a", step="X", payload={})

    # reload clean
    led2 = AppendOnlyLedger(persist_path=str(path))
    assert len(led2.entries()) == 2

    # entry roundtrip
    e = led.entries()[0]
    assert LedgerEntry.from_dict(e.to_dict()).hash == e.hash


def test_ledger_tamper_detection(tmp_path):
    path = tmp_path / "l.json"
    led = AppendOnlyLedger(persist_path=str(path))
    led.append(nonce="n1", actor_id="a", step="PLAN", payload={"k": 1})
    data = json.loads(path.read_text())
    data[0]["payload"]["k"] = 999  # mutate without recomputing hash
    path.write_text(json.dumps(data))
    with pytest.raises(LedgerIntegrityError):
        AppendOnlyLedger(persist_path=str(path))


def test_ledger_broken_chain(tmp_path):
    path = tmp_path / "l.json"
    led = AppendOnlyLedger(persist_path=str(path))
    led.append(nonce="n1", actor_id="a", step="PLAN", payload={})
    led.append(nonce="n2", actor_id="a", step="BUILD", payload={})
    data = json.loads(path.read_text())
    # break prev_hash linkage on 2nd entry, then re-sign that entry so the
    # hash check passes but the chain check fails
    data[1]["prev_hash"] = GENESIS_HASH
    data[1]["hash"] = LedgerEntry.compute_hash(
        nonce=data[1]["nonce"], actor_id=data[1]["actor_id"], step=data[1]["step"],
        payload=data[1]["payload"], timestamp=data[1]["timestamp"],
        prev_hash=GENESIS_HASH,
    )
    path.write_text(json.dumps(data))
    with pytest.raises(LedgerIntegrityError):
        AppendOnlyLedger(persist_path=str(path))


# --------------------------------------------------------------------------
# session
# --------------------------------------------------------------------------

def test_session_advance_record_and_helpers(tmp_path):
    led = AppendOnlyLedger(persist_path=str(tmp_path / "s.json"))
    sess = SessionScope.create(Actor.root("lead"), ledger=led, metadata={"env": "test"})
    assert sess.current_step() == "SPEC"
    assert sess.lineage()[0].role == "lead"

    t4 = EvidenceArtifact(tier=Tier.T4, source="hypothesis", content="x")
    info = sess.advance("PLAN", t4)
    assert info["status"] == "ADVANCED"
    assert sess.current_step() == "PLAN"
    assert sess.last_record()["step"] == "PLAN"
    assert len(led.entries()) == 1  # recorded

    sess.attach_metadata("foo", "bar")
    assert sess.metadata["foo"] == "bar"
    sess.require_step("PLAN")
    with pytest.raises(SessionScopeError):
        sess.require_step("BUILD")

    # child session inherits ledger + metadata copy
    child = sess.spawn_child("worker")
    assert child.actor.parent is sess.actor
    assert child.ledger is led
    assert child.metadata == sess.metadata and child.metadata is not sess.metadata


def test_session_advance_failure_raises():
    sess = SessionScope.create(Actor.root("lead"))
    with pytest.raises(SessionScopeError):
        sess.advance("BUILD", None)  # out of order + no evidence


# --------------------------------------------------------------------------
# governance (decorators)
# --------------------------------------------------------------------------

def test_requires_authority_decorator():
    @requires_authority("enforce_pipeline")
    def ok_fn():
        return "done"

    assert ok_fn() == "done"

    @requires_authority("rewrite_ledger_history")
    def bad_fn():
        return "nope"

    with pytest.raises(PermissionError):
        bad_fn()


def test_governed_step_decorator_paths():
    pipe = PipelineState()
    t4 = EvidenceArtifact(tier=Tier.T4, source="hypothesis", content="x")

    @governed_step("PLAN", pipe)
    def plan_step(*, evidence, session=None):
        return {"result": "ok"}

    out = plan_step(evidence=t4)
    assert out["result"] == "ok"
    assert out["_governance"]["pipeline"]["status"] == "ADVANCED"

    # session metadata attach branch
    sess = SessionScope.create(Actor.root("lead"))
    pipe2 = PipelineState()

    @governed_step("PLAN", pipe2)
    def plan2(*, evidence, session=None):
        return {"ok": True}

    plan2(evidence=t4, session=sess)
    assert sess.metadata["last_governed_step"] == "PLAN"

    # authority denial
    denier = AuthorityModel(allowed=set(), forbidden=set())

    @governed_step("PLAN", PipelineState(), authority=denier)
    def denied(*, evidence, session=None):
        return {}

    with pytest.raises(PermissionError):
        denied(evidence=t4)

    # pipeline violation (out of order) -> RuntimeError
    pipe3 = PipelineState()

    @governed_step("BUILD", pipe3)
    def build_bad(*, evidence, session=None):
        return {}

    with pytest.raises(RuntimeError):
        build_bad(evidence=t4)
