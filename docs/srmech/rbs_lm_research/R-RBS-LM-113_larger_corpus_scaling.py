"""R-RBS-LM-113 — Larger corpus scaling test (Item 3 of 5)

Tests R-RBS-LM-112 variable-length substrate at 100+ sentence scale.
Template-generated corpus across diverse subject/verb/object patterns.

Measures:
  - Retrieval accuracy as corpus scales (sentences from 30 → 100 → 200)
  - Skeleton-retrieval precision
  - Generation diversity
  - Substrate density (composite_density attestation per F141)
"""
import json
import time
import random
from pathlib import Path
import importlib.util
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
_spec = importlib.util.spec_from_file_location(
    "vl_memory", Path(__file__).parent / "R-RBS-LM-112_variable_length_sentences.py"
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["vl_memory"] = _mod
_spec.loader.exec_module(_mod)
VariableLengthSentenceMemory = _mod.VariableLengthSentenceMemory
encode_sentence_l3 = _mod.encode_sentence_l3
sim_k4_batch = _mod.sim_k4_batch

from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION


D = 8192


# Template-based sentence generator
SUBJECTS_DET_THE = ["cat", "dog", "child", "writer", "scientist", "engineer",
                    "artist", "teacher", "doctor", "musician", "captain", "farmer",
                    "baker", "queen", "knight", "wizard"]
SUBJECTS_DET_A = ["bird", "fish", "bear", "deer", "wolf", "fox", "rabbit", "horse",
                  "tiger", "lion", "frog", "owl"]
VERBS_TRANSITIVE_4w = ["sat", "ran", "ate", "watched", "drew", "wrote", "read", "built",
                       "painted", "explained", "treated", "studied", "played", "made",
                       "sailed", "flew", "swam", "slept", "drank"]
OBJECTS = ["mat", "park", "fish", "bird", "picture", "book", "paper", "bridge",
           "canvas", "lesson", "patient", "song", "bread", "ship", "sky", "sea",
           "cave", "stream", "tree", "stars", "house", "crops"]
PREPOSITIONS = ["on", "in", "at", "near", "under", "across", "behind", "above"]
DETERMINERS = ["the", "a", "my", "your"]
ADJECTIVES = ["long", "small", "tall", "happy", "ancient", "vast", "quiet"]


def _pick_det_subj(rng):
    """Pick (det, subj) — 60% 'the' pool, 40% 'a' pool."""
    idx = rng.choice([0, 1], p=[0.6, 0.4])
    if idx == 0:
        return "the", rng.choice(SUBJECTS_DET_THE)
    return "a", rng.choice(SUBJECTS_DET_A)


def gen_4word_sentences(rng, n):
    """[the/a] SUBJ VERB OBJ"""
    out = []
    for _ in range(n):
        det, subj = _pick_det_subj(rng)
        verb = rng.choice(VERBS_TRANSITIVE_4w)
        obj = rng.choice(OBJECTS)
        out.append([det, subj, verb, obj])
    return out


def gen_5word_sentences(rng, n):
    """[the] SUBJ VERB PREP OBJ"""
    out = []
    for _ in range(n):
        det, subj = _pick_det_subj(rng)
        verb = rng.choice(VERBS_TRANSITIVE_4w)
        prep = rng.choice(PREPOSITIONS)
        obj = rng.choice(OBJECTS)
        out.append([det, subj, verb, prep, obj])
    return out


def gen_6word_sentences(rng, n):
    """[the] SUBJ VERB PREP [the] OBJ"""
    out = []
    for _ in range(n):
        det, subj = _pick_det_subj(rng)
        verb = rng.choice(VERBS_TRANSITIVE_4w)
        prep = rng.choice(PREPOSITIONS)
        det2 = rng.choice(["the", "a"])
        obj = rng.choice(OBJECTS)
        out.append([det, subj, verb, prep, det2, obj])
    return out


def gen_7word_sentences(rng, n):
    """[the] SUBJ VERB ADJ [the] ADJ OBJ"""
    out = []
    for _ in range(n):
        det, subj = _pick_det_subj(rng)
        verb = rng.choice(VERBS_TRANSITIVE_4w)
        prep = rng.choice(PREPOSITIONS)
        det2 = rng.choice(["the", "a"])
        adj = rng.choice(ADJECTIVES)
        obj = rng.choice(OBJECTS)
        out.append([det, subj, verb, prep, det2, adj, obj])
    return out


def generate_corpus(n_target, rng):
    """Generate corpus distributed across 4-7 word lengths."""
    n_each = n_target // 4
    corpus = []
    corpus.extend(gen_4word_sentences(rng, n_each))
    corpus.extend(gen_5word_sentences(rng, n_each))
    corpus.extend(gen_6word_sentences(rng, n_each))
    corpus.extend(gen_7word_sentences(rng, n_target - 3 * n_each))
    # Dedupe by tuple
    seen = set()
    unique = []
    for s in corpus:
        key = tuple(s)
        if key not in seen:
            seen.add(key)
            unique.append(s)
    return unique


def measure_scaling(target_sizes, rng):
    """For each target size, build memory + measure metrics."""
    results = []
    for n_target in target_sizes:
        rng2 = np.random.default_rng(42)  # reset rng for deterministic corpus
        corpus = generate_corpus(n_target, rng2)
        actual_n = len(corpus)
        t0 = time.time()
        memory = VariableLengthSentenceMemory(D=D)
        for tokens in corpus:
            memory.learn_sentence(tokens)
        t_build = time.time() - t0

        # Self-recall
        t0 = time.time()
        sentences_matrix = np.stack(list(memory.sentences_l3.values()))
        sentence_keys = list(memory.sentences_l3.keys())
        correct = 0
        # Sample up to 50 for time control
        sample = corpus[:50] if len(corpus) > 50 else corpus
        for tokens in sample:
            target = encode_sentence_l3(tokens)
            sims = sim_k4_batch(target, sentences_matrix)
            if sentence_keys[int(sims.argmax())] == tuple(tokens):
                correct += 1
        t_recall = time.time() - t0

        results.append({
            "n_target": n_target,
            "n_actual": actual_n,
            "n_words": len(memory.words_l0),
            "n_bigrams": len(memory.bigrams_l1),
            "n_skeletons": len(memory.skeletons_l2),
            "n_sentences": len(memory.sentences_l3),
            "self_recall_sampled": correct / len(sample),
            "build_seconds": t_build,
            "recall_seconds": t_recall,
        })
    return results


def main():
    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}\n")

    target_sizes = [50, 100, 200, 400]
    rng = np.random.default_rng(42)

    print(f"{'n_target':>9} | {'n_actual':>9} | {'words':>5} | {'bigrams':>7} | {'skeletons':>9} | {'sentences':>9} | {'recall':>6} | {'build_s':>7} | {'recall_s':>8}")
    print("-" * 110)
    results = measure_scaling(target_sizes, rng)
    for r in results:
        print(
            f"{r['n_target']:>9} | {r['n_actual']:>9} | {r['n_words']:>5} | "
            f"{r['n_bigrams']:>7} | {r['n_skeletons']:>9} | {r['n_sentences']:>9} | "
            f"{r['self_recall_sampled']:.3f}  | {r['build_seconds']:>7.1f} | {r['recall_seconds']:>8.1f}"
        )

    # Generation diversity test at largest scale
    print()
    print("=" * 80)
    print("Generation diversity at N=400 (last config) — sample seeds")
    print("=" * 80)
    rng2 = np.random.default_rng(42)
    corpus = generate_corpus(400, rng2)
    memory = VariableLengthSentenceMemory(D=D)
    for tokens in corpus:
        memory.learn_sentence(tokens)

    sample_seeds = [("the", "cat"), ("the", "scientist"), ("a", "bird"), ("the", "musician"), ("a", "wolf")]
    diversity_results = {}
    for seed in sample_seeds:
        if seed not in memory.bigrams_l1:
            continue
        gen = memory.generate_variable_length(seed, top_k=10)
        diversity_results[str(seed)] = len(gen)
        print(f"\n  Seed: {seed}")
        for entry in gen[:5]:
            sent = " ".join(entry["sentence"])
            length = entry["length"]
            sim = entry["skeleton_sim"]
            print(f"    [L={length}, sim={sim:.2f}] {sent}")

    out = {
        "srmech_version": SRMECH_VERSION,
        "D": D,
        "scaling_results": results,
        "n_at_400_diversity": diversity_results,
    }
    out_path = Path(__file__).parent / "R-RBS-LM-113_results.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
