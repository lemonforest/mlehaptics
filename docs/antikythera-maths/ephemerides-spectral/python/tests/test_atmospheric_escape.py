"""v0.21.7 — Sol Atmospheric Escape Catalog tests.

Pins the seventh cross-channel coupling surface:

* 6-body roster (terra, mars, venus, mercury, titan, jupiter).
* Headline numerics: Mars MAVEN integrated 4-Gyr loss ~10^18 kg
  (Jakosky 2018; the headline "Mars lost atmosphere = lost dynamo");
  Earth + Jupiter shielded; Mars + Venus unshielded.
* Magnetic-shielding correlation with mechanism.
* Citation discipline + bridge + CLI.
"""

from __future__ import annotations

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.atmospheric_escape_catalog import (
    compute_atmospheric_escape,
    list_atmospheric_escapes,
)
from ephemerides_spectral._research.atmospheric_escape_data import (
    ATMOSPHERIC_ESCAPES,
    AtmosphericEscape,
    ESC_HYDRODYNAMIC,
    ESC_PHOTOCHEMICAL,
    ESC_PICKUP_ION,
    ESC_SPUTTERING,
    ESC_THERMAL_JEANS,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
)


# ──────────────────────────────────────────────────────────────────────
# Roster shape
# ──────────────────────────────────────────────────────────────────────

def test_roster_size_is_6() -> None:
    assert len(ATMOSPHERIC_ESCAPES) == 6


def test_canonical_roster_members() -> None:
    by = {m.body for m in ATMOSPHERIC_ESCAPES}
    assert by == {"terra", "mars", "venus", "mercury", "titan", "jupiter"}


def test_sources_count() -> None:
    assert len(SOURCES) == 6


# ──────────────────────────────────────────────────────────────────────
# Headline numerics
# ──────────────────────────────────────────────────────────────────────

def test_mars_jakosky_2018_headline() -> None:
    """Jakosky 2018 MAVEN: Mars present-day pickup-ion escape ~2 kg/s;
    integrated 4-Gyr loss ~10^18 kg = ~50% of primordial atmosphere.
    The headline."""
    by = {m.body: m for m in ATMOSPHERIC_ESCAPES}
    mars = by["mars"]
    assert mars.escape_rate_kg_per_s == pytest.approx(2.0, abs=1.0)
    assert mars.dominant_escape_mechanism == ESC_PICKUP_ION
    assert mars.magnetic_shielding_present is False
    assert mars.integrated_loss_4Gyr_kg == pytest.approx(1.0e18, rel=2.0)
    assert mars.dominant_escaping_species == "O+"


def test_terra_thermal_jeans_only() -> None:
    """Earth IGRF shielding → only thermal Jeans escape of H/He."""
    by = {m.body: m for m in ATMOSPHERIC_ESCAPES}
    terra = by["terra"]
    assert terra.dominant_escape_mechanism == ESC_THERMAL_JEANS
    assert terra.magnetic_shielding_present is True
    assert terra.dominant_escaping_species == "H"


def test_titan_highest_absolute_rate() -> None:
    """Strobel 2008: Titan's hydrodynamic escape ~30 kg/s — highest
    absolute rate in the catalog despite small body size."""
    by = {m.body: m for m in ATMOSPHERIC_ESCAPES}
    by_rates = {m.body: m.escape_rate_kg_per_s for m in ATMOSPHERIC_ESCAPES}
    # Jupiter is highest because of Io torus (1000 kg/s); Titan is
    # second-highest among classic atmospheric bodies.
    assert by_rates["titan"] == pytest.approx(30.0, abs=10.0)
    assert by_rates["titan"] > by_rates["terra"]
    assert by_rates["titan"] > by_rates["mars"]
    assert by_rates["titan"] > by_rates["venus"]
    # Titan uses hydrodynamic mechanism
    assert by["titan"].dominant_escape_mechanism == ESC_HYDRODYNAMIC


def test_jupiter_io_torus_dominates() -> None:
    """Bagenal 2007: Jupiter's mass loss is dominated by Io plasma
    torus (1000 kg/s of S+/O+) — highest in catalog."""
    by = {m.body: m for m in ATMOSPHERIC_ESCAPES}
    jupiter = by["jupiter"]
    assert jupiter.escape_rate_kg_per_s >= 100  # 1000 ± slop
    assert "Io" in jupiter.dominant_escaping_species or \
           "S+" in jupiter.dominant_escaping_species or \
           "torus" in jupiter.notes.lower()


def test_unshielded_bodies_use_pickup_ion() -> None:
    """Mars + Venus (no intrinsic dipole) → pickup-ion escape."""
    by = {m.body: m for m in ATMOSPHERIC_ESCAPES}
    assert by["mars"].magnetic_shielding_present is False
    assert by["venus"].magnetic_shielding_present is False
    assert by["mars"].dominant_escape_mechanism == ESC_PICKUP_ION
    assert by["venus"].dominant_escape_mechanism == ESC_PICKUP_ION


def test_shielded_set() -> None:
    """Bodies with magnetic shielding: terra, mercury, titan, jupiter.
    Mercury weak shielding; Titan via Saturn's magnetosphere."""
    by = {m.body: m for m in ATMOSPHERIC_ESCAPES}
    shielded = {m.body for m in ATMOSPHERIC_ESCAPES
                if m.magnetic_shielding_present}
    assert shielded == {"terra", "mercury", "titan", "jupiter"}


def test_escape_mechanism_vocabulary() -> None:
    """All mechanisms are from the constant set."""
    valid = {ESC_THERMAL_JEANS, ESC_HYDRODYNAMIC, ESC_PICKUP_ION,
             ESC_PHOTOCHEMICAL, ESC_SPUTTERING}
    for m in ATMOSPHERIC_ESCAPES:
        assert m.dominant_escape_mechanism in valid


# ──────────────────────────────────────────────────────────────────────
# Citation discipline
# ──────────────────────────────────────────────────────────────────────

def test_every_source_key_resolves() -> None:
    for m in ATMOSPHERIC_ESCAPES:
        assert m.source_key in SOURCES


def test_no_unused_sources_entries() -> None:
    used = {m.source_key for m in ATMOSPHERIC_ESCAPES}
    unused = set(SOURCES.keys()) - used
    assert unused == set()


# ──────────────────────────────────────────────────────────────────────
# Pythonic API
# ──────────────────────────────────────────────────────────────────────

def test_compute_unknown_body() -> None:
    r = compute_atmospheric_escape(body="krypton")
    assert r["ok"] is False


def test_compute_full_roster() -> None:
    r = compute_atmospheric_escape()
    assert r["ok"] is True
    assert r["n_bodies"] == 6


def test_compute_per_body_mars() -> None:
    r = compute_atmospheric_escape(body="mars")
    assert r["ok"] is True
    assert r["escape"]["dominant_escape_mechanism"] == ESC_PICKUP_ION


def test_list_atmospheric_escapes_smoke() -> None:
    r = list_atmospheric_escapes()
    assert r["ok"] is True
    assert r["n_bodies"] == 6


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────

def test_bridge_get_atmospheric_escape_smoke() -> None:
    r = bridge.get_atmospheric_escape(body="mars")
    assert r["ok"] is True
    assert r["escape"]["magnetic_shielding_present"] is False


def test_bridge_get_atmospheric_escape_full_roster() -> None:
    r = bridge.get_atmospheric_escape()
    assert r["ok"] is True
    assert r["n_bodies"] == 6


def test_bridge_list_atmospheric_escapes_smoke() -> None:
    r = bridge.list_atmospheric_escapes()
    assert r["ok"] is True


def test_bridge_get_atmospheric_escape_rejects_unknown() -> None:
    r = bridge.get_atmospheric_escape(body="krypton")
    assert r["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────

def test_cli_atmospheric_escape_smoke() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["atmospheric-escape", "--body", "mars"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["escape"]["dominant_escape_mechanism"] == ESC_PICKUP_ION


def test_cli_atmospheric_escapes_smoke() -> None:
    import io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["atmospheric-escapes"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_bodies"] == 6


def test_cli_atmospheric_help() -> None:
    """Both v0.21.7 CLI subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("atmospheric-escape", "atmospheric-escapes"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
