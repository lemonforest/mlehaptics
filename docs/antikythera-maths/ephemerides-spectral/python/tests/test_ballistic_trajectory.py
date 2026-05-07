"""v0.22.0 Layer A — Sol Ballistic Trajectory Catalog tests.

Pins the per-body short-range ballistic propagator + atmosphere
catalog. Vacuum cases match Vallado §8.6.2 closed-form to numerical
precision; drag cases verify monotonic range-reduction and
impact-velocity decay.
"""

from __future__ import annotations

import math

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.ballistic_trajectory_catalog import (
    compute_ballistic_trajectory,
    get_ballistic_atmosphere,
    list_ballistic_atmospheres,
)
from ephemerides_spectral._research.ballistic_trajectory_data import (
    BALLISTIC_ATMOSPHERES,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
    BallisticAtmosphere,
)


# ──────────────────────────────────────────────────────────────────────
# Roster shape
# ──────────────────────────────────────────────────────────────────────


def test_roster_size_is_7() -> None:
    assert len(BALLISTIC_ATMOSPHERES) == 7


def test_canonical_roster_members() -> None:
    by = {a.body for a in BALLISTIC_ATMOSPHERES}
    assert by == {
        "terra", "mars", "venus", "titan",
        "luna", "mercury", "jupiter",
    }


def test_sources_count() -> None:
    assert len(SOURCES) == 6


# ──────────────────────────────────────────────────────────────────────
# Per-body atmosphere headlines
# ──────────────────────────────────────────────────────────────────────


def test_terra_sea_level_density() -> None:
    """US Standard Atmosphere 1976: ρ₀ = 1.225 kg/m³ at sea level."""
    by = {a.body: a for a in BALLISTIC_ATMOSPHERES}
    assert by["terra"].rho_0_kg_m3 == pytest.approx(1.225, abs=0.001)
    assert by["terra"].scale_height_m == pytest.approx(8500.0, abs=200)


def test_venus_runaway_density() -> None:
    """VIRA: Venus surface 65 kg/m³ at 92 bar — fifty times Earth's."""
    by = {a.body: a for a in BALLISTIC_ATMOSPHERES}
    assert by["venus"].rho_0_kg_m3 >= 50.0
    assert by["venus"].rho_0_kg_m3 / by["terra"].rho_0_kg_m3 >= 40.0


def test_airless_bodies_have_zero_rho() -> None:
    by = {a.body: a for a in BALLISTIC_ATMOSPHERES}
    for airless in ("luna", "mercury"):
        assert by[airless].rho_0_kg_m3 == 0.0
        assert by[airless].has_atmosphere is False


def test_titan_thick_cold_atmosphere() -> None:
    """Cassini-Huygens: ρ surface = 5.43 kg/m³, H ≈ 20 km (cold N2)."""
    by = {a.body: a for a in BALLISTIC_ATMOSPHERES}
    titan = by["titan"]
    assert titan.rho_0_kg_m3 == pytest.approx(5.43, abs=0.5)
    assert titan.scale_height_m == pytest.approx(20000.0, abs=2000)


# ──────────────────────────────────────────────────────────────────────
# Vacuum closed-form (Vallado §8.6.2)
# ──────────────────────────────────────────────────────────────────────


def test_vacuum_range_matches_closed_form() -> None:
    """700 m/s @ 45° on Earth → range ≈ v²·sin(2·45°)/g ≈ 49966 m."""
    r = compute_ballistic_trajectory(body="terra", v_m_s=700.0, angle_deg=45.0)
    assert r["ok"] is True
    expected = 700.0 ** 2 * math.sin(math.radians(90.0)) / 9.80665
    assert r["trajectory"]["range_m"] == pytest.approx(expected, rel=1e-9)


def test_vacuum_apex_matches_closed_form() -> None:
    """700 m/s @ 45° on Earth → apex ≈ v²·sin²(45°)/(2g) ≈ 12491 m."""
    r = compute_ballistic_trajectory(body="terra", v_m_s=700.0, angle_deg=45.0)
    expected = (700.0 ** 2) * 0.5 / (2.0 * 9.80665)
    assert r["trajectory"]["peak_altitude_m"] == pytest.approx(expected, rel=1e-9)


def test_vacuum_tof_matches_closed_form() -> None:
    """700 m/s @ 45° on Earth → ToF ≈ 2v·sin(45°)/g ≈ 100.9 s."""
    r = compute_ballistic_trajectory(body="terra", v_m_s=700.0, angle_deg=45.0)
    expected = 2.0 * 700.0 * math.sin(math.radians(45.0)) / 9.80665
    assert r["trajectory"]["time_of_flight_s"] == pytest.approx(expected, rel=1e-9)


def test_luna_vacuum_longer_range_than_terra() -> None:
    """Same v + angle on Luna → range ~ 6× Earth (g_moon = 1.625 vs
    9.81; v²/g scales 6.04×)."""
    r_terra = compute_ballistic_trajectory(body="terra", v_m_s=500.0, angle_deg=45.0)
    r_luna = compute_ballistic_trajectory(body="luna", v_m_s=500.0, angle_deg=45.0)
    ratio = r_luna["trajectory"]["range_m"] / r_terra["trajectory"]["range_m"]
    assert ratio == pytest.approx(9.80665 / 1.625, rel=0.01)


# ──────────────────────────────────────────────────────────────────────
# With-drag invariants
# ──────────────────────────────────────────────────────────────────────


def test_drag_reduces_range_below_vacuum() -> None:
    """Drag must always shorten range vs vacuum on Earth."""
    r_vac = compute_ballistic_trajectory(
        body="terra", v_m_s=700.0, angle_deg=45.0,
    )
    r_drag = compute_ballistic_trajectory(
        body="terra", v_m_s=700.0, angle_deg=45.0,
        with_drag=True, ballistic_coefficient=1500.0,
    )
    assert r_drag["trajectory"]["range_m"] < r_vac["trajectory"]["range_m"]
    assert r_drag["trajectory"]["impact_velocity_m_s"] < 700.0


def test_drag_requires_bc_with_atmosphere() -> None:
    """with_drag=True needs explicit BC for atmospheric bodies."""
    r = compute_ballistic_trajectory(
        body="terra", v_m_s=700.0, angle_deg=45.0,
        with_drag=True,  # but no BC
    )
    assert r["ok"] is False
    assert "ballistic_coefficient" in r["error"]


def test_drag_silently_ignored_for_airless_bodies() -> None:
    """with_drag=True on Luna falls back to vacuum closed-form."""
    r = compute_ballistic_trajectory(
        body="luna", v_m_s=500.0, angle_deg=45.0,
        with_drag=True,  # Luna has no atmosphere → vacuum
    )
    assert r["ok"] is True
    assert r["trajectory"]["with_drag"] is False


def test_higher_bc_drags_less() -> None:
    """Higher BC = more massive / less drag → longer range."""
    r_low = compute_ballistic_trajectory(
        body="terra", v_m_s=700.0, angle_deg=45.0,
        with_drag=True, ballistic_coefficient=100.0,  # light bullet
    )
    r_high = compute_ballistic_trajectory(
        body="terra", v_m_s=700.0, angle_deg=45.0,
        with_drag=True, ballistic_coefficient=5000.0,  # heavy shell
    )
    assert r_high["trajectory"]["range_m"] > r_low["trajectory"]["range_m"]


# ──────────────────────────────────────────────────────────────────────
# Input validation
# ──────────────────────────────────────────────────────────────────────


def test_unknown_body_rejected() -> None:
    r = compute_ballistic_trajectory(body="krypton", v_m_s=100.0, angle_deg=45.0)
    assert r["ok"] is False


def test_negative_velocity_rejected() -> None:
    r = compute_ballistic_trajectory(body="terra", v_m_s=-100.0, angle_deg=45.0)
    assert r["ok"] is False


def test_out_of_range_angle_rejected() -> None:
    r = compute_ballistic_trajectory(body="terra", v_m_s=700.0, angle_deg=95.0)
    assert r["ok"] is False
    r = compute_ballistic_trajectory(body="terra", v_m_s=700.0, angle_deg=0.0)
    assert r["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# Citation discipline
# ──────────────────────────────────────────────────────────────────────


def test_every_source_key_resolves() -> None:
    for a in BALLISTIC_ATMOSPHERES:
        assert a.source_key in SOURCES


def test_no_unused_sources_entries() -> None:
    used = {a.source_key for a in BALLISTIC_ATMOSPHERES}
    unused = set(SOURCES.keys()) - used
    assert unused == set()


# ──────────────────────────────────────────────────────────────────────
# Atmosphere catalog API
# ──────────────────────────────────────────────────────────────────────


def test_get_atmosphere_per_body() -> None:
    r = get_ballistic_atmosphere(body="terra")
    assert r["ok"] is True
    assert r["atmosphere"]["rho_0_kg_m3"] == pytest.approx(1.225, abs=0.001)


def test_get_atmosphere_full_roster() -> None:
    r = get_ballistic_atmosphere()
    assert r["ok"] is True
    assert r["n_bodies"] == 7


def test_list_atmospheres_smoke() -> None:
    r = list_ballistic_atmospheres()
    assert r["ok"] is True
    assert r["n_bodies"] == 7
    assert r["n_sources"] == 6


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────


def test_bridge_compute_ballistic_trajectory() -> None:
    r = bridge.compute_ballistic_trajectory(
        body="terra", v_m_s=700.0, angle_deg=45.0,
    )
    assert r["ok"] is True
    assert r["trajectory"]["range_m"] > 49000.0


def test_bridge_get_ballistic_atmosphere() -> None:
    r = bridge.get_ballistic_atmosphere(body="venus")
    assert r["ok"] is True
    assert r["atmosphere"]["rho_0_kg_m3"] >= 50.0


def test_bridge_list_ballistic_atmospheres() -> None:
    r = bridge.list_ballistic_atmospheres()
    assert r["ok"] is True
    assert r["n_bodies"] == 7


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────


def test_cli_ballistic_trajectory_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main([
            "ballistic-trajectory",
            "--body", "terra", "--v", "700", "--angle", "45",
        ])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["trajectory"]["range_m"] > 49000.0


def test_cli_ballistic_atmospheres_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["ballistic-atmospheres"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_bodies"] == 7


def test_cli_ballistic_help() -> None:
    """All v0.22.0 Layer A subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("ballistic-trajectory", "ballistic-atmosphere",
                "ballistic-atmospheres"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
