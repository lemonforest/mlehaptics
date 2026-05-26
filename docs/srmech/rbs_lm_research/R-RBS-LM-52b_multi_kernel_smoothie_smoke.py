"""R-RBS-LM-52b — Multi-kernel smoothie K1 + K3 on notebooks.

Per user direction 2026-05-26:
  *"to a Expert of poetry, structure is more than knowledge, structure
  is also meaning of words. this might be important for our smoothie of
  knowledge."*

K1 captures PRESENCE (bag-of-tokens; permutation-invariant). For poetry,
code, math, speech — word ARRANGEMENT is meaning, and K1 is blind to it.
Add K3 (position-bound n-gram sequence) to capture arrangement-as-meaning.

Kernels (per-substrate-tunable):
  K1: presence (Class L eigendecomp of cooccurrence; Class A mint per
      eigenvec-top-token; Class M bundle) — validated in 52a-v2
  K3: sequence (position-bound n-gram bind via Class M bind + permute;
      Class M bundle over sampled n-grams from corpus)

Per-kernel FFT band-pass (R-RBS-LM-49 Method B): preserve top-50% of bands
by squared magnitude. "Graft out junky coupling" per user 2026-05-26.

Smoothie merge: R-RBS-LM-33 merge_instruments at uniform weight.

Probes encoded via same K1 path (mint+bundle) AND same K3 path
(position-bound n-gram bundle). Similarity vs each kernel separately AND
vs the smoothie.

Falsification:
  - K1 alone on notebooks: strong signal (validated in 52a-v2)
  - K3 alone on notebooks: should also show signal IF arrangement matters
    for notebook content (probably weaker than K1 since notebooks are
    concept-rich more than arrangement-rich)
  - Smoothie K1+K3: at minimum matches the better kernel; ideally combines
"""

import json
import random
import re
import sys
import numpy as np
from collections import Counter
from pathlib import Path

import srmech
from srmech.amsc.laplacian import dense_laplacian, hermitian_eigendecompose
from srmech.amsc.hdc import bundle, similarity, bind, permute
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
than just too very much such etc i.e. e.g. cf via vs per pre post sub
super inter intra extra meta non co de re un mis
""".split())


_MINT_CACHE = {}


def mint(token, D=8192):
    if token not in _MINT_CACHE:
        _MINT_CACHE[token] = mint_vector(token, D=D)
    return _MINT_CACHE[token]


# srmech.amsc.hdc.bundle caps at MAX_BUNDLE_N=257 (HDC majority-vote SNR limit).
# Use hierarchical chunked bundling for larger collections.
MAX_BUNDLE_N = 257
def hierarchical_bundle(vectors):
    """Bundle arbitrary-length vectors via hierarchical chunked Class M bundle.
    Each inner bundle has odd count via Class K parity-padding."""
    n = len(vectors)
    if n == 0:
        return mint("__empty_bundle__")
    if n == 1:
        return vectors[0]
    if n <= MAX_BUNDLE_N:
        if n % 2 == 0:
            vectors = vectors + [vectors[0]]
        return bundle(vectors)
    chunk = MAX_BUNDLE_N - 2  # 255 = odd; leaves room for parity-pad
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


# ----- K1: presence kernel (Class L eigendecomp + Class M mint+bundle) -----

def build_K1_presence(tokens_per_section, K=33, M_per_eigenvec=21,
                     vocab_size=200, window=5, D=8192):
    """Returns (instrument_bytes, metadata_dict)."""
    all_tokens = []
    for toks in tokens_per_section:
        all_tokens.extend(toks)
    freq = Counter(all_tokens)
    N = min(vocab_size, len(freq))
    vocab = [t for t, _ in freq.most_common(N)]
    vocab_idx = {t: i for i, t in enumerate(vocab)}

    # Co-occurrence edges (undirected; symmetric)
    edge_count = Counter()
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

    # Top-K eigenvectors → top-M tokens → mint+bundle
    top_k_indices = list(range(len(eigvals) - K, len(eigvals)))
    eigenvector_hvs = []
    for k_idx in reversed(top_k_indices):
        eigvec = eigvecs[:, k_idx]
        mag_sq = eigvec * eigvec
        top_idx = sorted(range(len(eigvec)), key=lambda i: -mag_sq[i])[:M_per_eigenvec]
        token_vectors = [mint(vocab[i]) for i in top_idx]
        eigenvector_hvs.append(bundle(token_vectors))
    instrument = bundle(eigenvector_hvs)

    return instrument, {
        "kernel": "K1_presence",
        "vocab_size": N,
        "n_edges": len(edges),
        "K_eigvecs": K,
        "M_per_eigvec": M_per_eigenvec,
    }


def encode_probe_K1(text):
    """K1 probe encoder: tokenize → mint each → bundle."""
    toks = tokenize_text(text)
    if not toks:
        return mint("__empty__")
    return hierarchical_bundle([mint(t) for t in toks])


# ----- K3: sequence kernel (position-bound n-gram bind + bundle) -----

def build_K3_sequence(tokens_per_section, n_gram=3, sample_n=5000,
                     position_stride=2731, seed=42, D=8192):
    """K3 kernel: position-bound n-gram bind via Class M.

    For each sampled n-gram (t_0, t_1, ..., t_{n-1}):
      hv = bind(mint(t_0), permute(mint(t_1), 1·stride), ..., permute(mint(t_{n-1}), (n-1)·stride))

    The permute rotates each token by a position-dependent amount; bind
    XOR-folds them. This is the canonical srmech ordered-binding (Class M
    bind + Class L positional rotation). Different permutation per
    position → order-sensitive composition: (A,B,C) ≠ (B,A,C).

    position_stride = D/3 ≈ 2731 ensures non-overlapping rotations for
    n_gram ≤ 3.
    """
    rng = random.Random(seed)
    all_ngrams = []
    for tokens in tokens_per_section:
        for i in range(len(tokens) - n_gram + 1):
            all_ngrams.append(tuple(tokens[i:i + n_gram]))
    if len(all_ngrams) > sample_n:
        all_ngrams = rng.sample(all_ngrams, sample_n)

    ngram_hvs = []
    for ng in all_ngrams:
        hv = mint(ng[0])
        for k in range(1, n_gram):
            permuted = permute(mint(ng[k]), k * position_stride)
            hv = bind(hv, permuted)
        ngram_hvs.append(hv)

    # Hierarchical Class M bundle (chunked at MAX_BUNDLE_N=257)
    instrument = hierarchical_bundle(ngram_hvs)

    return instrument, {
        "kernel": "K3_sequence",
        "n_gram": n_gram,
        "n_ngrams_total_corpus": sum(max(len(t) - n_gram + 1, 0) for t in tokens_per_section),
        "n_ngrams_sampled": len(all_ngrams) - (1 if len(all_ngrams) % 2 == 1 else 0),
        "position_stride": position_stride,
    }


def encode_probe_K3(text, n_gram=3, position_stride=2731):
    """K3 probe encoder: position-bound n-gram bind + hierarchical bundle."""
    toks = tokenize_text(text)
    if len(toks) < n_gram:
        return mint("__short__")
    ngram_hvs = []
    for i in range(len(toks) - n_gram + 1):
        ng = toks[i:i + n_gram]
        hv = mint(ng[0])
        for k in range(1, n_gram):
            permuted = permute(mint(ng[k]), k * position_stride)
            hv = bind(hv, permuted)
        ngram_hvs.append(hv)
    return hierarchical_bundle(ngram_hvs)


# ----- FFT band-pass (R-RBS-LM-49 Method B) — surgical compression -----

def fft_bandpass(instrument_bytes, retain_band_fraction=0.5):
    """Apply Method B surgical compression. Routes through srmech-equivalent
    numpy operations on the bit-stream (since srmech doesn't yet ship FFT
    band-pass as a named operation; this is R-RBS-LM-49z cleanup territory)."""
    bits = np.unpackbits(np.frombuffer(instrument_bytes, dtype=np.uint8), bitorder="big")
    bipolar = 2.0 * bits.astype(np.float64) - 1.0
    n = len(bipolar)
    spectrum = np.fft.rfft(bipolar)
    mag_sq = spectrum.real * spectrum.real + spectrum.imag * spectrum.imag
    n_keep = int(round(retain_band_fraction * len(spectrum)))
    if n_keep < 1:
        n_keep = 1
    keep_idx = np.argsort(-mag_sq)[:n_keep]
    mask = np.zeros(len(spectrum), dtype=bool)
    mask[keep_idx] = True
    spectrum_kept = spectrum * mask
    reconstructed = np.fft.irfft(spectrum_kept, n=n)
    new_bits = (reconstructed > 0).astype(np.uint8)
    return np.packbits(new_bits, bitorder="big").tobytes()


# ----- Smoothie merge (R-RBS-LM-33 merge_instruments at uniform weight) -----

def merge_uniform(instruments):
    """Uniform-weight per-bit majority across instruments. Mirrors
    R-RBS-LM-33 merge_instruments with n_obs=None. Needs odd count."""
    n = len(instruments)
    if n == 1:
        return instruments[0]
    arrays = []
    for inst in instruments:
        bits = np.unpackbits(np.frombuffer(inst, dtype=np.uint8), bitorder="big")
        arrays.append(bits.astype(np.int32))
    stacked = np.stack(arrays, axis=0)
    summed = stacked.sum(axis=0)
    merged_bits = (2 * summed > n).astype(np.uint8)
    return np.packbits(merged_bits, bitorder="big").tobytes()


# ----- Main -----

def main():
    print(f"=== R-RBS-LM-52b: K1 + K3 smoothie on notebooks ===\n")
    print(f"srmech: {srmech.__version__}")

    # ---- Load + tokenize ----
    notebooks = []
    for p in NOTEBOOK_PATHS:
        if not p.exists():
            continue
        notebooks.append((p.name, p.read_text()))
        print(f"  loaded {p.name}")

    sections = []
    for fname, text in notebooks:
        parts = re.split(r'\n#{2,3}\s+', text)
        for part in parts:
            if len(part) > 100:
                sections.append(tokenize_text(part))
    n_total = sum(len(s) for s in sections)
    print(f"Sections: {len(sections)}; total tokens: {n_total:,}")

    # ---- Build K1 ----
    print(f"\n--- Building K1 (presence kernel) ---")
    K1, K1_meta = build_K1_presence(sections)
    print(f"  K1: {len(K1)} bytes; meta: {K1_meta}")
    # NOTE per 52b v1: FFT band-pass DEGRADES mint-bundle signal (peak z 5.87→2.33).
    # Substrate-dependent: R-RBS-LM-49 confirmed FFT preserves byte-mode cascade
    # because its signal is spectrally concentrated; mint-bundle signal is
    # token-distributed not spectrally concentrated. Skip compression for K1/K3.
    K1_uncompressed = K1  # keep as-is; document the observation

    # ---- Build K3 ----
    print(f"\n--- Building K3 (sequence kernel) ---")
    K3, K3_meta = build_K3_sequence(sections)
    print(f"  K3: {len(K3)} bytes; meta: {K3_meta}")
    K3_uncompressed = K3

    # Per 52b v1 finding: instrument-level merge of K1+K3 dilutes signal because
    # probes are encoded by one encoder; cross-encoder/instrument similarity drops.
    # Use SCORE-LEVEL smoothie instead: compute K1_score and K3_score per probe,
    # take max (or weighted combination). This treats kernel-pair as multi-channel.
    print(f"\n--- Score-level smoothie: max(K1_score, K3_score) per probe ---")

    # ---- Probes ----
    notebook_probes = [
        "two substrate framework",
        "class l spine spectral",
        "born hopf readout",
        "operation primary cyclic algebra",
        "epistemic ceiling form not substrate",
        "fractal recursion substrate",
        "metric field ontology",
        "cascade match form claim",
        "Reading-D scale ladder",
        "biology cascade encoding",
        "class n rational anchor",
        "weak coupling truncate instrument",
        "cross substrate matching method",
        "L-system seed grammar tree",
        "Kaluza Klein photon metric",
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

    paragraphs = []
    for fname, text in notebooks:
        for p in re.split(r'\n\n+', text):
            if 50 < len(p) < 500:
                paragraphs.append(p)

    # Baselines per kernel
    def baseline_for_kernel(encoder, n=100):
        rng = random.Random(42)
        sims = []
        for _ in range(n):
            a, b = rng.sample(paragraphs, 2)
            sims.append(similarity(encoder(a), encoder(b)))
        m = sum(sims) / len(sims)
        s = (sum((x - m) ** 2 for x in sims) / len(sims)) ** 0.5
        return {"mean": m, "std": s, "max": max(sims), "min": min(sims), "n": n}

    print(f"\n--- Baselines (random paragraph pairs) ---")
    b_K1 = baseline_for_kernel(encode_probe_K1)
    b_K3 = baseline_for_kernel(encode_probe_K3)
    print(f"  K1 baseline:  mean={b_K1['mean']:+.4f}  std={b_K1['std']:.4f}  max={b_K1['max']:+.4f}")
    print(f"  K3 baseline:  mean={b_K3['mean']:+.4f}  std={b_K3['std']:.4f}  max={b_K3['max']:+.4f}")

    # ---- Smoke ----
    def smoke_against(instrument, encoder, baseline, label, probes, kind="probe"):
        results = []
        for p in probes:
            s = similarity(encoder(p), instrument)
            z = (s - baseline["mean"]) / max(baseline["std"], 1e-9)
            above_max = s > baseline["max"]
            results.append({"probe": p, "kind": kind, "sim": s, "z": z, "above_max": above_max})
        return results

    print(f"\n=== Smoke: K1 alone (no FFT compression) ===")
    k1_pos = smoke_against(K1_uncompressed, encode_probe_K1, b_K1, "K1", notebook_probes, "notebook")
    k1_neg = smoke_against(K1_uncompressed, encode_probe_K1, b_K1, "K1", negative_probes, "negative")
    for r in k1_pos + k1_neg:
        flag = "***" if r["above_max"] else "**" if r["z"] > 2 else "*" if r["z"] > 1 else ""
        print(f"  [{r['kind']:>8s}] {r['probe']:<38s} sim={r['sim']:+.4f}  z={r['z']:+.2f}  {flag}")

    print(f"\n=== Smoke: K3 alone (no FFT compression) ===")
    k3_pos = smoke_against(K3_uncompressed, encode_probe_K3, b_K3, "K3", notebook_probes, "notebook")
    k3_neg = smoke_against(K3_uncompressed, encode_probe_K3, b_K3, "K3", negative_probes, "negative")
    for r in k3_pos + k3_neg:
        flag = "***" if r["above_max"] else "**" if r["z"] > 2 else "*" if r["z"] > 1 else ""
        print(f"  [{r['kind']:>8s}] {r['probe']:<38s} sim={r['sim']:+.4f}  z={r['z']:+.2f}  {flag}")

    # Score-level smoothie: max(K1 z, K3 z) per probe
    print(f"\n=== Score-level smoothie: max(K1_z, K3_z) per probe ===")
    sm_results = []
    for kind, probes_set in [("notebook", notebook_probes), ("negative", negative_probes)]:
        for p in probes_set:
            s_K1 = similarity(encode_probe_K1(p), K1_uncompressed)
            z_K1 = (s_K1 - b_K1["mean"]) / max(b_K1["std"], 1e-9)
            above_max_K1 = s_K1 > b_K1["max"]
            s_K3 = similarity(encode_probe_K3(p), K3_uncompressed)
            z_K3 = (s_K3 - b_K3["mean"]) / max(b_K3["std"], 1e-9)
            above_max_K3 = s_K3 > b_K3["max"]
            # Multi-channel detector: max z across kernels
            max_z = max(z_K1, z_K3)
            any_above_max = above_max_K1 or above_max_K3
            sm_results.append({
                "probe": p, "kind": kind,
                "sim_K1": s_K1, "z_K1": z_K1,
                "sim_K3": s_K3, "z_K3": z_K3,
                "max_z": max_z,
                "above_max": any_above_max,
            })
    for r in sm_results:
        flag = "***" if r["above_max"] else "**" if r["max_z"] > 2 else "*" if r["max_z"] > 1 else ""
        print(f"  [{r['kind']:>8s}] {r['probe']:<38s} z_K1={r['z_K1']:+.2f}  z_K3={r['z_K3']:+.2f}  max_z={r['max_z']:+.2f}  {flag}")

    # ---- Aggregate verdict ----
    def summarize(results, label):
        notebooks_r = [r for r in results if r["kind"] == "notebook"]
        negs = [r for r in results if r["kind"] == "negative"]
        return {
            "label": label,
            "n_notebook": len(notebooks_r),
            "n_negative": len(negs),
            "nb_above_max": sum(1 for r in notebooks_r if r["above_max"]),
            "nb_z2": sum(1 for r in notebooks_r if r["z"] > 2),
            "nb_z1": sum(1 for r in notebooks_r if r["z"] > 1),
            "neg_above_max": sum(1 for r in negs if r["above_max"]),
            "neg_z2": sum(1 for r in negs if r["z"] > 2),
            "nb_peak_z": max(r["z"] for r in notebooks_r) if notebooks_r else 0,
        }

    # Synthetic summary record for score-level smoothie
    def smoothie_summary(records, label):
        notebooks_r = [r for r in records if r["kind"] == "notebook"]
        negs = [r for r in records if r["kind"] == "negative"]
        return {
            "label": label,
            "n_notebook": len(notebooks_r),
            "n_negative": len(negs),
            "nb_above_max": sum(1 for r in notebooks_r if r["above_max"]),
            "nb_z2": sum(1 for r in notebooks_r if r["max_z"] > 2),
            "nb_z1": sum(1 for r in notebooks_r if r["max_z"] > 1),
            "neg_above_max": sum(1 for r in negs if r["above_max"]),
            "neg_z2": sum(1 for r in negs if r["max_z"] > 2),
            "nb_peak_z": max(r["max_z"] for r in notebooks_r) if notebooks_r else 0,
        }
    summary = [
        summarize(k1_pos + k1_neg, "K1_alone"),
        summarize(k3_pos + k3_neg, "K3_alone"),
        smoothie_summary(sm_results, "smoothie_score_max"),
    ]

    print(f"\n\n{'='*72}\n=== R-RBS-LM-52b summary table\n{'='*72}\n")
    print(f"  {'kernel/smoothie':<22s}  {'NB above_max':>13s}  {'NB z>2':>7s}  {'NB z>1':>7s}  "
          f"{'NB peak z':>10s}  {'NEG above_max':>14s}  {'NEG z>2':>8s}")
    for s in summary:
        print(f"  {s['label']:<22s}  {s['nb_above_max']:>4d}/{s['n_notebook']:<7d}  "
              f"{s['nb_z2']:>3d}/{s['n_notebook']:<3d}  {s['nb_z1']:>3d}/{s['n_notebook']:<3d}  "
              f"{s['nb_peak_z']:>10.2f}  {s['neg_above_max']:>3d}/{s['n_negative']:<10d}  "
              f"{s['neg_z2']:>3d}/{s['n_negative']:<3d}")

    output = {
        "partition": "R-RBS-LM-52b",
        "srmech_version": srmech.__version__,
        "K1_meta": K1_meta,
        "K3_meta": K3_meta,
        "baselines": {"K1": b_K1, "K3": b_K3},
        "summary": summary,
        "K1_alone_results": k1_pos + k1_neg,
        "K3_alone_results": k3_pos + k3_neg,
        "smoothie_score_max_results": sm_results,
        "methodology_note_fft_bandpass_substrate_dependent": True,
    }
    out_path = HERE / "R-RBS-LM-52b_results.json"
    out_path.write_text(json.dumps(output, indent=2, default=str))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
