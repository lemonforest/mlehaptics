"""v0.21.8 — Sol Heat Flow Catalog tests.

Pins the eighth cross-channel coupling surface:

* 6-body roster (terra, mars, io, europa, enceladus, titan).
* Headline: Io 100 TW = 99% tidal (most volcanically active body in
  solar system; cross-references v0.21.4 Q~80 + v0.21.6 +3.6 cm/yr).
* Earth radiogenic-dominated; Mars radiogenic-dominated; ocean worlds
  tidal-dominated.
* Energy-budget fractions sum to ~1 invariant.
* Citation discipline + bridge + CLI.
"""

from __future__ import annotations

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.heat_flow_catalog import (
    compute_heat_flow,
    list_heat_flows,
)
from ephemerides_spectral._research.heat_flow_data import (
    HEAT_FLOWS,
    HeatFlow,
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
    assert len(HEAT_FLOWS) == 6


def test_canonical_roster_members() -> None:
    by = {m.body for m in HEAT_FLOWS}
    assert by == {"terra", "mars", "io", "europa", "enceladus", "titan"}


def test_sources_count() -> None:
    assert len(SOURCES) == 6


# ──────────────────────────────────────────────────────────────────────
# Headline numerics
# ──────────────────────────────────────────────────────────────────────

def test_io_100tw_99pct_tidal_headline() -> None:
    """Veeder 2012: Io ~100 TW total, 99% tidal — most volcanically
    active body in solar system. Cross-references v0.21.4 Q~80."""
    by = {m.body: m for m in HEAT_FLOWS}
    io = by["io"]
    assert io.total_heat_flow_TW == pytest.approx(100.0, abs=20.0)
    assert io.tidal_fraction >= 0.95
    assert io.precision_flag == PRECISION_HIGH


def test_terra_radiogenic_dominated() -> None:
    """Davies 2010: Earth 47 TW; ~66% radiogenic, ~34% primordial,
    tidal negligible."""
    by = {m.body: m for m in HEAT_FLOWS}
    terra = by["terra"]
    assert terra.total_heat_flow_TW == pytest.approx(47.0, abs=5.0)
    assert terra.radiogenic_fraction > 0.5
    assert terra.tidal_fraction < 0.01


def test_mars_radiogenic_dominated() -> None:
    """Frizzell 2023 InSight+GRS: Mars ~1.5 TW (crustal ~3-14 mW/m^2); radiogenic-dominated."""
    by = {m.body: m for m in HEAT_FLOWS}
    mars = by["mars"]
    assert mars.total_heat_flow_TW < 5.0  # << Earth's 47 TW
    assert mars.radiogenic_fraction > 0.5


def test_europa_tidal_dominated() -> None:
    """Vance 2018: Europa ~0.5 TW; tidal-dominated; maintains
    subsurface ocean."""
    by = {m.body: m for m in HEAT_FLOWS}
    europa = by["europa"]
    assert europa.tidal_fraction > 0.5
    assert "ocean" in europa.notes.lower()


def test_enceladus_south_polar_plumes() -> None:
    """Howett 2011: Enceladus ~10 GW = 0.01 TW; tidal-dominated;
    drives plume geyser system."""
    by = {m.body: m for m in HEAT_FLOWS}
    enceladus = by["enceladus"]
    assert enceladus.total_heat_flow_TW == pytest.approx(0.01, abs=0.005)
    assert enceladus.tidal_fraction > 0.9
    assert "plume" in enceladus.notes.lower()


def test_titan_modest_tidal_contribution() -> None:
    """Tobie 2008: Titan ~2 TW; modest tidal heating in icy outer
    mantle."""
    by = {m.body: m for m in HEAT_FLOWS}
    titan = by["titan"]
    assert titan.total_heat_flow_TW > 0.5
    assert titan.total_heat_flow_TW < 5.0
    assert titan.tidal_fraction > 0.3


def test_io_most_active() -> None:
    """Io should be the highest absolute heat flow in the catalog."""
    by_tw = {m.body: m.total_heat_flow_TW for m in HEAT_FLOWS}
    assert by_tw["io"] == max(by_tw.values())


def test_io_per_radius_ratio_exceeds_terra() -> None:
    """Io has 4× smaller radius than Earth but 2× more heat flow —
    extreme heat-flow-per-area excess driving the volcanism."""
    by = {m.body: m for m in HEAT_FLOWS}
    assert by["io"].total_heat_flow_TW > by["terra"].total_heat_flow_TW


# ──────────────────────────────────────────────────────────────────────
# Energy-budget invariants
# ──────────────────────────────────────────────────────────────────────

def test_fractions_sum_to_unity() -> None:
    """For every body, tidal + radiogenic + primordial fractions
    should sum to ~1 (within float-rounding tolerance)."""
    for m in HEAT_FLOWS:
        total = m.tidal_fraction + m.radiogenic_fraction + m.primordial_fraction
        assert total == pytest.approx(1.0, abs=0.05), (
            f"{m.body}: tidal={m.tidal_fraction} + "
            f"radiogenic={m.radiogenic_fraction} + "
            f"primordial={m.primordial_fraction} = {total} != 1"
        )


def test_all_fractions_in_unit_interval() -> None:
    """Every fraction must be in [0, 1]."""
    for m in HEAT_FLOWS:
        assert 0.0 <= m.tidal_fraction <= 1.0
        assert 0.0 <= m.radiogenic_fraction <= 1.0
        assert 0.0 <= m.primordial_fraction <= 1.0


def test_all_total_heat_flow_positive() -> None:
    for m in HEAT_FLOWS:
        assert m.total_heat_flow_TW > 0.0


# ──────────────────────────────────────────────────────────────────────
# Citation discipline
# ──────────────────────────────────────────────────────────────────────

def test_every_source_key_resolves() -> None:
    for m in HEAT_FLOWS:
        assert m.source_key in SOURCES


def test_no_unused_sources_entries() -> None:
    used = {m.source_key for m in HEAT_FLOWS}
    unused = set(SOURCES.keys()) - used
    assert unused == set()


# ──────────────────────────────────────────────────────────────────────
# Pythonic API
# ──────────────────────────────────────────────────────────────────────

def test_compute_unknown_body() -> None:
    r = compute_heat_flow(body="krypton")
    assert r["ok"] is False


def test_compute_full_roster() -> None:
    r = compute_heat_flow()
    assert r["ok"] is True
    assert r["n_bodies"] == 6


def test_compute_per_body_io() -> None:
    r = compute_heat_flow(body="io")
    assert r["ok"] is True
    assert r["heat_flow"]["total_heat_flow_TW"] == pytest.approx(100.0, abs=20.0)


def test_list_heat_flows_smoke() -> None:
    r = list_heat_flows()
    assert r["ok"] is True
    assert r["n_bodies"] == 6


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────

def test_bridge_get_heat_flow_smoke() -> None:
    r = bridge.get_heat_flow(body="io")
    assert r["ok"] is True
    assert r["heat_flow"]["tidal_fraction"] >= 0.95


def test_bridge_get_heat_flow_full_roster() -> None:
    r = bridge.get_heat_flow()
    assert r["ok"] is True
    assert r["n_bodies"] == 6


def test_bridge_list_heat_flows_smoke() -> None:
    r = bridge.list_heat_flows()
    assert r["ok"] is True


def test_bridge_get_heat_flow_rejects_unknown() -> None:
    r = bridge.get_heat_flow(body="krypton")
    assert r["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────

def test_cli_heat_flow_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["heat-flow", "--body", "io"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["heat_flow"]["tidal_fraction"] >= 0.95


def test_cli_heat_flows_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["heat-flows"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_bodies"] == 6


def test_cli_heat_flow_help() -> None:
    """Both v0.21.8 CLI subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("heat-flow", "heat-flows"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
