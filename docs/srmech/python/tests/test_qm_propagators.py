"""Tests for srmech.qm.propagators (Feynman propagators) — numpy-FREE (#564).

propagators flipped numpy-free at v0.7.5rc123: the 4×4 propagator numerators are
held in the framework-native :class:`~srmech.amsc.mat.Mat` carrier (consumed
straight from the numpy-free :mod:`srmech.qm.relativistic` producers), so these
tests assert the canonical propagator identities directly via ``Mat``-entry /
``mat_matmul`` / plain ``complex`` arithmetic — **no numpy, no ``.to_numpy()``**
oracle. The two relativistic-producer calls that previously bridged
``.to_numpy()`` (rc118) now consume the ``Mat`` directly.
"""

from __future__ import annotations

import math

import pytest

from srmech.amsc.laplacian import mat_matmul, mat_norm
from srmech.amsc.mat import Mat
from srmech.qm import propagators as prop
from srmech.qm import relativistic as rel


# ----------------------------------------------------------------------
# numpy-free helpers
# ----------------------------------------------------------------------


def _eye4_complex() -> "Mat":
    """The 4×4 complex identity ``I_4`` as a ``Mat`` (numpy-free)."""
    return Mat.from_rows(
        [[1.0 if i == j else 0.0 for j in range(4)] for i in range(4)],
        is_complex=True,
    )


def _mat_max_abs_diff(a: "Mat", b: "Mat") -> float:
    """Max element-wise modulus of ``A − B`` (numpy-free; tolerance oracle).

    ``abs()`` is permitted here — this is a TEST tolerance, not a cascade op."""
    worst = 0.0
    for i in range(a.n_rows):
        for j in range(a.n_cols):
            worst = max(worst, abs(complex(a[i, j]) - complex(b[i, j])))
    return worst


# ----------------------------------------------------------------------
# Scalar propagator
# ----------------------------------------------------------------------


def test_scalar_propagator_off_shell():
    """G_F(k²) = i / (k² - m²) off-shell."""
    G = prop.feynman_scalar_propagator(k_squared=10.0, m=1.0)
    expected = 1j / (10.0 - 1.0)
    assert abs(G - expected) < 1e-14


def test_scalar_propagator_on_shell_requires_epsilon():
    """On-shell k² = m² with epsilon=0 raises."""
    with pytest.raises(ValueError):
        prop.feynman_scalar_propagator(k_squared=4.0, m=2.0, epsilon=0.0)


def test_scalar_propagator_on_shell_with_epsilon():
    """With epsilon > 0, on-shell value is finite."""
    G = prop.feynman_scalar_propagator(k_squared=4.0, m=2.0, epsilon=1e-6)
    assert math.isfinite(G.real) and math.isfinite(G.imag)


def test_scalar_propagator_massless():
    """At m = 0: G(k²) = i / k²."""
    G = prop.feynman_scalar_propagator(k_squared=5.0, m=0.0)
    assert abs(G - 1j / 5.0) < 1e-14


def test_scalar_propagator_negative_mass_rejected():
    with pytest.raises(ValueError):
        prop.feynman_scalar_propagator(k_squared=1.0, m=-1.0)


# ----------------------------------------------------------------------
# Fermion propagator
# ----------------------------------------------------------------------


def test_fermion_propagator_off_shell_shape():
    """S_F(k) is a 4×4 complex ``Mat``."""
    k = [2.0, 1.0, 0.0, 0.0]
    S = prop.feynman_fermion_propagator(k, m=1.0)
    assert isinstance(S, Mat)
    assert S.shape == (4, 4)
    assert S.is_complex


def test_fermion_propagator_inverse_is_dirac_operator():
    """For off-shell k, (γ·k - m) S_F(k) = i I_4.

    The Dirac operator is the inverse of the fermion propagator up to the
    ``i`` of the iε prescription: ``(γ^μ k_μ - m) S_F(k) = i I_4``."""
    k = [3.0, 1.0, 0.0, 0.0]
    m = 1.0
    S = prop.feynman_fermion_propagator(k, m)
    # relativistic.* return numpy-free `Mat` (rc118) — consume directly (no
    # `.to_numpy()` bridge; propagators flipped numpy-free at rc123, #564).
    D = rel.dirac_operator_momentum_space(k, m)            # γ^μ k_μ - m I (Mat)
    product = mat_matmul(D, S)                             # Class-L matmul cascade
    target = Mat.from_rows(
        [[1j if i == j else 0.0 for j in range(4)] for i in range(4)],
        is_complex=True,
    )                                                     # i I_4
    diff = Mat.from_rows(
        [[product[i, j] - target[i, j] for j in range(4)] for i in range(4)],
        is_complex=True,
    )
    assert mat_norm(diff) < 1e-12


def test_fermion_propagator_clifford_pole_structure():
    """(p̸ + m)(p̸ - m) = (k² - m²) I_4 — the Clifford identity behind the pole.

    Multiplying the fermion-propagator numerator ``(γ·k + m)`` by ``(γ·k - m)``
    must give the scalar denominator ``(k² - m²)`` times the identity. This is
    why ``S_F`` reduces to the scalar pole on the diagonal."""
    k = [3.0, 1.0, 0.0, 0.0]
    m = 1.0
    slash_plus_m = rel.dirac_operator_momentum_space(k, -m)   # γ·k + m I (Mat)
    slash_minus_m = rel.dirac_operator_momentum_space(k, m)   # γ·k - m I (Mat)
    product = mat_matmul(slash_plus_m, slash_minus_m)
    k_sq = rel.four_momentum_squared(k)                       # k² (numpy-free)
    expected = Mat.from_rows(
        [[(k_sq - m * m) if i == j else 0.0 for j in range(4)] for i in range(4)],
        is_complex=True,
    )
    assert _mat_max_abs_diff(product, expected) < 1e-12


def test_fermion_propagator_on_shell_singular():
    """At k² = m², propagator with epsilon=0 raises."""
    k = [1.0, 0.0, 0.0, 0.0]  # k² = 1
    with pytest.raises(ValueError):
        prop.feynman_fermion_propagator(k, m=1.0, epsilon=0.0)


# ----------------------------------------------------------------------
# Photon propagator
# ----------------------------------------------------------------------


def test_photon_propagator_feynman_gauge_value():
    """In Feynman gauge: D^{μν} = -i g^{μν} / k²; a 4×4 ``Mat``."""
    D = prop.feynman_photon_propagator(k_squared=2.0)
    assert isinstance(D, Mat)
    assert D.shape == (4, 4)
    # -i g^{μν} / 2 — consume the numpy-free Minkowski Mat directly (rc118).
    eta = rel.minkowski_metric()
    expected = Mat.from_rows(
        [[-1j * eta[i, j] / 2.0 for j in range(4)] for i in range(4)],
        is_complex=True,
    )
    assert _mat_max_abs_diff(D, expected) < 1e-14


def test_photon_propagator_transverse_diagonal():
    """Feynman-gauge diagonal carries the mostly-minus metric signature.

    ``D^{00} = -i/k²`` (time), ``D^{ii} = +i/k²`` (space) — the η = diag(+,-,-,-)
    signature shows directly in the propagator diagonal."""
    D = prop.feynman_photon_propagator(k_squared=4.0)
    assert abs(D[0, 0] - (-1j / 4.0)) < 1e-14         # time-time: -i/k²
    for i in (1, 2, 3):
        assert abs(D[i, i] - (1j / 4.0)) < 1e-14      # space-space: +i/k²


def test_photon_propagator_on_shell_requires_epsilon():
    """Photon on-shell k² = 0 with epsilon=0 raises."""
    with pytest.raises(ValueError):
        prop.feynman_photon_propagator(k_squared=0.0, epsilon=0.0)


def test_photon_propagator_general_gauge():
    """In general gauge with k_squared > 0 and explicit k, the additional
    gauge-dependent k^μ k^ν term contributes — D differs from Feynman gauge."""
    k = [2.0, 1.0, 0.0, 0.0]
    k_squared = rel.four_momentum_squared(k)
    D_feyn = prop.feynman_photon_propagator(k_squared=k_squared, gauge_xi=0.0)
    D_xi = prop.feynman_photon_propagator(
        k_squared=k_squared, gauge_xi=0.5, k=k
    )
    # Should differ by the gauge term (some entry differs beyond tolerance).
    assert _mat_max_abs_diff(D_feyn, D_xi) > 1e-9


def test_photon_propagator_general_gauge_kk_term():
    """The general-gauge correction is exactly ``+i(1-ξ) k^μ k^ν / (k²)²``.

    D_ξ = D_feyn - [-i(1-ξ) k^μ k^ν / (k²)²], so check the (0,1) component."""
    k = [2.0, 1.0, 0.0, 0.0]
    xi = 0.5
    k_sq = rel.four_momentum_squared(k)
    D_feyn = prop.feynman_photon_propagator(k_squared=k_sq, gauge_xi=0.0)
    D_xi = prop.feynman_photon_propagator(k_squared=k_sq, gauge_xi=xi, k=k)
    # gauge_term_{μν} = -i (1-ξ) k_μ k_ν / (k²)²  ⇒  D_ξ - D_feyn = -gauge_term.
    expected_correction = 1j * (1.0 - xi) * k[0] * k[1] / (k_sq * k_sq)
    assert abs((D_xi[0, 1] - D_feyn[0, 1]) - expected_correction) < 1e-13


# ----------------------------------------------------------------------
# Massive vector propagator
# ----------------------------------------------------------------------


def test_massive_vector_propagator_shape():
    k = [3.0, 1.0, 0.0, 0.0]
    D = prop.feynman_massive_vector_propagator(k, m=2.0)
    assert isinstance(D, Mat)
    assert D.shape == (4, 4)
    assert D.is_complex


def test_massive_vector_propagator_zero_mass_rejected():
    k = [3.0, 1.0, 0.0, 0.0]
    with pytest.raises(ValueError):
        prop.feynman_massive_vector_propagator(k, m=0.0)


def test_massive_vector_propagator_on_shell_requires_epsilon():
    """At k² = m² with epsilon=0, raises."""
    m = 2.0
    k = [m, 0.0, 0.0, 0.0]  # k² = m²
    with pytest.raises(ValueError):
        prop.feynman_massive_vector_propagator(k, m, epsilon=0.0)


def test_massive_vector_propagator_off_shell_includes_kk_term():
    """The k^μ k^ν / m² term shows up in the numerator."""
    m = 1.0
    k = [2.0, 0.5, 0.0, 0.0]
    D = prop.feynman_massive_vector_propagator(k, m, epsilon=0.0)
    # Numerator: g^{μν} - k^μ k^ν / m². Verify the (0,1) component.
    k_sq = rel.four_momentum_squared(k)
    denom = k_sq - m * m
    expected_01 = -1j * (0.0 - k[0] * k[1] / (m * m)) / denom
    assert abs(D[0, 1] - expected_01) < 1e-13
