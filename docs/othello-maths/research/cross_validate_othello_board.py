"""Phase 1c.1 — cross-validate OthelloBoard legal-move generation.

Compares `research/othello_utils.py::OthelloBoard.legal_moves()`
against Takizawa's reference bitboard implementation
`research/third_party/reversi_misc.py::get_moves()` at every
position in a corpus.

Bit-ordering convention — confirmed to match ours
-------------------------------------------------
Upstream's `str2index` computes  `(col_letter - 'a') + 8 * (row_digit - 1)`.
Our `rc_to_idx(r, c)` computes   `r * 8 + c`  with r = row_digit - 1,
c = col_letter - 'a'.  Both produce the same integer, so bit `i` in
their bitboard ↔ index `i` in our state array.  Conversion is a
direct bit-packing, no remapping.

Corpora probed by the CLI
-------------------------
  --corpus pgn           : replay every ply in a PGN file (default:
                            the Barcelona EGP 2026 file shipped in
                            the repo).
  --corpus synthetic-N   : N random-play positions, seeded for
                            reproducibility.

Exit non-zero when --fail-on-mismatch is set and any disagreement
is found.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from othello_utils import (
    BLACK,
    BOARD_SIZE,
    EMPTY,
    N,
    OthelloBoard,
    WHITE,
    idx_to_rc,
    rc_to_idx,
)
from othello_pgn_loader import (
    _ensure_utf8_stdio,
    parse_pgn_file,
    replay,
)

_ensure_utf8_stdio()

# Make the vendored reference import-visible without polluting the
# research namespace: add the sibling directory on demand.
_THIRD_PARTY = Path(__file__).resolve().parent / "third_party"
if str(_THIRD_PARTY) not in sys.path:
    sys.path.insert(0, str(_THIRD_PARTY))

import reversi_misc as _ref  # noqa: E402  (sys.path manipulated above)


# ---------------------------------------------------------------------------
# State -> bitboard conversion
# ---------------------------------------------------------------------------


def state_to_bitboards(
    state: np.ndarray, side_to_move: int
) -> tuple[int, int]:
    """Pack an OthelloBoard state array into
    ``(player_bb, opponent_bb)`` using the upstream bit convention.

    ``state[i]`` values:
      +1 = black, -1 = white, 0 = empty.
    """
    player_bb = 0
    opponent_bb = 0
    for i in range(N):
        v = int(state[i])
        if v == side_to_move:
            player_bb |= 1 << i
        elif v == -side_to_move:
            opponent_bb |= 1 << i
    return player_bb, opponent_bb


def bitboard_to_index_set(bb: int) -> set[int]:
    out: set[int] = set()
    i = 0
    while bb:
        if bb & 1:
            out.add(i)
        bb >>= 1
        i += 1
    return out


# ---------------------------------------------------------------------------
# Per-position comparison
# ---------------------------------------------------------------------------


def compare_position(
    state: np.ndarray, side_to_move: int
) -> dict:
    """Run both engines at a position; return a dict with agreement
    status and (if any) the disagreeing indices."""
    # Our implementation
    board = OthelloBoard()
    board.state = state.copy()
    board.side_to_move = side_to_move
    ours = set(board.legal_moves())
    # Upstream implementation
    player_bb, opponent_bb = state_to_bitboards(state, side_to_move)
    theirs_bb = _ref.get_moves(player_bb, opponent_bb)
    theirs = bitboard_to_index_set(theirs_bb)
    return {
        "agree": ours == theirs,
        "ours_only": sorted(ours - theirs),
        "theirs_only": sorted(theirs - ours),
        "count_ours": len(ours),
        "count_theirs": len(theirs),
    }


# ---------------------------------------------------------------------------
# Corpus iteration
# ---------------------------------------------------------------------------


def iterate_pgn_positions(pgn_path: Path):
    """Yield (game_idx, ply, state, side_to_move) triples over every
    position reached in the PGN corpus."""
    games = parse_pgn_file(pgn_path)
    for gi, g in enumerate(games):
        try:
            _, states, move_log = replay(g["moves"])
        except Exception as exc:
            print(
                f"[cross_validate] game {gi}: replay failed "
                f"({exc}); skipping",
                file=sys.stderr,
            )
            continue
        # side_to_move at state index s equals: BLACK for s = 0,
        # then the opposite of the side that moved in move_log[s-1].
        side = BLACK
        for s_idx, st in enumerate(states):
            yield gi, s_idx, st, side
            if s_idx < len(move_log):
                side = -move_log[s_idx]["side"]  # pre-move side flips after move


def iterate_synthetic_positions(n: int, seed: int):
    """Play random legal moves from the start; yield every
    intermediate position until ``n`` positions have been yielded."""
    rng = np.random.default_rng(seed)
    produced = 0
    while produced < n:
        bb = OthelloBoard()
        while not bb.is_terminal() and produced < n:
            yield -1, produced, bb.state.copy(), bb.side_to_move
            produced += 1
            moves = bb.legal_moves()
            if moves:
                bb.play(int(rng.choice(moves)))
            else:
                bb.play(None)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run(corpus_source, results_path: Path, quiet: bool) -> dict:
    total = 0
    agree = 0
    disagreements: list[dict] = []
    for gi, ply, state, side in corpus_source:
        result = compare_position(state, side)
        total += 1
        if result["agree"]:
            agree += 1
        else:
            disagreements.append(
                {
                    "game": gi,
                    "ply": ply,
                    "side_to_move": side,
                    "ours_count": result["count_ours"],
                    "theirs_count": result["count_theirs"],
                    "ours_only": result["ours_only"],
                    "theirs_only": result["theirs_only"],
                }
            )
    summary = {
        "n_positions": total,
        "n_agree": agree,
        "n_disagree": total - agree,
        "agreement_rate": agree / total if total else 0.0,
        "first_disagreements": disagreements[:20],
    }
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with results_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    if not quiet:
        print(
            f"positions compared: {total}; "
            f"agreement: {agree}/{total} "
            f"({100.0 * summary['agreement_rate']:.3f}%)"
        )
        if summary["n_disagree"]:
            print(
                f"first {min(20, summary['n_disagree'])} "
                f"disagreements logged to {results_path}"
            )
        print(f"wrote {results_path}")
    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    default_pgn = (
        Path(__file__).resolve().parent.parent
        / "dataset" / "liveothello_Barcelona_EGP_2026.pgn"
    )
    default_results = (
        Path(__file__).resolve().parent.parent / "results"
        / "phase1c_cross_validation.json"
    )
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # Default run: Barcelona EGP 2026 (35 games, 2184 positions) + exit
  # non-zero if any disagreement is found.
  python research/cross_validate_othello_board.py \\
      --fail-on-mismatch

  # Quick synthetic run: 1000 random-play positions, seed 7.
  python research/cross_validate_othello_board.py \\
      --corpus synthetic --synthetic-n 1000 --seed 7

  # Combined: run PGN corpus AND a synthetic set, logging to a
  # custom results path.
  python research/cross_validate_othello_board.py \\
      --corpus both --synthetic-n 500 \\
      --out results/my_cross_validation.json

reading the output:
  Target agreement rate is 100%.  If any disagreement appears, the
  JSON file records up to 20 per-position diffs with 'ours_only'
  and 'theirs_only' index lists — inspect those to find the bug
  in OthelloBoard (or, unlikely, in the vendored reference).
""",
    )
    parser.add_argument(
        "--corpus", choices=("pgn", "synthetic", "both"), default="pgn",
        help="Which corpus to validate against.  'pgn' = the PGN "
             "transcript file (default: Barcelona EGP 2026).  "
             "'synthetic' = random-play positions from the starting "
             "position, with a fixed seed for reproducibility.  "
             "'both' = run PGN first then append synthetic.",
    )
    parser.add_argument(
        "--pgn", type=Path, default=default_pgn,
        help="Path to the Othello PGN file.  Only used when "
             "--corpus includes pgn.  Default: the Barcelona EGP "
             "2026 file shipped with this repo.",
    )
    parser.add_argument(
        "--synthetic-n", type=int, default=1000,
        help="Number of synthetic random-play positions to test.  "
             "Only used when --corpus includes synthetic.  Default: "
             "1000, which takes well under a second.",
    )
    parser.add_argument(
        "--seed", type=int, default=7,
        help="RNG seed for synthetic random-play position generation.  "
             "Use the same seed to reproduce a previous run exactly.",
    )
    parser.add_argument(
        "--out", type=Path, default=default_results,
        help="Output JSON path (parents created).  Default: "
             "../results/phase1c_cross_validation.json next to this "
             "script.",
    )
    parser.add_argument(
        "--fail-on-mismatch", action="store_true",
        help="Exit with status 1 if any position disagrees between "
             "OthelloBoard and the reference.  Use this flag in CI.  "
             "Default: exit 0 regardless; the mismatch list is in "
             "the JSON file either way.",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress the stdout summary line.  The JSON file is "
             "always written.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    sources = []
    if args.corpus in ("pgn", "both"):
        sources.append(iterate_pgn_positions(args.pgn))
    if args.corpus in ("synthetic", "both"):
        sources.append(
            iterate_synthetic_positions(args.synthetic_n, args.seed)
        )

    def combined():
        for s in sources:
            yield from s

    summary = run(combined(), args.out, args.quiet)
    if args.fail_on_mismatch and summary["n_disagree"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
