"""Search core: negamax + alpha-beta + iterative deepening.

Standard chess engine inner loop. Composes the TT, move ordering,
and quiescence search modules to produce a complete search.

Public entry point :func:`search` returns a :class:`SearchResult`
with the best move, score, depth reached, and node-count metrics.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

import chess

from ._board_adapter import board_to_position
from .ordering import order_moves
from .quiescence import quiescence
from .ttable import BoundType, TranspositionTable, TTEntry


# Sentinel scores. Use a large finite number rather than +/- inf so
# arithmetic operations (alpha-beta widening, score returning across
# negation) don't run into IEEE inf weirdness.
INF = 1.0e9
MATE_SCORE = 1.0e6   # leaves slack for mate-distance encoding


# ---- Search options + result containers ---------------------------


@dataclass
class SearchOptions:
    """Knobs for :func:`search`.

    Each ablation flag corresponds to one element of the §16.2 design
    so the §16 tournament can ablate them: ``--no-tt``, ``--no-mvv-lva``,
    ``--no-quiescence``.
    """
    max_depth: int = 4
    time_budget_ms: Optional[float] = None    # None == unbounded
    use_tt: bool = True
    use_mvv_lva: bool = True
    use_quiescence: bool = True
    quiescence_max_depth: int = 8

    def __post_init__(self) -> None:
        if self.max_depth < 1:
            raise ValueError(
                f"max_depth must be >= 1; got {self.max_depth}"
            )
        if (self.time_budget_ms is not None
                and self.time_budget_ms <= 0):
            raise ValueError(
                f"time_budget_ms must be > 0; got {self.time_budget_ms}"
            )


@dataclass
class SearchResult:
    """Outcome of a :func:`search` call.

    ``best_move`` is None only when ``board.is_game_over()`` was true
    on entry (no legal moves to recommend).
    """
    best_move: Optional[chess.Move]
    best_score: float
    depth_reached: int
    nodes_searched: int
    elapsed_ms: float
    pv: List[chess.Move] = field(default_factory=list)
    tt_hits: int = 0
    tt_size: int = 0


# ---- Negamax with alpha-beta --------------------------------------


@dataclass
class _SearchState:
    """Mutable per-search state passed to negamax. Avoids global vars."""
    evaluator: Callable[[Dict[int, str], bool], float]
    options: SearchOptions
    tt: Optional[TranspositionTable]
    deadline_s: Optional[float]
    nodes: int = 0
    aborted: bool = False


def _terminal_score(board: chess.Board, ply_from_root: int) -> float:
    """Score for a terminal node, from the side-to-move's perspective.

    Mate-distance correction: a faster mate is preferred, so we
    subtract ``ply_from_root`` from the mate score. Symmetric on
    both sides.
    """
    if board.is_checkmate():
        # Side to move just got mated -- catastrophic for us.
        return -(MATE_SCORE - ply_from_root)
    # Other game-over states (stalemate, threefold, 50-move,
    # insufficient) are draws.
    return 0.0


def _negamax(state: _SearchState,
             board: chess.Board,
             depth: int,
             alpha: float,
             beta: float,
             ply_from_root: int) -> float:
    """Negamax-with-alpha-beta. Returns score from side-to-move's POV."""
    state.nodes += 1

    # Time-budget short-circuit. We check periodically (every 1k
    # nodes) to keep the overhead trivial.
    if (state.deadline_s is not None
            and state.nodes % 1024 == 0
            and time.monotonic() > state.deadline_s):
        state.aborted = True
        # Return a benign score; the iterative-deepening wrapper
        # discards aborted iterations.
        return 0.0

    # Terminal node check (checkmate / stalemate / draw rules).
    if board.is_game_over():
        return _terminal_score(board, ply_from_root)

    # TT lookup. If we've seen this position before at >= depth,
    # we can sometimes return immediately based on bound type.
    tt_move: Optional[chess.Move] = None
    if state.tt is not None:
        entry = state.tt.lookup(board)
        if entry is not None:
            tt_move = entry.best_move
            if entry.depth >= depth:
                if entry.bound_type == BoundType.EXACT:
                    return entry.score
                elif (entry.bound_type == BoundType.LOWER
                      and entry.score >= beta):
                    return entry.score
                elif (entry.bound_type == BoundType.UPPER
                      and entry.score <= alpha):
                    return entry.score

    # Leaf node: descend into quiescence (or static eval if disabled).
    if depth == 0:
        if state.options.use_quiescence:
            return quiescence(
                board, alpha, beta, state.evaluator,
                board_to_position,
                max_depth=state.options.quiescence_max_depth,
            )
        return state.evaluator(board_to_position(board), board.turn)

    # Generate and order moves.
    moves: List[chess.Move] = list(board.legal_moves)
    if state.options.use_mvv_lva:
        moves = order_moves(board, moves, tt_move=tt_move)

    best_score = -INF
    best_move: Optional[chess.Move] = None
    original_alpha = alpha

    for move in moves:
        board.push(move)
        score = -_negamax(state, board, depth - 1, -beta, -alpha,
                          ply_from_root + 1)
        board.pop()

        if state.aborted:
            # Discard this iteration's results upstream.
            return best_score

        if score > best_score:
            best_score = score
            best_move = move
            if score > alpha:
                alpha = score
        if alpha >= beta:
            # Beta cutoff: this position is too good for the side to
            # move; the opponent would never let us reach it.
            break

    # Categorize the bound for TT storage.
    if state.tt is not None and not state.aborted:
        if best_score <= original_alpha:
            bound = BoundType.UPPER
        elif best_score >= beta:
            bound = BoundType.LOWER
        else:
            bound = BoundType.EXACT
        state.tt.store(board, depth, best_score, best_move, bound)

    return best_score


# ---- Iterative deepening + root search ----------------------------


def _extract_pv(tt: Optional[TranspositionTable],
                board: chess.Board,
                max_pv: int) -> List[chess.Move]:
    """Walk the TT to extract a principal variation.

    Each step: look up the current board's TT entry, push its
    best_move, repeat. Stops on TT miss, terminal, or max_pv.
    """
    if tt is None:
        return []
    pv: List[chess.Move] = []
    pushes = 0
    while pushes < max_pv and not board.is_game_over():
        entry = tt.lookup(board)
        if entry is None or entry.best_move is None:
            break
        if entry.best_move not in board.legal_moves:
            # TT collision or stale entry; abort PV walk.
            break
        pv.append(entry.best_move)
        board.push(entry.best_move)
        pushes += 1
    # Restore board state.
    for _ in range(pushes):
        board.pop()
    return pv


def search(board: chess.Board,
           evaluator: Callable[[Dict[int, str], bool], float],
           options: Optional[SearchOptions] = None) -> SearchResult:
    """Iterative-deepening alpha-beta search.

    Parameters
    ----------
    board : chess.Board
        The position to analyze. Mutated in-place during the search
        (push/pop) but **restored to its original state on return**.
    evaluator : callable
        ``evaluator(position_dict, side_to_move) -> float``. Any of
        the three §16.1 evaluator families works -- see
        :mod:`chess_spectral.engine.eval.material`,
        :mod:`...spectral`, :mod:`...qm`.
    options : SearchOptions, optional
        Search knobs. Defaults: depth 4, all optimizations on.

    Returns
    -------
    SearchResult with:
      * best_move : the recommended move (or None on game-over)
      * best_score : score from board.turn's perspective
      * depth_reached : the deepest fully-completed iteration
      * nodes_searched : total internal/leaf node visits
      * elapsed_ms : wall-clock time
      * pv : principal variation (best_move sequence)
      * tt_hits / tt_size : TT statistics if use_tt
    """
    if options is None:
        options = SearchOptions()

    start = time.monotonic()
    deadline_s = (
        start + options.time_budget_ms / 1000.0
        if options.time_budget_ms is not None else None
    )

    tt = TranspositionTable() if options.use_tt else None
    state = _SearchState(evaluator=evaluator, options=options, tt=tt,
                         deadline_s=deadline_s)

    if board.is_game_over():
        # No legal moves; return immediately with no recommendation.
        elapsed_ms = (time.monotonic() - start) * 1000.0
        return SearchResult(
            best_move=None,
            best_score=_terminal_score(board, 0),
            depth_reached=0,
            nodes_searched=0,
            elapsed_ms=elapsed_ms,
        )

    best_move: Optional[chess.Move] = None
    best_score: float = -INF
    depth_reached = 0

    for depth in range(1, options.max_depth + 1):
        # Reset abort flag at the start of each iteration.
        state.aborted = False
        nodes_at_iter_start = state.nodes

        # Root search: iterate moves explicitly so we can track the
        # best move (interior _negamax doesn't expose this).
        moves = list(board.legal_moves)
        if options.use_mvv_lva:
            # Try the previous-iteration best move first if any.
            tt_move = None
            if tt is not None:
                entry = tt.lookup(board)
                if entry is not None:
                    tt_move = entry.best_move
            moves = order_moves(board, moves, tt_move=tt_move)

        iter_best_score = -INF
        iter_best_move: Optional[chess.Move] = None
        alpha, beta = -INF, INF

        for move in moves:
            board.push(move)
            score = -_negamax(state, board, depth - 1, -beta, -alpha,
                              ply_from_root=1)
            board.pop()
            if state.aborted:
                break
            if score > iter_best_score:
                iter_best_score = score
                iter_best_move = move
                if score > alpha:
                    alpha = score
            # No beta cutoff at root: we want to evaluate every move
            # at depth 1+ to identify the best one (root window is
            # always (-INF, INF)).

        if state.aborted:
            # Discard this iteration's partial results; keep what
            # the previous iteration produced.
            break

        # Iteration completed: commit results.
        best_move = iter_best_move
        best_score = iter_best_score
        depth_reached = depth

        # Store root entry in TT so subsequent iterations can use
        # the previous best_move for ordering.
        if tt is not None and best_move is not None:
            tt.store(board, depth, best_score, best_move,
                     BoundType.EXACT)

        # If we found a forced mate, no need to search deeper.
        if abs(best_score) >= MATE_SCORE - 100:
            break

    elapsed_ms = (time.monotonic() - start) * 1000.0

    pv = _extract_pv(tt, board, max_pv=depth_reached) if tt else []

    return SearchResult(
        best_move=best_move,
        best_score=best_score,
        depth_reached=depth_reached,
        nodes_searched=state.nodes,
        elapsed_ms=elapsed_ms,
        pv=pv,
        tt_hits=tt.hits if tt is not None else 0,
        tt_size=len(tt) if tt is not None else 0,
    )
