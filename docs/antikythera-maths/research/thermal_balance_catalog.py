"""Sol Thermal Balance Catalog — query surface for the v0.21.10
cross-channel coupling ship (radiative equilibrium ↔ observed
temperature decomposition).

Promotes the v0.21.10 architectural commitment from research notebook
§17.4.2 to a stable ship surface — the **tenth cross-channel coupling
surface**, seventh in the post-trio sequence.

Cross-channel reach: connects v0.20.2 climatology (T_obs, Bond_albedo)
+ v0.21.8 heat flow + v0.21.9 outgassing into a unified energy-budget
picture. The decomposition T_obs - T_eq into greenhouse / tidal /
internal-heat contributions is independently verified by the heat-flow
budget.

**Not a re-derivation.** Decomposition values stored here are the
published thermal-balance breakdowns from cited papers.

Two bridge surfaces:

* :func:`compute_thermal_balance` — per-body query.
* :func:`list_thermal_balances` — full catalog enumeration.

Reference: research notebook §17.4.2.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .thermal_balance_data import (
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
    THERMAL_BALANCES,
    ThermalBalance,
)


# ---- Memoised lookups (built at module load) -------------------------

_BY_BODY: Dict[str, ThermalBalance] = {m.body: m for m in THERMAL_BALANCES}
_ALL_BODIES: List[str] = sorted(_BY_BODY.keys())


def _to_dict(m: ThermalBalance) -> Dict[str, Any]:
    return {
        "body": m.body,
        "equilibrium_temperature_K": m.equilibrium_temperature_K,
        "observed_temperature_K": m.observed_temperature_K,
        "greenhouse_offset_K": m.greenhouse_offset_K,
        "tidal_offset_K": m.tidal_offset_K,
        "internal_heat_offset_K": m.internal_heat_offset_K,
        "precision_flag": m.precision_flag,
        "notes": m.notes,
        "source_key": m.source_key,
    }


def compute_thermal_balance(body: Optional[str] = None) -> Dict[str, Any]:
    """Per-body radiative-equilibrium ↔ observed-temperature decomposition.

    The Stefan-Boltzmann radiative-equilibrium temperature is

        T_eq = ((1 - A) * S / (4 * σ))^(1/4)

    where S is the solar flux at the body and A the Bond albedo
    (v0.20.2 ``BodyClimatology``). The observed surface temperature
    (v0.20.2) typically differs from T_eq by greenhouse + tidal +
    internal-heat contributions.

    The cross-channel observation: **the v0.20.2 T_obs decomposition
    matches the v0.21.8 heat-flow energy budget**. For Earth, +33.5 K
    greenhouse + 47 TW geothermal flux is self-consistent. For
    Jupiter, +45 K internal-heat offset matches the planet radiating
    1.7× more heat than it absorbs from Sun.

    **Venus headline**: +505 K runaway-greenhouse offset — surface
    hotter than Mercury despite further from Sun.

    **Not a re-derivation.** Values shipped are published
    thermal-balance decompositions from cited papers.

    6-body roster.

    Parameters
    ----------
    body : str, optional. Single-body lookup; else full roster.

    Returns
    -------
    dict
        Single body: ``{ok, body, balance: {...}}``.
        Full roster: ``{ok, n_bodies, bodies: {name: {...}}}``.
    """
    if body is not None:
        name = str(body).lower().strip()
        if name not in _BY_BODY:
            return {
                "ok": False,
                "error": (
                    f"unknown body {body!r} in Sol Thermal Balance "
                    f"Catalog; known bodies are {_ALL_BODIES}"
                ),
            }
        return {
            "ok": True,
            "body": name,
            "balance": _to_dict(_BY_BODY[name]),
        }

    bodies: Dict[str, Dict[str, Any]] = {
        name: _to_dict(_BY_BODY[name]) for name in _ALL_BODIES
    }
    return {
        "ok": True,
        "n_bodies": len(_ALL_BODIES),
        "bodies": bodies,
    }


def list_thermal_balances() -> Dict[str, Any]:
    """Full catalog enumeration of every published thermal-balance
    decomposition."""
    return {
        "ok": True,
        "n_bodies": len(_ALL_BODIES),
        "n_sources": len(SOURCES),
        "bodies": list(_ALL_BODIES),
        "balances": [_to_dict(m) for m in THERMAL_BALANCES],
    }


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "THERMAL_BALANCES",
    "SOURCES",
    "ThermalBalance",
    "compute_thermal_balance",
    "list_thermal_balances",
]
