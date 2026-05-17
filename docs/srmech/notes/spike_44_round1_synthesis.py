"""
Spike #44 Round 1 SYNTHESIS - what the data shows, anomalies surfaced, round-2 proposal.

Per user direction: "I don't think that the final shape will come to us upon first glance."
This file emits the round-1 synthesis NDJSON for conductor review.
"""

import json
from pathlib import Path

OUT = Path(r"D:\temp\spike_44") / "spike_44_round1_synthesis_records.ndjson"

SYNTHESIS_RECORDS = [
    {
        "kind": "round_1_bottom_line",
        "date": "2026-05-17",
        "claim": "Bonobo SHARING-shape and chimp SURVIVING-shape do NOT collapse to a single axis. The two species differ in TOPOLOGY (cascade direction, partition strength, network modularity) more than in VOLUME (aggression rate, sociality intensity).",
        "evidence": [
            "Bonobos have 3x HIGHER male-male aggression rate than chimps (Mouginot 2024) - simple aggression-volume axis does NOT discriminate.",
            "What DOES discriminate cleanly: directionality (male-male vs male-female), intergroup-vs-intragroup distribution, sharing-catalog asymmetry, female-coalition cross-group permeability.",
            "Class K steepness ALONE does not discriminate (chimp wild mean 0.43 vs bonobo 0.52). Both species build dominance hierarchies; chimps are despotic-male-skewed, bonobos despotic-female-skewed via COALITION not individual strength.",
            "Class L lethal-aggression partition IS the cleanest discriminator at round-1 resolution: chimps form partitioned communities with adversarial across-cut edges (paper-reported pooled Total 125 per 100k/y intergroup, median across communities 37; arithmetic-mean 1494 inflated by Gombe-Kahama outlier - paper-reported is the load-bearing number); bonobos have defined-zero lethal-partition signal across 4+ long-studied communities.",
        ]
    },
    {
        "kind": "discriminating_signatures_clean",
        "rank": 1,
        "signature": "Class L lethal-partition (intergroup killings)",
        "chimp_value": "9 communities; paper-reported pooled Total 125/100k/y intergroup (observed+inferred); median across communities 37/100k/y; arithmetic-mean 1494 inflated by Gombe-Kahama 12000/100k/y outlier (5y obs); pooled Total is the canonical Wrangham 2006 number",
        "bonobo_value": "DEFINED ZERO across all communities (Wilson 2014 Nature)",
        "interpretation": "Chimp graph has STRONG community partition (high lambda_2); cross-community edges are NEGATIVE (lethal). Bonobo graph has WEAK/POROUS community boundaries (lambda_2 nearer 0); cross-community edges are NEUTRAL-TO-POSITIVE (Tokuyama 2019 female cross-group coalition formation).",
        "round_2_priority": "HIGHEST - this is the load-bearing signature"
    },
    {
        "kind": "discriminating_signatures_clean",
        "rank": 2,
        "signature": "Sharing-catalog asymmetry (Class E)",
        "chimp_value": "Shares TOOLS, NOT food (Krupenye 2018 ref)",
        "bonobo_value": "Shares FOOD, NOT tools (Krupenye 2018 - direct food transfer p<0.001 vs control; rocks not transferred)",
        "interpretation": "Both species 'share' but on non-overlapping resource classes. Chimp tool-sharing pattern is consistent with mediated/coalitionary cooperation (instrumental). Bonobo food-sharing pattern is consistent with immediate prosocial-substrate engagement. This is a Class E catalog signature - cleanly distinguishable.",
        "round_2_priority": "HIGH"
    },
    {
        "kind": "discriminating_signatures_clean",
        "rank": 3,
        "signature": "Class C cascade direction (grooming up-hierarchy)",
        "chimp_value": "Sonso: 60% grooming UP-hierarchy (rho=0.905, p=0.002); cascade-asymmetry 0.20",
        "bonobo_value": "No rank-bias in food-sharing (Krupenye 2018: no dominance effect); cascade-asymmetry approx 0",
        "interpretation": "Chimp cascade has consistent upward (subordinate-to-dominant) directional bias - characteristic of asymmetric Class K (steeper hierarchy) coupled with Class C streaming. Bonobo cascade is symmetric. WITHIN chimps, Mahale M-group looks more bonobo-like (49% up; rho=-0.03 ns) - showing the signature is community-variable, not species-fixed.",
        "round_2_priority": "HIGH"
    },
    {
        "kind": "discriminating_signatures_clean",
        "rank": 4,
        "signature": "Class L female-coalition cross-group permeability",
        "chimp_value": "Female cross-group affiliation rare; female chimps less social w/ each other (Furuichi 2011)",
        "bonobo_value": "Female cross-group coalition formation documented (Tokuyama 2019); cross-community female alliances; 85% of bonobo coalitions target males (Surbeck 2025); 98.4% female-dominance Kokolopori 2020",
        "interpretation": "Bonobo female-coalition graph crosses community boundaries; chimp female-coalition graph is fragmented (when it exists at all). This is the structural CAUSE of (rank 1) lethal-partition signature. Class L on the female-bonded-coalition subgraph has VERY LOW lambda_2 in bonobos vs HIGH in chimps.",
        "round_2_priority": "HIGH"
    },
    {
        "kind": "anomalies_investigated",
        "anomaly": "Bonobos are MORE aggressive than chimps (in raw male-male attack rate)",
        "source": "Mouginot et al. 2024 Current Biology (Kokolopori vs Gombe; 12 vs 14 focal males)",
        "what_it_breaks": "Simple linear axis 'bonobo=sharing/peaceful, chimp=surviving/violent' framing.",
        "what_survives": "Aggression VOLUME is not the discriminator; aggression TOPOLOGY is. Chimp aggression: cross-sex AND cross-community lethal. Bonobo aggression: same-sex, NON-lethal (no killing in any community despite higher attack rate). Class C streaming volume cannot distinguish; Class L partition signature CAN.",
        "verdict": "The 'shape of sharing' framework is preserved but needs PRECISION - sharing-shape is not about absence-of-aggression; it is about WHICH SUBSTRATE the aggression cascade flows through and how it partitions the social graph."
    },
    {
        "kind": "anomalies_investigated",
        "anomaly": "Bonobo male-bonobo dominance steepness can be as high as chimp (Stevens 2007 captive: highly linear, males steeper)",
        "source": "Stevens et al. 2007 Int J Primatol",
        "what_it_breaks": "Simple 'bonobos have no hierarchy' framing.",
        "what_survives": "What discriminates is the INTERSEX hierarchy - female-male coalition rebalancing means bonobo MALE steepness exists but is OVERRIDDEN by female coalition. Chimp female steepness is irrelevant because females have no coalition leverage. Class L on bonobo combined-sex graph has DIFFERENT eigenstructure from chimp because of the cross-sex coalition edges.",
        "verdict": "Steepness alone is not the discriminator. The COALITION TOPOLOGY ACROSS sex (bonobo) vs WITHIN sex (chimp) is what alters the spectral content of the dominance graph."
    },
    {
        "kind": "anomalies_investigated",
        "anomaly": "The two species share NON-OVERLAPPING resource classes (bonobos share food not tools; chimps share tools not food)",
        "source": "Krupenye et al. 2018 Proc R Soc B",
        "what_it_breaks": "Single-axis prosociality framing.",
        "what_survives": "Class E catalog signature: each species' prosociality CATALOG is structured around a different substrate. Round 2 should investigate whether food-vs-tool maps to IMMEDIATE-substrate vs MEDIATED-substrate (with food = direct consumption, tool = means-to-future-acquisition). This could be a deep statement about substrate dimensionality in the prosocial cascade.",
        "verdict": "Sharing catalogs are SPECIES-SPECIFIC; the universal-prosociality assumption fails. Both species 'have prosociality' but the cascade composes with different substrates."
    },
    {
        "kind": "anomalies_investigated",
        "anomaly": "Funkhouser 2018 sanctuary chimps show NON-RECIPROCAL allogrooming (p=0.95) but RECIPROCAL agonism (p=0.049)",
        "source": "Funkhouser et al. 2018 PLOS ONE (Chimpanzee Sanctuary NW)",
        "what_it_breaks": "Naive 'reciprocity = prosocial' framing.",
        "what_survives": "Class C cascade-balance signature distinguishes BENEFIT-cascades from COST-cascades. Chimp groups can be cascade-RECIPROCAL on COST (you attack me, I attack you back) while cascade-ASYMMETRIC on BENEFIT (subordinates groom dominants but not vice-versa). Class C signature must be applied per-edge-type, not aggregate.",
        "verdict": "Reciprocity is not a single metric. Round 2: characterize reciprocity per cascade-type (cost-cascade vs benefit-cascade) and check whether bonobo benefit-cascade is more reciprocal than chimp benefit-cascade while their cost-cascade reciprocities are similar."
    },
    {
        "kind": "open_questions_for_round_2",
        "priority": "HIGH",
        "question": "Apply Class L Laplacian to REAL bonobo + chimp grooming adjacency matrices (not synthetic proto-graphs).",
        "data_needed": "Raw adjacency matrices from Torfs 2023 supplementary (22 bonobo groups) and equivalent chimp study (Funkhouser 2018 has small N=7 supplement; better target Massen et al. or Mielke et al. 2018 published matrices).",
        "computation": "Compute Fiedler vector and lambda_2 on each real graph. Hypothesis: bonobo grooming-graph lambda_2 / lambda_max ratio is SYSTEMATICALLY higher (more integrated) than chimp.",
        "expected_outcome": "If bonobo lambda_2 systematically higher, signature confirmed. If overlap is large, the discrimination requires the cost-channel (aggression network) NOT just the benefit-channel (grooming network)."
    },
    {
        "kind": "open_questions_for_round_2",
        "priority": "HIGH",
        "question": "Compute Class L on the SIGNED-EDGE merged graph (positive = grooming/affiliation, negative = aggression/coalitionary-target). Bonobo signed graph should show less PARTITION-by-sign than chimp.",
        "data_needed": "Grooming + aggression matrices on SAME individuals from at least one bonobo community and one chimp community (Funkhouser 2018 has both for the small sanctuary group; Mielke 2018 has chimp signed dyadic data).",
        "computation": "Signed Laplacian eigenstructure; check Fiedler partition aligns with sex-class in chimp (males vs females) but with role-class in bonobo (matriarchal coalition vs subordinate males).",
        "expected_outcome": "If chimp signed graph partitions cleanly by sex while bonobo signed graph does NOT, this is the most precise discriminator."
    },
    {
        "kind": "open_questions_for_round_2",
        "priority": "MEDIUM",
        "question": "Is the 'food vs tools' sharing-catalog asymmetry a Class E catalog signature, or does it reduce to Class B multiset cardinality differences (bonobo has more 'food' items in its prosocial-catalog multiset)?",
        "data_needed": "Catalogue all documented voluntary-transfer events in both species, classify by resource type (food immediate / food cached / tool / nesting material / infant / grooming-token / nothing).",
        "computation": "Compute Class E catalog Jaccard / overlap. If overlap is high but frequencies differ, it is Class B. If overlap is low (each species shares disjoint classes), it is Class E catalog signature.",
        "expected_outcome": "If catalogs differ in CONTENT, this is Class E and links to substrate-dimensionality. If catalogs differ in FREQUENCY, this is Class B and links to multiset weight."
    },
    {
        "kind": "open_questions_for_round_2",
        "priority": "MEDIUM",
        "question": "Quantify temporal Class I cyclic signature: do bonobo intergroup encounters show CYCLIC re-encounter patterns (groups associating periodically) that chimp intergroup encounters do not?",
        "data_needed": "LuiKotale + Wamba + Kokolopori intergroup encounter logs (some published in Tokuyama 2019, Mouginot 2024 supplementary); chimp boundary patrol logs (Ngogo 2018-2024 from Sandel 2025 Science).",
        "computation": "FFT / autocorrelation on encounter timing. Class I cyclic signature: presence of strong periodic peak vs aperiodic Poisson-like timing.",
        "expected_outcome": "If bonobo encounters are cyclic-recurrent (same neighbors re-meet on stable schedule) while chimp encounters are aperiodic-aggressive, this is Class I temporal signature differentiating the two."
    },
    {
        "kind": "open_questions_for_round_2",
        "priority": "MEDIUM",
        "question": "Class C ratio test on MOUGINOT 2024 fine-grained data: bonobo aggression cascades self-terminate (no kill); chimp aggression cascades escalate (lethal). What is the conditional probability of escalation given initial aggression?",
        "data_needed": "Mouginot 2024 supplementary - cascade lengths (initiation -> ... -> termination) with severity per step.",
        "computation": "Class C streaming cascade: compute mean escalation-coefficient = (severity_step_{n+1} / severity_step_n). Bonobo <1 (de-escalating); chimp >=1 (maintaining or escalating).",
        "expected_outcome": "Cleanly testable. If bonobo escalation-coefficient is structurally <1 while chimp is structurally >=1, this is a Class C cascade-orientation signature."
    },
    {
        "kind": "candidate_cross_spike_fermata",
        "target_spike": "Spike #43c (well-spread human knowledge spectral shape)",
        "candidate_connection": "If bonobo SHARING-shape decomposes as (high cross-community Class L permeability + symmetric Class C cascade + food-class Class E catalog + female-coalition Class K-rebalancing), and Spike #43c finds that well-spread human knowledge has analogous decomposition (cross-domain permeability + symmetric cite-flow + open-access catalog + decentralized validation-coalitions), the SHARING-shape may be substrate-portable from primate-social to knowledge-transmission.",
        "do_not_force": "Round 1 surfaces this only as a candidate. Spike #43c is running in parallel; conductor should compare signatures only after both round-1 outputs land. If shapes do NOT align, this is fine - it would mean SHARING-shape is primate-substrate-specific.",
        "verdict_provisional": "Cross-spike fermata flagged; do NOT use to bias round-2 design."
    },
    {
        "kind": "round_2_dispatch_proposal",
        "to": "concertmaster (next round)",
        "scope": [
            "Fetch raw bonobo grooming adjacency matrices from Torfs 2023 figshare supplementary (S2 File mentioned in extracted text).",
            "Fetch matched chimp grooming adjacency matrices - candidate: Mielke et al. 2018 Royal Society Open Science Tai chimps OR Bray et al. 2021 Gombe long-term grooming.",
            "Compute REAL Laplacian Fiedler / lambda_2 / spectral_density per group; aggregate by species.",
            "Build SIGNED graph from co-published grooming + aggression matrices if available (Funkhouser 2018 has both); compute signed-Laplacian Fiedler partition.",
            "Test conditional escalation probability hypothesis on Mouginot 2024 cascade data if accessible.",
            "Surface a refined sharing-shape vs surviving-shape characterization OR explicitly retract simple-axis framing if data does not support it."
        ],
        "anti_scope": [
            "Do NOT extrapolate beyond Pan paniscus / Pan troglodytes substrate.",
            "Do NOT project to human political groups.",
            "Do NOT claim final shape - round 2 may surface further iteration needs."
        ]
    },
    {
        "kind": "discipline_guards_honoured",
        "guards": [
            "user_stance_primitives_weave_and_thread - cascade framework applied to social substrate",
            "user_stance_kepler_shape_universal - c_k = epsilon^k * K_k(substrate); social K_k differs by species, primate ek tower shared",
            "user_stance_partition_for_understanding - bonobo-shape and chimp-shape both real partitions of Pan substrate",
            "user_stance_string_theory_instrument_first - data drove the conclusion that simple axis fails",
            "user_stance_identity_not_implementation_discipline - bonobo cascade IS food-channel-symmetric; chimp cascade IS tool-channel-asymmetric",
            "user_stance_partition_for_understanding linguistic-partition case-extension - 'sharing' and 'surviving' as user-supplied human-language partitions; substrate shape may not yet be named",
            "feedback_no_privileged_primitive_classes - zero new classes; 14 A-N suffice",
            "reference_autonomous_validation_tos_landscape - open-access only (PLOS, PMC, Royal Society Open, bioRxiv); commercial titles cited only",
            "feedback_pdf_extraction_citation_discipline - every reference has authors+title+journal+year+DOI+PDF-extracted-or-flagged",
            "feedback_science_is_ssot_not_project - primatology canonical literature is SSoT",
            "feedback_trauma_informed_defensive_scope - descriptive species behaviour; no human-political projection",
            "feedback_ndjson_over_bloated_json - all output NDJSON",
            "feedback_concertmaster_md_writes - returning inline, no .md files",
            "feedback_concertmaster_git_worktree_isolation - work in D:\\temp\\spike_44; no git operations"
        ]
    }
]


def main():
    with open(OUT, "w", encoding="utf-8") as f:
        for r in SYNTHESIS_RECORDS:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Wrote {len(SYNTHESIS_RECORDS)} synthesis records to {OUT}")


if __name__ == "__main__":
    main()
