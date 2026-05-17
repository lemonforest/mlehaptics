"""
Spike #44 round 2 - Cross-clade signature analysis.

Apply Class K/L/C/E/I signatures to 7 species:
- Bonobo (matriarchal-via-coalition; male-philopatric; great ape)
- Chimp (patriarchal; male-philopatric; great ape) [CONTROL]
- African elephant (matriarchal-by-age; female-philopatric; mega-mammal)
- Orca (matriarchal-by-age; BIPATERNAL-philopatric; cetacean)
- Spotted hyena (matriarchal-by-coalition; female-philopatric; carnivore)
- Ring-tailed lemur (matriarchal-by-individual-dominance; female-philopatric; strepsirrhine)
- Naked mole-rat (matriarchal-by-eusociality; high inbreeding; eusocial rodent) [BOUNDARY]

Build fingerprint vector per species; cluster across species; identify which axis
the clustering best matches (sex / coalition / ecology / kinship).

Discipline: closed-form algebra. No SGD. No free parameters per-species.
"""

import math
import json
from pathlib import Path
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).parent))

from spike_44_r2_carry_forward import BONOBO_DATA, CHIMP_DATA
from spike_44_r2_elephant_data import ELEPHANT_DATA
from spike_44_r2_orca_data import ORCA_DATA
from spike_44_r2_hyena_data import HYENA_DATA
from spike_44_r2_lemur_data import LEMUR_DATA
from spike_44_r2_mole_rat_data import MOLE_RAT_DATA

OUT_DIR = Path(r"D:\temp\spike_44_r2")
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ===========================================================================
# Encoding to numerical fingerprint
# ===========================================================================

# Lethal-aggression encoded on log10 scale: 0 = none documented (defined-zero),
# 1 = rare (~0.1-1 per 100k/y), 2 = moderate (~10-100), 3 = high (~100-1000)
# Negative values for "rare but >0 in qualitative terms"
LETHAL_AGG_QUALITATIVE = {
    "defined_zero": 0.0,
    "essentially_zero_in_situ": 0.0,
    "very_rare": 1.0,
    "rare_to_moderate": 2.0,
    "documented_but_rare": 1.5,
    "documented_clan_wars": 2.5,  # hyena boundary wars - cited in Wrangham 2006 alongside chimp
    "documented": 2.0,
    "high_at_succession": 3.0,
    "high_infanticide": 2.5,  # hyena female infanticide 24% of juv mortality
    "rare": 1.0,
}


def _resolve_lethal(value):
    """Return lethal-aggression value on log10-per-100k-y scale."""
    if isinstance(value, (int, float)):
        if value == 0.0:
            return 0.0
        return float(math.log10(value + 1))
    if isinstance(value, str):
        for k, v in LETHAL_AGG_QUALITATIVE.items():
            if k in value:
                return v
    return None


def species_fingerprint(species_data):
    """Build a numerical signature fingerprint vector.

    Components:
      f1 = Class L intergroup-lethal-rate (log10 scale)
      f2 = Class L intragroup-lethal-rate (log10 scale)
      f3 = Class K female-dominant-intersex (0/1)
      f4 = Class K matriarchal (0/1)
      f5 = Class K all-females-outrank-all-males (0/1)
      f6 = Class L intersex-coalition (0/1)
      f7 = Class L female-coalition-for-dominance (0/1)
      f8 = Class L coalitions-high-frequency (0/1)
      f9 = Class E shares-food (0/1)
      f10 = Class E shares-tools (0/1)
      f11 = Class E allomothering (0/1)
      f12 = Class I multigenerational (0/1)
      f13 = Class I post-reproductive-longevity (0/1)
      f14 = kinship encoding: 0=patrilineal, 1=matrilineal-female-philopatric,
            2=both-natally-philopatric, 3=male-philopatric, 4=high-inbreeding-colony
      f15 = ecology: 0=arboreal/terrestrial-primate, 1=mega-mammal, 2=cetacean,
            3=carnivore, 4=subterranean-eusocial
    """
    s = species_data
    cat = s.get("sharing_catalog", {})

    # Intersex coalition: bonobo and hyena are true; others false
    intersex_coalition = s.get("intersex_coalitions_observed", False)

    kinship_map = {
        "male_philopatric": 3,
        "matrilineal_philopatry": 1,
        "matrilineal_both_sexes_natal_philopatric": 2,
        "matrilineal_female_philopatric": 1,
        "female_philopatric": 1,
        "extremely_high_inbreeding_within_colony": 4,
    }
    # Chimp / bonobo are male-philopatric; others see species_data
    if s["common"] == "Chimpanzee":
        kinship_code = 3
    elif s["common"] == "Bonobo":
        kinship_code = 3  # ALSO male-philopatric (despite female coalitions)
    else:
        kinship_code = kinship_map.get(s.get("kinship", ""), 3)

    # Ecology: simple coarse encoding
    ecology_map = {
        "Pan troglodytes": 0,  # primate
        "Pan paniscus": 0,
        "Loxodonta africana": 1,  # mega-mammal
        "Orcinus orca": 2,  # cetacean
        "Crocuta crocuta": 3,  # carnivore
        "Lemur catta": 0,  # primate
        "Heterocephalus glaber": 4,  # eusocial rodent
    }
    ecology_code = ecology_map.get(s["species"], 0)

    fp = {
        "species": s["species"],
        "common": s["common"],
        "f1_intergroup_lethal_log10": _resolve_lethal(s.get("intergroup_lethal_rate_per_100k_y", 0)),
        "f2_intragroup_lethal_log10": _resolve_lethal(s.get("intragroup_lethal_rate_per_100k_y", 0)),
        "f3_female_dominant_intersex": int(s.get("female_dominant_intersex", False)),
        "f4_matriarchal": int(s.get("matriarchal", False)),
        "f5_all_females_outrank_males": int(s.get("all_females_outrank_all_males", False)),
        "f6_intersex_coalition": int(intersex_coalition),
        "f7_female_coalition_dominance": int(s.get("female_coalitions_for_dominance", False)),
        "f8_coalitions_high_frequency": int(s.get("coalitions_high_frequency", False)),
        "f9_shares_food": int(cat.get("food", False)),
        "f10_shares_tools": int(cat.get("tools", False)),
        "f11_allomothering": int(cat.get("care_allomothering", False)),
        "f12_multigenerational": int(s.get("multigenerational_groups", False)
                                     or s.get("multigenerational_pods", False)
                                     or s.get("multigenerational_clans", False)
                                     or s.get("multigenerational_troops", False)
                                     or s.get("multigenerational_colonies", False)),
        "f13_post_reproductive_longevity": int(bool(s.get("post_reproductive_longevity_present", False)
                                                     or s.get("post_reproductive_grandmother_effect", False))),
        "f14_kinship_code": kinship_code,
        "f15_ecology_code": ecology_code,
    }
    return fp


# ===========================================================================
# Cross-clade signature application
# ===========================================================================

def all_fingerprints():
    return [
        species_fingerprint(BONOBO_DATA),
        species_fingerprint(CHIMP_DATA),
        species_fingerprint(ELEPHANT_DATA),
        species_fingerprint(ORCA_DATA),
        species_fingerprint(HYENA_DATA),
        species_fingerprint(LEMUR_DATA),
        species_fingerprint(MOLE_RAT_DATA),
    ]


# ===========================================================================
# Cross-clade clustering (computational, deterministic)
# ===========================================================================

def fingerprint_matrix(fps, feature_keys=None):
    """Return (n_species, n_features) matrix in deterministic feature order."""
    if feature_keys is None:
        feature_keys = [k for k in fps[0].keys() if k.startswith("f")]
    M = np.zeros((len(fps), len(feature_keys)))
    for i, fp in enumerate(fps):
        for j, key in enumerate(feature_keys):
            val = fp.get(key)
            if val is None:
                M[i, j] = 0.0
            else:
                M[i, j] = float(val)
    return M, feature_keys


def pairwise_distance_matrix(M):
    """Compute Euclidean pairwise distances between species fingerprints.
    Returns (n_species, n_species) symmetric matrix."""
    n = M.shape[0]
    D = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            D[i, j] = float(np.linalg.norm(M[i] - M[j]))
    return D


def closest_pairs(D, species_names):
    """Return sorted list of (sp_i, sp_j, distance) for non-diagonal pairs."""
    pairs = []
    n = D.shape[0]
    for i in range(n):
        for j in range(i+1, n):
            pairs.append((species_names[i], species_names[j], D[i, j]))
    pairs.sort(key=lambda x: x[2])
    return pairs


# ===========================================================================
# Hypothesis-specific feature subsets
# ===========================================================================

# H_sex: only sex/matriarchal features
H_SEX_FEATURES = ["f3_female_dominant_intersex", "f4_matriarchal", "f5_all_females_outrank_males"]

# H_coalition: coalition features
H_COALITION_FEATURES = ["f6_intersex_coalition", "f7_female_coalition_dominance", "f8_coalitions_high_frequency"]

# H_ecology: ecology + intergroup lethal aggression (which is shaped by niche)
H_ECOLOGY_FEATURES = ["f1_intergroup_lethal_log10", "f2_intragroup_lethal_log10",
                       "f9_shares_food", "f10_shares_tools", "f15_ecology_code"]

# H_kinship: kinship + multigenerational features
H_KINSHIP_FEATURES = ["f12_multigenerational", "f13_post_reproductive_longevity", "f14_kinship_code",
                       "f11_allomothering"]


def hypothesis_test(fps, feature_subset_name, feature_subset):
    """Test which species cluster together under given feature subset.
    Returns the closest 3 pairs.
    A 'good' hypothesis is one where matriarchal species cluster together under its
    feature subset.
    """
    M, _ = fingerprint_matrix(fps, feature_subset)
    species_names = [fp["common"] for fp in fps]
    D = pairwise_distance_matrix(M)
    pairs = closest_pairs(D, species_names)
    return {
        "hypothesis": feature_subset_name,
        "n_features": len(feature_subset),
        "closest_3_pairs": pairs[:3],
        "matriarchal_clades": ["Bonobo", "African savanna elephant", "Killer whale / orca",
                                "Spotted hyena", "Ring-tailed lemur", "Naked mole-rat"],
        "control_clade": "Chimpanzee",
        "pairs_sample": pairs[:10],
    }


def matriarchal_cohesion_score(fps, feature_subset, matriarchal_names, control_names):
    """How well-clustered are matriarchal species vs control under this feature subset?
    Score = (mean distance matriarchal-to-control) - (mean distance matriarchal-to-matriarchal)
    Higher = matriarchal cluster tighter under this hypothesis."""
    M, _ = fingerprint_matrix(fps, feature_subset)
    species_names = [fp["common"] for fp in fps]
    name_to_idx = {name: i for i, name in enumerate(species_names)}

    matri_idx = [name_to_idx[n] for n in matriarchal_names if n in name_to_idx]
    ctrl_idx = [name_to_idx[n] for n in control_names if n in name_to_idx]

    if len(matri_idx) < 2 or len(ctrl_idx) < 1:
        return None

    D = pairwise_distance_matrix(M)

    intra_dists = []
    for i in matri_idx:
        for j in matri_idx:
            if i < j:
                intra_dists.append(D[i, j])
    cross_dists = []
    for i in matri_idx:
        for j in ctrl_idx:
            cross_dists.append(D[i, j])

    intra_mean = float(np.mean(intra_dists)) if intra_dists else 0.0
    cross_mean = float(np.mean(cross_dists)) if cross_dists else 0.0
    return {
        "intra_matriarchal_mean_distance": intra_mean,
        "matriarchal_to_control_mean_distance": cross_mean,
        "cohesion_score": cross_mean - intra_mean,
        "n_intra_pairs": len(intra_dists),
        "n_cross_pairs": len(cross_dists),
    }


# ===========================================================================
# RUN
# ===========================================================================
def main():
    records = []
    fps = all_fingerprints()

    # Write each species fingerprint
    for fp in fps:
        records.append({"kind": "species_fingerprint", **fp})

    # Full-feature clustering
    M_full, full_keys = fingerprint_matrix(fps)
    species_names = [fp["common"] for fp in fps]
    D_full = pairwise_distance_matrix(M_full)
    pairs_full = closest_pairs(D_full, species_names)
    records.append({
        "kind": "cross_clade_clustering_FULL",
        "n_species": len(fps),
        "n_features": len(full_keys),
        "feature_keys": full_keys,
        "closest_5_pairs": pairs_full[:5],
        "all_pairs": pairs_full,
    })

    # Hypothesis tests
    matriarchal_names = ["Bonobo", "African savanna elephant", "Killer whale / orca",
                          "Spotted hyena", "Ring-tailed lemur"]  # exclude mole-rat as boundary
    control_names = ["Chimpanzee"]

    for h_name, h_feats in [("H_sex", H_SEX_FEATURES),
                              ("H_coalition", H_COALITION_FEATURES),
                              ("H_ecology", H_ECOLOGY_FEATURES),
                              ("H_kinship", H_KINSHIP_FEATURES)]:
        result = hypothesis_test(fps, h_name, h_feats)
        records.append({"kind": "hypothesis_test", **result})
        cohesion = matriarchal_cohesion_score(fps, h_feats, matriarchal_names, control_names)
        if cohesion:
            records.append({"kind": "matriarchal_cohesion_score", "hypothesis": h_name, **cohesion})

    # Include mole-rat version
    for h_name, h_feats in [("H_sex", H_SEX_FEATURES),
                              ("H_coalition", H_COALITION_FEATURES),
                              ("H_ecology", H_ECOLOGY_FEATURES),
                              ("H_kinship", H_KINSHIP_FEATURES)]:
        cohesion = matriarchal_cohesion_score(
            fps, h_feats,
            matriarchal_names + ["Naked mole-rat"],
            control_names
        )
        if cohesion:
            records.append({"kind": "matriarchal_cohesion_score_with_mole_rat", "hypothesis": h_name, **cohesion})

    # Per-feature anomaly check: which features actually discriminate?
    # For each feature, compute (mean for matriarchal) - (mean for control)
    matri_idx = [i for i, fp in enumerate(fps) if fp["common"] in matriarchal_names]
    ctrl_idx = [i for i, fp in enumerate(fps) if fp["common"] in control_names]
    for j, key in enumerate(full_keys):
        m_vals = [fps[i].get(key, 0) or 0 for i in matri_idx]
        c_vals = [fps[i].get(key, 0) or 0 for i in ctrl_idx]
        m_mean = float(np.mean(m_vals)) if m_vals else 0.0
        c_mean = float(np.mean(c_vals)) if c_vals else 0.0
        records.append({
            "kind": "feature_discrimination",
            "feature": key,
            "matriarchal_mean": m_mean,
            "control_mean": c_mean,
            "difference": m_mean - c_mean,
            "discriminates": abs(m_mean - c_mean) > 0.5,
        })

    return records


if __name__ == "__main__":
    records = main()
    out_path = OUT_DIR / "spike_44_r2_records_2026-05-17.ndjson"
    with open(out_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, default=str) + "\n")
    print(f"Wrote {len(records)} records to {out_path}")
    for r in records:
        kind = r.get("kind", "?")
        sp_or_hyp = r.get("common", r.get("hypothesis", r.get("feature", "")))
        print(f"  [{kind:42s}] {sp_or_hyp}")
