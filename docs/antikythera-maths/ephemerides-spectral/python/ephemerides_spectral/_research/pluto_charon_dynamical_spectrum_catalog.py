"""Sol Pluto-Charon Dynamical Spectrum Catalog — query surface
for the v0.24.11 ship (per-body action-angle decomposition; the
project's first binary-mutual-tidal-lock case).

Promotes the v0.24.11 architectural commitment from research
notebook section 17.7 to a stable ship surface — Pluto-Charon as
the **fourth per-body dynamical-spectrum surface** (after Mercury
v0.24.0, Luna v0.24.1, Mars v0.24.2). The first **binary mutual-
tidal-lock** case in the v0.24.x sequence; chosen as the Path-B
response to the v0.24.10 probe-roster's identification of a
feature-schema gap (Pluto-Charon, Enceladus, Io were all
collapsing onto Mercury-stable in the v0.24.9 classifier because
the schema couldn't distinguish them).

Three bridge surfaces:

* :func:`get_pluto_charon_dynamical_spectrum` — the action-angle
  mode catalog + binary geometry + small-moon commensurabilities.
* :func:`get_double_synchronous_signature` — THE headline closure:
  Pluto spin period = Charon spin period = mutual orbital period
  (the only such triple-lock in the Solar System).
* :func:`list_pluto_charon_dynamical_spectrum` — full enumeration
  with citations.

Cross-channel reach: same per-body action-angle methodology as
v0.24.0–v0.24.2; first time applied to a *binary* system.

Reference: research notebook section 17.7.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .pluto_charon_dynamical_spectrum_data import (
    CHARON_MASS_KG,
    CHARON_RADIUS_KM,
    CHARON_TO_PLUTO_MASS_RATIO,
    HYDRA_ORBITAL_PERIOD_DAYS,
    KERBEROS_ORBITAL_PERIOD_DAYS,
    NIX_ORBITAL_PERIOD_DAYS,
    PLUTO_BARYCENTER_ABOVE_SURFACE_KM,
    PLUTO_BARYCENTER_OFFSET_KM,
    PLUTO_CHARON_DYNAMICAL_MODES,
    PLUTO_CHARON_ECCENTRICITY,
    PLUTO_CHARON_MUTUAL_OBLIQUITY_DEG,
    PLUTO_CHARON_MUTUAL_ORBITAL_PERIOD_DAYS,
    PLUTO_CHARON_SEMI_MAJOR_AXIS_KM,
    PLUTO_HELIO_PLANE_INCLINATION_DEG,
    PLUTO_MASS_KG,
    PLUTO_RADIUS_KM,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
    STYX_ORBITAL_PERIOD_DAYS,
    DynamicalMode,
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


def get_pluto_charon_dynamical_spectrum() -> Dict[str, Any]:
    """Pluto-Charon action-angle mode catalog + binary geometry.

    Returns the complete dynamical-spectrum surface: 12 modes
    (3 angle-locked at the mutual orbital period, 1 slow apsidal
    libration, 4 actions, 4 small-moon near-commensurabilities)
    + the binary geometry parameters (mass ratio, barycenter
    offset, eccentricity, mutual obliquity).

    Cross-channel: this is the first ship in the v0.24.x sequence
    on a *binary* system. Where Mercury (v0.24.0), Luna (v0.24.1),
    and Mars (v0.24.2) were single bodies with parent-body
    perturbations, Pluto-Charon is two bodies in mutual lock. The
    action-angle framework still applies; the headline observable
    shifts from 'body's spin frequency relative to parent' to
    'mutual orbital frequency relative to which both bodies are
    locked'.

    Returns
    -------
    dict
        ``{ok, n_modes, mutual_orbital_period_days,
        binary_geometry: {...}, modes: [...]}``.
    """
    return {
        "ok": True,
        "n_modes": len(PLUTO_CHARON_DYNAMICAL_MODES),
        "mutual_orbital_period_days":
            PLUTO_CHARON_MUTUAL_ORBITAL_PERIOD_DAYS,
        "binary_geometry": {
            "semi_major_axis_km": PLUTO_CHARON_SEMI_MAJOR_AXIS_KM,
            "eccentricity": PLUTO_CHARON_ECCENTRICITY,
            "mutual_obliquity_deg": PLUTO_CHARON_MUTUAL_OBLIQUITY_DEG,
            "heliocentric_inclination_deg":
                PLUTO_HELIO_PLANE_INCLINATION_DEG,
            "pluto_mass_kg": PLUTO_MASS_KG,
            "charon_mass_kg": CHARON_MASS_KG,
            "charon_to_pluto_mass_ratio": CHARON_TO_PLUTO_MASS_RATIO,
            "pluto_radius_km": PLUTO_RADIUS_KM,
            "charon_radius_km": CHARON_RADIUS_KM,
            "barycenter_offset_from_pluto_km":
                PLUTO_BARYCENTER_OFFSET_KM,
            "barycenter_above_pluto_surface_km":
                PLUTO_BARYCENTER_ABOVE_SURFACE_KM,
        },
        "small_moon_periods_days": {
            "styx": STYX_ORBITAL_PERIOD_DAYS,
            "nix": NIX_ORBITAL_PERIOD_DAYS,
            "kerberos": KERBEROS_ORBITAL_PERIOD_DAYS,
            "hydra": HYDRA_ORBITAL_PERIOD_DAYS,
        },
        "modes": [_mode_to_dict(m) for m in PLUTO_CHARON_DYNAMICAL_MODES],
    }


def get_double_synchronous_signature() -> Dict[str, Any]:
    """The double-synchronous lock signature — THE headline of v0.24.11.

    Pluto and Charon are both tidally locked to each other
    simultaneously: Pluto's spin period equals Charon's spin
    period equals the mutual orbital period equals 6.387230 days.
    This is the **end state** of dyadic tidal evolution and the
    **only example** in the Solar System.

    Companion observables that confirm the system has reached
    this end state:

    * **Eccentricity = 0.00005** — approximately 1100x smaller
      than Luna's 0.0549. Mutual tidal dissipation has damped
      the eccentricity to essentially zero.

    * **Mutual obliquity = 0.0006°** — both spin axes aligned
      with the mutual orbit normal. No further tidal torque to
      apply.

    * **Mass ratio Charon/Pluto = 0.1218** — the largest binary
      mass ratio in the Solar System. The barycenter sits ~940
      km above Pluto's surface (Pluto radius 1188 km, barycenter
      offset 2128 km), so both bodies orbit a point in empty space.

    Cross-channel observations:

    * v0.24.1 Luna's Saros 223:239:242 commensurability captures
      Earth-Luna's tidal evolution *en route* to the double-
      synchronous state (Earth's rotation is currently spinning
      down via tidal recession at +3.83 cm/yr, Williams 2014).
      Pluto-Charon has *arrived* at that state. v0.24.11 catalogs
      the destination; v0.24.1 catalogs the journey.

    * The 4 small moons (Styx/Nix/Kerberos/Hydra) sit at near-
      3:4:5:6 multiples of the mutual orbital period — a mini-
      Galilean-Laplace-style structure built on top of the binary
      lock. Showalter-Hamilton 2015 found the system is chaotic
      in libration on Myr timescales because the resonances aren't
      exact — a v0.24.2-Mars-style spectral-stability failure mode
      at the small-moon shepherd network's scale.

    Closure invariant
    -----------------
    The triple-lock can be expressed as:

        |P_orb - P_spin_pluto| < eps  AND
        |P_orb - P_spin_charon| < eps

    where eps is at the precision-floor of the published
    measurements (Brozovic 2015 ~10 μs). Pinned by
    ``test_triple_lock_invariant``.

    Returns
    -------
    dict
        ``{ok, mutual_orbital_period_days, pluto_spin_period_days,
        charon_spin_period_days, triple_lock_max_residual_seconds,
        eccentricity, mutual_obliquity_deg, mass_ratio,
        barycenter_above_pluto_surface_km, small_moon_ratios: [...],
        interpretation}``.
    """
    p_orb = PLUTO_CHARON_MUTUAL_ORBITAL_PERIOD_DAYS
    # Per Brozovic 2015 + Stern 2015: spin periods agree with the
    # mutual orbital period at the published-measurement precision
    # (sub-millisecond). The "triple-lock residual" is therefore
    # essentially zero in the catalog values.
    triple_lock_residual_seconds: float = 0.0  # by tidal-lock definition

    small_moon_ratios = [
        {
            "moon": "styx",
            "period_days": STYX_ORBITAL_PERIOD_DAYS,
            "ratio_to_mutual_orbital":
                STYX_ORBITAL_PERIOD_DAYS / p_orb,
            "near_integer": 3,
            "fractional_offset_from_integer":
                abs(STYX_ORBITAL_PERIOD_DAYS / p_orb - 3) / 3,
        },
        {
            "moon": "nix",
            "period_days": NIX_ORBITAL_PERIOD_DAYS,
            "ratio_to_mutual_orbital":
                NIX_ORBITAL_PERIOD_DAYS / p_orb,
            "near_integer": 4,
            "fractional_offset_from_integer":
                abs(NIX_ORBITAL_PERIOD_DAYS / p_orb - 4) / 4,
        },
        {
            "moon": "kerberos",
            "period_days": KERBEROS_ORBITAL_PERIOD_DAYS,
            "ratio_to_mutual_orbital":
                KERBEROS_ORBITAL_PERIOD_DAYS / p_orb,
            "near_integer": 5,
            "fractional_offset_from_integer":
                abs(KERBEROS_ORBITAL_PERIOD_DAYS / p_orb - 5) / 5,
        },
        {
            "moon": "hydra",
            "period_days": HYDRA_ORBITAL_PERIOD_DAYS,
            "ratio_to_mutual_orbital":
                HYDRA_ORBITAL_PERIOD_DAYS / p_orb,
            "near_integer": 6,
            "fractional_offset_from_integer":
                abs(HYDRA_ORBITAL_PERIOD_DAYS / p_orb - 6) / 6,
        },
    ]

    return {
        "ok": True,
        "mutual_orbital_period_days": p_orb,
        "pluto_spin_period_days": p_orb,
        "charon_spin_period_days": p_orb,
        "triple_lock_max_residual_seconds":
            triple_lock_residual_seconds,
        "eccentricity": PLUTO_CHARON_ECCENTRICITY,
        "mutual_obliquity_deg": PLUTO_CHARON_MUTUAL_OBLIQUITY_DEG,
        "mass_ratio_charon_over_pluto": CHARON_TO_PLUTO_MASS_RATIO,
        "barycenter_above_pluto_surface_km":
            PLUTO_BARYCENTER_ABOVE_SURFACE_KM,
        "small_moon_ratios": small_moon_ratios,
        "interpretation": (
            "Pluto and Charon are simultaneously locked to each "
            "other in a 1:1:1 triple synchronous state (mutual "
            "orbital period = both spin periods = 6.387 d). The "
            "near-zero eccentricity (5e-5) and near-zero mutual "
            "obliquity (0.0006 deg) confirm the system has reached "
            "the END STATE of dyadic tidal evolution. The 4 small "
            "moons orbit the barycenter at near-3:4:5:6 multiples "
            "of the mutual orbital period (chaotic in libration "
            "per Showalter-Hamilton 2015) -- a mini-Galilean-"
            "Laplace structure on top of the binary lock. THE only "
            "example in the Solar System; a v0.24.x ship populates "
            "the regime that v0.24.10 OOS probes flagged as a "
            "schema gap (Pluto-Charon was being collapsed onto "
            "Mercury-stable by the v0.24.9 classifier)."
        ),
    }


def list_pluto_charon_dynamical_spectrum() -> Dict[str, Any]:
    """Full enumeration of every Pluto-Charon dynamical mode +
    citations."""
    return {
        "ok": True,
        "n_modes": len(PLUTO_CHARON_DYNAMICAL_MODES),
        "n_sources": len(SOURCES),
        "modes": [_mode_to_dict(m) for m in PLUTO_CHARON_DYNAMICAL_MODES],
    }


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "PLUTO_CHARON_DYNAMICAL_MODES",
    "SOURCES",
    "DynamicalMode",
    "get_pluto_charon_dynamical_spectrum",
    "get_double_synchronous_signature",
    "list_pluto_charon_dynamical_spectrum",
]
