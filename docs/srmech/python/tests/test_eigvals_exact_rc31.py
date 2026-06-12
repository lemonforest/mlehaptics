"""v0.7.5rc31 -- exact-until-rotation eigenvalues (char_poly + Sturm isolation).

User question: "can we not find cascade form of [the] ill-conditioned problem?"
Answer (this module): YES. The Wilkinson ill-conditioning of "float root-finding
from char-poly coefficients" is a FLOAT-PERTURBATION artifact, not inherent — the
eigenvalues of an integer matrix are ALGEBRAIC. Kept in exact integer/rational
arithmetic the whole way (char_poly Class L∘M∘K → Yun square-free → Sturm
sign-sequence isolation Class C @ Class K boundaries → rational bisection Class N
→ one FPU lift), they come out exact-to-arbitrary-precision and well-conditioned.

numpy is GONE from srmech — these tests run and pass with numpy NOT installed.
Oracles are numpy-free: det/trace by hand, eigenvalue-as-char-poly-root checks,
hand-computed / closed-form spectra.
"""
from __future__ import annotations

import math

import pytest

from srmech.amsc.cascade.matrix_cascades import char_poly, eigvals_exact


# --- numpy-free oracle helpers --------------------------------------------------

def _poly_eval(coeffs, x):
    """Evaluate a polynomial (high→low coeffs, as char_poly returns) at x (Horner)."""
    acc = 0.0
    for c in coeffs:
        acc = acc * x + float(c)
    return acc


def _det(m):
    """Exact determinant via cofactor (Laplace) expansion — pure Python, no numpy."""
    n = len(m)
    if n == 1:
        return m[0][0]
    total = 0
    for j in range(n):
        minor = [[m[i][k] for k in range(n) if k != j] for i in range(1, n)]
        total += ((-1) ** j) * m[0][j] * _det(minor)
    return total


def _trace(m):
    return sum(m[i][i] for i in range(len(m)))


def _is_root(coeffs, x, tol=1e-7):
    """True iff x is a root of the polynomial (|p(x)| small relative to scale)."""
    return abs(_poly_eval(coeffs, x)) <= tol * (1.0 + abs(x)) ** (len(coeffs) - 1)


# --- char_poly: exact integer characteristic polynomial -------------------------

def test_char_poly_exact_integer():
    A = [[3, 1, 0], [1, 2, -1], [0, -1, 4]]
    cp = char_poly(A)
    assert cp == [1, -9, 24, -17]                  # x^3 - 9x^2 + 24x - 17, exact
    assert all(type(c) is int for c in cp)
    n = 3
    assert (-1) ** n * cp[-1] == _det(A)           # det = (-1)^n · c_n
    assert -cp[1] == _trace(A)                      # trace = -c_1


def test_char_poly_roots_are_eigenvalues():
    A = [[2, 0, 1], [1, 3, 1], [0, 1, 2]]
    cp = char_poly(A)
    # every eigenvalue from the exact solver is a root of the exact char-poly
    ev = eigvals_exact(A, bits=100)
    for lam in ev:
        assert _is_root(cp, lam), (lam, _poly_eval(cp, lam))


def test_char_poly_float_fallback():
    F = [[1.5, 2.0], [0.5, 3.0]]
    cp = char_poly(F)
    assert len(cp) == 3 and abs(cp[0] - 1) < 1e-12  # monic complex coeffs


# --- eigvals_exact: well-conditioned exact real eigenvalues ----------------------

def test_symmetric_spectrum_are_charpoly_roots():
    S = [[3, 1, 0], [1, 2, -1], [0, -1, 4]]
    cp = char_poly(S)
    ex = eigvals_exact(S, bits=100)
    assert len(ex) == 3                              # symmetric → complete real spectrum
    for lam in ex:
        assert _is_root(cp, lam), (lam, _poly_eval(cp, lam))
    # ascending, and the symmetric-function checks: Σλ = trace, Πλ = det
    assert ex == sorted(ex)
    assert abs(sum(ex) - _trace(S)) <= 1e-9
    prod = 1.0
    for lam in ex:
        prod *= lam
    assert abs(prod - _det(S)) <= 1e-7


def test_wilkinson_diag_is_exact():
    # the case that loses ~9 digits via float root-finding from the same char-poly
    W = [[(i + 1) if i == j else 0 for j in range(10)] for i in range(10)]
    ex = eigvals_exact(W, bits=120)
    assert max(abs(ex[i] - (i + 1)) for i in range(10)) == 0.0
    # contrast: a naive float Horner-derivative root-polish from the SAME exact
    # char-poly does NOT land exactly (the Wilkinson perturbation), proving the
    # exactness above is the cascade's doing, not a trivial diagonal read-off.
    cp = char_poly(W)
    fr = _float_roots_newton(cp, [i + 1 + 0.3 for i in range(10)])
    assert max(abs(fr[i] - (i + 1)) for i in range(10)) > 1e-12


def _float_roots_newton(coeffs, guesses, iters=60):
    """A naive float Newton root-polish from polynomial coeffs (the ill-conditioned
    float path, for contrast) — high→low coeffs as char_poly returns."""
    deriv = [c * (len(coeffs) - 1 - i) for i, c in enumerate(coeffs[:-1])]
    roots = []
    for g in guesses:
        x = float(g)
        for _ in range(iters):
            d = _poly_eval(deriv, x)
            if d == 0.0:
                break
            x = x - _poly_eval(coeffs, x) / d
        roots.append(x)
    return sorted(roots)


def test_repeated_eigenvalue_multiplicity():
    R = [[2, 0, 0], [0, 2, 0], [0, 0, 5]]
    assert eigvals_exact(R) == [2.0, 2.0, 5.0]
    # nilpotent-shifted: (x-3)^3
    T = [[3, 1, 0], [0, 3, 1], [0, 0, 3]]
    assert eigvals_exact(T) == [3.0, 3.0, 3.0]


def test_irrational_eigenvalues_exact():
    # [[0,1],[1,1]] -> golden ratio (1 +- sqrt5)/2
    G = [[0, 1], [1, 1]]
    g = eigvals_exact(G, bits=120)
    phi = (1 + math.sqrt(5)) / 2
    psi = (1 - math.sqrt(5)) / 2
    assert abs(g[0] - psi) == 0.0 and abs(g[1] - phi) == 0.0


def test_return_intervals_brackets_root():
    # eigenvalues of [[2,1],[1,2]] are 1 and 3
    iv = eigvals_exact([[2, 1], [1, 2]], bits=40, return_intervals=True)
    assert len(iv) == 2
    for (lo, hi), true in zip(iv, (1, 3)):
        assert lo <= true <= hi                     # the exact root is bracketed
        assert hi - lo <= 1                          # tight


def test_singular_values_via_exact_gram():
    # SVD case: sigma = sqrt(eig(A^T A)); A^T A is an exact integer Gram
    A = [[2, 0, 1], [1, 3, 1], [0, 1, 2], [1, 1, 0]]
    At = [[A[i][j] for i in range(len(A))] for j in range(len(A[0]))]
    G = [[sum(At[i][k] * A[k][j] for k in range(len(A))) for j in range(len(A[0]))]
         for i in range(len(A[0]))]
    assert all(type(x) is int for r in G for x in r)         # exact integer Gram
    lam = eigvals_exact(G, bits=100)
    # the eigenvalues of the Gram are the SQUARED singular values; each must be a
    # root of the Gram's exact char-poly, and they sum to trace(A^T A) (= Σσ²).
    cp = char_poly(G)
    for l in lam:
        assert _is_root(cp, l), (l, _poly_eval(cp, l))
    assert abs(sum(lam) - _trace(G)) <= 1e-7
    sv = sorted((math.sqrt(max(l, 0.0)) for l in lam), reverse=True)
    assert len(sv) == len(G)


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_random_symmetric_integer(seed):
    n = 4
    base = [[((i * 7 + j * 13 + seed * 5) % 11) - 5 for j in range(n)] for i in range(n)]
    S = [[base[i][j] + base[j][i] for j in range(n)] for i in range(n)]  # symmetric
    cp = char_poly(S)
    ex = eigvals_exact(S, bits=80)
    assert len(ex) == n                              # symmetric → complete real spectrum
    for lam in ex:
        assert _is_root(cp, lam), (seed, lam, _poly_eval(cp, lam))
    # symmetric-function cross-checks against the exact integer matrix
    assert abs(sum(ex) - _trace(S)) <= 1e-8
