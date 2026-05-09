"""Shared helpers for the v0.27.0 phase A AMSC backfill of the
v0.24.3 Sun Dynamical Spectrum catalogue.

Mirrors `_mercury_amsc_helpers.py` (PR #303), `_luna_amsc_helpers.py`
(PR #306), and `_mars_amsc_helpers.py` (PR #308). Single row_type
('helioseismic_mode') simplifies the converter to one function.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from ephemerides_spectral._research.sun_dynamical_spectrum_data import (
    HELIOSEISMIC_MODES,
)


SOURCE_KEY_PROVENANCE: Dict[str, Dict[str, Any]] = {
    "davies_2014": {
        "source_doi": "10.1093/mnras/stu080",
        "source_published_date": "2014-04",
        "source_version": None,
    },
}

ENTERED_LOCALLY_AT: str = "2026-05-09"


def _composite_mode_name(mode) -> str:
    """Build the AMSC row name for a helioseismic_mode row by joining
    radial order n and spherical-harmonic degree l."""
    return f"n{mode.n}_l{mode.l}"


def mode_to_amsc_dict(mode) -> Dict[str, Any]:
    """Convert a :class:`HelioseismicMode` to its AMSC-shape dict."""
    prov = SOURCE_KEY_PROVENANCE[mode.source_key]
    return {
        "name": _composite_mode_name(mode),
        "row_type": "helioseismic_mode",
        "n": mode.n,
        "l": mode.l,
        "frequency_uhz": mode.frequency_uhz,
        "mode_class": mode.mode_class,
        "precision_flag": mode.precision_flag,
        "notes": mode.notes,
        "source_doi": prov["source_doi"],
        "source_published_date": prov["source_published_date"],
        "entered_locally_at": ENTERED_LOCALLY_AT,
        "source_version": prov["source_version"],
    }


def hand_coded_rows_in_amsc_shape() -> List[Dict[str, Any]]:
    """All hand-coded HELIOSEISMIC_MODES converted to AMSC-shape dicts
    in their source order."""
    return [mode_to_amsc_dict(m) for m in HELIOSEISMIC_MODES]


def emit_ndjson() -> str:
    rows = hand_coded_rows_in_amsc_shape()
    return "\n".join(
        json.dumps(row, ensure_ascii=False, sort_keys=False)
        for row in rows
    ) + "\n"
