"""analyze_chaos_length — is `chaos_ratio` length-driven, or does it
reflect genuine fiber/irrep tension?

Reads every `results/sweep_*/corpus_index.csv` under a results dir,
recomputes per-ply chaos ratios from the raw .spectralz files, and
emits Spearman correlations of (game length) vs (mean / median / max /
p90 / sqrt-normalised) chaos ratio. Optionally writes a per-game
markdown table and the per-ply time series for one focus game (default:
the global cr-max outlier).

Definitions (from chess_spectral.corpus.extract_features):
    L2_fiber[t] = sqrt(||FA||²[t] + ||FD||²[t])
    L2_irrep[t] = sqrt(sum_{c in {A1,A2,B1,B2,E,F1,F2,F3}} ||c||²[t])
    chaos_ratio = mean_t(L2_fiber[t]) / mean_t(L2_irrep[t])

Note that the dashboard's "fiber view" charts F1+F2+F3 — those channels
are *irrep* under the corpus definition. chaos_ratio is the
antisymmetric-pawn-breaking ratio, not the orbit-mixing ratio.

Usage:
    python analyze_chaos_length.py results/ [--out report.md] [--focus 7]
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
from scipy import stats

_PKG_PARENT = Path(__file__).resolve().parent / "chess-spectral" / "python"
sys.path.insert(0, str(_PKG_PARENT))

from chess_spectral.frame import read_encodings  # noqa: E402
from chess_spectral.corpus import (  # noqa: E402
    _frame_channel_energies,
    _IRREP_CHANNELS,
    _FIBER_CHANNELS,
)


def _per_ply_chaos(arr: np.ndarray) -> np.ndarray:
    """Returns shape (n_plies,): L2_fiber[t] / L2_irrep[t] per ply.
    Note this is the *per-ply* ratio (different from chaos_ratio,
    which is mean(L2_fiber) / mean(L2_irrep))."""
    e = _frame_channel_energies(arr)
    fiber = np.sqrt(sum(e[c] for c in _FIBER_CHANNELS))
    irrep = np.sqrt(sum(e[c] for c in _IRREP_CHANNELS))
    return np.where(irrep > 0.0, fiber / irrep, 0.0)


def _load_corpus(results_root: Path) -> list[dict]:
    """Walk every results/sweep_*/corpus_index.csv and pair each row
    with its .spectralz path. Returns one dict per game."""
    games = []
    for csv_path in sorted(results_root.glob("sweep_*/corpus_index.csv")):
        sweep_dir = csv_path.parent
        with csv_path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                idx = int(row["index"])
                spz = sweep_dir / "spectralz" / f"game_{idx:03d}.spectralz"
                if not spz.exists():
                    continue
                games.append({
                    "sweep": sweep_dir.name,
                    "index": idx,
                    "n_plies": int(row["n_plies"]),
                    "cr_csv": float(row["chaos_ratio"]),
                    "spz": spz,
                    "result": row.get("result", ""),
                    "white": row.get("white", ""),
                    "black": row.get("black", ""),
                })
    return games


def _summarise(games: list[dict]) -> None:
    """Compute every chaos-ratio variant for every game and store
    it back on the dict (mutates in place)."""
    for g in games:
        _, arr = read_encodings(str(g["spz"]))
        if arr.shape[0] == 0:
            continue
        per_ply = _per_ply_chaos(arr)
        e = _frame_channel_energies(arr)
        # Reproduce CSV's chaos_ratio: mean(L2_fiber) / mean(L2_irrep)
        l2f = np.sqrt(sum(e[c] for c in _FIBER_CHANNELS))
        l2i = np.sqrt(sum(e[c] for c in _IRREP_CHANNELS))
        cr_recomp = float(l2f.mean()) / float(l2i.mean())
        g["per_ply"] = per_ply
        g["cr_mean_of_means"] = cr_recomp        # the CSV definition
        g["cr_mean_per_ply"]  = float(per_ply.mean())
        g["cr_median"]        = float(np.median(per_ply))
        g["cr_max"]           = float(per_ply.max())
        g["cr_p90"]           = float(np.percentile(per_ply, 90))
        g["cr_sqrtnorm"]      = cr_recomp / np.sqrt(g["n_plies"])


def _spearman_block(games: list[dict]) -> dict[str, tuple[float, float]]:
    """ρ and p for game length vs each chaos-ratio variant."""
    n = np.array([g["n_plies"] for g in games], dtype=float)
    out = {}
    for col in ("cr_mean_of_means", "cr_mean_per_ply", "cr_median",
                "cr_max", "cr_p90", "cr_sqrtnorm"):
        v = np.array([g[col] for g in games], dtype=float)
        rho, p = stats.spearmanr(n, v)
        out[col] = (float(rho), float(p))
    return out


def _focus_game(games: list[dict], focus_spec: str | None) -> dict | None:
    if focus_spec is None:
        return max(games, key=lambda g: g.get("cr_max", 0.0))
    if ":" in focus_spec:
        sub, idx_str = focus_spec.split(":", 1)
        idx = int(idx_str)
        for g in games:
            if sub in g["sweep"] and g["index"] == idx:
                return g
        return None
    idx = int(focus_spec)
    for g in games:
        if g["index"] == idx:
            return g
    return None


def _emit_report(games: list[dict], focus: dict | None,
                 spearman: dict[str, tuple[float, float]]) -> str:
    lines: list[str] = []
    n_total = len(games)
    sweeps = sorted(set(g["sweep"] for g in games))
    lines.append("# Chaos Ratio vs Game Length")
    lines.append("")
    lines.append(f"Corpus: {n_total} games across {len(sweeps)} sweeps "
                 f"({', '.join(sweeps)}).")
    lines.append("")
    lines.append("## Formula")
    lines.append("")
    lines.append("```")
    lines.append("L2_fiber[t] = sqrt(||FA||² + ||FD||²)")
    lines.append("L2_irrep[t] = sqrt(||A1||² + ||A2||² + ||B1||² + ||B2||²")
    lines.append("                  + ||E||² + ||F1||² + ||F2||² + ||F3||²)")
    lines.append("chaos_ratio = mean_t(L2_fiber) / mean_t(L2_irrep)")
    lines.append("```")
    lines.append("Source: `chess_spectral/corpus.py:201-207`. Note the dashboard's")
    lines.append("'fiber view' (F1+F2+F3) is *not* what `chaos_ratio` measures —")
    lines.append("`chaos_ratio` is the antisymmetric-breaking ratio (FA+FD vs all)")
    lines.append("and treats F1/F2/F3 as part of the irrep denominator.")
    lines.append("")
    lines.append("## Spearman ρ (game length vs each variant)")
    lines.append("")
    lines.append(f"| Variant | ρ | p | Interpretation |")
    lines.append(f"|---|---:|---:|---|")
    for k, (rho, p) in spearman.items():
        sig = "**" if p < 0.05 else ""
        lines.append(f"| `{k}` | {sig}{rho:+.3f}{sig} | {p:.3g} | |")
    lines.append("")
    lines.append("## Per-game table")
    lines.append("")
    lines.append("| sweep | idx | plies | cr_csv | mean_per_ply | median | max | p90 | sqrt-norm |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for g in sorted(games, key=lambda g: -g["cr_max"]):
        lines.append(
            f"| {g['sweep'][:32]} | {g['index']} | {g['n_plies']} | "
            f"{g['cr_csv']:.3f} | {g['cr_mean_per_ply']:.3f} | "
            f"{g['cr_median']:.3f} | {g['cr_max']:.3f} | "
            f"{g['cr_p90']:.3f} | {g['cr_sqrtnorm']:.3f} |"
        )
    lines.append("")
    if focus is not None:
        lines.append(f"## Focus game: {focus['sweep']} #{focus['index']} "
                     f"({focus['n_plies']} plies, csv cr={focus['cr_csv']:.2f})")
        lines.append("")
        per_ply = focus["per_ply"]
        median = float(np.median(per_ply))
        spike_thresh = 3.0 * median
        spikes = np.where(per_ply > spike_thresh)[0]
        lines.append(f"Per-ply chaos ratio: median={median:.3f}, "
                     f"max={per_ply.max():.3f} at ply {int(per_ply.argmax())}, "
                     f"plies above 3×median ({spike_thresh:.2f}): "
                     f"{len(spikes)} of {len(per_ply)} "
                     f"({100*len(spikes)/len(per_ply):.1f}%).")
        lines.append("")
        lines.append("If spikes ≪ 10% of plies → spikes are localised events.")
        lines.append("If spikes ≫ 10% → ratio is uniformly elevated.")
        lines.append("")
        lines.append("Per-ply ratio time series (first 60 plies, 5-ply chunks):")
        lines.append("")
        lines.append("| ply | ratio |")
        lines.append("|---:|---:|")
        for t in range(0, min(60, len(per_ply)), 5):
            lines.append(f"| {t} | {per_ply[t]:.3f} |")
        if len(per_ply) > 60:
            lines.append("| ... | ... |")
            top10 = np.argsort(per_ply)[-10:][::-1]
            lines.append("")
            lines.append("Top-10 spike plies:")
            lines.append("")
            lines.append("| ply | ratio |")
            lines.append("|---:|---:|")
            for t in top10:
                lines.append(f"| {int(t)} | {per_ply[t]:.3f} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("results_root", type=Path,
                    help="Root dir containing sweep_*/ subdirs.")
    ap.add_argument("--focus", type=str, default=None,
                    help="Focus game spec: either a bare integer (matches the "
                         "first game with that index) or 'substring:index' "
                         "(e.g. 'hf:7' picks index 7 from the first sweep "
                         "whose name contains 'hf'). Default: global cr_max.")
    ap.add_argument("--out", type=Path, default=None,
                    help="Markdown output path. Default: stdout.")
    args = ap.parse_args()

    if not args.results_root.exists():
        ap.error(f"results_root not found: {args.results_root}")

    games = _load_corpus(args.results_root)
    if not games:
        ap.error("no games loaded — check sweep_*/spectralz/ contents")
    print(f"loaded {len(games)} games", file=sys.stderr)

    _summarise(games)
    spear = _spearman_block(games)
    focus = _focus_game(games, args.focus)
    report = _emit_report(games, focus, spear)

    if args.out is None:
        sys.stdout.write(report)
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")
        print(f"wrote {args.out} ({args.out.stat().st_size} bytes)",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    sys.exit(main())
