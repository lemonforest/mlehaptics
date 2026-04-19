"""analyze_stockfish_correlation — Phase 2 of the Δ/σ pipeline.

Sample positions from the v2 Δ/σ CSV produced by analyze_delta_sigma_v2.py,
evaluate every legal move with Stockfish, and compute Spearman ρ between the
Stockfish scalar and each of:

    κ_annihilate, κ_position, κ_threat, Δ (v1), Δ_v2

Also reports top-move-match rate per quantity (fraction of positions where that
quantity's argmax-over-legal-moves matches Stockfish's argmax).

Stockfish binary resolution (first match wins):
  1. --stockfish-path <file>
  2. $STOCKFISH_PATH environment variable
  3. Repo-local default: <repo>/docs/chess-maths/stockfish/
                         stockfish-windows-x86-64-avx2.exe
  4. shutil.which("stockfish") (system-wide install)

If none found, the script halts with an install message pointing at
https://stockfishchess.org/download/. No auto-install.

Python dependencies (installed once per environment):

    python -m pip install --user python-chess numpy scipy stockfish

`numpy` and `scipy` are imported by the chess_spectral encoder sibling; they
are NOT used directly here. `stockfish` is the UCI wrapper
(https://pypi.org/project/stockfish/).

Run `python analyze_stockfish_correlation.py --help` for the full CLI.
"""

from __future__ import annotations

import argparse
import csv
import io
import math
import os
import random
import shutil
import statistics
import subprocess
import sys
import textwrap
from pathlib import Path


# ─── Paths / defaults ──────────────────────────────────────────────────────

HERE = Path(__file__).resolve().parent
REPO_CHESS_MATHS = HERE.parents[1]  # docs/chess-maths
DEFAULT_V2_CSV = (REPO_CHESS_MATHS / "results" / "delta_sigma_chessgames_pair"
                  / "delta_sigma_analysis_v2_chessgames_pair.csv")
DEFAULT_STOCKFISH = (REPO_CHESS_MATHS / "stockfish"
                     / "stockfish-windows-x86-64-avx2.exe")
DEFAULT_OUTPUT_DIR = REPO_CHESS_MATHS / "results" / "stockfish_correlation"


# ─── Stockfish binary resolution ───────────────────────────────────────────

def resolve_stockfish(explicit: str | None) -> Path:
    """Return a path to a Stockfish binary, or halt with an install message.

    Resolution order: --stockfish-path > $STOCKFISH_PATH > repo-local default
    > shutil.which('stockfish').
    """
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    env = os.environ.get("STOCKFISH_PATH")
    if env:
        candidates.append(Path(env))
    candidates.append(DEFAULT_STOCKFISH)
    which = shutil.which("stockfish")
    if which:
        candidates.append(Path(which))

    for p in candidates:
        if p.is_file():
            return p

    sys.stderr.write(textwrap.dedent(f"""
        Stockfish binary not found. Expected at
          {DEFAULT_STOCKFISH}
        or pass --stockfish-path <file>, or set $STOCKFISH_PATH, or install
        system-wide (https://stockfishchess.org/download/). Halting Phase 2.
        """).lstrip())
    sys.exit(2)


def stockfish_uci_banner(binary: Path) -> str:
    """Send `uci\\nquit\\n` to the binary, return the `id name ...` line."""
    proc = subprocess.run(
        [str(binary)],
        input="uci\nquit\n",
        capture_output=True,
        text=True,
        timeout=10,
    )
    for line in proc.stdout.splitlines():
        if line.startswith("id name"):
            return line[len("id name "):].strip()
    return "unknown"


# ─── Imports that can fail loudly ──────────────────────────────────────────

def _require_imports():
    missing: list[str] = []
    try:
        import chess  # noqa: F401
        import chess.pgn  # noqa: F401
    except ImportError:
        missing.append("python-chess")
    try:
        from stockfish import Stockfish  # noqa: F401
    except ImportError:
        missing.append("stockfish")
    if missing:
        sys.stderr.write(
            "Missing Python packages: " + ", ".join(missing) + "\n"
            "Install with:\n"
            "  python -m pip install --user python-chess numpy scipy stockfish\n"
        )
        sys.exit(2)


# ─── v2 CSV loader ─────────────────────────────────────────────────────────

# These are the v2 columns we read; others in the file are ignored here.
_CSV_FLOAT_COLS = ("kappa_annihilate", "kappa_threat", "delta",
                   "kappa_position", "delta_v2")


def load_v2_rows(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            out = {
                "game_id": r["game_id"],
                "ply": int(r["ply"]),
                "fen": r["fen"],
                "side_to_move": r["side_to_move"],
                "move_uci": r["move_uci"],
                "move_san": r["move_san"],
                "was_played": r["was_played"] == "True",
            }
            for c in _CSV_FLOAT_COLS:
                out[c] = float(r[c])
            rows.append(out)
    return rows


def group_by_position(rows: list[dict]) -> dict[tuple[str, int], list[dict]]:
    out: dict[tuple[str, int], list[dict]] = {}
    for r in rows:
        out.setdefault((r["game_id"], r["ply"]), []).append(r)
    return out


# ─── Stockfish evaluation ──────────────────────────────────────────────────

def stockfish_scalar(ev: dict) -> float:
    """Map a Stockfish evaluation dict to a signed scalar.

    The python-stockfish wrapper returns
        {"type": "cp", "value": <centipawns>}   for normal positions
        {"type": "mate", "value": <plies>}      for forced mates
    Convention: scalar is always from the side-to-move's perspective, positive =
    good for side-to-move. For mates we compress into a large range that keeps
    mate-in-1 > mate-in-10 > … > mate-against-1 > …
    """
    v = ev.get("value")
    if v is None:
        return 0.0
    if ev.get("type") == "mate":
        sign = 1.0 if v >= 0 else -1.0
        # mate-in-1  -> +9990, mate-in-100 -> +9000, mate-against-1 -> -9990
        return sign * (10000 - abs(v) * 10)
    return float(v)


def eval_position_moves(sf, board, moves_uci: list[str]) -> list[dict]:
    """For each UCI in moves_uci, push→eval→pop; return per-move scalars.

    `sf` is a stockfish.Stockfish instance already pointed at the pre-move
    position. `board` is a python-chess Board at the same position. Side-to-
    move flips after each push, so we negate scalar to keep the score from the
    ORIGINAL side-to-move's POV (higher = better move for the mover we're
    ranking for).
    """
    import chess
    results: list[dict] = []
    for uci in moves_uci:
        mv = chess.Move.from_uci(uci)
        board.push(mv)
        sf.set_fen_position(board.fen())
        ev = sf.get_evaluation()
        cp = ev.get("value", 0) if ev.get("type") == "cp" else None
        mate = ev.get("value", 0) if ev.get("type") == "mate" else None
        scalar_after = stockfish_scalar(ev)
        # After push, side-to-move is the OPPONENT of the move's maker, so flip.
        scalar_for_mover = -scalar_after
        results.append({
            "move_uci": uci,
            "stockfish_cp": cp if cp is not None else "",
            "stockfish_mate": mate if mate is not None else "",
            "stockfish_scalar": scalar_for_mover,
        })
        board.pop()
    return results


# ─── Statistics ────────────────────────────────────────────────────────────

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


def top_move_match_rate(per_pos: list[list[dict]], quantity_key: str) -> float:
    """Fraction of positions where argmax of quantity matches argmax of stockfish_scalar."""
    if not per_pos:
        return float("nan")
    hits = 0
    for moves in per_pos:
        if len(moves) < 2:
            hits += 1
            continue
        sf_top = max(moves, key=lambda m: m["stockfish_scalar"])["move_uci"]
        q_top = max(moves, key=lambda m: m[quantity_key])["move_uci"]
        if sf_top == q_top:
            hits += 1
    return hits / len(per_pos)


# ─── Main pipeline ─────────────────────────────────────────────────────────

def main():
    _require_imports()
    # Now safe to import.
    import chess
    from stockfish import Stockfish

    ap = argparse.ArgumentParser(
        description=(
            "Phase 2: sample positions from the v2 delta/sigma CSV, evaluate "
            "every legal move with Stockfish, and compute Spearman rho between "
            "stockfish_scalar and each of (kappa_annihilate, kappa_position, "
            "kappa_threat, delta, delta_v2). Also reports top-move-match rate "
            "per quantity vs Stockfish's argmax."
        ),
        epilog=textwrap.dedent("""\
            Examples:
              # Defaults: 200 positions, depth 12, uses in-repo Stockfish 18.
              python analyze_stockfish_correlation.py

              # Smoke test: 10 positions, shallow depth.
              python analyze_stockfish_correlation.py --sample 10 --depth 6

              # Full correlation on a different CSV.
              python analyze_stockfish_correlation.py \\
                  --csv path/to/other_v2.csv --sample 500 --depth 15
            """),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--csv", type=Path, default=DEFAULT_V2_CSV,
                    help=f"Input v2 CSV. Default: {DEFAULT_V2_CSV}")
    ap.add_argument("--stockfish-path", type=str, default=None,
                    help=("Override Stockfish binary. Default resolution: "
                          "--stockfish-path > $STOCKFISH_PATH > "
                          f"{DEFAULT_STOCKFISH} > shutil.which('stockfish')."))
    ap.add_argument("--sample", type=int, default=200,
                    help="Positions to evaluate (was_played=True rows). Default 200.")
    ap.add_argument("--depth", type=int, default=12,
                    help="Stockfish search depth. Default 12.")
    ap.add_argument("--threads", type=int, default=1,
                    help="Stockfish UCI 'Threads' option. Default 1.")
    ap.add_argument("--hash-mb", type=int, default=64,
                    help="Stockfish UCI 'Hash' option in MiB. Default 64.")
    ap.add_argument("--seed", type=int, default=42,
                    help="RNG seed for position sampling. Default 42.")
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
                    help=f"Output directory. Default: {DEFAULT_OUTPUT_DIR}")
    args = ap.parse_args()

    binary = resolve_stockfish(args.stockfish_path)
    version = stockfish_uci_banner(binary)
    print(f"Stockfish binary: {binary}")
    print(f"Stockfish version: {version}")

    if not args.csv.exists():
        sys.exit(f"v2 CSV not found: {args.csv}\n"
                 f"Run analyze_delta_sigma_v2.py first.")

    print(f"Loading v2 CSV: {args.csv}")
    rows = load_v2_rows(args.csv)
    print(f"  loaded {len(rows)} rows")

    grouped = group_by_position(rows)
    position_keys = sorted(grouped.keys())
    print(f"  {len(position_keys)} distinct positions")

    rng = random.Random(args.seed)
    k = min(args.sample, len(position_keys))
    sample_keys = sorted(rng.sample(position_keys, k))
    print(f"Sampling {k} positions with seed {args.seed}.")

    sf = Stockfish(path=str(binary), depth=args.depth,
                   parameters={"Threads": args.threads, "Hash": args.hash_mb})

    args.output_dir.mkdir(parents=True, exist_ok=True)
    eval_csv_path = args.output_dir / "stockfish_evaluations_v2.csv"
    summary_path = args.output_dir / "stockfish_correlation_summary.txt"

    eval_rows: list[dict] = []
    per_pos_moves: list[list[dict]] = []

    for i, key in enumerate(sample_keys, 1):
        game_id, ply = key
        pos_rows = grouped[key]
        # All rows share the same FEN — take the first.
        fen = pos_rows[0]["fen"]
        board = chess.Board(fen)
        legal_uci = {m.uci() for m in board.legal_moves}

        # Only evaluate moves actually present as rows in the v2 CSV for
        # this position (should equal legal_uci, but we trust the CSV).
        moves_to_eval = [r["move_uci"] for r in pos_rows
                         if r["move_uci"] in legal_uci]
        if len(moves_to_eval) != len(pos_rows):
            print(f"  WARN: position {game_id} ply={ply}: "
                  f"{len(pos_rows)} rows but {len(moves_to_eval)} match legal moves")

        scalars = eval_position_moves(sf, board, moves_to_eval)
        by_uci = {s["move_uci"]: s for s in scalars}

        pos_moves: list[dict] = []
        for r in pos_rows:
            if r["move_uci"] not in by_uci:
                continue
            s = by_uci[r["move_uci"]]
            out = {
                "game_id": game_id,
                "ply": ply,
                "move_uci": r["move_uci"],
                "stockfish_cp": s["stockfish_cp"],
                "stockfish_mate": s["stockfish_mate"],
                "stockfish_scalar": s["stockfish_scalar"],
                "kappa_annihilate": r["kappa_annihilate"],
                "kappa_position": r["kappa_position"],
                "kappa_threat": r["kappa_threat"],
                "delta": r["delta"],
                "delta_v2": r["delta_v2"],
            }
            eval_rows.append(out)
            pos_moves.append(out)
        per_pos_moves.append(pos_moves)

        if i % 10 == 0 or i == k:
            print(f"  {i}/{k} positions ({len(eval_rows)} rows so far)")

    # ─── Write per-move CSV ───
    eval_rows_sorted = sorted(eval_rows,
                              key=lambda r: (r["game_id"], r["ply"], r["move_uci"]))
    with eval_csv_path.open("w", encoding="utf-8", newline="") as fh:
        cols = ["game_id", "ply", "move_uci",
                "stockfish_cp", "stockfish_mate", "stockfish_scalar",
                "kappa_annihilate", "kappa_position", "kappa_threat",
                "delta", "delta_v2"]
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in eval_rows_sorted:
            w.writerow({
                "game_id": r["game_id"],
                "ply": r["ply"],
                "move_uci": r["move_uci"],
                "stockfish_cp": r["stockfish_cp"],
                "stockfish_mate": r["stockfish_mate"],
                "stockfish_scalar": f"{r['stockfish_scalar']:.6f}",
                "kappa_annihilate": f"{r['kappa_annihilate']:.6f}",
                "kappa_position": f"{r['kappa_position']:.6f}",
                "kappa_threat": f"{r['kappa_threat']:.6f}",
                "delta": f"{r['delta']:.6f}",
                "delta_v2": f"{r['delta_v2']:.6f}",
            })
    print(f"Wrote {len(eval_rows_sorted)} rows -> {eval_csv_path}")

    # ─── Summary ───
    sf_scalars = [r["stockfish_scalar"] for r in eval_rows_sorted]
    pairs = [
        ("kappa_annihilate", [r["kappa_annihilate"] for r in eval_rows_sorted]),
        ("kappa_position",   [r["kappa_position"]   for r in eval_rows_sorted]),
        ("kappa_threat",     [r["kappa_threat"]     for r in eval_rows_sorted]),
        ("delta (v1)",       [r["delta"]            for r in eval_rows_sorted]),
        ("delta_v2",         [r["delta_v2"]         for r in eval_rows_sorted]),
    ]

    buf = io.StringIO()
    w = buf.write
    w("Stockfish correlation summary\n")
    w(f"  binary         : {binary}\n")
    w(f"  version        : {version}\n")
    w(f"  v2 csv         : {args.csv}\n")
    w(f"  sample size    : {k} positions (seed={args.seed})\n")
    w(f"  depth / threads: {args.depth} / {args.threads}\n")
    w(f"  hash MiB       : {args.hash_mb}\n")
    w(f"  per-move rows  : {len(eval_rows_sorted)}\n\n")

    w("stockfish_scalar distribution:\n")
    st = five_number(sf_scalars)
    if st.get("n", 0):
        w(f"  n={st['n']}  min={st['min']:.1f}  q1={st['q1']:.1f}  "
          f"median={st['median']:.1f}  q3={st['q3']:.1f}  max={st['max']:.1f}\n"
          f"  mean={st['mean']:.2f}  std={st['std']:.2f}\n\n")
    else:
        w("  (empty)\n\n")

    w("Spearman rho(stockfish_scalar, X):\n")
    for name, xs in pairs:
        rho = spearman_rho(sf_scalars, xs)
        w(f"  {name:<17}: rho={rho:+.4f}\n")

    w("\nTop-move match rate (argmax vs Stockfish argmax):\n")
    for name, _ in pairs:
        key = {
            "kappa_annihilate": "kappa_annihilate",
            "kappa_position":   "kappa_position",
            "kappa_threat":     "kappa_threat",
            "delta (v1)":       "delta",
            "delta_v2":         "delta_v2",
        }[name]
        rate = top_move_match_rate(per_pos_moves, key)
        w(f"  {name:<17}: {rate*100:.1f}%\n")

    sf_top_pct = top_move_match_rate(per_pos_moves, "stockfish_scalar")
    w(f"\n  (sanity) stockfish_scalar self-match : {sf_top_pct*100:.1f}% "
      "(should be 100.0)\n")

    text = buf.getvalue()
    summary_path.write_text(text, encoding="utf-8")
    print()
    print(text, end="")
    print(f"Summary -> {summary_path}")


if __name__ == "__main__":
    main()
