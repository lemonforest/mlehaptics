"""R-RBS-LM-97v2 — Polar / Klein-4 / Bipolar HDC capacity comparison

Reruns the R-RBS-LM-97 capacity comparison using upstream srmech v0.4.3
HDC catalog. Replaces the prior bare-np.sign bug (which produced
tie-zeros that broke bipolar bundle/unbind/similarity) with three
proper variants:

  * bipolar       — rank-1 abelian XOR over F_2 (sign_quantise dead_band=0)
  * polar         — 3-state {-1, 0, +1} (sign_quantise dead_band > 0)
  * klein4        — rank-2 abelian XOR over F_2 x F_2 (state in {0,1,2,3})

Methodology per F132 §7 capacity test:
  1. Generate N random hypervectors per variant
  2. Bind them pairwise into composite "memories"
  3. Query each memory with one operand; recover the other via unbind
  4. Measure similarity of recovered vector to ground-truth other operand
  5. Compare degradation as N grows (capacity headroom)

Variant-fair comparison: bipolar D=10000 (10000 bits = 1.25 KB),
polar D=10000 (~2 bits/element, ~2.5 KB), klein4 D=10000 (2 bits/element,
2.5 KB). Klein-4 has 2x density vs bipolar at matched D.

OPEN_SPECTRUM_VERIFICATION block at end per AMSC discipline.
"""
import json
import time
from pathlib import Path

import numpy as np

# Upstream srmech v0.4.3 catalog imports
from srmech.amsc import hdc
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION


def capacity_test_bipolar(D: int, N_pairs: int, rng: np.random.Generator):
    """Bipolar HDC capacity: bind N pairs into one bundle, query each."""
    # Random bipolar vectors in {-1, +1}
    A_vecs = rng.choice([-1, 1], size=(N_pairs, D)).astype(np.int8)
    B_vecs = rng.choice([-1, 1], size=(N_pairs, D)).astype(np.int8)
    # Bind pairs: A_i XOR B_i (sign-product for bipolar)
    bound_pairs = A_vecs * B_vecs
    # Bundle: per-bit majority (sum then sign; ties resolved by sign of sum)
    bundle_sum = bound_pairs.sum(axis=0)
    # Strict bipolar: ties go to +1 (avoid bare np.sign tie-zero bug)
    bundle = np.where(bundle_sum >= 0, 1, -1).astype(np.int8)
    # Query each A_i; recover candidate B_i via unbind (same as bind for bipolar)
    sims = []
    for i in range(N_pairs):
        candidate_B = bundle * A_vecs[i]
        # Cosine sim (== match-fraction * 2 - 1 for bipolar)
        sim = float(np.mean(candidate_B == B_vecs[i]) * 2 - 1)
        sims.append(sim)
    return float(np.mean(sims)), float(np.std(sims)), sims


def capacity_test_polar(D: int, N_pairs: int, rng: np.random.Generator):
    """Polar HDC capacity: 3-state {-1, 0, +1}; 0 is absorbing under bind."""
    # Random polar vectors. Use polar_random; default density per upstream
    A_vecs = np.array([hdc.polar_random(D, rng) for _ in range(N_pairs)])
    B_vecs = np.array([hdc.polar_random(D, rng) for _ in range(N_pairs)])
    # Pair-bind via polar_bind (multiplicative sign-product; 0 absorbing)
    bound_pairs = np.array(
        [hdc.polar_bind(A_vecs[i], B_vecs[i]) for i in range(N_pairs)]
    )
    # Bundle all pairs via polar_bundle (sticky-majority; ties produce 0)
    bundle = hdc.polar_bundle(*bound_pairs)
    # Query each A_i; recover candidate B_i via polar_unbind
    sims = []
    for i in range(N_pairs):
        candidate_B = hdc.polar_unbind(bundle, A_vecs[i])
        sim = float(hdc.polar_similarity(candidate_B, B_vecs[i]))
        sims.append(sim)
    return float(np.mean(sims)), float(np.std(sims)), sims


def capacity_test_klein4(D: int, N_pairs: int, rng: np.random.Generator):
    """Klein-4 HDC capacity: rank-2 abelian XOR over F_2 x F_2."""
    # Random Klein-4 vectors (states in {0,1,2,3})
    A_vecs = np.array([hdc.klein4_random(D, rng) for _ in range(N_pairs)])
    B_vecs = np.array([hdc.klein4_random(D, rng) for _ in range(N_pairs)])
    # Pair-bind via klein4_bind (component-wise XOR)
    bound_pairs = np.array(
        [hdc.klein4_bind(A_vecs[i], B_vecs[i]) for i in range(N_pairs)]
    )
    # Bundle all pairs via klein4_bundle (per-bit majority vote)
    bundle = hdc.klein4_bundle(*bound_pairs)
    # Query each A_i; recover candidate B_i via klein4_unbind (self-inverse)
    sims = []
    for i in range(N_pairs):
        candidate_B = hdc.klein4_unbind(bundle, A_vecs[i])
        sim = float(hdc.klein4_similarity(candidate_B, B_vecs[i]))
        sims.append(sim)
    return float(np.mean(sims)), float(np.std(sims)), sims


def main():
    D = 10000
    N_loads = [4, 8, 16, 32, 64, 128, 256, 512]
    rng = np.random.default_rng(42)

    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}")
    print(f"D={D}; N_loads={N_loads}")
    print()
    print(f"{'N_pairs':>8} | {'bipolar mean±std':>22} | {'polar mean±std':>22} | {'klein4 mean±std':>22} | {'time s':>8}")
    print("-" * 100)

    results = []
    for N in N_loads:
        t0 = time.time()
        bp_mean, bp_std, _ = capacity_test_bipolar(D, N, rng)
        po_mean, po_std, _ = capacity_test_polar(D, N, rng)
        k4_mean, k4_std, _ = capacity_test_klein4(D, N, rng)
        elapsed = time.time() - t0

        results.append({
            "N_pairs": N,
            "bipolar": {"mean": bp_mean, "std": bp_std},
            "polar":   {"mean": po_mean, "std": po_std},
            "klein4":  {"mean": k4_mean, "std": k4_std},
            "wall_seconds": elapsed,
        })
        print(
            f"{N:>8} | "
            f"{bp_mean:>+0.4f} ± {bp_std:>0.4f}    | "
            f"{po_mean:>+0.4f} ± {po_std:>0.4f}    | "
            f"{k4_mean:>+0.4f} ± {k4_std:>0.4f}    | "
            f"{elapsed:>8.2f}"
        )

    # Write results JSON
    out_path = Path(__file__).parent / "R-RBS-LM-97v2_results.json"
    out_path.write_text(json.dumps({
        "srmech_version": SRMECH_VERSION,
        "has_native": HAS_NATIVE,
        "abi": NATIVE_ABI_VERSION,
        "D": D,
        "N_loads": N_loads,
        "seed": 42,
        "results": results,
    }, indent=2))
    print(f"\nResults written to {out_path}")

    # OPEN_SPECTRUM_VERIFICATION block per AMSC discipline
    print()
    print("=" * 80)
    print("OPEN_SPECTRUM_VERIFICATION")
    print("=" * 80)
    print("Method: 3-way HDC capacity comparison (bipolar/polar/klein4)")
    print("Source: srmech.amsc.hdc upstream v0.4.3")
    print("Test: bind N pairs into one bundle; recover via unbind; measure similarity")
    print("Variants:")
    print("  bipolar: rank-1 abelian XOR over F_2; sign-product; tie -> +1")
    print("  polar:   3-state {-1, 0, +1}; 0 absorbing; sticky-majority bundle")
    print("  klein4:  rank-2 abelian XOR over F_2 x F_2; 4 states per position")
    print(f"D={D}; seed=42; N_loads={N_loads}")
    print()
    print("Reproducibility:")
    print(f"  python R-RBS-LM-97v2_polar_klein4_bipolar_capacity_compare.py")
    print(f"  produces R-RBS-LM-97v2_results.json")


if __name__ == "__main__":
    main()
