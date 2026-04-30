"""Gear-database accessor facade.

The Antikythera mechanism's surviving + reconstructed gears, with
tooth counts under three reconstructions (Freeth 2021, Wright,
Price 1974), fragment provenance, and the mesh DAG.

Re-exported from ``_research.gear_database``.
"""

from __future__ import annotations

from antikythera_spectral._research.gear_database import (
    ALL_GEARS,
    FREETH_2021,
    Gear,
    LUNAR_TRAIN,
    MAIN_TRAIN,
    MESH_EDGES,
    PLANETARY,
    PRICE_1974,
    WRIGHT,
)

# Keep a frozen tuple of supported reconstruction names so callers can
# validate user-supplied strings.
RECONSTRUCTIONS: tuple[str, ...] = (FREETH_2021, WRIGHT, PRICE_1974)
"""Tuple of valid reconstruction names. Use to validate caller input."""

__all__ = [
    # Gear data
    "ALL_GEARS",
    "Gear",
    "MAIN_TRAIN",
    "LUNAR_TRAIN",
    "PLANETARY",
    "MESH_EDGES",
    # Reconstruction names
    "FREETH_2021",
    "WRIGHT",
    "PRICE_1974",
    "RECONSTRUCTIONS",
]
