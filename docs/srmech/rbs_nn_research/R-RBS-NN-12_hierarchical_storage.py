"""R-RBS-NN-12 — Hierarchical two-tier storage for N > 257

Phase 2 of R-RBS-NN-10_FOLLOWUP_PHASED_PLAN.md.

Resolves the N=256 ceiling discovered in R-RBS-NN-FINDING_R11 by adding
hash-based bucket routing. Each bucket maintains its own polar composite
memory; bucket size stays below srmech.amsc.hdc.MAX_BUNDLE_N (=257).
Cross-bucket associations are stored in BOTH endpoint buckets so
retrieval from either side works.

Design (T2.1):
  - Hash each token's bucket via Class A SHA-256 content-mint
  - Each bucket has its own polar composite
  - learn_association(a, b) stores binding in bucket_a AND bucket_b
    (same bucket if both tokens hash to same bucket)
  - retrieve_associated(token) queries token's bucket only (O(K) not O(N))
  - Per-bucket coupling-informed decay (F149) operates independently

Properties:
  - Throughput: per-query O(K) where K = bucket size (vs flat O(N))
  - Storage: ≤ 2× flat (cross-bucket associations stored twice)
  - Determinism: same token + same n_buckets → same bucket assignment
  - F149-compatible: bucket-local forget_step_coupling preserved

Cross-references:
  - R-RBS-NN-10 (TwoTierRBSNNStorage parent class)
  - R-RBS-NN-FINDING_R11 (Phase 1; ceiling N=256 discovery)
  - F149 (sculpted decay; per-bucket coupling metric)
"""
from __future__ import annotations

import time
import math
from typing import Optional

import numpy as np

import sys
import importlib.util
from pathlib import Path

# Load parent class (filename has hyphens)
_spec = importlib.util.spec_from_file_location(
    "two_tier_storage_base", Path(__file__).parent / "R-RBS-NN-10_two_tier_storage.py"
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["two_tier_storage_base"] = _mod
_spec.loader.exec_module(_mod)
TwoTierRBSNNStorage = _mod.TwoTierRBSNNStorage
Tier1Concept = _mod.Tier1Concept
Tier2Synapse = _mod.Tier2Synapse

from srmech.amsc import hdc
from srmech.amsc import format as amsc_format


# Bucket-size headroom safety factor below MAX_BUNDLE_N=257
# At target=128 with avg 1.5× cross-bucket storage, supports N up to ~2700
# at degree=2 with 16 buckets
DEFAULT_BUCKET_TARGET_SIZE = 128
DEFAULT_N_BUCKETS = 16


def recommend_n_buckets(
    expected_n_concepts: int,
    expected_avg_degree: int = 2,
    target_bucket_size: int = DEFAULT_BUCKET_TARGET_SIZE,
) -> int:
    """Recommend n_buckets for an expected (N, degree) workload.

    Accounts for ~1.5× cross-bucket duplication in association storage.
    Returns the smallest power-of-2 number of buckets sufficient.
    """
    avg_synapses_per_concept = expected_avg_degree
    cross_bucket_factor = 1.5
    total_synapse_slots = expected_n_concepts * avg_synapses_per_concept * cross_bucket_factor
    raw = math.ceil(total_synapse_slots / target_bucket_size)
    # Round up to next power of 2 for cleaner hash partitioning
    return max(2, 1 << (raw - 1).bit_length())


class HierarchicalTwoTierRBSNNStorage(TwoTierRBSNNStorage):
    """Hierarchical extension of two-tier storage for N > MAX_BUNDLE_N.

    Inherits all Tier 1 + Class K bridge operations from
    `TwoTierRBSNNStorage`. Overrides Tier 2 operations with bucket-aware
    versions.
    """

    def __init__(
        self,
        D: int = 8192,
        n_buckets: int = DEFAULT_N_BUCKETS,
        seed: int = 42,
        bucket_strategy: str = "hash",
    ):
        super().__init__(D=D, seed=seed)
        if n_buckets < 1:
            raise ValueError(f"n_buckets must be ≥ 1, got {n_buckets}")
        if bucket_strategy not in ("hash", "sector_then_hash"):
            raise ValueError(
                f"bucket_strategy must be 'hash' or 'sector_then_hash'; got {bucket_strategy}"
            )
        self.n_buckets = n_buckets
        self.bucket_strategy = bucket_strategy
        # Per-bucket synapse dicts (canonical sorted-tuple key → synapse object)
        self.bucket_synapses: list[dict[tuple[str, str], Tier2Synapse]] = [
            {} for _ in range(n_buckets)
        ]
        # Per-bucket polar composite memories
        self.bucket_composites: list[Optional[np.ndarray]] = [None] * n_buckets
        # Phase 2.5 optimization: maintain per-bucket token set + neighbor map
        # for O(K) retrieval
        self.bucket_tokens: list[set[str]] = [set() for _ in range(n_buckets)]
        self.bucket_neighbors: list[set[int]] = [set() for _ in range(n_buckets)]

    # ------------ bucket routing ------------

    def _bucket_for(self, token: str) -> int:
        """Deterministic bucket assignment.

        bucket_strategy='hash' (default): pure Class A SHA-256 mod n_buckets
        bucket_strategy='sector_then_hash': partition by chirality sector first
            (4 sector groups), then hash within sector. Each sector gets
            n_buckets/4 sub-buckets. Useful when associations are mostly
            same-sector (reduces cross-bucket storage).
        """
        if self.bucket_strategy == "hash":
            digest = amsc_format.sha256_bytes(token.encode("utf-8"))
            return int(digest[:8], 16) % self.n_buckets
        elif self.bucket_strategy == "sector_then_hash":
            # Look up the concept's chirality sector if encoded
            if token in self.tier1:
                sector = self.tier1[token].sector
            else:
                # Unencoded token: default to sector 0 for bucket routing
                sector = 0
            sub_buckets = max(1, self.n_buckets // 4)
            sector_group = sector % 4  # safety
            digest = amsc_format.sha256_bytes(token.encode("utf-8"))
            sub_idx = int(digest[:8], 16) % sub_buckets
            return sector_group * sub_buckets + sub_idx
        else:
            raise ValueError(f"Unknown bucket_strategy: {self.bucket_strategy}")

    def _buckets_for_pair(self, token_a: str, token_b: str) -> set[int]:
        """The bucket(s) where the (a, b) binding should live."""
        return {self._bucket_for(token_a), self._bucket_for(token_b)}

    # ------------ Tier 2 overrides ------------

    def learn_association(
        self,
        token_a: str,
        token_b: str,
        plasticity_density: float = 0.67,
    ) -> Tier2Synapse:
        """Bind two concepts and store in the appropriate bucket(s)."""
        a = self.encode_concept(token_a) if token_a not in self.tier1 else self.tier1[token_a]
        b = self.encode_concept(token_b) if token_b not in self.tier1 else self.tier1[token_b]

        polar_a = self._klein4_to_polar(a.hv)
        polar_b = self._klein4_to_polar(b.hv)
        bound = hdc.polar_bind(polar_a, polar_b)

        n_zero = int((1.0 - plasticity_density) * self.D)
        if n_zero > 0:
            zero_pos = self.rng.choice(self.D, size=n_zero, replace=False)
            bound = bound.copy()
            bound[zero_pos] = 0

        actual_density = float(hdc.polar_density(bound))
        synapse = Tier2Synapse(
            token_a=token_a,
            token_b=token_b,
            polar_hv=bound,
            initial_density=actual_density,
            current_density=actual_density,
            last_reinforced=time.time(),
            reinforce_count=1,
        )

        # Store in target buckets (deduped if same)
        key = tuple(sorted([token_a, token_b]))
        target_buckets = self._buckets_for_pair(token_a, token_b)
        for bucket_idx in target_buckets:
            self.bucket_synapses[bucket_idx][key] = synapse
            self.bucket_tokens[bucket_idx].add(token_a)
            self.bucket_tokens[bucket_idx].add(token_b)

        # Phase 2.5 — maintain bucket-neighbor map for fast retrieve
        if len(target_buckets) > 1:
            buckets_list = sorted(target_buckets)
            for i, ba in enumerate(buckets_list):
                for bb in buckets_list[i + 1 :]:
                    self.bucket_neighbors[ba].add(bb)
                    self.bucket_neighbors[bb].add(ba)

        # Also store in flat tier2 for backward-compat / introspection
        self.tier2[key] = synapse

        # Rebundle affected buckets unless in batch mode
        if not self._batch_mode:
            for bucket_idx in target_buckets:
                self._rebundle_bucket(bucket_idx)
        return synapse

    def _rebundle_bucket(self, bucket_idx: int):
        synapses = self.bucket_synapses[bucket_idx]
        if not synapses:
            self.bucket_composites[bucket_idx] = None
            return
        hvs = [s.polar_hv for s in synapses.values()]
        self.bucket_composites[bucket_idx] = hdc.polar_bundle(*hvs)

    def _rebundle_composite(self):
        # Rebundle every bucket
        for idx in range(self.n_buckets):
            self._rebundle_bucket(idx)

    def retrieve_associated(
        self,
        token: str,
        top_k: int = 5,
        threshold: float = 0.55,
        fast: bool = True,
        temperature: float = 0.0,
    ) -> list[tuple[str, float]]:
        """Find associated tokens via the token's bucket composite.

        Args:
          fast: bucket-local + neighbor scoring (default True) or flat O(N).
          temperature: 0.0 (default) → hard top-k above threshold.
                       > 0.0 → softmax-ranked (R-RBS-NN-14b).
        """
        if token not in self.tier1:
            return []
        bucket_idx = self._bucket_for(token)
        composite = self.bucket_composites[bucket_idx]
        if composite is None:
            return []

        query_polar = self._klein4_to_polar(self.tier1[token].hv)
        candidate = hdc.polar_unbind(composite, query_polar)

        if fast:
            candidate_tokens = set(self.bucket_tokens[bucket_idx])
            for neighbor in self.bucket_neighbors[bucket_idx]:
                candidate_tokens.update(self.bucket_tokens[neighbor])
            candidate_tokens.discard(token)
        else:
            candidate_tokens = set(self.tier1.keys())
            candidate_tokens.discard(token)

        scores = []
        for other_token in candidate_tokens:
            other_concept = self.tier1[other_token]
            other_polar = self._klein4_to_polar(other_concept.hv)
            sim = float(hdc.polar_similarity(candidate, other_polar))
            scores.append((other_token, sim))

        if temperature <= 0.0:
            # Hard mode (R-RBS-NN-12 original)
            scores.sort(key=lambda x: x[1], reverse=True)
            return [(t, s) for t, s in scores[:top_k] if s >= threshold]
        else:
            # Soft mode (R-RBS-NN-14b)
            tokens_list = [t for t, _ in scores]
            sims = np.array([s for _, s in scores], dtype=np.float64)
            sims_scaled = sims / temperature
            sims_scaled -= sims_scaled.max()
            exp_scores = np.exp(sims_scaled)
            probs = exp_scores / exp_scores.sum()
            sorted_idx = np.argsort(probs)[::-1]
            return [(tokens_list[i], float(probs[i])) for i in sorted_idx[:top_k]]

    # ------------ Plasticity overrides ------------

    def forget_step(self, decay_rate: float = 0.05) -> dict:
        """Random decay applied per-bucket (independent per bucket)."""
        if not any(self.bucket_synapses):
            return {"decayed_synapses": 0, "total_synapses": 0, "strategy": "random"}
        decayed = 0
        total = 0
        seen_synapses = set()
        for bucket_idx, synapses in enumerate(self.bucket_synapses):
            for key, synapse in synapses.items():
                if key in seen_synapses:
                    continue  # don't decay same synapse twice if shared across buckets
                seen_synapses.add(key)
                total += 1
                non_zero = np.where(synapse.polar_hv != 0)[0]
                if len(non_zero) == 0:
                    continue
                n_decay = int(decay_rate * len(non_zero))
                if n_decay > 0:
                    decay_pos = self.rng.choice(non_zero, size=n_decay, replace=False)
                    synapse.polar_hv[decay_pos] = 0
                    synapse.current_density = float(hdc.polar_density(synapse.polar_hv))
                    decayed += 1
            self._rebundle_bucket(bucket_idx)
        return {"decayed_synapses": decayed, "total_synapses": total, "strategy": "random"}

    def forget_step_coupling(
        self,
        decay_rate: float = 0.05,
        strategy: str = "noise_floor",
    ) -> dict:
        """Sculpted decay PER BUCKET — F149 coupling metric applied locally.

        Each bucket computes its own coupling distribution; positions
        with low/high/mid coupling within that bucket get decayed.
        This means each bucket's sub-composite gets its own
        coupling-informed sharpening.
        """
        total_decayed = 0
        total_synapses_touched = 0
        total_positions_decayed = 0

        for bucket_idx, synapses in enumerate(self.bucket_synapses):
            if not synapses:
                continue
            synapse_stack = np.stack([s.polar_hv for s in synapses.values()])
            signed_sum = synapse_stack.sum(axis=0).astype(np.int64)
            coupling_score = signed_sum * signed_sum

            n_decay = int(decay_rate * self.D)
            if n_decay <= 0:
                continue

            sorted_idx = np.argsort(coupling_score)
            if strategy == "noise_floor":
                decay_positions = sorted_idx[:n_decay]
            elif strategy == "redundant":
                decay_positions = sorted_idx[-n_decay:]
            elif strategy == "middle":
                start = (self.D - n_decay) // 2
                decay_positions = sorted_idx[start : start + n_decay]
            else:
                raise ValueError(f"Unknown strategy: {strategy!r}")

            total_positions_decayed += n_decay

            for synapse in synapses.values():
                mask = synapse.polar_hv[decay_positions] != 0
                if mask.any():
                    synapse.polar_hv[decay_positions[mask]] = 0
                    synapse.current_density = float(hdc.polar_density(synapse.polar_hv))
                    total_decayed += 1
                total_synapses_touched += 1
            self._rebundle_bucket(bucket_idx)

        return {
            "decayed_synapses": total_decayed,
            "total_synapses": total_synapses_touched,
            "n_decay_positions_per_bucket": int(decay_rate * self.D),
            "strategy": strategy,
        }

    def rehearse(
        self,
        token_a: str,
        token_b: str,
        recovery_fraction: float = 0.5,
    ) -> Optional[Tier2Synapse]:
        """Rehearse — recompute target binding; restore decayed positions."""
        key = tuple(sorted([token_a, token_b]))
        # Find synapse in any bucket that has it
        synapse = None
        target_buckets = self._buckets_for_pair(token_a, token_b)
        for bucket_idx in target_buckets:
            if key in self.bucket_synapses[bucket_idx]:
                synapse = self.bucket_synapses[bucket_idx][key]
                break
        if synapse is None:
            return None

        a = self.tier1[token_a]
        b = self.tier1[token_b]
        target = hdc.polar_bind(self._klein4_to_polar(a.hv), self._klein4_to_polar(b.hv))

        zero_positions = np.where(synapse.polar_hv == 0)[0]
        if len(zero_positions) > 0:
            n_restore = int(recovery_fraction * len(zero_positions))
            if n_restore > 0:
                restore_pos = self.rng.choice(zero_positions, size=n_restore, replace=False)
                synapse.polar_hv[restore_pos] = target[restore_pos]
        synapse.current_density = float(hdc.polar_density(synapse.polar_hv))
        synapse.last_reinforced = time.time()
        synapse.reinforce_count += 1
        # Rebundle affected buckets
        for bucket_idx in target_buckets:
            self._rebundle_bucket(bucket_idx)
        return synapse

    # ------------ Attestation ------------

    def density_attestation(self) -> dict:
        """Bucket-aware density attestation."""
        # Collect unique synapses (some may be in multiple buckets);
        # Tier2Synapse isn't hashable so dedupe by canonical sorted-tuple key
        unique_by_key: dict[tuple[str, str], Tier2Synapse] = {}
        for bucket_dict in self.bucket_synapses:
            for key, synapse in bucket_dict.items():
                unique_by_key[key] = synapse
        all_synapses = list(unique_by_key.values())
        if not all_synapses:
            return {
                "n_concepts": len(self.tier1),
                "n_synapses": 0,
                "n_buckets": self.n_buckets,
                "mean_synapse_density": None,
                "composite_densities": None,
            }
        densities = [s.current_density for s in all_synapses]
        composite_densities = [
            float(hdc.polar_density(c)) if c is not None else None
            for c in self.bucket_composites
        ]
        return {
            "n_concepts": len(self.tier1),
            "n_synapses": len(all_synapses),
            "n_buckets": self.n_buckets,
            "mean_synapse_density": float(np.mean(densities)),
            "min_synapse_density": float(np.min(densities)),
            "max_synapse_density": float(np.max(densities)),
            "composite_densities": composite_densities,
            "mean_composite_density": float(np.mean([
                d for d in composite_densities if d is not None
            ])) if any(d is not None for d in composite_densities) else None,
        }

    def bucket_distribution(self) -> dict:
        """Per-bucket synapse count distribution."""
        sizes = [len(b) for b in self.bucket_synapses]
        return {
            "bucket_sizes": sizes,
            "max_bucket": max(sizes),
            "min_bucket": min(sizes),
            "mean_bucket": float(np.mean(sizes)),
            "exceeds_MAX_BUNDLE_N": [i for i, s in enumerate(sizes) if s >= 257],
        }

    def __repr__(self):
        att = self.density_attestation()
        dist = self.bucket_distribution()
        return (
            f"HierarchicalTwoTierRBSNNStorage(D={self.D}, "
            f"n_concepts={att['n_concepts']}, n_synapses={att['n_synapses']}, "
            f"n_buckets={self.n_buckets}, max_bucket={dist['max_bucket']})"
        )
