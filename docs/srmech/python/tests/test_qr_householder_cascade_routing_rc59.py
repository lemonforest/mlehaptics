"""rc59 — the QR shape-polymorphic pass.

The 8 ``matrix_cascades`` QR-internal matmul callsites (the Householder
reflector matvecs/outers, the self-binds, and the lstsq back-solve) route onto
the existing value-faithful ``dense_*`` kernels in ``srmech.amsc.laplacian``.
The kernels are value-faithful, so the decomposition INVARIANTS are preserved —
this test pins them across real/complex and 1-D / multi-column right-hand sides,
and asserts ``matrix_cascades`` no longer contributes any matmul-ledger token.

numpy-FREE (#564): numpy is GONE from srmech — ``qr``/``svd``/``lstsq``/``eigvals``
return plain Python lists. Fixtures use stdlib ``random``; the QR/SVD invariants
are checked with plain-list arithmetic; singular values are oracled by the
framework's own ``hermitian_eigendecompose`` on the Gram matrix; lstsq by the
defining normal-equation orthogonality; eigvals by the exact ``char_poly`` roots.
No numpy anywhere.
"""

from __future__ import annotations

import math
import pathlib
import random
import re

import pytest

from srmech.amsc.cascade import matrix_cascades as mc
from srmech.amsc.laplacian import hermitian_eigendecompose


_SHAPES = [(5, 5), (6, 3), (4, 4), (7, 2), (3, 3), (8, 5), (2, 2)]


# ── numpy-free list helpers ────────────────────────────────────────────


def _conjT(M):
    return [[complex(M[i][j]).conjugate() for i in range(len(M))]
            for j in range(len(M[0]))]


def _matmul(A, B):
    m, k, n = len(A), len(B), len(B[0])
    return [[sum(A[i][p] * B[p][j] for p in range(k)) for j in range(n)]
            for i in range(m)]


def _matvec(M, v):
    return [sum(M[i][j] * v[j] for j in range(len(v))) for i in range(len(M))]


def _mag2(z):
    z = complex(z)
    return z.real * z.real + z.imag * z.imag


def _max_recon_err2(C, A):
    return max(_mag2(complex(C[i][j]) - complex(A[i][j]))
               for i in range(len(A)) for j in range(len(A[0])))


def _max_off_identity_err2(G):
    n = len(G)
    return max(_mag2(complex(G[i][j]) - (1.0 if i == j else 0.0))
               for i in range(n) for j in range(n))


def _rand(rs, *dims, cplx=False):
    def gen(ds):
        if not ds:
            return (complex(rs.gauss(0, 1), rs.gauss(0, 1)) if cplx
                    else rs.gauss(0, 1))
        return [gen(ds[1:]) for _ in range(ds[0])]
    return gen(list(dims))


def _gram_singular_values(A):
    m, n = len(A), len(A[0])
    Ah = _conjT(A)
    G = _matmul(Ah, A) if n <= m else _matmul(A, Ah)
    w, _ = hermitian_eigendecompose(G)
    return sorted((math.sqrt(x) if x > 0.0 else 0.0) for x in w)


# ── QR invariants ──────────────────────────────────────────────────────


@pytest.mark.parametrize("m,n", _SHAPES)
@pytest.mark.parametrize("complex_input", [False, True])
def test_qr_invariants_hold(m, n, complex_input):
    rs = random.Random(m * 31 + n + (1000 if complex_input else 0))
    A = _rand(rs, m, n, cplx=complex_input)
    Q, R = mc.qr(A)
    k = min(m, n)
    assert len(Q) == m and len(Q[0]) == k
    assert len(R) == k and len(R[0]) == n
    assert _max_recon_err2(_matmul(Q, R), A) <= 1e-18               # reconstruction
    assert _max_off_identity_err2(_matmul(_conjT(Q), Q)) <= 1e-18   # orthonormal Q
    for i in range(k):                                              # upper-triangular
        for j in range(i):
            assert _mag2(R[i][j]) <= 1e-18


@pytest.mark.parametrize("m,n", [(5, 5), (6, 3), (4, 4), (8, 5)])
@pytest.mark.parametrize("complex_input", [False, True])
def test_svd_singular_values_match_gram_oracle(m, n, complex_input):
    rs = random.Random(m * 17 + n + (500 if complex_input else 0))
    A = _rand(rs, m, n, cplx=complex_input)
    s = mc.svd(A)[1]
    s_ref = _gram_singular_values(A)
    got = sorted(s)
    for a, b in zip(got, s_ref):
        assert (a - b) ** 2 <= 1e-14


@pytest.mark.parametrize("m,n", [(6, 3), (5, 5), (8, 4), (4, 4)])
def test_lstsq_1d_rhs_orthogonality(m, n):
    rs = random.Random(m * 13 + n)
    A = _rand(rs, m, n)
    b = _rand(rs, m)
    x = mc.lstsq(A, b)
    assert len(x) == n and not isinstance(x[0], list)
    # Aᵀ(Ax − b) ≈ 0 (defining least-squares orthogonality).
    r = [_matvec(A, x)[i] - b[i] for i in range(m)]
    Atr = _matvec(_conjT(A), r)
    assert max(_mag2(v) for v in Atr) <= 1e-16


@pytest.mark.parametrize("m,n,k", [(6, 3, 2), (5, 5, 4), (8, 4, 3), (4, 4, 1)])
def test_lstsq_multicolumn_rhs_orthogonality(m, n, k):
    """The shape-polymorphic back-solve path (2-D x in the triangular solve)."""
    rs = random.Random(m * 7 + n * 3 + k)
    A = _rand(rs, m, n)
    B = _rand(rs, m, k)
    X = mc.lstsq(A, B)
    assert len(X) == n and len(X[0]) == k
    resid = [[_matmul(A, X)[i][j] - B[i][j] for j in range(k)] for i in range(m)]
    AtR = _matmul(_conjT(A), resid)
    assert max(_mag2(AtR[i][j]) for i in range(n) for j in range(k)) <= 1e-16


def test_lstsq_complex_multicolumn_orthogonality():
    rs = random.Random(99)
    A = _rand(rs, 6, 3, cplx=True)
    B = _rand(rs, 6, 2, cplx=True)
    X = mc.lstsq(A, B)
    resid = [[_matmul(A, X)[i][j] - B[i][j] for j in range(2)] for i in range(6)]
    AhR = _matmul(_conjT(A), resid)
    assert max(_mag2(AhR[i][j]) for i in range(3) for j in range(2)) <= 1e-16


def test_eigvals_are_roots_of_char_poly():
    rs = random.Random(3)
    A = _rand(rs, 5, 5)
    ev = mc.eigvals(A)
    assert len(ev) == 5
    cp = mc.char_poly(A)
    scale = sum(_mag2(c) ** 0.5 for c in cp) + 1.0
    for lam in ev:
        val = 0.0 + 0.0j
        for c in cp:
            val = val * lam + complex(c)
        assert _mag2(val) ** 0.5 / scale < 1e-9


def test_matrix_cascades_contributes_no_matmul_token():
    """The QR-internals carry no counted matmul-ledger token any more — every
    contraction rides a dense_* / Mat kernel."""
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
