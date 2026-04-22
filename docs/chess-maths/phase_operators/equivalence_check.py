"""§11.3 phase-operator equivalence experiment.

Validates that phase-algebra destinations from §11.2 operators match
python-chess empty-board legal moves over all (polarization, origin)
pairs, writes a CSV per §11.3.5, and prints a summary to stdout.

Requires the chess_spectral package to be importable
(``pip install -e ../chess-spectral/python/`` if running from source).

Run from this directory:
    python equivalence_check.py [--out PATH] [--fail-on-mismatch]
"""
import argparse
import csv
import sys
from pathlib import Path

import chess

from chess_spectral.phase_operators import (
    phi, P_rook, P_bishop, P_queen, P_king, P_knight,
    P_pawn_white, P_pawn_black,
    phase_set_to_board,
)


POLARIZATIONS = ["N", "B", "R", "Q", "K", "P_white", "P_black"]

_PIECE_CHAR = {
    "N": "N", "B": "B", "R": "R", "Q": "Q", "K": "K",
    "P_white": "P", "P_black": "P",
}

_COLOR = {
    "N": chess.WHITE, "B": chess.WHITE, "R": chess.WHITE,
    "Q": chess.WHITE, "K": chess.WHITE,
    "P_white": chess.WHITE, "P_black": chess.BLACK,
}


def legal_dests_for(piece_char: str, r: int, c: int,
                    color: chess.Color = chess.WHITE) -> frozenset[tuple[int, int]]:
    """Empty-board-with-one-piece python-chess reference set.

    (r, c) is (rank, file) in our convention; matches chess.square(c, r).
    """
    board = chess.Board(None)
    piece = chess.Piece.from_symbol(
        piece_char.upper() if color == chess.WHITE else piece_char.lower()
    )
    origin_sq = chess.square(c, r)
    board.set_piece_at(origin_sq, piece)
    board.turn = color
    # King needs to be on the board for legal_moves to enumerate for non-king
    # pieces, but on an empty board python-chess is permissive — it allows
    # legal_moves on a board with only the piece under test. Verified.
    dests = set()
    for move in board.legal_moves:
        if move.from_square == origin_sq:
            to_sq = move.to_square
            dests.add((chess.square_rank(to_sq), chess.square_file(to_sq)))
    return frozenset(dests)


def phase_dests_for(polarization: str, r: int, c: int) -> frozenset[tuple[int, int]]:
    origin_phi = phi(r, c)
    if polarization == "R":
        phase_set = P_rook(origin_phi)
    elif polarization == "B":
        phase_set = P_bishop(origin_phi)
    elif polarization == "Q":
        phase_set = P_queen(origin_phi)
    elif polarization == "K":
        phase_set = P_king(origin_phi)
    elif polarization == "N":
        phase_set = P_knight(origin_phi)
    elif polarization == "P_white":
        phase_set = P_pawn_white(origin_phi, on_starting_rank=(r == 1),
                                 include_captures=False)
    elif polarization == "P_black":
        phase_set = P_pawn_black(origin_phi, on_starting_rank=(r == 6),
                                 include_captures=False)
    else:
        raise ValueError(f"unknown polarization: {polarization}")
    return phase_set_to_board(phase_set)


def _origins_for(polarization: str) -> list[tuple[int, int]]:
    if polarization in {"P_white", "P_black"}:
        return [(r, c) for r in range(1, 7) for c in range(8)]
    return [(r, c) for r in range(8) for c in range(8)]


def _serialize_set(s) -> str:
    return ";".join(f"({r},{c})" for (r, c) in sorted(s))


def run_experiment_1() -> list[dict]:
    rows = []
    for pol in POLARIZATIONS:
        piece_char = _PIECE_CHAR[pol]
        color = _COLOR[pol]
        for (r, c) in _origins_for(pol):
            phase_dests = phase_dests_for(pol, r, c)
            geom_dests = legal_dests_for(piece_char, r, c, color)
            equal = phase_dests == geom_dests
            missing = geom_dests - phase_dests
            extra = phase_dests - geom_dests
            rows.append({
                "polarization": pol,
                "origin_row": r,
                "origin_col": c,
                "phase_op_destinations": _serialize_set(phase_dests),
                "geometric_destinations": _serialize_set(geom_dests),
                "set_equal": "true" if equal else "false",
                "missing": _serialize_set(missing),
                "extra": _serialize_set(extra),
            })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out", type=Path,
        default=Path(__file__).resolve().parents[1]
        / "results" / "phase_operator_experiments" / "exp1_equivalence.csv",
        help="Output CSV path (parents created).")
    parser.add_argument("--fail-on-mismatch", action="store_true",
                        help="Exit nonzero if any (polarization, origin) mismatches.")
    args = parser.parse_args()

    rows = run_experiment_1()
    total = len(rows)
    matches = sum(1 for row in rows if row["set_equal"] == "true")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "polarization", "origin_row", "origin_col",
        "phase_op_destinations", "geometric_destinations",
        "set_equal", "missing", "extra",
    ]
    with args.out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"§11.3 complete: {matches}/{total} pairs equivalent")

    if args.fail_on_mismatch and matches != total:
        mismatched = [row for row in rows if row["set_equal"] == "false"]
        print(f"{len(mismatched)} mismatched pairs:", file=sys.stderr)
        for row in mismatched[:10]:
            print(f"  {row['polarization']} @ ({row['origin_row']},"
                  f"{row['origin_col']}): missing={row['missing']} "
                  f"extra={row['extra']}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
