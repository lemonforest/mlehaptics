"""
Spike #44 round 2 - Spotted hyena (Crocuta crocuta) data substrate.

Female-dominant carnivore: reverse sexual dimorphism; female-philopatric; clan-based
fission-fusion; matrilineal rank inheritance; high coalition formation rates.
Kinship structure: female-philopatric (males disperse to breed in other clans).

Sources (open-access PMC where possible):
- Holekamp et al. 2007 social intelligence (PMC2346515)
- Watts et al. 2025 long-term demography Liuwa (PMC11949567)
- Smith et al. 2010 coalitions (citation - paywall hyena Smith lab)
- Holekamp et al. 2011 society review (citation - paywall PDF)
- Engh et al. 2002 maternal rank inheritance (citation)
- Drea & Carter 2009 cooperative behavior (citation)
"""

HYENA_DATA = {
    "species": "Crocuta crocuta",
    "common": "Spotted hyena",
    "matriarchal": True,
    "female_dominant_intersex": True,
    "kinship": "matrilineal_female_philopatric",
    "kinship_note": "Females stay; males disperse to breed. Reverse sexual dimorphism (females larger). Females dominate all males structurally.",

    # Population & clan structure
    "clan_size_range": (6, 90),
    "clan_size_typical_prey_rich": 70,
    "n_clans_in_demography_study": 11,
    "n_individuals_in_demography_study": 663,
    "sex_ratio_skew": "near_balanced",
    "adult_sex_ratio": (83, 86),  # F, M from Liuwa
    "study_period_y": 10,
    "density_per_km2_range": (0.18, 1.01),
    "annual_survival_cubs_f": 0.76,
    "annual_survival_cubs_m": 0.75,
    "annual_survival_adults_f": 0.86,
    "annual_survival_adults_m": 0.82,
    "cub_mortality": 0.235,
    "directly_observed_deaths_in_10y": 13,
    "directly_observed_lion_kills": 4,

    # Class K - dominance hierarchy
    "female_dominance_hierarchy": True,
    "hierarchy_linearity": "strictly_linear",  # Holekamp 2007
    "hierarchy_stability": "extremely_stable_over_years",
    "rank_acquisition_age_months": 18,  # rank fixed by 18mo following mother
    "rank_inheritance": "matrilineal_immediately_below_mother",
    "rank_intersex_orientation": "female_dominate_all_males_structurally",
    # Reverse-sex hierarchy: females rank above males in every dyad
    "all_females_outrank_all_males": True,

    # Class L - intergroup / intragroup lethal aggression
    # CORRECTED 2026-05-17: hyenas have significant lethal aggression
    # Infanticide by females accounts for 24% of juvenile mortality
    # Inter-clan "wars" documented (Boydston et al. 2001) - exact rate not standardized
    "intergroup_lethal_rate_per_100k_y": "documented_clan_wars",
    "intergroup_lethal_note": "Boydston et al. 2001: inter-clan 'wars' at boundary territories; territory defense involves coalitions; outcome determined by numerical advantage. Cited in Wrangham 2006 PNAS as one of three species with lethal intergroup violence (with lions and chimps). Exact rate per 100k/y not standardized but documented as significant.",
    "intragroup_lethal_rate_per_100k_y": "high_infanticide",
    "intragroup_lethal_note": "Infanticide by females accounts for ~24% of juvenile mortality; 1 in 10 hyenas die from infanticide. All observed cases: adult female killers targeting juveniles <5mo. Siblicide ~5% of juvenile mortality.",
    "infanticide_documented": True,
    "infanticide_rate_frac_juvenile_mortality": 0.24,
    "infanticide_rate_per_birth": 0.10,
    "siblicide_frac_juvenile_mortality": 0.05,
    "infanticide_note": "Significant intragroup lethal aggression; female-female infanticide is leading source of juvenile mortality. Different from chimp pattern (male coalition lethal) but ALSO lethal.",
    # Compare: hyena lethal aggression - now better characterized
    # Infanticide by females + inter-clan boundary aggression are both significant
    "lethal_aggression_relative": "moderate_to_high_via_female_infanticide_and_clan_wars",
    "lethal_aggression_revised_round2": "Higher than initially encoded. Female-female infanticide IS lethal. Inter-clan boundary 'wars' documented though rate not standardized to 100k/y. Comparison: Hyena and Chimp both have significant intergroup AND intragroup lethal aggression - different sex-dynamics (chimp male-coalition lethal, hyena female-infanticide lethal) but BOTH lethal.",

    # Class C - cascade / coalitions / reconciliation
    "reconciliation_rate_frac_fights": 0.15,  # 15% of fights reconciled
    "reconciliation_sex_difference": "males_more_likely_to_reconcile_than_females",
    "coalition_formation": "extensive",
    "coalitions_join_dominant_side_frac": "almost_always",  # Holekamp 2007
    "coalition_role_in_rank_maintenance": True,
    "coalition_note": "Coalitions support dominant individuals to maintain matrilineal rank structure. Females support close kin most often (Smith 2010). Female-female coalitions central to clan structure.",

    # Class E - sharing catalog
    "sharing_catalog": {
        "food": True,  # mothers nurse offspring intensively; food sharing at kills
        "food_note": "Mothers nurse for up to 14 months; high maternal investment. Food sharing at kills among matriline.",
        "tools": False,
        "knowledge": True,  # hunting techniques, territory boundaries
        "knowledge_note": "Hunting strategies and territory learned from mother and matriline.",
        "care_allomothering": True,  # cooperative nursing/babysitting
        "vocalizations_call_ID": True,  # individual whoops, greeting ceremony
        "vocalizations_note": "Greeting ceremony reinforces social bonds (Smith et al.).",
        "physical_resources": False,
    },
    "knowledge_transmission_dominant_channel": "matrilineal_kin_clusters",

    # Class L - matriline modularity
    "modularity_proxy": "high_within_matriline_low_between_matriline",
    "matriline_clustering_in_rank": "adjacent_rank_positions",  # Holekamp 2007
    "between_matriline_permeability": "moderate",  # clan shares territory, matrilines distinct

    # Class I - multigenerational
    "multigenerational_clans": True,
    "post_reproductive_longevity_present": False,  # hyenas do not show clear menopause
    "longevity_y_female": 25,  # captive higher, wild ~14-20
    "longevity_y_male": 18,
    "reproductive_senescence_age_y": 20,

    # Coalition capability (KEY FEATURE)
    "intersex_coalitions_observed": True,  # females support each other against males
    "intersex_coalitions_note": "Female coalitions reinforce female-dominance over males. Adult males rank below adult females universally.",
    "female_coalitions_for_dominance": True,
    "female_coalitions_for_defense": True,
    "coalitions_high_frequency": True,
    "male_coalitions_observed": True,
    "male_coalitions_note": "Immigrant males form weak coalitions among themselves but rank below females.",

    "primary_refs": [
        "holekamp_2007_social_intelligence_pmc2346515",
        "watts_2025_long_term_demography_pmc11949567",
        "smith_2010_coalitions",
        "holekamp_2011_society_review",
        "engh_2002_rank_inheritance",
    ],
}


if __name__ == "__main__":
    import json
    print(json.dumps(HYENA_DATA, indent=2, default=str))
