"""Sol Tidal Migration Catalog — query surface for the v0.21.6
cross-channel coupling ship (tidal dissipation ↔ orbital migration).

Promotes the v0.21.6 architectural commitment from research notebook
§17.4.2 to a stable ship surface — the **sixth cross-channel coupling
surface**, third in the post-trio sequence (after v0.21.4 interior↔
rotation and v0.21.5 magnetic↔atmosphere via aurorae).

**Not a re-derivation.** Migration rates stored here are the published
secular drift fits from cited papers; this catalog is the navigation
layer.

Two bridge surfaces:

* :func:`compute_tidal_migration` — per-pair query (use canonical
  "parent-satellite" pair string).
* :func:`list_tidal_migrations` — full catalog enumeration.

Reference: research notebook §17.4.2.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .tidal_migration_data import (
    DIR_INWARD,
    DIR_LOCKED,
    DIR_OUTWARD,
    PRECISION_HIGH,
    PRECISION_LOW,
    PRECISION_MEDIUM,
    PRECISION_NONE,
    SOURCES,
    TIDAL_MIGRATIONS,
    TidalMigration,
)


# ---- Memoised lookups (built at module load) -------------------------

_BY_PAIR: Dict[str, TidalMigration] = {m.pair_name: m for m in TIDAL_MIGRATIONS}
_ALL_PAIRS: List[str] = sorted(_BY_PAIR.keys())


def _to_dict(m: TidalMigration) -> Dict[str, Any]:
    return {
        "pair_name": m.pair_name,
        "parent_body": m.parent_body,
        "satellite_body": m.satellite_body,
        "migration_rate_cm_per_year": m.migration_rate_cm_per_year,
        "migration_direction": m.migration_direction,
        "is_resonance_locked": m.is_resonance_locked,
        "additional_constraint": m.additional_constraint,
        "precision_flag": m.precision_flag,
        "notes": m.notes,
        "source_key": m.source_key,
    }


def compute_tidal_migration(pair: Optional[str] = None) -> Dict[str, Any]:
    """Per-pair tidal-dissipation ↔ orbital-migration constraint.

    A satellite's tidal interaction with its parent body dissipates
    mechanical energy and transfers angular momentum; the secular
    semi-major-axis drift is the observable signature. Direction
    follows from the spin-orbit relation:

    * Satellite faster than parent's rotation → inward migration
      (Phobos-Mars, Triton-Neptune retrograde).
    * Satellite slower than parent's rotation → outward migration
      (Moon-Earth, Galileans, Titan-Saturn).
    * Satellite tidally locked to parent → no migration
      (Charon-Pluto dual-synchronous; unique solar-system case).

    Resonance amplifies migration (Galilean Laplace 1:2:4).

    **Not a re-derivation.** Values shipped are the published secular
    drift fits from cited papers.

    6-pair roster: terra-luna, mars-phobos, jupiter-io, saturn-titan,
    neptune-triton, pluto-charon.

    Parameters
    ----------
    pair : str, optional. Canonical "parent-satellite" pair string;
        else full roster.

    Returns
    -------
    dict
        Single pair: ``{ok, pair, migration: {...}}``.
        Full roster: ``{ok, n_pairs, pairs: {pair_name: {...}}}``.
    """
    if pair is not None:
        name = str(pair).lower().strip()
        if name not in _BY_PAIR:
            return {
                "ok": False,
                "error": (
                    f"unknown pair {pair!r} in Sol Tidal Migration "
                    f"Catalog; known pairs are {_ALL_PAIRS}"
                ),
            }
        return {
            "ok": True,
            "pair": name,
            "migration": _to_dict(_BY_PAIR[name]),
        }

    pairs: Dict[str, Dict[str, Any]] = {
        name: _to_dict(_BY_PAIR[name]) for name in _ALL_PAIRS
    }
    return {
        "ok": True,
        "n_pairs": len(_ALL_PAIRS),
        "pairs": pairs,
    }


def list_tidal_migrations() -> Dict[str, Any]:
    """Full catalog enumeration of every published tidal-migration rate."""
    return {
        "ok": True,
        "n_pairs": len(_ALL_PAIRS),
        "n_sources": len(SOURCES),
        "pairs": list(_ALL_PAIRS),
        "migrations": [_to_dict(m) for m in TIDAL_MIGRATIONS],
    }


__all__ = [
    "PRECISION_HIGH",
    "PRECISION_MEDIUM",
    "PRECISION_LOW",
    "PRECISION_NONE",
    "DIR_OUTWARD",
    "DIR_INWARD",
    "DIR_LOCKED",
    "TIDAL_MIGRATIONS",
    "SOURCES",
    "TidalMigration",
    "compute_tidal_migration",
    "list_tidal_migrations",
]
