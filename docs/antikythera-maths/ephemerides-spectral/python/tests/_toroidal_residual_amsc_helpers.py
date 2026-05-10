"""Shared helpers for the v0.27.0 phase A AMSC backfill of the
v0.24.4 Per-body Toroidal-Residual J₂ Catalogue.

Mirrors `_{mercury,luna,mars,sun}_amsc_helpers.py` (PRs #303, #306,
#308, #309). Single row_type ('toroidal_residual_classification')
simplifies the converter to one function.

Cross-platform float discipline
-------------------------------
``rotation_parameter_q`` is computed via ``ω²·R³/GM`` in the
hand-coded module — a libm chain (``math.pi``, multiplications,
divisions) that produces last-bit-different results across
platforms (Windows libm vs POSIX libm; even between two Windows
hosts with different CRT versions). The dual-author test compares
dict equality, so a single ULP difference fails CI. Both the AMSC
NDJSON write path and the hand-coded → AMSC converter round
``rotation_parameter_q`` to 12 significant figures via
:func:`_round_sig` before emission, well above the input precision
(rotation periods + radii are 5–6 sig fig measurements; GM values
are 8 sig figs); the rounding throws away last-bit platform
divergence without losing physically meaningful precision. Other
fields in this catalogue are direct measurements, not libm-computed;
they don't need rounding.
"""

from __future__ import annotations

import json
import math
from typing import Any, Dict, List

from ephemerides_spectral._research.toroidal_residual_data import (
    TOROIDAL_RESIDUALS,
)


def _round_sig(x: float, sig: int = 12) -> float:
    """Round to ``sig`` significant figures. Used for libm-computed
    values to guarantee cross-platform byte-stability without
    requiring a tolerance-based comparison."""
    if x == 0.0:
        return 0.0
    digits = sig - int(math.floor(math.log10(abs(x)))) - 1
    return round(x, digits)


SOURCE_KEY_PROVENANCE: Dict[str, Dict[str, Any]] = {
    "egm2008": {
        "source_doi": "10.1029/2011JB008916",
        "source_published_date": "2012-04",
        "source_version": "EGM2008",
    },
    "genova_2016": {
        "source_doi": "10.1016/j.icarus.2016.02.050",
        "source_published_date": "2016-07",
        "source_version": "MRO99B",
    },
    "anderson_2002_venus": {
        "source_doi": "10.1006/icar.2002.6936",
        "source_published_date": "2002-10",
        "source_version": None,
    },
    "smith_2012_messenger": {
        "source_doi": "10.1126/science.1218809",
        "source_published_date": "2012-04-13",
        "source_version": "MESSENGER",
    },
    "konopliv_2013_grail": {
        "source_doi": "10.1002/jgre.20097",
        "source_published_date": "2013-07",
        "source_version": "GRAIL primary mission",
    },
    "iess_2018_juno": {
        "source_doi": "10.1038/nature25776",
        "source_published_date": "2018-03-08",
        "source_version": "Juno gravity science",
    },
    "iess_2019_cassini": {
        "source_doi": "10.1126/science.aat2965",
        "source_published_date": "2019-01-17",
        "source_version": "Cassini Grand Finale",
    },
    "jacobson_2014_uranus": {
        "source_doi": "10.1088/0004-6256/148/5/76",
        "source_published_date": "2014-11",
        "source_version": None,
    },
    "jacobson_2009_neptune": {
        "source_doi": "10.1088/0004-6256/137/5/4322",
        "source_published_date": "2009-05",
        "source_version": None,
    },
    "anderson_2001_galilean_gravity": {
        "source_doi": "10.1029/2000JE001367",
        "source_published_date": "2001-12",
        "source_version": "Galileo radio science",
    },
    "iess_2010_titan": {
        "source_doi": "10.1126/science.1182583",
        "source_published_date": "2010-03-12",
        "source_version": None,
    },
}

ENTERED_LOCALLY_AT: str = "2026-05-09"


def residual_to_amsc_dict(residual) -> Dict[str, Any]:
    """Convert a :class:`ToroidalResidual` to its AMSC-shape dict.

    ``rotation_parameter_q`` is rounded to 12 significant figures via
    :func:`_round_sig` to remove last-bit cross-platform libm
    divergence (the only libm-computed field in this catalogue;
    everything else is a direct measurement)."""
    prov = SOURCE_KEY_PROVENANCE[residual.source_key]
    return {
        "name": residual.body,
        "row_type": "toroidal_residual_classification",
        "rotation_period_days": residual.rotation_period_days,
        "equatorial_radius_km": residual.equatorial_radius_km,
        "GM_m3_s2": residual.GM_m3_s2,
        "rotation_parameter_q": _round_sig(residual.rotation_parameter_q),
        "J2_observed": residual.J2_observed,
        "moment_of_inertia_factor": residual.moment_of_inertia_factor,
        "regime": residual.regime,
        "fossil_figure": residual.fossil_figure,
        "precision_flag": residual.precision_flag,
        "notes": residual.notes,
        "source_doi": prov["source_doi"],
        "source_published_date": prov["source_published_date"],
        "entered_locally_at": ENTERED_LOCALLY_AT,
        "source_version": prov["source_version"],
    }


def hand_coded_rows_in_amsc_shape() -> List[Dict[str, Any]]:
    """All hand-coded TOROIDAL_RESIDUALS converted to AMSC-shape dicts
    in their source order."""
    return [residual_to_amsc_dict(r) for r in TOROIDAL_RESIDUALS]


def emit_ndjson() -> str:
    rows = hand_coded_rows_in_amsc_shape()
    return "\n".join(
        json.dumps(row, ensure_ascii=False, sort_keys=False)
        for row in rows
    ) + "\n"
