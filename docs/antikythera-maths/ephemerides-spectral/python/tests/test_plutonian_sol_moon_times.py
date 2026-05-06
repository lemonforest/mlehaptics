"""v0.15.0 — Sol Moon Times: Plutonian (Charon).

Pluto-Charon is the only mutually tidally locked planet-moon pair in
the solar system: both bodies show the same face to each other
forever, so the sidereal period IS the mutual rotation period (they
collapse into one timescale). The Charon:Pluto mass ratio (~0.12) is
the highest of any moon-planet pair, and the Pluto-Charon barycentre
sits OUTSIDE Pluto — the system is closer to a binary planet than a
planet-with-moon. Mirrors the per-family test pattern from v0.14.0
(Galileans), v0.14.1 (Saturnians), and v0.14.2 (Martians, Jovian
inner regulars, Uranian Titania, Neptunian Triton).
"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.bodies import BODIES
from ephemerides_spectral._research.time_scales import (
    SOL_MOON_TIME_J2000_JD_TDB,
)
from ephemerides_spectral.cli import main as cli_main


PLUTONIANS = [
    # (body_key, abbrev, sol_time_name, jd_to_fn, to_jd_fn)
    ("charon", "SPlChT", "Sol Pluto-Charon Time",
     bridge.jd_to_sol_pluto_charon_time, bridge.sol_pluto_charon_time_to_jd),
]


# ──────────────────────────────────────────────────────────────────────
# Bridge surface — per-Plutonian wrappers
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("body_key, abbrev, sol_time_name, jd_to_fn, _to_jd_fn", PLUTONIANS)
def test_plutonian_bridge_at_j2000_returns_zero_count(
        body_key, abbrev, sol_time_name, jd_to_fn, _to_jd_fn):
    out = jd_to_fn(SOL_MOON_TIME_J2000_JD_TDB)
    assert out["ok"] is True
    assert out["body_name"] == body_key
    assert out["parent_name"] == "pluto"
    assert out["sidereal_count"] == 0.0
    assert out["sidereal_phase"] == 0.0
    assert out["epoch"]["abbreviation"] == abbrev
    assert out["epoch"]["sol_time_name"] == sol_time_name


@pytest.mark.parametrize("body_key, _abbrev, _name, jd_to_fn, _to_jd_fn", PLUTONIANS)
def test_plutonian_bridge_after_one_sidereal_period(
        body_key, _abbrev, _name, jd_to_fn, _to_jd_fn):
    period = float(BODIES[body_key].period_days)
    jd_one = SOL_MOON_TIME_J2000_JD_TDB + period
    out = jd_to_fn(jd_one)
    assert out["ok"] is True
    assert abs(out["sidereal_count"] - 1.0) < 1e-9
    assert abs(out["sidereal_phase"] - 0.0) < 1e-9 or abs(out["sidereal_phase"] - 1.0) < 1e-9


@pytest.mark.parametrize("body_key, abbrev, _name, jd_to_fn, to_jd_fn", PLUTONIANS)
def test_plutonian_bridge_inverse_round_trip(
        body_key, abbrev, _name, jd_to_fn, to_jd_fn):
    jd0 = SOL_MOON_TIME_J2000_JD_TDB + 365.25 * 20.0  # +20 yr
    out = jd_to_fn(jd0)
    assert out["ok"] is True
    inv = to_jd_fn(out["sidereal_count"])
    assert inv["ok"] is True
    assert abs(inv["jd_tdb"] - jd0) < 1e-6
    assert inv["abbreviation"] == abbrev
    assert inv["body_name"] == body_key


def test_charon_period_matches_bodies_roster() -> None:
    """Charon's sidereal period is pulled from BODIES at call time;
    the v0.15.0 ship spec'd it at 6.38723000 days. Pin that here so
    a future BODIES tweak can't silently drift the time scale.

    Note: Charon and Pluto are MUTUALLY tidally locked, so the
    sidereal period equals the mutual rotation period of the pair.
    """
    assert float(BODIES["charon"].period_days) == 6.38723000


def test_charon_abbreviation_is_six_letters() -> None:
    """v0.14.1 policy: all moon abbreviations are 6-letter
    `S<Planet2><Moon2>T`. SPlChT → S + Pl + Ch + T = 6 letters.
    """
    out = bridge.jd_to_sol_pluto_charon_time(SOL_MOON_TIME_J2000_JD_TDB)
    abbrev = out["epoch"]["abbreviation"]
    assert abbrev == "SPlChT"
    assert len(abbrev) == 6


def test_plutonian_abbreviations_dont_collide_with_other_families() -> None:
    """SPlChT must not collide with any Galilean (SJu*), Saturnian
    (SSa*), Martian (SMa*), or Uranian (SUr*) abbreviation.
    """
    galilean_abbrevs = {"SJuIoT", "SJuEuT", "SJuGaT", "SJuCaT"}
    jovian_inner_abbrevs = {"SJuMeT", "SJuAdT", "SJuAmT", "SJuThT"}
    saturnian_abbrevs = {
        "SSaMiT", "SSaEnT", "SSaTeT", "SSaDiT", "SSaRhT", "SSaTiT",
        "SSaHyT", "SSaIaT", "SSaPhT", "SSaJaT", "SSaEpT",
    }
    martian_abbrevs = {"SMaPhT", "SMaDeT"}
    uranian_abbrevs = {"SUrMiT", "SUrArT", "SUrUmT", "SUrTiT", "SUrObT"}
    neptunian_abbrevs = {"SNeTrT"}
    plutonian_abbrevs = {abbrev for _, abbrev, *_ in PLUTONIANS}
    all_other = (galilean_abbrevs | jovian_inner_abbrevs | saturnian_abbrevs
                 | martian_abbrevs | uranian_abbrevs | neptunian_abbrevs)
    assert all_other.isdisjoint(plutonian_abbrevs), (
        f"abbreviation collision between Plutonians and prior families: "
        f"{all_other & plutonian_abbrevs}"
    )


def test_charon_pluto_mutual_tidal_lock_property() -> None:
    """Documentation property: Pluto and Charon are mutually tidally
    locked, so Charon's sidereal period equals its synodic period
    relative to Pluto and equals the spin period of both bodies.

    Mathematically the bridge doesn't enforce this; we just pin the
    period as specified in v0.15.0 and document why no separate
    'synodic' field is offered.
    """
    period = float(BODIES["charon"].period_days)
    # The v0.15.0 spec value, traceable to JPL HORIZONS.
    assert period == 6.38723000
    # No separate synodic correction needed -- mutual tidal lock means
    # sidereal == synodic == spin.


@pytest.mark.parametrize("body_key, _abbrev, _name, jd_to_fn, _to_jd_fn", PLUTONIANS)
def test_plutonian_bridge_rejects_non_finite_jd(
        body_key, _abbrev, _name, jd_to_fn, _to_jd_fn):
    out = jd_to_fn(float("nan"))
    assert out["ok"] is False
    out = jd_to_fn(float("inf"))
    assert out["ok"] is False
    out = jd_to_fn(float("-inf"))
    assert out["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# CLI surface — time-pluto-{moon}
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("body_key, abbrev, _name, _jd_fn, _inv_fn", PLUTONIANS)
def test_plutonian_cli_jd_path(body_key, abbrev, _name, _jd_fn, _inv_fn):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main([f"time-pluto-{body_key}", "--jd", "2451545.0"])
    assert rc == 0
    payload = json.loads(buf.getvalue())
    assert payload["ok"] is True
    assert payload["body_name"] == body_key
    assert payload["parent_name"] == "pluto"
    assert payload["epoch"]["abbreviation"] == abbrev


@pytest.mark.parametrize("body_key, abbrev, _name, _jd_fn, _inv_fn", PLUTONIANS)
def test_plutonian_cli_inverse_path(body_key, abbrev, _name, _jd_fn, _inv_fn):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main([f"time-pluto-{body_key}", "--sidereal-count", "100"])
    assert rc == 0
    payload = json.loads(buf.getvalue())
    assert payload["ok"] is True
    assert payload["sidereal_count"] == 100.0
    assert payload["abbreviation"] == abbrev
    expected_jd = (
        SOL_MOON_TIME_J2000_JD_TDB
        + 100.0 * float(BODIES[body_key].period_days)
    )
    assert abs(payload["jd_tdb"] - expected_jd) < 1e-6


@pytest.mark.parametrize("body_key, _abbrev, _name, _jd_fn, _inv_fn", PLUTONIANS)
def test_plutonian_cli_requires_jd_or_sidereal_count(
        body_key, _abbrev, _name, _jd_fn, _inv_fn):
    with pytest.raises(SystemExit):
        cli_main([f"time-pluto-{body_key}"])
