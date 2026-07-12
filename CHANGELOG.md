# Changelog

All notable changes to `provenance-gate` and `provenance-gate-signer` are
documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

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
