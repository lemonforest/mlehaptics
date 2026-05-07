"""Sol Magnetic Multipole Catalog — state-lookup query surface for the
solar-system internal-field roster.

Promotes the v0.20.1 architectural commitment from research notebook
§17.2 + §17.4.2 to a stable ship surface, mirroring the v0.19.0 Sol
Electromagnetic Instrument and v0.20.0 Sol Geodetic Catalog patterns.
**This is not a BIP encoder running on magnetic-field rhythms** — per
§17.4.1 the rhythm-mismatch finding generalises across magnetic
multipoles alongside solid-body geodesy and fluid-envelope channels:
internal-field Schmidt-normalised g_n^m / h_n^m coefficients are
static parameters at their epoch (the IGRF main field updates every
5 years on a published schedule; JRM33 is a Juno-prime-mission
snapshot; Voyager-derived AH5/O8 are single-flyby fits). The cyclic-
group encoder discipline does not transplant.

Instead this module is a **state-lookup query surface** holding three
internal channels:

* :data:`MAGNETIC_MULTIPOLE_MODELS` — per-body internal-field
  spherical-harmonic expansions in Schmidt quasi-normalisation
  (geomagnetic convention; not 4π-normalised geodesy convention).
* :data:`CRUSTAL_FIELD_MODELS` — per-body crustal anomaly fields
  (currently Earth EMM2017 only; Mars / Mercury crustal models
  candidates for future minor versions).
* :data:`SOLAR_SYNOPTIC_REFERENCES` — pointers into Stanford HMI /
  Wilcox Solar Observatory synoptic-magnetogram archives (the Sun's
  field is time-varying; lives behind a different surface).

Three bridge surfaces shape consumer access:

* :func:`compute_magnetic_multipoles` — per-body multipole expansion
  query (returns Schmidt coefficients + dipole headline).
* :func:`evaluate_magnetic_field` — vector field at (r, lat, lon)
  evaluated against the per-body multipole expansion (Schmidt
  quasi-normalised spherical-harmonic synthesis).
* :func:`compute_solar_synoptic_state` — Sun synoptic-state pointer
  surface (returns archive + cadence + the JD-aware coverage flag;
  the actual time-variable field lives in the external archive, not
  in the package wheel).

The data tables are in :mod:`magnetic_multipole_catalog_data`.
Citations live in its `SOURCES` dict; every numeric value carries a
`source_key` pointing into that dict so users can verify the
provenance.

Reference: research notebook §17.2 (the architectural scoping for
magnetic multipoles), §17.4.2 (the v0.20.1 ship sequence), and
§17.4.1 (the rhythm-mismatch finding that motivates the state-lookup
architecture).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from .magnetic_multipole_catalog_data import (
    CRUSTAL_FIELD_MODELS,
    MAGNETIC_MULTIPOLE_MODELS,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOLAR_SYNOPTIC_REFERENCES,
    SOURCES,
    CrustalFieldModel,
    MagneticMultipoleModel,
    SolarSynopticReference,
)


# ---- Memoised lookups (built at module load — μs on the per-body lists) ----

_MULTIPOLE_BY_BODY: Dict[str, MagneticMultipoleModel] = {
    m.body: m for m in MAGNETIC_MULTIPOLE_MODELS
}
_CRUSTAL_BY_BODY: Dict[str, CrustalFieldModel] = {
    m.body: m for m in CRUSTAL_FIELD_MODELS
}
_SYNOPTIC_BY_BODY: Dict[str, SolarSynopticReference] = {
    m.body: m for m in SOLAR_SYNOPTIC_REFERENCES
}

# Union of all bodies that have a magnetic-channel record of any kind.
_ALL_BODIES: List[str] = sorted(
    set(_MULTIPOLE_BY_BODY.keys())
    | set(_CRUSTAL_BY_BODY.keys())
    | set(_SYNOPTIC_BY_BODY.keys())
)


def _multipole_to_dict(m: MagneticMultipoleModel) -> Dict[str, Any]:
    return {
        "body": m.body,
        "model_name": m.model_name,
        "max_degree": m.max_degree,
        "reference_radius_km": m.reference_radius_km,
        "epoch_year": m.epoch_year,
        "g10_nT": m.g10_nT,
        "g11_nT": m.g11_nT,
        "h11_nT": m.h11_nT,
        "dipole_moment_T_m3": m.dipole_moment_T_m3,
        "dipole_tilt_deg": m.dipole_tilt_deg,
        "dipole_offset_km": m.dipole_offset_km,
        "full_coeff_archive": m.full_coeff_archive,
        "precision_flag": m.precision_flag,
        "structural_flag": m.structural_flag,
        "source_key": m.source_key,
    }


def _crustal_to_dict(m: CrustalFieldModel) -> Dict[str, Any]:
    return {
        "body": m.body,
        "model_name": m.model_name,
        "max_degree": m.max_degree,
        "reference_radius_km": m.reference_radius_km,
        "archive_url": m.archive_url,
        "file_size_mb": m.file_size_mb,
        "precision_flag": m.precision_flag,
        "source_key": m.source_key,
    }


def _synoptic_to_dict(m: SolarSynopticReference) -> Dict[str, Any]:
    return {
        "body": m.body,
        "decomposition_name": m.decomposition_name,
        "cadence_days": m.cadence_days,
        "archive_url": m.archive_url,
        "coverage_start_year": m.coverage_start_year,
        "coverage_end_year": m.coverage_end_year,
        "typical_max_degree": m.typical_max_degree,
        "source_key": m.source_key,
    }


def compute_magnetic_multipoles(
    body: Optional[str] = None,
    crustal: bool = False,
) -> Dict[str, Any]:
    """Return per-body magnetic multipole records.

    Parameters
    ----------
    body : str, optional. If given, return just that body's record.
        If omitted, return the full per-body catalog as a dict keyed
        by body name.
    crustal : bool, default False. If True and the requested body has
        a crustal field model on file (currently Earth only), the
        crustal record is included alongside the main-field record.

    Returns
    -------
    dict
        Single body (`body=name`):
            ``{"ok": True, "body": str, "main_field": {...} or None,
              "crustal_field": {...} or None}``
        Full roster (`body=None`):
            ``{"ok": True, "n_bodies": int, "bodies": {name: {...}}}``
        On error:
            ``{"ok": False, "error": "..."}``

    Bodies missing a particular channel return `None` rather than
    raising — the catalog is sparse by design (only Earth has a
    published deg-720 crustal anomaly model in v0.20.1).
    """
    if body is not None:
        name = str(body).lower().strip()
        if name not in _ALL_BODIES:
            return {
                "ok": False,
                "error": (
                    f"unknown body {body!r} in Sol Magnetic Multipole "
                    f"Catalog; known bodies are {_ALL_BODIES}"
                ),
            }
        main = _MULTIPOLE_BY_BODY.get(name)
        crust = _CRUSTAL_BY_BODY.get(name) if crustal else None
        return {
            "ok": True,
            "body": name,
            "main_field": _multipole_to_dict(main) if main else None,
            "crustal_field": _crustal_to_dict(crust) if crust else None,
        }

    # Full roster
    bodies: Dict[str, Dict[str, Any]] = {}
    for name in _ALL_BODIES:
        main = _MULTIPOLE_BY_BODY.get(name)
        crust = _CRUSTAL_BY_BODY.get(name) if crustal else None
        bodies[name] = {
            "main_field": _multipole_to_dict(main) if main else None,
            "crustal_field": _crustal_to_dict(crust) if crust else None,
        }
    return {
        "ok": True,
        "n_bodies": len(_ALL_BODIES),
        "n_multipole_models": len(MAGNETIC_MULTIPOLE_MODELS),
        "n_crustal_models": len(CRUSTAL_FIELD_MODELS),
        "bodies": bodies,
    }


def evaluate_magnetic_field(
    body: str,
    r_km: float,
    lat_deg: float,
    lon_deg: float,
    jd_tdb: Optional[float] = None,
) -> Dict[str, Any]:
    """Evaluate the vector magnetic field at (r, lat, lon) using the
    per-body multipole expansion (dipole-only synthesis in v0.20.1).

    Closed-form dipole synthesis from Schmidt-quasi-normalised
    coefficients. Higher-degree synthesis is left for v0.20.x or a
    future minor version — the v0.20.1 ship surface returns the
    dipole approximation, which is the dominant contribution beyond
    a few body-radii for every body in the roster.

    Parameters
    ----------
    body : str. Lower-case body name (must be in the multipole roster).
    r_km : float. Radial distance from body centre, in km. Must be
        > 0; values inside the body surface are accepted but flagged.
    lat_deg : float. Geocentric latitude, degrees, [-90, 90].
    lon_deg : float. Longitude, degrees (body-fixed frame; for Earth
        this is the IGRF geodetic convention).
    jd_tdb : float, optional. Currently ignored (v0.20.1 returns the
        epoch-fixed dipole; secular variation is a candidate for a
        future minor version). Reserved for forward compatibility.

    Returns
    -------
    dict
        ``{"ok": True, "body": str, "B_r_nT": float, "B_theta_nT": float,
          "B_phi_nT": float, "B_total_nT": float, "epoch_year": float,
          "synthesis_degree": int, "below_surface": bool}``
    """
    if not (math.isfinite(r_km) and math.isfinite(lat_deg)
            and math.isfinite(lon_deg)):
        return {"ok": False, "error": "r_km / lat_deg / lon_deg must be finite"}
    if r_km <= 0:
        return {"ok": False, "error": "r_km must be positive"}

    name = str(body).lower().strip()
    m = _MULTIPOLE_BY_BODY.get(name)
    if m is None:
        return {
            "ok": False,
            "error": (
                f"body {body!r} has no published multipole model "
                f"in Sol Magnetic Multipole Catalog; known bodies "
                f"are {sorted(_MULTIPOLE_BY_BODY.keys())}"
            ),
        }

    # Schmidt-quasi-normalised dipole synthesis at (r, lat, lon).
    # Convention: B_r = 2 (R/r)^3 [g10 cos θ + (g11 cos φ + h11 sin φ) sin θ]
    #             B_θ =   (R/r)^3 [g10 sin θ - (g11 cos φ + h11 sin φ) cos θ]
    #             B_φ =   (R/r)^3 [(g11 sin φ - h11 cos φ)]
    # where θ = colatitude (90° - lat), φ = lon, and the g/h are nT.
    R = m.reference_radius_km
    ratio_cubed = (R / r_km) ** 3
    colat = math.radians(90.0 - lat_deg)
    lon = math.radians(lon_deg)
    sin_t, cos_t = math.sin(colat), math.cos(colat)
    sin_p, cos_p = math.sin(lon), math.cos(lon)

    g10 = m.g10_nT or 0.0
    g11 = m.g11_nT or 0.0
    h11 = m.h11_nT or 0.0

    horiz = g11 * cos_p + h11 * sin_p
    horiz_orth = g11 * sin_p - h11 * cos_p

    B_r = 2.0 * ratio_cubed * (g10 * cos_t + horiz * sin_t)
    B_theta = ratio_cubed * (g10 * sin_t - horiz * cos_t)
    B_phi = ratio_cubed * horiz_orth
    B_total = math.sqrt(B_r * B_r + B_theta * B_theta + B_phi * B_phi)

    return {
        "ok": True,
        "body": name,
        "B_r_nT": B_r,
        "B_theta_nT": B_theta,
        "B_phi_nT": B_phi,
        "B_total_nT": B_total,
        "epoch_year": m.epoch_year,
        "synthesis_degree": 1,  # dipole-only in v0.20.1
        "below_surface": r_km < R,
    }


def compute_solar_synoptic_state(
    jd_tdb: Optional[float] = None,
) -> Dict[str, Any]:
    """Sun synoptic-state pointer surface.

    The Sun's internal field is time-varying with a ~22-yr Hale cycle
    (modulated by the ~11-yr sunspot cycle); a single static set of
    Schmidt coefficients is not the right representation. Instead the
    package ships a pointer into the published synoptic-magnetogram
    archive (Stanford HMI / Wilcox Solar Observatory) so consumers
    can pull the correct Carrington-rotation-cadence field for a
    specific JD outside the package itself.

    Parameters
    ----------
    jd_tdb : float, optional. If given, the response includes a
        `coverage_status` field of `"in_coverage"` / `"before_archive"`
        / `"future"` based on the archive's start year and current JD.

    Returns
    -------
    dict
        ``{"ok": True, "body": "sun", "n_archives": int,
          "archives": [{...}], "coverage_status": str, ...}``
    """
    if not _SYNOPTIC_BY_BODY:
        return {"ok": False, "error": "no solar synoptic references on file"}

    archives = [
        _synoptic_to_dict(_SYNOPTIC_BY_BODY[name])
        for name in sorted(_SYNOPTIC_BY_BODY.keys())
    ]
    out: Dict[str, Any] = {
        "ok": True,
        "body": "sun",
        "n_archives": len(archives),
        "archives": archives,
    }

    if jd_tdb is not None:
        if not math.isfinite(jd_tdb):
            return {"ok": False, "error": "jd_tdb must be finite"}
        # Approximate the requested year from JD_TDB by Julian-year
        # arithmetic (the synoptic archives are Carrington-rotation-
        # indexed; year-precision is fine for coverage triage).
        year_at_jd = 2000.0 + (jd_tdb - 2451545.0) / 365.25
        coverage_starts = [a["coverage_start_year"] for a in archives]
        coverage_ends = [
            a["coverage_end_year"] if a["coverage_end_year"] is not None
            else year_at_jd + 1.0  # treat None as "ongoing through now"
            for a in archives
        ]
        if year_at_jd < min(coverage_starts):
            status = "before_archive"
        elif any(s <= year_at_jd <= e for s, e in zip(coverage_starts, coverage_ends)):
            status = "in_coverage"
        else:
            status = "future"
        out["jd_tdb"] = jd_tdb
        out["year_at_jd"] = year_at_jd
        out["coverage_status"] = status

    return out


def list_magnetic_multipoles() -> Dict[str, Any]:
    """Return the full catalog enumeration — every published magnetic
    multipole model + every crustal field model + every solar synoptic
    reference."""
    return {
        "ok": True,
        "n_multipole_models": len(MAGNETIC_MULTIPOLE_MODELS),
        "n_crustal_models": len(CRUSTAL_FIELD_MODELS),
        "n_solar_synoptic_references": len(SOLAR_SYNOPTIC_REFERENCES),
        "n_sources": len(SOURCES),
        "n_bodies": len(_ALL_BODIES),
        "bodies": list(_ALL_BODIES),
        "multipoles": [_multipole_to_dict(m) for m in MAGNETIC_MULTIPOLE_MODELS],
        "crustal": [_crustal_to_dict(m) for m in CRUSTAL_FIELD_MODELS],
        "solar_synoptic": [
            _synoptic_to_dict(m) for m in SOLAR_SYNOPTIC_REFERENCES
        ],
    }


def compute_magnetic_architecture(
    target: Optional[str] = None,
) -> Dict[str, Any]:
    """Partition the catalog by per-body data-quality tier.

    Per the §17.1.6 ship-readiness convention, each body lands in a
    HIGH / MEDIUM / LOW / NONE tier based on its main-field
    `precision_flag`. Bodies with crustal-field coverage carry a
    `has_crustal` flag.

    Parameters
    ----------
    target : str, optional. Single-body lookup if given.

    Returns
    -------
    dict
        Full partition (`target=None`):
            ``{"ok": True, "n_bodies": int,
              "partitions": {tier: [body, ...]},
              "bodies": [{"name": str, "tier": str, "has_crustal": bool}, ...]}``
        Single body (`target=name`):
            ``{"ok": True, "body": str, "tier": str, "has_crustal": bool,
              "structural_flag": Optional[str]}``
    """

    def _body_tier(name: str) -> Dict[str, Any]:
        m = _MULTIPOLE_BY_BODY.get(name)
        tier = m.precision_flag if m is not None else PRECISION_NONE
        return {
            "name": name,
            "tier": tier,
            "has_crustal": name in _CRUSTAL_BY_BODY,
            "structural_flag": m.structural_flag if m is not None else None,
        }

    if target is not None:
        name = str(target).lower().strip()
        if name not in _ALL_BODIES:
            return {
                "ok": False,
                "error": (
                    f"unknown body {target!r} in Sol Magnetic Multipole "
                    f"Catalog; known bodies are {_ALL_BODIES}"
                ),
            }
        rec = _body_tier(name)
        return {
            "ok": True,
            "body": name,
            "tier": rec["tier"],
            "has_crustal": rec["has_crustal"],
            "structural_flag": rec["structural_flag"],
        }

    # Full partition.
    body_records: List[Dict[str, Any]] = []
    partitions: Dict[str, List[str]] = {
        PRECISION_HIGH: [],
        PRECISION_MEDIUM: [],
        PRECISION_LOW: [],
        PRECISION_NONE: [],
    }
    for name in _ALL_BODIES:
        rec = _body_tier(name)
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
    "MAGNETIC_MULTIPOLE_MODELS",
    "CRUSTAL_FIELD_MODELS",
    "SOLAR_SYNOPTIC_REFERENCES",
    "SOURCES",
    "MagneticMultipoleModel",
    "CrustalFieldModel",
    "SolarSynopticReference",
    "compute_magnetic_multipoles",
    "evaluate_magnetic_field",
    "compute_solar_synoptic_state",
    "list_magnetic_multipoles",
    "compute_magnetic_architecture",
]
