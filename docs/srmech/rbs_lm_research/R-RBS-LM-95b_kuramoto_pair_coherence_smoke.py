"""R-RBS-LM-95b — Kuramoto per-pair phase coherence vs synaptic-NN similarity.

Per R-RBS-LM-95 first iteration: corpus-populated Kuramoto ensemble has
heterogeneous coupling that doesn't drive GLOBAL synchronization. The
right metric is PER-PAIR phase coherence after equilibration.

This iteration computes:
  (a) Kuramoto-substrate metric: pairwise phase coherence
      coherence_ij = |<e^(i(θ_i - θ_j))>| averaged over last 25% of time
  (b) Synaptic-NN-substrate metric: PPMI cosine similarity (from
      R-RBS-LM-92 methodology)

Then compares: are the SAME pairs ranked highest in both metrics?

If yes → Kuramoto Tier 1 produces same cascade-structure as synaptic-NN
       Tier 2; two-tier architecture's "same cascade across substrates"
       hypothesis confirmed
If no → substrates produce DIFFERENT cascades; substrate-bound

This is the deciding test for Finding 119's architecture proposal.
"""

import json
import re
from collections import Counter
from pathlib import Path

import numpy as np


TOKEN_RE = re.compile(r"[a-zà-ùA-ZÀ-Ù]+")


def tokenize(text):
    return TOKEN_RE.findall(text.lower())


def load_corpus(path):
    with open(path, encoding="utf-8", errors="ignore") as f:
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


def cosine_similarity_matrix(M):
    """Pairwise cosine similarity between rows of M."""
    norms = np.linalg.norm(M, axis=1, keepdims=True)
    norms = np.where(norms > 0, norms, 1.0)
    M_norm = M / norms
    return M_norm @ M_norm.T


def kuramoto_step(theta, omega, K_matrix, dt):
    phase_diff = theta[None, :] - theta[:, None]
    interaction = (K_matrix * np.sin(phase_diff)).sum(axis=1) / len(theta)
    return theta + dt * (omega + interaction)


def integrate_and_record_coherence(theta_init, omega, K_matrix,
                                    T=200.0, dt=0.05,
                                    coherence_window_frac=0.25):
    """Integrate Kuramoto and record pairwise phase coherence over
    last `coherence_window_frac` of timesteps.

    Pairwise phase coherence:
      coherence_ij = |<e^(i(θ_i - θ_j))>|_t
    where the average is over the last fraction of timesteps.

    Returns:
      coherence_matrix: N x N pairwise phase coherence
      final_r: final order parameter
    """
    n_steps = int(T / dt)
    coherence_start = int(n_steps * (1 - coherence_window_frac))

    theta = theta_init.copy()
    N = len(theta)

    # Accumulate e^(i(θ_i - θ_j)) over the coherence window
    coherence_accum = np.zeros((N, N), dtype=np.complex128)
    n_recorded = 0

    for k in range(n_steps):
        theta = kuramoto_step(theta, omega, K_matrix, dt)
        theta = np.angle(np.exp(1j * theta))
        if k >= coherence_start:
            # phase_diff[i, j] = θ_i - θ_j
            phase_diff = theta[:, None] - theta[None, :]
            coherence_accum += np.exp(1j * phase_diff)
            n_recorded += 1

    coherence_matrix = np.abs(coherence_accum / n_recorded)
    z = np.exp(1j * theta).mean()
    final_r = float(np.abs(z))
    return coherence_matrix, final_r


def main():
    print("=" * 78)
    print("R-RBS-LM-95b — Kuramoto per-pair coherence vs synaptic-NN")
    print("=" * 78)
    print()

    corpus_path = "/tmp/mcguffey_sixth.txt"
    vocab_size = 80  # smaller for compute speed
    K_global = 8.0   # higher to overcome heterogeneity
    T = 150.0
    dt = 0.05

    tokens = load_corpus(corpus_path)
    counts = Counter(tokens)
    vocab = [tok for tok, _ in counts.most_common(vocab_size)]
    print(f"  corpus: {corpus_path}")
    print(f"  tokens: {len(tokens):,}, vocab: top-{vocab_size}")
    print(f"  K_global: {K_global}, T: {T}, dt: {dt}")
    print()

    # Build cooccurrence and PPMI
    W = build_cooccurrence(tokens, vocab, window=5)
    W_ppmi = ppmi_weight(W)
    ppmi_sim = cosine_similarity_matrix(W_ppmi)
    np.fill_diagonal(ppmi_sim, 0.0)
    print(f"  PPMI cosine similarity computed (synaptic-NN substrate metric)")

    # Kuramoto coupling from cooccurrence
    K_matrix = K_global * W / max(W.max(), 1.0)
    np.fill_diagonal(K_matrix, 0.0)
    print(f"  K_matrix: mean={K_matrix.mean():.3f}, max={K_matrix.max():.3f}")

    # Natural frequencies: rank-based
    rank = np.arange(vocab_size, dtype=np.float64)
    omega = 1.0 + 0.2 * (rank / vocab_size)  # narrow spread
    print(f"  omega range: [{omega[0]:.3f}, {omega[-1]:.3f}]")
    print()

    # Integrate
    rng = np.random.RandomState(2026)
    theta_init = rng.uniform(-np.pi, np.pi, vocab_size)
    print(f"  integrating Kuramoto and recording pairwise coherence...")
    coherence_matrix, final_r = integrate_and_record_coherence(
        theta_init, omega, K_matrix, T, dt
    )
    np.fill_diagonal(coherence_matrix, 0.0)
    print(f"  final r = {final_r:.4f}")
    print(f"  coherence_matrix: mean={coherence_matrix.mean():.3f}, "
          f"max={coherence_matrix.max():.3f}")
    print()

    # === The deciding comparison ===========================
    # Get top-K pair rankings from each metric and compare

    def top_pairs(matrix, k=20):
        """Return list of (i, j, value) for top-k off-diagonal pairs
        (i < j)."""
        pairs = []
        N = matrix.shape[0]
        for i in range(N):
            for j in range(i + 1, N):
                pairs.append((i, j, float(matrix[i, j])))
        pairs.sort(key=lambda x: -x[2])
        return pairs[:k]

    top_coherence = top_pairs(coherence_matrix, k=30)
    top_ppmi = top_pairs(ppmi_sim, k=30)

    coherence_pair_set = set((i, j) for i, j, _ in top_coherence)
    ppmi_pair_set = set((i, j) for i, j, _ in top_ppmi)
    overlap = coherence_pair_set & ppmi_pair_set
    print(f"  TOP-30 PAIR OVERLAP:")
    print(f"    Coherence top-30: {len(coherence_pair_set)} pairs")
    print(f"    PPMI top-30:      {len(ppmi_pair_set)} pairs")
    print(f"    Intersection:     {len(overlap)} pairs")
    print(f"    Overlap fraction: {len(overlap)/30:.2%}")
    print()

    print(f"  Top-10 KURAMOTO COHERENCE pairs:")
    for i, j, v in top_coherence[:10]:
        marker = " ✓" if (i, j) in ppmi_pair_set else ""
        print(f"    ({vocab[i]:<8}, {vocab[j]:<8})  coherence={v:.3f}{marker}")
    print()

    print(f"  Top-10 PPMI SIMILARITY pairs:")
    for i, j, v in top_ppmi[:10]:
        marker = " ✓" if (i, j) in coherence_pair_set else ""
        print(f"    ({vocab[i]:<8}, {vocab[j]:<8})  ppmi_sim={v:.3f}{marker}")
    print()

    # Spearman-like rank correlation between coherence and PPMI for all pairs
    all_coh = []
    all_ppmi = []
    for i in range(vocab_size):
        for j in range(i + 1, vocab_size):
            all_coh.append(coherence_matrix[i, j])
            all_ppmi.append(ppmi_sim[i, j])
    all_coh = np.array(all_coh)
    all_ppmi = np.array(all_ppmi)

    # Pearson on raw values
    if all_coh.std() > 0 and all_ppmi.std() > 0:
        pearson = float(np.corrcoef(all_coh, all_ppmi)[0, 1])
    else:
        pearson = 0.0

    # Spearman: rank both then Pearson
    coh_rank = np.argsort(np.argsort(all_coh))
    ppmi_rank = np.argsort(np.argsort(all_ppmi))
    if coh_rank.std() > 0 and ppmi_rank.std() > 0:
        spearman = float(np.corrcoef(coh_rank, ppmi_rank)[0, 1])
    else:
        spearman = 0.0

    print(f"  Pairwise metric correlation:")
    print(f"    Pearson  (raw values): {pearson:+.4f}")
    print(f"    Spearman (rank order): {spearman:+.4f}")
    print()

    print("=" * 78)
    print("VERDICT")
    print("=" * 78)
    print()

    if spearman > 0.50:
        print(f"  STRONG: Kuramoto coherence and PPMI similarity rank pairs")
        print(f"  similarly (Spearman {spearman:+.3f}). Tier 1 and Tier 2")
        print(f"  substrates produce the SAME cascade-structure.")
        print(f"  Architecture proposal Finding 119 validated.")
    elif spearman > 0.20:
        print(f"  PARTIAL: Kuramoto and PPMI agree above noise (Spearman")
        print(f"  {spearman:+.3f}). Substrates are correlated but not")
        print(f"  identical — some translation needed.")
    else:
        print(f"  WEAK/NULL: Substrates produce different cascades (Spearman")
        print(f"  {spearman:+.3f}). Two-tier architecture needs explicit")
        print(f"  substrate-translation, not direct lifting.")

    print()

    out_path = Path(__file__).parent / "R-RBS-LM-95b_pair_coherence_results.json"
    with open(out_path, "w") as f:
        json.dump({
            "corpus": corpus_path,
            "vocab_size": vocab_size,
            "K_global": K_global,
            "T": T, "dt": dt,
            "final_r": final_r,
            "top_30_coherence_pairs": [
                {"tok1": vocab[i], "tok2": vocab[j], "value": v}
                for i, j, v in top_coherence
            ],
            "top_30_ppmi_pairs": [
                {"tok1": vocab[i], "tok2": vocab[j], "value": v}
                for i, j, v in top_ppmi
            ],
            "top_30_overlap_count": len(overlap),
            "top_30_overlap_fraction": len(overlap) / 30,
            "pearson_corr": pearson,
            "spearman_corr": spearman,
        }, f, indent=2)
    print(f"Results saved: {out_path}")


if __name__ == "__main__":
    main()
