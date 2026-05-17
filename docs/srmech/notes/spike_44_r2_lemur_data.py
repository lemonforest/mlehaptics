"""
Spike #44 round 2 - Ring-tailed lemur (Lemur catta) data substrate.

Female-dominant primate: 100% female-over-male dominance; female-philopatric;
multi-male multi-female troops; despotic female dominance style.
Kinship structure: female-philopatric (males disperse).

Sources (open-access PMC where possible):
- Sauther et al. 1999 socioecology review (PDF, citation)
- Whitten & Brockman 2001 androgens (PMC1690709)
- Petty & Drea 2022 food / male deference (PMC9539500)
- Kappeler & Fichtel 2022 lemur intersexual dominance review (Frontiers - open)
- Pereira & Kappeler 1997 social play
"""

LEMUR_DATA = {
    "species": "Lemur catta",
    "common": "Ring-tailed lemur",
    "matriarchal": True,
    "female_dominant_intersex": True,
    "kinship": "female_philopatric",
    "kinship_note": "Females stay; males disperse (up to 1/3 of males move between troops/year). Multi-male/multi-female troops.",

    # Population & troop structure
    "troop_size_mean": 13,
    "troop_size_range": (5, 27),
    "adult_sex_ratio": "near_balanced",
    "social_org": "multi_male_multi_female",

    # Class K - dominance hierarchy
    "female_dominance_hierarchy": True,
    "hierarchy_linearity": "non_linear_in_both_sexes",  # but female-over-male universal
    "all_females_outrank_all_males": True,  # canonical lemur trait
    "female_over_male_win_rate_beza_mahafaly": 0.969,  # 96.9%
    "agonism_over_food_frac": 0.86,  # 86% of agonism at food
    "n_agonistic_interactions_beza_1800h": 2301,
    "agonism_per_hour": 1.28,  # 2301/1800

    # Petty & Drea 2022 (PMC9539500) male-deference rates
    "male_deference_rate_low_provisions": {
        "Group_1_2000": 0.58, "Group_3_2000": 0.51,
        "Group_1_2001": 0.61, "Group_3_2001": 0.60,
    },
    "male_deference_rate_high_provisions": {
        "Group_2_2002": 0.69, "Group_3_2002": 0.74,
    },
    "male_deference_LA_zoo_2016_17": 0.70,
    "deference_increases_with_food_availability": True,

    # Agonistic interaction rates per hour (Petty & Drea 2022)
    "female_to_male_agonism_per_hour_low_provisions": 5.2,
    "female_to_male_agonism_per_hour_high_provisions": 4.6,

    # Class L - intergroup / intragroup lethal aggression
    # Targeted aggression / "eviction" common in females; some lethal
    "intergroup_lethal_rate_per_100k_y": "rare_to_moderate",
    "intergroup_lethal_note": "Between-troop encounters at boundary territories common; injuries occur but population-level lethal rates not standardized. Female-female targeted aggression toward immigrants/dispersers known to be intense.",
    "intragroup_lethal_rate_per_100k_y": "documented",
    "intragroup_lethal_note": "Female-female 'targeting' or 'eviction' can be intense and occasionally lethal (Vick & Pereira 1989); siblicide rare; infanticide documented",
    "infanticide_documented": True,
    "infanticide_note": "Documented in stranger-male takeover contexts but rare due to female dominance.",
    "lethal_aggression_relative": "moderate_lower_than_chimp_higher_than_orca",

    # Class C - cascade / coalitions
    "coalition_formation": "moderate",
    "female_coalitions_against_males": True,
    "female_coalitions_note": "Females support each other in aggressive encounters against males.",
    "female_evict_other_females": True,
    "eviction_note": "Female-female targeting / eviction also occurs; not all-female-cooperative.",

    # Class E - sharing catalog
    "sharing_catalog": {
        "food": False,  # generally do not share food voluntarily
        "tools": False,
        "knowledge": True,  # ranging routes, food sources
        "care_allomothering": True,  # extensive (Pereira 1991)
        "allomothering_note": "Females nurse and care for related infants extensively.",
        "vocalizations_call_ID": True,
        "physical_resources": False,
    },
    "knowledge_transmission_dominant_channel": "maternal_and_matriline",

    # Class L - troop modularity
    "modularity_proxy": "single_troop_no_sub_groups",
    "between_troop_permeability": "low",  # territory-based; troops well-bounded

    # Class I - multigenerational
    "multigenerational_troops": True,
    "post_reproductive_longevity_present": False,  # no clear menopause
    "longevity_y": 18,  # wild ~16-20

    # Coalition capability
    "intersex_coalitions_observed": False,  # primarily intrasex
    "female_coalitions_for_dominance": True,
    "female_coalitions_for_defense": True,
    "coalitions_high_frequency": False,  # lower than hyena/bonobo

    # Cross-species lemur reference (Kappeler & Fichtel 2022 Frontiers - open)
    "lemur_aggression_rate_conflicts_per_h": 0.49,  # specific to L. catta in Madagascar
    "lemur_female_win_rate_conflicts_pct": 100.0,  # decided conflicts
    "lemur_decided_conflict_pct": "100%",  # L. catta has 100% decided conflicts

    "primary_refs": [
        "petty_drea_2022_male_deference_pmc9539500",
        "whitten_brockman_2001_androgens_pmc1690709",
        "kappeler_fichtel_2022_lemur_dominance_frontiers",
        "sauther_1999_socioecology",
        "vick_pereira_1989_eviction",
    ],
}


if __name__ == "__main__":
    import json
    print(json.dumps(LEMUR_DATA, indent=2, default=str))
