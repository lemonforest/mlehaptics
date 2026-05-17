"""Spike #32 — Q1 direct: try to extract π's CF from Ring C_n
EIGENVALUE structure (not from Archimedes semi-perimeter cascade).

The Ring C_n Laplacian eigenvalues are λ_k = 2 − 2·cos(2πk/n) for
k = 0..n-1. The smallest non-zero eigenvalue is λ_1 = 2 − 2·cos(2π/n).
For large n, λ_1 ≈ (2π/n)² (Taylor expansion of 1−cos).

If we could compute λ_1 as a rational (or rational interval) using
only integer-algebraic primitives (cyclotomic polynomials), we could
back out the convergent ladder of 2π/n, hence of π.

The cyclotomic polynomial Φ_n(x) has roots e^(2πi·k/n) for gcd(k,n)=1.
Its real part gives cos(2π·k/n) algebraically. The minimal polynomial
of 2·cos(2π/n) is the "Chebyshev minimal polynomial" Ψ_n(x), with
integer coefficients computable from cyclotomic polynomials.

For n a prime, Ψ_n has degree (n-1)/2. We can compute Ψ_n numerically
(its root extraction is well-conditioned for any n) WITHOUT using π.
The eigenvalue λ_1 = 2 − ψ where ψ is the largest root of Ψ_n.

This gives an algebraic path to ψ_n → λ_1 → 2π/n approximation
→ π convergents — entirely via integer polynomial root extraction.

ALTERNATIVELY: just use the fact that λ_1 corresponds to chord of
angle 2π/n, and chord² = 2(1−cos(angle)) = 4·sin²(angle/2). So
chord(2π/n) = 2·sin(π/n) and (chord/2)² = sin²(π/n).

In Archimedes notation, this IS the side² s_n² = 2 − 2·cos(2π/n)
of the regular n-gon. So the Ring C_n eigenvalue λ_1(n) IS the
Archimedes side² s_n², by direct identity.

Therefore: the Archimedes cascade we already ran IS the Ring C_n
eigenvalue cascade in disguise. The doubling cascade
n → 2n corresponds to taking the smallest non-zero eigenvalue of
each successive Ring graph, with the Pythagorean recurrence being
the algebraic-cyclic-cascade composition.

Conclusion: the Archimedes hexagon-doubling cascade IS the eigenvalue-
extraction-from-Ring-C_n cascade. The π convergent ladder that drops
out of the Archimedes cascade is the SAME π convergent ladder that
would drop out of a hypothetical "compute the smallest non-zero
eigenvalue of Ring C_6, then C_12, then C_24, ... as a rational
interval" approach.

This is the bridge: Q1 (Ring C_n cascade → π CF) is OPERATIONALLY
EQUIVALENT to the Archimedes cascade we already verified.
"""

from __future__ import annotations
import math


def archimedes_eigenvalue_identity():
    """Verify the identity numerically (with numpy LAPACK — uses π
    internally but we're just CHECKING the identity, not extracting π):

    λ_1(C_n) = 2 − 2·cos(2π/n) = side²(regular n-gon, R=1)
    """
    import numpy as np
    n_values = [6, 12, 24, 48, 96, 192]
    print("Verifying λ_1(C_n) = s_n² (Archimedes side² of regular n-gon)")
    print(f"  n  |  λ_1 (from C_n eigenvalues)  |  s_n² (Archimedes recurrence)")
    s_sq = 1.0  # start hexagon
    for n in n_values:
        # Compute λ_1 of Ring C_n
        A = np.zeros((n, n))
        for i in range(n):
            A[i, (i+1) % n] = 1
            A[i, (i-1) % n] = 1
        L = np.diag(A.sum(axis=1)) - A
        eigs = np.linalg.eigvalsh(L)
        lambda_1 = eigs[1]  # smallest non-zero
        if n == 6:
            print(f"  {n:3d}  |  λ_1 = {lambda_1:.10f}  |  s_n² = {s_sq:.10f}")
            # s_12² = 2 - √(4 - s_6²)
        else:
            s_sq_new = 2 - math.sqrt(4 - s_sq)
            s_sq = s_sq_new
            print(f"  {n:3d}  |  λ_1 = {lambda_1:.10f}  |  s_n² = {s_sq:.10f}")


if __name__ == "__main__":
    archimedes_eigenvalue_identity()
