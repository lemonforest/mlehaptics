"""Shared helpers for the v0.27.0 phase A AMSC backfill of the
v0.24.12 Loki Patera Eruption Cycle catalogue.

Mirrors `_axial_seamount_amsc_helpers.py` (PR #315) — multi-row-type
catalogue with two row types ('cycle_peak' / 'cycle_mode') sharing
one schema with row-type-specific optional fields. Mostly real,
Crossref-indexed DOIs (Veeder 1994 / Rathbun 2002 / de Kleer 2017 /
de Kleer 2019 *Nature* / Peale-Cassen-Reynolds 1979) plus one
`isbn:` for the Murray-Dermott 1999 *Solar System Dynamics* textbook
(canonical Galilean-Laplace 4:2:1 reference).
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from ephemerides_spectral._research.loki_patera_data import (
    LOKI_CYCLE_MODES,
    LOKI_CYCLE_PEAKS,
)


SOURCE_KEY_PROVENANCE: Dict[str, Dict[str, Any]] = {
    "veeder_1994": {
        # Veeder G. J. et al. (1994). Io's heat flow from infrared
        # radiometry: 1983-1993. J. Geophys. Res. 99:17095. The first
        # multi-year time-series of Io's thermal output, including
        # KAO observations of Loki's 1990 peak.
        "source_doi": "10.1029/94JE00637",
        "source_published_date": "1994-08",
        "source_version": None,
    },
    "rathbun_2002": {
        # Rathbun J. A., Spencer J. R., Davies A. G., Howell R. R.,
        # Wilson L. (2002). Loki, Io: A periodic volcano. Geophys.
        # Res. Lett. 29:1443. THE canonical paper establishing the
        # ~540-day quasi-periodic cycle. canonical_doi.
        "source_doi": "10.1029/2002GL014747",
        "source_published_date": "2002-08",
        "source_version": None,
    },
    "de_kleer_2017": {
        # de Kleer K. & de Pater I. (2017). Time variability of Io's
        # volcanic activity from near-IR adaptive optics observations
        # on 100 nights in 2013-2015. Icarus 280:378.
        "source_doi": "10.1016/j.icarus.2016.06.019",
        "source_published_date": "2016-12",
        "source_version": None,
    },
    "de_kleer_2019": {
        # de Kleer K. et al. Multi-phase volcanic resurfacing at Loki
        # Patera from quasi-periodic adaptive optics monitoring.
        # Nature 589:199-203. The hand-coded module's source_key is
        # `de_kleer_2019` (referencing the analysis era + Nature
        # Letter content). DOI registered ahead of print in 2020;
        # printed volume 589 was January 2021.
        "source_doi": "10.1038/s41586-020-03031-8",
        "source_published_date": "2021-01",
        "source_version": None,
    },
    "peale_cassen_reynolds_1979": {
        # Peale S. J., Cassen P., Reynolds R. T. (1979). Melting of
        # Io by tidal dissipation. Science 203:892. The famous Io
        # tidal-heating prediction published 2 weeks before Voyager
        # 1's confirming flyby observation of active volcanism.
        "source_doi": "10.1126/science.203.4383.892",
        "source_published_date": "1979-03-02",
        "source_version": None,
    },
    "murray_dermott_1999": {
        # Murray C. D. & Dermott S. F. (1999). *Solar System
        # Dynamics*. Cambridge University Press. The canonical
        # textbook reference for the Galilean Laplace 4:2:1
        # commensurability period parameters. ISBN-encoded since
        # the textbook predates DOI assignment for monographs of
        # this era.
        "source_doi": "isbn:978-0521575973",
        "source_published_date": "1999-02-13",
        "source_version": "1st edition",
    },
}

ENTERED_LOCALLY_AT: str = "2026-05-09"


def cycle_peak_to_amsc_dict(p) -> Dict[str, Any]:
    """Convert a :class:`LokiCyclePeakObservation` to its AMSC-shape
    dict; nulls out the cycle_mode-specific fields."""
    prov = SOURCE_KEY_PROVENANCE[p.source_key]
    return {
        "name": p.name,
        "row_type": "cycle_peak",
        "peak_year": p.peak_year,
        "peak_month": p.peak_month,
        "cycle_index_from_anchor": p.cycle_index_from_anchor,
        "period_days": None,
        "mode_class": None,
        "description": None,
        "precision_flag": p.precision_flag,
        "notes": p.notes,
        "source_doi": prov["source_doi"],
        "source_published_date": prov["source_published_date"],
        "entered_locally_at": ENTERED_LOCALLY_AT,
        "source_version": prov["source_version"],
    }


def cycle_mode_to_amsc_dict(m) -> Dict[str, Any]:
    """Convert a :class:`CycleMode` to its AMSC-shape dict; nulls out
    the cycle_peak-specific fields."""
    prov = SOURCE_KEY_PROVENANCE[m.source_key]
    return {
        "name": m.name,
        "row_type": "cycle_mode",
        "peak_year": None,
        "peak_month": None,
        "cycle_index_from_anchor": None,
        "period_days": m.period_days,
        "mode_class": m.mode_class,
        "description": m.description,
        "precision_flag": m.precision_flag,
        "notes": None,
        "source_doi": prov["source_doi"],
        "source_published_date": prov["source_published_date"],
        "entered_locally_at": ENTERED_LOCALLY_AT,
        "source_version": prov["source_version"],
    }


def hand_coded_rows_in_amsc_shape() -> List[Dict[str, Any]]:
    """All hand-coded rows converted to AMSC-shape dicts: cycle peaks
    first, then cycle modes."""
    return (
        [cycle_peak_to_amsc_dict(p) for p in LOKI_CYCLE_PEAKS]
        + [cycle_mode_to_amsc_dict(m) for m in LOKI_CYCLE_MODES]
    )


def emit_ndjson() -> str:
    rows = hand_coded_rows_in_amsc_shape()
    return "\n".join(
        json.dumps(row, ensure_ascii=False, sort_keys=False)
        for row in rows
    ) + "\n"
