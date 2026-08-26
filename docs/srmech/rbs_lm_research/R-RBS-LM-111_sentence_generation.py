"""R-RBS-LM-111 — Sentence generation via Klein-4 cross-level walk

Per user direction 2026-05-28: 'let's try sentence generation work!'

Builds on F155's pure-structure sentence layer (R-RBS-LM-110) — adds the
GENERATIVE walk through chirality-tagged levels.

ARCHITECTURE:
  Memory class holds 4 levels of structure (per F155 chirality-sector design):
    Sector 0: word-level atomic tokens
    Sector 1: word-word pair relationships
    Sector 2: frame structures (relationship-of-relationships)
    Sector 3: full sentences

  Generation algorithm — middle-out cross-level walk:
    1. Given seed (word or partial pair), find L1 pairs at sector 1
    2. For each L1, find L2 frames containing it at sector 2
    3. Extract OTHER L1 pair from frame
    4. Compose: first_pair + other_pair → 4-word sentence
    5. Optionally validate via sector 3 sentence-level recall

TESTS:
  Mode A: seed-word completion (given 'the', generate continuations)
  Mode B: seed-pair completion (given 'the cat', generate L2 frames + sentences)
  Mode C: analogy generation (given pattern, find/compose analogous sentences)

Coherence + novelty measured:
  Coherence = generated sentence retrievable at sector 3 (was in training) OR
              semantically plausible (composition of valid patterns)
  Novelty   = generated sentences NOT in original training corpus
"""
import json
from pathlib import Path
from collections import Counter, defaultdict

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


def encode_word_pair_l1(word_a: str, word_b: str) -> np.ndarray:
    word_a_l0 = encode_word_k4(word_a, sector=0)
    word_b_l0 = encode_word_k4(word_b, sector=0)
    bound = hdc.klein4_bind(word_a_l0, word_b_l0)
    return hdc.klein4_bind(bound, np.full(D, 1, dtype=np.uint8))


def encode_rel_pair_l2(word_pair_ab, word_pair_cd) -> np.ndarray:
    rel_ab_l1 = encode_word_pair_l1(*word_pair_ab)
    rel_cd_l1 = encode_word_pair_l1(*word_pair_cd)
    bound = hdc.klein4_bind(rel_ab_l1, rel_cd_l1)
    return hdc.klein4_bind(bound, np.full(D, 2, dtype=np.uint8))


def encode_sentence_l3(sentence_tokens) -> np.ndarray:
    accum = encode_word_k4(sentence_tokens[0], sector=0)
    for w in sentence_tokens[1:]:
        accum = hdc.klein4_bind(accum, encode_word_k4(w, sector=0))
    return hdc.klein4_bind(accum, np.full(D, 3, dtype=np.uint8))


def sim_k4_batch(query, candidates_matrix):
    return (candidates_matrix == query).mean(axis=1)


class HierarchicalKlein4SentenceMemory:
    """4-level chirality-tagged sentence memory + generation."""

    def __init__(self, D=8192):
        self.D = D
        self.words_l0 = {}    # word str → hv (sector 0)
        self.pairs_l1 = {}    # (a, b) tuple → hv (sector 1)
        self.frames_l2 = {}   # ((a,b), (c,d)) tuple → hv (sector 2)
        self.sentences_l3 = {} # tuple of words → hv (sector 3)

    def learn_sentence(self, tokens):
        for w in tokens:
            if w not in self.words_l0:
                self.words_l0[w] = encode_word_k4(w, sector=0)
        for i in range(len(tokens) - 1):
            pair = (tokens[i], tokens[i + 1])
            if pair not in self.pairs_l1:
                self.pairs_l1[pair] = encode_word_pair_l1(*pair)
        if len(tokens) == 4:
            frame_key = ((tokens[0], tokens[1]), (tokens[2], tokens[3]))
            if frame_key not in self.frames_l2:
                self.frames_l2[frame_key] = encode_rel_pair_l2(*frame_key)
        sentence_key = tuple(tokens)
        if sentence_key not in self.sentences_l3:
            self.sentences_l3[sentence_key] = encode_sentence_l3(tokens)

    def retrieve_l1_partners(self, seed_word, top_k=None):
        """Given a word, find L1 pairs starting with this word.

        For each L1 pair: unbind sector 1 tag + seed_word from pair → candidate partner
        Compare candidate to all words in vocab.
        """
        if seed_word not in self.words_l0:
            return []
        words_matrix = np.stack(list(self.words_l0.values()))
        word_list = list(self.words_l0.keys())
        seed_l0 = self.words_l0[seed_word]
        partners = []
        for pair, pair_hv in self.pairs_l1.items():
            # Unbind sector 1 → bound = word_a XOR word_b
            unsec = hdc.klein4_bind(pair_hv, np.full(self.D, 1, dtype=np.uint8))
            # XOR with seed (assumed first) → recovers other word
            candidate = hdc.klein4_bind(unsec, seed_l0)
            sims = sim_k4_batch(candidate, words_matrix)
            best_word = word_list[int(sims.argmax())]
            partners.append((pair, best_word, float(sims.max())))
        # Filter to pairs where seed_word is first AND recovery matches
        valid = [(p, w, s) for p, w, s in partners
                 if p[0] == seed_word and w == p[1]]
        valid.sort(key=lambda x: x[2], reverse=True)
        if top_k:
            valid = valid[:top_k]
        return [(p, s) for p, w, s in valid]

    def retrieve_l2_frames_for_l1(self, query_l1_pair, top_k=None):
        """Given an L1 pair, find L2 frames containing it; return the OTHER L1."""
        if query_l1_pair not in self.pairs_l1:
            return []
        q_l1 = self.pairs_l1[query_l1_pair]
        l1_matrix = np.stack(list(self.pairs_l1.values()))
        l1_pair_list = list(self.pairs_l1.keys())
        candidates = []
        for frame_key, frame_hv in self.frames_l2.items():
            # Unbind sector 2 → bound = rel_AB XOR rel_CD
            unsec = hdc.klein4_bind(frame_hv, np.full(self.D, 2, dtype=np.uint8))
            # XOR with query L1 → recovers other L1
            other_l1_candidate = hdc.klein4_bind(unsec, q_l1)
            sims = sim_k4_batch(other_l1_candidate, l1_matrix)
            best_l1_idx = int(sims.argmax())
            best_other_l1 = l1_pair_list[best_l1_idx]
            candidates.append((frame_key, best_other_l1, float(sims.max())))
        # Filter to frames actually containing query_l1
        valid = [c for c in candidates if query_l1_pair in c[0]]
        valid.sort(key=lambda x: x[2], reverse=True)
        if top_k:
            valid = valid[:top_k]
        return valid

    def sentence_recall(self, tokens, top_k=3):
        """Check if a sentence is recalled at sector 3 (was it in training?)."""
        target = encode_sentence_l3(tokens)
        sentences_matrix = np.stack(list(self.sentences_l3.values()))
        sentence_keys = list(self.sentences_l3.keys())
        sims = sim_k4_batch(target, sentences_matrix)
        top_idx = np.argsort(sims)[::-1][:top_k]
        return [(sentence_keys[i], float(sims[i])) for i in top_idx]

    def generate_from_seed_word(self, seed_word, top_k_l1=5, top_k_l2=3, top_k_total=10):
        """Mode A — given seed word, walk L1 → L2 → emit 4-word sentences."""
        generated = []
        l1_partners = self.retrieve_l1_partners(seed_word, top_k=top_k_l1)
        for first_pair, l1_sim in l1_partners:
            frames = self.retrieve_l2_frames_for_l1(first_pair, top_k=top_k_l2)
            for frame_key, other_l1, l2_sim in frames:
                # Determine which side is the first_pair vs other
                if frame_key[0] == first_pair:
                    second_pair = frame_key[1]
                else:
                    second_pair = frame_key[0]
                sentence = list(first_pair) + list(second_pair)
                # Combine L1 sim + L2 sim into a confidence score
                confidence = l1_sim * l2_sim
                generated.append({
                    "sentence": sentence,
                    "first_pair": first_pair,
                    "second_pair": second_pair,
                    "l1_sim": l1_sim,
                    "l2_sim": l2_sim,
                    "confidence": confidence,
                })
        generated.sort(key=lambda x: x["confidence"], reverse=True)
        return generated[:top_k_total]

    def generate_from_seed_pair(self, seed_pair, top_k=10):
        """Mode B — given partial L1 pair, walk L2 → emit sentence completions."""
        if seed_pair not in self.pairs_l1:
            return []
        frames = self.retrieve_l2_frames_for_l1(seed_pair, top_k=None)
        generated = []
        for frame_key, other_l1, l2_sim in frames:
            if frame_key[0] == seed_pair:
                second_pair = frame_key[1]
            else:
                second_pair = frame_key[0]
            sentence = list(seed_pair) + list(second_pair)
            generated.append({
                "sentence": sentence,
                "completion_pair": second_pair,
                "l2_sim": l2_sim,
            })
        generated.sort(key=lambda x: x["l2_sim"], reverse=True)
        return generated[:top_k]


def main():
    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}\n")

    # ============================================================
    # Training corpus — 30 sentences with diverse subject-verb-object patterns
    # ============================================================
    TRAINING = [
        # cat sentences
        ["the", "cat", "sat", "mat"],
        ["the", "cat", "ran", "park"],
        ["the", "cat", "watched", "bird"],
        ["the", "cat", "ate", "fish"],
        # dog sentences
        ["the", "dog", "sat", "mat"],
        ["the", "dog", "ran", "park"],
        ["the", "dog", "watched", "bird"],
        ["the", "dog", "ate", "fish"],
        # animal/nature
        ["a", "bird", "flew", "sky"],
        ["a", "fish", "swam", "sea"],
        ["a", "bear", "slept", "cave"],
        ["a", "deer", "drank", "stream"],
        # human roles
        ["the", "child", "drew", "picture"],
        ["the", "child", "read", "book"],
        ["the", "child", "ran", "park"],
        ["the", "writer", "wrote", "book"],
        ["the", "writer", "read", "letter"],
        ["the", "scientist", "studied", "stars"],
        ["the", "scientist", "wrote", "paper"],
        ["the", "engineer", "built", "bridge"],
        ["the", "engineer", "studied", "blueprint"],
        ["the", "artist", "painted", "canvas"],
        ["the", "artist", "drew", "picture"],
        ["the", "teacher", "explained", "lesson"],
        ["the", "teacher", "read", "book"],
        # gerunds with "a"
        ["a", "doctor", "treated", "patient"],
        ["a", "farmer", "grew", "crops"],
        ["a", "musician", "played", "song"],
        ["a", "baker", "made", "bread"],
        ["a", "captain", "sailed", "ship"],
    ]

    print(f"Training corpus: {len(TRAINING)} sentences")

    # ============================================================
    # Build memory
    # ============================================================
    memory = HierarchicalKlein4SentenceMemory(D=D)
    for tokens in TRAINING:
        memory.learn_sentence(tokens)

    print(f"  Words (L0):       {len(memory.words_l0)}")
    print(f"  L1 pairs:         {len(memory.pairs_l1)}")
    print(f"  L2 frames:        {len(memory.frames_l2)}")
    print(f"  L3 sentences:     {len(memory.sentences_l3)}")
    print()

    # ============================================================
    # Mode A: Seed-word completion
    # ============================================================
    print("=" * 80)
    print("Mode A: Seed-word completion ('the' → generate full sentence)")
    print("=" * 80)
    for seed in ["the", "a", "cat", "scientist", "artist"]:
        print(f"\n  Seed word: '{seed}'")
        gen = memory.generate_from_seed_word(seed, top_k_total=5)
        if not gen:
            print(f"    (no completions; seed not in vocab or no valid L1 partners)")
            continue
        for entry in gen:
            sent = " ".join(entry["sentence"])
            conf = entry["confidence"]
            print(f"    [{conf:.2f}] {sent}")

    # ============================================================
    # Mode B: Seed-pair completion
    # ============================================================
    print()
    print("=" * 80)
    print("Mode B: Seed-pair completion ('the cat' → generate full sentence)")
    print("=" * 80)
    for seed_pair in [("the", "cat"), ("the", "dog"), ("the", "writer"),
                       ("a", "bird"), ("a", "musician")]:
        print(f"\n  Seed pair: {seed_pair}")
        gen = memory.generate_from_seed_pair(seed_pair, top_k=5)
        if not gen:
            print(f"    (no completions)")
            continue
        for entry in gen:
            sent = " ".join(entry["sentence"])
            sim = entry["l2_sim"]
            print(f"    [{sim:.2f}] {sent}")

    # ============================================================
    # Mode C: Coherence + novelty analysis
    # ============================================================
    print()
    print("=" * 80)
    print("Mode C: Coherence + novelty analysis")
    print("=" * 80)
    training_set = {tuple(t) for t in TRAINING}
    # For each seed pair, count: how many generations are in training vs novel
    n_in_training, n_novel, n_total = 0, 0, 0
    novel_sentences = []
    for seed_pair in memory.pairs_l1.keys():
        gen = memory.generate_from_seed_pair(seed_pair, top_k=10)
        for entry in gen:
            sent = tuple(entry["sentence"])
            n_total += 1
            if sent in training_set:
                n_in_training += 1
            else:
                n_novel += 1
                novel_sentences.append(sent)
    print(f"\n  Total generated:     {n_total}")
    print(f"  In training corpus:  {n_in_training} ({n_in_training/n_total*100:.1f}%)")
    print(f"  NOVEL (not in train): {n_novel} ({n_novel/n_total*100:.1f}%)")
    print(f"\n  Sample novel sentences (first 10 unique):")
    seen = set()
    sample_count = 0
    for sent in novel_sentences:
        if sent in seen:
            continue
        seen.add(sent)
        print(f"    {' '.join(sent)}")
        sample_count += 1
        if sample_count >= 10:
            break

    # ============================================================
    # Mode C-bis: Test sentence-level recall
    # ============================================================
    print()
    print("=" * 80)
    print("Mode C-bis: Sentence-level recall (do training sentences survive?)")
    print("=" * 80)
    sentence_self_recall = 0
    for tokens in TRAINING:
        recalled = memory.sentence_recall(tokens, top_k=1)
        if recalled[0][0] == tuple(tokens) and recalled[0][1] > 0.99:
            sentence_self_recall += 1
    print(f"\n  Sentence self-recall (sector 3): {sentence_self_recall}/{len(TRAINING)} = {sentence_self_recall/len(TRAINING):.3f}")

    # ============================================================
    # Mode D: Cross-frame compositional novelty
    # ============================================================
    print()
    print("=" * 80)
    print("Mode D: Cross-frame compositional novelty")
    print("=" * 80)
    print("  Test: given seed pair, compose with second-pairs from OTHER frames.")
    print("  Plausibility = the composed L2 frame has high encoded-self-similarity")
    print("  to its own encoding (basic structural test; not semantic).\n")

    # Collect all second-pair candidates from training frames
    all_second_pairs = set()
    for frame_key in memory.frames_l2.keys():
        all_second_pairs.add(frame_key[0])
        all_second_pairs.add(frame_key[1])

    compositional_results = []
    for seed_pair in [("the", "cat"), ("the", "dog"), ("the", "scientist"), ("a", "musician")]:
        if seed_pair not in memory.pairs_l1:
            continue
        # Find frames the seed_pair IS NOT IN — candidates for novel composition
        in_training_seconds = set()
        for frame_key in memory.frames_l2.keys():
            if frame_key[0] == seed_pair:
                in_training_seconds.add(frame_key[1])
            elif frame_key[1] == seed_pair:
                in_training_seconds.add(frame_key[0])
        novel_candidates = all_second_pairs - in_training_seconds - {seed_pair}

        # For each novel candidate, build the would-be frame and check structural plausibility
        # (encode + check if encoded frame retrieves any actual frame at high sim)
        l2_matrix = np.stack(list(memory.frames_l2.values()))
        l2_keys = list(memory.frames_l2.keys())
        novel_with_scores = []
        for nc in sorted(novel_candidates):
            would_be_frame_hv = encode_rel_pair_l2(seed_pair, nc)
            sims = sim_k4_batch(would_be_frame_hv, l2_matrix)
            # Highest sim to any TRAINING frame; if high, the composed structure
            # is "near" some training frame (potential plausibility)
            best_match_idx = int(sims.argmax())
            best_match_sim = float(sims.max())
            novel_with_scores.append({
                "seed": seed_pair,
                "novel_second": nc,
                "sentence": list(seed_pair) + list(nc),
                "structural_sim_to_training": best_match_sim,
                "nearest_training_frame": l2_keys[best_match_idx],
            })
        # Show top-5 novel-but-plausible compositions
        novel_with_scores.sort(key=lambda x: x["structural_sim_to_training"], reverse=True)
        print(f"  Seed: {seed_pair}")
        for c in novel_with_scores[:5]:
            sent = " ".join(c["sentence"])
            ssim = c["structural_sim_to_training"]
            print(f"    [{ssim:.2f}] {sent}  (nearest train frame: {c['nearest_training_frame']})")
        compositional_results.extend(novel_with_scores[:3])
        print()

    # Output JSON
    out = {
        "srmech_version": SRMECH_VERSION,
        "D": D,
        "training_size": len(TRAINING),
        "n_words": len(memory.words_l0),
        "n_l1_pairs": len(memory.pairs_l1),
        "n_l2_frames": len(memory.frames_l2),
        "n_l3_sentences": len(memory.sentences_l3),
        "mode_c_total_generated": n_total,
        "mode_c_in_training": n_in_training,
        "mode_c_novel": n_novel,
        "mode_c_novel_pct": n_novel / n_total * 100 if n_total else 0,
        "sentence_self_recall": sentence_self_recall / len(TRAINING),
        "sample_novel_sentences": [" ".join(s) for s in list(seen)[:20]],
        "mode_d_compositional_samples": [{
            "seed": list(c["seed"]),
            "novel_second": list(c["novel_second"]),
            "sentence": c["sentence"],
            "structural_sim": c["structural_sim_to_training"],
        } for c in compositional_results[:15]],
    }
    out_path = Path(__file__).parent / "R-RBS-LM-111_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
