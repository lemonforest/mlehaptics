"""Open item 7 — chess-side A1/E Plancherel pair check.

The Othello §2d.c / §2d.e finding: D4-A1(s^2) and D4-E(s^2) are
near-mirror anti-correlated channels with Pearson = -0.834 on the
50-empty static corpus (N = 2587) and ~ -0.07 to -0.14 at
trajectory level across 4 PGN corpora.

The §2d.e analysis framed this as:
  - Othello has only the 5 D4 irrep channels, so A1/E share the
    full Plancherel norm budget and anticorrelate tightly.
  - Chess has 10 channels (5 D4 + 5 fiber: F1, F2, F3, FA, FD), so
    A1/E share their Plancherel budget with the fiber channels,
    and the anticorrelation is diluted.

This runner measures Pearson(E_A1, E_E) at trajectory level on all
committed chess spectralz corpora, to empirically confirm the
prediction that chess's mirror is weaker than Othello's.

Outputs: results/phase1e_chess_a1_e_pair.json
"""

from __future__ import annotations

__version__ = "0.2.0"

import argparse
import glob
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr, spearmanr

# Chess spectralz is bundled elsewhere — import path is project-
# relative.  The module exposes read_all() which reads header + all
# frames from a (possibly gzipped) .spectralz file.
_CHESS_PYTHON = (
    Path(__file__).resolve().parent.parent.parent
    / "chess-maths" / "chess-spectral" / "python"
)
if str(_CHESS_PYTHON) not in sys.path:
    sys.path.insert(0, str(_CHESS_PYTHON))

from chess_spectral.frame import read_all  # noqa: E402

# Chess encoder layout: 640 dims = 10 channels x 64.
# Channel order per chess_spectral/csv_export.py.
CHAN_NAMES = ("A1", "A2", "B1", "B2", "E", "F1", "F2", "F3", "FA", "FD")


def _channel_energy(enc: np.ndarray, ch_idx: int) -> float:
    block = enc[ch_idx * 64:(ch_idx + 1) * 64]
    return float(np.dot(block, block))


def scan_corpus(spectralz_glob: str) -> dict:
    files = sorted(glob.glob(spectralz_glob))
    energies: dict[str, list[float]] = {
        name: [] for name in CHAN_NAMES
    }
    n_games = 0
    n_plies = 0
    for p in files:
        try:
            _header, frames = read_all(p)
        except Exception as exc:
            print(f"skip {p}: {exc}", file=sys.stderr)
            continue
        n_games += 1
        for fr in frames:
            enc = np.asarray(fr.encoding, dtype=np.float64)
            for i, name in enumerate(CHAN_NAMES):
                energies[name].append(_channel_energy(enc, i))
            n_plies += 1
    return {
        "n_files": n_games,
        "n_plies": n_plies,
        "energies": {k: np.array(v) for k, v in energies.items()},
    }


def _pair_stats(x: np.ndarray, y: np.ndarray) -> dict:
    if len(x) < 10:
        return {"n": int(len(x))}
    pr = pearsonr(x, y)
    sp = spearmanr(x, y)
    return {
        "n": int(len(x)),
        "pearson_r": float(pr.statistic),
        "pearson_p": float(pr.pvalue),
        "spearman_rho": float(sp.statistic),
        "spearman_p":   float(sp.pvalue),
        "mean_x": float(x.mean()), "mean_y": float(y.mean()),
    }


def analyse_and_report(corpora: list[tuple[str, str]], out_json: Path):
    summary: dict = {"corpora": {}, "pooled": {}}
    pooled: dict[str, list[float]] = {k: [] for k in CHAN_NAMES}
    for tag, pattern in corpora:
        print(f"\n=== {tag} ===")
        data = scan_corpus(pattern)
        print(f"  n_files: {data['n_files']}  n_plies: {data['n_plies']}")
        if data["n_plies"] < 10:
            print("  (skipped, too few plies)")
            continue
        E = data["energies"]
        pair_stats = {
            "A1_vs_E":   _pair_stats(E["A1"], E["E"]),
            "A1_vs_B2":  _pair_stats(E["A1"], E["B2"]),
            "B2_vs_E":   _pair_stats(E["B2"], E["E"]),
            "A1_vs_FA":  _pair_stats(E["A1"], E["FA"]),
            "A1_vs_FD":  _pair_stats(E["A1"], E["FD"]),
            "E_vs_FA":   _pair_stats(E["E"],  E["FA"]),
            "mean_energies": {k: float(v.mean()) for k, v in E.items()},
        }
        summary["corpora"][tag] = {
            "n_files": data["n_files"],
            "n_plies": data["n_plies"],
            "pair_stats": pair_stats,
        }
        # pool
        for k in CHAN_NAMES:
            pooled[k].extend(E[k].tolist())
        # Stdout headline
        p = pair_stats["A1_vs_E"]
        print(
            f"  Pearson(E_A1, E_E)  = {p['pearson_r']:+.4f}  "
            f"p={p['pearson_p']:.2e}"
        )
        p = pair_stats["A1_vs_B2"]
        print(
            f"  Pearson(E_A1, E_B2) = {p['pearson_r']:+.4f}"
        )
        p = pair_stats["B2_vs_E"]
        print(
            f"  Pearson(E_B2, E_E)  = {p['pearson_r']:+.4f}"
        )
    # Pooled
    pool_arrays = {k: np.array(v) for k, v in pooled.items()}
    if len(pool_arrays["A1"]) > 10:
        summary["pooled"] = {
            "n_plies": int(len(pool_arrays["A1"])),
            "A1_vs_E":  _pair_stats(pool_arrays["A1"], pool_arrays["E"]),
            "A1_vs_B2": _pair_stats(pool_arrays["A1"], pool_arrays["B2"]),
            "B2_vs_E":  _pair_stats(pool_arrays["B2"], pool_arrays["E"]),
            "A1_vs_FA": _pair_stats(pool_arrays["A1"], pool_arrays["FA"]),
            "A1_vs_FD": _pair_stats(pool_arrays["A1"], pool_arrays["FD"]),
            "E_vs_FA":  _pair_stats(pool_arrays["E"],  pool_arrays["FA"]),
            "mean_energies": {
                k: float(v.mean()) for k, v in pool_arrays.items()
            },
        }
        p = summary["pooled"]["A1_vs_E"]
        print(
            f"\n=== Pooled (all corpora, N = {summary['pooled']['n_plies']}) ==="
        )
        print(
            f"  Pearson(E_A1, E_E)  = {p['pearson_r']:+.4f}  "
            f"p={p['pearson_p']:.2e}"
        )
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\nwrote {out_json}")


def _build_parser():
    research_dir = Path(__file__).resolve().parent
    default_out = (
        research_dir.parent / "results"
        / "phase1e_chess_a1_e_pair.json"
    )
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  python research/phase1e_chess_a1_e_pair.py

reading the output:
  Pearson(E_A1, E_E) near zero confirms the §2d.e prediction that
  chess's fiber channels (F1, F2, F3, FA, FD) dilute the A1/E
  Plancherel anticorrelation, making it an Othello-specific
  structural property rather than a general 8x8 D4 grid property.

  Report also includes E_A1 vs E_B2 and other cross-channel
  correlations for context.
""",
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
    analyse_and_report(corpora, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
