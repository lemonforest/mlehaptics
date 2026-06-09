"""v0.30.0rc2 — Sol Solar Rotation Catalog tests.

Pins the first solar-dynamics extension of the v0.24.3 Sun Dynamical
Spectrum: the Sun's surface differential rotation (Snodgrass-Ulrich
1990) + internal rotation (Schou 1998 / Howe 2009).

* Surface law Omega(lat) = A + B sin^2 + C sin^4 across latitude.
* THE closure invariant: the 1990 Doppler law reproduces Carrington's
  1863 sunspot-derived 25.38-day sidereal period at latitude ~26 deg,
  inside the sunspot active band (two independent methods agree).
"""

from __future__ import annotations

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.solar_rotation_catalog import (
    get_solar_differential_rotation,
    get_solar_internal_rotation,
    get_solar_rotation_closure,
    list_solar_differential_rotation,
)
from ephemerides_spectral._research.solar_rotation_data import (
    CARRINGTON_SIDEREAL_PERIOD_DAYS,
    ROTATION_ANCHORS,
    SOURCES,
    SU_A_DEG_PER_DAY,
    SU_B_DEG_PER_DAY,
    SU_C_DEG_PER_DAY,
    TACHOCLINE_RADIUS_R_SUN,
)


# ──────────────────────────────────────────────────────────────────────
# Coefficients + roster
# ──────────────────────────────────────────────────────────────────────


def test_snodgrass_ulrich_coefficients() -> None:
    """Snodgrass & Ulrich 1990 accepted-average coefficients (deg/day)."""
    assert SU_A_DEG_PER_DAY == pytest.approx(14.713, abs=1e-3)
    assert SU_B_DEG_PER_DAY == pytest.approx(-2.396, abs=1e-3)
    assert SU_C_DEG_PER_DAY == pytest.approx(-1.787, abs=1e-3)


def test_sources_count_4() -> None:
    assert len(SOURCES) == 4


def test_anchor_count_4() -> None:
    assert len(ROTATION_ANCHORS) == 4


def test_every_anchor_source_resolves() -> None:
    for a in ROTATION_ANCHORS:
        assert a.source_key in SOURCES


# ──────────────────────────────────────────────────────────────────────
# Surface differential rotation
# ──────────────────────────────────────────────────────────────────────


def test_seven_latitude_bands() -> None:
    r = get_solar_differential_rotation()
    assert r["n_bands"] == 7
    assert len(r["bands"]) == 7


def test_equatorial_period_24_5d() -> None:
    """Equatorial sidereal period 360/14.713 ~ 24.47 d (fastest)."""
    r = get_solar_differential_rotation()
    assert r["equatorial_sidereal_period_days"] == pytest.approx(24.47, abs=0.1)


def test_polar_period_34d() -> None:
    """Polar sidereal period 360/(A+B+C) ~ 34.19 d (slowest)."""
    r = get_solar_differential_rotation()
    assert r["polar_sidereal_period_days"] == pytest.approx(34.19, abs=0.1)


def test_equator_pole_lap_86d() -> None:
    """The equator laps the poles every ~86 days."""
    r = get_solar_differential_rotation()
    assert r["equator_pole_lap_days"] == pytest.approx(86.0, abs=2.0)


def test_period_monotone_in_latitude() -> None:
    """Sidereal period increases monotonically from equator to pole
    (the Sun rotates slower at higher latitude)."""
    r = get_solar_differential_rotation()
    periods = [b["sidereal_period_days"] for b in r["bands"]]
    for prev, curr in zip(periods[:-1], periods[1:]):
        assert curr > prev


def test_synodic_longer_than_sidereal() -> None:
    """At every band the synodic (Earth-relative) period exceeds the
    sidereal period (the Sun and Earth orbit the same way)."""
    r = get_solar_differential_rotation()
    for b in r["bands"]:
        assert b["synodic_period_days"] > b["sidereal_period_days"]


# ──────────────────────────────────────────────────────────────────────
# THE closure invariant: Doppler 1990 ↔ sunspot 1863
# ──────────────────────────────────────────────────────────────────────


def test_rotation_closure_reproduces_carrington_period() -> None:
    """THE headline: the Snodgrass-Ulrich law reproduces the 25.38-day
    Carrington sidereal period (residual ~ 0 by construction)."""
    r = get_solar_rotation_closure()
    assert r["reproduced_period_days"] == pytest.approx(
        CARRINGTON_SIDEREAL_PERIOD_DAYS, abs=1e-3,
    )
    assert abs(r["residual_days"]) < 1e-6


def test_carrington_latitude_in_sunspot_band() -> None:
    """The latitude at which the law gives 25.38 d (~26 deg) lies inside
    the sunspot active band — so the 1990 Doppler determination and
    Carrington's 1863 sunspot determination agree where they overlap."""
    r = get_solar_rotation_closure()
    assert r["latitude_in_sunspot_band"] is True
    assert 20.0 < r["carrington_latitude_deg"] < 30.0


# ──────────────────────────────────────────────────────────────────────
# Internal rotation
# ──────────────────────────────────────────────────────────────────────


def test_tachocline_radius() -> None:
    """The tachocline sits at ~0.70 R_sun (the dynamo seat)."""
    r = get_solar_internal_rotation()
    assert r["tachocline_radius_r_sun"] == pytest.approx(0.70, abs=0.02)
    assert TACHOCLINE_RADIUS_R_SUN == pytest.approx(0.70, abs=0.02)


def test_radiative_interior_is_rigid() -> None:
    """Below the tachocline the interior rotates nearly rigidly."""
    r = get_solar_internal_rotation()
    regimes = {a["region"]: a["regime"] for a in r["anchors"]}
    assert regimes["radiative_interior"] == "rigid_body"
    assert regimes["tachocline"] == "shear_boundary"


# ──────────────────────────────────────────────────────────────────────
# Pythonic API
# ──────────────────────────────────────────────────────────────────────


def test_get_solar_differential_rotation_smoke() -> None:
    r = get_solar_differential_rotation()
    assert r["ok"] is True
    assert r["body"] == "sol"


def test_get_solar_rotation_closure_smoke() -> None:
    r = get_solar_rotation_closure()
    assert r["ok"] is True
    assert r["latitude_in_sunspot_band"] is True


def test_list_solar_differential_rotation_smoke() -> None:
    r = list_solar_differential_rotation()
    assert r["ok"] is True
    assert r["n_sources"] == 4
    assert r["n_anchors"] == 4


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────


def test_bridge_get_solar_differential_rotation() -> None:
    r = bridge.get_solar_differential_rotation()
    assert r["ok"] is True
    assert r["n_bands"] == 7


def test_bridge_get_solar_rotation_closure() -> None:
    r = bridge.get_solar_rotation_closure()
    assert r["ok"] is True


def test_bridge_get_solar_internal_rotation() -> None:
    r = bridge.get_solar_internal_rotation()
    assert r["ok"] is True
    assert r["n_anchors"] == 4


def test_bridge_list_solar_differential_rotation() -> None:
    r = bridge.list_solar_differential_rotation()
    assert r["ok"] is True


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────


def _cli_json(argv):
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(argv)
    assert rc == 0
    return _json.loads(buf.getvalue())


def test_cli_solar_differential_rotation_smoke() -> None:
    payload = _cli_json(["solar-differential-rotation"])
    assert payload["body"] == "sol"
    assert payload["n_bands"] == 7


def test_cli_solar_rotation_closure_smoke() -> None:
    payload = _cli_json(["solar-rotation-closure"])
    assert payload["latitude_in_sunspot_band"] is True


def test_cli_solar_internal_rotation_smoke() -> None:
    payload = _cli_json(["solar-internal-rotation"])
    assert payload["n_anchors"] == 4


def test_cli_solar_differential_rotation_full_smoke() -> None:
    payload = _cli_json(["solar-differential-rotation-full"])
    assert payload["n_sources"] == 4


def test_cli_solar_rotation_help() -> None:
    """All v0.30.0rc2 CLI subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("solar-differential-rotation",
                "solar-rotation-closure",
                "solar-internal-rotation",
                "solar-differential-rotation-full"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
