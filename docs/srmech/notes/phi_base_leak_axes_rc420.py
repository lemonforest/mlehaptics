"""#T1114 — TEST B supplement: is §3.46.11's 0/19 Hopf-base leak the pair/cycle
TWIST, or something else?

§3.46.11 measured that the vector Hopf base is regrouping-invariant on **0 of
19** generic octonion triples (and `base_R` sign-flips on 11/19) while the
scalar φ and the norm N are invariant 19/19.  That is a real refutation of an
earlier guess.  What it does NOT say is which AXIS the leak lives on.  Three
axes are conflated in "the base moves":

  (i)   REGROUPING        (ab)c  vs  a(bc)      — the associativity axis (k=3,
                                                  §3.29.3 sense 4)
  (ii)  CYCLIC ROTATION   abc    vs  bca        — the ℤ/3 of the ab:bc:ca cycle
  (iii) TRANSPOSITION     abc    vs  acb        — naming a pair (the ℤ/2)

THE DISCRIMINATOR.  Run all three on an ℍ SUBALGEBRA OF 𝕆 THAT SPANS THE
DOUBLING SEAM — `span{e₀, e₁, e₄, e₅}` (the Fano line 145; verified closed and
associative through `cd_basis_product` / `associator`).  There the associator is
identically zero, so axis (i) CANNOT contribute — yet `q₀ = x[:4]` and
`q₁ = x[4:]` are both nonzero, so `octonion_frame_read` is NON-degenerate.

  base leaks on (ii)/(iii) at ℍ⊂𝕆 too  ⇒ the leak is NOT the associativity
                                          defect; it is plain non-commutativity
                                          (k=2), and the 0/19 is an artifact of
                                          asking a NON-SYMMETRIC function for a
                                          symmetric answer.
  base holds on (ii)/(iii) at ℍ⊂𝕆      ⇒ the leak IS carried by the k=3 defect.

Exact ℚ, numpy-free, no abs(), no fractions/math/decimal.
Run: cd docs/srmech/python && PYTHONPATH=$PWD python3 ../notes/phi_base_leak_axes_rc420.py
"""
from __future__ import annotations

import json
import sys
from itertools import product

import srmech
from srmech.cascade.atoms import net_chirality, pin_slot_at_zero
from srmech.cascade.cayley_dickson import (
    associator,
    cd_basis,
    cd_basis_product,
    cd_mult,
    cd_norm_sq,
    cd_three_form,
    octonion_frame_read,
)
from srmech.introspect.tool_schema import get_tool_schema, warmup_all

OUT = []


def emit(**rec):
    OUT.append(rec)


def _lcg_stream(seed, n):
    x = seed
    out = []
    for _ in range(n):
        x = (1103515245 * x + 12345) % (2 ** 31)
        out.append((x % 15) - 7)
    return out


def _generic_triples():
    """The SAME 19 triples §3.46.11 used (identical LCG + filter)."""
    vals = _lcg_stream(20260803, 8 * 3 * 200)
    octs, idx = [], 0
    while len(octs) < 60:
        v = tuple(vals[idx:idx + 8])
        idx += 8
        if any(v[m] != 0 for m in range(4)) and any(v[m] != 0 for m in range(4, 8)):
            octs.append(v)
    return [(octs[i], octs[i + 1], octs[i + 2]) for i in range(0, 57, 3)]


def _h_subalgebra_triples(line=(1, 4, 5)):
    """Generic elements of the ℍ subalgebra span{e0} ⊕ span(line) of 𝕆.
    Associative (0 associators) but NON-commutative, and both Hopf halves
    nonzero because the line crosses the doubling seam."""
    slots = (0,) + line
    vals = _lcg_stream(20260804, 4 * 3 * 400)
    octs, idx = [], 0
    while len(octs) < 60:
        four = vals[idx:idx + 4]
        idx += 4
        v = [0] * 8
        for s, val in zip(slots, four):
            v[s] = val
        v = tuple(v)
        if any(v[m] != 0 for m in range(4)) and any(v[m] != 0 for m in range(4, 8)):
            octs.append(v)
    return [(octs[i], octs[i + 1], octs[i + 2]) for i in range(0, 57, 3)]


def base_of(x):
    r = octonion_frame_read(x)
    return (tuple(r["base_H"]), r["base_R"])


def _pin(v):
    orientation, _ = pin_slot_at_zero(v)
    return orientation


def axes(triples, label):
    n = len(triples)
    regroup = cyc = transp = 0
    scal_regroup = scal_cyc = scal_transp = 0
    norm_regroup = norm_cyc = norm_transp = 0
    assoc_zero = 0
    baseR_signflip_regroup = baseR_signflip_cyc = 0
    for a, b, c in triples:
        if all(v == 0 for v in associator(a, b, c)):
            assoc_zero += 1
        L = cd_mult(cd_mult(a, b), c)          # abc, left bracketing
        R = cd_mult(a, cd_mult(b, c))          # abc, right bracketing
        Cy = cd_mult(cd_mult(b, c), a)         # bca, left bracketing
        Tr = cd_mult(cd_mult(a, c), b)         # acb, left bracketing
        bL, bR, bC, bT = base_of(L), base_of(R), base_of(Cy), base_of(Tr)
        regroup += (bL == bR)
        cyc += (bL == bC)
        transp += (bL == bT)
        scal_regroup += (L[0] == R[0])
        scal_cyc += (L[0] == Cy[0])
        scal_transp += (L[0] == Tr[0])
        norm_regroup += (cd_norm_sq(L) == cd_norm_sq(R))
        norm_cyc += (cd_norm_sq(L) == cd_norm_sq(Cy))
        norm_transp += (cd_norm_sq(L) == cd_norm_sq(Tr))
        if net_chirality([_pin(bL[1]), _pin(bR[1])]) == -1:
            baseR_signflip_regroup += 1
        if net_chirality([_pin(bL[1]), _pin(bC[1])]) == -1:
            baseR_signflip_cyc += 1
    return dict(label=label, n=n, associator_zero_on=assoc_zero,
                base_invariant_regrouping=regroup,
                base_invariant_cyclic=cyc,
                base_invariant_transposition=transp,
                scalar_invariant_regrouping=scal_regroup,
                scalar_invariant_cyclic=scal_cyc,
                scalar_invariant_transposition=scal_transp,
                norm_invariant_regrouping=norm_regroup,
                norm_invariant_cyclic=norm_cyc,
                norm_invariant_transposition=norm_transp,
                base_R_signflips_regrouping=baseR_signflip_regroup,
                base_R_signflips_cyclic=baseR_signflip_cyc)


def main():
    warmup_all()
    emit(kind="env", version=srmech.__version__, srmech_file=srmech.__file__,
         registry=len(get_tool_schema().tools),
         has_native=bool(getattr(srmech, "HAS_NATIVE", False)),
         numpy_present="numpy" in sys.modules,
         task="#T1114", test="B-supplement — which AXIS does the base leak on?")

    # the ℍ subalgebras of 𝕆 that span the seam — verified through shipped ops
    verified = []
    for line in ((1, 2, 3), (1, 4, 5), (2, 4, 6), (2, 5, 7), (3, 4, 7),
                 (1, 6, 7), (3, 5, 6)):
        S = (0,) + line
        closed = all(cd_basis_product(8, i, j)[0] in S for i in S for j in S)
        assoc = all(all(v == 0 for v in associator(cd_basis(8, i), cd_basis(8, j),
                                                   cd_basis(8, k)))
                    for i, j, k in product(S, repeat=3))
        verified.append({"fano_line": list(line), "closed_under_product": closed,
                         "associative": assoc,
                         "spans_doubling_seam": any(x >= 4 for x in line)})
    emit(kind="h_subalgebra_verification", rows=verified,
         note="7 Fano lines -> 7 ℍ subalgebras of 𝕆; 6 of them span the ℓ=e4 "
              "doubling seam, so octonion_frame_read is non-degenerate on them")

    emit(kind="axis_split", **axes(_generic_triples(),
                                   "generic 𝕆 (the §3.46.11 19 triples)"))
    for line in ((1, 4, 5), (2, 4, 6), (3, 4, 7)):
        emit(kind="axis_split",
             **axes(_h_subalgebra_triples(line),
                    f"ℍ subalgebra span{{e0}}+{line} ⊂ 𝕆 — ASSOCIATIVE, "
                    f"non-commutative, seam-spanning (CONTROL)"))

    rows = [r for r in OUT if r["kind"] == "axis_split"]
    h_rows = [r for r in rows if r["label"].startswith("ℍ")]
    leak_without_associator = any(
        r["base_invariant_cyclic"] < r["n"] or r["base_invariant_transposition"] < r["n"]
        for r in h_rows)
    holds_regroup = all(r["base_invariant_regrouping"] == r["n"] for r in h_rows)
    emit(kind="verdict", test="B-supplement",
         associator_free_control_holds_on_regrouping=holds_regroup,
         base_leaks_on_permutation_WITHOUT_associator=leak_without_associator,
         reading=("the 0/19 base leak is NOT the pair/cycle twist: on an "
                  "associator-FREE ℍ subalgebra the base still moves under "
                  "cyclic rotation and transposition, so that motion is plain "
                  "NON-COMMUTATIVITY (k=2), not the k=3 defect")
         if (leak_without_associator and holds_regroup) else
         "see rows — the clean separation did not appear")

    path = __file__.replace(".py", ".ndjson")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for rec in OUT:
            fh.write(json.dumps(rec, sort_keys=True, default=str) + "\n")
    print(f"wrote {len(OUT)} records -> {path}")
    for rec in OUT:
        if rec["kind"] in ("axis_split", "verdict"):
            print(json.dumps(rec, sort_keys=True, default=str)[:1200])


if __name__ == "__main__":
    main()
