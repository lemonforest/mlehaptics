"""rc59 — the QR shape-polymorphic pass.

The 8 ``matrix_cascades`` QR-internal matmul callsites (the Householder
reflector matvecs/outers, the ``np.vdot`` self-binds, and the lstsq back-solve)
route onto the existing value-faithful ``dense_*`` kernels in
``srmech.amsc.laplacian``. The kernels are value-faithful, so the decomposition
INVARIANTS are preserved — this test pins them vs numpy across real/complex and
1-D / multi-column right-hand sides, and asserts ``matrix_cascades`` no longer
contributes any matmul-ledger token.
"""

from __future__ import annotations

import re
import pathlib

import numpy as np
import pytest

from srmech.amsc.cascade import matrix_cascades as mc


_SHAPES = [(5, 5), (6, 3), (4, 4), (7, 2), (3, 3), (8, 5), (2, 2)]


@pytest.mark.parametrize("m,n", _SHAPES)
@pytest.mark.parametrize("complex_input", [False, True])
def test_qr_invariants_hold(m, n, complex_input):
    rng = np.random.default_rng(m * 31 + n + (1000 if complex_input else 0))
    A = rng.standard_normal((m, n))
    if complex_input:
        A = A + 1j * rng.standard_normal((m, n))
    Q, R = mc.qr(A)
    k = min(m, n)
    assert Q.shape == (m, k)
    assert R.shape == (k, n)
    assert np.allclose(Q @ R, A, atol=1e-9)                       # reconstruction
    assert np.allclose(np.conj(Q.T) @ Q, np.eye(k), atol=1e-9)    # orthonormal Q
    assert np.allclose(np.triu(R), R, atol=1e-9)                  # upper-triangular


@pytest.mark.parametrize("m,n", [(5, 5), (6, 3), (4, 4), (8, 5)])
@pytest.mark.parametrize("complex_input", [False, True])
def test_svd_singular_values_match_numpy(m, n, complex_input):
    rng = np.random.default_rng(m * 17 + n + (500 if complex_input else 0))
    A = rng.standard_normal((m, n))
    if complex_input:
        A = A + 1j * rng.standard_normal((m, n))
    s = mc.svd(A)[1]
    s_ref = np.linalg.svd(A, compute_uv=False)
    assert np.allclose(np.sort(s)[::-1], np.sort(s_ref)[::-1], atol=1e-7)


@pytest.mark.parametrize("m,n", [(6, 3), (5, 5), (8, 4), (4, 4)])
def test_lstsq_1d_rhs_matches_numpy(m, n):
    rng = np.random.default_rng(m * 13 + n)
    A = rng.standard_normal((m, n))
    b = rng.standard_normal(m)
    x = mc.lstsq(A, b)
    assert x.shape == (n,)
    assert np.allclose(x, np.linalg.lstsq(A, b, rcond=None)[0], atol=1e-8)


@pytest.mark.parametrize("m,n,k", [(6, 3, 2), (5, 5, 4), (8, 4, 3), (4, 4, 1)])
def test_lstsq_multicolumn_rhs_matches_numpy(m, n, k):
    """The shape-polymorphic back-solve path (2-D x in the triangular solve)."""
    rng = np.random.default_rng(m * 7 + n * 3 + k)
    A = rng.standard_normal((m, n))
    B = rng.standard_normal((m, k))
    X = mc.lstsq(A, B)
    assert X.shape == (n, k)
    assert np.allclose(X, np.linalg.lstsq(A, B, rcond=None)[0], atol=1e-8)


def test_lstsq_complex_multicolumn_matches_numpy():
    rng = np.random.default_rng(99)
    A = rng.standard_normal((6, 3)) + 1j * rng.standard_normal((6, 3))
    B = rng.standard_normal((6, 2)) + 1j * rng.standard_normal((6, 2))
    X = mc.lstsq(A, B)
    assert np.allclose(X, np.linalg.lstsq(A, B, rcond=None)[0], atol=1e-8)


def test_eigvals_multiset_matches_numpy():
    rng = np.random.default_rng(3)
    A = rng.standard_normal((5, 5))
    ev = mc.eigvals(A)
    assert ev.shape == (5,)
    got = np.sort_complex(ev)
    ref = np.sort_complex(np.linalg.eigvals(A))
    assert np.allclose(got, ref, atol=1e-9)


def test_matrix_cascades_contributes_no_matmul_token():
    """The QR-internals carry no counted matmul-ledger token any more — every
    contraction rides a dense_* kernel (numpy carriers-only here)."""
    src = pathlib.Path(mc.__file__).read_text(encoding="utf-8")
    pats = [
        re.compile(r" @[ =]"),
        re.compile(
            r"\b(?:np|numpy)\.(?:matmul|einsum|kron|convolve|correlate|outer"
            r"|tensordot|vdot|inner|cross)\b"
        ),
        re.compile(r"\.dot\("),
    ]
    assert sum(len(p.findall(src)) for p in pats) == 0
