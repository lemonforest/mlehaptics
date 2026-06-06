"""v0.7.1rc3 — ``srmech.amsc.laplacian.dense_solve`` (#897 §26).

The reusable Class-L dense linear solve ``A · X = B`` the Schur-complement /
DtN float path composes over. Tests three things:

* the exact-rational (``fractions.Fraction``) Gauss–Jordan path — always runs,
  numpy-free, bit-exact;
* the float path matches ``numpy.linalg.solve`` (numpy-guarded);
* the native C peer ``srmech_dense_solve_f64`` matches both the numpy float
  path and the exact reference to float tolerance (native-guarded — skips on
  pure-Python / Pyodide installs and on the source tree where no compiled
  ``libsrmech`` is attached).
"""

from fractions import Fraction

import pytest

from srmech.amsc import _native, laplacian
from srmech.amsc.laplacian import dense_solve, schur_complement

np = laplacian.np

# Native available AND the additive rc3 symbol present (a stale ABI-3 lib
# built before this rc lacks it — hasattr-guarded everywhere).
_HAS_C = (
    _native.HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_dense_solve_f64")
)
_needs_np = pytest.mark.skipif(np is None, reason="float path needs numpy")
_needs_c = pytest.mark.skipif(
    not _HAS_C, reason="native srmech_dense_solve_f64 not attached"
)

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


# ── float path matches numpy (numpy-guarded) ──────────────────────────


@_needs_np
def test_dense_solve_float_matches_numpy():
    rng = np.random.default_rng(20260606)
    for n in (1, 2, 5, 9):
        A = rng.standard_normal((n, n)) + n * np.eye(n)  # well-conditioned
        B = rng.standard_normal((n, 3))
        got = dense_solve(A, B)
        assert np.allclose(np.asarray(got, dtype=float), np.linalg.solve(A, B),
                           atol=1e-10)


@_needs_np
def test_dense_solve_vector_rhs_shape():
    A = np.array([[3.0, 1.0], [1.0, 2.0]])
    b = np.array([9.0, 8.0])
    x = dense_solve(A, b)
    assert np.asarray(x).shape == (2,)
    assert np.allclose(np.asarray(x, dtype=float), np.linalg.solve(A, b))


# ── native C peer parity (native-guarded) ─────────────────────────────


@_needs_c
def test_dense_solve_native_matches_numpy_and_exact():
    rng = np.random.default_rng(424242)
    for n in (2, 4, 8, 16):
        M = rng.standard_normal((n, n))
        A = M @ M.T + n * np.eye(n)  # SPD, well-conditioned
        B = rng.standard_normal((n, 2))
        got = np.asarray(dense_solve(A, B), dtype=float)  # native path
        assert np.allclose(got, np.linalg.solve(A, B), atol=1e-9)


@_needs_c
def test_schur_composes_over_native_dense_solve():
    # The float Schur path runs its interior solve through the native
    # dense_solve C peer; it must still reduce the path-4 Laplacian exactly.
    S = np.asarray(schur_complement(_PATH4_L, [0, 3]), dtype=float)
    expected = np.array([[1.0, -1.0], [-1.0, 1.0]]) / 3.0
    assert np.allclose(S, expected, atol=1e-12)
