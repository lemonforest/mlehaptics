"""R-RBS-LM-99 — Cross-sector retrieval at scale (F132 §7 load-bearing test)

Path 3/6 of the wishlist-gated research resume.

The load-bearing test for F132 Klein-4 HDC: does chirality-axis encoding
let us recover the dark-sector-conjugate of a concept from visible-sector
storage?

Methodology refinements per F138 §5:
  1. Factorise content from chirality: independent klein-4 vector PER concept;
     sector tag is a SEPARATE XOR layer (cleanly separable)
  2. D sweep: 1024, 4096, 16384 - show signal vs scale
  3. N sweep: 8, 16, 32, 64 - show capacity vs load
  4. Test cross-sector retrieval directly: encode concept C with sector A,
     query with sector B (B != A); does the result resemble C's chirality-flipped
     manifestation?

Key tests:
  T1. Same-sector retrieval: encode with sector A, query with sector A
      -> should recover original concept (above-random sim)
  T2. Cross-sector retrieval: encode with sector A, query with sector B (B = A flipped)
      -> should recover CPT-mirrored concept (chirality-axis prediction)
  T3. Discrimination: T1 sim > T2 sim > random pair sim
      -> confirms chirality axis is operational

Cross-references:
  - F132 §7 (cross-sector retrieval test specification)
  - F135 (substrate vs shadow; substrate-side chirality)
  - F137 (capacity calibration at moderate load)
  - F138 (cascade composition; encoding methodology improvements §5)
"""
import json
import time
from pathlib import Path

import numpy as np

from srmech.amsc import hdc
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION


# Sector mask helper: 4 sectors per F132 §3 mapping
SECTOR_NAMES = {
    0: "RH+ visible matter",
    1: "RH- dark antimatter",
    2: "LH+ visible antimatter",
    3: "LH- dark matter",
}

# CPT mirror: sector 0 <-> sector 3; sector 1 <-> sector 2
CPT_MIRROR = {0: 3, 1: 2, 2: 1, 3: 0}


def encode_concept(concept_seed: int, D: int, rng_for_content) -> np.ndarray:
    """Encode a concept as random Klein-4 hypervector (deterministic from seed).

    The concept's identity is in the random pattern; chirality tag is applied separately.
    """
    rng = np.random.default_rng(concept_seed)
    return hdc.klein4_random(D, rng)


def apply_sector(hv: np.ndarray, sector: int) -> np.ndarray:
    """Apply chirality-axis tag (XOR with constant sector mask). Cleanly separable."""
    D = len(hv)
    sector_mask = np.full(D, sector, dtype=np.uint8)
    return hdc.klein4_bind(hv, sector_mask)


def random_baseline_klein4(D: int, N_trials: int, rng) -> float:
    """Mean random-pair klein-4 similarity at this D."""
    sims = []
    for _ in range(N_trials):
        a = hdc.klein4_random(D, rng)
        b = hdc.klein4_random(D, rng)
        sims.append(float(hdc.klein4_similarity(a, b)))
    return float(np.mean(sims))


def run_scale_test(D: int, N_concepts: int, rng):
    """Run one (D, N_concepts) configuration. Return same-sector and cross-sector sims."""
    # Generate N_concepts random concept vectors, assign sectors round-robin
    concepts = []
    sectors = []
    for i in range(N_concepts):
        concepts.append(encode_concept(concept_seed=i, D=D, rng_for_content=rng))
        sectors.append(i % 4)

    # Tag each concept with its sector; bundle ALL into composite
    tagged = [apply_sector(c, s) for c, s in zip(concepts, sectors)]
    composite = hdc.klein4_bundle(*tagged)

    # T1: Same-sector retrieval (query with original sector; should recover concept)
    same_sector_sims = []
    # T2: Cross-sector retrieval (query with CPT-mirrored sector; should recover CPT-mirrored concept)
    cross_sector_sims = []

    for i, c in enumerate(concepts):
        own_sector = sectors[i]
        cpt_sector = CPT_MIRROR[own_sector]

        # Same-sector query: unbind composite with own_sector mask
        same_unbound = hdc.klein4_unbind(composite, np.full(D, own_sector, dtype=np.uint8))
        same_sim = float(hdc.klein4_similarity(same_unbound, c))
        same_sector_sims.append(same_sim)

        # Cross-sector query: unbind composite with cpt_sector mask
        cross_unbound = hdc.klein4_unbind(composite, np.full(D, cpt_sector, dtype=np.uint8))
        # We compare to the CPT-mirrored version of the concept
        c_mirrored = apply_sector(c, 3)  # full CPT flip = XOR with 3
        cross_sim = float(hdc.klein4_similarity(cross_unbound, c_mirrored))
        cross_sector_sims.append(cross_sim)

    return {
        "same_sector_mean": float(np.mean(same_sector_sims)),
        "same_sector_std": float(np.std(same_sector_sims)),
        "cross_sector_mean": float(np.mean(cross_sector_sims)),
        "cross_sector_std": float(np.std(cross_sector_sims)),
    }


def main():
    rng = np.random.default_rng(42)
    D_sweep = [1024, 4096, 16384]
    N_sweep = [8, 16, 32, 64]
    baseline_trials = 100

    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}")
    print()

    # Random baselines per D
    baselines = {}
    for D in D_sweep:
        baselines[D] = random_baseline_klein4(D, baseline_trials, rng)
        print(f"  klein-4 random baseline at D={D}: {baselines[D]:.4f}")
    print()

    # Run all configs
    print(f"{'D':>6} | {'N':>4} | {'same-sector':>14} | {'cross-sector':>14} | {'above-rand same':>16} | {'above-rand cross':>16}")
    print("-" * 100)

    results = []
    for D in D_sweep:
        for N in N_sweep:
            t0 = time.time()
            res = run_scale_test(D, N, rng)
            elapsed = time.time() - t0
            base = baselines[D]
            same_above = (res["same_sector_mean"] - base) / (1.0 - base)
            cross_above = (res["cross_sector_mean"] - base) / (1.0 - base)

            print(
                f"{D:>6} | {N:>4} | "
                f"{res['same_sector_mean']:>+0.4f} ± {res['same_sector_std']:.3f} | "
                f"{res['cross_sector_mean']:>+0.4f} ± {res['cross_sector_std']:.3f} | "
                f"{same_above:>+0.4f}         | "
                f"{cross_above:>+0.4f}"
            )

            results.append({
                "D": D,
                "N": N,
                "baseline": base,
                **res,
                "same_above_random": same_above,
                "cross_above_random": cross_above,
                "elapsed_sec": elapsed,
            })

    # Discrimination test: same > cross > random?
    print()
    print("=== Discrimination test (T3): same-sector > cross-sector > random? ===")
    for r in results:
        D, N = r["D"], r["N"]
        same = r["same_above_random"]
        cross = r["cross_above_random"]
        verdict = "PASS" if same > cross > -0.05 else "marginal" if same > cross else "FAIL"
        print(f"  D={D:>5}, N={N:>3}: same={same:+0.3f}, cross={cross:+0.3f}, gap={same-cross:+0.3f} -> {verdict}")

    # Write results JSON
    out_path = Path(__file__).parent / "R-RBS-LM-99_results.json"
    out_path.write_text(json.dumps({
        "srmech_version": SRMECH_VERSION,
        "has_native": HAS_NATIVE,
        "abi": NATIVE_ABI_VERSION,
        "D_sweep": D_sweep,
        "N_sweep": N_sweep,
        "seed": 42,
        "baselines": {str(k): v for k, v in baselines.items()},
        "results": results,
    }, indent=2))
    print(f"\nResults written to {out_path}")

    # OPEN_SPECTRUM_VERIFICATION
    print()
    print("=" * 80)
    print("OPEN_SPECTRUM_VERIFICATION")
    print("=" * 80)
    print(f"Source: srmech.amsc.hdc.klein4_* upstream v{SRMECH_VERSION}")
    print(f"D_sweep: {D_sweep}")
    print(f"N_sweep: {N_sweep}")
    print(f"Seed: 42")
    print(f"Reproducibility: python R-RBS-LM-99_cross_sector_retrieval_at_scale.py")


if __name__ == "__main__":
    main()
