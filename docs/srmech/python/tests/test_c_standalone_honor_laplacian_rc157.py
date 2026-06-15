"""rc157 — C standalone-complete honor: the Class-L node caps are GONE.

`srmech_laplacian.c` carried `SRMECH_LAPLACIAN_MAX_NODES 256` on four ops, none
of which actually needs scratch:

  * dense_laplacian   — `degree[256]` eliminated (L = D−A is row-local).
  * normalized_laplacian — `d_inv_sqrt[256]` eliminated (d^(−1/2) stashed in the
    diagonal, which L_sym overwrites anyway).
  * jacobi_eigvals    — rotates the caller's matrix IN PLACE (no scratch).
  * dense_matmul_complex — writes the caller's output buffer (no scratch).

rc157 lifts all four C caps and drops the Python `_can_dispatch_native` /
`mat_matmul` bounds-gate, so the bound is the caller's RAM. This proves it at
n = 300 > 256 (the old cap), native vs the pure-Python alternative.

Per [[feedback_c_must_be_standalone_complete_no_python_fallback]]. numpy-free.
"""

from srmech.amsc import _native
from srmech.amsc import laplacian as L
from srmech.amsc.mat import Mat


def _mat_equal(a, b, tol=0.0):
    if a.shape != b.shape:
        return False
    nr, nc = a.shape
    for i in range(nr):
        for j in range(nc):
            d = a[i, j] - b[i, j]
            if (d if d >= 0 else -d) > tol:
                return False
    return True


def _ring_edges(n):
    # A simple connected weighted ring + a few chords — deterministic, n>256.
    edges = [(i, (i + 1) % n) for i in range(n)]
    edges += [(i, (i + 7) % n) for i in range(0, n, 3)]
    weights = [1.0 + (i % 5) for i in range(len(edges))]
    return edges, weights


def _force_pure(fn):
    saved = _native.HAS_NATIVE
    try:
        _native.HAS_NATIVE = False
        return fn()
    finally:
        _native.HAS_NATIVE = saved


def test_dense_laplacian_over_old_cap_native_matches_pure():
    n = 300                                    # > old 256 cap
    edges, w = _ring_edges(n)
    native = L.dense_laplacian(n, edges, w)    # native when present
    pure = _force_pure(lambda: L.dense_laplacian(n, edges, w))
    assert native.shape == (n, n)
    assert _mat_equal(native, pure, tol=0.0)   # integer-ish weights → exact


def test_normalized_laplacian_over_old_cap_native_matches_pure():
    n = 300
    edges, w = _ring_edges(n)
    native = L.normalized_laplacian(n, edges, w)
    pure = _force_pure(lambda: L.normalized_laplacian(n, edges, w))
    assert native.shape == (n, n)
    assert _mat_equal(native, pure, tol=1e-9)  # float d^(−1/2); same cascade both sides


def test_jacobi_eigvals_over_old_cap_accepts_and_is_correct():
    # n = 300 honor + correctness: a diagonal matrix's eigenvalues are its
    # diagonal (Jacobi makes no rotation). Proves the C accepts n > 256.
    n = 300
    diag = [float(i + 1) for i in range(n)]
    rows = [[diag[i] if i == j else 0.0 for j in range(n)] for i in range(n)]
    ev = L.jacobi_eigvals(rows)
    got = sorted(float(ev[i]) for i in range(n))
    assert got == sorted(diag)

    # Algorithm parity at a feasible n (pure Jacobi is O(n³)): native == pure.
    m = 72
    rows2 = [[1.0 / (1 + abs(i - j)) for j in range(m)] for i in range(m)]
    nat = L.jacobi_eigvals(rows2)
    pur = _force_pure(lambda: L.jacobi_eigvals(rows2))
    for i in range(m):
        d = float(nat[i]) - float(pur[i])
        assert (d if d >= 0 else -d) < 1e-7


def test_mat_matmul_over_old_cap_accepts_and_is_correct():
    # n = 300 honor + correctness: A · I == A. Proves the C kernel accepts dims
    # > 256 (it writes only the caller's output buffer).
    n = 300
    a_rows = [[float((i * 3 + j) % 11) for j in range(n)] for i in range(n)]
    ident = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    A = Mat.from_rows(a_rows, is_complex=False)
    I = Mat.from_rows(ident, is_complex=False)
    prod = L.mat_matmul(A, I)
    assert _mat_equal(prod, A, tol=1e-9)

    # Algorithm parity at a feasible n: native == pure.
    m = 96
    ar = [[float((i + 2 * j) % 7) for j in range(m)] for i in range(m)]
    br = [[float((3 * i + j) % 5) for j in range(m)] for i in range(m)]
    Am, Bm = Mat.from_rows(ar, is_complex=False), Mat.from_rows(br, is_complex=False)
    nat = L.mat_matmul(Am, Bm)
    pur = _force_pure(lambda: L.mat_matmul(Am, Bm))
    assert _mat_equal(nat, pur, tol=1e-9)
