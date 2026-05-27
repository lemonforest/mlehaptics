"""R-RBS-LM-98 — Klein-4 (Class M rank-2 abelian) + Class L (Laplacian) cascade composition

Path 2/6 of the wishlist-gated research resume.

Tests whether Klein-4 HDC binding composes cleanly with Class L graph
Laplacian spectral decomposition. The composition pattern:

  Class L:  build graph -> Laplacian -> eigendecompose
                -> get eigvecs as concept-vectors over node-substrate
  Class M:  encode each eigvec as a Klein-4 hypervector with a
                chirality-axis tag per (γ₅, i·ω₇) sector
  Bundle:   all chirality-tagged eigvec-HVs into one composite memory
  Query:    given a query eigvec, recover its chirality-tag
            AND recover the (sector-filtered) candidate eigvec set

Success criteria:
  1. Klein-4 binding survives the L -> M cascade (no algebraic loss)
  2. Chirality-tag survives bundle + unbind (sector retrieval works)
  3. Per-sector eigvec content is recoverable with above-random similarity
  4. Cross-sector queries return DIFFERENT eigvec subsets (chirality
     discriminates)

This is the FIRST cascade composition test of the new upstream Klein-4
variant. F132 §7 cascade composition test.

Cross-references:
  - srmech.amsc.laplacian (Class L; dense_laplacian + hermitian_eigendecompose)
  - srmech.amsc.hdc.klein4_* (Class M rank-2 abelian)
  - F132 §4-5 (Klein-4 HDC engineering proposal)
"""
import json
import time
from pathlib import Path

import numpy as np

from srmech.amsc import hdc
from srmech.amsc import laplacian
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION


def build_small_graph(n_nodes: int = 32, density: float = 0.15, rng=None):
    """Build a small random undirected graph; return edges + uniform weights."""
    if rng is None:
        rng = np.random.default_rng(0)
    edges = []
    weights = []
    # Random Erdős-Rényi-ish
    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            if rng.random() < density:
                edges.append((i, j))
                weights.append(1.0)
    return n_nodes, edges, weights


def klein4_encode_eigvec(eigvec: np.ndarray, D: int, sector: int, rng) -> np.ndarray:
    """Encode a real-valued eigvec into a Klein-4 hypervector with chirality tag.

    Procedure:
      1. Threshold eigvec into discrete state contributions per HV position
      2. Initialise random klein-4 vector
      3. Apply chirality-axis tag via XOR with sector mask:
         sector 0 (RH orient+ visible matter):    no flip (state 0,0)
         sector 1 (RH orient- dark antimatter):   omega7 flip (state 0,1)
         sector 2 (LH orient+ visible antimatter): gamma5 flip (state 1,0)
         sector 3 (LH orient- dark matter):       both flips = CPT (state 1,1)
    """
    # 1. Build a base klein4 vector seeded by eigvec values (deterministic from eigvec)
    n = len(eigvec)
    # Hash-like mapping eigvec values to {0,1,2,3} states; positions repeat as needed
    indices = np.tile(np.arange(n), (D // n) + 1)[:D]
    # Map each eigvec component into a state via sign + magnitude thresholding
    states = np.zeros(D, dtype=np.uint8)
    for d in range(D):
        v = eigvec[indices[d]]
        # Quantise eigvec value into 4 states using 2-bit Gray-like code
        bit_high = 1 if v > 0 else 0  # gamma5 axis: sign
        bit_low = 1 if abs(v) > 0.1 else 0  # omega7 axis: magnitude
        states[d] = (bit_high << 1) | bit_low

    # 2. Apply chirality-axis tag (sector mask via klein4_bind with constant sector)
    sector_mask = np.full(D, sector, dtype=np.uint8)
    return hdc.klein4_bind(states, sector_mask)


def main():
    rng = np.random.default_rng(42)
    D = 1024
    n_nodes = 32
    edge_density = 0.15

    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}")
    print(f"D={D}, n_nodes={n_nodes}, edge_density={edge_density}")
    print()

    # Step 1: Class L - build graph + Laplacian eigendecompose
    print("Step 1: Class L (graph Laplacian eigendecompose)")
    t0 = time.time()
    n, edges, weights = build_small_graph(n_nodes, edge_density, rng)
    print(f"  Graph: n={n}, |E|={len(edges)}")
    L = laplacian.dense_laplacian(n, edges, weights)
    eigvals, eigvecs = laplacian.hermitian_eigendecompose(L)
    eigvecs = eigvecs.real  # discard imag noise per UPSTREAM_NOTES §2.1
    t_classL = time.time() - t0
    print(f"  Laplacian eigendecompose: {t_classL:.2f}s; eigvals shape={eigvals.shape}; eigvecs shape={eigvecs.shape}")
    print(f"  Smallest 3 eigvals: {eigvals[:3]}")
    print(f"  Largest 3 eigvals:  {eigvals[-3:]}")
    print()

    # Step 2: Class M - encode eigvecs into klein-4 HVs with chirality tags
    print("Step 2: Class M (Klein-4 chirality-tagged HDC encoding)")
    t0 = time.time()
    # Assign sectors round-robin across eigvecs
    sectors = [i % 4 for i in range(n)]  # 4 sectors per (γ₅, iω₇)
    eigvec_hvs = []
    for i in range(n):
        hv = klein4_encode_eigvec(eigvecs[:, i], D, sectors[i], rng)
        eigvec_hvs.append(hv)
    t_encode = time.time() - t0
    print(f"  Encoded {n} eigvecs into klein-4 HVs (D={D}): {t_encode:.3f}s")
    print(f"  Sector distribution: {[sum(1 for s in sectors if s == k) for k in range(4)]}")
    print()

    # Step 3: Bundle ALL chirality-tagged eigvec-HVs into one composite memory
    print("Step 3: Klein-4 bundle (all chirality-tagged eigvec-HVs into composite memory)")
    t0 = time.time()
    composite = hdc.klein4_bundle(*eigvec_hvs)
    t_bundle = time.time() - t0
    print(f"  Bundle: {t_bundle:.3f}s; sector_count of composite: {hdc.klein4_sector_count(composite).tolist()}")
    print()

    # Step 4: Query - given each eigvec HV, recover its chirality-tag
    print("Step 4: Chirality-tag recovery (success criterion 2)")
    t0 = time.time()
    correct_tags = 0
    similarities_to_self = []
    similarities_to_others = []
    for i in range(n):
        # Test each of the 4 possible sector masks; the one giving highest similarity wins
        best_sim = -1
        best_sector = -1
        for s in range(4):
            sector_mask = np.full(D, s, dtype=np.uint8)
            unbound = hdc.klein4_unbind(composite, sector_mask)
            sim = float(hdc.klein4_similarity(unbound, eigvec_hvs[i]))
            if sim > best_sim:
                best_sim = sim
                best_sector = s
        if best_sector == sectors[i]:
            correct_tags += 1
        similarities_to_self.append(best_sim)
    t_query = time.time() - t0
    tag_recall = correct_tags / n
    print(f"  Chirality-tag recall: {correct_tags}/{n} = {tag_recall:.3f}")
    print(f"  Query time: {t_query:.3f}s")
    print(f"  Mean self-sim: {np.mean(similarities_to_self):.4f}")
    print()

    # Step 5: Cross-sector discrimination test (success criterion 4)
    print("Step 5: Cross-sector discrimination")
    t0 = time.time()
    # For each sector, retrieve candidates and check they come from that sector
    sector_retrieval = {s: {"true": 0, "false": 0} for s in range(4)}
    for query_sector in range(4):
        sector_mask = np.full(D, query_sector, dtype=np.uint8)
        unbound = hdc.klein4_unbind(composite, sector_mask)
        # Find top-N eigvec HVs by similarity to unbound
        sims = [float(hdc.klein4_similarity(unbound, hv)) for hv in eigvec_hvs]
        top_k = np.argsort(sims)[::-1][:n // 4]
        for idx in top_k:
            if sectors[idx] == query_sector:
                sector_retrieval[query_sector]["true"] += 1
            else:
                sector_retrieval[query_sector]["false"] += 1
    t_disc = time.time() - t0
    print(f"  Cross-sector discrimination: {t_disc:.3f}s")
    for s in range(4):
        tp = sector_retrieval[s]["true"]
        fp = sector_retrieval[s]["false"]
        total = tp + fp
        precision = tp / total if total > 0 else 0.0
        random_prec = 0.25  # 1/4 = expected baseline
        print(f"  Sector {s}: precision = {tp}/{total} = {precision:.3f} (random baseline = {random_prec:.3f})")
    print()

    # Calibrate Klein-4 random baseline for above-random sim
    k4_random_sims = []
    for _ in range(50):
        a = hdc.klein4_random(D, rng)
        b = hdc.klein4_random(D, rng)
        k4_random_sims.append(float(hdc.klein4_similarity(a, b)))
    k4_random_mean = float(np.mean(k4_random_sims))
    print(f"Klein-4 random-pair similarity baseline: {k4_random_mean:.4f}")
    self_sim_above_random = [
        (s - k4_random_mean) / (1.0 - k4_random_mean) for s in similarities_to_self
    ]
    print(f"Mean above-random self-sim: {np.mean(self_sim_above_random):.4f}")
    print()

    # OPEN_SPECTRUM_VERIFICATION block
    print("=" * 80)
    print("OPEN_SPECTRUM_VERIFICATION")
    print("=" * 80)
    print(f"Source: srmech.amsc.laplacian + srmech.amsc.hdc upstream v{SRMECH_VERSION}")
    print(f"D={D}, n_nodes={n_nodes}, edge_density={edge_density}, seed=42")
    print(f"Cascade: Class L (Laplacian eigendecompose) -> Class M (Klein-4 chirality-tag)")
    print(f"Success criteria:")
    print(f"  1. Klein-4 binding survives cascade: ALL operations completed without algebraic error")
    print(f"  2. Chirality-tag recall: {tag_recall:.3f} (random baseline = 0.25)")
    print(f"  3. Above-random self-sim: {np.mean(self_sim_above_random):.4f}")
    print(f"  4. Cross-sector discrimination above random: see step 5 per-sector precision")

    # Write results JSON
    out_path = Path(__file__).parent / "R-RBS-LM-98_results.json"
    out_path.write_text(json.dumps({
        "srmech_version": SRMECH_VERSION,
        "has_native": HAS_NATIVE,
        "abi": NATIVE_ABI_VERSION,
        "D": D,
        "n_nodes": n_nodes,
        "edge_density": edge_density,
        "n_edges": len(edges),
        "eigvals_smallest_3": [float(x) for x in eigvals[:3]],
        "eigvals_largest_3": [float(x) for x in eigvals[-3:]],
        "tag_recall": tag_recall,
        "mean_self_sim": float(np.mean(similarities_to_self)),
        "mean_above_random_self_sim": float(np.mean(self_sim_above_random)),
        "klein4_random_baseline": k4_random_mean,
        "sector_retrieval": sector_retrieval,
        "timings": {
            "classL_seconds": t_classL,
            "encode_seconds": t_encode,
            "bundle_seconds": t_bundle,
            "query_seconds": t_query,
            "discrimination_seconds": t_disc,
        },
    }, indent=2))
    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
