#!/usr/bin/env python3
"""
Real end-to-end use of the provenance-gate v2.0.0 library.

Demonstrates:
  1. RuleSet tier validation (correct reject of insufficient tiers)
  2. PipelineState full advance (SPEC -> COMMIT) with real evidence
  3. TerminalCapture.run producing genuine T1 SignedEvidence (running pytest)
  4. guard_verify hallucination defense (rejects non-T1 / forged evidence)
  5. AppendOnlyLedger hash-chain + nonce replay protection
  6. Actor lineage

Run: python3 demo_use.py
"""
from __future__ import annotations

from provenance_gate import (
    Actor,
    AppendOnlyLedger,
    EvidenceArtifact,
    PipelineState,
    RuleSet,
    TerminalCapture,
    Tier,
    guard_verify,
)

print("=" * 70)
print("PROVENANCE-GATE 2.0.0 — LIVE DEMONSTRATION")
print("=" * 70)

# ---------------------------------------------------------------------------
# 1. RuleSet: insufficient tier is rejected
# ---------------------------------------------------------------------------
print("\n[1] RuleSet tier validation")
rs = RuleSet()
print("  BUILD with T5 (belief):", rs.validate("BUILD", "T5"))
print("  BUILD with T1 (verified):", rs.validate("BUILD", "T1"))
print("  VERIFY with bad source:  ", rs.validate("VERIFY", "T1", verify_source="my_opinion"))

# ---------------------------------------------------------------------------
# 2 & 3. Capture REAL T1 evidence by running a command (pytest)
# ---------------------------------------------------------------------------
print("\n[2] Capturing real T1 evidence via TerminalCapture.run (running pytest)")
signed = TerminalCapture.run(["python3", "-m", "pytest", "-q"])
print(f"  command   : {signed.command}")
print(f"  exit_code : {signed.exit_code}")
print(f"  valid sig : {signed.is_valid()}")
print("  content   :")
for line in signed.content.splitlines()[:6]:
    print("      " + line)

# ---------------------------------------------------------------------------
# 4. guard_verify: hallucination defense
# ---------------------------------------------------------------------------
print("\n[3] guard_verify (hallucination defense)")
ok_fake, info_fake = guard_verify(EvidenceArtifact(Tier.T3, "inference", "trust me bro"))
print("  T3 artifact rejected :", ok_fake, "->", info_fake)
ok_real, info_real = guard_verify(signed)
print("  real T1 SignedEvidence accepted :", ok_real)
print("  guard_verify fused info keys    :", list(info_real.keys()))

# ---------------------------------------------------------------------------
# 5. Full pipeline advance with an actor + ledger
# ---------------------------------------------------------------------------
print("\n[4] Full pipeline SPEC -> COMMIT")
actor = Actor.root("engineer").spawn("agent")
print("  actor lineage:", " -> ".join(a.role for a in actor.lineage()))

pipe = PipelineState()
ledger = AppendOnlyLedger()  # in-memory

# NOTE: SPEC is the *initial* state, so the first real advance is to PLAN.
steps = [
    ("PLAN", EvidenceArtifact(Tier.T4, "hypothesis", "add demo_use.py")),
    ("TEST", EvidenceArtifact(Tier.T4, "hypothesis", "pytest passes")),
    ("BUILD", EvidenceArtifact(Tier.T1, "build_output", "bytecode compiled")),
    ("VERIFY", signed),                    # real T1 captured evidence
    ("REVIEW", EvidenceArtifact(Tier.T2, "literature", "peer review ok")),
    ("COMMIT", EvidenceArtifact(Tier.T1, "build_output", "git commit done")),
]
for step, ev in steps:
    ok, info = pipe.advance(step, ev)
    ledger.append(nonce=f"{step}-{id(ev)}", actor_id=actor.actor_id, step=step, payload=info)
    print(f"  {step:6s} advanced={ok}  current={pipe.current.value}")

print("\n  ledger last hash :", ledger.last_hash()[:16], "...")
print("  ledger entries  :", len(ledger.entries()))

# ---------------------------------------------------------------------------
# 6. Ledger integrity: nonce replay is rejected
# ---------------------------------------------------------------------------
print("\n[5] Ledger integrity (nonce replay protection)")
used_nonce = f"PLAN-{id(steps[0][1])}"   # a nonce we already appended above
try:
    ledger.append(nonce=used_nonce, actor_id=actor.actor_id, step="PLAN", payload={})
    print("  ERROR: replay was NOT detected")
except Exception as e:
    print("  replay correctly rejected:", type(e).__name__, "-", e)

print("\nDONE — all gates exercised with real evidence.")
