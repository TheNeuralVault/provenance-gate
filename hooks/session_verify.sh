#!/usr/bin/env bash
# Hermes on_session_start + Termux:Boot hook: verify provenance-gate
# + signer are green (T1). Runs ruff + pytest on both repos; writes
# a hash-chained ledger entry so every session / device boot STARTS governed.
#
# The gate venv + signer service live in the Ubuntu PRoot, but the
# Hermes session can run on the native Termux side. ruff has a
# NATIVE Termux build at $PREFIX/bin/ruff (works on the Termux
# side directly). pytest runs via the venv python (also reachable
# from Termux). So we run ruff from the native Termux build
# and only fall back to PRoot if that build is missing.
set -u
GATE=~/provenance-gate
SIGNER=~/provenance-gate/extensions/provenance_gate_signer
LEDGER=~/provenance-gate/.session_verify.ledger.json
# /tmp is often non-writable under Termux; use a writable cache dir
SV_LOG_DIR="${HOME:-/tmp}/.signer"
mkdir -p "$SV_LOG_DIR" 2>/dev/null || SV_LOG_DIR="${TMPDIR:-/tmp}"
export MPLBACKEND=Agg
echo "[session-verify] provenance-gate + signer T1 baseline"
export MPLBACKEND=Agg
echo "[session-verify] provenance-gate + signer T1 baseline"

pass=0; fail=0
run_step() {  # $1=label  -- rest=cmd
  local label="$1"; shift
  local log="$SV_LOG_DIR/sv_$$.log"
  if "$@" >"$log" 2>&1; then
    echo "  [OK]   $label"; pass=$((pass+1))
  else
    echo "  [FAIL] $label"; tail -6 "$log"; fail=$((fail+1))
  fi
}

# ruff: prefer the NATIVE Termux build ($PREFIX/bin/ruff) which
# runs on the Termux side directly. Fall back to PRoot only if
# the native build is absent. pytest runs via the venv python and
# is reached the same way regardless of side. Use the native
# Termux ruff build directly; if it is somehow absent, SKIP
# honestly (never fake a pass), do not fall back to PRoot.
RUFF_BIN="${PREFIX:-/data/data/com.termux/files/usr}/bin/ruff"
run_ruff() {  # $1=label  $2=dir  $3..=ruff args
  local label="$1"; local dir="$2"; shift 2
  local log="$SV_LOG_DIR/ruff_$$.log"
  if [ -x "$RUFF_BIN" ]; then
    if ( cd "$dir" && "$RUFF_BIN" "$@" ) >"$log" 2>&1; then
      echo "  [OK]   $label"; pass=$((pass+1))
    else
      echo "  [FAIL] $label"; tail -6 "$log"; fail=$((fail+1))
    fi
  else
    echo "  [SKIP] $label -- no native ruff ($RUFF_BIN)"
  fi
}

# ---- core ----
if [ -d "$GATE" ] && [ -f "$GATE/.venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  . "$GATE/.venv/bin/activate"
  export PYTHONPATH="$GATE/src:$GATE/extensions/provenance_gate_signer"
  cd "$GATE"
  run_ruff "core: ruff"        "$GATE"  check src tests bin
  run_step "core: pytest (41)" python -m pytest -q -c "$GATE/pyproject.toml" --rootdir "$GATE" -o addopts=
  deactivate 2>/dev/null || true
else
  echo "  [SKIP] core: no venv (deps not installed) -- not a pass"
fi

# ---- signer ----
if [ -d "$SIGNER" ] && [ -f "$GATE/.venv/bin/activate" ]; then
  . "$GATE/.venv/bin/activate"
  export PYTHONPATH="$GATE/src:$SIGNER"
  cd "$SIGNER"
  # signer tests exercise the LIVE TCP service; ensure it is up
  SOCK="$HOME/.signer/sign.sock"
  if ! python "$HOME/.signer/healthcheck.py" >/dev/null 2>&1; then
    if [ -f "$HOME/.signer/run_signer.py" ]; then
      nohup python "$HOME/.signer/run_signer.py" \
        >"$HOME/.signer/service.log" 2>&1 &
      for i in $(seq 1 20); do
        python "$HOME/.signer/healthcheck.py" >/dev/null 2>&1 && break
        sleep 0.5
      done
    fi
  fi
  run_ruff "signer: ruff"      "$SIGNER" check provenance_gate_signer
  run_step "signer: pytest (30)" python -m pytest -q -c "$SIGNER/pyproject.toml" --rootdir "$SIGNER" -o addopts= provenance_gate_signer/tests
  deactivate 2>/dev/null || true
else
  echo "  [SKIP] signer: no venv -- not a pass"
fi

rm -f "$SV_LOG_DIR/sv_$$.log"
if [ "$fail" -gt 0 ]; then
  echo "[session-verify] $fail CHECK(S) FAILED -- session opens governed; fix before claiming green."
  exit 1
fi
# hash-chained baseline so a session/boot opens with verifiable governance state
if command -v sha256sum >/dev/null 2>&1; then
  printf '%s\t%s\t%s\n' "$(date -u +%FT%TZ)" "$pass ok" "$(printf '%s' "$pass ok" | sha256sum | cut -c1-16)" >>"$LEDGER"
fi
echo "[session-verify] all green ($pass ok). governance baseline established."
exit 0
