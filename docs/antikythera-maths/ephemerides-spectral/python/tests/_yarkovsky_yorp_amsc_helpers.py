"""Shared helpers for the v0.27.0 phase A AMSC backfill of the
v0.24.6 Sol Yarkovsky/YORP Catalogue.

Mirrors prior phase A helpers (mercury / luna / mars / sun /
toroidal / hawaii_chain). Single row_type ('yarkovsky_yorp_entry').
All source DOIs are real Crossref-indexed papers — no nodoi: /
historical: prefixes needed for this catalogue.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from ephemerides_spectral._research.yarkovsky_yorp_data import (
    YARKOVSKY_YORP_ENTRIES,
)


SOURCE_KEY_PROVENANCE: Dict[str, Dict[str, Any]] = {
    "farnocchia_2013": {
        "source_doi": "10.1016/j.icarus.2013.02.004",
        "source_published_date": "2013-05",
        "source_version": None,
    },
    "lowry_2007": {
        "source_doi": "10.1126/science.1139040",
        "source_published_date": "2007-04-13",
        "source_version": None,
    },
    "vokrouhlicky_2015_apophis": {
        "source_doi": "10.1016/j.icarus.2015.01.025",
        "source_published_date": "2015-05",
        "source_version": None,
    },
    "watanabe_2019_ryugu": {
        "source_doi": "10.1126/science.aav8032",
        "source_published_date": "2019-04-19",
        "source_version": None,
    },
    "lowry_2014_itokawa": {
        "source_doi": "10.1051/0004-6361/201322602",
        "source_published_date": "2014-02",
        "source_version": None,
    },
    "kaasalainen_2007": {
        "source_doi": "10.1038/nature05614",
        "source_published_date": "2007-03-22",
        "source_version": None,
    },
    "durech_2008_geographos": {
        "source_doi": "10.1051/0004-6361:200810672",
        "source_published_date": "2008-10",
        "source_version": None,
    },
    "farnocchia_2014_1950da": {
        "source_doi": "10.1016/j.icarus.2013.11.022",
        "source_published_date": "2014-02",
        "source_version": None,
    },
    "chesley_2003_golevka": {
        "source_doi": "10.1126/science.1091452",
        "source_published_date": "2003-12-05",
        "source_version": None,
    },
    "durech_2012_eger": {
        "source_doi": "10.1051/0004-6361/201219831",
        "source_published_date": "2012-11",
        "source_version": None,
    },
}

ENTERED_LOCALLY_AT: str = "2026-05-09"


def entry_to_amsc_dict(entry) -> Dict[str, Any]:
    prov = SOURCE_KEY_PROVENANCE[entry.source_key]
    return {
        "name": entry.short_name,
        "row_type": "yarkovsky_yorp_entry",
        "designation": entry.designation,
        "semi_major_axis_au": entry.semi_major_axis_au,
        "eccentricity": entry.eccentricity,
        "diameter_km": entry.diameter_km,
        "rotation_period_hours": entry.rotation_period_hours,
        "yarkovsky_drift_1e4_au_per_myr": entry.yarkovsky_drift_1e4_au_per_myr,
        "yarkovsky_uncertainty_1e4_au_per_myr": entry.yarkovsky_uncertainty_1e4_au_per_myr,
        "yorp_spin_rate_change_1e8_rad_per_day_sq": entry.yorp_spin_rate_change_1e8_rad_per_day_sq,
        "yorp_uncertainty_1e8_rad_per_day_sq": entry.yorp_uncertainty_1e8_rad_per_day_sq,
        "is_prograde": entry.is_prograde,
        "precision_flag": entry.precision_flag,
        "notes": entry.notes,
        "source_doi": prov["source_doi"],
        "source_published_date": prov["source_published_date"],
        "entered_locally_at": ENTERED_LOCALLY_AT,
        "source_version": prov["source_version"],
    }


def hand_coded_rows_in_amsc_shape() -> List[Dict[str, Any]]:
    return [entry_to_amsc_dict(e) for e in YARKOVSKY_YORP_ENTRIES]


def emit_ndjson() -> str:
    rows = hand_coded_rows_in_amsc_shape()
    return "\n".join(
        json.dumps(row, ensure_ascii=False, sort_keys=False)
        for row in rows
    ) + "\n"
