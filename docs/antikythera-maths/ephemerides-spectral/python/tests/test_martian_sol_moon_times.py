"""v0.14.2 — Sol Moon Times: Martians (Phobos / Deimos).

Mirrors test_saturnian_sol_moon_times.py, scaled to two moons. Same
invariants (J2000-zero, after-one-period, inverse round-trip, NaN/Inf
rejection, CLI parsing, abbreviation uniqueness) plus Mars-specific
sanity checks:

  - Phobos's orbital period is SHORTER than Mars's solar day (the
    well-known retrograde-from-the-surface property).
  - Phobos and Deimos are NOT in mean-motion resonance: their period
    ratio is ~3.96, comfortably away from any small-integer ratio
    (analogous to the Callisto-not-in-Laplace test in
    test_galilean_sol_moon_times.py).
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


MARTIAN_MOONS = [
    # (body_key, abbrev, sol_time_name, jd_to_fn, to_jd_fn)
    ("phobos", "SMaPhT", "Sol Mars-Phobos Time",
     bridge.jd_to_sol_mars_phobos_time, bridge.sol_mars_phobos_time_to_jd),
    ("deimos", "SMaDeT", "Sol Mars-Deimos Time",
     bridge.jd_to_sol_mars_deimos_time, bridge.sol_mars_deimos_time_to_jd),
]


# ──────────────────────────────────────────────────────────────────────
# Bridge surface — per-Martian wrappers
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("body_key, abbrev, sol_time_name, jd_to_fn, _to_jd_fn", MARTIAN_MOONS)
def test_martian_bridge_at_j2000_returns_zero_count(
        body_key, abbrev, sol_time_name, jd_to_fn, _to_jd_fn):
    out = jd_to_fn(SOL_MOON_TIME_J2000_JD_TDB)
    assert out["ok"] is True
    assert out["body_name"] == body_key
    assert out["parent_name"] == "mars"
    assert out["sidereal_count"] == 0.0
    assert out["sidereal_phase"] == 0.0
    assert out["epoch"]["abbreviation"] == abbrev
    assert out["epoch"]["sol_time_name"] == sol_time_name


@pytest.mark.parametrize("body_key, _abbrev, _name, jd_to_fn, _to_jd_fn", MARTIAN_MOONS)
def test_martian_bridge_after_one_sidereal_period(
        body_key, _abbrev, _name, jd_to_fn, _to_jd_fn):
    period = float(BODIES[body_key].period_days)
    jd_one = SOL_MOON_TIME_J2000_JD_TDB + period
    out = jd_to_fn(jd_one)
    assert out["ok"] is True
    assert abs(out["sidereal_count"] - 1.0) < 1e-9
    assert abs(out["sidereal_phase"] - 0.0) < 1e-9 or abs(out["sidereal_phase"] - 1.0) < 1e-9


@pytest.mark.parametrize("body_key, abbrev, _name, jd_to_fn, to_jd_fn", MARTIAN_MOONS)
def test_martian_bridge_inverse_round_trip(
        body_key, abbrev, _name, jd_to_fn, to_jd_fn):
    jd0 = SOL_MOON_TIME_J2000_JD_TDB + 365.25 * 20.0  # +20 yr
    out = jd_to_fn(jd0)
    assert out["ok"] is True
    inv = to_jd_fn(out["sidereal_count"])
    assert inv["ok"] is True
    assert abs(inv["jd_tdb"] - jd0) < 1e-6
    assert inv["abbreviation"] == abbrev
    assert inv["body_name"] == body_key


def test_martian_abbreviations_are_unique() -> None:
    """Phobos (SMaPhT) and Deimos (SMaDeT) must be distinct under the
    6-letter `S<Planet2><Moon2>T` convention.
    """
    abbrevs = {abbrev for _, abbrev, *_ in MARTIAN_MOONS}
    assert len(abbrevs) == 2, f"expected 2 unique abbrevs, got {abbrevs}"


def test_martian_abbreviations_dont_collide_with_galileans_or_saturnians() -> None:
    """All 4 Galilean (SJu*), 11 Saturnian (SSa*), and 2 Martian (SMa*)
    abbreviations must be globally distinct."""
    galilean_abbrevs = {"SJuIoT", "SJuEuT", "SJuGaT", "SJuCaT"}
    saturnian_abbrevs = {
        "SSaMiT", "SSaEnT", "SSaTeT", "SSaDiT", "SSaRhT", "SSaTiT",
        "SSaHyT", "SSaIaT", "SSaPhT", "SSaJaT", "SSaEpT",
    }
    martian_abbrevs = {abbrev for _, abbrev, *_ in MARTIAN_MOONS}
    assert galilean_abbrevs.isdisjoint(martian_abbrevs), (
        f"abbreviation collision between Galileans and Martians: "
        f"{galilean_abbrevs & martian_abbrevs}"
    )
    assert saturnian_abbrevs.isdisjoint(martian_abbrevs), (
        f"abbreviation collision between Saturnians and Martians: "
        f"{saturnian_abbrevs & martian_abbrevs}"
    )


@pytest.mark.parametrize("body_key, _abbrev, _name, jd_to_fn, _to_jd_fn", MARTIAN_MOONS)
def test_martian_bridge_rejects_non_finite_jd(
        body_key, _abbrev, _name, jd_to_fn, _to_jd_fn):
    out = jd_to_fn(float("nan"))
    assert out["ok"] is False
    out = jd_to_fn(float("inf"))
    assert out["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# CLI surface — time-mars-{moon}
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("body_key, abbrev, _name, _jd_fn, _inv_fn", MARTIAN_MOONS)
def test_martian_cli_jd_path(body_key, abbrev, _name, _jd_fn, _inv_fn):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main([f"time-mars-{body_key}", "--jd", "2451545.0"])
    assert rc == 0
    payload = json.loads(buf.getvalue())
    assert payload["ok"] is True
    assert payload["body_name"] == body_key
    assert payload["parent_name"] == "mars"
    assert payload["epoch"]["abbreviation"] == abbrev


@pytest.mark.parametrize("body_key, abbrev, _name, _jd_fn, _inv_fn", MARTIAN_MOONS)
def test_martian_cli_inverse_path(body_key, abbrev, _name, _jd_fn, _inv_fn):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main([f"time-mars-{body_key}", "--sidereal-count", "100"])
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


@pytest.mark.parametrize("body_key, _abbrev, _name, _jd_fn, _inv_fn", MARTIAN_MOONS)
def test_martian_cli_requires_jd_or_sidereal_count(
        body_key, _abbrev, _name, _jd_fn, _inv_fn):
    with pytest.raises(SystemExit):
        cli_main([f"time-mars-{body_key}"])


# ──────────────────────────────────────────────────────────────────────
# Mars-specific sanity witnesses.
#   - Phobos's orbital period is shorter than Mars's solar day (rises
#     in the west from Mars's surface).
#   - Phobos and Deimos are NOT in mean-motion resonance (period ratio
#     ~3.96 is comfortably non-small-integer — same tolerance as the
#     Callisto-not-in-Laplace test).
# ──────────────────────────────────────────────────────────────────────

def test_phobos_period_shorter_than_mars_solar_day() -> None:
    """Phobos's sidereal period (~7h 39m = 0.319 d) is SHORTER than
    Mars's own solar day (~24h 39m, very close to Earth's 1 d). This
    is what makes Phobos rise in the west from Mars's surface — the
    moon orbits faster than the planet rotates.

    A direct numeric Mars-solar-day value isn't carried in BODIES
    (BODIES[`mars`].period_days is the orbital year, 686.98 d). We
    therefore compare against an explicit literal lower bound (1.0 d)
    that any reasonable Mars solar-day value comfortably exceeds, and
    sanity-check that the ratio is the right way around.
    """
    p_phobos_days = float(BODIES["phobos"].period_days)
    # Phobos period is < 1 day (and well under Mars's ~1.0275-day solar day).
    assert p_phobos_days < 1.0, (
        f"Phobos sidereal period {p_phobos_days} d unexpectedly ≥ 1.0 d — "
        f"this would invalidate the 'rises in the west' property."
    )
    # Sanity: Phobos period much shorter than Deimos period.
    p_deimos_days = float(BODIES["deimos"].period_days)
    assert p_phobos_days < p_deimos_days, (
        f"Phobos period {p_phobos_days} d not < Deimos period {p_deimos_days} d "
        f"— BODIES values may have been swapped."
    )


def test_phobos_deimos_not_in_small_integer_resonance() -> None:
    """Phobos and Deimos have no established mean-motion resonance.
    Their period ratio T_Deimos / T_Phobos ≈ 3.958 is NOT close enough
    to 4.0 to qualify as a 4:1 mean-motion resonance under the typical
    libration-amplitude criterion (resonant pairs in the literature
    sit within ≲0.1% of the integer ratio — the Galilean 2:1 pairs
    are at parts-per-thousand; the Saturnian 2:1 Enceladus-Dione
    likewise).

    The Phobos-Deimos ratio is ~1% off 4:1 — which is "near a
    small-integer ratio" geometrically but well outside the band
    where libration would lock the pair.

    Analogue of test_callisto_is_not_in_laplace_resonance for the
    Galileans, with a tolerance appropriate to this pair (not the
    Galilean ≳10% gap that test uses, since Phobos-Deimos genuinely
    sit closer to a small-integer ratio).
    """
    p_phobos = float(BODIES["phobos"].period_days)
    p_deimos = float(BODIES["deimos"].period_days)
    # n_Phobos / n_Deimos = T_Deimos / T_Phobos ≈ 3.958 (NOT 4.0).
    n_phobos = 1.0 / p_phobos
    n_deimos = 1.0 / p_deimos
    ratio = n_phobos / n_deimos
    # Real-world Phobos-Deimos ratio: ~3.958. The literature does NOT
    # classify them as a 4:1 mean-motion resonance — the pair would need
    # to be within ~0.1% of 4.0 for libration to actually lock. We
    # confirm the ratio sits in the >0.5% off-band, NOT in the ≲0.1%
    # locked band.
    assert abs(ratio - 4.0) / 4.0 > 5e-3, (
        f"Phobos/Deimos ratio {ratio:.4f} is within 0.5% of 4.0 — "
        f"would imply a 4:1 mean-motion resonance not present in the "
        f"established literature."
    )
    # And the ratio is bounded above 3.9 (i.e. genuinely close-ish to
    # 4 but on the low side, as established by JPL HORIZONS).
    assert 3.9 < ratio < 4.0, (
        f"Phobos/Deimos ratio {ratio:.4f} outside the expected "
        f"(3.9, 4.0) band — BODIES values may have drifted."
    )
