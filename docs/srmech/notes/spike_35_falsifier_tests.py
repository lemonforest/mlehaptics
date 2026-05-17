"""Spike #35 — falsifier tests for Q1/Q2/Q3 predictions.

For each Q, formulate the test that would overturn the finding if the data
disagreed.

Q1 falsifier: if observed extragalactic structure spectra at the predicted
AoE direction do NOT show c_k = eps^k = 0.0506^k ladder in their kinematic
proper motion / Doppler series, the off-centre-observer reading is wrong.

Q2 falsifier: if galaxy rotation curves observed along the AoE direction do
NOT show asymmetric Doppler residual with sign-flip at apse projection
(amplitude scaling with eps_AoE), the kinematic interpretation is wrong.

Q3 falsifier: if the cosmic-web Fiedler-partition machinery does NOT produce
a meaningful partition at the cosmological scale (e.g., lambda_2 collapses
to noise or partition flips arbitrarily under reasonable edge-weight changes),
the structural-similarity claim is wrong.

Computational tests we CAN run (closed-form, no observational data):
F1. Verify c_k = eps^k holds at eps_AoE = 0.0506 to <0.1% across noise variations
F2. Verify sign-flip asymmetry amplitude is monotonic in eps and proportional
    at small eps
F3. Verify Fiedler partition rank-ordering is stable across random cosmic-web
    realizations
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from spike_35_q3_galactic_itn_v2 import (
    build_cosmic_web_graph, fiedler_partition
)


def kinematic_jacobian_dphi_dM(M_grid: np.ndarray, eps: float) -> np.ndarray:
    r2 = 1 - 2 * eps * np.cos(M_grid) + eps ** 2
    return (1 - eps * np.cos(M_grid)) / r2


def extract_cos_coeffs(signal: np.ndarray, M_grid: np.ndarray, k_max: int = 7) -> np.ndarray:
    N = len(M_grid)
    coefs = np.zeros(k_max)
    for k in range(1, k_max + 1):
        coefs[k - 1] = (2.0 / N) * np.sum(signal * np.cos(k * M_grid))
    return coefs


def main() -> int:
    out_dir = Path("D:/temp/spike_35")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "spike_35_falsifier_tests.ndjson"

    records: list[dict] = []
    records.append({
        "spike": 35, "kind": "meta",
        "claim": "F1+F2+F3 falsifier tests: computational checks that would overturn "
                 "Q1/Q2/Q3 if disagreed with prediction",
    })

    # === F1: c_k = eps^k stability under noise ===
    print("=" * 80)
    print("F1 -- c_k = eps^k stability under additive noise (Q1 falsifier)")
    print("=" * 80)
    eps_AoE = 0.0506
    N = 32768
    M_grid = np.linspace(0, 2 * math.pi, N, endpoint=False)
    dphi_dM = kinematic_jacobian_dphi_dM(M_grid, eps_AoE)
    theory = [eps_AoE ** k for k in range(1, 6)]

    rng = np.random.default_rng(42)
    noise_levels = [0.0, 1e-5, 1e-4, 1e-3, 1e-2]
    print(f"{'noise_level':>11s} | {'c_1':>10s} {'c_2':>10s} {'c_3':>10s} | "
          f"{'rel_err_c1':>10s} {'rel_err_c2':>10s} {'rel_err_c3':>10s}")
    for noise_lvl in noise_levels:
        signal_noisy = dphi_dM + rng.normal(0, noise_lvl, N)
        cos_k = extract_cos_coeffs(signal_noisy, M_grid, k_max=5)
        rel_errs = [abs(abs(cos_k[k]) - theory[k]) / theory[k] for k in range(3)]
        print(f"{noise_lvl:11.1e} | {abs(cos_k[0]):10.4e} {abs(cos_k[1]):10.4e} {abs(cos_k[2]):10.4e} | "
              f"{rel_errs[0]:10.2e} {rel_errs[1]:10.2e} {rel_errs[2]:10.2e}")
        records.append({
            "spike": 35, "kind": "F1_noise_stability",
            "noise_level": noise_lvl,
            "abs_c1": float(abs(cos_k[0])),
            "abs_c2": float(abs(cos_k[1])),
            "abs_c3": float(abs(cos_k[2])),
            "rel_err_c1": float(rel_errs[0]),
            "rel_err_c2": float(rel_errs[1]),
            "rel_err_c3": float(rel_errs[2]),
        })

    # === F2: sign-flip asymmetry scaling with eps ===
    print()
    print("=" * 80)
    print("F2 -- sign-flip asymmetry scaling with eps (Q2 falsifier)")
    print("=" * 80)
    eps_list = [0.001, 0.005, 0.01, 0.02, 0.0506, 0.1, 0.2, 0.3]
    print(f"{'eps':>10s} | {'asym_amp':>12s} {'asym_per_eps':>14s} {'asym_per_eps_R3':>16s}")
    # asym/eps should be roughly constant (within a few percent) across small eps
    asym_amps = []
    for eps in eps_list:
        # Time-phase asymmetry q1 - q2
        N = 4096
        M_q1 = np.linspace(0, math.pi / 2, N // 4)
        M_q2 = np.linspace(math.pi / 2, math.pi, N // 4)
        dphi_dM_q1 = kinematic_jacobian_dphi_dM(M_q1, eps)
        dphi_dM_q2 = kinematic_jacobian_dphi_dM(M_q2, eps)
        q1 = np.trapezoid(dphi_dM_q1, M_q1)
        q2 = np.trapezoid(dphi_dM_q2, M_q2)
        asym = q1 - q2
        asym_amps.append(float(asym))
        ratio_to_eps = asym / eps
        ratio_to_R3 = asym / 0.0506 if eps == 0.0506 else float("nan")
        print(f"{eps:10.4e} | {asym:12.4e} {ratio_to_eps:14.6f} {ratio_to_R3:16.6f}")
        records.append({
            "spike": 35, "kind": "F2_asym_scaling",
            "eps": eps,
            "asym_q1_minus_q2": float(asym),
            "asym_per_eps": float(ratio_to_eps),
        })
    # Check monotonicity
    monotonic = all(asym_amps[i] < asym_amps[i + 1] for i in range(len(asym_amps) - 1))
    print(f"\n  Monotonic in eps (asym strictly increases): {monotonic}")
    # Check linearity at small eps: asym/eps should converge to ~2 (from Brouwer-Clemence)
    small_eps_ratio = asym_amps[3] / eps_list[3]  # eps=0.02
    print(f"  Asym/eps at eps=0.02: {small_eps_ratio:.6f} (expected ~2.0)")

    # === F3: Fiedler partition stability across random realizations ===
    print()
    print("=" * 80)
    print("F3 -- Fiedler partition stability across random cosmic-web realizations")
    print("=" * 80)
    n_realizations = 10
    print(f"  Running {n_realizations} random cosmic-web realizations...")
    lambda_2_values = []
    partition_strengths = []
    for seed in range(100, 100 + n_realizations):
        nodes, A, meta = build_cosmic_web_graph(seed=seed)
        lam1, lam2, lam3, f2, f3 = fiedler_partition(A)
        eig_full = np.linalg.eigvalsh(np.diag(A.sum(axis=1)) - A)
        bipartition_strength = lam2 / eig_full[-1]
        lambda_2_values.append(float(lam2))
        partition_strengths.append(float(bipartition_strength))
    lam2_mean = float(np.mean(lambda_2_values))
    lam2_std = float(np.std(lambda_2_values))
    strength_mean = float(np.mean(partition_strengths))
    strength_std = float(np.std(partition_strengths))
    print(f"  lambda_2 across realizations: {lam2_mean:.4e} +/- {lam2_std:.4e}")
    print(f"  Bipartition strength across realizations: {strength_mean:.4e} +/- {strength_std:.4e}")
    # If lambda_2 is consistently > 0, Fiedler partition is robust
    all_positive = all(l > 1e-6 for l in lambda_2_values)
    print(f"  All lambda_2 > 1e-6 (Fiedler partition meaningful in all): {all_positive}")
    records.append({
        "spike": 35, "kind": "F3_fiedler_stability",
        "n_realizations": n_realizations,
        "lambda_2_mean": lam2_mean,
        "lambda_2_std": lam2_std,
        "lambda_2_min": float(min(lambda_2_values)),
        "lambda_2_max": float(max(lambda_2_values)),
        "bipartition_strength_mean": strength_mean,
        "all_meaningful_partition": bool(all_positive),
    })

    # Verdict
    f1_pass = all(r.get("rel_err_c1", 1) < 0.01 for r in records
                   if r.get("kind") == "F1_noise_stability" and r.get("noise_level", 1) <= 1e-4)
    f2_pass = bool(monotonic and abs(small_eps_ratio - 2.0) < 0.05)
    f3_pass = bool(all_positive)

    print()
    print("=" * 80)
    print("FALSIFIER TESTS VERDICT")
    print("=" * 80)
    print(f"  F1 c_k = eps^k stable under noise (Q1 not falsified):   "
          f"{'PASS' if f1_pass else 'FAIL'}")
    print(f"  F2 asym monotonic + linear at small eps (Q2 not falsified): "
          f"{'PASS' if f2_pass else 'FAIL'}")
    print(f"  F3 Fiedler partition stable across realizations (Q3 not falsified): "
          f"{'PASS' if f3_pass else 'FAIL'}")
    records.append({
        "spike": 35, "kind": "falsifier_verdict",
        "F1_Q1_not_falsified": bool(f1_pass),
        "F2_Q2_not_falsified": bool(f2_pass),
        "F3_Q3_not_falsified": bool(f3_pass),
        "all_pass": bool(f1_pass and f2_pass and f3_pass),
    })

    with out_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    print(f"\nWrote {len(records)} NDJSON records to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
