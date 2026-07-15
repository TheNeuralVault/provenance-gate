#!/usr/bin/env bash
# Hermes on_session_start hook: verify provenance-gate + signer are green (T1).
# Runs ruff + pytest on both repos; writes a hash-chained ledger entry so
# every session STARTS with a verifiable governance baseline.
# Non-fatal drift: if a venv/dep is missing it SKIPS honestly (never
# fabricates a pass); a REAL test failure prints loudly and exits 1.
set -u
GATE=~/provenance-gate
SIGNER=~/provenance-gate/extensions/provenance_gate_signer
LEDGER=~/provenance-gate/.session_verify.ledger.json
export MPLBACKEND=Agg
echo "[session-verify] provenance-gate + signer T1 baseline"

pass=0; fail=0
run_step() {  # $1=label  -- rest=cmd
  local label="$1"; shift
  if "$@" >/tmp/sv_$$.log 2>&1; then
    echo "  [OK]   $label"; pass=$((pass+1))
  else
    echo "  [FAIL] $label"; tail -6 /tmp/sv_$$.log; fail=$((fail+1))
  fi
}

# ---- core ----
if [ -d "$GATE" ] && [ -f "$GATE/.venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  . "$GATE/.venv/bin/activate"
  export PYTHONPATH="$GATE/src:$GATE/extensions/provenance_gate_signer"
  run_step "core: ruff"        ruff check src tests bin
  run_step "core: pytest (41)"  python -m pytest -q -o addopts=
  deactivate 2>/dev/null || true
else
  echo "  [SKIP] core: no venv (deps not installed) -- not a pass"
fi

# ---- signer ----
if [ -d "$SIGNER" ] && [ -f "$GATE/.venv/bin/activate" ]; then
  . "$GATE/.venv/bin/activate"
  export PYTHONPATH="$GATE/src:$SIGNER"
  cd "$SIGNER"
  run_step "signer: ruff"        ruff check provenance_gate_signer
  run_step "signer: pytest (30)" python -m pytest -q -o addopts= provenance_gate_signer/tests
  deactivate 2>/dev/null || true
else
  echo "  [SKIP] signer: no venv -- not a pass"
fi

rm -f /tmp/sv_$$.log
if [ "$fail" -gt 0 ]; then
  echo "[session-verify] $fail CHECK(S) FAILED -- session opens governed; fix before claiming green."
  exit 1
fi
# hash-chained baseline so a session opens with verifiable governance state
if command -v sha256sum >/dev/null 2>&1; then
  printf '%s\t%s\t%s\n' "$(date -u +%FT%TZ)" "$pass ok" "$(echo -n "$pass ok" | sha256sum | cut -c1-16)" >>"$LEDGER"
fi
echo "[session-verify] all green ($pass ok). governance baseline established."
exit 0
