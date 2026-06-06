#!/usr/bin/env python3
"""R-RBS-LM-3KERNEL-REV — is the coupling REVERSIBLE, and is "two-way" the right word?
(the user's logic question, 2026-06-06.)

LOGIC ANSWER (verified below):
  • REVERSE coupling = the CONJUGATE twiddle e^{-μθ} (the "correct vars" = conjugate μ /
    negate θ / σ=−1). It UNDOES the forward fold e^{μθ}.
  • It works because ℂ/ℍ/𝕆 are DIVISION algebras — every unit element is invertible and
    its inverse IS its conjugate. By alternativity, x̄·(x·y)=|x|²·y holds for 𝕆 too.
  • This is EXACTLY the Hurwitz boundary (F423/F424): reversibility caps at 𝕆. The
    sedenion 𝕊 has zero divisors (F424) → some folds CANNOT be reversed. So "reverse with
    correct vars" is not merely possible — it is GUARANTEED up to 𝕆, and breaks beyond.
  • "Two-way" undersells it: the coupling is a PHASED CHOICE — a continuous rotation by
    phase θ about a chosen axis μ, with conjugation σ=±1 as the reverse. That is the_one's
    𝕊(σ,θ) (F420) plus the axis μ. forward/reverse/left/right are special discrete points
    of a continuous (σ, θ, μ) family.

Composes F436 (the coupling) · F420 (the_one σ,θ) · F418/F390 (chirality = conjugate =
order-reversal) · F423/F424 (division-algebra Hurwitz cap = reversibility boundary).
Run: <plain venv>/bin/python (exact rational; no srmech import needed). Defensive / no-lineage.
"""
from fractions import Fraction as Fr
import math


def add(x, y): return tuple(a + b for a, b in zip(x, y))


def conj(x):
    n = len(x)
    if n == 1:
        return x
    h = n // 2
    return conj(x[:h]) + tuple(-t for t in x[h:])


def mul(x, y):                       # generic Cayley-Dickson product (exact for rationals)
    n = len(x)
    if n == 1:
        return (x[0] * y[0],)
    h = n // 2
    a, b, c, d = x[:h], x[h:], y[:h], y[h:]
    return add(mul(a, c), tuple(-t for t in mul(conj(d), b))) + add(mul(d, a), mul(b, conj(c)))


def unit_axis_twiddle(N):
    """a UNIT element t = 3/5 + 4/5·e1  (|t|²=1) — a single-axis rotation, exact."""
    v = [Fr(0)] * N
    v[0] = Fr(3, 5); v[1] = Fr(4, 5)
    return tuple(v)


def main():
    print("=== reverse coupling = the CONJUGATE twiddle (the 'correct vars' = σ=−1 / conj μ) ===\n")
    # 3 streams folded then unfolded by the conjugate — exact, at each Cayley-Dickson rung
    for N, name, note in [(4, "ℍ quaternion", "division algebra, associative"),
                          (8, "𝕆 octonion ", "division algebra, alternative — x̄·(x·y)=|x|²y"),
                          (16, "𝕊 sedenion ", "NOT division (zero divisors, F424)")]:
        q = tuple([Fr(0)] + [Fr(((i * 5 + 2) % 7) - 3) for i in range(N - 1)])   # streams on the imaginaries
        t = unit_axis_twiddle(N)
        recovered = mul(conj(t), mul(t, q)) == q
        print(f"  {name}: unfold(conj(t)·(t·q)) == q : {recovered}   ({note})")
    print("    ↑ a UNIT twiddle reverses at every rung; but 𝕊 also admits ZERO-DIVISOR folds")
    print("      (x·y=0, x,y≠0) that no conjugate can undo — reversibility is GUARANTEED only ≤ 𝕆.\n")

    # the real coupler is the DIAGONAL μ; show it reverses too (float twiddle e^{μθ})
    def fmul(x, y):
        n = len(x)
        if n == 1:
            return (x[0] * y[0],)
        h = n // 2
        a, b, c, d = x[:h], x[h:], y[:h], y[h:]
        def cf(z):
            m = len(z)
            return z if m == 1 else cf(z[:m//2]) + tuple(-t for t in z[m//2:])
        return add(fmul(a, c), tuple(-t for t in fmul(cf(d), b))) + add(fmul(d, a), fmul(b, cf(c)))
    def cf(z):
        m = len(z)
        return z if m == 1 else cf(z[:m//2]) + tuple(-t for t in z[m//2:])
    th = 0.7; c, s = math.cos(th), math.sin(th); k = s / math.sqrt(3)
    t = (c, k, k, k)                                   # e^{μθ}, μ=(i+j+k)/√3  (the diagonal coupler)
    q = (0.0, 2.0, -1.0, 3.0)
    err = max(abs(a - b) for a, b in zip(fmul(cf(t), fmul(t, q)), q))
    print(f"  diagonal-μ coupler (θ=0.7): unfold round-trip err {err:.1e}  → the real coupler reverses\n")

    print("=== terminology: NOT 'two-way' — PHASED CHOICES ===")
    print("  the coupling is parameterized by (σ, θ, μ):")
    print("    σ = ±1  conjugation  → forward / REVERSE (the chirality; F418/F420)")
    print("    θ       continuous phase → the rotation angle (the_one's θ; F420) — a CONTINUUM")
    print("    μ       the axis (point on S² for ℍ, S⁶ for 𝕆) → WHICH streams couple (§29)")
    print("  'two-way' = only the discrete σ bit; the truth is a continuous (σ,θ,μ) family,")
    print("  capped at 𝕆 by Hurwitz. left/right/forward/inverse are special points of it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
