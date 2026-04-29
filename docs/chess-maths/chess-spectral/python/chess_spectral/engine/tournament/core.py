"""Tournament harness core: agents, games, round-robin, ELO.

Pulled together from §16.3:
  * Agents bundle (evaluator, search_options, label).
  * Games play out via the search engine until terminal or max-ply.
  * Round-robin: every pair plays N_games rounds, alternating colors.
  * ELO updated incrementally; PGN logs (2D) or NDJSON4 (4D)
    optionally captured per game.

Dimension-agnostic via the ``play_one_move(board, agent)`` interface.
The caller provides the right ``board`` factory (chess.Board for 2D,
spatial_4d.Board4D for 4D).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import (
    Callable, List, Optional, Sequence, Tuple, Union,
)


# ---- Agent + result types -------------------------------------


@dataclass(frozen=True)
class Agent:
    """A configured chess engine: evaluator + search_options + label.

    The ``search_fn`` is the dim-specific ``search`` from
    ``chess_spectral.engine.search.search`` or
    ``chess_spectral_4d.engine.search.search``. The ``evaluator`` is
    one of the §16.1 ``evaluate(position, side_to_move) -> float``
    functions (material / spectral / qm).
    """
    label: str
    evaluator: Callable
    search_fn: Callable
    search_options: object   # SearchOptions (2D or 4D)


@dataclass
class GameResult:
    """Outcome of one game.

    ``score_white`` is 1.0 (white wins) / 0.0 (black wins) /
    0.5 (draw). ``moves`` is the played sequence. ``termination`` is
    a short string label: ``'checkmate'``, ``'stalemate'``,
    ``'threefold'``, ``'fifty_moves'``, ``'insufficient'``,
    ``'max_plies'``.
    """
    white: Agent
    black: Agent
    score_white: float
    moves: List[object]   # chess.Move (2D) or Move4D
    termination: str
    plies_played: int
    elapsed_ms: float


@dataclass
class TournamentResult:
    """Aggregated outcome of a round-robin tournament."""
    agents: List[Agent]
    games: List[GameResult]
    final_elos: dict   # label -> elo
    pair_records: dict   # (label_a, label_b) -> (wins, losses, draws)
    elapsed_ms: float


# ---- ELO rating ---------------------------------------------


class EloRating:
    """Incremental ELO updater. Standard formula:
        E = 1 / (1 + 10^((R_opp - R_self) / 400))
        R'_self = R_self + K * (S - E)
    where S is the actual score (1, 0.5, 0).

    K = 32 by default (FIDE-ish for development cycles); pass smaller
    K (e.g. 10) for fine-grained tournaments.
    """

    def __init__(self, initial: float = 1500.0, k: float = 32.0):
        self.initial = initial
        self.k = k
        self._ratings: dict[str, float] = {}

    def get(self, label: str) -> float:
        return self._ratings.setdefault(label, self.initial)

    def update(self, label_a: str, label_b: str,
               score_a: float) -> Tuple[float, float]:
        """Update both labels after a game where label_a scored
        score_a (1.0/0.5/0.0). Returns (new_a, new_b) ratings."""
        ra = self.get(label_a)
        rb = self.get(label_b)
        ea = 1.0 / (1.0 + 10.0 ** ((rb - ra) / 400.0))
        eb = 1.0 / (1.0 + 10.0 ** ((ra - rb) / 400.0))
        sa = score_a
        sb = 1.0 - score_a
        new_a = ra + self.k * (sa - ea)
        new_b = rb + self.k * (sb - eb)
        self._ratings[label_a] = new_a
        self._ratings[label_b] = new_b
        return new_a, new_b

    def all_ratings(self) -> dict:
        return dict(self._ratings)


# ---- Game play ----------------------------------------------


def _is_2d_board(board) -> bool:
    """Heuristic: 2D boards are chess.Board; 4D boards are
    spatial_4d.Board4D. We detect by attribute presence."""
    return hasattr(board, 'fen') and not hasattr(board, 'pawn_axis_at')


def play_game(white: Agent,
              black: Agent,
              board_factory: Callable[[], object],
              *,
              max_plies: int = 200,
              draw_predicates: Optional[Callable[[object], bool]] = None,
              ) -> GameResult:
    """Play a single game between white and black agents.

    Parameters
    ----------
    white, black : Agent
        Each side's engine configuration.
    board_factory : callable
        Returns a fresh starting board (chess.Board() for 2D,
        Board4D.empty()-then-populate for 4D). The caller is
        responsible for any specific starting-position setup.
    max_plies : int, default 200
        Hard cap on game length to avoid pathological infinite games.
    draw_predicates : optional callable
        ``draw_predicates(board) -> bool``. Caller-provided wrapper
        around the dim-specific draw rules
        (:mod:`chess_spectral.spatial_4d.draws.is_game_over` for 4D
        or python-chess's ``board.is_game_over()`` for 2D).
        If None, the harness queries dim-appropriate defaults.

    Returns
    -------
    GameResult with score_white in {1.0, 0.5, 0.0}, the move
    sequence, and a termination label.
    """
    board = board_factory()
    moves: List[object] = []
    start_time = time.monotonic()

    is_2d = _is_2d_board(board)

    # Draw / mate predicate fallback.
    if draw_predicates is None:
        if is_2d:
            def draw_predicates(b):
                return b.is_game_over()
        else:
            from chess_spectral.spatial_4d.draws import is_game_over
            draw_predicates = is_game_over

    plies = 0
    termination = 'max_plies'
    while plies < max_plies:
        if draw_predicates(board):
            # Determine reason. For 2D use python-chess's specific
            # predicates; for 4D use chess_spectral.spatial_4d.draws.
            termination = _classify_termination(board, is_2d)
            break

        # Whose turn?
        side_to_move = (
            board.turn if is_2d else board.turn
        )
        agent = white if side_to_move else black

        # Search for best move.
        result = agent.search_fn(board, agent.evaluator,
                                  agent.search_options)
        if result.best_move is None:
            # Engine couldn't find a move (shouldn't happen if
            # not game-over).
            termination = _classify_termination(board, is_2d)
            break

        board.push(result.best_move)
        moves.append(result.best_move)
        plies += 1

    # Score the game.
    score_white = _score_from_termination(board, termination, is_2d)

    elapsed_ms = (time.monotonic() - start_time) * 1000.0
    return GameResult(
        white=white, black=black,
        score_white=score_white,
        moves=moves,
        termination=termination,
        plies_played=plies,
        elapsed_ms=elapsed_ms,
    )


def _classify_termination(board, is_2d: bool) -> str:
    """Return a short termination label for game-over states."""
    if is_2d:
        if board.is_checkmate():
            return 'checkmate'
        if board.is_stalemate():
            return 'stalemate'
        if board.is_fivefold_repetition() if hasattr(
            board, 'is_fivefold_repetition'
        ) else False:
            return 'fivefold'
        if board.can_claim_threefold_repetition():
            return 'threefold'
        if board.can_claim_fifty_moves():
            return 'fifty_moves'
        if board.is_insufficient_material():
            return 'insufficient'
        return 'unknown'
    else:
        from chess_spectral.spatial_4d.draws import (
            is_checkmate, is_stalemate, is_threefold_repetition,
            is_fifty_move_rule, is_insufficient_material,
        )
        if is_checkmate(board):
            return 'checkmate'
        if is_stalemate(board):
            return 'stalemate'
        if is_threefold_repetition(board):
            return 'threefold'
        if is_fifty_move_rule(board):
            return 'fifty_moves'
        if is_insufficient_material(board):
            return 'insufficient'
        return 'unknown'


def _score_from_termination(board, termination: str,
                              is_2d: bool) -> float:
    """Convert termination label to score_white."""
    if termination == 'checkmate':
        # Side to move just got mated. board.turn is the loser.
        loser_white = board.turn   # both 2D and 4D use same convention
        return 0.0 if loser_white else 1.0
    if termination in ('stalemate', 'threefold', 'fifty_moves',
                        'insufficient', 'max_plies', 'fivefold',
                        'unknown'):
        return 0.5
    return 0.5


# ---- Round-robin ---------------------------------------------


def run_round_robin(agents: Sequence[Agent],
                    n_games_per_pair: int,
                    board_factory: Callable[[], object],
                    *,
                    max_plies: int = 200,
                    initial_elo: float = 1500.0,
                    elo_k: float = 32.0) -> TournamentResult:
    """Every pair plays n_games_per_pair games, alternating colors.

    Parameters
    ----------
    agents : sequence of Agent
        Participants. Pairs are formed from itertools.combinations.
    n_games_per_pair : int
        Number of games per pair. Half played as A-white, half as
        B-white (with rounding to nearest even number for symmetry).
    board_factory : callable
        Fresh-board constructor (see :func:`play_game`).
    max_plies : int
        Per-game hard cap.
    initial_elo : float, default 1500
    elo_k : float, default 32

    Returns
    -------
    TournamentResult with the full game list, final ELOs per
    label, and per-pair (wins, losses, draws) records.
    """
    from itertools import combinations

    elo = EloRating(initial=initial_elo, k=elo_k)
    games: List[GameResult] = []
    pair_records: dict = {}
    start_time = time.monotonic()

    for a, b in combinations(agents, 2):
        wld_ab = [0, 0, 0]   # wins-as-white, losses, draws (for a)
        n_white_a = (n_games_per_pair + 1) // 2
        n_white_b = n_games_per_pair - n_white_a
        for _ in range(n_white_a):
            game = play_game(a, b, board_factory, max_plies=max_plies)
            games.append(game)
            elo.update(a.label, b.label, game.score_white)
            if game.score_white > 0.5:
                wld_ab[0] += 1
            elif game.score_white < 0.5:
                wld_ab[1] += 1
            else:
                wld_ab[2] += 1
        for _ in range(n_white_b):
            game = play_game(b, a, board_factory, max_plies=max_plies)
            games.append(game)
            elo.update(b.label, a.label, game.score_white)
            # Score from a's perspective inverts since b was white.
            if game.score_white > 0.5:
                wld_ab[1] += 1   # a (black) lost
            elif game.score_white < 0.5:
                wld_ab[0] += 1   # a (black) won
            else:
                wld_ab[2] += 1
        pair_records[(a.label, b.label)] = tuple(wld_ab)

    elapsed_ms = (time.monotonic() - start_time) * 1000.0
    return TournamentResult(
        agents=list(agents),
        games=games,
        final_elos=elo.all_ratings(),
        pair_records=pair_records,
        elapsed_ms=elapsed_ms,
    )


__all__ = [
    "Agent",
    "GameResult",
    "TournamentResult",
    "EloRating",
    "play_game",
    "run_round_robin",
]
