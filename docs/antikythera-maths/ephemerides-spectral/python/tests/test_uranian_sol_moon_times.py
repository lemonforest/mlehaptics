"""v0.14.2 — Sol Moon Times: Uranians (Titania only, for now).

Mirrors test_saturnian_sol_moon_times.py shape, scaled to a single
moon. Currently Titania is the only Uranian in BODIES; Oberon /
Umbriel / Ariel / Miranda are queued for a future ship. Same
invariants as the Galilean / Saturnian families (J2000-zero,
after-one-period, inverse round-trip, NaN/Inf rejection, CLI
parsing) plus an explicit cross-check that SUrTiT (Titania) does
NOT collide with SSaTiT (Saturn's Titan) — both share the `Ti`
moon prefix, but the parent prefix (`Ur` vs `Sa`) keeps them
globally distinct under the v0.14.1 6-letter abbreviation policy.
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


URANIANS = [
    # (body_key, abbrev, sol_time_name, jd_to_fn, to_jd_fn)
    ("titania", "SUrTiT", "Sol Uranus-Titania Time",
     bridge.jd_to_sol_uranus_titania_time, bridge.sol_uranus_titania_time_to_jd),
]


# ──────────────────────────────────────────────────────────────────────
# Bridge surface — per-Uranian wrappers
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("body_key, abbrev, sol_time_name, jd_to_fn, _to_jd_fn", URANIANS)
def test_uranian_bridge_at_j2000_returns_zero_count(
        body_key, abbrev, sol_time_name, jd_to_fn, _to_jd_fn):
    out = jd_to_fn(SOL_MOON_TIME_J2000_JD_TDB)
    assert out["ok"] is True
    assert out["body_name"] == body_key
    assert out["parent_name"] == "uranus"
    assert out["sidereal_count"] == 0.0
    assert out["sidereal_phase"] == 0.0
    assert out["epoch"]["abbreviation"] == abbrev
    assert out["epoch"]["sol_time_name"] == sol_time_name


@pytest.mark.parametrize("body_key, _abbrev, _name, jd_to_fn, _to_jd_fn", URANIANS)
def test_uranian_bridge_after_one_sidereal_period(
        body_key, _abbrev, _name, jd_to_fn, _to_jd_fn):
    period = float(BODIES[body_key].period_days)
    jd_one = SOL_MOON_TIME_J2000_JD_TDB + period
    out = jd_to_fn(jd_one)
    assert out["ok"] is True
    assert abs(out["sidereal_count"] - 1.0) < 1e-9
    assert abs(out["sidereal_phase"] - 0.0) < 1e-9 or abs(out["sidereal_phase"] - 1.0) < 1e-9


@pytest.mark.parametrize("body_key, abbrev, _name, jd_to_fn, to_jd_fn", URANIANS)
def test_uranian_bridge_inverse_round_trip(
        body_key, abbrev, _name, jd_to_fn, to_jd_fn):
    jd0 = SOL_MOON_TIME_J2000_JD_TDB + 365.25 * 20.0  # +20 yr
    out = jd_to_fn(jd0)
    assert out["ok"] is True
    inv = to_jd_fn(out["sidereal_count"])
    assert inv["ok"] is True
    assert abs(inv["jd_tdb"] - jd0) < 1e-6
    assert inv["abbreviation"] == abbrev
    assert inv["body_name"] == body_key


def test_titania_period_matches_bodies_roster() -> None:
    """Titania's sidereal period is pulled from BODIES at call time;
    the v0.14.2 ship spec'd it at 8.70586900 days. Pin that here so
    a future BODIES tweak can't silently drift the time scale.
    """
    assert float(BODIES["titania"].period_days) == 8.70586900


def test_titania_abbreviation_is_six_letters() -> None:
    """v0.14.1 policy: all moon abbreviations are 6-letter
    `S<Planet2><Moon2>T`. SUrTiT → S + Ur + Ti + T = 6 letters.
    """
    out = bridge.jd_to_sol_uranus_titania_time(SOL_MOON_TIME_J2000_JD_TDB)
    abbrev = out["epoch"]["abbreviation"]
    assert abbrev == "SUrTiT"
    assert len(abbrev) == 6


def test_titania_does_not_collide_with_saturn_titan() -> None:
    """Cross-check: SUrTiT (Titania, Uranus) and SSaTiT (Titan, Saturn)
    share the `Ti` moon prefix but differ in the parent prefix
    (`Ur` vs `Sa`), so the abbreviations are globally distinct under
    the v0.14.1 6-letter policy. Without that policy switch (the old
    4-letter `S<Planet><Moon>T` form) both moons would have
    collapsed to `STiT` — the kind of collision the policy was
    designed to head off.
    """
    titania = bridge.jd_to_sol_uranus_titania_time(SOL_MOON_TIME_J2000_JD_TDB)
    titan   = bridge.jd_to_sol_saturn_titan_time(SOL_MOON_TIME_J2000_JD_TDB)
    a_titania = titania["epoch"]["abbreviation"]
    a_titan   = titan["epoch"]["abbreviation"]
    assert a_titania == "SUrTiT"
    assert a_titan == "SSaTiT"
    assert a_titania != a_titan
    # And confirm both share the `Ti` moon prefix — that's the whole
    # point of the cross-check; if a future rename drops the shared
    # `Ti` we want the test to scream so we re-evaluate.
    assert "Ti" in a_titania and "Ti" in a_titan
    # And the parent prefixes are what disambiguate them.
    assert a_titania[1:3] == "Ur"
    assert a_titan[1:3]   == "Sa"


def test_uranian_abbreviations_dont_collide_with_galileans_or_saturnians() -> None:
    """SUrTiT must not collide with any Galilean (SJu*) or any
    Saturnian (SSa*) abbreviation."""
    galilean_abbrevs = {"SJuIoT", "SJuEuT", "SJuGaT", "SJuCaT"}
    saturnian_abbrevs = {
        "SSaMiT", "SSaEnT", "SSaTeT", "SSaDiT", "SSaRhT", "SSaTiT",
        "SSaHyT", "SSaIaT", "SSaPhT", "SSaJaT", "SSaEpT",
    }
    uranian_abbrevs = {abbrev for _, abbrev, *_ in URANIANS}
    assert galilean_abbrevs.isdisjoint(uranian_abbrevs), (
        f"abbreviation collision between Galileans and Uranians: "
        f"{galilean_abbrevs & uranian_abbrevs}"
    )
    assert saturnian_abbrevs.isdisjoint(uranian_abbrevs), (
        f"abbreviation collision between Saturnians and Uranians: "
        f"{saturnian_abbrevs & uranian_abbrevs}"
    )


@pytest.mark.parametrize("body_key, _abbrev, _name, jd_to_fn, _to_jd_fn", URANIANS)
def test_uranian_bridge_rejects_non_finite_jd(
        body_key, _abbrev, _name, jd_to_fn, _to_jd_fn):
    out = jd_to_fn(float("nan"))
    assert out["ok"] is False
    out = jd_to_fn(float("inf"))
    assert out["ok"] is False
    out = jd_to_fn(float("-inf"))
    assert out["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# CLI surface — time-uranus-{moon}
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("body_key, abbrev, _name, _jd_fn, _inv_fn", URANIANS)
def test_uranian_cli_jd_path(body_key, abbrev, _name, _jd_fn, _inv_fn):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main([f"time-uranus-{body_key}", "--jd", "2451545.0"])
    assert rc == 0
    payload = json.loads(buf.getvalue())
    assert payload["ok"] is True
    assert payload["body_name"] == body_key
    assert payload["parent_name"] == "uranus"
    assert payload["epoch"]["abbreviation"] == abbrev


@pytest.mark.parametrize("body_key, abbrev, _name, _jd_fn, _inv_fn", URANIANS)
def test_uranian_cli_inverse_path(body_key, abbrev, _name, _jd_fn, _inv_fn):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main([f"time-uranus-{body_key}", "--sidereal-count", "100"])
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


@pytest.mark.parametrize("body_key, _abbrev, _name, _jd_fn, _inv_fn", URANIANS)
def test_uranian_cli_requires_jd_or_sidereal_count(
        body_key, _abbrev, _name, _jd_fn, _inv_fn):
    with pytest.raises(SystemExit):
        cli_main([f"time-uranus-{body_key}"])
