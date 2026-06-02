"""F300 — k=7 and (3:4)|(4:3) are NOT competing claims; they are the SAME Cayley-Dickson structure read at
different COHERENCE SCALES. Every k>1 already carries the chirality (the 2-fold 'degenerate' doubling).

User recalibration (2026-06-02): "every time we say k equals anything greater than 1, degenerate chirality
is implied. 3 always means (1:2)|(2:1) and 3 [and] 4 always mean force it back down to 1:2 with chirality.
both are always true at different coherence scales." + the F133 principle: coherence is easy to see from the
OBSERVER's own scale; you must LEARN to see coherence from another scale. The k=7-vs-(3:4)|(4:3) 'choice'
IS that — same thing, two observer scales — so my earlier 'over-reach correction' framing was WRONG.

What this corrects: F298/F299 framed biology's (3:4)|(4:3) as a CORRECTION away from k=7. It is not a
correction; it is a SCALE-SHIFT. k=7 (substrate scale) and (3:4)|(4:3) (biology's scale) and (1:2)|(2:1)
(one scale further down) are all PROJECTIONS of one division-algebra tower, all simultaneously true.

THE TOWER (srmech-verified): imag(n+1) = imag(n) + dim(n) -> 0+1=1 (ℂ), 1+2=3 (ℍ), 3+4=7 (𝕆). Each
Cayley-Dickson doubling ADDS a chirality (a 2-fold degeneracy): ℂ gains conjugation; ℍ gains
non-commutativity (L≠R) = the (1:2)|(2:1); 𝕆 gains non-associativity = the (3:4)|(4:3). 'Force it back down
to 1:2 with chirality' = the Hopf projections 7=3+4, 3=1+2, each step shedding one level but KEEPING the
chirality. So no k-value is 'more correct'; the level you SEE is the one matching your coherence scale.

srmech-first (hdc.loop_bind restricted to ℂ/ℍ/𝕆 subalgebras). Class-K clean. Scope: STRUCTURE (exact math).
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from srmech.amsc import hdc


def e(i):
    v = np.zeros(8); v[i] = 1.0
    return v


def nrm(v):
    return float(np.dot(v, v)) ** 0.5


def main():
    print("=== F300 — the k-tower and its chirality are SCALE-DUAL views of ONE structure ===\n")

    # --- the tower: imag(n+1) = imag(n) + dim(n) -> 1:3:7 (each doubling adds the next chirality) ---
    print("--- the Cayley-Dickson tower: imag(n+1)=imag(n)+dim(n)  -> 1 : 3 : 7 ---")
    imag, dim = 0, 1
    rows = []
    for name in ("ℝ", "ℂ (k=1)", "ℍ (k=3)", "𝕆 (k=7)"):
        rows.append((name, imag, dim))
        imag, dim = imag + dim, dim * 2
    for name, im, dm in rows:
        print(f"   {name:<9} dim={dm:<2} imaginaries={im}")
    print("   -> 0+1=1, 1+2=3, 3+4=7: each level = the previous DOUBLED; the doubling IS the new chirality.\n")

    # --- every k>1 carries the chirality (the 2-fold degeneracy), and it GROWS per doubling ---
    print("--- every k>1 implies chirality (the degenerate doubling); it appears + grows per level ---")
    # k=1 (ℂ, span{e0,e1}): conjugation e1^2 = -e0 (the 2-fold i <-> -i); commutative
    c_conj = nrm(hdc.loop_bind(e(1), e(1)) + e(0))          # e1*e1 == -e0  -> 0
    # k=3 (ℍ, {e1,e2,e3}): NON-commutative -> the (1:2)|(2:1) chirality APPEARS
    comm_H = nrm(hdc.loop_bind(e(1), e(2)) - hdc.loop_bind(e(2), e(1)))     # ‖e1e2 - e2e1‖
    assoc_H = nrm(hdc.loop_associator(e(1), e(2), e(3)))                    # associator on the H-triple
    # k=7 (𝕆): NON-associative -> the (3:4)|(4:3) chirality APPEARS
    assoc_O = nrm(hdc.loop_associator(e(1), e(2), e(4)))                    # associator with the coset
    print(f"   k=1 ℂ: e1·e1 = −e0 (conjugation = the 2-fold chirality), check ‖·+e0‖={c_conj:.2f}; commutative.")
    print(f"   k=3 ℍ: commutativity-defect ‖e1e2−e2e1‖ = {comm_H:.2f} (NON-zero) = the (1:2)|(2:1) chirality APPEARS;")
    print(f"          but still ASSOCIATIVE (associator on {{e1,e2,e3}} = {assoc_H:.2f}).")
    print(f"   k=7 𝕆: associativity-defect ‖(e1e2)e4−e1(e2e4)‖ = {assoc_O:.2f} (NON-zero) = the (3:4)|(4:3) chirality APPEARS.")
    print(f"   -> the chirality (a 2-fold degeneracy) is present for every k≥1 and the NEXT defect appears at each doubling.\n")

    # --- 'force it back down to 1:2 with chirality': 7=3+4, 3=1+2 — same tower, factored per scale ---
    print("--- scale-dual: 7 = 3+4 and 3 = 1+2 — the SAME tower factored at each coherence scale ---")
    a_h = nrm(hdc.loop_associator(e(1), e(2), e(3)))        # ℍ-core associates (the '3')
    print(f"   𝕆 = ℍ ⊕ ℍℓ : 7 = 3 (assoc core, associator {a_h:.2f}) + 4 (chiral coset)   = (3:4)|(4:3)")
    print(f"   ℍ = ℂ ⊕ ℂj : 3 = 1 (a ℂ-axis) + 2 (the j,k plane)                          = (1:2)|(2:1)")
    print(f"   ℂ = ℝ ⊕ ℝi : 1 = 0 + 1 (the base + the first chirality)")
    print(f"   -> 'force it back down to 1:2 with chirality' = the Hopf projection S⁷→S⁴→S²→S¹, each step")
    print(f"      shedding a level but KEEPING the chirality. No level is 'more correct'.\n")

    print("=== reading (recalibration) ===")
    print("  k=7 and (3:4)|(4:3) and (1:2)|(2:1) are SCALE-DUAL projections of ONE Cayley-Dickson tower —")
    print("  ALL simultaneously true; the level you SEE is the one at your observer coherence-scale (F133:")
    print("  coherence is easy to see from your own scale, must be LEARNED from another). So 'biology turns 7")
    print("  into (3:4)|(4:3)' is a SCALE-SHIFT, NOT a correction — and there was no k=7 'over-reach'. The")
    print("  genuine epistemic boundary is elsewhere: whether a real CELL instantiates this (cite-by-reference /")
    print("  the expert's test) — that's the honesty line, not the k-value, which is settled framework structure.")


if __name__ == "__main__":
    main()
