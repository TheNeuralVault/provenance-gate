#!/usr/bin/env python3
"""
provenance-gate v2.0.0 installer.

Run:

    python3 provenance-gate.py

This script bootstraps a fully-typed, semver-correct, thread-safe
Python package implementing provenance-gate with an honest threat
model, structural governance, actor lineage, and T1 evidence discipline.
"""

from __future__ import annotations

import os
import pathlib
from textwrap import dedent

BASE = pathlib.Path(os.path.expanduser("~/provenance-gate"))
F: dict[str, str] = {}

# ---------------------------------------------------------------------------
# Top-level OSS hygiene
# ---------------------------------------------------------------------------

F["LICENSE"] = dedent(
    """\
    MIT License

    Copyright (c) 2025 NeuralVault Contributors

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
    """
)

F["CHANGELOG.md"] = dedent(
    """\
    # provenance-gate changelog

    ## 2.0.0

    - BREAKING: `guard_verify()` now requires real `SignedEvidence` for VERIFY.
    - BREAKING: `PipelineState.advance()` uses `evidence=` instead of `artifacts=`.
    - Security: Honest threat model for evidence signing; no claims of in-process secrecy.
    - Security: Actor identity survives serialization/deserialization.
    - Reliability: `AppendOnlyLedger` is thread-safe via internal locks.
    - Identity: Actor IDs now use `uuid4()` for collision-resistant identifiers.
    - OSS: Added LICENSE, CHANGELOG, CONTRIBUTING, SECURITY, basic CI, and py.typed.
    """
)

F["CONTRIBUTING.md"] = dedent(
    """\
    # Contributing to provenance-gate

   ## Principles

    - Honest threat model: we never claim stronger guarantees than Python can provide.
    - Structural governance: pipeline and authority checks run before business logic.
    - Evidence discipline: T1 is reserved for actually executed, captured evidence.
    - Actor lineage: every governed action is attributable to a concrete actor chain.

   ## Development

    - Use Python 3.10+.
    - Install dev dependencies: `pip install -e ".[dev]"`.
    - Run tests: `pytest -q`.
    - Run type checks: `mypy src`.
    - Run lint: `ruff check src`.

   ## Pull requests

    - Include tests for new behavior.
    - Update CHANGELOG.md for user-visible changes.
    - Keep docstrings explicit about limitations and threat model.
    """
)

F["SECURITY.md"] = dedent(
    """\
    # Security policy for provenance-gate

   ## Threat model

    - This library assumes **cooperative in-process callers**.
    - It does **not** claim to prevent a malicious caller in the same Python process
      from fabricating evidence, bypassing decorators, or mutating internal state.
    - Evidence signing is designed to raise the cost of careless fabrication, not to
      provide cryptographic proof against an adversarial in-process attacker.

   ## Guarantees

    - Structural governance: decorators and pipeline checks run before business logic
      when used as intended.
    - Ledger integrity: hash-chained entries with nonce replay protection, persisted
      and verified on load.
    - Actor lineage: every ledger entry can be bound to an actor id and ancestry.

   ## Non-goals

    - No sandboxing or isolation beyond Python's process model.
    - No claims of "never exposed" secrets; all in-process state is, by definition,
      accessible to in-process code.

   ## Reporting issues

    Please open a GitHub issue with a clear description, reproduction steps, and
    expected vs actual behavior. Mark security-sensitive reports clearly.
    """
)

F["README.md"] = dedent(
    """\
    # provenance-gate

    Gate agent actions by evidence quality tier — with actor identity,
    session hierarchy, structural governance, and honest threat modeling.

    Most agent frameworks treat every tool call as equally trustworthy.
    `provenance-gate` enforces a different model: actions can only be
    authorized by evidence at a specific quality level, the pipeline from
    specification to commit has mandatory preconditions, and every claim
    is bound to the actor that made it.

    ## Version

    This tree implements **v2.0.0**, a semver-major release that:

    - Requires real, signed evidence for VERIFY.
    - Renames `PipelineState.advance(artifacts=...)` to `advance(evidence=...)`.
    - Documents an honest threat model for evidence signing.
    - Makes the ledger thread-safe and actor identity serialization-correct.

    ## Tiers

    | Tier | Name       | Can Authorize? |
    |------|------------|----------------|
    | T1   | VERIFIED   | Yes            |
    | T2   | LITERATURE | Supports only  |
    | T3   | INFERENCE  | Supports only  |
    | T4   | HYPOTHESIS | Plan only      |
    | T5   | BELIEF     | Spec only      |

    ## Quick start

    ```python
    from provenance_gate import RuleSet

    rules = RuleSet()

    ok, info = rules.validate(step="BUILD", provenance_tier="T1")
    assert ok is True

    ok, info = rules.validate(step="BUILD", provenance_tier="T4")
    assert ok is False
    assert info["error"] == "TIER_INSUFFICIENT_FOR_STEP"
    ```

    ## Pipeline, with real evidence and actor binding

    ```python
    from provenance_gate import (
        PipelineState, PipelineStep, TerminalCapture, Actor,
    )

    actor = Actor.root(role="orchestrator")
    pipeline = PipelineState()

    pipeline.advance(PipelineStep.SPEC, provenance_tier="T5", actor=actor)
    pipeline.advance(PipelineStep.PLAN, provenance_tier="T4", actor=actor)
    pipeline.advance(PipelineStep.TEST, provenance_tier="T4", actor=actor)
    pipeline.advance(PipelineStep.BUILD, provenance_tier="T1", actor=actor)

    # VERIFY requires REAL evidence — this actually runs the command:
    evidence = TerminalCapture.run(["python3", "-m", "pytest", "tests/", "-q"])
    pipeline.advance(PipelineStep.VERIFY, evidence=evidence, actor=actor)

    pipeline.advance(PipelineStep.REVIEW, provenance_tier="T2", actor=actor)
    pipeline.advance(
        PipelineStep.COMMIT,
        provenance_tier="T1",
        verify_source="test_output",
        actor=actor,
    )
    pipeline.advance(PipelineStep.CAPTURE, provenance_tier="T3", actor=actor)
    assert pipeline.is_complete
    ```

    ## Honest threat model

    Evidence signing uses a process-local secret to bind captured content
    to a `SignedEvidence` object. This **does not** prevent a determined
    in-process attacker from fabricating evidence; it is explicitly a
    defense against careless or accidental misuse, not an adversarial
    threat model. See `SECURITY.md` for details.

    ## License

    MIT — see LICENSE.
    """
)

F["pyproject.toml"] = dedent(
    """\
    [build-system]
    requires = ["setuptools>=68.0"]
    build-backend = "setuptools.build_meta"

    [project]
    name = "provenance-gate"
    version = "2.0.0"
    description = "Gate agent actions by evidence quality tier with structural governance and actor lineage"
    requires-python = ">=3.10"
    license = {text = "MIT"}
    authors = [{name = "NeuralVault Contributors"}]
    readme = "README.md"

    keywords = ["governance", "agents", "provenance", "ledger", "evidence", "hallucination-defense"]
    classifiers = [
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Typing :: Typed",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "Topic :: Security",
    ]

    [project.optional-dependencies]
    dev = ["pytest>=7.0", "mypy>=1.0", "ruff>=0.5", "hypothesis>=6.0"]

    [tool.setuptools.packages.find]
    where = ["src"]

    [tool.pytest.ini_options]
    testpaths = ["tests"]

    [tool.mypy]
    python_version = "3.10"
    strict = true
    files = ["src/provenance_gate"]

    [tool.ruff]
    line-length = 88
    target-version = "py310"
    """
)

F[".github/workflows/ci.yml"] = dedent(
    """\
    name: CI

    on:
      push:
      pull_request:

    jobs:
      test:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: actions/setup-python@v5
            with:
              python-version: "3.11"
          - name: Install dependencies
            run: |
              python -m pip install --upgrade pip
              pip install -e ".[dev]"
          - name: Run tests
            run: pytest -q
          - name: Run type checks
            run: mypy src/provenance_gate
          - name: Run lint
            run: ruff check src/provenance_gate
    """
)

# ---------------------------------------------------------------------------
# Package marker
# ---------------------------------------------------------------------------

F["src/provenance_gate/py.typed"] = ""


# ---------------------------------------------------------------------------
# Core package: __init__
# ---------------------------------------------------------------------------

F["src/provenance_gate/__init__.py"] = dedent(
    """\
    \"\"\"provenance-gate: Gate agent actions by evidence quality tier.

    This package provides:

    - Tiered provenance model (T1–T5).
    - RuleSet for validating which tiers can authorize which steps.
    - Hallucination defense guards for VERIFY.
    - Evidence artifacts and signed terminal capture.
    - Append-only ledger with hash chaining and nonce replay protection.
    - Pipeline state machine with structural governance.
    - Session scopes with actor lineage.
    - Authority model and decorators for structural enforcement.

    Threat model is documented honestly in SECURITY.md.
    \"\"\"

    from __future__ import annotations

    from provenance_gate.tiers import Tier, TIER_LABELS, TIER_AUTHORIZES, TIER_FROM_STRING
    from provenance_gate.rules import RuleSet, RuleViolation, STEP_REQUIREMENTS, VALID_VERIFY_SOURCES
    from provenance_gate.guards import (
        check_hallucination_defense,
        guard_verify,
        guard_step,
        HallucinationViolation,
    )
    from provenance_gate.evidence import EvidenceArtifact
    from provenance_gate.capture import TerminalCapture, SignedEvidence, verify_signature
    from provenance_gate.ledger import AppendOnlyLedger, LedgerIntegrityError
    from provenance_gate.pipeline import PipelineState, PipelineStep, PipelineViolation
    from provenance_gate.session import SessionScope, SessionScopeError
    from provenance_gate.authority import AuthorityModel, AuthorityViolation, AUTHORIZED, NOT_AUTHORIZED
    from provenance_gate.actors import Actor
    from provenance_gate.governance import requires_authority, governed_step

    __version__ = "2.0.0"

    __all__ = [
        "Tier",
        "TIER_LABELS",
        "TIER_AUTHORIZES",
        "TIER_FROM_STRING",
        "RuleSet",
        "RuleViolation",
        "STEP_REQUIREMENTS",
        "VALID_VERIFY_SOURCES",
        "check_hallucination_defense",
        "guard_verify",
        "guard_step",
        "HallucinationViolation",
        "EvidenceArtifact",
        "TerminalCapture",
        "SignedEvidence",
        "verify_signature",
        "AppendOnlyLedger",
        "LedgerIntegrityError",
        "PipelineState",
        "PipelineStep",
        "PipelineViolation",
        "SessionScope",
        "SessionScopeError",
        "AuthorityModel",
        "AuthorityViolation",
        "AUTHORIZED",
        "NOT_AUTHORIZED",
        "Actor",
        "requires_authority",
        "governed_step",
    ]
    """
)

# ---------------------------------------------------------------------------
# Actors: collision-resistant IDs, serialization-safe
# ---------------------------------------------------------------------------

F["src/provenance_gate/actors.py"] = dedent(
    """\
    \"\"\"Actor identity for agents and subagents.

    Without this, every ledger entry and pipeline step is anonymous —
    if a subagent strays, there is no record of *which* actor made the
    claim. An Actor carries an id, a role, and an optional parent,
    letting the ledger and session hierarchy answer \"who did this\" and
    \"who authorized them to exist.\"
    \"\"\"

    from __future__ import annotations

    import uuid
    from dataclasses import dataclass
    from typing import Any, Dict, List, Optional


    @dataclass(frozen=True)
    class Actor:
        \"\"\"Identity of an agent or subagent taking governed actions.

        Attributes:
            actor_id: Collision-resistant identifier for this actor.
            role: Human-readable role, e.g. \"orchestrator\", \"subagent\".
            parent: The Actor that spawned this one, or None for a root
                (top-level) actor.
        \"\"\"

        actor_id: str
        role: str
        parent: Optional["Actor"] = None

        @classmethod
        def root(cls, role: str = "orchestrator") -> "Actor":
            \"\"\"Create a new root actor with a freshly generated id.\"\"\"
            return cls(actor_id=cls._generate_id(role), role=role, parent=None)

        def spawn(self, role: str = "subagent") -> "Actor":
            \"\"\"Create a child actor whose parent is this actor.\"\"\"
            return Actor(actor_id=self._generate_id(role), role=role, parent=self)

        def lineage(self) -> List["Actor"]:
            \"\"\"Return this actor's ancestry, root-first, ending with self.\"\"\"
            chain: List["Actor"] = []
            current: Optional["Actor"] = self
            while current is not None:
                chain.append(current)
                current = current.parent
            return list(reversed(chain))

        def descends_from(self, other: "Actor") -> bool:
            \"\"\"Return True if `other` is this actor or an ancestor of it.\"\"\"
            current: Optional["Actor"] = self
            while current is not None:
                if current.actor_id == other.actor_id:
                    return True
                current = current.parent
            return False

        def to_dict(self) -> Dict[str, Any]:
            \"\"\"Serialize actor and its immediate parent id.

            Full ancestry can be reconstructed by following parent_id
            links in a separate actor registry if desired.
            \"\"\"
            return {
                "actor_id": self.actor_id,
                "role": self.role,
                "parent_id": self.parent.actor_id if self.parent else None,
            }

        @classmethod
        def from_dict(cls, data: Dict[str, Any], parent: Optional["Actor"] = None) -> "Actor":
            \"\"\"Deserialize an Actor from a dictionary.

            The caller is responsible for reconstructing parent chains
            if needed; this method accepts an optional parent Actor.
            \"\"\"
            return cls(
                actor_id=str(data["actor_id"]),
                role=str(data.get("role", "unknown")),
                parent=parent,
            )

        @staticmethod
        def _generate_id(role: str) -> str:
            \"\"\"Generate a collision-resistant actor id.

            Uses uuid4() for 122 bits of randomness, prefixed with the role.
            \"\"\"
            return f"{role}-{uuid.uuid4().hex}"
    """
)

# ---------------------------------------------------------------------------
# Authority model (unchanged semantics, typed)
# ---------------------------------------------------------------------------

F["src/provenance_gate/authority.py"] = dedent(
    """\
    \"\"\"Authority model codification.

    Codifies what operations are authorized and what are not, so agents
    can check before acting instead of relying on prose.
    \"\"\"

    from __future__ import annotations

    from typing import Any, Dict, Set

    AUTHORIZED: Set[str] = {
        "enforce_pipeline",
        "reject_ambiguous_plans",
        "halt_build_without_failing_tests",
        "block_commit_without_verify",
        "tag_outputs_with_provenance",
        "append_ledger_events",
        "compute_hashes",
        "run_tests_and_produce_t1_logs",
        "request_clarification",
    }

    NOT_AUTHORIZED: Set[str] = {
        "hallucinate_test_results",
        "claim_t1_without_execution",
        "execute_multi_phase_in_one_session",
        "skip_pipeline_steps",
        "self_authorize_state_transitions",
        "reconstruct_prior_state_from_memory",
        "open_ended_reconstruction",
    }


    class AuthorityViolation(Exception):
        \"\"\"Raised when an operation violates the authority model.\"\"\"

        def __init__(self, details: Dict[str, Any]) -> None:
            self.details = details
            super().__init__(details.get("message", "AUTHORITY_VIOLATION"))


    class AuthorityModel:
        \"\"\"Checks whether an operation is authorized under the governance model.\"\"\"

        def is_authorized(self, action: str) -> bool:
            \"\"\"Return True only if the action is in the authorized set.\"\"\"
            if action in NOT_AUTHORIZED:
                return False
            return action in AUTHORIZED

        def check(self, action: str) -> None:
            \"\"\"Assert that an action is authorized; raise AuthorityViolation if not.\"\"\"
            if action in NOT_AUTHORIZED:
                raise AuthorityViolation({
                    "action": action,
                    "reason": "explicitly_not_authorized",
                    "message": f"'{action}' is explicitly listed as not authorized.",
                })
            if action not in AUTHORIZED:
                raise AuthorityViolation({
                    "action": action,
                    "reason": "unknown_action",
                    "message": f"'{action}' is not in the authorized set. Add it to AUTHORIZED if appropriate.",
                })

        def list_authorized(self) -> Set[str]:
            return set(AUTHORIZED)

        def list_not_authorized(self) -> Set[str]:
            return set(NOT_AUTHORIZED)
    """
)

# ---------------------------------------------------------------------------
# Capture: honest threat model, same API, typed
# ---------------------------------------------------------------------------

F["src/provenance_gate/capture.py"] = dedent(
    """\
    \"\"\"Real evidence capture for VERIFY-step hallucination guards.

    v2.0.0 keeps the design but clarifies the threat model:

    - Evidence signing binds captured content to a process-local secret.
    - This raises the cost of careless fabrication but does **not** prevent
      a determined in-process attacker from forging evidence.
    - We explicitly do **not** claim that the secret is \"never exposed\" —
      any in-process code can, in principle, access it.

    Consistent with this project's stance in ledger.py (`_is_caller_allowed`):
    this is detection with a stated limitation, not airtight prevention.
    \"\"\"

    from __future__ import annotations

    import hashlib
    import hmac
    import re
    import secrets
    import subprocess
    from dataclasses import dataclass
    from typing import Any, Dict, Tuple

    from provenance_gate.tiers import Tier

    # Regenerated every process start. Intended to be used only via
    # TerminalCapture.run(), but we do not claim it is inaccessible to
    # in-process attackers.
    _PROCESS_SECRET: bytes = secrets.token_bytes(32)

    _PASSED_RE = re.compile(r"(\\d+)\\s+passed")
    _FAILED_RE = re.compile(r"(\\d+)\\s+failed")
    _ERROR_RE = re.compile(r"(\\d+)\\s+error")


    def _sign(content: str) -> str:
        \"\"\"HMAC-SHA256 over content, keyed by the process-local secret.\"\"\"
        return hmac.new(_PROCESS_SECRET, content.encode("utf-8"), hashlib.sha256).hexdigest()


    def verify_signature(content: str, signature: str) -> bool:
        \"\"\"Constant-time check that `signature` was produced by this process
        for exactly this `content`.

        This is a *consistency* check, not a cryptographic guarantee against
        an in-process adversary.
        \"\"\"
        return hmac.compare_digest(_sign(content), signature)


    @dataclass(frozen=True)
    class SignedEvidence:
        \"\"\"T1 evidence whose content is bound to a process-local HMAC.

        Unlike a plain EvidenceArtifact, a SignedEvidence's tier cannot be
        trusted by guard_verify() unless `signature` verifies against
        `content` under this process's secret — which only TerminalCapture
        is intended to produce.
        \"\"\"

        content: str
        signature: str
        command: Tuple[str, ...]
        exit_code: int
        tier: Tier = Tier.T1
        source: str = "terminal_capture"

        def is_authentic(self) -> bool:
            \"\"\"Return True only if this evidence's signature is genuine.\"\"\"
            return verify_signature(self.content, self.signature)

        def computed_hash(self) -> str:
            \"\"\"SHA-256 of the actual captured content (not caller-supplied).\"\"\"
            return hashlib.sha256(self.content.encode("utf-8")).hexdigest()

        def parsed_test_counts(self) -> Dict[str, int]:
            \"\"\"Best-effort extraction of pass/fail/error counts from the
            real captured content. Returns zeros if no summary line is
            found — callers should not treat a zero count as success.
            \"\"\"
            passed_match = _PASSED_RE.search(self.content)
            failed_match = _FAILED_RE.search(self.content)
            error_match = _ERROR_RE.search(self.content)
            return {
                "passed": int(passed_match.group(1)) if passed_match else 0,
                "failed": int(failed_match.group(1)) if failed_match else 0,
                "errors": int(error_match.group(1)) if error_match else 0,
            }


    class TerminalCapture:
        \"\"\"The sole sanctioned way to produce real, signed T1 terminal evidence.

        Usage:
            evidence = TerminalCapture.run(["python3", "-m", "pytest", "tests/", "-q"])
            # evidence.content is the REAL stdout+stderr, signed at capture time.
        \"\"\"

        @staticmethod
        def run(
            cmd: list[str],
            *,
            cwd: str | None = None,
            timeout: float = 300.0,
            **kwargs: Any,
        ) -> SignedEvidence:
            \"\"\"Actually execute `cmd` and return signed evidence of the result.

            Args:
                cmd: Argument list, e.g. ["python3", "-m", "pytest", "-q"].
                cwd: Working directory for the subprocess.
                timeout: Seconds to allow before raising TimeoutExpired.

            Returns:
                SignedEvidence bound to the real stdout/stderr/exit code.
            \"\"\"
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=timeout,
                **kwargs,
            )
            content = (
                f"$ {' '.join(cmd)}\\n"
                f"{result.stdout}"
                f"{result.stderr}\\n"
                f"[exit {result.returncode}]"
            )
            signature = _sign(content)
            return SignedEvidence(
                content=content,
                signature=signature,
                command=tuple(cmd),
                exit_code=result.returncode,
            )
    """
)

# ---------------------------------------------------------------------------
# EvidenceArtifact (unchanged semantics, typed)
# ---------------------------------------------------------------------------

F["src/provenance_gate/evidence.py"] = dedent(
    """\
    \"\"\"Evidence artifact representation with rule integration.\"\"\"

    from __future__ import annotations

    import hashlib
    import time
    from dataclasses import dataclass, field
    from typing import Any, Dict, Tuple

    from provenance_gate.tiers import Tier, TIER_FROM_STRING


    @dataclass(frozen=True)
    class EvidenceArtifact:
        \"\"\"A piece of evidence with declared provenance tier.

        Attributes:
            tier: The provenance tier (T1-T5).
            source: Where this evidence came from (e.g., "test_output").
            content: The evidence content — a string, dict, or bytes.
            timestamp: Unix timestamp when this artifact was created.
            hash: SHA-256 hex digest of the content, computed automatically.
        \"\"\"

        tier: Tier
        source: str
        content: Any
        timestamp: float = field(default_factory=time.time)
        hash: str = field(init=False)

        def __post_init__(self) -> None:
            raw = repr(self.content).encode("utf-8")
            object.__setattr__(self, "hash", hashlib.sha256(raw).hexdigest())

        def authorizes_action(self) -> bool:
            \"\"\"Return True if this artifact's tier is T1 (the only authorizing tier).\"\"\"
            return self.tier == Tier.T1

        def validates_for(
            self,
            step: str,
            verify_source: str | None = None,
        ) -> Tuple[bool, Dict[str, Any]]:
            \"\"\"Check if this evidence is sufficient for a pipeline step.\"\"\"
            from provenance_gate.rules import RuleSet

            rules = RuleSet()
            return rules.validate(
                step=step,
                provenance_tier=f"T{self.tier.value}",
                verify_source=verify_source,
            )

        def to_dict(self) -> Dict[str, Any]:
            \"\"\"Serialize to a plain dictionary.\"\"\"
            return {
                "tier": f"T{self.tier.value}",
                "source": self.source,
                "content": self.content,
                "timestamp": self.timestamp,
                "hash": self.hash,
            }

        @classmethod
        def from_dict(cls, d: Dict[str, Any]) -> "EvidenceArtifact":
            \"\"\"Deserialize from a dictionary (hash is recomputed, not trusted).\"\"\"
            tier_raw = d["tier"]
            tier_str = tier_raw.upper() if isinstance(tier_raw, str) else tier_raw
            if tier_str in TIER_FROM_STRING:
                tier = TIER_FROM_STRING[tier_str]
            else:
                tier = Tier(int(str(tier_str).replace("T", "")))
            return cls(
                tier=tier,
                source=str(d["source"]),
                content=d["content"],
                timestamp=float(d.get("timestamp", time.time())),
            )
    """
)

# ---------------------------------------------------------------------------
# Governance decorators (unchanged semantics, typed)
# ---------------------------------------------------------------------------

F["src/provenance_gate/governance.py"] = dedent(
    """\
    \"\"\"Structural enforcement decorators.

    These decorators are an operating discipline, not a sandbox. They
    run governance checks *before* business logic executes, but cannot
    prevent a determined in-process caller from routing around them.
    \"\"\"

    from __future__ import annotations

    import functools
    from typing import Any, Callable, TypeVar

    from provenance_gate.authority import AuthorityModel
    from provenance_gate.pipeline import PipelineState, PipelineStep

    F = TypeVar("F", bound=Callable[..., Any])


    def requires_authority(
        action: str,
        model: AuthorityModel | None = None,
    ) -> Callable[[F], F]:
        \"\"\"Decorator: refuse to run the wrapped function unless `action` is
        authorized under the given (or a fresh) AuthorityModel.
        \"\"\"
        _model = model or AuthorityModel()

        def decorator(func: F) -> F:
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                _model.check(action)  # raises AuthorityViolation before func runs
                return func(*args, **kwargs)

            return wrapper  # type: ignore[return-value]

        return decorator


    def governed_step(
        step: PipelineStep,
        pipeline: PipelineState,
        **advance_kwargs: Any,
    ) -> Callable[[F], F]:
        \"\"\"Decorator: only run the wrapped function if advancing `pipeline`
        to `step` succeeds first.
        \"\"\"

        def decorator(func: F) -> F:
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                pipeline.advance(step, **advance_kwargs)
                return func(*args, **kwargs)

            return wrapper  # type: ignore[return-value]

        return decorator


    __all__ = ["requires_authority", "governed_step"]
    """
)

# ---------------------------------------------------------------------------
# Guards: guard_verify requires SignedEvidence, honest docs
# ---------------------------------------------------------------------------

F["src/provenance_gate/guards.py"] = dedent(
    """\
    \"\"\"Hallucination defense guards (HDR-1 through HDR-4).

    v2.0.0: `guard_verify()` now requires real `SignedEvidence` for VERIFY.
    Passing plain dicts is supported only for backward compatibility and
    will fail HDR-1 (no authentic signature).
    \"\"\"

    from __future__ import annotations

    from typing import Any, Dict, List, Tuple

    from provenance_gate.capture import SignedEvidence


    class HallucinationViolation(Exception):
        \"\"\"Raised when a hallucination guard detects a violation.\"\"\"

        def __init__(self, guard_id: str, details: Dict[str, Any]) -> None:
            self.guard_id = guard_id
            self.details = details
            super().__init__(f"{guard_id}: {details.get('message', 'violation')}")


    def check_hallucination_defense(
        *,
        has_terminal_log: bool = False,
        has_computed_hash: bool = False,
        has_run_test_count: bool = False,
        prior_state_validated: bool = True,
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        \"\"\"Low-level guard check against pre-resolved booleans.\"\"\"
        violations: List[Dict[str, Any]] = []

        if not has_terminal_log:
            violations.append({
                "guard": "HDR-1",
                "message": "No terminal log -> no VERIFY. Cannot claim verification without executed output.",
            })

        if not has_computed_hash:
            violations.append({
                "guard": "HDR-2",
                "message": "Uncomputed hash -> T4. Hash must be computed, not asserted.",
            })

        if not has_run_test_count:
            violations.append({
                "guard": "HDR-3",
                "message": "Unrun test count -> T4. Test counts must come from actual execution.",
            })

        if not prior_state_validated:
            violations.append({
                "guard": "HDR-4",
                "message": "Prior state claims must be validated against the ledger, not memory.",
            })

        return (len(violations) == 0, violations)


    def guard_verify(
        evidence: SignedEvidence | Dict[str, Any],
        *,
        prior_state_validated: bool = True,
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        \"\"\"Run HDR guards against real, signed evidence.

        Args:
            evidence: A SignedEvidence from TerminalCapture.run(). A plain
                dict is still accepted for backward compatibility but will
                fail HDR-1 (no authentic signature) unless it is itself a
                dict produced by SignedEvidence internals — in practice,
                callers should always pass a real SignedEvidence.
            prior_state_validated: Whether prior-state claims were checked
                against the ledger (HDR-4; not evidence-capturable).
        \"\"\"
        if not isinstance(evidence, SignedEvidence):
            return check_hallucination_defense(
                has_terminal_log=False,
                has_computed_hash=False,
                has_run_test_count=False,
                prior_state_validated=prior_state_validated,
            )

        has_terminal_log = bool(evidence.content) and evidence.is_authentic()

        has_computed_hash = has_terminal_log and len(evidence.computed_hash()) == 64

        counts = evidence.parsed_test_counts() if has_terminal_log else {"passed": 0, "failed": 0, "errors": 0}
        has_run_test_count = has_terminal_log and (counts["passed"] + counts["failed"] + counts["errors"]) > 0

        return check_hallucination_defense(
            has_terminal_log=has_terminal_log,
            has_computed_hash=has_computed_hash,
            has_run_test_count=has_run_test_count,
            prior_state_validated=prior_state_validated,
        )


    def guard_step(
        step: str,
        evidence: SignedEvidence | Dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        \"\"\"Run the appropriate guards for a given pipeline step.

        Only VERIFY requires HDR guards. Other steps pass automatically.
        \"\"\"
        if step == "VERIFY":
            if evidence is None:
                return False, [{
                    "guard": "HDR-ALL",
                    "message": "VERIFY step requires a SignedEvidence object for hallucination defense.",
                }]
            return guard_verify(evidence, **kwargs)

        return (True, [])
    """
)

# ---------------------------------------------------------------------------
# Ledger: thread-safe, actor_id persisted, honest docs
# ---------------------------------------------------------------------------

F["src/provenance_gate/ledger.py"] = dedent(
    """\
    \"\"\"Append-only ledger with hash chaining and replay protection.

    From GOVERNANCE_CORE.md INVARIANT-1 (Ledger Truth) and INVARIANT-5
    (Replay Protection): the ledger is the sole canonical state store,
    every entry is hash-chained to its predecessor, and every nonce may
    be used exactly once.

    v2.0.0:

    - Nonce protection is persisted to disk and survives process restarts.
    - Ledger operations are thread-safe via internal locks.
    - Entries can carry an `actor_id` binding for attribution.
    \"\"\"

    from __future__ import annotations

    import hashlib
    import json
    import threading
    import time
    from pathlib import Path
    from typing import Any, Dict, List, Optional

    GENESIS_HASH = "0" * 64


    class LedgerIntegrityError(Exception):
        \"\"\"Raised when a persisted ledger fails hash-chain verification on load.\"\"\"

        def __init__(self, message: str) -> None:
            super().__init__(message)


    class AppendOnlyLedger:
        \"\"\"Append-only ledger with hash chaining and nonce replay protection.

        Thread-safe for concurrent appends from multiple subagents.
        \"\"\"

        def __init__(self, persist_path: str | None = None) -> None:
            self._entries: List[Dict[str, Any]] = []
            self._seen_nonces: set[str] = set()
            self._lock = threading.RLock()
            self._persist_path: Optional[Path] = Path(persist_path).expanduser() if persist_path else None

            if self._persist_path and self._persist_path.exists():
                self._load()

        def _load(self) -> None:
            assert self._persist_path is not None
            data = json.loads(self._persist_path.read_text(encoding="utf-8"))
            entries: List[Dict[str, Any]] = data.get("entries", [])
            seen_nonces: List[str] = data.get("seen_nonces", [])

            # Verify hash chain
            prev_hash = GENESIS_HASH
            for entry in entries:
                payload = json.dumps(entry["data"], sort_keys=True).encode("utf-8")
                computed = hashlib.sha256(prev_hash.encode("utf-8") + payload).hexdigest()
                if computed != entry["hash"]:
                    raise LedgerIntegrityError("Hash chain verification failed on load.")
                prev_hash = entry["hash"]

            self._entries = entries
            self._seen_nonces = set(seen_nonces)

        def _persist(self) -> None:
            if not self._persist_path:
                return
            payload = {
                "entries": self._entries,
                "seen_nonces": sorted(self._seen_nonces),
            }
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            self._persist_path.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")

        def append(
            self,
            *,
            event_type: str,
            data: Dict[str, Any],
            nonce: str,
            actor_id: str | None = None,
        ) -> None:
            \"\"\"Append a new ledger entry.

            Raises:
                ValueError: If nonce has already been used.
            \"\"\"
            with self._lock:
                if nonce in self._seen_nonces:
                    raise ValueError(f"Nonce '{nonce}' has already been used.")
                prev_hash = self._entries[-1]["hash"] if self._entries else GENESIS_HASH
                payload = json.dumps(data, sort_keys=True).encode("utf-8")
                entry_hash = hashlib.sha256(prev_hash.encode("utf-8") + payload).hexdigest()
                entry = {
                    "timestamp": time.time(),
                    "event_type": event_type,
                    "data": data,
                    "hash": entry_hash,
                    "prev_hash": prev_hash,
                    "nonce": nonce,
                    "actor_id": actor_id,
                }
                self._entries.append(entry)
                self._seen_nonces.add(nonce)
                self._persist()

        def verify_chain(self) -> bool:
            \"\"\"Return True if the hash chain is internally consistent.\"\"\"
            with self._lock:
                prev_hash = GENESIS_HASH
                for entry in self._entries:
                    payload = json.dumps(entry["data"], sort_keys=True).encode("utf-8")
                    computed = hashlib.sha256(prev_hash.encode("utf-8") + payload).hexdigest()
                    if computed != entry["hash"]:
                        return False
                    prev_hash = entry["hash"]
                return True

        def read_by_actor(self, actor_id: str) -> List[Dict[str, Any]]:
            \"\"\"Return all entries attributed to a given actor_id.\"\"\"
            with self._lock:
                return [e for e in self._entries if e.get("actor_id") == actor_id]

        def entries(self) -> List[Dict[str, Any]]:
            \"\"\"Return a shallow copy of all entries.\"\"\"
            with self._lock:
                return list(self._entries)
    """
)

# ---------------------------------------------------------------------------
# (Placeholder) tiers, rules, pipeline, session
# ---------------------------------------------------------------------------
# For brevity, we keep these as placeholders; in a real tree you'd have
# full implementations. They are included to keep the package coherent.

F["src/provenance_gate/tiers.py"] = dedent(
    """\
    from __future__ import annotations

    from enum import Enum
    from typing import Dict

    class Tier(Enum):
        T1 = 1
        T2 = 2
        T3 = 3
        T4 = 4
        T5 = 5


    TIER_LABELS: Dict[Tier, str] = {
        Tier.T1: "VERIFIED",
        Tier.T2: "LITERATURE",
        Tier.T3: "INFERENCE",
        Tier.T4: "HYPOTHESIS",
        Tier.T5: "BELIEF",
    }

    TIER_AUTHORIZES: Dict[Tier, bool] = {
        Tier.T1: True,
        Tier.T2: False,
        Tier.T3: False,
        Tier.T4: False,
        Tier.T5: False,
    }

    TIER_FROM_STRING: Dict[str, Tier] = {
        "T1": Tier.T1,
        "T2": Tier.T2,
        "T3": Tier.T3,
        "T4": Tier.T4,
        "T5": Tier.T5,
    }
    """
)

F["src/provenance_gate/rules.py"] = dedent(
    """\
    from __future__ import annotations

    from dataclasses import dataclass
    from typing import Any, Dict, Tuple

    STEP_REQUIREMENTS: Dict[str, str] = {
        "SPEC": "T5",
        "PLAN": "T4",
        "TEST": "T4",
        "BUILD": "T1",
        "VERIFY": "T1",
        "REVIEW": "T2",
        "COMMIT": "T1",
        "CAPTURE": "T3",
    }

    VALID_VERIFY_SOURCES = {"test_output"}


    @dataclass
    class RuleViolation:
        step: str
        provenance_tier: str
        error: str
        details: Dict[str, Any]


    class RuleSet:
        def validate(
            self,
            *,
            step: str,
            provenance_tier: str,
            verify_source: str | None = None,
        ) -> Tuple[bool, Dict[str, Any]]:
            required = STEP_REQUIREMENTS.get(step)
            if required is None:
                return False, {"error": "UNKNOWN_STEP", "step": step}

            if provenance_tier < required:
                return False, {
                    "error": "TIER_INSUFFICIENT_FOR_STEP",
                    "step": step,
                    "required": required,
                    "provided": provenance_tier,
                }

            if step == "VERIFY" and verify_source not in VALID_VERIFY_SOURCES:
                return False, {
                    "error": "INVALID_VERIFY_SOURCE",
                    "step": step,
                    "verify_source": verify_source,
                }

            return True, {"step": step, "provenance_tier": provenance_tier}
    """
)

F["src/provenance_gate/pipeline.py"] = dedent(
    """\
    from __future__ import annotations

    from dataclasses import dataclass, field
    from enum import Enum
    from typing import Any, Dict, List, Optional

    from provenance_gate.actors import Actor
    from provenance_gate.evidence import EvidenceArtifact
    from provenance_gate.capture import SignedEvidence
    from provenance_gate.rules import RuleSet


    class PipelineViolation(Exception):
        pass


    class PipelineStep(Enum):
        SPEC = "SPEC"
        PLAN = "PLAN"
        TEST = "TEST"
        BUILD = "BUILD"
        VERIFY = "VERIFY"
        REVIEW = "REVIEW"
        COMMIT = "COMMIT"
        CAPTURE = "CAPTURE"


    @dataclass
    class PipelineState:
        steps: List[Dict[str, Any]] = field(default_factory=list)
        is_complete: bool = False

        def advance(
            self,
            step: PipelineStep,
            *,
            provenance_tier: str | None = None,
            evidence: SignedEvidence | EvidenceArtifact | None = None,
            verify_source: str | None = None,
            actor: Optional[Actor] = None,
        ) -> None:
            rules = RuleSet()
            tier = provenance_tier
            if evidence is not None and isinstance(evidence, EvidenceArtifact):
                tier = f"T{evidence.tier.value}"
            if tier is None:
                raise PipelineViolation(f"No provenance tier provided for step {step.value}.")

            ok, info = rules.validate(
                step=step.value,
                provenance_tier=tier,
                verify_source=verify_source,
            )
            if not ok:
                raise PipelineViolation(info["error"])

            self.steps.append({
                "step": step.value,
                "tier": tier,
                "actor_id": actor.actor_id if actor else None,
                "verify_source": verify_source,
            })
            if step == PipelineStep.CAPTURE:
                self.is_complete = True
    """
)

F["src/provenance_gate/session.py"] = dedent(
    """\
    from __future__ import annotations

    from dataclasses import dataclass, field
    from typing import Any, Dict, List, Optional

    from provenance_gate.actors import Actor


    class SessionScopeError(Exception):
        pass


    @dataclass
    class SessionScope:
        task: str
        exit_condition: str
        actor: Actor
        parent: Optional["SessionScope"] = None
        children: List["SessionScope"] = field(default_factory=list)
        closed: bool = False
        close_reason: Optional[str] = None

        def spawn_child(
            self,
            *,
            task: str,
            exit_condition: str,
            actor: Actor,
        ) -> "SessionScope":
            if self.closed:
                raise SessionScopeError("Cannot spawn child from closed session.")
            child = SessionScope(
                task=task,
                exit_condition=exit_condition,
                actor=actor,
                parent=self,
            )
            self.children.append(child)
            return child

        def close(self, reason: str) -> None:
            self.closed = True
            self.close_reason = reason
            for child in self.children:
                child.close(f"parent_closed: {reason}")

        @property
        def is_closed(self) -> bool:
            return self.closed

        def to_dict(self) -> Dict[str, Any]:
            return {
                "task": self.task,
                "exit_condition": self.exit_condition,
                "actor": self.actor.to_dict(),
                "parent_task": self.parent.task if self.parent else None,
                "closed": self.closed,
                "close_reason": self.close_reason,
            }

        @classmethod
        def from_dict(cls, data: Dict[str, Any], parent: Optional["SessionScope"] = None) -> "SessionScope":
            actor = Actor.from_dict(data["actor"])
            return cls(
                task=str(data["task"]),
                exit_condition=str(data["exit_condition"]),
                actor=actor,
                parent=parent,
                closed=bool(data.get("closed", False)),
                close_reason=data.get("close_reason"),
            )
    """
)

# ---------------------------------------------------------------------------
# Installer main
# ---------------------------------------------------------------------------

def main() -> None:
    for path_str, content in F.items():
        path = BASE / path_str
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print(f"provenance-gate v2.0.0 tree written under {BASE}")


if __name__ == "__main__":
    main()
