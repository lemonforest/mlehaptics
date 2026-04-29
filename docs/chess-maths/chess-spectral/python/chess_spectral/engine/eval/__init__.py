"""chess_spectral.engine.eval -- the three evaluator families for 2D.

Public surface is ``material``, ``spectral`` (PR-3), ``qm`` (PR-4).
Each module exports an ``evaluate(position, side_to_move) -> float``
plus its own type-specific configuration knobs (e.g.,
``--eval-weights`` JSON for spectral / qm).
"""
from __future__ import annotations

from . import material  # noqa: F401

__all__ = ["material"]
