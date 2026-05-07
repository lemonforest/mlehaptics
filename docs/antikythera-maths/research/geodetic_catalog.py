"""Sol Geodetic Catalog — state-lookup query surface for the
solar-system solid-body geodetic stack.

Promotes the v0.20.0 architectural commitment from research notebook
§17.1 + §17.4.2 to a stable ship surface, mirroring the v0.19.0 Sol
Electromagnetic Instrument pattern. **This is not a BIP encoder
running on geodetic rhythms** — solid-body geodetic observables are
static parameters with no native rhythm (per §17.4.1 the rhythm-
mismatch finding generalises across solid-body geodesy alongside
magnetic multipoles and fluid-envelope channels). The cyclic-group
encoder discipline does not transplant.

Instead this module is a **state-lookup query surface** holding three
internal channels per body:

* :data:`GRAVITY_MODELS` — per-body gravity multipole expansions
  (spherical-harmonic Stokes coefficients for terrestrial bodies and
  the Moon; zonal-only J_n series for the gas + ice giants).
* :data:`TOPOGRAPHY_MODELS` — per-body topography / shape model
  metadata (full-coverage DEMs for the inner solar system + the Moon;
  partial-coverage SARTopo for Titan; polyhedral shape models for the
  small-body roster).
* :data:`INTERIOR_MODELS` — per-body interior structure (radial
  density profiles, layered models, moment-of-inertia constraints;
  PREM / GRAIL+Apollo / InSight / JRM33-companion / Cassini Grand
  Finale ring-seismology / Voyager-derived for the ice giants).

Three bridge surfaces shape consumer access:

* :func:`compute_geodetic_state` — per-body (or full-roster) state
  query returning gravity + topography + interior records.
* :func:`list_geodetic_models` — full catalog enumeration (all three
  channels, all bodies).
* :func:`compute_geodetic_architecture` — partition by data-quality
  tier (HIGH / MEDIUM / LOW per the §17.1.6 ship-readiness convention).

The data tables are in :mod:`geodetic_catalog_data`. Citations live
in its `SOURCES` dict; every numeric value carries a `source_key`
pointing into that dict so users can verify the provenance.

Reference: research notebook §17.1 (the architectural scoping),
§17.4.2 (the v0.20.0 ship sequence), and §17.4.1 (the rhythm-
mismatch finding that motivates the state-lookup architecture).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from .geodetic_catalog_data import (
    GRAVITY_MODELS,
    INTERIOR_MODELS,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
    TOPOGRAPHY_MODELS,
    GravityModel,
    InteriorLayer,
    InteriorModel,
    TopographyModel,
)


# ---- Memoised lookups (built at module load — μs on the per-channel lists) -

_GRAVITY_BY_BODY: Dict[str, GravityModel] = {m.body: m for m in GRAVITY_MODELS}
_TOPOGRAPHY_BY_BODY: Dict[str, TopographyModel] = {m.body: m for m in TOPOGRAPHY_MODELS}
_INTERIOR_BY_BODY: Dict[str, InteriorModel] = {m.body: m for m in INTERIOR_MODELS}

# Union of all bodies that appear in any channel.
_ALL_BODIES: List[str] = sorted(
    set(_GRAVITY_BY_BODY.keys())
    | set(_TOPOGRAPHY_BY_BODY.keys())
    | set(_INTERIOR_BY_BODY.keys())
)


def _gravity_to_dict(m: GravityModel) -> Dict[str, Any]:
    return {
        "body": m.body,
        "model_name": m.model_name,
        "max_degree": m.max_degree,
        "reference_radius_km": m.reference_radius_km,
        "gm_km3_per_s2": m.gm_km3_per_s2,
        "J2": m.J2,
        "J3": m.J3,
        "J4": m.J4,
        "full_coeff_archive": m.full_coeff_archive,
        "precision_flag": m.precision_flag,
        "source_key": m.source_key,
    }


def _topography_to_dict(m: TopographyModel) -> Dict[str, Any]:
    return {
        "body": m.body,
        "model_name": m.model_name,
        "representation": m.representation,
        "horizontal_resolution_km": m.horizontal_resolution_km,
        "vertical_precision_m": m.vertical_precision_m,
        "coverage_fraction": m.coverage_fraction,
        "power_spectrum_slope": m.power_spectrum_slope,
        "archive_url": m.archive_url,
        "precision_flag": m.precision_flag,
        "source_key": m.source_key,
    }


def _interior_to_dict(m: InteriorModel) -> Dict[str, Any]:
    return {
        "body": m.body,
        "model_name": m.model_name,
        "total_radius_km": m.total_radius_km,
        "total_mass_kg": m.total_mass_kg,
        "normalised_moi": m.normalised_moi,
        "has_subsurface_ocean": m.has_subsurface_ocean,
        "layers": [
            {
                "name": layer.name,
                "inner_radius_km": layer.inner_radius_km,
                "outer_radius_km": layer.outer_radius_km,
                "mean_density_kg_per_m3": layer.mean_density_kg_per_m3,
                "composition": layer.composition,
            }
            for layer in m.layers
        ],
        "archive_url": m.archive_url,
        "precision_flag": m.precision_flag,
        "source_key": m.source_key,
    }


def compute_geodetic_state(
    body: Optional[str] = None,
) -> Dict[str, Any]:
    """Return per-body geodetic state (gravity + topography + interior).

    Parameters
    ----------
    body : str, optional. If given, return just that body's records.
        If omitted, return the full per-body catalog as a dict keyed
        by body name with each value a `(gravity, topography, interior)`
        record sub-dict.

    Returns
    -------
    dict
        Single body (`body=name`):
            ``{"ok": True, "body": str, "gravity": {...} or None,
              "topography": {...} or None, "interior": {...} or None}``
        Full roster (`body=None`):
            ``{"ok": True, "n_bodies": int, "bodies": {name: {...}}}``
        On error:
            ``{"ok": False, "error": "..."}``

    Bodies missing a particular channel return `None` for that channel
    rather than raising — the catalog is sparse by design (not every
    body has a published interior model, for example).
    """
    if body is not None:
        name = str(body).lower().strip()
        if name not in _ALL_BODIES:
            return {
                "ok": False,
                "error": (
                    f"unknown body {body!r} in Sol Geodetic Catalog; "
                    f"known bodies are {_ALL_BODIES}"
                ),
            }
        return {
            "ok": True,
            "body": name,
            "gravity": (
                _gravity_to_dict(_GRAVITY_BY_BODY[name])
                if name in _GRAVITY_BY_BODY else None
            ),
            "topography": (
                _topography_to_dict(_TOPOGRAPHY_BY_BODY[name])
                if name in _TOPOGRAPHY_BY_BODY else None
            ),
            "interior": (
                _interior_to_dict(_INTERIOR_BY_BODY[name])
                if name in _INTERIOR_BY_BODY else None
            ),
        }

    # Full roster
    bodies: Dict[str, Dict[str, Any]] = {}
    for name in _ALL_BODIES:
        bodies[name] = {
            "gravity": (
                _gravity_to_dict(_GRAVITY_BY_BODY[name])
                if name in _GRAVITY_BY_BODY else None
            ),
            "topography": (
                _topography_to_dict(_TOPOGRAPHY_BY_BODY[name])
                if name in _TOPOGRAPHY_BY_BODY else None
            ),
            "interior": (
                _interior_to_dict(_INTERIOR_BY_BODY[name])
                if name in _INTERIOR_BY_BODY else None
            ),
        }
    return {
        "ok": True,
        "n_bodies": len(_ALL_BODIES),
        "bodies": bodies,
    }


def list_geodetic_models() -> Dict[str, Any]:
    """Return the full catalog enumeration — every model in every channel."""
    return {
        "ok": True,
        "n_gravity_models": len(GRAVITY_MODELS),
        "n_topography_models": len(TOPOGRAPHY_MODELS),
        "n_interior_models": len(INTERIOR_MODELS),
        "n_sources": len(SOURCES),
        "n_bodies": len(_ALL_BODIES),
        "bodies": list(_ALL_BODIES),
        "gravity": [_gravity_to_dict(m) for m in GRAVITY_MODELS],
        "topography": [_topography_to_dict(m) for m in TOPOGRAPHY_MODELS],
        "interior": [_interior_to_dict(m) for m in INTERIOR_MODELS],
    }


def compute_geodetic_architecture(
    target: Optional[str] = None,
) -> Dict[str, Any]:
    """Partition the catalog by per-body data-quality tier.

    Per the §17.1.6 ship-readiness convention, each body lands in a
    HIGH / MEDIUM / LOW / NONE tier based on the *worst* precision
    flag across its three channels. A body with HIGH gravity but LOW
    interior is summarised as MEDIUM (taking the median).

    Parameters
    ----------
    target : str, optional. Single-body lookup if given.

    Returns
    -------
    dict
        Full partition (`target=None`):
            ``{"ok": True, "n_bodies": int, "partitions": {tier: [body, ...]},
              "bodies": [{"name": str, "tier": str, ...}, ...]}``
        Single body (`target=name`):
            ``{"ok": True, "body": str, "tier": str, "channel_flags": {...}}``
    """
    def _body_tier(name: str) -> tuple[str, Dict[str, Optional[str]]]:
        flags: Dict[str, Optional[str]] = {
            "gravity": (
                _GRAVITY_BY_BODY[name].precision_flag
                if name in _GRAVITY_BY_BODY else None
            ),
            "topography": (
                _TOPOGRAPHY_BY_BODY[name].precision_flag
                if name in _TOPOGRAPHY_BY_BODY else None
            ),
            "interior": (
                _INTERIOR_BY_BODY[name].precision_flag
                if name in _INTERIOR_BY_BODY else None
            ),
        }
        # Tier ordering: HIGH > MEDIUM > LOW > NONE.
        order = {
            PRECISION_HIGH: 3,
            PRECISION_MEDIUM: 2,
            PRECISION_LOW: 1,
            PRECISION_NONE: 0,
        }
        present = [order.get(f, 0) for f in flags.values() if f is not None]
        if not present:
            return PRECISION_NONE, flags
        # Median tier across present channels.
        present.sort()
        median = present[len(present) // 2]
        for tier, value in order.items():
            if value == median:
                return tier, flags
        return PRECISION_NONE, flags

    if target is not None:
        name = str(target).lower().strip()
        if name not in _ALL_BODIES:
            return {
                "ok": False,
                "error": (
                    f"unknown body {target!r} in Sol Geodetic Catalog; "
                    f"known bodies are {_ALL_BODIES}"
                ),
            }
        tier, flags = _body_tier(name)
        return {
            "ok": True,
            "body": name,
            "tier": tier,
            "channel_flags": flags,
        }

    # Full partition.
    body_records = []
    partitions: Dict[str, List[str]] = {
        PRECISION_HIGH: [],
        PRECISION_MEDIUM: [],
        PRECISION_LOW: [],
        PRECISION_NONE: [],
    }
    for name in _ALL_BODIES:
        tier, flags = _body_tier(name)
        body_records.append({
            "name": name,
            "tier": tier,
            "channel_flags": flags,
        })
        partitions[tier].append(name)

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
    "GRAVITY_MODELS",
    "TOPOGRAPHY_MODELS",
    "INTERIOR_MODELS",
    "SOURCES",
    "GravityModel",
    "TopographyModel",
    "InteriorLayer",
    "InteriorModel",
    "compute_geodetic_state",
    "list_geodetic_models",
    "compute_geodetic_architecture",
]
