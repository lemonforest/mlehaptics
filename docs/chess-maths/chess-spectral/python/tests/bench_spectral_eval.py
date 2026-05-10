"""Diagnostic benchmark for the spectral evaluator hot path (1.13.0+).

Measures per-call latency for each evaluator variant on opening /
midgame / endgame position corpora. The discipline is **bench first**:
no claim that an evaluator variant is faster than another lands in
the CHANGELOG without a measurement from this harness, run on the
same corpora and the same iteration count, before-and-after the
change.

PGN-sourced corpora (1.19.0+)
-----------------------------

The hand-picked OPENING_FENS / MIDGAME_FENS / ENDGAME_FENS lists
below were honestly admitted in 1.14.0 to be ad-hoc. The
:mod:`chess_spectral.phase_classifier` module (1.16.0+) ships the
data-driven alternative — k-means on log-channel-energy fingerprints
from PGN games — but the bench harness still defaulted to
hand-picked corpora. The ``--pgn-corpus PATH`` flag (1.19.0+) closes
that gap: when supplied, the bench trains a phase classifier on the
PGN, deterministically samples N FENs per phase cluster, and uses
those in place of the hand-picked corpus. All other bench machinery
(variants, iters, summary table) is unchanged.

Variants registered as of 1.13.0 (see :data:`VARIANTS` below):

  * ``material``                 — Phase 6.1.1 baseline (integer
                                    addition; no encoder call)
  * ``qm``                       — Phase 6.1.3 QM-expectation
                                    (most expensive reference)
  * ``spectral_float64``         — current (1.0–1.12.x) spectral
                                    channel-energy path; encode
                                    via ``encode_640`` then numpy
                                    float64 sum-of-squares per
                                    channel
  * ``spectral_float32``         — (d) float32 downstream variant;
                                    mirrors the ephemerides
                                    two-stage architecture (integer
                                    encoder feeding lower-precision
                                    FPU pipeline; complex128 →
                                    complex64 in their case, float64
                                    → float32 in ours). 1.13.0+.
  * ``spectral_hybrid_8bit``     — (a) channel-energy-from-hybrid;
                                    encode via
                                    ``encode_2d_bip_hybrid``, then
                                    compute channel energy directly
                                    from the integer magnitude
                                    portion via uint8² sum (skip
                                    the decode step). 1.13.0+.
  * ``spectral_hybrid_with_tt``  — (b) hybrid + TT cache; encoded
                                    once per Zobrist key, reused on
                                    re-visit. 1.13.0+.
  * ``spectral_pyodide_pure_int``— (c) bypass numpy on the inner
                                    loop; pure-Python list
                                    arithmetic over uint8
                                    magnitudes. Surfaces the
                                    chess4D-OC consumer's expected
                                    win when WASM-numpy overhead
                                    dominates. 1.13.0+.

The corpora are deliberately mixed across game phase to expose
variance — endgame channel energies are very different in shape
from opening, and per-channel max(abs) scales differ by orders
of magnitude.

Usage::

    cd docs/chess-maths/chess-spectral/python
    python tests/bench_spectral_eval.py
    python tests/bench_spectral_eval.py --iters 1000
    python tests/bench_spectral_eval.py --variants material,spectral_float64
    python tests/bench_spectral_eval.py --output bench_results.json
    python tests/bench_spectral_eval.py --pgn-corpus ../../.pgn_cache/twic_tatamast26.pgn

The --output flag emits structured JSON suitable for CI artifacts
or longitudinal regression checks.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import sys
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional

HERE = Path(__file__).resolve().parent
PKG_DIR = HERE.parent
if str(PKG_DIR) not in sys.path:
    sys.path.insert(0, str(PKG_DIR))


# ─── Corpora ─────────────────────────────────────────────────────────


# Opening positions: piece-rich, all castling rights alive, channels
# at typical opening magnitudes.
OPENING_FENS: List[str] = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
    "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6 0 2",
    "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3",
    "rnbqkb1r/pppp1ppp/5n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
]

# Middlegame positions: mixed pieces, some castling done, channels
# in their richest dynamic range.
MIDGAME_FENS: List[str] = [
    "r1b2rk1/pp2bppp/2nppn2/q1p5/2P5/2N1PN2/PPQ1BPPP/2KR1B1R w - - 4 11",
    "r2q1rk1/pp1bbppp/2np1n2/4p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 0 8",
    "r1bq1rk1/pp2bppp/2n1pn2/2pp4/2P5/1PN1PN2/PB1P1PPP/R2QKB1R w KQ - 0 8",
    "r2qkb1r/pp2pppp/2n1bn2/3p4/3P4/2N2N2/PP2PPPP/R1BQKB1R w KQkq - 4 6",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
]

# Endgame positions: sparse, channels dominated by king activity +
# pawn structure; A1 / E channels small, FA / FD dominant.
ENDGAME_FENS: List[str] = [
    "8/8/8/4k3/4P3/4K3/8/8 w - - 0 1",
    "8/8/8/4k3/8/8/4R3/4K3 w - - 0 1",
    "8/3P4/8/8/8/8/4k3/4K3 w - - 0 1",
    "8/2k5/8/8/4K3/8/8/3R4 w - - 0 1",
    "4k3/8/4K3/4P3/8/8/8/8 w - - 0 1",
]

CORPORA: Dict[str, List[str]] = {
    "opening": OPENING_FENS,
    "midgame": MIDGAME_FENS,
    "endgame": ENDGAME_FENS,
}


# ─── PGN-sourced corpora (1.19.0+) ──────────────────────────────────


def build_pgn_sourced_corpora(
    pgn_path: str | Path,
    *,
    max_games: int = 100,
    positions_per_phase: int = 5,
    seed: int = 42,
    sample_every: int = 3,
    skip_initial_plies: int = 4,
) -> "tuple[Dict[str, List[str]], Dict[str, object]]":
    """Train phase classifier on PGN, return phase-keyed FEN corpora.

    Replaces the hand-picked ``CORPORA`` dict with FENs sampled
    deterministically from each phase-cluster the classifier learned.

    Parameters
    ----------
    pgn_path
        Path to a PGN file.
    max_games : int, optional
        Cap on games to walk for classifier training (default 100).
    positions_per_phase : int, optional
        Number of FENs sampled per phase-cluster. Default 5 (matches
        the hand-picked corpus size, so bench cell shape is
        unchanged).
    seed : int, optional
        Seed for the deterministic FEN sampler. Same seed → same
        sampled FENs, given the same PGN + classifier output.
    sample_every : int, optional
        Forwarded to :func:`extract_fingerprints_from_pgn`.
    skip_initial_plies : int, optional
        Forwarded to :func:`extract_fingerprints_from_pgn`.

    Returns
    -------
    corpora
        Dict ``{'opening': [...], 'midgame': [...], 'endgame': [...]}``.
        Each list has ``positions_per_phase`` FENs (or fewer if the
        cluster has fewer total positions).
    provenance
        Dict describing the PGN training run:
        ``{'pgn_path', 'max_games', 'positions_per_phase', 'seed',
        'training_position_count', 'cluster_counts'}``. Stamped into
        the bench output's top level for reproducibility.

    Raises
    ------
    ValueError
        If a phase-cluster has zero positions (classifier failed to
        recover all three phases). Caller should retry with a larger
        ``max_games`` or different PGN.
    """
    from chess_spectral.phase_classifier import (
        train_phase_classifier_from_pgn,
    )

    classifier, labeled = train_phase_classifier_from_pgn(
        pgn_path,
        max_games=max_games,
        sample_every=sample_every,
        skip_initial_plies=skip_initial_plies,
        seed=seed,
    )

    # Group FENs by phase label.
    fens_by_phase: Dict[str, List[str]] = {
        'opening': [], 'midgame': [], 'endgame': [],
    }
    for fen, _fp, cluster in labeled:
        phase = classifier.phase_map[cluster]
        fens_by_phase[phase].append(fen)

    cluster_counts = {
        phase: len(fens) for phase, fens in fens_by_phase.items()
    }

    # Validate every phase has at least one FEN — classifier should
    # always recover all three on real PGN data, but guard for the
    # degenerate "all-opening" or empty-corpus cases.
    for phase, fens in fens_by_phase.items():
        if not fens:
            raise ValueError(
                f"PGN-sourced corpus has zero positions for phase "
                f"{phase!r} (classifier counts={cluster_counts}). "
                f"Try a larger --pgn-max-games or a different PGN."
            )

    # Deterministic per-phase sampling via random.Random(seed).
    sampler = random.Random(seed)
    sampled_corpora: Dict[str, List[str]] = {}
    for phase in ('opening', 'midgame', 'endgame'):
        candidates = fens_by_phase[phase]
        n = min(positions_per_phase, len(candidates))
        # sort first for stable ordering across runs (PGN walk order
        # is deterministic but sampler-without-list-sort still varies
        # by interpreter ordering whims if the upstream changes).
        candidates_sorted = sorted(candidates)
        sampled_corpora[phase] = sampler.sample(candidates_sorted, n)

    provenance = {
        "source": "pgn",
        "pgn_path": str(pgn_path),
        "max_games": max_games,
        "positions_per_phase": positions_per_phase,
        "seed": seed,
        "sample_every": sample_every,
        "skip_initial_plies": skip_initial_plies,
        "training_position_count": len(labeled),
        "cluster_counts": cluster_counts,
        "phase_map": {str(k): v for k, v in classifier.phase_map.items()},
    }
    return sampled_corpora, provenance


# ─── Variant registry ───────────────────────────────────────────────


# Each variant: (description, evaluator_callable). The callable
# takes (pos: dict, side_to_move: bool) -> float to match the
# search core's evaluator signature. Variants that need precomputed
# state (e.g., hybrid encoding, TT cache) capture it via closure
# inside the registration helper.

VARIANTS: Dict[str, "tuple[str, Callable[[dict, bool], float]]"] = {}


def _register(name: str, description: str):
    """Decorator: register a (name, description, fn) variant.

    The callable signature is ``(position_dict, side_to_move_bool) ->
    float``. Variants that need precomputed state should capture it
    in the registration body.
    """
    def decorator(fn):
        VARIANTS[name] = (description, fn)
        return fn
    return decorator


@_register(
    "material",
    "Phase 6.1.1 material-only baseline. No encoder call — integer addition.",
)
def _eval_material(pos: dict, side: bool) -> float:
    from chess_spectral.engine.eval import material
    return material.evaluate(pos, side)


@_register(
    "spectral_float64",
    "Current spectral channel-energy path (encoder → float64 → "
    "numpy sum-of-squares per channel). The 1.0-1.12.x default.",
)
def _eval_spectral_float64(pos: dict, side: bool) -> float:
    from chess_spectral.engine.eval import spectral
    return spectral.evaluate(pos, side)


@_register(
    "qm",
    "QM expectation evaluator. Most expensive reference; included "
    "to bound the upper end of the bench-cost range.",
)
def _eval_qm(pos: dict, side: bool) -> float:
    try:
        from chess_spectral.engine.eval import qm
    except ImportError:
        # qm evaluator may not be present on minimal installs.
        return 0.0
    return qm.evaluate(pos, side)


# Variants (d), (a), (b), (c) are added by separate registration
# blocks below as their implementations land. Until they exist, this
# benchmark serves as the BEFORE-state reference and surfaces the
# baseline cost of each existing evaluator family.

try:
    from chess_spectral.engine.eval import spectral_float32
    @_register(
        "spectral_float32",
        "(d) float32 downstream variant: mirrors the ephemerides "
        "two-stage architecture by computing channel energies in "
        "float32 instead of float64. 1.13.0+.",
    )
    def _eval_spectral_float32(pos: dict, side: bool) -> float:
        return spectral_float32.evaluate(pos, side)
except ImportError:
    pass  # Not yet implemented — bench skips silently.


try:
    from chess_spectral.engine.eval import spectral_hybrid
    from chess_spectral.encoder_bip_hybrid import encode_2d_bip_hybrid

    @_register(
        "spectral_hybrid_8bit_full",
        "(a) channel-energy-from-hybrid, FULL path: encode the "
        "position to hybrid then evaluate. Bench-comparable to "
        "spectral_float64 — measures the full encode+eval cost. "
        "Expected modest speedup since encode dominates. 1.13.0+.",
    )
    def _eval_spectral_hybrid_8bit_full(pos: dict, side: bool) -> float:
        return spectral_hybrid.evaluate(pos, side, magnitude_bits=8)

    @_register(
        "spectral_hybrid_8bit_from_cache",
        "(a) channel-energy-from-hybrid, CACHE-HIT path: evaluator "
        "is given a precomputed hybrid (skip encode entirely). "
        "Measures the §16 TT-cache-hit cost. Expected ~10-100× "
        "speedup vs the full encode+eval path. 1.13.0+.",
    )
    def _eval_spectral_hybrid_8bit_from_cache(pos: dict,
                                              side: bool) -> float:
        # Closure-capture: precompute the hybrid once outside the
        # bench loop. The bench's _bench_one warmup runs this 5
        # times before timing — those warmups also pay the encode
        # cost; but the timed iterations re-use a cached hybrid
        # via a module-level dict keyed by id(pos).
        cached = _hybrid_cache_2d.get(id(pos))
        if cached is None:
            cached = encode_2d_bip_hybrid(pos, magnitude_bits=8)
            _hybrid_cache_2d[id(pos)] = cached
        return spectral_hybrid.evaluate_from_hybrid(cached, side)

    # Per-id cache; populated on first call per position. Mimics
    # the §16 TT cache hit pattern at the bench level.
    _hybrid_cache_2d: Dict[int, object] = {}

except ImportError:
    pass  # Not yet implemented.


try:
    from chess_spectral.encoder_pure_phase import (
        encode_2d_pure_phase_to_float,
    )
    from chess_spectral.engine.eval.spectral import (
        DEFAULT_WEIGHTS, channel_energies, _resolve_weights,
    )
    from chess_spectral.engine.eval.spectral import _CHANNEL_NAMES as _CN_SPEC

    @_register(
        "spectral_pure_phase",
        "(B-spike-4) pure-phase encoder: integer arithmetic "
        "throughout encode + dequantize at output. Returns float64 "
        "for parity with spectral_float64. 1.14.0+.",
    )
    def _eval_spectral_pure_phase(pos: dict, side: bool) -> float:
        v = encode_2d_pure_phase_to_float(pos)
        energies = channel_energies(v)
        score = 0.0
        for name in _CN_SPEC:
            score += DEFAULT_WEIGHTS.get(name, 1.0) * energies[name]
        if not side:
            score = -score
        return float(score)

except ImportError:
    pass


try:
    from chess_spectral.engine.eval.spectral_hybrid_cache import (
        make_cached_evaluator,
    )

    # Build a single shared cached evaluator. The cache warms up
    # over the bench iterations; first call per position misses,
    # subsequent ~999 calls hit. Models the steady-state of a
    # search with high TT hit rate.
    _cached_eval_fn, _cached_eval_cache = make_cached_evaluator(
        magnitude_bits=8, cache_size=1024)

    @_register(
        "spectral_hybrid_8bit_lru",
        "(b) hybrid + LRU cache: cache-aware evaluator that looks "
        "up the position-hash key in an in-process LRU. First call "
        "per position misses (full encode+eval cost); subsequent "
        "calls hit (~25× faster). Models the §16 TT-cache-hit "
        "steady state. 1.13.0+.",
    )
    def _eval_spectral_hybrid_8bit_lru(pos: dict, side: bool) -> float:
        return _cached_eval_fn(pos, side)

except ImportError:
    pass  # Not yet implemented.


# ─── Benchmark machinery ─────────────────────────────────────────────


def _fen_to_pos_side(fen: str) -> "tuple[dict, bool]":
    """Convert a FEN to (encoder-format pos dict, side_to_move bool).

    Side-to-move parsing follows the standard FEN convention: field
    [1] is 'w' (white) or 'b' (black).
    """
    from chess_spectral import fen_to_pos
    parts = fen.split()
    side_white = parts[1] == "w" if len(parts) > 1 else True
    return fen_to_pos(fen), side_white


def _bench_one(fn: Callable, pos: dict, side: bool,
               iters: int) -> Dict[str, float]:
    """Time ``fn(pos, side)`` over ``iters`` calls; return mean /
    median / p95 in microseconds.

    Warm-up: 5 calls before timing to amortize one-shot table loads
    + any JIT / import side effects.
    """
    # Warm up
    for _ in range(5):
        fn(pos, side)

    times_us: List[float] = []
    for _ in range(iters):
        t0 = time.perf_counter()
        fn(pos, side)
        t1 = time.perf_counter()
        times_us.append((t1 - t0) * 1e6)

    times_us.sort()
    p95_idx = min(len(times_us) - 1, int(0.95 * len(times_us)))
    return {
        "mean_us": statistics.mean(times_us),
        "median_us": statistics.median(times_us),
        "p95_us": times_us[p95_idx],
        "min_us": times_us[0],
        "max_us": times_us[-1],
        "iters": iters,
    }


def _format_us(seconds_us: float) -> str:
    """Format a microsecond value as a fixed-width string."""
    return f"{seconds_us:8.2f}"


def run_bench(
    variants: Optional[List[str]] = None,
    corpora: Optional[List[str]] = None,
    iters: int = 500,
    *,
    corpus_overrides: Optional[Dict[str, List[str]]] = None,
    corpus_provenance: Optional[Dict[str, object]] = None,
) -> Dict[str, object]:
    """Run the benchmark across selected variants × corpora.

    Parameters
    ----------
    variants
        Variant names from :data:`VARIANTS`. ``None`` → all
        registered.
    corpora
        Corpus names from :data:`CORPORA` (``"opening"`` /
        ``"midgame"`` / ``"endgame"``). ``None`` → all.
    iters
        Iterations per (variant × position) call site.
    corpus_overrides
        Optional dict ``{phase: [fen, ...]}``. When supplied, replaces
        the hand-picked :data:`CORPORA` lookup for the duration of
        this call. Used by the PGN-sourced corpus path (1.19.0+).
    corpus_provenance
        Optional metadata describing where the corpora came from.
        Stamped into the result dict's ``corpus_provenance`` key for
        reproducibility / CI artifact diffs.

    Returns
    -------
    dict
        Structured results suitable for JSON dump. Top-level keys:

          * ``"variants"``: list of variant names actually run
          * ``"corpora"``: list of corpus names actually run
          * ``"iters"``: iteration count
          * ``"results"``: nested dict
            ``{variant: {corpus: {fen: {mean_us, median_us, p95_us, ...}}}}``
          * ``"summary"``: per-(variant, corpus) median-of-medians
            for the headline table
          * ``"corpus_provenance"`` (1.19.0+): if supplied, the
            classifier-training metadata; else ``{"source": "hand_picked"}``.
    """
    corpus_lookup: Dict[str, List[str]] = (
        corpus_overrides if corpus_overrides is not None else CORPORA
    )
    chosen_variants = variants if variants else list(VARIANTS.keys())
    chosen_corpora = corpora if corpora else list(corpus_lookup.keys())

    # Filter to available variants only.
    chosen_variants = [v for v in chosen_variants if v in VARIANTS]

    results: Dict[str, Dict[str, Dict[str, Dict[str, float]]]] = {}
    summary: Dict[str, Dict[str, float]] = {}

    for variant_name in chosen_variants:
        _, fn = VARIANTS[variant_name]
        results[variant_name] = {}
        summary[variant_name] = {}
        for corpus_name in chosen_corpora:
            results[variant_name][corpus_name] = {}
            corpus_medians: List[float] = []
            for fen in corpus_lookup[corpus_name]:
                pos, side = _fen_to_pos_side(fen)
                stats = _bench_one(fn, pos, side, iters)
                results[variant_name][corpus_name][fen] = stats
                corpus_medians.append(stats["median_us"])
            summary[variant_name][corpus_name] = float(
                statistics.median(corpus_medians))

    provenance = (
        corpus_provenance if corpus_provenance is not None
        else {"source": "hand_picked"}
    )
    return {
        "variants": chosen_variants,
        "corpora": chosen_corpora,
        "iters": iters,
        "results": results,
        "summary": summary,
        "corpus_provenance": provenance,
    }


def _print_summary_table(bench: Dict[str, object]) -> None:
    """Print a human-readable summary table of median-of-medians
    per (variant, corpus) cell."""
    summary = bench["summary"]
    corpora = bench["corpora"]

    # Header
    name_w = max(len(v) for v in summary) if summary else 20
    name_w = max(name_w, 24)

    print()
    print(f"=== Spectral evaluator benchmark (iters={bench['iters']}, "
          f"median of per-position medians, µs) ===\n")
    header = f"{'Variant':<{name_w}} | "
    header += " | ".join(f"{c:>10}" for c in corpora)
    print(header)
    print("-" * len(header))

    # Find the fastest variant per corpus for ratio reporting.
    fastest_per_corpus = {}
    for c in corpora:
        cell_values = [summary[v][c] for v in summary if c in summary[v]]
        if cell_values:
            fastest_per_corpus[c] = min(cell_values)

    for variant_name, by_corpus in summary.items():
        cells = []
        for c in corpora:
            us = by_corpus.get(c)
            if us is None:
                cells.append("       n/a")
                continue
            fastest = fastest_per_corpus.get(c, us)
            ratio = us / fastest if fastest > 0 else 1.0
            if ratio == 1.0:
                cells.append(f"{_format_us(us)} *")  # fastest marker
            else:
                cells.append(f"{_format_us(us)} ")
        print(f"{variant_name:<{name_w}} | " + " | ".join(cells))

    print()
    print("Notes:")
    print("  * * marks the fastest variant per corpus (lower = faster).")
    print("  * Cells are median-of-medians across each corpus's positions.")
    print("  * Variants not yet implemented are silently skipped (see")
    print("    module docstring for the registry).")
    print()


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Diagnostic benchmark for spectral evaluator variants. "
            "Locks the BEFORE / AFTER measurement discipline for the "
            "1.13.0 B-spike-3 work — no speedup claim ships in the "
            "CHANGELOG without a measured delta from this harness."
        ),
    )
    ap.add_argument(
        "--iters", type=int, default=500,
        help="iterations per (variant × position) call site "
             "(default: 500)",
    )
    ap.add_argument(
        "--variants", default="all",
        help="comma-separated variant names from the registry, or "
             "'all' (default). Unknown names are dropped silently.",
    )
    ap.add_argument(
        "--corpora", default="all",
        help="comma-separated corpus names ('opening','midgame',"
             "'endgame'), or 'all' (default).",
    )
    ap.add_argument(
        "-o", "--output", default=None,
        help="write structured JSON results to FILE (in addition to "
             "the stdout summary table).",
    )
    ap.add_argument(
        "--quiet", action="store_true",
        help="Suppress the human-readable summary table on stdout. "
             "Use with --output for CI / programmatic consumers. "
             "(1.19.0+).",
    )
    ap.add_argument(
        "--pgn-corpus", default=None,
        help="(1.19.0+) Path to a PGN file. If set, train the "
             "phase classifier from chess_spectral.phase_classifier "
             "on the PGN, sample N FENs deterministically per "
             "phase-cluster, and use those instead of the hand-picked "
             "OPENING/MIDGAME/ENDGAME_FENS lists. The bench machinery "
             "is otherwise unchanged.",
    )
    ap.add_argument(
        "--pgn-max-games", type=int, default=100,
        help="(1.19.0+) Cap on games walked for classifier training. "
             "Default 100. Only used when --pgn-corpus is set.",
    )
    ap.add_argument(
        "--pgn-positions-per-phase", type=int, default=5,
        help="(1.19.0+) Number of FENs sampled per phase-cluster. "
             "Default 5 (matches the hand-picked corpus size). "
             "Only used when --pgn-corpus is set.",
    )
    ap.add_argument(
        "--pgn-seed", type=int, default=42,
        help="(1.19.0+) Seed for the deterministic FEN sampler AND "
             "for the k-means initialization. Same seed → same "
             "sampled FENs, given the same PGN. Default 42.",
    )
    args = ap.parse_args(argv)

    if args.variants == "all":
        variants = None
    else:
        variants = [v.strip() for v in args.variants.split(",") if v.strip()]

    if args.corpora == "all":
        corpora = None
    else:
        corpora = [c.strip() for c in args.corpora.split(",") if c.strip()]

    corpus_overrides: Optional[Dict[str, List[str]]] = None
    corpus_provenance: Optional[Dict[str, object]] = None
    if args.pgn_corpus:
        corpus_overrides, corpus_provenance = build_pgn_sourced_corpora(
            args.pgn_corpus,
            max_games=args.pgn_max_games,
            positions_per_phase=args.pgn_positions_per_phase,
            seed=args.pgn_seed,
        )
        if not args.quiet:
            counts = corpus_provenance["cluster_counts"]
            print(
                f"PGN corpus: {args.pgn_corpus} "
                f"({corpus_provenance['training_position_count']} "
                f"training positions; "
                f"opening={counts.get('opening', 0)}, "
                f"midgame={counts.get('midgame', 0)}, "
                f"endgame={counts.get('endgame', 0)}). "
                f"Sampling {args.pgn_positions_per_phase} per phase, "
                f"seed={args.pgn_seed}."
            )

    bench = run_bench(
        variants=variants,
        corpora=corpora,
        iters=args.iters,
        corpus_overrides=corpus_overrides,
        corpus_provenance=corpus_provenance,
    )
    if not args.quiet:
        _print_summary_table(bench)

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(
            json.dumps(bench, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        if not args.quiet:
            print(f"Wrote structured results to {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
