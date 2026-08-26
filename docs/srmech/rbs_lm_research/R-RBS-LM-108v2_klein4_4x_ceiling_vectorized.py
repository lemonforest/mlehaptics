"""R-RBS-LM-108v2 — Klein-4 4× ceiling deep dive (VECTORIZED)

Methodology refinement: R-RBS-LM-108 v1 used Python-loop pairwise similarity
which hit O(V²) Python-call overhead (V=2000 ran 46 min before killed).

V2 uses numpy vectorization: stack candidate vectors into (V, D) matrix;
compute all similarities in ONE numpy operation.

Expected speedup: 100×-1000× over v1's per-pair Python loops.

Substrate clarification per user direction 2026-05-28:
  srmech is C/Python parity (native C with Python wrappers).
  The slow path is the PYTHON LOOP calling fast C primitives.
  Vectorized numpy ops match what the native C ops do internally.
  For hot paths that don't vectorize cleanly, Julia is the right tool.
  This rewrite stays in Python+numpy since the shape vectorizes cleanly.
"""
import json
import time
from pathlib import Path

import numpy as np

from srmech.amsc import hdc, format as amsc_format
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION


def token_seed(name: str) -> int:
    return int(amsc_format.sha256_bytes(name.encode("utf-8"))[:8], 16)


def encode_bipolar_batch(names, D):
    """Encode N tokens into a (N, D) int8 matrix."""
    out = np.empty((len(names), D), dtype=np.int8)
    for i, name in enumerate(names):
        rng = np.random.default_rng(token_seed(name))
        out[i] = rng.choice([-1, 1], size=D).astype(np.int8)
    return out


def encode_klein4_batch(names, D, sectors=None):
    """Encode N tokens into a (N, D) uint8 matrix; optional per-token sector tags."""
    out = np.empty((len(names), D), dtype=np.uint8)
    for i, name in enumerate(names):
        rng = np.random.default_rng(token_seed(name))
        hv = hdc.klein4_random(D, rng)
        if sectors is not None:
            hv = hdc.klein4_bind(hv, np.full(D, sectors[i], dtype=np.uint8))
        out[i] = hv
    return out


def vectorized_match_fraction(query, candidates):
    """Vectorized match-fraction: query is (D,); candidates is (V, D).

    Returns (V,) array of (query == candidates).mean(axis=1).
    """
    return (candidates == query).mean(axis=1)


def test_bipolar_vocab_capacity(D, V):
    """Bipolar associative memory: bundle V context↔token bindings, vectorized recall."""
    # Generate V context and token HVs as matrices (V, D)
    contexts = encode_bipolar_batch([f"context_{i:05d}" for i in range(V)], D)
    tokens = encode_bipolar_batch([f"token_{i:05d}" for i in range(V)], D)
    # Bind: element-wise sign-product (V, D)
    bound = contexts * tokens
    # Bundle: sign of column-sum (D,)
    s = bound.sum(axis=0)
    composite = np.where(s >= 0, 1, -1).astype(np.int8)
    # Vectorized recall: for each context i, candidate_B = composite * context_i
    # Then find argmax similarity to any token
    candidate_Bs = composite[np.newaxis, :] * contexts  # (V, D) — broadcast composite
    # For each candidate, compute similarity to all tokens via matrix product
    # candidate_Bs @ tokens.T gives (V, V) of dot products (range -D..+D)
    sim_matrix = candidate_Bs.astype(np.int32) @ tokens.T.astype(np.int32)  # (V, V)
    # argmax along axis=1: which token is closest to each candidate
    preds = sim_matrix.argmax(axis=1)
    truth = np.arange(V)
    return float((preds == truth).mean())


def test_klein4_chirality_blind_capacity(D, V):
    """Klein-4 all in sector 0; bundled+recalled vectorized."""
    contexts_k4 = encode_klein4_batch([f"context_{i:05d}" for i in range(V)], D, sectors=[0] * V)
    tokens_k4 = encode_klein4_batch([f"token_{i:05d}" for i in range(V)], D, sectors=[0] * V)
    # Pair-bind: klein4 XOR via numpy bitwise XOR (klein-4 values are uint8 in {0,1,2,3})
    # The klein4_bind upstream is XOR over (F_2)^2; equivalent to bitwise XOR for uint8 in {0,1,2,3}.
    bound = contexts_k4 ^ tokens_k4  # (V, D) uint8
    # Bundle: per-position majority vote — for klein-4, this is the mode of the column
    # Vectorized mode: count occurrences of each state per column
    # Use bincount along axis=0
    counts = np.zeros((4, D), dtype=np.int32)
    for s in range(4):
        counts[s] = (bound == s).sum(axis=0)
    composite = counts.argmax(axis=0).astype(np.uint8)  # (D,)
    # Recall: unbind composite XOR context_i = candidate token; compare to all tokens
    candidate_Bs = composite[np.newaxis, :] ^ contexts_k4  # (V, D)
    # For each candidate, match-fraction with each stored token
    # Vectorize: sim_matrix[i, j] = (candidate_Bs[i] == tokens_k4[j]).mean()
    # Done via broadcasting: (V, 1, D) == (1, V, D) → (V, V, D) then mean(-1)
    # For V=2000, D=8192: 2000*2000*8192 = 32B bool → 32GB memory. TOO BIG.
    # Use chunked approach: process candidates in chunks of CHUNK
    CHUNK = 50  # process 50 candidates at a time
    preds = np.empty(V, dtype=np.int64)
    for start in range(0, V, CHUNK):
        end = min(start + CHUNK, V)
        chunk = candidate_Bs[start:end]  # (CHUNK, D)
        # (CHUNK, 1, D) == (1, V, D) → (CHUNK, V, D)
        sim = (chunk[:, np.newaxis, :] == tokens_k4[np.newaxis, :, :]).mean(axis=2)
        preds[start:end] = sim.argmax(axis=1)
    truth = np.arange(V)
    return float((preds == truth).mean())


def test_klein4_sectorized_capacity(D, V, n_sectors=4):
    """Klein-4 sectorized: V tokens distributed across 4 sectors, per-sector vectorized recall."""
    # Assign sectors deterministically (hash mod n_sectors)
    sectors = np.array([token_seed(f"token_{i:05d}") % n_sectors for i in range(V)], dtype=np.uint8)
    contexts_k4 = encode_klein4_batch([f"context_{i:05d}" for i in range(V)], D, sectors=sectors.tolist())
    tokens_k4 = encode_klein4_batch([f"token_{i:05d}" for i in range(V)], D, sectors=sectors.tolist())

    # Per-sector composites
    bound_all = contexts_k4 ^ tokens_k4  # (V, D)
    sector_composites = {}
    for s in range(n_sectors):
        mask = (sectors == s)
        if not mask.any():
            continue
        sector_bound = bound_all[mask]
        # Per-position klein-4 majority for this sector
        counts = np.zeros((4, D), dtype=np.int32)
        for state in range(4):
            counts[state] = (sector_bound == state).sum(axis=0)
        sector_composites[s] = counts.argmax(axis=0).astype(np.uint8)

    # Recall: per-token, use its sector composite to unbind, then find argmax over ALL tokens in vocab
    preds = np.empty(V, dtype=np.int64)
    CHUNK = 50
    # Pre-compute candidate_B for all i (using each i's sector composite)
    candidate_Bs = np.empty((V, D), dtype=np.uint8)
    for i in range(V):
        composite = sector_composites.get(int(sectors[i]))
        if composite is None:
            preds[i] = -1
            continue
        candidate_Bs[i] = composite ^ contexts_k4[i]

    for start in range(0, V, CHUNK):
        end = min(start + CHUNK, V)
        chunk = candidate_Bs[start:end]
        sim = (chunk[:, np.newaxis, :] == tokens_k4[np.newaxis, :, :]).mean(axis=2)
        preds[start:end] = sim.argmax(axis=1)
    truth = np.arange(V)
    correct = (preds == truth)
    valid = (preds != -1)
    if not valid.any():
        return 0.0
    return float(correct[valid].mean())


def main():
    D = 8192
    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}")
    print(f"VECTORIZED methodology — numpy batch instead of Python per-pair loops")
    print()

    V_sweep = [100, 250, 500, 1000, 2000, 4000]

    print(f"{'V':>5} | {'bipolar':>10} | {'klein4_blind':>14} | {'klein4_4sec':>13} | time(s)")
    print("-" * 80)
    results = []
    for V in V_sweep:
        t0 = time.time()
        bp = test_bipolar_vocab_capacity(D, V)
        t_bp = time.time() - t0
        t0 = time.time()
        k4_blind = test_klein4_chirality_blind_capacity(D, V)
        t_k4_blind = time.time() - t0
        t0 = time.time()
        k4_sec = test_klein4_sectorized_capacity(D, V, n_sectors=4)
        t_k4_sec = time.time() - t0
        total_t = t_bp + t_k4_blind + t_k4_sec
        print(f"{V:>5} | {bp:>10.3f} | {k4_blind:>14.3f} | {k4_sec:>13.3f} | {total_t:>7.1f}")
        results.append({
            "V": V,
            "bipolar_recall_at_1": bp,
            "klein4_blind_recall_at_1": k4_blind,
            "klein4_4sec_recall_at_1": k4_sec,
            "time_bipolar_s": t_bp,
            "time_klein4_blind_s": t_k4_blind,
            "time_klein4_4sec_s": t_k4_sec,
        })

    print()
    print("=" * 80)
    print("Capacity ceiling analysis (V at which recall ≥ 0.50):")
    print("=" * 80)

    def find_ceiling(results, key):
        ceiling = None
        for r in results:
            if r[key] >= 0.50:
                ceiling = r["V"]
        return ceiling

    bp_ceiling = find_ceiling(results, "bipolar_recall_at_1")
    k4_blind_ceiling = find_ceiling(results, "klein4_blind_recall_at_1")
    k4_sec_ceiling = find_ceiling(results, "klein4_4sec_recall_at_1")

    print(f"  Bipolar ceiling:                   V = {bp_ceiling}")
    print(f"  Klein-4 chirality-blind ceiling:   V = {k4_blind_ceiling}")
    print(f"  Klein-4 4-sector ceiling:          V = {k4_sec_ceiling}")
    print()

    if bp_ceiling and k4_sec_ceiling:
        ratio = k4_sec_ceiling / bp_ceiling
        print(f"  Klein-4-sectorized / bipolar ratio: {ratio:.2f}x")
        if ratio >= 3.5:
            print(f"  → 4× ceiling STRONGLY VALIDATED")
        elif ratio >= 2.5:
            print(f"  → 4× ceiling MODERATELY VALIDATED")
        elif ratio > 1.2:
            print(f"  → SOME lift but not 4×")
        else:
            print(f"  → 4× ceiling NOT VALIDATED")

    out = {
        "srmech_version": SRMECH_VERSION,
        "D": D,
        "V_sweep": V_sweep,
        "results": results,
        "ceilings": {
            "bipolar": bp_ceiling,
            "klein4_blind": k4_blind_ceiling,
            "klein4_4sec": k4_sec_ceiling,
        },
        "ratio_klein4_4sec_vs_bipolar": (k4_sec_ceiling / bp_ceiling) if bp_ceiling and k4_sec_ceiling else None,
        "methodology": "vectorized numpy batch — matrix products and broadcasting; chunked similarity for memory",
    }
    out_path = Path(__file__).parent / "R-RBS-LM-108v2_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
