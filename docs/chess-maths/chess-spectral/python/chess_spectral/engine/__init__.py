"""chess_spectral.engine -- 2D position evaluation, search, tournament.

Phase 6 (v1.6) engine surface for the 640-dim spectral encoder. Three
evaluator families share the API ``evaluate(position, side_to_move) ->
float``:

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

  ``position``: dict matching the encoder's input schema (sq_index ->
    piece char for 2D; sq4_index -> PieceValue for 4D). Do not pass a
    GameState wrapper -- use the wrapper's ``position`` accessor first.
  ``side_to_move``: True == white to move; False == black to move.
    Engine search loops alternate this on every ply.

Stability contract -- each evaluator's score is a deterministic function
of (position, side_to_move). No RNG; no system clock; no I/O.
"""
from __future__ import annotations

from .eval import material, spectral, qm  # noqa: F401
from . import search  # noqa: F401

__all__ = ["material", "spectral", "qm", "search"]
