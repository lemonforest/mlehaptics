"""v0.9.0rc24 — exact COMPLEX eigenvalues (the rotation-last roadmap's rc-E).

``eigvals_exact`` isolated only the REAL eigenvalues of an integer matrix
(char_poly → Yun square-free → Sturm → Fraction bisection). rc24 adds the COMPLEX
ones, EXACTLY isolated: a float-QR candidate is CERTIFIED as a unique root of the
exact integer characteristic polynomial in a rational box by the argument-principle
root-count ``_count_roots_in_box`` (the winding number in EXACT ``Fraction``
arithmetic — NO float in the count), then refined to ``bits``. The emitted
``complex`` is the single terminal projection of the certified box center.

The load-bearing piece is ``_count_roots_in_box`` — unit-tested HARD on its own
below (``x²+1`` / ``x²−2`` / ``x⁴+1``). Then the matrix-level cases.

numpy is GONE from srmech — these tests run and pass with numpy NOT installed.
Oracles are numpy-free: hand-known exact roots + the (numpy-free) ``mat_eigvals``
float-QR spectrum for the cases where float-QR is reliable.
"""
from __future__ import annotations

import cmath
import math
from fractions import Fraction as F

import pytest

from srmech.amsc.cascade.matrix_cascades import (
    _count_roots_in_box,
    eigvals_exact,
)
from srmech.amsc.laplacian import mat_eigvals
from srmech.amsc.mat import Mat


# ── helpers ─────────────────────────────────────────────────────────────────────

def _multiset_match(got, expected, tol=1e-9):
    """Assert that ``got`` and ``expected`` are the same multiset of complex
    numbers to ``tol`` (greedy nearest-neighbour pairing)."""
    got = [complex(g) for g in got]
    rem = [complex(e) for e in expected]
    assert len(got) == len(rem), (len(got), len(rem), got, rem)
    for g in got:
        j = min(range(len(rem)), key=lambda i: abs(g - rem[i]))
        d = abs(g - rem[j])
        assert d < tol, f"no match for {g!r} within {tol} (nearest {rem[j]!r}, d={d})"
        rem.pop(j)
    assert not rem


# ── _count_roots_in_box: the load-bearing exact primitive ────────────────────────

def test_count_box_x2_plus_1():
    """``p = x²+1`` has roots ±i. (low→high coeffs ``[1, 0, 1]``.)"""
    p = [1, 0, 1]
    assert _count_roots_in_box(p, F(-1, 2), F(1, 2), F(1, 2), F(3, 2)) == 1   # +i
    assert _count_roots_in_box(p, F(-1, 2), F(1, 2), F(-3, 2), F(-1, 2)) == 1  # -i
    assert _count_roots_in_box(p, F(-1, 2), F(1, 2), F(-1, 4), F(1, 4)) == 0   # 0
    assert _count_roots_in_box(p, F(-2), F(2), F(-2), F(2)) == 2               # both


def test_count_box_x2_minus_2():
    """``p = x²−2`` has the REAL roots ±√2 ≈ ±1.414 (low→high ``[-2, 0, 1]``)."""
    p = [-2, 0, 1]
    # a box that contains +√2 (its only root in [1,2]×[−½,½]):
    assert _count_roots_in_box(p, F(1), F(2), F(-1, 2), F(1, 2)) == 1
    # a box that does NOT (no root in [0,1]×[−½,½]):
    assert _count_roots_in_box(p, F(0), F(1), F(-1, 2), F(1, 2)) == 0
    # the wide strip catches both ±√2:
    assert _count_roots_in_box(p, F(-2), F(2), F(-1, 2), F(1, 2)) == 2


def test_count_box_x4_plus_1():
    """``p = x⁴+1`` has the 4 roots ``e^{iπ/4·{1,3,5,7}}`` ≈ (±0.707, ±0.707), one
    per quadrant (low→high ``[1, 0, 0, 0, 1]``)."""
    p = [1, 0, 0, 0, 1]
    assert _count_roots_in_box(p, F(0), F(2), F(0), F(2)) == 1     # Q1 (+,+)
    assert _count_roots_in_box(p, F(-2), F(0), F(0), F(2)) == 1    # Q2 (-,+)
    assert _count_roots_in_box(p, F(-2), F(0), F(-2), F(0)) == 1   # Q3 (-,-)
    assert _count_roots_in_box(p, F(0), F(2), F(-2), F(0)) == 1    # Q4 (+,-)
    assert _count_roots_in_box(p, F(-2), F(2), F(-2), F(2)) == 4   # all four
    # a tiny box around the origin holds none:
    assert _count_roots_in_box(p, F(-1, 10), F(1, 10), F(-1, 10), F(1, 10)) == 0


def test_count_box_boundary_root_raises():
    """A root exactly on the boundary makes the count ill-defined (half-integer
    winding) → a clear ValueError telling the caller to nudge the corners."""
    p = [1, 0, 1]                                      # x²+1, roots ±i
    with pytest.raises(ValueError):
        # +i lies on the top edge y = 1:
        _count_roots_in_box(p, F(-1, 2), F(1, 2), F(0), F(1))


def test_count_box_degenerate_args_raise():
    p = [1, 0, 1]
    with pytest.raises(ValueError):
        _count_roots_in_box(p, F(1), F(0), F(0), F(1))    # x0 >= x1
    with pytest.raises(ValueError):
        _count_roots_in_box([0, 0, 0], F(-1), F(1), F(-1), F(1))  # zero poly


# ── eigvals_exact(include_complex=...): matrix-level cases ───────────────────────

def test_rotation_pure_imaginary_and_backcompat():
    """``A = [[0,−1],[1,0]]`` (90° rotation, char poly x²+1) → eigenvalues {i, −i}.
    With ``include_complex=False`` it still returns ``[]`` (no real eigenvalues) —
    the backward-compatibility check."""
    A = [[0, -1], [1, 0]]
    # backward-compat: default is real-only, and this matrix has NO real eigenvalue.
    assert eigvals_exact(A) == []
    assert eigvals_exact(A, include_complex=False) == []
    # include_complex=True: the exact ±i.
    ev = eigvals_exact(A, include_complex=True, bits=80)
    assert len(ev) == 2
    _multiset_match(ev, [1j, -1j], tol=1e-12)
    # cross-check the float-QR spectrum (reliable for this matrix).
    _multiset_match(ev, list(mat_eigvals(Mat.from_rows(A))), tol=1e-9)


def test_companion_cube_roots_of_unity():
    """Companion of x³−1 ``[[0,0,1],[1,0,0],[0,1,0]]`` → {1, ω, ω²} with
    ω = (−1+√3 i)/2 ≈ −0.5 ± 0.866i. (NOTE: float-QR ``mat_eigvals`` STALLS on this
    cyclic permutation matrix — returns all-zeros — so the exact subdivision
    fallback carries it; we multiset-match the KNOWN exact roots, not mat_eigvals.)"""
    A = [[0, 0, 1], [1, 0, 0], [0, 1, 0]]
    ev = eigvals_exact(A, include_complex=True, bits=80)
    assert len(ev) == 3
    true = [1.0, cmath.exp(2j * math.pi / 3), cmath.exp(4j * math.pi / 3)]
    _multiset_match(ev, true, tol=1e-9)
    # ordering contract: the single real (1.0) comes first as a float.
    assert ev[0] == pytest.approx(1.0)
    assert isinstance(ev[0], float)


def test_one_real_one_complex_pair():
    """Companion of x³−x²+x−1 = (x−1)(x²+1) ``[[0,0,1],[1,0,-1],[0,1,1]]`` →
    {1, i, −i}."""
    A = [[0, 0, 1], [1, 0, -1], [0, 1, 1]]
    ev = eigvals_exact(A, include_complex=True, bits=80)
    assert len(ev) == 3
    _multiset_match(ev, [1.0, 1j, -1j], tol=1e-9)
    # mat_eigvals is reliable here (not a degenerate cyclic case).
    _multiset_match(ev, list(mat_eigvals(Mat.from_rows(A))), tol=1e-9)


def test_companion_x4_plus_1():
    """Companion of x⁴+1 → the 4 primitive 8th roots of unity
    ``e^{iπ/4·{1,3,5,7}}`` ≈ (±0.707, ±0.707). (float-QR also stalls here →
    subdivision fallback.)"""
    A = [[0, 0, 0, -1], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]]
    ev = eigvals_exact(A, include_complex=True, bits=80)
    assert len(ev) == 4
    true = [cmath.exp(1j * math.pi * k / 4) for k in (1, 3, 5, 7)]
    _multiset_match(ev, true, tol=1e-9)


def test_conjugate_symmetry_is_exact():
    """A complex root ``a+bi`` (b>0) pairs with its EXACT conjugate ``a−bi`` — the
    real parts equal and the imag parts exactly negated (mirrored off ONE box
    center, not two independent isolations)."""
    A = [[0, -1], [1, 0]]                              # ±i
    ev = eigvals_exact(A, include_complex=True, bits=64)
    cs = [z for z in ev if isinstance(z, complex) and abs(z.imag) > 1e-12]
    assert len(cs) == 2
    a, b = sorted(cs, key=lambda z: z.imag)            # a has im<0, b has im>0
    assert a.real == b.real                            # EXACT equal real parts
    assert a.imag == -b.imag                           # EXACT negated imag parts


def test_backcompat_real_only_default_unchanged():
    """``include_complex=False`` (default) equals the pre-rc24 real-only output on
    a real-spectrum integer symmetric matrix: ``[[2,1],[1,2]]`` → ``[1.0, 3.0]``."""
    S = [[2, 1], [1, 2]]
    assert eigvals_exact(S) == [1.0, 3.0]
    assert eigvals_exact(S, include_complex=False) == [1.0, 3.0]
    # include_complex=True on an all-real spectrum returns exactly the reals.
    assert eigvals_exact(S, include_complex=True) == [1.0, 3.0]


def test_return_intervals_real_only_path_unchanged():
    """``return_intervals=True`` still yields the exact (lo, hi) Fraction intervals
    on the real-only path (the rc-E param does not perturb it)."""
    S = [[2, 1], [1, 2]]
    iv = eigvals_exact(S, return_intervals=True)
    assert len(iv) == 2
    for (lo, hi) in iv:
        assert isinstance(lo, F) and isinstance(hi, F)
    # the bracketed centers are 1 and 3:
    centers = sorted(float((lo + hi) / 2) for (lo, hi) in iv)
    assert centers == [1.0, 3.0]


def test_real_part_type_float_complex_part_type_complex():
    """The return contract: reals are Python ``float`` (ascending, first); the
    certified complex eigenvalues are Python ``complex`` (sorted by (re, im),
    after the reals)."""
    A = [[0, 0, 1], [1, 0, -1], [0, 1, 1]]            # (x-1)(x^2+1) → {1, ±i}
    ev = eigvals_exact(A, include_complex=True, bits=64)
    reals = [z for z in ev if isinstance(z, float)]
    cplx = [z for z in ev if isinstance(z, complex)]
    assert reals == [1.0]
    assert len(cplx) == 2
    # complex sorted by (re, im): −i before +i (same re, im −1 < +1).
    assert cplx[0].imag < cplx[1].imag
    # and the reals precede the complex in the full list.
    assert ev.index(reals[0]) < min(ev.index(c) for c in cplx)


def test_multiset_matches_mat_eigvals_where_reliable():
    """For the cases where float-QR ``mat_eigvals`` is RELIABLE (not a degenerate
    cyclic permutation), the exactly-isolated spectrum multiset-matches it to
    ~1e-9 — the internal-validation contract."""
    cases = [
        [[0, -1], [1, 0]],                            # ±i
        [[0, 0, 1], [1, 0, -1], [0, 1, 1]],           # {1, ±i}
        [[2, 1], [1, 2]],                             # {1, 3} (all real)
    ]
    for rows in cases:
        ev = eigvals_exact(rows, include_complex=True, bits=64)
        qr = list(mat_eigvals(Mat.from_rows(rows)))
        _multiset_match(ev, qr, tol=1e-9)


def test_len_equals_matrix_order():
    """``len(result) == n`` for every include_complex spectrum (reals + complex
    with multiplicity)."""
    for rows in (
        [[0, -1], [1, 0]],
        [[0, 0, 1], [1, 0, 0], [0, 1, 0]],
        [[0, 0, 1], [1, 0, -1], [0, 1, 1]],
        [[0, 0, 0, -1], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]],
        [[2, 1], [1, 2]],
    ):
        n = len(rows)
        ev = eigvals_exact(rows, include_complex=True, bits=48)
        assert len(ev) == n


def test_determinism():
    """The certified spectrum is deterministic — repeated calls give identical
    results (same box centers, same float projection)."""
    A = [[0, 0, 1], [1, 0, 0], [0, 1, 0]]
    a = eigvals_exact(A, include_complex=True, bits=64)
    b = eigvals_exact(A, include_complex=True, bits=64)
    assert a == b
    # the real-only path too.
    assert eigvals_exact(A) == eigvals_exact(A)
