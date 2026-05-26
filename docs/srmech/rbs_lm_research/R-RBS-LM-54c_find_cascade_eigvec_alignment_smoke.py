"""R-RBS-LM-54c — Find-cascade: cross-domain eigvec alignment by content similarity.

Per user ITN-tube insight 2026-05-26:
  'it's one operation to find ITN, and a totally different cascade to
   ride the itn highway.'

54b failed at rank-matching (ratio 1.21) because eigenvalue rank is not
preserved across corpora. 54c builds the find-cascade explicitly:

  For each eigvec_A[i] in domain A:
    Find the best-matching eigvec_B[j] in domain B by CONTENT similarity
    (top-M token mint-bundle vs top-M token mint-bundle)
  Apply Hungarian-like 1-to-1 assignment for the global best alignment.
  This mapping {i → j} IS the ITN structure between domains.

This is the precondition for the ride-cascade (54d): once the alignment
is built, probe in A finds best A-eigvec, looks up its ALIGNED B-eigvec
(via mapping, not by rank), retrieves B's vocabulary at that aligned
position.

Quality measure: after alignment, the aligned eigvec PAIRS should have
much higher token overlap than rank-paired eigvecs.
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np

import srmech
from srmech.amsc.laplacian import dense_laplacian, hermitian_eigendecompose
from srmech.amsc.hdc import bundle, similarity, bind, permute
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


def build_eigvec_table(corpus_path, M_per_eigvec=21, vocab_size=200, window=5):
    """Build cascade; return per-eigvec dict with top-M tokens + mint-bundle hypervector."""
    text = strip_gutenberg(Path(corpus_path).read_text(encoding="utf-8", errors="replace"))
    chunks = chunk_text(text)
    filt = [tokenize_filtered(c) for c in chunks]
    all_t = [t for toks in filt for t in toks]
    freq = Counter(all_t)
    N = min(vocab_size, len(freq))
    vocab = [t for t, _ in freq.most_common(N)]
    idx_map = {t: i for i, t in enumerate(vocab)}
    edges = Counter()
    for toks in filt:
        idx = [idx_map[t] for t in toks if t in idx_map]
        for i in range(len(idx)):
            for j in range(i+1, min(i+window, len(idx))):
                a, b = idx[i], idx[j]
                if a == b: continue
                edges[(min(a,b), max(a,b))] += 1
    L = dense_laplacian(N, list(edges.keys()), [float(w) for w in edges.values()])
    ev, evc = hermitian_eigendecompose(L)
    table = []
    for k in range(len(ev) - 1, -1, -1):  # descending eigval
        eigvec = evc[:, k]
        mag_sq = eigvec * eigvec
        top_idx = np.argsort(-mag_sq)[:M_per_eigvec]
        top_tokens = [vocab[i] for i in top_idx]
        # Build mint-bundle hypervector for this eigvec's top tokens
        hv = hierarchical_bundle([mint(t) for t in top_tokens])
        table.append({
            "rank": len(ev) - 1 - k,
            "eigval": float(ev[k]),
            "top_tokens": top_tokens,
            "hypervector": hv,
        })
    return table, vocab


def find_alignment(table_A, table_B):
    """For each eigvec in A, find best-matching eigvec in B by HDC similarity.
    Returns list of (rank_A, rank_B, sim, A_tokens, B_tokens)."""
    n_A = len(table_A)
    n_B = len(table_B)
    # Compute full similarity matrix
    sim_matrix = np.zeros((n_A, n_B))
    for i in range(n_A):
        for j in range(n_B):
            sim_matrix[i, j] = similarity(table_A[i]["hypervector"], table_B[j]["hypervector"])

    # Greedy 1-to-1 assignment: for each i, pick the best-matching j that's not yet used
    used_B = set()
    alignment = []
    # Sort A indices by max sim (highest-similarity first; gets best matches)
    a_order = sorted(range(n_A), key=lambda i: -sim_matrix[i].max())
    for i in a_order:
        # Find best unused j
        candidates = [(j, sim_matrix[i, j]) for j in range(n_B) if j not in used_B]
        if not candidates: continue
        best_j, best_sim = max(candidates, key=lambda x: x[1])
        used_B.add(best_j)
        alignment.append({
            "rank_A": table_A[i]["rank"],
            "rank_B": table_B[best_j]["rank"],
            "sim": float(best_sim),
            "A_tokens": table_A[i]["top_tokens"][:7],
            "B_tokens": table_B[best_j]["top_tokens"][:7],
            "eigval_A": table_A[i]["eigval"],
            "eigval_B": table_B[best_j]["eigval"],
        })
    # Sort by rank_A
    alignment.sort(key=lambda x: x["rank_A"])
    return alignment, sim_matrix


def main():
    print(f"=== R-RBS-LM-54c — Find-cascade: eigvec alignment by content similarity ===\n")
    print(f"srmech: {srmech.__version__}")

    print(f"\n--- Building eigvec tables ---")
    table_A, vocab_A = build_eigvec_table(DOMAIN_A["path"])
    table_B, vocab_B = build_eigvec_table(DOMAIN_B["path"])
    table_C, vocab_C = build_eigvec_table(DOMAIN_C["path"])
    print(f"  {DOMAIN_A['label']:<18s}: {len(table_A)} eigvecs")
    print(f"  {DOMAIN_B['label']:<18s}: {len(table_B)} eigvecs (same-family)")
    print(f"  {DOMAIN_C['label']:<18s}: {len(table_C)} eigvecs (cross-family)")

    print(f"\n=== Find-cascade A ↔ B (same-family: {DOMAIN_A['label']} ↔ {DOMAIN_B['label']}) ===")
    alignment_AB, sim_AB = find_alignment(table_A, table_B)
    avg_sim_AB = np.mean([a["sim"] for a in alignment_AB])
    print(f"  Avg alignment similarity: {avg_sim_AB:+.4f}")
    # Top-20 aligned pairs by sim
    aligned_by_sim = sorted(alignment_AB, key=lambda x: -x["sim"])
    print(f"\n  Top-10 best-aligned pairs:")
    for a in aligned_by_sim[:10]:
        print(f"    A rank {a['rank_A']:>3d} ↔ B rank {a['rank_B']:>3d}  (sim={a['sim']:+.4f})")
        print(f"      A: {a['A_tokens']}")
        print(f"      B: {a['B_tokens']}")

    print(f"\n=== Find-cascade A ↔ C (cross-family: {DOMAIN_A['label']} ↔ {DOMAIN_C['label']}) ===")
    alignment_AC, sim_AC = find_alignment(table_A, table_C)
    avg_sim_AC = np.mean([a["sim"] for a in alignment_AC])
    print(f"  Avg alignment similarity: {avg_sim_AC:+.4f}")
    aligned_by_sim_C = sorted(alignment_AC, key=lambda x: -x["sim"])
    print(f"\n  Top-5 best-aligned pairs:")
    for a in aligned_by_sim_C[:5]:
        print(f"    A rank {a['rank_A']:>3d} ↔ C rank {a['rank_B']:>3d}  (sim={a['sim']:+.4f})")
        print(f"      A: {a['A_tokens']}")
        print(f"      C: {a['B_tokens']}")

    print(f"\n=== Rank-correlation between aligned pairs ===")
    # If alignment preserves rank-order, ranks should be similar
    a_ranks = [a["rank_A"] for a in alignment_AB]
    b_ranks = [a["rank_B"] for a in alignment_AB]
    # Compute Spearman-like correlation
    a_arr = np.array(a_ranks); b_arr = np.array(b_ranks)
    corr = np.corrcoef(a_arr, b_arr)[0, 1] if len(a_arr) > 1 else 0
    print(f"  A↔B rank correlation (aligned pairs): {corr:+.4f}")
    a_ranks_AC = [a["rank_A"] for a in alignment_AC]
    b_ranks_AC = [a["rank_B"] for a in alignment_AC]
    corr_AC = np.corrcoef(np.array(a_ranks_AC), np.array(b_ranks_AC))[0, 1] if len(a_ranks_AC) > 1 else 0
    print(f"  A↔C rank correlation (aligned pairs): {corr_AC:+.4f}")

    print(f"\n=== Verdict ===")
    print(f"  Same-family alignment avg sim: {avg_sim_AB:+.4f}")
    print(f"  Cross-family alignment avg sim: {avg_sim_AC:+.4f}")
    print(f"  Same-family vs cross-family ratio: {avg_sim_AB / max(avg_sim_AC, 1e-9):.2f}")
    if avg_sim_AB > avg_sim_AC * 1.5:
        verdict = "FIND-CASCADE SUCCESSFUL — same-family alignment significantly stronger than cross-family; ITN structure identified"
    elif avg_sim_AB > avg_sim_AC * 1.1:
        verdict = "FIND-CASCADE WEAK — alignment slightly favors same-family; partial ITN"
    else:
        verdict = "FIND-CASCADE FAILS — same-family alignment not detectably better than cross-family; eigvecs don't translate by content"
    print(f"\n  {verdict}")

    output = {
        "partition": "R-RBS-LM-54c",
        "domain_A": DOMAIN_A["label"],
        "domain_B_same_family": DOMAIN_B["label"],
        "domain_C_cross_family": DOMAIN_C["label"],
        "avg_alignment_sim_AB_same_family": float(avg_sim_AB),
        "avg_alignment_sim_AC_cross_family": float(avg_sim_AC),
        "ratio_AB_to_AC": float(avg_sim_AB / max(avg_sim_AC, 1e-9)),
        "rank_correlation_AB": float(corr),
        "rank_correlation_AC": float(corr_AC),
        "top_10_aligned_AB": aligned_by_sim[:10],
        "top_5_aligned_AC": aligned_by_sim_C[:5],
        "full_alignment_AB": alignment_AB,
        "verdict": verdict,
    }
    (HERE / "R-RBS-LM-54c_results.json").write_text(json.dumps(output, indent=2, default=str))
    print(f"\nResults: {HERE / 'R-RBS-LM-54c_results.json'}")


if __name__ == "__main__":
    main()
