#!/usr/bin/env python3
"""
provenance preflight guard  --  provenance-gate v2.0.0 enforcement

MANDATE (standing): every project MUST include + use provenance_gate.
If a project lacks the gate it must NOT run. This tool enforces that
mechanically: it hard-fails (nonzero exit, clear reason) when the gate or
its ledger is absent, so a project literally cannot start without governance.

Subcommands
  init   <project_dir> [actor_id]   install gate into a project (writes gate
                                    marker, project ledger, local run_gated.sh)
  check  <project_dir>              hard-fail (exit 2) if gate/ledger absent
  run    <project_dir> -- <cmd...>  check, then exec cmd; refuse if check fails
  verify <project_dir>              reload+verify the project ledger chain

Exit codes
  0  gate present / command ran / ledger good
  2  gate/ledger absent  (hard-fail -- the project must NOT run)
  3  ledger tamper detected
  1  other error
"""
import sys, os, json, subprocess

GATE_MARKER = ".provenance-gate"          # marker file proving gate is wired in
LEDGER_NAME = "governance.ledger.json"    # project-local hash-chained ledger


def _gate_importable():
    try:
        import provenance_gate  # noqa: F401
        return True, None
    except Exception as e:  # pragma: no cover - environment dependent
        return False, str(e)


def _ledger_path(project):
    return os.path.join(project, LEDGER_NAME)


def cmd_init(project, actor="agent-lead"):
    project = os.path.abspath(project)
    os.makedirs(project, exist_ok=True)
    ok, why = _gate_importable()
    if not ok:
        print(f"[PREFLIGHT] REFUSE: provenance_gate not importable: {why}", file=sys.stderr)
        return 2
    # marker
    with open(os.path.join(project, GATE_MARKER), "w") as f:
        f.write("provenance-gate v2.0.0 enforced by ~/provenance-gate/bin/preflight.py\n")
    # ledger (genesis entry via real AppendOnlyLedger)
    from provenance_gate import AppendOnlyLedger, EvidenceArtifact, Tier
    lp = _ledger_path(project)
    if not os.path.exists(lp):
        led = AppendOnlyLedger(persist_path=lp)
        led.append("genesis-init", actor, "SPEC",
                   {"content": "provenance gate installed", "tier": "T5"})
    # local runner that calls this central guard
    runner = os.path.join(project, "run_gated.sh")
    central = os.path.abspath(__file__)
    with open(runner, "w") as f:
        f.write("#!/usr/bin/env bash\n"
                "# provenance-gated runner: refuses to start if the gate is absent.\n"
                'exec "%s" run "%s" -- "$@"\n' % (central, project))
    os.chmod(runner, 0o755)
    print(f"[PREFLIGHT] gate installed at {project}")
    print(f"           marker  : {GATE_MARKER}")
    print(f"           ledger  : {LEDGER_NAME}")
    print(f"           runner  : run_gated.sh  (use it instead of running the project directly)")
    return 0


def cmd_check(project):
    project = os.path.abspath(project)
    if not os.path.isdir(project):
        print(f"[PREFLIGHT] REFUSE: project dir missing: {project}", file=sys.stderr)
        return 2
    ok, why = _gate_importable()
    if not ok:
        print(f"[PREFLIGHT] REFUSE: provenance_gate not importable -> {why}", file=sys.stderr)
        return 2
    marker = os.path.join(project, GATE_MARKER)
    if not os.path.exists(marker):
        print(f"[PREFLIGHT] REFUSE: gate marker {GATE_MARKER} absent -> "
              f"project not governed; run: preflight.py init {project}", file=sys.stderr)
        return 2
    lp = _ledger_path(project)
    if not os.path.exists(lp):
        print(f"[PREFLIGHT] REFUSE: ledger {LEDGER_NAME} absent -> "
              f"no provenance trail; run: preflight.py init {project}", file=sys.stderr)
        return 2
    # verify chain integrity (tamper = refuse)
    try:
        from provenance_gate import AppendOnlyLedger
        AppendOnlyLedger(persist_path=lp).entries()
    except Exception as e:
        print(f"[PREFLIGHT] REFUSE: ledger tamper/load error -> {type(e).__name__}: {e}",
              file=sys.stderr)
        return 3
    print(f"[PREFLIGHT] OK: gate present, ledger intact at {project}")
    return 0


def cmd_run(project, cmd):
    rc = cmd_check(project)
    if rc != 0:
        print("[PREFLIGHT] PROJECT NOT RUN -- provenance gate requirement unmet.",
              file=sys.stderr)
        return rc
    if not cmd:
        print("[PREFLIGHT] nothing to run (no command after --)", file=sys.stderr)
        return 1
    return subprocess.call(cmd)


def cmd_verify(project):
    lp = _ledger_path(os.path.abspath(project))
    if not os.path.exists(lp):
        print(f"[PREFLIGHT] REFUSE: no ledger at {lp}", file=sys.stderr)
        return 2
    try:
        from provenance_gate import AppendOnlyLedger
        n = len(AppendOnlyLedger(persist_path=lp).entries())
        print(f"[PREFLIGHT] ledger OK: {n} entries, hash chain verified")
        return 0
    except Exception as e:
        print(f"[PREFLIGHT] REFUSE: ledger tamper -> {type(e).__name__}: {e}", file=sys.stderr)
        return 3


def usage():
    print(__doc__, file=sys.stderr)
    return 1


def main(argv):
    if len(argv) < 3:
        return usage()
    sub, project = argv[1], argv[2]
    if sub == "init":
        actor = argv[3] if len(argv) > 3 else "agent-lead"
        return cmd_init(project, actor)
    if sub == "check":
        return cmd_check(project)
    if sub == "verify":
        return cmd_verify(project)
    if sub == "run":
        sep = argv.index("--") if "--" in argv else None
        if sep is None:
            print("[PREFLIGHT] 'run' needs '-- <cmd...>'", file=sys.stderr)
            return 1
        return cmd_run(project, argv[sep + 1:])
    return usage()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
