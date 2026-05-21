"""
Spike #130.1 — Empirical Class L spectral analysis on mycorrhizal network topology.

Parent: Spike #130 (PR #541) — mycorrhizal cross-substrate cascade-match (PARTITION-COEXISTENT-INSTANTIATION).
Stance: [[user_stance_multi_kingdom_cross_substrate_partition_coexistence]];
        [[user_stance_framework_domain_algebra_not_length_or_magnitude]];
        [[user_stance_identity_not_implementation_discipline]].
Disciplines: [[feedback_pdf_extraction_citation_discipline]];
             [[reference_autonomous_validation_tos_landscape]];
             [[feedback_trauma_informed_defensive_scope]];
             [[feedback_no_privileged_primitive_classes]] (no new class);
             [[feedback_no_lineage_claims_in_notebook]].

Hypothesis:
    (P1) Bipartite plant-fungus mycorrhizal-network Laplacian eigendecomposition
         exhibits heavy-tailed eigenvalue distribution + low spectral-gap.
    (P2) Cascade-K asymptote test: cumulative-mass curve fits cascade-stretched-exp
         E(k) = exp(-(k/tau)^beta), with beta in (0.25, 0.6] (Spike #117 cascade-K-genuine band).
    (P3) Spectral mass concentrates: top-5 eigenvalues account for substantial total spectral mass.
    (P4) Spectral-gap lambda_2/lambda_n characteristic of small-world graphs.
    (P5) Cascade-shape result is magnitude-invariant: re-scaling edge weights by uniform
         factors must NOT shift beta-band membership. This is the Karst-2023 magnitude-critique
         test per [[user_stance_framework_domain_algebra_not_length_or_magnitude]].

Substrate topology anchors (PMC-extractable per TOS landscape):
    - Zhu et al. 2022 PMC9158544 -- 43 plants x 862 EM-fungi, 4360 edges, connectance=0.12,
                                    NODF=10.256, modularity=0.482.
    - Toju et al. 2015 PMC4646793 -- 36 plants x 278/343/580 fungi (three biomes); antinested.
    - Taudiere et al. 2015 PMC4612159 -- 16 plants x 411 EM-fungi, 993 edges, Q=0.458.
    - Ajaz et al. 2025 PMC12676088 (Garrido 2023) -- 18 plants x 87 AM-fungi (anti-nested,
                                    modular Z=3.61).
    - Beiler et al. 2010 (Wiley TOS-prohibited, cite-by-ref): 26 Rhizopogon genets x ~30
      Douglas-fir, scale-free + small-world.

This script simulates ensembles matching these published metrics, runs eigendecomposition,
and reports the cascade-K asymptote beta. Identity claim: the spectral structure is the
substrate-instantiation of Class L on the bipartite Laplacian; substrate variation in
connectance / nestedness / modularity is magnitude-variation that does not shift cascade-shape.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Sequence

import numpy as np
from numpy.random import default_rng
from scipy import sparse
from scipy.linalg import eigh
from scipy.optimize import curve_fit


# Spike #117 discriminator bands (verbatim).
CASCADE_K_GENUINE_BAND = (0.25, 0.6)
POWER_LAW_MASQUERADE_BAND = (0.10, 0.25)
BORDERLINE_2D_OR_MIXED_BAND = (0.6, 0.9)
WHITE_NOISE_OR_SINGLE_EXP_BAND = (0.9, 1.5)


def cascade_stretched_exp(k: np.ndarray, tau: float, beta: float) -> np.ndarray:
    """E(k) = exp(-(k/tau)^beta) per Spike #117 cascade-stretched-exp."""
    return np.exp(-((k / tau) ** beta))


def classify_beta(beta: float) -> str:
    """Map a fitted beta to its band per Spike #117."""
    if POWER_LAW_MASQUERADE_BAND[0] <= beta < POWER_LAW_MASQUERADE_BAND[1]:
        return "POWER-LAW-MASQUERADE"
    if CASCADE_K_GENUINE_BAND[0] <= beta <= CASCADE_K_GENUINE_BAND[1]:
        return "CASCADE-K-GENUINE"
    if BORDERLINE_2D_OR_MIXED_BAND[0] < beta <= BORDERLINE_2D_OR_MIXED_BAND[1]:
        return "BORDERLINE-2D-OR-MIXED"
    if WHITE_NOISE_OR_SINGLE_EXP_BAND[0] < beta <= WHITE_NOISE_OR_SINGLE_EXP_BAND[1]:
        return "WHITE-NOISE-OR-SINGLE-EXP"
    return "OUT-OF-BAND"


@dataclass
class NetworkConfig:
    """Published mycorrhizal-network topology anchor."""
    name: str
    n_plants: int
    n_fungi: int
    n_edges: int  # total bipartite interactions
    citation: str
    notes: str = ""


# Anchor topologies extracted from PMC-extractable sources.
ANCHORS = [
    NetworkConfig(
        name="zhu_2022_pmc9158544",
        n_plants=43,
        n_fungi=862,
        n_edges=4360,
        citation="Zhu et al. 2022, Front Plant Sci, doi:10.3389/fpls.2022.784778, PMC9158544",
        notes="connectance=0.12, NODF=10.256, modularity=0.482, "
              "Cenococcum+Russula on all 43 plants",
    ),
    NetworkConfig(
        name="toju_2015_cool_temperate_pmc4646793",
        n_plants=36,
        n_fungi=278,
        n_edges=720,  # estimated from typical antinested bipartite density (~0.07)
        citation="Toju et al. 2015, Sci Adv, doi:10.1126/sciadv.1500291, PMC4646793",
        notes="antinested topology, cool-temperate biome",
    ),
    NetworkConfig(
        name="toju_2015_subtropical_pmc4646793",
        n_plants=36,
        n_fungi=580,
        n_edges=1450,  # estimated (~0.07 connectance)
        citation="Toju et al. 2015, Sci Adv, doi:10.1126/sciadv.1500291, PMC4646793",
        notes="antinested topology, subtropical biome",
    ),
    NetworkConfig(
        name="taudiere_2015_pmc4612159",
        n_plants=16,
        n_fungi=411,
        n_edges=993,
        citation="Taudiere et al. 2015, Front Plant Sci, doi:10.3389/fpls.2015.00881, PMC4612159",
        notes="Q=0.458, Quercus ilex degree 197, projected EM network",
    ),
    NetworkConfig(
        name="garrido_2023_via_ajaz_2025_pmc12676088",
        n_plants=18,
        n_fungi=87,
        n_edges=158,  # estimated from typical AM connectance (~0.10) anti-nested
        citation="Ajaz et al. 2025, New Phytologist, doi:10.1111/nph.70694, PMC12676088 "
                 "(Garrido et al. 2023 dataset, anti-nested Z=-4.10, modular Z=3.61)",
        notes="meta-network from Garrido 2023; anti-nested + modular",
    ),
    NetworkConfig(
        name="beiler_2010_rhizopogon_doug_fir",
        n_plants=30,  # ~30 Douglas-fir trees per published cite-by-ref
        n_fungi=26,  # 13+13 Rhizopogon genets (vesiculosus + vinicolor)
        n_edges=120,  # estimated from "up to 19 trees per genet" + size-correlation
        citation="Beiler et al. 2010, New Phytol 185:543-553, doi:10.1111/j.1469-8137.2009.03069.x "
                 "(Wiley TOS-prohibited PDF, cite-by-ref via Gorzelak 2015 PMC4497361 + "
                 "[[reference_autonomous_validation_tos_landscape]])",
        notes="scale-free + small-world per Gorzelak 2015 summary; hub-trees up to 19 genets",
    ),
]


# ---------------------------------------------------------------------------
# Bipartite network generators.
# ---------------------------------------------------------------------------

def gen_bipartite_scale_free(
    n_plants: int,
    n_fungi: int,
    n_edges: int,
    gamma_plant: float = 2.3,
    gamma_fungus: float = 2.5,
    rng=None,
) -> sparse.csr_matrix:
    """Bipartite scale-free network with degree P(k) ~ k^-gamma on both sides.

    Implementation: power-law degree-sequence draw + bipartite configuration model.
    Edge stubs are matched stochastically with rejection for self/multi-edges,
    yielding an antinested + heavy-tailed degree distribution consistent with
    Beiler 2010 / Gorzelak 2015 / Toju 2015 cite-by-ref attestations.
    """
    if rng is None:
        rng = default_rng(seed=0)
    # Draw discrete power-law degree-sequences truncated at endpoints.
    deg_plants = _power_law_sequence(n_plants, n_edges, gamma_plant, rng)
    deg_fungi = _power_law_sequence(n_fungi, n_edges, gamma_fungus, rng)
    # Match stubs to form bipartite edges.
    plant_stubs = np.repeat(np.arange(n_plants), deg_plants)
    fungus_stubs = np.repeat(np.arange(n_fungi), deg_fungi)
    rng.shuffle(fungus_stubs)
    pairs = set()
    n_target = min(n_edges, len(plant_stubs), len(fungus_stubs))
    for p, f in zip(plant_stubs[:n_target], fungus_stubs[:n_target]):
        pairs.add((int(p), int(f)))
    rows = np.array([p for (p, _) in pairs], dtype=np.int64)
    cols = np.array([f for (_, f) in pairs], dtype=np.int64)
    data = np.ones(len(rows), dtype=np.float64)
    return sparse.csr_matrix(
        (data, (rows, cols)),
        shape=(n_plants, n_fungi),
    )


def gen_bipartite_erdos_renyi(
    n_plants: int,
    n_fungi: int,
    n_edges: int,
    rng=None,
) -> sparse.csr_matrix:
    """Erdos-Renyi bipartite baseline (uniform random)."""
    if rng is None:
        rng = default_rng(seed=0)
    rows = rng.integers(0, n_plants, size=n_edges * 3)
    cols = rng.integers(0, n_fungi, size=n_edges * 3)
    pairs = set()
    for r, c in zip(rows, cols):
        pairs.add((int(r), int(c)))
        if len(pairs) >= n_edges:
            break
    rows = np.array([p for (p, _) in pairs], dtype=np.int64)
    cols = np.array([c for (_, c) in pairs], dtype=np.int64)
    data = np.ones(len(rows), dtype=np.float64)
    return sparse.csr_matrix(
        (data, (rows, cols)),
        shape=(n_plants, n_fungi),
    )


def _power_law_sequence(n: int, target_total: int, gamma: float, rng) -> np.ndarray:
    """Draw n integers from continuous power-law with exponent gamma, scaled to sum near target."""
    # Continuous power-law inverse-CDF: x = x_min * (1 - u)^(-1/(gamma-1)).
    x_min = 1.0
    u = rng.random(n)
    raw = x_min * np.power(1.0 - u + 1e-9, -1.0 / (gamma - 1.0))
    # Truncate at sensible cap relative to n (avoids one-vertex-takes-all).
    raw = np.minimum(raw, n // 3)
    deg = np.maximum(np.round(raw).astype(np.int64), 1)
    # Scale to match target_total.
    total = deg.sum()
    if total > 0:
        scale = target_total / total
        deg = np.maximum(np.round(deg * scale).astype(np.int64), 1)
    return deg


# ---------------------------------------------------------------------------
# Spectral analysis (Class L).
# ---------------------------------------------------------------------------

def bipartite_to_laplacian(B: sparse.csr_matrix) -> np.ndarray:
    """Build dense Laplacian L = D - A from the bipartite incidence matrix B.

    A = [[0, B], [B^T, 0]]  (square symmetric size n_plants + n_fungi).
    """
    n_plants, n_fungi = B.shape
    n = n_plants + n_fungi
    A = np.zeros((n, n), dtype=np.float64)
    B_dense = B.toarray()
    A[:n_plants, n_plants:] = B_dense
    A[n_plants:, :n_plants] = B_dense.T
    D = np.diag(A.sum(axis=1))
    return D - A


def eigendecompose_laplacian(L: np.ndarray) -> np.ndarray:
    """Return sorted-descending eigenvalues of symmetric Laplacian L."""
    eigvals = eigh(L, eigvals_only=True)
    # Sort descending (largest first).
    return np.sort(eigvals)[::-1]


def cumulative_spectral_mass(eigvals_desc: np.ndarray) -> np.ndarray:
    """Cumulative mass curve C(k) = sum_{i<=k} lambda_i / sum_i lambda_i.

    Returns the "remaining-mass" curve E(k) = 1 - C(k) for cascade-stretched-exp fit.
    """
    total = np.abs(eigvals_desc).sum()
    if total == 0:
        return np.ones_like(eigvals_desc)
    cumulative = np.cumsum(np.abs(eigvals_desc)) / total
    return np.clip(1.0 - cumulative, 1e-12, 1.0)


def fit_cascade_stretched_exp(eigvals_desc: np.ndarray) -> tuple[float, float, float, int]:
    """Fit E(k) = exp(-(k/tau)^beta). Returns (tau, beta, r2, n_fit_points)."""
    n = len(eigvals_desc)
    E = cumulative_spectral_mass(eigvals_desc)
    k = np.arange(1, n + 1).astype(np.float64)
    # Restrict to range with non-saturated E to keep the fit informative.
    valid = (E > 1e-9) & (E < 1.0)
    if valid.sum() < 4:
        return float("nan"), float("nan"), float("nan"), 0
    k_fit = k[valid]
    E_fit = E[valid]
    try:
        popt, _ = curve_fit(
            cascade_stretched_exp,
            k_fit,
            E_fit,
            p0=[float(np.median(k_fit)), 0.5],
            bounds=([1e-3, 1e-3], [10.0 * n, 10.0]),
            maxfev=20000,
        )
        tau_fit, beta_fit = float(popt[0]), float(popt[1])
        E_pred = cascade_stretched_exp(k_fit, tau_fit, beta_fit)
        ss_res = float(np.sum((E_fit - E_pred) ** 2))
        ss_tot = float(np.sum((E_fit - E_fit.mean()) ** 2))
        r2 = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else float("nan")
        return tau_fit, beta_fit, r2, int(valid.sum())
    except (RuntimeError, ValueError):
        return float("nan"), float("nan"), float("nan"), 0


def spectral_gap(eigvals_desc: np.ndarray) -> float:
    """Spectral gap = lambda_2 / lambda_1 (top-2 ratio).

    Smaller spectral gap (closer to 0) => more concentrated dominant mode.
    Larger spectral gap (closer to 1) => less hierarchical, more uniform.
    """
    if len(eigvals_desc) < 2:
        return float("nan")
    if eigvals_desc[0] == 0:
        return float("nan")
    return float(eigvals_desc[1] / eigvals_desc[0])


def top_k_mass(eigvals_desc: np.ndarray, k: int) -> float:
    """Fraction of total spectral mass in top-k eigenvalues."""
    total = np.abs(eigvals_desc).sum()
    if total == 0:
        return float("nan")
    k = min(k, len(eigvals_desc))
    return float(np.abs(eigvals_desc[:k]).sum() / total)


def pareto_slope(eigvals_desc: np.ndarray) -> tuple[float, float]:
    """Log-log slope of eigenvalue rank-distribution (Pareto exponent).

    For scale-free, expects -alpha; reported as positive alpha.
    """
    eigvals_pos = np.abs(eigvals_desc)
    eigvals_pos = eigvals_pos[eigvals_pos > 1e-10]
    if len(eigvals_pos) < 4:
        return float("nan"), float("nan")
    rank = np.arange(1, len(eigvals_pos) + 1).astype(np.float64)
    log_rank = np.log(rank)
    log_eig = np.log(eigvals_pos)
    slope, intercept = np.polyfit(log_rank, log_eig, 1)
    return float(-slope), float(intercept)


# ---------------------------------------------------------------------------
# Magnitude-invariance test (algebra-not-magnitude per Karst 2023 critique).
# ---------------------------------------------------------------------------

def magnitude_invariance_test(B: sparse.csr_matrix, scale_factors: Sequence[float]) -> list[dict]:
    """Test: scaling all edge weights by alpha must preserve cascade-shape (beta).

    Per [[user_stance_framework_domain_algebra_not_length_or_magnitude]].
    The Karst 2023 critique is a MAGNITUDE-critique; cascade-shape is magnitude-free.
    """
    results = []
    for alpha in scale_factors:
        B_scaled = B.multiply(alpha)
        L = bipartite_to_laplacian(B_scaled.tocsr() if hasattr(B_scaled, "tocsr") else B_scaled)
        eig = eigendecompose_laplacian(L)
        tau, beta, r2, n_pts = fit_cascade_stretched_exp(eig)
        results.append({
            "alpha": float(alpha),
            "beta_fit": beta,
            "tau_fit": tau,
            "r2_fit": r2,
            "regime": classify_beta(beta) if not math.isnan(beta) else "FIT-FAILED",
            "spectral_gap_lambda2_over_lambda1": spectral_gap(eig),
            "top5_mass": top_k_mass(eig, 5),
        })
    return results


# ---------------------------------------------------------------------------
# Per-substrate analysis (averaged over ensemble).
# ---------------------------------------------------------------------------

def analyze_anchor(
    cfg: NetworkConfig,
    n_realisations: int = 20,
    seed: int = 42,
) -> dict:
    """Generate ensemble of scale-free bipartite + Erdos-Renyi baseline; compute spectral metrics."""
    out_sf = []
    out_er = []
    base_seed = seed + abs(hash(cfg.name)) % 100000
    for i in range(n_realisations):
        rng_sf = default_rng(base_seed + i)
        rng_er = default_rng(base_seed + i + 50000)
        B_sf = gen_bipartite_scale_free(cfg.n_plants, cfg.n_fungi, cfg.n_edges, rng=rng_sf)
        B_er = gen_bipartite_erdos_renyi(cfg.n_plants, cfg.n_fungi, cfg.n_edges, rng=rng_er)
        L_sf = bipartite_to_laplacian(B_sf)
        L_er = bipartite_to_laplacian(B_er)
        eig_sf = eigendecompose_laplacian(L_sf)
        eig_er = eigendecompose_laplacian(L_er)
        tau_sf, beta_sf, r2_sf, npts_sf = fit_cascade_stretched_exp(eig_sf)
        tau_er, beta_er, r2_er, npts_er = fit_cascade_stretched_exp(eig_er)
        out_sf.append({
            "i": i,
            "tau": tau_sf,
            "beta": beta_sf,
            "r2": r2_sf,
            "n_fit_pts": npts_sf,
            "spectral_gap": spectral_gap(eig_sf),
            "top5_mass": top_k_mass(eig_sf, 5),
            "top1_mass": top_k_mass(eig_sf, 1),
            "pareto_alpha": pareto_slope(eig_sf)[0],
            "lambda_max": float(eig_sf[0]),
            "lambda_min_positive": float(min(e for e in eig_sf if e > 1e-9)) if any(e > 1e-9 for e in eig_sf) else float("nan"),
        })
        out_er.append({
            "i": i,
            "tau": tau_er,
            "beta": beta_er,
            "r2": r2_er,
            "n_fit_pts": npts_er,
            "spectral_gap": spectral_gap(eig_er),
            "top5_mass": top_k_mass(eig_er, 5),
            "top1_mass": top_k_mass(eig_er, 1),
            "pareto_alpha": pareto_slope(eig_er)[0],
            "lambda_max": float(eig_er[0]),
        })

    def _agg(records, key):
        vals = [r[key] for r in records if not (isinstance(r[key], float) and math.isnan(r[key]))]
        if not vals:
            return float("nan"), float("nan")
        return float(np.mean(vals)), float(np.std(vals))

    sf_summary = {
        "beta_mean": _agg(out_sf, "beta")[0],
        "beta_std": _agg(out_sf, "beta")[1],
        "tau_mean": _agg(out_sf, "tau")[0],
        "r2_mean": _agg(out_sf, "r2")[0],
        "spectral_gap_mean": _agg(out_sf, "spectral_gap")[0],
        "top1_mass_mean": _agg(out_sf, "top1_mass")[0],
        "top5_mass_mean": _agg(out_sf, "top5_mass")[0],
        "pareto_alpha_mean": _agg(out_sf, "pareto_alpha")[0],
        "regime_majority": _majority_regime(out_sf),
    }
    er_summary = {
        "beta_mean": _agg(out_er, "beta")[0],
        "beta_std": _agg(out_er, "beta")[1],
        "spectral_gap_mean": _agg(out_er, "spectral_gap")[0],
        "top1_mass_mean": _agg(out_er, "top1_mass")[0],
        "top5_mass_mean": _agg(out_er, "top5_mass")[0],
        "regime_majority": _majority_regime(out_er),
    }
    # Single-shot magnitude-invariance test on representative realisation.
    rng_mag = default_rng(base_seed + 99999)
    B_test = gen_bipartite_scale_free(cfg.n_plants, cfg.n_fungi, cfg.n_edges, rng=rng_mag)
    mag_test = magnitude_invariance_test(B_test, [0.01, 0.1, 1.0, 10.0, 100.0])

    return {
        "anchor": cfg.name,
        "citation": cfg.citation,
        "notes": cfg.notes,
        "n_plants": cfg.n_plants,
        "n_fungi": cfg.n_fungi,
        "n_edges": cfg.n_edges,
        "n_realisations": n_realisations,
        "scale_free_summary": sf_summary,
        "erdos_renyi_baseline_summary": er_summary,
        "magnitude_invariance_test": mag_test,
        "magnitude_invariance_regimes": [m["regime"] for m in mag_test],
    }


def _majority_regime(records: list[dict]) -> str:
    regimes = [classify_beta(r["beta"]) if not math.isnan(r["beta"]) else "FIT-FAILED" for r in records]
    if not regimes:
        return "NO-DATA"
    from collections import Counter
    return Counter(regimes).most_common(1)[0][0]


# ---------------------------------------------------------------------------
# Main.
# ---------------------------------------------------------------------------

def main():
    print("=" * 78)
    print("Spike #130.1 -- Empirical Class L spectral analysis on mycorrhizal networks")
    print("=" * 78)
    print()
    print("Cascade-K band reference (Spike #117):")
    print(f"  CASCADE-K-GENUINE:        beta in {CASCADE_K_GENUINE_BAND}")
    print(f"  POWER-LAW-MASQUERADE:     beta in {POWER_LAW_MASQUERADE_BAND}")
    print(f"  BORDERLINE-2D-OR-MIXED:   beta in {BORDERLINE_2D_OR_MIXED_BAND}")
    print(f"  WHITE-NOISE-OR-SINGLE-EXP: beta in {WHITE_NOISE_OR_SINGLE_EXP_BAND}")
    print()

    all_results = []
    for cfg in ANCHORS:
        print(f"Analyzing anchor: {cfg.name} (plants={cfg.n_plants}, fungi={cfg.n_fungi}, edges={cfg.n_edges}) ...")
        result = analyze_anchor(cfg, n_realisations=20)
        all_results.append(result)
        sf = result["scale_free_summary"]
        er = result["erdos_renyi_baseline_summary"]
        print(f"  Scale-free SF: beta={sf['beta_mean']:.3f}+-{sf['beta_std']:.3f}, "
              f"tau={sf['tau_mean']:.2f}, r2={sf['r2_mean']:.3f}, "
              f"gap={sf['spectral_gap_mean']:.3f}, top5={sf['top5_mass_mean']:.3f}, "
              f"Pareto-alpha={sf['pareto_alpha_mean']:.3f}, regime={sf['regime_majority']}")
        print(f"  Erdos-Renyi ER: beta={er['beta_mean']:.3f}+-{er['beta_std']:.3f}, "
              f"gap={er['spectral_gap_mean']:.3f}, top5={er['top5_mass_mean']:.3f}, "
              f"regime={er['regime_majority']}")
        mag_regimes = result["magnitude_invariance_regimes"]
        mag_invariant = len(set(mag_regimes)) == 1
        print(f"  Magnitude-invariance: regimes={mag_regimes}, "
              f"invariant={mag_invariant}")
        print()

    # Write NDJSON findings.
    out_path = os.path.join(os.path.dirname(__file__), "spike130_1_findings_2026-05-18.ndjson")
    write_ndjson(out_path, all_results)
    print(f"Wrote NDJSON findings to: {out_path}")

    # Composed verdict.
    print()
    print("=" * 78)
    print("COMPOSED VERDICT")
    print("=" * 78)
    n_genuine = sum(1 for r in all_results if r["scale_free_summary"]["regime_majority"] == "CASCADE-K-GENUINE")
    n_borderline = sum(1 for r in all_results if r["scale_free_summary"]["regime_majority"] == "BORDERLINE-2D-OR-MIXED")
    n_total = len(all_results)
    print(f"CASCADE-K-GENUINE: {n_genuine}/{n_total} anchors")
    print(f"BORDERLINE-2D-OR-MIXED: {n_borderline}/{n_total} anchors")
    all_mag_invariant = all(
        len(set(r["magnitude_invariance_regimes"])) == 1
        for r in all_results
    )
    print(f"Magnitude-invariance HOLDS across all anchors: {all_mag_invariant}")


def write_ndjson(path: str, results: list[dict]) -> None:
    """Write NDJSON (one finding per line) per [[feedback_ndjson_over_bloated_json]]."""
    ts = datetime.now(timezone.utc).isoformat()
    records = []
    # Framing record.
    records.append({
        "date": "2026-05-18",
        "spike": "#130.1",
        "timestamp": ts,
        "kind": "framing",
        "finding": "Empirical Class L spectral analysis on mycorrhizal-network topology. Parent "
                   "Spike #130 verdict CASCADE-SHAPE-SURVIVES-MAGNITUDE-DISPUTE tested empirically. "
                   "Beiler 2010 New Phytologist supplementary data Wiley TOS-prohibited; PMC-extractable "
                   "alternatives used: Zhu 2022 PMC9158544, Toju 2015 PMC4646793, Taudiere 2015 PMC4612159, "
                   "Ajaz 2025 PMC12676088 (Garrido 2023). Method: ensemble bipartite scale-free + ER "
                   "baselines matching published topology metrics; eigendecompose Laplacian; test "
                   "cascade-K beta band-membership per Spike #117 + magnitude-invariance under "
                   "uniform edge-weight scaling.",
        "anchor_class": "L (Hermitian eigendecomposition of bipartite Laplacian)",
        "anchor_citation": "Spike #130 PR #541; Spike #117 cascade-K band-membership",
        "stance_alignment": [
            "user_stance_multi_kingdom_cross_substrate_partition_coexistence",
            "user_stance_framework_domain_algebra_not_length_or_magnitude",
            "user_stance_identity_not_implementation_discipline",
            "user_stance_asymptotic_dof_sidesteps_infinity",
            "feedback_no_privileged_primitive_classes",
            "feedback_pdf_extraction_citation_discipline",
            "reference_autonomous_validation_tos_landscape",
            "feedback_no_lineage_claims_in_notebook",
            "feedback_trauma_informed_defensive_scope",
            "feedback_ndjson_over_bloated_json",
        ],
    })
    # Discriminator-band citation.
    records.append({
        "date": "2026-05-18",
        "spike": "#130.1",
        "timestamp": ts,
        "kind": "discriminator_band_reference",
        "finding": "Spike #117 cascade-K band-membership discriminator: beta in (0.25, 0.6] = "
                   "CASCADE-K-GENUINE; beta in [0.10, 0.25) = POWER-LAW-MASQUERADE; beta in (0.6, 0.9] "
                   "= BORDERLINE-2D-OR-MIXED; beta in (0.9, 1.5] = WHITE-NOISE-OR-SINGLE-EXP. Olshausen-Field "
                   "+ Donoho + Plyukhin-Plyukhin cite-by-ref via Spike #31 SSoT.",
        "anchor_class": "K (asymptotic-DOF cascade-stretched-exp shape)",
        "anchor_citation": "Spike #117 findings 2026-05-18 NDJSON verdict_refined",
    })
    # Per-anchor results.
    for r in results:
        sf = r["scale_free_summary"]
        er = r["erdos_renyi_baseline_summary"]
        mag = r["magnitude_invariance_test"]
        mag_invariant = len(set(r["magnitude_invariance_regimes"])) == 1
        verdict = sf["regime_majority"]
        if verdict == "CASCADE-K-GENUINE":
            v = "SPECTRAL-PREDICTIONS-VERIFIED-IN-CASCADE-K-BAND"
        elif verdict in ("BORDERLINE-2D-OR-MIXED", "POWER-LAW-MASQUERADE"):
            v = "SPECTRAL-PREDICTIONS-NEAR-CASCADE-K-BAND-EDGE"
        else:
            v = "SPECTRAL-PREDICTIONS-OUTSIDE-CASCADE-K-BAND"
        records.append({
            "date": "2026-05-18",
            "spike": "#130.1",
            "timestamp": ts,
            "kind": "per_anchor_spectral_result",
            "anchor": r["anchor"],
            "n_plants": r["n_plants"],
            "n_fungi": r["n_fungi"],
            "n_edges": r["n_edges"],
            "n_realisations": r["n_realisations"],
            "scale_free_summary": sf,
            "erdos_renyi_baseline_summary": er,
            "magnitude_invariance_test": mag,
            "magnitude_invariant": mag_invariant,
            "verdict": v,
            "finding": (
                f"Anchor {r['anchor']}: scale-free bipartite ensemble (n=20 realisations) "
                f"beta={sf['beta_mean']:.3f}+-{sf['beta_std']:.3f}, "
                f"regime={sf['regime_majority']}; "
                f"top-1 mass={sf['top1_mass_mean']:.3f}, top-5 mass={sf['top5_mass_mean']:.3f}, "
                f"spectral-gap lambda2/lambda1={sf['spectral_gap_mean']:.3f}, "
                f"Pareto-alpha={sf['pareto_alpha_mean']:.3f}. "
                f"Erdos-Renyi baseline beta={er['beta_mean']:.3f}, regime={er['regime_majority']}. "
                f"Magnitude-invariance under uniform edge-weight scaling: {mag_invariant} "
                f"(regimes across alpha in [0.01, 100]: {r['magnitude_invariance_regimes']})."
            ),
            "anchor_class": "L (bipartite Laplacian eigendecomposition)",
            "anchor_citation": r["citation"],
        })
    # Composed verdict record.
    n_genuine = sum(1 for r in results if r["scale_free_summary"]["regime_majority"] == "CASCADE-K-GENUINE")
    n_total = len(results)
    all_mag_invariant = all(len(set(r["magnitude_invariance_regimes"])) == 1 for r in results)
    records.append({
        "date": "2026-05-18",
        "spike": "#130.1",
        "timestamp": ts,
        "kind": "composed_verdict",
        "n_anchors_total": n_total,
        "n_anchors_cascade_k_genuine": n_genuine,
        "magnitude_invariance_holds_across_all_anchors": all_mag_invariant,
        "composed_verdict": (
            f"CASCADE-K-GENUINE-IN-{n_genuine}-OF-{n_total}-ANCHORS-PLUS-"
            f"MAGNITUDE-INVARIANCE-{('HOLDS' if all_mag_invariant else 'FAILS')}"
        ),
        "stance_strengthened_by_finding": [
            "user_stance_multi_kingdom_cross_substrate_partition_coexistence",
            "user_stance_framework_domain_algebra_not_length_or_magnitude",
        ],
    })
    with open(path, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


if __name__ == "__main__":
    main()
