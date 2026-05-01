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

    ``best_move`` is None only when no legal moves were available
    (true checkmate / stalemate / game-over). When the search aborts
    via the ``time_budget_ms`` deadline mid-iteration, ``best_move``
    is the best move from whichever iteration produced one — possibly
    a partial iteration; callers should consult ``timed_out`` to
    distinguish "natural completion" from "stopped at deadline."
    """
    best_move: Optional[chess.Move]
    best_score: float
    depth_reached: int
    nodes_searched: int
    elapsed_ms: float
    pv: List[chess.Move] = field(default_factory=list)
    tt_hits: int = 0
    tt_size: int = 0
    # 1.6.2: True if the iterative-deepening loop aborted because the
    # ``time_budget_ms`` deadline elapsed mid-iteration. ``depth_reached``
    # is still the deepest FULLY-completed iteration; ``best_move`` may
    # come from a partial iteration deeper than that.
    timed_out: bool = False


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


def _deadline_passed(state: _SearchState) -> bool:
    """Cheap deadline check, called on every node entry.

    1.6.2: Replaces the previous ``state.nodes % 1024 == 0`` gate.
    ``time.monotonic()`` is ~100ns; per-node search cost is dominated
    by move-gen at dense positions (~120ms/move at 4D 28-king start),
    so checking every node adds <1% overhead and gives us responsive
    deadline enforcement instead of waiting up to 1024 nodes."""
    return (state.deadline_s is not None
            and time.monotonic() > state.deadline_s)


def _materialize_legal_moves(state: _SearchState,
                              board: chess.Board) -> List[chess.Move]:
    """Materialize ``board.legal_moves`` with a deadline check
    after each yielded move.

    Replaces ``list(board.legal_moves)`` so a tight ``time_budget_ms``
    can interrupt move generation. Always collects at least one move
    when the position has legal moves — the deadline check is skipped
    on the first yield so the root iteration has at least one
    candidate to score (per the 1.6.2 user spec: best_move is never
    None when legal moves exist).

    On abort returns the partial list (>=1 move); callers check
    ``state.aborted`` and treat it as a non-exhaustive sample."""
    moves: List[chess.Move] = []
    for move in board.legal_moves:
        if moves and _deadline_passed(state):
            state.aborted = True
            break
        moves.append(move)
    return moves


def _negamax(state: _SearchState,
             board: chess.Board,
             depth: int,
             alpha: float,
             beta: float,
             ply_from_root: int) -> float:
    """Negamax-with-alpha-beta. Returns score from side-to-move's POV."""
    state.nodes += 1

    # 1.6.2: every-node deadline check (was every-1024). See
    # ``_deadline_passed`` for the rationale.
    if _deadline_passed(state):
        state.aborted = True
        # Return a benign score; the iterative-deepening wrapper
        # picks up partial-iteration progress at the root.
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

    # 1.6.2: deadline-aware materialization. On abort partway,
    # ``moves`` is partial and ordering is skipped (it'd be bogus on
    # a non-exhaustive sample anyway).
    moves = _materialize_legal_moves(state, board)
    if state.aborted and not moves:
        return 0.0
    if state.options.use_mvv_lva and not state.aborted:
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

        # 1.6.2: deadline-aware root materialization, same pattern as
        # interior _negamax. Without this a tight budget at a high-
        # branching position can spend the entire budget inside
        # ``list(board.legal_moves)`` and never enter the score loop.
        moves = _materialize_legal_moves(state, board)
        if not state.aborted and options.use_mvv_lva:
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
            # Per-move deadline check at the root: critical for tight
            # budgets where one ``_negamax(depth-1)`` call can cost
            # seconds. Skipped on the first move so we always score
            # at least one (best_move non-None guarantee).
            if iter_best_move is not None and _deadline_passed(state):
                state.aborted = True
                break
            board.push(move)
            score = -_negamax(state, board, depth - 1, -beta, -alpha,
                              ply_from_root=1)
            board.pop()
            # Adopt the score even when state.aborted is set — _negamax's
            # 0.0 sentinel is fine as a fallback so partial-iteration
            # progress is preserved.
            if score > iter_best_score:
                iter_best_score = score
                iter_best_move = move
                if score > alpha:
                    alpha = score
            if state.aborted:
                break
            # No beta cutoff at root: we want to evaluate every move
            # at depth 1+ to identify the best one (root window is
            # always (-INF, INF)).

        if state.aborted:
            # 1.6.2: KEEP the partial-iteration best move when timing
            # out. Previously we discarded the partial result and used
            # the previous fully-completed iteration; that meant a
            # ``time_budget_ms=2000`` at a slow position returned
            # ``best_move=None``. Now we carry forward whatever the
            # partial iteration produced (if any).
            if iter_best_move is not None:
                best_move = iter_best_move
                best_score = iter_best_score
                # depth_reached stays at the previous fully-completed
                # iteration's depth — the partial-iteration result is
                # at depth `depth` but flagged via timed_out.
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
        timed_out=state.aborted,
    )
