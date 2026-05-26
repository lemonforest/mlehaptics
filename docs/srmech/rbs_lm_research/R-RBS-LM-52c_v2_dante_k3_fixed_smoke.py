"""R-RBS-LM-52c-v2 — Dante test with K3 fixed: preserve stopwords for sequence.

Per 52c diagnosis:
  - Italian stopwords (nel, del, che, il) carry the arrangement-bearing
    information for sequence kernels. Filtering them destroyed K3.
  - K3 sample of 5000 saturates HDC SNR (~D/log₂D = 630 effective).

Iteration:
  - K1: keep stopword filter (concept retrieval; same as before)
  - K3: NO stopword filter (preserve structure-bearing function words)
  - K3 sample: cap at 500 (within HDC SNR budget)
  - K3 n-gram: try BOTH 3-gram AND 4-gram (longer phrases capture more
    arrangement; shorter capture more co-occurrence)
  - Score smoothie: max(z_K1, z_K3_n3, z_K3_n4)

This isolates the structure-as-meaning claim from the substrate-
preparation methodology.
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
DANTE_PATH = Path("/tmp/dante_italian.txt")


# Italian stopwords — used for K1 vocabulary filter, NOT for K3.
STOPWORDS_IT = set("""
il lo la gli le un una uno e ed di da del dello della dei degli delle
in nel nello nella nei negli nelle su sul sulla con per a al alla ai
agli alle che chi cui dove come quando perché perche quale quali questo
questa questi queste quello quella quelli quelle ma però pero se anche
ancora già gia poi allora dunque quindi mentre o ora ne ce ci si vi
sono è e ho ha hanno avete avevo aveva avete avevano fui era erano ero
sia stato stata stati state non sì si no più piu sempre mai forse
quasi cosi così molto poco tanto troppo ogni ognuno ogni tutto tutta
tutti tutte nessuno nessuna alcuni alcune alcuna altro altra altri altre
io tu egli ella esso essa noi voi essi esse mi ti gli le lui lei loro
suo sua suoi sue mio mia miei mie tuo tua tuoi tue nostro nostra nostri
nostre vostro vostra vostri vostre
""".split())


_MINT_CACHE = {}


def mint(token, D=8192):
    if token not in _MINT_CACHE:
        _MINT_CACHE[token] = mint_vector(token, D=D)
    return _MINT_CACHE[token]


MAX_BUNDLE_N = 257


def hierarchical_bundle(vectors):
    n = len(vectors)
    if n == 0:
        return mint("__empty__")
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


def tokenize_italian_raw(text):
    """All Italian tokens; NO stopword filter. For K3 sequence kernel."""
    raw = re.findall(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’]*[A-Za-zÀ-ÿ]|[A-Za-zÀ-ÿ]", text)
    return [t.lower().replace("’", "'") for t in raw if len(t) >= 1]


def tokenize_italian_filtered(text):
    """Italian tokens with stopword filter. For K1 presence kernel."""
    return [t for t in tokenize_italian_raw(text) if t not in STOPWORDS_IT and len(t) >= 2]


def strip_gutenberg(text):
    start_marker = re.search(r"\*\*\* START OF (THE )?PROJECT GUTENBERG", text)
    end_marker = re.search(r"\*\*\* END OF (THE )?PROJECT GUTENBERG", text)
    if start_marker:
        text = text[start_marker.end():]
    if end_marker:
        text = text[:end_marker.start()]
    return text.strip()


def build_K1_presence(filtered_tokens_per_section, K=33, M_per_eigenvec=21,
                     vocab_size=200, window=5):
    all_tokens = []
    for toks in filtered_tokens_per_section:
        all_tokens.extend(toks)
    freq = Counter(all_tokens)
    N = min(vocab_size, len(freq))
    vocab = [t for t, _ in freq.most_common(N)]
    vocab_idx = {t: i for i, t in enumerate(vocab)}

    edge_count = Counter()
    for tokens in filtered_tokens_per_section:
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
        token_vectors = [mint(vocab[i]) for i in top_idx]
        eigenvector_hvs.append(bundle(token_vectors))
    instrument = bundle(eigenvector_hvs)
    return instrument, {
        "kernel": "K1_presence",
        "vocab_size": N,
        "vocab_top_15": [(t, freq[t]) for t in vocab[:15]],
    }


def encode_probe_K1(text):
    toks = tokenize_italian_filtered(text)
    if not toks:
        return mint("__empty__")
    return hierarchical_bundle([mint(t) for t in toks])


def build_K3_sequence(raw_tokens_per_section, n_gram=3, sample_n=500,
                     position_stride=2731, seed=42):
    """K3 with raw (unfiltered) tokens — preserves structure."""
    rng = random.Random(seed)
    all_ngrams = []
    for tokens in raw_tokens_per_section:
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

    instrument = hierarchical_bundle(ngram_hvs)
    return instrument, {
        "kernel": f"K3_sequence_n{n_gram}",
        "n_gram": n_gram,
        "n_ngrams_corpus_total": sum(max(len(t) - n_gram + 1, 0) for t in raw_tokens_per_section),
        "n_ngrams_sampled": len(all_ngrams),
        "position_stride": position_stride,
    }


def encode_probe_K3(text, n_gram=3, position_stride=2731):
    """K3 probe: raw tokens (no stopword filter)."""
    toks = tokenize_italian_raw(text)
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


def main():
    print(f"=== R-RBS-LM-52c-v2: Dante with K3 fix (stopwords preserved) ===\n")
    print(f"srmech: {srmech.__version__}")

    if not DANTE_PATH.exists():
        print(f"FATAL: {DANTE_PATH} not found")
        sys.exit(2)
    text = strip_gutenberg(DANTE_PATH.read_text(encoding="utf-8", errors="replace"))
    print(f"Corpus: {len(text):,} chars")

    sections = re.split(r'\n\s*(?:Inferno|Purgatorio|Paradiso)\s*•?\s*Canto\s+[IVXLCDM]+', text)
    sections = [s for s in sections if len(s) > 200]
    print(f"Sections: {len(sections)}")

    raw_tokens = [tokenize_italian_raw(s) for s in sections]
    filtered_tokens = [tokenize_italian_filtered(s) for s in sections]
    n_raw = sum(len(t) for t in raw_tokens)
    n_filt = sum(len(t) for t in filtered_tokens)
    print(f"Tokens: {n_raw:,} raw; {n_filt:,} filtered (stopwords removed)")

    # K1: filtered
    print(f"\n--- K1 (presence; filtered) ---")
    K1, K1_meta = build_K1_presence(filtered_tokens)
    print(f"  vocab_top_15: {K1_meta['vocab_top_15'][:10]}")

    # K3-3: raw n=3
    print(f"\n--- K3 n=3 (sequence; raw tokens; sample 500) ---")
    K3_3, K3_3_meta = build_K3_sequence(raw_tokens, n_gram=3, sample_n=500)
    print(f"  {K3_3_meta}")

    # K3-4: raw n=4
    print(f"\n--- K3 n=4 (sequence; raw tokens; sample 500) ---")
    K3_4, K3_4_meta = build_K3_sequence(raw_tokens, n_gram=4, sample_n=500)
    print(f"  {K3_4_meta}")

    dante_probes = [
        "nel mezzo del cammin",
        "selva oscura",
        "lasciate ogne speranza voi",
        "Beatrice",
        "Virgilio guida",
        "amor che move il sole",
        "anime triste peccato",
        "fiamme inferno",
        "cerchio peccatori",
        "purgatorio monte",
        "Dio signore cielo",
        "Caronte traghettatore",
        "Minosse giudice",
        "ahi quanto a dir qual era",
        "tre fiere lonza leone lupa",
        "nel mezzo del cammin di nostra vita",  # the actual opening
        "lasciate ogne speranza voi ch'intrate",  # gate of hell
    ]
    negative_probes = [
        "spaghetti carbonara pomodoro",
        "calcio domenica stadio",
        "macchina ferrari rossa",
        "computer internet wifi",
        "smartphone telefono batteria",
        "gelato cioccolato vaniglia",
        "treno milano roma",
    ]

    # Baselines per kernel
    paragraphs = []
    for s in sections[:30]:
        for p in re.split(r'\n\n+', s):
            if 50 < len(p) < 500:
                paragraphs.append(p)

    def baseline(encoder, n=100):
        rng = random.Random(42)
        sims = []
        for _ in range(n):
            a, b = rng.sample(paragraphs, 2)
            sims.append(similarity(encoder(a), encoder(b)))
        m = sum(sims) / len(sims)
        s = (sum((x - m) ** 2 for x in sims) / len(sims)) ** 0.5
        return {"mean": m, "std": s, "max": max(sims), "min": min(sims)}

    b_K1 = baseline(encode_probe_K1)
    b_K3_3 = baseline(lambda t: encode_probe_K3(t, n_gram=3))
    b_K3_4 = baseline(lambda t: encode_probe_K3(t, n_gram=4))
    print(f"\nBaselines:")
    print(f"  K1:    mean={b_K1['mean']:+.4f}  std={b_K1['std']:.4f}  max={b_K1['max']:+.4f}")
    print(f"  K3-3:  mean={b_K3_3['mean']:+.4f}  std={b_K3_3['std']:.4f}  max={b_K3_3['max']:+.4f}")
    print(f"  K3-4:  mean={b_K3_4['mean']:+.4f}  std={b_K3_4['std']:.4f}  max={b_K3_4['max']:+.4f}")

    def smoke(instrument, encoder, b, probes, kind):
        out = []
        for p in probes:
            s = similarity(encoder(p), instrument)
            z = (s - b["mean"]) / max(b["std"], 1e-9)
            out.append({"probe": p, "kind": kind, "sim": s, "z": z,
                         "above_max": s > b["max"]})
        return out

    print(f"\n=== K1 smoke ===")
    k1 = smoke(K1, encode_probe_K1, b_K1, dante_probes, "dante") + \
         smoke(K1, encode_probe_K1, b_K1, negative_probes, "negative")
    for r in k1:
        flag = "***" if r["above_max"] else "**" if r["z"] > 2 else "*" if r["z"] > 1 else ""
        print(f"  [{r['kind']:>8s}] {r['probe']:<42s} sim={r['sim']:+.4f}  z={r['z']:+.2f}  {flag}")

    print(f"\n=== K3 n=3 smoke (raw tokens preserved) ===")
    k3_3 = smoke(K3_3, lambda t: encode_probe_K3(t, n_gram=3), b_K3_3, dante_probes, "dante") + \
           smoke(K3_3, lambda t: encode_probe_K3(t, n_gram=3), b_K3_3, negative_probes, "negative")
    for r in k3_3:
        flag = "***" if r["above_max"] else "**" if r["z"] > 2 else "*" if r["z"] > 1 else ""
        print(f"  [{r['kind']:>8s}] {r['probe']:<42s} sim={r['sim']:+.4f}  z={r['z']:+.2f}  {flag}")

    print(f"\n=== K3 n=4 smoke ===")
    k3_4 = smoke(K3_4, lambda t: encode_probe_K3(t, n_gram=4), b_K3_4, dante_probes, "dante") + \
           smoke(K3_4, lambda t: encode_probe_K3(t, n_gram=4), b_K3_4, negative_probes, "negative")
    for r in k3_4:
        flag = "***" if r["above_max"] else "**" if r["z"] > 2 else "*" if r["z"] > 1 else ""
        print(f"  [{r['kind']:>8s}] {r['probe']:<42s} sim={r['sim']:+.4f}  z={r['z']:+.2f}  {flag}")

    # Score smoothie: max(z_K1, z_K3-3, z_K3-4)
    print(f"\n=== Score smoothie max(K1, K3-3, K3-4) ===")
    sm = []
    for kind, probes in [("dante", dante_probes), ("negative", negative_probes)]:
        for p in probes:
            s1 = similarity(encode_probe_K1(p), K1)
            z1 = (s1 - b_K1["mean"]) / max(b_K1["std"], 1e-9)
            s3 = similarity(encode_probe_K3(p, n_gram=3), K3_3)
            z3 = (s3 - b_K3_3["mean"]) / max(b_K3_3["std"], 1e-9)
            s4 = similarity(encode_probe_K3(p, n_gram=4), K3_4)
            z4 = (s4 - b_K3_4["mean"]) / max(b_K3_4["std"], 1e-9)
            mx = max(z1, z3, z4)
            ab = (s1 > b_K1["max"]) or (s3 > b_K3_3["max"]) or (s4 > b_K3_4["max"])
            sm.append({"probe": p, "kind": kind, "z_K1": z1, "z_K3_3": z3,
                        "z_K3_4": z4, "max_z": mx, "above_max": ab})
    for r in sm:
        flag = "***" if r["above_max"] else "**" if r["max_z"] > 2 else "*" if r["max_z"] > 1 else ""
        print(f"  [{r['kind']:>8s}] {r['probe']:<42s} K1={r['z_K1']:+.2f} K3-3={r['z_K3_3']:+.2f} K3-4={r['z_K3_4']:+.2f} max={r['max_z']:+.2f} {flag}")

    def sumlabel(results, label, z_key="z"):
        ds = [r for r in results if r["kind"] == "dante"]
        negs = [r for r in results if r["kind"] == "negative"]
        return {
            "label": label,
            "n_dante": len(ds), "n_negative": len(negs),
            "d_above_max": sum(1 for r in ds if r["above_max"]),
            "d_z2": sum(1 for r in ds if r[z_key] > 2),
            "d_z1": sum(1 for r in ds if r[z_key] > 1),
            "neg_above_max": sum(1 for r in negs if r["above_max"]),
            "neg_z2": sum(1 for r in negs if r[z_key] > 2),
            "d_peak_z": max((r[z_key] for r in ds), default=0),
        }

    summary = [
        sumlabel(k1, "K1_alone"),
        sumlabel(k3_3, "K3_n3"),
        sumlabel(k3_4, "K3_n4"),
        sumlabel(sm, "smoothie_max_z", z_key="max_z"),
    ]
    print(f"\n\n{'='*72}\n=== R-RBS-LM-52c-v2 Dante summary\n{'='*72}\n")
    print(f"  {'kernel':<20s} {'D above_max':>13s} {'D z>2':>7s} {'D z>1':>7s} {'D peak z':>9s} {'NEG above_max':>14s} {'NEG z>2':>8s}")
    for s in summary:
        print(f"  {s['label']:<20s} {s['d_above_max']:>4d}/{s['n_dante']:<6d} "
              f"{s['d_z2']:>3d}/{s['n_dante']:<3d} {s['d_z1']:>3d}/{s['n_dante']:<3d} "
              f"{s['d_peak_z']:>9.2f} {s['neg_above_max']:>3d}/{s['n_negative']:<10d} "
              f"{s['neg_z2']:>3d}/{s['n_negative']:<3d}")

    # Compare to 52c v1
    print(f"\n=== Comparison vs 52c v1 ===")
    print(f"  52c v1 K1 peak z: 2.19; v2 K1 peak z: {summary[0]['d_peak_z']:.2f}")
    print(f"  52c v1 K3 peak z: 0.36; v2 K3-3 peak z: {summary[1]['d_peak_z']:.2f}")
    print(f"  52c v1 K3 peak z: 0.36; v2 K3-4 peak z: {summary[2]['d_peak_z']:.2f}")
    print(f"  52c v1 smoothie peak: 2.19; v2 smoothie peak: {summary[3]['d_peak_z']:.2f}")

    output = {
        "partition": "R-RBS-LM-52c-v2",
        "fix": "K3 uses raw (unfiltered) tokens; sample 500; n=3 AND n=4 tested",
        "srmech_version": srmech.__version__,
        "n_tokens_raw": n_raw,
        "n_tokens_filtered": n_filt,
        "K1_meta": K1_meta,
        "K3_n3_meta": K3_3_meta,
        "K3_n4_meta": K3_4_meta,
        "baselines": {"K1": b_K1, "K3_n3": b_K3_3, "K3_n4": b_K3_4},
        "summary": summary,
        "K1_results": k1,
        "K3_n3_results": k3_3,
        "K3_n4_results": k3_4,
        "smoothie_results": sm,
    }
    out_path = HERE / "R-RBS-LM-52c_v2_results.json"
    out_path.write_text(json.dumps(output, indent=2, default=str))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
