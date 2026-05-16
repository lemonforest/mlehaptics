"""Tests for srmech.qm.sm (electroweak, Higgs, Yukawa, CKM)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from srmech.qm import sm


# ----------------------------------------------------------------------
# Higgs
# ----------------------------------------------------------------------


def test_higgs_vev_formula():
    """v = sqrt(μ² / (2λ))."""
    v = sm.higgs_vev(mu_squared=4.0, lam=0.5)
    assert abs(v - math.sqrt(4.0 / 1.0)) < 1e-14


def test_higgs_potential_at_vev_is_minimum():
    """V(v) < V(φ) for φ near but not at v."""
    mu_sq, lam = 1.0, 0.25
    v = sm.higgs_vev(mu_sq, lam)
    V_at_vev = sm.higgs_potential(v + 0.0j, mu_sq, lam)
    V_at_zero = sm.higgs_potential(0.0 + 0.0j, mu_sq, lam)
    V_at_2vev = sm.higgs_potential(2.0 * v + 0.0j, mu_sq, lam)
    assert V_at_vev < V_at_zero
    assert V_at_vev < V_at_2vev


def test_higgs_potential_value_at_vev():
    """V(v) = -μ⁴ / (4λ) at the minimum."""
    mu_sq, lam = 2.0, 0.5
    v = sm.higgs_vev(mu_sq, lam)
    V_min = sm.higgs_potential(v + 0.0j, mu_sq, lam)
    expected = -(mu_sq ** 2) / (4.0 * lam)
    assert abs(V_min - expected) < 1e-13


def test_higgs_vev_invalid_inputs():
    with pytest.raises(ValueError):
        sm.higgs_vev(mu_squared=-1.0, lam=0.5)
    with pytest.raises(ValueError):
        sm.higgs_vev(mu_squared=1.0, lam=0.0)


# ----------------------------------------------------------------------
# Electroweak
# ----------------------------------------------------------------------


def test_weak_mixing_angle_simple():
    """tan θ_W = g'/g."""
    theta = sm.weak_mixing_angle(g=1.0, g_prime=1.0)
    assert abs(theta - math.pi / 4) < 1e-14


def test_w_boson_mass_formula():
    """M_W = g v / 2."""
    MW = sm.w_boson_mass(g=0.65, vev=246.0)
    assert abs(MW - 0.65 * 246.0 / 2.0) < 1e-12


def test_z_boson_mass_formula():
    """M_Z = v sqrt(g² + g'²) / 2."""
    g, g_prime, v = 0.65, 0.35, 246.0
    MZ = sm.z_boson_mass(g, g_prime, v)
    expected = v * math.sqrt(g * g + g_prime * g_prime) / 2.0
    assert abs(MZ - expected) < 1e-12


def test_weinberg_relation():
    """M_W = M_Z cos θ_W at machine precision (tree-level identity)."""
    for g, g_prime, v in [
        (0.65, 0.35, 246.0),
        (0.5, 0.5, 100.0),
        (1.0, 0.1, 50.0),
    ]:
        residual = sm.weinberg_relation_residual(g, g_prime, v)
        assert residual < 1e-12


def test_electroweak_summary_consistency():
    """Bundle returns self-consistent observables."""
    summary = sm.electroweak_summary(g=0.65, g_prime=0.35, vev=246.0)
    MW, MZ, cosW = summary["M_W"], summary["M_Z"], summary["cos_theta_W"]
    assert abs(MW - MZ * cosW) < 1e-12
    # sin²(θ_W) + cos²(θ_W) = 1
    sin_sq = summary["sin_theta_W"] ** 2
    cos_sq = summary["cos_theta_W"] ** 2
    assert abs(sin_sq + cos_sq - 1.0) < 1e-14


def test_electroweak_invalid_couplings():
    with pytest.raises(ValueError):
        sm.w_boson_mass(g=0.0, vev=246.0)
    with pytest.raises(ValueError):
        sm.z_boson_mass(g=0.5, g_prime=0.0, vev=246.0)


# ----------------------------------------------------------------------
# Yukawa
# ----------------------------------------------------------------------


def test_fermion_mass_from_yukawa_formula():
    """m_f = y_f v / sqrt(2)."""
    m_f = sm.fermion_mass_from_yukawa(yukawa=0.01, vev=246.0)
    expected = 0.01 * 246.0 / math.sqrt(2.0)
    assert abs(m_f - expected) < 1e-12


def test_fermion_mass_zero_yukawa():
    """Massless fermion at y = 0."""
    assert sm.fermion_mass_from_yukawa(yukawa=0.0, vev=246.0) == 0.0


def test_fermion_mass_invalid_vev():
    with pytest.raises(ValueError):
        sm.fermion_mass_from_yukawa(yukawa=0.01, vev=0.0)


# ----------------------------------------------------------------------
# CKM
# ----------------------------------------------------------------------


def test_ckm_identity_for_zero_angles():
    """CKM(0,0,0,0) = I_3."""
    V = sm.ckm_matrix(0.0, 0.0, 0.0, 0.0)
    np.testing.assert_allclose(V, np.eye(3, dtype=complex), atol=1e-14)


def test_ckm_unitary():
    """V V† = I for any mixing angles + CP phase."""
    V = sm.ckm_matrix(theta_12=0.227, theta_13=0.003, theta_23=0.042, delta_cp=1.20)
    np.testing.assert_allclose(V @ V.conj().T, np.eye(3, dtype=complex), atol=1e-13)


def test_ckm_unitarity_residual_small():
    """ckm_unitarity_residual returns ~0 for our parameterization."""
    V = sm.ckm_matrix(0.5, 0.2, 0.3, 0.7)
    assert sm.ckm_unitarity_residual(V) < 1e-13


def test_ckm_only_cabibbo_2x2_block():
    """If θ_13 = θ_23 = 0, V reduces to a Cabibbo-like 2×2 block."""
    V = sm.ckm_matrix(theta_12=0.4, theta_13=0.0, theta_23=0.0, delta_cp=0.5)
    # Top-left 2x2 block should be the Cabibbo rotation matrix.
    c12 = math.cos(0.4)
    s12 = math.sin(0.4)
    expected_2x2 = np.array([[c12, s12], [-s12, c12]], dtype=complex)
    np.testing.assert_allclose(V[:2, :2], expected_2x2, atol=1e-13)
    # Bottom-right should be 1.
    assert abs(V[2, 2] - 1.0) < 1e-14
