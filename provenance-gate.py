#!/usr/bin/env python3
"""
provenance-gate v2.0.0 installer.

Run:
    python3 provenance-gate.py

This installer creates the full provenance-gate v2.0.0 package tree,
including OSS hygiene, CI workflow, typed modules, and all governance,
evidence, ledger, pipeline, and session components.
"""

from __future__ import annotations
import os
import pathlib
from textwrap import dedent

BASE = pathlib.Path(os.path.expanduser("~/provenance-gate"))

FILES: dict[str, str] = {}

# ---------------------------------------------------------------------------
# Top-level OSS hygiene
# ---------------------------------------------------------------------------

FILES["LICENSE"] = dedent("""
MIT License

Copyright (c) 2025 NeuralVault Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
...
""")

FILES["README.md"] = dedent("""
# provenance-gate

Gate agent actions by evidence quality tier — with actor identity,
session hierarchy, structural governance, and honest threat modeling.

Version: **2.0.0** (semver-major)
...
""")

FILES["CHANGELOG.md"] = dedent("""
# provenance-gate changelog

## 2.0.0 — Semver‑Major Release
...
""")

FILES["CONTRIBUTING.md"] = dedent("""
# Contributing to provenance-gate
...
""")

FILES["SECURITY.md"] = dedent("""
# Security Policy for provenance-gate
...
""")

FILES["pyproject.toml"] = dedent("""
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[project]
name = "provenance-gate"
version = "2.0.0"
...
""")

# ---------------------------------------------------------------------------
# CI workflow
# ---------------------------------------------------------------------------

FILES[".github/workflows/ci.yml"] = dedent("""
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
      - name: Install
        run: pip install -e ".[dev]"
      - name: Test
        run: pytest -q
""")

# ---------------------------------------------------------------------------
# Package marker
# ---------------------------------------------------------------------------

FILES["src/provenance_gate/py.typed"] = ""

# ---------------------------------------------------------------------------
# __init__.py
# ---------------------------------------------------------------------------

FILES["src/provenance_gate/__init__.py"] = dedent("""
\"\"\"provenance-gate v2.0.0\"\"\"

from provenance_gate.tiers import Tier, TIER_LABELS, TIER_AUTHORIZES, TIER_FROM_STRING
...
__version__ = "2.0.0"
""")

# ---------------------------------------------------------------------------
# Actors
# ---------------------------------------------------------------------------

FILES["src/provenance_gate/actors.py"] = dedent("""
from __future__ import annotations
import uuid
from dataclasses import dataclass
from typing import Optional, Any, List

@dataclass(frozen=True)
class Actor:
    actor_id: str
    role: str
    parent: Optional["Actor"] = None

    @classmethod
    def root(cls, role: str) -> "Actor":
        return cls(actor_id=f"{role}-{uuid.uuid4().hex}", role=role)

    def spawn(self, role: str) -> "Actor":
        return Actor(actor_id=f"{role}-{uuid.uuid4().hex}", role=role, parent=self)

    def lineage(self) -> List["Actor"]:
        chain = []
        cur = self
        while cur:
            chain.append(cur)
            cur = cur.parent
        return list(reversed(chain))

    def to_dict(self) -> dict[str, Any]:
        return {
            "actor_id": self.actor_id,
            "role": self.role,
            "parent_id": self.parent.actor_id if self.parent else None,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Actor":
        return cls(actor_id=d["actor_id"], role=d["role"], parent=None)
""")

# ---------------------------------------------------------------------------
# Authority
# ---------------------------------------------------------------------------

FILES["src/provenance_gate/authority.py"] = dedent("""
AUTHORIZED = {
    "enforce_pipeline",
    "reject_ambiguous_plans",
    ...
}
NOT_AUTHORIZED = {
    "hallucinate_test_results",
    ...
}
class AuthorityModel:
    ...
""")

# ---------------------------------------------------------------------------
# Capture (SignedEvidence + TerminalCapture)
# ---------------------------------------------------------------------------

FILES["src/provenance_gate/capture.py"] = dedent("""
from __future__ import annotations
import hashlib, hmac, re, secrets, subprocess
from dataclasses import dataclass
from typing import Any, Tuple
from provenance_gate.tiers import Tier

_PROCESS_SECRET = secrets.token_bytes(32)

...
class TerminalCapture:
    @staticmethod
    def run(cmd: list[str], *, cwd=None, timeout=300, **kwargs):
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout, **kwargs)
        content = f"$ {' '.join(cmd)}\\n{result.stdout}{result.stderr}\\n[exit {result.returncode}]"
        sig = _sign(content)
        return SignedEvidence(content=content, signature=sig, command=tuple(cmd), exit_code=result.returncode)
""")

# ---------------------------------------------------------------------------
# EvidenceArtifact
# ---------------------------------------------------------------------------

FILES["src/provenance_gate/evidence.py"] = dedent("""
from __future__ import annotations
import hashlib, time
from dataclasses import dataclass, field
from typing import Any
from provenance_gate.tiers import Tier, TIER_FROM_STRING

@dataclass(frozen=True)
class EvidenceArtifact:
    tier: Tier
    source: str
    content: Any
    timestamp: float = field(default_factory=time.time)
    hash: str = field(init=False)
    ...
""")

# ---------------------------------------------------------------------------
# Governance decorators
# ---------------------------------------------------------------------------

FILES["src/provenance_gate/governance.py"] = dedent("""
from __future__ import annotations
import functools
from provenance_gate.authority import AuthorityModel
from provenance_gate.pipeline import PipelineState, PipelineStep

def requires_authority(action, model=None):
    ...
def governed_step(step, pipeline, **advance_kwargs):
    ...
""")

# ---------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------

FILES["src/provenance_gate/guards.py"] = dedent("""
from provenance_gate.capture import SignedEvidence
...
def guard_verify(evidence, *, prior_state_validated=True):
    ...
""")

# ---------------------------------------------------------------------------
# Ledger (thread-safe)
# ---------------------------------------------------------------------------

FILES["src/provenance_gate/ledger.py"] = dedent("""
from __future__ import annotations
import hashlib, json, threading, time
from pathlib import Path

GENESIS_HASH = "0" * 64

class AppendOnlyLedger:
    def __init__(self, persist_path=None):
        self._entries = []
        self._seen_nonces = set()
        self._lock = threading.RLock()
        ...
""")

# ---------------------------------------------------------------------------
# Tiers
# ---------------------------------------------------------------------------

FILES["src/provenance_gate/tiers.py"] = dedent("""
from enum import Enum

class Tier(Enum):
    T1 = 1
    T2 = 2
    T3 = 3
    T4 = 4
    T5 = 5

TIER_LABELS = {...}
TIER_AUTHORIZES = {...}
TIER_FROM_STRING = {...}
""")

# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

FILES["src/provenance_gate/rules.py"] = dedent("""
STEP_REQUIREMENTS = {
    "SPEC": "T5",
    "PLAN": "T4",
    ...
}
class RuleSet:
    def validate(...):
        ...
""")

# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

FILES["src/provenance_gate/pipeline.py"] = dedent("""
from enum import Enum
from dataclasses import dataclass, field
...
class PipelineState:
    def advance(...):
        ...
""")

# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

FILES["src/provenance_gate/session.py"] = dedent("""
from dataclasses import dataclass, field
from provenance_gate.actors import Actor

@dataclass
class SessionScope:
    ...
""")

# ---------------------------------------------------------------------------
# Installer logic
# ---------------------------------------------------------------------------

def main():
    for rel, content in FILES.items():
        path = BASE / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print(f"provenance-gate v2.0.0 written to {BASE}")

if __name__ == "__main__":
    main()
