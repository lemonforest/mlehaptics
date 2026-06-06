"""R-RBS-LM-WIKI — build a MODERN-USAGE srmech-native kernel from a LOCAL
Wikipedia dump (no HTTP streaming, no multi-download — one .bz2 + wikiextractor).

User direction (2026-06-06): "source the wikipedia tarball as a kernel. this way
we do not need http streams or several downloads" — and earlier: "i'm not sure
that our openstax k-12 + higher education captures modern usage either."

So this kernel is the MODERN-USAGE peer to the grammar / lexicon / domain kernels
of the RBS-SNN (F431). It reuses the PROVEN srmech-native, torch-free build
(R-RBS-LM-kernel_refresh / R-RBS-LM-52b), exactly:
  K1 (presence) = co-occurrence edges -> Class-L dense_laplacian
                  -> hermitian_eigendecompose -> top-K eigvecs -> top-M tokens
                  -> Class-A mint -> Class-M bundle. The Class-L eigenspectrum
                  IS the srmech-native storage signature (F172).
  K3 (sequence) = position-bound n-gram Class-M bind+permute -> bundle.

Corpus-appropriate VALIDATION (a general-knowledge corpus has no clean
"off-corpus" negative the way a framework notebook does, so we test STRUCTURE):
  baseline   = random real-article-pair similarity (the two-unrelated-articles floor)
  REAL       = held-out real article snippets vs the kernel (expect z > 0)
  SHUFFLED   = the SAME snippets, tokens shuffled (same bag, destroyed order/
               co-occurrence) vs the kernel  -> tests whether K1/K3 captured
               STRUCTURE, not just vocabulary (expect REAL > SHUFFLED, sharply
               for K3 whose n-grams are obliterated by the shuffle)
  GIBBERISH  = random non-corpus tokens vs the kernel (expect z ~ 0 / negative)

Run on the live 0.7.1 scientific venv:
  /tmp/verify_srmech_071_sci/bin/python \
    docs/srmech/rbs_lm_research/R-RBS-LM-WIKI_kernel_build.py \
    --corpus /home/skirklan/corpora/wikipedia/simplewiki_extracted \
    --tag simplewiki
"""

import argparse
import glob
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
OUTDIR = HERE / "kernels_wikipedia"
OUTDIR.mkdir(exist_ok=True)

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


def read_wiki_articles(corpus_dir, max_articles=0, min_chars=200):
    """Stream wikiextractor --json output: one JSON object per line with a
    'text' field. Yields per-article token lists (the kernel's 'sections')."""
    files = (sorted(glob.glob(str(Path(corpus_dir) / "*" / "wiki_*")))
             + sorted(glob.glob(str(Path(corpus_dir) / "*.jsonl"))))
    n = 0
    snippets = []          # keep some raw texts for the held-out validation
    for fp in files:
        with open(fp, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                text = obj.get("text", "")
                if len(text) < min_chars:
                    continue
                toks = tokenize_text(text)
                if len(toks) < 20:
                    continue
                yield toks, text
                n += 1
                if max_articles and n >= max_articles:
                    return


# ---- K1 presence (Class L eigendecomp + Class M mint+bundle) ----
def build_K1_presence(tokens_per_section, K=33, M_per_eigenvec=21,
                      vocab_size=256, window=5):
    freq = Counter()                      # vocabulary-frequency SELECTION (not storage)
    for toks in tokens_per_section:
        freq.update(toks)
    N = min(vocab_size, len(freq))
    vocab = [t for t, _ in freq.most_common(N)]
    vocab_idx = {t: i for i, t in enumerate(vocab)}

    edge_count = Counter()                # transient edge-weight accumulator -> Class L
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
    L = dense_laplacian(N, edges, weights)            # Class L (srmech-native)
    eigvals, eigvecs = hermitian_eigendecompose(L)    # the F172 storage signature

    top_k_indices = list(range(len(eigvals) - K, len(eigvals)))
    eigenvector_hvs = []
    for k_idx in reversed(top_k_indices):
        eigvec = eigvecs[:, k_idx]
        mag_sq = eigvec * eigvec
        top_idx = sorted(range(len(eigvec)), key=lambda i: -mag_sq[i])[:M_per_eigenvec]
        eigenvector_hvs.append(bundle([mint(vocab[i]) for i in top_idx]))
    instrument = bundle(eigenvector_hvs)
    eig_tail = [float(eigvals[i]) for i in reversed(top_k_indices)]
    total_tokens = sum(len(t) for t in tokens_per_section)
    return instrument, vocab, {
        "kernel": "K1_presence", "vocab_size": N, "n_edges": len(edges),
        "K_eigvecs": K, "M_per_eigvec": M_per_eigenvec, "window": window,
        "eig_tail_top8": eig_tail[:8],
        "total_tokens": total_tokens, "unique_tokens": len(freq),
    }


def encode_probe_K1(text):
    toks = tokenize_text(text)
    if not toks:
        return mint("__empty__")
    return hierarchical_bundle([mint(t) for t in toks])


# ---- K3 sequence (position-bound n-gram bind + bundle) ----
def build_K3_sequence(tokens_per_section, n_gram=3, sample_n=20000,
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


# ---- corpus-appropriate validation ----
GIBBERISH_VOCAB = ("zlorp quibnax vendil throbax muklee pltodge frinsel gwarbic "
                   "snovel hagrith plumduff yexall morbicund snylp drazzic "
                   "twillop garnex blundish veffry").split()


def shuffle_tokens(text, seed):
    toks = tokenize_text(text)
    rng = random.Random(seed)
    rng.shuffle(toks)
    return " ".join(toks)


def gibberish_like(text, seed):
    n = max(3, len(tokenize_text(text)))
    rng = random.Random(seed)
    return " ".join(rng.choice(GIBBERISH_VOCAB) for _ in range(n))


def baseline(encoder, snippets, n=100, seed=42):
    rng = random.Random(seed)
    sims = [similarity(encoder(a), encoder(b))
            for a, b in (rng.sample(snippets, 2) for _ in range(n))]
    m = sum(sims) / len(sims)
    s = (sum((x - m) ** 2 for x in sims) / len(sims)) ** 0.5
    return {"mean": m, "std": s, "max": max(sims), "min": min(sims), "n": n}


def category_z(instrument, encoder, base, texts):
    zs = []
    for t in texts:
        sim = similarity(encoder(t), instrument)
        zs.append((sim - base["mean"]) / max(base["std"], 1e-9))
    return {"mean_z": sum(zs) / len(zs), "max_z": max(zs), "min_z": min(zs), "n": len(zs)}


def save_instrument(name, inst, meta):
    binp = OUTDIR / f"{name}.bin"
    binp.write_bytes(inst)
    (OUTDIR / f"{name}.meta.json").write_text(json.dumps(meta, indent=2))
    return len(inst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, help="wikiextractor --json output dir")
    ap.add_argument("--tag", default="wiki", help="kernel name tag (e.g. simplewiki / enwiki)")
    ap.add_argument("--max-articles", type=int, default=0, help="0 = all")
    ap.add_argument("--vocab-size", type=int, default=256)
    ap.add_argument("--holdout", type=int, default=60, help="articles held out for validation")
    args = ap.parse_args()

    print(f"=== R-RBS-LM-WIKI kernel build  tag={args.tag}  (srmech {srmech.__version__}) ===")
    print(f"  corpus: {args.corpus}")

    sections, snippets = [], []
    for i, (toks, text) in enumerate(read_wiki_articles(args.corpus, args.max_articles)):
        sections.append(toks)
        if 200 < len(text) < 1200:
            snippets.append(text[:1200])
        if (i + 1) % 20000 == 0:
            print(f"  ...{i + 1:,} articles read")
    print(f"  total articles: {len(sections):,}   snippet pool: {len(snippets):,}")

    # hold out the last `holdout` snippets for validation; they still entered the
    # kernel build (the kernel is the whole-corpus instrument) — the test is
    # whether real STRUCTURE scores above the random-article-pair floor, and
    # above the shuffled / gibberish controls.
    rng = random.Random(7)
    holdout = rng.sample(snippets, min(args.holdout, len(snippets)))
    base_pool = [s for s in snippets if s not in set(holdout)]

    print("\n--- building kernels ---")
    K1, vocab, K1m = build_K1_presence(sections, vocab_size=args.vocab_size)
    K3, K3m = build_K3_sequence(sections)
    b1 = save_instrument(f"{args.tag}_K1", K1, {**K1m, "tag": args.tag, "top20_vocab": vocab[:20]})
    b3 = save_instrument(f"{args.tag}_K3", K3, {**K3m, "tag": args.tag})
    print(f"  K1: {b1} bytes  vocab={K1m['vocab_size']} edges={K1m['n_edges']:,} "
          f"tokens={K1m['total_tokens']:,} unique={K1m['unique_tokens']:,}")
    print(f"      eig_tail={[round(e,2) for e in K1m['eig_tail_top8'][:5]]}  top vocab={vocab[:12]}")
    print(f"  K3: {b3} bytes  ngrams_total={K3m['n_ngrams_total_corpus']:,} sampled={K3m['n_ngrams_sampled']:,}")

    print("\n--- validation (real vs shuffled vs gibberish) ---")
    base_K1 = baseline(encode_probe_K1, base_pool)
    base_K3 = baseline(encode_probe_K3, base_pool)
    real_K1 = category_z(K1, encode_probe_K1, base_K1, holdout)
    real_K3 = category_z(K3, encode_probe_K3, base_K3, holdout)
    shuf_texts = [shuffle_tokens(t, 100 + i) for i, t in enumerate(holdout)]
    gib_texts = [gibberish_like(t, 200 + i) for i, t in enumerate(holdout)]
    shuf_K1 = category_z(K1, encode_probe_K1, base_K1, shuf_texts)
    shuf_K3 = category_z(K3, encode_probe_K3, base_K3, shuf_texts)
    gib_K1 = category_z(K1, encode_probe_K1, base_K1, gib_texts)
    gib_K3 = category_z(K3, encode_probe_K3, base_K3, gib_texts)

    def row(name, d):
        print(f"    {name:18s} mean_z={d['mean_z']:+.2f}  (min {d['min_z']:+.2f} / max {d['max_z']:+.2f})")
    print(f"  K1 (presence)  baseline mean={base_K1['mean']:+.4f} std={base_K1['std']:.4f}")
    row("REAL", real_K1); row("SHUFFLED", shuf_K1); row("GIBBERISH", gib_K1)
    print(f"  K3 (sequence)  baseline mean={base_K3['mean']:+.4f} std={base_K3['std']:.4f}")
    row("REAL", real_K3); row("SHUFFLED", shuf_K3); row("GIBBERISH", gib_K3)

    structure_signal_K1 = real_K1["mean_z"] - shuf_K1["mean_z"]
    structure_signal_K3 = real_K3["mean_z"] - shuf_K3["mean_z"]
    print(f"\n  STRUCTURE SIGNAL (REAL - SHUFFLED):  K1={structure_signal_K1:+.2f}  K3={structure_signal_K3:+.2f}")
    print(f"  (K3 should drop sharply under shuffle — its n-grams are obliterated;")
    print(f"   K1's window co-occurrence is partially scrambled too.)")

    results = {
        "tag": args.tag, "srmech_version": srmech.__version__, "D": D,
        "n_articles": len(sections), "K1_meta": K1m, "K3_meta": K3m,
        "validation": {
            "K1": {"baseline": base_K1, "real": real_K1, "shuffled": shuf_K1, "gibberish": gib_K1,
                   "structure_signal": structure_signal_K1},
            "K3": {"baseline": base_K3, "real": real_K3, "shuffled": shuf_K3, "gibberish": gib_K3,
                   "structure_signal": structure_signal_K3},
        },
    }
    out = HERE / f"R-RBS-LM-WIKI_{args.tag}_results.json"
    out.write_text(json.dumps(results, indent=2, default=str))
    print(f"\nResults: {out}")
    print(f"Kernel artifacts: {OUTDIR}/ ({args.tag}_K1.bin + {args.tag}_K3.bin + meta)")


if __name__ == "__main__":
    main()
