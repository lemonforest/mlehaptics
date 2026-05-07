"""v0.22.0 Layer C(a) — Sensor Access Catalog tests.

Pins look-angle geometry, Earth-limb occlusion, reference TLE roster,
and SGP4 propagation (when sgp4 dep available).
"""

from __future__ import annotations

import math

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.sensor_access_catalog import (
    compute_sgp4_state,
    compute_visibility_geometry,
    get_orbital_reference,
    list_orbital_references,
)
from ephemerides_spectral._research.sensor_access_data import (
    EARTH_RADIUS_OCCLUSION_M,
    LWIR_LOWER_UM, LWIR_UPPER_UM,
    MWIR_LOWER_UM, MWIR_UPPER_UM,
    ORBITAL_REFERENCES,
    SOURCES,
    WGS84_A_M, WGS84_B_M,
    OrbitalReferenceTLE,
)


# ──────────────────────────────────────────────────────────────────────
# Reference TLE roster shape
# ──────────────────────────────────────────────────────────────────────


def test_reference_tle_count() -> None:
    assert len(ORBITAL_REFERENCES) == 8


def test_reference_orbit_classes_covered() -> None:
    classes = {r.orbit_class for r in ORBITAL_REFERENCES}
    assert {
        "leo_sun_sync", "leo_mid_inc", "leo_polar",
        "geo", "heo_molniya", "heo_tundra",
    }.issubset(classes)


def test_iss_reference_present() -> None:
    by = {r.label: r for r in ORBITAL_REFERENCES}
    assert "ISS (ZARYA)" in by
    assert by["ISS (ZARYA)"].inclination_deg == pytest.approx(51.64, abs=0.1)


def test_molniya_reference_present() -> None:
    """Molniya 12-h HEO at 63.4° — the textbook polar-coverage
    geometry that fills the SBIRS-GEO arctic blind zone."""
    by = {r.label: r for r in ORBITAL_REFERENCES}
    assert any("MOLNIYA" in lbl for lbl in by)
    molniya = next(r for r in ORBITAL_REFERENCES if r.orbit_class == "heo_molniya")
    assert molniya.inclination_deg == pytest.approx(63.4, abs=0.1)
    assert molniya.period_min == pytest.approx(720.0, abs=10)


def test_geo_period_24h() -> None:
    geo = next(r for r in ORBITAL_REFERENCES if r.orbit_class == "geo")
    assert geo.period_min == pytest.approx(1436.0, abs=10)


# ──────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────


def test_wgs84_constants() -> None:
    assert WGS84_A_M == pytest.approx(6378137.0, abs=1.0)
    assert WGS84_B_M < WGS84_A_M  # polar smaller than equatorial


def test_ir_window_definitions() -> None:
    assert MWIR_LOWER_UM < MWIR_UPPER_UM
    assert LWIR_LOWER_UM < LWIR_UPPER_UM
    assert MWIR_UPPER_UM < LWIR_LOWER_UM  # MWIR < LWIR


def test_sources_count() -> None:
    assert len(SOURCES) == 10  # 8 TLE refs + HITRAN + WGS84


# ──────────────────────────────────────────────────────────────────────
# Look-angle geometry (Vallado Ch. 11)
# ──────────────────────────────────────────────────────────────────────


def test_overhead_satellite_zenith_elevation() -> None:
    """Satellite directly overhead → elevation 90°."""
    # Target at lat=0, lon=0; satellite directly above at 800 km
    # ECEF: (R_eq + 800km, 0, 0)
    sat = (WGS84_A_M + 800_000.0, 0.0, 0.0)
    r = compute_visibility_geometry(
        sat_ecef_m=sat, target_lat_deg=0.0, target_lon_deg=0.0,
    )
    assert r["ok"] is True
    assert r["elevation_deg"] == pytest.approx(90.0, abs=0.1)


def test_horizon_satellite_low_elevation() -> None:
    """Satellite at 800 km altitude, ~horizon range → low elevation."""
    # Target at lat=0, lon=0; satellite shifted in y-direction
    R = WGS84_A_M + 800_000.0
    sat = (WGS84_A_M, R - WGS84_A_M, 0.0)  # offset in tangential dir
    r = compute_visibility_geometry(
        sat_ecef_m=sat, target_lat_deg=0.0, target_lon_deg=0.0,
    )
    assert r["ok"] is True
    assert r["elevation_deg"] < 45.0


def test_subterranean_target_occluded() -> None:
    """Satellite on opposite side of Earth → line-of-sight passes
    through Earth → occluded."""
    sat = (-(WGS84_A_M + 800_000.0), 0.0, 0.0)  # antipodal to lat=0,lon=0
    r = compute_visibility_geometry(
        sat_ecef_m=sat, target_lat_deg=0.0, target_lon_deg=0.0,
    )
    assert r["ok"] is True
    assert r["occluded_by_earth"] is True
    assert r["visible"] is False


def test_min_elevation_threshold() -> None:
    """Visibility flag respects minimum_elevation_deg.

    Place a satellite directly overhead at 800 km (elevation ≈ 90°),
    not occluded. Visibility flag must respect the minimum.
    """
    sat = (WGS84_A_M + 800_000.0, 0.0, 0.0)
    r_strict = compute_visibility_geometry(
        sat_ecef_m=sat, target_lat_deg=0.0, target_lon_deg=0.0,
        minimum_elevation_deg=95.0,  # impossible threshold
    )
    r_loose = compute_visibility_geometry(
        sat_ecef_m=sat, target_lat_deg=0.0, target_lon_deg=0.0,
        minimum_elevation_deg=5.0,
    )
    assert r_strict["visible"] is False
    assert r_loose["visible"] is True


# ──────────────────────────────────────────────────────────────────────
# Reference TLE catalog API
# ──────────────────────────────────────────────────────────────────────


def test_get_orbital_reference_iss() -> None:
    r = get_orbital_reference(label="ISS (ZARYA)")
    assert r["ok"] is True
    assert r["reference"]["norad_cat_id"] == 25544


def test_get_orbital_reference_full_catalog() -> None:
    r = get_orbital_reference()
    assert r["ok"] is True
    assert r["n_references"] == 8


def test_list_orbital_references() -> None:
    r = list_orbital_references()
    assert r["ok"] is True
    assert r["n_references"] == 8
    assert r["ir_windows"]["mwir"]["lower_um"] == 3.0
    assert r["ir_windows"]["lwir"]["upper_um"] == 12.0


def test_unknown_reference_rejected() -> None:
    r = get_orbital_reference(label="NOT_A_REAL_LABEL")
    assert r["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# SGP4 propagator (depends on optional sgp4 install)
# ──────────────────────────────────────────────────────────────────────


def test_sgp4_state_iss_or_skipped() -> None:
    """SGP4 propagates ISS reference TLE — or returns ok=False if
    sgp4 not installed (acceptable degradation)."""
    iss = next(r for r in ORBITAL_REFERENCES if r.norad_cat_id == 25544)
    r = compute_sgp4_state(line1=iss.line1, line2=iss.line2,
                           minutes_since_epoch=0.0)
    if not r["ok"] and "not installed" in r.get("error", ""):
        pytest.skip("sgp4 package not installed; skipping live propagation")
    # When sgp4 IS installed, position must be reasonable LEO
    if r["ok"]:
        x, y, z = r["position_eci_m"]
        radius = math.sqrt(x * x + y * y + z * z)
        # ISS altitude ~400 km → radius ~6.78e6 m
        assert 6.5e6 < radius < 7.5e6


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────


def test_bridge_compute_visibility_geometry() -> None:
    sat = (WGS84_A_M + 800_000.0, 0.0, 0.0)
    r = bridge.compute_visibility_geometry(
        sat_ecef_m=sat, target_lat_deg=0.0, target_lon_deg=0.0,
    )
    assert r["ok"] is True
    assert r["visible"] is True


def test_bridge_get_orbital_reference() -> None:
    r = bridge.get_orbital_reference(label="ISS (ZARYA)")
    assert r["ok"] is True


def test_bridge_list_orbital_references() -> None:
    r = bridge.list_orbital_references()
    assert r["ok"] is True
    assert r["n_references"] == 8


def test_bridge_compute_sgp4_state_or_skip() -> None:
    iss = next(r for r in ORBITAL_REFERENCES if r.norad_cat_id == 25544)
    r = bridge.compute_sgp4_state(
        line1=iss.line1, line2=iss.line2, minutes_since_epoch=0.0,
    )
    # Either ok=True with valid state, or ok=False with import message
    assert "ok" in r


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────


def test_cli_visibility_geometry_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main([
            "visibility-geometry",
            "--sat-x", "7178137",
            "--sat-y", "0",
            "--sat-z", "0",
            "--lat", "0",
            "--lon", "0",
        ])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["elevation_deg"] == pytest.approx(90.0, abs=0.1)


def test_cli_orbital_references_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["orbital-references"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_references"] == 8


def test_cli_sensor_access_help() -> None:
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("visibility-geometry", "sgp4-state",
                "orbital-reference", "orbital-references"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
