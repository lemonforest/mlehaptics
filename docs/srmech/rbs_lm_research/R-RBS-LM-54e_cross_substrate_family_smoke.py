"""R-RBS-LM-54e — Cross-substrate-FAMILY test of find-cascade alignment.

Per 54d: within-religious-family alignment works (find→ride gives 3.5/21
overlap; 52% over rank). Cross-family ride is just as good — religious
form-family is broader than substrate. But what happens across
substrate-families entirely (religious ↔ science / philosophy / novel)?

If find-cascade respects substrate-family boundaries:
  - KJV ↔ Quran (within religious): alignment quality A
  - KJV ↔ Bhagavad (within religious): similar quality A
  - KJV ↔ Origin (religious ↔ science): SHOULD BE LOWER
  - KJV ↔ Plato (religious ↔ philosophy): could go either way
  - KJV ↔ Frankenstein (religious ↔ novel): could go either way

If find-cascade is universal form-finder:
  - All alignments similar quality
  - Cascade has no substrate-family boundaries; just per-corpus form

This is the closing test for the 54 Rosetta Stone arc.
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
    "kjv_nt":       {"path": "/tmp/kjv_new_testament.txt", "family": "religious_abrahamic", "label": "KJV-NT"},
    "quran_sale":   {"path": "/tmp/quran_yusuf_ali.txt",   "family": "religious_abrahamic", "label": "Quran-Sale"},
    "bhagavad":     {"path": "/tmp/bhagavad_gita.txt",     "family": "religious_eastern",   "label": "Bhagavad Gita"},
    "origin":       {"path": "/tmp/origin_species.txt",    "family": "secular_science",     "label": "Origin of Species"},
    "plato":        {"path": "/tmp/plato_republic.txt",    "family": "secular_philosophy",  "label": "Plato Republic"},
    "frankenstein": {"path": "/tmp/frankenstein.txt",      "family": "secular_novel",       "label": "Frankenstein"},
}

ANCHOR = "kjv_nt"  # we'll align all others to this


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
        table.append({"rank": len(ev) - 1 - k, "eigval": float(ev[k]),
                       "top_tokens": top_tokens, "hypervector": hv})
    return table


def find_alignment(table_A, table_B):
    n_A = len(table_A); n_B = len(table_B)
    sim_matrix = np.zeros((n_A, n_B))
    for i in range(n_A):
        for j in range(n_B):
            sim_matrix[i, j] = similarity(table_A[i]["hypervector"], table_B[j]["hypervector"])
    used_B = set()
    alignment = {}
    sims = []
    a_order = sorted(range(n_A), key=lambda i: -sim_matrix[i].max())
    for i in a_order:
        candidates = [(j, sim_matrix[i, j]) for j in range(n_B) if j not in used_B]
        if not candidates: continue
        best_j, best_sim = max(candidates, key=lambda x: x[1])
        used_B.add(best_j)
        alignment[table_A[i]["rank"]] = (table_B[best_j]["rank"], best_sim)
        sims.append(best_sim)
    return alignment, sims


def main():
    print(f"=== R-RBS-LM-54e — Cross-substrate-family find-cascade test ===\n")
    print(f"srmech: {srmech.__version__}")
    print(f"Anchor: {DOMAINS[ANCHOR]['label']} ({DOMAINS[ANCHOR]['family']})")

    print(f"\n--- Building eigvec tables ---")
    tables = {}
    for key, info in DOMAINS.items():
        tables[key] = build_eigvec_table(info["path"])
        print(f"  {info['label']:<22s} ({info['family']:<22s}): {len(tables[key])} eigvecs")

    print(f"\n=== Find-cascade alignments: {ANCHOR} ↔ each other ===")
    alignments = {}
    avg_sims = {}
    for key in DOMAINS:
        if key == ANCHOR: continue
        align, sims = find_alignment(tables[ANCHOR], tables[key])
        alignments[key] = align
        avg_sims[key] = float(np.mean(sims))
        print(f"  {ANCHOR} ↔ {key:<14s} ({DOMAINS[key]['family']:<22s}): avg alignment sim = {avg_sims[key]:+.4f}")

    # Sort by family + alignment
    sorted_pairs = sorted(avg_sims.items(), key=lambda x: -x[1])
    print(f"\n=== Ranked by alignment strength (KJV-NT anchor) ===")
    print(f"  {'target':<20s} {'family':<22s} {'avg_sim':>9s}")
    for key, s in sorted_pairs:
        fam = DOMAINS[key]["family"]
        print(f"  {DOMAINS[key]['label']:<20s} {fam:<22s} {s:>+9.4f}")

    # Family-grouped analysis
    print(f"\n=== Family-grouped alignment averages ===")
    by_family = {}
    for key, s in avg_sims.items():
        f = DOMAINS[key]["family"]
        by_family.setdefault(f, []).append((key, s))
    for f, items in sorted(by_family.items()):
        avgs = [s for _, s in items]
        print(f"  {f:<30s} (n={len(items)}): avg sim = {np.mean(avgs):+.4f}; items: {[DOMAINS[k]['label'] for k,_ in items]}")

    # Same-family vs cross-family
    anchor_family = DOMAINS[ANCHOR]["family"]
    same_family_sims = [s for key, s in avg_sims.items() if DOMAINS[key]["family"] == anchor_family]
    cross_family_sims = [s for key, s in avg_sims.items() if DOMAINS[key]["family"] != anchor_family]
    print(f"\n  Same-family (={anchor_family}) avg sim: {np.mean(same_family_sims):+.4f}")
    print(f"  Cross-family avg sim:                      {np.mean(cross_family_sims):+.4f}")
    same_avg = np.mean(same_family_sims)
    cross_avg = np.mean(cross_family_sims)
    print(f"  Same/cross family ratio: {same_avg / max(cross_avg, 1e-9):.2f}")

    # Within religious-superfamily (Abrahamic + Eastern)
    religious_sims = [s for key, s in avg_sims.items() if DOMAINS[key]["family"].startswith("religious")]
    secular_sims = [s for key, s in avg_sims.items() if DOMAINS[key]["family"].startswith("secular")]
    print(f"\n  Religious super-family avg sim: {np.mean(religious_sims):+.4f}")
    print(f"  Secular cross-substrate-family avg sim: {np.mean(secular_sims):+.4f}")
    print(f"  Religious/secular ratio: {np.mean(religious_sims) / max(np.mean(secular_sims), 1e-9):.2f}")

    # Verdict
    print(f"\n=== Verdict ===")
    if np.mean(religious_sims) > np.mean(secular_sims) * 1.5:
        verdict = "SUBSTRATE-FAMILY BOUNDARIES STRONG — find-cascade aligns better within religious family than across to secular"
    elif np.mean(religious_sims) > np.mean(secular_sims) * 1.1:
        verdict = "WEAK substrate-family boundary — find-cascade has slight religious-family preference"
    elif abs(np.mean(religious_sims) - np.mean(secular_sims)) < 0.01:
        verdict = "NO substrate-family boundary — find-cascade is universal form-finder; aligns across all corpora similarly"
    else:
        verdict = "SECULAR alignment stronger than RELIGIOUS — counter-prediction; era/register dominates substrate-family"
    print(f"  {verdict}")

    # Best aligned pair across families
    print(f"\n=== Best individual aligned eigvec pairs by family ===")
    for key in DOMAINS:
        if key == ANCHOR: continue
        align = alignments[key]
        # Sort by sim
        sorted_align = sorted(align.items(), key=lambda x: -x[1][1])[:3]
        print(f"\n  {key} ({DOMAINS[key]['family']}):")
        for a_rank, (b_rank, sim) in sorted_align:
            a_tokens = tables[ANCHOR][a_rank]["top_tokens"][:7]
            b_tokens = tables[key][b_rank]["top_tokens"][:7]
            print(f"    A rank {a_rank} ↔ {key} rank {b_rank} (sim={sim:+.4f})")
            print(f"      A: {a_tokens}")
            print(f"      {key}: {b_tokens}")

    out = {
        "partition": "R-RBS-LM-54e",
        "anchor": DOMAINS[ANCHOR]["label"],
        "avg_alignment_sims": avg_sims,
        "same_family_avg": float(same_avg),
        "cross_family_avg": float(cross_avg),
        "religious_avg": float(np.mean(religious_sims)),
        "secular_avg": float(np.mean(secular_sims)),
        "religious_secular_ratio": float(np.mean(religious_sims) / max(np.mean(secular_sims), 1e-9)),
        "verdict": verdict,
    }
    (HERE / "R-RBS-LM-54e_results.json").write_text(json.dumps(out, indent=2, default=str))
    print(f"\nResults: {HERE / 'R-RBS-LM-54e_results.json'}")


if __name__ == "__main__":
    main()
