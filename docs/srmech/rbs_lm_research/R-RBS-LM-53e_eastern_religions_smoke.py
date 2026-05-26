"""R-RBS-LM-53e — Eastern religious texts added to the form-category matrix.

Per user direction 2026-05-26 (auto-queue): add Bhagavad Gita +
Tao Te Ching + Dhammapada (Buddhist) to 53's cross-religion matrix.

Tests: do Eastern religious texts cluster with Abrahamic on form-category,
OR form their own form-family? Predictions:
  - If single religious-form-category: all 6 texts ≈ same form
    (substrate-family is "religious-scripture-English-translation")
  - If two form-families (Abrahamic vs Eastern): off-diagonal within
    each family should fire stronger than across families

Same harness pattern as R-RBS-LM-53; just 3 more corpora added.
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
    "quran_sale":   {"path": "/tmp/quran_yusuf_ali.txt",       "label": "Quran (Sale 1734)",    "family": "abrahamic"},
    "kjv_ot":       {"path": "/tmp/kjv_old_testament.txt",     "label": "KJV Old Testament",    "family": "abrahamic"},
    "kjv_nt":       {"path": "/tmp/kjv_new_testament.txt",     "label": "KJV New Testament",    "family": "abrahamic"},
    "bhagavad_gita":{"path": "/tmp/bhagavad_gita.txt",         "label": "Bhagavad Gita (Arnold)","family": "eastern"},
    "tao_te_ching": {"path": "/tmp/tao_te_ching.txt",          "label": "Tao Te Ching (Legge)", "family": "eastern"},
    "dhammapada":   {"path": "/tmp/dhammapada.txt",            "label": "Dhammapada (Müller)",  "family": "eastern"},
}

PROBES = {
    "quran": [
        "Allah is one God", "Muhammad messenger", "Mecca pilgrimage", "Day of Judgment",
        "merciful most gracious", "Surah Fatihah", "fasting Ramadan",
    ],
    "judaism": [
        "In the beginning God created", "Moses Egypt deliverance", "ten commandments tablets",
        "promised land", "Psalm David Lord", "covenant Abraham", "burnt offerings altar",
    ],
    "christianity": [
        "Jesus Christ Lord", "Sermon on the Mount", "Last Supper bread wine",
        "love thy neighbor", "Holy Spirit Pentecost", "twelve apostles disciples",
        "kingdom of heaven",
    ],
    "hindu": [
        "Krishna Arjuna chariot", "Bhagavad Gita dharma", "atman soul self",
        "Brahman ultimate reality", "karma yoga action", "moksha liberation",
        "self knowledge realization",
    ],
    "taoist": [
        "Tao that can be named", "wu wei effortless action", "yin yang balance",
        "sage who knows acts", "water yields strong", "ten thousand things",
        "Tao Te Ching virtue",
    ],
    "buddhist": [
        "Buddha noble truths", "suffering desire attachment", "eightfold path",
        "nirvana enlightenment", "compassion wisdom mindfulness", "monk meditation",
        "Dhammapada verses doctrine",
    ],
    "negative": [
        "chocolate ice cream", "professional soccer", "computer programming",
        "smartphone battery", "vintage automobile", "gourmet kitchen",
        "weather forecast cloudy",
    ],
}

PROBE_TO_CORPUS = {
    "quran": "quran_sale", "judaism": "kjv_ot", "christianity": "kjv_nt",
    "hindu": "bhagavad_gita", "taoist": "tao_te_ching", "buddhist": "dhammapada",
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


def tokenize_raw(text):
    raw = re.findall(r"[A-Za-z][A-Za-z0-9'-]*[A-Za-z0-9]|[A-Za-z]", text)
    return [t.lower() for t in raw if len(t) >= 1]


def tokenize_filtered(text):
    return [t for t in tokenize_raw(text) if t not in STOPWORDS_EN and len(t) >= 2]


def strip_gutenberg(text):
    s = re.search(r"\*\*\* START OF (THE )?PROJECT GUTENBERG", text)
    e = re.search(r"\*\*\* END OF (THE )?PROJECT GUTENBERG", text)
    if s:
        text = text[s.end():]
    if e:
        text = text[:e.start()]
    return text.strip()


def chunk_text(text, n_chunks=64):
    raw_chunks = re.split(r"\n\s*\n+", text)
    out, cur, cur_size = [], [], 0
    target = max(len(text) // n_chunks, 1000)
    for c in raw_chunks:
        cur.append(c); cur_size += len(c)
        if cur_size >= target:
            out.append("\n".join(cur)); cur = []; cur_size = 0
    if cur:
        out.append("\n".join(cur))
    return out


def build_K1(filtered_tok_chunks, K=33, M=21, vocab_size=200, window=5):
    all_tok = [t for toks in filtered_tok_chunks for t in toks]
    freq = Counter(all_tok)
    N = min(vocab_size, len(freq))
    vocab = [t for t, _ in freq.most_common(N)]
    vocab_idx = {t: i for i, t in enumerate(vocab)}
    edge_count = Counter()
    for tokens in filtered_tok_chunks:
        indexed = [vocab_idx[t] for t in tokens if t in vocab_idx]
        for i in range(len(indexed)):
            for j in range(i + 1, min(i + window, len(indexed))):
                a, b = indexed[i], indexed[j]
                if a == b: continue
                edge_count[(min(a, b), max(a, b))] += 1
    L = dense_laplacian(N, list(edge_count.keys()), [float(w) for w in edge_count.values()])
    eigvals, eigvecs = hermitian_eigendecompose(L)
    top = list(range(len(eigvals) - K, len(eigvals)))
    hvs = []
    for k_idx in reversed(top):
        ev = eigvecs[:, k_idx]; ms = ev * ev
        idx = sorted(range(len(ev)), key=lambda i: -ms[i])[:M]
        hvs.append(bundle([mint(vocab[i]) for i in idx]))
    return bundle(hvs), {"vocab_top_10": [(t, freq[t]) for t in vocab[:10]]}


def build_K3(raw_tok_chunks, n_gram=4, sample_n=500, stride=2731, seed=42):
    rng = random.Random(seed)
    all_ng = []
    for tokens in raw_tok_chunks:
        for i in range(len(tokens) - n_gram + 1):
            all_ng.append(tuple(tokens[i:i + n_gram]))
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
        ng = toks[i:i + n_gram]
        hv = mint(ng[0])
        for k in range(1, n_gram):
            hv = bind(hv, permute(mint(ng[k]), k * stride))
        hvs.append(hv)
    return hierarchical_bundle(hvs)


def main():
    print(f"=== R-RBS-LM-53e — Eastern religions added to form-category matrix ===\n")
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
        K1, _ = build_K1(filt)
        K3, _ = build_K3(raw)
        instruments[key] = {"K1": K1, "K3": K3, "family": info["family"]}
        paragraphs[key] = [c for c in re.split(r'\n\n+', text) if 50 < len(c) < 500]
        print(f"  {info['label']} ({info['family']}): {sum(len(t) for t in raw):,} tokens; built")

    print(f"\n--- Building baselines per corpus ---")
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

    # 6x6 matrix: each probe-set vs each corpus
    print(f"\n=== 6x6 PROBE × INSTRUMENT MATRIX ===\n")
    matrix = {}
    for probe_set in ["quran", "judaism", "christianity", "hindu", "taoist", "buddhist"]:
        target = PROBE_TO_CORPUS[probe_set]
        matrix[probe_set] = {}
        for corpus_key in instruments:
            K1_inst = instruments[corpus_key]["K1"]
            K3_inst = instruments[corpus_key]["K3"]
            b_K1 = baselines[corpus_key]["K1"]; b_K3 = baselines[corpus_key]["K3"]
            results = []
            for p in PROBES[probe_set]:
                s1 = similarity(encode_K1(p), K1_inst)
                z1 = (s1 - b_K1["mean"]) / max(b_K1["std"], 1e-9)
                s3 = similarity(encode_K3(p), K3_inst)
                z3 = (s3 - b_K3["mean"]) / max(b_K3["std"], 1e-9)
                mx = max(z1, z3)
                ab = (s1 > b_K1["max"]) or (s3 > b_K3["max"])
                results.append({"probe": p, "z_K1": z1, "z_K3": z3, "max_z": mx, "above_max": ab})
            matrix[probe_set][corpus_key] = results

    # Summary: 6x6 table
    def stats(results):
        return {"peak": max((r["max_z"] for r in results), default=0),
                "z2": sum(1 for r in results if r["max_z"] > 2),
                "above_max": sum(1 for r in results if r["above_max"])}

    # Negative controls
    print(f"\n--- Negative controls (modern-non-religious) ---")
    neg_results = {}
    for corpus_key in instruments:
        K1_inst = instruments[corpus_key]["K1"]; K3_inst = instruments[corpus_key]["K3"]
        b_K1 = baselines[corpus_key]["K1"]; b_K3 = baselines[corpus_key]["K3"]
        rs = []
        for p in PROBES["negative"]:
            s1 = similarity(encode_K1(p), K1_inst)
            z1 = (s1 - b_K1["mean"]) / max(b_K1["std"], 1e-9)
            s3 = similarity(encode_K3(p), K3_inst)
            z3 = (s3 - b_K3["mean"]) / max(b_K3["std"], 1e-9)
            mx = max(z1, z3)
            ab = (s1 > b_K1["max"]) or (s3 > b_K3["max"])
            rs.append({"probe": p, "max_z": mx, "above_max": ab})
        neg_results[corpus_key] = rs
        print(f"  {corpus_key}: above_max {sum(1 for r in rs if r['above_max'])}/7; peak z {max(r['max_z'] for r in rs):.2f}")

    # Matrix print
    print(f"\n\n{'='*100}\n=== R-RBS-LM-53e: 6 probe-sets × 6 corpora — peak z (z2 count)\n{'='*100}\n")
    corpora_order = ["quran_sale", "kjv_ot", "kjv_nt", "bhagavad_gita", "tao_te_ching", "dhammapada"]
    print(f"  {'probe-set':<15s} " + " ".join(f"{c[:12]:>13s}" for c in corpora_order))
    for probe_set in ["quran", "judaism", "christianity", "hindu", "taoist", "buddhist"]:
        target = PROBE_TO_CORPUS[probe_set]
        cells = []
        for ck in corpora_order:
            st = stats(matrix[probe_set][ck])
            tag = "[D]" if ck == target else "   "
            cells.append(f"{tag}{st['peak']:+5.2f}({st['z2']})")
        print(f"  {probe_set:<15s} " + " ".join(f"{c:>13s}" for c in cells))

    # Family-level: are Abrahamic and Eastern within-family more similar than cross-family?
    def family_avg(probe_family, corpus_family):
        rs = []
        for probe_set in PROBE_TO_CORPUS:
            if probe_family == "abrahamic" and probe_set in ("quran", "judaism", "christianity"):
                pass
            elif probe_family == "eastern" and probe_set in ("hindu", "taoist", "buddhist"):
                pass
            else:
                continue
            for ck in instruments:
                if instruments[ck]["family"] != corpus_family: continue
                if PROBE_TO_CORPUS[probe_set] == ck: continue  # exclude diagonal
                for r in matrix[probe_set][ck]:
                    rs.append(r["max_z"])
        return sum(rs) / max(len(rs), 1)

    diag_avg = sum(stats(matrix[ps][PROBE_TO_CORPUS[ps]])["peak"]
                    for ps in PROBE_TO_CORPUS) / 6
    abra_abra = family_avg("abrahamic", "abrahamic")
    abra_east = family_avg("abrahamic", "eastern")
    east_abra = family_avg("eastern", "abrahamic")
    east_east = family_avg("eastern", "eastern")

    print(f"\n=== Family analysis (avg max_z; off-diagonal only) ===")
    print(f"  Diagonal avg peak z (each probe vs own substrate): {diag_avg:.2f}")
    print(f"  Abrahamic probes vs Abrahamic corpora (off-diag): {abra_abra:.2f}")
    print(f"  Abrahamic probes vs Eastern corpora:               {abra_east:.2f}")
    print(f"  Eastern probes vs Abrahamic corpora:               {east_abra:.2f}")
    print(f"  Eastern probes vs Eastern corpora (off-diag):     {east_east:.2f}")

    same_family = (abra_abra + east_east) / 2
    cross_family = (abra_east + east_abra) / 2
    print(f"\n  Same-family off-diag avg: {same_family:.2f}")
    print(f"  Cross-family off-diag avg: {cross_family:.2f}")
    print(f"  Family-specificity ratio: {same_family / max(cross_family, 0.01):.2f}")

    if same_family > cross_family * 1.5:
        verdict = "TWO FORM-FAMILIES — Abrahamic and Eastern have DISTINCT form-signatures"
    elif same_family > cross_family * 1.1:
        verdict = "Weak family-distinction — slight Abrahamic vs Eastern form-difference"
    else:
        verdict = "SINGLE form-family — religious-scripture-English-translation form spans both Abrahamic and Eastern"
    print(f"\n  Verdict: {verdict}")

    # Negative-control aggregate
    neg_above = sum(1 for k in neg_results for r in neg_results[k] if r["above_max"])
    print(f"  Negative-control above_max across all corpora: {neg_above}/{6*7}")

    output = {
        "partition": "R-RBS-LM-53e",
        "srmech_version": srmech.__version__,
        "matrix": matrix,
        "neg_results": neg_results,
        "diagonal_avg_peak_z": round(diag_avg, 2),
        "same_family_off_diag_avg": round(same_family, 2),
        "cross_family_off_diag_avg": round(cross_family, 2),
        "family_specificity_ratio": round(same_family / max(cross_family, 0.01), 2),
        "verdict": verdict,
        "n_negatives_above_max": neg_above,
    }
    (HERE / "R-RBS-LM-53e_results.json").write_text(json.dumps(output, indent=2, default=str))
    print(f"\nResults: {HERE / 'R-RBS-LM-53e_results.json'}")


if __name__ == "__main__":
    main()
