"""_canonical_substrate — Klein-4 chirality-level sentence substrate, catalog-driven.

Consumes substrate parameters from a srmech.amsc.Descriptor (loaded via
srmech.amsc.load_descriptor) — no parallel Python parameter parser, no
custom config dataclass. The catalog IS the config; srmech IS the loader.

Usage:
    from srmech.amsc import load_descriptor
    from _canonical_substrate import build_substrate, build_hierarchical_substrate

    desc = load_descriptor(catalog_path)
    params = desc.fetch["literature_curated"]   # all substrate sections live here
    memory = build_substrate(params)             # or build_hierarchical_substrate(params)

Per [[feedback_no_mvp_framing]] + user direction "catalogs are not new python
script mvp magics; cascade is handled by srmech with the toml and MPR things":
this module is the substrate LIBRARY (algebra implementation), not a parallel
config parser. Parameters are passed as nested dicts from the Descriptor.

Per [[feedback_upstream_srmech_fixes_as_research_notes]]: the library lives in
research subtree pending upstream absorption (UPSTREAM_NOTES wishlist item:
srmech.rbs_lm.substrate module + a 'substrate_parameterization' adapter so the
characterization run becomes a srmech cascade dispatch).
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Mapping

import numpy as np

from srmech.amsc import hdc, format as amsc_format


# ---------------------------------------------------------------------------
# Encoding primitives — D and hex_chars are arguments, not module-level
# ---------------------------------------------------------------------------

def token_seed(name: str, hex_chars: int) -> int:
    """SHA-256 prefix → integer seed. Hex prefix width is catalog-controlled."""
    digest = amsc_format.sha256_bytes(name.encode("utf-8"))
    return int(digest[:hex_chars], 16)


def encode_word_k4(word: str, *, D: int, sector: int, hex_chars: int) -> np.ndarray:
    rng = np.random.default_rng(token_seed(word, hex_chars))
    base = hdc.klein4_random(D, rng)
    return hdc.klein4_bind(base, np.full(D, sector, dtype=np.uint8))


def encode_bigram_l1(word_a: str, word_b: str, *, D: int, hex_chars: int) -> np.ndarray:
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
    """Fractional-agreement similarity (F132 §3 standard)."""
    return (candidates == query).mean(axis=1)


# ---------------------------------------------------------------------------
# Rolling context-state encoder — the F166 inference-substrate "hidden state"
# ---------------------------------------------------------------------------

class ContextSubstrate:
    """Rolling context-state encoder (F166 walk; the inference "hidden state").

    The last-k tokens → ONE Klein-4 substrate state via positional role-filler
    binding: bundle_p[ klein4_bind(pos_key(p), enc(token_p)) ]. This is the
    state an autoregressive RBS-LM conditions its next-token distribution on
    (Steps 1-4 all share it). Catalog-driven (D, hex_chars from the descriptor's
    substrate section); deterministic / bit-exact.

    Class composition: Class A (content-hash mint via enc) ∘ Class M (klein4
    bind) ∘ Class I/iω₇ position keys, bundled. NOT a bolted-on neural state —
    a named A-N cascade under the 28D chirality coordinate.

    The even-count bundle pad (never DROP a real token) is the fix for the
    R-RBS-LM-126 first-run odd/even sawtooth artifact: klein4_bundle needs an
    ODD count (majority tie-break), so an even window APPENDS a fixed neutral
    pad vector rather than discarding a real token.
    """

    def __init__(self, *, D: int, hex_chars: int, sector: int = 0):
        self.D = int(D)
        self.hex_chars = int(hex_chars)
        self.sector = int(sector)
        self._poskey: dict[int, np.ndarray] = {}
        self._pad = self.enc("__bundle_pad__")  # fixed neutral tie-breaker

    def enc(self, tok: str, sector: int | None = None) -> np.ndarray:
        return encode_word_k4(
            tok, D=self.D,
            sector=self.sector if sector is None else sector,
            hex_chars=self.hex_chars,
        )

    def pos_key(self, p: int) -> np.ndarray:
        if p not in self._poskey:
            self._poskey[p] = self.enc(f"__ctx_pos_{p}__")
        return self._poskey[p]

    def bundle_odd(self, vecs) -> np.ndarray:
        """klein4_bundle requires an ODD count; APPEND a fixed neutral pad when
        the count is even — never DROP a real token (the 126 sawtooth fix)."""
        if len(vecs) == 1:
            return vecs[0]
        if len(vecs) % 2 == 0:
            vecs = list(vecs) + [self._pad]
        return hdc.klein4_bundle(*vecs)

    def encode_context(self, window) -> np.ndarray:
        """last-k tokens → ONE Klein-4 state (positional role-filler bind + bundle)."""
        bound = [hdc.klein4_bind(self.pos_key(p), self.enc(tok))
                 for p, tok in enumerate(window)]
        return self.bundle_odd(bound)


# ---------------------------------------------------------------------------
# Canonical substrate class — params is the desc.fetch[adapter] nested dict
# ---------------------------------------------------------------------------

@dataclass
class CanonicalVariableLengthMemory:
    """Variable-length sentence substrate parameterized by a catalog nested dict.

    `params` is desc.fetch["literature_curated"] (or equivalent) from a
    srmech.amsc.Descriptor. Algebraically identical to R-RBS-LM-112's
    VariableLengthSentenceMemory; the difference is that every former magic
    number now flows in from the catalog.
    """

    params: Mapping[str, Any]
    words_l0: dict[str, np.ndarray] = field(default_factory=dict)
    bigrams_l1: dict[tuple[str, str], np.ndarray] = field(default_factory=dict)
    skeletons_l2: dict[tuple[tuple[str, str], tuple[str, str]], np.ndarray] = field(default_factory=dict)
    sentences_l3: dict[tuple, np.ndarray] = field(default_factory=dict)
    next_after: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    prev_before: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    skeleton_lengths: dict[tuple, set[int]] = field(default_factory=lambda: defaultdict(set))

    # --- catalog accessors (no parallel dataclass) ---

    @property
    def D(self) -> int:
        return int(self.params["substrate"]["D"])

    @property
    def hex_chars(self) -> int:
        return int(self.params["substrate"]["token_seed_hex_chars"])

    @property
    def min_skeleton_length(self) -> int:
        return int(self.params["substrate"]["min_skeleton_length"])

    @property
    def gen_params(self) -> Mapping[str, Any]:
        return self.params["generation"]

    def learn_sentence(self, tokens) -> None:
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

    def self_recall(self, tokens) -> bool:
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

    def walk_bigram_chain(
        self,
        start_word: str,
        end_word: str,
        max_length: int | None = None,
        max_paths: int | None = None,
    ) -> list[list[str]]:
        """BFS for paths start_word → end_word. Catalog-driven caps + cycle policy."""
        if start_word not in self.next_after:
            return []
        gp = self.gen_params
        m_len = int(gp["max_walk_length"]) if max_length is None else max_length
        m_paths = int(gp["max_paths"]) if max_paths is None else max_paths
        cycle_policy = str(gp["cycle_policy"])

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
                queue.append(path + [next_token])
        return paths

    def generate_variable_length(
        self,
        seed_bigram: tuple[str, str],
        top_k: int | None = None,
    ) -> list[dict]:
        gp = self.gen_params
        t_k = int(gp["default_top_k"]) if top_k is None else top_k
        l4_special = bool(gp.get("l4_direct_composition", False))
        fallback = set(int(x) for x in gp.get("skeleton_length_fallback", []))

        generated: list[dict] = []
        skeletons = self.retrieve_skeletons_for_first_bigram(seed_bigram)

        for skeleton, _last_unused, sk_sim in skeletons:
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
                paths = self.walk_bigram_chain(seed_bigram[1], end_bg[0])
                for path in paths:
                    full = [seed_bigram[0]] + path + [end_bg[1]]
                    if len(full) == target_length:
                        generated.append({
                            "sentence": full,
                            "length": target_length,
                            "skeleton": skeleton,
                            "skeleton_sim": sk_sim,
                            "middle_path": path[1:-1] if len(path) > 2 else [],
                        })

        seen = set()
        unique = []
        for g in generated:
            key = tuple(g["sentence"])
            if key not in seen:
                seen.add(key)
                unique.append(g)
        return unique[:t_k]


# ---------------------------------------------------------------------------
# Hierarchical wrapper — bucket strategy from catalog
# ---------------------------------------------------------------------------

@dataclass
class CanonicalHierarchicalMemory:
    """Hash-bucketed wrapper around CanonicalVariableLengthMemory."""

    params: Mapping[str, Any]
    n_buckets: int | None = None
    strategy: str | None = None
    buckets: list[CanonicalVariableLengthMemory] = field(default_factory=list)

    def __post_init__(self):
        h = self.params["hierarchical"]
        if self.n_buckets is None:
            self.n_buckets = int(h["n_buckets"])
        if self.strategy is None:
            self.strategy = str(h["default_strategy"])
        allowed = tuple(h["allowed_strategies"])
        if self.strategy not in allowed:
            raise ValueError(
                f"strategy {self.strategy!r} not in catalog allowed_strategies {allowed}"
            )
        self.buckets = [
            CanonicalVariableLengthMemory(params=self.params)
            for _ in range(self.n_buckets)
        ]

    def _bucket_for_sentence(self, tokens) -> int:
        h = self.params["hierarchical"]
        hex_chars = int(h["sentence_hash_hex_chars"])
        n = int(self.n_buckets)
        if self.strategy == "hash":
            digest = amsc_format.sha256_bytes(" ".join(tokens).encode("utf-8"))
            return int(digest[:hex_chars], 16) % n
        elif self.strategy == "first_bigram_hash":
            key = (
                tokens[0].encode("utf-8") if len(tokens) < 2 else
                f"{tokens[0]}_{tokens[1]}".encode("utf-8")
            )
            digest = amsc_format.sha256_bytes(key)
            return int(digest[:hex_chars], 16) % n
        elif self.strategy == "sector_then_hash":
            first = tokens[0] if tokens else ""
            seed = token_seed(first, int(self.params["substrate"]["token_seed_hex_chars"]))
            sector = seed % int(self.params["substrate"]["sector_count"])
            sub = max(1, n // int(self.params["substrate"]["sector_count"]))
            digest = amsc_format.sha256_bytes(" ".join(tokens).encode("utf-8"))
            sub_idx = int(digest[:hex_chars], 16) % sub
            return (sector * sub + sub_idx) % n
        else:
            raise ValueError(f"Unknown bucket_strategy: {self.strategy}")

    def learn_sentence(self, tokens):
        b = self._bucket_for_sentence(tokens)
        self.buckets[b].learn_sentence(tokens)
        return b

    def recall_sentence(self, tokens) -> bool:
        return self.buckets[self._bucket_for_sentence(tokens)].self_recall(tokens)

    def generate_from_seed(self, seed_bigram, top_k: int | None = None):
        gp = self.params["generation"]
        t_k = int(gp["default_top_k"]) if top_k is None else top_k
        all_results = []
        for bucket in self.buckets:
            if seed_bigram in bucket.bigrams_l1:
                all_results.extend(bucket.generate_variable_length(seed_bigram, top_k=t_k))
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
        all_w = set()
        for b in self.buckets:
            all_w.update(b.words_l0.keys())
        return len(all_w)

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


# ---------------------------------------------------------------------------
# Convenience builders — for code that has a Descriptor in hand
# ---------------------------------------------------------------------------

def build_substrate(params: Mapping[str, Any]) -> CanonicalVariableLengthMemory:
    """Build a flat substrate from desc.fetch[adapter] dict."""
    return CanonicalVariableLengthMemory(params=params)


def build_hierarchical_substrate(
    params: Mapping[str, Any],
    n_buckets: int | None = None,
    strategy: str | None = None,
) -> CanonicalHierarchicalMemory:
    """Build a hierarchical substrate from desc.fetch[adapter] dict."""
    return CanonicalHierarchicalMemory(params=params, n_buckets=n_buckets, strategy=strategy)
