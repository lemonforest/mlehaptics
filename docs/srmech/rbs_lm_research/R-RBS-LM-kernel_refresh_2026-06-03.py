"""Kernel refresh (2026-06-03) — rebuild the srmech + MFO notebook kernels.

User direction: "need updated kernels for srmech and mfo research notebooks.
they carry the knowledge of falsification."

The prior multi-kernel build (R-RBS-LM-52b) ran on srmech 0.4.2 against a far
smaller notebook state (116k-ngram corpus). Since then the two notebooks grew
to carry the whole F167->F338 arc INCLUDING the falsification record — every
correction, null finding, and triality-trimmed over-reach. The Class-L
co-occurrence-Laplacian eigenspectrum IS the srmech-native storage signature
(F172), so rebuilding the kernel on the current notebooks is how that
falsification knowledge enters the kernel.

This refresh:
  * builds a kernel PER NOTEBOOK (srmech alone, mfo alone) + the combined kernel
    — matching "kernels for srmech AND mfo";
  * uses the proven R-RBS-LM-52b method, srmech-native + torch-free:
      K1 (presence) = Class-L dense_laplacian -> hermitian_eigendecompose,
                      top-K eigvecs -> top-M tokens -> Class-A mint -> Class-M bundle
      K3 (sequence) = position-bound n-gram Class-M bind+permute -> bundle
  * SAVES the kernel instruments (.bin) + meta (.json) as artifacts;
  * runs a self-similarity smoke (kernel vs framework probes vs negatives) to
    confirm each kernel carries signal;
  * reports growth vs the prior 0.4.2 build (the accreted knowledge);
  * does NOT clobber R-RBS-LM-52b_results.json (the historical claim stands).

Run on the freshly-verified rc21 venv:
  /tmp/verify_srmech_v070rc21/bin/python \
    docs/srmech/rbs_lm_research/R-RBS-LM-kernel_refresh_2026-06-03.py
"""

import json
import random
import re
from collections import Counter
from pathlib import Path

import numpy as np

import srmech
from srmech.amsc.laplacian import dense_laplacian, hermitian_eigendecompose
from srmech.amsc.hdc import bundle, similarity, bind, permute
from srmech.signal_processing import mint_vector

HERE = Path(__file__).parent
REPO_ROOT = HERE.parent.parent.parent
OUTDIR = HERE / "kernels_refresh_2026-06-03"
OUTDIR.mkdir(exist_ok=True)

NOTEBOOKS = {
    "srmech": REPO_ROOT / "docs/srmech/srmech_research_notebook.md",
    "mfo": REPO_ROOT / "docs/antikythera-maths/mfo_spectral_research_notebook.md",
}

D = 8192

STOPWORDS = set("""
the a an and or but if then else of in on at to for with by from as is are
was were be been being have has had having do does did doing done will
would shall should may might can could not no this that these those it its
they them their there here he she we us our you your i me my mine yours
which what who whom whose where when why how all any some none many much
more most less few several each every both either neither so such only also
than just too very much such etc i.e. e.g. cf via vs per pre post sub
super inter intra extra meta non co de re un mis
""".split())

_MINT_CACHE = {}


def mint(token):
    if token not in _MINT_CACHE:
        _MINT_CACHE[token] = mint_vector(token, D=D)
    return _MINT_CACHE[token]


MAX_BUNDLE_N = 257


def hierarchical_bundle(vectors):
    n = len(vectors)
    if n == 0:
        return mint("__empty_bundle__")
    if n == 1:
        return vectors[0]
    if n <= MAX_BUNDLE_N:
        if n % 2 == 0:
            vectors = vectors + [vectors[0]]
        return bundle(vectors)
    chunk = MAX_BUNDLE_N - 2
    partials = []
    for i in range(0, n, chunk):
        ch = vectors[i:i + chunk]
        if len(ch) % 2 == 0:
            ch = ch + [ch[0]]
        partials.append(bundle(ch))
    return hierarchical_bundle(partials)


def tokenize_text(text):
    raw = re.findall(r'[A-Za-z][A-Za-z0-9_-]*[A-Za-z0-9]|[A-Za-z]', text)
    out = []
    for tok in raw:
        low = tok.lower()
        if low in STOPWORDS or len(low) < 2:
            continue
        out.append(low)
    return out


def sections_of(text):
    secs = []
    for part in re.split(r'\n#{2,3}\s+', text):
        if len(part) > 100:
            secs.append(tokenize_text(part))
    return secs


# ---- K1 presence (Class L eigendecomp + Class M mint+bundle) ----
def build_K1_presence(tokens_per_section, K=33, M_per_eigenvec=21,
                      vocab_size=200, window=5):
    all_tokens = []
    for toks in tokens_per_section:
        all_tokens.extend(toks)
    freq = Counter(all_tokens)            # vocabulary-frequency selection (most_common)
    N = min(vocab_size, len(freq))
    vocab = [t for t, _ in freq.most_common(N)]
    vocab_idx = {t: i for i, t in enumerate(vocab)}

    edge_count = Counter()                # edge-weight accumulator -> dense_laplacian (Class L)
    for tokens in tokens_per_section:
        indexed = [vocab_idx[t] for t in tokens if t in vocab_idx]
        for i in range(len(indexed)):
            for j in range(i + 1, min(i + window, len(indexed))):
                a, b = indexed[i], indexed[j]
                if a == b:
                    continue
                edge_count[(min(a, b), max(a, b))] += 1
    edges = list(edge_count.keys())
    weights = [float(w) for w in edge_count.values()]
    L = dense_laplacian(N, edges, weights)
    eigvals, eigvecs = hermitian_eigendecompose(L)

    top_k_indices = list(range(len(eigvals) - K, len(eigvals)))
    eigenvector_hvs = []
    for k_idx in reversed(top_k_indices):
        eigvec = eigvecs[:, k_idx]
        mag_sq = eigvec * eigvec
        top_idx = sorted(range(len(eigvec)), key=lambda i: -mag_sq[i])[:M_per_eigenvec]
        eigenvector_hvs.append(bundle([mint(vocab[i]) for i in top_idx]))
    instrument = bundle(eigenvector_hvs)
    # spectral signature: the top-K eigenvalue tail (F172 storage signature)
    eig_tail = [float(eigvals[i]) for i in reversed(top_k_indices)]
    return instrument, {
        "kernel": "K1_presence", "vocab_size": N, "n_edges": len(edges),
        "K_eigvecs": K, "M_per_eigvec": M_per_eigenvec,
        "eig_tail_top8": eig_tail[:8],
        "total_tokens": len(all_tokens), "unique_tokens": len(freq),
    }


def encode_probe_K1(text):
    toks = tokenize_text(text)
    if not toks:
        return mint("__empty__")
    return hierarchical_bundle([mint(t) for t in toks])


# ---- K3 sequence (position-bound n-gram bind + bundle) ----
def build_K3_sequence(tokens_per_section, n_gram=3, sample_n=5000,
                      position_stride=2731, seed=42):
    rng = random.Random(seed)
    all_ngrams = []
    for tokens in tokens_per_section:
        for i in range(len(tokens) - n_gram + 1):
            all_ngrams.append(tuple(tokens[i:i + n_gram]))
    total = len(all_ngrams)
    if total > sample_n:
        all_ngrams = rng.sample(all_ngrams, sample_n)
    ngram_hvs = []
    for ng in all_ngrams:
        hv = mint(ng[0])
        for k in range(1, n_gram):
            hv = bind(hv, permute(mint(ng[k]), k * position_stride))
        ngram_hvs.append(hv)
    instrument = hierarchical_bundle(ngram_hvs)
    return instrument, {
        "kernel": "K3_sequence", "n_gram": n_gram,
        "n_ngrams_total_corpus": total, "n_ngrams_sampled": len(all_ngrams),
        "position_stride": position_stride,
    }


def encode_probe_K3(text, n_gram=3, position_stride=2731):
    toks = tokenize_text(text)
    if len(toks) < n_gram:
        return mint("__short__")
    hvs = []
    for i in range(len(toks) - n_gram + 1):
        ng = toks[i:i + n_gram]
        hv = mint(ng[0])
        for k in range(1, n_gram):
            hv = bind(hv, permute(mint(ng[k]), k * position_stride))
        hvs.append(hv)
    return hierarchical_bundle(hvs)


# framework probes (live in the notebooks) vs negatives (live in neither)
FRAMEWORK_PROBES = [
    "stored relationship mechanism cyclic group",
    "primitive class operator vocabulary A N",
    "AMSC attestation provenance source doi",
    "hyperdimensional bind bundle permute klein four",
    "cascade composition class L laplacian eigenspectrum",
    "metric field ontology substrate excitation",
    "hopf fibration quaternionic four three seven",
    "so8 triality twenty eight dimension g2",
    "chirality gamma5 sector flip capacitor plate",
    "one three seven three partition hurwitz",
    "falsification null finding triality trimmed",
    "epistemic ceiling form not substrate reading",
]
NEGATIVE_PROBES = [
    "chocolate ice cream flavor",
    "professional soccer match score",
    "kitchen pencil sharpener metal",
    "tropical rainforest humidity bright",
    "vintage automobile manufacturing",
    "ocean coral reef colorful",
    "morning coffee croissant breakfast",
]


def baseline(encoder, paragraphs, n=100, seed=42):
    rng = random.Random(seed)
    sims = [similarity(encoder(a), encoder(b))
            for a, b in (rng.sample(paragraphs, 2) for _ in range(n))]
    m = sum(sims) / len(sims)
    s = (sum((x - m) ** 2 for x in sims) / len(sims)) ** 0.5
    return {"mean": m, "std": s, "max": max(sims), "min": min(sims), "n": n}


def smoke(instrument, encoder, base, probes):
    out = []
    for p in probes:
        sim = similarity(encoder(p), instrument)
        z = (sim - base["mean"]) / max(base["std"], 1e-9)
        out.append({"probe": p, "sim": sim, "z": z, "above_max": sim > base["max"]})
    return out


def save_instrument(name, inst, meta):
    binp = OUTDIR / f"{name}.bin"
    binp.write_bytes(inst)
    (OUTDIR / f"{name}.meta.json").write_text(json.dumps(meta, indent=2))
    return len(inst)


def main():
    print(f"=== Kernel refresh 2026-06-03 (srmech {srmech.__version__}) ===\n")

    loaded = {}
    for key, p in NOTEBOOKS.items():
        if not p.exists():
            print(f"  !! missing {p}"); continue
        loaded[key] = p.read_text()
        print(f"  {key:7s}: {p.name}  ({len(loaded[key]):,} chars)")

    # paragraph pool for baselines (both notebooks)
    paragraphs = []
    for text in loaded.values():
        for para in re.split(r'\n\n+', text):
            if 50 < len(para) < 500:
                paragraphs.append(para)
    print(f"  baseline paragraph pool: {len(paragraphs)}")

    results = {"refresh_date": "2026-06-03", "srmech_version": srmech.__version__, "D": D,
               "prior_build": {"srmech": "0.4.2", "n_ngrams_total_corpus": 116198},
               "per_notebook": {}, "combined": {}}

    base_K1 = baseline(encode_probe_K1, paragraphs)
    base_K3 = baseline(encode_probe_K3, paragraphs)
    print(f"\n  K1 baseline mean={base_K1['mean']:+.4f} std={base_K1['std']:.4f} max={base_K1['max']:+.4f}")
    print(f"  K3 baseline mean={base_K3['mean']:+.4f} std={base_K3['std']:.4f} max={base_K3['max']:+.4f}")

    # ---- per-notebook kernels ----
    section_sets = {}
    for key, text in loaded.items():
        secs = sections_of(text)
        section_sets[key] = secs
        print(f"\n--- {key} notebook kernel ---")
        K1, K1m = build_K1_presence(secs)
        K3, K3m = build_K3_sequence(secs)
        b1 = save_instrument(f"{key}_notebook_K1", K1, K1m)
        b3 = save_instrument(f"{key}_notebook_K3", K3, K3m)
        print(f"  K1: {b1} bytes  vocab={K1m['vocab_size']} edges={K1m['n_edges']} "
              f"tokens={K1m['total_tokens']:,} eig_tail={[round(e,2) for e in K1m['eig_tail_top8'][:4]]}")
        print(f"  K3: {b3} bytes  ngrams_total={K3m['n_ngrams_total_corpus']:,} sampled={K3m['n_ngrams_sampled']}")
        sm1 = smoke(K1, encode_probe_K1, base_K1, FRAMEWORK_PROBES)
        sm1n = smoke(K1, encode_probe_K1, base_K1, NEGATIVE_PROBES)
        sm3 = smoke(K3, encode_probe_K3, base_K3, FRAMEWORK_PROBES)
        sm3n = smoke(K3, encode_probe_K3, base_K3, NEGATIVE_PROBES)
        results["per_notebook"][key] = {
            "K1_meta": K1m, "K3_meta": K3m,
            "K1_fw_peak_z": max(r["z"] for r in sm1), "K1_fw_above_max": sum(r["above_max"] for r in sm1),
            "K1_neg_peak_z": max(r["z"] for r in sm1n), "K1_neg_above_max": sum(r["above_max"] for r in sm1n),
            "K3_fw_peak_z": max(r["z"] for r in sm3), "K3_fw_above_max": sum(r["above_max"] for r in sm3),
            "K3_neg_peak_z": max(r["z"] for r in sm3n), "K3_neg_above_max": sum(r["above_max"] for r in sm3n),
            "K1_fw_results": sm1, "K3_fw_results": sm3,
        }
        print(f"  K1 framework peak z={max(r['z'] for r in sm1):+.2f} (above_max {sum(r['above_max'] for r in sm1)}/{len(sm1)})  "
              f"neg peak z={max(r['z'] for r in sm1n):+.2f}")
        print(f"  K3 framework peak z={max(r['z'] for r in sm3):+.2f} (above_max {sum(r['above_max'] for r in sm3)}/{len(sm3)})  "
              f"neg peak z={max(r['z'] for r in sm3n):+.2f}")

    # ---- combined kernel (both notebooks; continuity with 52b) ----
    print(f"\n--- combined (srmech + mfo) kernel ---")
    all_secs = section_sets.get("srmech", []) + section_sets.get("mfo", [])
    cK1, cK1m = build_K1_presence(all_secs)
    cK3, cK3m = build_K3_sequence(all_secs)
    save_instrument("combined_K1", cK1, cK1m)
    save_instrument("combined_K3", cK3, cK3m)
    csm1 = smoke(cK1, encode_probe_K1, base_K1, FRAMEWORK_PROBES)
    csm1n = smoke(cK1, encode_probe_K1, base_K1, NEGATIVE_PROBES)
    csm3 = smoke(cK3, encode_probe_K3, base_K3, FRAMEWORK_PROBES)
    csm3n = smoke(cK3, encode_probe_K3, base_K3, NEGATIVE_PROBES)
    results["combined"] = {
        "K1_meta": cK1m, "K3_meta": cK3m,
        "K1_fw_peak_z": max(r["z"] for r in csm1), "K1_fw_above_max": sum(r["above_max"] for r in csm1),
        "K1_neg_peak_z": max(r["z"] for r in csm1n),
        "K3_fw_peak_z": max(r["z"] for r in csm3), "K3_fw_above_max": sum(r["above_max"] for r in csm3),
        "K3_neg_peak_z": max(r["z"] for r in csm3n),
    }
    print(f"  K1: vocab={cK1m['vocab_size']} edges={cK1m['n_edges']} tokens={cK1m['total_tokens']:,}  "
          f"fw peak z={max(r['z'] for r in csm1):+.2f} (above_max {sum(r['above_max'] for r in csm1)}/{len(csm1)})")
    print(f"  K3: ngrams_total={cK3m['n_ngrams_total_corpus']:,}  fw peak z={max(r['z'] for r in csm3):+.2f} "
          f"(above_max {sum(r['above_max'] for r in csm3)}/{len(csm3)})")
    print(f"  GROWTH vs prior 0.4.2 build: combined ngrams {cK3m['n_ngrams_total_corpus']:,} vs 116,198 "
          f"({cK3m['n_ngrams_total_corpus']/116198:.2f}x)")

    out = HERE / "R-RBS-LM-kernel_refresh_2026-06-03_results.json"
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"\nResults: {out}")
    print(f"Kernel artifacts: {OUTDIR}/ ({len(list(OUTDIR.glob('*.bin')))} .bin instruments)")


if __name__ == "__main__":
    main()
