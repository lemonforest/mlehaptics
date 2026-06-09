"""v0.7.5rc31 -- exact-until-rotation eigenvalues (char_poly + Sturm isolation).

User question: "can we not find cascade form of [the] ill-conditioned problem?"
Answer (this module): YES. The Wilkinson ill-conditioning of "float root-finding
from char-poly coefficients" is a FLOAT-PERTURBATION artifact, not inherent — the
eigenvalues of an integer matrix are ALGEBRAIC. Kept in exact integer/rational
arithmetic the whole way (char_poly Class L∘M∘K → Yun square-free → Sturm
sign-sequence isolation Class C @ Class K boundaries → rational bisection Class N
→ one FPU lift), they come out exact-to-arbitrary-precision and well-conditioned.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from srmech.amsc.cascade.matrix_cascades import char_poly, eigvals_exact


# --- char_poly: exact integer characteristic polynomial -------------------------

def test_char_poly_exact_integer():
    A = [[3, 1, 0], [1, 2, -1], [0, -1, 4]]
    cp = char_poly(A)
    assert cp == [1, -9, 24, -17]                  # x^3 - 9x^2 + 24x - 17, exact
    assert all(type(c) is int for c in cp)
    n = 3
    assert (-1) ** n * cp[-1] == round(np.linalg.det(np.array(A, dtype=float)))  # det
    assert -cp[1] == np.trace(np.array(A))                                       # trace


def test_char_poly_roots_are_eigenvalues():
    A = [[2, 0, 1], [1, 3, 1], [0, 1, 2]]
    roots = np.sort(np.roots([float(c) for c in char_poly(A)]).real)
    ev = np.sort(np.linalg.eigvals(np.array(A, dtype=float)).real)
    assert np.allclose(roots, ev, atol=1e-9)


def test_char_poly_float_fallback():
    F = [[1.5, 2.0], [0.5, 3.0]]
    cp = char_poly(F)
    assert len(cp) == 3 and abs(cp[0] - 1) < 1e-12  # monic complex coeffs


def test_char_poly_ndarray_input():
    assert char_poly(np.array([[3, 1, 0], [1, 2, -1], [0, -1, 4]])) == [1, -9, 24, -17]


# --- eigvals_exact: well-conditioned exact real eigenvalues ----------------------

def test_symmetric_matches_numpy():
    S = [[3, 1, 0], [1, 2, -1], [0, -1, 4]]
    ex = eigvals_exact(S, bits=100)
    nv = sorted(np.linalg.eigvalsh(np.array(S, dtype=float)))
    assert max(abs(ex[i] - nv[i]) for i in range(3)) <= 1e-12


def test_wilkinson_diag_is_exact():
    # the case that loses ~9 digits via float root-finding from the same char-poly
    W = np.diag(range(1, 11)).astype(int).tolist()
    ex = eigvals_exact(W, bits=120)
    assert max(abs(ex[i] - (i + 1)) for i in range(10)) == 0.0
    # contrast: float np.roots on the exact char-poly is NOT exact
    fr = np.sort(np.roots([float(c) for c in char_poly(W)]).real)
    assert max(abs(fr[i] - (i + 1)) for i in range(10)) > 1e-12


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
    sv = sorted((math.sqrt(max(l, 0.0)) for l in lam), reverse=True)
    sv_np = sorted(np.linalg.svd(np.array(A, dtype=float), compute_uv=False), reverse=True)
    assert max(abs(sv[i] - sv_np[i]) for i in range(len(sv))) <= 1e-9


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_random_symmetric_integer(seed):
    n = 4
    base = [[((i * 7 + j * 13 + seed * 5) % 11) - 5 for j in range(n)] for i in range(n)]
    S = [[base[i][j] + base[j][i] for j in range(n)] for i in range(n)]  # symmetric
    ex = eigvals_exact(S, bits=80)
    nv = sorted(np.linalg.eigvalsh(np.array(S, dtype=float)))
    assert len(ex) == n
    assert max(abs(ex[i] - nv[i]) for i in range(n)) <= 1e-9
