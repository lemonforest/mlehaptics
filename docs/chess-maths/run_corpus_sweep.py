#!/usr/bin/env python3
"""run_corpus_sweep.py — bulk PGN fetch + encode + feature extraction.

The corpus-scale counterpart to run_corpus_pilot.py. Fetches N games,
runs each through the PGN → NDJSON → spectralz pipeline, extracts
per-game features (mean channel energies, chaos ratio, NAG counts,
ply count) from the encoded frames, and writes a sortable index +
human-readable summary alongside the raw artifacts.

Output layout:

    docs/chess-maths/results/<run_id>/
        manifest.json          ← run params + aggregates + per-game metadata
        corpus_index.csv       ← one row per game (fully sortable in Excel)
        corpus_summary.md      ← top-N by feature, corpus-wide stats
        pgn/game_NNN.pgn       ← gitignored, regenerable from fetcher + seed
        ndjson/game_NNN.ndjson ← gitignored
        spectralz/game_NNN.spectralz ← gitignored

Default run_id is `sweep_<source>_<YYYY-MM-DD>_N<n>_seed<seed>` — the
`sweep_` prefix keeps it distinct from pilot runs.

Usage:
    python run_corpus_sweep.py --n 50 --seed 7
    python run_corpus_sweep.py --n 200 --seed 7 --run-id sweep_weekend
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "chess-spectral" / "python"))

from pgn_fetcher import PGNFetcher  # noqa: E402
from chess_spectral import process_game, extract_features  # noqa: E402
from chess_spectral.encoder import CHANNELS  # noqa: E402

BRIDGE = HERE / "chess-spectral" / "bridge" / "pgn_bridge.py"
ENCODER = HERE / "chess-spectral" / "python" / "spectral_py.py"
RESULTS_ROOT = HERE / "results"

# Column order for corpus_index.csv. Identity columns first (sortable in
# Excel without cognitive load), then numeric features that typically
# drive analysis (chaos, NAG counts), then the raw channel means.
_IDENTITY_COLS = (
    "index", "run_id", "result", "n_moves", "n_plies",
    "white", "black", "white_elo", "black_elo",
    "event", "date", "source_tc",
)
_FEATURE_COLS = (
    "chaos_ratio", "nag_count", "blunder_count", "mistake_count",
    "has_eval", "has_clk",
)
_CHANNEL_COLS = tuple(f"mean_{name}" for name, _ in CHANNELS)
_BYTES_COLS = ("pgn_bytes", "ndjson_bytes", "spectralz_bytes")
_ERROR_COL = ("error",)
INDEX_COLUMNS = (
    _IDENTITY_COLS + _FEATURE_COLS + _CHANNEL_COLS + _BYTES_COLS + _ERROR_COL
)


def _safe_default_run_id(source: str, n: int, seed: int | None) -> str:
    today = dt.date.today().isoformat()
    seed_str = f"_seed{seed}" if seed is not None else ""
    return f"sweep_{source}_{today}_N{n}{seed_str}"


def _row_for_csv(entry: dict[str, Any], run_id: str) -> dict[str, Any]:
    """Flatten a manifest entry + features dict into a single CSV row.
    Missing numeric fields become '' so the spreadsheet shows blanks
    (not zero) for failed games."""
    row = {col: "" for col in INDEX_COLUMNS}
    row["run_id"] = run_id
    for col in INDEX_COLUMNS:
        if col in entry:
            row[col] = entry[col]
    return row


def _top_n(rows: list[dict[str, Any]], key: str, n: int = 5,
           reverse: bool = True) -> list[dict[str, Any]]:
    viable = [r for r in rows if isinstance(r.get(key), (int, float))]
    viable.sort(key=lambda r: r[key], reverse=reverse)
    return viable[:n]


def _fmt_row_for_summary(row: dict[str, Any]) -> str:
    white = row.get("white", "?")
    black = row.get("black", "?")
    res = row.get("result", "?")
    return f"#{row['index']:>3} {white} vs {black} ({res})"


def _write_summary(rows: list[dict[str, Any]], out_path: Path,
                   run_id: str, elapsed_s: float,
                   n_requested: int, n_fetched: int,
                   n_encoded: int, n_errors: int) -> None:
    ok = [r for r in rows if not r.get("error")]

    def _stat(key: str) -> tuple[float, float, float] | None:
        vals = [r[key] for r in ok if isinstance(r.get(key), (int, float))]
        if not vals:
            return None
        return (
            statistics.mean(vals),
            statistics.median(vals),
            statistics.stdev(vals) if len(vals) > 1 else 0.0,
        )

    result_counts: dict[str, int] = {}
    for r in ok:
        result_counts[r.get("result", "?")] = \
            result_counts.get(r.get("result", "?"), 0) + 1

    lines: list[str] = []
    lines.append(f"# Corpus sweep summary — `{run_id}`")
    lines.append("")
    lines.append(f"- Games requested: **{n_requested}**")
    lines.append(f"- Games fetched:   **{n_fetched}**")
    lines.append(f"- Games encoded:   **{n_encoded}**")
    lines.append(f"- Errors:          **{n_errors}**")
    lines.append(f"- Wall time:       **{elapsed_s:.1f}s**")
    lines.append("")
    if result_counts:
        lines.append("## Result distribution")
        lines.append("")
        for res, count in sorted(result_counts.items(),
                                 key=lambda kv: -kv[1]):
            lines.append(f"- `{res}`: {count}")
        lines.append("")

    lines.append("## Numeric feature stats (successful games)")
    lines.append("")
    lines.append("| Feature | mean | median | stdev |")
    lines.append("|---|---|---|---|")
    for key in ("n_plies", "chaos_ratio", "nag_count", "blunder_count",
                "mean_F3", "mean_FA", "mean_FD"):
        st = _stat(key)
        if st:
            m, md, sd = st
            lines.append(f"| {key} | {m:.4f} | {md:.4f} | {sd:.4f} |")
    lines.append("")

    for key, label, rev in (
        ("chaos_ratio",   "Top 5 by chaos ratio (sharpest)", True),
        ("blunder_count", "Top 5 by blunder count (NAG heavy)", True),
        ("nag_count",     "Top 5 by total NAGs", True),
        ("n_plies",       "Top 5 by length", True),
    ):
        top = _top_n(ok, key, 5, reverse=rev)
        if not top:
            continue
        lines.append(f"## {label}")
        lines.append("")
        for r in top:
            v = r[key]
            tag = f"{v:.4f}" if isinstance(v, float) else str(v)
            lines.append(f"- `{tag:>10}`  {_fmt_row_for_summary(r)}")
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--n", type=int, default=50, help="Number of games to fetch")
    ap.add_argument("--seed", type=int, default=None,
                    help="RNG seed for reproducibility")
    ap.add_argument("--source", default="hf", choices=["hf"],
                    help="Fetch source (only 'hf' wired in this driver)")
    ap.add_argument("--min-moves", type=int, default=30)
    ap.add_argument("--max-moves", type=int, default=100)
    ap.add_argument("--tc-min", type=float, default=10.0)
    ap.add_argument("--run-id", default=None,
                    help="Output subdir under results/ (default: sweep_<...>)")
    ap.add_argument("--results-root", default=str(RESULTS_ROOT))
    args = ap.parse_args()

    run_id = args.run_id or _safe_default_run_id(args.source, args.n, args.seed)
    run_dir = Path(args.results_root) / run_id
    for sub in ("pgn", "ndjson", "spectralz"):
        (run_dir / sub).mkdir(parents=True, exist_ok=True)

    print(f"[sweep] run_id = {run_id}", file=sys.stderr)
    print(f"[sweep] output = {run_dir}", file=sys.stderr)

    t0 = time.time()
    print(f"[sweep] fetching {args.n} games from {args.source}...",
          file=sys.stderr)
    games = PGNFetcher(verbose=True).fetch_random_games(
        n=args.n, min_moves=args.min_moves, max_moves=args.max_moves,
        tc_base_min=args.tc_min, seed=args.seed,
    )
    if not games:
        print("[sweep] fetcher returned no games", file=sys.stderr)
        return 3

    rows: list[dict[str, Any]] = []
    n_encoded = 0
    n_errors = 0
    for i, game in enumerate(games, start=1):
        print(f"[sweep] [{i}/{len(games)}] game_{i:03d}", file=sys.stderr)
        entry = process_game(game, run_dir, i, BRIDGE, ENCODER)
        if "error" in entry:
            n_errors += 1
            print(f"[sweep]   error: {entry['error']}", file=sys.stderr)
            rows.append(entry)
            continue

        spectralz = run_dir / entry["spectralz"]
        ndjson = run_dir / entry["ndjson"]
        try:
            entry.update(extract_features(spectralz, ndjson))
            n_encoded += 1
        except Exception as e:  # noqa: BLE001
            entry["error"] = f"features: {e}"
            n_errors += 1
            print(f"[sweep]   feature extraction failed: {e}", file=sys.stderr)
        rows.append(entry)

    elapsed_s = time.time() - t0

    # corpus_index.csv — the main deliverable; one row per game.
    index_path = run_dir / "corpus_index.csv"
    with open(index_path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(INDEX_COLUMNS))
        w.writeheader()
        for entry in rows:
            w.writerow(_row_for_csv(entry, run_id))

    # corpus_summary.md — human-readable top-N snapshots.
    _write_summary(
        rows, run_dir / "corpus_summary.md",
        run_id, elapsed_s,
        n_requested=args.n, n_fetched=len(games),
        n_encoded=n_encoded, n_errors=n_errors,
    )

    # manifest.json — the authoritative per-game record.
    manifest = {
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "run_id":        run_id,
        "source":        args.source,
        "fetch_params": {
            "n":         args.n,
            "seed":      args.seed,
            "min_moves": args.min_moves,
            "max_moves": args.max_moves,
            "tc_min":    args.tc_min,
        },
        "tool_versions": {
            "python":  sys.version.split()[0],
            "bridge":  str(BRIDGE.relative_to(HERE)).replace("\\", "/"),
            "encoder": str(ENCODER.relative_to(HERE)).replace("\\", "/"),
        },
        "aggregates": {
            "n_requested": args.n,
            "n_fetched":   len(games),
            "n_encoded":   n_encoded,
            "n_errors":    n_errors,
            "wall_time_s": round(elapsed_s, 2),
        },
        "games": rows,
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    print(f"[sweep] manifest:     {run_dir / 'manifest.json'}", file=sys.stderr)
    print(f"[sweep] corpus index: {index_path}", file=sys.stderr)
    print(f"[sweep] summary:      {run_dir / 'corpus_summary.md'}",
          file=sys.stderr)
    print(f"[sweep] done: {n_encoded}/{len(games)} games encoded "
          f"({n_errors} errors) in {elapsed_s:.1f}s", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
