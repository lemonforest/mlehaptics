"""Parity tests for the ADR-0002 Phase 2 Class L broadening (v0.4.1rc5).

Four ops added per the Phase 1 spike finding (TDSE non-fitting case):

- ``hermitian_eigendecompose`` — complex Hermitian generalisation of
  ``jacobi_eigvals``.
- ``dense_matvec_complex`` — general complex ``M @ v``.
- ``elementwise_multiply_complex`` — pointwise ``a * b``.
- ``elementwise_transcendental`` — vectorised ``exp/cos/sin/log/exp_i``.

Post-#564 numpy is GONE from srmech; rc129 restores the numpy-carrier FORMAT:
``hermitian_eigendecompose`` / ``symmetric_eigendecompose`` return ``(Vec, Mat)``
(eigenVALUES a 1-D ``Vec``; eigenVECTORS a ``Mat`` whose COLUMNS are the
eigenvectors — ``V[i, k]`` = i-th component of k-th eigenvector), ``dense_matvec_*``
return a ``Vec``, ``dense_matmul_*`` / ``elementwise_*`` (rank-2) a ``Mat``.
Parity is against hand-computed values, reconstruction identities
(``H = V·diag(w)·Vᴴ``, ``VᴴV = I``), and stdlib ``cmath``/``math`` references —
never numpy LAPACK.
"""

from __future__ import annotations

import cmath
import math
import random

import pytest

from srmech.amsc import _native, laplacian


# ---------------------------------------------------------------------
# carrier-aware helpers (no numpy; rc129 Mat/Vec aware)
# ---------------------------------------------------------------------

def _nested(M):
    """rc129: a ``Mat`` carrier → nested list (``.tolist()``); pass lists thru."""
    return M.tolist() if hasattr(M, "tolist") else M


def _flat(v):
    """rc129: a ``Vec`` carrier → flat list (``.tolist()``); pass lists thru."""
    return v.tolist() if hasattr(v, "tolist") else v


def _make_hermitian(n, seed=0):
    rng = random.Random(seed)
    A = [[complex(rng.gauss(0, 1), rng.gauss(0, 1)) for _ in range(n)]
         for _ in range(n)]
    return [[(A[i][j] + A[j][i].conjugate()) / 2.0 for j in range(n)]
            for i in range(n)]


def _make_symmetric(n, seed=0):
    rng = random.Random(seed)
    A = [[rng.gauss(0, 1) for _ in range(n)] for _ in range(n)]
    return [[(A[i][j] + A[j][i]) / 2.0 for j in range(n)] for i in range(n)]


def _matvec(M, v):
    M = _nested(M)
    v = _flat(v)
    return [sum(M[i][k] * v[k] for k in range(len(v))) for i in range(len(M))]


def _conj_transpose(M):
    M = _nested(M)
    if not M:
        return []
    rows, cols = len(M), len(M[0])
    return [[M[i][j].conjugate() if isinstance(M[i][j], complex) else M[i][j]
             for i in range(rows)] for j in range(cols)]


def _max_recon_err(H, w, V):
    """max |H[i][j] − Σ_k V[i][k]·w[k]·conj(V[j][k])| (H = V diag(w) Vᴴ)."""
    H, V, w = _nested(H), _nested(V), _flat(w)
    n = len(H)
    err = 0.0
    for i in range(n):
        for j in range(n):
            s = sum(V[i][k] * w[k] * V[j][k].conjugate() for k in range(n))
            err = max(err, abs(s - H[i][j]))
    return err


def _max_unitary_err(V):
    """max |δ_ij − Σ_k conj(V[k][i])·V[k][j]| (columns orthonormal: VᴴV = I)."""
    V = _nested(V)
    n = len(V)
    err = 0.0
    for i in range(n):
        for j in range(n):
            s = sum(V[k][i].conjugate() * V[k][j] for k in range(n))
            d = 1.0 if i == j else 0.0
            err = max(err, abs(s - d))
    return err


# ---------------------------------------------------------------------
# hermitian_eigendecompose
# ---------------------------------------------------------------------


def test_hermitian_eigendecompose_real_diagonal():
    H = [[complex(d, 0.0) if i == j else 0j for j in range(4)]
         for i, d in enumerate([3.0, 1.0, 5.0, 2.0])]
    eigvals, V = laplacian.hermitian_eigendecompose(H)
    for got, exp in zip(eigvals, [1.0, 2.0, 3.0, 5.0]):
        assert abs(got - exp) < 1e-12
    # V is 4x4.
    assert len(V) == 4 and all(len(row) == 4 for row in V)


def test_hermitian_eigendecompose_reconstruction():
    H = _make_hermitian(4, seed=42)
    w, V = laplacian.hermitian_eigendecompose(H)
    # Eigenvalues ascending.
    assert all(w[i] <= w[i + 1] + 1e-12 for i in range(len(w) - 1))
    # H · V = V · diag(w) ⇔ H = V diag(w) Vᴴ: reconstruction residual tiny.
    assert _max_recon_err(H, w, V) < 1e-9


def test_hermitian_eigendecompose_unitary():
    H = _make_hermitian(5, seed=7)
    _, V = laplacian.hermitian_eigendecompose(H)
    # Columns orthonormal: VᴴV = I.
    assert _max_unitary_err(V) < 1e-9


def test_hermitian_eigendecompose_zero_size():
    w, V = laplacian.hermitian_eigendecompose([])
    assert list(w) == []
    assert list(V) == []


def test_hermitian_eigendecompose_2x2_pauli():
    """Pauli-Y: H = [[0, -i], [i, 0]]; eigvals = ±1."""
    H = [[0.0 + 0j, -1j], [1j, 0.0 + 0j]]
    w, V = laplacian.hermitian_eigendecompose(H)
    for got, exp in zip(sorted(w), [-1.0, 1.0]):
        assert abs(got - exp) < 1e-12
    # Reconstruction H = V diag(w) Vᴴ.
    assert _max_recon_err(H, w, V) < 1e-12


# ---------------------------------------------------------------------
# symmetric_eigendecompose  (real-symmetric Class L specialisation)
# ---------------------------------------------------------------------


def test_symmetric_eigendecompose_returns_real():
    """The whole point of the specialisation: real eigvals AND real
    eigvecs (no complex V for real-symmetric L)."""
    L = laplacian.dense_laplacian(4, [(0, 1), (1, 2), (2, 3), (3, 0)])
    eigvals, V = laplacian.symmetric_eigendecompose(L)
    assert all(not isinstance(e, complex) for e in eigvals)  # Vec iterates scalars
    Vl = V.tolist()                                          # rc129: real Mat
    assert all(not isinstance(Vl[i][j], complex)
               for i in range(len(Vl)) for j in range(len(Vl[i])))


def test_symmetric_eigendecompose_reconstruction():
    L = _make_symmetric(5, seed=42)
    w, V = laplacian.symmetric_eigendecompose(L)
    w = w.tolist()                                  # rc129: Vec eigenvalues
    V = V.tolist()                                  # rc129: real Mat eigenvectors
    assert all(w[i] <= w[i + 1] + 1e-12 for i in range(len(w) - 1))
    # Reconstruction L = V diag(w) Vᵀ (real ⇒ conj is identity).
    n = len(L)
    err = 0.0
    for i in range(n):
        for j in range(n):
            s = sum(V[i][k] * w[k] * V[j][k] for k in range(n))
            err = max(err, abs(s - L[i][j]))
    assert err < 1e-9


def test_symmetric_eigendecompose_orthonormal():
    L = _make_symmetric(6, seed=7)
    _, V = laplacian.symmetric_eigendecompose(L)
    V = V.tolist()                                  # rc129: real Mat eigenvectors
    # VᵀV = I.
    n = len(V)
    err = 0.0
    for i in range(n):
        for j in range(n):
            s = sum(V[k][i] * V[k][j] for k in range(n))
            d = 1.0 if i == j else 0.0
            err = max(err, abs(s - d))
    assert err < 1e-9


def test_symmetric_eigendecompose_diagonal():
    L = [[d if i == j else 0.0 for j in range(4)]
         for i, d in enumerate([3.0, 1.0, 5.0, 2.0])]
    eigvals, V = laplacian.symmetric_eigendecompose(L)
    for got, exp in zip(eigvals, [1.0, 2.0, 3.0, 5.0]):
        assert abs(got - exp) < 1e-12
    assert len(V) == 4 and all(len(row) == 4 for row in V)


def test_symmetric_eigendecompose_laplacian_nullspace():
    """A connected graph Laplacian has exactly one zero eigenvalue
    (the constant vector); smallest eigenvalue ≈ 0."""
    L = laplacian.dense_laplacian(4, [(0, 1), (1, 2), (2, 3)])
    eigvals, _ = laplacian.symmetric_eigendecompose(L)
    assert abs(eigvals[0]) < 1e-9


def test_symmetric_eigendecompose_zero_size():
    w, V = laplacian.symmetric_eigendecompose([])
    assert list(w) == []
    assert list(V) == []


def test_symmetric_eigendecompose_rejects_nonsquare():
    with pytest.raises(ValueError):
        laplacian.symmetric_eigendecompose([[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]])


def test_symmetric_eigendecompose_in_class_l_registry():
    assert "symmetric_eigendecompose" in laplacian.LAPLACIAN_OPS
    assert "symmetric_eigendecompose" in laplacian.__all__


# ---------------------------------------------------------------------
# dense_matvec_complex
# ---------------------------------------------------------------------


def test_dense_matvec_complex_matches_hand_computed():
    rng = random.Random(123)
    M = [[complex(rng.gauss(0, 1), rng.gauss(0, 1)) for _ in range(3)]
         for _ in range(5)]
    v = [complex(rng.gauss(0, 1), rng.gauss(0, 1)) for _ in range(3)]
    out = laplacian.dense_matvec_complex(M, v)
    expected = _matvec(M, v)
    assert len(out) == 5
    for a, b in zip(out, expected):
        assert abs(a - b) < 1e-12


def test_dense_matvec_complex_square():
    M = [[1 + 0j, 2 - 1j], [0 + 1j, 3 + 0j]]
    v = [1 - 1j, 2 + 0j]
    out = laplacian.dense_matvec_complex(M, v)
    for a, b in zip(out, _matvec(M, v)):
        assert abs(a - b) < 1e-12


def test_dense_matvec_complex_shape_mismatch():
    M = [[1 + 0j if i == j else 0j for j in range(3)] for i in range(3)]
    v = [0j, 0j]
    with pytest.raises(ValueError):
        laplacian.dense_matvec_complex(M, v)


# ---------------------------------------------------------------------
# dense_matmul_complex (matmul-kernel phase; #928) — the cascade ``A @ B``.
# ---------------------------------------------------------------------


def _matmul(A, B):
    rows, inner, cols = len(A), len(B), len(B[0])
    return [[sum(A[i][k] * B[k][j] for k in range(inner)) for j in range(cols)]
            for i in range(rows)]


def test_dense_matmul_complex_matches_hand_computed():
    rng = random.Random(456)
    A = [[complex(rng.gauss(0, 1), rng.gauss(0, 1)) for _ in range(3)]
         for _ in range(5)]
    B = [[complex(rng.gauss(0, 1), rng.gauss(0, 1)) for _ in range(4)]
         for _ in range(3)]
    out = laplacian.dense_matmul_complex(A, B)
    expected = _matmul(A, B)
    assert out.shape == (5, 4)                       # rc129: complex Mat carrier
    for i in range(5):
        for j in range(4):
            assert abs(out[i, j] - expected[i][j]) < 1e-12


def test_dense_matmul_complex_square_and_identity():
    A = [[1 + 0j, 2 - 1j], [0 + 1j, 3 + 0j]]
    B = [[2 + 0j, 0 + 1j], [1 - 1j, 4 + 0j]]
    out = laplacian.dense_matmul_complex(A, B)
    for i in range(2):
        for j in range(2):
            assert abs(out[i, j] - _matmul(A, B)[i][j]) < 1e-12
    eye = [[1 + 0j if i == j else 0j for j in range(2)] for i in range(2)]
    out2 = laplacian.dense_matmul_complex(A, eye)
    for i in range(2):
        for j in range(2):
            assert abs(out2[i, j] - A[i][j]) < 1e-12


def test_dense_matmul_complex_shape_mismatch():
    A = [[1 + 0j if i == j else 0j for j in range(3)] for i in range(3)]
    B = [[0j, 0j], [0j, 0j]]
    with pytest.raises(ValueError):
        laplacian.dense_matmul_complex(A, B)


def test_dense_matmul_complex_matches_matvec_per_column():
    # The matmul cascade must agree with the matvec cascade applied column-wise
    # (the contraction is the same op; this pins the two cascades consistent).
    rng = random.Random(789)
    A = [[complex(rng.gauss(0, 1), rng.gauss(0, 1)) for _ in range(4)]
         for _ in range(4)]
    B = [[complex(rng.gauss(0, 1), rng.gauss(0, 1)) for _ in range(3)]
         for _ in range(4)]
    out = laplacian.dense_matmul_complex(A, B)   # complex Mat
    ncols = len(B[0])
    for j in range(ncols):
        col = [B[i][j] for i in range(len(B))]
        mv = laplacian.dense_matvec_complex(A, col)  # complex Vec
        for i in range(out.n_rows):
            assert abs(out[i, j] - mv[i]) < 1e-12


# ---------------------------------------------------------------------
# elementwise_multiply_complex
# ---------------------------------------------------------------------


def test_elementwise_multiply_complex_matches_hand_computed():
    a = [1 + 1j, 2 - 1j, 3 + 0j, -1 + 2j]
    b = [1 - 1j, 1 + 1j, -1j, 0 + 0j]
    out = laplacian.elementwise_multiply_complex(a, b)
    for got, (ai, bi) in zip(out, zip(a, b)):
        assert abs(got - ai * bi) < 1e-12


def test_elementwise_multiply_complex_empty():
    out = laplacian.elementwise_multiply_complex([], [])
    assert list(out) == []


# ---------------------------------------------------------------------
# elementwise_transcendental
# ---------------------------------------------------------------------


def test_elementwise_transcendental_exp_matches_stdlib():
    x = [0.0, 0.5, 1.0, 2.0, -1.0]
    out = laplacian.elementwise_transcendental(x, "exp")
    for got, xi in zip(out, x):
        assert abs(got - math.exp(xi)) < 1e-12


def test_elementwise_transcendental_cos_sin_match_stdlib():
    x = [-3.0 + 6.0 * k / 6 for k in range(7)]   # linspace(-3, 3, 7)
    for got, xi in zip(laplacian.elementwise_transcendental(x, "cos"), x):
        assert abs(got - math.cos(xi)) < 1e-12
    for got, xi in zip(laplacian.elementwise_transcendental(x, "sin"), x):
        assert abs(got - math.sin(xi)) < 1e-12


def test_elementwise_transcendental_log_matches_stdlib():
    x = [1.0, 2.0, 10.0, 0.5, 100.0]
    out = laplacian.elementwise_transcendental(x, "log")
    for got, xi in zip(out, x):
        assert abs(got - math.log(xi)) < 1e-12


def test_elementwise_transcendental_log_rejects_nonpositive():
    x = [1.0, 0.0, 2.0]
    with pytest.raises((ValueError, FloatingPointError)):
        laplacian.elementwise_transcendental(x, "log")


def test_elementwise_transcendental_exp_i_complex():
    """exp_i(x) = exp(1j * x) — TDSE-relevant complex exponential."""
    x = [0.0, math.pi / 4, math.pi / 2, math.pi, 2 * math.pi]
    out = laplacian.elementwise_transcendental(x, "exp_i")
    for got, xi in zip(out, x):
        assert abs(got - cmath.exp(1j * xi)) < 1e-12


def test_elementwise_transcendental_unknown_op_rejected():
    x = [1.0, 2.0]
    with pytest.raises(ValueError):
        laplacian.elementwise_transcendental(x, "tanh")


# ---------------------------------------------------------------------
# LAPLACIAN_OPS registry
# ---------------------------------------------------------------------


def test_class_l_ops_registry_includes_new_ops():
    expected_new = {
        "hermitian_eigendecompose",
        "dense_matvec_complex",
        "elementwise_multiply_complex",
        "elementwise_transcendental",
    }
    expected_old = {
        "dense_adjacency",
        "dense_laplacian",
        "normalized_laplacian",
        "jacobi_eigvals",
    }
    ops = set(laplacian.LAPLACIAN_OPS)
    assert expected_new <= ops
    assert expected_old <= ops


def test_tdse_evolve_composition_end_to_end():
    """End-to-end TDSE compose test — the ADR-0002 Phase 1 spike scenario.

    psi(t) = V · diag(exp(-i*eigvals*t)) · Vᴴ · psi(0). With H Hermitian
    and psi(0) arbitrary, verify |psi(t)| preservation (unitary evolution)
    plus reconstruction against a direct stdlib spectral expm.
    """
    H = _make_hermitian(4, seed=99)
    psi0 = [1.0 + 0j, 0 + 0.5j, -0.5 + 0j, 0.5 + 0.5j]
    nrm0 = math.sqrt(sum(abs(z) ** 2 for z in psi0))
    psi0 = [z / nrm0 for z in psi0]
    t = 1.5
    n = len(H)

    # Compose via the Class L ops.
    w, V = laplacian.hermitian_eigendecompose(H)
    VH = _conj_transpose(V)
    psi_eig = laplacian.dense_matvec_complex(VH, psi0)
    phase = laplacian.elementwise_transcendental([-wi * t for wi in w], "exp_i")
    psi_eig_t = laplacian.elementwise_multiply_complex(phase, psi_eig)
    psi_t = laplacian.dense_matvec_complex(V, psi_eig_t)

    # Reference: direct spectral expm via stdlib cmath (V · diag(e^{-iwt}) · Vᴴ · psi0).
    ref_eig = _matvec(VH, psi0)
    ref_eig = [cmath.exp(-1j * w[k] * t) * ref_eig[k] for k in range(n)]
    psi_t_ref = _matvec(V, ref_eig)

    for a, b in zip(psi_t, psi_t_ref):
        assert abs(a - b) < 1e-10
    # Norm preserved by unitary evolution.
    norm_t = math.sqrt(sum(abs(z) ** 2 for z in psi_t))
    assert abs(norm_t - 1.0) < 1e-10
