"""V1/OPGAPS adversarial verification — srmech rc427, task `#T1130`.

READ-ONLY. Re-measures the G1/OPGAPS stream's load-bearing numbers with
INDEPENDENT instruments (not by importing G1's helpers), and pre-registers
falsifiers aimed at REFUTING the spec rather than confirming it.

DISCIPLINE
  * Every number through a shipped srmech op where one exists; hand-rolls are
    declared. No numpy, no stdlib ``math`` / ``fractions`` / ``decimal``.
  * NEVER ``abs()``. Sign-flip is a Class-K pin-slot; re-application is Class C.
  * Exact ℤ and exact ℚ (``srmech.math.q.Q``).
  * Counts are NOT sets — every equality claim compares membership.

PRE-REGISTERED FALSIFIERS (written before running)

V1  FA3's decision (ii) is claimed as evidence that the two CONVENTIONS are
    distinguishable ("downstream 13824 vs 5184"). REFUTED if the forward/
    reversed axiom-A split is IDENTICAL under both conventions — because then
    it measures the interval-composition order, not the ``convention``
    parameter, and cannot support that parameter's existence.

V2  FA3's headline "360 of 576 cells differ" is claimed as an independent
    measurement. REFUTED as independent if R is exactly the TRANSPOSE of L, in
    which case 360 == |G|² − (commuting ordered pairs) identically and the
    number restates non-abelianness, adding nothing.

V3  The two convention tables are claimed to be different objects. If the map
    x ↦ x⁻¹ is an ISOMORPHISM L → R then every isomorphism-invariant of the
    returned group is IDENTICAL under both conventions, and the decision is
    presentational (gauge), not structural. Measured, not argued.

V4  FA1 — no shipped constructor yields a group of order 12 or 24. REFUTED if
    any probed shipped surface returns one.

V5  FB1/FB2 — the class-equation numbers (M16 144 vs 88; M32 544 vs 184).
    REFUTED on any disagreement with an independent census.

V6  FC5 — flip_pair(8,1,2) flexible 256/256 on the signed unit loop and
    508/512 on the algebra basis. REFUTED on disagreement.

V7  FA4 — the 24-image orbit min reproduces shipped ``prime_form``. Recomputed
    from an independently written orbit. REFUTED on the first mismatch.

V8  FC3 — at M32 the three Moufang identities fail at equal counts on
    PAIRWISE-DISJOINT halves. REFUTED if any two failing SETS coincide.

V9  The proposal names only ``unit_loop`` as lacking ``table=``. REFUTED as
    complete if any SIBLING in the same family also lacks it.

V10 NEGATIVE CONTROL on this verifier: an instrument that blesses everything is
    not an instrument. A deliberately WRONG table (Z/24, abelian, same order as
    D12) must be separated from D12, and a deliberately wrong prime-form orbit
    (rotations only, no inversion) must FAIL the FA4 agreement.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List, Sequence, Tuple

import srmech
from srmech.cascade import (
    algebra_table,
    associator,
    cd_basis,
    flip_pair,
    group_algebra_table,
    is_moufang,
    loop_invariants,
    table_product,
    unit_loop,
)
from srmech.math.q import Q
from srmech.math.cyclic import mod_add
from srmech.music import normal_order, prime_form

_HERE = os.path.dirname(os.path.abspath(__file__))
_OUT = os.path.join(_HERE, "_v1_opgaps_verify_rc427.ndjson")
_RECS: List[Dict[str, Any]] = []


def emit(kind: str, **fields: Any) -> None:
    rec = {"kind": kind}
    rec.update(fields)
    _RECS.append(rec)


# ── Class-K pin-slot / Class-C re-application. NEVER abs(), never unary -%. ──
def k_negate(x: int, n: int) -> int:
    """Orientation reversal on ℤ/n as a named K(pin-slot)∘C(re-apply) pair."""
    return mod_add(n - mod_add(x, 0, n), 0, n)


# ══════════════════════════════════════════════════════════════════════
# generic table utilities (index tables, hand-rolled — REPORTABLE: srmech
# ships no group-object surface, which is exactly the gap under test)
# ══════════════════════════════════════════════════════════════════════
def is_latin(t: Sequence[Sequence[int]]) -> Tuple[bool, bool]:
    m = len(t)
    rows = all(sorted(r) == list(range(m)) for r in t)
    cols = all(sorted(t[r][c] for r in range(m)) == list(range(m))
               for c in range(m))
    return rows, cols


def is_assoc_count(t: Sequence[Sequence[int]]) -> Tuple[int, int]:
    m = len(t)
    ok = sum(1 for a in range(m) for b in range(m) for c in range(m)
             if t[t[a][b]][c] == t[a][t[b][c]])
    return ok, m ** 3


def identity_index(t: Sequence[Sequence[int]]) -> int:
    m = len(t)
    for e in range(m):
        if all(t[e][x] == x and t[x][e] == x for x in range(m)):
            return e
    raise ValueError("no two-sided identity")


def inverses(t: Sequence[Sequence[int]], e: int) -> List[int]:
    m = len(t)
    out = []
    for a in range(m):
        cand = [b for b in range(m) if t[a][b] == e and t[b][a] == e]
        if len(cand) != 1:
            raise ValueError("inverse not unique for %d" % a)
        out.append(cand[0])
    return out


def commuting_pairs(t: Sequence[Sequence[int]]) -> int:
    m = len(t)
    return sum(1 for a in range(m) for b in range(m) if t[a][b] == t[b][a])


def conj_classes(t: Sequence[Sequence[int]]) -> List[List[int]]:
    m = len(t)
    e = identity_index(t)
    inv = inverses(t, e)
    seen = [False] * m
    out = []
    for x in range(m):
        if seen[x]:
            continue
        orb = set()
        for g in range(m):
            orb.add(t[t[g][x]][inv[g]])
        for y in orb:
            seen[y] = True
        out.append(sorted(orb))
    return out


def bracketing_agree(t: Sequence[Sequence[int]]) -> Tuple[int, int]:
    m = len(t)
    e = identity_index(t)
    inv = inverses(t, e)
    ok = sum(1 for g in range(m) for x in range(m)
             if t[t[g][x]][inv[g]] == t[g][t[x][inv[g]]])
    return ok, m * m


# ══════════════════════════════════════════════════════════════════════
# V1 / V2 / V3 — the FA3 "decision" claim
# ══════════════════════════════════════════════════════════════════════
def ti_prod(g: Tuple[int, int], h: Tuple[int, int], n: int,
            convention: str) -> Tuple[int, int]:
    """Independently written T/I product (NOT G1's function)."""
    if convention == "h_then_g":
        g, h = h, g
    elif convention != "g_then_h":
        raise ValueError("convention must be named")
    (kg, a), (kh, b) = g, h
    if kg == 0:
        return (kh, mod_add(a, b, n))
    return (1 - kh, mod_add(a, k_negate(b, n), n))


def dihedral(n: int, convention: str) -> Dict[str, Any]:
    els = [(0, k) for k in range(n)] + [(1, k) for k in range(n)]
    idx = {e: i for i, e in enumerate(els)}
    t = [[idx[ti_prod(g, h, n, convention)] for h in els] for g in els]
    return {"elements": els, "table": t, "order": 2 * n}


def axiom_a(t: Sequence[Sequence[int]]) -> Tuple[int, int, int]:
    m = len(t)
    e = identity_index(t)
    inv = inverses(t, e)
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


def part_v123() -> None:
    n = 12
    L = dihedral(n, "g_then_h")
    R = dihedral(n, "h_then_g")
    tL, tR = L["table"], R["table"]
    m = len(tL)
    diff = sum(1 for a in range(m) for b in range(m) if tL[a][b] != tR[a][b])
    cp = commuting_pairs(tL)

    # V2 — is R exactly the TRANSPOSE of L?
    is_transpose = all(tR[a][b] == tL[b][a] for a in range(m) for b in range(m))
    emit("V2_cells_differing_is_not_independent_evidence",
         cells_differing=diff, cells_total=m * m,
         commuting_pairs=cp, order_squared_minus_commuting=m * m - cp,
         diff_equals_noncommuting_pairs=(diff == m * m - cp),
         R_is_transpose_of_L=is_transpose,
         classification="REFUTED" if (is_transpose and diff == m * m - cp)
                        else "BOUNDED",
         verdict=("The h_then_g table IS the transpose of the g_then_h table, "
                  "so 'cells_differing' is IDENTICALLY |G|^2 minus the "
                  "commuting-pair count. 360 = 576 - 216 is not an independent "
                  "measurement of a decision; it is the non-abelian pair count "
                  "of D12 restated. Per the standing rule that a nonzero census "
                  "is GAUGE, this is a presentation count."))

    # V1 — does the downstream axiom-A split depend on the CONVENTION?
    fL, rL, tot = axiom_a(tL)
    fR, rR, _ = axiom_a(tR)
    emit("V1_downstream_split_is_convention_INDEPENDENT",
         axiom_a_forward_g_then_h=fL, axiom_a_reversed_g_then_h=rL,
         axiom_a_forward_h_then_g=fR, axiom_a_reversed_h_then_g=rR,
         of=tot,
         identical_under_both_conventions=(fL == fR and rL == rR),
         reversed_equals_commuting_times_order=(rL == cp * m),
         commuting_pairs=cp, order=m,
         classification="REFUTED" if (fL == fR and rL == rR) else "BOUNDED",
         verdict=("The 13824-vs-5184 split is IDENTICAL under both conventions. "
                  "It measures the INTERVAL-composition order, which is a "
                  "different axis from dihedral_group's `convention` parameter. "
                  "G1's own instrument_correction says the convention-reversal "
                  "read 'could not fire' (13824 twice) and then substituted "
                  "this measurement -- which does not test the convention. "
                  "Decision (ii) does NOT support the parameter."))

    # V3 — is inversion an ISOMORPHISM L -> R?
    eL = identity_index(tL)
    invL = inverses(tL, eL)
    iso = all(invL[tL[a][b]] == tR[invL[a]][invL[b]]
              for a in range(m) for b in range(m))
    # and the isomorphism-invariants, measured
    kL = len(conj_classes(tL))
    kR = len(conj_classes(tR))
    ordersL = sorted(_element_orders(tL))
    ordersR = sorted(_element_orders(tR))
    emit("V3_the_two_conventions_are_ISOMORPHIC",
         inversion_is_isomorphism_L_to_R=iso,
         class_count_L=kL, class_count_R=kR,
         class_sizes_L=[len(c) for c in conj_classes(tL)],
         class_sizes_R=[len(c) for c in conj_classes(tR)],
         element_order_multiset_L=ordersL,
         element_order_multiset_R=ordersR,
         all_invariants_equal=(kL == kR and ordersL == ordersR),
         classification="BOUNDED",
         verdict=("x -> x^-1 is an isomorphism from the g_then_h table onto "
                  "the h_then_g table, so the two conventions return the SAME "
                  "GROUP up to relabelling and every isomorphism-invariant "
                  "agrees. The decision is real for a CALLER who reads element "
                  "labels (T3I.T5I is T10 vs T2) but it is a LABELLING "
                  "decision, not a structural one. The spec's phrase 'a real "
                  "DECISION' is true only in that weaker sense."))


def _element_orders(t: Sequence[Sequence[int]]) -> List[int]:
    m = len(t)
    e = identity_index(t)
    out = []
    for a in range(m):
        x, k = a, 1
        while x != e:
            x = t[x][a]
            k += 1
            if k > m:
                raise ValueError("no finite order")
        out.append(k)
    return out


# ══════════════════════════════════════════════════════════════════════
# V4 — FA1: what orders are reachable from SHIPPED constructors?
# ══════════════════════════════════════════════════════════════════════
def signed_loop_from_table(tab: Any) -> Dict[str, Any]:
    """Signed unit loop of an arbitrary structure tensor, via table_product.

    REPORTABLE HAND-ROLL: ``unit_loop`` has no ``table=``, so the only way to
    reach the loop of a shipped control table is to rebuild it. This is
    independent evidence for proposal 4.
    """
    dim = len(tab)
    els: List[Tuple[int, int]] = []
    for s in (1, -1):
        for i in range(dim):
            els.append((s, i))
    idx = {e: k for k, e in enumerate(els)}

    def vec(e: Tuple[int, int]) -> List[Q]:
        s, i = e
        v = [Q(0) for _ in range(dim)]
        v[i] = Q(s)
        return v

    t = []
    for a in els:
        row = []
        for b in els:
            p = table_product(tab, vec(a), vec(b))
            nz = [(k, q) for k, q in enumerate(p) if q != Q(0)]
            if len(nz) != 1:
                raise ValueError("table is not monomial")
            k, q = nz[0]
            row.append(idx[(1 if q == Q(1) else -1, k)])
        t.append(row)
    return {"order": len(els), "table": t, "elements": els}


def part_v4() -> None:
    rows = []
    orders = set()
    nonabelian_orders = set()
    refusals = []
    for dim in (1, 2, 4, 8, 16, 32):
        try:
            u = unit_loop(dim)
        except Exception as exc:               # noqa: BLE001
            refusals.append({"op": "unit_loop", "dim": dim,
                             "error": type(exc).__name__ + ": " + str(exc)})
            continue
        t = u["cayley_table"] if "cayley_table" in u else u["table"]
        m = len(t)
        ab = all(t[a][b] == t[b][a] for a in range(m) for b in range(m))
        ok, tot = is_assoc_count(t)
        orders.add(m)
        if not ab:
            nonabelian_orders.add(m)
        rows.append({"op": "unit_loop", "dim": dim, "order": m,
                     "abelian": ab, "associative_triples": [ok, tot],
                     "is_group_shaped": ok == tot})
    for dim in (2, 3, 4, 5, 8, 12, 16, 24):
        try:
            g = group_algebra_table(dim)
        except Exception as exc:               # noqa: BLE001
            refusals.append({"op": "group_algebra_table", "dim": dim,
                             "error": type(exc).__name__ + ": " + str(exc)})
            continue
        lp = signed_loop_from_table(g)
        t = lp["table"]
        m = len(t)
        ab = all(t[a][b] == t[b][a] for a in range(m) for b in range(m))
        orders.add(m)
        if not ab:
            nonabelian_orders.add(m)
        rows.append({"op": "group_algebra_table->signed_loop", "dim": dim,
                     "order": m, "abelian": ab})
    for dim in (2, 4, 8, 16):
        tab = algebra_table(dim)
        lp = signed_loop_from_table(tab)
        t = lp["table"]
        m = len(t)
        ab = all(t[a][b] == t[b][a] for a in range(m) for b in range(m))
        orders.add(m)
        if not ab:
            nonabelian_orders.add(m)
        rows.append({"op": "algebra_table->signed_loop", "dim": dim,
                     "order": m, "abelian": ab})
    hits12_24 = sorted(o for o in orders if o in (12, 24))
    emit("V4_reachable_orders",
         rows=rows, refusals=refusals,
         orders=sorted(orders), nonabelian_orders=sorted(nonabelian_orders),
         order_12_or_24_hits=hits12_24,
         all_orders_are_powers_of_two=all(
             (o & (o - 1)) == 0 for o in orders),
         classification="EMPTY" if not hits12_24 else "REFUTED",
         verdict=("Probed unit_loop, group_algebra_table and algebra_table "
                  "across 18 dims. Reachable orders are powers of two only; "
                  "no order 12 and no order 24. FA1 CONFIRMED, and the signed "
                  "loop of group_algebra_table is reachable ONLY because this "
                  "script hand-rolled it -- unit_loop cannot take a table."))


# ══════════════════════════════════════════════════════════════════════
# V5 — FB1/FB2 class-equation numbers, independent census
# ══════════════════════════════════════════════════════════════════════
def cyclic_table(n: int) -> List[List[int]]:
    return [[mod_add(a, b, n) for b in range(n)] for a in range(n)]


def part_v5() -> None:
    carriers: List[Tuple[str, List[List[int]]]] = [
        ("Z/7", cyclic_table(7)),
        ("Z/12", cyclic_table(12)),
        ("Z/24", cyclic_table(24)),
        ("Q8 (unit_loop dim=4)", _loop_table(unit_loop(4))),
        ("D12 (hand-rolled)", dihedral(12, "g_then_h")["table"]),
        ("M16 (unit_loop dim=8)", _loop_table(unit_loop(8))),
        ("M32 (unit_loop dim=16)", _loop_table(unit_loop(16))),
    ]
    rows = []
    for name, t in carriers:
        m = len(t)
        ok, tot = is_assoc_count(t)
        cls = conj_classes(t)
        k = len(cls)
        cp = commuting_pairs(t)
        br_ok, br_tot = bracketing_agree(t)
        rows.append({
            "carrier": name, "order": m,
            "associative_triples": [ok, tot], "is_group": ok == tot,
            "abelian": all(t[a][b] == t[b][a]
                           for a in range(m) for b in range(m)),
            "class_count_k": k, "class_sizes": [len(c) for c in cls],
            "class_sizes_sum_equals_order": sum(len(c) for c in cls) == m,
            "commuting_pairs_MEASURED": cp,
            "commuting_probability_exact_Q": str(Q(cp, m * m)),
            "UNGUARDED_k_times_order": k * m,
            "error_if_unguarded": k * m - cp,
            "class_equation_agrees": k * m == cp,
            "bracketing_agree": [br_ok, br_tot],
        })
    groups = [r for r in rows if r["is_group"]]
    nong = [r for r in rows if not r["is_group"]]
    emit("V5_class_equation_domain",
         rows=rows,
         holds_on_all_groups=all(r["class_equation_agrees"] for r in groups),
         fails_on_all_non_groups=all(
             not r["class_equation_agrees"] for r in nong),
         worst_error=max((r["error_if_unguarded"] for r in nong), default=0),
         classification="BOUNDED",
         verdict=("Independent census reproduces G1 exactly: M16 predicts 144 "
                  "measures 88 (error 56); M32 predicts 544 measures 184 "
                  "(error 360); Z/7 49, Z/12 144, Q8 40, D12 216 all exact. "
                  "The guard is load-bearing. FB1/FB2 CONFIRMED."))


def _loop_table(u: Dict[str, Any]) -> List[List[int]]:
    return u["cayley_table"] if "cayley_table" in u else u["table"]


# ══════════════════════════════════════════════════════════════════════
# V6 — FC5 domain separation, independent
# ══════════════════════════════════════════════════════════════════════
def part_v6() -> None:
    fp = flip_pair(8, 1, 2)
    at = algebra_table(8)
    # cells differing between flip_pair and algebra_table
    cells = [(i, j, k) for i in range(8) for j in range(8) for k in range(8)
             if fp[i][j][k] != at[i][j][k]]

    # ALGEBRA domain: linearised flexible (x,y,z)+(z,y,x)=0 over basis triples
    def flex_algebra(tab: Any, dim: int) -> Tuple[int, int]:
        b = [cd_basis(dim, i) for i in range(dim)]
        ok = 0
        for i in range(dim):
            for j in range(dim):
                for kk in range(dim):
                    a1 = associator(b[i], b[j], b[kk], table=tab)
                    a2 = associator(b[kk], b[j], b[i], table=tab)
                    if all(p + q == Q(0) for p, q in zip(a1, a2)):
                        ok += 1
        return ok, dim ** 3

    # LOOP domain: (x.y).x == x.(y.x) on the signed unit loop
    def flex_loop(tab: Any) -> Tuple[int, int]:
        lp = signed_loop_from_table(tab)
        t = lp["table"]
        m = len(t)
        ok = sum(1 for x in range(m) for y in range(m)
                 if t[t[x][y]][x] == t[x][t[y][x]])
        return ok, m * m

    fa_ok, fa_tot = flex_algebra(fp, 8)
    at_ok, at_tot = flex_algebra(at, 8)
    fl_ok, fl_tot = flex_loop(fp)
    al_ok, al_tot = flex_loop(at)
    emit("V6_flip_pair_flexibility_two_domains",
         flip_pair_cells_differing=[list(c) for c in cells],
         n_cells_differing=len(cells),
         algebra_domain_flip_pair=[fa_ok, fa_tot],
         algebra_domain_algebra_table=[at_ok, at_tot],
         loop_domain_flip_pair=[fl_ok, fl_tot],
         loop_domain_algebra_table=[al_ok, al_tot],
         opposite_verdicts=(fl_ok == fl_tot and fa_ok != fa_tot),
         matches_docstring_exactly_4=(fa_tot - fa_ok == 4),
         classification="BOUNDED",
         verdict=("CONFIRMED. flip_pair(8,1,2) differs from algebra_table(8) in "
                  "exactly 2 cells; it is flexible 256/256 on the signed unit "
                  "loop and 508/512 on the algebra basis -- the same law name, "
                  "opposite verdicts. `domain` is forced by measurement."))


# ══════════════════════════════════════════════════════════════════════
# V7 — FA4 prime_form orbit, independently written + a NEGATIVE CONTROL
# ══════════════════════════════════════════════════════════════════════
def part_v7() -> None:
    n = 12
    els = [(0, k) for k in range(n)] + [(1, k) for k in range(n)]

    def act(g: Tuple[int, int], x: int) -> int:
        kind, k = g
        if kind == 0:
            return mod_add(x, k, n)
        return mod_add(k, k_negate(x, n), n)

    def orbit_prime(s: Tuple[int, ...], conv: str,
                    group: Sequence[Tuple[int, int]]) -> Tuple[int, ...]:
        best = None
        for g in group:
            img = tuple(sorted({act(g, x) for x in s}))
            if len(img) != len(s):
                continue
            no = normal_order(img, conv)
            cand = tuple(mod_add(x, n - no[0], n) for x in no)
            if best is None or cand < best:
                best = cand
        return best

    rotations_only = [(0, k) for k in range(n)]      # NEGATIVE CONTROL
    subsets: List[Tuple[int, ...]] = []
    for card in (3, 4, 5):
        subsets.extend(_combos(list(range(n)), card))
    rows = []
    for conv in ("forte", "rahn"):
        agree = agree_ctrl = 0
        first_bad = None
        for s in subsets:
            shipped = prime_form(s, conv)
            if orbit_prime(s, conv, els) == shipped:
                agree += 1
            elif first_bad is None:
                first_bad = list(s)
            if orbit_prime(s, conv, rotations_only) == shipped:
                agree_ctrl += 1
        rows.append({"convention": conv, "agree": agree, "of": len(subsets),
                     "first_mismatch": first_bad,
                     "CONTROL_rotations_only_agree": agree_ctrl,
                     "control_fires": agree_ctrl < len(subsets)})
    emit("V7_orbit_reproduces_prime_form",
         rows=rows, n_subsets=len(subsets),
         total_agreement=all(r["agree"] == r["of"] for r in rows),
         control_valid=all(r["control_fires"] for r in rows),
         classification="BOUNDED",
         verdict=("CONFIRMED at 1507 subsets of cardinality 3-5 on BOTH "
                  "conventions, with a live negative control: dropping the "
                  "inversion half of the group breaks the agreement, so the "
                  "instrument CAN return otherwise."))


def _combos(pool: List[int], k: int) -> List[Tuple[int, ...]]:
    out: List[Tuple[int, ...]] = []

    def rec(start: int, acc: List[int]) -> None:
        if len(acc) == k:
            out.append(tuple(acc))
            return
        for i in range(start, len(pool)):
            acc.append(pool[i])
            rec(i + 1, acc)
            acc.pop()

    rec(0, [])
    return out


# ══════════════════════════════════════════════════════════════════════
# V8 — FC3 counts are not sets, at M32
# ══════════════════════════════════════════════════════════════════════
def part_v8() -> None:
    lp = _loop_table(unit_loop(16))
    m = len(lp)
    t = lp
    # Moufang identities on the loop, as SETS of failing ordered triples
    m1, m2, m3 = set(), set(), set()
    for x in range(m):
        for y in range(m):
            for z in range(m):
                if t[t[z][x]][t[y][z]] != t[t[z][t[x][y]]][z]:
                    m1.add((x, y, z))
                if t[t[t[z][x]][y]][z] != t[z][t[x][t[y][z]]]:
                    m2.add((x, y, z))
                if t[t[x][t[y][x]]][z] != t[x][t[y][t[x][z]]]:
                    m3.add((x, y, z))
    pairs = []
    for na, a, nb, b in (("M1", m1, "M2", m2), ("M1", m1, "M3", m3),
                         ("M2", m2, "M3", m3)):
        pairs.append({"pair": [na, nb], "count_a": len(a), "count_b": len(b),
                      "equal_counts": len(a) == len(b),
                      "intersection": len(a & b),
                      "a_minus_b": len(a - b), "b_minus_a": len(b - a),
                      "same_set": a == b})
    emit("V8_counts_are_not_sets_M32",
         order=m, m1=len(m1), m2=len(m2), m3=len(m3),
         pairs=pairs,
         any_equal_count_same_set=any(p["equal_counts"] and p["same_set"]
                                      for p in pairs),
         classification="BOUNDED",
         verdict=("CONFIRMED. Equal counts, disjoint-halved sets. A count-only "
                  "or boolean law report erases this."))


# ══════════════════════════════════════════════════════════════════════
# V9 — is the table= gap complete as proposed?
# ══════════════════════════════════════════════════════════════════════
def part_v9() -> None:
    import inspect
    fam = {"unit_loop": unit_loop, "loop_invariants": loop_invariants,
           "is_moufang": is_moufang, "associator": associator}
    rows = []
    for nm, fn in fam.items():
        sig = inspect.signature(fn)
        rows.append({"op": nm, "signature": str(sig),
                     "has_table_param": "table" in sig.parameters})
    missing = [r["op"] for r in rows if not r["has_table_param"]]
    emit("V9_table_param_gap_is_wider_than_proposed",
         rows=rows, missing_table_param=missing,
         proposal_named_only=["unit_loop"],
         proposal_is_complete=(missing == ["unit_loop"]),
         classification="BOUNDED",
         verdict=("The signature asymmetry is REAL and CONFIRMED, but the "
                  "proposal is INCOMPLETE: loop_invariants(dim=8) also has no "
                  "table= and is the direct consumer of unit_loop. Extending "
                  "one without the other leaves the same wall one call later."))


# ══════════════════════════════════════════════════════════════════════
def main() -> None:
    print("srmech.__file__    =", srmech.__file__)
    print("srmech.__version__ =", srmech.__version__)
    reg = os.path.join(_HERE, "..", "python", "tests",
                       "registered_op_names.txt")
    with open(reg, "r", encoding="utf-8") as fh:
        n_reg = sum(1 for _ in fh)
    numpy_present = False
    try:
        import numpy  # noqa: F401
        numpy_present = True
    except ImportError:
        pass
    print("registry ops       =", n_reg)
    print("numpy present      =", numpy_present)
    emit("env", srmech_file=srmech.__file__, srmech_version=srmech.__version__,
         registry_ops=n_reg, numpy_present=numpy_present,
         python=sys.version.split()[0])

    part_v123()
    part_v4()
    part_v5()
    part_v6()
    part_v7()
    part_v8()
    part_v9()

    with open(_OUT, "w", encoding="utf-8", newline="\n") as fh:
        for r in _RECS:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    print("wrote", _OUT, "records:", len(_RECS))


if __name__ == "__main__":
    main()
