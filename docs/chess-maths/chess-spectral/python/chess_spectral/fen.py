"""fen — FEN placement → encoder pos-dict conversion.

Single source of truth for the convention used across the 640-dim
encoder: square index = row*8 + col, row 0 = rank 8 (Black's back
rank). This mirrors codegen/emit_test_vectors.py::parse_fen_placement
and replaces the standalone `from pgn_bridge import fen_to_pos`
helper that used to live in the now-deleted docs/chess-maths/pgn_bridge.py.
"""
from __future__ import annotations


def fen_to_pos(fen: str) -> dict[int, str]:
    """Parse the placement field of a FEN string into {square: piece_char}.

    Accepts either a full FEN ("... w KQkq - 0 1") or just the placement
    field ("rnbqkbnr/..."). Square convention matches encode_640 / the C
    encoder: row 0 = rank 8, square 0 = a8, square 63 = h1.
    """
    if not fen:
        raise ValueError("empty FEN")
    placement = fen.split()[0]
    rows = placement.split("/")
    if len(rows) != 8:
        raise ValueError(f"bad FEN placement: {fen!r}")
    pos: dict[int, str] = {}
    for r, row in enumerate(rows):
        c = 0
        for ch in row:
            if ch.isdigit():
                c += int(ch)
            else:
                pos[r * 8 + c] = ch
                c += 1
        if c != 8:
            raise ValueError(f"bad FEN row {r}: {row!r}")
    return pos


def uci_to_indices(uci: str) -> tuple[int, int, int]:
    """Decode a UCI move ("e2e4", "e7e8q") into (from_sq, to_sq, promo).

    Square indices use the encoder convention (row 0 = rank 8). `promo`
    is the ASCII code of the promotion piece letter (uppercase) or 0 if
    the move isn't a promotion. Returns (0xFF, 0xFF, 0) for malformed
    input so callers can use it as a "no move" sentinel.
    """
    if not uci or len(uci) < 4:
        return (0xFF, 0xFF, 0)
    try:
        f_file = ord(uci[0]) - ord("a")
        f_rank = int(uci[1])
        t_file = ord(uci[2]) - ord("a")
        t_rank = int(uci[3])
    except (ValueError, IndexError):
        return (0xFF, 0xFF, 0)
    if not (0 <= f_file < 8 and 0 <= t_file < 8 and
            1 <= f_rank <= 8 and 1 <= t_rank <= 8):
        return (0xFF, 0xFF, 0)
    from_sq = (8 - f_rank) * 8 + f_file
    to_sq = (8 - t_rank) * 8 + t_file
    promo = ord(uci[4].upper()) if len(uci) >= 5 else 0
    return (from_sq & 0xFF, to_sq & 0xFF, promo & 0xFF)
