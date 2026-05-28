"""R-RBS-LM-115 — Grammar validity metric (Item 5 of 5)

Measure substrate-native compositional generation quality by
classifying each generated sentence's part-of-speech (POS) sequence
and checking whether it matches a grammatically valid template.

Substrate-native; no learned model. POS comes from the corpus
generator's word categories (SUBJECTS / VERBS / OBJECTS / PREPS / ADJS
/ DETERMINERS) — same vocabulary the substrate was trained on.

Grammar templates (by sentence length):
  L=4: DET SUBJ VERB OBJ
  L=5: DET SUBJ VERB PREP OBJ
  L=6: DET SUBJ VERB PREP DET OBJ
  L=7: DET SUBJ VERB PREP DET ADJ OBJ

For each generated sentence:
  1. Tag each word with its POS class from corpus categories
  2. Compare POS sequence to the expected template for its length
  3. Mark VALID if exact match, INVALID otherwise

Metric: pct_valid per seed + overall.
"""
import json
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


# Build POS lookup from corpus_gen categories — words can have multiple POS
# classes (homographs like 'bird' which is both SUBJ_DET_A and OBJ).
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


# Grammar templates by length
GRAMMAR_TEMPLATES = {
    4: ("DET", "SUBJ", "VERB", "OBJ"),
    5: ("DET", "SUBJ", "VERB", "PREP", "OBJ"),
    6: ("DET", "SUBJ", "VERB", "PREP", "DET", "OBJ"),
    7: ("DET", "SUBJ", "VERB", "PREP", "DET", "ADJ", "OBJ"),
}


def tag_pos(tokens: list[str]) -> tuple:
    """Tag each token with its POS class set. UNK if not in lookup."""
    return tuple(POS_LOOKUP.get(t, {"UNK"}) for t in tokens)


def is_grammatical(tokens: list[str]) -> tuple[bool, tuple, tuple]:
    """Check if any POS assignment matches the template for its length.

    Homographs (e.g. 'bird' as both SUBJ and OBJ) are valid if ANY
    assignment satisfies the template.
    """
    pos_seq = tag_pos(tokens)
    template = GRAMMAR_TEMPLATES.get(len(tokens))
    if template is None:
        return False, tuple(sorted(p)[0] for p in pos_seq), ("NO_TEMPLATE",)
    # Check whether each position's tag-set contains the expected tag
    valid = all(template[i] in pos_seq[i] for i in range(len(tokens)))
    # For display: pick the matching assignment if valid, else best-guess
    if valid:
        display = template
    else:
        display = tuple(sorted(p)[0] for p in pos_seq)
    return valid, display, template


def measure_grammar_validity(memory: HierarchicalVariableLengthMemory,
                              seeds: list[tuple], top_k: int = 20) -> dict:
    """For each seed, generate sentences and measure grammar validity."""
    per_seed = {}
    overall = {"n_generated": 0, "n_valid": 0, "by_length": {}, "invalid_examples": []}

    for seed in seeds:
        gen = memory.generate_from_seed(seed, top_k=top_k)
        n_valid = 0
        n_total = len(gen)
        invalid_samples = []
        by_length = {}

        for entry in gen:
            tokens = entry["sentence"]
            length = len(tokens)
            valid, pos_seq, template = is_grammatical(tokens)
            by_length.setdefault(length, {"total": 0, "valid": 0})
            by_length[length]["total"] += 1
            if valid:
                n_valid += 1
                by_length[length]["valid"] += 1
            else:
                if len(invalid_samples) < 3:
                    invalid_samples.append({
                        "sentence": " ".join(tokens),
                        "pos_seq": pos_seq,
                        "expected": template,
                    })

            # Aggregate
            overall["by_length"].setdefault(length, {"total": 0, "valid": 0})
            overall["by_length"][length]["total"] += 1
            if valid:
                overall["by_length"][length]["valid"] += 1
            else:
                if len(overall["invalid_examples"]) < 10:
                    overall["invalid_examples"].append({
                        "sentence": " ".join(tokens),
                        "pos_seq": list(pos_seq),
                        "expected": list(template),
                    })

        per_seed[str(seed)] = {
            "n_generated": n_total,
            "n_valid": n_valid,
            "pct_valid": (n_valid / n_total * 100) if n_total > 0 else 0.0,
            "by_length": by_length,
            "invalid_samples": invalid_samples,
        }
        overall["n_generated"] += n_total
        overall["n_valid"] += n_valid

    overall["pct_valid"] = (
        overall["n_valid"] / overall["n_generated"] * 100
        if overall["n_generated"] > 0 else 0.0
    )
    return {"per_seed": per_seed, "overall": overall}


def main():
    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}; D={D}\n")

    # Build hierarchical memory at N=2000 (good substrate density)
    rng = np.random.default_rng(42)
    corpus = generate_corpus(2000, rng)
    actual_n = len(corpus)
    print(f"Building hierarchical memory: N={actual_n}, n_buckets=16\n")

    memory = HierarchicalVariableLengthMemory(D=D, n_buckets=16)
    for tokens in corpus:
        memory.learn_sentence(tokens)

    # Sample seeds for grammar test
    seeds = [
        ("the", "cat"), ("the", "dog"), ("the", "scientist"),
        ("the", "musician"), ("the", "writer"), ("the", "queen"),
        ("a", "bird"), ("a", "wolf"), ("a", "tiger"), ("a", "fox"),
    ]

    print(f"Measuring grammar validity across {len(seeds)} seeds, top_k=20 each\n")
    metrics = measure_grammar_validity(memory, seeds, top_k=20)

    print(f"{'Seed':>20} | {'N gen':>5} | {'N valid':>7} | {'pct_valid':>9} | by_length")
    print("-" * 100)
    for seed_str, data in metrics["per_seed"].items():
        by_len_str = " ".join(
            f"L{L}={d['valid']}/{d['total']}" for L, d in sorted(data["by_length"].items())
        )
        print(
            f"{seed_str:>20} | {data['n_generated']:>5} | {data['n_valid']:>7} | "
            f"{data['pct_valid']:>8.1f}% | {by_len_str}"
        )

    print()
    print("=" * 80)
    print("OVERALL grammar validity")
    print("=" * 80)
    overall = metrics["overall"]
    print(f"  Total generated: {overall['n_generated']}")
    print(f"  Total valid:     {overall['n_valid']}")
    print(f"  Pct valid:       {overall['pct_valid']:.1f}%")
    print(f"  By length:")
    for L, d in sorted(overall["by_length"].items()):
        pct = d["valid"] / d["total"] * 100 if d["total"] > 0 else 0
        print(f"    L={L}: {d['valid']}/{d['total']} ({pct:.1f}%)")

    if overall["invalid_examples"]:
        print(f"\n  Sample INVALID sentences (first 5):")
        for ex in overall["invalid_examples"][:5]:
            print(f"    \"{ex['sentence']}\"")
            print(f"      POS:      {ex['pos_seq']}")
            print(f"      Expected: {ex['expected']}")

    out = {
        "srmech_version": SRMECH_VERSION,
        "D": D,
        "corpus_n": actual_n,
        "n_buckets": 16,
        "grammar_metrics": metrics,
    }
    out_path = Path(__file__).parent / "R-RBS-LM-115_results.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
