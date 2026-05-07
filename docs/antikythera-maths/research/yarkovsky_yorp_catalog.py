"""Sol Yarkovsky/YORP Catalog — query surface for the v0.24.6 ship
(per-asteroid thermal-radiation orbital + spin-state drift).

Promotes the v0.24.6 architectural commitment from research notebook
§17.7 to a stable ship surface — the **seventh and final ship in
the v0.24.x backlog**.

Three bridge surfaces:

* :func:`get_yarkovsky_yorp` — per-asteroid query.
* :func:`get_yorp_attractor_thresholds` — physical-regime
  threshold constants (rotational-fission limit, observability
  threshold, YORP obliquity attractors).
* :func:`list_yarkovsky_yorp` — full catalog enumeration.

Reference: research notebook §17.7.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .yarkovsky_yorp_data import (
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    ROTATIONAL_FISSION_PERIOD_HOURS,
    SOURCES,
    YARKOVSKY_OBSERVABILITY_DIAMETER_KM,
    YARKOVSKY_YORP_ENTRIES,
    YORP_OBLIQUITY_ATTRACTOR_HI_DEG,
    YORP_OBLIQUITY_ATTRACTOR_LO_DEG,
    YarkovskyYorpEntry,
)


_BY_SHORT: Dict[str, YarkovskyYorpEntry] = {
    e.short_name: e for e in YARKOVSKY_YORP_ENTRIES
}
_ALL_SHORT_NAMES: List[str] = sorted(_BY_SHORT.keys())


def _to_dict(e: YarkovskyYorpEntry) -> Dict[str, Any]:
    return {
        "designation": e.designation,
        "short_name": e.short_name,
        "semi_major_axis_au": e.semi_major_axis_au,
        "eccentricity": e.eccentricity,
        "diameter_km": e.diameter_km,
        "rotation_period_hours": e.rotation_period_hours,
        "yarkovsky_drift_1e4_au_per_myr":
            e.yarkovsky_drift_1e4_au_per_myr,
        "yarkovsky_uncertainty_1e4_au_per_myr":
            e.yarkovsky_uncertainty_1e4_au_per_myr,
        "yorp_spin_rate_change_1e8_rad_per_day_sq":
            e.yorp_spin_rate_change_1e8_rad_per_day_sq,
        "yorp_uncertainty_1e8_rad_per_day_sq":
            e.yorp_uncertainty_1e8_rad_per_day_sq,
        "is_prograde": e.is_prograde,
        "notes": e.notes,
        "source_key": e.source_key,
        "precision_flag": e.precision_flag,
    }


def get_yarkovsky_yorp(body: Optional[str] = None) -> Dict[str, Any]:
    """Per-asteroid Yarkovsky semi-major-axis drift + YORP
    spin-state evolution.

    Each entry stores measured **da/dt** (Yarkovsky semi-major-
    axis drift in 10⁻⁴ AU/Myr) and/or **dω/dt** (YORP spin-rate
    change in 10⁻⁸ rad/d²) when published. Both effects scale as
    1/D² so small bodies dominate the catalog.

    Headlines:
      * **(101955) Bennu** — OSIRIS-REx headline; -19×10⁻⁴ AU/Myr
        (~285 m/yr inward drift); first directly-imaged Yarkovsky-
        drifting asteroid.
      * **(54509) 2000 PH5 (YORP)** — first YORP detection (Lowry
        2007); 12-minute rotation period (near fission limit).
        Lent its name to the effect.
      * **(99942) Apophis** — Yarkovsky uncertainty matters for
        2068 close-approach impact-prediction.
      * **Prograde rotators drift outward; retrograde drift inward**
        — the diurnal-Yarkovsky direction signature.

    Cross-channel observation: where v0.23.0 catalogs **spin-orbit
    LOCKED** bodies (Mercury 3:2; Luna 1:1; Galileans), v0.24.6
    catalogs **spin-FREE** bodies driven *by sunlight* — the
    radiation-coupled analogue of v0.24.2 Mars's gravitation-coupled
    obliquity chaos.

    Parameters
    ----------
    body : str, optional. Single-asteroid lookup; else full roster.

    Returns
    -------
    dict
        Single body: ``{ok, body, entry: {...}}``.
        Full roster: ``{ok, n_asteroids, entries: {name: {...}}}``.
    """
    if body is not None:
        name = str(body).lower().strip()
        if name not in _BY_SHORT:
            return {
                "ok": False,
                "error": (
                    f"unknown asteroid {body!r} in Yarkovsky/YORP "
                    f"catalog; known names are {_ALL_SHORT_NAMES}"
                ),
            }
        return {
            "ok": True,
            "body": name,
            "entry": _to_dict(_BY_SHORT[name]),
        }

    return {
        "ok": True,
        "n_asteroids": len(_ALL_SHORT_NAMES),
        "entries": {
            name: _to_dict(_BY_SHORT[name]) for name in _ALL_SHORT_NAMES
        },
    }


def get_yorp_attractor_thresholds() -> Dict[str, Any]:
    """Physical-regime threshold constants for the Yarkovsky/YORP
    sequence.

    * **Rotational-fission limit** ~ 2.2 hours: rubble-pile
      asteroids at this rotation rate cannot be held together by
      cohesion alone; YORP-spin-up beyond this limit produces
      rotational fission (creating binary asteroids). The
      observed spin-rate-vs-size distribution clusters at this
      limit for D < ~10 km bodies, direct evidence of YORP-
      driven evolution.
    * **Observability diameter** ~ 30 km: Yarkovsky/YORP scale
      as 1/D², so for bodies larger than ~30 km the effect is
      below current observational sensitivity.
    * **YORP obliquity attractors** at ~55° and ~125°
      (Vokrouhlický-Čapek 2002): irregular asteroids' spin axes
      are driven toward these attractor states by the YORP torque.

    Returns
    -------
    dict
        ``{ok, rotational_fission_period_hours, observability_diameter_km,
        yorp_obliquity_attractor_lo_deg, yorp_obliquity_attractor_hi_deg}``.
    """
    return {
        "ok": True,
        "rotational_fission_period_hours": ROTATIONAL_FISSION_PERIOD_HOURS,
        "observability_diameter_km": YARKOVSKY_OBSERVABILITY_DIAMETER_KM,
        "yorp_obliquity_attractor_lo_deg": YORP_OBLIQUITY_ATTRACTOR_LO_DEG,
        "yorp_obliquity_attractor_hi_deg": YORP_OBLIQUITY_ATTRACTOR_HI_DEG,
        "interpretation": (
            "Three thresholds bound the small-body Yarkovsky/YORP "
            "regime: (1) rotational-fission at 2.2 h sets the spin-up "
            "limit; (2) ~30 km observability cap reflects the 1/D² "
            "scaling; (3) obliquity attractors at 55° and 125° "
            "are the long-term spin-axis end-states for irregular "
            "bodies."
        ),
    }


def list_yarkovsky_yorp() -> Dict[str, Any]:
    """Full catalog enumeration of every measured Yarkovsky/YORP
    record + citations."""
    return {
        "ok": True,
        "n_asteroids": len(_ALL_SHORT_NAMES),
        "n_sources": len(SOURCES),
        "entries": [_to_dict(e) for e in YARKOVSKY_YORP_ENTRIES],
    }


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "YARKOVSKY_YORP_ENTRIES",
    "SOURCES",
    "YarkovskyYorpEntry",
    "get_yarkovsky_yorp",
    "get_yorp_attractor_thresholds",
    "list_yarkovsky_yorp",
]
