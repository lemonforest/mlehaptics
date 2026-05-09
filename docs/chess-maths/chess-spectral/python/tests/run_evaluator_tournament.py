"""Tournament-driven evaluator validation runner (1.16.0+).

Addresses the deferred item from 1.14.0 amendment 1's stress-test
note: *"Tournament-driven evaluator validation — the question of
whether ``spectral_hybrid_8bit_lru`` actually beats ``material`` at
deep search via the §16 tournament harness."*

The §16.7 amendment de-gated B-spike-3 from the (now-contaminated)
Othello depth-decay finding. The open empirical question — does the
spectral evaluator family translate its raw-speedup advantage into
ELO advantage at depth ≥ 4? — remains. This runner is the
infrastructure for answering it.

Method
------

For each (evaluator_a, evaluator_b) pair × each depth × each
games-per-pair count:

  1. Build :class:`Agent` for each evaluator with a matching
     :class:`SearchOptions(max_depth=depth)`.
  2. Run :func:`run_round_robin` with N games per pair, alternating
     colors.
  3. Report:
     * Final ELO ratings per evaluator
     * Per-pair win/loss/draw record
     * Per-pair termination reason histogram

Repeat for each depth in the sweep.

Output is structured JSON suitable for archival, longitudinal
comparison, and cross-CI artifact diffing.

Usage
-----

::

    # Quick sanity sweep (small depth, small game count) — runs in seconds
    python tests/run_evaluator_tournament.py --depth 2 --games-per-pair 1

    # Realistic sweep (depth 4, 8 games per pair) — runs in minutes
    python tests/run_evaluator_tournament.py --depth 4 --games-per-pair 8 \\
        --variants material,spectral_float64,spectral_hybrid_8bit_lru

    # Multi-depth sweep — runs in hours; for ELO trend over depth
    python tests/run_evaluator_tournament.py --depths 2,3,4,5,6 \\
        --games-per-pair 4 \\
        --output tournament_sweep.json

Default variant set: material vs spectral_float64 vs spectral_hybrid_8bit_lru.
The spectral_hybrid_8bit_lru is the runtime winner at static eval
(~50µs/call vs ~870µs for spectral_float64); the question is whether
that translates to ELO at depth ≥ 4.

Caveats
-------

* This is **not a unit test** — it's a research tool. The
  ``test_run_evaluator_tournament_smoke`` test in the same directory
  runs the smallest possible tournament (depth=2, 1 game per pair)
  to verify the runner itself works.
* Game outcomes at low depth are noisy; small-N comparisons (< 20
  games per pair) are not statistically meaningful. Runner reports
  the number of games for context.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

HERE = Path(__file__).resolve().parent
PKG_DIR = HERE.parent
if str(PKG_DIR) not in sys.path:
    sys.path.insert(0, str(PKG_DIR))


# ─── Variant registry ───────────────────────────────────────────────


def _build_evaluator_variants() -> Dict[str, Tuple[str, Callable]]:
    """Return a registry of {variant_name: (description, evaluator_factory)}.

    Each ``evaluator_factory()`` returns a fresh ``(name, evaluator_fn)``
    pair — the cached evaluators (LRU variants) build a fresh cache
    per agent so games don't share state across pairs.
    """
    from chess_spectral.engine.eval import material, spectral

    registry: Dict[str, Tuple[str, Callable]] = {}

    def make_material_factory():
        return ('material', material.evaluate)

    def make_spectral_float64_factory():
        return ('spectral_float64', spectral.evaluate)

    def make_spectral_hybrid_8bit_lru_factory():
        from chess_spectral.engine.eval.spectral_hybrid_cache import (
            make_cached_evaluator,
        )
        evaluator_fn, _cache = make_cached_evaluator(
            magnitude_bits=8, cache_size=10_000,
        )
        return ('spectral_hybrid_8bit_lru', evaluator_fn)

    registry['material'] = (
        'Phase 6.1.1 material baseline; integer addition.',
        make_material_factory,
    )
    registry['spectral_float64'] = (
        'Current 1.0-1.12.x spectral evaluator (encode_640 + numpy '
        'sum-of-squares per channel).',
        make_spectral_float64_factory,
    )
    registry['spectral_hybrid_8bit_lru'] = (
        '1.13.0+ hybrid evaluator with LRU cache. Cache-hit fast path '
        '~50µs vs spectral_float64\'s ~870µs.',
        make_spectral_hybrid_8bit_lru_factory,
    )

    return registry


# ─── Tournament runner ──────────────────────────────────────────────


def run_one_tournament(
    variant_names: List[str],
    *,
    depth: int,
    games_per_pair: int,
    max_plies: int,
    starting_fen: Optional[str] = None,
    verbose: bool = False,
) -> Dict[str, object]:
    """Run a single round-robin tournament at one depth.

    Returns a JSON-serializable dict with final ELOs, per-pair
    records, and per-game termination reasons.
    """
    import chess
    from chess_spectral.engine.search import search, SearchOptions
    from chess_spectral.engine.tournament import (
        Agent, run_round_robin,
    )

    registry = _build_evaluator_variants()
    for name in variant_names:
        if name not in registry:
            raise ValueError(
                f"unknown variant {name!r}; available: "
                f"{sorted(registry)}"
            )

    # Build agents for each variant.
    agents: List[Agent] = []
    for name in variant_names:
        _description, factory = registry[name]
        label, evaluator = factory()
        agents.append(Agent(
            label=label,
            evaluator=evaluator,
            search_fn=search,
            search_options=SearchOptions(max_depth=depth),
        ))

    if starting_fen is not None:
        def board_factory():
            return chess.Board(starting_fen)
    else:
        def board_factory():
            return chess.Board()

    if verbose:
        print(
            f"  Tournament at depth={depth}, "
            f"games_per_pair={games_per_pair}, "
            f"max_plies={max_plies}",
            file=sys.stderr,
        )

    t_start = time.monotonic()
    result = run_round_robin(
        agents=agents,
        n_games_per_pair=games_per_pair,
        board_factory=board_factory,
        max_plies=max_plies,
    )
    elapsed = time.monotonic() - t_start

    # Build per-pair termination histogram.
    termination_per_pair: Dict[str, Dict[str, int]] = {}
    for game in result.games:
        key = f"{game.white.label}_vs_{game.black.label}"
        bucket = termination_per_pair.setdefault(key, {})
        bucket[game.termination] = bucket.get(game.termination, 0) + 1

    return {
        'depth': int(depth),
        'games_per_pair': int(games_per_pair),
        'max_plies': int(max_plies),
        'n_games_played': len(result.games),
        'elapsed_seconds': float(elapsed),
        'final_elos': dict(result.final_elos),
        'pair_records': {
            f"{a}_vs_{b}": {
                'wins': wins, 'losses': losses, 'draws': draws,
            }
            for (a, b), (wins, losses, draws) in result.pair_records.items()
        },
        'termination_by_pair': termination_per_pair,
        'mean_plies_per_game': (
            sum(g.plies_played for g in result.games) / len(result.games)
            if result.games else 0
        ),
        'mean_elapsed_per_game_ms': (
            sum(g.elapsed_ms for g in result.games) / len(result.games)
            if result.games else 0
        ),
    }


def run_depth_sweep(
    variant_names: List[str],
    depths: List[int],
    *,
    games_per_pair: int,
    max_plies: int,
    starting_fen: Optional[str] = None,
    verbose: bool = False,
) -> Dict[str, object]:
    """Run a tournament at each depth, return aggregated results."""
    sweep: List[Dict[str, object]] = []
    for depth in depths:
        if verbose:
            print(f"=== Depth {depth} ===", file=sys.stderr)
        result = run_one_tournament(
            variant_names,
            depth=depth,
            games_per_pair=games_per_pair,
            max_plies=max_plies,
            starting_fen=starting_fen,
            verbose=verbose,
        )
        sweep.append(result)
        if verbose:
            print(
                f"  Final ELOs: {result['final_elos']}",
                file=sys.stderr,
            )
            print(
                f"  Elapsed: {result['elapsed_seconds']:.1f}s "
                f"({result['n_games_played']} games)",
                file=sys.stderr,
            )

    return {
        'variants': list(variant_names),
        'depths': list(depths),
        'games_per_pair': int(games_per_pair),
        'max_plies': int(max_plies),
        'starting_fen': starting_fen,
        'results': sweep,
    }


# ─── CLI ────────────────────────────────────────────────────────────


def _main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tests/run_evaluator_tournament.py",
        description=(
            "Run a round-robin tournament between chess-spectral "
            "evaluator variants, optionally sweeping over depth. "
            "Reports ELO + per-pair records as JSON for archival."
        ),
    )
    parser.add_argument(
        "--variants", type=str,
        default="material,spectral_float64,spectral_hybrid_8bit_lru",
        help="Comma-separated variant list. Default: 3-way comparison.",
    )
    parser.add_argument(
        "--depth", type=int, default=None,
        help="Single depth (mutually exclusive with --depths).",
    )
    parser.add_argument(
        "--depths", type=str, default=None,
        help=(
            "Comma-separated depth sweep, e.g. '2,3,4,5,6'. "
            "Mutually exclusive with --depth."
        ),
    )
    parser.add_argument(
        "--games-per-pair", type=int, default=4,
        help="Games per agent pair, alternating colors. Default 4.",
    )
    parser.add_argument(
        "--max-plies", type=int, default=200,
        help="Hard cap on game length (ply count). Default 200.",
    )
    parser.add_argument(
        "--starting-fen", type=str, default=None,
        help=(
            "Custom starting FEN. Default: standard initial position. "
            "Useful for testing endgame-like starting positions."
        ),
    )
    parser.add_argument(
        "--output", type=Path, default=None,
        help="Write structured JSON results to this path.",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress per-tournament progress output to stderr.",
    )
    args = parser.parse_args(argv)

    variants = [v.strip() for v in args.variants.split(",")]
    if args.depth is not None and args.depths is not None:
        parser.error("specify either --depth or --depths, not both")
    if args.depths is not None:
        depths = [int(d.strip()) for d in args.depths.split(",")]
    else:
        depths = [args.depth or 4]

    verbose = not args.quiet
    output = run_depth_sweep(
        variants,
        depths=depths,
        games_per_pair=args.games_per_pair,
        max_plies=args.max_plies,
        starting_fen=args.starting_fen,
        verbose=verbose,
    )

    if args.output is not None:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)
        print(
            f"Wrote {args.output} ({len(output['results'])} depth(s))",
            file=sys.stderr,
        )
    else:
        # Pretty-print to stdout if no --output.
        print(json.dumps(output, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
