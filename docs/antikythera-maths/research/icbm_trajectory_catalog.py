"""ICBM Trajectory Catalog — query surface for the v0.22.0 trajectory
+ sensing ship (Layer B: 3-regime Earth ICBM).

Promotes the v0.22.0 architectural commitment from research notebook
§17.5.2 to a stable ship surface — **Layer B** of the four-layer
trajectory + sensing surface.

Cross-channel reach: extends Layer A short-range ballistic to the
3-regime exo-atmospheric case (boost ↔ midcourse Kepler ↔ Allen-Eggers
re-entry). Earth-only; the math generalises trivially via swap-in of
body μ + atmosphere from Layer A.

**Not a re-derivation.** Midcourse Kepler propagation uses the
standard vis-viva + flight-path-angle-at-burnout closed forms
(Bate-Mueller-White Ch. 6). Re-entry uses Allen-Eggers (1958) closed-
form ballistic solution. **No specific RV signatures, no specific
sensor sensitivities, no specific kill-vehicle parameters.**

Three bridge surfaces:

* :func:`compute_icbm_trajectory` — 3-regime propagator from burnout
  state (boost is a boundary condition).
* :func:`get_icbm_reference_profile` — textbook open-literature
  reference profile lookup (SRBM / MRBM / ICBM).
* :func:`list_icbm_reference_profiles` — full enumeration.

Reference: research notebook §17.5.2.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from .icbm_trajectory_data import (
    BOOST_BURNOUT_ALTITUDE_DEFAULT_M,
    EARTH_MU_M3_S2,
    EARTH_RADIUS_M,
    EARTH_SURFACE_G_M_S2,
    ICBM_REFERENCE_PROFILES,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    REENTRY_INTERFACE_ALTITUDE_M,
    REENTRY_RHO_0_KG_M3,
    REENTRY_SCALE_HEIGHT_M,
    SOURCES,
    ICBMReferenceProfile,
)


# ---- Memoised lookups (built at module load) -------------------------

_BY_PROFILE: Dict[str, ICBMReferenceProfile] = {
    p.profile_name: p for p in ICBM_REFERENCE_PROFILES
}
_ALL_PROFILES: List[str] = sorted(_BY_PROFILE.keys())


def _profile_to_dict(p: ICBMReferenceProfile) -> Dict[str, Any]:
    return {
        "profile_name": p.profile_name,
        "range_km": p.range_km,
        "burnout_velocity_m_s": p.burnout_velocity_m_s,
        "burnout_flight_path_angle_deg": p.burnout_flight_path_angle_deg,
        "midcourse_apex_km": p.midcourse_apex_km,
        "midcourse_duration_s": p.midcourse_duration_s,
        "reentry_velocity_m_s": p.reentry_velocity_m_s,
        "typical_warhead_bc_kg_m2": p.typical_warhead_bc_kg_m2,
        "typical_decoy_bc_kg_m2": p.typical_decoy_bc_kg_m2,
        "precision_flag": p.precision_flag,
        "notes": p.notes,
        "source_key": p.source_key,
    }


# ---------------------------------------------------------------------------
# Midcourse Kepler ellipse (Bate-Mueller-White Ch. 6)
# ---------------------------------------------------------------------------


def _midcourse_kepler(
    r_burnout_m: float,
    v_burnout_m_s: float,
    gamma_burnout_rad: float,
) -> Dict[str, Any]:
    """Kepler-ellipse propagation from burnout state.

    Input: (r, v, γ) at burnout (geocentric). Output: orbital elements
    + apex altitude + ground range + midcourse duration + re-entry
    state.

    Standard derivation — vis-viva (specific energy) + specific angular
    momentum from γ, then Kepler ellipse parameters:

        ε  = v²/2 - μ/r
        a  = -μ/(2ε)
        h  = r · v · cos γ
        e  = sqrt(1 + 2εh²/μ²)
        r_apex = a(1 + e)

    The free-flight range angle Φ (geocentric ground-range arc) is
    computed via the chord-symmetry relation
    cos Φ = ... (BMW eq. 6.4-12).
    """
    mu = EARTH_MU_M3_S2
    r = r_burnout_m
    v = v_burnout_m_s
    gamma = gamma_burnout_rad

    # Specific orbital energy
    epsilon = v * v / 2.0 - mu / r
    if epsilon >= 0.0:
        return {
            "ok": False,
            "error": (
                "Burnout state is non-elliptical (escape); Layer B "
                "requires elliptical (sub-orbital) trajectories."
            ),
        }
    semi_major_axis_m = -mu / (2.0 * epsilon)

    # Specific angular momentum
    h = r * v * math.cos(gamma)
    e_sq = 1.0 + 2.0 * epsilon * h * h / (mu * mu)
    eccentricity = math.sqrt(max(e_sq, 0.0))
    apex_radius_m = semi_major_axis_m * (1.0 + eccentricity)
    apex_altitude_m = apex_radius_m - EARTH_RADIUS_M

    # Re-entry interface — find true anomaly where r = R_earth + 100km
    r_reentry = EARTH_RADIUS_M + REENTRY_INTERFACE_ALTITUDE_M
    p_param = h * h / mu  # semi-latus rectum
    cos_nu_reentry = (p_param / r_reentry - 1.0) / max(eccentricity, 1e-12)
    cos_nu_reentry = max(-1.0, min(1.0, cos_nu_reentry))
    nu_reentry = math.acos(cos_nu_reentry)
    # We want the descending leg (nu > π) — symmetric of nu_burnout
    # via the apex.

    # True anomaly at burnout from r + γ:
    cos_nu_burnout = (p_param / r - 1.0) / max(eccentricity, 1e-12)
    cos_nu_burnout = max(-1.0, min(1.0, cos_nu_burnout))
    nu_burnout = math.acos(cos_nu_burnout)
    if gamma < 0.0:  # descending at burnout (unusual)
        nu_burnout = 2.0 * math.pi - nu_burnout

    # Ascending leg: ν from nu_burnout up to π (apex), then descending
    # past π until ν = 2π - nu_reentry.
    nu_at_reentry_descending = 2.0 * math.pi - nu_reentry

    # Free-flight range angle (geocentric arc) = ν_descending_re-entry
    # - ν_burnout (mod 2π)
    range_angle_rad = nu_at_reentry_descending - nu_burnout
    if range_angle_rad < 0.0:
        range_angle_rad += 2.0 * math.pi
    ground_range_m = EARTH_RADIUS_M * range_angle_rad

    # Re-entry velocity from vis-viva at r = R_earth + 100km:
    v_reentry = math.sqrt(2.0 * (epsilon + mu / r_reentry))
    # Re-entry flight-path angle (descending; γ_reentry > 0 measured
    # below local horizontal):
    cos_gamma_re = h / (r_reentry * v_reentry)
    cos_gamma_re = max(-1.0, min(1.0, cos_gamma_re))
    gamma_reentry_rad = math.acos(cos_gamma_re)

    # Midcourse duration via Kepler eccentric-anomaly conversion. For a
    # back-of-envelope textbook approach, integrate r·dν / v_perp.
    # Simpler: estimate midcourse duration as time-to-apex * 2 from
    # vis-viva mean motion. Use Kepler's third law for period:
    period_s = 2.0 * math.pi * math.sqrt(
        semi_major_axis_m ** 3 / mu
    )
    # Eccentric anomaly at burnout / re-entry
    def _ecc_anomaly(nu: float) -> float:
        # E from ν: tan(E/2) = sqrt((1-e)/(1+e)) · tan(ν/2)
        return 2.0 * math.atan2(
            math.sqrt(max(1 - eccentricity, 0.0)) * math.sin(nu / 2.0),
            math.sqrt(max(1 + eccentricity, 0.0)) * math.cos(nu / 2.0),
        )
    E_burnout = _ecc_anomaly(nu_burnout)
    E_reentry = _ecc_anomaly(nu_at_reentry_descending)
    # Mean anomaly M = E - e sin E
    M_burnout = E_burnout - eccentricity * math.sin(E_burnout)
    M_reentry = E_reentry - eccentricity * math.sin(E_reentry)
    if M_reentry < M_burnout:
        M_reentry += 2.0 * math.pi
    midcourse_duration_s = (M_reentry - M_burnout) * period_s / (2.0 * math.pi)

    return {
        "ok": True,
        "semi_major_axis_m": semi_major_axis_m,
        "eccentricity": eccentricity,
        "specific_energy_J_kg": epsilon,
        "specific_angular_momentum_m2_s": h,
        "apex_altitude_m": apex_altitude_m,
        "apex_radius_m": apex_radius_m,
        "ground_range_m": ground_range_m,
        "ground_range_km": ground_range_m / 1000.0,
        "midcourse_duration_s": midcourse_duration_s,
        "reentry_velocity_m_s": v_reentry,
        "reentry_flight_path_angle_deg": math.degrees(gamma_reentry_rad),
        "reentry_altitude_m": REENTRY_INTERFACE_ALTITUDE_M,
        "true_anomaly_burnout_rad": nu_burnout,
        "true_anomaly_reentry_rad": nu_at_reentry_descending,
    }


# ---------------------------------------------------------------------------
# Re-entry (Allen-Eggers, NACA Report 1381, 1958)
# ---------------------------------------------------------------------------


def _allen_eggers_reentry(
    v_e_m_s: float,
    gamma_e_rad: float,
    bc_kg_m2: float,
    n_samples: int,
) -> Dict[str, Any]:
    """Allen-Eggers closed-form ballistic re-entry.

    The Allen-Eggers solution assumes constant flight-path angle γ_e
    through the re-entry corridor. Velocity decays as

        v(h) = v_e · exp[-K · exp(-h/H)]
        K    = ρ₀ · H / (2 · BC · sin γ_e)

    and the peak deceleration occurs at the altitude where dV/dt is
    maximum — closed-form

        h_peak_decel = H · ln(K)
        a_peak       = -v_e² · sin γ_e / (2 e · H)

    where e is Euler's number. The peak deceleration is independent
    of BC — that's the famous Allen-Eggers result. **The
    BC-differential discrimination physics rides on the *altitude*
    at which peak decel occurs, not its magnitude.**
    """
    H = REENTRY_SCALE_HEIGHT_M
    rho_0 = REENTRY_RHO_0_KG_M3

    if gamma_e_rad <= 1e-6:
        return {
            "ok": False,
            "error": "Re-entry flight-path angle too shallow for "
                     "Allen-Eggers (γ must be > 0).",
        }

    K = rho_0 * H / (2.0 * bc_kg_m2 * math.sin(gamma_e_rad))
    if K <= 0.0:
        return {"ok": False, "error": "Invalid Allen-Eggers K parameter."}

    h_peak_decel_m = H * math.log(K) if K > 1.0 else 0.0
    # Peak deceleration magnitude (independent of BC)
    a_peak_m_s2 = (v_e_m_s ** 2) * math.sin(gamma_e_rad) / (
        2.0 * math.e * H
    )

    # Altitude profile from re-entry interface (100 km) down to surface
    samples: List[Dict[str, float]] = []
    if n_samples > 1:
        h_top = REENTRY_INTERFACE_ALTITUDE_M
        for i in range(n_samples):
            h = h_top * (1.0 - i / (n_samples - 1))
            v = v_e_m_s * math.exp(-K * math.exp(-h / H))
            # Local deceleration via dV/dh:
            #   dV/dh = -V · K · exp(-h/H) · (-1/H) = V·K·exp(-h/H)/H
            #   a = V · dV/dh · sin γ (along path) — sign convention
            local_decel = (v * v) * K * math.exp(-h / H) / H * math.sin(gamma_e_rad)
            samples.append({
                "altitude_m": h,
                "velocity_m_s": v,
                "deceleration_m_s2": local_decel,
            })

    # Surface impact velocity
    v_surface = v_e_m_s * math.exp(-K)

    return {
        "ok": True,
        "v_entry_m_s": v_e_m_s,
        "gamma_entry_deg": math.degrees(gamma_e_rad),
        "ballistic_coefficient_kg_m2": bc_kg_m2,
        "K_parameter": K,
        "peak_deceleration_m_s2": a_peak_m_s2,
        "peak_deceleration_g": a_peak_m_s2 / EARTH_SURFACE_G_M_S2,
        "altitude_of_peak_decel_m": h_peak_decel_m,
        "surface_impact_velocity_m_s": v_surface,
        "n_samples": len(samples),
        "samples": samples,
    }


# ---------------------------------------------------------------------------
# Public bridge surfaces
# ---------------------------------------------------------------------------


def compute_icbm_trajectory(
    burnout_velocity_m_s: float,
    burnout_flight_path_angle_deg: float,
    burnout_altitude_m: float = BOOST_BURNOUT_ALTITUDE_DEFAULT_M,
    ballistic_coefficient_kg_m2: float = 10000.0,
    n_reentry_samples: int = 33,
) -> Dict[str, Any]:
    """3-regime Earth ICBM ballistic trajectory propagator.

    Boost is a boundary condition (user supplies burnout state v, γ,
    h). Midcourse propagates the Kepler ellipse to the re-entry
    interface (100 km). Re-entry uses Allen-Eggers ballistic re-entry
    (NACA Report 1381, 1958).

    **Boost is intentionally not modelled** — boost-phase trajectory
    requires vehicle-specific Isp, thrust profile, gravity-turn pitch
    program. Those cross into operationally-sensitive territory; the
    publishable Layer B surface starts from burnout state.

    Parameters
    ----------
    burnout_velocity_m_s : float
        Speed at end of boost (typically 1500-7500 m/s depending on
        range class).
    burnout_flight_path_angle_deg : float
        Burnout flight-path angle above local horizontal (typically
        20-45° for sub-orbital ballistic; smaller for longer range).
    burnout_altitude_m : float, default 200000
        Altitude at burnout (typically 150-300 km).
    ballistic_coefficient_kg_m2 : float, default 10000
        Re-entry ballistic coefficient BC = m/(C_d·A). Heavy compact RV
        is 5000-15000 kg/m²; light decoy is 10-50 kg/m².
    n_reentry_samples : int, default 33
        Number of re-entry trajectory samples.

    Returns
    -------
    dict
        ``{ok, midcourse: {...Kepler elements + apex + ground range +
        duration + re-entry state...}, reentry: {...Allen-Eggers
        velocity profile + peak decel...}}``.

    References
    ----------
    Bate R. R., Mueller D. D., White J. E. (1971). *Fundamentals of
    Astrodynamics*, Dover. Ch. 6 (ballistic missile midcourse).

    Allen H. J., Eggers A. J. (1958). NACA Report 1381 (closed-form
    ballistic re-entry).

    Vallado D. A. (2013). *Fundamentals of Astrodynamics*, 4th ed.,
    §9.6.

    Sessler/UCS (2000). *Countermeasures* (BC-differential
    discrimination physics).
    """
    if burnout_velocity_m_s <= 0.0:
        return {
            "ok": False,
            "error": f"burnout_velocity_m_s must be positive; got "
                     f"{burnout_velocity_m_s}",
        }
    if not (0.0 < burnout_flight_path_angle_deg < 90.0):
        return {
            "ok": False,
            "error": (
                "burnout_flight_path_angle_deg must be in (0, 90); got "
                f"{burnout_flight_path_angle_deg}"
            ),
        }
    if burnout_altitude_m < 0.0:
        return {
            "ok": False,
            "error": f"burnout_altitude_m must be >= 0; got "
                     f"{burnout_altitude_m}",
        }
    if ballistic_coefficient_kg_m2 <= 0.0:
        return {
            "ok": False,
            "error": (
                "ballistic_coefficient_kg_m2 must be positive; got "
                f"{ballistic_coefficient_kg_m2}"
            ),
        }

    r_burnout = EARTH_RADIUS_M + burnout_altitude_m
    gamma_burnout_rad = math.radians(burnout_flight_path_angle_deg)

    midcourse = _midcourse_kepler(
        r_burnout, burnout_velocity_m_s, gamma_burnout_rad
    )
    if not midcourse["ok"]:
        return midcourse

    reentry = _allen_eggers_reentry(
        v_e_m_s=midcourse["reentry_velocity_m_s"],
        gamma_e_rad=math.radians(midcourse["reentry_flight_path_angle_deg"]),
        bc_kg_m2=ballistic_coefficient_kg_m2,
        n_samples=n_reentry_samples,
    )
    if not reentry["ok"]:
        return reentry

    total_flight_time_s = midcourse["midcourse_duration_s"] + (
        # Allen-Eggers descent time approximation: h_top / (v_e · sin γ)
        REENTRY_INTERFACE_ALTITUDE_M / (
            midcourse["reentry_velocity_m_s"]
            * math.sin(math.radians(
                midcourse["reentry_flight_path_angle_deg"]
            ))
        )
    )

    return {
        "ok": True,
        "burnout": {
            "velocity_m_s": burnout_velocity_m_s,
            "flight_path_angle_deg": burnout_flight_path_angle_deg,
            "altitude_m": burnout_altitude_m,
        },
        "midcourse": midcourse,
        "reentry": reentry,
        "total_flight_time_s": total_flight_time_s,
        "ballistic_coefficient_kg_m2": ballistic_coefficient_kg_m2,
    }


def get_icbm_reference_profile(
    profile_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Textbook open-literature reference profile lookup.

    Returns canonical reference profiles for SRBM / MRBM / ICBM range
    classes from Wilkening 2000 + Sessler/UCS 2000. **Not operational
    parameters** — these are the textbook reference values used as
    sanity-check fixtures.
    """
    if profile_name is not None:
        name = str(profile_name).lower().strip()
        if name not in _BY_PROFILE:
            return {
                "ok": False,
                "error": (
                    f"unknown profile {profile_name!r}; known profiles "
                    f"are {_ALL_PROFILES}"
                ),
            }
        return {
            "ok": True,
            "profile_name": name,
            "profile": _profile_to_dict(_BY_PROFILE[name]),
        }

    return {
        "ok": True,
        "n_profiles": len(_ALL_PROFILES),
        "profiles": {
            name: _profile_to_dict(_BY_PROFILE[name])
            for name in _ALL_PROFILES
        },
    }


def list_icbm_reference_profiles() -> Dict[str, Any]:
    """Full enumeration of ICBM reference profiles + citations."""
    return {
        "ok": True,
        "n_profiles": len(_ALL_PROFILES),
        "n_sources": len(SOURCES),
        "profiles": [_profile_to_dict(p) for p in ICBM_REFERENCE_PROFILES],
    }


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "EARTH_MU_M3_S2",
    "EARTH_RADIUS_M",
    "ICBM_REFERENCE_PROFILES",
    "SOURCES",
    "ICBMReferenceProfile",
    "compute_icbm_trajectory",
    "get_icbm_reference_profile",
    "list_icbm_reference_profiles",
]
