"""v0.21.9 — Sol Volcanic Outgassing Catalog tests.

Pins the ninth cross-channel coupling surface:

* 6-body roster (terra, mars, venus, io, enceladus, jupiter).
* Headline: Io 1 ton/s SO2 outgassing matches Jupiter Io-torus 1
  ton/s injection → matches v0.21.7 1000 kg/s pickup-ion escape.
  Three independent observational handles on Io→Jupiter mass-transfer.
* Mars dormant flag + non-zero escape rate → "dead planet" story.
* Citation discipline + bridge + CLI.
"""

from __future__ import annotations

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.volcanic_outgassing_catalog import (
    compute_volcanic_outgassing,
    list_volcanic_outgassings,
)
from ephemerides_spectral._research.volcanic_outgassing_data import (
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
    SRC_DORMANT,
    SRC_MAGNETOSPHERIC_INJECTION,
    SRC_PLUME_VENTING,
    SRC_SUBAERIAL_VOLCANISM,
    SRC_SUBMARINE_VOLCANISM,
    SRC_TIDAL_VOLCANISM,
    VOLCANIC_OUTGASSINGS,
    VolcanicOutgassing,
)


# ──────────────────────────────────────────────────────────────────────
# Roster shape
# ──────────────────────────────────────────────────────────────────────

def test_roster_size_is_6() -> None:
    assert len(VOLCANIC_OUTGASSINGS) == 6


def test_canonical_roster_members() -> None:
    by = {m.body for m in VOLCANIC_OUTGASSINGS}
    assert by == {"terra", "mars", "venus", "io", "enceladus", "jupiter"}


def test_sources_count() -> None:
    assert len(SOURCES) == 6


# ──────────────────────────────────────────────────────────────────────
# Headline numerics
# ──────────────────────────────────────────────────────────────────────

def test_io_sulfur_dioxide_one_ton_per_second() -> None:
    """Lellouch 2007: Io outgassing ~1 ton/s SO2 from tidal volcanism.
    Cross-references v0.21.8 100 TW heat flow."""
    by = {m.body: m for m in VOLCANIC_OUTGASSINGS}
    io = by["io"]
    assert io.outgassing_rate_kg_per_s == pytest.approx(1000.0, rel=0.5)
    assert "SO2" in io.dominant_outgassed_species
    assert io.source_mechanism == SRC_TIDAL_VOLCANISM
    assert io.is_active is True


def test_io_jupiter_torus_balance() -> None:
    """Io outgassing rate ≈ Jupiter Io-torus injection rate. Three-ship
    cross-channel closure: v0.21.4 + v0.21.6 + v0.21.8 + v0.21.7 +
    v0.21.9 all converge on Io→Jupiter mass-transfer pipeline."""
    by = {m.body: m for m in VOLCANIC_OUTGASSINGS}
    io_rate = by["io"].outgassing_rate_kg_per_s
    jupiter_rate = by["jupiter"].outgassing_rate_kg_per_s
    # Both should match within factor-of-2 (steady state)
    ratio = io_rate / jupiter_rate
    assert 0.5 <= ratio <= 2.0, (
        f"Io outgassing {io_rate} kg/s vs Jupiter Io-torus injection "
        f"{jupiter_rate} kg/s should match in steady state"
    )


def test_mars_dormant_dead_planet_story() -> None:
    """Modern Mars effectively dormant; outgassing ≈ 0 while v0.21.7
    escape ≈ 2 kg/s → atmospheric inventory shrinking. Famous
    'dead planet' story made quantitative."""
    by = {m.body: m for m in VOLCANIC_OUTGASSINGS}
    mars = by["mars"]
    assert mars.is_active is False
    assert mars.source_mechanism == SRC_DORMANT
    assert mars.outgassing_rate_kg_per_s < 1.0  # << escape rate


def test_terra_carbon_cycle_baseline() -> None:
    """Earth outgassing ~3 kg/s CO2; balanced by carbonate-silicate
    weathering on geological timescales (NOT atmospheric escape)."""
    by = {m.body: m for m in VOLCANIC_OUTGASSINGS}
    terra = by["terra"]
    assert terra.outgassing_rate_kg_per_s == pytest.approx(3.0, abs=2.0)
    assert "CO2" in terra.dominant_outgassed_species
    assert terra.is_active is True


def test_enceladus_plume_h2o() -> None:
    """Hansen 2011 INMS: ~200 kg/s H2O plume venting; supplies
    Saturn E-ring."""
    by = {m.body: m for m in VOLCANIC_OUTGASSINGS}
    enceladus = by["enceladus"]
    assert enceladus.outgassing_rate_kg_per_s == pytest.approx(200.0, abs=100)
    assert "H2O" in enceladus.dominant_outgassed_species
    assert enceladus.source_mechanism == SRC_PLUME_VENTING
    assert "E-ring" in enceladus.notes


def test_jupiter_via_io_injection() -> None:
    """Jupiter's 'outgassing' is via Io plasma torus — the upstream
    side of v0.21.7's 1000 kg/s magnetospheric escape."""
    by = {m.body: m for m in VOLCANIC_OUTGASSINGS}
    jupiter = by["jupiter"]
    assert jupiter.source_mechanism == SRC_MAGNETOSPHERIC_INJECTION
    assert jupiter.outgassing_rate_kg_per_s == pytest.approx(1000.0, rel=0.5)


def test_venus_active_modest_rate() -> None:
    """Bullock 2001: Venus 0.5 kg/s active hotspot outgassing;
    matches v0.21.7 0.4 kg/s escape rate (steady-state CO2)."""
    by = {m.body: m for m in VOLCANIC_OUTGASSINGS}
    venus = by["venus"]
    assert venus.is_active is True
    assert venus.outgassing_rate_kg_per_s < 5.0


def test_active_set() -> None:
    """5 of 6 bodies actively outgassing; only Mars is dormant."""
    active = [m.body for m in VOLCANIC_OUTGASSINGS if m.is_active]
    inactive = [m.body for m in VOLCANIC_OUTGASSINGS if not m.is_active]
    assert len(active) == 5
    assert len(inactive) == 1
    assert "mars" in inactive


def test_source_mechanism_vocabulary() -> None:
    """Mechanisms come from the constant set."""
    valid = {SRC_SUBAERIAL_VOLCANISM, SRC_SUBMARINE_VOLCANISM,
             SRC_TIDAL_VOLCANISM, SRC_PLUME_VENTING,
             SRC_MAGNETOSPHERIC_INJECTION, SRC_DORMANT}
    for m in VOLCANIC_OUTGASSINGS:
        assert m.source_mechanism in valid


# ──────────────────────────────────────────────────────────────────────
# Citation discipline
# ──────────────────────────────────────────────────────────────────────

def test_every_source_key_resolves() -> None:
    for m in VOLCANIC_OUTGASSINGS:
        assert m.source_key in SOURCES


def test_no_unused_sources_entries() -> None:
    used = {m.source_key for m in VOLCANIC_OUTGASSINGS}
    unused = set(SOURCES.keys()) - used
    assert unused == set()


# ──────────────────────────────────────────────────────────────────────
# Pythonic API
# ──────────────────────────────────────────────────────────────────────

def test_compute_unknown_body() -> None:
    r = compute_volcanic_outgassing(body="krypton")
    assert r["ok"] is False


def test_compute_full_roster() -> None:
    r = compute_volcanic_outgassing()
    assert r["ok"] is True
    assert r["n_bodies"] == 6


def test_compute_per_body_io() -> None:
    r = compute_volcanic_outgassing(body="io")
    assert r["ok"] is True
    assert r["outgassing"]["source_mechanism"] == SRC_TIDAL_VOLCANISM


def test_list_volcanic_outgassings_smoke() -> None:
    r = list_volcanic_outgassings()
    assert r["ok"] is True
    assert r["n_bodies"] == 6


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────

def test_bridge_get_volcanic_outgassing_smoke() -> None:
    r = bridge.get_volcanic_outgassing(body="io")
    assert r["ok"] is True
    assert r["outgassing"]["outgassing_rate_kg_per_s"] >= 500


def test_bridge_get_volcanic_outgassing_full_roster() -> None:
    r = bridge.get_volcanic_outgassing()
    assert r["ok"] is True
    assert r["n_bodies"] == 6


def test_bridge_list_volcanic_outgassings_smoke() -> None:
    r = bridge.list_volcanic_outgassings()
    assert r["ok"] is True


def test_bridge_get_volcanic_outgassing_rejects_unknown() -> None:
    r = bridge.get_volcanic_outgassing(body="krypton")
    assert r["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────

def test_cli_volcanic_outgassing_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["volcanic-outgassing", "--body", "io"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["outgassing"]["source_mechanism"] == SRC_TIDAL_VOLCANISM


def test_cli_volcanic_outgassings_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["volcanic-outgassings"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_bodies"] == 6


def test_cli_volcanic_help() -> None:
    """Both v0.21.9 CLI subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("volcanic-outgassing", "volcanic-outgassings"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
