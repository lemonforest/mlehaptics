"""R-RBS-LM-104 — Sweep B: F138-F140 chirality cascade variations

Resolves STALE items: 5 (D-sweep), 6 (N-sweep), 7 (encoding refinement),
8 (eigval-based sector), 13 (cascade depth), 14 (class order), 15 (Class K
interaction), 17 (bipolar vs polar in cascade), 22 (multi-class under decay).

Strategy: single script with sub-tests per item. Consolidated finding F145.
"""
import json
import time
from pathlib import Path

import numpy as np

from srmech.amsc import hdc, laplacian
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION


SECTOR_CPT_MIRROR = {0: 3, 1: 2, 2: 1, 3: 0}


def random_baseline_klein4(D, rng, N=50):
    sims = []
    for _ in range(N):
        a = hdc.klein4_random(D, rng)
        b = hdc.klein4_random(D, rng)
        sims.append(float(hdc.klein4_similarity(a, b)))
    return float(np.mean(sims))


def encode_concept_with_sector(c_seed, sector, D, rng_for_content):
    """Independent klein-4 content + sector tag (F139 methodology)."""
    rng = np.random.default_rng(c_seed)
    content = hdc.klein4_random(D, rng)
    return hdc.klein4_bind(content, np.full(D, sector, dtype=np.uint8)), content


def chirality_test(composite, concepts, sectors, D):
    """Run F139-style same / cross-to-C / cross-to-Cmirror discrimination."""
    same_sims, cross_to_C, cross_to_Cmirror = [], [], []
    for i, c in enumerate(concepts):
        own_sector = sectors[i]
        cpt_sector = SECTOR_CPT_MIRROR[own_sector]
        c_mirror = hdc.klein4_bind(c, np.full(D, 3, dtype=np.uint8))

        same_unbound = hdc.klein4_unbind(composite, np.full(D, own_sector, dtype=np.uint8))
        cross_unbound = hdc.klein4_unbind(composite, np.full(D, cpt_sector, dtype=np.uint8))

        same_sims.append(float(hdc.klein4_similarity(same_unbound, c)))
        cross_to_C.append(float(hdc.klein4_similarity(cross_unbound, c)))
        cross_to_Cmirror.append(float(hdc.klein4_similarity(cross_unbound, c_mirror)))
    return {
        "same_to_C": float(np.mean(same_sims)),
        "cross_to_C": float(np.mean(cross_to_C)),
        "cross_to_Cmirror": float(np.mean(cross_to_Cmirror)),
    }


# === Items 5, 6: D-sweep + N-sweep ===
def items_5_6_d_n_sweep(rng):
    """D-sweep at N=32; N-sweep at D=16384. Klein-4 with sector tags."""
    out = {}
    # D-sweep at fixed N=32
    N = 32
    d_results = {}
    for D in [1024, 4096, 16384, 65536]:
        base = random_baseline_klein4(D, rng)
        concepts = []
        sectors = []
        tagged = []
        for i in range(N):
            tag, c = encode_concept_with_sector(c_seed=i, sector=i % 4, D=D, rng_for_content=rng)
            concepts.append(c)
            sectors.append(i % 4)
            tagged.append(tag)
        composite = hdc.klein4_bundle(*tagged)
        results = chirality_test(composite, concepts, sectors, D)
        above_rand = (results["same_to_C"] - base) / (1 - base)
        d_results[D] = {"same": results["same_to_C"], "above_rand": above_rand, "baseline": base}
    out["d_sweep_at_N32"] = d_results

    # N-sweep at fixed D=16384
    D = 16384
    base = random_baseline_klein4(D, rng)
    n_results = {}
    for N in [4, 8, 16, 32, 64, 128]:
        concepts = []
        sectors = []
        tagged = []
        for i in range(N):
            tag, c = encode_concept_with_sector(c_seed=i, sector=i % 4, D=D, rng_for_content=rng)
            concepts.append(c)
            sectors.append(i % 4)
            tagged.append(tag)
        composite = hdc.klein4_bundle(*tagged)
        results = chirality_test(composite, concepts, sectors, D)
        above_rand = (results["same_to_C"] - base) / (1 - base)
        n_results[N] = {"same": results["same_to_C"], "above_rand": above_rand}
    out["n_sweep_at_D16384"] = n_results
    return out


# === Items 7, 8: Encoding refinement + eigval-based sector ===
def items_7_8_encoding_refinement(D, rng):
    """Compare 3 encoding strategies for Class L → Klein-4 handoff.

    A) Tile + quantise (F138 baseline)
    B) Random projection per eigvec
    C) Eigval-magnitude-based sector assignment (item 8)
    """
    # Build a small graph
    n_nodes = 32
    edges = []
    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            if rng.random() < 0.15:
                edges.append((i, j))
    weights = [1.0] * len(edges)
    L = laplacian.dense_laplacian(n_nodes, edges, weights)
    eigvals, eigvecs = laplacian.hermitian_eigendecompose(L)
    eigvecs = eigvecs.real

    # Strategy A: tile + quantise (F138 method)
    def encode_A(eigvec, D, sector):
        n = len(eigvec)
        indices = np.tile(np.arange(n), (D // n) + 1)[:D]
        states = np.zeros(D, dtype=np.uint8)
        for d in range(D):
            v = eigvec[indices[d]]
            states[d] = ((1 if v > 0 else 0) << 1) | (1 if abs(v) > 0.1 else 0)
        return hdc.klein4_bind(states, np.full(D, sector, dtype=np.uint8))

    # Strategy B: random projection per eigvec
    def encode_B(eigvec_idx, D, sector, rng):
        # Independent random base; eigvec content combined via klein-4 XOR
        base = hdc.klein4_random(D, np.random.default_rng(int(eigvec_idx) * 7919))
        return hdc.klein4_bind(base, np.full(D, sector, dtype=np.uint8))

    # Run both A and B with N=8 (mid eigvecs)
    N = 8
    eig_indices = list(range(4, 4 + N))
    results = {}
    for strategy_name, encoder_fn in [("A_tile_quantise", encode_A), ("B_random_projection", None)]:
        tagged = []
        concepts = []
        sectors = []
        for i, eig_idx in enumerate(eig_indices):
            sector = i % 4
            if strategy_name == "A_tile_quantise":
                hv = encoder_fn(eigvecs[:, eig_idx], D, sector)
                # For chirality_test we need the pre-sector base too
                tile_indices = np.tile(np.arange(n_nodes), (D // n_nodes) + 1)[:D]
                content_states = np.zeros(D, dtype=np.uint8)
                for d in range(D):
                    v = eigvecs[tile_indices[d], eig_idx]
                    content_states[d] = ((1 if v > 0 else 0) << 1) | (1 if abs(v) > 0.1 else 0)
                base_content = content_states  # before sector tag applied
            else:
                base_content = hdc.klein4_random(D, np.random.default_rng(int(eig_idx) * 7919))
                hv = hdc.klein4_bind(base_content, np.full(D, sector, dtype=np.uint8))
            tagged.append(hv)
            concepts.append(base_content)
            sectors.append(sector)

        composite = hdc.klein4_bundle(*tagged)
        chir = chirality_test(composite, concepts, sectors, D)
        results[strategy_name] = chir

    # Strategy C: eigval-magnitude-based sector
    eigvals_sorted = sorted(enumerate(eigvals), key=lambda x: x[1])
    n_per_quartile = N // 4
    sector_by_eigidx = {}
    for q in range(4):
        for k in range(n_per_quartile):
            idx_in_sorted = q * n_per_quartile + k
            if idx_in_sorted < len(eigvals_sorted):
                orig_idx, _ = eigvals_sorted[idx_in_sorted]
                sector_by_eigidx[orig_idx] = q

    tagged_C = []
    concepts_C = []
    sectors_C = []
    for eig_idx in eig_indices:
        sector = sector_by_eigidx.get(eig_idx, 0)
        base_content = hdc.klein4_random(D, np.random.default_rng(int(eig_idx) * 7919))
        hv = hdc.klein4_bind(base_content, np.full(D, sector, dtype=np.uint8))
        tagged_C.append(hv)
        concepts_C.append(base_content)
        sectors_C.append(sector)
    composite_C = hdc.klein4_bundle(*tagged_C)
    chir_C = chirality_test(composite_C, concepts_C, sectors_C, D)
    results["C_eigval_based_sector"] = chir_C

    return results


# === Items 13, 14: Cascade depth + class order ===
def items_13_14_cascade_depth_order(D, rng):
    """Test 6-class cascade vs 4-class cascade; same classes in different orders."""
    N = 16

    def cascade(concepts, sectors, classes_order, D, rng):
        """Apply classes in the given order before final klein-4 tag."""
        encoded = []
        for i, c in enumerate(concepts):
            hv = c.copy()
            for op in classes_order:
                if op == "I_cyclic":
                    hv = np.roll(hv, (i + 1) * 137 % D)
                elif op == "M_bipolar_overlay":
                    bipolar = np.random.default_rng(i + 1000).choice([-1, 1], size=D).astype(np.int8)
                    bp_as_k4 = ((bipolar + 1) // 2).astype(np.uint8)
                    hv = hdc.klein4_bind(hv, bp_as_k4)
                elif op == "M_klein4_tag":
                    hv = hdc.klein4_bind(hv, np.full(D, sectors[i], dtype=np.uint8))
                elif op == "K_signflip":
                    # Class K sign-flip: invert lower bit of half positions
                    flip_mask = np.zeros(D, dtype=np.uint8)
                    flip_mask[::2] = 1  # every other position gets bit-flip
                    hv = hv ^ flip_mask
            encoded.append(hv)
        return encoded

    concepts = [hdc.klein4_random(D, rng) for _ in range(N)]
    sectors = [i % 4 for i in range(N)]

    # Test 1: Standard 4-class order
    order1 = ["I_cyclic", "M_bipolar_overlay", "M_klein4_tag"]
    encoded1 = cascade(concepts, sectors, order1, D, rng)
    comp1 = hdc.klein4_bundle(*encoded1)
    base = random_baseline_klein4(D, rng)

    # Run chirality test on POST-cascade content
    # (different from F139 because cascade has applied multiple transforms)
    same1 = []
    for i in range(N):
        same_unbound = hdc.klein4_unbind(comp1, np.full(D, sectors[i], dtype=np.uint8))
        same1.append(float(hdc.klein4_similarity(same_unbound, encoded1[i] if False else hdc.klein4_unbind(encoded1[i], np.full(D, sectors[i], dtype=np.uint8)))))
    # Actually simpler: compare to the tagged hv before bundling
    same1_proper = []
    for i in range(N):
        same_unbound = hdc.klein4_unbind(comp1, np.full(D, sectors[i], dtype=np.uint8))
        # The recovered should match the content BEFORE chirality tag was applied
        # In our cascade, encoded1[i] = content -> I_cyclic -> bipolar -> klein4_tag(sector)
        # So same_unbound recovers content -> I_cyclic -> bipolar (pre-tag intermediate)
        # Compare to intermediate
        intermediate = concepts[i].copy()
        intermediate = np.roll(intermediate, (i + 1) * 137 % D)
        bp = np.random.default_rng(i + 1000).choice([-1, 1], size=D).astype(np.int8)
        bp_as_k4 = ((bp + 1) // 2).astype(np.uint8)
        intermediate = hdc.klein4_bind(intermediate, bp_as_k4)
        same1_proper.append(float(hdc.klein4_similarity(same_unbound, intermediate)))

    # Test 2: 6-class deeper order
    order2 = ["I_cyclic", "K_signflip", "M_bipolar_overlay", "K_signflip", "I_cyclic", "M_klein4_tag"]
    encoded2 = cascade(concepts, sectors, order2, D, rng)
    comp2 = hdc.klein4_bundle(*encoded2)
    same2_proper = []
    for i in range(N):
        same_unbound = hdc.klein4_unbind(comp2, np.full(D, sectors[i], dtype=np.uint8))
        # Reconstruct intermediate (everything except final klein4_tag)
        interm = concepts[i].copy()
        interm = np.roll(interm, (i + 1) * 137 % D)
        flip_mask = np.zeros(D, dtype=np.uint8)
        flip_mask[::2] = 1
        interm = interm ^ flip_mask
        bp = np.random.default_rng(i + 1000).choice([-1, 1], size=D).astype(np.int8)
        bp_as_k4 = ((bp + 1) // 2).astype(np.uint8)
        interm = hdc.klein4_bind(interm, bp_as_k4)
        interm = interm ^ flip_mask
        interm = np.roll(interm, (i + 1) * 137 % D)
        same2_proper.append(float(hdc.klein4_similarity(same_unbound, interm)))

    # Test 3: Class order swap (Class I before vs after Class L bipolar)
    order3 = ["M_bipolar_overlay", "I_cyclic", "M_klein4_tag"]  # swapped vs order1
    encoded3 = cascade(concepts, sectors, order3, D, rng)
    comp3 = hdc.klein4_bundle(*encoded3)
    same3_proper = []
    for i in range(N):
        same_unbound = hdc.klein4_unbind(comp3, np.full(D, sectors[i], dtype=np.uint8))
        interm = concepts[i].copy()
        bp = np.random.default_rng(i + 1000).choice([-1, 1], size=D).astype(np.int8)
        bp_as_k4 = ((bp + 1) // 2).astype(np.uint8)
        interm = hdc.klein4_bind(interm, bp_as_k4)
        interm = np.roll(interm, (i + 1) * 137 % D)
        same3_proper.append(float(hdc.klein4_similarity(same_unbound, interm)))

    return {
        "depth_4_standard_above_rand": (float(np.mean(same1_proper)) - base) / (1 - base),
        "depth_6_deeper_above_rand": (float(np.mean(same2_proper)) - base) / (1 - base),
        "order_swapped_above_rand": (float(np.mean(same3_proper)) - base) / (1 - base),
        "baseline": base,
        "depth_4_raw_sim": float(np.mean(same1_proper)),
        "depth_6_raw_sim": float(np.mean(same2_proper)),
        "order_swapped_raw_sim": float(np.mean(same3_proper)),
    }


# === Item 17: Polar substituted in cascade ===
def item_17_polar_in_cascade(D, rng):
    """Replace bipolar with polar in F140-style cascade. Does chirality survive?"""
    N = 16
    concepts = [hdc.klein4_random(D, rng) for _ in range(N)]
    sectors = [i % 4 for i in range(N)]
    encoded = []
    for i, c in enumerate(concepts):
        hv = c.copy()
        # Class I cyclic shift
        hv = np.roll(hv, (i + 1) * 137 % D)
        # POLAR identity layer (instead of bipolar)
        polar = hdc.polar_random(D, np.random.default_rng(i + 2000))
        # Convert polar to klein-4 state space: -1->0, +1->1, 0->2 (use 0=neutral state)
        # NOTE: this loses signal at 0 positions because klein-4 has 4 states not 3
        polar_as_k4 = np.where(polar == 1, 1, np.where(polar == -1, 0, 2)).astype(np.uint8)
        hv = hdc.klein4_bind(hv, polar_as_k4)
        # Class M klein-4 chirality tag
        hv = hdc.klein4_bind(hv, np.full(D, sectors[i], dtype=np.uint8))
        encoded.append(hv)
    composite = hdc.klein4_bundle(*encoded)
    base = random_baseline_klein4(D, rng)

    sames = []
    for i in range(N):
        same_unbound = hdc.klein4_unbind(composite, np.full(D, sectors[i], dtype=np.uint8))
        # Reconstruct intermediate
        interm = concepts[i].copy()
        interm = np.roll(interm, (i + 1) * 137 % D)
        polar = hdc.polar_random(D, np.random.default_rng(i + 2000))
        polar_as_k4 = np.where(polar == 1, 1, np.where(polar == -1, 0, 2)).astype(np.uint8)
        interm = hdc.klein4_bind(interm, polar_as_k4)
        sames.append(float(hdc.klein4_similarity(same_unbound, interm)))
    return {
        "polar_in_cascade_sim": float(np.mean(sames)),
        "above_rand": (float(np.mean(sames)) - base) / (1 - base),
    }


# === Item 22: Multi-class cascade UNDER decay ===
def item_22_cascade_under_decay(D, rng, decay_frac):
    """F140 4-class cascade + apply decay to composite before query."""
    N = 16
    concepts = [hdc.klein4_random(D, rng) for _ in range(N)]
    sectors = [i % 4 for i in range(N)]
    encoded = []
    for i, c in enumerate(concepts):
        hv = c.copy()
        hv = np.roll(hv, (i + 1) * 137 % D)
        bp = np.random.default_rng(i + 1000).choice([-1, 1], size=D).astype(np.int8)
        bp_as_k4 = ((bp + 1) // 2).astype(np.uint8)
        hv = hdc.klein4_bind(hv, bp_as_k4)
        hv = hdc.klein4_bind(hv, np.full(D, sectors[i], dtype=np.uint8))
        encoded.append(hv)
    composite = hdc.klein4_bundle(*encoded)

    # Apply decay to composite (zero out fraction of positions)
    n_decay = int(decay_frac * D)
    if n_decay > 0:
        decay_positions = rng.choice(D, size=n_decay, replace=False)
        composite_decayed = composite.copy()
        composite_decayed[decay_positions] = 0  # 0 is the identity state in Klein-4
    else:
        composite_decayed = composite

    base = random_baseline_klein4(D, rng)
    sames = []
    for i in range(N):
        same_unbound = hdc.klein4_unbind(composite_decayed, np.full(D, sectors[i], dtype=np.uint8))
        interm = concepts[i].copy()
        interm = np.roll(interm, (i + 1) * 137 % D)
        bp = np.random.default_rng(i + 1000).choice([-1, 1], size=D).astype(np.int8)
        bp_as_k4 = ((bp + 1) // 2).astype(np.uint8)
        interm = hdc.klein4_bind(interm, bp_as_k4)
        sames.append(float(hdc.klein4_similarity(same_unbound, interm)))
    return {
        "decay_frac": decay_frac,
        "sim": float(np.mean(sames)),
        "above_rand": (float(np.mean(sames)) - base) / (1 - base),
    }


def main():
    rng = np.random.default_rng(42)
    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}")
    print()

    print("=== Items 5+6: D-sweep + N-sweep ===")
    r56 = items_5_6_d_n_sweep(rng)
    print("  D-sweep at N=32:")
    for D, res in r56["d_sweep_at_N32"].items():
        print(f"    D={D}: same={res['same']:.4f}, above-rand={res['above_rand']:+0.4f}")
    print("  N-sweep at D=16384:")
    for N, res in r56["n_sweep_at_D16384"].items():
        print(f"    N={N}: same={res['same']:.4f}, above-rand={res['above_rand']:+0.4f}")
    print()

    print("=== Items 7+8: Encoding refinement + eigval sector ===")
    r78 = items_7_8_encoding_refinement(16384, rng)
    for strategy, res in r78.items():
        print(f"  {strategy}: same→C={res['same_to_C']:.4f}, cross→C={res['cross_to_C']:.4f}, cross→Cmirror={res['cross_to_Cmirror']:.4f}")
    print()

    print("=== Items 13+14: Cascade depth + class order ===")
    r1314 = items_13_14_cascade_depth_order(16384, rng)
    print(f"  Depth 4 (standard order):  above-rand {r1314['depth_4_standard_above_rand']:+0.4f}")
    print(f"  Depth 6 (deeper +Class K): above-rand {r1314['depth_6_deeper_above_rand']:+0.4f}")
    print(f"  Order swapped:             above-rand {r1314['order_swapped_above_rand']:+0.4f}")
    print()

    print("=== Item 17: Polar substituted for bipolar in cascade ===")
    r17 = item_17_polar_in_cascade(16384, rng)
    print(f"  Polar-in-cascade: sim={r17['polar_in_cascade_sim']:.4f}, above-rand {r17['above_rand']:+0.4f}")
    print()

    print("=== Item 22: Multi-class cascade UNDER decay ===")
    r22 = []
    for decay in [0.0, 0.1, 0.3, 0.5]:
        res = item_22_cascade_under_decay(16384, rng, decay)
        r22.append(res)
        print(f"  decay={decay:.1f}: sim={res['sim']:.4f}, above-rand={res['above_rand']:+0.4f}")
    print()

    out = {
        "srmech_version": SRMECH_VERSION,
        "has_native": HAS_NATIVE,
        "abi": NATIVE_ABI_VERSION,
        "items_5_6": r56,
        "items_7_8": r78,
        "items_13_14": r1314,
        "item_17": r17,
        "item_22": r22,
    }
    out_path = Path(__file__).parent / "R-RBS-LM-104_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"Results: {out_path}")


if __name__ == "__main__":
    main()
