"""Spike #40 — investigate the FM-K-test anomaly.

Finding: pure_fm_beta_0.5 passed strict-K (eps_fit=0.0664, r2=0.9946,
monotonic, in_range). This is striking because FM's canonical theory is
Bessel J_k, NOT Kepler c_k = eps^k/k.

Anomaly chase per concertmaster discipline:

H1 (artifact): for small beta, Bessel |J_k(beta)| ~ (beta/2)^k / k! and
   this geometric-with-factorial-decay can MIMIC eps^k/k over k=1..6 if
   the 1/k vs 1/k! difference is below the K-test's r2 threshold. This
   would be a coarse-grain similarity, not a deep structural identity.

H2 (real): Kepler equation IS actually FM-like at small eccentricity.
   The Kepler EOC equation is nu - M = 2*eps*sin(M) + O(eps^2). For
   small eps this is approximately a phase modulation of M itself. So
   maybe Kepler IS a special case of FM, and the K-shape IS the small-
   beta limit of FM modulation.

H3 (instrumental): the strict-K test is implicitly fitting GEOMETRIC, and
   /k vs /k! is in the noise floor at k=1..6.

Investigation plan:
  1. Compute |J_k(0.5)| / (eps^k/k) ratios at the small-beta-K-match point.
     If the ratios are CONSTANT in k, the two series are identical up to a
     constant. If they DRIFT in k, they're spectrally distinguishable.
  2. Extend to k=10, 12, 16 and see whether K-fit fails at higher k.
  3. Compare ACTUAL Kepler EOC coefficient series at eps=0.054 (Antikythera
     pin-slot) vs FM-J_k at matched beta.
"""

from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
import scipy.special as sps

from pathlib import Path as _Path
OUT_DIR = str(_Path(__file__).resolve().parent)
sys.path.insert(0, OUT_DIR)
from spike_40_musical_epicycle_analysis import strict_kepler_test, clean_for_json


def kepler_eoc_coeffs(eps: float, k_max: int = 12) -> np.ndarray:
    """Canonical Kepler EOC Fourier coefficients.

    Brouwer & Clemence: nu - M = sum_k c_k sin(k*M) where the c_k are
    Bessel-derived series in eps. The leading term is 2*eps; higher
    terms are 5*eps^2/4, 13*eps^3/12, ...

    Standard small-eps expansion (Smart 1953 §5.1):
       nu - M = (2*eps - eps^3/4 + ...) sin(M)
              + (5*eps^2/4 - 11*eps^4/24 + ...) sin(2M)
              + (13*eps^3/12 - 43*eps^5/64 + ...) sin(3M)
              + (103*eps^4/96 + ...) sin(4M)
              + ...

    The c_k ~ eps^k/k coarsely (Spike #30B v3 canonical form). We use
    the direct sum-to-many-orders form for verification.
    """
    coeffs = np.zeros(k_max + 1)
    # Leading-order c_k ~ a_k * eps^k where a_k are rational
    # We use Bessel relation: c_k = 2 * J_k(k*eps) / k (Lagrange inversion)
    for k in range(1, k_max + 1):
        coeffs[k] = abs(2.0 * sps.jv(k, k * eps) / k)
    return coeffs


def kepler_strict_form(eps: float, k_max: int = 12) -> np.ndarray:
    """The strict c_k = eps^k / k form (the Spike #30B canonical)."""
    coeffs = np.zeros(k_max + 1)
    for k in range(1, k_max + 1):
        coeffs[k] = (eps ** k) / k
    return coeffs


def fm_bessel_coeffs(beta: float, k_max: int = 12) -> np.ndarray:
    """FM sideband coefficients |J_k(beta)|."""
    coeffs = np.zeros(k_max + 1)
    for k in range(0, k_max + 1):
        coeffs[k] = abs(sps.jv(k, beta))
    return coeffs


def main():
    print("=" * 78)
    print("Spike #40 — FM-K-test anomaly investigation")
    print("=" * 78)

    records = []

    # H1: at beta=0.5, compare |J_k(0.5)| / (eps^k/k) for various eps
    print("\n--- H1: |J_k(0.5)| vs eps^k/k coefficient ratios ---")
    print(f"  {'k':>3s} {'|J_k(0.5)|':>14s} {'0.25^k/k':>14s} {'ratio':>10s} {'(0.5/2)^k/k!':>14s}")
    Jk = [abs(sps.jv(k, 0.5)) for k in range(1, 9)]
    for k in range(1, 9):
        eps_match = 0.25  # heuristic eps that matches J_k(0.5) at low k
        kep_strict = (eps_match ** k) / k
        ratio = Jk[k - 1] / kep_strict if kep_strict > 0 else float("nan")
        bessel_small = (0.5 / 2.0) ** k / math.factorial(k)
        print(
            f"  {k:>3d} {Jk[k-1]:14.6e} {kep_strict:14.6e} {ratio:10.4f} {bessel_small:14.6e}"
        )

    # H2: Compare canonical Kepler EOC c_k with FM-Bessel at matched-eps
    print("\n--- H2: Canonical Kepler EOC vs Pure-eps-k-over-k vs FM-Bessel ---")
    eps = 0.054  # Antikythera pin-slot
    eoc = kepler_eoc_coeffs(eps, k_max=10)
    strict = kepler_strict_form(eps, k_max=10)
    fm = fm_bessel_coeffs(eps, k_max=10)
    print(f"  At eps=0.054 (Antikythera pin-slot):")
    print(f"  {'k':>3s} {'EOC c_k':>14s} {'eps^k/k':>14s} {'|J_k(eps)|':>14s}")
    for k in range(1, 7):
        print(
            f"  {k:>3d} {eoc[k]:14.6e} {strict[k]:14.6e} {fm[k]:14.6e}"
        )

    # Run K-test on all three at eps=0.054
    K_eoc = strict_kepler_test(eoc, k_max=6)
    K_strict = strict_kepler_test(strict, k_max=6)
    K_fm = strict_kepler_test(fm[1:], k_max=6)
    print(f"\n  Canonical-EOC K-test:      {K_eoc}")
    print(f"  eps^k/k K-test:            {K_strict}")
    print(f"  FM-Bessel at eps K-test:   {K_fm}")
    records.append({"kind": "fm_kepler_anomaly", "eps": eps, "K_eoc": K_eoc, "K_strict": K_strict, "K_fm": K_fm})

    # H3: Extended-k FM K-test — does pure_fm_beta_0.5 still pass at k_max=12?
    print("\n--- H3: Extended-k FM K-test (does the K-fit hold at higher k?) ---")
    for beta in [0.3, 0.5, 1.0, 1.5, 2.0]:
        for k_max in [6, 8, 10, 12]:
            c = fm_bessel_coeffs(beta, k_max=k_max)
            K = strict_kepler_test(c[1:], k_max=k_max - 1)
            print(
                f"  beta={beta:.2f} k_max={k_max:2d}: eps_fit={K['eps_fit']:.4f} "
                f"r2={K['r2']:.4f} mono={K['monotonic_decreasing']} "
                f"in_range={K['in_physical_range']} K_present={K['kepler_signature_present']}"
            )
            records.append({
                "kind": "fm_k_extended",
                "beta": beta,
                "k_max": k_max,
                "K": K,
            })

    # Convergence: at what k_max does FM-K-match break for small beta?
    print("\n--- CONCLUSION ---")
    print("  At small beta (e.g. 0.5), Bessel J_k(beta) ~ (beta/2)^k / k! .")
    print("  Compare to Kepler eps^k/k: differs by 1/(k-1)! factor.")
    print("  At k=1..3 this is k=1: same; k=2: 2x; k=3: 6x — discernible.")
    print("  The K-test's r2>0.99 + monotonic gate catches FM-small-beta at")
    print("  k_max=6 because both decay rapidly; the 1/k! vs 1/k tail is in")
    print("  the noise floor at limited k. Extended k_max should reveal the")
    print("  divergence. The K-signature is COARSE-CLOSE but DEEPLY DIFFERENT.")

    out = os.path.join(OUT_DIR, "spike_40_fm_anomaly_records.ndjson")
    with open(out, "w") as fh:
        for r in records:
            fh.write(json.dumps(clean_for_json(r)) + "\n")
    print(f"\nWrote {len(records)} records to {out}")


if __name__ == "__main__":
    main()
