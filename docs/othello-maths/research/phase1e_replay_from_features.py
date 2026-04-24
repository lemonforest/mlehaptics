"""Phase 1e.x — replay phase 1b/1c/1d analyses from encoder CSV features.

Companion to the v0.2.0 othello_spectral encoder: loads a
corpus-features CSV produced by ``othello_spectral.features`` and
recomputes the §2b aggregate statistics (B1 vs B2 population,
A1- vs rho correlation, peak/drop trajectory) from the encoded
channel energies.

This serves two purposes:

  1. Verify that the encoder produces numerically-consistent
     observables against the direct-projection reference used in
     consolidated_tests.py / game_trajectory_tests.py.  A pass
     confirms the encoder can be a drop-in replacement for the
     ad-hoc-projection pipelines in §2b-§2d.

  2. Enables re-running phase 1b-1d aggregates on any new corpus
     in seconds (CSV is ~250 KB per game × 35 games = 9 MB for
     Barcelona; aggregates are numpy ops, sub-second).
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr


def _load_features(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def _to_float(d: dict, key: str, default: float = float("nan")) -> float:
    v = d.get(key)
    if v is None or v == "":
        return default
    try:
        return float(v)
    except ValueError:
        return default


def run(features_csv: Path, out_json: Path) -> dict:
    rows = _load_features(features_csv)
    n = len(rows)
    print(f"loaded {n} rows from {features_csv.name}")
    if n < 10:
        print("too few rows for aggregate analysis", file=sys.stderr)
        return {"error": "too_few_rows", "n": n}

    # Channel-energy columns
    e_a1m = np.array([_to_float(r, "E_magn_A1minus") for r in rows])
    e_b1m = np.array([_to_float(r, "E_magn_B1minus") for r in rows])
    e_b2m = np.array([_to_float(r, "E_magn_B2minus") for r in rows])
    e_em = np.array([_to_float(r, "E_magn_Eminus") for r in rows])
    e_a1o = np.array([_to_float(r, "E_occ_A1plus") for r in rows])
    e_eo = np.array([_to_float(r, "E_occ_Eplus") for r in rows])
    e_a2o = np.array([_to_float(r, "E_occ_A2plus") for r in rows])
    e_b1o = np.array([_to_float(r, "E_occ_B1plus") for r in rows])
    e_b2o = np.array([_to_float(r, "E_occ_B2plus") for r in rows])
    # rho = occupation count / 64.  We don't store it directly in the
    # features CSV; the sum of occupation-irrep energies equals the
    # total occupation norm = disc_count, so rho = disc_count / 64.
    # Alternatively: norm_total is dominated by the fiber (L @ s)
    # contribution which confounds this; use occupation channels only.
    disc_count = e_a1o + e_a2o + e_b1o + e_b2o + e_eo
    # By Plancherel the sum equals ||occ||^2 = disc_count exactly.
    rho = disc_count / 64.0

    summary: dict = {
        "features_csv": str(features_csv),
        "n_plies": int(n),
        "mean_energies": {
            "magn_A1minus": float(e_a1m.mean()),
            "magn_B1minus": float(e_b1m.mean()),
            "magn_B2minus": float(e_b2m.mean()),
            "magn_Eminus":  float(e_em.mean()),
            "occ_A1plus":   float(e_a1o.mean()),
            "occ_A2plus":   float(e_a2o.mean()),
            "occ_B1plus":   float(e_b1o.mean()),
            "occ_B2plus":   float(e_b2o.mean()),
            "occ_Eplus":    float(e_eo.mean()),
        },
    }

    # §2b.T2 — B1 vs B2 population asymmetry
    summary["b1_b2_asymmetry"] = {
        "magn_mean_B1_over_B2": float(e_b1m.mean() / max(e_b2m.mean(), 1e-12)),
        "occ_mean_B1_over_B2":  float(e_b1o.mean() / max(e_b2o.mean(), 1e-12)),
        "magn_B2_gt_B1_fraction": float(np.mean(e_b2m > e_b1m)),
        "occ_B2_gt_B1_fraction":  float(np.mean(e_b2o > e_b1o)),
    }

    # §2.E3 / §2b.E3 — Spearman(rho, A1- energy)
    sp_rho_a1m = spearmanr(rho, e_a1m)
    summary["rho_vs_a1_minus"] = {
        "rho": float(sp_rho_a1m.statistic),
        "p": float(sp_rho_a1m.pvalue),
        "n": int(n),
    }
    # Also d4_a1_occupation vs rho (should be near-tautological)
    sp_rho_a1o = spearmanr(rho, e_a1o)
    summary["rho_vs_d4_a1_occ"] = {
        "rho": float(sp_rho_a1o.statistic),
        "p": float(sp_rho_a1o.pvalue),
        "n": int(n),
    }

    # Cross-channel: (A1-, E-), (A1-occ, E-occ), (B1-, B2-)
    pairs = [
        ("a1_minus_vs_e_minus",   e_a1m, e_em),
        ("a1_occ_vs_e_occ",       e_a1o, e_eo),
        ("b1_minus_vs_b2_minus",  e_b1m, e_b2m),
        ("b1_occ_vs_b2_occ",      e_b1o, e_b2o),
    ]
    cross: dict = {}
    for label, a, b in pairs:
        if a.std() > 0 and b.std() > 0:
            c = float(np.corrcoef(a, b)[0, 1])
        else:
            c = float("nan")
        cross[label] = {"pearson_r": c}
    summary["cross_channel_pearson"] = cross

    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\n=== Replay aggregates (N = {n}) ===")
    m = summary["mean_energies"]
    print(f"  mean E magn A1- = {m['magn_A1minus']:.3f}  B1- = {m['magn_B1minus']:.3f}  "
          f"B2- = {m['magn_B2minus']:.3f}  E- = {m['magn_Eminus']:.3f}")
    print(f"  mean E occ  A1+ = {m['occ_A1plus']:.3f}  B1+ = {m['occ_B1plus']:.3f}  "
          f"B2+ = {m['occ_B2plus']:.3f}  E+ = {m['occ_Eplus']:.3f}")
    a = summary["b1_b2_asymmetry"]
    print(f"  B2/B1 ratio: magn = {a['magn_mean_B1_over_B2'] ** -1:.2f}x  "
          f"occ = {a['occ_mean_B1_over_B2'] ** -1:.2f}x")
    r = summary["rho_vs_a1_minus"]
    print(f"  Spearman(rho, A1- energy) = {r['rho']:+.3f}  p = {r['p']:.2e}")
    print(f"  cross-channel Pearson:")
    for k, v in cross.items():
        print(f"    {k:28s}  r = {v['pearson_r']:+.3f}")
    print(f"\nwrote {out_json}")
    return summary


def _build_parser():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  # Replay phase 1b aggregates from Barcelona features CSV.
  python research/phase1e_replay_from_features.py \\
      --features ../results/barcelona_features.csv \\
      --out ../results/phase1e_replay_barcelona.json

notes:
  The features CSV must have been produced by
  othello_spectral.features extracted from a .spectralz file in the
  current encoder layout (12 channels, CHANNEL_NAMES order).  For
  different encoders, first regenerate features via
  ``python -m othello_spectral.features <spectralz> --out <csv>``.
""",
    )
    p.add_argument("--features", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    return p


def main(argv=None):
    args = _build_parser().parse_args(argv)
    if not args.features.exists():
        print(f"features CSV not found: {args.features}", file=sys.stderr)
        return 2
    run(args.features, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
