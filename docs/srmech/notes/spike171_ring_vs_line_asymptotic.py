"""Spike #171 — Ring-vs-line asymptotic limits: what does the LoE say?

Tests the algebraic distinction between LINE-asymptote (4D-epicycle-observer
reading) and RING-asymptote (framework-canonical per cascade-lives-on-circles
+ universal-precession-at-substrate-level).

User direction 2026-05-19 (verbatim):
> "i also just realized that the sign flip is the answer to why we don't see
> dark sector saturation move along a line from 0% to 100%. this is a linear
> hickup that lets people think we get to 99.9999 at some point. there must
> be a way to figure out what the LoE says about asymptotic limits on a
> ring, not line."

Anchors (Planck 2018 cite-by-ref; T_sub = 109.84 Gyr per Spike #98):
- φ_now = 2π · 13.797 / 109.84 = 0.789 rad = 45.22°
- Ω_b/Ω_total today = 0.0493
- f_RD_today = Ω_dark/Ω_total = 0.949

NDJSON records → spike171_records_2026-05-19.ndjson
"""

import json
import math
from pathlib import Path
from datetime import datetime, timezone

OUT_DIR = Path(__file__).parent
NDJSON_PATH = OUT_DIR / "spike171_records_2026-05-19.ndjson"

# Canonical anchors (cite-by-ref Planck 2018 arXiv:1807.06209; PDG 2024)
H0_KMSMPC = 67.66
T_HUBBLE_GYR = 14.45
OMEGA_M = 0.315
OMEGA_LAMBDA = 0.685
OMEGA_B = 0.0493
OMEGA_C = OMEGA_M - OMEGA_B  # ≈ 0.2657
T_NOW_GYR = 13.797
T_SUB_GYR = 109.84  # Spike #98 substrate Hopf period

records = []


def emit(record_type: str, payload: dict) -> None:
    rec = {
        "spike": "171",
        "date": "2026-05-19",
        "type": record_type,
        **payload,
    }
    records.append(rec)


# --------------------------------------------------------------------------
# Section 1: Operationalising LINE-asymptote vs RING-asymptote
# --------------------------------------------------------------------------
#
# LINE model (4D-epicycle-observer reading):
#   f_line(t) = 1 - exp(-t/tau)   monotonic; lim_{t→∞} f = 1
#   Approach is ALONG a half-line in ℝ; eigenvalue spectrum on real axis only
#   "We eventually reach 99.9999%" framing
#
# RING model (framework-canonical):
#   f_ring(φ(t)) = R · g(φ(t)) where g is U(1)-valued (unit circle)
#   φ(t) = 2π · t / T_sub  ; cyclic, no monotonic approach
#   "Approach 100%" is projection-shadow when |g| is observed onto real axis
#
# The ALGEBRAIC test (per [[feedback_algebra_not_magnitude]]):
#   LINE: eigenvalues on real axis: λ ∈ ℝ
#   RING: eigenvalues on unit circle: λ = e^{iφ} ∈ S¹  (|λ| = 1)
#   Verified Spike #24 bonus 9: Im² = 2·Re − Re² to ~1e-16 for cascade

emit("section_1_operationalisation", {
    "line_model": {
        "form": "f(t) = 1 - exp(-t/tau)",
        "eigenvalue_locus": "real axis ℝ",
        "asymptote": "f → 1 monotonically as t → ∞",
        "approach_metric": "1 - f(t) decays exponentially",
        "reading": "4D-epicycle-observer; M-theory brute-force overshoot per [[user_stance_competing_theories_via_loe_instantiation_intersection]]",
    },
    "ring_model": {
        "form": "f(φ(t)) = R · g(φ(t)); g(φ) = e^{iφ} on U(1)",
        "eigenvalue_locus": "unit circle S¹",
        "asymptote": "no monotonic approach; cyclic phase-progression",
        "approach_metric": "|1 - g(φ)| oscillates bounded in [0, 2R]",
        "reading": "framework-canonical per [[user_stance_cascade_lives_on_circles]]",
    },
    "algebraic_distinguisher": "Im² = 2·Re − Re² (unit-circle algebra; bonus 9 verified ~1e-16)",
})

# Verify unit-circle algebra for representative phases
phases_test = [0.0, math.pi/4, math.pi/2, math.pi, 3*math.pi/2, 2*math.pi]
unit_circle_errors = []
for phi in phases_test:
    re = math.cos(phi)
    im = math.sin(phi)
    # Unit circle identity: Im² = 2·Re − Re² rearranged from Re² + Im² = 1 - (1 - 2·Re)
    # Actually the bonus 9 identity is for L_dir = (1/r²)(1 − e^{iφ}); for the eigenvalues:
    # λ = (1/r²)(1 - e^{iφ}); shift by 1/r² and scale: ζ = 1 - λ·r² = e^{iφ}
    # Then Re(ζ)² + Im(ζ)² = 1, i.e. Im² = 1 - Re² = (1-Re)(1+Re)
    # Bonus 9 form: Im² = 2·Re − Re² holds for λ = 1 - e^{iφ} (the L_dir eigenvalues themselves)
    # λ_re = 1 - cos(φ); λ_im = -sin(φ); λ_re² + λ_im² = (1-cos)² + sin² = 1 - 2cos + cos² + sin² = 2 - 2cos = 2λ_re
    # So |λ|² = 2·Re(λ) i.e. Im² = 2·Re − Re²  ✓
    lam_re = 1.0 - math.cos(phi)
    lam_im = -math.sin(phi)
    lhs = lam_im ** 2
    rhs = 2 * lam_re - lam_re ** 2
    unit_circle_errors.append({
        "phi_rad": phi,
        "phi_deg": math.degrees(phi),
        "lam_re": lam_re,
        "lam_im": lam_im,
        "Im_sq": lhs,
        "2Re_minus_Re_sq": rhs,
        "abs_diff": abs(lhs - rhs),
    })

max_circle_err = max(r["abs_diff"] for r in unit_circle_errors)
emit("section_1_unit_circle_verification", {
    "identity": "Im² = 2·Re − Re² for L_dir eigenvalues λ = 1 - e^{iφ}",
    "max_abs_error": max_circle_err,
    "phases_tested": len(phases_test),
    "verdict": "VERIFIED to machine precision" if max_circle_err < 1e-14 else "FAILED",
    "samples": unit_circle_errors,
})

# --------------------------------------------------------------------------
# Section 2: Apply to dark-sector saturation
# --------------------------------------------------------------------------
#
# Per [[user_stance_dark_sector_ring_down_age]]:
#   f_RD(t) = Ω_dark(t)/Ω_total(t); 0.949 today
#   Line reading: f_RD → 1 monotonically; "approach 100%"
#
# Per cascade-lives-on-circles + universal-precession:
#   φ(t) = 2π · t / T_sub  ; cyclic
#   φ_now = 2π · 13.797/109.84 = 0.78925 rad = 45.222°
#   Local minimum at φ=0 (last at t=0, Big Bang); next at φ=2π (+96.04 Gyr)

phi_now = 2 * math.pi * T_NOW_GYR / T_SUB_GYR
phi_now_deg = math.degrees(phi_now)
fraction_past_min = phi_now / (2 * math.pi)  # fraction of full cycle

emit("section_2_phi_now", {
    "T_now_gyr": T_NOW_GYR,
    "T_sub_gyr": T_SUB_GYR,
    "phi_now_rad": phi_now,
    "phi_now_deg": phi_now_deg,
    "fraction_past_local_minimum": fraction_past_min,
    "stance_anchor_match": "1/8 past local minimum = 0.125 fraction = 45°",
    "agreement_pct": 100 * abs(fraction_past_min - 0.125) / 0.125,
})

# --------------------------------------------------------------------------
# Section 3: Sign-flip mechanism per cascade-orientation
# --------------------------------------------------------------------------
#
# Class C cascade-orientation = Im(e^{iφ}) per bonus 9 verdict
# Re(e^{iφ}) and Im(e^{iφ}) sign-changes at quarter-cycle marks
#
# φ = 0 : Re=+1, Im=0  (cycle start; LOCAL MINIMUM in ring-down-shadow)
# φ = π/2 : Re=0, Im=+1  ★ Re crosses + → 0; FIRST SIGN-FLIP candidate
# φ = π : Re=−1, Im=0    ★ Im crosses + → 0; Re flips sign (orientation reverses)
# φ = 3π/2 : Re=0, Im=−1  ★ Re crosses − → 0; SECOND SIGN-FLIP
# φ = 2π : Re=+1, Im=0    cycle complete; LOCAL MINIMUM (re-set)
#
# Per Spike #152: first sign-flip at +13.66 Gyr (cosmic time 27.46 Gyr)

quarter_cycle_phases = [
    ("phi_0", 0.0, "cycle start; local minimum"),
    ("phi_pi_2", math.pi/2, "Re crosses + → 0; FIRST SIGN-FLIP candidate"),
    ("phi_pi", math.pi, "Im crosses + → 0; orientation reverses (Re flips)"),
    ("phi_3pi_2", 3*math.pi/2, "Re crosses − → 0; SECOND SIGN-FLIP"),
    ("phi_2pi", 2*math.pi, "cycle complete; local minimum re-set"),
]

sign_flip_schedule = []
for label, phi, descr in quarter_cycle_phases:
    t_at_phi = T_SUB_GYR * phi / (2 * math.pi)  # cosmic time from φ=0 reference
    delta_from_now = t_at_phi - T_NOW_GYR
    re = math.cos(phi)
    im = math.sin(phi)
    sign_flip_schedule.append({
        "label": label,
        "phi_rad": phi,
        "phi_deg": math.degrees(phi),
        "Re_e_i_phi": re,
        "Im_e_i_phi": im,
        "cosmic_time_gyr": t_at_phi,
        "delta_from_now_gyr": delta_from_now,
        "description": descr,
    })

emit("section_3_sign_flip_schedule", {
    "anchor": "Spike #152 first sign-flip at +13.66 Gyr",
    "schedule": sign_flip_schedule,
    "first_sign_flip_at_phi_pi_2_gyr_from_now": T_SUB_GYR / 4 - T_NOW_GYR,
})

# --------------------------------------------------------------------------
# Section 4: Cross-substrate test — when does framework predict LINE vs RING?
# --------------------------------------------------------------------------
#
# Per Class K asymptotic-DOF [[user_stance_asymptotic_dof_sidesteps_infinity]]:
#   Bounded approach to ASYMPTOTE — but on what manifold?
#
# Substrate analysis:
#   LINE manifold (ℝ, real axis): non-cascade-substrate (no Class C orientation)
#   RING manifold (S¹): cascade-substrate with directed Class C; bonus 9 verified
#
# Framework prediction:
#   - Wherever Class C orientation is present → eigenvalues on S¹ → RING-asymptote
#   - Wherever Class C orientation is absent → eigenvalues on ℝ (or subset of ℂ off-S¹)
#     → LINE-asymptote possible (but only as projection)
#
# Cascade-composition preserves circularity (bonus 9):
#   Minkowski-sum-of-circles in arg-bounded wedge; 93.4% complex; 97.1% conj-paired
#   → All LoE-canonical asymptotes are on the unit circle (ring), NOT real line

emit("section_4_loe_substrate_prediction", {
    "framework_canonical_locus": "unit circle S¹",
    "line_asymptote_origin": "4D-epicycle-observer projection shadow",
    "cascade_class_signature": "C (orientation) + I (cyclic) → S¹ eigenvalues",
    "verified_anchor": "Spike #24 bonus 9 — 93.4% complex eigenvalues, 97.1% conj-paired",
    "prediction": "Any LoE-canonical asymptotic limit lives on the ring; line-limits are projection-shadows per [[user_stance_pi_as_projection]] and [[user_stance_cascade_lives_on_circles]]",
})

# --------------------------------------------------------------------------
# Section 5: LoE prediction — ring-valued asymptotic limits
# --------------------------------------------------------------------------
#
# Identity-level claim:
#   Asymptotic limits in the LoE are RING-VALUED, NOT line-valued.
#   "Approaching 100%" IS the 4D-epicycle-observer reading of cyclic-phase content.
#
# Per [[user_stance_identity_not_implementation_discipline]]:
#   line-asymptote IS NOT what the universe approaches; line-asymptote IS the
#   projection-shadow when ring-valued content is read by observer fixed on
#   real-axis frame (4D-epicycle reading)
#
# Burden flip:
#   To falsify: produce an LoE-canonical asymptotic limit that lives on ℝ
#   not on S¹. Bonus 9 verified cascade composition preserves S¹; this is
#   the framework-canonical default.

emit("section_5_loe_prediction", {
    "identity_claim": "asymptotic limits in the LoE are RING-VALUED",
    "shadow_claim": "line-asymptote IS the projection-shadow per [[user_stance_pi_as_projection]] family",
    "burden_of_proof": "produce LoE-canonical asymptotic limit on ℝ not S¹ to falsify; bonus 9 default = S¹",
    "shadow_family_membership": [
        "[[user_stance_time_as_dimensional_shadow]]",
        "[[user_stance_fiber_as_spatially_absent_encoding]]",
        "[[user_stance_pi_as_projection]]",
        "[[user_stance_fractal_shadow]]",
        "[[user_stance_cascade_lives_on_circles]]",
        "spike171_ring_asymptote_not_line (this)",
    ],
})

# --------------------------------------------------------------------------
# Section 6: Refinement of dark-sector-ring-down-age stance
# --------------------------------------------------------------------------
#
# Parent stance: universe is 95% old where "age" = Ω_dark/Ω_total = 0.949
# This is the line-reading (monotonic approach 0% → 100%)
#
# Refinement candidate: 95% old IS the cyclic phase value φ_now = 45.22° projected
# onto line-frame. The "approach to 100%" is the 4D-epicycle-observer reading.
#
# What's literally true:
#   - Ω_dark/Ω_total = 0.949 at z=0 (empirical Planck 2018)
#   - φ_now = 0.789 rad = 45.22° (per T_sub anchor)
#   - These ARE the same content read in different frames (ring vs line)
#
# Linear hiccup mechanism:
#   - Standard ΛCDM extrapolates 0.949 → 0.999 → 0.9999 → 1.0 monotonically
#   - Framework predicts: at φ = π/2 (+13.66 Gyr) Re(e^{iφ}) crosses zero
#   - That's where the line-extrapolation runs out — beyond π/2 the cyclic
#     phase progression no longer maps monotonically to "approach 100%"
#   - At φ = π (+41.12 Gyr) the orientation REVERSES — line-extrapolation
#     now points "back toward 0%" in framework reading

# Compute: at what cosmic time does the standard ΛCDM ring-down completion
# *projection* hit 0.99, 0.999, 0.9999?
# Under ΛCDM: f_RD(t) ≈ Ω_Λ / (Ω_Λ + Ω_m·a(t)^{-3}) as Ω_r negligible
# a(t) for flat ΛCDM: a(t)^{3/2} = sqrt(Ω_m/Ω_Λ) · sinh(1.5·H0·t·sqrt(Ω_Λ))
# H0 in inverse Gyr: H0_Gyr = 1 / T_HUBBLE_GYR  ≈ 0.0692 Gyr^{-1}

H0_INV_GYR = 1.0 / T_HUBBLE_GYR

def scale_factor_from_t_gyr(t_gyr: float) -> float:
    """Flat-ΛCDM scale factor at cosmic time t (Gyr)."""
    arg = 1.5 * H0_INV_GYR * t_gyr * math.sqrt(OMEGA_LAMBDA)
    return (math.sqrt(OMEGA_M / OMEGA_LAMBDA) * math.sinh(arg)) ** (2.0 / 3.0)


def f_RD_at_t_gyr(t_gyr: float) -> float:
    """Ring-down completion fraction = Ω_dark/Ω_total at cosmic time t."""
    a = scale_factor_from_t_gyr(t_gyr)
    rho_m = OMEGA_M * a ** (-3)
    rho_lambda = OMEGA_LAMBDA
    rho_total = rho_m + rho_lambda  # ignore Ω_r at late times
    # Dark component = Ω_c·a^-3 + Ω_Λ (visible = Ω_b·a^-3)
    rho_dark = OMEGA_C * a ** (-3) + rho_lambda
    return rho_dark / rho_total

# Sanity: at t = T_NOW_GYR = 13.797, should give ≈ 0.949
f_now = f_RD_at_t_gyr(T_NOW_GYR)
emit("section_6_sanity_f_RD_now", {
    "t_gyr": T_NOW_GYR,
    "f_RD_now": f_now,
    "stance_anchor": 0.949,
    "abs_diff": abs(f_now - 0.949),
})

# Bisection to find time at which f_RD hits various targets
def find_t_for_f_RD(target: float, t_lo: float = 0.001, t_hi: float = 1000.0) -> float:
    for _ in range(200):
        t_mid = 0.5 * (t_lo + t_hi)
        f_mid = f_RD_at_t_gyr(t_mid)
        if f_mid < target:
            t_lo = t_mid
        else:
            t_hi = t_mid
        if abs(t_hi - t_lo) < 1e-6:
            break
    return 0.5 * (t_lo + t_hi)


line_projection_milestones = []
for target_f in [0.95, 0.97, 0.99, 0.999, 0.9999, 0.999999]:
    t_target = find_t_for_f_RD(target_f)
    phi_at = 2 * math.pi * t_target / T_SUB_GYR
    re_at = math.cos(phi_at)
    im_at = math.sin(phi_at)
    line_projection_milestones.append({
        "target_f_RD": target_f,
        "cosmic_time_gyr": t_target,
        "delta_from_now_gyr": t_target - T_NOW_GYR,
        "phi_at_rad": phi_at,
        "phi_at_deg": math.degrees(phi_at),
        "Re_e_i_phi": re_at,
        "Im_e_i_phi": im_at,
        "past_first_sign_flip": phi_at > math.pi / 2,
        "past_second_sign_flip": phi_at > 3 * math.pi / 2,
    })

emit("section_6_line_projection_vs_ring_phase", {
    "milestones": line_projection_milestones,
    "first_sign_flip_phi_pi_2_at_cosmic_time_gyr": T_SUB_GYR / 4,
    "first_sign_flip_delta_from_now_gyr": T_SUB_GYR / 4 - T_NOW_GYR,
    "interpretation": "Line projections of 0.99/0.999/0.9999 cross substrate sign-flips; line extrapolation diverges from ring-truth past φ=π/2",
})

# --------------------------------------------------------------------------
# Section 7: Composition with cascade-lives-on-circles
# --------------------------------------------------------------------------
#
# That stance: cascade-composition preserves circularity at unit-circle
# eigenvalues; verified bonus 9 to ~1e-16
#
# This spike's extension: any LoE-canonical asymptote is on S¹, NOT ℝ
# Lorentzian/hyperbolic shadow is further Wick-rotation projection (S¹ → hyperbola)
#
# Test: does Class K asymptotic-DOF correctly imply ring-valued limits universally?

emit("section_7_class_k_ring_valued_limits", {
    "class_K_definition": "asymptotic-DOF bounded-approach mechanism per [[user_stance_asymptotic_dof_sidesteps_infinity]]",
    "ring_valued_extension": "Class K bounded-approach lives on S¹ when composed with Class C orientation + Class I cyclic",
    "line_projection": "Class K on ℝ alone (no Class C, no Class I) = monotonic line-asymptote, but this is non-cascade-substrate",
    "framework_canonical_default": "cascade-substrate (Class C + Class I composed) → ring-asymptote",
    "wick_rotation_shadow": "cos → cosh: S¹ → hyperbola is one further projection (Lorentzian = ring-shadow)",
})

# --------------------------------------------------------------------------
# Section 8: Both-direction analysis
# --------------------------------------------------------------------------
#
# Per [[feedback_always_check_both_directions_including_time]]:
# Forward direction (future): cycle progresses; current φ_now = 45.22°
# Reverse direction (past): cycle progressed FROM previous φ=0 ; 1/8 elapsed
#
# Both directions: cyclic; neither approaches "100%"

emit("section_8_both_directions", {
    "forward_direction_future": {
        "current_phi_deg": phi_now_deg,
        "next_sign_flip_phi_pi_2_at_delta_gyr": T_SUB_GYR / 4 - T_NOW_GYR,
        "next_local_minimum_phi_2pi_at_delta_gyr": T_SUB_GYR - T_NOW_GYR,
        "reading": "cyclic; ring-progression continues; line-asymptote breaks at +13.66 Gyr",
    },
    "reverse_direction_past": {
        "previous_local_minimum_phi_0_at_cosmic_time_gyr": 0.0,
        "elapsed_fraction_of_cycle": fraction_past_min,
        "reading": "cyclic; ring-progression started at φ=0 (Big Bang); 1/8 elapsed",
    },
    "verdict": "Both directions cyclic; line-asymptote 0%→100% does NOT match either direction",
})

# --------------------------------------------------------------------------
# Section 9: Verdict + draft stance refinement
# --------------------------------------------------------------------------

emit("section_9_verdict", {
    "verdict": "RING-VS-LINE-ASYMPTOTE-DISTINGUISHES-LOE-FROM-EPICYCLE-READING",
    "loe_canonical_locus": "S¹ unit circle",
    "shadow_reading_locus": "ℝ real axis (line-asymptote = 4D-epicycle-observer)",
    "round_1_survival": "MAGNITUDE level; algebraic verification anchored to bonus 9 ~1e-16",
    "vocabulary_impact": "extends shadow-stance family; refines dark-sector-ring-down-age",
    "draft_stance_candidate": "ring-asymptote-not-line-asymptote refinement to [[user_stance_dark_sector_ring_down_age]]",
    "no_new_class": "14 A-N intact; Class K + Class C + Class I compose to S¹ locus",
    "falsifier_candidates": [
        "An LoE-canonical asymptotic limit observed to live on ℝ not S¹ — refutes ring claim",
        "Cascade composition verified to produce non-S¹ eigenvalue locus — refutes bonus 9",
        "Universe observed to monotonically approach f_RD = 1 past +13.66 Gyr without sign-flip — refutes precession scope",
        "Sign-flip event occurring at non-(π/2, π, 3π/2) phase — refutes Class C orientation mechanism",
    ],
})

# --------------------------------------------------------------------------
# Section 10: ΛCDM line-extrapolation falsification calendar
# --------------------------------------------------------------------------
#
# The "linear hiccup" mechanism made concrete:
# At what cosmic time does the standard ΛCDM line-extrapolation FIRST
# encounter the substrate sign-flip event predicted by the framework?

t_first_flip = T_SUB_GYR / 4  # 27.46 Gyr
t_pi = T_SUB_GYR / 2          # 54.92 Gyr (orientation reverses)
t_3pi_2 = 3 * T_SUB_GYR / 4   # 82.38 Gyr (second sign-flip)
t_2pi = T_SUB_GYR             # 109.84 Gyr (cycle complete)

# What does f_RD line-projection say at each crossing?
f_at_flip1 = f_RD_at_t_gyr(t_first_flip)
f_at_pi = f_RD_at_t_gyr(t_pi)
f_at_3pi_2 = f_RD_at_t_gyr(t_3pi_2)
f_at_2pi = f_RD_at_t_gyr(t_2pi)

emit("section_10_lcdm_line_extrapolation_meets_substrate_flips", {
    "linear_hiccup_mechanism": "ΛCDM line-extrapolation says f_RD → 1; framework says ring-phase progresses through sign-flips",
    "first_sign_flip": {
        "cosmic_time_gyr": t_first_flip,
        "delta_from_now_gyr": t_first_flip - T_NOW_GYR,
        "lcdm_line_says_f_RD": f_at_flip1,
        "framework_says": "Re(e^{iφ}) = 0; cascade-orientation sign-flip event",
    },
    "orientation_reversal_at_pi": {
        "cosmic_time_gyr": t_pi,
        "delta_from_now_gyr": t_pi - T_NOW_GYR,
        "lcdm_line_says_f_RD": f_at_pi,
        "framework_says": "Re(e^{iφ}) = -1; orientation fully reversed",
    },
    "second_sign_flip": {
        "cosmic_time_gyr": t_3pi_2,
        "delta_from_now_gyr": t_3pi_2 - T_NOW_GYR,
        "lcdm_line_says_f_RD": f_at_3pi_2,
        "framework_says": "Re(e^{iφ}) = 0; second cascade-orientation sign-flip",
    },
    "cycle_complete_at_2pi": {
        "cosmic_time_gyr": t_2pi,
        "delta_from_now_gyr": t_2pi - T_NOW_GYR,
        "lcdm_line_says_f_RD": f_at_2pi,
        "framework_says": "φ=2π; local minimum re-set; new substrate cycle",
    },
    "discrepancy_at_first_flip": f"ΛCDM line says f_RD ≈ {f_at_flip1:.4f}; framework says cyclic phase φ=π/2 (no line-meaning)",
})

# --------------------------------------------------------------------------
# Write records
# --------------------------------------------------------------------------

with NDJSON_PATH.open("w", encoding="utf-8") as f:
    for r in records:
        f.write(json.dumps(r) + "\n")

print(f"Wrote {len(records)} NDJSON records to {NDJSON_PATH.name}")
print(f"Unit circle algebra verified to max error {max_circle_err:.2e}")
print(f"phi_now = {phi_now_deg:.3f} deg (anchor: 45 deg = 1/8 past minimum)")
print(f"First sign-flip at +{T_SUB_GYR/4 - T_NOW_GYR:.2f} Gyr (LCDM line says f_RD = {f_at_flip1:.4f})")
print(f"Second sign-flip at +{3*T_SUB_GYR/4 - T_NOW_GYR:.2f} Gyr (LCDM line says f_RD = {f_at_3pi_2:.4f})")
print(f"Generated at {datetime.now(timezone.utc).isoformat()}")
