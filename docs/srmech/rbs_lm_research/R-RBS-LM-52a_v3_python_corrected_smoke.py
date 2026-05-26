"""R-RBS-LM-52a-v3 — Python code with corrected mint+bundle methodology.

Closes the loop from R-RBS-LM-52a's original NO-signal result on Python
code. The methodology has been corrected via 52a-v2/52b/52c iterations:
  - mint_vector per token + bundle (similarity-preserving)
  - No FFT band-pass on mint-bundle (substrate-dependent; degrades)
  - K1 (filtered) + K3 (raw tokens; sample-500 at SNR optimum)
  - Score-level smoothie max(z_K1, z_K3)

Test: does Python code corpus yield clean Path E signal with the
corrected pipeline? Same docs/srmech/rbs_lm_research/*.py files as 52a.
"""

import json
import random
import re
import sys
import tokenize as py_tokenize
from collections import Counter
from pathlib import Path

import srmech
from srmech.amsc.laplacian import dense_laplacian, hermitian_eigendecompose
from srmech.amsc.hdc import bundle, similarity, bind, permute
from srmech.signal_processing import mint_vector


HERE = Path(__file__).parent


# Filter aggressive punctuation; keep NAME + STRING + NUMBER + COMMENT.
# Class K-style filter at pre-vocabulary stage.
PY_OP_DROP = set("( ) , . { } [ ] : ; = + - * / % @ ! ? | & ^ ~ < > = == != "
                  ">= <= -> ** // += -= *= /= //= %= **= |= &= ^= >>= <<= "
                  "@= := ... \\".split())


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


def tokenize_python_filtered(path):
    """K1 vocab: NAME tokens only (identifiers + keywords). Drop operators."""
    tokens = []
    try:
        with open(path, "rb") as f:
            for tok in py_tokenize.tokenize(f.readline):
                if tok.type == py_tokenize.NAME:
                    tokens.append(tok.string.lower())
    except Exception:
        pass
    return tokens


def tokenize_python_raw(path):
    """K3 sequence: NAME + OP (so structure preserved). Drop strings/numbers/comments."""
    tokens = []
    try:
        with open(path, "rb") as f:
            for tok in py_tokenize.tokenize(f.readline):
                if tok.type in (py_tokenize.NAME, py_tokenize.OP):
                    s = tok.string
                    # Normalize lowercase for NAME; keep OP as-is
                    if tok.type == py_tokenize.NAME:
                        s = s.lower()
                    tokens.append(s)
    except Exception:
        pass
    return tokens


def tokenize_text_filtered(text):
    """For probe encoding (text-format probes)."""
    raw = re.findall(r'[A-Za-z][A-Za-z0-9_]*', text)
    return [t.lower() for t in raw if len(t) >= 2]


def tokenize_text_raw(text):
    """For K3 probes: words + operators preserved."""
    # Match identifiers OR single-char operators
    raw = re.findall(r'[A-Za-z][A-Za-z0-9_]*|[(){}\[\].,;:=+\-*/%@!?|&^~<>]', text)
    return [t.lower() if t.isalpha() else t for t in raw]


def build_K1(filtered_tokens_per_file, K=33, M=21, vocab_size=200, window=5):
    all_tokens = [t for toks in filtered_tokens_per_file for t in toks]
    freq = Counter(all_tokens)
    N = min(vocab_size, len(freq))
    vocab = [t for t, _ in freq.most_common(N)]
    vocab_idx = {t: i for i, t in enumerate(vocab)}
    edge_count = Counter()
    for tokens in filtered_tokens_per_file:
        indexed = [vocab_idx[t] for t in tokens if t in vocab_idx]
        for i in range(len(indexed)):
            for j in range(i + 1, min(i + window, len(indexed))):
                a, b = indexed[i], indexed[j]
                if a == b:
                    continue
                edge_count[(min(a, b), max(a, b))] += 1
    L = dense_laplacian(N, list(edge_count.keys()), [float(w) for w in edge_count.values()])
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


def build_K3(raw_tokens_per_file, n_gram=4, sample_n=500, position_stride=2731, seed=42):
    rng = random.Random(seed)
    all_ngrams = []
    for tokens in raw_tokens_per_file:
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
    return hierarchical_bundle(hvs), {"kernel": f"K3_n{n_gram}",
                                        "n_ngrams_corpus": sum(max(len(t) - n_gram + 1, 0) for t in raw_tokens_per_file),
                                        "n_sampled": len(all_ngrams)}


def encode_K1(text):
    toks = tokenize_text_filtered(text)
    return hierarchical_bundle([mint(t) for t in toks]) if toks else mint("__empty__")


def encode_K3(text, n_gram=4, position_stride=2731):
    toks = tokenize_text_raw(text)
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
    print(f"=== R-RBS-LM-52a-v3: Python code with corrected mint+bundle ===\n")
    print(f"srmech: {srmech.__version__}")

    files = sorted(HERE.glob("*.py"))
    # Skip self
    files = [f for f in files if "52a-v3" not in f.name and "52a_v3" not in f.name]
    print(f"Corpus: {len(files)} Python files")

    filt = [tokenize_python_filtered(f) for f in files]
    raw = [tokenize_python_raw(f) for f in files]
    print(f"Tokens: filtered {sum(len(t) for t in filt):,}; raw {sum(len(t) for t in raw):,}")

    print(f"\n--- K1 (presence; NAME-only filter) ---")
    K1, K1_m = build_K1(filt)
    print(f"  vocab_top_15: {K1_m['vocab_top_15']}")
    print(f"  n_edges: {K1_m['n_edges']}")

    print(f"\n--- K3 n=4 (sequence; NAME+OP raw; sample 500) ---")
    K3_4, K3_4_m = build_K3(raw, n_gram=4, sample_n=500)
    print(f"  {K3_4_m}")

    # Probes — code-specific structural phrases
    code_probes = [
        "def encode loe content",
        "def cascade compose",
        "def main self",
        "import numpy as",
        "class K3 Tripartition",
        "for i in range",
        "if not condition return",
        "from srmech amsc import",
        "self instrument bytes",
        "def hierarchical bundle vectors",
        "bind permute mint vector",
        "dense laplacian eigendecompose",
        "n gram position stride",
        "tokenize text raw",
        "encode probe K1",
    ]

    non_code_probes = [
        "chocolate ice cream sundae",
        "professional soccer team striker",
        "kitchen pencil sharpener metal",
        "tropical rainforest jungle humid",
        "vintage automobile classic ford",
    ]

    paragraphs = []
    for f in files[:10]:
        try:
            text = f.read_text()
            paras = text.split("\n\n")
            for p in paras:
                if 50 < len(p) < 500:
                    paragraphs.append(p)
        except Exception:
            pass

    def baseline(enc, n=100):
        rng = random.Random(42)
        ss = []
        for _ in range(n):
            a, b = rng.sample(paragraphs, 2)
            ss.append(similarity(enc(a), enc(b)))
        m = sum(ss) / len(ss)
        sd = (sum((x - m) ** 2 for x in ss) / len(ss)) ** 0.5
        return {"mean": m, "std": sd, "max": max(ss), "min": min(ss)}

    b_K1 = baseline(encode_K1)
    b_K3 = baseline(encode_K3)
    print(f"\nBaselines:")
    print(f"  K1: mean={b_K1['mean']:+.4f} std={b_K1['std']:.4f} max={b_K1['max']:+.4f}")
    print(f"  K3: mean={b_K3['mean']:+.4f} std={b_K3['std']:.4f} max={b_K3['max']:+.4f}")

    def smoke(inst, enc, b, probes, kind):
        return [
            {"probe": p, "kind": kind, "sim": s, "z": (s - b["mean"]) / max(b["std"], 1e-9),
             "above_max": s > b["max"]}
            for p in probes for s in [similarity(enc(p), inst)]
        ]

    print(f"\n=== K1 (NAME tokens; filtered) ===")
    k1 = smoke(K1, encode_K1, b_K1, code_probes, "code") + smoke(K1, encode_K1, b_K1, non_code_probes, "non_code")
    for r in k1:
        f = "***" if r["above_max"] else "**" if r["z"] > 2 else "*" if r["z"] > 1 else ""
        print(f"  [{r['kind']:>8s}] {r['probe']:<42s} sim={r['sim']:+.4f} z={r['z']:+.2f} {f}")

    print(f"\n=== K3 n=4 (NAME+OP raw) ===")
    k3 = smoke(K3_4, encode_K3, b_K3, code_probes, "code") + smoke(K3_4, encode_K3, b_K3, non_code_probes, "non_code")
    for r in k3:
        f = "***" if r["above_max"] else "**" if r["z"] > 2 else "*" if r["z"] > 1 else ""
        print(f"  [{r['kind']:>8s}] {r['probe']:<42s} sim={r['sim']:+.4f} z={r['z']:+.2f} {f}")

    print(f"\n=== Smoothie max(K1, K3) ===")
    sm = []
    for kind, probes in [("code", code_probes), ("non_code", non_code_probes)]:
        for p in probes:
            s1 = similarity(encode_K1(p), K1)
            z1 = (s1 - b_K1["mean"]) / max(b_K1["std"], 1e-9)
            s3 = similarity(encode_K3(p), K3_4)
            z3 = (s3 - b_K3["mean"]) / max(b_K3["std"], 1e-9)
            mx = max(z1, z3)
            ab = (s1 > b_K1["max"]) or (s3 > b_K3["max"])
            sm.append({"probe": p, "kind": kind, "z_K1": z1, "z_K3": z3, "max_z": mx, "above_max": ab})
    for r in sm:
        f = "***" if r["above_max"] else "**" if r["max_z"] > 2 else "*" if r["max_z"] > 1 else ""
        print(f"  [{r['kind']:>8s}] {r['probe']:<42s} K1={r['z_K1']:+.2f} K3={r['z_K3']:+.2f} max={r['max_z']:+.2f} {f}")

    def summarize(rs, label, z_key="z"):
        cs = [r for r in rs if r["kind"] == "code"]
        ncs = [r for r in rs if r["kind"] == "non_code"]
        return {"label": label,
                "code_above_max": sum(1 for r in cs if r["above_max"]),
                "code_z2": sum(1 for r in cs if r[z_key] > 2),
                "code_z1": sum(1 for r in cs if r[z_key] > 1),
                "noncode_above_max": sum(1 for r in ncs if r["above_max"]),
                "code_peak": max((r[z_key] for r in cs), default=0)}

    summary = [
        summarize(k1, "K1"),
        summarize(k3, "K3_n4"),
        summarize(sm, "smoothie_max", "max_z"),
    ]
    print(f"\n\n{'='*72}\n=== R-RBS-LM-52a-v3 summary\n{'='*72}\n")
    print(f"  {'kernel':<18s} {'code above_max':>15s} {'code z>2':>10s} {'code z>1':>10s} {'code peak':>11s} {'NC above_max':>13s}")
    for s in summary:
        print(f"  {s['label']:<18s} {s['code_above_max']:>5d}/15        {s['code_z2']:>5d}/15     {s['code_z1']:>5d}/15     {s['code_peak']:>11.2f} {s['noncode_above_max']:>5d}/5")

    # Comparison to original 52a + 52a-v2 (notebooks)
    print(f"\n=== Loop closure vs original 52a ===")
    print(f"  52a (original; encode_loe_content): 0/15 z>2; verdict NO signal")
    print(f"  52a-v3 (corrected; mint+bundle):    {summary[0]['code_z2']}/15 K1 z>2; peak {summary[0]['code_peak']:.2f}")
    if summary[0]['code_z2'] >= 2 and summary[0]['noncode_above_max'] == 0:
        verdict = "✓ Loop closed — Python code substrate works with corrected methodology"
    elif summary[0]['code_z1'] >= 5:
        verdict = "Partial signal — code corpus discriminates but weaker than notebooks"
    else:
        verdict = "Weak/no signal — code substrate may be intrinsically less retrievable than text-substrate at this scale"
    print(f"  Verdict: {verdict}")

    out = {"partition": "R-RBS-LM-52a-v3", "summary": summary,
           "K1_meta": K1_m, "K3_meta": K3_4_m,
           "baselines": {"K1": b_K1, "K3": b_K3},
           "K1_results": k1, "K3_results": k3, "smoothie_results": sm,
           "verdict": verdict}
    (HERE / "R-RBS-LM-52a_v3_results.json").write_text(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
