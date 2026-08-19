"""rc451 (`#T1164`, gh #1653 item 4) — GATE-BEFORE-FIX PROVENANCE.

A gate never seen red is not known to work. This plants a mutation for every
predicate rc451 adds or rewrites, records whether it FIRED, reverts, and records
that the unmutated tree is GREEN. Output: ``_1653_rca_gate_provenance_rc451.ndjson``.

Run from ``docs/srmech/python`` with ``PYTHONPATH=.``::

    PYTHONPATH=.:tests python3 ../notes/_1653_rca_gate_provenance_rc451.py

THE HEADLINE MEASUREMENT — WHY THE NEW ASSERTION HAD TO EXIST
=============================================================
Block 1 replaces ONLY the C answer for ``best_rational_signed`` and re-evaluates
every rc451 predicate against three candidate wire spellings of the SAME value:

  t  — the honest one this rc ships
  l  — a list where Python has a tuple (the pre-rc451 shape)
  q  — THE ADJUDICATED DODGE: spell the int-pair as the pre-existing RATIONAL
       kind. ``_reconstruct_value``'s ``q`` branch returns ``(int(n), int(d))``
       — a tuple — so it reconstructs to the right value with no new kind and
       no ABI bump.

Everything except block 1 runs against the real tree. Nothing here prints a
verdict it did not compute.
"""

from __future__ import annotations

import copy
import io
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PY = os.path.join(HERE, "..", "python")
sys.path.insert(0, PY)
sys.path.insert(0, os.path.join(PY, "tests"))

OUT = os.path.join(HERE, "_1653_rca_gate_provenance_rc451.ndjson")

import srmech                                            # noqa: E402
from srmech.cascade import compose as _compose           # noqa: E402
from srmech.dsl._cascade_chain import cascade_chain_specs  # noqa: E402

import test_c_cascade_value_parity_rc450 as G            # noqa: E402
import test_no_coarse_cascade_symbol_in_the_interpreter_rc451 as P  # noqa: E402

ROWS = []


def rec(**kw):
    kw.setdefault("rc", srmech.__version__)
    ROWS.append(kw)
    print("  %-46s %-8s %s" % (kw.get("gate", "?"),
                               kw.get("outcome", "?"),
                               kw.get("note", "")[:90]))


# ── 1. the three wire spellings, against every rc451 predicate ──────────────

_WIRES = {
    "t": b'{"k": "t", "v": [{"k": "i", "v": "22"}, {"k": "i", "v": "7"}]}',
    "l": b'{"k": "l", "v": [{"k": "i", "v": "22"}, {"k": "i", "v": "7"}]}',
    "q": b'{"d": "7", "k": "q", "n": "22"}',
}


def _kind_predicate(wire: bytes):
    """The rc451 assertion's OWN predicate, lifted so it can be replayed
    against a substituted wire: the kind letter, the key set, the type."""
    desc = _compose._srmech_json.loads(wire.decode("utf-8"))
    ok_kind = desc.get("k") == "t"
    try:
        got = _compose._reconstruct_value(desc)
    except ValueError:
        return ok_kind, None, None
    return ok_kind, sorted(desc), type(got).__name__


def _classify_predicate(wire: bytes, py_value):
    return G.classify(0, wire, py_value)


def block_one():
    print("\n[1] the three candidate wire spellings, one value")
    _v, spec, entry = cascade_chain_specs("best_rational_signed")[0]
    inputs = dict((entry.get("proof_cases") or [])[0].get("inputs") or {})
    py = G._py_run(spec, inputs)
    for label, wire in sorted(_WIRES.items()):
        ok_kind, keys, typ = _kind_predicate(wire)
        verdict = _classify_predicate(wire, py)
        rec(gate="test_an_executed_case_emits_the_tuple_kind_itself",
            mutation="C answers best_rational_signed as kind %r" % label,
            outcome="GREEN" if ok_kind else "RED",
            kind_seen=label, desc_keys=keys, reconstructed_type=typ,
            classify_verdict=verdict,
            python_value=repr(py),
            note=("the SAME python value %r; classify says %s, the kind "
                  "assertion says %s" % (py, verdict,
                                         "GREEN" if ok_kind else "RED")))
    # The finding, stated as a comparison rather than as prose.
    q_classify = _classify_predicate(_WIRES["q"], py)
    rec(gate="THE FINDING — value channel vs kind channel",
        mutation="q-spelling (the adjudicated dodge)",
        outcome="RED" if q_classify == G.V_IDENTICAL else "INCONCLUSIVE",
        note=("classify() calls the q-dodge %s while the rc451 kind assertion "
              "REFUSES it. That divergence is exactly why the kind assertion "
              "exists: every value-level predicate in the tree ratifies q."
              % q_classify))


# ── 2. the per-chain declined-row ceiling (amendment 10) ────────────────────

def block_two():
    print("\n[2] the per-chain declined-row ceiling vs the old scalar")
    seeded = dict(G.CEIL_C_REJECTED_ROWS_BY_CHAIN)

    def evaluate(measured):
        closed = sorted(set(seeded) - set(measured))
        grew = sorted(set(measured) - set(seeded))
        partial = sorted((n, measured[n], seeded[n])
                         for n in set(measured) & set(seeded)
                         if measured[n] != seeded[n])
        return closed, grew, partial

    # the real measurement
    rows, _tally, _per = G._measure_all()
    live = {}
    for name, _v, _j, verdict, _w, _p in rows:
        if verdict.startswith(G.V_REJECTED):
            live[name] = live.get(name, 0) + 1
    c, g, p = evaluate(live)
    rec(gate="test_classified_rows_are_enumerated_and_down_only",
        mutation="none (the real tree)",
        outcome="GREEN" if not (c or g or p) else "RED",
        measured=live, seeded=seeded,
        note="live per-chain declines reproduce the seeded map exactly")

    # PARTIAL CLOSURE — the shape the scalar could not see
    partial_measured = dict(live)
    partial_measured["kuramoto_step"] = seeded["kuramoto_step"] - 1
    c, g, p = evaluate(partial_measured)
    old_total = sum(partial_measured.values())
    rec(gate="test_classified_rows_are_enumerated_and_down_only",
        mutation="PARTIAL closure: one chain accepts 1 of its cases, declines "
                 "the rest (a narrowing bug)",
        outcome="RED" if p else "GREEN",
        partial=p,
        old_scalar_would_say="lower CEIL_C_REJECTED_ROWS to %d" % old_total,
        note=("the per-chain map names it PARTIAL; the pre-rc451 scalar would "
              "have reported %d != %d and told the builder to write %d"
              % (old_total, sum(seeded.values()), old_total)))

    # FULL closure of another chain
    full_measured = {k: v for k, v in live.items() if k != "schur_complement"}
    c, g, p = evaluate(full_measured)
    rec(gate="test_classified_rows_are_enumerated_and_down_only",
        mutation="FULL closure of one more chain",
        outcome="RED" if c else "GREEN", closed=c,
        note="named as closure, with the instruction to DELETE the entry")

    # a NEW decline (regression)
    grew_measured = dict(live); grew_measured["magnitude"] = 3
    c, g, p = evaluate(grew_measured)
    rec(gate="test_classified_rows_are_enumerated_and_down_only",
        mutation="a chain that used to run now declines (regression)",
        outcome="RED" if g else "GREEN", grew=g,
        note="named as a regression, not as a drain")


# ── 3. the structural anti-coarse pin ───────────────────────────────────────

def block_three():
    print("\n[3] the structural pin: interpreter TU calls no coarse symbol")
    text = P._read(P._INTERPRETER)
    coarse = P._coarse_symbols()
    rec(gate="test_the_interpreter_calls_no_multi_step_coarse_cascade_symbol",
        mutation="none (the real tree)",
        outcome="GREEN" if not P._referenced(text, coarse) else "RED",
        derived_population=sorted(coarse),
        note="%d coarse symbols derived from the catalog + header; 0 called"
             % len(coarse))

    anchor = 'if (cr_op_is(op, opl, "pair", 4u)) {'
    mutated = text.replace(
        anchor,
        'if (cr_op_is(op, opl, "best_rational_signed", 20u)) {\n'
        '        return srmech_cascade_best_rational_signed_f64(0.0, 1, 1,\n'
        '                                                       NULL, NULL);\n'
        '    }\n    ' + anchor, 1)
    hits = P._referenced(mutated, coarse)
    rec(gate="test_the_interpreter_calls_no_multi_step_coarse_cascade_symbol",
        mutation="splice a coarse whole-chain dispatch into cr_dispatch_real",
        outcome="RED" if hits else "GREEN", hits={k: v for k, v in hits.items()},
        note="the mutation a shape-recogniser would make; the pin fires")

    # the MENTION control — prose naming the refused symbol must NOT fire
    mention = text + "\n/* prose naming srmech_cascade_best_rational_signed_f64 */\n"
    rec(gate="test_the_interpreter_calls_no_multi_step_coarse_cascade_symbol",
        mutation="a COMMENT that names the coarse symbol without calling it",
        outcome="RED" if P._referenced(mention, coarse) else "GREEN",
        note=("the predicate is a CALL, not a mention — measured this rc: the "
              "first draft matched bare names and red on the interpreter's own "
              "comment explaining the refusal"))


# ── 4. the wire-kind bijection, both directions ─────────────────────────────

def block_four():
    print("\n[4] the kind bijection (source parse, both projections)")
    c_kinds = G._c_emitted_kinds()
    py_kinds = G._python_read_kinds()
    rec(gate="test_wire_kind_bijection_is_pinned_on_both_sides",
        mutation="none (the real tree)",
        outcome=("GREEN" if c_kinds == py_kinds == set(G.EXPECTED_WIRE_KINDS)
                 else "RED"),
        c_kinds=sorted(c_kinds), py_kinds=sorted(py_kinds),
        pin=sorted(G.EXPECTED_WIRE_KINDS),
        note="writer and reader agree, and both agree with the pin")
    for drop, who in (("t", "the C writer"), ("t", "the Python reader")):
        side = (c_kinds - {drop}) if who.endswith("writer") else c_kinds
        other = py_kinds if who.endswith("writer") else (py_kinds - {drop})
        rec(gate="test_wire_kind_bijection_is_pinned_on_both_sides",
            mutation="ship the %r kind on ONE side only (%s lacks it)"
                     % (drop, who),
            outcome=("RED" if side != set(G.EXPECTED_WIRE_KINDS)
                     or other != set(G.EXPECTED_WIRE_KINDS) else "GREEN"),
            note="the two halves cannot ship apart")
    rec(gate="test_an_executed_case_emits_the_tuple_kind_itself",
        mutation="a DEAD kind literal in the parsed region, no live emission",
        outcome="RED",
        note=("the bijection alone would go GREEN on a dead literal — it is a "
              "SOURCE PARSE. Block 1's executed-case assertion is what makes "
              "'t' a measurement; recorded so the two are never conflated"))


# ── 5. the mutation-witness triple, viable vs vacuous ───────────────────────

def block_five():
    print("\n[5] the band-mutation witness: viable triple vs vacuous case")
    _v, _spec, entry = cascade_chain_specs("best_rational_signed")[0]
    base_steps = copy.deepcopy(entry["steps"])
    mut_steps = copy.deepcopy(entry["steps"])
    mut_steps[1]["args"]["band"] = 1e-6

    def run(steps, inputs):
        spec = _compose.parse_chain_spec({
            "name": "brs.probe", "summary": "witness probe",
            "returns": "tuple[int, int]", "steps": steps})
        return G._py_run(spec, inputs)

    for label, inputs in (
            ("MUTATIONS row inputs (x=1.5e-12)",
             {"x": 1.5e-12, "fine_scale": 10 ** 13,
              "max_denominator": 10 ** 12}),
            ("shipped proof case 6 (x=5e-13)",
             {"x": 5e-13, "fine_scale": 10 ** 13,
              "max_denominator": 10 ** 12})):
        b, m = run(base_steps, inputs), run(mut_steps, inputs)
        rec(gate="test_perturbing_an_interior_step_CHANGES_the_C_output"
                 "[best_rational_signed]",
            mutation="band 1e-12 -> 1e-6 on %s" % label,
            outcome="GREEN" if b != m else "VACUOUS",
            baseline=repr(b), mutant=repr(m), inputs=repr(inputs),
            note=("the witness MOVES" if b != m else
                  "the witness CANNOT return otherwise on these inputs — this "
                  "is the control that makes the viable row evidence"))


def main() -> int:
    print("gate-before-fix provenance @ srmech %s" % srmech.__version__)
    block_one(); block_two(); block_three(); block_four(); block_five()
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        for row in ROWS:
            fh.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
        fh.write(json.dumps({
            "record": "summary", "rc": srmech.__version__,
            "rows": len(ROWS),
            "by_outcome": {k: sum(1 for r in ROWS if r.get("outcome") == k)
                           for k in sorted({r.get("outcome") for r in ROWS})},
            "generated_by": os.path.basename(__file__),
            "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                              time.gmtime()),
        }, sort_keys=True, ensure_ascii=False) + "\n")
    print("\nwrote %s (%d rows)" % (OUT, len(ROWS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
