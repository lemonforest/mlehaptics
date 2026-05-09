"""Shared helpers for the v0.27.0 phase A AMSC backfill of the
v0.24.0 Mercury Dynamical Spectrum catalogue.

The hand-coded ``_research/mercury_dynamical_spectrum_data.py`` module
predates the AMSC framework; its row dataclasses (``DynamicalMode``,
``PrecessionContribution``) don't carry source_doi / published_date /
entered_locally_at fields directly. This module provides the
converter that maps the hand-coded rows into AMSC-shape dicts,
filling in the attestation fields from a static SOURCE_KEY mapping
that's the single source of truth for the per-row provenance.

Used by:

* the test that ratchets agreement between the AMSC NDJSON at
  ``research/attested/mercury_dynamical_spectrum/mercury_dynamical_spectrum.ndjson``
  and the hand-coded module's contents (dual-author byte-stable diff,
  inheriting the Saturn-rings PR #291 pattern).
* the regenerator script that re-emits the AMSC NDJSON from the
  hand-coded module when the canonical values change.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from ephemerides_spectral._research.mercury_dynamical_spectrum_data import (
    MERCURY_DYNAMICAL_MODES,
    MERCURY_PRECESSION_CONTRIBUTIONS,
)


# Static mapping from the hand-coded module's source_key to the
# AMSC-required DOI + published_date + (optional) source_version.
# Author-curated; one row per cited reference in the SOURCES dict
# of `mercury_dynamical_spectrum_data.py`. The DOI for Einstein 1915
# uses NASA ADS bibcode form (no Crossref DOI exists for the 1915
# Sitzungsberichte paper); the schema accepts ``minLength: 5``.
SOURCE_KEY_PROVENANCE: Dict[str, Dict[str, Any]] = {
    "jpl_de441": {
        "source_doi": "10.3847/1538-3881/abd414",
        "source_published_date": "2021-02",
        "source_version": "DE441",
    },
    "margot_2007": {
        "source_doi": "10.1126/science.1140514",
        "source_published_date": "2007-05-04",
        "source_version": None,
    },
    "clemence_1947": {
        "source_doi": "10.1103/RevModPhys.19.361",
        "source_published_date": "1947",
        "source_version": None,
    },
    "einstein_1915": {
        # NASA ADS bibcode (Sitzungsberichte 1915 paper has no
        # Crossref DOI; ADS bibcode is the canonical identifier).
        "source_doi": "ads:1915SPAW.......831E",
        "source_published_date": "1915-11-25",
        "source_version": None,
    },
    "verma_2014": {
        "source_doi": "10.1051/0004-6361/201322124",
        "source_published_date": "2014-01",
        "source_version": "INPOP",
    },
    "park_2017": {
        "source_doi": "10.3847/1538-3881/aa5be2",
        "source_published_date": "2017-02",
        "source_version": None,
    },
    "murray_dermott_1999": {
        "source_doi": "isbn:978-0521575973",
        "source_published_date": "1999-02-13",
        "source_version": "1st edition",
    },
    "laskar_1989": {
        "source_doi": "10.1038/338237a0",
        "source_published_date": "1989-03-16",
        "source_version": None,
    },
}

# Date the AMSC backfill was first authored. Constant for every row
# in this catalogue's first ship; future amendments update the
# row-specific value.
ENTERED_LOCALLY_AT: str = "2026-05-09"


def mode_to_amsc_dict(mode) -> Dict[str, Any]:
    """Convert a :class:`DynamicalMode` to its AMSC-shape dict.

    Fills in attestation fields from
    :data:`SOURCE_KEY_PROVENANCE`; nulls out the
    precession_contribution-specific fields.
    """
    prov = SOURCE_KEY_PROVENANCE[mode.source_key]
    return {
        "name": mode.name,
        "row_type": "dynamical_mode",
        "frequency_per_century": mode.frequency_per_century,
        "period_days": mode.period_days,
        "amplitude_value": mode.amplitude_value,
        "amplitude_units": mode.amplitude_units,
        "angle_or_action": mode.angle_or_action,
        "arcsec_per_century": None,
        "physics_class": None,
        "precision_flag": mode.precision_flag,
        "notes": mode.notes,
        "source_doi": prov["source_doi"],
        "source_published_date": prov["source_published_date"],
        "entered_locally_at": ENTERED_LOCALLY_AT,
        "source_version": prov["source_version"],
    }


def contribution_to_amsc_dict(contrib) -> Dict[str, Any]:
    """Convert a :class:`PrecessionContribution` to its AMSC-shape dict.

    Fills in attestation fields from
    :data:`SOURCE_KEY_PROVENANCE`; nulls out the
    dynamical_mode-specific fields.
    """
    prov = SOURCE_KEY_PROVENANCE[contrib.source_key]
    return {
        "name": contrib.contributor,
        "row_type": "precession_contribution",
        "frequency_per_century": None,
        "period_days": None,
        "amplitude_value": None,
        "amplitude_units": None,
        "angle_or_action": None,
        "arcsec_per_century": contrib.arcsec_per_century,
        "physics_class": contrib.physics_class,
        "precision_flag": contrib.precision_flag,
        "notes": contrib.notes,
        "source_doi": prov["source_doi"],
        "source_published_date": prov["source_published_date"],
        "entered_locally_at": ENTERED_LOCALLY_AT,
        "source_version": prov["source_version"],
    }


def hand_coded_rows_in_amsc_shape() -> List[Dict[str, Any]]:
    """All hand-coded rows converted to AMSC-shape dicts, in the same
    order they appear in the source module (modes first, then
    contributions). Identity-preserving and order-preserving."""
    return (
        [mode_to_amsc_dict(m) for m in MERCURY_DYNAMICAL_MODES]
        + [contribution_to_amsc_dict(c) for c in MERCURY_PRECESSION_CONTRIBUTIONS]
    )


def emit_ndjson() -> str:
    """Render the full AMSC NDJSON content from the hand-coded
    module. Returns the canonical text (LF newlines, deterministic
    JSON serialisation) that should match the committed
    ``mercury_dynamical_spectrum.ndjson`` byte-for-byte modulo the
    leading comment header."""
    rows = hand_coded_rows_in_amsc_shape()
    # Match the saturn_rings NDJSON formatting: one JSON object per
    # line, sort_keys=False so field order matches the schema's
    # logical grouping rather than alphabetic.
    return "\n".join(
        json.dumps(row, ensure_ascii=False, sort_keys=False)
        for row in rows
    ) + "\n"
