"""R-RBS-NN-16 — Phase 5 remaining candidates (F140 + F-R12 + F139 harmonic extensions)

Three sub-tests:

  Test 1 (F140 cascade harmonic ordering):
    Standard F140 cascade is L(H3) + M-bipolar(H2) + I(H3) + M-klein4(H2).
    Compare:
      Variant A — H3 first, then H2 (L + I + M-bipolar + M-klein4)
      Variant B — H2 first, then H3 (M-bipolar + M-klein4 + L overlay + I shift)
      Variant C — interleaved (F140 baseline)
    Measure chirality discrimination signal per variant.

  Test 2 (F-R12 harmonic bucketing):
    Build 3 hierarchical storage variants on a structured harmonic-labeled corpus:
      'hash' — F-R12 baseline
      'sector_then_hash' — F-R12 alternative
      'harmonic' — NEW: group H1 / H2 / H3 tokens into separate bucket groups
    Measure retrieval quality per strategy.

  Test 3 (F139 3-cycle Klein-4 rotation):
    Apply a 3-cycle permutation to sector tags (0 → 1 → 2 → 0; skip 3).
    Test whether 3-cycle rotation gives meaningful retrieval distinct from
    full CPT mirror (XOR with 3).

Per user intuition: this maps to NN architecture and brain structure
(cortical laterality, cyclic gamma rhythms, triple-stream processing).
Per [[feedback_no_lineage_claims_in_notebook]]: framework-level structural
reading; no biological/clinical claims.
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

_spec_h = importlib.util.spec_from_file_location(
    "hierarchical_storage", Path(__file__).parent / "R-RBS-NN-12_hierarchical_storage.py"
)
_mod_h = importlib.util.module_from_spec(_spec_h)
sys.modules["hierarchical_storage"] = _mod_h
_spec_h.loader.exec_module(_mod_h)
HierarchicalTwoTierRBSNNStorage = _mod_h.HierarchicalTwoTierRBSNNStorage
recommend_n_buckets = _mod_h.recommend_n_buckets

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


# ============================================================
# TEST 1 — F140 cascade harmonic ordering
# ============================================================
def test_1_cascade_ordering(D, N, rng):
    """Test cascade with different harmonic orderings."""
    sectors = [i % 4 for i in range(N)]
    base_concepts = [hdc.klein4_random(D, np.random.default_rng(i)) for i in range(N)]

    def cascade(operators, concept, sector, idx):
        """Apply operators in order; return encoded HV."""
        hv = concept.copy()
        for op in operators:
            if op == "L_spectral":
                # Class L (H3): apply a random Class-L-like permutation
                # Use a fixed seed for reproducibility, derive from concept idx
                spec_rng = np.random.default_rng(idx * 31)
                perm = spec_rng.permutation(D)
                hv = hv[perm]
            elif op == "I_cyclic":
                hv = np.roll(hv, (idx + 1) * 137 % D)
            elif op == "M_bipolar":
                bp = np.random.default_rng(idx + 1000).choice([-1, 1], size=D).astype(np.int8)
                bp_k4 = ((bp + 1) // 2).astype(np.uint8)
                hv = hdc.klein4_bind(hv, bp_k4)
            elif op == "M_klein4_tag":
                hv = hdc.klein4_bind(hv, np.full(D, sector, dtype=np.uint8))
            else:
                raise ValueError(f"Unknown op: {op}")
        return hv

    # Three orderings
    orderings = {
        "A_H3_then_H2": ["L_spectral", "I_cyclic", "M_bipolar", "M_klein4_tag"],
        "B_H2_then_H3": ["M_bipolar", "M_klein4_tag", "L_spectral", "I_cyclic"],
        "C_interleaved": ["L_spectral", "M_bipolar", "I_cyclic", "M_klein4_tag"],  # F140 baseline
    }

    base = random_baseline_klein4(D, rng)
    results = {}

    for order_name, ops in orderings.items():
        encoded = [cascade(ops, base_concepts[i], sectors[i], i) for i in range(N)]
        composite = hdc.klein4_bundle(*encoded)
        # Chirality discrimination test (F139-style)
        # For variant B, the chirality tag is in the middle, not outermost — different unbind needed
        # For variants A and C with klein4_tag as outermost, we can unbind directly
        # For variant B, unbind needs to reverse the L_spectral and I_cyclic after unbinding the tag
        # Simplest comparison: unbind with sector mask, compare against intermediate pre-tag HV
        sames = []
        for i in range(N):
            # Reconstruct the intermediate pre-tag HV
            intermediate_ops = ops[:-1] if order_name in ("A_H3_then_H2", "C_interleaved") else ops[:1] + ops[2:]
            # Simpler: for non-tag-last variants, we just measure round-trip via klein4_tag op
            if order_name in ("A_H3_then_H2", "C_interleaved"):
                # tag is last; unbind by XORing with sector
                same_unbound = hdc.klein4_unbind(composite, np.full(D, sectors[i], dtype=np.uint8))
                # Intermediate = same cascade without final tag
                interm = cascade(ops[:-1], base_concepts[i], sectors[i], i)
                sames.append(float(hdc.klein4_similarity(same_unbound, interm)))
            else:
                # Variant B: M_klein4_tag is at index 1; the sector mask is bound there but
                # subsequent L_spectral and I_cyclic operations were applied AFTER.
                # To recover the SECTOR-TAGGED intermediate, we'd need to inverse L_spectral and I_cyclic,
                # which are not bind-style invertible. So we measure differently for B:
                # we measure how well the composite preserves chirality structure by comparing
                # to a SECTOR-FLIPPED version of the same encoding.
                # Specifically: unbind with sector tag (won't be clean), compare to encoded[i].
                same_unbound = hdc.klein4_unbind(composite, np.full(D, sectors[i], dtype=np.uint8))
                sames.append(float(hdc.klein4_similarity(same_unbound, encoded[i])))

        above_rand = (float(np.mean(sames)) - base) / (1 - base)
        results[order_name] = {
            "raw_sim": float(np.mean(sames)),
            "above_rand": above_rand,
            "ops": ops,
        }
    return results, base


# ============================================================
# TEST 2 — F-R12 harmonic bucketing
# ============================================================
def build_harmonic_lexicon():
    """A 19-token corpus with explicit harmonic labels.

    Returns (tokens, token_harmonics, pair_associations)
    """
    h1_tokens = ["apple", "water", "calendar", "engine", "octahedron"]
    h2_tokens = ["L_alanine", "D_alanine", "left_helix", "right_helix",
                 "ccw_rotation", "cw_rotation", "levo_glucose", "dextro_glucose"]
    h3_tokens = ["triad_a_part1", "triad_a_part2", "triad_a_part3",
                 "cyclic_b_step1", "cyclic_b_step2", "cyclic_b_step3"]

    tokens = h1_tokens + h2_tokens + h3_tokens
    harmonics = {t: 1 for t in h1_tokens} | {t: 2 for t in h2_tokens} | {t: 3 for t in h3_tokens}

    pairs = [
        # H1: arbitrary content pairs
        ("apple", "water"),
        ("calendar", "engine"),
        # H2: chiral pairs (Klein-4 sectors 0 ↔ 2)
        ("L_alanine", "D_alanine"),
        ("left_helix", "right_helix"),
        ("ccw_rotation", "cw_rotation"),
        ("levo_glucose", "dextro_glucose"),
        # H3: triplet cyclic bindings
        ("triad_a_part1", "triad_a_part2"),
        ("triad_a_part2", "triad_a_part3"),
        ("triad_a_part3", "triad_a_part1"),
        ("cyclic_b_step1", "cyclic_b_step2"),
        ("cyclic_b_step2", "cyclic_b_step3"),
        ("cyclic_b_step3", "cyclic_b_step1"),
    ]
    return tokens, harmonics, pairs


class HarmonicBucketedStorage(HierarchicalTwoTierRBSNNStorage):
    """Hierarchical storage with harmonic-based bucket assignment.

    Buckets are partitioned into 3 harmonic groups:
      Group H1 (chirality-invariant): buckets 0..n_buckets/3-1
      Group H2 (chiral inverse):       buckets n_buckets/3..2*n_buckets/3-1
      Group H3 (chiral rotation):      buckets 2*n_buckets/3..n_buckets-1

    Tokens get routed to their harmonic group's bucket subset, then
    hash-routed within that subset.
    """

    def __init__(self, D, n_buckets, token_harmonics, seed=42):
        # Ensure n_buckets is divisible by 3 for clean partitioning
        n_buckets = max(3, ((n_buckets + 2) // 3) * 3)
        super().__init__(D=D, n_buckets=n_buckets, seed=seed, bucket_strategy="hash")
        self.token_harmonics = token_harmonics
        self.bucket_strategy = "harmonic"  # override

    def _bucket_for(self, token: str) -> int:
        harmonic = self.token_harmonics.get(token, 1)
        sub_buckets = self.n_buckets // 3
        group_base = (harmonic - 1) * sub_buckets
        from srmech.amsc import format as amsc_format
        digest = amsc_format.sha256_bytes(token.encode("utf-8"))
        sub_idx = int(digest[:8], 16) % sub_buckets
        return group_base + sub_idx


def test_2_harmonic_bucketing(D):
    """Test 3 bucketing strategies on harmonic-labeled corpus."""
    tokens, harmonics, pairs = build_harmonic_lexicon()
    n_buckets = 9  # ensure divisibility by 3 for harmonic grouping

    storages = {}

    # Hash bucketing (F-R12 baseline)
    s_hash = HierarchicalTwoTierRBSNNStorage(D=D, n_buckets=n_buckets, seed=42, bucket_strategy="hash")
    for t in tokens:
        s_hash.encode_concept(t)
    s_hash.batch_learn(pairs, plasticity_density=0.67)
    storages["hash"] = s_hash

    # Sector-then-hash bucketing
    s_sector = HierarchicalTwoTierRBSNNStorage(D=D, n_buckets=n_buckets, seed=42, bucket_strategy="sector_then_hash")
    for t in tokens:
        s_sector.encode_concept(t, auto_sector=True)  # use chirality classifier
    s_sector.batch_learn(pairs, plasticity_density=0.67)
    storages["sector"] = s_sector

    # Harmonic bucketing
    s_harm = HarmonicBucketedStorage(D=D, n_buckets=n_buckets, token_harmonics=harmonics, seed=42)
    for t in tokens:
        s_harm.encode_concept(t, auto_sector=True)
    s_harm.batch_learn(pairs, plasticity_density=0.67)
    storages["harmonic"] = s_harm

    # Measure retrieval per strategy
    results = {}
    for strategy, storage in storages.items():
        correct = 0
        for a, b in pairs:
            retrieved = storage.retrieve_associated(a, top_k=5, threshold=0.0)
            tokens_ret = [t for t, _ in retrieved]
            if b in tokens_ret:
                correct += 1
        dist = storage.bucket_distribution()
        results[strategy] = {
            "precision_top_5": correct / len(pairs),
            "bucket_sizes": dist["bucket_sizes"],
            "max_bucket": dist["max_bucket"],
        }
    return results


# ============================================================
# TEST 3 — F139 3-cycle Klein-4 rotation
# ============================================================
def sector_3_cycle(sector: int) -> int:
    """3-cycle permutation through {0, 1, 2}; sector 3 → 3 (fixed point)."""
    if sector == 0:
        return 1
    elif sector == 1:
        return 2
    elif sector == 2:
        return 0
    else:
        return 3


def test_3_3cycle_rotation(D, N, rng):
    """F139-style cross-sector retrieval but with 3-cycle rotation vs CPT mirror."""
    sectors = [i % 3 for i in range(N)]  # restrict to {0, 1, 2}; skip sector 3
    concepts = [hdc.klein4_random(D, rng) for _ in range(N)]
    tagged = [hdc.klein4_bind(c, np.full(D, s, dtype=np.uint8)) for c, s in zip(concepts, sectors)]
    composite = hdc.klein4_bundle(*tagged)
    base = random_baseline_klein4(D, rng)

    # F139 predictions per concept i with own sector s_i:
    # same: unbind with s_i, compare to c_i (should match if direct retrieval works)
    # cpt:  unbind with (s_i XOR 3), compare to c_i (should anti-correlate per F139)
    # 3cyc: unbind with sector_3_cycle(s_i), compare to c_i (NEW; harmonic-3 test)

    same_to_C, cpt_to_C, cyc_to_C, cyc_to_C_rotated = [], [], [], []

    for i, c in enumerate(concepts):
        own_s = sectors[i]
        cpt_s = own_s ^ 3
        cyc_s = sector_3_cycle(own_s)
        cyc_rotation_mask = own_s ^ cyc_s  # the XOR equivalent of the rotation

        # Same-sector
        same_unbound = hdc.klein4_unbind(composite, np.full(D, own_s, dtype=np.uint8))
        same_to_C.append(float(hdc.klein4_similarity(same_unbound, c)))

        # CPT mirror
        cpt_unbound = hdc.klein4_unbind(composite, np.full(D, cpt_s, dtype=np.uint8))
        cpt_to_C.append(float(hdc.klein4_similarity(cpt_unbound, c)))

        # 3-cycle: unbind with the 3-cycled sector
        cyc_unbound = hdc.klein4_unbind(composite, np.full(D, cyc_s, dtype=np.uint8))
        cyc_to_C.append(float(hdc.klein4_similarity(cyc_unbound, c)))
        # 3-cycle to rotated-target: compare cyc_unbound to c_rotated (the 3-cycle-rotated concept)
        c_rotated = hdc.klein4_bind(c, np.full(D, cyc_rotation_mask, dtype=np.uint8))
        cyc_to_C_rotated.append(float(hdc.klein4_similarity(cyc_unbound, c_rotated)))

    return {
        "same_to_C": float(np.mean(same_to_C)),
        "cpt_to_C_anticorrelation": float(np.mean(cpt_to_C)),
        "cyc_to_C": float(np.mean(cyc_to_C)),
        "cyc_to_C_rotated": float(np.mean(cyc_to_C_rotated)),
        "random_baseline": base,
        "above_rand": {
            "same": (float(np.mean(same_to_C)) - base) / (1 - base),
            "cpt": (float(np.mean(cpt_to_C)) - base) / (1 - base),
            "cyc": (float(np.mean(cyc_to_C)) - base) / (1 - base),
            "cyc_rotated": (float(np.mean(cyc_to_C_rotated)) - base) / (1 - base),
        },
    }


def main():
    D = 8192
    rng = np.random.default_rng(42)
    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}")
    print()

    # ============================================================
    # TEST 1
    # ============================================================
    print("=" * 80)
    print("TEST 1 — F140 cascade harmonic ordering")
    print("=" * 80)
    test1_res, base1 = test_1_cascade_ordering(D, N=16, rng=rng)
    print(f"  Random baseline: {base1:.4f}")
    for order_name, res in test1_res.items():
        print(f"  {order_name:<25}: raw={res['raw_sim']:+0.4f}, above-rand={res['above_rand']:+0.4f}")

    # ============================================================
    # TEST 2
    # ============================================================
    print()
    print("=" * 80)
    print("TEST 2 — F-R12 harmonic bucketing on harmonic-labeled corpus")
    print("=" * 80)
    test2_res = test_2_harmonic_bucketing(D)
    for strategy, res in test2_res.items():
        print(f"  {strategy:<10}: p@5={res['precision_top_5']:.3f}  bucket_sizes={res['bucket_sizes']}  max={res['max_bucket']}")

    # ============================================================
    # TEST 3
    # ============================================================
    print()
    print("=" * 80)
    print("TEST 3 — F139 3-cycle Klein-4 rotation (sectors {0,1,2}; skip 3)")
    print("=" * 80)
    test3_res = test_3_3cycle_rotation(D, N=24, rng=rng)
    print(f"  Random baseline: {test3_res['random_baseline']:.4f}")
    ar = test3_res["above_rand"]
    print(f"  same-sector to C:        sim={test3_res['same_to_C']:+0.4f}  above-rand={ar['same']:+0.4f}")
    print(f"  CPT-mirror to C:         sim={test3_res['cpt_to_C_anticorrelation']:+0.4f}  above-rand={ar['cpt']:+0.4f} (expect anti-correlation per F139)")
    print(f"  3-cycle to C (raw):      sim={test3_res['cyc_to_C']:+0.4f}  above-rand={ar['cyc']:+0.4f}")
    print(f"  3-cycle to C_rotated:    sim={test3_res['cyc_to_C_rotated']:+0.4f}  above-rand={ar['cyc_rotated']:+0.4f} (does rotation recover the rotated target?)")

    # ============================================================
    # Hypothesis check
    # ============================================================
    print()
    print("=" * 80)
    print("Hypothesis check across all 3 tests")
    print("=" * 80)

    # Test 1: which cascade ordering wins?
    best_order = max(test1_res.items(), key=lambda x: x[1]["above_rand"])
    print(f"  Test 1: best cascade ordering = {best_order[0]} (above-rand {best_order[1]['above_rand']:+0.4f})")

    # Test 2: which bucketing wins?
    best_bucketing = max(test2_res.items(), key=lambda x: x[1]["precision_top_5"])
    print(f"  Test 2: best bucketing = {best_bucketing[0]} (p@5 {best_bucketing[1]['precision_top_5']:.3f})")

    # Test 3: does 3-cycle to rotated target work?
    cyc_recovers_rotated = ar["cyc_rotated"] > 0.10  # arbitrary threshold
    print(f"  Test 3: 3-cycle recovers rotated target (above-rand > 0.10): {cyc_recovers_rotated}")
    print(f"          above-rand same: {ar['same']:+0.3f}")
    print(f"          above-rand cyc-rotated: {ar['cyc_rotated']:+0.3f}")

    out = {
        "srmech_version": SRMECH_VERSION,
        "D": D,
        "test_1_cascade_ordering": test1_res,
        "test_2_harmonic_bucketing": test2_res,
        "test_3_3cycle_rotation": test3_res,
        "hypothesis_summary": {
            "best_cascade_ordering": best_order[0],
            "best_bucketing_strategy": best_bucketing[0],
            "3cycle_recovers_rotated": cyc_recovers_rotated,
        },
    }
    out_path = Path(__file__).parent / "R-RBS-NN-16_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
