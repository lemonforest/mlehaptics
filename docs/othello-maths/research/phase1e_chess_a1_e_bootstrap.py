"""Follow-up iv — chess drnykterstein_N10 small-sample bootstrap probe.

Open-7 pooled chess Pearson(E_A1, E_E) = +0.041 (null overall),
but drnykterstein_N10 registered -0.2013 while ashchess_N50 gave
+0.0106 and hf_N50 gave +0.1157.  Is the drnykterstein value a
small-sample fluke or a player-specific signature?

Two diagnostics:
  1. Per-game Pearson distribution across each corpus (50 and 10
     values per corpus).  If per-game Pearsons are widely spread
     with both signs, the corpus mean is noise.  If they cluster
     at a non-zero value, the effect is real at the player/corpus
     level.
  2. Bootstrap: resample 10 random games from ashchess_N50 (1000
     times), compute Pearson on each resampled pool, get the
     distribution.  Check whether -0.20 lies in a plausible tail.

Outputs: results/phase1e_chess_a1_e_bootstrap.json
"""

from __future__ import annotations

__version__ = "0.2.0"

import argparse
import glob
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr

_CHESS_PYTHON = (
    Path(__file__).resolve().parent.parent.parent
    / "chess-maths" / "chess-spectral" / "python"
)
if str(_CHESS_PYTHON) not in sys.path:
    sys.path.insert(0, str(_CHESS_PYTHON))

from chess_spectral.frame import read_all  # noqa: E402


def _energies_per_game(path: str) -> tuple[np.ndarray, np.ndarray]:
    _, frames = read_all(path)
    a1 = np.array(
        [
            np.dot(fr.encoding[:64], fr.encoding[:64])
            for fr in frames
        ], dtype=np.float64,
    )
    e = np.array(
        [
            np.dot(fr.encoding[4 * 64:5 * 64], fr.encoding[4 * 64:5 * 64])
            for fr in frames
        ], dtype=np.float64,
    )
    return a1, e


def analyse(corpora: list[tuple[str, str]]) -> dict:
    per_corpus: dict[str, dict] = {}
    per_corpus_raw: dict[str, list[tuple[np.ndarray, np.ndarray]]] = {}
    for tag, pattern in corpora:
        print(f"\n=== {tag} ===")
        files = sorted(glob.glob(pattern))
        per_game_pearson: list[float] = []
        per_game_n: list[int] = []
        game_arrays: list[tuple[np.ndarray, np.ndarray]] = []
        for p in files:
            try:
                a1, e = _energies_per_game(p)
            except Exception as exc:
                print(f"  skip {Path(p).name}: {exc}")
                continue
            if len(a1) < 10 or a1.std() < 1e-9 or e.std() < 1e-9:
                continue
            pr = pearsonr(a1, e)
            per_game_pearson.append(float(pr.statistic))
            per_game_n.append(int(len(a1)))
            game_arrays.append((a1, e))
        arr = np.array(per_game_pearson)
        per_corpus[tag] = {
            "n_games": int(len(arr)),
            "n_plies_total": int(np.sum(per_game_n)),
            "per_game_pearson": {
                "mean":   float(arr.mean()) if arr.size else None,
                "median": float(np.median(arr)) if arr.size else None,
                "std":    float(arr.std()) if arr.size else None,
                "min":    float(arr.min()) if arr.size else None,
                "max":    float(arr.max()) if arr.size else None,
            },
            "pooled_pearson": None,
        }
        per_corpus_raw[tag] = game_arrays
        if game_arrays:
            all_a1 = np.concatenate([g[0] for g in game_arrays])
            all_e = np.concatenate([g[1] for g in game_arrays])
            pr = pearsonr(all_a1, all_e)
            per_corpus[tag]["pooled_pearson"] = {
                "r": float(pr.statistic),
                "p": float(pr.pvalue),
                "n_plies": int(len(all_a1)),
            }
        print(f"  n_games: {per_corpus[tag]['n_games']}  n_plies: {per_corpus[tag]['n_plies_total']}")
        if per_corpus[tag]["pooled_pearson"]:
            print(f"  pooled r = {per_corpus[tag]['pooled_pearson']['r']:+.4f}")
        pgm = per_corpus[tag]["per_game_pearson"]
        print(f"  per-game r:  mean = {pgm['mean']:+.4f}  "
              f"median = {pgm['median']:+.4f}  "
              f"range = [{pgm['min']:+.3f}, {pgm['max']:+.3f}]")

    # --- Bootstrap: resample 10 games from ashchess_N50 ---
    if "ashchess_N50" in per_corpus_raw:
        source = per_corpus_raw["ashchess_N50"]
        rng = np.random.default_rng(42)
        n_trials = 1000
        sample_size = 10
        pooled_rs = []
        for _ in range(n_trials):
            idx = rng.choice(len(source), size=sample_size, replace=True)
            a1s = np.concatenate([source[i][0] for i in idx])
            es = np.concatenate([source[i][1] for i in idx])
            if a1s.std() > 0 and es.std() > 0:
                pooled_rs.append(float(pearsonr(a1s, es).statistic))
        pooled_rs = np.array(pooled_rs)
        boot = {
            "n_trials": int(len(pooled_rs)),
            "sample_size": sample_size,
            "source_corpus": "ashchess_N50",
            "mean":      float(pooled_rs.mean()),
            "median":    float(np.median(pooled_rs)),
            "std":       float(pooled_rs.std()),
            "quantiles": {
                "2.5%":  float(np.percentile(pooled_rs, 2.5)),
                "25%":   float(np.percentile(pooled_rs, 25)),
                "50%":   float(np.percentile(pooled_rs, 50)),
                "75%":   float(np.percentile(pooled_rs, 75)),
                "97.5%": float(np.percentile(pooled_rs, 97.5)),
            },
        }
        # Where does drnykterstein's -0.20 sit?
        dr_pooled = per_corpus.get("drnykterstein_N10", {}).get(
            "pooled_pearson", {}
        )
        if dr_pooled:
            target = dr_pooled["r"]
            percentile = float(
                np.mean(pooled_rs <= target) * 100.0
            )
            boot["drnykterstein_observed"] = target
            boot["drnykterstein_percentile_in_null"] = percentile
            print(f"\n=== Bootstrap (resample 10 from ashchess_N50, 1000 trials) ===")
            print(f"  mean   = {boot['mean']:+.4f}")
            print(f"  median = {boot['median']:+.4f}")
            print(f"  std    = {boot['std']:.4f}")
            print(f"  2.5-97.5 percentile: "
                  f"[{boot['quantiles']['2.5%']:+.4f}, "
                  f"{boot['quantiles']['97.5%']:+.4f}]")
            print(f"\n  drnykterstein observed Pearson = {target:+.4f}")
            print(f"  percentile in null (fraction of bootstrap <= observed) = {percentile:.2f}%")
            if percentile < 2.5:
                print("  ~> drnykterstein value is BELOW the 2.5th percentile of the null; unusually low.")
            elif percentile > 97.5:
                print("  ~> drnykterstein value is ABOVE the 97.5th percentile; unusually high.")
            else:
                print("  ~> drnykterstein value is WITHIN the 95% null interval; plausible under small-sample noise.")
        return {
            "per_corpus": per_corpus,
            "bootstrap": boot,
        }
    return {"per_corpus": per_corpus}


def _build_parser():
    default_out = (
        Path(__file__).resolve().parent.parent / "results"
        / "phase1e_chess_a1_e_bootstrap.json"
    )
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--out", type=Path, default=default_out)
    return p


def main(argv=None):
    args = _build_parser().parse_args(argv)
    research_dir = Path(__file__).resolve().parent
    results_root = research_dir.parent.parent / "chess-maths" / "results"
    corpora = [
        (
            "ashchess_N50",
            str(results_root / "sweep_chain_lichess_ashchess_2026-04-21_N50" / "spectralz" / "game_*.spectralz"),
        ),
        (
            "drnykterstein_N10",
            str(results_root / "sweep_chain_lichess_drnykterstein_2026-04-14_N10" / "spectralz" / "game_*.spectralz"),
        ),
        (
            "hf_N50",
            str(results_root / "sweep_hf_2026-04-20_N50" / "spectralz" / "game_*.spectralz"),
        ),
    ]
    summary = analyse(corpora)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
