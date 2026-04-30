"""chess_spectral.engine -- 2D position evaluation, search, tournament.

Phase 6 (v1.6) engine surface for the 640-dim spectral encoder. Mirrors
:mod:`chess_spectral_4d.engine` (4D) in shape.

  * **material** -- sum of signed piece values (centipawns). Baseline.
    No encoder call.
  * **spectral** -- per-channel L2 energy weighted sum (10 channels x
    64 modes). Encodes via :func:`chess_spectral.encode_640`.
  * **qm** -- Born-rule expectation values of Hermitian observables
    on the QM lift psi in C^640. Uses :mod:`chess_spectral.qm_2d`.

The :mod:`chess_spectral.engine.search` package is the search core
(negamax + alpha-beta + iterative deepening + transposition tables +
move ordering + quiescence). :mod:`chess_spectral.engine.tournament`
(PR-7) consumes both. The 4D analogue lives in
:mod:`chess_spectral_4d.engine` with the same module layout and
identical surface.

Convention -- ``evaluate(position, side_to_move) -> float``
  Returns a real-valued score from the side-to-move's perspective.
  Positive == side_to_move is winning. Negative == losing.
  Zero == drawn (or the evaluator has no signal).

The tournament harness composes search + evaluator into Agent
configurations and runs round-robin matches to empirically validate
the spectral / QM framework's chess-relevance per §16.5 and the
§2787 ship gate (per-depth Elo sweep across 3+ depths × 3
evaluators × 2 dimensions).
"""
from __future__ import annotations

from .eval import material, spectral, qm  # noqa: F401
from . import search  # noqa: F401

__all__ = ["material", "spectral", "qm", "search"]
