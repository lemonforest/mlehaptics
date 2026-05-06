"""Sol Electromagnetic Instrument — state-at-epoch query surface for the
solar-system electromagnetic sector.

Promotes the v0.19.0 architectural commitment from research notebook
§16.9 to a stable ship surface. **This is not a BIP encoder running on
EM rhythms** — the §16.3 / §16.9.1 rhythm-mismatch finding established
that magnetic / synchrotron / Carrington / solar-cycle clocks do not
form a low-order rational lattice with each other or with orbital
periods, so the cyclic-group encoder discipline doesn't transplant.

Instead this module is a **state-at-epoch query surface**:

* :data:`SOL_EM_BODIES` — the 16-body roster of bodies with significant
  EM observables (intrinsic dipole, induced response, plasma source, or
  significant photoelectric charging). Strict subset of the v0.16.0
  52-body celestial roster.
* :data:`EM_COUPLINGS` — the static catalog of significant pairwise EM
  interactions (Jupiter–Io flux tube, Saturn–Enceladus mass loading,
  Saturn–Titan induced magnetosphere, Sun–Earth IMF reconnection, etc.).
* :func:`compute_em_state_at_jd` — advances per-body rotation phases
  from the v0.19.0 EM_REFERENCE_JD (J2000.0) and returns the full
  per-body state at the requested JD.
* :func:`compute_em_architecture` — partitions the roster into the
  three EM classes (`magnetised` / `induced` / `unmagnetised`) +
  `star`. Different partition than the v0.18.0 inner/outer split from
  :mod:`body_architecture`, since the relevant axis is intrinsic-field
  presence rather than orbital position.

The data tables are in :mod:`em_instrument_data`. Citations live in
its `SOURCES` dict; every numeric value carries a `source_key`
pointing into that dict so users can verify the provenance.

Reference: research notebook §16 (the architectural scoping) +
§16.10 (the EM-sector citations).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from .em_instrument_data import (
    EM_CLASS_INDUCED,
    EM_CLASS_MAGNETISED,
    EM_CLASS_STAR,
    EM_CLASS_UNMAGNETISED,
    EM_COUPLINGS,
    EM_REFERENCE_JD,
    SOL_EM_BODIES,
    SOURCES,
    EmBodyState,
    EmCoupling,
)


# ---- Memoised lookups (built at module load — μs on a 16-entry list) -

_BODY_BY_NAME: Dict[str, EmBodyState] = {b.name: b for b in SOL_EM_BODIES}


def _rotation_phase_at_jd(body: EmBodyState, jd_tdb: float) -> float:
    """Fractional rotation phase ∈ [0, 1) advanced from EM_REFERENCE_JD.

    Linear advance: phase = ((jd_tdb - REF) / period) mod 1.0. The
    encoder anchor is the IAU prime-meridian convention at J2000.0
    (consistent with body-rotation-phase usage elsewhere in the
    package). The linear-phase approximation neglects rotation-period
    drift over the integration horizon — for the magnetised bodies
    in the EM roster the drift over a 200-yr DE441 horizon is
    negligible (parts per 10⁶), well below the order-of-magnitude
    precision the EM data tables themselves carry.
    """
    if body.rotation_period_days <= 0.0:
        return 0.0
    delta_days = jd_tdb - EM_REFERENCE_JD
    cycles = delta_days / body.rotation_period_days
    # Pythonic modulo handles negative jd_tdb correctly.
    return cycles % 1.0


def compute_em_state_at_jd(jd_tdb: float) -> Dict[str, Any]:
    """Compute the full per-body EM state at the requested JD.

    Returns a Pyodide-compatible dict (no numpy / no custom classes
    on the output edge) with shape:

        {
            "ok": True,
            "jd_tdb": float,
            "n_bodies": int,
            "reference_jd": float,
            "bodies": [
                {
                    "name": str,
                    "em_class": str,
                    "rotation_phase": float,             # ∈ [0, 1)
                    "rotation_period_days": float,
                    "rotation_period_uncertainty_pct": float,
                    "intrinsic_dipole_moment_T_m3": Optional[float],
                    "synchrotron_power_W": Optional[float],
                    "plasma_source_rate_kg_per_s": Optional[float],
                    "photoelectric_potential_V": Optional[float],
                    "source_key": str,
                },
                ...
            ],
        }

    Parameters
    ----------
    jd_tdb : float
        Julian Date in TDB. Any finite real number.

    Notes
    -----
    The IMF / solar-wind state is *not* included in this state-at-epoch
    response. Per notebook §16.9.1 the IMF varies on Carrington (27.3 d)
    + stochastic CME timescales and is deferred to a separate
    (currently unimplemented) `bridge.get_imf_state(jd_tdb)` query that
    would pull from an OMNI cache. v0.19.0 ships the per-body
    static-plus-rotation-phase observables only.
    """
    if not isinstance(jd_tdb, (int, float)) or not math.isfinite(jd_tdb):
        return {
            "ok": False,
            "error": f"jd_tdb must be a finite real number, got {jd_tdb!r}",
        }

    body_records: List[Dict[str, Any]] = []
    for body in SOL_EM_BODIES:
        body_records.append({
            "name": body.name,
            "em_class": body.em_class,
            "rotation_phase": _rotation_phase_at_jd(body, float(jd_tdb)),
            "rotation_period_days": body.rotation_period_days,
            "rotation_period_uncertainty_pct": body.rotation_period_uncertainty_pct,
            "intrinsic_dipole_moment_T_m3": body.intrinsic_dipole_moment_T_m3,
            "synchrotron_power_W": body.synchrotron_power_W,
            "plasma_source_rate_kg_per_s": body.plasma_source_rate_kg_per_s,
            "photoelectric_potential_V": body.photoelectric_potential_V,
            "source_key": body.source_key,
        })

    return {
        "ok": True,
        "jd_tdb": float(jd_tdb),
        "n_bodies": len(SOL_EM_BODIES),
        "reference_jd": EM_REFERENCE_JD,
        "bodies": body_records,
    }


def list_em_couplings() -> Dict[str, Any]:
    """Return the static catalog of significant pairwise EM couplings."""
    return {
        "ok": True,
        "n_couplings": len(EM_COUPLINGS),
        "couplings": [
            {
                "body_a": c.body_a,
                "body_b": c.body_b,
                "kind": c.kind,
                "power_W": c.power_W,
                "dominant_timescale": c.dominant_timescale,
                "note": c.note,
                "source_key": c.source_key,
            }
            for c in EM_COUPLINGS
        ],
    }


def compute_em_architecture(target: Optional[str] = None) -> Dict[str, Any]:
    """Classify the EM roster into magnetised / induced / unmagnetised.

    Parameters
    ----------
    target : str, optional
        Body name. If given, return just that body's record;
        else return the full partition.

    Returns
    -------
    dict
        Full partition (target=None):
            ``{"ok": True, "n_bodies": 16, "bodies": [...],
              "partitions": {"magnetised": [...], "induced": [...],
                             "unmagnetised": [...], "star": [...]}}``
        Single-body (target=name):
            ``{"ok": True, "name": str, "em_class": str, ...}``
        On error: ``{"ok": False, "error": str}``.
    """
    if target is not None:
        name = str(target).lower().strip()
        body = _BODY_BY_NAME.get(name)
        if body is None:
            return {
                "ok": False,
                "error": (
                    f"unknown body {target!r}; valid names in SOL_EM_BODIES "
                    f"are {[b.name for b in SOL_EM_BODIES]}"
                ),
            }
        return {
            "ok": True,
            "name": body.name,
            "em_class": body.em_class,
            "intrinsic_dipole_moment_T_m3": body.intrinsic_dipole_moment_T_m3,
            "rotation_period_days": body.rotation_period_days,
            "source_key": body.source_key,
        }

    # Full partition.
    body_records = [
        {
            "name": b.name,
            "em_class": b.em_class,
            "intrinsic_dipole_moment_T_m3": b.intrinsic_dipole_moment_T_m3,
            "rotation_period_days": b.rotation_period_days,
            "source_key": b.source_key,
        }
        for b in SOL_EM_BODIES
    ]

    partitions = {
        EM_CLASS_MAGNETISED: [b.name for b in SOL_EM_BODIES if b.em_class == EM_CLASS_MAGNETISED],
        EM_CLASS_INDUCED: [b.name for b in SOL_EM_BODIES if b.em_class == EM_CLASS_INDUCED],
        EM_CLASS_UNMAGNETISED: [b.name for b in SOL_EM_BODIES if b.em_class == EM_CLASS_UNMAGNETISED],
        EM_CLASS_STAR: [b.name for b in SOL_EM_BODIES if b.em_class == EM_CLASS_STAR],
    }

    return {
        "ok": True,
        "n_bodies": len(SOL_EM_BODIES),
        "bodies": body_records,
        "partitions": partitions,
    }


__all__ = [
    "EM_CLASS_MAGNETISED",
    "EM_CLASS_INDUCED",
    "EM_CLASS_UNMAGNETISED",
    "EM_CLASS_STAR",
    "EM_REFERENCE_JD",
    "SOL_EM_BODIES",
    "EM_COUPLINGS",
    "SOURCES",
    "EmBodyState",
    "EmCoupling",
    "compute_em_state_at_jd",
    "list_em_couplings",
    "compute_em_architecture",
]
