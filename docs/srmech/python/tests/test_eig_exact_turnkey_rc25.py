"""0.9.0rc25 — `factor_integer_poly` + the turnkey `eig_exact` (rotation-last rc-F).

rc-F closes the exact eigensolver into a one-call API. Two new ops in
``srmech/amsc/cascade/matrix_cascades.py``:

1. **`factor_integer_poly(coeffs)`** — factor an integer polynomial into its
   IRREDUCIBLE factors over ℚ (Zassenhaus: content/primitive split → Yun
   square-free → factor mod a good prime in 𝔽_p[x] via distinct-degree +
   Cantor–Zassenhaus → Hensel-lift to mod p^k ≥ 2·Mignotte+1 → recombine by
   trial division). Returns ``[(factor_coeffs, multiplicity)]``; ``Π factor**mult``
   reconstructs the input up to sign/content. All exact integer/Fraction.
2. **`eig_exact(a)`** — turnkey: ``char_poly`` → ``factor_integer_poly`` (the
   irreducible min-polys with algebraic multiplicities) → isolate each factor's
   roots (real + the rc-E complex) → ``Qalg`` per root → ``eigvec_exact`` → all
   exact eigenpairs, with self-validation (Σ alg-mult == n; Π(x−λ) reconstructs the
   char-poly; A·v ≈ λ·v). Makes exact COMPLEX eigenVECTORS reachable. Defective
   matrices return the geometric eigenvectors + a ``defective`` flag (Jordan
   generalized eigenvectors are out of scope).

numpy is GONE from srmech — this module is numpy-free and runs with numpy NOT
installed. Eigenvectors are defined only UP TO SCALE, so vector comparisons check
proportionality, not literal equality.
"""
from __future__ import annotations

import cmath
import importlib.util
import math

import pytest

from srmech.amsc.cascade.matrix_cascades import (
    eig_exact,
    eigvals_exact,
    factor_integer_poly,
)


def test_numpy_is_absent_so_this_runs_not_skips():
    assert importlib.util.find_spec("numpy") is None, (
        "this rc25 turnkey ratchet must run on the numpy-ABSENT matrix")


# ── helpers ──────────────────────────────────────────────────────────────────────
def _ipoly_mul(a, b):
    out = [0] * (len(a) + len(b) - 1)
    for i, av in enumerate(a):
        for j, bv in enumerate(b):
            out[i + j] += av * bv
    while len(out) > 1 and out[-1] == 0:
        out.pop()
    return out


def _reconstruct(factors):
    """Π factor**mult over the integer factors (low→high)."""
    out = [1]
    for fac, mult in factors:
        for _ in range(mult):
            out = _ipoly_mul(out, list(fac))
    return out


def _content(p):
    g = 0
    for c in p:
        x = c if c >= 0 else -c
        while x:
            g, x = x, g % x
    return g


def _primitive_pos_lead(p):
    p = list(p)
    while len(p) > 1 and p[-1] == 0:
        p.pop()
    cont = _content(p)
    if cont == 0:
        return [0]
    if p[-1] < 0:
        cont = -cont
    return [c // cont for c in p]


def _product_reconstructs(coeffs, factors):
    """The factorisation's product equals the input up to sign/content."""
    recon = _primitive_pos_lead(_reconstruct(factors))
    target = _primitive_pos_lead(coeffs)
    return recon == target


def _abs(x):
    return x if x >= 0 else -x


def _proportional(u, w, tol=1e-7):
    """True iff complex vectors are scalar multiples (cross-ratio ~0 everywhere)."""
    n = len(u)
    for i in range(n):
        for j in range(n):
            if abs(complex(u[i]) * complex(w[j]) - complex(u[j]) * complex(w[i])) > tol:
                return False
    return True


# ── factor_integer_poly ──────────────────────────────────────────────────────────
def test_factor_x4_minus_1():
    """x⁴−1 = (x−1)(x+1)(x²+1)."""
    fac = factor_integer_poly([-1, 0, 0, 0, 1])
    fac_set = {(f, m) for f, m in fac}
    assert fac_set == {((-1, 1), 1), ((1, 1), 1), ((1, 0, 1), 1)}
    assert _product_reconstructs([-1, 0, 0, 0, 1], fac)


def test_factor_x4_plus_1_irreducible():
    """x⁴+1 is irreducible over ℚ (the 8th cyclotomic)."""
    fac = factor_integer_poly([1, 0, 0, 0, 1])
    assert fac == [((1, 0, 0, 0, 1), 1)]
    assert _product_reconstructs([1, 0, 0, 0, 1], fac)


def test_factor_min_poly_sqrt2_plus_sqrt3_irreducible():
    """x⁴−10x²+1 is irreducible (the minimal polynomial of √2+√3)."""
    fac = factor_integer_poly([1, 0, -10, 0, 1])
    assert fac == [((1, 0, -10, 0, 1), 1)]
    assert _product_reconstructs([1, 0, -10, 0, 1], fac)


def test_factor_x2_plus_1_squared_multiplicity():
    """(x²+1)² → the single irreducible (x²+1) at multiplicity 2."""
    fac = factor_integer_poly([1, 0, 2, 0, 1])
    assert fac == [((1, 0, 1), 2)]
    assert _product_reconstructs([1, 0, 2, 0, 1], fac)


def test_factor_x6_minus_1():
    """x⁶−1 = (x−1)(x+1)(x²+x+1)(x²−x+1)."""
    fac = factor_integer_poly([-1, 0, 0, 0, 0, 0, 1])
    fac_set = {(f, m) for f, m in fac}
    assert fac_set == {((-1, 1), 1), ((1, 1), 1), ((1, 1, 1), 1), ((1, -1, 1), 1)}
    assert _product_reconstructs([-1, 0, 0, 0, 0, 0, 1], fac)


def test_factor_x3_minus_2_irreducible():
    """x³−2 is irreducible (Eisenstein at 2)."""
    fac = factor_integer_poly([-2, 0, 0, 1])
    assert fac == [((-2, 0, 0, 1), 1)]
    assert _product_reconstructs([-2, 0, 0, 1], fac)


def test_factor_reducible_cubic():
    """(x−2)(x²+x+1) = x³−x²−x−2."""
    coeffs = [-2, -1, -1, 1]                          # low→high
    fac = factor_integer_poly(coeffs)
    fac_set = {(f, m) for f, m in fac}
    assert fac_set == {((-2, 1), 1), ((1, 1, 1), 1)}
    assert _product_reconstructs(coeffs, fac)


def test_factor_linear_is_irreducible():
    """A linear polynomial 2x−4 → its primitive irreducible (x−2)."""
    fac = factor_integer_poly([-4, 2])
    assert fac == [((-2, 1), 1)]
    assert _product_reconstructs([-4, 2], fac)


def test_factor_zero_polynomial_raises():
    with pytest.raises(ValueError):
        factor_integer_poly([0, 0, 0])


def test_factor_nonzero_constant_no_factors():
    assert factor_integer_poly([5]) == []


# ── eig_exact: rational eigenvalues ───────────────────────────────────────────────
def test_eig_symmetric_rational():
    """[[2,1],[1,2]] → {1:[1,−1], 3:[1,1]} (rational eigenvectors, each A·v=λ·v)."""
    res = eig_exact([[2, 1], [1, 2]])
    assert len(res) == 2
    by_val = {round(e["value"].real): e for e in res}
    assert set(by_val) == {1, 3}
    assert by_val[1]["min_poly"] == (-1, 1)
    assert by_val[3]["min_poly"] == (-3, 1)
    assert _proportional(by_val[1]["vector"], [1.0, -1.0])
    assert _proportional(by_val[3]["vector"], [1.0, 1.0])
    for e in res:
        assert e["algebraic_multiplicity"] == 1
        assert e["geometric_multiplicity"] == 1
        assert e["defective"] is False
        _assert_eigenrelation([[2, 1], [1, 2]], e["value"], e["vector"])


# ── eig_exact: ℚ(√5) real-algebraic eigenvectors ─────────────────────────────────
def test_eig_sqrt5():
    """[[1,1],[1,2]] → eigenvalues (3±√5)/2, exact real-algebraic eigenvectors."""
    A = [[1, 1], [1, 2]]
    res = eig_exact(A)
    assert len(res) == 2
    vals = sorted(e["value"].real for e in res)
    assert vals[0] == pytest.approx((3 - 5 ** 0.5) / 2)
    assert vals[1] == pytest.approx((3 + 5 ** 0.5) / 2)
    for e in res:
        assert e["min_poly"] == (1, -3, 1)            # λ²−3λ+1
        assert e["defective"] is False
        lam = e["value"].real
        # eigenvector of [[1,1],[1,2]] for λ is ∝ [1, λ−1]
        assert _proportional(e["vector"], [1.0, lam - 1.0])
        _assert_eigenrelation(A, e["value"], e["vector"])


# ── eig_exact: the rc-F payoff — COMPLEX eigenpairs + eigenvectors ───────────────
def test_eig_rotation_complex_eigenvectors():
    """[[0,−1],[1,0]] → COMPLEX eigenpairs {i, −i} with COMPLEX eigenvectors;
    A·v = λ·v complex to 1e-9 (the rc-F payoff)."""
    A = [[0, -1], [1, 0]]
    res = eig_exact(A, bits=80)
    assert len(res) == 2
    vals = sorted((e["value"] for e in res), key=lambda z: z.imag)
    assert abs(vals[0] - (-1j)) < 1e-12
    assert abs(vals[1] - 1j) < 1e-12
    for e in res:
        assert e["min_poly"] == (1, 0, 1)             # x²+1
        assert e["defective"] is False
        # the eigenvector is genuinely complex
        assert any(abs(complex(c).imag) > 1e-6 for c in e["vector"])
        _assert_eigenrelation(A, e["value"], e["vector"], tol=1e-9)


def test_eig_companion_cube_roots_of_unity():
    """Companion of x³−1 → {1, ω, ω²} with eigenvectors."""
    A = [[0, 0, 1], [1, 0, 0], [0, 1, 0]]
    res = eig_exact(A, bits=80)
    assert len(res) == 3
    vals = [e["value"] for e in res]
    true = [1.0 + 0j, cmath.exp(2j * math.pi / 3), cmath.exp(4j * math.pi / 3)]
    for t in true:
        assert min(abs(v - t) for v in vals) < 1e-9
    for e in res:
        _assert_eigenrelation(A, e["value"], e["vector"], tol=1e-9)


# ── eig_exact: repeated eigenvalue, non-defective ────────────────────────────────
def test_eig_2I_repeated_not_defective():
    """2·I (2×2) → λ=2 alg-mult 2, geom-mult 2, NOT defective; one distinct entry,
    its primary eigenvector valid."""
    A = [[2, 0], [0, 2]]
    res = eig_exact(A)
    assert len(res) == 1                              # one DISTINCT eigenvalue
    e = res[0]
    assert e["value"] == pytest.approx(2.0)
    assert e["algebraic_multiplicity"] == 2
    assert e["geometric_multiplicity"] == 2
    assert e["defective"] is False
    assert e["min_poly"] == (-2, 1)
    _assert_eigenrelation(A, e["value"], e["vector"])


# ── eig_exact: defective ─────────────────────────────────────────────────────────
def test_eig_defective_jordan_block():
    """Defective [[2,1],[0,2]] → λ=2 alg-mult 2, geom-mult 1, ONE eigenvector,
    defective=True (Jordan generalized eigenvectors out of scope)."""
    A = [[2, 1], [0, 2]]
    res = eig_exact(A)
    assert len(res) == 1
    e = res[0]
    assert e["value"] == pytest.approx(2.0)
    assert e["algebraic_multiplicity"] == 2
    assert e["geometric_multiplicity"] == 1
    assert e["defective"] is True
    assert e["min_poly"] == (-2, 1)
    # the single geometric eigenvector is ∝ [1, 0]
    assert _proportional(e["vector"], [1.0, 0.0])
    _assert_eigenrelation(A, e["value"], e["vector"])


# ── self-validation holds + cross-check against eigvals_exact ────────────────────
def test_self_validation_and_cross_check_eigvals():
    """For every case: Σ alg-mult == n; the eigenvalue multiset (with algebraic
    multiplicity) cross-checks ``eigvals_exact(include_complex=True)``; and the
    eig_exact self-validation (asserted internally) did not raise."""
    cases = [
        [[2, 1], [1, 2]],
        [[1, 1], [1, 2]],
        [[0, -1], [1, 0]],
        [[0, 0, 1], [1, 0, 0], [0, 1, 0]],
        [[2, 0], [0, 2]],
        [[2, 1], [0, 2]],
    ]
    for A in cases:
        n = len(A)
        res = eig_exact(A, bits=64)
        total_alg = sum(e["algebraic_multiplicity"] for e in res)
        assert total_alg == n, (A, total_alg, n)
        # the full eigenvalue multiset (each value repeated alg-mult times).
        got = []
        for e in res:
            got.extend([e["value"]] * e["algebraic_multiplicity"])
        ref = list(eigvals_exact(A, include_complex=True, bits=64))
        ref = [complex(r) for r in ref]
        # greedy multiset match
        assert len(got) == len(ref) == n
        rem = list(ref)
        for g in got:
            k = min(range(len(rem)), key=lambda i: abs(g - rem[i]))
            assert abs(g - rem[k]) < 1e-7, (A, g, rem)
            rem.pop(k)


def test_eig_exact_project_false_returns_qalg():
    """``project=False`` hands back the EXACT Qalg eigenvalue + Qalg eigenvector
    basis (for callers staying in the field)."""
    from srmech.amsc.qalg import Qalg
    res = eig_exact([[2, 1], [1, 2]], project=False)
    assert len(res) == 2
    for e in res:
        assert isinstance(e["value_qalg"], Qalg)
        assert isinstance(e["vectors_qalg"], list)
        assert all(isinstance(v, list) for v in e["vectors_qalg"])
        assert all(isinstance(c, Qalg) for v in e["vectors_qalg"] for c in v)
        assert "min_poly" in e and "algebraic_multiplicity" in e


def test_eig_determinism():
    A = [[0, 0, 1], [1, 0, 0], [0, 1, 0]]
    a = eig_exact(A, bits=64)
    b = eig_exact(A, bits=64)
    assert [(e["value"], tuple(e["vector"])) for e in a] == \
           [(e["value"], tuple(e["vector"])) for e in b]


def test_eig_empty_matrix():
    assert eig_exact([]) == []


# ── shared eigen-relation float check ─────────────────────────────────────────────
def _assert_eigenrelation(A, value, vector, tol=1e-9):
    """A·v ≈ value·v (complex float check)."""
    n = len(A)
    for i in range(n):
        lhs = sum(complex(A[i][j]) * complex(vector[j]) for j in range(n))
        rhs = complex(value) * complex(vector[i])
        assert abs(lhs - rhs) < tol, (
            f"A·v != λ·v at component {i}: {lhs!r} vs {rhs!r} (λ={value!r})")
