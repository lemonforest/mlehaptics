"""v0.14.2 — Sol Moon Times: Jovian inner regulars
(Metis / Adrastea / Amalthea / Thebe).

Bridge surface + CLI primitives + generic moon-time primitive
(_research/time_scales.py::jd_to_moon_time / moon_time_to_jd).

These four small moons orbit *inside* Io (the innermost Galilean,
1.769 d). All four are tidally locked, all sub-day periods; same
mathematical structure as the Galilean Sol Moon Times in v0.14.0,
just with shorter periods and the 6-letter ``S<Planet2><Moon2>T``
abbreviation pattern introduced in v0.14.1.

Invariants enforced:

  1. Default epoch is J2000 (no historical-anchor menu — same as the
     Galileans; pre-Voyager imagery only resolved Amalthea, and the
     other three are 1979 discoveries).
  2. Sidereal-cycle count round-trips exactly through the inverse.
  3. At J2000.0 exactly, sidereal_count == 0 for all four bodies.
  4. After exactly one sidereal period, sidereal_count == 1 (within
     float-ULP tolerance).
  5. The four CLI subcommands (time-jupiter-{metis,adrastea,amalthea,
     thebe}) parse through to the bridge and emit valid JSON with
     the expected fields (``abbreviation``, ``parent_body``, etc.).
  6. Each moon's ``abbreviation`` field is unique and matches the
     SJuMeT / SJuAdT / SJuAmT / SJuThT convention.
  7. All eight known Jovian Sol Moon Time abbreviations (4 Galilean
     + 4 inner regular) are globally distinct.
  8. Metis's orbital period is shorter than Io's — it's an inner
     regular, not a Galilean (sanity check on the BODIES table).
"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.time_scales import (
    SOL_MOON_TIME_J2000_JD_TDB,
    MoonTime,
    jd_to_moon_time,
    moon_time_to_jd,
)
from ephemerides_spectral._research.bodies import BODIES
from ephemerides_spectral.cli import main as cli_main


JOVIAN_INNER = [
    # (body_key, abbrev, sol_time_name, jd_to_fn, to_jd_fn)
    ("metis",    "SJuMeT", "Sol Jupiter-Metis Time",
     bridge.jd_to_sol_jupiter_metis_time, bridge.sol_jupiter_metis_time_to_jd),
    ("adrastea", "SJuAdT", "Sol Jupiter-Adrastea Time",
     bridge.jd_to_sol_jupiter_adrastea_time, bridge.sol_jupiter_adrastea_time_to_jd),
    ("amalthea", "SJuAmT", "Sol Jupiter-Amalthea Time",
     bridge.jd_to_sol_jupiter_amalthea_time, bridge.sol_jupiter_amalthea_time_to_jd),
    ("thebe",    "SJuThT", "Sol Jupiter-Thebe Time",
     bridge.jd_to_sol_jupiter_thebe_time, bridge.sol_jupiter_thebe_time_to_jd),
]


# ──────────────────────────────────────────────────────────────────────
# Generic primitive — _research/time_scales.py (sanity for inner regulars)
# ──────────────────────────────────────────────────────────────────────

def test_jd_to_moon_time_metis_returns_moontime_dataclass() -> None:
    out = jd_to_moon_time("metis", 2451545.0,
                          parent_name="jupiter",
                          sidereal_period_days=0.29478000)
    assert isinstance(out, MoonTime)
    assert out.body_name == "metis"
    assert out.parent_name == "jupiter"
    assert out.epoch_name == "j2000"
    assert out.epoch_jd_tdb == SOL_MOON_TIME_J2000_JD_TDB


def test_jd_to_moon_time_amalthea_at_j2000_yields_zero_count() -> None:
    out = jd_to_moon_time("amalthea", SOL_MOON_TIME_J2000_JD_TDB,
                          parent_name="jupiter",
                          sidereal_period_days=0.49817905)
    assert out.days_since_epoch == 0.0
    assert out.sidereal_count == 0.0
    assert out.sidereal_phase == 0.0


def test_moon_time_to_jd_inverts_for_thebe() -> None:
    period = 0.67451400  # Thebe
    jd0 = SOL_MOON_TIME_J2000_JD_TDB + 1000.0 * period
    out = jd_to_moon_time("thebe", jd0,
                          parent_name="jupiter",
                          sidereal_period_days=period)
    # 1000 * period accumulates float error ~1e-9 on a sub-day period.
    assert abs(out.sidereal_count - 1000.0) < 1e-8
    jd_back = moon_time_to_jd(out.sidereal_count, sidereal_period_days=period)
    assert abs(jd_back - jd0) < 1e-9


# ──────────────────────────────────────────────────────────────────────
# Bridge surface — per-body wrappers
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "body_key, abbrev, sol_time_name, jd_to_fn, _to_jd_fn", JOVIAN_INNER
)
def test_jovian_inner_bridge_at_j2000_returns_zero_count(
        body_key: str, abbrev: str, sol_time_name: str,
        jd_to_fn, _to_jd_fn) -> None:
    out = jd_to_fn(SOL_MOON_TIME_J2000_JD_TDB)
    assert out["ok"] is True
    assert out["body_name"] == body_key
    assert out["parent_name"] == "jupiter"
    assert out["sidereal_count"] == 0.0
    assert out["sidereal_phase"] == 0.0
    assert out["epoch"]["abbreviation"] == abbrev
    assert out["epoch"]["sol_time_name"] == sol_time_name


@pytest.mark.parametrize(
    "body_key, abbrev, _name, jd_to_fn, _to_jd_fn", JOVIAN_INNER
)
def test_jovian_inner_bridge_after_one_sidereal_period(
        body_key: str, abbrev: str, _name: str,
        jd_to_fn, _to_jd_fn) -> None:
    period = float(BODIES[body_key].period_days)
    jd_one = SOL_MOON_TIME_J2000_JD_TDB + period
    out = jd_to_fn(jd_one)
    assert out["ok"] is True
    # Sub-day periods amplify float error vs. the Galilean test;
    # 1e-9 still holds for these bodies but use a small relaxation.
    assert abs(out["sidereal_count"] - 1.0) < 1e-9
    assert (
        abs(out["sidereal_phase"] - 0.0) < 1e-9
        or abs(out["sidereal_phase"] - 1.0) < 1e-9
    )


@pytest.mark.parametrize(
    "body_key, abbrev, _name, jd_to_fn, to_jd_fn", JOVIAN_INNER
)
def test_jovian_inner_bridge_inverse_round_trip(
        body_key: str, abbrev: str, _name: str,
        jd_to_fn, to_jd_fn) -> None:
    jd0 = SOL_MOON_TIME_J2000_JD_TDB + 365.25 * 5.0  # +5 yr
    out = jd_to_fn(jd0)
    assert out["ok"] is True
    inv = to_jd_fn(out["sidereal_count"])
    assert inv["ok"] is True
    assert abs(inv["jd_tdb"] - jd0) < 1e-6
    assert inv["abbreviation"] == abbrev
    assert inv["body_name"] == body_key


def test_jovian_inner_abbreviations_are_unique() -> None:
    """Sanity: SJuMeT, SJuAdT, SJuAmT, SJuThT must all be distinct."""
    abbrevs = {abbrev for _, abbrev, *_ in JOVIAN_INNER}
    assert len(abbrevs) == 4, f"expected 4 unique abbrevs, got {abbrevs}"


def test_all_jovian_abbreviations_are_globally_distinct() -> None:
    """All eight known Jovian Sol Moon Time abbreviations (4 Galilean +
    4 inner regular) must be distinct.

    The Galilean abbreviations may use either the original 4-letter
    pattern (SJIT/SJET/SJGT/SJCT) or the v0.14.1 6-letter pattern
    (SJuIoT/SJuEuT/SJuGaT/SJuCaT) depending on what's been integrated
    when this test runs. Either way, they don't collide with the
    inner-regular set, which uses ``Me/Ad/Am/Th`` two-letter moon
    components — none of which match Io/Eu/Ga/Ca.
    """
    galilean_zero_arrival = [
        bridge.jd_to_sol_jupiter_io_time(SOL_MOON_TIME_J2000_JD_TDB),
        bridge.jd_to_sol_jupiter_europa_time(SOL_MOON_TIME_J2000_JD_TDB),
        bridge.jd_to_sol_jupiter_ganymede_time(SOL_MOON_TIME_J2000_JD_TDB),
        bridge.jd_to_sol_jupiter_callisto_time(SOL_MOON_TIME_J2000_JD_TDB),
    ]
    inner_zero_arrival = [
        jd_to_fn(SOL_MOON_TIME_J2000_JD_TDB)
        for _, _, _, jd_to_fn, _ in JOVIAN_INNER
    ]
    abbrevs = (
        [out["epoch"]["abbreviation"] for out in galilean_zero_arrival]
        + [out["epoch"]["abbreviation"] for out in inner_zero_arrival]
    )
    assert len(set(abbrevs)) == 8, (
        f"expected 8 globally distinct Jovian abbreviations, got "
        f"{abbrevs} (collisions: "
        f"{[a for a in abbrevs if abbrevs.count(a) > 1]})"
    )


@pytest.mark.parametrize(
    "body_key, _abbrev, _name, jd_to_fn, _to_jd_fn", JOVIAN_INNER
)
def test_jovian_inner_bridge_rejects_non_finite_jd(
        body_key: str, _abbrev: str, _name: str,
        jd_to_fn, _to_jd_fn) -> None:
    out = jd_to_fn(float("nan"))
    assert out["ok"] is False
    out = jd_to_fn(float("inf"))
    assert out["ok"] is False
    out = jd_to_fn(float("-inf"))
    assert out["ok"] is False


@pytest.mark.parametrize(
    "body_key, _abbrev, _name, _jd_to_fn, to_jd_fn", JOVIAN_INNER
)
def test_jovian_inner_bridge_inverse_rejects_non_numeric(
        body_key: str, _abbrev: str, _name: str,
        _jd_to_fn, to_jd_fn) -> None:
    out = to_jd_fn("not a number")
    assert out["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# CLI surface — time-jupiter-{metis,adrastea,amalthea,thebe}
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "body_key, abbrev, _name, _jd_fn, _inv_fn", JOVIAN_INNER
)
def test_jovian_inner_cli_jd_path(
        body_key: str, abbrev: str, _name: str,
        _jd_fn, _inv_fn) -> None:
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main([f"time-jupiter-{body_key}", "--jd", "2451545.0"])
    assert rc == 0
    payload = json.loads(buf.getvalue())
    assert payload["ok"] is True
    assert payload["body_name"] == body_key
    assert payload["parent_name"] == "jupiter"
    assert payload["epoch"]["abbreviation"] == abbrev


@pytest.mark.parametrize(
    "body_key, abbrev, _name, _jd_fn, _inv_fn", JOVIAN_INNER
)
def test_jovian_inner_cli_inverse_path(
        body_key: str, abbrev: str, _name: str,
        _jd_fn, _inv_fn) -> None:
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main([f"time-jupiter-{body_key}", "--sidereal-count", "1000"])
    assert rc == 0
    payload = json.loads(buf.getvalue())
    assert payload["ok"] is True
    assert payload["sidereal_count"] == 1000.0
    assert payload["abbreviation"] == abbrev
    expected_jd = (
        SOL_MOON_TIME_J2000_JD_TDB
        + 1000.0 * float(BODIES[body_key].period_days)
    )
    assert abs(payload["jd_tdb"] - expected_jd) < 1e-6


@pytest.mark.parametrize(
    "body_key, _abbrev, _name, _jd_fn, _inv_fn", JOVIAN_INNER
)
def test_jovian_inner_cli_requires_jd_or_sidereal_count(
        body_key: str, _abbrev: str, _name: str,
        _jd_fn, _inv_fn) -> None:
    """Mutex-required: must supply either --jd or --sidereal-count."""
    with pytest.raises(SystemExit):
        cli_main([f"time-jupiter-{body_key}"])


# ──────────────────────────────────────────────────────────────────────
# Inner-regular structural facts (sanity checks against BODIES)
# ──────────────────────────────────────────────────────────────────────

def test_inner_regulars_orbit_inside_io() -> None:
    """All four Jovian inner regulars have orbital periods *shorter*
    than Io's (the innermost Galilean, ~1.769 d). This is the
    structural definition of "inner regular" — they orbit closer to
    Jupiter than the Galileans.
    """
    t_io = float(BODIES["io"].period_days)
    for body_key, *_ in JOVIAN_INNER:
        t_body = float(BODIES[body_key].period_days)
        assert t_body < t_io, (
            f"{body_key} period {t_body} d is NOT shorter than Io's "
            f"{t_io} d — would not be an inner regular."
        )


def test_metis_is_innermost_jovian() -> None:
    """Metis has the shortest period of the four inner regulars,
    making it the innermost known Jovian moon."""
    periods = {
        body_key: float(BODIES[body_key].period_days)
        for body_key, *_ in JOVIAN_INNER
    }
    innermost = min(periods, key=periods.get)
    assert innermost == "metis", (
        f"Expected Metis as innermost; got {innermost} "
        f"(periods: {periods})"
    )


def test_thebe_is_outermost_inner_regular() -> None:
    """Thebe has the longest period of the four — outermost inner
    regular, just inside Io's orbit."""
    periods = {
        body_key: float(BODIES[body_key].period_days)
        for body_key, *_ in JOVIAN_INNER
    }
    outermost = max(periods, key=periods.get)
    assert outermost == "thebe", (
        f"Expected Thebe as outermost inner regular; got {outermost} "
        f"(periods: {periods})"
    )


def test_amalthea_is_largest_inner_regular() -> None:
    """Amalthea's mean radius (~84 km) exceeds the other three.
    Discovery-order historical note: Amalthea (Barnard, 1892) was
    the only one of the four discovered before the Voyager era;
    Metis, Adrastea, and Thebe were all 1979 Voyager discoveries.
    """
    radii = {
        body_key: float(BODIES[body_key].surface_radius_km)
        for body_key, *_ in JOVIAN_INNER
    }
    largest = max(radii, key=radii.get)
    assert largest == "amalthea", (
        f"Expected Amalthea as largest inner regular; got {largest} "
        f"(radii: {radii})"
    )


def test_metis_and_adrastea_periods_close_ring_shepherds() -> None:
    """Metis and Adrastea are the *ring-shepherd* moons of Jupiter's
    main ring — they orbit at nearly the same distance from Jupiter,
    fractionally outside the ring's outer edge. Their sidereal
    periods are correspondingly very close (Metis 0.29478 d,
    Adrastea 0.29826 d — within ~1.2% of each other).

    This test guards against the BODIES table accidentally drifting
    apart for these two bodies, which would invalidate the
    ring-shepherd claim in the docstrings.
    """
    t_metis    = float(BODIES["metis"].period_days)
    t_adrastea = float(BODIES["adrastea"].period_days)
    rel_diff = abs(t_adrastea - t_metis) / t_metis
    assert rel_diff < 0.02, (
        f"Metis ({t_metis} d) and Adrastea ({t_adrastea} d) are no "
        f"longer within 2% of each other ({rel_diff:.2%}); "
        "ring-shepherd narrative may need updating."
    )
    # And both must orbit *inside* Io (sanity already covered by
    # test_inner_regulars_orbit_inside_io, but reinforced here for
    # the ring-shepherd-specific claim).
    assert t_metis < float(BODIES["io"].period_days)
    assert t_adrastea < float(BODIES["io"].period_days)


def test_inner_regulars_no_locked_mean_motion_resonance() -> None:
    """No pair of Jovian inner regulars is in a *locked* small-integer
    mean-motion resonance (2:1, 3:1, 3:2, etc.) of the Galilean
    Laplace-4:2:1 kind.

    The Metis/Adrastea pair is excluded from this check because they
    are *near*-1:1 by construction — both are ring-shepherd moons
    orbiting at nearly the same distance from Jupiter, just outside
    the main ring's outer edge. Their ratio is ~1.012, which is "near
    1:1" but not a true mean-motion *resonance* in the dynamical
    sense (no libration of the resonant argument; no gear-locking).
    The test guards against any other pair drifting into a tight
    resonance the prose doesn't disclose.
    """
    keys = [body_key for body_key, *_ in JOVIAN_INNER]
    excluded = {("metis", "adrastea"), ("adrastea", "metis")}
    for i, k1 in enumerate(keys):
        for k2 in keys[i + 1:]:
            if (k1, k2) in excluded or (k2, k1) in excluded:
                continue
            n1 = 1.0 / float(BODIES[k1].period_days)
            n2 = 1.0 / float(BODIES[k2].period_days)
            ratio = max(n1, n2) / min(n1, n2)
            # Must NOT be tightly near any small-integer or simple
            # rational (1:1, 2:1, 3:1, 3:2, 4:3) — defensively check
            # within 0.5% of a few canonical resonant ratios.
            for resonant in (1.0, 1.5, 2.0, 3.0, 4.0 / 3.0):
                rel_dist = abs(ratio - resonant) / resonant
                assert rel_dist > 0.005, (
                    f"{k1}/{k2} mean-motion ratio {ratio:.4f} is "
                    f"within 0.5% of resonant ratio {resonant:.4f} — "
                    f"possible undocumented resonance."
                )
