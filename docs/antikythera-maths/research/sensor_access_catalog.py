"""Sensor Access Catalog — query surface for the v0.22.0 trajectory +
sensing ship (Layer C(a): SGP4 + look-angle access geometry).

Promotes the v0.22.0 architectural commitment from research notebook
§17.5.3 to a stable ship surface — **Layer C(a)** of the four-layer
trajectory + sensing surface.

Cross-channel reach: complements Layer A/B trajectory propagators
with the orbital-asset-positioning geometry that answers "can asset X
geometrically observe target Y?" SGP4 propagation is delegated to
Brandon Rhodes' ``sgp4`` package when available; without it, this
module degrades to pure look-angle geometry on user-supplied state
vectors.

**Not a re-derivation.** Look-angle geometry from Vallado Ch. 11.
SGP4/SDP4 propagator is the public NORAD model (Vallado et al. 2006
revisitation; Rhodes' Python implementation). IR transmission windows
are HITRAN-canonical bands. **No specific RV signatures, no specific
sensor sensitivities, no targeting capability claims.** Publishable
textbook geometry only.

Three bridge surfaces:

* :func:`compute_visibility_geometry` — slant range + elevation +
  azimuth + occlusion test.
* :func:`get_orbital_reference` / :func:`list_orbital_references` —
  reference TLE catalog access.
* :func:`compute_sgp4_state` — TLE → state vector via ``sgp4`` if
  available.

Reference: research notebook §17.5.3.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from .sensor_access_data import (
    EARTH_RADIUS_OCCLUSION_M,
    LWIR_LOWER_UM, LWIR_UPPER_UM,
    MWIR_LOWER_UM, MWIR_UPPER_UM,
    NIR_LOWER_UM, NIR_UPPER_UM,
    ORBITAL_REFERENCES,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
    VIS_LOWER_UM, VIS_UPPER_UM,
    WGS84_A_M, WGS84_B_M, WGS84_F,
    OrbitalReferenceTLE,
)


# ---- Memoised lookups (built at module load) -------------------------

_BY_LABEL: Dict[str, OrbitalReferenceTLE] = {
    r.label: r for r in ORBITAL_REFERENCES
}
_BY_NORAD: Dict[int, OrbitalReferenceTLE] = {
    r.norad_cat_id: r for r in ORBITAL_REFERENCES
}
_ALL_LABELS: List[str] = sorted(_BY_LABEL.keys())


def _ref_to_dict(r: OrbitalReferenceTLE) -> Dict[str, Any]:
    return {
        "label": r.label,
        "norad_cat_id": r.norad_cat_id,
        "orbit_class": r.orbit_class,
        "line1": r.line1,
        "line2": r.line2,
        "inclination_deg": r.inclination_deg,
        "period_min": r.period_min,
        "apogee_km": r.apogee_km,
        "perigee_km": r.perigee_km,
        "precision_flag": r.precision_flag,
        "notes": r.notes,
        "source_key": r.source_key,
    }


# ---------------------------------------------------------------------------
# Coordinate transforms (Vallado Ch. 3 + Ch. 11)
# ---------------------------------------------------------------------------


def _geodetic_to_ecef(
    lat_deg: float, lon_deg: float, alt_m: float,
) -> Tuple[float, float, float]:
    """WGS-84 geodetic (lat, lon, alt) → ECEF (x, y, z) meters."""
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    e2 = WGS84_F * (2.0 - WGS84_F)  # squared eccentricity
    sin_lat = math.sin(lat)
    N = WGS84_A_M / math.sqrt(1.0 - e2 * sin_lat * sin_lat)
    x = (N + alt_m) * math.cos(lat) * math.cos(lon)
    y = (N + alt_m) * math.cos(lat) * math.sin(lon)
    z = (N * (1.0 - e2) + alt_m) * sin_lat
    return x, y, z


def _ecef_to_enu_at(
    target_lat_deg: float, target_lon_deg: float,
    dx: float, dy: float, dz: float,
) -> Tuple[float, float, float]:
    """ECEF delta vector → ENU (East-North-Up) at target lat/lon.

    Standard rotation matrix (Vallado §3.3).
    """
    lat = math.radians(target_lat_deg)
    lon = math.radians(target_lon_deg)
    sl, cl = math.sin(lat), math.cos(lat)
    so, co = math.sin(lon), math.cos(lon)

    east = -so * dx + co * dy
    north = -sl * co * dx - sl * so * dy + cl * dz
    up = cl * co * dx + cl * so * dy + sl * dz
    return east, north, up


def _enu_to_az_el_range(
    east: float, north: float, up: float,
) -> Tuple[float, float, float]:
    """ENU vector → (azimuth_deg, elevation_deg, slant_range_m)."""
    slant_range = math.sqrt(east * east + north * north + up * up)
    if slant_range < 1e-9:
        return 0.0, 90.0, 0.0
    elevation = math.degrees(math.asin(up / slant_range))
    azimuth = math.degrees(math.atan2(east, north)) % 360.0
    return azimuth, elevation, slant_range


def _line_segment_occluded_by_earth(
    sat_ecef: Tuple[float, float, float],
    tgt_ecef: Tuple[float, float, float],
) -> bool:
    """Check whether the line segment from satellite to target passes
    through the solid Earth.

    Standard ray-sphere intersection with the Earth's mean radius.
    Returns True if line-of-sight is occluded.
    """
    px, py, pz = sat_ecef
    qx, qy, qz = tgt_ecef
    dx, dy, dz = qx - px, qy - py, qz - pz
    # Find closest approach to origin along segment t ∈ [0, 1]:
    #   |P + t·D|² = closest when t = -P·D / |D|²
    d_dot_d = dx * dx + dy * dy + dz * dz
    if d_dot_d < 1e-9:
        return False
    p_dot_d = px * dx + py * dy + pz * dz
    t_closest = -p_dot_d / d_dot_d
    # If closest approach is outside segment, no Earth occlusion
    # along the segment itself
    if t_closest <= 0.0 or t_closest >= 1.0:
        return False
    # Closest point on segment to Earth center
    cx = px + t_closest * dx
    cy = py + t_closest * dy
    cz = pz + t_closest * dz
    closest_dist = math.sqrt(cx * cx + cy * cy + cz * cz)
    return closest_dist < EARTH_RADIUS_OCCLUSION_M


# ---------------------------------------------------------------------------
# Public bridge surfaces
# ---------------------------------------------------------------------------


def compute_visibility_geometry(
    sat_ecef_m: Tuple[float, float, float],
    target_lat_deg: float,
    target_lon_deg: float,
    target_altitude_m: float = 0.0,
    minimum_elevation_deg: float = 5.0,
) -> Dict[str, Any]:
    """Per-instant visibility geometry: satellite ECEF → target lat/lon.

    Computes slant range, elevation above target's local horizontal,
    azimuth in the target's ENU frame, and Earth-limb occlusion.
    Returns ``visible=True`` iff elevation ≥ minimum_elevation_deg AND
    line-of-sight is not occluded by the Earth.

    Parameters
    ----------
    sat_ecef_m : (x, y, z)
        Satellite Earth-Centered Earth-Fixed position (meters).
    target_lat_deg : float
        Target geodetic latitude (degrees).
    target_lon_deg : float
        Target geodetic longitude (degrees, east-positive).
    target_altitude_m : float, default 0.0
        Target altitude above WGS-84 ellipsoid (meters).
    minimum_elevation_deg : float, default 5.0
        Minimum elevation above target horizon for visibility flag.
        5° is the textbook reference (atmospheric refraction
        + low-elevation noise floor).

    Returns
    -------
    dict
        ``{ok, slant_range_m, slant_range_km, azimuth_deg,
        elevation_deg, occluded_by_earth, visible}``.

    References
    ----------
    Vallado D. A. (2013). *Fundamentals of Astrodynamics*, 4th ed.,
    §3.3 (coordinate transforms) + Ch. 11 (look-angle geometry).
    """
    tx, ty, tz = _geodetic_to_ecef(
        target_lat_deg, target_lon_deg, target_altitude_m,
    )
    sx, sy, sz = sat_ecef_m
    dx, dy, dz = sx - tx, sy - ty, sz - tz

    east, north, up = _ecef_to_enu_at(
        target_lat_deg, target_lon_deg, dx, dy, dz,
    )
    azimuth, elevation, slant_range = _enu_to_az_el_range(east, north, up)
    occluded = _line_segment_occluded_by_earth(
        (sx, sy, sz), (tx, ty, tz),
    )
    visible = (elevation >= minimum_elevation_deg) and (not occluded)

    return {
        "ok": True,
        "slant_range_m": slant_range,
        "slant_range_km": slant_range / 1000.0,
        "azimuth_deg": azimuth,
        "elevation_deg": elevation,
        "occluded_by_earth": occluded,
        "visible": visible,
        "minimum_elevation_deg": minimum_elevation_deg,
    }


def compute_sgp4_state(
    line1: str,
    line2: str,
    minutes_since_epoch: float = 0.0,
) -> Dict[str, Any]:
    """Propagate a TLE via SGP4/SDP4 to obtain ECI position/velocity.

    Delegates to Brandon Rhodes' ``sgp4`` package when available
    (install via ``pip install ephemerides-spectral[ephemeris]`` —
    Skyfield brings ``sgp4`` transitively). When the package is not
    available, returns ``ok=False`` with a degradation message.

    Parameters
    ----------
    line1, line2 : str
        Two-line-element set (NORAD format).
    minutes_since_epoch : float, default 0.0
        Minutes past the TLE epoch (positive forward in time).

    Returns
    -------
    dict
        ``{ok, position_eci_m: (x, y, z), velocity_eci_m_s: (vx, vy, vz),
        epoch_jd, error}``. Position in meters (sgp4 returns km — we
        convert), velocity in m/s.

    References
    ----------
    Hoots F. R., Roehrich R. L. (1980). Spacetrack Report #3 (SGP4
    canonical reference).

    Vallado D. A., Crawford P., Hujsak R., Kelso T. S. (2006).
    Revisiting Spacetrack Report #3, AIAA 2006-6753.
    """
    try:
        from sgp4.api import Satrec  # type: ignore
    except ImportError:
        return {
            "ok": False,
            "error": (
                "sgp4 package not installed; install "
                "`ephemerides-spectral[ephemeris]` to enable SGP4 "
                "propagation."
            ),
        }

    sat = Satrec.twoline2rv(line1, line2)
    jd_epoch = sat.jdsatepoch + sat.jdsatepochF
    jd_target = jd_epoch + minutes_since_epoch / 1440.0
    jd_int = math.floor(jd_target)
    jd_frac = jd_target - jd_int
    err, r_km, v_km_s = sat.sgp4(jd_int, jd_frac)
    if err != 0:
        return {
            "ok": False,
            "error": f"SGP4 propagation error code {err}",
            "epoch_jd": jd_epoch,
        }

    return {
        "ok": True,
        "position_eci_m": (r_km[0] * 1000.0, r_km[1] * 1000.0, r_km[2] * 1000.0),
        "velocity_eci_m_s": (v_km_s[0] * 1000.0, v_km_s[1] * 1000.0, v_km_s[2] * 1000.0),
        "epoch_jd": jd_epoch,
        "minutes_since_epoch": minutes_since_epoch,
    }


def get_orbital_reference(label: Optional[str] = None) -> Dict[str, Any]:
    """Reference TLE lookup by label (e.g. "ISS (ZARYA)").

    These are textbook reference TLEs — fetch fresh ones from
    CelesTrak / Space-Track for operational use.
    """
    if label is not None:
        if label not in _BY_LABEL:
            return {
                "ok": False,
                "error": (
                    f"unknown reference {label!r}; known references "
                    f"are {_ALL_LABELS}"
                ),
            }
        return {
            "ok": True,
            "label": label,
            "reference": _ref_to_dict(_BY_LABEL[label]),
        }

    return {
        "ok": True,
        "n_references": len(_ALL_LABELS),
        "references": {
            lbl: _ref_to_dict(_BY_LABEL[lbl]) for lbl in _ALL_LABELS
        },
    }


def list_orbital_references() -> Dict[str, Any]:
    """Full enumeration of orbital reference TLEs + IR window
    constants + citations."""
    return {
        "ok": True,
        "n_references": len(_ALL_LABELS),
        "n_sources": len(SOURCES),
        "references": [_ref_to_dict(r) for r in ORBITAL_REFERENCES],
        "ir_windows": {
            "vis": {"lower_um": VIS_LOWER_UM, "upper_um": VIS_UPPER_UM},
            "nir": {"lower_um": NIR_LOWER_UM, "upper_um": NIR_UPPER_UM},
            "mwir": {"lower_um": MWIR_LOWER_UM, "upper_um": MWIR_UPPER_UM},
            "lwir": {"lower_um": LWIR_LOWER_UM, "upper_um": LWIR_UPPER_UM},
        },
    }


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "ORBITAL_REFERENCES",
    "SOURCES",
    "OrbitalReferenceTLE",
    "compute_visibility_geometry",
    "compute_sgp4_state",
    "get_orbital_reference",
    "list_orbital_references",
]
