"""R-RBS-LM-53f — Translation stability matrix.

Tests how much of the form-signature is preserved across translators of
the SAME source. Per MFO §VII.6.20: cascade reads form of the
translation, not substrate of the original. So translations should
show RECOGNIZABLE but NOT IDENTICAL form-signatures.

Pairs available:
  - Quran: Sale 1734 (PG 7440) vs Rodwell 1861 (PG 3434)
  - Bhagavad Gita: Arnold 1885 only (single translation in our set)
  - KJV: only PG 10 (single)

Test: encode Quran-Sale and Quran-Rodwell separately; build K1 + K3
each; cross-match. Predictions:
  - Sale vs Rodwell K1 similarity: HIGH (same source, English-target,
    similar concept-set) but NOT 1.0
  - Sale-probes fire on Rodwell instrument (z >> 1)
  - Sale ≠ Rodwell at K3 level: translator-specific arrangement
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

# Translation pairs of the same source (Quran has two PG-available English
# translations 127 years apart; serves as our test pair)
TRANSLATIONS = {
    "quran_sale_1734":   {"path": "/tmp/quran_yusuf_ali.txt",  "source": "Quran", "translator": "George Sale 1734"},
    "quran_rodwell_1861":{"path": "/tmp/rodwell_quran.txt",    "source": "Quran", "translator": "J.M. Rodwell 1861"},
    # Comparison: another religious text by different content, to be a true negative
    "kjv_nt":            {"path": "/tmp/kjv_new_testament.txt", "source": "Christian NT", "translator": "KJV 1611"},
}

PROBES = {
    "quran": [
        "Allah merciful most gracious", "messenger of God Mohammed", "Day of Judgment paradise",
        "fasting Ramadan", "infidels unbelievers", "alms charity zakat",
        "Surah opening Bismillah",
    ],
    "christian": [
        "Jesus Christ Lord savior", "Holy Spirit Pentecost", "Sermon on the Mount",
        "Last Supper bread wine", "kingdom of heaven parable", "twelve apostles disciples",
        "Paul epistles letters",
    ],
    "negative": [
        "chocolate ice cream", "professional soccer", "computer programming",
        "smartphone battery", "vintage automobile", "gourmet pasta kitchen",
        "modern weather forecast",
    ],
}


STOPWORDS_EN = set("""
the a an and or but if then else of in on at to for with by from as is are
was were be been being have has had having do does did doing done will
would shall should may might can could not no this that these those it its
they them their there here he she we us our you your i me my mine yours
which what who whom whose where when why how all any some none many much
more most less few several each every both either neither so such only also
than just too very much such etc ie eg via vs per pre post sub super
o which thee thou thy ye us our hath shall
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


def tokenize_raw(text):
    return [t.lower() for t in re.findall(r"[A-Za-z][A-Za-z0-9'-]*[A-Za-z0-9]|[A-Za-z]", text) if len(t) >= 1]


def tokenize_filtered(text):
    return [t for t in tokenize_raw(text) if t not in STOPWORDS_EN and len(t) >= 2]


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


def build_K1(filt_chunks, K=33, M=21, vocab_size=200, window=5):
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
    ev, evc = hermitian_eigendecompose(L)
    top = list(range(len(ev) - K, len(ev)))
    hvs = []
    for k in reversed(top):
        x = evc[:, k]; ms = x * x
        idx = sorted(range(len(x)), key=lambda i: -ms[i])[:M]
        hvs.append(bundle([mint(vocab[i]) for i in idx]))
    return bundle(hvs), {"vocab_top_10": [(t, freq[t]) for t in vocab[:10]]}


def build_K3(raw_chunks, n_gram=4, sample_n=500, stride=2731, seed=42):
    rng = random.Random(seed)
    all_ng = []
    for toks in raw_chunks:
        for i in range(len(toks) - n_gram + 1):
            all_ng.append(tuple(toks[i:i+n_gram]))
    if len(all_ng) > sample_n:
        all_ng = rng.sample(all_ng, sample_n)
    hvs = []
    for ng in all_ng:
        hv = mint(ng[0])
        for k in range(1, n_gram):
            hv = bind(hv, permute(mint(ng[k]), k * stride))
        hvs.append(hv)
    return hierarchical_bundle(hvs), {"n_sampled": len(all_ng)}


def encode_K1(text):
    toks = tokenize_filtered(text)
    return hierarchical_bundle([mint(t) for t in toks]) if toks else mint("__empty__")


def encode_K3(text, n_gram=4, stride=2731):
    toks = tokenize_raw(text)
    if len(toks) < n_gram: return mint("__short__")
    hvs = []
    for i in range(len(toks) - n_gram + 1):
        ng = toks[i:i+n_gram]
        hv = mint(ng[0])
        for k in range(1, n_gram):
            hv = bind(hv, permute(mint(ng[k]), k * stride))
        hvs.append(hv)
    return hierarchical_bundle(hvs)


def main():
    print(f"=== R-RBS-LM-53f — Translation stability matrix ===\n")
    print(f"srmech: {srmech.__version__}")
    instruments, paragraphs = {}, {}
    for key, info in TRANSLATIONS.items():
        p = Path(info["path"])
        if not p.exists():
            print(f"  MISSING: {p}"); continue
        text = strip_gutenberg(p.read_text(encoding="utf-8", errors="replace"))
        chunks = chunk_text(text)
        raw = [tokenize_raw(c) for c in chunks]
        filt = [tokenize_filtered(c) for c in chunks]
        K1, _ = build_K1(filt)
        K3, _ = build_K3(raw)
        instruments[key] = {"K1": K1, "K3": K3, "source": info["source"], "translator": info["translator"]}
        paragraphs[key] = [c for c in re.split(r'\n\n+', text) if 50 < len(c) < 500]
        print(f"  {info['source']} ({info['translator']}): {sum(len(t) for t in raw):,} tokens; built")

    baselines = {}
    for k in instruments:
        paras = paragraphs[k]
        rng = random.Random(42)
        def bl(enc, n=80):
            ss = [similarity(enc(a), enc(b))
                  for a, b in (rng.sample(paras, 2) for _ in range(n))]
            m = sum(ss) / len(ss)
            sd = (sum((x - m) ** 2 for x in ss) / len(ss)) ** 0.5
            return {"mean": m, "std": sd, "max": max(ss), "min": min(ss)}
        baselines[k] = {"K1": bl(encode_K1), "K3": bl(encode_K3)}

    # ===== TEST 1: Inter-instrument similarity =====
    # Direct K1-to-K1 similarity between two Quran translations vs Quran-Sale to KJV-NT
    print(f"\n=== TEST 1: Direct inter-instrument similarity ===")
    keys = list(instruments.keys())
    for i, k1 in enumerate(keys):
        for k2 in keys[i:]:
            sim_K1 = similarity(instruments[k1]["K1"], instruments[k2]["K1"])
            sim_K3 = similarity(instruments[k1]["K3"], instruments[k2]["K3"])
            label = "(SAME)" if k1 == k2 else "(same-source)" if instruments[k1]["source"] == instruments[k2]["source"] else "(diff-source)"
            print(f"  {k1:<24s} ↔ {k2:<24s} K1={sim_K1:+.4f}  K3={sim_K3:+.4f}  {label}")

    # ===== TEST 2: Probe matrix =====
    print(f"\n\n=== TEST 2: Probe matrix ===\n")
    matrix = {}
    for probe_set in ["quran", "christian"]:
        matrix[probe_set] = {}
        for ck in instruments:
            results = []
            K1_inst = instruments[ck]["K1"]
            K3_inst = instruments[ck]["K3"]
            b_K1 = baselines[ck]["K1"]; b_K3 = baselines[ck]["K3"]
            for p in PROBES[probe_set]:
                s1 = similarity(encode_K1(p), K1_inst)
                z1 = (s1 - b_K1["mean"]) / max(b_K1["std"], 1e-9)
                s3 = similarity(encode_K3(p), K3_inst)
                z3 = (s3 - b_K3["mean"]) / max(b_K3["std"], 1e-9)
                mx = max(z1, z3)
                ab = (s1 > b_K1["max"]) or (s3 > b_K3["max"])
                results.append({"probe": p, "z_K1": z1, "z_K3": z3, "max_z": mx, "above_max": ab})
            matrix[probe_set][ck] = results
            peaks = max(r["max_z"] for r in results)
            z2 = sum(1 for r in results if r["max_z"] > 2)
            print(f"  {probe_set:<10s} probes vs {ck:<24s} peak z={peaks:+.2f}  z>2: {z2}/{len(results)}")

    # ===== TEST 3: Cross-translation probe stability =====
    # Quran probes should fire on BOTH Sale and Rodwell — at similar magnitudes
    print(f"\n\n=== TEST 3: Quran probe stability across translations ===")
    quran_sale_peaks = [r["max_z"] for r in matrix["quran"]["quran_sale_1734"]]
    quran_rodwell_peaks = [r["max_z"] for r in matrix["quran"]["quran_rodwell_1861"]]
    print(f"  {'probe':<40s} {'Sale':>8s} {'Rodwell':>9s} {'delta':>8s}")
    for i, p in enumerate(PROBES["quran"]):
        d = quran_rodwell_peaks[i] - quran_sale_peaks[i]
        print(f"  {p:<40s} {quran_sale_peaks[i]:>+8.2f} {quran_rodwell_peaks[i]:>+9.2f} {d:>+8.2f}")
    avg_sale = sum(quran_sale_peaks) / len(quran_sale_peaks)
    avg_rod = sum(quran_rodwell_peaks) / len(quran_rodwell_peaks)
    print(f"  {'AVG':<40s} {avg_sale:>+8.2f} {avg_rod:>+9.2f} {avg_rod - avg_sale:>+8.2f}")

    # ===== Verdict =====
    sale_rod_sim = similarity(instruments["quran_sale_1734"]["K1"], instruments["quran_rodwell_1861"]["K1"])
    sale_kjv_sim = similarity(instruments["quran_sale_1734"]["K1"], instruments["kjv_nt"]["K1"])
    rod_kjv_sim = similarity(instruments["quran_rodwell_1861"]["K1"], instruments["kjv_nt"]["K1"])

    print(f"\n=== Verdict ===")
    print(f"  Sale ↔ Rodwell K1 similarity (same source):     {sale_rod_sim:+.4f}")
    print(f"  Sale ↔ KJV-NT K1 similarity (diff source):       {sale_kjv_sim:+.4f}")
    print(f"  Rodwell ↔ KJV-NT K1 similarity (diff source):    {rod_kjv_sim:+.4f}")
    ratio = sale_rod_sim / max(abs(sale_kjv_sim), 0.0001)
    print(f"  Translation-stability ratio (same/diff): {ratio:.2f}")

    if sale_rod_sim > sale_kjv_sim * 2 and sale_rod_sim > rod_kjv_sim * 2:
        verdict = "TRANSLATION STABILITY HIGH — same-source translations share form-signature; cross-source clearly distinct"
    elif sale_rod_sim > sale_kjv_sim and sale_rod_sim > rod_kjv_sim:
        verdict = "TRANSLATION STABILITY MODERATE — same-source signal detectable but cross-source signal also present"
    else:
        verdict = "TRANSLATION STABILITY LOW — translator dominates form-signature (substrate-form-leakage)"
    print(f"\n  Verdict: {verdict}")

    output = {
        "partition": "R-RBS-LM-53f",
        "srmech_version": srmech.__version__,
        "inter_instrument_K1": {
            "sale_rodwell": sale_rod_sim,
            "sale_kjv": sale_kjv_sim,
            "rodwell_kjv": rod_kjv_sim,
        },
        "translation_stability_ratio": round(ratio, 2),
        "matrix": matrix,
        "quran_probes_sale_peaks": quran_sale_peaks,
        "quran_probes_rodwell_peaks": quran_rodwell_peaks,
        "verdict": verdict,
    }
    (HERE / "R-RBS-LM-53f_results.json").write_text(json.dumps(output, indent=2, default=str))
    print(f"\nResults: {HERE / 'R-RBS-LM-53f_results.json'}")


if __name__ == "__main__":
    main()
