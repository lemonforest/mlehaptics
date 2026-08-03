#!/usr/bin/env python3
"""Ripple-gate runner (`#T1063`) -- one command for the FAST dispatch-surface gates.

When a public op is registered or a ``ToolEntry`` is edited, the change *ripples*
to a fixed family of CI gates: the C tool registry, the carrier / rosetta / MCP
surfaces, the worked-example ledger, the ~55 ``describe()["tools"]["total"]``
count-pins, the ref-notation and JPL ratchets, and the version pin. That gate
list used to live only in a private memory file, so each build brief
hand-transcribed a subset and dropped gates (rc385 ate two CI-red rounds on the
worked-example family alone). This runner puts the list in the REPO, as one
runnable command, so an agent runs ``python3 tools/ripple_check.py`` before
pushing and the tree -- not a lossy human relay -- owns the gate set.

The gate list is the committed manifest ``tools/ripple_gates.txt`` (one target
per line; ``#`` comments and blank lines ignored). A companion meta-test,
``tests/test_ripple_manifest_covers_known_gates.py``, asserts the manifest can
never silently shrink below the known dispatch-surface families.

Usage
-----
    python3 tools/ripple_check.py            # run the gates (fast: seconds .. ~2 min)
    python3 tools/ripple_check.py --regen    # regen the surface FIRST, then run the gates
    python3 tools/ripple_check.py --regen-only   # run only the regen preamble
    python3 tools/ripple_check.py --list     # print the resolved gate targets, exit 0
    python3 tools/ripple_check.py --manifest PATH   # use an alternate manifest
    python3 tools/ripple_check.py -- -x -q   # forward extra args to pytest

Regen preamble (a dispatch-surface change usually needs regen FIRST)
--------------------------------------------------------------------
``--regen`` runs, in the load-bearing order:

    python3 tools/regen_all.py                        # rebuild every generated file + verify idempotence
    python3 tools/run_worked_examples.py --only-stale # refresh the executed-example ledger

These are DELIBERATELY two steps: ``run_worked_examples.py`` is not a codegen
step and is not run by ``regen_all.py``, but the executed-ledger gate
(``test_worked_examples_execute_rc354``) reds until the ledger is refreshed.
"regen, then verify" is one story; this runner is that story.

Exit code: the runner exits with pytest's return code (nonzero if any gate
fails). ``--regen`` aborts nonzero if the regen preamble itself fails.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # docs/srmech/python/tools
PKG_ROOT = _HERE.parent                           # docs/srmech/python
DEFAULT_MANIFEST = _HERE / "ripple_gates.txt"


def load_manifest(path: str | Path) -> list[str]:
    """Return the ordered list of pytest targets declared in a manifest file.

    A manifest line is a pytest target (``tests/foo.py`` or a node id
    ``tests/foo.py::test_bar``), resolved relative to the package root. Blank
    lines and lines whose first non-space character is ``#`` are dropped; an
    inline ``  # ...`` trailer (two-space guard, so ``::test_x#y`` is safe) is
    stripped.
    """
    targets: list[str] = []
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        marker = line.find("  #")
        if marker != -1:
            line = line[:marker].strip()
        if line:
            targets.append(line)
    return targets


def target_file(target: str) -> str:
    """The file part of a pytest target ('tests/x.py::test_y' -> 'tests/x.py')."""
    return target.split("::", 1)[0]


def _run(cmd: list[str], cwd: Path) -> int:
    print("+ " + " ".join(str(c) for c in cmd), flush=True)
    return subprocess.run(cmd, cwd=str(cwd)).returncode


def run_regen(pkg_root: Path) -> int:
    """Rebuild the dispatch surface: regen_all, THEN refresh the worked-example ledger."""
    rc = _run([sys.executable, "tools/regen_all.py"], pkg_root)
    if rc != 0:
        return rc
    return _run(
        [sys.executable, "tools/run_worked_examples.py", "--only-stale"], pkg_root
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="ripple_check.py",
        description="Run the FAST dispatch-surface ripple gates (see module docstring).",
    )
    ap.add_argument(
        "--regen",
        action="store_true",
        help="regenerate the dispatch surface FIRST (regen_all + run_worked_examples "
        "--only-stale), then run the gates",
    )
    ap.add_argument(
        "--regen-only",
        action="store_true",
        help="run only the regen preamble (no gates)",
    )
    ap.add_argument(
        "--list",
        action="store_true",
        help="print the resolved gate targets and exit 0",
    )
    ap.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST),
        help="alternate manifest file (used to prove the runner returns failure)",
    )
    ap.add_argument(
        "pytest_args",
        nargs="*",
        help="extra args forwarded to pytest (put them after a bare --)",
    )
    args = ap.parse_args(argv)

    targets = load_manifest(args.manifest)

    if args.list:
        for t in targets:
            print(t)
        return 0

    if args.regen or args.regen_only:
        rc = run_regen(PKG_ROOT)
        if rc != 0:
            print("ripple_check: regen preamble FAILED; aborting before gates",
                  file=sys.stderr)
            return rc
        if args.regen_only:
            return 0

    if not targets:
        print(f"ripple_check: manifest {args.manifest} has no targets", file=sys.stderr)
        return 1

    cmd = [
        sys.executable, "-m", "pytest",
        *targets,
        "-q", "-p", "no:cacheprovider",
        *args.pytest_args,
    ]
    return _run(cmd, PKG_ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
