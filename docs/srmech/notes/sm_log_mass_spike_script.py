"""
SM log-mass eigenvalue spike (2026-05-12).

RESEARCH SPIKE #5 — MFO-natural reframing of §XIII.1.

KEY REFRAMING (per user): MFO's "field is fundamental, spatial emerges"
ontology makes log(m²/m_ref²) — not m or m² — the natural variable for
SM masses. Mass is a property of the emergent localization spectrum;
the field substrate's natural scale variable is logarithmic (path integral
action, RG flow). The previous spikes (#1-4) operated in linear-mass
space, which is a category error under MFO.

In log-m² space, SM charged-fermion eigenvalues normalized to electron:
  e=0, u=2.88, d=4.43, s=10.42, μ=10.66, c=15.65, τ=16.31, b=18.05, t=25.46

This range [0, 25.5] is BOUNDED — fractal eigenvalue spectra naturally
fit here.

STRUCTURAL FEATURES (the things any candidate must reproduce, not just
fit numerically):

  Feature 1: 3-cluster structure
     Cluster L = {e, u, d, s, μ}  in [0, ~10.7]
     Cluster M = {c, τ}            in [15.7, 16.3]
     Cluster H = {b, t}             in [18.1, 25.5]

  Feature 2: Near-degeneracies (split-doublets)
     (s, μ): gap 0.24
     (c, τ): gap 0.66

  Feature 3: Bounded total span ~25.5

  Feature 4: Multiplicity count 18 = 3 generations × 6 fermion-types
     (matches D₃ irrep block count from MFO MPM finding)

A random scatter of 9 values in [0, 25.5] has vanishing probability of
reproducing all four features. So we run a null test against features 1+2
to set the bar.

Then we look at candidate F × G/H spectra and check which reproduces
these features. Standard sphere candidates and fractal × sphere products.

Reproduce: `python -X utf8 docs/srmech/notes/sm_log_mass_spike_script.py`
"""

import json
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import scipy.sparse as sp
import scipy.linalg

RNG_SEED = 20260512
OUT_DIR = Path(__file__).parent
RESULTS_FILE = OUT_DIR / "sm-log-mass-spike-per-test-2026-05-12.ndjson"

# ── SM input (log-m² normalized to electron) ────────────────────────────

SM_MASSES_MEV = {
    "e": 0.511,  "u": 2.16,    "d": 4.67,
    "s": 93.4,   "μ": 105.66,
    "c": 1270.0, "τ": 1776.86,
    "b": 4180.0, "t": 172760.0,
}

def sm_log_m_sq_values():
    """ln(m²/m_e²) for 9 charged fermions, sorted ascending."""
    m_e = SM_MASSES_MEV["e"]
    return sorted([(name, 2 * np.log(m / m_e)) for name, m in SM_MASSES_MEV.items()],
                   key=lambda x: x[1])


# ── Structural feature extractors ───────────────────────────────────────

def detect_clusters(values, gap_threshold_factor=2.5):
    """
    Detect clusters as runs of consecutive values where each gap to the next
    is < gap_threshold_factor × median(gaps within the cluster so far).
    Simpler proxy: gap > threshold (1.5) → cluster boundary.
    """
    if len(values) < 2:
        return [list(values)]
    gaps = np.diff(values)
    median_gap = np.median(gaps)
    boundary_threshold = max(2.5 * median_gap, 1.5)
    clusters = [[values[0]]]
    for i in range(1, len(values)):
        if gaps[i - 1] > boundary_threshold:
            clusters.append([values[i]])
        else:
            clusters[-1].append(values[i])
    return clusters


def count_near_degeneracies(values, threshold=1.0):
    """Pairs (i, j) with |v_i - v_j| < threshold (excluding identical indices)."""
    n = len(values)
    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            if abs(values[i] - values[j]) < threshold:
                pairs.append((i, j, abs(values[i] - values[j])))
    return pairs


def structural_signature(values):
    """Compact signature: (n_clusters, near_deg_count, total_span)."""
    values = sorted(values)
    clusters = detect_clusters(values)
    pairs = count_near_degeneracies(values, threshold=1.0)
    span = values[-1] - values[0]
    return {
        "n_clusters": len(clusters),
        "cluster_sizes": [len(c) for c in clusters],
        "near_deg_pairs": len(pairs),
        "span": float(span),
    }


# ── Candidate spectra in [0, 25.5] log-m² range ─────────────────────────

def s2_spectrum_first_n(l_max, n):
    eigs, mults = [], []
    for l in range(l_max + 1):
        eigs.extend([l * (l + 1)] * (2 * l + 1))
    return sorted(eigs)[:n]


def s3_spectrum_first_n(l_max, n):
    eigs = []
    for l in range(l_max + 1):
        eigs.extend([l * (l + 2)] * ((l + 1) ** 2))
    return sorted(eigs)[:n]


def cp2_spectrum_first_n(l_max, n):
    eigs = []
    for l in range(l_max + 1):
        eigs.extend([4 * l * (l + 2) / 3] * ((l + 1) * (l + 2) // 2))
    return sorted(eigs)[:n]


def build_sg_laplacian(level):
    coords = [(0.0, 0.0), (1.0, 0.0), (0.5, np.sqrt(3) / 2)]
    triangles = [(0, 1, 2)]
    for _ in range(level - 1):
        nc = list(coords)
        nt = []
        mc = {}
        for tri in triangles:
            a, b, c = tri
            def mid(i, j):
                k = (min(i, j), max(i, j))
                if k not in mc:
                    mc[k] = len(nc)
                    nc.append(((coords[i][0] + coords[j][0]) / 2,
                                (coords[i][1] + coords[j][1]) / 2))
                return mc[k]
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            nt.extend([(a, ab, ca), (b, ab, bc), (c, bc, ca)])
        coords, triangles = nc, nt
    edges = set()
    for a, b, c in triangles:
        for i, j in [(a, b), (b, c), (c, a)]:
            edges.add((min(i, j), max(i, j)))
    n = len(coords)
    rows, cols = [], []
    for i, j in edges:
        rows += [i, j]; cols += [j, i]
    A = sp.coo_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n)).tocsr()
    deg = np.asarray(A.sum(axis=1)).ravel()
    return (sp.diags(deg) - A).toarray()


def sg_eigvals(level, n):
    L = build_sg_laplacian(level)
    eigs = np.sort(scipy.linalg.eigvalsh(L))[:n + 5]  # extra for non-zero filter
    return eigs


def product_spectrum_first_n(eigs_a, eigs_b, n):
    """Cartesian product (eigenvalue sums) first n."""
    sums = sorted(float(a + b) for a in eigs_a for b in eigs_b)
    return sums[:n]


# ── Fit and score ──────────────────────────────────────────────────────

def fit_to_sm(candidate_eigs_first_9, sm_values):
    """
    Linear regression: SM_log_m² = a × eig + b.
    Returns (a, b, R², per-particle residuals).
    """
    if len(candidate_eigs_first_9) != len(sm_values):
        return None
    x = np.array(candidate_eigs_first_9)
    y = np.array(sm_values)
    a, b = np.polyfit(x, y, 1)
    pred = a * x + b
    ss_res = np.sum((y - pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    return {"a": float(a), "b": float(b), "r2": float(r2),
            "residuals": [float(r) for r in y - pred],
            "predicted": [float(p) for p in pred]}


# ── Null test ───────────────────────────────────────────────────────────

def null_structural_match(rng, sm_span, n_trials=5000):
    """
    Random 9 values in [0, sm_span]; how often do they reproduce
    SM's structural signature (3 clusters, ≥2 near-deg pairs)?
    """
    sm_sig_target = {"n_clusters": 3, "near_deg_pairs": 2}
    matches = 0
    for _ in range(n_trials):
        random_values = np.sort(rng.uniform(0, sm_span, 9))
        sig = structural_signature(random_values)
        if (sig["n_clusters"] == sm_sig_target["n_clusters"]
                and sig["near_deg_pairs"] >= sm_sig_target["near_deg_pairs"]):
            matches += 1
    return matches / n_trials


# ── Main ────────────────────────────────────────────────────────────────

def main():
    rng = np.random.default_rng(RNG_SEED)
    records = []

    print("=== SM log-mass² eigenvalue spike (MFO-natural variable) ===\n")

    sm_log_m_sq = sm_log_m_sq_values()
    sm_values = [v for _, v in sm_log_m_sq]
    sm_names = [n for n, _ in sm_log_m_sq]

    print("SM input (log m²/m_e², sorted):")
    for n, v in sm_log_m_sq:
        print(f"  {n:>3s} : {v:7.3f}")
    print()

    # Structural signature of SM
    sm_sig = structural_signature(sm_values)
    sm_clusters = detect_clusters(sm_values)
    sm_pairs = count_near_degeneracies(sm_values, threshold=1.0)
    print(f"Structural signature of SM log m²:")
    print(f"  Clusters ({sm_sig['n_clusters']}): "
          f"{[[f'{v:.2f}' for v in c] for c in sm_clusters]}")
    print(f"  Near-degeneracies (gap < 1.0): {len(sm_pairs)}")
    for i, j, g in sm_pairs:
        print(f"     ({sm_names[i]}, {sm_names[j]}): gap = {g:.3f}")
    print(f"  Total span: {sm_sig['span']:.3f}")
    print()
    records.append({"test": "sm_structural_signature",
                     "values": sm_values, "names": sm_names,
                     "clusters": [[float(v) for v in c] for c in sm_clusters],
                     "near_deg_pairs": [(sm_names[i], sm_names[j], float(g))
                                          for i, j, g in sm_pairs],
                     "span": float(sm_sig["span"])})

    # Null test
    print("=== Null test: random 9 values in [0, 25.5] ===\n")
    null_match_rate = null_structural_match(rng, sm_sig["span"], n_trials=5000)
    print(f"  Probability of (3 clusters AND ≥2 near-deg pairs) under uniform null: "
          f"{100 * null_match_rate:.2f}%")
    print(f"  This is the bar a candidate must beat to provide real structural signal\n")
    records.append({"test": "null_structural_match_rate",
                      "rate_pct": float(100 * null_match_rate)})

    # Candidates: spectra in log-m² range
    print("=== Candidate spectra (first 9 non-zero eigenvalues) ===\n")
    candidates = {}

    # Single homogeneous spaces
    candidates["S²_first9"] = s2_spectrum_first_n(8, 9)
    candidates["S³_first9"] = s3_spectrum_first_n(6, 9)
    candidates["CP²_first9"] = cp2_spectrum_first_n(6, 9)

    # Fractal × sphere products
    sg2 = sg_eigvals(2, 30)
    sg2_nonzero = sg2[sg2 > 1e-9][:5]
    sg3 = sg_eigvals(3, 30)
    sg3_nonzero = sg3[sg3 > 1e-9][:5]
    candidates["SG2_first9"] = list(sg2[:9])
    candidates["SG3_first9"] = list(sg3[:9])
    candidates["SG2 × S²"] = product_spectrum_first_n(sg2_nonzero, [0, 2, 6, 12, 20], 9)
    candidates["SG2 × CP²"] = product_spectrum_first_n(sg2_nonzero,
                                                          [0, 4, 32/3, 20], 9)
    candidates["SG3 × S²"] = product_spectrum_first_n(sg3_nonzero, [0, 2, 6, 12, 20], 9)
    candidates["SG3 × CP²"] = product_spectrum_first_n(sg3_nonzero,
                                                          [0, 4, 32/3, 20], 9)

    print(f"{'candidate':<20s} {'eigs (first 9)':>60s}")
    print("-" * 85)
    for name, eigs in candidates.items():
        eigs_str = ", ".join(f"{e:.3f}" for e in eigs)
        print(f"{name:<20s} [{eigs_str}]")
    print()

    # For each: fit, structural signature
    print("=== Fit (linear regression to SM log-m²) + structural match ===\n")
    print(f"{'candidate':<20s} {'a':>9s} {'b':>9s} {'R²':>9s} "
          f"{'sig_clusters':>15s} {'sig_near_deg':>15s}")
    print("-" * 90)
    rows = []
    for name, eigs in candidates.items():
        if len(eigs) < 9:
            print(f"{name:<20s}  (too few eigenvalues)")
            continue
        fit = fit_to_sm(eigs[:9], sm_values)
        if fit is None:
            continue
        # Compute structural signature of fitted predictions
        pred_sig = structural_signature(fit["predicted"])
        max_resid = max(abs(r) for r in fit["residuals"])
        print(f"{name:<20s} {fit['a']:>9.4f} {fit['b']:>9.4f} {fit['r2']:>9.4f} "
              f"{pred_sig['n_clusters']:>15d} {pred_sig['near_deg_pairs']:>15d}")
        rows.append({"test": "candidate_fit", "candidate": name,
                       **fit, "max_residual": float(max_resid),
                       "pred_n_clusters": pred_sig["n_clusters"],
                       "pred_near_deg_pairs": pred_sig["near_deg_pairs"]})
    records.extend(rows)
    print()

    # Best candidate by structural match + R²
    print("=== Verdict ===\n")
    valid = [r for r in rows if r["r2"] > 0.8]
    by_struct = [r for r in valid if r["pred_n_clusters"] == sm_sig["n_clusters"]
                                   and r["pred_near_deg_pairs"] >= len(sm_pairs)]
    if by_struct:
        best = max(by_struct, key=lambda r: r["r2"])
        print(f"  Candidates matching SM structural signature (3 clusters + ≥{len(sm_pairs)} near-deg):")
        for r in by_struct:
            print(f"    {r['candidate']:<20s} R² = {r['r2']:.4f}  "
                  f"max_resid = {r['max_residual']:.3f}")
        print(f"\n  Best: {best['candidate']} (R² = {best['r2']:.4f})")
    else:
        print(f"  NO candidate reproduces SM's structural signature")
        print(f"  (3 clusters AND ≥{len(sm_pairs)} near-degeneracies)")
        print()
        print(f"  Best by R² alone:")
        best_r2 = max(valid, key=lambda r: r["r2"]) if valid else None
        if best_r2:
            print(f"    {best_r2['candidate']} R² = {best_r2['r2']:.4f} "
                  f"but {best_r2['pred_n_clusters']} clusters, "
                  f"{best_r2['pred_near_deg_pairs']} near-deg pairs")

    print()
    print(f"  Null test bar: random 9 values reproduce structural sig "
          f"{100 * null_match_rate:.2f}% of the time")
    print(f"  → Candidates beating this bar are providing real structural signal")

    # Save + plot
    with open(RESULTS_FILE, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    # Plot SM log-m² + best candidates
    fig, ax = plt.subplots(figsize=(13, 6))
    x_pos = np.arange(len(sm_values))
    ax.scatter(x_pos, sm_values, color="black", s=80, zorder=5,
                label="SM log(m²/m_e²)")
    for i, name in enumerate(sm_names):
        ax.annotate(name, (i, sm_values[i]), textcoords="offset points",
                     xytext=(0, 10), ha="center", fontsize=11)

    # Overlay top-3 candidates
    rows_sorted = sorted(rows, key=lambda r: -r["r2"])[:3]
    colors = ["steelblue", "coral", "seagreen"]
    for r, c in zip(rows_sorted, colors):
        ax.plot(x_pos, r["predicted"], "-o", color=c, alpha=0.6,
                  label=f"{r['candidate']} (R²={r['r2']:.3f})")
    ax.set_xticks(x_pos); ax.set_xticklabels(sm_names)
    ax.set_ylabel("ln(m²/m_e²)")
    ax.set_title("SM log-mass² vs candidate F × G/H spectra (MFO-natural variable)")
    ax.legend(); ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "sm-log-mass-spike-2026-05-12.png", dpi=100)
    plt.close()

    print(f"\nResults: {RESULTS_FILE.name}")
    print(f"Plot:    sm-log-mass-spike-2026-05-12.png")


if __name__ == "__main__":
    main()
