"""Shared helpers for the v0.27.0 phase A AMSC backfill of the
v0.24.7 Mars Tharsis Volcanic Chain Catalogue.

Mirrors prior phase A helpers (mercury / luna / mars / sun /
toroidal / hawaii_chain / yarkovsky_yorp). Single row_type
('tharsis_volcano'). All source DOIs are real Crossref-indexed
papers — no nodoi: / historical: prefixes needed.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from ephemerides_spectral._research.mars_tharsis_data import (
    MARS_THARSIS_VOLCANOES,
)


SOURCE_KEY_PROVENANCE: Dict[str, Dict[str, Any]] = {
    "hartmann_neukum_2001": {
        "source_doi": "10.1023/A:1011945222010",
        "source_published_date": "2001",
        "source_version": None,
    },
    "hartmann_2005": {
        "source_doi": "10.1016/j.icarus.2004.11.023",
        "source_published_date": "2005-04",
        "source_version": None,
    },
    "werner_2009": {
        "source_doi": "10.1016/j.icarus.2008.12.019",
        "source_published_date": "2009-05",
        "source_version": None,
    },
    "plescia_2004": {
        "source_doi": "10.1029/2002JE002031",
        "source_published_date": "2004-03",
        "source_version": None,
    },
}

ENTERED_LOCALLY_AT: str = "2026-05-09"


def volcano_to_amsc_dict(v) -> Dict[str, Any]:
    prov = SOURCE_KEY_PROVENANCE[v.source_key]
    return {
        "name": v.name,
        "row_type": "tharsis_volcano",
        "age_myr": v.age_myr,
        "age_uncertainty_myr": v.age_uncertainty_myr,
        "latitude_deg": v.latitude_deg,
        "longitude_deg": v.longitude_deg,
        "summit_elevation_m": v.summit_elevation_m,
        "edifice_diameter_km": v.edifice_diameter_km,
        "role": v.role,
        "precision_flag": v.precision_flag,
        "notes": v.notes,
        "source_doi": prov["source_doi"],
        "source_published_date": prov["source_published_date"],
        "entered_locally_at": ENTERED_LOCALLY_AT,
        "source_version": prov["source_version"],
    }


def hand_coded_rows_in_amsc_shape() -> List[Dict[str, Any]]:
    return [volcano_to_amsc_dict(v) for v in MARS_THARSIS_VOLCANOES]


def emit_ndjson() -> str:
    rows = hand_coded_rows_in_amsc_shape()
    return "\n".join(
        json.dumps(row, ensure_ascii=False, sort_keys=False)
        for row in rows
    ) + "\n"
