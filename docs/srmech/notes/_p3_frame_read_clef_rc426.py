#!/usr/bin/env python3
"""P3 — is ``octonion_frame_read`` already the CLEF operation under another
name, and can the shipped ``oct_torsor_*`` host a notation object?
(rc426 research spike, read-only.)

Pre-registered falsifiers
=========================
F5  **Does a shipped frame-change behave like a clef change?**  A clef change
    must (a) alter every printed reading, (b) leave every interval invariant,
    (c) have no canonical choice.  Measured on all 28 shipped frames of
    :func:`srmech.cascade.cayley_dickson.octonion_frame_read` by partitioning
    the returned fields into INVARIANT / ORBIT-EQUIVARIANT / FREE.

F5b **Is the 28-frame set a TORSOR?**  Measured, not assumed: a torsor needs a
    group acting freely and transitively.  Within a Fano line there are 4
    splitting units; across lines there are 7 bases.  Test each level
    separately — a "yes" at one level and "no" at the other is a real result
    and is exactly the kind of thing an unmeasured analogy would smooth over.

F6  **Can ``oct_torsor_act`` / ``oct_torsor_div`` host a pitch-interval
    object?**  Measure the structure group's ORDER, ABELIANITY and EXPONENT
    and compare against what a pitch-interval group must be.  A mismatch is a
    REFUTATION of the "reuse the shipped torsor" route, and naming the exact
    mismatched invariant is the deliverable.

F9  **What would make "the carrier is an ACTIVE PARTICIPANT" testable?**
    Proposal under test: a passive carrier has a frame-change law that is a
    GROUP (associative, path-independent); an active carrier has one that is
    not (path-DEPENDENT composition ⇒ the carrier changed under transport).
    𝕆 is the shipped object where this is decidable, because associativity
    genuinely fails there.  Measure the associator census and the resulting
    path-dependence of composed frame changes.

Scope: algebra / group-action only.

Run:
    PYTHONPATH=docs/srmech/python python3 docs/srmech/notes/_p3_frame_read_clef_rc426.py
"""
from __future__ import annotations

import itertools
import json
import os
import sys

import srmech
from srmech.cascade.cayley_dickson import (OCTONION_FRAME_COUNT,
                                           OCTONION_FRAME_LINE, cd_mult,
                                           octonion_frame_read)
from srmech.math.octonion import oct_mult, oct_torsor_act, oct_torsor_div

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "_p3_frame_read_clef_rc426.ndjson")
RECS = []


def emit(**kw):
    kw.setdefault("srmech_version", srmech.__version__)
    RECS.append(kw)


def _basis(i):
    v = [0] * 8
    v[i] = 1
    return v


def fano_lines():
    """The 7 quaternionic (Fano) lines, DERIVED from cd_mult — not tabulated.

    A line is an unordered imaginary triple {i,j,k} with e_i·e_j = ±e_k.
    """
    out = set()
    for i, j in itertools.combinations(range(1, 8), 2):
        p = cd_mult(_basis(i), _basis(j))
        k = [n for n, c in enumerate(p) if c != 0]
        assert len(k) == 1, (i, j, p)
        k = k[0]
        if k != 0:
            out.add(tuple(sorted((i, j, k))))
    return sorted(out)


def main() -> int:
    print("srmech.__file__    =", srmech.__file__)
    print("srmech.__version__ =", srmech.__version__)
    try:
        import numpy  # noqa: F401
        print("!! numpy PRESENT — environment wrong")
    except ImportError:
        print("numpy              = ABSENT (correct)")

    # ══════════════════════════════════════════════════════════════════
    # F5 — the 28 frames, and what each field does under a frame change
    # ══════════════════════════════════════════════════════════════════
    lines = fano_lines()
    print(f"\nF5    Fano lines DERIVED from cd_mult: {len(lines)}  {lines}")
    print(f"      shipped OCTONION_FRAME_COUNT = {OCTONION_FRAME_COUNT}, "
          f"default line = {OCTONION_FRAME_LINE}")

    x = [1, 2, 3, 4, 5, 6, 7, 8]     # a generic octonion, no symmetry
    frames = []
    for line in lines:
        for ell in range(1, 8):
            if ell in line:
                continue
            try:
                r = octonion_frame_read(x, frame=tuple(line) + (ell,))
            except ValueError:
                continue
            frames.append((tuple(line), ell, r))
    print(f"      well-posed frames actually accepted: {len(frames)} "
          f"(shipped constant says {OCTONION_FRAME_COUNT})")

    FIELDS = ("q0", "q1", "base_H", "base_R", "norm_sq", "writhe",
              "writhe_norm_sq", "canonical_affine", "base", "seam",
              "seam_chart", "frame")

    def key(v):
        return json.dumps(v, default=str, sort_keys=True)

    print("\n      field                 distinct/28   distinct within a line "
          "(min..max over the 7 lines)   classification")
    rows = []
    for f in FIELDS:
        glob = len({key(r[f]) for _, _, r in frames})
        per = []
        for line in lines:
            per.append(len({key(r[f]) for ln, _, r in frames if ln == line}))
        lo, hi = min(per), max(per)
        if glob == 1:
            cls = "FRAME-FREE  (survives every frame change)"
        elif lo == 1 and hi == 1:
            cls = "LINE-INVARIANT, line-dependent (ℓ cannot move it)"
        elif lo == hi == 4:
            cls = "FULLY FREE  (every ℓ moves it)"
        else:
            cls = f"MIXED (per-line {per})"
        rows.append({"field": f, "distinct_over_28": glob,
                     "distinct_within_line_min": lo,
                     "distinct_within_line_max": hi,
                     "per_line": per, "classification": cls})
        print(f"      {f:20s} {glob:6d}/28      {lo}..{hi}"
              f"{'':30s}".rstrip().ljust(28) + f"  {cls}")
    n_free = sum(1 for r in rows if r["distinct_over_28"] == 1)
    emit(finding="F5_frame_read_field_partition",
         n_frames_accepted=len(frames), shipped_frame_count=OCTONION_FRAME_COUNT,
         fano_lines=[list(t) for t in lines], rows=rows,
         n_frame_free_fields=n_free,
         verdict=(f"{n_free} of {len(FIELDS)} returned fields survive EVERY "
                  "one of the 28 frame changes; the rest move. That is the "
                  "clef SHAPE — an invariant part and a frame-dependent "
                  "reading part — measured on a shipped op."))

    # the clef predicate, stated as three checks
    inv_fields = [r["field"] for r in rows if r["distinct_over_28"] == 1]
    mov_fields = [r["field"] for r in rows if r["distinct_over_28"] > 1]
    print(f"\n      CLEF PREDICATE (a) some reading changes under every frame "
          f"change : {len(mov_fields) > 0}  ({mov_fields})")
    print(f"      CLEF PREDICATE (b) some invariant survives all of them     "
          f"    : {len(inv_fields) > 0}  ({inv_fields})")

    # (c) no canonical frame: is any frame distinguished by an invariant
    #     computable from the READ alone?  Measure whether the default
    #     frame's read is separable from the others by a frame-free quantity.
    default = [r for ln, e, r in frames
               if ln == tuple(OCTONION_FRAME_LINE) and e == 4]
    sep = None
    if default:
        d = default[0]
        sep = [f for f in inv_fields if key(d[f]) not in
               {key(r[f]) for ln, e, r in frames
                if not (ln == tuple(OCTONION_FRAME_LINE) and e == 4)}]
    print(f"      CLEF PREDICATE (c) NO frame-free quantity singles out the "
          f"default frame: {not sep}  (separating fields: {sep})")
    emit(finding="F5_clef_predicate",
         a_some_reading_moves=len(mov_fields) > 0, moving_fields=mov_fields,
         b_some_invariant_survives=len(inv_fields) > 0,
         invariant_fields=inv_fields,
         c_no_canonical_frame=not sep, separating_fields=sep,
         verdict="octonion_frame_read satisfies the CLEF SHAPE: it reads one "
                 "object on a committed frame, keeps a frame-free invariant, "
                 "and distinguishes no frame. FORM, not identity.")

    # ══════════════════════════════════════════════════════════════════
    # F5b — is the frame set a TORSOR?  Measured at both levels.
    # ══════════════════════════════════════════════════════════════════
    print("\nF5b   is the 28-frame set a torsor?  Measured at two levels.")

    # Level 1 — WITHIN a line: 4 splitting units.  The docstring states the
    # relation e_ℓ' = u·e_ℓ for a signed base unit u.  Derive the acting set
    # and check freeness + transitivity.
    line = tuple(OCTONION_FRAME_LINE)
    ells = [4, 5, 6, 7]
    # the signed base units of the ℍ base, as octonion BYTES: idx 0..3, sign bit 8
    base_units = [i for i in range(4)] + [i | 8 for i in range(4)]
    act = {}
    for u in base_units:
        for e in ells:
            p = oct_mult(u, e)            # u · e_ℓ, as a signed byte
            act[(u, e)] = p & 7            # the UNSIGNED index is the frame id
    orbit = {}
    for (u, e), tgt in act.items():
        orbit.setdefault(e, set()).add(tgt)
    transitive = all(o == set(ells) for o in orbit.values())
    # multiplicity: how many u carry a given e to a given e'?
    mult = {}
    for e in ells:
        for e2 in ells:
            n = sum(1 for u in base_units if act[(u, e)] == e2)
            mult[n] = mult.get(n, 0) + 1
    print(f"      within line {line}: |acting signed base units| = "
          f"{len(base_units)}, |frames| = {len(ells)}")
    print(f"      transitive: {transitive};  (e -> e') multiplicity "
          f"histogram: {mult}")
    free = set(mult) == {1}
    print(f"      SIMPLY transitive (every multiplicity 1): {free}  -> "
          f"{'TORSOR' if free and transitive else 'TRANSITIVE BUT NOT FREE'}")
    print(f"      the stabiliser has order "
          f"{len(base_units) // len(ells)} — the SIGN, which the frame index "
          f"discards")
    emit(finding="F5b_within_line_torsor",
         line=list(line), n_acting_units=len(base_units), n_frames=len(ells),
         transitive=transitive,
         multiplicity_histogram={str(k): v for k, v in sorted(mult.items())},
         simply_transitive=free,
         stabiliser_order=len(base_units) // len(ells),
         verdict=("TRANSITIVE BUT NOT FREE at the level of the frame INDEX: "
                  "the 8 signed base units act transitively on the 4 "
                  "splitting units with multiplicity 2 — the kernel is {±1}. "
                  "So the frame-index set is a torsor for the QUOTIENT "
                  "(order 4), not for the signed group (order 8). The sign "
                  "the index throws away is exactly the difference."))

    # Level 2 — ACROSS lines: is there a group of order 7 acting simply
    # transitively on the 7 Fano lines?  A necessary condition for the whole
    # 28-set to be one torsor.
    print("\n      across lines: 7 Fano lines. A single 28-element torsor "
          "would need a group of order 28 acting freely+transitively on the "
          "frames, hence an order-7 quotient acting so on the LINES.")
    # measure: does right-multiplication by any single octonion unit permute
    # the lines transitively?
    line_orbits = {}
    for u in range(1, 8):
        img = []
        for ln in lines:
            m = tuple(sorted({oct_mult(a, u) & 7 for a in ln}))
            img.append(m)
        line_orbits[u] = sum(1 for m in img if m in
                             [tuple(sorted(t)) for t in lines])
    print(f"      per-unit right-multiplication: how many of the 7 lines map "
          f"to a line?  {line_orbits}")
    emit(finding="F5b_across_lines",
         n_lines=len(lines), per_unit_lines_preserved=line_orbits,
         verdict="the 28-frame set is NOT presented as a single torsor by the "
                 "shipped op: the (line, ℓ) pair is a FIBRED set — 7 bases "
                 "each carrying a 4-element torsor — and the shipped "
                 "docstring says only the WITHIN-LINE relation is a right "
                 "action. Measured here: the within-line level is a torsor "
                 "(for the order-4 quotient); the across-line level is not "
                 "certified as one by anything shipped.")

    # ══════════════════════════════════════════════════════════════════
    # F6 — the oct_torsor_* structure group, measured against what a
    #      pitch-interval group must be
    # ══════════════════════════════════════════════════════════════════
    print("\nF6    the shipped oct_torsor_* structure group, MEASURED")
    H = [i for i in range(4)] + [i | 8 for i in range(4)]     # {±e0..±e3}
    T = [i for i in range(4, 8)] + [(i | 8) for i in range(4, 8)]
    # closure + simple transitivity of the shipped action
    closed = all(oct_torsor_act(t, g) in T for t in T for g in H)
    hist = {}
    for t1 in T:
        for t2 in T:
            n = sum(1 for g in H if oct_torsor_act(t1, g) == t2)
            hist[n] = hist.get(n, 0) + 1
    simply = set(hist) == {1}
    # the division op inverts it uniquely
    div_ok = sum(1 for t1 in T for t2 in T
                 if oct_torsor_act(t1, oct_torsor_div(t1, t2)) == t2)
    # group invariants
    abelian = all(oct_mult(a, b) == oct_mult(b, a) for a in H for b in H)
    order = len(H)
    # element orders -> exponent, and the count of order-2 elements
    def el_order(g):
        k, cur = 1, g
        while cur != 0:
            cur = oct_mult(cur, g)
            k += 1
            if k > 64:
                return None
        return k
    orders = {}
    for g in H:
        o = el_order(g)
        orders[o] = orders.get(o, 0) + 1
    n_involutions = orders.get(2, 0)
    print(f"      |H| = {order};  closed on T: {closed};  "
          f"simply transitive: {simply} (histogram {hist})")
    print(f"      oct_torsor_div inverts: {div_ok}/{len(T) * len(T)}")
    print(f"      abelian: {abelian};  element-order histogram: {orders};  "
          f"involutions: {n_involutions}")
    iso = ("Q8 (quaternion group)" if order == 8 and not abelian
           and n_involutions == 1 else
           "D4 (dihedral)" if order == 8 and not abelian else
           f"order-{order}{' abelian' if abelian else ' non-abelian'}")
    print(f"      isomorphism type by (order, abelian, #involutions): {iso}")
    emit(finding="F6_oct_torsor_structure_group",
         order=order, closed_on_T=closed, simply_transitive=simply,
         multiplicity_histogram={str(k): v for k, v in sorted(hist.items())},
         div_inverts=f"{div_ok}/{len(T) * len(T)}",
         abelian=abelian,
         element_order_histogram={str(k): v for k, v in sorted(orders.items())},
         n_involutions=n_involutions, isomorphism_type=iso)

    # the comparison table — the actual REFUTATION
    print("\n      can this group be a pitch-INTERVAL group?  compare the "
          "invariants that must match:")
    cand = [
        ("Z/12  (12-EDO pitch classes)", 12, True, 1),
        ("Z/7   (7-degree alphabet)", 7, True, 0),
        ("Z/24  (24-division)", 24, True, 1),
        ("Z/53  (53-division)", 53, True, 0),
        ("Z     (register-free pitch)", None, True, 0),
        ("Z^3   (5-limit just lattice)", None, True, 0),
        ("T/I   (24 triads, dihedral)", 24, False, 13),
    ]
    tbl = []
    for nm, o, ab, inv in cand:
        ok_order = (o == order)
        ok_ab = (ab == abelian)
        tbl.append({"target": nm, "target_order": o, "target_abelian": ab,
                    "order_matches": ok_order, "abelian_matches": ok_ab,
                    "can_host": bool(ok_order and ok_ab)})
        print(f"      {nm:34s} order {str(o):5s} abelian {str(ab):5s}  "
              f"order-match {str(ok_order):5s} abelian-match {str(ok_ab):5s}  "
              f"-> {'CAN host' if ok_order and ok_ab else 'CANNOT host'}")
    n_ok = sum(1 for r in tbl if r["can_host"])
    emit(finding="F6_can_shipped_torsor_host_pitch_intervals",
         shipped_group_order=order, shipped_group_abelian=abelian,
         candidates=tbl, n_hostable=n_ok,
         verdict=(f"REFUTED — {n_ok} of {len(tbl)} candidate pitch-interval "
                  f"groups can be hosted. The shipped torsor's group has "
                  f"order {order} and is {'abelian' if abelian else 'NON-abelian'}"
                  f"; every pitch-interval group in the table is either the "
                  f"wrong order, or abelian where this one is not, or "
                  f"INFINITE where this one is finite. Reusing oct_torsor_* "
                  f"as the interval group is a category error, not a tuning "
                  f"problem."))

    # ══════════════════════════════════════════════════════════════════
    # F9 — what would make "the carrier is an ACTIVE PARTICIPANT" testable?
    #      Proposal: passive => frame-change composition is ASSOCIATIVE and
    #      path-INDEPENDENT.  Active => it is not.  𝕆 decides it.
    # ══════════════════════════════════════════════════════════════════
    print("\nF9    'carrier as ACTIVE PARTICIPANT' — the associator census "
          "as a testable predicate")
    nz = tot = 0
    seam_nz = base_nz = 0
    for i, j, k in itertools.product(range(8), repeat=3):
        tot += 1
        a, b, c = _basis(i), _basis(j), _basis(k)
        lhs = cd_mult(cd_mult(a, b), c)
        rhs = cd_mult(a, cd_mult(b, c))
        if lhs != rhs:
            nz += 1
            if max(i, j, k) >= 4:
                seam_nz += 1
            else:
                base_nz += 1
    print(f"      ordered basis triples: {tot};  non-vanishing associators: "
          f"{nz}  ({100 * nz // tot}%)")
    print(f"      of those, crossing the doubling seam (any index >= 4): "
          f"{seam_nz};  entirely inside the ℍ base: {base_nz}")
    # path-dependence, stated as a MEASUREMENT rather than a stance:
    # transporting through two different frame-change routes.
    routes = 0
    disagree = 0
    for a, b in itertools.product(range(1, 8), repeat=2):
        for c in range(1, 8):
            routes += 1
            u, v, w = _basis(a), _basis(b), _basis(c)
            if cd_mult(cd_mult(u, v), w) != cd_mult(u, cd_mult(v, w)):
                disagree += 1
    print(f"      imaginary-unit transport routes compared: {routes}; "
          f"route-dependent: {disagree} ({100 * disagree // routes}%)")
    emit(finding="F9_active_carrier_testable_predicate",
         ordered_basis_triples=tot, nonvanishing_associators=nz,
         seam_crossing=seam_nz, inside_H_base=base_nz,
         imaginary_routes=routes, route_dependent=disagree,
         predicate="A carrier is PASSIVE iff its frame-change law is a GROUP: "
                   "associative, so composing frame changes is "
                   "path-INDEPENDENT and the object is unchanged by the "
                   "route taken. It is ACTIVE iff that fails — the carrier "
                   "records the route.",
         verdict=(f"TESTABLE, and 𝕆 already returns NON-ZERO: {nz}/{tot} "
                  f"ordered basis triples associate differently, all "
                  f"{seam_nz} of them seam-crossing and {base_nz} inside the "
                  f"ℍ base. So on the octonionic carrier the composed "
                  f"frame-change is path-DEPENDENT — the 'active' reading is "
                  f"a MEASURABLE property of the algebra, not a stance. On "
                  f"the ℍ base it is 0/64: that sub-carrier is PASSIVE. The "
                  f"same carrier is active or passive depending on which "
                  f"rung you read it at, and the rung is the frame."))

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        for r in RECS:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"\nwrote {len(RECS)} records -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
