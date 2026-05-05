"""v0.12.0 — Sol Kinematics — focused tests.

Same six per-body validation pins that the Phase A audit script
(`research/kinematics_dynamics_audit.py`) verifies independently,
plus the system-level fraction-in-Jupiter / fraction-in-outer-planets
checks. Two implementations agreeing on the same nine published values
— if either drifts, the other catches it.

Plus end-to-end CLI exercises for `kinematics --body`, `kinematics --all`,
and the `--state` flag on representative `time-*` subcommands.
"""

from __future__ import annotations

import io
import json
import math
from contextlib import redirect_stdout
from typing import Any, Dict

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.bodies import BODIES
from ephemerides_spectral._research.kinematics import (
    AU_M,
    DEFAULT_FRAME,
    SUN_MASS_KG,
    SUPPORTED_FRAMES,
    KinematicState,
    get_full_system_state,
    get_kinematic_state,
)


# ──────────────────────────────────────────────────────────────────────
# Per-body validation pins (mirror Phase A audit)
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("body,expected_kms,rel_tol", [
    ("mercury", 47.36, 0.02),
    ("terra",   29.78, 0.02),
    ("mars",    24.07, 0.02),
    ("jupiter", 13.07, 0.02),
    ("pluto",    4.74, 0.05),
])
def test_orbital_velocity_matches_published(
    body: str, expected_kms: float, rel_tol: float,
) -> None:
    """Per-body orbital velocity within published-value tolerance."""
    state = get_kinematic_state(body)
    assert state.note is None, (
        f"{body} kinematic state returned note: {state.note}"
    )
    rel_err = abs(state.orbital_velocity_km_s - expected_kms) / expected_kms
    assert rel_err <= rel_tol, (
        f"{body} orbital velocity: computed {state.orbital_velocity_km_s:.3f} km/s "
        f"vs. expected {expected_kms} (rel err {rel_err:.2%} > {rel_tol:.0%})"
    )


def test_jupiter_holds_60_percent_of_total_angular_momentum() -> None:
    """The famous fact: Jupiter alone carries ~61% of total system L."""
    states = get_full_system_state()
    total_lz = sum(
        s.angular_momentum_z_kg_m2_s
        for s in states.values() if s.note is None
    )
    jupiter_lz = states["jupiter"].angular_momentum_z_kg_m2_s
    fraction = jupiter_lz / total_lz
    assert 0.55 <= fraction <= 0.65, (
        f"Jupiter holds {fraction*100:.2f}% of total L — expected ~61%"
    )


def test_outer_planets_hold_99_percent_of_planetary_angular_momentum() -> None:
    """Outer planets (Jupiter+Saturn+Uranus+Neptune) hold >99% of planet L."""
    states = get_full_system_state()
    planet_lz = sum(
        s.angular_momentum_z_kg_m2_s
        for body_key, s in states.items()
        if s.note is None and BODIES[body_key].category == "planet"
    )
    outer_lz = sum(
        states[k].angular_momentum_z_kg_m2_s
        for k in ("jupiter", "saturn", "uranus", "neptune")
    )
    fraction = outer_lz / planet_lz
    assert fraction > 0.99, (
        f"Outer planets hold {fraction*100:.2f}% of planetary L — "
        f"expected >99%"
    )


def test_total_kinetic_energy_dominated_by_outer_planets() -> None:
    """Total KE check — sanity, no precision pin (depends on mass scaling)."""
    states = get_full_system_state()
    total_ke = sum(
        s.kinetic_energy_j for s in states.values() if s.note is None
    )
    assert total_ke > 0  # trivially
    # Jupiter's KE alone is ~50% of system total
    jupiter_ke = states["jupiter"].kinetic_energy_j
    assert jupiter_ke / total_ke > 0.4, (
        f"Jupiter's KE fraction: {jupiter_ke/total_ke:.2%} — expected >40%"
    )


# ──────────────────────────────────────────────────────────────────────
# Primitive surface
# ──────────────────────────────────────────────────────────────────────

def test_default_frame_is_heliocentric_ecliptic() -> None:
    assert DEFAULT_FRAME == "heliocentric_ecliptic"
    assert "heliocentric_ecliptic" in SUPPORTED_FRAMES
    assert "parent_centric" in SUPPORTED_FRAMES


def test_unknown_body_raises() -> None:
    with pytest.raises(KeyError, match="unknown body"):
        get_kinematic_state("fictitious")


def test_unknown_frame_raises() -> None:
    with pytest.raises(ValueError, match="frame must be"):
        get_kinematic_state("mars", frame="galactocentric")


def test_jd_tdb_arg_accepted_for_forward_compat() -> None:
    """v0.12.0 ignores --jd-tdb but accepts it cleanly."""
    s = get_kinematic_state("mars", jd_tdb=2451545.0)
    assert s.body == "mars"
    # The result should be identical to no-JD call (mean elements)
    s2 = get_kinematic_state("mars", jd_tdb=None)
    assert s.orbital_velocity_m_s == s2.orbital_velocity_m_s


def test_sun_returns_note_no_error() -> None:
    """Sun has period=0 → no Kepler computation; should set `note`."""
    s = get_kinematic_state("sun")
    assert s.body == "sun"
    assert s.note is not None
    assert "period_days = 0" in s.note
    assert s.orbital_velocity_m_s == 0.0
    assert s.kinetic_energy_j == 0.0
    # Sun's mass should still be set correctly
    assert abs(s.mass_kg - SUN_MASS_KG) / SUN_MASS_KG < 1e-12


def test_every_body_has_state_or_note() -> None:
    """Sanity: every body either has a clean state or an explanatory note."""
    states = get_full_system_state()
    for body_key, s in states.items():
        assert s.body == body_key
        if s.note is not None:
            # Sun is the only expected note-carrier
            assert body_key == "sun", (
                f"{body_key} returned unexpected note: {s.note}"
            )
        else:
            assert s.orbital_velocity_m_s > 0
            assert s.semi_major_axis_m > 0


def test_semi_major_axis_au_consistent_with_metres() -> None:
    """The convenience field semi_major_axis_au equals semi_major_axis_m / AU_M."""
    s = get_kinematic_state("terra")
    assert s.semi_major_axis_au == pytest.approx(s.semi_major_axis_m / AU_M)


def test_kinetic_energy_consistent_with_velocity_and_mass() -> None:
    """KE = 0.5 m v². No floating-point slop."""
    s = get_kinematic_state("mars")
    expected_ke = 0.5 * s.mass_kg * s.orbital_velocity_m_s ** 2
    assert s.kinetic_energy_j == pytest.approx(expected_ke, rel=1e-12)


def test_angular_momentum_consistent_with_mvr() -> None:
    """|L| = m·v·r for the circular orbit."""
    s = get_kinematic_state("jupiter")
    expected_L = s.mass_kg * s.orbital_velocity_m_s * s.semi_major_axis_m
    assert s.angular_momentum_kg_m2_s == pytest.approx(expected_L, rel=1e-12)


# ──────────────────────────────────────────────────────────────────────
# Bridge surface
# ──────────────────────────────────────────────────────────────────────

def test_bridge_get_kinematic_state_smoke() -> None:
    r = bridge.get_kinematic_state("mars")
    assert r["ok"] is True
    assert r["body"] == "mars"
    assert r["abbreviation"] == "Sol-K"
    assert r["frame"] == "heliocentric_ecliptic"
    assert "orbital_velocity_km_s" in r
    assert "semi_major_axis_au" in r


def test_bridge_unknown_body_returns_ok_false() -> None:
    r = bridge.get_kinematic_state("fictitious")
    assert r["ok"] is False
    assert "must be one of" in r["error"]


def test_bridge_get_full_system_state_smoke() -> None:
    r = bridge.get_full_system_state()
    assert r["ok"] is True
    assert r["abbreviation"] == "Sol-K"
    assert r["n_bodies"] == 38
    assert r["n_with_state"] == 37  # all except Sun
    assert "totals" in r
    assert "fraction_in_jupiter" in r["totals"]
    # The headline fact baked into the bridge totals
    assert 0.55 <= r["totals"]["fraction_in_jupiter"] <= 0.65


def test_bridge_apply_state_correction_augments_result() -> None:
    """`apply_state_correction` adds a `kinematic_state` block to time-* output."""
    mars_time = bridge.jd_to_mars_time(2451545.0)
    augmented = bridge.apply_state_correction(mars_time, "time-mars")
    assert "msd" in augmented
    assert "kinematic_state" in augmented
    assert augmented["kinematic_state"]["applied"] is True
    assert augmented["kinematic_state"]["body"] == "mars"
    assert augmented["kinematic_state"]["orbital_velocity_km_s"] == pytest.approx(
        24.129, rel=0.01
    )


def test_bridge_apply_state_no_op_for_unknown_subcommand() -> None:
    mars_time = bridge.jd_to_mars_time(2451545.0)
    augmented = bridge.apply_state_correction(mars_time, "time-bogus")
    assert "kinematic_state" not in augmented


def test_bridge_apply_state_no_op_on_error_response() -> None:
    err = {"ok": False, "error": "something"}
    out = bridge.apply_state_correction(err, "time-mars")
    assert out is err  # unchanged


# ──────────────────────────────────────────────────────────────────────
# CLI surface
# ──────────────────────────────────────────────────────────────────────

def _run_cli_json(*argv: str) -> Dict[str, Any]:
    from ephemerides_spectral.cli import main
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = main(list(argv))
    text = buf.getvalue()
    brace = text.find("{")
    assert brace >= 0, f"no JSON in stdout: {text!r}"
    parsed = json.loads(text[brace:])
    return {"_rc": rc, **parsed}


def test_cli_kinematics_body() -> None:
    r = _run_cli_json("kinematics", "--body", "mars")
    assert r["_rc"] == 0
    assert r["ok"] is True
    assert r["body"] == "mars"
    assert r["orbital_velocity_km_s"] == pytest.approx(24.129, rel=0.01)


def test_cli_kinematics_all() -> None:
    r = _run_cli_json("kinematics", "--all")
    assert r["_rc"] == 0
    assert r["ok"] is True
    assert r["n_bodies"] == 38
    assert "totals" in r
    assert 0.55 <= r["totals"]["fraction_in_jupiter"] <= 0.65


def test_cli_state_flag_on_time_mars() -> None:
    r = _run_cli_json("time-mars", "--jd", "2451545.0", "--state")
    assert r["_rc"] == 0
    assert r["ok"] is True
    assert "msd" in r
    assert "kinematic_state" in r
    assert r["kinematic_state"]["body"] == "mars"


def test_cli_state_flag_on_time_terra_luna() -> None:
    """STLT body is Terra (per the SPRT_COMMAND_MAP convention)."""
    r = _run_cli_json("time-terra-luna", "--jd", "2451545.0", "--state")
    assert r["_rc"] == 0
    assert r["ok"] is True
    assert "synodic_count" in r
    assert "kinematic_state" in r
    assert r["kinematic_state"]["body"] == "terra"


def test_cli_no_state_flag_means_no_correction() -> None:
    """Default (no --state) → output unchanged from previous releases."""
    r = _run_cli_json("time-mars", "--jd", "2451545.0")
    assert r["_rc"] == 0
    assert "msd" in r
    assert "kinematic_state" not in r


def test_cli_state_and_proper_compose() -> None:
    """--state and --proper apply independently and both blocks appear."""
    r = _run_cli_json("time-mars", "--jd", "2451545.0", "--state", "--proper")
    assert r["_rc"] == 0
    assert "kinematic_state" in r
    assert "proper_time" in r
    assert "msd_proper" in r
