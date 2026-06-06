"""Sol Solar Rotation Catalog — query surface for the v0.30.0rc2 ship
(surface differential rotation + internal rotation).

The first **solar-dynamics** extension of the v0.24.3 Sun Dynamical
Spectrum (helioseismic p-modes): the Sun's latitude-dependent surface
rotation and its helioseismically-inverted internal profile, read as a
spectral rotation-profile (in scope per ``docs/antikythera-maths/
CLAUDE.md`` — "rotation as a spectral profile").

Four query surfaces:

* :func:`get_solar_differential_rotation` — the Snodgrass-Ulrich 1990
  surface law ``Omega(lat) = A + B sin^2 + C sin^4`` evaluated across
  latitude, with per-band sidereal + synodic periods and the
  equator-to-pole lap time.
* :func:`get_solar_rotation_closure` — THE closure invariant: the 1990
  *Doppler* differential-rotation law reproduces Carrington's 1863
  *sunspot*-derived 25.38-day sidereal period at a latitude (~26°)
  inside the sunspot active band — two independent determinations,
  127 years apart, agreeing.
* :func:`get_solar_internal_rotation` — the helioseismic internal
  structure (differential convection zone / tachocline shear at
  ~0.70 R_sun / near-rigid radiative interior; Schou 1998, Howe 2009).
* :func:`list_solar_differential_rotation` — enumeration + citations.

Scope note: this is rotation-as-a-spectral-profile (a scalar angular
rate field ``Omega(lat)`` + a 1-D radial transition). It is NOT a
3-D magnetohydrodynamic dynamo simulation. ``the_one`` does not apply:
``Omega(lat)`` is a scalar rate field, not a Hurwitz rotation (the
ℂ/n=1 case at most; the octonion machinery adds nothing here — see
task #524).

Reference: research notebook §17 (solar dynamics).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List

from .solar_rotation_data import (
    CARRINGTON_SIDEREAL_PERIOD_DAYS,
    EARTH_ORBITAL_RATE_DEG_PER_DAY,
    ROTATION_ANCHORS,
    SOURCES,
    SU_A_DEG_PER_DAY,
    SU_B_DEG_PER_DAY,
    SU_C_DEG_PER_DAY,
    TACHOCLINE_RADIUS_R_SUN,
    anchor_to_data_dict,
)


#: Latitude bands (deg) at which the profile is tabulated.
_LATITUDE_BANDS_DEG: List[float] = [0.0, 15.0, 30.0, 45.0, 60.0, 75.0, 90.0]


def _omega_deg_per_day(latitude_deg: float) -> float:
    """Sidereal rotation rate at a latitude (Snodgrass-Ulrich 1990)."""
    s2 = math.sin(math.radians(latitude_deg)) ** 2
    return (
        SU_A_DEG_PER_DAY
        + SU_B_DEG_PER_DAY * s2
        + SU_C_DEG_PER_DAY * s2 * s2
    )


def _sidereal_period_days(omega_deg_per_day: float) -> float:
    """Sidereal rotation period (days) from a sidereal rate."""
    return 360.0 / omega_deg_per_day


def _synodic_period_days(omega_deg_per_day: float) -> float:
    """Synodic (Earth-relative) rotation period (days): the rate seen
    from the orbiting Earth is the sidereal rate minus Earth's mean
    orbital rate."""
    return 360.0 / (omega_deg_per_day - EARTH_ORBITAL_RATE_DEG_PER_DAY)


def _carrington_latitude_deg() -> float:
    """The latitude at which the Snodgrass-Ulrich law gives the
    canonical Carrington sidereal period (25.38 d).

    Solve ``A + B s + C s^2 = 360 / P_carr`` for ``s = sin^2(lat)``
    (a quadratic in s), take the physical root in ``[0, 1]``.
    """
    omega_target = 360.0 / CARRINGTON_SIDEREAL_PERIOD_DAYS
    # C s^2 + B s + (A - omega_target) = 0
    a_q = SU_C_DEG_PER_DAY
    b_q = SU_B_DEG_PER_DAY
    c_q = SU_A_DEG_PER_DAY - omega_target
    disc = b_q * b_q - 4.0 * a_q * c_q
    assert disc >= 0.0, "no real Carrington-latitude root"
    sqrt_disc = math.sqrt(disc)
    # Two roots; pick the one with sin^2 in [0, 1].
    for sign in (1.0, -1.0):
        s = (-b_q + sign * sqrt_disc) / (2.0 * a_q)
        if 0.0 <= s <= 1.0:
            return math.degrees(math.asin(math.sqrt(s)))
    raise ValueError("no physical Carrington-latitude root in [0, 1]")


def _band_dict(latitude_deg: float) -> Dict[str, Any]:
    omega = _omega_deg_per_day(latitude_deg)
    return {
        "latitude_deg": latitude_deg,
        "sidereal_rate_deg_per_day": omega,
        "sidereal_period_days": _sidereal_period_days(omega),
        "synodic_period_days": _synodic_period_days(omega),
    }


def get_solar_differential_rotation() -> Dict[str, Any]:
    """The Sun's surface differential rotation — the Snodgrass-Ulrich
    1990 law across latitude.

    Headlines: the equator rotates in ~24.5 d (sidereal) and the poles
    in ~34 d, so the equator laps the poles every ~86 days. The
    per-band table gives the sidereal + synodic period at each latitude.

    Returns
    -------
    dict
        ``{ok, body, law, coefficients, bands, equatorial_*, polar_*,
        equator_pole_lap_days}``.
    """
    eq_omega = _omega_deg_per_day(0.0)
    pole_omega = _omega_deg_per_day(90.0)
    lap_days = 360.0 / (eq_omega - pole_omega)
    return {
        "ok": True,
        "body": "sol",
        "subject": "surface_differential_rotation",
        "law": "Omega(lat) = A + B sin^2(lat) + C sin^4(lat)  [deg/day, sidereal]",
        "coefficients": {
            "A_deg_per_day": SU_A_DEG_PER_DAY,
            "B_deg_per_day": SU_B_DEG_PER_DAY,
            "C_deg_per_day": SU_C_DEG_PER_DAY,
        },
        "n_bands": len(_LATITUDE_BANDS_DEG),
        "bands": [_band_dict(lat) for lat in _LATITUDE_BANDS_DEG],
        "equatorial_sidereal_period_days": _sidereal_period_days(eq_omega),
        "polar_sidereal_period_days": _sidereal_period_days(pole_omega),
        "equator_pole_lap_days": lap_days,
    }


def get_solar_rotation_closure() -> Dict[str, Any]:
    """THE closure invariant — two independent solar-rotation
    determinations, 127 years apart, agree.

    Carrington (1863) tracked low-latitude **sunspots** and fixed the
    canonical sidereal rotation period at **25.38 days**. The
    Snodgrass-Ulrich (1990) **Doppler-feature** differential-rotation
    law reproduces exactly that period at a latitude (~26°) that lies
    **inside the sunspot active band** (~5°-35°, the butterfly
    diagram). The two methods — sunspot tracking vs Doppler imaging,
    separated by 127 years — agree where they overlap. That is the
    closure: small-method-independent invariant, like the ring (p:q)
    resonance and the helioseismic asymptotic relation.

    Returns
    -------
    dict
        ``{ok, body, carrington_sidereal_period_days,
        carrington_latitude_deg, latitude_in_sunspot_band,
        reproduced_period_days, residual_days, interpretation}``.
    """
    lat = _carrington_latitude_deg()
    omega = _omega_deg_per_day(lat)
    reproduced = _sidereal_period_days(omega)
    sunspot_band_min, sunspot_band_max = 5.0, 35.0
    return {
        "ok": True,
        "body": "sol",
        "carrington_sidereal_period_days": CARRINGTON_SIDEREAL_PERIOD_DAYS,
        "carrington_latitude_deg": lat,
        "sunspot_active_band_deg": [sunspot_band_min, sunspot_band_max],
        "latitude_in_sunspot_band": sunspot_band_min <= lat <= sunspot_band_max,
        "reproduced_period_days": reproduced,
        "residual_days": reproduced - CARRINGTON_SIDEREAL_PERIOD_DAYS,
        "interpretation": (
            "The Snodgrass-Ulrich 1990 Doppler differential-rotation law "
            "reproduces Carrington's 1863 sunspot-derived 25.38-day "
            "sidereal period at latitude ~26 deg, inside the sunspot "
            "active band (~5-35 deg). Two independent determinations "
            "(sunspot tracking vs Doppler imaging, 127 years apart) "
            "agree where they overlap."
        ),
    }


def get_solar_internal_rotation() -> Dict[str, Any]:
    """The Sun's helioseismically-inverted internal rotation.

    Three regimes (Schou 1998 SOI/MDI; Howe 2009 review): the
    **convection zone** (r > 0.7 R_sun) rotates differentially like the
    surface; the **radiative interior** (r < 0.7 R_sun) rotates nearly
    *rigidly*; the transition is the thin **tachocline** shear layer at
    ~0.70 R_sun — the seat of the solar dynamo.

    Returns
    -------
    dict
        ``{ok, body, tachocline_radius_r_sun, n_anchors, anchors}``.
    """
    return {
        "ok": True,
        "body": "sol",
        "subject": "internal_rotation",
        "tachocline_radius_r_sun": TACHOCLINE_RADIUS_R_SUN,
        "n_anchors": len(ROTATION_ANCHORS),
        "anchors": [anchor_to_data_dict(a) for a in ROTATION_ANCHORS],
    }


def list_solar_differential_rotation() -> Dict[str, Any]:
    """Full enumeration of solar-rotation data + citations."""
    return {
        "ok": True,
        "body": "sol",
        "n_anchors": len(ROTATION_ANCHORS),
        "n_sources": len(SOURCES),
        "coefficients": {
            "A_deg_per_day": SU_A_DEG_PER_DAY,
            "B_deg_per_day": SU_B_DEG_PER_DAY,
            "C_deg_per_day": SU_C_DEG_PER_DAY,
        },
        "anchors": [anchor_to_data_dict(a) for a in ROTATION_ANCHORS],
    }


__all__ = [
    "get_solar_differential_rotation",
    "get_solar_rotation_closure",
    "get_solar_internal_rotation",
    "list_solar_differential_rotation",
]
