"""chess_spectral_4d.engine.eval -- 4D evaluator family.

Public surface is ``material``, ``spectral``, ``qm`` (PR-4).
Each module exports an ``evaluate(position, side_to_move) -> float``
matching the 2D contract in :mod:`chess_spectral.engine.eval`.
"""
from __future__ import annotations

from . import material  # noqa: F401
from . import spectral  # noqa: F401

__all__ = ["material", "spectral"]
