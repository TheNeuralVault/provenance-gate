# Changelog

All notable changes to `provenance-gate` and `provenance-gate-signer` are
documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [provenance-gate-signer 0.1.4] — 2026-07-12 (metadata accuracy)

### Fixed
- Signer `pyproject.toml` now declares explicit trove classifiers including
  `Operating System :: POSIX :: Linux` and `Operating System :: MacOS`,
  correctly reflecting that the signer is **POSIX-only** (its security
  boundary is an `AF_UNIX` socket, which CPython does not expose on Windows;
  CPython #77589 open). Previously the package shipped without classifiers,
  defaulting to an OS-agnostic implication. Classifier strings validated
  against the PyPI trove classifier list.

## [2.0.1] / [provenance-gate-signer 0.1.3] — 2026-07-12 (release hygiene + portability)

### Fixed
- **Cross-platform CI (macOS + Windows).** Source-verified, not assumed:
  - macOS: AF_UNIX `sun_path` is capped at **104 bytes** on macOS/BSD
    (`char sun_path[104]`; Linux 108). Tests bound UNIX sockets under pytest's
    long `tmp_path` (~124 bytes on macOS runners) → `bind()` raised before
    `listen()`, so the server-readiness Event never set. Added a `short_sock`
    conftest fixture that binds under a short `tempfile.mkdtemp()` path and
    converted all five UNIX-socket tests to it.
  - Windows: `socket.AF_UNIX` is **undefined on win32** (CPython #77589 open;
    typeshed excludes it). The signer is POSIX-only by design — its security
    boundary is an AF_UNIX socket — so Windows was dropped from the signer CI
    matrix (core still covers Windows).
- **Server-readiness race.** `SigningService.serve_path` now sets a `_ready`
  Event after `listen()`, and fixtures/tests wait on it instead of polling the
  socket file (which races bind vs listen and never sees AF_UNIX sockets, whose
  size is 0).
- **CI hardening.** All third-party actions pinned to full commit SHAs
  (supply-chain integrity); `actions/checkout`, `actions/setup-python`,
  `semgrep/semgrep-action` (repo moved returntocorp→semgrep; SHA resolver
  follows the tag redirect but not a raw-SHA redirect, so the SHA is pinned
  under the current owner). Added least-privilege `permissions: contents: read`
  and a `concurrency` group. Enabled pip caching. The build step now performs
  real T1 verification: build wheel → install into a clean venv → import-smoke.

### Security
- CI SAST (Bandit + Semgrep) continues green across the matrix.

## [2.0.0] — Semver-Major

### Added
- Tiered evidence model (T1–T5) with `TIER_AUTHORIZES` truth table.
- `RuleSet.validate` — central gate enforcing step→minimum-tier and
  `VERIFY` source rules; returns specific `RuleViolation` codes.
- `AppendOnlyLedger` with hash chaining and nonce replay protection.
- `PipelineState` step machine (`SPEC→PLAN→TEST→BUILD→VERIFY→REVIEW→COMMIT`)
  with structural governance.
- Hallucination-defense guards: `guard_verify`, `guard_step`,
  `check_hallucination_defense`.
- Session scopes with actor lineage; `AuthorityModel` + `requires_authority` /
  `governed_step` structural decorators.
- Signer extension `provenance-gate-signer`:
  - Pure-Python Ed25519 (RFC 8032) with projective (X,Y,Z) arithmetic.
  - `SigningService` holding the private key in a **separate process** —
    closes the in-process adversary gap.
  - `CaptureClient` / `AttestedCapture` / `ServiceVerifier` client surface.

### Changed
- Ed25519 sign+verify performance improved ~19x by replacing per-addition
  modular inverse with iterative projective double-and-add (single inversion).
  Verified bit-equal to the affine reference across many scalars.
- `verify()` in the signer now compares canonical point encodings with
  `hmac.compare_digest` (constant-time) instead of `==`.

### Fixed
- Closed 5 core coverage gaps (guards/ledger/pipeline) and 15 signer error
  branches — both packages now at 100% line coverage.
- `SigningService` gained a `shutdown()` / stop-event so server threads never
  leak and `finally`/teardown branches are exercised.
- SPDX `license = "MIT"` (removed deprecated classifier) — no build warnings.

### Security
- SAST: Bandit clean; Semgrep ruleset (`semgrep.yml`) encoded as four
  invariants; portable AST scanner (`scripts/sast_invariant_scan.py`)
  enforces the same locally without the glibc-only `semgrep-core` binary.
- Fuzz/property tests for Ed25519 tamper/forgery rejection and the governance
  invariant.

## [1.x] — Pre-2.0 lineage

Earlier releases established the tiered-evidence concept, the HMAC-signed
`TerminalCapture`, and the append-only ledger. See git history for details.
