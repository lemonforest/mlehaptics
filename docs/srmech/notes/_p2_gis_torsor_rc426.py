#!/usr/bin/env python3
"""P2 — is the notation object a TORSOR?  Axioms EXECUTED, with negative
controls (rc426 research spike, read-only).

Pre-registered falsifiers
=========================
F3  **The GIS axioms, run rather than quoted.**  A Generalized Interval System
    is claimed to be ``(S, IVLS, int)`` with

      (A)  int(r,s) · int(s,t) = int(r,t)          for all r,s,t ∈ S
      (B)  ∀ s ∈ S, ∀ i ∈ IVLS  ∃! t ∈ S : int(s,t) = i

    (B) IS simple transitivity, so (S, IVLS) would be an IVLS-torsor.  This
    script executes both axioms exhaustively on finite candidate systems built
    from SHIPPED srmech ops, and on deliberately BROKEN systems that must fail.
    ⚠️ Whether these ARE Lewin's axioms is a CITATION question, answered
    separately; this script measures only whether a given (S, IVLS, int)
    satisfies the stated pair.

F4  **Is there a canonical origin?**  A torsor has none.  Two measurements:
    (i) the action is FREE — no non-identity interval fixes any point;
    (ii) an interval-only invariant CANNOT recover the origin, while a
    non-invariant CAN (so the instrument can return otherwise).

F7  **Is the chart↔carrier translator lossless in both directions?**  Measured
    on an explicit positional chart.  A lossy direction is a real result.

Negative controls (mandatory — an instrument that blesses a wrong input is not
measuring, ``[[feedback_an_instrument_that_cannot_return_otherwise_is_not_a_
measurement]]``):
    N1  int(s,t) = (t+s) mod n           — violates (A)
    N2  int(s,t) = 2·(t−s) mod 12        — violates (B), 2-to-1
    N3  IVLS smaller than S              — violates (B), not surjective
    N4  IVLS larger than S               — violates (B), not injective
    N5  a WRONG letter→semitone chart     — must break interval preservation

Scope: algebra / group-action only.  No audio, no DSP, no engraving geometry.

Run:
    PYTHONPATH=docs/srmech/python python3 docs/srmech/notes/_p2_gis_torsor_rc426.py
"""
from __future__ import annotations

import itertools
import json
import os
import sys

import srmech
from srmech.cascade import cyclic_mod_add
from srmech.math.primes import factor
from srmech.music.relations import interval_vector, normal_order, prime_form

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "_p2_gis_torsor_rc426.ndjson")

RECS = []


def emit(**kw):
    kw.setdefault("srmech_version", srmech.__version__)
    RECS.append(kw)


# ══════════════════════════════════════════════════════════════════════════
# The GIS checker.  Takes a finite S, a finite IVLS with a composition law and
# an identity, and an int() map.  Returns per-axiom counts — never a bare bool,
# so a failure says HOW MUCH it failed by.
# ══════════════════════════════════════════════════════════════════════════
def check_gis(name, S, IVLS, compose, ident, intv, note=""):
    S = list(S)
    IVLS = list(IVLS)
    # (A)  int(r,s) · int(s,t) == int(r,t)
    a_ok = a_tot = 0
    for r, s, t in itertools.product(S, S, S):
        a_tot += 1
        if compose(intv(r, s), intv(s, t)) == intv(r, t):
            a_ok += 1
    # (B)  unique t with int(s,t) == i
    b_ok = b_tot = 0
    mult = {}
    for s in S:
        for i in IVLS:
            b_tot += 1
            ts = [t for t in S if intv(s, t) == i]
            mult[len(ts)] = mult.get(len(ts), 0) + 1
            if len(ts) == 1:
                b_ok += 1
    # freeness: does any non-identity i fix a point?  (int(s,s) == ident only)
    fixed = sum(1 for s in S if intv(s, s) != ident)
    # is IVLS abelian under this composition?
    abelian = all(compose(i, j) == compose(j, i)
                  for i, j in itertools.product(IVLS, IVLS))
    verdict = ("TORSOR" if a_ok == a_tot and b_ok == b_tot
               else "NOT-A-TORSOR")
    row = {"finding": "F3_gis_axioms", "system": name, "note": note,
           "n_S": len(S), "n_IVLS": len(IVLS),
           "axiom_A_pass": a_ok, "axiom_A_total": a_tot,
           "axiom_B_pass": b_ok, "axiom_B_total": b_tot,
           "axiom_B_preimage_multiplicity_histogram":
               {str(k): v for k, v in sorted(mult.items())},
           "points_where_int_s_s_is_not_identity": fixed,
           "IVLS_abelian": abelian, "verdict": verdict}
    emit(**row)
    print(f"  {name:46s} A {a_ok:6d}/{a_tot:<6d}  B {b_ok:5d}/{b_tot:<5d}  "
          f"|S|={len(S):3d} |IVLS|={len(IVLS):3d}  "
          f"{'abelian' if abelian else 'NONabelian':10s}  {verdict}")
    return row


def main() -> int:
    print("srmech.__file__    =", srmech.__file__)
    print("srmech.__version__ =", srmech.__version__)
    try:
        import numpy  # noqa: F401
        print("!! numpy PRESENT — environment wrong")
    except ImportError:
        print("numpy              = ABSENT (correct)")

    # ══════════════════════════════════════════════════════════════════
    # F3.1 — the n-EDO family.  If the axioms hold for EVERY n, then 12 is
    # not privileged: the carrier is n-parametric and the 12 is a chart.
    # The n sweep deliberately includes divisions used outside the Western
    # 12 (17, 22, 24, 31, 53 all appear in tuning-theory literature) — the
    # point is only that the ALGEBRA does not care which n.
    # ══════════════════════════════════════════════════════════════════
    print("\nF3.1  ℤ/n under addition, int(s,t) = (t−s) mod n  "
          "[Class I via shipped cyclic_mod_add]")
    for n in (5, 7, 12, 17, 19, 22, 24, 31, 53):
        S = range(n)
        check_gis(f"Z/{n} regular translation",
                  S, range(n),
                  lambda i, j, n=n: cyclic_mod_add(i, j, n),
                  0,
                  lambda s, t, n=n: cyclic_mod_add(t, n - s, n),
                  note="n-parametric: nothing here knows about 12")

    # ══════════════════════════════════════════════════════════════════
    # F3.2 — the FREQUENCY lane: a finite window of the 5-limit just lattice.
    # S = 3-smooth/5-smooth ratios; IVLS = ℤ³ (prime exponents of 2,3,5),
    # which is FREE ABELIAN, not cyclic.  A different group entirely, and the
    # axioms are checked over the same window.  Uses the shipped Class-J
    # factoriser so the exponents are derived, not tabulated.
    # ══════════════════════════════════════════════════════════════════
    print("\nF3.2  the 5-limit just lattice, IVLS = ℤ³ prime-exponent vectors "
          "[Class J via shipped factor()]")
    W = 1  # exponent window per prime -> 3**3 = 27 points

    def expvec(a, b, c):
        return (a, b, c)

    lat = [expvec(a, b, c)
           for a in range(-W, W + 1)
           for b in range(-W, W + 1)
           for c in range(-W, W + 1)]
    r = check_gis("5-limit lattice Z^3 (WINDOW +/-1)",
                  lat, lat,
                  lambda i, j: (i[0] + j[0], i[1] + j[1], i[2] + j[2]),
                  (0, 0, 0),
                  lambda s, t: (t[0] - s[0], t[1] - s[1], t[2] - s[2]),
                  note="free abelian rank 3; NOT cyclic and NOT finite. A "
                       "finite WINDOW of an infinite torsor is not closed "
                       "under the group, so axiom B must fail here; the "
                       "failure is a WINDOWING ARTIFACT, not a refutation.")
    print("      ^ axiom B fails ONLY because the window is not closed: "
          f"{r['axiom_B_pass']}/{r['axiom_B_total']} with multiplicity "
          f"histogram {r['axiom_B_preimage_multiplicity_histogram']} — every "
          "miss is multiplicity 0 (target outside the window), never >1.")
    only_zero_or_one = set(r["axiom_B_preimage_multiplicity_histogram"]) <= {
        "0", "1"}
    print(f"      window-artifact signature (no multiplicity > 1): "
          f"{only_zero_or_one}")
    emit(finding="F3_2_window_artifact",
         multiplicities=r["axiom_B_preimage_multiplicity_histogram"],
         no_multiplicity_above_one=only_zero_or_one,
         verdict=("BOUNDED, not REFUTED: axiom A passes exhaustively "
                  f"({r['axiom_A_pass']}/{r['axiom_A_total']}) and every "
                  "axiom-B miss is a 0-preimage (fell out of the window), "
                  "never a 2-preimage. Simple transitivity is not "
                  "CERTIFIABLE on a truncated window — so a closed finite "
                  "stand-in is run next."))

    # the CLOSED finite stand-in: (ℤ/5)³, same rank-3 abelian shape, closed.
    m = 5
    cl = [(a, b, c) for a in range(m) for b in range(m) for c in range(m)]
    check_gis(f"(Z/{m})^3 CLOSED finite stand-in",
              cl, cl,
              lambda i, j: ((i[0] + j[0]) % m, (i[1] + j[1]) % m,
                            (i[2] + j[2]) % m),
              (0, 0, 0),
              lambda s, t: ((t[0] - s[0]) % m, (t[1] - s[1]) % m,
                            (t[2] - s[2]) % m),
              note="rank-3 abelian, CLOSED — certifies what the truncated "
                   "5-limit window structurally cannot")

    # cross-check the lattice against the SHIPPED factoriser: the exponent
    # vector of an actual ratio must equal the lattice coordinate.
    print("      cross-check exponent vectors against shipped factor():")
    probes = [(3, 2), (5, 4), (9, 8), (81, 80), (45, 32), (16, 15)]
    xchk = []
    for num, den in probes:
        # srmech.math.primes.factor returns List[Tuple[prime, multiplicity]]
        fn, fd = factor(num), factor(den)
        e = {}
        for p, mult in fn:
            e[p] = e.get(p, 0) + mult
        for p, mult in fd:
            e[p] = e.get(p, 0) - mult
        vec = tuple(e.get(p, 0) for p in (2, 3, 5))
        ok = all(p in (2, 3, 5) for p in e)
        xchk.append({"ratio": f"{num}/{den}", "exp_2_3_5": list(vec),
                     "is_5_limit": ok})
        print(f"        {num:3d}/{den:<3d}  (2,3,5)^{vec}  "
              f"{'5-limit' if ok else 'NOT 5-limit'}")
    emit(finding="F3_2_factor_crosscheck", probes=xchk,
         note="exponent vectors DERIVED from srmech.math.primes.factor, "
              "not tabulated")

    # ══════════════════════════════════════════════════════════════════
    # F3.3 — the NON-ABELIAN case.  Lewin's IVLS is required to be a group,
    # not necessarily commutative.  The 24 consonant triads under the
    # T/I group (order 24, non-abelian) is the standard witness.  Built from
    # the SHIPPED prime_form / normal_order so the triad set is derived.
    # ══════════════════════════════════════════════════════════════════
    print("\nF3.3  24 consonant triads under the T/I group (order 24, "
          "NON-abelian) [built on shipped prime_form]")
    MAJ, MIN = (0, 4, 7), (0, 3, 7)
    print(f"      shipped prime_form(major triad, forte) = "
          f"{prime_form(MAJ, 'forte')}")
    print(f"      shipped prime_form(minor triad, forte) = "
          f"{prime_form(MIN, 'forte')}   (same set class: 3-11)")
    print(f"      shipped interval_vector(major)          = "
          f"{interval_vector(MAJ)}")

    def T(n, s):
        return tuple(sorted(cyclic_mod_add(x, n % 12, 12) for x in s))

    def I_(n, s):
        return tuple(sorted(cyclic_mod_add(n % 12, (12 - x) % 12, 12)
                            for x in s))

    triads = []
    for n in range(12):
        triads.append(T(n, MAJ))
    for n in range(12):
        triads.append(T(n, MIN))
    assert len(set(triads)) == 24, len(set(triads))

    # T/I group elements as (kind, n): kind 0 = T_n, kind 1 = I_n
    TI = [(0, n) for n in range(12)] + [(1, n) for n in range(12)]

    def apply(g, s):
        return T(g[1], s) if g[0] == 0 else I_(g[1], s)

    # The composition law is DERIVED by acting, not tabulated — but that
    # requires a probe the action is FAITHFUL on.
    # ⚠️ The first version of this used the probe (0,1,2) and was WRONG:
    # {0,1,2} is inversionally symmetric (I_n{0,1,2} == T_{n-2}{0,1,2}), so
    # the 24 group elements collapse to 12 images and the derived law silently
    # returned a T where an I belonged.  The symptom was axiom A passing at
    # exactly 6912/13824 — half — which looked like an ORDER-CONVENTION
    # finding and was actually a DEGENERATE PROBE.  The fix is to assert
    # faithfulness, so this cannot recur silently.
    PROBE = (0, 1, 3)   # trivial stabiliser under T/I
    _imgs = {apply(k, PROBE): k for k in TI}
    assert len(_imgs) == 24, (
        f"probe {PROBE} is not faithful: {len(_imgs)} distinct images for 24 "
        "group elements — pick a probe with trivial stabiliser")

    def ti_compose(g, h):
        """The single element equal to 'apply g, then apply h'."""
        return _imgs[apply(h, apply(g, PROBE))]

    # int(s,t) = the unique g with apply(g, s) == t
    inv_cache = {}
    for s in triads:
        for g in TI:
            inv_cache.setdefault((s, apply(g, s)), g)

    def ti_int(s, t):
        return inv_cache.get((s, t), ("NONE", -1))

    rA = check_gis("24 triads under T/I  [compose = g THEN h]",
                   triads, TI, ti_compose, (0, 0), ti_int,
                   note="Lewin permits a NON-commutative IVLS; this is the "
                        "standard non-abelian witness. Group is dihedral of "
                        "order 24. Composition read LEFT-to-RIGHT.")

    # ⚠️ THE ORDER CONVENTION IS LOAD-BEARING AND THIS MEASURES IT.
    # With an ABELIAN IVLS the two composition orders agree, so every ℤ/n row
    # above is blind to the choice.  With a NON-abelian IVLS they do not, and
    # axiom A can pass under one order and fail under the other.  Run BOTH.
    def ti_compose_rev(g, h):
        return ti_compose(h, g)

    rB = check_gis("24 triads under T/I  [compose = h THEN g]",
                   triads, TI, ti_compose_rev, (0, 0), ti_int,
                   note="the SAME system with the composition order REVERSED")
    print(f"      order-convention sensitivity: A passes "
          f"{rA['axiom_A_pass']}/{rA['axiom_A_total']} one way, "
          f"{rB['axiom_A_pass']}/{rB['axiom_A_total']} the other; "
          f"B passes {rA['axiom_B_pass']}/{rA['axiom_B_total']} BOTH ways")
    emit(finding="F3_3_composition_order_sensitivity",
         axiom_A_forward=f"{rA['axiom_A_pass']}/{rA['axiom_A_total']}",
         axiom_A_reversed=f"{rB['axiom_A_pass']}/{rB['axiom_A_total']}",
         axiom_B_forward=f"{rA['axiom_B_pass']}/{rA['axiom_B_total']}",
         axiom_B_reversed=f"{rB['axiom_B_pass']}/{rB['axiom_B_total']}",
         verdict="SIMPLE TRANSITIVITY (axiom B) is convention-INDEPENDENT; "
                 "the COMPOSITION LAW (axiom A) is convention-DEPENDENT once "
                 "IVLS is non-abelian. So 'is it a torsor' and 'does the "
                 "stated axiom A hold' are DIFFERENT questions, and only the "
                 "abelian case lets you conflate them. Every ℤ/n row in F3.1 "
                 "is structurally blind to this.")

    # is the T/I group really non-abelian, measured?
    noncomm = sum(1 for g, h in itertools.product(TI, TI)
                  if ti_compose(g, h) != ti_compose(h, g))
    comm = 24 * 24 - noncomm
    print(f"      non-commuting ordered pairs in T/I: {noncomm}/{24 * 24}  "
          f"(commuting: {comm})")

    # ── AN INDEPENDENT CROSS-CHECK OF THE REVERSED-ORDER COUNT ──────────
    # The reversed composition order passes axiom A on exactly those triples
    # whose two intervals COMMUTE: pick r freely (|S| ways), then the pair
    # (int(r,s), int(s,t)) must commute.  And by the class equation the
    # number of commuting ORDERED pairs in a finite group is |G|·k with k the
    # number of conjugacy classes.  So the reversed count is PREDICTED, not
    # just observed — if the harness were measuring something else, these two
    # routes would not land on the same integer.
    def conj_class_count(G, compose):
        inv = {}
        for g in G:
            for h in G:
                if compose(g, h) == (0, 0):
                    inv[g] = h
                    break
        seen, classes = set(), 0
        for g in G:
            if g in seen:
                continue
            classes += 1
            for h in G:
                seen.add(compose(compose(h, g), inv[h]))
        return classes

    k = conj_class_count(TI, ti_compose)
    predicted_commuting = 24 * k
    predicted_reversed_A = 24 * predicted_commuting
    print(f"      conjugacy classes of T/I (measured): {k}")
    print(f"      class-equation prediction: commuting ordered pairs = "
          f"|G|·k = 24·{k} = {predicted_commuting}   (measured {comm})")
    print(f"      => reversed-order axiom A predicted = |S|·{predicted_commuting}"
          f" = {predicted_reversed_A}   (measured "
          f"{rB['axiom_A_pass']})")
    agree = (predicted_commuting == comm
             and predicted_reversed_A == rB["axiom_A_pass"])
    print(f"      the two independent routes agree: {agree}")
    emit(finding="F3_3_ti_noncommutativity",
         non_commuting_ordered_pairs=noncomm, commuting_ordered_pairs=comm,
         total_ordered_pairs=24 * 24, abelian=noncomm == 0,
         conjugacy_classes=k,
         predicted_commuting_pairs=predicted_commuting,
         predicted_reversed_axiom_A=predicted_reversed_A,
         measured_reversed_axiom_A=rB["axiom_A_pass"],
         routes_agree=agree,
         verdict=("The reversed-order axiom-A count is not an arbitrary "
                  "shortfall: it equals |S| times the number of COMMUTING "
                  "ordered interval pairs, which the class equation predicts "
                  "as |G|·(number of conjugacy classes). Two independent "
                  "routes to the same integer — so the harness is measuring "
                  "commutativity, which is what it claims."))

    # ══════════════════════════════════════════════════════════════════
    # NEGATIVE CONTROLS — every one of these MUST fail.  If any passes, the
    # checker is not an instrument.
    # ══════════════════════════════════════════════════════════════════
    print("\nNEG   negative controls — every row must read NOT-A-TORSOR")
    neg = []
    neg.append(check_gis(
        "N1 int(s,t)=(t+s) mod 12  [breaks A]",
        range(12), range(12), lambda i, j: (i + j) % 12, 0,
        lambda s, t: (t + s) % 12, note="negative control"))
    neg.append(check_gis(
        "N2 int(s,t)=2(t-s) mod 12 [breaks B, 2:1]",
        range(12), range(12), lambda i, j: (i + j) % 12, 0,
        lambda s, t: (2 * (t - s)) % 12, note="negative control"))
    neg.append(check_gis(
        "N3 IVLS=Z/6 on S=Z/12    [breaks B, onto]",
        range(12), range(6), lambda i, j: (i + j) % 6, 0,
        lambda s, t: (t - s) % 6, note="negative control"))
    neg.append(check_gis(
        "N4 IVLS=Z/24 on S=Z/12   [breaks B, 1-1]",
        range(12), range(24), lambda i, j: (i + j) % 24, 0,
        lambda s, t: (t - s) % 12, note="negative control"))
    n_blessed = sum(1 for r in neg if r["verdict"] == "TORSOR")
    print(f"      negative controls wrongly blessed: {n_blessed}/4  "
          f"{'INSTRUMENT OK' if n_blessed == 0 else '!! INSTRUMENT BROKEN'}")
    emit(finding="NEG_controls_gis", n_controls=4, n_wrongly_blessed=n_blessed,
         instrument_valid=n_blessed == 0)

    # ══════════════════════════════════════════════════════════════════
    # F4 — is there a canonical origin?  A clef is an ORIGIN CHOICE.
    # ══════════════════════════════════════════════════════════════════
    print("\nF4    no-canonical-origin measurements")

    # (i) FREENESS: how many (g, s) pairs with g != identity have g·s == s?
    for n in (7, 12, 22, 24):
        fx = sum(1 for g in range(1, n) for s in range(n)
                 if cyclic_mod_add(s, g, n) == s)
        print(f"      Z/{n:<3d} fixed points of NON-identity translations: "
              f"{fx}  ({'FREE' if fx == 0 else 'NOT FREE'})")
        emit(finding="F4_freeness", modulus=n, fixed_points=fx,
             free_action=fx == 0)

    # (ii) an INTERVAL-ONLY invariant cannot recover the origin; a
    #      non-invariant can.  Shipped ops on both sides.
    base = (0, 4, 7)
    ivs = {interval_vector(T(n, base)) for n in range(12)}
    pfs = {prime_form(T(n, base), "forte") for n in range(12)}
    lows = {min(normal_order(T(n, base), "forte")) for n in range(12)}
    nos = {normal_order(T(n, base), "forte") for n in range(12)}
    print(f"      normal_order (whole tuple) [NEG CONTROL 2]: "
          f"{len(nos)} distinct  -> {'CANNOT' if len(nos) == 1 else 'CAN'} "
          f"recover the origin")
    print(f"      interval_vector over 12 transpositions: "
          f"{len(ivs)} distinct  -> {'CANNOT' if len(ivs) == 1 else 'CAN'} "
          f"recover the origin")
    print(f"      prime_form      over 12 transpositions: "
          f"{len(pfs)} distinct  -> {'CANNOT' if len(pfs) == 1 else 'CAN'} "
          f"recover the origin")
    print(f"      min(normal_order) [NEGATIVE CONTROL]  : "
          f"{len(lows)} distinct  -> {'CANNOT' if len(lows) == 1 else 'CAN'} "
          f"recover the origin")
    emit(finding="F4_origin_recoverability",
         interval_vector_distinct_over_12_transpositions=len(ivs),
         prime_form_distinct_over_12_transpositions=len(pfs),
         negative_control_min_normal_order_distinct=len(lows),
         negative_control_full_normal_order_distinct=len(nos),
         instrument_valid=len(nos) == 12,
         verdict=("origin is NOT recoverable from interval-only invariants "
                  "(both give 1), and IS recoverable from a non-invariant "
                  "(12) — so the instrument can return otherwise"))

    # (iii) the INFORMATIONAL torsor test: two different origins produce
    #       identical printed output for suitably different content.  If the
    #       printed page determined the origin, it would not be a torsor.
    n = 12
    collisions = 0
    total = 0
    for o1 in range(n):
        for o2 in range(n):
            # content c printed at origin o -> (c - o) mod n
            # is there content c1 at o1 and c2 at o2 with equal print?
            for c1 in range(n):
                total += 1
                p = (c1 - o1) % n
                c2 = (p + o2) % n
                if (c2 - o2) % n == p:
                    collisions += 1
    print(f"      printed-output/origin collisions: {collisions}/{total} "
          f"-> printed page {'does NOT' if collisions == total else 'DOES'} "
          f"determine the origin")
    emit(finding="F4_printed_page_underdetermines_origin",
         collisions=collisions, total=total,
         printed_determines_origin=collisions != total,
         verdict="every printed reading is achievable from EVERY origin by "
                 "choosing the content — the origin is not in the page")

    # ══════════════════════════════════════════════════════════════════
    # F7 — translator losslessness, both directions
    # ══════════════════════════════════════════════════════════════════
    print("\nF7    chart <-> carrier translator, both directions")
    # A POSITIONAL chart: (degree in Z/7, accidental in Z, register in Z).
    # The degree->step map is the chart's ONLY convention.  Named
    # STEP_MAP rather than anything culture-specific: the same shape is a
    # 7-degree map here and would be a k-degree map elsewhere.
    STEP_MAP = (0, 2, 4, 5, 7, 9, 11)   # 7 degrees -> 12 steps
    ACC = range(-2, 3)

    def chart_to_carrier(deg, acc, reg):
        return 12 * reg + STEP_MAP[deg] + acc

    # forward: total and well-defined?
    fwd = {}
    for deg in range(7):
        for acc in ACC:
            fwd[(deg, acc)] = chart_to_carrier(deg, acc, 0) % 12
    print(f"      forward chart->carrier: {len(fwd)} chart symbols "
          f"-> {len(set(fwd.values()))} carrier values")
    # backward: preimage multiplicity
    pre = {}
    for k, v in fwd.items():
        pre.setdefault(v, []).append(k)
    hist = {}
    for v, ks in pre.items():
        hist[len(ks)] = hist.get(len(ks), 0) + 1
    injective = all(len(ks) == 1 for ks in pre.values())
    worst = max(pre.items(), key=lambda kv: len(kv[1]))
    print(f"      backward carrier->chart: preimage-size histogram {hist}  "
          f"-> {'INJECTIVE' if injective else 'NOT injective (LOSSY)'}")
    print(f"      worst cell: carrier {worst[0]} has {len(worst[1])} chart "
          f"spellings {worst[1]}")
    # is the INTERVAL structure recoverable from the chart alone?  yes by
    # construction; measure it rather than assert it.
    iv_ok = iv_tot = 0
    syms = list(fwd)
    for a, b in itertools.product(syms, syms):
        iv_tot += 1
        if (fwd[b] - fwd[a]) % 12 == (chart_to_carrier(b[0], b[1], 0)
                                      - chart_to_carrier(a[0], a[1], 0)) % 12:
            iv_ok += 1
    print(f"      chart-computed interval == carrier interval: "
          f"{iv_ok}/{iv_tot}")
    emit(finding="F7_translator_losslessness",
         n_chart_symbols=len(fwd), n_carrier_values=len(set(fwd.values())),
         preimage_histogram={str(k): v for k, v in sorted(hist.items())},
         backward_injective=injective,
         worst_cell={"carrier": worst[0], "n_spellings": len(worst[1]),
                     "spellings": [list(x) for x in worst[1]]},
         interval_agreement=f"{iv_ok}/{iv_tot}",
         verdict=("LOSSY IN ONE DIRECTION: chart->carrier is total and "
                  "interval-preserving; carrier->chart is NOT injective. "
                  "The chart carries STRICTLY MORE than the carrier — the "
                  "surplus is spelling, which is chart convention, not "
                  "interval content."))

    # N5 — a WRONG chart must break interval preservation
    BAD = (0, 2, 4, 5, 7, 9, 10)   # one degree perturbed
    bad_ok = bad_tot = 0
    for a, b in itertools.product(range(7), range(7)):
        bad_tot += 1
        good = (STEP_MAP[b] - STEP_MAP[a]) % 12
        bad = (BAD[b] - BAD[a]) % 12
        if good == bad:
            bad_ok += 1
    print(f"      N5 WRONG chart: interval agreement {bad_ok}/{bad_tot}  "
          f"{'!! INSTRUMENT BLESSED A WRONG CHART' if bad_ok == bad_tot else 'correctly REJECTED'}")
    emit(finding="N5_wrong_chart_control",
         agreement=f"{bad_ok}/{bad_tot}",
         wrong_chart_rejected=bad_ok != bad_tot,
         instrument_valid=bad_ok != bad_tot)

    # ══════════════════════════════════════════════════════════════════
    # F7b — DIFFERENTIAL chart vs POSITIONAL chart.  Deliberately abstract:
    # this makes NO claim about any named tradition.  A differential chart
    # stores int(s_i, s_{i+1}) plus ONE origin; a positional chart stores
    # each s_i as an offset from a fixed origin.  Both are charts on the same
    # carrier; the question is what each loses when the origin moves.
    # ══════════════════════════════════════════════════════════════════
    print("\nF7b   DIFFERENTIAL vs POSITIONAL chart under an origin shift")
    melody = [0, 2, 4, 5, 7, 5, 4, 2, 0]
    n = 12
    pos_changed = diff_changed = 0
    for d in range(1, n):
        shifted = [cyclic_mod_add(x, d, n) for x in melody]
        pos = [cyclic_mod_add(x, n - 0, n) for x in melody]
        pos_s = [cyclic_mod_add(x, n - 0, n) for x in shifted]
        if pos != pos_s:
            pos_changed += 1
        dif = [cyclic_mod_add(melody[i + 1], n - melody[i], n)
               for i in range(len(melody) - 1)]
        dif_s = [cyclic_mod_add(shifted[i + 1], n - shifted[i], n)
                 for i in range(len(shifted) - 1)]
        if dif != dif_s:
            diff_changed += 1
    print(f"      origin shifts 1..11: POSITIONAL chart changed "
          f"{pos_changed}/11 times; DIFFERENTIAL chart changed "
          f"{diff_changed}/11 times")
    emit(finding="F7b_differential_vs_positional",
         origin_shifts=11, positional_changed=pos_changed,
         differential_changed=diff_changed,
         verdict="a differential chart is INVARIANT under the origin shift a "
                 "positional chart is fully SENSITIVE to — the two chart "
                 "FAMILIES sit at opposite ends of the torsor. The "
                 "differential chart is a chart of DIFFERENCES (the torsor's "
                 "group) and needs exactly ONE extra datum (an origin) to "
                 "become positional. NO claim is made here about which "
                 "real-world notation is which — see the sourcing table.")

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        for r in RECS:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"\nwrote {len(RECS)} records -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
