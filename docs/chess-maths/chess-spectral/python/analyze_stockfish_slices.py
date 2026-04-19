"""analyze_stockfish_slices — slice-level reanalysis of the Phase 2 CSV.

Reads an existing stockfish_evaluations_v2.csv (produced by
analyze_stockfish_correlation.py) and the v2 delta/sigma CSV, joins them on
(game_id, ply, move_uci), and computes Spearman rho between stockfish_scalar
and each of (kappa_annihilate, kappa_position, kappa_threat, delta, delta_v2)
broken down by slice:

  * Ply range:                early (<=15), middle (16-35), endgame (>=36)
  * Capture vs non-capture
  * Material balance:         |white - black| <= 1 pawn-unit (balanced) vs not
  * Aggressor piece type:     one slice per P/N/B/R/Q/K
  * |kappa_position| bucket:  low (<10), medium (10-100), high (>100)

Also reports played-move rank distribution per slice under each of the five
signals: for each position in the slice, rank = 1 + (# of moves at that
position with a strictly higher signal value than the played move).

No new Stockfish evaluations are run — this is pure reanalysis.

Run `python analyze_stockfish_slices.py --help` for CLI options.
"""

from __future__ import annotations

import argparse
import csv
import io
import math
import statistics
import sys
import textwrap
from pathlib import Path


# ─── Paths / defaults ──────────────────────────────────────────────────────

HERE = Path(__file__).resolve().parent
REPO_CHESS_MATHS = HERE.parents[1]  # docs/chess-maths
DEFAULT_V2_CSV = (REPO_CHESS_MATHS / "results" / "delta_sigma_chessgames_pair"
                  / "delta_sigma_analysis_v2_chessgames_pair.csv")
DEFAULT_EVAL_CSV = (REPO_CHESS_MATHS / "results" / "stockfish_correlation"
                    / "stockfish_evaluations_v2.csv")
DEFAULT_OUTPUT = (REPO_CHESS_MATHS / "results" / "delta_sigma_chessgames_pair"
                  / "stockfish_slice_analysis.txt")

# Piece values for material-balance calculation.
# Same as the v2/v1 scripts: notebook §9c (P overridden to 0.84 vs tables.py).
PIECE_VALUE = {
    "P": 0.84, "N": 2.0, "B": 3.4, "R": 5.4, "Q": 8.8,  # K excluded from material
}
SIGNAL_KEYS = ("kappa_annihilate", "kappa_position", "kappa_threat",
               "delta", "delta_v2")
NOTABLE_RHO = 0.30       # |rho| above this flagged
MIN_N_FOR_TRUST = 100    # slices smaller than this get a warning


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


# ─── FEN helpers ───────────────────────────────────────────────────────────

def material_balance(fen: str) -> float:
    """Return white_material - black_material (pawn-unit sum, K excluded)."""
    placement = fen.split()[0]
    total = 0.0
    for ch in placement:
        if ch.isalpha():
            up = ch.upper()
            v = PIECE_VALUE.get(up)
            if v is None:
                continue
            total += v if ch.isupper() else -v
    return total


# ─── Loaders ───────────────────────────────────────────────────────────────

def load_eval_csv(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rows.append({
                "game_id": r["game_id"],
                "ply": int(r["ply"]),
                "move_uci": r["move_uci"],
                "stockfish_scalar": float(r["stockfish_scalar"]),
                "kappa_annihilate": float(r["kappa_annihilate"]),
                "kappa_position":   float(r["kappa_position"]),
                "kappa_threat":     float(r["kappa_threat"]),
                "delta":            float(r["delta"]),
                "delta_v2":         float(r["delta_v2"]),
            })
    return rows


def load_v2_index(path: Path, want_keys: set[tuple[str, int, str]]
                  ) -> tuple[dict, dict]:
    """Read only rows whose (game_id, ply, move_uci) appears in want_keys.

    Returns:
      move_attrs: {(game_id, ply, move_uci): {"is_capture", "aggressor_type", "was_played"}}
      fens:       {(game_id, ply): fen}
    """
    move_attrs: dict = {}
    fens: dict = {}
    want_pos = {(g, p) for (g, p, _) in want_keys}
    with path.open("r", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            gid = r["game_id"]
            ply = int(r["ply"])
            if (gid, ply) not in want_pos:
                continue
            key = (gid, ply, r["move_uci"])
            if key in want_keys:
                move_attrs[key] = {
                    "is_capture": r["is_capture"] == "True",
                    "aggressor_type": r["aggressor_type"],
                    "was_played": r["was_played"] == "True",
                }
            fens.setdefault((gid, ply), r["fen"])
    return move_attrs, fens


# ─── Enrichment ────────────────────────────────────────────────────────────

def enrich(eval_rows: list[dict], move_attrs: dict, fens: dict) -> list[dict]:
    """Attach is_capture / aggressor_type / was_played / material_balance / side."""
    bal_cache: dict = {}
    out: list[dict] = []
    missing_attrs = 0
    for r in eval_rows:
        key = (r["game_id"], r["ply"], r["move_uci"])
        attrs = move_attrs.get(key)
        if attrs is None:
            missing_attrs += 1
            continue
        pos_key = (r["game_id"], r["ply"])
        if pos_key not in bal_cache:
            fen = fens[pos_key]
            bal_cache[pos_key] = (material_balance(fen), fen.split()[1])  # side
        bal, side = bal_cache[pos_key]
        r2 = dict(r)
        r2.update(attrs)
        r2["material_balance"] = bal
        r2["side_to_move"] = side
        out.append(r2)
    if missing_attrs:
        print(f"WARN: {missing_attrs} eval rows had no v2 match, skipped")
    return out


# ─── Slice definitions ─────────────────────────────────────────────────────

def slice_defs(rows: list[dict]) -> list[tuple[str, list[dict]]]:
    """Return a list of (slice_name, rows_in_slice) tuples."""
    slices: list[tuple[str, list[dict]]] = []

    # --- Ply range ---
    slices.append(("ply <=15 (early)",  [r for r in rows if r["ply"] <= 15]))
    slices.append(("ply 16-35 (middle)", [r for r in rows if 16 <= r["ply"] <= 35]))
    slices.append(("ply >=36 (endgame)", [r for r in rows if r["ply"] >= 36]))

    # --- Capture vs non-capture ---
    slices.append(("captures",     [r for r in rows if r["is_capture"]]))
    slices.append(("non-captures", [r for r in rows if not r["is_capture"]]))

    # --- Material balance (|bal| <= 1 pawn unit = 0.84) ---
    slices.append(("material balanced (|bal| <= 1P)",
                   [r for r in rows if abs(r["material_balance"]) <= PIECE_VALUE["P"]]))
    slices.append(("material imbalanced (|bal| >  1P)",
                   [r for r in rows if abs(r["material_balance"]) >  PIECE_VALUE["P"]]))

    # --- Aggressor piece type ---
    for letter in ("P", "N", "B", "R", "Q", "K"):
        slices.append((f"aggressor={letter}",
                       [r for r in rows if r["aggressor_type"] == letter]))

    # --- |kappa_position| magnitude buckets ---
    slices.append(("|kappa_position| < 10",
                   [r for r in rows if abs(r["kappa_position"]) < 10]))
    slices.append(("|kappa_position| 10-100",
                   [r for r in rows if 10 <= abs(r["kappa_position"]) <= 100]))
    slices.append(("|kappa_position| > 100",
                   [r for r in rows if abs(r["kappa_position"]) > 100]))

    return slices


# ─── Analysis ──────────────────────────────────────────────────────────────

def rho_table(rows: list[dict]) -> dict[str, float]:
    sf = [r["stockfish_scalar"] for r in rows]
    return {k: spearman_rho(sf, [r[k] for r in rows]) for k in SIGNAL_KEYS}


def played_move_ranks(rows: list[dict]) -> dict[str, list[int]]:
    """For each position in `rows` that has a played move, compute the
    played move's rank (1 = highest) under each of the 5 signals. Rank uses
    strict-greater semantics: rank = 1 + count(other_values > played_value).
    Ties therefore don't push the played move down.
    """
    # Group by position.
    by_pos: dict[tuple[str, int], list[dict]] = {}
    for r in rows:
        by_pos.setdefault((r["game_id"], r["ply"]), []).append(r)

    ranks: dict[str, list[int]] = {k: [] for k in SIGNAL_KEYS}
    for moves in by_pos.values():
        played = [m for m in moves if m["was_played"]]
        if not played:
            continue
        played_move = played[0]
        for k in SIGNAL_KEYS:
            pv = played_move[k]
            rk = 1 + sum(1 for m in moves if m[k] > pv)
            ranks[k].append(rk)
    return ranks


def rank_summary(ranks: list[int]) -> str:
    if not ranks:
        return "n=0"
    n = len(ranks)
    top1 = sum(1 for r in ranks if r == 1)
    top3 = sum(1 for r in ranks if r <= 3)
    mean = sum(ranks) / n
    median = statistics.median(ranks)
    return (f"n={n:<5}  top1={top1}/{n} ({top1 / n * 100:5.1f}%)  "
            f"top3={top3}/{n} ({top3 / n * 100:5.1f}%)  "
            f"mean={mean:5.2f}  median={median:5.1f}")


# ─── Report ────────────────────────────────────────────────────────────────

def fmt_rho(name: str, val: float, notable: bool) -> str:
    if math.isnan(val):
        return f"    {name:<17}: rho=  NaN"
    mark = "  <-- notable" if notable else ""
    return f"    {name:<17}: rho={val:+.4f}{mark}"


def render_report(rows: list[dict], eval_csv: Path, v2_csv: Path) -> str:
    buf = io.StringIO()
    w = buf.write
    w("Stockfish slice reanalysis (no new evaluations)\n")
    w(f"  eval csv       : {eval_csv}\n")
    w(f"  v2 csv (attrs) : {v2_csv}\n")
    w(f"  total rows     : {len(rows)}\n")
    w(f"  notable threshold: |rho| >= {NOTABLE_RHO:.2f}\n")
    w(f"  min n for trust  : {MIN_N_FOR_TRUST}\n\n")

    # Global baseline.
    w("=" * 72 + "\n")
    w("GLOBAL (all rows)\n")
    w("=" * 72 + "\n")
    rho = rho_table(rows)
    for k in SIGNAL_KEYS:
        w(fmt_rho(k, rho[k], abs(rho[k]) >= NOTABLE_RHO if not math.isnan(rho[k]) else False) + "\n")
    w("\n  Played-move rank distribution (global):\n")
    ranks = played_move_ranks(rows)
    for k in SIGNAL_KEYS:
        w(f"    {k:<17}: {rank_summary(ranks[k])}\n")
    w("\n")

    # Per-slice.
    for name, sub in slice_defs(rows):
        w("-" * 72 + "\n")
        warn = "  [WARN: small sample]" if len(sub) < MIN_N_FOR_TRUST else ""
        w(f"SLICE: {name}   (n={len(sub)} rows){warn}\n")
        if not sub:
            w("  (empty slice)\n\n")
            continue
        srho = rho_table(sub)
        for k in SIGNAL_KEYS:
            v = srho[k]
            notable = (not math.isnan(v)) and abs(v) >= NOTABLE_RHO
            w(fmt_rho(k, v, notable) + "\n")
        sranks = played_move_ranks(sub)
        w("  Played-move rank distribution:\n")
        for k in SIGNAL_KEYS:
            w(f"    {k:<17}: {rank_summary(sranks[k])}\n")
        w("\n")

    # Notable summary.
    w("=" * 72 + "\n")
    w("NOTABLE SLICES (|rho| >= {:.2f}, n >= {})\n".format(NOTABLE_RHO, MIN_N_FOR_TRUST))
    w("=" * 72 + "\n")
    any_notable = False
    for name, sub in slice_defs(rows):
        if len(sub) < MIN_N_FOR_TRUST:
            continue
        srho = rho_table(sub)
        notables = [(k, v) for k, v in srho.items()
                    if not math.isnan(v) and abs(v) >= NOTABLE_RHO]
        if notables:
            any_notable = True
            w(f"  {name} (n={len(sub)}):\n")
            for k, v in notables:
                w(f"    {k:<17}: rho={v:+.4f}\n")
    if not any_notable:
        w("  (none)\n")
    return buf.getvalue()


# ─── CLI ───────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description=(
            "Slice-level reanalysis of the existing Phase 2 Stockfish CSV. "
            "Joins stockfish_evaluations_v2.csv with the v2 delta/sigma CSV "
            "on (game_id, ply, move_uci), then reports Spearman rho and "
            "played-move rank distributions per slice. No new Stockfish runs."
        ),
        epilog=textwrap.dedent("""\
            Examples:
              # Defaults.
              python analyze_stockfish_slices.py

              # Point at a different eval CSV.
              python analyze_stockfish_slices.py \\
                  --eval-csv path/to/stockfish_evaluations_v2.csv
            """),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--eval-csv", type=Path, default=DEFAULT_EVAL_CSV,
                    help=f"Phase 2 stockfish evaluations CSV. Default: {DEFAULT_EVAL_CSV}")
    ap.add_argument("--v2-csv", type=Path, default=DEFAULT_V2_CSV,
                    help=("v2 delta/sigma CSV, used for is_capture / "
                          f"aggressor_type / was_played / fen. Default: {DEFAULT_V2_CSV}"))
    ap.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                    help=f"Output text file. Default: {DEFAULT_OUTPUT}")
    args = ap.parse_args()

    for p in (args.eval_csv, args.v2_csv):
        if not p.exists():
            sys.exit(f"Missing input: {p}")

    print(f"Loading eval CSV: {args.eval_csv}")
    eval_rows = load_eval_csv(args.eval_csv)
    print(f"  {len(eval_rows)} rows")

    want = {(r["game_id"], r["ply"], r["move_uci"]) for r in eval_rows}
    print(f"Loading v2 CSV (filtered to {len(want)} keys): {args.v2_csv}")
    move_attrs, fens = load_v2_index(args.v2_csv, want)
    print(f"  matched {len(move_attrs)} move rows, {len(fens)} positions")

    rows = enrich(eval_rows, move_attrs, fens)
    print(f"  enriched {len(rows)} rows\n")

    text = render_report(rows, args.eval_csv, args.v2_csv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    print(f"\nWrote -> {args.output}")


if __name__ == "__main__":
    main()
