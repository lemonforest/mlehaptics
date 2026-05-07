"""Sol Spherical Harmonic Catalog — unified query surface across the
gravity sector (v0.20.0 Stokes coefficients) and the magnetic sector
(v0.20.1 Schmidt coefficients).

Promotes the v0.21.0 architectural commitment from research notebook
§17.4.2 to a stable ship surface. **This is a unification refactor,
not a data store**. The underlying records still live in:

* :mod:`geodetic_catalog_data` (gravity multipoles; 4π-normalised
  Stokes coefficients C̄_nm / S̄_nm, the geodesy convention).
* :mod:`magnetic_multipole_catalog_data` (magnetic multipoles;
  Schmidt quasi-normalised g_n^m / h_n^m, the geomagnetic convention).

The v0.20.0 + v0.20.1 surfaces (`bridge.get_geodetic_state`,
`bridge.get_magnetic_multipoles`, etc.) continue to work unchanged —
the unification is a NEW query surface that lets consumers ask "what
spherical-harmonic representations does the catalog have for body X,
across all channels?" with one call instead of two.

**Normalisation handling.** The two conventions cannot be mixed without
re-normalisation:

* Geodesy (4π-normalised, fully normalised): coefficient magnitudes
  decay rapidly with degree; integration over the sphere returns the
  total potential.
* Geomagnetic (Schmidt quasi-normalised): coefficient magnitudes are
  in physical units (nT) at the body surface; integration uses
  Legendre functions with Schmidt's normalisation factor.

The conversion factor between the two for degree n, order m is

  C̄_nm = g_n^m / sqrt((2 - δ_0m) * (2n + 1))    (m ≤ n)

where δ_0m = 1 if m = 0 else 0. See Winch et al. (2005), "Geomagnetic
Reference Spectra", for the full derivation. Each entry in this
catalog carries a `normalisation_convention` field so consumers know
which conversion to apply.

Reference: research notebook §17.4.2 (the v0.21.0 ship sequence) and
§17.4.1 (the rhythm-mismatch finding that motivates state-lookup
catalogs across both sectors).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from .geodetic_catalog_data import (
    GRAVITY_MODELS as _GRAVITY_MODELS,
    SOURCES as _GEODETIC_SOURCES,
)
from .magnetic_multipole_catalog_data import (
    MAGNETIC_MULTIPOLE_MODELS as _MAGNETIC_MODELS,
    SOURCES as _MAGNETIC_SOURCES,
)


# ---- Normalisation conventions -------------------------------------------

#: Channel labels for the unified catalog.
CHANNEL_GRAVITY: str = "gravity"
CHANNEL_MAGNETIC: str = "magnetic"
CHANNEL_BOTH: str = "both"

#: Normalisation convention labels.
NORM_4PI_STOKES: str = "4pi-Stokes"            # geodesy: C̄_nm / S̄_nm
NORM_SCHMIDT_QUASI: str = "Schmidt-quasi-norm"  # geomagnetic: g_n^m / h_n^m

_VALID_CHANNELS: frozenset = frozenset({
    CHANNEL_GRAVITY, CHANNEL_MAGNETIC, CHANNEL_BOTH,
})


# ---- Memoised lookups (built at module load) ----------------------------

_GRAVITY_BY_BODY: Dict[str, Any] = {m.body: m for m in _GRAVITY_MODELS}
_MAGNETIC_BY_BODY: Dict[str, Any] = {m.body: m for m in _MAGNETIC_MODELS}
_ALL_BODIES: List[str] = sorted(
    set(_GRAVITY_BY_BODY.keys()) | set(_MAGNETIC_BY_BODY.keys())
)
_BOTH_CHANNELS_BODIES: List[str] = sorted(
    set(_GRAVITY_BY_BODY.keys()) & set(_MAGNETIC_BY_BODY.keys())
)


def _gravity_to_unified(m: Any) -> Dict[str, Any]:
    """Convert a v0.20.0 GravityModel to the unified shape."""
    return {
        "body": m.body,
        "channel": CHANNEL_GRAVITY,
        "model_name": m.model_name,
        "max_degree": m.max_degree,
        "reference_radius_km": m.reference_radius_km,
        "normalisation_convention": NORM_4PI_STOKES,
        "leading_coefficients": {
            "gm_km3_per_s2": m.gm_km3_per_s2,
            "J2": m.J2,
            "J3": m.J3,
            "J4": m.J4,
        },
        "full_coeff_archive": m.full_coeff_archive,
        "precision_flag": m.precision_flag,
        "source_key": m.source_key,
    }


def _magnetic_to_unified(m: Any) -> Dict[str, Any]:
    """Convert a v0.20.1 MagneticMultipoleModel to the unified shape."""
    return {
        "body": m.body,
        "channel": CHANNEL_MAGNETIC,
        "model_name": m.model_name,
        "max_degree": m.max_degree,
        "reference_radius_km": m.reference_radius_km,
        "normalisation_convention": NORM_SCHMIDT_QUASI,
        "leading_coefficients": {
            "epoch_year": m.epoch_year,
            "g10_nT": m.g10_nT,
            "g11_nT": m.g11_nT,
            "h11_nT": m.h11_nT,
            "dipole_moment_T_m3": m.dipole_moment_T_m3,
            "dipole_tilt_deg": m.dipole_tilt_deg,
            "dipole_offset_km": m.dipole_offset_km,
        },
        "full_coeff_archive": m.full_coeff_archive,
        "precision_flag": m.precision_flag,
        "structural_flag": m.structural_flag,
        "source_key": m.source_key,
    }


def compute_spherical_harmonics(
    body: str,
    channel: str = CHANNEL_BOTH,
) -> Dict[str, Any]:
    """Per-body spherical-harmonic query across gravity + magnetic.

    Single-body query; returns one or both channels in a unified shape.
    The underlying records are the v0.20.0 GravityModel + v0.20.1
    MagneticMultipoleModel — this surface adapts them to a common
    representation with explicit `normalisation_convention` so
    consumers know which conversion factors to apply when crossing
    channels.

    Parameters
    ----------
    body : str. Lower-case body name.
    channel : str, default "both". One of "gravity", "magnetic", "both".

    Returns
    -------
    dict
        ``{"ok": True, "body": str, "channels": {channel_name: {...}}}``
        with `channels` containing one or two entries depending on the
        request and the body's coverage. Bodies absent from a requested
        channel return that channel as None.
        On error: ``{"ok": False, "error": "..."}``.
    """
    if channel not in _VALID_CHANNELS:
        return {
            "ok": False,
            "error": (
                f"unknown channel {channel!r}; valid choices are "
                f"{sorted(_VALID_CHANNELS)}"
            ),
        }

    name = str(body).lower().strip()
    if name not in _ALL_BODIES:
        return {
            "ok": False,
            "error": (
                f"unknown body {body!r} in Sol Spherical Harmonic "
                f"Catalog; known bodies are {_ALL_BODIES}"
            ),
        }

    out_channels: Dict[str, Any] = {}
    if channel in (CHANNEL_GRAVITY, CHANNEL_BOTH):
        m = _GRAVITY_BY_BODY.get(name)
        out_channels[CHANNEL_GRAVITY] = (
            _gravity_to_unified(m) if m else None
        )
    if channel in (CHANNEL_MAGNETIC, CHANNEL_BOTH):
        m = _MAGNETIC_BY_BODY.get(name)
        out_channels[CHANNEL_MAGNETIC] = (
            _magnetic_to_unified(m) if m else None
        )

    return {
        "ok": True,
        "body": name,
        "channels": out_channels,
    }


def list_spherical_harmonic_models() -> Dict[str, Any]:
    """Full catalog enumeration across both channels.

    Returns every gravity model + every magnetic model in the unified
    shape, plus the merged `bodies` union, the both-channels subset,
    and the merged citation dict spanning both sectors.
    """
    # Merge SOURCES dicts. Keys collide rarely (gravity / magnetic
    # citations are typically distinct papers); on collision the
    # gravity-side wins (no semantic disagreement, just disambiguation).
    merged_sources = dict(_MAGNETIC_SOURCES)
    merged_sources.update(_GEODETIC_SOURCES)

    return {
        "ok": True,
        "n_bodies": len(_ALL_BODIES),
        "n_both_channels_bodies": len(_BOTH_CHANNELS_BODIES),
        "n_gravity_models": len(_GRAVITY_MODELS),
        "n_magnetic_models": len(_MAGNETIC_MODELS),
        "n_merged_sources": len(merged_sources),
        "n_geodetic_sources": len(_GEODETIC_SOURCES),
        "n_magnetic_sources": len(_MAGNETIC_SOURCES),
        "bodies": list(_ALL_BODIES),
        "both_channels_bodies": list(_BOTH_CHANNELS_BODIES),
        "gravity": [_gravity_to_unified(m) for m in _GRAVITY_MODELS],
        "magnetic": [_magnetic_to_unified(m) for m in _MAGNETIC_MODELS],
        "normalisation_conventions": {
            CHANNEL_GRAVITY: NORM_4PI_STOKES,
            CHANNEL_MAGNETIC: NORM_SCHMIDT_QUASI,
        },
    }


def convert_normalisation(
    coefficient_value: float,
    n: int,
    m: int,
    from_convention: str,
    to_convention: str,
) -> Dict[str, Any]:
    """Convert a single spherical-harmonic coefficient between
    4π-normalised Stokes and Schmidt-quasi-normalised conventions.

    Per Winch et al. (2005) "Geomagnetic Reference Spectra", the
    relation is

        C̄_nm = g_n^m / sqrt((2 - δ_0m) * (2n + 1))    (m ≤ n)

    where δ_0m = 1 if m = 0 else 0. So:

    * Schmidt → 4π-Stokes: divide by ``sqrt((2 - δ_0m) * (2n + 1))``.
    * 4π-Stokes → Schmidt: multiply by ``sqrt((2 - δ_0m) * (2n + 1))``.

    Note: this conversion is purely algebraic (the conventions
    differ only in their normalisation prefactors); it does NOT
    cross between physical channels — gravity-side g_n^m has no
    physical interpretation, nor does magnetic-side Stokes C̄_nm.
    The conversion is for users who need to apply a gravity field's
    coefficient table in geomagnetic-convention software, or vice
    versa.

    Parameters
    ----------
    coefficient_value : float. The numeric coefficient.
    n : int. Spherical-harmonic degree (≥ 0).
    m : int. Spherical-harmonic order (0 ≤ m ≤ n).
    from_convention, to_convention : str. One of `NORM_4PI_STOKES` or
        `NORM_SCHMIDT_QUASI`.

    Returns
    -------
    dict
        ``{"ok": True, "value": float, "factor": float,
          "from": str, "to": str}``
        On error: ``{"ok": False, "error": "..."}``.
    """
    if not math.isfinite(coefficient_value):
        return {"ok": False, "error": "coefficient_value must be finite"}
    if n < 0:
        return {"ok": False, "error": f"degree n must be >= 0, got {n}"}
    if m < 0 or m > n:
        return {
            "ok": False,
            "error": f"order m must satisfy 0 <= m <= n; got n={n}, m={m}",
        }
    valid = {NORM_4PI_STOKES, NORM_SCHMIDT_QUASI}
    if from_convention not in valid:
        return {
            "ok": False,
            "error": (
                f"unknown from_convention {from_convention!r}; "
                f"valid: {sorted(valid)}"
            ),
        }
    if to_convention not in valid:
        return {
            "ok": False,
            "error": (
                f"unknown to_convention {to_convention!r}; "
                f"valid: {sorted(valid)}"
            ),
        }

    if from_convention == to_convention:
        return {
            "ok": True,
            "value": coefficient_value,
            "factor": 1.0,
            "from": from_convention,
            "to": to_convention,
        }

    delta_0m = 1 if m == 0 else 0
    schmidt_to_4pi = 1.0 / math.sqrt((2.0 - delta_0m) * (2 * n + 1))

    if (from_convention == NORM_SCHMIDT_QUASI
            and to_convention == NORM_4PI_STOKES):
        factor = schmidt_to_4pi
    else:  # 4pi → Schmidt is the reciprocal
        factor = 1.0 / schmidt_to_4pi

    return {
        "ok": True,
        "value": coefficient_value * factor,
        "factor": factor,
        "from": from_convention,
        "to": to_convention,
    }


__all__ = [
    "CHANNEL_GRAVITY",
    "CHANNEL_MAGNETIC",
    "CHANNEL_BOTH",
    "NORM_4PI_STOKES",
    "NORM_SCHMIDT_QUASI",
    "compute_spherical_harmonics",
    "list_spherical_harmonic_models",
    "convert_normalisation",
]
