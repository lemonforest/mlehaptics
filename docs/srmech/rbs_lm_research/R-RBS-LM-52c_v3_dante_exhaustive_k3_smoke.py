"""R-RBS-LM-52c-v3 — Dante K3 with EXHAUSTIVE n-gram bundling.

Per 52c-v2 finding: K3 n=4 with stopwords preserved fires at z=1.79 on
4 canonical Dante phrases (5× improvement over v1). Limitation: 500-n-gram
sample missed many corpus n-grams (~0.4% coverage of ~117k).

52c-v3 tests: does EXHAUSTIVE (all corpus 4-grams) lift the signal further?
Per R-RBS-LM-46b's success with hierarchical bundles of thousands of byte
observations, the D/log₂(D) heuristic SNR limit isn't a hard ceiling.

Also try n=5 for longer canonical phrases ("nel mezzo del cammin di nostra"
is a 6-gram at raw token granularity).
"""

import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

import srmech
from srmech.amsc.laplacian import dense_laplacian, hermitian_eigendecompose
from srmech.amsc.hdc import bundle, similarity, bind, permute
from srmech.signal_processing import mint_vector


HERE = Path(__file__).parent
DANTE_PATH = Path("/tmp/dante_italian.txt")


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
    raw = re.findall(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’]*[A-Za-zÀ-ÿ]|[A-Za-zÀ-ÿ]", text)
    return [t.lower().replace("’", "'") for t in raw if len(t) >= 1]


def tokenize_italian_filtered(text):
    return [t for t in tokenize_italian_raw(text) if t not in STOPWORDS_IT and len(t) >= 2]


def strip_gutenberg(text):
    s = re.search(r"\*\*\* START OF (THE )?PROJECT GUTENBERG", text)
    e = re.search(r"\*\*\* END OF (THE )?PROJECT GUTENBERG", text)
    if s:
        text = text[s.end():]
    if e:
        text = text[:e.start()]
    return text.strip()


def build_K1(filtered_tokens_per_section, K=33, M=21, vocab_size=200, window=5):
    all_tokens = [t for toks in filtered_tokens_per_section for t in toks]
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
    top_k = list(range(len(eigvals) - K, len(eigvals)))
    eigvec_hvs = []
    for k_idx in reversed(top_k):
        ev = eigvecs[:, k_idx]
        ms = ev * ev
        top = sorted(range(len(ev)), key=lambda i: -ms[i])[:M]
        eigvec_hvs.append(bundle([mint(vocab[i]) for i in top]))
    return bundle(eigvec_hvs), {"vocab_top_10": [(t, freq[t]) for t in vocab[:10]]}


def encode_K1(text):
    toks = tokenize_italian_filtered(text)
    return hierarchical_bundle([mint(t) for t in toks]) if toks else mint("__empty__")


def build_K3_exhaustive(raw_tokens_per_section, n_gram=4, position_stride=2731):
    """EXHAUSTIVE n-gram bundling (no sampling). All corpus n-grams contribute."""
    ngram_hvs = []
    n_total = 0
    for tokens in raw_tokens_per_section:
        for i in range(len(tokens) - n_gram + 1):
            ng = tokens[i:i + n_gram]
            hv = mint(ng[0])
            for k in range(1, n_gram):
                hv = bind(hv, permute(mint(ng[k]), k * position_stride))
            ngram_hvs.append(hv)
            n_total += 1
    instrument = hierarchical_bundle(ngram_hvs)
    return instrument, {"kernel": f"K3_n{n_gram}_exhaustive", "n_gram": n_gram,
                         "n_ngrams": n_total, "position_stride": position_stride}


def encode_K3(text, n_gram=4, position_stride=2731):
    toks = tokenize_italian_raw(text)
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


def main():
    print(f"=== R-RBS-LM-52c-v3: Dante exhaustive K3 (no sampling) ===\n")
    print(f"srmech: {srmech.__version__}")
    text = strip_gutenberg(DANTE_PATH.read_text(encoding="utf-8", errors="replace"))
    sections = [s for s in re.split(r'\n\s*(?:Inferno|Purgatorio|Paradiso)\s*•?\s*Canto\s+[IVXLCDM]+', text) if len(s) > 200]
    raw_t = [tokenize_italian_raw(s) for s in sections]
    filt_t = [tokenize_italian_filtered(s) for s in sections]
    print(f"Sections: {len(sections)}; raw tokens: {sum(len(t) for t in raw_t):,}")

    print("\n--- K1 (presence) ---")
    K1, K1_m = build_K1(filt_t)

    print("\n--- K3 n=4 EXHAUSTIVE ---")
    import time
    t0 = time.time()
    K3_4, K3_4_m = build_K3_exhaustive(raw_t, n_gram=4)
    print(f"  {K3_4_m}; built in {time.time()-t0:.1f}s")

    print("\n--- K3 n=5 EXHAUSTIVE ---")
    t0 = time.time()
    K3_5, K3_5_m = build_K3_exhaustive(raw_t, n_gram=5)
    print(f"  {K3_5_m}; built in {time.time()-t0:.1f}s")

    dante_probes = [
        "nel mezzo del cammin di nostra vita",
        "lasciate ogne speranza voi ch'intrate",
        "amor che move il sole",
        "ahi quanto a dir qual era",
        "nel mezzo del cammin",
        "selva oscura selvaggia aspra",
        "tre fiere lonza leone lupa",
        "lasciate ogne speranza voi",
        "amor che move il sole e l'altre stelle",
        "diritta via era smarrita",
        "anime triste peccato dolore",
        "cerchio peccatori inferno",
        "Beatrice Virgilio guida",
        "Caronte traghettatore anime",
        "purgatorio monte salita",
    ]
    neg_probes = [
        "spaghetti carbonara pomodoro fresco",
        "calcio domenica stadio partita",
        "macchina ferrari rossa veloce",
        "computer internet wifi password",
        "smartphone telefono batteria caricabatterie",
        "gelato cioccolato vaniglia limone",
        "treno milano roma napoli",
    ]

    paragraphs = []
    for s in sections[:30]:
        for p in re.split(r'\n\n+', s):
            if 50 < len(p) < 500:
                paragraphs.append(p)

    def baseline(enc, n=100):
        rng = random.Random(42)
        ss = [similarity(enc(a), enc(b)) for a, b in (rng.sample(paragraphs, 2) for _ in range(n))]
        m = sum(ss) / len(ss)
        sd = (sum((x - m) ** 2 for x in ss) / len(ss)) ** 0.5
        return {"mean": m, "std": sd, "max": max(ss), "min": min(ss)}

    b_K1 = baseline(encode_K1)
    b_K3_4 = baseline(lambda t: encode_K3(t, 4))
    b_K3_5 = baseline(lambda t: encode_K3(t, 5))
    print(f"\nBaselines:")
    print(f"  K1:   mean={b_K1['mean']:+.4f} std={b_K1['std']:.4f} max={b_K1['max']:+.4f}")
    print(f"  K3-4: mean={b_K3_4['mean']:+.4f} std={b_K3_4['std']:.4f} max={b_K3_4['max']:+.4f}")
    print(f"  K3-5: mean={b_K3_5['mean']:+.4f} std={b_K3_5['std']:.4f} max={b_K3_5['max']:+.4f}")

    def smoke(inst, enc, b, probes, kind):
        return [
            {"probe": p, "kind": kind, "sim": s, "z": (s - b["mean"]) / max(b["std"], 1e-9),
             "above_max": s > b["max"]}
            for p in probes for s in [similarity(enc(p), inst)]
        ]

    print(f"\n=== K1 ===")
    k1 = smoke(K1, encode_K1, b_K1, dante_probes, "dante") + smoke(K1, encode_K1, b_K1, neg_probes, "negative")
    for r in k1:
        f = "***" if r["above_max"] else "**" if r["z"] > 2 else "*" if r["z"] > 1 else ""
        print(f"  [{r['kind']:>8s}] {r['probe']:<48s} sim={r['sim']:+.4f} z={r['z']:+.2f} {f}")

    print(f"\n=== K3 n=4 EXHAUSTIVE ===")
    k3_4 = smoke(K3_4, lambda t: encode_K3(t, 4), b_K3_4, dante_probes, "dante") + \
           smoke(K3_4, lambda t: encode_K3(t, 4), b_K3_4, neg_probes, "negative")
    for r in k3_4:
        f = "***" if r["above_max"] else "**" if r["z"] > 2 else "*" if r["z"] > 1 else ""
        print(f"  [{r['kind']:>8s}] {r['probe']:<48s} sim={r['sim']:+.4f} z={r['z']:+.2f} {f}")

    print(f"\n=== K3 n=5 EXHAUSTIVE ===")
    k3_5 = smoke(K3_5, lambda t: encode_K3(t, 5), b_K3_5, dante_probes, "dante") + \
           smoke(K3_5, lambda t: encode_K3(t, 5), b_K3_5, neg_probes, "negative")
    for r in k3_5:
        f = "***" if r["above_max"] else "**" if r["z"] > 2 else "*" if r["z"] > 1 else ""
        print(f"  [{r['kind']:>8s}] {r['probe']:<48s} sim={r['sim']:+.4f} z={r['z']:+.2f} {f}")

    # Smoothie max
    print(f"\n=== Smoothie max(K1, K3-4, K3-5) ===")
    sm = []
    for kind, probes in [("dante", dante_probes), ("negative", neg_probes)]:
        for p in probes:
            s1 = similarity(encode_K1(p), K1)
            z1 = (s1 - b_K1["mean"]) / max(b_K1["std"], 1e-9)
            s4 = similarity(encode_K3(p, 4), K3_4)
            z4 = (s4 - b_K3_4["mean"]) / max(b_K3_4["std"], 1e-9)
            s5 = similarity(encode_K3(p, 5), K3_5)
            z5 = (s5 - b_K3_5["mean"]) / max(b_K3_5["std"], 1e-9)
            mx = max(z1, z4, z5)
            ab = (s1 > b_K1["max"]) or (s4 > b_K3_4["max"]) or (s5 > b_K3_5["max"])
            sm.append({"probe": p, "kind": kind, "z_K1": z1, "z_K3_4": z4,
                        "z_K3_5": z5, "max_z": mx, "above_max": ab})
    for r in sm:
        f = "***" if r["above_max"] else "**" if r["max_z"] > 2 else "*" if r["max_z"] > 1 else ""
        print(f"  [{r['kind']:>8s}] {r['probe']:<48s} K1={r['z_K1']:+.2f} K3-4={r['z_K3_4']:+.2f} K3-5={r['z_K3_5']:+.2f} max={r['max_z']:+.2f} {f}")

    # Summary
    def summ(rs, label, z_key="z"):
        ds = [r for r in rs if r["kind"] == "dante"]
        negs = [r for r in rs if r["kind"] == "negative"]
        return {"label": label, "nd": len(ds), "nn": len(negs),
                "d_above_max": sum(1 for r in ds if r["above_max"]),
                "d_z2": sum(1 for r in ds if r[z_key] > 2),
                "d_z1": sum(1 for r in ds if r[z_key] > 1),
                "neg_above_max": sum(1 for r in negs if r["above_max"]),
                "d_peak": max((r[z_key] for r in ds), default=0)}

    summary = [
        summ(k1, "K1_alone"),
        summ(k3_4, "K3_n4_exhaustive"),
        summ(k3_5, "K3_n5_exhaustive"),
        summ(sm, "smoothie_max", "max_z"),
    ]
    print(f"\n\n{'='*72}\n=== R-RBS-LM-52c-v3 summary\n{'='*72}\n")
    print(f"  {'kernel':<20s} {'D above_max':>13s} {'D z>2':>7s} {'D z>1':>7s} {'D peak':>8s} {'NEG ab_max':>12s}")
    for s in summary:
        print(f"  {s['label']:<20s} {s['d_above_max']:>4d}/{s['nd']:<6d} {s['d_z2']:>3d}/{s['nd']:<3d} {s['d_z1']:>3d}/{s['nd']:<3d} {s['d_peak']:>8.2f} {s['neg_above_max']:>3d}/{s['nn']:<8d}")

    print(f"\n=== vs 52c-v2 ===")
    print(f"  v2 K3 n=4 peak: 1.79; v3 K3 n=4 (exhaustive) peak: {summary[1]['d_peak']:.2f}")
    print(f"  v3 NEW: K3 n=5 (exhaustive) peak: {summary[2]['d_peak']:.2f}")

    out = {"partition": "R-RBS-LM-52c-v3", "summary": summary,
           "K3_n4_meta": K3_4_m, "K3_n5_meta": K3_5_m,
           "baselines": {"K1": b_K1, "K3_n4": b_K3_4, "K3_n5": b_K3_5},
           "K1_results": k1, "K3_n4_results": k3_4, "K3_n5_results": k3_5,
           "smoothie_results": sm}
    (HERE / "R-RBS-LM-52c_v3_results.json").write_text(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
