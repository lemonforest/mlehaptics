"""v0.9.0rc28 — ``eigvals_exact(include_complex=True)`` on REPEATED complex roots.

BUGFIX rc28. ``eigvals_exact(include_complex=True)`` HUNG on a matrix with a
REPEATED complex eigenvalue (e.g. the companion of ``(x²+1)²`` → ±i each
multiplicity 2). The complex path isolated roots on the FULL characteristic
polynomial, but box-subdivision cannot separate COINCIDENT roots: for a repeated
complex root ``_count_roots_in_box`` returns the multiplicity (≥ 2) in EVERY box
containing it, never 1, so ``_certify_complex_root`` shrank its box forever and
``_isolate_complex_roots_upper`` subdivided the same region forever (Fraction
denominators exploding) → the practical hang.

The fix mirrors the REAL path: isolate the complex roots PER SQUARE-FREE FACTOR
(``_square_free_factors``). Each square-free factor has all-SIMPLE roots, so the
box subdivision ALWAYS terminates; each isolated upper-half root is emitted with
its algebraic multiplicity (and its conjugate likewise).

These tests assert the repeated-complex cases now TERMINATE (a finite per-call
budget) AND return the correct eigenvalue multiset, cross-checked against
``eig_exact`` (which already handled them correctly via per-irreducible-factor
isolation). The rc24 simple-complex regressions are re-asserted unchanged.

numpy is GONE from srmech — these tests run and pass with numpy NOT installed.
"""
from __future__ import annotations

import time

import pytest

from srmech.amsc.cascade.matrix_cascades import (
    eig_exact,
    eigvals_exact,
)


# ── helpers ─────────────────────────────────────────────────────────────────────

def _companion(coeffs_low):
    """Companion matrix of the MONIC integer polynomial ``coeffs_low`` (low→high).

    ``C = [[0,…,0,−c0],[1,0,…,0,−c1],…,[0,…,1,−c_{n-1}]]`` — the last column is the
    negated low→high coefficients, with 1s on the sub-diagonal. Its characteristic
    polynomial is exactly the input (its eigenvalues are the polynomial's roots).
    """
    deg = len(coeffs_low) - 1
    assert coeffs_low[-1] == 1, "companion expects a monic polynomial"
    comp = [[0] * deg for _ in range(deg)]
    for i in range(1, deg):
        comp[i][i - 1] = 1
    for i in range(deg):
        comp[i][deg - 1] = -coeffs_low[i]
    return comp


def _pmul(a, b):
    """Integer polynomial multiply (low→high)."""
    out = [0] * (len(a) + len(b) - 1)
    for i, av in enumerate(a):
        for j, bv in enumerate(b):
            out[i + j] += av * bv
    return out


def _multiset_match(got, expected, tol=1e-9):
    """Assert ``got`` and ``expected`` are the same complex multiset to ``tol``
    (greedy nearest-neighbour pairing)."""
    got = [complex(g) for g in got]
    rem = [complex(e) for e in expected]
    assert len(got) == len(rem), (len(got), len(rem), got, rem)
    for g in got:
        j = min(range(len(rem)), key=lambda i: abs(g - rem[i]))
        d = abs(g - rem[j])
        assert d < tol, f"no match for {g!r} within {tol} (nearest {rem[j]!r}, d={d})"
        rem.pop(j)


def _eig_exact_multiset(comp, bits=80):
    """The eigenvalue multiset (with algebraic multiplicity) from ``eig_exact`` —
    the independent oracle (it isolates per IRREDUCIBLE factor, already correct on
    repeated complex roots)."""
    out = []
    for e in eig_exact(comp, bits=bits):
        out.extend([complex(e["value"])] * e["algebraic_multiplicity"])
    return out


# the polynomials under test (low→high), keyed by name.
_X2P1 = [1, 0, 1]            # x² + 1            → ±i
_X2P1_SQ = _pmul(_X2P1, _X2P1)            # (x²+1)²  → ±i each mult 2
_X2P1_CUBE = _pmul(_X2P1_SQ, _X2P1)       # (x²+1)³  → ±i each mult 3
_XM1_X2P1_SQ = _pmul([-1, 1], _X2P1_SQ)   # (x−1)(x²+1)² → 1, ±i each mult 2
_X2P1_X2P4 = _pmul(_X2P1, [4, 0, 1])      # (x²+1)(x²+4) → ±i, ±2i (all simple)


# ── the repeated-complex cases: TERMINATE + correct multiset ─────────────────────

def test_x2p1_squared_terminates_and_correct():
    """Companion of (x²+1)² → {i, i, −i, −i}. Used to HANG; must now be fast +
    correct."""
    comp = _companion(_X2P1_SQ)
    t0 = time.time()
    ev = eigvals_exact(comp, include_complex=True, bits=80)
    dt = time.time() - t0
    assert dt < 30.0, f"eigvals_exact hung/too slow: {dt:.1f}s"
    _multiset_match(ev, [1j, 1j, -1j, -1j])


def test_x2p1_cubed_terminates_and_correct():
    """Companion of (x²+1)³ → ±i each multiplicity 3."""
    comp = _companion(_X2P1_CUBE)
    t0 = time.time()
    ev = eigvals_exact(comp, include_complex=True, bits=80)
    dt = time.time() - t0
    assert dt < 30.0, f"eigvals_exact hung/too slow: {dt:.1f}s"
    _multiset_match(ev, [1j, 1j, 1j, -1j, -1j, -1j])


def test_xm1_x2p1_squared_terminates_and_correct():
    """Companion of (x−1)(x²+1)² → {1, i, i, −i, −i} (mixed real + repeated
    complex)."""
    comp = _companion(_XM1_X2P1_SQ)
    t0 = time.time()
    ev = eigvals_exact(comp, include_complex=True, bits=80)
    dt = time.time() - t0
    assert dt < 30.0, f"eigvals_exact hung/too slow: {dt:.1f}s"
    _multiset_match(ev, [1 + 0j, 1j, 1j, -1j, -1j])


# ── simple-complex regressions (must STILL be correct) ───────────────────────────

def test_mixed_distinct_complex_regression():
    """(x²+1)(x²+4) → {±i, ±2i} — all simple; the regression the per-factor path
    must not break."""
    comp = _companion(_X2P1_X2P4)
    ev = eigvals_exact(comp, include_complex=True, bits=80)
    _multiset_match(ev, [1j, -1j, 2j, -2j])


def test_rc24_simple_complex_regressions():
    """The rc24 simple-complex cases still correct: rotation → ±i; x³−1; x⁴+1."""
    # rotation [[0,−1],[1,0]] → ±i.
    _multiset_match(
        eigvals_exact([[0, -1], [1, 0]], include_complex=True, bits=80),
        [1j, -1j])
    # x³ − 1 → 1, the two primitive cube roots of unity.
    comp3 = _companion([-1, 0, 0, 1])
    import cmath
    cube = [cmath.exp(2j * cmath.pi * k / 3) for k in range(3)]
    _multiset_match(eigvals_exact(comp3, include_complex=True, bits=80), cube, tol=1e-8)
    # x⁴ + 1 → the four primitive 8th roots of unity.
    comp4 = _companion([1, 0, 0, 0, 1])
    quart = [cmath.exp(1j * cmath.pi * (2 * k + 1) / 4) for k in range(4)]
    _multiset_match(eigvals_exact(comp4, include_complex=True, bits=80), quart, tol=1e-8)


# ── cross-check vs eig_exact (the independent oracle) ─────────────────────────────

@pytest.mark.parametrize("name,poly", [
    ("(x^2+1)^2", _X2P1_SQ),
    ("(x^2+1)^3", _X2P1_CUBE),
    ("(x-1)(x^2+1)^2", _XM1_X2P1_SQ),
    ("(x^2+1)(x^2+4)", _X2P1_X2P4),
])
def test_eigvals_exact_agrees_with_eig_exact(name, poly):
    """eigvals_exact(include_complex=True) must AGREE (multiset) with eig_exact,
    which isolates per irreducible factor and already handled repeated complex
    roots correctly."""
    comp = _companion(poly)
    got = [complex(z) for z in eigvals_exact(comp, include_complex=True, bits=80)]
    ref = _eig_exact_multiset(comp, bits=80)
    _multiset_match(got, ref, tol=1e-7)


def test_all_real_spectrum_unaffected():
    """A purely-real spectrum still returns only floats (include_complex no-op
    when n_real == n)."""
    ev = eigvals_exact([[2, 1], [0, 2]], include_complex=True, bits=80)
    assert all(isinstance(x, float) for x in ev)
    _multiset_match([complex(x) for x in ev], [2 + 0j, 2 + 0j])
