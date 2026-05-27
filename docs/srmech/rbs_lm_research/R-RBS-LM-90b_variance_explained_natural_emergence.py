"""R-RBS-LM-90b — Variance-explained spectral analysis for natural tier emergence.

Follow-up to R-RBS-LM-90. The strict gap-cut test (4 tiers from top-3
largest gaps in bottom 14 Laplacian eigvals) returned NULL — none of
the 4 corpora matched 1:3:7:3 exactly.

BUT all 4 corpora qualitatively showed tier-like structure (1 isolated
low + secondary + bulk). The 1:3:7:3 prediction might be at a
DIFFERENT spectral location, or the strict cardinality match might be
the wrong test for "1:3:7'ish."

This follow-up tests a different angle: VARIANCE-EXPLAINED
INTERPRETATION.

If the 14-class A-N architecture predicts:
  1 anchor (dominant direction)
  3 substrate-projection (secondary directions)
  7 cascade-detection (tertiary directions)
  3 meta-cascade (quaternary directions)

then PCA-style analysis of the cooccurrence matrix should show natural
"shoulders" in the variance-explained curve at positions 1, 4, 11, 14.

Test:
  1. Build PMI-weighted cooccurrence (sparser, more meaningful than raw)
  2. Eigendecompose (largest = most variance-explained)
  3. Plot variance-explained per component
  4. Find natural inflection points
  5. Check if those points correspond to 1, 4, 11, 14

Per user direction: "don't force it, let it emerge"
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
    if not p.exists():
        raise FileNotFoundError(path)
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


def pmi_weight(W):
    """Positive pointwise mutual information weighting.

    PMI(x,y) = log( P(x,y) / (P(x)P(y)) )
    Positive PMI (PPMI) keeps only the positive values.
    """
    total = W.sum()
    if total == 0:
        return W
    row_sums = W.sum(axis=1, keepdims=True)
    col_sums = W.sum(axis=0, keepdims=True)
    # Avoid log(0) via small epsilon
    eps = 1e-10
    p_joint = W / total
    p_x = row_sums / total
    p_y = col_sums / total
    # PMI = log(p_joint / (p_x * p_y))
    denom = p_x @ np.ones((1, W.shape[1]))  # wrong... let me fix
    # Actually: p_x.shape (N,1), p_y.shape (1,N), outer (N,N)
    expected = p_x * p_y  # broadcasts to (N,N)
    # Avoid divide-by-zero
    with np.errstate(divide='ignore', invalid='ignore'):
        pmi = np.log((p_joint + eps) / (expected + eps))
    # Positive PMI
    ppmi = np.maximum(pmi, 0.0)
    return ppmi


def variance_explained_curve(M):
    """Eigendecompose symmetric M, return sorted eigvals descending and
    variance-explained per component."""
    # Symmetrize
    M_sym = 0.5 * (M + M.T)
    eigvals = np.linalg.eigvalsh(M_sym)
    # Sort descending (largest variance first)
    eigvals = np.sort(eigvals)[::-1]
    # Variance explained: |eigval| / sum(|eigvals|)  (use abs because
    # PPMI can have negative eigenvalues; we want spectral magnitude)
    abs_eigvals = np.abs(eigvals)
    total = abs_eigvals.sum()
    if total == 0:
        return eigvals, np.zeros_like(eigvals)
    var_explained = abs_eigvals / total
    return eigvals, var_explained


def find_inflection_points(var_explained, n_top=20):
    """Find positions where the variance-explained drops most sharply
    (natural shoulders/breaks)."""
    # Look at the discrete derivative: drop[i] = var[i] - var[i+1]
    drops = -np.diff(var_explained[:n_top + 1])
    # Largest drops indicate where the "explanatory power" decreases most
    # An inflection at position i means "tier through position i,
    # then next tier starts at i+1"
    sorted_drop_idx = np.argsort(drops)[::-1]  # largest first
    return drops, sorted_drop_idx


def analyze_corpus(name, path, vocab_size=200, window=5):
    print(f"\n{'=' * 78}")
    print(f"CORPUS: {name}")
    print(f"{'=' * 78}")

    tokens = load_corpus(path)
    counts = Counter(tokens)
    vocab = [tok for tok, _ in counts.most_common(vocab_size)]
    W = build_cooccurrence(tokens, vocab, window=window)
    W_ppmi = pmi_weight(W)

    eigvals, var_explained = variance_explained_curve(W_ppmi)
    print(f"  tokens={len(tokens):,}  vocab={vocab_size}  window={window}")
    print(f"  PPMI eigvals top-3: {eigvals[:3]}")
    print(f"  PPMI variance-explained top-20:")
    cumvar = 0.0
    for i in range(min(20, len(var_explained))):
        cumvar += var_explained[i]
        bar_len = int(var_explained[i] * 200)
        bar = "█" * bar_len
        print(f"    [{i:2d}] {var_explained[i]:.4f}  cum={cumvar:.4f}  {bar}")

    drops, sorted_drop_idx = find_inflection_points(var_explained, n_top=20)
    print(f"\n  Top-5 inflection points (largest drops in variance):")
    for k in range(5):
        idx = sorted_drop_idx[k]
        print(f"    after position {idx}: drop={drops[idx]:.4f}")

    # Test specific prediction: 1:3:7:3 -> shoulders should appear at
    # cumulative positions 1, 4 (=1+3), 11 (=1+3+7), 14 (=1+3+7+3)
    target_positions = [0, 3, 10, 13]  # 0-indexed: after pos 0, 3, 10, 13
    target_drops = [drops[p] if p < len(drops) else 0.0
                    for p in target_positions]
    median_drop_top20 = float(np.median(drops[:20]))
    # Are these drops larger than median?
    print(f"\n  1:3:7:3 prediction — drops at positions 0, 3, 10, 13:")
    for p, d in zip(target_positions, target_drops):
        is_big = d > median_drop_top20
        print(f"    after position {p:2d}: drop={d:.4f}  "
              f"(median top-20 drop={median_drop_top20:.4f})  "
              f"{'BIG ✓' if is_big else 'normal'}")

    # Check if the predicted positions are among the top-5 drops
    top5_set = set(sorted_drop_idx[:5].tolist())
    target_hits = sum(1 for p in target_positions if p in top5_set)
    print(f"\n  Predicted-position hits in top-5 inflection points: "
          f"{target_hits} / 4")

    return {
        "corpus": name,
        "n_tokens": len(tokens),
        "vocab_size": vocab_size,
        "window": window,
        "eigvals_top_20": [float(x) for x in eigvals[:20]],
        "var_explained_top_20": [float(x) for x in var_explained[:20]],
        "top5_inflection_indices": sorted_drop_idx[:5].tolist(),
        "predicted_position_drops": [float(d) for d in target_drops],
        "predicted_hits_in_top5": target_hits,
    }


def main():
    print("=" * 78)
    print("R-RBS-LM-90b — Variance-explained spectral analysis")
    print("(PPMI cooccurrence; PCA-style eigendecomp; look for natural shoulders)")
    print("=" * 78)

    CORPORA = [
        ("Dante (Italian)",        "/tmp/dante_italian.txt"),
        ("Sherlock Holmes (Eng)",  "/tmp/sherlock.txt"),
        ("McGuffey 6th (Eng)",     "/tmp/mcguffey_sixth.txt"),
        ("OpenStax Algebra (Eng)", "/tmp/openstax_elem_algebra.txt"),
    ]

    results = []
    for name, path in CORPORA:
        try:
            r = analyze_corpus(name, path)
            results.append(r)
        except FileNotFoundError as e:
            print(f"\nSKIP: {e}")

    print("\n\n" + "=" * 78)
    print("SUMMARY")
    print("=" * 78)
    print()
    print(f"{'Corpus':<28} {'Top-5 inflection positions':<30} "
          f"{'1/4/11/14 hits'}")
    print("-" * 78)
    for r in results:
        positions = r["top5_inflection_indices"]
        hits = r["predicted_hits_in_top5"]
        print(f"{r['corpus']:<28} {str(positions):<30} {hits}/4")

    print()
    total_hits = sum(r["predicted_hits_in_top5"] for r in results)
    print(f"Total predicted-position hits across 4 corpora: "
          f"{total_hits} / 16")
    print()
    if total_hits >= 12:
        print("VERDICT: 1:3:7:3 structure DETECTED at variance-explained level.")
    elif total_hits >= 6:
        print("VERDICT: Partial signal — some predicted shoulders appear.")
    else:
        print("VERDICT: 1:3:7:3 prediction not strongly attested at")
        print("  variance-explained level either. Natural shoulders are")
        print("  elsewhere in the spectrum.")

    print()
    print("Per MFO §VII.6.20: form-iso reading; report what emerges.")

    out_path = Path(__file__).parent / "R-RBS-LM-90b_variance_explained_results.json"
    with open(out_path, "w") as f:
        json.dump({"corpora_results": results}, f, indent=2)
    print(f"\nResults saved: {out_path}")


if __name__ == "__main__":
    main()
