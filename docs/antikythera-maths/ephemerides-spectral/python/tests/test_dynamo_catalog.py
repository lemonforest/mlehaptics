"""v0.21.2 — Sol Dynamo Region Catalog tests.

Pins the second cross-channel coupling surface in the §17.4.2 v0.21.x
sequence:

* 5-body roster (terra, mercury, jupiter, saturn, ganymede).
* Headline numerics: Earth CMB at 3486 km / 0.547 R_E (Lowes 1974,
  matches seismology to <1%); Jupiter dynamo at 0.85 R_J in metallic H
  (Connerney 2022); Saturn 0.55 R_S in metallic H (Cao 2020); Ganymede
  small Fe-FeS core at 0.27 R_G (Schubert 1996).
* Citation discipline: every source_key resolves; no unused SOURCES.
* Bridge surfaces (smoke + rejection paths).
* CLI surfaces (basic + --help).
"""

from __future__ import annotations

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.dynamo_catalog import (
    compute_dynamo_region,
    list_dynamo_regions,
)
from ephemerides_spectral._research.dynamo_catalog_data import (
    DYNAMO_REGIONS,
    DynamoRegion,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
)


# ──────────────────────────────────────────────────────────────────────
# Roster shape
# ──────────────────────────────────────────────────────────────────────

def test_roster_size_is_5() -> None:
    assert len(DYNAMO_REGIONS) == 5


def test_canonical_roster_members() -> None:
    by = {m.body for m in DYNAMO_REGIONS}
    assert by == {"terra", "mercury", "jupiter", "saturn", "ganymede"}


def test_sources_count() -> None:
    assert len(SOURCES) == 5


# ──────────────────────────────────────────────────────────────────────
# Headline numerics
# ──────────────────────────────────────────────────────────────────────

def test_earth_cmb_depth_pinned() -> None:
    """Lowes 1974 / Bloxham & Jackson 1992: R_dynamo / R_E ≈ 0.547,
    matching seismology CMB depth ~2891 km to better than 1%."""
    by = {m.body: m for m in DYNAMO_REGIONS}
    terra = by["terra"]
    assert terra.dynamo_radius_fraction == pytest.approx(0.547, abs=0.01)
    assert terra.dynamo_radius_km == pytest.approx(3486.0, abs=20)
    assert "Fe-Ni" in terra.conducting_material


def test_jupiter_metallic_h_dynamo_pinned() -> None:
    """Connerney 2022 from JRM33: dynamo at ~0.85 R_J in metallic H."""
    by = {m.body: m for m in DYNAMO_REGIONS}
    jupiter = by["jupiter"]
    assert jupiter.dynamo_radius_fraction == pytest.approx(0.85, abs=0.05)
    assert "metallic H" in jupiter.conducting_material


def test_saturn_metallic_h_dynamo_pinned() -> None:
    """Cao 2020 / Stevenson 2010: dynamo at ~0.55 R_S in metallic H."""
    by = {m.body: m for m in DYNAMO_REGIONS}
    saturn = by["saturn"]
    assert saturn.dynamo_radius_fraction == pytest.approx(0.55, abs=0.10)
    assert "metallic H" in saturn.conducting_material


def test_ganymede_small_iron_core_pinned() -> None:
    """Schubert 1996: small Fe-FeS core at ~0.27 R_G."""
    by = {m.body: m for m in DYNAMO_REGIONS}
    ganymede = by["ganymede"]
    assert ganymede.dynamo_radius_fraction == pytest.approx(0.27, abs=0.05)
    assert "Fe" in ganymede.conducting_material


def test_mercury_stable_strat_flagged() -> None:
    """Mercury's notes should call out the weak-field / stable-
    stratification anomaly per Christensen 2006."""
    by = {m.body: m for m in DYNAMO_REGIONS}
    mercury = by["mercury"]
    assert mercury.notes is not None
    assert ("weak-field" in mercury.notes.lower()
            or "stable" in mercury.notes.lower())


def test_dynamo_radius_km_consistent_with_fraction() -> None:
    """For every record: dynamo_radius_km ≈ fraction × surface_radius_km."""
    for m in DYNAMO_REGIONS:
        expected = m.dynamo_radius_fraction * m.surface_radius_km
        assert m.dynamo_radius_km == pytest.approx(expected, rel=0.01)


def test_conducting_materials_diverse() -> None:
    """Roster spans terrestrial Fe-Ni cores + metallic H + Fe-FeS."""
    materials = {m.conducting_material for m in DYNAMO_REGIONS}
    has_iron = any("Fe" in mat for mat in materials)
    has_metallic_h = any("metallic H" in mat for mat in materials)
    assert has_iron
    assert has_metallic_h


# ──────────────────────────────────────────────────────────────────────
# Citation discipline
# ──────────────────────────────────────────────────────────────────────

def test_every_source_key_resolves() -> None:
    for m in DYNAMO_REGIONS:
        assert m.source_key in SOURCES


def test_no_unused_sources_entries() -> None:
    used = {m.source_key for m in DYNAMO_REGIONS}
    unused = set(SOURCES.keys()) - used
    assert unused == set()


# ──────────────────────────────────────────────────────────────────────
# Precision-flag invariants
# ──────────────────────────────────────────────────────────────────────

def test_every_flag_is_valid_tier() -> None:
    valid = {PRECISION_HIGH, PRECISION_MEDIUM, PRECISION_LOW, PRECISION_NONE}
    for m in DYNAMO_REGIONS:
        assert m.precision_flag in valid


def test_terra_jupiter_saturn_high_tier() -> None:
    """Multi-mission high-degree datasets → HIGH."""
    by = {m.body: m for m in DYNAMO_REGIONS}
    assert by["terra"].precision_flag == PRECISION_HIGH
    assert by["jupiter"].precision_flag == PRECISION_HIGH
    assert by["saturn"].precision_flag == PRECISION_HIGH


def test_mercury_ganymede_medium_tier() -> None:
    """Single-mission or dipole-only → MEDIUM."""
    by = {m.body: m for m in DYNAMO_REGIONS}
    assert by["mercury"].precision_flag == PRECISION_MEDIUM
    assert by["ganymede"].precision_flag == PRECISION_MEDIUM


# ──────────────────────────────────────────────────────────────────────
# Pythonic API
# ──────────────────────────────────────────────────────────────────────

def test_compute_unknown_body() -> None:
    r = compute_dynamo_region(body="krypton")
    assert r["ok"] is False


def test_compute_full_roster() -> None:
    r = compute_dynamo_region()
    assert r["ok"] is True
    assert r["n_bodies"] == 5


def test_compute_per_body_terra() -> None:
    r = compute_dynamo_region(body="terra")
    assert r["ok"] is True
    assert r["region"]["dynamo_radius_km"] == pytest.approx(3486.0, abs=20)


def test_list_dynamo_regions_smoke() -> None:
    r = list_dynamo_regions()
    assert r["ok"] is True
    assert r["n_bodies"] == 5


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────

def test_bridge_get_dynamo_region_smoke() -> None:
    r = bridge.get_dynamo_region(body="jupiter")
    assert r["ok"] is True


def test_bridge_get_dynamo_region_full_roster() -> None:
    r = bridge.get_dynamo_region()
    assert r["ok"] is True
    assert r["n_bodies"] == 5


def test_bridge_list_dynamo_regions_smoke() -> None:
    r = bridge.list_dynamo_regions()
    assert r["ok"] is True


def test_bridge_get_dynamo_region_rejects_unknown() -> None:
    r = bridge.get_dynamo_region(body="krypton")
    assert r["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────

def test_cli_dynamo_region_smoke() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["dynamo-region", "--body", "jupiter"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["region"]["dynamo_radius_fraction"] == pytest.approx(0.85, abs=0.05)


def test_cli_dynamo_regions_smoke() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["dynamo-regions"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_bodies"] == 5


def test_cli_dynamo_help() -> None:
    """Both v0.21.2 CLI subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("dynamo-region", "dynamo-regions"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
