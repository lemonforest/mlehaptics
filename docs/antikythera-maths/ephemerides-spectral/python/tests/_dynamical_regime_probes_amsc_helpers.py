"""Shared helpers for the v0.27.0 phase A AMSC backfill of the
v0.24.10 Sol Dynamical-Regime Out-of-Sample Probe Roster.

Single row_type ('regime_probe'). Each probe carries a direct paper
DOI (no v024_N indirection). Mixed real-DOI / isbn: catalogue —
Murray-Dermott 1999 is a textbook (ISBN-keyed via the project's
convention).
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from ephemerides_spectral._research.dynamical_regime_probes_data import (
    REGIME_PROBES,
)


SOURCE_KEY_PROVENANCE: Dict[str, Dict[str, Any]] = {
    "pierce_morgan_1992": {
        "source_doi": "10.1130/MEM179-p1",
        "source_published_date": "1992",
        "source_version": "GSA Memoir 179",
    },
    "courtillot_1986": {
        "source_doi": "10.1016/0012-821X(86)90118-4",
        "source_published_date": "1986",
        "source_version": None,
    },
    "stern_1992": {
        "source_doi": "10.1146/annurev.aa.30.090192.001153",
        "source_published_date": "1992-09",
        "source_version": None,
    },
    "murray_dermott_1999": {
        # Murray-Dermott 1999 *Solar System Dynamics* — Cambridge
        # University Press textbook. ISBN-keyed via the project's
        # convention (matches Mercury/Luna helpers).
        "source_doi": "isbn:978-0521575973",
        "source_published_date": "1999-02-13",
        "source_version": "1st edition",
    },
    "peale_cassen_reynolds_1979": {
        "source_doi": "10.1126/science.203.4383.892",
        "source_published_date": "1979-03-02",
        "source_version": None,
    },
    "bills_2005": {
        "source_doi": "10.1029/2004JE002376",
        "source_published_date": "2005-07",
        "source_version": None,
    },
    "park_2016": {
        "source_doi": "10.1038/nature18955",
        "source_published_date": "2016-08-04",
        "source_version": None,
    },
    "kjeldsen_2005": {
        "source_doi": "10.1086/497530",
        "source_published_date": "2005-12-20",
        "source_version": None,
    },
    "russell_2012": {
        "source_doi": "10.1126/science.1219381",
        "source_published_date": "2012-05-11",
        "source_version": None,
    },
    "kaspi_beloborodov_2017": {
        "source_doi": "10.1146/annurev-astro-081915-023329",
        "source_published_date": "2017-08",
        "source_version": None,
    },
}

ENTERED_LOCALLY_AT: str = "2026-05-09"


def probe_to_amsc_dict(p) -> Dict[str, Any]:
    prov = SOURCE_KEY_PROVENANCE[p.source_key]
    return {
        "name": p.name,
        "row_type": "regime_probe",
        "description": p.description,
        "time_scale_log_s": p.time_scale_log_s,
        "spatial_scale_log_km": p.spatial_scale_log_km,
        "stability_index": p.stability_index,
        "has_commensurability": p.has_commensurability,
        "prediction_track_signal": p.prediction_track_signal,
        "dimensionality": p.dimensionality,
        "forcing_class_index": p.forcing_class_index,
        "expected_regime": p.expected_regime,
        "ood_expected": p.ood_expected,
        "precision_flag": p.precision_flag,
        "notes": p.notes,
        "source_doi": prov["source_doi"],
        "source_published_date": prov["source_published_date"],
        "entered_locally_at": ENTERED_LOCALLY_AT,
        "source_version": prov["source_version"],
    }


def hand_coded_rows_in_amsc_shape() -> List[Dict[str, Any]]:
    return [probe_to_amsc_dict(p) for p in REGIME_PROBES]


def emit_ndjson() -> str:
    rows = hand_coded_rows_in_amsc_shape()
    return "\n".join(
        json.dumps(row, ensure_ascii=False, sort_keys=False)
        for row in rows
    ) + "\n"
