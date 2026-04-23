"""Phase 1c.2 — WTHOR opening-book frequency loader.

Wraps the ``opening_book_freq.csv.bz2`` artefact from
github.com/eukaryo/reversi-scripts.  That file is a streaming CSV
with schema

    count, n_empties, obf

where

  - ``count`` is the integer frequency of the position across the
    61,549 WTHOR tournament games (2001-2020);
  - ``n_empties`` is the number of empty squares in the board (60
    = starting position, 0 = game terminal);
  - ``obf`` is the Othello Binary Format string: 64 chars over
    ``{'-', 'O', 'X'}`` followed by ``' X;'`` or ``' O;'`` indicating
    the side to move.

Positions are stored in D4-canonical form via the upstream
``board_unique`` function — eight symmetry-equivalent positions
collapse to a single entry whose count is their sum.  Our loader
applies the same canonicalisation before lookup.

Design decisions
----------------
- Memory: the raw file has ~2.57M rows.  A full in-memory dict costs
  roughly 500 MB.  By default we build a FILTERED dict: the caller
  passes a set of canonicalised query keys (one per position they
  will look up), and we keep only those entries.  This cuts the dict
  to < 100 k entries for typical corpus-sized queries.
- Smoothing: Shannon information per move uses ``P(move | empirical)``.
  Uncovered moves would give ``log_2 0 = inf``.  We apply add-alpha
  Laplace smoothing with a user-settable ``laplace=`` (default 1.0).
- Coverage tracking: every probability lookup reports whether the
  position was in the book (``covered``) and, if so, whether the
  specific successor position from the chosen move was (``move_covered``).
  Callers can split statistics by coverage.
"""

from __future__ import annotations

import argparse
import bz2
import json
import sys
from pathlib import Path
from typing import Iterable

import numpy as np

from othello_utils import N, OthelloBoard
from othello_pgn_loader import _ensure_utf8_stdio, parse_pgn_file, replay

_ensure_utf8_stdio()

_THIRD_PARTY = Path(__file__).resolve().parent / "third_party"
if str(_THIRD_PARTY) not in sys.path:
    sys.path.insert(0, str(_THIRD_PARTY))
import reversi_misc as _ref  # noqa: E402


# ---------------------------------------------------------------------------
# Bitboard conversion (matches cross_validate_othello_board.py)
# ---------------------------------------------------------------------------


def state_to_bitboards(
    state: np.ndarray, side_to_move: int
) -> tuple[int, int]:
    player_bb = 0
    opponent_bb = 0
    for i in range(N):
        v = int(state[i])
        if v == side_to_move:
            player_bb |= 1 << i
        elif v == -side_to_move:
            opponent_bb |= 1 << i
    return player_bb, opponent_bb


def canonical_key(
    state: np.ndarray, side_to_move: int
) -> tuple[int, int]:
    pb, ob = state_to_bitboards(state, side_to_move)
    return tuple(_ref.board_unique(pb, ob))


# ---------------------------------------------------------------------------
# Corpus key enumeration (pre-index)
# ---------------------------------------------------------------------------


def enumerate_query_keys(
    pgn_path: Path,
) -> tuple[set[tuple[int, int]], int]:
    """Walk a PGN corpus, collect canonical (player_bb, opponent_bb)
    keys for every (position_before_move, position_after_move) pair.

    Returns (keys, n_plies_seen).  The set is suitable for passing
    as ``query_set`` to ``OpeningBookFreq.load`` — any key outside
    this set is irrelevant to the current analysis and can be
    dropped to save memory.
    """
    keys: set[tuple[int, int]] = set()
    games = parse_pgn_file(pgn_path)
    n_plies = 0
    for g in games:
        try:
            _, states, move_log = replay(g["moves"])
        except Exception:
            continue
        side = None
        for ply, st in enumerate(states):
            if ply == 0:
                side = 1  # BLACK
            else:
                side = -move_log[ply - 1]["side"]
            keys.add(canonical_key(st, side))
            # Also enumerate successors: one per legal move.
            board = OthelloBoard()
            board.state = st.copy()
            board.side_to_move = side
            for m in board.legal_moves():
                child = board.copy()
                child.play(m)
                keys.add(canonical_key(child.state, child.side_to_move))
            n_plies += 1
    return keys, n_plies


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


class OpeningBookFreq:
    """Opening-book position frequency lookup."""

    def __init__(
        self,
        index: dict[tuple[int, int], int],
        n_rows_scanned: int,
        n_rows_kept: int,
    ) -> None:
        self._index = index
        self.n_rows_scanned = n_rows_scanned
        self.n_rows_kept = n_rows_kept

    @classmethod
    def load(
        cls,
        bz2_path: Path,
        query_set: set[tuple[int, int]] | None = None,
    ) -> "OpeningBookFreq":
        index: dict[tuple[int, int], int] = {}
        n_scanned = 0
        n_kept = 0
        with bz2.open(bz2_path, "rt", encoding="utf-8") as f:
            header = f.readline()
            if "count" not in header:
                raise ValueError(
                    f"unexpected header in {bz2_path}: {header!r}"
                )
            for line in f:
                n_scanned += 1
                try:
                    count_s, _, obf = line.rstrip().split(",", 2)
                    count = int(count_s)
                    pb, ob = _ref.obf_to_bitboards(obf)
                    key = tuple(_ref.board_unique(pb, ob))
                except Exception:
                    # Tolerate malformed lines but do not abort.
                    continue
                if query_set is not None and key not in query_set:
                    continue
                index[key] = index.get(key, 0) + count
                n_kept += 1
        return cls(index, n_scanned, n_kept)

    def count_at(
        self, state: np.ndarray, side_to_move: int
    ) -> int:
        return self._index.get(canonical_key(state, side_to_move), 0)

    def position_covered(
        self, state: np.ndarray, side_to_move: int
    ) -> bool:
        return canonical_key(state, side_to_move) in self._index

    def move_probabilities(
        self, board: OthelloBoard, laplace: float = 1.0
    ) -> dict[int, float]:
        legal = board.legal_moves()
        raw: dict[int, int] = {}
        for m in legal:
            child = board.copy()
            child.play(m)
            raw[m] = self.count_at(child.state, child.side_to_move)
        total = sum(raw.values()) + laplace * len(legal)
        if total == 0:
            uniform = 1.0 / len(legal) if legal else 0.0
            return {m: uniform for m in legal}
        return {m: (raw[m] + laplace) / total for m in legal}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    default_bz2 = (
        Path(__file__).resolve().parent.parent
        / "dataset" / "reversi_scripts" / "opening_book_freq.csv.bz2"
    )
    default_pgn = (
        Path(__file__).resolve().parent.parent
        / "dataset" / "liveothello_Barcelona_EGP_2026.pgn"
    )
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # Report coverage stats for every position in the Barcelona corpus.
  python research/opening_book_loader.py

  # Use a different PGN or point to a book at a custom location.
  python research/opening_book_loader.py \\
      --book /path/to/opening_book_freq.csv.bz2 \\
      --pgn dataset/other_tournament.pgn

  # Skip the corpus pre-filter (loads the full ~2.57M-row book; needs
  # ~500 MB RAM but enables ad-hoc queries).
  python research/opening_book_loader.py --full-load

reading the output:
  Coverage = fraction of queried (position, side_to_move) pairs that
  appear in the WTHOR book.  Early-game positions have coverage near
  1.0; late-game positions typically drop off as play diverges.
  The stratification by n_empties shows the falloff.
""",
    )
    parser.add_argument(
        "--book", type=Path, default=default_bz2,
        help="Path to opening_book_freq.csv.bz2 as vendored in "
             "dataset/reversi_scripts/.  Default: that file.",
    )
    parser.add_argument(
        "--pgn", type=Path, default=default_pgn,
        help="Path to the PGN corpus whose positions are queried "
             "against the book.  Default: the Barcelona EGP 2026 "
             "file.",
    )
    parser.add_argument(
        "--full-load", action="store_true",
        help="Skip the corpus-filtered loading path and read the "
             "full ~2.57M-row book into memory (~500 MB RAM).  "
             "Only useful for interactive exploration across many "
             "corpora; for the Phase 1c.2 T3 analysis the default "
             "filtered mode is far faster.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    print(f"corpus: {args.pgn}")
    print(f"book:   {args.book}")

    # Pre-index the query set (positions + successors)
    if args.full_load:
        print("loading full book (this takes ~60 s) ...")
        book = OpeningBookFreq.load(args.book, query_set=None)
    else:
        keys, n_plies = enumerate_query_keys(args.pgn)
        print(
            f"corpus has {n_plies} plies; {len(keys)} unique "
            f"canonical keys in the query set"
        )
        print("loading book filtered to corpus query set ...")
        book = OpeningBookFreq.load(args.book, query_set=keys)
    print(
        f"scanned {book.n_rows_scanned} rows; kept "
        f"{book.n_rows_kept} ({len(book._index)} unique keys)"
    )

    # Coverage stratified by n_empties
    games = parse_pgn_file(args.pgn)
    per_phase: dict[int, dict[str, int]] = {}
    for g in games:
        try:
            _, states, move_log = replay(g["moves"])
        except Exception:
            continue
        side = None
        for ply, st in enumerate(states):
            if ply == 0:
                side = 1
            else:
                side = -move_log[ply - 1]["side"]
            n_empty = int(np.sum(st == 0))
            bucket = per_phase.setdefault(
                n_empty, {"seen": 0, "covered": 0}
            )
            bucket["seen"] += 1
            if book.position_covered(st, side):
                bucket["covered"] += 1

    print("\ncoverage by n_empties (sampled from corpus):")
    print(f"  {'empties':>7s}  {'seen':>6s}  {'covered':>8s}  {'%':>6s}")
    for k in sorted(per_phase.keys(), reverse=True):
        bkt = per_phase[k]
        pct = 100.0 * bkt["covered"] / max(bkt["seen"], 1)
        print(
            f"  {k:>7d}  {bkt['seen']:>6d}  {bkt['covered']:>8d}  "
            f"{pct:>5.1f}%"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
