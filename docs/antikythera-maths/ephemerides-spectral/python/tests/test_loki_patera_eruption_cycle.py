"""v0.24.12 — Sol Loki Patera Eruption Cycle Catalog tests.

Pins the **second time** the project ships a *temporal-spectrum*
observable on a single sub-system (after v0.24.8 Axial Seamount).
Where Axial is a mid-ocean-ridge submarine volcano driven by mantle-
plume magma supply, **Loki Patera is driven by tidal heating from
the Galilean Laplace 4:2:1 mean-motion resonance** — the canonical
3-body orbital lock between Io, Europa, and Ganymede.

Headline closure: the Galilean Laplace commensurability
(4*P_Io ≈ 2*P_Europa ≈ P_Ganymede) is verified to within ~1% by
the published orbital periods. The deep-mechanism reason Loki
exists at all.
"""

from __future__ import annotations

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.loki_patera_catalog import (
    get_loki_galilean_laplace_signature,
    get_loki_patera_eruption_cycle,
    list_loki_patera_eruption_cycle,
)
from ephemerides_spectral._research.loki_patera_data import (
    EUROPA_ORBITAL_PERIOD_DAYS,
    GANYMEDE_ORBITAL_PERIOD_DAYS,
    IO_FORCED_ECCENTRICITY,
    IO_ORBITAL_PERIOD_DAYS,
    IO_TIDAL_HEATING_W,
    LOKI_CYCLE_MODES,
    LOKI_CYCLE_PEAKS,
    LOKI_CYCLE_PERIOD_RANGE_DAYS,
    LOKI_DIAMETER_KM,
    LOKI_FRACTION_OF_IO_OUTPUT,
    LOKI_LATITUDE_DEG,
    LOKI_LAVA_LAKE_AREA_KM2,
    LOKI_LONGITUDE_DEG,
    LOKI_MEAN_CYCLE_PERIOD_DAYS,
    PRECISION_HIGH,
    SOURCES,
    CycleMode,
    LokiCyclePeakObservation,
)


# ──────────────────────────────────────────────────────────────────────
# Roster shape
# ──────────────────────────────────────────────────────────────────────


def test_cycle_peaks_count_6() -> None:
    """Six published cycle-peak observations spanning 1990-2017."""
    assert len(LOKI_CYCLE_PEAKS) == 6


def test_cycle_modes_count_6() -> None:
    """Six action-angle modes: main cycle, brightening, resurfacing,
    cooling, Io orbital, Galilean Laplace 4:2:1."""
    assert len(LOKI_CYCLE_MODES) == 6


def test_sources_count_8() -> None:
    """Eight cited sources: Rathbun 2002 (canonical periodicity);
    de Kleer 2017+ AO monitoring; Veeder 1994 long-baseline thermal;
    Spencer 1990 Voyager-era; Rathbun-Spencer 2010 multi-volcano
    review; de Kleer 2019 multi-phase analysis; Peale-Cassen-Reynolds
    1979 tidal-heating prediction; Murray-Dermott 1999 textbook."""
    assert len(SOURCES) == 8


def test_cycle_peak_names_unique() -> None:
    names = [p.name for p in LOKI_CYCLE_PEAKS]
    assert len(names) == len(set(names))


def test_cycle_mode_names_unique() -> None:
    names = [m.name for m in LOKI_CYCLE_MODES]
    assert len(names) == len(set(names))


def test_every_cycle_peak_source_resolves() -> None:
    for p in LOKI_CYCLE_PEAKS:
        assert p.source_key in SOURCES


def test_every_cycle_mode_source_resolves() -> None:
    for m in LOKI_CYCLE_MODES:
        assert m.source_key in SOURCES


# ──────────────────────────────────────────────────────────────────────
# Loki Patera geometry / location (Voyager-confirmed values)
# ──────────────────────────────────────────────────────────────────────


def test_loki_latitude_north_equator() -> None:
    """Loki Patera sits ~12.7° N of Io's equator."""
    assert 10.0 < LOKI_LATITUDE_DEG < 15.0


def test_loki_diameter_about_200km() -> None:
    """Loki Patera is the largest persistent thermal anomaly in the
    Solar System. ~200 km diameter caldera."""
    assert 150.0 < LOKI_DIAMETER_KM < 250.0


def test_loki_lava_lake_area_realistic() -> None:
    """Lava lake area scales as π·r² for ~165 km mean diameter,
    giving ~21,000 km²."""
    assert 15000.0 < LOKI_LAVA_LAKE_AREA_KM2 < 30000.0


# ──────────────────────────────────────────────────────────────────────
# Cycle period (the headline observable)
# ──────────────────────────────────────────────────────────────────────


def test_mean_cycle_period_540_days() -> None:
    """Rathbun 2002 canonical mean cycle period."""
    assert LOKI_MEAN_CYCLE_PERIOD_DAYS == 540.0


def test_cycle_period_range_brackets_mean() -> None:
    """Quasi-periodic — observed periods range 480-580 days, with
    the mean inside the range."""
    lo, hi = LOKI_CYCLE_PERIOD_RANGE_DAYS
    assert lo < LOKI_MEAN_CYCLE_PERIOD_DAYS < hi


def test_cycle_period_range_about_pm_50_days() -> None:
    """The range half-width is ~50 days (~10% of the mean) — that's
    the 'quasi' in quasi-periodic."""
    lo, hi = LOKI_CYCLE_PERIOD_RANGE_DAYS
    half_width = (hi - lo) / 2.0
    assert 30.0 < half_width < 80.0


# ──────────────────────────────────────────────────────────────────────
# Tidal-heating forcing budget
# ──────────────────────────────────────────────────────────────────────


def test_io_tidal_heating_about_1e14_W() -> None:
    """Canonical Io globally-integrated tidal dissipation."""
    assert 5.0e13 < IO_TIDAL_HEATING_W < 5.0e14


def test_io_forced_eccentricity_about_4e_minus_3() -> None:
    """Forced by the Galilean Laplace 4:2:1 lock; far above
    tidal-damping equilibrium."""
    assert 0.001 < IO_FORCED_ECCENTRICITY < 0.01


def test_loki_fraction_of_io_output_5_to_15_percent() -> None:
    """Loki accounts for 5-15% of Io's globally-integrated thermal
    output — the dominant single contributor."""
    lo, hi = LOKI_FRACTION_OF_IO_OUTPUT
    assert 0.0 < lo < hi < 0.3


def test_loki_thermal_output_dominant_single_contributor() -> None:
    """At 5-15% of ~10^14 W, Loki contributes ~5e12 to ~1.5e13 W —
    larger than the Earth's total volcanic output (~3e10 W) by
    ~2-3 orders of magnitude."""
    lo_frac, hi_frac = LOKI_FRACTION_OF_IO_OUTPUT
    loki_low_W = lo_frac * IO_TIDAL_HEATING_W
    loki_high_W = hi_frac * IO_TIDAL_HEATING_W
    earth_volcanic_W = 3.0e10
    assert loki_low_W > 100.0 * earth_volcanic_W
    assert loki_high_W > 100.0 * earth_volcanic_W


# ──────────────────────────────────────────────────────────────────────
# Galilean Laplace 4:2:1 commensurability — THE headline closure
# ──────────────────────────────────────────────────────────────────────


def test_galilean_periods_increase_4_2_1_factor_2() -> None:
    """Each step in the chain doubles the period (factor-2 mean-
    motion resonance)."""
    assert EUROPA_ORBITAL_PERIOD_DAYS > IO_ORBITAL_PERIOD_DAYS
    assert GANYMEDE_ORBITAL_PERIOD_DAYS > EUROPA_ORBITAL_PERIOD_DAYS


def test_4_io_period_close_to_ganymede() -> None:
    """4 * P_Io ≈ P_Ganymede (the 4:1 leg of the Laplace lock).
    Agreement to within ~1%."""
    four_io = 4.0 * IO_ORBITAL_PERIOD_DAYS
    residual = abs(four_io - GANYMEDE_ORBITAL_PERIOD_DAYS)
    fractional = residual / GANYMEDE_ORBITAL_PERIOD_DAYS
    assert fractional < 0.02


def test_2_europa_period_close_to_ganymede() -> None:
    """2 * P_Europa ≈ P_Ganymede (the 2:1 leg)."""
    two_europa = 2.0 * EUROPA_ORBITAL_PERIOD_DAYS
    residual = abs(two_europa - GANYMEDE_ORBITAL_PERIOD_DAYS)
    fractional = residual / GANYMEDE_ORBITAL_PERIOD_DAYS
    assert fractional < 0.02


def test_galilean_laplace_signature_returns_ok() -> None:
    """The headline signature surface returns ok=True with the
    expected residual structure."""
    sig = get_loki_galilean_laplace_signature()
    assert sig["ok"] is True
    assert sig["max_residual_fractional"] < 0.02
    assert sig["max_residual_days"] > 0.0


def test_galilean_laplace_signature_contains_loki_cycle_ratio() -> None:
    """Loki's ~540-d cycle is ~305 Io orbital periods (a useful
    decomposition for action-angle work — the cycle is NOT a small-
    integer multiple of Io's orbital period; it's a slow lava-lake
    overturn timescale on top of the orbital forcing)."""
    sig = get_loki_galilean_laplace_signature()
    ratio = sig["loki_cycle_to_io_orbital_ratio"]
    expected = LOKI_MEAN_CYCLE_PERIOD_DAYS / IO_ORBITAL_PERIOD_DAYS
    assert ratio == pytest.approx(expected)
    assert 250.0 < ratio < 400.0


def test_galilean_laplace_signature_io_eccentricity_pinned() -> None:
    sig = get_loki_galilean_laplace_signature()
    assert sig["io_forced_eccentricity"] == IO_FORCED_ECCENTRICITY


# ──────────────────────────────────────────────────────────────────────
# Cycle peak ordering / cycle indexing
# ──────────────────────────────────────────────────────────────────────


def test_cycle_peaks_chronologically_ordered() -> None:
    """Peaks are listed earliest-to-latest by year."""
    years = [p.peak_year for p in LOKI_CYCLE_PEAKS]
    assert years == sorted(years)


def test_cycle_peaks_span_at_least_25_years() -> None:
    """Coverage 1990-2015 minimum."""
    years = [p.peak_year for p in LOKI_CYCLE_PEAKS]
    assert max(years) - min(years) >= 25


def test_2002_peak_is_anchor() -> None:
    """The 2002 peak (Rathbun's anchor for the periodicity claim) is
    cycle_index_from_anchor=0; later peaks have positive indices."""
    by_year = {p.peak_year: p for p in LOKI_CYCLE_PEAKS}
    assert by_year[2002].cycle_index_from_anchor == 0
    assert by_year[2013].cycle_index_from_anchor > 0
    assert by_year[2015].cycle_index_from_anchor > (
        by_year[2013].cycle_index_from_anchor
    )


# ──────────────────────────────────────────────────────────────────────
# get_loki_patera_eruption_cycle (headline catalog surface)
# ──────────────────────────────────────────────────────────────────────


def test_get_eruption_cycle_returns_ok() -> None:
    cat = get_loki_patera_eruption_cycle()
    assert cat["ok"] is True


def test_get_eruption_cycle_includes_peaks_and_modes() -> None:
    cat = get_loki_patera_eruption_cycle()
    assert cat["n_peaks"] == 6
    assert cat["n_modes"] == 6
    assert len(cat["peaks"]) == 6
    assert len(cat["modes"]) == 6


def test_get_eruption_cycle_includes_location_and_geometry() -> None:
    cat = get_loki_patera_eruption_cycle()
    assert "location" in cat
    assert "geometry" in cat
    assert cat["location"]["latitude_deg"] == LOKI_LATITUDE_DEG
    assert cat["geometry"]["diameter_km"] == LOKI_DIAMETER_KM


def test_get_eruption_cycle_alternate_longitude_180_degrees() -> None:
    """Loki's longitude can be expressed as either ~309.6° W (negative
    east-positive) or ~50.4° E. The catalog surfaces both."""
    cat = get_loki_patera_eruption_cycle()
    loc = cat["location"]
    primary = loc["longitude_deg"]
    alternate = loc["alternate_longitude_e_deg"]
    assert primary < 0.0
    assert alternate > 0.0
    assert alternate == pytest.approx(360.0 + primary)


def test_get_eruption_cycle_includes_forcing_budget() -> None:
    cat = get_loki_patera_eruption_cycle()
    forc = cat["forcing"]
    assert forc["io_tidal_heating_W"] == IO_TIDAL_HEATING_W
    assert forc["io_forced_eccentricity"] == IO_FORCED_ECCENTRICITY
    assert forc["io_orbital_period_days"] == IO_ORBITAL_PERIOD_DAYS


# ──────────────────────────────────────────────────────────────────────
# list_loki_patera_eruption_cycle (full enumeration)
# ──────────────────────────────────────────────────────────────────────


def test_list_eruption_cycle_returns_ok() -> None:
    r = list_loki_patera_eruption_cycle()
    assert r["ok"] is True
    assert r["n_peaks"] == 6
    assert r["n_modes"] == 6
    assert r["n_sources"] == 8


# ──────────────────────────────────────────────────────────────────────
# Bridge wrappers
# ──────────────────────────────────────────────────────────────────────


def test_bridge_get_loki_patera_eruption_cycle() -> None:
    r = bridge.get_loki_patera_eruption_cycle()
    assert r["ok"] is True
    assert r["n_peaks"] == 6


def test_bridge_get_loki_galilean_laplace_signature() -> None:
    r = bridge.get_loki_galilean_laplace_signature()
    assert r["ok"] is True
    assert r["max_residual_fractional"] < 0.02


def test_bridge_list_loki_patera_eruption_cycle() -> None:
    r = bridge.list_loki_patera_eruption_cycle()
    assert r["ok"] is True
    assert r["n_peaks"] == 6


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────


def test_cli_loki_patera_eruption_cycle_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["loki-patera-eruption-cycle"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["ok"] is True
    assert payload["n_peaks"] == 6


def test_cli_loki_galilean_laplace_signature_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["loki-galilean-laplace-signature"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["ok"] is True
    assert payload["max_residual_fractional"] < 0.02


def test_cli_loki_patera_eruption_cycle_full_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["loki-patera-eruption-cycle-full"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["ok"] is True
    assert payload["n_sources"] == 8


def test_cli_loki_help() -> None:
    """All v0.24.12 CLI subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in (
        "loki-patera-eruption-cycle",
        "loki-galilean-laplace-signature",
        "loki-patera-eruption-cycle-full",
    ):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0


# ──────────────────────────────────────────────────────────────────────
# Cross-references to cousin v0.24.x ships
# ──────────────────────────────────────────────────────────────────────


def test_loki_dataclass_types() -> None:
    """Sanity: catalog is built from concrete dataclasses, not loose
    dicts."""
    for p in LOKI_CYCLE_PEAKS:
        assert isinstance(p, LokiCyclePeakObservation)
    for m in LOKI_CYCLE_MODES:
        assert isinstance(m, CycleMode)


def test_high_precision_constants_exposed() -> None:
    """Discipline check: the precision-tier constants exposed at the
    data module's surface match the v0.24.8 / v0.24.11 convention."""
    assert PRECISION_HIGH == "high"
