"""v0.14.2 + v0.16.0 — Sol Moon Times: Neptunian roster.

v0.14.2 shipped Triton alone. v0.16.0 adds Proteus (second-largest
Neptunian, near-spherical despite small size, fills sub-graph between
Triton's 5.88 d and the deferred inner-Neptunian close-packed cluster)
and Nereid (most eccentric major-moon orbit in the solar system,
e=0.749, period ~360.13 d extends Neptune's low-frequency tail).

Same invariants as the v0.14.x / v0.15.0 family tests (J2000-zero,
after-one-period, inverse round-trip, NaN/Inf rejection, CLI parsing,
abbreviation uniqueness vs. all prior families).

EDGE-CASE NOTE FOR FUTURE MAINTAINERS — TRITON IS RETROGRADE
============================================================
Triton is the only large moon in the solar system that orbits its
parent planet RETROGRADE (backward relative to Neptune's rotation).
This is strong evidence that Triton is a captured Kuiper Belt
object, not a primordial Neptunian moon. Because of the retrograde
orbit, tidal interactions DECELERATE Triton (instead of accelerating
it as for prograde moons), so its orbit is decaying inward — in
~3.6 Gyr it will cross Neptune's Roche limit and be torn apart into
a ring system.

The Sol Time encoder convention (per v0.5.4 Sol Uranian Time) keeps
``sidereal_period_days`` POSITIVE (5.87685400) regardless of orbital
direction — the encoder advances ``omega = +2π/P`` for all bodies,
so the Sol Time count proceeds positive-monotonically. Retrograde-ness
is documented in the bridge / CLI prose but does not enter the
time-scale arithmetic. The tests here verify the count is positive
and monotone, exactly as for prograde moons.
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


NEPTUNIANS = [
    # (body_key, abbrev, sol_time_name, jd_to_fn, to_jd_fn)
    # v0.14.2
    ("triton", "SNeTrT", "Sol Neptune-Triton Time",
     bridge.jd_to_sol_neptune_triton_time, bridge.sol_neptune_triton_time_to_jd),
    # v0.16.0 — Proteus + Nereid (sub-graph completion)
    ("proteus", "SNePrT", "Sol Neptune-Proteus Time",
     bridge.jd_to_sol_neptune_proteus_time, bridge.sol_neptune_proteus_time_to_jd),
    ("nereid", "SNeNeT", "Sol Neptune-Nereid Time",
     bridge.jd_to_sol_neptune_nereid_time, bridge.sol_neptune_nereid_time_to_jd),
]


# ──────────────────────────────────────────────────────────────────────
# Bridge surface — per-Neptunian wrappers
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("body_key, abbrev, sol_time_name, jd_to_fn, _to_jd_fn", NEPTUNIANS)
def test_neptunian_bridge_at_j2000_returns_zero_count(
        body_key, abbrev, sol_time_name, jd_to_fn, _to_jd_fn):
    out = jd_to_fn(SOL_MOON_TIME_J2000_JD_TDB)
    assert out["ok"] is True
    assert out["body_name"] == body_key
    assert out["parent_name"] == "neptune"
    assert out["sidereal_count"] == 0.0
    assert out["sidereal_phase"] == 0.0
    assert out["epoch"]["abbreviation"] == abbrev
    assert out["epoch"]["sol_time_name"] == sol_time_name


@pytest.mark.parametrize("body_key, _abbrev, _name, jd_to_fn, _to_jd_fn", NEPTUNIANS)
def test_neptunian_bridge_after_one_sidereal_period(
        body_key, _abbrev, _name, jd_to_fn, _to_jd_fn):
    period = float(BODIES[body_key].period_days)
    jd_one = SOL_MOON_TIME_J2000_JD_TDB + period
    out = jd_to_fn(jd_one)
    assert out["ok"] is True
    # Despite retrograde orbit, the count is positive (encoder uses
    # +omega for all bodies — see module docstring).
    assert abs(out["sidereal_count"] - 1.0) < 1e-9
    assert abs(out["sidereal_phase"] - 0.0) < 1e-9 or abs(out["sidereal_phase"] - 1.0) < 1e-9


@pytest.mark.parametrize("body_key, abbrev, _name, jd_to_fn, to_jd_fn", NEPTUNIANS)
def test_neptunian_bridge_inverse_round_trip(
        body_key, abbrev, _name, jd_to_fn, to_jd_fn):
    jd0 = SOL_MOON_TIME_J2000_JD_TDB + 365.25 * 20.0  # +20 yr
    out = jd_to_fn(jd0)
    assert out["ok"] is True
    inv = to_jd_fn(out["sidereal_count"])
    assert inv["ok"] is True
    assert abs(inv["jd_tdb"] - jd0) < 1e-6
    assert inv["abbreviation"] == abbrev
    assert inv["body_name"] == body_key


def test_neptunian_abbreviations_are_unique() -> None:
    """Sanity: every Neptunian abbreviation is internally distinct
    under the 6-letter `S<Planet2><Moon2>T` convention. v0.14.2
    shipped only Triton (SNeTrT); v0.16.0 added Proteus (SNePrT)
    and Nereid (SNeNeT) — three distinct abbreviations."""
    abbrevs = {abbrev for _, abbrev, *_ in NEPTUNIANS}
    assert len(abbrevs) == len(NEPTUNIANS), (
        f"expected {len(NEPTUNIANS)} unique abbrevs, got {abbrevs}"
    )


def test_neptunian_abbreviations_dont_collide_with_galileans_or_saturnians() -> None:
    """The Triton abbreviation (SNeTrT) must be globally distinct
    from the 4 Galilean (SJu*) and 11 Saturnian (SSa*) abbreviations.
    """
    galilean_abbrevs = {"SJuIoT", "SJuEuT", "SJuGaT", "SJuCaT"}
    saturnian_abbrevs = {
        "SSaMiT", "SSaEnT", "SSaTeT", "SSaDiT", "SSaRhT",
        "SSaTiT", "SSaHyT", "SSaIaT", "SSaPhT", "SSaJaT", "SSaEpT",
    }
    neptunian_abbrevs = {abbrev for _, abbrev, *_ in NEPTUNIANS}
    assert galilean_abbrevs.isdisjoint(neptunian_abbrevs), (
        f"abbreviation collision between Galileans and Neptunians: "
        f"{galilean_abbrevs & neptunian_abbrevs}"
    )
    assert saturnian_abbrevs.isdisjoint(neptunian_abbrevs), (
        f"abbreviation collision between Saturnians and Neptunians: "
        f"{saturnian_abbrevs & neptunian_abbrevs}"
    )


@pytest.mark.parametrize("body_key, _abbrev, _name, jd_to_fn, _to_jd_fn", NEPTUNIANS)
def test_neptunian_bridge_rejects_non_finite_jd(
        body_key, _abbrev, _name, jd_to_fn, _to_jd_fn):
    out = jd_to_fn(float("nan"))
    assert out["ok"] is False
    out = jd_to_fn(float("inf"))
    assert out["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# CLI surface — time-neptune-{moon}
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("body_key, abbrev, _name, _jd_fn, _inv_fn", NEPTUNIANS)
def test_neptunian_cli_jd_path(body_key, abbrev, _name, _jd_fn, _inv_fn):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main([f"time-neptune-{body_key}", "--jd", "2451545.0"])
    assert rc == 0
    payload = json.loads(buf.getvalue())
    assert payload["ok"] is True
    assert payload["body_name"] == body_key
    assert payload["parent_name"] == "neptune"
    assert payload["epoch"]["abbreviation"] == abbrev


@pytest.mark.parametrize("body_key, abbrev, _name, _jd_fn, _inv_fn", NEPTUNIANS)
def test_neptunian_cli_inverse_path(body_key, abbrev, _name, _jd_fn, _inv_fn):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main([f"time-neptune-{body_key}", "--sidereal-count", "100"])
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


@pytest.mark.parametrize("body_key, _abbrev, _name, _jd_fn, _inv_fn", NEPTUNIANS)
def test_neptunian_cli_requires_jd_or_sidereal_count(
        body_key, _abbrev, _name, _jd_fn, _inv_fn):
    """Mutex-required: must supply either --jd or --sidereal-count."""
    with pytest.raises(SystemExit):
        cli_main([f"time-neptune-{body_key}"])


# ──────────────────────────────────────────────────────────────────────
# Triton-specific witness: retrograde period is positive in BODIES
# ──────────────────────────────────────────────────────────────────────

def test_triton_period_is_positive_despite_retrograde_orbit() -> None:
    """Per the v0.5.4 Sol Uranian Time convention (also retrograde-
    rotation), Triton's `sidereal_period_days` in BODIES is POSITIVE
    (5.87685400) regardless of orbital direction. The encoder
    advances `omega = +2π/P` for all bodies, so the Sol Time count
    proceeds positive-monotonically. Retrograde-ness is documented
    in the bridge / CLI prose but does not enter the time-scale
    arithmetic — this test pins that contract.
    """
    period = float(BODIES["triton"].period_days)
    assert period > 0.0, (
        f"Triton period in BODIES must stay positive (encoder convention); "
        f"got {period}"
    )
    # Positive monotone count: at jd > j2000, sidereal_count > 0.
    out = bridge.jd_to_sol_neptune_triton_time(
        SOL_MOON_TIME_J2000_JD_TDB + 100.0
    )
    assert out["ok"] is True
    assert out["sidereal_count"] > 0.0, (
        "Sol Time count must be positive-monotone forward in JD even "
        "for retrograde moons (encoder uses +omega for all bodies)."
    )
