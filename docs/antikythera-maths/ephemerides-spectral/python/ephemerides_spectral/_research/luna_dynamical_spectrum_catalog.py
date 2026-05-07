"""Sol Luna Dynamical Spectrum Catalog — query surface for the v0.24.1
ship (second per-body dynamical-spectrum surface).

Promotes the v0.24.1 architectural commitment from research notebook
§17.7 to a stable ship surface. Mirrors the v0.24.0 Mercury catalog
structure: action-angle decomposition + a headline closure-invariant
cross-channel observation.

Mercury's v0.24.0 headline was the **Le Verrier / Einstein perihelion-
precession contribution decomposition** (closure: Newtonian + GR + J₂
sums to Clemence 1947's observed total within ±0.5 arcsec/century).

Luna's v0.24.1 headline is the **Saros integer-commensurability
closure**: 223 synodic ≈ 239 anomalistic ≈ 242 draconitic months ≈
19 eclipse years all agree within ~0.5 day. This is a textbook
small-denominator phenomenon and it is **exactly the kind of
structure the project's BIP encoder is built to detect** — three
irrational-looking frequency ratios that share a near-rational
commensurability. The Saros cycle is the closure that lets ancient
astronomers (Babylonian, Mesoamerican, Greek) predict eclipses
before they understood why.

Three bridge surfaces:

* :func:`get_luna_dynamical_spectrum` — full action-angle mode catalog.
* :func:`get_luna_saros_commensurability` — Saros closure invariant
  with all four 6585.x-day products + max-spread invariant.
* :func:`list_luna_dynamical_spectrum` — full enumeration.

Reference: research notebook §17.7.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .luna_dynamical_spectrum_data import (
    ECLIPSE_YEAR_DAYS,
    LUNA_ANOMALISTIC_MONTH_DAYS,
    LUNA_APSIDAL_PRECESSION_YEARS,
    LUNA_DRACONITIC_MONTH_DAYS,
    LUNA_DYNAMICAL_MODES,
    LUNA_ECCENTRICITY,
    LUNA_FORCED_LIBRATION_LONGITUDE_ARCSEC,
    LUNA_INCLINATION_TO_ECLIPTIC_DEG,
    LUNA_NODAL_PRECESSION_YEARS,
    LUNA_NORMALISED_MOI_C_OVER_MR2,
    LUNA_OBLIQUITY_TO_ORBIT_DEG,
    LUNA_SEMI_MAJOR_AXIS_KM,
    LUNA_SIDEREAL_MONTH_DAYS,
    LUNA_SYNODIC_MONTH_DAYS,
    LUNA_TROPICAL_MONTH_DAYS,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SAROS_COMMENSURABILITY,
    SOURCES,
    DynamicalMode,
    SarosCommensurability,
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


def _saros_to_dict(s: SarosCommensurability) -> Dict[str, Any]:
    return {
        "name": s.name,
        "integer_count": s.integer_count,
        "unit_period_days": s.unit_period_days,
        "product_days": s.product_days,
        "notes": s.notes,
        "source_key": s.source_key,
        "precision_flag": s.precision_flag,
    }


def get_luna_dynamical_spectrum() -> Dict[str, Any]:
    """Luna's full action-angle dynamical-mode catalog.

    Second per-body dynamical-spectrum surface. Decomposes Luna's
    dynamical state into 8 angle modes (sidereal + synodic +
    anomalistic + draconitic mean motions; spin frequency locked
    1:1; forced libration at orbital frequency; apsidal precession
    8.85 yr; nodal precession 18.61 yr) plus 3 action modes
    (eccentricity, inclination, obliquity to orbit — Cassini state 2).

    Headline modes:
      * **1:1 tidal lock** with sidereal orbital motion — synchronous
        rotation (cross-references v0.23.0).
      * **Forced libration in longitude**, ~7.9 arcsec amplitude —
        Williams 2014 LLR — the most precisely-measured libration in
        the Solar System; constrains C/MR² = 0.3932 ± 0.0002.
      * **Four distinct 'months'** (sidereal/synodic/anomalistic/
        draconitic) — they differ because perigee precesses (apsidal,
        8.85 yr prograde) and nodes regress (nodal, 18.61 yr
        retrograde).
      * **Cassini state 2 obliquity** 6.687° — substantially larger
        than Mercury's Cassini-state-1 0.034° because Luna sits on a
        different equilibrium branch.
    """
    return {
        "ok": True,
        "body": "luna",
        "n_modes": len(LUNA_DYNAMICAL_MODES),
        "modes": [_mode_to_dict(m) for m in LUNA_DYNAMICAL_MODES],
        "constants": {
            "semi_major_axis_km": LUNA_SEMI_MAJOR_AXIS_KM,
            "eccentricity": LUNA_ECCENTRICITY,
            "inclination_to_ecliptic_deg": LUNA_INCLINATION_TO_ECLIPTIC_DEG,
            "obliquity_to_orbit_deg": LUNA_OBLIQUITY_TO_ORBIT_DEG,
            "sidereal_month_days": LUNA_SIDEREAL_MONTH_DAYS,
            "synodic_month_days": LUNA_SYNODIC_MONTH_DAYS,
            "anomalistic_month_days": LUNA_ANOMALISTIC_MONTH_DAYS,
            "draconitic_month_days": LUNA_DRACONITIC_MONTH_DAYS,
            "tropical_month_days": LUNA_TROPICAL_MONTH_DAYS,
            "eclipse_year_days": ECLIPSE_YEAR_DAYS,
            "forced_libration_longitude_arcsec":
                LUNA_FORCED_LIBRATION_LONGITUDE_ARCSEC,
            "normalised_moi_C_over_MR2":
                LUNA_NORMALISED_MOI_C_OVER_MR2,
            "apsidal_precession_years": LUNA_APSIDAL_PRECESSION_YEARS,
            "nodal_precession_years": LUNA_NODAL_PRECESSION_YEARS,
        },
    }


def get_luna_saros_commensurability() -> Dict[str, Any]:
    """Saros cycle integer-commensurability closure invariant.

    THE headline cross-channel observation of v0.24.1: Luna's three
    distinct months (synodic, anomalistic, draconitic) admit a
    small-integer commensurability that produces the famous
    ~18.03-year Saros eclipse-recurrence cycle.

    The closure: each of these four products is a candidate
    "Saros period," and they all agree within ~0.5 day:

      223 × synodic   = 6585.32 d
      239 × anomalistic = 6585.54 d
      242 × draconitic = 6585.36 d
      19 × eclipse-year = 6585.78 d

    The 0.5-day spread is THE invariant — pinned in tests as
    `max(products) - min(products) < 1.0 day`. This is a textbook
    small-denominator phenomenon and exactly the kind of structure
    the project's BIP encoder is built to detect: three
    irrational-looking frequency ratios sharing a near-rational
    commensurability.

    The Saros cycle is *also* the closure that let ancient
    astronomers (Babylonian, Mesoamerican, Greek — including the
    Antikythera mechanism's eclipse predictor!) forecast eclipses
    centuries before they understood the underlying gravitational
    physics. The Antikythera mechanism's Saros dial is literally
    a hardware implementation of this commensurability — making
    this a direct cross-strand observation between
    `ephemerides-spectral` and `antikythera-spectral`.

    Returns
    -------
    dict
        ``{ok, body, mean_period_days, max_spread_days, products: [
        {name, integer_count, unit_period_days, product_days, ...}]}``.
    """
    products = [s.product_days for s in SAROS_COMMENSURABILITY]
    mean_period = sum(products) / len(products)
    max_spread = max(products) - min(products)
    return {
        "ok": True,
        "body": "luna",
        "n_products": len(SAROS_COMMENSURABILITY),
        "mean_period_days": mean_period,
        "mean_period_years": mean_period / 365.25,
        "max_spread_days": max_spread,
        "products": [_saros_to_dict(s) for s in SAROS_COMMENSURABILITY],
    }


def list_luna_dynamical_spectrum() -> Dict[str, Any]:
    """Full enumeration of Luna dynamical-spectrum data + citations."""
    return {
        "ok": True,
        "body": "luna",
        "n_modes": len(LUNA_DYNAMICAL_MODES),
        "n_saros_products": len(SAROS_COMMENSURABILITY),
        "n_sources": len(SOURCES),
        "modes": [_mode_to_dict(m) for m in LUNA_DYNAMICAL_MODES],
        "saros_products": [
            _saros_to_dict(s) for s in SAROS_COMMENSURABILITY
        ],
    }


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "LUNA_DYNAMICAL_MODES",
    "SAROS_COMMENSURABILITY",
    "SOURCES",
    "DynamicalMode",
    "SarosCommensurability",
    "get_luna_dynamical_spectrum",
    "get_luna_saros_commensurability",
    "list_luna_dynamical_spectrum",
]
