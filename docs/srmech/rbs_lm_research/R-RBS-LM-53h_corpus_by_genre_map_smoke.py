"""R-RBS-LM-53h — Project Gutenberg corpus-by-genre form-category map.

Per user direction 2026-05-26 (auto-queue close): build pairwise instrument-
similarity map across 14 corpora spanning genres. Cluster by form-category;
reveal natural form-families.

Corpora (14 total):
  Religious-Abrahamic: Quran-Sale, KJV-OT, KJV-NT
  Religious-Eastern:   Bhagavad Gita, Tao Te Ching, Dhammapada
  Religious-translation-pair: Quran-Rodwell (1861)
  Secular-drama:   Shakespeare
  Secular-novel:   Frankenstein
  Secular-science: Origin of Species
  Secular-philosophy: Plato Republic
  Secular-poetry:  Whitman Leaves of Grass
  Secular-children: Alice in Wonderland
  Secular-detective: Sherlock Holmes

Output: 14x14 pairwise K1 similarity matrix; cluster analysis.
"""

import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

import srmech
from srmech.amsc.laplacian import dense_laplacian, hermitian_eigendecompose
from srmech.amsc.hdc import bundle, similarity, bind, permute
from srmech.signal_processing import mint_vector


HERE = Path(__file__).parent

CORPORA = {
    "quran_sale":   {"path": "/tmp/quran_yusuf_ali.txt",     "family": "religious_abrahamic"},
    "quran_rodwell":{"path": "/tmp/rodwell_quran.txt",        "family": "religious_abrahamic"},
    "kjv_ot":       {"path": "/tmp/kjv_old_testament.txt",   "family": "religious_abrahamic"},
    "kjv_nt":       {"path": "/tmp/kjv_new_testament.txt",   "family": "religious_abrahamic"},
    "bhagavad":     {"path": "/tmp/bhagavad_gita.txt",       "family": "religious_eastern"},
    "tao":          {"path": "/tmp/tao_te_ching.txt",        "family": "religious_eastern"},
    "dhamma":       {"path": "/tmp/dhammapada.txt",          "family": "religious_eastern"},
    "shakespeare":  {"path": "/tmp/shakespeare.txt",         "family": "secular_drama"},
    "origin":       {"path": "/tmp/origin_species.txt",      "family": "secular_science"},
    "frankenstein": {"path": "/tmp/frankenstein.txt",        "family": "secular_novel"},
    "plato":        {"path": "/tmp/plato_republic.txt",      "family": "secular_philosophy"},
    "whitman":      {"path": "/tmp/whitman.txt",             "family": "secular_poetry"},
    "alice":        {"path": "/tmp/alice.txt",               "family": "secular_children"},
    "sherlock":     {"path": "/tmp/sherlock.txt",            "family": "secular_detective"},
}


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


def tokenize_raw(text):
    return [t.lower() for t in re.findall(r"[A-Za-z][A-Za-z0-9'-]*[A-Za-z0-9]|[A-Za-z]", text) if len(t) >= 1]


def tokenize_filtered(text):
    return [t for t in tokenize_raw(text) if t not in STOPWORDS_EN and len(t) >= 2]


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


def build_K1(filt_chunks, K=33, M=21, vocab_size=200, window=5):
    all_t = [t for toks in filt_chunks for t in toks]
    freq = Counter(all_t)
    N = min(vocab_size, len(freq))
    vocab = [t for t, _ in freq.most_common(N)]
    idx_map = {t: i for i, t in enumerate(vocab)}
    edges = Counter()
    for toks in filt_chunks:
        idx = [idx_map[t] for t in toks if t in idx_map]
        for i in range(len(idx)):
            for j in range(i+1, min(i+window, len(idx))):
                a, b = idx[i], idx[j]
                if a == b: continue
                edges[(min(a,b), max(a,b))] += 1
    L = dense_laplacian(N, list(edges.keys()), [float(w) for w in edges.values()])
    ev, evc = hermitian_eigendecompose(L)
    top = list(range(len(ev) - K, len(ev)))
    hvs = []
    for k in reversed(top):
        x = evc[:, k]; ms = x * x
        idx = sorted(range(len(x)), key=lambda i: -ms[i])[:M]
        hvs.append(bundle([mint(vocab[i]) for i in idx]))
    return bundle(hvs), {"vocab_top_10": [(t, freq[t]) for t in vocab[:10]]}


def main():
    print(f"=== R-RBS-LM-53h — Corpus-by-genre form-category map (14 corpora) ===\n")
    print(f"srmech: {srmech.__version__}")
    instruments = {}
    K1_meta = {}
    for key, info in CORPORA.items():
        p = Path(info["path"])
        if not p.exists():
            print(f"  MISSING: {p}")
            continue
        text = strip_gutenberg(p.read_text(encoding="utf-8", errors="replace"))
        chunks = chunk_text(text)
        filt = [tokenize_filtered(c) for c in chunks]
        K1, K1_m = build_K1(filt)
        instruments[key] = K1
        K1_meta[key] = K1_m
        n_tokens = sum(len(t) for t in filt)
        print(f"  {key:<14s} ({info['family']:<22s}): {n_tokens:>7,} tokens; top tokens: {[t for t,_ in K1_m['vocab_top_10'][:5]]}")

    # Build full pairwise similarity matrix
    print(f"\n\n=== Pairwise K1 similarity matrix ({len(instruments)} corpora) ===\n")
    keys = list(instruments.keys())
    matrix = {}
    for k1 in keys:
        matrix[k1] = {}
        for k2 in keys:
            matrix[k1][k2] = round(similarity(instruments[k1], instruments[k2]), 4)

    # Print matrix
    print(f"  {'':<14s} " + " ".join(f"{k[:10]:>10s}" for k in keys))
    for k1 in keys:
        row = [f"{matrix[k1][k2]:>+10.3f}" for k2 in keys]
        print(f"  {k1:<14s} " + " ".join(row))

    # Family analysis
    print(f"\n=== Family-cluster analysis ===\n")
    fam_pairs = {}
    for k1 in keys:
        for k2 in keys:
            if k1 == k2: continue
            f1 = CORPORA[k1]["family"]
            f2 = CORPORA[k2]["family"]
            key = "same" if f1 == f2 else "different"
            fam_pairs.setdefault(key, []).append(matrix[k1][k2])

    # Aggregate by family
    fam_keys = sorted(set(CORPORA[k]["family"] for k in keys))
    fam_avg = {}
    print(f"  Within-family vs cross-family similarity:")
    for f in fam_keys:
        members = [k for k in keys if CORPORA[k]["family"] == f]
        within = []
        for i, m1 in enumerate(members):
            for m2 in members[i+1:]:
                within.append(matrix[m1][m2])
        within_avg = sum(within) / max(len(within), 1) if within else None
        # Cross-family avg
        cross = []
        for m1 in members:
            for k2 in keys:
                if CORPORA[k2]["family"] != f:
                    cross.append(matrix[m1][k2])
        cross_avg = sum(cross) / max(len(cross), 1)
        fam_avg[f] = {"within": within_avg, "cross": cross_avg, "n_within": len(within)}
        if within:
            print(f"    {f:<28s} within (n={len(within)}): {within_avg:+.4f}; cross: {cross_avg:+.4f}; ratio: {within_avg / max(cross_avg, 1e-9):.2f}")
        else:
            print(f"    {f:<28s} (singleton); cross: {cross_avg:+.4f}")

    avg_within = sum(fam_pairs["same"]) / max(len(fam_pairs["same"]), 1)
    avg_cross = sum(fam_pairs["different"]) / max(len(fam_pairs["different"]), 1)
    print(f"\n  Overall within-family avg: {avg_within:+.4f} (n={len(fam_pairs['same'])})")
    print(f"  Overall cross-family avg:  {avg_cross:+.4f} (n={len(fam_pairs['different'])})")
    print(f"  Form-category coherence ratio: {avg_within / max(avg_cross, 1e-9):.2f}")

    # Top-K nearest neighbors per corpus (informal clustering)
    print(f"\n\n=== Top-3 nearest neighbors per corpus ===\n")
    for k in keys:
        sims = [(k2, matrix[k][k2]) for k2 in keys if k2 != k]
        sims.sort(key=lambda x: -x[1])
        f = CORPORA[k]["family"]
        top3 = ", ".join(f"{n}({s:+.3f}; {CORPORA[n]['family'][:11]})" for n, s in sims[:3])
        print(f"  {k:<14s} ({f:<22s}): {top3}")

    # Verdict
    print(f"\n=== Verdict ===")
    if avg_within > avg_cross * 2:
        verdict = "STRONG family-clustering — form-categories cleanly partition the corpus"
    elif avg_within > avg_cross * 1.3:
        verdict = "MODERATE family-clustering — form-categories visible; some cross-family overlap"
    elif avg_within > avg_cross:
        verdict = "WEAK family-clustering — categories detectable but blurry"
    else:
        verdict = "NO clustering — corpus-pairs equally similar regardless of family (form is era-or-language-dominated, not category-dominated)"
    print(f"  {verdict}")

    output = {
        "partition": "R-RBS-LM-53h",
        "srmech_version": srmech.__version__,
        "corpora": {k: {"family": CORPORA[k]["family"]} for k in instruments},
        "pairwise_matrix": matrix,
        "family_avg": fam_avg,
        "overall_within": avg_within,
        "overall_cross": avg_cross,
        "coherence_ratio": avg_within / max(avg_cross, 1e-9),
        "verdict": verdict,
    }
    (HERE / "R-RBS-LM-53h_results.json").write_text(json.dumps(output, indent=2, default=str))
    print(f"\nResults: {HERE / 'R-RBS-LM-53h_results.json'}")


if __name__ == "__main__":
    main()
