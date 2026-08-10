"""#T1114 — TEST B: does φ's PAIRWISE (k=2) content factor apart from its
CYCLIC (k=3) content?

φ = `cd_three_form` — the exact-ℚ G₂ associative 3-form, "the `ab:bc:ca`
ternary object" (§3.46.11).  Its structure holds three pairwise (k=2)
relations arranged in a (k=3) cycle.

    FACTORS          ⇒ ⊗ ⇒ agrees with a leg-(d) PASS
    DOES NOT FACTOR  ⇒ ⋊ ⇒ agrees with a leg-(d) FAIL

k=3 SENSE DECLARATION (§3.29.3 `:5483` forbids conflating the four senses):
this test uses **sense 4, the associator triangle** — the carrier's own
k=3 loop defect.  Test A uses **sense 3, rep-triality τ / Aut(V₄)=S₃**.
They are DIFFERENT k=3 objects and nothing here claims otherwise.

THE FOUR MEASUREMENTS
  B1  S₃-representation content of φ and of the associator.  S₃ = ℤ/3 ⋊ ℤ/2 is
      itself the archetypal semidirect product: ℤ/3 = the cycle, ℤ/2 = naming a
      pair.  If a quantity transforms by the sign CHARACTER sgn(σ), the S₃
      action on it factors through the abelianisation S₃/A₃ = ℤ/2 — the cycle
      contributes +1 and the transposition −1, independently.  That is the
      FACTORS signal ON THAT QUANTITY.
  B2  The pair-naming test, verbatim from the question: bind each of the three
      pairs first and ask whether the cycle's report changes.  Six nestings.
  B3  The 0/19 base leak — twist, or artifact?  Separated into
        (i)   leak under S₃ PERMUTATION of the slots       (the pair/cycle axis)
        (ii)  leak under REGROUPING of the brackets        (the associativity axis)
        (iii) frame dependence (`octonion_frame_read(frame=…)`)
      An artifact would move with the frame; a pair/cycle twist would show in
      (i); an associativity defect shows only in (ii).
  B4  The 7-of-35 vs 168 reconciliation, counted through the ops.

NEGATIVE CONTROLS (mandatory)
  MUST-FACTOR  ℍ (dim 4) — associative, so every bracketing agrees;
               `group_algebra_table` — commutative + associative.
  MUST-NOT-FACTOR  `flip_pair(8, i, j)` — the shipped one-named-bit control
               breaks FLEXIBILITY, so the associator must lose the sign
               character;  and 𝕊 (dim 16) on SEAM-CROSSING inputs, where
               alternativity fails (a basis-only probe at 𝕊 is known to lie —
               §3.29.3).

Exact ℚ, numpy-free, no abs() (magnitudes only ever as Class-N squared norms;
signs only ever as Class-K pins), no fractions/math/decimal.
Run: cd docs/srmech/python && PYTHONPATH=$PWD python3 ../notes/phi_pair_cycle_factorisation_rc420.py
"""
from __future__ import annotations

import json
import sys
from itertools import permutations, product

import srmech
from srmech.cascade.atoms import net_chirality, pin_slot_at_zero
from srmech.cascade.cayley_dickson import (
    associator,
    cd_basis,
    cd_conjugate,
    cd_mult,
    cd_norm_sq,
    cd_three_form,
    flip_pair,
    group_algebra_table,
    octonion_frame_read,
    table_product,
)
from srmech.math.modular_linalg import gf_rref
from srmech.introspect.tool_schema import get_tool_schema, warmup_all

OUT = []


def emit(**rec):
    OUT.append(rec)


SGN = {(0, 1, 2): 1, (1, 2, 0): 1, (2, 0, 1): 1,
       (1, 0, 2): -1, (0, 2, 1): -1, (2, 1, 0): -1}
CYCLES = ((0, 1, 2), (1, 2, 0), (2, 0, 1))
TRANSPOSITIONS = ((1, 0, 2), (0, 2, 1), (2, 1, 0))


def E(dim, i):
    return cd_basis(dim, i)


def _pin(v):
    orientation, _ = pin_slot_at_zero(v)
    return orientation


def _neg(t):
    """Class-C reorientation of a tuple (never a bare abs / magnitude strip)."""
    return tuple(net_chirality([-1]) * v for v in t)


def _scale(s, t):
    return tuple(s * v for v in t)


# ── the deterministic 19 generic triples of §3.46.11 (same LCG, exact ints) ──
def _lcg_stream(seed, n):
    x = seed
    out = []
    for _ in range(n):
        x = (1103515245 * x + 12345) % (2 ** 31)
        out.append((x % 15) - 7)
    return out


def _generic_triples():
    vals = _lcg_stream(20260803, 8 * 3 * 200)
    octs = []
    idx = 0
    while len(octs) < 60:
        v = tuple(vals[idx:idx + 8])
        idx += 8
        if any(v[m] != 0 for m in range(4)) and any(v[m] != 0 for m in range(4, 8)):
            octs.append(v)
    return [(octs[i], octs[i + 1], octs[i + 2]) for i in range(0, 57, 3)]


TRIPLES = _generic_triples()


# ══════════════════════════════════════════════════════════════════════════
# B1 — the S₃-representation content
# ══════════════════════════════════════════════════════════════════════════
def s3_content(dim, table=None, label=""):
    """Does φ / the associator transform by the S₃ sign character?

    Split the census into the ℤ/3 (cycle) part and the ℤ/2 (pair-naming) part
    so the two factors are reported SEPARATELY — that separation IS the
    factorisation question."""
    im = list(range(1, dim))
    kw = {} if table is None else {"table": table}
    tot = phi_cyc = phi_tr = phi_full = phi_sym = phi_1dim = 0
    a_cyc = a_tr = a_full = a_sym = a_1dim = 0
    for a, b, c in product(im, repeat=3):
        t = (E(dim, a), E(dim, b), E(dim, c))
        p0 = cd_three_form(t[0], t[1], t[2], **kw)
        A0 = tuple(associator(t[0], t[1], t[2], **kw))
        tot += 1
        ok_pc = ok_pt = ok_ac = ok_at = True
        ok_ps = ok_as = True          # the TRIVIAL character (fully symmetric)
        for perm in CYCLES:
            if cd_three_form(t[perm[0]], t[perm[1]], t[perm[2]], **kw) != p0:
                ok_pc = False
            if tuple(associator(t[perm[0]], t[perm[1]], t[perm[2]], **kw)) != A0:
                ok_ac = False
        for perm in TRANSPOSITIONS:
            pp = cd_three_form(t[perm[0]], t[perm[1]], t[perm[2]], **kw)
            Ap = tuple(associator(t[perm[0]], t[perm[1]], t[perm[2]], **kw))
            if pp != -p0:
                ok_pt = False
            if pp != p0:
                ok_ps = False
            if Ap != _neg(A0):
                ok_at = False
            if Ap != A0:
                ok_as = False
        phi_cyc += ok_pc
        phi_tr += ok_pt
        phi_sym += (ok_pc and ok_ps)
        phi_full += (ok_pc and ok_pt)
        # a 1-DIMENSIONAL character of S₃ is trivial or sign; BOTH kill A₃, i.e.
        # BOTH factor through S₃/A₃ = ℤ/2 — that is the FACTORS signal.
        phi_1dim += (ok_pc and (ok_pt or ok_ps))
        a_cyc += ok_ac
        a_tr += ok_at
        a_sym += (ok_ac and ok_as)
        a_full += (ok_ac and ok_at)
        a_1dim += (ok_ac and (ok_at or ok_as))
    return dict(label=label, dim=dim, ordered_imaginary_triples=tot,
                phi_z3_invariant=phi_cyc, phi_transposition_anti=phi_tr,
                phi_sign_character=phi_full, phi_trivial_character=phi_sym,
                phi_one_dim_character=phi_1dim,
                assoc_z3_invariant=a_cyc, assoc_transposition_anti=a_tr,
                assoc_sign_character=a_full, assoc_trivial_character=a_sym,
                assoc_one_dim_character=a_1dim,
                factors=(phi_1dim == tot and a_1dim == tot))


# ══════════════════════════════════════════════════════════════════════════
# B2 — the pair-naming test
# ══════════════════════════════════════════════════════════════════════════
def _six_nestings(a, b, c, table=None):
    """The three named pairs × the two sides, in cyclic order:
        name ab -> (ab)c , c(ab)      name bc -> a(bc) , (bc)a
        name ca -> b(ca) , (ca)b """
    mul = (lambda x, y: cd_mult(x, y)) if table is None else \
          (lambda x, y: table_product(table, x, y))
    ab, bc, ca = mul(a, b), mul(b, c), mul(c, a)
    return {
        "name_ab_left": mul(ab, c), "name_ab_right": mul(c, ab),
        "name_bc_left": mul(a, bc), "name_bc_right": mul(bc, a),
        "name_ca_left": mul(b, ca), "name_ca_right": mul(ca, b),
    }


def pair_naming(triples, table=None, label="", frame=4, dim=8):
    """Does NAMING a pair change what the cycle reports?"""
    scal_same = base_same = norm_same = 0
    scal_same_left = 0
    n = 0
    for a, b, c in triples:
        nests = _six_nestings(a, b, c, table)
        vals = list(nests.values())
        n += 1
        scal = {v[0] for v in vals}
        nrm = {cd_norm_sq(v) for v in vals}
        if len(scal) == 1:
            scal_same += 1
        if len(nrm) == 1:
            norm_same += 1
        lefts = [nests[k][0] for k in nests if k.endswith("_left")]
        if len(set(lefts)) == 1:
            scal_same_left += 1
        if dim == 8:
            bases = {(tuple(octonion_frame_read(v, frame=frame)["base_H"]),
                      octonion_frame_read(v, frame=frame)["base_R"]) for v in vals}
            if len(bases) == 1:
                base_same += 1
    return dict(label=label, n=n, frame=frame,
                scalar_report_invariant_all6=scal_same,
                scalar_report_invariant_left3=scal_same_left,
                norm_report_invariant_all6=norm_same,
                base_report_invariant_all6=(base_same if dim == 8 else None))


def main():
    warmup_all()
    emit(kind="env", version=srmech.__version__, srmech_file=srmech.__file__,
         registry=len(get_tool_schema().tools),
         has_native=bool(getattr(srmech, "HAS_NATIVE", False)),
         numpy_present="numpy" in sys.modules,
         task="#T1114", test="B — the φ factorisation",
         k3_sense="sense 4 (the associator triangle). Test A used sense 3 "
                  "(rep-triality tau). Different objects; no identity claimed.")

    # ── B1: the S₃ content, and its controls ─────────────────────────────
    emit(kind="B1_s3_content", **s3_content(4, label="H (dim 4) — MUST-FACTOR control"))
    emit(kind="B1_s3_content", **s3_content(8, label="O (dim 8) — the measurement"))
    emit(kind="B1_s3_content",
         **s3_content(8, table=group_algebra_table(8),
                      label="group_algebra_table(8) — MUST-FACTOR control "
                            "(here φ carries the TRIVIAL character, not the "
                            "sign one — both are 1-dim, both factor)"))
    emit(kind="B1_s3_content",
         **s3_content(8, table=flip_pair(8, 1, 2),
                      label="flip_pair(8,1,2) — MUST-NOT-FACTOR control"))
    emit(kind="B1_s3_content",
         **s3_content(16, label="S (dim 16) basis — MUST-NOT-FACTOR control"))

    # 𝕊 basis probe (known to LIE — §3.29.3 rung-4 is not basis-visible) and
    # the seam-crossing probe that does not.
    seam_a = tuple(1 if k in (1, 10) else 0 for k in range(16))
    seam_b = tuple(1 if k in (2, 9) else 0 for k in range(16))
    seam_c = tuple(1 if k in (4,) else 0 for k in range(16))
    sgn_ok = 0
    A0 = tuple(associator(seam_a, seam_b, seam_c))
    p0 = cd_three_form(seam_a, seam_b, seam_c)
    rows = []
    t = (seam_a, seam_b, seam_c)
    for perm in permutations((0, 1, 2)):
        s = SGN[perm]
        Ap = tuple(associator(t[perm[0]], t[perm[1]], t[perm[2]]))
        pp = cd_three_form(t[perm[0]], t[perm[1]], t[perm[2]])
        ok = (Ap == _scale(s, A0)) and (pp == s * p0)
        sgn_ok += ok
        rows.append({"perm": list(perm), "sgn": s, "assoc_sign_char": Ap == _scale(s, A0),
                     "phi_sign_char": pp == s * p0})
    emit(kind="B1_sedenion_seam_control",
         label="S (dim 16) SEAM-CROSSING — MUST-NOT-FACTOR control",
         inputs={"a": "e1+e10", "b": "e2+e9", "c": "e4"},
         sign_character_holds=f"{sgn_ok}/6", rows=rows,
         note="a basis-only probe at S falsely reports alternativity (§3.29.3); "
              "the seam-crossing input is the one that can return otherwise")

    # ── B2: the pair-naming test ─────────────────────────────────────────
    emit(kind="B2_pair_naming",
         **pair_naming(TRIPLES, label="O generic 19 (the §3.46.11 triples)"))
    basis_triples = [(E(8, i), E(8, j), E(8, k))
                     for i, j, k in ((1, 2, 4), (1, 2, 3), (2, 4, 6), (1, 4, 6))]
    emit(kind="B2_pair_naming", **pair_naming(basis_triples, label="O basis triples"))
    quat = [(tuple(list(a[:4]) + [0] * 4), tuple(list(b[:4]) + [0] * 4),
             tuple(list(c[:4]) + [0] * 4)) for a, b, c in TRIPLES]
    emit(kind="B2_pair_naming",
         **pair_naming(quat, label="H-embedded (associative) — MUST-FACTOR control "
                                   "(base read is DEGENERATE here: q1 == 0)"))
    emit(kind="B2_pair_naming",
         **pair_naming(TRIPLES, table=group_algebra_table(8),
                       label="group_algebra_table(8) — MUST-FACTOR control, "
                             "NON-degenerate (both halves nonzero)"))

    # the frame-dependence discriminator is NOT runnable through the shipped op
    frame_err = None
    try:
        octonion_frame_read(TRIPLES[0][0], frame=2)
    except ValueError as exc:
        frame_err = str(exc)[:200]
    emit(kind="B3_frame_variation_unavailable",
         op="octonion_frame_read", accepted_frame=4, error=frame_err,
         note="the artifact-vs-structure test 'does the leak move with the "
              "frame?' cannot be run through the shipped op — it is hard-pinned "
              "to the standard doubling seam l = e4. 𝕆 has SEVEN ℍ subalgebras "
              "(one per Fano line); the op reads one. REPORTABLE GAP, not a "
              "workaround: no foreign module was used to route around it.")

    # ── B3: the base leak, split by AXIS ─────────────────────────────────
    # (i) under S₃ permutation of the slots — the pair/cycle axis.
    # (ii) under regrouping of the brackets — the associativity axis.
    perm_inv = regroup_inv = 0
    perm_inv_upto_sign = 0
    signflip = 0
    for a, b, c in TRIPLES:
        L = cd_mult(cd_mult(a, b), c)
        R = cd_mult(a, cd_mult(b, c))
        rL, rR = octonion_frame_read(L), octonion_frame_read(R)
        if rL["base_H"] == rR["base_H"] and rL["base_R"] == rR["base_R"]:
            regroup_inv += 1
        # Class-K pin on the product of the two base_R orientations.
        if net_chirality([_pin(rL["base_R"]), _pin(rR["base_R"])]) == -1:
            signflip += 1
        # the S₃ axis: hold the BRACKETING fixed, permute the slots
        base0 = (tuple(rL["base_H"]), rL["base_R"])
        same = same_sign = True
        for perm in permutations((0, 1, 2)):
            t = (a, b, c)
            P = cd_mult(cd_mult(t[perm[0]], t[perm[1]]), t[perm[2]])
            rP = octonion_frame_read(P)
            if (tuple(rP["base_H"]), rP["base_R"]) != base0:
                same = False
            if (tuple(rP["base_H"]), rP["base_R"]) not in (
                    base0, (tuple(_neg(base0[0])), -base0[1])):
                same_sign = False
        perm_inv += same
        perm_inv_upto_sign += same_sign
    emit(kind="B3_base_leak_axes", n=len(TRIPLES),
         base_invariant_under_REGROUPING=regroup_inv,
         base_R_sign_flips_under_regrouping=signflip,
         base_invariant_under_S3_PERMUTATION=perm_inv,
         base_invariant_under_S3_upto_sign=perm_inv_upto_sign,
         reads="if the leak were the pair/cycle (S₃) twist it would show in the "
               "PERMUTATION column; if it is the associativity defect it shows "
               "only in the REGROUPING column")

    # (iii) the associator's coordinate census — the notebook's own mechanism
    cls = {"zero": 0, "base_only": 0, "seam_only": 0, "mixed": 0}
    input_seam = {"nonzero_input_crosses_seam": 0, "nonzero_input_within_H": 0}
    for i, j, k in product(range(8), repeat=3):
        A = associator(E(8, i), E(8, j), E(8, k))
        if all(v == 0 for v in A):
            cls["zero"] += 1
            continue
        base = any(A[m] != 0 for m in (1, 2, 3))
        seam = any(A[m] != 0 for m in (4, 5, 6, 7))
        cls["mixed" if (base and seam) else ("base_only" if base else "seam_only")] += 1
        if max(i, j, k) >= 4:
            input_seam["nonzero_input_crosses_seam"] += 1
        else:
            input_seam["nonzero_input_within_H"] += 1
    emit(kind="B3_associator_census", classes=cls, input_side=input_seam,
         note="OUTPUT-coordinate census (base-half vs seam) is a DIFFERENT "
              "statement from the INPUT-triple seam-crossing census in "
              "octonion_frame_read's docstring; both measured here so they "
              "cannot be conflated")

    # ── B4: 7-of-35 vs 168, counted through the ops ──────────────────────
    im = list(range(1, 8))
    phi_unordered = phi_ordered = 0
    assoc_unordered = assoc_ordered = 0
    lines = []
    for i, j, k in product(im, repeat=3):
        p = cd_three_form(E(8, i), E(8, j), E(8, k))
        A = associator(E(8, i), E(8, j), E(8, k))
        if p != 0:
            phi_ordered += 1
        if any(v != 0 for v in A):
            assoc_ordered += 1
    for i in im:
        for j in im:
            for k in im:
                if i < j < k:
                    p = cd_three_form(E(8, i), E(8, j), E(8, k))
                    if p != 0:
                        phi_unordered += 1
                        lines.append([i, j, k, int(_pin(p))])
                    if any(v != 0 for v in associator(E(8, i), E(8, j), E(8, k))):
                        assoc_unordered += 1
    # |GL(3,2)| as the count of ordered F₂³ bases, via the shipped GF rref.
    indep = 0
    for x, y, z in product(im, repeat=3):
        r = gf_rref([[(x >> b) & 1 for b in range(3)],
                     [(y >> b) & 1 for b in range(3)],
                     [(z >> b) & 1 for b in range(3)]], 2)
        if r["rank"] == 3:
            indep += 1
    emit(kind="B4_reconciliation",
         unordered_3subsets=35, phi_support_unordered=phi_unordered,
         phi_support_ordered=phi_ordered,
         assoc_support_unordered=assoc_unordered,
         assoc_support_ordered=assoc_ordered,
         ordered_F2_independent_triples=indep,
         gl_3_2_order=7 * 6 * 4,
         checks={"35 = 7 + 28": 35 == phi_unordered + assoc_unordered,
                 "phi ordered == 7*6 == 42": phi_ordered == phi_unordered * 6,
                 "assoc ordered == 28*6 == 168": assoc_ordered == assoc_unordered * 6,
                 "42 + 168 == 210 == 7*6*5": phi_ordered + assoc_ordered == 7 * 6 * 5,
                 "343 - 210 == 133 (ordered triples with a repeat)":
                     343 - (phi_ordered + assoc_ordered) == 133,
                 "det3-support == assoc-support == |GL(3,2)|":
                     indep == assoc_ordered == 168},
         fano_lines=lines,
         note="phi's support is the 7 LINES (42 ordered); 168 is its COMPLEMENT "
              "(the 28 non-lines, 42+168=210). |GL(3,2)|=168 coincides for a "
              "REASON: GL(3,2) acts simply transitively on ordered F2^3 bases, "
              "so |GL(3,2)| IS the number of ordered independent triples.")

    # ── VERDICT ──────────────────────────────────────────────────────────
    b1 = [r for r in OUT if r["kind"] == "B1_s3_content"]
    b2 = [r for r in OUT if r["kind"] == "B2_pair_naming"]
    emit(kind="verdict", test="B — the φ factorisation",
         b1_summary=[{"label": r["label"],
                      "phi_1dim_character":
                      f"{r['phi_one_dim_character']}/{r['ordered_imaginary_triples']}",
                      "assoc_1dim_character":
                      f"{r['assoc_one_dim_character']}/{r['ordered_imaginary_triples']}",
                      "phi_sign_character":
                      f"{r['phi_sign_character']}/{r['ordered_imaginary_triples']}",
                      "phi_trivial_character":
                      f"{r['phi_trivial_character']}/{r['ordered_imaginary_triples']}",
                      "assoc_sign_character":
                      f"{r['assoc_sign_character']}/{r['ordered_imaginary_triples']}",
                      "factors": r["factors"]}
                     for r in b1],
         b2_summary=[{"label": r["label"],
                      "scalar_all6": f"{r['scalar_report_invariant_all6']}/{r['n']}",
                      "scalar_left3": f"{r['scalar_report_invariant_left3']}/{r['n']}",
                      "norm_all6": f"{r['norm_report_invariant_all6']}/{r['n']}",
                      "base_all6": r["base_report_invariant_all6"]} for r in b2])

    path = __file__.replace(".py", ".ndjson")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for rec in OUT:
            fh.write(json.dumps(rec, sort_keys=True, default=str) + "\n")
    print(f"wrote {len(OUT)} records -> {path}")
    for rec in OUT:
        if rec["kind"] in ("B1_s3_content", "B2_pair_naming", "B3_base_leak_axes",
                           "B3_associator_census", "B4_reconciliation",
                           "B1_sedenion_seam_control", "verdict"):
            print(json.dumps(rec, sort_keys=True, default=str)[:1400])


if __name__ == "__main__":
    main()
