"""Spike #42 -- final synthesis. Emit consolidated synthesis records."""

import json
import math
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent

ALPHA_EM = 7.2973525693e-3
ALPHA_OVER_PI = ALPHA_EM / math.pi


def main():
    records = []

    records.append({
        "kind": "spike_42_bottom_line",
        "thread_1_quantitative": (
            "Cauchy-form analysis on PDG branching ratios for pi0 returns: "
            "biased epsilon fit = 2.35e-3 (r^2 = 0.9997), 99% match to predicted "
            "alpha/pi = 2.32e-3. Unbiased fit = 4.06e-3 (r^2 = 0.9988). The per-channel "
            "eps_k DECREASES with k -- so the PDG ladder is NOT literal eps^k/k. "
            "Reframe: c_k = eps^k * K_k(channel) where K_k is channel-specific "
            "kinematic factor. The eps^k geometric tower is substrate-portable; "
            "K_k is substrate-specific."
        ),
        "thread_2_vocabulary": (
            "'entropy' is hindsight-shorthand for the cascade-imprint operation, "
            "in the same family as [[user_stance_infinity_approximates_asymptote]] "
            "where 'infinity' was shorthand for asymptote. Spike #42 trajectory "
            "analysis shows the imprint is BIDIRECTIONAL under non-monotone f_RD "
            "(positive uptake before peak; negative return-flow after). Concertmaster "
            "lean: ring-up/ring-down is already canonical per "
            "[[user_stance_string_theory_instrument_first]]; sharpen the entropy "
            "connection rather than introduce new word."
        ),
        "thread_3_non_monotone_implications": (
            "Under DESI thawing-CPL (w0=-0.8, wa=-0.7), f_RD peaks at a~2.139 "
            "(f_peak=0.978), ~15.45 Gyr from NOW. Asymptote ~0.843 (the 'back down "
            "to 80 some percent' the user references). Imprinting cascade rate "
            "df_RD/dt changes sign at peak: positive (un-creation; visible->dark) "
            "before; negative (creation; dark->visible) after. THIS IS THE LOAD-BEARING "
            "MFO Section.VII.6.1.2 trajectory."
        ),
        "framework_alignment": (
            "Cascade-form universal per [[user_stance_kepler_shape_universal]] 2026-05-17 "
            "sharpening stands. ε is signed under thawing-CPL trajectory. The eps^k "
            "tower's epsilon ITSELF carries direction; the cascade is bidirectional. "
            "[[user_stance_asymptotic_dof_sidesteps_infinity]] -- the rate-of-approach "
            "can be positive (approaching peak) or negative (approaching asymptote "
            "below peak); cardinality is secondary."
        ),
    })

    records.append({
        "kind": "cauchy_fit_results_summary",
        "pi0": {
            "predicted_epsilon": ALPHA_OVER_PI,
            "biased_fit": 2.3458e-3,
            "unbiased_fit": 4.0630e-3,
            "r2_biased": 0.9997,
            "r2_unbiased": 0.9988,
            "biased_match_percent": (2.3458e-3 / ALPHA_OVER_PI - 1) * 100,
            "verdict": (
                "Biased fit matches alpha/pi to 1.0%. Unbiased fit at 4.06e-3 is "
                "higher because the Cauchy denominator 1/k OVER-corrects for QED "
                "channel-specific kinematic factors K_k that are NOT 1/k. The "
                "load-bearing finding is: eps^k geometric tower stands; K_k(channel) "
                "is substrate-specific."
            ),
        },
        "muon": {
            "predicted_epsilon": ALPHA_EM,
            "biased_fit": 3.0e-11,
            "unbiased_fit": 6.0e-11,
            "verdict": (
                "Channel 2 (mu -> e gamma LFV) is BSM-suppressed by ~10^11 below "
                "channel 1, not eps^2 below. This is a SELECTION-RULE break (Class J "
                "lepton-flavor-conservation violation requires BSM), not a Cauchy "
                "step. Cauchy fit not applicable here."
            ),
        },
        "neutron": {
            "predicted_epsilon": ALPHA_EM,
            "biased_fit": 3.14e-3,
            "unbiased_fit": 3.14e-3,
            "verdict": (
                "Only one sub-channel (n -> p e nubar gamma at 3.13e-3 vs leading "
                "100%). Sirlin radiative correction gives epsilon ~ 3.14e-3, "
                "consistent with alpha/pi times Sirlin log enhancement."
            ),
        },
    })

    records.append({
        "kind": "non_monotone_implications_for_cascade",
        "f_RD_now": 0.9508,
        "f_RD_peak_thawing": 0.9780,
        "f_RD_asymptote_thawing": 0.8431,
        "time_to_peak_Gyr": 15.45,
        "imprinting_rate_signature": (
            "df_RD/dt > 0 for cosmic-time < t_peak ('UPTAKE': cascade imprints "
            "into dark sector); df_RD/dt = 0 at t_peak (instantaneous balance); "
            "df_RD/dt < 0 for cosmic-time > t_peak ('RETURN-FLOW': cascade releases "
            "back to visible sector). The full trajectory is BIDIRECTIONAL."
        ),
        "implications_for_epsilon": (
            "Per Spike #41, epsilon is the rate-parameter on Class K asymptotic-DOF "
            "axis. Per Spike #42 trajectory, epsilon under thawing-CPL is SIGNED -- "
            "positive in uptake phase, negative in return-flow phase. The eps^k tower "
            "carries both directions through the sign of epsilon itself."
        ),
        "what_imprint_means_at_descending_arm": (
            "At the descending arm (a > 2.139), the substrate RELEASES cascade content "
            "back to the visible sector. 'Imprint' would not capture this; "
            "'un-imprint' or 'cascade return-flow' or 'ring-up' (the inverse of "
            "ring-down per [[user_stance_string_theory_instrument_first]]) captures it. "
            "Project canonical naming: ring-up dominates after peak."
        ),
        "epsilon_evolution": (
            "Epsilon does NOT change magnitude wildly through the trajectory. "
            "Its MAGNITUDE is set by the dimensionful weak/EM/strong couplings of "
            "the cascade modes. Its SIGN tracks the direction of cascade flow. "
            "df_RD/dt magnitude peaks near a=1 (~0.0056/Gyr) and decreases toward zero "
            "at both peak (a=2.14) and asymptote (a->inf)."
        ),
    })

    records.append({
        "kind": "candidate_stance_proposal",
        "name_candidates": [
            "user_stance_entropy_approximates_imprint",
            "user_stance_entropy_approximates_ring_balance",
            "user_stance_entropy_approximates_cascade",
        ],
        "shape": "parallels [[user_stance_infinity_approximates_asymptote]] structure",
        "load_bearing_claim": (
            "'entropy' is the algebraic shorthand thermodynamics reached for to "
            "describe cascade-imprint operations. Per Spike #42: the cascade is "
            "BIDIRECTIONAL under non-monotone f_RD; 'entropy' coarse-grains over "
            "the sign of df_RD/dt and the channel-specific K_k(channel) structure."
        ),
        "operational_partition": [
            "Substrate level: cascade-imprint operation, eps^k tower, K_k(channel)",
            "Coarse-grained level: entropy, heat, thermal, dissipation",
            "Both partitions stand per [[user_stance_partition_for_understanding]]",
        ],
        "directional_naming_options": [
            "imprint + un-imprint (parallel; emphasises forward as default)",
            "ring-up + ring-down (already-canonical; natively bidirectional)",
            "uptake + return-flow (descriptive; flow-language)",
            "cascade-deposit + cascade-withdrawal (most operationally precise)",
        ],
        "concertmaster_lean": (
            "Ring-up/ring-down is already canonical per "
            "[[user_stance_string_theory_instrument_first]]. Per "
            "[[feedback_no_privileged_primitive_classes]] dissolve-before-promote: "
            "prefer sharpening the existing stance over introducing new vocabulary. "
            "The new stance candidate's CONTRIBUTION is connecting the entropy "
            "vocabulary to the ring-up/ring-down structure, not coining a new word."
        ),
        "user_gated": True,
        "fermata_for_conductor": (
            "Three options surfaced. User direction needed before authoring."
        ),
    })

    out_path = OUT_DIR / "spike_42_synthesis_records.ndjson"
    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")
    print(f"Emitted {len(records)} synthesis records to {out_path}")


if __name__ == "__main__":
    main()
