"""R-RBS-LM-94 — Arts-corpus transmission-function vs substrate-content test.

Tests user's earlier framework reading hypothesis:
> "are all of the Arts all about sharing internal imagery and the
> abstract with others as a means of sharing knowledge?"

If arts are TRANSMISSION-FUNCTION (externalizing internal state for
inter-individual sharing), their eigenstructure should look different
from substrate-content corpora:
  - Substrate-content corpora: clean dominant axis capturing substrate-in-use
  - Transmission corpora: multi-coupled with no dominant single substrate,
    OR: dominant axis captures the rendering/encoding vocabulary rather
    than substrate content

Test:
  1. Build combined arts corpus (drawing + perspective + music_theory)
  2. Compute eigenstructure
  3. Compare top-K eigvec content + variance-explained shape to
     substrate-content corpora (Sherlock / OpenStax / McGuffey)
  4. Report differences in shape and content

If arts shows clear single dominant axis with substrate-like content
  → arts IS specialized substrate (not transmission-distinct)
If arts shows multi-coupled spectrum with rendering-like vocabulary
  → arts behaves as transmission function
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


def load_corpus_files(paths):
    all_tokens = []
    for p in paths:
        path = Path(p)
        if not path.exists():
            continue
        with open(path, encoding="utf-8", errors="ignore") as f:
            all_tokens.extend(tokenize(f.read()))
    return all_tokens


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
    W_sym = 0.5 * (W + W.T)
    eigvals, eigvecs = np.linalg.eigh(W_sym)
    order = np.argsort(eigvals)[::-1]
    return eigvals[order], eigvecs[:, order]


def variance_explained_curve(eigvals):
    abs_eigvals = np.abs(eigvals)
    total = abs_eigvals.sum()
    if total == 0:
        return np.zeros_like(eigvals)
    return abs_eigvals / total


def eigvec_top_tokens(eigvec, vocab, top_k=10):
    abs_load = np.abs(eigvec)
    top_idx = np.argsort(abs_load)[::-1][:top_k]
    return [(vocab[i], float(eigvec[i])) for i in top_idx]


def analyze_corpus(name, paths, vocab_size=200, window=5):
    print(f"\n{'=' * 78}")
    print(f"CORPUS: {name}")
    print(f"{'=' * 78}")

    tokens = load_corpus_files(paths)
    print(f"  tokens={len(tokens):,}")

    counts = Counter(tokens)
    vocab = [tok for tok, _ in counts.most_common(vocab_size)]
    W = build_cooccurrence(tokens, vocab, window)
    W_ppmi = ppmi_weight(W)
    eigvals, eigvecs = spectral_decomp(W_ppmi)
    var_exp = variance_explained_curve(eigvals)

    print(f"  Top-10 eigvals: " +
          ", ".join(f"{v:.2f}" for v in eigvals[:10]))
    print(f"  Var-explained top-10: " +
          ", ".join(f"{v:.3f}" for v in var_exp[:10]))
    cumvar_top1 = var_exp[0]
    cumvar_top3 = var_exp[:3].sum()
    cumvar_top10 = var_exp[:10].sum()
    print(f"  Cumvar [1/3/10]: {cumvar_top1:.3f} / "
          f"{cumvar_top3:.3f} / {cumvar_top10:.3f}")

    # Top-3 eigvec content
    print(f"\n  Top-3 eigvec content:")
    for k in range(3):
        toks = eigvec_top_tokens(eigvecs[:, k], vocab, 8)
        print(f"    eigvec[{k}]: " +
              ", ".join(f"{t}({l:+.2f})" for t, l in toks))

    # Spectral concentration metric: how much of total variance in
    # top-K?
    # Low cumvar_top1 + high cumvar_top10 = multi-coupled / no single dom axis
    # High cumvar_top1 = clean dominant axis
    cumvar_drop_0_to_1 = var_exp[0] - var_exp[1]
    print(f"\n  Spectral concentration (1->2 drop): {cumvar_drop_0_to_1:.4f}")

    return {
        "corpus": name,
        "n_tokens": len(tokens),
        "top_10_eigvals": [float(v) for v in eigvals[:10]],
        "var_explained_top_10": [float(v) for v in var_exp[:10]],
        "cumvar_top_1": float(cumvar_top1),
        "cumvar_top_3": float(cumvar_top3),
        "cumvar_top_10": float(cumvar_top10),
        "spectral_concentration_drop_0_1": float(cumvar_drop_0_to_1),
        "top_3_eigvec_content": [
            [(t, l) for t, l in eigvec_top_tokens(eigvecs[:, k], vocab, 8)]
            for k in range(3)
        ],
    }


def main():
    print("=" * 78)
    print("R-RBS-LM-94 — Arts transmission-function vs substrate-content")
    print("=" * 78)

    CORPORA = [
        # Combined arts (transmission-function candidate)
        ("ARTS (combined: drawing+perspective+music)", [
            "/tmp/ec_drawing_easy.txt",
            "/tmp/ec_perspective_art.txt",
            "/tmp/ec_music_theory.txt",
        ]),
        # Substrate-content reference corpora
        ("Substrate: Sherlock Holmes", ["/tmp/sherlock.txt"]),
        ("Substrate: OpenStax Algebra", ["/tmp/openstax_elem_algebra.txt"]),
        ("Substrate: McGuffey 6th", ["/tmp/mcguffey_sixth.txt"]),
    ]

    results = []
    for name, paths in CORPORA:
        try:
            r = analyze_corpus(name, paths)
            results.append(r)
        except (FileNotFoundError, IndexError) as e:
            print(f"\nSKIP {name}: {e}")

    print("\n\n" + "=" * 78)
    print("COMPARISON — arts vs substrate-content corpora")
    print("=" * 78)
    print()
    print(f"{'Corpus':<42} {'top1':<8} {'top3':<8} "
          f"{'top10':<8} {'drop[0->1]'}")
    print("-" * 78)
    for r in results:
        print(f"{r['corpus']:<42} {r['cumvar_top_1']:<8.3f} "
              f"{r['cumvar_top_3']:<8.3f} {r['cumvar_top_10']:<8.3f} "
              f"{r['spectral_concentration_drop_0_1']:.4f}")

    print()
    print("INTERPRETATION:")
    print("  cumvar_top_1 HIGH    = clean dominant axis (single substrate)")
    print("  cumvar_top_1 LOW     = multi-coupled / no single dominant axis")
    print("  spectral drop 0->1   = how sharply the dominant axis stands out")
    print()

    arts = next((r for r in results if "ARTS" in r["corpus"]), None)
    if arts:
        substrate_results = [r for r in results if "Substrate" in r["corpus"]]
        if substrate_results:
            arts_top1 = arts["cumvar_top_1"]
            substrate_top1s = [r["cumvar_top_1"] for r in substrate_results]
            avg_substrate_top1 = np.mean(substrate_top1s)
            print(f"  Arts cumvar_top_1:               {arts_top1:.3f}")
            print(f"  Substrate cumvar_top_1 (avg):    {avg_substrate_top1:.3f}")
            print(f"  Min substrate cumvar_top_1:      {min(substrate_top1s):.3f}")
            print(f"  Max substrate cumvar_top_1:      {max(substrate_top1s):.3f}")
            print()
            if arts_top1 < min(substrate_top1s):
                print("  VERDICT: Arts has LOWER concentration than all substrate")
                print("    corpora — consistent with multi-coupled transmission")
                print("    function (no single dominant substrate axis).")
            elif arts_top1 > max(substrate_top1s):
                print("  VERDICT: Arts has HIGHER concentration than substrate")
                print("    corpora — suggests arts IS its own clean substrate")
                print("    (not transmission-distinct).")
            else:
                print("  VERDICT: Arts concentration is WITHIN substrate range —")
                print("    no clear distinction between transmission and substrate")
                print("    at this methodology.")

    out_path = Path(__file__).parent / "R-RBS-LM-94_arts_transmission_results.json"
    with open(out_path, "w") as f:
        json.dump({"corpora_results": results}, f, indent=2)
    print(f"\nResults saved: {out_path}")


if __name__ == "__main__":
    main()
