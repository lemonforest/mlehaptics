"""rc39 — lstsq + einsum + non-Hermitian eig as A-N cascades.

lstsq = {QR} o Class M (Qᴴ b) o Class I (back-substitution);
einsum = Class B/D (spec) o Class I (index iteration) o Class M (sum-of-products);
eigvals = Class K (iterate) o Class L o {QR} o Class C (shifted-QR iteration).
numpy as CONTAINER only — no np.linalg.{lstsq,eig,eigvals}.
"""
import numpy as np
import pytest

from srmech.amsc.cascade.matrix_cascades import eigvals, einsum, lstsq


def test_lstsq_overdetermined_and_square():
    rng = np.random.default_rng(201)
    for shape in [(6, 3), (8, 4), (5, 5), (10, 1)]:
        for cplx in (False, True):
            A = rng.standard_normal(shape)
            b = rng.standard_normal(shape[0])
            if cplx:
                A = A + 1j * rng.standard_normal(shape)
                b = b + 1j * rng.standard_normal(shape[0])
            x = lstsq(A, b)
            x_np = np.linalg.lstsq(A, b, rcond=None)[0]
            assert np.max(np.abs(x - x_np)) <= 1e-9, (shape, cplx)


def test_lstsq_multiple_rhs():
    rng = np.random.default_rng(202)
    A = rng.standard_normal((7, 3))
    B = rng.standard_normal((7, 4))
    x = lstsq(A, B)
    x_np = np.linalg.lstsq(A, B, rcond=None)[0]
    assert x.shape == (3, 4)
    assert np.max(np.abs(x - x_np)) <= 1e-9


def test_lstsq_underdetermined_raises():
    with pytest.raises(NotImplementedError):
        lstsq(np.ones((2, 5)), np.ones(2))


def test_einsum_general_cases():
    rng = np.random.default_rng(203)
    cases = [
        ("ij,jk->ik", (rng.standard_normal((3, 4)), rng.standard_normal((4, 2)))),
        ("ii->", (rng.standard_normal((5, 5)),)),
        ("ij->ji", (rng.standard_normal((3, 4)),)),
        ("i,i->", (rng.standard_normal(6), rng.standard_normal(6))),
        ("i,j->ij", (rng.standard_normal(3), rng.standard_normal(4))),
        ("ij,j->i", (rng.standard_normal((4, 5)), rng.standard_normal(5))),
        ("ij,kl->ijkl", (rng.standard_normal((2, 3)), rng.standard_normal((2, 2)))),
        ("ij", (rng.standard_normal((3, 4)),)),           # implicit transpose-to-self
        ("ijk,kl->ijl", (rng.standard_normal((2, 3, 4)), rng.standard_normal((4, 2)))),
    ]
    for spec, ops in cases:
        got = np.asarray(einsum(spec, *ops))
        want = np.einsum(spec, *ops)
        assert np.max(np.abs(got - want)) <= 1e-9, spec


def test_einsum_complex():
    rng = np.random.default_rng(204)
    a = rng.standard_normal((3, 3)) + 1j * rng.standard_normal((3, 3))
    b = rng.standard_normal((3, 3)) + 1j * rng.standard_normal((3, 3))
    assert np.max(np.abs(np.asarray(einsum("ij,jk->ik", a, b)) - np.einsum("ij,jk->ik", a, b))) <= 1e-9


def _evsort(v):
    return np.array(sorted(v, key=lambda z: (round(z.real, 8), round(z.imag, 8))))


def test_eigvals_matches_numpy_multiset():
    rng = np.random.default_rng(205)
    for _ in range(20):
        n = int(rng.integers(2, 8))
        A = rng.standard_normal((n, n))
        if rng.integers(0, 2):
            A = A + 1j * rng.standard_normal((n, n))
        ev = eigvals(A)
        ev_np = np.linalg.eigvals(A)
        assert np.max(np.abs(_evsort(ev) - _evsort(ev_np))) <= 1e-7, n


def test_eigvals_complex_conjugate_pair_of_real_matrix():
    # 2-D rotation has eigenvalues ±i — a real matrix with complex eigenvalues.
    A = np.array([[0.0, -1.0], [1.0, 0.0]])
    ev = _evsort(eigvals(A))
    assert np.max(np.abs(ev - np.array([-1j, 1j]))) <= 1e-9


def test_eigvals_empty_and_scalar():
    assert eigvals(np.zeros((0, 0))).shape == (0,)
    assert np.allclose(eigvals(np.array([[3.0]])), np.array([3.0]))


def test_eigvals_rejects_nonsquare():
    with pytest.raises(ValueError):
        eigvals(np.ones((2, 3)))


def test_no_abs_no_nplinalg_eig():
    """No abs() and no np.linalg.{eig,eigvals,lstsq} in the call graph."""
    import ast
    import inspect

    from srmech.amsc.cascade import matrix_cascades as mc

    tree = ast.parse(inspect.getsource(mc))
    assert not [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "abs"
    ], "abs() is never fine"
    forbidden = {"qr", "svd", "eig", "eigh", "eigvals", "lstsq"}
    leaks = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in forbidden:
            base = node.value
            if isinstance(base, ast.Attribute) and base.attr == "linalg":
                leaks.add(f"np.linalg.{node.attr}")
    assert not leaks, f"must not call the numpy engine: {leaks}"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
