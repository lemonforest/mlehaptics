"""v0.14.1 — Sol Moon Times: Saturnians (Mimas / Enceladus / Tethys / Dione /
Rhea / Titan / Hyperion / Iapetus / Phoebe + Janus / Epimetheus).

Mirrors test_galilean_sol_moon_times.py, scaled to 11 moons. Same invariants
(J2000-zero, after-one-period, inverse round-trip, NaN/Inf rejection, CLI
parsing, abbreviation uniqueness) plus Saturnian-specific resonance
witnesses (Mimas-Tethys 4:2, Enceladus-Dione 2:1, Titan-Hyperion 4:3) and
the Janus-Epimetheus co-orbital pair check.
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


SATURNIANS = [
    # (body_key, abbrev, sol_time_name, jd_to_fn, to_jd_fn)
    ("mimas",      "SSaMiT", "Sol Saturn-Mimas Time",
     bridge.jd_to_sol_saturn_mimas_time, bridge.sol_saturn_mimas_time_to_jd),
    ("enceladus",  "SSaEnT", "Sol Saturn-Enceladus Time",
     bridge.jd_to_sol_saturn_enceladus_time, bridge.sol_saturn_enceladus_time_to_jd),
    ("tethys",     "SSaTeT", "Sol Saturn-Tethys Time",
     bridge.jd_to_sol_saturn_tethys_time, bridge.sol_saturn_tethys_time_to_jd),
    ("dione",      "SSaDiT", "Sol Saturn-Dione Time",
     bridge.jd_to_sol_saturn_dione_time, bridge.sol_saturn_dione_time_to_jd),
    ("rhea",       "SSaRhT", "Sol Saturn-Rhea Time",
     bridge.jd_to_sol_saturn_rhea_time, bridge.sol_saturn_rhea_time_to_jd),
    ("titan",      "SSaTiT", "Sol Saturn-Titan Time",
     bridge.jd_to_sol_saturn_titan_time, bridge.sol_saturn_titan_time_to_jd),
    ("hyperion",   "SSaHyT", "Sol Saturn-Hyperion Time",
     bridge.jd_to_sol_saturn_hyperion_time, bridge.sol_saturn_hyperion_time_to_jd),
    ("iapetus",    "SSaIaT", "Sol Saturn-Iapetus Time",
     bridge.jd_to_sol_saturn_iapetus_time, bridge.sol_saturn_iapetus_time_to_jd),
    ("phoebe",     "SSaPhT", "Sol Saturn-Phoebe Time",
     bridge.jd_to_sol_saturn_phoebe_time, bridge.sol_saturn_phoebe_time_to_jd),
    ("janus",      "SSaJaT", "Sol Saturn-Janus Time",
     bridge.jd_to_sol_saturn_janus_time, bridge.sol_saturn_janus_time_to_jd),
    ("epimetheus", "SSaEpT", "Sol Saturn-Epimetheus Time",
     bridge.jd_to_sol_saturn_epimetheus_time, bridge.sol_saturn_epimetheus_time_to_jd),
]


# ──────────────────────────────────────────────────────────────────────
# Bridge surface — per-Saturnian wrappers
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("body_key, abbrev, sol_time_name, jd_to_fn, _to_jd_fn", SATURNIANS)
def test_saturnian_bridge_at_j2000_returns_zero_count(
        body_key, abbrev, sol_time_name, jd_to_fn, _to_jd_fn):
    out = jd_to_fn(SOL_MOON_TIME_J2000_JD_TDB)
    assert out["ok"] is True
    assert out["body_name"] == body_key
    assert out["parent_name"] == "saturn"
    assert out["sidereal_count"] == 0.0
    assert out["sidereal_phase"] == 0.0
    assert out["epoch"]["abbreviation"] == abbrev
    assert out["epoch"]["sol_time_name"] == sol_time_name


@pytest.mark.parametrize("body_key, _abbrev, _name, jd_to_fn, _to_jd_fn", SATURNIANS)
def test_saturnian_bridge_after_one_sidereal_period(
        body_key, _abbrev, _name, jd_to_fn, _to_jd_fn):
    period = float(BODIES[body_key].period_days)
    jd_one = SOL_MOON_TIME_J2000_JD_TDB + period
    out = jd_to_fn(jd_one)
    assert out["ok"] is True
    assert abs(out["sidereal_count"] - 1.0) < 1e-9
    assert abs(out["sidereal_phase"] - 0.0) < 1e-9 or abs(out["sidereal_phase"] - 1.0) < 1e-9


@pytest.mark.parametrize("body_key, abbrev, _name, jd_to_fn, to_jd_fn", SATURNIANS)
def test_saturnian_bridge_inverse_round_trip(
        body_key, abbrev, _name, jd_to_fn, to_jd_fn):
    jd0 = SOL_MOON_TIME_J2000_JD_TDB + 365.25 * 20.0  # +20 yr
    out = jd_to_fn(jd0)
    assert out["ok"] is True
    inv = to_jd_fn(out["sidereal_count"])
    assert inv["ok"] is True
    assert abs(inv["jd_tdb"] - jd0) < 1e-6
    assert inv["abbreviation"] == abbrev
    assert inv["body_name"] == body_key


def test_saturnian_abbreviations_are_unique() -> None:
    """All 11 Saturnian abbreviations must be distinct under the
    6-letter `S<Planet2><Moon2>T` convention. Tethys (SSaTeT) vs
    Titan (SSaTiT) — the collision that triggered the policy switch.
    Enceladus (SSaEnT) vs Epimetheus (SSaEpT) — the second collision.
    """
    abbrevs = {abbrev for _, abbrev, *_ in SATURNIANS}
    assert len(abbrevs) == 11, f"expected 11 unique abbrevs, got {abbrevs}"


def test_saturnian_abbreviations_dont_collide_with_galileans() -> None:
    """All 4 Galilean (SJu*) and 11 Saturnian (SSa*) abbreviations
    must be globally distinct."""
    galilean_abbrevs = {"SJuIoT", "SJuEuT", "SJuGaT", "SJuCaT"}
    saturnian_abbrevs = {abbrev for _, abbrev, *_ in SATURNIANS}
    assert galilean_abbrevs.isdisjoint(saturnian_abbrevs), (
        f"abbreviation collision between Galileans and Saturnians: "
        f"{galilean_abbrevs & saturnian_abbrevs}"
    )


@pytest.mark.parametrize("body_key, _abbrev, _name, jd_to_fn, _to_jd_fn", SATURNIANS)
def test_saturnian_bridge_rejects_non_finite_jd(
        body_key, _abbrev, _name, jd_to_fn, _to_jd_fn):
    out = jd_to_fn(float("nan"))
    assert out["ok"] is False
    out = jd_to_fn(float("inf"))
    assert out["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# CLI surface — time-saturn-{moon}
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("body_key, abbrev, _name, _jd_fn, _inv_fn", SATURNIANS)
def test_saturnian_cli_jd_path(body_key, abbrev, _name, _jd_fn, _inv_fn):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main([f"time-saturn-{body_key}", "--jd", "2451545.0"])
    assert rc == 0
    payload = json.loads(buf.getvalue())
    assert payload["ok"] is True
    assert payload["body_name"] == body_key
    assert payload["parent_name"] == "saturn"
    assert payload["epoch"]["abbreviation"] == abbrev


@pytest.mark.parametrize("body_key, abbrev, _name, _jd_fn, _inv_fn", SATURNIANS)
def test_saturnian_cli_inverse_path(body_key, abbrev, _name, _jd_fn, _inv_fn):
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main([f"time-saturn-{body_key}", "--sidereal-count", "100"])
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


@pytest.mark.parametrize("body_key, _abbrev, _name, _jd_fn, _inv_fn", SATURNIANS)
def test_saturnian_cli_requires_jd_or_sidereal_count(
        body_key, _abbrev, _name, _jd_fn, _inv_fn):
    with pytest.raises(SystemExit):
        cli_main([f"time-saturn-{body_key}"])


# ──────────────────────────────────────────────────────────────────────
# Saturnian resonance witnesses (Mimas-Tethys 4:2, Enceladus-Dione 2:1,
# Titan-Hyperion 4:3, Janus-Epimetheus co-orbital ≈1:1).
# ──────────────────────────────────────────────────────────────────────

def test_mimas_tethys_4_to_2_resonance() -> None:
    """Mimas-Tethys 4:2 resonance opens the Cassini Division.
    Mean-motion ratio n_Mimas / n_Tethys ≈ 2.0 (the 4:2 form is just 2:1).
    """
    n_mimas  = 1.0 / float(BODIES["mimas"].period_days)
    n_tethys = 1.0 / float(BODIES["tethys"].period_days)
    ratio = n_mimas / n_tethys
    assert abs(ratio - 2.0) < 0.01, (
        f"Mimas-Tethys mean-motion ratio {ratio:.4f} not near 2.0"
    )


def test_enceladus_dione_2_to_1_resonance() -> None:
    """Enceladus-Dione 2:1 mean-motion resonance powers Enceladus's
    tidal heating and cryovolcanism."""
    n_enceladus = 1.0 / float(BODIES["enceladus"].period_days)
    n_dione     = 1.0 / float(BODIES["dione"].period_days)
    ratio = n_enceladus / n_dione
    assert abs(ratio - 2.0) < 0.01, (
        f"Enceladus-Dione mean-motion ratio {ratio:.4f} not near 2.0"
    )


def test_titan_hyperion_4_to_3_resonance() -> None:
    """Titan-Hyperion 4:3 mean-motion resonance drives Hyperion's
    chaotic rotation. n_Titan / n_Hyperion ≈ 4/3 ≈ 1.333."""
    n_titan    = 1.0 / float(BODIES["titan"].period_days)
    n_hyperion = 1.0 / float(BODIES["hyperion"].period_days)
    ratio = n_titan / n_hyperion
    expected = 4.0 / 3.0
    assert abs(ratio - expected) < 0.01, (
        f"Titan-Hyperion mean-motion ratio {ratio:.4f} not near {expected:.4f}"
    )


def test_janus_epimetheus_co_orbital_pair() -> None:
    """Janus and Epimetheus share the same orbit (horseshoe configuration).
    Their periods differ by ~30 seconds out of ~16.7 hours (the swap
    cycle is ~4 years). In the BODIES table both appear at the same
    semi-major axis to 4 decimals.
    """
    p_janus      = float(BODIES["janus"].period_days)
    p_epimetheus = float(BODIES["epimetheus"].period_days)
    # Period difference at the second-decimal-precision level (BODIES
    # carries 8 decimals; the swap is real but tiny).
    assert abs(p_janus - p_epimetheus) < 0.01, (
        f"Janus / Epimetheus periods differ too much: "
        f"{p_janus} vs {p_epimetheus}"
    )
    # And the period-ratio is essentially 1.0.
    assert abs(p_janus / p_epimetheus - 1.0) < 0.001
