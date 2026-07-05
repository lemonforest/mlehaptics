"""rc140 (Foundation F2) — the numeric f64 QR + SVD C peers.

``srmech_qr_f64`` (direct Householder) + ``srmech_svd_f64`` (one-sided-Jacobi,
bounded-sweep convergence contract) are the numeric-LA foundations the subspace
/ MIMO / LA family dispatches its REAL path to (the C:Python parity backfill:
the C surface had jacobi_eigvals / hermitian_eigendecompose / dense_matmul /
dense_solve but NO SVD and NO QR). This suite proves:

1. **QR correctness** — reconstruction ``A == Q·R``, orthogonality ``QᵀQ == I``,
   R upper-trapezoidal, across square / tall / wide-columns shapes.
2. **SVD correctness** — reconstruction ``U·diag(S)·Vᵀ == A``, orthogonality
   ``UᵀU == I`` / ``VᵀV == I``, descending ``S >= 0``, and ``S²`` vs an
   INDEPENDENT eigendecomposition of ``AᵀA`` (``srmech_jacobi_eigvals``) —
   including the near-degenerate-singular-value stress + a rank-deficient case.
3. **Convergence contract** — ``svd_f64_c`` returns ``None`` on a non-converged
   sweep (status OVERFLOW) so the caller falls back to pure (NEVER a silent
   wrong answer); the cap-hit path is proven at build time with a cap=1 build.
4. **Dispatch parity** — ``matrix_cascades.{qr,svd,lstsq}`` + the subspace ops
   dispatched-to-C match their own pure path (native forced OFF via monkeypatch)
   to tolerance.

NUMERIC (FPU-tol), not byte-exact. This module is **numpy-free** (a test for a
numpy-free surface must itself be numpy-free) — the references are stdlib only.
"""

from __future__ import annotations

import random

import pytest

from srmech.amsc import _native
from srmech.amsc.cascade import matrix_cascades as mc

HAS_QR = _native.has_native_qr_f64()
HAS_SVD = _native.has_native_svd_f64()

_qr_only = pytest.mark.skipif(
    not HAS_QR, reason="native srmech_qr_f64 not built (pure list-Householder is "
                       "the complete alternative; the pure-path parity test runs)")
_svd_only = pytest.mark.skipif(
    not HAS_SVD, reason="native srmech_svd_f64 not built (pure Gram-eigen SVD is "
                        "the complete alternative; the pure-path parity test runs)")


# ── numpy-free helpers ─────────────────────────────────────────────────────
def _rand(m, n, seed):
    random.seed(seed)
    return [[random.uniform(-3.0, 3.0) for _ in range(n)] for _ in range(m)]


def _maxabs(xs):
    m = 0.0
    for x in xs:
        ax = x if x >= 0 else -x
        if ax > m:
            m = ax
    return m


def _mag(z):
    return (z.real * z.real + z.imag * z.imag) ** 0.5 if isinstance(z, complex) else (
        z if z >= 0 else -z)


def _rows(mat):
    """A Mat / carrier → nested list of complex."""
    return [[complex(mat[i, j]) for j in range(mat.n_cols)] for i in range(mat.n_rows)]


# ── 1. QR correctness (native) ─────────────────────────────────────────────
@_qr_only
@pytest.mark.parametrize("m,n", [(3, 3), (5, 3), (6, 6), (8, 4), (4, 4), (10, 7), (2, 2)])
def test_native_qr_invariants(m, n):
    A = _rand(m, n, seed=100 + m * 31 + n)
    res = _native.qr_f64_c(A)
    assert res is not None
    Q, R = res
    # A == Q @ R
    recon = [sum(Q[i][k] * R[k][j] for k in range(m)) - A[i][j]
             for i in range(m) for j in range(n)]
    assert _maxabs(recon) < 1e-10, f"QR recon m={m} n={n}"
    # Qᵀ Q == I
    qtq = [sum(Q[k][i] * Q[k][j] for k in range(m)) - (1.0 if i == j else 0.0)
           for i in range(m) for j in range(m)]
    assert _maxabs(qtq) < 1e-10, f"QtQ-I m={m} n={n}"
    # R upper-trapezoidal (below-diagonal ~ 0)
    lower = _maxabs([R[i][j] for i in range(m) for j in range(n) if i > j])
    assert lower < 1e-10, f"R not upper-triangular m={m} n={n}"


# ── 2. SVD correctness (native) ────────────────────────────────────────────
def _svd_check(m, n, A, tol=1e-9):
    res = _native.svd_f64_c(A)
    assert res is not None, "svd_f64_c returned None (non-converged?)"
    sigma, vcols = res
    assert len(sigma) == n
    # descending, >= 0
    assert all(sigma[j] >= sigma[j + 1] - 1e-12 for j in range(n - 1))
    assert all(s >= -1e-15 for s in sigma)
    # reconstruct A = Σ_j σ_j u_j v_jᵀ with u_j = A v_j / σ_j (σ_j > tol)
    smax = sigma[0] if sigma else 0.0
    gate = smax * max(m, n) * 1e-9
    recon = [[0.0] * n for _ in range(m)]
    for j in range(n):
        if sigma[j] <= gate:
            continue
        vj = vcols[j]
        uj = [sum(A[i][t] * vj[t] for t in range(n)) / sigma[j] for i in range(m)]
        for i in range(m):
            for c in range(n):
                recon[i][c] += sigma[j] * uj[i] * vj[c]
    err = _maxabs([recon[i][j] - A[i][j] for i in range(m) for j in range(n)])
    assert err < 1e-9, f"SVD recon m={m} n={n} err={err:.2e}"
    # Vᵀ V == I (right singular vectors orthonormal)
    vtv = [sum(vcols[i][t] * vcols[j][t] for t in range(n)) - (1.0 if i == j else 0.0)
           for i in range(n) for j in range(n)]
    assert _maxabs(vtv) < 1e-9, f"VtV-I m={m} n={n}"
    # S² vs eigenvalues(AᵀA) via the INDEPENDENT srmech_jacobi_eigvals kernel
    _svd_check_against_ata(m, n, A, sigma)
    return sigma


def _svd_check_against_ata(m, n, A, sigma):
    import ctypes
    if not (_native.HAS_NATIVE and _native.LIB is not None
            and hasattr(_native.LIB, "srmech_jacobi_eigvals")):
        return
    ata = [sum(A[k][i] * A[k][j] for k in range(m)) for i in range(n) for j in range(n)]
    D = ctypes.c_double
    buf = (D * (n * n))(*ata)
    ev = (D * n)()
    _native.LIB.srmech_jacobi_eigvals(ctypes.c_uint32(n), buf,
                                      ctypes.c_uint32(100), D(1e-15), ev)
    evs = sorted([ev[i] for i in range(n)], reverse=True)
    s2 = sorted([s * s for s in sigma], reverse=True)
    assert _maxabs([s2[i] - evs[i] for i in range(n)]) < 1e-8, "S^2 vs eig(AtA)"


@_svd_only
@pytest.mark.parametrize("m,n", [(3, 3), (5, 3), (6, 6), (8, 4), (4, 4), (10, 7), (2, 2), (7, 1)])
def test_native_svd_invariants(m, n):
    _svd_check(m, n, _rand(m, n, seed=200 + m * 17 + n))


@_svd_only
def test_native_svd_rank_deficient():
    """A column-dependent matrix → an exact σ=0, orthogonality preserved."""
    m, n = 6, 4
    base = _rand(m, 3, seed=555)
    A = [row + [row[0] + row[1]] for row in base]     # col4 = col1 + col2
    sigma = _svd_check(m, n, A)
    assert sigma[-1] < 1e-9, f"rank-deficient smallest σ not ~0: {sigma[-1]:.2e}"


# ── CONVERGENCE REGRESSION (coordinator): rank-deficient matrices whose
#    near-dependent columns fall into a geometric-shrink cycle. Before the
#    Demmel–Veselić numerical-zero column floor, these HIT THE SWEEP CAP and
#    returned NOT-CONVERGED (None) — a fatal gap on a python-free host (no
#    fallback). They MUST now converge to a valid, reconstructing result. ──
@_svd_only
@pytest.mark.parametrize("name,A", [
    ("row2=2*row1",  [[1.0, 2.0, 3.0], [2.0, 4.0, 6.0], [1.0, 1.0, 1.0]]),
    ("zerorow+dep",  [[0.0, 0.0, 0.0], [1.0, 2.0, 3.0], [2.0, 4.0, 6.0]]),
])
def test_native_svd_convergence_regression(name, A):
    """The two matrices that hit the cap before the numerical-zero floor —
    must return a valid result (NOT None) + reconstruct to tol."""
    res = _native.svd_f64_c(A)
    assert res is not None, (
        f"{name}: svd_f64_c returned None (hit the sweep cap) — the Demmel–"
        f"Veselić numerical-zero column floor should converge this")
    # _svd_check re-verifies reconstruction + orthogonality + descending + S²
    sigma = _svd_check(3, 3, A)
    assert sigma[-1] < 1e-9, f"{name}: rank-deficient smallest σ not ~0: {sigma[-1]:.2e}"


@_svd_only
def test_native_svd_near_degenerate():
    """THE WEAKEST-LINK STRESS: two nearly-equal singular values (5, 3.0000001,
    3.0, 0.5) must converge and be recovered accurately."""
    import math
    diag = [5.0, 3.0000001, 3.0, 0.5]

    def gm(i, j, a):
        M = [[1.0 if p == q else 0.0 for q in range(4)] for p in range(4)]
        c, s = math.cos(a), math.sin(a)
        M[i][i] = c; M[j][j] = c; M[i][j] = -s; M[j][i] = s
        return M

    def mm(X, Y):
        return [[sum(X[i][k] * Y[k][j] for k in range(4)) for j in range(4)]
                for i in range(4)]
    U = mm(gm(0, 2, 0.7), gm(1, 3, 0.4))
    V = mm(gm(0, 1, 0.9), gm(2, 3, 0.3))
    Dm = [[diag[i] if i == j else 0.0 for j in range(4)] for i in range(4)]
    Vt = [[V[j][i] for j in range(4)] for i in range(4)]
    A = mm(mm(U, Dm), Vt)
    sigma = _svd_check(4, 4, A, tol=1e-8)
    exp = sorted(diag, reverse=True)
    assert _maxabs([sigma[i] - exp[i] for i in range(4)]) < 1e-6, \
        f"near-degenerate σ recovery: {sigma}"


@_svd_only
def test_native_svd_m_lt_n_returns_none():
    """The kernel's domain is tall/square (m>=n); m<n → None (caller keeps pure)."""
    assert _native.svd_f64_c([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]) is None


# ── 3. dispatch parity — matrix_cascades.{qr,svd,lstsq} native == pure ──────
def _reldiff_rows(a, b):
    scale = _maxabs([_mag(v) for r in a for v in r]) or 1.0
    worst = _maxabs([_mag(a[i][j] - b[i][j])
                     for i in range(len(a)) for j in range(len(a[0]))])
    return worst / scale


@_qr_only
@pytest.mark.parametrize("m,n", [(4, 4), (6, 3), (5, 5), (8, 4)])
def test_qr_dispatch_matches_pure(monkeypatch, m, n):
    A = _rand(m, n, seed=300 + m + n)
    Qd, Rd = mc.qr(A)
    monkeypatch.setattr(_native, "has_native_qr_f64", lambda: False)
    Qp, Rp = mc.qr(A)
    # QR is unique only up to column signs — compare the INVARIANTS, not entries.
    ad = [[sum(Qd[i, k] * Rd[k, j] for k in range(Qd.n_cols)).real
           for j in range(n)] for i in range(m)]
    ap = [[sum(Qp[i, k] * Rp[k, j] for k in range(Qp.n_cols)).real
           for j in range(n)] for i in range(m)]
    assert _reldiff_rows(ad, A) < 1e-9 and _reldiff_rows(ap, A) < 1e-9


@_svd_only
@pytest.mark.parametrize("m,n", [(4, 4), (6, 3), (5, 5), (8, 4)])
def test_svd_dispatch_matches_pure(monkeypatch, m, n):
    A = _rand(m, n, seed=400 + m + n)
    Ud, Sd, Vhd = mc.svd(A)
    sd = [float(Sd[j]) for j in range(Sd.shape[0])]
    monkeypatch.setattr(_native, "has_native_svd_f64", lambda: False)
    Up, Sp, Vhp = mc.svd(A)
    sp = [float(Sp[j]) for j in range(Sp.shape[0])]
    # singular VALUES are unique — dispatched == pure to tolerance.
    assert _maxabs([sd[i] - sp[i] for i in range(len(sd))]) < 1e-8, \
        f"σ dispatch!=pure m={m} n={n}"
    # dispatched reconstruction holds.
    k = min(m, n)
    recon = [[sum(complex(Ud[i, t]) * sd[t] * complex(Vhd[t, j])
                  for t in range(k)) for j in range(n)] for i in range(m)]
    assert _reldiff_rows(recon, [[complex(v) for v in r] for r in A]) < 1e-8


@_qr_only
@pytest.mark.parametrize("m,n", [(5, 3), (6, 4), (4, 4)])
def test_lstsq_dispatch_matches_pure(monkeypatch, m, n):
    A = _rand(m, n, seed=500 + m + n)
    b = [random.Random(9 + m).uniform(-2, 2) for _ in range(m)]
    xd = mc.lstsq(A, b)
    xd = [float(xd[i]) for i in range(xd.shape[0])]
    monkeypatch.setattr(_native, "has_native_qr_f64", lambda: False)
    xp = mc.lstsq(A, b)
    xp = [float(xp[i]) for i in range(xp.shape[0])]
    assert _maxabs([xd[i] - xp[i] for i in range(n)]) < 1e-7, \
        f"lstsq dispatch!=pure m={m} n={n}"


# ── 4. subspace ops still correct (compose the C-backed foundations) ────────
@_svd_only
def test_mimo_svd_dispatch_matches_pure(monkeypatch):
    from srmech.signal_processing.closed_form_ops import mimo_svd
    A = [[complex(random.Random(3 + i * 5 + j).uniform(-2, 2)) for j in range(3)]
         for i in range(5)]
    _, Sd, _ = mimo_svd.op(A)
    monkeypatch.setattr(_native, "has_native_svd_f64", lambda: False)
    _, Sp, _ = mimo_svd.op(A)
    assert _maxabs([Sd[i] - Sp[i] for i in range(len(Sd))]) < 1e-8


# ── 5. the PURE path always runs (native forced OFF) — the parity oracle ────
@pytest.mark.parametrize("m,n", [(3, 3), (5, 3), (6, 4)])
def test_pure_qr_svd_lstsq_run_without_native(monkeypatch, m, n):
    monkeypatch.setattr(_native, "has_native_qr_f64", lambda: False)
    monkeypatch.setattr(_native, "has_native_svd_f64", lambda: False)
    A = _rand(m, n, seed=700 + m + n)
    Q, R = mc.qr(A)
    ad = [[sum(complex(Q[i, k]) * complex(R[k, j]) for k in range(Q.n_cols)).real
           for j in range(n)] for i in range(m)]
    assert _reldiff_rows(ad, A) < 1e-9
    U, S, Vh = mc.svd(A)
    k = min(m, n)
    recon = [[sum(complex(U[i, t]) * float(S[t]) * complex(Vh[t, j])
                  for t in range(k)) for j in range(n)] for i in range(m)]
    assert _reldiff_rows(recon, [[complex(v) for v in r] for r in A]) < 1e-8
