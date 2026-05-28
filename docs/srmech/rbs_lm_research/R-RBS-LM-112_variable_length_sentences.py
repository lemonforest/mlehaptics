"""R-RBS-LM-112 — Variable-length sentence support (Item 1 of 5)

Extends F156's 4-word-hardcoded design to arbitrary length sentences.

DESIGN per substrate-native chirality-level approach (F155/F156):

  L0 sector 0:  individual words
  L1 sector 1:  all consecutive bigrams (T_i, T_{i+1}) for i in 0..N-2
  L2 sector 2:  SKELETON frame = ((T_0, T_1), (T_{N-2}, T_{N-1}))
                — first bigram + last bigram of any sentence
                — captures subject-phrase + predicate-phrase structure
                  regardless of intermediate length
  L3 sector 3:  full sentence (any length)

For variable-length generation:
  1. L2 retrieval: given seed L1, find skeleton frames with this L1 at start
  2. L1 chain: walk bigram chain from end of seed L1 to start of last L1
  3. Compose: T_0 T_1 [middle chain] T_{N-2} T_{N-1}

This generalizes F156's 4-word case (no middle to fill).

TESTS:
  - Mixed-length corpus: 3, 4, 5, 6, 7-word sentences
  - Retrieval at L0/L1/L2/L3 for each length
  - Generation of variable-length sentences from seeds
"""
import json
from pathlib import Path
from collections import defaultdict

import numpy as np

from srmech.amsc import hdc, format as amsc_format
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION


D = 8192


def token_seed(name: str) -> int:
    return int(amsc_format.sha256_bytes(name.encode("utf-8"))[:8], 16)


def encode_word_k4(word: str, sector: int = 0) -> np.ndarray:
    rng = np.random.default_rng(token_seed(word))
    base = hdc.klein4_random(D, rng)
    return hdc.klein4_bind(base, np.full(D, sector, dtype=np.uint8))


def encode_bigram_l1(word_a: str, word_b: str) -> np.ndarray:
    w_a = encode_word_k4(word_a, sector=0)
    w_b = encode_word_k4(word_b, sector=0)
    bound = hdc.klein4_bind(w_a, w_b)
    return hdc.klein4_bind(bound, np.full(D, 1, dtype=np.uint8))


def encode_skeleton_l2(first_bigram, last_bigram) -> np.ndarray:
    first_l1 = encode_bigram_l1(*first_bigram)
    last_l1 = encode_bigram_l1(*last_bigram)
    bound = hdc.klein4_bind(first_l1, last_l1)
    return hdc.klein4_bind(bound, np.full(D, 2, dtype=np.uint8))


def encode_sentence_l3(tokens) -> np.ndarray:
    accum = encode_word_k4(tokens[0], sector=0)
    for w in tokens[1:]:
        accum = hdc.klein4_bind(accum, encode_word_k4(w, sector=0))
    return hdc.klein4_bind(accum, np.full(D, 3, dtype=np.uint8))


def sim_k4_batch(query, candidates):
    return (candidates == query).mean(axis=1)


class VariableLengthSentenceMemory:
    """Variable-length sentence storage + generation on Klein-4 chirality-level substrate."""

    def __init__(self, D=8192):
        self.D = D
        self.words_l0 = {}
        self.bigrams_l1 = {}   # (T_i, T_{i+1}) → hv
        self.skeletons_l2 = {}  # ((T_0,T_1), (T_{N-2},T_{N-1})) → hv
        self.sentences_l3 = {}  # tuple(tokens) → hv
        # Adjacency map: given a token, what bigrams CONTINUE from it?
        self.next_after = defaultdict(set)  # T_i → set of T_{i+1}
        self.prev_before = defaultdict(set)  # T_i → set of T_{i-1}
        # Map skeletons → which sentence lengths exhibit them
        self.skeleton_lengths = defaultdict(set)

    def learn_sentence(self, tokens):
        if len(tokens) < 2:
            return  # need at least 2 tokens for any structure

        for w in tokens:
            if w not in self.words_l0:
                self.words_l0[w] = encode_word_k4(w, sector=0)

        # L1 — all consecutive bigrams
        for i in range(len(tokens) - 1):
            bigram = (tokens[i], tokens[i + 1])
            if bigram not in self.bigrams_l1:
                self.bigrams_l1[bigram] = encode_bigram_l1(*bigram)
            self.next_after[tokens[i]].add(tokens[i + 1])
            self.prev_before[tokens[i + 1]].add(tokens[i])

        # L2 — skeleton frame (first bigram, last bigram)
        if len(tokens) >= 4:
            first_bigram = (tokens[0], tokens[1])
            last_bigram = (tokens[-2], tokens[-1])
            skeleton = (first_bigram, last_bigram)
            if skeleton not in self.skeletons_l2:
                self.skeletons_l2[skeleton] = encode_skeleton_l2(first_bigram, last_bigram)
            self.skeleton_lengths[skeleton].add(len(tokens))

        # L3 — full sentence
        sentence_key = tuple(tokens)
        if sentence_key not in self.sentences_l3:
            self.sentences_l3[sentence_key] = encode_sentence_l3(tokens)

    def retrieve_bigrams_starting_with(self, word):
        """Find all L1 bigrams (word, X) for known X."""
        if word not in self.words_l0:
            return []
        results = []
        words_matrix = np.stack(list(self.words_l0.values()))
        word_list = list(self.words_l0.keys())
        seed_l0 = self.words_l0[word]
        for bigram, bg_hv in self.bigrams_l1.items():
            unsec = hdc.klein4_bind(bg_hv, np.full(self.D, 1, dtype=np.uint8))
            candidate = hdc.klein4_bind(unsec, seed_l0)
            sims = sim_k4_batch(candidate, words_matrix)
            best_word = word_list[int(sims.argmax())]
            if bigram[0] == word and best_word == bigram[1]:
                results.append((bigram, float(sims.max())))
        return results

    def retrieve_skeletons_for_first_bigram(self, first_bigram):
        """Given (T_0, T_1), find skeletons starting with this bigram."""
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

    def walk_bigram_chain(self, start_word, end_word, max_length=10):
        """Walk bigram chain from start_word to end_word using next_after adjacency.

        Returns list of intermediate token paths (greedy BFS-style).
        """
        if start_word not in self.next_after:
            return []
        # BFS for paths from start_word ending in end_word
        from collections import deque
        queue = deque([[start_word]])
        paths = []
        while queue and len(paths) < 5:
            path = queue.popleft()
            if len(path) > max_length:
                continue
            last_token = path[-1]
            if last_token == end_word and len(path) > 1:
                paths.append(path)
                continue
            for next_token in self.next_after.get(last_token, set()):
                if next_token not in path:  # no cycles
                    queue.append(path + [next_token])
        return paths

    def generate_variable_length(self, seed_bigram, top_k=5):
        """Variable-length sentence generation.

        1. Find skeletons where seed_bigram is first
        2. For each skeleton, extract last bigram
        3. Walk bigram chain from seed_bigram[1] to last_bigram[0]
        4. Compose: seed + middle + last
        """
        generated = []
        skeletons = self.retrieve_skeletons_for_first_bigram(seed_bigram)
        for skeleton, last_bigram, sk_sim in skeletons:
            # Determine which is the last bigram in the skeleton
            if skeleton[0] == seed_bigram:
                end_bg = skeleton[1]
            else:
                end_bg = skeleton[0]
            # Look up what lengths this skeleton supports
            for target_length in self.skeleton_lengths.get(skeleton, {4}):
                if target_length == 4:
                    # Direct composition: no middle
                    sentence = list(seed_bigram) + list(end_bg)
                    generated.append({
                        "sentence": sentence,
                        "length": 4,
                        "skeleton": skeleton,
                        "skeleton_sim": sk_sim,
                    })
                else:
                    # Need middle words: walk chain from seed[1] to end_bg[0]
                    paths = self.walk_bigram_chain(seed_bigram[1], end_bg[0], max_length=target_length)
                    for path in paths:
                        if len(path) + 1 == target_length - 1:  # path includes start and end of middle
                            # Full sentence: seed[0] + path + end_bg[1]
                            full = [seed_bigram[0]] + path + [end_bg[1]]
                            if len(full) == target_length:
                                generated.append({
                                    "sentence": full,
                                    "length": target_length,
                                    "skeleton": skeleton,
                                    "skeleton_sim": sk_sim,
                                    "middle_path": path[1:-1] if len(path) > 2 else [],
                                })
        # Dedupe
        seen = set()
        unique = []
        for g in generated:
            key = tuple(g["sentence"])
            if key not in seen:
                seen.add(key)
                unique.append(g)
        return unique[:top_k]


def main():
    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}\n")

    # Variable-length corpus
    TRAINING = [
        # 3-word (skip; can't form skeleton)
        # 4-word (baseline; F156 compatible)
        ["the", "cat", "sat", "mat"],
        ["the", "dog", "sat", "mat"],
        ["the", "cat", "ate", "fish"],
        # 5-word
        ["the", "cat", "sat", "on", "mat"],
        ["the", "dog", "ran", "in", "park"],
        ["the", "child", "drew", "a", "picture"],
        # 6-word
        ["the", "cat", "sat", "on", "the", "mat"],
        ["the", "dog", "watched", "a", "bird", "fly"],
        ["the", "writer", "wrote", "a", "long", "book"],
        # 7-word
        ["the", "cat", "watched", "a", "bird", "in", "tree"],
        ["the", "scientist", "studied", "the", "stars", "with", "telescope"],
        # Larger frame variety
        ["a", "bird", "flew", "across", "the", "sky"],
        ["a", "ship", "sailed", "across", "the", "sea"],
        ["the", "teacher", "explained", "the", "lesson", "to", "students"],
    ]

    print(f"Training corpus: {len(TRAINING)} sentences, lengths {sorted({len(t) for t in TRAINING})}")

    memory = VariableLengthSentenceMemory(D=D)
    for tokens in TRAINING:
        memory.learn_sentence(tokens)

    print(f"  Words:        {len(memory.words_l0)}")
    print(f"  L1 bigrams:   {len(memory.bigrams_l1)}")
    print(f"  L2 skeletons: {len(memory.skeletons_l2)}")
    print(f"  L3 sentences: {len(memory.sentences_l3)}")
    print()

    # Test 1: sentence-level self-recall (all variable lengths)
    print("=" * 80)
    print("T1: Sentence self-recall (variable lengths)")
    print("=" * 80)
    sentences_matrix = np.stack(list(memory.sentences_l3.values()))
    sentence_keys = list(memory.sentences_l3.keys())
    correct = 0
    for tokens in TRAINING:
        target = encode_sentence_l3(tokens)
        sims = sim_k4_batch(target, sentences_matrix)
        if sentence_keys[int(sims.argmax())] == tuple(tokens):
            correct += 1
    print(f"  Self-recall: {correct}/{len(TRAINING)} = {correct/len(TRAINING):.3f}")

    # Test 2: skeleton retrieval
    print()
    print("=" * 80)
    print("T2: Skeleton (L2) retrieval — given first bigram, find skeletons")
    print("=" * 80)
    for seed in [("the", "cat"), ("the", "dog"), ("the", "scientist"), ("a", "bird")]:
        if seed not in memory.bigrams_l1:
            continue
        skeletons = memory.retrieve_skeletons_for_first_bigram(seed)
        print(f"\n  Seed: {seed}")
        for sk, other, sim in skeletons[:5]:
            lengths = sorted(memory.skeleton_lengths.get(sk, set()))
            print(f"    [{sim:.2f}] skeleton {sk} (lengths: {lengths})")

    # Test 3: variable-length generation
    print()
    print("=" * 80)
    print("T3: Variable-length generation")
    print("=" * 80)
    for seed in [("the", "cat"), ("the", "dog"), ("the", "writer"), ("a", "bird"), ("the", "scientist")]:
        if seed not in memory.bigrams_l1:
            continue
        gen = memory.generate_variable_length(seed, top_k=5)
        if not gen:
            print(f"\n  Seed: {seed}  → no completions")
            continue
        print(f"\n  Seed: {seed}")
        for entry in gen:
            sent = " ".join(entry["sentence"])
            length = entry["length"]
            sk_sim = entry["skeleton_sim"]
            print(f"    [L={length}, sim={sk_sim:.2f}] {sent}")

    # Output JSON
    out = {
        "srmech_version": SRMECH_VERSION,
        "D": D,
        "training_size": len(TRAINING),
        "length_distribution": {l: sum(1 for t in TRAINING if len(t) == l) for l in sorted({len(t) for t in TRAINING})},
        "n_words": len(memory.words_l0),
        "n_bigrams": len(memory.bigrams_l1),
        "n_skeletons": len(memory.skeletons_l2),
        "sentence_self_recall": correct / len(TRAINING),
    }
    out_path = Path(__file__).parent / "R-RBS-LM-112_results.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
