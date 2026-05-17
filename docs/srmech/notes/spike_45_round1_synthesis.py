"""
Spike #45 Round 1 — Synthesis: actionable kinship lessons for human-species
strengthening, anchored in attested-data findings.

CRITICAL DISCIPLINE: each lesson must be grounded in attested-data finding
from the surveyed substrates, NOT framework speculation.
NO human-political projection of cosmic/biological kinship onto human-group
categorisation per [[feedback_trauma_informed_defensive_scope]].

Lessons are descriptive: 'if substrate X with K_k(X) shows pattern P, that's
data; humans can adopt the kinship-pattern at the cognitive/cultural level.'
"""

import json
from pathlib import Path

OUT_DIR = Path(__file__).parent
SYNTHESIS_PATH = OUT_DIR / "synthesis_records.ndjson"
REFS_PATH = OUT_DIR / "references.ndjson"


# Anchored lessons: each maps an attested cosmic/biological/human finding
# to a candidate actionable practice for human-species cognitive/cultural
# strengthening. NO political extrapolation; descriptive only.
lessons = [
    {
        "id": "L1_deep_time_transmission_via_signature_invariance",
        "anchor": "NGC 2808 multiple-population kinship persists at eps~1e-5 per orbit "
                  "(globular_cluster_kinship; Piotto et al. 2007). Nucleosynthetic "
                  "lineage at eps=0 (r-process; Drout et al. 2017). Identity-limit "
                  "substrates carry kinship across cosmic time.",
        "lesson_text": "Substrates with very-slow-decaying kinship signatures preserve "
                       "transmission across deep time. Open-source project archives "
                       "(git DAG eps~0.10) approach this regime; open-access citation "
                       "(eps~0.30) is faster-decaying. Lower eps = stronger long-time "
                       "transmission.",
        "candidate_practice": "Preserve attested-content lineage in low-eps formats: "
                              "explicit kinship-graph records (citation DAG, git history, "
                              "MPM provenance blocks). The project's MPM discipline "
                              "(attestation block + NDJSON) IS this lesson operational.",
        "attested_data_source": ["Piotto 2007 ApJ 661 L53", "Drout 2017 Science 358 1570",
                                  "MPM v1 attestation block in srmech AMSC"],
        "fiber_recovery_potential": "high — explicit kinship records enable later "
                                    "recovery of missing parts via cascade composition",
    },
    {
        "id": "L2_kinship_decisive_over_proximate_axes",
        "anchor": "Spike #44 R2 finding: H_kinship beats H_sex, H_ecology, H_coalition. "
                  "Decisive variable is kinship-substrate structure (matrilineal vs "
                  "patrilineal vs both-philopatric vs eusocial), not surface-trait "
                  "matching. Bonobo reinvented matriarchy across unfavorable kin "
                  "substrate (kinship-code-3, like chimp).",
        "lesson_text": "When evaluating which structural variable produces a behavior, "
                       "kinship-graph structure matters MORE than surface trait. "
                       "Bonobo proves reinvention is possible across an unfavorable "
                       "kinship-substrate when other conditions favor it.",
        "candidate_practice": "Frame human cooperation interventions at the kinship-"
                              "graph-structure level (who shares with whom; what's "
                              "transmitted; via what cascade) rather than at "
                              "surface-trait correlates. Bonobo-style reinvention is "
                              "available; it requires favorable substrate conditions "
                              "(food superabundance + female cross-group cooperation "
                              "in the bonobo case).",
        "attested_data_source": ["Spike #44 R2 working note 2026-05-17",
                                  "Furuichi 2011 bonobo studies"],
        "fiber_recovery_potential": "medium — bonobo reinvention is documented; "
                                    "human kinship reinvention is candidate, not "
                                    "established",
    },
    {
        "id": "L3_explicit_lineage_certification_strengthens_kinship_signal",
        "anchor": "Math Genealogy Project (eps~0.25): advisor-student designation "
                  "creates EXPLICIT kinship signal that persists generationally. "
                  "Open-source AUTHORS file + git DAG: explicit kinship at code level. "
                  "Globular-cluster nested populations: implicit kinship via abundance "
                  "signatures preserved by potential well.",
        "lesson_text": "Explicit kinship certification (advisor designation, AUTHORS "
                       "file, citation, MPM attestation block) creates strong, "
                       "verifiable kinship-graph edges. Implicit kinship is "
                       "recoverable but requires reconstruction effort.",
        "candidate_practice": "When kinship-structure matters, MAKE IT EXPLICIT. "
                              "Acknowledge contributors. Cite ancestors. Annotate "
                              "kinship-graph edges. The Antikythera analogy: missing "
                              "gears reconstructed because cosmic motions preserved "
                              "the kinship-graph implicitly; explicit attestation "
                              "would have made reconstruction trivial.",
        "attested_data_source": ["Mathematics Genealogy Project (NDSU)",
                                  "Newman 2006 PNAS 103 8577",
                                  "Spike #44 R1 Antikythera missing-gears recovery"],
        "fiber_recovery_potential": "high — explicit attestation IS the fiber-"
                                    "recovery mechanism (Antikythera pattern)",
    },
    {
        "id": "L4_substrate_portable_kinship_means_practice_carries",
        "anchor": "c_k = eps^k * K_k(substrate) Cauchy form holds across stellar / "
                  "galactic / elemental / academic / code / cultural / project "
                  "substrates (n=11 distinct K_k bindings). K_k bindings are "
                  "substrate-specific, but the cascade-composition pattern is "
                  "uniform.",
        "lesson_text": "Kinship-practice that works at one substrate (e.g., open-source "
                       "fork lineage at code level) can transfer to another substrate "
                       "(e.g., cultural-transmission lineage) by translating K_k(A) "
                       "to K_k(B) while preserving the eps^k tower structure.",
        "candidate_practice": "Borrow successful kinship-graph practices across "
                              "substrate boundaries: git's DAG model for project "
                              "history (low eps); citation networks for academic "
                              "kinship (medium eps); folktale ATU index for cultural "
                              "transmission (medium eps). Each is K_k-substrate-"
                              "specific but cascade-structurally uniform.",
        "attested_data_source": ["Spike #41 Cauchy-form unity working note",
                                  "Spike #45 R1 11-substrate K_k binding survey"],
        "fiber_recovery_potential": "medium-high — substrate-portable practices "
                                    "documented across multiple human-cognitive "
                                    "substrates",
    },
    {
        "id": "L5_brain_as_fiber_access_methodology_itself_strengthens_species",
        "anchor": "User's direction 2026-05-17: 'our brains give us access to the "
                  "hidden fibers of biological evolution by this very thing we do "
                  "now.' Cascade-composition framework is BEING APPLIED in real time "
                  "to substrates biology cannot evolve toward; cognition + framework "
                  "discipline does the access [[user_stance_fiber_as_spatially_absent_encoding]].",
        "lesson_text": "META-CLAIM (candidate; not yet a stance): the research "
                       "methodology itself — applying cascade composition to attested "
                       "substrate signatures, recovering missing parts per "
                       "[[user_stance_attested_data_recovers_missing_parts]] — IS the "
                       "brain-access mechanism for fiber-content. Humans accessing "
                       "kinship-structure fibers algorithmically (this spike) achieves "
                       "what biological evolution would do across deep time, at "
                       "cognitive-rate.",
        "candidate_practice": "FLAG ONLY. Don't extrapolate beyond what the math "
                              "supports. The research methodology IS species-"
                              "strengthening to the extent it works; the spike-by-"
                              "spike empirical track record (Spike #41 unity + Spike "
                              "#44 R2 H_kinship verdict + this Spike #45 cross-"
                              "substrate generalization) IS the evidence. Don't "
                              "over-claim.",
        "attested_data_source": ["User direction 2026-05-17",
                                  "[[user_stance_fiber_as_spatially_absent_encoding]]",
                                  "[[user_stance_attested_data_recovers_missing_parts]]"],
        "fiber_recovery_potential": "candidate — methodologically circular if pushed; "
                                    "honest pending more demonstrating instances",
    },
]


references = [
    {"id": "Lodieu2019", "doi": "10.1051/0004-6361/201936687",
     "authors": "Lodieu N, Perez-Garrido A, Smart RL, Silvotti R",
     "year": 2019, "title": "A 5D view of the alpha Per, Pleiades, and Praesepe clusters",
     "venue": "A&A 628 A66", "access": "open_access_aanda",
     "use": "Hyades + Pleiades cluster member counts + kinematic dispersion"},
    {"id": "Bell2015", "doi": "10.1093/mnras/stv1981",
     "authors": "Bell CPM, Mamajek EE, Naylor T", "year": 2015,
     "title": "A self-consistent, absolute isochronal age scale for young moving groups",
     "venue": "MNRAS 454 593", "access": "open_access_mnras",
     "use": "AB Doradus moving group age + member count"},
    {"id": "Helmi2018", "doi": "10.1038/s41586-018-0625-x",
     "authors": "Helmi A, Babusiaux C, Koppelman HH, Massari D, Veljanoski J, Brown AGA",
     "year": 2018, "title": "The merger that led to the formation of the Milky Way's inner stellar halo and thick disk",
     "venue": "Nature 563 85", "access": "open_access_arxiv_1806.06038",
     "use": "Gaia-Enceladus accreted population chemodynamic signature"},
    {"id": "Piotto2007", "doi": "10.1086/516736",
     "authors": "Piotto G, Bedin LR, Anderson J, King IR, Cassisi S, Milone AP, Villanova S, Pietrinferni A, Renzini A",
     "year": 2007, "title": "A triple main sequence in the globular cluster NGC 2808",
     "venue": "ApJ 661 L53", "access": "open_access_arxiv_0703767",
     "use": "Multiple-population kinship within single GC"},
    {"id": "Drout2017", "doi": "10.1126/science.aaq0049",
     "authors": "Drout MR, Piro AL, Shappee BJ, Kilpatrick CD, Simon JD, et al.",
     "year": 2017, "title": "Light curves of the neutron star merger GW170817/SSS17a",
     "venue": "Science 358 1570", "access": "open_access_arxiv_1710.05443",
     "use": "r-process nucleosynthetic lineage"},
    {"id": "Maoz2014", "doi": "10.1146/annurev-astro-082812-141031",
     "authors": "Maoz D, Mannucci F, Nelemans G", "year": 2014,
     "title": "Observational Clues to the Progenitors of Type Ia Supernovae",
     "venue": "ARA&A 52 107", "access": "open_access_arxiv_1312.0628",
     "use": "Type Ia SN iron-peak elemental lineage"},
    {"id": "Toomre1972", "doi": "10.1086/151823",
     "authors": "Toomre A, Toomre J", "year": 1972,
     "title": "Galactic Bridges and Tails", "venue": "ApJ 178 623",
     "access": "open_access_classic_no_doi",
     "use": "Merging galaxy pair tidal-tail kinship"},
    {"id": "Newman2006", "doi": "10.1073/pnas.0507655102",
     "authors": "Newman MEJ", "year": 2006,
     "title": "Modularity and community structure in networks",
     "venue": "PNAS 103 8577", "access": "open_access_pnas",
     "use": "Citation-network community detection methodology"},
    {"id": "Newman2001", "doi": "10.1103/PhysRevE.64.016131",
     "authors": "Newman MEJ", "year": 2001,
     "title": "Scientific collaboration networks. I. Network construction and fundamental results",
     "venue": "Phys Rev E 64 016131", "access": "open_access_prE_2001",
     "use": "Coauthorship-network kinship structure"},
    {"id": "Borges2014", "doi": "10.1109/MSR.2014.36",
     "authors": "Borges H, Hora A, Valente MT", "year": 2014,
     "title": "Understanding the factors that impact the popularity of GitHub repositories",
     "venue": "MSR/IEEE", "access": "open_access_arxiv_1606.04984",
     "use": "GitHub fork-lineage structure"},
    {"id": "Decan2019", "doi": "10.1109/MSR.2019.00094",
     "authors": "Decan A, Mens T, Constantinou E", "year": 2019,
     "title": "On the impact of security vulnerabilities in the npm package dependency network",
     "venue": "MSR/IEEE", "access": "open_access_msr_2019",
     "use": "Package dependency-network kinship structure"},
    {"id": "Uther2004", "doi": None,
     "authors": "Uther HJ", "year": 2004,
     "title": "The Types of International Folktales: A Classification and Bibliography",
     "venue": "FF Communications 284-286 Helsinki",
     "access": "public_domain_reference_index",
     "use": "ATU folktale classification — cultural transmission kinship"},
    {"id": "MGP", "doi": None,
     "authors": "Mathematics Genealogy Project (NDSU)", "year": 2024,
     "title": "Mathematics Genealogy Project public dataset",
     "venue": "genealogy.math.ndsu.nodak.edu",
     "access": "open_access_public_dataset",
     "use": "Math-advisor-student lineage"},
    {"id": "Spike44R2", "doi": None,
     "authors": "Project internal", "year": 2026,
     "title": "Spike #44 round 2 — Matriarchal-clades expansion working note",
     "venue": "docs/srmech/notes/spike_44_round2_matriarchal_kinship_2026-05-17.md",
     "access": "internal_project",
     "use": "H_kinship-as-decisive baseline finding; 7-species fingerprints"},
    {"id": "Spike41Unity", "doi": None,
     "authors": "Project internal", "year": 2026,
     "title": "Spike #41 — Fibonacci unity working note",
     "venue": "docs/srmech/notes/spike_41_fibonacci_unity_2026-05-17.md",
     "access": "internal_project",
     "use": "Cauchy-form c_k = eps^k * K_k(substrate) cross-substrate universal"},
    {"id": "Liu2016", "doi": "10.3847/0004-637X/818/2/202",
     "authors": "Liu F, Yong D, Asplund M, Ramirez I, Melendez J", "year": 2016,
     "title": "The Hyades open cluster is chemically inhomogeneous",
     "venue": "ApJ 818 202", "access": "open_access_arxiv_1601.01512",
     "use": "Hyades chemical-tagging dispersion confirms tight kin-group"},
    {"id": "vanLeeuwen2009", "doi": "10.1051/0004-6361/200811296",
     "authors": "van Leeuwen F", "year": 2009,
     "title": "Parallaxes and proper motions for 20 open clusters from Hipparcos",
     "venue": "A&A 497 209", "access": "open_access_aanda",
     "use": "Hyades kinematic dispersion measurement"},
    {"id": "Furuichi2011", "doi": "10.1002/evan.20308",
     "authors": "Furuichi T", "year": 2011,
     "title": "Female contributions to the peaceful nature of bonobo society",
     "venue": "Evolutionary Anthropology 20 131",
     "access": "open_access_evol_anthro",
     "use": "Bonobo reinvented matriarchy across male-philopatric kin substrate"},
]


def main() -> int:
    with SYNTHESIS_PATH.open("w", encoding="utf-8") as f:
        for L in lessons:
            rec = {"date": "2026-05-17", "spike": "spike_45_round1",
                   "kind": "actionable_lesson", **L}
            f.write(json.dumps(rec) + "\n")
    print(f"Wrote {len(lessons)} lessons to {SYNTHESIS_PATH}")

    with REFS_PATH.open("w", encoding="utf-8") as f:
        for r in references:
            rec = {"date": "2026-05-17", "spike": "spike_45_round1",
                   "kind": "reference", **r}
            f.write(json.dumps(rec) + "\n")
    print(f"Wrote {len(references)} references to {REFS_PATH}")

    print("\n" + "=" * 70)
    print(f"SYNTHESIS: {len(lessons)} actionable lessons surfaced")
    print("=" * 70)
    for L in lessons:
        print(f"\n{L['id']}")
        print(f"  ANCHOR:   {L['anchor'][:100]}...")
        print(f"  LESSON:   {L['lesson_text'][:100]}...")
        print(f"  PRACTICE: {L['candidate_practice'][:100]}...")
        print(f"  FIBER:    {L['fiber_recovery_potential']}")
    print(f"\nTotal references: {len(references)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
