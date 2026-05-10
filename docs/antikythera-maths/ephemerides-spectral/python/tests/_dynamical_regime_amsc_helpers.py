"""Shared helpers for the v0.27.0 phase A AMSC backfill of the
v0.24.9 Sol Dynamical-Regime Classifier Training Roster.

Single row_type ('regime_example'); each row is one v0.24.x ship's
7-feature signature vector + regime label. Maps each `v024_N`
source_key in the hand-coded module to the canonical paper most
identified with that v0.24.x ship — same DOIs the per-ship AMSC
helpers use for their respective ship's primary citation.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from ephemerides_spectral._research.dynamical_regime_data import (
    REGIME_EXAMPLES,
)


SOURCE_KEY_PROVENANCE: Dict[str, Dict[str, Any]] = {
    "v024_0": {
        # Mercury Dynamical Spectrum: Margot 2007 *Science* 316:710 —
        # Mercury 3:2 spin-orbit lock from Earth-based radar speckle
        # tracking. The headline empirical-anchor of the v0.24.0 ship.
        "source_doi": "10.1126/science.1140514",
        "source_published_date": "2007-05-04",
        "source_version": None,
    },
    "v024_1": {
        # Luna Dynamical Spectrum: Williams & Boggs 2014 *JGR Planets*
        # 119:1546 — LLR-anchored libration + Saros 223:239:242
        # closure. Canonical reference for the v0.24.1 ship.
        "source_doi": "10.1002/2013JE004489",
        "source_published_date": "2014-07",
        "source_version": None,
    },
    "v024_2": {
        # Mars Dynamical Spectrum: Laskar & Robutel 1993 *Nature*
        # 361:608 — the chaotic-obliquity finding (KAM small-
        # denominator failure on Mars secular fundamentals).
        "source_doi": "10.1038/361608a0",
        "source_published_date": "1993-02-18",
        "source_version": None,
    },
    "v024_3": {
        # Sun Dynamical Spectrum: Davies 2014 *MNRAS* 439:2025 —
        # BiSON 22-yr low-degree p-mode catalogue, the headline
        # helioseismology data source for the v0.24.3 ship.
        "source_doi": "10.1093/mnras/stu080",
        "source_published_date": "2014-04",
        "source_version": "BiSON",
    },
    "v024_4": {
        # Toroidal-Residual J₂: Iess 2019 *Science* 364:eaat2965 —
        # Cassini Grand Finale Saturn gravity (Saturn is THE extreme
        # case at q ≈ 0.155, closest to Maclaurin-Jacobi bifurcation).
        "source_doi": "10.1126/science.aat2965",
        "source_published_date": "2019-01-17",
        "source_version": "Cassini Grand Finale",
    },
    "v024_5": {
        # Hawaiian-Emperor Chain: Sharp & Clague 2006 *Science*
        # 313:1281 — canonical 47.5 Myr bend-age + Ar-Ar dates.
        "source_doi": "10.1126/science.1128489",
        "source_published_date": "2006-09-01",
        "source_version": None,
    },
    "v024_6": {
        # Yarkovsky/YORP: Chesley 2003 *Science* 302:1739 — THE first-
        # ever Yarkovsky detection (Golevka via radar ranging).
        "source_doi": "10.1126/science.1091452",
        "source_published_date": "2003-12-05",
        "source_version": None,
    },
    "v024_7": {
        # Mars Tharsis: Plescia 2004 *J. Geophys. Res.* 109:E03003 —
        # canonical Mars-volcano morphometric compilation; the
        # headline reference for the v0.24.7 ship.
        "source_doi": "10.1029/2002JE002031",
        "source_published_date": "2004-03",
        "source_version": None,
    },
    "v024_8": {
        # Axial Seamount: Chadwick 2016 *Science* 354:1395 — the
        # canonical successfully-forecast eruption (2015 HIT).
        "source_doi": "10.1126/science.aah4666",
        "source_published_date": "2016-12-16",
        "source_version": None,
    },
    "v024_11": {
        # Pluto-Charon Dynamical Spectrum: Brozovic 2015 *Icarus*
        # 246:317 — post-New-Horizons orbital fit; mass ratio +
        # mutual lock + small-moon orbits.
        "source_doi": "10.1016/j.icarus.2014.03.015",
        "source_published_date": "2015-01",
        "source_version": None,
    },
    "v024_12": {
        # Loki Patera (Io) Eruption Cycle: Rathbun 2002 *Icarus*
        # 158:286 — canonical ~540-day periodicity prediction
        # (validated by subsequent observations).
        "source_doi": "10.1006/icar.2002.6878",
        "source_published_date": "2002-08",
        "source_version": None,
    },
}

ENTERED_LOCALLY_AT: str = "2026-05-09"


def example_to_amsc_dict(ex) -> Dict[str, Any]:
    prov = SOURCE_KEY_PROVENANCE[ex.source_key]
    return {
        "name": ex.name,
        "row_type": "regime_example",
        "ship_version": ex.ship_version,
        "regime_label": ex.regime_label,
        "description": ex.description,
        "catalog_module": ex.catalog_module,
        "time_scale_log_s": ex.time_scale_log_s,
        "spatial_scale_log_km": ex.spatial_scale_log_km,
        "stability_index": ex.stability_index,
        "has_commensurability": ex.has_commensurability,
        "prediction_track_signal": ex.prediction_track_signal,
        "dimensionality": ex.dimensionality,
        "forcing_class_index": ex.forcing_class_index,
        "precision_flag": ex.precision_flag,
        "notes": ex.notes,
        "source_doi": prov["source_doi"],
        "source_published_date": prov["source_published_date"],
        "entered_locally_at": ENTERED_LOCALLY_AT,
        "source_version": prov["source_version"],
    }


def hand_coded_rows_in_amsc_shape() -> List[Dict[str, Any]]:
    return [example_to_amsc_dict(ex) for ex in REGIME_EXAMPLES]


def emit_ndjson() -> str:
    rows = hand_coded_rows_in_amsc_shape()
    return "\n".join(
        json.dumps(row, ensure_ascii=False, sort_keys=False)
        for row in rows
    ) + "\n"
