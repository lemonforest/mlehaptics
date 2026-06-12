"""Parity tests for Class L — graph Laplacian operations.

Tests the four public operations (``dense_adjacency``,
``dense_laplacian``, ``normalized_laplacian``, ``jacobi_eigvals``)
against hand-computed reference values. When
``srmech.amsc._native.HAS_NATIVE`` is ``True``, the native ↔ fallback
parity sweep runs (toggling the flag to force the pure-Python fallback
path and comparing outputs to ~1e-12 tolerance).

Post-#564 numpy is GONE from srmech: the build ops return
``list[list[float]]`` and ``jacobi_eigvals`` returns ``list[float]``
(ascending). Reference values are hand-computed or supplied by srmech's
OWN pure-Python Jacobi cascade — never numpy LAPACK.
"""

from __future__ import annotations

import math
import random

import pytest

from srmech.amsc import _native, laplacian


# ---------------------------------------------------------------------
# plain-list helpers (no numpy)
# ---------------------------------------------------------------------

def _assert_matrix_equal(M, expected, tol=0.0):
    assert len(M) == len(expected)
    for i in range(len(expected)):
        assert len(M[i]) == len(expected[i])
        for j in range(len(expected[i])):
            if tol:
                assert abs(M[i][j] - expected[i][j]) <= tol
            else:
                assert M[i][j] == expected[i][j]


def _transpose(M):
    return [[M[j][i] for j in range(len(M))] for i in range(len(M[0]))] if M else []


def _is_symmetric(M, tol=1e-12):
    n = len(M)
    return all(abs(M[i][j] - M[j][i]) <= tol for i in range(n) for j in range(n))


def _random_symmetric(n, rng):
    A = [[rng.gauss(0.0, 1.0) for _ in range(n)] for _ in range(n)]
    return [[(A[i][j] + A[j][i]) / 2.0 for j in range(n)] for i in range(n)]


def _random_edges(n, m, rng):
    return [(rng.randrange(n), rng.randrange(n)) for _ in range(m)]


# ---------------------------------------------------------------------
# dense_adjacency — reference + edge cases
# ---------------------------------------------------------------------

def test_adjacency_empty_graph():
    A = laplacian.dense_adjacency(5, [])
    assert len(A) == 5 and all(len(row) == 5 for row in A)
    _assert_matrix_equal(A, [[0.0] * 5 for _ in range(5)])


def test_adjacency_triangle():
    # 3-cycle: 0-1, 1-2, 2-0
    A = laplacian.dense_adjacency(3, [(0, 1), (1, 2), (2, 0)])
    expected = [
        [0, 1, 1],
        [1, 0, 1],
        [1, 1, 0],
    ]
    _assert_matrix_equal(A, expected)


def test_adjacency_weighted():
    A = laplacian.dense_adjacency(3, [(0, 1), (1, 2)], weights=[2.5, 3.5])
    expected = [
        [0.0, 2.5, 0.0],
        [2.5, 0.0, 3.5],
        [0.0, 3.5, 0.0],
    ]
    _assert_matrix_equal(A, expected)


def test_adjacency_self_loop_adds_2w_to_diagonal():
    A = laplacian.dense_adjacency(2, [(0, 0), (0, 1)])
    expected = [[2.0, 1.0], [1.0, 0.0]]
    _assert_matrix_equal(A, expected)


def test_adjacency_out_of_range_rejected():
    with pytest.raises(ValueError):
        laplacian.dense_adjacency(3, [(0, 5)])


# ---------------------------------------------------------------------
# dense_laplacian — reference + spectral properties
# ---------------------------------------------------------------------

def test_laplacian_triangle():
    L = laplacian.dense_laplacian(3, [(0, 1), (1, 2), (2, 0)])
    expected = [
        [2, -1, -1],
        [-1, 2, -1],
        [-1, -1, 2],
    ]
    _assert_matrix_equal(L, expected)


def test_laplacian_path_graph():
    # Path 0-1-2-3 has degree sequence [1, 2, 2, 1]
    L = laplacian.dense_laplacian(4, [(0, 1), (1, 2), (2, 3)])
    expected = [
        [1, -1, 0, 0],
        [-1, 2, -1, 0],
        [0, -1, 2, -1],
        [0, 0, -1, 1],
    ]
    _assert_matrix_equal(L, expected, tol=0.0)


def test_laplacian_is_symmetric_positive_semidefinite():
    rng = random.Random(20260515)
    for _ in range(20):
        n = rng.randint(3, 31)
        m = rng.randint(n - 1, n * (n - 1) // 2 + 1)
        edges = _random_edges(n, m, rng)
        L = laplacian.dense_laplacian(n, edges)
        assert _is_symmetric(L, tol=1e-12)
        # PSD via srmech's OWN Jacobi cascade (not numpy LAPACK).
        eigs = laplacian.jacobi_eigvals(L)
        assert min(eigs) >= -1e-9


def test_laplacian_row_sums_zero():
    L = laplacian.dense_laplacian(5, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)])
    for row in L:
        assert abs(sum(row)) < 1e-12


# ---------------------------------------------------------------------
# normalized_laplacian — reference + spectral properties
# ---------------------------------------------------------------------

def test_normalized_laplacian_triangle():
    Lsym = laplacian.normalized_laplacian(3, [(0, 1), (1, 2), (2, 0)])
    # Triangle: each vertex has degree 2; d_inv_sqrt = 1/sqrt(2)
    off = -1.0 / 2.0  # -1 * (1/sqrt(2)) * (1/sqrt(2)) = -1/2
    expected = [
        [1.0, off, off],
        [off, 1.0, off],
        [off, off, 1.0],
    ]
    _assert_matrix_equal(Lsym, expected, tol=1e-12)


def test_normalized_laplacian_isolated_vertex_zero_diagonal():
    # 2 nodes, edge (0,1); vertex 2 isolated
    Lsym = laplacian.normalized_laplacian(3, [(0, 1)])
    # Node 2 has degree 0; L_sym[2,2] should be 0
    assert Lsym[2][2] == 0.0


def test_normalized_laplacian_eigvals_in_0_2():
    rng = random.Random(20260516)
    for _ in range(20):
        n = rng.randint(3, 19)
        m = rng.randint(n - 1, n * (n - 1) // 2 + 1)
        edges = _random_edges(n, m, rng)
        # Drop self-loops for the symmetric-eigval bound to hold
        edges = [(u, v) for (u, v) in edges if u != v]
        if not edges:
            continue
        Lsym = laplacian.normalized_laplacian(n, edges)
        eigs = laplacian.jacobi_eigvals(Lsym)   # srmech's own cascade
        # Normalised Laplacian eigvals lie in [0, 2] (graph theory).
        assert min(eigs) >= -1e-9, f"min eig {min(eigs)} < 0"
        assert max(eigs) <= 2.0 + 1e-9, f"max eig {max(eigs)} > 2"


# ---------------------------------------------------------------------
# jacobi_eigvals — closed-form spectra + cascade cross-check
# ---------------------------------------------------------------------

def test_jacobi_eigvals_diagonal():
    M = [[1.0, 0.0, 0.0], [0.0, 2.0, 0.0], [0.0, 0.0, 3.0]]
    eigs = laplacian.jacobi_eigvals(M)
    for got, exp in zip(eigs, [1.0, 2.0, 3.0]):
        assert abs(got - exp) < 1e-12


def test_jacobi_eigvals_2x2():
    M = [[2.0, 1.0], [1.0, 2.0]]
    eigs = laplacian.jacobi_eigvals(M)
    # Closed form: 1, 3
    for got, exp in zip(eigs, [1.0, 3.0]):
        assert abs(got - exp) < 1e-12


def test_jacobi_eigvals_matches_cascade_random_sweep():
    """The (native) jacobi path agrees with srmech's OWN pure-Python Jacobi
    cascade across random symmetric matrices — the native ↔ cascade parity."""
    rng = random.Random(20260517)
    for _ in range(15):
        n = rng.randint(3, 23)
        M = _random_symmetric(n, rng)
        eigs_main = laplacian.jacobi_eigvals(M, max_sweeps=100, tolerance=1e-12)
        eigs_cascade = sorted(laplacian._jacobi_eigvals_py([row[:] for row in M]))
        for a, b in zip(sorted(eigs_main), eigs_cascade):
            assert abs(a - b) < 1e-9


def test_jacobi_eigvals_on_laplacian():
    L = laplacian.dense_laplacian(4, [(0, 1), (1, 2), (2, 3), (3, 0)])
    eigs = laplacian.jacobi_eigvals(L)
    # 4-cycle Laplacian eigvals: 0, 2, 2, 4 (closed-form algebraic)
    for got, exp in zip(sorted(eigs), [0.0, 2.0, 2.0, 4.0]):
        assert abs(got - exp) < 1e-9


def test_jacobi_eigvals_does_not_mutate_input():
    M = [[2.0, 1.0], [1.0, 3.0]]
    M_copy = [row[:] for row in M]
    _ = laplacian.jacobi_eigvals(M)
    assert M == M_copy


# ---------------------------------------------------------------------
# C ↔ Python parity (requires HAS_NATIVE)
# ---------------------------------------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_native_dense_adjacency_matches_fallback():
    rng = random.Random(20260518)
    saved = _native.HAS_NATIVE
    try:
        for _ in range(20):
            n = rng.randint(3, 31)
            m = rng.randint(n, n * (n - 1) // 2 + 1)
            edges = _random_edges(n, m, rng)
            ws = [rng.uniform(0.5, 2.0) for _ in range(m)]

            _native.HAS_NATIVE = True
            A_native = laplacian.dense_adjacency(n, edges, ws)
            _native.HAS_NATIVE = False
            A_fallback = laplacian.dense_adjacency(n, edges, ws)
            _assert_matrix_equal(A_native, A_fallback, tol=1e-12)
    finally:
        _native.HAS_NATIVE = saved


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_native_dense_laplacian_matches_fallback():
    rng = random.Random(20260519)
    saved = _native.HAS_NATIVE
    try:
        for _ in range(15):
            n = rng.randint(3, 31)
            m = rng.randint(n, n * (n - 1) // 2 + 1)
            edges = _random_edges(n, m, rng)

            _native.HAS_NATIVE = True
            L_native = laplacian.dense_laplacian(n, edges)
            _native.HAS_NATIVE = False
            L_fallback = laplacian.dense_laplacian(n, edges)
            _assert_matrix_equal(L_native, L_fallback, tol=1e-12)
    finally:
        _native.HAS_NATIVE = saved


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_native_jacobi_matches_fallback():
    rng = random.Random(20260520)
    saved = _native.HAS_NATIVE
    try:
        for _ in range(10):
            n = rng.randint(3, 23)
            M = _random_symmetric(n, rng)

            _native.HAS_NATIVE = True
            eigs_native = laplacian.jacobi_eigvals(M, max_sweeps=100, tolerance=1e-12)
            _native.HAS_NATIVE = False
            eigs_fallback = laplacian.jacobi_eigvals(M)
            for a, b in zip(sorted(eigs_native), sorted(eigs_fallback)):
                assert abs(a - b) < 1e-9
    finally:
        _native.HAS_NATIVE = saved


def test_jacobi_eigvals_large_n_falls_back():
    # n > MAX_NATIVE_NODES forces the pure-Python cascade even when HAS_NATIVE.
    # Use a diagonal matrix so the closed-form spectrum is its sorted diagonal.
    n = laplacian.MAX_NATIVE_NODES + 1
    rng = random.Random(20260521)
    diag = [rng.uniform(-5.0, 5.0) for _ in range(n)]
    M = [[diag[i] if i == j else 0.0 for j in range(n)] for i in range(n)]
    eigs = laplacian.jacobi_eigvals(M)
    expected = sorted(diag)
    for a, b in zip(sorted(eigs), expected):
        assert abs(a - b) < 1e-9
