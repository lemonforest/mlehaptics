"""v0.7.1rc3 — ``srmech.amsc.laplacian.dense_solve`` (#897 §26).

The reusable Class-L dense linear solve ``A · X = B`` the Schur-complement /
DtN float path composes over. Tests two things:

* the exact-rational (``fractions.Fraction``) Gauss–Jordan path — always runs,
  numpy-free, bit-exact;
* the float path (native C peer ``srmech_dense_solve_f64`` when attached, else
  the pure-Python list solve) matches the EXACT-Fraction reference to float
  tolerance (native-guarded — the C-symbol-presence test skips on pure-Python /
  Pyodide installs and on a stale-ABI lib that predates the rc3 symbol).

numpy-FREE (#564): numpy is GONE from srmech — ``dense_solve`` returns plain
Python lists (exact=True → ``Fraction`` lists). The obsolete numpy-parity tests
have been DELETED; the float path is verified against the framework's own
exact-Fraction oracle, never against numpy.
"""

from fractions import Fraction

import pytest

from srmech.amsc import _native, laplacian  # noqa: F401
from srmech.amsc.laplacian import dense_solve, schur_complement

# Native available AND the additive rc3 symbol present (a stale ABI-3 lib
# built before this rc lacks it — hasattr-guarded everywhere).
_HAS_C = (
    _native.HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_dense_solve_f64")
)
_needs_c = pytest.mark.skipif(
    not _HAS_C, reason="native srmech_dense_solve_f64 not attached"
)


def _lcg(seed):
    """Deterministic numpy-free pseudo-random stream in (-1, 1)."""
    state = (seed * 2654435761 + 12345) & 0x7FFFFFFF
    while True:
        state = (1103515245 * state + 12345) & 0x7FFFFFFF
        yield (state / 0x3FFFFFFF) - 1.0


def _matmul(A, B):
    """Plain-list matrix product (numpy-free)."""
    m, k, n = len(A), len(B), len(B[0])
    return [[sum(A[i][p] * B[p][j] for p in range(k)) for j in range(n)]
            for i in range(m)]


def _transpose(A):
    return [[A[i][j] for i in range(len(A))] for j in range(len(A[0]))]

# Path graph 0-1-2-3 Laplacian + its interior block (the rc1 worked instance).
_PATH4_L = [
    [1, -1, 0, 0],
    [-1, 2, -1, 0],
    [0, -1, 2, -1],
    [0, 0, -1, 1],
]
_THIRD = Fraction(1, 3)
_EXPECTED_S = [[_THIRD, -_THIRD], [-_THIRD, _THIRD]]


# ── exact-rational path (always runs) ─────────────────────────────────


def test_dense_solve_exact_identity():
    # I · X = B  ⟹  X = B, bit-exact in Fraction.
    I = [[1, 0], [0, 1]]
    B = [[2, 3], [5, 7]]
    X = dense_solve(I, B, exact=True)
    assert X == [[Fraction(2), Fraction(3)], [Fraction(5), Fraction(7)]]


def test_dense_solve_exact_known():
    # 2x = 1 over the rationals → x = 1/2 exactly (never a float reciprocal).
    X = dense_solve([[2]], [[1]], exact=True)
    assert X == [[Fraction(1, 2)]]


def test_dense_solve_exact_pivot_swap():
    # First diagonal entry is zero — partial pivoting (exact: any nonzero
    # pivot) must swap rows. [[0,1],[1,0]] · X = [[1],[2]] → X = [[2],[1]].
    X = dense_solve([[0, 1], [1, 0]], [[1], [2]], exact=True)
    assert X == [[Fraction(2)], [Fraction(1)]]


def test_dense_solve_singular_raises_exact():
    with pytest.raises(ZeroDivisionError):
        dense_solve([[1, 1], [1, 1]], [[1], [2]], exact=True)


def test_dense_solve_rejects_non_square():
    with pytest.raises(ValueError):
        dense_solve([[1, 2, 3], [4, 5, 6]], [[1], [2]], exact=True)


# ── float path matches the exact-Fraction reference (always runs) ──────


def test_dense_solve_float_matches_exact():
    """The float solve (native C peer when attached, else pure-Python) equals
    the exact-Fraction Gauss–Jordan reference — numpy-free."""
    g = _lcg(20260606)
    for n in (1, 2, 5, 9):
        # Well-conditioned: diagonally-dominant rational matrix.
        A = [[Fraction(int(round(next(g) * 100)), 100) for _ in range(n)]
             for _ in range(n)]
        for i in range(n):
            A[i][i] += Fraction(n)
        B = [[Fraction(int(round(next(g) * 100)), 100) for _ in range(3)]
             for _ in range(n)]
        Af = [[float(x) for x in row] for row in A]
        Bf = [[float(x) for x in row] for row in B]
        got = dense_solve(Af, Bf)             # float path
        want = dense_solve(A, B, exact=True)  # exact oracle
        for i in range(n):
            for j in range(3):
                assert abs(got[i][j] - float(want[i][j])) < 1e-10


def test_dense_solve_vector_rhs_shape():
    """A 1-D RHS yields a flat list of the right length; values match exact."""
    A = [[3.0, 1.0], [1.0, 2.0]]
    b = [9.0, 8.0]
    x = dense_solve(A, b)
    assert isinstance(x, list) and len(x) == 2
    assert not isinstance(x[0], list)  # flat, not nested
    want = dense_solve([[Fraction(3), Fraction(1)], [Fraction(1), Fraction(2)]],
                       [Fraction(9), Fraction(8)], exact=True)
    for i in range(2):
        assert abs(x[i] - float(want[i])) < 1e-12


# ── native C peer parity (native-guarded) ─────────────────────────────


@_needs_c
def test_dense_solve_native_matches_exact():
    """The native ``srmech_dense_solve_f64`` path matches the exact-Fraction
    reference to float tolerance on SPD inputs — numpy-free."""
    g = _lcg(424242)
    for n in (2, 4, 8, 16):
        M = [[Fraction(int(round(next(g) * 50)), 50) for _ in range(n)]
             for _ in range(n)]
        # A = M·Mᵀ + n·I → SPD, well-conditioned (exact Fraction).
        MMt = _matmul(M, _transpose(M))
        A = [[MMt[i][j] + (Fraction(n) if i == j else Fraction(0))
              for j in range(n)] for i in range(n)]
        B = [[Fraction(int(round(next(g) * 50)), 50) for _ in range(2)]
             for _ in range(n)]
        Af = [[float(x) for x in row] for row in A]
        Bf = [[float(x) for x in row] for row in B]
        got = dense_solve(Af, Bf)             # native path
        want = dense_solve(A, B, exact=True)  # exact oracle
        for i in range(n):
            for j in range(2):
                assert abs(got[i][j] - float(want[i][j])) < 1e-9


@_needs_c
def test_schur_composes_over_native_dense_solve():
    # The float Schur path runs its interior solve through the native
    # dense_solve C peer; it must still reduce the path-4 Laplacian exactly
    # (verified against the exact (1/3)·[[1,-1],[-1,1]] reference; numpy-free).
    S = schur_complement(_PATH4_L, [0, 3])
    for i in range(2):
        for j in range(2):
            assert abs(S[i][j] - float(_EXPECTED_S[i][j])) < 1e-12
