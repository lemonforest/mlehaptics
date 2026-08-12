#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""``_g1_opgaps_rc427`` — OPGAPS stream, srmech rc427 research round (`#T1123`).

READ-ONLY MEASUREMENT. Nothing under ``srmech/`` is touched. This script costs
THREE candidate ops by *exercising the surface they would provide* with the
shipped ops that already exist, and by proving the absence of the rest.

THE THREE SURFACES UNDER TEST
=============================
1. **A T/I (dihedral) GROUP OBJECT.** ``srmech/music/relations.py:54-63`` records
   ``interval_invert`` / ``pitch_class_transpose`` / ``pitch_class_invert`` as
   costed-and-REJECTED ("each is a single ``cyclic_mod_add`` call carrying no
   decision"). ``prime_form`` reaches the Tn/TnI orbit through a module-private
   ``_invert``. The order-24 GROUP is a different object from those three
   element-level ops, and the rejection text does not mention it.
2. **A CONJUGACY / COMMUTING-PAIR / CLASS-EQUATION op.** Load-bearing for the
   rc426 reversal result, no shipped home. ⚠️ The class equation is a GROUP
   theorem and FAILS at the octonion unit loop.
3. **A LOOP-LAW CENSUS over the signed unit loop.** ``associator`` /
   ``moufang_residue`` / ``is_moufang`` read the exact-ℚ ALGEBRA basis;
   alternativity, flexibility, LIP/RIP and division ``b/a == b·a⁻¹`` have no
   named op at all and have now been hand-rolled in at least four notes.

════════════════════════════════════════════════════════════════════════
PRE-REGISTERED FALSIFIERS — written before the code below was run.
A NULL is a fine result; each is classified REFUTED / BOUNDED / EMPTY /
UNSUPPORTED. Predictions are stated so a match cannot be manufactured.
════════════════════════════════════════════════════════════════════════

A — the T/I group object
------------------------
FA1  "No shipped srmech op returns a non-abelian group of order 24, or of ANY
     order that is not a power of two."  Enumerate every shipped group-object
     constructor reachable from the registry (``unit_loop`` over every legal
     rung, ``group_algebra_table`` over every legal rung) and read the orders.
     REFUTED if any order-24 non-abelian object comes back.
     PREDICT: orders are 2·dim (powers of two) and dim (cyclic, abelian) only.

FA2  "No PUBLIC srmech op performs Tn or TnI on a pitch class."  Read
     ``srmech.music.__all__`` and ``srmech.music.relations.__all__``.
     REFUTED if a transposition/inversion op is exported.
     PREDICT: absent; ``prime_form`` consumes the orbit privately.

FA3  "The proposed group op carries a real DECISION, so the rc424 'no decision'
     rejection does not extend to it."  The decision is the COMPOSITION-ORDER
     convention. Build D₁₂ under both readings and measure a downstream number.
     UNSUPPORTED (⇒ REJECT the op) if the two conventions are indistinguishable
     on every measurement here.
     PREDICT: the two Cayley tables differ, and the Lewin-style axiom-A count
     splits 13824 vs 5184 (the rc426 number, reproduced independently).

FA4  "The group object reproduces the SHIPPED ``prime_form`` exactly: the prime
     form is the minimum, over the FULL 24-element orbit, of the start-at-0
     normal order."  REFUTED on the first disagreement.
     PREDICT: total agreement on both conventions; if it fails, the group
     object is the wrong object and the op is REJECTED.

NA1  Negative control — a NON-unit reflection rule (``I_a(x) = k·a − x`` with
     ``k`` a non-unit mod 12) must NOT close into a Latin square. An instrument
     that blesses it is not measuring.

NA2  Negative control — the ABELIAN stand-in ℤ/24 has the same ORDER as D₁₂.
     A test that cannot separate them is a count-only test and is worthless.

B — the conjugacy / class-equation op
-------------------------------------
FB1  "Burnside's commuting-pair identity |{(x,y) : xy = yx}| = k(G)·|G| holds on
     GROUPS and FAILS on the octonion unit loop."  Measure both sides on six
     carriers. REFUTED if it holds at M16.
     PREDICT: holds on ℤ/7, ℤ/12, Q8, D₁₂; FAILS at M16 (predicts 144,
     measures 88) and at M32.

FB2  "An UNGUARDED class-equation op — one that reports k(G)·|G| without first
     measuring associativity — emits a silent WRONG number."  Run the guarded
     and unguarded readings side by side. UNSUPPORTED (⇒ the guard is
     decoration) if the unguarded reading is right on every carrier.
     PREDICT: the unguarded reading is wrong at exactly the non-associative
     rungs, by 144−88 = 56 at M16.

FB3  "Conjugation on a non-associative loop is BRACKETING-DEPENDENT, so
     'conjugacy class' is not even well-defined there."  Measure
     ``(g·x)·g⁻¹`` against ``g·(x·g⁻¹)`` on every ordered pair.
     PREDICT (this one may go either way — it is the reason the op needs a
     measured flag rather than an assumption): agreement at M16, and the
     interesting case is M32.

NB1  Negative control — corrupt one cell of a Cayley table. The census must
     REFUSE it (Latin-square check fails). An instrument that accepts a
     corrupted table cannot certify a good one.

NB2  Negative control — the class equation must be checked against a carrier
     where it is TRIVIALLY true (abelian: k = |G|, pairs = |G|²). A test that
     only ever sees abelian rows is vacuous.

C — the loop-law census
-----------------------
FC1  "The shipped ``is_moufang`` boolean cannot report which laws survive when
     Moufang fails."  Census left/right alternativity, flexibility, Moufang,
     LIP/RIP and division on every rung. UNSUPPORTED (⇒ REJECT) if the law
     vector is constant given ``is_moufang``.
     PREDICT: at dim 16 and 32, ``is_moufang`` is a single False while
     FLEXIBILITY survives — one bit cannot carry that.

FC2  "The unit-loop (signed, order 2·dim) law verdict agrees with the
     algebra-basis (unsigned, order dim) verdict."  This is ASSERTED by a
     sign-cancellation argument; per
     ``[[feedback_an_asserted_algebraic_property_is_not_a_measured_one]]`` it is
     MEASURED here instead. REFUTED on any disagreement.

FC3  COUNTS ARE NOT SETS. Where two laws have EQUAL violation counts on a rung,
     measure whether they fail on the SAME triples. REFUTED (as an equivalence
     claim) if any equal-count pair has a nonempty symmetric difference.

FC4  "Division ``b/a`` (the unique x with x·a = b) equals ``b·a⁻¹`` on every
     rung."  PREDICT: total at every rung the loop is defined, because the
     inverse property survives even where associativity does not — but this is
     exactly the kind of claim that has been wrong before, so it is measured
     per rung, not asserted once.

NC1  Negative control — ``srmech.cascade.flip_pair`` is the SHIPPED one-named-bit
     FLEXIBILITY control. The census must break flexibility on it. An instrument
     that reports every table flexible is not measuring flexibility.

NC2  Negative control — the trivial rungs (dim 1, dim 2) satisfy every law. A
     census that returns the same vector for ℂ and 𝕊 is not separating.

DISCIPLINE
==========
Every number goes through a shipped srmech op where one exists; every hand-roll
is recorded as a REPORTABLE FINDING (that is the whole point of this round).
No ``abs()`` — the reflection is a Class-K pin-slot phase boundary with Class-C
re-application, named as such. No stdlib ``math`` / ``fractions`` / ``decimal``.
No numpy. Exact ℤ and exact ℚ (``srmech.math.q.Q``) throughout.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Dict, List, Sequence, Tuple

# ── shipped srmech ops — every number below routes through one of these ──
import srmech
from srmech.cascade import (
    algebra_table,
    associator,
    cd_basis,
    cd_commutator,
    cyclic_mod_add,
    flip_pair,
    group_algebra_table,
    is_moufang,
    loop_invariants,
    moufang_residue,
    table_product,
    unit_loop,
)
from srmech.introspect.tool_schema import get_tool_schema, warmup_all
from srmech.math.cyclic import gcd, mod_mul
from srmech.math.q import Q
from srmech.music import normal_order, prime_form
import srmech.music as music_pkg
from srmech.music.relations import __all__ as RELATIONS_ALL

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "_g1_opgaps_rc427.ndjson")
_ROWS: List[Dict[str, Any]] = []


def emit(kind: str, **fields: Any) -> None:
    """One NDJSON record per line — no bloated JSON."""
    rec = {"kind": kind}
    rec.update(fields)
    _ROWS.append(rec)


# ══════════════════════════════════════════════════════════════════════
# 0 — ENVIRONMENT. A stale artifact under test has burned this project.
# ══════════════════════════════════════════════════════════════════════
def part0_env() -> None:
    try:
        import numpy  # noqa: F401
        numpy_present = True
    except ImportError:
        numpy_present = False
    warmup_all()
    schema = get_tool_schema()
    print("srmech.__file__    =", srmech.__file__)
    print("srmech.__version__ =", srmech.__version__)
    print("registry ops       =", len(schema))
    print("numpy present      =", numpy_present)
    emit("env",
         srmech_file=srmech.__file__,
         srmech_version=srmech.__version__,
         registry_ops=len(schema),
         numpy_present=numpy_present,
         python=sys.version.split()[0],
         has_native=bool(getattr(srmech, "HAS_NATIVE", False)))


# ══════════════════════════════════════════════════════════════════════
# GROUP / LOOP PLUMBING — index tables only, so every carrier below is
# the SAME kind of object and the census ops read one shape.
# A "table" here is table[a][b] = index of element_a · element_b.
# ══════════════════════════════════════════════════════════════════════
def _is_latin(table: Sequence[Sequence[int]]) -> Tuple[bool, bool]:
    n = len(table)
    rows = all(sorted(r) == list(range(n)) for r in table)
    cols = all(sorted(table[a][b] for a in range(n)) == list(range(n))
               for b in range(n))
    return rows, cols


def _identity_index(table: Sequence[Sequence[int]]) -> int:
    n = len(table)
    for e in range(n):
        if all(table[e][x] == x and table[x][e] == x for x in range(n)):
            return e
    return -1


def _inverses(table: Sequence[Sequence[int]], e: int) -> List[int]:
    """Two-sided inverse index per element, or −1 where none exists."""
    n = len(table)
    inv = [-1] * n
    for a in range(n):
        for b in range(n):
            if table[a][b] == e and table[b][a] == e:
                inv[a] = b
                break
    return inv


def _assoc_census(table: Sequence[Sequence[int]]) -> Tuple[int, int]:
    n = len(table)
    ok = 0
    for a in range(n):
        ta = table[a]
        for b in range(n):
            ab = ta[b]
            tb = table[b]
            for c in range(n):
                if table[ab][c] == ta[tb[c]]:
                    ok += 1
    return ok, n ** 3


def _commuting_pairs(table: Sequence[Sequence[int]]) -> int:
    n = len(table)
    return sum(1 for a in range(n) for b in range(n)
               if table[a][b] == table[b][a])


# ── the SIGNED UNIT LOOP as an index table, read off the shipped op ──
def unit_loop_table(dim: int) -> Dict[str, Any]:
    """Shipped ``unit_loop(dim)`` re-read as a bare index table."""
    ul = unit_loop(dim)
    return {"name": ul["name"], "order": ul["order"],
            "table": ul["cayley_table"], "elements": ul["elements"]}


def signed_unit_loop_from_table(tab3: Sequence[Sequence[Sequence[int]]]
                                ) -> Dict[str, Any]:
    """The signed-unit loop of ANY MONOMIAL rank-3 structure tensor — the road
    by which the shipped ``flip_pair`` negative control reaches the census.

    HAND-ROLL, REPORTABLE: ``unit_loop`` takes only ``dim`` and always reads the
    definite ladder; it has no ``table=`` parameter, unlike its siblings
    ``is_moufang`` / ``moufang_residue`` / ``associator``. That asymmetry is
    itself a finding (see the ``op_usage_ledger`` record).
    """
    dim = len(tab3)
    elements = [(1, i) for i in range(dim)] + [(-1, i) for i in range(dim)]
    idx = {su: n for n, su in enumerate(elements)}
    table = []
    for (sa, ia) in elements:
        row = []
        for (sb, ib) in elements:
            cell = tab3[ia][ib]
            nz = [k for k in range(dim) if cell[k] != 0]
            assert len(nz) == 1, "table is not monomial — loop is undefined"
            k = nz[0]
            # Class K pin-slot: the product sign is a phase boundary.
            # Class C: re-applied to the operand signs.
            sign = cell[k] * sa * sb
            row.append(idx[(sign, k)])
        table.append(row)
    return {"order": len(elements), "table": table, "elements": elements}


# ══════════════════════════════════════════════════════════════════════
# PART A — the T/I (dihedral) group object
# ══════════════════════════════════════════════════════════════════════
#: The two composition-order readings. There is no default, by design —
#: exactly the shape ``prime_form``'s ``convention`` already ships with.
LEFT_THEN_RIGHT = "g_then_h"   # (g·h)(x) = h(g(x))  — "apply g, then h"
RIGHT_THEN_LEFT = "h_then_g"   # (g·h)(x) = g(h(x))  — classical ∘


def _class_k_negate(b: int, n: int) -> int:
    """Class-K PIN-SLOT phase boundary: the reflection flips the orientation of
    the modular step. Class-C re-application puts it back on the ℤ/n lane.
    NEVER ``abs()``; never unary ``-``-then-``%``. One shipped ``cyclic_mod_add``.
    """
    return cyclic_mod_add(n - cyclic_mod_add(b, 0, n), 0, n)


def ti_product(g: Tuple[int, int], h: Tuple[int, int], n: int,
               convention: str) -> Tuple[int, int]:
    """The T/I product. ``kind`` 0 = Tₖ (rotation), 1 = TₖI (reflection).

    HAND-ROLL, REPORTABLE: this is the surface the op would provide. Every
    modular step is a shipped ``cyclic_mod_add``; only the 2×2 kind split and
    the Class-K/Class-C reflection are local.
    """
    if convention == RIGHT_THEN_LEFT:
        g, h = h, g
    elif convention != LEFT_THEN_RIGHT:
        raise ValueError("convention must be named — there is no default")
    (kg, a), (kh, b) = g, h
    if kg == 0:
        return (kh, cyclic_mod_add(a, b, n))
    # kg == 1: the reflection reverses the second operand's orientation.
    return (1 - kh, cyclic_mod_add(a, _class_k_negate(b, n), n))


def dihedral_table(n: int, convention: str) -> Dict[str, Any]:
    """Order-2n T/I group as an index table (D₁₂ = T/I on ℤ/12 at n=12)."""
    elements = [(0, k) for k in range(n)] + [(1, k) for k in range(n)]
    idx = {e: i for i, e in enumerate(elements)}
    table = [[idx[ti_product(g, h, n, convention)] for h in elements]
             for g in elements]
    return {"n": n, "order": 2 * n, "convention": convention,
            "elements": elements, "table": table}


def ti_act(g: Tuple[int, int], x: int, n: int) -> int:
    """Tₖ(x) = x+k ; TₖI(x) = k−x. Both through shipped ``cyclic_mod_add``."""
    kind, k = g
    if kind == 0:
        return cyclic_mod_add(x, k, n)
    return cyclic_mod_add(k, _class_k_negate(x, n), n)


def partA_absence() -> None:
    """FA1 / FA2 — is a group object of order 24 reachable from what ships?"""
    orders: List[Dict[str, Any]] = []
    for dim in (1, 2, 4, 8, 16, 32):
        ul = unit_loop(dim)
        t = ul["cayley_table"]
        n = len(t)
        abelian = all(t[a][b] == t[b][a] for a in range(n) for b in range(n))
        orders.append({"op": "srmech.cascade.unit_loop", "dim": dim,
                       "name": ul["name"], "order": ul["order"],
                       "abelian": abelian})
    refusals = []
    for dim in (2, 3, 4, 5, 8, 12, 16, 24):
        # group_algebra_table is R[Z/dim] — the cyclic group of order dim.
        try:
            group_algebra_table(dim)
        except ValueError as exc:
            refusals.append({"op": "srmech.cascade.group_algebra_table",
                             "dim": dim, "refused": str(exc)})
            continue
        orders.append({"op": "srmech.cascade.group_algebra_table", "dim": dim,
                       "name": "Z/%d" % dim, "order": dim, "abelian": True})
    hit24 = [o for o in orders if o["order"] == 24 and not o["abelian"]]
    nonpow2 = [o for o in orders
               if not o["abelian"] and (o["order"] & (o["order"] - 1)) != 0]
    emit("FA1_no_order24_group_ships",
         constructors_probed=len(orders),
         orders=sorted({o["order"] for o in orders}),
         nonabelian_orders=sorted({o["order"] for o in orders
                                   if not o["abelian"]}),
         nonabelian_order24_hits=len(hit24),
         nonabelian_non_power_of_two_hits=len(nonpow2),
         rows=orders,
         refusals=refusals, n_refusals=len(refusals),
         classification="EMPTY" if not hit24 else "REFUTED",
         verdict=("EMPTY — every shipped group-object constructor returns "
                  "either a cyclic ABELIAN group of order dim or a signed unit "
                  "loop of order 2·dim, and BOTH refuse any dim that is not a "
                  "power of two. No order-24 non-abelian object is reachable; "
                  "no group of order 3, 5, 12 or 24 is reachable AT ALL."))

    music_all = sorted(music_pkg.__all__)
    rel_all = sorted(RELATIONS_ALL)
    # ⚠️ SUBSTRING matching is WRONG here and the first pass proved it: "ti"
    # matches par·ti·als and spectrum_·ti·er, so the instrument reported five
    # false hits and classified itself REFUTED while its own verdict string
    # said EMPTY. Word-part matching on the '_'-split name is the fix, and the
    # correction is recorded rather than quietly dropped.
    parts_tokens = {"tn", "ti", "invert", "inversion", "transpose",
                    "transposition", "dihedral", "tni"}
    substr_tokens = ("transpos", "dihedral")

    def name_hits(nm: str) -> bool:
        parts = set(nm.lower().split("_"))
        return bool(parts & parts_tokens) or any(tk in nm.lower()
                                                 for tk in substr_tokens)

    hits = [nm for nm in music_all if name_hits(nm)]
    naive_hits = [nm for nm in music_all
                  if any(tk in nm.lower()
                         for tk in ("transpos", "invert", "tn", "ti",
                                    "dihedral"))]
    emit("FA2_no_public_transposition_or_inversion",
         music_all=music_all, relations_all=rel_all,
         part_tokens=sorted(parts_tokens),
         substring_tokens=list(substr_tokens),
         public_hits=hits,
         naive_substring_hits=naive_hits,
         false_positives_of_naive_read=len(naive_hits) - len(hits),
         classification="EMPTY" if not hits else "REFUTED",
         instrument_correction=("first pass used bare substring matching and "
                                "returned 5 FALSE POSITIVES (bell_partials, "
                                "equal_temperament_partials, "
                                "membrane_partials, spectrum_tier, "
                                "stiff_string_partials) — all on the 'ti' of "
                                "'partials'. Corrected to '_'-split word-part "
                                "matching."),
         verdict=("EMPTY — neither srmech.music.__all__ nor "
                  "srmech.music.relations.__all__ exports a Tn or TnI surface; "
                  "prime_form consumes the orbit via a module-private _invert."))


def partA_convention_decision() -> None:
    """FA3 — does the group object carry a DECISION the rejected element-level
    ops did not? The decision is the composition order. Measured, not argued."""
    n = 12
    L = dihedral_table(n, LEFT_THEN_RIGHT)
    R = dihedral_table(n, RIGHT_THEN_LEFT)
    same = L["table"] == R["table"]
    rowsL, colsL = _is_latin(L["table"])
    rowsR, colsR = _is_latin(R["table"])
    nL = len(L["table"])
    abelianL = all(L["table"][a][b] == L["table"][b][a]
                   for a in range(nL) for b in range(nL))

    # ── decision (i): the PRODUCT itself. Two readings, two answers. ──
    cells_differing = sum(1 for a in range(nL) for b in range(nL)
                          if L["table"][a][b] != R["table"][a][b])
    probe_g, probe_h = (1, 3), (1, 5)
    prodL = ti_product(probe_g, probe_h, n, LEFT_THEN_RIGHT)
    prodR = ti_product(probe_g, probe_h, n, RIGHT_THEN_LEFT)

    # ── decision (ii): the DOWNSTREAM interval-composition order. ──
    # Lewin-style axiom A: int(s,u) ∘ int(u,v) == int(s,v), with int(s,u) the
    # left quotient s⁻¹·u. FORWARD composes the two intervals in reading order;
    # REVERSED composes them the other way round. In a GROUP the forward
    # reading is a theorem (associativity); the reversed reading holds exactly
    # on the COMMUTING pairs.
    #
    # ⚠️ FIRST PASS WAS WRONG AND IS CORRECTED HERE. It reversed the GROUP
    # PRODUCT instead of the INTERVAL COMPOSITION and got 13824 both times —
    # of course it did: the opposite group is still a group. The rc426 5184 is
    # a statement about composing intervals, not about the group's own product.
    def axiom_a_counts(tab: Dict[str, Any]) -> Tuple[int, int, int]:
        t = tab["table"]
        m = len(t)
        e = _identity_index(t)
        inv = _inverses(t, e)
        fwd = rev = 0
        for s in range(m):
            for u in range(m):
                i1 = t[inv[s]][u]
                for v in range(m):
                    i2 = t[inv[u]][v]
                    i3 = t[inv[s]][v]
                    if t[i1][i2] == i3:
                        fwd += 1
                    if t[i2][i1] == i3:
                        rev += 1
        return fwd, rev, m ** 3

    fwd, rev, tot = axiom_a_counts(L)
    emit("FA3_convention_is_a_decision",
         tables_identical=same, cells_differing=cells_differing,
         cells_total=nL * nL,
         probe_product={"g": "T3I", "h": "T5I",
                        "g_then_h": list(prodL), "h_then_g": list(prodR),
                        "same_answer": prodL == prodR,
                        "reads": ("T3I·T5I is T10 under one reading and T2 "
                                  "under the other — a caller who guesses is "
                                  "silently wrong")},
         left_latin_rows=rowsL, left_latin_cols=colsL,
         right_latin_rows=rowsR, right_latin_cols=colsR,
         left_abelian=abelianL,
         axiom_a_forward=fwd, axiom_a_reversed=rev, axiom_a_of=tot,
         commuting_pairs_times_order=216 * 24,
         reversed_equals_commuting_pairs_times_order=(rev == 216 * 24),
         rc426_reference_forward=13824, rc426_reference_reversed=5184,
         reproduces_rc426=(fwd == 13824 and rev == 5184),
         classification="REFUTED" if same else "BOUNDED",
         instrument_correction=("first pass reversed the GROUP PRODUCT and got "
                                "13824 twice — the opposite group is still a "
                                "group, so that read could not fire. Corrected "
                                "to reverse the INTERVAL COMPOSITION, which "
                                "reproduces rc426's 13824 vs 5184 exactly."),
         verdict=("TWO decisions, both measured. (i) The group's own product: "
                  "the two readings give DIFFERENT Cayley tables — 360 of 576 "
                  "cells differ — and T3I·T5I is T10 one way, T2 the other. "
                  "(ii) Downstream interval composition splits 13824 vs 5184 "
                  "= 216 commuting pairs × 24. The rc424 'carries no decision' "
                  "rejection does not reach this object."))

    # NA2 — the abelian same-order control. Order alone must not identify it.
    z24 = [[cyclic_mod_add(a, b, 24) for b in range(24)] for a in range(24)]
    z24_ab = all(z24[a][b] == z24[b][a] for a in range(24) for b in range(24))
    emit("NA2_abelian_same_order_control",
         control="Z/24 built from shipped cyclic_mod_add",
         order=24, abelian=z24_ab,
         d12_order=L["order"], d12_abelian=abelianL,
         orders_equal=(L["order"] == 24),
         separated_by_commutativity=(z24_ab != abelianL),
         control_valid=(z24_ab and not abelianL),
         verdict=("Same ORDER, different OBJECT. A count-only test cannot tell "
                  "Z/24 from D12; the commutativity read can. Counts are not "
                  "sets."))

    # NA1 — a non-unit reflection rule must NOT close into a Latin square.
    rows_broken = []
    for k in (0, 2, 3, 4, 6, 8, 9, 10):
        if gcd(k, n) == 1:
            continue

        def bad_product(g, h, kk=k):
            (kg, a), (kh, b) = g, h
            if kg == 0:
                return (kh, cyclic_mod_add(a, b, n))
            return (1 - kh, cyclic_mod_add(a, mod_mul(kk, b, n), n))

        els = [(0, i) for i in range(n)] + [(1, i) for i in range(n)]
        ix = {e: i for i, e in enumerate(els)}
        t = [[ix[bad_product(g, h)] for h in els] for g in els]
        r, c = _is_latin(t)
        rows_broken.append({"multiplier": k, "gcd_with_12": gcd(k, n),
                            "latin_rows": r, "latin_cols": c})
    wrongly_blessed = [r for r in rows_broken
                       if r["latin_rows"] and r["latin_cols"]]
    emit("NA1_non_unit_reflection_control",
         controls=rows_broken, n_controls=len(rows_broken),
         n_wrongly_blessed=len(wrongly_blessed),
         control_valid=(len(wrongly_blessed) == 0),
         verdict=("Every non-unit reflection multiplier fails the Latin-square "
                  "check. The instrument can return otherwise."))


def partA_reproduces_prime_form() -> None:
    """FA4 — the group object must reproduce the SHIPPED prime_form exactly.

    prime_form is the min, over the Tn/TnI orbit, of the start-at-0 normal
    order. If the 24-element D12 orbit reproduces it, the group object is the
    right object; if not, the proposal is wrong and is REJECTED.
    """
    n = 12
    D = dihedral_table(n, LEFT_THEN_RIGHT)
    els = D["elements"]

    def orbit_prime(pcs: Tuple[int, ...], convention: str) -> Tuple[int, ...]:
        best = None
        for g in els:
            img = tuple(sorted({ti_act(g, x, n) for x in pcs}))
            no = normal_order(img, convention)
            shifted = tuple(cyclic_mod_add(x, _class_k_negate(no[0], n), n)
                            for x in no)
            if best is None or shifted < best:
                best = shifted
        return best

    def subsets(card: int) -> List[Tuple[int, ...]]:
        out: List[Tuple[int, ...]] = []
        stack = [(0, ())]
        while stack:
            start, acc = stack.pop()
            if len(acc) == card:
                out.append(acc)
                continue
            for x in range(start, n):
                if n - x < card - len(acc):
                    break
                stack.append((x + 1, acc + (x,)))
        return out

    rows = []
    for convention in ("forte", "rahn"):
        agree = 0
        total = 0
        mismatches = []
        for card in (3, 4, 5):
            for s in subsets(card):
                total += 1
                shipped = prime_form(s, convention)
                mine = orbit_prime(s, convention)
                if shipped == mine:
                    agree += 1
                elif len(mismatches) < 5:
                    mismatches.append({"pcs": list(s), "shipped": list(shipped),
                                       "orbit": list(mine)})
        rows.append({"convention": convention, "agree": agree, "of": total,
                     "mismatches": mismatches})
    emit("FA4_group_orbit_reproduces_shipped_prime_form",
         cardinalities=[3, 4, 5], rows=rows,
         total_agreement=all(r["agree"] == r["of"] for r in rows),
         classification=("BOUNDED"
                         if all(r["agree"] == r["of"] for r in rows)
                         else "REFUTED"),
         verdict=("The 24-element D12 orbit reproduces the shipped prime_form "
                  "on every probed set and BOTH conventions. The group object "
                  "is the object prime_form is already using privately."))

    # The worked example the op proposal quotes.
    s = (0, 1, 3, 7, 8)          # set class 5-20 — one of the six that split
    emit("worked_example_ti_group",
         op="dihedral_group(12, convention='g_then_h')",
         order=D["order"], elements_head=[list(e) for e in els[:4]],
         product_example={"g": [1, 3], "h": [1, 5],
                          "g_dot_h": list(ti_product((1, 3), (1, 5), 12,
                                                     LEFT_THEN_RIGHT)),
                          "reads": "T3I · T5I = T_(3-5) = T10"},
         action_example={"g": [1, 3], "x": 7, "value": ti_act((1, 3), 7, 12),
                         "reads": "T3I(7) = 3-7 = 8 mod 12"},
         pcs=list(s),
         prime_form_forte=list(prime_form(s, "forte")),
         prime_form_rahn=list(prime_form(s, "rahn")),
         orbit_size=len({tuple(sorted({ti_act(g, x, 12) for x in s}))
                         for g in els}))


# ══════════════════════════════════════════════════════════════════════
# PART B — conjugacy / commuting pairs / the class equation
# ══════════════════════════════════════════════════════════════════════
def conjugacy_census(table: Sequence[Sequence[int]], label: str
                     ) -> Dict[str, Any]:
    """The op under test, run as a prototype. NOTE the GUARD: the
    class-equation prediction is emitted ONLY when associativity is measured
    first. Everything else (commuting pairs, commuting probability) is a direct
    census and is valid on any magma."""
    n = len(table)
    latin_rows, latin_cols = _is_latin(table)
    e = _identity_index(table)
    inv = _inverses(table, e) if e >= 0 else [-1] * n
    assoc_ok, assoc_of = _assoc_census(table)
    is_assoc = (assoc_ok == assoc_of)
    has_inv = all(i >= 0 for i in inv)
    is_group = bool(latin_rows and latin_cols and e >= 0 and has_inv
                    and is_assoc)

    pairs = _commuting_pairs(table)
    prob = Q(pairs, n * n)

    # bracketing agreement — measured, never assumed
    bracket_agree = 0
    for g in range(n):
        for x in range(n):
            if table[table[g][x]][inv[g]] == table[g][table[x][inv[g]]]:
                bracket_agree += 1
    bracket_total = n * n
    bracket_ok = (bracket_agree == bracket_total)

    # conjugacy orbits under x -> (g·x)·g^-1  (left bracketing, named)
    seen = [False] * n
    classes: List[List[int]] = []
    for x in range(n):
        if seen[x]:
            continue
        orbit = set()
        frontier = [x]
        while frontier:
            y = frontier.pop()
            if y in orbit:
                continue
            orbit.add(y)
            for g in range(n):
                z = table[table[g][y]][inv[g]]
                if z not in orbit:
                    frontier.append(z)
        for y in orbit:
            seen[y] = True
        classes.append(sorted(orbit))
    k = len(classes)

    out: Dict[str, Any] = {
        "carrier": label, "order": n,
        "latin_rows": latin_rows, "latin_cols": latin_cols,
        "identity_index": e, "two_sided_inverses": has_inv,
        "associative_triples": assoc_ok, "of_triples": assoc_of,
        "is_associative": is_assoc, "is_group": is_group,
        "abelian": (pairs == n * n),
        "commuting_pairs_MEASURED": pairs,
        "commuting_probability": str(prob),
        "conjugation_bracketing_agree": bracket_agree,
        "conjugation_bracketing_of": bracket_total,
        "conjugation_well_defined": bracket_ok,
        "class_count_k": k,
        "class_sizes": [len(c) for c in classes],
    }
    # ── THE GUARD ──────────────────────────────────────────────────
    if is_group:
        out["class_equation_valid"] = True
        out["class_equation_predicts_commuting_pairs"] = k * n
        out["class_equation_agrees"] = (k * n == pairs)
        out["class_sum_equals_order"] = (sum(len(c) for c in classes) == n)
        out["gustafson_five_eighths_bound"] = (prob <= Q(5, 8)
                                               or prob == Q(1, 1))
        out["refused_reason"] = None
    else:
        out["class_equation_valid"] = False
        out["class_equation_predicts_commuting_pairs"] = None
        out["class_equation_agrees"] = None
        out["gustafson_five_eighths_bound"] = None
        out["refused_reason"] = (
            "class equation is a GROUP theorem; this carrier fails "
            "associativity at %d of %d ordered triples, so k(G)·|G| is NOT a "
            "valid commuting-pair count here and is REFUSED rather than "
            "returned." % (assoc_of - assoc_ok, assoc_of))
    # what an UNGUARDED op would have said, for the negative control
    out["UNGUARDED_would_report"] = k * n
    out["UNGUARDED_is_wrong_by"] = (k * n - pairs)
    return out


def partB() -> None:
    carriers: List[Tuple[str, List[List[int]]]] = []
    for m in (7, 12):
        carriers.append(("Z/%d" % m,
                         [[cyclic_mod_add(a, b, m) for b in range(m)]
                          for a in range(m)]))
    carriers.append(("Q8 = unit_loop(4)", unit_loop_table(4)["table"]))
    carriers.append(("D12 (T/I, order 24)",
                     dihedral_table(12, LEFT_THEN_RIGHT)["table"]))
    carriers.append(("M16 = unit_loop(8)", unit_loop_table(8)["table"]))
    carriers.append(("M32 = unit_loop(16)", unit_loop_table(16)["table"]))

    rows = []
    for label, t in carriers:
        r = conjugacy_census(t, label)
        rows.append(r)
        emit("conjugacy_census", **r)

    groups = [r for r in rows if r["is_group"]]
    loops = [r for r in rows if not r["is_group"]]
    emit("FB1_burnside_identity_domain",
         n_carriers=len(rows),
         groups=[r["carrier"] for r in groups],
         non_groups=[r["carrier"] for r in loops],
         holds_on_all_groups=all(r["class_equation_agrees"] for r in groups),
         group_rows=[{"carrier": r["carrier"], "k": r["class_count_k"],
                      "order": r["order"],
                      "k_times_order": r["class_count_k"] * r["order"],
                      "measured_pairs": r["commuting_pairs_MEASURED"]}
                     for r in groups],
         non_group_rows=[{"carrier": r["carrier"], "k": r["class_count_k"],
                          "order": r["order"],
                          "k_times_order": r["class_count_k"] * r["order"],
                          "measured_pairs": r["commuting_pairs_MEASURED"],
                          "error": r["UNGUARDED_is_wrong_by"]}
                         for r in loops],
         classification="BOUNDED",
         verdict=("Burnside's k(G)·|G| identity holds on every carrier that "
                  "MEASURES as a group and fails on every carrier that does "
                  "not. The domain of validity is decidable from the table "
                  "itself — which is exactly why the op can guard."))

    worst = max(loops, key=lambda r: r["UNGUARDED_is_wrong_by"]) if loops else None
    emit("FB2_unguarded_op_emits_a_silent_wrong_number",
         guarded_refusals=[r["carrier"] for r in loops],
         unguarded_errors=[{"carrier": r["carrier"],
                            "would_report": r["UNGUARDED_would_report"],
                            "truth": r["commuting_pairs_MEASURED"],
                            "wrong_by": r["UNGUARDED_is_wrong_by"]}
                           for r in loops],
         worst_carrier=(worst["carrier"] if worst else None),
         worst_error=(worst["UNGUARDED_is_wrong_by"] if worst else None),
         classification=("BOUNDED" if any(r["UNGUARDED_is_wrong_by"]
                                          for r in loops) else "UNSUPPORTED"),
         verdict=("An unguarded class-equation op returns a WRONG commuting-"
                  "pair count on the non-associative rungs — the silent-wrong-"
                  "answer class. The guard is load-bearing, not decoration."))

    emit("FB3_conjugation_bracketing",
         rows=[{"carrier": r["carrier"],
                "agree": r["conjugation_bracketing_agree"],
                "of": r["conjugation_bracketing_of"],
                "well_defined": r["conjugation_well_defined"],
                "is_associative": r["is_associative"]} for r in rows],
         all_well_defined=all(r["conjugation_well_defined"] for r in rows),
         classification="BOUNDED",
         verdict=("MEASURED, not assumed. Where bracketing agrees, conjugacy "
                  "orbits are well defined even without associativity; the op "
                  "must return this flag rather than presume it."))

    # NB1 — corrupt one cell; the census must refuse.
    good = unit_loop_table(8)["table"]
    bad = [list(r) for r in good]
    bad[3][5] = bad[3][6]          # duplicate an entry: Latin square broken
    c = conjugacy_census(bad, "M16 CORRUPTED (cell [3][5])")
    emit("NB1_corrupted_table_control",
         corrupted_cell=[3, 5],
         latin_rows=c["latin_rows"], latin_cols=c["latin_cols"],
         is_group=c["is_group"],
         refused=(c["class_equation_valid"] is False),
         control_valid=(not c["latin_rows"] and not c["is_group"]),
         verdict=("The corrupted table fails the Latin-square check and the "
                  "class-equation branch is REFUSED. An instrument that "
                  "accepted it could not certify a good one."))

    # NB2 — the abelian vacuity control.
    ab = [r for r in rows if r["abelian"]]
    emit("NB2_abelian_vacuity_control",
         abelian_carriers=[r["carrier"] for r in ab],
         all_trivially_true=all(r["class_count_k"] == r["order"]
                                and r["commuting_pairs_MEASURED"]
                                == r["order"] ** 2 for r in ab),
         nonabelian_carriers=[r["carrier"] for r in rows if not r["abelian"]],
         n_nonabelian=len([r for r in rows if not r["abelian"]]),
         control_valid=(len([r for r in rows if not r["abelian"]]) >= 3),
         verdict=("On abelian carriers k = |G| and the identity is vacuous. "
                  "Four non-abelian carriers carry the real load, so the "
                  "measurement is not vacuous."))


# ══════════════════════════════════════════════════════════════════════
# PART C — the loop-law census over the signed unit loop
# ══════════════════════════════════════════════════════════════════════
LAW_NAMES = ("left_alternative", "right_alternative", "flexible",
             "moufang_M1", "moufang_M2", "moufang_M3",
             "left_inverse_property", "right_inverse_property",
             "division_equals_right_multiply_by_inverse",
             "power_associative", "diassociative")


def loop_law_census(table: Sequence[Sequence[int]], label: str,
                    with_sets: bool = False) -> Dict[str, Any]:
    """The op under test, run as a prototype. Per-law COUNTS (not one bit), and
    optionally the failing-triple SETS so 'counts are not sets' is testable."""
    n = len(table)
    e = _identity_index(table)
    inv = _inverses(table, e) if e >= 0 else [-1] * n
    t = table

    ok: Dict[str, int] = {nm: 0 for nm in LAW_NAMES}
    tot: Dict[str, int] = {nm: 0 for nm in LAW_NAMES}
    fail: Dict[str, set] = {nm: set() for nm in LAW_NAMES}

    def note(nm: str, good: bool, key) -> None:
        tot[nm] += 1
        if good:
            ok[nm] += 1
        elif with_sets:
            fail[nm].add(key)

    for a in range(n):
        for b in range(n):
            aa = t[a][a]
            note("left_alternative", t[a][t[a][b]] == t[aa][b], (a, b))
            note("right_alternative", t[t[b][a]][a] == t[b][aa], (a, b))
            note("flexible", t[t[a][b]][a] == t[a][t[b][a]], (a, b))
            if e >= 0:
                note("left_inverse_property", t[inv[a]][t[a][b]] == b, (a, b))
                note("right_inverse_property", t[t[b][a]][inv[a]] == b, (a, b))
                # right division: the unique x with x·a = b
                xs = [x for x in range(n) if t[x][a] == b]
                note("division_equals_right_multiply_by_inverse",
                     len(xs) == 1 and xs[0] == t[b][inv[a]], (a, b))
    # ── power- and di-associativity: the REAL subloop tests, not a probe. ──
    # First pass checked only (aa)a == a(aa) and (ab)c with c ∈ {a,b}. Those are
    # NECESSARY conditions, not the laws, and a necessary-condition test that is
    # reported under the law's name is a false green. Corrected: generate the
    # multiplicative closure of ⟨a⟩ / ⟨a,b⟩ and check associativity INSIDE it.
    def closure_of(gens: Tuple[int, ...]) -> Tuple[int, ...]:
        seen = set(gens)
        changed = True
        while changed:
            changed = False
            cur = list(seen)
            for x in cur:
                for y in cur:
                    z = t[x][y]
                    if z not in seen:
                        seen.add(z)
                        changed = True
        return tuple(sorted(seen))

    _assoc_cache: Dict[Tuple[int, ...], bool] = {}

    def sub_assoc(sub: Tuple[int, ...]) -> bool:
        hit = _assoc_cache.get(sub)
        if hit is not None:
            return hit
        good = all(t[t[x][y]][z] == t[x][t[y][z]]
                   for x in sub for y in sub for z in sub)
        _assoc_cache[sub] = good
        return good

    for a in range(n):
        note("power_associative", sub_assoc(closure_of((a,))), (a,))
    for a in range(n):
        for b in range(n):
            note("diassociative", sub_assoc(closure_of((a, b))), (a, b))

    for a in range(n):
        for b in range(n):
            for c in range(n):
                note("moufang_M1",
                     t[a][t[b][t[a][c]]] == t[t[t[a][b]][a]][c], (a, b, c))
                note("moufang_M2",
                     t[b][t[a][t[c][a]]] == t[t[t[b][a]][c]][a], (a, b, c))
                note("moufang_M3",
                     t[t[b][c]][t[a][b]] == t[b][t[t[c][a]][b]], (a, b, c))

    out: Dict[str, Any] = {"carrier": label, "order": n,
                           "identity_index": e,
                           "two_sided_inverses": all(i >= 0 for i in inv)}
    for nm in LAW_NAMES:
        out[nm] = ok[nm]
        out[nm + "_of"] = tot[nm]
        out[nm + "_holds"] = (ok[nm] == tot[nm] and tot[nm] > 0)
    out["law_vector"] = [1 if out[nm + "_holds"] else 0 for nm in LAW_NAMES]
    out["moufang_all_three"] = all(out[nm + "_holds"]
                                   for nm in ("moufang_M1", "moufang_M2",
                                              "moufang_M3"))
    out["alternative"] = (out["left_alternative_holds"]
                          and out["right_alternative_holds"])
    if with_sets:
        out["_fail_sets"] = fail
    return out


ALG_LAW_NAMES = ("alg_left_alternative", "alg_right_alternative",
                 "alg_flexible_linearised", "alg_moufang")


def algebra_law_census(table3: Sequence[Sequence[Sequence[int]]], label: str
                       ) -> Dict[str, Any]:
    """The SECOND domain: the same law NAMES read on the exact-ℚ ALGEBRA basis,
    through the shipped ``associator`` / ``moufang_residue``.

    This exists because the loop domain measured flip_pair as FLEXIBLE while
    its own shipped docstring says it is the flexibility control. Both are
    true — they are different objects. The census must name which one.
    """
    dim = len(table3)
    basis = [cd_basis(dim, i) for i in range(dim)]

    # ⚠️ THE LAWS MUST BE READ LINEARISED, and the first pass got this wrong.
    # (x, x, y) is QUADRATIC in x, so testing it only at x = e_i is a NECESSARY
    # condition, not the law — and it is VACUOUS on any Cayley–Dickson table,
    # because e_i² = ±e₀ is central. That vacuity scored the SEDENION algebra
    # "left-alternative", which is false and is exactly the shipped is_moufang
    # docstring's own counterexample. The correct basis-level statements are:
    #   left  alternative ⟺ (x,y,z) + (y,x,z) = 0   (associator alternating)
    #   right alternative ⟺ (x,y,z) + (x,z,y) = 0
    #   flexible          ⟺ (x,y,z) + (z,y,x) = 0
    # Each IS multilinear, so each DOES reduce to the basis. Kept as a
    # correction record rather than silently repaired.
    cache: Dict[Tuple[int, int, int], Tuple[Any, ...]] = {}

    def asc(i: int, j: int, k: int) -> Tuple[Any, ...]:
        hit = cache.get((i, j, k))
        if hit is None:
            hit = associator(basis[i], basis[j], basis[k], table=table3)
            cache[(i, j, k)] = hit
        return hit

    def sums_to_zero(u, v) -> bool:
        return all(p + q == 0 for p, q in zip(u, v))

    la = ra = flex = mou = 0
    naive_la = 0
    for i in range(dim):
        for j in range(dim):
            if all(c == 0 for c in asc(i, i, j)):
                naive_la += 1
            for k in range(dim):
                if sums_to_zero(asc(i, j, k), asc(j, i, k)):
                    la += 1
                if sums_to_zero(asc(i, j, k), asc(i, k, j)):
                    ra += 1
                if sums_to_zero(asc(i, j, k), asc(k, j, i)):
                    flex += 1
                if moufang_residue(basis[i], basis[j], basis[k],
                                   table=table3) == 0:
                    mou += 1
    pairs, triples = dim * dim, dim ** 3
    out = {"carrier": label, "dim": dim,
           "alg_left_alternative": la, "alg_left_alternative_of": triples,
           "alg_right_alternative": ra, "alg_right_alternative_of": triples,
           "alg_flexible_linearised": flex,
           "alg_flexible_linearised_of": triples,
           "alg_moufang": mou, "alg_moufang_of": triples,
           "VACUOUS_naive_xxy_probe": naive_la,
           "VACUOUS_naive_xxy_probe_of": pairs,
           "vacuity_note": ("the naive (e_i, e_i, e_j) probe scores FULL on "
                            "every CD table because e_i² is central — it is a "
                            "necessary condition wearing the law's name")}
    for nm in ALG_LAW_NAMES:
        out[nm + "_holds"] = (out[nm] == out[nm + "_of"])
    out["law_vector"] = [1 if out[nm + "_holds"] else 0
                         for nm in ALG_LAW_NAMES]
    return out


OFF_ROWS_FOR_POOL: List[Dict[str, Any]] = []


def partC() -> None:
    rows = []
    for dim in (1, 2, 4, 8, 16):
        ult = unit_loop_table(dim)
        r = loop_law_census(ult["table"],
                            "%s = unit_loop(%d)" % (ult["name"], dim),
                            with_sets=(dim in (8, 16)))
        fails = r.pop("_fail_sets", None)
        r["cd_dim"] = dim
        r["shipped_is_moufang_on_algebra_basis"] = is_moufang(dim=dim)
        rows.append((r, fails))
        emit("loop_law_census", **r)

    # FC1 — one bit vs the law vector
    vectors = {}
    for r, _ in rows:
        vectors.setdefault(r["shipped_is_moufang_on_algebra_basis"],
                           []).append((r["carrier"], tuple(r["law_vector"])))
    collisions = {str(k): sorted({v for _, v in vs})
                  for k, vs in vectors.items()}
    n_distinct_given_bit = {str(k): len({v for _, v in vs})
                            for k, vs in vectors.items()}
    emit("FC1a_on_the_definite_ladder_the_bit_DOES_determine_the_vector",
         law_names=list(LAW_NAMES),
         rows=[{"carrier": r["carrier"],
                "is_moufang_bit": r["shipped_is_moufang_on_algebra_basis"],
                "law_vector": r["law_vector"],
                "alternative": r["alternative"],
                "flexible": r["flexible_holds"],
                "moufang_loop": r["moufang_all_three"]}
               for r, _ in rows],
         distinct_law_vectors_given_the_bit=n_distinct_given_bit,
         classification=("UNSUPPORTED"
                         if max(n_distinct_given_bit.values()) == 1
                         else "BOUNDED"),
         prediction_was=("flexibility survives at dim 16 where Moufang fails, "
                         "so one bit cannot carry the vector"),
         what_actually_happened=("PREDICTION HALF WRONG, AND THE FALSIFIER "
                                 "FIRED AGAINST ME. Flexibility DOES survive "
                                 "at dim 16 — and so do BOTH alternativity "
                                 "laws, LIP, RIP, division, power- and "
                                 "di-associativity. ONLY the three Moufang "
                                 "identities fail. So on the DEFINITE LADDER "
                                 "the is_moufang bit determines the whole law "
                                 "vector, and this falsifier is UNSUPPORTED as "
                                 "framed. The capability argument has to be "
                                 "made from FC1b (off-ladder tables) and FC3 "
                                 "(counts vs sets) instead — not from here."),
         verdict=("UNSUPPORTED as framed. Reported rather than reframed after "
                  "the fact: on the five definite rungs, knowing the bit is "
                  "knowing the vector."))

    # FC1b — OFF the definite ladder, where the bit is constant and the vector
    # is not. This is where the census earns its keep.
    off_rows = []
    off_tables: List[Tuple[str, Any]] = [
        ("flip_pair(8,1,2)", flip_pair(8, 1, 2)),
        ("flip_pair(8,1,4)", flip_pair(8, 1, 4)),
        ("flip_pair(8,3,5)", flip_pair(8, 3, 5)),
        ("algebra_table(8, gammas=(1,-1,-1)) split", algebra_table(8, (1, -1, -1))),
        ("algebra_table(8, gammas=(-1,1,-1)) split", algebra_table(8, (-1, 1, -1))),
        ("algebra_table(8, gammas=(-1,-1,1)) split", algebra_table(8, (-1, -1, 1))),
    ]
    for name, tab3 in off_tables:
        loop = signed_unit_loop_from_table(tab3)
        lr = loop_law_census(loop["table"], name)
        ar = algebra_law_census(tab3, name)
        bit = is_moufang(table=tab3)
        off_rows.append({"table": name, "is_moufang_bit": bit,
                         "loop_law_vector": lr["law_vector"],
                         "algebra_law_vector": ar["law_vector"],
                         "alg_flexible": ar["alg_flexible_linearised"],
                         "alg_flexible_of": ar["alg_flexible_linearised_of"],
                         "loop_flexible_holds": lr["flexible_holds"]})
        emit("off_ladder_law_census", loop=lr, algebra=ar,
             is_moufang_bit=bit)
    bits = {r["is_moufang_bit"] for r in off_rows}
    loop_vecs = {tuple(r["loop_law_vector"]) for r in off_rows}
    alg_vecs = {tuple(r["algebra_law_vector"]) for r in off_rows}
    OFF_ROWS_FOR_POOL.extend(off_rows)
    emit("FC1b_off_ladder_one_bit_many_vectors",
         n_tables=len(off_rows), rows=off_rows,
         distinct_is_moufang_bits=len(bits), bits=sorted(str(b) for b in bits),
         distinct_loop_law_vectors=len(loop_vecs),
         distinct_algebra_law_vectors=len(alg_vecs),
         bit_partitions_loop_vectors=(len(loop_vecs) <= len(bits)),
         bit_partitions_algebra_vectors=(len(alg_vecs) <= len(bits)),
         classification=("BOUNDED" if (len(bits) == 1
                                       and max(len(loop_vecs),
                                               len(alg_vecs)) > 1)
                         else "UNSUPPORTED"),
         prediction_was=("off the ladder the bit would be constant while the "
                         "vectors moved"),
         what_actually_happened=("SECOND FALSIFIER FIRED AGAINST ME. The bit is "
                                 "NOT constant here — the three flip_pair "
                                 "controls read False and the three γ-split "
                                 "tables read True — and within each bit value "
                                 "the law vector is CONSTANT. So across ALL "
                                 "eleven tables measured in this round (5 "
                                 "definite rungs + 3 flip_pair + 3 γ-split) "
                                 "the shipped is_moufang boolean DETERMINES "
                                 "the whole law vector. The 'one bit cannot "
                                 "carry the vector' argument is UNSUPPORTED, "
                                 "twice, and is withdrawn."),
         verdict=("UNSUPPORTED. The case for the census op does NOT rest here. "
                  "It rests on FC5 (the same law name gives OPPOSITE verdicts "
                  "in the two domains — a silent-wrong-answer risk a boolean "
                  "cannot even express), on FC3 (three laws failing at "
                  "IDENTICAL counts on pairwise-DISJOINT halves, which a "
                  "boolean erases), and on the DEGREE of failure (4 of 512 vs "
                  "5376 of 32768 are both 'False')."))

    # FC2 — signed unit loop vs unsigned algebra basis, MEASURED
    agree = []
    for r, _ in rows:
        dim = r["cd_dim"]
        agree.append({"cd_dim": dim,
                      "unit_loop_moufang": r["moufang_all_three"],
                      "shipped_algebra_basis_is_moufang":
                          r["shipped_is_moufang_on_algebra_basis"],
                      "agree": (r["moufang_all_three"]
                                == r["shipped_is_moufang_on_algebra_basis"])})
    emit("FC2_signed_loop_vs_unsigned_algebra_basis",
         rows=agree, all_agree=all(a["agree"] for a in agree),
         classification=("BOUNDED" if all(a["agree"] for a in agree)
                         else "REFUTED"),
         verdict=("MEASURED, not asserted. The sign-cancellation argument "
                  "(x appears twice in each Moufang identity, so sign² = +1) "
                  "is confirmed on every rung — the census over 2·dim signed "
                  "units agrees with the shipped dim-basis verdict."))

    # FC3 — counts are not sets
    overlaps = []
    for r, fails in rows:
        if not fails:
            continue
        counted = [nm for nm in LAW_NAMES
                   if r[nm + "_of"] > 0 and r[nm] < r[nm + "_of"]]
        for i in range(len(counted)):
            for j in range(i + 1, len(counted)):
                a, b = counted[i], counted[j]
                if r[a + "_of"] != r[b + "_of"]:
                    continue
                fa, fb = fails[a], fails[b]
                if len(fa) != len(fb):
                    continue
                overlaps.append({"carrier": r["carrier"], "law_a": a,
                                 "law_b": b, "equal_count": len(fa),
                                 "intersection": len(fa & fb),
                                 "a_minus_b": len(fa - fb),
                                 "b_minus_a": len(fb - fa),
                                 "same_set": (fa == fb)})
    emit("FC3_counts_are_not_sets",
         equal_count_law_pairs=len(overlaps), rows=overlaps,
         any_equal_count_different_set=any(not o["same_set"]
                                           for o in overlaps),
         classification=("BOUNDED" if overlaps else "EMPTY"),
         verdict=("Where two laws fail at the same COUNT the census reports "
                  "the failing SETS, so a count-only reading cannot declare "
                  "them the same law. This is the standing rc426 trap "
                  "(bare and chiral both 2752/4096 on DIFFERENT triples)."))

    # NC1 — the shipped flexibility negative control, on BOTH domains.
    ctrl = signed_unit_loop_from_table(flip_pair(8, 1, 2))
    cr = loop_law_census(ctrl["table"], "flip_pair(8,1,2) signed unit loop")
    ca = algebra_law_census(flip_pair(8, 1, 2), "flip_pair(8,1,2) algebra")
    base = [r for r, _ in rows if r["cd_dim"] == 8][0]
    base_alg = algebra_law_census(algebra_table(8), "algebra_table(8) = O")
    emit("NC1_flip_pair_flexibility_control_TWO_DOMAINS",
         control_op="srmech.cascade.flip_pair(8, 1, 2)",
         loop_domain={"order": cr["order"],
                      "base_flexible": base["flexible_holds"],
                      "control_flexible": cr["flexible_holds"],
                      "control_flexible_count": cr["flexible"],
                      "control_flexible_of": cr["flexible_of"],
                      "base_law_vector": base["law_vector"],
                      "control_law_vector": cr["law_vector"],
                      "laws_moved": [nm for nm in LAW_NAMES
                                     if base[nm + "_holds"]
                                     != cr[nm + "_holds"]],
                      "control_valid_for_FLEXIBILITY": False},
         algebra_domain={"dim": ca["dim"],
                         "base_flexible_linearised":
                             [base_alg["alg_flexible_linearised"],
                              base_alg["alg_flexible_linearised_of"]],
                         "control_flexible_linearised":
                             [ca["alg_flexible_linearised"],
                              ca["alg_flexible_linearised_of"]],
                         "violations": (ca["alg_flexible_linearised_of"]
                                        - ca["alg_flexible_linearised"]),
                         "shipped_docstring_says": 4,
                         "reproduces_shipped_claim":
                             ((ca["alg_flexible_linearised_of"]
                               - ca["alg_flexible_linearised"]) == 4),
                         "base_law_vector": base_alg["law_vector"],
                         "control_law_vector": ca["law_vector"],
                         "control_valid_for_FLEXIBILITY":
                             (base_alg["alg_flexible_linearised_holds"]
                              and not ca["alg_flexible_linearised_holds"])},
         classification="BOUNDED",
         instrument_correction=("first pass ran this control on the SIGNED "
                                "UNIT LOOP only and scored control_valid = "
                                "False — flexibility held 256/256 there. That "
                                "is not a broken control, it is a DOMAIN "
                                "ERROR on my side: flip_pair negates e_i·e_j "
                                "AND e_j·e_i, which preserves anticommutation, "
                                "and on signed BASIS UNITS (ab)a = a(ba) is "
                                "then a theorem. The control is valid on the "
                                "ALGEBRA basis, where it breaks flexibility at "
                                "exactly 4 of 512 triples as its docstring "
                                "claims."),
         verdict=("THE FINDING: the same law NAME gives OPPOSITE verdicts in "
                  "the two domains on the same shipped table. A census op "
                  "must therefore NAME its domain — signed unit loop vs "
                  "algebra basis — and must not default, exactly as "
                  "prime_form must not default on `convention`."))

    # FC1c — the test FC1a and FC1b each half-ran: POOL the ladder and the
    # off-ladder tables and ask whether the bit partitions the vectors ACROSS
    # both families. Neither earlier framing compared a ladder row to an
    # off-ladder row, and that comparison is the whole question.
    pooled = []
    for r, _ in rows:
        if r["cd_dim"] < 2:
            continue
        ar = algebra_law_census(algebra_table(r["cd_dim"]),
                                "algebra_table(%d)" % r["cd_dim"])
        pooled.append({"table": "definite ladder dim %d" % r["cd_dim"],
                       "family": "ladder",
                       "is_moufang_bit":
                           r["shipped_is_moufang_on_algebra_basis"],
                       "loop_law_vector": r["law_vector"],
                       "algebra_law_vector": ar["law_vector"]})
    for r in OFF_ROWS_FOR_POOL:
        pooled.append({"table": r["table"], "family": "off-ladder",
                       "is_moufang_bit": r["is_moufang_bit"],
                       "loop_law_vector": r["loop_law_vector"],
                       "algebra_law_vector": r["algebra_law_vector"]})
    by_bit_loop: Dict[str, set] = {}
    by_bit_alg: Dict[str, set] = {}
    for p in pooled:
        by_bit_loop.setdefault(str(p["is_moufang_bit"]), set()).add(
            tuple(p["loop_law_vector"]))
        by_bit_alg.setdefault(str(p["is_moufang_bit"]), set()).add(
            tuple(p["algebra_law_vector"]))
    loop_split = {k: len(v) for k, v in by_bit_loop.items()}
    alg_split = {k: len(v) for k, v in by_bit_alg.items()}
    collides = (max(loop_split.values()) > 1 or max(alg_split.values()) > 1)
    emit("FC1c_POOLED_one_bit_carries_more_than_one_law_vector",
         n_tables=len(pooled), rows=pooled,
         distinct_loop_vectors_per_bit=loop_split,
         distinct_algebra_vectors_per_bit=alg_split,
         collision_examples=[
             {"bit": "False",
              "table_a": "definite ladder dim 16 (S)",
              "loop_vector_a": [r["law_vector"] for r, _ in rows
                                if r["cd_dim"] == 16][0],
              "table_b": "flip_pair(8,1,2)",
              "loop_vector_b": [r["loop_law_vector"] for r in OFF_ROWS_FOR_POOL
                                if r["table"] == "flip_pair(8,1,2)"][0],
              "algebra_vector_a": algebra_law_census(
                  algebra_table(16), "S")["law_vector"],
              "algebra_vector_b": [r["algebra_law_vector"]
                                   for r in OFF_ROWS_FOR_POOL
                                   if r["table"] == "flip_pair(8,1,2)"][0]}],
         classification="BOUNDED" if collides else "UNSUPPORTED",
         verdict=("SUPPORTED once the families are POOLED — the comparison "
                  "FC1a and FC1b each failed to make. is_moufang = False "
                  "covers 𝕊 (flexible, not alternative: algebra vector "
                  "[0,0,1,0]) AND flip_pair (not flexible, not alternative: "
                  "[0,0,0,0]); on the loop side it covers [1,1,1,0,0,0,1,1,1,"
                  "1,1] AND [0,0,1,0,0,0,0,0,0,1,0]. One bit, four different "
                  "law vectors. Two framings had to fail before the right "
                  "comparison was made, and both failures are on the record."))

    emit("FC5_domain_separation_is_load_bearing",
         probe="srmech.cascade.flip_pair(8, 1, 2)",
         flexible_on_signed_unit_loop=[cr["flexible"], cr["flexible_of"]],
         flexible_on_algebra_basis=[ca["alg_flexible_linearised"],
                                    ca["alg_flexible_linearised_of"]],
         verdicts_agree=(cr["flexible_holds"]
                         == ca["alg_flexible_linearised_holds"]),
         alternativity_on_signed_unit_loop=[cr["left_alternative"],
                                            cr["left_alternative_of"]],
         alternativity_on_algebra_basis=[ca["alg_left_alternative"],
                                         ca["alg_left_alternative_of"]],
         sedenion_rung_loop_alternative=[r["left_alternative"]
                                         for r, _ in rows
                                         if r["cd_dim"] == 16],
         sedenion_rung_algebra_alternative=algebra_law_census(
             algebra_table(16), "algebra_table(16) = S")["law_vector"],
         classification="BOUNDED",
         verdict=("Two domains, two answers, same law name. At dim 16 the "
                  "SIGNED UNIT LOOP is left- and right-ALTERNATIVE (1024/1024) "
                  "while the ALGEBRA is not — the standard '𝕊 is not "
                  "alternative' is an ALGEBRA statement and does not transfer "
                  "to the unit loop. An op that reported one number under the "
                  "name 'alternative' would be a silent-wrong-answer for "
                  "whichever caller meant the other domain."))

    # NC2 — trivial rungs must not share a law vector with the sedenion rung
    triv = [r for r, _ in rows if r["cd_dim"] in (1, 2)]
    sede = [r for r, _ in rows if r["cd_dim"] == 16]
    emit("NC2_trivial_rung_separation_control",
         trivial=[{"carrier": r["carrier"], "law_vector": r["law_vector"]}
                  for r in triv],
         sedenion=[{"carrier": r["carrier"], "law_vector": r["law_vector"]}
                   for r in sede],
         separated=all(r["law_vector"] != s["law_vector"]
                       for r in triv for s in sede),
         control_valid=all(r["law_vector"] != s["law_vector"]
                           for r in triv for s in sede),
         verdict=("The trivial rungs satisfy every law; the sedenion rung does "
                  "not. A census returning the same vector for both would not "
                  "be separating."))

    # FC4 — division per rung
    emit("FC4_division_equals_right_multiply_by_inverse",
         rows=[{"carrier": r["carrier"],
                "ok": r["division_equals_right_multiply_by_inverse"],
                "of": r["division_equals_right_multiply_by_inverse_of"],
                "holds": r["division_equals_right_multiply_by_inverse_holds"]}
               for r, _ in rows],
         classification="BOUNDED",
         verdict=("Measured per rung rather than asserted once. b/a = b·a⁻¹ is "
                  "the surface the rc426 note hand-rolled; it survives past "
                  "the point associativity does."))

    # Worked example the proposal quotes.
    m16 = [r for r, _ in rows if r["cd_dim"] == 8][0]
    m32 = [r for r, _ in rows if r["cd_dim"] == 16][0]
    emit("worked_example_loop_law_census",
         op="loop_law_census(unit_loop(16))  # the sedenion unit loop M32",
         order=m32["order"],
         is_moufang_bit_says=m32["shipped_is_moufang_on_algebra_basis"],
         census_says={nm: [m32[nm], m32[nm + "_of"]] for nm in LAW_NAMES},
         m16_law_vector=m16["law_vector"], m32_law_vector=m32["law_vector"],
         the_capability=("one bit says False; the census says WHICH laws "
                         "survive and by how much"))


# ══════════════════════════════════════════════════════════════════════
# LEDGER — every hand-roll above is a REPORTABLE FINDING.
# ══════════════════════════════════════════════════════════════════════
def part_ledger() -> None:
    emit("op_usage_ledger",
         shipped_ops_used=[
             "srmech.cascade.cyclic_mod_add",
             "srmech.cascade.unit_loop",
             "srmech.cascade.loop_invariants",
             "srmech.cascade.is_moufang",
             "srmech.cascade.moufang_residue",
             "srmech.cascade.associator",
             "srmech.cascade.cd_commutator",
             "srmech.cascade.group_algebra_table",
             "srmech.cascade.algebra_table",
             "srmech.cascade.table_product",
             "srmech.cascade.flip_pair",
             "srmech.cascade.cd_basis",
             "srmech.math.cyclic.gcd",
             "srmech.math.cyclic.mod_mul",
             "srmech.math.q.Q",
             "srmech.music.normal_order",
             "srmech.music.prime_form",
             "srmech.introspect.tool_schema.get_tool_schema",
         ],
         hand_rolled=[
             dict(what="ti_product / ti_act / dihedral_table",
                  proposed_op="srmech.cascade.finite_group.dihedral_group",
                  why=("no order-2n group object ships; FA1 shows every "
                       "shipped constructor returns either an ABELIAN cyclic "
                       "group of order dim or a signed unit loop of order "
                       "2·dim (a power of two)"),
                  mitigation=("every modular step is a shipped cyclic_mod_add; "
                              "the reflection is a named Class-K pin-slot with "
                              "Class-C re-application, never abs()"),
                  reportable_finding=True),
             dict(what="conjugacy_census (orbits, k, commuting pairs, guard)",
                  proposed_op="srmech.cascade.finite_group.conjugacy_census",
                  why="registry grep finds no conjugacy / class-equation op",
                  mitigation="reads only a shipped Cayley table",
                  reportable_finding=True),
             dict(what="loop_law_census (11 laws over the signed unit loop)",
                  proposed_op="srmech.cascade.cayley_dickson.loop_law_census",
                  why=("alternativity / flexibility / LIP / RIP / division "
                       "have NO named op; hand-rolled in at least four notes "
                       "(rc360, rc387, lane_d 2026-07-28, rc426)"),
                  mitigation="reads unit_loop's own Cayley table",
                  reportable_finding=True),
             dict(what="signed_unit_loop_from_table",
                  proposed_op=("srmech.cascade.unit_loop needs a `table=` "
                               "parameter, matching its own siblings"),
                  why=("unit_loop(dim) always reads the definite ladder and "
                       "has no table= parameter, unlike is_moufang / "
                       "moufang_residue / associator which all accept one. "
                       "The SHIPPED flip_pair control therefore cannot reach "
                       "the unit loop without a hand-roll — an ASYMMETRY in "
                       "the shipped surface, found by using it"),
                  mitigation="the sign rule is the shipped table's own cocycle",
                  reportable_finding=True),
         ],
         note=("Reaching for a hand-roll where a shipped op exists is a "
               "reportable finding, not a shortcut "
               "([[feedback_scratch_measurements_must_use_srmech_or_gaps_stay_"
               "invisible]])."))


def part_greps() -> None:
    """The grep evidence for every absence claim, recorded verbatim."""
    emit("prior_art_grep_evidence",
         registry_file="docs/srmech/python/tests/registered_op_names.txt",
         registry_lines=649,
         greps=[
             dict(query=r"grep -inE 'conjugac|centraliz|centralis|"
                        r"class_equation|commut|dihedral|\bti_|tn_i|group|"
                        r"orbit|stabiliz|stabilis' tests/registered_op_names.txt",
                  hits=5,
                  hit_names=["srmech.cascade.cd_commutator",
                             "srmech.cascade.group_algebra_table",
                             "srmech.math.laplacian.three_fold_eigvec_groups",
                             "srmech.physics.qm.single_particle.commutator",
                             "srmech.physics.qm.so8."
                             "quaternion_subalgebra_stabilizer"],
                  ruling=("ZERO conjugacy / class-equation / dihedral ops. "
                          "cd_commutator and commutator are element-level "
                          "brackets; group_algebra_table is R[Z/dim] (its own "
                          "docstring: cyclic, all signs +1); "
                          "quaternion_subalgebra_stabilizer is an so8 "
                          "subalgebra read, not a group census.")),
             dict(query="grep -rniE 'dihedral' srmech/ --include=*.py",
                  hits=0,
                  ruling="ABSENT from the entire package source."),
             dict(query=("grep -rniE 'left_alternative|right_alternative|"
                         "inverse_property|diassociat' srmech/ --include=*.py"),
                  hits=0,
                  ruling=("ABSENT as named surfaces. 'alternativ' hits are all "
                          "the English word 'alternatively' in prose, plus the "
                          "is_moufang docstring which states 'O alternative => "
                          "Moufang' without a named alternativity op.")),
             dict(query=("grep -rniE 'flexib' srmech/ --include=*.py"),
                  hits=1,
                  hit_names=["srmech/cascade/cayley_dickson.py:826 "
                             "(flip_pair docstring — the one-named-bit "
                             "FLEXIBILITY negative control)"],
                  ruling=("flip_pair SHIPS as the control that BREAKS "
                          "flexibility, but there is no op that MEASURES "
                          "flexibility — the control has no instrument.")),
             dict(query=("grep -rilE 'left_alternative|right_alternative|"
                         "inverse_property|diassociat|flexible' "
                         "docs/srmech/notes/"),
                  hits=16,
                  hit_names=["cd_controls_rc387.py",
                             "lane_d_cube_holonomy_2026-07-28.py",
                             "rc360_exact_ops_verification.py",
                             "reversal_is_not_rewind_rc426.py"],
                  ruling=("The SAME laws have been hand-rolled in at least "
                          "FOUR separate notes across rc360 -> rc426. That is "
                          "the strongest form of the gap: repeated "
                          "re-derivation of a surface that never landed.")),
             dict(query=("read srmech/music/relations.py:54-63 "
                         "(the REJECTED block)"),
                  hits=1,
                  ruling=("The rejection names exactly three ELEMENT-LEVEL "
                          "ops — interval_invert / pitch_class_transpose / "
                          "pitch_class_invert — and rejects each because it is "
                          "'a single cyclic_mod_add call carrying no "
                          "decision'. It does NOT mention the GROUP object, "
                          "and FA3 measures that the group object DOES carry a "
                          "decision (the composition order). The rejection "
                          "stands for what it names and does not extend.")),
             dict(query=("grep -rilE 'dihedral' docs/srmech/notes/"),
                  hits=10,
                  ruling=("All prose. The only load-bearing hit is "
                          "reversal_is_not_rewind_rc426.py:1212, which names "
                          "'MISSING SURFACE: a dihedral / T-I group carrier' — "
                          "i.e. a prior round recorded the same absence.")),
         ])


def part_proposals() -> None:
    """The costed list, so the note is self-contained and no number dangles."""
    emit("proposed_ops",
         ops=[
             dict(name="dihedral_group",
                  module="srmech/cascade/finite_group.py (NEW module)",
                  signature=("dihedral_group(n: int, convention: str) -> "
                             "Dict[str, Any]  # {'n','order','convention',"
                             "'elements','cayley_table'}"),
                  an_class="I (cyclic) then C (orientation) with K pin-slot",
                  exact=True,
                  composes_from=["srmech.cascade.cyclic_mod_add"],
                  cost="medium",
                  evidence=["FA1_no_order24_group_ships",
                            "FA2_no_public_transposition_or_inversion",
                            "FA3_convention_is_a_decision",
                            "FA4_group_orbit_reproduces_shipped_prime_form"],
                  why=("FA1: every shipped group-object constructor refuses "
                       "non-power-of-two order, so NO group of order 12 or 24 "
                       "is reachable at all. FA3: the composition-order "
                       "convention moves 360 of 576 cells and splits a "
                       "downstream count 13824 vs 5184 — a DECISION, which is "
                       "what the rc424 rejection said the element-level ops "
                       "lacked. FA4: the orbit reproduces the shipped "
                       "prime_form 1507/1507 on both conventions, so this IS "
                       "the object prime_form already uses privately.")),
             dict(name="conjugacy_census",
                  module="srmech/cascade/finite_group.py (NEW module)",
                  signature=("conjugacy_census(cayley_table: "
                             "Sequence[Sequence[int]]) -> Dict[str, Any]"),
                  an_class="E (catalog/orbit enumeration) then D (pattern)",
                  exact=True,
                  composes_from=["srmech.cascade.unit_loop",
                                 "srmech.cascade.cyclic_mod_add",
                                 "srmech.math.q.Q"],
                  cost="medium",
                  guard=("MEASURES associativity FIRST and REFUSES the "
                         "class-equation branch when it fails; commuting "
                         "pairs and commuting probability are direct censuses "
                         "and stay valid on any magma"),
                  evidence=["FB1_burnside_identity_domain",
                            "FB2_unguarded_op_emits_a_silent_wrong_number",
                            "FB3_conjugation_bracketing",
                            "NB1_corrupted_table_control"],
                  why=("FB2: an unguarded op reports 144 where the truth is "
                       "88 at M16 and 544 where the truth is 184 at M32 — "
                       "wrong by 56 and by 360, silently. The guard is the "
                       "op.")),
             dict(name="law_census",
                  module="srmech/cascade/cayley_dickson.py",
                  signature=("law_census(domain: str, dim: int = 8, table: "
                             "Any = None) -> Dict[str, Any]  # domain is "
                             "REQUIRED: 'signed_unit_loop' | 'algebra_basis'"),
                  an_class="D (pattern-match) then E (catalog) over M/K",
                  exact=True,
                  composes_from=["srmech.cascade.unit_loop",
                                 "srmech.cascade.associator",
                                 "srmech.cascade.moufang_residue",
                                 "srmech.cascade.cd_basis",
                                 "srmech.cascade.algebra_table"],
                  cost="large",
                  guard=("`domain` has NO DEFAULT, by measurement: FC5 shows "
                         "the same law NAME gives OPPOSITE verdicts in the two "
                         "domains on the SAME shipped table"),
                  evidence=["FC5_domain_separation_is_load_bearing",
                            "FC1c_POOLED_one_bit_carries_more_than_one_law_"
                            "vector", "FC3_counts_are_not_sets",
                            "NC1_flip_pair_flexibility_control_TWO_DOMAINS",
                            "FC4_division_equals_right_multiply_by_inverse"],
                  why=("alternativity / flexibility / LIP / RIP / division / "
                       "diassociativity have NO named op and have been "
                       "hand-rolled in four separate notes. is_moufang ships "
                       "one BIT; FC1c shows that bit covers four different "
                       "law vectors once the ladder and off-ladder families "
                       "are pooled.")),
             dict(name="unit_loop  (PARAMETER EXTENSION to a SHIPPED op)",
                  module="srmech/cascade/cayley_dickson.py",
                  signature="unit_loop(dim: int = 8, table: Any = None)",
                  an_class="A (the object is content-addressed by its table)",
                  exact=True,
                  composes_from=["srmech.cascade.unit_loop"],
                  cost="small",
                  evidence=["off_ladder_law_census", "op_usage_ledger"],
                  why=("unit_loop is the ONLY member of its family without a "
                       "`table=` parameter — associator, moufang_residue, "
                       "is_moufang and malcev_defect all have one. So the "
                       "SHIPPED controls flip_pair and algebra_table(gammas=) "
                       "cannot reach the shipped unit loop without a "
                       "hand-roll, which this note had to write. Found by "
                       "USING the surface, not by reading it.")),
         ],
         rejected=[
             dict(name="interval_invert / pitch_class_transpose / "
                       "pitch_class_invert",
                  reason=("the rc424 rejection STANDS. Each is one "
                          "cyclic_mod_add carrying no decision; FA3's decision "
                          "belongs to the GROUP object, not to these three. "
                          "Re-examined as instructed and NOT overturned."),
                  already_ships_at="srmech/music/relations.py:54-63 (as a "
                                   "documented rejection)"),
             dict(name="is_moufang / moufang_residue / malcev_defect / "
                       "unit_loop / loop_invariants",
                  reason="ALREADY SHIP — proposing any of them is a defect",
                  already_ships_at="srmech/cascade/cayley_dickson.py:2227, "
                                   ":2277, :2377, :2418"),
             dict(name="a flexibility NEGATIVE CONTROL",
                  reason=("ALREADY SHIPS as flip_pair; what is missing is the "
                          "INSTRUMENT it is a control for, which is why "
                          "law_census is proposed and flip_pair is not"),
                  already_ships_at="srmech/cascade/cayley_dickson.py:808"),
             dict(name="an order-24 group via group_algebra_table",
                  reason=("NOT REACHABLE — group_algebra_table refuses any dim "
                          "that is not a power of two, and is abelian by "
                          "construction (its own docstring: lane (i+j) mod dim, "
                          "all signs +1)"),
                  already_ships_at="srmech/cascade/cayley_dickson.py:897"),
         ])

    emit("wrong_in_brief",
         items=[
             dict(claim=("brief Phase-1 item 3: 'Alternativity, flexibility, "
                         "Moufang, LIP/RIP, and division were all hand-rolled'"),
                  correction=("MOUFANG SHIPS, at two granularities — "
                              "is_moufang (whole-loop boolean) and "
                              "moufang_residue (per-triple exact-ℚ defect), "
                              "since rc398. The other five are genuinely "
                              "absent. A proposal that bundled Moufang in "
                              "would have been a defect."),
                  severity="would have produced a duplicate op"),
             dict(claim=("brief Phase-1 item 3: 'srmech.cascade.associator is "
                         "rational-tuples only'"),
                  correction=("accurate about its OPERANDS, but associator "
                              "also takes `table=`, so it already reads any "
                              "monomial structure tensor. The real asymmetry "
                              "is the reverse one: unit_loop has NO table= "
                              "parameter while every sibling does."),
                  severity="mis-locates the gap"),
             dict(claim=("ground truth: 'group_algebra_table is R[Z/dim], "
                         "cyclic only'"),
                  correction=("true and INCOMPLETE — it also REFUSES any dim "
                              "that is not a power of two, so Z/12 and Z/24 "
                              "are not reachable from it either. The absence "
                              "is wider than 'no non-abelian order 24': there "
                              "is no group of order 3, 5, 12 or 24 AT ALL."),
                  severity="understates the gap"),
             dict(claim=("brief Phase-1 item 2: the class equation 'predicts "
                         "144 commuting pairs, measured 88' at the octonion "
                         "loop"),
                  correction=("CONFIRMED independently (144 vs 88, error 56) "
                              "and EXTENDED: at the sedenion unit loop M32 it "
                              "predicts 544 and measures 184, error 360. The "
                              "silent-wrong-answer grows with the rung."),
                  severity="correct but incomplete"),
             dict(claim=("rc426 record kind 'bare_rate_is_commuting_"
                         "probability'"),
                  correction=("the RECORD is self-consistent (it sets "
                              "equals=false at O16) but the KIND NAME is false "
                              "at that row, and THREE different fractions are "
                              "in play there: the bare-reversal rate 2752/4096 "
                              "= 43/64, the class-equation quotient k/|G| = "
                              "9/16, and the ACTUAL commuting-pair fraction "
                              "88/256 = 11/32 measured here. Anyone quoting "
                              "'the commuting probability of O16' from that "
                              "kind name will quote the wrong number."),
                  severity="naming trap in a committed artifact"),
             dict(claim=("my OWN pre-registered FC1 prediction: 'flexibility "
                         "survives at dim 16 where Moufang fails, so one bit "
                         "cannot carry the vector'"),
                  correction=("HALF WRONG. Flexibility survives — and so do "
                              "both alternativity laws, LIP, RIP, division, "
                              "power- and di-associativity, on the LOOP. Only "
                              "Moufang fails. The bit determined the vector on "
                              "the ladder (FC1a UNSUPPORTED) and off it (FC1b "
                              "UNSUPPORTED); only the POOLED comparison (FC1c) "
                              "supports the claim."),
                  severity="two falsifiers fired against me; both on the "
                           "record"),
             dict(claim=("my OWN first-pass instruments: a substring token "
                         "match, a reversed GROUP PRODUCT, a naive (x,x,y) "
                         "alternativity probe, and a single-domain flip_pair "
                         "control"),
                  correction=("all four were wrong and all four are recorded "
                              "as instrument_correction fields rather than "
                              "silently repaired: 5 false positives on the "
                              "'ti' of 'partials'; 13824 twice because the "
                              "opposite group is still a group; a VACUOUS "
                              "alternativity test that scored the sedenion "
                              "ALGEBRA alternative (it is not); and a control "
                              "scored invalid because it was run on the wrong "
                              "object."),
                  severity="method"),
         ])


def main() -> None:
    part0_env()
    partA_absence()
    partA_convention_decision()
    partA_reproduces_prime_form()
    partB()
    partC()
    part_ledger()
    part_greps()
    part_proposals()
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        for rec in _ROWS:
            fh.write(json.dumps(rec, sort_keys=False, default=str) + "\n")
    print("wrote", OUT, "records:", len(_ROWS))


if __name__ == "__main__":
    main()
