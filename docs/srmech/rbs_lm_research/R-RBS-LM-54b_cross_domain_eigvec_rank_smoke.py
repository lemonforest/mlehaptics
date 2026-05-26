"""R-RBS-LM-54b — Cross-domain probe via eigenvector-rank matching.

Per 54a precondition: same-family eigenvalue spectra are measurably
similar. Test whether eigenvector RANK CORRESPONDENCE carries cross-
domain semantic alignment.

Mechanism:
  1. Probe in domain A's vocabulary (e.g., a KJV phrase)
  2. Encode probe via domain A's mints (Class A content-mint per token)
  3. Compute probe alignment with each domain A eigenvector
  4. Identify rank-K eigenvector that maximally aligns
  5. Look at domain B's RANK-K eigenvector (same rank position)
  6. Extract domain B's TOP TOKENS at that rank
  7. These tokens are the "cross-domain rendering" of the probe's
     structural meaning

If this works: cross-domain retrieval emerges from rank correspondence
of eigenvectors across same-family corpora.

If it doesn't: rank-matching is too crude; need alternative mapping
(e.g., eigvec content-similarity, not rank).
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


# Test pair: same-family (Abrahamic). KJV-NT ↔ Quran-Sale.
DOMAIN_A = {"key": "kjv_nt",     "path": "/tmp/kjv_new_testament.txt", "label": "KJV-NT"}
DOMAIN_B = {"key": "quran_sale", "path": "/tmp/quran_yusuf_ali.txt",   "label": "Quran-Sale"}

# Also test cross-family as control: KJV-NT ↔ Bhagavad
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


def build_eigenvectors(corpus_path, vocab_size=200, window=5):
    """Build cascade + return per-eigenvector (token, weight) lists ranked by eigenvalue."""
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
    # Eigenvalues from hermitian_eigendecompose come sorted ascending; we want descending (largest first = highest structural rank)
    # eigenvectors are columns of evc; column k corresponds to eigenvalue ev[k]
    ranked = []
    for k in range(len(ev) - 1, -1, -1):  # descending
        eigvec = evc[:, k]
        eigval = ev[k]
        # Top tokens by squared magnitude (preserves signed structure)
        mag_sq = eigvec * eigvec
        top_idx = np.argsort(-mag_sq)[:30]
        top_tokens = [(vocab[i], float(eigvec[i])) for i in top_idx]
        ranked.append({"eigval": float(eigval), "eigvec": eigvec, "top_tokens": top_tokens})
    return ranked, vocab


def encode_phrase_mint_bundle(phrase):
    """Encode probe phrase as mint+bundle bundle (vocab-aware)."""
    toks = tokenize_filtered(phrase)
    if not toks: return mint("__empty__")
    return hierarchical_bundle([mint(t) for t in toks])


def best_aligned_rank(probe_phrase, eigvectors_ranked, vocab):
    """Find the eigvec rank whose token-bundle best matches probe.
    Use mint-bundle similarity in the actual HDC space.
    """
    probe_bundle = encode_phrase_mint_bundle(probe_phrase)
    sims = []
    for rank, ev in enumerate(eigvectors_ranked):
        # Bundle the top-M tokens of this eigvec
        top_M_tokens = [t for t, _ in ev["top_tokens"][:21]]
        if not top_M_tokens:
            sims.append(0.0)
            continue
        eigvec_bundle = hierarchical_bundle([mint(t) for t in top_M_tokens])
        sims.append(similarity(probe_bundle, eigvec_bundle))
    best_rank = int(np.argmax(sims))
    return best_rank, sims[best_rank], sims


def main():
    print(f"=== R-RBS-LM-54b — Cross-domain probe via eigvec-rank matching ===\n")
    print(f"srmech: {srmech.__version__}")

    # Build eigenvector-ranked tables for 3 corpora
    print(f"\n--- Building eigvec-ranked tables ---")
    A_ranked, A_vocab = build_eigenvectors(DOMAIN_A["path"])
    B_ranked, B_vocab = build_eigenvectors(DOMAIN_B["path"])
    C_ranked, C_vocab = build_eigenvectors(DOMAIN_C["path"])
    print(f"  {DOMAIN_A['label']:<18s} (N=200): top tokens at rank 0: {[t for t,_ in A_ranked[0]['top_tokens'][:5]]}")
    print(f"  {DOMAIN_B['label']:<18s} (N=200): top tokens at rank 0: {[t for t,_ in B_ranked[0]['top_tokens'][:5]]}")
    print(f"  {DOMAIN_C['label']:<18s} (N=200): top tokens at rank 0: {[t for t,_ in C_ranked[0]['top_tokens'][:5]]}")

    # Test phrases — sourced from KJV-NT canonical content (will use as domain A probe)
    test_phrases = [
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

    print(f"\n\n=== Cross-domain probe matrix: probe in {DOMAIN_A['label']}, retrieve in target domain ===\n")

    for probe in test_phrases:
        print(f"\n--- Probe: '{probe}' ---")
        # Find best-aligned rank in domain A (KJV-NT)
        a_rank, a_sim, a_all_sims = best_aligned_rank(probe, A_ranked, A_vocab)
        print(f"  Domain A ({DOMAIN_A['label']}) best-aligned rank: {a_rank} "
              f"(sim={a_sim:+.4f}; eigval={A_ranked[a_rank]['eigval']:.1f})")
        print(f"    A rank-{a_rank} top tokens: {[t for t,_ in A_ranked[a_rank]['top_tokens'][:7]]}")

        # Same rank in domain B (Quran-Sale) — same-family target
        b_top = [t for t, _ in B_ranked[a_rank]['top_tokens'][:7]]
        print(f"    B (same-family, {DOMAIN_B['label']}) rank-{a_rank} top tokens: {b_top}")
        b_eigval = B_ranked[a_rank]['eigval']
        print(f"      eigval B at rank {a_rank}: {b_eigval:.1f}")

        # Same rank in domain C (Bhagavad) — cross-family control
        c_top = [t for t, _ in C_ranked[a_rank]['top_tokens'][:7]]
        print(f"    C (cross-family, {DOMAIN_C['label']}) rank-{a_rank} top tokens: {c_top}")
        c_eigval = C_ranked[a_rank]['eigval']
        print(f"      eigval C at rank {a_rank}: {c_eigval:.1f}")

    # Aggregate analysis
    print(f"\n\n=== Aggregate: probe → rank in A → look up same rank in B and C ===\n")
    a_to_b_token_overlap = []
    a_to_c_token_overlap = []
    rank_distrib = []

    for probe in test_phrases:
        a_rank, _, _ = best_aligned_rank(probe, A_ranked, A_vocab)
        rank_distrib.append(a_rank)
        # Token overlap: how many of B's top-21 at rank-K share with A's top-21 at rank-K?
        a_tokens = set(t for t, _ in A_ranked[a_rank]['top_tokens'][:21])
        b_tokens = set(t for t, _ in B_ranked[a_rank]['top_tokens'][:21])
        c_tokens = set(t for t, _ in C_ranked[a_rank]['top_tokens'][:21])
        a_to_b_token_overlap.append(len(a_tokens & b_tokens))
        a_to_c_token_overlap.append(len(a_tokens & c_tokens))

    avg_overlap_AB = np.mean(a_to_b_token_overlap)
    avg_overlap_AC = np.mean(a_to_c_token_overlap)
    print(f"  Avg token-overlap A∩B at probe's best rank (same-family): {avg_overlap_AB:.1f} / 21")
    print(f"  Avg token-overlap A∩C at probe's best rank (cross-family): {avg_overlap_AC:.1f} / 21")
    print(f"  Rank distribution across probes: {rank_distrib}")

    if avg_overlap_AB > avg_overlap_AC * 1.5:
        verdict = "RANK-MATCHING WORKS — same-family token overlap at matched rank significantly higher than cross-family"
    elif avg_overlap_AB > avg_overlap_AC:
        verdict = "WEAK RANK-MATCHING — same-family token overlap slightly higher; partial cross-domain alignment"
    else:
        verdict = "RANK-MATCHING FAILS — rank-correspondence does NOT carry semantic alignment; need alternative mapping"
    print(f"\n  Verdict: {verdict}")

    # Save
    output = {
        "partition": "R-RBS-LM-54b",
        "domain_A": DOMAIN_A["label"],
        "domain_B_same_family": DOMAIN_B["label"],
        "domain_C_cross_family": DOMAIN_C["label"],
        "avg_token_overlap_A_B_same_family": float(avg_overlap_AB),
        "avg_token_overlap_A_C_cross_family": float(avg_overlap_AC),
        "rank_distribution": rank_distrib,
        "verdict": verdict,
    }
    (HERE / "R-RBS-LM-54b_results.json").write_text(json.dumps(output, indent=2, default=str))
    print(f"\nResults: {HERE / 'R-RBS-LM-54b_results.json'}")


if __name__ == "__main__":
    main()
