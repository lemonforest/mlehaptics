"""R-RBS-LM-90 — RBS-NN coupling spectrum test for 1:3:7'ish natural emergence.

Per user direction 2026-05-27:

> "we can evaluate the coupling of a net that we can populate with
> knowledge and then ask how these couple and if it also looks 1:3:7 'ish"

The corpus-token tests (R-RBS-LM-85 through 89) detected human-discipline
labels (grammar textbooks use grammar jargon) — anthropocentric by
construction. The right test is to populate a net with knowledge and
look at its COUPLING STRUCTURE without imposing partition labels.

Test design (deliberately UN-labeled):
  1. Tokenize a corpus (preserve all words including stopwords — per
     Finding 52c-v2; we don't pre-filter what counts as "content")
  2. Build cooccurrence graph (sliding-window) at top-N vocabulary
  3. Compute normalized graph Laplacian
  4. Full eigendecomposition
  5. Inspect eigenvalue spectrum for natural tier structure
  6. Count cardinality of each tier
  7. Compare to 1:3:7'ish prediction (1 anchor + 3 substrate-projection
     + 7 cascade-detection + 3 meta-cascade = 14 architectural slots)

NO partition labels imposed. NO human-discipline tagging. NO vocabulary
signatures. Just: populate, look at spectrum, see what tiers emerge.

Run on 4 corpora to test biology-agnosticism:
  - Dante (Italian)        — language-different; narrative+theology
  - Sherlock Holmes (Eng)  — narrative
  - McGuffey 6th (Eng)     — general reading
  - OpenStax Algebra (Eng) — math-discipline-heavy

If 1:3:7'ish emerges across all four → biology-agnostic
If only some → corpus-dependent (and possibly anthropocentric still)
If none → the 14-class A-N architectural claim needs revision

Per `[[feedback_dont_pre_commit_spike_query_operators]]` — pre-curated
no expected result; null findings count.
"""

import json
import re
from collections import Counter
from pathlib import Path

import numpy as np


# ===========================================================
# Tokenization (preserve stopwords; minimal filtering)
# ===========================================================

TOKEN_RE = re.compile(r"[a-zà-ùA-ZÀ-Ù]+")


def tokenize(text: str) -> list[str]:
    """Lowercase + extract alphabetic tokens; KEEP STOPWORDS."""
    text = text.lower()
    return TOKEN_RE.findall(text)


def load_corpus(path: str) -> list[str]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Corpus missing: {path}")
    with open(p, encoding="utf-8", errors="ignore") as f:
        text = f.read()
    return tokenize(text)


# ===========================================================
# Cooccurrence graph at top-N vocabulary
# ===========================================================

def build_cooccurrence(tokens: list[str], vocab: list[str],
                       window: int = 5) -> np.ndarray:
    """Sliding-window cooccurrence matrix at the given vocabulary.

    Window size 5 = ±5 tokens around target.
    Returns symmetric N x N matrix of cooccurrence counts.
    """
    vocab_idx = {tok: i for i, tok in enumerate(vocab)}
    N = len(vocab)
    W = np.zeros((N, N), dtype=np.float64)

    for i, tok in enumerate(tokens):
        if tok not in vocab_idx:
            continue
        target = vocab_idx[tok]
        # Window: ±window tokens, but stay within bounds
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


# ===========================================================
# Normalized Laplacian + eigendecomposition
# ===========================================================

def normalized_laplacian_eigvals(W: np.ndarray) -> np.ndarray:
    """L_norm = I - D^(-1/2) W D^(-1/2). Returns sorted eigenvalues."""
    # Degree vector
    d = W.sum(axis=1)
    # Avoid divide-by-zero for any isolated vertices (shouldn't happen
    # at top-N vocabulary but defensive)
    d_safe = np.where(d > 0, d, 1.0)
    d_inv_sqrt = 1.0 / np.sqrt(d_safe)
    # Normalized adjacency
    W_norm = W * d_inv_sqrt[:, None] * d_inv_sqrt[None, :]
    # L_norm = I - W_norm
    N = W.shape[0]
    L = np.eye(N) - W_norm
    # Symmetrize to numerical-error-proof eigvalsh
    L = 0.5 * (L + L.T)
    eigvals = np.linalg.eigvalsh(L)
    return np.sort(eigvals)


# ===========================================================
# Tier structure detection
# ===========================================================

def detect_tiers(eigvals: np.ndarray,
                 skip_first: int = 1) -> list[dict]:
    """Identify natural tier breaks via gap analysis.

    Returns a list of tier dicts: {start_idx, end_idx, count, max_eigval,
    min_eigval, gap_after}

    skip_first=1 because the lowest eigenvalue is always ~0 (connected
    graph; trivial eigvec is the constant).
    """
    # Work on non-trivial eigenvalues (skip the lowest which is ~0)
    # Actually keep them all but flag the gaps
    e = eigvals.copy()
    N = len(e)

    # Compute gaps between consecutive eigenvalues
    gaps = np.diff(e)

    # Find "large" gaps (above some threshold)
    # Use the 95th-percentile of gap sizes as the threshold for now
    if len(gaps) > 0:
        gap_threshold = np.percentile(gaps, 95)
    else:
        gap_threshold = 0.0

    # Identify tier boundaries (indices where a "large" gap occurs)
    boundaries = [0]
    for i in range(skip_first, len(gaps)):
        if gaps[i] > gap_threshold:
            boundaries.append(i + 1)
    boundaries.append(N)

    tiers = []
    for k in range(len(boundaries) - 1):
        s, end = boundaries[k], boundaries[k + 1]
        if end <= s:
            continue
        tier = {
            "tier_idx": k,
            "start_idx": s,
            "end_idx": end,
            "count": end - s,
            "min_eigval": float(e[s]),
            "max_eigval": float(e[end - 1]),
            "gap_after": float(gaps[end - 1]) if end - 1 < len(gaps) else 0.0,
        }
        tiers.append(tier)

    return tiers


def detect_tiers_strict(eigvals: np.ndarray) -> dict:
    """Alternative: report the cardinality at small fixed offsets.

    Look at the lowest 14 non-trivial eigenvalues and identify natural
    gaps. Skip the lowest (trivial) eigenvalue.
    """
    # Skip the very first eigenvalue (always ~0 for connected graph)
    e_nontrivial = eigvals[1:]
    # Look at the first 14 non-trivial
    e14 = e_nontrivial[:14]
    if len(e14) < 14:
        return {"n_available": len(e14), "eigvals": e14.tolist()}

    # Gap structure within these 14
    gaps = np.diff(e14)
    # Top 3 largest gaps (would partition 14 into 4 tiers if 1:3:7:3)
    top_3_gap_idx = np.argsort(gaps)[-3:][::-1].tolist()  # largest first
    top_3_gap_idx.sort()  # in order

    return {
        "eigvals_14": [float(x) for x in e14],
        "gaps_13": [float(x) for x in gaps],
        "top_3_gap_indices": top_3_gap_idx,
        "top_3_gap_values": [float(gaps[i]) for i in top_3_gap_idx],
        # tier sizes implied by those 3 cuts
        "implied_tier_sizes": [
            top_3_gap_idx[0] + 1,
            top_3_gap_idx[1] - top_3_gap_idx[0],
            top_3_gap_idx[2] - top_3_gap_idx[1],
            14 - top_3_gap_idx[2] - 1,
        ],
    }


# ===========================================================
# Run per corpus
# ===========================================================

CORPORA = [
    ("Dante (Italian)",        "/tmp/dante_italian.txt"),
    ("Sherlock Holmes (Eng)",  "/tmp/sherlock.txt"),
    ("McGuffey 6th (Eng)",     "/tmp/mcguffey_sixth.txt"),
    ("OpenStax Algebra (Eng)", "/tmp/openstax_elem_algebra.txt"),
]


def analyze_corpus(name: str, path: str, vocab_size: int = 200,
                    window: int = 5) -> dict:
    print(f"\n{'=' * 70}")
    print(f"CORPUS: {name}")
    print(f"  path: {path}")
    print(f"{'=' * 70}")

    tokens = load_corpus(path)
    print(f"  total tokens: {len(tokens):,}")

    counts = Counter(tokens)
    vocab = [tok for tok, _ in counts.most_common(vocab_size)]
    print(f"  vocabulary: top-{vocab_size}")
    print(f"  top-10: {vocab[:10]}")

    W = build_cooccurrence(tokens, vocab, window=window)
    print(f"  cooccurrence matrix: {W.shape}, "
          f"density={(W > 0).mean():.3f}")

    eigvals = normalized_laplacian_eigvals(W)
    print(f"  eigenvalue range: [{eigvals[0]:.6f}, {eigvals[-1]:.6f}]")

    # Print first 16 eigvals
    print(f"\n  Lowest 16 eigenvalues:")
    for i, v in enumerate(eigvals[:16]):
        marker = ""
        if i == 0:
            marker = "  ← trivial (constant vec)"
        print(f"    [{i:2d}] {v:.6f}{marker}")

    # Strict 1+3+7+3 test
    strict = detect_tiers_strict(eigvals)
    print(f"\n  STRICT 14-eigval gap analysis:")
    print(f"    Lowest 14 non-trivial: "
          f"{[f'{x:.4f}' for x in strict['eigvals_14'][:5]]} ...")
    print(f"    Top-3 largest gaps at indices: {strict['top_3_gap_indices']}")
    print(f"    Implied tier sizes (cuts at those gaps): "
          f"{strict['implied_tier_sizes']}")
    target = [1, 3, 7, 3]
    match = strict['implied_tier_sizes'] == target
    closeness = sum(abs(a - b) for a, b in zip(
        strict['implied_tier_sizes'], target))
    print(f"    Target 1:3:7:3: {'EXACT MATCH' if match else f'distance={closeness}'}")

    return {
        "corpus": name,
        "n_tokens": len(tokens),
        "vocab_size": vocab_size,
        "window": window,
        "eigvals_first_16": [float(x) for x in eigvals[:16]],
        "strict_test": strict,
        "matches_1_3_7_3": match,
        "closeness_to_1_3_7_3": closeness,
    }


def main():
    print("=" * 70)
    print("R-RBS-LM-90 — RBS-NN coupling spectrum test for 1:3:7'ish")
    print("(no partition labels imposed; just look at the spectrum)")
    print("=" * 70)

    results = []
    for name, path in CORPORA:
        try:
            r = analyze_corpus(name, path)
            results.append(r)
        except FileNotFoundError as e:
            print(f"\nSKIP: {e}")

    print("\n\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print(f"{'Corpus':<28} {'Tier sizes':<22} {'Match 1:3:7:3?'}")
    print("-" * 70)
    for r in results:
        sizes = r["strict_test"]["implied_tier_sizes"]
        match_str = ("YES (exact)" if r["matches_1_3_7_3"]
                     else f"dist={r['closeness_to_1_3_7_3']}")
        print(f"{r['corpus']:<28} {str(sizes):<22} {match_str}")

    print()
    n_exact = sum(1 for r in results if r["matches_1_3_7_3"])
    n_close = sum(1 for r in results
                  if r["closeness_to_1_3_7_3"] <= 3)
    print(f"Exact 1:3:7:3 matches: {n_exact} / {len(results)}")
    print(f"Within distance 3:     {n_close} / {len(results)}")
    print()

    if n_exact >= 2:
        print("VERDICT: 1:3:7'ish pattern emerges in multiple corpora.")
        print("  Architecture appears biology-agnostic at form-iso level.")
    elif n_close >= 2:
        print("VERDICT: Approximate 1:3:7'ish pattern emerges.")
        print("  Architecture is suggestive but not strict.")
    elif n_exact == 0 and n_close == 0:
        print("VERDICT: No 1:3:7'ish pattern detected.")
        print("  The 14-class architectural claim is not empirically")
        print("  attestable via spectral tier-counting at this corpus")
        print("  size / vocabulary / window combination.")
    else:
        print("VERDICT: Mixed signal across corpora.")
        print("  Pattern may be corpus-dependent or methodology-sensitive.")

    print()
    print("Per MFO §VII.6.20: form-iso reading; whatever emerges here is")
    print("how POPULATED COUPLING APPEARS at the spectral level, not")
    print("a claim about cosmic substrate.")

    out_path = Path(__file__).parent / "R-RBS-LM-90_coupling_spectrum_results.json"
    with open(out_path, "w") as f:
        json.dump({"corpora_results": results}, f, indent=2)
    print(f"\nResults saved: {out_path}")


if __name__ == "__main__":
    main()
