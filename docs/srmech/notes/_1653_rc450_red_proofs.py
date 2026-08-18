#!/usr/bin/env python3
"""rc450 (`#T1160`, gh #1653) — THE RED PROOFS. Committed generating code.

"A gate that was never seen red is not known to work." Every gate rc450 lands
or edits is driven here into the state it exists to detect, and the observation
is written to ``_1653_rc450_red_proofs.ndjson`` beside this file.

Five proofs, each of which states WHAT WOULD MAKE IT REPORT OTHERWISE:

  P1  the BLOCKED-agreement gate, run against the PRE-SYNC (rc449) table. It
      must report exactly the drifts an independent parse found. Fewer would
      mean the gate cannot see what two parses saw, and would disqualify it.
  P2  the step-mutation exempt-set pin, against a source copy carrying a FOURTH
      name. It must red.
  P3  the ripple-manifest FROZEN floor, against a manifest copy with one
      newly-frozen entry deleted. It must red.
  P4  the value comparator, with ``_bits`` swapped for a NORMALISING encoder of
      the kind the rc444 wedge-join script already contains. Every red witness
      must stop being red — which is the proof that those witnesses are load
      bearing rather than decorative.
  P5  the planted descriptor-interior mutations, NEUTRALISED (the mutant left
      equal to the baseline). The witness must fail, proving it is the MOVEMENT
      that is asserted and not merely that two runs happened.

Run from ``docs/srmech/python`` with ``PYTHONPATH=.``::

    PYTHONPATH=. python3 ../notes/_1653_rc450_red_proofs.py \\
        --rc449-ratchet /path/to/rc449/test_c_cascade_parity_ratchet_rc446.py

``--rc449-ratchet`` is the rc449 (pre-sync) copy of the ratchet, obtained with
``git show HEAD:docs/srmech/python/tests/test_c_cascade_parity_ratchet_rc446.py``.
It is passed in rather than embedded, because an embedded literal of the old
table would be an ASSERTED baseline and this file is about measured ones. If it
is not supplied, P1 reports ``SKIPPED_NO_BASELINE`` — explicitly, never silently.

Discipline: no numpy, no stdlib fractions/math/decimal. Read-only over the tree
except for the one NDJSON it writes beside itself.
"""
from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRM = os.path.abspath(os.path.join(HERE, ".."))
PKG = os.path.join(SRM, "python")
TESTS = os.path.join(PKG, "tests")
OUT = os.path.join(HERE, "_1653_rc450_red_proofs.ndjson")

sys.path.insert(0, PKG)
sys.path.insert(0, TESTS)


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _ndjson(path, key="id"):
    rows = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("record") == "summary":
                continue
            rows[rec[key]] = rec
    assert rows, "empty parse of %s" % path
    return rows


# ── P1 — the BLOCKED-agreement gate, born red ────────────────────────────────

def p1_blocked_agreement(rc449_ratchet):
    """Apply the rc450 gate's OWN predicates to the rc449 table."""
    if not rc449_ratchet:
        return dict(proof="P1_blocked_agreement_born_red",
                    outcome="SKIPPED_NO_BASELINE",
                    detail="--rc449-ratchet not supplied; the pre-sync table "
                           "could not be measured, and an unmeasured baseline "
                           "is reported as such rather than assumed")
    old = _load(rc449_ratchet, "_rc449_ratchet_baseline")
    matrix = _ndjson(os.path.join(HERE, "_1653_gate_matrix_rc445.ndjson"),
                     key="chain")
    ledger = _ndjson(os.path.join(HERE, "_1653_gap_ledger.ndjson"))

    gate_drifts, new_type_contradictions, missing_rows = [], [], []
    for name, row in sorted(old.BLOCKED.items()):
        m = matrix.get(name)
        if m is None:
            missing_rows.append(name)
            continue
        here, there = set(row["gates"]), set(m.get("gates") or [])
        if here != there:
            gate_drifts.append(dict(chain=name, blocked=sorted(here),
                                    matrix=sorted(there)))
        cited = ledger.get(row["ledger_row"])
        if cited is None:
            missing_rows.append("%s -> %s" % (name, row["ledger_row"]))
            continue
        if bool(row["new_type"]) != bool(cited["new_type"]):
            new_type_contradictions.append(
                dict(chain=name, blocked_new_type=bool(row["new_type"]),
                     ledger_row=row["ledger_row"],
                     ledger_new_type=bool(cited["new_type"])))

    # The independently-measured expectation. Stated as a NUMBER the gate has
    # to reach, so "the gate found fewer" is a distinguishable outcome from
    # "the gate found them".
    expect_gates, expect_new_type = 3, 6
    ok = (len(gate_drifts) == expect_gates
          and len(new_type_contradictions) == expect_new_type)
    return dict(
        proof="P1_blocked_agreement_born_red",
        outcome="RED_AS_EXPECTED" if ok else "GATE_DISQUALIFIED",
        expected=dict(gate_set_drifts=expect_gates,
                      new_type_contradictions=expect_new_type),
        observed=dict(gate_set_drifts=len(gate_drifts),
                      new_type_contradictions=len(new_type_contradictions)),
        gate_drifts=gate_drifts,
        new_type_contradictions=new_type_contradictions,
        unresolvable_citations=missing_rows,
        would_report_otherwise_if=(
            "the rc449 table had agreed with the gate matrix, or the parse "
            "returned an empty population (both parsers assert non-empty), or "
            "the rc450 gate's predicates were looser than the two independent "
            "parses that found these same 3 and 6"),
        note=("NOTE ON THE 6: at rc450 only TWO rows still differ from their "
              "cited ledger row, and both carry a written new_type_reason. "
              "The other four were resolved by REPOINTING the citation "
              "(best_rational_signed -> wire_tuple_kind_absent, "
              "parallel_sector_dispatch -> carrier_mapping) or by correcting "
              "the CHAIN flag (the three step_form_map rows, which said False "
              "while citing a row that has said true all along)."))


# ── P2 — the exempt-set pin ──────────────────────────────────────────────────

def p2_exempt_pin():
    gate = _load(os.path.join(
        TESTS, "test_blocked_row_agrees_with_gate_matrix_rc450.py"),
        "_rc450_blocked_gate")
    witness = os.path.join(TESTS, "test_step_mutation_witness_rc447.py")
    src = open(witness, encoding="utf-8").read()
    live = gate._exempt_names_by_ast()

    marker = "exempt = {"
    mutated = src.replace(marker, 'exempt = {\n        "cyclic_gcd": "x",', 1)
    tree = ast.parse(mutated)
    got = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "exempt"
                for t in node.targets):
            got = frozenset(k.value for k in node.value.keys
                            if isinstance(k, ast.Constant))
            break
    reds = got is not None and got != gate.EXPECTED_EXEMPT
    return dict(
        proof="P2_exempt_set_pin_reds_on_a_fourth_name",
        outcome="RED_AS_EXPECTED" if reds else "PIN_IS_BLIND",
        live_exempt=sorted(live), pinned=sorted(gate.EXPECTED_EXEMPT),
        mutated_exempt=sorted(got) if got else None,
        would_report_otherwise_if=(
            "the extraction were by attribute access (module.exempt raises "
            "AttributeError, and a swallowed error pins the EMPTY set, which "
            "passes forever while the exemption list grows)"))


# ── P3 — the FROZEN manifest floor ───────────────────────────────────────────

def p3_frozen_floor():
    meta = _load(os.path.join(TESTS,
                              "test_ripple_manifest_covers_known_gates.py"),
                 "_rc450_manifest_meta")
    man = os.path.join(PKG, "tools", "ripple_gates.txt")
    victim = "tests/test_c_cascade_value_parity_rc450.py"
    assert victim in meta.FROZEN_KNOWN_GATES, "victim is not frozen"

    tmp = tempfile.mkdtemp(prefix="rc450_ripple_")
    try:
        scratch = os.path.join(tmp, "ripple_gates.txt")
        with open(man, encoding="utf-8") as fh:
            lines = [ln for ln in fh if ln.strip() != victim]
        with open(scratch, "w", encoding="utf-8") as fh:
            fh.writelines(lines)
        listed = {ln.strip().split("::")[0]
                  for ln in open(scratch, encoding="utf-8")
                  if ln.strip() and not ln.strip().startswith("#")}
        frozen_files = {g for g in meta.FROZEN_KNOWN_GATES
                        if "::" not in g}
        missing = sorted(frozen_files - listed)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return dict(
        proof="P3_frozen_floor_reds_on_a_deleted_entry",
        outcome="RED_AS_EXPECTED" if missing == [victim] else "FLOOR_IS_BLIND",
        deleted=victim, reported_missing=missing,
        frozen_total=len(meta.FROZEN_KNOWN_GATES),
        would_report_otherwise_if=(
            "FROZEN_KNOWN_GATES did not contain the entry, i.e. if the gate "
            "were merely LISTED and not frozen — a listed-only entry can be "
            "trimmed out of the manifest with nothing to say so"))


# ── P4 — the comparator, collapsed ───────────────────────────────────────────

def p4_collapsed_comparator():
    """Swap _bits for the normalising encoder the wedge-join script contains.

    If the red witnesses survive that swap, they were not testing the encoding
    and the whole comparator could be replaced by a collapsing one unnoticed.
    """
    gate = _load(os.path.join(TESTS, "test_c_cascade_value_parity_rc450.py"),
                 "_rc450_value_gate")
    # Captured BEFORE the swap. The first draft called ``gate._bits`` for its
    # fall-through, which — once ``gate._bits`` had been rebound to this very
    # function — recursed 991 frames deep and died. Recording that here because
    # it is the same class of mistake this file exists to catch: a reference
    # resolved at call time rather than at capture time.
    _orig_bits = gate._bits

    def collapsed(x):
        # float -> int where integral, tuple -> list, str -> its content,
        # bool -> int. Exactly the shape of notes/_1653_wedge_join_rc444.py.
        if isinstance(x, bool):
            return b"i" + repr(int(x)).encode()
        if isinstance(x, float) and x == int(x):
            return b"i" + repr(int(x)).encode()
        if isinstance(x, (tuple, list)):
            return b"[" + b",".join(collapsed(v) for v in x) + b"]"
        if isinstance(x, str):
            try:
                return b"i" + repr(int(x)).encode()
            except ValueError:
                return b"s" + x.encode()
        return _orig_bits(x)

    reds = [
        (b'{"k": "s", "v": "6"}', 6, "str -> int"),
        (b'{"k": "i", "v": "3"}', 3.0, "int -> float"),
        (b'{"items": [{"k": "i", "v": "5"}, {"k": "i", "v": "6"}], "k": "l"}',
         (5, 6), "list -> tuple"),
        (b'{"k": "i", "v": "1"}', True, "bool -> int"),
    ]
    saved = gate._bits
    survived, collapsed_away = [], []
    try:
        gate._bits = collapsed
        for wire, py, label in reds:
            v = gate.classify(0, wire, py)
            (survived if v == gate.V_DIVERGENT
             else collapsed_away).append(label)
    finally:
        gate._bits = saved

    # And confirm the SHIPPED encoder still calls them all divergent.
    still_red = [label for wire, py, label in reds
                 if gate.classify(0, wire, py) == gate.V_DIVERGENT]
    ok = not survived and len(still_red) == len(reds)
    return dict(
        proof="P4_red_witnesses_die_under_a_collapsing_encoder",
        outcome="RED_AS_EXPECTED" if ok else "WITNESSES_ARE_DECORATIVE",
        collapsed_away=collapsed_away,
        survived_the_collapse=survived,
        red_under_shipped_encoder=still_red,
        would_report_otherwise_if=(
            "the witnesses compared raw wire spellings rather than "
            "reconstructed values, in which case a collapsing VALUE encoder "
            "would not change their outcome and they would prove nothing "
            "about the encoding"))


# ── P5 — the planted mutation, neutralised ───────────────────────────────────

def p5_mutation_must_move():
    gate = _load(os.path.join(TESTS, "test_c_cascade_value_parity_rc450.py"),
                 "_rc450_value_gate2")
    from srmech.dsl._cascade_chain import cascade_chain_specs
    import copy as _copy

    out = []
    for name, apply_mut, ctx in (
        ("magnitude",
         lambda ch: ch["steps"][1]["args"].__setitem__("orientation", -1),
         {"x": -3.5}),
        ("net_chirality",
         lambda ch: ch["steps"][0].__setitem__("fold_init", -1),
         {"orientations": [-1, -1]}),
    ):
        _v, _s, entry = cascade_chain_specs(name)[0]
        base = gate._chain_only(entry)
        rc_b, wire_b, ok_b = gate._c_run(base, ctx)

        real = _copy.deepcopy(base)
        apply_mut(real)
        rc_r, wire_r, _ = gate._c_run(real, ctx)

        # NEUTRALISED: the "mutation" that changes nothing.
        neutral = _copy.deepcopy(base)
        rc_n, wire_n, _ = gate._c_run(neutral, ctx)

        out.append(dict(
            chain=name, baseline_ran=bool(ok_b and rc_b == 0),
            baseline_wire=wire_b.decode("utf-8"),
            mutant_wire=wire_r.decode("utf-8"),
            mutant_moved=wire_r != wire_b,
            neutral_wire=wire_n.decode("utf-8"),
            neutral_moved=wire_n != wire_b))

    ok = all(r["baseline_ran"] and r["mutant_moved"] and not r["neutral_moved"]
             for r in out)
    return dict(
        proof="P5_descriptor_interior_mutation_moves_the_C_output",
        outcome="RED_AS_EXPECTED" if ok else "WITNESS_IS_VACUOUS",
        rows=out,
        would_report_otherwise_if=(
            "the C run loop did not parse the step literal — a coarse "
            "compiled symbol, a cached value or a pre-seeded accumulator "
            "produces the SAME wire for base and mutant, because the mutated "
            "literal lives inside the chain document and never reaches it. "
            "Contrast the ctx-wire control (cyclic_gcd b=18->19), which such "
            "an implementation tracks perfectly and which therefore cannot "
            "serve as this witness."))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--rc449-ratchet", default=None)
    args = ap.parse_args(argv)

    proofs = [
        p1_blocked_agreement(args.rc449_ratchet),
        p2_exempt_pin(),
        p3_frozen_floor(),
        p4_collapsed_comparator(),
        p5_mutation_must_move(),
    ]
    try:
        from srmech.version import __version__ as rc
    except Exception:                                   # pragma: no cover
        rc = None

    with open(OUT, "w", encoding="utf-8") as fh:
        for p in proofs:
            p["rc"] = rc
            fh.write(json.dumps(p, sort_keys=True) + "\n")
        fh.write(json.dumps({
            "record": "summary", "rc": rc, "n_proofs": len(proofs),
            "outcomes": {p["proof"]: p["outcome"] for p in proofs},
        }, sort_keys=True) + "\n")

    print("rc450 RED PROOFS")
    print("-" * 68)
    for p in proofs:
        print("%-52s %s" % (p["proof"], p["outcome"]))
    print("-" * 68)
    print("wrote", OUT)
    bad = [p["proof"] for p in proofs
           if p["outcome"] not in ("RED_AS_EXPECTED", "SKIPPED_NO_BASELINE")]
    if bad:
        print("!! NOT PROVEN RED:", bad)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
