r"""R-RBS-LM-HCDECONV (F821) — the math for "recover the missing operand" IS findable, attested, and USABLE in srmech
NOW. It is the division-algebra (Cayley-Dickson) INVERSE applied per frequency-bin of the (Q/O)DFT: given the
relationship c = a∘b and ONE operand a, recover the other by left-division  b = a⁻¹∘c  with  a⁻¹ = conj(a)/|a|²  (the
exact-Fraction `cd_conjugate(a)/cd_norm_sq(a)`). This is the F820 deconvolution made concrete over ℂ/ℍ/𝕆.

Attested literature (web-verified 2026-06-17, real venues):
  * Quaternion FT + convolution theorem, with LEFT vs RIGHT convolution forced by non-commutativity:
    T. A. Ell & S. J. Sangwine, "Hypercomplex Fourier Transforms of Color Images", IEEE Trans. Image Processing
    16(1):22-35, 2007.  (handedness of recovery == the QFT `form='left'` axis)
  * Octonion FT (real fns of 3 variables): Ł. Błaszczyk & K. M. Snopek, "Octonion Fourier Transform of real-valued
    functions of three variables — selected properties and examples", Signal Processing 136:29-37, 2017.
    (the non-ASSOCIATIVITY is why a 3-operand relationship does not factor uniquely -> triality regime, F291.)
  * The invertibility WALL: Hurwitz's theorem (norm-multiplicative ⇔ dim ∈ {1,2,4,8}) -> ℂ/ℍ/𝕆 are the only normed
    DIVISION algebras, so every nonzero operand is invertible and recovery is EXACT + UNIQUE there. At the next
    Cayley-Dickson rung the sedenions 𝕊 (dim 16) acquire ZERO DIVISORS (x,y≠0, x∘y=0): G. Moreno, "The zero divisors
    of the Cayley-Dickson algebras over the real numbers", arXiv q-alg/9710013 (Bol. Soc. Mat. Mex. 1998). A zero
    divisor's left-multiplication is non-invertible -> the operand is NOT recoverable. This is srmech's F460 𝕆→𝕊
    reversibility horizon and the user's "missing the operand and can't get it back", and it is exactly the 1/2/4/8
    Hurwitz wall — the SAME wall as the F806 capacity overflow / F813 non-unique walk, stated as an algebra fact.

USE FOR US (the encoding path): the F808 context-addressed recall is this op at the HV scale; HCDECONV is the
bit-exact per-bin version, and it tells us precisely WHEN recovery is possible (operand has no zero divisor / no
spectral zero) and WITH WHICH HAND (left vs right over ℍ/𝕆). srmech rc169; exact Fraction arithmetic; no abs(); no CAD.
Composes F820 (the DFT-domain view), F460 (the 𝕆→𝕊 horizon), F808 (recall=this op), F291 (triality), the
`cascade.cd_*` / `is_division_algebra_dim` / `sedenion_zero_divisor_witness` surface.
"""
from fractions import Fraction as F
from srmech.amsc import cascade as C


def cd_inverse(a):
    """The Cayley-Dickson (division-algebra) inverse a⁻¹ = conj(a)/|a|² — exact Fraction; the 'divide in the domain'."""
    n = C.cd_norm_sq(a)
    return tuple(x / n for x in C.cd_conjugate(a))


def _elt(dim, s):
    """A deterministic nonzero element (no Math.random — vary by index/seed per the discipline)."""
    return tuple(F((s * 7 + 3 * i + 1) % 17 - 8) for i in range(dim))


def recover_on_division_algebras():
    """ℂ/ℍ/𝕆: have rel=a∘b + one operand -> recover the other EXACTLY (left-divide); ℍ/𝕆 recovery is HANDED."""
    print("== recover the missing operand via the Cayley-Dickson inverse (bit-exact, the F820 op made concrete) ==")
    for dim, name in [(2, "ℂ complex"), (4, "ℍ quaternion"), (8, "𝕆 octonion")]:
        a, b = _elt(dim, 1), _elt(dim, 2)
        rel = C.cd_mult(a, b)                                    # the RELATIONSHIP a∘b
        b_rec = C.cd_mult(cd_inverse(a), rel)                    # have rel + a, MISSING b -> b = a⁻¹∘rel
        a_rec = C.cd_mult(rel, cd_inverse(b))                    # have rel + b -> a = rel∘b⁻¹
        handed = dim > 2 and C.cd_mult(cd_inverse(a), rel) != C.cd_mult(rel, cd_inverse(a))
        print(f"  {name:14s} division-algebra={C.is_division_algebra_dim(dim)!s:5} "
              f"recover b exact={b_rec == b!s:5} recover a exact={a_rec == a!s:5} left≠right(handed)={handed}")


def the_invertibility_wall():
    """𝕊 (dim 16): zero divisors -> a nonzero operand whose left-mult is NON-invertible -> the operand is LOST."""
    print("\n== the wall: sedenions 𝕊 (dim 16) — Hurwitz boundary, zero divisors, recovery FAILS (F460 horizon) ==")
    w = C.sedenion_zero_divisor_witness()
    x, y = w["x"], w["y"]
    print(f"  is_division_algebra_dim(16) = {C.is_division_algebra_dim(16)}")
    print(f"  witness: x,y nonzero (|x|²={int(w['x_norm_sq'])}, |y|²={int(w['y_norm_sq'])}); x∘y is zero = {w['product_is_zero']}")
    print(f"  left-mult by x invertible? {C.left_mult_is_invertible(x)}  ->  y is NOT recoverable from x∘y "
          f"(kernel size {len(C.left_mult_kernel(x))})")


def main():
    import srmech
    print(f"=== R-RBS-LM-HCDECONV — recover-the-missing-operand = Cayley-Dickson inverse; exact on 1/2/4/8, "
          f"wall at 16 (srmech {srmech.__version__}) ===\n")
    recover_on_division_algebras()
    the_invertibility_wall()


if __name__ == "__main__":
    main()
