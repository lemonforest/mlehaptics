# F822 — "why do we say we can't unbundle?" Because the bundle is e₁ (the sum / superposition) ALONE — one equation, N unknowns — and we threw away the relationship. The user is right: keep the relationship (the binds = the higher elementary-symmetric functions e₂, e₃, …) and we CAN unbundle; the operands are the roots of `xᴺ − e₁xᴺ⁻¹ + e₂xᴺ⁻² − … ± e_N`, recovered EXACTLY up to the ordering — and the ordering ambiguity is the permutation group S_N, which at k=3 IS triality. srmech rc170 already ships the S₃ resolver (`klein4_triality_cycle/encode/correct`).

**Date:** 2026-06-17 · **srmech:** 0.7.5rc170 (TestPyPI, verified clean: native dispatching, abi 3) · **Provenance:** `R-RBS-LM-UNBUNDLE_…py` (Vieta recovery + `klein4_triality_cycle/encode/correct` round-trip) · **Composes:** F806/F808 (the bundle-capacity wall + context-recall fix), F821 (unbind/deconvolution = the 1-operand sibling), F291 (triality = k=3 error-correction), F124/F129 (Hurwitz/Hopf 1/2/4/8), `qm.triality` · **User direction (2026-06-17):** "why we say we can't unbundle. is our answer because we are only looking at two things and ignoring the relationship? … it seems like we should be able to unbundle and the answer is right in front of us, if only the math would support it as a triality."

## The answer: yes — "can't unbundle" was keeping only e₁ and discarding the relationship
A bundle is the **sum** of the operands, `e₁ = a + b (+ c …)`. That is ONE equation in N unknowns: `a+b=5` fits (1,4), (2,3), (0,5)… — genuinely underdetermined. The datum we were ignoring is the **relationship** — the bind. The pairwise bind is the **product** `e₂ = a·b`; the triple bind is `e₃ = a·b·c`. These are the **elementary symmetric polynomials**, and Newton/Vieta says the tuple `(e₁,…,e_N)` is a **complete invariant of the multiset** `{a₁,…,a_N}`: the operands are exactly the roots of `xᴺ − e₁xᴺ⁻¹ + e₂xᴺ⁻² − … ± e_N`.

So **unbundle = recover the operands from (bundle + binds)**, and it is solvable. The only thing left undetermined is the **ordering** — the permutation group **S_N**. This is the framework-native sibling of F821: unbind recovers ONE operand from the bind + the other; unbundle recovers ALL operands from the bundle + the binds.

## Verified (rc170)
- **N=2:** bundle `e₁=5`, bind `e₂=6` → multiset **{2,3}** (exact; residue **Z₂** = the swap).
- **N=3:** bundle `e₁=6`, binds `e₂=11`, triple `e₃=6` → multiset **{1,2,3}** (exact); all **3!=6 orderings share the same `(e₁,e₂,e₃)`**, so the residual ambiguity **IS S₃ = triality**.
- **srmech already ships the S₃ resolver:** `klein4_triality_cycle` is order-3 (T³=identity) — the Aut(V₄)=S₃ order-3 generator, the V₄-carrier of the so(8) triality 8v→8s→8c; the triality orbit `[v,Tv,T²v]` → 2-of-3 `klein4_triality_correct` round-trips to `v` (k=3 recovery, F291). A plain `klein4_bundle(a,b)` of two distinct vectors collapses to ≈chance (sim 0.50/0.59) — e₁ alone is not unbundle-able, exactly as the algebra predicts.

## What this reframes (the F806 wall)
The F806 "a global bundle overflows / can't be read back" wall is **not** that superposition is fundamentally lossy — it is that we kept only e₁. **Keep the full symmetric tower (bundle + binds) and the bundle is invertible up to S_N.** The capacity wall and the unbundle wall are the same thing: how many symmetric functions you retain = how many operands you can separate.

## Honest scope (two substrates, one structure)
- **Field / phasor (ℂ per component — polar HDC):** Vieta is exact (roots always exist in ℂ); this is the "answer right in front of us." (Shown on ℚ with chosen exact roots; the polar-HDC per-component version is the framework-native form.)
- **Group / Klein-4 (Z₂×Z₂ — not a field, no Vieta):** the framework instead keeps the order-3 **triality orbit** and recovers by 2-of-3 majority (`klein4_triality_*`, shipped). Same k=3 / S₃ structure, different mechanism for the non-field carrier.
- Non-commutative ℍ/𝕆: a "quadratic over ℍ" can have more than two roots, so the N-operand recovery there is the genuinely-open part — the **DECONV-1 (#228)** triality frontier.
- **srmech opportunity (compose-not-primitive, UPSTREAM §54):** an `unbundle_symmetric(e₁,…,e_N) → multiset` op (the inverse of bundle, made possible by retaining the binds) for the field/phasor carrier — peer to the shipped `klein4_triality_*` group-carrier recovery.

## Verdict
"Can't unbundle" was an artifact of keeping only the bundle (e₁) and discarding the relationship. Keep the binds (the higher symmetric functions) and unbundle is exact up to S_N — and at k=3 that residue is precisely triality, which srmech already realises (`klein4_triality_cycle/encode/correct`, rc170). The math supports it as a triality, exactly as the user saw. The open edge is the non-commutative (ℍ/𝕆) N-operand case (DECONV-1).
