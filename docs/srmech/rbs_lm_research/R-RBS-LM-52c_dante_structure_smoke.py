"""R-RBS-LM-52c — Dante's Divine Comedy: structure-as-meaning test.

Per user direction 2026-05-26: *"let's also see what happens when we
make a kernel from Dante's, The Divine Comedy. It's not the best
example, but it's a book sitting next to me on a stack of books."*

Dante is a structure-bearing corpus by construction: terza rima
(interlocking aba bcb cdc... rhyme), canto structure, fixed meter,
canonical 33+33+33+1 partition. Word ARRANGEMENT is meaning.

This is the falsification test for the poetry-as-structure hypothesis
from R-RBS-LM-52a Phase A Finding 37:
  - K1 (presence) should fire on Dante-specific TOKENS (Beatrice,
    Virgilio, selva, peccato, purgatorio) regardless of structure
  - K3 (sequence) should fire on Dante-specific n-grams that capture
    arrangement (nel mezzo del cammin; amor che move il sole; etc.)
  - Both should discriminate from negative-control probes (modern
    Italian non-Dante content)

Per 52b v2 finding: NO FFT band-pass (degrades mint-bundle signal).
Score-level smoothie: max(z_K1, z_K3) per probe.

Source: La Divina Commedia, Project Gutenberg PG ebook 1012 (Italian
original). Pre-fetched to /tmp/dante_italian.txt.
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


# Italian stopwords — most common Italian function words. Removing them
# pushes the vocabulary toward semantic content (Class K-style filter at
# the pre-vocabulary stage).
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
    chunk = MAX_BUNDLE_N - 2  # 255 odd
    partials = []
    for i in range(0, n, chunk):
        ch = vectors[i:i + chunk]
        if len(ch) % 2 == 0:
            ch = ch + [ch[0]]
        partials.append(bundle(ch))
    return hierarchical_bundle(partials)


def tokenize_italian(text):
    """Word-level Italian tokenization. Handles standard Italian
    orthography incl. apostrophes (l'altre → l'altre as a single token)."""
    # Capture words with optional apostrophe contraction
    raw = re.findall(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’]*[A-Za-zÀ-ÿ]|[A-Za-zÀ-ÿ]", text)
    out = []
    for tok in raw:
        low = tok.lower().replace("’", "'")
        if low in STOPWORDS_IT or len(low) < 2:
            continue
        out.append(low)
    return out


def strip_gutenberg(text):
    """Strip PG header/footer; keep just the work content."""
    start_marker = re.search(r"\*\*\* START OF (THE )?PROJECT GUTENBERG", text)
    end_marker = re.search(r"\*\*\* END OF (THE )?PROJECT GUTENBERG", text)
    if start_marker:
        text = text[start_marker.end():]
    if end_marker:
        text = text[:end_marker.start()]
    return text.strip()


def build_K1_presence(tokens_per_section, K=33, M_per_eigenvec=21,
                     vocab_size=200, window=5, D=8192):
    all_tokens = []
    for toks in tokens_per_section:
        all_tokens.extend(toks)
    freq = Counter(all_tokens)
    N = min(vocab_size, len(freq))
    vocab = [t for t, _ in freq.most_common(N)]
    vocab_idx = {t: i for i, t in enumerate(vocab)}

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
        "vocab_top_15": [(t, freq[t]) for t in vocab[:15]],
    }


def encode_probe_K1(text):
    toks = tokenize_italian(text)
    if not toks:
        return mint("__empty__")
    return hierarchical_bundle([mint(t) for t in toks])


def build_K3_sequence(tokens_per_section, n_gram=3, sample_n=5000,
                     position_stride=2731, seed=42):
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

    instrument = hierarchical_bundle(ngram_hvs)
    return instrument, {
        "kernel": "K3_sequence",
        "n_gram": n_gram,
        "n_ngrams_corpus": sum(max(len(t) - n_gram + 1, 0) for t in tokens_per_section),
        "n_ngrams_sampled": len(all_ngrams),
        "position_stride": position_stride,
    }


def encode_probe_K3(text, n_gram=3, position_stride=2731):
    toks = tokenize_italian(text)
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
    print(f"=== R-RBS-LM-52c: Dante structure-as-meaning test ===\n")
    print(f"srmech: {srmech.__version__}")

    if not DANTE_PATH.exists():
        print(f"FATAL: Dante text not found at {DANTE_PATH}")
        sys.exit(2)

    raw_text = DANTE_PATH.read_text(encoding="utf-8", errors="replace")
    text = strip_gutenberg(raw_text)
    print(f"Dante corpus: {len(text):,} chars after PG header/footer strip")
    print(f"First 200 chars: {text[:200]!r}")

    # Section by canto (numerical headings like "Inferno • Canto I")
    sections = re.split(r'\n\s*(?:Inferno|Purgatorio|Paradiso)\s*•?\s*Canto\s+[IVXLCDM]+', text)
    sections = [s for s in sections if len(s) > 200]
    print(f"\nSections (cantos + header): {len(sections)}")

    tokens_per_section = [tokenize_italian(s) for s in sections]
    n_total = sum(len(t) for t in tokens_per_section)
    print(f"Tokens: {n_total:,}")

    # ---- Build K1 ----
    print(f"\n--- K1 (presence) ---")
    K1, K1_meta = build_K1_presence(tokens_per_section)
    print(f"  K1: {len(K1)} bytes; vocab_top_15: {K1_meta['vocab_top_15'][:10]}")

    # ---- Build K3 ----
    print(f"\n--- K3 (sequence) ---")
    K3, K3_meta = build_K3_sequence(tokens_per_section)
    print(f"  K3: {len(K3)} bytes; {K3_meta['n_ngrams_corpus']:,} ngrams total in corpus; {K3_meta['n_ngrams_sampled']:,} sampled")

    # ---- Probes ----
    dante_probes = [
        "nel mezzo del cammin",                # Inferno I.1
        "selva oscura",                          # Inferno I (dark wood)
        "lasciate ogne speranza voi",            # Inferno III gate
        "Beatrice",                              # central character
        "Virgilio guida",                        # Virgil as guide
        "amor che move il sole",                 # Paradiso XXXIII last lines
        "anime triste peccato",                  # damned souls / sin
        "fiamme inferno",                        # flames / hell
        "cerchio peccatori",                     # circle of sinners
        "purgatorio monte",                      # purgatory mountain
        "Dio signore cielo",                     # God / heaven
        "Caronte traghettatore",                 # Charon the ferryman
        "Minosse giudice",                       # Minos judge
        "ahi quanto a dir qual era",             # Inferno I structural opening
        "tre fiere lonza leone lupa",            # three beasts from Inferno I
        "cammino vita oscura",                   # arrangement match: cammin vita
        "cielo stelle amor",                     # paradisal triad
    ]

    # Modern Italian negative controls (non-Dante topics)
    negative_probes = [
        "spaghetti carbonara pomodoro",
        "calcio domenica stadio",
        "macchina ferrari rossa",
        "computer internet wifi",
        "smartphone telefono batteria",
        "gelato cioccolato vaniglia",
        "treno milano roma",
    ]

    paragraphs = []
    for s in sections[:30]:  # subset for baseline
        for p in re.split(r'\n\n+', s):
            if 50 < len(p) < 500:
                paragraphs.append(p)
    print(f"Baseline paragraph pool: {len(paragraphs)}")

    def baseline_for_kernel(encoder, n=100):
        rng = random.Random(42)
        sims = []
        for _ in range(n):
            a, b = rng.sample(paragraphs, 2)
            sims.append(similarity(encoder(a), encoder(b)))
        m = sum(sims) / len(sims)
        s = (sum((x - m) ** 2 for x in sims) / len(sims)) ** 0.5
        return {"mean": m, "std": s, "max": max(sims), "min": min(sims), "n": n}

    b_K1 = baseline_for_kernel(encode_probe_K1)
    b_K3 = baseline_for_kernel(encode_probe_K3)
    print(f"\nBaselines:")
    print(f"  K1: mean={b_K1['mean']:+.4f}  std={b_K1['std']:.4f}  max={b_K1['max']:+.4f}")
    print(f"  K3: mean={b_K3['mean']:+.4f}  std={b_K3['std']:.4f}  max={b_K3['max']:+.4f}")

    # ---- Smoke ----
    def smoke(instrument, encoder, baseline, probes, kind):
        results = []
        for p in probes:
            s = similarity(encoder(p), instrument)
            z = (s - baseline["mean"]) / max(baseline["std"], 1e-9)
            above_max = s > baseline["max"]
            results.append({"probe": p, "kind": kind, "sim": s, "z": z, "above_max": above_max})
        return results

    print(f"\n=== K1 (presence) smoke ===")
    k1_d = smoke(K1, encode_probe_K1, b_K1, dante_probes, "dante")
    k1_n = smoke(K1, encode_probe_K1, b_K1, negative_probes, "negative")
    for r in k1_d + k1_n:
        flag = "***" if r["above_max"] else "**" if r["z"] > 2 else "*" if r["z"] > 1 else ""
        print(f"  [{r['kind']:>8s}] {r['probe']:<42s} sim={r['sim']:+.4f}  z={r['z']:+.2f}  {flag}")

    print(f"\n=== K3 (sequence) smoke ===")
    k3_d = smoke(K3, encode_probe_K3, b_K3, dante_probes, "dante")
    k3_n = smoke(K3, encode_probe_K3, b_K3, negative_probes, "negative")
    for r in k3_d + k3_n:
        flag = "***" if r["above_max"] else "**" if r["z"] > 2 else "*" if r["z"] > 1 else ""
        print(f"  [{r['kind']:>8s}] {r['probe']:<42s} sim={r['sim']:+.4f}  z={r['z']:+.2f}  {flag}")

    print(f"\n=== Score-level smoothie: max(z_K1, z_K3) ===")
    smoothie_results = []
    for kind, probes in [("dante", dante_probes), ("negative", negative_probes)]:
        for p in probes:
            s1 = similarity(encode_probe_K1(p), K1)
            z1 = (s1 - b_K1["mean"]) / max(b_K1["std"], 1e-9)
            ab1 = s1 > b_K1["max"]
            s3 = similarity(encode_probe_K3(p), K3)
            z3 = (s3 - b_K3["mean"]) / max(b_K3["std"], 1e-9)
            ab3 = s3 > b_K3["max"]
            max_z = max(z1, z3)
            smoothie_results.append({
                "probe": p, "kind": kind,
                "z_K1": z1, "z_K3": z3, "max_z": max_z,
                "above_max": ab1 or ab3,
            })
    for r in smoothie_results:
        flag = "***" if r["above_max"] else "**" if r["max_z"] > 2 else "*" if r["max_z"] > 1 else ""
        print(f"  [{r['kind']:>8s}] {r['probe']:<42s} z_K1={r['z_K1']:+.2f}  z_K3={r['z_K3']:+.2f}  max_z={r['max_z']:+.2f}  {flag}")

    # Summary
    def summarize(results, label, z_key="z"):
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
        summarize(k1_d + k1_n, "K1_alone"),
        summarize(k3_d + k3_n, "K3_alone"),
        summarize(smoothie_results, "smoothie_max_z", z_key="max_z"),
    ]

    print(f"\n\n{'='*72}\n=== R-RBS-LM-52c Dante summary\n{'='*72}\n")
    print(f"  {'kernel':<20s} {'D above_max':>12s} {'D z>2':>7s} {'D z>1':>7s} {'D peak z':>9s} {'NEG above_max':>14s} {'NEG z>2':>8s}")
    for s in summary:
        print(f"  {s['label']:<20s} {s['d_above_max']:>4d}/{s['n_dante']:<6d} "
              f"{s['d_z2']:>3d}/{s['n_dante']:<3d} {s['d_z1']:>3d}/{s['n_dante']:<3d} "
              f"{s['d_peak_z']:>9.2f} {s['neg_above_max']:>3d}/{s['n_negative']:<10d} "
              f"{s['neg_z2']:>3d}/{s['n_negative']:<3d}")

    # Reading
    k1_summary = summary[0]
    k3_summary = summary[1]
    sm_summary = summary[2]
    print(f"\n=== Reading (structure-as-meaning hypothesis) ===")
    print(f"  K1 peak z (presence): {k1_summary['d_peak_z']:.2f}")
    print(f"  K3 peak z (sequence): {k3_summary['d_peak_z']:.2f}")
    if k3_summary['d_peak_z'] > k1_summary['d_peak_z'] * 1.3:
        print(f"  → K3 dominates K1 — structure-as-meaning hypothesis SUPPORTED on Dante")
    elif k1_summary['d_peak_z'] > k3_summary['d_peak_z'] * 1.3:
        print(f"  → K1 dominates K3 — Dante's signal is more in tokens than arrangement")
    else:
        print(f"  → K1 and K3 comparable — both contribute; smoothie should help")
    print(f"  Smoothie peak z: {sm_summary['d_peak_z']:.2f}")
    print(f"  Negative-control discrimination: 0/{sm_summary['n_negative']} above_max" if sm_summary['neg_above_max'] == 0
          else f"  WARN: negatives leaking through {sm_summary['neg_above_max']}/{sm_summary['n_negative']}")

    output = {
        "partition": "R-RBS-LM-52c",
        "srmech_version": srmech.__version__,
        "source": "Dante La Divina Commedia (Italian; PG ebook 1012)",
        "n_sections": len(sections),
        "n_tokens": n_total,
        "K1_meta": K1_meta,
        "K3_meta": K3_meta,
        "baselines": {"K1": b_K1, "K3": b_K3},
        "summary": summary,
        "K1_results": k1_d + k1_n,
        "K3_results": k3_d + k3_n,
        "smoothie_results": smoothie_results,
    }
    out_path = HERE / "R-RBS-LM-52c_results.json"
    out_path.write_text(json.dumps(output, indent=2, default=str))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
