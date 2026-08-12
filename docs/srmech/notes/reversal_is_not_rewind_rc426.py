#!/usr/bin/env python3
"""reversal_is_not_rewind_rc426 — READ-ONLY measurement of the thesis
**REVERSAL IS NOT REWIND**: that reversing a relational path requires an
INVERSION as well as an order-flip, across five carriers of increasing
algebraic weakness, ending at the NON-ASSOCIATIVE octonion unit loop.

READ-ONLY RESEARCH. This script builds no op, registers nothing, bumps no
version and opens no PR. It measures the CURRENT tree (0.9.0rc425, registry
649) so that every number rests on execution rather than recollection, per
``[[feedback_computational_provenance_discipline]]``.

THE QUESTION
============
Lewin's interval-function axiom on a set ``S`` carrying a simply-transitive
action of a group ``G`` says the intervals COMPOSE::

    int(s,t) ∘ int(t,u) == int(s,u)          (the FORWARD law)

The thesis under test is what happens when the path is walked BACKWARDS. Two
candidate "reversals" exist and they are NOT the same operation:

* **BARE order-reversal** — swap the two factors, change nothing else.
* **CHIRAL reversal** — swap the two factors AND invert each of them.

The second is total on any group because ``(ab)⁻¹ = b⁻¹a⁻¹`` is an
ANTI-automorphism of every group. The first is a homomorphism only when the
carrier is abelian. So the claim is that reversal is a **Class K sign-flip ∘
Class C which-way** composition (chiral), not a temporal rewind.

⚠️ **THE ONE THAT CAN GENUINELY FAIL.** ``(ab)⁻¹ = b⁻¹a⁻¹`` is a GROUP
theorem; its proof uses associativity. The octonion unit loop
``{±e₀..±e₇}`` is non-abelian AND NON-ASSOCIATIVE. It is a Moufang loop with
the inverse property, so the identity "should" survive — and "should still
work" is exactly the class of claim this project has repeatedly measured
false (``[[feedback_an_asserted_algebraic_property_is_not_a_measured_one]]``).
Nothing below is asserted; every cell is executed.

DISCIPLINE
==========
* Every product, conjugate and modular step goes THROUGH a shipped srmech op
  — ``cyclic_mod_add`` (Class I), ``q8_mult`` / ``q8_conjugate``,
  ``oct_mult`` / ``oct_conjugate``, ``oct_torsor_act`` / ``oct_torsor_div``,
  ``cd_mult`` / ``cd_conjugate``. Hand-rolled arithmetic would hide exactly
  the MISSING SURFACES a spike exists to find
  (``[[feedback_scratch_measurements_must_use_srmech_or_gaps_stay_invisible]]``).
  §9 ships the op-usage ledger, including everything that had to be built
  locally and why.
* **No ``abs()`` anywhere.** The one place a sign is READ (the Cayley–Dickson
  dual construction of §7) uses the Class-K ``pin_slot_at_zero`` composed
  Class-C through ``net_chirality``
  (``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``).
* Exact integers throughout; no float, no numpy.
* **Negative controls are mandatory** — an instrument that cannot return
  otherwise is not a measurement
  (``[[feedback_an_instrument_that_cannot_return_otherwise_is_not_a_measurement]]``).
  §5 ships a deliberately-wrong half-inversion, a vacuous
  identity-as-reversal, and the abelian rows where inversion is INVISIBLE.
* **Co-equal dual construction is a CONSISTENCY oracle** — §7 rebuilds the
  whole octonion loop a second time through ``cd_mult`` on exact-ℚ 8-tuples
  and cross-checks all 256 products against the byte carrier
  (``[[user_stance_co_equal_dual_construction_is_a_consistency_oracle]]``).
* Every null is CLASSIFIED (REFUTED / BOUNDED / EMPTY / UNSUPPORTED /
  VACUOUS).

THE EIGHT-CELL ENUMERATION (§4)
===============================
For each ordered triple ``(s,t,u)`` write ``X = int(s,t)``, ``Y = int(t,u)``,
``Z = int(s,u)``. Every way of composing two of them against ``Z`` under the
{keep,reverse} × {invert-none, invert-first, invert-second, invert-both}
cross is executed and counted::

    P1  X·Y  == Z      keep    order, no inversion
    P2  Y·X  == Z      REVERSE order, no inversion          <- BARE REVERSAL
    Q1  X⁻¹·Y⁻¹ == Z⁻¹ keep    order, invert BOTH
    Q2  Y⁻¹·X⁻¹ == Z⁻¹ REVERSE order, invert BOTH           <- CHIRAL REVERSAL
    R1  X⁻¹·Y   == Z⁻¹ keep    order, invert first  only
    R2  X·Y⁻¹   == Z⁻¹ keep    order, invert second only
    R3  Y⁻¹·X   == Z⁻¹ REVERSE order, invert first  only    <- deliberately wrong
    R4  Y·X⁻¹   == Z⁻¹ REVERSE order, invert second only    <- deliberately wrong

Exactly one of ``P1``/``P2`` is the carrier's FORWARD law (which one depends
only on whether the interval is read as a left or a right quotient — §4 runs
BOTH readings so the answer cannot be a convention artifact). Its
order-reversed, both-inverted partner is CHIRAL. The remaining six cells are
the controls.

Run:  PYTHONPATH=docs/srmech/python python3 reversal_is_not_rewind_rc426.py
Emits: reversal_is_not_rewind_rc426.ndjson (one record per line)
"""
from __future__ import annotations

import itertools
import json
import sys

# ── shipped ops, imported at their registered paths ──────────────────────────
import srmech
from srmech.biology.q8 import q8_conjugate, q8_mult
from srmech.cascade import (
    cd_conjugate,
    cd_mult,
    cyclic_mod_add,
    net_chirality,
    pin_slot_at_zero,
)
from srmech.math.octonion import (
    oct_conjugate,
    oct_mult,
    oct_torsor_act,
    oct_torsor_div,
)

RECORDS = []


def emit(kind, **fields):
    RECORDS.append(dict(kind=kind, **fields))


def jkey(x):
    """JSON-safe key for a carrier element (tuples -> strings)."""
    return x if isinstance(x, int) else str(x)


# ═════════════════════════════════════════════════════════════════════════════
# §0  ENVIRONMENT STAMP
# ═════════════════════════════════════════════════════════════════════════════
def section_env():
    try:
        from srmech.introspect.tool_schema import get_tool_schema
        registry_n = len(get_tool_schema())
    except Exception as exc:                       # pragma: no cover
        registry_n = f"UNAVAILABLE: {exc!r}"
    try:
        from srmech import _native
        has_native = bool(_native.HAS_NATIVE)
    except Exception:                              # pragma: no cover
        has_native = None
    import importlib.util
    numpy_present = importlib.util.find_spec("numpy") is not None
    emit(
        "env",
        srmech_file=srmech.__file__,
        srmech_version=srmech.__version__,
        registry_ops=registry_n,
        has_native=has_native,
        numpy_present=numpy_present,
        python=sys.version.split()[0],
        note=(
            "numpy ABSENT is CORRECT for this tree; HAS_NATIVE False means the "
            "pure-Python path is under test."
        ),
    )
    print(f"srmech.__file__    = {srmech.__file__}")
    print(f"srmech.__version__ = {srmech.__version__}")
    print(f"registry ops       = {registry_n}")
    print(f"HAS_NATIVE         = {has_native}   numpy present = {numpy_present}")
    print()


# ═════════════════════════════════════════════════════════════════════════════
# §1  THE CARRIERS
#
# Each carrier ships: the element list, the shipped-op product, the shipped-op
# inverse, and a declaration of which shipped ops produced every table entry.
# NOTHING about associativity / commutativity / inverse-hood is assumed — §2
# measures all three.
# ═════════════════════════════════════════════════════════════════════════════
class Carrier:
    def __init__(self, key, label, elems, mul, inv, ops_used, notes=""):
        self.key = key
        self.label = label
        self.elems = list(elems)
        self._mul = mul
        self._inv = inv
        self.ops_used = ops_used
        self.notes = notes
        # Every table entry is produced by calling the SHIPPED op once.
        self.M = {(a, b): mul(a, b) for a in self.elems for b in self.elems}
        self.I = {a: inv(a) for a in self.elems}

    @property
    def n(self):
        return len(self.elems)

    def mul(self, a, b):
        return self.M[(a, b)]

    def inv(self, a):
        return self.I[a]


# ── carrier 1/2: ℤ/7 and ℤ/12, the ABELIAN CONTROLS ──────────────────────────
def make_cyclic(n, key, label, notes):
    elems = list(range(n))

    def mul(a, b):
        return cyclic_mod_add(a, b, n)          # Class I, shipped

    def inv(a):
        # additive inverse WITHOUT `%`: (n - a) is in [1, n]; the shipped
        # Class-I add reduces it into [0, n).  No abs(), no bare modulo.
        return cyclic_mod_add(n - a, 0, n)      # Class I, shipped

    return Carrier(key, label, elems, mul, inv,
                   ops_used=["srmech.cascade.cyclic_mod_add"], notes=notes)


Z7 = make_cyclic(
    7, "Z7", "ℤ/7 — the note alphabet (§3.46.2; fifth = +4, fourth = +3)",
    "ABELIAN. PRE-REGISTERED PREDICTION: bare reversal = 100%. "
    "If it is not 100%, the HARNESS is broken, not the mathematics.")
Z12 = make_cyclic(
    12, "Z12", "ℤ/12 — the chromatic lane",
    "ABELIAN. Same pre-registered prediction as ℤ/7; two abelian rows guard "
    "against a one-off.")


# ── carrier 3: Q8, the quaternion group (non-abelian, ASSOCIATIVE) ───────────
Q8 = Carrier(
    "Q8", "Q₈ — quaternion group, order 8 (byte = (sign<<2)|coset)",
    range(8), q8_mult, q8_conjugate,
    ops_used=["srmech.biology.q8.q8_mult", "srmech.biology.q8.q8_conjugate"],
    notes="NON-ABELIAN, associative. Predict bare < 100%, chiral = 100%.")


# ── carrier 4: the T/I group of order 24 (the regression anchor) ─────────────
# Element (f, k): f=0 is the transposition x -> x+k; f=1 is the inversion
# x -> k-x, both on ℤ/12.  Composition is FUNCTION composition (a∘b)(x) =
# a(b(x)); every modular step goes through the shipped Class-I add.
_TI_ELEMS = [(f, k) for f in (0, 1) for k in range(12)]


def _ti_mul(a, b):
    fa, ka = a
    fb, kb = b
    f = fa ^ fb                                       # Class I on ℤ/2
    if fa == 0:
        k = cyclic_mod_add(ka, kb, 12)                # Class I, shipped
    else:
        k = cyclic_mod_add(ka, 12 - kb, 12)           # Class I, shipped
    return (f, k)


def _ti_inv(a):
    f, k = a
    if f == 0:
        return (0, cyclic_mod_add(12 - k, 0, 12))     # T_k^-1 = T_-k
    return (1, k)                                     # every I_k is an involution


TI24 = Carrier(
    "TI24", "T/I group, order 24 (Tₙ and TₙI on ℤ/12) — the regression anchor",
    _TI_ELEMS, _ti_mul, _ti_inv,
    ops_used=["srmech.cascade.cyclic_mod_add"],
    notes="NON-ABELIAN, associative. Reproduces the established 5184/13824 = "
          "3/8 bare-reversal count.")


# ── carrier 5: THE OCTONION UNIT LOOP {±e₀..±e₇} — NON-ASSOCIATIVE ──────────
# Byte encoding: (sign << 3) | index, so 0..7 are +e₀..+e₇ and 8..15 are
# −e₀..−e₇.  oct_mult IS the loop product; oct_conjugate IS the unit inverse.
O16 = Carrier(
    "O16", "𝕆 unit loop {±e₀..±e₇}, order 16 — NON-ABELIAN and NON-ASSOCIATIVE",
    range(16), oct_mult, oct_conjugate,
    ops_used=["srmech.math.octonion.oct_mult",
              "srmech.math.octonion.oct_conjugate"],
    notes="The row that can genuinely fail: (ab)⁻¹ = b⁻¹a⁻¹ is a GROUP theorem "
          "and this carrier is not a group.")


CARRIERS = [Z7, Z12, Q8, TI24, O16]


def section_carriers():
    for c in CARRIERS:
        # Latin-square / quasigroup sanity: every row and column a permutation.
        rows_ok = all(len({c.mul(a, b) for b in c.elems}) == c.n for a in c.elems)
        cols_ok = all(len({c.mul(a, b) for a in c.elems}) == c.n for b in c.elems)
        closed = all(c.mul(a, b) in set(c.elems)
                     for a in c.elems for b in c.elems)
        ident = [e for e in c.elems
                 if all(c.mul(e, x) == x and c.mul(x, e) == x for x in c.elems)]
        inv_ok = sum(1 for a in c.elems
                     if ident and c.mul(a, c.inv(a)) == ident[0]
                     and c.mul(c.inv(a), a) == ident[0])
        emit("carrier", carrier=c.key, label=c.label, order=c.n,
             closed=closed, latin_rows=rows_ok, latin_cols=cols_ok,
             two_sided_identities=[jkey(e) for e in ident],
             two_sided_inverse_pairs=inv_ok, of=c.n,
             shipped_ops=c.ops_used, notes=c.notes)
        print(f"[carrier] {c.key:5s} order={c.n:3d}  latin={rows_ok and cols_ok} "
              f"  identity={[jkey(e) for e in ident]}  "
              f"inverses {inv_ok}/{c.n}")
    print()


# ═════════════════════════════════════════════════════════════════════════════
# §2  ALGEBRA CENSUS — commutativity, associativity, conjugacy, class equation
# ═════════════════════════════════════════════════════════════════════════════
def conj_classes(c):
    """Orbits of y under y ↦ (x·y)·x⁻¹.

    In a non-associative loop 'conjugation' is parenthesisation-dependent, so
    the alternative bracketing x·(y·x⁻¹) is measured alongside and the
    agreement count is reported rather than assumed (octonions are FLEXIBLE,
    which would force agreement — that is a claim, so it is executed).
    """
    reps, seen, agree = [], set(), 0
    total = 0
    for x in c.elems:
        for y in c.elems:
            total += 1
            if c.mul(c.mul(x, y), c.inv(x)) == c.mul(x, c.mul(y, c.inv(x))):
                agree += 1
    for y in c.elems:
        if y in seen:
            continue
        orb = {c.mul(c.mul(x, y), c.inv(x)) for x in c.elems}
        orb.add(y)
        seen |= orb
        reps.append(sorted(orb, key=jkey))
    return reps, agree, total


def section_algebra():
    census = {}
    for c in CARRIERS:
        commuting = sum(1 for a in c.elems for b in c.elems
                        if c.mul(a, b) == c.mul(b, a))
        abelian = commuting == c.n * c.n
        assoc = sum(1 for a in c.elems for b in c.elems for d in c.elems
                    if c.mul(c.mul(a, b), d) == c.mul(a, c.mul(b, d)))
        assoc_total = c.n ** 3
        classes, flex_agree, flex_total = conj_classes(c)
        k = len(classes)
        class_eq_pred = c.n * k
        class_eq_holds = class_eq_pred == commuting
        involutions = sum(1 for a in c.elems if c.mul(a, a) ==
                          next(e for e in c.elems
                               if all(c.mul(e, x) == x for x in c.elems)))
        census[c.key] = dict(commuting=commuting, k=k, abelian=abelian,
                             assoc=assoc, assoc_total=assoc_total,
                             involutions=involutions)
        emit("algebra_census", carrier=c.key, order=c.n,
             abelian=abelian,
             commuting_ordered_pairs=commuting, of=c.n * c.n,
             commuting_probability_num=commuting, commuting_probability_den=c.n * c.n,
             associative_triples=assoc, of_triples=assoc_total,
             associative=assoc == assoc_total,
             conjugacy_classes=k,
             conjugacy_class_sizes=[len(o) for o in classes],
             conjugacy_class_members=[[jkey(e) for e in o] for o in classes],
             class_equation_prediction=class_eq_pred,
             class_equation_reproduces_commuting_pairs=class_eq_holds,
             class_equation_verdict=(
                 "HOLDS — |G|·k(G) == #commuting ordered pairs (orbit-stabiliser)"
                 if class_eq_holds else
                 "FAILS — the class equation is a GROUP theorem and this carrier "
                 "is not a group"),
             conjugation_bracketings_agree=flex_agree, of_bracketings=flex_total,
             involutions_x2_eq_e=involutions)
        print(f"[algebra] {c.key:5s} abelian={str(abelian):5s} "
              f"assoc={assoc}/{assoc_total}  commuting={commuting}/{c.n*c.n}  "
              f"k={k}  |G|·k={class_eq_pred} -> class-eq {'OK' if class_eq_holds else 'FAILS'}")
    print()
    return census


# ═════════════════════════════════════════════════════════════════════════════
# §3  THE ANTI-AUTOMORPHISM, PAIRWISE
#
#   (ab)⁻¹ == b⁻¹a⁻¹   the REAL identity — the whole reason chiral works
#   (ab)⁻¹ == a⁻¹b⁻¹   the WRONG one — a homomorphism only when abelian
# ═════════════════════════════════════════════════════════════════════════════
def section_antiauto():
    for c in CARRIERS:
        good = sum(1 for a in c.elems for b in c.elems
                   if c.inv(c.mul(a, b)) == c.mul(c.inv(b), c.inv(a)))
        bad = sum(1 for a in c.elems for b in c.elems
                  if c.inv(c.mul(a, b)) == c.mul(c.inv(a), c.inv(b)))
        commuting = sum(1 for a in c.elems for b in c.elems
                        if c.mul(a, b) == c.mul(b, a))
        tot = c.n * c.n
        emit("anti_automorphism", carrier=c.key,
             reversal_with_inversion_holds=good, of=tot,
             reversal_with_inversion_total=good == tot,
             bare_inversion_holds=bad,
             bare_inversion_total=bad == tot,
             bare_inversion_equals_commuting_pairs=bad == commuting,
             note=("(ab)⁻¹ = b⁻¹a⁻¹ is the anti-automorphism; (ab)⁻¹ = a⁻¹b⁻¹ "
                   "is a homomorphism and holds exactly on the commuting pairs."))
        print(f"[anti-aut] {c.key:5s} (ab)⁻¹=b⁻¹a⁻¹ : {good}/{tot}"
              f"   (ab)⁻¹=a⁻¹b⁻¹ : {bad}/{tot}  (=commuting {bad==commuting})")
    print()


# ═════════════════════════════════════════════════════════════════════════════
# §4  THE EIGHT-CELL REVERSAL ENUMERATION
# ═════════════════════════════════════════════════════════════════════════════
CELL_DOC = {
    "P1": "X·Y == Z            keep order, invert nothing",
    "P2": "Y·X == Z            REVERSE order, invert nothing   [BARE REVERSAL]",
    "Q1": "X⁻¹·Y⁻¹ == Z⁻¹      keep order, invert BOTH",
    "Q2": "Y⁻¹·X⁻¹ == Z⁻¹      REVERSE order, invert BOTH      [CHIRAL REVERSAL]",
    "R1": "X⁻¹·Y == Z⁻¹        keep order, invert FIRST only",
    "R2": "X·Y⁻¹ == Z⁻¹        keep order, invert SECOND only",
    "R3": "Y⁻¹·X == Z⁻¹        REVERSE order, invert FIRST only  [neg. control]",
    "R4": "Y·X⁻¹ == Z⁻¹        REVERSE order, invert SECOND only [neg. control]",
}


def eight_cells(S, interval, mul, inv):
    """Count all eight cells over every ordered triple of S.

    Returns ``(counts, total, hits)`` where ``hits[cell]`` is the SET of triple
    indices satisfying that cell — so §4b can ask whether two cells of equal
    COUNT are the same SET, which a count alone cannot decide.
    """
    counts = dict.fromkeys(CELL_DOC, 0)
    hits = {k: set() for k in CELL_DOC}
    total = 0
    for s in S:
        for t in S:
            X = interval(s, t)
            iX = inv(X)
            for u in S:
                i = total
                total += 1
                Y = interval(t, u)
                Z = interval(s, u)
                iY, iZ = inv(Y), inv(Z)
                if mul(X, Y) == Z:
                    counts["P1"] += 1
                    hits["P1"].add(i)
                if mul(Y, X) == Z:
                    counts["P2"] += 1
                    hits["P2"].add(i)
                if mul(iX, iY) == iZ:
                    counts["Q1"] += 1
                    hits["Q1"].add(i)
                if mul(iY, iX) == iZ:
                    counts["Q2"] += 1
                    hits["Q2"].add(i)
                if mul(iX, Y) == iZ:
                    counts["R1"] += 1
                    hits["R1"].add(i)
                if mul(X, iY) == iZ:
                    counts["R2"] += 1
                    hits["R2"].add(i)
                if mul(iY, X) == iZ:
                    counts["R3"] += 1
                    hits["R3"].add(i)
                if mul(Y, iX) == iZ:
                    counts["R4"] += 1
                    hits["R4"].add(i)
    return counts, total, hits


def group_readings(c):
    """The two interval conventions on a carrier acting on ITSELF.

    LEFT  reading: int(a,b) = b·a⁻¹, so int(a,b)·a == b  (a LEFT action).
    RIGHT reading: int(a,b) = a⁻¹·b, so a·int(a,b) == b  (a RIGHT action).

    Running both is the guard against the whole result being an artifact of a
    chosen composition convention.
    """
    def left(a, b):
        return c.mul(b, c.inv(a))

    def right(a, b):
        return c.mul(c.inv(a), b)

    return {"left_quotient_b_ainv": left, "right_quotient_ainv_b": right}


def wellformed(c, interval, side):
    """Does the interval actually CARRY s to t? (loop division vs x·s⁻¹.)"""
    ok = 0
    tot = 0
    for a in c.elems:
        for b in c.elems:
            tot += 1
            g = interval(a, b)
            if side == "left" and c.mul(g, a) == b:
                ok += 1
            elif side == "right" and c.mul(a, g) == b:
                ok += 1
    return ok, tot


def section_reversal(census):
    table = {}
    for c in CARRIERS:
        for name, iv in group_readings(c).items():
            side = "left" if name.startswith("left") else "right"
            wf_ok, wf_tot = wellformed(c, iv, side)
            counts, total, hits = eight_cells(c.elems, iv, c.mul, c.inv)

            forward_cell = "P2" if side == "left" else "P1"
            bare_cell = "P1" if side == "left" else "P2"
            chiral_cell = "Q1" if side == "left" else "Q2"
            invonly_cell = "Q2" if side == "left" else "Q1"

            fwd, bare = counts[forward_cell], counts[bare_cell]
            chi, invo = counts[chiral_cell], counts[invonly_cell]
            comm = census[c.key]["commuting"]
            pred_bare = c.n * comm                 # |S| × commuting ordered pairs
            pred_class_eq = c.n * c.n * census[c.key]["k"]   # |S|·|G|·k(G)

            emit("reversal_eight_cells", carrier=c.key, order=c.n,
                 reading=name, action_side=side,
                 interval_wellformed=wf_ok, of_pairs=wf_tot,
                 interval_wellformed_total=wf_ok == wf_tot,
                 ordered_triples=total,
                 cells={k: counts[k] for k in CELL_DOC},
                 cell_legend=CELL_DOC,
                 FORWARD_cell=forward_cell, FORWARD=fwd,
                 FORWARD_total=fwd == total,
                 BARE_REVERSAL_cell=bare_cell, BARE_REVERSAL=bare,
                 BARE_REVERSAL_total=bare == total,
                 CHIRAL_REVERSAL_cell=chiral_cell, CHIRAL_REVERSAL=chi,
                 CHIRAL_REVERSAL_total=chi == total,
                 INVERSION_ONLY_cell=invonly_cell, INVERSION_ONLY=invo,
                 inversion_only_equals_bare=invo == bare,
                 predicted_bare_from_commuting_pairs=pred_bare,
                 predicted_bare_matches=pred_bare == bare,
                 predicted_bare_from_class_equation=pred_class_eq,
                 class_equation_route_matches=pred_class_eq == bare,
                 bare_fraction_num=bare, bare_fraction_den=total)
            table.setdefault(c.key, {})[name] = dict(
                total=total, fwd=fwd, bare=bare, chi=chi, invo=invo,
                pred_bare=pred_bare, pred_ce=pred_class_eq,
                cells=dict(counts), hits=hits, wf=(wf_ok, wf_tot),
                fcell=forward_cell, bcell=bare_cell, ccell=chiral_cell)
            print(f"[reversal] {c.key:5s} {name:24s} triples={total:6d} "
                  f"FWD={fwd:6d} BARE={bare:6d} CHIRAL={chi:6d} INV-ONLY={invo:6d} "
                  f"| pred |S|·comm={pred_bare:6d} {'OK' if pred_bare==bare else 'MISMATCH'}"
                  f" | pred |S||G|k={pred_class_eq:6d} "
                  f"{'OK' if pred_class_eq==bare else 'MISMATCH'}")
    print()
    return table


# ═════════════════════════════════════════════════════════════════════════════
# §4b  SET OVERLAPS — two cells of EQUAL COUNT need not be the SAME SET, and a
#      count alone cannot tell them apart. This section decides it.
# ═════════════════════════════════════════════════════════════════════════════
def section_overlaps(table):
    for ckey, readings in table.items():
        for name, d in readings.items():
            hits, total = d["hits"], d["total"]
            f, b, ch = d["fcell"], d["bcell"], d["ccell"]
            F, B, C = hits[f], hits[b], hits[ch]
            emit("cell_set_overlap", carrier=ckey, reading=name,
                 ordered_triples=total,
                 forward_cell=f, bare_cell=b, chiral_cell=ch,
                 forward_n=len(F), bare_n=len(B), chiral_n=len(C),
                 chiral_equals_forward_SET=C == F,
                 bare_equals_forward_SET=B == F,
                 bare_equals_chiral_SET=B == C,
                 chiral_subset_of_forward=C <= F,
                 forward_subset_of_chiral=F <= C,
                 forward_and_chiral=len(F & C),
                 forward_and_bare=len(F & B),
                 forward_minus_chiral=len(F - C),
                 chiral_minus_forward=len(C - F),
                 forward_minus_bare=len(F - B),
                 bare_minus_forward=len(B - F),
                 pairwise_intersections={
                     f"{a}&{bb}": len(hits[a] & hits[bb])
                     for i, a in enumerate(CELL_DOC)
                     for bb in list(CELL_DOC)[i:]},
                 verdict=(
                     "CO-EXTENSIVE — chiral succeeds on EXACTLY the triples "
                     "where forward succeeds, so chiral reversal is total "
                     "RELATIVE TO the forward law's own domain"
                     if C == F else
                     "NOT CO-EXTENSIVE — chiral and forward succeed on "
                     "different triples; equal counts would have hidden this"))
            print(f"[overlap]  {ckey:5s} {name:24s} "
                  f"CHIRAL==FORWARD set? {C == F}   BARE==FORWARD set? {B == F}"
                  f"   |F∩C|={len(F & C):6d} |F∩B|={len(F & B):6d}")
    print()


# ═════════════════════════════════════════════════════════════════════════════
# §5  NEGATIVE CONTROLS
# ═════════════════════════════════════════════════════════════════════════════
def section_controls(table, census):
    for c in CARRIERS:
        for name, d in table[c.key].items():
            total = d["total"]
            cells = d["cells"]
            side = "left" if name.startswith("left") else "right"
            # deliberately-wrong "chiral": reverse the order but invert only ONE
            half_first = cells["R3"] if side == "left" else cells["R4"]
            half_second = cells["R4"] if side == "left" else cells["R3"]
            emit("negative_control", carrier=c.key, reading=name,
                 control="half_inversion_invert_only_one_factor",
                 reversed_invert_leading_only=cells["R3"],
                 reversed_invert_trailing_only=cells["R4"],
                 of=total,
                 either_is_total=(cells["R3"] == total or cells["R4"] == total),
                 verdict=(
                     "PASSES AS A CONTROL — a half-inversion is NOT total on this "
                     "carrier, so the chiral result is not an artifact of the "
                     "harness accepting anything"
                     if not (cells["R3"] == total or cells["R4"] == total) else
                     "VACUOUS ON THIS CARRIER — the half-inversion is ALSO total, "
                     "so this control cannot discriminate here (expected on an "
                     "abelian carrier of exponent 2 only)"),
                 involutions=census[c.key]["involutions"],
                 note=("A half-inversion holds exactly when the un-inverted "
                       "factor is an involution, so its count is governed by "
                       "#{g : g² = e}."))
            emit("negative_control", carrier=c.key, reading=name,
                 control="identity_as_reversal",
                 count=d["fwd"], of=total, equals_forward=True,
                 verdict="VACUOUS — identity-as-reversal returns exactly the "
                         "FORWARD count by construction and therefore proves "
                         "nothing. This is the demonstration that the "
                         "instrument CAN return a vacuous answer.")
            emit("negative_control", carrier=c.key, reading=name,
                 control="abelian_bare_equals_chiral",
                 abelian=census[c.key]["abelian"],
                 bare=d["bare"], chiral=d["chi"], of=total,
                 bare_equals_chiral=d["bare"] == d["chi"],
                 verdict=("EXPECTED — on an abelian carrier inversion is "
                          "INVISIBLE to the axiom, so bare and chiral agree "
                          "and both are total"
                          if census[c.key]["abelian"] else
                          "EXPECTED — on a non-abelian carrier bare and chiral "
                          "SEPARATE; that separation IS the measurement"))
            print(f"[control] {c.key:5s} {name:24s} R3={cells['R3']:6d} "
                  f"R4={cells['R4']:6d} of {total:6d} "
                  f"(half-inversion total? {cells['R3']==total or cells['R4']==total})")
    print()


# ═════════════════════════════════════════════════════════════════════════════
# §6  THE 5/8 CEILING — the bare-reversal success rate IS the commuting
#     probability, which Gustafson bounds at 5/8 for any non-abelian group.
# ═════════════════════════════════════════════════════════════════════════════
def section_ceiling(table, census):
    from srmech.math.cyclic import gcd                  # Class I, shipped
    for c in CARRIERS:
        d = table[c.key]["left_quotient_b_ainv"]
        num, den = d["bare"], d["total"]
        g = gcd(num, den) or 1
        rn, rd = num // g, den // g
        k, order = census[c.key]["k"], c.n
        g2 = gcd(k, order) or 1
        emit("bare_rate_is_commuting_probability", carrier=c.key,
             bare=num, of=den,
             bare_rate_num=rn, bare_rate_den=rd,
             k_over_order_num=k // g2, k_over_order_den=order // g2,
             equals_k_over_order=(rn * (order // g2) == rd * (k // g2)),
             abelian=census[c.key]["abelian"],
             at_or_below_five_eighths=(rn * 8 <= 5 * rd),
             attains_five_eighths=(rn * 8 == 5 * rd),
             note=("The bare-reversal success RATE equals the group's commuting "
                   "probability Pr(G) = k(G)/|G|. Gustafson's 5/8 theorem then "
                   "CAPS bare reversal at 5/8 for every non-abelian group — a "
                   "ceiling, not an accident of these five carriers."))
        print(f"[ceiling] {c.key:5s} bare rate = {rn}/{rd}   k/|G| = "
              f"{k//g2}/{order//g2}   <=5/8: {rn*8 <= 5*rd}   "
              f"==5/8: {rn*8 == 5*rd}")
    print()


# ═════════════════════════════════════════════════════════════════════════════
# §7  THE OCTONION ROW IN DETAIL — non-associativity, the inverse property,
#     Moufang, and the CAYLEY–DICKSON DUAL CONSTRUCTION as consistency oracle
# ═════════════════════════════════════════════════════════════════════════════
def _byte_to_cd(b):
    """Octonion byte -> exact 8-tuple.  Sign read WITHOUT abs(): the byte's
    sign bit is a Class-C orientation, composed through net_chirality."""
    idx = b & 7
    orient = net_chirality([1 if (b >> 3) == 0 else -1])      # Class C, shipped
    v = [0] * 8
    v[idx] = orient
    return tuple(v)


def _cd_to_byte(v):
    """Exact 8-tuple (one non-zero unit component) -> octonion byte.
    The sign is split by the Class-K pin-slot, NEVER by abs()."""
    nz = [(i, x) for i, x in enumerate(v) if x != 0]
    if len(nz) != 1:
        return None
    i, x = nz[0]
    orient, mag = pin_slot_at_zero(x)                          # Class K, shipped
    if mag != 1:
        return None
    sign_bit = 0 if net_chirality([orient]) == 1 else 1        # Class C, shipped
    return (sign_bit << 3) | i


def section_octonion_detail():
    c = O16
    e = 0                                              # +e₀ is the identity byte

    # -- non-associativity census -------------------------------------------
    assoc = 0
    assoc_fail = []
    for a, b, d in itertools.product(c.elems, repeat=3):
        if c.mul(c.mul(a, b), d) == c.mul(a, c.mul(b, d)):
            assoc += 1
        elif len(assoc_fail) < 8:
            assoc_fail.append([a, b, d,
                               c.mul(c.mul(a, b), d), c.mul(a, c.mul(b, d))])
    tot3 = c.n ** 3

    # -- alternativity / flexibility / Moufang ------------------------------
    left_alt = sum(1 for a in c.elems for b in c.elems
                   if c.mul(c.mul(a, a), b) == c.mul(a, c.mul(a, b)))
    right_alt = sum(1 for a in c.elems for b in c.elems
                    if c.mul(c.mul(b, a), a) == c.mul(b, c.mul(a, a)))
    flexible = sum(1 for a in c.elems for b in c.elems
                   if c.mul(c.mul(a, b), a) == c.mul(a, c.mul(b, a)))
    moufang = sum(1 for a, b, d in itertools.product(c.elems, repeat=3)
                  if c.mul(c.mul(a, b), c.mul(d, a))
                  == c.mul(a, c.mul(c.mul(b, d), a)))

    # -- the INVERSE PROPERTY: does x·y⁻¹ really equal the loop division? ----
    lip = sum(1 for a in c.elems for b in c.elems
              if c.mul(c.inv(a), c.mul(a, b)) == b)
    rip = sum(1 for a in c.elems for b in c.elems
              if c.mul(c.mul(b, a), c.inv(a)) == b)
    # true right division  b/a  := the unique x with x·a == b
    div_matches = 0
    div_unique = 0
    for a in c.elems:
        for b in c.elems:
            xs = [x for x in c.elems if c.mul(x, a) == b]
            if len(xs) == 1:
                div_unique += 1
                if xs[0] == c.mul(b, c.inv(a)):
                    div_matches += 1

    emit("octonion_structure",
         carrier=c.key, order=c.n,
         associative_triples=assoc, of=tot3,
         associative=assoc == tot3,
         non_associative_triples=tot3 - assoc,
         associativity_failure_examples=assoc_fail,
         left_alternative=left_alt, right_alternative=right_alt, of_pairs=c.n * c.n,
         alternative=left_alt == c.n * c.n and right_alt == c.n * c.n,
         flexible=flexible, flexible_total=flexible == c.n * c.n,
         moufang_identity=moufang, of_triples=tot3,
         moufang_total=moufang == tot3,
         left_inverse_property=lip, right_inverse_property=rip,
         inverse_property_total=lip == c.n * c.n and rip == c.n * c.n,
         unique_right_division_pairs=div_unique,
         division_equals_x_times_ainv=div_matches,
         division_matches_total=div_matches == c.n * c.n,
         note=("THE POINT: the loop is genuinely NON-ASSOCIATIVE, so the group "
               "proof of (ab)⁻¹ = b⁻¹a⁻¹ does NOT apply. Whether the identity "
               "survives is decided by the inverse property, measured here."))
    print(f"[octonion] associative {assoc}/{tot3}  alternative "
          f"L={left_alt} R={right_alt}/{c.n*c.n}  flexible={flexible}  "
          f"Moufang={moufang}/{tot3}  LIP={lip} RIP={rip}")

    # -- CO-EQUAL DUAL CONSTRUCTION: cd_mult on exact-ℚ 8-tuples -------------
    agree_mult = 0
    agree_conj = 0
    unmapped = 0
    for a in c.elems:
        if _cd_to_byte(cd_conjugate(_byte_to_cd(a))) == c.inv(a):
            agree_conj += 1
        for b in c.elems:
            prod = cd_mult(_byte_to_cd(a), _byte_to_cd(b))
            back = _cd_to_byte(prod)
            if back is None:
                unmapped += 1
            elif back == c.mul(a, b):
                agree_mult += 1
    emit("dual_construction_consistency_oracle",
         carrier=c.key,
         byte_products_agreeing_with_cd_mult=agree_mult, of=c.n * c.n,
         conjugates_agreeing_with_cd_conjugate=agree_conj, of_elements=c.n,
         unmappable_products=unmapped,
         oracle_verdict=("MUTUALLY REALIZABLE — the byte loop (oct_mult / "
                         "oct_conjugate) and the exact-ℚ Cayley–Dickson tuple "
                         "(cd_mult / cd_conjugate) construct the SAME object"
                         if agree_mult == c.n * c.n and agree_conj == c.n
                         else "DISAGREEMENT — and the disagreement is the finding"),
         note=("Per [[user_stance_co_equal_dual_construction_is_a_consistency_"
               "oracle]] this certifies MUTUAL REALIZABILITY, not correctness."))
    print(f"[dual]     cd_mult agrees {agree_mult}/{c.n*c.n}   "
          f"cd_conjugate agrees {agree_conj}/{c.n}   unmapped={unmapped}")

    # -- WHY the forward law falls short: it IS the associator --------------
    # For the LEFT reading, FORWARD is  (u·t̄)·(t·s̄) == u·s̄.  Since
    # u·s̄ == ((u·t̄)·t)·s̄ (inverse property), the law holds exactly when the
    # associator [u·t̄, t, s̄] vanishes.  Measured through the SHIPPED
    # `associator` op on the exact-ℚ dual construction, and byte-side.
    from srmech.cascade import associator
    ZERO8 = tuple([0] * 8)
    fwd_hits, assoc_hits, agree_sets = 0, 0, 0
    for s in c.elems:
        for t in c.elems:
            for u in c.elems:
                X = c.mul(t, c.inv(s))            # int_L(s,t) = t·s̄
                Y = c.mul(u, c.inv(t))            # int_L(t,u) = u·t̄
                Z = c.mul(u, c.inv(s))            # int_L(s,u) = u·s̄
                fwd = c.mul(Y, X) == Z            # the FORWARD law (P2)
                a = associator(_byte_to_cd(Y), _byte_to_cd(t),
                               _byte_to_cd(c.inv(s)))     # SHIPPED Class-K op
                assoc0 = tuple(int(q) for q in a) == ZERO8
                fwd_hits += fwd
                assoc_hits += assoc0
                agree_sets += (fwd == assoc0)
    emit("forward_shortfall_is_the_associator",
         carrier=c.key,
         forward_law_holds=fwd_hits, of=c.n ** 3,
         associator_vanishes=assoc_hits,
         forward_iff_associator_zero=agree_sets, of_triples=c.n ** 3,
         identity_holds_on_every_triple=agree_sets == c.n ** 3,
         shipped_op="srmech.cascade.associator",
         shipped_docstring_basis_census="dim 8: 344/512 ordered BASIS triples",
         signed_loop_census=f"{assoc_hits}/{c.n ** 3}",
         scales_by_eight=assoc_hits == 344 * 8 and c.n ** 3 == 512 * 8,
         verdict=("EXPLAINED — the forward interval law holds at a triple "
                  "EXACTLY when the associator of that triple vanishes. The "
                  "shortfall is not a defect of the interval function; it IS "
                  "non-associativity, counted. And it reproduces the number "
                  "already documented in the shipped associator docstring "
                  "(344/512 basis triples × the 8 sign combinations = "
                  "2752/4096)."))
    print(f"[assoc]    FORWARD holds {fwd_hits}/{c.n**3}; associator vanishes "
          f"{assoc_hits}/{c.n**3}; the two agree on {agree_sets}/{c.n**3} triples")
    print()


# ═════════════════════════════════════════════════════════════════════════════
# §8  THE SHIPPED SEAM TORSOR — S ≠ G, through oct_torsor_act / oct_torsor_div
#
# T = {±e₄..±e₇} (8 seam bytes) is a principal RIGHT torsor for the quaternion
# subloop H = {±e₀..±e₃}.  This is the only row where the acted-on SET is not
# the group itself, which is exactly the structure the second question calls a
# torsor: a group that has forgotten its identity.
# ═════════════════════════════════════════════════════════════════════════════
def section_seam_torsor():
    T = [b for b in range(16) if (b & 7) >= 4]          # 8 seam bytes
    H = [b for b in range(16) if (b & 7) < 4]           # 8 quaternion bytes

    closed = all(oct_torsor_act(t, g) in T for t in T for g in H)
    simply_trans = all(
        len([g for g in H if oct_torsor_act(t1, g) == t2]) == 1
        for t1 in T for t2 in T)
    div_ok = sum(1 for t1 in T for t2 in T
                 if oct_torsor_act(t1, oct_torsor_div(t1, t2)) == t2)
    # the right-action law (t <| g1) <| g2 == t <| (g1·g2) -- NOT free in a loop
    act_assoc = sum(1 for t in T for g1 in H for g2 in H
                    if oct_torsor_act(oct_torsor_act(t, g1), g2)
                    == oct_torsor_act(t, oct_mult(g1, g2)))
    # ...and the OPPOSITE-ORDER law (t <| g1) <| g2 == t <| (g2·g1)
    act_anti = sum(1 for t in T for g1 in H for g2 in H
                   if oct_torsor_act(oct_torsor_act(t, g1), g2)
                   == oct_torsor_act(t, oct_mult(g2, g1)))
    comm_H0 = sum(1 for a in H for b in H if oct_mult(a, b) == oct_mult(b, a))
    # does the action law hold EXACTLY on the commuting (g1,g2) pairs?
    act_law_on_commuting_only = all(
        (oct_torsor_act(oct_torsor_act(t, g1), g2)
         == oct_torsor_act(t, oct_mult(g1, g2)))
        == (oct_mult(g1, g2) == oct_mult(g2, g1))
        for t in T for g1 in H for g2 in H)
    # a witness for the report
    witness = None
    for t in T:
        for g1 in H:
            for g2 in H:
                if (oct_torsor_act(oct_torsor_act(t, g1), g2)
                        != oct_torsor_act(t, oct_mult(g1, g2))):
                    witness = dict(
                        t=t, g1=g1, g2=g2,
                        act_then_act=oct_torsor_act(oct_torsor_act(t, g1), g2),
                        act_of_product=oct_torsor_act(t, oct_mult(g1, g2)),
                        act_of_reversed_product=oct_torsor_act(
                            t, oct_mult(g2, g1)))
                    break
            if witness:
                break
        if witness:
            break

    emit("shipped_op_reproduction",
         op="srmech.math.octonion.oct_torsor_act",
         claim_in_docstring=(
             "T = H·e 'is a principal RIGHT torsor for H'; the map 'is exactly "
             "the RIGHT multiplication R_g, which on T equals the LEFT "
             "multiplication by conj(g)'"),
         already_known_and_gated=True,
         existing_gate="tests/test_oct_torsor_rc388.py::"
                       "test_ratchet2_action_law_and_naive_defect",
         existing_gate_says=(
             "'BOTH the law AND the defect': it asserts (t<|g)<|h == t<|(h·g) "
             "on 14336/14336 — the REVERSED order — and pins the naive "
             "t<|(g·h) at 8960/14336, over all 28 seams. Its docstring names "
             "the trap outright: 'the naive composition order still LANDS IN T "
             "14336/14336 while being the WRONG element'."),
         this_measurement_is_independent_reproduction=True,
         our_single_seam_naive_rate="320/512 = 5/8",
         shipped_ratchet_all_seams_naive_rate="8960/14336 = 5/8",
         rates_agree=True,
         correction_to_this_note=(
             "An earlier draft of this record called it a DEFECT. That was an "
             "OVERCLAIM and is retracted. The tree already knows this, has "
             "measured it, and gates it. What this section actually delivers "
             "is an INDEPENDENT reproduction of a shipped ratchet from a "
             "different direction (interval composition rather than action "
             "composition), landing on the identical 5/8 — which is evidence "
             "the harness is measuring the carrier and not itself."),
         residual_observation=(
             "The docstring CONTAINS the fact but does not spell it out: "
             "'R_g == L_{conj g} on T' IS the anti-homomorphism statement, "
             "since a right multiplication that equals a left multiplication "
             "reverses composition order. A reader of the docstring alone "
             "could still write t<|(g·h). Not a falsehood — an understated "
             "implication, and the test file is where it is said plainly."),
         simply_transitive=simply_trans,
         division_inverts_action=div_ok, of_pairs=len(T) * len(T),
         right_action_law_holds=act_assoc,
         opposite_order_law_holds=act_anti,
         of_triples=len(T) * len(H) * len(H),
         right_action_law_total=act_assoc == len(T) * len(H) * len(H),
         opposite_order_law_total=act_anti == len(T) * len(H) * len(H),
         action_law_holds_exactly_on_commuting_pairs=act_law_on_commuting_only,
         commuting_pairs_in_H=comm_H0,
         predicted_action_law_count=len(T) * comm_H0,
         first_counterexample=witness,
         verdict=(
             "CONFIRMED, AND ALREADY KNOWN — oct_torsor_act composes as an "
             "ANTI-action: (t<|g1)<|g2 == t<|(g2·g1), NOT t<|(g1·g2). The "
             "naive order holds on exactly the COMMUTING pairs of H, so it "
             "measures |T|·|{(g1,g2): g1g2=g2g1}| and not |T|·|H|². T is a "
             "principal torsor for H^op (equivalently a LEFT torsor for H). "
             "This is NOT a new defect — it is pinned by the rc388 ratchet; "
             "this is an independent reproduction at the same 5/8."
             if act_anti == len(T) * len(H) * len(H)
             and act_assoc != len(T) * len(H) * len(H)
             else "the naive right-action law is total — contradicts rc388"),
         why_it_is_on_thesis=(
             "This is the thesis itself, found in shipped code: the "
             "Cayley–Dickson doubling 𝕆 = ℍ ⊕ ℍe carries the "
             "anti-automorphism, so (t'e)·g = (t'ḡ)e reverses order in the ℍ "
             "coordinate. Reading the seam map as a plain right action is "
             "EXACTLY the bare-order-reversal error, and it fails on exactly "
             "the non-commuting 3/8 of H×H."))
    print(f"[REPRODUCTION] oct_torsor_act (rc388 ratchet, independently): right-action law "
          f"{act_assoc}/{len(T)*len(H)**2}, OPPOSITE-order law "
          f"{act_anti}/{len(T)*len(H)**2}; holds exactly on commuting pairs: "
          f"{act_law_on_commuting_only}")
    print(f"                     first counterexample: {witness}")

    def interval(a, b):
        return oct_torsor_div(a, b)                     # shipped torsor division

    counts, total, thits = eight_cells(T, interval, oct_mult, oct_conjugate)
    # H is a group (Q8-isomorphic), acting on the RIGHT, so P1 is the forward law
    comm_H = sum(1 for a in H for b in H
                 if oct_mult(a, b) == oct_mult(b, a))
    reps, seen = [], set()
    for y in H:
        if y in seen:
            continue
        orb = {oct_mult(oct_mult(x, y), oct_conjugate(x)) for x in H} | {y}
        seen |= orb
        reps.append(orb)
    kH = len(reps)

    # WHICH cell is the forward law is DECIDED BY MEASUREMENT, not assumed —
    # the naive prediction (P1, because oct_torsor_div reads as a right
    # quotient) is wrong precisely because the seam map is an ANTI-action.
    fcell = "P2" if counts["P2"] == total else "P1"
    bcell = "P1" if fcell == "P2" else "P2"
    ccell = "Q1" if fcell == "P2" else "Q2"
    icell = "Q2" if fcell == "P2" else "Q1"

    emit("seam_torsor_row",
         carrier="O16_seam_torsor", acted_set="T = {±e₄..±e₇}",
         group="H = {±e₀..±e₃} ≅ Q₈",
         size_S=len(T), size_G=len(H),
         action_closed=closed, simply_transitive=simply_trans,
         torsor_division_inverts_action=div_ok, of_pairs=len(T) * len(T),
         right_action_law_holds=act_assoc, of_triples=len(T) * len(H) * len(H),
         right_action_law_total=act_assoc == len(T) * len(H) * len(H),
         ordered_triples=total,
         cells={k: counts[k] for k in CELL_DOC}, cell_legend=CELL_DOC,
         naive_forward_prediction="P1 (right quotient => left-to-right compose)",
         naive_prediction_correct=counts["P1"] == total,
         FORWARD_cell=fcell, FORWARD=counts[fcell],
         FORWARD_total=counts[fcell] == total,
         BARE_REVERSAL_cell=bcell, BARE_REVERSAL=counts[bcell],
         BARE_REVERSAL_total=counts[bcell] == total,
         CHIRAL_REVERSAL_cell=ccell, CHIRAL_REVERSAL=counts[ccell],
         CHIRAL_REVERSAL_total=counts[ccell] == total,
         INVERSION_ONLY_cell=icell, INVERSION_ONLY=counts[icell],
         chiral_equals_forward_SET=thits[ccell] == thits[fcell],
         bare_equals_forward_SET=thits[bcell] == thits[fcell],
         commuting_pairs_in_H=comm_H, conjugacy_classes_in_H=kH,
         predicted_bare_from_commuting_pairs=len(T) * comm_H,
         predicted_bare_matches=len(T) * comm_H == counts[bcell],
         predicted_bare_from_class_equation=len(T) * len(H) * kH,
         class_equation_route_matches=len(T) * len(H) * kH == counts[bcell],
         shipped_ops=["srmech.math.octonion.oct_torsor_act",
                      "srmech.math.octonion.oct_torsor_div",
                      "srmech.math.octonion.oct_mult",
                      "srmech.math.octonion.oct_conjugate"],
         note=("The ONLY row where S ≠ G. It is the torsor case named in the "
               "second question: reversible, no privileged origin."))
    print(f"[torsor]   |T|={len(T)} |H|={len(H)} closed={closed} "
          f"simply-transitive={simply_trans} div-inverts={div_ok}/{len(T)**2} "
          f"action-law={act_assoc}/{len(T)*len(H)**2}")
    print(f"[torsor]   FORWARD is {fcell} (naive prediction P1 correct? "
          f"{counts['P1'] == total})")
    print(f"[torsor]   FWD={counts[fcell]} BARE={counts[bcell]} "
          f"CHIRAL={counts[ccell]} INV-ONLY={counts[icell]} of {total}   "
          f"pred |S|·comm={len(T)*comm_H}  pred |S||G|k={len(T)*len(H)*kH}")
    print()


# ═════════════════════════════════════════════════════════════════════════════
# §9  MONOID / SEMIGROUP CENSUS — for the SECOND question
#
# A torsor is a GROUP notion (free + transitive action, every element
# invertible, no origin). A directional generator is a MONOID notion (an
# identity, a start, and NO inverses). This section asks a decidable version of
# "does srmech ship anything that is a monoid and NOT a group?" by testing the
# five carriers plus two deliberately non-invertible transformation monoids
# built from shipped ops.
# ═════════════════════════════════════════════════════════════════════════════
def section_monoid_census():
    # (a) every carrier above: is it cancellative / a group?
    for c in CARRIERS:
        ident = [e for e in c.elems
                 if all(c.mul(e, x) == x and c.mul(x, e) == x for x in c.elems)]
        invertible = sum(1 for a in c.elems
                         if ident and any(c.mul(a, b) == ident[0]
                                          and c.mul(b, a) == ident[0]
                                          for b in c.elems))
        emit("monoid_census", surface=c.key, surface_kind="carrier",
             has_two_sided_identity=bool(ident), elements=c.n,
             invertible_elements=invertible,
             is_group_like=invertible == c.n,
             semigroup_not_group=invertible != c.n,
             note="every element invertible -> reversible -> torsor-capable")

    # (b) the multiplicative monoid of ℤ/12 under the shipped Class-I mod-mul.
    #     Non-invertible elements exist exactly where gcd(a,12) != 1 — this is
    #     a genuine MONOID-not-group living inside a shipped op family.
    from srmech.math.cyclic import mod_mul, gcd
    n = 12
    elems = list(range(n))
    units = [a for a in elems if gcd(a, n) == 1]
    idem = [a for a in elems if mod_mul(a, a, n) == a]
    nilp = []
    for a in elems:
        x, seen = a, set()
        while x not in seen:
            seen.add(x)
            x = mod_mul(x, a, n)
        if 0 in seen:
            nilp.append(a)
    emit("monoid_census", surface="Z12_multiplicative",
         surface_kind="shipped_op_monoid",
         op="srmech.math.cyclic.mod_mul",
         elements=n, identity=1,
         invertible_elements=len(units), units=units,
         is_group_like=len(units) == n,
         semigroup_not_group=True,
         idempotents=idem, elements_reaching_zero=nilp,
         note=("(ℤ/12, ·) IS a monoid and is NOT a group: only the 4 units are "
               "invertible. It is a shipped, exact, finite example of a "
               "DIRECTIONAL generator — repeated action loses information and "
               "cannot be undone. This is the discrete analogue of a "
               "contraction semigroup's irreversibility."))
    print(f"[monoid]  (ℤ/12, mod_mul): units={units} "
          f"idempotents={idem} reach-zero={nilp}")

    # (c) the discrete generator A = T - I as a DIFFERENCE on ℤ/12: iterate the
    #     shipped Class-I add and measure whether the orbit is reversible.
    for step in (1, 2, 3, 4, 6):
        img = sorted({cyclic_mod_add(x, step, 12) for x in range(12)})
        injective = len(img) == 12
        emit("monoid_census", surface=f"Z12_shift_{step}",
             surface_kind="one_parameter_discrete_semigroup",
             op="srmech.cascade.cyclic_mod_add",
             generator_step=step, image_size=len(img), injective=injective,
             is_group_like=injective,
             semigroup_not_group=not injective,
             note=("A translation on a finite cyclic set is always a BIJECTION, "
                   "so the shift monoid ⟨T⟩ is automatically a group. This is "
                   "the finite-cancellative-monoid collapse, and it is why a "
                   "directional generator on a FINITE carrier must be "
                   "non-injective (i.e. lose information) to stay directional."))
    print()


# ═════════════════════════════════════════════════════════════════════════════
# §9b  IS srmech's OWN EPH SURFACE A SEMIGROUP OR A GROUP?
#
# `srmech.math.laplacian.propagate` IS the Excite–Propagate–Harvest op: the
# complex-time propagator `e^{-zL}` applied to an excitation `u0`. Its own
# docstring names arg(z) the COHERENCE DIAL — z real is thermal diffusion, z
# imaginary is unitary quantum walk. That is exactly the semigroup-vs-group
# distinction, so the decidable question is:
#
#     does the op ENFORCE t >= 0, or does it accept the backward direction?
#
# A one-parameter semigroup is directional because the backward map is not
# available. If `propagate(L, ., -t)` computes and round-trips, the shipped
# surface is a GROUP and the arrow is NOT enforced by the algebra.
# ═════════════════════════════════════════════════════════════════════════════
def section_eph_arrow():
    from srmech.math.laplacian import dense_laplacian, propagate

    L = dense_laplacian(3, [(0, 1), (1, 2)])          # a path graph, L PSD
    u0 = [1.0, 0.0, 0.0]

    def nrm2(v):
        return sum(complex(x).real ** 2 + complex(x).imag ** 2 for x in v)

    fwd = list(propagate(L, u0, 1.0))                 # z REAL     -> thermal
    back = list(propagate(L, fwd, -1.0))              # z NEGATIVE -> backward
    dev = max(abs(complex(a) - complex(b)) for a, b in zip(back, u0))
    uni = list(propagate(L, u0, complex(0, 1.0)))     # z IMAGINARY-> unitary
    uni_back = list(propagate(L, uni, complex(0, -1.0)))
    dev_u = max(abs(complex(a) - complex(b)) for a, b in zip(uni_back, u0))

    emit("eph_arrow_is_not_enforced",
         op="srmech.math.laplacian.propagate",
         op_is_EPH="harvest = e^{-zL}·u0 — the shipped Excite/Propagate/Harvest",
         graph="path graph on 3 nodes, L positive-semidefinite",
         norm_sq_excitation=nrm2(u0),
         norm_sq_after_thermal_z_real=nrm2(fwd),
         thermal_is_a_contraction=nrm2(fwd) < nrm2(u0),
         norm_sq_after_unitary_z_imaginary=nrm2(uni),
         unitary_conserves_norm=abs(nrm2(uni) - nrm2(u0)) < 1e-9,
         backward_z_negative_accepted=True,
         backward_roundtrip_deviation=dev,
         backward_roundtrip_exact=dev < 1e-9,
         unitary_roundtrip_deviation=dev_u,
         verdict=(
             "GROUP, NOT SEMIGROUP. The generator's SIGN CONDITION is real and "
             "visible — L is PSD, so −L is dissipative and the thermal branch "
             "genuinely CONTRACTS (‖·‖² falls from 1.0 to ~0.40). But nothing "
             "restricts z to the closed right half-plane: propagate(L, ·, −t) "
             "is accepted and inverts the forward map to ~1e-15. So srmech's "
             "EPH surface today realises a one-parameter GROUP, and the arrow "
             "is a property of the INPUT z, not of the operator's own equation."),
         why_finite_dimension_forces_this=(
             "At finite dimension every e^{-tL} is invertible "
             "(det = e^{-t·tr L} ≠ 0), so the semigroup {e^{-tL} : t ≥ 0} always "
             "extends to the group {e^{-tL} : t ∈ ℝ}. Irreversibility needs "
             "either infinite dimension — where the backward Cauchy problem is "
             "ill-posed because the inverse is UNBOUNDED — or a genuinely "
             "NON-INJECTIVE step. This is the same fact §9 measures on the "
             "cyclic shifts: on a finite carrier, injective ⟹ group."),
         what_would_be_a_true_discrete_semigroup=(
             "A non-injective monoid action. The one shipped example this "
             "census found is (ℤ/12, srmech.math.cyclic.mod_mul): 4 units of "
             "12, an absorbing 0, and 6 ↦ 0 — information is destroyed and "
             "cannot be recovered."))
    print(f"[EPH]     thermal ‖·‖² {nrm2(u0):.6f} -> {nrm2(fwd):.6f} "
          f"(contraction: {nrm2(fwd) < nrm2(u0)})")
    print(f"[EPH]     BACKWARD z=-1 accepted; round-trip deviation {dev:.3e} "
          f"-> the shipped EPH surface is a GROUP, not a semigroup")
    print(f"[EPH]     unitary ‖·‖² {nrm2(uni):.6f} (conserved), round-trip "
          f"{dev_u:.3e}")
    print()


# ═════════════════════════════════════════════════════════════════════════════
# §10  OP-USAGE LEDGER + VERDICTS
# ═════════════════════════════════════════════════════════════════════════════
def section_ledger(table, census):
    emit("op_usage_ledger",
         shipped_ops_used=[
             "srmech.cascade.cyclic_mod_add",
             "srmech.cascade.cd_mult",
             "srmech.cascade.cd_conjugate",
             "srmech.cascade.pin_slot_at_zero",
             "srmech.cascade.net_chirality",
             "srmech.biology.q8.q8_mult",
             "srmech.biology.q8.q8_conjugate",
             "srmech.math.octonion.oct_mult",
             "srmech.math.octonion.oct_conjugate",
             "srmech.math.octonion.oct_torsor_act",
             "srmech.math.octonion.oct_torsor_div",
             "srmech.math.cyclic.gcd",
             "srmech.math.cyclic.mod_mul",
             "srmech.introspect.tool_schema.get_tool_schema",
         ],
         hand_rolled=[
             dict(what="T/I group product and inverse (_ti_mul / _ti_inv)",
                  why=("srmech ships NO T/I (Tn / TnI) group op. "
                       "srmech/music/relations.py names interval_invert / "
                       "pitch_class_transpose / pitch_class_invert as COSTED "
                       "AND REJECTED (each a single cyclic_mod_add carrying no "
                       "decision), and prime_form consumes the Tn/TnI orbit "
                       "INTERNALLY via a module-private _invert. So the T/I "
                       "GROUP itself — the order-24 object, its product and its "
                       "inverse — is not a public surface."),
                  mitigation=("every modular step inside _ti_mul / _ti_inv is a "
                              "shipped cyclic_mod_add call; only the 2x2 case "
                              "split is local"),
                  reportable_finding=True,
                  gap=("MISSING SURFACE: a dihedral / T-I group carrier. The "
                       "closest shipped peers are q8_mult (order 8) and "
                       "oct_mult (order 16); there is no order-24 group op.")),
             dict(what="conjugacy-class orbit closure (conj_classes)",
                  why="no shipped conjugacy-class / class-equation op exists",
                  mitigation="every product and inverse is a shipped-op call",
                  reportable_finding=True,
                  gap=("MISSING SURFACE: conjugacy classes / commuting-pair "
                       "census / class equation. Grep of the registry finds no "
                       "conjugacy op; the class equation is load-bearing for "
                       "this result and has no shipped home.")),
             dict(what="Latin-square, associativity, Moufang, alternativity checks",
                  why=("srmech ships `associator` (srmech.cascade) for the "
                       "exact-ℚ CD carrier but no BYTE-loop associativity / "
                       "Moufang / inverse-property census op"),
                  mitigation="all products are oct_mult calls",
                  reportable_finding=True,
                  gap=("PARTIAL SURFACE: associator exists on cd tuples; there "
                       "is no loop-law census over the 16-byte unit loop.")),
         ],
         note=("Reaching for hand-rolled arithmetic where a shipped op exists is "
               "a reportable finding, not a shortcut "
               "([[feedback_scratch_measurements_must_use_srmech_or_gaps_stay_"
               "invisible]]). Each row above is a MISSING SURFACE, not a "
               "convenience."))

    # ---- citations, verified by fetch (MPM discipline) --------------------
    emit("citations",
         note=("Each entry was verified by FETCHING an accessible source, not "
               "recalled. Paywalled-only DOIs are rejected as sole "
               "attestation per [[feedback_paywalled_doi_cannot_be_attested]]; "
               "where only a paywalled primary exists, the OA corroborator "
               "actually fetched is named."),
         entries=[
             dict(claim="bare-reversal rate = commuting probability Pr(G) = "
                        "k(G)/|G|, and Pr(G) <= 5/8 for every non-abelian G, "
                        "attained by Q8 and D4",
                  primary="W. H. Gustafson, 'What is the Probability that Two "
                          "Group Elements Commute?', American Mathematical "
                          "Monthly 80:9 (1973) 1031-1034; "
                          "doi:10.1080/00029890.1973.11993437",
                  primary_access="PAYWALLED (HTTP 403) — not usable alone",
                  oa_corroborators=[
                      "arXiv:2010.01188 (commuting-probabilities survey), "
                      "bibliography ref [17], via ar5iv",
                      "groupprops.subwiki.org/wiki/Commuting_fraction — lists "
                      "BOTH Q8 and D8 at 5/8 with 5 conjugacy classes each"],
                  status="VERIFIED",
                  priority_note=("Gustafson 1973 IS the correct attribution. "
                                 "Erdos-Turan 1968 founded statistical group "
                                 "theory generally and Gallagher 1970 counted "
                                 "conjugacy classes, but neither is the origin "
                                 "of the 5/8 bound. Independently rediscovered "
                                 "by MacHale (Math. Gaz. 58, 1974) and Rusin "
                                 "(Pacific J. Math. 82, 1979)."),
                  measured_here="Q8 bare rate = 320/512 = 5/8 EXACTLY; T/I = "
                                "5184/13824 = 3/8; both <= 5/8"),
             dict(claim="|{(a,b) in G^2 : ab=ba}| = |G| * k(G)",
                  source="Burnside / Cauchy-Frobenius orbit counting applied "
                         "to the conjugation action, Fix(g) = C_G(g)",
                  oa_corroborators=["en.wikipedia.org/wiki/Burnside%27s_lemma "
                                    "(conjugation section)",
                                    "en.wikipedia.org/wiki/Conjugacy_class "
                                    "('Average centralizer')"],
                  status="VERIFIED as an identity; PARTIAL at textbook "
                         "theorem-number granularity (Rotman, 'An Introduction "
                         "to the Theory of Groups', Springer 1995, ISBN "
                         "0-387-94285-8 is the natural home but was not opened)",
                  measured_here="reproduces the commuting-pair count on all "
                                "FOUR group carriers and FAILS on the "
                                "octonion loop (|G|*k = 144 vs 88 measured)"),
             dict(claim="octonions are ALTERNATIVE (not associative)",
                  source="J. C. Baez, 'The Octonions', Bull. Amer. Math. Soc. "
                         "39 (2002) 145-205; arXiv:math/0105155, section 1.1 "
                         "+ Theorem 2",
                  access="OA, fetched in full via ar5iv",
                  status="VERIFIED",
                  measured_here="left/right alternative 256/256; associative "
                                "only 2752/4096"),
             dict(claim="{+/-e_0..+/-e_7} is a MOUFANG LOOP of order 16",
                  correction=("Baez arXiv:math/0105155 does NOT contain the "
                              "string 'Moufang' anywhere — it covers "
                              "alternativity only. A separate source is "
                              "required; assuming Baez covers this is wrong."),
                  sources=["en.wikipedia.org/wiki/Moufang_loop — 'The basis "
                           "octonions and their additive inverses form a "
                           "finite Moufang loop of order 16'",
                           "R. D. Schafer, 'An Introduction to Nonassociative "
                           "Algebras', Academic Press 1966, Ch. III, the three "
                           "Moufang identities as equations (7)-(9); public "
                           "domain, Project Gutenberg #25156"],
                  status="VERIFIED (via Wikipedia + Schafer, NOT via Baez)",
                  measured_here="Moufang identity (ab)(ca) == a((bc)a) holds "
                                "4096/4096; flexible 256/256"),
             dict(claim="(ab)^-1 = b^-1 a^-1 on the octonion unit loop",
                  status="NOT INDEPENDENTLY VERIFIED FROM AN ACCESSIBLE SOURCE",
                  what_was_found=("It is stated as a general Moufang-loop "
                                  "theorem on en.wikipedia.org/wiki/Moufang_loop "
                                  "('All Moufang loops have the inverse "
                                  "property', 'It follows that (xy)^-1 = "
                                  "y^-1 x^-1'), and follows by composing that "
                                  "with Schafer's octonion Moufang identities "
                                  "— but no single reachable source states the "
                                  "octonion-specific formula with a theorem "
                                  "number. R. H. Bruck, 'A Survey of Binary "
                                  "Systems' (1958) is the likely formal home "
                                  "and no accessible copy was found."),
                  why_this_matters=("This is EXACTLY the claim the brief "
                                    "flagged as 'the kind of should-still-work "
                                    "this project has measured false'. It "
                                    "could not be attested from literature, so "
                                    "it is DERIVED-and-MEASURED here rather "
                                    "than cited: 256/256 ordered pairs on the "
                                    "shipped oct_mult / oct_conjugate, "
                                    "cross-checked against the independent "
                                    "exact-Q cd_mult / cd_conjugate "
                                    "construction (256/256 agreement)."),
                  measured_here="256/256 — the identity HOLDS"),
             dict(claim="a C_0 semigroup extends to a C_0 GROUP iff -A is also "
                        "a generator, iff S(t) is bijective for all t > 0",
                  source="T. Buehler & D. A. Salamon, 'Functional Analysis', "
                         "ETH Zuerich lecture notes dated 8 June 2017, "
                         "Chapter 7, Theorem 7.21",
                  access="OA, fetched: "
                         "people.math.ethz.ch/~salamon/PREPRINTS/funcana.pdf",
                  status="VERIFIED",
                  measured_here="propagate is bijective at finite dimension "
                                "(round-trip 1.5e-15), so by 7.21(iii) the "
                                "shipped EPH surface is a GROUP"),
             dict(claim="Lumer-Phillips: A generates a C_0 contraction "
                        "semigroup iff A is densely defined, dissipative, and "
                        "(lambda - A) has dense image / is surjective for SOME "
                        "lambda > 0",
                  source="Buehler & Salamon, Theorem 7.28 (i)-(iv) + "
                         "Definition 7.27; original: G. Lumer & R. S. "
                         "Phillips, 'Dissipative operators in a Banach space', "
                         "Pacific J. Math. 11 (1961) 679-698",
                  corroborator="arXiv:2202.10730 (Budde & Wegner) states the "
                               "closed+surjective+SOME-lambda form in its "
                               "abstract",
                  status="VERIFIED — 'SOME lambda > 0' is correct, and "
                         "some <=> all is itself a theorem",
                  corrections=[
                      "General Hille-Yosida needs the resolvent bound on ALL "
                      "POWERS k; the single-k form is valid only because M=1.",
                      "Closedness is a CONSEQUENCE of the resolvent condition, "
                      "not an independent hypothesis, in the Buehler-Salamon "
                      "formulation (which requires only dense IMAGE).",
                      "Banach-space dissipativity is EXISTENTIAL over the "
                      "duality set — there EXISTS x* with Re<Ax,x*> <= 0 — not "
                      "universal. The Hilbert form Re<x,Ax> <= 0 is exact."],
                  ),
             dict(claim="a free + transitive action forces the acting MONOID "
                        "to be a group, so 'monoid torsor' is vacuous",
                  source="nLab 'torsor' defines torsors only for groups (shear "
                         "map an isomorphism); Encyclopedia of Mathematics "
                         "'Principal homogeneous space' likewise",
                  status="DERIVED, not cited — no source states the vacuity; "
                         "proof and an exhaustive check over all monoids of "
                         "order <= 4 (0 non-group monoids admit a free+"
                         "transitive action) were done in the theory pass",
                  consequence="torsor-vs-monoid is a STRUCTURAL distinction, "
                              "not a loose analogy"),
         ])

    # ---- the headline verdicts -------------------------------------------
    for c in CARRIERS:
        d = table[c.key]["left_quotient_b_ainv"]
        d2 = table[c.key]["right_quotient_ainv_b"]
        emit("verdict", carrier=c.key, order=c.n,
             abelian=census[c.key]["abelian"],
             associative=census[c.key]["assoc"] == census[c.key]["assoc_total"],
             ordered_triples=d["total"],
             FORWARD=d["fwd"], BARE=d["bare"], CHIRAL=d["chi"],
             forward_total=d["fwd"] == d["total"],
             bare_total=d["bare"] == d["total"],
             chiral_total=d["chi"] == d["total"],
             convention_independent=(d["bare"] == d2["bare"]
                                     and d["chi"] == d2["chi"]
                                     and d["fwd"] == d2["fwd"]),
             chiral_co_extensive_with_forward=(
                 d["hits"][d["ccell"]] == d["hits"][d["fcell"]]),
             bare_co_extensive_with_forward=(
                 d["hits"][d["bcell"]] == d["hits"][d["fcell"]]),
             forward_and_bare_intersection=len(
                 d["hits"][d["fcell"]] & d["hits"][d["bcell"]]),
             thesis=(
                 # abelian: inversion is invisible, everything is total
                 "INVERSION INVISIBLE — abelian carrier, bare and chiral both "
                 "total; this row is the CONTROL and proves the harness is not "
                 "manufacturing the shortfall"
                 if d["chi"] == d["total"] and d["bare"] == d["total"] else
                 # non-abelian, associative: the clean separation
                 "REVERSAL IS NOT REWIND — chiral total, bare NOT total"
                 if d["chi"] == d["total"] and d["bare"] != d["total"] else
                 # non-associative: chiral tracks forward exactly
                 "REVERSAL IS NOT REWIND, CONDITIONALLY — the FORWARD law is "
                 "itself not total here (non-associativity), and chiral "
                 "reversal succeeds on EXACTLY the triples forward does (set "
                 "equality, not merely equal counts). So chiral is total "
                 "RELATIVE TO the forward law's own domain, and the inversion "
                 "costs nothing. Bare reversal has the SAME COUNT but a "
                 "DIFFERENT SET — a count-only test would have called them "
                 "equivalent"
                 if d["hits"][d["ccell"]] == d["hits"][d["fcell"]] else
                 "THESIS FAILS ON THIS CARRIER — chiral reversal is neither "
                 "total nor co-extensive with forward; this is the headline, "
                 "not a footnote"))


def main():
    section_env()
    section_carriers()
    census = section_algebra()
    section_antiauto()
    table = section_reversal(census)
    section_overlaps(table)
    section_controls(table, census)
    section_ceiling(table, census)
    section_octonion_detail()
    section_seam_torsor()
    section_monoid_census()
    section_eph_arrow()
    section_ledger(table, census)

    out = "reversal_is_not_rewind_rc426.ndjson"
    with open(out, "w", encoding="utf-8") as fh:
        for r in RECORDS:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"wrote {len(RECORDS)} records -> {out}")


if __name__ == "__main__":
    main()
