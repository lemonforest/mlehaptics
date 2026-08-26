"""R-RBS-LM-53g — Secular-vs-religious form discrimination at scale.

Per user direction 2026-05-26 (auto-queue): tests whether cascade detects
form-category boundary between religious and secular content at scale.

7 corpora across form-categories:
  Religious: Quran (Sale), KJV-OT, KJV-NT
  Secular novel:    Frankenstein (Shelley 1818)
  Secular drama:    Shakespeare Complete Works
  Secular science:  Origin of Species (Darwin 1859)
  Secular philosophy: Republic (Plato; Jowett tr)

Probes from each form-category. Hypothesis per MFO §VII.6.20:
  - Form-category sub-clusters detectable (religious cluster; secular
    sub-cluster by sub-genre)
  - But within-category substrate-rank inaccessible (KJV vs Shelley
    is a category-distinction; Shakespeare vs Plato is sub-category)
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

CORPORA = {
    "quran_sale":  {"path": "/tmp/quran_yusuf_ali.txt",   "category": "religious", "subcat": "religious"},
    "kjv_ot":      {"path": "/tmp/kjv_old_testament.txt", "category": "religious", "subcat": "religious"},
    "kjv_nt":      {"path": "/tmp/kjv_new_testament.txt", "category": "religious", "subcat": "religious"},
    "shakespeare": {"path": "/tmp/shakespeare.txt",       "category": "secular",   "subcat": "drama"},
    "origin":      {"path": "/tmp/origin_species.txt",    "category": "secular",   "subcat": "science"},
    "frankenstein":{"path": "/tmp/frankenstein.txt",      "category": "secular",   "subcat": "novel"},
    "plato":       {"path": "/tmp/plato_republic.txt",    "category": "secular",   "subcat": "philosophy"},
}

PROBES = {
    "religious": [
        "Allah is one God merciful",
        "Lord God almighty maker heaven",
        "Jesus Christ savior gospel",
        "covenant Abraham faith",
        "Sermon on the Mount blessed",
        "scripture revealed prophet",
        "soul eternal salvation",
    ],
    "drama_shakespeare": [
        "thee forsooth gentleman",
        "stage exit enter",
        "to be or not to be",
        "love beloved beauty",
        "kingdom honor crown",
        "death tragic murder villain",
        "act scene speak doth",
    ],
    "science_darwin": [
        "species variation selection",
        "natural selection adaptation",
        "geographical distribution organisms",
        "fossil record geological",
        "common descent ancestor",
        "instinct behavior animal",
        "competition resources environment",
    ],
    "novel_gothic": [
        "monster creature horror",
        "creator scientist experiment",
        "lonely sorrow despair",
        "wild storm mountains",
        "letter brother sister",
        "secret dark fearful",
        "death loss grief mourning",
    ],
    "philosophy_plato": [
        "justice virtue good",
        "Socrates dialogue ask",
        "city state guardian rulers",
        "soul reason intellect",
        "knowledge ignorance truth",
        "forms ideals reality",
        "republic ideal philosophical",
    ],
    "modern_negative": [
        "smartphone wifi battery",
        "computer programming Python",
        "professional soccer match",
        "chocolate ice cream sundae",
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
    print(f"=== R-RBS-LM-53g — Secular vs religious at scale ===\n")
    print(f"srmech: {srmech.__version__}")
    instruments, paragraphs = {}, {}
    for key, info in CORPORA.items():
        p = Path(info["path"])
        if not p.exists():
            print(f"  MISSING: {p}"); continue
        text = strip_gutenberg(p.read_text(encoding="utf-8", errors="replace"))
        chunks = chunk_text(text)
        raw = [tokenize_raw(c) for c in chunks]
        filt = [tokenize_filtered(c) for c in chunks]
        K1, K1_m = build_K1(filt)
        K3, K3_m = build_K3(raw)
        instruments[key] = {"K1": K1, "K3": K3, "category": info["category"], "subcat": info["subcat"]}
        paragraphs[key] = [c for c in re.split(r'\n\n+', text) if 50 < len(c) < 500]
        print(f"  {key:<15s} ({info['subcat']:<12s}): {sum(len(t) for t in raw):,} tokens; "
              f"top tokens: {[t for t,_ in K1_m['vocab_top_10'][:5]]}")

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

    # 5 probe categories × 7 corpora matrix
    print(f"\n=== Probe × instrument matrix ===\n")
    matrix = {}
    for probe_set in ["religious", "drama_shakespeare", "science_darwin",
                       "novel_gothic", "philosophy_plato"]:
        matrix[probe_set] = {}
        for ck in instruments:
            K1_inst = instruments[ck]["K1"]; K3_inst = instruments[ck]["K3"]
            b_K1 = baselines[ck]["K1"]; b_K3 = baselines[ck]["K3"]
            rs = []
            for p in PROBES[probe_set]:
                s1 = similarity(encode_K1(p), K1_inst)
                z1 = (s1 - b_K1["mean"]) / max(b_K1["std"], 1e-9)
                s3 = similarity(encode_K3(p), K3_inst)
                z3 = (s3 - b_K3["mean"]) / max(b_K3["std"], 1e-9)
                mx = max(z1, z3)
                ab = (s1 > b_K1["max"]) or (s3 > b_K3["max"])
                rs.append({"probe": p, "z_K1": z1, "z_K3": z3, "max_z": mx, "above_max": ab})
            matrix[probe_set][ck] = rs

    # Print matrix
    print(f"  {'probe / corpus':<22s} " + " ".join(f"{k[:11]:>12s}" for k in instruments))
    for probe_set, row in matrix.items():
        cells = []
        for ck in instruments:
            peaks = [r["max_z"] for r in row[ck]]
            pk = max(peaks)
            z2 = sum(1 for x in peaks if x > 2)
            cells.append(f"{pk:+5.2f}({z2})")
        print(f"  {probe_set:<22s} " + " ".join(f"{c:>12s}" for c in cells))

    # Negative controls
    neg_results = {}
    for ck in instruments:
        K1_inst = instruments[ck]["K1"]; K3_inst = instruments[ck]["K3"]
        b_K1 = baselines[ck]["K1"]; b_K3 = baselines[ck]["K3"]
        rs = []
        for p in PROBES["modern_negative"]:
            s1 = similarity(encode_K1(p), K1_inst)
            z1 = (s1 - b_K1["mean"]) / max(b_K1["std"], 1e-9)
            s3 = similarity(encode_K3(p), K3_inst)
            z3 = (s3 - b_K3["mean"]) / max(b_K3["std"], 1e-9)
            mx = max(z1, z3)
            ab = (s1 > b_K1["max"]) or (s3 > b_K3["max"])
            rs.append({"probe": p, "max_z": mx, "above_max": ab})
        neg_results[ck] = rs

    # Category analysis: do religious probes fire on religious corpora more than secular?
    def avg_in_class(probe_set, category):
        sims = []
        for ck in instruments:
            if instruments[ck]["category"] == category:
                for r in matrix[probe_set][ck]:
                    sims.append(r["max_z"])
        return sum(sims) / max(len(sims), 1)

    print(f"\n=== Category averages (avg peak z per probe-set per category) ===")
    print(f"  {'probe-set':<22s} {'vs religious':>14s} {'vs secular':>12s} {'specificity':>14s}")
    for probe_set in matrix:
        rel = avg_in_class(probe_set, "religious")
        sec = avg_in_class(probe_set, "secular")
        ratio = (max(rel, 0.0001) / max(sec, 0.0001)) if probe_set == "religious" else (max(sec, 0.0001) / max(rel, 0.0001))
        # The probe's preferred class:
        pref = "religious" if rel > sec else "secular"
        print(f"  {probe_set:<22s} {rel:>+14.2f} {sec:>+12.2f}  pref={pref:>9s} ratio={ratio:.2f}")

    # Sub-category test: does novel_gothic probe fire harder on Frankenstein than Shakespeare?
    print(f"\n=== Sub-category test (probe set's preferred secular sub-corpus) ===")
    for probe_set in ["drama_shakespeare", "science_darwin", "novel_gothic", "philosophy_plato"]:
        peak_per_corpus = {ck: max(r["max_z"] for r in matrix[probe_set][ck])
                            for ck in instruments if instruments[ck]["category"] == "secular"}
        best = max(peak_per_corpus.items(), key=lambda x: x[1])
        print(f"  {probe_set:<22s} → best secular: {best[0]:<14s} (z={best[1]:+.2f})")

    # Negative control aggregate
    neg_above = sum(1 for ck in neg_results for r in neg_results[ck] if r["above_max"])
    print(f"\n  Negative-control above_max: {neg_above}/{7*4} ({100*neg_above/(7*4):.0f}%)")

    output = {
        "partition": "R-RBS-LM-53g",
        "srmech_version": srmech.__version__,
        "matrix": matrix,
        "neg_results": neg_results,
        "category_averages": {
            ps: {"vs_religious": avg_in_class(ps, "religious"),
                 "vs_secular": avg_in_class(ps, "secular")}
            for ps in matrix
        },
    }
    (HERE / "R-RBS-LM-53g_results.json").write_text(json.dumps(output, indent=2, default=str))


if __name__ == "__main__":
    main()
