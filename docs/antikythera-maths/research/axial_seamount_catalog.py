"""Sol Axial Seamount Eruption Chronology Catalog — query surface
for the v0.24.8 ship (temporal-spectrum eruption-cycle observable
on a real-time-monitored submarine volcano; the prediction-track-
record analogue of v0.24.5 Hawaii / v0.24.7 Mars Tharsis spatial
ships).

Promotes the v0.24.8 architectural commitment from research
notebook §17.7 to a stable ship surface — the **first time** the
project ships a *temporal-spectrum* observable on a single sub-
system rather than a spatial graph or per-body action-angle roster.

Three bridge surfaces:

* :func:`get_axial_seamount_chronology` — full eruption record +
  inflation-phase rates + Chadwick forecast track-record.
* :func:`get_axial_inflation_cycle_signature` — THE headline
  closure: quasi-periodic mean inter-eruption interval +
  prediction track-record summary (1 HIT + 1 MISS as of the
  catalog reference date) + the v0.24.2-style spectral-stability
  failure-mode signature.
* :func:`list_axial_seamount` — full enumeration with citations.

Cross-channel reach: same v0.24.x methodology arc as v0.24.0-
v0.24.7, but applied to a temporal observable (eruption cycle
period) rather than a spatial graph. The "missed 2024-2025
prediction" is the v0.24.2-style spectral-stability failure mode
applied at decade / cm-per-year scale instead of Gyr / arcsec-
per-year.

Reference: research notebook §17.7.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .axial_seamount_data import (
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
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
    AxialEruption,
    ChadwickForecast,
    InflationPhase,
)

# ---- Catalog reference date (2026-05-07; matches release date) ------
# The "as of" cutoff for declaring forecast outcomes (HIT / MISS / OPEN).
# Documented inside the data module rather than recomputed at query
# time so the catalog is reproducible.
CATALOG_REFERENCE_YEAR: int = 2026


def _eruption_to_dict(e: AxialEruption) -> Dict[str, Any]:
    return {
        "name": e.name,
        "year": e.year,
        "month": e.month,
        "approximate_day": e.approximate_day,
        "julian_date": e.julian_date,
        "caldera_floor_subsidence_m": e.caldera_floor_subsidence_m,
        "notes": e.notes,
        "source_key": e.source_key,
        "precision_flag": e.precision_flag,
    }


def _inflation_phase_to_dict(p: InflationPhase) -> Dict[str, Any]:
    return {
        "name": p.name,
        "start_year": p.start_year,
        "end_year": p.end_year,
        "duration_yr": p.end_year - p.start_year,
        "mean_inflation_rate_cm_per_yr": p.mean_inflation_rate_cm_per_yr,
        "notes": p.notes,
        "source_key": p.source_key,
        "precision_flag": p.precision_flag,
    }


def _forecast_to_dict(f: ChadwickForecast) -> Dict[str, Any]:
    return {
        "name": f.name,
        "issued_year": f.issued_year,
        "target_start_year": f.target_start_year,
        "target_end_year": f.target_end_year,
        "outcome": f.outcome,
        "notes": f.notes,
        "source_key": f.source_key,
    }


def _inter_eruption_intervals_yr() -> List[Dict[str, Any]]:
    """Compute inter-eruption intervals in years from JD differences."""
    sorted_eruptions = sorted(AXIAL_ERUPTIONS, key=lambda e: e.julian_date)
    intervals: List[Dict[str, Any]] = []
    for prev, curr in zip(sorted_eruptions[:-1], sorted_eruptions[1:]):
        dt_days = curr.julian_date - prev.julian_date
        dt_yr = dt_days / 365.25
        intervals.append({
            "from": prev.name,
            "to": curr.name,
            "interval_days": float(dt_days),
            "interval_years": float(dt_yr),
        })
    return intervals


def get_axial_seamount_chronology() -> Dict[str, Any]:
    """Axial Seamount eruption chronology + inflation phases +
    Chadwick forecast track-record.

    Each eruption carries:

    * ``name``, ``year``, ``month``, ``approximate_day``,
      ``julian_date``, ``caldera_floor_subsidence_m``, ``source_key``.

    Each inflation phase carries:

    * ``name``, ``start_year``, ``end_year``, ``duration_yr``,
      ``mean_inflation_rate_cm_per_yr``, ``source_key``.

    Each Chadwick forecast carries:

    * ``name``, ``issued_year``, ``target_start_year``,
      ``target_end_year``, ``outcome`` (HIT / MISS / OPEN),
      ``source_key``.

    Cross-strand observation: the methodology framework (Chadwick
    2016 inflation-rate-controlled trigger) has both **HIT** the
    2015 eruption and **MISS** the 2024-2025 forecast window on
    the same body. This is the project's first *single-body*
    track record of spectral prediction succeeding under one
    cycle and failing under the next — the v0.24.2 Mars
    chaotic-mode signature applied at decade timescales.

    Returns
    -------
    dict
        ``{ok, n_eruptions, summit, caldera, geodetic_trigger_m,
        eruptions: [...], inflation_phases: [...], forecasts: [...]}``.
    """
    return {
        "ok": True,
        "n_eruptions": len(AXIAL_ERUPTIONS),
        "summit": {
            "latitude_deg": AXIAL_SUMMIT_LAT_DEG,
            "longitude_deg": AXIAL_SUMMIT_LON_DEG,
            "depth_below_sea_surface_m": AXIAL_SUMMIT_DEPTH_M,
        },
        "caldera": {
            "length_km": AXIAL_CALDERA_LENGTH_KM,
            "width_km": AXIAL_CALDERA_WIDTH_KM,
        },
        "geodetic_trigger_m": AXIAL_GEODETIC_TRIGGER_M,
        "catalog_reference_year": CATALOG_REFERENCE_YEAR,
        "eruptions": [_eruption_to_dict(e) for e in AXIAL_ERUPTIONS],
        "inflation_phases": [
            _inflation_phase_to_dict(p) for p in INFLATION_PHASES
        ],
        "forecasts": [_forecast_to_dict(f) for f in CHADWICK_FORECASTS],
    }


def get_axial_inflation_cycle_signature() -> Dict[str, Any]:
    """The Axial Seamount inflation-cycle signature — THE headline
    of v0.24.8.

    **Two complementary spectral observations**:

    **(1) Inter-eruption interval distribution** — the 1998-2011
    cycle ran ~13.2 yr at ~15 cm/yr inflation; the 2011-2015 cycle
    ran ~4.1 yr at ~70 cm/yr. The intervals are NOT constant; the
    cycle period adapts to the inflation rate. The **rate-period
    product** (inflation rate x interval) is the conserved
    observable that the Chadwick-Nooner methodology assumes
    constant — empirically validated for 1998-2015 by the 2015
    successful forecast.

    **(2) Methodology track-record asymmetry** — the same Chadwick-
    Nooner methodology that successfully predicted the 2015
    eruption (1 HIT) has missed the 2024-2025 forecast window
    (1 MISS as of catalog reference date 2026). The miss arises
    from **post-2015 inflation slowing below the 2011-2015
    reference** — the rate-period-product assumption is broken
    when the rate itself is non-stationary. This is the **v0.24.2
    Mars-style spectral-stability failure mode applied at decade
    timescales**: a quasi-periodic mode that is Diophantine-stable
    over one observation window and small-denominator-fragile
    outside it.

    Cross-channel positioning: where v0.24.5 Hawaii (with plate
    tectonics) -> spatial trajectory and v0.24.7 Mars Tharsis
    (no plate tectonics) -> spatial cogenetic family, v0.24.8
    Axial Seamount (mid-ocean-ridge hotspot) -> **temporal quasi-
    periodic cycle with measurable methodology track-record**.
    Same v0.24.x algebraic discipline; different observable axis;
    the **first explicit prediction-reliability ship**.

    Returns
    -------
    dict
        ``{ok, n_eruptions, n_intervals, intervals: [...],
        mean_interval_years, n_forecasts, forecast_track_record:
        {hits, misses, opens}, methodology_observation, ...}``.
    """
    intervals = _inter_eruption_intervals_yr()
    mean_interval_yr: float = (
        sum(i["interval_years"] for i in intervals) / max(len(intervals), 1)
        if intervals else float("nan")
    )

    hits = [f for f in CHADWICK_FORECASTS if f.outcome == "HIT"]
    misses = [f for f in CHADWICK_FORECASTS if f.outcome == "MISS"]
    opens = [f for f in CHADWICK_FORECASTS if f.outcome == "OPEN"]

    # Compute the rate-period product across the OOI-instrumented era,
    # which is the Chadwick-Nooner conserved observable.
    rate_period_products: List[Dict[str, Any]] = []
    phase_by_name = {p.name: p for p in INFLATION_PHASES}
    interval_to_phase = [
        ("axial_1998->axial_2011", "phase_1998_to_2011"),
        ("axial_2011->axial_2015", "phase_2011_to_2015"),
    ]
    for interval, (label, phase_name) in zip(intervals, interval_to_phase):
        if phase_name in phase_by_name:
            phase = phase_by_name[phase_name]
            product_cm = (
                phase.mean_inflation_rate_cm_per_yr
                * interval["interval_years"]
            )
            rate_period_products.append({
                "interval_label": label,
                "inflation_rate_cm_per_yr":
                    phase.mean_inflation_rate_cm_per_yr,
                "interval_years": interval["interval_years"],
                "rate_period_product_cm": product_cm,
            })

    # Spread of the rate-period product across cycles -- if the
    # Chadwick-Nooner conservation hypothesis is right, this should
    # be tight; large spread signals trouble for constant-rate
    # extrapolation.
    if rate_period_products:
        rpp_values = [r["rate_period_product_cm"] for r in rate_period_products]
        rpp_mean = sum(rpp_values) / len(rpp_values)
        rpp_spread = max(rpp_values) - min(rpp_values)
    else:
        rpp_mean = float("nan")
        rpp_spread = float("nan")

    return {
        "ok": True,
        "n_eruptions": len(AXIAL_ERUPTIONS),
        "n_intervals": len(intervals),
        "intervals": intervals,
        "mean_interval_years": mean_interval_yr,
        "rate_period_products": rate_period_products,
        "rate_period_product_mean_cm": rpp_mean,
        "rate_period_product_spread_cm": rpp_spread,
        "n_forecasts": len(CHADWICK_FORECASTS),
        "forecast_track_record": {
            "n_hits": len(hits),
            "n_misses": len(misses),
            "n_opens": len(opens),
            "hits": [_forecast_to_dict(f) for f in hits],
            "misses": [_forecast_to_dict(f) for f in misses],
            "opens": [_forecast_to_dict(f) for f in opens],
        },
        "methodology_observation": (
            "The Chadwick-Nooner inflation-rate-controlled trigger "
            "framework has a single-body track record on Axial "
            "Seamount of one HIT (2015 eruption forecast at 6-month "
            "lead) and one MISS (2024-2025 forecast window not met "
            "as of catalog reference year 2026). The miss arises "
            "from post-2015 inflation slowing below the 2011-2015 "
            "reference, breaking the constant-rate extrapolation "
            "assumption. This is the v0.24.2-style spectral-"
            "stability failure mode applied at decade timescales: "
            "a quasi-periodic dynamical mode that is Diophantine-"
            "stable over one observation window and small-"
            "denominator-fragile outside it. Same algebraic "
            "structure as Mars's secular-resonance obliquity "
            "chaos, on a wildly different observational scale."
        ),
    }


def list_axial_seamount() -> Dict[str, Any]:
    """Full enumeration of Axial Seamount catalog data + citations."""
    return {
        "ok": True,
        "n_eruptions": len(AXIAL_ERUPTIONS),
        "n_inflation_phases": len(INFLATION_PHASES),
        "n_forecasts": len(CHADWICK_FORECASTS),
        "n_sources": len(SOURCES),
        "eruptions": [_eruption_to_dict(e) for e in AXIAL_ERUPTIONS],
        "inflation_phases": [
            _inflation_phase_to_dict(p) for p in INFLATION_PHASES
        ],
        "forecasts": [_forecast_to_dict(f) for f in CHADWICK_FORECASTS],
    }


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "CATALOG_REFERENCE_YEAR",
    "AXIAL_ERUPTIONS",
    "INFLATION_PHASES",
    "CHADWICK_FORECASTS",
    "SOURCES",
    "AxialEruption",
    "InflationPhase",
    "ChadwickForecast",
    "get_axial_seamount_chronology",
    "get_axial_inflation_cycle_signature",
    "list_axial_seamount",
]
