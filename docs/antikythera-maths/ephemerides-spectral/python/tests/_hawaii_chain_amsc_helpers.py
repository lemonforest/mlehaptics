"""Shared helpers for the v0.27.0 phase A AMSC backfill of the
v0.24.5 Hawaiian-Emperor Chain Spectral Catalogue.

Mirrors prior phase A helpers (mercury / luna / mars / sun /
toroidal). Single row_type ('seamount'). Introduces the `nodoi:`
DOI-prefix convention for pre-DOI book chapters and observatory
compilations.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from ephemerides_spectral._research.hawaii_chain_data import (
    HAWAIIAN_EMPEROR_SEAMOUNTS,
)


SOURCE_KEY_PROVENANCE: Dict[str, Dict[str, Any]] = {
    "sharp_clague_2006": {
        "source_doi": "10.1126/science.1128489",
        "source_published_date": "2006-09-01",
        "source_version": None,
    },
    "duncan_keller_2004": {
        "source_doi": "10.1029/2004GC000704",
        "source_published_date": "2004-08",
        "source_version": "ODP Leg 197",
    },
    "duncan_clague_1985": {
        "source_doi": "nodoi:duncan_clague_1985_pacific_plate_motion",
        "source_published_date": "1985",
        "source_version": "Plenum Ocean Basins and Margins vol 7A",
    },
    "keller_1995_meiji": {
        "source_doi": "nodoi:keller_1995_odp_leg145_meiji",
        "source_published_date": "1995",
        "source_version": "ODP Leg 145",
    },
    "o_connor_2013": {
        "source_doi": "10.1002/ggge.20267",
        "source_published_date": "2013-11",
        "source_version": None,
    },
    "clague_dalrymple_1989": {
        "source_doi": "nodoi:clague_dalrymple_1989_geology_north_america",
        "source_published_date": "1989",
        "source_version": "GSA Geology of North America vol N",
    },
    "garcia_2010": {
        "source_doi": "10.1093/petrology/egq027",
        "source_published_date": "2010-07",
        "source_version": None,
    },
    "clague_2010": {
        "source_doi": "nodoi:usgs_hvo_clague_2010_compilation",
        "source_published_date": "2010",
        "source_version": "USGS HVO compilation",
    },
}

ENTERED_LOCALLY_AT: str = "2026-05-09"


def seamount_to_amsc_dict(s) -> Dict[str, Any]:
    prov = SOURCE_KEY_PROVENANCE[s.source_key]
    return {
        "name": s.name,
        "row_type": "seamount",
        "age_myr": s.age_myr,
        "age_uncertainty_myr": s.age_uncertainty_myr,
        "latitude_deg": s.latitude_deg,
        "longitude_deg": s.longitude_deg,
        "arc": s.arc,
        "precision_flag": s.precision_flag,
        "notes": s.notes,
        "source_doi": prov["source_doi"],
        "source_published_date": prov["source_published_date"],
        "entered_locally_at": ENTERED_LOCALLY_AT,
        "source_version": prov["source_version"],
    }


def hand_coded_rows_in_amsc_shape() -> List[Dict[str, Any]]:
    return [seamount_to_amsc_dict(s) for s in HAWAIIAN_EMPEROR_SEAMOUNTS]


def emit_ndjson() -> str:
    rows = hand_coded_rows_in_amsc_shape()
    return "\n".join(
        json.dumps(row, ensure_ascii=False, sort_keys=False)
        for row in rows
    ) + "\n"
