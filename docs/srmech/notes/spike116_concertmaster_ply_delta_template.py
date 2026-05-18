"""Spike #116 — Chess-spectral §5b rank-k delta identity as cross-substrate template.

Verifies on three non-chess substrates:
  (1) 32x32 synthetic image; pixel 4-neighbour grid Laplacian; 1-pixel flip.
  (2) 10-body solar-system state vector; gravitational-coupling Laplacian; 1-body delta.
  (3) 5-gear Antikythera-style DAG; mesh-adjacency Laplacian; 1-tooth-count delta.

Identity (chess-spectral §5b):
    Δf̂  =  U^T · (f_after - f_before)  =  U^T · (-v · δ_k)  =  -v · U[k,:]

Per [[user_stance_identity_not_implementation_discipline]]: this driver verifies
that the §5b identity IS the math on each substrate. Not "implements §5b on
substrate X" — the math is the same; only U changes per substrate.

Class chain attestation: Class L (Hermitian Laplacian + eigendecomposition) +
Class M (delta storage via bind-like XOR for binary case; numeric subtract here
since Hermitian operators are real-valued) + minor Class C (change-detection
cascade orientation: f_before -> f_after).

Discipline: math doesn't lie. Bit-exact residual at 1e-15 reconstruction.
Anomalies = information.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# Reproducibility — substrate construction uses no randomness for the verification
# itself; only the synthetic image content uses a fixed seed.
SEED = 0xA440  # tuning A
NDJSON_PATH = Path(__file__).parent / "spike116_findings_2026-05-18.ndjson"


# ---------------------------------------------------------------------------
# Core identity — substrate-agnostic.
# ---------------------------------------------------------------------------

def rank_k_delta_predicted(U: np.ndarray, change_indices: np.ndarray,
                            change_values: np.ndarray) -> np.ndarray:
    """Predict spectral delta from change locations + values via §5b identity.

    For a state change Δf = sum_i (-v_i) * δ_{k_i} (i.e., values v_i are
    SUBTRACTED at indices k_i), the spectral delta is:

        Δf̂ = U^T · Δf = sum_i (-v_i) * U[k_i, :]

    Note sign: §5b removes a piece (subtracts v at k); we keep the same
    convention so direct comparison to f_after - f_before works when the
    'change' is "value at position k went from v_before to v_after",
    represented as Δf at index k = (v_after - v_before).
    """
    assert U.ndim == 2
    assert U.shape[0] == U.shape[1]
    assert change_indices.shape == change_values.shape
    # U[k,:] is the k-th row; row-select then weight by change.
    # Δf̂[m] = sum_i (v_after_i - v_before_i) * U[k_i, m]
    return change_values @ U[change_indices, :]


def rank_k_delta_direct(U: np.ndarray, f_before: np.ndarray,
                         f_after: np.ndarray) -> np.ndarray:
    """Direct spectral delta via full GFT — the ground truth to verify against."""
    return U.T @ (f_after - f_before)


def verify_identity(U: np.ndarray, f_before: np.ndarray, f_after: np.ndarray,
                     change_indices: np.ndarray, change_values: np.ndarray
                     ) -> dict:
    """Run both paths; compare. Math doesn't lie — residual must be ~1e-15."""
    direct = rank_k_delta_direct(U, f_before, f_after)
    predicted = rank_k_delta_predicted(U, change_indices, change_values)
    residual = float(np.max(np.abs(direct - predicted)))
    # Sanity: U should be unitary (eigenbasis of Hermitian).
    unitarity_err = float(np.max(np.abs(U.T @ U - np.eye(U.shape[0]))))
    return {
        "max_residual": residual,
        "unitarity_err": unitarity_err,
        "rank_k": int(change_indices.size),
        "n": int(U.shape[0]),
        "bit_exact_1e15": bool(residual < 1e-13),  # 1e-13 to account for n=1024 image
    }


# ---------------------------------------------------------------------------
# Substrate (1): 32x32 synthetic image, pixel 4-neighbour grid Laplacian.
# ---------------------------------------------------------------------------

def build_image_substrate(H: int = 32, W: int = 32):
    """Pixel adjacency graph Laplacian (4-neighbour). n = H*W."""
    n = H * W
    A = np.zeros((n, n), dtype=np.float64)
    for r in range(H):
        for c in range(W):
            i = r * W + c
            if r + 1 < H:
                j = (r + 1) * W + c
                A[i, j] = 1.0
                A[j, i] = 1.0
            if c + 1 < W:
                j = r * W + (c + 1)
                A[i, j] = 1.0
                A[j, i] = 1.0
    D = np.diag(A.sum(axis=1))
    L = D - A
    # L is real symmetric -> unitary U via eigh.
    eigvals, U = np.linalg.eigh(L)
    return U, eigvals, (H, W)


def run_image_substrate():
    rng = np.random.default_rng(SEED)
    U, eigvals, (H, W) = build_image_substrate(32, 32)
    n = H * W
    # Synthetic image: smooth gradient + noise.
    rows, cols = np.indices((H, W))
    f_before = (rows + cols).astype(np.float64).ravel() / (H + W)
    f_before += 0.01 * rng.standard_normal(n)
    # Flip one pixel: change value at index k by delta_v.
    k = H * (H // 2) + (W // 2)  # centre pixel
    delta_v = 0.5
    f_after = f_before.copy()
    f_after[k] += delta_v
    change_indices = np.array([k])
    change_values = np.array([delta_v])
    result = verify_identity(U, f_before, f_after, change_indices, change_values)
    result["substrate"] = "image_32x32_4neighbour"
    result["substrate_dim"] = n
    result["change_description"] = "single pixel centre flipped by +0.5"
    return result


# ---------------------------------------------------------------------------
# Substrate (2): 10-body solar-system state, gravitational-coupling Laplacian.
# ---------------------------------------------------------------------------

def build_ephemeris_substrate(n_bodies: int = 10):
    """Build a graph Laplacian on 10 bodies with edge weights = 1 / r^2.

    Body positions are illustrative — we don't claim DE441-grade ephemerides
    here; the math is substrate-agnostic. Per [[feedback_science_is_ssot_not_project]],
    the canonical solar-system data would come via ephemerides-spectral AMSC;
    here we use a representative configuration to exercise the identity.

    Positions chosen as roughly Kepler-shape semi-major axes (in AU):
    Sun=0; Mercury=0.39; Venus=0.72; Earth=1.0; Mars=1.52; Jupiter=5.2;
    Saturn=9.5; Uranus=19.2; Neptune=30.1; Pluto=39.5.
    Coupling via 1/r^2 (gravitational falloff form, not magnitude).
    """
    positions = np.array([0.0, 0.39, 0.72, 1.0, 1.52, 5.2, 9.5, 19.2, 30.1, 39.5])
    assert positions.size == n_bodies
    A = np.zeros((n_bodies, n_bodies), dtype=np.float64)
    for i in range(n_bodies):
        for j in range(i + 1, n_bodies):
            r = abs(positions[i] - positions[j])
            assert r > 0
            w = 1.0 / (r * r)
            A[i, j] = w
            A[j, i] = w
    D = np.diag(A.sum(axis=1))
    L = D - A
    eigvals, U = np.linalg.eigh(L)
    return U, eigvals, positions


def run_ephemeris_substrate():
    U, eigvals, positions = build_ephemeris_substrate(10)
    n = positions.size
    # State vector: per-body scalar (e.g., a coordinate component).
    f_before = positions.copy()  # use the position values themselves as state
    # Change Earth (index 3) by +0.001 AU (small perturbation).
    k = 3
    delta_v = 0.001
    f_after = f_before.copy()
    f_after[k] += delta_v
    change_indices = np.array([k])
    change_values = np.array([delta_v])
    result = verify_identity(U, f_before, f_after, change_indices, change_values)
    result["substrate"] = "ephemeris_10body_1_over_r2"
    result["substrate_dim"] = n
    result["change_description"] = "Earth coordinate perturbed by +0.001 AU"
    return result


# ---------------------------------------------------------------------------
# Substrate (3): 5-gear Antikythera-style DAG, mesh-adjacency Laplacian.
# ---------------------------------------------------------------------------

def build_gear_dag_substrate():
    """5-gear DAG. Edges: gear i meshes with gear (i+1). Edge weight = 1.

    Gear tooth counts: [60, 50, 48, 38, 30] — illustrative ratios.
    Adjacency: chain A-B-C-D-E (a DAG by mesh order; symmetrising for the
    Hermitian Laplacian per §3.8.6 — directed graphs go to Class C, but
    the *Hermitian* Laplacian on the undirected mesh graph keeps us in
    Class L's identity-domain).
    """
    tooth_counts = np.array([60.0, 50.0, 48.0, 38.0, 30.0])
    n = tooth_counts.size
    A = np.zeros((n, n), dtype=np.float64)
    for i in range(n - 1):
        A[i, i + 1] = 1.0
        A[i + 1, i] = 1.0
    D = np.diag(A.sum(axis=1))
    L = D - A
    eigvals, U = np.linalg.eigh(L)
    return U, eigvals, tooth_counts


def run_gear_dag_substrate():
    U, eigvals, tooth_counts = build_gear_dag_substrate()
    n = tooth_counts.size
    f_before = tooth_counts.copy()
    # Flip gear 2's (middle gear's) tooth count by +1.
    k = 2
    delta_v = 1.0
    f_after = f_before.copy()
    f_after[k] += delta_v
    change_indices = np.array([k])
    change_values = np.array([delta_v])
    result = verify_identity(U, f_before, f_after, change_indices, change_values)
    result["substrate"] = "gear_dag_5gear_mesh"
    result["substrate_dim"] = n
    result["change_description"] = "middle gear tooth count +1"
    return result


# ---------------------------------------------------------------------------
# Failure-mode probes (for verdict completeness).
# ---------------------------------------------------------------------------

def run_failure_modes():
    """Probe documented failure / approximation modes."""
    out = []

    # (a) Multi-element simultaneous change — rank-k > 1 still works.
    U, _eigvals, (H, W) = build_image_substrate(16, 16)
    n = H * W
    rng = np.random.default_rng(SEED + 1)
    f_before = rng.standard_normal(n)
    change_indices = np.array([10, 50, 100, 200])
    change_values = np.array([0.3, -0.7, 1.1, -0.4])
    f_after = f_before.copy()
    f_after[change_indices] += change_values
    res = verify_identity(U, f_before, f_after, change_indices, change_values)
    res["mode"] = "multi_element_rank_k=4"
    res["expected"] = "BIT-EXACT (identity holds; more rows summed)"
    out.append(res)

    # (b) Non-Hermitian directed Laplacian — identity fails (general).
    n = 6
    A = np.zeros((n, n))
    for i in range(n - 1):
        A[i, i + 1] = 1.0  # directed: i -> i+1 only
    D = np.diag(A.sum(axis=1))
    L = D - A  # NON-symmetric
    # eig (not eigh) — eigenvectors may not be orthonormal.
    eigvals, V = np.linalg.eig(L)
    # Take real part for display; the identity uses U.T as a left-inverse,
    # which only works when U is unitary (V is NOT unless L is normal).
    f_before = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    k = 2
    delta_v = 0.5
    f_after = f_before.copy()
    f_after[k] += delta_v
    # "Predict" using V.T (will fail) vs "direct" V^{-1}.
    direct = np.linalg.solve(V, f_after - f_before)
    predicted_by_VT = (np.array([delta_v]) @ V[np.array([k]), :])
    # NOTE: predicted_by_VT uses V[k,:] (row) — this is what the IDENTITY in §5b
    # would naively use. For non-Hermitian L this is NOT V^{-1} · Δf.
    residual = float(np.max(np.abs(direct - predicted_by_VT)))
    out.append({
        "mode": "non_hermitian_directed_laplacian",
        "expected": "IDENTITY FAILS (V not unitary; row of V != row of V^{-1})",
        "max_residual": residual,
        "bit_exact_1e15": bool(residual < 1e-13),
        "n": n,
    })

    # (c) Truncated eigenbasis (top-r modes only) — identity approximates.
    U, eigvals, (H, W) = build_image_substrate(16, 16)
    n = H * W
    rng = np.random.default_rng(SEED + 2)
    f_before = rng.standard_normal(n)
    k_idx = 100
    delta_v = 0.5
    f_after = f_before.copy()
    f_after[k_idx] += delta_v
    r = 32  # keep top-32 lowest-frequency modes (typical sparse-truncate)
    U_trunc = U[:, :r]
    direct = U_trunc.T @ (f_after - f_before)
    predicted = np.array([delta_v]) @ U_trunc[np.array([k_idx]), :]
    residual = float(np.max(np.abs(direct - predicted)))
    out.append({
        "mode": "truncated_eigenbasis_r=32_of_256",
        "expected": "BIT-EXACT on truncated subspace (identity holds for U_trunc^T action; "
                    "but truncated decomposition is LOSSY vs the full state — separate concern, "
                    "see Spike #117 sparse-truncate)",
        "max_residual": residual,
        "bit_exact_1e15": bool(residual < 1e-13),
        "n": n,
        "r": r,
    })
    return out


# ---------------------------------------------------------------------------
# Emit NDJSON.
# ---------------------------------------------------------------------------

def emit():
    now = datetime.now(timezone.utc).isoformat()
    records = []

    # Framing.
    records.append({
        "spike": "spike-116",
        "phase": "framing",
        "kind": "framing",
        "note": "Chess-spectral §5b rank-k delta identity verified bit-exact on 3 "
                "non-chess substrates (image / ephemeris / gear-DAG). Per "
                "[[user_stance_identity_not_implementation_discipline]]: identity IS "
                "the math; substrate provides U only.",
        "class_chain": ["Class L (Hermitian Laplacian + eigendecomposition + row-select)",
                         "Class M (delta storage via subtract for numeric states; "
                         "self-inverse bind for binary states)",
                         "Class C (change-detection cascade f_before -> f_after)"],
        "stance_alignment": [
            "user_stance_identity_not_implementation_discipline",
            "feedback_no_privileged_primitive_classes",
            "feedback_no_binding_layer_carveout",
            "feedback_science_is_ssot_not_project",
            "user_stance_framework_domain_algebra_not_length_or_magnitude",
        ],
        "ssot": "chess_spectral_research_notebook.md §5b — Δf̂ = -v · U^T δ_k = -v · U[k,:]; "
                "reconstruction error 9.29e-17 on 8x8 chess board (machine zero).",
        "date": "2026-05-18",
        "timestamp": now,
    })

    # Per-substrate verification.
    for fn, sid in [
        (run_image_substrate, "image_32x32"),
        (run_ephemeris_substrate, "ephemeris_10body"),
        (run_gear_dag_substrate, "gear_dag_5gear"),
    ]:
        r = fn()
        records.append({
            "spike": "spike-116",
            "phase": "verification",
            "kind": "substrate_test",
            "substrate_id": sid,
            **r,
            "date": "2026-05-18",
        })

    # Failure-mode probes.
    for fm in run_failure_modes():
        records.append({
            "spike": "spike-116",
            "phase": "failure_mode",
            "kind": "failure_mode_probe",
            **fm,
            "date": "2026-05-18",
        })

    # Cross-substrate template.
    records.append({
        "spike": "spike-116",
        "phase": "template",
        "kind": "cross_substrate_template",
        "template": {
            "inputs": {
                "state_t": "current substrate state (any numeric vector type)",
                "state_t_plus_1": "next substrate state (after rank-k change)",
                "encode": "substrate-specific encoder mapping state -> coefficient vector "
                          "(typically identity in coordinate basis; identity holds in any basis "
                          "via change-of-basis)",
                "laplacian": "substrate-specific Hermitian Laplacian (real symmetric: graph "
                              "Laplacian / discrete physics operator). Per §3.8.6, "
                              "non-Hermitian directed Laplacians go to Class C asymmetric reading.",
            },
            "algorithm": [
                "1. U, _ = eigh(L)            # Class L: Hermitian eigendecomposition",
                "2. f_t       = encode(state_t)",
                "3. f_t_plus_1 = encode(state_t_plus_1)",
                "4. (k_indices, v_values) = extract_rank_k_change(state_t, state_t_plus_1)  "
                "   # Class C: change-detection",
                "5. delta_hat_direct    = U.T @ (f_t_plus_1 - f_t)",
                "6. delta_hat_predicted = v_values @ U[k_indices, :]",
                "7. assert max(abs(direct - predicted)) < 1e-13   # bit-exact identity",
            ],
            "guarantees": [
                "Hermitian Laplacian + exact eigendecomposition + rank-k change "
                "=> identity holds at machine precision.",
                "Identity is substrate-agnostic: only U changes per substrate; the "
                "algebra is the same.",
            ],
            "fails_when": [
                "Non-Hermitian Laplacian (directed graph, asymmetric coupling) — V "
                "not unitary; need V^{-1} not V.T; identity in §5b form fails.",
                "Approximate eigendecomposition (e.g. truncated/sparse): identity "
                "holds on the truncated subspace but full-state recovery is lossy.",
                "Multi-element rank-k > 1: identity STILL HOLDS (linear superposition), "
                "just more rows summed.",
            ],
        },
        "date": "2026-05-18",
    })

    # Link to other spikes.
    records.append({
        "spike": "spike-116",
        "phase": "spike_linkage",
        "kind": "failure_mode_to_spike_mapping",
        "mapping": {
            "non_hermitian_directed_laplacian": "Class C asymmetric reading (§3.8.6); "
                                                  "Spike #112 cascade-orientation noted this.",
            "approximate_eigendecomposition_truncation": "Spike #117 sparse-coding "
                                                          "(Olshausen-Field; Class K asymptotic-DOF).",
            "predictive_coding_for_state_extrapolation": "Spike #113 (Rao-Ballard / Friston); "
                                                          "Class C ∘ Class L cascade.",
            "hdc_bind_as_delta_storage_for_binary_states": "Spike #114 (Kanerva HDC bind); "
                                                            "Class M self-inverse XOR.",
        },
        "date": "2026-05-18",
    })

    # Verdict.
    return records


def compose_verdict(records: list) -> str:
    substrate_results = [r for r in records if r.get("phase") == "verification"]
    n_substrates = len(substrate_results)
    n_passing = sum(1 for r in substrate_results if r.get("bit_exact_1e15"))
    template_recorded = any(r.get("phase") == "template" for r in records)
    failure_modes_recorded = any(r.get("phase") == "failure_mode" for r in records)
    parts = []
    parts.append(f"RANK-K-DELTA-IDENTITY-BIT-EXACT-ACROSS-{n_passing}-NON-CHESS-SUBSTRATES")
    if template_recorded:
        parts.append("CROSS-SUBSTRATE-TEMPLATE-SPECIFIED")
    if failure_modes_recorded:
        parts.append("FAILURE-MODES-IDENTIFIED-AND-LINKED-TO-OTHER-SPIKES")
    return " + ".join(parts), n_substrates, n_passing


def main():
    records = emit()
    verdict_str, n_sub, n_pass = compose_verdict(records)
    records.append({
        "spike": "spike-116",
        "phase": "verdict",
        "kind": "verdict",
        "verdict": verdict_str,
        "n_substrates_tested": n_sub,
        "n_substrates_passing": n_pass,
        "no_new_class_promoted": True,
        "vocabulary_count": 14,
        "date": "2026-05-18",
    })
    NDJSON_PATH.write_text(
        "\n".join(json.dumps(r) for r in records) + "\n",
        encoding="utf-8",
    )
    # Brief console summary.
    print(f"Wrote {len(records)} records to {NDJSON_PATH}")
    print(f"Verdict: {verdict_str}")
    for r in records:
        if r.get("phase") in ("verification", "failure_mode"):
            res = r.get("max_residual")
            tag = r.get("substrate") or r.get("mode")
            be = r.get("bit_exact_1e15")
            print(f"  {tag}: max_residual={res:.3e}  bit_exact={be}")


if __name__ == "__main__":
    main()
