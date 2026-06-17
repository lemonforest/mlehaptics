# F821 — the math for "recover the missing operand" IS findable, attested, and USABLE in srmech NOW: it is the division-algebra (Cayley–Dickson) INVERSE, the bit-exact form of the F820 spectral deconvolution. Verified on the real surface: over ℂ/ℍ/𝕆 you recover the missing operand EXACTLY (`b = a⁻¹∘rel`, `a⁻¹ = conj(a)/|a|²`), the recovery is HANDED on ℍ/𝕆 (left ≠ right), and it hits a hard WALL at the sedenions 𝕊 (dim 16) where zero divisors make the operand unrecoverable — which is exactly srmech's F460 𝕆→𝕊 horizon and the 1/2/4/8 Hurwitz boundary.

**Date:** 2026-06-17 · **srmech:** 0.7.5rc169 · **Provenance:** `R-RBS-LM-HCDECONV_…py` (introspect-then-use: `cascade.cd_mult/cd_conjugate/cd_norm_sq`, `is_division_algebra_dim`, `left_mult_is_invertible/left_mult_kernel`, `sedenion_zero_divisor_witness`) · **Composes:** F820 (the DFT-domain deconvolution view this makes exact), F460 (the 𝕆→𝕊 reversibility horizon = this wall), F808 (recall = this op at HV scale), F291 (triality), F124/F129 (Hopf / Hurwitz 1/2/4/8) · **User direction (2026-06-17):** "let's see if that is some math we can find and use for srmech and us now."

## The math (web-verified, real venues — citation discipline)
- **Quaternion FT + convolution theorem, LEFT vs RIGHT (from non-commutativity):** T. A. Ell & S. J. Sangwine, "Hypercomplex Fourier Transforms of Color Images," *IEEE Trans. Image Processing* 16(1):22–35, 2007. The non-commutativity of ℍ forces a *left* and a *right* convolution — i.e. recovering the missing operand is **handed**. (srmech's `quaternion_dft(form='left')`.)
- **Octonion FT:** Ł. Błaszczyk & K. M. Snopek, "Octonion Fourier Transform of real-valued functions of three variables — selected properties and examples," *Signal Processing* 136:29–37, 2017 (ADS 2017SigPr.136...29B); convolution theorems extended in *Circuits Syst. Signal Process.* (2025). The non-ASSOCIATIVITY of 𝕆 is why a three-operand relationship does not factor uniquely → the triality regime.
- **The invertibility WALL:** Hurwitz's theorem — `‖xy‖=‖x‖‖y‖` holds iff dim ∈ {1,2,4,8}, so ℂ/ℍ/𝕆 are the only normed *division* algebras and every nonzero operand is invertible (recovery exact + unique). At the next Cayley–Dickson rung the sedenions 𝕊 (dim 16) acquire ZERO DIVISORS: G. Moreno, "The zero divisors of the Cayley–Dickson algebras over the real numbers," arXiv:q-alg/9710013 (1998). "Unlike the octonions, [sedenions] are neither alternative nor division; zero divisors appear abundantly."

## The operation, made concrete + verified (bit-exact, exact-Fraction)
`b = a⁻¹ ∘ rel` where `rel = a ∘ b` and `a⁻¹ = cd_conjugate(a) / cd_norm_sq(a)`:

| algebra | division algebra? | recover b exact | recover a exact | left ≠ right (handed)? |
|---|---|---|---|---|
| ℂ (2) | yes | **True** | **True** | no (commutative) |
| ℍ (4) | yes | **True** | **True** | **yes** |
| 𝕆 (8) | yes | **True** | **True** | **yes** |
| 𝕊 (16) | **no** | — | — | — (recovery FAILS) |

The wall, demonstrated: `is_division_algebra_dim(16) = False`; the `sedenion_zero_divisor_witness` gives `x = e₁+e₁₀`, `y = e₄−e₁₅` (both nonzero, |x|²=|y|²=2) with **x∘y = 0**; `left_mult_is_invertible(x) = False`, left-mult kernel size 4 → **y is not recoverable from x∘y** (the operand is genuinely lost).

## What it gives US (the encoding path) now
- It is the **bit-exact per-frequency-bin version of the F808 recall**: "have the bundle (relationship) + one operand → recover the other" = `cd_inverse`-multiply in the (Q/O)DFT domain. The F808 HV walk is the approximate (similarity) form; HCDECONV is the exact algebra form.
- It tells us **WHEN recovery is possible** (the operand has no zero divisor ⇔ no spectral zero ⇔ dim ≤ 8) and **WITH WHICH HAND** (left vs right over ℍ/𝕆 — the framework's chirality as an operator, F130). This is the SAME invertibility wall as the F806 capacity overflow / F813 non-unique-walk tail, now stated as a clean algebra fact on the 1/2/4/8 ladder.
- Immediately usable: `cd_mult` + `cd_conjugate`/`cd_norm_sq` are shipped (0.7.3); the only ergonomic gap is no packaged `cd_inverse`/`cd_left_divide` helper (we compose it in 3 lines) — a candidate srmech addition (compose-not-primitive; no ABI bump).

## Honest scope + the next question (handed to the expert)
- Verified for the TWO-operand case (exact on ℂ/ℍ/𝕆 by the inverse property of the Moufang loop). The genuinely-open part is the **THREE-operand** non-associative case: recovering one missing operand from `(a∘b)∘c` over 𝕆 depends on the bracketing, and that is where **triality** (k=3, F291; `qm.triality.triality_companions`) lives — DECONV-1 (#228) carries it forward.
- Framework-reading only; the QDFT/ODFT TOML-cascade packaging is queued at BX-5.

## Verdict
Yes — the math is found, attested (Ell–Sangwine 2007; Błaszczyk–Snopek 2017; Hurwitz; Moreno 1998), and usable in srmech today: recover-the-missing-operand = the Cayley–Dickson inverse, exact and handed on ℂ/ℍ/𝕆, failing exactly at the sedenion zero-divisor wall (= F460). It is the bit-exact spine of the F808 recall and pins the invertibility condition to the 1/2/4/8 Hurwitz ladder. The open frontier is octonionic three-operand recovery = triality (DECONV-1).
