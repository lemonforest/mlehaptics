"""Tests for srmech.qm.spin (Pauli matrices, Clifford algebra).

numpy-FREE end to end (v0.7.5rc115, #564): ``pauli_matrices`` /
``pauli_identity`` / ``pauli_spin_operator`` return :class:`~srmech.amsc.mat.Mat`,
and **these tests use no numpy** — the eigenvalue checks go through the
framework's own Class-L numpy-free Hermitian eigendecomposition
(:func:`srmech.amsc.laplacian.mat_hermitian_eigendecompose`), matrix products
through :func:`~srmech.amsc.laplacian.mat_matmul`, and every matrix-equality
check is a direct ``Mat``-entry comparison. A test for a numpy-free module must
itself run with numpy genuinely absent — there is no ``.to_numpy()`` here
(numpy is not a validation reference;
``[[feedback_no_numpy_rosetta_peer_continuous_float_error_collecting]]``).
"""

from __future__ import annotations

import pytest

from srmech.amsc.laplacian import mat_hermitian_eigendecompose, mat_matmul
from srmech.qm import spin


# ---------------------------------------------------------------------------
# numpy-free Mat helpers (no numpy oracle).
# ---------------------------------------------------------------------------


def _entries(m):
    """Flat row-major list of a ``Mat``'s plain (complex) entries."""
    return [m[i, j] for i in range(m.n_rows) for j in range(m.n_cols)]


def _max_abs_combo(*signed):
    """``max_k |Σ sign·entry_k|`` over aligned entries of equal-shape Mats.

    ``signed`` is a sequence of ``(scalar, Mat)`` pairs; the scalar folds the
    sign (and any coefficient) into an entrywise linear combination. The
    magnitude is the plain Python ``abs`` of a scalar (Class-K on a number,
    not a cascade ``abs()``), used only as a test tolerance gate.
    """
    flats = [_entries(m) for _, m in signed]
    coeffs = [c for c, _ in signed]
    n = len(flats[0])
    return max(
        abs(sum(c * fl[k] for c, fl in zip(coeffs, flats))) for k in range(n)
    )


def _eigvals_ascending(m):
    """Ascending real eigenvalues of a Hermitian ``Mat`` (Class-L, numpy-free)."""
    evals, _vecs = mat_hermitian_eigendecompose(m)
    return [evals[i, 0] for i in range(evals.n_rows)]


# ---------------------------------------------------------------------------
# Tests.
# ---------------------------------------------------------------------------


def test_pauli_matrices_hermitian():
    """All Pauli matrices are Hermitian: ``σ = σ†`` (exact)."""
    sx, sy, sz = spin.pauli_matrices()
    for label, s in (("σ_x", sx), ("σ_y", sy), ("σ_z", sz)):
        assert _max_abs_combo((1, s), (-1, s.conj().T)) < 1e-14, label


def test_pauli_matrices_traceless():
    """tr(σ_i) = 0."""
    sx, sy, sz = spin.pauli_matrices()
    for s in (sx, sy, sz):
        trace = sum(s[i, i] for i in range(s.n_rows))
        assert abs(trace) < 1e-14


def test_pauli_matrices_square_identity():
    """σ_i² = I (exact, via the numpy-free native matmul)."""
    sx, sy, sz = spin.pauli_matrices()
    I = spin.pauli_identity()
    for s in (sx, sy, sz):
        assert _max_abs_combo((1, mat_matmul(s, s)), (-1, I)) < 1e-14


def test_pauli_eigenvalues():
    """Each σ_i has eigenvalues ±1 (Class-L Hermitian eigendecomp)."""
    sx, sy, sz = spin.pauli_matrices()
    for s in (sx, sy, sz):
        eigvals = _eigvals_ascending(s)
        assert abs(eigvals[0] - (-1.0)) < 1e-13
        assert abs(eigvals[1] - 1.0) < 1e-13


def test_pauli_clifford_residuals():
    """{σ_i, σ_j} = 2 δ_{ij} I and [σ_i, σ_j] = 2i ε_{ijk} σ_k at machine precision."""
    max_anti, max_comm = spin.pauli_clifford_residuals()
    assert max_anti < 1e-13
    assert max_comm < 1e-13


def test_pauli_spin_operator_eigenvalues_half():
    """S_n = (1/2) σ·n̂ has eigenvalues ±½ for any direction (plain lists)."""
    for direction in [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
        [1.0, 1.0, 1.0],
        [0.3, -0.7, 1.5],
    ]:
        S = spin.pauli_spin_operator(direction)
        eigvals = _eigvals_ascending(S)
        assert abs(eigvals[0] - (-0.5)) < 1e-13
        assert abs(eigvals[1] - 0.5) < 1e-13


def test_pauli_spin_operator_zero_direction_raises():
    with pytest.raises(ValueError):
        spin.pauli_spin_operator([0.0, 0.0, 0.0])


def test_pauli_spin_operator_wrong_shape_raises():
    with pytest.raises(ValueError):
        spin.pauli_spin_operator([1.0, 0.0])


def test_pauli_anti_commute_cross_pairs():
    """σ_i σ_j = -σ_j σ_i for i ≠ j, i.e. σ_iσ_j + σ_jσ_i = 0 (exact)."""
    sx, sy, sz = spin.pauli_matrices()
    pairs = [(sx, sy), (sy, sz), (sx, sz)]
    for a, b in pairs:
        assert _max_abs_combo(
            (1, mat_matmul(a, b)), (1, mat_matmul(b, a))
        ) < 1e-14
