"""
Fiedler vs HRP vs GICS — clustering benchmark spike test.

Spike: does the project's graph-Laplacian Fiedler partition (gateway-graph
eigendecomposition primitive, ephemerides-spectral §13) outperform, match, or
underperform Lopez-de-Prado 2016 Hierarchical Risk Parity (HRP) and the GICS
industry-sector classification on an equity-correlation clustering benchmark?

Math-doesn't-lie. MPM discipline: closed-form numerical linear algebra
(numpy/scipy/sklearn); no SGD; no test-set hyperparameter tuning; deterministic
seed for synthetic data. NDJSON output.

References:
- Lopez-de-Prado 2016 *Building Diversified Portfolios that Outperform Out-of-Sample*
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2708678
- Mantegna 1999 https://arxiv.org/abs/cond-mat/9802256
- Onnela et al 2003 https://arxiv.org/abs/cond-mat/0303579
- Ephemerides §13.9 hybrid Fiedler partition (Matthews φ = +0.336, Spearman ρ = +0.743)

Dispatch: D:\\GitHub\\mlehaptics\\docs\\srmech\\notes\\financial-scoping-2026-05-11.md
(Fermata 3 spike-test candidate (a))

Author: concertmaster role, 2026-05-11.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import scipy.cluster.hierarchy as sch
from scipy.linalg import eigh
from scipy.spatial.distance import squareform
from sklearn.cluster import KMeans
from sklearn.metrics import (
    adjusted_rand_score,
    normalized_mutual_info_score,
)

# ---------------------------------------------------------------------------
# Reproducibility and constants (SSOT)
# ---------------------------------------------------------------------------

SEED = 20260511  # 2026-05-11; deterministic across runs
N_BOOTSTRAP = 200  # bootstrap CI samples for accuracy/ARI/NMI

# Block-correlation benchmark (Lopez-de-Prado AFML chapter 16 style)
# 50 assets across 10 GICS-like sectors; 5 assets per sector
N_ASSETS = 50
N_SECTORS = 10
N_PER_SECTOR = 5
INTRA_SECTOR_CORR = 0.5  # moderate within-sector correlation
INTER_SECTOR_CORR = 0.05  # weak between-sector correlation

# T^N quantum-walk lift evaluation timepoints (rad)
TN_LIFT_TIMES = [0.0, 0.1, 0.5, 1.0, 2.0, 5.0]

OUTPUT_DIR = Path(r"D:\GitHub\mlehaptics\docs\srmech\notes")
NDJSON_PATH = OUTPUT_DIR / "fiedler-vs-hrp-vs-gics-spike-per-metric-2026-05-11.ndjson"


# ---------------------------------------------------------------------------
# Data generation (deterministic synthetic correlation matrix)
# ---------------------------------------------------------------------------


def build_block_correlation(
    n_sectors: int,
    n_per_sector: int,
    intra: float,
    inter: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Build a block-correlation matrix with known ground-truth cluster labels.

    Construction: C_ij = 1 if i==j; intra if same sector; inter otherwise.
    This is Lopez-de-Prado's canonical synthetic benchmark for clustering-method
    comparison (Advances in Financial Machine Learning, ch. 16). The block
    structure has a known eigenstructure: one large "market mode" eigenvalue,
    (n_sectors-1) "sector contrast" eigenvalues, and n_sectors*(n_per_sector-1)
    idiosyncratic eigenvalues — directly analogous to MFO Phase B 18-block
    rep-theory prediction from S_k × S_m symmetry.
    """
    n = n_sectors * n_per_sector
    sector_labels = np.repeat(np.arange(n_sectors), n_per_sector)
    same_sector = sector_labels[:, None] == sector_labels[None, :]
    C = np.where(same_sector, intra, inter)
    np.fill_diagonal(C, 1.0)
    return C, sector_labels


def add_correlation_noise(
    C_base: np.ndarray,
    n_observations: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Add realistic sample-correlation noise via Wishart-style return simulation.

    Generate `n_observations` joint-normal returns with population correlation
    `C_base`, then return the empirical sample correlation. Approximately
    matches the noise level of real S&P 500 daily-returns correlation at the
    chosen `n_observations` (e.g., 252 = 1 trading year).
    """
    n_assets = C_base.shape[0]
    # Cholesky of C_base for joint-normal sampling
    L = np.linalg.cholesky(C_base + 1e-12 * np.eye(n_assets))
    Z = rng.standard_normal(size=(n_observations, n_assets))
    R = Z @ L.T
    R_centered = R - R.mean(axis=0)
    C_sample = (R_centered.T @ R_centered) / (n_observations - 1)
    # Normalize to correlation
    d = np.sqrt(np.diag(C_sample))
    C_sample = C_sample / np.outer(d, d)
    # Enforce symmetry against round-off
    C_sample = 0.5 * (C_sample + C_sample.T)
    np.fill_diagonal(C_sample, 1.0)
    return C_sample


# ---------------------------------------------------------------------------
# Correlation distance (Mantegna 1999)
# ---------------------------------------------------------------------------


def correlation_distance(C: np.ndarray) -> np.ndarray:
    """
    Mantegna 1999 correlation distance d_ij = sqrt(2*(1-rho_ij)).

    Properties: d=0 when rho=1, d=sqrt(2) when rho=0, d=2 when rho=-1.
    Satisfies the triangle inequality on positive-semidefinite C.
    """
    # Clip for numerical safety against tiny excursions outside [-1, 1]
    C_clipped = np.clip(C, -1.0, 1.0)
    return np.sqrt(2.0 * (1.0 - C_clipped))


# ---------------------------------------------------------------------------
# Method 1: Fiedler partition (project primitive)
# ---------------------------------------------------------------------------


def fiedler_clustering(
    C: np.ndarray,
    n_clusters: int,
    n_eigenvectors: int = 2,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Spectral clustering via graph-Laplacian Fiedler partition.

    Build the correlation graph with edge weight w_ij = 1 - d_ij/sqrt(2) =
    (1 + rho_ij) / 2 (mapping rho ∈ [-1,1] → w ∈ [0,1], rho=1 → w=1, rho=-1 → w=0).
    Compute the normalized graph Laplacian L = I - D^(-1/2) A D^(-1/2), take the
    first `n_eigenvectors` non-trivial eigenvectors (Fiedler vector + extensions),
    embed assets in R^{n_eigenvectors}, and k-means cluster.

    For 2-cluster case (n_clusters=2), the canonical Fiedler partition is
    sign(f_2). For k > 2, follow the project's §13.9 hybrid approach: embed in
    (f_2, ..., f_{k}) and k-means.

    Returns: (cluster_labels, eigenvalues, fiedler_embedding)
    """
    n = C.shape[0]

    # Adjacency (weights in [0, 1])
    A = 0.5 * (C + 1.0)
    np.fill_diagonal(A, 0.0)  # remove self-loops

    # Degree
    d = A.sum(axis=1)
    d_inv_sqrt = 1.0 / np.sqrt(d + 1e-12)
    D_inv_sqrt = np.diag(d_inv_sqrt)

    # Normalized Laplacian L_sym = I - D^(-1/2) A D^(-1/2)
    L_sym = np.eye(n) - D_inv_sqrt @ A @ D_inv_sqrt
    L_sym = 0.5 * (L_sym + L_sym.T)  # symmetrize against round-off

    # Eigendecomposition (smallest first)
    eigvals, eigvecs = eigh(L_sym)

    # First eigenvalue ~ 0 (trivial); use eigenvectors 1..n_eigenvectors (Fiedler+)
    embedding = eigvecs[:, 1:1 + n_eigenvectors]

    # k-means in the eigenbasis (deterministic seed)
    if n_clusters == 2:
        # Canonical Fiedler partition: sign(f_2)
        labels = (embedding[:, 0] > 0).astype(int)
    else:
        km = KMeans(n_clusters=n_clusters, random_state=SEED, n_init=10)
        labels = km.fit_predict(embedding)

    return labels, eigvals, embedding


# ---------------------------------------------------------------------------
# Method 2: Hierarchical Risk Parity (Lopez-de-Prado 2016)
# ---------------------------------------------------------------------------


def hrp_clustering(C: np.ndarray, n_clusters: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    HRP clustering: single-linkage hierarchical clustering on correlation distance.

    Lopez-de-Prado 2016 uses single-linkage on d_ij = sqrt(0.5*(1-rho)); the
    Mantegna-1999 distance d_ij = sqrt(2*(1-rho)) is equivalent up to a constant
    scale factor and preserves cluster topology. We use the Mantegna form for
    consistency with the rest of the spike.

    Returns: (cluster_labels, linkage_matrix)
    """
    D = correlation_distance(C)
    # scipy expects condensed distance matrix
    D_condensed = squareform(D, checks=False)

    # Single-linkage clustering (Lopez-de-Prado canonical choice)
    Z = sch.linkage(D_condensed, method="single")

    # Cut tree at k clusters
    labels = sch.fcluster(Z, t=n_clusters, criterion="maxclust")
    # Normalize labels to 0..k-1
    _, labels = np.unique(labels, return_inverse=True)
    return labels, Z


# ---------------------------------------------------------------------------
# Method 3: GICS-style ground-truth labels
# ---------------------------------------------------------------------------
# Ground truth IS the block-structure sector labels; this is the benchmark
# against which Fiedler and HRP are scored.


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


def cluster_purity(true_labels: np.ndarray, pred_labels: np.ndarray) -> float:
    """
    Cluster purity: fraction of points correctly clustered.

    For each predicted cluster, assign it the most-common true label; count
    matches.
    """
    n = len(true_labels)
    correct = 0
    for c in np.unique(pred_labels):
        mask = pred_labels == c
        if mask.sum() == 0:
            continue
        most_common = np.bincount(true_labels[mask]).argmax()
        correct += (true_labels[mask] == most_common).sum()
    return correct / n


def cluster_size_distribution(labels: np.ndarray) -> Dict[str, float]:
    """Per-cluster size summary: min, max, std (cluster-size imbalance)."""
    _, counts = np.unique(labels, return_counts=True)
    return {
        "min_size": int(counts.min()),
        "max_size": int(counts.max()),
        "std_size": float(counts.std()),
        "n_clusters_nonempty": int(len(counts)),
    }


def eigenvalue_gap(eigvals: np.ndarray, k: int) -> Dict[str, float]:
    """
    Eigenvalue-gap signature: ratio of (k+1)-th to k-th non-trivial eigenvalue.

    A meaningful gap at index k indicates k clusters are well-separated. Returns
    eigenvalue at index k, gap (lambda_{k+1} - lambda_k), and ratio lambda_{k+1}/lambda_k.
    """
    return {
        "lambda_k": float(eigvals[k]),
        "lambda_k_plus_1": float(eigvals[k + 1]),
        "gap": float(eigvals[k + 1] - eigvals[k]),
        "ratio": float(eigvals[k + 1] / (eigvals[k] + 1e-12)),
    }


# ---------------------------------------------------------------------------
# Bootstrap confidence intervals
# ---------------------------------------------------------------------------


def bootstrap_metric(
    metric_fn,
    true_labels: np.ndarray,
    pred_labels: np.ndarray,
    n_boot: int,
    rng: np.random.Generator,
) -> Tuple[float, float, float]:
    """
    Bootstrap (mean, lower, upper) 95% CI for a clustering metric.

    Resamples (true, pred) label pairs with replacement.
    """
    n = len(true_labels)
    samples = np.empty(n_boot, dtype=float)
    for b in range(n_boot):
        idx = rng.integers(0, n, size=n)
        samples[b] = metric_fn(true_labels[idx], pred_labels[idx])
    return float(samples.mean()), float(np.percentile(samples, 2.5)), float(np.percentile(samples, 97.5))


# ---------------------------------------------------------------------------
# T^N quantum-walk lift side-experiment
# ---------------------------------------------------------------------------


def tn_quantum_walk_lift(
    C: np.ndarray,
    times: List[float],
    sector_labels: np.ndarray,
) -> List[Dict]:
    """
    T^N quantum-walk lift U(t) = exp(-i L t) on the correlation Laplacian.

    Per srmech §3.5.1 layer (b): phase-preserving evolution on the same Laplacian
    eigenbasis that Fiedler/HRP use magnitude-only. The question: does the
    magnitude (|psi|^2) at t > 0 reproduce the Fiedler partition? Do the phases
    surface sub-structure invisible to magnitude-PCA?

    Method: start with a uniform initial state psi_0 = 1/sqrt(N), evolve via
    exp(-i L t), measure (a) the cluster purity of magnitude-based clustering
    after evolution, (b) the phase variance per ground-truth sector.

    Returns: per-time NDJSON-style records.
    """
    n = C.shape[0]
    A = 0.5 * (C + 1.0)
    np.fill_diagonal(A, 0.0)
    d = A.sum(axis=1)
    d_inv_sqrt = 1.0 / np.sqrt(d + 1e-12)
    D_inv_sqrt = np.diag(d_inv_sqrt)
    L_sym = np.eye(n) - D_inv_sqrt @ A @ D_inv_sqrt
    L_sym = 0.5 * (L_sym + L_sym.T)

    # Diagonalize once
    eigvals, eigvecs = eigh(L_sym)

    # Initial state: localized on each asset, evolve, look at coherence
    # Use a different initialization: localized "kicks" then evolve
    records = []
    for t in times:
        # Spectral exponentiation: U(t) = V @ diag(exp(-i*lambda*t)) @ V^T
        phase_factors = np.exp(-1j * eigvals * t)
        # Apply to identity (gives the full propagator as a matrix)
        U = eigvecs @ np.diag(phase_factors) @ eigvecs.T

        # Magnitude- and phase-based per-asset signature: U @ uniform_state
        psi_0 = np.ones(n, dtype=complex) / np.sqrt(n)
        psi_t = U @ psi_0

        magnitudes = np.abs(psi_t)
        phases = np.angle(psi_t)

        # Phase variance per sector (the load-bearing test for "phase surfaces info")
        phase_var_per_sector = []
        for s in np.unique(sector_labels):
            ph = phases[sector_labels == s]
            # Circular variance for phase data
            mean_vec = np.exp(1j * ph).mean()
            circ_var = 1.0 - np.abs(mean_vec)
            phase_var_per_sector.append(float(circ_var))

        # Magnitude variance per sector (control: does magnitude show sector structure?)
        mag_var_per_sector = []
        for s in np.unique(sector_labels):
            mg = magnitudes[sector_labels == s]
            mag_var_per_sector.append(float(mg.var()))

        # Phase-based clustering: use phases as 1D embedding (after wrapping),
        # treat phase distance via circular metric, cluster with KMeans on
        # (cos(phase), sin(phase)) 2D embedding (Stack/Plotkin-style circular k-means)
        if t > 0:
            phase_embed = np.column_stack([np.cos(phases), np.sin(phases)])
            km_phase = KMeans(n_clusters=N_SECTORS, random_state=SEED, n_init=10)
            phase_labels = km_phase.fit_predict(phase_embed)
            phase_purity = cluster_purity(sector_labels, phase_labels)
            phase_ari = adjusted_rand_score(sector_labels, phase_labels)
        else:
            phase_purity = float("nan")
            phase_ari = float("nan")

        records.append(
            {
                "time": float(t),
                "mean_circular_phase_var": float(np.mean(phase_var_per_sector)),
                "mean_magnitude_var": float(np.mean(mag_var_per_sector)),
                "phase_clustering_purity": float(phase_purity) if t > 0 else None,
                "phase_clustering_ari": float(phase_ari) if t > 0 else None,
                "max_magnitude": float(magnitudes.max()),
                "min_magnitude": float(magnitudes.min()),
            }
        )

    return records


# ---------------------------------------------------------------------------
# Main spike experiment
# ---------------------------------------------------------------------------


@dataclass
class SpikeResult:
    method: str
    metric: str
    value: float
    ci_low: float
    ci_high: float
    ground_truth: str
    config: Dict


def run_spike(
    n_observations: int,
    rng: np.random.Generator,
    label: str,
) -> List[Dict]:
    """
    Run the full Fiedler vs HRP vs GICS comparison at a given sample size.

    Returns list of NDJSON-style records.
    """
    # Generate noisy sample correlation
    C_base, sector_labels = build_block_correlation(
        N_SECTORS, N_PER_SECTOR, INTRA_SECTOR_CORR, INTER_SECTOR_CORR
    )
    C_sample = add_correlation_noise(C_base, n_observations, rng)

    results: List[Dict] = []

    # --- Method 1: Fiedler partition ---
    fiedler_labels, fiedler_eigvals, fiedler_embedding = fiedler_clustering(
        C_sample, n_clusters=N_SECTORS, n_eigenvectors=N_SECTORS - 1
    )

    # Metrics
    f_purity = cluster_purity(sector_labels, fiedler_labels)
    f_nmi = normalized_mutual_info_score(sector_labels, fiedler_labels)
    f_ari = adjusted_rand_score(sector_labels, fiedler_labels)

    # Bootstrap CIs
    f_purity_mean, f_purity_lo, f_purity_hi = bootstrap_metric(
        cluster_purity, sector_labels, fiedler_labels, N_BOOTSTRAP, rng
    )
    f_ari_mean, f_ari_lo, f_ari_hi = bootstrap_metric(
        adjusted_rand_score, sector_labels, fiedler_labels, N_BOOTSTRAP, rng
    )
    f_nmi_mean, f_nmi_lo, f_nmi_hi = bootstrap_metric(
        normalized_mutual_info_score,
        sector_labels,
        fiedler_labels,
        N_BOOTSTRAP,
        rng,
    )

    f_sizes = cluster_size_distribution(fiedler_labels)
    f_gap = eigenvalue_gap(fiedler_eigvals, N_SECTORS)

    config = {
        "n_assets": N_ASSETS,
        "n_sectors": N_SECTORS,
        "n_per_sector": N_PER_SECTOR,
        "intra_sector_corr": INTRA_SECTOR_CORR,
        "inter_sector_corr": INTER_SECTOR_CORR,
        "n_observations": n_observations,
        "n_clusters_requested": N_SECTORS,
        "label": label,
        "seed": SEED,
    }

    for metric_name, val, lo, hi in [
        ("purity", f_purity, f_purity_lo, f_purity_hi),
        ("nmi", f_nmi, f_nmi_lo, f_nmi_hi),
        ("ari", f_ari, f_ari_lo, f_ari_hi),
    ]:
        results.append(
            {
                "method": "Fiedler",
                "metric": metric_name,
                "value": float(val),
                "ci_low": float(lo),
                "ci_high": float(hi),
                "ground_truth": "GICS_block_labels",
                "config": config,
            }
        )

    results.append(
        {
            "method": "Fiedler",
            "metric": "eigenvalue_gap_at_k",
            "value": f_gap["gap"],
            "lambda_k": f_gap["lambda_k"],
            "lambda_k_plus_1": f_gap["lambda_k_plus_1"],
            "ratio": f_gap["ratio"],
            "config": config,
        }
    )
    results.append(
        {
            "method": "Fiedler",
            "metric": "cluster_size_distribution",
            "min_size": f_sizes["min_size"],
            "max_size": f_sizes["max_size"],
            "std_size": f_sizes["std_size"],
            "n_clusters_nonempty": f_sizes["n_clusters_nonempty"],
            "config": config,
        }
    )

    # --- Method 2: HRP (single-linkage hierarchical) ---
    hrp_labels, hrp_Z = hrp_clustering(C_sample, n_clusters=N_SECTORS)

    h_purity = cluster_purity(sector_labels, hrp_labels)
    h_nmi = normalized_mutual_info_score(sector_labels, hrp_labels)
    h_ari = adjusted_rand_score(sector_labels, hrp_labels)

    h_purity_mean, h_purity_lo, h_purity_hi = bootstrap_metric(
        cluster_purity, sector_labels, hrp_labels, N_BOOTSTRAP, rng
    )
    h_ari_mean, h_ari_lo, h_ari_hi = bootstrap_metric(
        adjusted_rand_score, sector_labels, hrp_labels, N_BOOTSTRAP, rng
    )
    h_nmi_mean, h_nmi_lo, h_nmi_hi = bootstrap_metric(
        normalized_mutual_info_score, sector_labels, hrp_labels, N_BOOTSTRAP, rng
    )

    h_sizes = cluster_size_distribution(hrp_labels)

    # Dendrogram cut height at k clusters (HRP equivalent of "eigenvalue gap")
    # Z[:, 2] is the merge-distance at each merge; the (N - k)-th merge is the
    # final merge that produces k clusters; the gap between that merge and the
    # (N - k - 1)-th merge is the "cut quality"
    if N_SECTORS < N_ASSETS:
        cut_distance = float(hrp_Z[-N_SECTORS, 2]) if N_SECTORS > 1 else float("nan")
        next_distance = (
            float(hrp_Z[-N_SECTORS - 1, 2])
            if N_SECTORS > 1 and N_SECTORS < N_ASSETS - 1
            else float("nan")
        )
        cut_gap = cut_distance - next_distance
    else:
        cut_distance = float("nan")
        next_distance = float("nan")
        cut_gap = float("nan")

    for metric_name, val, lo, hi in [
        ("purity", h_purity, h_purity_lo, h_purity_hi),
        ("nmi", h_nmi, h_nmi_lo, h_nmi_hi),
        ("ari", h_ari, h_ari_lo, h_ari_hi),
    ]:
        results.append(
            {
                "method": "HRP",
                "metric": metric_name,
                "value": float(val),
                "ci_low": float(lo),
                "ci_high": float(hi),
                "ground_truth": "GICS_block_labels",
                "config": config,
            }
        )

    results.append(
        {
            "method": "HRP",
            "metric": "dendrogram_cut_gap",
            "value": cut_gap,
            "cut_distance": cut_distance,
            "next_distance": next_distance,
            "config": config,
        }
    )
    results.append(
        {
            "method": "HRP",
            "metric": "cluster_size_distribution",
            "min_size": h_sizes["min_size"],
            "max_size": h_sizes["max_size"],
            "std_size": h_sizes["std_size"],
            "n_clusters_nonempty": h_sizes["n_clusters_nonempty"],
            "config": config,
        }
    )

    # --- Method 3: GICS (ground truth = perfect baseline) ---
    # Trivially purity=1, NMI=1, ARI=1 by construction; we include it for completeness
    results.append(
        {
            "method": "GICS",
            "metric": "purity",
            "value": 1.0,
            "ci_low": 1.0,
            "ci_high": 1.0,
            "ground_truth": "self",
            "config": config,
        }
    )
    results.append(
        {
            "method": "GICS",
            "metric": "nmi",
            "value": 1.0,
            "ci_low": 1.0,
            "ci_high": 1.0,
            "ground_truth": "self",
            "config": config,
        }
    )
    results.append(
        {
            "method": "GICS",
            "metric": "ari",
            "value": 1.0,
            "ci_low": 1.0,
            "ci_high": 1.0,
            "ground_truth": "self",
            "config": config,
        }
    )

    # --- T^N quantum-walk lift side experiment ---
    tn_records = tn_quantum_walk_lift(C_sample, TN_LIFT_TIMES, sector_labels)
    for rec in tn_records:
        rec.update({"method": "TN_quantum_walk_lift", "config": config})
        results.append(rec)

    # --- 2-way Fiedler partition (canonical sign-of-Fiedler-vector) ---
    # For comparison to ephemerides §13 (which is a 2-way partition)
    fiedler_2way_labels, _, _ = fiedler_clustering(
        C_sample, n_clusters=2, n_eigenvectors=1
    )
    # Synthetic 2-way ground truth: split sectors 0-4 vs 5-9 (arbitrary but consistent)
    sector_2way_truth = (sector_labels >= N_SECTORS // 2).astype(int)
    f2_purity = cluster_purity(sector_2way_truth, fiedler_2way_labels)
    f2_ari = adjusted_rand_score(sector_2way_truth, fiedler_2way_labels)
    f2_nmi = normalized_mutual_info_score(sector_2way_truth, fiedler_2way_labels)

    results.append(
        {
            "method": "Fiedler_2way_sign_of_f2",
            "metric": "purity_vs_arbitrary_2way",
            "value": float(f2_purity),
            "ari": float(f2_ari),
            "nmi": float(f2_nmi),
            "note": (
                "2-way Fiedler is the canonical sign-of-Fiedler-vector partition "
                "(ephemerides §13 style). Arbitrary 2-way ground truth (sectors 0-4 "
                "vs 5-9) is not a meaningful benchmark when blocks are interchangeable; "
                "included to make project parity visible."
            ),
            "config": config,
        }
    )

    return results


def run_anomaly_chase(rng: np.random.Generator) -> List[Dict]:
    """
    Anomaly investigations triggered by the main spike.

    Specifically:
    (1) Why might Fiedler outperform / underperform HRP at different cluster
        cardinalities? Test k=2, 5, 10, 15.
    (2) Sensitivity to intra-sector correlation strength.
    (3) Eigenvalue spectrum visualization data (for verifying GICS-symmetric
        block structure produces 1 + (k-1) + k(m-1) eigenvalue pattern).
    """
    anomalies: List[Dict] = []

    # Anomaly 1: cluster-cardinality sensitivity
    C_base, sector_labels = build_block_correlation(
        N_SECTORS, N_PER_SECTOR, INTRA_SECTOR_CORR, INTER_SECTOR_CORR
    )
    C_sample = add_correlation_noise(C_base, 252, rng)

    for k_test in [2, 5, 10, 15, 20]:
        if k_test == 2:
            fiedler_labels, _, _ = fiedler_clustering(
                C_sample, n_clusters=2, n_eigenvectors=1
            )
        else:
            fiedler_labels, _, _ = fiedler_clustering(
                C_sample, n_clusters=k_test, n_eigenvectors=k_test - 1
            )
        hrp_labels, _ = hrp_clustering(C_sample, n_clusters=k_test)

        f_ari = adjusted_rand_score(sector_labels, fiedler_labels)
        h_ari = adjusted_rand_score(sector_labels, hrp_labels)
        f_purity = cluster_purity(sector_labels, fiedler_labels)
        h_purity = cluster_purity(sector_labels, hrp_labels)

        anomalies.append(
            {
                "anomaly_chase": "cardinality_sensitivity",
                "k_clusters": k_test,
                "fiedler_ari": float(f_ari),
                "hrp_ari": float(h_ari),
                "fiedler_purity": float(f_purity),
                "hrp_purity": float(h_purity),
                "delta_ari_fiedler_minus_hrp": float(f_ari - h_ari),
            }
        )

    # Anomaly 2: intra-sector correlation sensitivity (extended low-SNR sweep)
    for intra in [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.50, 0.65, 0.80]:
        C_base_alt, sector_labels_alt = build_block_correlation(
            N_SECTORS, N_PER_SECTOR, intra, INTER_SECTOR_CORR
        )
        C_sample_alt = add_correlation_noise(C_base_alt, 252, rng)

        fiedler_labels, _, _ = fiedler_clustering(
            C_sample_alt, n_clusters=N_SECTORS, n_eigenvectors=N_SECTORS - 1
        )
        hrp_labels, _ = hrp_clustering(C_sample_alt, n_clusters=N_SECTORS)

        f_ari = adjusted_rand_score(sector_labels_alt, fiedler_labels)
        h_ari = adjusted_rand_score(sector_labels_alt, hrp_labels)

        anomalies.append(
            {
                "anomaly_chase": "intra_corr_sensitivity",
                "intra_sector_corr": float(intra),
                "fiedler_ari": float(f_ari),
                "hrp_ari": float(h_ari),
                "delta_ari_fiedler_minus_hrp": float(f_ari - h_ari),
            }
        )

    # Anomaly 3: eigenvalue spectrum vs S_k × S_m prediction
    # For perfect block model (no noise), expected eigenvalues:
    # - 1 large mode: 1 + (m-1)*intra + (k-1)*m*inter  (with m=n_per_sector, k=n_sectors)
    # - (k-1) sector contrast modes at: 1 + (m-1)*intra - m*inter
    # - k*(m-1) idiosyncratic modes at: 1 - intra
    # Test on the noiseless base matrix
    eigvals_base, _ = eigh(C_base)
    eigvals_base_sorted = np.sort(eigvals_base)[::-1]  # largest first

    m = N_PER_SECTOR
    k = N_SECTORS
    predicted_market_mode = 1 + (m - 1) * INTRA_SECTOR_CORR + (k - 1) * m * INTER_SECTOR_CORR
    predicted_sector_contrast = 1 + (m - 1) * INTRA_SECTOR_CORR - m * INTER_SECTOR_CORR
    predicted_idiosyncratic = 1 - INTRA_SECTOR_CORR

    anomalies.append(
        {
            "anomaly_chase": "block_model_eigenvalue_prediction",
            "predicted_market_mode": float(predicted_market_mode),
            "empirical_eigval_0": float(eigvals_base_sorted[0]),
            "predicted_sector_contrast": float(predicted_sector_contrast),
            "empirical_eigval_1_to_9_mean": float(eigvals_base_sorted[1:k].mean()),
            "predicted_idiosyncratic": float(predicted_idiosyncratic),
            "empirical_eigval_10_to_49_mean": float(eigvals_base_sorted[k:].mean()),
            "n_sector_contrast_modes_predicted": int(k - 1),
            "n_idiosyncratic_modes_predicted": int(k * (m - 1)),
            "n_total_modes": int(N_ASSETS),
            "note": (
                "MFO Phase B 18-block style: structural prediction from group "
                "symmetry S_k × S_m. Should match perfectly on noiseless base C."
            ),
        }
    )

    return anomalies


def run_realistic_snr_sweep(rng: np.random.Generator) -> List[Dict]:
    """
    Realistic S&P-500-style sweep at discrimination-zone intra-corr.

    The main benchmark intra=0.5, inter=0.05 is unrealistically clean — real
    S&P 500 daily-returns inter-sector correlations are ~0.3 (market mode is
    dominant). This sweep tests the discrimination zone with realistic noise.

    Multiple independent samples per condition (n_trials) to get robust
    win/lose statistics.
    """
    records: List[Dict] = []

    # Realistic S&P 500 sector parameters (Onnela et al 2003 typical ranges)
    # Strong market mode means inter-sector ~ 0.3, intra-sector ~ 0.5
    n_trials = 20

    for intra, inter, scenario in [
        (0.50, 0.30, "SP500_realistic_strong_market_mode"),
        (0.40, 0.25, "SP500_realistic_moderate_market_mode"),
        (0.30, 0.20, "SP500_realistic_weak_market_mode"),
        (0.25, 0.05, "block_model_weak_intra"),
        (0.20, 0.05, "block_model_very_weak_intra"),
    ]:
        f_aris: List[float] = []
        h_aris: List[float] = []
        f_purities: List[float] = []
        h_purities: List[float] = []
        tn_phase_purities: List[float] = []

        for trial in range(n_trials):
            C_base, sector_labels = build_block_correlation(
                N_SECTORS, N_PER_SECTOR, intra, inter
            )
            C_sample = add_correlation_noise(C_base, 252, rng)

            fiedler_labels, _, _ = fiedler_clustering(
                C_sample, n_clusters=N_SECTORS, n_eigenvectors=N_SECTORS - 1
            )
            hrp_labels, _ = hrp_clustering(C_sample, n_clusters=N_SECTORS)

            f_aris.append(adjusted_rand_score(sector_labels, fiedler_labels))
            h_aris.append(adjusted_rand_score(sector_labels, hrp_labels))
            f_purities.append(cluster_purity(sector_labels, fiedler_labels))
            h_purities.append(cluster_purity(sector_labels, hrp_labels))

            # T^N walk phase-clustering at the discrimination zone
            tn = tn_quantum_walk_lift(C_sample, [1.0], sector_labels)
            if tn[0]["phase_clustering_purity"] is not None:
                tn_phase_purities.append(tn[0]["phase_clustering_purity"])

        records.append(
            {
                "anomaly_chase": "realistic_snr_sweep",
                "scenario": scenario,
                "intra_sector_corr": intra,
                "inter_sector_corr": inter,
                "n_trials": n_trials,
                "fiedler_ari_mean": float(np.mean(f_aris)),
                "fiedler_ari_std": float(np.std(f_aris)),
                "hrp_ari_mean": float(np.mean(h_aris)),
                "hrp_ari_std": float(np.std(h_aris)),
                "fiedler_purity_mean": float(np.mean(f_purities)),
                "hrp_purity_mean": float(np.mean(h_purities)),
                "tn_phase_purity_mean": float(np.mean(tn_phase_purities))
                if tn_phase_purities
                else None,
                "delta_ari_fiedler_minus_hrp_mean": float(
                    np.mean(np.array(f_aris) - np.array(h_aris))
                ),
                "fiedler_wins_count": int(
                    np.sum(np.array(f_aris) > np.array(h_aris))
                ),
                "hrp_wins_count": int(
                    np.sum(np.array(h_aris) > np.array(f_aris))
                ),
                "ties_count": int(np.sum(np.array(f_aris) == np.array(h_aris))),
            }
        )
        print(
            f"[OK] {scenario}: Fiedler ARI {np.mean(f_aris):.3f} vs HRP ARI "
            f"{np.mean(h_aris):.3f} (delta {np.mean(f_aris) - np.mean(h_aris):+.3f}, "
            f"F wins {np.sum(np.array(f_aris) > np.array(h_aris))}/{n_trials})"
        )

    return records


def main():
    rng = np.random.default_rng(SEED)

    # Multi-sample-size sweep
    all_results: List[Dict] = []
    for n_obs, label in [
        (252, "1_year_daily"),
        (1260, "5_year_daily"),
        (5040, "20_year_daily"),
    ]:
        results = run_spike(n_obs, rng, label)
        all_results.extend(results)
        print(f"[OK] Completed {label}: n={n_obs} observations")

    # Anomaly investigations
    anomaly_results = run_anomaly_chase(rng)
    all_results.extend(anomaly_results)
    print(f"[OK] Completed anomaly chase ({len(anomaly_results)} records)")

    # Realistic-SNR multi-trial sweep
    snr_results = run_realistic_snr_sweep(rng)
    all_results.extend(snr_results)
    print(f"[OK] Completed realistic SNR sweep ({len(snr_results)} scenarios)")

    # Write NDJSON
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with NDJSON_PATH.open("w", encoding="utf-8") as f:
        for rec in all_results:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"[OK] NDJSON written: {NDJSON_PATH}")
    print(f"[OK] Total records: {len(all_results)}")

    # Print key headline numbers
    print("\n=== HEADLINE METRICS (n_observations=252, 1 trading year) ===")
    for rec in all_results:
        if rec.get("config", {}).get("label") == "1_year_daily" and rec.get("metric") in [
            "purity",
            "ari",
            "nmi",
        ]:
            method = rec["method"]
            metric = rec["metric"]
            val = rec["value"]
            print(f"  {method:30s} | {metric:8s} = {val:.4f}")


if __name__ == "__main__":
    main()
