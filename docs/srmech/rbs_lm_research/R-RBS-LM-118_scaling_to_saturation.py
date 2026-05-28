"""R-RBS-LM-118 — Corpus scaling to substrate saturation full coverage

Extends R-RBS-LM-113's N=50..400 sample-50 measurement to:
  - N up to substrate-saturation (find capacity bound where self-recall drops)
  - D sweep at fixed N to characterize dimension dependence
  - FULL-corpus recall (not sample-50)
  - Skeleton-uniqueness ratio per N
  - Build + retrieval latency scaling

Per [[feedback_no_mvp_framing]] + [[feedback_full_coverage_shipping_mpm_way]]:
finds where substrate breaks, not where the demo stops.

Per F154 4× ceiling: at D=8192, Klein-4 capacity is ~4× polar baseline.
Theoretical capacity scales linearly with D. This test characterizes
the empirical (not theoretical) saturation curve.
"""
import json
import time
from pathlib import Path
import importlib.util
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
_spec_vl = importlib.util.spec_from_file_location(
    "vl_memory", Path(__file__).parent / "R-RBS-LM-112_variable_length_sentences.py"
)
_mod_vl = importlib.util.module_from_spec(_spec_vl)
sys.modules["vl_memory"] = _mod_vl
_spec_vl.loader.exec_module(_mod_vl)
VariableLengthSentenceMemory = _mod_vl.VariableLengthSentenceMemory
encode_sentence_l3 = _mod_vl.encode_sentence_l3
sim_k4_batch = _mod_vl.sim_k4_batch

_spec_c = importlib.util.spec_from_file_location(
    "corpus_gen", Path(__file__).parent / "R-RBS-LM-113_larger_corpus_scaling.py"
)
_mod_c = importlib.util.module_from_spec(_spec_c)
sys.modules["corpus_gen"] = _mod_c
_spec_c.loader.exec_module(_mod_c)

# Reload encode functions at custom D via monkey-patching the module's D
import importlib

from srmech.amsc import hdc, format as amsc_format
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION


def make_encoders(D: int):
    """Build closures with parameterized D — substrate stays clean per call."""

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

    def encode_sentence_l3_d(tokens) -> np.ndarray:
        accum = encode_word_k4(tokens[0], sector=0)
        for w in tokens[1:]:
            accum = hdc.klein4_bind(accum, encode_word_k4(w, sector=0))
        return hdc.klein4_bind(accum, np.full(D, 3, dtype=np.uint8))

    return encode_word_k4, encode_bigram_l1, encode_skeleton_l2, encode_sentence_l3_d


def measure_n_at_d(N: int, D: int, rng_seed: int = 42) -> dict:
    """Build memory at corpus size N, dimension D; measure full-corpus self-recall."""
    rng = np.random.default_rng(rng_seed)
    corpus = _mod_c.generate_corpus(N, rng)
    actual_n = len(corpus)

    # Patch vl_memory module's D for clean per-D run
    enc_word, enc_bigram, enc_skel, enc_sent = make_encoders(D)

    # We rebuild a fresh memory instance at this D
    memory = VariableLengthSentenceMemory(D=D)
    # Monkey-patch the module-level encode functions used internally
    orig_enc_word = _mod_vl.encode_word_k4
    orig_enc_bigram = _mod_vl.encode_bigram_l1
    orig_enc_skel = _mod_vl.encode_skeleton_l2
    orig_enc_sent = _mod_vl.encode_sentence_l3
    _mod_vl.encode_word_k4 = enc_word
    _mod_vl.encode_bigram_l1 = enc_bigram
    _mod_vl.encode_skeleton_l2 = enc_skel
    _mod_vl.encode_sentence_l3 = enc_sent
    try:
        t_build_start = time.time()
        for tokens in corpus:
            memory.learn_sentence(tokens)
        t_build = time.time() - t_build_start

        # FULL-corpus self-recall (not sample-50)
        t_recall_start = time.time()
        sentences_matrix = np.stack(list(memory.sentences_l3.values()))
        sentence_keys = list(memory.sentences_l3.keys())
        correct = 0
        for tokens in corpus:
            target = enc_sent(tokens)
            sims = sim_k4_batch(target, sentences_matrix)
            if sentence_keys[int(sims.argmax())] == tuple(tokens):
                correct += 1
        t_recall = time.time() - t_recall_start
    finally:
        _mod_vl.encode_word_k4 = orig_enc_word
        _mod_vl.encode_bigram_l1 = orig_enc_bigram
        _mod_vl.encode_skeleton_l2 = orig_enc_skel
        _mod_vl.encode_sentence_l3 = orig_enc_sent

    skel_unique = len(memory.skeletons_l2)
    skel_ratio = skel_unique / actual_n if actual_n > 0 else 0
    return {
        "N_target": N,
        "N_actual": actual_n,
        "D": D,
        "n_words": len(memory.words_l0),
        "n_bigrams": len(memory.bigrams_l1),
        "n_skeletons": skel_unique,
        "skeleton_uniqueness_ratio": skel_ratio,
        "n_sentences_l3": len(memory.sentences_l3),
        "self_recall": correct / actual_n,
        "n_correct": correct,
        "n_misclassified": actual_n - correct,
        "build_seconds": t_build,
        "recall_seconds": t_recall,
    }


def main():
    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}\n")

    # PHASE 1: N-sweep at D=8192 baseline — find substrate saturation
    print("=" * 110)
    print("PHASE 1: N-sweep at D=8192 — find substrate saturation (FULL-corpus recall)")
    print("=" * 110)
    print(f"{'N_target':>8} | {'N_act':>5} | {'words':>5} | {'bigrams':>7} | {'skels':>5} | "
          f"{'skel_ratio':>10} | {'recall':>6} | {'misclass':>8} | {'build_s':>8} | {'recall_s':>9}")
    print("-" * 110)

    n_sweep = [400, 800, 1600, 3200, 6400, 12800]
    phase1_results = []
    for N in n_sweep:
        r = measure_n_at_d(N, D=8192)
        phase1_results.append(r)
        print(
            f"{r['N_target']:>8} | {r['N_actual']:>5} | {r['n_words']:>5} | "
            f"{r['n_bigrams']:>7} | {r['n_skeletons']:>5} | "
            f"{r['skeleton_uniqueness_ratio']:>10.3f} | {r['self_recall']:>6.3f} | "
            f"{r['n_misclassified']:>8} | {r['build_seconds']:>8.1f} | {r['recall_seconds']:>9.1f}"
        )
        if r['self_recall'] < 0.95:
            print(f"  ⚠ self-recall dropped below 0.95 at N={N}; substrate saturating")

    # PHASE 2: D-sweep at fixed N=2000 — characterize dimension dependence
    print()
    print("=" * 110)
    print("PHASE 2: D-sweep at N=2000 — characterize dimension dependence")
    print("=" * 110)
    print(f"{'D':>5} | {'N_act':>5} | {'words':>5} | {'bigrams':>7} | {'skels':>5} | "
          f"{'recall':>6} | {'misclass':>8} | {'build_s':>8} | {'recall_s':>9}")
    print("-" * 100)

    d_sweep = [2048, 4096, 8192, 16384, 32768]
    phase2_results = []
    for D in d_sweep:
        r = measure_n_at_d(2000, D=D)
        phase2_results.append(r)
        print(
            f"{r['D']:>5} | {r['N_actual']:>5} | {r['n_words']:>5} | "
            f"{r['n_bigrams']:>7} | {r['n_skeletons']:>5} | "
            f"{r['self_recall']:>6.3f} | {r['n_misclassified']:>8} | "
            f"{r['build_seconds']:>8.1f} | {r['recall_seconds']:>9.1f}"
        )

    # PHASE 3: extreme N at D=16384 — push past D=8192 saturation
    print()
    print("=" * 110)
    print("PHASE 3: extreme N at D=16384 — confirm D dependence at extreme scale")
    print("=" * 110)
    print(f"{'N_target':>8} | {'D':>5} | {'N_act':>5} | {'recall':>6} | {'misclass':>8} | {'build_s':>8}")
    print("-" * 80)
    phase3_results = []
    for N in [6400, 12800, 25600]:
        r = measure_n_at_d(N, D=16384)
        phase3_results.append(r)
        print(
            f"{r['N_target']:>8} | {r['D']:>5} | {r['N_actual']:>5} | "
            f"{r['self_recall']:>6.3f} | {r['n_misclassified']:>8} | {r['build_seconds']:>8.1f}"
        )

    out = {
        "srmech_version": SRMECH_VERSION,
        "phase1_n_sweep_at_D8192": phase1_results,
        "phase2_d_sweep_at_N2000": phase2_results,
        "phase3_extreme_n_at_D16384": phase3_results,
    }
    out_path = Path(__file__).parent / "R-RBS-LM-118_results.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
