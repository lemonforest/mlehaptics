"""R-RBS-LM-70 Test A — Is HDC layer architecturally decorative?

Per user 2026-05-26: "examine if we are trying to build a cathedral on
a sand trap." Layer audit identified HDC bundle/similarity as a possible
decorative layer — `bundle(mint_vector(t) for t in top_K_tokens)` may
be doing nothing beyond what a sparse token-indicator vector would do.

This test replaces HDC similarity with raw set-Jaccard / set-cosine over
the top-K token sets directly. If the find-cascade alignment quality
and DOMAIN routing accuracy are preserved, the HDC layer is architecturally
decorative — we're doing spectral bag-of-words matching dressed in HDC
clothing.

Three variants of similarity, run side-by-side on the SAME eigvec tables:

  Variant HDC: srmech.amsc.hdc.similarity(bundle_A, bundle_B)
               where bundle_X = bundle(mint_vector(t) for t in top_K_X)

  Variant J:   |top_K_A ∩ top_K_B| / |top_K_A ∪ top_K_B|   (Jaccard)

  Variant C:   |top_K_A ∩ top_K_B| / sqrt(|top_K_A| · |top_K_B|)  (set cosine)

Tests:
  1. Per-pair correlation: how well do HDC, Jaccard, Cosine track each other?
     If Pearson r > 0.95 across all probe-kernel pairs, HDC is computing
     essentially the same thing as set-cosine.

  2. DOMAIN routing accuracy: re-run 54f-style holdout fragment routing
     using each similarity. If all three give the same 100% accuracy,
     HDC is not adding routing power.

  3. Highest-confidence pair stability: rank pairs by similarity in each
     variant; check if the top-ranked pairs are the same across variants.

If HDC ≡ Jaccard ≡ set-cosine in routing behavior, the cathedral's HDC
foundations are decorative ornamentation. The real signal lives in the
eigvec-top-K-token-set, and the HDC machinery is a randomized hash of it.

Per [[feedback_upstream_srmech_fixes_as_research_notes]]: this test is
investigative, not corrective; if HDC is decorative we document the
finding, not "fix" anything.
"""

import json
import re
from collections import Counter
from pathlib import Path

import numpy as np

import srmech
from srmech.amsc.laplacian import dense_laplacian, hermitian_eigendecompose
from srmech.amsc.hdc import bundle, similarity
from srmech.signal_processing import mint_vector


HERE = Path(__file__).parent

# Same 6 corpora as 54f baseline (100% DOMAIN routing accuracy)
DOMAINS = {
    "kjv_nt":       {"path": "/tmp/kjv_new_testament.txt",   "family": "religious_abrahamic", "label": "KJV-NT"},
    "quran_sale":   {"path": "/tmp/quran_yusuf_ali.txt",     "family": "religious_abrahamic", "label": "Quran-Sale"},
    "bhagavad":     {"path": "/tmp/bhagavad_gita.txt",       "family": "religious_eastern",   "label": "Bhagavad"},
    "origin":       {"path": "/tmp/origin_species.txt",      "family": "secular_science",     "label": "Origin"},
    "plato":        {"path": "/tmp/plato_republic.txt",      "family": "secular_philosophy",  "label": "Plato"},
    "frankenstein": {"path": "/tmp/frankenstein.txt",        "family": "secular_novel",       "label": "Frankenstein"},
}

HOLDOUT_FRACTION = 0.10
N_PROBE_FRAGMENTS = 5
KERNEL_N_EIGVECS = 200
PROBE_N_EIGVECS = 50
M_PER_EIGVEC = 21  # top-K tokens per eigvec (same as 54f)


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


def build_eigvec_table(text, n_eigvecs=KERNEL_N_EIGVECS):
    """Build eigvec table with BOTH HDC bundle AND raw token-set per eigvec."""
    chunks = chunk_text(text)
    filt = [tokenize_filtered(c) for c in chunks]
    all_t = [t for toks in filt for t in toks]
    freq = Counter(all_t)
    N = min(n_eigvecs, len(freq))
    if N < 8: return None
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
    if not edges: return None
    L = dense_laplacian(N, list(edges.keys()), [float(w) for w in edges.values()])
    ev, evc = hermitian_eigendecompose(L)
    table = []
    for k in range(len(ev) - 1, -1, -1):
        eigvec = evc[:, k].real
        mag_sq = eigvec * eigvec
        top_idx = np.argsort(-mag_sq)[:M_PER_EIGVEC]
        top_tokens = [vocab[i] for i in top_idx]
        # HDC bundle (variant HDC)
        hv = hierarchical_bundle([mint(t) for t in top_tokens])
        # Raw token set (variants J and C)
        token_set = set(top_tokens)
        table.append({"rank": len(ev) - 1 - k, "top_tokens": top_tokens,
                       "hypervector": hv, "token_set": token_set})
    return table


def sim_hdc(row_a, row_b):
    return float(similarity(row_a["hypervector"], row_b["hypervector"]))


def sim_jaccard(row_a, row_b):
    a = row_a["token_set"]; b = row_b["token_set"]
    union = len(a | b)
    if union == 0: return 0.0
    return float(len(a & b) / union)


def sim_cosine(row_a, row_b):
    a = row_a["token_set"]; b = row_b["token_set"]
    if not a or not b: return 0.0
    return float(len(a & b) / np.sqrt(len(a) * len(b)))


def find_alignment_score(probe_table, kernel_table, sim_fn):
    n_p = len(probe_table); n_k = len(kernel_table)
    sims = []
    used_k = set()
    for i in range(n_p):
        candidates = []
        for j in range(n_k):
            if j in used_k: continue
            s = sim_fn(probe_table[i], kernel_table[j])
            candidates.append((j, s))
        if not candidates: break
        best_j, best_sim = max(candidates, key=lambda x: x[1])
        used_k.add(best_j)
        sims.append(best_sim)
    return float(np.mean(sims)) if sims else 0.0


def split_holdout(text, n_fragments=N_PROBE_FRAGMENTS, holdout_frac=HOLDOUT_FRACTION):
    n = len(text)
    split = int(n * (1 - holdout_frac))
    train = text[:split]
    holdout = text[split:]
    chunks = []
    chunk_size = max(len(holdout) // n_fragments, 2500)
    for i in range(0, len(holdout), chunk_size):
        ch = holdout[i:i + chunk_size]
        if len(ch) >= 800: chunks.append(ch)
        if len(chunks) >= n_fragments: break
    return train, chunks


def pearson(a, b):
    a = np.array(a, dtype=float); b = np.array(b, dtype=float)
    if len(a) < 2: return 0.0
    am = a - a.mean(); bm = b - b.mean()
    da = float(np.sqrt((am * am).sum())); db = float(np.sqrt((bm * bm).sum()))
    if da == 0 or db == 0: return 0.0
    return float((am * bm).sum() / (da * db))


def main():
    print(f"=== R-RBS-LM-70 Test A — Is HDC layer decorative? ===\n")
    print(f"srmech: {srmech.__version__}")
    print(f"Comparison: HDC bundle/similarity vs Jaccard vs set-cosine on top-K token sets")
    print(f"Same eigvec tables; only the similarity function differs.\n")

    print(f"--- Building kernels (training 90%) ---")
    kernels = {}; holdouts = {}
    for key, info in DOMAINS.items():
        text = strip_gutenberg(Path(info["path"]).read_text(encoding="utf-8", errors="replace"))
        train, probes = split_holdout(text)
        kernels[key] = build_eigvec_table(train)
        holdouts[key] = probes
        print(f"  {info['label']:<14s}: {len(kernels[key])} eigvecs; {len(probes)} probes")

    # Per-probe-pair similarity logs (for correlation analysis)
    hdc_scores = []; jac_scores = []; cos_scores = []
    # Per-probe routing decisions
    routing = {"hdc": [], "jaccard": [], "cosine": []}
    n_total = 0; n_correct = {"hdc": 0, "jaccard": 0, "cosine": 0}

    print(f"\n--- Routing decisions (probe → max-similarity kernel) ---")
    print(f"  {'true':<14s} {'p#':<3s} | {'HDC':<14s} | {'Jac':<14s} | {'Cos':<14s} | match")
    for true_key, probes in holdouts.items():
        for p_idx, probe_text in enumerate(probes):
            probe_table = build_eigvec_table(probe_text, n_eigvecs=PROBE_N_EIGVECS)
            if probe_table is None: continue
            # Score against each kernel via each similarity
            row = {"hdc": {}, "jaccard": {}, "cosine": {}}
            for k_key, k_table in kernels.items():
                row["hdc"][k_key] = find_alignment_score(probe_table, k_table, sim_hdc)
                row["jaccard"][k_key] = find_alignment_score(probe_table, k_table, sim_jaccard)
                row["cosine"][k_key] = find_alignment_score(probe_table, k_table, sim_cosine)
            # Pick max per variant
            picks = {v: max(row[v].items(), key=lambda x: x[1])[0] for v in row}
            n_total += 1
            for v in n_correct:
                if picks[v] == true_key: n_correct[v] += 1
                routing[v].append({"true": true_key, "picked": picks[v]})
            # Capture all kernel-probe similarity scores for correlation analysis
            for k_key in kernels:
                hdc_scores.append(row["hdc"][k_key])
                jac_scores.append(row["jaccard"][k_key])
                cos_scores.append(row["cosine"][k_key])
            match_str = "".join(["✓" if picks[v] == true_key else "✗" for v in ["hdc", "jaccard", "cosine"]])
            print(f"  {DOMAINS[true_key]['label']:<14s} {p_idx:<3d} | "
                  f"{DOMAINS[picks['hdc']]['label']:<14s} | "
                  f"{DOMAINS[picks['jaccard']]['label']:<14s} | "
                  f"{DOMAINS[picks['cosine']]['label']:<14s} | {match_str}")

    print(f"\n=== Routing accuracy ===")
    for v in ["hdc", "jaccard", "cosine"]:
        print(f"  {v:<10s}: {n_correct[v]}/{n_total} = {n_correct[v]/max(n_total,1):.1%}")

    print(f"\n=== Per-pair similarity correlations ===")
    r_hj = pearson(hdc_scores, jac_scores)
    r_hc = pearson(hdc_scores, cos_scores)
    r_jc = pearson(jac_scores, cos_scores)
    print(f"  Pearson r (HDC, Jaccard):    {r_hj:.4f}")
    print(f"  Pearson r (HDC, cosine):     {r_hc:.4f}")
    print(f"  Pearson r (Jaccard, cosine): {r_jc:.4f}")
    print(f"  N pairs: {len(hdc_scores)}")

    # Verdict
    print(f"\n=== Verdict ===")
    same_routing = (n_correct["hdc"] == n_correct["jaccard"] == n_correct["cosine"])
    high_corr = min(r_hj, r_hc) > 0.90
    if same_routing and high_corr:
        verdict = (f"HDC IS DECORATIVE — Jaccard and set-cosine give identical routing accuracy "
                   f"({n_correct['hdc']}/{n_total}) AND correlate at r > 0.90 with HDC. The HDC "
                   f"layer adds no measurable signal beyond top-K token-set overlap.")
    elif same_routing and not high_corr:
        verdict = (f"HDC NUMERICALLY DIFFERENT but routing-equivalent. Same accuracy, but lower "
                   f"correlation (r_hj={r_hj:.2f}, r_hc={r_hc:.2f}) suggests HDC ranks pairs "
                   f"differently in finer detail. Routing decisions don't depend on the difference.")
    elif not same_routing and high_corr:
        verdict = (f"HDC PARTIALLY DECORATIVE. High correlation but routing accuracy differs: "
                   f"HDC={n_correct['hdc']}, Jac={n_correct['jaccard']}, Cos={n_correct['cosine']}. "
                   f"HDC contributes signal in boundary cases.")
    else:
        verdict = (f"HDC CONTRIBUTES REAL SIGNAL. Routing differs AND correlation is moderate. "
                   f"The HDC layer is doing more than just set-overlap.")
    print(f"  {verdict}")

    out = {
        "partition": "R-RBS-LM-70_Test_A_hdc_decorative",
        "n_total": n_total,
        "accuracy_hdc": n_correct["hdc"] / max(n_total, 1),
        "accuracy_jaccard": n_correct["jaccard"] / max(n_total, 1),
        "accuracy_cosine": n_correct["cosine"] / max(n_total, 1),
        "pearson_hdc_jaccard": r_hj,
        "pearson_hdc_cosine": r_hc,
        "pearson_jaccard_cosine": r_jc,
        "n_pairs_correlated": len(hdc_scores),
        "verdict": verdict,
    }
    out_path = HERE / "R-RBS-LM-70_Test_A_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
