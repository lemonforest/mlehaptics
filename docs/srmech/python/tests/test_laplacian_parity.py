"""Parity tests for Class L — graph Laplacian operations.

Tests the four public operations (``dense_adjacency``,
``dense_laplacian``, ``normalized_laplacian``, ``jacobi_eigvals``)
against reference values and numpy-equivalence. When
``srmech.amsc._native.HAS_NATIVE`` is ``True``, the native ↔ fallback
parity sweep runs (toggling the flag to force the fallback path and
comparing outputs to ~1e-12 tolerance).
"""

from __future__ import annotations

import numpy as np
import pytest

from srmech.amsc import _native, laplacian


# ---------------------------------------------------------------------
# dense_adjacency — reference + edge cases
# ---------------------------------------------------------------------

def test_adjacency_empty_graph():
    A = laplacian.dense_adjacency(5, [])
    assert A.shape == (5, 5)
    np.testing.assert_array_equal(A, np.zeros((5, 5)))


def test_adjacency_triangle():
    # 3-cycle: 0-1, 1-2, 2-0
    A = laplacian.dense_adjacency(3, [(0, 1), (1, 2), (2, 0)])
    expected = np.array([
        [0, 1, 1],
        [1, 0, 1],
        [1, 1, 0],
    ], dtype=np.float64)
    np.testing.assert_array_equal(A, expected)


def test_adjacency_weighted():
    A = laplacian.dense_adjacency(3, [(0, 1), (1, 2)], weights=[2.5, 3.5])
    expected = np.array([
        [0.0, 2.5, 0.0],
        [2.5, 0.0, 3.5],
        [0.0, 3.5, 0.0],
    ])
    np.testing.assert_array_equal(A, expected)


def test_adjacency_self_loop_adds_2w_to_diagonal():
    A = laplacian.dense_adjacency(2, [(0, 0), (0, 1)])
    expected = np.array([[2.0, 1.0], [1.0, 0.0]])
    np.testing.assert_array_equal(A, expected)


def test_adjacency_out_of_range_rejected():
    with pytest.raises(ValueError):
        laplacian.dense_adjacency(3, [(0, 5)])


# ---------------------------------------------------------------------
# dense_laplacian — reference + spectral properties
# ---------------------------------------------------------------------

def test_laplacian_triangle():
    L = laplacian.dense_laplacian(3, [(0, 1), (1, 2), (2, 0)])
    expected = np.array([
        [ 2, -1, -1],
        [-1,  2, -1],
        [-1, -1,  2],
    ], dtype=np.float64)
    np.testing.assert_array_equal(L, expected)


def test_laplacian_path_graph():
    # Path 0-1-2-3 has degree sequence [1, 2, 2, 1]
    L = laplacian.dense_laplacian(4, [(0, 1), (1, 2), (2, 3)])
    expected = np.array([
        [ 1, -1,  0,  0],
        [-1,  2, -1,  0],
        [ 0, -1,  2, -1],
        [ 0,  0, -1,  1],
    ], dtype=np.float64)
    np.testing.assert_array_equal(L, expected)


def test_laplacian_is_symmetric_positive_semidefinite():
    rng = np.random.default_rng(20260515)
    for trial in range(20):
        n = int(rng.integers(3, 32))
        m = int(rng.integers(n - 1, n * (n - 1) // 2 + 1))
        edges = [
            (int(rng.integers(0, n)), int(rng.integers(0, n)))
            for _ in range(m)
        ]
        L = laplacian.dense_laplacian(n, edges)
        np.testing.assert_allclose(L, L.T, atol=1e-12)
        eigs = np.linalg.eigvalsh(L)
        # Smallest eigenvalue should be >= -1e-10 (PSD with float noise).
        assert eigs.min() >= -1e-10


def test_laplacian_row_sums_zero():
    L = laplacian.dense_laplacian(5, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)])
    np.testing.assert_allclose(L.sum(axis=1), np.zeros(5), atol=1e-12)


# ---------------------------------------------------------------------
# normalized_laplacian — reference + spectral properties
# ---------------------------------------------------------------------

def test_normalized_laplacian_triangle():
    Lsym = laplacian.normalized_laplacian(3, [(0, 1), (1, 2), (2, 0)])
    # Triangle: each vertex has degree 2; d_inv_sqrt = 1/sqrt(2)
    off = -1.0 / 2.0  # -1 * (1/sqrt(2)) * (1/sqrt(2)) = -1/2
    expected = np.array([
        [1.0, off, off],
        [off, 1.0, off],
        [off, off, 1.0],
    ])
    np.testing.assert_allclose(Lsym, expected, atol=1e-12)


def test_normalized_laplacian_isolated_vertex_zero_diagonal():
    # 2 nodes, edge (0,1); vertex 2 isolated
    Lsym = laplacian.normalized_laplacian(3, [(0, 1)])
    # Node 2 has degree 0; L_sym[2,2] should be 0
    assert Lsym[2, 2] == 0.0


def test_normalized_laplacian_eigvals_in_0_2():
    rng = np.random.default_rng(20260516)
    for _ in range(20):
        n = int(rng.integers(3, 20))
        m = int(rng.integers(n - 1, n * (n - 1) // 2 + 1))
        edges = [
            (int(rng.integers(0, n)), int(rng.integers(0, n)))
            for _ in range(m)
        ]
        # Drop self-loops for the symmetric-eigval bound to hold
        edges = [(u, v) for (u, v) in edges if u != v]
        if not edges:
            continue
        Lsym = laplacian.normalized_laplacian(n, edges)
        eigs = np.linalg.eigvalsh(Lsym)
        # Normalised Laplacian eigvals lie in [0, 2] (graph theory).
        assert eigs.min() >= -1e-10, f"min eig {eigs.min()} < 0"
        assert eigs.max() <= 2.0 + 1e-10, f"max eig {eigs.max()} > 2"


# ---------------------------------------------------------------------
# jacobi_eigvals — agreement with numpy.linalg.eigvalsh
# ---------------------------------------------------------------------

def test_jacobi_eigvals_diagonal():
    M = np.diag([1.0, 2.0, 3.0])
    eigs = laplacian.jacobi_eigvals(M)
    np.testing.assert_allclose(eigs, [1.0, 2.0, 3.0], atol=1e-12)


def test_jacobi_eigvals_2x2():
    M = np.array([[2.0, 1.0], [1.0, 2.0]])
    eigs = laplacian.jacobi_eigvals(M)
    # Closed form: 1, 3
    np.testing.assert_allclose(eigs, [1.0, 3.0], atol=1e-12)


def test_jacobi_eigvals_matches_numpy_random_sweep():
    rng = np.random.default_rng(20260517)
    for trial in range(15):
        n = int(rng.integers(3, 24))
        # Random symmetric matrix
        M = rng.standard_normal((n, n))
        M = (M + M.T) / 2
        eigs_jacobi = laplacian.jacobi_eigvals(M, max_sweeps=100, tolerance=1e-12)
        eigs_numpy = np.sort(np.linalg.eigvalsh(M))
        np.testing.assert_allclose(eigs_jacobi, eigs_numpy, atol=1e-10)


def test_jacobi_eigvals_on_laplacian():
    L = laplacian.dense_laplacian(4, [(0, 1), (1, 2), (2, 3), (3, 0)])
    eigs = laplacian.jacobi_eigvals(L)
    # 4-cycle Laplacian eigvals: 0, 2, 2, 4 (closed-form algebraic)
    np.testing.assert_allclose(eigs, [0.0, 2.0, 2.0, 4.0], atol=1e-10)


def test_jacobi_eigvals_does_not_mutate_input():
    M = np.array([[2.0, 1.0], [1.0, 3.0]])
    M_copy = M.copy()
    _ = laplacian.jacobi_eigvals(M)
    np.testing.assert_array_equal(M, M_copy)


# ---------------------------------------------------------------------
# C ↔ Python parity (requires HAS_NATIVE)
# ---------------------------------------------------------------------

@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_native_dense_adjacency_matches_fallback():
    rng = np.random.default_rng(20260518)
    saved = _native.HAS_NATIVE
    try:
        for _ in range(20):
            n = int(rng.integers(3, 32))
            m = int(rng.integers(n, n * (n - 1) // 2 + 1))
            edges = [
                (int(rng.integers(0, n)), int(rng.integers(0, n)))
                for _ in range(m)
            ]
            ws = rng.uniform(0.5, 2.0, size=m).tolist()

            _native.HAS_NATIVE = True
            A_native = laplacian.dense_adjacency(n, edges, ws)
            _native.HAS_NATIVE = False
            A_fallback = laplacian.dense_adjacency(n, edges, ws)
            np.testing.assert_allclose(A_native, A_fallback, atol=1e-12)
    finally:
        _native.HAS_NATIVE = saved


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_native_dense_laplacian_matches_fallback():
    rng = np.random.default_rng(20260519)
    saved = _native.HAS_NATIVE
    try:
        for _ in range(15):
            n = int(rng.integers(3, 32))
            m = int(rng.integers(n, n * (n - 1) // 2 + 1))
            edges = [
                (int(rng.integers(0, n)), int(rng.integers(0, n)))
                for _ in range(m)
            ]

            _native.HAS_NATIVE = True
            L_native = laplacian.dense_laplacian(n, edges)
            _native.HAS_NATIVE = False
            L_fallback = laplacian.dense_laplacian(n, edges)
            np.testing.assert_allclose(L_native, L_fallback, atol=1e-12)
    finally:
        _native.HAS_NATIVE = saved


@pytest.mark.skipif(not _native.HAS_NATIVE, reason="native lib not loaded")
def test_native_jacobi_matches_fallback():
    rng = np.random.default_rng(20260520)
    saved = _native.HAS_NATIVE
    try:
        for _ in range(10):
            n = int(rng.integers(3, 24))
            M = rng.standard_normal((n, n))
            M = (M + M.T) / 2

            _native.HAS_NATIVE = True
            eigs_native = laplacian.jacobi_eigvals(M, max_sweeps=100, tolerance=1e-12)
            _native.HAS_NATIVE = False
            eigs_fallback = laplacian.jacobi_eigvals(M)
            np.testing.assert_allclose(eigs_native, eigs_fallback, atol=1e-10)
    finally:
        _native.HAS_NATIVE = saved


def test_jacobi_eigvals_large_n_falls_back():
    # n > MAX_NATIVE_NODES forces numpy fallback even when HAS_NATIVE
    n = laplacian.MAX_NATIVE_NODES + 1
    rng = np.random.default_rng(20260521)
    M = rng.standard_normal((n, n))
    M = (M + M.T) / 2
    eigs = laplacian.jacobi_eigvals(M)
    eigs_ref = np.sort(np.linalg.eigvalsh(M))
    np.testing.assert_allclose(eigs, eigs_ref, atol=1e-10)
