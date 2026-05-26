"""R-RBS-LM-52a — Path E direct kernel eigendecomp via srmech-native.

Per user direction 2026-05-26: pivot from Path D (LLM-distillation) to
Path E (direct kernel eigendecomp). Code corpus is operation-primary by
construction; eigendecomp extracts the relationship-of-relationship basis
WITHOUT an LLM intermediate. The "smoothie of kernels" is multi-kernel
blending via R-RBS-LM-33 merge primitives at the eigenbasis level.

Phase A: local Python corpus (`docs/srmech/rbs_lm_research/*.py`). Validates
the srmech-native pipeline end-to-end before The Stack streaming (Phase B).

Pipeline (every step routes through srmech catalog):

  corpus → tokenize (stdlib `tokenize`)
         → token co-occurrence edges (Class A content-address + Class B TLV frame)
         → srmech.amsc.laplacian.dense_adjacency (Class L)
         → srmech.amsc.laplacian.dense_laplacian (Class L)
         → srmech.amsc.laplacian.hermitian_eigendecompose (Class L)
         → top-K eigenvectors → high-magnitude-token strings
         → srmech.signal_processing.encode_loe_content (Path A LoE; xor biology way)
         → srmech.amsc.hdc.bundle (Class M)
         → cascade instrument (1024 bytes; D=8192)

Read-mode: probes encoded via `encode_loe_content`; similarity vs instrument
via `srmech.amsc.hdc.similarity` (Class M read). Baseline: random pair
similarities over corpus phrases.

Pre-registered:
  - Probe sim > baseline_max → operation-primary substrate signal detected
  - Probe sim ≈ baseline → no signal at this scale / extractor too lossy
  - Probe sim < baseline_min → ANTI-signal (would be informative)
"""

import io
import json
import random
import sys
import tokenize
from collections import Counter
from pathlib import Path

import srmech
from srmech.amsc.laplacian import (
    dense_adjacency, dense_laplacian, hermitian_eigendecompose,
)
from srmech.amsc.hdc import bundle, similarity, bind
from srmech.signal_processing import encode_loe_content


HERE = Path(__file__).parent


def tokenize_python_file(path):
    """Use stdlib tokenize to extract lexical tokens.

    Returns list of token strings. Skip whitespace/newline/dedent tokens.
    """
    tokens = []
    with open(path, "rb") as f:
        try:
            for tok in tokenize.tokenize(f.readline):
                if tok.type in (tokenize.NAME, tokenize.OP, tokenize.STRING,
                                tokenize.NUMBER, tokenize.COMMENT):
                    # Truncate very long string tokens to keep vocab tractable
                    s = tok.string
                    if len(s) > 60:
                        s = s[:60]
                    tokens.append(s)
        except (tokenize.TokenizeError, IndentationError, SyntaxError) as e:
            print(f"    tokenize warning: {e}")
    return tokens


def build_cooccurrence_edges(file_tokens, vocab_idx, window=5):
    """Sliding-window co-occurrence; symmetric edges via canonical (min, max).

    Class A (content-address) for token identity; Class B-like (positional
    framing) for window scope.
    """
    edge_count = Counter()
    for fname, tokens in file_tokens:
        indexed = [vocab_idx[t] for t in tokens if t in vocab_idx]
        n = len(indexed)
        for i in range(n):
            for j in range(i + 1, min(i + window, n)):
                a, b = indexed[i], indexed[j]
                if a == b:
                    continue
                edge_count[(min(a, b), max(a, b))] += 1
    return edge_count


def encode_eigenvector(eigvec, vocab, top_m=20):
    """Encode an eigenvector via Path A LoE.

    Pick the top-m vocabulary entries by squared magnitude (Class L
    selection; preserves signed structure without abs()). Serialize their
    tokens as content; encode via srmech.signal_processing.encode_loe_content.
    """
    # Class L computation: squared magnitude preserves signed structure
    mag_sq = eigvec * eigvec
    top_idx = list(sorted(range(len(eigvec)), key=lambda i: -mag_sq[i])[:top_m])
    content = " ".join(vocab[i] for i in top_idx)
    return encode_loe_content(content, D=8192)


def sample_corpus_phrases(file_tokens, n=80, length=8, seed=42):
    """Draw random phrases from the corpus for baseline + probe pool."""
    rng = random.Random(seed)
    phrases = []
    seen = set()
    for fname, tokens in file_tokens:
        if len(tokens) < length:
            continue
        for _ in range(20):
            i = rng.randrange(0, len(tokens) - length)
            phrase = " ".join(tokens[i:i + length])
            if phrase not in seen:
                phrases.append(phrase)
                seen.add(phrase)
                if len(phrases) >= n:
                    return phrases
    return phrases


def main():
    print(f"=== R-RBS-LM-52a Path E — srmech-native code-corpus cascade ===\n")
    print(f"srmech: {srmech.__version__}")

    # ---- 1. Walk corpus ----
    corpus_files = sorted(HERE.glob("*.py"))
    # Skip the smoke file itself (would create circular reference)
    corpus_files = [f for f in corpus_files if "R-RBS-LM-52a" not in f.name]
    print(f"Corpus: {len(corpus_files)} Python files in {HERE.name}")

    # ---- 2. Tokenize ----
    file_tokens = []
    all_tokens = []
    for f in corpus_files:
        tokens = tokenize_python_file(f)
        file_tokens.append((f.name, tokens))
        all_tokens.extend(tokens)
    n_total = len(all_tokens)
    n_unique = len(set(all_tokens))
    print(f"Tokenized: {n_total:,} tokens; {n_unique:,} unique")

    # ---- 3. Vocabulary (frequency-pruned to fit srmech native n≤256) ----
    freq = Counter(all_tokens)
    N = min(200, len(freq))  # keep below srmech's n=256 native Jacobi bound
    vocab = [t for t, _ in freq.most_common(N)]
    vocab_idx = {t: i for i, t in enumerate(vocab)}
    coverage = sum(freq[t] for t in vocab) / max(n_total, 1)
    print(f"Vocabulary: top-{N} tokens (coverage {100*coverage:.1f}% of all tokens)")
    print(f"  top 10: {[(t, freq[t]) for t in vocab[:10]]}")

    # ---- 4. Co-occurrence edges ----
    edge_count = build_cooccurrence_edges(file_tokens, vocab_idx, window=5)
    n_edges = len(edge_count)
    total_weight = sum(edge_count.values())
    print(f"Edges: {n_edges:,} unique co-occurrence pairs "
          f"(total weight {total_weight:,})")

    # ---- 5. Build Laplacian via srmech.amsc.laplacian ----
    edges = list(edge_count.keys())
    weights = [float(w) for w in edge_count.values()]
    L = dense_laplacian(N, edges, weights)
    print(f"Laplacian: shape={L.shape}, nnz≈{(L != 0).sum()}")

    # ---- 6. Eigendecompose via Class L primitive ----
    print(f"\nEigendecomposing (srmech.amsc.laplacian.hermitian_eigendecompose)...")
    eigvals, eigvecs = hermitian_eigendecompose(L)
    print(f"  Eigvals (sorted ascending; first 5): {eigvals[:5].round(4).tolist()}")
    print(f"  Eigvals (top 5): {eigvals[-5:].round(4).tolist()}")
    print(f"  Eigvecs shape: {eigvecs.shape}")

    # ---- 7. Encode top-K eigenvectors via Path A LoE ----
    # K must be ODD per srmech.amsc.hdc.bundle parity discipline (avoids
    # tie-breaking bias at even voter count — same issue we saw in R-RBS-LM-46a)
    K = 33
    # Use the K LARGEST eigenvalues — these carry the most spectral energy
    top_k_indices = list(range(len(eigvals) - K, len(eigvals)))
    fingerprints = []
    print(f"\nEncoding top-{K} eigenvectors via encode_loe_content (Path A LoE)...")
    for rank, k_idx in enumerate(reversed(top_k_indices)):
        fp = encode_eigenvector(eigvecs[:, k_idx], vocab, top_m=20)
        fingerprints.append(fp)
        if rank < 5:
            # Show what the top eigenvector "contains"
            mag_sq = eigvecs[:, k_idx] * eigvecs[:, k_idx]
            top_5 = sorted(range(N), key=lambda i: -mag_sq[i])[:5]
            print(f"  rank {rank}: eigval={eigvals[k_idx]:.3f}; "
                  f"top tokens: {[vocab[i] for i in top_5]}")

    # ---- 8. Bundle into cascade instrument ----
    instrument = bundle(fingerprints)
    print(f"\nInstrument: {len(instrument)} bytes (D=8192)")

    # ---- 9. Read-mode rank smoke ----
    print(f"\n=== Read-mode smoke ===")

    # Build probe set from common Python idioms + corpus phrases
    static_probes = [
        "def encode_loe_content",
        "def cascade_compose",
        "rotate point angle",
        "instrument bundle",
        "eigenvector eigenvalue",
        "def main",
        "import numpy",
        "class K3Tripartition",
        "self . attribute",
        "for i in range",
        "if not condition",
        "return result",
        "from srmech . amsc",
        "list comprehension",  # generic phrase; expected near baseline
        "completely unrelated jargon flavor",  # expected near baseline (no overlap)
    ]

    # Pool of corpus phrases for baseline
    corpus_phrases = sample_corpus_phrases(file_tokens, n=80, length=8, seed=42)

    # Baseline: pairwise similarity of random corpus-phrase pairs
    rng = random.Random(42)
    baseline_sims = []
    for _ in range(100):
        a, b = rng.sample(corpus_phrases, 2)
        fa = encode_loe_content(a, D=8192)
        fb = encode_loe_content(b, D=8192)
        baseline_sims.append(similarity(fa, fb))

    bl_mean = sum(baseline_sims) / len(baseline_sims)
    bl_max = max(baseline_sims)
    bl_min = min(baseline_sims)
    bl_std = (sum((s - bl_mean) ** 2 for s in baseline_sims) / len(baseline_sims)) ** 0.5
    print(f"Baseline (random corpus-phrase pairs, n=100):")
    print(f"  mean: {bl_mean:+.4f}")
    print(f"  std:  {bl_std:.4f}")
    print(f"  max:  {bl_max:+.4f}")
    print(f"  min:  {bl_min:+.4f}")

    # Also: random encoding pair similarity (true noise floor)
    rng2 = random.Random(99)
    noise_sims = []
    for _ in range(50):
        # Random ASCII strings
        sa = "".join(chr(rng2.randint(32, 126)) for _ in range(40))
        sb = "".join(chr(rng2.randint(32, 126)) for _ in range(40))
        noise_sims.append(similarity(encode_loe_content(sa, D=8192),
                                     encode_loe_content(sb, D=8192)))
    noise_mean = sum(noise_sims) / len(noise_sims)
    print(f"  Random-string pair noise mean: {noise_mean:+.4f}")

    # Probe similarities to the instrument
    print(f"\nProbe similarities vs cascade instrument:")
    probe_results = []
    for p in static_probes:
        fp = encode_loe_content(p, D=8192)
        s = similarity(fp, instrument)
        above_baseline_max = s > bl_max
        z_score = (s - bl_mean) / max(bl_std, 1e-9)
        flag = "***" if above_baseline_max else "**" if z_score > 2 else "*" if z_score > 1 else ""
        probe_results.append({"probe": p, "similarity": s, "z_score": z_score,
                               "above_baseline_max": above_baseline_max})
        print(f"  {p:<40s} sim={s:+.4f}  z={z_score:+.2f}  {flag}")

    # ---- 10. Falsification reading ----
    print(f"\n=== Falsification reading ===")
    n_above_max = sum(1 for r in probe_results if r["above_baseline_max"])
    n_above_2sig = sum(1 for r in probe_results if r["z_score"] > 2)
    n_above_1sig = sum(1 for r in probe_results if r["z_score"] > 1)
    print(f"  Probes above baseline_max: {n_above_max}/{len(probe_results)}")
    print(f"  Probes z > 2 (vs baseline): {n_above_2sig}/{len(probe_results)}")
    print(f"  Probes z > 1 (vs baseline): {n_above_1sig}/{len(probe_results)}")

    if n_above_max >= len(probe_results) // 2:
        verdict = "STRONG signal — Path E cascade preserves code-substrate structure"
    elif n_above_2sig >= len(probe_results) // 3:
        verdict = "SIGNAL — multiple probes above 2σ baseline"
    elif n_above_1sig >= len(probe_results) // 3:
        verdict = "WEAK signal — some probes above 1σ; below strong threshold"
    else:
        verdict = "NO signal — probes indistinguishable from baseline (lossy or wrong encoding for retrieval)"
    print(f"\n  Verdict: {verdict}")

    # ---- 11. Save ----
    output = {
        "partition": "R-RBS-LM-52a",
        "phase": "A — local Python corpus methodology validation",
        "srmech_version": srmech.__version__,
        "corpus_files": [f.name for f in corpus_files],
        "n_files": len(corpus_files),
        "n_tokens_total": n_total,
        "n_tokens_unique": n_unique,
        "vocab_size": N,
        "vocab_coverage_pct": round(100 * coverage, 1),
        "n_edges": n_edges,
        "total_edge_weight": total_weight,
        "laplacian_shape": list(L.shape),
        "eigvals_top_5": eigvals[-5:].tolist(),
        "eigvals_bottom_5": eigvals[:5].tolist(),
        "K_eigenvectors_encoded": K,
        "instrument_bytes": len(instrument),
        "D": 8192,
        "baseline_n": len(baseline_sims),
        "baseline_mean": bl_mean,
        "baseline_std": bl_std,
        "baseline_max": bl_max,
        "baseline_min": bl_min,
        "noise_mean_random_strings": noise_mean,
        "probe_results": probe_results,
        "n_probes_above_baseline_max": n_above_max,
        "n_probes_z_above_2": n_above_2sig,
        "n_probes_z_above_1": n_above_1sig,
        "verdict": verdict,
    }
    out_path = HERE / "R-RBS-LM-52a_results.json"
    out_path.write_text(json.dumps(output, indent=2, default=str))
    print(f"\nResults: {out_path}")


if __name__ == "__main__":
    main()
