"""
Spike #144 overall synthesis — three axes summary.

Axis 1: heliopause boundary unit-consistency check (n=2)
Axis 2: Faraday rotation vs stellar density at latitude scale (n=4)
Axis 3: close binary R_HE vs inter-component d_geom (n=5)
Axis 3 (corrected): same after data-quality correction
"""

import json
import math
from pathlib import Path

# Per-axis summary
axis_verdicts = {
    "axis1_heliopause_dgeom_consistency": "UNIT-CONSISTENT-WEAK-N2",
    "axis2_RM_vs_stellar_vs_HI": "DEGENERATE-LAT-SCALE-NO-DISCRIMINATION",
    "axis3_close_binary_RHE_dgeom": "ORIGINAL-NEGATIVE-CORRECTED-TO-NULL",
}

# Cross-axis structure
axis1_supports_framework = False  # only "doesn't contradict", weak
axis2_supports_framework = False  # null, can't discriminate
axis3_supports_framework = False  # null after correction

n_strong_positive = 0
n_weak_positive = 1  # axis 1 (consistency check)
n_null = 2           # axis 2, axis 3 corrected
n_negative_original_pre_correction = 1  # axis 3 original

# Stance-candidate implications
# The pre-spike candidate stance was:
#   magnetic_field_is_2d_boundary_of_7d_g_ball
# Three axes provide NO consolidated empirical support for this
# stance at the inter-body scale that goes beyond intra-body
# Spike #143 results. Specifically:
#   - Axis 1: framework "doesn't contradict" the heliopause distance,
#     but standard ram-pressure model also gets within factor ~1.23.
#     No discrimination.
#   - Axis 2: at gross latitude scale (n=4), all canonical proxies
#     (n_e, H I, CO, stellar density) co-vary with RM. Higher-resolution
#     pixel-level analysis would be required.
#   - Axis 3: with proper data quality (V471 Tau K-dwarf field; Saar-
#     Reiners saturation), the original signal disappears. Saturated
#     regime makes the test underpowered a priori.

stance_implications = {
    "candidate_stance": "magnetic_field_is_2d_boundary_of_7d_g_ball",
    "stance_held_pending_decision": True,
    "spike_144_provides_consolidated_support": False,
    "spike_144_falsifies_stance": False,
    "honest_summary": (
        "Spike #144 returns three NULL or WEAK results at inter-body scale. "
        "None of the three axes provides discrimination between framework "
        "and canonical models, due to (a) tiny n, (b) degenerate alternative "
        "proxies at gross spatial scales, (c) saturation effects in close-"
        "binary regime. Spike #143's intra-body d_geom monotone signal stays. "
        "Inter-body extension is currently UNDERDETERMINED. The stance candidate "
        "remains held pending consolidated multi-spike evidence."
    ),
}

# Overall verdict
records = [
    {
        "date": "2026-05-19",
        "spike": "#144",
        "kind": "overall_synthesis",
        "branch": "research/spike-144-inter-body-7dg-ball-boundary-signatures",
        "parent_spike": "#143",
        "axis_verdicts": axis_verdicts,
        "n_strong_positive": n_strong_positive,
        "n_weak_positive": n_weak_positive,
        "n_null": n_null,
        "stance_candidate_status": "HELD-NO-CONSOLIDATED-SUPPORT-FROM-SPIKE-144",
        "overall_verdict": "INTER-BODY-EXTENSION-UNDERDETERMINED-FROM-CURRENT-AXES",
        "intra_body_signal_preserved": "Spike #143 intra-body d_geom monotone signal NOT affected; result stands at p<0.05",
        "n_observations_total": 11,  # 2 + 4 + 5
        "method_caveat": "Small-n across all axes; pre-registered roster locked the spike out of post-hoc curation; results report what math gives.",
    },
    {
        "date": "2026-05-19",
        "spike": "#144",
        "kind": "stance_decision_input",
        **stance_implications,
    },
    {
        "date": "2026-05-19",
        "spike": "#144",
        "kind": "follow_up_dispatches",
        "spike_candidates": [
            {
                "name": "pixel-level RM analysis",
                "rationale": "Axis 2 degeneracy is gross-bin artifact; pixel-level Oppermann RM map vs Gaia DR3 stellar density at HEALPix Nside=64 would test the framework at angular scales below disk-scale-height where stellar density doesn't track HI",
                "scope": "1-2 day spike, requires healpy + downloading Oppermann RM healpix map",
            },
            {
                "name": "RS CVn / Algol P_rot harmonic Fourier search",
                "rationale": "Axis 3 saturation argument means R_HE test is wrong shape; direct test is Fourier-decomposing photometric light curves of synchronized close binaries to find harmonic content at n*P_orb beyond fundamental, controlling for ellipsoidal variation",
                "scope": "2-3 day spike, requires TESS/Kepler photometry of synchronized binary sample",
            },
            {
                "name": "magnetar QPO inter-7D_g-ball coupling",
                "rationale": "Magnetar quasi-periodic oscillations at kHz tied to inter-7D_g-ball boundary modes; far stronger inter-body coupling expected; SGR 1806-20 hyperflare QPO catalog gives clean substrate",
                "scope": "high-effort spike, requires careful framework prediction first",
            },
        ],
    },
]

out_path = Path(__file__).resolve().parent / "spike144_overall_synthesis.ndjson"
with out_path.open("w", encoding="utf-8") as f:
    for r in records:
        f.write(json.dumps(r) + "\n")

print("SPIKE 144 — INTER-BODY 7D_G BALL BOUNDARY SIGNATURES")
print(f"  Axis 1 (heliopause):       UNIT-CONSISTENT-WEAK-N2")
print(f"  Axis 2 (Faraday vs stars): DEGENERATE-LAT-SCALE-NO-DISCRIMINATION")
print(f"  Axis 3 (close binaries):   ORIGINAL-NEGATIVE-CORRECTED-TO-NULL")
print(f"  Overall verdict: INTER-BODY-EXTENSION-UNDERDETERMINED")
print(f"  Stance candidate magnetic_field_is_2d_boundary_of_7d_g_ball: HELD")
print(f"  Spike #143 intra-body signal preserved (independent finding)")
print(f"  Output: spike144_overall_synthesis.ndjson")
