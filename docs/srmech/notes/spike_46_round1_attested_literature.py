"""Spike #46 Round 1 — Attested literature anchoring.

Compile attested references from open-access sources for each substrate.
Per [[feedback_pdf_extraction_citation_discipline]] and
[[reference_autonomous_validation_tos_landscape]]:
- Only open-access sources verified inline
- Canonical paywalled refs cited but flagged
- All authors+title+year+venue+DOI/arXiv-ID recorded with provenance

For Round 1 this script COMPILES the reference list with provenance fields.
No autonomous PDF extraction performed; user can authorise round 2
to autonomous-fetch open-access PMC / arXiv PDFs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone


@dataclass
class Reference:
    citation_key: str
    authors: str
    year: int
    title: str
    venue: str
    doi: str | None
    arxiv_id: str | None
    pmid: str | None
    pmc_id: str | None
    license_status: str  # 'open_access' | 'paywall_canonical' | 'preprint_arxiv' | 'pmc_oa' | 'textbook_canonical'
    relates_to_substrates: list[str]
    relates_to_falsifiers: list[str]
    summary: str
    notes: str = ""


REFS: list[Reference] = [
    # ============= QUANTUM MEASUREMENT =============
    Reference(
        citation_key="vonNeumann_1932_mathematical_foundations",
        authors="von Neumann, J.",
        year=1932,
        title="Mathematische Grundlagen der Quantenmechanik",
        venue="Springer (1932); Princeton UP (1955) English",
        doi=None,
        arxiv_id=None,
        pmid=None,
        pmc_id=None,
        license_status="textbook_canonical",
        relates_to_substrates=["quantum_measurement_eigenstate_selection"],
        relates_to_falsifiers=["F1_signed_asymptote_present"],
        summary=(
            "Canonical formulation of quantum measurement axiom (projection postulate). "
            "Establishes the structural fact: superposition → measurement → single eigenstate. "
            "Selection happens; the 'why this one' is the measurement problem."
        ),
        notes="Foundational; no live URL needed.",
    ),
    Reference(
        citation_key="Aspect_1982_PRL_Bell_test",
        authors="Aspect, A.; Grangier, P.; Roger, G.",
        year=1982,
        title="Experimental Realization of Einstein-Podolsky-Rosen-Bohm Gedankenexperiment",
        venue="Physical Review Letters 49:91",
        doi="10.1103/PhysRevLett.49.91",
        arxiv_id=None,
        pmid=None,
        pmc_id=None,
        license_status="paywall_canonical",
        relates_to_substrates=["quantum_measurement_eigenstate_selection"],
        relates_to_falsifiers=["F1_signed_asymptote_present", "F3_substrate_decisions_are_selections"],
        summary=(
            "Bell-test confirms quantum non-locality; rules out local hidden variables. "
            "Establishes structural fact: outcome selection is genuine, not pre-determined."
        ),
        notes="APS paywall; abstract on aps.org.",
    ),
    Reference(
        citation_key="Wheeler_1978_delayed_choice",
        authors="Wheeler, J. A.",
        year=1978,
        title="The 'Past' and the 'Delayed-Choice' Double-Slit Experiment",
        venue="In: Mathematical Foundations of Quantum Theory (Marlow, ed.), Academic Press",
        doi=None,
        arxiv_id=None,
        pmid=None,
        pmc_id=None,
        license_status="textbook_canonical",
        relates_to_substrates=["quantum_measurement_eigenstate_selection"],
        relates_to_falsifiers=["F4_chosen_vs_determined"],
        summary=(
            "Delayed-choice: the 'selection' happens AFTER the trajectory is fixed. "
            "Forces reframing of when selection occurs. Relevant to F4 (chosen vs determined)."
        ),
    ),

    # ============= CHEMICAL KINETICS =============
    Reference(
        citation_key="LeChatelier_1884_equilibrium",
        authors="Le Chatelier, H.",
        year=1884,
        title="Sur un énoncé général des lois des équilibres chimiques",
        venue="Comptes rendus hebdomadaires des séances de l'Académie des sciences 99:786",
        doi=None,
        arxiv_id=None,
        pmid=None,
        pmc_id=None,
        license_status="open_access",  # ~140yr public domain
        relates_to_substrates=["chemical_kinetics_le_chatelier"],
        relates_to_falsifiers=["F1_signed_asymptote_present", "F3_substrate_decisions_are_selections"],
        summary=(
            "Canonical statement of equilibrium shift under perturbation. "
            "Direction of system response is determined by sign of perturbation; structural "
            "asymptote-selection at molecular scale, no nervous system required."
        ),
        notes="Public domain (>140y); BnF Gallica likely has scans.",
    ),
    Reference(
        citation_key="Atkins_dePaula_PhysicalChemistry_textbook",
        authors="Atkins, P.; de Paula, J.",
        year=2018,
        title="Physical Chemistry (11th ed.)",
        venue="Oxford University Press",
        doi=None,
        arxiv_id=None,
        pmid=None,
        pmc_id=None,
        license_status="textbook_canonical",
        relates_to_substrates=["chemical_kinetics_le_chatelier"],
        relates_to_falsifiers=["F3_substrate_decisions_are_selections"],
        summary=(
            "Modern canonical textbook treatment of equilibrium thermodynamics and kinetics. "
            "Ch. 6 (chemical equilibrium) + Ch. 21 (reaction dynamics)."
        ),
    ),

    # ============= BACTERIAL CHEMOTAXIS =============
    Reference(
        citation_key="Berg_Brown_1972_Nature_chemotaxis",
        authors="Berg, H. C.; Brown, D. A.",
        year=1972,
        title="Chemotaxis in Escherichia coli analysed by three-dimensional tracking",
        venue="Nature 239:500",
        doi="10.1038/239500a0",
        arxiv_id=None,
        pmid="4563019",
        pmc_id=None,
        license_status="paywall_canonical",
        relates_to_substrates=["bacterial_chemotaxis_run_tumble"],
        relates_to_falsifiers=[
            "F1_signed_asymptote_present", "F2_consciousness_without_asymptote",
            "F3_substrate_decisions_are_selections"
        ],
        summary=(
            "Canonical observation that E. coli swimming = run/tumble episodes; tumble frequency "
            "modulated by signed-temporal-gradient of attractant. Direction-selection without "
            "nervous system. Critical for F2: bacterial 'selection' substrate has no conventional "
            "consciousness — but DOES have asymptotic-DOF direction-selection."
        ),
        notes="Nature paywall; abstract open.",
    ),
    Reference(
        citation_key="Macnab_Koshland_1972_PNAS_temporal_gradient",
        authors="Macnab, R. M.; Koshland, D. E.",
        year=1972,
        title="The gradient-sensing mechanism in bacterial chemotaxis",
        venue="PNAS 69:2509",
        doi="10.1073/pnas.69.9.2509",
        arxiv_id=None,
        pmid="4560688",
        pmc_id="PMC426988",
        license_status="pmc_oa",
        relates_to_substrates=["bacterial_chemotaxis_run_tumble"],
        relates_to_falsifiers=["F1_signed_asymptote_present"],
        summary=(
            "Demonstrates bacteria sense TEMPORAL gradients (signed Δconcentration / Δt), "
            "not instantaneous gradients. Establishes the 'signed-ε rate parameter' instance "
            "explicitly for this substrate. PMC open-access."
        ),
        notes="PMC OA — can be autonomously fetched in round 2 per ToS.",
    ),
    Reference(
        citation_key="Sourjik_Wingreen_2012_review",
        authors="Sourjik, V.; Wingreen, N. S.",
        year=2012,
        title="Responding to chemical gradients: bacterial chemotaxis",
        venue="Current Opinion in Cell Biology 24:262",
        doi="10.1016/j.ceb.2011.11.008",
        arxiv_id=None,
        pmid="22169400",
        pmc_id="PMC3320702",
        license_status="pmc_oa",
        relates_to_substrates=["bacterial_chemotaxis_run_tumble"],
        relates_to_falsifiers=["F3_substrate_decisions_are_selections"],
        summary="Modern review of chemotaxis mechanism; receptor clustering, CheY-P, motor bias.",
    ),

    # ============= PLANT TROPISM =============
    Reference(
        citation_key="Darwin_Darwin_1880_movement_in_plants",
        authors="Darwin, C.; Darwin, F.",
        year=1880,
        title="The Power of Movement in Plants",
        venue="John Murray, London",
        doi=None,
        arxiv_id=None,
        pmid=None,
        pmc_id=None,
        license_status="open_access",  # public domain
        relates_to_substrates=["plant_tropism_phototropism_gravitropism"],
        relates_to_falsifiers=[
            "F1_signed_asymptote_present", "F2_consciousness_without_asymptote",
            "F3_substrate_decisions_are_selections"
        ],
        summary=(
            "Canonical observational record of plant tropisms (phototropism, gravitropism, "
            "circumnutation). Pre-biochemistry; observed direction-selection without nervous system. "
            "Darwin's framing 'movement' (motion-toward-end) is structurally the user's "
            "direction-selection at substrate level."
        ),
        notes="Public domain; Internet Archive scans available.",
    ),
    Reference(
        citation_key="Whippo_Hangarter_2006_Plant_Cell",
        authors="Whippo, C. W.; Hangarter, R. P.",
        year=2006,
        title="Phototropism: bending towards enlightenment",
        venue="The Plant Cell 18:1110",
        doi="10.1105/tpc.105.039669",
        arxiv_id=None,
        pmid="16670442",
        pmc_id="PMC1456870",
        license_status="pmc_oa",
        relates_to_substrates=["plant_tropism_phototropism_gravitropism"],
        relates_to_falsifiers=["F3_substrate_decisions_are_selections"],
        summary=(
            "Modern review of phototropism mechanism: PHOT1/PHOT2 photoreceptors, "
            "auxin polar transport, PIN protein localization. Substrate-binding (K_k) for "
            "plant tropism is auxin gradient + PIN localization."
        ),
        notes="PMC OA.",
    ),

    # ============= SHRIMP / FISH MAUTHNER STARTLE =============
    Reference(
        citation_key="Faber_Korn_1978_Mauthner_book",
        authors="Faber, D. S.; Korn, H. (eds.)",
        year=1978,
        title="Neurobiology of the Mauthner Cell",
        venue="Raven Press, New York",
        doi=None,
        arxiv_id=None,
        pmid=None,
        pmc_id=None,
        license_status="textbook_canonical",
        relates_to_substrates=["shrimp_tail_flip_mauthner_cell"],
        relates_to_falsifiers=[
            "F1_signed_asymptote_present", "F4_chosen_vs_determined",
            "F5_shrimp_choice_vs_pure_reflex"
        ],
        summary=(
            "Canonical monograph on Mauthner cell physiology. Bilateral pair of giant neurons, "
            "reciprocal inhibition, first-fire-wins selection for left-vs-right escape. "
            "Critical for F5: the conventional framing is 'reflex' (not deliberative). "
            "User's structural reframe: the math is identical to direction-selection at "
            "higher substrates."
        ),
    ),
    Reference(
        citation_key="Edwards_Heitler_Krasne_1999_TINS_review",
        authors="Edwards, D. H.; Heitler, W. J.; Krasne, F. B.",
        year=1999,
        title="Fifty years of a command neuron: the neurobiology of escape behavior in the crayfish",
        venue="Trends in Neurosciences 22:153",
        doi="10.1016/S0166-2236(98)01340-X",
        arxiv_id=None,
        pmid="10203853",
        pmc_id=None,
        license_status="paywall_canonical",
        relates_to_substrates=["shrimp_tail_flip_mauthner_cell"],
        relates_to_falsifiers=["F5_shrimp_choice_vs_pure_reflex"],
        summary=(
            "Half-century review of crayfish escape circuit. Establishes that even 'pure-reflex' "
            "escape is modulated by context, satiety, recent-history — i.e. NOT purely fixed-action-pattern. "
            "Relevant to F5: selection-on-asymptote argument is strengthened by demonstrated modulability."
        ),
        notes="Elsevier paywall.",
    ),
    Reference(
        citation_key="Krasne_Wine_1975_JEB_crayfish",
        authors="Krasne, F. B.; Wine, J. J.",
        year=1975,
        title="Extrinsic modulation of crayfish escape behaviour",
        venue="Journal of Experimental Biology 63:433",
        doi=None,
        arxiv_id=None,
        pmid="1159369",
        pmc_id=None,
        license_status="open_access",  # JEB open after embargo
        relates_to_substrates=["shrimp_tail_flip_mauthner_cell"],
        relates_to_falsifiers=["F5_shrimp_choice_vs_pure_reflex"],
        summary=(
            "Demonstrates that crayfish tail-flip is gated/modulated by descending pathways — "
            "NOT a purely automatic reflex. Even at this 'simple' substrate, the selection "
            "incorporates context. Strengthens F5 reframing."
        ),
        notes="JEB OA after embargo; can be PMC mirror.",
    ),

    # ============= SINGLE NEURON =============
    Reference(
        citation_key="HodgkinHuxley_1952_JP_action_potential",
        authors="Hodgkin, A. L.; Huxley, A. F.",
        year=1952,
        title="A quantitative description of membrane current and its application to conduction and excitation in nerve",
        venue="Journal of Physiology 117:500",
        doi="10.1113/jphysiol.1952.sp004764",
        arxiv_id=None,
        pmid="12991237",
        pmc_id="PMC1392413",
        license_status="pmc_oa",
        relates_to_substrates=["neuron_action_potential_threshold"],
        relates_to_falsifiers=["F1_signed_asymptote_present", "F3_substrate_decisions_are_selections"],
        summary=(
            "Canonical action-potential formalism. Gating variables m, h, n; voltage-gated channels; "
            "threshold non-linearity. Establishes the single-neuron substrate as binary-direction "
            "selector on signed (V_m - V_thresh). PMC OA available."
        ),
        notes="PMC OA — full PDF autonomously fetchable in round 2.",
    ),

    # ============= HUMAN DELIBERATION =============
    Reference(
        citation_key="Libet_1983_Brain_readiness_potential",
        authors="Libet, B.; Gleason, C. A.; Wright, E. W.; Pearl, D. K.",
        year=1983,
        title="Time of conscious intention to act in relation to onset of cerebral activity (readiness-potential)",
        venue="Brain 106:623",
        doi="10.1093/brain/106.3.623",
        arxiv_id=None,
        pmid="6640273",
        pmc_id=None,
        license_status="paywall_canonical",
        relates_to_substrates=["human_conscious_deliberation_libet_paradigm"],
        relates_to_falsifiers=[
            "F2_consciousness_without_asymptote", "F4_chosen_vs_determined",
            "F5_shrimp_choice_vs_pure_reflex"
        ],
        summary=(
            "Canonical demonstration that readiness potential precedes conscious awareness of "
            "intent to act by ~350ms. Establishes that the conventional 'conscious choice' is "
            "downstream of pre-conscious neural commitment. Hard test for F4: does the user's "
            "claim survive Libet? Reading: YES — structural reframe makes Libet intelligible."
        ),
        notes="Oxford UP paywall; widely cited; abstract open.",
    ),
    Reference(
        citation_key="Soon_2008_NatNeurosci_unconscious_decisions",
        authors="Soon, C. S.; Brass, M.; Heinze, H.-J.; Haynes, J.-D.",
        year=2008,
        title="Unconscious determinants of free decisions in the human brain",
        venue="Nature Neuroscience 11:543",
        doi="10.1038/nn.2112",
        arxiv_id=None,
        pmid="18408715",
        pmc_id=None,
        license_status="paywall_canonical",
        relates_to_substrates=["human_conscious_deliberation_libet_paradigm"],
        relates_to_falsifiers=["F2_consciousness_without_asymptote", "F4_chosen_vs_determined"],
        summary=(
            "fMRI extends Libet: pre-conscious neural activity predicts left/right choice up "
            "to 10 seconds before subject reports awareness. Structural direction-selection "
            "happens at substrate level WELL before introspective conscious frame registers it. "
            "Strengthens F4 reframing: 'chosen' and 'physics-determined' resolve at different levels."
        ),
        notes="Nature paywall.",
    ),
    Reference(
        citation_key="Haggard_2008_NatRevNeurosci_volition",
        authors="Haggard, P.",
        year=2008,
        title="Human volition: towards a neuroscience of will",
        venue="Nature Reviews Neuroscience 9:934",
        doi="10.1038/nrn2497",
        arxiv_id=None,
        pmid="19020512",
        pmc_id=None,
        license_status="paywall_canonical",
        relates_to_substrates=["human_conscious_deliberation_libet_paradigm"],
        relates_to_falsifiers=["F2_consciousness_without_asymptote", "F4_chosen_vs_determined"],
        summary=(
            "Comprehensive review of human-volition neuroscience post-Libet. Discusses what-when-whether "
            "components of action; ties to motor preparation, SMA, prefrontal veto. Substrate-level "
            "components of conventional 'conscious decision'."
        ),
        notes="Nature paywall.",
    ),
    Reference(
        citation_key="Wegner_Wheatley_1999_illusion",
        authors="Wegner, D. M.; Wheatley, T.",
        year=1999,
        title="Apparent mental causation: sources of the experience of will",
        venue="American Psychologist 54:480",
        doi="10.1037/0003-066X.54.7.480",
        arxiv_id=None,
        pmid="10424155",
        pmc_id=None,
        license_status="paywall_canonical",
        relates_to_substrates=["human_conscious_deliberation_libet_paradigm"],
        relates_to_falsifiers=["F4_chosen_vs_determined"],
        summary=(
            "Argues experience of conscious will is a post-hoc interpretive narrative attached "
            "to actions already initiated at substrate level. Frames conventional consciousness "
            "as illusory commentary on substrate-level direction-selection. Directly supports "
            "user's reframing partition (conventional consciousness vs structural consciousness)."
        ),
        notes="APA paywall.",
    ),
    Reference(
        citation_key="Schultze_Kraft_2016_PNAS_veto",
        authors="Schultze-Kraft, M.; Birman, D.; Rusconi, M.; Allefeld, C.; Görgen, K.; Dähne, S.; Blankertz, B.; Haynes, J.-D.",
        year=2016,
        title="The point of no return in vetoing self-initiated movements",
        venue="PNAS 113:1080",
        doi="10.1073/pnas.1513569112",
        arxiv_id=None,
        pmid="26668390",
        pmc_id="PMC4743795",
        license_status="pmc_oa",
        relates_to_substrates=["human_conscious_deliberation_libet_paradigm"],
        relates_to_falsifiers=["F4_chosen_vs_determined", "F5_shrimp_choice_vs_pure_reflex"],
        summary=(
            "Demonstrates ~200ms window in which already-initiated action can be vetoed. "
            "Even within 'unconscious initiation' substrate, there's a downstream selection-against-end "
            "operation. Relevant to F4: the selection isn't single-shot at one moment, it's a chain "
            "of substrate-level direction-selections."
        ),
        notes="PMC OA.",
    ),

    # ============= CONSCIOUSNESS THEORY / META =============
    Reference(
        citation_key="Tononi_2008_IIT_BiolBull",
        authors="Tononi, G.",
        year=2008,
        title="Consciousness as integrated information: a provisional manifesto",
        venue="Biological Bulletin 215:216",
        doi="10.2307/25470707",
        arxiv_id=None,
        pmid="19098144",
        pmc_id=None,
        license_status="paywall_canonical",
        relates_to_substrates=["human_conscious_deliberation_libet_paradigm", "neuron_action_potential_threshold"],
        relates_to_falsifiers=["F2_consciousness_without_asymptote"],
        summary=(
            "Integrated Information Theory (IIT): consciousness identified with integrated information "
            "Φ. Substrate-portable framework — applies to any system with sufficient integrated "
            "information, not just human brains. Partial alignment with user's structural claim "
            "(both are substrate-portable structural definitions), but IIT requires integration "
            "topology rather than asymptotic-DOF selection. Two different structural definitions "
            "at the same level."
        ),
        notes="Marine Biological Lab paywall; Tononi PDF often on his Wisconsin website.",
    ),
    Reference(
        citation_key="Friston_2010_NatRevNeurosci_FEP",
        authors="Friston, K.",
        year=2010,
        title="The free-energy principle: a unified brain theory?",
        venue="Nature Reviews Neuroscience 11:127",
        doi="10.1038/nrn2787",
        arxiv_id=None,
        pmid="20068583",
        pmc_id=None,
        license_status="paywall_canonical",
        relates_to_substrates=["human_conscious_deliberation_libet_paradigm", "bacterial_chemotaxis_run_tumble"],
        relates_to_falsifiers=["F3_substrate_decisions_are_selections"],
        summary=(
            "Free-Energy Principle (FEP): adaptive systems minimise surprise (variational free energy). "
            "Direction-selection in FEP is 'action that minimises prediction error'. Substrate-portable "
            "(bacteria → humans). Compatible with the user's structural claim — selection toward "
            "low-free-energy end of asymptote IS the FEP version of direction-selection. K_k(substrate) "
            "is the generative model's specific form."
        ),
        notes="Nature paywall.",
    ),
    Reference(
        citation_key="Chalmers_1995_facing_hard_problem",
        authors="Chalmers, D. J.",
        year=1995,
        title="Facing up to the problem of consciousness",
        venue="Journal of Consciousness Studies 2:200",
        doi=None,
        arxiv_id=None,
        pmid=None,
        pmc_id=None,
        license_status="open_access",
        relates_to_substrates=["human_conscious_deliberation_libet_paradigm"],
        relates_to_falsifiers=["F2_consciousness_without_asymptote"],
        summary=(
            "Hard problem of consciousness: why is there subjective experience associated with "
            "physical processes? Defines 'consciousness' for the philosophical tradition. "
            "User's structural reframe sidesteps the hard problem at the structural-direction-selection "
            "level — that level doesn't require qualia, only end-selection on signed asymptote. "
            "Conventional consciousness (with qualia) sits at a different ontological level "
            "per [[user_stance_partition_for_understanding]]."
        ),
        notes="Published as JCS open-access PDF on Chalmers' website.",
    ),
    Reference(
        citation_key="Toomre_Toomre_1972_ApJ_mergers",
        authors="Toomre, A.; Toomre, J.",
        year=1972,
        title="Galactic bridges and tails",
        venue="Astrophysical Journal 178:623",
        doi="10.1086/151823",
        arxiv_id=None,
        pmid=None,
        pmc_id=None,
        license_status="open_access",  # NASA ADS provides full PDF
        relates_to_substrates=["cosmic_galaxy_merger_trajectory_selection"],
        relates_to_falsifiers=["F1_signed_asymptote_present", "F3_substrate_decisions_are_selections"],
        summary=(
            "Canonical galaxy-merger simulation paper. Two galaxies approach; outcome bifurcates "
            "based on signed (kinetic - escape) energy. Cosmic-scale direction-selection on signed "
            "asymptotic-DOF; no nervous system, pure dynamics."
        ),
        notes="ADS provides scanned PDF.",
    ),
]


def emit_records():
    """Emit NDJSON records (one per reference)."""
    records = []
    for ref in REFS:
        record = {
            "date": "2026-05-17",
            "spike": "46",
            "kind": "reference",
            "phase": "round1",
            **asdict(ref),
        }
        records.append(record)
    return records


def emit_summary():
    """Provenance summary."""
    n = len(REFS)
    by_license = {}
    for r in REFS:
        by_license[r.license_status] = by_license.get(r.license_status, 0) + 1
    n_doi = sum(1 for r in REFS if r.doi)
    n_pmc = sum(1 for r in REFS if r.pmc_id)
    n_arxiv = sum(1 for r in REFS if r.arxiv_id)
    return {
        "date": "2026-05-17",
        "spike": "46",
        "kind": "reference_summary",
        "n_references": n,
        "by_license": by_license,
        "n_with_doi": n_doi,
        "n_with_pmc_id": n_pmc,
        "n_with_arxiv_id": n_arxiv,
        "n_pmc_oa_or_open_access": by_license.get("pmc_oa", 0) + by_license.get("open_access", 0),
        "verdict": (
            "Mix of textbook/canonical (foundational, no live URL needed) and PMC OA / open access "
            "(autonomously fetchable for round 2). Paywall canonical refs cited but flagged. "
            "Per [[reference_autonomous_validation_tos_landscape]], no autonomous fetching attempted "
            "in round 1 — full provenance recorded."
        ),
    }


def main():
    out_path = "D:/temp/spike_46/spike_46_round1_references.ndjson"
    records = emit_records()
    summary = emit_summary()
    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")
        f.write(json.dumps(summary) + "\n")
    print(f"Wrote {len(records) + 1} records to {out_path}")
    print(f"\nProvenance summary:")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
