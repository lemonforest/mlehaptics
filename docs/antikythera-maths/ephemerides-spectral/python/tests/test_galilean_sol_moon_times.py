"""v0.14.0 — Sol Moon Times: Galileans (Io / Europa / Ganymede / Callisto).

Bridge surface + CLI primitives + generic moon-time primitive
(_research/time_scales.py::jd_to_moon_time / moon_time_to_jd).

Invariants enforced:

  1. Default epoch is J2000 (no historical-anchor menu like STLT;
     Galileans don't have a Greek-astronomy archive).
  2. Sidereal-cycle count round-trips exactly through the inverse.
  3. At J2000.0 exactly, sidereal_count == 0 for all four Galileans.
  4. After exactly one sidereal period, sidereal_count == 1 (within
     float-ULP tolerance for the period encoding).
  5. The four CLI subcommands (time-jupiter-io, ...-europa, ...-ganymede,
     ...-callisto) parse through to the bridge and emit valid JSON
     with the expected fields (`abbreviation`, `parent_body`, etc.).
  6. Each moon's `abbreviation` field is unique and matches the SJIT /
     SJET / SJGT / SJCT convention.
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


GALILEANS = [
    # (body_key, abbrev, sol_time_name, jd_to_fn, to_jd_fn)
    ("io",       "SJIT", "Sol Jupiter-Io Time",
     bridge.jd_to_sol_jupiter_io_time, bridge.sol_jupiter_io_time_to_jd),
    ("europa",   "SJET", "Sol Jupiter-Europa Time",
     bridge.jd_to_sol_jupiter_europa_time, bridge.sol_jupiter_europa_time_to_jd),
    ("ganymede", "SJGT", "Sol Jupiter-Ganymede Time",
     bridge.jd_to_sol_jupiter_ganymede_time, bridge.sol_jupiter_ganymede_time_to_jd),
    ("callisto", "SJCT", "Sol Jupiter-Callisto Time",
     bridge.jd_to_sol_jupiter_callisto_time, bridge.sol_jupiter_callisto_time_to_jd),
]


# ──────────────────────────────────────────────────────────────────────
# Generic primitive — _research/time_scales.py
# ──────────────────────────────────────────────────────────────────────

def test_jd_to_moon_time_returns_moontime_dataclass() -> None:
    out = jd_to_moon_time("io", 2451545.0,
                          parent_name="jupiter",
                          sidereal_period_days=1.76913786)
    assert isinstance(out, MoonTime)
    assert out.body_name == "io"
    assert out.parent_name == "jupiter"
    assert out.epoch_name == "j2000"
    assert out.epoch_jd_tdb == SOL_MOON_TIME_J2000_JD_TDB


def test_jd_to_moon_time_at_j2000_yields_zero_count() -> None:
    out = jd_to_moon_time("io", SOL_MOON_TIME_J2000_JD_TDB,
                          parent_name="jupiter",
                          sidereal_period_days=1.76913786)
    assert out.days_since_epoch == 0.0
    assert out.sidereal_count == 0.0
    assert out.sidereal_phase == 0.0


def test_moon_time_to_jd_inverts_jd_to_moon_time() -> None:
    # 100 sidereal cycles forward, then back through the inverse.
    period = 1.76913786  # Io
    jd0 = SOL_MOON_TIME_J2000_JD_TDB + 100.0 * period
    out = jd_to_moon_time("io", jd0,
                          parent_name="jupiter",
                          sidereal_period_days=period)
    # The arithmetic 100 * period truncated by float is ~6e-11 off;
    # tighter tolerance would test the float ALU not the math.
    assert abs(out.sidereal_count - 100.0) < 1e-9
    jd_back = moon_time_to_jd(out.sidereal_count, sidereal_period_days=period)
    assert abs(jd_back - jd0) < 1e-9


def test_jd_to_moon_time_rejects_zero_or_negative_period() -> None:
    with pytest.raises(ValueError):
        jd_to_moon_time("io", 2451545.0,
                        parent_name="jupiter",
                        sidereal_period_days=0.0)
    with pytest.raises(ValueError):
        jd_to_moon_time("io", 2451545.0,
                        parent_name="jupiter",
                        sidereal_period_days=-1.0)


# ──────────────────────────────────────────────────────────────────────
# Bridge surface — per-Galilean wrappers
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("body_key, abbrev, sol_time_name, jd_to_fn, _to_jd_fn", GALILEANS)
def test_galilean_bridge_at_j2000_returns_zero_count(
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


@pytest.mark.parametrize("body_key, abbrev, _name, jd_to_fn, _to_jd_fn", GALILEANS)
def test_galilean_bridge_after_one_sidereal_period(
        body_key: str, abbrev: str, _name: str,
        jd_to_fn, _to_jd_fn) -> None:
    period = float(BODIES[body_key].period_days)
    jd_one = SOL_MOON_TIME_J2000_JD_TDB + period
    out = jd_to_fn(jd_one)
    assert out["ok"] is True
    # Sidereal count should be 1.0 to within float-ULP.
    assert abs(out["sidereal_count"] - 1.0) < 1e-9
    # Phase wraps back to (effectively) zero.
    assert abs(out["sidereal_phase"] - 0.0) < 1e-9 or abs(out["sidereal_phase"] - 1.0) < 1e-9


@pytest.mark.parametrize("body_key, abbrev, _name, jd_to_fn, to_jd_fn", GALILEANS)
def test_galilean_bridge_inverse_round_trip(
        body_key: str, abbrev: str, _name: str,
        jd_to_fn, to_jd_fn) -> None:
    period = float(BODIES[body_key].period_days)
    jd0 = SOL_MOON_TIME_J2000_JD_TDB + 365.25 * 20.0  # +20 yr
    out = jd_to_fn(jd0)
    assert out["ok"] is True
    inv = to_jd_fn(out["sidereal_count"])
    assert inv["ok"] is True
    assert abs(inv["jd_tdb"] - jd0) < 1e-6
    assert inv["abbreviation"] == abbrev
    assert inv["body_name"] == body_key


def test_galilean_abbreviations_are_unique() -> None:
    """Sanity: SJIT, SJET, SJGT, SJCT must all be distinct."""
    abbrevs = {abbrev for _, abbrev, *_ in GALILEANS}
    assert len(abbrevs) == 4, f"expected 4 unique abbrevs, got {abbrevs}"


@pytest.mark.parametrize("body_key, _abbrev, _name, jd_to_fn, _to_jd_fn", GALILEANS)
def test_galilean_bridge_rejects_non_finite_jd(
        body_key: str, _abbrev: str, _name: str,
        jd_to_fn, _to_jd_fn) -> None:
    out = jd_to_fn(float("nan"))
    assert out["ok"] is False
    out = jd_to_fn(float("inf"))
    assert out["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# CLI surface — time-jupiter-{io, europa, ganymede, callisto}
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("body_key, abbrev, _name, _jd_fn, _inv_fn", GALILEANS)
def test_galilean_cli_jd_path(
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


@pytest.mark.parametrize("body_key, abbrev, _name, _jd_fn, _inv_fn", GALILEANS)
def test_galilean_cli_inverse_path(
        body_key: str, abbrev: str, _name: str,
        _jd_fn, _inv_fn) -> None:
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main([f"time-jupiter-{body_key}", "--sidereal-count", "100"])
    assert rc == 0
    payload = json.loads(buf.getvalue())
    assert payload["ok"] is True
    assert payload["sidereal_count"] == 100.0
    assert payload["abbreviation"] == abbrev
    # Inverse should land at j2000 + 100 * sidereal_period.
    expected_jd = (
        SOL_MOON_TIME_J2000_JD_TDB
        + 100.0 * float(BODIES[body_key].period_days)
    )
    assert abs(payload["jd_tdb"] - expected_jd) < 1e-6


@pytest.mark.parametrize("body_key, _abbrev, _name, _jd_fn, _inv_fn", GALILEANS)
def test_galilean_cli_requires_jd_or_sidereal_count(
        body_key: str, _abbrev: str, _name: str,
        _jd_fn, _inv_fn) -> None:
    """Mutex-required: must supply either --jd or --sidereal-count."""
    with pytest.raises(SystemExit):
        cli_main([f"time-jupiter-{body_key}"])


# ──────────────────────────────────────────────────────────────────────
# Laplace resonance witness (Io : Europa : Ganymede ≈ 4 : 2 : 1)
# ──────────────────────────────────────────────────────────────────────

def test_laplace_resonance_in_sidereal_periods() -> None:
    """The Galilean Laplace resonance is a property of Io / Europa /
    Ganymede mean motions: ``n_Io − 3·n_Europa + 2·n_Ganymede ≈ 0``.

    The pairwise mean-motion ratios are also each ~2:1 (Io:Europa and
    Europa:Ganymede), but that's a derived consequence of the canonical
    three-body form above.
    """
    t_io       = float(BODIES["io"].period_days)
    t_europa   = float(BODIES["europa"].period_days)
    t_ganymede = float(BODIES["ganymede"].period_days)
    # n = 1/T (mean motion proxy in cycles/day)
    n_io       = 1.0 / t_io
    n_europa   = 1.0 / t_europa
    n_ganymede = 1.0 / t_ganymede
    # The Laplace combination — exact at infinite precision, ~10⁻⁴
    # at our period-table precision (BODIES periods are good to ~1e-8
    # but cancel on subtraction; see _research/bodies.py for sources).
    laplace_residual = n_io - 3.0 * n_europa + 2.0 * n_ganymede
    assert abs(laplace_residual) < 1e-3, (
        f"Galilean Laplace residual {laplace_residual:.2e} exceeds "
        "tolerance — sidereal-period values in BODIES may have "
        "drifted; cross-check against JPL HORIZONS / NASA fact sheet."
    )
    # Sanity: pairwise 2:1 ratios should both hold to ~1%.
    assert abs(n_io / n_europa - 2.0) < 0.02
    assert abs(n_europa / n_ganymede - 2.0) < 0.02


def test_callisto_is_not_in_laplace_resonance() -> None:
    """Callisto is the only Galilean NOT in the Laplace resonance.
    Verify n_Callisto is irrationally related to the inner triple
    (no small-integer ratio at the Laplace tolerance).
    """
    t_io       = float(BODIES["io"].period_days)
    t_callisto = float(BODIES["callisto"].period_days)
    n_io       = 1.0 / t_io
    n_callisto = 1.0 / t_callisto
    # Closest small-integer match would be n_Io / n_Callisto ≈ 9.4...
    ratio = n_io / n_callisto
    # Distance to the nearest integer; should be substantial (NOT a
    # near-integer ratio like Io / Europa = 2.0001).
    nearest_int = round(ratio)
    assert abs(ratio - nearest_int) > 0.1, (
        f"Callisto's period ratio to Io is {ratio:.4f} — too close to "
        f"integer {nearest_int}, suggesting a resonance our test missed."
    )
