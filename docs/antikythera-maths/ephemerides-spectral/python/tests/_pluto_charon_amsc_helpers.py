"""Shared helpers for the v0.27.0 phase A AMSC backfill of the
v0.24.11 Pluto-Charon Dynamical Spectrum catalogue.

Mirrors `_luna_amsc_helpers.py` (PR #306) — single dataclass
(``DynamicalMode``) but with all-real, Crossref-indexed source DOIs
(no nodoi: / historical: / isbn: prefixes; the entire Pluto-Charon
catalogue is post-1990 modern literature, with the headline payload
sourced from Brozovic 2015's post-New-Horizons orbital fit).

Cross-platform float discipline
-------------------------------
``frequency_per_century`` is computed as a single division
(``_DAYS_PER_CENTURY / period_days``) in the hand-coded module —
the same shape as v0.24.0 Mercury / v0.24.1 Luna / v0.24.2 Mars
catalogues, which all run cleanly across Windows + POSIX without
``_round_sig`` rounding. A pure division of two finite floats does
not exhibit the multi-step libm divergence that motivated the
toroidal-residual rounding (``ω²·R³/GM`` is a 3-multiplication +
1-division chain involving ``math.pi``); a single FDIV is bit-stable
across platforms, so no rounding is required here.

The action-variable rows carry ``period_days = float('inf')``,
which Python's ``json`` module emits as the non-standard
``Infinity`` token — accepted symmetrically by ``json.loads`` so
the NDJSON round-trips cleanly.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from ephemerides_spectral._research.pluto_charon_dynamical_spectrum_data import (
    PLUTO_CHARON_DYNAMICAL_MODES,
)


SOURCE_KEY_PROVENANCE: Dict[str, Dict[str, Any]] = {
    "stern_1992": {
        # Stern S. A. (1992). The Pluto-Charon system. Annual Review
        # of Astronomy and Astrophysics 30:185-233. The canonical
        # pre-New-Horizons review of the binary's mutual tidal lock.
        "source_doi": "10.1146/annurev.aa.30.090192.001153",
        "source_published_date": "1992-09",
        "source_version": None,
    },
    "brozovic_2015": {
        # Brozovic M., Showalter M. R., Jacobson R. A., Buie M. W.
        # (2015). The orbits and masses of satellites of Pluto.
        # Icarus 246:317-329. The post-New-Horizons definitive
        # orbital fit; canonical_doi.
        "source_doi": "10.1016/j.icarus.2014.03.015",
        "source_published_date": "2015-01",
        "source_version": None,
    },
    "stern_2015": {
        # Stern S. A. et al. (2015). The Pluto system: Initial
        # results from its exploration by New Horizons. Science
        # 350:aad1815.
        "source_doi": "10.1126/science.aad1815",
        "source_published_date": "2015-10-16",
        "source_version": "New Horizons",
    },
    "showalter_hamilton_2015": {
        # Showalter M. R. & Hamilton D. P. (2015). Resonant
        # interactions and chaotic rotation of Pluto's small moons.
        # Nature 522:45-49.
        "source_doi": "10.1038/nature14469",
        "source_published_date": "2015-06-04",
        "source_version": None,
    },
    "showalter_2015_nature": {
        # Showalter et al. 2015 (Kerberos discovery + small-moon
        # dynamics). Same DOI as showalter_hamilton_2015 — the same
        # Nature 522:45 paper carries the dynamical characterisation
        # used for both the Kerberos 5:1 near-resonance and the
        # general small-moon orbital framework.
        "source_doi": "10.1038/nature14469",
        "source_published_date": "2015-06-04",
        "source_version": None,
    },
}

ENTERED_LOCALLY_AT: str = "2026-05-09"


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
        "precision_flag": mode.precision_flag,
        "notes": mode.notes,
        "source_doi": prov["source_doi"],
        "source_published_date": prov["source_published_date"],
        "entered_locally_at": ENTERED_LOCALLY_AT,
        "source_version": prov["source_version"],
    }


def hand_coded_rows_in_amsc_shape() -> List[Dict[str, Any]]:
    """All hand-coded PLUTO_CHARON_DYNAMICAL_MODES converted to
    AMSC-shape dicts in their source order."""
    return [mode_to_amsc_dict(m) for m in PLUTO_CHARON_DYNAMICAL_MODES]


def emit_ndjson() -> str:
    rows = hand_coded_rows_in_amsc_shape()
    return "\n".join(
        json.dumps(row, ensure_ascii=False, sort_keys=False)
        for row in rows
    ) + "\n"
