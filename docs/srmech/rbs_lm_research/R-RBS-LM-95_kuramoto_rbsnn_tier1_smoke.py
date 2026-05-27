"""R-RBS-LM-95 — Kuramoto coupled-oscillator RBS-NN Tier 1 simulation.

Per user direction 2026-05-27:
> "and yes we do want to begin the research kuramoto tests with our
> RBS-NN work"

Per Finding 119: two-tier architecture proposal — Tier 1 discrete-
cyclic (coupled-oscillator) + Tier 2 continuous-NN (synaptic).
Per Finding 121: biology compresses to 4:3:7; anchor + operations
inseparable in coupled-oscillator substrate.

This first Kuramoto smoke tests:
  1. Does the 4-unit operational core emerge above critical K_c?
  2. Does populating the oscillator ensemble with corpus data
     produce clustering that matches our synaptic-NN methodology?
  3. Is the same cascade-sequence observable across substrates?

Kuramoto dynamics:
  dθ_i/dt = ω_i + (1/N) Σ_j K_ij · sin(θ_j - θ_i)

Where:
  ω_i = natural frequency (derived from token frequency)
  K_ij = pairwise coupling strength (derived from cooccurrence)
  θ_i = phase of oscillator i

Order parameter:
  r(t) · e^(i·ψ(t)) = (1/N) Σ_j e^(i·θ_j)

If the same operator-cascade emerges as in R-RBS-LM-92 synaptic-NN
methodology → Tier 1 and Tier 2 substrates support the same
operations → two-tier architecture validated.

If different cascade emerges → substrate-bound; explicit
translation between Tier 1 and Tier 2 needed.

Smoke design:
  Part 1: small N=4 test — verify operational-core emerges at K_c
  Part 2: N=100 corpus-populated ensemble — compare clustering
          to Finding 113 natural clusters
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


def kuramoto_step(theta, omega, K_matrix, dt):
    """Single Euler step of Kuramoto dynamics.

    dθ_i/dt = ω_i + (1/N) Σ_j K_ij · sin(θ_j - θ_i)

    Vectorized: compute sin(θ_j - θ_i) for all pairs, weight by K,
    sum across j, divide by N, add ω_i, integrate.
    """
    N = len(theta)
    # phase_diff[i, j] = θ_j - θ_i
    phase_diff = theta[None, :] - theta[:, None]
    # weighted sin of phase differences
    sin_pd = np.sin(phase_diff)
    # interaction: sum over j of K_ij · sin(θ_j - θ_i)
    interaction = (K_matrix * sin_pd).sum(axis=1) / N
    dtheta_dt = omega + interaction
    return theta + dt * dtheta_dt


def order_parameter(theta):
    """Kuramoto order parameter r·e^(iψ) = (1/N) Σ e^(iθ)."""
    z = np.exp(1j * theta).mean()
    return float(np.abs(z)), float(np.angle(z))


def integrate_kuramoto(theta_init, omega, K_matrix, T=200.0, dt=0.05):
    """Integrate Kuramoto dynamics over time T with timestep dt.

    Returns:
      theta_history: shape (n_steps, N) phases over time
      r_history: shape (n_steps,) order parameter magnitude over time
    """
    n_steps = int(T / dt)
    N = len(theta_init)
    theta = theta_init.copy()
    theta_history = np.zeros((n_steps, N))
    r_history = np.zeros(n_steps)

    for k in range(n_steps):
        theta_history[k] = theta
        r, _ = order_parameter(theta)
        r_history[k] = r
        theta = kuramoto_step(theta, omega, K_matrix, dt)
        # Wrap phases to [-π, π]
        theta = np.angle(np.exp(1j * theta))

    return theta_history, r_history


def find_synchronized_clusters(theta_final, threshold=0.3):
    """Cluster oscillators by final phase similarity.

    Two oscillators are in the same cluster if |θ_i - θ_j| < threshold
    (in radians). Returns list of cluster index lists.
    """
    N = len(theta_final)
    # Pairwise phase differences (wrapped to [-π, π])
    diffs = np.abs(np.angle(
        np.exp(1j * (theta_final[None, :] - theta_final[:, None]))
    ))
    # Union-find for clusters
    parent = list(range(N))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    for i in range(N):
        for j in range(i + 1, N):
            if diffs[i, j] < threshold:
                union(i, j)

    clusters = {}
    for i in range(N):
        root = find(i)
        clusters.setdefault(root, []).append(i)
    return list(clusters.values())


# ===========================================================
# Part 1: Small N=4 test — operational core emergence
# ===========================================================

def part1_small_4_oscillator_test():
    print("=" * 78)
    print("PART 1: N=4 oscillator operational-core test")
    print("=" * 78)
    print()
    print("Test: does the 4-unit emerge as ONE synchronized cluster")
    print("      above critical K_c?")
    print()
    print("Setup: 4 oscillators, all-to-all coupling, slight ω spread")
    print()

    N = 4
    omega = np.array([0.95, 1.00, 1.05, 1.10])  # slight frequency spread
    theta_init = np.random.RandomState(42).uniform(-np.pi, np.pi, N)

    print(f"  natural frequencies omega = {omega}")
    print(f"  random initial phases theta_init = {theta_init}")
    print()
    print(f"  Sweeping K from 0 to 2.0 in 11 steps...")
    print(f"  Each run: T=100, dt=0.05")
    print()
    print(f"  {'K':<6} {'final r':<10} {'is sync (r > 0.95)':<22} "
          f"{'cluster count'}")
    print("  " + "-" * 70)

    K_values = np.linspace(0.0, 2.0, 11)
    results = []
    for K_global in K_values:
        K_matrix = np.full((N, N), K_global)
        np.fill_diagonal(K_matrix, 0.0)  # no self-coupling
        _, r_history = integrate_kuramoto(
            theta_init, omega, K_matrix, T=100.0, dt=0.05
        )
        # Final r (last 10% of timesteps, averaged)
        final_r = float(np.mean(r_history[-200:]))
        is_sync = final_r > 0.95
        # Get final theta to find clusters
        theta_history, _ = integrate_kuramoto(
            theta_init, omega, K_matrix, T=100.0, dt=0.05
        )
        clusters = find_synchronized_clusters(theta_history[-1])
        n_clusters = len(clusters)
        results.append({
            "K": float(K_global),
            "final_r": final_r,
            "is_sync": is_sync,
            "n_clusters": n_clusters,
        })
        print(f"  {K_global:<6.2f} {final_r:<10.4f} "
              f"{'YES' if is_sync else 'no':<22} {n_clusters}")

    # Find K_c (smallest K where final_r > 0.95)
    K_c = None
    for r in results:
        if r["is_sync"]:
            K_c = r["K"]
            break

    print()
    if K_c is not None:
        print(f"  VERDICT: K_c ≈ {K_c:.2f} (smallest K with full sync)")
        print(f"  Above K_c, all 4 oscillators synchronize into ONE")
        print(f"  cluster — the operational core emerges.")
    else:
        print("  VERDICT: no synchronization in K range — try higher K")

    return results, K_c


# ===========================================================
# Part 2: Corpus-populated N=100 ensemble
# ===========================================================

def part2_corpus_populated_ensemble(corpus_path, vocab_size=100,
                                     K_global=2.0):
    print()
    print("=" * 78)
    print(f"PART 2: N={vocab_size} corpus-populated ensemble")
    print(f"  corpus: {corpus_path}")
    print(f"  K_global = {K_global}")
    print("=" * 78)
    print()

    tokens = load_corpus(corpus_path)
    print(f"  tokens loaded: {len(tokens):,}")

    counts = Counter(tokens)
    vocab = [tok for tok, _ in counts.most_common(vocab_size)]
    print(f"  vocab top-{vocab_size}: {vocab[:10]} ...")

    W = build_cooccurrence(tokens, vocab, window=5)
    # Normalize W to [0, K_global]
    W_max = W.max()
    if W_max == 0:
        print("  ERROR: zero cooccurrence")
        return None
    K_matrix = K_global * W / W_max
    np.fill_diagonal(K_matrix, 0.0)
    print(f"  K_matrix: shape={K_matrix.shape}, "
          f"mean={K_matrix.mean():.3f}, "
          f"max={K_matrix.max():.3f}")

    # Natural frequencies: log-uniformly spaced based on token frequency
    # rank. High-freq tokens get LOW natural freq (slower, more
    # foundational); low-freq tokens get HIGH natural freq (faster,
    # more peripheral).
    rank = np.arange(vocab_size, dtype=np.float64)
    omega = 1.0 + 0.5 * (rank / vocab_size)
    print(f"  omega range: [{omega[0]:.3f}, {omega[-1]:.3f}]")

    # Random initial phases
    rng = np.random.RandomState(2026)
    theta_init = rng.uniform(-np.pi, np.pi, vocab_size)

    # Integrate
    T = 200.0
    dt = 0.05
    print(f"  integrating Kuramoto for T={T}, dt={dt}...")
    theta_history, r_history = integrate_kuramoto(
        theta_init, omega, K_matrix, T, dt
    )
    final_r = float(np.mean(r_history[-200:]))
    print(f"  final order parameter r = {final_r:.4f}")
    print(f"  initial order parameter r = {r_history[0]:.4f}")

    # Find clusters at end of simulation
    clusters = find_synchronized_clusters(theta_history[-1], threshold=0.5)
    clusters_by_size = sorted(clusters, key=len, reverse=True)
    print()
    print(f"  {len(clusters)} synchronized clusters at simulation end:")
    print(f"  (showing top-10 by size)")
    for c_idx, cluster_indices in enumerate(clusters_by_size[:10]):
        tokens_in_cluster = [vocab[i] for i in cluster_indices]
        size = len(tokens_in_cluster)
        # Show up to 8 tokens
        token_str = ", ".join(tokens_in_cluster[:8])
        if size > 8:
            token_str += f", ... ({size} total)"
        print(f"    cluster {c_idx} (size={size}): {token_str}")

    return {
        "corpus_path": corpus_path,
        "vocab_size": vocab_size,
        "K_global": K_global,
        "final_r": final_r,
        "initial_r": float(r_history[0]),
        "n_clusters": len(clusters),
        "cluster_sizes": [len(c) for c in clusters_by_size],
        "top_clusters": [
            {"size": len(c), "tokens": [vocab[i] for i in c[:20]]}
            for c in clusters_by_size[:10]
        ],
    }


def main():
    print("=" * 78)
    print("R-RBS-LM-95 — Kuramoto RBS-NN Tier 1 simulation")
    print("=" * 78)

    # Part 1: small N=4 test
    part1_results, K_c = part1_small_4_oscillator_test()

    # Part 2: corpus-populated N=100 ensemble
    part2_result = part2_corpus_populated_ensemble(
        "/tmp/mcguffey_sixth.txt",
        vocab_size=100,
        K_global=2.0,
    )

    print()
    print("=" * 78)
    print("CROSS-PART OBSERVATIONS")
    print("=" * 78)
    print()
    if K_c is not None:
        print(f"  Part 1: 4-oscillator operational core emerges at K_c≈{K_c:.2f}")
    if part2_result:
        print(f"  Part 2: N=100 corpus-populated ensemble")
        print(f"    K_global=2.0, final_r={part2_result['final_r']:.3f}")
        print(f"    {part2_result['n_clusters']} synchronized clusters")
        cs = part2_result['cluster_sizes']
        print(f"    cluster sizes (top): {cs[:10]}")
        # Check 1+3 emergence
        if len(cs) >= 4:
            print(f"    Cluster cardinality 1+1+1+1 / 1+3 / 1+1+2 read: "
                  f"{cs[0]}+{cs[1]}+{cs[2]}+{cs[3]}+...")

    out_path = Path(__file__).parent / "R-RBS-LM-95_kuramoto_results.json"
    with open(out_path, "w") as f:
        json.dump({
            "part1_4_oscillator": part1_results,
            "K_c_estimate": K_c,
            "part2_corpus_populated": part2_result,
        }, f, indent=2)
    print(f"\nResults saved: {out_path}")


if __name__ == "__main__":
    main()
