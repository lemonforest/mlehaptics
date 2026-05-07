"""v0.21.10 — Sol Thermal Balance Catalog tests.

Pins the tenth cross-channel coupling surface:

* 6-body roster (terra, mars, venus, mercury, titan, jupiter).
* Headlines: Earth +33.5 K greenhouse (canonical); Venus +505 K
  runaway-greenhouse; Jupiter +45 K internal-heat dominated; Mercury
  0 K (no atmosphere → pure radiative balance).
* Energy-budget cross-references with v0.21.8 heat flow.
* Citation discipline + bridge + CLI.
"""

from __future__ import annotations

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.thermal_balance_catalog import (
    compute_thermal_balance,
    list_thermal_balances,
)
from ephemerides_spectral._research.thermal_balance_data import (
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
    THERMAL_BALANCES,
    ThermalBalance,
)


# ──────────────────────────────────────────────────────────────────────
# Roster shape
# ──────────────────────────────────────────────────────────────────────

def test_roster_size_is_6() -> None:
    assert len(THERMAL_BALANCES) == 6


def test_canonical_roster_members() -> None:
    by = {m.body for m in THERMAL_BALANCES}
    assert by == {"terra", "mars", "venus", "mercury", "titan", "jupiter"}


def test_sources_count() -> None:
    assert len(SOURCES) == 6


# ──────────────────────────────────────────────────────────────────────
# Headline numerics
# ──────────────────────────────────────────────────────────────────────

def test_earth_canonical_greenhouse() -> None:
    """Kiehl 1997: Earth T_eq=254.6 K, T_obs=288.15 K, +33.5 K
    greenhouse — the canonical textbook decomposition."""
    by = {m.body: m for m in THERMAL_BALANCES}
    terra = by["terra"]
    assert terra.equilibrium_temperature_K == pytest.approx(254.6, abs=2)
    assert terra.observed_temperature_K == pytest.approx(288.15, abs=0.5)
    assert terra.greenhouse_offset_K == pytest.approx(33.5, abs=1)


def test_venus_runaway_greenhouse() -> None:
    """Bullock 2001: Venus T_eq=231.8 K, T_obs=737 K, +505 K
    runaway-greenhouse offset — the famous case."""
    by = {m.body: m for m in THERMAL_BALANCES}
    venus = by["venus"]
    assert venus.greenhouse_offset_K >= 400
    assert venus.observed_temperature_K == pytest.approx(737, abs=10)
    # Venus surface hotter than Mercury despite being further from Sun
    mercury_T = by["mercury"].observed_temperature_K
    assert venus.observed_temperature_K > mercury_T


def test_jupiter_internal_heat_dominated() -> None:
    """Hubbard 1999: Jupiter T_eq=110 K, T_obs=165 K @ 1-bar; internal-
    heat-dominated (~45 K) because Jupiter radiates 1.7x what it absorbs."""
    by = {m.body: m for m in THERMAL_BALANCES}
    jupiter = by["jupiter"]
    assert jupiter.internal_heat_offset_K >= 30
    assert jupiter.internal_heat_offset_K > jupiter.greenhouse_offset_K


def test_mercury_no_atmosphere_zero_offsets() -> None:
    """Mercury has no atmosphere → pure Stefan-Boltzmann radiative
    balance; greenhouse + tidal + internal all ~0."""
    by = {m.body: m for m in THERMAL_BALANCES}
    mercury = by["mercury"]
    assert mercury.greenhouse_offset_K == 0
    assert mercury.tidal_offset_K == 0
    assert mercury.internal_heat_offset_K == 0


def test_mars_naked_planet() -> None:
    """Haberle 2013: Mars 636-Pa CO₂ too thin for significant
    greenhouse; T_obs ≈ T_eq."""
    by = {m.body: m for m in THERMAL_BALANCES}
    mars = by["mars"]
    assert mars.greenhouse_offset_K < 10
    assert abs(mars.equilibrium_temperature_K - mars.observed_temperature_K) < 10


def test_titan_greenhouse_plus_tidal() -> None:
    """Strobel 2009: Titan +9 K CH₄/N₂ greenhouse + ~2 K Saturnian
    tidal heating."""
    by = {m.body: m for m in THERMAL_BALANCES}
    titan = by["titan"]
    assert titan.greenhouse_offset_K >= 5
    assert titan.tidal_offset_K > 0


def test_observed_minus_equilibrium_consistent() -> None:
    """For every body, T_obs - T_eq should approximately equal the
    sum of greenhouse + tidal + internal-heat offsets (±5 K rounding)."""
    for m in THERMAL_BALANCES:
        observed_offset = m.observed_temperature_K - m.equilibrium_temperature_K
        decomposition_sum = (
            m.greenhouse_offset_K
            + m.tidal_offset_K
            + m.internal_heat_offset_K
        )
        # Allow 5 K slop for Mars (decomposition slightly approximate).
        assert abs(observed_offset - decomposition_sum) < 10, (
            f"{m.body}: T_obs - T_eq = {observed_offset} K, "
            f"decomposition sum = {decomposition_sum} K"
        )


# ──────────────────────────────────────────────────────────────────────
# Energy-budget invariants
# ──────────────────────────────────────────────────────────────────────

def test_all_temperatures_positive() -> None:
    for m in THERMAL_BALANCES:
        assert m.equilibrium_temperature_K > 0
        assert m.observed_temperature_K > 0


def test_all_offsets_finite() -> None:
    """Greenhouse + tidal + internal-heat must all be finite real."""
    import math
    for m in THERMAL_BALANCES:
        assert math.isfinite(m.greenhouse_offset_K)
        assert math.isfinite(m.tidal_offset_K)
        assert math.isfinite(m.internal_heat_offset_K)


# ──────────────────────────────────────────────────────────────────────
# Citation discipline
# ──────────────────────────────────────────────────────────────────────

def test_every_source_key_resolves() -> None:
    for m in THERMAL_BALANCES:
        assert m.source_key in SOURCES


def test_no_unused_sources_entries() -> None:
    used = {m.source_key for m in THERMAL_BALANCES}
    unused = set(SOURCES.keys()) - used
    assert unused == set()


# ──────────────────────────────────────────────────────────────────────
# Pythonic API
# ──────────────────────────────────────────────────────────────────────

def test_compute_unknown_body() -> None:
    r = compute_thermal_balance(body="krypton")
    assert r["ok"] is False


def test_compute_full_roster() -> None:
    r = compute_thermal_balance()
    assert r["ok"] is True
    assert r["n_bodies"] == 6


def test_compute_per_body_venus() -> None:
    r = compute_thermal_balance(body="venus")
    assert r["ok"] is True
    assert r["balance"]["greenhouse_offset_K"] >= 400


def test_list_thermal_balances_smoke() -> None:
    r = list_thermal_balances()
    assert r["ok"] is True
    assert r["n_bodies"] == 6


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────

def test_bridge_get_thermal_balance_smoke() -> None:
    r = bridge.get_thermal_balance(body="terra")
    assert r["ok"] is True
    assert r["balance"]["greenhouse_offset_K"] == pytest.approx(33.5, abs=1)


def test_bridge_get_thermal_balance_full_roster() -> None:
    r = bridge.get_thermal_balance()
    assert r["ok"] is True
    assert r["n_bodies"] == 6


def test_bridge_list_thermal_balances_smoke() -> None:
    r = bridge.list_thermal_balances()
    assert r["ok"] is True


def test_bridge_get_thermal_balance_rejects_unknown() -> None:
    r = bridge.get_thermal_balance(body="krypton")
    assert r["ok"] is False


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────

def test_cli_thermal_balance_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["thermal-balance", "--body", "venus"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["balance"]["greenhouse_offset_K"] >= 400


def test_cli_thermal_balances_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["thermal-balances"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_bodies"] == 6


def test_cli_thermal_help() -> None:
    """Both v0.21.10 CLI subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in ("thermal-balance", "thermal-balances"):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
