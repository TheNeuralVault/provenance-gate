# Contributing to provenance-gate

Thanks for contributing. This project enforces a **verification gate** — not
just "code that runs," but "code with evidence." Pull requests that cannot be
verified against the bar below will be held until they are.

## Prerequisites

- Python ≥ 3.10
- Install with dev extras: `python -m pip install -e ".[dev]"` (core) and the
  same in `extensions/provenance_gate_signer`.

## Before you open a PR

Run these locally and ensure they are green:

```bash
# 1. Tests + coverage (both packages must stay at 100%)
python -m pytest -q --cov=src/provenance_gate
cd extensions/provenance_gate_signer && python -m pytest -q --cov=provenance_gate_signer

# 2. Static types — strict mypy must be clean
python -m mypy src
python -m mypy provenance_gate_signer

# 3. SAST gate (Bandit + portable invariant scanner)
bash scripts/sast_gate.sh
```

## Rules of the road

1. **No coverage regression.** New code needs a test that exercises the new
   branch. We hold 100% on both packages; a gap is a bug, not a TODO.
2. **No unverified claims in code or docs.** If you assert a property, add a
   test or a fuzz case that proves it. Assertions without evidence are removed.
3. **Cryptography is sacred.** Any change to `keys.py`, `capture.py`, or the
   `RuleSet`/`verify` paths requires: (a) a roundtrip + tamper + forgery test,
   (b) a review note explaining the change, (c) no `==`/`!=` on signature
   material (use `hmac.compare_digest`).
4. **Governance invariants are load-bearing.** Do not weaken `RuleSet.validate`
   or the tier→step map without a documented, reviewed rationale. The fuzz
   suite (`tests/test_rules_fuzz.py`) asserts the invariant; breaking it must
   break the build.
5. **Docs are part of the deliverable.** README/CHANGELOG/SECURITY must stay
   accurate. A stub doc is a failing deliverable for a distribution package.

## What "top-tier" means here

This package is aimed at engineers, developers, and the general public as a
trust boundary for autonomous agents. That bar is:

- strict `mypy` clean, 100% line coverage, SAST clean, fuzz-validated crypto,
  clean build + `twine check`, and a reproducible local gate.
- Honest threat modeling (see `SECURITY.md`) — we document what we do and do
  not protect, rather than overclaiming.

## Reporting security issues

See `SECURITY.md`. Do **not** open public issues for vulnerabilities.
