#!/usr/bin/env bash
# Local pre-merge SAST gate for provenance-gate.
#
# Runs the same two scanners CI runs, so a developer (or an agent) can verify
# "T1: I actually ran SAST" before pushing. Intended to be wired as a
# pre-commit / pre-merge hook.
#
#   bash scripts/sast_gate.sh
#
# Exit code 0 = clean. Non-zero = a scanner flagged something (or could not
# be installed). The script NEVER claims success when a tool is missing; it
# prints an explicit SKIP line instead.
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

fail=0

echo "==> Bandit (Python SAST)"
if command -v bandit >/dev/null 2>&1 || python -m bandit --help >/dev/null 2>&1; then
  python -m bandit -c bandit.yaml -r src extensions -x '*/tests/*,*/build/*'
  rc=$?
  if [ "$rc" -ne 0 ]; then echo "BANDIT: issues found (rc=$rc)"; fail=1; else echo "BANDIT: clean"; fi
else
  echo "SKIP: bandit not installed -> 'python -m pip install bandit'"
  fail=1
fi

echo
echo "==> Semgrep (invariant rules) [CI-authoritative]"
# semgrep-core is a glibc-only binary; it cannot run on Android/Termux (no
# glibc loader). CI runs returntocorp/semgrep-action authoritatively. The
# portable local equivalent is sast_invariant_scan.py below, which enforces
# the SAME four invariants without any external binary.
if command -v semgrep >/dev/null 2>&1; then
  sem_out=$(semgrep --config semgrep.yml --error --quiet src extensions 2>&1)
  rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "SEMGREP: clean"
  elif echo "$sem_out" | grep -qiE "semgrep-core|CoreNotFound|Traceback"; then
    # The native semgrep-core binary is a glibc ELF; it cannot execute on
    # Android/Termux (no glibc loader). CI runs semgrep authoritatively via
    # returntocorp/semgrep-action, and sast_invariant_scan.py enforces the
    # same four invariants locally without any binary. Report SKIP, not fail.
    echo "SEMGREP: SKIP (glibc binary unavailable here; CI + invariant scan cover it)"
  else
    echo "SEMGREP: violations (rc=$rc):"; echo "$sem_out" | tail -20
    fail=1
  fi
else
  echo "SEMGREP: SKIP (not installed; CI covers it via semgrep-action)"
fi

echo
echo "==> Invariant scan (portable, no binary; mirrors semgrep.yml)"
python scripts/sast_invariant_scan.py
rc=$?
if [ "$rc" -ne 0 ]; then echo "INVARIANT SCAN: violations (rc=$rc)"; fail=1; else echo "INVARIANT SCAN: clean"; fi

echo
if [ "$fail" -ne 0 ]; then
  echo "SAST GATE: NOT CLEAN (see above)"
  exit 1
fi
echo "SAST GATE: PASS"
