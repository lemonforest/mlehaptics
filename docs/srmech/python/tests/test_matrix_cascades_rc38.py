"""rc38 — QR + SVD matrix factorizations as A-N cascades.

qr = Householder reflectors (Class M product of K-sign-flip o M-outer o N-scale);
svd = Gram-matrix hermitian_eigendecompose (Class L) o sqrt (Class N+K) o
A*V*Sigma^-1 (Class M).

QR/SVD are unique only up to signs, so U/V/Q/R need not match element-wise; the
DEFINING INVARIANTS do (reconstruction, orthonormality, upper-triangular R), and
the singular VALUES (unique) equal sqrt of the eigenvalues of the Gram matrix
``AᴴA``.

numpy-FREE (#564): numpy is GONE from srmech — ``qr``/``svd`` return plain Python
lists. Fixtures use stdlib ``random``; invariants are checked with plain-list
matrix arithmetic; the singular-value oracle is the framework's own
``hermitian_eigendecompose`` on the Gram matrix (no ``np.linalg.svd``).
"""
import cmath
import math
import random

import pytest

from srmech.amsc.cascade.matrix_cascades import qr, svd
from srmech.amsc.laplacian import hermitian_eigendecompose

_SHAPES = [(4, 4), (6, 3), (3, 6), (1, 1), (5, 2), (2, 5), (7, 7)]


# ── numpy-free list helpers ────────────────────────────────────────────


def _conjT(M):
    return [[complex(M[i][j]).conjugate() for i in range(len(M))]
            for j in range(len(M[0]))]


def _matmul(A, B):
    m, k, n = len(A), len(B), len(B[0])
    return [[sum(A[i][p] * B[p][j] for p in range(k)) for j in range(n)]
            for i in range(m)]


def _mag2(z):
    z = complex(z)
    return z.real * z.real + z.imag * z.imag


def _max_recon_err2(C, A):
    """max |C[i][j] - A[i][j]|² over the grid."""
    return max(_mag2(complex(C[i][j]) - complex(A[i][j]))
               for i in range(len(A)) for j in range(len(A[0])))


def _max_off_identity_err2(G):
    """max |G[i][j] - δ_ij|² (orthonormality residual)."""
    n = len(G)
    return max(_mag2(complex(G[i][j]) - (1.0 if i == j else 0.0))
               for i in range(n) for j in range(n))


def _mats(shape, rs):
    """A real and a complex matrix of the given shape (numpy-free)."""
    m, n = shape
    yield [[rs.gauss(0.0, 1.0) for _ in range(n)] for _ in range(m)]
    yield [[complex(rs.gauss(0.0, 1.0), rs.gauss(0.0, 1.0)) for _ in range(n)]
           for _ in range(m)]


def _gram_singular_values(A):
    """Reference singular values: sqrt of the (nonneg) eigenvalues of the
    smaller Gram matrix (AᴴA if n<=m else AAᴴ) via hermitian_eigendecompose."""
    m, n = len(A), len(A[0])
    Ah = _conjT(A)
    G = _matmul(Ah, A) if n <= m else _matmul(A, Ah)
    w, _ = hermitian_eigendecompose(G)
    # clamp tiny negatives from rounding (Class-K sign-branch, no abs()).
    return sorted((math.sqrt(x) if x > 0.0 else 0.0) for x in w)


def test_qr_invariants():
    rs = random.Random(101)
    for shape in _SHAPES:
        for A in _mats(shape, rs):
            Q, R = qr(A)
            m, n = shape
            k = min(m, n)
            assert len(Q) == m and len(Q[0]) == k, shape
            assert len(R) == k and len(R[0]) == n, shape
            # reconstruction Q·R ≈ A
            assert _max_recon_err2(_matmul(Q, R), A) <= 1e-18, ("recon", shape)
            # orthonormal Q: Qᴴ·Q ≈ I
            assert _max_off_identity_err2(_matmul(_conjT(Q), Q)) <= 1e-18, ("orth", shape)
            # R upper-triangular: strictly-lower entries ≈ 0
            for i in range(k):
                for j in range(i):
                    assert _mag2(R[i][j]) <= 1e-18, ("upper", shape)


def test_qr_complete_mode():
    rs = random.Random(102)
    A = [[rs.gauss(0.0, 1.0) for _ in range(3)] for _ in range(6)]
    Q, R = qr(A, mode="complete")
    assert len(Q) == 6 and len(Q[0]) == 6
    assert len(R) == 6 and len(R[0]) == 3
    assert _max_recon_err2(_matmul(Q, R), A) <= 1e-18
    assert _max_off_identity_err2(_matmul(_conjT(Q), Q)) <= 1e-18


def test_qr_invalid_mode():
    with pytest.raises(ValueError):
        qr([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], mode="banana")


def test_svd_invariants_and_singular_values():
    rs = random.Random(103)
    for shape in _SHAPES:
        for A in _mats(shape, rs):
            U, s, Vh = svd(A)
            m, n = shape
            k = min(m, n)
            assert len(U) == m and len(U[0]) == k, shape
            assert len(s) == k, shape
            assert len(Vh) == k and len(Vh[0]) == n, shape
            # descending, non-negative
            for i in range(k - 1):
                assert s[i] - s[i + 1] >= -1e-12, ("descending", shape)
            assert all(v >= -1e-12 for v in s), ("nonneg", shape)
            # reconstruction U·diag(s)·Vh ≈ A
            Us = [[U[i][p] * s[p] for p in range(k)] for i in range(m)]
            assert _max_recon_err2(_matmul(Us, Vh), A) <= 1e-16, ("recon", shape)
            # U columns orthonormal: Uᴴ·U ≈ I
            assert _max_off_identity_err2(_matmul(_conjT(U), U)) <= 1e-16, ("U-orth", shape)
            # V rows orthonormal: Vh·Vhᴴ ≈ I
            assert _max_off_identity_err2(_matmul(Vh, _conjT(Vh))) <= 1e-16, ("V-orth", shape)
            # singular VALUES are unique → match the Gram-eigenvalue oracle.
            s_ref = _gram_singular_values(A)
            for a, b in zip(sorted(s), s_ref):
                assert (a - b) ** 2 <= 1e-16, ("sval", shape)


def test_svd_empty():
    """An empty input returns three empty lists (numpy-free)."""
    U, s, Vh = svd([])
    assert U == [] and s == [] and Vh == []


def test_svd_full_matrices_not_implemented():
    with pytest.raises(NotImplementedError):
        svd([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]], full_matrices=True)


def test_matrix_cascades_no_abs_no_nplinalg():
    """No abs() (discipline) and NO np.linalg.qr/svd (the engine we replace)."""
    import ast
    import inspect

    from srmech.amsc.cascade import matrix_cascades as mc

    src = inspect.getsource(mc)
    tree = ast.parse(src)
    bad_abs = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "abs"
    ]
    assert not bad_abs, "abs() is never fine — use hypot / real-imag / sign-branch"
    # No np.linalg.{qr,svd} attribute access in the call graph.
    forbidden = {"qr", "svd", "eig", "eigh", "lstsq"}
    leaks = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in forbidden:
            base = node.value
            if isinstance(base, ast.Attribute) and base.attr == "linalg":
                leaks.add(f"np.linalg.{node.attr}")
    assert not leaks, f"matrix_cascades must not call the numpy engine: {leaks}"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
