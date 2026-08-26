"""R-RBS-LM-92 — Evolution of coupling structure through eigval+eigvec.

User direction 2026-05-27:
> "Keep exploring how structured knowledge seems to evolve through
> coupling and through eigenval structure (or also eigenvector unless
> that's the wrong call)"

Eigenvector IS the right call. Eigenvalues tell us "how concentrated"
the coupling is in each spectral mode; eigenvectors tell us "what"
(which tokens load on that mode). Prior tests looked at eigenvalues
only.

This test tracks BOTH across stages of corpus accumulation:
  - Take a corpus, slice into stages (10%, 25%, 50%, 75%, 100% of tokens)
  - At each stage, build cooccurrence + eigendecompose
  - Report:
    (a) eigvalue spectrum evolution (does it stabilize? what scale?)
    (b) eigvector content evolution (do the same tokens persistently
        dominate the top modes? or do they drift?)
    (c) stability metric: cosine similarity between stage-N and
        stage-(N+1) top-K eigvecs

If knowledge structure has an asymptotic-DoF coupling — the eigvecs
should CONVERGE as the corpus grows. The convergence rate tells us
when the structure has "settled."

If different corpora show similar evolution patterns (same shape of
convergence) — that suggests a universal evolution dynamic.
If they differ — the evolution is corpus-dependent.

Run on 3 corpora:
  - Sherlock Holmes (English narrative)
  - OpenStax Algebra (math discipline)
  - McGuffey 6th (mixed K-12)
"""

import json
import re
from collections import Counter
from pathlib import Path

import numpy as np


TOKEN_RE = re.compile(r"[a-zà-ùA-ZÀ-Ù]+")


def tokenize(text):
    text = text.lower()
    return TOKEN_RE.findall(text)


def load_corpus(path):
    p = Path(path)
    with open(p, encoding="utf-8", errors="ignore") as f:
        return tokenize(f.read())


def build_cooccurrence(tokens, vocab, window=5):
    vocab_idx = {tok: i for i, tok in enumerate(vocab)}
    N = len(vocab)
    W = np.zeros((N, N), dtype=np.float64)
    for i, tok in enumerate(tokens):
        if tok not in vocab_idx:
            continue
        target = vocab_idx[tok]
        start = max(0, i - window)
        end = min(len(tokens), i + window + 1)
        for j in range(start, end):
            if j == i:
                continue
            other = tokens[j]
            if other not in vocab_idx:
                continue
            W[target, vocab_idx[other]] += 1.0
    return W


def ppmi_weight(W):
    total = W.sum()
    if total == 0:
        return W
    row_sums = W.sum(axis=1, keepdims=True)
    col_sums = W.sum(axis=0, keepdims=True)
    eps = 1e-10
    p_joint = W / total
    p_x = row_sums / total
    p_y = col_sums / total
    expected = p_x * p_y
    with np.errstate(divide='ignore', invalid='ignore'):
        pmi = np.log((p_joint + eps) / (expected + eps))
    return np.maximum(pmi, 0.0)


def spectral_decomp(W):
    """Symmetrize + eigendecompose. Returns eigvals descending and
    corresponding eigvecs (columns)."""
    W_sym = 0.5 * (W + W.T)
    eigvals, eigvecs = np.linalg.eigh(W_sym)
    # Sort descending (largest variance first)
    order = np.argsort(eigvals)[::-1]
    return eigvals[order], eigvecs[:, order]


def eigvec_top_tokens(eigvec, vocab, top_k=10):
    """Return the top-K tokens by absolute loading on this eigvec.
    Sign-handled: report with sign (+ for positive loading, - for negative).
    """
    abs_load = np.abs(eigvec)
    top_idx = np.argsort(abs_load)[::-1][:top_k]
    return [
        (vocab[i], float(eigvec[i]))
        for i in top_idx
    ]


def eigvec_cosine_similarity(v1, v2):
    """Cosine similarity (absolute value because eigvec signs are arbitrary)."""
    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    if n1 == 0 or n2 == 0:
        return 0.0
    return float(np.abs(np.dot(v1, v2) / (n1 * n2)))


def analyze_corpus_evolution(name, path, vocab_size=200, window=5):
    print(f"\n{'=' * 78}")
    print(f"CORPUS: {name}")
    print(f"{'=' * 78}")

    tokens = load_corpus(path)
    print(f"  total tokens: {len(tokens):,}")

    # Fix vocabulary to the top-N of the FULL corpus so we can compare
    # across stages with consistent dimension
    counts = Counter(tokens)
    vocab = [tok for tok, _ in counts.most_common(vocab_size)]
    print(f"  fixed vocab: top-{vocab_size}")

    stages = [0.10, 0.25, 0.50, 0.75, 1.00]
    stage_results = []
    prev_eigvecs = None

    for stage in stages:
        n = int(len(tokens) * stage)
        stage_tokens = tokens[:n]

        W = build_cooccurrence(stage_tokens, vocab, window=window)
        W_ppmi = ppmi_weight(W)
        eigvals, eigvecs = spectral_decomp(W_ppmi)

        # Track top-5 eigvec content
        top_eigvec_content = []
        for k in range(5):
            top_eigvec_content.append(
                eigvec_top_tokens(eigvecs[:, k], vocab, top_k=8)
            )

        # Cosine similarity to previous stage's top-5 eigvecs (where applicable)
        stability = []
        if prev_eigvecs is not None:
            for k in range(5):
                sim = eigvec_cosine_similarity(
                    eigvecs[:, k], prev_eigvecs[:, k])
                stability.append(sim)

        stage_results.append({
            "stage": stage,
            "n_tokens_used": n,
            "top_5_eigvals": [float(x) for x in eigvals[:5]],
            "top_5_eigvec_content": [
                [(tok, load) for tok, load in mode]
                for mode in top_eigvec_content
            ],
            "stability_vs_prev": stability,
        })
        prev_eigvecs = eigvecs.copy()

    # Print evolution
    print(f"\n  Stage-by-stage top-5 eigenvalues:")
    print(f"  {'stage':<8} {'n_tok':<10} {'eig1':<8} {'eig2':<8} "
          f"{'eig3':<8} {'eig4':<8} {'eig5':<8}")
    for sr in stage_results:
        evs = sr["top_5_eigvals"]
        print(f"  {sr['stage']:<8.2f} {sr['n_tokens_used']:<10,} "
              f"{evs[0]:<8.2f} {evs[1]:<8.2f} {evs[2]:<8.2f} "
              f"{evs[3]:<8.2f} {evs[4]:<8.2f}")

    print(f"\n  Top-5 eigvec STABILITY (cosine sim vs prior stage):")
    print(f"  {'stage':<8} {'eig1':<8} {'eig2':<8} {'eig3':<8} "
          f"{'eig4':<8} {'eig5':<8}")
    for sr in stage_results:
        if sr["stability_vs_prev"]:
            s = sr["stability_vs_prev"]
            print(f"  {sr['stage']:<8.2f} {s[0]:<8.3f} {s[1]:<8.3f} "
                  f"{s[2]:<8.3f} {s[3]:<8.3f} {s[4]:<8.3f}")

    print(f"\n  Top-3 eigvec CONTENT at FINAL stage:")
    final = stage_results[-1]
    for k in range(3):
        mode_content = final["top_5_eigvec_content"][k]
        toks_str = ", ".join(
            f"{tok}({load:+.2f})"
            for tok, load in mode_content[:6])
        print(f"    eigvec[{k}]: {toks_str}")

    # Also print top-3 eigvec content at FIRST stage to compare
    print(f"\n  Top-3 eigvec CONTENT at FIRST stage (10% of corpus):")
    first = stage_results[0]
    for k in range(3):
        mode_content = first["top_5_eigvec_content"][k]
        toks_str = ", ".join(
            f"{tok}({load:+.2f})"
            for tok, load in mode_content[:6])
        print(f"    eigvec[{k}]: {toks_str}")

    return {
        "corpus": name,
        "total_tokens": len(tokens),
        "vocab_size": vocab_size,
        "window": window,
        "stage_results": stage_results,
    }


def main():
    print("=" * 78)
    print("R-RBS-LM-92 — Coupling evolution through eigvals + eigvecs")
    print("(does coupling structure converge with corpus accumulation?)")
    print("=" * 78)

    CORPORA = [
        ("Sherlock Holmes",   "/tmp/sherlock.txt"),
        ("OpenStax Algebra",  "/tmp/openstax_elem_algebra.txt"),
        ("McGuffey 6th",      "/tmp/mcguffey_sixth.txt"),
    ]

    results = []
    for name, path in CORPORA:
        try:
            r = analyze_corpus_evolution(name, path)
            results.append(r)
        except FileNotFoundError:
            print(f"\nSKIP: {path} not found")

    print("\n\n" + "=" * 78)
    print("CROSS-CORPUS COMPARISON")
    print("=" * 78)
    print()

    # Compare final stability across corpora — does each show the
    # same convergence pattern?
    print("Final-stage (75% → 100%) top-5 eigvec stability:")
    print(f"  {'corpus':<24} {'eig1':<8} {'eig2':<8} {'eig3':<8} "
          f"{'eig4':<8} {'eig5':<8}  mean")
    for r in results:
        if r["stage_results"][-1]["stability_vs_prev"]:
            s = r["stage_results"][-1]["stability_vs_prev"]
            mean_s = np.mean(s)
            print(f"  {r['corpus']:<24} {s[0]:<8.3f} {s[1]:<8.3f} "
                  f"{s[2]:<8.3f} {s[3]:<8.3f} {s[4]:<8.3f}  {mean_s:.3f}")
    print()

    # Compare top eigvec1 content across corpora (universal anchor token set?)
    print("Top eigvec[0] (anchor) content at full corpus, across corpora:")
    print("-" * 78)
    for r in results:
        final = r["stage_results"][-1]
        mode_content = final["top_5_eigvec_content"][0]
        toks = [tok for tok, _ in mode_content[:8]]
        print(f"  {r['corpus']:<24}: {', '.join(toks)}")
    print()

    # Save
    out_path = (Path(__file__).parent
                / "R-RBS-LM-92_coupling_evolution_results.json")
    with open(out_path, "w") as f:
        json.dump({"corpora_results": results}, f, indent=2)
    print(f"Results saved: {out_path}")


if __name__ == "__main__":
    main()
