"""
Spike #44 round 2 - Orca / killer whale (Orcinus orca) data substrate.

Matrilineal mammal: matriarch-led pods; both sexes natally philopatric (rare in mammals);
post-reproductive grandmother effect; resident vs transient ecotype distinction.
Kinship structure: matrilineal (mother-offspring strongest bonds; both sexes stay).

Sources (open-access PMC where possible):
- Brent et al. 2015 Curr Biol (citation-only behind Elsevier): menopause / leadership
- Towers et al. 2018 Sci Rep (PMC5861072): infanticide (one event)
- Foster et al. 2017 / Croft et al. 2017 (PMC5666093): mortality risk by network position
- Buchanan et al. 2024 (PMC11022014): social and genetic connectivity
- Weiss et al. 2021 (PMID:34130498): age/sex influence on associations
- Towers et al. 2024 revised ages (PMC11890658): demographic discounting
"""

ORCA_DATA = {
    "species": "Orcinus orca",
    "common": "Killer whale / orca",
    "matriarchal": True,
    "kinship": "matrilineal_both_sexes_natal_philopatric",
    "kinship_note": "BOTH sexes stay in natal matrilineal pod for life (RARE in mammals - shared only with pilot whales and a few others). Strongest bonds: mother-offspring (especially mother-son).",

    # Population & pod structure (Northern Resident KW reference population)
    "population_studied": "Northern_Resident_KW_1973_2016",
    "study_period_y": 50,
    "annual_growth_rate": 0.022,
    "n_communities": 27,  # Buchanan et al. 2024 on broader 457-whale network
    "individuals_in_buchanan_network": 457,
    "encounters": 548,
    "median_communities_per_year": 6,
    "community_range_per_year": (5, 9),
    "mean_community_size": 11.0,
    "community_size_sd": 5.9,

    # Network metrics
    "simple_ratio_index_mean": 0.19,
    "simple_ratio_index_sd": 0.19,
    "simple_ratio_index_range": (0.03, 1.0),
    "modularity_Q_buchanan_2024": 0.68,  # high modularity = strong matriline partitions
    "modularity_note": "Q=0.68 indicates strongly modular network; pods/matrilines are nearly-discrete social units.",
    "strong_dyads_pairs": 501,
    "strong_dyads_frac_of_nonzero": 0.10,
    "strongest_assoc_dyad_type": "mother_son",

    # Genetic relatedness
    "network_mean_relatedness": 0.030,
    "within_community_relatedness": 0.075,
    "within_subcluster_relatedness": 0.135,
    "genetic_diversity_haplotypes": 6,

    # Sex ratio at pod level
    "sex_ratio_skew": "near_balanced",
    "sex_ratio_note": "Pods contain both sexes; both natally philopatric. Mating occurs cross-pod (avoiding incest).",

    # Class K - dominance
    "female_dominance_hierarchy": True,
    "hierarchy_steepness_published": None,  # not formally measured with steepness statistics
    "matriarch_role_age_threshold_y": 40,
    "matriarch_role_description": "Post-reproductive females (40+) lead foraging decisions, especially during salmon scarcity (Brent 2015).",
    "rank_intersex_orientation": "matriarch_lead_decisions_no_explicit_intersex_dominance",
    "rank_inheritance": "matrilineal_succession",

    # Class L - intergroup / intragroup lethal aggression
    # CONFIRMED LETHAL EVENT: Towers et al. 2018 (one infanticide in 5300+ encounters)
    # Rate: 1 event / (5300 encounters * estimated encounter-population)
    # Conservatively: WCT population "several hundred"; 1 lethal event over ~40+ years
    # Approx 1 / (300 individuals * 40 yr) = 0.83 per 100,000 individual-years
    "intergroup_lethal_rate_per_100k_y": 0.0,  # the one event was within population (transient ecotype)
    "intragroup_lethal_rate_per_100k_y": 0.83,  # ~1 / (300 * 40) extrapolated very rough
    "infanticide_documented": True,
    "infanticide_n_confirmed_events": 1,
    "infanticide_observation_encounters": 5300,
    "infanticide_observation_y": 43,  # 1973-2016
    "infanticide_perpetrator": "32y_male_plus_46y+_mother",
    "infanticide_victim": "neonate_<2_days",
    "lethal_aggression_note": "Only ONE confirmed lethal event in WCT population in >5300 photographically documented encounters over 43 years. Categorically rare. Other reports cite intra-pod fighting but no lethal outcomes documented.",

    # Class C - cascade composition / aggression
    "aggression_rate_published": None,  # not standardized
    "aggression_note": "Aggression rates low; mostly play-fighting and dominance display. Quantitative published rates rare due to observation difficulty.",

    # Class E - sharing catalog
    "sharing_catalog": {
        "food": True,  # resident orcas SHARE prey (salmon) extensively
        "food_note": "Resident orcas share fish among pod members; mothers feed adult sons (Wright 2015 Curr Biol).",
        "tools": False,  # no documented tool use
        "knowledge": True,  # foraging routes, prey identification, vocal dialects
        "knowledge_note": "Vocal clan dialects transmitted matrilineally; foraging knowledge from matriarchs.",
        "care_allomothering": True,
        "vocalizations_call_ID": True,
        "vocalizations_note": "Each matriline has dialect; pod-specific calls.",
        "physical_resources": False,
    },
    "knowledge_transmission_dominant_channel": "matrilineal_vocal_clan",

    # Mortality risk by network position (Foster et al. PMC5666093)
    "male_mortality_hazard_high_closeness_centrality": 0.33,
    "male_mortality_hazard_high_within_community_degree": 0.21,
    "female_mortality_no_network_effect": True,
    "social_centrality_sex_dimorphism_note": "Males with high social centrality have significantly reduced mortality risk; females show no such effect. Sex-dimorphic dependence on social network.",

    # Class I - multigenerational
    "multigenerational_pods": True,
    "post_reproductive_longevity_present": True,
    "post_reproductive_grandmother_effect": True,
    "post_reproductive_grandmother_effect_note": "Brent 2015 + Croft 2017: grandmother presence improves grandcalf survival; menopause selected for ecological knowledge transmission.",
    "longevity_y_female": 80,
    "longevity_y_male": 50,
    "reproductive_senescence_age_y": 40,

    # Coalition capability
    "intersex_coalitions_observed": False,  # no analog to bonobo intersex coalitions
    "female_coalitions_for_defense_observed": True,  # cooperative hunting/defense
    "female_coalitions_for_dominance": False,  # not against rivals in pod
    "coalition_note": "Pod-wide cooperation in hunting; female-led decision-making during scarcity. Not coalition-AGAINST-others; coalition-FOR-the-group.",

    "primary_refs": [
        "buchanan_2024_genetic_connectivity_pmc11022014",
        "foster_2017_mortality_risk_pmc5666093",
        "towers_2018_infanticide_pmc5861072",
        "weiss_2021_age_sex_associations_prsb",
        "brent_2015_menopause_curr_biol",
        "towers_2024_age_revisions_pmc11890658",
    ],
}


if __name__ == "__main__":
    import json
    print(json.dumps(ORCA_DATA, indent=2, default=str))
