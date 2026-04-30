"""chess_spectral_4d.engine -- 4D position evaluation, search, tournament.

Phase 6 (v1.6) engine surface for the 4D spectral encoder. Mirrors
:mod:`chess_spectral.engine` (2D) at every level.

Submodules:
  * ``eval.material`` -- baseline piece-value sum (PR-2; in main)
  * ``eval.spectral`` -- per-channel L2 energy weighted sum (PR-3; in main)
  * ``eval.qm``       -- Born-rule expectation values (PR-4; in main)
  * ``search``        -- bitboard-driven 4D search core (PR-7-I; in main soon)

The 4D analogue of :mod:`chess_spectral.engine.tournament` will
be added in a follow-up PR. Each evaluator submodule exports an
``evaluate(position, side_to_move) -> float`` matching the 2D
contract.
"""
from __future__ import annotations

from .eval import material  # noqa: F401

# search may not yet be merged when this package is imported
# from a stacked branch; tolerate ImportError until PR-7-I lands.
try:
    from . import search  # noqa: F401
except ImportError:
    search = None  # type: ignore

__all__ = [name for name, val in (
    ("material", material), ("search", search),
) if val is not None]
