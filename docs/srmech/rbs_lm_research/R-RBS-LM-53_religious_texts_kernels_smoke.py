"""R-RBS-LM-53 — Religious texts kernels: Quran + KJV-OT + KJV-NT cross-matrix.

Per user direction 2026-05-26: *"now lets kernel major religious texts
because they are open and well studied. ... Start with the big 3, Islam,
Judaism, and Christianity. let's see if this is another good candidate for
auto queued tasks."*

Auto-queued pattern: one parameterized smoke loads all 3 corpora,
builds K1 + K3 instruments per corpus, runs probe-matrix against each.

Sources (all Project Gutenberg, public domain):
  - Quran: PG 7440 (George Sale 1734 English; despite "Yusuf Ali" PG metadata)
  - KJV Old Testament: extracted from PG 10 (lines 97-76405)
  - KJV New Testament: extracted from PG 10 (lines 76406-99971)

KJV-OT serves as proxy for Tanakh (same content; Christian translation;
caveat per MFO §VII.6.20 — form-claim not substrate-claim).

53d cross-matrix: each religion's probes tested against each religion's
instrument. Diagonal expected to fire (substrate-self); off-diagonal near
baseline (per epistemic ceiling — form distinct across substrates).
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
    "quran_sale": {
        "path": "/tmp/quran_yusuf_ali.txt",
        "label": "Quran (Sale 1734 English)",
    },
    "kjv_ot": {
        "path": "/tmp/kjv_old_testament.txt",
        "label": "KJV Old Testament (Tanakh proxy)",
    },
    "kjv_nt": {
        "path": "/tmp/kjv_new_testament.txt",
        "label": "KJV New Testament",
    },
}

# Probes per religious tradition — canonical phrases
PROBES = {
    "quran": [
        "Allah is one God",
        "Muhammad messenger of God",
        "Mecca pilgrimage Kaaba",
        "five pillars of faith",
        "Quran revelation Gabriel",
        "Day of Judgment paradise",
        "fasting Ramadan holy month",
        "merciful most gracious",
        "Surah Fatihah opening",
        "infidels unbelievers",
        "alms charity zakat",
        "prophet Mohammed teachings",
    ],
    "judaism": [
        "In the beginning God created",
        "Moses Egypt deliverance pharaoh",
        "ten commandments tablets stone",
        "promised land flowing milk honey",
        "Solomon's temple Jerusalem",
        "covenant Abraham Isaac Jacob",
        "Psalm David Lord shepherd",
        "Babylonian exile captivity",
        "prophet Isaiah Jeremiah",
        "burnt offerings altar priest",
        "manna desert wandering",
        "law of Moses statutes",
    ],
    "christianity": [
        "Jesus Christ Lord savior",
        "Sermon on the Mount blessed",
        "Last Supper bread wine",
        "Gethsemane prayer betrayal",
        "love thy neighbor as thyself",
        "blessed are the meek poor",
        "Holy Spirit Pentecost",
        "twelve apostles disciples",
        "kingdom of heaven parable",
        "crucifixion resurrection death",
        "good Samaritan parable",
        "Paul epistles letters churches",
    ],
    "negative": [
        "chocolate ice cream sundae",
        "professional soccer match",
        "computer programming Python",
        "smartphone notification battery",
        "tropical rainforest humidity",
        "vintage automobile classic",
        "gourmet kitchen recipes pasta",
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


def build_K1(filtered_token_chunks, K=33, M=21, vocab_size=200, window=5):
    all_tokens = [t for toks in filtered_token_chunks for t in toks]
    freq = Counter(all_tokens)
    N = min(vocab_size, len(freq))
    vocab = [t for t, _ in freq.most_common(N)]
    vocab_idx = {t: i for i, t in enumerate(vocab)}
    edge_count = Counter()
    for tokens in filtered_token_chunks:
        indexed = [vocab_idx[t] for t in tokens if t in vocab_idx]
        for i in range(len(indexed)):
            for j in range(i + 1, min(i + window, len(indexed))):
                a, b = indexed[i], indexed[j]
                if a == b:
                    continue
                edge_count[(min(a, b), max(a, b))] += 1
    L = dense_laplacian(N, list(edge_count.keys()),
                        [float(w) for w in edge_count.values()])
    eigvals, eigvecs = hermitian_eigendecompose(L)
    top = list(range(len(eigvals) - K, len(eigvals)))
    hvs = []
    for k_idx in reversed(top):
        ev = eigvecs[:, k_idx]
        ms = ev * ev
        idx = sorted(range(len(ev)), key=lambda i: -ms[i])[:M]
        hvs.append(bundle([mint(vocab[i]) for i in idx]))
    return bundle(hvs), {"vocab_top_15": [(t, freq[t]) for t in vocab[:15]],
                         "vocab_size": N, "n_edges": len(edge_count)}


def build_K3(raw_token_chunks, n_gram=4, sample_n=500, position_stride=2731,
             seed=42):
    rng = random.Random(seed)
    all_ngrams = []
    for tokens in raw_token_chunks:
        for i in range(len(tokens) - n_gram + 1):
            all_ngrams.append(tuple(tokens[i:i + n_gram]))
    if len(all_ngrams) > sample_n:
        all_ngrams = rng.sample(all_ngrams, sample_n)
    hvs = []
    for ng in all_ngrams:
        hv = mint(ng[0])
        for k in range(1, n_gram):
            hv = bind(hv, permute(mint(ng[k]), k * position_stride))
        hvs.append(hv)
    return hierarchical_bundle(hvs), {"n_ngrams_corpus": sum(max(len(t) - n_gram + 1, 0) for t in raw_token_chunks),
                                       "n_sampled": len(all_ngrams)}


def encode_K1(text):
    toks = tokenize_filtered(text)
    return hierarchical_bundle([mint(t) for t in toks]) if toks else mint("__empty__")


def encode_K3(text, n_gram=4, position_stride=2731):
    toks = tokenize_raw(text)
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


def chunk_text(text, n_chunks=64):
    """Split long text into chunks for K1 cooccurrence."""
    raw_chunks = re.split(r"\n\s*\n+", text)
    out = []
    cur = []
    target = max(len(text) // n_chunks, 1000)
    cur_size = 0
    for c in raw_chunks:
        cur.append(c)
        cur_size += len(c)
        if cur_size >= target:
            out.append("\n".join(cur))
            cur = []
            cur_size = 0
    if cur:
        out.append("\n".join(cur))
    return out


def main():
    print(f"=== R-RBS-LM-53 — religious texts kernels (3-corpus matrix) ===\n")
    print(f"srmech: {srmech.__version__}")

    instruments = {}  # key → {"K1": bytes, "K3": bytes, "K1_meta": ..., "K3_meta": ...}
    paragraphs_by_corpus = {}

    for key, info in CORPORA.items():
        p = Path(info["path"])
        if not p.exists():
            print(f"  MISSING: {p}")
            continue
        raw = p.read_text(encoding="utf-8", errors="replace")
        text = strip_gutenberg(raw)
        chunks = chunk_text(text)
        raw_toks = [tokenize_raw(c) for c in chunks]
        filt_toks = [tokenize_filtered(c) for c in chunks]
        n_raw = sum(len(t) for t in raw_toks)
        n_filt = sum(len(t) for t in filt_toks)
        print(f"\n--- {info['label']} ({key}) ---")
        print(f"  chars: {len(text):,}; chunks: {len(chunks)}; tokens: raw {n_raw:,} filtered {n_filt:,}")

        K1, K1_m = build_K1(filt_toks)
        K3, K3_m = build_K3(raw_toks)
        print(f"  K1 vocab_top_10: {K1_m['vocab_top_15'][:10]}")
        print(f"  K3: {K3_m['n_ngrams_corpus']:,} corpus 4-grams; {K3_m['n_sampled']} sampled")
        instruments[key] = {"K1": K1, "K3": K3, "K1_meta": K1_m, "K3_meta": K3_m}

        paras = [c for c in re.split(r'\n\n+', text) if 50 < len(c) < 500]
        paragraphs_by_corpus[key] = paras

    # Baselines per corpus + kernel
    print(f"\n=== Baselines ===")
    baselines = {}
    for key in instruments:
        paras = paragraphs_by_corpus[key]
        rng = random.Random(42)

        def bl(enc, n=80):
            ss = [similarity(enc(a), enc(b))
                  for a, b in (rng.sample(paras, 2) for _ in range(n))]
            m = sum(ss) / len(ss)
            sd = (sum((x - m) ** 2 for x in ss) / len(ss)) ** 0.5
            return {"mean": m, "std": sd, "max": max(ss), "min": min(ss)}

        baselines[key] = {"K1": bl(encode_K1), "K3": bl(encode_K3)}
        b = baselines[key]
        print(f"  {key}:")
        print(f"    K1: mean={b['K1']['mean']:+.4f} std={b['K1']['std']:.4f} max={b['K1']['max']:+.4f}")
        print(f"    K3: mean={b['K3']['mean']:+.4f} std={b['K3']['std']:.4f} max={b['K3']['max']:+.4f}")

    # ===== Diagonal: each religion's probes against its OWN instrument =====
    print(f"\n\n{'='*72}\n=== DIAGONAL — each probe-set vs OWN instrument\n{'='*72}\n")
    diagonal_results = {}

    PROBE_TO_CORPUS = {"quran": "quran_sale", "judaism": "kjv_ot",
                        "christianity": "kjv_nt"}

    for probe_set, corpus_key in PROBE_TO_CORPUS.items():
        if corpus_key not in instruments:
            continue
        K1_inst = instruments[corpus_key]["K1"]
        K3_inst = instruments[corpus_key]["K3"]
        b_K1 = baselines[corpus_key]["K1"]
        b_K3 = baselines[corpus_key]["K3"]
        print(f"\n--- {probe_set} probes vs {corpus_key} instrument ---")
        results = []
        for p in PROBES[probe_set]:
            s1 = similarity(encode_K1(p), K1_inst)
            z1 = (s1 - b_K1["mean"]) / max(b_K1["std"], 1e-9)
            s3 = similarity(encode_K3(p), K3_inst)
            z3 = (s3 - b_K3["mean"]) / max(b_K3["std"], 1e-9)
            mx = max(z1, z3)
            ab1 = s1 > b_K1["max"]; ab3 = s3 > b_K3["max"]
            results.append({"probe": p, "z_K1": z1, "z_K3": z3, "max_z": mx,
                             "above_max": ab1 or ab3})
            flag = "***" if (ab1 or ab3) else "**" if mx > 2 else "*" if mx > 1 else ""
            print(f"  {p:<42s} K1={z1:+.2f} K3={z3:+.2f} max={mx:+.2f} {flag}")
        diagonal_results[probe_set] = results

    # ===== Negative controls vs each instrument =====
    print(f"\n\n{'='*72}\n=== NEGATIVE CONTROLS (modern non-religious topics)\n{'='*72}\n")
    negative_per_corpus = {}
    for corpus_key in instruments:
        K1_inst = instruments[corpus_key]["K1"]
        K3_inst = instruments[corpus_key]["K3"]
        b_K1 = baselines[corpus_key]["K1"]
        b_K3 = baselines[corpus_key]["K3"]
        print(f"\n--- vs {corpus_key} instrument ---")
        results = []
        for p in PROBES["negative"]:
            s1 = similarity(encode_K1(p), K1_inst)
            z1 = (s1 - b_K1["mean"]) / max(b_K1["std"], 1e-9)
            s3 = similarity(encode_K3(p), K3_inst)
            z3 = (s3 - b_K3["mean"]) / max(b_K3["std"], 1e-9)
            mx = max(z1, z3)
            ab1 = s1 > b_K1["max"]; ab3 = s3 > b_K3["max"]
            results.append({"probe": p, "z_K1": z1, "z_K3": z3, "max_z": mx,
                             "above_max": ab1 or ab3})
            flag = "***" if (ab1 or ab3) else "**" if mx > 2 else "*" if mx > 1 else ""
            print(f"  {p:<42s} K1={z1:+.2f} K3={z3:+.2f} max={mx:+.2f} {flag}")
        negative_per_corpus[corpus_key] = results

    # ===== Cross-religion matrix: each probe-set vs OTHER religions =====
    print(f"\n\n{'='*72}\n=== CROSS-RELIGION MATRIX (off-diagonal — form vs substrate test)\n{'='*72}\n")
    cross_matrix = {}
    for probe_set in ["quran", "judaism", "christianity"]:
        cross_matrix[probe_set] = {}
        for corpus_key in instruments:
            target_corpus = PROBE_TO_CORPUS[probe_set]
            if corpus_key == target_corpus:
                continue  # this is the diagonal
            K1_inst = instruments[corpus_key]["K1"]
            K3_inst = instruments[corpus_key]["K3"]
            b_K1 = baselines[corpus_key]["K1"]
            b_K3 = baselines[corpus_key]["K3"]
            print(f"\n--- {probe_set} probes vs {corpus_key} ---")
            results = []
            for p in PROBES[probe_set]:
                s1 = similarity(encode_K1(p), K1_inst)
                z1 = (s1 - b_K1["mean"]) / max(b_K1["std"], 1e-9)
                s3 = similarity(encode_K3(p), K3_inst)
                z3 = (s3 - b_K3["mean"]) / max(b_K3["std"], 1e-9)
                mx = max(z1, z3)
                ab1 = s1 > b_K1["max"]; ab3 = s3 > b_K3["max"]
                results.append({"probe": p, "z_K1": z1, "z_K3": z3, "max_z": mx,
                                 "above_max": ab1 or ab3})
                flag = "***" if (ab1 or ab3) else "**" if mx > 2 else "*" if mx > 1 else ""
                print(f"  {p:<42s} K1={z1:+.2f} K3={z3:+.2f} max={mx:+.2f} {flag}")
            cross_matrix[probe_set][corpus_key] = results

    # ===== Summary table =====
    def summarize(results):
        return {
            "n": len(results),
            "above_max": sum(1 for r in results if r["above_max"]),
            "z2": sum(1 for r in results if r["max_z"] > 2),
            "z1": sum(1 for r in results if r["max_z"] > 1),
            "peak_z": max((r["max_z"] for r in results), default=0),
        }

    print(f"\n\n{'='*72}\n=== R-RBS-LM-53 SUMMARY: cross-religion 3x3 matrix\n{'='*72}\n")
    print(f"  {'probe / instrument':<28s} {'quran_sale':>11s} {'kjv_ot':>11s} {'kjv_nt':>11s} {'negative':>11s}")
    print(f"  {'-'*28} {'-'*11} {'-'*11} {'-'*11} {'-'*11}")

    table = {}
    for probe_set in ["quran", "judaism", "christianity"]:
        target = PROBE_TO_CORPUS[probe_set]
        row = {}
        for corpus_key in ["quran_sale", "kjv_ot", "kjv_nt"]:
            if corpus_key == target:
                results = diagonal_results[probe_set]
            else:
                results = cross_matrix[probe_set][corpus_key]
            row[corpus_key] = summarize(results)
        table[probe_set] = row
        # Format row
        cells = []
        for ck in ["quran_sale", "kjv_ot", "kjv_nt"]:
            s = row[ck]
            marker = " [own]" if ck == target else ""
            cells.append(f"z2={s['z2']:>2d}/12 pk={s['peak_z']:>4.1f}{marker}")
        # Negative-against-self
        neg_summary = summarize(negative_per_corpus[target])
        neg_cell = f"z2={neg_summary['z2']:>2d}/7 pk={neg_summary['peak_z']:>4.1f}"
        print(f"  {probe_set:<28s} {cells[0]:>11s} {cells[1]:>11s} {cells[2]:>11s} {neg_cell:>11s}")

    # Verdict reasoning
    print(f"\n=== Verdict reasoning ===")
    # Diagonal strength: average peak z of (probe-set vs OWN instrument)
    diag_peaks = [table[ps][PROBE_TO_CORPUS[ps]]["peak_z"] for ps in ["quran", "judaism", "christianity"]]
    # Off-diagonal strength: average peak z of (probe-set vs OTHER instruments)
    off_diag_peaks = []
    for ps in ["quran", "judaism", "christianity"]:
        target = PROBE_TO_CORPUS[ps]
        for ck in ["quran_sale", "kjv_ot", "kjv_nt"]:
            if ck != target:
                off_diag_peaks.append(table[ps][ck]["peak_z"])
    avg_diag = sum(diag_peaks) / len(diag_peaks)
    avg_off = sum(off_diag_peaks) / len(off_diag_peaks)
    print(f"  Diagonal avg peak z (probe vs own substrate): {avg_diag:.2f}")
    print(f"  Off-diagonal avg peak z (probe vs other substrate): {avg_off:.2f}")
    print(f"  Substrate-specificity ratio: {avg_diag/max(avg_off, 0.01):.2f}")

    # Negative controls
    neg_max_z = max(max(r["max_z"] for r in negative_per_corpus[ck]) for ck in instruments)
    neg_above = sum(1 for ck in instruments for r in negative_per_corpus[ck] if r["above_max"])
    print(f"  Negative-control peak across all corpora: {neg_max_z:.2f}")
    print(f"  Negative-control above_max across all corpora: {neg_above}/{3*7}")

    if avg_diag > avg_off * 1.5 and neg_above < 3:
        verdict = "✓ SUBSTRATE-DISTINGUISHING — diagonal fires harder than off-diagonal; substrates have distinct form-signatures"
    elif avg_diag > avg_off:
        verdict = "Partial — diagonal > off-diagonal but not dramatically; substrate-form-leakage real"
    else:
        verdict = "FAILED — substrates indistinguishable by methodology (would invalidate per-substrate form claim)"
    print(f"\n  Verdict: {verdict}")

    output = {
        "partition": "R-RBS-LM-53",
        "srmech_version": srmech.__version__,
        "corpora": {k: {"label": CORPORA[k]["label"], "n_chunks": len(paragraphs_by_corpus[k])} for k in instruments},
        "baselines": baselines,
        "diagonal_results": diagonal_results,
        "negative_results": negative_per_corpus,
        "cross_matrix": cross_matrix,
        "summary_table": table,
        "verdict": verdict,
        "avg_diag_peak_z": round(avg_diag, 2),
        "avg_off_diag_peak_z": round(avg_off, 2),
        "substrate_specificity_ratio": round(avg_diag / max(avg_off, 0.01), 2),
    }
    out_path = HERE / "R-RBS-LM-53_results.json"
    out_path.write_text(json.dumps(output, indent=2, default=str))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
