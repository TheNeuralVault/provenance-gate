"""Tests for the provenance preflight guard (bin/preflight.py).

Enforces the standing mandate: a project lacking the provenance gate/ledger
must NOT run. These tests exercise the real CLI behaviors against a
self-contained throwaway project (the `eng` fixture) -- present->0,
absent->2 (refuse), tampered->3. No dependency on any sibling
repo existing, so the suite is portable and hermetic.
"""
import json
import os
import subprocess
import sys

import pytest

# Guard under test (repo-relative so the test is portable / hermetic).
_HERE = os.path.dirname(os.path.abspath(__file__))
PF = os.path.join(_HERE, os.pardir, "bin", "preflight.py")


@pytest.fixture()
def eng(tmp_path):
    """A throwaway project the preflight guard governs.

    Exercises the real guard semantics (init -> check -> run -> verify,
    tamper -> refuse) against a self-contained target. Mirrors how the
    guard protects a real project (e.g. QEA-JS-ENGINES) without
    hardcoding that project's path.
    """
    proj = tmp_path / "eng"
    proj.mkdir()
    init = subprocess.run(
        [sys.executable, PF, "init", str(proj)], capture_output=True, text=True
    )
    assert init.returncode == 0, init.stderr
    yield str(proj)
    # teardown: leave no ledger behind so a fresh governed project is restored
    lp = os.path.join(str(proj), "governance.ledger.json")
    if os.path.exists(lp):
        os.remove(lp)


def _run(args):
    return subprocess.run(
        [sys.executable, PF, *args], capture_output=True, text=True
    )


# --- init / check ---------------------------------------------------------
def test_init_creates_marker_and_ledger(eng):
    # init is idempotent; re-running must still pass check
    assert _run(["init", eng]).returncode == 0
    assert _run(["check", eng]).returncode == 0
    assert os.path.exists(os.path.join(eng, ".provenance-gate"))
    assert os.path.exists(os.path.join(eng, "governance.ledger.json"))


def test_check_present_passes(eng):
    assert _run(["check", eng]).returncode == 0


# --- run (the enforcement that matters) -----------------------------------
def test_run_gated_executes_command(eng):
    res = _run(["run", eng, "--", "echo", "ok"])
    assert res.returncode == 0
    assert "ok" in res.stdout


def test_check_absent_refuses(tmp_path):
    d = str(tmp_path / "none")
    assert _run(["check", d]).returncode == 2


def test_run_ungated_refuses_and_does_not_execute(tmp_path):
    d = str(tmp_path / "none")
    res = _run(["run", d, "--", "echo", "SHOULD-NOT-RUN"])
    assert res.returncode == 2
    assert "SHOULD-NOT-RUN" not in res.stdout


# --- ledger integrity -----------------------------------------------------
def test_verify_tampered_refuses(eng):
    lp = os.path.join(eng, "governance.ledger.json")
    with open(lp) as fh:
        raw = json.load(fh)
    raw[0]["payload"]["content"] = "tampered"
    with open(lp, "w") as fh:
        json.dump(raw, fh)
    assert _run(["verify", eng]).returncode == 3


def test_verify_clean_passes(eng):
    assert _run(["verify", eng]).returncode == 0
