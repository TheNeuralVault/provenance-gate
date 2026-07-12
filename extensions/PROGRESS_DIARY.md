# provenance_gate_signer — progress diary (ledger of work)

Format: date · status · what changed · open questions
This is the working ledger for the out-of-process T1 signing extension.
Core `provenance_gate` package is NEVER modified by this work.

---

## 2026-07-12 — session 1

### Goal
Sketch a real, tested out-of-process Ed25519 signing extension that closes the
in-process adversary gap in provenance-gate, WITHOUT modifying the core package.

### What was built (real code, ruff-clean)
- extensions/provenance_gate_signer/  (separate package, dep on provenance-gate)
  - keys.py        — Ed25519 sign/verify/keygen
  - service.py     — SigningService (only private-key holder); UNIX + TCP servers
  - client.py      — CaptureClient (cannot sign), AttestedCapture, ServiceVerifier
  - tests/test_signer.py — 10 tests incl. test_inprocess_adversary_cannot_forge
  - pyproject.toml, README.md, __init__.py

### Environment blocker discovered
- cryptography prebuilt wheel is BINARY-INCOMPATIBLE with Termux / Py3.14
  (ImportError: PyExc_Warning missing from _rust.abi3.so).
- User approved `pip install --no-binary :all: cryptography` (source build).
- Source build STILL failed with same PyExc_Warning error (rust binding ABI
  mismatch on Termux Py3.14). NOT fixable by rebuild.
- Decision: drop the `cryptography` binary dep entirely. Reimplemented Ed25519
  as a PURE-PYTHON RFC 8032 module in keys.py (no compiled deps). Restored
  hermes-agent's cryptography to 46.0.7 to avoid breaking the agent.

### Testing status
- ruff: ALL CHECKS PASSED (strict ruleset).
- mypy: NOT yet run (config path bug to fix: files=["provenance_gate_signer"]
  wrong because cwd IS the package).
- pytest: BLOCKED on pure-python Ed25519 correctness bug (see below).

### FINAL VERIFICATION (this session) — ALL GREEN
- ruff: All checks passed (strict: E,F,W,I,UP,B,C4,SIM,RUF).
- mypy (shipped src, strict): Success — no issues in 4 source files.
- pytest + cov gate (--cov-fail-under=90): 10 passed, 92.07% coverage.
- Pure-Python Ed25519 cross-checked against cryptography 46.0.7:
    * my sign() == cryptography sign() byte-for-byte (same seed/msg)
    * cryptography verifies my sig; my verify() verifies cryptography sig
    * tampered message rejected; 5 random roundtrips OK
- build: wheel built (py3-none-any — pure Python, NO binary dep, runs on
  Termux/Ubuntu/PyPI identically).
- twine check: PASSED.
- clean-venv install + import smoke: OK (verify True, version 0.1.0, core 2.0.0).

### KEY BUG FIXED (do not regress)
- Pure-Python Ed25519 `_xrecover` used WRONG decompression denominator:
  `xx = (y^2 - 1) / (d*y^2 - 1)` — should be `(d*y^2 + 1)` for the Edwards
  curve `-x^2 + y^2 = 1 + d x^2 y^2`. Verified correct root = (x-coordinate
  of Ed25519 base point); sign-flip logic then yields even root = BX.
- setuptools `packages.find` where was "." (inside package) -> wheel shipped
  ZERO .py modules. Fixed to where = [".."] so the package is discovered from
  the parent dir. CONFIRMED wheel now contains all 5 modules.

### DECISION (user-approved): drop `cryptography` binary dep
- cryptography prebuilt wheel is binary-incompatible with Termux Py3.14
  (PyExc_Warning missing from _rust.abi3.so). Source build also failed.
- Reimplemented Ed25519 as pure-Python RFC 8032 (keys.py) — no compiled deps.
- hermes-agent's cryptography restored to 46.0.7 (was temporarily 49.0.0).

### CORE PACKAGE STATUS
- provenance-gate core was NOT modified by this work. The extension composes
  via AttestedCapture.to_t1_artifact() -> core EvidenceArtifact(T1).

### FILES (uncommitted, in working tree)
- /data/data/com.termux/files/home/provenance-gate/extensions/provenance_gate_signer/*
- /data/data/com.termux/files/home/provenance-gate/extensions/PROGRESS_DIARY.md

### NEXT (deferred)
- Publish provenance-gate + signer to PyPI/TestPyPI (not yet done).
- Optionally wire SigningService into core's capture path as an opt-in backend.

