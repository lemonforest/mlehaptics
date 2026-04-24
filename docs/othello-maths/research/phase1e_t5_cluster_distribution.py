"""Open item 3 — §10.10 T5 FK-BC flank-cluster size distribution.

T1 (phase1e_flipcount_distribution) measured the per-MOVE flip
count distribution (an exponential, rejecting power-law).  T5
moves up a level: per-POSITION, extract the set of flanking-chain
sizes (maximal same-colour runs bracketed by opponent or boundary
along each ray) and fit to FK-Blume-Capel cluster-size scaling.

Chain definition
----------------

Walking from a disc at (r, c) along ray direction d, a "chain"
is the maximal run of same-colour cells ending where the next
cell is opponent or empty or out-of-bounds.  We extract chains
from the friendly perspective:

    For each disc at v and each direction d:
      if s(v+d) != s(v): skip (no continuation)
      walk until hit end; record chain_length >= 2

Chains are double-counted if we iterate both endpoints.  We
de-duplicate by keeping only the (origin, direction) where
origin is the lexicographically-smallest cell along the chain.

Fits
----

Per-corpus (aggregated across all ply positions), the chain-length
distribution is compared against two candidate models:

  Exponential:  P(n) ∝ exp(-lambda * n)
  Power-law:    P(n) ∝ n^(-tau)    (FK-BC prediction)

AIC selects the better fit.  A power-law preference would be
consistent with §10.10 T5's FK-Blume-Capel clustering
expectation (tau ≈ 2 at the percolation-critical point in 2D).
"""

from __future__ import annotations

__version__ = "0.2.0"

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

from othello_pgn_loader import (
    _ensure_utf8_stdio, parse_pgn_file, replay,
)
from othello_utils import (
    BLACK, BOARD_SIZE, N, RAY_OFFSETS, in_bounds, rc_to_idx, idx_to_rc,
)

_ensure_utf8_stdio()


def chains_of_state(state: np.ndarray) -> list[int]:
    """Extract all same-colour chains of length >= 2 from this state.

    Chain = maximal run of same-coloured cells along a single ray.
    De-duplicated by keeping only the chain starting at the
    smallest-index endpoint.
    """
    chains: list[int] = []
    for v in range(N):
        s_v = int(state[v])
        if s_v == 0:
            continue
        v_r, v_c = idx_to_rc(v)
        for d_name, (dr, dc) in RAY_OFFSETS.items():
            # Consider only rays whose step direction is 'forward'
            # in index order, and where the immediate neighbour is
            # also friendly: we're looking for chain starts.  A
            # chain "starts" at the cell whose predecessor (-d)
            # is NOT friendly (opp, empty, or out-of-bounds).
            pr, pc = v_r - dr, v_c - dc
            if in_bounds(pr, pc):
                prev_idx = rc_to_idx(pr, pc)
                if int(state[prev_idx]) == s_v:
                    continue  # not a start
            # Walk forward and count
            r, c = v_r, v_c
            length = 0
            while in_bounds(r, c) and int(
                state[rc_to_idx(r, c)]
            ) == s_v:
                length += 1
                r += dr
                c += dc
            if length >= 2:
                chains.append(length)
    return chains


def _fit_exponential(lengths: np.ndarray) -> dict:
    k = lengths
    if k.size == 0:
        return {"lambda": None, "aic": None, "n": 0}
    mean = float(k.mean())
    # Shifted-geometric: n >= 2 support.
    # MLE for shifted geometric on {2, 3, ...} : lambda = -ln p,
    # p_hat = 1 - 1/(mean-1) approximately.
    p_hat = 1.0 - 1.0 / max(mean - 1.0, 1e-6)
    p_hat = min(max(p_hat, 1e-6), 1.0 - 1e-6)
    lam = -math.log(p_hat)
    loglik = np.sum(np.log((1 - p_hat) * p_hat ** (k - 2)))
    aic = 2.0 * 1 - 2.0 * float(loglik)
    return {
        "lambda": float(lam), "p_hat": float(p_hat),
        "mean": mean, "aic": aic, "n": int(k.size),
    }


def _fit_power_law_discrete(lengths: np.ndarray, n_min: int = 2) -> dict:
    k = lengths[lengths >= n_min]
    if k.size == 0:
        return {"tau": None, "aic": None, "n": 0}
    n = k.size
    tau = 1.0 + n / np.sum(np.log(k / (n_min - 0.5)))
    obs_max = int(np.max(k))
    support = np.arange(n_min, obs_max + 1)
    norm = float(np.sum(support ** -tau))
    loglik = np.sum(-tau * np.log(k)) - n * math.log(norm)
    aic = 2.0 * 1 - 2.0 * float(loglik)
    return {
        "tau": float(tau), "n_min": n_min, "n_max_observed": obs_max,
        "aic": aic, "n": int(k.size),
    }


def analyze_corpus(pgn_path: Path) -> dict:
    games = parse_pgn_file(pgn_path)
    chains: list[int] = []
    n_positions = 0
    n_games_ok = 0
    for g in games:
        try:
            _, states, _ = replay(g["moves"])
        except Exception:
            continue
        n_games_ok += 1
        for st in states:
            n_positions += 1
            chains.extend(chains_of_state(st))
    arr = np.array(chains, dtype=int)
    meta = {
        "corpus": str(pgn_path),
        "n_games_replayed": n_games_ok,
        "n_positions_scanned": n_positions,
        "n_chains": int(arr.size),
    }
    if arr.size == 0:
        return {**meta, "error": "no chains"}
    histogram = {int(n): int(np.sum(arr == n)) for n in range(2, 9)}
    # Tail above 8
    tail = int(np.sum(arr > 8))
    if tail:
        histogram["9+"] = tail
    summary = {
        **meta,
        "mean": float(arr.mean()),
        "std":  float(arr.std()),
        "max":  int(arr.max()),
        "histogram": histogram,
        "fit_exponential": _fit_exponential(arr),
        "fit_power_law":   _fit_power_law_discrete(arr, n_min=2),
    }
    e_aic = summary["fit_exponential"].get("aic")
    p_aic = summary["fit_power_law"].get("aic")
    if e_aic is not None and p_aic is not None:
        summary["preferred"] = (
            "power_law" if p_aic < e_aic else "exponential"
        )
        summary["aic_diff_pl_minus_exp"] = p_aic - e_aic
    return summary


def _build_parser():
    default_results = (
        Path(__file__).resolve().parent.parent / "results"
    )
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # Default: all 4 committed corpora.
  python research/phase1e_t5_cluster_distribution.py

  # Single corpus.
  python research/phase1e_t5_cluster_distribution.py \\
      --pgn ../dataset/liveothello_World_Championships_2005.pgn

reading the output:
  'preferred' picks the lower-AIC fit.  A power-law preference at
  tau ~ 2 would match the 2D-FK-BC percolation-critical expectation
  (§10.10 T5).  An exponential preference at all corpora (mirroring
  T1's per-move result) would rule out critical FK-BC clustering
  at the chain level, matching a sub-critical regime.
""",
    )
    default_pgns = [
        "../dataset/liveothello_Barcelona_EGP_2026.pgn",
        "../dataset/liveothello_World_Championships_2005.pgn",
        "../dataset/liveothello-2026-APR.pgn",
        "../dataset/liveothello_2025_all.pgn",
    ]
    p.add_argument(
        "--pgn", type=Path, action="append", default=None,
        help="PGN to analyse.  Repeatable.  Default: 4 corpora.",
    )
    p.add_argument(
        "--out", type=Path,
        default=default_results / "phase1e_t5_cluster_distribution.json",
    )
    return p


def main(argv=None):
    args = _build_parser().parse_args(argv)
    research_dir = Path(__file__).resolve().parent
    if args.pgn is None:
        pgns = [
            research_dir.parent / "dataset" / fn for fn in [
                "liveothello_Barcelona_EGP_2026.pgn",
                "liveothello_World_Championships_2005.pgn",
                "liveothello-2026-APR.pgn",
                "liveothello_2025_all.pgn",
            ]
        ]
    else:
        pgns = args.pgn
    all_summaries = {}
    for pgn in pgns:
        if not pgn.exists():
            print(f"skip (not found): {pgn}")
            continue
        print(f"\n=== {pgn.name} ===")
        s = analyze_corpus(pgn)
        all_summaries[pgn.stem] = s
        print(f"  n_games_replayed:   {s.get('n_games_replayed', '?')}")
        print(f"  n_positions:        {s.get('n_positions_scanned', '?')}")
        print(f"  n_chains:           {s.get('n_chains', '?')}")
        if "mean" in s:
            print(
                f"  mean length = {s['mean']:.3f}  std = {s['std']:.3f}  "
                f"max = {s['max']}"
            )
            pl = s["fit_power_law"]
            ex = s["fit_exponential"]
            print(f"  power-law tau = {pl['tau']:.3f}  AIC = {pl['aic']:.1f}")
            print(f"  exponential lambda = {ex['lambda']:.3f}  AIC = {ex['aic']:.1f}")
            if "preferred" in s:
                print(
                    f"  preferred: {s['preferred']}  "
                    f"(AIC diff = {s['aic_diff_pl_minus_exp']:+.1f})"
                )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        json.dump(all_summaries, f, indent=2)
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
