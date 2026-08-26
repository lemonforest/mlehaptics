"""R-RBS-LM-54k — Cross-kernel weighting / triangulation.

Per user 2026-05-26: "weight from different kernel is a candidate to
test as well... This looks like the Golden path... bind two different
domain translation kernels to the same translation layer."

Tests multiple kernels active simultaneously in one ride:

  T1 Triangulation (intersection):
       anchor → target  direct path
       anchor → intermediate → target  indirect path
       emit tokens that BOTH paths produce

  T2 Triangulation (additive):
       emit = direct_ride + indirect_ride

  T3 Triangulation (multiplicative):
       emit = direct_ride × indirect_ride
       (agreement-amplifying; nonzero only on shared emissions)

  T4 Modulation (meta-kernel subtraction):
       emit = direct_ride − meta_kernel_baseline
       (where meta_kernel is a third corpus acting as "background form")

  T5 Consensus across N intermediates:
       emit = average of rides through multiple intermediates

This matches the Golden Path architecture (multiple bound kernels +
shared translation layer). The 54i finding was that English-prose-
translator-form dominates; here we test if MULTIPLE kernels acting
in concert can isolate substrate-specific alignment signal.
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
    "pope_iliad":   {"path": "/tmp/iliad_pope.txt",                  "label": "Pope Iliad"},
    "whitman":      {"path": "/tmp/whitman.txt",                     "label": "Whitman"},
    "kjv_nt":       {"path": "/tmp/kjv_new_testament.txt",           "label": "KJV-NT"},
    "quran_sale":   {"path": "/tmp/quran_yusuf_ali.txt",             "label": "Quran"},
    "bhagavad":     {"path": "/tmp/bhagavad_gita.txt",               "label": "Bhagavad"},
    "frankenstein": {"path": "/tmp/frankenstein.txt",                "label": "Frankenstein"},
    "plato":        {"path": "/tmp/plato_republic.txt",              "label": "Plato"},
    "origin":       {"path": "/tmp/origin_species.txt",              "label": "Origin"},
}

# Anchor → target via intermediate, plus a meta-kernel for modulation
TRIPLES = [
    {"anchor": "kjv_nt",      "target": "quran_sale",   "intermediate": "bhagavad",    "meta": "frankenstein",  "note": "religious-family triangulation via Eastern"},
    {"anchor": "milton",      "target": "shakespeare",  "intermediate": "pope_iliad",  "meta": "frankenstein",  "note": "poetry triangulation"},
    {"anchor": "frankenstein","target": "plato",        "intermediate": "origin",      "meta": "shakespeare",   "note": "prose triangulation"},
    {"anchor": "whitman",     "target": "milton",       "intermediate": "shakespeare", "meta": "frankenstein",  "note": "free-verse via shake"},
    {"anchor": "origin",      "target": "frankenstein", "intermediate": "plato",       "meta": "shakespeare",   "note": "prose Victorian via philosophy"},
]

HOLDOUT_FRACTION = 0.10
N_PROBE_FRAGMENTS = 4
KERNEL_N_EIGVECS = 200
TOP_K_RANKS_PER_TOKEN = 3
TOP_N_EMITTED_PER_RANK = 7

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
        eigvec = evc[:, k].real  # explicit real cast (54h ComplexWarning fix)
        mag_sq = eigvec * eigvec
        top_idx = np.argsort(-mag_sq)[:M_per_eigvec]
        top_tokens = [vocab[i] for i in top_idx]
        hv = hierarchical_bundle([mint(t) for t in top_tokens])
        table.append({"rank": len(ev) - 1 - k, "eigval": float(np.real(ev[k])),
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


def ride_through(anchor_table, anchor_idx_map, alignment_chain, target_table_chain, anchor_text):
    """Ride via a chain of (alignment, target_table) pairs.
    chain = [(align_1, table_1), (align_2, table_2), ...]
    First alignment goes anchor→table_1, second goes table_1→table_2, etc.
    Returns Counter of emitted tokens from the FINAL target_table.
    """
    anchor_tokens = tokenize_filtered(anchor_text)
    emitted = Counter()
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
            current_pos = table_pos
            # Walk the alignment chain
            ok = True
            for (align, _table) in alignment_chain:
                if current_pos not in align:
                    ok = False; break
                current_pos, _ = align[current_pos]
            if not ok: continue
            # Emit from final target_table_chain[-1]
            final_table = target_table_chain[-1]
            for t in final_table[current_pos]["top_tokens"][:TOP_N_EMITTED_PER_RANK]:
                emitted[t] += 1.0
    return emitted


def cosine(a, b):
    na = np.linalg.norm(a); nb = np.linalg.norm(b)
    if na == 0 or nb == 0: return 0.0
    return float(np.dot(a, b) / (na * nb))


def eval_emission(emitted, anchor_freq, target_freq):
    if not emitted: return 0.0
    union = list(set(emitted.keys()) | set(anchor_freq.keys()) | set(target_freq.keys()))
    e_vec = np.array([emitted.get(t, 0) for t in union], dtype=float)
    a_vec = np.array([anchor_freq.get(t, 0) for t in union], dtype=float)
    t_vec = np.array([target_freq.get(t, 0) for t in union], dtype=float)
    if e_vec.sum() == 0: return 0.0
    return cosine(e_vec, t_vec) - cosine(e_vec, a_vec)


def intersect_emit(emit_A, emit_B):
    out = Counter()
    for t in set(emit_A) & set(emit_B):
        out[t] = min(emit_A[t], emit_B[t])
    return out


def add_emit(emit_A, emit_B):
    out = Counter(emit_A)
    for t, w in emit_B.items():
        out[t] += w
    return out


def mul_emit(emit_A, emit_B):
    out = Counter()
    for t in set(emit_A) & set(emit_B):
        out[t] = emit_A[t] * emit_B[t]
    return out


def subtract_emit(emit_A, emit_B, alpha=1.0):
    """A − alpha * B; clipped at 0."""
    out = Counter()
    for t, w in emit_A.items():
        residual = w - alpha * emit_B.get(t, 0)
        if residual > 0:
            out[t] = residual
    return out


def main():
    print(f"=== R-RBS-LM-54k — Cross-kernel triangulation ===\n")
    print(f"srmech: {srmech.__version__}")

    random.seed(42); np.random.seed(42)

    needed = set()
    for trip in TRIPLES:
        for role in ["anchor", "target", "intermediate", "meta"]:
            needed.add(trip[role])

    kernels = {}; holdouts = {}
    print(f"\n--- Building kernels (training 90%) ---")
    for key in sorted(needed):
        text = strip_gutenberg(Path(DOMAINS[key]["path"]).read_text(encoding="utf-8", errors="replace"))
        train, probes = split_holdout(text)
        table, vocab, idx_map, freq = build_eigvec_table(train)
        kernels[key] = {"table": table, "vocab": vocab, "idx_map": idx_map, "freq": freq}
        holdouts[key] = probes
        print(f"  {DOMAINS[key]['label']:<18s}: {len(table)} eigvecs; {len(probes)} probes")

    print(f"\n=== Per-triple variant sweep ===")
    all_results = []
    for trip in TRIPLES:
        ak = kernels[trip["anchor"]]
        tk = kernels[trip["target"]]
        ik = kernels[trip["intermediate"]]
        mk = kernels[trip["meta"]]

        align_AT = find_alignment(ak["table"], tk["table"])
        align_AI = find_alignment(ak["table"], ik["table"])
        align_IT = find_alignment(ik["table"], tk["table"])
        align_AM = find_alignment(ak["table"], mk["table"])

        target_vocab = tk["vocab"]
        weights = np.array([tk["freq"].get(t, 1) for t in target_vocab], dtype=float)
        weights /= weights.sum()
        baseline_scores = []
        for probe_text in holdouts[trip["anchor"]]:
            atoks = tokenize_filtered(probe_text)
            n_emit = len(atoks) * TOP_K_RANKS_PER_TOKEN * TOP_N_EMITTED_PER_RANK
            rand_idx = np.random.choice(len(target_vocab), size=min(n_emit, 1000), p=weights, replace=True)
            wp = Counter(target_vocab[i] for i in rand_idx)
            baseline_scores.append(eval_emission(wp, ak["freq"], tk["freq"]))
        baseline_mean = float(np.mean(baseline_scores))

        print(f"\n--- {DOMAINS[trip['anchor']]['label']} → {DOMAINS[trip['target']]['label']}  "
              f"(via {DOMAINS[trip['intermediate']]['label']}; meta={DOMAINS[trip['meta']]['label']}) — {trip['note']} ---")
        print(f"  freq-weighted baseline: {baseline_mean:+.3f}")

        # Compute direct and indirect rides for each probe
        direct_scores = []
        meta_scores = []  # ride to meta (for modulation subtraction)
        t1_scores = []; t2_scores = []; t3_scores = []; t4_scores = []
        for probe_text in holdouts[trip["anchor"]]:
            direct_emit = ride_through(ak["table"], ak["idx_map"], [(align_AT, tk["table"])], [tk["table"]], probe_text)
            indirect_emit = ride_through(ak["table"], ak["idx_map"],
                                          [(align_AI, ik["table"]), (align_IT, tk["table"])],
                                          [ik["table"], tk["table"]], probe_text)
            meta_emit = ride_through(ak["table"], ak["idx_map"], [(align_AM, mk["table"])], [mk["table"]], probe_text)

            direct_scores.append(eval_emission(direct_emit, ak["freq"], tk["freq"]))

            # T1: intersection
            t1_emit = intersect_emit(direct_emit, indirect_emit)
            t1_scores.append(eval_emission(t1_emit, ak["freq"], tk["freq"]))

            # T2: additive
            t2_emit = add_emit(direct_emit, indirect_emit)
            t2_scores.append(eval_emission(t2_emit, ak["freq"], tk["freq"]))

            # T3: multiplicative
            t3_emit = mul_emit(direct_emit, indirect_emit)
            t3_scores.append(eval_emission(t3_emit, ak["freq"], tk["freq"]))

            # T4: modulation — subtract a meta-kernel's distribution from direct
            # Need to translate meta-emit into target-vocab space.
            # Use meta-kernel frequency distribution as the "background"
            # Compute residual = direct_emit − alpha * (meta_freq_normalized * total_direct)
            total_direct = sum(direct_emit.values())
            total_meta = sum(mk["freq"].values())
            meta_norm_emit = Counter({t: v / total_meta * total_direct for t, v in mk["freq"].items()})
            t4_emit = subtract_emit(direct_emit, meta_norm_emit, alpha=0.5)
            t4_scores.append(eval_emission(t4_emit, ak["freq"], tk["freq"]))

        direct_mean = float(np.mean(direct_scores))
        t1_mean = float(np.mean(t1_scores)); t2_mean = float(np.mean(t2_scores))
        t3_mean = float(np.mean(t3_scores)); t4_mean = float(np.mean(t4_scores))
        d_d = direct_mean - baseline_mean
        d1 = t1_mean - baseline_mean; d2 = t2_mean - baseline_mean
        d3 = t3_mean - baseline_mean; d4 = t4_mean - baseline_mean
        print(f"  direct ride (54g):              {direct_mean:+.3f}  vs baseline {d_d:+.3f}")
        print(f"  T1 triangulation intersection:  {t1_mean:+.3f}  vs baseline {d1:+.3f}  {'✓' if d1>0.02 else ' '}")
        print(f"  T2 triangulation additive:      {t2_mean:+.3f}  vs baseline {d2:+.3f}  {'✓' if d2>0.02 else ' '}")
        print(f"  T3 triangulation multiplicative:{t3_mean:+.3f}  vs baseline {d3:+.3f}  {'✓' if d3>0.02 else ' '}")
        print(f"  T4 meta-kernel subtraction:     {t4_mean:+.3f}  vs baseline {d4:+.3f}  {'✓' if d4>0.02 else ' '}")

        all_results.append({
            "anchor": trip["anchor"], "target": trip["target"],
            "intermediate": trip["intermediate"], "meta": trip["meta"],
            "note": trip["note"], "baseline": baseline_mean,
            "direct": direct_mean,
            "T1_intersect": t1_mean, "T2_add": t2_mean,
            "T3_mul": t3_mean, "T4_meta_sub": t4_mean,
            "direct_delta": d_d, "T1_delta": d1, "T2_delta": d2,
            "T3_delta": d3, "T4_delta": d4,
        })

    # Aggregate
    print(f"\n=== Cross-pair variant ranking ===")
    # (variant_label, dict_key_for_mean, dict_key_for_delta)
    variant_spec = [
        ("direct",       "direct",        "direct_delta",   "direct ride (54g)"),
        ("T1_intersect", "T1_intersect",  "T1_delta",       "T1 triangulation ∩"),
        ("T2_add",       "T2_add",        "T2_delta",       "T2 triangulation +"),
        ("T3_mul",       "T3_mul",        "T3_delta",       "T3 triangulation ×"),
        ("T4_meta_sub",  "T4_meta_sub",   "T4_delta",       "T4 meta subtraction"),
    ]
    print(f"  {'variant':<26s} {'avg':>9s} {'avg Δ':>9s} {'wins':>7s} {'losses':>7s}")
    summary = {}
    for (v_key, mean_k, delta_k, lab) in variant_spec:
        deltas = [r[delta_k] for r in all_results]
        means = [r[mean_k] for r in all_results]
        wins = sum(1 for d in deltas if d > 0.02)
        losses = sum(1 for d in deltas if d < -0.02)
        summary[v_key] = {"avg_mean": float(np.mean(means)), "avg_delta": float(np.mean(deltas)), "wins": wins, "losses": losses, "label": lab}
        print(f"  {lab:<26s} {np.mean(means):>+9.3f} {np.mean(deltas):>+9.3f} {wins:>7d} {losses:>7d}")

    best = max(summary.items(), key=lambda x: x[1]["avg_delta"])
    print(f"\n=== Verdict ===")
    print(f"  Best variant: {best[1]['label']}; avg Δ = {best[1]['avg_delta']:+.3f}")
    if best[1]["avg_delta"] > 0.05:
        verdict = f"CROSS-KERNEL HELPS: {best[1]['label']} avg lift +{best[1]['avg_delta']:.3f}; multi-kernel architecture wins"
    elif best[1]["avg_delta"] > 0.0:
        verdict = f"CROSS-KERNEL MARGINAL: best {best[1]['label']} avg lift {best[1]['avg_delta']:+.3f}"
    else:
        verdict = f"CROSS-KERNEL INSUFFICIENT: even best variant below baseline ({best[1]['avg_delta']:+.3f})"
    print(f"  {verdict}")

    out = {
        "partition": "R-RBS-LM-54k",
        "per_triple": all_results,
        "variant_summary": summary,
        "best_variant": best[0],
        "verdict": verdict,
    }
    out_path = HERE / "R-RBS-LM-54k_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
