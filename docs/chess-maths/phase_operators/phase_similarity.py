"""§11.5 Path 2: phase-tuple similarity as field gradient indicator.

Computes cosine similarity between encode_640(position_before) and
encode_640(position_after_move). A candidate phase-native signal whose
correlation with thermodynamic quantities (including is_check_unsafe)
§11.5 is set up to measure.

See PHASE_OPERATOR_SUPPLEMENT.md §11.5.2 for the underlying field-theoretic
motivation.
"""
import sys
from pathlib import Path

import chess
import numpy as np


def _locate_encoder():
    """Add the chess_spectral package to sys.path if not already importable."""
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
from chess_spectral import encode_640, fen_to_pos  # type: ignore  # noqa: E402


def phase_similarity(board_before: chess.Board, move: chess.Move) -> float:
    """Cosine similarity between encode_640 before and after `move`.

    Returns a float in [-1, 1]. 1.0 means the 640-dim encoding is identical
    (impossible for any real move since at least one piece's phase changes).
    Higher values mean the field configuration changes less.
    """
    fen_before = board_before.fen()
    board_after = board_before.copy(stack=False)
    board_after.push(move)
    fen_after = board_after.fen()

    enc_before = encode_640(fen_to_pos(fen_before))
    enc_after = encode_640(fen_to_pos(fen_after))

    num = float(np.dot(enc_before, enc_after))
    den = float(np.linalg.norm(enc_before) * np.linalg.norm(enc_after))
    if den == 0.0:
        return 0.0
    return num / den
