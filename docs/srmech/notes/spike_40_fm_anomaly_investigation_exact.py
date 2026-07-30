"""Spike #40 EXACT PORT of ``spike_40_fm_anomaly_investigation.py`` (2026-07-30).

The Kepler-EOC vs FM-small-beta overlap chase, run in exact rationals.

The anomaly: ``pure_fm_beta_0.5`` passes the strict K-test even though FM's
canonical theory is Bessel ``J_k``, not Kepler ``c_k = eps^k / k``.

  H1 (artifact)     small-beta ``|J_k(beta)| ~ (beta/2)^k / k!`` can MIMIC
                    ``eps^k / k`` over k = 1..6
  H2 (real)         Kepler EOC IS phase modulation at small eccentricity
  H3 (instrumental) the strict-K test fits GEOMETRIC and the ``1/k`` vs
                    ``1/k!`` tail is below its r2 gate at k <= 6

Everything is exact: the Bessel values are GAP-1 rational series, the
eccentricity ``eps = 0.054`` is read as the rational ``27/500`` it denotes,
and ``eps^k / k`` uses the exact Class-N integer power rather than
``exp(k log eps)``.

Original imports removed: ``numpy``, ``scipy.special``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path as _Path
from typing import List

OUT_DIR = str(_Path(__file__).resolve().parent)
sys.path.insert(0, OUT_DIR)

from spike_40_exact_primitives import (  # noqa: E402
    ONE, ZERO, Q,
    bessel_j, mag, provenance_records, qfrom_decimal, qpow_q,
    strict_kepler_test, write_ndjson,
)

_FACT = [1]


def _fact(n: int) -> int:
    while len(_FACT) <= n:
        _FACT.append(_FACT[-1] * len(_FACT))
    return _FACT[n]


def kepler_eoc_coeffs(eps: Q, k_max: int = 12) -> List[Q]:
    """Canonical Kepler EOC Fourier coefficients ``c_k = |2 J_k(k eps) / k|``.

    Lagrange-inversion / Bessel form (Brouwer & Clemence; Smart 1953 §5.1).
    Exact: ``k*eps`` is rational, so ``J_k(k eps)`` is a rational series.
    """
    out = [ZERO] * (k_max + 1)
    for k in range(1, k_max + 1):
        out[k] = mag(Q(2, 1) * bessel_j(k, Q(k, 1) * eps) / Q(k, 1))
    return out


def kepler_strict_form(eps: Q, k_max: int = 12) -> List[Q]:
    """The strict ``c_k = eps^k / k`` form (Spike #30B canonical), exact."""
    out = [ZERO] * (k_max + 1)
    for k in range(1, k_max + 1):
        out[k] = qpow_q(eps, Q(k, 1)) / Q(k, 1)
    return out


def fm_bessel_coeffs(beta: Q, k_max: int = 12) -> List[Q]:
    return [mag(bessel_j(k, beta)) for k in range(0, k_max + 1)]


def main() -> None:
    print("=" * 78)
    print("Spike #40 EXACT PORT - FM-K-test anomaly investigation")
    print("=" * 78)
    records: List[dict] = provenance_records(
        "spike_40_fm_anomaly_investigation_exact.py")

    # --- H1: |J_k(1/2)| vs (1/4)^k / k -------------------------------------
    print("\n--- H1: |J_k(1/2)| vs eps^k/k coefficient ratios ---")
    print(f"  {'k':>3s} {'|J_k(1/2)|':>16s} {'(1/4)^k/k':>16s} {'ratio':>12s} "
          f"{'(1/4)^k/k!':>16s}")
    h1_rows = []
    eps_match = Q(1, 4)
    for k in range(1, 9):
        jk = mag(bessel_j(k, Q(1, 2)))
        kep = qpow_q(eps_match, Q(k, 1)) / Q(k, 1)
        ratio = jk / kep
        small = qpow_q(Q(1, 4), Q(k, 1)) / Q(_fact(k), 1)
        print(f"  {k:>3d} {jk.as_float():16.6e} {kep.as_float():16.6e} "
              f"{ratio.as_float():12.4f} {small.as_float():16.6e}")
        h1_rows.append({
            "k": k,
            "abs_J_k_half": jk.as_float(),
            "eps_match_pow_k_over_k": kep.as_float(),
            "ratio": ratio.as_float(),
            "small_beta_asymptote": small.as_float(),
        })
    records.append({
        "kind": "fm_h1_ratio_drift",
        "eps_match": eps_match.as_float(),
        "rows": h1_rows,
        "finding": (
            "The ratio DRIFTS in k (it is not constant), so |J_k(beta)| and "
            "eps^k/k are spectrally distinguishable in principle — H1 'pure "
            "artifact' is not supported as an identity, only as a "
            "coarse-resolution coincidence."
        ),
    })

    # --- H2: canonical Kepler EOC vs eps^k/k vs FM-Bessel at eps ------------
    print("\n--- H2: Canonical Kepler EOC vs eps^k/k vs FM-Bessel ---")
    eps = qfrom_decimal("0.054")            # Antikythera pin-slot = 27/500
    eoc = kepler_eoc_coeffs(eps, k_max=10)
    strict = kepler_strict_form(eps, k_max=10)
    fm = fm_bessel_coeffs(eps, k_max=10)
    print(f"  At eps = {eps.numerator}/{eps.denominator} (Antikythera pin-slot):")
    print(f"  {'k':>3s} {'EOC c_k':>16s} {'eps^k/k':>16s} {'|J_k(eps)|':>16s}")
    for k in range(1, 7):
        print(f"  {k:>3d} {eoc[k].as_float():16.6e} {strict[k].as_float():16.6e} "
              f"{fm[k].as_float():16.6e}")
    k_eoc = strict_kepler_test(eoc, k_max=6)
    k_strict = strict_kepler_test(strict, k_max=6)
    k_fm = strict_kepler_test(fm[1:], k_max=6)
    records.append({
        "kind": "fm_kepler_anomaly",
        "eps": eps.as_float(),
        "eps_exact": f"{eps.numerator}/{eps.denominator}",
        "eps_note": "0.054 read as the rational 27/500 it DENOTES, not as the "
                    "nearest double (which differs at the 1e-18 level).",
        "K_eoc": k_eoc,
        "K_strict": k_strict,
        "K_fm": k_fm,
    })
    print(f"\n  Canonical-EOC   K_present={k_eoc['kepler_signature_present']} "
          f"eps_fit={k_eoc['eps_fit']:.6f} r2={k_eoc['r2']:.6f}")
    print(f"  eps^k/k         K_present={k_strict['kepler_signature_present']} "
          f"eps_fit={k_strict['eps_fit']:.6f} r2={k_strict['r2']:.6f}")
    print(f"  FM-Bessel@eps   K_present={k_fm['kepler_signature_present']} "
          f"eps_fit={k_fm['eps_fit']:.6f} r2={k_fm['r2']:.6f}")

    # --- H3: extended-k FM K-test ------------------------------------------
    print("\n--- H3: Extended-k FM K-test ---")
    for beta_s in ["0.3", "0.5", "1.0", "1.5", "2.0"]:
        beta = qfrom_decimal(beta_s)
        for k_max in [6, 8, 10, 12]:
            c = fm_bessel_coeffs(beta, k_max=k_max)
            K = strict_kepler_test(c[1:], k_max=k_max - 1)
            print(f"  beta={float(beta_s):.2f} k_max={k_max:2d}: "
                  f"eps_fit={K['eps_fit']:.4f} r2={K['r2']:.4f} "
                  f"mono={K['monotonic_decreasing']} "
                  f"in_range={K['in_physical_range']} "
                  f"K_present={K['kepler_signature_present']}")
            records.append({
                "kind": "fm_k_extended",
                "beta": float(beta_s),
                "beta_exact": f"{beta.numerator}/{beta.denominator}",
                "k_max": k_max,
                "K": K,
            })

    print("\n--- CONCLUSION ---")
    print("  At small beta, J_k(beta) ~ (beta/2)^k / k!; Kepler is eps^k / k.")
    print("  They differ by a 1/(k-1)! factor, which the strict-K r2 gate")
    print("  cannot see at k_max=6 but which the exact ratio table above shows")
    print("  DRIFTING in k. Coarse-close, deeply different.")

    out = os.path.join(OUT_DIR, "spike_40_fm_anomaly_records_exact.ndjson")
    write_ndjson(out, records)
    print(f"\nWrote {len(records)} records to {out}")


if __name__ == "__main__":
    main()
