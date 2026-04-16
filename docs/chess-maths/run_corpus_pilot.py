#!/usr/bin/env python3
"""run_corpus_pilot.py — end-to-end PGN fetch + bridge + encode pipeline.

Small-N smoke test for the chess-spectral corpus pipeline: fetches a
handful of random games from a source (HuggingFace fishtest today;
TWIC / chessgames.com are also available in pgn_fetcher.py but not
wired into this driver), writes one PGN per game, runs the v2 lossless
bridge, then the 640-dim encoder, and emits a manifest.json.

Output layout (keeps docs/chess-maths/ clean by writing into results/):

    docs/chess-maths/results/<run_id>/
        manifest.json
        pgn/game_NNN.pgn
        ndjson/game_NNN.ndjson
        spectralz/game_NNN.spectralz

Usage:
    python run_corpus_pilot.py --n 3 --seed 42
    python run_corpus_pilot.py --n 20 --seed 7 --run-id smoke_2026-04-14

For corpus-scale runs (feature extraction + sortable index), see
run_corpus_sweep.py — this driver is intentionally minimal.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "chess-spectral" / "python"))

from pgn_fetcher import PGNFetcher  # noqa: E402
from chess_spectral import process_game  # noqa: E402

BRIDGE = HERE / "chess-spectral" / "bridge" / "pgn_bridge.py"
ENCODER = HERE / "chess-spectral" / "python" / "spectral_py.py"
RESULTS_ROOT = HERE / "results"


def _safe_default_run_id(source: str, n: int, seed: int | None) -> str:
    today = dt.date.today().isoformat()
    seed_str = f"_seed{seed}" if seed is not None else ""
    return f"pilot_{source}_{today}_N{n}{seed_str}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--n", type=int, default=3, help="Number of games to fetch")
    ap.add_argument("--seed", type=int, default=None, help="RNG seed for reproducibility")
    ap.add_argument("--source", default="hf", choices=["hf"],
                    help="Fetch source (only 'hf' wired in this pilot)")
    ap.add_argument("--min-moves", type=int, default=30)
    ap.add_argument("--max-moves", type=int, default=100)
    ap.add_argument("--tc-min", type=float, default=10.0)
    ap.add_argument("--run-id", default=None, help="Output subdir under results/")
    ap.add_argument("--results-root", default=str(RESULTS_ROOT))
    args = ap.parse_args()

    run_id = args.run_id or _safe_default_run_id(args.source, args.n, args.seed)
    run_dir = Path(args.results_root) / run_id
    for sub in ("pgn", "ndjson", "spectralz"):
        (run_dir / sub).mkdir(parents=True, exist_ok=True)

    print(f"[pilot] run_id = {run_id}", file=sys.stderr)
    print(f"[pilot] output = {run_dir}", file=sys.stderr)

    print(f"[pilot] fetching {args.n} games from HuggingFace...", file=sys.stderr)
    games = PGNFetcher(verbose=True).fetch_random_games(
        n=args.n, min_moves=args.min_moves, max_moves=args.max_moves,
        tc_base_min=args.tc_min, seed=args.seed,
    )
    if not games:
        print("[pilot] fetcher returned no games", file=sys.stderr)
        return 3

    manifest_games = []
    for i, game in enumerate(games, start=1):
        print(f"[pilot] [{i}/{len(games)}] game_{i:03d}", file=sys.stderr)
        entry = process_game(game, run_dir, i, BRIDGE, ENCODER)
        if "error" in entry:
            print(f"[pilot]   error: {entry['error']}", file=sys.stderr)
        manifest_games.append(entry)

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
        "games": manifest_games,
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(f"[pilot] manifest: {run_dir / 'manifest.json'}", file=sys.stderr)
    print(f"[pilot] done: {len(manifest_games)} games processed", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
