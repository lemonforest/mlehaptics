"""R-RBS-LM-54a — Rosetta Stone precondition: eigenvalue spectrum comparison.

Per user direction 2026-05-26 (GOLDEN PATH): "cross domain knowledge
finding will mean that all we need to do is bind two different domain
translation kernels to the same translation layer."

The Rosetta Stone hypothesis requires that same-substrate-family corpora
have SIMILAR vocab-independent structural signatures. The Laplacian
eigenvalue spectrum IS that vocab-independent signature — it describes
the GRAPH structure of relationships without caring which tokens are at
which nodes.

54a precondition test:
  - Build Laplacian per corpus (same as 53)
  - Extract eigenvalues only (drop eigenvectors; eigenvalues are
    vocab-independent structural signature)
  - Normalize spectra (relative shape, not absolute scale)
  - Compute pairwise structural-form similarity:
    * Cosine similarity of sorted eigenvalue spectra
    * KS distance on normalized distributions
    * Spectral-coherence ratio (same-family vs cross-family)

If same-family eigenvalue spectra are similar AND cross-family different →
rosetta stone precondition SURVIVES; we can build the shared translation
layer.

Test corpora (already have):
  Same-family Abrahamic: kjv_ot, kjv_nt, quran_sale, quran_rodwell
  Same-family Eastern:   bhagavad, tao, dhamma
  Cross-family secular:  shakespeare, origin, frankenstein, plato
"""

import json
import math
import random
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np

import srmech
from srmech.amsc.laplacian import dense_laplacian, hermitian_eigendecompose


HERE = Path(__file__).parent

CORPORA = {
    "kjv_ot":       {"path": "/tmp/kjv_old_testament.txt", "family": "abrahamic"},
    "kjv_nt":       {"path": "/tmp/kjv_new_testament.txt", "family": "abrahamic"},
    "quran_sale":   {"path": "/tmp/quran_yusuf_ali.txt",   "family": "abrahamic"},
    "quran_rodwell":{"path": "/tmp/rodwell_quran.txt",     "family": "abrahamic"},
    "bhagavad":     {"path": "/tmp/bhagavad_gita.txt",     "family": "eastern"},
    "tao":          {"path": "/tmp/tao_te_ching.txt",      "family": "eastern"},
    "dhamma":       {"path": "/tmp/dhammapada.txt",        "family": "eastern"},
    "shakespeare":  {"path": "/tmp/shakespeare.txt",       "family": "secular_lit"},
    "origin":       {"path": "/tmp/origin_species.txt",    "family": "secular_sci"},
    "frankenstein": {"path": "/tmp/frankenstein.txt",      "family": "secular_lit"},
    "plato":        {"path": "/tmp/plato_republic.txt",    "family": "secular_phi"},
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


def compute_eigvals(filt_chunks, vocab_size=200, window=5):
    """Build Laplacian; extract eigenvalues (no eigenvectors — vocab-independent)."""
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
    eigvals, _ = hermitian_eigendecompose(L)
    return np.array(sorted(eigvals)), vocab[:15]


def normalize_spectrum(spectrum):
    """Normalize eigenvalue spectrum for relative-shape comparison.
    Divide by max so the largest eigenvalue is 1.0 (relative magnitudes preserved)."""
    spectrum = np.array(spectrum, dtype=np.float64)
    spectrum = spectrum[spectrum > 1e-9]  # drop zero eigenvalue (always present)
    if len(spectrum) == 0:
        return spectrum
    return spectrum / spectrum.max()


def cosine_spectrum_similarity(a, b):
    """Cosine similarity of sorted normalized eigenvalue spectra.
    Both must be normalized + same length (sort + take min-length common)."""
    a = normalize_spectrum(a)
    b = normalize_spectrum(b)
    n = min(len(a), len(b))
    if n == 0: return 0.0
    a = a[-n:]  # top-n eigenvalues (most structural)
    b = b[-n:]
    num = np.dot(a, b)
    den = np.linalg.norm(a) * np.linalg.norm(b)
    return float(num / max(den, 1e-9))


def ks_distance(a, b):
    """Kolmogorov-Smirnov distance between normalized eigenvalue distributions.
    Lower = more similar."""
    a = normalize_spectrum(a)
    b = normalize_spectrum(b)
    # Empirical CDFs
    all_x = np.sort(np.concatenate([a, b]))
    cdf_a = np.searchsorted(np.sort(a), all_x, side='right') / len(a)
    cdf_b = np.searchsorted(np.sort(b), all_x, side='right') / len(b)
    return float(np.abs(cdf_a - cdf_b).max())


def main():
    print(f"=== R-RBS-LM-54a — Eigenvalue spectrum comparison (Rosetta Stone precondition) ===\n")
    print(f"srmech: {srmech.__version__}")

    # Build eigenvalue spectrum per corpus
    spectra = {}
    vocab_samples = {}
    for key, info in CORPORA.items():
        p = Path(info["path"])
        if not p.exists():
            print(f"  MISSING: {p}"); continue
        text = strip_gutenberg(p.read_text(encoding="utf-8", errors="replace"))
        chunks = chunk_text(text)
        filt = [tokenize_filtered(c) for c in chunks]
        ev, vocab = compute_eigvals(filt)
        spectra[key] = ev
        vocab_samples[key] = vocab
        n_evs = len(ev)
        # Top 5 and bottom 5 eigvals
        print(f"  {key:<14s} ({info['family']:<14s}): N_eigvals={n_evs}, "
              f"top 3: {ev[-3:].round(1).tolist()}, bottom 3 (nonzero): "
              f"{ev[ev > 1e-9][:3].round(2).tolist() if (ev > 1e-9).any() else 'none'}")

    # ===== Pairwise structural-form similarity matrix =====
    print(f"\n\n=== Pairwise Cosine Similarity of normalized eigenvalue spectra ===\n")
    keys = list(spectra.keys())
    cos_matrix = {}
    for k1 in keys:
        cos_matrix[k1] = {}
        for k2 in keys:
            cos_matrix[k1][k2] = cosine_spectrum_similarity(spectra[k1], spectra[k2])

    print(f"  {'':<14s} " + " ".join(f"{k[:9]:>10s}" for k in keys))
    for k1 in keys:
        cells = " ".join(f"{cos_matrix[k1][k2]:>+10.3f}" for k2 in keys)
        print(f"  {k1:<14s} " + cells)

    # ===== KS distance matrix =====
    print(f"\n\n=== Pairwise KS distance (lower = more similar spectra) ===\n")
    ks_matrix = {}
    for k1 in keys:
        ks_matrix[k1] = {}
        for k2 in keys:
            ks_matrix[k1][k2] = ks_distance(spectra[k1], spectra[k2])

    print(f"  {'':<14s} " + " ".join(f"{k[:9]:>10s}" for k in keys))
    for k1 in keys:
        cells = " ".join(f"{ks_matrix[k1][k2]:>10.3f}" for k2 in keys)
        print(f"  {k1:<14s} " + cells)

    # ===== Family analysis =====
    print(f"\n\n=== Family-level spectral-form coherence ===\n")
    within_cos, cross_cos = [], []
    within_ks, cross_ks = [], []
    for k1 in keys:
        for k2 in keys:
            if k1 == k2: continue
            f1 = CORPORA[k1]["family"]
            f2 = CORPORA[k2]["family"]
            if f1 == f2:
                within_cos.append(cos_matrix[k1][k2])
                within_ks.append(ks_matrix[k1][k2])
            else:
                cross_cos.append(cos_matrix[k1][k2])
                cross_ks.append(ks_matrix[k1][k2])

    print(f"  Within-family eigenvalue cosine avg: {np.mean(within_cos):+.4f} (n={len(within_cos)})")
    print(f"  Cross-family eigenvalue cosine avg:  {np.mean(cross_cos):+.4f} (n={len(cross_cos)})")
    print(f"  Structural-form coherence ratio (cos): {np.mean(within_cos) / max(np.mean(cross_cos), 1e-9):.2f}")
    print()
    print(f"  Within-family KS distance avg:   {np.mean(within_ks):.4f}")
    print(f"  Cross-family KS distance avg:    {np.mean(cross_ks):.4f}")
    print(f"  Structural-form coherence ratio (KS, inverted): "
          f"{np.mean(cross_ks) / max(np.mean(within_ks), 1e-9):.2f}")

    # ===== Compare to R-RBS-LM-53h K1-bundle results =====
    print(f"\n=== Comparison to 53h K1-bundle similarity (vocab-DEPENDENT form) ===")
    print(f"  R-RBS-LM-53h overall coherence ratio (K1 bundle): 1.57")

    cos_ratio = np.mean(within_cos) / max(np.mean(cross_cos), 1e-9)
    ks_ratio = np.mean(cross_ks) / max(np.mean(within_ks), 1e-9)

    # Verdict
    print(f"\n=== Verdict (Rosetta Stone precondition) ===")
    if cos_ratio > 1.5 or ks_ratio > 1.5:
        verdict = "SUPPORTED — same-family eigenvalue spectra are measurably more similar than cross-family; Rosetta Stone precondition holds"
    elif cos_ratio > 1.1 or ks_ratio > 1.1:
        verdict = "WEAKLY SUPPORTED — same-family spectra are slightly more similar; cascade-form has limited structural transferability"
    else:
        verdict = "NOT SUPPORTED — eigenvalue spectra are family-independent; rosetta stone precondition fails (vocabulary IS the form-content)"
    print(f"  {verdict}")

    output = {
        "partition": "R-RBS-LM-54a",
        "srmech_version": srmech.__version__,
        "vocab_samples": vocab_samples,
        "cos_matrix": {k1: {k2: round(v, 4) for k2, v in d.items()} for k1, d in cos_matrix.items()},
        "ks_matrix": {k1: {k2: round(v, 4) for k2, v in d.items()} for k1, d in ks_matrix.items()},
        "within_cos_avg": float(np.mean(within_cos)),
        "cross_cos_avg": float(np.mean(cross_cos)),
        "within_ks_avg": float(np.mean(within_ks)),
        "cross_ks_avg": float(np.mean(cross_ks)),
        "cos_coherence_ratio": round(cos_ratio, 2),
        "ks_coherence_ratio": round(ks_ratio, 2),
        "verdict": verdict,
    }
    (HERE / "R-RBS-LM-54a_results.json").write_text(json.dumps(output, indent=2, default=str))
    print(f"\nResults: {HERE / 'R-RBS-LM-54a_results.json'}")


if __name__ == "__main__":
    main()
