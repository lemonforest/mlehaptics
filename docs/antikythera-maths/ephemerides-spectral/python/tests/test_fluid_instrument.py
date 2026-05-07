"""v0.20.2 — Sol Fluid Instrument tests.

Pins:

* Three layers shipped together per §17.4.2 full-coverage commitment:
  21 climatology entries + 10 archive pointers + 21 coverage records.
* 17 atmospheric + 4 airless body partition.
* Headline numerics: terra 288.15 K / 101325 Pa; mars 210 K / 636 Pa;
  venus 737 K / 92 bar; titan 94 K / 1.45 bar (denser than Earth's
  despite the cold!); triton 38 K / 1.4 Pa (one of the coldest known
  surfaces); jupiter 165 K @ 1-bar reference.
* State-at-epoch coverage: ONLY terra (ERA5) + mars (MCD v6.1) have
  the True flag; all 19 other bodies fall back to climatology.
* Citation discipline: every source_key resolves; no unused SOURCES.
* Coverage-status triage: in_coverage / before_archive / future /
  no_state_at_epoch.
* Bridge surfaces (smoke + rejection paths).
* CLI surfaces (basic + --help).
"""

from __future__ import annotations

import math

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.fluid_instrument import (
    compute_fluid_architecture,
    compute_fluid_state,
    list_fluid_archives,
)
from ephemerides_spectral._research.fluid_instrument_data import (
    BODY_CLIMATOLOGY,
    BodyClimatology,
    FLUID_ARCHIVES,
    FLUID_STATE_COVERAGE,
    FluidArchive,
    FluidStateCoverage,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
)


# ──────────────────────────────────────────────────────────────────────
# Roster shape
# ──────────────────────────────────────────────────────────────────────

def test_climatology_count() -> None:
    """Per §17.4.2: at least 16 bodies. v0.20.2 ships 21 (full coverage
    of the published-atmospheric roster + 4 airless small bodies)."""
    assert len(BODY_CLIMATOLOGY) == 21


def test_archive_count() -> None:
    """10 archive pointers covering the bodies with refereed external
    archive holdings (ERA5, MCD, VIRA + Akatsuki, Cassini, Juno, MAVEN,
    Voyager 2 Uranus + Neptune, New Horizons)."""
    assert len(FLUID_ARCHIVES) == 10


def test_coverage_count_matches_climatology() -> None:
    """One coverage record per climatology body."""
    assert len(FLUID_STATE_COVERAGE) == len(BODY_CLIMATOLOGY)


def test_sources_count() -> None:
    """24 distinct citations covering every numeric value."""
    assert len(SOURCES) == 24


def test_atmospheric_vs_airless_split() -> None:
    """17 atmospheric + 4 airless small bodies (ceres, vesta, bennu, ryugu)."""
    atm = [m for m in BODY_CLIMATOLOGY if m.has_atmosphere]
    airless = [m for m in BODY_CLIMATOLOGY if not m.has_atmosphere]
    assert len(atm) == 17
    assert len(airless) == 4
    assert {m.body for m in airless} == {"ceres", "vesta", "bennu", "ryugu"}


def test_canonical_atmospheric_members() -> None:
    """Every body in the planned §17.4.2 atmospheric set must be present."""
    by = {m.body for m in BODY_CLIMATOLOGY if m.has_atmosphere}
    expected = {"terra", "mars", "venus", "titan", "triton", "pluto",
                "io", "europa", "ganymede", "enceladus",
                "mercury", "luna", "sun",
                "jupiter", "saturn", "uranus", "neptune"}
    assert by == expected


# ──────────────────────────────────────────────────────────────────────
# Headline numeric pins
# ──────────────────────────────────────────────────────────────────────

def test_terra_climatology_pinned() -> None:
    """NASA Earth fact sheet: T = 288.15 K, P = 101325 Pa."""
    by = {m.body: m for m in BODY_CLIMATOLOGY}
    terra = by["terra"]
    assert terra.mean_surface_temperature_K == pytest.approx(288.15, abs=0.5)
    assert terra.mean_surface_pressure_Pa == pytest.approx(101325.0, rel=0.01)
    assert terra.bond_albedo == pytest.approx(0.306, abs=0.05)


def test_mars_climatology_pinned() -> None:
    """NASA Mars fact sheet / MCD: T ~ 210 K, P ~ 636 Pa."""
    by = {m.body: m for m in BODY_CLIMATOLOGY}
    mars = by["mars"]
    assert mars.mean_surface_temperature_K == pytest.approx(210.0, abs=15)
    assert mars.mean_surface_pressure_Pa == pytest.approx(636.0, rel=0.5)


def test_venus_climatology_pinned() -> None:
    """Venus surface: 737 K, 92 bar (= 9.2e6 Pa)."""
    by = {m.body: m for m in BODY_CLIMATOLOGY}
    venus = by["venus"]
    assert venus.mean_surface_temperature_K == pytest.approx(737.0, abs=10)
    assert venus.mean_surface_pressure_Pa == pytest.approx(9.2e6, rel=0.05)


def test_titan_atmosphere_denser_than_earth() -> None:
    """Titan ships 94 K + 1.45 bar — denser than Earth's despite the
    cold (the famous result; only moon with a thick atmosphere)."""
    by = {m.body: m for m in BODY_CLIMATOLOGY}
    titan = by["titan"]
    assert titan.mean_surface_temperature_K == pytest.approx(94.0, abs=5)
    assert titan.mean_surface_pressure_Pa > 100_000.0  # > 1 bar


def test_triton_is_among_coldest() -> None:
    """Triton at 38 K is one of the coldest known surfaces."""
    by = {m.body: m for m in BODY_CLIMATOLOGY}
    triton = by["triton"]
    assert triton.mean_surface_temperature_K is not None
    assert triton.mean_surface_temperature_K < 50.0


def test_jupiter_1bar_reference() -> None:
    """Gas giants ship at the 1-bar reference level by convention."""
    by = {m.body: m for m in BODY_CLIMATOLOGY}
    jupiter = by["jupiter"]
    assert jupiter.mean_surface_temperature_K == pytest.approx(165.0, abs=15)
    assert jupiter.mean_surface_pressure_Pa == pytest.approx(1e5, rel=0.05)


def test_terra_obliquity_pinned() -> None:
    """Earth obliquity = 23.4393°."""
    by = {m.body: m for m in BODY_CLIMATOLOGY}
    assert by["terra"].obliquity_deg == pytest.approx(23.4393, abs=0.01)


def test_uranus_extreme_obliquity() -> None:
    """Uranus's 97.77° obliquity is the famous extreme axial tilt."""
    by = {m.body: m for m in BODY_CLIMATOLOGY}
    uranus = by["uranus"]
    assert uranus.obliquity_deg > 90.0


# ──────────────────────────────────────────────────────────────────────
# Source-citation discipline (ratchet)
# ──────────────────────────────────────────────────────────────────────

def test_every_climatology_source_key_resolves() -> None:
    for m in BODY_CLIMATOLOGY:
        assert m.source_key in SOURCES, (
            f"climatology {m.body} has unknown source_key {m.source_key!r}"
        )


def test_every_archive_source_key_resolves() -> None:
    for m in FLUID_ARCHIVES:
        assert m.source_key in SOURCES, (
            f"archive {m.body}/{m.archive_name} has unknown source_key "
            f"{m.source_key!r}"
        )


def test_every_coverage_source_key_resolves() -> None:
    """Coverage records optionally cite the underlying archive's source_key.
    If set, must resolve."""
    for m in FLUID_STATE_COVERAGE:
        if m.source_key:
            assert m.source_key in SOURCES, (
                f"coverage {m.body} has unknown source_key {m.source_key!r}"
            )


def test_no_unused_sources_entries() -> None:
    """Ratchet: every SOURCES entry is actually cited."""
    used = (
        {m.source_key for m in BODY_CLIMATOLOGY}
        | {m.source_key for m in FLUID_ARCHIVES}
        | {m.source_key for m in FLUID_STATE_COVERAGE if m.source_key}
    )
    unused = set(SOURCES.keys()) - used
    assert unused == set(), f"unused SOURCES entries: {unused}"


# ──────────────────────────────────────────────────────────────────────
# Precision-flag invariants
# ──────────────────────────────────────────────────────────────────────

def test_every_climatology_flag_is_valid_tier() -> None:
    valid = {PRECISION_HIGH, PRECISION_MEDIUM, PRECISION_LOW, PRECISION_NONE}
    for m in BODY_CLIMATOLOGY:
        assert m.precision_flag in valid


def test_every_archive_flag_is_valid_tier() -> None:
    valid = {PRECISION_HIGH, PRECISION_MEDIUM, PRECISION_LOW, PRECISION_NONE}
    for m in FLUID_ARCHIVES:
        assert m.precision_flag in valid


def test_terra_climatology_is_high_tier() -> None:
    by = {m.body: m for m in BODY_CLIMATOLOGY}
    assert by["terra"].precision_flag == PRECISION_HIGH


def test_mars_climatology_is_high_tier() -> None:
    by = {m.body: m for m in BODY_CLIMATOLOGY}
    assert by["mars"].precision_flag == PRECISION_HIGH


# ──────────────────────────────────────────────────────────────────────
# State-at-epoch coverage
# ──────────────────────────────────────────────────────────────────────

def test_only_terra_and_mars_have_state_at_epoch() -> None:
    """v0.20.2 ships state-at-epoch wrappers for ONLY terra (ERA5) and
    mars (MCD v6.1). All other bodies fall back to climatology."""
    by = {m.body: m for m in FLUID_STATE_COVERAGE}
    state_at_epoch = [m.body for m in FLUID_STATE_COVERAGE
                       if m.has_state_at_epoch]
    assert set(state_at_epoch) == {"terra", "mars"}


def test_terra_era5_coverage_starts_1940() -> None:
    """ERA5 reanalysis coverage begins 1940-01-01 (= JD ≈ 2429630.5)."""
    by = {m.body: m for m in FLUID_STATE_COVERAGE}
    terra = by["terra"]
    assert terra.has_state_at_epoch is True
    assert terra.coverage_start_jd is not None
    # 1940-01-01 = JD 2429630.5
    assert terra.coverage_start_jd == pytest.approx(2429630.5, abs=400)


def test_non_state_at_epoch_bodies_fall_back() -> None:
    """Bodies without state-at-epoch coverage carry the
    'out-of-coverage-fallback-to-climatology' query_type."""
    for m in FLUID_STATE_COVERAGE:
        if not m.has_state_at_epoch:
            assert "fallback" in m.query_type.lower() or \
                   "out-of-coverage" in m.query_type.lower(), (
                       f"{m.body} has unexpected query_type {m.query_type!r}"
                   )


# ──────────────────────────────────────────────────────────────────────
# Pythonic API — error paths + body-shape
# ──────────────────────────────────────────────────────────────────────

def test_compute_fluid_state_unknown_body() -> None:
    r = compute_fluid_state(body="krypton")
    assert r["ok"] is False


def test_compute_fluid_state_full_roster_shape() -> None:
    r = compute_fluid_state()
    assert r["ok"] is True
    # 21 climatology bodies + (possibly mars-upper-atmosphere as a
    # separate archive-only body string) = 21 or 22.
    assert r["n_bodies"] >= 21


def test_compute_fluid_state_terra_with_jd_in_coverage() -> None:
    """JD ≈ 2459580.5 (~2022) is well within ERA5 coverage."""
    r = compute_fluid_state(body="terra", jd_tdb=2459580.5)
    assert r["ok"] is True
    assert r["coverage_status"] == "in_coverage"
    assert r["climatology"] is not None


def test_compute_fluid_state_terra_with_jd_before_archive() -> None:
    """JD = 2400000.0 (~1858) predates ERA5 coverage."""
    r = compute_fluid_state(body="terra", jd_tdb=2400000.0)
    assert r["ok"] is True
    assert r["coverage_status"] == "before_archive"


def test_compute_fluid_state_venus_no_state_at_epoch() -> None:
    """Venus has no state-at-epoch wrapper; coverage_status flags it."""
    r = compute_fluid_state(body="venus", jd_tdb=2459580.5)
    assert r["ok"] is True
    assert r["coverage_status"] == "no_state_at_epoch"


def test_compute_fluid_state_invalid_jd() -> None:
    r = compute_fluid_state(body="terra", jd_tdb=float("inf"))
    assert r["ok"] is False


def test_compute_fluid_state_lat_lon_passthrough() -> None:
    """Lat/lon are passed through unchanged for the consumer."""
    r = compute_fluid_state(body="terra", lat=45.0, lon=120.0)
    assert r["ok"] is True
    assert r["lat"] == 45.0
    assert r["lon"] == 120.0


def test_compute_fluid_state_airless_body() -> None:
    """Bennu has has_atmosphere=False; climatology field still present
    (with atmosphere fields None) and archive list empty."""
    r = compute_fluid_state(body="bennu")
    assert r["ok"] is True
    assert r["climatology"] is not None
    assert r["climatology"]["has_atmosphere"] is False
    assert r["climatology"]["mean_surface_pressure_Pa"] is None


def test_compute_fluid_architecture_unknown_target() -> None:
    r = compute_fluid_architecture(target="krypton")
    assert r["ok"] is False


def test_compute_fluid_architecture_full_partition() -> None:
    r = compute_fluid_architecture()
    assert r["ok"] is True
    p = r["partitions"]
    assert PRECISION_HIGH in p
    assert PRECISION_MEDIUM in p
    assert PRECISION_LOW in p
    assert PRECISION_NONE in p


def test_compute_fluid_architecture_terra_high_tier() -> None:
    r = compute_fluid_architecture(target="terra")
    assert r["ok"] is True
    assert r["tier"] == PRECISION_HIGH
    assert r["has_state_at_epoch"] is True


def test_compute_fluid_architecture_mars_high_tier() -> None:
    r = compute_fluid_architecture(target="mars")
    assert r["ok"] is True
    assert r["tier"] == PRECISION_HIGH
    assert r["has_state_at_epoch"] is True


def test_compute_fluid_architecture_venus_no_state_at_epoch() -> None:
    r = compute_fluid_architecture(target="venus")
    assert r["ok"] is True
    # Venus has climatology but no state-at-epoch wrapper.
    assert r["has_state_at_epoch"] is False


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────

def test_bridge_get_fluid_state_full_roster() -> None:
    r = bridge.get_fluid_state()
    assert r["ok"] is True
    assert r["n_climatology_entries"] == 21
    assert r["n_archive_entries"] == 10


def test_bridge_get_fluid_state_per_body() -> None:
    r = bridge.get_fluid_state(body="titan")
    assert r["ok"] is True
    assert r["climatology"]["mean_surface_pressure_Pa"] > 100_000


def test_bridge_get_fluid_state_with_jd() -> None:
    r = bridge.get_fluid_state(body="mars", jd_tdb=2459580.5)
    assert r["ok"] is True
    assert r["coverage_status"] == "in_coverage"


def test_bridge_list_fluid_archives_smoke() -> None:
    r = bridge.list_fluid_archives()
    assert r["ok"] is True
    assert r["n_climatology"] == 21
    assert r["n_archives"] == 10
    assert r["n_coverage"] == 21
    assert r["n_sources"] == 24


def test_bridge_fluid_architecture_smoke() -> None:
    r = bridge.fluid_architecture()
    assert r["ok"] is True
    assert PRECISION_HIGH in r["partitions"]


def test_bridge_fluid_architecture_target_terra() -> None:
    r = bridge.fluid_architecture(target="terra")
    assert r["ok"] is True
    assert r["tier"] == PRECISION_HIGH


def test_bridge_get_fluid_state_rejects_unknown() -> None:
    r = bridge.get_fluid_state(body="krypton")
    assert r["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────

def test_cli_fluid_state_smoke() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["fluid-state", "--body", "terra"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["ok"] is True
    assert payload["climatology"]["mean_surface_temperature_K"] == pytest.approx(
        288.15, abs=0.5
    )


def test_cli_fluid_state_with_jd() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main([
            "fluid-state", "--body", "mars", "--jd-tdb", "2459580.5",
        ])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["coverage_status"] == "in_coverage"


def test_cli_fluid_archives_smoke() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["fluid-archives"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_archives"] == 10


def test_cli_fluid_architecture_smoke() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["fluid-architecture", "--target", "terra"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["tier"] == PRECISION_HIGH


def test_cli_fluid_help() -> None:
    """All three v0.20.2 CLI subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("fluid-state", "fluid-archives", "fluid-architecture"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
