"""rc38 — QR + SVD matrix factorizations as A-N cascades.

qr = Householder reflectors (Class M product of K-sign-flip o M-outer o N-scale);
svd = Gram-matrix hermitian_eigendecompose (Class L) o sqrt (Class N+K) o
A*V*Sigma^-1 (Class M). numpy as CONTAINER only — no np.linalg.qr/svd.

QR/SVD are unique only up to signs, so U/V/Q/R need not match numpy element-
wise; the DEFINING INVARIANTS do (reconstruction, orthonormality, upper-
triangular R), and the singular VALUES (unique) match numpy.linalg.svd.
"""
import numpy as np
import pytest

from srmech.amsc.cascade.matrix_cascades import qr, svd

_SHAPES = [(4, 4), (6, 3), (3, 6), (1, 1), (5, 2), (2, 5), (7, 7)]


def _mats(shape, rng):
    """A real and a complex matrix of the given shape."""
    yield rng.standard_normal(shape)
    yield rng.standard_normal(shape) + 1j * rng.standard_normal(shape)


def test_qr_invariants():
    rng = np.random.default_rng(101)
    for shape in _SHAPES:
        for A in _mats(shape, rng):
            Q, R = qr(A)
            m, n = A.shape
            k = min(m, n)
            assert Q.shape == (m, k) and R.shape == (k, n), shape
            assert np.max(np.abs(Q @ R - A)) <= 1e-9, ("recon", shape)
            assert np.max(np.abs(np.conj(Q.T) @ Q - np.eye(k))) <= 1e-9, ("orth", shape)
            if R.size:
                assert np.max(np.abs(np.tril(R, -1))) <= 1e-9, ("upper", shape)


def test_qr_complete_mode():
    rng = np.random.default_rng(102)
    A = rng.standard_normal((6, 3))
    Q, R = qr(A, mode="complete")
    assert Q.shape == (6, 6) and R.shape == (6, 3)
    assert np.max(np.abs(Q @ R - A)) <= 1e-9
    assert np.max(np.abs(Q.T @ Q - np.eye(6))) <= 1e-9


def test_qr_invalid_mode():
    with pytest.raises(ValueError):
        qr(np.eye(3), mode="banana")


def test_svd_invariants_and_singular_values():
    rng = np.random.default_rng(103)
    for shape in _SHAPES:
        for A in _mats(shape, rng):
            U, s, Vh = svd(A)
            m, n = A.shape
            k = min(m, n)
            assert U.shape == (m, k) and s.shape == (k,) and Vh.shape == (k, n), shape
            # descending
            assert np.all(np.diff(s) <= 1e-12), ("descending", shape)
            assert np.max(np.abs(U @ np.diag(s) @ Vh - A)) <= 1e-8, ("recon", shape)
            assert np.max(np.abs(np.conj(U.T) @ U - np.eye(k))) <= 1e-8, ("U-orth", shape)
            assert np.max(np.abs(Vh @ np.conj(Vh.T) - np.eye(k))) <= 1e-8, ("V-orth", shape)
            # singular VALUES are unique → match numpy
            s_np = np.linalg.svd(A, compute_uv=False)
            assert np.max(np.abs(s - s_np)) <= 1e-8, ("sval", shape)


def test_svd_empty():
    U, s, Vh = svd(np.zeros((0, 3)))
    assert U.shape == (0, 0) and s.shape == (0,) and Vh.shape == (0, 3)


def test_svd_full_matrices_not_implemented():
    with pytest.raises(NotImplementedError):
        svd(np.eye(3), full_matrices=True)


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
