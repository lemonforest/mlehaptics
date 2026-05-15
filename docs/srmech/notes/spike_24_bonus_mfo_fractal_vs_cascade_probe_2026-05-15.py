"""Spike #24 bonus 7 — MFO fractal-requirement probe via nested-gear-cascade.

Question being tested (verbatim user phrasing, 2026-05-15):
    Is fractal a REQUIREMENT for MFO's SM-spectrum-targeting program, or
    does fractal simply DESCRIBE the shape of a structure that spans ~11
    orders of magnitude with three-fold sub-structure? "Probably it isn't
    a fractal, but a fractal probably looks like it, or is it in reverse
    direction." Pin-slot nested-gear-cascade alternative proposed (per
    Antikythera precedent: small gears that compose into large gears that
    compose into a huge ring).

Methodological commitment (per `[[feedback_antiquity_not_greek]]`):
    Falsifier MUST be a spectral-graph operation, not a math-consistency
    check. We test fractal-substrate vs nested-gear-cascade substrate via
    Class L on their eigenvalue degeneracy graphs (same instrument the
    bonus 5 synthesis used for 3+7+1 vs pure-4D).

Three substrates to compare (all 3D-spatial; held in the same 3+7+1
context as MFO §IV.4):
    1. M_SG3D      = Sierpinski gasket SG(level=3), MFO §IV.2 reference
                     fractal substrate. Decimation R(λ) = λ(5-λ).
    2. M_GEAR3D    = Nested-gear-cascade C_{n1} × C_{n2} × C_{n3} with
                     deeply hierarchical tooth counts spanning multiple
                     orders of magnitude AND three-fold sub-structure
                     (the user's proposed alternative).
    3. M_SMOOTH3D  = Smooth anisotropic T^3 (the bonus 5 cleanest-tower
                     baseline).

Each is then embedded in the same 3+7+1 product: F × T^7 × S^1, and the
spectra are compared by:
    (a) span of orders of magnitude in the eigenvalue distribution
    (b) presence of three-fold sub-structure (e.g. three sub-clusters)
    (c) Class L on the degeneracy graph (Fiedler λ_2, connected
        components, gap CV)
    (d) reversed-direction probe: when a deep gear cascade is observed
        only via its spectrum, does it LOOK fractal-like by these same
        Class L measures?

Deterministic. Seed = 20260515. Output: NDJSON one record per line.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Iterable

import numpy as np


SEED = 20260515
rng = np.random.default_rng(SEED)

HERE = Path(__file__).parent
NDJSON_PATH = HERE / "spike_24_bonus_mfo_fractal_vs_cascade_probe_2026-05-15.ndjson"


# ─── Helpers (shared with bonus 5 probe; re-implemented inline for self-containment) ──


def cycle_eigenvalues(n: int, radius: float = 1.0) -> np.ndarray:
    """Closed-form eigenvalues of C_n on cycle of circumference 2*pi*radius.

    Discrete-Laplacian eigenvalues on C_n are 2*(1 - cos(2*pi*k/n)) for
    k=0..n-1. Per `[[user_stance_pi_as_projection]]`: this is the
    continuous-projection of integer-cyclic-cyclic ℤ/n algebra; the
    integer-cyclic content is upstream.
    """
    k = np.arange(n)
    eigs = 2.0 * (1.0 - np.cos(2.0 * np.pi * k / n)) / (2.0 * np.pi * radius / n) ** 2
    return np.sort(eigs)


def sg_pre_eigenvalues_iterated(levels: int) -> np.ndarray:
    """Sierpinski-gasket pre-gasket eigenvalues via spectral decimation.

    Per MFO §IV.2: R(λ) = λ(5-λ); inverse R⁻¹(w) = (5 ± sqrt(25 - 4w))/2.
    Level 0 seeds with Neumann BC: {0, 5}. Born eigenvalues added at
    each level: {2, 5}.
    """
    eigs = [0.0, 5.0]
    for _ in range(levels):
        new_eigs = []
        for w in eigs:
            disc = 25.0 - 4.0 * w
            if disc < -1e-12:
                continue
            disc = max(disc, 0.0)
            root = math.sqrt(disc)
            new_eigs.append((5.0 + root) / 2.0)
            new_eigs.append((5.0 - root) / 2.0)
        new_eigs.extend([2.0, 5.0])
        eigs = sorted(set(round(x, 12) for x in new_eigs if x >= -1e-12))
    return np.array(sorted(eigs))


def product_eigenvalues(spectra: list[np.ndarray], topN: int = 80) -> np.ndarray:
    """Product-manifold eigenvalues = pairwise sums of factor eigenvalues."""
    eigs = np.array([0.0])
    for sp_factor in spectra:
        combined = (eigs[:, None] + sp_factor[None, :]).ravel()
        combined.sort()
        keep = min(len(combined), max(topN * 4, 200))
        eigs = combined[:keep]
    return eigs[:topN]


def torus_eigenvalues(radii: list[float], topN: int = 80) -> np.ndarray:
    """Anisotropic torus T^k eigenvalues: sum_i (n_i / R_i)^2 with ±n_i degeneracy."""
    per_axis = []
    for R in radii:
        nmax = max(8, int(topN ** (1.0 / max(len(radii), 1))) + 2)
        vals = []
        for n in range(nmax + 1):
            vals.append((n / R) ** 2)
            if n > 0:
                vals.append((n / R) ** 2)
        per_axis.append(np.array(sorted(vals)))
    return product_eigenvalues(per_axis, topN=topN)


def spectral_gap_profile(eigs: np.ndarray) -> dict:
    """Gap statistics: 'tower / gap' structure of a spectrum."""
    eigs = np.sort(np.unique(np.round(eigs, 10)))
    gaps = np.diff(eigs)
    gaps = gaps[gaps > 1e-12]
    if len(gaps) == 0:
        return {
            "n_eigs": int(len(eigs)),
            "n_gaps": 0,
            "mean_gap": 0.0,
            "max_gap": 0.0,
            "min_gap": 0.0,
            "gap_to_mean_ratio": 0.0,
            "cv_gap": 0.0,
        }
    return {
        "n_eigs": int(len(eigs)),
        "n_gaps": int(len(gaps)),
        "mean_gap": float(np.mean(gaps)),
        "max_gap": float(np.max(gaps)),
        "min_gap": float(np.min(gaps)),
        "gap_to_mean_ratio": float(np.max(gaps) / np.mean(gaps)),
        "cv_gap": float(np.std(gaps) / np.mean(gaps)),
    }


def multiplicity_profile(eigs: np.ndarray, bin_width: float = 0.25) -> tuple[np.ndarray, np.ndarray]:
    """Histogram of eigenvalues into bins."""
    lo, hi = eigs.min(), eigs.max()
    n_bins = max(int(np.ceil((hi - lo) / bin_width)), 8)
    bins = np.linspace(lo, hi + 1e-9, n_bins + 1)
    counts, edges = np.histogram(eigs, bins=bins)
    centers = 0.5 * (edges[1:] + edges[:-1])
    return centers, counts


def degeneracy_graph_class_l(eigs: np.ndarray, bin_width: float = 0.25) -> dict:
    """Class L on the degeneracy graph (per bonus 5 §3.2 instrument)."""
    centers, counts = multiplicity_profile(eigs, bin_width=bin_width)
    n = len(centers)
    if n < 4:
        return {"n_bins": n, "lambda_2": 0.0, "fiedler_ratio": 0.0,
                "n_connected_components": 1, "max_multiplicity": int(counts.max())}
    A = np.zeros((n, n))
    for i in range(n - 1):
        w = float(min(counts[i], counts[i + 1]))
        A[i, i + 1] = w
        A[i + 1, i] = w
    degrees = A.sum(axis=1)
    L = np.diag(degrees) - A
    eigvals = np.sort(np.linalg.eigvalsh(L))
    lambda_2 = float(eigvals[1]) if n > 1 else 0.0
    lambda_max = float(eigvals[-1])
    n_zero = int(np.sum(eigvals < 1e-9))
    return {
        "n_bins": int(n),
        "lambda_2": lambda_2,
        "lambda_max": lambda_max,
        "fiedler_ratio": float(lambda_2 / lambda_max) if lambda_max > 1e-12 else 0.0,
        "n_connected_components": n_zero,
        "max_multiplicity": int(counts.max()),
        "n_distinct_levels": int(np.sum(counts > 0)),
    }


def write_record(record: dict, fp) -> None:
    fp.write(json.dumps(record, sort_keys=True) + "\n")


# ─── (A) Nested-gear-cascade substrate construction ─────────────────────────


def gear_cascade_eigenvalues(
    tooth_counts: list[int],
    radii: list[float] | None = None,
    topN: int = 100,
) -> np.ndarray:
    """Nested-gear-cascade substrate as product of cyclic groups.

    Per the user's framing (verbatim): "small gears that are large gear
    that is a huge ring and all the others move inside." Algebraically:
    nested ℤ/n composition. Spectrally: product manifold of C_{n_i} cycles.

    Per `[[user_stance_kepler_shape_universal]]` and the Antikythera
    precedent (PR #416 §11.6.17): bronze gear-train carries multi-scale
    composition via nested ℤ/n. The 76-year Callippic cycle is encoded
    by 53 × 64 × 64-tooth gears; the 19-year Metonic by 19 × 47 × 127;
    etc. Multi-scale spans naturally with cascade depth.

    Spectrum: cycle Laplacian eigenvalues on each C_{n_i} are
    2(1 - cos(2πk/n_i))/Δx² with Δx = 2πR/n_i. Product manifold eigenvalues
    = sums.

    Tooth counts span many orders of magnitude: small gear n_1 ~ 3-7,
    intermediate n_2 ~ 30-70, large ring n_3 ~ 300-700. Each radius set
    independently. This is the analog of the Antikythera's 53/64/64
    nested gear-train composition.
    """
    if radii is None:
        radii = [1.0] * len(tooth_counts)
    per_axis = []
    for n_i, R_i in zip(tooth_counts, radii):
        per_axis.append(cycle_eigenvalues(n_i, radius=R_i))
    return product_eigenvalues(per_axis, topN=topN)


# ─── (B) 11-orders-of-magnitude span: can gear cascade reach it? ───────────


def measure_orders_of_magnitude_span(eigs: np.ndarray) -> dict:
    """Compute log-range of non-zero eigenvalues — directly addressing
    the user's question: 'whatever we need to build to scale this order
    of magnitude.'

    SM mass-squared ratios span 11 orders of magnitude (MFO §IV.6).
    Test: does the candidate substrate naturally produce eigenvalue
    ratios spanning that range?
    """
    eigs_pos = eigs[eigs > 1e-15]
    if len(eigs_pos) < 2:
        return {"n_eigs": int(len(eigs_pos)), "log_span": 0.0, "min": 0.0, "max": 0.0}
    return {
        "n_eigs": int(len(eigs_pos)),
        "log_span": float(np.log10(eigs_pos.max() / eigs_pos.min())),
        "min": float(eigs_pos.min()),
        "max": float(eigs_pos.max()),
        "median": float(np.median(eigs_pos)),
    }


# ─── (C) Three-fold sub-structure detection ─────────────────────────────────


def detect_three_fold_substructure(eigs: np.ndarray, k_clusters: int = 3) -> dict:
    """Detect whether a spectrum has three-fold sub-clustering (MFO §IV.5).

    Method: take log-eigenvalues (so the test is multiplicative-scale-aware,
    matching the way SM masses cluster — three generations span 11 orders
    of magnitude with within-generation splittings small relative to
    inter-generation gaps).

    Then cluster via 1D k-means with k=3 and measure:
        - within-cluster variance (smaller = cleaner three-fold structure)
        - between-cluster variance (larger = sharper inter-generation gaps)
        - Calinski-Harabasz-like ratio (Var_between / Var_within)

    A perfectly three-fold-self-similar fractal would have low within-
    cluster variance + high between-cluster variance.

    Per MFO §IV.5: this is the load-bearing fractal-specific claim
    ("three generations from three-fold self-similarity"). Test whether
    the gear-cascade can match it.
    """
    eigs_pos = eigs[eigs > 1e-15]
    if len(eigs_pos) < 3 * k_clusters:
        return {"valid": False, "n_eigs": int(len(eigs_pos))}

    log_eigs = np.log10(eigs_pos).reshape(-1, 1)
    # simple 1D k-means (deterministic init)
    sorted_log = np.sort(log_eigs.ravel())
    # initialise centroids at evenly-spaced quantiles
    centroids = np.array([
        sorted_log[int(len(sorted_log) * (i + 0.5) / k_clusters)]
        for i in range(k_clusters)
    ])

    # Lloyd iterations
    for _ in range(100):
        # assign
        labels = np.argmin(np.abs(log_eigs.ravel()[:, None] - centroids[None, :]), axis=1)
        # update
        new_centroids = np.array([
            log_eigs.ravel()[labels == k].mean() if np.sum(labels == k) > 0 else centroids[k]
            for k in range(k_clusters)
        ])
        if np.allclose(new_centroids, centroids, rtol=1e-8):
            break
        centroids = new_centroids

    overall_mean = log_eigs.mean()
    var_within = 0.0
    var_between = 0.0
    cluster_sizes = []
    for k in range(k_clusters):
        members = log_eigs.ravel()[labels == k]
        cluster_sizes.append(int(len(members)))
        if len(members) > 0:
            var_within += np.sum((members - centroids[k]) ** 2)
            var_between += len(members) * (centroids[k] - overall_mean) ** 2
    n = len(log_eigs)
    var_within = float(var_within / max(n - k_clusters, 1))
    var_between = float(var_between / max(k_clusters - 1, 1))
    ch_ratio = var_between / var_within if var_within > 1e-12 else float("inf")
    return {
        "valid": True,
        "n_eigs": int(n),
        "k_clusters": k_clusters,
        "cluster_centroids_log": [float(c) for c in centroids],
        "cluster_sizes": cluster_sizes,
        "var_within_log_units": var_within,
        "var_between_log_units": var_between,
        "ch_ratio": ch_ratio,
        "min_cluster_centroid_gap_log": float(np.min(np.diff(sorted(centroids)))),
        "max_cluster_centroid_gap_log": float(np.max(np.diff(sorted(centroids)))),
    }


# ─── (D) Reversed-direction probe: do they look the same? ──────────────────


def construct_blind_observer_spectra() -> dict:
    """Build matched eigenvalue counts across substrate types and measure
    Class-L statistics WITHOUT telling the observer which substrate is which.

    Per the user's reverse-direction hypothesis: "a fractal probably
    looks like it [a gear cascade], or is it in reverse direction."
    i.e. are fractal-spectrum and gear-cascade-spectrum mutually
    distinguishable?

    Construction protocol:
        - Match topN across all substrates (topN=80 for all).
        - Embed each 3D-substrate in same 3+7+1 (× T^7 × S^1).
        - Measure: log_span, three-fold-substructure CH ratio, Class L
          on degeneracy graph (Fiedler λ_2, n_connected_components).

    Verdict: if the metrics OVERLAP across substrates, the spectra are
    not Class-L-distinguishable (reverse-direction reading holds). If
    they DIFFER, the spectra are distinguishable (fractal-required or
    one-way-not-required reading).
    """
    return {}  # placeholder; real work in main()


# ─── (E) Verdict synthesis ──────────────────────────────────────────────────


def verdict_synthesis(records: list[dict]) -> dict:
    """Synthesise findings into one of four verdicts.

    - REQUIRED: fractal-specific claim survives; cascade falsifies.
    - ONE_WAY_NOT_REQUIRED: load-bearing requirement is more general
      (multi-scale + three-fold); both substrates satisfy.
    - INVERSE_DESCRIPTION: spectra are Class-L-indistinguishable; fractal
      and cascade are dual descriptions of the same underlying structure.
    - UNFALSIFIABLE: spectral-graph test cannot decide at SM-scale.
    """
    # filter for the three core substrate records
    by_substrate = {r["substrate"]: r for r in records if r.get("phase") == "substrate_classL"}

    if not all(k in by_substrate for k in ("M_SG3D", "M_GEAR3D", "M_SMOOTH3D")):
        return {"verdict": "INCOMPLETE", "reason": "missing substrate records"}

    sg = by_substrate["M_SG3D"]
    gear = by_substrate["M_GEAR3D"]
    smooth = by_substrate["M_SMOOTH3D"]

    # discriminator metrics
    span_diff_sg_gear = abs(sg["log_span"] - gear["log_span"])
    cv_diff_sg_gear = abs(sg["cv_gap"] - gear["cv_gap"])
    lambda2_diff_sg_gear = abs(sg["fiedler_lambda_2"] - gear["fiedler_lambda_2"])
    cc_diff_sg_gear = abs(sg["n_connected_components"] - gear["n_connected_components"])

    # three-fold metrics
    ch_sg = sg.get("three_fold_ch_ratio", 0.0)
    ch_gear = gear.get("three_fold_ch_ratio", 0.0)
    ch_smooth = smooth.get("three_fold_ch_ratio", 0.0)

    # decision logic
    # Indistinguishable threshold: <20% difference on all 4 discriminators
    sg_span = max(sg["log_span"], 1e-6)
    if (
        span_diff_sg_gear / sg_span < 0.2
        and cv_diff_sg_gear < 0.3
        and cc_diff_sg_gear == 0
        and lambda2_diff_sg_gear < 0.3
    ):
        verdict = "INVERSE_DESCRIPTION"
    elif gear["log_span"] >= 0.7 * sg["log_span"] and ch_gear >= 0.5 * ch_sg:
        # cascade matches both span AND three-fold substructure capability
        verdict = "ONE_WAY_NOT_REQUIRED"
    elif gear["log_span"] < 0.5 * sg["log_span"] or ch_gear < 0.2 * ch_sg:
        # cascade fails at either span or three-fold; fractal is doing something
        # the cascade cannot
        verdict = "REQUIRED"
    else:
        verdict = "UNFALSIFIABLE"

    return {
        "verdict": verdict,
        "span_M_SG3D": float(sg["log_span"]),
        "span_M_GEAR3D": float(gear["log_span"]),
        "span_M_SMOOTH3D": float(smooth["log_span"]),
        "three_fold_ch_M_SG3D": float(ch_sg),
        "three_fold_ch_M_GEAR3D": float(ch_gear),
        "three_fold_ch_M_SMOOTH3D": float(ch_smooth),
        "cv_diff_sg_vs_gear": float(cv_diff_sg_gear),
        "fiedler_diff_sg_vs_gear": float(lambda2_diff_sg_gear),
        "ccs_diff_sg_vs_gear": int(cc_diff_sg_gear),
    }


# ─── Main ────────────────────────────────────────────────────────────────────


def measure_substrate(name: str, eigs_3d: np.ndarray, embed_in_371: bool = True) -> dict:
    """Embed substrate's 3D spectrum in the 3+7+1 product (if requested) and
    measure all discriminators."""
    if embed_in_371:
        # MFO §IV.4 product rule
        sp_T7 = torus_eigenvalues([1.0, 1.05, 1.1, 1.15, 1.2, 1.25, 1.3], topN=200)
        sp_S1 = cycle_eigenvalues(32, radius=1.0)[:100]
        eigs = product_eigenvalues([eigs_3d, sp_T7, sp_S1], topN=120)
    else:
        eigs = np.asarray(eigs_3d)[:120]

    span = measure_orders_of_magnitude_span(eigs)
    three_fold = detect_three_fold_substructure(eigs, k_clusters=3)
    gap = spectral_gap_profile(eigs)
    class_l = degeneracy_graph_class_l(eigs, bin_width=0.25)

    return {
        "phase": "substrate_classL",
        "substrate": name,
        "embedded_3plus7plus1": embed_in_371,
        "n_eigs_3d_substrate": int(len(eigs_3d)),
        "n_eigs_total": int(len(eigs)),
        "lambda_max": float(eigs.max()),
        "lambda_min_nonzero": float(eigs[eigs > 1e-15].min()) if (eigs > 1e-15).any() else 0.0,
        "log_span": float(span["log_span"]),
        "median_eig": float(span.get("median", 0.0)),
        "three_fold_ch_ratio": float(three_fold.get("ch_ratio", 0.0)) if three_fold.get("valid") else 0.0,
        "three_fold_cluster_sizes": three_fold.get("cluster_sizes", []),
        "three_fold_centroids_log": three_fold.get("cluster_centroids_log", []),
        "three_fold_var_within_log": float(three_fold.get("var_within_log_units", 0.0)) if three_fold.get("valid") else 0.0,
        "three_fold_var_between_log": float(three_fold.get("var_between_log_units", 0.0)) if three_fold.get("valid") else 0.0,
        "min_cluster_centroid_gap_log": float(three_fold.get("min_cluster_centroid_gap_log", 0.0)) if three_fold.get("valid") else 0.0,
        "cv_gap": float(gap["cv_gap"]),
        "gap_max_mean_ratio": float(gap["gap_to_mean_ratio"]),
        "fiedler_lambda_2": float(class_l["lambda_2"]),
        "fiedler_ratio": float(class_l["fiedler_ratio"]),
        "n_connected_components": int(class_l["n_connected_components"]),
        "max_multiplicity": int(class_l["max_multiplicity"]),
        "n_distinct_levels": int(class_l["n_distinct_levels"]),
    }


def main() -> None:
    records: list[dict] = []

    # Header record: provenance + question + seed
    records.append({
        "phase": "header",
        "spike": "24_bonus_7_mfo_fractal_requirement",
        "date": "2026-05-15",
        "seed": SEED,
        "question": (
            "Is fractal REQUIRED for MFO SM-spectrum-targeting, or only one "
            "instance of a more general multi-scale + three-fold cascade requirement? "
            "Compare nested-gear-cascade vs Sierpinski-gasket substrate via Class L."
        ),
        "method": "MFO IV.4 product-geometry + bonus5 degeneracy-graph Class L",
        "discipline": "antiquity-geocentric methodological discriminator: falsifier is spectral-graph operation",
    })

    # ─── Substrate 1: M_SG3D (the MFO §IV.2 reference fractal) ──────
    sg_eigs = sg_pre_eigenvalues_iterated(levels=3)
    records.append({
        "phase": "substrate_construction",
        "substrate": "M_SG3D",
        "construction": "Sierpinski gasket SG(level=3); MFO §IV.2 spectral decimation",
        "decimation_rule": "R(lambda) = lambda * (5 - lambda)",
        "n_eigs_substrate_only": int(len(sg_eigs)),
        "spectral_dim_dS": float(2 * math.log(3) / math.log(5)),
        "hausdorff_dim_dH": float(math.log(3) / math.log(2)),
        "three_fold_self_similar": True,
    })
    records.append(measure_substrate("M_SG3D", sg_eigs, embed_in_371=True))

    # ─── Substrate 2: M_GEAR3D (nested gear cascade with multi-scale span) ──
    # Antikythera-style: small gears compose into large gears compose into
    # huge ring. To span MANY orders of magnitude in the spectrum, use
    # exponentially-graduated radii (small Δx => large eigenvalues; large Δx
    # => small eigenvalues). This is exactly the Antikythera precedent:
    # 53 × 64 × 64 → 76-year Callippic spans orders of magnitude across
    # period ratios. Use three-fold-available structure: 3 nested cycles.
    # Tooth counts: 7 (innermost), 49 (middle), 343 (outermost ring) —
    # geometric progression r=7. Radii likewise graduated: 0.01, 0.5, 25.0
    # — three orders of magnitude in geometric scale per the user's
    # "small gears that are large gear that is a huge ring" framing.
    gear_tooth_counts = [7, 49, 343]  # three-fold available; r=7 geometric
    gear_radii = [0.01, 0.5, 25.0]    # geometric: 50× each step
    gear_eigs = gear_cascade_eigenvalues(
        tooth_counts=gear_tooth_counts,
        radii=gear_radii,
        topN=200,
    )
    records.append({
        "phase": "substrate_construction",
        "substrate": "M_GEAR3D",
        "construction": "Nested gear cascade C_{7} × C_{49} × C_{343} with geometric-progression radii",
        "tooth_counts": gear_tooth_counts,
        "tooth_count_progression": "geometric, r=7",
        "radii": gear_radii,
        "radii_progression": "geometric, r=50",
        "three_fold_available": "yes — 3 nested cycles + r=7 ratio",
        "antikythera_precedent": "PR #416 §11.6.17 — bronze multi-scale composition (53×64×64 → 76-year Callippic)",
        "n_eigs_substrate_only": int(len(gear_eigs)),
    })
    records.append(measure_substrate("M_GEAR3D", gear_eigs, embed_in_371=True))

    # ─── Substrate 3: M_SMOOTH3D (smooth anisotropic torus baseline) ──────
    # The bonus 5 finding's "cleanest 3+7+1 signature" — smooth-3D substrate.
    smooth_eigs = torus_eigenvalues([1.0, 1.1, 1.2], topN=200)
    records.append({
        "phase": "substrate_construction",
        "substrate": "M_SMOOTH3D",
        "construction": "Smooth anisotropic T^3 (radii 1.0, 1.1, 1.2)",
        "n_eigs_substrate_only": int(len(smooth_eigs)),
        "three_fold_available": "no (no special structure)",
    })
    records.append(measure_substrate("M_SMOOTH3D", smooth_eigs, embed_in_371=True))

    # ─── (D) Deep-cascade scaling: can gear cascade span 11 orders of magnitude? ─
    # Test progressively deeper gear cascades. Per user's question: "whatever
    # we need to build to scale this order of magnitude." Cascade depth scaling
    # study.
    cascade_depth_results = []
    for n_levels in [2, 3, 4, 5, 6]:
        # geometric tooth-count progression r=7, with r=10 radii progression
        tooth_counts = [7 ** (i + 1) for i in range(n_levels)]
        # cap each tooth count at 1024 to keep computation tractable
        tooth_counts = [min(t, 1024) for t in tooth_counts]
        # geometric radii spanning a wide range
        radii_min = 1e-3
        radii_max = 1e3
        radii = [
            radii_min * (radii_max / radii_min) ** (i / max(n_levels - 1, 1))
            for i in range(n_levels)
        ]
        try:
            eigs_d = gear_cascade_eigenvalues(
                tooth_counts=tooth_counts,
                radii=radii,
                topN=150,
            )
            span = measure_orders_of_magnitude_span(eigs_d)
            cascade_depth_results.append({
                "phase": "cascade_depth_scaling",
                "n_levels": n_levels,
                "tooth_counts": tooth_counts,
                "radii_min": float(min(radii)),
                "radii_max": float(max(radii)),
                "radii_geometric_span_orders": float(math.log10(max(radii) / min(radii))),
                "spectrum_log_span": float(span["log_span"]),
                "n_eigs": int(span["n_eigs"]),
                "lambda_min": float(span["min"]),
                "lambda_max": float(span["max"]),
            })
        except Exception as e:
            cascade_depth_results.append({
                "phase": "cascade_depth_scaling",
                "n_levels": n_levels,
                "error": str(e),
            })
    records.extend(cascade_depth_results)

    # ─── (E) Antikythera period-ratio test: real bronze gear-train scaling ─
    # PR #416 §11.6.17 bronze data: 53 × 64 × 64 = 76 year Callippic cycle.
    # 19 × 47 × 127 ratio for Metonic. Test how a literal Antikythera-bronze
    # gear cascade composition spans across period ratios.
    antikythera_period_results = []
    # Each named cycle's tooth-counted gear-train, period in days
    antikythera_cycles = [
        {"name": "lunar_anomaly", "teeth": [223, 38], "period_days": 411.78},   # 1 anomalistic month chain
        {"name": "metonic", "teeth": [19, 47, 127], "period_days": 6939.69},    # 19-year
        {"name": "callippic", "teeth": [53, 64, 64], "period_days": 27758.75},  # 76-year
        {"name": "saros", "teeth": [223, 38, 53], "period_days": 6585.32},      # 18-year
        {"name": "exeligmos", "teeth": [3, 223, 38, 53], "period_days": 19755.96},  # 54-year
    ]
    # Span across all cycles
    log_period_min = math.log10(min(c["period_days"] for c in antikythera_cycles))
    log_period_max = math.log10(max(c["period_days"] for c in antikythera_cycles))
    antikythera_period_results.append({
        "phase": "antikythera_period_scaling",
        "n_cycles": len(antikythera_cycles),
        "cycles_named": [c["name"] for c in antikythera_cycles],
        "log_period_span_days": float(log_period_max - log_period_min),
        "max_chain_depth_teeth_per_cycle": max(len(c["teeth"]) for c in antikythera_cycles),
        "max_tooth_count": max(t for c in antikythera_cycles for t in c["teeth"]),
        "min_tooth_count": min(t for c in antikythera_cycles for t in c["teeth"]),
    })
    records.extend(antikythera_period_results)

    # ─── (F) Cross-substrate vocabulary: which Spike #24 primitive classes
    # are instantiated by each substrate at the 3D position? ──
    # Per bonus 5 §4 cross-substrate prediction; per Class A-N vocabulary.
    primitive_consolidation = {
        "M_SG3D": {
            "I_cyclic_group": "absent (fractal is not cyclic)",
            "J_prime_factorisation": "absent (decimation R is polynomial, not factorisation)",
            "K_kepler_shape_pinslot": "absent (no equation-of-centre in fractal Laplacian)",
            "L_graph_Laplacian": "native (Sierpinski Laplacian)",
            "self_similarity": "three-fold (canonical)",
            "multi_scale_span_mechanism": "decimation factor 5 per level",
        },
        "M_GEAR3D": {
            "I_cyclic_group": "native (each C_n_i is ℤ/n_i)",
            "J_prime_factorisation": "native (tooth-count prime structure)",
            "K_kepler_shape_pinslot": "native (gear cascade IS pin-slot algebra per PR #416 §11.6.17)",
            "L_graph_Laplacian": "native (cycle Laplacian)",
            "self_similarity": "available (cascade depth)",
            "multi_scale_span_mechanism": "tooth-count geometric progression + radii geometric progression",
        },
        "M_SMOOTH3D": {
            "I_cyclic_group": "weak (closed-loop topology only)",
            "J_prime_factorisation": "absent (continuous spectrum)",
            "K_kepler_shape_pinslot": "absent",
            "L_graph_Laplacian": "native (anisotropic torus Laplacian)",
            "self_similarity": "absent",
            "multi_scale_span_mechanism": "anisotropic radii only",
        },
    }
    for substrate_name, prims in primitive_consolidation.items():
        records.append({
            "phase": "primitive_consolidation",
            "substrate": substrate_name,
            "I_cyclic_group_instantiation": prims["I_cyclic_group"],
            "J_prime_factorisation_instantiation": prims["J_prime_factorisation"],
            "K_kepler_shape_pinslot_instantiation": prims["K_kepler_shape_pinslot"],
            "L_graph_laplacian_instantiation": prims["L_graph_Laplacian"],
            "self_similarity_status": prims["self_similarity"],
            "multi_scale_span_mechanism": prims["multi_scale_span_mechanism"],
        })

    # ─── (G) Final verdict synthesis ────────────────────────────────────────
    verdict = verdict_synthesis(records)
    records.append({
        "phase": "verdict_synthesis",
        **verdict,
    })

    # ─── Write NDJSON ───────────────────────────────────────────────────────
    with NDJSON_PATH.open("w", encoding="utf-8") as fp:
        for rec in records:
            write_record(rec, fp)

    print(f"# Spike #24 bonus 7 — MFO fractal-requirement probe")
    print(f"# Deterministic seed: {SEED}")
    print(f"# Output: {NDJSON_PATH}")
    print(f"# Records written: {len(records)}")
    print()
    print(f"# Verdict: {verdict.get('verdict', 'INCOMPLETE')}")
    print(f"#   M_SG3D log-span:        {verdict.get('span_M_SG3D', 0.0):.3f}")
    print(f"#   M_GEAR3D log-span:      {verdict.get('span_M_GEAR3D', 0.0):.3f}")
    print(f"#   M_SMOOTH3D log-span:    {verdict.get('span_M_SMOOTH3D', 0.0):.3f}")
    print(f"#   M_SG3D 3-fold CH:       {verdict.get('three_fold_ch_M_SG3D', 0.0):.3f}")
    print(f"#   M_GEAR3D 3-fold CH:     {verdict.get('three_fold_ch_M_GEAR3D', 0.0):.3f}")
    print(f"#   CV diff SG vs GEAR:     {verdict.get('cv_diff_sg_vs_gear', 0.0):.3f}")
    print(f"#   Fiedler diff SG vs GEAR: {verdict.get('fiedler_diff_sg_vs_gear', 0.0):.3f}")
    print(f"#   CC diff SG vs GEAR:     {verdict.get('ccs_diff_sg_vs_gear', 0)}")


if __name__ == "__main__":
    main()
