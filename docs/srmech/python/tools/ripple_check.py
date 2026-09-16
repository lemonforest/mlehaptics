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

    python3 tools/regen_all.py               # rebuild every generated file + verify idempotence
    python3 tools/run_worked_examples.py     # re-execute the worked-example ledger, IN FULL

These are DELIBERATELY two steps: ``run_worked_examples.py`` is not a codegen
step and is not run by ``regen_all.py``, but the executed-ledger gate
(``test_worked_examples_execute_rc354``) reds until the ledger is refreshed.
"regen, then verify" is one story; this runner is that story.

The second step is a FULL re-execution (rc469, `#T1188`). It used to be scoped
by a stale selector keyed on the snippet-TEXT hash, which is blind to exactly
the change ``--regen`` exists to propagate: a regen moves the dispatch surface
UNDERNEATH snippets whose text has not moved a byte, so the scoped form
re-executed nothing and the runner reported a refreshed ledger it had not
refreshed. Full is the only spelling that keeps "regen, then verify" true.

⚠️ THE FULL RUN IS HOST-COUPLED, and the ledger's ceiling is right to be strict
about it. :func:`run_worked_examples.backfill`'s docstring records that the pure
cell is pinned at ``{unexpected_raise: 96, timeout: 1}`` while a native-Windows
re-run measures **97**, because one snippet
(``amsc.catalog.register_attested_root``) hardcodes a ``/mnt/d/...`` path for
the sister package's attested root. Run this under WSL2, or expect the ceiling
to name that snippet.

Exit code: the runner exits with pytest's return code (nonzero if any gate
fails). ``--regen`` aborts nonzero if the regen preamble itself fails.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
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


def _run(cmd: list[str], cwd: Path, env: dict | None = None) -> int:
    print("+ " + " ".join(str(c) for c in cmd), flush=True)
    return subprocess.run(cmd, cwd=str(cwd), env=env).returncode


def run_regen(pkg_root: Path) -> int:
    """Rebuild the dispatch surface: regen_all, THEN re-execute the ledger IN FULL.

    Full, not scoped: a regen changes the dispatch surface under snippets whose
    TEXT never moves, and the selector this used to pass hashed exactly that
    text. See the module docstring for the host coupling (WSL2; the pure cell's
    ceiling encodes one absolute path).
    """
    rc = _run([sys.executable, "tools/regen_all.py"], pkg_root)
    if rc != 0:
        return rc
    return _run([sys.executable, "tools/run_worked_examples.py"], pkg_root)


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


#: The forwarded pytest options this runner ACCEPTS (rc473 instrument repair 1,
#: `#T1188`). It is an allow-list: every other forwarded argument is refused
#: before anything runs. The manifest meta-test can see a line that narrows a
#: gate; it cannot see an option typed at run time.
#:
#: ⚠️ The instrument round shipped a DENY-list here — ``-k``, ``-m``,
#: ``--deselect`` and nine more — and gate round i1 ran ``-xk``, ``-qk``,
#: ``-o addopts=-k ...`` and ``--setup-plan`` straight past it, with this runner
#: exiting 0 on a subset or on nothing. A deny-list must name every spelling of a
#: filter, and pytest's parser accepts more spellings than a list names (short
#: flags CLUSTER, and ``addopts`` can be overridden from the command line).
#:
#: pytest 9.0.3's ``--help`` describes each option below as changing what is
#: REPORTED (verbosity, report characters, tracebacks, locals, header, colour,
#: durations), how output is CAPTURED, or when a failing run STOPS; none of those
#: descriptions selects, skips or replaces a test. (Until instrument repair 2,
#: `#T1188`, this sentence said so without naming its source; other pytest
#: versions' help was not read.) ``-x`` / ``--maxfail`` stop early only after
#: a failure, so the run is red either way. Short flags cluster (``-xq``,
#: ``-vv``); ``-r`` takes the rest of its cluster, or the next argument, as its
#: report characters. And the list is not the only guard: the gate run loads
#: ``tests/_collection_count_plugin.py``, and :func:`judge_counts` fails a green
#: run whose counts show an item collected but not kept, deselected, or not run,
#: or whose per-item accounting shows a collected node id that did not run (or a
#: node id that ran and was not collected).
#: (Instrument repair 2, `#T1188`: this read "fails a green run whose collection
#: lost an item, however that removal was spelled". Gate round i2 found a conftest
#: hookwrapper that removed an item before the plugin's first count. Instrument
#: repair 3: it then read four TOTALS, and gate round j1 measured two geometries
#: that move no total — a setup-only protocol, which runs no test body, and a
#: substitution, which drops one item and repeats another. The removals the check
#: was measured to see, and the ones it cannot, are listed in :func:`judge_counts`
#: and the plugin's docstring.)
ALLOWED_SHORT_FLAGS = frozenset("xqvsl")
ALLOWED_LONG_FLAGS = frozenset({"--exitfirst", "--quiet", "--verbose",
                                "--showlocals", "--no-header", "--full-trace"})
#: Long options that take a value, each with the values accepted for it.
ALLOWED_LONG_VALUED = {
    "--maxfail": re.compile(r"[0-9]+"),
    "--tb": re.compile(r"auto|long|short|no|line|native"),
    "--capture": re.compile(r"fd|sys|no|tee-sys"),
    "--durations": re.compile(r"[0-9]+"),
    "--durations-min": re.compile(r"[0-9]+(?:\.[0-9]+)?"),
    "--color": re.compile(r"yes|no|auto"),
}
_REPORT_CHARS = re.compile(r"[A-Za-z]+")

#: The plugin the gate run loads, and the variable naming the file it writes.
COUNT_PLUGIN = "tests._collection_count_plugin"
COUNT_ENV = "SRMECH_COLLECTION_COUNT_OUT"
#: The per-item accounting that plugin writes beside the four totals (instrument repair
#: 3, `#T1188`): the node ids in one of its two multisets and not in the other, each as
#: ``{"n": <exact count>, "names": [...]}``. Counts compare cardinalities, and gate round
#: j1 measured a substitution that leaves every cardinality equal.
COUNT_ID_DIFFS = ("selected_missing", "selected_extra", "ran_missing", "ran_extra")


def refused_forwarded_args(pytest_args: list[str]) -> list[str]:
    """Every forwarded argument that is not on the allow-list, in order.

    Walks the arguments the way pytest's own parser reads them: a single-dash
    argument is a CLUSTER of short flags (``-xk pin`` is ``-x`` and then
    ``-k pin``), a long option may carry ``=value``, and a value-taking option
    consumes the next argument. Anything else — a short flag outside
    :data:`ALLOWED_SHORT_FLAGS`, an unlisted long option, a value the option does
    not accept, a positional argument — is returned rather than guessed at.
    """
    bad: list[str] = []
    i = 0
    while i < len(pytest_args):
        arg = pytest_args[i]
        i += 1
        if arg.startswith("--"):
            name, eq, value = arg.partition("=")
            if name in ALLOWED_LONG_FLAGS and not eq:
                continue
            rx = ALLOWED_LONG_VALUED.get(name)
            if rx is not None:
                if not eq and i < len(pytest_args):
                    value = pytest_args[i]
                    i += 1
                if (eq or value) and rx.fullmatch(value):
                    continue
            bad.append(arg)
        elif arg.startswith("-") and len(arg) > 1:
            letters = arg[1:]
            for j, ch in enumerate(letters):
                if ch in ALLOWED_SHORT_FLAGS:
                    continue
                if ch == "r":
                    chars = letters[j + 1:]
                    if not chars and i < len(pytest_args):
                        chars = pytest_args[i]
                        i += 1
                    if not _REPORT_CHARS.fullmatch(chars):
                        bad.append(arg)
                    break
                bad.append(arg)
                break
        else:
            bad.append(arg)
    return bad


def read_counts(path: str | Path) -> dict | None:
    """The counts and per-item accounting ``tests/_collection_count_plugin.py``
    wrote, or ``None`` when it wrote nothing readable."""
    try:
        text = Path(path).read_text(encoding="utf-8")
        data = json.loads(text) if text.strip() else None
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def judge_counts(rc: int, counts: dict | None) -> int:
    """pytest's return code, unless the run it reports on is not the manifest's.

    (rc473 instrument repairs 1, 2 and 3, `#T1188`.) ``tests/_collection_count_plugin.py``
    writes what the gate run collected (``pytest_itemcollected``), kept once collection
    finished, deselected and ran (an item whose protocol reached the ``call`` phase, or
    whose ``setup`` report was not ``passed``), plus the node ids that are in one of
    those multisets and not the other. A GREEN run fails when ``selected`` or ``ran``
    differs from ``collected``, when anything was deselected, when any of the four id
    differences is non-empty, or when the plugin wrote no counts or no id accounting. A
    red run keeps pytest's own code.

    ⚠️ Instrument repair 1 said this fails a green run that lost an item "whatever
    removed" it. It compared ``selected`` with a first count read in a ``tryfirst``
    hookwrapper, and gate round i2 ran a conftest ``tryfirst`` hookwrapper that
    filtered before its ``yield`` past it, the runner exiting 0 on a run that had
    lost items.

    ⚠️ Instrument repair 2 then compared four TOTALS, with ``ran`` counted from
    ``setup``-phase reports, and gate round j1 measured two geometries that pass those
    four: a setup-only protocol (``--setup-plan`` / ``--setup-only`` from an ini
    ``addopts``, or ``setuponly`` set by a conftest ``pytest_configure``), which logs a
    ``setup`` report for every item and calls no test function; and a substitution,
    which drops one item and repeats another, moving no total at all. Hence ``ran`` at
    the ``call`` phase and the ids. What this function is measured to fail, and what the
    plugin cannot see (an item that never reaches ``pytest_itemcollected``; an item that
    runs and is reported skipped; an item whose BODY is replaced), are listed in that
    plugin's docstring and in the rc473 CHANGELOG, INSTRUMENT REPAIR 3.
    """
    if (counts is None or not isinstance(counts.get("collected"), int)
            or not isinstance(counts.get("ran"), int)):
        print("ripple_check: FAILED -- the gate run reported no collection counts "
              f"({COUNT_PLUGIN} wrote nothing readable), so it cannot show that it "
              "ran what the manifest collects.", file=sys.stderr)
        return rc or 1
    collected, selected = counts["collected"], counts.get("selected")
    deselected, ran = counts.get("deselected") or 0, counts["ran"]
    diffs = {name: counts.get(name) for name in COUNT_ID_DIFFS}
    if any(not isinstance(d, dict) or not isinstance(d.get("n"), int)
           for d in diffs.values()):
        print("ripple_check: FAILED -- the gate run reported counts without the "
              f"per-item accounting ({COUNT_PLUGIN} wrote no "
              f"{' / '.join(COUNT_ID_DIFFS)}), so the counts cannot show WHICH items "
              "ran.", file=sys.stderr)
        return rc or 1
    off = {name: d for name, d in diffs.items() if d["n"]}
    if selected != collected or deselected or ran != collected or off:
        if rc != 0 and selected == collected and not deselected and not off:
            print(f"ripple_check: red -- the gate run collected {collected} items and "
                  f"ran {ran}; pytest exited {rc}.", flush=True)
            return rc
        detail = "; ".join(f"{name} {d['n']} ({', '.join(d['names'])})"
                           for name, d in off.items())
        print(f"ripple_check: FAILED -- the gate run collected {collected} items, kept "
              f"{selected} ({deselected} deselected) and ran {ran}"
              + (f" -- by node id: {detail}" if off else "")
              + ". A run that did not run every item the manifest collects is not the "
                "manifest's run, and its green would read as the manifest's.",
              file=sys.stderr)
        return rc or 1
    print(f"ripple_check: the gate run ran all {collected} items the manifest's "
          "targets collect -- the node ids that ran are the node ids collected, none "
          "missing and none repeated", flush=True)
    return rc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="ripple_check.py",
        description="Run the FAST dispatch-surface ripple gates (see module docstring).",
    )
    ap.add_argument(
        "--regen",
        action="store_true",
        help="regenerate the dispatch surface FIRST (regen_all + a FULL "
        "run_worked_examples), then run the gates",
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

    # REFUSED before anything runs (rc473 instrument round, `#T1188`; an
    # allow-list since instrument repair 1): a forwarded `-k` / `-xk` /
    # `-o addopts=...` / `--setup-plan` ... narrows the gate run to a subset no
    # manifest reader can see, or runs nothing, and the runner would then report
    # that green as the manifest's. PYTEST_ADDOPTS reaches the same parser from
    # the environment, and PYTEST_PLUGINS loads a module into the gate run (and
    # into every pytest child a gate starts), which can remove items; a non-empty
    # value of either is refused (PYTEST_PLUGINS since instrument repair 2).
    refused = refused_forwarded_args(args.pytest_args)
    if refused:
        print("ripple_check: REFUSED -- forwarded pytest argument(s) "
              f"{refused} are not on this runner's allow-list (-x -q -v -s -l, "
              "-r<chars>, --tb, --maxfail, --capture, --durations, "
              "--durations-min, --color, --exitfirst, --quiet, --verbose, "
              "--showlocals, --no-header, --full-trace). Anything else can "
              "narrow the gate run to a subset the manifest does not name, and a "
              "green subset would read as a green manifest. Run the whole "
              "manifest, or run pytest on the file you want directly.",
              file=sys.stderr)
        return 2
    for name in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS"):
        if os.environ.get(name, "").strip():
            print(f"ripple_check: REFUSED -- {name} is set ({os.environ[name]!r}). "
                  "pytest reads it from the environment, past this runner's "
                  "allow-list; unset it for the ripple sweep.", file=sys.stderr)
            return 2

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

    # The gate run loads tests/_collection_count_plugin.py (instrument repairs 1,
    # 2 and 3, `#T1188`), and judge_counts fails a green run whose counts show an
    # item collected but not kept, deselected, or not run, or whose per-item
    # accounting shows a collected node id that did not run. (This read "whatever
    # spelling removed it" until instrument repair 2, and compared four totals
    # until instrument repair 3, which gate round j1 passed with a setup-only
    # protocol and with a substitution; see judge_counts for what the counts and
    # ids were measured to see and what they cannot.)
    fd, count_path = tempfile.mkstemp(prefix="ripple_count_", suffix=".json")
    os.close(fd)
    try:
        cmd = [
            sys.executable, "-m", "pytest",
            *targets,
            "-q", "-p", "no:cacheprovider", "-p", COUNT_PLUGIN,
            *args.pytest_args,
        ]
        rc = _run(cmd, PKG_ROOT, env=dict(os.environ, **{COUNT_ENV: count_path}))
        return judge_counts(rc, read_counts(count_path))
    finally:
        try:
            os.unlink(count_path)
        except OSError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
