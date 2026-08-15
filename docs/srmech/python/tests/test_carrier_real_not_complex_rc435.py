"""rc435 (`#T1140`) — the real-carrier ratchet, and the boundary that bounds it.

gh #1530 §N, SPACE half: *the container must not declare more degrees of freedom
than the object has.* ``hydrogen_radial`` built a provably-real tridiagonal
Hamiltonian and then declared a COMPLEX carrier for it — 2× the buffer, and on
the numpy-free fallback path a real-symmetric matrix sent through the complex
Jacobi's real ``2n×2n`` embedding instead of the direct ``n×n`` one. rc435 flips
that carrier to ``is_complex=False``.

**THE FINDING THAT BOUNDS THE FIX — measured, and it refutes the framing the
change was filed under.** On the pure path ``is_complex`` is NOT a storage
declaration. It is an **ALGORITHM SELECTOR**: :func:`_hermitian_eig_py` branches
``if not h.is_complex`` to the direct ``n×n`` Jacobi, else to the real ``2n×2n``
embedding. Those are different rotation sequences over different matrices, so
they accumulate rounding differently. Measured consequence:

  * eigenVALUES are **bit-identical** between the two carriers (both arms) — so
    ``hydrogen_radial``'s energies, the physically meaningful return, do not move;
  * eigenVECTORS differ at ~1e-14 on the PURE arm, and **not merely by sign**;
  * on the NATIVE arm nothing moves at all, because the C entry ignores the flag
    (``_mat_to_interleaved_cbuf`` widens unconditionally), so both carriers run
    the identical complex kernel on the identical doubles.

That eigenvector movement is inside the op's declared contract, which pins
"eigenvalues + reconstruction + unitarity, NOT element-wise parity — an
eigenvector is fixed only up to a unit-modulus phase". And it moves the pure arm
*toward* the native one (measured: pure eigvec[0][0] was 0.5740264305118639 and
native 0.5740264305118833; after the flip pure reads 0.5740264305118833 — an
exact match), so the flip CLOSES a pure/native projection gap rather than opening
one.

So this file ratchets the claims that are actually true and load-bearing:
eigenvalues by ``==``, eigenvectors by the op's real contract. It does NOT assert
element-wise eigenvector parity, because that is false and a gate asserting it
would be pinning a coincidence.

The discriminator is proved REAL rather than permissive by
:func:`test_gate_fires_on_a_genuinely_complex_matrix` — forcing the same
conversion where the imaginary axis DOES carry content moves the spectrum.

numpy-free; no ``abs()`` (Class-K sign pin + Class-C re-application); no stdlib
``math`` / ``fractions`` / ``decimal``.
"""

import inspect

from srmech.math.mat import Mat
from srmech.math.laplacian import mat_hermitian_eigendecompose
from srmech.physics.qm import potentials
from srmech.signal_processing.closed_form_ops import ica_jade


# ---------------------------------------------------------------------------
# helpers (no abs(): Class-K sign pin + Class-C re-application)
# ---------------------------------------------------------------------------


def _kc_mag(x):
    """``|x|`` via the Class-K pin-slot sign branch + Class-C re-application."""
    return -x if x < 0.0 else x


def _hydrogen_rows(n_grid, r_max=45.0, l_quantum=0):
    """The EXACT rows ``hydrogen_radial`` builds, rebuilt independently so the
    gate compares carriers on identical data rather than trusting the op to have
    built what we think it did."""
    dr = r_max / (n_grid + 1)
    inv_2dr2 = 1.0 / (2.0 * dr * dr)
    lcent = l_quantum * (l_quantum + 1)
    rows = [[0.0] * n_grid for _ in range(n_grid)]
    for i in range(n_grid):
        ri = (i + 1) * dr
        rows[i][i] = 2.0 * inv_2dr2 + lcent / (2.0 * ri * ri) - 1.0 / ri
        if i + 1 < n_grid:
            rows[i][i + 1] = -inv_2dr2
            rows[i + 1][i] = -inv_2dr2
    return rows


def _eig(rows, is_complex):
    h = Mat.from_rows(rows, is_complex=is_complex)
    ev, vecs = mat_hermitian_eigendecompose(h)
    n = vecs.n_rows
    return [ev[i, 0] for i in range(n)], vecs


# ---------------------------------------------------------------------------
# THE RATCHET — eigenvalues, by `==`, not by a tolerance
# ---------------------------------------------------------------------------


def test_hydrogen_hamiltonian_eigenvalues_are_bit_identical_across_carriers():
    """The claim the storage fix actually rests on: dropping the unused
    imaginary axis does not move a single eigenvalue bit."""
    for n_grid in (20, 45):
        rows = _hydrogen_rows(n_grid)
        vals_cplx, _ = _eig(rows, True)
        vals_real, _ = _eig(rows, False)
        assert vals_real == vals_cplx, (
            f"hydrogen H spectrum MOVED at n_grid={n_grid} when the carrier "
            f"dropped its unused imaginary axis")


def test_hydrogen_radial_energies_match_the_complex_carrier_reference():
    """END-TO-END on the shipped op: the returned energies must equal, exactly,
    what the pre-rc435 complex carrier produced on the same grid."""
    n_grid, r_max = 60, 45.0
    _r, energies, _vecs = potentials.hydrogen_radial(n_grid=n_grid, r_max=r_max)
    ref_vals, _ = _eig(_hydrogen_rows(n_grid, r_max), True)
    assert energies == ref_vals, (
        "hydrogen_radial's energies MOVED against the complex-carrier reference")


def test_real_carrier_eigenvectors_satisfy_the_ops_actual_contract():
    """Eigenvectors are pinned the way the op pins them — reconstruction and
    orthonormality — NOT element-wise.

    This is deliberate. Element-wise parity across carriers is FALSE on the pure
    arm (the flag selects a different Jacobi), so a gate asserting it would pin a
    coincidence and would fail the moment it ran without the ``.so``.
    """
    n = 24
    rows = _hydrogen_rows(n)
    vals, vecs = _eig(rows, False)

    # V is orthonormal:  VᵀV = I
    for a in range(n):
        for b in range(n):
            dot = 0.0
            for i in range(n):
                dot += vecs[i, a].real * vecs[i, b].real
            expect = 1.0 if a == b else 0.0
            assert _kc_mag(dot - expect) < 1e-9, (
                f"eigenvectors not orthonormal at ({a},{b}): {dot}")

    # H reconstructs:  H = V·diag(λ)·Vᵀ
    for i in range(n):
        for j in range(n):
            acc = 0.0
            for k in range(n):
                acc += vecs[i, k].real * vals[k] * vecs[j, k].real
            assert _kc_mag(acc - rows[i][j]) < 1e-9, (
                f"reconstruction failed at ({i},{j})")


# ---------------------------------------------------------------------------
# FIRING PROOF — the discriminator is real, not permissive
# ---------------------------------------------------------------------------


def test_gate_fires_on_a_genuinely_complex_matrix():
    """NEGATIVE CONTROL. The same real-cast, applied where the imaginary axis DOES
    carry content, must MOVE the spectrum.

    ``σ_y = [[0, -i], [i, 0]]`` has spectrum ``{-1, +1}``; real-cast it becomes
    the zero matrix, spectrum ``{0, 0}``. If this ever passed, the assertions
    above would be vacuous — they would be confirming that dropping the imaginary
    axis never matters, which is false.
    """
    sigma_y = [[0j, -1j], [1j, 0j]]
    vals_cplx, _ = _eig(sigma_y, True)
    vals_real, _ = _eig(sigma_y, False)
    assert vals_real != vals_cplx, (
        "real-casting σ_y did NOT change its spectrum — the bit-identity "
        "assertions above are therefore vacuous and prove nothing")
    assert _kc_mag(vals_cplx[0] - (-1.0)) < 1e-12
    assert _kc_mag(vals_cplx[1] - 1.0) < 1e-12
    assert vals_real == [0.0, 0.0]


# ---------------------------------------------------------------------------
# THE BOUNDARY — why ica_jade is deliberately NOT converted
# ---------------------------------------------------------------------------


def test_is_complex_is_an_algorithm_selector_on_the_pure_path():
    """PIN THE FINDING, so the reason ica_jade was left alone cannot be lost.

    ``_hermitian_eig_py`` branches on the carrier flag. That makes the flag an
    algorithm selector on the numpy-free path, not a storage declaration — which
    is why "flip every provably-real carrier" is NOT a safe blanket rewrite.
    """
    from srmech.math import laplacian

    src = inspect.getsource(laplacian._hermitian_eig_py)
    assert "if not h.is_complex:" in src, (
        "_hermitian_eig_py no longer branches on the carrier flag — re-measure "
        "whether a real-carrier flip is now genuinely storage-only, and update "
        "the ica_jade note in this file and at its call site")


def test_ica_jade_covariance_deliberately_stays_on_a_complex_carrier():
    """``cov`` is provably real, but flipping it changes the SHIPPED OUTPUT at
    O(1) on the pure arm: the JADE Givens sweep is threshold-driven
    (``_abs(theta) < tol`` decides whether a rotation happens), so a ~1e-14
    change in the whitening basis is amplified. Measured W[0][0]: -0.01280
    before, 0.13968 after. Valid separation either way, but a reproducibility
    change — not a storage-only one — so it does not ride this rc.
    """
    src = inspect.getsource(ica_jade)
    assert "Mat.from_rows(cov, is_complex=True)" in src, (
        "ica_jade's covariance carrier was flipped — that changes the shipped "
        "W/S at O(1) on the numpy-free path. If this is intended, it needs its "
        "own rc with the output change stated in the CHANGELOG, not a "
        "storage-only one")
    assert "ALGORITHM SELECTOR" in src, (
        "the rc435 note explaining WHY this carrier stays complex was removed; "
        "without it the site reads as an un-caught defect and will be "
        "'fixed' again")


# ---------------------------------------------------------------------------
# REGRESSION PINS
# ---------------------------------------------------------------------------


def test_hydrogen_radial_declares_a_real_carrier():
    """Pin the fix at the source so it cannot silently re-promote."""
    src = inspect.getsource(potentials.hydrogen_radial)
    assert "Mat.from_rows(rows, is_complex=False)" in src, (
        "hydrogen_radial re-promoted its real Hamiltonian to a complex carrier")


def test_hydrogen_radial_return_contract_unchanged():
    """The public return is unchanged: eigenvectors are still a REAL Mat.

    This is the check that would have caught deleting the ``.real`` extraction as
    "now redundant" — the Class-L primitive returns ALWAYS-complex eigenvectors
    regardless of the input carrier, so that extraction is what makes the return
    real, and it is NOT made redundant by the real input carrier.
    """
    r, energies, vecs = potentials.hydrogen_radial(n_grid=120, r_max=45.0)
    assert len(r) == 120 and len(energies) == 120
    assert isinstance(vecs, Mat)
    assert vecs.is_complex is False, (
        "hydrogen_radial must still return REAL eigenvectors")
    # the 1s binding energy — the one piece of physics in the contract. n_grid
    # must actually resolve it: the finite-grid error is O(dr²), so a coarse grid
    # reads ≈ -0.33 and says nothing about the carrier.
    assert -0.6 < energies[0] < -0.4


def test_primitive_returns_complex_eigenvectors_for_a_real_carrier():
    """The contract the fix depends on, asserted rather than assumed."""
    rows = _hydrogen_rows(12)
    _vals, vecs = _eig(rows, False)
    assert vecs.is_complex is True, (
        "mat_hermitian_eigendecompose stopped returning complex eigenvectors "
        "for a real input — hydrogen_radial's .real extraction may now be "
        "redundant, or worse, wrong")
