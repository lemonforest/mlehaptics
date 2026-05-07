"""v0.20.1 — Sol Magnetic Multipole Catalog tests.

Pins:

* The 7-body main-field roster (terra / jupiter / saturn / mercury /
  uranus / neptune / ganymede) + 1 crustal model (Earth EMM2017) +
  1 solar synoptic reference (Stanford HMI).
* Headline numerics: IGRF-13 g10/g11/h11 + dipole tilt 9.41°; JRM33
  dipole moment ~1.5e20 T·m³ + tilt 10.31°; Cao 2020 Saturn dipole
  tilt < 0.007° (the famous result); Mercury offset dipole ~484 km
  northward; Uranus / Neptune tilted-offset structural flags.
* Citation discipline: every source_key resolves; no unused SOURCES
  entries (ratchet test).
* Precision-flag invariants — every flag is in the four-tier set.
* Dipole synthesis sanity checks: B_total at Earth surface ≈ IGRF
  textbook ~30000–60000 nT range; field decays as (R/r)^3 in the
  far field.
* Bridge surfaces (smoke + rejection paths).
* CLI surfaces (basic + --help).

Mirrors test_em_instrument.py and test_geodetic_catalog.py shape.
"""

from __future__ import annotations

import math

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.magnetic_multipole_catalog import (
    compute_magnetic_architecture,
    compute_magnetic_multipoles,
    compute_solar_synoptic_state,
    evaluate_magnetic_field,
    list_magnetic_multipoles,
)
from ephemerides_spectral._research.magnetic_multipole_catalog_data import (
    CRUSTAL_FIELD_MODELS,
    CrustalFieldModel,
    MAGNETIC_MULTIPOLE_MODELS,
    MagneticMultipoleModel,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOLAR_SYNOPTIC_REFERENCES,
    SOURCES,
    SolarSynopticReference,
)


# ──────────────────────────────────────────────────────────────────────
# Roster shape
# ──────────────────────────────────────────────────────────────────────

def test_main_field_roster_size_is_7() -> None:
    """Per §17.4.2: every body with a published refereed internal-field
    multipole model. v0.20.1 ships 7 — no body in the published roster
    is omitted."""
    assert len(MAGNETIC_MULTIPOLE_MODELS) == 7


def test_canonical_roster_members() -> None:
    """The 7 published-internal-field bodies per §17.4.2."""
    by = {m.body for m in MAGNETIC_MULTIPOLE_MODELS}
    expected = {"terra", "jupiter", "saturn", "mercury",
                "uranus", "neptune", "ganymede"}
    assert by == expected


def test_crustal_field_roster() -> None:
    """Earth EMM2017 only in v0.20.1 (Mars / Mercury crustal models
    are candidates for a future minor)."""
    assert len(CRUSTAL_FIELD_MODELS) == 1
    assert CRUSTAL_FIELD_MODELS[0].body == "terra"
    assert CRUSTAL_FIELD_MODELS[0].model_name == "EMM2017"
    assert CRUSTAL_FIELD_MODELS[0].max_degree == 720


def test_solar_synoptic_roster() -> None:
    """One synoptic-archive pointer (Stanford HMI / WSO)."""
    assert len(SOLAR_SYNOPTIC_REFERENCES) == 1
    assert SOLAR_SYNOPTIC_REFERENCES[0].body == "sun"


def test_sources_dict_size_at_least_7() -> None:
    """At least one citation per main-field model + crustal + synoptic."""
    assert len(SOURCES) >= 7


# ──────────────────────────────────────────────────────────────────────
# Headline numeric pins
# ──────────────────────────────────────────────────────────────────────

def test_terra_igrf13_pinned() -> None:
    """IGRF-13 (Alken 2021) — g10 ≈ -29404.8 nT; tilt ≈ 9.41°."""
    by = {m.body: m for m in MAGNETIC_MULTIPOLE_MODELS}
    terra = by["terra"]
    assert terra.model_name == "IGRF-13"
    assert terra.max_degree == 13
    assert terra.dipole_tilt_deg == pytest.approx(9.41, abs=0.5)
    # Schmidt-quasi-normalised g10 is negative for Earth (south magnetic
    # pole in the geographic NORTH hemisphere — the geomagnetic convention).
    assert terra.g10_nT is not None
    assert terra.g10_nT < 0


def test_jupiter_jrm33_pinned() -> None:
    """JRM33 (Connerney 2022) — dipole moment ~1.5e20 T·m³; tilt 10.31°."""
    by = {m.body: m for m in MAGNETIC_MULTIPOLE_MODELS}
    jupiter = by["jupiter"]
    assert jupiter.model_name == "JRM33"
    assert jupiter.max_degree == 18
    assert jupiter.dipole_tilt_deg == pytest.approx(10.31, abs=0.5)
    assert jupiter.dipole_moment_T_m3 is not None
    assert 1.0e20 <= jupiter.dipole_moment_T_m3 <= 2.0e20
    assert jupiter.structural_flag == "great_blue_spot_resolved"


def test_saturn_axisymmetric_pinned() -> None:
    """Cao 2020 — the famous dipole tilt < 0.007° axisymmetry result.
    The notebook §17.4.2 spec requires this to ship as a structural_flag."""
    by = {m.body: m for m in MAGNETIC_MULTIPOLE_MODELS}
    saturn = by["saturn"]
    assert saturn.model_name == "Cao-2020"
    assert saturn.max_degree == 14
    assert saturn.dipole_tilt_deg == pytest.approx(0.007, abs=0.005)
    assert saturn.structural_flag is not None
    assert "axisymmetric" in saturn.structural_flag


def test_mercury_offset_dipole_pinned() -> None:
    """Thébault 2018 — Mercury offset dipole ~484 km northward."""
    by = {m.body: m for m in MAGNETIC_MULTIPOLE_MODELS}
    mercury = by["mercury"]
    assert mercury.model_name == "Thebault-2018"
    assert mercury.max_degree == 5
    assert mercury.dipole_offset_km is not None
    assert 400 <= mercury.dipole_offset_km <= 600


def test_uranus_voyager_only_flag() -> None:
    """Holme & Bloxham AH5 — Voyager-only single flyby; precision LOW."""
    by = {m.body: m for m in MAGNETIC_MULTIPOLE_MODELS}
    uranus = by["uranus"]
    assert uranus.model_name == "AH5"
    assert uranus.precision_flag == PRECISION_LOW
    assert uranus.dipole_tilt_deg == pytest.approx(58.6, abs=2.0)


def test_neptune_voyager_only_flag() -> None:
    """Holme & Bloxham O8 — Voyager-only single flyby; precision LOW."""
    by = {m.body: m for m in MAGNETIC_MULTIPOLE_MODELS}
    neptune = by["neptune"]
    assert neptune.model_name == "O8"
    assert neptune.precision_flag == PRECISION_LOW
    assert neptune.dipole_tilt_deg == pytest.approx(47.0, abs=2.0)


def test_ganymede_only_intrinsic_moon_dipole() -> None:
    """Kivelson 2002 — only solar-system moon with confirmed intrinsic
    dipole. Per §17.4.2: dipole-only published, max_degree=1."""
    by = {m.body: m for m in MAGNETIC_MULTIPOLE_MODELS}
    ganymede = by["ganymede"]
    assert ganymede.model_name == "Kivelson-2002"
    assert ganymede.max_degree == 1
    assert ganymede.structural_flag is not None
    assert "intrinsic" in ganymede.structural_flag


# ──────────────────────────────────────────────────────────────────────
# Source-citation discipline (ratchet)
# ──────────────────────────────────────────────────────────────────────

def test_every_main_field_source_key_resolves() -> None:
    for m in MAGNETIC_MULTIPOLE_MODELS:
        assert m.source_key in SOURCES, (
            f"main-field {m.body} has unknown source_key {m.source_key!r}"
        )


def test_every_crustal_source_key_resolves() -> None:
    for m in CRUSTAL_FIELD_MODELS:
        assert m.source_key in SOURCES, (
            f"crustal {m.body} has unknown source_key {m.source_key!r}"
        )


def test_every_synoptic_source_key_resolves() -> None:
    for m in SOLAR_SYNOPTIC_REFERENCES:
        assert m.source_key in SOURCES, (
            f"synoptic {m.body} has unknown source_key {m.source_key!r}"
        )


def test_no_unused_sources_entries() -> None:
    """Ratchet: every SOURCES entry is actually cited."""
    used = (
        {m.source_key for m in MAGNETIC_MULTIPOLE_MODELS}
        | {m.source_key for m in CRUSTAL_FIELD_MODELS}
        | {m.source_key for m in SOLAR_SYNOPTIC_REFERENCES}
    )
    unused = set(SOURCES.keys()) - used
    assert unused == set(), f"unused SOURCES entries: {unused}"


# ──────────────────────────────────────────────────────────────────────
# Precision-flag invariants
# ──────────────────────────────────────────────────────────────────────

def test_every_main_field_flag_is_valid_tier() -> None:
    valid = {PRECISION_HIGH, PRECISION_MEDIUM, PRECISION_LOW, PRECISION_NONE}
    for m in MAGNETIC_MULTIPOLE_MODELS:
        assert m.precision_flag in valid


def test_high_tier_members() -> None:
    """Per §17.4.2 ship-readiness convention: current-best models
    (IGRF-13, JRM33, Cao 2020) are HIGH."""
    by = {m.body: m.precision_flag for m in MAGNETIC_MULTIPOLE_MODELS}
    assert by["terra"] == PRECISION_HIGH
    assert by["jupiter"] == PRECISION_HIGH
    assert by["saturn"] == PRECISION_HIGH


def test_low_tier_members() -> None:
    """Voyager-only single-flyby models are LOW."""
    by = {m.body: m.precision_flag for m in MAGNETIC_MULTIPOLE_MODELS}
    assert by["uranus"] == PRECISION_LOW
    assert by["neptune"] == PRECISION_LOW


# ──────────────────────────────────────────────────────────────────────
# Pythonic API — error paths + body-shape
# ──────────────────────────────────────────────────────────────────────

def test_compute_multipoles_unknown_body() -> None:
    r = compute_magnetic_multipoles(body="krypton")
    assert r["ok"] is False
    assert "unknown body" in r["error"].lower()


def test_compute_multipoles_full_roster_shape() -> None:
    r = compute_magnetic_multipoles()
    assert r["ok"] is True
    # Union: 7 multipole bodies + 1 sun-only synoptic body = 8.
    assert r["n_bodies"] == 8


def test_compute_multipoles_per_body_terra_with_crustal() -> None:
    r = compute_magnetic_multipoles(body="terra", crustal=True)
    assert r["ok"] is True
    assert r["main_field"]["model_name"] == "IGRF-13"
    assert r["crustal_field"]["model_name"] == "EMM2017"


def test_compute_multipoles_per_body_terra_without_crustal() -> None:
    """Default crustal=False omits the crustal record."""
    r = compute_magnetic_multipoles(body="terra")
    assert r["ok"] is True
    assert r["main_field"]["model_name"] == "IGRF-13"
    assert r["crustal_field"] is None


def test_compute_multipoles_sun_has_no_main_field() -> None:
    """Sun's field is time-varying; lives behind compute_solar_synoptic_state.
    The main-field record is None for the sun."""
    r = compute_magnetic_multipoles(body="sun")
    assert r["ok"] is True
    assert r["main_field"] is None


def test_evaluate_magnetic_field_smoke() -> None:
    r = evaluate_magnetic_field(
        body="terra", r_km=7000.0, lat_deg=0.0, lon_deg=0.0,
    )
    assert r["ok"] is True
    # Earth dipole field at equatorial r=7000 km should be in the
    # 15000-30000 nT range (surface ~30000 nT * (R/r)^3 ≈ 22500 nT).
    assert 10000 < r["B_total_nT"] < 35000
    assert r["below_surface"] is False


def test_evaluate_magnetic_field_decays_as_r_cubed() -> None:
    """B(2R) / B(R) ≈ 1/8 for a pure dipole; verify on Jupiter."""
    near = evaluate_magnetic_field(
        body="jupiter", r_km=71492.0, lat_deg=0.0, lon_deg=0.0,
    )
    far = evaluate_magnetic_field(
        body="jupiter", r_km=2 * 71492.0, lat_deg=0.0, lon_deg=0.0,
    )
    ratio = far["B_total_nT"] / near["B_total_nT"]
    assert ratio == pytest.approx(1.0 / 8.0, rel=1e-3)


def test_evaluate_magnetic_field_unknown_body() -> None:
    r = evaluate_magnetic_field(
        body="krypton", r_km=7000, lat_deg=0, lon_deg=0,
    )
    assert r["ok"] is False


def test_evaluate_magnetic_field_no_multipole_record() -> None:
    """Mars has no global intrinsic multipole — should be rejected."""
    r = evaluate_magnetic_field(
        body="mars", r_km=4000, lat_deg=0, lon_deg=0,
    )
    assert r["ok"] is False


def test_evaluate_magnetic_field_invalid_r() -> None:
    r = evaluate_magnetic_field(
        body="terra", r_km=-1.0, lat_deg=0, lon_deg=0,
    )
    assert r["ok"] is False


def test_evaluate_magnetic_field_non_finite() -> None:
    r = evaluate_magnetic_field(
        body="terra", r_km=float("nan"), lat_deg=0, lon_deg=0,
    )
    assert r["ok"] is False


def test_compute_solar_synoptic_no_jd() -> None:
    r = compute_solar_synoptic_state()
    assert r["ok"] is True
    assert r["body"] == "sun"
    assert r["n_archives"] >= 1


def test_compute_solar_synoptic_in_coverage() -> None:
    """JD ≈ 2455562.5 corresponds to ~2011-01-01, well inside Stanford
    HMI coverage (HMI launched 2010)."""
    r = compute_solar_synoptic_state(jd_tdb=2455562.5)
    assert r["ok"] is True
    assert r["coverage_status"] == "in_coverage"


def test_compute_solar_synoptic_before_archive() -> None:
    """JD = 2451545.0 (J2000) predates Stanford HMI coverage."""
    r = compute_solar_synoptic_state(jd_tdb=2451545.0)
    assert r["ok"] is True
    assert r["coverage_status"] == "before_archive"


def test_compute_solar_synoptic_non_finite() -> None:
    r = compute_solar_synoptic_state(jd_tdb=float("inf"))
    assert r["ok"] is False


def test_compute_magnetic_architecture_unknown_target() -> None:
    r = compute_magnetic_architecture(target="krypton")
    assert r["ok"] is False


def test_compute_magnetic_architecture_full_partition() -> None:
    r = compute_magnetic_architecture()
    assert r["ok"] is True
    p = r["partitions"]
    assert PRECISION_HIGH in p
    assert PRECISION_MEDIUM in p
    assert PRECISION_LOW in p
    assert PRECISION_NONE in p
    # The sun appears in the union of bodies (synoptic-only) but has no
    # multipole record → tier = NONE.
    assert "sun" in p[PRECISION_NONE]


@pytest.mark.parametrize("body,expected_tier", [
    ("terra", PRECISION_HIGH),
    ("jupiter", PRECISION_HIGH),
    ("saturn", PRECISION_HIGH),
    ("mercury", PRECISION_MEDIUM),
    ("ganymede", PRECISION_MEDIUM),
    ("uranus", PRECISION_LOW),
    ("neptune", PRECISION_LOW),
    ("sun", PRECISION_NONE),
])
def test_compute_magnetic_architecture_per_body_tier(
    body: str, expected_tier: str,
) -> None:
    r = compute_magnetic_architecture(target=body)
    assert r["ok"] is True
    assert r["tier"] == expected_tier


def test_terra_has_crustal_flag() -> None:
    r = compute_magnetic_architecture(target="terra")
    assert r["has_crustal"] is True


def test_jupiter_has_no_crustal_flag() -> None:
    r = compute_magnetic_architecture(target="jupiter")
    assert r["has_crustal"] is False


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────

def test_bridge_get_magnetic_multipoles_full_roster() -> None:
    r = bridge.get_magnetic_multipoles()
    assert r["ok"] is True
    assert r["n_multipole_models"] == 7


def test_bridge_get_magnetic_multipoles_per_body() -> None:
    r = bridge.get_magnetic_multipoles(body="jupiter")
    assert r["ok"] is True
    assert r["main_field"]["model_name"] == "JRM33"


def test_bridge_evaluate_magnetic_field_smoke() -> None:
    r = bridge.evaluate_magnetic_field(
        body="terra", r_km=7000.0, lat_deg=45.0, lon_deg=0.0,
    )
    assert r["ok"] is True
    assert r["synthesis_degree"] == 1


def test_bridge_get_solar_synoptic_state_smoke() -> None:
    r = bridge.get_solar_synoptic_state()
    assert r["ok"] is True
    assert r["body"] == "sun"


def test_bridge_list_magnetic_multipoles_smoke() -> None:
    r = bridge.list_magnetic_multipoles()
    assert r["ok"] is True
    assert r["n_multipole_models"] == 7
    assert r["n_crustal_models"] == 1
    assert r["n_solar_synoptic_references"] == 1


def test_bridge_magnetic_architecture_smoke() -> None:
    r = bridge.magnetic_architecture()
    assert r["ok"] is True
    assert PRECISION_HIGH in r["partitions"]


def test_bridge_magnetic_architecture_target_saturn() -> None:
    r = bridge.magnetic_architecture(target="saturn")
    assert r["ok"] is True
    assert r["tier"] == PRECISION_HIGH
    assert r["structural_flag"] is not None
    assert "axisymmetric" in r["structural_flag"]


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────

def test_cli_magnetic_multipoles_smoke() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["magnetic-multipoles", "--body", "jupiter"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["ok"] is True
    assert payload["main_field"]["model_name"] == "JRM33"


def test_cli_magnetic_field_smoke() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main([
            "magnetic-field",
            "--body", "terra",
            "--r-km", "7000",
            "--lat-deg", "0",
            "--lon-deg", "0",
        ])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["ok"] is True


def test_cli_solar_synoptic_smoke() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["solar-synoptic"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["ok"] is True


def test_cli_magnetic_models_smoke() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["magnetic-models"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_multipole_models"] == 7


def test_cli_magnetic_architecture_smoke() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["magnetic-architecture", "--target", "jupiter"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["tier"] == PRECISION_HIGH


def test_cli_magnetic_help() -> None:
    """All five v0.20.1 CLI subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("magnetic-multipoles", "magnetic-field",
                "solar-synoptic", "magnetic-models",
                "magnetic-architecture"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
