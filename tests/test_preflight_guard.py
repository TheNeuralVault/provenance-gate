"""
Tests for the provenance preflight guard (bin/preflight.py).

Enforces the standing mandate: a project lacking the provenance gate/ledger
must NOT run. These tests exercise the real CLI behaviors against the
committed guard file -- present->0, absent->2 (refuse), tampered->3.
"""
import json
import os
import subprocess
import sys
import tempfile

import pytest

PF = "/data/data/com.termux/files/home/provenance-gate/bin/preflight.py"
ENG = "/data/data/com.termux/files/home/agent_forces/_scan/gh_classify/repos/Sovereign-Neural-Matrix/QEA-JS-ENGINES"


def _run(args):
    return subprocess.run(
        [sys.executable, PF] + args, capture_output=True, text=True
    )


@pytest.fixture(autouse=True)
def _governed():
    """Ensure the target project is governed before/after each test.
    Teardown deletes any ledger left behind (e.g. tampered by a test) so a
    clean governed ledger is restored for the next test."""
    _run(["init", ENG])
    yield
    lp = os.path.join(ENG, "governance.ledger.json")
    if os.path.exists(lp):
        os.remove(lp)
    _run(["init", ENG])


# --- init / check ---------------------------------------------------------

def test_init_creates_marker_and_ledger():
    # init is idempotent; re-running must still pass check
    assert _run(["init", ENG]).returncode == 0
    assert _run(["check", ENG]).returncode == 0
    assert os.path.exists(os.path.join(ENG, ".provenance-gate"))
    assert os.path.exists(os.path.join(ENG, "governance.ledger.json"))


def test_check_present_passes():
    assert _run(["check", ENG]).returncode == 0


# --- run (the enforcement that matters) -----------------------------------

def test_run_gated_executes_command():
    res = _run(["run", ENG, "--", "echo", "ok"])
    assert res.returncode == 0
    assert "ok" in res.stdout


def test_check_absent_refuses():
    d = tempfile.mkdtemp()
    assert _run(["check", d]).returncode == 2


def test_run_ungated_refuses_and_does_not_execute():
    d = tempfile.mkdtemp()
    res = _run(["run", d, "--", "echo", "SHOULD-NOT-RUN"])
    assert res.returncode == 2
    assert "SHOULD-NOT-RUN" not in res.stdout


# --- ledger integrity -----------------------------------------------------

def test_verify_tampered_refuses():
    lp = os.path.join(ENG, "governance.ledger.json")
    raw = json.load(open(lp))
    raw[0]["payload"]["content"] = "tampered"
    json.dump(raw, open(lp, "w"))
    assert _run(["verify", ENG]).returncode == 3


def test_verify_clean_passes():
    assert _run(["verify", ENG]).returncode == 0
