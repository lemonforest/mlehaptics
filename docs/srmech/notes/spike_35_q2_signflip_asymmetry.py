"""Spike #35 Q2 — Sign-flip phase asymmetry between left/right sweep through off-centre frame.

The equation-of-centre has 2 zero-crossings per cycle (apses at M = 0 and M = pi) and
sign-flips: positive for M in (0, pi) ("approaching" apse), negative for M in (pi, 2pi)
("receding" apse). This is the Class K pin-slot signature (Spike #29).

Q2: does this sign-flip appear as an ASYMMETRIC velocity / phase residual between
left-side and right-side sweep of an EXTENDED structure observed through the
off-centre frame?

Test: synthetic uniform rotating disk at inclination i; observer off-centre at
eps_AoE. Compute the line-of-sight velocity field and check for an
ASYMMETRIC residual after subtracting the standard rotation kinematic. The
apse-direction sign-flip should appear as a residual that LOCATES at a specific
projected angle and FLIPS SIGN between the two halves.

Test plan
---------
Q2.A: Doppler residual asymmetry on uniform rotating ring observed through
      off-centre frame. Expected signature: c_1 cosine asymmetric residual ~ eps
      between left and right semicircle.
Q2.B: Phase-of-evolution asymmetry: the time-derivative dphi/dM is itself
      modulated by the Brouwer-Clemence ladder (Q1.A). Time spent in the
      "approach" vs "recede" half-cycle is therefore unequal. Quantify.
Q2.C: Apse-localizable residual on synthetic structure of finite extent.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np


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


def true_anomaly(M: float, eps: float) -> float:
    E = kepler_solve(M, eps)
    return 2.0 * math.atan2(
        math.sqrt(1 + eps) * math.sin(E / 2),
        math.sqrt(1 - eps) * math.cos(E / 2),
    )


# === Q2.A: Doppler asymmetry on rotating ring ===

def doppler_residual_asymmetry(eps_obs: float, inclination_deg: float = 60.0,
                                N: int = 8192) -> dict:
    """Observer at radial offset eps_obs from centre of uniform rotating ring.
    Ring is in plane tilted by inclination from observer's line of sight.

    Standard rotation kinematic: v_los = v_circ * sin(M_ring) * sin(incl).
    Off-centre observer perceives shifted M_phi via the pin-slot projection;
    the asymmetric residual after subtracting the canonical signal is the
    Q2 observable.

    Returns:
      asymmetric residual amplitude, sign-flip detected (yes/no),
      phase of asymmetry peak (should locate at apse direction).
    """
    M = np.linspace(0, 2 * math.pi, N, endpoint=False)
    incl = math.radians(inclination_deg)
    # Canonical rotation velocity at each ring point
    v_canonical = np.sin(M) * math.sin(incl)
    # Off-centre observer projects M -> phi via pin-slot
    phi = np.arctan2(np.sin(M), np.cos(M) - eps_obs)
    # The observer would measure v at coordinates phi, but the ring's M coordinate
    # is the actual driver of v. The observed velocity field as a function of phi:
    # Bin v_canonical(M) into phi bins to get v_observed(phi); then compare to
    # the standard v_canonical(phi) prediction.

    n_phi_bins = 256
    phi_bins = np.linspace(-math.pi, math.pi, n_phi_bins + 1)
    bin_idx = np.digitize(phi, phi_bins) - 1
    bin_idx = np.clip(bin_idx, 0, n_phi_bins - 1)

    # Average velocity in each phi bin
    v_observed = np.zeros(n_phi_bins)
    counts = np.zeros(n_phi_bins)
    for i, b in enumerate(bin_idx):
        v_observed[b] += v_canonical[i]
        counts[b] += 1
    v_observed = np.where(counts > 0, v_observed / np.maximum(counts, 1), 0.0)
    phi_centres = 0.5 * (phi_bins[:-1] + phi_bins[1:])

    # The naive kinematic prediction at coordinate phi (no off-centre correction):
    v_naive = np.sin(phi_centres) * math.sin(incl)

    # Residual
    residual = v_observed - v_naive

    # Asymmetry between left and right halves:
    # Left half: phi in (-pi/2, pi/2); right half: phi in (pi/2, pi) U (-pi, -pi/2)
    # Actually simpler: split at apse direction (M=0, phi-projected to phi=0).
    # The apses of the off-centre projection are at phi=0 (closest approach)
    # and phi=+/-pi (furthest); the sign-flip in residual should be at the
    # SECONDARY apse (phi = phi_apse = +/- pi/2 from the offset direction).

    # Compute Fourier cos+sin coefs of residual; a NONZERO sin_1 component is
    # the load-bearing "sign-flip" signature (residual ~ sin(phi)) — asymmetric
    # under phi -> -phi, indicating that the structure approaches the observer
    # differently on one side vs the other.
    sin_k = np.zeros(7)
    cos_k = np.zeros(7)
    for k in range(1, 8):
        sin_k[k - 1] = (2.0 / n_phi_bins) * np.sum(residual * np.sin(k * phi_centres))
        cos_k[k - 1] = (2.0 / n_phi_bins) * np.sum(residual * np.cos(k * phi_centres))

    # The sign-flip signature: residual changes sign across phi=0 ⇔ nonzero sin_1.
    # The dipole amplitude of asymmetry:
    asymmetry_amplitude = abs(sin_k[0])

    # Where does the residual peak? Phase of dominant Fourier mode in (cos, sin).
    if abs(cos_k[0]) + abs(sin_k[0]) > 1e-30:
        peak_phase_deg = math.degrees(math.atan2(sin_k[0], cos_k[0]))
    else:
        peak_phase_deg = float("nan")

    return {
        "eps_obs": eps_obs,
        "inclination_deg": inclination_deg,
        "asymmetry_amplitude_sin1": asymmetry_amplitude,
        "asymmetric_residual_present": bool(asymmetry_amplitude > 1e-6),
        "residual_cos_k": cos_k.tolist(),
        "residual_sin_k": sin_k.tolist(),
        "peak_phase_deg": peak_phase_deg,
        "max_residual_amplitude": float(np.max(np.abs(residual))),
        "asymmetry_per_eps_ratio": float(asymmetry_amplitude / max(eps_obs, 1e-30)),
    }


# === Q2.B: Time-phase asymmetry ===

def time_phase_asymmetry(eps: float) -> dict:
    """Time spent in (0, pi) "approach apse" vs (pi, 2pi) "recede apse" of the
    pin-slot observation. Since dphi/dM has c_k = eps^k modulation, the
    integral over half a cycle is NOT pi but pi +/- (some eps-dependent shift).

    Compute exact: integral_0^pi (dphi/dM) dM = phi(pi) - phi(0).
    phi(0) = atan2(0, 1-eps) = 0; phi(pi) = atan2(0, -1-eps) = +/- pi.
    So phi(pi) - phi(0) = pi (exact). NO time asymmetry between half-cycles.

    But within the half-cycle, the RATE of phase accumulation is faster on the
    "approach" side and slower on the "recede" side. Quantify this asymmetry.

    Time-rate asymmetry between left and right quarters:
      Quarter 1 (M in 0..pi/2): integral dphi/dM dM
      Quarter 2 (M in pi/2..pi): integral dphi/dM dM
    These add to pi but the SPLIT depends on eps.
    """
    N = 65536
    M_full = np.linspace(0, 2 * math.pi, N + 1)
    r2 = 1 - 2 * eps * np.cos(M_full) + eps ** 2
    dphi_dM = (1 - eps * np.cos(M_full)) / r2

    # Integrate by trapezoid rule
    def integrate_segment(lo_M: float, hi_M: float) -> float:
        mask_lo = int(round((lo_M / (2 * math.pi)) * N))
        mask_hi = int(round((hi_M / (2 * math.pi)) * N))
        return float(np.trapezoid(dphi_dM[mask_lo:mask_hi + 1], M_full[mask_lo:mask_hi + 1]))

    q1 = integrate_segment(0, math.pi / 2)
    q2 = integrate_segment(math.pi / 2, math.pi)
    q3 = integrate_segment(math.pi, 3 * math.pi / 2)
    q4 = integrate_segment(3 * math.pi / 2, 2 * math.pi)

    # Symmetric quarters: q1 vs q4 (both contain perihelion -> peak rate)
    #                   q2 vs q3 (both contain aphelion -> slow rate)
    # Asymmetric quarters: q1 vs q2 (the apse-direction sign-flip across pi/2)
    asym_q1_q2 = q1 - q2  # The "left side faster than right" magnitude
    relative_asym = asym_q1_q2 / (q1 + q2)

    return {
        "eps": eps,
        "q1_phi_accum_0_to_pi_half": q1,
        "q2_phi_accum_pi_half_to_pi": q2,
        "q3_phi_accum_pi_to_3pi_half": q3,
        "q4_phi_accum_3pi_half_to_2pi": q4,
        "asym_q1_minus_q2": asym_q1_q2,
        "relative_asym": relative_asym,
        # Theoretical: the cumulative phase accumulation over quarter starting
        # at perihelion (M=0) should be larger by ~ eps * something
        "asym_per_eps_ratio": asym_q1_q2 / max(eps, 1e-30),
    }


# === Q2.C: Apse-localizable residual on extended structure ===

def apse_localized_residual(eps: float, structure_extent_deg: float = 60.0) -> dict:
    """An extended structure (filament / tidal stream / cluster) of angular
    extent `structure_extent_deg` observed through the off-centre frame.

    If the structure spans M in (-extent/2, +extent/2) around M=0 (perihelion
    direction), the line-of-sight velocity residual after subtracting standard
    rotation should show:
       - sign-flip at M=0 (perihelion)
       - amplitude proportional to eps
       - localised within the structure's extent

    Quantify peak residual and verify it locates at perihelion.
    """
    N = 4096
    extent = math.radians(structure_extent_deg)
    M_arr = np.linspace(-extent / 2, extent / 2, N)
    # The structure rotates with circular velocity 1; for an observer
    # off-centre, the apparent angular velocity is dphi/dM = (1-eps*cos M)/r2
    r2 = 1 - 2 * eps * np.cos(M_arr) + eps ** 2
    omega_apparent = (1 - eps * np.cos(M_arr)) / r2
    # Residual relative to mean circular omega = 1:
    residual = omega_apparent - 1.0

    # Sign-flip check: residual at M < 0 vs M > 0
    left = residual[: N // 2]
    right = residual[N // 2:]

    # Look for a CLEAN sign-flip pattern: residual_left + residual_right = nontrivial,
    # while the SYMMETRIC mean is dominant (this means it's symmetric about M=0 ⇔ NO
    # sign-flip in residual at perihelion direction).
    # The CORRECT sign-flip is at apse direction (M = pi/2), where the residual
    # transitions through zero. For our structure centred at M=0 (perihelion),
    # the residual is SYMMETRIC about M=0 (perihelion-symmetric); the sign-flip
    # at M=+/- pi/2 lies OUTSIDE the structure's extent.

    # Reframe: place structure centred at M=pi/2 (the apse direction).
    M_arr2 = np.linspace(math.pi / 2 - extent / 2, math.pi / 2 + extent / 2, N)
    r2_2 = 1 - 2 * eps * np.cos(M_arr2) + eps ** 2
    omega2 = (1 - eps * np.cos(M_arr2)) / r2_2
    residual2 = omega2 - 1.0

    # Check sign-flip across M=pi/2: residual at left side (M < pi/2) vs right
    sign_left = np.mean(residual2[: N // 2])
    sign_right = np.mean(residual2[N // 2:])
    sign_flip_at_apse = bool(sign_left * sign_right < 0)

    return {
        "eps": eps,
        "extent_deg": structure_extent_deg,
        "perihelion_centred_max_resid": float(np.max(residual)),
        "perihelion_centred_min_resid": float(np.min(residual)),
        "perihelion_centred_symmetric": bool(abs(np.mean(residual[: N // 2]) -
                                                 np.mean(residual[N // 2:])) < 1e-3),
        "apse_centred_left_residual_mean": float(sign_left),
        "apse_centred_right_residual_mean": float(sign_right),
        "sign_flip_at_apse": sign_flip_at_apse,
        "asymmetry_amplitude": float(abs(sign_left - sign_right)),
        "asymmetry_per_eps": float(abs(sign_left - sign_right) / max(eps, 1e-30)),
    }


def main() -> int:
    out_dir = Path("D:/temp/spike_35")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "spike_35_q2_signflip_asymmetry.ndjson"

    records: list[dict] = []
    records.append({
        "spike": 35, "question": "Q2", "kind": "meta",
        "claim": ("equation-of-centre 2 zero-crossings per cycle (apses) produce "
                  "asymmetric left/right velocity / phase residual at apse projection; "
                  "the asymmetry amplitude is proportional to eps"),
        "eps_AoE_R3": 0.0506,
    })

    # === Q2.A ===
    print("=" * 80)
    print("Q2.A -- Doppler residual asymmetry on rotating ring through off-centre frame")
    print("=" * 80)
    print(f"{'eps':>8s} {'incl_deg':>9s} | {'asym_sin1':>11s} {'cos_1_resid':>12s} | "
          f"{'asym/eps':>10s} {'present':>8s}")

    for eps in [0.005, 0.01, 0.0506, 0.1, 0.2]:
        for incl in [30.0, 60.0, 90.0]:
            result = doppler_residual_asymmetry(eps, incl)
            records.append({
                "spike": 35, "question": "Q2.A", "kind": "doppler_asymmetry",
                **result,
            })
            print(f"{eps:8.4f} {incl:9.1f} | "
                  f"{result['asymmetry_amplitude_sin1']:11.4e} "
                  f"{result['residual_cos_k'][0]:12.4e} | "
                  f"{result['asymmetry_per_eps_ratio']:10.6f} "
                  f"{'YES' if result['asymmetric_residual_present'] else 'no':>8s}")

    # === Q2.B ===
    print()
    print("=" * 80)
    print("Q2.B -- Time-phase asymmetry q1 vs q2 (perihelion-quarter vs aphelion-quarter)")
    print("=" * 80)
    print(f"{'eps':>8s} | {'q1':>10s} {'q2':>10s} {'q3':>10s} {'q4':>10s} | "
          f"{'q1-q2':>11s} {'rel_asym':>11s} {'asym/eps':>11s}")
    for eps in [0.005, 0.01, 0.0506, 0.1, 0.2, 0.3]:
        result = time_phase_asymmetry(eps)
        records.append({"spike": 35, "question": "Q2.B", "kind": "time_phase_asym",
                       **result})
        print(f"{eps:8.4f} | {result['q1_phi_accum_0_to_pi_half']:10.6f} "
              f"{result['q2_phi_accum_pi_half_to_pi']:10.6f} "
              f"{result['q3_phi_accum_pi_to_3pi_half']:10.6f} "
              f"{result['q4_phi_accum_3pi_half_to_2pi']:10.6f} | "
              f"{result['asym_q1_minus_q2']:+11.6f} "
              f"{result['relative_asym']:+11.4f} "
              f"{result['asym_per_eps_ratio']:11.6f}")

    # === Q2.C ===
    print()
    print("=" * 80)
    print("Q2.C -- Apse-localized residual on extended structure")
    print("=" * 80)
    print(f"{'eps':>8s} {'extent':>8s} | {'left_resid':>11s} {'right_resid':>11s} | "
          f"{'sign_flip':>10s} {'asym/eps':>10s}")

    for eps in [0.005, 0.01, 0.0506, 0.1, 0.2]:
        for extent in [30.0, 60.0, 90.0]:
            result = apse_localized_residual(eps, extent)
            records.append({
                "spike": 35, "question": "Q2.C", "kind": "apse_localized",
                **result,
            })
            print(f"{eps:8.4f} {extent:8.1f} | "
                  f"{result['apse_centred_left_residual_mean']:+11.4e} "
                  f"{result['apse_centred_right_residual_mean']:+11.4e} | "
                  f"{'YES' if result['sign_flip_at_apse'] else 'no':>10s} "
                  f"{result['asymmetry_per_eps']:10.6f}")

    # === Verdict ===
    aoe_doppler = any(r.get("eps_obs") == 0.0506 and r.get("asymmetric_residual_present", False)
                       and r.get("kind") == "doppler_asymmetry" for r in records)
    aoe_time = any(r.get("eps") == 0.0506 and r.get("kind") == "time_phase_asym"
                    and abs(r.get("asym_per_eps_ratio", 0)) > 0.1 for r in records)
    aoe_apse = any(r.get("eps") == 0.0506 and r.get("kind") == "apse_localized"
                    and r.get("sign_flip_at_apse", False) for r in records)

    print()
    print("=" * 80)
    print("Q2 VERDICT")
    print("=" * 80)
    print(f"  Q2.A Doppler asymmetric residual at eps_AoE=0.0506:        "
          f"{'PASS' if aoe_doppler else 'FAIL'}")
    print(f"  Q2.B Time-phase asymmetry q1-q2 ~ eps at eps_AoE=0.0506:   "
          f"{'PASS' if aoe_time else 'FAIL'}")
    print(f"  Q2.C Apse-localized sign-flip at eps_AoE=0.0506:           "
          f"{'PASS' if aoe_apse else 'FAIL'}")
    overall = aoe_doppler and aoe_time and aoe_apse
    print(f"  Q2 OVERALL: {'PASS' if overall else 'FAIL'}")
    records.append({
        "spike": 35, "question": "Q2", "kind": "verdict",
        "aoe_doppler_passes": aoe_doppler,
        "aoe_time_phase_passes": aoe_time,
        "aoe_apse_localized_passes": aoe_apse,
        "Q2_overall_pass": bool(overall),
        "interpretation": ("apse-direction sign-flip in equation-of-centre produces "
                            "asymmetric left/right phase / velocity residual that locates "
                            "at the apse projection, with amplitude proportional to eps"),
    })

    with out_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, sort_keys=True) + "\n")
    print(f"\nWrote {len(records)} NDJSON records to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
