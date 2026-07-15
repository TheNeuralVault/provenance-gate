# Release record — provenance-gate + provenance-gate-signer

**Date (UTC):** 2026-07-15
**Released by:** Hermes Agent (TheNeuralVault)

## Published to PyPI (verified installable)

| Package | Version | PyPI URL | Verified |
|----------|---------|-----------|----------|
| provenance-gate | 2.0.2 | https://pypi.org/project/provenance-gate/2.0.2/ | `pip install` + import + version OK |
| provenance-gate-signer | 0.1.5 | https://pypi.org/project/provenance-gate-signer/0.1.5/ | `pip install` + import + sign/verify OK |

## What changed (vs 2.0.1 / 0.1.4)
- Version attributes synced between `pyproject.toml` and package `__version__`
  (core was 2.0.0 in `__init__`, signer was 0.1.2 — now consistent).
- `tests/test_import.py` now asserts `__version__` against `pyproject.toml`
  (single source of truth; drift-proof).
- Signer fuzz test (`test_fuzz.py`) import-safe via `try/except importorskip`
  (27 passed/1 skipped bare venv; 30 with hypothesis).
- Guard `bin/preflight.py` ruff-clean; `tests/test_preflight_guard.py`
  portable (no hardcoded sibling-repo path).
- Session-start T1 hook (`hooks/session_verify.sh`) pins governance to every session.

## Verification (real, not asserted)
- core: ruff clean · mypy src clean · 41 pytest passed
- signer: ruff clean · 30 pytest passed
- `twine check` PASSED on all 4 artifacts (2 wheels + 2 sdists)
- Clean-venv install from PyPI: both import, versions correct,
  signer 0.1.5 signs+verifies Ed25519.

## Security note
The PyPI token used for this upload was exposed in local Hermes logs and
has been REVOKED by the owner. Do NOT reuse it. Future uploads must
use a fresh scoped token.
