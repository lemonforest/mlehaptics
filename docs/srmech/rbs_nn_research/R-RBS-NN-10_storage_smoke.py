"""R-RBS-NN-10 — Two-tier storage smoke test

Demonstrates the full operational cycle of the two-tier RBS-NN storage:
  encode → learn associations → retrieve → decay (forget) → rehearse → recover

Tests against an 11-concept "kitchen knowledge graph" with 8 associations.
"""
import json
import time
from pathlib import Path
import sys
import importlib.util

import numpy as np

# Local module load (filename contains hyphens)
spec = importlib.util.spec_from_file_location(
    "two_tier_storage", Path(__file__).parent / "R-RBS-NN-10_two_tier_storage.py"
)
mod = importlib.util.module_from_spec(spec)
sys.modules["two_tier_storage"] = mod  # Register before exec for Python 3.14 dataclass introspection
spec.loader.exec_module(mod)
TwoTierRBSNNStorage = mod.TwoTierRBSNNStorage

from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION


def divider(s):
    print()
    print("=" * 72)
    print(s)
    print("=" * 72)


def main():
    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}")

    # Initialize storage
    storage = TwoTierRBSNNStorage(D=8192, seed=42)
    print(f"\nInitialized: {storage}")

    # Concepts to encode (a "kitchen knowledge graph")
    # Mix of sectors to demonstrate chirality-axis use
    CONCEPTS = [
        ("apple",   0),  # RH+ visible matter (default)
        ("orange",  0),
        ("knife",   0),
        ("fork",    0),
        ("plate",   0),
        # Chirality-bearing concepts (chiral molecules / mirror)
        ("L_amino",  0),  # canonical biological homochirality (RH+)
        ("D_amino",  2),  # mirror (LH+)
        # Plasticity-tagged "memory" concepts
        ("breakfast",   0),
        ("lunch",       0),
        ("yesterday",   0),
        ("last_week",   0),
    ]

    divider("ENCODE — concepts into Tier 1 (Klein-4)")
    for token, sector in CONCEPTS:
        c = storage.encode_concept(token, chirality_sector=sector)
        print(f"  {token:<12} → sector {sector}, hv[:8] = {c.hv[:8].tolist()}")

    print(f"\nTier 1 sector distribution: {storage.sector_distribution()}")

    # Verify CPT mirror works for the chiral pair
    cpt_L = storage.cpt_mirror("L_amino")
    cpt_D = storage.cpt_mirror("D_amino")
    print(f"\nCPT mirror check (chirality-axis op):")
    print(f"  L_amino hv[:8]:     {storage.tier1['L_amino'].hv[:8].tolist()}")
    print(f"  L_amino mirror[:8]: {cpt_L[:8].tolist()}")

    divider("LEARN — associations into Tier 2 (Polar)")
    ASSOCIATIONS = [
        ("apple", "orange"),         # fruits
        ("knife", "fork"),           # utensils
        ("plate", "knife"),          # tableware
        ("plate", "fork"),
        ("L_amino", "D_amino"),     # chiral pair (cross-sector)
        ("breakfast", "apple"),
        ("breakfast", "orange"),
        ("lunch", "plate"),
    ]
    for a, b in ASSOCIATIONS:
        s = storage.learn_association(a, b, plasticity_density=0.67)
        print(f"  {a:<12} ↔ {b:<12}  density={s.current_density:.3f}")

    print(f"\nStorage state: {storage}")
    att = storage.density_attestation()
    print(f"Density attestation: {att}")

    divider("RETRIEVE — associated concepts via Tier 2")
    for query in ["apple", "knife", "L_amino", "breakfast", "plate"]:
        results = storage.retrieve_associated(query, top_k=5, threshold=0.55)
        results_str = ", ".join(f"{t} ({s:.3f})" for t, s in results)
        print(f"  retrieve_associated('{query}') → [{results_str}]")

    divider("FORGET — apply decay to Tier 2")
    for step in range(3):
        report = storage.forget_step(decay_rate=0.15)
        att = storage.density_attestation()
        print(
            f"  Step {step+1}: decayed {report['decayed_synapses']}/{report['total_synapses']} synapses; "
            f"mean density now {att['mean_synapse_density']:.3f}"
        )

    # Show retrieval degradation
    print("\nRetrieval AFTER decay (expect weaker signals):")
    for query in ["apple", "knife", "L_amino", "breakfast"]:
        results = storage.retrieve_associated(query, top_k=5, threshold=0.50)
        if results:
            results_str = ", ".join(f"{t} ({s:.3f})" for t, s in results)
            print(f"  '{query}' → [{results_str}]")
        else:
            print(f"  '{query}' → [DEGRADED below threshold]")

    divider("REHEARSE — strengthen specific bindings")
    # Rehearse the chiral pair + breakfast/apple
    for a, b in [("L_amino", "D_amino"), ("breakfast", "apple"), ("knife", "fork")]:
        s = storage.rehearse(a, b, recovery_fraction=0.5)
        if s:
            print(
                f"  rehearse({a}, {b}): density {s.current_density:.3f}, "
                f"reinforce_count={s.reinforce_count}"
            )

    att = storage.density_attestation()
    print(f"\nDensity attestation after rehearsal: {att}")

    print("\nRetrieval AFTER rehearsal (expect recovered signal for rehearsed pairs):")
    for query in ["apple", "knife", "L_amino", "breakfast"]:
        results = storage.retrieve_associated(query, top_k=5, threshold=0.50)
        if results:
            results_str = ", ".join(f"{t} ({s:.3f})" for t, s in results)
            print(f"  '{query}' → [{results_str}]")
        else:
            print(f"  '{query}' → [no recovery]")

    divider("CHIRALITY-AXIS — cross-sector retrieval (F139 pattern)")
    # The L_amino ↔ D_amino association lives in Tier 2.
    # Query with L_amino should retrieve D_amino (the chiral mirror).
    # This demonstrates substrate-level chirality preservation through the bridge.
    result_chiral = storage.retrieve_associated("L_amino", top_k=3, threshold=0.0)
    print(f"  retrieve_associated('L_amino') → {result_chiral}")
    print("  (D_amino should be present as the chiral-pair partner)")

    # Output JSON summary
    summary = {
        "srmech_version": SRMECH_VERSION,
        "has_native": HAS_NATIVE,
        "D": storage.D,
        "n_concepts": len(storage.tier1),
        "n_synapses": len(storage.tier2),
        "sector_distribution": storage.sector_distribution(),
        "final_density_attestation": storage.density_attestation(),
        "synapse_history": [
            {
                "pair": list(key),
                "initial_density": s.initial_density,
                "current_density": s.current_density,
                "reinforce_count": s.reinforce_count,
            }
            for key, s in storage.tier2.items()
        ],
    }
    out_path = Path(__file__).parent / "R-RBS-NN-10_results.json"
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"\nResults: {out_path}")
    print(f"\nFinal: {storage}")


if __name__ == "__main__":
    main()
