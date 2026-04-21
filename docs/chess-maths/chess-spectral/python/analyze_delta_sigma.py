"""analyze_delta_sigma — per-move Δ and σ collection with fiber-space kappa_position.

Computes kappa_position, a scalar measuring how the moving excitation
changes the position's fiber-channel coupling (F1, F2, F3, FA, FD —
dims 320:640 of the 640-dim encoding).

    kappa_position(board, move) =
        sign(||fiber_after||_2 - ||fiber_before||_2) * ||fiber_after - fiber_before||_2

The refined delta:

    delta_v2 = kappa_annihilate + kappa_position - kappa_threat

The CSV retains every column from v1 and appends:

    kappa_position, delta_v2, sigma_v2

where sigma_v2 is std-dev of delta_v2 across the same fiber-neighbor set
used for sigma (aggressor-type match OR destination match).

Do not modify piece values or v1 quantities here. This script preserves
them for side-by-side comparison.

Dependencies: numpy, python-chess, chess_spectral (local package).
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
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
try:
    from chess_spectral import encode_640, fen_to_pos, CHANNELS
except ImportError as e:
    sys.stderr.write(
        f"error: could not import spectral encoder from {HERE}\n"
        f"       ({e})\n"
        f"       Ensure docs/chess-maths/chess-spectral/python/chess_spectral/ "
        f"is importable and its deps (numpy, scipy) are installed.\n"
    )
    sys.exit(3)


# ─── Paths / defaults ──────────────────────────────────────────────────────

REPO_CHESS_MATHS = HERE.parent.parent
DEFAULT_CORPUS_DIR = REPO_CHESS_MATHS / "results" / "chessgames_pair_2026-04-15_N2"
DEFAULT_PGN = DEFAULT_CORPUS_DIR / "pgn"
DEFAULT_LABEL = "chessgames_pair"


# ─── Piece values (v1 parity; see analyze_delta_sigma.py docstring) ───────

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


# ─── Fiber channel slice ──────────────────────────────────────────────────

_FIBER_START = dict(CHANNELS)["F1"]   # 320
_FIBER_END = 640                       # through FD
assert _FIBER_START == 320, f"unexpected F1 offset {_FIBER_START}"
assert (_FIBER_END - _FIBER_START) == 320


# ─── CSV schema ────────────────────────────────────────────────────────────

CSV_COLUMNS = [
    "game_id", "ply", "fen", "side_to_move",
    "move_uci", "move_san",
    "is_capture", "aggressor_type", "target_type",
    "kappa_annihilate", "kappa_threat", "delta", "sigma",
    "kappa_position", "delta_v2", "sigma_v2",
    "was_played",
]


# ─── Per-move quantities (v1 functions preserved verbatim) ────────────────

def captured_piece(board: chess.Board, move: chess.Move) -> chess.Piece | None:
    if board.is_en_passant(move):
        ep_sq = move.to_square + (-8 if board.turn == chess.WHITE else 8)
        return board.piece_at(ep_sq)
    return board.piece_at(move.to_square)


def kappa_annihilate(aggressor_type: int, target_type: int | None) -> float:
    if target_type is None:
        return 0.0
    return PIECE_VALUES[target_type] - PIECE_VALUES[aggressor_type]


def kappa_threat(board: chess.Board, move: chess.Move, aggressor_type: int) -> float:
    self_value = PIECE_VALUES[aggressor_type]
    self_color = board.turn
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


# ─── Fiber-space gradient (new in v2) ──────────────────────────────────────

def kappa_position(fiber_before: np.ndarray, fiber_after: np.ndarray) -> float:
    """Scalar fiber-coupling change, signed by total fiber energy change."""
    delta = fiber_after - fiber_before
    magnitude = float(np.linalg.norm(delta))
    energy_before = float(np.linalg.norm(fiber_before))
    energy_after = float(np.linalg.norm(fiber_after))
    sign = 1.0 if energy_after >= energy_before else -1.0
    return sign * magnitude


# ─── Fiber-neighbor σ (v1 logic, applied to both delta and delta_v2) ──────

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


# ─── Main per-position row builder ─────────────────────────────────────────

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

    # One encoding for the current position (shared across all legal moves).
    enc_before = encode_640(fen_to_pos(fen))
    fiber_before = enc_before[_FIBER_START:_FIBER_END]

    meta: dict[chess.Move, dict] = {}
    for m in legal:
        aggressor = board.piece_at(m.from_square)
        aggressor_type = aggressor.piece_type
        target_piece = captured_piece(board, m)
        target_type = target_piece.piece_type if target_piece is not None else None

        k_ann = kappa_annihilate(aggressor_type, target_type)
        k_thr = kappa_threat(board, m, aggressor_type)

        post = board.copy(stack=False)
        post.push(m)
        enc_after = encode_640(fen_to_pos(post.fen()))
        fiber_after = enc_after[_FIBER_START:_FIBER_END]
        k_pos = kappa_position(fiber_before, fiber_after)

        delta_v1 = k_ann - k_thr
        delta_v2 = k_ann + k_pos - k_thr

        meta[m] = {
            "aggressor_type": aggressor_type,
            "target_type": target_type,
            "is_capture": target_type is not None,
            "san": board.san(m),
            "k_ann": k_ann,
            "k_thr": k_thr,
            "k_pos": k_pos,
            "delta": delta_v1,
            "delta_v2": delta_v2,
        }

    for m in legal:
        neighbors = fiber_neighbors(m, legal, meta)
        if len(neighbors) < 3:
            meta[m]["sigma"] = float("nan")
            meta[m]["sigma_v2"] = float("nan")
        else:
            meta[m]["sigma"] = statistics.stdev(meta[n]["delta"] for n in neighbors)
            meta[m]["sigma_v2"] = statistics.stdev(meta[n]["delta_v2"] for n in neighbors)

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
            "kappa_position": info["k_pos"],
            "delta_v2": info["delta_v2"],
            "sigma_v2": info["sigma_v2"],
            "was_played": (m == played),
        })
    return rows


# ─── Game validation & source iteration (copied from v1) ──────────────────

def mainline_ply_count(game: chess.pgn.Game) -> int:
    n = 0
    for _ in game.mainline_moves():
        n += 1
    return n


def is_valid_game(game, min_plies):
    if game is None:
        return False, "null game"
    if game.errors:
        return False, f"parser errors ({len(game.errors)})"
    plies = mainline_ply_count(game)
    if plies < min_plies:
        return False, f"too short ({plies} plies < {min_plies})"
    return True, ""


def iter_source_games(pgn_path: Path, min_plies: int):
    accepted: list[tuple[str, chess.pgn.Game]] = []
    counts = {"total": 0, "kept": 0,
              "skip_null": 0, "skip_parser_errors": 0, "skip_short": 0}

    def _consume(fh, prefix: str, multi_game: bool):
        idx = 0
        while True:
            try:
                game = chess.pgn.read_game(fh)
            except Exception:
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
                start = len(accepted)
                _consume(fh, pgn_file.stem, multi_game=True)
                if len(accepted) - start == 1:
                    gid_old, game = accepted[-1]
                    accepted[-1] = (pgn_file.stem, game)
    else:
        with pgn_path.open("r", encoding="utf-8") as fh:
            _consume(fh, pgn_path.stem, multi_game=True)
    return accepted, counts


def collect_rows_from_games(
    games: list[tuple[str, chess.pgn.Game]],
    sample_positions: int | None,
    seed: int,
) -> list[dict]:
    # First: enumerate all positions (board, played, game_id, ply).
    positions: list[tuple] = []
    for game_id, game in games:
        board = game.board()
        for ply, played in enumerate(game.mainline_moves(), start=1):
            if not any(True for _ in board.legal_moves):
                break
            positions.append((board.copy(stack=False), played, game_id, ply))
            board.push(played)

    if sample_positions is not None and sample_positions < len(positions):
        rng = random.Random(seed)
        positions = sorted(positions, key=lambda t: (t[2], t[3]))
        positions = rng.sample(positions, sample_positions)
        positions.sort(key=lambda t: (t[2], t[3]))
        print(f"  sampled to {len(positions)} positions (seed={seed})")

    rows: list[dict] = []
    n_done = 0
    t_report = 0
    import time as _t
    t0 = _t.perf_counter()
    for board, played, game_id, ply in positions:
        rows.extend(compute_position_rows(board, played, game_id, ply))
        n_done += 1
        if n_done - t_report >= 500:
            elapsed = _t.perf_counter() - t0
            rate = n_done / elapsed if elapsed > 0 else 0.0
            remaining = (len(positions) - n_done) / rate if rate > 0 else float("nan")
            print(f"  [{n_done}/{len(positions)}] positions done  "
                  f"({rate:.1f}/s, ~{remaining:.0f}s remaining)")
            t_report = n_done
    return rows


# ─── CSV I/O ───────────────────────────────────────────────────────────────

def _fnum(x):
    return "NaN" if (isinstance(x, float) and math.isnan(x)) else f"{x:.6f}"


def rows_to_csv_dict(r: dict) -> dict:
    out = dict(r)
    out["is_capture"] = "True" if r["is_capture"] else "False"
    out["was_played"] = "True" if r["was_played"] else "False"
    for c in ("kappa_annihilate", "kappa_threat", "delta",
              "kappa_position", "delta_v2"):
        out[c] = f"{r[c]:.6f}"
    out["sigma"] = _fnum(r["sigma"])
    out["sigma_v2"] = _fnum(r["sigma_v2"])
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
                "kappa_position": float(r["kappa_position"]),
                "delta_v2": float(r["delta_v2"]),
                "sigma_v2": float("nan") if r["sigma_v2"] == "NaN" else float(r["sigma_v2"]),
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
        return s[lo] if lo == hi else s[lo] + (s[hi] - s[lo]) * (idx - lo)
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
        idx = sorted(range(n), key=lambda i: vals[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and vals[idx[j + 1]] == vals[idx[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[idx[k]] = avg
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
      f"{PIECE_VALUES[chess.QUEEN]}, {PIECE_VALUES[chess.KING]}\n\n")
    w(f"Total games:         {len(games)}\n")
    w(f"Total rows:          {total_rows}\n")
    w(f"Total positions:     {total_positions}\n")
    w(f"Mean legal / pos:    {mean_legal:.2f}\n\n")

    for col, label in [
        ("kappa_annihilate", "kappa_annihilate"),
        ("kappa_threat",     "kappa_threat"),
        ("kappa_position",   "kappa_position (new)"),
        ("delta",            "delta (v1)"),
        ("delta_v2",         "delta_v2 (v1 + kappa_position)"),
    ]:
        vals = [r[col] for r in rows]
        w(fmt_dist(label, five_number(vals))); w("\n")

    sigma_raw = [r["sigma"] for r in rows]
    sigma_nan = sum(1 for v in sigma_raw if math.isnan(v))
    w(fmt_dist("sigma (v1)", five_number(sigma_raw), nan_count=sigma_nan)); w("\n")
    sigma_v2_raw = [r["sigma_v2"] for r in rows]
    sigma_v2_nan = sum(1 for v in sigma_v2_raw if math.isnan(v))
    w(fmt_dist("sigma_v2 (new)", five_number(sigma_v2_raw), nan_count=sigma_v2_nan)); w("\n")

    # kappa_position by capture vs non-capture
    k_pos_capture = [r["kappa_position"] for r in rows if r["is_capture"]]
    k_pos_quiet   = [r["kappa_position"] for r in rows if not r["is_capture"]]
    w("kappa_position by move type:\n")
    if k_pos_capture:
        w(f"  captures (n={len(k_pos_capture)}): "
          f"mean={statistics.mean(k_pos_capture):+.4f}, "
          f"std={statistics.pstdev(k_pos_capture):.4f}\n")
    if k_pos_quiet:
        w(f"  quiets   (n={len(k_pos_quiet)}): "
          f"mean={statistics.mean(k_pos_quiet):+.4f}, "
          f"std={statistics.pstdev(k_pos_quiet):.4f}\n")
    w("\n")

    # Per-position ranks under each formula.
    def rank_of(target, group, key):
        target_val = target[key]
        return sum(1 for r in group if r[key] > target_val) + 1

    rank_delta: list[int] = []
    rank_delta_v2: list[int] = []
    sigma_of_played: list[float] = []
    sigma_v2_of_played: list[float] = []
    played_not_top_v1: list[float] = []
    played_not_top_v2: list[float] = []
    top_switched = 0       # positions where top move changed between v1 and v2
    promoted_to_top = 0    # positions where played move was not top-v1 but is top-v2
    demoted_from_top = 0   # played was top-v1 but not top-v2

    for (gid, ply), group in positions.items():
        played_rows = [r for r in group if r["was_played"]]
        if len(played_rows) != 1:
            continue
        played = played_rows[0]

        r1 = rank_of(played, group, "delta")
        r2 = rank_of(played, group, "delta_v2")
        rank_delta.append(r1)
        rank_delta_v2.append(r2)

        if not math.isnan(played["sigma"]):
            sigma_of_played.append(played["sigma"])
            played_not_top_v1.append(0.0 if r1 == 1 else 1.0)
        if not math.isnan(played["sigma_v2"]):
            sigma_v2_of_played.append(played["sigma_v2"])
            played_not_top_v2.append(0.0 if r2 == 1 else 1.0)

        # Top-move switches between formulas (regardless of played move)
        top_v1 = max(r["delta"] for r in group)
        top_v2 = max(r["delta_v2"] for r in group)
        top_v1_set = {r["move_uci"] for r in group if r["delta"] == top_v1}
        top_v2_set = {r["move_uci"] for r in group if r["delta_v2"] == top_v2}
        if top_v1_set.isdisjoint(top_v2_set):
            top_switched += 1
        if r1 != 1 and r2 == 1:
            promoted_to_top += 1
        if r1 == 1 and r2 != 1:
            demoted_from_top += 1

    def top_count(ranks):
        return sum(1 for r in ranks if r == 1)

    w(f"Rank of played move (n positions = {len(rank_delta)}):\n")
    if rank_delta:
        t1 = top_count(rank_delta)
        t2 = top_count(rank_delta_v2)
        w(f"  under delta      (v1): {t1}/{len(rank_delta)} "
          f"({100.0*t1/len(rank_delta):.1f}%)   mean rank {sum(rank_delta)/len(rank_delta):.2f}\n")
        w(f"  under delta_v2   (v2): {t2}/{len(rank_delta_v2)} "
          f"({100.0*t2/len(rank_delta_v2):.1f}%)   mean rank {sum(rank_delta_v2)/len(rank_delta_v2):.2f}\n")
        w(f"  top move DISJOINT across v1/v2 (any played): {top_switched}/{len(positions)} "
          f"({100.0*top_switched/len(positions):.1f}%)\n")
        w(f"  played move NOT top-v1 but IS top-v2 (v2 promotes): {promoted_to_top}\n")
        w(f"  played move IS  top-v1 but NOT top-v2 (v2 demotes): {demoted_from_top}\n")
    w("\n")

    # Spearman on per-row scalars (everything lines up).
    def pair(a, b):
        return [(r[a], r[b]) for r in rows
                if not (math.isnan(r.get(a, 0.0)) or math.isnan(r.get(b, 0.0)))]

    pairs = pair("delta", "delta_v2")
    rho_d_d2 = spearman_rho([p[0] for p in pairs], [p[1] for p in pairs])
    w(f"Spearman rho (delta vs delta_v2): {rho_d_d2:.4f} "
      f"(n={len(pairs)})\n")
    w("  (rho close to 1 => v2 is a small perturbation; rho << 1 => substantial redirection)\n\n")

    if sigma_of_played:
        rho = spearman_rho(sigma_of_played, played_not_top_v1)
        w(f"Spearman rho ( sigma(played)    vs played_is_NOT_top(v1) ): "
          f"rho={rho:.4f}  n={len(sigma_of_played)}\n")
    if sigma_v2_of_played:
        rho = spearman_rho(sigma_v2_of_played, played_not_top_v2)
        w(f"Spearman rho ( sigma_v2(played) vs played_is_NOT_top(v2) ): "
          f"rho={rho:.4f}  n={len(sigma_v2_of_played)}\n")

    return buf.getvalue()


# ─── CLI ──────────────────────────────────────────────────────────────────

def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="analyze_delta_sigma.py",
        description="Phase 1: compute per-move kappa_position (fiber-space "
                    "gradient from the 640-dim spectral encoding) and the "
                    "refined delta_v2 = kappa_annihilate + kappa_position - "
                    "kappa_threat. Adds three new columns (kappa_position, "
                    "delta_v2, sigma_v2) to the v1 CSV schema.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              # Full run (2 reference games, all positions, fresh CSV)
              python analyze_delta_sigma.py

              # Sample 1000 positions uniformly at random (faster iteration)
              python analyze_delta_sigma.py --sample-positions 1000 --seed 42

              # Sample 100 games from lichess and append to existing CSV
              python analyze_delta_sigma.py \\
                  --pgn docs/chess-maths/dataset-place/lichess_db_broadcast_2022-11.pgn \\
                  --label chessgames_pair --sample 100 --seed 42 --append
        """),
    )
    parser.add_argument("--pgn", type=Path, default=DEFAULT_PGN,
        help=f"Source PGN file or directory. Default: {DEFAULT_PGN}")
    parser.add_argument("--label", default=DEFAULT_LABEL,
        help=f"Output label. Default '{DEFAULT_LABEL}'.")
    parser.add_argument("--sample", type=int, default=None, metavar="N",
        help="Randomly sample N valid GAMES from a single multi-game PGN.")
    parser.add_argument("--sample-positions", type=int, default=None, metavar="N",
        help="After game selection, uniformly sample N POSITIONS. Useful for "
             "fast iteration when the fiber encoder is the bottleneck.")
    parser.add_argument("--seed", type=int, default=42,
        help="RNG seed. Default 42.")
    parser.add_argument("--min-plies", type=int, default=20,
        help="Minimum plies for a game to be considered valid. Default 20.")
    parser.add_argument("--append", action="store_true",
        help="Append to existing v2 CSV; dedupe by game_id; re-sort; "
             "regenerate summary.")
    parser.add_argument("--output-dir", type=Path, default=None,
        help="Override output directory. Default: "
             "<repo>/docs/chess-maths/results/delta_sigma_<label>/.")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    pgn_path = args.pgn
    if not pgn_path.exists():
        print(f"error: --pgn path not found: {pgn_path}", file=sys.stderr)
        return 2
    if args.sample is not None and pgn_path.is_dir():
        print("error: --sample requires a single multi-game .pgn file.", file=sys.stderr)
        return 2

    out_dir = args.output_dir or (REPO_CHESS_MATHS / "results" / f"delta_sigma_{args.label}")
    csv_path = out_dir / f"delta_sigma_analysis_v2_{args.label}.csv"
    summary_path = out_dir / f"delta_sigma_summary_v2_{args.label}.txt"

    print(f"Scanning PGN source: {pgn_path}")
    accepted, counts = iter_source_games(pgn_path, args.min_plies)
    print(f"  total: {counts['total']}  kept: {counts['kept']}  "
          f"parse-errs: {counts['skip_parser_errors']}  "
          f"short: {counts['skip_short']}  null: {counts['skip_null']}")

    if args.sample is not None:
        n_avail = len(accepted)
        if args.sample >= n_avail:
            print(f"  sample ({args.sample}) >= available ({n_avail}); using all.")
        else:
            rng = random.Random(args.seed)
            accepted = sorted(accepted, key=lambda gg: gg[0])
            accepted = rng.sample(accepted, args.sample)
            accepted.sort(key=lambda gg: gg[0])
            print(f"  sampled games: {len(accepted)} (seed={args.seed})")

    if not accepted:
        print("error: no valid games to process.", file=sys.stderr)
        return 1

    print(f"Computing delta/sigma/kappa_position over {len(accepted)} game(s)...")
    new_rows = collect_rows_from_games(accepted, args.sample_positions, args.seed)
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
        print(f"  existing: {len(existing)} | appending: {len(new_rows)} | "
              f"combined: {len(all_rows)}")
    else:
        if args.append:
            print(f"  --append given but {csv_path} does not exist; writing fresh.")
        all_rows = new_rows

    write_csv(all_rows, csv_path)
    print(f"CSV written: {csv_path}")

    source_desc = (pgn_path.name if not append_mode
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
