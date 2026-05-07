"""Sol Spin-Orbit Resonance Catalog — query surface for the v0.23.0
ship (eleventh cross-channel coupling surface).

Promotes the v0.23.0 architectural commitment from research notebook
§17.4.2 to a stable ship surface — **eleventh cross-channel coupling
surface**, resumed after the v0.22.0 trajectory + sensing discipline
pivot.

Cross-channel reach: closes the tidal-physics triple with v0.21.4
(rotational constraints / tidal Q-factor) + v0.21.6 (tidal migration
secular drift). The end-state of long-term tidal evolution is the
spin-orbit resonance lock the body settles into; v0.21.4 measures
the *dissipation efficiency*, v0.21.6 measures the *secular drift*,
and v0.23.0 measures the *resulting equilibrium*.

**Not a re-derivation.** Rotation periods + orbital periods +
libration amplitudes are the published values from cited papers
(Margot 2007, Williams 2014, Lainey 2009, Iess 2012, McKinnon 2017,
etc.).

Three bridge surfaces:

* :func:`compute_spin_orbit_resonance` — per-body query.
* :func:`get_spin_orbit_resonance` — alias for per-body query.
* :func:`list_spin_orbit_resonances` — full catalog enumeration.

Reference: research notebook §17.4.2 + §17.6.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .spin_orbit_resonance_data import (
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
    SPIN_ORBIT_RESONANCES,
    SpinOrbitResonance,
)


# ---- Memoised lookups (built at module load) -------------------------

_BY_BODY: Dict[str, SpinOrbitResonance] = {
    s.body: s for s in SPIN_ORBIT_RESONANCES
}
_ALL_BODIES: List[str] = sorted(_BY_BODY.keys())


def _to_dict(s: SpinOrbitResonance) -> Dict[str, Any]:
    return {
        "body": s.body,
        "parent": s.parent,
        "p_numerator": s.p_numerator,
        "q_denominator": s.q_denominator,
        "ratio_label": f"{s.p_numerator}:{s.q_denominator}",
        "ratio_value": s.p_numerator / s.q_denominator,
        "rotation_period_days": s.rotation_period_days,
        "orbital_period_days": s.orbital_period_days,
        "libration_amplitude_arcsec": s.libration_amplitude_arcsec,
        "is_dual_synchronous": s.is_dual_synchronous,
        "precision_flag": s.precision_flag,
        "notes": s.notes,
        "source_key": s.source_key,
    }


def compute_spin_orbit_resonance(
    body: Optional[str] = None,
) -> Dict[str, Any]:
    """Per-body spin-orbit resonance state + libration amplitude.

    For each body in the catalog, returns the integer (p, q) ratio
    where ``p`` = rotations and ``q`` = orbits, plus the rotation +
    orbital periods (days) and libration amplitude (arcsec).

    The Solar-System headline: **Mercury is the only non-1:1 spin-orbit
    resonance** — locked at 3:2 (three rotations per two orbits) by
    high orbital eccentricity (e=0.206). Discovered by Pettengill &
    Dyce 1965 radar; explained by Colombo 1965 + Goldreich & Peale
    1966 as a stable equilibrium.

    All other catalog entries are **1:1 tidal locks** — Luna (Williams
    2014 LLR ~7.9 arcsec libration), Galileans (Lainey 2009/2020),
    Titan (Iess 2012 ~52 arcsec; anomalous magnitude attributed to
    icy outer shell decoupled by subsurface ocean), Triton (retrograde
    1:1), and Pluto-Charon (the unique **dual-synchronous** case where
    both bodies are tidally locked to each other).

    Cross-channel: this is the **end-state** of the tidal evolution
    that v0.21.4 (Q-factor) measures the dissipation rate of, and
    that v0.21.6 (orbital migration) measures the secular drift of.

    8-body roster.

    Parameters
    ----------
    body : str, optional. Single-body lookup; else full roster.

    Returns
    -------
    dict
        Single body: ``{ok, body, resonance: {...}}``.
        Full roster: ``{ok, n_bodies, bodies: {name: {...}}}``.
    """
    if body is not None:
        name = str(body).lower().strip()
        if name not in _BY_BODY:
            return {
                "ok": False,
                "error": (
                    f"unknown body {body!r} in Sol Spin-Orbit Resonance "
                    f"Catalog; known bodies are {_ALL_BODIES}"
                ),
            }
        return {
            "ok": True,
            "body": name,
            "resonance": _to_dict(_BY_BODY[name]),
        }

    bodies: Dict[str, Dict[str, Any]] = {
        name: _to_dict(_BY_BODY[name]) for name in _ALL_BODIES
    }
    return {
        "ok": True,
        "n_bodies": len(_ALL_BODIES),
        "bodies": bodies,
    }


def get_spin_orbit_resonance(body: Optional[str] = None) -> Dict[str, Any]:
    """Alias for :func:`compute_spin_orbit_resonance`."""
    return compute_spin_orbit_resonance(body=body)


def list_spin_orbit_resonances() -> Dict[str, Any]:
    """Full catalog enumeration of every published spin-orbit
    resonance record."""
    return {
        "ok": True,
        "n_bodies": len(_ALL_BODIES),
        "n_sources": len(SOURCES),
        "bodies": list(_ALL_BODIES),
        "resonances": [_to_dict(s) for s in SPIN_ORBIT_RESONANCES],
    }


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "SPIN_ORBIT_RESONANCES",
    "SOURCES",
    "SpinOrbitResonance",
    "compute_spin_orbit_resonance",
    "get_spin_orbit_resonance",
    "list_spin_orbit_resonances",
]
