"""
provenance-gate: Gate agent actions by evidence quality tier.

This package provides:

- Tiered provenance model (T1-T5).
- RuleSet for validating which tiers can authorize which steps.
- Hallucination defense guards for VERIFY.
- Evidence artifacts and signed terminal capture.
- Append-only ledger with hash chaining and nonce replay protection.
- Pipeline state machine with structural governance.
- Session scopes with actor lineage.
- Authority model and decorators for structural enforcement.

Threat model is documented honestly in SECURITY.md.
"""

from __future__ import annotations

from provenance_gate.actors import Actor
from provenance_gate.authority import (
    AUTHORIZED,
    NOT_AUTHORIZED,
    AuthorityModel,
    AuthorityViolation,
)
from provenance_gate.capture import (
    SignedEvidence,
    TerminalCapture,
    verify_signature,
)
from provenance_gate.evidence import EvidenceArtifact
from provenance_gate.governance import governed_step, requires_authority
from provenance_gate.guards import (
    HallucinationViolation,
    check_hallucination_defense,
    guard_step,
    guard_verify,
)
from provenance_gate.ledger import AppendOnlyLedger, LedgerIntegrityError
from provenance_gate.pipeline import PipelineState, PipelineStep, PipelineViolation
from provenance_gate.rules import (
    STEP_REQUIREMENTS,
    VALID_VERIFY_SOURCES,
    RuleSet,
    RuleViolation,
)
from provenance_gate.session import SessionScope, SessionScopeError
from provenance_gate.tiers import (
    TIER_AUTHORIZES,
    TIER_FROM_STRING,
    TIER_LABELS,
    Tier,
)

__version__ = "2.0.0"

__all__ = [
    "AUTHORIZED",
    "NOT_AUTHORIZED",
    "STEP_REQUIREMENTS",
    "TIER_AUTHORIZES",
    "TIER_FROM_STRING",
    "TIER_LABELS",
    "VALID_VERIFY_SOURCES",
    "Actor",
    "AppendOnlyLedger",
    "AuthorityModel",
    "AuthorityViolation",
    "EvidenceArtifact",
    "HallucinationViolation",
    "LedgerIntegrityError",
    "PipelineState",
    "PipelineStep",
    "PipelineViolation",
    "RuleSet",
    "RuleViolation",
    "SessionScope",
    "SessionScopeError",
    "SignedEvidence",
    "TerminalCapture",
    "Tier",
    "check_hallucination_defense",
    "governed_step",
    "guard_step",
    "guard_verify",
    "requires_authority",
    "verify_signature",
]
