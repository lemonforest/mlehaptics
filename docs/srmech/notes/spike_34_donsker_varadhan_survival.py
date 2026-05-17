"""Spike #34 — Donsker-Varadhan literal stretched-exp regime on random-walk
survival probability in randomly placed absorbing traps.

This is the F-3 follow-up from Spike #31. Tests the canonical claim:

    <S(t)>_traps  ~  exp(-c * t^β)   with   β = d_S / (d_S + 2)

where the expectation is over disorder (random trap placement) and
S(t) is the survival probability of a continuous-time random walk
starting from a random free site, with absorbing traps placed
uniformly at density ρ.

References (canonical SSoT per [[feedback_science_is_ssot_not_project]]):

  Donsker, M.D. & Varadhan, S.R.S. (1979). Asymptotic evaluation of
  certain Markov process expectations for large time. IV. Commun.
  Pure Appl. Math. 36 (1979).  [Euclidean derivation β = d/(d+2)]

  Plyukhin, A.V. & Plyukhin, Y. (2016). Stretching exponent for traps.
  arXiv:1610.04801.  [Fractal extension; β = d_S/(d_S+2) on substrates
  of spectral dimension d_S]

Method:
  1. Build substrate Laplacian L (graph-Laplacian, same as Spike #31).
  2. For each of M trap realisations:
       a. Pick N_traps = round(ρ * N) random sites; mark as absorbing.
       b. Restrict L to the (N - N_traps) free sites: L_FF.
       c. Eigendecompose L_FF (cost: O(n_free^3) dense).
       d. Compute S_m(t) = (1/N_free) * 1^T * exp(-t * L_FF) * 1
                          = sum_k c_k * exp(-mu_k * t)
          with c_k = (1^T v_k)^2 / N_free.
       e. The full eigendecomp gives an EXACT continuous-time analytic
          S_m(t) — no Monte-Carlo variance. Disorder noise only.
  3. Average <S(t)> = (1/M) sum_m S_m(t).
  4. Fit log(-log(<S(t)>)) vs log(t) in the asymptotic regime;
     extract empirical β.
  5. Functional-form discrimination: compare stretched-exp r² to
     (a) single-exp r² and (b) power-law r² over the same window.

Output: NDJSON at D:/temp/spike_34/spike_34_records.ndjson.

Author: concertmaster dispatch for Spike #34, 2026-05-16.
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

# Reuse Spike #31 substrate builders
sys.path.insert(0, "D:/temp/spike_31")
from spike_31_stretched_exp_beta import (
    build_sierpinski_laplacian,
    build_path_laplacian,
    build_cycle_laplacian,
    build_torus_laplacian,
    build_random_kregular_laplacian,
)


# ------------------------------------------------------------------------
# Trap-restricted Laplacian + survival probability
# ------------------------------------------------------------------------

def restrict_laplacian_to_free_sites(L: sp.csr_matrix, trap_indices: np.ndarray, n: int) -> np.ndarray:
    """Return L_FF = L restricted to the free (non-trap) sites.

    Dirichlet boundary at traps: physically, when a walker hits a trap it is
    absorbed and never returns. Mathematically, this is equivalent to deleting
    trap rows + columns from L, giving the restricted operator on free sites.

    Returns a dense numpy array of shape (n_free, n_free).
    """
    mask = np.ones(n, dtype=bool)
    mask[trap_indices] = False
    # Dense path: small substrates, exact eigendecomp
    Ld = L.toarray()
    LFF = Ld[np.ix_(mask, mask)]
    return LFF


def survival_probability_single_realisation(LFF: np.ndarray, t_grid: np.ndarray) -> tuple[np.ndarray, dict]:
    """For a single trap realisation, compute S(t) via dense eigendecomposition of L_FF.

    S(t) = (1/N_free) * 1^T * exp(-t * L_FF) * 1
         = sum_k (1^T v_k)^2 / N_free * exp(-mu_k * t)

    where (mu_k, v_k) are eigenpairs of L_FF (which is symmetric PD on free sites
    so long as the free subgraph contains at least one site adjacent to a trap;
    otherwise the connected component without trap-neighbors has a zero mode
    and contributes a constant 1/n_free to S(t) — surviving forever in that
    isolated component).

    Returns:
        S(t) of shape len(t_grid)
        diagnostic dict
    """
    n_free = LFF.shape[0]
    # Symmetric so use eigvalsh; we need eigenvectors too.
    mu, V = sla.eigh(LFF)
    # Initial-state amplitudes for uniform initial distribution
    one = np.ones(n_free)
    a = V.T @ one  # shape (n_free,)
    # c_k = a_k^2 / N_free
    c = (a * a) / n_free
    # S(t) = sum_k c_k * exp(-mu_k * t)
    # Vectorise: exp(-outer(t_grid, mu)) shape (len(t), n_free)
    # For large n_free this is expensive; chunk.
    S = np.zeros_like(t_grid)
    chunk = 512
    for i0 in range(0, n_free, chunk):
        i1 = min(i0 + chunk, n_free)
        block_mu = mu[i0:i1]
        block_c = c[i0:i1]
        S += np.exp(-np.outer(t_grid, block_mu)) @ block_c
    diag = {
        "n_free": int(n_free),
        "mu_min": float(mu.min()),
        "mu_max": float(mu.max()),
        "n_zero_modes": int(np.sum(np.abs(mu) < 1e-10)),
    }
    return S, diag


def survival_probability_disorder_averaged(
    L: sp.csr_matrix,
    n: int,
    trap_density: float,
    n_realisations: int,
    t_grid: np.ndarray,
    seed: int = 42,
) -> tuple[np.ndarray, list[dict]]:
    """Disorder-averaged survival probability <S(t)>_traps.

    Returns:
        <S(t)> averaged over n_realisations trap configurations
        list of per-realisation diagnostics
    """
    rng = np.random.default_rng(seed)
    S_avg = np.zeros_like(t_grid)
    diags = []
    n_traps = max(1, int(round(trap_density * n)))
    for m in range(n_realisations):
        trap_indices = rng.choice(n, size=n_traps, replace=False)
        LFF = restrict_laplacian_to_free_sites(L, trap_indices, n)
        S, diag = survival_probability_single_realisation(LFF, t_grid)
        S_avg += S
        diag["realisation"] = m
        diag["n_traps"] = n_traps
        diags.append(diag)
    S_avg /= n_realisations
    return S_avg, diags


# ------------------------------------------------------------------------
# Spectral dimension (reuse Weyl-density method from Spike #31)
# ------------------------------------------------------------------------

def empirical_d_S(L: sp.csr_matrix, frac: float = 0.10) -> float:
    """Empirical d_S from full-spectrum Weyl asymptotic; same as Spike #31."""
    eigs = sla.eigvalsh(L.toarray())
    nz = np.sort(eigs[eigs > 1e-10])
    counts = np.arange(1, len(nz) + 1).astype(float)
    nfit = max(10, int(len(nz) * frac))
    nfit = min(nfit, len(nz) - 1)
    p = np.polyfit(np.log(nz[:nfit]), np.log(counts[:nfit]), 1)
    return 2.0 * p[0]


# ------------------------------------------------------------------------
# Functional-form discrimination: stretched-exp vs single-exp vs power-law
# ------------------------------------------------------------------------

def fit_stretched_exp(t: np.ndarray, S: np.ndarray, lo: float, hi: float) -> dict:
    """Fit log(-log(S)) vs log(t); linearisation of S = exp(-(t/tau)^beta).

    Window mask: keep points where S in (lo, hi).

    Returns dict with beta, tau, r2, n_fit, t_min, t_max, S_min, S_max.
    """
    mask = (S > lo) & (S < hi)
    if mask.sum() < 5:
        return {"form": "stretched_exp", "beta": float("nan"), "tau": float("nan"),
                "r2": 0.0, "n_fit": int(mask.sum()), "reason": "insufficient points"}
    y = np.log(-np.log(S[mask]))
    x = np.log(t[mask])
    p = np.polyfit(x, y, 1)
    beta = p[0]
    intercept = p[1]
    tau = math.exp(-intercept / beta) if abs(beta) > 1e-12 else float("nan")
    yhat = np.polyval(p, x)
    ss_res = ((y - yhat) ** 2).sum()
    ss_tot = ((y - y.mean()) ** 2).sum()
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-15 else 1.0
    return {"form": "stretched_exp", "beta": float(beta), "tau": float(tau),
            "r2": float(r2), "n_fit": int(mask.sum()),
            "t_min": float(t[mask].min()), "t_max": float(t[mask].max()),
            "S_min": float(S[mask].min()), "S_max": float(S[mask].max())}


def fit_single_exp(t: np.ndarray, S: np.ndarray, lo: float, hi: float) -> dict:
    """Fit log(S) vs t; linearisation of S = A*exp(-k*t)."""
    mask = (S > lo) & (S < hi)
    if mask.sum() < 5:
        return {"form": "single_exp", "k": float("nan"), "log_A": float("nan"),
                "r2": 0.0, "n_fit": int(mask.sum()), "reason": "insufficient points"}
    y = np.log(S[mask])
    x = t[mask]
    p = np.polyfit(x, y, 1)
    k = -p[0]
    log_A = p[1]
    yhat = np.polyval(p, x)
    ss_res = ((y - yhat) ** 2).sum()
    ss_tot = ((y - y.mean()) ** 2).sum()
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-15 else 1.0
    return {"form": "single_exp", "k": float(k), "log_A": float(log_A),
            "r2": float(r2), "n_fit": int(mask.sum()),
            "t_min": float(x.min()), "t_max": float(x.max())}


def fit_power_law(t: np.ndarray, S: np.ndarray, lo: float, hi: float) -> dict:
    """Fit log(S) vs log(t); linearisation of S = A * t^p."""
    mask = (S > lo) & (S < hi)
    if mask.sum() < 5:
        return {"form": "power_law", "exponent": float("nan"), "log_A": float("nan"),
                "r2": 0.0, "n_fit": int(mask.sum()), "reason": "insufficient points"}
    y = np.log(S[mask])
    x = np.log(t[mask])
    p = np.polyfit(x, y, 1)
    yhat = np.polyval(p, x)
    ss_res = ((y - yhat) ** 2).sum()
    ss_tot = ((y - y.mean()) ** 2).sum()
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-15 else 1.0
    return {"form": "power_law", "exponent": float(p[0]), "log_A": float(p[1]),
            "r2": float(r2), "n_fit": int(mask.sum())}


# ------------------------------------------------------------------------
# Per-substrate analysis
# ------------------------------------------------------------------------

def analyse_substrate(
    name: str,
    L: sp.csr_matrix,
    n: int,
    predicted_d_S: float,
    trap_density: float,
    n_realisations: int,
    n_t_pts: int = 256,
    seed: int = 42,
    notes: dict | None = None,
) -> dict:
    """Full per-substrate Donsker-Varadhan survival analysis.

    Returns a record dict.
    """
    t0 = time.time()

    # 1. Empirical d_S (full unrestricted L spectrum, same as Spike #31)
    d_S_emp = empirical_d_S(L)
    predicted_beta = (
        predicted_d_S / (predicted_d_S + 2.0)
        if not math.isnan(predicted_d_S) else float("nan")
    )

    # 2. Build t-grid: capture asymptotic regime up to where S becomes small
    # Probe lambda_min, lambda_max from FULL L (free-site L_FF will be similar)
    eigs = sla.eigvalsh(L.toarray())
    nz = eigs[eigs > 1e-10]
    lam_min = float(nz[0])
    lam_max = float(nz[-1])
    # t span: from ~1/lam_max (fastest mode just decayed) to where S ~ 1e-4
    # For Donsker-Varadhan asymptotic, need t such that t * lam_min >> 1
    t_lo = 0.1 / lam_max
    t_hi = 50.0 / lam_min
    t_grid = np.geomspace(t_lo, t_hi, n_t_pts)

    # 3. Disorder-averaged S(t)
    t_S0 = time.time()
    S_avg, diags = survival_probability_disorder_averaged(
        L, n, trap_density, n_realisations, t_grid, seed=seed,
    )
    t_S = time.time() - t_S0

    # 4. Functional-form discrimination at LOOSE window (S in [1e-3, 1 - 1e-3])
    # Donsker-Varadhan asymptotic kicks in once S is well-below 1.
    LOOSE_LO, LOOSE_HI = 1e-3, 1.0 - 1e-3
    fit_st_loose = fit_stretched_exp(t_grid, S_avg, LOOSE_LO, LOOSE_HI)
    fit_sx_loose = fit_single_exp(t_grid, S_avg, LOOSE_LO, LOOSE_HI)
    fit_pl_loose = fit_power_law(t_grid, S_avg, LOOSE_LO, LOOSE_HI)

    # 5. Tail window — should be MOST asymptotic regime
    TAIL_LO, TAIL_HI = 1e-4, 1e-1
    fit_st_tail = fit_stretched_exp(t_grid, S_avg, TAIL_LO, TAIL_HI)
    fit_sx_tail = fit_single_exp(t_grid, S_avg, TAIL_LO, TAIL_HI)
    fit_pl_tail = fit_power_law(t_grid, S_avg, TAIL_LO, TAIL_HI)

    # 6. Determine functional-form winner at tail
    fits_tail = [fit_st_tail, fit_sx_tail, fit_pl_tail]
    valid_fits = [f for f in fits_tail if not math.isnan(f["r2"]) and f["n_fit"] >= 5]
    if valid_fits:
        winner = max(valid_fits, key=lambda f: f["r2"])
        winner_form = winner["form"]
        winner_r2 = winner["r2"]
    else:
        winner_form = "insufficient_data"
        winner_r2 = float("nan")

    t_total = time.time() - t0

    return {
        "substrate": name,
        "n_vertices": int(n),
        "trap_density_rho": float(trap_density),
        "n_traps": diags[0]["n_traps"] if diags else 0,
        "n_realisations": int(n_realisations),
        "lambda_min_nonzero": lam_min,
        "lambda_max": lam_max,
        "predicted_d_S": float(predicted_d_S) if not math.isnan(predicted_d_S) else None,
        "empirical_d_S": float(d_S_emp),
        "predicted_beta_canonical": float(predicted_beta) if not math.isnan(predicted_beta) else None,
        # Loose-window fits
        "fit_stretched_exp_loose": fit_st_loose,
        "fit_single_exp_loose": fit_sx_loose,
        "fit_power_law_loose": fit_pl_loose,
        "delta_beta_loose": (
            float(fit_st_loose["beta"] - predicted_beta)
            if not math.isnan(fit_st_loose["beta"]) and not math.isnan(predicted_beta)
            else None
        ),
        # Tail-window fits (Donsker-Varadhan asymptotic regime)
        "fit_stretched_exp_tail": fit_st_tail,
        "fit_single_exp_tail": fit_sx_tail,
        "fit_power_law_tail": fit_pl_tail,
        "delta_beta_tail": (
            float(fit_st_tail["beta"] - predicted_beta)
            if not math.isnan(fit_st_tail["beta"]) and not math.isnan(predicted_beta)
            else None
        ),
        # Winner
        "winner_form_tail": winner_form,
        "winner_r2_tail": float(winner_r2) if not math.isnan(winner_r2) else None,
        # Spectrum sanity
        "n_realisations_diag": diags,
        "time_survival_seconds": float(t_S),
        "time_total_seconds": float(t_total),
        "S_avg_t_grid_sample": {
            "t_min": float(t_grid.min()),
            "t_max": float(t_grid.max()),
            "S_min": float(S_avg.min()),
            "S_max": float(S_avg.max()),
        },
        "notes": notes or {},
    }


# ------------------------------------------------------------------------
# Main — sweep
# ------------------------------------------------------------------------

def main():
    print("=" * 100)
    print("Spike #34 — Donsker-Varadhan literal stretched-exp regime on")
    print("            random-walk survival probability with random traps")
    print("=" * 100)
    print("Canonical SSoT:")
    print("  Donsker-Varadhan 1979 (Euclidean β = d/(d+2))")
    print("  Plyukhin-Plyukhin arXiv:1610.04801 (fractal β = d_S/(d_S+2))")
    print()
    print("Prediction:  <S(t)>_traps  ~  exp(-c * t^β)  with  β = d_S/(d_S+2)")
    print()

    sierp_dS = 2.0 * math.log(3.0) / math.log(5.0)
    records = []

    # Trap density sweep diagnostic — F4 falsifier
    rho_values = [0.02, 0.05, 0.10]
    n_realisations = 32

    # Sierpinski cascade — load-bearing
    for levels in [4, 5, 6]:  # n=42, 123, 366; level 7 = 1095 (slow w/ realisations)
        print(f"--- Sierpinski levels={levels} ---")
        L, n = build_sierpinski_laplacian(levels)
        print(f"   n_vertices = {n}", flush=True)
        for rho in rho_values:
            t0 = time.time()
            rec = analyse_substrate(
                f"sierpinski_levels_{levels}_rho_{rho}", L, n, sierp_dS,
                trap_density=rho, n_realisations=n_realisations,
                seed=42 + levels,
                notes={"canonical_d_S_source": "Rammal-Toulouse 1983",
                       "canonical_d_S_formula": "2*log(3)/log(5)",
                       "predicted_beta_DV": f"{sierp_dS / (sierp_dS + 2.0):.4f}"},
            )
            records.append(rec)
            print(f"   rho={rho}: beta_tail={rec['fit_stretched_exp_tail']['beta']:+.4f} "
                  f"(pred {rec['predicted_beta_canonical']:.4f}, "
                  f"Δβ={rec['delta_beta_tail']:+.4f}), "
                  f"r²_st={rec['fit_stretched_exp_tail']['r2']:.4f}, "
                  f"r²_sx={rec['fit_single_exp_tail']['r2']:.4f}, "
                  f"r²_pl={rec['fit_power_law_tail']['r2']:.4f}, "
                  f"winner={rec['winner_form_tail']}, "
                  f"({time.time()-t0:.1f}s)", flush=True)

    # Path P_n — 1D baseline
    for nn in [256, 512]:
        print(f"--- Path P_{nn} ---")
        L = build_path_laplacian(nn)
        for rho in rho_values:
            t0 = time.time()
            rec = analyse_substrate(
                f"path_n_{nn}_rho_{rho}", L, nn, 1.0,
                trap_density=rho, n_realisations=n_realisations,
                seed=100 + nn,
                notes={"canonical_d_S_formula": "1 (1D path)",
                       "predicted_beta_DV": "0.3333"},
            )
            records.append(rec)
            print(f"   rho={rho}: beta_tail={rec['fit_stretched_exp_tail']['beta']:+.4f} "
                  f"(pred {rec['predicted_beta_canonical']:.4f}, "
                  f"Δβ={rec['delta_beta_tail']:+.4f}), "
                  f"r²_st={rec['fit_stretched_exp_tail']['r2']:.4f}, "
                  f"r²_sx={rec['fit_single_exp_tail']['r2']:.4f}, "
                  f"r²_pl={rec['fit_power_law_tail']['r2']:.4f}, "
                  f"winner={rec['winner_form_tail']}, "
                  f"({time.time()-t0:.1f}s)", flush=True)

    # Cycle C_n — 1D cyclic baseline
    for nn in [256, 512]:
        print(f"--- Cycle C_{nn} ---")
        L = build_cycle_laplacian(nn)
        for rho in rho_values:
            t0 = time.time()
            rec = analyse_substrate(
                f"cycle_n_{nn}_rho_{rho}", L, nn, 1.0,
                trap_density=rho, n_realisations=n_realisations,
                seed=200 + nn,
                notes={"canonical_d_S_formula": "1 (1D cyclic)",
                       "predicted_beta_DV": "0.3333"},
            )
            records.append(rec)
            print(f"   rho={rho}: beta_tail={rec['fit_stretched_exp_tail']['beta']:+.4f} "
                  f"(pred {rec['predicted_beta_canonical']:.4f}, "
                  f"Δβ={rec['delta_beta_tail']:+.4f}), "
                  f"r²_st={rec['fit_stretched_exp_tail']['r2']:.4f}, "
                  f"r²_sx={rec['fit_single_exp_tail']['r2']:.4f}, "
                  f"r²_pl={rec['fit_power_law_tail']['r2']:.4f}, "
                  f"winner={rec['winner_form_tail']}, "
                  f"({time.time()-t0:.1f}s)", flush=True)

    # Torus C_n x C_n — 2D baseline
    for side in [16, 24]:  # n=256, 576
        nn = side * side
        print(f"--- Torus T_{side}x{side} (n={nn}) ---")
        L = build_torus_laplacian(side)
        for rho in rho_values:
            t0 = time.time()
            rec = analyse_substrate(
                f"torus_{side}x{side}_n_{nn}_rho_{rho}", L, nn, 2.0,
                trap_density=rho, n_realisations=n_realisations,
                seed=300 + side,
                notes={"canonical_d_S_formula": "2 (2D torus)",
                       "predicted_beta_DV": "0.5000"},
            )
            records.append(rec)
            print(f"   rho={rho}: beta_tail={rec['fit_stretched_exp_tail']['beta']:+.4f} "
                  f"(pred {rec['predicted_beta_canonical']:.4f}, "
                  f"Δβ={rec['delta_beta_tail']:+.4f}), "
                  f"r²_st={rec['fit_stretched_exp_tail']['r2']:.4f}, "
                  f"r²_sx={rec['fit_single_exp_tail']['r2']:.4f}, "
                  f"r²_pl={rec['fit_power_law_tail']['r2']:.4f}, "
                  f"winner={rec['winner_form_tail']}, "
                  f"({time.time()-t0:.1f}s)", flush=True)

    # Negative control: random 3-regular
    for nn in [256, 512]:
        print(f"--- Random 3-regular n={nn} (NEGATIVE CONTROL) ---")
        L = build_random_kregular_laplacian(nn, k=3, seed=42)
        for rho in rho_values:
            t0 = time.time()
            rec = analyse_substrate(
                f"random_3regular_n_{nn}_rho_{rho}", L, nn, float("nan"),
                trap_density=rho, n_realisations=n_realisations,
                seed=400 + nn,
                notes={"canonical_d_S_formula": "undefined (random graph)",
                       "control": "negative — not cascade substrate"},
            )
            records.append(rec)
            print(f"   rho={rho}: beta_tail={rec['fit_stretched_exp_tail']['beta']:+.4f}, "
                  f"r²_st={rec['fit_stretched_exp_tail']['r2']:.4f}, "
                  f"r²_sx={rec['fit_single_exp_tail']['r2']:.4f}, "
                  f"r²_pl={rec['fit_power_law_tail']['r2']:.4f}, "
                  f"winner={rec['winner_form_tail']}, "
                  f"({time.time()-t0:.1f}s)", flush=True)

    # Write NDJSON
    from pathlib import Path as _Path
    out_path = str(_Path(__file__).resolve().parent / "spike_34_records_2026-05-17.ndjson")
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
            # Drop the bulky diag list to keep records compact
            r2 = {k: v for k, v in r.items() if k != "n_realisations_diag"}
            r2["n_realisations_diag_summary"] = {
                "n_realisations": len(r["n_realisations_diag"]),
                "n_free_first": r["n_realisations_diag"][0]["n_free"] if r["n_realisations_diag"] else None,
                "mu_min_avg": float(np.mean([d["mu_min"] for d in r["n_realisations_diag"]])) if r["n_realisations_diag"] else None,
            }
            f.write(json.dumps(clean(r2)) + "\n")
    print(f"\nWrote {len(records)} records to {out_path}")
    return records


if __name__ == "__main__":
    main()
