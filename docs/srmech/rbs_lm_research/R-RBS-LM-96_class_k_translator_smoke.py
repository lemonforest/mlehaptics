"""R-RBS-LM-96 — Test Class K (pin-slot/Kepler) as explicit Tier 1 → Tier 2 translator.

Per Finding 122 open question + user direction 2026-05-27:
> "don't forget to also do testing Class K as the explicit translator
> if we didn't"

Finding 122 showed Kuramoto coherence (Tier 1) vs PPMI similarity
(Tier 2) have Spearman correlation -0.004 — substrates detect
different structure.

Finding 120 said Class K (Kepler-shape / pin-slot) is the bridge.
Finding 124 said Hopf twist is the topological form of Class K.

The test: take Kuramoto coherence matrix, apply pin_slot transform
with varying eccentricity, check if at some eccentricity the
transformed matrix approaches PPMI similarity in rank-order.

Pin-slot transform per srmech.amsc.kepler:
  pin_slot(θ, ε) = atan2(ε·sin(θ), 1 + ε·cos(θ))

Interpreting:
  θ = phase angle (from Kuramoto coherence Tier 1 reading)
  ε = eccentricity (varies; 0 = identity, larger = more lift)
  Output = projected phase = candidate Tier 2 reading

We need to map between (i, j) pairs and a θ angle. Strategy:
  Treat Kuramoto coherence[i, j] as |z| of a complex number
  z = coherence_ij · e^(i·phase_ij). Then the "θ" is the phase
  of pair (i, j). Apply pin_slot to get transformed phase, then
  re-extract magnitude.

Simpler approach: treat coherence value directly as the input to
a non-linear transform parameterized by eccentricity, mimicking
the Kepler equation-of-centre Fourier expansion:

  transformed(c) = c + Σ_{k=1}^{n} a_k · e^k · sin(k · acos(c))

where a_k are the equation-of-centre coefficients (from srmech).

This applies the Class K eccentricity-dependent transform to each
coherence value, treating coherence as cos(M) of a mean anomaly.

Then test: does the transformed coherence correlate better with PPMI
than raw coherence does?
"""

import json
import re
from collections import Counter
from pathlib import Path

import numpy as np


TOKEN_RE = re.compile(r"[a-zà-ùA-ZÀ-Ù]+")


# Equation-of-centre Fourier coefficients from srmech.amsc.kepler
EOC_COEFFS = (
    2.0,            # k=1: 2 e             sin(M)
    5.0 / 4.0,      # k=2: (5/4) e^2       sin(2M)
    13.0 / 12.0,    # k=3: (13/12) e^3     sin(3M)
    103.0 / 96.0,   # k=4: (103/96) e^4    sin(4M)
    1097.0 / 960.0, # k=5: (1097/960) e^5  sin(5M)
    1223.0 / 960.0, # k=6: (1223/960) e^6  sin(6M)
)


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
    norms = np.linalg.norm(M, axis=1, keepdims=True)
    norms = np.where(norms > 0, norms, 1.0)
    M_norm = M / norms
    return M_norm @ M_norm.T


def kuramoto_step(theta, omega, K_matrix, dt):
    phase_diff = theta[None, :] - theta[:, None]
    interaction = (K_matrix * np.sin(phase_diff)).sum(axis=1) / len(theta)
    return theta + dt * (omega + interaction)


def integrate_kuramoto_and_record_coherence(
    theta_init, omega, K_matrix, T=150.0, dt=0.05,
    coherence_window_frac=0.25
):
    n_steps = int(T / dt)
    coherence_start = int(n_steps * (1 - coherence_window_frac))
    theta = theta_init.copy()
    N = len(theta)
    coherence_accum = np.zeros((N, N), dtype=np.complex128)
    n_recorded = 0
    for k in range(n_steps):
        theta = kuramoto_step(theta, omega, K_matrix, dt)
        theta = np.angle(np.exp(1j * theta))
        if k >= coherence_start:
            phase_diff = theta[:, None] - theta[None, :]
            coherence_accum += np.exp(1j * phase_diff)
            n_recorded += 1
    return np.abs(coherence_accum / n_recorded)


def class_k_eoc_transform(coherence_matrix, eccentricity, n_terms=6):
    """Apply Class K equation-of-centre eccentricity-dependent transform.

    Treat each coherence value c ∈ [0, 1] as cos(M) of a mean anomaly M.
    Then M = acos(c). Apply the Kepler equation-of-centre lift:

      ν - M = Σ_{k=1}^{n} a_k · e^k · sin(k·M)

    The transformed value is then cos(ν) = cos(M + (ν-M)).
    Effectively applies the Class K lift to the coherence-as-cosine-of-angle.

    eccentricity e ∈ [0, 1) parameterizes the lift cost. e=0 returns
    the input unchanged.
    """
    e = float(eccentricity)
    if e == 0.0:
        return coherence_matrix.copy()
    # Treat coherence as cos(M) where M is mean anomaly
    c = np.clip(coherence_matrix, -1.0, 1.0)
    M = np.arccos(c)
    # Compute equation of centre series
    eoc = np.zeros_like(M)
    for k in range(min(n_terms, len(EOC_COEFFS))):
        coeff = EOC_COEFFS[k]
        eoc += coeff * (e ** (k + 1)) * np.sin((k + 1) * M)
    # True anomaly ν = M + (ν - M)
    nu = M + eoc
    # Re-extract magnitude as cos(ν)
    return np.cos(nu)


def spearman_corr(x, y):
    """Spearman rank correlation."""
    rx = np.argsort(np.argsort(x))
    ry = np.argsort(np.argsort(y))
    if rx.std() > 0 and ry.std() > 0:
        return float(np.corrcoef(rx, ry)[0, 1])
    return 0.0


def pair_vector(matrix):
    """Return flat array of upper-triangle off-diagonal entries."""
    N = matrix.shape[0]
    vals = []
    for i in range(N):
        for j in range(i + 1, N):
            vals.append(matrix[i, j])
    return np.array(vals)


def main():
    print("=" * 78)
    print("R-RBS-LM-96 — Class K explicit translator test")
    print("=" * 78)
    print()

    corpus_path = "/tmp/mcguffey_sixth.txt"
    vocab_size = 80
    K_global = 8.0
    T = 150.0

    print(f"  setup matches R-RBS-LM-95b:")
    print(f"    corpus: {corpus_path}")
    print(f"    vocab: top-{vocab_size}, K_global: {K_global}, T: {T}")
    print()

    # Load + build cooccurrence + PPMI
    tokens = load_corpus(corpus_path)
    counts = Counter(tokens)
    vocab = [tok for tok, _ in counts.most_common(vocab_size)]
    W = build_cooccurrence(tokens, vocab, window=5)
    W_ppmi = ppmi_weight(W)
    ppmi_sim = cosine_similarity_matrix(W_ppmi)
    np.fill_diagonal(ppmi_sim, 0.0)

    # Build Kuramoto coupling and integrate
    K_matrix = K_global * W / max(W.max(), 1.0)
    np.fill_diagonal(K_matrix, 0.0)
    rank = np.arange(vocab_size, dtype=np.float64)
    omega = 1.0 + 0.2 * (rank / vocab_size)
    rng = np.random.RandomState(2026)
    theta_init = rng.uniform(-np.pi, np.pi, vocab_size)

    print(f"  integrating Kuramoto...")
    coherence_matrix = integrate_kuramoto_and_record_coherence(
        theta_init, omega, K_matrix, T
    )
    np.fill_diagonal(coherence_matrix, 0.0)
    print(f"  coherence_matrix: mean={coherence_matrix.mean():.3f}, "
          f"max={coherence_matrix.max():.3f}")
    print()

    # Baseline: raw coherence vs PPMI (from R-RBS-LM-95b)
    coh_pairs = pair_vector(coherence_matrix)
    ppmi_pairs = pair_vector(ppmi_sim)
    baseline_spearman = spearman_corr(coh_pairs, ppmi_pairs)
    print(f"  Baseline (raw Kuramoto vs PPMI):")
    print(f"    Spearman corr: {baseline_spearman:+.4f}")
    print()

    # Sweep eccentricity
    print(f"  Sweeping eccentricity e from 0.0 to 0.99...")
    print(f"  Looking for e* where transformed-coherence -> PPMI rank")
    print()
    print(f"  {'e':<8} {'Spearman vs PPMI':<22} {'change vs baseline'}")
    print("  " + "-" * 60)

    e_values = np.array([
        0.0, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99
    ])

    results = []
    best_e = 0.0
    best_spearman = baseline_spearman
    for e in e_values:
        transformed = class_k_eoc_transform(coherence_matrix, e)
        np.fill_diagonal(transformed, 0.0)
        trans_pairs = pair_vector(transformed)
        sp = spearman_corr(trans_pairs, ppmi_pairs)
        change = sp - baseline_spearman
        results.append({
            "eccentricity": float(e),
            "spearman_vs_ppmi": float(sp),
            "change_vs_baseline": float(change),
        })
        marker = ""
        if abs(sp) > abs(best_spearman):
            best_spearman = sp
            best_e = e
            marker = " ← best so far"
        print(f"  {e:<8.2f} {sp:<+22.4f} {change:+.4f}{marker}")

    print()
    print("=" * 78)
    print("VERDICT")
    print("=" * 78)
    print()
    print(f"  Baseline Spearman (raw):     {baseline_spearman:+.4f}")
    print(f"  Best Spearman after Class K: {best_spearman:+.4f}  at e={best_e:.2f}")
    print(f"  Improvement:                  {best_spearman - baseline_spearman:+.4f}")
    print()

    abs_improvement = abs(best_spearman) - abs(baseline_spearman)
    if abs_improvement > 0.15:
        print(f"  STRONG: Class K with eccentricity {best_e:.2f} substantively")
        print(f"  translates Tier 1 toward Tier 2. The translator hypothesis")
        print(f"  is supported.")
    elif abs_improvement > 0.05:
        print(f"  MODERATE: Class K provides some translation work. The")
        print(f"  bridge is doing something but not enough to fully bridge")
        print(f"  the substrates.")
    else:
        print(f"  WEAK/NULL: Class K equation-of-centre transform doesn't")
        print(f"  meaningfully translate Kuramoto coherence to PPMI rank.")
        print(f"  Either the wrong Class K operation is being tried, OR the")
        print(f"  substrates need richer translation than scalar lift.")

    print()

    # Save
    out_path = (Path(__file__).parent
                / "R-RBS-LM-96_class_k_translator_results.json")
    with open(out_path, "w") as f:
        json.dump({
            "baseline_spearman": baseline_spearman,
            "best_eccentricity": float(best_e),
            "best_spearman": float(best_spearman),
            "improvement": float(best_spearman - baseline_spearman),
            "sweep_results": results,
        }, f, indent=2)
    print(f"  Results saved: {out_path}")


if __name__ == "__main__":
    main()
