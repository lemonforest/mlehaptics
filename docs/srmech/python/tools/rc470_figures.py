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

⚠️ rc471 (`#T1188`): THE APPARATUS MOVED OUT; THE FIGURES STAYED
----------------------------------------------------------------
The run, the witness, the prose diff and the pytest plumbing now live in
``tools/figure_run.py``, so every later rc gets them without copying this file.
What remains here is rc470's OWN figures and nothing else.

**And this file was DEAD when rc471 opened.** It read its comparison baseline
from ``main``, so the day rc470 merged, ``main`` became rc470 and the name the
baseline reader wanted (``R3_VOCABULARY``) was gone — ``KeyError`` at what was
then line 215, MEASURED on the rc471 branch before anything else was touched.
A harness the whole arc depends on cannot carry a moving part. The baseline is
now the immutable commit :data:`R3_BASELINE_COMMIT`, asserted by the sha256 of
the file it reads, and ``figure_run.assert_immutable_baseline`` refuses a
branch or a tag outright. This file already contained the right precedent one
section further down — the ``def_blob`` drain is read at the raw SHA
``fe3454677`` — and contradicted itself.

THE STATIC-TREE WITNESS
-----------------------
Printing a number is not enough — the sibling lane that reported *"lexical
DECLARED is 246"* printed one. What it could not show was that the tree it
measured was the tree it thought it was measuring. So beside every figure this
run prints ``srmech.__file__``, and around the whole run it prints each
instrument's blob sha256, taken at the START and again at the END, with an
equality assertion — the direct evidence that nothing moved the tree DURING the
measurement.

⚠️ The ``== HEAD`` column is EOL-NORMALISED as of rc471, because it could not
previously return anything BUT ``!= HEAD``: see ``figure_run.head_state``.

THE PROSE DIFF
--------------
Each figure carries the LITERAL the prose must contain, built from the MEASURED
value. A figure that moves therefore renders a needle the prose does not hold,
and this script exits non-zero naming the file, the label and both values. It
is a diff, not a re-read: nothing here asserts that a number is *correct*, only
that the prose and this tree agree about it.

⚠️ rc471 WIDENED THE POPULATION, AND IT WENT RED ON ITS FIRST RUN. Through
rc470 the diff read exactly TWO files (``CHANGELOG.md`` and
``tests/demotion_census.ndjson``) while NINE were hash-witnessed — it witnessed
the others' bytes and never read their prose, which is how a stale comment
survived rc470's own freshness discipline. ``tests/test_r3_reader_rc470.py`` is
now in the population, and :func:`_the_gates_own_baseline_line` reads the
``MEASURED at`` comment that names the arc's baseline triple. It disagrees with
this tree, and the disagreement is the finding, not a failure of the run.

WHAT IT CANNOT DO, stated rather than left to be discovered
-----------------------------------------------------------
1. It checks PRESENCE of a rendered literal, not that the literal is in the
   sentence a reader would attach it to. A figure moved into an unrelated
   paragraph still passes.
2. The SUBSTANTIVE count (182) is 223 minus a HAND-MAINTAINED ledger. This run
   regenerates the 223 and the arithmetic; it cannot regenerate the hand-read.
   That is why the arc's baseline is quotable only as the PAIR.
3. Gate totals are re-run here, so this script is slow. ``--quick`` skips them
   and is NOT sufficient for a final run; it says so and exits with a marker.
   ``--control`` ADDS the per-set pytest shape beside the union and diffs the
   two; it never changes a reported figure, only checks one.

numpy-free. No ``abs()``. Every digest routes through
``srmech.amsc.format.sha256_bytes``.
"""

from __future__ import annotations

import inspect
import json
import os
import re
import sys
from pathlib import Path

PY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PY_ROOT))
sys.path.insert(0, str(PY_ROOT / "tools"))

import figure_run as fr  # noqa: E402  (path set above)

#: THE IMMUTABLE BASELINE. ``1fd37c736`` is the commit the ``srmech-v0.9.0rc469``
#: tag names; the SHA rather than the tag, following this file's own
#: ``fe3454677`` precedent, because a tag is a pointer. Two other commits carry
#: a byte-identical probe (``fc717212d``, ``dd9b174c8``; all three resolve to
#: git blob ``74677bb55c31bbe579f9add843a16c865f99d0b8``), so the pin is a
#: choice of PROVENANCE, not of content.
R3_BASELINE_COMMIT = "1fd37c736"

#: sha256 of ``R3_BASELINE_COMMIT:docs/srmech/python/tools/demotion_probe.py``.
#: Without it, a SHA that resolves but names the WRONG tree fails later with a
#: ``KeyError`` on whatever name is missing — which is precisely how the ``main``
#: baseline failed. With it, a misidentified pin fails HERE, with both digests.
R3_BASELINE_SHA256 = (
    "497aa882a2159e90cc8e6b96ef0de244b853df117e9bc358d88e7c59aa07ebb7")

#: Everything whose bytes decide a figure below. The blob of each is printed
#: twice — before and after — and the two must agree. rc471 added
#: ``tools/figure_run.py``: the apparatus now lives there, so its bytes decide
#: every figure this file prints.
INSTRUMENTS = (
    "tools/demotion_probe.py",
    "tools/rc470_figures.py",
    "tools/figure_run.py",
    "tools/canfail_preload.py",
    "tests/test_r3_reader_rc470.py",
    "tests/test_declared_inexactness_rc466.py",
    "tests/test_silent_carrier_demotion_rc463.py",
    "tests/test_notebook_currency_rc420.py",
    "tests/demotion_census.ndjson",
    "CHANGELOG.md",
)

#: The gate sets, unchanged from rc470. rc471 runs their UNION in ONE pytest
#: and splits the tally back per file; ``--control`` re-runs the old per-set
#: shape and diffs, because one agreeing run is not proof of order-independence.
GATE_SETS = (
    ("tests/test_signal_processing_scaffolding.py",
     "tests/test_readme_currency_rc419.py",
     "tests/test_notebook_currency_rc420.py",
     "tests/test_frame_scope_rc430.py",
     "tests/test_synth_args_provenance_rc430.py",
     "tests/test_native_sha256.py"),
    ("tests/test_declared_inexactness_rc466.py",
     "tests/test_exact_twiddle_rc468.py",
     "tests/test_r3_reader_rc470.py"),
    ("tests/test_notebook_currency_rc420.py",),
)

#: The needle each gate set's figure is diffed against. rc471 moved these off
#: rc470's "**N passed**" sentences and onto its own, because ``passed`` is not
#: a property of the tree — see the ⚠️ in :func:`main`. The rc470 figures are
#: still COMPARED, and printed beside each set, but they are the reading of a
#: different cell and are not the diff target.
GATE_NEEDLES = (
    "gate set 1 → **{v} collected**",
    "gate set 2 → **{v} collected**",
    "gate set 3 → **{v} collected**",
)

#: What the rc470 entry quotes for each set, from a NATIVE-PRESENT host
#: (`CHANGELOG.md`, the rc470 gate-totals paragraph). Printed as a comparison,
#: never asserted: this tree cannot reproduce a native-cell reading.
RC470_QUOTED = (166, 192, 40)

#: The R3 gate whose can-fail figures this run reproduces.
R3_GATE = ("tests/test_r3_reader_rc470.py",)

#: The gate file whose OWN prose the widened diff now reads (rc471, W1.7).
R3_GATE_FILE = "tests/test_r3_reader_rc470.py"

_MEASURED_AT = re.compile(
    r"MEASURED at [\d.a-z]+: (\d+) DECLARED, (\d+) pinned here, "
    r"\*\*(\d+) substantive\*\*")


def _the_gates_own_baseline_line(run, declared, pinned, substantive):
    """Diff the gate's own ``MEASURED at`` comment against this tree.

    This is the figure the rc470 population could not hold: the gate is
    hash-witnessed but its PROSE was never read, so a comment naming the arc's
    baseline triple could drift from the assertions ten lines below it in the
    same file and nothing fired.
    """
    text = run.prose(R3_GATE_FILE)
    # rc472 repair pass (`#T1188`): the LAST such line, not the first. rc472
    # appended its triples BELOW rc471's, so `.search()` kept reading rc471's
    # (223, 41, 182) against a tree that measures (236, 41, 195) and printed
    # RED for a disagreement that was this reader's, not the gate's. The gate
    # file keeps the dated chain in order and ends it with the live triple.
    found = list(_MEASURED_AT.finditer(text))
    m = found[-1] if found else None
    if m is None:
        run.figure("gate's MEASURED-at comment", "<no MEASURED at line>",
                   "MEASURED at", where=R3_GATE_FILE)
        return
    quoted = tuple(int(g) for g in m.groups())
    live = (declared, pinned, substantive)
    print(f"  [{'OK ' if quoted == live else 'RED'}] gate's MEASURED-at "
          f"comment quotes {quoted}; this tree measures {live}")
    if quoted != live:
        run.failures.append(
            (R3_GATE_FILE, "MEASURED-at comment triple", live,
             f"{declared} DECLARED, {pinned} pinned here, "
             f"**{substantive} substantive**"))
    run.figures.append(("gate's MEASURED-at comment", quoted))


def main(argv) -> int:
    quick = "--quick" in argv
    control = "--control" in argv

    run = fr.FigureRun(title="rc470 FIGURE RUN  (`#T1188`)  [core: figure_run]",
                       instruments=INSTRUMENTS,
                       baseline_commit=R3_BASELINE_COMMIT)
    run.header()

    import demotion_probe as dp
    from srmech._resolve import resolve_dotted_callable
    from srmech.introspect.tool_schema import get_tool_schema

    print("\n-- RULER 1: the R3 declaration reader --")
    tools = list(get_tool_schema().tools)
    fns = [(e.name, resolve_dotted_callable(e.name)) for e in tools]
    run.figure("registry entries", len(fns),
               "| entries / resolved / unresolved | **{v} / {v} / 0** |")
    declared = sorted(n for n, f in fns if dp.declaration_hits(f))
    run.figure("DECLARED, lexical", len(declared),
               "| DECLARED, after the comprehension fold in the delegate walk | **{v}**",
               "**{v} DECLARED lexically,")
    # W1.7 — the gate's OWN pinned literal, read from the gate's prose
    run.figure("DECLARED, pinned in the R3 gate", len(declared),
               "assert len(declared) == {v}", where=R3_GATE_FILE)
    run.figure("reader_signature", dp.reader_signature(),
               "{v}", where="tests/demotion_census.ndjson")

    # the pinned ledger, read from the gate that owns it
    gate = run.prose(R3_GATE_FILE)
    blk = gate[gate.index("_RESIDUAL_TOPIC_MISREADS = {"):gate.index("#: The classes above")]
    pinned = re.findall(r'^    "([\w.]+)":', blk, re.M)
    run.figure("pinned topical misreads", len(pinned),
               "| — of those, **TOPICAL MISREADS** pinned by name | **{v}** |",
               "**39 cannot survive the question**".replace("39", "{v}"),
               "and the {v} of 223 readings that no lexical rule can fix")
    run.figure("pinned topical misreads, pinned in the R3 gate", len(pinned),
               "len(\n        _RESIDUAL_TOPIC_MISREADS) == {v}",
               where=R3_GATE_FILE)
    run.figure("substantive DECLARED", len(declared) - len(pinned),
               "| — **SUBSTANTIVE DECLARED** | **{v}** |",
               "**223 DECLARED lexically, 41 pinned as topical misreads, "
               "{v} substantive**")
    run.figure("substantive DECLARED, pinned in the R3 gate",
               len(declared) - len(pinned),
               "len(declared) - len(_RESIDUAL_TOPIC_MISREADS) == {v}",
               where=R3_GATE_FILE)
    _the_gates_own_baseline_line(run, len(declared), len(pinned),
                                 len(declared) - len(pinned))
    unknown = sorted(set(pinned) - set(declared))
    assert not unknown, f"pinned but not DECLARED: {unknown}"

    riders = [n for n in pinned
              if dp.declaration_hits(resolve_dotted_callable(n))[0].endswith(")")]
    run.figure("pins riding the delegate follow", len(riders),
               "Twenty-six of the {v} pins ride it".replace("{v}", str(len(pinned)))
               if len(riders) == 26 else "RIDERS-MOVED-{v}")

    # the rc469 reader, re-implemented by reading the PINNED baseline's source
    #
    # ⚠️ THE MECHANISM IS HELD CONSTANT ON PURPOSE, and this is a REPAIR, not
    # a convenience. The baseline's `declaration_hits` walks bare
    # `code.co_names`, so re-executing it verbatim inherits the very PEP 709
    # defect rc470's last commit fixed: MEASURED, it reads 202 on CPython
    # 3.10.21 and 3.11.16 and **204** on 3.12.3 and 3.14.7 — so the published
    # "202" was never a property of the tree either, only a 3.10 reading, and
    # this script's own output would have depended on which interpreter ran it.
    # Re-using the baseline's VOCABULARY over the SHIPPED (folded) delegate
    # walk isolates the thing the comparison is actually for — what the rc469
    # WORD LIST read — and yields **204 on all of 3.10 / 3.11 / 3.12 / 3.14**.
    # The delta this feeds ("206 is the READER's move") is a vocabulary delta,
    # and holding the mechanism fixed is what makes it one.
    main_src = run.baseline_source("tools/demotion_probe.py",
                                   expect_sha256=R3_BASELINE_SHA256)
    ns = {"__name__": "demotion_probe_baseline_rc469", "__file__": "<baseline>"}
    exec(compile(main_src, "<rc469:tools/demotion_probe.py>", "exec"), ns)
    _vocab = ns["R3_VOCABULARY"]

    def old_hits(fn):
        """the rc469 baseline's VOCABULARY over rc470's folded delegate walk."""
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
    run.figure("DECLARED, rc469 reader", len(old_declared),
               "| DECLARED, rc469 reader | **{v}** |")
    run.figure("pins already DECLARED under rc469", len(set(pinned) & old_declared),
               "**{v} of the 41 read DECLARED under the rc469 reader too**")
    added = sorted(set(pinned) - old_declared)
    run.figure("pins the widening added", len(added), "The **SIX** the widening added"
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
    reg_occ = sum(len(WIDE.findall(inspect.getdoc(f) or ""))
                  for _, f in fns)
    run.figure("bounding quantifier, 732 registry docstrings", reg_occ,
               "**{v} occurrences, 0 live instances**")
    # ONE walk of the population, both patterns (rc471; rc470 walked it twice)
    swept = run.sweep({"wide": WIDE, "bare": BARE}, exclude=EXCLUDE)
    for tag, needle in (("wide", "**{v} occurrences on 6 LINES in 4 FILES**"),
                        ("bare", "spelling gives **{v}** on that")):
        occ, lines, files = swept[tag]
        run.figure(f"bounding quantifier [{tag}], subtree minus the two "
                   f"self-referential files", occ, needle)
        if tag == "wide":
            run.figure("  … on lines", lines, "occurrences on {v} LINES in")
            run.figure("  … in files", files, "LINES in {v} FILES**")

    print("\n-- the CENSUS --")
    cen = [json.loads(x) for x in
           run.prose("tests/demotion_census.ndjson").splitlines() if x.strip()]
    meta = next(r for r in cen if r.get("record") == "meta")
    run.figure("census n_rows", meta["n_rows"], "`n_rows` {v}")
    run.figure("census n_ops", meta["n_ops"], "`n_ops` {v}")
    run.figure("registry_signature", meta["registry_signature_sha256"]["native"],
               "`{v}` in BOTH cells")
    for cell in ("native", "pure"):
        run.figure(f"undeclared roster [{cell}]", len(meta["undeclared"][cell]),
                   "`EXPECTED_UNDECLARED_N` stays `{{\"native\": {v}, \"pure\": {v}}}`")
    run.figure("census reader_signature agrees with the live reader",
               meta["reader_signature_sha256"]["native"] == dp.reader_signature(),
               "written **per cell**")

    print("\n-- the DEF_BLOB drain (`fe3454677`) --")
    out = fr.git("show", "fe3454677", "--",
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
    run.figure("modules whose def_blob moved", len(mods), "**FIVE modules, not six**"
               if len(mods) == 5 else "DEFBLOB-MODULES-{v}")
    run.figure("rows whose def_blob moved", rows, "= {v} rows;")

    print("\n-- RULER 2: the notebook dead-path marker --")
    nb = run.prose("tests/test_notebook_currency_rc420.py")
    m = re.search(r"_PROSE_DEAD_PATH_CEIL\s*=\s*(\d+)", nb)
    run.figure("_PROSE_DEAD_PATH_CEIL", int(m.group(1)),
               "`_PROSE_DEAD_PATH_CEIL` goes **10 → {v}**")

    if quick:
        print("\n!! --quick: GATE TOTALS AND CAN-FAIL FIGURES NOT MEASURED.")
        print("!! This run is NOT a final figure run.")
    else:
        print("\n-- GATE TOTALS (ONE union pytest, split on junit classname) --")
        # ⚠️ THE QUOTED FIGURE IS `collected` = passed + skipped, NOT `passed`,
        # and rc471 changed it for a measured reason. A row that skips because
        # `libsrmech` is absent PASSES on a host that has one, so the same
        # unchanged gate reports two different "N passed" numbers on two hosts
        # — a figure that is a property of the tree × the cell, quoted as
        # though it were a property of the tree. MEASURED on this branch, with
        # HAS_NATIVE False: set 1 is 148 passed + 18 skipped and set 2 is 189
        # passed + 3 skipped, against the 166 and 192 the rc470 entry quotes
        # from a native-present host. `collected` reproduces BOTH exactly.
        xml = _outside_the_tree("rc470_figures_junit") / "union.xml"
        totals, tally = run.union_pytest(GATE_SETS, xml)
        for rel, row in sorted(tally.items()):
            print(f"      {rel:52} {row['collected']:4d} collected "
                  f"= {row['passed']} passed + {row['skipped']} skipped"
                  + (f"  ({row['failed']} FAILED)" if row["failed"] else "")
                  + (f"  ({row['error']} ERROR)" if row["error"] else ""))
        for i, (got, needle, rc470) in enumerate(
                zip(totals, GATE_NEEDLES, RC470_QUOTED), 1):
            reach = got["collected"] + got["failed"] + got["error"]
            print(f"    gate set {i}: {got['collected']} collected "
                  f"= {got['passed']} passed + {got['skipped']} skipped"
                  + (f", {got['failed']} FAILED" if got["failed"] else "")
                  + f"   [rc470 quoted {rc470} passed on a native host; "
                    f"collected+failed here = {reach}"
                  + ("]" if reach == rc470 else " — DOES NOT ACCOUNT]"))
            run.figure(f"gate set {i}", got["collected"], needle)
            if got["failed"] or got["error"]:
                run.failures.append(
                    ("<pytest>", f"gate set {i} is not green", got,
                     "0 failed, 0 error"))
        if control:
            print("\n-- ORDER-INDEPENDENCE CONTROL: the old per-set shape --")
            per_set = run.per_set_pytest(GATE_SETS)
            union_collected = [t["collected"] for t in totals]
            print(f"    union   {union_collected}")
            print(f"    per-set {per_set}")
            if per_set != union_collected:
                run.failures.append(
                    ("<pytest>", "order independence", union_collected, per_set))
                print("    !! THE UNION AND THE PER-SET SHAPE DISAGREE — a test's "
                      "outcome depends on which siblings ran with it.")
            else:
                print("    the union and the per-set shape agree.")

        print("\n-- CAN-FAIL (mutants on a COPY; the tree is never written) --")
        import canfail_preload as cf
        tmp = _outside_the_tree("rc470_figures_canfail")
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
        clean = f"{tally.get(R3_GATE[0], {}).get('passed', 0)} passed"
        print(f"    r3 gate, clean (recovered from the union XML) -> {clean}")
        run.figure("r3 gate, clean", clean, "clean **{v}**")
        run.figure("r3 gate, negation refusal disabled",
                   run.pytest_line(R3_GATE, mutant=tmp / "neg"),
                   "(`if False:` on the clause-local guard) → **{v}**")
        run.figure("r3 gate, stated-bound stem removed",
                   run.pytest_line(R3_GATE, mutant=tmp / "stem"),
                   "remove the stated-bound stem → **{v}**")

    return run.footer()


def _outside_the_tree(name: str) -> Path:
    """A scratch directory that is NOT inside the package tree.

    Same rule ``canfail_preload.write_mutant`` enforces for mutants: anything
    written under ``PY_ROOT`` is collectable by pytest, importable by a sibling
    process and committable by accident.
    """
    out = Path(os.environ.get("TMPDIR", "/tmp")) / name
    out.mkdir(parents=True, exist_ok=True)
    return out


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
