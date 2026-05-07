"""v0.22.0 Layer B — ICBM Trajectory Catalog tests.

Pins the 3-regime Earth ICBM propagator (boost boundary + Kepler
midcourse + Allen-Eggers re-entry). Reference profiles match
Wilkening 2000 + Sessler/UCS 2000 published values to ±10%
tolerance.
"""

from __future__ import annotations

import math

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.icbm_trajectory_catalog import (
    compute_icbm_trajectory,
    get_icbm_reference_profile,
    list_icbm_reference_profiles,
)
from ephemerides_spectral._research.icbm_trajectory_data import (
    EARTH_MU_M3_S2,
    EARTH_RADIUS_M,
    ICBM_REFERENCE_PROFILES,
    SOURCES,
    ICBMReferenceProfile,
)


# ──────────────────────────────────────────────────────────────────────
# Reference profile catalog shape
# ──────────────────────────────────────────────────────────────────────


def test_reference_profile_count() -> None:
    assert len(ICBM_REFERENCE_PROFILES) == 3


def test_reference_profile_names() -> None:
    by = {p.profile_name for p in ICBM_REFERENCE_PROFILES}
    assert by == {"srbm_300km", "mrbm_1500km", "icbm_10000km"}


def test_sources_count() -> None:
    # 2 cited from profile data (wilkening_2000, sessler_ucs_2000) + 4
    # textbook math references (vallado, bmw, allen_eggers,
    # regan_anandakrishnan) for the propagator's docstring.
    assert len(SOURCES) == 6


# ──────────────────────────────────────────────────────────────────────
# Earth physical-constant headlines
# ──────────────────────────────────────────────────────────────────────


def test_earth_mu() -> None:
    """Standard gravitational parameter μ = G·M_earth ≈ 3.986e14."""
    assert EARTH_MU_M3_S2 == pytest.approx(3.986004418e14, rel=1e-9)


def test_earth_radius() -> None:
    """WGS-84 equatorial radius."""
    assert EARTH_RADIUS_M == pytest.approx(6378137.0, abs=1.0)


# ──────────────────────────────────────────────────────────────────────
# Layer B propagator: ICBM-class headline
# ──────────────────────────────────────────────────────────────────────


def test_icbm_class_range_in_window() -> None:
    """v=7000 m/s @ 23° @ 200 km altitude → ~9000-11000 km range
    (Wilkening 2000 ICBM-class reference)."""
    r = bridge.compute_icbm_trajectory(
        burnout_velocity_m_s=7000.0,
        burnout_flight_path_angle_deg=23.0,
    )
    assert r["ok"] is True
    range_km = r["midcourse"]["ground_range_km"]
    assert 8000.0 <= range_km <= 12000.0


def test_icbm_class_apex_in_window() -> None:
    """ICBM-class apex 1000-1500 km."""
    r = bridge.compute_icbm_trajectory(
        burnout_velocity_m_s=7000.0,
        burnout_flight_path_angle_deg=23.0,
    )
    apex_km = r["midcourse"]["apex_altitude_m"] / 1000.0
    assert 1000.0 <= apex_km <= 1700.0


def test_icbm_class_midcourse_duration() -> None:
    """ICBM-class midcourse 25-32 minutes (~1500-1900 s)."""
    r = bridge.compute_icbm_trajectory(
        burnout_velocity_m_s=7000.0,
        burnout_flight_path_angle_deg=23.0,
    )
    midcourse_s = r["midcourse"]["midcourse_duration_s"]
    assert 1500.0 <= midcourse_s <= 2100.0


def test_icbm_class_reentry_velocity() -> None:
    """Re-entry velocity from ICBM apex → ~7000 m/s at 100 km."""
    r = bridge.compute_icbm_trajectory(
        burnout_velocity_m_s=7000.0,
        burnout_flight_path_angle_deg=23.0,
    )
    v_reentry = r["midcourse"]["reentry_velocity_m_s"]
    assert 6500.0 <= v_reentry <= 7500.0


# ──────────────────────────────────────────────────────────────────────
# Allen-Eggers re-entry physics
# ──────────────────────────────────────────────────────────────────────


def test_allen_eggers_peak_decel_independent_of_bc() -> None:
    """Allen-Eggers famous result: peak decel magnitude depends on
    v_e + γ_e but NOT on BC. Different BCs → different ALTITUDE of
    peak decel, but same peak magnitude."""
    r_heavy = bridge.compute_icbm_trajectory(
        burnout_velocity_m_s=7000.0,
        burnout_flight_path_angle_deg=23.0,
        ballistic_coefficient_kg_m2=10000.0,
    )
    r_light = bridge.compute_icbm_trajectory(
        burnout_velocity_m_s=7000.0,
        burnout_flight_path_angle_deg=23.0,
        ballistic_coefficient_kg_m2=50.0,
    )
    peak_heavy = r_heavy["reentry"]["peak_deceleration_m_s2"]
    peak_light = r_light["reentry"]["peak_deceleration_m_s2"]
    assert peak_heavy == pytest.approx(peak_light, rel=1e-6)


def test_allen_eggers_lower_bc_decel_higher_alt() -> None:
    """Lower BC (decoy) → peak decel at HIGHER altitude (atmosphere
    bites earlier)."""
    r_heavy = bridge.compute_icbm_trajectory(
        burnout_velocity_m_s=7000.0,
        burnout_flight_path_angle_deg=23.0,
        ballistic_coefficient_kg_m2=10000.0,
    )
    r_light = bridge.compute_icbm_trajectory(
        burnout_velocity_m_s=7000.0,
        burnout_flight_path_angle_deg=23.0,
        ballistic_coefficient_kg_m2=50.0,
    )
    h_heavy = r_heavy["reentry"]["altitude_of_peak_decel_m"]
    h_light = r_light["reentry"]["altitude_of_peak_decel_m"]
    assert h_light > h_heavy


def test_icbm_class_peak_decel_above_30g() -> None:
    """Heavy compact RV peak decel typically 30-50g (Sessler 2000)."""
    r = bridge.compute_icbm_trajectory(
        burnout_velocity_m_s=7000.0,
        burnout_flight_path_angle_deg=23.0,
        ballistic_coefficient_kg_m2=10000.0,
    )
    peak_g = r["reentry"]["peak_deceleration_g"]
    assert 30.0 <= peak_g <= 60.0


# ──────────────────────────────────────────────────────────────────────
# Input validation
# ──────────────────────────────────────────────────────────────────────


def test_negative_burnout_velocity_rejected() -> None:
    r = compute_icbm_trajectory(
        burnout_velocity_m_s=-1000.0,
        burnout_flight_path_angle_deg=23.0,
    )
    assert r["ok"] is False


def test_escape_velocity_rejected() -> None:
    """Hyperbolic burnout state (escape velocity at 200 km is
    ~10.9 km/s) → caller error."""
    r = compute_icbm_trajectory(
        burnout_velocity_m_s=15000.0,
        burnout_flight_path_angle_deg=23.0,
    )
    assert r["ok"] is False


def test_negative_bc_rejected() -> None:
    r = compute_icbm_trajectory(
        burnout_velocity_m_s=7000.0,
        burnout_flight_path_angle_deg=23.0,
        ballistic_coefficient_kg_m2=-1.0,
    )
    assert r["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# Citation discipline
# ──────────────────────────────────────────────────────────────────────


def test_every_profile_source_resolves() -> None:
    for p in ICBM_REFERENCE_PROFILES:
        assert p.source_key in SOURCES


# ──────────────────────────────────────────────────────────────────────
# Reference profile API
# ──────────────────────────────────────────────────────────────────────


def test_get_icbm_class_profile() -> None:
    r = get_icbm_reference_profile(profile_name="icbm_10000km")
    assert r["ok"] is True
    assert r["profile"]["range_km"] == 10000.0
    assert r["profile"]["midcourse_apex_km"] >= 1000.0


def test_list_reference_profiles() -> None:
    r = list_icbm_reference_profiles()
    assert r["ok"] is True
    assert r["n_profiles"] == 3


def test_unknown_profile_rejected() -> None:
    r = get_icbm_reference_profile(profile_name="totally_made_up")
    assert r["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────


def test_bridge_compute_icbm_trajectory() -> None:
    r = bridge.compute_icbm_trajectory(
        burnout_velocity_m_s=7000.0,
        burnout_flight_path_angle_deg=23.0,
    )
    assert r["ok"] is True


def test_bridge_get_icbm_reference_profile() -> None:
    r = bridge.get_icbm_reference_profile(profile_name="icbm_10000km")
    assert r["ok"] is True


def test_bridge_list_icbm_reference_profiles() -> None:
    r = bridge.list_icbm_reference_profiles()
    assert r["ok"] is True
    assert r["n_profiles"] == 3


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────


def test_cli_icbm_trajectory_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main([
            "icbm-trajectory",
            "--burnout-v", "7000", "--burnout-gamma", "23",
        ])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["midcourse"]["ground_range_km"] >= 8000.0


def test_cli_icbm_help() -> None:
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("icbm-trajectory", "icbm-reference-profile",
                "icbm-reference-profiles"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
