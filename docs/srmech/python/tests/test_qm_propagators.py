"""Tests for srmech.qm.propagators (Feynman propagators)."""

from __future__ import annotations

import numpy as np
import pytest

from srmech.qm import propagators as prop
from srmech.qm import relativistic as rel


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
    assert np.isfinite(G.real) and np.isfinite(G.imag)


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
    """S_F(k) is a 4×4 complex matrix."""
    k = np.array([2.0, 1.0, 0.0, 0.0])
    S = prop.feynman_fermion_propagator(k, m=1.0)
    assert S.shape == (4, 4)
    assert S.dtype == complex


def test_fermion_propagator_inverse_is_dirac_operator():
    """For off-shell k, (γ·k - m) S_F(k) = i I_4."""
    k = np.array([3.0, 1.0, 0.0, 0.0])
    m = 1.0
    S = prop.feynman_fermion_propagator(k, m)
    D = rel.dirac_operator_momentum_space(k, m)
    np.testing.assert_allclose(D @ S, 1j * np.eye(4), atol=1e-12)


def test_fermion_propagator_on_shell_singular():
    """At k² = m², propagator with epsilon=0 raises."""
    k = np.array([1.0, 0.0, 0.0, 0.0])  # k² = 1
    with pytest.raises(ValueError):
        prop.feynman_fermion_propagator(k, m=1.0, epsilon=0.0)


# ----------------------------------------------------------------------
# Photon propagator
# ----------------------------------------------------------------------


def test_photon_propagator_feynman_gauge_shape():
    """In Feynman gauge: D^{μν} = -i g^{μν} / k²; 4×4 matrix."""
    D = prop.feynman_photon_propagator(k_squared=2.0)
    assert D.shape == (4, 4)
    expected = -1j * rel.minkowski_metric() / 2.0
    np.testing.assert_allclose(D, expected, atol=1e-14)


def test_photon_propagator_on_shell_requires_epsilon():
    """Photon on-shell k² = 0 with epsilon=0 raises."""
    with pytest.raises(ValueError):
        prop.feynman_photon_propagator(k_squared=0.0, epsilon=0.0)


def test_photon_propagator_general_gauge():
    """In general gauge with k_squared > 0 and explicit k, additional
    gauge-dependent term contributes."""
    k = np.array([2.0, 1.0, 0.0, 0.0])
    k_squared = rel.four_momentum_squared(k)
    D_feyn = prop.feynman_photon_propagator(k_squared=k_squared, gauge_xi=0.0)
    D_xi = prop.feynman_photon_propagator(
        k_squared=k_squared, gauge_xi=0.5, k=k
    )
    # Should differ by the gauge term.
    assert not np.allclose(D_feyn, D_xi)


# ----------------------------------------------------------------------
# Massive vector propagator
# ----------------------------------------------------------------------


def test_massive_vector_propagator_shape():
    k = np.array([3.0, 1.0, 0.0, 0.0])
    D = prop.feynman_massive_vector_propagator(k, m=2.0)
    assert D.shape == (4, 4)
    assert D.dtype == complex


def test_massive_vector_propagator_zero_mass_rejected():
    k = np.array([3.0, 1.0, 0.0, 0.0])
    with pytest.raises(ValueError):
        prop.feynman_massive_vector_propagator(k, m=0.0)


def test_massive_vector_propagator_on_shell_requires_epsilon():
    """At k² = m² with epsilon=0, raises."""
    m = 2.0
    k = np.array([m, 0.0, 0.0, 0.0])  # k² = m²
    with pytest.raises(ValueError):
        prop.feynman_massive_vector_propagator(k, m, epsilon=0.0)


def test_massive_vector_propagator_off_shell_includes_kk_term():
    """The k^μ k^ν / m² term shows up in the numerator."""
    m = 1.0
    k = np.array([2.0, 0.5, 0.0, 0.0])
    D = prop.feynman_massive_vector_propagator(k, m, epsilon=0.0)
    # Numerator: g^{μν} - k^μ k^ν / m². Verify the (0,1) component.
    k_sq = rel.four_momentum_squared(k)
    denom = k_sq - m * m
    expected_01 = -1j * (0.0 - k[0] * k[1] / (m * m)) / denom
    assert abs(D[0, 1] - expected_01) < 1e-13
