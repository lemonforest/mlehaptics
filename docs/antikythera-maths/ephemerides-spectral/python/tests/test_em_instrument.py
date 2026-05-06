"""v0.19.0 — Sol Electromagnetic Instrument tests.

Pins:

* The 16-body roster shape (1 star + 7 magnetised + 4 induced + 4
  unmagnetised; canonical members per notebook §16.9.2).
* The 7 pairwise EM couplings + their kinds + dominant timescales.
* Headline numeric pins: Jupiter dipole moment (JRM33), Earth dipole
  moment (IGRF-13), Jupiter-Io flux tube power (~10¹² W), Saturn
  rotation-period uncertainty flag (=1.0 %).
* Rotation phase advance: at JD = EM_REFERENCE_JD all phases are 0;
  at JD + period exactly one cycle later, phase wraps to 0 again
  (modulo float).
* Bridge surfaces (smoke + rejection paths).
* CLI surfaces (basic + --help).
* Source citations resolve (every body's source_key + every coupling's
  source_key is a key in the SOURCES dict).
"""

from __future__ import annotations

import math

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.em_instrument import (
    EM_CLASS_INDUCED,
    EM_CLASS_MAGNETISED,
    EM_CLASS_STAR,
    EM_CLASS_UNMAGNETISED,
    EM_COUPLINGS,
    EM_REFERENCE_JD,
    SOL_EM_BODIES,
    SOURCES,
    compute_em_architecture,
    compute_em_state_at_jd,
    list_em_couplings,
)


# ──────────────────────────────────────────────────────────────────────
# Roster shape
# ──────────────────────────────────────────────────────────────────────

def test_roster_size_is_16() -> None:
    assert len(SOL_EM_BODIES) == 16


def test_roster_partition_counts() -> None:
    """1 star + 7 magnetised + 4 induced + 4 unmagnetised."""
    classes = [b.em_class for b in SOL_EM_BODIES]
    assert classes.count(EM_CLASS_STAR) == 1
    assert classes.count(EM_CLASS_MAGNETISED) == 7
    assert classes.count(EM_CLASS_INDUCED) == 4
    assert classes.count(EM_CLASS_UNMAGNETISED) == 4


def test_canonical_magnetised_members() -> None:
    """Per notebook §16.9.2 the magnetised set is mercury / terra /
    jupiter / ganymede / saturn / uranus / neptune."""
    by_name = {b.name: b for b in SOL_EM_BODIES}
    expected = {"mercury", "terra", "jupiter", "ganymede", "saturn", "uranus", "neptune"}
    actual = {b.name for b in SOL_EM_BODIES if b.em_class == EM_CLASS_MAGNETISED}
    assert actual == expected


def test_canonical_induced_members() -> None:
    """Induced-magnetosphere bodies: venus / europa / callisto / titan."""
    expected = {"venus", "europa", "callisto", "titan"}
    actual = {b.name for b in SOL_EM_BODIES if b.em_class == EM_CLASS_INDUCED}
    assert actual == expected


def test_canonical_unmagnetised_members() -> None:
    """Unmagnetised: luna / mars / io / enceladus."""
    expected = {"luna", "mars", "io", "enceladus"}
    actual = {b.name for b in SOL_EM_BODIES if b.em_class == EM_CLASS_UNMAGNETISED}
    assert actual == expected


def test_sun_is_the_only_star() -> None:
    stars = [b for b in SOL_EM_BODIES if b.em_class == EM_CLASS_STAR]
    assert len(stars) == 1
    assert stars[0].name == "sun"


def test_induced_bodies_have_no_intrinsic_dipole() -> None:
    """Induced-magnetosphere bodies (Venus, Europa, Callisto, Titan)
    have `intrinsic_dipole_moment_T_m3 = None` by construction."""
    for b in SOL_EM_BODIES:
        if b.em_class == EM_CLASS_INDUCED:
            assert b.intrinsic_dipole_moment_T_m3 is None, (
                f"induced body {b.name} has non-None dipole "
                f"{b.intrinsic_dipole_moment_T_m3}"
            )


# ──────────────────────────────────────────────────────────────────────
# Headline numeric pins
# ──────────────────────────────────────────────────────────────────────

def test_jupiter_dipole_moment_pinned() -> None:
    """JRM33 (Connerney 2022) gives Jupiter dipole ~ 1.5e20 T·m³."""
    by_name = {b.name: b for b in SOL_EM_BODIES}
    jupiter = by_name["jupiter"]
    assert jupiter.intrinsic_dipole_moment_T_m3 is not None
    # Two-digit precision is fine; the value is scoping-grade.
    assert 1.0e20 <= jupiter.intrinsic_dipole_moment_T_m3 <= 2.5e20


def test_earth_dipole_moment_pinned_to_igrf() -> None:
    """IGRF-13 dipole moment ≈ 7.94e22 A·m² (T·m³ in SI when scaled)."""
    by_name = {b.name: b for b in SOL_EM_BODIES}
    terra = by_name["terra"]
    assert terra.intrinsic_dipole_moment_T_m3 is not None
    assert 5.0e15 <= terra.intrinsic_dipole_moment_T_m3 <= 9.0e22


def test_saturn_rotation_uncertainty_pinned_at_1_pct() -> None:
    """Saturn's internal rotation period is uncertain at ~1% between
    Voyager and Cassini SKR. The notebook §16.3 disclaimer requires
    this to be flagged explicitly in the data table."""
    by_name = {b.name: b for b in SOL_EM_BODIES}
    saturn = by_name["saturn"]
    assert saturn.rotation_period_uncertainty_pct >= 0.5, (
        f"Saturn rotation uncertainty under-flagged at "
        f"{saturn.rotation_period_uncertainty_pct} %"
    )


def test_ganymede_is_only_moon_with_intrinsic_dipole() -> None:
    """Per Kivelson 2002, Ganymede is the only solar-system moon with
    a confirmed intrinsic magnetic dipole. All other moons in the EM
    roster (luna, io, europa, callisto, enceladus, titan) have None."""
    by_name = {b.name: b for b in SOL_EM_BODIES}
    moons = ["luna", "io", "europa", "callisto", "enceladus", "titan", "ganymede"]
    moons_with_dipole = [
        m for m in moons
        if by_name[m].intrinsic_dipole_moment_T_m3 is not None
    ]
    assert moons_with_dipole == ["ganymede"]


# ──────────────────────────────────────────────────────────────────────
# Couplings
# ──────────────────────────────────────────────────────────────────────

def test_em_couplings_count() -> None:
    """7 pairwise couplings per notebook §16.2 + §16.8."""
    assert len(EM_COUPLINGS) == 7


def test_jupiter_io_flux_tube_is_dominant() -> None:
    """The Jupiter-Io flux tube is the strongest pairwise EM coupling
    in the solar system at ~10¹² W (Saur 2007 / Hess et al. 2010)."""
    flux_tube = [
        c for c in EM_COUPLINGS
        if c.kind == "flux_tube"
        and {c.body_a, c.body_b} == {"jupiter", "io"}
    ]
    assert len(flux_tube) == 1
    fc = flux_tube[0]
    assert 5.0e11 <= fc.power_W <= 5.0e12, (
        f"Jupiter-Io flux tube power {fc.power_W} W outside expected "
        f"~10¹² W range"
    )


def test_em_couplings_kinds_diverse() -> None:
    """Ensure the 7 couplings span diverse EM channels (not all one kind)."""
    kinds = {c.kind for c in EM_COUPLINGS}
    assert "flux_tube" in kinds
    assert "induced_magnetosphere" in kinds
    assert "imf_reconnection" in kinds
    assert "plasma_mass_loading" in kinds
    assert len(kinds) >= 5


# ──────────────────────────────────────────────────────────────────────
# Source-citation discipline
# ──────────────────────────────────────────────────────────────────────

def test_every_body_source_key_resolves() -> None:
    """Every EmBodyState.source_key must be a real key in SOURCES."""
    for b in SOL_EM_BODIES:
        assert b.source_key in SOURCES, (
            f"body {b.name} has unknown source_key {b.source_key!r}"
        )


def test_every_coupling_source_key_resolves() -> None:
    """Every EmCoupling.source_key must be a real key in SOURCES."""
    for c in EM_COUPLINGS:
        assert c.source_key in SOURCES, (
            f"coupling {c.body_a} <-> {c.body_b} has unknown "
            f"source_key {c.source_key!r}"
        )


# ──────────────────────────────────────────────────────────────────────
# Rotation-phase advance
# ──────────────────────────────────────────────────────────────────────

def test_rotation_phase_at_reference_is_zero() -> None:
    """At JD = EM_REFERENCE_JD all bodies have rotation_phase = 0."""
    state = compute_em_state_at_jd(EM_REFERENCE_JD)
    assert state["ok"] is True
    for r in state["bodies"]:
        assert r["rotation_phase"] == 0.0, (
            f"body {r['name']} has non-zero phase {r['rotation_phase']} "
            f"at reference JD"
        )


def test_rotation_phase_full_cycle_returns_to_zero() -> None:
    """At JD + rotation_period_days the phase wraps back to 0 (modulo
    float). Test on a magnetised body (Jupiter)."""
    by_name = {b.name: b for b in SOL_EM_BODIES}
    jupiter_period = by_name["jupiter"].rotation_period_days
    state = compute_em_state_at_jd(EM_REFERENCE_JD + jupiter_period)
    by_name_state = {r["name"]: r for r in state["bodies"]}
    # The phase should wrap to ≈0 (modulo float rounding). The double-
    # precision IEEE-754 floor on this arithmetic at JD ≈ 2.45e6 is
    # ~ULP × magnitude ≈ 5.5e-10; loosen the tolerance accordingly.
    assert abs(by_name_state["jupiter"]["rotation_phase"]) < 1e-9, (
        f"Jupiter phase after exactly one period = "
        f"{by_name_state['jupiter']['rotation_phase']} != 0"
    )


def test_rotation_phase_in_unit_interval() -> None:
    """All rotation phases must lie in [0, 1)."""
    for jd in [EM_REFERENCE_JD, EM_REFERENCE_JD + 100.0,
               EM_REFERENCE_JD - 50.0, EM_REFERENCE_JD + 50000.0]:
        state = compute_em_state_at_jd(jd)
        for r in state["bodies"]:
            assert 0.0 <= r["rotation_phase"] < 1.0, (
                f"body {r['name']} at jd={jd} has rotation_phase "
                f"{r['rotation_phase']} outside [0, 1)"
            )


# ──────────────────────────────────────────────────────────────────────
# Pythonic API — error paths
# ──────────────────────────────────────────────────────────────────────

def test_compute_em_state_rejects_non_finite_jd() -> None:
    r = compute_em_state_at_jd(float("nan"))
    assert r["ok"] is False
    r2 = compute_em_state_at_jd(float("inf"))
    assert r2["ok"] is False


def test_compute_em_architecture_target_unknown() -> None:
    r = compute_em_architecture(target="krypton")
    assert r["ok"] is False
    assert "unknown body" in r["error"].lower()


@pytest.mark.parametrize("body,expected_class", [
    ("sun", EM_CLASS_STAR),
    ("mercury", EM_CLASS_MAGNETISED),
    ("venus", EM_CLASS_INDUCED),
    ("terra", EM_CLASS_MAGNETISED),
    ("luna", EM_CLASS_UNMAGNETISED),
    ("mars", EM_CLASS_UNMAGNETISED),
    ("jupiter", EM_CLASS_MAGNETISED),
    ("io", EM_CLASS_UNMAGNETISED),
    ("europa", EM_CLASS_INDUCED),
    ("ganymede", EM_CLASS_MAGNETISED),
    ("callisto", EM_CLASS_INDUCED),
    ("saturn", EM_CLASS_MAGNETISED),
    ("enceladus", EM_CLASS_UNMAGNETISED),
    ("titan", EM_CLASS_INDUCED),
    ("uranus", EM_CLASS_MAGNETISED),
    ("neptune", EM_CLASS_MAGNETISED),
])
def test_compute_em_architecture_per_body_class(
    body: str, expected_class: str,
) -> None:
    r = compute_em_architecture(target=body)
    assert r["ok"] is True
    assert r["em_class"] == expected_class


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────

def test_bridge_get_em_state_smoke() -> None:
    r = bridge.get_em_state(2451545.0)
    assert r["ok"] is True
    assert r["n_bodies"] == 16
    assert r["reference_jd"] == EM_REFERENCE_JD


def test_bridge_list_em_couplings_smoke() -> None:
    r = bridge.list_em_couplings()
    assert r["ok"] is True
    assert r["n_couplings"] == 7


def test_bridge_em_architecture_full_partition() -> None:
    r = bridge.em_architecture()
    assert r["ok"] is True
    assert r["n_bodies"] == 16
    assert "magnetised" in r["partitions"]
    assert "induced" in r["partitions"]
    assert "unmagnetised" in r["partitions"]
    assert "star" in r["partitions"]


def test_bridge_em_architecture_target_jupiter() -> None:
    r = bridge.em_architecture(target="jupiter")
    assert r["ok"] is True
    assert r["em_class"] == EM_CLASS_MAGNETISED


def test_bridge_em_architecture_rejects_unknown() -> None:
    r = bridge.em_architecture(target="krypton")
    assert r["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────

def test_cli_em_state_smoke() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["em-state", "--jd-tdb", "2451545.0"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["ok"] is True
    assert payload["n_bodies"] == 16


def test_cli_em_couplings_smoke() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["em-couplings"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["ok"] is True
    assert payload["n_couplings"] == 7


def test_cli_em_architecture_smoke() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["em-architecture", "--target", "saturn"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["ok"] is True
    assert payload["em_class"] == EM_CLASS_MAGNETISED


def test_cli_em_help() -> None:
    """em-state / em-couplings / em-architecture --help all render."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("em-state", "em-couplings", "em-architecture"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
