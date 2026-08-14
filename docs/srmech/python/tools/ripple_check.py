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
    python3 tools/ripple_check.py            # collect-sweep, then run the gates
    python3 tools/ripple_check.py --regen    # regen the surface FIRST, then run the gates
    python3 tools/ripple_check.py --regen-only   # run only the regen preamble
    python3 tools/ripple_check.py --collect-only # run ONLY the collection sweep
    python3 tools/ripple_check.py --list     # print the resolved gate targets, exit 0
    python3 tools/ripple_check.py --manifest PATH   # use an alternate manifest
    python3 tools/ripple_check.py -- -x -q   # forward extra args to pytest

COLLECTION SWEEP -- runs FIRST, always, and is not optional (rc424, `#T1113`)
-----------------------------------------------------------------------------
Before any gate runs, this runner does a whole-suite ``pytest --collect-only``
and ABORTS on any collection error.

It is here because of a measured failure mode this runner could not see. rc424
renamed ``closed_form_ops/music.py`` to ``music_doa.py`` and left ONE stale
importer in an unrelated test file. CI went red on **twelve jobs** -- all six
pure shards, every native cell, asserts-live and the partition guard -- from
that single line, because **an import error at COLLECTION kills the whole
shard**: pytest never gets far enough to run anything, so the breadth of the
red reflects the failure MODE, not the blast radius.

The critical part: this runner was **GREEN** on the same tree. Every gate in
the manifest imported fine; the stale importer was in a file no gate targets.
A rename is therefore invisible BOTH to targeted tests AND to a manifest-driven
runner -- the manifest can only ever see the files it names, and the whole
point of a rename defect is that it breaks a file nobody thought to name.

A collect-only sweep has the opposite shape: it touches EVERY import in the
suite without executing a single test. Measured on this tree: ~14.5k tests
resolved in ~49 s. That is a different axis from the two gates already added
for adjacent blind spots -- rc421's search-corpus witness (prose drift) and
rc422's README currency (shipped literals) -- and it is the cheapest instrument
in the set relative to what it catches.

It is deliberately NOT a ``ripple_gates.txt`` line. The manifest is a list of
pytest TARGETS, and this is a sweep over the whole suite rather than a target;
encoding it as one would misfile it and, worse, subject it to the same
"only sees what it names" limit it exists to escape. Instead
``tests/test_ripple_manifest_covers_known_gates.py`` pins that this runner
still performs the sweep, so it cannot be quietly dropped.

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


#: The whole-suite import sweep. ``--collect-only`` resolves every test in
#: ``tests/`` WITHOUT executing one, so it costs a fraction of a run and sees
#: every import -- including the files no gate targets, which is exactly where
#: a rename defect hides. ``-q`` keeps the output to the summary line;
#: ``--no-header`` and ``no:cacheprovider`` keep it side-effect-free.
COLLECT_SWEEP = ["-m", "pytest", "tests/", "--collect-only", "-q",
                 "--no-header", "-p", "no:cacheprovider"]


def run_collect_sweep(pkg_root: Path) -> int:
    """Resolve every test in the suite; nonzero on ANY collection error.

    pytest exits 2 when collection fails, so the RETURN CODE alone decides --
    no output parsing, nothing to drift.

    Output is captured rather than streamed for one practical reason:
    ``--collect-only -q`` prints one line per test, and this suite has ~14.5k
    of them. Dumping that on every run would bury the gate results that follow
    and train a reader to skip the runner's output, which is the opposite of
    what a pre-push check is for. On SUCCESS only pytest's own summary line is
    echoed; on FAILURE the entire captured output is replayed, because that is
    the moment the detail matters.
    """
    cmd = [sys.executable, *COLLECT_SWEEP]
    print("+ " + " ".join(str(c) for c in cmd), flush=True)
    proc = subprocess.run(cmd, cwd=str(pkg_root), text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    lines = [ln for ln in (proc.stdout or "").splitlines() if ln.strip()]
    if proc.returncode == 0:
        print(lines[-1] if lines else "(collected, no summary line)", flush=True)
    else:
        print(proc.stdout or "", flush=True)
    return proc.returncode


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
        "--collect-only",
        action="store_true",
        help="run ONLY the whole-suite collection sweep (no regen, no gates)",
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

    if args.collect_only:
        return run_collect_sweep(PKG_ROOT)

    if args.regen or args.regen_only:
        rc = run_regen(PKG_ROOT)
        if rc != 0:
            print("ripple_check: regen preamble FAILED; aborting before gates",
                  file=sys.stderr)
            return rc
        if args.regen_only:
            return 0

    # THE COLLECTION SWEEP, before anything else and not optional. A file that
    # cannot be IMPORTED reports no failures -- it reports nothing -- so gate
    # results computed after a collection error are not merely incomplete, they
    # are misleading. Running it first means a stale importer is named here, in
    # seconds, instead of arriving as a dozen red CI jobs whose breadth hides a
    # one-line cause. See the module docstring for the measured rc424 case.
    rc = run_collect_sweep(PKG_ROOT)
    if rc != 0:
        print(
            "ripple_check: COLLECTION FAILED -- some test file cannot be "
            "imported.\n"
            "  Gate results are meaningless until this is fixed: a shard that "
            "fails to collect\n"
            "  runs nothing, so it reports no failures rather than the right "
            "ones.\n"
            "  Fix the import above, then re-run.",
            file=sys.stderr,
        )
        return rc

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
