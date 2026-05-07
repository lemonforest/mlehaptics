"""v0.24.8 — Sol Axial Seamount Eruption Chronology Catalog tests.

Pins the **first time** the project ships a *temporal-spectrum*
observable on a single sub-system (Axial Seamount eruption cycle)
rather than a spatial graph or per-body action-angle roster. The
HIT/MISS asymmetry of the Chadwick-Nooner forecast methodology is
the v0.24.2-style spectral-stability failure mode applied at
decade timescales.
"""

from __future__ import annotations

import pytest

from ephemerides_spectral import bridge
from ephemerides_spectral._research.axial_seamount_catalog import (
    CATALOG_REFERENCE_YEAR,
    get_axial_inflation_cycle_signature,
    get_axial_seamount_chronology,
    list_axial_seamount,
)
from ephemerides_spectral._research.axial_seamount_data import (
    AXIAL_CALDERA_LENGTH_KM,
    AXIAL_CALDERA_WIDTH_KM,
    AXIAL_ERUPTIONS,
    AXIAL_GEODETIC_TRIGGER_M,
    AXIAL_SUMMIT_DEPTH_M,
    AXIAL_SUMMIT_LAT_DEG,
    AXIAL_SUMMIT_LON_DEG,
    CHADWICK_FORECASTS,
    INFLATION_PHASES,
    PRECISION_HIGH,
    SOURCES,
    AxialEruption,
    ChadwickForecast,
    InflationPhase,
)


# ──────────────────────────────────────────────────────────────────────
# Roster shape
# ──────────────────────────────────────────────────────────────────────


def test_eruption_count_3() -> None:
    """Three confirmed historical eruptions: 1998, 2011, 2015."""
    assert len(AXIAL_ERUPTIONS) == 3


def test_inflation_phases_count_4() -> None:
    """Four inflation phases: pre-1998, 1998-2011, 2011-2015, post-2015."""
    assert len(INFLATION_PHASES) == 4


def test_forecasts_count_2() -> None:
    """Two published Chadwick-Nooner forecasts."""
    assert len(CHADWICK_FORECASTS) == 2


def test_eruption_names_unique() -> None:
    names = [e.name for e in AXIAL_ERUPTIONS]
    assert len(names) == len(set(names))


def test_sources_count() -> None:
    assert len(SOURCES) == 10


def test_catalog_reference_year() -> None:
    """Catalog reference year is 2026 (the cutoff for HIT/MISS/OPEN
    classification of forecast outcomes)."""
    assert CATALOG_REFERENCE_YEAR == 2026


# ──────────────────────────────────────────────────────────────────────
# Eruption history (canonical years + ordering)
# ──────────────────────────────────────────────────────────────────────


def test_1998_eruption_year() -> None:
    by = {e.name: e for e in AXIAL_ERUPTIONS}
    assert by["axial_1998"].year == 1998


def test_2011_eruption_year() -> None:
    by = {e.name: e for e in AXIAL_ERUPTIONS}
    assert by["axial_2011"].year == 2011


def test_2015_eruption_year() -> None:
    by = {e.name: e for e in AXIAL_ERUPTIONS}
    assert by["axial_2015"].year == 2015


def test_eruptions_are_chronological() -> None:
    """Eruption JDs increase monotonically."""
    sorted_jds = [e.julian_date for e in
                  sorted(AXIAL_ERUPTIONS, key=lambda e: e.julian_date)]
    assert sorted_jds == sorted(sorted_jds)


def test_caldera_floor_subsidence_in_metres_scale() -> None:
    """Each eruption's caldera-floor deflation is in the 2-4 m range
    (Caress 2012 / Chadwick 2016 calibration)."""
    for e in AXIAL_ERUPTIONS:
        assert 1.0 < e.caldera_floor_subsidence_m < 5.0


# ──────────────────────────────────────────────────────────────────────
# Caldera + summit geometry (Caress 2012 bathymetry)
# ──────────────────────────────────────────────────────────────────────


def test_summit_in_juan_de_fuca_region() -> None:
    """Summit at ~46N, ~130W (Juan de Fuca Ridge axis)."""
    assert 45.0 < AXIAL_SUMMIT_LAT_DEG < 47.0
    assert -131.0 < AXIAL_SUMMIT_LON_DEG < -129.0


def test_summit_depth_around_1500m() -> None:
    """Caldera floor sits ~1500 m below sea surface (Caress 2012)."""
    assert 1400.0 < AXIAL_SUMMIT_DEPTH_M < 1600.0


def test_caldera_dimensions() -> None:
    """Caldera ~3 x 8 km."""
    assert 2.0 < AXIAL_CALDERA_WIDTH_KM < 5.0
    assert 6.0 < AXIAL_CALDERA_LENGTH_KM < 10.0


def test_geodetic_trigger_threshold() -> None:
    """Chadwick 2016 inflation-trigger threshold ~0.5 m."""
    assert 0.1 < AXIAL_GEODETIC_TRIGGER_M < 1.0


# ──────────────────────────────────────────────────────────────────────
# Inflation phases (rate timeline)
# ──────────────────────────────────────────────────────────────────────


def test_2011_to_2015_phase_was_fastest() -> None:
    """The 2011-2015 inflation phase had the fastest rate (~70 cm/yr)
    -- nearly 5x the prior cycle's rate. This is why the inter-
    eruption interval was only 4 yr instead of 13."""
    by = {p.name: p for p in INFLATION_PHASES}
    fastest = max(
        INFLATION_PHASES,
        key=lambda p: p.mean_inflation_rate_cm_per_yr,
    )
    assert fastest.name == "phase_2011_to_2015"
    assert fastest.mean_inflation_rate_cm_per_yr >= 50.0


def test_post_2015_phase_slower_than_2011_to_2015() -> None:
    """Post-2015 inflation rate < 2011-2015 reference rate. THIS is
    the rate-decay that broke the Chadwick-Nooner constant-rate
    extrapolation underlying the 2024-2025 forecast."""
    by = {p.name: p for p in INFLATION_PHASES}
    assert (by["phase_post_2015"].mean_inflation_rate_cm_per_yr
            < by["phase_2011_to_2015"].mean_inflation_rate_cm_per_yr)


# ──────────────────────────────────────────────────────────────────────
# Forecast track-record (THE headline)
# ──────────────────────────────────────────────────────────────────────


def test_2015_forecast_was_a_hit() -> None:
    """The Chadwick 2016 forecast for the 2015 eruption was a HIT
    (eruption occurred within the published target window)."""
    by = {f.name: f for f in CHADWICK_FORECASTS}
    assert by["forecast_2015_eruption"].outcome == "HIT"


def test_2024_2025_forecast_was_a_miss() -> None:
    """The 2024-2025 Chadwick-Nooner forecast window was a MISS as
    of the catalog reference year (2026): the post-2015 inflation
    rate slowed below the 2011-2015 reference, breaking the
    constant-rate extrapolation."""
    by = {f.name: f for f in CHADWICK_FORECASTS}
    assert by["forecast_2024_2025_window"].outcome == "MISS"


def test_track_record_is_one_hit_one_miss() -> None:
    """The Chadwick-Nooner methodology has a single-body track record
    of one HIT and one MISS on Axial Seamount as of 2026 -- the
    project's first explicit prediction-reliability ship."""
    sig = get_axial_inflation_cycle_signature()
    tr = sig["forecast_track_record"]
    assert tr["n_hits"] == 1
    assert tr["n_misses"] == 1


# ──────────────────────────────────────────────────────────────────────
# Spectral signature (the v0.24.2 cousin)
# ──────────────────────────────────────────────────────────────────────


def test_inter_eruption_intervals_count() -> None:
    """3 eruptions -> 2 intervals."""
    sig = get_axial_inflation_cycle_signature()
    assert sig["n_intervals"] == 2


def test_first_interval_is_13_years() -> None:
    """1998 -> 2011 ~ 13 years."""
    sig = get_axial_inflation_cycle_signature()
    first = sig["intervals"][0]
    assert first["from"] == "axial_1998"
    assert first["to"] == "axial_2011"
    assert 12.5 < first["interval_years"] < 14.0


def test_second_interval_is_4_years() -> None:
    """2011 -> 2015 ~ 4 years."""
    sig = get_axial_inflation_cycle_signature()
    second = sig["intervals"][1]
    assert second["from"] == "axial_2011"
    assert second["to"] == "axial_2015"
    assert 3.5 < second["interval_years"] < 4.5


def test_rate_period_products_have_two_entries() -> None:
    """Two intervals -> two rate-period products."""
    sig = get_axial_inflation_cycle_signature()
    assert len(sig["rate_period_products"]) == 2


def test_rate_period_product_spread_nonzero() -> None:
    """The rate-period product is NOT exactly conserved across the
    two cycles -- the spread is the signature that the Chadwick-
    Nooner constant-rate-times-period observable is only
    approximately constant. This is exactly the v0.24.2 spectral-
    stability fragility motif."""
    sig = get_axial_inflation_cycle_signature()
    assert sig["rate_period_product_spread_cm"] > 50.0


def test_methodology_observation_mentions_v0_24_2_parallel() -> None:
    """The interpretation field must call out the v0.24.2 Mars
    spectral-stability cousin -- this is the cross-channel
    headline."""
    sig = get_axial_inflation_cycle_signature()
    obs = sig["methodology_observation"].lower()
    assert "decade" in obs
    assert "stability" in obs or "stable" in obs
    assert "mars" in obs


# ──────────────────────────────────────────────────────────────────────
# Citation discipline
# ──────────────────────────────────────────────────────────────────────


def test_every_eruption_source_key_resolves() -> None:
    for e in AXIAL_ERUPTIONS:
        assert e.source_key in SOURCES


def test_every_inflation_phase_source_key_resolves() -> None:
    for p in INFLATION_PHASES:
        assert p.source_key in SOURCES


def test_every_forecast_source_key_resolves() -> None:
    for f in CHADWICK_FORECASTS:
        assert f.source_key in SOURCES


def test_canonical_papers_in_sources() -> None:
    """Chadwick 2016 + Caress 2012 + Wilcock 2016 + Nooner-Chadwick
    2016 + Dziak-Fox 1999 must all be cited."""
    for ref in (
        "chadwick_2016", "caress_2012", "wilcock_2016",
        "nooner_chadwick_2016", "dziak_fox_1999",
    ):
        assert ref in SOURCES


# ──────────────────────────────────────────────────────────────────────
# Pythonic API
# ──────────────────────────────────────────────────────────────────────


def test_get_axial_seamount_chronology_smoke() -> None:
    r = get_axial_seamount_chronology()
    assert r["ok"] is True
    assert r["n_eruptions"] == 3


def test_get_axial_inflation_cycle_signature_smoke() -> None:
    r = get_axial_inflation_cycle_signature()
    assert r["ok"] is True
    assert r["n_intervals"] == 2
    assert r["forecast_track_record"]["n_hits"] >= 1
    assert r["forecast_track_record"]["n_misses"] >= 1


def test_list_axial_seamount_smoke() -> None:
    r = list_axial_seamount()
    assert r["ok"] is True
    assert r["n_eruptions"] == 3
    assert r["n_inflation_phases"] == 4
    assert r["n_forecasts"] == 2
    assert r["n_sources"] == 10


# ──────────────────────────────────────────────────────────────────────
# Bridge surfaces
# ──────────────────────────────────────────────────────────────────────


def test_bridge_get_axial_seamount_chronology() -> None:
    r = bridge.get_axial_seamount_chronology()
    assert r["ok"] is True
    assert r["n_eruptions"] == 3


def test_bridge_get_axial_inflation_cycle_signature() -> None:
    r = bridge.get_axial_inflation_cycle_signature()
    assert r["ok"] is True
    assert r["n_intervals"] == 2


def test_bridge_list_axial_seamount() -> None:
    r = bridge.list_axial_seamount()
    assert r["ok"] is True
    assert r["n_eruptions"] == 3


# ──────────────────────────────────────────────────────────────────────
# CLI surfaces
# ──────────────────────────────────────────────────────────────────────


def test_cli_axial_seamount_chronology_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["axial-seamount-chronology"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_eruptions"] == 3


def test_cli_axial_inflation_cycle_signature_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["axial-inflation-cycle-signature"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["forecast_track_record"]["n_misses"] >= 1


def test_cli_axial_seamount_full_smoke() -> None:
    import io as _io
    import json as _json
    from contextlib import redirect_stdout

    from ephemerides_spectral.cli import main as cli_main

    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = cli_main(["axial-seamount-full"])
    assert rc == 0
    payload = _json.loads(buf.getvalue())
    assert payload["n_eruptions"] == 3


def test_cli_axial_help() -> None:
    """All v0.24.8 CLI subcommands render --help cleanly."""
    from ephemerides_spectral.cli import main as cli_main

    for cmd in (
        "axial-seamount-chronology",
        "axial-inflation-cycle-signature",
        "axial-seamount-full",
    ):
        with pytest.raises(SystemExit) as exc_info:
            cli_main([cmd, "--help"])
        assert exc_info.value.code == 0
