"""Sol Mercury Dynamical Spectrum Catalog — query surface for the
v0.24.0 ship (first per-body dynamical-spectrum surface).

Promotes the v0.24.0 architectural commitment from research notebook
§17.7 to a stable ship surface. **First per-body dynamical-spectrum
surface in the project**: rather than decompose between two channels
(as v0.21.x cross-channel surfaces did), this surface decomposes a
single body's dynamical state into action-angle modes, with
emphasis on the **perihelion-precession contribution decomposition**
(Le Verrier → Newcomb → Einstein → Clemence → Verma → Park lineage)
as the headline cross-channel observation: every contribution from a
neighboring body is independently measurable and citable.

Mercury chosen as cleanest first target: no moon, no atmosphere, no
ocean, smallest in the planetary roster, in the historically richest
dynamical-test position.

Cross-channel reach: this is a **discipline pivot** — the
methodology shift from v0.21.x cross-channel-coupling decomposition
to per-body dynamical decomposition. The natural follow-on (v0.24.x)
extends to Luna (LLR 50+ years), Mars (chaotic obliquity), the Sun
(helioseismology), small bodies (Yarkovsky/YORP).

Three bridge surfaces:

* :func:`get_mercury_dynamical_spectrum` — full body's mode catalog.
* :func:`get_mercury_precession_decomposition` — perihelion-precession
  contribution-by-perturber breakdown.
* :func:`list_mercury_dynamical_spectrum` — full enumeration with
  citations.

Reference: research notebook §17.7.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .mercury_dynamical_spectrum_data import (
    MERCURY_DYNAMICAL_MODES,
    MERCURY_ECCENTRICITY,
    MERCURY_FORCED_LIBRATION_ARCSEC,
    MERCURY_INCLINATION_DEG,
    MERCURY_NORMALISED_MOI_C_OVER_MR2,
    MERCURY_OBLIQUITY_ARCMIN,
    MERCURY_OBLIQUITY_DEG,
    MERCURY_ORBITAL_PERIOD_DAYS,
    MERCURY_PRECESSION_CONTRIBUTIONS,
    MERCURY_ROTATION_PERIOD_DAYS,
    MERCURY_SEMI_MAJOR_AXIS_AU,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
    DynamicalMode,
    PrecessionContribution,
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


def _contribution_to_dict(c: PrecessionContribution) -> Dict[str, Any]:
    return {
        "contributor": c.contributor,
        "arcsec_per_century": c.arcsec_per_century,
        "physics_class": c.physics_class,
        "notes": c.notes,
        "source_key": c.source_key,
        "precision_flag": c.precision_flag,
    }


def get_mercury_dynamical_spectrum() -> Dict[str, Any]:
    """Mercury's full action-angle dynamical-mode catalog.

    Decomposes Mercury's dynamical state into angle variables (live
    on tori — orbital phase, spin phase, perihelion longitude,
    ascending node) and action variables (live on real intervals —
    semi-major axis, eccentricity, inclination, obliquity).

    Each mode carries:
      * ``frequency_per_century`` — cycles per century (or 0 for
        secular slow variables).
      * ``period_days`` — equivalent period.
      * ``amplitude_value`` + ``amplitude_units`` — characteristic
        excursion in source-paper units (e.g., 35.8 arcsec for
        forced libration; 0.2056 dimensionless for eccentricity).
      * ``angle_or_action`` — phase-space class.
      * ``source_key`` — citation key into ``SOURCES``.

    The headline modes:
      * **3:2 spin-orbit lock** — Mercury's spin frequency is exactly
        3/2 of orbital mean motion (Pettengill 1965 / Margot 2007).
      * **Forced libration at orbital frequency** — 35.8 arcsec
        amplitude; the measurement that constrained C/MR² = 0.346 ±
        0.014 (Margot 2007).
      * **Perihelion precession** — 574.10 arcsec/century (see
        :func:`get_mercury_precession_decomposition` for the per-
        perturber breakdown — the Le Verrier / Einstein decomposition).
      * **Tiny obliquity** — 2.04 ± 0.08 arcmin (Margot 2007); Mercury
        occupies Cassini state 1.

    Returns
    -------
    dict
        ``{ok, body, n_modes, modes: [...], constants: {...}}``.

    References
    ----------
    Margot J. L. et al. (2007). *Science* 316, 710-714.
    Park R. S. et al. (2021). JPL DE441 ephemeris.
    Murray C. D. & Dermott S. F. (1999). *Solar System Dynamics*.
    """
    return {
        "ok": True,
        "body": "mercury",
        "n_modes": len(MERCURY_DYNAMICAL_MODES),
        "modes": [_mode_to_dict(m) for m in MERCURY_DYNAMICAL_MODES],
        "constants": {
            "semi_major_axis_au": MERCURY_SEMI_MAJOR_AXIS_AU,
            "eccentricity": MERCURY_ECCENTRICITY,
            "inclination_deg": MERCURY_INCLINATION_DEG,
            "orbital_period_days": MERCURY_ORBITAL_PERIOD_DAYS,
            "rotation_period_days": MERCURY_ROTATION_PERIOD_DAYS,
            "obliquity_arcmin": MERCURY_OBLIQUITY_ARCMIN,
            "obliquity_deg": MERCURY_OBLIQUITY_DEG,
            "forced_libration_arcsec": MERCURY_FORCED_LIBRATION_ARCSEC,
            "normalised_moi_C_over_MR2": MERCURY_NORMALISED_MOI_C_OVER_MR2,
        },
    }


def get_mercury_precession_decomposition() -> Dict[str, Any]:
    """Mercury perihelion-precession contribution-by-perturber
    decomposition.

    THE headline cross-channel observation of v0.24.0: Mercury's
    secular perihelion precession (574.10 arcsec/century, Clemence
    1947) decomposes as a sum of Newtonian perturbations from
    neighbouring planets + the post-Newtonian general-relativistic
    Schwarzschild correction + the solar quadrupole-moment
    correction.

    The Le Verrier 1859 → Newcomb 1882 → Einstein 1915 → Clemence
    1947 → Park 2017 lineage:

      Total observed:  574.10 ± 0.65  arcsec/century  (Clemence 1947)
      Newtonian sum:   531.63          (Verma 2014 INPOP fit)
        - Venus:        277.42
        - Jupiter:      153.58
        - Earth:         90.04
        - Saturn:         7.30
        - Mars+other:     3.29
      General Relativity:           42.98  (Einstein 1915 prediction)
      Solar J₂ (oblateness):         0.025 (Park 2017 from MESSENGER)
      Sum:                         ~574.6  ✓ matches observed

    This is the spectral fingerprint version of "Mercury's orbit is
    a sum of contributions from neighbouring fields" — every entry
    is an independent measurement / theoretical prediction.

    The closure of the Newtonian + GR sum to within ±0.5 arcsec/century
    of the observed value is one of the most precise quantitative
    confirmations of general relativity. Park 2017's MESSENGER
    radioscience ranging measured the GR contribution at 42.98 ±
    0.04 arcsec/century — confirming Einstein 1915's prediction to
    one part in 10^4.

    Returns
    -------
    dict
        ``{ok, body, n_contributions, total_observed_arcsec_per_century,
        contributions: [...], invariant_residual_arcsec_per_century}``.

    References
    ----------
    Le Verrier U. J. J. (1859). Newtonian-perturbation calculation.
    Einstein A. (1915). GR derivation.
    Clemence G. M. (1947). *Rev. Mod. Phys.* 19, 361.
    Park R. S. et al. (2017). *Astron. J.* 153, 121.
    Verma A. K. et al. (2014). *Astron. Astrophys.* 561, A115.
    """
    contribs = MERCURY_PRECESSION_CONTRIBUTIONS
    observed = next(
        c for c in contribs if c.physics_class == "observation"
    )
    summed_predictions = sum(
        c.arcsec_per_century
        for c in contribs
        if c.physics_class != "observation"
    )
    residual = observed.arcsec_per_century - summed_predictions

    return {
        "ok": True,
        "body": "mercury",
        "n_contributions": len(contribs),
        "total_observed_arcsec_per_century": observed.arcsec_per_century,
        "summed_prediction_arcsec_per_century": summed_predictions,
        "invariant_residual_arcsec_per_century": residual,
        "contributions": [_contribution_to_dict(c) for c in contribs],
    }


def list_mercury_dynamical_spectrum() -> Dict[str, Any]:
    """Full enumeration of Mercury dynamical-spectrum data + citations.
    """
    return {
        "ok": True,
        "body": "mercury",
        "n_modes": len(MERCURY_DYNAMICAL_MODES),
        "n_contributions": len(MERCURY_PRECESSION_CONTRIBUTIONS),
        "n_sources": len(SOURCES),
        "modes": [_mode_to_dict(m) for m in MERCURY_DYNAMICAL_MODES],
        "precession_contributions": [
            _contribution_to_dict(c)
            for c in MERCURY_PRECESSION_CONTRIBUTIONS
        ],
    }


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "MERCURY_DYNAMICAL_MODES",
    "MERCURY_PRECESSION_CONTRIBUTIONS",
    "SOURCES",
    "DynamicalMode",
    "PrecessionContribution",
    "get_mercury_dynamical_spectrum",
    "get_mercury_precession_decomposition",
    "list_mercury_dynamical_spectrum",
]
