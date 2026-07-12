"""srmech 0.9.0rc40 — the EXACT-RATIONAL matrix carrier C peer (srmech_qmat_*):
byte/value parity of the native ``srmech_qmat_{rref,rank,det,inverse,solve,
nullspace}`` against the pure-Python ``QMat`` Gauss-Jordan AND an independent
``fractions.Fraction`` oracle. Numpy-free, math-free (no ``import math`` / numpy).

Parity is asserted exact when the native ``srmech_qmat_*`` peer is present, and
skipped cleanly otherwise (the pure-Python QMat body is the complete,
ceiling-free alternative + the oracle). The hardest case — the rc34 QMat keystone
with ``Q(10**40+1, 3**30)`` entries whose ``det`` is an 81-digit numerator over
``3**60`` (> 2**64) — is cross-checked Python == C == Fraction-oracle EXACTLY,
proving no int64/Q61 ceiling.

The pure path is forced by patching ``srmech.amsc.qmat._native`` to ``None`` for
the pure run; the C path is exercised directly through the ``_native.qmat_*_c``
marshallers. Both are compared to the Fraction oracle.
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from srmech.amsc import qmat as _qmat_mod
from srmech.amsc.q import Q
from srmech.amsc.qmat import QMat


def _native():
    try:
        from srmech.amsc import _native as nat
    except ImportError:
        return None
    if not getattr(nat, "has_native_qmat", lambda: False)():
        return None
    return nat


_NATIVE = _native()
_skip_no_native = pytest.mark.skipif(
    _NATIVE is None, reason="native srmech_qmat_* peer not present (pure is the oracle)")


# ── pure-path helpers (force QMat onto its pure Gauss-Jordan body) ────────────
class _force_pure:
    """Context manager: patch qmat._native -> None so QMat runs its pure body."""

    def __enter__(self):
        self._saved = _qmat_mod._native
        _qmat_mod._native = lambda: None
        return self

    def __exit__(self, *exc):
        _qmat_mod._native = self._saved
        return False


def _pure_det(m: QMat) -> Q:
    with _force_pure():
        return m.det()


def _pure_rref(m: QMat) -> QMat:
    with _force_pure():
        return m.rref()


def _pure_rank(m: QMat) -> int:
    with _force_pure():
        return m.rank()


def _pure_inverse(m: QMat):
    with _force_pure():
        return m.inverse()


def _pure_solve(m: QMat, b):
    with _force_pure():
        return m.solve(b)


def _pure_nullspace(m: QMat):
    with _force_pure():
        return m.nullspace()


# ── Fraction Gauss-Jordan oracle (independent of srmech) ──────────────────────
def _to_frac(m):
    return [[Fraction(q.numerator, q.denominator) for q in r] for r in m._rows]


def _as_frac(x):
    """Coerce a Q or Fraction (or int) entry to an exact Fraction."""
    if isinstance(x, Fraction):
        return x
    num = getattr(x, "numerator", None)
    den = getattr(x, "denominator", None)
    if num is not None and den is not None:
        return Fraction(num, den)
    return Fraction(x)


def _frac_rref(rows, n_left):
    R = [[_as_frac(x) for x in r] for r in rows]
    nr = len(R)
    tc = len(R[0]) if R else 0
    piv_cols = []
    prc = {}
    r = 0
    for c in range(n_left):
        p = None
        for rr in range(r, nr):
            if R[rr][c] != 0:
                p = rr
                break
        if p is None:
            continue
        R[r], R[p] = R[p], R[r]
        inv = Fraction(1) / R[r][c]
        R[r] = [x * inv for x in R[r]]
        for rr in range(nr):
            if rr != r and R[rr][c] != 0:
                f = R[rr][c]
                R[rr] = [R[rr][j] - f * R[r][j] for j in range(tc)]
        piv_cols.append(c)
        prc[c] = r
        r += 1
        if r == nr:
            break
    return R, piv_cols, prc


def _frac_det(rows):
    n = len(rows)
    R = _to_frac_rows(rows)
    sign = 1
    prod = Fraction(1)
    for c in range(n):
        p = None
        for rr in range(c, n):
            if R[rr][c] != 0:
                p = rr
                break
        if p is None:
            return Fraction(0)
        if p != c:
            R[c], R[p] = R[p], R[c]
            sign = -sign
        prod *= R[c][c]
        for rr in range(c + 1, n):
            if R[rr][c] != 0:
                f = R[rr][c] / R[c][c]
                R[rr] = [R[rr][j] - f * R[c][j] for j in range(n)]
    return prod * sign


def _to_frac_rows(rows):
    return [[Fraction(q.numerator, q.denominator) for q in r] for r in rows]


def _frac_inverse(rows):
    n = len(rows)
    M = _to_frac_rows(rows)
    aug = [M[i] + [Fraction(1) if i == j else Fraction(0) for j in range(n)]
           for i in range(n)]
    R, pcols, _ = _frac_rref(aug, n)
    if pcols != list(range(n)):
        return None
    return [[R[i][n + j] for j in range(n)] for i in range(n)]


def _frac_solve(rows, b_rows):
    n = len(rows)
    bc = len(b_rows[0])
    M = _to_frac_rows(rows)
    B = _to_frac_rows(b_rows)
    aug = [M[i] + B[i] for i in range(n)]
    R, pcols, _ = _frac_rref(aug, n)
    if pcols != list(range(n)):
        return None
    return [[R[i][n + j] for j in range(bc)] for i in range(n)]


def _frac_nullspace(rows, n_cols):
    R, pcols, prc = _frac_rref(rows, n_cols)
    free = [c for c in range(n_cols) if c not in prc]
    out = []
    for fc in free:
        v = [Fraction(0)] * n_cols
        v[fc] = Fraction(1)
        for c in pcols:
            v[c] = -R[prc[c]][fc]
        out.append(v)
    return out


def _qmat_to_frac(m):
    return [[Fraction(q.numerator, q.denominator) for q in r] for r in m._rows]


# ── the matrices under test (hardcoded, no RNG) ───────────────────────────────
def _M(rows):
    return QMat.from_rows(rows)


# Full-rank invertibles + singulars + tall/wide (varied by hardcoded constants).
_FULL = [
    _M([[1, 2], [3, 4]]),
    _M([[2, 1], [1, 3]]),
    _M([[4, 7], [2, 6]]),
    _M([[1, 2, 3], [4, 5, 6], [7, 8, 10]]),
    _M([[2, 0, -1], [1, 3, 2], [0, -1, 4]]),
    _M([[Q(1, 2), Q(1, 3)], [Q(1, 4), Q(2, 5)]]),
    _M([[5, 1, 2, 0], [0, 3, 1, 1], [1, 0, 4, 2], [2, 1, 0, 3]]),
    _M([[Q(3, 7), Q(-2, 5), Q(1)], [Q(1), Q(4, 3), Q(-1, 2)],
        [Q(0), Q(2), Q(5, 6)]]),
]

_SINGULAR = [
    _M([[1, 2], [2, 4]]),
    _M([[1, 2, 3], [2, 4, 6], [1, 1, 1]]),
    _M([[1, 2, 3], [2, 4, 6]]),                       # rank 1, wide
    _M([[0, 0], [0, 0]]),
    _M([[1, 0, 1], [0, 1, 1], [1, 1, 2]]),            # rank 2, r2 = r0+r1
]


def _rm_pairs(m):
    return [(q._n, q._d) for r in m._rows for q in r]


# ─────────────────────────── det ─────────────────────────────────────────────
@_skip_no_native
@pytest.mark.parametrize("m", _FULL + [s for s in _SINGULAR if s.n_rows == s.n_cols])
def test_det_parity(m):
    pure = _pure_det(m)
    cpair = _NATIVE.qmat_det_c(_rm_pairs(m), m.n_rows)
    cval = Q(cpair[0], cpair[1])
    oracle = _frac_det(m._rows)
    assert pure == cval
    assert Fraction(cval.numerator, cval.denominator) == oracle


@_skip_no_native
def test_det_keystone_81_digit():
    # The rc34 QMat keystone: Q(10**40+1, 3**30) on the diagonal, 1 off it.
    e = Q(10**40 + 1, 3**30)
    m = _M([[e, Q(1)], [Q(1), e]])
    pure = _pure_det(m)
    cpair = _NATIVE.qmat_det_c(_rm_pairs(m), 2)
    cval = Q(cpair[0], cpair[1])
    a = Fraction(10**40 + 1, 3**30)
    oracle = a * a - 1                                # det of [[a,1],[1,a]]
    assert len(str(oracle.numerator).lstrip("-")) == 81   # > 2**64 numerator
    assert oracle.denominator == 3**60
    assert pure == cval
    assert Fraction(cval.numerator, cval.denominator) == oracle


# ─────────────────────────── rref / rank ─────────────────────────────────────
@_skip_no_native
@pytest.mark.parametrize("m", _FULL + _SINGULAR)
def test_rref_parity(m):
    pure = _pure_rref(m)
    res = _NATIVE.qmat_rref_c(_rm_pairs(m), m.n_rows, m.n_cols)
    cpairs, crank, _piv = res
    cmat = _qmat_from_flat_pairs(cpairs, m.n_rows, m.n_cols)
    assert _qmat_to_frac(pure) == _qmat_to_frac(cmat)
    # RREF is canonical (unique), so it equals the Fraction oracle too.
    oracle, opiv, _ = _frac_rref(m._rows, m.n_cols)
    assert _qmat_to_frac(cmat) == oracle
    assert crank == len(opiv)


@_skip_no_native
@pytest.mark.parametrize("m", _FULL + _SINGULAR)
def test_rank_parity(m):
    pure = _pure_rank(m)
    crank = _NATIVE.qmat_rank_c(_rm_pairs(m), m.n_rows, m.n_cols)
    _, opiv, _ = _frac_rref(m._rows, m.n_cols)
    assert pure == crank == len(opiv)


def _qmat_from_flat_pairs(pairs, nr, nc):
    return QMat.from_rows(
        [[Q(pairs[r * nc + c][0], pairs[r * nc + c][1]) for c in range(nc)]
         for r in range(nr)])


# ─────────────────────────── inverse ─────────────────────────────────────────
@_skip_no_native
@pytest.mark.parametrize("m", _FULL)
def test_inverse_parity_full(m):
    pure = _pure_inverse(m)
    cpairs, sing = _NATIVE.qmat_inverse_c(_rm_pairs(m), m.n_rows)
    assert not sing
    cmat = _qmat_from_flat_pairs(cpairs, m.n_rows, m.n_rows)
    oracle = _frac_inverse(m._rows)
    assert _qmat_to_frac(pure) == _qmat_to_frac(cmat) == oracle
    # round-trip: A @ A^-1 == I
    prod = m.matmul(cmat)
    n = m.n_rows
    assert prod == QMat.identity(n)


@_skip_no_native
@pytest.mark.parametrize("m", [s for s in _SINGULAR if s.n_rows == s.n_cols])
def test_inverse_singular(m):
    _, sing = _NATIVE.qmat_inverse_c(_rm_pairs(m), m.n_rows)
    assert sing
    assert _frac_inverse(m._rows) is None
    # the pure QMat raises ValueError; so must the dispatched one.
    with _force_pure():
        with pytest.raises(ValueError):
            m.inverse()
    with pytest.raises(ValueError):
        m.inverse()


# ─────────────────────────── solve ───────────────────────────────────────────
_SOLVE_CASES = [
    (_M([[2, 1], [1, 3]]), [[3], [5]]),
    (_M([[1, 2], [3, 4]]), [[5], [6]]),
    (_M([[4, 7], [2, 6]]), [[1], [1]]),
    (_M([[1, 2, 3], [4, 5, 6], [7, 8, 10]]), [[6], [15], [25]]),
    # multi-column RHS
    (_M([[2, 1], [1, 3]]), [[3, 1], [5, 0]]),
]


@_skip_no_native
@pytest.mark.parametrize("m,b", _SOLVE_CASES)
def test_solve_parity(m, b):
    pure = _pure_solve(m, b)
    bmat = QMat.from_rows(b)
    cpairs, sing = _NATIVE.qmat_solve_c(_rm_pairs(m), m.n_rows,
                                        _rm_pairs(bmat), bmat.n_cols)
    assert not sing
    cmat = _qmat_from_flat_pairs(cpairs, m.n_rows, bmat.n_cols)
    oracle = _frac_solve(m._rows, bmat._rows)
    assert _qmat_to_frac(pure) == _qmat_to_frac(cmat) == oracle
    # round-trip A @ x == b
    assert m.matmul(cmat) == bmat


@_skip_no_native
def test_solve_singular():
    m = _M([[1, 2], [2, 4]])
    b = QMat.from_rows([[1], [2]])
    _, sing = _NATIVE.qmat_solve_c(_rm_pairs(m), 2, _rm_pairs(b), 1)
    assert sing
    with _force_pure():
        with pytest.raises(ValueError):
            m.solve(b)
    with pytest.raises(ValueError):
        m.solve(b)


# ─────────────────────────── nullspace ───────────────────────────────────────
_NULL_CASES = [
    _M([[1, 2, 3], [2, 4, 6]]),                       # rank 1 -> 2 free
    _M([[1, 0, 1], [0, 1, 1], [1, 1, 2]]),            # rank 2 -> 1 free
    _M([[1, 2], [2, 4]]),                             # rank 1 -> 1 free
    _M([[0, 0, 0], [0, 0, 0]]),                       # rank 0 -> 3 free
    _M([[Q(1, 2), Q(1), Q(3, 2)], [Q(1), Q(2), Q(3)]]),  # rational, rank 1
]


@_skip_no_native
@pytest.mark.parametrize("m", _NULL_CASES)
def test_nullspace_parity(m):
    pure = _pure_nullspace(m)
    cols = _NATIVE.qmat_nullspace_c(_rm_pairs(m), m.n_rows, m.n_cols)
    oracle = _frac_nullspace(m._rows, m.n_cols)
    # same basis SIZE
    assert len(pure) == len(cols) == len(oracle)
    # element-for-element basis match (pure column vectors are n×1 QMats)
    for k, vec in enumerate(cols):
        cfrac = [Fraction(p[0], p[1]) for p in vec]
        pfrac = [Fraction(q.numerator, q.denominator) for (q,) in pure[k]._rows]
        assert cfrac == pfrac == oracle[k]
        # each basis vector is in the kernel: A @ v == 0
        vmat = QMat.from_rows([[Q(p[0], p[1])] for p in vec])
        prod = m.matmul(vmat)
        assert all(q == 0 for (q,) in prod._rows)


@_skip_no_native
def test_nullspace_full_rank_empty():
    m = _M([[1, 2], [3, 4]])                          # full column rank
    cols = _NATIVE.qmat_nullspace_c(_rm_pairs(m), 2, 2)
    assert cols == []
    with _force_pure():
        assert m.nullspace() == []


# ─────────────────────────── coefficient-growth ceiling ──────────────────────
@_skip_no_native
def test_coefficient_growth_no_spurious_overflow():
    # A 4x4 with LARGE rational entries whose exact elimination pushes the
    # intermediate (num, den) magnitudes far past 2**64 (the inverse entries are
    # ratios of 3x3 minors of ~13-digit numbers ≈ 50+ digits) — confirm the arena
    # bound holds (no spurious OVERFLOW), the result is EXACT (Python == C ==
    # Fraction-oracle), and A @ A^-1 == I.
    rows = [
        [Q(10**13 + 1, 3), Q(10**13 + 2, 7), Q(-1, 11), Q(2)],
        [Q(1), Q(10**13 + 5, 13), Q(3, 5), Q(10**13 + 7, 2)],
        [Q(-10**13, 17), Q(2), Q(10**13 + 11, 19), Q(1, 3)],
        [Q(4), Q(-10**13 + 1, 23), Q(1), Q(10**13 + 13, 29)],
    ]
    m = _M(rows)
    cpairs, sing = _NATIVE.qmat_inverse_c(_rm_pairs(m), 4)
    assert not sing
    cmat = _qmat_from_flat_pairs(cpairs, 4, 4)
    # at least one inverse entry must exceed 2**64 in |num| or den (real growth).
    # Class-K magnitude via an explicit sign-branch, never an ALU abs().
    def _mag(x):
        return x if x >= 0 else -x
    big = any(_mag(p[0]) > 2**64 or p[1] > 2**64 for p in cpairs)
    assert big
    assert _qmat_to_frac(cmat) == _frac_inverse(m._rows)
    assert m.matmul(cmat) == QMat.identity(4)
    # det parity at this magnitude too (58-digit numerator, > 2**64)
    dp = _NATIVE.qmat_det_c(_rm_pairs(m), 4)
    assert _mag(dp[0]) > 2**64
    assert Fraction(dp[0], dp[1]) == _frac_det(m._rows)
    assert _pure_det(m) == Q(dp[0], dp[1])
