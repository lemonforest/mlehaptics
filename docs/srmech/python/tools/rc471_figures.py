r"""EVERY FIGURE the rc471 (`#T1188`) W7 prose quotes, re-printed by ONE run.

WHY THIS FILE EXISTS
--------------------
``tools/rc470_figures.py`` exists because "no figure this run did not print"
failed three times inside rc470's own re-validation. rc471 lifted that harness's
reusable core into :mod:`figure_run` so a later rc gets it without copying the
file — and this is the first rc to take delivery. What lives here is rc471's
W7 figures and nothing else; rc470's stay in rc470's file.

⚠️ **IT DRIVES NO PYTEST, AND THAT IS A DESIGN DECISION, NOT AN OMISSION.**
rc470's harness re-ran gate files to recover their totals, which is why it needs
a ``--quick`` mode that its own banner calls *"NOT sufficient for a final run"*.
Every figure below is derived from the TREE — the census manifest, the registry,
the probe's own constants and the git baseline — so there is one mode and it is
the final one. It also means the run is safe to give a read-only ``GIT_DIR``
export, which is the only way git answers inside a worktree whose ``.git`` is a
pointer file holding a Windows path; rc471 measured what an ambient ``GIT_DIR``
does to a process that CAN reach pytest, and the answer was a fixture commit on
the live branch.

WHAT IT CANNOT DO, stated rather than left to be discovered
-----------------------------------------------------------
1. It checks PRESENCE of a rendered literal in the prose, not that the literal
   sits in the sentence a reader would attach it to.
2. The two WALL CLOCKS this rc quotes — 49.9 s native, 190.0 s pure — are NOT
   here, and cannot be: a wall clock is a property of the host and the hour,
   not of the tree, and re-running the census to re-print them would take
   longer than the rc. They are quoted with their host, as a pair, and the
   entry says they are not constants. Everything else the entry quotes is
   below.
3. It re-derives the regeneration diff from the baseline BLOB, so it proves the
   census on disk stands in the stated relation to ``R471_BASELINE_COMMIT``. It
   cannot prove that blob was the right baseline; the sha256 pin is what does
   that.

numpy-free. No ``abs()``. Every digest routes through
``srmech.amsc.format.sha256_bytes``.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PY_ROOT))
sys.path.insert(0, str(PY_ROOT / "tools"))

import figure_run as fr             # noqa: E402  (path set above)
import census_regen_diff as crd     # noqa: E402
import demotion_probe as dp         # noqa: E402

#: THE IMMUTABLE BASELINE for W7: the last commit BEFORE the regeneration, i.e.
#: the census as rc470 left it. A raw SHA, never a branch and never a tag,
#: following ``rc470_figures.R3_BASELINE_COMMIT``'s precedent and for the same
#: reason — rc470's harness read ``main:…`` and died the day rc470 merged.
R471_BASELINE_COMMIT = "bf117f391"

#: sha256 of ``R471_BASELINE_COMMIT:docs/srmech/python/tests/demotion_census.ndjson``
#: (247078 bytes, 706 lines, LF). Without it a SHA that RESOLVES but names the
#: wrong tree fails later as a confusing zero-diff instead of here, loudly.
R471_BASELINE_CENSUS_SHA256 = (
    "c4092cbd3d16d7259f70662f765367d39705908ff496fb9ee88b11289b5ef795")

#: Everything whose bytes decide a figure below, hashed BEFORE and AFTER.
INSTRUMENTS = (
    "tests/demotion_census.ndjson",
    "tools/demotion_probe.py",
    "tools/census_regen_diff.py",
    "tools/figure_run.py",
    "tools/rc471_figures.py",
    "tests/test_silent_carrier_demotion_rc463.py",
    "tests/test_census_regen_diff_rc471.py",
    "CHANGELOG.md",
)

#: The scalar-parameter type spellings the rc472 lane would enumerate. Written
#: out rather than pattern-matched, because "does this string mean a float?" is
#: exactly the judgment rc470 measured going wrong when it was left to a regex.
SCALAR_FLOAT_TYPES = ("float", "float | None", "Optional[float]")

#: The homonym pattern. ``class (c)`` and ``class-(c)`` are the same term and a
#: reader conflating them is the hazard; the STRICT spelling alone under-counts
#: (5 files against 9 on this tree). Written as a compiled pattern in this file
#: rather than passed through a shell, per the rule this arc's own classifier
#: defects established: backtick stripping by the WSL/Windows shell layers
#: produced two false negatives in this rc's research phase and a Unicode-minus
#: blind spot produced a third.
CLASS_C_RX = re.compile(r"class[- ]\(c\)", re.I)

#: The word whose ABSENCE from the tree is the first leg of the equiseparation
#: refusal. Lower-cased before matching.
EQUISEP_NEEDLE = "equisep"

#: ⚠️ SELF-REFERENTIAL POPULATION. Both sweeps below count occurrences of a
#: word in ``docs/srmech``, and this file and the CHANGELOG entry it checks are
#: ABOUT that word — so including them measures the measurement. They are
#: excluded BY NAME and the exclusion is printed with the figure, the same
#: shape ``rc470_figures`` uses for its negation sweep.
SWEEP_EXCLUDE = (
    "docs/srmech/python/tools/rc471_figures.py",
    "docs/srmech/python/CHANGELOG.md",
)


def _text_files(root: Path):
    """Every file under ``root`` that is TEXT, in one walk.

    NUL-byte test, which is what ``grep`` uses: the subtree holds a PDF, and a
    binary read with ``errors="replace"`` can manufacture a match out of
    mojibake — measured, it added one phantom file to the homonym count.
    """
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(fr.REPO).as_posix()
        if rel in SWEEP_EXCLUDE:
            continue
        try:
            data = p.read_bytes()
        except OSError:                                   # pragma: no cover
            continue
        if b"\0" in data:
            continue
        yield rel, data.decode("utf-8", "replace")


def _render_by_verdict(d) -> str:
    return " / ".join(f"{k} {d[k]}" for k in sorted(d))


def main(argv) -> int:
    run = fr.FigureRun(title="rc471 W7 FIGURE RUN  (`#T1188`)  [core: figure_run]",
                       instruments=INSTRUMENTS,
                       baseline_commit=R471_BASELINE_COMMIT)
    run.header()

    census_text = Path(PY_ROOT, "tests/demotion_census.ndjson").read_text(
        encoding="utf-8")
    meta, rows = crd.load(census_text)
    base_text = run.baseline_source("tests/demotion_census.ndjson",
                                    R471_BASELINE_CENSUS_SHA256)
    bmeta, brows = crd.load(base_text)

    # ── the regeneration ────────────────────────────────────────────────────
    print("\n-- W7: THE REGENERATION --")
    run.figure("census n_rows", meta["n_rows"], "`n_rows` **{v}**")
    run.figure("census n_ops", meta["n_ops"], "`n_ops` **{v}**")
    run.figure("cells measured", json.dumps(meta["cells_measured"]),
               "`cells_measured` `{v}`")
    for cel in ("native", "pure"):
        run.figure(f"by_verdict [{cel}]",
                   _render_by_verdict(meta["by_verdict"][cel]),
                   "{v}")
        run.figure(f"probe_signature [{cel}]",
                   meta["probe_signature_sha256"][cel], "`{v}`")
        run.figure(f"measured_at.srmech_version [{cel}]",
                   meta["measured_at"][cel]["srmech_version"], "`{v}`")
        run.figure(f"measured_at.python [{cel}]",
                   meta["measured_at"][cel]["python"], "python `{v}`")
    run.figure("probe_signature agrees with the live probe",
               meta["probe_signature_sha256"]["native"] == dp.probe_signature()
               and meta["probe_signature_sha256"]["pure"] == dp.probe_signature(),
               "both cells carry the live probe signature: **{v}**")
    run.figure("registry_signature", meta["registry_signature_sha256"]["native"],
               "`{v}`")
    run.figure("reader_signature", meta["reader_signature_sha256"]["native"],
               "`{v}`")

    # ── the invariant, re-derived from the pinned baseline ──────────────────
    print("\n-- W7.2: THE INVARIANT, re-derived from the pinned baseline --")
    B = {crd.key(r): r for r in brows}
    A = {crd.key(r): r for r in rows}
    moved_meta = sorted(k for k in set(bmeta) | set(meta)
                        if bmeta.get(k, "\0") != meta.get(k, "\0"))
    run.figure("meta keys that moved", ", ".join(moved_meta),
               "exactly two meta keys moved — `{v}`")
    run.figure("meta keys byte-identical",
               len([k for k in bmeta if k not in moved_meta]),
               "the other **{v}** are byte-identical")
    differing = [k for k in sorted(set(A) & set(B))
                 if json.dumps(A[k], sort_keys=True)
                 != json.dumps(B[k], sort_keys=True)]
    run.figure("data lines differing at all", len(differing),
               "data lines differing AT ALL: **{v} of 705**")
    run.figure("rows added", len(set(A) - set(B)), "**{v}** rows added")
    run.figure("rows removed", len(set(B) - set(A)), "**{v}** removed")
    cells_seen = sum(1 for k in set(A) & set(B) for c in ("native", "pure")
                     if (A[k].get(c) or {}).get("verdict") is not None
                     or (B[k].get(c) or {}).get("verdict") is not None)
    changed = [k for k in sorted(set(A) & set(B)) for c in ("native", "pure")
               if (A[k].get(c) or {}).get("verdict")
               != (B[k].get(c) or {}).get("verdict")]
    run.figure("verdict cells compared", cells_seen,
               "**{v}** verdict cells compared")
    run.figure("verdict changes", len(changed), "VERDICT CHANGES **{v}**")
    run.figure("by_verdict byte-identical to the baseline's",
               json.dumps(meta["by_verdict"], sort_keys=True)
               == json.dumps(bmeta["by_verdict"], sort_keys=True),
               "byte-identical to the baseline's: **{v}**")

    # ── why (ii) is 0 and not 37 ────────────────────────────────────────────
    print("\n-- W7.2: WHY clause (ii) reads 0 rather than rc470's 37 --")
    demoted = [r for r in rows
               if (r.get("native") or {}).get("verdict") == "DEMOTED"
               or (r.get("pure") or {}).get("verdict") == "DEMOTED"]
    with_decl = [r for r in rows if "declares" in (r.get("native") or {})
                 or "declares" in (r.get("pure") or {})]
    decl_cells = sum(1 for r in rows for c in ("native", "pure")
                     if "declares" in (r.get(c) or {}))
    run.figure("rows DEMOTED in either cell", len(demoted), "**{v}** DEMOTED rows")
    run.figure("rows carrying a `declares` key", len(with_decl),
               "the same **{v}** rows carry a `declares` key")
    run.figure("`declares` cell-columns", decl_cells,
               "**{v}** `declares` cell-columns")
    run.figure("DEMOTED rows in srmech.math.rational",
               len([r for r in with_decl
                    if r["op"].startswith("srmech.math.rational.")]),
               "**{v}** of them belong to `srmech.math.rational`")

    # ── the seam with rc472 ─────────────────────────────────────────────────
    print("\n-- THE SEAM: rc471 holds the population, rc472 adds a lane --")
    from srmech.introspect.tool_schema import get_tool_schema
    entries = list(get_tool_schema().tools)
    run.figure("registry entries", len(entries), "Registry total **{v}**")
    seq = {(e.name, p.name) for e in entries for p in (e.parameters or ())
           if dp.sequence_shaped(p.type or "")}
    run.figure("sequence-shaped (op, param) pairs", len(seq),
               "**{v}** sequence-shaped `(op, param)` pairs")
    run.figure("… over distinct ops", len({o for o, _ in seq}),
               "over **{v}** distinct ops")
    run.figure("census keys == sequence-shaped pairs",
               {(r["op"], r["param"]) for r in rows} == seq,
               "an IDENTITY, measured: **{v}**")
    scalar = {(e.name, p.name) for e in entries for p in (e.parameters or ())
              if (p.type or "").strip() in SCALAR_FLOAT_TYPES}
    run.figure("scalar-float (op, param) pairs", len(scalar),
               "**{v}** scalar-float `(op, param)` pairs")
    run.figure("… over distinct ops", len({o for o, _ in scalar}),
               "over **{v}** ops")
    census_ops = {r["op"] for r in rows}
    run.figure("… of those ops, already in the census",
               len({o for o, _ in scalar} & census_ops),
               "**{v}** of those ops ALREADY carry a census row")
    rat = sorted({o for o, _ in scalar
                  if o.startswith("srmech.math.rational.")})
    run.figure("rational scalar-float ops", len(rat),
               "is **{v}**, not nine")
    run.figure("… absent from the census",
               len([o for o in rat if o not in census_ops]),
               "all **{v}** absent from the census")
    by_name = {e.name: e for e in entries}
    run.figure("… distinct return carriers over that set",
               ", ".join(sorted({by_name[o].returns.type for o in rat})),
               "return carriers `{v}`")
    run.figure("NO_SHAPE rows [native]",
               sum(1 for r in rows
                   if (r.get("native") or {}).get("verdict") == "NO_SHAPE"),
               "NO_SHAPE at **{v}** in both cells")
    gate = Path(PY_ROOT, "tests/test_silent_carrier_demotion_rc463.py").read_text(
        encoding="utf-8")
    m = re.search(r"^CEIL_DEMOTION_UNREACHED\s*[:=]\s*(.+)$", gate, re.M)
    run.figure("CEIL_DEMOTION_UNREACHED source", (m.group(1) if m else ""),
               "`CEIL_DEMOTION_UNREACHED = {v}`")

    # ── the equiseparation refusal ──────────────────────────────────────────
    print("\n-- THE EQUISEPARATION WITNESS, REFUSED --")
    run.figure("commits touching the string `equisep`, all refs",
               len([ln for ln in fr.git("log", "-S", EQUISEP_NEEDLE, "--all",
                                        "--oneline").splitlines() if ln.strip()]),
               "**{v}** commits")
    print("  ONE walk, both sweeps. population EXCLUDES (self-referential):")
    for rel in SWEEP_EXCLUDE:
        print(f"    {rel}")
    eq_hits, cc_hits = [], []
    for rel, text in _text_files(Path(fr.REPO, "docs/srmech")):
        if EQUISEP_NEEDLE in text.lower():
            eq_hits.append(rel)
        if CLASS_C_RX.search(text):
            cc_hits.append(rel)
    run.figure("files under docs/srmech holding `equisep`", len(eq_hits),
               "**{v}** files")
    probe_src = Path(PY_ROOT, "tools/demotion_probe.py").read_text(
        encoding="utf-8").split("\n")
    live_h = next(i + 1 for i, s in enumerate(probe_src)
                  if s.startswith("H = 3 * 2 ** 53"))
    run.figure("`H` assignment, live line", live_h,
               "`tools/demotion_probe.py:{v}`")
    base_probe = fr.git("show",
                        "4475997fd:docs/srmech/python/tools/demotion_probe.py"
                        ).split("\n")
    run.figure("`H` assignment, line on the merge base", next(
        i + 1 for i, s in enumerate(base_probe) if s.startswith("H = 3 * 2 ** 53")),
        "line **{v}** on the merge base")
    run.figure("UNRESOLVED_AT_WITNESS rows [native]",
               meta["by_verdict"]["native"]["UNRESOLVED_AT_WITNESS"],
               "holds **{v}** row in each cell")

    # The witness triples, and the verdict string equiseparation cannot reach.
    P, F, G = dp.P, dp.F, dp.G
    X = next(c for c in range(F, F + 4096)
             if float(c - 1) == float(c) == float(c + 1))
    run.figure("shipped separations (P-F, G-F)", f"{P - F}, {G - F}",
               "separations are **{v}**")
    run.figure("smallest symmetric equiseparated triple, offset from 2**53",
               X - F, "at `2**53 + {v}`")

    def exact_route(x):
        return x * 3

    def demoting_route(x):
        return float(x) * 3.0

    verdicts = {}
    for tname, triple in (("shipped", (P, F, G)),
                          ("equiseparated", (X - 1, X, X + 1))):
        for rname, fn in (("exact", exact_route),
                          ("demoting", demoting_route)):
            verdicts[(tname, rname)] = dp._verdict(
                *[dp.canon(fn(w)) for w in triple])
    run.figure("shipped triple / exact route", verdicts[("shipped", "exact")],
               "the exact route **{v}**")
    run.figure("shipped triple / demoting route",
               verdicts[("shipped", "demoting")],
               "the demoting route **{v}**")
    run.figure("equiseparated triple / exact route",
               verdicts[("equiseparated", "exact")],
               "still reads **{v}** on the exact route")
    run.figure("equiseparated triple / demoting route",
               verdicts[("equiseparated", "demoting")],
               "reads **{v}** on the demoting one")
    run.figure("DEMOTED reachable under the equiseparated triple",
               verdicts[("equiseparated", "demoting")] == "DEMOTED",
               "reachable at all: **{v}**")

    # The homonym, from the SAME walk, with a pattern written in this file.
    for rel in cc_hits:
        print(f"    class[- ](c): {rel}")
    run.figure("files under docs/srmech matching `class[- ](c)`", len(cc_hits),
               "**{v}** files under `docs/srmech/`")
    run.figure("… of those, rc433-named",
               len([r for r in cc_hits if "rc433" in r.rsplit("/", 1)[-1]]),
               "**{v}** of them named for RC433")

    return run.footer()


if __name__ == "__main__":                                # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
