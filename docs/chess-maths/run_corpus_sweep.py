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
import datetime as dt
import json
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "chess-spectral" / "python"))

from pgn_fetcher import PGNFetcher, LichessSource  # noqa: E402
from chess_spectral import (  # noqa: E402
    process_game, extract_features,
    write_index_csv, write_summary_md, INDEX_COLUMNS,
)

BRIDGE = HERE / "chess-spectral" / "bridge" / "pgn_bridge.py"
ENCODER = HERE / "chess-spectral" / "python" / "spectral_py.py"
RESULTS_ROOT = HERE / "results"


def _safe_default_run_id(source: str, n: int, seed: int | None,
                         username: str | None = None) -> str:
    today = dt.date.today().isoformat()
    seed_str = f"_seed{seed}" if seed is not None else ""
    # Lichess runs get username in the id so "sweep_lichess_X_Y_Z" is unique
    # across different players scraped on the same day.
    user_str = f"_{username.lower()}" if username else ""
    return f"sweep_{source}{user_str}_{today}_N{n}{seed_str}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--n", type=int, default=50, help="Number of games to fetch")
    ap.add_argument("--seed", type=int, default=None,
                    help="RNG seed for reproducibility")
    ap.add_argument("--source", default="hf", choices=["hf", "lichess"],
                    help="Fetch source ('hf' = fishtest HuggingFace, "
                         "'lichess' = Lichess user-games with eval+clk)")
    ap.add_argument("--min-moves", type=int, default=30)
    ap.add_argument("--max-moves", type=int, default=100)
    ap.add_argument("--tc-min", type=float, default=10.0,
                    help="HF-only: min time control in seconds")
    # Lichess-specific
    ap.add_argument("--username",
                    help="Lichess username (required for --source lichess)")
    ap.add_argument("--perf", default="blitz,rapid",
                    help="Lichess perf type(s), comma-separated "
                         "(default: blitz,rapid)")
    ap.add_argument("--rated", action="store_true", default=True,
                    help="Lichess: rated games only (default: true)")
    ap.add_argument("--since-year", type=int,
                    help="Lichess: start year filter (inclusive)")
    ap.add_argument("--until-year", type=int,
                    help="Lichess: end year filter (inclusive)")
    ap.add_argument("--chain", action="store_true",
                    help="Lichess: Fibonacci-style opponent chain walk "
                         "(seed user -> opponent -> opponent of opponent...). "
                         "Stops when N games collected or chain dead-ends.")
    ap.add_argument("--chain-buffer", type=int, default=8,
                    help="Per-step buffer when searching for an unseen game "
                         "in chain mode (default: 8)")
    ap.add_argument("--run-id", default=None,
                    help="Output subdir under results/ (default: sweep_<...>)")
    ap.add_argument("--results-root", default=str(RESULTS_ROOT))
    args = ap.parse_args()

    if args.source == "lichess" and not args.username:
        ap.error("--source lichess requires --username")

    default_id = _safe_default_run_id(
        args.source, args.n, args.seed, username=args.username,
    )
    if args.source == "lichess" and args.chain:
        # sweep_lichess_X_DATE_NN  ->  sweep_chain_lichess_X_DATE_NN
        default_id = default_id.replace("sweep_", "sweep_chain_", 1)
    run_id = args.run_id or default_id
    run_dir = Path(args.results_root) / run_id
    for sub in ("pgn", "ndjson", "spectralz"):
        (run_dir / sub).mkdir(parents=True, exist_ok=True)

    print(f"[sweep] run_id = {run_id}", file=sys.stderr)
    print(f"[sweep] output = {run_dir}", file=sys.stderr)

    t0 = time.time()
    if args.source == "hf":
        print(f"[sweep] fetching {args.n} games from HuggingFace fishtest...",
              file=sys.stderr)
        games = PGNFetcher(verbose=True).fetch_random_games(
            n=args.n, min_moves=args.min_moves, max_moves=args.max_moves,
            tc_base_min=args.tc_min, seed=args.seed,
        )
    else:  # lichess
        li = LichessSource(verbose=True)
        if args.chain:
            print(f"[sweep] chain-walking from Lichess user "
                  f"'{args.username}' (perf={args.perf}, target N={args.n})...",
                  file=sys.stderr)
            games = li.fetch_opponent_chain(
                args.username, n=args.n,
                rated=args.rated, perf=args.perf,
                buffer=args.chain_buffer,
                min_moves=args.min_moves, max_moves=args.max_moves,
            )
        else:
            print(f"[sweep] fetching {args.n} games from Lichess user "
                  f"'{args.username}' (perf={args.perf})...", file=sys.stderr)
            games = li.fetch_user_games(
                args.username, n=args.n, rated=args.rated, perf=args.perf,
                since_year=args.since_year, until_year=args.until_year,
                min_moves=args.min_moves, max_moves=args.max_moves,
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
    write_index_csv(rows, index_path, run_id)

    # corpus_summary.md — human-readable top-N snapshots.
    write_summary_md(
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
            "n":          args.n,
            "seed":       args.seed,
            "min_moves":  args.min_moves,
            "max_moves":  args.max_moves,
            "tc_min":     args.tc_min if args.source == "hf" else None,
            "username":   args.username if args.source == "lichess" else None,
            "perf":       args.perf if args.source == "lichess" else None,
            "rated":      args.rated if args.source == "lichess" else None,
            "since_year": args.since_year if args.source == "lichess" else None,
            "until_year": args.until_year if args.source == "lichess" else None,
            "chain":      args.chain if args.source == "lichess" else None,
            "chain_buffer": args.chain_buffer if (args.source == "lichess" and args.chain) else None,
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
