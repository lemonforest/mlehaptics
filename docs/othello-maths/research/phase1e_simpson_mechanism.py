"""Item 8 — chess Simpson's paradox mechanism.

Open-7/iv found that chess per-game Pearson(E_A1, E_E) is strongly
negative (-0.18 to -0.58 median) while pooled Pearson is near zero
(+0.04 ashchess, +0.12 hf).  The user's hypothesis: between-game
baseline variation dominates the within-game anticorrelation when
pooled.

This runner decomposes the variance using the law of total
covariance.  For random variables A, E with grouping variable G
(game index):

  Cov(A, E) = E[Cov(A, E | G)] + Cov(E[A | G], E[E | G])
           = (within-game covariance, averaged) +
             (between-game covariance of per-game means)

Normalising by (sd_A, sd_E) gives the decomposition of the pooled
Pearson into within-contribution and between-contribution.

If within-game Pearson is strongly negative (~-0.5) and pooled is
near zero, then between-game Pearson of game-means must be
strongly positive, compensating.  The Simpson's paradox then is
"game-level mean shifts of A1 and E are positively correlated
(better games have high mean A1 AND high mean E), but within a
fixed game the two quantities anti-correlate."

Also checks the analogous Othello decomposition to contrast.
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

from chess_spectral.frame import read_all as chess_read_all  # noqa: E402

from othello_spectral import encode_768
from othello_spectral.tables import CHANNEL_NAMES
from othello_pgn_loader import (
    _ensure_utf8_stdio, parse_pgn_file, replay,
)

_ensure_utf8_stdio()


def variance_decomposition(
    xs_per_game: list[np.ndarray], ys_per_game: list[np.ndarray],
) -> dict:
    """Decompose pooled Pearson(X, Y) into within-game and between-game
    contributions.  Returns dict with the three Pearsons and their
    cov/var components.
    """
    # Flatten
    x_all = np.concatenate(xs_per_game)
    y_all = np.concatenate(ys_per_game)
    n_total = len(x_all)
    n_games = len(xs_per_game)

    # Within-game contributions (centred per-game)
    x_cent = []
    y_cent = []
    game_sizes = []
    game_means_x = []
    game_means_y = []
    for xs, ys in zip(xs_per_game, ys_per_game):
        if len(xs) < 2:
            continue
        mx, my = xs.mean(), ys.mean()
        game_sizes.append(len(xs))
        game_means_x.append(mx)
        game_means_y.append(my)
        x_cent.append(xs - mx)
        y_cent.append(ys - my)
    xc_all = np.concatenate(x_cent)
    yc_all = np.concatenate(y_cent)
    game_sizes = np.array(game_sizes)
    game_means_x = np.array(game_means_x)
    game_means_y = np.array(game_means_y)

    # Total variance / covariance
    total_cov = float(np.cov(x_all, y_all, ddof=0)[0, 1])
    total_var_x = float(np.var(x_all, ddof=0))
    total_var_y = float(np.var(y_all, ddof=0))
    pooled_r = total_cov / (
        np.sqrt(total_var_x * total_var_y) + 1e-30
    )

    # Within-group cov / var (sum of centred products / n_total)
    within_cov = float(np.mean(xc_all * yc_all))
    within_var_x = float(np.mean(xc_all ** 2))
    within_var_y = float(np.mean(yc_all ** 2))
    within_r = within_cov / (
        np.sqrt(within_var_x * within_var_y) + 1e-30
    )

    # Between-group cov / var (weighted by game size)
    w = game_sizes / game_sizes.sum()
    mean_mx = float(np.sum(w * game_means_x))
    mean_my = float(np.sum(w * game_means_y))
    between_cov = float(
        np.sum(w * (game_means_x - mean_mx) * (game_means_y - mean_my))
    )
    between_var_x = float(np.sum(w * (game_means_x - mean_mx) ** 2))
    between_var_y = float(np.sum(w * (game_means_y - mean_my) ** 2))
    between_r = between_cov / (
        np.sqrt(between_var_x * between_var_y) + 1e-30
    )

    # Law of total covariance check
    decomposition_cov = within_cov + between_cov
    decomposition_var_x = within_var_x + between_var_x
    decomposition_var_y = within_var_y + between_var_y

    return {
        "n_games": n_games,
        "n_plies_total": n_total,
        "pooled_pearson":  pooled_r,
        "within_pearson":  within_r,
        "between_pearson": between_r,
        "within_covariance":  within_cov,
        "between_covariance": between_cov,
        "pooled_covariance":  total_cov,
        "decomp_check_cov": decomposition_cov,
        "decomp_check_var_x": decomposition_var_x,
        "decomp_check_var_y": decomposition_var_y,
        "within_fraction_of_var_x": within_var_x / total_var_x,
        "within_fraction_of_var_y": within_var_y / total_var_y,
        "within_fraction_of_cov":
            within_cov / total_cov if abs(total_cov) > 1e-12 else None,
    }


def _chess_corpus_per_game(pattern: str) -> list[tuple[np.ndarray, np.ndarray]]:
    """Return list of (A1_energies, E_energies) per chess game."""
    out = []
    for p in sorted(glob.glob(pattern)):
        try:
            _, frames = chess_read_all(p)
        except Exception as exc:
            print(f"  skip {Path(p).name}: {exc}", file=sys.stderr)
            continue
        encs = np.array([fr.encoding for fr in frames])
        a1 = np.sum(encs[:, 0 * 64:1 * 64] ** 2, axis=1)
        e = np.sum(encs[:, 4 * 64:5 * 64] ** 2, axis=1)
        if len(a1) >= 5 and a1.std() > 0 and e.std() > 0:
            out.append((a1, e))
    return out


def _othello_corpus_per_game(
    pgn_path: Path, ch_a: int, ch_b: int,
) -> list[tuple[np.ndarray, np.ndarray]]:
    games = parse_pgn_file(pgn_path)
    out = []
    for gi, g in enumerate(games):
        try:
            _, states, _ = replay(g["moves"])
        except Exception:
            continue
        encs = np.array(
            [encode_768(st) for st in states], dtype=np.float64,
        )
        a = np.sum(encs[:, ch_a * 64:(ch_a + 1) * 64] ** 2, axis=1)
        b = np.sum(encs[:, ch_b * 64:(ch_b + 1) * 64] ** 2, axis=1)
        if len(a) >= 5 and a.std() > 0 and b.std() > 0:
            out.append((a, b))
        if (gi + 1) % 200 == 0:
            print(f"    processed {gi + 1} games", flush=True)
    return out


def run(out_json: Path) -> dict:
    research_dir = Path(__file__).resolve().parent
    chess_results = research_dir.parent.parent / "chess-maths" / "results"
    dataset = research_dir.parent / "dataset"
    chess_sources = [
        (
            "ashchess_N50",
            str(chess_results / "sweep_chain_lichess_ashchess_2026-04-21_N50" / "spectralz" / "game_*.spectralz"),
        ),
        (
            "drnykterstein_N10",
            str(chess_results / "sweep_chain_lichess_drnykterstein_2026-04-14_N10" / "spectralz" / "game_*.spectralz"),
        ),
        (
            "hf_N50",
            str(chess_results / "sweep_hf_2026-04-20_N50" / "spectralz" / "game_*.spectralz"),
        ),
    ]
    othello_sources = [
        (
            "othello_barcelona_35",
            dataset / "liveothello_Barcelona_EGP_2026.pgn",
            "magn_A1minus", "magn_Eminus",
        ),
        (
            "othello_all2025_2178",
            dataset / "liveothello_2025_all.pgn",
            "magn_A1minus", "magn_Eminus",
        ),
        (
            "othello_all2025_occ",
            dataset / "liveothello_2025_all.pgn",
            "occ_A1plus", "occ_Eplus",
        ),
    ]
    results: dict = {"chess": {}, "othello": {}}

    # Chess
    for tag, pattern in chess_sources:
        print(f"\n=== chess {tag} ===")
        per_game = _chess_corpus_per_game(pattern)
        xs = [p[0] for p in per_game]
        ys = [p[1] for p in per_game]
        d = variance_decomposition(xs, ys)
        results["chess"][tag] = d
        print(f"  pooled_r  = {d['pooled_pearson']:+.4f}")
        print(f"  within_r  = {d['within_pearson']:+.4f}")
        print(f"  between_r = {d['between_pearson']:+.4f}")
        if d["within_fraction_of_cov"] is not None:
            print(f"  within / pooled cov  fraction = {d['within_fraction_of_cov']:+.3f}")

    # Othello
    name_to_idx = {n: i for i, n in enumerate(CHANNEL_NAMES)}
    for tag, pgn, ch_a_name, ch_b_name in othello_sources:
        if not pgn.exists():
            continue
        print(f"\n=== othello {tag} ({ch_a_name} vs {ch_b_name}) ===")
        ca, cb = name_to_idx[ch_a_name], name_to_idx[ch_b_name]
        per_game = _othello_corpus_per_game(pgn, ca, cb)
        xs = [p[0] for p in per_game]
        ys = [p[1] for p in per_game]
        d = variance_decomposition(xs, ys)
        results["othello"][tag] = {
            "ch_a": ch_a_name,
            "ch_b": ch_b_name,
            **d,
        }
        print(f"  pooled_r  = {d['pooled_pearson']:+.4f}")
        print(f"  within_r  = {d['within_pearson']:+.4f}")
        print(f"  between_r = {d['between_pearson']:+.4f}")
        if d["within_fraction_of_cov"] is not None:
            print(f"  within / pooled cov  fraction = {d['within_fraction_of_cov']:+.3f}")

    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nwrote {out_json}")
    return results


def _build_parser():
    default_out = (
        Path(__file__).resolve().parent.parent / "results"
        / "phase1e_simpson_mechanism.json"
    )
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--out", type=Path, default=default_out)
    return p


def main(argv=None):
    args = _build_parser().parse_args(argv)
    run(args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
