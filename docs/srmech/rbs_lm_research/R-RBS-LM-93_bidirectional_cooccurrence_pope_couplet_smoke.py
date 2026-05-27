"""R-RBS-LM-93 — Bidirectional cooccurrence Pope-couplet test.

Per user direction 2026-05-27:
> "pope's strict prose where the shape of the end had to meet the shape
> of the next line is very much like our primitive operators, the
> form/function that creates the structure for a discrete now also
> shapes the structure of what is next and what was last by the same
> very form/function. we tossed this aside because it was hard to find
> NN matchy things but this may be a valuable tool elsewhere, or even
> in explaining the primitives"

The Pope heroic-couplet structure says the operator shapes past +
present + future BIDIRECTIONALLY. Static symmetric cooccurrence
(R-RBS-LM-85 through R-RBS-LM-92) FLATTENS this — it can't see
forward-vs-backward asymmetry that would reveal sequence-operators.

This test builds FORWARD and BACKWARD cooccurrence matrices
separately:
  W_fwd[i, j] = count(j appears after i within window)
  W_bwd[i, j] = count(j appears before i within window)

For order-invariant patterns: W_fwd ≈ W_bwd^T (symmetric)
For sequence-operators: W_fwd ≠ W_bwd^T (asymmetric)

Tokens with high forward/backward asymmetry are candidates for
sequence-operator-like behavior (the trailing 3? the meta-cascade?).

Run on a corpus and report:
  (a) Overall asymmetry: norm(W_fwd - W_bwd^T) / norm(W_fwd + W_bwd^T)
  (b) Per-token asymmetry: which tokens have most-asymmetric profiles
  (c) Eigenstructure of W_fwd vs W_bwd vs W_sym = (W_fwd + W_bwd^T)/2

If forward/backward eigenstructure differs significantly → there's
sequence-operator content that static cooccurrence misses.
If they're essentially the same → the static tests captured most
of the available signal.

NO partition labels imposed. No predicted result.
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


def build_directional_cooccurrence(tokens, vocab, window=5):
    """Return (W_fwd, W_bwd) where:
      W_fwd[i, j] = count of j appearing AFTER i within window
      W_bwd[i, j] = count of j appearing BEFORE i within window
    Both are N x N matrices."""
    vocab_idx = {tok: i for i, tok in enumerate(vocab)}
    N = len(vocab)
    W_fwd = np.zeros((N, N), dtype=np.float64)
    W_bwd = np.zeros((N, N), dtype=np.float64)

    for i, tok in enumerate(tokens):
        if tok not in vocab_idx:
            continue
        target = vocab_idx[tok]
        # FORWARD: j in (i, i+window]
        end = min(len(tokens), i + window + 1)
        for j in range(i + 1, end):
            other = tokens[j]
            if other not in vocab_idx:
                continue
            W_fwd[target, vocab_idx[other]] += 1.0
        # BACKWARD: j in [i-window, i)
        start = max(0, i - window)
        for j in range(start, i):
            other = tokens[j]
            if other not in vocab_idx:
                continue
            W_bwd[target, vocab_idx[other]] += 1.0
    return W_fwd, W_bwd


def asymmetry_score(W_fwd, W_bwd):
    """Overall asymmetry: norm(W_fwd - W_bwd^T) / norm(W_fwd + W_bwd^T).

    If W_fwd[i,j] = count(j after i) and W_bwd[i,j] = count(j before i)
    then in a symmetric setting we expect W_fwd[i,j] ≈ W_bwd[j,i] (i.e.,
    W_fwd ≈ W_bwd^T). Asymmetry is the deviation from that.
    """
    diff = W_fwd - W_bwd.T
    total = W_fwd + W_bwd.T
    n_diff = np.linalg.norm(diff)
    n_total = np.linalg.norm(total)
    if n_total == 0:
        return 0.0
    return float(n_diff / n_total)


def per_token_asymmetry(W_fwd, W_bwd, vocab):
    """For each token, compute its forward-profile vs backward-profile
    distance.

    forward_profile[i] = row i of W_fwd (what follows token i)
    backward_profile[i] = row i of W_bwd (what precedes token i)

    Tokens with very different forward and backward profiles are
    sequence-asymmetric.
    """
    scores = []
    for i, tok in enumerate(vocab):
        fwd = W_fwd[i]
        bwd = W_bwd[i]
        # Normalize
        n_f = np.linalg.norm(fwd)
        n_b = np.linalg.norm(bwd)
        if n_f > 0 and n_b > 0:
            fwd_n = fwd / n_f
            bwd_n = bwd / n_b
            cos_sim = float(fwd_n @ bwd_n)
        else:
            cos_sim = 0.0
        scores.append((tok, cos_sim, float(n_f), float(n_b)))
    return sorted(scores, key=lambda x: x[1])  # most-asymmetric first


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
    W_sym = 0.5 * (W + W.T)
    eigvals, eigvecs = np.linalg.eigh(W_sym)
    order = np.argsort(eigvals)[::-1]
    return eigvals[order], eigvecs[:, order]


def eigvec_top_tokens(eigvec, vocab, top_k=8):
    abs_load = np.abs(eigvec)
    top_idx = np.argsort(abs_load)[::-1][:top_k]
    return [(vocab[i], float(eigvec[i])) for i in top_idx]


def analyze_corpus_bidirectional(name, path, vocab_size=200, window=5):
    print(f"\n{'=' * 78}")
    print(f"CORPUS: {name}")
    print(f"{'=' * 78}")

    tokens = load_corpus(path)
    counts = Counter(tokens)
    vocab = [tok for tok, _ in counts.most_common(vocab_size)]

    print(f"  tokens={len(tokens):,}  vocab={vocab_size}  window={window}")

    W_fwd, W_bwd = build_directional_cooccurrence(tokens, vocab, window)
    W_sym = 0.5 * (W_fwd + W_bwd.T)  # symmetric combination

    # Overall asymmetry
    asym = asymmetry_score(W_fwd, W_bwd)
    print(f"\n  Overall asymmetry score: {asym:.4f}")
    print(f"    (0 = fully symmetric; 1 = fully asymmetric)")

    # Per-token asymmetry
    per_tok = per_token_asymmetry(W_fwd, W_bwd, vocab)
    print(f"\n  Top-15 MOST-ASYMMETRIC tokens (low cos sim between fwd/bwd):")
    for i in range(15):
        tok, sim, nf, nb = per_tok[i]
        print(f"    {tok:<18}  fwd<->bwd cos sim={sim:.3f}  "
              f"|fwd|={nf:.1f}  |bwd|={nb:.1f}")

    print(f"\n  Top-5 MOST-SYMMETRIC tokens (high cos sim):")
    for i in range(5):
        tok, sim, nf, nb = per_tok[-(i + 1)]
        print(f"    {tok:<18}  fwd<->bwd cos sim={sim:.3f}  "
              f"|fwd|={nf:.1f}  |bwd|={nb:.1f}")

    # Compare eigenstructures
    W_fwd_ppmi = ppmi_weight(W_fwd)
    W_bwd_ppmi = ppmi_weight(W_bwd)
    W_sym_ppmi = ppmi_weight(W_sym)

    eigvals_f, eigvecs_f = spectral_decomp(W_fwd_ppmi)
    eigvals_b, eigvecs_b = spectral_decomp(W_bwd_ppmi)
    eigvals_s, eigvecs_s = spectral_decomp(W_sym_ppmi)

    print(f"\n  Top-5 eigenvalues (FWD / BWD / SYM):")
    for k in range(5):
        print(f"    [{k}] fwd={eigvals_f[k]:.2f}  bwd={eigvals_b[k]:.2f}  "
              f"sym={eigvals_s[k]:.2f}")

    # Top eigvec content comparison
    print(f"\n  Top eigvec[0] content (FWD):")
    toks_f = eigvec_top_tokens(eigvecs_f[:, 0], vocab, 6)
    print(f"    " + ", ".join(f"{t}({l:+.2f})" for t, l in toks_f))
    print(f"  Top eigvec[0] content (BWD):")
    toks_b = eigvec_top_tokens(eigvecs_b[:, 0], vocab, 6)
    print(f"    " + ", ".join(f"{t}({l:+.2f})" for t, l in toks_b))
    print(f"  Top eigvec[0] content (SYM):")
    toks_s = eigvec_top_tokens(eigvecs_s[:, 0], vocab, 6)
    print(f"    " + ", ".join(f"{t}({l:+.2f})" for t, l in toks_s))

    # Compute eigvec[0] FWD vs BWD cosine sim
    eigvec0_sim = float(np.abs(
        eigvecs_f[:, 0] @ eigvecs_b[:, 0] /
        (np.linalg.norm(eigvecs_f[:, 0]) * np.linalg.norm(eigvecs_b[:, 0]))
    ))
    print(f"\n  Cosine similarity FWD eigvec[0] vs BWD eigvec[0]: "
          f"{eigvec0_sim:.4f}")
    print(f"    (high = same direction; low = direction-asymmetric)")

    return {
        "corpus": name,
        "n_tokens": len(tokens),
        "overall_asymmetry": asym,
        "top_15_asymmetric": [
            {"token": t, "fwd_bwd_cos_sim": s, "fwd_norm": nf, "bwd_norm": nb}
            for t, s, nf, nb in per_tok[:15]
        ],
        "top_5_symmetric": [
            {"token": t, "fwd_bwd_cos_sim": s, "fwd_norm": nf, "bwd_norm": nb}
            for t, s, nf, nb in per_tok[-5:]
        ],
        "top_5_eigvals_fwd": [float(x) for x in eigvals_f[:5]],
        "top_5_eigvals_bwd": [float(x) for x in eigvals_b[:5]],
        "top_5_eigvals_sym": [float(x) for x in eigvals_s[:5]],
        "eigvec0_fwd_vs_bwd_sim": eigvec0_sim,
        "eigvec0_content_fwd": [(t, l) for t, l in toks_f],
        "eigvec0_content_bwd": [(t, l) for t, l in toks_b],
        "eigvec0_content_sym": [(t, l) for t, l in toks_s],
    }


def main():
    print("=" * 78)
    print("R-RBS-LM-93 — Bidirectional cooccurrence Pope-couplet test")
    print("(does forward vs backward direction reveal sequence-operators?)")
    print("=" * 78)

    CORPORA = [
        ("Sherlock Holmes",     "/tmp/sherlock.txt"),
        ("OpenStax Algebra",    "/tmp/openstax_elem_algebra.txt"),
        ("Dante Italian",       "/tmp/dante_italian.txt"),
        ("McGuffey 6th",        "/tmp/mcguffey_sixth.txt"),
    ]

    results = []
    for name, path in CORPORA:
        try:
            r = analyze_corpus_bidirectional(name, path)
            results.append(r)
        except FileNotFoundError:
            print(f"\nSKIP: {path}")

    print("\n\n" + "=" * 78)
    print("CROSS-CORPUS SUMMARY")
    print("=" * 78)
    print()
    print(f"{'Corpus':<22} {'Asymmetry':<12} {'FWD vs BWD eigvec[0] sim'}")
    print("-" * 78)
    for r in results:
        print(f"{r['corpus']:<22} {r['overall_asymmetry']:<12.4f} "
              f"{r['eigvec0_fwd_vs_bwd_sim']:.4f}")

    print()
    print("Are the most-asymmetric tokens consistent across corpora?")
    print("-" * 78)
    # Get top-5 asymmetric per corpus
    for r in results:
        tops = [t["token"] for t in r["top_15_asymmetric"][:5]]
        print(f"  {r['corpus']:<22}: {', '.join(tops)}")

    out_path = (Path(__file__).parent
                / "R-RBS-LM-93_bidirectional_results.json")
    with open(out_path, "w") as f:
        json.dump({"corpora_results": results}, f, indent=2)
    print(f"\nResults saved: {out_path}")


if __name__ == "__main__":
    main()
