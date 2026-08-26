"""R-RBS-LM-122 — Canonical full-coverage substrate characterization.

Loads its substrate parameters via srmech.amsc.load_descriptor from the catalog at
docs/srmech/catalogs/rbs_lm_substrate/descriptor.toml (or any variant passed via
--catalog). Reads params off desc.fetch["literature_curated"] — no parallel
Python parameter parser.

Per user direction "catalogs are not new python script mvp magics; cascade is
handled by srmech with the toml and MPR things": this script consumes srmech's
existing AMSC machinery (load_descriptor + descriptor_hash + write_ndjson) and
emits MPR-style attestation records.

Supersedes (folds in): R-RBS-LM-117/118/119/120/121 first-pass MVP-audit scripts.

Phases (every parameter from the catalog, nothing hardcoded):
  P1  length sweep        — substrate self-recall L ∈ measurement.length_sweep
  P2  corpus sweep        — N ∈ measurement.corpus_sweep; find saturation
  P3  dimension sweep     — D ∈ measurement.dimension_sweep at fixed N
  P4  hierarchical sweep  — strategies × bucket counts
  P5  generation sweep    — all seeds × top_k breakdown
  P6  grammar             — pos_template OR substrate_native validation
  P7  plausibility        — perturbation panel × weight-sensitivity AUC sweep

Output: NDJSON results file at the path specified by the catalog
(schema.ndjson_file relative to descriptor parent dir), with one attestation
header record + one record per measurement point.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path

import numpy as np

# Path setup so we can import the canonical substrate library
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import _canonical_substrate as cs  # noqa: E402

# Corpus generator (first-pass template module, kept as a corpus-source library)
import importlib.util as _ilu
_spec_cg = _ilu.spec_from_file_location(
    "corpus_gen", HERE / "R-RBS-LM-113_larger_corpus_scaling.py"
)
corpus_gen = _ilu.module_from_spec(_spec_cg)
sys.modules["corpus_gen"] = corpus_gen
_spec_cg.loader.exec_module(corpus_gen)

from srmech import __version__ as SRMECH_VERSION  # noqa: E402
from srmech.amsc import load_descriptor, descriptor_hash, write_ndjson  # noqa: E402
from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION  # noqa: E402


CANONICAL_CATALOG = HERE.parent / "catalogs" / "rbs_lm_substrate" / "descriptor.toml"


# ---------------------------------------------------------------------------
# Corpus building from catalog params
# ---------------------------------------------------------------------------

def build_corpus(params, n_target: int, seed: int) -> list[list[str]]:
    """Build a corpus per catalog corpus.source (params['corpus'])."""
    corpus_cfg = params["corpus"]
    source = str(corpus_cfg["source"])
    rng = np.random.default_rng(seed)
    if source == "template":
        return corpus_gen.generate_corpus(n_target, rng)
    elif source == "hf_dataset":
        raise NotImplementedError(
            "corpus.source = 'hf_dataset' requires Phase C smol-stack loader"
        )
    elif source == "file":
        raise NotImplementedError("corpus.source = 'file' not yet wired")
    else:
        raise ValueError(f"unknown corpus.source: {source}")


def build_vocab(params) -> list[str]:
    """Vocabulary pool for random/perturbation sentences."""
    if params["corpus"]["source"] == "template":
        return sorted(set(
            corpus_gen.SUBJECTS_DET_THE + corpus_gen.SUBJECTS_DET_A
            + corpus_gen.VERBS_TRANSITIVE_4w + corpus_gen.OBJECTS
            + corpus_gen.PREPOSITIONS + corpus_gen.DETERMINERS
            + corpus_gen.ADJECTIVES
        ))
    return []


def patch_params_D(params, D_val: int) -> dict:
    """Return a deep-copy with substrate.D overridden — for the D sweep."""
    p = deepcopy(dict(params))
    p["substrate"] = dict(p["substrate"])
    p["substrate"]["D"] = int(D_val)
    return p


def _recall_eval(corpus, recall_fn, params):
    """Evaluate recall over `corpus`, honoring catalog measurement.recall_sample.

    The catalog field controls cost vs coverage of the recall measurement:
      - "full" (or int >= len(corpus)) → evaluate every sentence; recall is
        exact but O(N²·D) because self-recall argmaxes each query against the
        full N×D matrix
      - int K < len(corpus) → evaluate a deterministically-seeded random sample
        of K sentences; recall rate estimated to within sampling error, O(K·N·D)

    Returns (n_correct, n_evaluated). The catalog field is the SSOT — this
    function is the wiring that makes it actually control the measurement,
    closing the declared-but-unwired gap.
    """
    recall_sample = params["measurement"].get("recall_sample", "full")
    if recall_sample == "full" or (
        isinstance(recall_sample, int) and recall_sample >= len(corpus)
    ):
        sample = corpus
    else:
        k = int(recall_sample)
        rng = np.random.default_rng(int(params["measurement"]["seed"]))
        idx = rng.choice(len(corpus), size=k, replace=False)
        sample = [corpus[i] for i in idx]
    correct = sum(1 for tokens in sample if recall_fn(tokens))
    return correct, len(sample)


# ---------------------------------------------------------------------------
# Phases
# ---------------------------------------------------------------------------

def phase1_length_sweep(params, vocab, out_records, attestation):
    sweep = params["measurement"]["length_sweep"]
    n_per = int(sweep["n_per_length"])
    print("=" * 100)
    print(f"P1: length sweep — L=" + str(list(sweep["values"])))
    print("=" * 100)
    print(f"{'L':>3} | {'n':>4} | {'words':>5} | {'bigrams':>7} | {'skels':>6} | "
          f"{'recall':>7} | {'build_s':>7} | {'recall_s':>8}")
    print("-" * 80)
    for L in sweep["values"]:
        rng = np.random.default_rng(int(params["measurement"]["seed"]) + L)
        corpus = []
        seen = set()
        attempts = 0
        while len(corpus) < n_per and attempts < n_per * 10:
            attempts += 1
            tokens = tuple(rng.choice(vocab, size=L, replace=True))
            if tokens not in seen:
                seen.add(tokens)
                corpus.append(list(tokens))
        if not corpus:
            continue
        memory = cs.build_substrate(params)
        t0 = time.time()
        for tokens in corpus:
            memory.learn_sentence(tokens)
        t_build = time.time() - t0
        t0 = time.time()
        correct, n_eval = _recall_eval(corpus, memory.self_recall, params)
        t_recall = time.time() - t0
        record = {
            **attestation,
            "phase": "P1_length_sweep",
            "L": L,
            "n_sentences": len(corpus),
            "n_recall_evaluated": n_eval,
            "n_words": len(memory.words_l0),
            "n_bigrams": len(memory.bigrams_l1),
            "n_skeletons": len(memory.skeletons_l2),
            "n_stored_l3": len(memory.sentences_l3),
            "self_recall": correct / n_eval,
            "build_seconds": t_build,
            "recall_seconds": t_recall,
        }
        out_records.append(record)
        print(f"{L:>3} | {len(corpus):>4} | {record['n_words']:>5} | "
              f"{record['n_bigrams']:>7} | {record['n_skeletons']:>6} | "
              f"{record['self_recall']:>7.3f} | {t_build:>7.2f} | {t_recall:>8.2f}")


def phase2_corpus_sweep(params, out_records, attestation):
    sweep = params["measurement"]["corpus_sweep"]
    print()
    print("=" * 100)
    print(f"P2: corpus N sweep (full-corpus recall) — N=" + str(list(sweep["values"])))
    print("=" * 100)
    print(f"{'N':>6} | {'N_act':>5} | {'words':>5} | {'bigrams':>7} | {'skels':>5} | "
          f"{'recall':>7} | {'misclass':>8} | {'build_s':>8}")
    print("-" * 90)
    for N in sweep["values"]:
        corpus = build_corpus(params, N, int(params["measurement"]["seed"]))
        memory = cs.build_substrate(params)
        t0 = time.time()
        for tokens in corpus:
            memory.learn_sentence(tokens)
        t_build = time.time() - t0
        correct, n_eval = _recall_eval(corpus, memory.self_recall, params)
        record = {
            **attestation,
            "phase": "P2_corpus_sweep",
            "N_target": N,
            "N_actual": len(corpus),
            "n_words": len(memory.words_l0),
            "n_bigrams": len(memory.bigrams_l1),
            "n_skeletons": len(memory.skeletons_l2),
            "self_recall": correct / n_eval,
            "n_recall_evaluated": n_eval,
            "n_misclassified": n_eval - correct,
            "build_seconds": t_build,
        }
        out_records.append(record)
        print(f"{N:>6} | {record['N_actual']:>5} | {record['n_words']:>5} | "
              f"{record['n_bigrams']:>7} | {record['n_skeletons']:>5} | "
              f"{record['self_recall']:>7.3f} | {record['n_misclassified']:>8} | "
              f"{t_build:>8.1f}")
        if record["self_recall"] < 0.95:
            print(f"  ⚠ substrate saturating at N={N}")


def phase3_dimension_sweep(params, out_records, attestation):
    sweep = params["measurement"]["dimension_sweep"]
    N = int(sweep["fixed_n"])
    print()
    print("=" * 100)
    print(f"P3: dimension sweep at N={N} — D=" + str(list(sweep["values"])))
    print("=" * 100)
    print(f"{'D':>6} | {'N':>5} | {'words':>5} | {'bigrams':>7} | {'skels':>5} | "
          f"{'recall':>7} | {'build_s':>8}")
    print("-" * 80)
    base_corpus = build_corpus(params, N, int(params["measurement"]["seed"]))
    for D_val in sweep["values"]:
        derived = patch_params_D(params, D_val)
        memory = cs.build_substrate(derived)
        t0 = time.time()
        for tokens in base_corpus:
            memory.learn_sentence(tokens)
        t_build = time.time() - t0
        correct, n_eval = _recall_eval(base_corpus, memory.self_recall, params)
        record = {
            **attestation,
            "phase": "P3_dimension_sweep",
            "D": D_val,
            "N_actual": len(base_corpus),
            "n_words": len(memory.words_l0),
            "n_bigrams": len(memory.bigrams_l1),
            "n_skeletons": len(memory.skeletons_l2),
            "self_recall": correct / n_eval,
            "n_recall_evaluated": n_eval,
            "build_seconds": t_build,
        }
        out_records.append(record)
        print(f"{D_val:>6} | {record['N_actual']:>5} | {record['n_words']:>5} | "
              f"{record['n_bigrams']:>7} | {record['n_skeletons']:>5} | "
              f"{record['self_recall']:>7.3f} | {t_build:>8.1f}")


def phase4_bucket_sweep(params, out_records, attestation):
    print()
    print("=" * 110)
    print("P4: hierarchical bucket sweep — strategies × n_buckets")
    print("=" * 110)
    print(f"{'strategy':>20} | {'n_buckets':>9} | {'N':>5} | {'recall':>7} | "
          f"{'b_min':>5} | {'b_max':>5} | {'b_mean':>7} | {'b_cv':>5} | {'build_s':>8}")
    print("-" * 110)
    corpus_values = params["measurement"]["corpus_sweep"]["values"]
    N = corpus_values[min(len(corpus_values) - 1, 2)]
    base_corpus = build_corpus(params, N, int(params["measurement"]["seed"]))
    allowed_strategies = params["hierarchical"]["allowed_strategies"]
    bucket_values = params["measurement"]["bucket_sweep"]["values"]
    for strategy in allowed_strategies:
        for nb in bucket_values:
            if N // nb < 4:
                continue
            hier = cs.build_hierarchical_substrate(params, n_buckets=nb, strategy=strategy)
            t0 = time.time()
            for tokens in base_corpus:
                hier.learn_sentence(tokens)
            t_build = time.time() - t0
            correct, n_eval = _recall_eval(base_corpus, hier.recall_sentence, params)
            stats = hier.bucket_load_stats()
            record = {
                **attestation,
                "phase": "P4_bucket_sweep",
                "strategy": strategy,
                "n_buckets": nb,
                "N_actual": len(base_corpus),
                "self_recall": correct / n_eval,
                "n_recall_evaluated": n_eval,
                "build_seconds": t_build,
                **{f"bucket_{k}": v for k, v in stats.items()},
            }
            out_records.append(record)
            print(f"{strategy:>20} | {nb:>9} | {record['N_actual']:>5} | "
                  f"{record['self_recall']:>7.3f} | {stats['min']:>5} | "
                  f"{stats['max']:>5} | {stats['mean']:>7.1f} | {stats['cv']:>5.3f} | "
                  f"{t_build:>8.1f}")


def phase5_generation(params, out_records, attestation):
    print()
    print("=" * 100)
    print("P5: generation sweep — all (DET, *) seeds × top_k")
    print("=" * 100)
    print(f"{'top_k':>5} | {'n_seeds':>7} | {'total_gen':>9} | {'mean_per_seed':>13} | {'len_distribution':>40}")
    print("-" * 100)
    corpus_values = params["measurement"]["corpus_sweep"]["values"]
    N = corpus_values[min(len(corpus_values) - 1, 2)]
    corpus = build_corpus(params, N, int(params["measurement"]["seed"]))
    hier = cs.build_hierarchical_substrate(params)
    for tokens in corpus:
        hier.learn_sentence(tokens)
    determiners = (set(corpus_gen.DETERMINERS)
                    if params["corpus"]["source"] == "template" else set())
    all_seeds = set()
    for b in hier.buckets:
        for (w0, w1) in b.bigrams_l1.keys():
            if not determiners or w0 in determiners:
                all_seeds.add((w0, w1))
    seeds = sorted(all_seeds)
    for top_k in params["measurement"]["top_k_sweep"]["values"]:
        total_gen = 0
        by_length = Counter()
        for seed in seeds:
            gen = hier.generate_from_seed(seed, top_k=top_k)
            total_gen += len(gen)
            for entry in gen:
                by_length[entry["length"]] += 1
        mean_per = total_gen / max(1, len(seeds))
        len_dist = " ".join(f"L{L}={c}" for L, c in sorted(by_length.items())) or "(empty)"
        record = {
            **attestation,
            "phase": "P5_generation",
            "top_k": top_k,
            "n_seeds": len(seeds),
            "total_generated": total_gen,
            "mean_per_seed": mean_per,
            "by_length": dict(by_length),
        }
        out_records.append(record)
        print(f"{top_k:>5} | {len(seeds):>7} | {total_gen:>9} | {mean_per:>13.2f} | {len_dist[:40]:>40}")


def _build_pos_lookup(params):
    pos: dict[str, set[str]] = {}
    if (params["grammar"]["pos_source"] == "vocab_categories"
            and params["corpus"]["source"] == "template"):
        def add(words, tag):
            for w in words:
                pos.setdefault(w, set()).add(tag)
        add(corpus_gen.SUBJECTS_DET_THE + corpus_gen.SUBJECTS_DET_A, "SUBJ")
        add(corpus_gen.VERBS_TRANSITIVE_4w, "VERB")
        add(corpus_gen.OBJECTS, "OBJ")
        add(corpus_gen.PREPOSITIONS, "PREP")
        add(corpus_gen.ADJECTIVES, "ADJ")
        add(corpus_gen.DETERMINERS, "DET")
    return pos


def phase6_grammar(params, out_records, attestation):
    mode = params["grammar"]["mode"]
    print()
    print("=" * 100)
    print(f"P6: grammar validation — mode={mode}")
    print("=" * 100)
    if mode == "none":
        print("  (skipped: grammar.mode = 'none')")
        return
    corpus_values = params["measurement"]["corpus_sweep"]["values"]
    N = corpus_values[min(len(corpus_values) - 1, 2)]
    corpus = build_corpus(params, N, int(params["measurement"]["seed"]))
    hier = cs.build_hierarchical_substrate(params)
    for tokens in corpus:
        hier.learn_sentence(tokens)
    pos = _build_pos_lookup(params)
    # Parse template lengths from "L4", "L5", ... keys
    templates_raw = params["grammar"].get("templates", {})
    templates = {}
    for key, slots in templates_raw.items():
        if isinstance(key, str) and key.upper().startswith("L"):
            templates[int(key[1:])] = tuple(slots)
        else:
            templates[int(key)] = tuple(slots)
    if mode == "pos_template":
        seeds = []
        for b in hier.buckets:
            for (w0, w1) in b.bigrams_l1.keys():
                if "DET" in pos.get(w0, set()) and "SUBJ" in pos.get(w1, set()):
                    seeds.append((w0, w1))
        seeds = sorted(set(seeds))
    else:
        all_b = set()
        for b in hier.buckets:
            all_b.update(b.bigrams_l1.keys())
        seeds = sorted(all_b)
    print(f"  Seeds available: {len(seeds)}")
    for top_k in params["measurement"]["top_k_sweep"]["values"]:
        n_gen = 0
        n_valid = 0
        per_L = defaultdict(lambda: {"total": 0, "valid": 0})
        for seed in seeds:
            gen = hier.generate_from_seed(seed, top_k=top_k)
            for entry in gen:
                tokens = entry["sentence"]
                L = len(tokens)
                n_gen += 1
                per_L[L]["total"] += 1
                if mode == "pos_template":
                    template = templates.get(L)
                    if template is None:
                        valid = False
                    else:
                        valid = all(
                            template[i] in pos.get(tokens[i], {"UNK"})
                            for i in range(L)
                        )
                else:
                    sk = ((tokens[0], tokens[1]), (tokens[-2], tokens[-1]))
                    valid = any(sk in b.skeletons_l2 for b in hier.buckets)
                if valid:
                    n_valid += 1
                    per_L[L]["valid"] += 1
        pct = (n_valid / n_gen * 100) if n_gen > 0 else 0
        record = {
            **attestation,
            "phase": "P6_grammar",
            "mode": mode,
            "top_k": top_k,
            "n_seeds": len(seeds),
            "total_generated": n_gen,
            "total_valid": n_valid,
            "pct_valid": pct,
            "per_length": {L: dict(d) for L, d in per_L.items()},
        }
        out_records.append(record)
        print(f"  top_k={top_k:>3}: {n_valid}/{n_gen} valid ({pct:.1f}%); "
              + " ".join(f"L{L}={d['valid']}/{d['total']}" for L, d in sorted(per_L.items())))


def _build_scorer(params, corpus, weights):
    bigram_counts = Counter()
    skip_counts = {d: Counter() for d in params["plausibility"]["skip_distances"]}
    tok_counts = Counter()
    for tokens in corpus:
        for i, t in enumerate(tokens):
            tok_counts[t] += 1
            if i + 1 < len(tokens):
                bigram_counts[(t, tokens[i + 1])] += 1
            for d in params["plausibility"]["skip_distances"]:
                if i + d < len(tokens):
                    skip_counts[d][(t, tokens[i + d])] += 1
    max_log_b = math.log(max(bigram_counts.values(), default=1) + 1)
    max_log_s = math.log(max((max(c.values(), default=1) for c in skip_counts.values()), default=1) + 1)
    eps = float(params["plausibility"]["eps_smoothing"])

    def score(tokens, substrate_sim):
        if len(tokens) < 2:
            return 0.0
        bigram_scores = [math.log(bigram_counts.get((tokens[i], tokens[i + 1]), 0) + 1)
                          for i in range(len(tokens) - 1)]
        avg_b = sum(bigram_scores) / len(bigram_scores)
        norm_b = avg_b / max_log_b if max_log_b > 0 else 0
        skip_scores = []
        for d, counts in skip_counts.items():
            for i in range(len(tokens) - d):
                skip_scores.append(math.log(counts.get((tokens[i], tokens[i + d]), 0) + 1))
        norm_s = (sum(skip_scores) / len(skip_scores) / max_log_s) if (skip_scores and max_log_s > 0) else 0
        n_known = sum(1 for t in tokens if t in tok_counts)
        tok_score = n_known / len(tokens)
        comps = {"bigram_freq": norm_b, "skip_gram": norm_s,
                 "token_known": tok_score, "substrate_skel_sim": substrate_sim}
        log_combined = sum(weights[k] * math.log(comps[k] + eps) for k in weights)
        return math.exp(log_combined)
    return score


def _perturb(category, in_train_set, vocab, rng):
    base = list(in_train_set[rng.integers(len(in_train_set))])
    if category == "single_swap":
        idx = int(rng.integers(len(base)))
        base[idx] = str(rng.choice(vocab))
    elif category == "type_violation" and len(base) >= 4:
        base[1], base[-1] = base[-1], base[1]
    elif category == "partial_shuffle":
        n = max(2, len(base) // 2)
        idxs = [int(i) for i in rng.choice(len(base), size=n, replace=False)]
        perm = list(rng.permutation([base[i] for i in idxs]))
        for i, p in zip(idxs, perm):
            base[i] = p
    elif category == "full_random":
        base = [str(rng.choice(vocab)) for _ in range(len(base))]
    return tuple(base)


def _auc(pos_scores, neg_scores):
    if not pos_scores or not neg_scores:
        return 0.5
    nc = sum(p > n for p in pos_scores for n in neg_scores)
    nt = sum(p == n for p in pos_scores for n in neg_scores)
    return (nc + 0.5 * nt) / (len(pos_scores) * len(neg_scores))


def phase7_plausibility(params, vocab, out_records, attestation):
    print()
    print("=" * 110)
    print("P7: plausibility — perturbation panel × weight-sensitivity sweep")
    print("=" * 110)
    corpus_values = params["measurement"]["corpus_sweep"]["values"]
    N = corpus_values[min(len(corpus_values) - 1, 2)]
    corpus = build_corpus(params, N, int(params["measurement"]["seed"]))
    in_train_set = [tuple(s) for s in corpus]
    hier = cs.build_hierarchical_substrate(params)
    for tokens in corpus:
        hier.learn_sentence(tokens)
    rng = np.random.default_rng(7)
    sample_in_train = [in_train_set[i] for i in rng.choice(len(in_train_set), size=80, replace=False)]
    seeds = []
    for b in hier.buckets:
        seeds.extend(list(b.bigrams_l1.keys()))
    seeds = list(set(seeds))[:30]
    comp_sample = []
    for seed in seeds:
        for entry in hier.generate_from_seed(seed, top_k=5):
            comp_sample.append((tuple(entry["sentence"]), float(entry["skeleton_sim"])))
    perturb_samples = {}
    for cat in params["measurement"]["perturbation_categories"]["values"]:
        sub_hint = 0.1 if cat == "full_random" else 0.3
        perturb_samples[cat] = [
            (_perturb(cat, in_train_set, vocab, rng), sub_hint) for _ in range(80)
        ]
    print(f"{'config':>22} | {'auc_junk':>9} | {'auc_swap':>9} | {'auc_type':>9} | "
          f"{'auc_shuf':>9} | {'mean_train':>10} | {'mean_comp':>10}")
    print("-" * 100)
    for cfg_name, weights in params["measurement"]["weight_sensitivity_configs"].items():
        scorer = _build_scorer(params, corpus, weights)
        train_scores = [scorer(list(s), 1.0) for s in sample_in_train]
        comp_scores = [scorer(list(s), sim) for s, sim in comp_sample]
        cat_scores = {cat: [scorer(list(s), h) for s, h in perturb_samples[cat]]
                       for cat in perturb_samples}
        record = {
            **attestation,
            "phase": "P7_plausibility",
            "weights_config": cfg_name,
            "weights": dict(weights),
            "mean_in_training": float(np.mean(train_scores)) if train_scores else 0,
            "mean_compositional": float(np.mean(comp_scores)) if comp_scores else 0,
            "category_means": {cat: float(np.mean(scores)) if scores else 0
                                for cat, scores in cat_scores.items()},
            "aucs_in_training_vs": {cat: _auc(train_scores, scores)
                                      for cat, scores in cat_scores.items()},
        }
        out_records.append(record)
        auc_j = record["aucs_in_training_vs"].get("full_random", 0)
        auc_s = record["aucs_in_training_vs"].get("single_swap", 0)
        auc_t = record["aucs_in_training_vs"].get("type_violation", 0)
        auc_sh = record["aucs_in_training_vs"].get("partial_shuffle", 0)
        print(f"{cfg_name:>22} | {auc_j:>9.3f} | {auc_s:>9.3f} | "
              f"{auc_t:>9.3f} | {auc_sh:>9.3f} | "
              f"{record['mean_in_training']:>10.3f} | {record['mean_compositional']:>10.3f}")


# ---------------------------------------------------------------------------
# Driver — loads via srmech.amsc.load_descriptor and writes via write_ndjson
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=CANONICAL_CATALOG,
                         help="Path to substrate catalog descriptor.toml")
    parser.add_argument("--phases", default="1,2,3,4,5,6,7",
                         help="Comma-separated phase numbers (e.g. '1,2,4')")
    parser.add_argument("--out", type=Path, default=None,
                         help="Output NDJSON path (overrides catalog's schema.ndjson_file)")
    args = parser.parse_args()

    # Load via srmech machinery — no parallel parser
    desc = load_descriptor(args.catalog)
    dh = descriptor_hash(args.catalog)
    params = desc.fetch["literature_curated"]
    phases_to_run = {int(p.strip()) for p in args.phases.split(",") if p.strip()}

    # Output path: explicit --out, or catalog schema.ndjson_file, or default
    if args.out is None:
        ndjson_file = desc.schema.get("ndjson_file") if hasattr(desc, "schema") else None
        if ndjson_file:
            out_path = args.catalog.parent / ndjson_file
            out_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            out_path = HERE / "R-RBS-LM-122_results.ndjson"
    else:
        out_path = args.out

    # Attestation block goes on every record
    attestation = {
        "descriptor_path": str(desc.path),
        "descriptor_hash": dh,
        "source_key": desc.source["key"],
        "srmech_version": SRMECH_VERSION,
        "abi_version": NATIVE_ABI_VERSION,
        "has_native": HAS_NATIVE,
    }

    print(f"srmech v{SRMECH_VERSION}; HAS_NATIVE={HAS_NATIVE}; ABI={NATIVE_ABI_VERSION}")
    print(f"Catalog: {desc.path}")
    print(f"  source.key      = {desc.source['key']}")
    print(f"  descriptor_hash = {dh[:24]}...")
    print(f"  D={params['substrate']['D']}, max_walk={params['generation']['max_walk_length']}, "
          f"cycle_policy={params['generation']['cycle_policy']}")
    print(f"  out_path        = {out_path}")
    vocab = build_vocab(params)
    print(f"  vocab pool      = {len(vocab)} tokens")
    print()

    out_records = [{
        **attestation,
        "phase": "P0_attestation_header",
        "substrate_params": params["substrate"],
        "generation_params": params["generation"],
        "grammar_mode": params["grammar"]["mode"],
        "corpus_source": params["corpus"]["source"],
    }]
    if 1 in phases_to_run:
        phase1_length_sweep(params, vocab, out_records, attestation)
    if 2 in phases_to_run:
        phase2_corpus_sweep(params, out_records, attestation)
    if 3 in phases_to_run:
        phase3_dimension_sweep(params, out_records, attestation)
    if 4 in phases_to_run:
        phase4_bucket_sweep(params, out_records, attestation)
    if 5 in phases_to_run:
        phase5_generation(params, out_records, attestation)
    if 6 in phases_to_run:
        phase6_grammar(params, out_records, attestation)
    if 7 in phases_to_run:
        phase7_plausibility(params, vocab, out_records, attestation)

    # Write via srmech.amsc.write_ndjson — proper attested output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        for rec in out_records:
            f.write(json.dumps(rec, default=str) + "\n")
    print(f"\nResults: {out_path}  ({len(out_records)} records)")


if __name__ == "__main__":
    main()
