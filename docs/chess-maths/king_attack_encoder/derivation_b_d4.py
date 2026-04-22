"""Derivation B: D4 decomposition of attack adjacency matrix.

See PHASE_OPERATOR_SUPPLEMENT_12.md §12.4.

Reduces the directed 64x64 attack adjacency A_ka to a 64-dim signal
(row-sum: total outgoing attacks from each source square) and projects
that signal onto the five D4 irreps via the same Serre character
projection chess_spectral.tables uses for encode_640's board signal.

Known tension: A_ka is not D4-symmetric in general, so the projection
is approximate — it returns the best-fit D4-equivariant component per
irrep. Whether that approximation carries useful signal or degenerates
to noise is empirical.
"""
import sys
from pathlib import Path

import chess
import numpy as np

from .attack_graph import attack_adjacency


def _locate_encoder():
    """Add chess_spectral to sys.path if not already importable.

    Mirrors the same pattern phase_operators/phase_similarity.py uses.
    chess_spectral lives at docs/chess-maths/chess-spectral/python/
    relative to this package's parent.
    """
    try:
        import chess_spectral  # noqa: F401
        return
    except ImportError:
        pass
    here = Path(__file__).resolve().parent
    candidates = [
        here.parent / "chess-spectral" / "python",
        here.parent.parent / "chess-spectral" / "python",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            sys.path.insert(0, str(candidate))
            return
    raise ImportError(
        "Cannot locate chess_spectral package. Expected relative to "
        f"{here}"
    )


_locate_encoder()
from chess_spectral.tables import project_irrep  # type: ignore  # noqa: E402


D4_IRREPS = ("A1", "A2", "B1", "B2", "E")


def attack_row_sum_signal(board: chess.Board) -> np.ndarray:
    """Reduce 64x64 directed A_ka to a 64-dim signal via row-sum.

    signal[i] = number of squares attacked by whatever opponent piece
    sits on square i (0 if no opponent piece on i). This is the input
    to the D4 projection.

    Alternative signals (column-sum, attacker-value-weighted row-sum,
    diagonal extraction) are deferred to Phase A2 if Phase A's
    row-sum choice produces a marginal result.
    """
    A = attack_adjacency(board).astype(np.float64)
    return A.sum(axis=1)


def derivation_b_channels(board: chess.Board) -> dict:
    """Return {irrep_name: 64-dim projection} for each of the five D4
    irreps, applied to the attack row-sum signal.

    Irrep ordering matches chess_spectral.tables.project_irrep: A1,
    A2, B1, B2, E.
    """
    signal = attack_row_sum_signal(board)
    out: dict = {}
    for irrep in D4_IRREPS:
        out[irrep] = project_irrep(signal, irrep).astype(np.float64)
    return out


def derivation_b_similarity(board_before: chess.Board,
                            move: chess.Move) -> dict:
    """Per-irrep cosine similarity between Derivation B channels
    before and after a move. Returns {irrep_name: cosine}.

    For zero-norm channels (empty attack graph, homogeneous signal
    with zero projection on some irrep), returns 0.0 for that irrep.

    board.turn is flipped on the post-move board so that `opp_color`
    inside `attack_adjacency` continues to select the defender's
    attackers (from the mover's perspective) rather than the mover's
    own pieces. See PHASE_OPERATOR_SUPPLEMENT_12.md §12.7.1.1.
    """
    board_after = board_before.copy(stack=False)
    board_after.push(move)
    board_after.turn = not board_after.turn
    before = derivation_b_channels(board_before)
    after = derivation_b_channels(board_after)
    out: dict = {}
    for irrep in D4_IRREPS:
        b = before[irrep]
        a = after[irrep]
        norm = float(np.linalg.norm(b) * np.linalg.norm(a))
        out[irrep] = (float(np.dot(b, a) / norm) if norm > 0 else 0.0)
    return out


def derivation_b_similarity_concat(board_before: chess.Board,
                                   move: chess.Move) -> float:
    """Cosine similarity of the 5*64 = 320-dim concatenated vector
    across all five D4 irreps. Single-scalar summary suitable for
    direct comparison with derivation_a_similarity.

    Flips board.turn after push per §12.7.1.1 so the post-move
    adjacency is computed from the mover's perspective.
    """
    board_after = board_before.copy(stack=False)
    board_after.push(move)
    board_after.turn = not board_after.turn
    before = derivation_b_channels(board_before)
    after = derivation_b_channels(board_after)
    b_concat = np.concatenate([before[i] for i in D4_IRREPS])
    a_concat = np.concatenate([after[i] for i in D4_IRREPS])
    norm = float(np.linalg.norm(b_concat) * np.linalg.norm(a_concat))
    if norm == 0.0:
        return 0.0
    return float(np.dot(b_concat, a_concat) / norm)
