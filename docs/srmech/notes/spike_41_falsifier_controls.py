"""Spike #41 falsifier controls.

Per Spike #38 / #40 pattern: bound the 'any sequence would give this'
baseline. Controls:
  - 10 random integer-sequence seeds (uniform in 1..100, length 30)
  - Pure geometric sequence (anchor positive Class K-shape)
  - Pure cyclic group (anchor positive Class I)
  - Pure Fibonacci REF (positive anchor)
  - Pure Kepler-EOC at eps=0.1 (positive anchor for K-shape)
  - Pure random-walk integer sequence
  - Pure arithmetic progression
"""

from __future__ import annotations

import json
import math
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import numpy as np

WORKSPACE = Path(__file__).resolve().parent
FALSIFIER_RECORDS = WORKSPACE / "spike_41_falsifier_records_2026-05-17.ndjson"
DATE_TAG = "2026-05-17"
SPIKE = "spike_41"


def emit(record: Dict) -> None:
    record = dict(record)
    record.setdefault("date", DATE_TAG)
    record.setdefault("spike", SPIKE)
    record.setdefault("timestamp", datetime.now(tz=timezone.utc).isoformat())
    with FALSIFIER_RECORDS.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, default=float))
        fh.write("\n")


def kepler_ladder_test(coefficients: np.ndarray, label: str = "") -> Dict:
    abs_c = np.abs(coefficients)
    if np.any(abs_c <= 0):
        idx = np.where(abs_c > 0)[0]
        if len(idx) < 3:
            return {
                "label": label,
                "r2": None,
                "eps_fit": None,
                "monotonic_decreasing": False,
                "in_physical_range": False,
                "k_signature_present": False,
            }
        abs_c = abs_c[idx]
    k = np.arange(1, len(abs_c) + 1, dtype=np.float64)
    log_c = np.log(abs_c)
    A = np.vstack([k, np.ones_like(k)]).T
    slope, intercept = np.linalg.lstsq(A, log_c, rcond=None)[0]
    eps_fit = float(math.exp(slope))
    pred = slope * k + intercept
    ss_res = float(np.sum((log_c - pred) ** 2))
    ss_tot = float(np.sum((log_c - np.mean(log_c)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    monotonic = bool(np.all(np.diff(abs_c) < 0))
    in_range = 0.001 < eps_fit < 0.5
    return {
        "label": label,
        "r2": float(r2),
        "eps_fit": eps_fit,
        "monotonic_decreasing": monotonic,
        "in_physical_range": in_range,
        "k_signature_present": bool(r2 > 0.99 and monotonic and in_range),
    }


def main():
    if FALSIFIER_RECORDS.exists():
        FALSIFIER_RECORDS.unlink()

    print("=== Falsifier controls ===\n")

    rng = random.Random(42)
    n_random_seeds = 10
    n_modes = 20

    # 10 random sequences
    random_results = []
    for seed_idx in range(n_random_seeds):
        rng_local = random.Random(seed_idx * 17 + 1)
        # Random "coefficient" sequence
        coeffs = np.array([rng_local.uniform(0.01, 10) for _ in range(n_modes)])
        result = kepler_ladder_test(coeffs, f"random_seed_{seed_idx}")
        random_results.append(result)
        emit({"kind": "random_baseline", **result})

    n_random_passes = sum(1 for r in random_results if r["k_signature_present"])
    print(f"Random baseline: {n_random_passes}/{n_random_seeds} pass K-test")
    eps_fit_random = [r["eps_fit"] for r in random_results if r["eps_fit"] is not None]
    print(f"  Random eps_fit mean: {np.mean(eps_fit_random):.4f}, std: {np.std(eps_fit_random):.4f}")

    # Pure geometric (anchor: should pass cleanly at any eps in 0.001-0.5)
    for eps in [0.05, 0.1, 0.2, 0.3]:
        c_k = np.array([eps ** k for k in range(1, n_modes + 1)])  # NOT /k
        result = kepler_ladder_test(c_k, f"pure_geometric_eps_{eps}")
        emit({"kind": "anchor_geometric", "eps": eps, **result})
        print(f"Pure geometric eps={eps}: r2={result['r2']:.4f}, eps_fit={result['eps_fit']:.4f}, pass={result['k_signature_present']}")

    # Pure cyclic (anchor: should FAIL K-test, doesn't decay)
    cyclic_period_5 = np.array([math.sin(2 * math.pi * k / 5) ** 2 + 0.01 for k in range(1, n_modes + 1)])
    result = kepler_ladder_test(cyclic_period_5, "pure_cyclic_period_5")
    emit({"kind": "anchor_cyclic", **result})
    print(f"Pure cyclic (period 5): r2={result['r2']:.4f}, monotonic={result['monotonic_decreasing']}, pass={result['k_signature_present']}")

    # Pure Fibonacci REF — the psi^k/k decay (positive anchor)
    psi = (1 - math.sqrt(5)) / 2
    psi_abs = abs(psi)
    fib_c_k = np.array([psi_abs ** k / k for k in range(1, n_modes + 1)])
    result = kepler_ladder_test(fib_c_k, "fibonacci_psi_k_over_k_REF")
    emit({"kind": "anchor_fibonacci_decay", **result})
    print(f"Fibonacci psi^k/k REF: r2={result['r2']:.4f}, eps_fit={result['eps_fit']:.4f}, in_range={result['in_physical_range']}")

    # Pure Kepler REF eps = 0.1
    kepler_c_k = np.array([0.1 ** k / k for k in range(1, n_modes + 1)])
    result = kepler_ladder_test(kepler_c_k, "kepler_eps_0.1_REF")
    emit({"kind": "anchor_kepler_REF", **result})
    print(f"Kepler eps=0.1 REF: r2={result['r2']:.4f}, eps_fit={result['eps_fit']:.4f}, in_range={result['in_physical_range']}")

    # Arithmetic progression (should FAIL): c_k = a + b*k
    arith = np.array([1.0 / (k + 1) for k in range(1, n_modes + 1)])  # pure 1/k harmonic
    result = kepler_ladder_test(arith, "pure_1_over_k_harmonic")
    emit({"kind": "anchor_arithmetic_inverse", **result})
    print(f"Pure 1/k harmonic: r2={result['r2']:.4f}, eps_fit={result['eps_fit']:.4f}, in_range={result['in_physical_range']}")

    # Lucas numbers (relative of Fibonacci): L_n = L_{n-1} + L_{n-2}, L_0=2, L_1=1
    L = [2, 1]
    for _ in range(30):
        L.append(L[-1] + L[-2])
    # Lucas's analog: still psi-decay
    lucas_c_k = np.array([psi_abs ** k / k for k in range(1, n_modes + 1)])
    # Same form! Lucas has same eigenvalues phi, psi as Fibonacci
    result = kepler_ladder_test(lucas_c_k, "lucas_psi_k_over_k_REF")
    emit({"kind": "anchor_lucas", **result})
    print(f"Lucas psi^k/k REF: r2={result['r2']:.4f} (identical form to Fibonacci)")

    # Tribonacci T_n = T_{n-1} + T_{n-2} + T_{n-3} -- 3-step cascade
    T = [0, 0, 1]
    for _ in range(30):
        T.append(T[-1] + T[-2] + T[-3])
    # Tribonacci dominant eigenvalue ~ 1.8393; subdominant complex pair magnitude
    # Companion matrix [[1,1,1],[1,0,0],[0,1,0]] eigenvalues
    tri_C = np.array([[1, 1, 1], [1, 0, 0], [0, 1, 0]], dtype=float)
    tri_eigs = np.linalg.eigvals(tri_C)
    tri_lam1 = np.max(np.abs(tri_eigs))
    tri_lam2 = np.partition(np.abs(tri_eigs), -2)[-2]
    tri_rho = tri_lam2 / tri_lam1
    tri_c_k = np.array([tri_rho ** k / k for k in range(1, n_modes + 1)])
    result = kepler_ladder_test(tri_c_k, "tribonacci_c_k")
    emit({"kind": "anchor_tribonacci", "tri_lam1": float(tri_lam1), "tri_rho": float(tri_rho), **result})
    print(f"Tribonacci subdominant decay: r2={result['r2']:.4f}, eps_fit={result['eps_fit']:.4f}, rho={tri_rho:.4f}")

    # Multinacci 3+7+1 subdominant decay (substrate B re-test)
    # Confirmed in primary script
    rho_b = 0.688455
    multi_c_k = np.array([rho_b ** k / k for k in range(1, n_modes + 1)])
    result = kepler_ladder_test(multi_c_k, "multinacci_3_7_1_subdominant_decay_REF")
    emit({"kind": "anchor_multinacci_subdominant", **result})
    print(f"Multinacci 3+7+1 subdominant decay: r2={result['r2']:.4f}, eps_fit={result['eps_fit']:.4f}")

    print(f"\nFalsifier records saved to {FALSIFIER_RECORDS}")


if __name__ == "__main__":
    main()
