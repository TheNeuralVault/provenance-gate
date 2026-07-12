# Security Policy

## Scope

`provenance-gate` is a **governance discipline** layer for agent systems. It
gates actions (BUILD / VERIFY / COMMIT, etc.) behind evidence-quality tiers
(T1–T5) and records every accepted step in a hash-chained, nonce-protected
append-only ledger. The point is to make "I verified this" *demonstrable* and
to defend against an agent (or its operator) asserting success it did not earn.

## Threat model (stated honestly)

| Threat | Addressed? | How |
| --- | --- | --- |
| Agent claims a build passed without running it | Yes | Only `T1` (executed + signed-capture) evidence authorizes BUILD/VERIFY/COMMIT. `verify_claim` rejects non-T1 / forged artifacts. |
| Tampering with the ledger after the fact | Yes | Ledger is hash-chained; `_load_and_verify()` raises `LedgerIntegrityError` on a hash/prev-hash/nonce mismatch. |
| Nonce replay of a ledger entry | Yes | `AppendOnlyLedger.append` requires a unique `nonce`; replay is detected on load. |
| In-process adversary forges a signature | Yes (signer ext) | `provenance-gate-signer` holds the Ed25519 private key in a **separate process**; the agent only ever sees attested captures + the public key. |
| Ed25519 forgery / tamper acceptance | Yes (signer ext) | Verified-against-affine-reference projective arithmetic; canonical-encoding compare with `hmac.compare_digest`. Property/fuzz tests reject tampered/forged inputs. |

### What this package does NOT guarantee

- **The HMAC signing secret is process-local.** It binds evidence to the
  process that produced it; it is a *discipline mechanism*, not a
  cryptographic isolation boundary against a compromised host. A process that
  can read the secret can sign its own artifacts — so treat the secret like any
  other in-process credential.
- **It does not sandbox the agent.** It gates *decisions*, not *execution*.
  Pair it with OS-level isolation for untrusted agents.
- **Supply-chain integrity of dependencies** is the consumer's
  responsibility. We pin our own CI actions to commit SHAs; you should pin
  `provenance-gate` in your own lockfiles.

## Supported platforms

- Core (`provenance-gate`): Linux, macOS, Windows — Python 3.10–3.13.
- Signer (`provenance-gate-signer`): **POSIX only** (Linux, macOS). Its
  security boundary is an `AF_UNIX` socket, which CPython does not expose on
  Windows (CPython #77589 open). On Windows, use the in-process `guard_verify`
  path instead.

## Reporting a vulnerability

Open a private security advisory on the repository, or file an issue marked
`security`. Do not disclose publicly until a fix is released.

## Static analysis

CI runs Bandit and a custom Semgrep ruleset (`semgrep.yml`) as four invariants;
`scripts/sast_invariant_scan.py` enforces the same locally without the
glibc-only `semgrep-core` binary.
