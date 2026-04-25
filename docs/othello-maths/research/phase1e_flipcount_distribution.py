"""§10.10 T1 — flip-count distribution across PGN corpora.

For every position visited in a corpus, enumerate all legal moves
and record the flip count of each move (number of opponent discs the
move would flip).  Aggregate over the whole corpus and test whether
the distribution is power-law, exponential, or FK-Blume-Capel-like.

Phase 1 (§2.E5) measured this on random-play surrogates (N=7216
candidate moves, mean 2.28, std 1.81, max 13).  Phase 1b (§2b.T1)
did a single-corpus measurement on Barcelona (mean 2.23 +/- 0.70
per-position max).  This runner extends to multi-corpus comparison
with a power-law vs exponential MLE fit.

Two fits are computed (both on the positive-support histogram):

  Exponential:  P(k) ∝ exp(-λ k)   with MLE λ̂ = 1 / (mean_k - 1)
                (shifted-geometric approximation for k >= 1)

  Power-law:    P(k) ∝ k^(-α)      with MLE α̂ using Clauset-Shalizi-
                Newman for discrete data on [1, k_max].

AIC difference reports which fit is preferred.  A substantial
power-law preference is the §10.10 T1 prediction under FK-Blume-
Capel scaling.
"""

from __future__ import annotations

__version__ = "0.2.0"  # paired with othello_spectral v0.2.0

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

from othello_pgn_loader import (
    _ensure_utf8_stdio, parse_pgn_file, replay,
)
from othello_utils import OthelloBoard

_ensure_utf8_stdio()


def _simulate_flip_count(bb: OthelloBoard, move_idx: int) -> int:
    """Return the number of opponent discs that a legal move would
    flip, without mutating the board."""
    clone = bb.copy()
    before_counts = clone.disc_counts()
    clone.play(move_idx)
    after_counts = clone.disc_counts()
    # Mover's discs went up by 1 (placement) + flips; opponent went
    # down by flips.  flips = opp_before - opp_after.
    if bb.side_to_move == 1:  # BLACK
        opp_before = before_counts[1]  # white count
        opp_after = after_counts[1]
    else:
        opp_before = before_counts[0]  # black count
        opp_after = after_counts[0]
    return opp_before - opp_after


def collect_flip_counts(pgn_path: Path) -> tuple[list[int], dict]:
    """Replay every game; at every board state emit one flip-count
    per legal move (not just the chosen move)."""
    games = parse_pgn_file(pgn_path)
    flips: list[int] = []
    n_positions = 0
    n_games_ok = 0
    for g in games:
        try:
            _, states, move_log = replay(g["moves"])
        except Exception:
            continue
        n_games_ok += 1
        for ply, st in enumerate(states):
            bb = OthelloBoard()
            bb.state = st.copy()
            if ply == 0:
                bb.side_to_move = 1  # BLACK opens
            else:
                bb.side_to_move = -move_log[ply - 1]["side"]
            legal = bb.legal_moves()
            if not legal:
                continue
            n_positions += 1
            for mv in legal:
                flips.append(_simulate_flip_count(bb, mv))
    meta = {
        "corpus": str(pgn_path),
        "n_games_requested": len(games),
        "n_games_replayed": n_games_ok,
        "n_positions": n_positions,
        "n_candidate_moves": len(flips),
    }
    return flips, meta


def _fit_exponential(flips: np.ndarray) -> dict:
    if flips.size == 0:
        return {"lambda": None, "aic": None, "n": 0}
    # Shifted-geometric MLE: for values k in {1, 2, ...}
    # P(k) = (1-p) * p^(k-1), mean = 1/(1-p).  lambda = -log(p).
    k = flips[flips >= 1]
    if k.size == 0:
        return {"lambda": None, "aic": None, "n": 0}
    mean = float(np.mean(k))
    p_hat = 1.0 - 1.0 / mean
    p_hat = min(max(p_hat, 1e-6), 1.0 - 1e-6)
    lam = -math.log(p_hat)
    loglik = np.sum(
        np.log((1 - p_hat) * p_hat ** (k - 1))
    )
    aic = 2.0 * 1 - 2.0 * float(loglik)  # 1 free parameter
    return {
        "lambda": float(lam),
        "p_hat": float(p_hat),
        "mean": mean,
        "loglik": float(loglik),
        "aic": aic,
        "n": int(k.size),
    }


def _fit_power_law_discrete(
    flips: np.ndarray, k_min: int = 1, k_max: int | None = None,
) -> dict:
    """Clauset-Shalizi-Newman (2009) discrete-MLE for P(k) ~ k^(-α)
    on k in [k_min, k_max].  Closed form:

        alpha_hat ≈ 1 + n / sum_i log(k_i / (k_min - 0.5))

    (the 0.5 offset is the continuous-approx correction).
    """
    k = flips[flips >= k_min]
    if k_max is not None:
        k = k[k <= k_max]
    if k.size == 0:
        return {"alpha": None, "aic": None, "n": 0}
    n = k.size
    alpha = 1.0 + n / np.sum(np.log(k / (k_min - 0.5)))
    # Approximate AIC using a discrete-zeta likelihood truncation at
    # the observed k_max (closed-form Zeta(alpha) is slow, we use an
    # empirical normaliser over the observed support).
    obs_max = int(np.max(k))
    ks = np.arange(k_min, obs_max + 1)
    normaliser = float(np.sum(ks ** -alpha))
    loglik = np.sum(-alpha * np.log(k)) - n * math.log(normaliser)
    aic = 2.0 * 1 - 2.0 * float(loglik)
    return {
        "alpha": float(alpha),
        "k_min": int(k_min),
        "k_max_observed": obs_max,
        "loglik": float(loglik),
        "aic": aic,
        "n": int(n),
    }


def histogram(flips: np.ndarray, k_max: int = 20) -> dict[int, int]:
    h = {}
    for k in range(0, k_max + 1):
        h[k] = int(np.sum(flips == k))
    tail = int(np.sum(flips > k_max))
    if tail:
        h[f"{k_max + 1}+"] = tail
    return h


def analyze_corpus(pgn_path: Path) -> dict:
    flips_list, meta = collect_flip_counts(pgn_path)
    flips = np.array(flips_list, dtype=int)
    if flips.size == 0:
        return {**meta, "error": "no flips"}
    summary = {
        **meta,
        "mean":   float(flips.mean()),
        "std":    float(flips.std()),
        "max":    int(flips.max()),
        "histogram": histogram(flips, k_max=20),
        "fit_exponential_shifted": _fit_exponential(flips),
        "fit_power_law":           _fit_power_law_discrete(flips, k_min=1),
    }
    # AIC comparison (both on k >= 1 sample)
    exp_aic = summary["fit_exponential_shifted"].get("aic")
    pl_aic = summary["fit_power_law"].get("aic")
    if exp_aic is not None and pl_aic is not None:
        summary["preferred"] = (
            "power_law" if pl_aic < exp_aic else "exponential"
        )
        summary["aic_diff_pl_minus_exp"] = pl_aic - exp_aic
    return summary


def _build_parser():
    default_results = (
        Path(__file__).resolve().parent.parent / "results"
    )
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # Multi-corpus run (default: all 4 PGNs in dataset/).
  python research/phase1e_flipcount_distribution.py

  # Single-corpus probe.
  python research/phase1e_flipcount_distribution.py \\
      --pgn ../dataset/liveothello_World_Championships_2005.pgn

reading the output:
  The 'preferred' field picks the lower-AIC fit.  A power-law
  preference is the §10.10 T1 prediction under FK-Blume-Capel
  scaling; an exponential preference is the standard random-play
  null.
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
        help="PGN to process.  Repeatable.  Default: the 4 committed "
             "liveothello corpora.",
    )
    p.add_argument(
        "--out", type=Path,
        default=default_results / "phase1e_flipcount_distribution.json",
        help="Output JSON path.",
    )
    return p


def main(argv=None):
    args = _build_parser().parse_args(argv)
    research_dir = Path(__file__).resolve().parent
    if args.pgn is None:
        pgns = [
            research_dir.parent / "dataset" / fname
            for fname in [
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
        print(f"  n_games_replayed:  {s.get('n_games_replayed', '?')}")
        print(f"  n_positions:       {s.get('n_positions', '?')}")
        print(f"  n_candidate_moves: {s.get('n_candidate_moves', '?')}")
        if "mean" in s:
            print(
                f"  mean flip = {s['mean']:.3f}  std = {s['std']:.3f}  "
                f"max = {s['max']}"
            )
            pl = s["fit_power_law"]
            ex = s["fit_exponential_shifted"]
            if pl.get("alpha") is not None:
                print(f"  power-law alpha = {pl['alpha']:.3f}  AIC = {pl['aic']:.1f}")
            if ex.get("lambda") is not None:
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
