"""R-RBS-NN-10 — Two-tier RBS-NN storage prototype

Operational implementation of ARCHITECTURAL_PATTERN_two_tier_klein4_polar:

  Tier 1 — Klein-4 chirality-tagged concept storage (F139 validated)
  Tier 2 — Polar associative memory with plasticity dynamics (F141 validated)
  Class K bridge — Tier 1 ↔ Tier 2 boundary translation (F120 / F146)

Demonstrates the full operational cycle:
  - encode_concept: store concept in Tier 1
  - learn_association: bind two concepts; store in Tier 2 with timestamp
  - retrieve_associated: given a concept, find its associated concepts via Tier 2
  - forget_step: apply Hebbian decay to unused Tier 2 synapses
  - rehearse: strengthen a binding (F146 §3: +17.9% signal recovery)
  - density_attestation: report Tier 2 substrate-health via polar_density

Substrate-encoding primitives from srmech v0.4.3 catalog.

Cross-references:
  - ARCHITECTURAL_PATTERN_two_tier_klein4_polar.md (foundation)
  - F139 (chirality axis operational at scale)
  - F141 (polar plasticity graceful)
  - F146 (Klein-4 NOT plasticity-graceful; justifies two-tier)
  - F148 (long-pending R-RBS-LM-55 framework reading: relationship-axis)
  - R-RBS-NN-4 token encoder (encode_concept routes through this)
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from srmech.amsc import hdc
from srmech.amsc import format as amsc_format


SECTOR_VISIBLE_MATTER = 0      # RH+ (default for plain content)
SECTOR_DARK_ANTIMATTER = 1     # RH-
SECTOR_VISIBLE_ANTIMATTER = 2  # LH+
SECTOR_DARK_MATTER = 3         # LH-


@dataclass
class Tier1Concept:
    """A concept stored in Tier 1 (Klein-4 chirality-tagged hypervector)."""
    token: str
    hv: np.ndarray  # uint8, shape (D,), values in {0,1,2,3}
    sector: int     # 0-3 (γ₅, iω₇) per F132 §3
    encoded_at: float


@dataclass
class Tier2Synapse:
    """An association stored in Tier 2 (polar binding with plasticity)."""
    token_a: str
    token_b: str
    polar_hv: np.ndarray  # int8, shape (D,), values in {-1, 0, +1}
    initial_density: float
    current_density: float
    last_reinforced: float
    reinforce_count: int = 0


class TwoTierRBSNNStorage:
    """Operational two-tier RBS-NN storage.

    Tier 1: Klein-4 concept layer (chirality-tagged hypervectors).
    Tier 2: Polar associative memory (plasticity-aware bindings).
    Class K bridge: translation between tiers via chirality-flip ops.

    Batch mode: when working with large numbers of associations, the
    per-call composite rebundle becomes O(N*D) per call. Use
    `storage._batch_mode = True` to defer rebundle, then call
    `storage._rebundle_composite()` once at the end. (Or use the
    `batch_learn` helper.)
    """

    def __init__(self, D: int = 8192, seed: int = 42):
        self.D = D
        self.tier1: dict[str, Tier1Concept] = {}
        self.tier2: dict[tuple[str, str], Tier2Synapse] = {}
        self.tier2_composite: Optional[np.ndarray] = None  # bundled polar HV
        self.rng = np.random.default_rng(seed)
        self._creation_time = time.time()
        self._batch_mode = False  # when True, learn_association skips rebundle

    def batch_learn(self, pairs, plasticity_density: float = 0.67):
        """Learn many associations efficiently — rebundle composite once at the end.

        Args:
          pairs: iterable of (token_a, token_b) tuples
          plasticity_density: density target for each synapse

        Returns:
          number of synapses created/updated
        """
        self._batch_mode = True
        try:
            n = 0
            for a, b in pairs:
                self.learn_association(a, b, plasticity_density=plasticity_density)
                n += 1
        finally:
            self._batch_mode = False
        self._rebundle_composite()
        return n

    # ------------ Tier 1 operations ------------

    def encode_concept(
        self,
        token: str,
        chirality_sector: int = SECTOR_VISIBLE_MATTER,
    ) -> Tier1Concept:
        """Encode a concept into Tier 1.

        Per R-RBS-NN-4 token encoder: deterministic SHA-256 seeding.
        Sector tag applied via klein4_bind with sector_mask.
        """
        if token in self.tier1:
            return self.tier1[token]
        # Deterministic seed from token (Class A content-mint)
        digest = amsc_format.sha256_bytes(token.encode("utf-8"))
        seed = int(digest[:8], 16)
        rng = np.random.default_rng(seed)
        base = hdc.klein4_random(self.D, rng)
        sector_mask = np.full(self.D, chirality_sector, dtype=np.uint8)
        tagged = hdc.klein4_bind(base, sector_mask)
        concept = Tier1Concept(
            token=token,
            hv=tagged,
            sector=chirality_sector,
            encoded_at=time.time(),
        )
        self.tier1[token] = concept
        return concept

    def retrieve_concept(self, token: str) -> Optional[Tier1Concept]:
        """Return Tier 1 concept for a token (None if not encoded)."""
        return self.tier1.get(token)

    def cpt_mirror(self, token: str) -> Optional[np.ndarray]:
        """Return the CPT-mirrored hypervector for a token (chirality-axis op)."""
        c = self.retrieve_concept(token)
        if c is None:
            return None
        return hdc.klein4_cpt_mirror(c.hv)

    # ------------ Class K bridge: Tier 1 → Tier 2 ------------

    def _klein4_to_polar(self, k4_hv: np.ndarray) -> np.ndarray:
        """Bridge: convert Klein-4 hypervector to polar via state-XOR-bit sign.

        Per ARCHITECTURAL_PATTERN_two_tier_klein4_polar §4 candidate mapping:
          klein4 0 (00) → polar +1  (visible matter / CPT-conjugate)
          klein4 1 (01) → polar -1  (visible antimatter)
          klein4 2 (10) → polar -1  (dark matter)
          klein4 3 (11) → polar +1
        Sign comes from XOR of the two state bits.
        """
        sign_bits = ((k4_hv >> 1) ^ (k4_hv & 1)) == 0
        return np.where(sign_bits, 1, -1).astype(np.int8)

    # ------------ Tier 2 operations ------------

    def learn_association(
        self,
        token_a: str,
        token_b: str,
        plasticity_density: float = 0.67,
    ) -> Tier2Synapse:
        """Bind two concepts into a Tier 2 polar association.

        Procedure:
          1. Ensure both tokens are encoded in Tier 1
          2. Bridge each via Class K to polar representation
          3. Bind via polar multiplicative product
          4. Apply density adjustment (zero out (1-density) fraction)
          5. Store synapse with timestamp
          6. Re-bundle the Tier 2 composite memory
        """
        a = self.encode_concept(token_a) if token_a not in self.tier1 else self.tier1[token_a]
        b = self.encode_concept(token_b) if token_b not in self.tier1 else self.tier1[token_b]

        polar_a = self._klein4_to_polar(a.hv)
        polar_b = self._klein4_to_polar(b.hv)
        bound = hdc.polar_bind(polar_a, polar_b)

        # Density adjustment: zero out (1-density) positions
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
        # Use canonical key (sorted) so (A,B) and (B,A) collide
        key = tuple(sorted([token_a, token_b]))
        self.tier2[key] = synapse
        if not self._batch_mode:
            self._rebundle_composite()
        return synapse

    def _rebundle_composite(self):
        """Rebuild the Tier 2 composite from all current synapses."""
        if not self.tier2:
            self.tier2_composite = None
            return
        hvs = [s.polar_hv for s in self.tier2.values()]
        self.tier2_composite = hdc.polar_bundle(*hvs)

    def retrieve_associated(
        self,
        token: str,
        top_k: int = 5,
        threshold: float = 0.55,
    ) -> list[tuple[str, float]]:
        """Given a token, find tokens associated to it via Tier 2.

        Procedure:
          1. Bridge query token to polar
          2. Unbind from Tier 2 composite to recover candidate hv
          3. For each known token in Tier 1, score similarity to candidate
          4. Return top-k tokens above threshold
        """
        if self.tier2_composite is None or token not in self.tier1:
            return []
        query_polar = self._klein4_to_polar(self.tier1[token].hv)
        candidate = hdc.polar_unbind(self.tier2_composite, query_polar)
        # Score against each Tier 1 token (excluding query itself)
        scores = []
        for other_token, other_concept in self.tier1.items():
            if other_token == token:
                continue
            other_polar = self._klein4_to_polar(other_concept.hv)
            sim = float(hdc.polar_similarity(candidate, other_polar))
            scores.append((other_token, sim))
        # Sort by score, return top-k above threshold
        scores.sort(key=lambda x: x[1], reverse=True)
        return [(t, s) for t, s in scores[:top_k] if s >= threshold]

    # ------------ Plasticity dynamics ------------

    def forget_step(self, decay_rate: float = 0.05) -> dict:
        """Apply RANDOM Hebbian decay to Tier 2 synapses (baseline).

        Per F141: zero-injection decay is graceful (vs sign-flip noise).
        Per F146 §3: decay-recovery via rehearsal works.

        Decay zeros out additional positions in each synapse's polar_hv.
        Updates current_density. Re-bundles composite.

        NOTE: This is RANDOM decay (uniform position selection). For
        coupling-aware sculpted decay, use forget_step_coupling().
        Per user framework direction 2026-05-28: random decay may be
        the wrong substrate model — real substrate decay is likely
        cascade-informed.
        """
        if not self.tier2:
            return {"decayed_synapses": 0, "total_synapses": 0, "strategy": "random"}
        decayed = 0
        for synapse in self.tier2.values():
            non_zero_positions = np.where(synapse.polar_hv != 0)[0]
            if len(non_zero_positions) == 0:
                continue
            n_decay = int(decay_rate * len(non_zero_positions))
            if n_decay > 0:
                decay_pos = self.rng.choice(non_zero_positions, size=n_decay, replace=False)
                synapse.polar_hv[decay_pos] = 0
                synapse.current_density = float(hdc.polar_density(synapse.polar_hv))
                decayed += 1
        self._rebundle_composite()
        return {
            "decayed_synapses": decayed,
            "total_synapses": len(self.tier2),
            "strategy": "random",
        }

    def forget_step_coupling(
        self,
        decay_rate: float = 0.05,
        strategy: str = "noise_floor",
    ) -> dict:
        """Sculpted decay via Class K∘L coupling metric.

        Per user framework direction 2026-05-28: real substrate decay is
        not random — it's cascade-informed. This method uses the
        signed-sum-squared coupling metric (per F144 §1.2,
        srmech.amsc.coupling.signed_sum_squared upstream in v0.4.3) to
        choose positions to drop based on their coupling contribution
        across the synapse bundle.

        For polar HDC: per-position coupling score is
            score[i] = (sum_synapses(synapse.polar_hv[i]))^2
        Range [0, n_synapses^2]. Zero contributors don't vote; ±1
        contributors do. High score = many synapses agree at that
        position. Low score = balanced or no-commitment positions.

        Strategies:
          'noise_floor' — drop positions with LOWEST coupling
            (these are noise / no-consensus; drop to preserve signal)
          'redundant' — drop positions with HIGHEST coupling
            (drop consensus; preserves specificity at cost of common signal)
          'middle' — drop middle-coupling band
            (preserves both noise and consensus; tests middle-position hypothesis)

        Args:
          decay_rate: fraction of D positions to decay (global, not per-synapse)
          strategy: see above

        Returns:
          dict with {strategy, decayed_synapses, total_synapses, n_decay_positions}
        """
        if not self.tier2:
            return {
                "decayed_synapses": 0,
                "total_synapses": 0,
                "strategy": strategy,
                "n_decay_positions": 0,
            }

        # Stack all synapse polar HVs into a matrix [N_synapses, D]
        synapse_stack = np.stack([s.polar_hv for s in self.tier2.values()])
        # Per-position signed-sum (range [-N, N]) and its square (range [0, N^2])
        signed_sum = synapse_stack.sum(axis=0).astype(np.int64)
        coupling_score = signed_sum * signed_sum  # per-position; shape (D,)

        n_decay = int(decay_rate * self.D)
        if n_decay <= 0:
            return {
                "decayed_synapses": 0,
                "total_synapses": len(self.tier2),
                "strategy": strategy,
                "n_decay_positions": 0,
            }

        # Choose positions per strategy
        sorted_idx = np.argsort(coupling_score)
        if strategy == "noise_floor":
            decay_positions = sorted_idx[:n_decay]
        elif strategy == "redundant":
            decay_positions = sorted_idx[-n_decay:]
        elif strategy == "middle":
            start = (self.D - n_decay) // 2
            decay_positions = sorted_idx[start : start + n_decay]
        else:
            raise ValueError(
                f"Unknown strategy: {strategy!r}. "
                f"Expected 'noise_floor', 'redundant', or 'middle'."
            )

        # Zero those positions in every synapse where they're currently non-zero
        decayed = 0
        for synapse in self.tier2.values():
            mask = synapse.polar_hv[decay_positions] != 0
            if mask.any():
                synapse.polar_hv[decay_positions[mask]] = 0
                synapse.current_density = float(hdc.polar_density(synapse.polar_hv))
                decayed += 1

        self._rebundle_composite()
        return {
            "decayed_synapses": decayed,
            "total_synapses": len(self.tier2),
            "strategy": strategy,
            "n_decay_positions": int(n_decay),
        }

    def rehearse(
        self,
        token_a: str,
        token_b: str,
        recovery_fraction: float = 0.5,
    ) -> Optional[Tier2Synapse]:
        """Strengthen an existing binding via Hebbian rehearsal.

        Per F146 §3: 50% rehearsal of decayed positions yields ~+17.9% signal recovery.

        Procedure:
          1. Find synapse for (token_a, token_b)
          2. Recompute the original target polar binding
          3. At decayed (0) positions, restore from target with `recovery_fraction` probability
          4. Update last_reinforced + reinforce_count + density
          5. Rebundle composite
        """
        key = tuple(sorted([token_a, token_b]))
        if key not in self.tier2:
            return None
        synapse = self.tier2[key]
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
        self._rebundle_composite()
        return synapse

    # ------------ Attestation / introspection ------------

    def density_attestation(self) -> dict:
        """Report Tier 2 substrate-health metrics."""
        if not self.tier2:
            return {
                "n_concepts": len(self.tier1),
                "n_synapses": 0,
                "mean_synapse_density": None,
                "composite_density": None,
            }
        densities = [s.current_density for s in self.tier2.values()]
        return {
            "n_concepts": len(self.tier1),
            "n_synapses": len(self.tier2),
            "mean_synapse_density": float(np.mean(densities)),
            "min_synapse_density": float(np.min(densities)),
            "max_synapse_density": float(np.max(densities)),
            "composite_density": float(hdc.polar_density(self.tier2_composite))
                if self.tier2_composite is not None else None,
        }

    def sector_distribution(self) -> dict:
        """Per-sector concept distribution in Tier 1."""
        counts = {0: 0, 1: 0, 2: 0, 3: 0}
        for c in self.tier1.values():
            counts[c.sector] += 1
        return counts

    def __repr__(self):
        a = self.density_attestation()
        return (
            f"TwoTierRBSNNStorage(D={self.D}, "
            f"n_concepts={a['n_concepts']}, n_synapses={a['n_synapses']}, "
            f"composite_density={a['composite_density']})"
        )
