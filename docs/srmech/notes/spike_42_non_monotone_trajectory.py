"""Spike #42 — non-monotone f_RD trajectory connection to imprinting cascade.

Per MFO Sec.VII.6.1.2 (DESI 2024 thawing-CPL w0=-0.8, wa=-0.7):
  f_RD(NOW) ~ 0.949 (Planck 2018)
  f_RD PEAKS at ~0.978 at a~2.14 (~16 Gyr from now)
  f_RD asymptote (a->inf, thawing-CPL) ~ 0.843

The trajectory is NON-MONOTONE: rises past max-engagement, then descends
toward the lower thawing-CPL asymptote.

Question: how does the imprinting cascade rate change sign through this
trajectory?

Setup:
  - f_RD = Omega_dark / Omega_total = (Omega_c * a^-3 + Omega_DE(a)) / T(a)
  - Under DESI thawing-CPL: w(a) = w0 + wa * (1 - a)
  - Omega_DE(a) = Omega_Lambda * a^(-3*(1+w0+wa)) * exp(3*wa*(a-1))

The "imprinting cascade rate" we're measuring per Spike #42 is:
  df_RD/dt = (cascade-deposit rate)

When df_RD/dt > 0 (rising): un-creation dominates (visible -> dark)
When df_RD/dt = 0 (peak):   instantaneous balance
When df_RD/dt < 0 (falling): creation > un-creation (dark -> visible)

Per Spike #41 sharpening: epsilon (rate-parameter on K-axis) is signed by
the direction of cascade flow. df_RD/dt sign IS the direction of flow.

Per [[user_stance_dark_sector_ring_down_rate_is_cascade_stretched]]:
The cascade has signature K(t)/N = 1 - f_RD(t) ~ t^(-d_S/2) * H(log_lambda t).
The substrate-Laplacian d_S parameterizes the ASYMPTOTIC-DOF axis.
Under thawing-CPL, the cascade is non-monotone -- the rate-parameter
epsilon doesn't just decay; it has a SIGN that flips.

THIS IS THE DEEPEST FINDING OF SPIKE #42.
"""

from __future__ import annotations

import math
import json
from pathlib import Path
from typing import List, Tuple

OUT_DIR = Path(__file__).resolve().parent

# Cosmological parameters (Planck 2018; Aghanim et al. 2020 A&A 641 A6)
H0_KM_S_MPC = 67.4
OMEGA_R = 9.18e-5
OMEGA_B = 0.0493
OMEGA_C = 0.265
OMEGA_LAMBDA = 0.6889
OMEGA_DARK = OMEGA_C + OMEGA_LAMBDA  # 0.954
# Visible matter:
OMEGA_VISIBLE = OMEGA_B + OMEGA_R  # 0.0493 + tiny radiation

# DESI 2024 VI / DR2 thawing-CPL central values
W0_THAWING = -0.8
WA_THAWING = -0.7

# LCDM baseline
W0_LCDM = -1.0
WA_LCDM = 0.0


def E_squared(a: float, w0: float, wa: float) -> float:
    """E^2 = T(a) = H(a)^2 / H_0^2 under CPL parameterization w(a) = w0 + wa(1-a).

    Omega_DE(a) = Omega_Lambda * a^(-3(1+w0+wa)) * exp(3*wa*(a-1))
    """
    if a <= 0:
        return float("inf")
    omega_de = OMEGA_LAMBDA * (a ** (-3.0 * (1.0 + w0 + wa))) * math.exp(3.0 * wa * (a - 1.0))
    return OMEGA_R * a**-4.0 + (OMEGA_B + OMEGA_C) * a**-3.0 + omega_de


def f_RD(a: float, w0: float, wa: float) -> float:
    """Ring-down completion fraction = Omega_dark(a) / Omega_total(a)."""
    omega_de_a = OMEGA_LAMBDA * (a ** (-3.0 * (1.0 + w0 + wa))) * math.exp(3.0 * wa * (a - 1.0))
    omega_c_a = OMEGA_C * a**-3.0
    omega_b_a = OMEGA_B * a**-3.0
    omega_r_a = OMEGA_R * a**-4.0
    total = omega_r_a + omega_b_a + omega_c_a + omega_de_a
    dark = omega_c_a + omega_de_a
    return dark / total


def df_RD_da(a: float, w0: float, wa: float, ha: float = 1e-6) -> float:
    """Numerical derivative df_RD/da using central differences."""
    return (f_RD(a + ha, w0, wa) - f_RD(a - ha, w0, wa)) / (2 * ha)


def dt_da_Gyr(a: float, w0: float, wa: float) -> float:
    """Convert da -> dt (cosmic time) in Gyr.

    da/dt = H(a) * a -> dt/da = 1 / (H(a) * a) = 1 / (H_0 * sqrt(E^2(a)) * a)
    Convert: H_0 = 67.4 km/s/Mpc -> 1/H_0 = 14.51 Gyr (Hubble time)
    """
    HUBBLE_TIME_GYR = 14.51  # 1/H_0 with H_0 = 67.4 km/s/Mpc
    E = math.sqrt(E_squared(a, w0, wa))
    return HUBBLE_TIME_GYR / (E * a)


def cosmic_time_Gyr(a_start: float, a_end: float, w0: float, wa: float, n_steps: int = 1000) -> float:
    """Integrate dt/da from a_start to a_end (trapezoidal)."""
    if a_end <= a_start:
        return 0.0
    da = (a_end - a_start) / n_steps
    total = 0.0
    a_prev = a_start
    dt_prev = dt_da_Gyr(a_prev, w0, wa)
    for i in range(1, n_steps + 1):
        a_curr = a_start + i * da
        dt_curr = dt_da_Gyr(a_curr, w0, wa)
        total += 0.5 * (dt_prev + dt_curr) * da
        dt_prev = dt_curr
    return total


def find_peak_a(w0: float, wa: float, a_low: float = 1.0, a_high: float = 10.0) -> Tuple[float, float]:
    """Bisect to find a* where df_RD/da = 0 (peak of f_RD trajectory)."""
    # Brute-force grid scan first
    a_grid = [a_low + (a_high - a_low) * i / 1000 for i in range(1001)]
    derivs = [df_RD_da(a, w0, wa) for a in a_grid]
    # Find sign change
    for i in range(len(derivs) - 1):
        if derivs[i] > 0 and derivs[i + 1] < 0:
            # Sign change -- peak between a_grid[i] and a_grid[i+1]
            a_peak = (a_grid[i] + a_grid[i + 1]) / 2
            return a_peak, f_RD(a_peak, w0, wa)
    # No sign change -> monotonic
    return float("nan"), float("nan")


def main():
    print("=== Spike #42 -- Non-monotone f_RD trajectory analysis ===\n")
    print(f"Cosmological parameters:")
    print(f"  H_0 = {H0_KM_S_MPC} km/s/Mpc")
    print(f"  Omega_r = {OMEGA_R:.4e}")
    print(f"  Omega_b = {OMEGA_B}")
    print(f"  Omega_c = {OMEGA_C}")
    print(f"  Omega_Lambda = {OMEGA_LAMBDA}")
    print(f"  Omega_dark = Omega_c + Omega_Lambda = {OMEGA_DARK}")
    print(f"  Omega_visible = Omega_b + Omega_r = {OMEGA_VISIBLE:.4f}")
    print()
    print(f"DESI thawing-CPL: w0 = {W0_THAWING}, wa = {WA_THAWING}")
    print(f"LCDM:             w0 = {W0_LCDM}, wa = {WA_LCDM}")
    print()

    # f_RD(NOW) = f_RD(a=1) under both
    print(f"f_RD(NOW; a=1):")
    print(f"  LCDM:     f_RD = {f_RD(1.0, W0_LCDM, WA_LCDM):.4f}")
    print(f"  thawing:  f_RD = {f_RD(1.0, W0_THAWING, WA_THAWING):.4f}")
    print()

    # f_RD at various scale factors
    print("f_RD trajectory (thawing-CPL):")
    a_vals = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 5.0, 10.0, 100.0, 1000.0]
    for a in a_vals:
        f_thawing = f_RD(a, W0_THAWING, WA_THAWING)
        f_lcdm = f_RD(a, W0_LCDM, WA_LCDM)
        deriv_thawing = df_RD_da(a, W0_THAWING, WA_THAWING)
        sign_str = "+" if deriv_thawing > 0 else ("-" if deriv_thawing < 0 else "0")
        print(f"  a={a:>8.2f}: f_RD(thawing)={f_thawing:.4f}, f_RD(LCDM)={f_lcdm:.4f}, df/da sign: {sign_str}")
    print()

    # Find peak in thawing-CPL
    a_peak, f_peak = find_peak_a(W0_THAWING, WA_THAWING, 0.5, 10.0)
    print(f"Peak of f_RD under thawing-CPL:")
    print(f"  a_peak = {a_peak:.4f}")
    print(f"  f_peak = {f_peak:.4f}")
    if not math.isnan(a_peak):
        t_peak_gyr = cosmic_time_Gyr(1.0, a_peak, W0_THAWING, WA_THAWING)
        print(f"  cosmic time from NOW to peak: {t_peak_gyr:.2f} Gyr")
    print()

    # Asymptote (a -> very large)
    a_asymptote = 10000.0
    f_asymptote = f_RD(a_asymptote, W0_THAWING, WA_THAWING)
    print(f"Far-future asymptote (a={a_asymptote}):")
    print(f"  f_RD(thawing, a->inf) = {f_asymptote:.4f}")
    print()

    # Connect to imprinting cascade rate
    print("=== Imprinting cascade rate analysis ===\n")
    print("df_RD/dt is the IMPRINTING CASCADE RATE (cascade-deposit per unit cosmic time).")
    print()
    print("Sign of df_RD/dt tracks the direction of cascade flow:")
    print("  df_RD/dt > 0: UN-CREATION dominates (visible -> dark; ring-down accumulating)")
    print("  df_RD/dt = 0: instantaneous BALANCE (peak)")
    print("  df_RD/dt < 0: CREATION > un-creation (dark -> visible; cascade un-winding)")
    print()
    a_samples = [1.0, 1.5, 2.0, 2.14, 2.5, 3.0, 5.0, 10.0]
    print(f"{'a':>10} {'f_RD':>10} {'df/dt (1/Gyr)':>16} {'phase':>20}")
    for a in a_samples:
        f = f_RD(a, W0_THAWING, WA_THAWING)
        df_da = df_RD_da(a, W0_THAWING, WA_THAWING)
        # df/dt = df/da * da/dt = df/da / (dt/da)
        df_dt = df_da / dt_da_Gyr(a, W0_THAWING, WA_THAWING)
        if df_dt > 1e-6:
            phase = "UN-CREATION (rising)"
        elif df_dt < -1e-6:
            phase = "CREATION (falling)"
        else:
            phase = "BALANCE (peak)"
        print(f"{a:>10.2f} {f:>10.4f} {df_dt:>16.6f}  {phase:>20}")

    print()
    print("Key finding: the imprinting cascade rate CHANGES SIGN at the peak.")
    print(f"  Before peak (a < {a_peak:.3f}): rate is POSITIVE; cascade IMPRINTS into dark sector")
    print(f"  At peak (a = {a_peak:.3f}):    rate is ZERO; instantaneous balance")
    print(f"  After peak (a > {a_peak:.3f}): rate is NEGATIVE; cascade DE-IMPRINTS from dark sector")
    print()
    print("This is THE LOAD-BEARING finding for Spike #42 vocabulary reposture:")
    print("The cascade is BIDIRECTIONAL. 'Imprint' captures only one direction.")
    print("'Un-imprint' / 'de-cascade' / 'return-flow' captures the other.")
    print()

    # Connect to Cauchy-form rate-parameter
    print("=== Connection to Spike #41 epsilon rate-parameter ===\n")
    print("Per Spike #41: epsilon is the rate-parameter on Class K asymptotic-DOF axis.")
    print("Per Spike #42 finding: pi0 has epsilon = alpha/pi positive constant.")
    print("Per Spike #42 non-monotone analysis: dark-sector cascade has SIGNED epsilon.")
    print()
    print("Reframe: cascade rate-parameter is epsilon(t) = sign(df_RD/dt) * |epsilon_K(t)|")
    print()
    print("Under thawing-CPL:")
    print("  epsilon(t) > 0 for cosmic time < t_peak (now ~16 Gyr away)")
    print("  epsilon(t) = 0 at t_peak (instantaneous balance)")
    print("  epsilon(t) < 0 for cosmic time > t_peak")
    print()
    print("Under LCDM (monotone):")
    print("  epsilon(t) > 0 for all cosmic time; asymptotes to 0 at de Sitter heat death")
    print()
    print("This is consistent with [[user_stance_asymptotic_dof_sidesteps_infinity]]")
    print("sharpening (Spike #41): epsilon is the rate-of-approach. Under thawing-CPL,")
    print("the rate-of-approach has both positive and negative regimes -- the cascade")
    print("approaches an asymptote that is BELOW its peak value.")
    print()

    # Emit NDJSON records
    records = []

    # Trajectory samples
    a_grid = []
    a = 0.1
    while a <= 100.0:
        a_grid.append(a)
        a *= 1.05  # log-spaced
    for a in a_grid:
        f_thawing = f_RD(a, W0_THAWING, WA_THAWING)
        f_lcdm = f_RD(a, W0_LCDM, WA_LCDM)
        df_dt_thawing = df_RD_da(a, W0_THAWING, WA_THAWING) / dt_da_Gyr(a, W0_THAWING, WA_THAWING)
        records.append({
            "kind": "trajectory_sample",
            "a": a,
            "f_RD_thawing": f_thawing,
            "f_RD_LCDM": f_lcdm,
            "df_RD_dt_thawing_per_Gyr": df_dt_thawing,
            "phase": "rising" if df_dt_thawing > 1e-6 else ("falling" if df_dt_thawing < -1e-6 else "peak"),
        })

    # Summary record
    records.append({
        "kind": "non_monotone_summary",
        "f_RD_now_thawing": f_RD(1.0, W0_THAWING, WA_THAWING),
        "f_RD_now_LCDM": f_RD(1.0, W0_LCDM, WA_LCDM),
        "a_peak_thawing": a_peak,
        "f_RD_peak_thawing": f_peak,
        "cosmic_time_to_peak_Gyr": cosmic_time_Gyr(1.0, a_peak, W0_THAWING, WA_THAWING) if not math.isnan(a_peak) else None,
        "f_RD_asymptote_thawing": f_asymptote,
        "f_RD_asymptote_LCDM": f_RD(a_asymptote, W0_LCDM, WA_LCDM),
        "imprinting_cascade_sign_change_at_a": a_peak,
        "claim_bidirectional": (
            "The imprinting cascade is bidirectional under thawing-CPL: "
            "positive (un-creation; visible->dark) before peak; "
            "negative (creation; dark->visible) after peak."
        ),
        "epsilon_signing_per_spike_41_sharpening": (
            "Class K asymptotic-DOF rate-parameter epsilon is SIGNED. "
            "Sign tracks direction of cascade flow."
        ),
    })

    out_path = OUT_DIR / "spike_42_trajectory_records.ndjson"
    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")
    print(f"\nEmitted {len(records)} trajectory records to {out_path}")


if __name__ == "__main__":
    main()
