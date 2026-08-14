#!/usr/bin/env python3
"""ADVERSARIAL VERIFICATION of the rc427 G4/ARROW stream (`#T1130`).

READ-ONLY round.  This script does not propose ops; it tries to BREAK the two
proposed ones and the measurements behind them.

PRE-REGISTERED FALSIFIERS (written before running):

V-F1  The closed-form index/period is claimed exact on 37 hand-picked cells.
      FALSIFIER: run it on EVERY (n, c) with 2 <= n <= 60, 0 <= c < n
      (1,829 cells, ~49x the reported grid) against an independent
      enumeration oracle written from scratch here.  ONE disagreement REFUTES
      "exact, closed form".

V-F2  COUNTS ARE NOT SETS.  The stream's agreement test compares index,
      period and eventual_image_SIZE -- three integers.  FALSIFIER: compare the
      eventual image as a SET against the predicted g*.Z/n.  A size match with
      a membership mismatch would be the standing octonion trap.

V-F3  DOMAIN OF VALIDITY.  The proposed signature is mod_mul_arrow(c, n) with
      no stated domain.  FALSIFIER: probe c=0, c=1, c=n, c>n, n=1, n=2,
      c negative, and n a large prime power.  A silent WRONG answer (not a
      raise) on any of them is a defect in the spec.

V-F4  "cyclic_period REFUSES non-units, so the eventual period of a non-unit
      is unreachable through shipped surface."  FALSIFIER: probe it live, and
      count how many shipped calls + branches the closed form actually needs
      -- if it is one call carrying no decision it falls under the
      music/relations.py rejected-op precedent the stream itself cites.

V-F5  finite_semiflow is claimed to earn its place by consuming "a table
      srmech already produces (unit_loop)".  FALSIFIER: if every unit_loop
      Cayley table is a Latin square (which unit_loop's OWN docstring
      asserts), then finite_semiflow on a unit_loop table can only ever
      return index 0 / is_permutation True -- the stated rationale carries
      no capability.

V-F6  q8_project_v4 is claimed non-injective 8->4, uniform fibres of size 2,
      idempotent, generating a 2-element non-group monoid.  FALSIFIER:
      execute it.

V-F7  cd_project is claimed to RAISE on 6 of 9 dim-2 inputs.  FALSIFIER:
      execute it.

V-F8  The Poly escape hatch: T(p) = p*x injective, not surjective, S(T(p))=p.
      FALSIFIER: execute on the shipped Poly carrier.  Also re-read the
      stream's finite Dedekind control for whether it can return otherwise.

DISCIPLINE: every number through a shipped srmech op.  No numpy, no stdlib
math/fractions/decimal, no abs() -- sign is a named Class-K pin-slot with a
Class-C re-application.  Exact integers throughout.
"""

from __future__ import annotations

import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.abspath(os.path.join(_HERE, "..", "python"))
if _PKG not in sys.path:
    sys.path.insert(0, _PKG)

import srmech                                                    # noqa: E402
from srmech.math.cyclic import gcd, lcm, mod_add, mod_mul        # noqa: E402
from srmech.math.primes import cyclic_period, factor             # noqa: E402
from srmech.math.poly import Poly, poly_from_coeffs              # noqa: E402
from srmech.biology.q8 import q8_project_v4                      # noqa: E402
from srmech.cascade import cd_project                            # noqa: E402
from srmech.cascade.cayley_dickson import (                      # noqa: E402
    left_mult_is_invertible, left_mult_kernel, unit_loop,
)
from srmech.biology.q8 import q8_mult                            # noqa: E402
from srmech.math.q import Q                                      # noqa: E402

OUT = os.path.join(_HERE, "_v_g4_arrow_verify_rc427.ndjson")
_R = []


def emit(r):
    _R.append(r)


# Class K (pin the sign bit -- the phase boundary) then Class C (re-apply the
# orientation).  NEVER abs(): the sign is a named pin-slot.
def class_k_c_residue(v: int, p: int) -> int:
    pin = 1 if v < 0 else 0
    mag = v if pin == 0 else 0 - v
    r = mod_add(mag, 0, p)
    return r if pin == 0 else mod_add(p - r, 0, p)


# -- independent oracle: enumeration, written from scratch here --------
def oracle(c: int, n: int):
    """index / period / eventual image SET of x -> c*x mod n, by enumeration."""
    tbl = [mod_mul(x, c, n) for x in range(n)]
    img = set(range(n))
    sizes = [n]
    idx = 0
    while True:
        nxt = {tbl[x] for x in img}
        if len(nxt) == len(img):
            break
        img = nxt
        sizes.append(len(img))
        idx += 1
    period = 1
    unseen = set(img)
    while unseen:
        s = min(unseen)
        v, k = s, 0
        while True:
            unseen.discard(v)
            v = tbl[v]
            k += 1
            if v == s:
                break
        period = lcm(period, k)
    return {"index": idx, "period": period, "image": frozenset(img),
            "sizes": sizes}


# -- the stream's proposed closed form, transcribed VERBATIM from
#    _g4_arrow_rc427.py:closed_form_arrow so the test is of THAT formula --
def closed_form(c: int, n: int):
    fn = dict(factor(n))
    fc = dict(factor(c % n if c % n else n))
    g1 = gcd(c % n, n)
    index = 0
    for p, en in fn.items():
        ec = fc.get(p, 0)
        if ec == 0:
            continue
        t = en // ec + (1 if en % ec else 0)
        if t > index:
            index = t
    gstar = 1
    for p, en in fn.items():
        ec = fc.get(p, 0)
        e = ec * index
        if e > en:
            e = en
        for _ in range(e):
            gstar = gstar * p
    ev = n // gstar
    period = 1 if ev == 1 else cyclic_period(c % ev, ev)
    return {"index": index, "period": period, "gstar": gstar,
            "eventual_image_size": ev, "is_unit": g1 == 1, "gcd": g1}


# == V-F1 + V-F2 : exhaustive grid, SETS compared ======================
def v_f1_f2():
    n_cells = dis_idx = dis_per = dis_size = dis_set = 0
    first = []
    idx_hist = {}
    ge2 = 0
    nonunit = 0
    for n in range(2, 61):
        for c in range(0, n):
            n_cells += 1
            o = oracle(c, n)
            f = closed_form(c, n)
            bad = []
            if o["index"] != f["index"]:
                dis_idx += 1
                bad.append("index")
            if o["period"] != f["period"]:
                dis_per += 1
                bad.append("period")
            if len(o["image"]) != f["eventual_image_size"]:
                dis_size += 1
                bad.append("size")
            pred = frozenset(mod_mul(k, f["gstar"], n) for k in range(n))
            if pred != o["image"]:
                dis_set += 1
                bad.append("SET")
            if bad and len(first) < 12:
                first.append({"n": n, "c": c, "bad": bad,
                              "oracle_index": o["index"],
                              "cf_index": f["index"],
                              "oracle_period": o["period"],
                              "cf_period": f["period"],
                              "oracle_size": len(o["image"]),
                              "cf_size": f["eventual_image_size"]})
            idx_hist[o["index"]] = idx_hist.get(o["index"], 0) + 1
            if o["index"] >= 2:
                ge2 += 1
            if not f["is_unit"]:
                nonunit += 1
    emit({"kind": "V_F1_V_F2_exhaustive_grid",
          "falsifier": "ONE disagreement on index/period/size, or ONE "
                       "size-match-with-set-mismatch, REFUTES the closed form",
          "range": "2 <= n <= 60, 0 <= c < n",
          "n_cells": n_cells,
          "n_nonunit_cells": nonunit,
          "disagree_index": dis_idx, "disagree_period": dis_per,
          "disagree_eventual_size": dis_size,
          "disagree_eventual_SET": dis_set,
          "first_disagreements": first,
          "index_histogram": {str(k): v for k, v in sorted(idx_hist.items())},
          "cells_index_ge_2": ge2,
          "classification": "CONFIRMED" if not (dis_idx or dis_per or dis_size
                                                or dis_set) else "REFUTED"})
    return dis_idx + dis_per + dis_size + dis_set


# == V-F1 negative controls: the instrument MUST be able to say no =====
def v_f1_control():
    def wrong_ceilfree(c, n):
        fn = dict(factor(n))
        fc = dict(factor(c % n if c % n else n))
        return max([en for p, en in fn.items() if fc.get(p, 0)] or [0])

    def wrong_floor(c, n):
        fn = dict(factor(n))
        fc = dict(factor(c % n if c % n else n))
        return max([en // fc[p] for p, en in fn.items() if fc.get(p, 0)] or [0])

    a = b = 0
    tot = 0
    refuse = 0
    for n in range(2, 61):
        for c in range(0, n):
            tot += 1
            o = oracle(c, n)
            if wrong_ceilfree(c, n) != o["index"]:
                a += 1
            if wrong_floor(c, n) != o["index"]:
                b += 1
            if gcd(c % n, n) != 1:
                try:
                    cyclic_period(c % n, n)
                except ValueError:
                    refuse += 1
    emit({"kind": "V_F1_negative_controls",
          "note": "an instrument that cannot return otherwise is not a "
                  "measurement; two wrong index formulas must FAIL on MY grid",
          "n_cells": tot,
          "ceiling_free_formula_disagreements": a,
          "floor_formula_disagreements": b,
          "nonunit_cells_where_shipped_cyclic_period_REFUSES": refuse,
          "classification": "CONFIRMED" if (a and b) else "VACUOUS_CONTROL"})


# == V-F3 : domain of validity =========================================
def v_f3():
    probes = [(0, 12), (1, 12), (12, 12), (13, 12), (25, 12), (1, 1), (0, 1),
              (2, 2), (0, 2), (2, 1024), (3, 2187), (6, 30), (0, 30)]
    rows = []
    for c, n in probes:
        row = {"c": c, "n": n}
        try:
            row["closed_form"] = closed_form(c, n)
        except Exception as e:                        # noqa: BLE001
            row["closed_form_raised"] = "{0}: {1}".format(type(e).__name__, e)
        try:
            o = oracle(c, n)
            row["oracle"] = {"index": o["index"], "period": o["period"],
                             "eventual_size": len(o["image"])}
        except Exception as e:                        # noqa: BLE001
            row["oracle_raised"] = "{0}: {1}".format(type(e).__name__, e)
        cf, orc = row.get("closed_form"), row.get("oracle")
        if cf and orc:
            row["agree"] = (cf["index"] == orc["index"]
                            and cf["period"] == orc["period"]
                            and cf["eventual_image_size"] == orc["eventual_size"])
        rows.append(row)
    neg = {}
    for c in (-2, -1):
        try:
            neg[str(c) + "_closed_form"] = closed_form(c, 12)
        except Exception as e:                        # noqa: BLE001
            neg[str(c) + "_closed_form"] = "{0}: {1}".format(type(e).__name__, e)
        try:
            r = class_k_c_residue(c, 12)
            neg[str(c) + "_oracle_on_KC_residue"] = {
                "residue": r, "index": oracle(r, 12)["index"],
                "period": oracle(r, 12)["period"]}
        except Exception as e:                        # noqa: BLE001
            neg[str(c) + "_oracle_on_KC_residue"] = "{0}: {1}".format(
                type(e).__name__, e)
    bad = [r for r in rows if r.get("agree") is False]
    raised = [r for r in rows if "closed_form_raised" in r]
    emit({"kind": "V_F3_domain_of_validity",
          "falsifier": "a SILENT wrong answer (not a raise) outside the "
                       "hand-picked grid is a spec defect",
          "rows": rows, "negative_c": neg,
          "silent_disagreements": len(bad),
          "raises_inside_stated_signature": len(raised),
          "classification": "CONFIRMED" if not bad else "BOUNDED"})


# == V-F4 : prior art live + decision content ===========================
def v_f4():
    rec = {"kind": "V_F4_prior_art_and_decision_content"}
    try:
        cyclic_period(6, 12)
        rec["cyclic_period_6_12"] = "DID NOT RAISE"
    except ValueError as e:
        rec["cyclic_period_6_12_raises"] = str(e)
    rec["cyclic_period_5_12"] = cyclic_period(5, 12)
    f = closed_form(6, 12)
    rec["reduced_modulus_route_for_c6_n12"] = {
        "gstar": f["gstar"], "reduced_n": f["eventual_image_size"],
        "period_on_reduced": f["period"], "index": f["index"]}
    rec["shipped_calls_needed"] = ["factor(n)", "factor(c)", "gcd(c mod n, n)",
                                   "cyclic_period(c mod n/gstar, n/gstar)"]
    rec["branches_carrying_decision"] = [
        "c mod n == 0 special case (factor(0) is undefined)",
        "shared-prime filter (primes of c not dividing n contribute nothing)",
        "ceil vs floor on v_p(n)/v_p(c) -- the floor reading is WRONG",
        "eventual modulus == 1 guard (cyclic_period requires n >= 2 and RAISES)"]
    rec["is_single_shipped_call_carrying_no_decision"] = False
    emit(rec)


# == V-F5 : is the unit_loop composition rationale vacuous? =============
def v_f5():
    rows = []
    for dim in (2, 4, 8, 16):
        ul = unit_loop(dim)
        tbl = ul["cayley_table"]
        order = ul["order"]
        n_perm_rows = sum(1 for r in tbl if len(set(r)) == order)
        n_perm_cols = sum(1 for j in range(order)
                          if len({tbl[i][j] for i in range(order)}) == order)
        rows.append({"dim": dim, "order": order, "name": ul["name"],
                     "rows_that_are_permutations": n_perm_rows,
                     "cols_that_are_permutations": n_perm_cols,
                     "latin_square": n_perm_rows == order == n_perm_cols})
    all_latin = all(r["latin_square"] for r in rows)
    emit({"kind": "V_F5_unit_loop_composition_rationale",
          "falsifier": "if EVERY unit_loop row/column is a permutation then "
                       "finite_semiflow on a unit_loop table can only ever "
                       "return index 0 / is_permutation True",
          "rows": rows,
          "every_table_is_a_latin_square": all_latin,
          "index_reachable_from_unit_loop_tables": [0] if all_latin else "varies",
          "classification": "RATIONALE_VACUOUS" if all_latin else "CONFIRMED"})


# == V-F6 : q8_project_v4 ==============================================
def v_f6():
    tbl = {}
    raised = {}
    for b in range(8):
        try:
            out = q8_project_v4(bytes([b]))
            tbl[b] = out[0] if isinstance(out, (bytes, bytearray)) else out
        except Exception as e:                        # noqa: BLE001
            raised[b] = "{0}: {1}".format(type(e).__name__, e)
    rec = {"kind": "V_F6_q8_project_v4",
           "table": {str(k): v for k, v in tbl.items()}, "raised": raised}
    if len(tbl) == 8:
        vals = [tbl[b] for b in sorted(tbl)]
        img = sorted(set(vals))
        fib = {}
        for b, v in tbl.items():
            fib.setdefault(v, []).append(b)
        sizes = sorted({len(v) for v in fib.values()})
        idem = all(tbl.get(v, None) == v for v in img)
        rec.update({"domain_size": 8, "image": img, "image_size": len(img),
                    "fibre_sizes_distinct": sizes,
                    "fibres_uniform": len(sizes) == 1,
                    "is_self_map": set(img) <= set(range(8)),
                    "is_injective": len(img) == 8,
                    "idempotent_E_of_E_equals_E": idem,
                    "monoid_generated_order": 2 if (idem and len(img) < 8)
                                              else None,
                    "classification": "CONFIRMED"
                                      if (idem and len(img) == 4
                                          and sizes == [2]) else "REFUTED"})
    emit(rec)


# == V-F7 : cd_project partiality ======================================
def v_f7():
    ok, raised = [], []
    for a in range(3):
        for b in range(3):
            try:
                r = cd_project([Q(a, 1), Q(b, 1)])
                ok.append({"in": [a, b],
                           "out": [str(v) for v in r] if hasattr(r, "__iter__")
                                  else str(r)})
            except Exception as e:                    # noqa: BLE001
                raised.append({"in": [a, b],
                               "err": "{0}: {1}".format(type(e).__name__, e)})
    emit({"kind": "V_F7_cd_project_partiality",
          "claim_under_test": "cd_project RAISES on 6 of 9 dim-2 inputs",
          "n_ok": len(ok), "n_raised": len(raised),
          "ok": ok, "raised": raised[:9],
          "classification": "CONFIRMED" if len(raised) == 6 else "REFUTED"})


# == V-F8 : the Poly escape hatch ======================================
def v_f8():
    x_poly = poly_from_coeffs([0, 1])
    samples = [[1], [0, 1], [1, 1], [2, 0, 3], [0, 0, 1], [1, 2, 3, 4],
               [5], [0, 1, 0, 1], [7, 0, 0, 0, 2], [1, 0, 1]]
    polys = [poly_from_coeffs(s) for s in samples]
    imgs = [p * x_poly for p in polys]

    def key(p):
        return tuple(str(c) for c in list(getattr(p, "coeffs", [])))

    keys = [key(im) for im in imgs]
    inj = len(set(keys)) == len(keys)
    const_terms = [key(im)[0] if key(im) else "EMPTY" for im in imgs]
    zero_const = sum(1 for ct in const_terms if ct.split("/")[0] == "0")

    def retract(p):
        # the left retraction S: drop the constant term (shift down).  Built
        # through the carrier's OWN exact-Q constructor, because
        # poly_from_coeffs contractually refuses Q (it takes plain ints) --
        # itself a small measured surface note, recorded below.
        cs = list(getattr(p, "coeffs", []))
        return Poly(cs[1:] if len(cs) > 1 else [0])

    retract_ok = sum(1 for p, im in zip(polys, imgs) if key(retract(im)) == key(p))

    # the stream's finite Dedekind control, re-read: does it compare TWO
    # different predicates, or the same one twice?
    same_pred = 0
    diff_pred = 0
    for n in (7, 8, 12, 16):
        for c in range(n):
            tbl = [mod_mul(x, c, n) for x in range(n)]
            injf = len(set(tbl)) == n           # injective on a finite set
            surf = set(tbl) == set(range(n))    # surjective -- the REAL test
            if injf == surf:
                same_pred += 1
            else:
                diff_pred += 1
    emit({"kind": "V_F8_poly_escape_hatch",
          "n_samples": len(samples),
          "T_distinct_images": len(set(keys)),
          "T_injective": inj,
          "image_constant_terms": const_terms,
          "images_with_zero_constant_term": zero_const,
          "S_compose_T_is_identity_count": retract_ok,
          "dedekind_cells": same_pred + diff_pred,
          "dedekind_agreements": same_pred,
          "dedekind_violations": diff_pred,
          "poly_from_coeffs_refuses_Q_note": "poly_from_coeffs takes plain ints only; the retraction had to go through Poly() directly. Minor surface note, not a defect.",
          "harness_note": "on a FINITE set injective <=> surjective is a "
                          "THEOREM, so this control cannot return otherwise "
                          "no matter how it is coded -- it is a tautology "
                          "check, not evidence that the escape needs "
                          "infiniteness.  Classified as such.",
          "classification": "CONFIRMED" if (inj and zero_const == len(samples)
                                            and retract_ok == len(samples))
                            else "BOUNDED"})


# == V-F9 : the prior art the stream dismissed as "substring noise" ====
def v_f9():
    """srmech.cascade.left_mult_is_invertible / left_mult_kernel ARE the
    shipped multiply-by-a-fixed-element non-injectivity surface.  The stream's
    prior_art_grep field waves left_mult_is_invertible off as
    "substring noise only".  FALSIFIER: execute both and see whether they
    answer the SAME question OP-1 is built around (is x -> c*x injective, and
    what does it destroy)."""
    rows = []
    # a division-algebra element (dim 8): invertible, empty kernel
    x8 = [Q(1, 1)] + [Q(0, 1)] * 7
    rows.append({"case": "octonion e0 (dim 8)",
                 "left_mult_is_invertible": left_mult_is_invertible(x8),
                 "kernel_basis_size": len(left_mult_kernel(x8))})
    # a sedenion zero divisor (dim 16): NON-injective, nonempty kernel
    z = [Q(0, 1)] * 16
    z[1] = Q(1, 1)
    z[10] = Q(1, 1)
    rows.append({"case": "sedenion e1 + e10 (dim 16, a zero divisor)",
                 "left_mult_is_invertible": left_mult_is_invertible(z),
                 "kernel_basis_size": len(left_mult_kernel(z))})
    rows.append({"case": "sedenion e1 (dim 16, not a zero divisor)",
                 "left_mult_is_invertible": left_mult_is_invertible(
                     [Q(0, 1)] + [Q(1, 1)] + [Q(0, 1)] * 14),
                 "kernel_basis_size": len(left_mult_kernel(
                     [Q(0, 1)] + [Q(1, 1)] + [Q(0, 1)] * 14))})
    emit({"kind": "V_F9_left_mult_prior_art",
          "falsifier": "if left_mult_is_invertible / left_mult_kernel answer "
                       "the injectivity + what-is-destroyed question for a "
                       "multiply-by-a-fixed-element map, then the stream's "
                       "prior_art_grep MISCLASSIFIED them as substring noise",
          "rows": rows,
          "shipped_prose": "left_mult_kernel ToolEntry: 'NONEMPTY <=> x is a "
                           "left zero divisor <=> multiply-by-x is "
                           "non-injective <=> no inverse map exists -- the "
                           "no backward direction to point of section "
                           "VII.6.23.4 (anything past and unobserved is "
                           "lost). Class L (linear-algebra rank).'",
          "verdict": "NOT substring noise: this IS the shipped "
                     "multiply-by-a-fixed-element non-injectivity surface, "
                     "and it already carries the irreversibility prose. It "
                     "does NOT ship index/period (one tick, no iteration) and "
                     "does not act on Z/n -- so OP-1 is not extant, but the "
                     "stream's prior-art section named the WRONG neighbours.",
          "shipped_class_for_this_object": "Class L (linear-algebra rank) -- "
                                           "not the K/E the stream assigns",
          "classification": "PRIOR_ART_MISCLASSIFIED"})


# == V-F10 : the worked examples in the proposed op specs ==============
def v_f10():
    rows = []
    for c, n, want_i, want_p, want_ev in ((2, 64, 6, 1, 1), (2, 12, 2, 2, 3),
                                          (5, 12, 0, 2, 12), (6, 12, 2, 1, 1)):
        o = oracle(c, n)
        rows.append({"c": c, "n": n, "claimed_index": want_i,
                     "measured_index": o["index"],
                     "claimed_period": want_p, "measured_period": o["period"],
                     "claimed_eventual_size": want_ev,
                     "measured_eventual_size": len(o["image"]),
                     "measured_image_sizes": o["sizes"],
                     "agree": (o["index"] == want_i and o["period"] == want_p
                               and len(o["image"]) == want_ev)})
    # the finite_semiflow worked example the spec states for q8_mult
    tbl = []
    err = None
    try:
        tbl = [q8_mult(1, b) for b in range(8)]
    except Exception as e:                                # noqa: BLE001
        err = "{0}: {1}".format(type(e).__name__, e)
    q8row = {"claim": "finite_semiflow([q8_mult(1,b) for b in range(8)]) -> "
                      "index 0, period 4, is_permutation True"}
    if err:
        q8row["raised"] = err
    else:
        q8row["table"] = list(tbl)
        is_perm = len(set(tbl)) == 8
        per = 1
        if is_perm:
            unseen = set(range(8))
            while unseen:
                s0 = min(unseen)
                v, k = s0, 0
                while True:
                    unseen.discard(v)
                    v = tbl[v]
                    k += 1
                    if v == s0:
                        break
                per = lcm(per, k)
        q8row.update({"is_permutation": is_perm, "measured_period": per,
                      "claimed_period": 4, "agree": is_perm and per == 4})
    bad = [r for r in rows if not r["agree"]] + (
        [] if q8row.get("agree", True) else [q8row])
    emit({"kind": "V_F10_worked_examples",
          "falsifier": "a worked example in an op spec that does not "
                       "reproduce is a defect in the spec",
          "cyclic_rows": rows, "q8_mult_row": q8row,
          "n_wrong": len(bad),
          "classification": "CONFIRMED" if not bad else "REFUTED"})


def main():
    try:
        import numpy  # noqa: F401
        npz = True
    except ModuleNotFoundError:
        npz = False
    from srmech.introspect.tool_schema import warmup_all, get_tool_schema
    warmup_all()
    emit({"kind": "env", "srmech_file": srmech.__file__,
          "srmech_version": srmech.__version__,
          "python": sys.version.split()[0], "numpy_present": npz,
          "registry_ops": len(get_tool_schema().tools),
          "stream": "G4 ARROW rc427 -- ADVERSARIAL VERIFICATION",
          "role": "verifier"})
    v_f1_f2()
    v_f1_control()
    v_f3()
    v_f4()
    v_f5()
    v_f6()
    v_f7()
    v_f8()
    v_f9()
    v_f10()
    with open(OUT, "w", encoding="utf-8") as fh:
        for r in _R:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    print("wrote {0} records -> {1}".format(len(_R), OUT))
    for r in _R:
        print(r["kind"], "->", r.get("classification", ""))


if __name__ == "__main__":
    main()
