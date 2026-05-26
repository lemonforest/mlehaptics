"""R-RBS-LM-54h — Sharper ride: alignment-sim weighting + top-N sweep.

54g showed ride is half-positive: vocab-switching works (vs identity)
but doesn't beat freq-weighted-target baseline (because ride emits
~20k tokens uniformly per probe — frequency dominates).

This partition sharpens the ride emission three ways:
  V1: alignment-sim WEIGHT each emission (currently uniform count=1)
  V2: anchor-mag × alignment-sim WEIGHT (token participation × match quality)
  V3: Reduce top_N_emit (7 → 3 → 1) to concentrate emission on
      best aligned target tokens per rank

Test pairs cover the empirical landscape from 54m / 54n:
  Milton → Shakespeare: rule-dense poetry (54m showed +0.053 r-vs-wgt)
  Frankenstein → Plato: prose→prose (54m showed -0.023)
  KJV → Quran:          same-family abrahamic (54g showed -0.036)
  Whitman → Milton:     free-verse anchor (54m showed -0.245)
  Origin → Frankenstein: prose (54m showed -0.220)

Hypothesis: sharpening should improve ALL pairs by reducing the
frequency-baseline-dilution effect. The biggest improvement should
appear in pairs where alignment signal is real but currently swamped.
"""

import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np

import srmech
from srmech.amsc.laplacian import dense_laplacian, hermitian_eigendecompose
from srmech.amsc.hdc import bundle, similarity
from srmech.signal_processing import mint_vector


HERE = Path(__file__).parent

DOMAINS = {
    "shakespeare":  {"path": "/tmp/shakespeare.txt",                 "label": "Shakespeare"},
    "milton":       {"path": "/tmp/paradise_lost.txt",               "label": "Milton"},
    "whitman":      {"path": "/tmp/whitman.txt",                     "label": "Whitman"},
    "kjv_nt":       {"path": "/tmp/kjv_new_testament.txt",           "label": "KJV-NT"},
    "quran_sale":   {"path": "/tmp/quran_yusuf_ali.txt",             "label": "Quran"},
    "frankenstein": {"path": "/tmp/frankenstein.txt",                "label": "Frankenstein"},
    "plato":        {"path": "/tmp/plato_republic.txt",              "label": "Plato"},
    "origin":       {"path": "/tmp/origin_species.txt",              "label": "Origin"},
}

PAIRS = [
    {"anchor": "milton",       "target": "shakespeare",   "note": "rule-dense poetry (54m positive)"},
    {"anchor": "frankenstein", "target": "plato",         "note": "prose→prose (54m near-zero)"},
    {"anchor": "kjv_nt",       "target": "quran_sale",    "note": "same-fam religious (54g best)"},
    {"anchor": "whitman",      "target": "milton",        "note": "free-verse anchor (54m -0.245)"},
    {"anchor": "origin",       "target": "frankenstein",  "note": "prose Victorian (54m -0.220)"},
]

HOLDOUT_FRACTION = 0.10
N_PROBE_FRAGMENTS = 4
KERNEL_N_EIGVECS = 200
TOP_K_RANKS_PER_TOKEN = 3

STOPWORDS_EN = set("""
the a an and or but if then else of in on at to for with by from as is are
was were be been being have has had having do does did doing done will
would shall should may might can could not no this that these those it its
they them their there here he she we us our you your i me my mine yours
which what who whom whose where when why how all any some none many much
more most less few several each every both either neither so such only also
than just too very much such etc ie eg via vs per pre post sub super
o which thee thou thy ye us our hath shall said say
""".split())


_MINT_CACHE = {}


def mint(token, D=8192):
    if token not in _MINT_CACHE:
        _MINT_CACHE[token] = mint_vector(token, D=D)
    return _MINT_CACHE[token]


MAX_BUNDLE_N = 257


def hierarchical_bundle(vectors):
    n = len(vectors)
    if n == 0: return mint("__empty__")
    if n == 1: return vectors[0]
    if n <= MAX_BUNDLE_N:
        if n % 2 == 0: vectors = vectors + [vectors[0]]
        return bundle(vectors)
    chunk = MAX_BUNDLE_N - 2
    partials = []
    for i in range(0, n, chunk):
        ch = vectors[i:i + chunk]
        if len(ch) % 2 == 0: ch = ch + [ch[0]]
        partials.append(bundle(ch))
    return hierarchical_bundle(partials)


def tokenize_filtered(text):
    raw = re.findall(r"[A-Za-z][A-Za-z0-9'-]*[A-Za-z0-9]|[A-Za-z]", text)
    return [t.lower() for t in raw if t.lower() not in STOPWORDS_EN and len(t) >= 2]


def strip_gutenberg(text):
    s = re.search(r"\*\*\* START OF (THE )?PROJECT GUTENBERG", text)
    e = re.search(r"\*\*\* END OF (THE )?PROJECT GUTENBERG", text)
    if s: text = text[s.end():]
    if e: text = text[:e.start()]
    return text.strip()


def chunk_text(text, n_chunks=64):
    raw = re.split(r"\n\s*\n+", text)
    out, cur, sz = [], [], 0
    target = max(len(text) // n_chunks, 1000)
    for c in raw:
        cur.append(c); sz += len(c)
        if sz >= target:
            out.append("\n".join(cur)); cur = []; sz = 0
    if cur: out.append("\n".join(cur))
    return out


def build_eigvec_table(text, n_eigvecs=KERNEL_N_EIGVECS, M_per_eigvec=21):
    chunks = chunk_text(text)
    filt = [tokenize_filtered(c) for c in chunks]
    all_t = [t for toks in filt for t in toks]
    freq = Counter(all_t)
    N = min(n_eigvecs, len(freq))
    if N < 8: return None, None, None, None
    vocab = [t for t, _ in freq.most_common(N)]
    idx_map = {t: i for i, t in enumerate(vocab)}
    edges = Counter()
    for toks in filt:
        idx = [idx_map[t] for t in toks if t in idx_map]
        for i in range(len(idx)):
            for j in range(i+1, min(i+5, len(idx))):
                a, b = idx[i], idx[j]
                if a == b: continue
                edges[(min(a,b), max(a,b))] += 1
    if not edges: return None, None, None, None
    L = dense_laplacian(N, list(edges.keys()), [float(w) for w in edges.values()])
    ev, evc = hermitian_eigendecompose(L)
    table = []
    for k in range(len(ev) - 1, -1, -1):
        eigvec = evc[:, k]
        mag_sq = eigvec * eigvec
        top_idx = np.argsort(-mag_sq)[:M_per_eigvec]
        top_tokens = [vocab[i] for i in top_idx]
        hv = hierarchical_bundle([mint(t) for t in top_tokens])
        table.append({"rank": len(ev) - 1 - k, "eigval": float(ev[k]),
                       "top_tokens": top_tokens, "hypervector": hv, "eigvec_full": eigvec})
    return table, vocab, idx_map, freq


def find_alignment(table_A, table_B):
    n_A = len(table_A); n_B = len(table_B)
    sim_matrix = np.zeros((n_A, n_B))
    for i in range(n_A):
        for j in range(n_B):
            sim_matrix[i, j] = similarity(table_A[i]["hypervector"], table_B[j]["hypervector"])
    used_B = set()
    alignment = {}
    a_order = sorted(range(n_A), key=lambda i: -sim_matrix[i].max())
    for i in a_order:
        candidates = [(j, sim_matrix[i, j]) for j in range(n_B) if j not in used_B]
        if not candidates: continue
        best_j, best_sim = max(candidates, key=lambda x: x[1])
        used_B.add(best_j)
        alignment[i] = (best_j, float(best_sim))
    return alignment


def split_holdout(text, n_fragments=N_PROBE_FRAGMENTS, holdout_frac=HOLDOUT_FRACTION):
    n = len(text)
    split = int(n * (1 - holdout_frac))
    train = text[:split]
    holdout = text[split:]
    chunks = []
    chunk_size = max(len(holdout) // n_fragments, 4000)
    for i in range(0, len(holdout), chunk_size):
        ch = holdout[i:i + chunk_size]
        if len(ch) >= 1000: chunks.append(ch)
        if len(chunks) >= n_fragments: break
    return train, chunks


def ride_with_weighting(anchor_table, anchor_idx_map, alignment, target_table, anchor_text,
                        top_n_emit, weighting_mode):
    """Variant ride with selectable weighting + top_N.

    weighting_mode in {'uniform', 'align_sim', 'mag_x_sim'}
    """
    anchor_tokens = tokenize_filtered(anchor_text)
    emitted_weights = Counter()
    for atok in anchor_tokens:
        if atok not in anchor_idx_map: continue
        vocab_idx = anchor_idx_map[atok]
        per_rank_mags = []
        for i, row in enumerate(anchor_table):
            mag_sq = float(row["eigvec_full"][vocab_idx] ** 2)
            per_rank_mags.append((i, mag_sq))
        per_rank_mags.sort(key=lambda x: -x[1])
        for table_pos, mag in per_rank_mags[:TOP_K_RANKS_PER_TOKEN]:
            if mag <= 1e-9: break
            if table_pos not in alignment: continue
            target_pos, align_sim = alignment[table_pos]
            if weighting_mode == "uniform":
                w = 1.0
            elif weighting_mode == "align_sim":
                w = max(align_sim, 0.0)
            elif weighting_mode == "mag_x_sim":
                w = max(align_sim, 0.0) * mag
            else:
                w = 1.0
            for t in target_table[target_pos]["top_tokens"][:top_n_emit]:
                emitted_weights[t] += w
    return emitted_weights


def cosine(a, b):
    na = np.linalg.norm(a); nb = np.linalg.norm(b)
    if na == 0 or nb == 0: return 0.0
    return float(np.dot(a, b) / (na * nb))


def eval_ride(emitted, anchor_freq, target_freq):
    union = list(set(emitted.keys()) | set(anchor_freq.keys()) | set(target_freq.keys()))
    e_vec = np.array([emitted.get(t, 0) for t in union], dtype=float)
    a_vec = np.array([anchor_freq.get(t, 0) for t in union], dtype=float)
    t_vec = np.array([target_freq.get(t, 0) for t in union], dtype=float)
    if e_vec.sum() == 0: return 0.0
    return cosine(e_vec, t_vec) - cosine(e_vec, a_vec)


VARIANTS = [
    {"label": "V0 baseline (54g)",        "mode": "uniform",    "top_n": 7},
    {"label": "V1 align-sim weighted",    "mode": "align_sim",  "top_n": 7},
    {"label": "V2 mag × sim weighted",    "mode": "mag_x_sim",  "top_n": 7},
    {"label": "V3 mag × sim, top-3",      "mode": "mag_x_sim",  "top_n": 3},
    {"label": "V4 mag × sim, top-1",      "mode": "mag_x_sim",  "top_n": 1},
    {"label": "V5 uniform top-1",         "mode": "uniform",    "top_n": 1},
]


def main():
    print(f"=== R-RBS-LM-54h — Sharper ride: weighting + top-N sweep ===\n")
    print(f"srmech: {srmech.__version__}")

    random.seed(42); np.random.seed(42)

    needed = set()
    for p in PAIRS:
        needed.add(p["anchor"]); needed.add(p["target"])

    kernels = {}; holdouts = {}
    print(f"\n--- Building kernels (training 90%) ---")
    for key in sorted(needed):
        text = strip_gutenberg(Path(DOMAINS[key]["path"]).read_text(encoding="utf-8", errors="replace"))
        train, probes = split_holdout(text)
        table, vocab, idx_map, freq = build_eigvec_table(train)
        kernels[key] = {"table": table, "vocab": vocab, "idx_map": idx_map, "freq": freq}
        holdouts[key] = probes
        print(f"  {DOMAINS[key]['label']:<18s}: {len(table)} eigvecs; {len(probes)} probes")

    print(f"\n=== Per-pair sweep ===")
    all_results = []
    for pair in PAIRS:
        anchor_key = pair["anchor"]; target_key = pair["target"]
        ak = kernels[anchor_key]; tk = kernels[target_key]
        alignment = find_alignment(ak["table"], tk["table"])
        target_vocab = tk["vocab"]
        weights = np.array([tk["freq"].get(t, 1) for t in target_vocab], dtype=float)
        weights /= weights.sum()

        # Freq-weighted baseline (single computation)
        baseline_scores = []
        for probe_text in holdouts[anchor_key]:
            atoks = tokenize_filtered(probe_text)
            n_emit_typical = len(atoks) * TOP_K_RANKS_PER_TOKEN * 7
            rand_idx = np.random.choice(len(target_vocab), size=min(n_emit_typical, 1000), p=weights, replace=True)
            wp = Counter(target_vocab[i] for i in rand_idx)
            baseline_scores.append(eval_ride(wp, ak["freq"], tk["freq"]))
        baseline_mean = float(np.mean(baseline_scores))

        print(f"\n--- {DOMAINS[anchor_key]['label']} → {DOMAINS[target_key]['label']} ({pair['note']}) ---")
        print(f"  freq-weighted baseline: {baseline_mean:+.3f}")

        pair_results = {"anchor": anchor_key, "target": target_key, "note": pair["note"], "baseline": baseline_mean, "variants": {}}
        for variant in VARIANTS:
            ride_scores = []
            for probe_text in holdouts[anchor_key]:
                emit = ride_with_weighting(ak["table"], ak["idx_map"], alignment, tk["table"], probe_text,
                                            top_n_emit=variant["top_n"], weighting_mode=variant["mode"])
                ride_scores.append(eval_ride(emit, ak["freq"], tk["freq"]))
            ride_mean = float(np.mean(ride_scores))
            delta = ride_mean - baseline_mean
            tag = "✓" if delta > 0.0 else " "
            print(f"  {variant['label']:<24s}: ride={ride_mean:+.3f}; ride−baseline={delta:+.3f} {tag}")
            pair_results["variants"][variant["label"]] = {"ride_mean": ride_mean, "ride_minus_baseline": delta}
        all_results.append(pair_results)

    # Aggregate by variant: which is best ACROSS pairs?
    print(f"\n=== Cross-pair variant ranking ===")
    print(f"  {'variant':<28s} {'avg ride':>9s} {'avg r−b':>9s} {'wins':>7s} {'losses':>7s}")
    variant_summary = {}
    for v in VARIANTS:
        rides = [p["variants"][v["label"]]["ride_mean"] for p in all_results]
        deltas = [p["variants"][v["label"]]["ride_minus_baseline"] for p in all_results]
        wins = sum(1 for d in deltas if d > 0.02)
        losses = sum(1 for d in deltas if d < -0.02)
        variant_summary[v["label"]] = {
            "avg_ride": float(np.mean(rides)),
            "avg_delta": float(np.mean(deltas)),
            "wins": wins, "losses": losses,
        }
        print(f"  {v['label']:<28s} {np.mean(rides):>+9.3f} {np.mean(deltas):>+9.3f} {wins:>7d} {losses:>7d}")

    # Verdict
    print(f"\n=== Verdict ===")
    best_variant = max(variant_summary.items(), key=lambda x: x[1]["avg_delta"])
    print(f"  Best variant: {best_variant[0]}")
    print(f"    avg ride−baseline: {best_variant[1]['avg_delta']:+.3f}; wins={best_variant[1]['wins']}/{len(all_results)}")

    if best_variant[1]["avg_delta"] > 0.05:
        verdict = f"SHARPER RIDE WORKS: {best_variant[0]} avg lift +{best_variant[1]['avg_delta']:.3f}"
    elif best_variant[1]["avg_delta"] > 0.0:
        verdict = f"SHARPER RIDE MARGINAL: best variant {best_variant[0]} avg lift {best_variant[1]['avg_delta']:+.3f}"
    else:
        verdict = f"SHARPER RIDE INSUFFICIENT: even best variant ({best_variant[0]}) below baseline ({best_variant[1]['avg_delta']:+.3f})"
    print(f"  {verdict}")

    out = {
        "partition": "R-RBS-LM-54h",
        "per_pair": all_results,
        "variant_summary": variant_summary,
        "best_variant": best_variant[0],
        "verdict": verdict,
    }
    out_path = HERE / "R-RBS-LM-54h_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
