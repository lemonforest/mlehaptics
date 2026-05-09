"""Search-tree benchmark — combines move-gen + eval into nodes/sec
at depth (1.16.0+).

Addresses the deferred item from 1.14.0 amendment 1's stress-test
note: *"Move-gen cost in the bench (currently bench measures only
static eval; combining with move-gen for nodes/sec at depth is
real but separate work)."*

This bench complements two existing benches:

  * ``tests/bench_spectral_eval.py`` — measures only static
    ``evaluator(pos, side)`` cost, ignoring search-tree shape.
  * ``tests/bench_phase_operator_movegen.py`` — measures only
    ``legal_moves()`` cost, ignoring evaluator cost.

Neither captures the **integrated** cost of running an alpha-beta
search at depth — which is what actually matters for the §16 search
engine. This bench fills the gap by running
:func:`chess_spectral.engine.search.search` at a configurable depth
on representative positions, recording ``nodes_searched`` and
``elapsed_ms``, and reporting **nodes/sec** as the headline metric.

The numbers expose the actual search-time tradeoff between evaluator
variants. The static-eval bench in ``bench_spectral_eval.py`` showed
``spectral_hybrid_8bit_lru`` at ~50 µs/call vs ``spectral_float64``'s
~870 µs/call (~17× speedup); the open empirical question is whether
that translates to nodes/sec advantage at depth, where TT collisions,
quiescence, and move ordering matter alongside raw eval cost.

Usage
-----

::

    cd docs/chess-maths/chess-spectral/python

    # Quick: depth 4 on the standard mixed corpus, 3 reps per position
    python tests/bench_search_tree.py

    # Custom depth:
    python tests/bench_search_tree.py --depth 5

    # Specific variants:
    python tests/bench_search_tree.py --variants material,spectral_hybrid_8bit_lru

    # JSON for archival (regression checks across CI runs):
    python tests/bench_search_tree.py --output bench_search_tree.json

The output JSON has the same shape across all chess-spectral bench
runners — variant × position × metric — so longitudinal comparison
across releases is straightforward.

Caveats
-------

* Search-tree shape depends on TT seed, move ordering, quiescence
  behavior. Reps are averaged; small variance is expected.
* depth=4 is the default; higher depths (5-7) are realistic for
  testing scaling but each game position adds 5-10× cost.
* The bench includes warmup runs to amortize JIT-like effects (lazy
  module loads, TT fill-from-empty).
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional

HERE = Path(__file__).resolve().parent
PKG_DIR = HERE.parent
if str(PKG_DIR) not in sys.path:
    sys.path.insert(0, str(PKG_DIR))


# ─── Corpora ────────────────────────────────────────────────────────


# Re-use the same hand-picked corpus as ``bench_spectral_eval.py`` so
# the search-tree bench numbers are directly comparable to the
# static-eval numbers from §20.21. (Future: swap in PGN-classified
# corpus from ``chess_spectral.phase_classifier`` once the bench has
# baseline numbers locked in.)

OPENING_FENS: List[str] = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6 0 2",
]
MIDGAME_FENS: List[str] = [
    "r1b2rk1/pp2bppp/2nppn2/q1p5/2P5/2N1PN2/PPQ1BPPP/2KR1B1R w - - 4 11",
    "r2q1rk1/pp1bbppp/2np1n2/4p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 0 8",
]
ENDGAME_FENS: List[str] = [
    "8/8/8/4k3/4P3/4K3/8/8 w - - 0 1",
    "8/8/8/4k3/8/8/4R3/4K3 w - - 0 1",
]

CORPORA: Dict[str, List[str]] = {
    "opening": OPENING_FENS,
    "midgame": MIDGAME_FENS,
    "endgame": ENDGAME_FENS,
}


# ─── Variant registry (mirrors bench_spectral_eval) ─────────────────


def _build_variants() -> Dict[str, Callable]:
    """Return {variant_name: evaluator_fn_factory}."""
    from chess_spectral.engine.eval import material, spectral

    registry: Dict[str, Callable] = {}

    def make_material():
        return material.evaluate

    def make_spectral_float64():
        return spectral.evaluate

    def make_spectral_hybrid_8bit_lru():
        from chess_spectral.engine.eval.spectral_hybrid_cache import (
            make_cached_evaluator,
        )
        evaluator_fn, _cache = make_cached_evaluator(
            magnitude_bits=8, cache_size=10_000,
        )
        return evaluator_fn

    registry['material'] = make_material
    registry['spectral_float64'] = make_spectral_float64
    registry['spectral_hybrid_8bit_lru'] = make_spectral_hybrid_8bit_lru
    return registry


# ─── Single search bench ────────────────────────────────────────────


def bench_one_search(
    fen: str,
    evaluator_factory: Callable,
    *,
    depth: int,
    reps: int,
    warmup: int = 1,
) -> Dict[str, object]:
    """Run ``search(...)`` at depth ``depth`` on a single FEN, record
    nodes_searched + elapsed_ms × ``reps`` reps.

    Builds a fresh evaluator (and fresh LRU cache, for cached variants)
    per rep so cache state doesn't bleed across reps. ``warmup`` reps
    run before timing starts to amortize lazy-init cost.

    Returns
    -------
    dict with:
      * ``mean_nodes`` (int) — average nodes_searched across reps
      * ``mean_elapsed_ms`` (float) — average elapsed time
      * ``nodes_per_sec`` (float) — derived
      * ``depth_reached`` (int) — should equal depth
      * ``per_rep_elapsed_ms`` (list of floats) — for variance check
    """
    import chess
    from chess_spectral.engine.search import search, SearchOptions
    options = SearchOptions(max_depth=depth)

    # Warmup runs (not timed; just lazy-init).
    for _ in range(warmup):
        evaluator = evaluator_factory()
        board = chess.Board(fen)
        search(board, evaluator, options)

    rep_results = []
    for _ in range(reps):
        evaluator = evaluator_factory()
        board = chess.Board(fen)
        t_start = time.perf_counter()
        result = search(board, evaluator, options)
        t_elapsed_ms = (time.perf_counter() - t_start) * 1000.0
        rep_results.append({
            'nodes_searched': result.nodes_searched,
            'elapsed_ms': t_elapsed_ms,
            'depth_reached': result.depth_reached,
            'best_move': str(result.best_move) if result.best_move else None,
        })

    mean_nodes = statistics.mean(
        r['nodes_searched'] for r in rep_results
    )
    mean_elapsed_ms = statistics.mean(
        r['elapsed_ms'] for r in rep_results
    )
    nodes_per_sec = (
        mean_nodes / (mean_elapsed_ms / 1000.0)
        if mean_elapsed_ms > 0 else 0.0
    )
    return {
        'mean_nodes': float(mean_nodes),
        'mean_elapsed_ms': float(mean_elapsed_ms),
        'nodes_per_sec': float(nodes_per_sec),
        'depth_reached': rep_results[0]['depth_reached'],
        'per_rep_elapsed_ms': [r['elapsed_ms'] for r in rep_results],
    }


# ─── Sweep across variant × corpus ──────────────────────────────────


def run_sweep(
    variants: List[str],
    *,
    depth: int,
    reps: int,
    corpora: Optional[Dict[str, List[str]]] = None,
    verbose: bool = True,
) -> Dict[str, object]:
    """Run the bench over all (variant × corpus × position) combinations."""
    if corpora is None:
        corpora = CORPORA
    registry = _build_variants()
    for v in variants:
        if v not in registry:
            raise ValueError(
                f"unknown variant {v!r}; available: {sorted(registry)}"
            )

    sweep: Dict[str, Dict[str, List[Dict[str, object]]]] = {}
    for variant in variants:
        sweep[variant] = {}
        factory = registry[variant]
        for corpus_name, fens in corpora.items():
            sweep[variant][corpus_name] = []
            for i, fen in enumerate(fens):
                if verbose:
                    print(
                        f"  {variant} × {corpus_name}[{i}]: "
                        f"{fen[:30]}...",
                        file=sys.stderr,
                    )
                result = bench_one_search(
                    fen, factory,
                    depth=depth, reps=reps,
                )
                sweep[variant][corpus_name].append({
                    'fen': fen,
                    **result,
                })

    # Aggregate per-corpus per-variant means.
    aggregates: Dict[str, Dict[str, float]] = {}
    for variant in variants:
        aggregates[variant] = {}
        for corpus_name in corpora:
            entries = sweep[variant][corpus_name]
            mean_nps = statistics.mean(e['nodes_per_sec'] for e in entries)
            mean_nodes = statistics.mean(e['mean_nodes'] for e in entries)
            mean_ms = statistics.mean(e['mean_elapsed_ms'] for e in entries)
            aggregates[variant][corpus_name] = {
                'mean_nodes_per_sec': float(mean_nps),
                'mean_nodes': float(mean_nodes),
                'mean_elapsed_ms': float(mean_ms),
            }

    return {
        'depth': int(depth),
        'reps': int(reps),
        'variants': list(variants),
        'corpora': {k: list(v) for k, v in corpora.items()},
        'sweep': sweep,
        'aggregates': aggregates,
    }


# ─── Pretty printer ─────────────────────────────────────────────────


def _format_table(aggregates: Dict[str, Dict[str, dict]],
                  corpora: Dict[str, List[str]]) -> str:
    """Render the aggregates as a markdown-ish table."""
    corpus_names = list(corpora.keys())
    lines = []
    header = "| Variant | " + " | ".join(
        f"{c} (k_nodes/s)" for c in corpus_names
    ) + " |"
    sep = "|" + "|".join(["---"] * (len(corpus_names) + 1)) + "|"
    lines.append(header)
    lines.append(sep)
    for variant, by_corpus in aggregates.items():
        cells = [variant]
        for c in corpus_names:
            nps = by_corpus[c]['mean_nodes_per_sec']
            cells.append(f"{nps / 1000:.1f}")
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


# ─── CLI ────────────────────────────────────────────────────────────


def _main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tests/bench_search_tree.py",
        description=(
            "Benchmark search-tree throughput (nodes/sec) at depth, "
            "for each evaluator variant × corpus combination. "
            "Reports raw timings + aggregate nodes/sec."
        ),
    )
    parser.add_argument(
        "--variants", type=str,
        default="material,spectral_float64,spectral_hybrid_8bit_lru",
        help="Comma-separated variant list.",
    )
    parser.add_argument(
        "--depth", type=int, default=4,
        help="Search depth (default 4).",
    )
    parser.add_argument(
        "--reps", type=int, default=3,
        help="Reps per (variant, position) cell (default 3).",
    )
    parser.add_argument(
        "--output", type=Path, default=None,
        help="Write structured JSON to this path.",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress per-cell progress output to stderr.",
    )
    args = parser.parse_args(argv)

    variants = [v.strip() for v in args.variants.split(",")]
    output = run_sweep(
        variants,
        depth=args.depth,
        reps=args.reps,
        verbose=not args.quiet,
    )

    if args.output is not None:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)
        print(f"Wrote {args.output}", file=sys.stderr)

    # Always print the aggregate table (markdown-ish).
    print()
    print(f"Search-tree bench at depth={args.depth}, reps={args.reps}:")
    print()
    print(_format_table(output['aggregates'], CORPORA))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
