#!/usr/bin/env python3
"""
Spike #161 — AGN past-direction extended discovery.

User direction 2026-05-19:
> "did our AGN ball was already here when processive motivator arrived theory research?"

Per [[feedback_always_check_both_directions_including_time]]: Spike #152 tested
FUTURE-direction (AGN survive sign-flip at +13.66 Gyr). This spike tests
PAST-direction explicitly — were AGN already present when the precessive
motivator's "arrival" occurred?

The user's question forces a precise definition of "arrival." We test three
operationalizations:

  (a) ARRIVAL_SUBSTRATE_COEVAL — the precessive motivator is substrate-coeval
      with the substrate itself. "Arrival" = Big Bang or earlier. Per
      [[user_stance_universal_precession_at_substrate_level]] this is the
      load-bearing reading (substrate cycle-phase is monotonic from t=0).

  (b) ARRIVAL_LAST_PHI_ZERO_RESET — "arrival" = most recent φ=0 crossing of the
      current substrate cycle. With T_sub = 109.84 Gyr and φ_now ≈ 0.789 rad
      (≈ 45.2° = 1/8 past φ=0), the last reset was at t = 0 (Big Bang exactly
      aligns with the start of the current substrate cycle per Spike #98).
      Same as (a) for the current epoch.

  (c) ARRIVAL_FIRST_OBSERVABLE_MANIFESTATION — "arrival" = first cosmic epoch
      at which precession became OBSERVABLE in 3D_s. Per Saadeh 2016
      isotropy bound at 121k:1 odds against 3D_s shear, this never happens
      at current sensitivity. But the framework's read of the FIRST
      precessive sign-flip (φ = π/2 crossing) is a candidate "first
      observable manifestation event." Per Spike #152 that first sign-flip
      is at t = 27.46 Gyr — in the FUTURE. So no past arrival under (c).

  (d) FIRST DIMPLE SIGN-FLIP IN THE PAST — per
      [[user_stance_bidirectional_3ds_7dg_dimple_with_epoch_sign_flip]],
      dimple-direction reverses at φ = π/2 / π / 3π/2 / 2π crossings.
      LOOK BACKWARD: at what past cosmic epoch was the LAST sign-flip
      (going backwards: previous φ=0 crossing AT t=0; before that the
      previous cycle's φ=3π/2 sign-flip occurred at t = −T_sub/4 ≈
      −27.46 Gyr — i.e., BEFORE THE BIG BANG). So under this framework
      reading, the LAST past sign-flip happened "before the Big Bang"
      relative to the current substrate cycle.

For each operationalization, we compare against the cosmic time of observed
high-redshift AGN:

  - SDSS J1342+0928 at z=7.54 (Bañados+ 2018 Nature 553:473; arXiv:1712.01860)
    cosmic time ≈ 690 Myr post-Big-Bang
  - UHZ1 at z=10.3 (Bogdán+ 2024 / Larson+ 2023; Chandra+JWST detection;
    arXiv:2305.15458 + arXiv:2308.10980)
    cosmic time ≈ 470 Myr post-Big-Bang
  - ULAS J1120+0641 at z=7.085 (Mortlock+ 2011 Nature 474:616)
    cosmic time ≈ 770 Myr post-Big-Bang

Plus cross-substrate "fossil" comparison:

  - Population III stars: theoretical formation z ≈ 30 → t ≈ 100 Myr
  - First globular clusters: oldest at age ≈ 13.0 Gyr → formed ≈ 800 Myr
    post-Big-Bang (z ≈ 6-7)
  - Cosmic web filaments: dark-matter-dominated, traceable to recombination
    (z=1100 → t=380 kyr) but observable filaments form at z~5-6
  - CMB: z = 1100, t = 380 kyr post-Big-Bang
  - BBN: t = 1-1000 s post-Big-Bang

Outputs:
  - spike161_records_2026-05-19.ndjson — NDJSON per-record findings
  - prints quantitative results to stdout

Framework anchors (per Spike #152):
  - H_0 = 67.66 km/s/Mpc (Planck 2018 VI)
  - Ω_m = 0.315, Ω_Λ = 0.685, Ω_b = 0.0493, Ω_r ≈ 9.2e-5
  - T_sub = 2π/H_Λ ≈ 109.84 Gyr (Spike #98)
  - φ_now ≈ 0.789 rad = 45.22° (matches "1/8 past last local minimum" stance)

DEFENSIVE / RESEARCH-EDUCATIONAL ONLY per [[feedback_trauma_informed_defensive_scope]].
"""

from __future__ import annotations

import json
import math
from pathlib import Path

# ---------------------------------------------------------------------------
# Cosmological anchors (Planck 2018 VI + PDG 2024) — identical to Spike #152
# ---------------------------------------------------------------------------

H0_KMS_MPC = 67.66
H0_PER_GYR = H0_KMS_MPC * (3.1557e16 / 3.0857e19)
T_HUBBLE_GYR = 1.0 / H0_PER_GYR

OMEGA_M = 0.315
OMEGA_L = 0.685
OMEGA_B = 0.0493
OMEGA_C = OMEGA_M - OMEGA_B
OMEGA_R = 9.2e-5

T_SUB_GYR = 109.84
T_NOW_GYR = 13.797
PHASE_NOW = 2.0 * math.pi * T_NOW_GYR / T_SUB_GYR  # ≈ 0.789 rad

# Substrate-cycle anchor
OMEGA_SUB_RAD_S = 2.0 * math.pi / (T_SUB_GYR * 3.1557e16)  # ≈ 1.81e-18 rad/s

# ---------------------------------------------------------------------------
# Standard cosmology helpers
# ---------------------------------------------------------------------------

def hubble_LCDM(a: float) -> float:
    return math.sqrt(OMEGA_R / a**4 + OMEGA_M / a**3 + OMEGA_L)

def cosmic_time_LCDM_gyr(a: float, n_steps: int = 200000) -> float:
    """Integrate t(a) = ∫_0^a da'/(a' H(a'))."""
    if a <= 0:
        return 0.0
    log_a0 = -10.0
    log_a1 = math.log(a)
    dlog = (log_a1 - log_a0) / n_steps
    t = 0.0
    for i in range(n_steps):
        log_a_mid = log_a0 + (i + 0.5) * dlog
        a_mid = math.exp(log_a_mid)
        t += dlog / hubble_LCDM(a_mid)
    return t * T_HUBBLE_GYR

def a_from_z(z: float) -> float:
    return 1.0 / (1.0 + z)

def cosmic_time_from_z_gyr(z: float) -> float:
    return cosmic_time_LCDM_gyr(a_from_z(z), n_steps=200000)

def f_RD_LCDM(a: float) -> float:
    """Ring-down fraction f_RD = Ω_dark / Ω_total."""
    rho_b = OMEGA_B / a**3
    rho_r = OMEGA_R / a**4
    rho_c = OMEGA_C / a**3
    rho_L = OMEGA_L
    rho_total = rho_b + rho_r + rho_c + rho_L
    return (rho_c + rho_L) / rho_total

def omega_visible_fraction(a: float) -> float:
    rho_b = OMEGA_B / a**3
    rho_total = OMEGA_R / a**4 + OMEGA_M / a**3 + OMEGA_L
    return rho_b / rho_total

# ---------------------------------------------------------------------------
# Past-direction precessive-motivator schedule
# ---------------------------------------------------------------------------

def past_sign_flip_schedule(phase_now: float, n_past_cycles: int = 3) -> list[dict]:
    """
    Look BACKWARDS along the substrate cycle-phase axis.

    Phase progresses monotonically at rate 2π/T_sub. At the Big Bang (t=0)
    the current substrate cycle's φ = 0 (per Spike #98 anchor — substrate-
    cycle is coeval with cosmological substrate; φ_now ≈ 1/8 past φ=0 →
    last φ=0 reset was at t=0 exactly).

    Looking before t=0: PREVIOUS substrate cycle's events occur at negative
    cosmic time. The previous φ=3π/2 sign-flip was at t = -T_sub/4 ≈
    -27.46 Gyr (i.e., before the Big Bang).

    Returns past-direction event schedule for n_past_cycles before now.
    """
    events = []
    targets_in_cycle = [
        (0.0,             "phi=0 (current cycle start)"),
        (math.pi/2,       "phi=pi/2 (Re sign-flip)"),
        (math.pi,         "phi=pi (Im sign-flip)"),
        (3*math.pi/2,     "phi=3pi/2 (Re sign-flip)"),
        (2*math.pi,       "phi=2pi (cycle complete = phi=0 next)"),
    ]
    # The current cycle: phase grows from 0 to 2π over t in [0, T_sub]
    # Phase NOW = 2π t_now / T_sub
    # past events: phases φ_k < phase_now in current cycle, plus all of previous cycles
    # Convert each target phase to its absolute "phase coordinate" running backward
    # In current cycle (k=0): event_phase = target (in [0, 2π])
    # In previous cycle (k=-1): event_phase = target - 2π * 1 (in [-2π, 0])
    # ...etc
    for k in range(0, -n_past_cycles - 1, -1):
        for tp, name in targets_in_cycle:
            event_phase_abs = tp + 2.0 * math.pi * k
            if event_phase_abs > phase_now:
                continue
            # cosmic time at this event
            delta_phase = phase_now - event_phase_abs  # positive (in past)
            dt_gyr = delta_phase * T_SUB_GYR / (2.0 * math.pi)
            t_event_gyr = T_NOW_GYR - dt_gyr
            events.append({
                "cycle_offset": k,
                "phase_target_rad": tp,
                "phase_target_label": name,
                "event_phase_abs_rad": event_phase_abs,
                "delta_from_now_gyr": -dt_gyr,
                "cosmic_time_gyr": t_event_gyr,
                "is_pre_big_bang": t_event_gyr < 0,
            })
    events.sort(key=lambda r: r["cosmic_time_gyr"], reverse=True)
    return events

# ---------------------------------------------------------------------------
# High-z AGN observational anchors
# ---------------------------------------------------------------------------
#
# Citation hygiene per [[feedback_pdf_extraction_citation_discipline]]:
#   - SDSS J1342+0928 (z=7.5413): Bañados+ 2018, Nature 553:473.
#     arXiv:1712.01860. CITE-BY-REF (Round 1 — PDF not extracted this spike).
#     Cosmic time at z=7.54: ~690 Myr (Planck cosmology).
#   - UHZ1 (z≈10.3): Bogdán+ 2024 (Chandra X-ray, Nature Astronomy);
#     Larson+ 2023 (JWST spectroscopy, ApJL 953:L29).
#     arXiv:2305.15458 (Larson NIRSpec) + arXiv:2308.10980 (Bogdán Chandra).
#     CITE-BY-REF.
#   - ULAS J1120+0641 (z=7.0851): Mortlock+ 2011, Nature 474:616.
#     CITE-BY-REF.
#   - Pop III formation z~20-30: Bromm+ 2002 ApJ 564:23 (theory); cite-by-ref.
#   - Globular cluster ages: VandenBerg+ 2013 ApJ 775:134; cite-by-ref.
#   - CMB / BBN: PDG 2024 standard cosmology; cite-by-ref.
#
# Note: all cosmic-time values computed in this script from Planck 2018 cosmology
# and z; the citations are for the redshift measurements themselves.

OBSERVATIONAL_ANCHORS = [
    {"label": "UHZ1",                "z": 10.3,    "source": "Bogdán+ 2024 / Larson+ 2023 (arXiv:2308.10980 / arXiv:2305.15458)", "kind": "AGN"},
    {"label": "SDSS J1342+0928",     "z": 7.5413,  "source": "Bañados+ 2018 (arXiv:1712.01860)",                                  "kind": "AGN"},
    {"label": "ULAS J1120+0641",     "z": 7.0851,  "source": "Mortlock+ 2011 (Nature 474:616)",                                   "kind": "AGN"},
    {"label": "Population III (theory upper)", "z": 30.0, "source": "Bromm+ 2002 (theory; cite-by-ref)",                          "kind": "first stars"},
    {"label": "Population III (theory lower)", "z": 20.0, "source": "Bromm+ 2002 (theory; cite-by-ref)",                          "kind": "first stars"},
    {"label": "Earliest globular cluster", "z": 6.5, "source": "VandenBerg+ 2013 (cite-by-ref; age ~13.0 Gyr)",                   "kind": "globular cluster"},
    {"label": "First cosmic web filaments (theory)", "z": 5.0, "source": "Sheth-Tormen 1999 / Bond 1996 (cite-by-ref)",           "kind": "cosmic web"},
    {"label": "CMB recombination",   "z": 1100.0,  "source": "Planck 2018 VI (arXiv:1807.06209)",                                 "kind": "CMB"},
    # BBN handled below (special — t = ~3 minutes post-Big-Bang)
]

# ---------------------------------------------------------------------------
# Ring-down completion at past epochs (per [[user_stance_dark_sector_ring_down_age]])
# ---------------------------------------------------------------------------

def ring_down_progression_summary(anchor_times: list[tuple[str, float]]) -> list[dict]:
    """For each (label, cosmic_time_gyr) anchor, compute f_RD at that epoch.

    Per the user-stance ring-down age model:
      a → 0 (Big Bang): 0% ring-down
      a ≈ 3e-4 (matter-radiation equality): ~42% ring-down
      a = 1 (now): 95% ring-down
      a → ∞: 100% ring-down
    """
    out = []
    for label, t_gyr in anchor_times:
        # invert cosmic_time → a numerically
        lo, hi = 1.0e-10, 1.0e3
        for _ in range(80):
            mid = math.sqrt(lo * hi)
            t_mid = cosmic_time_LCDM_gyr(mid, n_steps=50000)
            if t_mid < t_gyr:
                lo = mid
            else:
                hi = mid
        a_at_anchor = lo
        f_rd_at_anchor = f_RD_LCDM(a_at_anchor)
        out.append({
            "label": label,
            "cosmic_time_gyr": t_gyr,
            "scale_factor": a_at_anchor,
            "f_RD": f_rd_at_anchor,
            "f_RD_pct": f_rd_at_anchor * 100.0,
        })
    return out

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    records: list[dict] = []
    print("=" * 80)
    print("Spike #161 — AGN past-direction extended discovery")
    print("=" * 80)

    # (1) Three arrival operationalizations
    print("\n--- (1) Three operationalisations of 'precessive motivator arrival' ---\n")

    # (a) Substrate-coeval — arrival = Big Bang (or earlier)
    arrival_a = {
        "label": "(a) ARRIVAL_SUBSTRATE_COEVAL",
        "interpretation": "precessive motivator coeval with substrate itself",
        "cosmic_time_of_arrival_gyr": 0.0,
        "note": "per Spike #98 + [[user_stance_universal_precession_at_substrate_level]]; substrate cycle-phase monotonic from t=0",
    }
    print(f"  (a) Substrate-coeval: arrival at t = 0 Gyr (Big Bang or earlier)")
    records.append({"spike": 161, "record_type": "arrival_operationalisation", **arrival_a})

    # (b) Last φ=0 reset
    # Phase now ≈ 0.789 rad in current cycle (k=0); last reset at t such that φ=0
    # → φ_now * T_sub / (2π) = T_NOW_GYR → t_last_reset = 0 (exactly Big Bang)
    t_last_phi_zero = T_NOW_GYR - (PHASE_NOW / (2.0 * math.pi)) * T_SUB_GYR
    arrival_b = {
        "label": "(b) ARRIVAL_LAST_PHI_ZERO_RESET",
        "interpretation": "last substrate-cycle φ=0 reset",
        "cosmic_time_of_arrival_gyr": t_last_phi_zero,
        "phase_now_rad": PHASE_NOW,
        "T_sub_gyr": T_SUB_GYR,
        "note": "current φ_now = 0.789 rad ≈ 45° = 1/8 past φ=0; coincides with Big Bang per substrate-coeval anchor",
    }
    print(f"  (b) Last φ=0 reset: t = {t_last_phi_zero:.4f} Gyr (matches Big Bang)")
    records.append({"spike": 161, "record_type": "arrival_operationalisation", **arrival_b})

    # (c) First observable manifestation
    arrival_c_first_sign_flip = T_NOW_GYR + (math.pi/2 - PHASE_NOW) * T_SUB_GYR / (2.0 * math.pi)
    arrival_c = {
        "label": "(c) ARRIVAL_FIRST_OBSERVABLE_MANIFESTATION",
        "interpretation": "first cosmic epoch at which precession is observable (first sign-flip)",
        "cosmic_time_of_arrival_gyr": arrival_c_first_sign_flip,
        "delta_from_now_gyr": arrival_c_first_sign_flip - T_NOW_GYR,
        "note": "FUTURE event; framework predicts precession invisible until first sign-flip; past-direction question is N/A for this reading",
        "past_direction_applicable": False,
    }
    print(f"  (c) First observable manifestation: t = {arrival_c_first_sign_flip:.2f} Gyr (FUTURE event; past-direction N/A)")
    records.append({"spike": 161, "record_type": "arrival_operationalisation", **arrival_c})

    # (2) Past-direction sign-flip schedule
    print("\n--- (2) Past-direction sign-flip schedule (3 cycles back) ---\n")
    past_events = past_sign_flip_schedule(PHASE_NOW, n_past_cycles=3)
    for ev in past_events[:15]:  # closest 15
        flag = " [PRE-BIG-BANG]" if ev["is_pre_big_bang"] else ""
        print(f"  {ev['phase_target_label']:34s}: t = {ev['cosmic_time_gyr']:9.2f} Gyr  (Δ = {ev['delta_from_now_gyr']:9.2f}){flag}")
        records.append({
            "spike": 161,
            "record_type": "past_sign_flip",
            **ev,
        })

    # (3) High-z AGN past-direction test
    print("\n--- (3) High-z AGN vs precessive-motivator arrival ---\n")
    agn_records = []
    for anchor in OBSERVATIONAL_ANCHORS:
        t_gyr = cosmic_time_from_z_gyr(anchor["z"])
        t_myr = t_gyr * 1000.0
        # Test against each arrival operationalisation
        delta_a = t_gyr - arrival_a["cosmic_time_of_arrival_gyr"]
        delta_b = t_gyr - arrival_b["cosmic_time_of_arrival_gyr"]
        # delta_c is N/A since arrival_c is in the future

        verdict_vs_a = "POST-arrival" if delta_a > 0 else "PRE-arrival"
        verdict_vs_b = "POST-arrival" if delta_b > 0 else "PRE-arrival"

        print(f"  {anchor['label']:42s} z={anchor['z']:6.2f}  t={t_myr:7.1f} Myr  vs(a) {verdict_vs_a:13s}  vs(b) {verdict_vs_b:13s}")

        rec = {
            "spike": 161,
            "record_type": "high_z_anchor",
            "label": anchor["label"],
            "z": anchor["z"],
            "kind": anchor["kind"],
            "source": anchor["source"],
            "cosmic_time_gyr": t_gyr,
            "cosmic_time_myr": t_myr,
            "delta_vs_arrival_a_gyr": delta_a,
            "delta_vs_arrival_b_gyr": delta_b,
            "verdict_vs_a": verdict_vs_a,
            "verdict_vs_b": verdict_vs_b,
        }
        records.append(rec)
        agn_records.append(rec)

    # BBN special — t ≈ 3 min = 5.7e-14 Gyr
    bbn_rec = {
        "spike": 161,
        "record_type": "high_z_anchor",
        "label": "BBN (3 min post-BB)",
        "z": 1.0e9,  # very early
        "kind": "BBN",
        "source": "PDG 2024 (cite-by-ref)",
        "cosmic_time_gyr": 5.71e-14,
        "cosmic_time_myr": 5.71e-11,
        "delta_vs_arrival_a_gyr": 5.71e-14,
        "delta_vs_arrival_b_gyr": 5.71e-14,
        "verdict_vs_a": "POST-arrival",
        "verdict_vs_b": "POST-arrival",
    }
    records.append(bbn_rec)
    print(f"  {'BBN (3 min)':42s} z=large  t=  0.0 Myr  vs(a) POST-arrival   vs(b) POST-arrival")

    # (4) Ring-down completion at past epochs
    print("\n--- (4) Ring-down completion (f_RD) at past anchor epochs ---\n")
    anchor_times = [(a["label"], a["cosmic_time_gyr"]) for a in agn_records] + [("now", T_NOW_GYR)]
    rd_progression = ring_down_progression_summary(anchor_times)
    for r in rd_progression:
        print(f"  {r['label']:42s} t={r['cosmic_time_gyr']*1000:7.1f} Myr  f_RD = {r['f_RD_pct']:6.2f}%")
        records.append({
            "spike": 161,
            "record_type": "ring_down_at_past_anchor",
            **r,
        })

    # (5) Cross-substrate "fossil" partition
    print("\n--- (5) Cross-substrate fossil partition (pre/post-first-past-sign-flip) ---\n")
    # First past sign-flip = LAST φ-crossing before now. Per (2): the φ=0
    # current-cycle start at t=0; before that (k=-1 cycle): φ=3π/2 at
    # t = -T_sub/4 ≈ -27.46 Gyr (PRE-BIG-BANG)
    last_past_signflip_in_observable = past_events[0]
    print(f"  Most recent past sign-flip in observable universe: "
          f"{last_past_signflip_in_observable['phase_target_label']} at t = "
          f"{last_past_signflip_in_observable['cosmic_time_gyr']:.4f} Gyr")
    print(f"  (If this is at t=0, ALL observable AGN are POST-arrival relative to it)")
    print()
    pre_first_signflip = []
    post_first_signflip = []
    flip_time = last_past_signflip_in_observable["cosmic_time_gyr"]
    for rec in agn_records + [bbn_rec]:
        if rec["cosmic_time_gyr"] < flip_time:
            pre_first_signflip.append(rec["label"])
        else:
            post_first_signflip.append(rec["label"])
    print(f"  PRE-first-past-sign-flip (t < {flip_time:.2f} Gyr): {pre_first_signflip if pre_first_signflip else 'NONE in observable'}")
    print(f"  POST-first-past-sign-flip: {len(post_first_signflip)} anchors")
    records.append({
        "spike": 161,
        "record_type": "cross_substrate_partition",
        "first_past_signflip_time_gyr": flip_time,
        "pre_signflip_anchors": pre_first_signflip,
        "post_signflip_anchors": post_first_signflip,
    })

    # (6) Composite verdict
    print("\n--- (6) Composite past-direction verdict ---\n")
    summary = {
        "spike": 161,
        "record_type": "framework_summary",
        "scope": "research-educational",
        "do_not_canonicalize": True,
        "verdict_compose": [
            "ARRIVAL-A-SUBSTRATE-COEVAL-AGN-ALL-POST-ARRIVAL",
            "ARRIVAL-B-LAST-PHI-ZERO-RESET-COINCIDES-WITH-BIG-BANG",
            "ARRIVAL-C-FIRST-OBSERVABLE-MANIFESTATION-FUTURE-PAST-N/A",
            "ALL-OBSERVED-AGN-POST-PRECESSIVE-MOTIVATOR-ARRIVAL-UNDER-FRAMEWORK-CANONICAL-READING",
            "LAST-PAST-SIGN-FLIP-IS-PHI-EQUALS-ZERO-AT-BIG-BANG-OR-PRE-BIG-BANG-IF-LOOKING-BEYOND",
            "RING-DOWN-AT-470-MYR-UHZ1-EPOCH-FAR-FROM-95-PCT-CURRENT",
            "USER-FRAMING-AGN-ALREADY-HERE-WHEN-MOTIVATOR-ARRIVED-REQUIRES-PRE-BIG-BANG-AGN-NOT-OBSERVED",
            "BIDIRECTIONAL-DIMPLE-EPOCH-FLIP-AT-PHI-EQUALS-ZERO-IS-T-EQUALS-ZERO-PER-SUBSTRATE-COEVAL",
            "ZERO-NEW-PRIMITIVE-CLASS-REQUIRED",
            "DO-NOT-MERGE-AUTONOMOUSLY-HIGH-VOCABULARY-IMPACT",
        ],
        "agn_count_post_arrival": len(post_first_signflip),
        "agn_count_pre_arrival_a": 0,
        "framework_anchor_spikes": [98, 124, 152],
    }
    records.append(summary)
    for line in summary["verdict_compose"]:
        print(f"  - {line}")

    # Write NDJSON
    out_path = Path(__file__).parent / "spike161_records_2026-05-19.ndjson"
    with out_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, sort_keys=True, default=str) + "\n")
    print(f"\nWrote {len(records)} records to {out_path}")

    return records


if __name__ == "__main__":
    main()
