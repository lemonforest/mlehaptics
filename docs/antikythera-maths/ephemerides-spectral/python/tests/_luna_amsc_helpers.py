"""Shared helpers for the v0.27.0 phase A AMSC backfill of the
v0.24.1 Luna Dynamical Spectrum catalogue.

Mirrors `_mercury_amsc_helpers.py` (PR #303) — the pattern is
identical: the v0.24.1 hand-coded module's row dataclasses
(``DynamicalMode``, ``SarosCommensurability``) predate the AMSC
framework and don't carry source_doi / published_date /
entered_locally_at fields directly. This helper provides the
converter that maps hand-coded rows to AMSC-shape dicts via a
static SOURCE_KEY_PROVENANCE table.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from ephemerides_spectral._research.luna_dynamical_spectrum_data import (
    LUNA_DYNAMICAL_MODES,
    SAROS_COMMENSURABILITY,
)


SOURCE_KEY_PROVENANCE: Dict[str, Dict[str, Any]] = {
    "allens_astrophysical_quantities": {
        "source_doi": "isbn:978-0387987460",
        "source_published_date": "2000",
        "source_version": "4th edition",
    },
    "jpl_de441": {
        "source_doi": "10.3847/1538-3881/abd414",
        "source_published_date": "2021-02",
        "source_version": "DE441",
    },
    "williams_2014": {
        "source_doi": "10.1002/2013JE004489",
        "source_published_date": "2014-07",
        "source_version": None,
    },
    "murray_dermott_1999": {
        "source_doi": "isbn:978-0521575973",
        "source_published_date": "1999-02-13",
        "source_version": "1st edition",
    },
    "cassini_1693": {
        # Pre-DOI historical work. The "historical:" prefix is the
        # project's convention for stable identifiers of works that
        # predate Crossref / ADS bibcode systems.
        "source_doi": "historical:cassini_1693_lunar_libration",
        "source_published_date": "1693",
        "source_version": None,
    },
    "meeus_1991": {
        "source_doi": "isbn:978-0943396354",
        "source_published_date": "1991",
        "source_version": "1st edition",
    },
}

ENTERED_LOCALLY_AT: str = "2026-05-09"


def mode_to_amsc_dict(mode) -> Dict[str, Any]:
    """Convert a :class:`DynamicalMode` to its AMSC-shape dict.
    Nulls out the saros_commensurability-specific fields."""
    prov = SOURCE_KEY_PROVENANCE[mode.source_key]
    return {
        "name": mode.name,
        "row_type": "dynamical_mode",
        "frequency_per_century": mode.frequency_per_century,
        "period_days": mode.period_days,
        "amplitude_value": mode.amplitude_value,
        "amplitude_units": mode.amplitude_units,
        "angle_or_action": mode.angle_or_action,
        "integer_count": None,
        "unit_period_days": None,
        "product_days": None,
        "precision_flag": mode.precision_flag,
        "notes": mode.notes,
        "source_doi": prov["source_doi"],
        "source_published_date": prov["source_published_date"],
        "entered_locally_at": ENTERED_LOCALLY_AT,
        "source_version": prov["source_version"],
    }


def saros_to_amsc_dict(saros) -> Dict[str, Any]:
    """Convert a :class:`SarosCommensurability` to its AMSC-shape dict.
    Nulls out the dynamical_mode-specific fields."""
    prov = SOURCE_KEY_PROVENANCE[saros.source_key]
    return {
        "name": saros.name,
        "row_type": "saros_commensurability",
        "frequency_per_century": None,
        "period_days": None,
        "amplitude_value": None,
        "amplitude_units": None,
        "angle_or_action": None,
        "integer_count": saros.integer_count,
        "unit_period_days": saros.unit_period_days,
        "product_days": saros.product_days,
        "precision_flag": saros.precision_flag,
        "notes": saros.notes,
        "source_doi": prov["source_doi"],
        "source_published_date": prov["source_published_date"],
        "entered_locally_at": ENTERED_LOCALLY_AT,
        "source_version": prov["source_version"],
    }


def hand_coded_rows_in_amsc_shape() -> List[Dict[str, Any]]:
    """All hand-coded rows converted to AMSC-shape dicts, modes
    first then saros-commensurability rows."""
    return (
        [mode_to_amsc_dict(m) for m in LUNA_DYNAMICAL_MODES]
        + [saros_to_amsc_dict(s) for s in SAROS_COMMENSURABILITY]
    )


def emit_ndjson() -> str:
    """Render the full AMSC NDJSON content from the hand-coded
    module."""
    rows = hand_coded_rows_in_amsc_shape()
    return "\n".join(
        json.dumps(row, ensure_ascii=False, sort_keys=False)
        for row in rows
    ) + "\n"
