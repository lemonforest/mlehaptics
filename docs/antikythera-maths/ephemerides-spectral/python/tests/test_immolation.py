"""Immolation suite for ephemerides-spectral.

Cheap-but-load-bearing release-gate tests: every name in
``bridge.__all__`` must resolve, the version string must agree
between version.py and pyproject.toml, and the v0.3.0 time-scale +
natural-resonance surface must be wired through.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral.version import __version__


# Names exported from bridge.__all__ that are *constants* rather than
# callables. They must still resolve via getattr, but `callable()` is
# the wrong check for them.
_BRIDGE_CONSTANTS = frozenset({
    "DEFAULT_BACKEND",
    "SUPPORTED_BACKENDS",
    "SUPPORTED_BODIES",
    "ALLOWED_KERNELS",
    "LUNAR_KERNELS",
    "CATALOG_PATCHES",  # v0.4.0 — bundled patch names tuple
})


def test_bridge_api_contract() -> None:
    """Every name in bridge.__all__ must resolve; functions must be callable."""
    assert len(bridge.__all__) >= 3
    for name in bridge.__all__:
        attr = getattr(bridge, name)  # raises if missing
        if name in _BRIDGE_CONSTANTS:
            # Constants: not callable, but must be a non-None value.
            assert attr is not None, f"{name} is None"
        else:
            assert callable(attr), f"{name} is in __all__ but not callable"


def test_version_agreement() -> None:
    """Version in pyproject.toml must match version.py."""
    if sys.version_info >= (3, 11):
        import tomllib
    else:  # pragma: no cover — only hit on py3.10
        import tomli as tomllib  # type: ignore[no-redef]

    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with pyproject.open("rb") as f:
        data = tomllib.load(f)
    assert data["project"]["version"] == __version__


def test_bridge_has_v030_surface() -> None:
    """The v0.3.0 time-scale + natural-resonance surface must be present."""
    expected = {
        "jd_to_mars_time",
        "mars_time_to_jd",
        "get_lunar_phase",
        "list_lunar_kernels",
        "get_natural_resonance_group",
    }
    missing = expected - set(bridge.__all__)
    assert not missing, f"missing v0.3.0 surface in bridge.__all__: {missing}"


def test_bridge_has_v054_uranus_surface() -> None:
    """The v0.5.4 Sol Uranus Time surface must be present."""
    expected = {
        "jd_to_sol_uranian_time",
        "sol_uranian_time_to_jd",
    }
    missing = expected - set(bridge.__all__)
    assert not missing, f"missing v0.5.4 surface in bridge.__all__: {missing}"


def test_natural_resonance_group_returns_z60() -> None:
    """v0.5.0 seven-resonance set yields Z_60 = Z_4 × Z_3 × Z_5.

    The Saturnian additions (Mimas-Tethys 4:2, Enceladus-Dione 2:1,
    Titan-Hyperion 4:3) bump the natural modulus from 30 (v0.2.0)
    to 60 — the Titan-Hyperion 4:3 contributes lcm(4,3) = 12,
    introducing the factor of 4 (= 2²) over the v0.2.0 modulus of 30.
    Prime factor SET is unchanged at {2, 3, 5}, but the multiplicity
    of 2 grew from 1 to 2.
    """
    out = bridge.get_natural_resonance_group()
    assert out["ok"] is True
    assert out["natural_modulus"] == 60
    assert out["prime_factors"] == [2, 3, 5]


def test_mars_time_round_trip_at_reference() -> None:
    """Allison & McEwen reference: 2000-01-06 UTC ↔ MSD ≈ 44795.99."""
    forward = bridge.jd_to_mars_time(2451549.5)
    assert forward["ok"] is True
    assert abs(forward["msd"] - 44795.999817) < 1e-4
    inverse = bridge.mars_time_to_jd(forward["msd"])
    assert inverse["ok"] is True
    assert abs(inverse["jd_utc"] - 2451549.5) < 1e-9


# ──────────────────────────────────────────────────────────────────────
# Sol Uranus Time (v0.5.4)
# ──────────────────────────────────────────────────────────────────────

def test_sol_uranus_time_at_epoch_returns_zero_usd() -> None:
    """At the SUT epoch (2007 northern equinox, JD 2454451.0) the
    Uranian Sol Date should be exactly zero, the SUT time-of-day
    should be exactly 0.0 hours, and the orbital phase should be 0.0
    (the start of the season cycle)."""
    out = bridge.jd_to_sol_uranian_time(2454451.0)
    assert out["ok"] is True
    assert abs(out["usd"]) < 1e-9
    assert abs(out["sut_hours"]) < 1e-9
    assert abs(out["orbital_phase"]) < 1e-9
    assert out["season"] == "northern-autumn"
    assert out["retrograde"] is True


def test_sol_uranus_time_round_trip() -> None:
    """JD → USD → JD must round-trip to within ULP."""
    jd = 2451545.0  # J2000
    fwd = bridge.jd_to_sol_uranian_time(jd)
    assert fwd["ok"] is True
    inv = bridge.sol_uranian_time_to_jd(fwd["usd"])
    assert inv["ok"] is True
    assert abs(inv["jd_tdb"] - jd) < 1e-6


def test_sol_uranus_time_carries_retrograde_flag() -> None:
    """Uranus rotates retrograde; the result must surface that fact."""
    out = bridge.jd_to_sol_uranian_time(2451545.0)
    assert out["retrograde"] is True
    # And the epoch metadata must surface the axial tilt + period.
    epoch = out["epoch"]
    assert epoch["sidereal_day_hours"] == 17.24
    assert abs(epoch["orbital_period_years"] - 84.0205) < 0.01
    assert epoch["axial_tilt_deg"] == 97.77
    assert epoch["season_names"] == [
        "northern-autumn", "southern-summer",
        "northern-spring", "northern-summer",
    ]


def test_sol_uranus_time_advances_uniformly() -> None:
    """USD should advance uniformly: dt = sidereal_day_days for 1 USD."""
    epoch = 2454451.0
    sidereal_day_d = 17.24 / 24.0
    out0 = bridge.jd_to_sol_uranian_time(epoch + 1.0 * sidereal_day_d)
    assert abs(out0["usd"] - 1.0) < 1e-9
    out1 = bridge.jd_to_sol_uranian_time(epoch + 100.0 * sidereal_day_d)
    assert abs(out1["usd"] - 100.0) < 1e-9


def test_sol_uranus_time_seasons_partition_orbit_into_four() -> None:
    """Four seasons span the orbit; the boundary at orbital_phase=0.25
    transitions from northern-autumn to southern-summer."""
    epoch = 2454451.0
    P_orbital = 30688.5
    quarter = P_orbital / 4
    out_q1 = bridge.jd_to_sol_uranian_time(epoch + quarter * 0.99)
    out_q2 = bridge.jd_to_sol_uranian_time(epoch + quarter * 1.01)
    assert out_q1["season"] == "northern-autumn"
    assert out_q2["season"] == "southern-summer"


# ──────────────────────────────────────────────────────────────────────
# v0.5.5 — moon catalog patches (Phase C)
# ──────────────────────────────────────────────────────────────────────

_V055_MOON_PATCHES = (
    "dione-1.06yr-diagonal-v2",
    "tethys-0.38yr-diagonal-v2",
    "enceladus-0.39yr-diagonal-v2",
    "titan-0.69yr-diagonal-v2",
    "iapetus-0.22yr-diagonal-v2",
)


def test_v055_moon_patches_present_in_catalog() -> None:
    """The 5 vindicated moon patches must appear in the bundled catalog."""
    out = bridge.list_catalog_patches()
    assert out["ok"] is True
    catalog_names = {p["name"] for p in out["patches"]}
    for name in _V055_MOON_PATCHES:
        assert name in catalog_names, f"missing {name} from bundled catalog"


def test_v055_moon_patches_carry_measured_shrinkage() -> None:
    """Each v0.5.5 moon patch's notes string must pin its measured
    shrinkage% — the same regression-test gate the v0.5.2 planet
    patches carry."""
    out = bridge.list_catalog_patches()
    by_name = {p["name"]: p for p in out["patches"]}
    for name in _V055_MOON_PATCHES:
        notes = by_name[name].get("notes", "")
        assert "MEASURED SHRINKAGE" in notes, (
            f"{name} missing measured-shrinkage gate in notes"
        )
        assert "Phase C" in notes, f"{name} missing Phase C provenance"


def test_v055_moon_patches_apply_and_clear() -> None:
    """Each v0.5.5 moon patch must apply via the bridge and clear cleanly."""
    bridge.clear_patches()
    try:
        for name in _V055_MOON_PATCHES:
            applied = bridge.apply_patch(name)
            assert applied["ok"] is True, f"apply {name} failed: {applied}"
        active = bridge.list_active_patches()
        active_names = {p["name"] for p in active["patches"]}
        for name in _V055_MOON_PATCHES:
            assert name in active_names
        cleared = bridge.clear_patches()
        assert cleared["ok"] is True
        assert cleared["cleared"] >= len(_V055_MOON_PATCHES)
    finally:
        bridge.clear_patches()
