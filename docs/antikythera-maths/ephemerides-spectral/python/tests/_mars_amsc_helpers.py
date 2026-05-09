"""Shared helpers for the v0.27.0 phase A AMSC backfill of the
v0.24.2 Mars Dynamical Spectrum catalogue.

Mirrors `_mercury_amsc_helpers.py` (PR #303) and
`_luna_amsc_helpers.py` (PR #306). The pattern: convert hand-coded
``DynamicalMode`` + ``SecularResonance`` rows to AMSC-shape dicts
via a static SOURCE_KEY_PROVENANCE table.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from ephemerides_spectral._research.mars_dynamical_spectrum_data import (
    MARS_DYNAMICAL_MODES,
    MARS_SECULAR_RESONANCES,
)


SOURCE_KEY_PROVENANCE: Dict[str, Dict[str, Any]] = {
    "jpl_de441": {
        "source_doi": "10.3847/1538-3881/abd414",
        "source_published_date": "2021-02",
        "source_version": "DE441",
    },
    "le_maistre_2023": {
        "source_doi": "10.1038/s41586-023-06150-0",
        "source_published_date": "2023-06",
        "source_version": None,
    },
    "ward_1973": {
        "source_doi": "10.1126/science.181.4096.260",
        "source_published_date": "1973-07-20",
        "source_version": None,
    },
    "laskar_1993": {
        "source_doi": "10.1038/361608a0",
        "source_published_date": "1993-02-18",
        "source_version": None,
    },
    "laskar_2004": {
        "source_doi": "10.1016/j.icarus.2004.04.005",
        "source_published_date": "2004-08",
        "source_version": None,
    },
    "laskar_2008": {
        # Nature 459, 11 June 2009 (the source_key naming is by the
        # arXiv-preprint year 2008; the published Nature paper is 2009).
        "source_doi": "10.1038/nature08096",
        "source_published_date": "2009-06-11",
        "source_version": None,
    },
    "touma_wisdom_1993": {
        "source_doi": "10.1126/science.259.5099.1294",
        "source_published_date": "1993-02-26",
        "source_version": None,
    },
}

ENTERED_LOCALLY_AT: str = "2026-05-09"


def _composite_resonance_name(res) -> str:
    """Build the AMSC row name for a secular_resonance row by joining
    Mars mode + secular partner with a double-underscore separator.
    Keeps the per-row identifier unambiguous when multiple secular
    pairings share the same Mars mode."""
    return f"{res.mars_mode}__{res.secular_partner}"


def mode_to_amsc_dict(mode) -> Dict[str, Any]:
    """Convert a :class:`DynamicalMode` to its AMSC-shape dict."""
    prov = SOURCE_KEY_PROVENANCE[mode.source_key]
    return {
        "name": mode.name,
        "row_type": "dynamical_mode",
        "frequency_per_century": mode.frequency_per_century,
        "period_days": mode.period_days,
        "amplitude_value": mode.amplitude_value,
        "amplitude_units": mode.amplitude_units,
        "angle_or_action": mode.angle_or_action,
        "mars_mode": None,
        "secular_partner": None,
        "partner_description": None,
        "proximity_arcsec_per_year": None,
        "precision_flag": mode.precision_flag,
        "notes": mode.notes,
        "source_doi": prov["source_doi"],
        "source_published_date": prov["source_published_date"],
        "entered_locally_at": ENTERED_LOCALLY_AT,
        "source_version": prov["source_version"],
    }


def resonance_to_amsc_dict(res) -> Dict[str, Any]:
    """Convert a :class:`SecularResonance` to its AMSC-shape dict."""
    prov = SOURCE_KEY_PROVENANCE[res.source_key]
    return {
        "name": _composite_resonance_name(res),
        "row_type": "secular_resonance",
        "frequency_per_century": None,
        "period_days": None,
        "amplitude_value": None,
        "amplitude_units": None,
        "angle_or_action": None,
        "mars_mode": res.mars_mode,
        "secular_partner": res.secular_partner,
        "partner_description": res.partner_description,
        "proximity_arcsec_per_year": res.proximity_arcsec_per_year,
        "precision_flag": res.precision_flag,
        "notes": res.notes,
        "source_doi": prov["source_doi"],
        "source_published_date": prov["source_published_date"],
        "entered_locally_at": ENTERED_LOCALLY_AT,
        "source_version": prov["source_version"],
    }


def hand_coded_rows_in_amsc_shape() -> List[Dict[str, Any]]:
    """All hand-coded rows converted to AMSC-shape dicts, modes first
    then secular-resonance rows."""
    return (
        [mode_to_amsc_dict(m) for m in MARS_DYNAMICAL_MODES]
        + [resonance_to_amsc_dict(r) for r in MARS_SECULAR_RESONANCES]
    )


def emit_ndjson() -> str:
    rows = hand_coded_rows_in_amsc_shape()
    return "\n".join(
        json.dumps(row, ensure_ascii=False, sort_keys=False)
        for row in rows
    ) + "\n"
