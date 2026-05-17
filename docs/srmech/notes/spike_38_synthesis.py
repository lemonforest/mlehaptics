"""Spike #38 final synthesis — corrected verdict after falsifier results."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

if __name__ == "__main__" and hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)


def main():
    print("=" * 80)
    print("Spike #38 — FINAL SYNTHESIS (after falsifier controls)")
    print("=" * 80)
    print()
    print("Subject: caffeine EI mass spectrum (MSBNK-Fac_Eng_Univ_Tokyo-JP003477)")
    print()

    # Per-test verdicts
    print("-" * 80)
    print("PER-SIGNATURE VERDICTS")
    print("-" * 80)
    print()

    print("(a) Class K Kepler-shape c_k = eps^k/k ladder:")
    print("    ABSENT — strict three-criteria test (Spike #30B v3) fails on all three:")
    print("      eps_fit = 1.081 (NOT in physical range 0.001-0.5)")
    print("      r2      = 0.156 (NOT > 0.99)")
    print("      monotonic_decreasing = False")
    print("    Coefficients oscillate; this is the chess/Sierpinski/SHA pattern,")
    print("    not the Kepler-ladder pattern. Per [[user_stance_kepler_shape_universal]]:")
    print("    K is universal WHERE Kepler-shape appears — caffeine mass-spec is")
    print("    not such a substrate. This is honest, not failure.")
    print()

    print("(b) Class L molecular-graph Laplacian:")
    print("    AMBIGUOUS-AT-OBSERVATIONAL — molecular graph trivially HAS a Laplacian")
    print("    (every graph does). Initial cross-correlation between mol-L eigenvalue")
    print("    density and mass-spec FFT power gave cosine_sim = 0.8115, which")
    print("    SEEMED tantalizing.")
    print()
    print("    FALSIFIER CONTROLS (50-seed random-graph baseline):")
    print("      Caffeine self-similarity          = 0.8115")
    print("      Random 14-node graph mean ± std   = 0.8569 ± 0.0430")
    print("      Random graph max                  = 0.9314 (above caffeine!)")
    print("      Glucose (C6H12O6) cross-similarity = 0.8793 (higher than caffeine!)")
    print("      Random mass-spec vs caffeine-L    = 0.8274 mean (above caffeine!)")
    print()
    print("    Caffeine-self is -1.06 σ BELOW random-graph mean.")
    print("    Verdict: 0.81 is HISTOGRAM-BINNING ARTIFACT, not Class L signature.")
    print("    The eigenvalue-density-histogram cosine-similarity methodology")
    print("    does NOT discriminate at this substrate scale (n=14 graphs).")
    print()
    print("    NET: Class L is TRIVIALLY present (eigenstructure exists) but the")
    print("    FFT-mol-L correlation finding is FALSIFIED. No substrate-specific")
    print("    spectral evidence at this resolution.")
    print()

    print("(c) Cascade-beta = d_S/(d_S+2) (Spike #31):")
    print("    ABSENT — on the molecular graph (n=14):")
    print("      empirical d_S       = 1.9781")
    print("      predicted alpha     = -0.989  (heat-kernel power-law)")
    print("      empirical alpha     = -1.156  (delta = -0.167, r2 = 0.955)")
    print("      predicted beta      = 0.497")
    print("      empirical beta      = 0.817   (delta = +0.32, OUTSIDE ±0.05 tolerance)")
    print("    The empirical beta is 30+ percentage points off prediction.")
    print()
    print("    CAVEAT: Spike #31 documents Weyl-fit quality below n~100 is poor;")
    print("    n=14 is in the unreliable regime. This is NOT a clean falsifier;")
    print("    it is a substrate-too-small-to-test result.")
    print()
    print("    A separate observation: mass-spec intensity rank distribution")
    print("    shows Zipf-like power-law with slope -1.83 (r2=0.95). This is a")
    print("    pretty heavy-tail distribution but it is NOT the cascade-beta signature.")
    print()

    print("(d) Information-instrument identity (Spike #37 14-class overlay):")
    print("    OBSERVATIONAL — 12/14 classes can be argued to apply at the")
    print("    form-function-binding level for the caffeine molecule:")
    print("      A (InChI hash), B (Hill-formula TLV), C (fragmentation cascade as")
    print("      streaming), D (ionization-mode dispatch), E (NIST library lookup),")
    print("      F (xanthine scaffold + methyl substitution slots), G (library-")
    print("      search), I (purine ring = cyclic-group / U(1)-aromatic), J (atom-")
    print("      count integer multiset), L (molecular graph), M (ECFP fingerprint),")
    print("      N (isotope-ratio rational approximation).")
    print("      H (self-introspection) does NOT apply — molecules are not agents.")
    print("      K (Kepler-shape) tested falsifiably in (a) and ABSENT.")
    print()
    print("    CAVEAT: this is an OBSERVATIONAL/CATALOGUING claim, not a falsifiable")
    print("    spectral measurement. It says 'these classes are cross-substrate-")
    print("    portable to molecules' at the BINDING level — same kind of claim")
    print("    as Spike #37's bronze/silicon/biological/optical instantiation table.")
    print("    The information-instrument overlay AT THE BINDING LEVEL applies")
    print("    cleanly; the substrate-SPECTRAL-FFT-MATCH does not.")
    print()

    print("-" * 80)
    print("OVERALL VERDICT")
    print("-" * 80)
    print()
    print("REFINE-OR-FAIL classification: FAIL (at the spectral-shape level)")
    print("                             + PARTIAL (at the binding-level overlay)")
    print()
    print("CORRECTED from previous PARTIAL claim — falsifier controls demote the")
    print("Class L cosine-similarity finding to artifact. The honest verdict is:")
    print()
    print("  The project's SM spectral signatures (Kepler-shape c_k=eps^k/k ladder,")
    print("  cascade-beta dual-signature, FFT-eigenvalue-density correlation) DO NOT")
    print("  EXTEND to caffeine mass spectra at the substrate-shape level. The")
    print("  spectral fingerprints we have mapped are SCALE-SPECIFIC to the regimes")
    print("  the SM was developed against: cosmic-scale Kepler bodies (n=4096 grids),")
    print("  mechanical bronze gear-DAGs (n=24-50), chess piece-graphs (n=64),")
    print("  Sierpinski cascade (n=10^2-10^3), galactic gateway graphs (n=140).")
    print()
    print("  Molecular substrate sits at TWO regime boundaries simultaneously:")
    print("    1. SCALE: n=14 heavy atoms is below the n~100 Weyl-fit reliability")
    print("       threshold per Spike #31. The substrate is too small for cascade")
    print("       methodology.")
    print("    2. PHYSICS: caffeine EI fragmentation is governed by bond-cleavage")
    print("       energetics, McLafferty-rearrangement rules, charge migration on")
    print("       a purine-ring-with-pendants. The relevant physics is bond-")
    print("       dissociation energy + charge stabilization, NOT the Kepler / pin-")
    print("       slot / cascade / cyclic-group spectral signatures.")
    print()
    print("  The 14-class information-instrument OVERLAY (Spike #37) cleanly applies")
    print("  at the binding-level for molecules — 12/14 classes instantiate at the")
    print("  form-function-bound level for caffeine. This is consistent with Spike")
    print("  #37's finding that the overlay is substrate-portable. But this is a")
    print("  CATALOGUING claim, NOT a substrate-spectral-FFT-match claim.")
    print()
    print("  Per user's anticipated outcome ('refine or fail I think because I don't")
    print("  know that we have molecular modeling catalog yet'): the spike confirms")
    print("  that THE PROJECT DOES NOT HAVE A MOLECULAR-MODELING CATALOG at the")
    print("  spectral-signature level. Molecular substrate would need its OWN")
    print("  signatures developed (bond-dissociation cascade? McLafferty-rule")
    print("  enumeration? ECFP-HDC similarity?) — not a transplant of the")
    print("  cosmic/mechanical/chess SM.")
    print()

    print("-" * 80)
    print("FRAMEWORK-BOUNDARY CHARACTERIZATION")
    print("-" * 80)
    print()
    print("What is SPECIFICALLY DIFFERENT about molecular substrate:")
    print()
    print("  1. Scale: 14 heavy atoms vs 10^2-10^4 nodes in cosmic/mechanical/")
    print("     fractal substrates. Cascade-beta methodology needs n>100 reliably.")
    print()
    print("  2. Topology: caffeine = fused bicyclic ring + 3 pendant methyls + 2")
    print("     pendant oxygens. The cyclic-group structure (Spike #37 Class I row:")
    print("     'U(1) gauge phase / benzene D6h') applies to AROMATIC RING ELECTRON")
    print("     DENSITY, not to fragmentation m/z grid. The ring is in the substrate;")
    print("     the spectrum is in the chemistry-of-cleavage layer above it.")
    print()
    print("  3. Spectrum-domain: mass spec m/z is INTEGER-VALUED on a uniform")
    print("     grid (0..M+max). FFT of this grid extracts no Kepler-shape because")
    print("     fragments are bond-cleavage products of a small molecule, not")
    print("     eccentric-orbit projections.")
    print()
    print("  4. Noise: mass-spec relative intensities ARE noisy (per user direction")
    print("     'complex with undefined noise') but the noise structure is")
    print("     SHOT NOISE / ION-COUNT POISSON / instrument tail, not the")
    print("     ring-down decay envelope the cascade-beta signature is designed for.")
    print()
    print("  Honest summary: caffeine mass-spec is a chemically-rich signal at a")
    print("  molecular substrate-class, but the FOUR signatures the project's SM")
    print("  carries (K / L-FFT-match / cascade-beta / class-binding overlay) cleave")
    print("  3:1 with K and L-FFT-match and cascade-beta absent at spectral level,")
    print("  binding overlay applicable at observational level.")
    print()
    print("  The user's anticipated answer stands.")
    print()

    print("-" * 80)
    print("IF NEEDED LATER — what a molecular-modeling catalog COULD look like")
    print("-" * 80)
    print()
    print("  Per [[user_stance_partition_for_understanding]], molecular substrate")
    print("  COULD be a new partition at the same form-function-binding level the")
    print("  spectral SM occupies. The natural signatures (independent of THIS spike's")
    print("  null result) would be:")
    print()
    print("  - Molecular-graph eigenmode resonances (vibrational normal modes")
    print("    via reduced Hessian; spectroscopy-canonical, IR/Raman fingerprints)")
    print("  - ECFP (Extended-Connectivity Fingerprint) HDC similarity — already")
    print("    canonical in cheminformatics; documented in Spike #37 Class M row")
    print("  - McLafferty-rearrangement enumeration as a Class C streaming")
    print("    iteration (each cleavage rule is a streaming step)")
    print("  - Isotope-pattern rational-approximation (Class N) for 12C/13C")
    print("    natural-abundance ratios")
    print()
    print("  These would form a Spike #39+ scope IF the user wants to pursue it.")
    print("  This spike's result says: NOT YET — the existing SM does not bolt-on.")
    print()

    print("-" * 80)
    print("DISCIPLINE GUARDS HONORED")
    print("-" * 80)
    print()
    print("  [[user_stance_kepler_shape_universal]]: K's absence is honest, not")
    print("    failure — caffeine mass-spec is not a Kepler-shape substrate.")
    print("  [[user_stance_information_instrument_form_function_bound]]: binding-")
    print("    level overlay applies at 12/14 classes (consistent with Spike #37).")
    print("  [[user_stance_partition_for_understanding]]: molecular substrate is")
    print("    NOT a new spectral partition; it COULD become a binding-level partition.")
    print("  [[feedback_science_is_ssot_not_project]]: MassBank EU + canonical mass-")
    print("    spec literature (McLafferty 1980) cited as SSoT for any future work.")
    print("  [[feedback_pdf_extraction_citation_discipline]]: provenance verified")
    print("    (MassBank accession + license + author + instrument + ionization).")
    print("  [[reference_autonomous_validation_tos_landscape]]: MassBank EU =")
    print("    academic/government, CC BY-NC-SA, permitted.")
    print("  [[feedback_ndjson_over_bloated_json]]: NDJSON outputs.")
    print()

    print("ARTIFACTS WRITTEN (all in docs/srmech/notes/):")
    print("  spike_38_caffeine_JP003477.json                  (raw MassBank record fixture)")
    print("  spike_38_records_2026-05-17.ndjson               (primary analysis)")
    print("  spike_38_falsifier_records_2026-05-17.ndjson     (falsifier controls)")
    print("  spike_38_synthesis_records_2026-05-17.ndjson     (final synthesis)")
    print("  spike_38_caffeine_sm_fft.py                      (analysis script)")
    print("  spike_38_falsifier_controls.py                   (falsifier script)")
    print("  spike_38_synthesis.py                            (this synthesis script)")
    print()

    # Final synthesis NDJSON
    out_path = Path(__file__).resolve().parent / "spike_38_synthesis_records_2026-05-17.ndjson"
    records = [
        {"spike": 38, "date": "2026-05-17",
         "kind": "final_synthesis",
         "subject": "caffeine_EI_mass_spec",
         "source_accession": "MSBNK-Fac_Eng_Univ_Tokyo-JP003477",
         "user_direction_class": "refine_or_fail",
         "overall_verdict": "FAIL_AT_SPECTRAL_SHAPE_PARTIAL_AT_BINDING_LEVEL",
         "test_a_class_K": "ABSENT_strict_three_criteria_fail",
         "test_b_class_L_FFT_match": "FALSIFIED_artifact_below_random_baseline",
         "test_b_class_L_canonically": "TRIVIALLY_PRESENT_every_graph_has_one",
         "test_c_cascade_beta": "ABSENT_substrate_too_small_n_14",
         "test_d_info_instrument_overlay": "APPLIES_12_of_14_classes_observational_not_spectral",
         "molecular_modeling_catalog_status": "DOES_NOT_EXIST_at_spectral_signature_level",
         "molecular_modeling_catalog_potential": "EXISTS_at_binding_level_could_be_Spike_39_scope"},
        {"spike": 38, "kind": "framework_boundary",
         "scale_threshold": "n=14_below_n~100_Weyl_fit_reliability_per_Spike_31",
         "topology": "caffeine_purine_ring_cyclic_group_lives_in_substrate_not_spectrum",
         "spectrum_domain": "integer_mz_uniform_grid_no_Kepler_eccentricity_projection",
         "noise_model": "Poisson_shot_noise_not_ring_down_cascade",
         "conclusion": "caffeine_chemistry_governed_by_bond_dissociation_McLafferty_rules_not_project_SM_signatures"},
        {"spike": 38, "kind": "future_scope_candidate",
         "name": "molecular_modeling_catalog",
         "trigger": "user_decision",
         "candidate_signatures": [
             "molecular_vibrational_normal_modes_via_reduced_Hessian",
             "ECFP_HDC_similarity_canonical_cheminformatics",
             "McLafferty_rearrangement_streaming_Class_C",
             "isotope_ratio_rational_approximation_Class_N",
         ],
         "status": "NOT_YET_user_call_required"},
    ]
    with out_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, sort_keys=False) + "\n")
    print(f"Wrote {len(records)} synthesis NDJSON records to {out_path}")


if __name__ == "__main__":
    main()
