"""chess_spectral_4d.engine -- 4D position evaluation, search, tournament.

Phase 6 (v1.6) engine surface for the 45 056-dim spectral encoder.
Same shape as :mod:`chess_spectral.engine` (2D); see that module's
docstring for the cross-cutting design (evaluator API contract,
side-to-move flipping convention, deterministic-output contract).

The 4D position schema differs from 2D in one specific way: pawn
values are axis-typed tuples, e.g., ``('P', 'w')`` for a W-axis white
pawn. The material evaluator strips the axis info -- material count
is the same regardless of pawn axis -- so the spectral / QM
evaluators (PR-3 / PR-4) are the only ones that consume axis
information.
"""
from __future__ import annotations

from .eval import material  # noqa: F401

__all__ = ["material"]
