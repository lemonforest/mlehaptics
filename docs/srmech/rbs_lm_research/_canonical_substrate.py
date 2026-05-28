"""_canonical_substrate — Catalog-driven Klein-4 chirality-level sentence substrate.

Canonical implementation paired with the AMSC catalog at
docs/srmech/catalogs/rbs_lm_substrate/descriptor.toml. Every parameter that
was a module-level constant in the R-RBS-LM-112 first-pass library is now
read from a SubstrateConfig (see _substrate_config.py).

Relationship to R-RBS-LM-112 first-pass library:
  - R-RBS-LM-112 is preserved as historical record (paired with F157 v1)
  - This module is the canonical successor (paired with F162) — same algebra,
    catalog-parameterized, no module-level magic numbers
  - F157 v1's empirical evidence chain stays intact in git history; F162's
    full-coverage results are produced by this module + R-RBS-LM-122

Per [[feedback_no_mvp_framing]] + [[feedback_full_coverage_shipping_mpm_way]]:
all generation-machinery caps that limited output to L≤10 (max_walk_length=10,
max_paths<5, l4-direct-composition special-case, no-cycles policy) are now
catalog fields, no longer hardcoded. Same for hierarchical bucket strategy,
grammar templates, plausibility weights, and measurement protocol.

Per [[user_stance_kepler_shape_universal]]: algebra IS the primitives. The
substrate's algebraic behavior is identical to R-RBS-LM-112; only the
configurability is restored.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from srmech.amsc import hdc, format as amsc_format

# Import config types via relative-aware loader. Callers can also pass any
# object exposing the required attributes; we don't bind to the dataclass type.
try:
    from ._substrate_config import SubstrateConfig
except ImportError:  # pragma: no cover — script-mode fallback for direct exec
    SubstrateConfig = Any  # type: ignore[misc,assignment]


# ---------------------------------------------------------------------------
# Encoding primitives — all D and hex-chars are config-driven
# ---------------------------------------------------------------------------

def token_seed(name: str, hex_chars: int) -> int:
    """SHA-256 prefix → integer seed. Catalog controls hex prefix width."""
    digest = amsc_format.sha256_bytes(name.encode("utf-8"))
    return int(digest[:hex_chars], 16)


def encode_word_k4(word: str, *, D: int, sector: int, hex_chars: int) -> np.ndarray:
    rng = np.random.default_rng(token_seed(word, hex_chars))
    base = hdc.klein4_random(D, rng)
    return hdc.klein4_bind(base, np.full(D, sector, dtype=np.uint8))


def encode_bigram_l1(
    word_a: str, word_b: str, *, D: int, hex_chars: int
) -> np.ndarray:
    w_a = encode_word_k4(word_a, D=D, sector=0, hex_chars=hex_chars)
    w_b = encode_word_k4(word_b, D=D, sector=0, hex_chars=hex_chars)
    bound = hdc.klein4_bind(w_a, w_b)
    return hdc.klein4_bind(bound, np.full(D, 1, dtype=np.uint8))


def encode_skeleton_l2(
    first_bigram: tuple[str, str],
    last_bigram: tuple[str, str],
    *,
    D: int,
    hex_chars: int,
) -> np.ndarray:
    first_l1 = encode_bigram_l1(*first_bigram, D=D, hex_chars=hex_chars)
    last_l1 = encode_bigram_l1(*last_bigram, D=D, hex_chars=hex_chars)
    bound = hdc.klein4_bind(first_l1, last_l1)
    return hdc.klein4_bind(bound, np.full(D, 2, dtype=np.uint8))


def encode_sentence_l3(tokens, *, D: int, hex_chars: int) -> np.ndarray:
    accum = encode_word_k4(tokens[0], D=D, sector=0, hex_chars=hex_chars)
    for w in tokens[1:]:
        accum = hdc.klein4_bind(
            accum, encode_word_k4(w, D=D, sector=0, hex_chars=hex_chars)
        )
    return hdc.klein4_bind(accum, np.full(D, 3, dtype=np.uint8))


def sim_k4_batch(query: np.ndarray, candidates: np.ndarray) -> np.ndarray:
    """Fractional-agreement similarity. F132 §3 standard."""
    return (candidates == query).mean(axis=1)


# ---------------------------------------------------------------------------
# Canonical substrate class
# ---------------------------------------------------------------------------

@dataclass
class CanonicalVariableLengthMemory:
    """Catalog-parameterized variable-length sentence substrate.

    Algebraic behavior identical to R-RBS-LM-112's VariableLengthSentenceMemory;
    every magic number is now a catalog parameter.

    Construction:
        memory = CanonicalVariableLengthMemory(config)
    where config is a SubstrateConfig from _substrate_config.load_substrate_config().
    """

    config: Any  # SubstrateConfig — typed as Any so this module can be exec'd standalone
    words_l0: dict[str, np.ndarray] = field(default_factory=dict)
    bigrams_l1: dict[tuple[str, str], np.ndarray] = field(default_factory=dict)
    skeletons_l2: dict[tuple[tuple[str, str], tuple[str, str]], np.ndarray] = field(default_factory=dict)
    sentences_l3: dict[tuple, np.ndarray] = field(default_factory=dict)
    next_after: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    prev_before: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    skeleton_lengths: dict[tuple, set[int]] = field(default_factory=lambda: defaultdict(set))

    @property
    def D(self) -> int:
        return int(self.config.substrate.D)

    @property
    def hex_chars(self) -> int:
        return int(self.config.substrate.token_seed_hex_chars)

    @property
    def min_skeleton_length(self) -> int:
        return int(self.config.substrate.min_skeleton_length)

    def learn_sentence(self, tokens):
        """Add a sentence to the substrate. No length cap.

        Catalog gates: min_skeleton_length controls L2 storage.
        """
        if len(tokens) < 2:
            return  # algebraic floor — need at least one bigram

        for w in tokens:
            if w not in self.words_l0:
                self.words_l0[w] = encode_word_k4(
                    w, D=self.D, sector=0, hex_chars=self.hex_chars
                )

        for i in range(len(tokens) - 1):
            bigram = (tokens[i], tokens[i + 1])
            if bigram not in self.bigrams_l1:
                self.bigrams_l1[bigram] = encode_bigram_l1(
                    *bigram, D=self.D, hex_chars=self.hex_chars
                )
            self.next_after[tokens[i]].add(tokens[i + 1])
            self.prev_before[tokens[i + 1]].add(tokens[i])

        # L2 skeleton — gated by catalog (default 4; can lower to 2 for short-sentence corpora)
        if len(tokens) >= self.min_skeleton_length:
            first_bigram = (tokens[0], tokens[1])
            last_bigram = (tokens[-2], tokens[-1])
            skeleton = (first_bigram, last_bigram)
            if skeleton not in self.skeletons_l2:
                self.skeletons_l2[skeleton] = encode_skeleton_l2(
                    first_bigram, last_bigram, D=self.D, hex_chars=self.hex_chars
                )
            self.skeleton_lengths[skeleton].add(len(tokens))

        sentence_key = tuple(tokens)
        if sentence_key not in self.sentences_l3:
            self.sentences_l3[sentence_key] = encode_sentence_l3(
                tokens, D=self.D, hex_chars=self.hex_chars
            )

    # ------------------------------------------------------------------
    # Retrieval primitives
    # ------------------------------------------------------------------

    def self_recall(self, tokens) -> bool:
        """Encode + cosine-max → is it the same sentence?"""
        if not self.sentences_l3:
            return False
        target = encode_sentence_l3(tokens, D=self.D, hex_chars=self.hex_chars)
        matrix = np.stack(list(self.sentences_l3.values()))
        keys = list(self.sentences_l3.keys())
        sims = sim_k4_batch(target, matrix)
        return keys[int(sims.argmax())] == tuple(tokens)

    def retrieve_skeletons_for_first_bigram(self, first_bigram):
        if first_bigram not in self.bigrams_l1:
            return []
        q_l1 = self.bigrams_l1[first_bigram]
        l1_matrix = np.stack(list(self.bigrams_l1.values()))
        l1_list = list(self.bigrams_l1.keys())
        candidates = []
        for skeleton, sk_hv in self.skeletons_l2.items():
            unsec = hdc.klein4_bind(sk_hv, np.full(self.D, 2, dtype=np.uint8))
            other_bigram_cand = hdc.klein4_bind(unsec, q_l1)
            sims = sim_k4_batch(other_bigram_cand, l1_matrix)
            best_idx = int(sims.argmax())
            best_other = l1_list[best_idx]
            candidates.append((skeleton, best_other, float(sims.max())))
        valid = [c for c in candidates if first_bigram in c[0]]
        valid.sort(key=lambda x: x[2], reverse=True)
        return valid

    # ------------------------------------------------------------------
    # Walk + generation — every cap is catalog-driven, NO false idols
    # ------------------------------------------------------------------

    def walk_bigram_chain(
        self,
        start_word: str,
        end_word: str,
        max_length: int | None = None,
        max_paths: int | None = None,
    ) -> list[list[str]]:
        """BFS for paths from start_word ending in end_word.

        max_length defaults to catalog generation.max_walk_length (NOT hardcoded 10).
        max_paths defaults to catalog generation.max_paths (NOT hardcoded 5).
        cycle_policy from catalog: 'forbid' | 'allow' | 'count_limited'.
        """
        if start_word not in self.next_after:
            return []

        cfg = self.config.generation
        m_len = cfg.max_walk_length if max_length is None else max_length
        m_paths = cfg.max_paths if max_paths is None else max_paths
        cycle_policy = cfg.cycle_policy

        queue: deque[list[str]] = deque([[start_word]])
        paths: list[list[str]] = []
        while queue and len(paths) < m_paths:
            path = queue.popleft()
            if len(path) > m_len:
                continue
            last_token = path[-1]
            if last_token == end_word and len(path) > 1:
                paths.append(path)
                continue
            for next_token in self.next_after.get(last_token, set()):
                if cycle_policy == "forbid" and next_token in path:
                    continue
                if cycle_policy == "count_limited" and path.count(next_token) >= 2:
                    continue
                # cycle_policy == "allow" — no filter
                queue.append(path + [next_token])
        return paths

    def generate_variable_length(
        self,
        seed_bigram: tuple[str, str],
        top_k: int | None = None,
    ) -> list[dict]:
        """Generate sentences from seed bigram. All caps are catalog-driven.

        No L=4 special-case unless catalog.generation.l4_direct_composition is True.
        Skeleton-length fallback from catalog (default empty = no fallback).
        """
        cfg = self.config.generation
        t_k = cfg.default_top_k if top_k is None else top_k
        l4_special = cfg.l4_direct_composition
        fallback = set(cfg.skeleton_length_fallback)

        generated: list[dict] = []
        skeletons = self.retrieve_skeletons_for_first_bigram(seed_bigram)

        for skeleton, _last_bigram_unused, sk_sim in skeletons:
            if skeleton[0] == seed_bigram:
                end_bg = skeleton[1]
            else:
                end_bg = skeleton[0]

            lengths_for_skel = self.skeleton_lengths.get(skeleton, fallback)

            for target_length in lengths_for_skel:
                if l4_special and target_length == 4:
                    sentence = list(seed_bigram) + list(end_bg)
                    generated.append({
                        "sentence": sentence,
                        "length": 4,
                        "skeleton": skeleton,
                        "skeleton_sim": sk_sim,
                    })
                    continue

                # Uniform walk-based composition for all lengths
                paths = self.walk_bigram_chain(seed_bigram[1], end_bg[0])
                for path in paths:
                    # full sentence: seed[0] + path + end_bg[1]
                    full = [seed_bigram[0]] + path + [end_bg[1]]
                    if len(full) == target_length:
                        generated.append({
                            "sentence": full,
                            "length": target_length,
                            "skeleton": skeleton,
                            "skeleton_sim": sk_sim,
                            "middle_path": path[1:-1] if len(path) > 2 else [],
                        })

        # Dedupe by sentence tuple
        seen = set()
        unique = []
        for g in generated:
            key = tuple(g["sentence"])
            if key not in seen:
                seen.add(key)
                unique.append(g)
        return unique[:t_k]


# ---------------------------------------------------------------------------
# Hierarchical wrapper — catalog-driven bucket strategy
# ---------------------------------------------------------------------------

@dataclass
class CanonicalHierarchicalMemory:
    """Hierarchical wrapper around CanonicalVariableLengthMemory.

    bucket strategy comes from catalog.hierarchical.default_strategy (or override
    via constructor `strategy` argument). Cross-bucket merge for generation.
    """

    config: Any
    n_buckets: int | None = None
    strategy: str | None = None
    buckets: list[CanonicalVariableLengthMemory] = field(default_factory=list)

    def __post_init__(self):
        h = self.config.hierarchical
        if self.n_buckets is None:
            self.n_buckets = h.n_buckets
        if self.strategy is None:
            self.strategy = h.default_strategy
        if self.strategy not in h.allowed_strategies:
            raise ValueError(
                f"strategy {self.strategy!r} not in catalog allowed_strategies "
                f"{h.allowed_strategies}"
            )
        self.buckets = [
            CanonicalVariableLengthMemory(config=self.config)
            for _ in range(self.n_buckets)
        ]

    def _bucket_for_sentence(self, tokens) -> int:
        hex_chars = int(self.config.hierarchical.sentence_hash_hex_chars)
        n = int(self.n_buckets)
        if self.strategy == "hash":
            digest = amsc_format.sha256_bytes(" ".join(tokens).encode("utf-8"))
            return int(digest[:hex_chars], 16) % n
        elif self.strategy == "first_bigram_hash":
            if len(tokens) < 2:
                key = tokens[0].encode("utf-8") if tokens else b""
            else:
                key = f"{tokens[0]}_{tokens[1]}".encode("utf-8")
            digest = amsc_format.sha256_bytes(key)
            return int(digest[:hex_chars], 16) % n
        elif self.strategy == "sector_then_hash":
            # Partition by first-token sector first, then hash within sector
            first = tokens[0] if tokens else ""
            seed = token_seed(first, int(self.config.substrate.token_seed_hex_chars))
            sector = seed % int(self.config.substrate.sector_count)
            sub_buckets = max(1, n // int(self.config.substrate.sector_count))
            digest = amsc_format.sha256_bytes(" ".join(tokens).encode("utf-8"))
            sub = int(digest[:hex_chars], 16) % sub_buckets
            return (sector * sub_buckets + sub) % n
        else:
            raise ValueError(f"Unknown bucket_strategy: {self.strategy}")

    def learn_sentence(self, tokens):
        b = self._bucket_for_sentence(tokens)
        self.buckets[b].learn_sentence(tokens)
        return b

    def recall_sentence(self, tokens) -> bool:
        return self.buckets[self._bucket_for_sentence(tokens)].self_recall(tokens)

    def generate_from_seed(self, seed_bigram, top_k: int | None = None) -> list[dict]:
        cfg = self.config.generation
        t_k = cfg.default_top_k if top_k is None else top_k
        all_results: list[dict] = []
        for bucket in self.buckets:
            if seed_bigram in bucket.bigrams_l1:
                results = bucket.generate_variable_length(seed_bigram, top_k=t_k)
                all_results.extend(results)
        seen = set()
        unique = []
        for entry in sorted(all_results, key=lambda e: -e["skeleton_sim"]):
            key = tuple(entry["sentence"])
            if key not in seen:
                seen.add(key)
                unique.append(entry)
        return unique[:t_k]

    def total_sentences(self) -> int:
        return sum(len(b.sentences_l3) for b in self.buckets)

    def total_words(self) -> int:
        all_words = set()
        for b in self.buckets:
            all_words.update(b.words_l0.keys())
        return len(all_words)

    def bucket_load_stats(self) -> dict:
        loads = np.array([len(b.sentences_l3) for b in self.buckets])
        return {
            "n_buckets": int(self.n_buckets),
            "strategy": self.strategy,
            "min": int(loads.min()),
            "max": int(loads.max()),
            "mean": float(loads.mean()),
            "std": float(loads.std()),
            "cv": float(loads.std() / loads.mean()) if loads.mean() > 0 else 0.0,
            "empty_buckets": int((loads == 0).sum()),
        }
