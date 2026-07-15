#!/usr/bin/env bash
# Hermes pre_tool_call hook (terminal tool): refuse to commit / push
# into the provenance-gate repos unless their suites are green (T1).
# Non-fatal drift guard: if the venv/deps are missing it SKIPS (never
# fabricates a pass), but a real test failure prints and exits non-zero.
set -u
GATE=~/TheNeuralVault/provenance-gate
SIGNER=~/TheNeuralVault/provenance-gate/extensions/provenance_gate_signer
export MPLBACKEND=Agg

# Only gate git commit/push inside those repos.
if [ "${HERMES_TOOL_ARGS:-}" ]; then
  case "$HERMES_TOOL_ARGS" in
    *"commit"*|*"push"*) : ;;
    *) exit 0 ;;
  esac
fi

for d in "$GATE" "$SIGNER"; do
  [ -d "$d" ] || continue
  venv="$d/.venv/bin/activate"
  [ -f "$venv" ] || { echo "[pre-commit] SKIP: no venv at $d (deps not installed)"; continue; }
  ( cd "$d" && . "$venv" && \
    ruff check src tests bin >/dev/null 2>&1 && \
    python -m pytest -q -o addopts= >/dev/null 2>&1 ) \
    || { echo "[pre-commit] REFUSE: $d suite not green"; exit 1; }
done
exit 0
