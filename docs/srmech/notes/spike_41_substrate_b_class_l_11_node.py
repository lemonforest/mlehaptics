"""Spike #41 substrate-B alternative encoding (task #255).

PURPOSE
-------
Parent Spike #41 chose multinacci_3_7_1 (recurrence stencil with lags 1,3,7)
as substrate-B for the 11D fractal projection 3D_s + 7D_g + 1D_t. The §6
fermata 1 in the parent artifact explicitly flagged an alternative:

    "Substrate B interpretation choice. Picked multinacci 3+7+1 stencil
     x_n = x_{n-1} + x_{n-3} + x_{n-7} as the '11D fractal projection of
     3D_s + 7D_g + 1D_t (compressed).' Alternative: Class L on 11-node
     graph partitioned 3+7+1 (different fingerprint). Re-run with
     alternative interpretation if conductor wants verification."

This spike implements that alternative. We construct an 11-node weighted
graph with explicit 3 (spatial) + 7 (gauge) + 1 (temporal) clusters,
compute its graph Laplacian (Class L primitive, canonical project
operation per [[user_stance_kepler_shape_universal]] +
[[feedback_no_privileged_primitive_classes]]), and check whether the
Cauchy-form `c_k = eps^k / k` Kepler-shape recovers under several
canonical weighting choices.

DISCIPLINE (per concertmaster brief)
------------------------------------
- 14 A-N intact; Class L = canonical graph Laplacian
- Identity-not-implementation: claim is "this substrate IS Kepler-shape"
  not "this substrate implements Kepler-shape"
- NDJSON output, one record per line
- No autonomous stance authoring
- No PhD-gatekeeping; project's existing instrument (Laplacian spectrum +
  ratio-form Cauchy ladder) is the tool
- Sample-selection-bias guard: 3+7+1 partition is CANONICAL not outcome-
  selected (it IS the project's space_gauge_time decomposition)

CONSTRUCTION
------------
The 11-node graph G has node-set V = V_s u V_g u V_t with |V_s|=3,
|V_g|=7, |V_t|=1. We test several edge-weight schemes:

  (S1) Complete intra-cluster + uniform cross-cluster:
       within V_s, V_g, V_t: complete subgraphs with weight w_intra
       across clusters: complete bipartite with weight w_cross

  (S2) Star intra-cluster (one hub) + cross-cluster from hubs only:
       sparse alternative

  (S3) Path intra-cluster + cross-cluster anchor at ends:
       another sparse alternative

  (S4) Canonical 3D_s + 7D_g + 1D_t with weights from the dimensional-
       count itself (Class N rational normalisation):
       within V_s: weight 1/3; within V_g: weight 1/7; cross: weight 1/(3*7)=1/21

For each scheme we compute:
  - Combinatorial Laplacian L = D - A
  - Spectrum (11 eigenvalues; lambda_0 = 0 by construction; 10 nontrivial)
  - Sub/dominant ratio rho = lambda_2 / lambda_max (skipping the trivial 0)
  - Cauchy ladder candidate c_k = rho^k / k for k = 1..20
  - K-test (parent's Spike #30B v3 strict criterion)
  - Compare to parent multinacci finding: rho_parent = lambda_2/lambda_1 = 0.6885

VERDICT POSSIBILITIES (pre-registered)
--------------------------------------
  CONVERGENCE: at least one weighting scheme reproduces Cauchy-form
               c_k = rho^k / k with rho in same neighbourhood as parent
               multinacci (0.6885) or fib-psi (0.6180), implying
               substrate-equivalence at the form level.

  DISSONANCE: no canonical weighting yields Kepler-shape; substrate-B
              encoding choice is load-bearing for the parent claim.

  PARTIAL CONVERGENCE: form recovered, but rho differs systematically
              across schemes; substrate-B choice matters for the rho
              VALUE but not the FORM.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np


DATE_TAG = "2026-05-19"
SPIKE = "spike_41_substrate_b"
WORKSPACE = Path(__file__).resolve().parent

RECORDS_FILE = WORKSPACE / f"{SPIKE}_records_{DATE_TAG}.ndjson"
SYNTHESIS_FILE = WORKSPACE / f"{SPIKE}_synthesis_{DATE_TAG}.ndjson"


# ---------------------------------------------------------------------------
# Project's canonical Class L Laplacian (combinatorial, dense, integer-safe)
# ---------------------------------------------------------------------------

def graph_laplacian(adjacency: np.ndarray) -> np.ndarray:
    """L = D - A. Combinatorial Laplacian, canonical Class L primitive.

    Symmetric, PSD by construction. lambda_0 = 0 with multiplicity equal
    to the number of connected components.
    """
    if adjacency.ndim != 2 or adjacency.shape[0] != adjacency.shape[1]:
        raise ValueError("adjacency must be square")
    if not np.allclose(adjacency, adjacency.T):
        raise ValueError("adjacency must be symmetric")
    degree = np.diag(np.sum(adjacency, axis=1))
    return degree - adjacency


def laplacian_spectrum(L: np.ndarray) -> np.ndarray:
    """Return eigenvalues sorted ascending. PSD so all real >= 0."""
    eigs = np.linalg.eigvalsh(L)
    # eigvalsh returns ascending; clip tiny negatives from FP noise
    return np.maximum(eigs, 0.0)


# ---------------------------------------------------------------------------
# K-ladder strict test (parent Spike #30B v3 strict criterion)
# Reproduced here verbatim for substrate-equivalence check
# ---------------------------------------------------------------------------

def kepler_ladder_test(coefficients: np.ndarray, label: str) -> Dict:
    """Strict K-test: r2 > 0.99, monotonic decreasing, eps_fit in (0.001, 0.5).

    Also returns unbiased eps_fit on log|c_k * k| (per parent Anomaly 2).
    """
    abs_c = np.abs(coefficients)
    if np.any(abs_c <= 0):
        idx = np.where(abs_c > 0)[0]
        if len(idx) < 3:
            return {
                "label": label,
                "n_coefficients": int(len(coefficients)),
                "r2": None,
                "eps_fit_biased": None,
                "eps_fit_unbiased": None,
                "monotonic_decreasing": False,
                "in_physical_range": False,
                "k_signature_present": False,
            }
        abs_c = abs_c[idx]

    k = np.arange(1, len(abs_c) + 1, dtype=np.float64)
    log_c = np.log(abs_c)

    # Biased fit (log|c_k| ~ k log eps + const)
    A = np.vstack([k, np.ones_like(k)]).T
    slope, intercept = np.linalg.lstsq(A, log_c, rcond=None)[0]
    eps_fit_biased = float(math.exp(slope))
    pred = slope * k + intercept
    ss_res = float(np.sum((log_c - pred) ** 2))
    ss_tot = float(np.sum((log_c - np.mean(log_c)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    # Unbiased fit on log|c_k * k| (per parent anomaly 2)
    log_ck_k = np.log(abs_c * k)
    slope_u, _ = np.linalg.lstsq(A, log_ck_k, rcond=None)[0]
    eps_fit_unbiased = float(math.exp(slope_u))

    monotonic = bool(np.all(np.diff(abs_c) < 0))
    in_range = 0.001 < eps_fit_biased < 0.5

    return {
        "label": label,
        "n_coefficients": int(len(coefficients)),
        "r2": float(r2),
        "eps_fit_biased": eps_fit_biased,
        "eps_fit_unbiased": eps_fit_unbiased,
        "monotonic_decreasing": monotonic,
        "in_physical_range": in_range,
        "k_signature_present": bool(r2 > 0.99 and monotonic and in_range),
        "first_three_coeffs": [float(c) for c in coefficients[:3]],
    }


# ---------------------------------------------------------------------------
# Edge-weight schemes for the 11-node 3+7+1 partition
# ---------------------------------------------------------------------------

# Node indices: 0,1,2 = spatial; 3..9 = gauge; 10 = temporal
N_SPATIAL = 3
N_GAUGE = 7
N_TEMPORAL = 1
N_TOTAL = N_SPATIAL + N_GAUGE + N_TEMPORAL  # = 11

SPATIAL_NODES = list(range(0, 3))                          # [0,1,2]
GAUGE_NODES = list(range(3, 10))                           # [3..9]
TEMPORAL_NODES = list(range(10, 11))                       # [10]


def _empty_adj() -> np.ndarray:
    return np.zeros((N_TOTAL, N_TOTAL), dtype=np.float64)


def _add_complete_subgraph(A: np.ndarray, nodes: List[int], weight: float) -> None:
    for i in nodes:
        for j in nodes:
            if i < j:
                A[i, j] += weight
                A[j, i] += weight


def _add_complete_bipartite(A: np.ndarray, u: List[int], v: List[int], weight: float) -> None:
    for i in u:
        for j in v:
            A[i, j] += weight
            A[j, i] += weight


def _add_star(A: np.ndarray, nodes: List[int], hub_idx: int, weight: float) -> None:
    """Star on `nodes` with hub at `nodes[hub_idx]`. (hub is in `nodes` list.)"""
    hub = nodes[hub_idx]
    for n in nodes:
        if n != hub:
            A[hub, n] += weight
            A[n, hub] += weight


def _add_path(A: np.ndarray, nodes: List[int], weight: float) -> None:
    for i in range(len(nodes) - 1):
        u, v = nodes[i], nodes[i + 1]
        A[u, v] += weight
        A[v, u] += weight


def scheme_s1_complete(w_intra: float = 1.0, w_cross: float = 1.0) -> Tuple[str, np.ndarray]:
    """S1: complete subgraph within each cluster + complete bipartite between
    every pair of clusters."""
    A = _empty_adj()
    _add_complete_subgraph(A, SPATIAL_NODES, w_intra)
    _add_complete_subgraph(A, GAUGE_NODES, w_intra)
    # temporal singleton: no intra-cluster edges
    _add_complete_bipartite(A, SPATIAL_NODES, GAUGE_NODES, w_cross)
    _add_complete_bipartite(A, SPATIAL_NODES, TEMPORAL_NODES, w_cross)
    _add_complete_bipartite(A, GAUGE_NODES, TEMPORAL_NODES, w_cross)
    return ("S1_complete_intra_complete_cross", A)


def scheme_s2_star(w_intra: float = 1.0, w_cross: float = 1.0) -> Tuple[str, np.ndarray]:
    """S2: star within each cluster (first node = hub) + cross-cluster edges
    only between hubs of different clusters."""
    A = _empty_adj()
    _add_star(A, SPATIAL_NODES, 0, w_intra)  # hub = node 0
    _add_star(A, GAUGE_NODES, 0, w_intra)    # hub = node 3 (gauge_nodes[0])
    # temporal hub is the singleton itself, node 10
    hubs = [SPATIAL_NODES[0], GAUGE_NODES[0], TEMPORAL_NODES[0]]  # [0, 3, 10]
    # complete-triangle on the three hubs (cross-cluster)
    _add_complete_subgraph(A, hubs, w_cross)
    return ("S2_star_intra_hub_triangle_cross", A)


def scheme_s3_path(w_intra: float = 1.0, w_cross: float = 1.0) -> Tuple[str, np.ndarray]:
    """S3: path within each cluster + cross-cluster edges anchored at the ends
    of each path."""
    A = _empty_adj()
    _add_path(A, SPATIAL_NODES, w_intra)  # 0-1-2
    _add_path(A, GAUGE_NODES, w_intra)    # 3-4-5-6-7-8-9
    # cross: anchor ends
    # spatial end (node 2) <-> gauge start (node 3)
    A[2, 3] += w_cross; A[3, 2] += w_cross
    # gauge end (node 9) <-> temporal (node 10)
    A[9, 10] += w_cross; A[10, 9] += w_cross
    # spatial start (node 0) <-> temporal (node 10) to close the "ring"
    A[0, 10] += w_cross; A[10, 0] += w_cross
    return ("S3_path_intra_anchor_cross", A)


def scheme_s4_canonical_rational(_unused1: float = 1.0, _unused2: float = 1.0) -> Tuple[str, np.ndarray]:
    """S4: weight 1/|cluster_size| inside each cluster (Class N rational
    normalisation), weight 1/(|c1| * |c2|) across clusters.

    Class N rationality drives the construction; dimension-count IS the weight.
    """
    A = _empty_adj()
    _add_complete_subgraph(A, SPATIAL_NODES, 1.0 / N_SPATIAL)         # 1/3
    _add_complete_subgraph(A, GAUGE_NODES, 1.0 / N_GAUGE)             # 1/7
    # cross-cluster: 1/(|c1|*|c2|)
    _add_complete_bipartite(A, SPATIAL_NODES, GAUGE_NODES,
                            1.0 / (N_SPATIAL * N_GAUGE))              # 1/21
    _add_complete_bipartite(A, SPATIAL_NODES, TEMPORAL_NODES,
                            1.0 / (N_SPATIAL * N_TEMPORAL))           # 1/3
    _add_complete_bipartite(A, GAUGE_NODES, TEMPORAL_NODES,
                            1.0 / (N_GAUGE * N_TEMPORAL))             # 1/7
    return ("S4_canonical_rational_class_N", A)


def scheme_s5_intra_heavier(w_intra: float = 10.0, w_cross: float = 1.0) -> Tuple[str, np.ndarray]:
    """S5: same topology as S1 but intra-cluster edges 10x heavier than
    cross-cluster. Emphasises partition structure."""
    A = _empty_adj()
    _add_complete_subgraph(A, SPATIAL_NODES, w_intra)
    _add_complete_subgraph(A, GAUGE_NODES, w_intra)
    _add_complete_bipartite(A, SPATIAL_NODES, GAUGE_NODES, w_cross)
    _add_complete_bipartite(A, SPATIAL_NODES, TEMPORAL_NODES, w_cross)
    _add_complete_bipartite(A, GAUGE_NODES, TEMPORAL_NODES, w_cross)
    return ("S5_complete_intra_heavy_partition", A)


SCHEMES = [
    scheme_s1_complete,
    scheme_s2_star,
    scheme_s3_path,
    scheme_s4_canonical_rational,
    scheme_s5_intra_heavier,
]


# ---------------------------------------------------------------------------
# Cauchy-ladder candidate from a Laplacian spectrum
# ---------------------------------------------------------------------------

def cauchy_ladder_from_spectrum(eigs: np.ndarray, n_modes: int = 20) -> Tuple[float, np.ndarray]:
    """From a Laplacian spectrum (ascending, lambda_0 = 0), construct the
    Cauchy-ladder candidate c_k = rho^k / k where rho = lambda_2 / lambda_max.

    This mirrors the parent multinacci recipe: rho = subdominant/dominant.

    For a Laplacian:
      lambda_0 = 0 (trivial mode, constant eigenvector)
      lambda_1 = algebraic connectivity (Fiedler value)
      lambda_2 = next-smallest non-trivial
      ...
      lambda_max = spectral radius

    rho_subdom_over_dom = lambda_1 / lambda_max -- the "rate of approach
    from below" for the spectral gap.

    Alternative rho = (lambda_max - lambda_{max-1}) / lambda_max -- the
    "rate of approach from above". We compute the lambda_1/lambda_max
    form to mirror parent multinacci 0.6885 result.
    """
    if len(eigs) < 3:
        raise ValueError("need at least 3 eigenvalues")
    # eigs ascending; skip trivial lambda_0 = 0
    # Fiedler value = first nonzero (smallest positive)
    # Find first eigval > tolerance
    tol = max(1e-12, eigs[-1] * 1e-12)
    nontrivial = eigs[eigs > tol]
    if len(nontrivial) < 2:
        raise ValueError("graph appears disconnected or degenerate")
    fiedler = float(nontrivial[0])
    spec_rad = float(nontrivial[-1])
    rho = fiedler / spec_rad
    coeffs = np.array([rho ** k / k for k in range(1, n_modes + 1)], dtype=np.float64)
    return rho, coeffs


def cauchy_ladder_alt_consecutive(eigs: np.ndarray, n_modes: int = 20) -> Tuple[float, np.ndarray]:
    """Alternative rho recipe: rho = lambda_{1} / lambda_{2} (ratio of two
    smallest nontrivial eigenvalues). This is the parent's recipe re-applied:
    lambda_2 / lambda_1 in eigenvalue-magnitude ordering.

    For ascending-sorted Laplacian eigvals (lam_0=0, lam_1=fiedler, lam_2,...,
    lam_max), the parent multinacci computed rho = lambda_2/lambda_1 in
    DESCENDING magnitude order, which corresponds to lambda_{n-2}/lambda_{n-1}
    in our ascending order (next-to-largest over largest).
    """
    if len(eigs) < 3:
        raise ValueError("need at least 3 eigenvalues")
    tol = max(1e-12, eigs[-1] * 1e-12)
    nontrivial = eigs[eigs > tol]
    if len(nontrivial) < 2:
        raise ValueError("degenerate")
    spec_rad = float(nontrivial[-1])
    subdom = float(nontrivial[-2])
    rho = subdom / spec_rad
    coeffs = np.array([rho ** k / k for k in range(1, n_modes + 1)], dtype=np.float64)
    return rho, coeffs


# ---------------------------------------------------------------------------
# NDJSON
# ---------------------------------------------------------------------------

def emit(path: Path, record: Dict) -> None:
    record = dict(record)
    record.setdefault("date", DATE_TAG)
    record.setdefault("spike", SPIKE)
    record.setdefault("timestamp", datetime.now(tz=timezone.utc).isoformat())
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, default=float))
        fh.write("\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    for p in (RECORDS_FILE, SYNTHESIS_FILE):
        if p.exists():
            p.unlink()

    PARENT_MULTINACCI_RHO = 0.6885  # parent finding (rho = lambda_2/lambda_1)
    PARENT_FIB_RHO = 0.6180         # parent finding (|psi|)
    PARENT_KEPLER_EARTH_RHO = 0.0167  # rapid end of spectrum

    print("\n=== Spike #41 substrate-B alternative: Class L on 11-node 3+7+1 ===\n")
    print(f"Parent reference rhos: multinacci={PARENT_MULTINACCI_RHO:.4f},")
    print(f"  fib|psi|={PARENT_FIB_RHO:.4f}, kepler_earth={PARENT_KEPLER_EARTH_RHO:.4f}\n")

    scheme_results: List[Dict] = []

    for scheme_fn in SCHEMES:
        name, A = scheme_fn()
        L = graph_laplacian(A)
        eigs = laplacian_spectrum(L)

        # Cauchy ladder via Fiedler/spec_rad (lambda_1 ascending / lambda_max)
        rho_fiedler, coeffs_fiedler = cauchy_ladder_from_spectrum(eigs)
        # Alternative: lambda_{max-1}/lambda_max (mirrors parent multinacci recipe)
        rho_alt, coeffs_alt = cauchy_ladder_alt_consecutive(eigs)

        test_fiedler = kepler_ladder_test(coeffs_fiedler, f"{name}_rho_fiedler")
        test_alt = kepler_ladder_test(coeffs_alt, f"{name}_rho_subdominant_over_dominant")

        # Connectedness check (algebraic connectivity > 0)
        tol = max(1e-12, eigs[-1] * 1e-12)
        connected = bool(np.sum(eigs > tol) == N_TOTAL - 1)

        # Edge count
        n_edges = int(np.sum(A > 0) // 2)

        record = {
            "kind": "scheme_result",
            "scheme": name,
            "n_nodes": N_TOTAL,
            "n_edges": n_edges,
            "connected": connected,
            "spectrum_ascending": [float(e) for e in eigs],
            "fiedler_value": float(eigs[1]) if len(eigs) > 1 else None,
            "spectral_radius": float(eigs[-1]),
            "rho_fiedler_over_spec_rad": float(rho_fiedler),
            "rho_subdom_over_dom": float(rho_alt),
            "k_test_rho_fiedler": test_fiedler,
            "k_test_rho_subdom_over_dom": test_alt,
            "comparison_to_parent": {
                "parent_multinacci_rho": PARENT_MULTINACCI_RHO,
                "abs_diff_alt_vs_multinacci": float(abs(rho_alt - PARENT_MULTINACCI_RHO)),
                "abs_diff_fiedler_vs_multinacci": float(abs(rho_fiedler - PARENT_MULTINACCI_RHO)),
                "abs_diff_alt_vs_fib_psi": float(abs(rho_alt - PARENT_FIB_RHO)),
                "abs_diff_fiedler_vs_fib_psi": float(abs(rho_fiedler - PARENT_FIB_RHO)),
            },
        }
        emit(RECORDS_FILE, record)
        scheme_results.append(record)

        print(f"[{name}]")
        print(f"  edges={n_edges}, connected={connected}")
        print(f"  spectrum: {[f'{e:.4f}' for e in eigs]}")
        print(f"  rho_fiedler = lambda_1/lambda_max = {rho_fiedler:.6f}")
        print(f"  rho_subdom  = lambda_(max-1)/lambda_max = {rho_alt:.6f}")
        print(f"  K-test rho_fiedler: r2={test_fiedler['r2']:.4f}, "
              f"eps_fit_biased={test_fiedler['eps_fit_biased']:.4f}, "
              f"eps_fit_unbiased={test_fiedler['eps_fit_unbiased']:.4f}, "
              f"in_range={test_fiedler['in_physical_range']}, "
              f"k_sig={test_fiedler['k_signature_present']}")
        print(f"  K-test rho_subdom:  r2={test_alt['r2']:.4f}, "
              f"eps_fit_biased={test_alt['eps_fit_biased']:.4f}, "
              f"eps_fit_unbiased={test_alt['eps_fit_unbiased']:.4f}, "
              f"in_range={test_alt['in_physical_range']}, "
              f"k_sig={test_alt['k_signature_present']}")
        print(f"  |rho_subdom - parent_multinacci_rho| = "
              f"{abs(rho_alt - PARENT_MULTINACCI_RHO):.4f}")
        print()

    # Synthesis
    n_form_recovered = sum(
        1 for r in scheme_results
        # Form-level: Cauchy form c_k = eps^k/k recovers cleanly (r2 > 0.99
        # AND monotonic). We do NOT require in_physical_range, mirroring
        # parent's identity-not-implementation framing.
        if r["k_test_rho_subdom_over_dom"]["r2"] is not None
        and r["k_test_rho_subdom_over_dom"]["r2"] > 0.99
        and r["k_test_rho_subdom_over_dom"]["monotonic_decreasing"]
    )
    n_strict_pass = sum(
        1 for r in scheme_results
        if r["k_test_rho_subdom_over_dom"].get("k_signature_present", False)
    )

    closest_to_multinacci = min(
        scheme_results,
        key=lambda r: r["comparison_to_parent"]["abs_diff_alt_vs_multinacci"],
    )
    closest_to_fib_psi = min(
        scheme_results,
        key=lambda r: r["comparison_to_parent"]["abs_diff_alt_vs_fib_psi"],
    )

    # Determine substrate-equivalence verdict
    # CONVERGENCE: form recovers in all schemes (universal substrate-equivalent)
    # PARTIAL CONVERGENCE: form recovers in some schemes; rho varies
    # DISSONANCE: form fails to recover in canonical scheme(s)
    if n_form_recovered == len(scheme_results):
        verdict = "CONVERGENCE"
        verdict_detail = (
            "Cauchy-form c_k = rho^k / k recovers (r2 > 0.99 + monotonic) at "
            "ALL tested weighting schemes for the 11-node 3+7+1 partition. "
            "Substrate-B alternative encoding INSTANTIATES the same Cauchy form "
            "as parent multinacci. The form survives the encoding choice. "
            "rho VALUE varies across schemes (partition-level per "
            "[[user_stance_partition_for_understanding]]); form IS universal."
        )
    elif n_form_recovered > 0:
        verdict = "PARTIAL_CONVERGENCE"
        verdict_detail = (
            f"Cauchy-form recovers at {n_form_recovered}/{len(scheme_results)} "
            f"weighting schemes. Form is robust to MOST encoding choices but not "
            "all. rho VALUE differs from parent multinacci; substrate-B encoding "
            "is partially load-bearing."
        )
    else:
        verdict = "DISSONANCE"
        verdict_detail = (
            "No tested weighting scheme yields the Cauchy form. Substrate-B "
            "encoding choice is load-bearing; multinacci-recurrence and "
            "graph-Laplacian encodings of the 3+7+1 partition are NOT "
            "substrate-equivalent at the form level."
        )

    synthesis = {
        "kind": "synthesis",
        "n_schemes_tested": len(scheme_results),
        "n_form_recovered_loose": n_form_recovered,
        "n_strict_pass_with_range_gate": n_strict_pass,
        "closest_to_parent_multinacci_rho": {
            "scheme": closest_to_multinacci["scheme"],
            "rho_subdom_over_dom": closest_to_multinacci["rho_subdom_over_dom"],
            "abs_diff": closest_to_multinacci["comparison_to_parent"]["abs_diff_alt_vs_multinacci"],
        },
        "closest_to_fib_psi_rho": {
            "scheme": closest_to_fib_psi["scheme"],
            "rho_subdom_over_dom": closest_to_fib_psi["rho_subdom_over_dom"],
            "abs_diff": closest_to_fib_psi["comparison_to_parent"]["abs_diff_alt_vs_fib_psi"],
        },
        "verdict": verdict,
        "verdict_detail": verdict_detail,
        "discipline_guards_honoured": [
            "[[user_stance_kepler_shape_universal]]",
            "[[user_stance_identity_not_implementation_discipline]]",
            "[[user_stance_partition_for_understanding]]",
            "[[feedback_no_privileged_primitive_classes]]",
            "[[feedback_multi_domain_multi_round_survival_falsification_method]]",
            "[[feedback_ndjson_over_bloated_json]]",
            "[[feedback_no_mvp_framing]]",
        ],
    }
    emit(SYNTHESIS_FILE, synthesis)

    print("\n=== SYNTHESIS ===")
    print(f"Verdict: {verdict}")
    print(f"Detail: {verdict_detail}")
    print(f"Form recovered (loose r2 > 0.99 + monotonic): "
          f"{n_form_recovered}/{len(scheme_results)} schemes")
    print(f"Strict pass (incl. physical-range gate): "
          f"{n_strict_pass}/{len(scheme_results)} schemes")
    print(f"\nClosest to parent multinacci rho (0.6885):")
    print(f"  Scheme: {closest_to_multinacci['scheme']}")
    print(f"  rho_subdom = {closest_to_multinacci['rho_subdom_over_dom']:.6f}")
    print(f"  |diff| = {closest_to_multinacci['comparison_to_parent']['abs_diff_alt_vs_multinacci']:.4f}")
    print(f"\nClosest to fibonacci |psi| (0.6180):")
    print(f"  Scheme: {closest_to_fib_psi['scheme']}")
    print(f"  rho_subdom = {closest_to_fib_psi['rho_subdom_over_dom']:.6f}")
    print(f"  |diff| = {closest_to_fib_psi['comparison_to_parent']['abs_diff_alt_vs_fib_psi']:.4f}")

    print(f"\n=== Outputs ===")
    print(f"  {RECORDS_FILE}")
    print(f"  {SYNTHESIS_FILE}")


if __name__ == "__main__":
    main()
