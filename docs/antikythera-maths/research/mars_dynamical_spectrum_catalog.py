"""Sol Mars Dynamical Spectrum Catalog — query surface for the v0.24.2
ship (third per-body dynamical-spectrum surface).

Promotes the v0.24.2 architectural commitment from research notebook
§17.7 to a stable ship surface. Mars is the **contrast case** to
v0.24.0 Mercury (clean closure: Le Verrier/Einstein perihelion
decomposition) and v0.24.1 Luna (clean closure: Saros integer
commensurability).

Mars's headline is the **opposite** of clean closure: secular-
resonance overlap drives **chaotic obliquity wandering** over Gyr
timescales (Laskar 1993; Laskar et al. 2004). Mars is the canonical
observable signature in our Solar System of **KAM-theory small-
denominator failure** — the regime where the action-angle
formalism's quasi-periodic torus structure breaks down.

Three bridge surfaces:

* :func:`get_mars_dynamical_spectrum` — full action-angle catalog.
* :func:`get_mars_secular_resonance_overlap` — the chaos driver:
  proximity of Mars spin-axis precession to inner-Solar-System
  secular fundamentals s₃, s₄, etc.
* :func:`list_mars_dynamical_spectrum` — full enumeration.

Reference: research notebook §17.7.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .mars_dynamical_spectrum_data import (
    MARS_DYNAMICAL_MODES,
    MARS_ECCENTRICITY,
    MARS_INCLINATION_TO_ECLIPTIC_DEG,
    MARS_NORMALISED_MOI_C_OVER_MR2,
    MARS_OBLIQUITY_DEG,
    MARS_OBLIQUITY_LASKAR_MAX_DEG,
    MARS_OBLIQUITY_LASKAR_MIN_DEG,
    MARS_OBLIQUITY_MEAN_GYR_DEG,
    MARS_ORBITAL_PERIOD_DAYS,
    MARS_SECULAR_RESONANCES,
    MARS_SEMI_MAJOR_AXIS_AU,
    MARS_SIDEREAL_DAY_DAYS,
    MARS_SIDEREAL_DAY_HOURS,
    MARS_SPIN_AXIS_PRECESSION_PERIOD_YEARS,
    MARS_SPIN_AXIS_PRECESSION_RATE_ARCSEC_PER_YEAR,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
    DynamicalMode,
    SecularResonance,
)


def _mode_to_dict(m: DynamicalMode) -> Dict[str, Any]:
    return {
        "name": m.name,
        "frequency_per_century": m.frequency_per_century,
        "period_days": m.period_days,
        "amplitude_value": m.amplitude_value,
        "amplitude_units": m.amplitude_units,
        "angle_or_action": m.angle_or_action,
        "notes": m.notes,
        "source_key": m.source_key,
        "precision_flag": m.precision_flag,
    }


def _resonance_to_dict(r: SecularResonance) -> Dict[str, Any]:
    return {
        "mars_mode": r.mars_mode,
        "secular_partner": r.secular_partner,
        "partner_description": r.partner_description,
        "proximity_arcsec_per_year": r.proximity_arcsec_per_year,
        "notes": r.notes,
        "source_key": r.source_key,
        "precision_flag": r.precision_flag,
    }


def get_mars_dynamical_spectrum() -> Dict[str, Any]:
    """Mars's full action-angle dynamical-mode catalog.

    Third per-body dynamical-spectrum surface in v0.24.x. Contrast
    case to Mercury's clean Le Verrier/Einstein closure and Luna's
    clean Saros commensurability.

    8-mode catalog: orbital mean motion, spin frequency, spin-axis
    precession (~171 kyr — the chaos-driver mode), apsidal precession
    (g₄ secular fundamental), nodal precession (s₄), eccentricity
    (action; varies 0.005-0.119 over secular cycle), inclination
    (action), obliquity (action; **chaotic** over Gyr per Laskar).

    Headlines:
      * **Chaotic obliquity** — present-day 25.19°, but Gyr-scale
        excursion range ~0°-60° (Laskar et al. 2004) with mean ~37.6°.
      * **No spin-orbit lock** — unlike Mercury (3:2) / Luna (1:1) /
        Galileans / Titan / Pluto-Charon, Mars is rotationally free.
      * **C/MR² = 0.3645 ± 0.0005** — Le Maistre 2023 InSight RISE
        measurement; cross-references v0.21.4 rotational constraint.
      * **Spin-axis precession 171 kyr** — Ward 1973 / Touma-Wisdom
        1993; this is the mode whose frequency crosses the inner-
        Solar-System secular fundamentals to produce chaos.
    """
    return {
        "ok": True,
        "body": "mars",
        "n_modes": len(MARS_DYNAMICAL_MODES),
        "modes": [_mode_to_dict(m) for m in MARS_DYNAMICAL_MODES],
        "constants": {
            "semi_major_axis_au": MARS_SEMI_MAJOR_AXIS_AU,
            "eccentricity": MARS_ECCENTRICITY,
            "inclination_to_ecliptic_deg":
                MARS_INCLINATION_TO_ECLIPTIC_DEG,
            "orbital_period_days": MARS_ORBITAL_PERIOD_DAYS,
            "sidereal_day_hours": MARS_SIDEREAL_DAY_HOURS,
            "sidereal_day_days": MARS_SIDEREAL_DAY_DAYS,
            "obliquity_deg": MARS_OBLIQUITY_DEG,
            "normalised_moi_C_over_MR2":
                MARS_NORMALISED_MOI_C_OVER_MR2,
            "spin_axis_precession_period_years":
                MARS_SPIN_AXIS_PRECESSION_PERIOD_YEARS,
            "spin_axis_precession_rate_arcsec_per_year":
                MARS_SPIN_AXIS_PRECESSION_RATE_ARCSEC_PER_YEAR,
            "obliquity_laskar_min_deg":
                MARS_OBLIQUITY_LASKAR_MIN_DEG,
            "obliquity_laskar_max_deg":
                MARS_OBLIQUITY_LASKAR_MAX_DEG,
            "obliquity_mean_gyr_deg": MARS_OBLIQUITY_MEAN_GYR_DEG,
        },
    }


def get_mars_secular_resonance_overlap() -> Dict[str, Any]:
    """Mars secular-resonance overlap — THE chaos-driver headline.

    The cross-channel observation specific to Mars: proximity of
    Mars's spin-axis precession frequency (~7.58 arcsec/yr) to the
    inner-Solar-System secular orbital fundamentals (s₃ ≈ -18.86,
    s₄ ≈ -17.74, etc., arcsec/yr) drives Mars obliquity chaos.

    Where Mercury's v0.24.0 closure was a *successful sum* (Newtonian
    + GR + J₂ ≈ observed within ±1 arcsec/century) and Luna's
    v0.24.1 closure was a *successful integer commensurability*
    (223:239:242 within < 1 day spread), Mars's v0.24.2 "closure" is
    a *failure mode*: the secular frequencies overlap so tightly that
    the quasi-periodic torus structure of action-angle dynamics
    breaks down, producing chaos on Gyr timescales.

    This is the **observable signature of KAM-theory small-
    denominator failure** in our Solar System.

    The catalog ships:
      * Mars spin-axis precession rate (~7.58 arcsec/yr).
      * Inner-system secular fundamental frequencies s₃, s₄, ...
      * Pairwise frequency proximity for each near-resonance.

    Cross-channel observation: **without Earth's stabilising Moon,
    Earth would be subject to similar chaos.** The Moon's tidal
    stabilisation of Earth's spin axis is a load-bearing piece of
    long-term climate predictability — and v0.24.1 Luna already
    captured the LLR-precision libration that constrains the
    Earth-Moon tidal-locking mechanism.

    Returns
    -------
    dict
        ``{ok, body, n_resonances, mars_spin_precession_rate_arcsec_yr,
        resonances: [...], chaos_invariant: {min_proximity_arcsec_yr,
        chaos_threshold_arcsec_yr}}``.
    """
    proximities = [
        r.proximity_arcsec_per_year for r in MARS_SECULAR_RESONANCES
    ]
    min_proximity = min(proximities)
    return {
        "ok": True,
        "body": "mars",
        "n_resonances": len(MARS_SECULAR_RESONANCES),
        "mars_spin_precession_rate_arcsec_yr":
            MARS_SPIN_AXIS_PRECESSION_RATE_ARCSEC_PER_YEAR,
        "resonances": [
            _resonance_to_dict(r) for r in MARS_SECULAR_RESONANCES
        ],
        "chaos_invariant": {
            "min_proximity_arcsec_yr": min_proximity,
            "chaos_threshold_arcsec_yr": 12.0,
            "chaos_active": min_proximity < 12.0,
            "obliquity_excursion_range_deg": [
                MARS_OBLIQUITY_LASKAR_MIN_DEG,
                MARS_OBLIQUITY_LASKAR_MAX_DEG,
            ],
            "obliquity_mean_gyr_deg": MARS_OBLIQUITY_MEAN_GYR_DEG,
            "obliquity_present_deg": MARS_OBLIQUITY_DEG,
        },
    }


def list_mars_dynamical_spectrum() -> Dict[str, Any]:
    """Full enumeration of Mars dynamical-spectrum data + citations."""
    return {
        "ok": True,
        "body": "mars",
        "n_modes": len(MARS_DYNAMICAL_MODES),
        "n_resonances": len(MARS_SECULAR_RESONANCES),
        "n_sources": len(SOURCES),
        "modes": [_mode_to_dict(m) for m in MARS_DYNAMICAL_MODES],
        "secular_resonances": [
            _resonance_to_dict(r) for r in MARS_SECULAR_RESONANCES
        ],
    }


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "MARS_DYNAMICAL_MODES",
    "MARS_SECULAR_RESONANCES",
    "SOURCES",
    "DynamicalMode",
    "SecularResonance",
    "get_mars_dynamical_spectrum",
    "get_mars_secular_resonance_overlap",
    "list_mars_dynamical_spectrum",
]
