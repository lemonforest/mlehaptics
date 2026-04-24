"""Fit the SheafPhaseOperator's (12, 8) coupling matrix M to
maximise |Pearson(E_fiber_through_A1_irrep, archive_mean_lb)|.

Baselines to beat:
  identity                          partial rho = -0.447
  scale_fiber_by_owner_lambda2      partial rho = -0.503

Pipeline:
  1. Precompute per-state features[8] and baseline fiber outputs
     at 2587 tasklist positions.  (Sheaf spectrum per state is
     the expensive step; cached so the optimizer loop runs on
     precomputed arrays.)
  2. For each candidate M (12, 8), compute weighted fiber
     energies -> project through D4-A1 -> Pearson with
     archive_mean_lb.
  3. scipy.optimize.minimize on -|Pearson| starting from an
     interpretable initialisation (emphasise lambda2_W on
     channel 11 of pending_white, etc.).
  4. Report the fitted M, its Pearson + Spearman + partial rho
     (controlling |disc_diff|) against archive_mean_lb, and
     compare to the hand-tuned baseline.

Caveat: we're optimising a non-convex, finite-sample objective.
Overfitting is a concern; we hold out 25 % of the tasklist as a
validation set and report train / val scores separately.

Outputs:
  results/phase1e_learned_coupling.json     - best M + scores
"""

from __future__ import annotations

__version__ = "0.3.1"

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.stats import pearsonr, spearmanr

from d4_z2 import D4_CHARS, D4_DIMS, D4_PERMS
from othello_spectral import encode_768
from othello_spectral.phase_operator import (
    SheafPhaseOperator, _sheaf_spectrum_features, _features_array,
)
from othello_utils import BLACK, N

_THIRD_PARTY = Path(__file__).resolve().parent / "third_party"
if str(_THIRD_PARTY) not in sys.path:
    sys.path.insert(0, str(_THIRD_PARTY))
import reversi_misc as _ref  # noqa: E402


def _d4_project_energy(sig: np.ndarray, irrep: str) -> float:
    proj = np.zeros_like(sig, dtype=float)
    for g in range(8):
        proj = proj + D4_CHARS[irrep][g] * sig[D4_PERMS[g]]
    d_mu = D4_DIMS[irrep]
    proj = proj * (d_mu / 8.0)
    return float(np.sum(proj * proj))


def obf_to_state(obf: str) -> tuple[np.ndarray, int]:
    player_bb, opp_bb = _ref.obf_to_bitboards(obf)
    side = BLACK if obf[65] == "X" else -BLACK
    state = np.zeros(N, dtype=int)
    for i in range(N):
        if (player_bb >> i) & 1:
            state[i] = side
        elif (opp_bb >> i) & 1:
            state[i] = -side
    return state, side


def precompute(
    tasklist: Path, archive: Path,
) -> dict:
    """Walk the tasklist; precompute per-state 8-d features and
    the raw 64-d pending_black/white fiber vectors.  Returns
    arrays we can feed to the optimizer hot loop."""
    with tasklist.open("r", encoding="utf-8") as f:
        trows = list(csv.DictReader(f))
    with archive.open("r", encoding="utf-8") as f:
        arows = {r["parent_obf"]: r for r in csv.DictReader(f)}
    n = len(trows)
    features = np.zeros((n, 8), dtype=np.float64)
    fiber_pb = np.zeros((n, 64), dtype=np.float64)
    fiber_pw = np.zeros((n, 64), dtype=np.float64)
    targets = np.full(n, np.nan, dtype=np.float64)
    disc_diff = np.zeros(n, dtype=np.float64)

    t0 = time.time()
    for i, r in enumerate(trows):
        obf = r["obf"]
        state, side = obf_to_state(obf)
        b = int(np.sum(state == BLACK))
        w = int(np.sum(state == -BLACK))
        disc_diff[i] = abs(
            (b - w) if side == BLACK else (w - b)
        )
        feats = _sheaf_spectrum_features(state)
        features[i, :] = _features_array(feats)
        enc = encode_768(state)  # sheaf-default
        fiber_pb[i, :] = enc[10 * 64:11 * 64]
        fiber_pw[i, :] = enc[11 * 64:12 * 64]
        a = arows.get(obf)
        if a is not None:
            try:
                targets[i] = float(a.get("mean_lb", "") or "nan")
            except ValueError:
                pass
        if (i + 1) % 500 == 0:
            elapsed = time.time() - t0
            print(f"  precomputed {i + 1}/{n} ({elapsed:.0f}s)", flush=True)

    return {
        "features": features,
        "fiber_pb": fiber_pb,
        "fiber_pw": fiber_pw,
        "targets": targets,
        "disc_diff": disc_diff,
    }


def _apply_coupling_to_fiber(
    fiber: np.ndarray, features: np.ndarray, m_row: np.ndarray,
) -> np.ndarray:
    """Given raw fiber[n, 64] and features[n, 8], apply per-state
    weight = features[i] @ m_row to scale the fiber row i.  Returns
    weighted_fiber[n, 64]."""
    weights = features @ m_row  # (n,)
    return fiber * weights[:, None]


def _channel_energy_through_a1(
    weighted_fiber: np.ndarray,
) -> np.ndarray:
    """For each row (state), project through D4-A1 and return the
    scalar channel energy.  This is what correlates with
    archive_mean_lb."""
    n = weighted_fiber.shape[0]
    # A1 projection is the fully-symmetric D4 average.
    # Can be vectorised: build the D4-A1 projector once and
    # multiply.
    chi_d4 = D4_CHARS["A1"]
    energies = np.zeros(n, dtype=np.float64)
    for i in range(n):
        proj = np.zeros(64, dtype=np.float64)
        sig = weighted_fiber[i]
        for g in range(8):
            proj = proj + chi_d4[g] * sig[D4_PERMS[g]]
        proj = proj * (1.0 / 8.0)   # d_mu = 1 for A1
        energies[i] = float(np.dot(proj, proj))
    return energies


def _pearson_abs(x: np.ndarray, y: np.ndarray) -> float:
    if x.std() < 1e-12 or y.std() < 1e-12:
        return 0.0
    r = float(pearsonr(x, y).statistic)
    return abs(r)


def objective(
    m_flat: np.ndarray,
    features: np.ndarray, fiber: np.ndarray, targets: np.ndarray,
    mask: np.ndarray,
) -> float:
    """Negative |Pearson| on the training subset.

    m_flat has 8 elements (one row of the (12, 8) matrix — we
    only optimise the row(s) that affect the fiber channels since
    other channels don't enter the fiber energy.)
    """
    weighted = _apply_coupling_to_fiber(
        fiber, features, m_flat,
    )
    energies = _channel_energy_through_a1(weighted[mask])
    return -_pearson_abs(energies, targets[mask])


def run(
    tasklist: Path, archive: Path, out_json: Path,
    val_fraction: float = 0.25, seed: int = 42,
) -> dict:
    print("precomputing features + fiber vectors...")
    data = precompute(tasklist, archive)
    mask_all = ~np.isnan(data["targets"])
    print(f"  {int(mask_all.sum())} positions with archive_mean_lb")

    # train / val split
    rng = np.random.default_rng(seed)
    n = int(mask_all.sum())
    idx = np.where(mask_all)[0]
    rng.shuffle(idx)
    n_val = int(n * val_fraction)
    val_idx = idx[:n_val]
    train_idx = idx[n_val:]
    train_mask = np.zeros(len(mask_all), dtype=bool)
    train_mask[train_idx] = True
    val_mask = np.zeros(len(mask_all), dtype=bool)
    val_mask[val_idx] = True
    print(f"  train: {int(train_mask.sum())}  val: {int(val_mask.sum())}")

    # Optimise one coupling row at a time.  Per Exp 1 the winning
    # channel is `fiber_pw` through D4-A1 (pending_white, A1).
    # So we search for the best 8-d row that maps features -> weight
    # applied to pending_white.

    fiber = data["fiber_pw"]

    # --- Baseline: no coupling, raw pending_white ------------------
    e_raw = _channel_energy_through_a1(fiber)
    r_train_raw = pearsonr(
        e_raw[train_mask], data["targets"][train_mask],
    ).statistic
    r_val_raw = pearsonr(
        e_raw[val_mask], data["targets"][val_mask],
    ).statistic
    print(
        f"  baseline (identity weights): train r = {r_train_raw:+.4f}  "
        f"val r = {r_val_raw:+.4f}"
    )

    # --- Baseline: hand-tuned scale_fiber_by_owner_lambda2 --------
    # weight = 1 / (1 + lambda2_W) where feature index 1 is
    # lambda2_W (see _features_array ordering).
    m_handtuned = np.zeros(8, dtype=np.float64)
    # This isn't a linear function of features, so we use a
    # two-stage form: weights = 1/(1 + lambda2_W).  For the
    # linear-coupling framework, simulate with m = [0, -0.5, 0,
    # 0, 0, 0, 0, 0] which gives weight ~ -0.5 * lambda2_W (not
    # identical but directionally similar).  Skip as a formal
    # baseline; report Exp 1's absolute numbers instead.

    # --- Learned coupling ------------------------------------------
    # Initial guess: small random.
    rng = np.random.default_rng(seed + 1)
    best_obj = float("inf")
    best_m = None
    n_restarts = 6
    for restart in range(n_restarts):
        if restart == 0:
            # Deterministic init: coefficient on lambda2_W only.
            m0 = np.array(
                [0, -0.5, 0, 0, 0, 0, 0, 0], dtype=np.float64,
            )
        else:
            m0 = rng.normal(0.0, 0.2, size=8)
        res = minimize(
            objective, m0,
            args=(
                data["features"], fiber, data["targets"], train_mask,
            ),
            method="Nelder-Mead",
            options={"maxiter": 1000, "xatol": 1e-5, "fatol": 1e-6},
        )
        val_score = objective(
            res.x, data["features"], fiber, data["targets"], val_mask,
        )
        print(
            f"  restart {restart}: train obj = {res.fun:+.4f}  "
            f"val obj = {val_score:+.4f}"
        )
        if res.fun < best_obj:
            best_obj = res.fun
            best_m = res.x.copy()

    # Final report
    weighted_best = _apply_coupling_to_fiber(
        fiber, data["features"], best_m,
    )
    e_best = _channel_energy_through_a1(weighted_best)

    def _metrics(indices):
        ys = data["targets"][indices]
        xs = e_best[indices]
        pr = pearsonr(xs, ys)
        sp = spearmanr(xs, ys)
        # partial on |disc_diff|
        dd = data["disc_diff"][indices]
        if dd.std() > 0:
            cx = np.polyfit(dd, xs, 1)
            cy = np.polyfit(dd, ys, 1)
            xr = xs - (cx[0] * dd + cx[1])
            yr = ys - (cy[0] * dd + cy[1])
            sp_p = spearmanr(xr, yr)
            partial_rho = float(sp_p.statistic)
        else:
            partial_rho = None
        return {
            "pearson_r": float(pr.statistic),
            "spearman_rho": float(sp.statistic),
            "partial_rho": partial_rho,
            "n": int(len(ys)),
        }

    train_scores = _metrics(train_mask)
    val_scores = _metrics(val_mask)
    overall_scores = _metrics(mask_all)

    summary = {
        "tasklist": str(tasklist),
        "best_m_coefficients": best_m.tolist(),
        "feature_order": [
            "lambda2_B", "lambda2_W",
            "lambdamax_B", "lambdamax_W",
            "entropy_B",  "entropy_W",
            "kerdim_B",   "kerdim_W",
        ],
        "train": train_scores,
        "val":   val_scores,
        "overall": overall_scores,
        "baseline_identity": {
            "train_pearson": float(r_train_raw),
            "val_pearson":   float(r_val_raw),
        },
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with out_json.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\n=== Learned coupling summary ===")
    print(f"best m = {best_m}")
    print(f"  feature: {summary['feature_order']}")
    print(
        f"\n  train  pearson={train_scores['pearson_r']:+.4f}  "
        f"spearman={train_scores['spearman_rho']:+.4f}  "
        f"partial={train_scores['partial_rho']:+.4f}"
    )
    print(
        f"  val    pearson={val_scores['pearson_r']:+.4f}  "
        f"spearman={val_scores['spearman_rho']:+.4f}  "
        f"partial={val_scores['partial_rho']:+.4f}"
    )
    print(
        f"  all    pearson={overall_scores['pearson_r']:+.4f}  "
        f"spearman={overall_scores['spearman_rho']:+.4f}  "
        f"partial={overall_scores['partial_rho']:+.4f}"
    )
    print(f"\nBaselines (from Exp 1 / §1e.7.x):")
    print(f"  identity pending_white A1            partial rho = -0.447")
    print(f"  scale_fiber_by_owner_lambda2         partial rho = -0.503")
    print(f"\nwrote {out_json}")
    return summary


def _build_parser():
    research_dir = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--tasklist", type=Path,
        default=research_dir.parent / "dataset" / "reversi_scripts"
        / "empty50_tasklist_edax_knowledge.csv",
    )
    p.add_argument(
        "--archive-summary", type=Path,
        default=research_dir.parent / "results"
        / "phase1d_archive_summary.csv",
    )
    p.add_argument(
        "--out", type=Path,
        default=research_dir.parent / "results"
        / "phase1e_learned_coupling.json",
    )
    p.add_argument(
        "--val-fraction", type=float, default=0.25,
    )
    p.add_argument("--seed", type=int, default=42)
    return p


def main(argv=None):
    args = _build_parser().parse_args(argv)
    if not args.tasklist.exists() or not args.archive_summary.exists():
        print("tasklist or archive missing", file=sys.stderr)
        return 2
    run(
        args.tasklist, args.archive_summary, args.out,
        args.val_fraction, args.seed,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
