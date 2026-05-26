"""R-RBS-LM-54i — Compressed-semantic substrates in the DOMAIN anchor + ride pipeline.

Per user (2026-05-26): "if we look at Egyptian glyphs, we can maybe see
how important root words are to the tangible things they describe, in
our translation layer. Or even North American Native languages might
be compressed enough for a real world candidate."

Compressed substrates (where most tokens carry tangible / load-bearing
content; less stopword padding; ritual/formal repetitive structure)
should give SHARPER eigvec tables and sharper DOMAIN anchor signals.

This partition expands the kernel set with compressed-semantic
substrates (mostly Wallis Budge translations of Egyptian and
Babylonian texts, plus already-cached Eastern compressed substrates)
and re-runs:
  1. 54f-style DOMAIN anchor: does fragment routing still hit 100%
     when kernels are more confusable (multiple Budge translations)?
  2. Cross-substrate alignment scores: do compressed substrates give
     SHARPER find-cascade alignments than English-prose-form?
  3. Translator-stability re-test (Finding 49): Budge translates BOTH
     Egyptian and Babylonian — do they cluster as "Budge form" or split
     as "Egyptian vs Babylonian substrate"?

Available compressed-semantic kernels added:
  - Budge Egyptian Literature (PG 15932; 589K)
  - Budge Babylonian Legends of Creation (PG 9914; 129K)
  - Budge Book of the Dead (PG 7145; 91K)
  - Tao Te Ching (English translation; cached from 53e; ~80K)
  - Dhammapada (English translation; cached from 53e; ~88K)

Compared against English-prose baselines:
  - KJV-NT, Quran-Sale (religious_abrahamic)
  - Plato, Frankenstein (secular)
"""

import json
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
    # English-prose baselines (well-tested in 54a-g)
    "kjv_nt":         {"path": "/tmp/kjv_new_testament.txt",   "family": "english_religious_prose",      "substrate_class": "english_prose", "label": "KJV-NT"},
    "quran_sale":     {"path": "/tmp/quran_yusuf_ali.txt",     "family": "english_religious_prose",      "substrate_class": "english_prose", "label": "Quran-YusufAli"},
    "plato":          {"path": "/tmp/plato_republic.txt",      "family": "english_secular_prose",        "substrate_class": "english_prose", "label": "Plato Republic"},
    "frankenstein":   {"path": "/tmp/frankenstein.txt",        "family": "english_secular_prose",        "substrate_class": "english_prose", "label": "Frankenstein"},
    # Compressed-semantic substrates (ancient + Eastern)
    "budge_egypt":    {"path": "/tmp/budge_egyptian_lit.txt",  "family": "compressed_ancient_egyptian",  "substrate_class": "compressed",    "label": "Budge Egyptian Lit"},
    "budge_babylon":  {"path": "/tmp/budge_babylonian.txt",    "family": "compressed_ancient_mesopot",   "substrate_class": "compressed",    "label": "Budge Babylonian"},
    "book_of_dead":   {"path": "/tmp/book_of_dead_budge.txt",  "family": "compressed_egyptian_funerary", "substrate_class": "compressed",    "label": "Book of the Dead"},
    "tao_te_ching":   {"path": "/tmp/tao_te_ching.txt",        "family": "compressed_east_asian",        "substrate_class": "compressed",    "label": "Tao Te Ching"},
    "dhammapada":     {"path": "/tmp/dhammapada.txt",          "family": "compressed_east_asian",        "substrate_class": "compressed",    "label": "Dhammapada"},
}

HOLDOUT_FRACTION = 0.10
N_PROBE_FRAGMENTS = 4
KERNEL_N_EIGVECS = 200
PROBE_N_EIGVECS = 50

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
        eigvec = evc[:, k]
        mag_sq = eigvec * eigvec
        top_idx = np.argsort(-mag_sq)[:M_per_eigvec]
        top_tokens = [vocab[i] for i in top_idx]
        hv = hierarchical_bundle([mint(t) for t in top_tokens])
        table.append({"rank": len(ev) - 1 - k, "eigval": float(ev[k]),
                       "top_tokens": top_tokens, "hypervector": hv})
    return table


def find_alignment_score(probe_table, kernel_table):
    n_p = len(probe_table); n_k = len(kernel_table)
    sims = []
    used_k = set()
    for i in range(n_p):
        candidates = []
        for j in range(n_k):
            if j in used_k: continue
            s = similarity(probe_table[i]["hypervector"], kernel_table[j]["hypervector"])
            candidates.append((j, s))
        if not candidates: break
        best_j, best_sim = max(candidates, key=lambda x: x[1])
        used_k.add(best_j)
        sims.append(best_sim)
    return float(np.mean(sims)) if sims else 0.0


def find_pairwise_alignment(table_A, table_B):
    """Hungarian-style greedy bipartite for kernel-to-kernel similarity."""
    n_A = len(table_A); n_B = len(table_B)
    sim_matrix = np.zeros((n_A, n_B))
    for i in range(n_A):
        for j in range(n_B):
            sim_matrix[i, j] = similarity(table_A[i]["hypervector"], table_B[j]["hypervector"])
    used_B = set()
    sims = []
    a_order = sorted(range(n_A), key=lambda i: -sim_matrix[i].max())
    for i in a_order:
        candidates = [(j, sim_matrix[i, j]) for j in range(n_B) if j not in used_B]
        if not candidates: continue
        best_j, best_sim = max(candidates, key=lambda x: x[1])
        used_B.add(best_j)
        sims.append(best_sim)
    return float(np.mean(sims))


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


def main():
    print(f"=== R-RBS-LM-54i — Compressed-semantic substrates in DOMAIN+ride pipeline ===\n")
    print(f"srmech: {srmech.__version__}")
    print(f"Holdout: {HOLDOUT_FRACTION:.0%}; probes per corpus: {N_PROBE_FRAGMENTS}")
    print(f"N kernels: {len(DOMAINS)} ({sum(1 for d in DOMAINS.values() if d['substrate_class']=='compressed')} compressed + {sum(1 for d in DOMAINS.values() if d['substrate_class']=='english_prose')} english_prose)")

    print(f"\n--- Building kernels (training 90%) ---")
    kernels = {}
    holdouts = {}
    for key, info in DOMAINS.items():
        text = strip_gutenberg(Path(info["path"]).read_text(encoding="utf-8", errors="replace"))
        train, probes = split_holdout(text)
        kernels[key] = build_eigvec_table(train)
        holdouts[key] = probes
        sc = info["substrate_class"]
        print(f"  [{sc:<12s}] {info['label']:<26s}: kernel={len(kernels[key])} eigvecs; {len(probes)} probes (corpus={len(text)//1024}K)")

    # === Test 1: DOMAIN anchor accuracy on expanded kernel set ===
    print(f"\n=== Test 1: DOMAIN anchor routing (re-test of 54f on expanded set) ===")
    n_correct = 0
    n_correct_family = 0
    n_correct_substrate_class = 0
    n_total = 0
    confusion = {}
    score_records = []
    for true_key, probes in holdouts.items():
        for p_idx, probe_text in enumerate(probes):
            probe_table = build_eigvec_table(probe_text, n_eigvecs=PROBE_N_EIGVECS)
            if probe_table is None: continue
            scores = {k: find_alignment_score(probe_table, kt) for k, kt in kernels.items()}
            picked = max(scores.items(), key=lambda x: x[1])[0]
            is_correct_kernel = (picked == true_key)
            is_correct_family = (DOMAINS[picked]["family"] == DOMAINS[true_key]["family"])
            is_correct_substrate_class = (DOMAINS[picked]["substrate_class"] == DOMAINS[true_key]["substrate_class"])
            n_total += 1
            if is_correct_kernel: n_correct += 1
            if is_correct_family: n_correct_family += 1
            if is_correct_substrate_class: n_correct_substrate_class += 1
            confusion.setdefault(true_key, Counter())[picked] += 1
            score_records.append({"true": true_key, "probe": p_idx, "scores": scores, "picked": picked})
            tag = "OK" if is_correct_kernel else ("~F" if is_correct_family else ("~SC" if is_correct_substrate_class else "X"))
            sc = DOMAINS[picked]["substrate_class"]
            print(f"  [{tag:<3s}] {DOMAINS[true_key]['label']:<26s} p{p_idx} → {DOMAINS[picked]['label']:<26s} [{sc:<12s}] top={scores[picked]:+.3f}")

    print(f"\n=== Accuracy ===")
    print(f"  Exact kernel match:       {n_correct}/{n_total} = {n_correct/max(n_total,1):.1%}  (chance = {1/len(DOMAINS):.1%})")
    print(f"  Same-family match:        {n_correct_family}/{n_total} = {n_correct_family/max(n_total,1):.1%}")
    print(f"  Same-substrate-class:     {n_correct_substrate_class}/{n_total} = {n_correct_substrate_class/max(n_total,1):.1%}")

    # === Test 2: Pairwise kernel-to-kernel alignment matrix ===
    print(f"\n=== Test 2: Kernel-to-kernel pairwise alignment matrix ===")
    keys = list(DOMAINS.keys())
    pairwise = {}
    for i, a in enumerate(keys):
        for b in keys[i+1:]:
            pairwise[(a, b)] = find_pairwise_alignment(kernels[a], kernels[b])

    # Display matrix
    print(f"\n  {'A \\\\ B':<14s}", end="")
    for b in keys: print(f"{b[:9]:>10s}", end="")
    print()
    for a in keys:
        print(f"  {a[:14]:<14s}", end="")
        for b in keys:
            if a == b: print(f"{'-':>10s}", end="")
            elif (a, b) in pairwise: print(f"{pairwise[(a,b)]:>+10.3f}", end="")
            else: print(f"{pairwise[(b,a)]:>+10.3f}", end="")
        print()

    # === Test 3: Compressed-vs-prose family analysis ===
    print(f"\n=== Test 3: Substrate-class clustering ===")
    sc_groups = {}  # substrate_class -> [pairwise alignments WITHIN class]
    cross_class = []
    for (a, b), s in pairwise.items():
        sc_a = DOMAINS[a]["substrate_class"]
        sc_b = DOMAINS[b]["substrate_class"]
        if sc_a == sc_b:
            sc_groups.setdefault(sc_a, []).append(s)
        else:
            cross_class.append(s)
    for sc, sims in sc_groups.items():
        print(f"  Within '{sc}' (n={len(sims)} pairs): mean alignment = {np.mean(sims):+.3f}")
    print(f"  Cross substrate-class (n={len(cross_class)} pairs): mean alignment = {np.mean(cross_class):+.3f}")
    within_mean = np.mean([s for sims in sc_groups.values() for s in sims])
    print(f"  Within/cross ratio: {within_mean/max(np.mean(cross_class), 1e-9):.2f}")

    # === Test 4: Translator-stability re-test (Finding 49) ===
    # Wallis Budge translates BOTH Egyptian and Babylonian. Do these cluster
    # as "Budge style" or split as "Egyptian vs Babylonian substrate"?
    print(f"\n=== Test 4: Translator-stability (Wallis Budge re-test of Finding 49) ===")
    budge_pairs = [
        ("budge_egypt", "budge_babylon"),
        ("budge_egypt", "book_of_dead"),
        ("budge_babylon", "book_of_dead"),
    ]
    non_budge_eg_pairs = [
        ("budge_egypt", "tao_te_ching"),
        ("budge_egypt", "dhammapada"),
        ("budge_babylon", "tao_te_ching"),
    ]
    budge_sims = []
    for a, b in budge_pairs:
        s = pairwise.get((a, b), pairwise.get((b, a)))
        budge_sims.append(s)
        print(f"  Budge-Budge   {a} ↔ {b}: {s:+.3f}")
    eg_to_eastern = []
    for a, b in non_budge_eg_pairs:
        s = pairwise.get((a, b), pairwise.get((b, a)))
        eg_to_eastern.append(s)
        print(f"  Budge-Eastern {a} ↔ {b}: {s:+.3f}")
    print(f"  Avg Budge↔Budge:   {np.mean(budge_sims):+.3f}")
    print(f"  Avg Budge↔Eastern: {np.mean(eg_to_eastern):+.3f}")
    ratio = np.mean(budge_sims) / max(np.mean(eg_to_eastern), 1e-9)
    print(f"  Budge-cluster ratio: {ratio:.2f}")
    if ratio > 1.5:
        translator_verdict = f"Budge form dominates substrate (clusters as 'Budge style' — Finding 49 RE-CONFIRMED for ancient corpora)"
    elif ratio > 1.15:
        translator_verdict = f"Budge translator signal present but modest (weakly clusters)"
    else:
        translator_verdict = f"Substrate-content dominates (Budge translations DO split by Egyptian/Babylonian substrate; counter-Finding 49)"
    print(f"  Translator-stability verdict: {translator_verdict}")

    # === Aggregate verdict ===
    print(f"\n=== Verdict ===")
    exact_acc = n_correct / max(n_total, 1)
    if exact_acc >= 0.90:
        anchor_verdict = f"STRONG: DOMAIN anchor still works at {exact_acc:.0%} on expanded {len(DOMAINS)}-kernel set"
    elif exact_acc >= 0.70:
        anchor_verdict = f"MODERATE: DOMAIN anchor works at {exact_acc:.0%}; some confusion within substrate-class"
    elif n_correct_substrate_class / max(n_total, 1) >= 0.85:
        anchor_verdict = f"SUBSTRATE-CLASS only: anchor confuses within-class but separates classes ({n_correct_substrate_class/max(n_total,1):.0%})"
    else:
        anchor_verdict = f"WEAK: DOMAIN anchor degraded to {exact_acc:.0%} with compressed substrates"
    print(f"  DOMAIN anchor: {anchor_verdict}")
    print(f"  Translator stability: {translator_verdict}")

    out = {
        "partition": "R-RBS-LM-54i",
        "n_kernels": len(DOMAINS),
        "exact_acc": exact_acc,
        "family_acc": n_correct_family / max(n_total, 1),
        "substrate_class_acc": n_correct_substrate_class / max(n_total, 1),
        "pairwise_alignment": {f"{a}|{b}": float(s) for (a, b), s in pairwise.items()},
        "within_class_mean": float(np.mean([s for sims in sc_groups.values() for s in sims])),
        "cross_class_mean": float(np.mean(cross_class)),
        "budge_budge_avg": float(np.mean(budge_sims)),
        "budge_eastern_avg": float(np.mean(eg_to_eastern)),
        "budge_ratio": float(ratio),
        "anchor_verdict": anchor_verdict,
        "translator_verdict": translator_verdict,
    }
    out_path = HERE / "R-RBS-LM-54i_results.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
