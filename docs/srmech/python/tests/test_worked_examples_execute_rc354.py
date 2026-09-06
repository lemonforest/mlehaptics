"""rc354 — the worked-example EXECUTION gate (gh #1530 §K).

THE COMPLEMENT, NOT THE COMPETITOR
==================================
``tests/test_worked_examples_strict_zero_rc353.py`` is a **decidable** gate:
three properties read off the registry with no re-execution, milliseconds, no
flake. Its own docstring says plainly what it cannot do —

    It is **NOT** a truth guard. It cannot distinguish a captured output from a
    typed one — only re-execution can […]

This is that re-execution. rc353 is unchanged and stays green; neither gate
subsumes the other.

WHAT IT ASSERTS, AND WHAT IT DELIBERATELY DOES NOT
==================================================
It asserts that every snippet **compiles and runs**, and that every
**documented raise actually fires with the documented type**. It does NOT
compare printed results against the ``output`` field: in this tree that field
is a human-composed rendering, not a REPL transcript, so a diff against it
would fail on formatting and teach nothing. Saying so is the point — a gate
believed to check more than it does is the next false green.

THE EXPLICIT KEY
================
A documented raise is marked by the inline ``# -> <ExcType>`` comment, bound to
the STATEMENT it follows. §K asked explicit-key vs a scan over ``worked`` and
``output``; the scan is rejected on measurement, because 9 snippets carry a
raise annotation and die EARLIER from an unrelated cause. "This snippet
documents a raise, therefore a raise is a pass" marks all 9 GREEN — a false
green in the test built to stop one, strictly worse than the two false-RED
traps §K records. A marked statement must raise **that exact type**; an
unmarked statement must not raise. Both directions fail loudly, so a marker
that does not fire is itself a failure and prose cannot green anything.

BOTH §K TRAPS ARE HONOURED
==========================
* **a documented raise is a PASS** — ``hdc.loop_bind_hd`` raises
  ``AssertionError`` at line 22 of 23 and line 23 is its own annotation. It is
  a teaching guard, not a breakage, and this gate VERIFIES it fires rather than
  reporting it broken. It was never "fixed".
* **guard detection never reads the ``output`` field** — only the statement
  binding. A guard whose ``output`` text was reworded is unaffected.

THE SHAPE: TWO STRICT ZEROS AND A DOWN-ONLY CEIL
================================================
Same rc348 discipline: strict zero on the decidable classes (freshness,
compiles, markers), a down-only ceiling on the residual that drains over time.
The ceiling is **per failure class**, never one global number, so a genome
regression cannot hide behind a laplacian fix — and per CI cell, because
native dispatch changes outcomes.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

LEDGER = Path(__file__).resolve().parent / "worked_examples_result.ndjson"

# ── the down-only ceilings, MEASURED, never guessed ───────────────────────
#
# Seeded by running ``python3 tools/run_worked_examples.py`` once in each cell
# and committing what it printed. A gain is BANKED: an under-count fails just
# as loudly as an over-count, so a snippet repair must lower the number here in
# the same commit.
#
# ``pure`` = HAS_NATIVE False. Native dispatch changes outcomes (``is_prime``
# on Mersenne M61 is minutes of trial division in Python and fast in C), so a
# number measured in one cell must never be pinned against the other.
#
# ``None`` means NOT YET MEASURED IN THIS CELL, and the ceiling test SKIPS with
# that reason rather than asserting a number nobody ran. Copying the native
# figures across would be a guess wearing a measurement's clothes — precisely
# the failure mode this arc keeps repairing. Seed it by running the executor in
# a numpy-absent, native-absent cell and committing what it printed.
CEIL_WORKED_EXAMPLE_FAILURES = {
    # measured 2026-07-28, WSL2 / CPython 3.10.12 / HAS_NATIVE True, 427
    # snippets: 326 ok, 96 unexpected_raise, 4 needs_subprocess, 1 timeout
    # (``rbs_lm.encode_aboutness``), 0 syntax_error, 0 marker failures.
    "native": {"unexpected_raise": 96, "timeout": 1},
    # measured at rc460, CPython 3.10 / HAS_NATIVE False / numpy ABSENT, 605
    # snippets: 504 ok, 96 unexpected_raise, 4 needs_subprocess, 1 timeout
    # (``rbs_lm.encode_aboutness``), 0 syntax_error, 0 marker failures.
    #
    # ⚠️ SEEDED BECAUSE rc460 SILENTLY DISARMED THIS RATCHET, and a green
    # board is exactly how that hid.  rc459's committed ledger carried
    # ``"native": true`` and the ceiling below it was ENFORCED.  rc460
    # regenerated the ledger in a native-absent worktree, the meta row flipped
    # to ``"native": false``, the cell selector above swung to ``"pure"`` — and
    # ``"pure"`` was ``None``, so the assertion stopped running and reported
    # itself as one routine ``skipped``.  Nothing regressed numerically; the
    # ratchet simply went inert while every number it guards stayed correct.
    #
    # These figures are NOT the native column copied across — that is the
    # failure this block's own docstring names, and it would be undetectable
    # here precisely because the two cells happen to agree on both classes.
    # They are read off the rc460 ledger itself, which IS a run in this cell
    # (its meta row records ``native: false``), i.e. the measurement the
    # paragraph above asks for rather than a guess wearing its clothes.  That
    # the two cells agree is not a coincidence: the residual is dominated by
    # snippet defects that do not care about native dispatch (missing
    # ``tomli``, cwd-relative attested-row reads, ``NameError`` on undefined
    # names).
    #
    # ⚠️ BUT THE PURE FIGURE IS HOST-DEPENDENT, AND THE RATCHET IS RIGHT TO
    # BE STRICT ABOUT IT.  Re-running the executor on a native-Windows host
    # (CPython 3.14, numpy absent, HAS_NATIVE False) measured **97**, not 96 —
    # and the single differing snippet is ``amsc.catalog.register_attested_root``,
    # whose worked example hardcodes the WSL path
    # ``/mnt/d/GitHub/mlehaptics/.../ephemerides-spectral/...`` for the SISTER
    # package's attested root.  Where that path resolves the snippet succeeds;
    # where it does not, ``get_attested_dataset`` returns a payload with no
    # ``total`` key and line 18 dies on ``KeyError: 'total'``.
    #
    # So this ledger encodes one fact about the machine that generated it, and
    # a regeneration elsewhere WILL read 97 and trip the ceiling.  That is the
    # ratchet working, not breaking: the right response is to fix the snippet's
    # absolute path (it is the only host-coupled one found), not to raise the
    # number.  Recorded here because it is invisible from the committed
    # artifact alone — the ledger reports a tally, never the host it needed.
    "pure": {"unexpected_raise": 96, "timeout": 1},
}


def _rows():
    assert LEDGER.exists(), (
        f"{LEDGER.name} is missing. Run: python3 tools/run_worked_examples.py")
    rows = [json.loads(l) for l in LEDGER.read_text(encoding="utf-8").splitlines()
            if l.strip()]
    meta = next(r for r in rows if r.get("record") == "meta")
    return meta, [r for r in rows if "name" in r]


def _live():
    """``{name: src_sha256}`` recomputed from the LIVE schema."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
    import run_worked_examples as rwe
    return {j["name"]: j["src_sha256"] for j in rwe.collect()}


# ── (A) STRICT ZERO — the ledger is fresh ─────────────────────────────────

def test_ledger_is_fresh_against_the_live_schema() -> None:
    """Every snippet's ``src_sha256`` matches, and the name sets are equal.

    This is the assertion that makes the other three trustworthy: without it
    the ratchet reports on a tree that no longer exists. It catches added,
    removed AND edited snippets, per-snippet rather than per-run, so the fix is
    ``--only-stale`` and costs one import plus the changed snippets.
    """
    _meta, rows = _rows()
    ledger = {r["name"]: r["src_sha256"] for r in rows}
    live = _live()
    added = sorted(set(live) - set(ledger))
    removed = sorted(set(ledger) - set(live))
    edited = sorted(n for n in set(live) & set(ledger) if live[n] != ledger[n])
    assert not (added or removed or edited), (
        "the worked-example ledger is STALE. Re-run:\n"
        "    python3 tools/run_worked_examples.py --only-stale\n"
        f"  added({len(added)}):   {added[:8]}\n"
        f"  removed({len(removed)}): {removed[:8]}\n"
        f"  edited({len(edited)}):  {edited[:8]}")


# ── (B) STRICT ZERO — every snippet compiles ──────────────────────────────

def test_no_snippet_is_a_syntax_error() -> None:
    """rc353 shipped 7 snippets holding an English sentence where code goes.

    ``max component drift  # -> 3.552713678800501e-15`` is not Python. Zero
    execution, zero judgement, seven one-line repairs — pinned at zero here.
    """
    _meta, rows = _rows()
    bad = sorted(r["name"] for r in rows if r["status"] == "syntax_error")
    assert not bad, (
        f"{len(bad)} worked snippet(s) do not parse. A snippet is CODE; put "
        f"the sentence in `why` or `explanation` and make the line compute the "
        f"value the `output` field records:\n  " + "\n  ".join(bad[:10]))


# ── (C) STRICT ZERO — every marked statement raises its marked type ───────

def test_every_documented_raise_actually_fires() -> None:
    """The assertion that kills all three classifier traps at once.

    It cannot mark a guard broken (trap 1: a fired marker is a PASS), it does
    not read ``output`` at all (trap 2), and it cannot be satisfied by an
    unrelated earlier exception (trap 3: the marker is bound to a STATEMENT, so
    dying at line 2 does not discharge a marker on line 20).
    """
    _meta, rows = _rows()
    bad = []
    for r in rows:
        for p in r["problems"]:
            if p["kind"] == "marker_did_not_fire":
                bad.append(f"{r['name']}: line {p['line']} documents "
                           f"{p['expected']} and nothing was raised")
            elif p["kind"] == "marker_mismatch":
                bad.append(f"{r['name']}: line {p['line']} documents "
                           f"{p['expected']}, got {p['got']}")
    assert not bad, (
        f"{len(bad)} documented raise(s) are wrong. Fix the CAUSE, never "
        f"delete the marker — a guard that no longer guards is the defect:\n  "
        + "\n  ".join(bad[:10]))


# ── (D) DOWN-ONLY CEIL — the residual, per class ──────────────────────────

def test_unexpected_outcomes_are_at_or_below_the_ceiling() -> None:
    """Per failure CLASS, never one global number, and never given back."""
    meta, rows = _rows()
    cell = "native" if meta.get("native") else "pure"
    ceil = CEIL_WORKED_EXAMPLE_FAILURES[cell]
    if ceil is None:
        pytest.skip(
            f"no ceiling has been MEASURED for the {cell!r} cell. Seed it with "
            f"`python3 tools/run_worked_examples.py` in that cell and commit "
            f"what it printed — do not copy the other cell's numbers.")
    tally = Counter(r["status"] for r in rows)
    over, under = [], []
    for kind, limit in ceil.items():
        n = tally.get(kind, 0)
        if n > limit:
            names = [r["name"] for r in rows if r["status"] == kind][:6]
            over.append(f"{kind}: {n} > CEIL {limit}  e.g. {names}")
        elif n < limit:
            under.append(f"{kind}: {n} < CEIL {limit} — BANK IT")
    assert not over, (
        f"[{cell}] worked-example failures went UP:\n  " + "\n  ".join(over))
    if under:
        pytest.fail(
            f"[{cell}] the ceiling is now too loose — lower "
            f"CEIL_WORKED_EXAMPLE_FAILURES in the SAME commit so the gain "
            f"cannot be given back:\n  " + "\n  ".join(under))


def test_the_cell_the_committed_ledger_selects_is_actually_SEEDED() -> None:
    """The ceiling above may not SKIP on the ledger this tree ships.

    rc460 is why this exists.  Regenerating the ledger in a native-absent
    worktree flipped its meta row from ``"native": true`` to ``false``, which
    swung the cell selector from ``"native"`` to ``"pure"`` — and ``"pure"``
    was ``None``, so the down-only ratchet stopped asserting and said so as a
    single ``skipped``.  On a board that is otherwise green, one skip reads as
    routine; it took a deliberate rc-over-rc comparison to notice that a gate
    which had been ENFORCING at rc459 was inert at rc460, with every number it
    guards unchanged.

    The skip itself is the right behaviour for a genuinely unmeasured cell —
    asserting a number nobody ran is the worse failure.  What was missing is
    that NOBODY IS TOLD.  This test is the paired assertion: the skip stays
    available as a seeding path, but it can no longer apply to the artifact
    actually committed.  Regenerate in a new cell and the suite goes RED with
    instructions, instead of quietly dropping a ratchet.
    """
    meta, _rows_ = _rows()
    cell = "native" if meta.get("native") else "pure"
    assert cell in CEIL_WORKED_EXAMPLE_FAILURES, (
        f"the committed ledger selects cell {cell!r}, which has no entry in "
        f"CEIL_WORKED_EXAMPLE_FAILURES at all")
    assert CEIL_WORKED_EXAMPLE_FAILURES[cell] is not None, (
        f"the committed ledger was generated in the {cell!r} cell "
        f"(meta native={meta.get('native')!r}) and NO ceiling has been "
        f"measured for it, so the down-only ratchet next door is SKIPPING on "
        f"the artifact this tree actually ships. Seed it: run "
        f"`python3 tools/run_worked_examples.py` in this cell and commit what "
        f"it printed — do NOT copy the other cell's numbers.")


def test_the_needs_subprocess_set_is_declared_not_silently_timed_out() -> None:
    """Four snippets need a REAL second process. Declared, never a timeout.

    A timeout on these would be the harness lying about them — reporting a
    budget failure for something it structurally cannot run in-worker.
    """
    _meta, rows = _rows()
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
    import run_worked_examples as rwe
    declared = set(rwe.NEEDS_SUBPROCESS)
    seen = {r["name"] for r in rows if r["status"] == "needs_subprocess"}
    assert seen == declared & {r["name"] for r in rows}, (seen, declared)
    for r in rows:
        if r["name"] in declared:
            assert r["status"] != "timeout", r["name"]


# ── (F) STRICT ZERO — every row knows which module DEFINES it ─────────────

def test_every_row_carries_its_defining_module_and_content_stamp() -> None:
    """``def_module`` + ``def_blob`` on all 651 rows, and the module must be
    the LIVE one. (rc468, `#T1188`)

    The freshness hook matched a row to a changed module by its PUBLISHED
    dotted name. ``srmech.cascade.compensated_sum`` is defined in
    ``srmech.cascade.composites`` and re-exported by the package ``__init__``,
    so that test could not match it: measured, **165 of 651 rows (25.3%)**
    across 64 defining modules were invisible, all-or-nothing per module.
    Recording the defining module IN THE ROW is what lets the hook stay
    import-free and still see them.

    ⚠️ THE FIELD ERODES IF ONLY ``collect()`` SETS IT. A record that comes back
    from the worker is a fresh dict, so ``run()`` must stamp it too — otherwise
    every re-run row silently loses both fields, i.e. exactly the rows a
    by-name pass touches. This assertion is what makes that failure loud.
    """
    _meta, rows = _rows()
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
    import run_worked_examples as rwe

    missing = sorted(r["name"] for r in rows
                     if not r.get("def_module") or not r.get("def_blob"))
    assert not missing, (
        f"{len(missing)} ledger row(s) carry no defining-module stamp. "
        "Re-run them, or `python3 tools/run_worked_examples.py --backfill` if "
        "their defining modules have not moved since meta.verified_at:\n"
        f"  {missing[:8]}")

    live = {j["name"]: j["def_module"] for j in rwe.collect()}
    wrong = sorted(r["name"] for r in rows
                   if r["name"] in live and r["def_module"] != live[r["name"]])
    assert not wrong, (
        "a row's recorded defining module is not where the op lives now. "
        "That is a REBIND — a package __init__ now re-exports it from a "
        "different submodule — and the row's content stamp is watching the "
        f"wrong file:\n  {[(n, live[n]) for n in wrong[:8]]}")


# ── the meta-test: prove the gate can go red ──────────────────────────────

_PLANTED = {
    # the rc353 shape: an English sentence where code goes.
    "prose_in_code": {"status": "syntax_error",
                      "problems": [{"kind": "syntax_error", "line": 10,
                                    "detail": "invalid syntax"}]},
    # a guard that stopped guarding — the marker no longer fires.
    "marker_dead": {"status": "marker_did_not_fire",
                    "problems": [{"kind": "marker_did_not_fire", "line": 20,
                                  "expected": "ValueError"}]},
    # the cwd-relative read: open('srmech/amsc/...') from anywhere real.
    "cwd_relative_read": {"status": "unexpected_raise",
                          "problems": [{"kind": "unexpected_raise", "line": 3,
                                        "expected": None,
                                        "got": "FileNotFoundError"}]},
    # an unbounded loop the parent has to kill.
    "runaway": {"status": "timeout",
                "problems": [{"kind": "timeout", "budget_s": 15.0}]},
}


@pytest.mark.parametrize("kind", sorted(_PLANTED))
def test_gate_fires_on_a_planted_defect(kind: str) -> None:
    """A guard that has never been seen to fail is not evidence.

    Each plant is a shape that ACTUALLY SHIPPED in this tree, so these are
    reproductions rather than synthetic probes.
    """
    rec = dict(_PLANTED[kind], name="planted." + kind, src_sha256="0" * 64,
               markers_fired=[], statements=0)
    tripped_b = rec["status"] == "syntax_error"
    tripped_c = any(p["kind"] in ("marker_did_not_fire", "marker_mismatch")
                    for p in rec["problems"])
    tripped_d = rec["status"] in ("unexpected_raise", "timeout")
    expected = {"prose_in_code": tripped_b, "marker_dead": tripped_c,
                "cwd_relative_read": tripped_d, "runaway": tripped_d}[kind]
    assert expected, (
        f"the planted {kind!r} defect did NOT trip its assertion — the gate "
        f"would ship this shape green. Fix the check, not the plant.")
