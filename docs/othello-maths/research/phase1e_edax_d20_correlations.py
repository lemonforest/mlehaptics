"""Phase 1e.1 analysis — spectral × edax d=20 correlations on the
2587 tasklist, and the Reading A vs Reading B verdict.

Reading A (aggregation): the 43 % gain from Phase 1d.b
  rho(D4-A1(s^2), edax_score_preproof)   = -0.349 (raw)
  rho(D4-A1(s^2), archive_mean_lb)       = -0.498 (raw)
is mostly because archive_mean_lb is a smoother y-variable (averaged
over 300k-600k children each).  A strong-search engine at the same
effort as Takizawa per sub-problem would give near-identical
correlation to archive_mean_lb.

Reading B (alignment): the spectral channel genuinely picks up
ground-truth-aligned content beyond what a strong deep-search engine
captures.

Decision rule:
  rho_pre = rho(D4-A1, edax_score_preproof)    (known, ~-0.349 raw)
  rho_d20 = rho(D4-A1, edax_d20)               (this run)
  rho_arc = rho(D4-A1, archive_mean_lb)        (known, ~-0.498 raw)

  Case A (aggregation dominates):
    rho_d20 between rho_pre and rho_arc, closer to rho_arc
    => Reading A load-bearing; spectral agrees with any strong
       evaluator once noise is averaged down.

  Case B (alignment substantive):
    rho_d20 near rho_pre, much weaker than rho_arc
    => Reading B load-bearing; spectral sees more than engine heuristic.

Inputs
------
  results/phase1e_edax_d20.csv           -- per-position d=20 score
  results/phase1d_spectral_vs_perfectplay.csv -- per-position spectral

Output
------
  results/phase1e_edax_d20_correlations.json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr


def _load(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def _float(v) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def _residualize(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    if x.ndim == 1:
        x = x.reshape(-1, 1)
    X = np.concatenate([x, np.ones((len(y), 1))], axis=1)
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    return y - X @ coef


def run(
    edax_csv: Path, spectral_csv: Path, out_json: Path,
) -> dict:
    edax_rows = _load(edax_csv)
    spec_rows = _load(spectral_csv)
    # Join on obf
    spec_by_obf = {r["obf"]: r for r in spec_rows}
    joined = []
    for e in edax_rows:
        obf = e["obf"]
        if obf not in spec_by_obf:
            continue
        d20 = _float(e.get("edax_d20_score"))
        if d20 is None or int(e.get("parse_ok", "0") or 0) != 1:
            continue
        s = spec_by_obf[obf]
        joined.append({"obf": obf, "edax_d20_score": d20, **s})

    n_total_edax = len(edax_rows)
    n_joined = len(joined)
    print(f"edax rows: {n_total_edax}")
    print(f"spectral rows: {len(spec_rows)}")
    print(f"joined rows with parse_ok d=20: {n_joined}")
    if n_joined < 50:
        print("Too few joined rows; stopping.", file=sys.stderr)
        return {"n_joined": n_joined, "error": "insufficient data"}

    def col(name: str) -> np.ndarray:
        return np.array(
            [_float(r[name]) for r in joined], dtype=float
        )

    # Spectral channels
    channels = {
        "d4_a1_occ": col("d4_a1_occupation_energy"),
        "d4_a2_occ": col("d4_a2_occupation_energy"),
        "d4_b1_occ": col("d4_b1_occupation_energy"),
        "d4_b2_occ": col("d4_b2_occupation_energy"),
        "d4_e_occ":  col("d4_e_occupation_energy"),
        "a1_minus":  col("a1_minus_energy"),
        "e_minus":   col("e_minus_energy"),
    }
    # Targets
    targets = {
        "edax_score_preproof": col("edax_score"),
        "edax_d20_score":      np.array(
            [r["edax_d20_score"] for r in joined], dtype=float
        ),
        "archive_mean_lb":     col("archive_mean_lb"),
        "archive_mean_ub":     col("archive_mean_ub"),
    }
    DD = np.abs(col("disc_diff_player_minus_opp"))

    correlations: dict[str, dict] = {}
    for ch_name, ch_vec in channels.items():
        for tg_name, tg_vec in targets.items():
            mask = ~np.isnan(ch_vec) & ~np.isnan(tg_vec)
            x = ch_vec[mask]
            y = tg_vec[mask]
            if len(x) < 20:
                continue
            sp = spearmanr(x, y)
            # Partial on |disc_diff|
            dd = DD[mask]
            if dd.std() > 0:
                xr = _residualize(x, dd)
                yr = _residualize(y, dd)
                sp_p = spearmanr(xr, yr)
                partial = {
                    "rho": float(sp_p.statistic),
                    "p": float(sp_p.pvalue),
                }
            else:
                partial = None
            correlations[f"{ch_name}__vs__{tg_name}"] = {
                "raw_rho": float(sp.statistic),
                "raw_p": float(sp.pvalue),
                "partial_rho": partial["rho"] if partial else None,
                "partial_p": partial["p"] if partial else None,
                "n": int(len(x)),
            }

    # Reading A vs B verdict for D4-A1(s^2)
    rho_pre_raw = correlations["d4_a1_occ__vs__edax_score_preproof"]["raw_rho"]
    rho_d20_raw = correlations["d4_a1_occ__vs__edax_d20_score"]["raw_rho"]
    rho_arc_raw = correlations["d4_a1_occ__vs__archive_mean_lb"]["raw_rho"]
    rho_pre_par = correlations["d4_a1_occ__vs__edax_score_preproof"]["partial_rho"]
    rho_d20_par = correlations["d4_a1_occ__vs__edax_d20_score"]["partial_rho"]
    rho_arc_par = correlations["d4_a1_occ__vs__archive_mean_lb"]["partial_rho"]

    # "A-score" = how close d20 is to arc vs pre (0 = all pre, 1 = all arc)
    def position(pre, d20, arc):
        total = abs(arc - pre)
        if total < 1e-9:
            return float("nan")
        return (abs(d20) - abs(pre)) / (abs(arc) - abs(pre))

    verdict = {
        "raw": {
            "rho_pre": rho_pre_raw,
            "rho_d20": rho_d20_raw,
            "rho_arc": rho_arc_raw,
            "a_position": position(rho_pre_raw, rho_d20_raw, rho_arc_raw),
        },
        "partial": {
            "rho_pre": rho_pre_par,
            "rho_d20": rho_d20_par,
            "rho_arc": rho_arc_par,
            "a_position": position(rho_pre_par, rho_d20_par, rho_arc_par),
        },
    }

    summary = {
        "n_joined": n_joined,
        "n_edax_total": n_total_edax,
        "n_spectral_total": len(spec_rows),
        "correlations": correlations,
        "reading_a_vs_b_verdict_d4_a1_occ": verdict,
    }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Stdout highlights
    print(f"\n=== Phase 1e.1 edax d=20 correlation results (N = {n_joined}) ===")
    print(f"  {'channel':14s}  {'target':22s}  {'raw rho':>10s}  {'partial rho':>14s}")
    for k, v in correlations.items():
        ch, tg = k.split("__vs__")
        print(
            f"  {ch:14s}  {tg:22s}  {v['raw_rho']:+10.3f}  "
            f"{(v['partial_rho'] if v['partial_rho'] is not None else 0.0):+14.3f}"
        )
    print("\n  D4-A1(s^2) Reading A vs B verdict:")
    v = verdict["raw"]
    print(f"    raw:     pre={v['rho_pre']:+.3f}  d20={v['rho_d20']:+.3f}  arc={v['rho_arc']:+.3f}  a_position={v['a_position']:+.3f}")
    v = verdict["partial"]
    print(f"    partial: pre={v['rho_pre']:+.3f}  d20={v['rho_d20']:+.3f}  arc={v['rho_arc']:+.3f}  a_position={v['a_position']:+.3f}")
    print(
        "\n  Reading guide:  a_position ~ 1.0 -> Reading A (aggregation) dominates;"
        "\n                   a_position ~ 0.0 -> Reading B (alignment) dominates;"
        "\n                   a_position in between -> mixed."
    )
    print(f"\nwrote {out_json}")
    return summary


def _build_parser():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # Default: use the canonical phase1e_edax_d20.csv and the §2d.b
  # phase1d_spectral_vs_perfectplay.csv, write the verdict JSON.
  python research/phase1e_edax_d20_correlations.py

  # Custom pairing (e.g. against the accuracy=100 re-aggregation
  # spectral CSV).
  python research/phase1e_edax_d20_correlations.py \\
      --edax-csv ../results/phase1e_edax_d20.csv \\
      --spectral-csv ../results/phase1e_spectral_vs_perfectplay_exact100.csv \\
      --out-json ../results/phase1e_edax_d20_correlations_exact100.json

reading the output:
  'reading_a_vs_b_verdict_d4_a1_occ.a_position' quantifies where
  the d=20 correlation sits between pre-proof (0.0) and
  archive_mean_lb (1.0).  |a_position| <~ 0.1 means d=20 tracks
  pre-proof (Reading B dominates); |a_position| ~> 0.7 means d=20
  tracks archive_mean_lb (Reading A dominates).
""",
    )
    default_edax = (
        Path(__file__).resolve().parent.parent / "results"
        / "phase1e_edax_d20.csv"
    )
    default_spec = (
        Path(__file__).resolve().parent.parent / "results"
        / "phase1d_spectral_vs_perfectplay.csv"
    )
    default_out = (
        Path(__file__).resolve().parent.parent / "results"
        / "phase1e_edax_d20_correlations.json"
    )
    p.add_argument("--edax-csv", type=Path, default=default_edax)
    p.add_argument("--spectral-csv", type=Path, default=default_spec)
    p.add_argument("--out-json", type=Path, default=default_out)
    return p


def main(argv=None):
    args = _build_parser().parse_args(argv)
    run(args.edax_csv, args.spectral_csv, args.out_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
