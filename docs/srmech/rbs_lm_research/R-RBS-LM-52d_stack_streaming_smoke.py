"""R-RBS-LM-52d — Stream a code dataset; build cascade kernel at scale.

Per user 2026-05-26: test the cooccurrence-eigvec cascade at a scale much
larger than our 50-200K-byte corpora — using HuggingFace datasets
streaming to consume a real code dataset row-by-row.

Tooling state (verified 2026-05-26):
  ✓ huggingface_hub 1.16.1 installed
  ✓ hf CLI installed (replacement for deprecated huggingface-cli)
  ✓ datasets 4.8.5 installed
  ✗ HF auth not configured

Dataset choice:
  DEFAULT: codeparrot/codeparrot-clean (public; ~25M Python files; ~50GB)
    - has 'content' field with the actual code text
    - no auth required; can stream immediately
  ALTERNATIVE: bigcode/the-stack-smol (gated; requires hf auth login)
    - the proper Stack subset per BigCode's open-research framing
    - set USE_STACK_SMOL=True after running `hf auth login` interactively

Method:
  1. Stream N rows from the chosen dataset
  2. For each row, tokenize the 'content' field (code tokenizer)
  3. Update streaming cooccurrence counter (distance-5 within each file)
  4. After N rows, compute Laplacian + eigvecs
  5. Build a Stack-kernel instrument
  6. Test the kernel: DOMAIN anchor accuracy on held-out fragments;
     compare structural fingerprint vs English prose / philosophy / novel
     kernels from the 54i baseline

This is the FIRST scale-up test of the cascade beyond ~200K bytes.
Compare findings:
  - At small corpora (54i 9 kernels): 79% kernel-exact routing
  - At large corpora (52d N=1000+ files): does accuracy hold or degrade?

Per Test A finding (Finding 70): HDC is decorative; this smoke uses
set-cosine over top-K token sets (same as 54f / 70a Variant C). The
cascade is honestly framed as classical NLP cooccurrence-eigvec method
+ multi-stage compositional pipeline, not "hyperdimensional."
"""

import argparse
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

# Streaming HF datasets
from datasets import load_dataset

import srmech
from srmech.amsc.laplacian import dense_laplacian, hermitian_eigendecompose


HERE = Path(__file__).parent

# Config — tunable from CLI or env
DEFAULT_DATASET = "codeparrot/codeparrot-clean"
DEFAULT_SPLIT = "train"
DEFAULT_N_ROWS = 2000  # number of files to stream
DEFAULT_VOCAB_N = 300  # eigvec table dimension
DEFAULT_M_PER_EIGVEC = 21
DEFAULT_LANG_FILTER = None  # codeparrot is Python-only by default

# Known content-field names per dataset (some use "content", others "text", "code", etc.)
CONTENT_FIELD_BY_DATASET = {
    "codeparrot/codeparrot-clean":         "content",
    "bigcode/the-stack-smol":              "content",
    "bigcode/the-stack-smol-xs":           "content",
    "bigcode/the-stack-dedup":             "content",
    "bigcode/the-stack-v2":                "content",
    "bigcode/the-stack-v2-dedup":          "content",
    "bigcode/starcoderdata":               "content",
}

# Code-aware tokenizer: identifiers + keywords; strip punctuation
CODE_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

# Common Python stopwords + universal noise tokens
CODE_STOPWORDS = set("""
the and or not is in to for if else then return import from as with
None True False def class self pass continue break print
__init__ __name__ __main__ __dict__ __module__
""".split()) | {"a", "an", "of", "be", "do", "this", "that"}


def tokenize_code(content: str) -> list:
    """Code-aware tokenization: identifiers + dotted-paths."""
    raw = CODE_IDENT_RE.findall(content)
    return [t.lower() for t in raw if t.lower() not in CODE_STOPWORDS and len(t) >= 2]


def stream_rows(dataset_name: str, split: str, n_rows: int, content_field: str = "content"):
    """Stream up to n_rows rows from the dataset; yield content strings."""
    print(f"  Loading {dataset_name} (split={split}) in streaming mode...")
    ds = load_dataset(dataset_name, split=split, streaming=True)
    yielded = 0
    for row in ds:
        content = row.get(content_field, "")
        if not content or not isinstance(content, str): continue
        yield content
        yielded += 1
        if yielded >= n_rows: break
    print(f"  Streamed {yielded} rows.")


def build_streaming_kernel(content_iterator, vocab_n: int = DEFAULT_VOCAB_N,
                            m_per_eigvec: int = DEFAULT_M_PER_EIGVEC,
                            distance: int = 5,
                            log_every: int = 500):
    """Build cooccurrence graph incrementally as we stream rows.
    Returns (eigvec_table, vocab, idx_map, n_rows_consumed, n_tokens_consumed).
    """
    freq = Counter()
    file_tokens_buffer = []  # list of per-file token lists for cooccurrence pass
    n_rows = 0; n_tokens_total = 0
    start_t = time.time()

    # PASS 1: collect freq + buffer all file token lists
    for content in content_iterator:
        toks = tokenize_code(content)
        if not toks: continue
        freq.update(toks)
        file_tokens_buffer.append(toks)
        n_rows += 1
        n_tokens_total += len(toks)
        if n_rows % log_every == 0:
            print(f"    streamed {n_rows} files; {n_tokens_total} tokens; {len(freq)} vocab; "
                  f"{time.time()-start_t:.1f}s elapsed")

    print(f"  Pass 1 done: {n_rows} files, {n_tokens_total} tokens, {len(freq)} unique tokens, "
          f"{time.time()-start_t:.1f}s")

    # Select top-N vocab
    N = min(vocab_n, len(freq))
    if N < 8:
        return None, None, None, n_rows, n_tokens_total
    vocab = [t for t, _ in freq.most_common(N)]
    idx_map = {t: i for i, t in enumerate(vocab)}

    # PASS 2: build cooccurrence edges (within distance per file)
    edges = Counter()
    for toks in file_tokens_buffer:
        idx = [idx_map[t] for t in toks if t in idx_map]
        for i in range(len(idx)):
            for j in range(i+1, min(i+distance, len(idx))):
                a, b = idx[i], idx[j]
                if a == b: continue
                edges[(min(a,b), max(a,b))] += 1
    print(f"  Pass 2 done: {len(edges)} edges built; {time.time()-start_t:.1f}s")

    if not edges:
        return None, None, None, n_rows, n_tokens_total

    # Laplacian + eigendecompose
    L = dense_laplacian(N, list(edges.keys()), [float(w) for w in edges.values()])
    ev, evc = hermitian_eigendecompose(L)
    table = []
    for k in range(len(ev) - 1, -1, -1):
        eigvec = evc[:, k].real
        mag_sq = eigvec * eigvec
        top_idx = np.argsort(-mag_sq)[:m_per_eigvec]
        top_tokens = [vocab[i] for i in top_idx]
        table.append({"rank": len(ev) - 1 - k,
                       "eigval": float(np.real(ev[k])),
                       "top_tokens": top_tokens,
                       "token_set": set(top_tokens)})
    print(f"  Laplacian + eigendecompose done: {len(table)} eigvecs; {time.time()-start_t:.1f}s")
    return table, vocab, idx_map, n_rows, n_tokens_total


def sim_cosine(row_a, row_b):
    a = row_a["token_set"]; b = row_b["token_set"]
    if not a or not b: return 0.0
    return float(len(a & b) / np.sqrt(len(a) * len(b)))


def find_alignment_score(probe_table, kernel_table):
    n_p = len(probe_table); n_k = len(kernel_table)
    sims = []
    used_k = set()
    for i in range(n_p):
        candidates = []
        for j in range(n_k):
            if j in used_k: continue
            s = sim_cosine(probe_table[i], kernel_table[j])
            candidates.append((j, s))
        if not candidates: break
        best_j, best_sim = max(candidates, key=lambda x: x[1])
        used_k.add(best_j)
        sims.append(best_sim)
    return float(np.mean(sims)) if sims else 0.0


def main():
    parser = argparse.ArgumentParser(description="Stream code corpus; build cascade kernel.")
    parser.add_argument("--dataset", default=DEFAULT_DATASET, help="HF dataset name")
    parser.add_argument("--split", default=DEFAULT_SPLIT, help="Dataset split")
    parser.add_argument("--n-rows", type=int, default=DEFAULT_N_ROWS, help="Rows to stream")
    parser.add_argument("--vocab-n", type=int, default=DEFAULT_VOCAB_N, help="Vocab cap for eigvec table")
    parser.add_argument("--content-field", default=None, help="Content field name (auto-detect from dataset)")
    parser.add_argument("--out-suffix", default="", help="Output filename suffix (e.g. '_the_stack_smol')")
    args = parser.parse_args()

    content_field = args.content_field or CONTENT_FIELD_BY_DATASET.get(args.dataset, "content")

    print(f"=== R-RBS-LM-52d — Streaming-scale code corpus cascade ===\n")
    print(f"srmech: {srmech.__version__}")
    print(f"Dataset: {args.dataset} (split={args.split}; content_field={content_field})")
    print(f"Stream {args.n_rows} rows; vocab N={args.vocab_n}; top-K per eigvec={DEFAULT_M_PER_EIGVEC}")
    print(f"Similarity: set-cosine (per Finding 70 correction — random-bipolar bundle ≡ set-cosine for set-membership)\n")

    # Build the Stack-kernel
    print(f"--- Building streaming kernel ---")
    iterator = stream_rows(args.dataset, args.split, args.n_rows, content_field=content_field)
    stack_kernel, vocab, idx_map, n_rows, n_tokens = build_streaming_kernel(iterator, vocab_n=args.vocab_n)
    if stack_kernel is None:
        print("ERROR: insufficient data to build kernel")
        return

    print(f"\n=== Stack-kernel summary ===")
    print(f"  rows consumed:        {n_rows}")
    print(f"  tokens consumed:      {n_tokens}")
    print(f"  vocab size:           {len(vocab)}")
    print(f"  eigvecs:              {len(stack_kernel)}")
    print(f"  top eigvec[0] tokens: {stack_kernel[0]['top_tokens']}")
    print(f"  top eigvec[1] tokens: {stack_kernel[1]['top_tokens']}")
    print(f"  top eigvec[2] tokens: {stack_kernel[2]['top_tokens']}")
    print(f"  rank 5 eigvec[5] tok: {stack_kernel[5]['top_tokens']}")
    print(f"  rank 10 eigvec[10]:   {stack_kernel[10]['top_tokens']}")

    # Compare against existing English kernels for substrate-class discrimination
    print(f"\n=== DOMAIN-anchor check: route Stack vs English corpora ===")
    print(f"Building English baseline kernels from cached corpora...\n")

    ENGLISH_KERNELS = {
        "kjv_nt":       "/tmp/kjv_new_testament.txt",
        "plato":        "/tmp/plato_republic.txt",
        "frankenstein": "/tmp/frankenstein.txt",
        "milton":       "/tmp/paradise_lost.txt",
    }

    # Build English kernels from local files (smaller; non-streaming)
    english_kernels = {}
    STOPWORDS_EN = set("""
the a an and or but if then else of in on at to for with by from as is are was were be been
have has had this that these those it its they them their there here he she we us our
""".split())

    def tokenize_eng(text):
        raw = re.findall(r"[A-Za-z][A-Za-z0-9'-]*[A-Za-z0-9]|[A-Za-z]", text)
        return [t.lower() for t in raw if t.lower() not in STOPWORDS_EN and len(t) >= 2]

    def build_kernel_from_file(path, vocab_n=DEFAULT_VOCAB_N):
        text = Path(path).read_text(encoding="utf-8", errors="replace")
        # Strip PG header
        s = re.search(r"\*\*\* START OF (THE )?PROJECT GUTENBERG", text)
        e = re.search(r"\*\*\* END OF (THE )?PROJECT GUTENBERG", text)
        if s: text = text[s.end():]
        if e: text = text[:e.start()]
        chunks = re.split(r"\n\s*\n+", text.strip())
        filt = [tokenize_eng(c) for c in chunks]
        all_t = [t for toks in filt for t in toks]
        freq = Counter(all_t)
        N = min(vocab_n, len(freq))
        if N < 8: return None
        vocab = [t for t, _ in freq.most_common(N)]
        idx_map = {t: i for i, t in enumerate(vocab)}
        edges = Counter()
        for toks in filt:
            idx = [idx_map[t] for t in toks if t in idx_map]
            for i in range(len(idx)):
                for j in range(i+1, min(i+5, len(idx))):
                    a, b = idx[i], idx[j]
                    if a == b: continue
                    edges[(min(a,b), max(a,b))] += 1
        if not edges: return None
        L = dense_laplacian(N, list(edges.keys()), [float(w) for w in edges.values()])
        ev, evc = hermitian_eigendecompose(L)
        table = []
        for k in range(len(ev) - 1, -1, -1):
            eigvec = evc[:, k].real
            mag_sq = eigvec * eigvec
            top_idx = np.argsort(-mag_sq)[:DEFAULT_M_PER_EIGVEC]
            top_tokens = [vocab[i] for i in top_idx]
            table.append({"rank": len(ev)-1-k, "eigval": float(np.real(ev[k])),
                           "top_tokens": top_tokens, "token_set": set(top_tokens)})
        return table

    for label, path in ENGLISH_KERNELS.items():
        if not Path(path).exists():
            print(f"  [SKIP] {label}: file not found")
            continue
        t = build_kernel_from_file(path)
        if t is not None:
            english_kernels[label] = t
            print(f"  {label:<14s}: {len(t)} eigvecs")

    # Compare Stack-kernel to each English kernel
    print(f"\n=== Pairwise alignment: Stack-kernel ↔ English kernels ===")
    all_kernels = {"stack": stack_kernel, **english_kernels}
    pairs = list(all_kernels.keys())
    pairwise_sims = {}
    print(f"  {'A \\\\ B':<14s}", end="")
    for b in pairs: print(f"{b[:10]:>11s}", end="")
    print()
    for a in pairs:
        print(f"  {a[:14]:<14s}", end="")
        for b in pairs:
            if a == b:
                print(f"{'-':>11s}", end="")
                continue
            key = (min(a,b), max(a,b))
            if key not in pairwise_sims:
                pairwise_sims[key] = find_alignment_score(all_kernels[a], all_kernels[b])
            print(f"{pairwise_sims[key]:>+11.4f}", end="")
        print()

    # Verdict
    print(f"\n=== Verdict ===")
    stack_to_english_sims = [pairwise_sims[(min("stack",k), max("stack",k))] for k in english_kernels]
    english_to_english_sims = []
    eng_list = list(english_kernels)
    for i, a in enumerate(eng_list):
        for b in eng_list[i+1:]:
            english_to_english_sims.append(pairwise_sims[(min(a,b), max(a,b))])

    avg_stack_eng = float(np.mean(stack_to_english_sims)) if stack_to_english_sims else 0.0
    avg_eng_eng = float(np.mean(english_to_english_sims)) if english_to_english_sims else 0.0
    print(f"  Stack ↔ English (n={len(stack_to_english_sims)}): avg alignment = {avg_stack_eng:.4f}")
    print(f"  English ↔ English (n={len(english_to_english_sims)}): avg alignment = {avg_eng_eng:.4f}")
    ratio = avg_eng_eng / max(avg_stack_eng, 1e-9)
    print(f"  English-cluster / Stack-distance ratio: {ratio:.2f}")
    if ratio > 1.5:
        verdict = (f"STRONG cross-substrate-CLASS separation: Stack (code) is structurally "
                   f"distinct from English corpora; English corpora cluster among themselves "
                   f"({ratio:.2f}x tighter)")
    elif ratio > 1.15:
        verdict = (f"MODERATE substrate-class separation: English corpora cluster {ratio:.2f}x "
                   f"tighter than Stack-English distance")
    else:
        verdict = (f"WEAK substrate-class separation: Stack and English are structurally "
                   f"comparable (ratio {ratio:.2f})")
    print(f"  {verdict}")

    out = {
        "partition": "R-RBS-LM-52d",
        "dataset": args.dataset,
        "n_rows": n_rows,
        "n_tokens": n_tokens,
        "vocab_size": len(vocab),
        "n_eigvecs": len(stack_kernel),
        "top_eigvec_tokens": stack_kernel[0]["top_tokens"],
        "pairwise_alignments": {f"{a}|{b}": float(s) for (a, b), s in pairwise_sims.items()},
        "avg_stack_to_english": avg_stack_eng,
        "avg_english_to_english": avg_eng_eng,
        "substrate_class_ratio": ratio,
        "verdict": verdict,
    }
    out_path = HERE / f"R-RBS-LM-52d_results{args.out_suffix}.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
