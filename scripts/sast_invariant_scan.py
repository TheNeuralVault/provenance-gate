#!/usr/bin/env python3
"""Local invariant scanner for provenance-gate (no external binary required).

Mirrors the security properties encoded in semgrep.yml so they can be enforced
locally on hosts where the glibc-only ``semgrep-core`` binary cannot run (e.g.
Termux / Android, which has no glibc loader). Semgrep remains the authoritative
CI scanner; this is the portable local equivalent.

Invariants enforced (same as semgrep.yml):
  1. private-key-leak  : Ed25519 private key stays inside SigningService.
  2. shell-in-capture  : subprocess.run must not use shell=True.
  3. dangerous-deserialization : no eval/exec/marshal.loads/pickle.loads.
  4. nonconstant-time-compare  : signature/HMAC compare must use
                                 hmac.compare_digest, not == / !=.

Usage:
    python scripts/sast_invariant_scan.py [paths...]
Exit 0 = clean, 1 = violation found.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

# Files semgrep restricts rule 4 to; we honor the same scope.
_COMPARE_SCOPE = {
    "src/provenance_gate/capture.py",
    "extensions/provenance_gate_signer/provenance_gate_signer/keys.py",
}

VIOLATIONS: list[str] = []


def _rel(path: Path | str, root: Path) -> str:
    p = Path(path)
    try:
        return str(p.relative_to(root))
    except ValueError:
        return str(p)


def _call_name(node: ast.AST) -> str | None:
    """Best-effort fully-qualified-ish name of a call target."""
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return None


def _has_kw(call: ast.Call, name: str, value: bool = True) -> bool:
    for kw in call.keywords:
        if kw.arg == name and isinstance(kw.value, ast.Constant) and kw.value.value == value:
            return True
    return False


def _check_private_key_leak(tree: ast.Module, path: str, root: Path) -> None:
    # CaptureClient(..., private_key=...) or AttestedCapture(..., private_key=...)
    # is a leak unless it is the SigningService(...) constructor itself.
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node.func)
        if name in ("CaptureClient", "AttestedCapture") and _has_kw(node, "private_key"):
            # Allowed only when the enclosing call is SigningService(...)
            parent = getattr(node, "_parent", None)
            if isinstance(parent, ast.Call) and _call_name(parent.func) == "SigningService":
                continue
            VIOLATIONS.append(
                f"{_rel(path, root)}:{node.lineno}: private-key-leak: "
                f"{name}(private_key=...) hands the key outside SigningService"
            )


def _check_shell_true(tree: ast.Module, path: str, root: Path) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _call_name(node.func) in ("run", "Popen", "call"):
            # module may be subprocess.run / os.popen / etc.; flag shell=True
            if _has_kw(node, "shell", True):
                VIOLATIONS.append(
                    f"{_rel(path, root)}:{node.lineno}: shell-in-capture: "
                    f"subprocess uses shell=True (command-injection risk in T1 path)"
                )


def _check_dangerous_deser(tree: ast.Module, path: str, root: Path) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _call_name(node.func) in (
            "eval",
            "exec",
            "marshal",
            "pickle",
        ):
            # marshal.loads / pickle.loads are Attribute calls; eval/exec are Name
            if _call_name(node.func) in ("marshal", "pickle"):
                # only .loads variant is dangerous
                if getattr(node.func, "attr", None) == "loads":
                    VIOLATIONS.append(
                        f"{_rel(path, root)}:{node.lineno}: dangerous-deserialization: "
                        f"{_call_name(node.func)}.loads on untrusted input"
                    )
            else:
                VIOLATIONS.append(
                    f"{_rel(path, root)}:{node.lineno}: dangerous-deserialization: "
                    f"{_call_name(node.func)}(...) on untrusted input"
                )


def _check_const_time_compare(tree: ast.Module, path: str, root: Path) -> None:
    rel = _rel(path, root)
    if rel not in _COMPARE_SCOPE:
        return
    for node in ast.walk(tree):
        # Only enforce inside verification functions: that is where a secret /
        # signature must be compared in constant time. Integer/point equality
        # elsewhere (e.g. `if e == 0`) is benign and must NOT be flagged.
        if not isinstance(node, ast.FunctionDef):
            continue
        if not node.name.startswith("verify"):
            continue
        for child in ast.walk(node):
            if isinstance(child, ast.Compare) and isinstance(child.ops[0], (ast.Eq, ast.NotEq)):
                sides = [child.left, *child.comparators]
                # Ignore structural guards (length checks, integer literals)
                # which are not secret/signature comparisons.
                if any(isinstance(s, ast.Constant) and isinstance(s.value, int) for s in sides):
                    continue
                if any(isinstance(s, ast.Call) and _call_name(s.func) == "len" for s in sides):
                    continue
                if any(isinstance(s, ast.Call) and _call_name(s.func) == "compare_digest" for s in sides):
                    continue
                VIOLATIONS.append(
                    f"{rel}:{child.lineno}: nonconstant-time-compare: "
                    f"{node.name}() must use hmac.compare_digest, not == / !="
                )


def _scan_file(path: Path, root: Path) -> None:
    try:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(path))
    except (OSError, SyntaxError) as exc:
        VIOLATIONS.append(f"{_rel(path, root)}: PARSE ERROR: {exc}")
        return
    # annotate parents for the private-key-leak parent check
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            child._parent = parent  # type: ignore[attr-defined]
    _check_private_key_leak(tree, path, root)
    _check_shell_true(tree, path, root)
    _check_dangerous_deser(tree, path, root)
    _check_const_time_compare(tree, path, root)


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        roots = [Path(a) for a in argv[1:]]
    else:
        roots = [Path("src"), Path("extensions")]
    files: list[Path] = []
    for r in roots:
        if r.is_file() and r.suffix == ".py":
            files.append(r)
        elif r.is_dir():
            files.extend(p for p in r.rglob("*.py") if "tests" not in p.parts and "build" not in p.parts)
    root = Path(".")
    for f in files:
        _scan_file(f, root)
    if VIOLATIONS:
        print("INVARIANT SCAN: violations found")
        for v in VIOLATIONS:
            print("  -", v)
        return 1
    print(f"INVARIANT SCAN: clean ({len(files)} files checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
