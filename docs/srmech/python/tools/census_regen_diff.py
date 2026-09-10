r"""THE CENSUS REGENERATION INVARIANT, asserted by a script rather than an eye.

WHY THIS FILE EXISTS
--------------------
An rc that changes the INSTRUMENT and not the POPULATION owes one claim:
*nothing the instrument decides moved.* rc470 made that claim ("37 of 705 data
lines, 74 cell-columns, 29 ops, differing ONLY in ``declares``; verdict changes
== 0") and checked it with a scratch script that was never committed, so the
next rc making the same claim had nothing to run. This is that script, shipped,
because a load-bearing count owes its generating code.

It compares the COMMITTED ``tests/demotion_census.ndjson`` against the
regenerated one and prints five clauses, each with its own PASS / FAIL:

  (i)   the meta line differs ONLY in keys named as expected on the command
        line (``--meta-may-move``), nothing else;
  (ii)  every DATA line that differs at all differs ONLY in ``declares`` — the
        one field a reader change is allowed to move — and no row is added or
        removed;
  (iii) VERDICT CHANGES == 0, counted over every row x every cell;
  (iv)  ``meta.by_verdict`` is byte-identical to the expected table;
  (v)   ``n_rows`` / ``n_ops`` / ``cells_measured`` are the expected ones.

⚠️ **IT RUNS NO GIT, AND THAT IS DELIBERATE.** The baseline is passed in as a
FILE. WSL git cannot open a worktree whose ``.git`` is a pointer file holding a
Windows path, and the obvious workaround — exporting ``GIT_DIR`` /
``GIT_WORK_TREE`` — points every git FIXTURE in the suite at the real
repository; rc471 measured that the hard way (see its CHANGELOG entry). Extract
the baseline with whichever git can read the tree::

    git show <ref>:docs/srmech/python/tests/demotion_census.ndjson > /tmp/base.ndjson
    python3 tools/census_regen_diff.py /tmp/base.ndjson tests/demotion_census.ndjson

RECORDED RESULT — rc471 (`#T1188`), the regeneration this file was written for:
**INVARIANT HELD 5/5**, and clause (ii) came out at **0 of 705 data lines
differing at all** rather than at rc470's 37, because ``declares`` is written
onto DEMOTED rows ONLY and none of the 69 DEMOTED rows belongs to
``srmech.math.rational``, the module that rc's prose work edited. The whole
two-cell regeneration is **one changed line**, the meta.

rc472 (`#T1188`) added two ALLOWANCES, each pinned before its regeneration
ran and each red-proven in every direction by the test file:

* ``--expect-added N --added-lane LANE`` — a new census LANE adds exactly N
  rows, every one in the named lane, and moves none (C2, the scalar lane).
* ``--expect-moved N --moved-from VERDICT`` — a REPAIR to the instrument's
  reach moves exactly N verdict cells PER CELL, every one OUT of the named
  verdict and none INTO it, the SAME rows in every cell; the cell-columns
  that moved are the only data allowed to differ outside ``declares`` (C3,
  the required-scalar fill: rows that raised at a synthesised sibling now
  bind and are asked). The direction is the half an accident cannot satisfy.
* ``--may-relabel KEY[,KEY…]`` — rows named IN ADVANCE may differ outside
  ``declares`` in ``shape`` ONLY; every named row must actually relabel (a
  name with no change is slack, and red), and an unnamed row that relabels
  is still red. Minted for the C3 labeller repair, where the label of a
  decided candidate had been recovered by object identity and CPython's
  small-int interning made the scalar slot read "harvested".

RECORDED RESULT — rc472 C3 (`#T1188`): the FIRST regeneration under the
fill repair came back **BROKEN on clause (ii) alone** — 13 rows moved per
cell exactly as pinned, and two rows whose verdict did not move relabelled
``synth[1] -> harvested`` (``feynman_photon_propagator::k_squared``,
``higgs_potential::phi``): the labeller's identity test, fooled by the fill
value being the same interned ``1`` as the slot. The labeller was repaired
to record each candidate's label beside it, the rows the repair would touch
were named BEFORE the second run, and the second run is the one committed.

numpy-free. No ``abs()``. No ``hashlib``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

#: The one field a differing DATA line is allowed to differ in. It is the R3
#: reader's output, and rc470 established that a reader change cannot move a
#: verdict — the verdict is read off VALUES the op returns, the label off its
#: DOCSTRING. Widening this set is a claim about the instrument, not a
#: convenience: anything else moving means the measurement moved.
DATA_MAY_MOVE = ("declares",)


def load(text: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """``(meta, rows)`` from one manifest's text."""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        raise SystemExit("empty manifest")
    return json.loads(lines[0]), [json.loads(ln) for ln in lines[1:]]


def key(r: Dict[str, Any]) -> str:
    return f"{r['op']}::{r['param']}"


def paths(d: Dict[str, Any], prefix: Tuple[str, ...] = ()
          ) -> Dict[Tuple[str, ...], Any]:
    """Flatten one row into ``{tuple-path: leaf value}``.

    A flatten rather than a top-level compare, because the cell columns are
    nested dicts and a top-level ``!=`` cannot say WHICH field moved — which is
    the whole question clause (ii) asks.
    """
    out: Dict[Tuple[str, ...], Any] = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out.update(paths(v, prefix + (k,)))
        else:
            out[prefix + (k,)] = v
    return out


_ABSENT = "\0ABSENT\0"


def _lane_of(ty: str) -> str:
    """The census lane of a registry type, read from the SHARED instrument."""
    import sys
    tools = str(Path(__file__).resolve().parent)
    if tools not in sys.path:
        sys.path.insert(0, tools)
    import demotion_probe as dp  # noqa: E402
    return dp.lane_of(ty)


def compare(before_txt: str, after_txt: str, *,
            meta_may_move: Tuple[str, ...],
            by_verdict: Dict[str, Dict[str, int]] | None,
            n_rows: int | None, n_ops: int | None,
            cells: Tuple[str, ...],
            expect_added: int = 0, added_lane: str = "",
            expect_moved: int = 0, moved_from: str = "",
            may_relabel: Tuple[str, ...] = ()) -> int:
    """``expect_added`` / ``added_lane`` (rc472, `#T1188`): an rc that adds a
    LANE to the census adds rows without moving any. Clause (ii) then holds
    iff EXACTLY ``expect_added`` rows were added, EVERY one of them is in
    ``added_lane`` (read from the row's registry type through the shared
    :func:`demotion_probe.lane_of`), and still no row was removed. The
    default ``0`` is the rc471 behaviour byte for byte: any addition breaks
    clause (ii). Clause (iii) is unchanged — verdicts are compared over the
    keys BOTH manifests carry, so the added rows cannot hide a move and a
    move cannot hide among the added rows.

    ``expect_moved`` / ``moved_from`` (rc472 C3, `#T1188`): a repair to the
    instrument's REACH moves verdicts. Clause (iii) then holds iff EVERY cell
    carries EXACTLY ``expect_moved`` changed verdict cells, every one of them
    from ``moved_from`` to something else (none INTO it), and the changed
    KEY SET is identical across cells. Clause (ii) exempts exactly the
    cell-columns whose verdict moved under that allowance — never a whole
    row, never a row that did not move — and still refuses additions and
    removals. The default ``0`` is the rc471 behaviour byte for byte.

    ``may_relabel`` (rc472 C3, `#T1188`): row keys named in advance whose
    ``shape`` label — and nothing else — may differ. Every named key must
    actually differ in ``shape`` (no slack), and a ``shape`` move on any
    other row is an offender exactly as before.
    """
    mb, rb = load(before_txt)
    ma, ra = load(after_txt)
    B = {key(r): r for r in rb}
    A = {key(r): r for r in ra}
    ok = True

    # Verdict moves are computed FIRST, because the rc472-C3 allowance lets
    # clause (ii) exempt exactly the cell-columns whose verdict moved under it.
    changes: List[Tuple[str, str, Any, Any]] = []
    seen = 0
    for k in sorted(set(A) & set(B)):
        for cel in cells:
            vb = (B[k].get(cel) or {}).get("verdict")
            va = (A[k].get(cel) or {}).get("verdict")
            if vb is not None or va is not None:
                seen += 1
            if vb != va:
                changes.append((k, cel, vb, va))
    allowed_moves = {(k, cel) for k, cel, vb, va in changes
                     if expect_moved and moved_from
                     and vb == moved_from and va != moved_from}

    # ---- (i) the meta line -------------------------------------------------
    movers = sorted(k for k in set(mb) | set(ma)
                    if mb.get(k, _ABSENT) != ma.get(k, _ABSENT))
    c1 = set(movers) <= set(meta_may_move)
    ok &= c1
    print(f"(i)   meta keys that MOVED: {movers}")
    print(f"      allowed to move:      {sorted(meta_may_move)}")
    for k in movers:
        print(f"        - {k}")
        print(f"            before {json.dumps(mb.get(k), sort_keys=True)}")
        print(f"            after  {json.dumps(ma.get(k), sort_keys=True)}")
    print(f"      meta keys BYTE-IDENTICAL: "
          f"{sorted(k for k in mb if k not in movers)}")
    print(f"      CLAUSE (i): {'PASS' if c1 else 'FAIL'}\n")

    # ---- (ii) every differing data line ------------------------------------
    added, removed = sorted(set(A) - set(B)), sorted(set(B) - set(A))
    relabel_seen: Dict[str, List[Tuple[Tuple[str, ...], Any, Any]]] = {}
    differing: List[str] = []
    bad: List[Tuple[str, List[Tuple[Tuple[str, ...], Any, Any]]]] = []
    moved_ok = 0
    for k in sorted(set(A) & set(B)):
        pa, pb = paths(A[k]), paths(B[k])
        diff = sorted(p for p in set(pa) | set(pb)
                      if pa.get(p, _ABSENT) != pb.get(p, _ABSENT))
        if not diff:
            continue
        differing.append(k)
        offenders = [p for p in diff if p[-1] not in DATA_MAY_MOVE
                     and not (len(p) > 1 and (k, p[0]) in allowed_moves)
                     and not (k in may_relabel and p[-1] == "shape")]
        if k in may_relabel:
            relabelled = [p for p in diff if p[-1] == "shape"]
            if relabelled:
                relabel_seen[k] = [(p, pb.get(p), pa.get(p)) for p in relabelled]
        moved_ok += len(diff) - len(offenders)
        if offenders:
            bad.append((k, [(p, pb.get(p), pa.get(p)) for p in offenders]))
    lane_bad: List[Tuple[str, str]] = []
    if added and added_lane:
        for k in added:
            try:
                lane = _lane_of(A[k].get("type") or "")
            except ValueError as exc:
                lane = f"<{exc}>"
            if lane != added_lane:
                lane_bad.append((k, lane))
    relabel_missing = [k for k in may_relabel if k not in relabel_seen]
    c2 = (not bad and not removed and len(added) == expect_added
          and (not added or bool(added_lane)) and not lane_bad
          and not relabel_missing)
    ok &= c2
    print(f"(ii)  rows added {len(added)} (expected {expect_added}"
          f"{', lane ' + added_lane if added_lane else ''})  "
          f"removed {len(removed)}")
    print(f"      data lines differing at all: {len(differing)} of "
          f"{len(set(A) & set(B))} shared")
    print(f"      of those, differing ONLY in {list(DATA_MAY_MOVE)}: "
          f"{len(differing) - len(bad)}")
    print(f"      cell-columns moved inside {list(DATA_MAY_MOVE)}: {moved_ok}")
    for k, offs in bad:
        print(f"      !! {k} differs OUTSIDE {list(DATA_MAY_MOVE)}:")
        for p, b, a in offs:
            print(f"           {'.'.join(p)}: {b!r} -> {a!r}")
    if may_relabel:
        print(f"      rows allowed to RELABEL (shape only): {len(may_relabel)} "
              f"named, {len(relabel_seen)} relabelled")
        for k in sorted(relabel_seen):
            for p, b, a in relabel_seen[k]:
                print(f"         {k} {'.'.join(p)}: {b!r} -> {a!r}")
        for k in relabel_missing:
            print(f"      !! {k} was named in --may-relabel but did not "
                  f"relabel (slack)")
    if added:
        # the added population, by cell and verdict, so the addition is a
        # printed figure rather than a bare count
        for cel in cells:
            hist: Dict[str, int] = {}
            for k in added:
                v = (A[k].get(cel) or {}).get("verdict")
                if v is not None:
                    hist[v] = hist.get(v, 0) + 1
            print(f"      added rows [{cel}] by_verdict "
                  f"{json.dumps(dict(sorted(hist.items())), sort_keys=True)}")
        print(f"      added rows over {len({A[k]['op'] for k in added})} ops")
        if len(added) != expect_added or not added_lane:
            for k in added:
                print(f"      !! ADDED {k}")
    for k, lane in lane_bad:
        print(f"      !! ADDED {k} is in lane {lane!r}, not {added_lane!r}")
    for k in removed:
        print(f"      !! REMOVED {k}")
    print(f"      CLAUSE (ii): {'PASS' if c2 else 'FAIL'}\n")

    # ---- (iii) verdicts ----------------------------------------------------
    per_cell = {cel: sorted(k for k, c, _vb, _va in changes if c == cel)
                for cel in cells}
    wrong_dir = [(k, cel, vb, va) for k, cel, vb, va in changes
                 if not (vb == moved_from and va != moved_from)]
    same_set = all(per_cell[cel] == per_cell[cells[0]] for cel in cells)
    if expect_moved:
        c3 = (bool(moved_from) and not wrong_dir and same_set
              and all(len(per_cell[cel]) == expect_moved for cel in cells))
    else:
        c3 = not changes
    ok &= c3
    print(f"(iii) verdict cells compared: {seen} over "
          f"{len(set(A) & set(B))} rows x {len(cells)} cells")
    print(f"      VERDICT CHANGES: {len(changes)}"
          + (f" (expected {expect_moved} per cell, every one OUT of "
             f"{moved_from!r} and none INTO it)" if expect_moved else ""))
    for k, cel, vb, va in changes:
        fine = expect_moved and (k, cel) in allowed_moves
        print(f"      {'  ' if fine else '!!'} {k} [{cel}] {vb} -> {va}")
    if expect_moved:
        for cel in cells:
            print(f"      moved [{cel}]: {len(per_cell[cel])}")
        if not moved_from:
            print("      !! --expect-moved given with no --moved-from: an "
                  "allowance must name the verdict it is for")
        if not same_set:
            print("      !! the moved key sets DIFFER across cells:")
            base_set = set(per_cell[cells[0]])
            for cel in cells[1:]:
                for k in sorted(set(per_cell[cel]) ^ base_set):
                    print(f"           {k}: moved in "
                          f"{[c for c in cells if k in per_cell[c]]}")
        for k, cel, vb, va in wrong_dir:
            print(f"      !! {k} [{cel}] {vb} -> {va} is not a move OUT of "
                  f"{moved_from!r}")
        hist: Dict[str, int] = {}
        for k, cel, vb, va in changes:
            hist[f"{vb}->{va}"] = hist.get(f"{vb}->{va}", 0) + 1
        print(f"      transitions: {json.dumps(dict(sorted(hist.items())))}")
    print(f"      CLAUSE (iii): {'PASS' if c3 else 'FAIL'}\n")

    # ---- (iv) by_verdict ---------------------------------------------------
    got = ma.get("by_verdict")
    if by_verdict is None:
        c4 = json.dumps(got, sort_keys=True) == json.dumps(
            mb.get("by_verdict"), sort_keys=True)
        print("(iv)  meta.by_verdict compared against the BASELINE's "
              "(no --by-verdict given)")
    else:
        c4 = json.dumps(got, sort_keys=True) == json.dumps(
            by_verdict, sort_keys=True)
        print("(iv)  meta.by_verdict compared against the EXPECTED table")
    ok &= c4
    for cel in cells:
        print(f"        {cel} got      "
              f"{json.dumps((got or {}).get(cel), sort_keys=True)}")
        want = (by_verdict or mb.get('by_verdict') or {}).get(cel)
        print(f"        {cel} expected {json.dumps(want, sort_keys=True)}")
    print(f"      CLAUSE (iv): {'PASS' if c4 else 'FAIL'}\n")

    # ---- (v) shape ---------------------------------------------------------
    c5 = (ma.get("cells_measured") == list(cells)
          and (n_rows is None or (ma.get("n_rows") == n_rows
                                  and len(ra) == n_rows))
          and (n_ops is None or ma.get("n_ops") == n_ops))
    ok &= c5
    print(f"(v)   n_rows {ma.get('n_rows')} (data lines on disk {len(ra)}), "
          f"n_ops {ma.get('n_ops')}, cells_measured {ma.get('cells_measured')}")
    print(f"      expected n_rows {n_rows}, n_ops {n_ops}, "
          f"cells {list(cells)}")
    print(f"      CLAUSE (v): {'PASS' if c5 else 'FAIL'}\n")

    print(f"INVARIANT: {'HELD (5/5)' if ok else 'BROKEN'}")
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("baseline", type=Path,
                    help="the COMMITTED manifest, extracted to a file")
    ap.add_argument("regenerated", type=Path,
                    help="the manifest this run produced")
    ap.add_argument("--meta-may-move", default="measured_at",
                    help="comma-separated meta keys allowed to differ")
    ap.add_argument("--by-verdict", default="",
                    help="JSON {cell: {verdict: n}} the regenerated meta must "
                         "match byte-for-byte; default is the baseline's own")
    ap.add_argument("--n-rows", type=int, default=None)
    ap.add_argument("--n-ops", type=int, default=None)
    ap.add_argument("--cells", default="native,pure")
    ap.add_argument("--expect-added", type=int, default=0,
                    help="rows the regenerated manifest may ADD — exactly this "
                         "many, every one in --added-lane (rc472: a new census "
                         "lane adds rows without moving any); default 0")
    ap.add_argument("--added-lane", default="",
                    help="the census lane every added row must belong to "
                         "('sequence' or 'scalar', read from the row's registry "
                         "type through demotion_probe.lane_of)")
    ap.add_argument("--expect-moved", type=int, default=0,
                    help="verdict cells the regenerated manifest may MOVE — "
                         "exactly this many PER CELL, every one OUT of "
                         "--moved-from and none INTO it, the same rows in "
                         "every cell (rc472 C3: a reach repair); default 0")
    ap.add_argument("--moved-from", default="",
                    help="the verdict every allowed move must leave (e.g. "
                         "'RAISED')")
    ap.add_argument("--may-relabel", default="",
                    help="comma-separated row keys (op::param) whose `shape` "
                         "label — and nothing else — may differ; every one "
                         "must actually relabel")
    a = ap.parse_args(argv)
    return compare(
        a.baseline.read_text(encoding="utf-8"),
        a.regenerated.read_text(encoding="utf-8"),
        meta_may_move=tuple(s for s in a.meta_may_move.split(",") if s),
        by_verdict=json.loads(a.by_verdict) if a.by_verdict else None,
        n_rows=a.n_rows, n_ops=a.n_ops,
        cells=tuple(s for s in a.cells.split(",") if s),
        expect_added=a.expect_added, added_lane=a.added_lane,
        expect_moved=a.expect_moved, moved_from=a.moved_from,
        may_relabel=tuple(s for s in a.may_relabel.split(",") if s))


if __name__ == "__main__":                                # pragma: no cover
    raise SystemExit(main())
