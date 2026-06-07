r"""R-RBS-SNN-FRAMES — resolving 14 vs 15, and WHY each ladder rung has exactly ONE fiber/DoF.

The slip: {1, 1+1, 3+1, 7+1} = {1,2,4,8} sums to 15 — that PREPENDS a leading ℝ(1), a FOURTH algebra. the_one
is THREE algebras ℂ⊕ℍ⊕𝕆 = (1+1)+(3+1)+(7+1) = 2+4+8 = 14 (verified: block dims [2,4,8], no leading ℝ). The three
+1's are the three block-REALS = the grammar slots (B,H,N) = the OUTER fiber (F496). There is no separate ℝ block.

The user's two reconciliations, both correct:
  (a) "the 7+1 falls back to the very first 1" — YES: the +1 that completes 𝕆 (7→8) IS the real line ℝ; every
      division algebra's real is the SAME scalar. In the nested view there is ONE real, reused — so you don't add
      a fresh ℝ rung. 𝕆 is also the LAST division algebra (is_div(16)=False, F460) — the ladder closes at 8.
  (b) "each addressable ℂ/ℍ/𝕆 only ever sees 1 moving frame, so each ladder has 1 fiber/DoF" — YES, and this is
      the WHY: a division algebra has exactly ONE real axis (a theorem) = its single observer / moving frame (the
      etak frame, F482). One frame per addressable level ⇒ exactly one fiber/DoF (the +1) per rung. The three +1's
      (B/H/N) = the three moving frames, one per addressed algebra. ℝ alone = a bare frame with NO content (0
      imaginary) — not a separate addressable level — which is exactly why it's 14 (three content-frames), not 15.

And the 15 is not wrong, it is the NEXT rung: 1+2+4+8 = 15 = the imaginary dim of the sedenion 𝕊 (16−1) — BX-2's
"the 15". So the_one (14) sits one real below the sedenion-imaginary (15). srmech 0.7.4.
"""
import srmech
from srmech.amsc.cascade import cayley_dickson as cd
from srmech.amsc.cascade import the_one


def main():
    print(f"=== R-RBS-SNN-FRAMES — 14 vs 15; one moving frame per addressable level = one fiber/DoF per rung  (srmech {srmech.__version__}) ===\n")
    S = the_one(sigma=1, theta_num=1, theta_den=7, terms=8)
    blockdims = [1 + len(b.imag) for b in S.blocks]                      # 1 real + imag per block
    algs = [b.algebra for b in S.blocks]

    print("THE RESOLUTION — the_one is THREE algebras, no leading ℝ:")
    print(f"  blocks {tuple(algs)}  dims {blockdims}  = (1+1)+(3+1)+(7+1) = {sum(blockdims)}  (= the_one dim {S.dim})")
    print(f"  the three +1's = the three block-REALS = grammar {S.grammar_slots} = the OUTER fiber (F496); NO 4th ℝ.")
    print(f"  your {{1, 1+1, 3+1, 7+1}} = {{1,2,4,8}} = {1+2+4+8} prepends a bare ℝ → that is the over-count.\n")

    print("(a) 'the 7+1 falls back to the first 1' — YES (the real is shared / the ladder closes at 𝕆):")
    print(f"    the +1 completing 𝕆 (7→8) IS the real ℝ; every algebra's real is the same scalar.")
    print(f"    𝕆 (dim 8) is the LAST division algebra: is_div(8)={cd.is_division_algebra_dim(8)}, is_div(16)={cd.is_division_algebra_dim(16)} → closes at 8.\n")

    print("(b) 'each addressable ℂ/ℍ/𝕆 sees 1 moving frame ⇒ 1 fiber/DoF per rung' — YES, and this is the WHY:")
    print(f"    each division algebra has exactly ONE real axis (theorem) = its single observer / moving frame (etak, F482).")
    print(f"    one frame per addressable level ⇒ exactly one fiber/DoF (the +1) per rung.")
    print(f"    the three +1's (B/H/N) = three moving frames, one per addressed algebra ℂ/ℍ/𝕆.")
    print(f"    ℝ alone = a bare frame with 0 imaginary content → not a separate addressable level → 14, not 15.\n")

    print("THE 15 IS THE NEXT RUNG (not wrong):")
    print(f"    1+2+4+8 = 15 = the imaginary dim of the sedenion 𝕊 (16−1) — BX-2's 'the 15'.")
    print(f"    the_one (14) = one real BELOW the sedenion-imaginary (15); CD_DIMS {cd.CD_DIMS}.\n")

    ok = sum(blockdims) == 14 and tuple(algs) == ("C", "H", "O") and len(S.grammar_slots) == 3
    print("VERDICT:")
    print(f"  • 14 = ℂ⊕ℍ⊕𝕆 = (1+1)+(3+1)+(7+1); the three +1's = the block-reals = B/H/N = the OUTER fiber. No leading ℝ.")
    print(f"  • each addressable level sees ONE moving frame (its single real axis) ⇒ ONE fiber/DoF per rung — that is")
    print(f"    WHY F496's outer fiber is exactly +1 per block. The 15 is the sedenion-imaginary (the next rung). checks: {ok}")


if __name__ == "__main__":
    main()
