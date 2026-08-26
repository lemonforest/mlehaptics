"""R-RBS-NN-13b — Mixed-precision Tier 1 (hybrid encoding)

Phase 3b of R-RBS-NN-10_FOLLOWUP_PHASED_PLAN.md.

Per F146 §6: hybrid encoding (Klein-4 chirality + polar overlay) gives
+0.32 above-rand at scale — best of all tested variants in the
controlled F146 experiment. This test asks: does hybrid encoding give
better retrieval at the STORAGE level (after going through learn /
bundle / retrieve cycle)?

Three-way comparison at N=100, D=8192:
  A: Tier 1 = pure Klein-4 (current default)
  B: Tier 1 = pure polar
  C: Tier 1 = hybrid (Klein-4 chirality + polar overlay; per R-RBS-NN-4 §3.4)

For each variant, we override the bridge `_klein4_to_polar` to handle
the source variant correctly, then measure retrieval.

This test extends the existing two-tier storage WITHOUT subclassing —
we just configure the Tier 1 encoding choice per concept.
"""
import json
import time
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
Tier1Concept = _mod.Tier1Concept

# Also load R-RBS-NN-4 encoder for the variant logic
_enc_spec = importlib.util.spec_from_file_location(
    "token_encoder_4", Path(__file__).parent / "R-RBS-NN-4_token_encoder.py"
)
_enc_mod = importlib.util.module_from_spec(_enc_spec)
sys.modules["token_encoder_4"] = _enc_mod
_enc_spec.loader.exec_module(_enc_mod)
encode_token = _enc_mod.encode_token

from srmech.amsc import hdc
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION


class MixedPrecisionStorage(TwoTierRBSNNStorage):
    """Two-tier storage with per-concept variant choice.

    Each concept can be encoded as 'klein4', 'polar', or 'hybrid'.
    The bridge to Tier 2 adapts per variant:
      - klein4 → polar via state-XOR-bit sign extraction (parent class)
      - polar → polar identity
      - hybrid → already polar-typed (no bridge needed)
    """

    def __init__(self, D: int = 8192, seed: int = 42):
        super().__init__(D=D, seed=seed)
        # Track per-concept variant choice
        self.concept_variant: dict[str, str] = {}

    def encode_concept_variant(
        self,
        token: str,
        variant: str = "klein4",
        chirality_sector: int = 0,
        plasticity_density: float = 0.67,
    ) -> Tier1Concept:
        """Encode a concept with explicit variant choice.

        For klein4: stored as Klein-4 HV with sector tag (parent class behavior)
        For polar:  stored as polar HV directly (skips Klein-4)
        For hybrid: Klein-4 + polar overlay (per R-RBS-NN-4 hybrid path)

        Note: this returns a Tier1Concept whose .hv field is the encoded HV
        IN ITS NATIVE VARIANT TYPE (uint8 for klein4 / hybrid-collapsed-to-polar;
        int8 for polar). The bridge step in learn_association needs to know
        which is which.
        """
        if token in self.tier1:
            return self.tier1[token]

        if variant == "klein4":
            return self.encode_concept(token, chirality_sector=chirality_sector)
        elif variant in ("polar", "hybrid"):
            # R-RBS-NN-4 encoder class_hint mapping:
            #   polar variant → 'plasticity' class_hint (produces polar HV)
            #   hybrid variant → 'hybrid' class_hint
            class_hint = "plasticity" if variant == "polar" else "hybrid"
            res = encode_token(
                token,
                D=self.D,
                class_hint=class_hint,
                chirality_sector=chirality_sector,
                plasticity_density=plasticity_density,
            )
            concept = Tier1Concept(
                token=token,
                hv=res["hv"],
                sector=chirality_sector,
                encoded_at=time.time(),
            )
            self.tier1[token] = concept
            self.concept_variant[token] = variant
            return concept
        else:
            raise ValueError(f"Unknown variant: {variant!r}")

    def _klein4_to_polar(self, hv: np.ndarray) -> np.ndarray:
        """Bridge that adapts based on the source hv type.

        Klein-4 (uint8 in {0,1,2,3}): use parent class XOR-bit-sign mapping
        Polar (int8 in {-1, 0, +1}): identity (already polar)
        Hybrid (int8 from polar+klein4 combined): identity (already polar)
        """
        if hv.dtype == np.uint8:
            # Klein-4: parent class mapping
            sign_bits = ((hv >> 1) ^ (hv & 1)) == 0
            return np.where(sign_bits, 1, -1).astype(np.int8)
        elif hv.dtype == np.int8:
            # Already polar / hybrid → identity
            return hv
        else:
            raise ValueError(f"Unexpected hv dtype: {hv.dtype}")


def synthetic_lexicon(n):
    return [f"concept_{i:04d}" for i in range(n)]


def random_association_graph(tokens, degree, seed):
    rng = np.random.default_rng(seed)
    n = len(tokens)
    pairs_set = set()
    for i in range(n):
        for _ in range(degree):
            j = int(rng.integers(0, n))
            if j == i:
                j = (j + 1) % n
            key = tuple(sorted([tokens[i], tokens[j]]))
            pairs_set.add(key)
    return list(pairs_set)


def build_storage_with_variant(D, N, variant, seed=42):
    tokens = synthetic_lexicon(N)
    pairs = random_association_graph(tokens, degree=2, seed=N * 7)
    storage = MixedPrecisionStorage(D=D, seed=seed)
    for tok in tokens:
        storage.encode_concept_variant(tok, variant=variant, chirality_sector=0)
    storage.batch_learn(pairs, plasticity_density=0.67)
    return storage, pairs


def measure_retrieval(storage, pairs, top_k=3, max_pairs=200):
    if len(pairs) > max_pairs:
        sampled_idx = np.random.default_rng(0).choice(len(pairs), size=max_pairs, replace=False)
        sampled = [pairs[i] for i in sampled_idx]
    else:
        sampled = pairs
    correct_top_k = 0
    sims_correct = []
    for a, b in sampled:
        retrieved = storage.retrieve_associated(a, top_k=top_k, threshold=0.0)
        if not retrieved:
            continue
        tokens = [t for t, _ in retrieved]
        if b in tokens:
            idx = tokens.index(b)
            correct_top_k += 1
            sims_correct.append(retrieved[idx][1])
    return {
        "p_at_top_k": correct_top_k / len(sampled) if sampled else 0.0,
        "mean_sim_correct": float(np.mean(sims_correct)) if sims_correct else 0.0,
        "n_evaluated": len(sampled),
    }


def main():
    D = 8192
    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}")
    print()

    results = []
    print(f"{'variant':<15} | {'N':>4} | {'p@3':>6} | {'mean sim':>8} | {'comp density':>13} | {'build (s)':>10}")
    print("-" * 90)
    for N in [50, 100, 200]:
        for variant in ["klein4", "polar", "hybrid"]:
            t = time.time()
            storage, pairs = build_storage_with_variant(D, N, variant)
            t_build = time.time() - t
            metrics = measure_retrieval(storage, pairs, max_pairs=200)
            att = storage.density_attestation()
            print(
                f"  {variant:<13} | {N:>4} | {metrics['p_at_top_k']:.3f}  | "
                f"{metrics['mean_sim_correct']:+0.3f}   | "
                f"{att.get('composite_density', 0):.3f}         | "
                f"{t_build:.2f}"
            )
            results.append({
                "variant": variant,
                "N": N,
                "p_at_top_k": metrics["p_at_top_k"],
                "mean_sim_correct": metrics["mean_sim_correct"],
                "composite_density": att.get("composite_density"),
                "build_sec": t_build,
            })

    # Hypothesis check
    print()
    print("=" * 80)
    print("Hypothesis check")
    print("=" * 80)
    # Compare hybrid vs klein4 at each N
    for N in [50, 100, 200]:
        klein4_p3 = next(r["p_at_top_k"] for r in results if r["N"] == N and r["variant"] == "klein4")
        polar_p3 = next(r["p_at_top_k"] for r in results if r["N"] == N and r["variant"] == "polar")
        hybrid_p3 = next(r["p_at_top_k"] for r in results if r["N"] == N and r["variant"] == "hybrid")
        print(
            f"  N={N}: klein4={klein4_p3:.3f}, polar={polar_p3:.3f}, hybrid={hybrid_p3:.3f}  "
            f"(F146 §6 prediction: hybrid > both)"
        )
        winner = max([("klein4", klein4_p3), ("polar", polar_p3), ("hybrid", hybrid_p3)],
                     key=lambda x: x[1])
        print(f"        winner: {winner[0]} at {winner[1]:.3f}")

    out = {
        "srmech_version": SRMECH_VERSION,
        "has_native": HAS_NATIVE,
        "D": D,
        "results": results,
    }
    out_path = Path(__file__).parent / "R-RBS-NN-13b_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
