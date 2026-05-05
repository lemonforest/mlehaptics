"""v0.13.0 — Sol Dynamics — focused tests.

Same validation pins as the Phase A audit script, with dynamics-
specific additions: total system energy < 0 (system is bound),
Earth-Sun force ≈ 3.54e22 N, Sun KE / Mc² < 1e-12.

Plus end-to-end CLI exercises for `dynamics` (system / body / pair
modes), the `--dynamics` flag composition, and bridge-error paths.
"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from typing import Any, Dict

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.bodies import BODIES
from ephemerides_spectral._research.dynamics import (
    G,
    BodyEnergies,
    DynamicsState,
    ForceContribution,
    get_body_energies,
    get_dynamics,
    get_force_between,
)


# ──────────────────────────────────────────────────────────────────────
# System-level validation pins
# ──────────────────────────────────────────────────────────────────────

def test_system_total_energy_is_negative_bound() -> None:
    """The Solar System is gravitationally bound — total E must be < 0."""
    d = get_dynamics()
    assert d.total_energy_j < 0, (
        f"Total system energy {d.total_energy_j:.3e} J — expected negative"
    )
    assert d.is_bound is True


def test_kinetic_plus_potential_equals_total() -> None:
    """Sanity: total = KE + PE."""
    d = get_dynamics()
    assert d.total_energy_j == pytest.approx(
        d.total_kinetic_energy_j + d.total_potential_energy_j, rel=1e-12
    )


def test_virial_theorem_for_circular_orbits() -> None:
    """For circular orbits, KE = -PE/2; total = -KE = PE/2."""
    d = get_dynamics()
    expected_total = d.total_potential_energy_j / 2
    rel_err = abs(d.total_energy_j - expected_total) / abs(expected_total)
    assert rel_err < 0.01, (
        f"Virial theorem violation: total {d.total_energy_j:.3e} vs. "
        f"expected PE/2 = {expected_total:.3e} (rel err {rel_err:.2%})"
    )


def test_jupiter_holds_61_percent_of_total_l() -> None:
    """Same headline fact as Kinematics, recomputed from Dynamics."""
    d = get_dynamics()
    assert 0.55 <= d.fraction_in_jupiter <= 0.65, (
        f"Jupiter fraction of L {d.fraction_in_jupiter:.4f}"
    )


def test_outer_planets_hold_99_percent_of_planetary_l() -> None:
    d = get_dynamics()
    assert d.fraction_in_outer_planets_of_planet_total > 0.99


def test_sun_ke_relative_negligible() -> None:
    """Sun barely moves in barycentric frame — KE / Mc² < 1e-12."""
    d = get_dynamics()
    assert d.sun_ke_relative_to_rest_mass < 1e-12, (
        f"Sun KE / Mc² = {d.sun_ke_relative_to_rest_mass:.2e}; "
        f"too large — check Sun-Jupiter wobble math"
    )


# ──────────────────────────────────────────────────────────────────────
# Per-body energies
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("body", ["mercury", "terra", "mars", "jupiter", "saturn"])
def test_per_body_total_energy_is_negative(body: str) -> None:
    """Each Sol-orbiting body in a stable orbit has total E < 0."""
    e = get_body_energies(body)
    assert e.note is None
    assert e.total_energy_j < 0, (
        f"{body} total E = {e.total_energy_j:.3e} J — expected negative"
    )


def test_virial_holds_per_body() -> None:
    """For each circular-orbit body: KE = -PE/2."""
    e = get_body_energies("terra")
    assert e.kinetic_energy_j == pytest.approx(
        -e.potential_energy_j / 2, rel=0.01
    )


# ──────────────────────────────────────────────────────────────────────
# Pair-wise forces
# ──────────────────────────────────────────────────────────────────────

def test_earth_sun_force_matches_textbook() -> None:
    """The textbook Earth-Sun gravitational force ≈ 3.54e22 N at 1 AU.

    This is the most-cited validation value for any Solar-System
    gravitational force.
    """
    f = get_force_between("terra", "sun")
    assert f.note is None
    expected_n = 3.54e22
    rel_err = abs(f.force_magnitude_n - expected_n) / expected_n
    assert rel_err < 0.01, (
        f"Earth-Sun force {f.force_magnitude_n:.3e} N vs. expected "
        f"{expected_n:.3e} (rel err {rel_err:.2%})"
    )


def test_force_is_symmetric() -> None:
    """F_ab == F_ba (Newton's 3rd law). Both magnitudes equal."""
    f_ab = get_force_between("terra", "mars")
    f_ba = get_force_between("mars", "terra")
    assert f_ab.force_magnitude_n == pytest.approx(f_ba.force_magnitude_n, rel=1e-12)


def test_self_force_is_zero() -> None:
    """A body exerts no force on itself."""
    f = get_force_between("mars", "mars")
    assert f.force_magnitude_n == 0.0


def test_force_falls_off_with_distance() -> None:
    """F should decrease as 1/r² between Mercury-Sun and Pluto-Sun."""
    f_merc = get_force_between("mercury", "sun")
    f_pluto = get_force_between("pluto", "sun")
    assert f_merc.force_magnitude_n > f_pluto.force_magnitude_n


def test_force_inverse_square_law() -> None:
    """F = G*M*m/r². Validate explicitly for Earth-Sun at known distance."""
    f = get_force_between("terra", "sun")
    # Reconstruct: F = G * M_sun * m_terra / d²
    M_sun = 1.98892e30
    m_terra = 5.972e24  # close to BODIES["terra"].mass_earth * EARTH_MASS_KG
    expected = G * M_sun * m_terra / (f.distance_m ** 2)
    rel_err = abs(f.force_magnitude_n - expected) / expected
    assert rel_err < 0.001, (
        f"Inverse-square check: {f.force_magnitude_n:.3e} vs. {expected:.3e}"
    )


# ──────────────────────────────────────────────────────────────────────
# Primitive interface
# ──────────────────────────────────────────────────────────────────────

def test_unknown_body_raises() -> None:
    with pytest.raises(KeyError):
        get_body_energies("fictitious")


def test_unknown_body_in_force_raises() -> None:
    with pytest.raises(KeyError):
        get_force_between("fictitious", "mars")


# ──────────────────────────────────────────────────────────────────────
# Bridge surface
# ──────────────────────────────────────────────────────────────────────

def test_bridge_get_dynamics_smoke() -> None:
    r = bridge.get_dynamics()
    assert r["ok"] is True
    assert r["abbreviation"] == "Sol-D"
    assert r["is_bound"] is True
    assert r["total_energy_j"] < 0
    assert 0.55 <= r["fraction_in_jupiter"] <= 0.65


def test_bridge_get_force_between_smoke() -> None:
    r = bridge.get_force_between("terra", "sun")
    assert r["ok"] is True
    assert r["abbreviation"] == "Sol-D"
    assert r["force_magnitude_n"] == pytest.approx(3.54e22, rel=0.01)


def test_bridge_get_body_energies_smoke() -> None:
    r = bridge.get_body_energies("jupiter")
    assert r["ok"] is True
    assert r["abbreviation"] == "Sol-D"
    assert r["total_energy_j"] < 0
    assert r["potential_energy_j"] < 0


def test_bridge_unknown_body_returns_ok_false() -> None:
    r = bridge.get_body_energies("fictitious")
    assert r["ok"] is False
    assert "must be one of" in r["error"]


def test_bridge_apply_dynamics_correction_augments_result() -> None:
    """`apply_dynamics_correction` adds a `dynamics` block to time-* output."""
    mars_time = bridge.jd_to_mars_time(2451545.0)
    augmented = bridge.apply_dynamics_correction(mars_time, "time-mars")
    assert "msd" in augmented
    assert "dynamics" in augmented
    assert augmented["dynamics"]["applied"] is True
    assert augmented["dynamics"]["body"] == "mars"
    assert augmented["dynamics"]["total_energy_j"] < 0
    assert augmented["dynamics"]["is_bound"] is True


def test_bridge_apply_dynamics_no_op_for_unknown_subcommand() -> None:
    mars_time = bridge.jd_to_mars_time(2451545.0)
    augmented = bridge.apply_dynamics_correction(mars_time, "time-bogus")
    assert "dynamics" not in augmented


def test_bridge_apply_dynamics_no_op_on_error_response() -> None:
    err = {"ok": False, "error": "something"}
    out = bridge.apply_dynamics_correction(err, "time-mars")
    assert out is err


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


def test_cli_dynamics_system_aggregate() -> None:
    r = _run_cli_json("dynamics")
    assert r["_rc"] == 0
    assert r["ok"] is True
    assert r["is_bound"] is True
    assert "fraction_in_jupiter" in r


def test_cli_dynamics_per_body() -> None:
    r = _run_cli_json("dynamics", "--body", "mars")
    assert r["_rc"] == 0
    assert r["ok"] is True
    assert "total_energy_j" in r
    assert r["total_energy_j"] < 0


def test_cli_dynamics_pair_force() -> None:
    r = _run_cli_json("dynamics", "--body", "terra", "--from", "sun")
    assert r["_rc"] == 0
    assert r["ok"] is True
    assert "force_magnitude_n" in r
    assert r["force_magnitude_n"] == pytest.approx(3.54e22, rel=0.01)


def test_cli_dynamics_from_without_body_errors() -> None:
    r = _run_cli_json("dynamics", "--from", "sun")
    assert r["_rc"] == 1
    assert r["ok"] is False


def test_cli_dynamics_flag_on_time_mars() -> None:
    r = _run_cli_json("time-mars", "--jd", "2451545.0", "--dynamics")
    assert r["_rc"] == 0
    assert r["ok"] is True
    assert "dynamics" in r
    assert r["dynamics"]["body"] == "mars"
    assert r["dynamics"]["total_energy_j"] < 0


def test_cli_compose_dynamics_state_proper() -> None:
    """All three augmenting flags compose without conflict."""
    r = _run_cli_json("time-mars", "--jd", "2451545.0",
                      "--state", "--proper", "--dynamics")
    assert r["_rc"] == 0
    assert "kinematic_state" in r
    assert "proper_time" in r
    assert "dynamics" in r
    assert "msd_proper" in r
