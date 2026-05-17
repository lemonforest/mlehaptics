"""Spike #41 final synthesis: write the closing assessment records."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

WORKSPACE = Path(__file__).resolve().parent
SYNTHESIS = WORKSPACE / "spike_41_synthesis_records_2026-05-17.ndjson"
DATE_TAG = "2026-05-17"


def emit(record: Dict) -> None:
    record = dict(record)
    record.setdefault("date", DATE_TAG)
    record.setdefault("spike", "spike_41")
    record.setdefault("timestamp", datetime.now(tz=timezone.utc).isoformat())
    with SYNTHESIS.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, default=float))
        fh.write("\n")


def main():
    # Append anomaly investigation summary
    emit({
        "kind": "anomaly_resolution_psd_artifact",
        "anomaly": "Step 5 PSD cosine sim ~ 1.0 between fibonacci_log and multinacci_log",
        "root_cause": "log(geometric_sequence) is a linear ramp; FFT of any linear ramp gives identical 1/k-sawtooth PSD shape",
        "resolution": "Time-domain PSD comparison is not a useful fingerprint for growing-substrate sequences. Coefficient-series Cauchy-form comparison (Step 6) is load-bearing.",
        "spike_38_pattern": "methodology degenerate at this regime",
    })

    # Cauchy bias resolution
    emit({
        "kind": "anomaly_resolution_cauchy_1k_bias",
        "anomaly": "Step 1 Kepler EOC at eps=0.1 gave biased eps_fit=0.088",
        "root_cause": "c_k = eps^k / k Cauchy form; log|c_k| has -log(k) bias term; biased fit under-estimates eps systematically",
        "resolution": "Fit log|c_k * k| instead; recovers eps to machine precision for ALL c_k = eps^k / k families (Kepler, Fibonacci psi-decay, Multinacci subdominant decay)",
        "spike_30b_precedent": "Spike #30B Anomaly 3 documented the same bias",
    })

    # Final bottom-line synthesis
    emit({
        "kind": "BOTTOM_LINE",
        "question": "Do (A) Fibonacci, (B) 11D fractal projection, (C) gear+pin-slot cascade share the same structural fingerprint?",
        "verdict": "PARTIAL UNITY at three structural levels; partition-level differences are expected per [[user_stance_partition_for_understanding]]",
        "level_0_form_identity": "CONFIRMED -- all three instantiate c_k = eps^k / k Cauchy form (math doesn't lie: psi^k/k IS literally identical to Kepler EOC at eps=|psi|)",
        "substrate_specific_eps": {
            "fibonacci": "eps = |psi| = 0.6180 (the most-irrational asymptotic-DOF rate)",
            "multinacci_3_7_1": "eps = lam2/lam1 = 0.6885 (subdominant/dominant eigvalue ratio)",
            "kepler_orbital": "eps = orbital eccentricity (substrate-dependent; Earth = 0.0167, Antikythera pin-slot = 0.054)",
        },
        "class_participation_unity": {
            "Class_L_eigenstructure": "CONFIRMED universal (every substrate has closed-form eigendecomposition)",
            "Class_K_asymptotic_DOF": "CONFIRMED universal (geometric approach to limit per [[user_stance_asymptotic_dof_sidesteps_infinity]])",
            "Class_I_cyclic_substrate": "CONFIRMED universal (Pisano periods / multinacci cyclic / mean-anomaly M)",
            "Class_N_rational_form": "CONFIRMED universal (1/k Class N participation; CF convergents form Class N ladder)",
            "Class_C_streaming": "CONFIRMED universal (Binet sum / multinacci sum / EOC k-sum)",
        },
        "partition_level_differences": {
            "cascade_depth": "Fibonacci=2-step, Multinacci=3-step (3+7+1 partition), Kepler=infinite-order expansion of 1D substrate",
            "physical_eps_range": "Kepler typically in [0.001, 0.5]; Fibonacci |psi|=0.618 is OUTSIDE that range",
            "interpretation": "Spike #30B 'in_physical_range' gate filters substrate-DISCRIMINATION; structural-IDENTITY survives the gate by being identity-level not implementation-level per [[user_stance_identity_not_implementation_discipline]]",
        },
        "fibonacci_kepler_special_relationship": (
            "Fibonacci's psi-decay IS the Kepler EOC at the slowest possible "
            "asymptotic-DOF approach rate (phi is 'most irrational'; psi=1/phi is "
            "the corresponding decay rate). Class K asymptotic-DOF spectrum has "
            "Kepler-orbital eps at one end (rapid approach: e=0.0167) and "
            "phi-related eps at the other (slowest approach: |psi|=0.618). "
            "Both ends are the SAME mathematical operation; they differ only in "
            "the rate-parameter."
        ),
        "MFO_walked_steps_pattern_honoured": (
            "Per user direction 'refinement is in the steps we walked in MFO to "
            "find unity among all the things': 7 walked steps documented in "
            "spike_41_iteration_log.ndjson. Step 4 identity-test was the load-"
            "bearing finding (math doesn't lie: identical to machine precision). "
            "Steps 5 and 6 refined the methodology (PSD-artifact ruled out; "
            "coefficient-series load-bearing). Unity appears at form-level; "
            "partition-level differences are expected and honoured."
        ),
        "candidate_new_stance_for_conductor_review": {
            "stance_name_candidate_1": "fibonacci_psi_decay_is_kepler_form_at_slowest_dof",
            "stance_name_candidate_2": "kepler_asymptotic_dof_spectrum_spans_orbital_to_phi",
            "stance_name_candidate_3": "cauchy_form_universal_c_k_equals_eps_k_over_k",
            "framing": (
                "The form c_k = eps^k / k is the universal Cauchy-form signature "
                "across closed-form recurrence substrates. The eps parameter is "
                "substrate-specific and lives on the Class N (continued-fraction "
                "convergence rate) spectrum: rapid convergence at one end (Kepler "
                "orbital), slowest at the other (Fibonacci |psi|=1/phi). All "
                "instantiate Class L (eigendecomp) o Class K (asymptotic-DOF) o "
                "Class I (cyclic substrate) o Class N (rational normalisation) o "
                "Class C (streaming sum). Five classes co-participate in every "
                "substrate; no privileged class per "
                "[[feedback_no_privileged_primitive_classes]]."
            ),
            "joins_shadow_stance_family": (
                "Joins [[user_stance_kepler_shape_universal]] / "
                "[[user_stance_cascade_lives_on_circles]] / "
                "[[user_stance_asymptotic_dof_sidesteps_infinity]] / "
                "[[user_stance_epicycle_via_gear_plus_pin]] / "
                "[[user_stance_identity_not_implementation_discipline]] as a "
                "candidate stance at the Cauchy-form identity level. Burden of "
                "proof flips: counter-claim requires a closed-form recurrence "
                "substrate that does NOT decompose to c_k = eps^k / k Cauchy form."
            ),
        },
        "fermatas_for_conductor": [
            "Confirm Substrate B interpretation: is multinacci 3+7+1 the right reading of '11D fractal projection of 3D_s + 7D_g + 1D_t'? Alternative: Class L on 11-node partitioned graph (different fingerprint).",
            "Should the candidate stance be promoted, or does it dissolve into existing stances (kepler-shape-universal + asymptotic-dof + cauchy-form) without earning its own name?",
            "Should the Spike #30B v3 strict K-test be augmented with an unbiased-fit variant (log|c_k * k|) to handle structural-identity claims separately from substrate-discrimination?",
        ],
    })

    print(f"Final synthesis appended to {SYNTHESIS}")
    print(f"Total synthesis records:")
    import subprocess
    print(subprocess.run(["wc", "-l", str(SYNTHESIS)], capture_output=True, text=True).stdout)


if __name__ == "__main__":
    main()
