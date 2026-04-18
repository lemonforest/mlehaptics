"""analyze_delta_sigma — per-move Δ and σ collection across a GM corpus.

First-pass collector for two per-move scalars:

  κ_annihilate(self, target) = piece_value[target] − piece_value[self]
                               (0 for non-captures)
  κ_threat(dest, self)       = Σ_{opp pieces attacking dest after the move}
                                   max(0, piece_value[self] − piece_value[opp])
  Δ                          = κ_annihilate − κ_threat
  σ(move)                    = stdev(Δ over fiber-neighbors of move)

Fiber-neighbors of a move are the legal moves from the same position that
share its aggressor type OR its destination square. (The spec's third
condition — same aggressor type AND same origin — is a subset of the first
and adds nothing.)

Purpose: generate raw data; no interpretation, no tuning, no plotting.

Piece values: spectrally-derived per notebook §9c (P=0.84, N=2.0, B=3.4,
R=5.4, Q=8.8, K=2.5). These are hardcoded rather than imported from
chess_spectral.tables.SPECTRAL_VALS because that module overrides P to 1.0
(see tables.py:157) — a known divergence flagged for later reconciliation.

Run `python analyze_delta_sigma.py --help` for CLI options.
"""

from __future__ import annotations

import argparse
import csv
import io
import math
import random
import statistics
import sys
import textwrap
from pathlib import Path

import chess
import chess.pgn


# ─── Paths / defaults ──────────────────────────────────────────────────────

HERE = Path(__file__).resolve().parent
REPO_CHESS_MATHS = HERE.parent.parent
DEFAULT_CORPUS_DIR = REPO_CHESS_MATHS / "results" / "chessgames_pair_2026-04-15_N2"
DEFAULT_PGN = DEFAULT_CORPUS_DIR / "pgn"
DEFAULT_LABEL = "chessgames_pair"


# ─── Piece values ──────────────────────────────────────────────────────────

# See module docstring for the divergence from SPECTRAL_VALS.
PIECE_VALUES: dict[int, float] = {
    chess.PAWN:   0.84,
    chess.KNIGHT: 2.0,
    chess.BISHOP: 3.4,
    chess.ROOK:   5.4,
    chess.QUEEN:  8.8,
    chess.KING:   2.5,
}
PIECE_LETTER: dict[int, str] = {
    chess.PAWN: "P", chess.KNIGHT: "N", chess.BISHOP: "B",
    chess.ROOK: "R", chess.QUEEN: "Q", chess.KING: "K",
}


# ─── CSV schema ────────────────────────────────────────────────────────────

CSV_COLUMNS = [
    "game_id", "ply", "fen", "side_to_move",
    "move_uci", "move_san",
    "is_capture", "aggressor_type", "target_type",
    "kappa_annihilate", "kappa_threat", "delta", "sigma",
    "was_played",
]


# ─── Per-move quantities ───────────────────────────────────────────────────

def captured_piece(board: chess.Board, move: chess.Move) -> chess.Piece | None:
    """Return the piece captured by ``move`` on ``board`` (handles en passant)."""
    if board.is_en_passant(move):
        ep_sq = move.to_square + (-8 if board.turn == chess.WHITE else 8)
        return board.piece_at(ep_sq)
    return board.piece_at(move.to_square)


def kappa_annihilate(aggressor_type: int, target_type: int | None) -> float:
    if target_type is None:
        return 0.0
    return PIECE_VALUES[target_type] - PIECE_VALUES[aggressor_type]


def kappa_threat(board: chess.Board, move: chess.Move, aggressor_type: int) -> float:
    """Aggregate threat to the just-moved piece on its destination square.

    Evaluated on the post-move board. Promotion is not specially modeled —
    we still use the pre-move aggressor type (PAWN) for self_value per
    first-pass spec.
    """
    self_value = PIECE_VALUES[aggressor_type]
    self_color = board.turn  # before push: colour of the moving side

    post = board.copy(stack=False)
    post.push(move)
    dest = move.to_square

    total = 0.0
    for sq, piece in post.piece_map().items():
        if piece.color == self_color:
            continue
        if dest in post.attacks(sq):
            total += max(0.0, self_value - PIECE_VALUES[piece.piece_type])
    return total


def fiber_neighbors(
    target: chess.Move,
    moves: list[chess.Move],
    meta: dict[chess.Move, dict],
) -> list[chess.Move]:
    a_type = meta[target]["aggressor_type"]
    dest = target.to_square
    out: list[chess.Move] = []
    for m in moves:
        if meta[m]["aggressor_type"] == a_type or m.to_square == dest:
            out.append(m)
    return out


def compute_position_rows(
    board: chess.Board,
    played: chess.Move,
    game_id: str,
    ply: int,
) -> list[dict]:
    legal = list(board.legal_moves)
    if not legal:
        return []

    fen = board.fen()
    side = "w" if board.turn == chess.WHITE else "b"

    meta: dict[chess.Move, dict] = {}
    for m in legal:
        aggressor = board.piece_at(m.from_square)
        aggressor_type = aggressor.piece_type
        target_piece = captured_piece(board, m)
        target_type = target_piece.piece_type if target_piece is not None else None

        k_ann = kappa_annihilate(aggressor_type, target_type)
        k_thr = kappa_threat(board, m, aggressor_type)

        meta[m] = {
            "aggressor_type": aggressor_type,
            "target_type": target_type,
            "is_capture": target_type is not None,
            "san": board.san(m),
            "k_ann": k_ann,
            "k_thr": k_thr,
            "delta": k_ann - k_thr,
        }

    for m in legal:
        neighbors = fiber_neighbors(m, legal, meta)
        neigh_deltas = [meta[n]["delta"] for n in neighbors]
        if len(neigh_deltas) < 3:
            meta[m]["sigma"] = float("nan")
        else:
            meta[m]["sigma"] = statistics.stdev(neigh_deltas)

    rows: list[dict] = []
    for m in sorted(legal, key=lambda x: x.uci()):
        info = meta[m]
        rows.append({
            "game_id": game_id,
            "ply": ply,
            "fen": fen,
            "side_to_move": side,
            "move_uci": m.uci(),
            "move_san": info["san"],
            "is_capture": info["is_capture"],
            "aggressor_type": PIECE_LETTER[info["aggressor_type"]],
            "target_type": (PIECE_LETTER[info["target_type"]]
                            if info["target_type"] is not None else "none"),
            "kappa_annihilate": info["k_ann"],
            "kappa_threat": info["k_thr"],
            "delta": info["delta"],
            "sigma": info["sigma"],
            "was_played": (m == played),
        })
    return rows


# ─── Game validation & source iteration ────────────────────────────────────

def mainline_ply_count(game: chess.pgn.Game) -> int:
    n = 0
    for _ in game.mainline_moves():
        n += 1
    return n


def is_valid_game(game: chess.pgn.Game | None, min_plies: int) -> tuple[bool, str]:
    """Return (ok, reason). Reason is empty when ok is True."""
    if game is None:
        return False, "null game"
    if game.errors:
        # python-chess populates .errors on illegal / unparseable moves.
        return False, f"parser errors ({len(game.errors)})"
    plies = mainline_ply_count(game)
    if plies < min_plies:
        return False, f"too short ({plies} plies < {min_plies})"
    return True, ""


def iter_source_games(
    pgn_path: Path,
    min_plies: int,
) -> list[tuple[str, chess.pgn.Game, dict[str, int]]]:
    """Enumerate valid games from a PGN file or a directory of PGN files.

    Returns (game_id, game, filter_counts) — game_id is deterministic and
    unique within the source. filter_counts is a summary dict (total, kept,
    skipped_by_reason) returned alongside each yielded game only once at
    the end for simplicity this is NOT yielded; see the returned list.
    """
    accepted: list[tuple[str, chess.pgn.Game]] = []
    counts = {"total": 0, "kept": 0,
              "skip_null": 0, "skip_parser_errors": 0, "skip_short": 0}

    def _consume(fh, prefix: str, multi_game: bool):
        idx = 0
        while True:
            try:
                game = chess.pgn.read_game(fh)
            except Exception:
                # Catastrophic parse error — advance by bailing out of this handle.
                return
            if game is None:
                return
            counts["total"] += 1
            ok, reason = is_valid_game(game, min_plies)
            if not ok:
                if reason == "null game":
                    counts["skip_null"] += 1
                elif reason.startswith("parser errors"):
                    counts["skip_parser_errors"] += 1
                else:
                    counts["skip_short"] += 1
                idx += 1
                continue
            gid = f"{prefix}_{idx:04d}" if multi_game else prefix
            accepted.append((gid, game))
            counts["kept"] += 1
            idx += 1

    if pgn_path.is_dir():
        for pgn_file in sorted(pgn_path.glob("*.pgn")):
            with pgn_file.open("r", encoding="utf-8") as fh:
                # Allow multi-game files in a directory: use stem_####.
                # But if a file has exactly one game, use the bare stem.
                start_accepted = len(accepted)
                _consume(fh, pgn_file.stem, multi_game=True)
                added = len(accepted) - start_accepted
                if added == 1:
                    # Rename back to bare stem (backward compatibility).
                    gid_old, game = accepted[-1]
                    accepted[-1] = (pgn_file.stem, game)
    else:
        with pgn_path.open("r", encoding="utf-8") as fh:
            _consume(fh, pgn_path.stem, multi_game=True)

    return accepted, counts


# ─── Row collection ────────────────────────────────────────────────────────

def collect_rows_from_games(games: list[tuple[str, chess.pgn.Game]]) -> list[dict]:
    rows: list[dict] = []
    for game_id, game in games:
        board = game.board()
        for ply, played in enumerate(game.mainline_moves(), start=1):
            if not any(True for _ in board.legal_moves):
                break
            rows.extend(compute_position_rows(board, played, game_id, ply))
            board.push(played)
    return rows


# ─── CSV I/O ───────────────────────────────────────────────────────────────

def rows_to_csv_dict(r: dict) -> dict:
    out = dict(r)
    out["is_capture"] = "True" if r["is_capture"] else "False"
    out["was_played"] = "True" if r["was_played"] else "False"
    out["kappa_annihilate"] = f"{r['kappa_annihilate']:.6f}"
    out["kappa_threat"] = f"{r['kappa_threat']:.6f}"
    out["delta"] = f"{r['delta']:.6f}"
    s = r["sigma"]
    out["sigma"] = "NaN" if math.isnan(s) else f"{s:.6f}"
    return out


def load_csv_rows(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows.append({
                "game_id": r["game_id"],
                "ply": int(r["ply"]),
                "fen": r["fen"],
                "side_to_move": r["side_to_move"],
                "move_uci": r["move_uci"],
                "move_san": r["move_san"],
                "is_capture": r["is_capture"] == "True",
                "aggressor_type": r["aggressor_type"],
                "target_type": r["target_type"],
                "kappa_annihilate": float(r["kappa_annihilate"]),
                "kappa_threat": float(r["kappa_threat"]),
                "delta": float(r["delta"]),
                "sigma": float("nan") if r["sigma"] == "NaN" else float(r["sigma"]),
                "was_played": r["was_played"] == "True",
            })
    return rows


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows_sorted = sorted(rows, key=lambda r: (r["game_id"], r["ply"], r["move_uci"]))
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        w.writeheader()
        for r in rows_sorted:
            w.writerow(rows_to_csv_dict(r))


# ─── Summary statistics ────────────────────────────────────────────────────

def five_number(values: list[float]) -> dict:
    vals = [v for v in values if not math.isnan(v)]
    if not vals:
        return {"n": 0}
    n = len(vals)
    s = sorted(vals)

    def q(p: float) -> float:
        idx = p * (n - 1)
        lo, hi = int(math.floor(idx)), int(math.ceil(idx))
        if lo == hi:
            return s[lo]
        return s[lo] + (s[hi] - s[lo]) * (idx - lo)

    mean = sum(vals) / n
    std = statistics.pstdev(vals) if n > 1 else 0.0
    return {"n": n, "min": s[0], "max": s[-1], "mean": mean, "std": std,
            "q1": q(0.25), "median": q(0.50), "q3": q(0.75)}


def fmt_dist(name: str, stats: dict, nan_count: int | None = None) -> str:
    if stats.get("n", 0) == 0:
        return f"{name}: empty\n"
    parts = [
        f"{name}:",
        f"  n      = {stats['n']}",
        f"  min    = {stats['min']:.4f}",
        f"  q1     = {stats['q1']:.4f}",
        f"  median = {stats['median']:.4f}",
        f"  q3     = {stats['q3']:.4f}",
        f"  max    = {stats['max']:.4f}",
        f"  mean   = {stats['mean']:.4f}",
        f"  std    = {stats['std']:.4f}",
    ]
    if nan_count is not None:
        parts.append(f"  nan    = {nan_count}")
    return "\n".join(parts) + "\n"


def spearman_rho(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return float("nan")

    def ranks(vals: list[float]) -> list[float]:
        indexed = sorted(range(n), key=lambda i: vals[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and vals[indexed[j + 1]] == vals[indexed[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[indexed[k]] = avg
            i = j + 1
        return r

    rx, ry = ranks(xs), ranks(ys)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    dy = math.sqrt(sum((b - my) ** 2 for b in ry))
    if dx == 0 or dy == 0:
        return float("nan")
    return num / (dx * dy)


def summarise(rows: list[dict], source_desc: str) -> str:
    buf = io.StringIO()
    w = buf.write

    positions: dict[tuple, list[dict]] = {}
    for r in rows:
        positions.setdefault((r["game_id"], r["ply"]), []).append(r)

    games = sorted({r["game_id"] for r in rows})
    total_rows = len(rows)
    total_positions = len(positions)
    mean_legal = total_rows / total_positions if total_positions else 0.0

    w(f"Source: {source_desc}\n")
    w(f"Piece values (P,N,B,R,Q,K): "
      f"{PIECE_VALUES[chess.PAWN]}, {PIECE_VALUES[chess.KNIGHT]}, "
      f"{PIECE_VALUES[chess.BISHOP]}, {PIECE_VALUES[chess.ROOK]}, "
      f"{PIECE_VALUES[chess.QUEEN]}, {PIECE_VALUES[chess.KING]}\n")
    w("\n")
    w(f"Total games:         {len(games)}\n")
    w(f"Total rows:          {total_rows}\n")
    w(f"Total positions:     {total_positions}\n")
    w(f"Mean legal / pos:    {mean_legal:.2f}\n")
    w("\n")

    k_ann_vals = [r["kappa_annihilate"] for r in rows]
    k_thr_vals = [r["kappa_threat"] for r in rows]
    delta_vals = [r["delta"] for r in rows]
    sigma_vals_raw = [r["sigma"] for r in rows]
    sigma_nan = sum(1 for v in sigma_vals_raw if math.isnan(v))

    w(fmt_dist("kappa_annihilate", five_number(k_ann_vals))); w("\n")
    w(fmt_dist("kappa_threat", five_number(k_thr_vals))); w("\n")
    w(fmt_dist("delta", five_number(delta_vals))); w("\n")
    w(fmt_dist("sigma", five_number(sigma_vals_raw), nan_count=sigma_nan)); w("\n")

    ranks: list[int] = []
    sigma_of_played: list[float] = []
    is_not_top: list[float] = []
    for (gid, ply), group in positions.items():
        played_rows = [r for r in group if r["was_played"]]
        if len(played_rows) != 1:
            continue
        played = played_rows[0]
        played_delta = played["delta"]
        strictly_above = sum(1 for r in group if r["delta"] > played_delta)
        rank = strictly_above + 1
        ranks.append(rank)
        if not math.isnan(played["sigma"]):
            sigma_of_played.append(played["sigma"])
            is_not_top.append(0.0 if rank == 1 else 1.0)

    w(f"Rank of played move's delta (1 = highest delta; n positions = {len(ranks)}):\n")
    if ranks:
        rank_hist: dict[int, int] = {}
        for r in ranks:
            rank_hist[r] = rank_hist.get(r, 0) + 1
        top_n = sum(1 for r in ranks if r == 1)
        w(f"  played move is top-delta: {top_n}/{len(ranks)} "
          f"({100.0 * top_n / len(ranks):.1f}%)\n")
        w(f"  mean rank:   {sum(ranks)/len(ranks):.2f}\n")
        w(f"  median rank: {statistics.median(ranks):.1f}\n")
        w("  rank histogram (rank : count):\n")
        for r in sorted(rank_hist):
            bar = "#" * min(60, rank_hist[r])
            w(f"    {r:3d} : {rank_hist[r]:4d} {bar}\n")
    w("\n")

    w(f"Spearman rho ( sigma(played)  vs  played_is_NOT_top_delta ): "
      f"n={len(sigma_of_played)}\n")
    if len(sigma_of_played) >= 2:
        rho = spearman_rho(sigma_of_played, is_not_top)
        w(f"  rho = {rho:.4f}\n")
        w("  (positive rho => high-sigma positions are where played move "
          "is NOT the top-delta pick;\n"
          "   that would be evidence that sigma flags unreliable-gradient "
          "positions.)\n")
    else:
        w("  insufficient data.\n")

    return buf.getvalue()


# ─── CLI ──────────────────────────────────────────────────────────────────

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="analyze_delta_sigma.py",
        description="Collect per-move delta (kappa_annihilate - kappa_threat) "
                    "and sigma (std-dev of delta across fiber-neighbors) for "
                    "every legal move of every ply in a GM corpus. Writes one "
                    "CSV and one summary .txt.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              # Default: 2 reference GM games (chessgames_pair), fresh CSV.
              python analyze_delta_sigma.py

              # Sample 100 random valid games from a multi-game PGN and APPEND
              # to the existing chessgames_pair CSV:
              python analyze_delta_sigma.py \\
                  --pgn docs/chess-maths/dataset-place/lichess_db_broadcast_2022-11.pgn \\
                  --label chessgames_pair --sample 100 --seed 42 --append

              # Fresh CSV at a new label:
              python analyze_delta_sigma.py --pgn some.pgn --label lichess_sample_100 \\
                  --sample 100 --seed 42
        """),
    )
    parser.add_argument(
        "--pgn", type=Path, default=DEFAULT_PGN,
        help=f"Source PGN: either a single multi-game .pgn file or a "
             f"directory of .pgn files. Default: {DEFAULT_PGN}",
    )
    parser.add_argument(
        "--label", default=DEFAULT_LABEL,
        help=f"Label used for output directory and filenames. Default: "
             f"'{DEFAULT_LABEL}'.",
    )
    parser.add_argument(
        "--sample", type=int, default=None, metavar="N",
        help="Randomly sample N valid games from the source. Applies only "
             "to single-file multi-game PGN inputs. If N exceeds the number "
             "of valid games, all are used. Games are first filtered by "
             "--min-plies and python-chess parser errors (game.errors must "
             "be empty) before sampling.",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="RNG seed for --sample (for reproducibility). Default: 42.",
    )
    parser.add_argument(
        "--min-plies", type=int, default=20,
        help="Minimum ply count for a game to be considered valid. Games "
             "shorter than this, or with non-empty game.errors, are "
             "dropped before sampling. Default: 20.",
    )
    parser.add_argument(
        "--append", action="store_true",
        help="Append to the existing CSV if it exists. New rows whose "
             "game_id already appears in the target CSV are skipped "
             "(dedupe). The combined CSV is always re-sorted by "
             "(game_id, ply, move_uci), and the summary .txt is "
             "regenerated over the combined dataset. Without this flag, an "
             "existing CSV is silently overwritten (matching the "
             "deterministic first-run behavior).",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=None,
        help="Override output directory. Default: "
             "<repo>/docs/chess-maths/results/delta_sigma_<label>/.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    pgn_path = args.pgn
    if not pgn_path.exists():
        print(f"error: --pgn path not found: {pgn_path}", file=sys.stderr)
        return 2
    if args.sample is not None and pgn_path.is_dir():
        print("error: --sample requires a single multi-game .pgn file, not a directory.",
              file=sys.stderr)
        return 2

    out_dir = args.output_dir or (REPO_CHESS_MATHS / "results" / f"delta_sigma_{args.label}")
    csv_path = out_dir / f"delta_sigma_analysis_{args.label}.csv"
    summary_path = out_dir / f"delta_sigma_summary_{args.label}.txt"

    print(f"Scanning PGN source: {pgn_path}")
    accepted, counts = iter_source_games(pgn_path, args.min_plies)
    print(f"  total games read:       {counts['total']}")
    print(f"  kept (valid):           {counts['kept']}")
    print(f"  skipped (null):         {counts['skip_null']}")
    print(f"  skipped (parser errs):  {counts['skip_parser_errors']}")
    print(f"  skipped (< min-plies):  {counts['skip_short']}")

    if args.sample is not None:
        n_available = len(accepted)
        if args.sample >= n_available:
            print(f"  sample ({args.sample}) >= available ({n_available}); using all.")
        else:
            rng = random.Random(args.seed)
            # Sort first for deterministic selection given seed.
            accepted = sorted(accepted, key=lambda gg: gg[0])
            accepted = rng.sample(accepted, args.sample)
            accepted.sort(key=lambda gg: gg[0])
            print(f"  sampled:                {len(accepted)} (seed={args.seed})")

    if not accepted:
        print("error: no valid games to process.", file=sys.stderr)
        return 1

    print(f"Computing delta/sigma over {len(accepted)} game(s)...")
    new_rows = collect_rows_from_games(accepted)
    print(f"  new rows: {len(new_rows)}")

    append_mode = args.append and csv_path.exists()
    if append_mode:
        existing = load_csv_rows(csv_path)
        existing_ids = {r["game_id"] for r in existing}
        pre = len(new_rows)
        new_rows = [r for r in new_rows if r["game_id"] not in existing_ids]
        dropped = pre - len(new_rows)
        if dropped:
            print(f"  dropped {dropped} rows whose game_id was already in {csv_path.name}")
        all_rows = existing + new_rows
        print(f"  existing rows: {len(existing)} | appending: {len(new_rows)} "
              f"| combined: {len(all_rows)}")
    else:
        if args.append:
            print(f"  --append given but {csv_path} does not exist; writing fresh.")
        all_rows = new_rows

    write_csv(all_rows, csv_path)
    print(f"CSV written: {csv_path}")

    source_desc = (f"{pgn_path.name}"
                   if not append_mode
                   else f"appended {pgn_path.name} -> {csv_path.name}")
    summary = summarise(all_rows, source_desc)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(summary, encoding="utf-8")
    print(f"Summary written: {summary_path}")
    print()
    print(summary, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
