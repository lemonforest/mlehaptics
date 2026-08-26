"""R-RBS-LM-108 — Klein-4 4× ceiling deep dive for LLM token binding

User direction: upstream doc integration suggested a klein-4 4× ceiling
deep dive as it relates to LLM token binding.

Hypothesis under test:
  Klein-4's 4 chirality sectors function as 4 INDEPENDENT associative-memory
  channels at the same D. If bipolar crashes at V≈C bindings, klein-4
  sectorized should reach V≈4C — a 4× capacity lift via sectorization.

Test pattern (LLM-style token-binding):
  - Build vocabulary of V tokens
  - Build N=V (context, next_token) bindings — each token appears in one binding
  - Bipolar: bundle ALL N bind-pairs into one composite at D
  - Klein-4 sectorized: assign tokens to 4 sectors round-robin; bundle V/4
    pairs per sector at the SAME D; query with sector-tagged unbind
  - Measure recall@1: given each context HV, can we recover its bound token?

V sweep across LLM scales: 100, 500, 1000, 2500, 5000, 10000.

Predictions:
  H1: bipolar recall crashes at V around ~256-512 at D=8192 (per F-R11)
  H2: klein-4 sectorized maintains recall up to V around ~1024-2048 (~4× bipolar)
  H3: if H2 holds, the 4× sectorization mechanism is empirically validated for
      LLM token binding context

Important caveats:
  - Per F137 §3: at MATCHED BITS bipolar beats klein-4 on RAW capacity
  - Per F-R13b: klein-4 doesn't beat bipolar on retrieval at moderate N
  - This test is about SECTORIZATION as multiplier, NOT raw klein-4 advantage
  - Klein-4 here uses 4 PARALLEL independent channels (one per sector); bipolar
    has just one channel
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


def encode_bipolar(name: str, D: int) -> np.ndarray:
    rng = np.random.default_rng(token_seed(name))
    return rng.choice([-1, 1], size=D).astype(np.int8)


def encode_klein4(name: str, D: int, sector: int) -> np.ndarray:
    rng = np.random.default_rng(token_seed(name))
    base = hdc.klein4_random(D, rng)
    sector_mask = np.full(D, sector, dtype=np.uint8)
    return hdc.klein4_bind(base, sector_mask)


def test_bipolar_capacity(D: int, V: int):
    """Standard bipolar associative memory: bundle V context↔token bindings, recall."""
    # Generate V (context, token) pairs
    contexts = [encode_bipolar(f"context_{i:05d}", D) for i in range(V)]
    tokens = [encode_bipolar(f"token_{i:05d}", D) for i in range(V)]
    # Bind: each pair becomes context * token (sign-product)
    bound = [contexts[i] * tokens[i] for i in range(V)]
    # Bundle: sign of sum
    s = np.sum(bound, axis=0).astype(np.int32)
    composite = np.where(s >= 0, 1, -1).astype(np.int8)
    # Recall: for each context, unbind composite and find nearest token
    correct = 0
    for i in range(V):
        candidate = composite * contexts[i]  # unbind
        # Find nearest token in vocab (top-1 by sign-match)
        sims = [float(np.mean(candidate == tokens[j]) * 2 - 1) for j in range(V)]
        best = int(np.argmax(sims))
        if best == i:
            correct += 1
    return correct / V


def test_klein4_sectorized_capacity(D: int, V: int, n_sectors: int = 4):
    """Klein-4 sectorized: distribute V tokens across 4 sectors, bundle per sector."""
    # Assign each token to a sector deterministically (hash mod n_sectors)
    sectors = [token_seed(f"token_{i:05d}") % n_sectors for i in range(V)]
    # Encode contexts and tokens per sector
    contexts = [encode_klein4(f"context_{i:05d}", D, sectors[i]) for i in range(V)]
    tokens = [encode_klein4(f"token_{i:05d}", D, sectors[i]) for i in range(V)]
    # Per-sector bundle of pairs
    sector_bundles = {s: [] for s in range(n_sectors)}
    for i in range(V):
        bound = hdc.klein4_bind(contexts[i], tokens[i])
        sector_bundles[sectors[i]].append(bound)
    composites = {}
    for s in range(n_sectors):
        if sector_bundles[s]:
            composites[s] = hdc.klein4_bundle(*sector_bundles[s])
        else:
            composites[s] = None

    # Recall: for each context, unbind from its sector's composite; find nearest token in vocab
    correct = 0
    for i in range(V):
        s = sectors[i]
        composite = composites[s]
        if composite is None:
            continue
        candidate = hdc.klein4_unbind(composite, contexts[i])
        # Find nearest token in vocab (using klein4_similarity)
        sims = []
        for j in range(V):
            sim = float(hdc.klein4_similarity(candidate, tokens[j]))
            sims.append(sim)
        best = int(np.argmax(sims))
        if best == i:
            correct += 1
    return correct / V


def test_klein4_chirality_blind_capacity(D: int, V: int):
    """Klein-4 chirality-blind: all tokens in sector 0; same as bipolar+more states."""
    contexts = [encode_klein4(f"context_{i:05d}", D, 0) for i in range(V)]
    tokens = [encode_klein4(f"token_{i:05d}", D, 0) for i in range(V)]
    bound = [hdc.klein4_bind(contexts[i], tokens[i]) for i in range(V)]
    composite = hdc.klein4_bundle(*bound)
    correct = 0
    for i in range(V):
        candidate = hdc.klein4_unbind(composite, contexts[i])
        sims = [float(hdc.klein4_similarity(candidate, tokens[j])) for j in range(V)]
        best = int(np.argmax(sims))
        if best == i:
            correct += 1
    return correct / V


def main():
    D = 8192
    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}")
    print()

    # Use smaller V values for time control; O(V^2) retrieve cost
    V_sweep = [100, 250, 500, 1000, 2000]

    print(f"{'V':>5} | {'bipolar':>10} | {'klein4_blind':>14} | {'klein4_4sec':>13} | time(s)")
    print("-" * 80)
    results = []
    for V in V_sweep:
        t0 = time.time()
        bp = test_bipolar_capacity(D, V)
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

    # Find ceiling thresholds
    print()
    print("=" * 80)
    print("Capacity ceiling analysis (V at which recall drops below 0.50):")
    print("=" * 80)

    def find_ceiling(results, key):
        # Find the largest V where recall >= 0.50
        ceiling = None
        for r in results:
            if r[key] >= 0.50:
                ceiling = r["V"]
        return ceiling

    bp_ceiling = find_ceiling(results, "bipolar_recall_at_1")
    k4_blind_ceiling = find_ceiling(results, "klein4_blind_recall_at_1")
    k4_sec_ceiling = find_ceiling(results, "klein4_4sec_recall_at_1")

    print(f"  Bipolar ceiling (recall ≥ 0.50):           V = {bp_ceiling}")
    print(f"  Klein-4 chirality-blind ceiling:           V = {k4_blind_ceiling}")
    print(f"  Klein-4 4-sector ceiling:                  V = {k4_sec_ceiling}")
    print()

    if bp_ceiling and k4_sec_ceiling:
        ratio = k4_sec_ceiling / bp_ceiling
        print(f"  Klein-4-sectorized / bipolar ratio:        {ratio:.2f}x")
        print(f"  Hypothesis: 4x ceiling lift via sectorization.")
        if ratio >= 3.0:
            print(f"  Verdict: STRONG SUPPORT (ratio ≥ 3x)")
        elif ratio >= 2.0:
            print(f"  Verdict: MODERATE SUPPORT (ratio ≥ 2x)")
        elif ratio > 1.1:
            print(f"  Verdict: WEAK SUPPORT (ratio > 1.1)")
        else:
            print(f"  Verdict: NO SUPPORT (ratio ≤ 1.1)")

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
    }
    out_path = Path(__file__).parent / "R-RBS-LM-108_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
