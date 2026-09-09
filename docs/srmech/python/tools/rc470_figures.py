r"""EVERY FIGURE the rc470 (`#T1188`) prose quotes, re-printed by ONE run.

WHY THIS FILE EXISTS
--------------------
"No figure this run did not print" failed three times inside rc470's own
re-validation, and it failed for a reason that is a property of the RULE, not
of the people following it. A figure printed *when it was written* satisfies
"printed once", and is then carried past a later commit, a ledger
regeneration, a restore, or a sibling lane's report — and this branch had every
one of those after every figure was written. **The property that matters is a
property of the FINAL TREE, not of the writer.** So:

    Every figure in shipped prose is re-printed by ONE run executed after the
    LAST edit to the tree, and the prose is diffed against that run's output. A
    figure the final run cannot produce is DELETED, not adjusted. A figure
    carried from an earlier draft, an earlier commit's run, or another lane's
    report is INVENTED until re-printed.

This script is that run, and it is shipped rather than left in a scratchpad
because a load-bearing number owes its generating code
(`[[feedback_computational_provenance_discipline]]`).

THE STATIC-TREE WITNESS
-----------------------
Printing a number is not enough — the sibling lane that reported *"lexical
DECLARED is 246"* printed one. What it could not show was that the tree it
measured was the tree it thought it was measuring. So beside every figure this
run prints ``srmech.__file__``, and around the whole run it prints:

* ``git status --porcelain`` for each instrument, and whether the working-tree
  blob equals the ``HEAD`` blob;
* each instrument's blob sha256, taken at the START and again at the END, with
  an equality assertion — which is the direct evidence that nothing moved the
  tree DURING the measurement. Had this existed, Lane 1's failing run would
  have printed the mutant's blob beside its 246 and named the mutation instead
  of the integer.

THE PROSE DIFF
--------------
Each figure carries the LITERAL the prose must contain, built from the MEASURED
value. A figure that moves therefore renders a needle the prose does not hold,
and this script exits non-zero naming the file, the label and both values. It
is a diff, not a re-read: nothing here asserts that a number is *correct*, only
that the prose and this tree agree about it.

WHAT IT CANNOT DO, stated rather than left to be discovered
-----------------------------------------------------------
1. It checks PRESENCE of a rendered literal, not that the literal is in the
   sentence a reader would attach it to. A figure moved into an unrelated
   paragraph still passes.
2. The SUBSTANTIVE count (180) is 219 minus a HAND-MAINTAINED ledger. This run
   regenerates the 219 and the arithmetic; it cannot regenerate the hand-read.
   That is why the arc's baseline is quotable only as the PAIR.
3. Gate totals are re-run here, so this script is slow (~5 min). ``--quick``
   skips them and is NOT sufficient for a final run; it says so and exits with
   a marker.

numpy-free. No ``abs()``. Every digest routes through
``srmech.amsc.format.sha256_bytes``.
"""

from __future__ import annotations

import inspect
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

PY_ROOT = Path(__file__).resolve().parents[1]
REPO = PY_ROOT.parents[2]
sys.path.insert(0, str(PY_ROOT))
sys.path.insert(0, str(PY_ROOT / "tools"))

#: Everything whose bytes decide a figure below. The blob of each is printed
#: twice — before and after — and the two must agree.
INSTRUMENTS = (
    "tools/demotion_probe.py",
    "tools/rc470_figures.py",
    "tools/canfail_preload.py",
    "tests/test_r3_reader_rc470.py",
    "tests/test_declared_inexactness_rc466.py",
    "tests/test_silent_carrier_demotion_rc463.py",
    "tests/test_notebook_currency_rc420.py",
    "tests/demotion_census.ndjson",
    "CHANGELOG.md",
)

FAILURES = []
FIGURES = []


def _sha(b: bytes) -> str:
    from srmech.amsc.format import sha256_bytes
    return sha256_bytes(b)


def _git(*args) -> str:
    return subprocess.run(["git", "-C", str(REPO), *args],
                          capture_output=True, text=True).stdout


def snapshot() -> dict:
    return {rel: _sha(Path(PY_ROOT, rel).read_bytes()) for rel in INSTRUMENTS}


def figure(label, value, *needles, where="CHANGELOG.md"):
    """Record a measured figure and diff the prose against it.

    ``needles`` are format strings; ``{v}`` becomes the measured value. Every
    rendered needle must occur in ``where``.
    """
    import srmech
    FIGURES.append((label, value))
    text = Path(PY_ROOT, where).read_text(encoding="utf-8")
    bad = [n.format(v=value) for n in needles if n.format(v=value) not in text]
    mark = "OK " if not bad else "RED"
    print(f"  [{mark}] {label} = {value!r}   [srmech {srmech.__file__}]")
    for n in bad:
        print(f"        MISSING FROM {where}: {n!r}")
        FAILURES.append((where, label, value, n))


def main(argv) -> int:
    quick = "--quick" in argv
    t0 = time.time()

    import srmech
    from srmech import _native
    import demotion_probe as dp
    from srmech._resolve import resolve_dotted_callable
    from srmech.introspect.tool_schema import get_tool_schema

    print("=" * 78)
    print("rc470 FIGURE RUN  (`#T1188`)")
    print("=" * 78)
    print(f"srmech.__version__ {srmech.__version__}")
    print(f"srmech.__file__    {srmech.__file__}")
    print(f"HAS_NATIVE         {_native.HAS_NATIVE}")
    for mod in ("numpy", "sympy"):
        try:
            __import__(mod)
            print(f"{mod:18} PRESENT  <-- every figure below is quoted "
                  f"numpy/sympy-ABSENT; this run is NOT comparable")
        except ModuleNotFoundError:
            print(f"{mod:18} absent (ModuleNotFoundError)")
    print(f"git HEAD           {_git('rev-parse', 'HEAD').strip()}")
    print(f"git branch         {_git('rev-parse', '--abbrev-ref', 'HEAD').strip()}")

    print("\n-- STATIC-TREE WITNESS: instruments --")
    porcelain = _git("status", "--porcelain", "--",
                     *[f"docs/srmech/python/{r}" for r in INSTRUMENTS])
    print("git status --porcelain (instruments):")
    print("  " + ("\n  ".join(porcelain.splitlines()) or "(clean)"))
    before = snapshot()
    for rel, h in before.items():
        head = _git("rev-parse", f"HEAD:docs/srmech/python/{rel}").strip()
        live = _git("hash-object", str(Path(PY_ROOT, rel))).strip()
        print(f"  {rel:44} sha256 {h[:32]}…  "
              f"{'== HEAD' if head == live else '!= HEAD (uncommitted)'}")

    print("\n-- RULER 1: the R3 declaration reader --")
    tools = list(get_tool_schema().tools)
    fns = [(e.name, resolve_dotted_callable(e.name)) for e in tools]
    figure("registry entries", len(fns),
           "| entries / resolved / unresolved | **{v} / {v} / 0** |")
    declared = sorted(n for n, f in fns if dp.declaration_hits(f))
    figure("DECLARED, lexical", len(declared),
           "| DECLARED, after the comprehension fold in the delegate walk | **{v}**",
           "**{v} DECLARED lexically,")
    figure("reader_signature", dp.reader_signature(),
           "{v}", where="tests/demotion_census.ndjson")

    # the pinned ledger, read from the gate that owns it
    gate = Path(PY_ROOT, "tests/test_r3_reader_rc470.py").read_text(encoding="utf-8")
    blk = gate[gate.index("_RESIDUAL_TOPIC_MISREADS = {"):gate.index("#: The classes above")]
    pinned = re.findall(r'^    "([\w.]+)":', blk, re.M)
    figure("pinned topical misreads", len(pinned),
           "| — of those, **TOPICAL MISREADS** pinned by name | **{v}** |",
           "**39 cannot survive the question**".replace("39", "{v}"),
           "and the {v} of 222 readings that no lexical rule can fix")
    figure("substantive DECLARED", len(declared) - len(pinned),
           "| — **SUBSTANTIVE DECLARED** | **{v}** |",
           "**222 DECLARED lexically, 41 pinned as topical misreads, "
           "{v} substantive**")
    unknown = sorted(set(pinned) - set(declared))
    assert not unknown, f"pinned but not DECLARED: {unknown}"

    riders = [n for n in pinned
              if dp.declaration_hits(resolve_dotted_callable(n))[0].endswith(")")]
    figure("pins riding the delegate follow", len(riders),
           "Twenty-six of the {v} pins ride it".replace("{v}", str(len(pinned)))
           if len(riders) == 26 else "RIDERS-MOVED-{v}")

    # the rc469 (main) reader, re-implemented by reading main's own source
    #
    # ⚠️ THE MECHANISM IS HELD CONSTANT ON PURPOSE, and this is a REPAIR, not
    # a convenience. main's `declaration_hits` walks bare `code.co_names`, so
    # re-executing it verbatim inherits the very PEP 709 defect rc470's last
    # commit fixed: MEASURED, it reads 202 on CPython 3.10.21 and 3.11.16 and
    # **204** on 3.12.3 and 3.14.7 — so the published "202" was never a
    # property of the tree either, only a 3.10 reading, and this script's own
    # output would have depended on which interpreter ran it. Re-using main's
    # VOCABULARY over the SHIPPED (folded) delegate walk isolates the thing the
    # comparison is actually for — what the rc469 WORD LIST read — and yields
    # **204 on all of 3.10 / 3.11 / 3.12 / 3.14**. The delta this feeds
    # ("206 is the READER's move") is a vocabulary delta, and holding the
    # mechanism fixed is what makes it one.
    main_src = _git("show", "main:docs/srmech/python/tools/demotion_probe.py")
    ns = {"__name__": "demotion_probe_main_rc469", "__file__": "<main>"}
    exec(compile(main_src, "<main:tools/demotion_probe.py>", "exec"), ns)
    _vocab = ns["R3_VOCABULARY"]

    def old_hits(fn):
        """main's rc469 VOCABULARY over rc470's folded delegate walk."""
        doc = (inspect.getdoc(fn) or "").lower()
        hits = [d for d in _vocab if d in doc]
        try:
            if "exact" in inspect.signature(fn).parameters:
                hits.append("exact= opt-in")
        except (TypeError, ValueError):
            pass
        if not hits:
            code = getattr(fn, "__code__", None)
            glb = getattr(fn, "__globals__", {}) or {}
            for name in (dp._delegate_names(code) if code is not None else ()):
                delegate = glb.get(name)
                if delegate is None or delegate is fn or not callable(delegate):
                    continue
                ddoc = (inspect.getdoc(delegate) or "").lower()
                hits += [f"{d} (via {name})" for d in _vocab if d in ddoc]
                if hits:
                    break
        return hits

    old_declared = {n for n, f in fns if old_hits(f)}
    figure("DECLARED, rc469 reader", len(old_declared),
           "| DECLARED, rc469 reader | **{v}** |")
    figure("pins already DECLARED under rc469", len(set(pinned) & old_declared),
           "**{v} of the 41 read DECLARED under the rc469 reader too**")
    added = sorted(set(pinned) - old_declared)
    figure("pins the widening added", len(added), "The **SIX** the widening added"
           if len(added) == 6 else "WIDENING-ADDED-{v}")

    print("\n-- the NEGATION residuals --")
    WIDE = re.compile(r"\bno (?:more|worse|greater|larger) than\b", re.I)
    BARE = re.compile(r"\bno more than\b", re.I)
    # ⚠️ THE POPULATION EXCLUDES THE FILES WHOSE SUBJECT *IS* THIS RESIDUAL,
    # and the exclusion is the finding rather than a convenience. Both of them
    # QUOTE the shape they are counting, so each is inside its own population
    # and every edit to either moves the figure. Measured, twice: rewriting the
    # probe's disclosure took the count 10 -> 11, and adding THIS SCRIPT --
    # whose prose-diff needle contains the phrase verbatim -- took it 8 -> 9 on
    # its very first run. A self-referential population cannot be quoted
    # stably; naming the exclusion is the only honest way to quote it at all.
    EXCLUDE = tuple(sorted(
        (PY_ROOT / "tools" / n).resolve()
        for n in ("demotion_probe.py", "rc470_figures.py")))
    print("  population EXCLUDES (each one QUOTES the shape it counts):")
    for p in EXCLUDE:
        print(f"    {p.relative_to(PY_ROOT)}")
    reg_occ = sum(len(WIDE.findall(__import__("inspect").getdoc(f) or ""))
                  for _, f in fns)
    figure("bounding quantifier, 732 registry docstrings", reg_occ,
           "**{v} occurrences, 0 live instances**")
    for tag, rx, needle in (
            ("wide", WIDE, "**{v} occurrences on 6 LINES in 4 FILES**"),
            ("bare", BARE, "spelling gives **{v}** on that")):
        occ = lines = files = 0
        for sub in ("srmech", "tests", "tools"):
            for p in sorted((PY_ROOT / sub).rglob("*.py")):
                if p.resolve() in EXCLUDE:
                    continue
                got = [len(rx.findall(s)) for s in
                       p.read_text(encoding="utf-8", errors="replace").split("\n")
                       if rx.search(s)]
                if got:
                    files += 1
                    lines += len(got)
                    occ += sum(got)
        figure(f"bounding quantifier [{tag}], subtree minus the two "
               f"self-referential files", occ, needle)
        if tag == "wide":
            figure("  … on lines", lines, "occurrences on {v} LINES in")
            figure("  … in files", files, "LINES in {v} FILES**")

    print("\n-- the CENSUS --")
    cen = [json.loads(x) for x in
           Path(PY_ROOT, "tests/demotion_census.ndjson")
           .read_text(encoding="utf-8").splitlines() if x.strip()]
    meta = next(r for r in cen if r.get("record") == "meta")
    figure("census n_rows", meta["n_rows"], "`n_rows` {v}")
    figure("census n_ops", meta["n_ops"], "`n_ops` {v}")
    figure("registry_signature", meta["registry_signature_sha256"]["native"],
           "`{v}` in BOTH cells")
    for cell in ("native", "pure"):
        figure(f"undeclared roster [{cell}]", len(meta["undeclared"][cell]),
               "`EXPECTED_UNDECLARED_N` stays `{{\"native\": {v}, \"pure\": {v}}}`")
    figure("census reader_signature agrees with the live reader",
           meta["reader_signature_sha256"]["native"] == dp.reader_signature(),
           "written **per cell**")

    print("\n-- the DEF_BLOB drain (`fe3454677`) --")
    out = _git("show", "fe3454677", "--",
               "docs/srmech/python/tests/example_args_ledger.ndjson")
    plus, minus = {}, {}
    for line in out.split("\n"):
        if line[:2] in ("+{", "-{"):
            r = json.loads(line[1:])
            if r.get("record") != "meta":
                (plus if line[0] == "+" else minus)[r["op"]] = r
    mods, rows = set(), 0
    for op in set(plus) & set(minus):
        if minus[op].get("def_blob") != plus[op].get("def_blob"):
            mods.add(plus[op].get("def_module"))
            rows += 1
    figure("modules whose def_blob moved", len(mods), "**FIVE modules, not six**"
           if len(mods) == 5 else "DEFBLOB-MODULES-{v}")
    figure("rows whose def_blob moved", rows, "= {v} rows;")

    print("\n-- RULER 2: the notebook dead-path marker --")
    nb = Path(PY_ROOT, "tests/test_notebook_currency_rc420.py").read_text(encoding="utf-8")
    m = re.search(r"_PROSE_DEAD_PATH_CEIL\s*=\s*(\d+)", nb)
    figure("_PROSE_DEAD_PATH_CEIL", int(m.group(1)),
           "`_PROSE_DEAD_PATH_CEIL` goes **10 → {v}**")

    if quick:
        print("\n!! --quick: GATE TOTALS AND CAN-FAIL FIGURES NOT MEASURED.")
        print("!! This run is NOT a final figure run.")
    else:
        print("\n-- GATE TOTALS (re-run, foreground) --")
        sets = (
            (("tests/test_signal_processing_scaffolding.py",
              "tests/test_readme_currency_rc419.py",
              "tests/test_notebook_currency_rc420.py",
              "tests/test_frame_scope_rc430.py",
              "tests/test_synth_args_provenance_rc430.py",
              "tests/test_native_sha256.py"),
             "`test_native_sha256.py` → **{v} passed**"),
            (("tests/test_declared_inexactness_rc466.py",
              "tests/test_exact_twiddle_rc468.py",
              "tests/test_r3_reader_rc470.py"),
             "`test_r3_reader_rc470.py` → **{v} passed**"),
            (("tests/test_notebook_currency_rc420.py",),
             "`test_notebook_currency_rc420.py` → **{v} passed**"),
        )
        for i, (files, needle) in enumerate(sets, 1):
            n = _pytest_passed(files)
            figure(f"gate set {i}", n, needle)

        print("\n-- CAN-FAIL (mutants on a COPY; the tree is never written) --")
        import canfail_preload as cf
        tmp = Path(os.environ.get("TMPDIR", "/tmp")) / "rc470_figures_canfail"
        neg = cf.write_mutant(
            "demotion_probe",
            [("if _R3_NEG.search(sent[:m.start()]):", "if False:  # MUTANT")],
            tmp / "neg")
        stem_pat = ('    ("truncation",          r"' + chr(92) + "btruncation"
                    + chr(92) + "s+(?:remainder|error)" + chr(92) + 'b"\n'
                    '                            r"|' + chr(92) + "babsolute"
                    + chr(92) + "s+error" + chr(92) + 'b"),\n')
        stem = cf.write_mutant("demotion_probe", [(stem_pat, "")], tmp / "stem")
        print(f"  mutant(neg)  {neg}  sha256 {cf.blob_sha256(neg)[:32]}…")
        print(f"  mutant(stem) {stem} sha256 {cf.blob_sha256(stem)[:32]}…")
        gate_file = ("tests/test_r3_reader_rc470.py",)
        figure("r3 gate, clean", _pytest_line(gate_file),
               "clean **{v}**")
        figure("r3 gate, negation refusal disabled",
               _pytest_line(gate_file, mutant=tmp / "neg"),
               "(`if False:` on the clause-local guard) → **{v}**")
        figure("r3 gate, stated-bound stem removed",
               _pytest_line(gate_file, mutant=tmp / "stem"),
               "remove the stated-bound stem → **{v}**")

    print("\n-- STATIC-TREE WITNESS: instruments, AFTER --")
    after = snapshot()
    moved = [k for k in before if before[k] != after[k]]
    for rel in INSTRUMENTS:
        flag = "MOVED DURING THE RUN" if rel in moved else "unchanged"
        print(f"  {rel:44} sha256 {after[rel][:32]}…  {flag}")
    if moved:
        print(f"\n!! {len(moved)} INSTRUMENT(S) CHANGED WHILE THIS RUN WAS "
              f"MEASURING: {moved}. EVERY FIGURE ABOVE IS VOID — the tree was "
              f"not static. This is the exact condition that produced rc470's "
              f"phantom `246 != 219`.")
        FAILURES.append(("<tree>", "static-tree witness", moved, "unchanged"))

    print("\n" + "=" * 78)
    print(f"{len(FIGURES)} figures, {len(FAILURES)} disagreeing with the prose, "
          f"{time.time() - t0:.1f}s")
    if FAILURES:
        print("\nPROSE DISAGREES WITH THIS TREE:")
        for where, label, value, needle in FAILURES:
            print(f"  {where}: {label} measured {value!r}; prose does not "
                  f"contain {needle!r}")
        print("\nA figure the final run cannot produce is DELETED, not "
              "adjusted. Fix the prose, then re-run this script LAST.")
        return 1
    print("Every figure in the prose is reproduced by this run.")
    return 0


def _pytest_passed(files) -> int:
    return int(re.search(r"(\d+) passed", _pytest_line(files)).group(1))


def _pytest_line(files, mutant=None) -> str:
    env = dict(os.environ)
    if mutant is not None:
        env["CANFAIL_DIR"] = str(mutant)
        env["CANFAIL_MODULE"] = "demotion_probe"
        env["PYTHONPATH"] = str(PY_ROOT / "tools")
    cmd = [sys.executable, "-m", "pytest", *files, "-q", "-p", "no:cacheprovider"]
    if mutant is not None:
        cmd += ["-p", "canfail_preload"]
    out = subprocess.run(cmd, cwd=str(PY_ROOT), capture_output=True, text=True,
                         env=env).stdout
    tail = [x for x in out.strip().split("\n") if "passed" in x or "failed" in x]
    line = re.sub(r"\s+in\s+[\d.]+s.*$", "", tail[-1]) if tail else "<no result>"
    print(f"    pytest {' '.join(Path(f).name for f in files)}"
          f"{' [MUTANT ' + mutant.name + ']' if mutant else ''} -> {line}")
    return line


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
