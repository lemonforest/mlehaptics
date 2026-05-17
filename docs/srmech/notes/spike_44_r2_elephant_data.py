"""
Spike #44 round 2 - African elephant (Loxodonta africana) data substrate.

Matriarchal mammal: oldest female leads family group; multigenerational matriline;
allomothering; cross-family bond groups; fission-fusion at higher tiers.
Kinship structure: matrilineal philopatry (females stay, males disperse).

Sources (open-access PMC where possible):
- McComb et al. 2001 (matriarchs as repositories - Science, citation-only)
- McComb et al. 2011 Proc R Soc B (PMC3169024): leadership / matriarch age & response
- McComb et al. 2014 Proc R Soc B (PMC3874604): culling-disruption effects
- Goldenberg et al. 2016 Curr Biol (citation-only): vertical transmission
- Webber et al. 2023 review (PMC12044372): knowledge transmission
- Chiyo et al. 2022 elephant play (PMC11634687): play / aggression / family-bonds
- Allen et al. 2020 (PMC8692974): male aggression effects of mature bull presence
- Foley et al. 2008 (BMC Ecol): age & response (cited via review)
- Wittemyer et al. 2005 (Anim Behav): multi-tier social structure
"""

ELEPHANT_DATA = {
    "species": "Loxodonta africana",
    "common": "African savanna elephant",
    "matriarchal": True,
    "kinship": "matrilineal_philopatry",
    "kinship_note": "Females stay in natal core group; males disperse around puberty (10-14y).",

    # Population & social tier structure
    # Amboseli is the canonical long-term site
    "amboseli_population": 1500,
    "amboseli_family_groups": 58,
    "mean_adults_per_family": 5.0,
    "adult_per_family_sd": 2.6,
    "matriarch_age_range_y": (23, 70),
    "core_group_individuals_example": 83,
    "core_groups_in_example_set": 10,

    # Sex ratio
    "sex_ratio_skew": "female_biased_adult_groups",
    "sex_ratio_note": "Family groups are female-biased; males live separately in bachelor groups or solitary post-dispersal.",

    # Class K - dominance hierarchy
    # Wittemyer & Getz 2007 found dominance hierarchy among Samburu females
    "female_dominance_hierarchy": True,
    "hierarchy_steepness_published": None,  # not standardized across studies
    "rank_assigned_by": "age_and_body_size",
    "rank_intersex_orientation": "n/a - sexes mostly socially separate",
    "rank_inheritance": "matrilineal_succession_to_matriarch_on_death",

    # Class L - intergroup / intragroup lethal aggression
    # ELEPHANTS DO NOT CONDUCT LETHAL INTERGROUP ATTACKS ON CONSPECIFICS
    # Note: well-documented absence; bull elephants in musth can be aggressive toward
    # non-conspecific targets (rhinos, humans, livestock) but conspecific lethal
    # intergroup attacks are not in the canonical literature
    "intergroup_lethal_rate_per_100k_y": 0.0,
    "intragroup_lethal_rate_per_100k_y": 0.0,
    "lethal_aggression_note": "Canonical literature (Moss, Poole, Wittemyer, Foley reviews) does not report intergroup or intragroup lethal attacks among conspecifics. Bulls in musth can be highly aggressive but conspecific killings are not documented as a population-rate phenomenon. Calf mortality is overwhelmingly predation/disease, not infanticide.",
    "infanticide_documented": False,

    # Class C - cascade composition / aggression rates / play (proxy for affiliation)
    # Chiyo et al. 2022 (PMC11634687): 52 aggression bouts in 230.5h = 22.6/100h
    # for 15 elephants studied; aggression > between families than within
    "aggression_bouts_per_100h": 22.6,
    "aggression_within_vs_between_families": "more_between_than_within (p=0.002)",
    "aggression_note": "Aggression occurs but mostly low-intensity; cross-family > within-family. NOT lethal.",
    # Allen et al. 2020 (PMC8692974): 1527 focal follows; 68.5% had zero aggression
    "focal_follow_with_zero_aggression_frac": 0.685,
    "older_male_presence_reduces_aggression_coef": -0.242,
    "older_male_presence_reduces_aggression_p": 0.001,

    # Play frequencies (proxy for affiliative cascade)
    "play_age_correlation_r": -0.738,
    "play_male_vs_female_higher": "male",
    "play_between_vs_within_families": "more_between_than_within (p=0.004)",

    # Class E - sharing catalog (what gets transferred between individuals)
    "sharing_catalog": {
        "food": False,   # elephants generally do not share food voluntarily
        "tools": False,  # elephants do not use tools at population level
        "knowledge": True,   # migration routes, water sources, threat ID
        "care_allomothering": True,  # extensive allomothering
        "vocalizations_call_ID": True,  # contact calls, distress calls
        "physical_resources": False,
    },
    "knowledge_transmission_dominant_channel": "matriarchal_repository",
    "allomothering_observed": True,
    "calf_survival_increases_with_older_females_present": True,

    # Class L Fiedler-partition proxy
    # Webber et al. 2023 review: family groups bond into "bond groups" then "clans"
    # Fission-fusion at multiple tiers; not categorical isolation
    "social_tier_structure": ["mother_calf", "core_group", "bond_group", "clan"],
    "n_social_tiers": 4,
    "between_tier_permeability": "high_at_bond_group_level",
    "modularity_proxy": "moderate_at_core_group_level_low_at_bond_clan_level",

    # Class I - cyclic/multigenerational
    "multigenerational_groups": True,
    "matriarch_succession": "oldest_remaining_female_at_matriarch_death",
    "longevity_y": 60,  # wild
    "post_reproductive_longevity_present": True,  # ages 55-60 reproductive decline
    "post_reproductive_role": "knowledge_repository_decision_leader",

    # Coalition capability
    # Elephants form defensive coalitions during threats but not coalitions for dominance
    "intersex_coalitions_observed": False,
    "female_coalitions_for_defense_observed": True,
    "female_coalitions_for_dominance": False,
    "coalition_note": "Family-group defensive coalitions are universal (response to lions, threats). Dominance-coalitions are not documented because there is essentially no intergroup competition to coalesce against. Hierarchy is age-based and accepted.",

    # References
    "primary_refs": [
        "mccomb_2011_prsb_pmc3169024",
        "mccomb_2014_prsb_pmc3874604",
        "chiyo_2024_play_pmc11634687",
        "allen_2020_aggression_pmc8692974",
        "webber_2023_review_pmc12044372",
        "wittemyer_2008_social_tier",
    ],
}


if __name__ == "__main__":
    import json
    print(json.dumps(ELEPHANT_DATA, indent=2, default=str))
