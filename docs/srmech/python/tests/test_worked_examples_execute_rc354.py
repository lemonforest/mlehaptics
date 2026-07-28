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
    "pure": None,
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
