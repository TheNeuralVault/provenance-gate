# provenance-gate

Gate autonomous-agent actions by **evidence quality tier** — with actor
identity, session hierarchy, structural governance, and honest threat modeling.

`provenance-gate` turns "trust me, I built/tested it" into a machine-checked
invariant: **only T1 (real, executed, captured) evidence can authorize BUILD,
VERIFY, or COMMIT.** Lower tiers (literature, inference, hypothesis, belief)
can plan and reason, but cannot drive a high-assurance action.

- Core package: `provenance-gate` (MIT, Python ≥3.10)
- Signing extension: `provenance-gate-signer` (out-of-process Ed25519 T1 signing)

---

## Why it exists

An autonomous coding agent can assert "I built/tested/deployed it" with zero
proof. That is a hallucination vector at the exact moment power is exercised
(writing code, signing, shipping). `provenance-gate` closes that gap by
requiring tiered, signed, auditable evidence before any such action runs.

## Install

```bash
pip install provenance-gate
pip install provenance-gate-signer   # optional: out-of-process Ed25519 signing
```

From source (editable, with dev/test tooling):

```bash
git clone <repo> && cd provenance-gate
python -m pip install -e ".[dev]"
cd extensions/provenance_gate_signer && python -m pip install -e ".[dev]"
```

## The evidence tiers (T1–T5)

| Tier | Name        | Can authorize | Meaning                                  |
|------|-------------|---------------|------------------------------------------|
| T1   | VERIFIED    | **yes**       | Real executed + captured evidence        |
| T2   | LITERATURE  | no            | Cited docs / prior art                   |
| T3   | INFERENCE   | no            | Logical inference from evidence          |
| T4   | HYPOTHESIS  | no            | Proposed, untested                       |
| T5   | BELIEF      | no            | Assertion without evidence               |

Only T1 can drive `BUILD`, `VERIFY`, `COMMIT`.

## Step → minimum tier

Every pipeline transition is gated by `RuleSet.validate(step, tier, ...)`:

```
SPEC→T5, PLAN→T4, TEST→T4, CAPTURE→T3, REVIEW→T2,
BUILD→T1, VERIFY→T1, COMMIT→T1
```

`VERIFY` additionally requires `verify_source ∈ {test_output, build_output,
runtime_capture}`. Any unknown tier/step, or a tier below the step's minimum,
is rejected with a specific `RuleViolation` code (`INVALID_TIER`,
`INVALID_STEP`, `INVALID_VERIFY_SOURCE`, `TIER_INSUFFICIENT_FOR_STEP`).

## Quickstart

```python
from provenance_gate import RuleSet, Tier, PipelineStep

rules = RuleSet()
# A belief-level claim cannot authorize a build:
result = rules.validate(PipelineStep.BUILD, Tier.T5)
assert not result.ok          # TIER_INSUFFICIENT_FOR_STEP

# T1 evidence can:
result = rules.validate(PipelineStep.BUILD, Tier.T1,
                        verify_source="build_output")
assert result.ok
```

### Capturing real (T1) evidence

```python
from provenance_gate import TerminalCapture

cap = TerminalCapture(command="pytest -q", workdir=".")
result = cap.run()                 # runs, captures stdout/stderr/exit code
assert result.is_valid             # HMAC-signed in-process
print(result.signature, result.pubkey)
```

### Out-of-process signing (recommended for untrusted agents)

```python
# privileged signing process:
from provenance_gate_signer import run_service
svc = run_service("./signer.sock")     # holds Ed25519 key; agent never sees it

# agent process:
from provenance_gate_signer import CaptureClient, AttestedCapture
client = CaptureClient("./signer.sock")
ev = client.capture(command="pytest -q", workdir=".")
assert ev.is_valid                    # signed by the service, not the agent
artifact = ev.to_t1_artifact()        # drops into guard_verify / pipeline
```

## Architecture

- `tiers.py` — `Tier` enum (T1–T5) and `TIER_AUTHORIZES` truth table.
- `rules.py` — `RuleSet.validate`, the central gate logic.
- `evidence.py` / `capture.py` — `EvidenceArtifact`, `TerminalCapture`,
  `SignedEvidence` (HMAC-verified captures).
- `ledger.py` — `AppendOnlyLedger` with hash chaining + nonce replay guard.
- `pipeline.py` — `PipelineState` step machine with structural governance.
- `guards.py` — hallucination-defense guards (`guard_verify`, `guard_step`,
  `check_hallucination_defense`).
- `session.py` / `actors.py` — session scopes with actor lineage.
- `governance.py` — `requires_authority` / `governed_step` structural decorators.
- `authority.py` — `AuthorityModel` (who may authorize what).

Signer extension (`provenance-gate-signer`):
- `keys.py` — pure-Python Ed25519 (RFC 8032) with projective arithmetic.
- `service.py` — `SigningService` (holds the private key in a separate process).
- `client.py` — `CaptureClient` / `AttestedCapture` / `ServiceVerifier`.

## Quality bar (this is what "high grade" means here)

- **100% test coverage** on both packages (core 475 stmts, signer 288 stmts).
- **Strict `mypy`** (`strict = true`) — clean on all source files.
- **SAST**: Bandit clean; Semgrep (via CI) + a portable AST invariant scanner
  (`scripts/sast_invariant_scan.py`) enforce four hard invariants locally.
- **Property/fuzz tests**: Ed25519 roundtrip + tamper + forgery rejection;
  `RuleSet` governance invariant fuzzed over 500 random + exhaustive combos.
- **Build + twine**: wheel/sdist build clean; `twine check` passes.
- **Local gate**: `bash scripts/sast_gate.sh` runs Bandit + the invariant
  scanner; CI adds the multi-OS matrix + Semgrep.

Run the local gate before pushing:

```bash
bash scripts/sast_gate.sh
python -m pytest -q
```

## Documentation

- `SECURITY.md` — threat model + coordinated disclosure.
- `CONTRIBUTING.md` — how to contribute and the verification gate.
- `CHANGELOG.md` — release history.

## License

MIT — see `LICENSE`.
