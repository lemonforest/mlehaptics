"""Shared helpers for the v0.27.0 phase A AMSC backfill of the
v0.24.8 Axial Seamount Eruption Chronology Catalogue.

Mirrors prior phase A helpers. Multi-row-type catalogue: 3 row types
(eruption / inflation_phase / forecast). The post-2015 follow-up
analyses (conference proceedings + OOI Cabled Array status updates
that document the post-2015 inflation-rate slowing + 2024-2025
forecast MISS) carry a `nodoi:` prefix because they aren't
Crossref-indexed publications.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from ephemerides_spectral._research.axial_seamount_data import (
    AXIAL_ERUPTIONS,
    INFLATION_PHASES,
    CHADWICK_FORECASTS,
)


SOURCE_KEY_PROVENANCE: Dict[str, Dict[str, Any]] = {
    "dziak_fox_1999": {
        "source_doi": "10.1029/1999GL002327",
        "source_published_date": "1999-12-01",
        "source_version": None,
    },
    "caress_2012": {
        "source_doi": "10.1038/ngeo1496",
        "source_published_date": "2012-07",
        "source_version": None,
    },
    "chadwick_2016": {
        "source_doi": "10.1126/science.aah4666",
        "source_published_date": "2016-12-16",
        "source_version": None,
    },
    "nooner_chadwick_2009": {
        "source_doi": "10.1029/2008GC002315",
        "source_published_date": "2009-02",
        "source_version": None,
    },
    "nooner_chadwick_2016": {
        # Companion paper to Chadwick 2016 in the same Science issue
        # (354:1399-1403). The hand-coded SOURCES dict cited the
        # 10.1126/science.aah4666 family; this entry uses the same
        # canonical Chadwick-Nooner-2016 DOI for byte-stable agreement
        # with the hand-coded module's source_key labelling.
        "source_doi": "10.1126/science.aah4666",
        "source_published_date": "2016-12-16",
        "source_version": None,
    },
    "nooner_chadwick_post_2015": {
        # Post-2015 follow-up analyses are conference proceedings +
        # OOI Cabled Array status updates — not a Crossref-indexed
        # publication. The `nodoi:` prefix marks this following the
        # PR #312 Hawaii convention.
        "source_doi": "nodoi:nooner_chadwick_post_2015_ooi_followup",
        "source_published_date": "2024",
        "source_version": "OOI Cabled Array follow-up",
    },
}

ENTERED_LOCALLY_AT: str = "2026-05-09"


def eruption_to_amsc_dict(e) -> Dict[str, Any]:
    prov = SOURCE_KEY_PROVENANCE[e.source_key]
    return {
        "name": e.name,
        "row_type": "eruption",
        "year": e.year,
        "month": e.month,
        "approximate_day": e.approximate_day,
        "julian_date": e.julian_date,
        "caldera_floor_subsidence_m": e.caldera_floor_subsidence_m,
        "start_year": None,
        "end_year": None,
        "mean_inflation_rate_cm_per_yr": None,
        "issued_year": None,
        "target_start_year": None,
        "target_end_year": None,
        "outcome": None,
        "precision_flag": e.precision_flag,
        "notes": e.notes,
        "source_doi": prov["source_doi"],
        "source_published_date": prov["source_published_date"],
        "entered_locally_at": ENTERED_LOCALLY_AT,
        "source_version": prov["source_version"],
    }


def inflation_phase_to_amsc_dict(p) -> Dict[str, Any]:
    prov = SOURCE_KEY_PROVENANCE[p.source_key]
    return {
        "name": p.name,
        "row_type": "inflation_phase",
        "year": None,
        "month": None,
        "approximate_day": None,
        "julian_date": None,
        "caldera_floor_subsidence_m": None,
        "start_year": p.start_year,
        "end_year": p.end_year,
        "mean_inflation_rate_cm_per_yr": p.mean_inflation_rate_cm_per_yr,
        "issued_year": None,
        "target_start_year": None,
        "target_end_year": None,
        "outcome": None,
        "precision_flag": p.precision_flag,
        "notes": p.notes,
        "source_doi": prov["source_doi"],
        "source_published_date": prov["source_published_date"],
        "entered_locally_at": ENTERED_LOCALLY_AT,
        "source_version": prov["source_version"],
    }


def forecast_to_amsc_dict(f) -> Dict[str, Any]:
    prov = SOURCE_KEY_PROVENANCE[f.source_key]
    return {
        "name": f.name,
        "row_type": "forecast",
        "year": None,
        "month": None,
        "approximate_day": None,
        "julian_date": None,
        "caldera_floor_subsidence_m": None,
        "start_year": None,
        "end_year": None,
        "mean_inflation_rate_cm_per_yr": None,
        "issued_year": f.issued_year,
        "target_start_year": f.target_start_year,
        "target_end_year": f.target_end_year,
        "outcome": f.outcome,
        # ChadwickForecast doesn't carry a precision_flag; pin "high"
        # for HIT and "medium" for MISS to match the level of
        # observational confidence in each outcome.
        "precision_flag": "high" if f.outcome == "HIT" else "medium",
        "notes": f.notes,
        "source_doi": prov["source_doi"],
        "source_published_date": prov["source_published_date"],
        "entered_locally_at": ENTERED_LOCALLY_AT,
        "source_version": prov["source_version"],
    }


def hand_coded_rows_in_amsc_shape() -> List[Dict[str, Any]]:
    """All hand-coded rows converted to AMSC-shape dicts: eruptions
    first, then inflation phases, then forecasts."""
    return (
        [eruption_to_amsc_dict(e) for e in AXIAL_ERUPTIONS]
        + [inflation_phase_to_amsc_dict(p) for p in INFLATION_PHASES]
        + [forecast_to_amsc_dict(f) for f in CHADWICK_FORECASTS]
    )


def emit_ndjson() -> str:
    rows = hand_coded_rows_in_amsc_shape()
    return "\n".join(
        json.dumps(row, ensure_ascii=False, sort_keys=False)
        for row in rows
    ) + "\n"
