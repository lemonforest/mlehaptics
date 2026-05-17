"""
Spike #44 round 2 - Carry-forward of round-1 bonobo + chimp data.

Round 1 (PR #479; spike_44_round1_*) established:
- Bonobo: HIGHER raw aggression than chimp (Mouginot 2024) but ZERO lethal events (Wilson 2014)
- Chimp: 125/100k/y intergroup lethal kill rate (Wrangham 2006 pooled)
- Female-coalition Class L OVERRIDES male Class K steepness in bonobos (Surbeck 2025)
- Chimps lack intersex coalition; female-coalition essentially absent
- Class L lethal-aggression partition is the cleanest single discriminator round 1 found

Round 2 reframes these in the hypothesis-discrimination context.
"""

BONOBO_DATA = {
    "species": "Pan paniscus",
    "common": "Bonobo",
    "matriarchal": True,  # female-dominant via coalition
    "female_dominant_via_coalition": True,
    "kinship": "male_philopatric",  # IMPORTANT: bonobo and chimp BOTH male-philopatric
    "kinship_note": "Males stay in natal community; females disperse. BUT bonobo females form COALITIONS across natal lines.",

    # Class K
    "male_steepness_range": (0.35, 0.70),
    "male_steepness_mean": 0.52,
    "intersex_dominance": "female_via_coalition",
    "female_dominance_kokolopori_2020": 0.984,  # 98.4%
    "female_dominance_eyengo_1998": 1.0,
    "female_coalition_target_males_frac": 0.85,

    # Class L
    "intergroup_lethal_rate_per_100k_y": 0.0,
    "intragroup_lethal_rate_per_100k_y": 0.0,  # essentially zero (1 incident Feb 2025 LuiKotale)
    "infanticide_documented": False,  # no bonobo infanticide confirmed

    # Class C
    "male_attack_rate_per_100k_h": 6903,  # 3x chimp (Mouginot 2024)
    "male_female_aggression_frac": 0.1,

    # Class E
    "sharing_catalog": {
        "food": True,
        "tools": False,
        "knowledge": True,
        "care_allomothering": True,
        "vocalizations_call_ID": True,
        "physical_resources": False,
    },

    # Coalition
    "intersex_coalitions_observed": True,  # KEY: female-coalition crosses sex line
    "female_coalitions_for_dominance": True,
    "female_coalitions_cross_natal_lines": True,  # Tokuyama 2019

    # Kinship -- bonobos break expected pattern (despite male-philopatry, females coalesce)
    "anomaly": "FEMALE_COALITION_DESPITE_MALE_PHILOPATRY",
}

CHIMP_DATA = {
    "species": "Pan troglodytes",
    "common": "Chimpanzee",
    "matriarchal": False,
    "patriarchal": True,
    "male_dominant_intersex": True,
    "kinship": "male_philopatric",
    "kinship_note": "Males stay in natal community; females disperse. Male coalitions strong, female coalitions weak.",

    # Class K
    "male_steepness_range": (0.22, 0.70),
    "male_steepness_mean": 0.43,
    "intersex_dominance": "male",

    # Class L
    "intergroup_lethal_rate_per_100k_y_pooled": 125,  # Wrangham 2006 pooled
    "intergroup_lethal_rate_per_100k_y_arithmetic": 1494,  # arithmetic mean (Gombe-Kahama outlier)
    "intragroup_lethal_rate_per_100k_y_range": (0, 1008),
    "infanticide_documented": True,
    "infanticide_note": "Documented across communities; ~50% of infants in some communities die from infanticide.",

    # Class C
    "male_attack_rate_per_100k_h": 2301,
    "male_female_aggression_frac": 0.5,

    # Class E
    "sharing_catalog": {
        "food": False,  # generally not voluntary
        "tools": True,
        "knowledge": True,
        "care_allomothering": False,  # mostly mother only
        "vocalizations_call_ID": True,
        "physical_resources": False,
    },

    # Coalition
    "intersex_coalitions_observed": False,
    "male_coalitions_observed": True,
    "male_coalitions_for_dominance": True,
    "male_coalitions_for_intergroup_violence": True,
    "female_coalitions_essentially_absent": True,
}


if __name__ == "__main__":
    import json
    print("BONOBO:")
    print(json.dumps(BONOBO_DATA, indent=2, default=str))
    print("\nCHIMP:")
    print(json.dumps(CHIMP_DATA, indent=2, default=str))
