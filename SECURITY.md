# Security Policy — provenance-gate

This document states, honestly, what `provenance-gate` does and does **not**
protect. We prefer accurate boundaries over reassuring language.

## Threat model

### In scope (what this package defends)

- **Hallucinated authorization.** An agent cannot claim BUILD/VERIFY/COMMIT
  authority from a lower-tier (T2–T5) assertion. `RuleSet.validate` enforces
  the step→minimum-tier map; only T1 (real, executed, captured) evidence
  authorizes a high-assurance action.
- **Forged in-process evidence (core).** `TerminalCapture` signs command
  output with an HMAC key held in the agent process. This prevents *accidental*
  or *downstream* mislabeling of evidence within a trusted process.
- **Forged evidence from a compromised agent process (signer extension).** With
  `provenance-gate-signer`, the Ed25519 private key lives in a **separate
  privileged process**. A compromised agent can request capture but cannot
  mint a valid signature — it never holds the key and cannot invoke the
  service's signing path. Verification uses only the public key.
- **Tampering / replay.** `AppendOnlyLedger` hash-chains entries and rejects
  nonce replay. `verify()` rejects wrong-key, flipped-message, and
  flipped-signature inputs (property-tested).
- **Injection in the capture path.** Capture runs commands as an explicit argv
  list with `shell=False` (verified by SAST). No `eval`/`exec`/`pickle`/
  `marshal.loads` on untrusted input (verified by SAST).

### Out of scope (what this package does NOT guarantee)

- **Malicious insiders with the signing key.** Whoever holds the Ed25519
  private key can produce valid signatures. Protect the key like any secret.
- **Compromise of the privileged signing process.** If the signing process
  itself is taken over, its signatures are trusted by design. Run it with least
  privilege, isolated from the agent.
- **Supply-chain of dependencies.** We pin and test, but do not vouch for
  third-party packages beyond our tests. Review your environment.
- **Side-channel leakage of non-secret values.** Constant-time comparison is
  used on signature material; we do not claim broad constant-time guarantees
  across the whole crypto stack.

## Supported versions

Security fixes target the latest released minor of `provenance-gate` (2.x) and
`provenance-gate-signer` (0.1.x). Older majors are not patched.

## Reporting a vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Email the maintainers (see repository metadata) with:

- a description of the vulnerability and its impact,
- steps to reproduce,
- affected version(s).

We aim to acknowledge within 72 hours and to provide a remediation timeline
within 7 days. Coordinated disclosure is preferred; we will credit reporters
who wish to be named.

## Cryptography notes

- Ed25519 implementation follows RFC 8032. The signing/verify math was verified
  bit-equal against an affine reference and fuzz-tested for tamper/forgery
  rejection. Sign+verify was measured ~19x faster after moving to iterative
  projective arithmetic (single modular inversion per operation).
- Verification compares canonical point encodings with `hmac.compare_digest`
  (constant-time), not `==`.
