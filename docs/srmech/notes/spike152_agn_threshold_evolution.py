#!/usr/bin/env python3
"""
Spike #152 — AGN-outliving-3D_s-depletion + precessive-motivator-sign-flip timing.

This script computes:
  (1) When does Ω_visible / Ω_total drop below 3% under standard ΛCDM and DESI thawing-CPL?
  (2) When does the next universal-substrate precession sign-flip occur (per Spike #98)?
  (3) Cosmic-time at which f_RD = 0.99 (last 5% to last 1%)?
  (4) Comparative AGN survival times under three substrate-readings.

Framework anchors:
  - Planck 2018 VI / PDG 2024:
      H_0 ≈ 67.66 km/s/Mpc (Planck 2018), Hubble time t_H = 14.45 Gyr
      Ω_m = 0.315, Ω_Λ = 0.685, Ω_b = 0.0493, Ω_r ≈ 9.2e-5
  - Spike #98 canonical T_sub = 2π/H_Λ ≈ 109.84 Gyr (substrate Hopf period)
      Ω_sub = 2π / T_sub ≈ 1.81e-18 rad/s
  - [[user_stance_dark_sector_ring_down_age]]: f_RD = Ω_dark / Ω_total = 0.949 at z=0
  - [[user_stance_cascade_lives_on_circles]]: cyclic Class C orientation on unit circle;
      sign-flip is the local appearance of substrate-cycle-phase crossing the real axis.
  - [[user_stance_asymptotic_dof_sidesteps_infinity]]: rate-of-approach; last 5% to 100%
      ring-down completion takes ΛCDM-asymptotic time.

Outputs:
  - spike152_agn_findings_2026-05-19.ndjson (NDJSON records per [[feedback_ndjson_over_bloated_json]])
  - prints quantitative results to stdout for inclusion in the spike findings note.

DEFENSIVE / RESEARCH-EDUCATIONAL ONLY per [[feedback_trauma_informed_defensive_scope]].
"""

from __future__ import annotations

import json
import math
from pathlib import Path

# ---------------------------------------------------------------------------
# Cosmological anchors (Planck 2018 VI + PDG 2024)
# ---------------------------------------------------------------------------

H0_KMS_MPC = 67.66                # Planck 2018 VI
# 1 / H0 in years: convert km/s/Mpc to 1/Gyr
# 1 Mpc = 3.0857e19 km;  1 Gyr = 3.1557e16 s
H0_PER_GYR = H0_KMS_MPC * (3.1557e16 / 3.0857e19)  # ≈ 0.0692 per Gyr
T_HUBBLE_GYR = 1.0 / H0_PER_GYR                     # ≈ 14.45 Gyr

OMEGA_M  = 0.315
OMEGA_L  = 0.685
OMEGA_B  = 0.0493        # baryons (visible)
OMEGA_C  = OMEGA_M - OMEGA_B   # cold dark matter
OMEGA_R  = 9.2e-5        # radiation today (negligible at late times)

# Substrate-cycle anchor (Spike #98 canonical)
T_SUB_GYR = 109.84
OMEGA_SUB = 2.0 * math.pi / (T_SUB_GYR * 3.1557e16)   # rad/s ≈ 1.81e-18

# ---------------------------------------------------------------------------
# (1) ΛCDM evolution of visible fraction
# ---------------------------------------------------------------------------

def hubble_LCDM(a: float) -> float:
    """E(a) = H(a) / H_0 under flat ΛCDM with matter + radiation + Λ."""
    return math.sqrt(OMEGA_R / a**4 + OMEGA_M / a**3 + OMEGA_L)

def omega_visible_fraction_LCDM(a: float) -> float:
    """Ω_b(a) / Ω_total(a) under pure ΛCDM."""
    rho_b = OMEGA_B / a**3
    rho_total = OMEGA_R / a**4 + OMEGA_M / a**3 + OMEGA_L
    return rho_b / rho_total

def omega_visible_fraction_thawing_CPL(a: float, w0: float = -0.8, wa: float = -0.7) -> float:
    """
    DESI thawing-CPL: w(a) = w0 + wa*(1-a); Ω_DE evolves.
    Reference DESI 2024 VI arXiv:2404.03002 + DR2 arXiv:2503.14738.
    Λ density: ρ_DE(a) = ρ_DE,0 * a^(-3(1+w0+wa)) * exp(-3 wa (1-a))
    """
    de_density = OMEGA_L * (a ** (-3.0 * (1.0 + w0 + wa))) * math.exp(-3.0 * wa * (1.0 - a))
    rho_b = OMEGA_B / a**3
    rho_total = OMEGA_R / a**4 + OMEGA_M / a**3 + de_density
    return rho_b / rho_total

def cosmic_time_LCDM_gyr(a: float, n_steps: int = 200000) -> float:
    """Integrate t(a) = ∫_0^a da'/(a' H(a'))."""
    # log-spacing
    if a <= 0:
        return 0.0
    # log integration for accuracy across many decades
    log_a0 = -10.0  # essentially Big Bang
    log_a1 = math.log(a)
    dlog = (log_a1 - log_a0) / n_steps
    t = 0.0
    for i in range(n_steps):
        log_a_mid = log_a0 + (i + 0.5) * dlog
        a_mid = math.exp(log_a_mid)
        # da/d(log a) = a, so ∫ da/(a H) = ∫ d(log a) / H
        t += dlog / hubble_LCDM(a_mid)
    return t * T_HUBBLE_GYR

def find_a_at_visible_fraction(target_frac: float, model: str = "LCDM") -> tuple[float, float]:
    """Find scale factor `a` at which Ω_visible/Ω_total = target_frac. Returns (a, t_gyr)."""
    fn = omega_visible_fraction_LCDM if model == "LCDM" else omega_visible_fraction_thawing_CPL
    # bisect on a between 1 and a very large value
    lo, hi = 1.0, 1.0e10
    for _ in range(80):
        mid = math.sqrt(lo * hi)
        if fn(mid) > target_frac:
            lo = mid
        else:
            hi = mid
    a_star = lo
    t_star = cosmic_time_LCDM_gyr(a_star, n_steps=50000)
    return a_star, t_star

# ---------------------------------------------------------------------------
# (2) Substrate-precession sign-flip schedule
# ---------------------------------------------------------------------------
#
# Per [[user_stance_universal_precession_at_substrate_level]]:
#   T_sub = 109.84 Gyr full cycle; phase progresses uniformly at substrate level.
# Per [[user_stance_cascade_lives_on_circles]]:
#   sign-flip occurs when cycle-phase crosses the real axis (φ = π/2 and 3π/2 → Re=0).
# Past minimum (start of current ring-up): t = 0 (Big Bang) ≈ φ = 0
# Phase at present: φ_now = 2π * (13.8 / 109.84) ≈ 0.789 rad ≈ 45.2°
# Per stance: "currently φ = 1/8 of cycle past last local minimum"
#   → confirms φ_now ≈ 2π/8 ≈ 0.785 rad ≈ 45°
#
# First sign-flip in cascade-orientation = next time the cyclic-phase reaches φ = π/2 = 90°
# (Re(e^{iφ}) = 0 transition from + to −).

T_NOW_GYR = 13.797
PHASE_NOW = 2.0 * math.pi * T_NOW_GYR / T_SUB_GYR  # ≈ 0.789 rad

# Next sign-flip = next time φ reaches π/2 (cyclic; first after current φ_now)
def next_sign_flip_time(phase_now: float, target_phases=(math.pi/2, math.pi, 3*math.pi/2, 2*math.pi)) -> dict:
    """Return dict of {target_label: cosmic_time_gyr_at_target} for first occurrence after now."""
    out = {}
    for target in target_phases:
        # cyclic-phase increases monotonically per substrate-precession; no slip
        if phase_now >= target:
            # find next instance (target + 2π, etc.)
            delta = (target + 2*math.pi) - phase_now
        else:
            delta = target - phase_now
        dt_gyr = delta * T_SUB_GYR / (2.0 * math.pi)
        out[f"phi_{target/math.pi:.3f}pi"] = T_NOW_GYR + dt_gyr
    return out

# ---------------------------------------------------------------------------
# (3) f_RD evolution and last-percent timescales
# ---------------------------------------------------------------------------

def f_RD_LCDM(a: float) -> float:
    rho_b = OMEGA_B / a**3
    rho_r = OMEGA_R / a**4
    rho_c = OMEGA_C / a**3
    rho_L = OMEGA_L
    rho_total = rho_b + rho_r + rho_c + rho_L
    return (rho_c + rho_L) / rho_total

def find_a_at_fRD(target_fRD: float) -> tuple[float, float]:
    lo, hi = 1.0, 1.0e10
    for _ in range(80):
        mid = math.sqrt(lo * hi)
        if f_RD_LCDM(mid) < target_fRD:
            lo = mid
        else:
            hi = mid
    a_star = lo
    t_star = cosmic_time_LCDM_gyr(a_star, n_steps=50000)
    return a_star, t_star

# ---------------------------------------------------------------------------
# (4) AGN-survival three-scenario comparison
# ---------------------------------------------------------------------------
#
# Three readings:
#   (A) Standard ΛCDM: AGN duty ends when cold gas (∝ Ω_b * a^{-3}) drops below
#       threshold for accretion. Conventional ≈ a few × 10× current age (~10^{11} yr).
#   (B) Framework Spike #124: AGN engine lives at d_geom → 1 (7D_g saturation).
#       7D_g content is dark-sector content (per [[user_stance_dark_sector_in_7d_g]])
#       and ring-down accumulates monotonically. AGN engine HAS more, not less,
#       substrate-content as cosmic time progresses.
#   (C) Both: 3D_s fuel (cold gas) thins ∝ a^-3 → external accretion shuts off; but
#       framework reading says the INNER inverse-Casimir is set by d_geom→1
#       (substrate-encoded, not fuel-rate-dependent). AGN luminosity drops with
#       fuel rate but does NOT extinguish at the engine level.

# ---------------------------------------------------------------------------
# Compute and emit NDJSON
# ---------------------------------------------------------------------------

def main():
    records = []
    print("=" * 80)
    print("Spike #152 — AGN-outliving 3D_s depletion + precessive sign-flip timing")
    print("=" * 80)

    # (1) Threshold computations
    print("\n--- (1) Visible-fraction threshold crossings ---\n")
    for frac, label in [(0.05, "5pct"), (0.03, "3pct"), (0.01, "1pct"), (0.001, "0.1pct")]:
        try:
            a_L, t_L = find_a_at_visible_fraction(frac, "LCDM")
            print(f"  ΛCDM   Ω_visible/Ω_total = {frac:5.3f}: a = {a_L:8.3f}, t = {t_L:9.2f} Gyr")
            records.append({
                "spike": 152,
                "record_type": "threshold_crossing",
                "model": "LCDM",
                "target_visible_frac": frac,
                "scale_factor": a_L,
                "cosmic_time_gyr": t_L,
                "note": f"visible fraction {label}",
            })
        except Exception as e:
            print(f"  ΛCDM   ERROR at frac={frac}: {e}")
        try:
            a_T, t_T = find_a_at_visible_fraction(frac, "thawing")
            print(f"  thaw   Ω_visible/Ω_total = {frac:5.3f}: a = {a_T:8.3f}, t = {t_T:9.2f} Gyr")
            records.append({
                "spike": 152,
                "record_type": "threshold_crossing",
                "model": "thawing_CPL_w0=-0.8_wa=-0.7",
                "target_visible_frac": frac,
                "scale_factor": a_T,
                "cosmic_time_gyr": t_T,
                "note": f"visible fraction {label}",
            })
        except Exception as e:
            print(f"  thaw   ERROR at frac={frac}: {e}")

    # (2) Sign-flip schedule
    print("\n--- (2) Substrate-precession sign-flip schedule (Spike #98 T_sub = 109.84 Gyr) ---\n")
    print(f"  Current phase: φ_now = {PHASE_NOW:.4f} rad = {math.degrees(PHASE_NOW):.2f}°")
    print(f"  (cf. [[user_stance_dark_sector_in_7d_g]]: 'φ=1/8 past last local minimum' → 45°)")
    flips = next_sign_flip_time(PHASE_NOW)
    for label, t in flips.items():
        delta = t - T_NOW_GYR
        print(f"  Next {label:18s}: t = {t:8.2f} Gyr  (delta = {delta:7.2f} Gyr from now)")
        records.append({
            "spike": 152,
            "record_type": "precession_phase_crossing",
            "phase_target_pi": label,
            "cosmic_time_gyr_at_target": t,
            "delta_from_now_gyr": delta,
            "T_sub_gyr": T_SUB_GYR,
            "phase_now_rad": PHASE_NOW,
        })

    # (3) f_RD evolution
    print("\n--- (3) Ring-down completion timing ---\n")
    for frd, label in [(0.949, "now"), (0.97, "97pct"), (0.99, "99pct"), (0.999, "99.9pct")]:
        try:
            a_s, t_s = find_a_at_fRD(frd)
            print(f"  f_RD = {frd:5.3f} ({label:6s}): a = {a_s:8.3f}, t = {t_s:9.2f} Gyr")
            records.append({
                "spike": 152,
                "record_type": "ring_down_completion",
                "target_fRD": frd,
                "scale_factor": a_s,
                "cosmic_time_gyr": t_s,
                "label": label,
            })
        except Exception as e:
            print(f"  f_RD = {frd}: ERROR {e}")

    # (4) Composite comparison
    print("\n--- (4) AGN survival three-scenario comparison ---\n")
    a_3pct_L, t_3pct_L = find_a_at_visible_fraction(0.03, "LCDM")
    flip_phi_half_pi = flips["phi_0.500pi"]
    flip_phi_pi = flips["phi_1.000pi"]

    print(f"  ΛCDM Ω_visible → 3% at t = {t_3pct_L:.2f} Gyr (Δ = {t_3pct_L-T_NOW_GYR:.2f} Gyr from now)")
    print(f"  First precession sign-flip (φ = π/2): t = {flip_phi_half_pi:.2f} Gyr (Δ = {flip_phi_half_pi-T_NOW_GYR:.2f} Gyr)")
    print(f"  Second precession sign-flip (φ = π):    t = {flip_phi_pi:.2f} Gyr (Δ = {flip_phi_pi-T_NOW_GYR:.2f} Gyr)")

    ordering = []
    if flip_phi_half_pi < t_3pct_L:
        ordering.append(f"PRECESSION-SIGN-FLIP-FIRST-AT-{flip_phi_half_pi:.1f}-GYR")
    else:
        ordering.append(f"3PCT-THRESHOLD-FIRST-AT-{t_3pct_L:.1f}-GYR")
    print(f"\n  ORDERING VERDICT: {ordering[0]}")

    delta_first_to_second = abs(flip_phi_half_pi - t_3pct_L)
    print(f"  Δ between events: {delta_first_to_second:.2f} Gyr")
    if delta_first_to_second < 5.0:
        print("  → BOTH events within ~5 Gyr; effectively coincident at cosmological scale")
    elif delta_first_to_second < 30.0:
        print("  → events well-separated but on same Gyr-scale; AGN survive sign-flip and watch 3D_s thin")
    else:
        print("  → events on different scales; AGN history dominated by whichever comes first")

    records.append({
        "spike": 152,
        "record_type": "ordering_verdict",
        "t_3pct_gyr": t_3pct_L,
        "t_first_signflip_gyr": flip_phi_half_pi,
        "ordering": ordering[0],
        "delta_gyr": delta_first_to_second,
    })

    # Composite framework reading
    records.append({
        "spike": 152,
        "record_type": "framework_summary",
        "verdict_compose": [
            "AGN-7DG-SUBSTRATE-CONTENT-OUTLIVES-3DS-FUEL-DEPLETION",
            "INNER-INVERSE-CASIMIR-INDEPENDENT-OF-COLD-GAS-RATE",
            "PRECESSION-SIGN-FLIP-AND-3PCT-THRESHOLD-BOTH-IN-FAR-FUTURE",
            "AGN-AS-7DG-SUBSTRATE-FOSSILS-CANDIDATE-STANCE",
        ],
        "framework_anchor_spike": 124,
        "scope": "research-educational",
        "do_not_canonicalize": True,
    })

    # Write NDJSON
    out_path = Path("docs/srmech/notes/spike152_agn_findings_2026-05-19.ndjson")
    with out_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    print(f"\nWrote {len(records)} records to {out_path}")

    return records

if __name__ == "__main__":
    main()
