"""v0.21.1 — Sol Topography-Gravity Admittance Catalog tests.

Pins the first cross-channel coupling surface in the §17.4.2 v0.21.x
sequence:

* 5-body roster (terra, luna, mars, mercury, venus) — every body with
  a peer-reviewed topography-gravity admittance study.
* Headline numerics: Wieczorek 2013 lunar crustal density 2550 kg/m³;
  Wieczorek 2007 Earth continental Z ~50 mGal/km; Anderson 2002 Venus
  Z ~200 mGal/km (highest in catalog; weak Airy compensation).
* Citation discipline: every source_key resolves; no unused SOURCES.
* Bridge surfaces (smoke + rejection paths).
* CLI surfaces (basic + --help).
"""

from __future__ import annotations

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.admittance_catalog import (
    compute_topography_gravity_admittance,
    list_admittance_spectra,
)
from ephemerides_spectral._research.admittance_catalog_data import (
    ADMITTANCE_SPECTRA,
    AdmittanceSpectrum,
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
    """v0.21.1 ships 5 bodies — every published peer-reviewed
    admittance study in the §17.4.2 commitment scope."""
    assert len(ADMITTANCE_SPECTRA) == 5


def test_canonical_roster_members() -> None:
    by = {m.body for m in ADMITTANCE_SPECTRA}
    expected = {"terra", "luna", "mars", "mercury", "venus"}
    assert by == expected


def test_sources_count() -> None:
    """5 distinct citations (one per body, since each comes from a
    different paper)."""
    assert len(SOURCES) == 5


# ──────────────────────────────────────────────────────────────────────
# Headline numerics
# ──────────────────────────────────────────────────────────────────────

def test_wieczorek_2013_lunar_crustal_density() -> None:
    """The famous Wieczorek 2013 GRAIL+LOLA result: lunar crustal
    density 2550 kg/m³ (revised down from prior ~2900)."""
    by = {m.body: m for m in ADMITTANCE_SPECTRA}
    luna = by["luna"]
    assert luna.inferred_crustal_density_kg_per_m3 == pytest.approx(2550.0, abs=50)
    assert luna.precision_flag == PRECISION_HIGH


def test_wieczorek_2007_earth_continental_z() -> None:
    """Watts 2001 / Wieczorek 2007: continental-mean Z ~50 mGal/km."""
    by = {m.body: m for m in ADMITTANCE_SPECTRA}
    terra = by["terra"]
    assert terra.mean_admittance_mGal_per_km == pytest.approx(50.0, abs=15)


def test_venus_highest_admittance() -> None:
    """Venus has the highest mean Z in the catalog because it lacks
    Airy isostatic compensation under Magellan-resolved conditions."""
    by_z = {m.body: m.mean_admittance_mGal_per_km for m in ADMITTANCE_SPECTRA}
    venus_z = by_z["venus"]
    other_max = max(z for body, z in by_z.items() if body != "venus")
    assert venus_z > other_max
    assert venus_z >= 150.0  # Anderson 2002 reported range


def test_mars_dominated_by_tharsis() -> None:
    """Mars admittance is dominated by Tharsis at low degrees; the
    notes field should call this out per the original paper's caveat."""
    by = {m.body: m for m in ADMITTANCE_SPECTRA}
    mars = by["mars"]
    assert mars.notes is not None
    assert "tharsis" in mars.notes.lower()


def test_isostatic_models_diverse() -> None:
    """The 5-body catalog spans Airy + lithospheric_flexure models."""
    models = {m.isostatic_model for m in ADMITTANCE_SPECTRA}
    assert "Airy" in models
    assert "lithospheric_flexure" in models


def test_degree_ranges_are_valid() -> None:
    """Every spectrum has a sensible degree window."""
    for m in ADMITTANCE_SPECTRA:
        assert m.degree_min >= 2  # n=0,1 are gauge-fixed (mass + COM)
        assert m.degree_max > m.degree_min


# ──────────────────────────────────────────────────────────────────────
# Citation discipline (ratchet)
# ──────────────────────────────────────────────────────────────────────

def test_every_source_key_resolves() -> None:
    for m in ADMITTANCE_SPECTRA:
        assert m.source_key in SOURCES, (
            f"admittance {m.body} has unknown source_key {m.source_key!r}"
        )


def test_no_unused_sources_entries() -> None:
    used = {m.source_key for m in ADMITTANCE_SPECTRA}
    unused = set(SOURCES.keys()) - used
    assert unused == set(), f"unused SOURCES entries: {unused}"


# ──────────────────────────────────────────────────────────────────────
# Precision-flag invariants
# ──────────────────────────────────────────────────────────────────────

def test_every_flag_is_valid_tier() -> None:
    valid = {PRECISION_HIGH, PRECISION_MEDIUM, PRECISION_LOW, PRECISION_NONE}
    for m in ADMITTANCE_SPECTRA:
        assert m.precision_flag in valid


def test_terra_luna_mars_are_high_tier() -> None:
    """Modern multi-mission datasets (GRAIL, MRO/InSight) → HIGH tier."""
    by = {m.body: m for m in ADMITTANCE_SPECTRA}
    assert by["terra"].precision_flag == PRECISION_HIGH
    assert by["luna"].precision_flag == PRECISION_HIGH
    assert by["mars"].precision_flag == PRECISION_HIGH


def test_mercury_venus_are_medium_tier() -> None:
    """Single-mission datasets (MESSENGER, Magellan-only) → MEDIUM."""
    by = {m.body: m for m in ADMITTANCE_SPECTRA}
    assert by["mercury"].precision_flag == PRECISION_MEDIUM
    assert by["venus"].precision_flag == PRECISION_MEDIUM


# ──────────────────────────────────────────────────────────────────────
# Pythonic API
# ──────────────────────────────────────────────────────────────────────

def test_compute_unknown_body() -> None:
    r = compute_topography_gravity_admittance(body="krypton")
    assert r["ok"] is False
    assert "unknown body" in r["error"].lower()


def test_compute_full_roster() -> None:
    r = compute_topography_gravity_admittance()
    assert r["ok"] is True
    assert r["n_bodies"] == 5
    assert "luna" in r["bodies"]


def test_compute_per_body_luna() -> None:
    r = compute_topography_gravity_admittance(body="luna")
    assert r["ok"] is True
    assert r["spectrum"]["inferred_crustal_density_kg_per_m3"] == pytest.approx(2550.0, abs=50)


def test_list_admittance_spectra_smoke() -> None:
    r = list_admittance_spectra()
    assert r["ok"] is True
    assert r["n_bodies"] == 5
    assert r["n_sources"] == 5


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────

def test_bridge_get_admittance_smoke() -> None:
    r = bridge.get_topography_gravity_admittance(body="terra")
    assert r["ok"] is True


def test_bridge_get_admittance_full_roster() -> None:
    r = bridge.get_topography_gravity_admittance()
    assert r["ok"] is True
    assert r["n_bodies"] == 5


def test_bridge_list_admittance_spectra_smoke() -> None:
    r = bridge.list_admittance_spectra()
    assert r["ok"] is True
    assert r["n_bodies"] == 5


def test_bridge_get_admittance_rejects_unknown() -> None:
    r = bridge.get_topography_gravity_admittance(body="krypton")
    assert r["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────

def test_cli_admittance_smoke() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["admittance", "--body", "luna"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["spectrum"]["inferred_crustal_density_kg_per_m3"] == pytest.approx(2550.0, abs=50)


def test_cli_admittance_spectra_smoke() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["admittance-spectra"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_bodies"] == 5


def test_cli_admittance_help() -> None:
    """Both v0.21.1 CLI subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("admittance", "admittance-spectra"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
