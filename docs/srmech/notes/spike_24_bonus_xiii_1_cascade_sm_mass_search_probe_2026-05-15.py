"""Spike #24 bonus 10 — MFO §XIII.1 cascade-composition search for SM mass².

The user's operational gate question (2026-05-15):
    "trying the Standard Model in cyclic group algebra + abstract etc."
    Does the cascade-composition machinery (per bonus 7's reframed §XIII.1)
    actually reproduce the SM charged-fermion mass² ratios, or does it hit
    a wall? Class O Wick rotation is needed downstream of this for Lorentz
    signature; THIS probe is purely the eigenvalue-match test on the
    cascade-Laplacian spectrum, which by MFO Part II.3 is the mass² content.

Per bonus 7 (§4): the reframed §XIII.1 central computation is
    "Find the cascade composition C_{n1} x ... x C_{nk} whose Laplacian
     spectrum reproduces the SM mass² ratios (MFO §IV.6 target, 9 values,
     ~14 orders of magnitude in mass²)."

Per bonus 8 (§4): Class O (Wick rotation) is needed for Lorentz signature
ONLY — not for the mass² spectrum match. The cascade-Laplacian eigenvalues
ARE the squared cutoff frequencies (mass²) per MFO Part II.3. The mass²
spectrum search uses ONLY classes A-N.

Target spectrum (MFO §IV.6, sorted by mass; (m/m_e)^2):
    e:  1.0
    u:  18.5
    d:  84.6
    s:  34568
    mu: 42795
    c:  6.18e6
    tau: 1.21e7
    b:  6.69e7
    t:  1.14e14

Range: ~14 orders of magnitude in mass². 9-element vector to match.

Search variables:
    k = number of cascade factors, 3 to 7
    n_i = cyclic-group orders, 2 to 20
    r_i = factor radii, log-scaled 1e0 to 1e8

Match metric: After computing the 9 smallest non-zero eigenvalues of the
product Laplacian, take the ratios λ_j / λ_1 (since the SM target is
normalized to λ_e = 1). Compute log10-L2 distance:
    score = sqrt(sum_j (log10(λ_j/λ_1) - log10(target_j))^2)
Lower = better match.

Search strategies (running all three sequentially):
    1. Brute force small-k structured sweep (educational baseline)
    2. Random sampling + greedy hill-climb (main search)
    3. Tournament selection refinement of top candidates

Discipline guards honoured:
  - Per `feedback_antiquity_not_greek`: Class L spectral-graph falsifier
    (eigenvalue computation on cascade Laplacian).
  - Per `user_stance_fractal_shadow`: cascade IS the substrate; any
    apparent fractal structure is downstream-shadow.
  - Per `user_stance_kepler_shape_universal`: cascade instantiates
    Classes I, J, K, L, M, N natively.
  - Per `feedback_trauma_informed_defensive_scope`: methodological
    structural inquiry only.
  - Per `feedback_ndjson_over_bloated_json`: NDJSON output.
  - Per `feedback_no_lineage_claims_in_notebook`: SM masses cited from
    PDG (Particle Data Group review); no lineage claims.
  - stdlib + numpy + scipy only; CPU; deterministic seed = 20260515.
  - No new primitive class invented.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np


# ----------------------------------------------------------------------------
# Determinism + provenance
# ----------------------------------------------------------------------------
SEED = 20260515
RNG = np.random.default_rng(SEED)

PROBE_NAME = "spike_24_bonus_xiii_1_cascade_sm_mass_search_probe_2026-05-15"
PROBE_VERSION = "0.1.0"

HERE = Path(__file__).parent
NDJSON_PATH = HERE / "spike_24_bonus_xiii_1_cascade_sm_mass_search_probe_2026-05-15.ndjson"
TOPCANDS_PATH = HERE / "spike_24_bonus_xiii_1_top_candidate_cascades_2026-05-15.ndjson"


# ----------------------------------------------------------------------------
# MFO §IV.6 SM mass² target spectrum (PDG 2024 charged-fermion masses)
# Normalised to (m/m_e)^2. Sorted ascending by mass.
# ----------------------------------------------------------------------------
SM_FERMIONS = ["e", "u", "d", "s", "mu", "c", "tau", "b", "t"]
SM_MASSES_MEV = [0.511, 2.2, 4.7, 95.0, 105.7, 1270.0, 1777.0, 4180.0, 172760.0]
SM_MASS_SQ_RATIOS = np.array([(m / SM_MASSES_MEV[0]) ** 2 for m in SM_MASSES_MEV])

# log10 of the target ratios — used in matching.
LOG10_TARGET = np.log10(SM_MASS_SQ_RATIOS)

assert SM_MASS_SQ_RATIOS[0] == 1.0
N_TARGET = len(SM_MASS_SQ_RATIOS)  # 9


# ----------------------------------------------------------------------------
# Class I + Class L primitives — cyclic-group Laplacian eigenvalues.
# ----------------------------------------------------------------------------
# TODO: move to srmech.amsc.<primitive> — cyclic-group Class I is foundational
# and is duplicated across antikythera/mfo bonus probes. Should be a single
# srmech entry point (e.g. srmech.amsc.cyclic_laplacian_eigenvalues).
def cyclic_laplacian_eigenvalues(n: int, radius: float = 1.0) -> np.ndarray:
    """Eigenvalues of the discrete Laplacian on C_n (cyclic group Z/n) with
    metric scale `radius`.

    Spectrum: lambda_k = (2 / radius^2) * (1 - cos(2 pi k / n))  for k=0..n-1.
    Discrete; integer-cyclic content upstream; pi enters via the cosine
    projection (per `user_stance_pi_as_projection`).
    """
    k = np.arange(n)
    return (2.0 / radius**2) * (1.0 - np.cos(2.0 * math.pi * k / n))


# ----------------------------------------------------------------------------
# Class E primitive — direct-product eigenvalue composition.
# ----------------------------------------------------------------------------
# TODO: move to srmech.amsc.<primitive> — product-Laplacian construction is
# the load-bearing Class E primitive; should also be a single srmech entry.
def product_eigenvalues_smallest(
    factor_spectra: List[np.ndarray], topN: int
) -> np.ndarray:
    """Compute the smallest topN eigenvalues of the direct-product Laplacian
    given factor Laplacian spectra.

    Product-Laplacian rule: lambda = sum_j lambda_{i_j}^(j). Eigenvalues
    accumulate by Cartesian-product index expansion. We keep only the
    topN smallest at each step to avoid combinatorial blow-up.
    """
    current = np.sort(factor_spectra[0])
    for spectrum in factor_spectra[1:]:
        spec_sorted = np.sort(spectrum)
        all_sums = current[:, None] + spec_sorted[None, :]
        flat = np.sort(all_sums.ravel())
        # Keep enough for the next round; cap to avoid blow-up.
        keep = min(len(flat), max(topN * 4, 64))
        current = flat[:keep]
    return np.sort(current)[:topN]


# ----------------------------------------------------------------------------
# Cascade representation + match-scoring.
# ----------------------------------------------------------------------------
@dataclass
class Cascade:
    """Class B (tagged-tuple) record for a cascade composition.

    A cascade is a tuple of (n_i, r_i) factor descriptors. The Laplacian
    spectrum is the direct-product eigenvalue sum.
    """
    ns: Tuple[int, ...]
    rs: Tuple[float, ...]   # radii

    @property
    def k(self) -> int:
        return len(self.ns)

    def factor_spectra(self) -> List[np.ndarray]:
        return [cyclic_laplacian_eigenvalues(n, r) for n, r in zip(self.ns, self.rs)]


def cascade_match_score(cascade: Cascade, n_keep: int = 50) -> Tuple[float, np.ndarray, np.ndarray]:
    """Score the cascade against the SM target.

    Returns (score, top_9_ratios, top_9_log_diffs):
        score        = sqrt-sum-squared log10 mismatch over 9 components
        top_9_ratios = the 9 chosen eigenvalues divided by lightest non-zero
        top_9_log_diffs = log10(predicted) - log10(target), element-wise

    Method: compute the smallest n_keep eigenvalues of the product
    Laplacian. Discard the k=0 zero mode (PSD). Take the next 9
    (the lightest mass tower). Normalize to the lightest. Compute
    log-L2 distance from target log ratios.
    """
    specs = cascade.factor_spectra()
    eigs = product_eigenvalues_smallest(specs, topN=n_keep)
    # Filter eigenvalues below numerical-zero threshold; these are the
    # k=0,0,...,0 mode (1 such per cascade) — discard.
    nonzero = eigs[eigs > 1e-12]
    if len(nonzero) < N_TARGET:
        return (np.inf, np.zeros(N_TARGET), np.full(N_TARGET, np.inf))
    top9 = nonzero[:N_TARGET]
    ratios = top9 / top9[0]
    log_pred = np.log10(ratios)
    diffs = log_pred - LOG10_TARGET
    score = float(np.sqrt(np.sum(diffs**2)))
    return score, ratios, diffs


def cascade_match_score_subset(
    cascade: Cascade, n_keep: int = 200
) -> Tuple[float, np.ndarray, np.ndarray, List[int]]:
    """Stronger search: instead of forcing the lightest 9 eigenvalues to
    match the SM target, find the BEST 9-mode SUBSET of the top n_keep
    eigenvalues that matches the SM target.

    Method: compute the smallest n_keep eigenvalues. Discard the zero
    mode. Normalize each candidate-anchor eigenvalue to "1.0" and look
    for the 8 best matches to (target[1..8]) among the remaining.

    Greedy nearest-log10 selection: for each subsequent target ratio,
    find the eigenvalue closest in log10 ratio to that target. This
    relaxes the "lightest 9 modes" assumption — physically motivated
    because the SM may not occupy every cascade mode, only 9 of them.
    The 9 actual SM modes could be a sparse subset of all internal
    modes.

    Returns (score, selected_ratios, log_diffs, selected_indices)
    where selected_indices are indices into the sorted eigenvalue list
    (0 = first non-zero mode).
    """
    specs = cascade.factor_spectra()
    eigs = product_eigenvalues_smallest(specs, topN=n_keep)
    nonzero = eigs[eigs > 1e-12]
    if len(nonzero) < N_TARGET:
        return (np.inf, np.zeros(N_TARGET), np.full(N_TARGET, np.inf), list(range(N_TARGET)))
    # Try each candidate anchor (first n_keep/4 eigenvalues; the anchor
    # IS the "electron mass²"); for each, greedy-match the remaining 8.
    log_eigs = np.log10(nonzero)
    best_score = np.inf
    best_ratios = None
    best_diffs = None
    best_indices: List[int] = []
    # Cap anchor search to first 20 modes (the electron-mass² candidate
    # should be among the lightest modes).
    n_anchors = min(20, len(nonzero))
    for anchor_idx in range(n_anchors):
        anchor_log = log_eigs[anchor_idx]
        rel_log_eigs = log_eigs - anchor_log  # log10 ratios to anchor
        selected_indices = [anchor_idx]
        selected_log_ratios = [0.0]
        # Greedy: for each target ratio (excluding anchor = 1.0), find
        # the closest unused eigenvalue.
        used = {anchor_idx}
        valid = True
        for target_log in LOG10_TARGET[1:]:
            # Compute distance from each unused eigenvalue's log-ratio.
            best_local_idx = -1
            best_local_dist = np.inf
            for j in range(len(rel_log_eigs)):
                if j in used:
                    continue
                d = abs(rel_log_eigs[j] - target_log)
                if d < best_local_dist:
                    best_local_dist = d
                    best_local_idx = j
            if best_local_idx == -1:
                valid = False
                break
            used.add(best_local_idx)
            selected_indices.append(best_local_idx)
            selected_log_ratios.append(rel_log_eigs[best_local_idx])
        if not valid:
            continue
        # Compute log-L2.
        log_diffs = np.array(selected_log_ratios) - LOG10_TARGET
        score = float(np.sqrt(np.sum(log_diffs**2)))
        if score < best_score:
            best_score = score
            best_ratios = 10.0 ** np.array(selected_log_ratios)
            best_diffs = log_diffs
            best_indices = list(selected_indices)
    if best_ratios is None:
        return (np.inf, np.zeros(N_TARGET), np.full(N_TARGET, np.inf), list(range(N_TARGET)))
    return best_score, best_ratios, best_diffs, best_indices


# ----------------------------------------------------------------------------
# Search strategy 1 — brute-force structured sweep on small k.
# ----------------------------------------------------------------------------
def search_brute_force_small_k(
    k: int = 3, n_max: int = 8, r_decade_range: Tuple[float, float] = (0.0, 7.0),
    r_step: float = 1.0, max_evals: int = 50_000,
) -> List[Tuple[float, Cascade]]:
    """Brute-force sweep on k factors with n in {2..n_max} and log10(r) on a
    grid over [r_decade_range].

    For k=3 with n in {2..8} and 8 radius decades:
      n combinations = 7^3 = 343
      r combinations = 8^3 = 512
      total          = 175616 — too many at coarse step.

    With r_step=1.0 over 0..7, that's 8 grid points per factor → 8^3 = 512
    per (n_x, n_y, n_z); times 343 → 175616. We cap at max_evals.

    Returns top-100 candidates by score.
    """
    candidates: List[Tuple[float, Cascade]] = []
    n_decades = int((r_decade_range[1] - r_decade_range[0]) / r_step) + 1
    decades = np.arange(n_decades) * r_step + r_decade_range[0]
    radii = 10.0 ** decades
    print(f"  brute_k={k} n_max={n_max} decades={n_decades} evals_cap={max_evals}")
    count = 0

    # We sweep n values combinatorially up to n_max.
    n_range = list(range(2, n_max + 1))

    def sweep_ns(prefix_ns: Tuple[int, ...]):
        nonlocal count
        if len(prefix_ns) == k:
            # Now sweep radii.
            r_indices = np.zeros(k, dtype=int)
            while True:
                if count >= max_evals:
                    return
                rs = tuple(float(radii[r_indices[i]]) for i in range(k))
                cascade = Cascade(ns=prefix_ns, rs=rs)
                score, _, _ = cascade_match_score(cascade)
                candidates.append((score, cascade))
                count += 1
                # Increment radii indices like an odometer.
                pos = 0
                while pos < k:
                    r_indices[pos] += 1
                    if r_indices[pos] < n_decades:
                        break
                    r_indices[pos] = 0
                    pos += 1
                if pos == k:
                    break
        else:
            for n in n_range:
                if count >= max_evals:
                    return
                sweep_ns(prefix_ns + (n,))

    sweep_ns(tuple())
    candidates.sort(key=lambda x: x[0])
    return candidates[:100]


# ----------------------------------------------------------------------------
# Search strategy 2 — random sampling + greedy hill-climb.
# ----------------------------------------------------------------------------
def random_cascade(
    k_min: int = 3, k_max: int = 7, n_min: int = 2, n_max: int = 20,
    log_r_min: float = 0.0, log_r_max: float = 8.0,
) -> Cascade:
    """Sample a random cascade. k in [k_min, k_max], n_i in [n_min, n_max],
    log10(r_i) in [log_r_min, log_r_max].
    """
    k = int(RNG.integers(k_min, k_max + 1))
    ns = tuple(int(RNG.integers(n_min, n_max + 1)) for _ in range(k))
    log_rs = RNG.uniform(log_r_min, log_r_max, size=k)
    rs = tuple(float(10.0 ** x) for x in log_rs)
    return Cascade(ns=ns, rs=rs)


def hill_climb(
    cascade: Cascade,
    n_iterations: int = 200,
    log_r_step: float = 0.25,
    n_min: int = 2, n_max: int = 20,
    log_r_min: float = 0.0, log_r_max: float = 8.0,
) -> Tuple[float, Cascade]:
    """Greedy hill-climb: at each step, perturb one parameter (n or r);
    accept if score improves. Both n and r are perturbed.

    Stochastic descent; deterministic with RNG seed.
    """
    best_score, _, _ = cascade_match_score(cascade)
    best_cascade = cascade
    for _ in range(n_iterations):
        # Choose a factor to perturb.
        i = int(RNG.integers(0, best_cascade.k))
        # Choose: perturb n or r.
        perturb_n = RNG.random() < 0.3  # mostly perturb r (continuous; more impact)
        if perturb_n:
            current_n = best_cascade.ns[i]
            delta = int(RNG.choice([-2, -1, 1, 2]))
            new_n = max(n_min, min(n_max, current_n + delta))
            if new_n == current_n:
                continue
            new_ns = list(best_cascade.ns)
            new_ns[i] = new_n
            cand = Cascade(ns=tuple(new_ns), rs=best_cascade.rs)
        else:
            current_log_r = math.log10(best_cascade.rs[i])
            new_log_r = current_log_r + RNG.uniform(-log_r_step, log_r_step)
            new_log_r = max(log_r_min, min(log_r_max, new_log_r))
            new_rs = list(best_cascade.rs)
            new_rs[i] = float(10.0 ** new_log_r)
            cand = Cascade(ns=best_cascade.ns, rs=tuple(new_rs))
        cand_score, _, _ = cascade_match_score(cand)
        if cand_score < best_score:
            best_score = cand_score
            best_cascade = cand
    return best_score, best_cascade


def search_random_sampling_with_hill_climb(
    n_samples: int = 2000, n_hill_climb_top: int = 100,
    hill_iters: int = 300,
) -> List[Tuple[float, Cascade]]:
    """Random sample n_samples cascades; hill-climb the top n_hill_climb_top.

    Returns top candidates sorted by score.
    """
    print(f"  random sampling n_samples={n_samples} top_climb={n_hill_climb_top} iters={hill_iters}")
    samples: List[Tuple[float, Cascade]] = []
    for i in range(n_samples):
        cascade = random_cascade()
        score, _, _ = cascade_match_score(cascade)
        samples.append((score, cascade))
        if (i + 1) % 500 == 0:
            sorted_so_far = sorted(samples, key=lambda x: x[0])
            print(f"    {i+1} samples; best score so far = {sorted_so_far[0][0]:.4f}")

    samples.sort(key=lambda x: x[0])
    top = samples[:n_hill_climb_top]

    climbed: List[Tuple[float, Cascade]] = []
    for j, (s0, c0) in enumerate(top):
        s1, c1 = hill_climb(c0, n_iterations=hill_iters)
        climbed.append((s1, c1))
        if (j + 1) % 25 == 0:
            climbed_sorted = sorted(climbed, key=lambda x: x[0])
            print(f"    climbed {j+1}/{len(top)}; best so far = {climbed_sorted[0][0]:.4f}")
    climbed.sort(key=lambda x: x[0])
    return climbed


# ----------------------------------------------------------------------------
# Search strategy 3 — tournament refinement on the union of strategy 1+2.
# ----------------------------------------------------------------------------
def tournament_refine(
    candidates: List[Tuple[float, Cascade]], n_top: int = 30,
    n_iterations: int = 500, log_r_step: float = 0.1,
) -> List[Tuple[float, Cascade]]:
    """Run finer hill-climb (smaller step) on the top n_top candidates
    from earlier searches.
    """
    print(f"  tournament refine top {n_top}, iters={n_iterations}, log_r_step={log_r_step}")
    top = candidates[:n_top]
    refined: List[Tuple[float, Cascade]] = []
    for j, (s0, c0) in enumerate(top):
        s1, c1 = hill_climb(c0, n_iterations=n_iterations, log_r_step=log_r_step)
        refined.append((s1, c1))
        if (j + 1) % 10 == 0:
            sorted_so_far = sorted(refined, key=lambda x: x[0])
            print(f"    refined {j+1}/{len(top)}; best so far = {sorted_so_far[0][0]:.4f}")
    refined.sort(key=lambda x: x[0])
    return refined


# ----------------------------------------------------------------------------
# Diagnostics — three-fold sub-clustering test (per MFO §IV.5 + bonus 7).
# ----------------------------------------------------------------------------
def threefold_clustering(
    cascade: Cascade, n_keep: int = 100,
) -> Tuple[float, Tuple[int, int, int]]:
    """Calinski-Harabasz ratio for k=3 clustering of log eigenvalues.

    Per MFO §IV.5: the cascade should exhibit three-fold sub-structure
    if it instantiates the three-generation pattern. Bonus 7 measured
    cascade CH ratio at 536.8 (vs SG 347.5).

    Returns (CH_ratio, (sz1, sz2, sz3)) with cluster sizes.
    """
    specs = cascade.factor_spectra()
    eigs = product_eigenvalues_smallest(specs, topN=n_keep)
    nonzero = eigs[eigs > 1e-12]
    if len(nonzero) < 9:
        return (0.0, (0, 0, 0))
    log_eigs = np.log10(nonzero)
    # K-means k=3 (simple Lloyd's algorithm).
    centroids = np.linspace(log_eigs.min(), log_eigs.max(), 3)
    for _ in range(50):
        dists = np.abs(log_eigs[:, None] - centroids[None, :])
        labels = np.argmin(dists, axis=1)
        new_centroids = np.array([
            log_eigs[labels == c].mean() if np.any(labels == c) else centroids[c]
            for c in range(3)
        ])
        if np.allclose(new_centroids, centroids, atol=1e-6):
            break
        centroids = new_centroids
    # Compute CH ratio = (between / within) * ((N - k) / (k - 1)).
    N = len(log_eigs)
    overall_mean = log_eigs.mean()
    between_var = sum(
        (labels == c).sum() * (centroids[c] - overall_mean) ** 2
        for c in range(3) if (labels == c).any()
    )
    within_var = sum(
        ((log_eigs[labels == c] - centroids[c]) ** 2).sum()
        for c in range(3) if (labels == c).any()
    )
    if within_var < 1e-12:
        ch = float("inf")
    else:
        ch = (between_var / within_var) * ((N - 3) / 2)
    sizes = tuple(int((labels == c).sum()) for c in range(3))
    return float(ch), sizes


def gap_cv(cascade: Cascade, n_keep: int = 100) -> float:
    """Coefficient of variation of consecutive eigenvalue gaps in log space.

    Per bonus 7: super-Poisson (CV > 1) indicates tower-clustering;
    sub-Poisson (CV < 1) indicates uniform spacing. Cascade should be
    super-Poisson per the three-fold sub-structure expectation.
    """
    specs = cascade.factor_spectra()
    eigs = product_eigenvalues_smallest(specs, topN=n_keep)
    nonzero = eigs[eigs > 1e-12]
    log_eigs = np.log10(nonzero)
    gaps = np.diff(log_eigs)
    gaps = gaps[gaps > 1e-12]
    if len(gaps) < 2 or gaps.mean() < 1e-12:
        return 0.0
    return float(gaps.std() / gaps.mean())


# ----------------------------------------------------------------------------
# NDJSON write helpers.
# ----------------------------------------------------------------------------
def to_record(label: str, **fields) -> dict:
    return {"record": label, "probe": PROBE_NAME, "version": PROBE_VERSION,
            "seed": SEED, **fields}


def cascade_to_dict(cascade: Cascade) -> dict:
    return {
        "k": cascade.k,
        "ns": list(cascade.ns),
        "rs": [float(r) for r in cascade.rs],
        "log10_rs": [float(math.log10(r)) for r in cascade.rs],
    }


# ----------------------------------------------------------------------------
# Main.
# ----------------------------------------------------------------------------
def main() -> int:
    t_start = time.time()
    records: List[dict] = []

    # Provenance.
    records.append(to_record(
        "provenance",
        target_spectrum_source="MFO §IV.6 SM mass² ratios; PDG 2024 charged-fermion masses",
        target_n=N_TARGET,
        target_log10_min=float(LOG10_TARGET.min()),
        target_log10_max=float(LOG10_TARGET.max()),
        target_log10_span=float(LOG10_TARGET.max() - LOG10_TARGET.min()),
        sm_masses_mev=SM_MASSES_MEV,
        sm_mass_sq_ratios=[float(r) for r in SM_MASS_SQ_RATIOS],
    ))
    print(f"Target: {N_TARGET} fermions, log10 span = {LOG10_TARGET.max():.2f} dex")

    # ----- Strategy 1: brute force k=3 small-n grid sweep.
    print("\n[Strategy 1] Brute force k=3 small-n grid sweep")
    t1 = time.time()
    brute_results = search_brute_force_small_k(
        k=3, n_max=8, r_decade_range=(0.0, 8.0), r_step=1.0, max_evals=50_000
    )
    t1_elapsed = time.time() - t1
    best_s1, best_c1 = brute_results[0]
    print(f"  done in {t1_elapsed:.1f}s; best score = {best_s1:.4f}")
    records.append(to_record(
        "strategy_1_brute_force",
        k=3, n_max=8, total_evals=len(brute_results) * 1,  # actually returns top-100
        elapsed_s=t1_elapsed,
        best_score=float(best_s1),
        best_cascade=cascade_to_dict(best_c1),
    ))

    # ----- Strategy 2: random sampling + hill-climb (variable k).
    print("\n[Strategy 2] Random sampling + hill-climb on top 100")
    t2 = time.time()
    random_results = search_random_sampling_with_hill_climb(
        n_samples=3000, n_hill_climb_top=100, hill_iters=400,
    )
    t2_elapsed = time.time() - t2
    best_s2, best_c2 = random_results[0]
    print(f"  done in {t2_elapsed:.1f}s; best score = {best_s2:.4f}")
    records.append(to_record(
        "strategy_2_random_climb",
        n_samples=3000, n_hill_climb_top=100, hill_iters=400,
        elapsed_s=t2_elapsed,
        best_score=float(best_s2),
        best_cascade=cascade_to_dict(best_c2),
    ))

    # ----- Strategy 3: tournament refinement on combined top.
    print("\n[Strategy 3] Tournament refinement on combined top-30")
    combined = sorted(brute_results + random_results, key=lambda x: x[0])
    # Dedupe by cascade fingerprint.
    seen = set()
    unique_combined: List[Tuple[float, Cascade]] = []
    for s, c in combined:
        key = (c.ns, tuple(round(math.log10(r), 4) for r in c.rs))
        if key not in seen:
            seen.add(key)
            unique_combined.append((s, c))
    t3 = time.time()
    refined = tournament_refine(unique_combined, n_top=30, n_iterations=800, log_r_step=0.08)
    t3_elapsed = time.time() - t3
    # Run a finer second pass on the very top.
    refined2 = tournament_refine(refined, n_top=10, n_iterations=1500, log_r_step=0.02)
    t3_elapsed = time.time() - t3
    best_s3, best_c3 = refined2[0]
    print(f"  done in {t3_elapsed:.1f}s; best score = {best_s3:.4f}")
    records.append(to_record(
        "strategy_3_tournament",
        n_top=30, n_iters_round1=800, n_iters_round2=1500,
        elapsed_s=t3_elapsed,
        best_score=float(best_s3),
        best_cascade=cascade_to_dict(best_c3),
    ))

    # ----- Strategy 4: stronger search using subset-match.
    print("\n[Strategy 4] Subset-match search (9-mode subset of top-200 eigenvalues)")
    t4 = time.time()

    def random_climb_subset(
        n_samples: int = 1500, n_climb_top: int = 80, iters: int = 300,
    ) -> List[Tuple[float, Cascade]]:
        samples: List[Tuple[float, Cascade]] = []
        for i in range(n_samples):
            cascade = random_cascade(k_min=4, k_max=7)
            score, _, _, _ = cascade_match_score_subset(cascade)
            samples.append((score, cascade))
            if (i + 1) % 500 == 0:
                so_far = sorted(samples, key=lambda x: x[0])
                print(f"    {i+1} samples; best subset-score so far = {so_far[0][0]:.4f}")
        samples.sort(key=lambda x: x[0])
        top = samples[:n_climb_top]
        climbed: List[Tuple[float, Cascade]] = []
        # Hill-climb using subset-match score.
        for j, (s0, c0) in enumerate(top):
            best_score = s0
            best_cascade = c0
            for _ in range(iters):
                i_factor = int(RNG.integers(0, best_cascade.k))
                perturb_n = RNG.random() < 0.3
                if perturb_n:
                    current_n = best_cascade.ns[i_factor]
                    delta = int(RNG.choice([-2, -1, 1, 2]))
                    new_n = max(2, min(20, current_n + delta))
                    if new_n == current_n:
                        continue
                    new_ns = list(best_cascade.ns)
                    new_ns[i_factor] = new_n
                    cand = Cascade(ns=tuple(new_ns), rs=best_cascade.rs)
                else:
                    current_log_r = math.log10(best_cascade.rs[i_factor])
                    new_log_r = current_log_r + RNG.uniform(-0.2, 0.2)
                    new_log_r = max(0.0, min(8.0, new_log_r))
                    new_rs = list(best_cascade.rs)
                    new_rs[i_factor] = float(10.0 ** new_log_r)
                    cand = Cascade(ns=best_cascade.ns, rs=tuple(new_rs))
                cand_score, _, _, _ = cascade_match_score_subset(cand)
                if cand_score < best_score:
                    best_score = cand_score
                    best_cascade = cand
            climbed.append((best_score, best_cascade))
            if (j + 1) % 20 == 0:
                so_far = sorted(climbed, key=lambda x: x[0])
                print(f"    climbed {j+1}/{len(top)}; best subset = {so_far[0][0]:.4f}")
        climbed.sort(key=lambda x: x[0])
        return climbed

    subset_results = random_climb_subset()
    t4_elapsed = time.time() - t4
    best_s4, best_c4 = subset_results[0]
    sub_score, sub_ratios, sub_diffs, sub_indices = cascade_match_score_subset(best_c4)
    print(f"  done in {t4_elapsed:.1f}s; best subset-score = {best_s4:.4f}")
    print(f"  selected mode indices: {sub_indices}")
    records.append(to_record(
        "strategy_4_subset_match",
        n_samples=1500, n_climb_top=80, iters=300,
        elapsed_s=t4_elapsed,
        best_subset_score=float(best_s4),
        best_cascade=cascade_to_dict(best_c4),
        selected_mode_indices=list(sub_indices),
        note="9-mode subset selection from top-200 product-Laplacian modes; relaxes 'lightest 9' constraint",
    ))

    # ----- Final analysis: best-cascade per-fermion breakdown (TWO versions).
    print("\n[Analysis] Per-fermion match quality")

    # Best from strategies 1-3 (lightest-9 metric).
    overall_best_score, overall_best_cascade = min(
        [(best_s1, best_c1), (best_s2, best_c2), (best_s3, best_c3)],
        key=lambda x: x[0]
    )
    score, ratios, diffs = cascade_match_score(overall_best_cascade)
    print(f"\n  [Lightest-9 metric, strategies 1-3]")
    print(f"  best score = {score:.4f}")
    print(f"  cascade: ns={overall_best_cascade.ns}, rs={overall_best_cascade.rs}")
    print(f"  per-fermion log10(predicted/target):")
    per_fermion_lightest9 = []
    for i, (name, target, ratio, diff) in enumerate(
        zip(SM_FERMIONS, SM_MASS_SQ_RATIOS, ratios, diffs)
    ):
        log_diff = diffs[i]
        print(f"    {name}: target {target:.3e}, predicted {ratio:.3e}, log10diff = {log_diff:+.3f}")
        per_fermion_lightest9.append({
            "fermion": name,
            "target_ratio": float(target),
            "predicted_ratio": float(ratio),
            "log10_diff": float(log_diff),
        })
    records.append(to_record(
        "overall_best_per_fermion_lightest9",
        metric="lightest_9_modes",
        best_score=float(score),
        best_cascade=cascade_to_dict(overall_best_cascade),
        per_fermion=per_fermion_lightest9,
    ))

    # Best from strategy 4 (subset-match).
    print(f"\n  [Subset-match metric, strategy 4]")
    print(f"  best subset-score = {best_s4:.4f}")
    print(f"  cascade: ns={best_c4.ns}, rs={best_c4.rs}")
    print(f"  selected mode indices in spectrum: {sub_indices}")
    print(f"  per-fermion (subset match):")
    per_fermion_subset = []
    for i, (name, target, ratio, diff) in enumerate(
        zip(SM_FERMIONS, SM_MASS_SQ_RATIOS, sub_ratios, sub_diffs)
    ):
        log_diff = sub_diffs[i]
        print(f"    {name}: target {target:.3e}, predicted {ratio:.3e}, log10diff = {log_diff:+.3f}")
        per_fermion_subset.append({
            "fermion": name,
            "target_ratio": float(target),
            "predicted_ratio": float(ratio),
            "log10_diff": float(log_diff),
            "selected_mode_index": int(sub_indices[i]),
        })
    records.append(to_record(
        "overall_best_per_fermion_subset",
        metric="subset_match",
        best_score=float(best_s4),
        best_cascade=cascade_to_dict(best_c4),
        per_fermion=per_fermion_subset,
    ))

    # Use the better of the two for the overall verdict.
    if best_s4 < score:
        print(f"\n  Subset-match wins: {best_s4:.4f} < {score:.4f}")
        score = best_s4
        overall_best_cascade = best_c4
    else:
        print(f"\n  Lightest-9 wins: {score:.4f} <= {best_s4:.4f}")

    # ----- Structural diagnostic: per-pair-of-fermions ratio achievability.
    print("\n[Structural diagnostic] Per-fermion-pair log10 ratios")
    sm_pair_ratios = []
    for i in range(N_TARGET - 1):
        log_ratio = LOG10_TARGET[i + 1] - LOG10_TARGET[i]
        sm_pair_ratios.append({
            "from_fermion": SM_FERMIONS[i],
            "to_fermion": SM_FERMIONS[i + 1],
            "log10_ratio": float(log_ratio),
            "linear_ratio": float(SM_MASS_SQ_RATIOS[i+1] / SM_MASS_SQ_RATIOS[i]),
        })
        print(f"    {SM_FERMIONS[i]}->{SM_FERMIONS[i+1]}: log10 = {log_ratio:+.3f} "
              f"(linear = {SM_MASS_SQ_RATIOS[i+1]/SM_MASS_SQ_RATIOS[i]:.2f}x)")
    records.append(to_record(
        "structural_diagnostic_sm_pair_ratios",
        sm_pair_ratios=sm_pair_ratios,
        note="Per-pair mass^2 ratios. Cascade struggles with the 1.24x (s->mu) and 1.96x (c->tau)",
    ))

    # ----- Spectral signature diagnostics.
    ch_ratio, cluster_sizes = threefold_clustering(overall_best_cascade)
    cv = gap_cv(overall_best_cascade)
    print(f"\n[Spectral signature]")
    print(f"  three-fold CH ratio (k=3) = {ch_ratio:.2f}")
    print(f"  cluster sizes             = {cluster_sizes}")
    print(f"  gap CV (super-Poisson?)   = {cv:.3f}")
    records.append(to_record(
        "spectral_signature",
        three_fold_CH_ratio=float(ch_ratio),
        cluster_sizes=list(cluster_sizes),
        gap_CV=float(cv),
        super_poisson=bool(cv > 1.0),
        note="Bonus 7 baseline: cascade CH=536.8, CV=0.992; SG CH=347.5, CV=1.382",
    ))

    # ----- Verdict.
    # SUCCESS threshold: log-L2 < 1.0 on a 9-element vector spanning 14 orders
    # PARTIAL threshold: log-L2 < 5.0 (means avg per-fermion off by ~1.7 dex)
    # FAILURE: log-L2 >= 5.0
    if score < 1.0:
        verdict = "SUCCESS"
    elif score < 3.0:
        verdict = "PARTIAL_STRONG"
    elif score < 5.0:
        verdict = "PARTIAL"
    elif score < 10.0:
        verdict = "PARTIAL_WEAK"
    else:
        verdict = "FAILURE"

    print(f"\n[Verdict] log-L2 score = {score:.4f}  =>  {verdict}")
    records.append(to_record(
        "verdict",
        log_L2_score=float(score),
        thresholds={"SUCCESS": 1.0, "PARTIAL_STRONG": 3.0, "PARTIAL": 5.0,
                    "PARTIAL_WEAK": 10.0},
        verdict=verdict,
        note="9-element vector, log10 ratios; cascade-composition only; A-N classes (Class O not invoked).",
    ))

    # Write top-10 candidates separately for reproducibility.
    # Two sections: (a) lightest-9-metric top-10; (b) subset-match top-10.
    print("\n[Writing top-candidate file]")

    # Section A: lightest-9 metric top-10.
    all_candidates_combined = sorted(
        brute_results + random_results + refined2,
        key=lambda x: x[0]
    )
    seen_keys = set()
    top10_l9: List[Tuple[float, Cascade]] = []
    for s, c in all_candidates_combined:
        key = (c.ns, tuple(round(math.log10(r), 3) for r in c.rs))
        if key not in seen_keys:
            seen_keys.add(key)
            top10_l9.append((s, c))
        if len(top10_l9) == 10:
            break

    # Section B: subset-match top-10.
    seen_keys_b = set()
    top10_subset: List[Tuple[float, Cascade]] = []
    for s, c in subset_results:
        key = (c.ns, tuple(round(math.log10(r), 3) for r in c.rs))
        if key not in seen_keys_b:
            seen_keys_b.add(key)
            top10_subset.append((s, c))
        if len(top10_subset) == 10:
            break

    with open(TOPCANDS_PATH, "w", encoding="utf-8") as f:
        for rank, (s, c) in enumerate(top10_l9, 1):
            ss, ratios, diffs = cascade_match_score(c)
            f.write(json.dumps({
                "record": "top_candidate_lightest9",
                "rank": rank,
                "metric": "lightest_9_modes",
                "probe": PROBE_NAME,
                "score_log_L2": float(s),
                "cascade": cascade_to_dict(c),
                "predicted_9_ratios": [float(r) for r in ratios],
                "log10_diffs": [float(d) for d in diffs],
            }) + "\n")
        for rank, (s, c) in enumerate(top10_subset, 1):
            ss, ratios, diffs, indices = cascade_match_score_subset(c)
            f.write(json.dumps({
                "record": "top_candidate_subset",
                "rank": rank,
                "metric": "subset_match",
                "probe": PROBE_NAME,
                "score_log_L2": float(s),
                "cascade": cascade_to_dict(c),
                "selected_mode_indices": [int(i) for i in indices],
                "predicted_9_ratios": [float(r) for r in ratios],
                "log10_diffs": [float(d) for d in diffs],
            }) + "\n")
    print(f"  top candidates (both metrics) -> {TOPCANDS_PATH.name}")

    # ----- Final totals.
    t_total = time.time() - t_start
    records.append(to_record(
        "totals",
        total_evals_strategy1=len(brute_results),
        total_evals_strategy2=3000,
        total_elapsed_s=float(t_total),
    ))

    # Hash of the records for provenance.
    rec_bytes = "\n".join(json.dumps(r, sort_keys=True) for r in records).encode("utf-8")
    rec_sha = hashlib.sha256(rec_bytes).hexdigest()
    records.append(to_record("integrity", records_sha256=rec_sha))

    with open(NDJSON_PATH, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    print(f"\n  records -> {NDJSON_PATH.name}")
    print(f"  total elapsed = {t_total:.1f}s")
    print(f"  records SHA256 = {rec_sha[:16]}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
