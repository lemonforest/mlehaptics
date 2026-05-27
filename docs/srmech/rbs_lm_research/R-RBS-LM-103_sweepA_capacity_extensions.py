"""R-RBS-LM-103 — Sweep A: F137 capacity extensions (stale items 1-4, 9-11)

Consolidated empirical sweep covering 7 STALE_PATHS_QUEUE items:

  Item 1: Skip-zero polar similarity — does excluding zero-zero matches change polar's lead?
  Item 2: Per-bit-info capacity — bits-per-position normalisation
  Item 3: D-matched-bits comparison — bipolar D=2N vs klein-4 D=N (matched total bits)
  Item 4: Noise robustness across variants — bit-corruption (NOT decay)
  Item 9: Very-high-N collapse threshold — at what N do all variants flatten to random?
  Item 10: Partial chirality flips — XOR with mask 1 (γ₅ only) vs mask 2 (iω₇ only) vs mask 3 (full CPT)
  Item 11: Mixed-sector bundles — asymmetric sector distributions (e.g., 75/25 split)

Output: results JSON + F144 finding markdown.
"""
import json
import time
from pathlib import Path

import numpy as np

from srmech.amsc import hdc
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION


def sim_bipolar(a, b):
    return float(np.mean(a == b) * 2 - 1)


def sim_polar(a, b):
    return float(hdc.polar_similarity(a, b))


def sim_polar_skip_zero(a, b):
    mask = (a != 0) & (b != 0)
    if not np.any(mask):
        return 0.0
    return float(np.mean(a[mask] == b[mask]))


def sim_klein4(a, b):
    return float(hdc.klein4_similarity(a, b))


def random_baselines(D, rng):
    bp, po_def, po_skip, k4 = [], [], [], []
    for _ in range(100):
        a_bp = rng.choice([-1, 1], size=D).astype(np.int8)
        b_bp = rng.choice([-1, 1], size=D).astype(np.int8)
        bp.append(sim_bipolar(a_bp, b_bp))
        a_po = hdc.polar_random(D, rng)
        b_po = hdc.polar_random(D, rng)
        po_def.append(sim_polar(a_po, b_po))
        po_skip.append(sim_polar_skip_zero(a_po, b_po))
        a_k4 = hdc.klein4_random(D, rng)
        b_k4 = hdc.klein4_random(D, rng)
        k4.append(sim_klein4(a_k4, b_k4))
    return {
        "bipolar": float(np.mean(bp)),
        "polar_default": float(np.mean(po_def)),
        "polar_skip_zero": float(np.mean(po_skip)),
        "klein4": float(np.mean(k4)),
    }


# Item 1: Skip-zero polar similarity
def item1_skip_zero_polar(D, N_pairs, rng):
    A = [hdc.polar_random(D, rng) for _ in range(N_pairs)]
    B = [hdc.polar_random(D, rng) for _ in range(N_pairs)]
    bound = [hdc.polar_bind(a, b) for a, b in zip(A, B)]
    comp = hdc.polar_bundle(*bound)
    sims_def, sims_skip = [], []
    for i in range(N_pairs):
        unbound = hdc.polar_unbind(comp, A[i])
        sims_def.append(sim_polar(unbound, B[i]))
        sims_skip.append(sim_polar_skip_zero(unbound, B[i]))
    return float(np.mean(sims_def)), float(np.mean(sims_skip))


# Item 3: D-matched-bits comparison
def item3_d_matched_bits(N_pairs, rng):
    """bipolar D=20000 (~20000 bits) vs klein-4 D=10000 (~20000 bits via 2-bit states)."""
    D_bp = 20000
    D_k4 = 10000

    # Bipolar
    A = [rng.choice([-1, 1], size=D_bp).astype(np.int8) for _ in range(N_pairs)]
    B = [rng.choice([-1, 1], size=D_bp).astype(np.int8) for _ in range(N_pairs)]
    bound = [a * b for a, b in zip(A, B)]
    s = np.sum(bound, axis=0)
    comp_bp = np.where(s >= 0, 1, -1).astype(np.int8)
    bp_sims = [sim_bipolar(comp_bp * A[i], B[i]) for i in range(N_pairs)]

    # Klein-4 at half D
    A_k4 = [hdc.klein4_random(D_k4, rng) for _ in range(N_pairs)]
    B_k4 = [hdc.klein4_random(D_k4, rng) for _ in range(N_pairs)]
    bound_k4 = [hdc.klein4_bind(a, b) for a, b in zip(A_k4, B_k4)]
    comp_k4 = hdc.klein4_bundle(*bound_k4)
    k4_sims = [sim_klein4(hdc.klein4_unbind(comp_k4, A_k4[i]), B_k4[i]) for i in range(N_pairs)]

    return float(np.mean(bp_sims)), float(np.mean(k4_sims))


# Item 4: Noise robustness (bit-flip corruption, NOT polar zero-decay)
def item4_noise_robustness(D, N_pairs, noise_frac, rng):
    """Apply random bit-flip noise to bound pairs BEFORE bundling."""
    # Bipolar
    A_bp = [rng.choice([-1, 1], size=D).astype(np.int8) for _ in range(N_pairs)]
    B_bp = [rng.choice([-1, 1], size=D).astype(np.int8) for _ in range(N_pairs)]
    bound_bp = [a * b for a, b in zip(A_bp, B_bp)]
    # Inject noise: flip random fraction of positions
    n_flip = int(noise_frac * D)
    for vec in bound_bp:
        flip_pos = rng.choice(D, size=n_flip, replace=False)
        vec[flip_pos] = -vec[flip_pos]
    s = np.sum(bound_bp, axis=0)
    comp_bp = np.where(s >= 0, 1, -1).astype(np.int8)
    bp_sims = [sim_bipolar(comp_bp * A_bp[i], B_bp[i]) for i in range(N_pairs)]

    # Klein-4: noise = random XOR with random state
    A_k4 = [hdc.klein4_random(D, rng) for _ in range(N_pairs)]
    B_k4 = [hdc.klein4_random(D, rng) for _ in range(N_pairs)]
    bound_k4 = [hdc.klein4_bind(a, b) for a, b in zip(A_k4, B_k4)]
    for vec in bound_k4:
        flip_pos = rng.choice(D, size=n_flip, replace=False)
        flip_vals = rng.integers(1, 4, size=n_flip).astype(np.uint8)
        vec[flip_pos] = vec[flip_pos] ^ flip_vals
    comp_k4 = hdc.klein4_bundle(*bound_k4)
    k4_sims = [sim_klein4(hdc.klein4_unbind(comp_k4, A_k4[i]), B_k4[i]) for i in range(N_pairs)]

    # Polar: noise = bit-flip on ±1 positions (keep 0s)
    A_po = [hdc.polar_random(D, rng) for _ in range(N_pairs)]
    B_po = [hdc.polar_random(D, rng) for _ in range(N_pairs)]
    bound_po = [hdc.polar_bind(a, b) for a, b in zip(A_po, B_po)]
    for vec in bound_po:
        flip_pos = rng.choice(D, size=n_flip, replace=False)
        nz_at_flip = flip_pos[vec[flip_pos] != 0]
        vec[nz_at_flip] = -vec[nz_at_flip]
    comp_po = hdc.polar_bundle(*bound_po)
    po_sims = [sim_polar(hdc.polar_unbind(comp_po, A_po[i]), B_po[i]) for i in range(N_pairs)]

    return float(np.mean(bp_sims)), float(np.mean(k4_sims)), float(np.mean(po_sims))


# Item 9: Very-high-N collapse
def item9_high_n_collapse(D, rng):
    N_sweep = [4, 16, 64, 256, 1024, 4096]
    results = []
    for N in N_sweep:
        # Use first 50 as test pairs to avoid quadratic blowup at N=4096
        n_test = min(N, 50)
        A_k4 = [hdc.klein4_random(D, rng) for _ in range(N)]
        B_k4 = [hdc.klein4_random(D, rng) for _ in range(N)]
        bound = [hdc.klein4_bind(a, b) for a, b in zip(A_k4, B_k4)]
        comp = hdc.klein4_bundle(*bound)
        sims = [sim_klein4(hdc.klein4_unbind(comp, A_k4[i]), B_k4[i]) for i in range(n_test)]
        results.append((N, float(np.mean(sims))))
    return results


# Item 10: Partial chirality flips
def item10_partial_flips(D, rng):
    """Compare mask=1 (omega7 only), mask=2 (gamma5 only), mask=3 (CPT) flip discrimination."""
    N = 16
    concepts = [hdc.klein4_random(D, rng) for _ in range(N)]
    sectors = [i % 4 for i in range(N)]
    tagged = [hdc.klein4_bind(c, np.full(D, s, dtype=np.uint8)) for c, s in zip(concepts, sectors)]
    composite = hdc.klein4_bundle(*tagged)

    results = {}
    for query_mask in [1, 2, 3]:
        # Unbind with this mask; compare to original concept
        same_to_C = []
        for i in range(N):
            unbound = hdc.klein4_unbind(
                composite,
                np.full(D, sectors[i] ^ query_mask, dtype=np.uint8)
            )
            same_to_C.append(sim_klein4(unbound, concepts[i]))
        results[query_mask] = float(np.mean(same_to_C))
    return results


# Item 11: Mixed-sector bundles
def item11_mixed_sector(D, rng):
    """Asymmetric sector distribution (75/25 split between sectors 0 and 2)."""
    N = 16
    sectors = [0] * 12 + [2] * 4  # 12 visible, 4 antimatter (mismatched ratio)
    concepts = [hdc.klein4_random(D, rng) for _ in range(N)]
    tagged = [hdc.klein4_bind(c, np.full(D, s, dtype=np.uint8)) for c, s in zip(concepts, sectors)]
    composite = hdc.klein4_bundle(*tagged)

    # Retrieve sector 0 and sector 2 separately
    s0_sims, s2_sims = [], []
    for i, (c, s) in enumerate(zip(concepts, sectors)):
        unbound = hdc.klein4_unbind(composite, np.full(D, s, dtype=np.uint8))
        sim = sim_klein4(unbound, c)
        if s == 0:
            s0_sims.append(sim)
        else:
            s2_sims.append(sim)
    return float(np.mean(s0_sims)), float(np.mean(s2_sims))


def main():
    rng = np.random.default_rng(42)
    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}")
    print()

    D = 10000
    N_pairs = 32

    base = random_baselines(D, rng)
    print(f"Baselines @ D={D}: {base}")
    print()

    print("=== Item 1: Skip-zero polar similarity ===")
    polar_def, polar_skip = item1_skip_zero_polar(D, N_pairs, rng)
    above_def = (polar_def - base["polar_default"]) / (1 - base["polar_default"])
    above_skip = (polar_skip - base["polar_skip_zero"]) / (1 - base["polar_skip_zero"])
    print(f"  polar default sim:    {polar_def:.4f}  (above-rand {above_def:+0.4f})")
    print(f"  polar skip-zero sim:  {polar_skip:.4f}  (above-rand {above_skip:+0.4f})")
    print(f"  Verdict: skip-zero {'shrinks' if above_skip < above_def else 'increases'} polar's lead")
    print()

    print("=== Item 2: Per-bit-info capacity (info per position) ===")
    # bipolar = log2(2)=1 bit/pos; klein-4 = 2 bits/pos; polar ≈ log2(3)*density ≈ 1.06 bits/pos at 0.67 density
    bits_per_pos = {"bipolar": 1.0, "klein4": 2.0, "polar": 1.06}
    print(f"  Info bits per position: {bits_per_pos}")
    print(f"  At D=10000: bipolar={1.0*D:.0f}b, klein4={2.0*D:.0f}b, polar={1.06*D:.0f}b")
    print()

    print("=== Item 3: D-matched-bits (bipolar D=20000 vs klein-4 D=10000, both ~20000b) ===")
    bp_matched, k4_matched = item3_d_matched_bits(N_pairs, rng)
    bp_matched_above = (bp_matched - base["bipolar"]) / (1 - base["bipolar"])
    k4_matched_above = (k4_matched - base["klein4"]) / (1 - base["klein4"])
    print(f"  bipolar (D=20000): sim={bp_matched:+0.4f}  above-rand {bp_matched_above:+0.4f}")
    print(f"  klein-4 (D=10000): sim={k4_matched:+0.4f}  above-rand {k4_matched_above:+0.4f}")
    print(f"  Verdict: at matched bits, {'bipolar' if bp_matched_above > k4_matched_above else 'klein-4'} wins by {abs(bp_matched_above - k4_matched_above):.4f}")
    print()

    print("=== Item 4: Noise robustness (bit-flip corruption) ===")
    print(f"{'noise':>6} | {'bipolar above-rand':>18} | {'klein4 above-rand':>18} | {'polar above-rand':>18}")
    print("-" * 80)
    noise_results = []
    for noise_frac in [0.0, 0.1, 0.2, 0.3, 0.5]:
        bp, k4, po = item4_noise_robustness(D, N_pairs, noise_frac, rng)
        bp_ar = (bp - base["bipolar"]) / (1 - base["bipolar"])
        k4_ar = (k4 - base["klein4"]) / (1 - base["klein4"])
        po_ar = (po - base["polar_default"]) / (1 - base["polar_default"])
        print(f"{noise_frac:>6.2f} | {bp_ar:>+0.4f}            | {k4_ar:>+0.4f}            | {po_ar:>+0.4f}")
        noise_results.append({"noise": noise_frac, "bipolar": bp_ar, "klein4": k4_ar, "polar": po_ar})
    print()

    print("=== Item 9: Very-high-N collapse threshold (Klein-4) ===")
    collapse_results = item9_high_n_collapse(D, rng)
    print(f"{'N':>6} | {'klein-4 sim':>12} | {'above-rand':>12}")
    print("-" * 50)
    for N, sim in collapse_results:
        ar = (sim - base["klein4"]) / (1 - base["klein4"])
        print(f"{N:>6} | {sim:>+0.4f}     | {ar:>+0.4f}")
    print()

    print("=== Item 10: Partial chirality flips ===")
    partial_results = item10_partial_flips(D, rng)
    print(f"  query mask=1 (omega7 flip only): same-to-C = {partial_results[1]:.4f}  above-rand {(partial_results[1] - base['klein4']) / (1 - base['klein4']):+0.4f}")
    print(f"  query mask=2 (gamma5 flip only): same-to-C = {partial_results[2]:.4f}  above-rand {(partial_results[2] - base['klein4']) / (1 - base['klein4']):+0.4f}")
    print(f"  query mask=3 (full CPT):         same-to-C = {partial_results[3]:.4f}  above-rand {(partial_results[3] - base['klein4']) / (1 - base['klein4']):+0.4f}")
    print()

    print("=== Item 11: Mixed-sector bundles (75% sector 0, 25% sector 2) ===")
    s0_sim, s2_sim = item11_mixed_sector(D, rng)
    s0_ar = (s0_sim - base["klein4"]) / (1 - base["klein4"])
    s2_ar = (s2_sim - base["klein4"]) / (1 - base["klein4"])
    print(f"  sector 0 retrieval (12/16 concepts): sim={s0_sim:.4f}  above-rand {s0_ar:+0.4f}")
    print(f"  sector 2 retrieval ( 4/16 concepts): sim={s2_sim:.4f}  above-rand {s2_ar:+0.4f}")
    print()

    out = {
        "srmech_version": SRMECH_VERSION,
        "has_native": HAS_NATIVE,
        "abi": NATIVE_ABI_VERSION,
        "D": D,
        "N_pairs": N_pairs,
        "baselines": base,
        "item1_polar_default_above_rand": above_def,
        "item1_polar_skip_zero_above_rand": above_skip,
        "item2_bits_per_position": bits_per_pos,
        "item3_d_matched_bits_above_rand": {"bipolar_D20000": bp_matched_above, "klein4_D10000": k4_matched_above},
        "item4_noise_robustness": noise_results,
        "item9_high_n_collapse": [{"N": N, "sim": s, "above_rand": (s - base["klein4"]) / (1 - base["klein4"])} for N, s in collapse_results],
        "item10_partial_flips": {f"mask_{k}": v for k, v in partial_results.items()},
        "item11_mixed_sector": {"sector_0_above_rand": s0_ar, "sector_2_above_rand": s2_ar},
    }
    out_path = Path(__file__).parent / "R-RBS-LM-103_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"Results: {out_path}")


if __name__ == "__main__":
    main()
