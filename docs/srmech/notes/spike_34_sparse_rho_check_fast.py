"""Sparse-rho check FAST — smaller substrates, fewer realisations."""

from __future__ import annotations

import io
import math
import sys
import time

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

import numpy as np
import scipy.linalg as sla

sys.path.insert(0, "D:/temp/spike_31")
from spike_31_stretched_exp_beta import (
    build_path_laplacian, build_cycle_laplacian, build_torus_laplacian,
    build_sierpinski_laplacian,
)

sys.path.insert(0, "D:/temp/spike_34")
from spike_34_donsker_varadhan_survival import survival_probability_disorder_averaged
from spike_34_v2_production import extract_DV_beta


def sweep(name, L, n, predicted_dS, rho_list, n_real):
    print(f"\n=== {name} (n={n}, d_S_pred={predicted_dS}) ===", flush=True)
    pred_beta = predicted_dS / (predicted_dS + 2.0)
    print(f"   Predicted β = {pred_beta:.4f}", flush=True)
    eigs = sla.eigvalsh(L.toarray())
    nz = np.sort(eigs[eigs > 1e-10])
    lam_min, lam_max = nz[0], nz[-1]
    for rho in rho_list:
        n_traps = max(1, int(round(rho * n)))
        if n_traps < 1 or n - n_traps < 3:
            print(f"   rho={rho}: SKIP (n_traps={n_traps})", flush=True)
            continue
        t_grid = np.geomspace(0.01/lam_max, 200.0/lam_min, 512)
        t0 = time.time()
        S_avg, _ = survival_probability_disorder_averaged(L, n, rho, n_real, t_grid, seed=42)
        dv = extract_DV_beta(t_grid, S_avg, r2_threshold=0.999, win=30, step=3)
        beta = dv['beta_DV']
        dt = time.time() - t0
        if beta == beta:  # not NaN
            print(f"   rho={rho:>6.3f} (n_traps={n_traps:>4d}): β_DV={beta:+.4f}, "
                  f"Δβ={beta-pred_beta:+.4f}, S_min={dv['S_at_min']:.3e} "
                  f"({dt:.1f}s)", flush=True)
        else:
            print(f"   rho={rho:>6.3f}: β_DV=NaN ({dt:.1f}s)", flush=True)


def main():
    # Path P_1024
    L = build_path_laplacian(1024)
    sweep("Path P_1024", L, 1024, 1.0,
          rho_list=[0.005, 0.01, 0.02, 0.05, 0.10, 0.20], n_real=32)

    # Cycle C_1024
    L = build_cycle_laplacian(1024)
    sweep("Cycle C_1024", L, 1024, 1.0,
          rho_list=[0.005, 0.01, 0.02, 0.05, 0.10, 0.20], n_real=32)

    # Sierpinski L=6 (n=1095)
    L, n = build_sierpinski_laplacian(6)
    sierp_dS = 2.0 * math.log(3.0) / math.log(5.0)
    sweep(f"Sierpinski L=6 (n={n})", L, n, sierp_dS,
          rho_list=[0.005, 0.01, 0.02, 0.05, 0.10, 0.20], n_real=32)

    # Torus T_24 (n=576)
    L = build_torus_laplacian(24)
    sweep("Torus T_24x24 (n=576)", L, 576, 2.0,
          rho_list=[0.005, 0.01, 0.02, 0.05, 0.10, 0.20], n_real=24)


if __name__ == "__main__":
    main()
