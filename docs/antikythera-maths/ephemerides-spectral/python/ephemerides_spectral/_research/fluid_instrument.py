"""Sol Fluid Instrument — climatology + archive index + state-at-epoch
query surface for the solar-system fluid envelope (atmospheres, oceans,
cryospheres, exospheres).

Promotes the v0.20.2 architectural commitment from research notebook
§17.3 + §17.4.2 to a stable ship surface. Ships **all three Option-D
layers together** per the §17.4.2 full-coverage commitment — no MVP
subset, no deferred layer.

The three layers:

* :data:`BODY_CLIMATOLOGY` — climatological summary scalars per body
  (mean surface temperature, mean surface pressure, dominant gas
  composition, obliquity, orbital eccentricity, Bond albedo).
* :data:`FLUID_ARCHIVES` — archive-pointer index per atmospheric body
  (canonical external data sources with file format + access protocol
  + temporal coverage + endpoint URL).
* :data:`FLUID_STATE_COVERAGE` — state-at-epoch coverage flags per
  body. Earth (ERA5) and Mars (MCD v6.1) have the True flag; all
  other bodies fall back to the climatological summary with explicit
  out-of-coverage notes.

**This is NOT a BIP encoder running on fluid-envelope rhythms** — per
§17.4.1 the rhythm-mismatch finding generalises across fluid-envelope
channels alongside solid-body geodesy and magnetic multipoles. Fluid
envelopes have *spatial* variability (lat/lon dependence) and *temporal*
variability on weather-/climate-cycle timescales, but those timescales
do not form a low-order rational lattice with orbital periods, so the
cyclic-group encoder discipline does not transplant. The Sol Fluid
Instrument is a **state-lookup query surface** with optional state-at-
epoch indirection through external archive holdings (ERA5, MCD).

External archive integration policy
-----------------------------------
The package ships **pointers** into the canonical archives plus the
climatological-summary fallback. Live HTTP calls to ERA5 / MCD are NOT
part of v0.20.2 — `bridge.get_fluid_state(body, jd_tdb=...)` returns
the archive endpoint + the climatological fallback in a single dict;
it is up to the consumer to pull the actual state-at-epoch field via
the archive's own API (CDS-API for ERA5, the Python wrapper for MCD).
The package never makes outbound network calls.

Three bridge surfaces shape consumer access:

* :func:`compute_fluid_state` — per-body fluid state query, returning
  climatology + archive pointer + (where applicable) state-at-epoch
  coverage triage.
* :func:`list_fluid_archives` — full archive enumeration.
* :func:`compute_fluid_architecture` — partition by data-quality tier
  (HIGH / MEDIUM / LOW / NONE per the §17.1.6 ship-readiness convention).

The data tables are in :mod:`fluid_instrument_data`. Citations live in
its `SOURCES` dict; every numeric value carries a `source_key` pointing
into that dict so users can verify the provenance.

Reference: research notebook §17.3 (the architectural scoping for the
fluid envelope), §17.4.2 (the v0.20.2 ship sequence), and §17.4.1
(the rhythm-mismatch finding that motivates the state-lookup
architecture).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from .fluid_instrument_data import (
    BODY_CLIMATOLOGY,
    BodyClimatology,
    FLUID_ARCHIVES,
    FLUID_STATE_COVERAGE,
    FluidArchive,
    FluidStateCoverage,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
)


# ---- Memoised lookups (built at module load — μs on per-body lists) -

_CLIMATOLOGY_BY_BODY: Dict[str, BodyClimatology] = {
    m.body: m for m in BODY_CLIMATOLOGY
}
_ARCHIVES_BY_BODY: Dict[str, List[FluidArchive]] = {}
for _archive in FLUID_ARCHIVES:
    _ARCHIVES_BY_BODY.setdefault(_archive.body, []).append(_archive)
_COVERAGE_BY_BODY: Dict[str, FluidStateCoverage] = {
    m.body: m for m in FLUID_STATE_COVERAGE
}

# Union of all bodies that have any kind of fluid record.
_ALL_BODIES: List[str] = sorted(
    set(_CLIMATOLOGY_BY_BODY.keys())
    | set(_ARCHIVES_BY_BODY.keys())
    | set(_COVERAGE_BY_BODY.keys())
)


def _climatology_to_dict(m: BodyClimatology) -> Dict[str, Any]:
    return {
        "body": m.body,
        "has_atmosphere": m.has_atmosphere,
        "mean_surface_temperature_K": m.mean_surface_temperature_K,
        "mean_surface_pressure_Pa": m.mean_surface_pressure_Pa,
        "dominant_gases": (
            [list(pair) for pair in m.dominant_gases]
            if m.dominant_gases is not None else None
        ),
        "obliquity_deg": m.obliquity_deg,
        "orbital_eccentricity": m.orbital_eccentricity,
        "bond_albedo": m.bond_albedo,
        "notes": m.notes,
        "precision_flag": m.precision_flag,
        "source_key": m.source_key,
    }


def _archive_to_dict(m: FluidArchive) -> Dict[str, Any]:
    return {
        "body": m.body,
        "archive_name": m.archive_name,
        "archive_url": m.archive_url,
        "format": m.format,
        "access_protocol": m.access_protocol,
        "temporal_coverage_start_year": m.temporal_coverage_start_year,
        "temporal_coverage_end_year": m.temporal_coverage_end_year,
        "notes": m.notes,
        "precision_flag": m.precision_flag,
        "source_key": m.source_key,
    }


def _coverage_to_dict(m: FluidStateCoverage) -> Dict[str, Any]:
    return {
        "body": m.body,
        "has_state_at_epoch": m.has_state_at_epoch,
        "coverage_start_jd": m.coverage_start_jd,
        "coverage_end_jd": m.coverage_end_jd,
        "query_type": m.query_type,
        "notes": m.notes,
        "source_key": m.source_key,
    }


def compute_fluid_state(
    body: Optional[str] = None,
    jd_tdb: Optional[float] = None,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
) -> Dict[str, Any]:
    """Per-body fluid state query.

    Returns climatology + archive pointer index + state-at-epoch
    coverage triage for the requested body. **Does not make external
    HTTP calls** — the response is a self-contained dict with the
    archive endpoint + the climatological fallback; consumers fetch
    the actual reanalysis field via the archive's own API (CDS-API
    for ERA5, the Python wrapper for MCD).

    Parameters
    ----------
    body : str, optional. If given, return just that body's record.
        If omitted, return the full per-body catalog as a dict keyed
        by body name.
    jd_tdb : float, optional. Reserved — when given, the response
        adds a `coverage_status` flag relative to the body's archive
        coverage window (`in_coverage` / `before_archive` / `future`
        / `no_state_at_epoch`).
    lat : float, optional. Reserved for spatial query interface.
        Currently passed through unchanged (the body's archive
        endpoint accepts the lat/lon directly; this surface does
        not interpolate the field itself).
    lon : float, optional. Same.

    Returns
    -------
    dict
        Single body (`body=name`):
            ``{"ok": True, "body": str, "climatology": {...} or None,
              "archives": [...] or [], "state_coverage": {...} or None,
              "coverage_status": str (only if jd_tdb is given)}``
        Full roster (`body=None`):
            ``{"ok": True, "n_bodies": int, "bodies": {name: {...}}}``
    """
    if body is not None:
        name = str(body).lower().strip()
        if name not in _ALL_BODIES:
            return {
                "ok": False,
                "error": (
                    f"unknown body {body!r} in Sol Fluid Instrument; "
                    f"known bodies are {_ALL_BODIES}"
                ),
            }
        clim = _CLIMATOLOGY_BY_BODY.get(name)
        archives = _ARCHIVES_BY_BODY.get(name, [])
        cov = _COVERAGE_BY_BODY.get(name)

        out: Dict[str, Any] = {
            "ok": True,
            "body": name,
            "climatology": _climatology_to_dict(clim) if clim else None,
            "archives": [_archive_to_dict(a) for a in archives],
            "state_coverage": _coverage_to_dict(cov) if cov else None,
        }
        if lat is not None:
            out["lat"] = lat
        if lon is not None:
            out["lon"] = lon
        if jd_tdb is not None:
            if not math.isfinite(jd_tdb):
                return {"ok": False, "error": "jd_tdb must be finite"}
            out["jd_tdb"] = jd_tdb
            out["coverage_status"] = _coverage_status(cov, jd_tdb)
        return out

    # Full roster
    bodies: Dict[str, Dict[str, Any]] = {}
    for name in _ALL_BODIES:
        clim = _CLIMATOLOGY_BY_BODY.get(name)
        archives = _ARCHIVES_BY_BODY.get(name, [])
        cov = _COVERAGE_BY_BODY.get(name)
        bodies[name] = {
            "climatology": _climatology_to_dict(clim) if clim else None,
            "archives": [_archive_to_dict(a) for a in archives],
            "state_coverage": _coverage_to_dict(cov) if cov else None,
        }
    return {
        "ok": True,
        "n_bodies": len(_ALL_BODIES),
        "n_climatology_entries": len(BODY_CLIMATOLOGY),
        "n_archive_entries": len(FLUID_ARCHIVES),
        "n_coverage_entries": len(FLUID_STATE_COVERAGE),
        "bodies": bodies,
    }


def _coverage_status(cov: Optional[FluidStateCoverage],
                      jd_tdb: float) -> str:
    """Triage a JD against a coverage record."""
    if cov is None or not cov.has_state_at_epoch:
        return "no_state_at_epoch"
    start = cov.coverage_start_jd
    end = cov.coverage_end_jd
    if start is not None and jd_tdb < start:
        return "before_archive"
    if end is not None and jd_tdb > end:
        return "future"
    return "in_coverage"


def list_fluid_archives() -> Dict[str, Any]:
    """Return the full Sol Fluid Instrument archive enumeration.

    Returns every climatology entry, every archive pointer, every
    state-at-epoch coverage record. Each entry carries a `source_key`
    pointing into the `_research.fluid_instrument_data.SOURCES`
    citation dict so users can verify the provenance of every numeric
    value.
    """
    return {
        "ok": True,
        "n_climatology": len(BODY_CLIMATOLOGY),
        "n_archives": len(FLUID_ARCHIVES),
        "n_coverage": len(FLUID_STATE_COVERAGE),
        "n_sources": len(SOURCES),
        "n_bodies": len(_ALL_BODIES),
        "bodies": list(_ALL_BODIES),
        "climatology": [_climatology_to_dict(m) for m in BODY_CLIMATOLOGY],
        "archives": [_archive_to_dict(m) for m in FLUID_ARCHIVES],
        "coverage": [_coverage_to_dict(m) for m in FLUID_STATE_COVERAGE],
    }


def compute_fluid_architecture(
    target: Optional[str] = None,
) -> Dict[str, Any]:
    """Partition the catalog by per-body data-quality tier.

    Per the §17.1.6 ship-readiness convention, each body lands in a
    HIGH / MEDIUM / LOW / NONE tier based on its climatology
    `precision_flag`. Bodies with state-at-epoch coverage carry a
    `has_state_at_epoch` flag; bodies with archive holdings carry an
    `n_archives` count.

    Parameters
    ----------
    target : str, optional. Single-body lookup if given.

    Returns
    -------
    dict
        Full partition (`target=None`):
            ``{"ok": True, "n_bodies": int,
              "partitions": {tier: [body, ...]},
              "bodies": [{"name": str, "tier": str,
                          "has_atmosphere": bool,
                          "has_state_at_epoch": bool,
                          "n_archives": int}, ...]}``
        Single body (`target=name`):
            ``{"ok": True, "body": str, "tier": str,
              "has_atmosphere": bool, "has_state_at_epoch": bool,
              "n_archives": int}``
    """
    def _body_record(name: str) -> Dict[str, Any]:
        clim = _CLIMATOLOGY_BY_BODY.get(name)
        cov = _COVERAGE_BY_BODY.get(name)
        archives = _ARCHIVES_BY_BODY.get(name, [])
        return {
            "name": name,
            "tier": (clim.precision_flag if clim is not None
                     else PRECISION_NONE),
            "has_atmosphere": (clim.has_atmosphere if clim is not None
                               else False),
            "has_state_at_epoch": (cov.has_state_at_epoch if cov is not None
                                   else False),
            "n_archives": len(archives),
        }

    if target is not None:
        name = str(target).lower().strip()
        if name not in _ALL_BODIES:
            return {
                "ok": False,
                "error": (
                    f"unknown body {target!r} in Sol Fluid Instrument; "
                    f"known bodies are {_ALL_BODIES}"
                ),
            }
        rec = _body_record(name)
        return {
            "ok": True,
            "body": name,
            "tier": rec["tier"],
            "has_atmosphere": rec["has_atmosphere"],
            "has_state_at_epoch": rec["has_state_at_epoch"],
            "n_archives": rec["n_archives"],
        }

    body_records: List[Dict[str, Any]] = []
    partitions: Dict[str, List[str]] = {
        PRECISION_HIGH: [],
        PRECISION_MEDIUM: [],
        PRECISION_LOW: [],
        PRECISION_NONE: [],
    }
    for name in _ALL_BODIES:
        rec = _body_record(name)
        body_records.append(rec)
        partitions[rec["tier"]].append(name)

    return {
        "ok": True,
        "n_bodies": len(_ALL_BODIES),
        "partitions": partitions,
        "bodies": body_records,
    }


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "BODY_CLIMATOLOGY",
    "FLUID_ARCHIVES",
    "FLUID_STATE_COVERAGE",
    "SOURCES",
    "BodyClimatology",
    "FluidArchive",
    "FluidStateCoverage",
    "compute_fluid_state",
    "list_fluid_archives",
    "compute_fluid_architecture",
]
