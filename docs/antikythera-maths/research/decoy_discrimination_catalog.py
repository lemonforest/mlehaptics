"""Decoy Discrimination Catalog — query surface for the v0.22.0
trajectory + sensing ship (Layer C(b): BC-differential discrimination).

Promotes the v0.22.0 architectural commitment from research notebook
§17.5.4 to a stable ship surface — **Layer C(b)** of the four-layer
trajectory + sensing surface.

Cross-channel reach: closes Layer B + Layer C with the **only
publishable physics-based midcourse-surviving discrimination
mechanism** — the differential ballistic-coefficient deceleration in
the upper atmospheric drag tail (60-100 km altitude band, Sessler/UCS
*Countermeasures* 2000).

In vacuum (midcourse), heavy compact RV and light replica decoy
follow identical trajectories. On re-entry, the heavier RV
(BC ~10000 kg/m²) decelerates slowly in the upper atmosphere; the
lighter decoy (BC ~50 kg/m²) decelerates rapidly. The **discrimination
altitude** is where the velocity gap exceeds a measurable threshold.

**Not a re-derivation.** Allen-Eggers velocity-vs-altitude is the
canonical closed-form (NACA Report 1381, 1958). BC class baselines
are open-literature (Sessler/UCS 2000). **No specific weapon-system
parameters, no specific decoy designs, no specific discrimination
algorithm thresholds.** Publishable physics only.

Three bridge surfaces:

* :func:`compute_bc_differential` — Δv vs altitude profile for two
  BCs.
* :func:`get_bc_reference_class` / :func:`list_bc_reference_classes` —
  reference BC class catalog access.
* :func:`compute_discrimination_altitude` — find the altitude at
  which Δv exceeds a measurable threshold.

Reference: research notebook §17.5.4.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from .decoy_discrimination_data import (
    BC_REFERENCE_CLASSES,
    DEFAULT_DISCRIMINATION_BAND_LOWER_KM,
    DEFAULT_DISCRIMINATION_BAND_UPPER_KM,
    DEFAULT_RHO_0_KG_M3,
    DEFAULT_SCALE_HEIGHT_M,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
    BCReferenceClass,
)


# ---- Memoised lookups (built at module load) -------------------------

_BY_CLASS: Dict[str, BCReferenceClass] = {
    c.class_name: c for c in BC_REFERENCE_CLASSES
}
_ALL_CLASSES: List[str] = sorted(_BY_CLASS.keys())


def _class_to_dict(c: BCReferenceClass) -> Dict[str, Any]:
    return {
        "class_name": c.class_name,
        "typical_bc_kg_m2": c.typical_bc_kg_m2,
        "typical_mass_kg": c.typical_mass_kg,
        "typical_diameter_m": c.typical_diameter_m,
        "drag_coefficient": c.drag_coefficient,
        "precision_flag": c.precision_flag,
        "notes": c.notes,
        "source_key": c.source_key,
    }


# ---------------------------------------------------------------------------
# Allen-Eggers velocity-vs-altitude (NACA Report 1381, 1958)
# ---------------------------------------------------------------------------


def _allen_eggers_velocity(
    v_e_m_s: float,
    gamma_e_rad: float,
    bc_kg_m2: float,
    altitude_m: float,
) -> float:
    """Allen-Eggers velocity at altitude h.

    v(h) = v_e · exp[-K · exp(-h/H)]
    K    = ρ₀ · H / (2 · BC · sin γ_e)
    """
    H = DEFAULT_SCALE_HEIGHT_M
    K = DEFAULT_RHO_0_KG_M3 * H / (2.0 * bc_kg_m2 * math.sin(gamma_e_rad))
    return v_e_m_s * math.exp(-K * math.exp(-altitude_m / H))


# ---------------------------------------------------------------------------
# Public bridge surfaces
# ---------------------------------------------------------------------------


def compute_bc_differential(
    bc_heavy_kg_m2: float,
    bc_light_kg_m2: float,
    entry_velocity_m_s: float = 7000.0,
    entry_flight_path_angle_deg: float = 23.0,
    altitude_band_lower_km: float = DEFAULT_DISCRIMINATION_BAND_LOWER_KM,
    altitude_band_upper_km: float = DEFAULT_DISCRIMINATION_BAND_UPPER_KM,
    n_samples: int = 41,
) -> Dict[str, Any]:
    """BC-differential velocity separation in the upper atmospheric
    drag tail.

    Computes ``Δv(h) = v_heavy(h) - v_light(h)`` over the
    discrimination altitude band [lower, upper]. The heavier RV
    (higher BC) decelerates more slowly than the lighter decoy
    (lower BC); Δv grows with decreasing altitude until the decoy is
    effectively at terminal velocity.

    This is the **only physics-based midcourse-surviving
    discriminator** (Sessler/UCS 2000). At the re-entry interface
    (100 km), Δv ≈ 0 (both objects still at v_entry). By 60 km, Δv
    can reach ~5000 m/s for a (10000, 50) BC pair.

    Parameters
    ----------
    bc_heavy_kg_m2 : float
        Heavier object's ballistic coefficient (kg/m²) — typically
        warhead-class (5000-15000).
    bc_light_kg_m2 : float
        Lighter object's ballistic coefficient (kg/m²) — typically
        decoy-class (10-50).
    entry_velocity_m_s : float, default 7000
        Velocity at 100 km re-entry interface (m/s). Typical ICBM-
        class re-entry speed.
    entry_flight_path_angle_deg : float, default 23
        Flight-path angle below local horizontal at re-entry interface
        (degrees).
    altitude_band_lower_km : float, default 60
        Lower bound of the discrimination altitude band (km).
    altitude_band_upper_km : float, default 100
        Upper bound (km). 100 km = Karman line / re-entry interface.
    n_samples : int, default 41
        Number of altitude samples in the band.

    Returns
    -------
    dict
        ``{ok, samples: [{altitude_m, v_heavy_m_s, v_light_m_s,
        delta_v_m_s, delta_v_fraction}, ...], peak_delta_v_m_s,
        altitude_at_peak_delta_v_m, ...}``.

    References
    ----------
    Allen H. J., Eggers A. J. (1958). NACA Report 1381 (closed-form
    ballistic re-entry).

    Sessler A. M., Cornwall J. M., et al. (2000). *Countermeasures*,
    UCS / MIT (BC-differential discrimination physics + Table 8.1).
    """
    if bc_heavy_kg_m2 <= 0.0 or bc_light_kg_m2 <= 0.0:
        return {"ok": False, "error": "Ballistic coefficients must be positive."}
    if bc_heavy_kg_m2 <= bc_light_kg_m2:
        return {
            "ok": False,
            "error": (
                f"bc_heavy ({bc_heavy_kg_m2}) must exceed bc_light "
                f"({bc_light_kg_m2}); BC-differential physics relies "
                "on the heavier object decelerating more slowly."
            ),
        }
    if not (0.0 < entry_flight_path_angle_deg < 90.0):
        return {
            "ok": False,
            "error": (
                "entry_flight_path_angle_deg must be in (0, 90); got "
                f"{entry_flight_path_angle_deg}"
            ),
        }
    if altitude_band_upper_km <= altitude_band_lower_km:
        return {
            "ok": False,
            "error": (
                f"altitude_band_upper_km ({altitude_band_upper_km}) "
                f"must exceed altitude_band_lower_km "
                f"({altitude_band_lower_km})"
            ),
        }
    if n_samples < 2:
        return {"ok": False, "error": "n_samples must be >= 2."}

    gamma_e = math.radians(entry_flight_path_angle_deg)

    samples: List[Dict[str, float]] = []
    peak_dv = 0.0
    h_at_peak_dv = altitude_band_upper_km * 1000.0

    for i in range(n_samples):
        # Sweep from upper (re-entry interface) DOWN to lower
        frac = i / (n_samples - 1)
        h_km = altitude_band_upper_km - frac * (
            altitude_band_upper_km - altitude_band_lower_km
        )
        h_m = h_km * 1000.0
        v_heavy = _allen_eggers_velocity(
            entry_velocity_m_s, gamma_e, bc_heavy_kg_m2, h_m,
        )
        v_light = _allen_eggers_velocity(
            entry_velocity_m_s, gamma_e, bc_light_kg_m2, h_m,
        )
        dv = v_heavy - v_light
        samples.append({
            "altitude_m": h_m,
            "altitude_km": h_km,
            "v_heavy_m_s": v_heavy,
            "v_light_m_s": v_light,
            "delta_v_m_s": dv,
            "delta_v_fraction": dv / entry_velocity_m_s,
        })
        if dv > peak_dv:
            peak_dv = dv
            h_at_peak_dv = h_m

    return {
        "ok": True,
        "bc_heavy_kg_m2": bc_heavy_kg_m2,
        "bc_light_kg_m2": bc_light_kg_m2,
        "bc_ratio": bc_heavy_kg_m2 / bc_light_kg_m2,
        "entry_velocity_m_s": entry_velocity_m_s,
        "entry_flight_path_angle_deg": entry_flight_path_angle_deg,
        "altitude_band_lower_km": altitude_band_lower_km,
        "altitude_band_upper_km": altitude_band_upper_km,
        "peak_delta_v_m_s": peak_dv,
        "altitude_at_peak_delta_v_m": h_at_peak_dv,
        "altitude_at_peak_delta_v_km": h_at_peak_dv / 1000.0,
        "n_samples": len(samples),
        "samples": samples,
    }


def compute_discrimination_altitude(
    bc_heavy_kg_m2: float,
    bc_light_kg_m2: float,
    entry_velocity_m_s: float = 7000.0,
    entry_flight_path_angle_deg: float = 23.0,
    delta_v_threshold_m_s: float = 100.0,
    altitude_band_lower_km: float = DEFAULT_DISCRIMINATION_BAND_LOWER_KM,
    altitude_band_upper_km: float = DEFAULT_DISCRIMINATION_BAND_UPPER_KM,
) -> Dict[str, Any]:
    """Find the altitude at which |Δv| first exceeds a threshold.

    Sweeps the altitude band from upper (re-entry interface) DOWN to
    lower. Returns the **first** altitude (highest, closest to
    re-entry interface) at which the velocity gap exceeds the
    threshold — that's the **discrimination altitude**, the highest
    altitude at which a BC-differential measurement could
    distinguish the two objects.

    Parameters
    ----------
    bc_heavy_kg_m2, bc_light_kg_m2 : float
        Ballistic coefficients (kg/m²). Heavy must exceed light.
    entry_velocity_m_s : float, default 7000
        Velocity at re-entry interface (m/s).
    entry_flight_path_angle_deg : float, default 23
        Re-entry flight-path angle (degrees).
    delta_v_threshold_m_s : float, default 100
        Δv threshold for declaring "discriminable" (m/s). 100 m/s is
        a textbook reference; **not an operational threshold**.
    altitude_band_lower_km, altitude_band_upper_km : float
        Search band (km).

    Returns
    -------
    dict
        ``{ok, discrimination_altitude_m, delta_v_at_threshold_m_s,
        threshold_crossed, ...}``. ``threshold_crossed=False`` means
        the BC pair never separates by the threshold within the band
        — discrimination is impossible at these altitudes.
    """
    if delta_v_threshold_m_s <= 0.0:
        return {"ok": False, "error": "delta_v_threshold_m_s must be positive."}

    diff = compute_bc_differential(
        bc_heavy_kg_m2=bc_heavy_kg_m2,
        bc_light_kg_m2=bc_light_kg_m2,
        entry_velocity_m_s=entry_velocity_m_s,
        entry_flight_path_angle_deg=entry_flight_path_angle_deg,
        altitude_band_lower_km=altitude_band_lower_km,
        altitude_band_upper_km=altitude_band_upper_km,
        n_samples=201,
    )
    if not diff["ok"]:
        return diff

    threshold_crossed = False
    discrimination_altitude_m = None
    delta_v_at_threshold = 0.0
    for s in diff["samples"]:
        if s["delta_v_m_s"] >= delta_v_threshold_m_s:
            threshold_crossed = True
            discrimination_altitude_m = s["altitude_m"]
            delta_v_at_threshold = s["delta_v_m_s"]
            break

    return {
        "ok": True,
        "bc_heavy_kg_m2": bc_heavy_kg_m2,
        "bc_light_kg_m2": bc_light_kg_m2,
        "delta_v_threshold_m_s": delta_v_threshold_m_s,
        "threshold_crossed": threshold_crossed,
        "discrimination_altitude_m": discrimination_altitude_m,
        "discrimination_altitude_km": (
            discrimination_altitude_m / 1000.0
            if discrimination_altitude_m is not None
            else None
        ),
        "delta_v_at_threshold_m_s": delta_v_at_threshold,
        "peak_delta_v_m_s": diff["peak_delta_v_m_s"],
        "altitude_band_lower_km": altitude_band_lower_km,
        "altitude_band_upper_km": altitude_band_upper_km,
    }


def get_bc_reference_class(
    class_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Open-literature reference BC class lookup.

    Returns canonical class baselines (heavy_rv / light_rv /
    replica_decoy / chaff_decoy) from Sessler/UCS 2000 Table 8.1.
    **Not specific weapon-system parameters.**
    """
    if class_name is not None:
        name = str(class_name).lower().strip()
        if name not in _BY_CLASS:
            return {
                "ok": False,
                "error": (
                    f"unknown class {class_name!r}; known classes "
                    f"are {_ALL_CLASSES}"
                ),
            }
        return {
            "ok": True,
            "class_name": name,
            "bc_class": _class_to_dict(_BY_CLASS[name]),
        }

    return {
        "ok": True,
        "n_classes": len(_ALL_CLASSES),
        "classes": {
            name: _class_to_dict(_BY_CLASS[name]) for name in _ALL_CLASSES
        },
    }


def list_bc_reference_classes() -> Dict[str, Any]:
    """Full enumeration of BC reference classes + citations."""
    return {
        "ok": True,
        "n_classes": len(_ALL_CLASSES),
        "n_sources": len(SOURCES),
        "classes": [_class_to_dict(c) for c in BC_REFERENCE_CLASSES],
    }


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "BC_REFERENCE_CLASSES",
    "SOURCES",
    "BCReferenceClass",
    "compute_bc_differential",
    "compute_discrimination_altitude",
    "get_bc_reference_class",
    "list_bc_reference_classes",
]
