"""R-RBS-LM-52a-v2 — Path E corrected: mint_vector per token + bundle.

Iteration on R-RBS-LM-52a' after diagnosis:
  - 52a/52a' used encode_loe_content (content-fingerprint; orthogonal-at-noise
    for different-but-overlapping content). NOT similarity-preserving.
  - 52a-v2 uses srmech.signal_processing.mint_vector per token + bundle (Class M).
    Verified similarity-preserving: bundle(A,B,C) vs bundle(A,B,C,D,E) = +0.61.

Pipeline (every step routes through srmech catalog):

  corpus → word tokens
         → co-occurrence Laplacian (srmech.amsc.laplacian)
         → hermitian_eigendecompose (Class L)
         → for each top-K eigenvector: top-M tokens by squared magnitude
         → mint_vector per token (Class A content-mint, named)
         → bundle per-eigenvector (Class M; odd-count for parity discipline)
         → bundle of all eigenvector hypervectors (Class M outer; odd-count)
         → cascade instrument

  probe → word tokens
        → mint_vector per token
        → bundle (Class M)
        → similarity vs instrument (Class M read)
"""

import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

import srmech
from srmech.amsc.laplacian import dense_laplacian, hermitian_eigendecompose
from srmech.amsc.hdc import bundle, similarity
from srmech.signal_processing import mint_vector


HERE = Path(__file__).parent
REPO_ROOT = HERE.parent.parent.parent

NOTEBOOK_PATHS = [
    REPO_ROOT / "docs/srmech/srmech_research_notebook.md",
    REPO_ROOT / "docs/antikythera-maths/mfo_spectral_research_notebook.md",
]


STOPWORDS = set("""
the a an and or but if then else of in on at to for with by from as is are
was were be been being have has had having do does did doing done will
would shall should may might can could not no this that these those it its
they them their there here he she we us our you your i me my mine yours
which what who whom whose where when why how all any some none many much
more most less few several each every both either neither so such only also
than just too very much such etc i.e. e.g. cf via vs vs. per pre post sub
super inter intra extra meta non non- co- de- re- un- mis-
""".split())


# srmech.signal_processing.mint_vector is deterministic per (name, D); cache it.
_MINT_CACHE = {}


def mint(token, D=8192):
    if token not in _MINT_CACHE:
        _MINT_CACHE[token] = mint_vector(token, D=D)
    return _MINT_CACHE[token]


def tokenize_text(text):
    raw = re.findall(r'[A-Za-z][A-Za-z0-9_-]*[A-Za-z0-9]|[A-Za-z]', text)
    out = []
    for tok in raw:
        low = tok.lower()
        if low in STOPWORDS or len(low) < 2:
            continue
        out.append(low)
    return out


def build_cooccurrence_edges(tokens_per_section, vocab_idx, window=5):
    edge_count = Counter()
    for tokens in tokens_per_section:
        indexed = [vocab_idx[t] for t in tokens if t in vocab_idx]
        n = len(indexed)
        for i in range(n):
            for j in range(i + 1, min(i + window, n)):
                a, b = indexed[i], indexed[j]
                if a == b:
                    continue
                edge_count[(min(a, b), max(a, b))] += 1
    return edge_count


def encode_eigenvector_via_mint_bundle(eigvec, vocab, top_m=21, D=8192):
    """Per-token mint + bundle. top_m must be odd for bundle parity.

    Class L (squared-magnitude selection; signed structure via sq-norm)
    + Class A (mint_vector per token) + Class M (bundle).
    """
    assert top_m % 2 == 1, "top_m must be odd per bundle parity discipline"
    mag_sq = eigvec * eigvec
    top_idx = sorted(range(len(eigvec)), key=lambda i: -mag_sq[i])[:top_m]
    token_vectors = [mint(vocab[i], D=D) for i in top_idx]
    return bundle(token_vectors)


def encode_probe_via_mint_bundle(text, D=8192):
    """Probe encoding: tokenize, mint each, bundle.

    Must produce odd token count for bundle parity; if even, drop the
    last token deterministically.
    """
    toks = tokenize_text(text)
    if not toks:
        return mint("__empty__", D=D)
    # Ensure odd count via Class K-style truncation (drop last if even)
    if len(toks) % 2 == 0:
        toks = toks[:-1] if len(toks) > 1 else toks + toks  # if exactly 1, double (still odd? no — 2 even)
    if len(toks) % 2 == 0:
        toks = toks + [toks[0]]  # pad with first token to make odd (3 from 2)
    return bundle([mint(t, D=D) for t in toks])


def main():
    print(f"=== R-RBS-LM-52a-v2 Path E (corrected): mint_vector + bundle ===\n")
    print(f"srmech: {srmech.__version__}")

    # ---- 1-4. Same as 52a': load + tokenize + vocab + edges ----
    notebooks = []
    for p in NOTEBOOK_PATHS:
        if not p.exists():
            print(f"  MISSING: {p}")
            continue
        text = p.read_text()
        notebooks.append((p.name, text))
        print(f"  loaded {p.name}: {len(text):,} chars")

    sections = []
    for fname, text in notebooks:
        parts = re.split(r'\n#{2,3}\s+', text)
        for part in parts:
            if len(part) > 100:
                sections.append((fname, part))
    print(f"Sections: {len(sections)}")

    tokens_per_section = []
    all_tokens = []
    for fname, sect in sections:
        toks = tokenize_text(sect)
        tokens_per_section.append(toks)
        all_tokens.extend(toks)
    n_total = len(all_tokens)
    n_unique = len(set(all_tokens))
    print(f"Tokens: {n_total:,} total; {n_unique:,} unique")

    freq = Counter(all_tokens)
    N = min(200, len(freq))
    vocab = [t for t, _ in freq.most_common(N)]
    vocab_idx = {t: i for i, t in enumerate(vocab)}
    coverage = sum(freq[t] for t in vocab) / max(n_total, 1)
    print(f"Vocab: top-{N} (coverage {100*coverage:.1f}%)")

    edge_count = build_cooccurrence_edges(tokens_per_section, vocab_idx, window=5)
    edges = list(edge_count.keys())
    weights = [float(w) for w in edge_count.values()]
    L = dense_laplacian(N, edges, weights)
    print(f"Edges: {len(edges):,}; Laplacian: {L.shape}")

    # ---- 5. Eigendecompose ----
    print(f"\nEigendecomposing...")
    eigvals, eigvecs = hermitian_eigendecompose(L)

    # ---- 6. Encode top-K eigenvectors via mint_vector + bundle ----
    K = 33  # odd for outer-bundle parity
    M_per_eigenvec = 21  # odd for inner-bundle parity
    top_k_indices = list(range(len(eigvals) - K, len(eigvals)))
    eigenvector_hvs = []
    print(f"Encoding top-{K} eigvecs × top-{M_per_eigenvec} tokens via mint + bundle...")
    for rank, k_idx in enumerate(reversed(top_k_indices)):
        hv = encode_eigenvector_via_mint_bundle(
            eigvecs[:, k_idx], vocab, top_m=M_per_eigenvec)
        eigenvector_hvs.append(hv)

    # Outer bundle into cascade instrument
    instrument = bundle(eigenvector_hvs)
    print(f"Instrument: {len(instrument)} bytes (D=8192)")

    # ---- 7. Read-mode smoke ----
    print(f"\n=== Read-mode smoke ===")

    notebook_probes = [
        "two substrate framework",
        "class l spine spectral",
        "born hopf readout",
        "operation primary cyclic algebra",
        "geometry primary continuous hopf",
        "epistemic ceiling form not substrate",
        "B/H/N readout projection",
        "fractal recursion substrate",
        "Hopf fibration division algebra",
        "Class N rational anchor",
        "weak coupling truncate instrument",
        "metric field ontology",
        "cascade match form claim",
        "cross substrate matching",
        "Reading-D scale ladder",
        "Kaluza Klein photon off diagonal metric",
        "combination principle dissociation",
        "L-system seed grammar",
        "biology cascade encoding",
        "AMSC attestation provenance",
    ]

    negative_probes = [
        "chocolate ice cream flavor",
        "professional soccer match score",
        "kitchen pencil sharpener metal",
        "tropical rainforest humidity bright",
        "vintage automobile manufacturing",
        "ocean coral reef colorful",
        "morning coffee croissant breakfast",
    ]

    # Baseline: random pairs of notebook-paragraph encodings (using same path)
    paragraphs = []
    for fname, sect in sections:
        para_pool = re.split(r'\n\n+', sect)
        for p in para_pool:
            if 50 < len(p) < 500:
                paragraphs.append(p)
    print(f"Baseline paragraph pool: {len(paragraphs)}")

    rng = random.Random(42)
    baseline_sims = []
    for _ in range(100):
        a, b = rng.sample(paragraphs, 2)
        fa = encode_probe_via_mint_bundle(a)
        fb = encode_probe_via_mint_bundle(b)
        baseline_sims.append(similarity(fa, fb))

    bl_mean = sum(baseline_sims) / len(baseline_sims)
    bl_max = max(baseline_sims)
    bl_min = min(baseline_sims)
    bl_std = (sum((s - bl_mean) ** 2 for s in baseline_sims) / len(baseline_sims)) ** 0.5
    print(f"\nBaseline (random paragraph pairs, n=100):")
    print(f"  mean: {bl_mean:+.4f}; std: {bl_std:.4f}; max: {bl_max:+.4f}; min: {bl_min:+.4f}")

    print(f"\n=== Notebook-domain probes vs instrument ===")
    notebook_results = []
    for p in notebook_probes:
        fp = encode_probe_via_mint_bundle(p)
        s = similarity(fp, instrument)
        z = (s - bl_mean) / max(bl_std, 1e-9)
        above_max = s > bl_max
        flag = "***" if above_max else "**" if z > 2 else "*" if z > 1 else ""
        notebook_results.append({"probe": p, "similarity": s, "z_score": z,
                                  "above_baseline_max": above_max})
        print(f"  {p:<42s} sim={s:+.4f}  z={z:+.2f}  {flag}")

    print(f"\n=== Negative-control probes ===")
    neg_results = []
    for p in negative_probes:
        fp = encode_probe_via_mint_bundle(p)
        s = similarity(fp, instrument)
        z = (s - bl_mean) / max(bl_std, 1e-9)
        above_max = s > bl_max
        flag = "***" if above_max else "**" if z > 2 else "*" if z > 1 else ""
        neg_results.append({"probe": p, "similarity": s, "z_score": z,
                             "above_baseline_max": above_max})
        print(f"  {p:<42s} sim={s:+.4f}  z={z:+.2f}  {flag}")

    # Verdict
    n_above_max_nb = sum(1 for r in notebook_results if r["above_baseline_max"])
    n_above_2sig_nb = sum(1 for r in notebook_results if r["z_score"] > 2)
    n_above_1sig_nb = sum(1 for r in notebook_results if r["z_score"] > 1)
    n_above_max_neg = sum(1 for r in neg_results if r["above_baseline_max"])
    n_above_2sig_neg = sum(1 for r in neg_results if r["z_score"] > 2)

    print(f"\n=== Verdict ===")
    print(f"  Notebook probes above baseline_max: {n_above_max_nb}/{len(notebook_results)}")
    print(f"  Notebook probes z > 2: {n_above_2sig_nb}/{len(notebook_results)}")
    print(f"  Notebook probes z > 1: {n_above_1sig_nb}/{len(notebook_results)}")
    print(f"  Negative-control above max: {n_above_max_neg}/{len(neg_results)}")
    print(f"  Negative-control z > 2: {n_above_2sig_neg}/{len(neg_results)}")

    if n_above_max_nb >= len(notebook_results) // 2 and n_above_max_neg == 0:
        verdict = "STRONG signal — methodology works; corrected encoding pathway"
    elif n_above_2sig_nb >= len(notebook_results) // 3 and n_above_max_neg == 0:
        verdict = "SIGNAL — methodology shows positive signal"
    elif n_above_1sig_nb >= len(notebook_results) // 2:
        verdict = "WEAK signal — partial; refine parameters or kernel"
    elif n_above_max_neg >= n_above_max_nb:
        verdict = "NO discrimination — methodology still doesn't distinguish coherent from incoherent"
    else:
        verdict = "NO signal — encoding pathway still wrong or signal beneath noise floor"

    print(f"\n  Verdict: {verdict}")

    output = {
        "partition": "R-RBS-LM-52a-v2",
        "phase": "A-v2 — mint_vector + bundle (corrected encoding)",
        "srmech_version": srmech.__version__,
        "n_tokens": n_total,
        "n_unique": n_unique,
        "vocab_size": N,
        "vocab_top_10": [(t, freq[t]) for t in vocab[:10]],
        "n_edges": len(edges),
        "K": K, "M_per_eigenvec": M_per_eigenvec,
        "instrument_bytes": len(instrument),
        "baseline_mean": bl_mean, "baseline_std": bl_std,
        "baseline_max": bl_max, "baseline_min": bl_min,
        "notebook_probes": notebook_results,
        "negative_probes": neg_results,
        "n_above_max_notebook": n_above_max_nb,
        "n_above_max_negative": n_above_max_neg,
        "verdict": verdict,
    }
    out_path = HERE / "R-RBS-LM-52a_v2_results.json"
    out_path.write_text(json.dumps(output, indent=2, default=str))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
