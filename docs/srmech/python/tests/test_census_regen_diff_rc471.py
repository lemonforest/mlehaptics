r"""rc471 (`#T1188`) — THE REGENERATION INVARIANT'S OWN CAN-FAIL.

``tools/census_regen_diff.py`` is the instrument that decides whether a census
regeneration moved anything the instrument decides. rc470 made the same claim
("verdict changes == 0") with a scratch script that was never committed, so the
claim had generating code exactly once and then did not.

An instrument that cannot return otherwise is not a measurement, so this file
does not merely run the tool on the shipped pair and read PASS. It builds a
minimal two-row manifest, mutates ONE thing at a time, and asserts the tool
reports each mutation on the right clause — with a positive control (the
unmutated pair) that must come back HELD.

The five clauses, and the mutation that must break each:

  (i)   an unexpected META key moves                    -> ``registry_signature_sha256``
  (ii)  a DATA line differs outside ``declares``        -> a ``reason`` string
        …and a row is added / removed                   -> drop a row
  (iii) a VERDICT moves                                 -> EXACT -> DEMOTED
  (iv)  ``by_verdict`` disagrees with the expected      -> one count off by one
  (v)   the shape is not the expected one               -> wrong ``n_ops``

⚠️ Clause (ii) and clause (iii) are NOT the same assertion wearing two names: a
``declares`` move satisfies (ii)'s allowance and leaves (iii) untouched, and
that combination is asserted here as its own case. Without it, "differs only in
``declares``" and "no verdict moved" could both be carried by one comparison
and a regression in either would look like a regression in the other.

numpy-free. No ``abs()``.
"""

import json
import sys
from pathlib import Path

import pytest

_TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import census_regen_diff as crd     # noqa: E402  (tools/ path set above)

CENSUS = Path(__file__).resolve().parents[1] / "tests" / "demotion_census.ndjson"

_META = {
    "record": "meta",
    "cells_measured": ["native", "pure"],
    "registry_signature_sha256": {"native": "aa" * 32, "pure": "aa" * 32},
    "reader_signature_sha256": {"native": "bb" * 32, "pure": "bb" * 32},
    "probe_signature_sha256": {"native": "cc" * 32, "pure": "cc" * 32},
    "measured_at": {"native": {"python": "3.12", "srmech_version": "0.0.0"},
                    "pure": {"python": "3.12", "srmech_version": "0.0.0"}},
    "n_rows": 2,
    "n_ops": 2,
    "by_verdict": {"native": {"EXACT": 1, "DEMOTED": 1},
                   "pure": {"EXACT": 1, "DEMOTED": 1}},
    "undeclared": {"native": [], "pure": []},
    "divergent": [],
    "witness": {"P": "9007199254740993", "F": "9007199254740992",
                "G": "9007199254740994"},
}
_ROWS = [
    {"op": "pkg.mod.alpha", "param": "xs", "type": "list[float]",
     "base_source": "ledger",
     "native": {"verdict": "EXACT", "leaf": [0], "shape": "harvested"},
     "pure": {"verdict": "EXACT", "leaf": [0], "shape": "harvested"}},
    {"op": "pkg.mod.beta", "param": "ys", "type": "list[float]",
     "base_source": "ledger",
     "native": {"verdict": "DEMOTED", "reason": "collapsed", "declares": [],
                "leaf": [0], "shape": "harvested"},
     "pure": {"verdict": "DEMOTED", "reason": "collapsed", "declares": [],
              "leaf": [0], "shape": "harvested"}},
]


def _text(meta=None, rows=None) -> str:
    m = json.loads(json.dumps(_META)) if meta is None else meta
    r = json.loads(json.dumps(_ROWS)) if rows is None else rows
    return "\n".join([json.dumps(m, sort_keys=True)]
                     + [json.dumps(x, sort_keys=True) for x in r]) + "\n"


def _run(before: str, after: str, **kw) -> int:
    opts = dict(meta_may_move=("measured_at",),
                by_verdict=_META["by_verdict"], n_rows=2, n_ops=2,
                cells=("native", "pure"))
    opts.update(kw)
    return crd.compare(before, after, **opts)


# ── the positive control ─────────────────────────────────────────────────────
def test_an_unmutated_pair_is_HELD():
    """Without this, every red below could be the tool refusing everything."""
    assert _run(_text(), _text()) == 0


def test_a_measured_at_move_alone_is_still_HELD():
    """The ONE meta key a re-measure always moves must not break the claim."""
    m = json.loads(json.dumps(_META))
    m["measured_at"]["native"]["srmech_version"] = "9.9.9"
    assert _run(_text(), _text(meta=m)) == 0


# ── (i) ──────────────────────────────────────────────────────────────────────
def test_an_unexpected_meta_key_breaks_clause_i(capsys):
    m = json.loads(json.dumps(_META))
    m["registry_signature_sha256"]["native"] = "dd" * 32
    assert _run(_text(), _text(meta=m)) == 1
    out = capsys.readouterr().out
    assert "CLAUSE (i): FAIL" in out
    assert "registry_signature_sha256" in out


# ── (ii) ─────────────────────────────────────────────────────────────────────
def test_a_declares_move_alone_is_HELD_and_leaves_the_verdict_clause_green(
        capsys):
    """(ii)'s ALLOWANCE and (iii)'s silence, asserted as one case.

    This is the combination rc470's regeneration actually produced (74
    ``declares`` cell-columns, zero verdicts). It must read as HELD, or the
    tool cannot tell a reader change from a measurement change.
    """
    rows = json.loads(json.dumps(_ROWS))
    rows[1]["native"]["declares"] = ["float64"]
    assert _run(_text(), _text(rows=rows)) == 0
    out = capsys.readouterr().out
    assert "data lines differing at all: 1 of 2" in out
    assert "cell-columns moved inside ['declares']: 1" in out
    assert "VERDICT CHANGES: 0" in out


def test_a_field_outside_declares_breaks_clause_ii(capsys):
    rows = json.loads(json.dumps(_ROWS))
    rows[1]["native"]["reason"] = "collapsed differently"
    assert _run(_text(), _text(rows=rows)) == 1
    out = capsys.readouterr().out
    assert "CLAUSE (ii): FAIL" in out
    assert "native.reason" in out


def test_a_dropped_row_breaks_clause_ii(capsys):
    rows = json.loads(json.dumps(_ROWS))[:1]
    assert _run(_text(), _text(rows=rows), n_rows=None) == 1
    out = capsys.readouterr().out
    assert "CLAUSE (ii): FAIL" in out
    assert "REMOVED pkg.mod.beta::ys" in out


def test_an_added_row_breaks_clause_ii(capsys):
    rows = json.loads(json.dumps(_ROWS))
    extra = json.loads(json.dumps(_ROWS[0]))
    extra["op"] = "pkg.mod.gamma"
    rows.append(extra)
    assert _run(_text(), _text(rows=rows), n_rows=None, n_ops=None) == 1
    out = capsys.readouterr().out
    assert "CLAUSE (ii): FAIL" in out
    assert "ADDED pkg.mod.gamma::xs" in out


# ── (ii), the rc472 allowance: a NEW LANE adds rows without moving any ───────
def _scalar_extra(op="pkg.mod.gamma", ty="float"):
    extra = json.loads(json.dumps(_ROWS[0]))
    extra["op"], extra["param"], extra["type"] = op, "x", ty
    return extra


def _meta_for(rows):
    """A meta line CONSISTENT with ``rows`` — n_rows / n_ops / by_verdict
    derived — so each test below fails on the clause it names and no other."""
    m = json.loads(json.dumps(_META))
    m["n_rows"] = len(rows)
    m["n_ops"] = len({r["op"] for r in rows})
    m["by_verdict"] = {}
    for cel in ("native", "pure"):
        hist = {}
        for r in rows:
            v = r[cel]["verdict"]
            hist[v] = hist.get(v, 0) + 1
        m["by_verdict"][cel] = hist
    return m


#: The meta keys a LANE-ADDING regeneration legitimately moves besides
#: ``measured_at`` — each is pinned EXPLICITLY by clause (iv) / (v), which is
#: why clause (i) may let it through. ``probe_signature_sha256`` is the fifth
#: such key in the real rc472 run (a new lane is a new PROBE_SPEC member) and
#: is deliberately NOT in this fixture's list: the fixture never moves it, so
#: listing it here would be an allowance nothing exercises.
_LANE_ADD_MAY_MOVE = ("measured_at", "by_verdict", "n_rows", "n_ops")


def _run_added(rows, **kw):
    m = _meta_for(rows)
    opts = dict(n_rows=m["n_rows"], n_ops=m["n_ops"], by_verdict=m["by_verdict"],
                meta_may_move=_LANE_ADD_MAY_MOVE)
    opts.update(kw)
    return _run(_text(), _text(meta=m, rows=rows), **opts)


def test_a_lane_addition_still_refuses_an_unlisted_meta_move_rc472(capsys):
    """The allowance is BY KEY: with the fixture's own three keys allowed, a
    moved registry signature is still clause (i) RED."""
    rows = json.loads(json.dumps(_ROWS)) + [_scalar_extra()]
    m = _meta_for(rows)
    m["registry_signature_sha256"]["native"] = "dd" * 32
    assert _run(_text(), _text(meta=m, rows=rows), n_rows=3, n_ops=3,
                by_verdict=m["by_verdict"], meta_may_move=_LANE_ADD_MAY_MOVE,
                expect_added=1, added_lane="scalar") == 1
    out = capsys.readouterr().out
    assert "CLAUSE (i): FAIL" in out and "registry_signature_sha256" in out
    assert "CLAUSE (ii): PASS" in out


def test_an_expected_added_row_in_the_named_lane_is_HELD_rc472(capsys):
    """rc472 (`#T1188`): the scalar lane adds rows and moves none. Exactly the
    expected count, every one in the named lane, and the addition is PRINTED
    per cell by verdict so it is a figure rather than a bare count."""
    rows = json.loads(json.dumps(_ROWS)) + [_scalar_extra()]
    assert _run_added(rows, expect_added=1, added_lane="scalar") == 0
    out = capsys.readouterr().out
    assert "rows added 1 (expected 1, lane scalar)" in out
    assert 'added rows [native] by_verdict {"EXACT": 1}' in out
    assert "added rows over 1 ops" in out
    assert "VERDICT CHANGES: 0" in out
    assert "INVARIANT: HELD (5/5)" in out


def test_an_added_row_outside_the_named_lane_breaks_clause_ii_rc472(capsys):
    """A SEQUENCE row arriving under a scalar-lane allowance is not the lane
    growing — it is a population change the allowance was never for."""
    rows = json.loads(json.dumps(_ROWS)) + [_scalar_extra(ty="list[float]")]
    assert _run_added(rows, expect_added=1, added_lane="scalar") == 1
    out = capsys.readouterr().out
    assert "CLAUSE (ii): FAIL" in out
    assert "is in lane 'sequence', not 'scalar'" in out
    assert "CLAUSE (iii): PASS" in out and "CLAUSE (iv): PASS" in out


def test_more_added_rows_than_expected_breaks_clause_ii_rc472(capsys):
    rows = json.loads(json.dumps(_ROWS)) + [_scalar_extra(),
                                            _scalar_extra(op="pkg.mod.delta")]
    assert _run_added(rows, expect_added=1, added_lane="scalar") == 1
    out = capsys.readouterr().out
    assert "rows added 2 (expected 1, lane scalar)" in out
    assert "CLAUSE (ii): FAIL" in out
    assert "CLAUSE (iv): PASS" in out


def test_an_expected_addition_with_no_lane_named_breaks_clause_ii_rc472(capsys):
    """An allowance must name the lane it is for, or any row could ride it."""
    rows = json.loads(json.dumps(_ROWS)) + [_scalar_extra()]
    assert _run_added(rows, expect_added=1, added_lane="") == 1
    out = capsys.readouterr().out
    assert "CLAUSE (ii): FAIL" in out
    assert "CLAUSE (iv): PASS" in out


def test_an_expected_addition_does_not_license_a_removal_rc472(capsys):
    rows = json.loads(json.dumps(_ROWS))[:1] + [_scalar_extra()]
    assert _run_added(rows, expect_added=1, added_lane="scalar") == 1
    out = capsys.readouterr().out
    assert "REMOVED pkg.mod.beta::ys" in out
    assert "CLAUSE (ii): FAIL" in out
    assert "CLAUSE (iv): PASS" in out


def test_an_expected_addition_does_not_hide_a_moved_verdict_rc472(capsys):
    """Clause (iii) runs over the SHARED keys, so an addition cannot mask a
    move and a move cannot pass as an addition."""
    rows = json.loads(json.dumps(_ROWS)) + [_scalar_extra()]
    rows[0]["native"]["verdict"] = "DEMOTED"
    assert _run_added(rows, expect_added=1, added_lane="scalar") == 1
    out = capsys.readouterr().out
    # the ADDITION is accounted for exactly as expected ...
    assert "rows added 1 (expected 1, lane scalar)  removed 0" in out
    # ... and the MOVE is still reported on its own clause (clause (ii) also
    # flags the moved verdict as a field outside `declares`, exactly as the
    # rc471 precedent `test_a_moved_verdict_breaks_clause_iii` records).
    assert "VERDICT CHANGES: 1" in out
    assert "pkg.mod.alpha::xs [native] EXACT -> DEMOTED" in out
    assert "CLAUSE (iii): FAIL" in out


# ── (iii) ────────────────────────────────────────────────────────────────────
def test_a_moved_verdict_breaks_clause_iii(capsys):
    rows = json.loads(json.dumps(_ROWS))
    rows[0]["native"]["verdict"] = "DEMOTED"
    assert _run(_text(), _text(rows=rows)) == 1
    out = capsys.readouterr().out
    assert "CLAUSE (iii): FAIL" in out
    assert "VERDICT CHANGES: 1" in out
    assert "pkg.mod.alpha::xs [native] EXACT -> DEMOTED" in out


# ── (iii), the rc472-C3 allowance: a REACH REPAIR moves verdicts OUT of one
#    named verdict — exactly N per cell, the same rows in every cell, none
#    INTO it, and nothing else ────────────────────────────────────────────────
def _raised_pair(after_native="EXACT", after_pure="EXACT", moved_rows=(0,)):
    """``(before, after)`` row lists: every index in ``moved_rows`` reads
    RAISED in both cells BEFORE and the given verdicts AFTER."""
    before = json.loads(json.dumps(_ROWS))
    after = json.loads(json.dumps(_ROWS))
    for i in moved_rows:
        for cel in ("native", "pure"):
            before[i][cel] = {"verdict": "RAISED", "reason": "TypeError: planted"}
        for cel, v in (("native", after_native), ("pure", after_pure)):
            after[i][cel] = {"verdict": v, "leaf": [0], "shape": "[1]*8"}
            if v == "DEMOTED":
                after[i][cel]["declares"] = []
    return before, after


def _run_moved(before, after, **kw):
    mb, ma = _meta_for(before), _meta_for(after)
    opts = dict(n_rows=ma["n_rows"], n_ops=ma["n_ops"],
                by_verdict=ma["by_verdict"], meta_may_move=_LANE_ADD_MAY_MOVE)
    opts.update(kw)
    return _run(_text(meta=mb, rows=before), _text(meta=ma, rows=after), **opts)


def test_an_expected_move_out_of_the_named_verdict_is_HELD_rc472(capsys):
    """rc472 C3 (`#T1188`): the required-scalar fill lets rows BIND that used
    to raise at a synthesised sibling, so their verdict moves OUT of RAISED.
    The allowance is exactly N per cell, every move out of the named verdict
    and none into it, the same rows in every cell — and the cell-columns
    that moved are the ONLY data that may differ outside `declares`."""
    before, after = _raised_pair()
    assert _run_moved(before, after, expect_moved=1, moved_from="RAISED") == 0
    out = capsys.readouterr().out
    assert ("VERDICT CHANGES: 2 (expected 1 per cell, every one OUT of "
            "'RAISED' and none INTO it)") in out
    assert "moved [native]: 1" in out and "moved [pure]: 1" in out
    assert 'transitions: {"RAISED->EXACT": 2}' in out
    assert "CLAUSE (ii): PASS" in out and "CLAUSE (iii): PASS" in out
    assert "INVARIANT: HELD (5/5)" in out


def test_more_moves_than_expected_breaks_clause_iii_rc472(capsys):
    before, after = _raised_pair(moved_rows=(0, 1))
    assert _run_moved(before, after, expect_moved=1, moved_from="RAISED") == 1
    out = capsys.readouterr().out
    assert "moved [native]: 2" in out
    assert "CLAUSE (iii): FAIL" in out


def test_a_move_INTO_the_named_verdict_breaks_clause_iii_rc472(capsys):
    """The direction is the half an accident cannot satisfy: a row ARRIVING
    in RAISED under an out-of-RAISED allowance is red even at the right
    count."""
    before, after = _raised_pair()
    for cel in ("native", "pure"):
        after[1][cel] = {"verdict": "RAISED", "reason": "planted"}
    assert _run_moved(before, after, expect_moved=2, moved_from="RAISED") == 1
    out = capsys.readouterr().out
    assert "moved [native]: 2" in out
    assert ("pkg.mod.beta::ys [native] DEMOTED -> RAISED is not a move OUT "
            "of 'RAISED'") in out
    assert "CLAUSE (iii): FAIL" in out


def test_a_move_from_another_verdict_breaks_clause_iii_rc472(capsys):
    before, after = _raised_pair()
    for cel in ("native", "pure"):
        after[1][cel]["verdict"] = "EXACT"        # DEMOTED -> EXACT
    assert _run_moved(before, after, expect_moved=2, moved_from="RAISED") == 1
    out = capsys.readouterr().out
    assert ("pkg.mod.beta::ys [native] DEMOTED -> EXACT is not a move OUT "
            "of 'RAISED'") in out
    assert "CLAUSE (iii): FAIL" in out


def test_cells_that_move_different_rows_break_clause_iii_rc472(capsys):
    """'The same N rows in every cell' is part of the pin: a native-only move
    beside a pure-only move elsewhere has the right COUNT in each cell and
    is still red."""
    before, after = _raised_pair(moved_rows=(0, 1))
    after[0]["pure"] = json.loads(json.dumps(before[0]["pure"]))
    after[1]["native"] = json.loads(json.dumps(before[1]["native"]))
    assert _run_moved(before, after, expect_moved=1, moved_from="RAISED") == 1
    out = capsys.readouterr().out
    assert "moved [native]: 1" in out and "moved [pure]: 1" in out
    assert "the moved key sets DIFFER across cells" in out
    assert "CLAUSE (iii): FAIL" in out


def test_an_expected_move_does_not_license_an_unmoved_rows_field_rc472(capsys):
    """The clause (ii) exemption is per moved CELL-COLUMN, never per file: a
    `reason` edit on a row whose verdict did not move is still red."""
    before, after = _raised_pair()
    after[1]["native"]["reason"] = "reworded"
    assert _run_moved(before, after, expect_moved=1, moved_from="RAISED") == 1
    out = capsys.readouterr().out
    assert "pkg.mod.beta::ys differs OUTSIDE ['declares']" in out
    assert "CLAUSE (ii): FAIL" in out
    assert "CLAUSE (iii): PASS" in out


def test_an_expected_move_with_no_verdict_named_breaks_clause_iii_rc472(capsys):
    before, after = _raised_pair()
    assert _run_moved(before, after, expect_moved=1, moved_from="") == 1
    out = capsys.readouterr().out
    assert "an allowance must name the verdict it is for" in out
    assert "CLAUSE (iii): FAIL" in out


def test_an_expected_move_does_not_license_an_addition_rc472(capsys):
    before, after = _raised_pair()
    after.append(_scalar_extra())
    assert _run_moved(before, after, expect_moved=1, moved_from="RAISED") == 1
    out = capsys.readouterr().out
    assert "ADDED pkg.mod.gamma::x" in out
    assert "CLAUSE (ii): FAIL" in out
    assert "CLAUSE (iii): PASS" in out


# ── (ii), the rc472-C3 labeller allowance: rows named IN ADVANCE may differ
#    in `shape` only; every named row must relabel; an unnamed relabel is red ─
def _relabelled(keys=("pkg.mod.alpha::xs",)):
    rows = json.loads(json.dumps(_ROWS))
    for r in rows:
        if f"{r['op']}::{r['param']}" in keys:
            for cel in ("native", "pure"):
                r[cel]["shape"] = "synth[0]"
    return rows


def test_a_named_relabel_in_shape_only_is_HELD_rc472(capsys):
    assert _run(_text(), _text(rows=_relabelled()),
                may_relabel=("pkg.mod.alpha::xs",)) == 0
    out = capsys.readouterr().out
    assert "rows allowed to RELABEL (shape only): 1 named, 1 relabelled" in out
    assert "pkg.mod.alpha::xs native.shape: 'harvested' -> 'synth[0]'" in out
    assert "CLAUSE (ii): PASS" in out and "INVARIANT: HELD (5/5)" in out


def test_an_unnamed_relabel_is_still_red_rc472(capsys):
    assert _run(_text(), _text(rows=_relabelled()),
                may_relabel=("pkg.mod.beta::ys",)) == 1
    out = capsys.readouterr().out
    assert "pkg.mod.alpha::xs differs OUTSIDE ['declares']" in out
    assert "pkg.mod.beta::ys was named in --may-relabel but did not relabel" in out
    assert "CLAUSE (ii): FAIL" in out


def test_a_named_row_may_not_move_anything_but_shape_rc472(capsys):
    rows = _relabelled()
    rows[0]["native"]["leaf"] = [1]
    assert _run(_text(), _text(rows=rows),
                may_relabel=("pkg.mod.alpha::xs",)) == 1
    out = capsys.readouterr().out
    assert "native.leaf: [0] -> [1]" in out
    assert "CLAUSE (ii): FAIL" in out


def test_a_named_row_that_does_not_relabel_is_slack_and_red_rc472(capsys):
    assert _run(_text(), _text(), may_relabel=("pkg.mod.alpha::xs",)) == 1
    out = capsys.readouterr().out
    assert "pkg.mod.alpha::xs was named in --may-relabel but did not relabel" in out
    assert "CLAUSE (ii): FAIL" in out


# ── (iv) ─────────────────────────────────────────────────────────────────────
def test_a_by_verdict_count_off_by_one_breaks_clause_iv(capsys):
    m = json.loads(json.dumps(_META))
    m["by_verdict"]["pure"]["EXACT"] = 2
    assert _run(_text(), _text(meta=m)) == 1
    out = capsys.readouterr().out
    assert "CLAUSE (iv): FAIL" in out


# ── (v) ──────────────────────────────────────────────────────────────────────
def test_a_wrong_n_ops_breaks_clause_v(capsys):
    m = json.loads(json.dumps(_META))
    m["n_ops"] = 3
    assert _run(_text(), _text(meta=m)) == 1
    out = capsys.readouterr().out
    assert "CLAUSE (v): FAIL" in out


def test_a_missing_cell_breaks_clause_v(capsys):
    m = json.loads(json.dumps(_META))
    m["cells_measured"] = ["pure"]
    assert _run(_text(), _text(meta=m)) == 1
    assert "CLAUSE (v): FAIL" in capsys.readouterr().out


# ── the tool against the SHIPPED manifest, self-compared ─────────────────────
def test_the_shipped_manifest_is_HELD_against_itself(capsys):
    """A shape check on the real file: it must parse, and the identity compare
    must be clean. It says nothing about the regeneration — that comparison
    needs the committed BASELINE, which only git can produce and which this
    file deliberately does not shell out for."""
    text = CENSUS.read_text(encoding="utf-8")
    meta, rows = crd.load(text)
    assert meta["record"] == "meta"
    assert len(rows) == meta["n_rows"]
    assert crd.compare(text, text, meta_may_move=(),
                       by_verdict=meta["by_verdict"],
                       n_rows=meta["n_rows"], n_ops=meta["n_ops"],
                       cells=("native", "pure")) == 0
    assert "INVARIANT: HELD (5/5)" in capsys.readouterr().out


def test_DATA_MAY_MOVE_is_exactly_declares():
    """Widening it is a claim about the instrument, not a convenience — so it
    is pinned, and a later rc that widens it has to move this line and say why.
    """
    assert crd.DATA_MAY_MOVE == ("declares",)


def test_the_tool_shells_out_to_no_git():
    """The baseline arrives as a FILE, on purpose: rc471 measured what an
    ambient ``GIT_DIR`` does to a suite full of git fixtures."""
    src = (_TOOLS / "census_regen_diff.py").read_text(encoding="utf-8")
    code = "\n".join(ln for ln in src.splitlines()
                     if not ln.lstrip().startswith("#"))
    assert "subprocess" not in code
    assert "import git" not in code


@pytest.mark.parametrize("bad", ["", "   \n\n"])
def test_an_empty_manifest_is_refused_loudly(bad):
    with pytest.raises(SystemExit):
        crd.load(bad)
