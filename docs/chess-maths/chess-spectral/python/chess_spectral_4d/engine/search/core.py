"""4D search core: negamax + alpha-beta + iterative deepening.

4D analogue of :mod:`chess_spectral.engine.search.core`. See the 2D
module for the full design rationale; this module mirrors it for
Board4D + Move4D.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from chess_spectral.spatial_4d import Board4D, Move4D
from .ordering import order_moves
from .quiescence import quiescence
from .ttable import BoundType, TranspositionTable4D, TTEntry


INF = 1.0e9
MATE_SCORE = 1.0e6


@dataclass
class SearchOptions:
    max_depth: int = 4
    time_budget_ms: Optional[float] = None
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
    best_move: Optional[Move4D]
    best_score: float
    depth_reached: int
    nodes_searched: int
    elapsed_ms: float
    pv: List[Move4D] = field(default_factory=list)
    tt_hits: int = 0
    tt_size: int = 0
    # 1.6.2: True if the search aborted because the
    # ``time_budget_ms`` deadline elapsed mid-iteration.
    # ``best_move`` is the best move found so far (possibly from a
    # partial iteration); ``depth_reached`` is the deepest FULLY-
    # completed iteration. ``best_move is None`` only when the
    # position has no legal moves.
    timed_out: bool = False


@dataclass
class _SearchState:
    evaluator: Callable[[Dict[int, object], bool], float]
    options: SearchOptions
    tt: Optional[TranspositionTable4D]
    deadline_s: Optional[float]
    nodes: int = 0
    aborted: bool = False


def _terminal_score(board: Board4D, ply_from_root: int) -> float:
    """Mate score from side-to-move's perspective. is_check
    determines whether it's mate (negative) or stalemate (0)."""
    if board.is_check():
        return -(MATE_SCORE - ply_from_root)
    return 0.0


def _is_terminal(board: Board4D) -> bool:
    """Check if the position is terminal (no legal moves)."""
    for _ in board.legal_moves():
        return False
    return True


def _deadline_passed(state: _SearchState) -> bool:
    """Cheap deadline check. ``time.monotonic()`` is ~100ns, dwarfed
    by the per-move-gen cost (~120ms at the 28-king starting position),
    so we can afford to check on every node entry rather than gating
    by ``state.nodes % 1024``. The 1024-gate added latency proportional
    to per-node cost, which at dense 4D positions made the deadline
    check effectively unreachable mid-iteration."""
    return (state.deadline_s is not None
            and time.monotonic() > state.deadline_s)


def _materialize_legal_moves(state: _SearchState,
                              board: Board4D) -> List[Move4D]:
    """Materialize ``board.legal_moves()`` with a deadline check
    after each yield.

    Replaces ``list(board.legal_moves())`` so a tight ``time_budget_ms``
    can interrupt move generation. At dense 28-king positions a full
    legal-move set takes ~250s; bailing partway gives the search at
    least a few moves to evaluate before the deadline.

    Always collects at least one move when the position has legal
    moves — the deadline check is skipped on the first yield. This
    guarantees that the root iteration has at least one candidate
    move to score, so ``best_move`` is never None when legal moves
    exist (per the 1.6.2 user spec).

    On abort, returns the partial list (>=1 move). The caller must
    check ``state.aborted`` and treat it as a non-exhaustive sample.
    """
    moves: List[Move4D] = []
    for move in board.legal_moves():
        if moves and _deadline_passed(state):
            state.aborted = True
            break
        moves.append(move)
    return moves


def _negamax(state: _SearchState,
             board: Board4D,
             depth: int,
             alpha: float,
             beta: float,
             ply_from_root: int) -> float:
    state.nodes += 1

    # 1.6.2: every-node deadline check, not every-1024.
    if _deadline_passed(state):
        state.aborted = True
        return 0.0

    if _is_terminal(board):
        return _terminal_score(board, ply_from_root)

    tt_move: Optional[Move4D] = None
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

    if depth == 0:
        if state.options.use_quiescence:
            return quiescence(
                board, alpha, beta, state.evaluator,
                max_depth=state.options.quiescence_max_depth,
            )
        return state.evaluator(board.to_position_dict(), board.turn)

    # 1.6.2: deadline-aware materialization. If we abort partway the
    # caller receives a partial moves list; we still try to score them
    # so the partial-iteration result is preserved at the root.
    moves = _materialize_legal_moves(state, board)
    if state.aborted and not moves:
        return 0.0
    if state.options.use_mvv_lva and not state.aborted:
        moves = order_moves(board, moves, tt_move=tt_move)

    best_score = -INF
    best_move: Optional[Move4D] = None
    original_alpha = alpha

    for move in moves:
        board.push(move)
        score = -_negamax(state, board, depth - 1, -beta, -alpha,
                          ply_from_root + 1)
        board.pop()

        if state.aborted:
            return best_score

        if score > best_score:
            best_score = score
            best_move = move
            if score > alpha:
                alpha = score
        if alpha >= beta:
            break

    if state.tt is not None and not state.aborted:
        if best_score <= original_alpha:
            bound = BoundType.UPPER
        elif best_score >= beta:
            bound = BoundType.LOWER
        else:
            bound = BoundType.EXACT
        state.tt.store(board, depth, best_score, best_move, bound)

    return best_score


def search(board: Board4D,
           evaluator: Callable[[Dict[int, object], bool], float],
           options: Optional[SearchOptions] = None) -> SearchResult:
    """Iterative-deepening alpha-beta search on a 4D Board4D.

    Same surface as :func:`chess_spectral.engine.search.search` (2D).
    See that module's docstring for parameter details.

    Note on perf: 4D move generation in pure Python is slow (~250s
    for the 28-king starting position's 2152-move legal set). For
    practical search depths use shallow positions or set
    ``time_budget_ms`` to bound runtime; the engine respects the
    budget and returns the deepest completed iteration.
    """
    if options is None:
        options = SearchOptions()

    start = time.monotonic()
    deadline_s = (
        start + options.time_budget_ms / 1000.0
        if options.time_budget_ms is not None else None
    )

    tt = TranspositionTable4D() if options.use_tt else None
    state = _SearchState(evaluator=evaluator, options=options,
                          tt=tt, deadline_s=deadline_s)

    if _is_terminal(board):
        elapsed_ms = (time.monotonic() - start) * 1000.0
        return SearchResult(
            best_move=None,
            best_score=_terminal_score(board, 0),
            depth_reached=0,
            nodes_searched=0,
            elapsed_ms=elapsed_ms,
        )

    best_move: Optional[Move4D] = None
    best_score: float = -INF
    depth_reached = 0

    for depth in range(1, options.max_depth + 1):
        state.aborted = False

        # 1.6.2: deadline-aware materialization at root, same as in
        # interior _negamax. If we abort during move-gen, ``moves`` is
        # whatever subset we collected; we score those and use the
        # partial-iteration best_move on exit.
        moves = _materialize_legal_moves(state, board)
        if not state.aborted and options.use_mvv_lva:
            tt_move = None
            if tt is not None:
                entry = tt.lookup(board)
                if entry is not None:
                    tt_move = entry.best_move
            moves = order_moves(board, moves, tt_move=tt_move)

        iter_best_score = -INF
        iter_best_move: Optional[Move4D] = None
        alpha, beta = -INF, INF

        for move in moves:
            # Per-move deadline check at the root: critical for tight
            # budgets where a single ``_negamax(depth-1)`` call can
            # cost seconds. Skipped on the first move to guarantee at
            # least one root move is scored even on a tight budget
            # (so ``best_move`` is non-None when legal moves exist).
            if iter_best_move is not None and _deadline_passed(state):
                state.aborted = True
                break
            board.push(move)
            score = -_negamax(state, board, depth - 1, -beta, -alpha,
                              ply_from_root=1)
            board.pop()
            # Even when state.aborted is set inside _negamax (deadline
            # tripped during recursion), the move's score has been
            # computed (or is the 0.0 sentinel from a depth-0 abort);
            # adopt it as iter_best_move if it improves on the running
            # best so we always have something to return.
            if score > iter_best_score:
                iter_best_score = score
                iter_best_move = move
                if score > alpha:
                    alpha = score
            if state.aborted:
                break

        if state.aborted:
            # 1.6.2: KEEP the partial-iteration best move when timing
            # out, so callers get something rather than the previous
            # iteration's already-stale answer. Only adopt if the
            # partial iteration scored at least one move.
            if iter_best_move is not None:
                best_move = iter_best_move
                best_score = iter_best_score
                # depth_reached stays at the previous fully-completed
                # iteration's depth — the partial-iteration result is
                # at depth `depth` but flagged via timed_out.
            break

        best_move = iter_best_move
        best_score = iter_best_score
        depth_reached = depth

        if tt is not None and best_move is not None:
            tt.store(board, depth, best_score, best_move,
                     BoundType.EXACT)

        if abs(best_score) >= MATE_SCORE - 100:
            break

    elapsed_ms = (time.monotonic() - start) * 1000.0

    return SearchResult(
        best_move=best_move,
        best_score=best_score,
        depth_reached=depth_reached,
        nodes_searched=state.nodes,
        elapsed_ms=elapsed_ms,
        pv=[],   # PV extraction TODO
        tt_hits=tt.hits if tt is not None else 0,
        tt_size=len(tt) if tt is not None else 0,
        timed_out=state.aborted,
    )
