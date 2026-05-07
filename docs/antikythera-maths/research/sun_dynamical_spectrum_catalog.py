"""Sol Sun Dynamical Spectrum Catalog — query surface for the v0.24.3
ship (fourth per-body dynamical-spectrum surface).

Promotes the v0.24.3 architectural commitment from research notebook
§17.7 to a stable ship surface — a **methodology extension** from
rigid-body action-angle decomposition (Mercury / Luna / Mars) to
**stellar-oscillation continuum normal-mode spectrum**
(helioseismology).

Where v0.24.0–v0.24.2 decomposed each body's dynamical state into
~10 angle/action modes, v0.24.3 ships the helioseismic asymptotic
relation as a closure invariant analogous to Luna's Saros
commensurability — three constants (Δν, δν, ε) generate the
entire continuum mode spectrum to ~1 μHz precision.

Three bridge surfaces:

* :func:`get_sun_dynamical_spectrum` — sample p-mode catalog +
  asymptotic-relation constants.
* :func:`get_helioseismic_asymptotic_relation` — Δν, δν, ν_max +
  predicted-vs-measured residuals (the closure invariant).
* :func:`list_sun_dynamical_spectrum` — full enumeration.

Reference: research notebook §17.7.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .sun_dynamical_spectrum_data import (
    HELIOSEISMIC_MODES,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
    SUN_ASYMPTOTIC_PHASE_OFFSET,
    SUN_EFFECTIVE_TEMPERATURE_K,
    SUN_LARGE_FREQUENCY_SEPARATION_UHZ,
    SUN_LUMINOSITY_W,
    SUN_MASS_KG,
    SUN_NU_MAX_UHZ,
    SUN_PMODE_FREQUENCY_CYCLE_SHIFT_UHZ,
    SUN_RADIUS_M,
    SUN_SMALL_FREQUENCY_SEPARATION_UHZ,
    SUN_SURFACE_GRAVITY_M_S2,
    HelioseismicMode,
)


def _mode_to_dict(m: HelioseismicMode) -> Dict[str, Any]:
    return {
        "n": m.n,
        "l": m.l,
        "frequency_uhz": m.frequency_uhz,
        "mode_class": m.mode_class,
        "notes": m.notes,
        "source_key": m.source_key,
        "precision_flag": m.precision_flag,
    }


def _asymptotic_predicted_uhz(
    n: int, l: int,
    delta_nu: float = SUN_LARGE_FREQUENCY_SEPARATION_UHZ,
    delta_small: float = SUN_SMALL_FREQUENCY_SEPARATION_UHZ,
    epsilon: float = SUN_ASYMPTOTIC_PHASE_OFFSET,
) -> float:
    """Tassoul 1980 asymptotic relation prediction.

    ν_{n,l} ≈ Δν · (n + l/2 + ε) - δν · l(l+1) / (n + l/2 + ε)

    The leading-order term Δν · (n + l/2 + ε) gives the "main p-mode
    comb"; the second-order δν correction breaks the (l=0, l=2)
    degeneracy and is sensitive to the helium-core sound-speed
    gradient.
    """
    nominal = n + l / 2.0 + epsilon
    return (
        delta_nu * nominal
        - delta_small * l * (l + 1) / nominal
    )


def get_sun_dynamical_spectrum() -> Dict[str, Any]:
    """Sun's helioseismic p-mode catalog + asymptotic-relation
    constants.

    Fourth per-body dynamical-spectrum surface in v0.24.x, and the
    first **stellar** entry. Methodology extension from rigid-body
    action-angle (Mercury / Luna / Mars) to continuum normal-mode
    spectrum.

    Headlines:
      * **Δν = 135.1 μHz** — large frequency separation between
        consecutive radial orders n. Sound-travel-time inverse;
        ∝ √(M/R³); the ν-max-and-Δν asteroseismic-anchor pair.
      * **δν = 9.0 μHz** — small frequency separation between
        l=0 and l=2 modes; sensitive to deep-interior sound-speed
        gradient + helium-core composition.
      * **ν_max = 3090 μHz** — peak amplitude frequency; predicted
        by Brown 1991 to scale as g/√T_eff (validated extensively
        across asteroseismic targets).
      * **Sample 20 p-modes** (n=18-25, l=0-2) from BiSON 30-yr
        catalog (Davies 2014). The "main p-mode comb."

    The Sun is the **only star** where individual modes are
    resolvable to high SNR via spatially-resolved Doppler imaging
    (GOLF/SoHO low-degree; SDO-HMI mid-degree; BiSON sub-mHz).
    """
    return {
        "ok": True,
        "body": "sol",
        "n_modes": len(HELIOSEISMIC_MODES),
        "modes": [_mode_to_dict(m) for m in HELIOSEISMIC_MODES],
        "constants": {
            "mass_kg": SUN_MASS_KG,
            "radius_m": SUN_RADIUS_M,
            "luminosity_w": SUN_LUMINOSITY_W,
            "effective_temperature_K": SUN_EFFECTIVE_TEMPERATURE_K,
            "surface_gravity_m_s2": SUN_SURFACE_GRAVITY_M_S2,
            "large_frequency_separation_uhz":
                SUN_LARGE_FREQUENCY_SEPARATION_UHZ,
            "small_frequency_separation_uhz":
                SUN_SMALL_FREQUENCY_SEPARATION_UHZ,
            "nu_max_uhz": SUN_NU_MAX_UHZ,
            "asymptotic_phase_offset": SUN_ASYMPTOTIC_PHASE_OFFSET,
            "pmode_frequency_cycle_shift_uhz":
                SUN_PMODE_FREQUENCY_CYCLE_SHIFT_UHZ,
        },
    }


def get_helioseismic_asymptotic_relation() -> Dict[str, Any]:
    """Helioseismic asymptotic-relation closure invariant — THE
    headline of v0.24.3.

    The Tassoul 1980 asymptotic relation:

        ν_{n,l} ≈ Δν · (n + l/2 + ε) - δν · l(l+1) / (n + l/2 + ε)

    predicts the entire p-mode comb from just three constants
    (Δν, δν, ε) — analogous to Luna's Saros commensurability where
    223:239:242 integer triple predicts eclipse recurrence from
    three months.

    Closure: agreement of asymptotic prediction with measured
    frequencies for hundreds of (n, l) pairs to ~1 μHz precision is
    the v0.24.3 closure invariant — pinned by
    `test_asymptotic_relation_closure_invariant` (max residual
    across the catalog).

    For each catalogued mode:

    * predicted_uhz = asymptotic-relation prediction
    * measured_uhz = BiSON / SOI-MDI catalog value
    * residual_uhz = measured - predicted

    The residual structure is itself diagnostic — systematic
    residual patterns at specific (n, l) reveal interior structure
    (the Brun 2002 / Christensen-Dalsgaard 2002 inversion methodology).

    Returns
    -------
    dict
        ``{ok, body, asymptotic_constants, n_modes, max_residual_uhz,
        rms_residual_uhz, modes: [{n, l, measured_uhz, predicted_uhz,
        residual_uhz}, ...]}``.
    """
    rows: List[Dict[str, Any]] = []
    residuals: List[float] = []
    for m in HELIOSEISMIC_MODES:
        pred = _asymptotic_predicted_uhz(m.n, m.l)
        residual = m.frequency_uhz - pred
        residuals.append(residual)
        rows.append({
            "n": m.n,
            "l": m.l,
            "measured_uhz": m.frequency_uhz,
            "predicted_uhz": pred,
            "residual_uhz": residual,
        })

    max_residual = max(abs(r) for r in residuals)
    rms_residual = (
        sum(r * r for r in residuals) / len(residuals)
    ) ** 0.5

    return {
        "ok": True,
        "body": "sol",
        "asymptotic_constants": {
            "large_frequency_separation_uhz":
                SUN_LARGE_FREQUENCY_SEPARATION_UHZ,
            "small_frequency_separation_uhz":
                SUN_SMALL_FREQUENCY_SEPARATION_UHZ,
            "phase_offset_epsilon": SUN_ASYMPTOTIC_PHASE_OFFSET,
            "nu_max_uhz": SUN_NU_MAX_UHZ,
        },
        "n_modes": len(HELIOSEISMIC_MODES),
        "max_residual_uhz": max_residual,
        "rms_residual_uhz": rms_residual,
        "modes": rows,
    }


def list_sun_dynamical_spectrum() -> Dict[str, Any]:
    """Full enumeration of Sun dynamical-spectrum data + citations."""
    return {
        "ok": True,
        "body": "sol",
        "n_modes": len(HELIOSEISMIC_MODES),
        "n_sources": len(SOURCES),
        "modes": [_mode_to_dict(m) for m in HELIOSEISMIC_MODES],
    }


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "HELIOSEISMIC_MODES",
    "SOURCES",
    "HelioseismicMode",
    "get_sun_dynamical_spectrum",
    "get_helioseismic_asymptotic_relation",
    "list_sun_dynamical_spectrum",
]
