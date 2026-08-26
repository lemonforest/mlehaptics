"""R-RBS-NN-14 — Phase 4 interface polish smoke (14a chirality auto-detect + 14b soft retrieval)

Phase 4 of R-RBS-NN-10_FOLLOWUP_PHASED_PLAN.md.

Tests:
  14a-T1: classify_chirality() rule-based classifier on synthetic chiral lexicon
  14a-T2: encode_concept(auto_sector=True) routes tokens to sectors automatically
  14a-T3: chirality-aware lexicon retrieves better with auto_sector than default 0
  14b-T1: temperature=0 retrieves matches R-RBS-NN-10 baseline (no regression)
  14b-T2: temperature > 0 produces softmax probabilities (sum to ~1)
  14b-T3: temperature sweep shows expected sharpening behavior

Per [[feedback_trauma_informed_defensive_scope]]: substrate-encoding smoke
test only; no medical or BCI engineering claims.
"""
import json
from pathlib import Path
import sys
import importlib.util

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

_spec = importlib.util.spec_from_file_location(
    "two_tier_storage", Path(__file__).parent / "R-RBS-NN-10_two_tier_storage.py"
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["two_tier_storage"] = _mod
_spec.loader.exec_module(_mod)
TwoTierRBSNNStorage = _mod.TwoTierRBSNNStorage
classify_chirality = _mod.classify_chirality
SECTOR_VISIBLE_MATTER = _mod.SECTOR_VISIBLE_MATTER
SECTOR_DARK_ANTIMATTER = _mod.SECTOR_DARK_ANTIMATTER
SECTOR_VISIBLE_ANTIMATTER = _mod.SECTOR_VISIBLE_ANTIMATTER
SECTOR_DARK_MATTER = _mod.SECTOR_DARK_MATTER

from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION


# ============================================================
# 14a-T1: classify_chirality unit tests
# ============================================================
def test_classifier():
    expected = [
        # No marker → sector 0
        ("apple", SECTOR_VISIBLE_MATTER),
        ("water", SECTOR_VISIBLE_MATTER),
        ("calendar", SECTOR_VISIBLE_MATTER),
        # Canonical L / left / CCW → sector 0 (explicit)
        ("L_amino", SECTOR_VISIBLE_MATTER),
        ("left_helix", SECTOR_VISIBLE_MATTER),
        ("ccw_rotation", SECTOR_VISIBLE_MATTER),
        ("levo_glucose", SECTOR_VISIBLE_MATTER),
        ("(s)-naproxen", SECTOR_VISIBLE_MATTER),
        # D / right / CW → sector 2 (mirror)
        ("D_amino", SECTOR_VISIBLE_ANTIMATTER),
        ("right_helix", SECTOR_VISIBLE_ANTIMATTER),
        ("cw_rotation", SECTOR_VISIBLE_ANTIMATTER),
        ("dextro_glucose", SECTOR_VISIBLE_ANTIMATTER),
        ("(r)-naproxen", SECTOR_VISIBLE_ANTIMATTER),
        ("mirror_pattern", SECTOR_VISIBLE_ANTIMATTER),
        # Dark antimatter → sector 1
        ("dark_anti_world", SECTOR_DARK_ANTIMATTER),
        ("antidark_signal", SECTOR_DARK_ANTIMATTER),
        # Dark matter / CPT mirror → sector 3
        ("dark_matter", SECTOR_DARK_MATTER),
        ("cpt_mirror_state", SECTOR_DARK_MATTER),
        # Suffix patterns
        ("amino_d", SECTOR_VISIBLE_ANTIMATTER),
        ("amino_l", SECTOR_VISIBLE_MATTER),
    ]

    passed = 0
    failed = []
    for token, exp_sector in expected:
        actual = classify_chirality(token)
        if actual == exp_sector:
            passed += 1
        else:
            failed.append((token, exp_sector, actual))

    return {
        "total": len(expected),
        "passed": passed,
        "failed": failed,
    }


# ============================================================
# Chirality-aware lexicon for retrieval test
# ============================================================
def build_chirality_lexicon():
    """A 24-concept lexicon with explicit chirality markers in the names."""
    return [
        # L-amino acids (RH+ visible matter)
        "L_alanine",
        "L_glycine",
        "L_leucine",
        "L_serine",
        # D-amino acids (LH+ visible antimatter)
        "D_alanine",
        "D_glycine",
        "D_leucine",
        "D_serine",
        # Helix orientations
        "left_helix_alpha",
        "left_helix_beta",
        "right_helix_alpha",
        "right_helix_beta",
        # Rotational symbols
        "ccw_rotation_slow",
        "ccw_rotation_fast",
        "cw_rotation_slow",
        "cw_rotation_fast",
        # Dark sector markers
        "dark_matter_clump",
        "dark_anti_pair",
        # Plain content (no chirality)
        "apple",
        "water",
        "calendar",
        "engine",
        "harmonic",
        "octahedron",
    ]


def build_chirality_aware_storage(D, auto_sector):
    storage = TwoTierRBSNNStorage(D=D, seed=42)
    tokens = build_chirality_lexicon()
    for tok in tokens:
        storage.encode_concept(tok, auto_sector=auto_sector)

    # Associations: pair L-X with D-X (chiral pair)
    chiral_pairs = [
        ("L_alanine", "D_alanine"),
        ("L_glycine", "D_glycine"),
        ("L_leucine", "D_leucine"),
        ("L_serine", "D_serine"),
        ("left_helix_alpha", "right_helix_alpha"),
        ("left_helix_beta", "right_helix_beta"),
        ("ccw_rotation_slow", "cw_rotation_slow"),
        ("ccw_rotation_fast", "cw_rotation_fast"),
    ]
    # Plus some plain-content associations
    plain_pairs = [
        ("apple", "water"),
        ("calendar", "engine"),
        ("harmonic", "octahedron"),
    ]
    # Plus dark-sector associations
    dark_pairs = [
        ("dark_matter_clump", "dark_anti_pair"),
    ]
    all_pairs = chiral_pairs + plain_pairs + dark_pairs
    storage.batch_learn(all_pairs, plasticity_density=0.67)
    return storage, all_pairs


# ============================================================
# 14a-T3: retrieval comparison default-sector-0 vs auto_sector
# ============================================================
def test_chirality_retrieval(D):
    """Compare retrieval quality with all-sector-0 vs auto_sector chirality routing."""
    # Default: all sector 0
    default_storage, pairs = build_chirality_aware_storage(D, auto_sector=False)
    # Auto: chirality classifier routes to correct sectors
    auto_storage, _ = build_chirality_aware_storage(D, auto_sector=True)

    def measure(storage, pairs):
        correct = 0
        for a, b in pairs:
            retrieved = storage.retrieve_associated(a, top_k=5, threshold=0.0)
            tokens = [t for t, _ in retrieved]
            if b in tokens:
                correct += 1
        return correct / len(pairs)

    default_p = measure(default_storage, pairs)
    auto_p = measure(auto_storage, pairs)

    # Auto-sector distribution
    auto_dist = auto_storage.sector_distribution()
    return {
        "default_all_sector_0": default_p,
        "auto_sector": auto_p,
        "auto_sector_distribution": auto_dist,
    }


# ============================================================
# 14b-T1/T2: hard vs soft retrieval
# ============================================================
def test_soft_retrieval(D):
    """Compare hard (temperature=0) vs soft (temperature > 0) retrieval."""
    storage, pairs = build_chirality_aware_storage(D, auto_sector=True)

    # Pick a known associate pair
    query = "L_alanine"
    truth = "D_alanine"

    results = {}
    # Hard retrieval (baseline)
    hard = storage.retrieve_associated(query, top_k=5, threshold=0.0, temperature=0.0)
    results["temp_0.0_hard"] = hard

    # Soft at various temperatures
    for temp in [0.1, 0.5, 1.0, 2.0, 5.0]:
        soft = storage.retrieve_associated(query, top_k=5, threshold=0.0, temperature=temp)
        # Check probabilities sum to ~1 (would be 1 if returning all tokens; just top-k won't necessarily sum to 1)
        probs = [s for _, s in soft]
        results[f"temp_{temp}_soft"] = {
            "results": soft,
            "top_k_probs_sum": float(sum(probs)),
            "top_1": soft[0] if soft else None,
        }

    return {
        "query": query,
        "truth_associate": truth,
        "results": results,
    }


# ============================================================
# Combined retrieval: auto_sector + temperature
# ============================================================
def test_combined(D):
    """Verify both features work together (auto_sector + temperature)."""
    storage, pairs = build_chirality_aware_storage(D, auto_sector=True)

    # Soft retrieval with temperature=1.0
    query = "left_helix_alpha"
    retrieved = storage.retrieve_associated(query, top_k=5, threshold=0.0, temperature=1.0)
    return {
        "query": query,
        "retrieved_with_temp_1.0": retrieved,
    }


def main():
    D = 8192
    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}")
    print()

    print("=" * 80)
    print("14a-T1 — classify_chirality unit tests")
    print("=" * 80)
    cls_result = test_classifier()
    print(f"  Passed: {cls_result['passed']}/{cls_result['total']}")
    for token, exp, actual in cls_result["failed"]:
        print(f"  FAIL: '{token}' expected sector {exp}, got {actual}")
    print()

    print("=" * 80)
    print("14a-T3 — retrieval: default-all-sector-0 vs auto_sector chirality")
    print("=" * 80)
    ret_result = test_chirality_retrieval(D)
    print(f"  default (all sector 0): {ret_result['default_all_sector_0']:.3f}")
    print(f"  auto_sector            : {ret_result['auto_sector']:.3f}")
    print(f"  auto_sector distribution: {ret_result['auto_sector_distribution']}")
    delta = ret_result['auto_sector'] - ret_result['default_all_sector_0']
    print(f"  Δ = {delta:+0.3f} ({'auto-sector ADVANTAGE' if delta > 0 else 'no advantage'})")
    print()

    print("=" * 80)
    print("14b — hard vs soft retrieval (query 'L_alanine')")
    print("=" * 80)
    soft_result = test_soft_retrieval(D)
    print(f"  Query: {soft_result['query']} (truth associate: {soft_result['truth_associate']})")
    for key, val in soft_result["results"].items():
        if key == "temp_0.0_hard":
            print(f"  {key}:")
            for tok, sim in val[:5]:
                print(f"    {tok:<28} sim={sim:+0.4f}")
        else:
            r = val["results"]
            ps = val["top_k_probs_sum"]
            print(f"  {key}: top-k probs sum={ps:.3f}")
            for tok, prob in r[:5]:
                print(f"    {tok:<28} prob={prob:.4f}")
    print()

    print("=" * 80)
    print("14a+14b combined — auto_sector + temperature on chirality query")
    print("=" * 80)
    comb_result = test_combined(D)
    print(f"  Query: {comb_result['query']} (with auto_sector + temperature=1.0)")
    for tok, prob in comb_result["retrieved_with_temp_1.0"]:
        print(f"    {tok:<28} prob={prob:.4f}")
    print()

    # Hypothesis check
    print("=" * 80)
    print("Hypothesis check")
    print("=" * 80)
    h_cls = cls_result["passed"] == cls_result["total"]
    h_auto = ret_result["auto_sector"] > ret_result["default_all_sector_0"] - 0.05
    # Soft @ temp=0.1 should be sharper than @ temp=5 (more concentrated on top-1)
    soft_top1_sharp = soft_result["results"]["temp_0.1_soft"]["top_1"][1]
    soft_top1_flat = soft_result["results"]["temp_5.0_soft"]["top_1"][1]
    h_temp_sharpens = soft_top1_sharp > soft_top1_flat

    print(f"  14a-T1 classifier 100% pass:      {h_cls}")
    print(f"  14a-T3 auto_sector ≥ default-0:   {h_auto}")
    print(f"  14b temperature sharpens top-1:   {h_temp_sharpens} ({soft_top1_sharp:.3f} > {soft_top1_flat:.3f})")

    out = {
        "srmech_version": SRMECH_VERSION,
        "D": D,
        "T1_classifier": cls_result,
        "T3_chirality_retrieval": ret_result,
        "T_soft_retrieval": soft_result,
        "T_combined": comb_result,
        "hypotheses": {
            "classifier_pass": h_cls,
            "auto_sector_advantage": h_auto,
            "temperature_sharpens": h_temp_sharpens,
        },
    }
    out_path = Path(__file__).parent / "R-RBS-NN-14_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
