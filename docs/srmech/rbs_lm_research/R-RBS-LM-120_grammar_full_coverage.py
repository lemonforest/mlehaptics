"""R-RBS-LM-120 — Grammar validity full coverage extension

Extends R-RBS-LM-115 (10 seeds × top_k=20 = 200 samples) to:
  - ALL non-trivial seeds (every bigram in the trained substrate that
    corresponds to a (DET, SUBJ) opener)
  - top_k sweep: {5, 10, 20, 50, 100}
  - Per-length × per-template-position violation analysis
  - Per-template-position error rate (which template slots fail most?)
  - Sentence-length × validity-rate breakdown
  - Corpus-size sensitivity: does grammar rate hold at larger N?

Per [[feedback_no_mvp_framing]] + [[feedback_full_coverage_shipping_mpm_way]]:
characterizes the substrate's grammar fidelity across the full
(seeds × top_k × N) volume, not just one slice.
"""
import json
from collections import defaultdict, Counter
from pathlib import Path
import importlib.util
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
for spec_name, fname in [
    ("vl_memory", "R-RBS-LM-112_variable_length_sentences.py"),
    ("corpus_gen", "R-RBS-LM-113_larger_corpus_scaling.py"),
    ("hier_memory", "R-RBS-LM-114_hierarchical_scale_up.py"),
]:
    _spec = importlib.util.spec_from_file_location(
        spec_name, Path(__file__).parent / fname
    )
    _mod = importlib.util.module_from_spec(_spec)
    sys.modules[spec_name] = _mod
    _spec.loader.exec_module(_mod)

import corpus_gen
import hier_memory

generate_corpus = corpus_gen.generate_corpus
HierarchicalVariableLengthMemory = hier_memory.HierarchicalVariableLengthMemory

from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION
from srmech import __version__ as SRMECH_VERSION


D = 8192


# Build POS lookup with multi-class support (homographs handled by design)
POS_LOOKUP: dict[str, set[str]] = {}


def _add_pos(words, tag):
    for w in words:
        POS_LOOKUP.setdefault(w, set()).add(tag)


_add_pos(corpus_gen.SUBJECTS_DET_THE + corpus_gen.SUBJECTS_DET_A, "SUBJ")
_add_pos(corpus_gen.VERBS_TRANSITIVE_4w, "VERB")
_add_pos(corpus_gen.OBJECTS, "OBJ")
_add_pos(corpus_gen.PREPOSITIONS, "PREP")
_add_pos(corpus_gen.ADJECTIVES, "ADJ")
_add_pos(corpus_gen.DETERMINERS, "DET")


GRAMMAR_TEMPLATES = {
    4: ("DET", "SUBJ", "VERB", "OBJ"),
    5: ("DET", "SUBJ", "VERB", "PREP", "OBJ"),
    6: ("DET", "SUBJ", "VERB", "PREP", "DET", "OBJ"),
    7: ("DET", "SUBJ", "VERB", "PREP", "DET", "ADJ", "OBJ"),
}


def tag_pos(tokens):
    return tuple(POS_LOOKUP.get(t, {"UNK"}) for t in tokens)


def is_grammatical(tokens):
    """Returns (valid, pos_seq, template, per_pos_match) — multi-class POS allowed."""
    pos_seq = tag_pos(tokens)
    template = GRAMMAR_TEMPLATES.get(len(tokens))
    if template is None:
        return False, pos_seq, ("NO_TEMPLATE",), []
    per_pos = [template[i] in pos_seq[i] for i in range(len(tokens))]
    return all(per_pos), pos_seq, template, per_pos


def get_all_det_subj_seeds(memory):
    """Return all (det, subj) bigrams present in the substrate as candidate seeds."""
    all_bigrams = set()
    for b in memory.buckets:
        all_bigrams.update(b.bigrams_l1.keys())
    seeds = [
        (w0, w1) for (w0, w1) in all_bigrams
        if "DET" in POS_LOOKUP.get(w0, set()) and "SUBJ" in POS_LOOKUP.get(w1, set())
    ]
    return sorted(seeds)


def measure_grammar_at_top_k(memory, seeds, top_k):
    """Measure grammar validity across all seeds at given top_k."""
    total_generated = 0
    total_valid = 0
    per_length = defaultdict(lambda: {"total": 0, "valid": 0})
    # Per-template-position error counts: which slot fails most?
    per_position_errors = defaultdict(Counter)  # L → Counter of position_idx → count
    pos_violation_examples = defaultdict(list)  # L → [examples]

    for seed in seeds:
        gen = memory.generate_from_seed(seed, top_k=top_k)
        for entry in gen:
            tokens = entry["sentence"]
            L = len(tokens)
            valid, pos_seq, template, per_pos_match = is_grammatical(tokens)
            total_generated += 1
            per_length[L]["total"] += 1
            if valid:
                total_valid += 1
                per_length[L]["valid"] += 1
            else:
                for i, matched in enumerate(per_pos_match):
                    if not matched:
                        per_position_errors[L][i] += 1
                if len(pos_violation_examples[L]) < 5:
                    pos_violation_examples[L].append({
                        "sentence": " ".join(tokens),
                        "pos_seq": [sorted(s) for s in pos_seq],
                        "expected": list(template),
                        "violations_at": [i for i, m in enumerate(per_pos_match) if not m],
                    })

    return {
        "top_k": top_k,
        "n_seeds": len(seeds),
        "total_generated": total_generated,
        "total_valid": total_valid,
        "pct_valid": (total_valid / total_generated * 100) if total_generated > 0 else 0,
        "per_length": dict(per_length),
        "per_length_pct": {
            L: (d["valid"] / d["total"] * 100) if d["total"] > 0 else 0
            for L, d in per_length.items()
        },
        "per_position_errors": {L: dict(c) for L, c in per_position_errors.items()},
        "violation_examples": dict(pos_violation_examples),
    }


def main():
    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}\n")

    # PHASE 1: build substrate at N=2000 (matches R-RBS-LM-115 baseline)
    # then measure across full seed set and top_k sweep
    print("=" * 100)
    print("PHASE 1: Full seed × top_k sweep at corpus N=2000 (matches R-RBS-LM-115 baseline)")
    print("=" * 100)
    rng = np.random.default_rng(42)
    corpus = generate_corpus(2000, rng)
    actual_n = len(corpus)
    print(f"Corpus: {actual_n} sentences\n")
    memory = HierarchicalVariableLengthMemory(D=D, n_buckets=16)
    for tokens in corpus:
        memory.learn_sentence(tokens)

    seeds = get_all_det_subj_seeds(memory)
    print(f"All (DET, SUBJ) seeds in substrate: {len(seeds)}\n")

    top_k_sweep = [5, 10, 20, 50, 100]
    phase1_results = []
    print(f"{'top_k':>5} | {'n_seeds':>7} | {'n_gen':>6} | {'n_valid':>7} | {'pct_valid':>9} | "
          f"{'L=4':>6} | {'L=5':>6} | {'L=6':>6} | {'L=7':>6}")
    print("-" * 90)
    for top_k in top_k_sweep:
        r = measure_grammar_at_top_k(memory, seeds, top_k)
        phase1_results.append(r)
        L_pcts = r["per_length_pct"]
        print(
            f"{r['top_k']:>5} | {r['n_seeds']:>7} | {r['total_generated']:>6} | "
            f"{r['total_valid']:>7} | {r['pct_valid']:>8.1f}% | "
            f"{L_pcts.get(4, 0):>5.1f}% | {L_pcts.get(5, 0):>5.1f}% | "
            f"{L_pcts.get(6, 0):>5.1f}% | {L_pcts.get(7, 0):>5.1f}%"
        )

    # PHASE 2: per-position violation analysis at top_k=20 (R-RBS-LM-115 baseline)
    print()
    print("=" * 100)
    print("PHASE 2: Per-template-position violation analysis at top_k=20")
    print("=" * 100)
    baseline = next(r for r in phase1_results if r["top_k"] == 20)
    print(f"{'L':>3} | template slots → violation counts")
    print("-" * 80)
    for L, errors in sorted(baseline["per_position_errors"].items()):
        template = GRAMMAR_TEMPLATES.get(L, ())
        total_errors = sum(errors.values())
        slot_str = " ".join(
            f"{i}:{template[i] if i < len(template) else '?'}={errors.get(i, 0)}"
            for i in range(L)
        )
        print(f"{L:>3} | {slot_str}   (total slot-errors: {total_errors})")

    # PHASE 3: corpus-size sensitivity — does grammar rate hold at larger N?
    print()
    print("=" * 100)
    print("PHASE 3: Corpus-size sensitivity — grammar rate at varying N (top_k=20)")
    print("=" * 100)
    print(f"{'N':>5} | {'N_act':>5} | {'seeds':>5} | {'gen':>4} | {'valid':>5} | "
          f"{'pct':>5}")
    print("-" * 60)
    phase3_results = []
    for N_target in [400, 1000, 2000, 4000]:
        rng_n = np.random.default_rng(42)
        corpus_n = generate_corpus(N_target, rng_n)
        memory_n = HierarchicalVariableLengthMemory(D=D, n_buckets=16)
        for tokens in corpus_n:
            memory_n.learn_sentence(tokens)
        seeds_n = get_all_det_subj_seeds(memory_n)
        r = measure_grammar_at_top_k(memory_n, seeds_n, 20)
        r["N_target"] = N_target
        r["N_actual"] = len(corpus_n)
        phase3_results.append(r)
        print(
            f"{N_target:>5} | {r['N_actual']:>5} | {r['n_seeds']:>5} | "
            f"{r['total_generated']:>4} | {r['total_valid']:>5} | "
            f"{r['pct_valid']:>4.1f}%"
        )

    out = {
        "srmech_version": SRMECH_VERSION,
        "D": D,
        "phase1_topk_sweep": phase1_results,
        "phase2_per_position_errors_baseline_topk20": {
            "per_position_errors": baseline["per_position_errors"],
            "violation_examples": baseline["violation_examples"],
        },
        "phase3_corpus_size_sensitivity": phase3_results,
    }
    out_path = Path(__file__).parent / "R-RBS-LM-120_results.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
