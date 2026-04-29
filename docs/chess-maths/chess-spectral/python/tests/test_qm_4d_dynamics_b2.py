"""Unit tests for chess_spectral.qm_4d_dynamics — Phase 4 milestone B2.

Covers the free-Hamiltonian Zeno-style time-evolution layer (per
ADR-002 Option A § 3.1):

  1. ``H_FREE_4D`` shape and Hermiticity (real-symmetric, eigvals ≤ 0).
  2. Spectrum matches the Kron-sum of P_8 1D eigenvalues from Pre-flight 3
     (``tables_4d.kron_sum4_eigvals``) at machine precision.
  3. Norm preservation under :func:`evolve_under_h0` for random ``ψ``
     and various ``t`` (anti-Hermitian generator -> unitary U).
  4. Energy conservation (Heisenberg picture):
     ``<ψ_t|H_0|ψ_t> == <ψ_0|H_0|ψ_0>``.
  5. Time-reversal invariance: ``U(-t) U(t) = I``.
  6. Composition: ``U(t1) U(t2) = U(t1 + t2)``.
  7. Channel-restricted evolution leaves other 10 channels untouched.
  8. Free-Hamiltonian eigenstate phase rotation:
     ``ψ_k(t) = exp(-i E_k t) ψ_k(0)``.

Phase 3.5 / ADR-002 references hard-coded into the spec:

  * ADR-002 §3.1 — H_0 = -Δ_{P_8^4} as the free Hamiltonian for the
    Zeno-style time evolution between move boundaries.
  * Pre-flight 3 — encoder is the simultaneous eigenbasis of (Δ, B_4
    commutant). Used as the test oracle for the spectrum match (test 2)
    and for the eigenstate phase-rotation check (test 8).

Run with ``pytest tests/test_qm_4d_dynamics_b2.py -v`` from python/.
"""
from __future__ import annotations

import os
import sys
from typing import List, Tuple

import numpy as np
import pytest
import scipy.sparse as sp

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

from chess_spectral import encoder_4d as _enc4    # noqa: E402
from chess_spectral import qm_4d_dynamics as dyn  # noqa: E402
from chess_spectral import tables_4d as _t4       # noqa: E402


# ---- Tolerances -----------------------------------------------------

# Project-standard 1e-10 for B2 tests (Pre-flight 3 reports 1e-13 on
# the spectrum identity itself; we use a slightly loose 1e-10 here so
# we don't trip on Krylov-subspace truncation in expm_multiply, which
# is the primary noise source in evolution tests).
TOL = 1e-10
RNG_SEED = 20260429


# ---- Module-scoped fixtures -----------------------------------------


@pytest.fixture(scope='module')
def H0() -> sp.csr_matrix:
    """The cached H_FREE_4D singleton."""
    return dyn.H_FREE_4D


@pytest.fixture(scope='module')
def H0_dense(H0: sp.csr_matrix) -> np.ndarray:
    """Dense form for energy-expectation comparisons. 4096x4096 fits in
    ~256 MB for complex128 — well within memory budget."""
    return H0.toarray()


@pytest.fixture(scope='module')
def random_states_4096() -> List[np.ndarray]:
    """20 independent random unit-norm psi vectors in C^4096."""
    rng = np.random.default_rng(RNG_SEED)
    out: List[np.ndarray] = []
    for _ in range(20):
        v = rng.standard_normal(4096) + 1j * rng.standard_normal(4096)
        v /= np.linalg.norm(v)
        out.append(v.astype(np.complex128))
    return out


@pytest.fixture(scope='module')
def evolution_times() -> List[float]:
    """The four representative t values exercised across tests."""
    return [0.1, 1.0, 5.0, 10.0]


# ---- 1. Shape and Hermiticity --------------------------------------


def test_b2_h_free_shape(H0: sp.csr_matrix) -> None:
    """H_FREE_4D is a 4096x4096 complex128 sparse matrix.

    The 4096-dim block size matches `CHANNEL_DIM` from the encoder
    (since H_0 acts on the per-channel 4096-mode space). Dtype is
    complex128 throughout the QM module per the convention announced
    in qm_4d.py.
    """
    assert H0.shape == (4096, 4096), f"H0 shape {H0.shape} != (4096, 4096)"
    assert H0.dtype == np.complex128, f"H0 dtype {H0.dtype} != complex128"
    assert sp.issparse(H0), "H_FREE_4D must be sparse for memory budget"


def test_b2_h_free_hermitian(H0: sp.csr_matrix) -> None:
    """H_0 = -Δ is real-symmetric, therefore Hermitian.

    Since Δ is built from a 1D path-graph Laplacian (real-symmetric)
    via Kronecker sum, the result is exactly real-symmetric -- not
    just within tolerance. We assert nnz of H - H^† is zero (no
    floating-point drift).
    """
    diff = H0 - H0.conj().T
    diff.eliminate_zeros()
    assert diff.nnz == 0, (
        f"H_FREE_4D not Hermitian: H - H^† has {diff.nnz} nonzero "
        f"entries (max |diff| = {np.max(np.abs(diff.data)) if diff.nnz else 0})"
    )


def test_b2_h_free_eigvals_nonpositive(H0_dense: np.ndarray) -> None:
    """All eigvals of H_0 = -Δ are real and non-positive (within float
    precision). Δ is positive-semidefinite, so -Δ is negative-
    semidefinite. The largest eigval should be ~0 (Δ has a zero mode:
    the constant vector). The smallest is -spectral_radius(Δ).
    """
    eigs = np.linalg.eigvalsh(H0_dense)
    # Real part imaginary check
    assert np.allclose(eigs.imag, 0.0, atol=TOL), (
        f"H_0 has complex eigvals (max |imag| = {np.max(np.abs(eigs.imag))})"
    )
    # Largest eigenvalue should be ~0 (the zero mode of Δ)
    assert eigs.max() < TOL, (
        f"H_0 has positive eigval {eigs.max()} > {TOL}"
    )
    # Smallest eigval matches the negation of Δ's spectral radius
    # which is 4 * 3.84776 ≈ -15.39 (since Δ_{P_8} has max eigval
    # ~3.84776 and Kron-sum scales linearly with dim).
    expected_min = -4 * 3.847759065022573
    assert abs(eigs.min() - expected_min) < TOL, (
        f"H_0 min eigval {eigs.min()} != expected {expected_min} "
        f"(diff {eigs.min() - expected_min})"
    )


# ---- 2. Spectrum match against Kron-sum from Pre-flight 3 ----------


def test_b2_spectrum_matches_kron_sum_4d(H0_dense: np.ndarray) -> None:
    """The eigenvalues of -H_0 (= Δ) match the Kron-sum of the P_8 1D
    eigenvalues exactly (to 1e-10).

    Pre-flight 3 result: P_8 1D spectrum is
    ``[0, 0.15224, 0.58579, 1.23463, 2.0, 2.76537, 3.41421, 3.84776]``.
    The 4D spectrum of Δ_{P_8^4} is the Kronecker sum (every quadruple
    sum ``λ_i + λ_j + λ_k + λ_l``). H_0 = -Δ has the negation, so
    eigvals(-H_0) should match the Kron-sum directly.

    Source of truth: :func:`tables_4d.kron_sum4_eigvals`.
    """
    eigs_neg_h = np.linalg.eigvalsh(-H0_dense)  # spectrum of -H_0 = Δ

    _, evals_1d = _t4.eig_p8()
    kron_sum = _t4.kron_sum4_eigvals(evals_1d)
    kron_sum_sorted = np.sort(kron_sum)

    # eigvalsh returns sorted ascending; so does np.sort. Comparable
    # element-wise.
    assert eigs_neg_h.shape == kron_sum_sorted.shape, (
        f"shape mismatch: eigvals shape {eigs_neg_h.shape} vs "
        f"Kron-sum shape {kron_sum_sorted.shape}"
    )

    residual = np.max(np.abs(eigs_neg_h - kron_sum_sorted))
    assert residual < TOL, (
        f"spectrum residual {residual} exceeds tolerance {TOL}; "
        f"first few eigvals: H={eigs_neg_h[:5]} Kron-sum={kron_sum_sorted[:5]}; "
        f"last few: H={eigs_neg_h[-5:]} Kron-sum={kron_sum_sorted[-5:]}"
    )

    # Also: smallest eigval is exactly 0 (Δ has the constant zero mode)
    # and largest is 4 * (max P_8 eigval)
    assert abs(eigs_neg_h[0]) < TOL, f"smallest -H_0 eigval {eigs_neg_h[0]} != 0"
    assert abs(eigs_neg_h[-1] - 4 * evals_1d[-1]) < TOL, (
        f"largest -H_0 eigval {eigs_neg_h[-1]} != 4 * {evals_1d[-1]}"
    )


def test_b2_spectrum_p8_1d_matches_findings_doc() -> None:
    """The P_8 1D spectrum matches the values reported in
    research/spectral_identity_4d_findings.md.

    This is a regression check on tables_4d.eig_p8 to keep the docs
    and the test oracle in sync. The reported values are
    ``[0, 0.15224, 0.58579, 1.23463, 2.0, 2.76537, 3.41421, 3.84776]``
    (rounded to 5 decimals in the doc).
    """
    _, evals_1d = _t4.eig_p8()
    expected = np.array([
        0.0, 0.15224, 0.58579, 1.23463, 2.00000,
        2.76537, 3.41421, 3.84776,
    ])
    # 5e-5 tolerance because the doc reports to 5 decimals
    diff = np.max(np.abs(np.sort(evals_1d) - expected))
    assert diff < 5e-5, (
        f"P_8 1D spectrum drift {diff} > 5e-5; "
        f"current = {np.sort(evals_1d)}, expected = {expected}"
    )


# ---- 3. Norm preservation -------------------------------------------


def test_b2_norm_preservation(
    random_states_4096: List[np.ndarray],
    evolution_times: List[float],
) -> None:
    """For 20 random unit-norm ψ ∈ C^4096 and t ∈ {0.1, 1.0, 5.0, 10.0},
    ‖U(t)ψ‖ = 1 within 1e-10.

    Generates 80 (psi, t) pairs and asserts norm preservation per pair.
    The Krylov subspace machinery in expm_multiply has rounding error
    proportional to ‖A‖ * |t|; for our case ‖H_0‖ ≈ 15.4 and |t| ≤ 10,
    so the error scale is ~150 * eps_double ≈ 3e-14, well within TOL.
    """
    failures: List[Tuple[int, float, float]] = []
    for i, psi in enumerate(random_states_4096):
        for t in evolution_times:
            psi_t = dyn.evolve_under_h0(psi, t)
            n = float(np.linalg.norm(psi_t))
            if abs(n - 1.0) > TOL:
                failures.append((i, t, n))
    assert not failures, (
        f"norm-preservation failed for {len(failures)} (psi_idx, t) pairs: "
        f"{failures[:5]}"
    )


def test_b2_norm_preservation_full_45056(
    evolution_times: List[float],
) -> None:
    """Norm preservation extends to the full 45 056-dim case (parallel
    evolution of all 11 channels under the same H_0).
    """
    rng = np.random.default_rng(RNG_SEED + 1)
    psi = rng.standard_normal(45056) + 1j * rng.standard_normal(45056)
    psi /= np.linalg.norm(psi)
    psi = psi.astype(np.complex128)
    for t in evolution_times:
        psi_t = dyn.evolve_under_h0(psi, t)
        n = float(np.linalg.norm(psi_t))
        assert abs(n - 1.0) < TOL, (
            f"full 45056-dim norm not preserved at t={t}: ||psi||={n}"
        )


# ---- 4. Energy conservation -----------------------------------------


def test_b2_energy_conservation(
    H0_dense: np.ndarray,
    random_states_4096: List[np.ndarray],
    evolution_times: List[float],
) -> None:
    """For unitary U(t) = exp(-i H_0 t), <ψ_t|H_0|ψ_t> = <ψ_0|H_0|ψ_0>.

    This is the Heisenberg-picture statement of energy conservation
    (textbook QM). For our H_0 the spectral spread is ~15.4, so the
    expectation values land in [-15.4, 0]; the test compares them
    additively within TOL.
    """
    failures: List[Tuple[int, float, float, float]] = []
    for i, psi in enumerate(random_states_4096):
        E0 = float(np.vdot(psi, H0_dense @ psi).real)
        for t in evolution_times:
            psi_t = dyn.evolve_under_h0(psi, t)
            Et = float(np.vdot(psi_t, H0_dense @ psi_t).real)
            if abs(Et - E0) > TOL:
                failures.append((i, t, E0, Et))
    assert not failures, (
        f"energy-conservation failed for {len(failures)} pairs: "
        f"{failures[:5]}"
    )


# ---- 5. Time-reversal -----------------------------------------------


def test_b2_time_reversal(
    random_states_4096: List[np.ndarray],
    evolution_times: List[float],
) -> None:
    """U(-t) U(t) = I; equivalently evolve forward then back recovers ψ.

    Tests Frobenius residual ‖U(-t)U(t)ψ - ψ‖ < TOL for all (ψ, t).
    The error scale is twice the single-step Krylov error, still well
    within TOL.
    """
    failures: List[Tuple[int, float, float]] = []
    for i, psi in enumerate(random_states_4096):
        for t in evolution_times:
            psi_t = dyn.evolve_under_h0(psi, t)
            psi_back = dyn.evolve_under_h0(psi_t, -t)
            residual = float(np.linalg.norm(psi_back - psi))
            if residual > TOL:
                failures.append((i, t, residual))
    assert not failures, (
        f"time-reversal failed for {len(failures)} pairs: {failures[:5]}"
    )


# ---- 6. Composition -------------------------------------------------


def test_b2_composition(
    random_states_4096: List[np.ndarray],
) -> None:
    """U(t1) U(t2) = U(t1 + t2) for all t1, t2.

    Exercise a few representative time pairs across 20 ψ's. The pair
    (5.0, 5.0) -> (10.0) is the most stringent (largest |t|, so the
    Krylov truncation has the most opportunity to drift).
    """
    pairs: List[Tuple[float, float]] = [
        (0.05, 0.05),
        (0.3, 0.7),
        (1.0, 1.0),
        (5.0, 5.0),
        (-0.5, 1.5),  # one negative
    ]
    failures: List[Tuple[int, float, float, float]] = []
    for i, psi in enumerate(random_states_4096):
        for t1, t2 in pairs:
            lhs = dyn.evolve_under_h0(dyn.evolve_under_h0(psi, t1), t2)
            rhs = dyn.evolve_under_h0(psi, t1 + t2)
            residual = float(np.linalg.norm(lhs - rhs))
            if residual > TOL:
                failures.append((i, t1, t2, residual))
    assert not failures, (
        f"composition failed for {len(failures)} cases: {failures[:5]}"
    )


# ---- 7. Channel-restricted evolution --------------------------------


def test_b2_channel_restricted_a1() -> None:
    """evolve_under_h0(psi_45056, t, channel='A1') evolves only the A_1
    block; the other 10 channels are returned unchanged.
    """
    rng = np.random.default_rng(RNG_SEED + 2)
    psi = rng.standard_normal(45056) + 1j * rng.standard_normal(45056)
    psi /= np.linalg.norm(psi)
    psi = psi.astype(np.complex128)

    psi_t = dyn.evolve_under_h0(psi, 0.5, channel='A1')

    # A_1 block (indices 0..4096) should differ from input
    a1_diff = float(np.linalg.norm(psi_t[0:4096] - psi[0:4096]))
    # All other 10 blocks (indices 4096..45056) should be identical
    other_diff = float(np.linalg.norm(psi_t[4096:45056] - psi[4096:45056]))

    assert a1_diff > TOL, (
        f"A_1 block was not evolved (||diff|| = {a1_diff})"
    )
    assert other_diff < TOL, (
        f"non-A_1 channels were modified (||diff|| = {other_diff})"
    )

    # Sanity: full norm is preserved (since A_1 evolves unitarily and
    # other channels are unchanged).
    assert abs(float(np.linalg.norm(psi_t)) - 1.0) < TOL


def test_b2_channel_restricted_all_11_channels() -> None:
    """Iterate over every channel name; each restriction modifies that
    channel's 4096-block only.

    Source of truth for channel names: encoder_4d.CHANNELS_4D.
    """
    rng = np.random.default_rng(RNG_SEED + 3)
    psi = rng.standard_normal(45056) + 1j * rng.standard_normal(45056)
    psi /= np.linalg.norm(psi)
    psi = psi.astype(np.complex128)

    for name, offset in _enc4.CHANNELS_4D:
        psi_t = dyn.evolve_under_h0(psi, 0.3, channel=name)
        start = offset
        end = offset + 4096
        # That block should differ
        ch_diff = float(np.linalg.norm(psi_t[start:end] - psi[start:end]))
        # All other regions should be unchanged
        before = float(np.linalg.norm(psi_t[:start] - psi[:start]))
        after = float(np.linalg.norm(psi_t[end:] - psi[end:]))
        assert ch_diff > TOL, f"channel {name!r}: block was not evolved"
        assert before < TOL, f"channel {name!r}: block before was modified"
        assert after < TOL, f"channel {name!r}: block after was modified"


def test_b2_channel_unknown_name_raises() -> None:
    """Passing an unrecognized channel name raises ValueError."""
    rng = np.random.default_rng(RNG_SEED + 4)
    psi = rng.standard_normal(45056) + 1j * rng.standard_normal(45056)
    psi /= np.linalg.norm(psi)
    psi = psi.astype(np.complex128)
    with pytest.raises(ValueError, match="unknown channel name"):
        dyn.evolve_under_h0(psi, 0.5, channel='NOT_A_CHANNEL')


def test_b2_channel_with_4096_block_raises() -> None:
    """Passing channel='A1' with a 4096-dim block (instead of full
    45 056) is ambiguous and must raise ValueError."""
    rng = np.random.default_rng(RNG_SEED + 5)
    psi = rng.standard_normal(4096) + 1j * rng.standard_normal(4096)
    psi /= np.linalg.norm(psi)
    psi = psi.astype(np.complex128)
    with pytest.raises(ValueError, match="channel argument"):
        dyn.evolve_under_h0(psi, 0.5, channel='A1')


def test_b2_invalid_psi_shape_raises() -> None:
    """psi shapes other than (4096,) or (45056,) raise ValueError."""
    with pytest.raises(ValueError, match="psi must have shape"):
        dyn.evolve_under_h0(np.zeros(2048, dtype=np.complex128), 0.5)
    with pytest.raises(ValueError, match="psi must be 1-D"):
        dyn.evolve_under_h0(np.zeros((4096, 1), dtype=np.complex128), 0.5)


# ---- 8. Free-Hamiltonian eigenstates --------------------------------


def test_b2_eigenstate_phase_rotation(H0_dense: np.ndarray) -> None:
    """For each of the 8 lowest eigenvectors v_k of H_0,
    evolve_under_h0(v_k, t) ≈ exp(-i E_k t) v_k for various t.

    This is the textbook QM statement: in the energy basis, time
    evolution is just a per-eigenstate phase rotation. Our test
    ensures the implementation respects this for the bottom of the
    spectrum (where the eigenvalues are well-separated and the
    eigvecs are unambiguous up to global phase).

    Picks t values across [0.1, 5.0] to hit a range of phase rotations
    (E_k * t spans roughly 0..150 radians for the bottom eigenstates).
    """
    eigs, vecs = np.linalg.eigh(H0_dense)
    # The 8 lowest eigenstates (most negative eigvals).
    lowest_8 = vecs[:, :8].astype(np.complex128)
    eigs_lowest = eigs[:8]
    times = [0.1, 0.5, 1.0, 2.5, 5.0]

    failures: List[Tuple[int, float, float, float]] = []
    for k in range(8):
        v = lowest_8[:, k]
        # Normalize defensively (eigh returns orthonormal columns
        # but the type cast can introduce sub-eps drift).
        v = v / np.linalg.norm(v)
        for t in times:
            v_t = dyn.evolve_under_h0(v, t)
            expected_phase = np.exp(-1j * eigs_lowest[k] * t)
            v_expected = expected_phase * v
            residual = float(np.linalg.norm(v_t - v_expected))
            if residual > TOL:
                failures.append((k, eigs_lowest[k], t, residual))
    assert not failures, (
        f"eigenstate phase-rotation failed for {len(failures)} cases: "
        f"first few = {failures[:5]}"
    )


def test_b2_zero_mode_is_static(H0_dense: np.ndarray) -> None:
    """The constant vector (zero mode of Δ, eigval ~0 of H_0) is
    invariant under U(t) for any t. This is a stronger version of the
    eigenstate test: the t=anything phase factor is exp(0) = 1.
    """
    # Zero mode of Δ_{P_8^4} = constant vector / sqrt(4096)
    v0 = np.ones(4096, dtype=np.complex128) / np.sqrt(4096)
    # Sanity: v0 is in the kernel of H_0
    Hv = H0_dense @ v0
    assert float(np.linalg.norm(Hv)) < TOL, (
        f"v0 is not in ker(H_0): ||H v|| = {np.linalg.norm(Hv)}"
    )
    for t in (0.1, 1.0, 5.0, 10.0, -3.7):
        v_t = dyn.evolve_under_h0(v0, t)
        residual = float(np.linalg.norm(v_t - v0))
        assert residual < TOL, (
            f"zero mode drifted at t={t}: ||v_t - v_0|| = {residual}"
        )
