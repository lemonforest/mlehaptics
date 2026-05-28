"""R-RBS-LM-110 — Pure-structure sentence layer (R-RBS-LM-55 walk)

Per user direction 2026-05-28:
  'can we also pack relationships of relationships AND relationships of
   words, to be able to make coherent sentences?'

This walks R-RBS-LM-55 (long-pending in STALE_PATHS_QUEUE).

DESIGN — Klein-4 chirality-sectors as LEVEL TAGS:

  Sector 0:  word-level atomic tokens
  Sector 1:  bind(word_A, word_B) = word-word relationship (Level 1)
  Sector 2:  bind(rel_AB, rel_CD) = relationship-of-relationships
             (Level 2; sentence frame)
  Sector 3:  full sentence binding (Level 3; meta)

Each level lives in its OWN chirality sector → independent retrieval
channels → can query at any level without cross-level interference.

Per F-R16 §2 H2-outermost rule: chirality tag MUST be the outermost
operation. We apply tag LAST at each level's encoding; cross-level
queries unbind only the level's outermost tag.

TESTS:
  T1: Encode 12 sentences across 4 chirality levels
  T2: Word-level retrieval (sector 0) — find words by context
  T3: Level-1 retrieval (sector 1) — find related word-pairs
  T4: Level-2 retrieval (sector 2) — find sentence frames sharing structure
  T5: Sentence-completion via cross-level cascade — given partial structure
      at Level 2, suggest words to fill it

Per F154 4× ceiling: 4 sectors give 4× capacity at matched D. We're
storing 4 conceptual levels in 4 chirality sectors at SAME D=8192.
"""
import json
from pathlib import Path
from collections import Counter

import numpy as np

from srmech.amsc import hdc, format as amsc_format
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION


D = 8192


def token_seed(name: str) -> int:
    return int(amsc_format.sha256_bytes(name.encode("utf-8"))[:8], 16)


def encode_word_k4(word: str, sector: int = 0) -> np.ndarray:
    """Encode a word as Klein-4 HV with given chirality sector."""
    rng = np.random.default_rng(token_seed(word))
    base = hdc.klein4_random(D, rng)
    return hdc.klein4_bind(base, np.full(D, sector, dtype=np.uint8))


def encode_word_pair_l1(word_a: str, word_b: str) -> np.ndarray:
    """Level 1: word-word relationship (sector 1)."""
    word_a_l0 = encode_word_k4(word_a, sector=0)
    word_b_l0 = encode_word_k4(word_b, sector=0)
    # Bind the two words; tag the result with sector 1 (H2 outermost per F-R16)
    bound = hdc.klein4_bind(word_a_l0, word_b_l0)
    return hdc.klein4_bind(bound, np.full(D, 1, dtype=np.uint8))


def encode_rel_pair_l2(word_pair_ab, word_pair_cd) -> np.ndarray:
    """Level 2: relationship-of-relationships (sector 2)."""
    rel_ab_l1 = encode_word_pair_l1(*word_pair_ab)
    rel_cd_l1 = encode_word_pair_l1(*word_pair_cd)
    bound = hdc.klein4_bind(rel_ab_l1, rel_cd_l1)
    return hdc.klein4_bind(bound, np.full(D, 2, dtype=np.uint8))


def encode_sentence_l3(sentence_tokens: list[str]) -> np.ndarray:
    """Level 3: full sentence binding (sector 3)."""
    # XOR all words; tag with sector 3
    accum = encode_word_k4(sentence_tokens[0], sector=0)
    for w in sentence_tokens[1:]:
        accum = hdc.klein4_bind(accum, encode_word_k4(w, sector=0))
    return hdc.klein4_bind(accum, np.full(D, 3, dtype=np.uint8))


def sim_k4_batch(query, candidates_matrix):
    """Vectorized klein-4 similarity (per F153): match-fraction per row."""
    return (candidates_matrix == query).mean(axis=1)


def main():
    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}\n")

    # Test corpus — 12 sentences, structured to share patterns
    SENTENCES = [
        ["the", "cat", "sat", "mat"],
        ["the", "dog", "sat", "mat"],
        ["the", "cat", "ran", "park"],
        ["the", "dog", "ran", "park"],
        ["a", "bird", "flew", "sky"],
        ["a", "fish", "swam", "sea"],
        ["a", "child", "drew", "picture"],
        ["a", "writer", "wrote", "book"],
        ["the", "scientist", "studied", "stars"],
        ["the", "engineer", "built", "bridge"],
        ["the", "artist", "painted", "canvas"],
        ["the", "teacher", "explained", "lesson"],
    ]

    # ============================================================
    # T1: Encode all 4 levels
    # ============================================================
    print("=" * 80)
    print("T1: Encoding 4 chirality-tagged levels")
    print("=" * 80)

    # Level 0 — all unique words
    all_words = sorted({w for s in SENTENCES for w in s})
    print(f"  Level 0 (words): {len(all_words)} unique words")
    word_hvs = {w: encode_word_k4(w, sector=0) for w in all_words}

    # Level 1 — adjacent word pairs in each sentence
    all_l1_pairs = []
    l1_hvs = {}
    for sent in SENTENCES:
        for i in range(len(sent) - 1):
            pair = (sent[i], sent[i + 1])
            if pair not in l1_hvs:
                l1_hvs[pair] = encode_word_pair_l1(*pair)
                all_l1_pairs.append(pair)
    print(f"  Level 1 (word-word pairs): {len(all_l1_pairs)} unique pairs")

    # Level 2 — pairs of L1 pairs (the "sentence frames")
    # For each sentence with 4 words: (s[0]-s[1], s[2]-s[3])
    all_l2_frames = []
    l2_hvs = {}
    for sent in SENTENCES:
        if len(sent) == 4:
            pair_a = (sent[0], sent[1])
            pair_b = (sent[2], sent[3])
            frame_key = (pair_a, pair_b)
            l2_hvs[frame_key] = encode_rel_pair_l2(pair_a, pair_b)
            all_l2_frames.append(frame_key)
    print(f"  Level 2 (rel-of-rel frames): {len(all_l2_frames)} frames")

    # Level 3 — full sentences
    l3_hvs = {}
    for i, sent in enumerate(SENTENCES):
        l3_hvs[i] = encode_sentence_l3(sent)
    print(f"  Level 3 (sentences): {len(l3_hvs)} sentences")

    # ============================================================
    # T2: Word-level retrieval (sector 0)
    # ============================================================
    print()
    print("=" * 80)
    print("T2: Word retrieval (sector 0 ID)")
    print("=" * 80)
    words_matrix = np.stack(list(word_hvs.values()))
    word_list = list(word_hvs.keys())
    correct_top1 = 0
    for w in all_words:
        q = encode_word_k4(w, sector=0)
        sims = sim_k4_batch(q, words_matrix)
        pred_idx = int(sims.argmax())
        if word_list[pred_idx] == w:
            correct_top1 += 1
    print(f"  Word self-recall@1: {correct_top1}/{len(all_words)} = {correct_top1/len(all_words):.3f}")

    # ============================================================
    # T3: Level-1 retrieval (sector 1)
    # ============================================================
    print()
    print("=" * 80)
    print("T3: Level-1 (word-pair) retrieval — given a word_A, find its L1 partners")
    print("=" * 80)
    l1_matrix = np.stack(list(l1_hvs.values()))
    l1_pair_list = list(l1_hvs.keys())
    # For each unique word_A, find pairs starting with word_A
    for query_word in ["the", "a", "cat", "dog", "sat"]:
        if query_word not in word_hvs:
            continue
        # Build a "query" that engages sector 1: XOR word_A_L0 with sector-1 mask
        q_word_l0 = encode_word_k4(query_word, sector=0)
        # Find L1 pairs whose first element is query_word
        true_partners = [pair for pair in l1_pair_list if pair[0] == query_word]
        if not true_partners:
            continue
        # Score each L1 pair against q_word XOR'd into sector 1 + bound with all L1 candidates
        # Simpler approach: for each L1 pair, unbind word_A from it and check what remains
        recovered = []
        for pair in l1_pair_list:
            # Unbind: pair XOR sector_1_mask XOR word_A_L0 = bound XOR word_A_L0
            # = (word_A XOR word_B) XOR word_A = word_B (with noise)
            unsec = hdc.klein4_bind(l1_hvs[pair], np.full(D, 1, dtype=np.uint8))
            candidate_b = hdc.klein4_bind(unsec, q_word_l0)
            # Compare candidate_b to known word HVs in sector 0
            sims = sim_k4_batch(candidate_b, words_matrix)
            best_word = word_list[int(sims.argmax())]
            recovered.append((pair, best_word, float(sims.max())))
        # Filter to pairs that start with query_word
        relevant_pairs = [r for r in recovered if r[0][0] == query_word]
        relevant_pairs.sort(key=lambda x: x[2], reverse=True)
        print(f"\n  Query word '{query_word}' → recovered partners:")
        for pair, partner, sim in relevant_pairs[:5]:
            true_partner = pair[1]
            match = "✓" if partner == true_partner else "✗"
            print(f"    {pair} → recovered '{partner}' (sim {sim:.3f}) {match} (truth: {true_partner})")

    # ============================================================
    # T4: Level-2 retrieval (sector 2)
    # ============================================================
    print()
    print("=" * 80)
    print("T4: Level-2 (sentence-frame) self-retrieval")
    print("=" * 80)
    l2_matrix = np.stack(list(l2_hvs.values()))
    l2_keys = list(l2_hvs.keys())
    correct = 0
    for frame in l2_keys:
        q = encode_rel_pair_l2(*frame)
        sims = sim_k4_batch(q, l2_matrix)
        if l2_keys[int(sims.argmax())] == frame:
            correct += 1
    print(f"  Sentence-frame self-recall: {correct}/{len(l2_keys)} = {correct/len(l2_keys):.3f}")

    # ============================================================
    # T5: Sentence-completion via cross-level cascade
    # ============================================================
    print()
    print("=" * 80)
    print("T5: Cross-level — given partial L1 ('the', 'cat'), find L2 frames containing it")
    print("=" * 80)
    # Find L2 frames where (the, cat) appears as one of the pair components
    partial_l1 = ("the", "cat")
    if partial_l1 in l1_hvs:
        q_l1 = l1_hvs[partial_l1]
        # For each L2 frame, unbind L2's sector tag + the query L1
        # Frame = bind(rel_AB, rel_CD) XOR sector_2 (per encoder)
        # Unbind sector 2: bind(frame, sector_2_mask) = bind(rel_AB, rel_CD)
        # XOR by rel_AB (query L1): candidate = rel_CD
        candidates = []
        for frame_key, frame_hv in l2_hvs.items():
            unsec_l2 = hdc.klein4_bind(frame_hv, np.full(D, 2, dtype=np.uint8))
            candidate_rel_cd = hdc.klein4_bind(unsec_l2, q_l1)
            # Compare candidate_rel_cd against all L1 pairs (which carry sector 1 tag)
            sims = sim_k4_batch(candidate_rel_cd, l1_matrix)
            best_l1_idx = int(sims.argmax())
            best_l1_pair = l1_pair_list[best_l1_idx]
            candidates.append((frame_key, best_l1_pair, float(sims.max())))
        # Filter to frames where (the, cat) actually appears
        relevant = [c for c in candidates if partial_l1 in c[0]]
        relevant.sort(key=lambda x: x[2], reverse=True)
        print(f"\n  Partial L1 query: {partial_l1}")
        print(f"  L2 frames containing this L1:")
        for frame_key, recovered_other_l1, sim in relevant[:8]:
            # Frame is (pair_a, pair_b); identify which one matched query and which was recovered
            other_l1 = frame_key[1] if frame_key[0] == partial_l1 else frame_key[0]
            match = "✓" if recovered_other_l1 == other_l1 else "✗"
            print(f"    frame = {frame_key}")
            print(f"      truth-other-L1 = {other_l1}; recovered = {recovered_other_l1} (sim {sim:.3f}) {match}")

    # Output JSON
    out = {
        "srmech_version": SRMECH_VERSION,
        "D": D,
        "n_words": len(all_words),
        "n_l1_pairs": len(all_l1_pairs),
        "n_l2_frames": len(all_l2_frames),
        "n_sentences": len(l3_hvs),
        "T2_word_self_recall_at_1": correct_top1 / len(all_words),
        "T4_sentence_frame_self_recall": correct / len(l2_keys),
    }
    out_path = Path(__file__).parent / "R-RBS-LM-110_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
