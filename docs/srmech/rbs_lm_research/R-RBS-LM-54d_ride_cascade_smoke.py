"""R-RBS-LM-54d — Ride-cascade: cross-domain probe via 54c's alignment.

Per user ITN-tube insight: find-cascade (54c) and ride-cascade (54d)
are different operations. 54c established the explicit eigvec alignment
between domains (1.14 same-family vs cross-family ratio).

54d uses 54c's alignment to translate:
  1. Probe in domain A
  2. Find best-aligned A eigvec (via probe→eigvec mint-bundle similarity)
  3. Look up that A-eigvec's ALIGNED B-eigvec (via the alignment dict from
     54c, NOT same rank)
  4. Retrieve B's top tokens at the aligned eigvec
  5. These tokens are the domain-B-vocab translation of the probe form

Comparison: ride via 54c-alignment vs ride via same-rank (54b's broken
method). Same-family token overlap should improve.
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

DOMAIN_A = {"key": "kjv_nt",     "path": "/tmp/kjv_new_testament.txt", "label": "KJV-NT"}
DOMAIN_B = {"key": "quran_sale", "path": "/tmp/quran_yusuf_ali.txt",   "label": "Quran-Sale"}
DOMAIN_C = {"key": "bhagavad",   "path": "/tmp/bhagavad_gita.txt",     "label": "Bhagavad Gita"}


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


def build_eigvec_table(corpus_path, M_per_eigvec=21):
    text = strip_gutenberg(Path(corpus_path).read_text(encoding="utf-8", errors="replace"))
    chunks = chunk_text(text)
    filt = [tokenize_filtered(c) for c in chunks]
    all_t = [t for toks in filt for t in toks]
    freq = Counter(all_t)
    N = min(200, len(freq))
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
    L = dense_laplacian(N, list(edges.keys()), [float(w) for w in edges.values()])
    ev, evc = hermitian_eigendecompose(L)
    table = []
    for k in range(len(ev) - 1, -1, -1):
        eigvec = evc[:, k]
        mag_sq = eigvec * eigvec
        top_idx = np.argsort(-mag_sq)[:M_per_eigvec]
        top_tokens = [vocab[i] for i in top_idx]
        hv = hierarchical_bundle([mint(t) for t in top_tokens])
        table.append({
            "rank": len(ev) - 1 - k,
            "eigval": float(ev[k]),
            "top_tokens": top_tokens,
            "hypervector": hv,
        })
    return table


def find_alignment(table_A, table_B):
    """54c's find-cascade — returns dict mapping rank_A → rank_B."""
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
        best_j, _ = max(candidates, key=lambda x: x[1])
        used_B.add(best_j)
        alignment[table_A[i]["rank"]] = table_B[best_j]["rank"]
    return alignment


def encode_probe(phrase):
    toks = tokenize_filtered(phrase)
    if not toks: return mint("__empty__")
    return hierarchical_bundle([mint(t) for t in toks])


def best_aligned_rank(probe_phrase, table):
    probe = encode_probe(probe_phrase)
    sims = [similarity(probe, ev["hypervector"]) for ev in table]
    return int(np.argmax(sims))


def main():
    print(f"=== R-RBS-LM-54d — Ride-cascade via 54c alignment ===\n")
    print(f"srmech: {srmech.__version__}")

    print(f"--- Building eigvec tables ---")
    A = build_eigvec_table(DOMAIN_A["path"])
    B = build_eigvec_table(DOMAIN_B["path"])
    C = build_eigvec_table(DOMAIN_C["path"])
    print(f"  A: {DOMAIN_A['label']}  B: {DOMAIN_B['label']} (same-family)  C: {DOMAIN_C['label']} (cross-family)")

    print(f"\n--- Building find-cascade alignment (54c) ---")
    alignment_AB = find_alignment(A, B)
    alignment_AC = find_alignment(A, C)
    print(f"  A→B alignment built ({len(alignment_AB)} pairs)")
    print(f"  A→C alignment built ({len(alignment_AC)} pairs)")

    probes = [
        "Jesus Christ Lord savior",
        "Sermon on the Mount blessed",
        "kingdom of heaven parable",
        "love thy neighbor",
        "twelve apostles disciples",
        "Holy Spirit Pentecost",
        "Last Supper bread wine",
        "Gospel of Matthew",
        "Paul epistle letter",
        "good Samaritan parable",
    ]

    print(f"\n\n=== 54d Ride-cascade: probe → A-rank → ALIGNED B-rank (via 54c) vs RANK B-rank (54b broken) ===\n")
    by_alignment = []
    by_rank = []
    rng_same = []
    by_alignment_C = []
    for probe in probes:
        a_rank = best_aligned_rank(probe, A)
        A_tokens = set(A[a_rank]["top_tokens"][:21])

        # RIDE via 54c alignment
        b_rank_aligned = alignment_AB.get(a_rank, a_rank)
        B_aligned_tokens = set(B[b_rank_aligned]["top_tokens"][:21])
        overlap_aligned = len(A_tokens & B_aligned_tokens)

        # RIDE via same-rank (54b broken method, for comparison)
        b_rank_same = a_rank
        B_same_rank_tokens = set(B[b_rank_same]["top_tokens"][:21])
        overlap_same_rank = len(A_tokens & B_same_rank_tokens)

        # Cross-family ride via 54c
        c_rank_aligned = alignment_AC.get(a_rank, a_rank)
        C_aligned_tokens = set(C[c_rank_aligned]["top_tokens"][:21])
        overlap_AC_aligned = len(A_tokens & C_aligned_tokens)

        by_alignment.append(overlap_aligned)
        by_rank.append(overlap_same_rank)
        by_alignment_C.append(overlap_AC_aligned)

        print(f"\n  Probe: '{probe}'")
        print(f"    A best rank: {a_rank}")
        print(f"    A tokens: {A[a_rank]['top_tokens'][:7]}")
        print(f"    B ALIGNED rank (via 54c): {b_rank_aligned} — tokens: {B[b_rank_aligned]['top_tokens'][:7]}")
        print(f"      A∩B (aligned) = {overlap_aligned}/21")
        print(f"    B SAME rank (54b method):  {b_rank_same} — tokens: {B[b_rank_same]['top_tokens'][:7]}")
        print(f"      A∩B (same rank) = {overlap_same_rank}/21")
        print(f"    C ALIGNED rank (cross-family): {c_rank_aligned} — tokens: {C[c_rank_aligned]['top_tokens'][:7]}")
        print(f"      A∩C (aligned) = {overlap_AC_aligned}/21")

    print(f"\n\n=== Summary ===\n")
    print(f"  Avg A∩B token overlap via 54c alignment (same-family): {np.mean(by_alignment):.2f} / 21")
    print(f"  Avg A∩B token overlap via 54b same-rank   (same-family): {np.mean(by_rank):.2f} / 21")
    print(f"  Avg A∩C token overlap via 54c alignment (cross-family): {np.mean(by_alignment_C):.2f} / 21")
    print()
    print(f"  Alignment-vs-rank improvement: {np.mean(by_alignment) - np.mean(by_rank):+.2f} tokens")
    print(f"  Same-family advantage over cross-family: {np.mean(by_alignment) - np.mean(by_alignment_C):+.2f} tokens")

    if np.mean(by_alignment) > np.mean(by_rank) * 1.5:
        verdict_a = "FIND→RIDE works — alignment-based retrieval significantly outperforms rank-based"
    elif np.mean(by_alignment) > np.mean(by_rank) + 0.5:
        verdict_a = "FIND→RIDE moderately improves over rank-matching"
    else:
        verdict_a = "FIND→RIDE not materially better than rank — alignment isn't tightening the ride"

    if np.mean(by_alignment) > np.mean(by_alignment_C) * 1.5:
        verdict_b = "Same-family translation cleanly beats cross-family"
    elif np.mean(by_alignment) > np.mean(by_alignment_C):
        verdict_b = "Same-family slight edge over cross-family"
    else:
        verdict_b = "Cross-family ride is as good as same-family (form-family is broader than substrate)"

    print(f"\n  Verdict (alignment vs rank): {verdict_a}")
    print(f"  Verdict (same vs cross family): {verdict_b}")

    out = {
        "partition": "R-RBS-LM-54d",
        "avg_AB_via_alignment": float(np.mean(by_alignment)),
        "avg_AB_via_rank": float(np.mean(by_rank)),
        "avg_AC_via_alignment": float(np.mean(by_alignment_C)),
        "alignment_vs_rank_improvement": float(np.mean(by_alignment) - np.mean(by_rank)),
        "same_vs_cross_family_advantage": float(np.mean(by_alignment) - np.mean(by_alignment_C)),
        "verdict_alignment_vs_rank": verdict_a,
        "verdict_same_vs_cross": verdict_b,
    }
    (HERE / "R-RBS-LM-54d_results.json").write_text(json.dumps(out, indent=2, default=str))
    print(f"\nResults: {HERE / 'R-RBS-LM-54d_results.json'}")


if __name__ == "__main__":
    main()
