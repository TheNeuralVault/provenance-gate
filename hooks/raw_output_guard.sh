#!/usr/bin/env bash
# pre_response hook: block any block claiming to be "raw output" that
# contains interleaved prose narration instead of literal stdout.
# Hermes passes the drafted response on stdin; we inspect and exit
# non-zero to reject delivery if it violates the raw-output contract.
set -u
MSG=$(cat)
# trigger phrases that indicate prose characterization, not raw output
if printf '%s' "$MSG" | grep -qiE "matches the commit|as you can see|this confirms|I reported|verified by|correctly shown|as expected"; then
  echo "RAW-OUTPUT GUARDRAIL TRIPPED: paste literal stdout, no prose characterization." >&2
  exit 1
fi
# if block self-labels raw/literal output, it must not contain first-person narration
if printf '%s' "$MSG" | grep -qiE "raw (un)?edited|literal (terminal|stdout)|paste[d]? (the )?raw"; then
  if printf '%s' "$MSG" | grep -qiE "\bI (ran|confirmed|verified|checked|see|assert)\b|this (confirms|shows|means)|in other words"; then
    echo "RAW-OUTPUT GUARDRAIL TRIPPED: labeled raw but contains narration." >&2
    exit 1
  fi
fi
exit 0
