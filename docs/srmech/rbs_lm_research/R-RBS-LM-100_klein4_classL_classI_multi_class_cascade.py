"""R-RBS-LM-100 — Klein-4 + Class L + Class I + Class M (bipolar) multi-class cascade

Path 4/6 of the wishlist-gated research resume.

Tests whether the chirality-axis (Class M rank-2 abelian = Klein-4) survives
composition with multiple other srmech classes in a longer cascade:

  Class L (Laplacian):       graph -> eigvecs -> spectral features
  Class I (cyclic / modular): cyclic-shift permute positions per concept
  Class M (bipolar):         encode concept identity as bipolar HV
  Class M (Klein-4):         apply chirality tag via sector mask
  Bundle:                    composite memory
  Query:                     same / cross / cpt-mirror retrieval

The key question per F132: does chirality-tag content survive multi-class
processing? Specifically:
  - After Class L spectral decomposition projects concepts
  - After Class I cyclic permutation perturbs positions
  - After bipolar binding mixes content
  - Can we still recover the chirality-tag at the end?

This is a strictly harder test than F139 (which used direct Klein-4 bundle).
Multi-class processing introduces noise/structure at every step; chirality
must survive all of it.

Cross-references:
  - F132 §4 (Klein-4 native operations)
  - F139 (chirality axis operational at direct bundle scale)
  - srmech.amsc.laplacian, srmech.amsc.hdc, srmech.amsc.cyclic
"""
import json
import time
from pathlib import Path

import numpy as np

from srmech.amsc import hdc, laplacian
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION


SECTOR_CPT_MIRROR = {0: 3, 1: 2, 2: 1, 3: 0}


def cyclic_shift(arr: np.ndarray, k: int) -> np.ndarray:
    """Class I cyclic shift (modular permute)."""
    return np.roll(arr, k)


def encode_multi_class(
    eigvec: np.ndarray,
    bipolar_seed: int,
    chirality_sector: int,
    cyclic_offset: int,
    D: int,
) -> np.ndarray:
    """Full multi-class cascade encoder.

    1. Class M bipolar: random bipolar HV seeded by concept ID
    2. Class L spectral content: quantise eigvec into klein-4 states; combine
    3. Class I cyclic shift: rotate by concept-specific offset
    4. Class M klein-4: tag chirality sector
    """
    rng = np.random.default_rng(bipolar_seed)

    # 1. Class M bipolar identity HV
    bipolar = rng.choice([-1, 1], size=D).astype(np.int8)

    # 2. Class L spectral content: map eigvec components into klein-4 states
    # Tile-and-quantise (same as R-RBS-LM-98)
    n = len(eigvec)
    indices = np.tile(np.arange(n), (D // n) + 1)[:D]
    spectral_states = np.zeros(D, dtype=np.uint8)
    for d in range(D):
        v = eigvec[indices[d]]
        bit_high = 1 if v > 0 else 0
        bit_low = 1 if abs(v) > 0.1 else 0
        spectral_states[d] = (bit_high << 1) | bit_low

    # Convert bipolar to klein-4 state-space (map -1 -> 0, +1 -> 1, encoded in low bit only)
    bipolar_as_k4 = ((bipolar + 1) // 2).astype(np.uint8)

    # Combine bipolar and spectral via klein-4 bind (component-wise XOR)
    content = hdc.klein4_bind(bipolar_as_k4, spectral_states)

    # 3. Class I cyclic shift
    shifted = cyclic_shift(content, cyclic_offset)

    # 4. Class M klein-4 chirality tag
    sector_mask = np.full(D, chirality_sector, dtype=np.uint8)
    tagged = hdc.klein4_bind(shifted, sector_mask)

    return tagged, bipolar, spectral_states, shifted  # return intermediates for analysis


def decode_chirality(composite: np.ndarray, query_sector: int) -> np.ndarray:
    """Reverse the chirality-tag step only; other classes remain encoded."""
    D = len(composite)
    return hdc.klein4_unbind(composite, np.full(D, query_sector, dtype=np.uint8))


def main():
    rng = np.random.default_rng(42)
    D = 16384
    n_nodes = 64
    edge_density = 0.10
    N_concepts = 16

    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}")
    print(f"D={D}, n_nodes={n_nodes}, N_concepts={N_concepts}")
    print()

    # Class L step: build graph + Laplacian + eigendecompose
    t0 = time.time()
    edges, weights = [], []
    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            if rng.random() < edge_density:
                edges.append((i, j))
                weights.append(1.0)
    L = laplacian.dense_laplacian(n_nodes, edges, weights)
    eigvals, eigvecs = laplacian.hermitian_eigendecompose(L)
    eigvecs = eigvecs.real
    t_classL = time.time() - t0
    print(f"Class L: |E|={len(edges)}, eigendecompose {t_classL:.2f}s")

    # Encode N_concepts using top N_concepts eigvecs (sorted by eigval)
    # Use N_concepts mid-band eigvecs (skip zero eigval and largest noise)
    skip = 4
    selected_eigvec_indices = list(range(skip, skip + N_concepts))
    selected_eigvals = [float(eigvals[i]) for i in selected_eigvec_indices]
    print(f"Using eigvec indices {skip}..{skip + N_concepts - 1}; eigval range: [{min(selected_eigvals):.3f}, {max(selected_eigvals):.3f}]")

    # Assign each concept a sector, cyclic offset, bipolar seed
    concepts_meta = []
    encoded = []
    intermediates = []
    for i, eig_idx in enumerate(selected_eigvec_indices):
        sector = i % 4
        cyclic_offset = (i * 137) % D  # prime-like spacing
        bipolar_seed = 1000 + i

        tagged, bipolar, spectral, shifted = encode_multi_class(
            eigvec=eigvecs[:, eig_idx],
            bipolar_seed=bipolar_seed,
            chirality_sector=sector,
            cyclic_offset=cyclic_offset,
            D=D,
        )
        concepts_meta.append({
            "i": i,
            "eig_idx": eig_idx,
            "eigval": selected_eigvals[i],
            "sector": sector,
            "cyclic_offset": cyclic_offset,
            "bipolar_seed": bipolar_seed,
        })
        encoded.append(tagged)
        intermediates.append({
            "bipolar": bipolar,
            "spectral": spectral,
            "shifted": shifted,
        })

    # Bundle all encoded concepts
    t0 = time.time()
    composite = hdc.klein4_bundle(*encoded)
    t_bundle = time.time() - t0
    print(f"Bundle {N_concepts} multi-class encoded vectors: {t_bundle:.2f}s")
    print(f"Composite sector_count: {hdc.klein4_sector_count(composite).tolist()}")
    print()

    # The load-bearing test: can we still discriminate chirality after Class L + I + M cascade?
    # Per F139 methodology: same/cross discrimination test
    print(f"{'Concept':>8} | {'Sector':>6} | {'same_to_C':>12} | {'cross_to_C':>12} | {'cross_to_Cmir':>14}")
    print("-" * 80)

    same_sims, cross_sims_origC, cross_sims_Cmirror = [], [], []
    for i, c_meta in enumerate(concepts_meta):
        target = encoded[i]
        own_sector = c_meta["sector"]
        cpt_sector = SECTOR_CPT_MIRROR[own_sector]
        target_mirror = hdc.klein4_bind(target, np.full(D, 3, dtype=np.uint8))

        # Same-sector
        same_unbound = decode_chirality(composite, own_sector)
        # Cross-sector
        cross_unbound = decode_chirality(composite, cpt_sector)

        # In the multi-class cascade, the target IS the post-shift, post-bipolar-bind, pre-chirality-tag vector
        # i.e., before the final chirality XOR was applied. Comparing recovered unbind to original-tagged target.
        same_sim = float(hdc.klein4_similarity(same_unbound, intermediates[i]["shifted"]))
        cross_sim_origC = float(hdc.klein4_similarity(cross_unbound, intermediates[i]["shifted"]))
        shifted_mirror = hdc.klein4_bind(intermediates[i]["shifted"], np.full(D, 3, dtype=np.uint8))
        cross_sim_Cmirror = float(hdc.klein4_similarity(cross_unbound, shifted_mirror))

        same_sims.append(same_sim)
        cross_sims_origC.append(cross_sim_origC)
        cross_sims_Cmirror.append(cross_sim_Cmirror)

        print(f"{i:>8} | {own_sector:>6} | {same_sim:>+0.4f}     | {cross_sim_origC:>+0.4f}     | {cross_sim_Cmirror:>+0.4f}")

    print()
    print("=== Summary ===")
    print(f"Mean same -> C (own-sector content):  {np.mean(same_sims):+0.4f} ± {np.std(same_sims):.4f}")
    print(f"Mean cross -> C (cpt-sector to own):  {np.mean(cross_sims_origC):+0.4f} ± {np.std(cross_sims_origC):.4f}")
    print(f"Mean cross -> C_mirror (cpt to flip): {np.mean(cross_sims_Cmirror):+0.4f} ± {np.std(cross_sims_Cmirror):.4f}")

    # Random baseline
    k4_random_sims = []
    for _ in range(100):
        a = hdc.klein4_random(D, rng)
        b = hdc.klein4_random(D, rng)
        k4_random_sims.append(float(hdc.klein4_similarity(a, b)))
    base = float(np.mean(k4_random_sims))
    print(f"Random baseline:                       {base:+0.4f}")
    print()
    print(f"Above-random: same={(np.mean(same_sims)-base)/(1-base):+0.4f}, "
          f"cross-to-C={(np.mean(cross_sims_origC)-base)/(1-base):+0.4f}, "
          f"cross-to-Cmirror={(np.mean(cross_sims_Cmirror)-base)/(1-base):+0.4f}")

    # F132 §7 prediction tests (matching F139 methodology)
    print()
    print("=== F132 §7 + F139 prediction tests (after multi-class cascade) ===")
    p1 = np.mean(same_sims) > base + 0.03
    p2 = np.mean(cross_sims_origC) < base - 0.01  # F139 found anti-correlation
    p3 = np.mean(cross_sims_Cmirror) > base + 0.03
    p4 = abs(np.mean(cross_sims_Cmirror) - np.mean(same_sims)) < 0.02
    print(f"  P1 (same > random + 0.03):       {p1}")
    print(f"  P2 (cross-to-C anti-correlates): {p2}")
    print(f"  P3 (cross-to-Cmirror > random):  {p3}")
    print(f"  P4 (cross-Cmirror ≈ same):       {p4}")

    out_path = Path(__file__).parent / "R-RBS-LM-100_results.json"
    out_path.write_text(json.dumps({
        "srmech_version": SRMECH_VERSION,
        "has_native": HAS_NATIVE,
        "abi": NATIVE_ABI_VERSION,
        "D": D,
        "n_nodes": n_nodes,
        "edge_density": edge_density,
        "N_concepts": N_concepts,
        "n_edges": len(edges),
        "seed": 42,
        "selected_eigvals": selected_eigvals,
        "mean_same_sim": float(np.mean(same_sims)),
        "mean_cross_to_C": float(np.mean(cross_sims_origC)),
        "mean_cross_to_Cmirror": float(np.mean(cross_sims_Cmirror)),
        "random_baseline": base,
        "P1_pass": bool(p1),
        "P2_pass": bool(p2),
        "P3_pass": bool(p3),
        "P4_pass": bool(p4),
        "all_predictions_pass": bool(p1 and p2 and p3 and p4),
        "per_concept": [{
            "i": cm["i"], "sector": cm["sector"], "eig_idx": cm["eig_idx"], "eigval": cm["eigval"],
            "same_sim": same_sims[cm["i"]],
            "cross_to_C": cross_sims_origC[cm["i"]],
            "cross_to_Cmirror": cross_sims_Cmirror[cm["i"]],
        } for cm in concepts_meta],
    }, indent=2))
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
