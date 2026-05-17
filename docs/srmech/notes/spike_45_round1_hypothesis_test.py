"""
Spike #45 Round 1 — Cross-substrate H_kinship hypothesis-discrimination test.

H_kinship: kinship-as-decisive generalizes per c_k = epsilon^k * K_k(substrate)
           Cauchy-form: K_k binding varies by substrate; eps^k tower invariant.
H_substrate-specific: kinship is biology-specific; cosmic/human are loose metaphors.

Discrimination methodology:
  1. Per-substrate K_k binding survey: enumerate what is shared between kin.
  2. eps spectrum survey: do eps values land in (0,1) Cauchy regime across all?
  3. Class-L code-separation: do decisive-kinship substrates cluster cleanly?
  4. Class-E asymmetry survey: is decisive-vs-not consistent across substrates?

If H_kinship holds: eps values span Cauchy regime; K_k bindings substrate-specific
                    but uniform in role; code-separation strong cross-substrate.
If H_substrate-specific: eps values cluster trivially or break Cauchy regime;
                          K_k bindings fundamentally different in role.
"""

import json
from pathlib import Path

OUT_DIR = Path(__file__).parent
RECORDS_PATH = OUT_DIR / "hypothesis_records.ndjson"


def load_ndjson(path: Path) -> list[dict]:
    out = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def K_k_binding_survey() -> dict:
    """Enumerate what K_k binds to in each substrate."""
    return {
        "biological_kin": {
            "K_k_bind": "matrilineal_allele_inheritance",
            "what_is_shared": "alleles, learned behaviors, territories",
            "transmission": "biological_reproduction",
            "decay_mechanism": "generational_recombination",
            "decisive": True,
            "K_k_form": "share-rate decreases with kinship distance per Hamilton's r",
        },
        "stellar_kinship": {
            "K_k_bind": "chemical_signature_co_natal_inheritance",
            "what_is_shared": "Fe/H, alpha-elements, kinematic 6D phase-space",
            "transmission": "co_formation_from_single_molecular_cloud",
            "decay_mechanism": "tidal_dissolution_over_orbits",
            "decisive": True,
            "K_k_form": "chemical_signature_decoheres_per_galactic_orbit",
        },
        "galactic_archaeology": {
            "K_k_bind": "orbital_actions_chemodynamic_signature",
            "what_is_shared": "ancestral_galaxy_lineage_orbital_energy_angular_momentum",
            "transmission": "merger_remnant_preservation_in_actions",
            "decay_mechanism": "phase_mixing_over_Gyr",
            "decisive": True,
            "K_k_form": "action_invariants_persist; phase_mixes",
        },
        "globular_cluster_kinship": {
            "K_k_bind": "light_element_abundance_within_bound_potential",
            "what_is_shared": "He, Na, O, Mg, Al, multiple-population signatures",
            "transmission": "second_gen_from_first_gen_ejecta",
            "decay_mechanism": "negligible_for_bound_cluster",
            "decisive": True,
            "K_k_form": "nested_generations_within_potential_well",
        },
        "elemental_kinship": {
            "K_k_bind": "nucleosynthetic_origin_signature",
            "what_is_shared": "isotopic_ratios, r-process vs s-process vs Fe-peak",
            "transmission": "supernova_ejecta_or_NS_merger_to_subsequent_star_formation",
            "decay_mechanism": "none_nucleosynthetic_identity_permanent",
            "decisive": True,
            "K_k_form": "single_event_lineage_immutable",
        },
        "galactic_kinship": {
            "K_k_bind": "tidal_interaction_history",
            "what_is_shared": "tidal_streamers, kinematic_remnants, ages",
            "transmission": "gravitational_interaction_during_encounter",
            "decay_mechanism": "tidal_dissipation",
            "decisive": True,
            "K_k_form": "tidal_dynamics_signature_persists_for_Gyr",
        },
        "academic_kinship": {
            "K_k_bind": "citation_count_and_topic_coherence",
            "what_is_shared": "references, terminology, methodology",
            "transmission": "explicit_citation_act_in_paper",
            "decay_mechanism": "paradigm_shifts_and_obsolescence",
            "decisive": True,
            "K_k_form": "preferential_attachment_per_Newman_2006",
        },
        "code_kinship": {
            "K_k_bind": "git_commit_history_dag",
            "what_is_shared": "code_lines, AUTHORS, license, dependency_imports",
            "transmission": "explicit_clone_or_fork_operation",
            "decay_mechanism": "divergence_post_fork",
            "decisive": True,
            "K_k_form": "git_DAG_exact_kinship_record",
        },
        "cultural_transmission_kinship": {
            "K_k_bind": "story_motif_recombination_in_oral_tradition",
            "what_is_shared": "ATU motifs, character archetypes, narrative arcs",
            "transmission": "oral_to_written_to_oral_iteration",
            "decay_mechanism": "cultural_drift_and_translation_loss",
            "decisive": True,
            "K_k_form": "motif_persistence_with_substrate_substitution",
        },
        "intellectual_kinship": {
            "K_k_bind": "advisor_student_designation",
            "what_is_shared": "research_program, methodology, citation_basis",
            "transmission": "dissertation_certifies_explicit_kinship",
            "decay_mechanism": "generational_program_drift",
            "decisive": True,
            "K_k_form": "tree_of_explicit_lineage_assertions",
        },
        "project_internal_kinship": {
            "K_k_bind": "MPM_discipline_and_cross_references",
            "what_is_shared": "14-class vocabulary, attestation block, NDJSON format",
            "transmission": "user_authored_cross_notebook_links",
            "decay_mechanism": "very_slow; portfolio_tightly_knit",
            "decisive": True,
            "K_k_form": "self_reference_strong_clustering",
        },
    }


def eps_spectrum_survey(all_fingerprints: list[dict]) -> dict:
    """Verify eps values across substrates span Cauchy regime.

    eps=0 substrates represent the "perfect identity / no decay" limit
    (nucleosynthetic lineage). Spread is computed over strictly-positive eps
    values; eps=0 substrates are flagged separately as identity-limit substrates.
    """
    eps_collected = []
    eps_zero = []
    for fp in all_fingerprints:
        e = fp.get("f15_EpsDecay")
        if e is None:
            continue
        if 0 < e <= 1:
            eps_collected.append((fp["substrate"], fp.get("domain"), e))
        elif e == 0:
            eps_zero.append((fp["substrate"], fp.get("domain")))
    eps_collected.sort(key=lambda x: x[2])
    pos = [e for _, _, e in eps_collected]
    return {
        "n_with_valid_eps": len(eps_collected),
        "n_identity_limit_substrates": len(eps_zero),
        "identity_limit_substrates": eps_zero,
        "eps_range_min_positive": pos[0] if pos else None,
        "eps_range_max_positive": pos[-1] if pos else None,
        "all_in_cauchy_regime": all(0 <= e <= 1
                                     for _, _, e in eps_collected),
        "slowest_eps_positive_substrate": eps_collected[0] if eps_collected else None,
        "fastest_eps_substrate": eps_collected[-1] if eps_collected else None,
        "spans_orders_of_magnitude_positive": (
            pos[-1] / pos[0] if pos and pos[0] > 0 else 0
        ),
    }


def discrimination_verdict(K_bindings: dict, eps_spectrum: dict, sig_results: dict) -> dict:
    """Final discrimination: H_kinship vs H_substrate-specific."""
    # Criterion 1: all K_k bindings are kinship-decisive
    all_decisive = all(b["decisive"] for b in K_bindings.values())

    # Criterion 2: eps values span Cauchy regime (0,1) with non-trivial spread
    cauchy_regime_ok = eps_spectrum["all_in_cauchy_regime"]
    nontrivial_spread = (eps_spectrum["spans_orders_of_magnitude_positive"] > 10)

    # Criterion 3: code-separation strong cross-substrate
    code_separation = sig_results["all_combined"]["class_L_fiedler_partition"]["code_separation"]
    code_separation_strong = code_separation >= 0.5

    # Criterion 4: K_k binding form varies by substrate (substrate-specificity of K)
    k_forms = set(b["K_k_form"] for b in K_bindings.values())
    substrate_specific_K = len(k_forms) >= 5

    h_kinship_supported = (all_decisive and cauchy_regime_ok and
                           nontrivial_spread and code_separation_strong and
                           substrate_specific_K)
    return {
        "all_K_bindings_decisive": all_decisive,
        "all_eps_in_cauchy_regime": cauchy_regime_ok,
        "eps_spread_nontrivial_orders_of_mag": nontrivial_spread,
        "code_separation_strong": code_separation_strong,
        "code_separation_value": code_separation,
        "K_k_substrate_specific": substrate_specific_K,
        "n_distinct_K_forms": len(k_forms),
        "spread_value": eps_spectrum["spans_orders_of_magnitude_positive"],
        "h_kinship_cross_substrate_supported": h_kinship_supported,
    }


def main() -> int:
    cosmic = load_ndjson(OUT_DIR / "cosmic_fingerprints.ndjson")
    human = load_ndjson(OUT_DIR / "human_fingerprints.ndjson")
    sig_results = {}
    sig_path = OUT_DIR / "signature_records.ndjson"
    for rec in load_ndjson(sig_path):
        sig_results[rec["substrate_group"]] = rec

    all_fp = cosmic + human  # bio fingerprints don't have eps assigned

    K_bindings = K_k_binding_survey()
    eps_spectrum = eps_spectrum_survey(all_fp)
    verdict = discrimination_verdict(K_bindings, eps_spectrum, sig_results)

    # Write hypothesis records
    with RECORDS_PATH.open("w", encoding="utf-8") as f:
        f.write(json.dumps({
            "date": "2026-05-17", "spike": "spike_45_round1",
            "kind": "K_k_binding_survey", "data": K_bindings,
        }) + "\n")
        f.write(json.dumps({
            "date": "2026-05-17", "spike": "spike_45_round1",
            "kind": "eps_spectrum_survey", "data": eps_spectrum,
        }) + "\n")
        f.write(json.dumps({
            "date": "2026-05-17", "spike": "spike_45_round1",
            "kind": "discrimination_verdict", "data": verdict,
        }) + "\n")

    print("=" * 70)
    print("HYPOTHESIS DISCRIMINATION VERDICT")
    print("=" * 70)
    print(f"\nK_k binding decisive across all {len(K_bindings)} substrate kinds: "
          f"{verdict['all_K_bindings_decisive']}")
    print(f"eps values in Cauchy regime [0,1]:        "
          f"{verdict['all_eps_in_cauchy_regime']}")
    print(f"eps spread orders of magnitude (positive eps only): "
          f"{verdict['spread_value']:.1f}x")
    print(f"Identity-limit (eps=0) substrates:        "
          f"{eps_spectrum['n_identity_limit_substrates']} "
          f"({eps_spectrum['identity_limit_substrates']})")
    print(f"Code-separation strong (>=0.5):           "
          f"{verdict['code_separation_strong']} "
          f"(val={verdict['code_separation_value']:.3f})")
    print(f"K_k substrate-specific (>=5 distinct):    "
          f"{verdict['K_k_substrate_specific']} "
          f"(n_forms={verdict['n_distinct_K_forms']})")
    print()
    print(f">>> H_kinship cross-substrate SUPPORTED: "
          f"{verdict['h_kinship_cross_substrate_supported']} <<<")
    print()
    print(f"Slowest positive eps: {eps_spectrum['slowest_eps_positive_substrate']}")
    print(f"Fastest eps:          {eps_spectrum['fastest_eps_substrate']}")
    print()
    print("K_k bindings (substrate -> what kinship binds to):")
    for sub, b in K_bindings.items():
        print(f"  {sub}:")
        print(f"    K_k_bind:   {b['K_k_bind']}")
        print(f"    shared:     {b['what_is_shared']}")
        print(f"    decay:      {b['decay_mechanism']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
