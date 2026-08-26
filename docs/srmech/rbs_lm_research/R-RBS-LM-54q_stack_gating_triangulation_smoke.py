"""R-RBS-LM-54q — Stack 54j G4 gating + 54k triangulation.

Two independent improvements over baseline ride (54g):
  54j G4: sqrt(ride × target_freq) — geometric mean multiplicative blend
  54k T1: anchor→target ∩ anchor→intermediate→target — intersection

The architectural question: do they stack, or are they redundant?

Variants tested:
  D    direct ride (54g baseline)
  D+G4 direct ride + G4 gating (54j G4)
  T1   direct ∩ indirect (54k T1)
  T1+G4 T1 intersection + G4 gating  ← stacked
  T2   direct + indirect (54k T2)
  T2+G4 T2 additive + G4 gating       ← stacked
  T4   direct − meta_baseline (54k T4)
  T4+G4 T4 meta-subtract + G4 gating  ← stacked

Hypothesis: T1+G4 should beat both T1 alone and D+G4 alone if the
benefits are independent. If not, they're redundant (both extract
the same alignment-specific signal).

Test pairs match 54k triples for direct comparability.
"""

import json
import random
import re
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

TRIPLES = [
    {"anchor": "kjv_nt",      "target": "quran_sale",   "intermediate": "bhagavad",    "meta": "frankenstein",  "note": "religious-family via Eastern"},
    {"anchor": "milton",      "target": "shakespeare",  "intermediate": "pope_iliad",  "meta": "frankenstein",  "note": "poetry triangulation"},
    {"anchor": "frankenstein","target": "plato",        "intermediate": "origin",      "meta": "shakespeare",   "note": "prose triangulation"},
    {"anchor": "whitman",     "target": "milton",       "intermediate": "shakespeare", "meta": "frankenstein",  "note": "free-verse via Shake"},
    {"anchor": "origin",      "target": "frankenstein", "intermediate": "plato",       "meta": "shakespeare",   "note": "prose Victorian via philo"},
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
        eigvec = evc[:, k].real
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


def ride_chain(anchor_table, anchor_idx_map, alignment_chain, final_target_table, anchor_text):
    """Ride via a chain of alignments. Returns Counter of target tokens."""
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
            ok = True
            for align in alignment_chain:
                if current_pos not in align:
                    ok = False; break
                current_pos, _ = align[current_pos]
            if not ok: continue
            for t in final_target_table[current_pos]["top_tokens"][:TOP_N_EMITTED_PER_RANK]:
                emitted[t] += 1.0
    return emitted


def intersect_emit(a, b):
    out = Counter()
    for t in set(a) & set(b):
        out[t] = min(a[t], b[t])
    return out


def add_emit(a, b):
    out = Counter(a)
    for t, w in b.items():
        out[t] += w
    return out


def subtract_emit(a, b, alpha=1.0):
    out = Counter()
    for t, w in a.items():
        r = w - alpha * b.get(t, 0)
        if r > 0:
            out[t] = r
    return out


def apply_g4(emit, target_freq):
    """G4 gating: emit_score(t) = sqrt(ride_emit(t) × target_freq(t))."""
    out = Counter()
    for t, w in emit.items():
        tf = target_freq.get(t, 0)
        if tf > 0:
            out[t] = float(np.sqrt(w * tf))
    return out


def cosine(a, b):
    na = np.linalg.norm(a); nb = np.linalg.norm(b)
    if na == 0 or nb == 0: return 0.0
    return float(np.dot(a, b) / (na * nb))


def eval_emission(emit, anchor_freq, target_freq):
    if not emit: return 0.0
    union = list(set(emit.keys()) | set(anchor_freq.keys()) | set(target_freq.keys()))
    e_vec = np.array([emit.get(t, 0) for t in union], dtype=float)
    a_vec = np.array([anchor_freq.get(t, 0) for t in union], dtype=float)
    t_vec = np.array([target_freq.get(t, 0) for t in union], dtype=float)
    if e_vec.sum() == 0: return 0.0
    return cosine(e_vec, t_vec) - cosine(e_vec, a_vec)


def main():
    print(f"=== R-RBS-LM-54q — Stack G4 gating + triangulation ===\n")
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

    print(f"\n=== Per-triple stacked sweep ===")
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

        # Pre-compute ride emissions for all probes
        variants = {"D": [], "D+G4": [], "T1": [], "T1+G4": [], "T2": [], "T2+G4": [], "T4": [], "T4+G4": []}
        for probe_text in holdouts[trip["anchor"]]:
            d_emit = ride_chain(ak["table"], ak["idx_map"], [align_AT], tk["table"], probe_text)
            i_emit = ride_chain(ak["table"], ak["idx_map"], [align_AI, align_IT], tk["table"], probe_text)
            m_emit = ride_chain(ak["table"], ak["idx_map"], [align_AM], mk["table"], probe_text)

            t1_emit = intersect_emit(d_emit, i_emit)
            t2_emit = add_emit(d_emit, i_emit)
            # T4 meta-subtraction: subtract meta_kernel distribution as background
            total_d = sum(d_emit.values())
            total_meta = sum(mk["freq"].values())
            meta_norm = Counter({t: v / total_meta * total_d for t, v in mk["freq"].items()})
            t4_emit = subtract_emit(d_emit, meta_norm, alpha=0.5)

            variants["D"].append(eval_emission(d_emit, ak["freq"], tk["freq"]))
            variants["D+G4"].append(eval_emission(apply_g4(d_emit, tk["freq"]), ak["freq"], tk["freq"]))
            variants["T1"].append(eval_emission(t1_emit, ak["freq"], tk["freq"]))
            variants["T1+G4"].append(eval_emission(apply_g4(t1_emit, tk["freq"]), ak["freq"], tk["freq"]))
            variants["T2"].append(eval_emission(t2_emit, ak["freq"], tk["freq"]))
            variants["T2+G4"].append(eval_emission(apply_g4(t2_emit, tk["freq"]), ak["freq"], tk["freq"]))
            variants["T4"].append(eval_emission(t4_emit, ak["freq"], tk["freq"]))
            variants["T4+G4"].append(eval_emission(apply_g4(t4_emit, tk["freq"]), ak["freq"], tk["freq"]))

        pair_results = {"anchor": trip["anchor"], "target": trip["target"], "note": trip["note"], "baseline": baseline_mean, "variants": {}}
        for vname, scores in variants.items():
            m = float(np.mean(scores))
            d = m - baseline_mean
            tag = "✓" if d > 0.02 else (" " if d > -0.02 else "-")
            print(f"  {vname:<8s}: {m:+.3f}  vs baseline {d:+.3f}  {tag}")
            pair_results["variants"][vname] = {"mean": m, "delta": d}
        all_results.append(pair_results)

    # Cross-pair ranking
    print(f"\n=== Cross-pair variant ranking ===")
    print(f"  {'variant':<10s} {'avg':>9s} {'avg Δ':>9s} {'wins':>7s} {'losses':>7s}")
    summary = {}
    for vname in ["D", "D+G4", "T1", "T1+G4", "T2", "T2+G4", "T4", "T4+G4"]:
        means = [r["variants"][vname]["mean"] for r in all_results]
        deltas = [r["variants"][vname]["delta"] for r in all_results]
        wins = sum(1 for d in deltas if d > 0.02)
        losses = sum(1 for d in deltas if d < -0.02)
        summary[vname] = {"avg_mean": float(np.mean(means)), "avg_delta": float(np.mean(deltas)), "wins": wins, "losses": losses}
        print(f"  {vname:<10s} {np.mean(means):>+9.3f} {np.mean(deltas):>+9.3f} {wins:>7d} {losses:>7d}")

    # Stacking analysis
    print(f"\n=== Stacking analysis (do G4 and triangulation compose?) ===")
    pairs_to_compare = [
        ("D",  "D+G4",  "G4 lift on direct"),
        ("T1", "T1+G4", "G4 lift on T1 intersection"),
        ("T2", "T2+G4", "G4 lift on T2 additive"),
        ("T4", "T4+G4", "G4 lift on T4 meta-sub"),
    ]
    for v1, v2, desc in pairs_to_compare:
        lift = summary[v2]["avg_delta"] - summary[v1]["avg_delta"]
        print(f"  {desc}: {summary[v1]['avg_delta']:+.3f} → {summary[v2]['avg_delta']:+.3f}  (lift {lift:+.3f})")

    best = max(summary.items(), key=lambda x: x[1]["avg_delta"])
    print(f"\n=== Verdict ===")
    print(f"  Best variant: {best[0]}  avg Δ = {best[1]['avg_delta']:+.3f}; wins {best[1]['wins']}/{len(all_results)}")
    if best[1]["avg_delta"] > 0.05:
        verdict = f"STACK WORKS: best variant {best[0]} avg lift +{best[1]['avg_delta']:.3f}"
    elif best[1]["avg_delta"] > 0.0:
        verdict = f"STACK MARGINAL: best variant {best[0]} avg lift +{best[1]['avg_delta']:.3f}"
    else:
        verdict = f"STACK INSUFFICIENT: best ({best[0]}) still below baseline ({best[1]['avg_delta']:+.3f})"
    print(f"  {verdict}")

    out = {
        "partition": "R-RBS-LM-54q",
        "per_pair": all_results,
        "variant_summary": summary,
        "best_variant": best[0],
        "verdict": verdict,
    }
    out_path = HERE / "R-RBS-LM-54q_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
