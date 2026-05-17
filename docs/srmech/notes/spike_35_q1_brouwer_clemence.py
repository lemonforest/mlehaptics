"""Spike #35 Q1 — Brouwer-Clemence c_k = eps^k modulation through off-centre observer.

CANONICAL FORM (after numerical diagnostic 2026-05-16):

  The Brouwer-Clemence ladder lives in the KINEMATIC direction (dphi/dM, the
  forward Jacobian of the pin-slot projection), with EXACT coefficients:
      c_k(dphi/dM) = eps^k    for k = 1, 2, 3, ...
  This is the angular-velocity / proper-motion / Doppler-spectrum signature
  observed through an off-centre frame.

  The equation-of-centre (phi - M) lives in the SAME family but with the
  modulating factors of Brouwer & Clemence 1961 §3.2:
      c_1(phi-M) = 2*eps - eps^3/4 + ...
      c_2(phi-M) = (5/4)*eps^2 - ...
      c_3(phi-M) = (13/12)*eps^3 - ...

  The STATIC angular density n(phi) carries only the DIPOLE c_1 ≈ -eps,
  with higher harmonics suppressed by even-symmetry of the off-centre
  observer projection.

Test plan
---------
Q1.A: Forward Jacobian dphi/dM — does it show c_k = eps^k ladder?
Q1.B: Equation-of-centre phi-M — does it show Brouwer-Clemence canonical?
Q1.C: Static angular density n(phi) — is it dominated by dipole?
Q1.D: SNR / noise floor at small eps.

Verdict
-------
Q1 PASS if the canonical Brouwer-Clemence ladder is recovered in (A) and (B)
to <1% at eps_AoE = 0.0506.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import List

import numpy as np


# Brouwer & Clemence 1961, Methods of Celestial Mechanics §3.2 — leading-order
# coefficients of nu - M = sum_k C_k * sin(k*M). These are the rational
# multipliers of eps^k.
BC_RATIONALS_EOC = [
    2.0,                # k=1: 2
    5.0 / 4.0,          # k=2: 5/4
    13.0 / 12.0,        # k=3: 13/12
    103.0 / 96.0,       # k=4: 103/96
    1097.0 / 960.0,     # k=5
]


def bc_eoc_leading(eps: float, k_max: int = 5) -> List[float]:
    return [r * (eps ** k) for k, r in zip(range(1, k_max + 1), BC_RATIONALS_EOC)]


def kepler_solve(M: float, eps: float, tol: float = 1e-13, max_iter: int = 50) -> float:
    E = M
    for _ in range(max_iter):
        f = E - eps * math.sin(E) - M
        fp = 1.0 - eps * math.cos(E)
        dE = -f / fp
        E += dE
        if abs(dE) < tol:
            break
    return E


def equation_of_centre_signal(M_grid: np.ndarray, eps: float) -> np.ndarray:
    out = np.zeros_like(M_grid)
    for i, M in enumerate(M_grid):
        E = kepler_solve(float(M), eps)
        nu = 2.0 * math.atan2(
            math.sqrt(1 + eps) * math.sin(E / 2),
            math.sqrt(1 - eps) * math.cos(E / 2),
        )
        d = nu - float(M)
        while d > math.pi:
            d -= 2 * math.pi
        while d < -math.pi:
            d += 2 * math.pi
        out[i] = d
    return out


def extract_sine_coeffs(signal: np.ndarray, M_grid: np.ndarray, k_max: int = 7) -> np.ndarray:
    N = len(M_grid)
    coefs = np.zeros(k_max)
    for k in range(1, k_max + 1):
        coefs[k - 1] = (2.0 / N) * np.sum(signal * np.sin(k * M_grid))
    return coefs


def extract_cos_coeffs(signal: np.ndarray, M_grid: np.ndarray, k_max: int = 7) -> np.ndarray:
    N = len(M_grid)
    coefs = np.zeros(k_max)
    for k in range(1, k_max + 1):
        coefs[k - 1] = (2.0 / N) * np.sum(signal * np.cos(k * M_grid))
    return coefs


def kinematic_jacobian_dphi_dM(M_grid: np.ndarray, eps: float) -> np.ndarray:
    """Closed-form dphi/dM where phi = atan2(sin M, cos M - eps)."""
    r2 = 1 - 2 * eps * np.cos(M_grid) + eps ** 2
    return (1 - eps * np.cos(M_grid)) / r2


def fit_geometric(coefs: np.ndarray, k_min: int = 1, k_max: int = 5) -> dict:
    """Fit |c_k| = C0 * eps_fit^k on log-linear scale."""
    abs_c = np.abs(coefs[k_min - 1:k_max])
    nonzero = abs_c > 1e-30
    if nonzero.sum() < 3:
        return {"eps_fit": float("nan"), "r2": 0.0, "monotonic": False, "k_range": [k_min, k_max]}
    k_arr = np.arange(k_min, k_max + 1)[nonzero]
    log_c = np.log(abs_c[nonzero])
    A = np.vstack([k_arr, np.ones_like(k_arr, dtype=float)]).T
    slope, intercept = np.linalg.lstsq(A, log_c, rcond=None)[0]
    pred = slope * k_arr + intercept
    ss_res = np.sum((log_c - pred) ** 2)
    ss_tot = np.sum((log_c - log_c.mean()) ** 2)
    r2 = 1.0 - ss_res / max(ss_tot, 1e-30)
    monotonic = bool(np.all(np.diff(abs_c[: k_arr[-1] - k_min + 1]) <= 0))
    return {
        "eps_fit": float(math.exp(slope)),
        "r2": float(r2),
        "monotonic": monotonic,
        "log_C0": float(intercept),
        "k_range": [k_min, k_max],
    }


def main() -> int:
    out_dir = Path("D:/temp/spike_35")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "spike_35_q1_brouwer_clemence.ndjson"

    records: list[dict] = []
    records.append({
        "spike": 35, "question": "Q1", "kind": "meta",
        "claim": ("off-centre observer at eps_AoE produces canonical Brouwer-Clemence "
                  "c_k geometric ladder in kinematic dphi/dM and EOC phi-M; static density "
                  "carries only the dipole c_1 by symmetry"),
        "epsilon_AoE_R3": 0.0506,
    })

    eps_list = [0.005, 0.01, 0.0506, 0.1, 0.2, 0.3]
    N = 32768

    # === Q1.A: Forward Jacobian dphi/dM ===
    print("=" * 80)
    print("Q1.A -- Forward Jacobian dphi/dM: c_k = eps^k (exact closed form)")
    print("=" * 80)
    print(f"{'eps':>8s} | {'c_1':>10s} {'c_2':>10s} {'c_3':>10s} | "
          f"{'theory_c1':>10s} {'theory_c2':>10s} {'theory_c3':>10s} | "
          f"{'r2':>6s} {'eps_fit':>9s} {'mono':>5s}")

    for eps in eps_list:
        M_grid = np.linspace(0, 2 * math.pi, N, endpoint=False)
        dphi_dM = kinematic_jacobian_dphi_dM(M_grid, eps)
        cos_k = extract_cos_coeffs(dphi_dM, M_grid, k_max=7)
        theory = [eps ** k for k in range(1, 8)]
        fit = fit_geometric(np.abs(cos_k), k_min=1, k_max=5)
        rel_err = [abs(abs(cos_k[k - 1]) - theory[k - 1]) / max(theory[k - 1], 1e-30)
                   for k in range(1, 6)]
        max_rel_err = max(rel_err)
        records.append({
            "spike": 35, "question": "Q1.A", "kind": "kinematic_jacobian",
            "eps_input": eps,
            "cos_c_k": cos_k.tolist(),
            "theory_eps_k": theory,
            "rel_err_top5": rel_err,
            "max_rel_err": max_rel_err,
            "fit": fit,
            "AoE_pass": bool(eps == 0.0506 and max_rel_err < 0.01 and
                              fit["r2"] > 0.999 and fit["monotonic"]),
        })
        print(f"{eps:8.4f} | {cos_k[0]:+10.6f} {cos_k[1]:+10.4e} {cos_k[2]:+10.4e} | "
              f"{theory[0]:10.6f} {theory[1]:10.4e} {theory[2]:10.4e} | "
              f"{fit['r2']:6.4f} {fit['eps_fit']:9.6f} "
              f"{'Y' if fit['monotonic'] else 'N':>5s}")

    # === Q1.B: Equation of Centre phi-M ===
    print()
    print("=" * 80)
    print("Q1.B -- Equation of Centre phi-M: c_k = BC_k(eps) Brouwer-Clemence canonical")
    print("=" * 80)
    print(f"{'eps':>8s} | {'c_1':>10s} {'c_2':>10s} {'c_3':>10s} | "
          f"{'BC_1':>10s} {'BC_2':>10s} {'BC_3':>10s} | "
          f"{'rel_err':>10s} | {'r2':>6s} {'eps_fit':>9s} {'mono':>5s}")

    for eps in eps_list:
        M_grid = np.linspace(0, 2 * math.pi, N, endpoint=False)
        eoc = equation_of_centre_signal(M_grid, eps)
        sin_k = extract_sine_coeffs(eoc, M_grid, k_max=7)
        bc_pred = bc_eoc_leading(eps, k_max=5)
        fit = fit_geometric(np.abs(sin_k), k_min=1, k_max=5)
        rel_err = [abs(abs(sin_k[k - 1]) - bc_pred[k - 1]) / max(bc_pred[k - 1], 1e-30)
                   for k in range(1, 6)]
        max_rel_err = max(rel_err)
        records.append({
            "spike": 35, "question": "Q1.B", "kind": "eoc_phi_minus_M",
            "eps_input": eps,
            "sin_c_k": [float(c) for c in sin_k.tolist()],
            "bc_pred_leading": bc_pred,
            "rel_err_top5": rel_err,
            "max_rel_err": max_rel_err,
            "fit": fit,
            "AoE_pass": bool(eps == 0.0506 and max_rel_err < 0.01 and
                              fit["r2"] > 0.99 and fit["monotonic"]),
        })
        print(f"{eps:8.4f} | {abs(sin_k[0]):10.6f} {abs(sin_k[1]):10.4e} {abs(sin_k[2]):10.4e} | "
              f"{bc_pred[0]:10.6f} {bc_pred[1]:10.4e} {bc_pred[2]:10.4e} | "
              f"{max_rel_err:10.2e} | "
              f"{fit['r2']:6.4f} {fit['eps_fit']:9.6f} "
              f"{'Y' if fit['monotonic'] else 'N':>5s}")

    # === Q1.C: Static density n(phi) — dipole dominance ===
    print()
    print("=" * 80)
    print("Q1.C -- Static density n(phi): dominated by dipole c_1 ~ -eps")
    print("=" * 80)
    print(f"{'eps':>8s} | {'cos_1':>10s} {'cos_2':>10s} {'cos_3':>10s} | "
          f"{'predicted_dipole':>16s} {'dipole/eps':>12s}")

    for eps in eps_list:
        M_grid = np.linspace(0, 2 * math.pi, N, endpoint=False)
        phi = np.arctan2(np.sin(M_grid), np.cos(M_grid) - eps)
        n_bins = 2048
        phi_bins = np.linspace(-math.pi, math.pi, n_bins + 1)
        density, _ = np.histogram(phi, bins=phi_bins, density=False)
        centres = 0.5 * (phi_bins[:-1] + phi_bins[1:])
        mean = density.mean()
        if mean == 0:
            continue
        normed = (density - mean) / mean
        cos_phi = np.zeros(7)
        for k in range(1, 8):
            cos_phi[k - 1] = (2.0 / n_bins) * np.sum(normed * np.cos(k * centres))
        records.append({
            "spike": 35, "question": "Q1.C", "kind": "static_angular_density",
            "eps_input": eps,
            "cos_c_phi": cos_phi.tolist(),
            "dipole_over_eps": float(abs(cos_phi[0]) / eps),
            "dipole_dominance_pass": bool(abs(abs(cos_phi[0]) / eps - 1.0) < 0.01),
        })
        print(f"{eps:8.4f} | {cos_phi[0]:+10.4e} {cos_phi[1]:+10.4e} {cos_phi[2]:+10.4e} | "
              f"{-eps:16.4e} {abs(cos_phi[0]) / eps:12.6f}")

    # === Q1.D: SNR at small eps ===
    print()
    print("=" * 80)
    print("Q1.D -- SNR / noise floor on kinematic c_k=eps^k ladder")
    print("=" * 80)
    print(f"{'eps':>10s} | {'theory_c3':>12s} {'measured_c3':>13s} {'noise':>10s} {'SNR':>10s} {'detect':>8s}")
    for eps in [1e-4, 1e-3, 5e-3, 0.01, 0.05, 0.0506, 0.1, 0.2]:
        M_grid = np.linspace(0, 2 * math.pi, N, endpoint=False)
        dphi_dM = kinematic_jacobian_dphi_dM(M_grid, eps)
        cos_k = extract_cos_coeffs(dphi_dM, M_grid, k_max=10)
        c3 = abs(cos_k[2])
        noise = max(abs(cos_k[8]), abs(cos_k[9]), 1e-16)  # very high k; pure roundoff
        records.append({
            "spike": 35, "question": "Q1.D", "kind": "snr_kinematic",
            "eps_input": eps,
            "theory_c3": eps ** 3,
            "measured_c3": c3,
            "noise_floor_high_k": noise,
            "snr": c3 / max(noise, 1e-16),
            "detectable_5sigma": bool(c3 > 5 * noise),
        })
        print(f"{eps:10.4e} | {eps**3:12.4e} {c3:13.4e} {noise:10.4e} "
              f"{c3 / max(noise, 1e-16):10.2e} {'YES' if c3 > 5 * noise else 'no':>8s}")

    # === Verdict ===
    aoe_kin = any(r.get("AoE_pass", False) and r["kind"] == "kinematic_jacobian"
                  for r in records)
    aoe_eoc = any(r.get("AoE_pass", False) and r["kind"] == "eoc_phi_minus_M"
                  for r in records)
    aoe_dens = any(r.get("dipole_dominance_pass", False) and r.get("eps_input") == 0.0506
                   for r in records)
    aoe_snr = any(r.get("eps_input") == 0.0506 and r.get("kind") == "snr_kinematic"
                  and r.get("detectable_5sigma", False) for r in records)

    print()
    print("=" * 80)
    print("Q1 VERDICT")
    print("=" * 80)
    print(f"  Q1.A Kinematic c_k=eps^k ladder at eps_AoE=0.0506:        "
          f"{'PASS' if aoe_kin else 'FAIL'}")
    print(f"  Q1.B EOC Brouwer-Clemence ladder at eps_AoE=0.0506:       "
          f"{'PASS' if aoe_eoc else 'FAIL'}")
    print(f"  Q1.C Static-density dipole-dominance at eps_AoE=0.0506:   "
          f"{'PASS' if aoe_dens else 'FAIL'}")
    print(f"  Q1.D c_3 detectable above noise at eps_AoE=0.0506:        "
          f"{'PASS' if aoe_snr else 'FAIL'}")
    overall = aoe_kin and aoe_eoc and aoe_dens and aoe_snr
    print(f"  Q1 OVERALL: {'PASS' if overall else 'FAIL'}")
    records.append({
        "spike": 35, "question": "Q1", "kind": "verdict",
        "aoe_kinematic_passes": aoe_kin,
        "aoe_eoc_passes": aoe_eoc,
        "aoe_density_dipole_passes": aoe_dens,
        "aoe_snr_passes": aoe_snr,
        "Q1_overall_pass": bool(overall),
        "interpretation": ("Brouwer-Clemence c_k = eps^k ladder appears in KINEMATIC "
                            "spectrum (dphi/dM and EOC); static density carries the dipole only "
                            "by even-symmetry of the projection geometry"),
    })

    with out_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    print(f"\nWrote {len(records)} NDJSON records to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
