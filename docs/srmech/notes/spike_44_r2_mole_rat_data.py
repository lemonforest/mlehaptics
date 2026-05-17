"""
Spike #44 round 2 - Naked mole-rat (Heterocephalus glaber) data substrate.

EUSOCIAL MAMMAL boundary case. Single breeding queen + 1-3 breeding males + sterile
workers (60-300 colony size). Queen-driven aggression; reproductive suppression of
all other females.

USER CONSTRAINT FLAG: User said "don't lean on female INSECT hive behavior unless
math/science force." Naked mole-rats are MAMMALIAN eusocial — the boundary case.
Surface with explicit flag for conductor decision.

Sources:
- Clarke & Faulkes 1997 dominance + queen succession (Proc R Soc B, paywall)
- Clarke & Faulkes 2001 intracolony aggression (Anim Behav, paywall)
- Reeve & Sherman 1991 queen activation (PNAS, citation)
- Smith et al. 2024 / 2026 peaceful queen succession (Sci Adv, paywall - news coverage)
- Faulkes et al. 1997 dispersal morphs (Behaviour)
"""

MOLE_RAT_DATA = {
    "species": "Heterocephalus glaber",
    "common": "Naked mole-rat",
    "matriarchal": True,
    "eusocial": True,
    "boundary_case_flag": "USER_CONSTRAINT_REVIEW",
    "boundary_case_note": "User said don't lean on female INSECT hive behavior unless math forces. Naked mole-rats are MAMMALIAN eusocial — same colony structure as eusocial insects (single breeding queen + sterile workers) but mammalian. Surface as boundary case; conductor decides if hypothesis discrimination benefits from including.",

    "kinship": "extremely_high_inbreeding_within_colony",
    "kinship_note": "Within-colony relatedness very high (often >0.5 - sib-mating common); single queen breeds with 1-3 males. Workers = siblings/nephews/nieces of queen.",

    # Colony structure
    "colony_size_range": (60, 300),
    "colony_size_typical": 80,
    "breeding_females_per_colony": 1,  # queen only
    "breeding_males_per_colony_range": (1, 3),
    "non_breeding_workers": "all_other_individuals",
    "reproductive_suppression": "all_other_females",
    "reproductive_suppression_note": "Queen suppresses ovulation in ALL other colony females via aggression + pheromones.",

    # Class K - dominance hierarchy
    "female_dominance_hierarchy": True,
    "hierarchy_linearity": "linear_with_queen_at_top",
    "all_workers_outrank_no_one_relative_to_queen": True,
    "rank_assigned_by": "queen_position_then_body_weight_inversely",
    "rank_acquisition_by_aggression": True,

    # Class L - intergroup / intragroup lethal aggression
    # Intracolony aggression DRIVEN BY QUEEN; lethal at queen succession
    # Note: queen succession 2026 (Science Adv) showed PEACEFUL transition
    # documented in one colony; previous understanding was lethal succession
    "intergroup_lethal_rate_per_100k_y": "essentially_zero_in_situ",
    "intergroup_lethal_note": "Inter-colony lethal aggression at boundaries documented but quantification low. Mole-rats avoid foreign colonies.",
    "intragroup_lethal_rate_per_100k_y": "high_at_succession",
    "intragroup_lethal_note": "Queen succession historically observed lethal (fights between high-ranking females following queen death). 2026 Science Advances reported one PEACEFUL succession; rare. Generally: succession is the lethal-event period.",
    "infanticide_documented": True,
    "infanticide_note": "Queen has been observed killing offspring of subordinate females who break suppression. Pups from non-queen females typically don't survive.",
    "queen_initiated_aggression_dominant_pattern": True,
    "shoves_per_hour_published": None,  # paywalled
    "shoves_per_hour_qualitative": "very_high_queen_to_workers",

    # Class C - cascade
    "coalition_formation": "essentially_none",
    "coalition_note": "Workers do not form coalitions against queen; queen-individual hierarchy.",
    "aggression_pattern": "vertical_top_down_queen_to_workers",

    # Class E - sharing catalog
    "sharing_catalog": {
        "food": True,   # workers feed queen and pups
        "food_note": "Workers provision queen + young; food sharing within colony.",
        "tools": False,
        "knowledge": False,  # minimal learned behavior; mostly genetic role
        "care_allomothering": True,  # workers care for queen's young
        "care_note": "All non-breeding females allomother queen's young.",
        "vocalizations_call_ID": True,
        "vocalizations_note": "Vocal repertoire 17+ calls; colony-specific dialect.",
        "physical_resources": True,  # burrow maintenance, soil distribution
    },
    "knowledge_transmission_dominant_channel": "genetic_role_specification_plus_queen_pheromones",

    # Class L - colony modularity
    "modularity_proxy": "single_colony_one_partition",
    "between_colony_permeability": "very_low",  # disperser morphs exist but rare

    # Class I - multigenerational
    "multigenerational_colonies": True,
    "post_reproductive_longevity": "queen_lives_until_replaced_or_dies",
    "longevity_y": 30,  # extreme for rodent size; queens may breed 20+ years

    # Coalition capability
    "intersex_coalitions_observed": False,
    "female_coalitions_for_dominance": False,
    "female_coalitions_for_defense": "colony_wide_yes",
    "coalitions_high_frequency": False,

    # Disperser morphs (Faulkes 1997+)
    "disperser_morphs_exist": True,
    "disperser_morph_note": "Rare disperser morphs leave to found new colonies.",

    # Worker differentiation
    "worker_morph_differentiation": "size_based_(small_foragers_large_tunnelers)",

    "primary_refs": [
        "clarke_faulkes_1997_dominance_succession",
        "clarke_faulkes_2001_intracolony_aggression",
        "reeve_sherman_1991_queen_activation",
        "smith_2026_peaceful_succession_sci_adv",
        "faulkes_1997_disperser_morphs",
    ],
}


if __name__ == "__main__":
    import json
    print(json.dumps(MOLE_RAT_DATA, indent=2, default=str))
