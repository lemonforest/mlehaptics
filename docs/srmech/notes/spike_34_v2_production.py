"""Spike #34 v2 — Production analysis with sliding-window minimum-slope β.

Diagnostic (spike_34/diagnostic_window.py) showed that the Donsker-Varadhan
asymptotic β value emerges as the MINIMUM SLOPE of log(-log(<S(t)>)) vs log(t),
which sits in the intermediate-to-late tail BEFORE the finite-size cutoff
re-stretches the decay.

Methodology:
  1. Compute disorder-averaged <S(t)> over M trap realisations (analytic
     eigendecomposition; no MC variance).
  2. Compute sliding-window linear slope of y=log(-log(S)) vs x=log(t).
  3. Empirical β = minimum slope across windows where the local linear
     fit r² > 0.999 (asymptotic-linearity criterion).
  4. Functional-form discrimination via SAME-window single-exp / power-law fits.

Sweep:
  - Substrates: Sierpinski L=4,5,6,7; Path P_n n=256,512; Cycle C_n n=256,512;
    Torus T_n×n n=24,32; Random 3-regular n=256,512 (negative control)
  - Trap density rho in {0.02, 0.05, 0.10}
  - Realisations: 64 (Sierpinski/Path/Cycle); 32 (Torus/Random; expensive eig)

Output: NDJSON at D:/temp/spike_34/spike_34_v2_records.ndjson.
"""

from __future__ import annotations

import io
import json
import math
import sys
import time

if __name__ == "__main__" and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

import numpy as np
import scipy.linalg as sla
import scipy.sparse as sp

sys.path.insert(0, "D:/temp/spike_31")
from spike_31_stretched_exp_beta import (
    build_sierpinski_laplacian,
    build_path_laplacian,
    build_cycle_laplacian,
    build_torus_laplacian,
    build_random_kregular_laplacian,
)

sys.path.insert(0, "D:/temp/spike_34")
from spike_34_donsker_varadhan_survival import (
    survival_probability_disorder_averaged,
)


def empirical_d_S(L: sp.csr_matrix, frac: float = 0.10) -> float:
    eigs = sla.eigvalsh(L.toarray())
    nz = np.sort(eigs[eigs > 1e-10])
    counts = np.arange(1, len(nz) + 1).astype(float)
    nfit = max(10, int(len(nz) * frac))
    nfit = min(nfit, len(nz) - 1)
    p = np.polyfit(np.log(nz[:nfit]), np.log(counts[:nfit]), 1)
    return 2.0 * p[0]


def sliding_window_slopes(t: np.ndarray, S: np.ndarray, win: int = 30, step: int = 3) -> dict:
    """Compute sliding-window linear-regression slopes of log(-log(S)) vs log(t).

    Returns dict with arrays:
      - slope_arr: local linear slope
      - r2_arr:    local linear-fit r²
      - t_centre:  geometric centre of window
      - S_centre:  approximate S at window centre
    """
    valid = (S > 1e-14) & (S < 0.999)
    t_v = t[valid]
    S_v = S[valid]
    y = np.log(-np.log(S_v))
    x = np.log(t_v)
    slope_arr, r2_arr, t_centre, S_centre = [], [], [], []
    for i in range(0, len(y) - win + 1, step):
        xi = x[i:i+win]
        yi = y[i:i+win]
        p = np.polyfit(xi, yi, 1)
        yhat = np.polyval(p, xi)
        ss_res = ((yi - yhat) ** 2).sum()
        ss_tot = ((yi - yi.mean()) ** 2).sum()
        r2 = 1.0 - (ss_res / ss_tot if ss_tot > 1e-15 else 1.0)
        slope_arr.append(p[0])
        r2_arr.append(r2)
        t_centre.append(np.exp(np.mean(xi)))
        # S at midpoint
        mid_idx = i + win // 2
        S_centre.append(S_v[mid_idx])
    return {
        "slope": np.array(slope_arr),
        "r2": np.array(r2_arr),
        "t_centre": np.array(t_centre),
        "S_centre": np.array(S_centre),
    }


def extract_DV_beta(t: np.ndarray, S: np.ndarray, r2_threshold: float = 0.9990,
                    win: int = 30, step: int = 3) -> dict:
    """Extract the Donsker-Varadhan asymptotic β via sliding-window minimum-slope.

    Method:
      1. Compute sliding-window linear-regression slopes of log(-log(S)) vs log(t)
      2. Restrict to windows with r² >= r2_threshold (locally linear)
      3. Restrict to windows in the "tail" (S < 0.5) to avoid early-time
         single-exponential regime
      4. β_DV = MINIMUM slope across qualifying windows.
         This is where the cascade-stretching is most pronounced; finite-size
         corrections push β upward at both ends.

    Returns dict:
      - beta_DV: minimum slope
      - t_at_min: t-centre at minimum
      - S_at_min: S-centre at minimum
      - r2_at_min: r² of the linear fit at that window
      - n_qualifying_windows: count
    """
    sw = sliding_window_slopes(t, S, win=win, step=step)
    # Quality + tail criteria
    qual_mask = (sw["r2"] >= r2_threshold) & (sw["S_centre"] < 0.5) & (sw["S_centre"] > 1e-12)
    if qual_mask.sum() == 0:
        return {
            "beta_DV": float("nan"),
            "t_at_min": None,
            "S_at_min": None,
            "r2_at_min": None,
            "n_qualifying_windows": 0,
            "reason": "no qualifying windows",
        }
    qual_slopes = sw["slope"][qual_mask]
    qual_r2 = sw["r2"][qual_mask]
    qual_t = sw["t_centre"][qual_mask]
    qual_S = sw["S_centre"][qual_mask]
    idx_min = int(np.argmin(qual_slopes))
    return {
        "beta_DV": float(qual_slopes[idx_min]),
        "t_at_min": float(qual_t[idx_min]),
        "S_at_min": float(qual_S[idx_min]),
        "r2_at_min": float(qual_r2[idx_min]),
        "n_qualifying_windows": int(qual_mask.sum()),
        "qualifying_slope_range": [float(qual_slopes.min()), float(qual_slopes.max())],
        "qualifying_S_range": [float(qual_S.min()), float(qual_S.max())],
    }


def fit_form_in_window(t: np.ndarray, S: np.ndarray, S_min: float, S_max: float, form: str) -> dict:
    """Fit a specific functional form (stretched_exp / single_exp / power_law)
    in the S-window [S_min, S_max].
    """
    mask = (S > S_min) & (S < S_max)
    if mask.sum() < 5:
        return {"form": form, "r2": 0.0, "n_fit": int(mask.sum()), "reason": "insufficient"}
    t_v = t[mask]
    S_v = S[mask]
    if form == "stretched_exp":
        y = np.log(-np.log(S_v))
        x = np.log(t_v)
        p = np.polyfit(x, y, 1)
        beta = p[0]
        intercept = p[1]
        yhat = np.polyval(p, x)
        ss_res = ((y - yhat) ** 2).sum()
        ss_tot = ((y - y.mean()) ** 2).sum()
        r2 = 1.0 - (ss_res / ss_tot if ss_tot > 1e-15 else 1.0)
        tau = math.exp(-intercept / beta) if abs(beta) > 1e-12 else float("nan")
        return {"form": form, "beta": float(beta), "tau": float(tau),
                "r2": float(r2), "n_fit": int(mask.sum())}
    elif form == "single_exp":
        y = np.log(S_v)
        x = t_v
        p = np.polyfit(x, y, 1)
        yhat = np.polyval(p, x)
        ss_res = ((y - yhat) ** 2).sum()
        ss_tot = ((y - y.mean()) ** 2).sum()
        r2 = 1.0 - (ss_res / ss_tot if ss_tot > 1e-15 else 1.0)
        return {"form": form, "k": float(-p[0]), "log_A": float(p[1]),
                "r2": float(r2), "n_fit": int(mask.sum())}
    elif form == "power_law":
        y = np.log(S_v)
        x = np.log(t_v)
        p = np.polyfit(x, y, 1)
        yhat = np.polyval(p, x)
        ss_res = ((y - yhat) ** 2).sum()
        ss_tot = ((y - y.mean()) ** 2).sum()
        r2 = 1.0 - (ss_res / ss_tot if ss_tot > 1e-15 else 1.0)
        return {"form": form, "exponent": float(p[0]), "log_A": float(p[1]),
                "r2": float(r2), "n_fit": int(mask.sum())}
    else:
        raise ValueError(f"Unknown form {form}")


def analyse_substrate_v2(
    name: str,
    L: sp.csr_matrix,
    n: int,
    predicted_d_S: float,
    trap_density: float,
    n_realisations: int,
    n_t_pts: int = 512,
    seed: int = 42,
    notes: dict | None = None,
) -> dict:
    """Per-substrate analysis v2 — sliding-window minimum-slope β."""
    t0 = time.time()

    d_S_emp = empirical_d_S(L)
    predicted_beta = (
        predicted_d_S / (predicted_d_S + 2.0)
        if not math.isnan(predicted_d_S) else float("nan")
    )

    eigs = sla.eigvalsh(L.toarray())
    nz = eigs[eigs > 1e-10]
    lam_min = float(nz[0])
    lam_max = float(nz[-1])

    t_grid = np.geomspace(0.01 / lam_max, 200.0 / lam_min, n_t_pts)

    t_S0 = time.time()
    S_avg, diags = survival_probability_disorder_averaged(
        L, n, trap_density, n_realisations, t_grid, seed=seed,
    )
    t_S = time.time() - t_S0

    # Extract DV β via sliding-window minimum slope
    dv = extract_DV_beta(t_grid, S_avg, r2_threshold=0.999, win=30, step=3)

    # Functional-form discrimination at the SAME-S window where DV β was found
    # (compare stretched_exp vs single_exp vs power_law in that local window)
    if dv["S_at_min"] is not None and not math.isnan(dv["beta_DV"]):
        # Define a window of width ~factor 10 in S around the DV-minimum point
        center = dv["S_at_min"]
        S_lo = center / 10
        S_hi = center * 10
        S_lo = max(S_lo, 1e-12)
        S_hi = min(S_hi, 0.95)
        fit_st = fit_form_in_window(t_grid, S_avg, S_lo, S_hi, "stretched_exp")
        fit_sx = fit_form_in_window(t_grid, S_avg, S_lo, S_hi, "single_exp")
        fit_pl = fit_form_in_window(t_grid, S_avg, S_lo, S_hi, "power_law")
    else:
        fit_st = {"form": "stretched_exp", "r2": float("nan"), "reason": "no DV window"}
        fit_sx = {"form": "single_exp", "r2": float("nan"), "reason": "no DV window"}
        fit_pl = {"form": "power_law", "r2": float("nan"), "reason": "no DV window"}
        S_lo, S_hi = None, None

    # Also do tail-window discrimination (S in [1e-4, 1e-1])
    fit_st_tail = fit_form_in_window(t_grid, S_avg, 1e-4, 1e-1, "stretched_exp")
    fit_sx_tail = fit_form_in_window(t_grid, S_avg, 1e-4, 1e-1, "single_exp")
    fit_pl_tail = fit_form_in_window(t_grid, S_avg, 1e-4, 1e-1, "power_law")

    # Functional-form winner at DV-window
    valid_fits = [f for f in [fit_st, fit_sx, fit_pl]
                  if "r2" in f and not math.isnan(f.get("r2", float("nan")))]
    winner_form = "insufficient_data"
    winner_r2 = float("nan")
    if valid_fits:
        winner = max(valid_fits, key=lambda f: f["r2"])
        winner_form = winner["form"]
        winner_r2 = winner["r2"]

    t_total = time.time() - t0

    record = {
        "substrate": name,
        "n_vertices": int(n),
        "trap_density_rho": float(trap_density),
        "n_realisations": int(n_realisations),
        "lambda_min_nonzero": lam_min,
        "lambda_max": lam_max,
        "predicted_d_S": float(predicted_d_S) if not math.isnan(predicted_d_S) else None,
        "empirical_d_S": float(d_S_emp),
        "predicted_beta_canonical": float(predicted_beta) if not math.isnan(predicted_beta) else None,
        # DV β via sliding-window minimum
        "DV_beta": dv["beta_DV"] if dv["beta_DV"] == dv["beta_DV"] else None,
        "DV_t_at_min": dv["t_at_min"],
        "DV_S_at_min": dv["S_at_min"],
        "DV_r2_at_min": dv["r2_at_min"],
        "DV_n_qualifying_windows": dv["n_qualifying_windows"],
        "DV_qualifying_slope_range": dv.get("qualifying_slope_range"),
        "DV_qualifying_S_range": dv.get("qualifying_S_range"),
        "delta_beta_DV_vs_canonical": (
            float(dv["beta_DV"] - predicted_beta)
            if dv["beta_DV"] == dv["beta_DV"] and not math.isnan(predicted_beta)
            else None
        ),
        # Functional-form discrimination at DV-window
        "DV_window_S_range": [S_lo, S_hi] if S_lo is not None else None,
        "fit_stretched_exp_DV_window": fit_st,
        "fit_single_exp_DV_window": fit_sx,
        "fit_power_law_DV_window": fit_pl,
        "winner_form_DV_window": winner_form,
        "winner_r2_DV_window": float(winner_r2) if not math.isnan(winner_r2) else None,
        # Tail-window discrimination
        "fit_stretched_exp_tail": fit_st_tail,
        "fit_single_exp_tail": fit_sx_tail,
        "fit_power_law_tail": fit_pl_tail,
        "time_survival_seconds": float(t_S),
        "time_total_seconds": float(t_total),
        "S_dynamic_range": [float(S_avg.min()), float(S_avg.max())],
        "notes": notes or {},
    }
    return record


def main():
    print("=" * 100)
    print("Spike #34 v2 — Donsker-Varadhan survival-with-traps")
    print("=" * 100)
    print("Method: sliding-window minimum-slope β extraction")
    print("Prediction: <S(t)>_traps ~ exp(-c * t^β), β = d_S/(d_S+2)")
    print()

    sierp_dS = 2.0 * math.log(3.0) / math.log(5.0)
    records = []

    rho_values = [0.02, 0.05, 0.10]
    n_real_default = 64
    n_real_torus = 32

    # Sierpinski cascade
    for levels in [4, 5, 6]:
        L, n = build_sierpinski_laplacian(levels)
        print(f"\n--- Sierpinski L={levels} (n={n}) ---")
        for rho in rho_values:
            t0 = time.time()
            rec = analyse_substrate_v2(
                f"sierpinski_L{levels}_rho{rho}", L, n, sierp_dS,
                trap_density=rho, n_realisations=n_real_default,
                seed=42 + levels,
                notes={"canonical_d_S": "2*log(3)/log(5)",
                       "expected_beta_DV": f"{sierp_dS / (sierp_dS + 2.0):.4f}"},
            )
            records.append(rec)
            dv_b = rec['DV_beta'] if rec['DV_beta'] is not None else float('nan')
            dvb_s = f"{dv_b:+.4f}" if dv_b == dv_b else "  n/a"
            db = rec['delta_beta_DV_vs_canonical']
            db_s = f"{db:+.4f}" if db is not None else "  n/a"
            print(f"   rho={rho}: β_DV={dvb_s} (pred {rec['predicted_beta_canonical']:.4f}, "
                  f"Δβ={db_s}), winner_DV={rec['winner_form_DV_window']} "
                  f"r²={rec['winner_r2_DV_window']:.4f}, ({time.time()-t0:.1f}s)", flush=True)

    # Path P_n
    for nn in [256, 512]:
        L = build_path_laplacian(nn)
        print(f"\n--- Path P_{nn} ---")
        for rho in rho_values:
            t0 = time.time()
            rec = analyse_substrate_v2(
                f"path_n{nn}_rho{rho}", L, nn, 1.0,
                trap_density=rho, n_realisations=n_real_default,
                seed=100 + nn,
                notes={"canonical_d_S": "1 (1D path)", "expected_beta_DV": "0.3333"},
            )
            records.append(rec)
            dv_b = rec['DV_beta'] if rec['DV_beta'] is not None else float('nan')
            dvb_s = f"{dv_b:+.4f}" if dv_b == dv_b else "  n/a"
            db = rec['delta_beta_DV_vs_canonical']
            db_s = f"{db:+.4f}" if db is not None else "  n/a"
            print(f"   rho={rho}: β_DV={dvb_s} (pred {rec['predicted_beta_canonical']:.4f}, "
                  f"Δβ={db_s}), winner_DV={rec['winner_form_DV_window']} "
                  f"r²={rec['winner_r2_DV_window']:.4f}, ({time.time()-t0:.1f}s)", flush=True)

    # Cycle C_n
    for nn in [256, 512]:
        L = build_cycle_laplacian(nn)
        print(f"\n--- Cycle C_{nn} ---")
        for rho in rho_values:
            t0 = time.time()
            rec = analyse_substrate_v2(
                f"cycle_n{nn}_rho{rho}", L, nn, 1.0,
                trap_density=rho, n_realisations=n_real_default,
                seed=200 + nn,
                notes={"canonical_d_S": "1 (1D cyclic)", "expected_beta_DV": "0.3333"},
            )
            records.append(rec)
            dv_b = rec['DV_beta'] if rec['DV_beta'] is not None else float('nan')
            dvb_s = f"{dv_b:+.4f}" if dv_b == dv_b else "  n/a"
            db = rec['delta_beta_DV_vs_canonical']
            db_s = f"{db:+.4f}" if db is not None else "  n/a"
            print(f"   rho={rho}: β_DV={dvb_s} (pred {rec['predicted_beta_canonical']:.4f}, "
                  f"Δβ={db_s}), winner_DV={rec['winner_form_DV_window']} "
                  f"r²={rec['winner_r2_DV_window']:.4f}, ({time.time()-t0:.1f}s)", flush=True)

    # Torus
    for side in [16, 24]:
        nn = side * side
        L = build_torus_laplacian(side)
        print(f"\n--- Torus T_{side}x{side} (n={nn}) ---")
        for rho in rho_values:
            t0 = time.time()
            rec = analyse_substrate_v2(
                f"torus_{side}x{side}_n{nn}_rho{rho}", L, nn, 2.0,
                trap_density=rho, n_realisations=n_real_torus,
                seed=300 + side,
                notes={"canonical_d_S": "2 (2D torus)", "expected_beta_DV": "0.5000"},
            )
            records.append(rec)
            dv_b = rec['DV_beta'] if rec['DV_beta'] is not None else float('nan')
            dvb_s = f"{dv_b:+.4f}" if dv_b == dv_b else "  n/a"
            db = rec['delta_beta_DV_vs_canonical']
            db_s = f"{db:+.4f}" if db is not None else "  n/a"
            print(f"   rho={rho}: β_DV={dvb_s} (pred {rec['predicted_beta_canonical']:.4f}, "
                  f"Δβ={db_s}), winner_DV={rec['winner_form_DV_window']} "
                  f"r²={rec['winner_r2_DV_window']:.4f}, ({time.time()-t0:.1f}s)", flush=True)

    # Random 3-regular (NEGATIVE CONTROL)
    for nn in [256, 512]:
        L = build_random_kregular_laplacian(nn, k=3, seed=42)
        print(f"\n--- Random 3-regular n={nn} (NEGATIVE CONTROL) ---")
        for rho in rho_values:
            t0 = time.time()
            rec = analyse_substrate_v2(
                f"random_3reg_n{nn}_rho{rho}", L, nn, float("nan"),
                trap_density=rho, n_realisations=n_real_default,
                seed=400 + nn,
                notes={"canonical_d_S": "undefined (random graph)",
                       "control": "negative"},
            )
            records.append(rec)
            dv_b = rec['DV_beta'] if rec['DV_beta'] is not None else float('nan')
            dvb_s = f"{dv_b:+.4f}" if dv_b == dv_b else "  n/a"
            print(f"   rho={rho}: β_DV={dvb_s}, "
                  f"winner_DV={rec['winner_form_DV_window']} "
                  f"r²={rec['winner_r2_DV_window']:.4f}, ({time.time()-t0:.1f}s)", flush=True)

    # NDJSON output
    from pathlib import Path as _Path
    out_path = str(_Path(__file__).resolve().parent / "spike_34_v2_records_2026-05-17.ndjson")

    def clean(d):
        out = {}
        for k, v in d.items():
            if isinstance(v, (int, str, bool)) or v is None:
                out[k] = v
            elif isinstance(v, float):
                out[k] = None if math.isnan(v) else v
            elif isinstance(v, dict):
                out[k] = clean(v)
            elif isinstance(v, list):
                out[k] = [clean(x) if isinstance(x, dict) else x for x in v]
            elif isinstance(v, (np.floating, np.integer, np.bool_)):
                out[k] = v.item()
            elif isinstance(v, np.ndarray):
                out[k] = v.tolist()
            else:
                out[k] = str(v)
        return out

    with open(out_path, "w") as f:
        for r in records:
            f.write(json.dumps(clean(r)) + "\n")

    print(f"\nWrote {len(records)} records to {out_path}")

    # Print verdict table
    print("\n" + "=" * 100)
    print("VERDICT TABLE — Spike #34 (Donsker-Varadhan survival-with-traps)")
    print("=" * 100)
    print(f"{'substrate':<26s} {'rho':>5s} {'n':>5s} | {'d_S':>6s} {'b_pred':>6s} {'b_DV':>6s} {'Δb':>6s} | "
          f"{'r²_st':>6s} {'r²_sx':>6s} {'r²_pl':>6s} {'winner':>10s}")
    print("-" * 110)
    for r in records:
        d_S = r["predicted_d_S"]
        d_S_s = f"{d_S:.3f}" if d_S is not None else "  n/a"
        b_pred = r["predicted_beta_canonical"]
        b_pred_s = f"{b_pred:.4f}" if b_pred is not None else "  n/a"
        b_DV = r["DV_beta"]
        b_DV_s = f"{b_DV:.4f}" if b_DV is not None else "  n/a"
        db = r["delta_beta_DV_vs_canonical"]
        db_s = f"{db:+.4f}" if db is not None else "  n/a"
        r2_st = r["fit_stretched_exp_DV_window"].get("r2", float("nan"))
        r2_sx = r["fit_single_exp_DV_window"].get("r2", float("nan"))
        r2_pl = r["fit_power_law_DV_window"].get("r2", float("nan"))
        winner = r["winner_form_DV_window"][:10]
        print(f"{r['substrate']:<26s} {r['trap_density_rho']:>5.2f} {r['n_vertices']:>5d} | "
              f"{d_S_s:>6s} {b_pred_s:>6s} {b_DV_s:>6s} {db_s:>6s} | "
              f"{r2_st:>6.3f} {r2_sx:>6.3f} {r2_pl:>6.3f} {winner:>10s}")

    return records


if __name__ == "__main__":
    main()
