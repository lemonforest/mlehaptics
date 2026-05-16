"""Spike #24 bonus 13 — Active-count statistical-significance verification.

The bonus 12 audit-summary surfaced a candidate structural finding (its §10
"the one surprise"): the top-10 bonus-10 cascades that match SM mass^2 ratios
at log-L2 <= ~1.0 dex via subset-match exhibit **effective-active-count in
{3, 4}** with **8/10 = exactly 4**. The candidate claim: 4 matches SM
gauge-group rank (rank SU(3) + rank SU(2) + rank U(1) = 2 + 1 + 1 = 4).

This probe verifies the candidate by computing the active-count distribution
under a null hypothesis (random cascades subset-matching random targets) and
comparing bonus 10's observed {3:2, 4:8} against the null.

Methodology (6 steps):

  Step 1 - Random cascade generation.
    N = 1000+ random cascades: 4-6 cyclic factors, n_i in {2,3,...,16},
    radii log-uniform in [1.0, 1e6] (same range as bonus 10 best).
    For each, compute lowest-200 product-Laplacian spectrum.

  Step 2 - Random target generation.
    M = 100+ random 9-element target vectors, log-uniform over 11 decades
    (same span as SM mass^2 target).

  Step 3 - Active-count of matched 9 modes.
    For each (cascade, target), greedy subset-match the 9 modes; count
    factors with >=1 non-trivial mode-index in the matched subset.

  Step 4 - Significance test.
    Compare bonus-10's {3: 2, 4: 8} against random ensemble. Compute
    p-value (binomial for the >= 8/10 = 4 statistic).

  Step 5 - Robustness checks.
    Vary cascade size (4/5/6/7 factors); reflection-invariance verification;
    tower-truncation dependence (top-200 vs top-500 vs full tower).

  Step 6 - SM-specific check.
    Rerun the top-10 SM cascades and verify bonus 12's {3:2, 4:8} numbers.

Verdict outcomes:
  CONFIRMED   : p < 0.01 (preferably) / p < 0.05 (acceptable)
  UNCERTAIN   : p in [0.05, 0.2]
  COINCIDENCE : p > 0.2

Discipline guards:
  - Per feedback_antiquity_not_greek: Class L Laplacian eigenvalue
    computation is the falsifier substrate.
  - Per feedback_trauma_informed_defensive_scope: structural inquiry only.
  - Per feedback_ndjson_over_bloated_json: NDJSON outputs.
  - Per feedback_no_lineage_claims_in_notebook: no external lineage claims.
  - stdlib + numpy + scipy only; CPU; deterministic seed = 20260515.
  - No new primitive class invented.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Dict, Optional

import numpy as np


# ----------------------------------------------------------------------------
# Determinism + provenance
# ----------------------------------------------------------------------------
SEED = 20260515
RNG = np.random.default_rng(SEED)

PROBE_NAME = "spike_24_bonus_13_active_count_significance_probe_2026-05-15"
PROBE_VERSION = "0.1.0"

HERE = Path(__file__).parent
NDJSON_PATH = HERE / "spike_24_bonus_13_active_count_significance_probe_2026-05-15.ndjson"
PIDS_PATH = HERE / "spike_24_bonus_13_pids.txt"


# ----------------------------------------------------------------------------
# SM target spectrum (same as bonus 10).
# ----------------------------------------------------------------------------
SM_FERMIONS = ["e", "u", "d", "s", "mu", "c", "tau", "b", "t"]
SM_MASSES_MEV = [0.511, 2.2, 4.7, 95.0, 105.7, 1270.0, 1777.0, 4180.0, 172760.0]
SM_MASS_SQ_RATIOS = np.array([(m / SM_MASSES_MEV[0]) ** 2 for m in SM_MASSES_MEV])
LOG10_SM_TARGET = np.log10(SM_MASS_SQ_RATIOS)
SM_TARGET_SPAN_DEC = float(LOG10_SM_TARGET[-1] - LOG10_SM_TARGET[0])  # 11.06 dex
N_TARGET = len(SM_MASS_SQ_RATIOS)  # 9


# ----------------------------------------------------------------------------
# Class I + Class L primitives — cyclic-group Laplacian eigenvalues.
# (Same primitive as bonus 10, returned with k-indices so we can identify
# which factor index activated each mode.)
# ----------------------------------------------------------------------------
def cyclic_laplacian_spectrum(n: int, radius: float) -> Tuple[np.ndarray, np.ndarray]:
    """Cyclic-group Laplacian spectrum on C_n with metric scale `radius`.

    Returns (eigvals, k_indices):
      eigvals[k] = (2 / radius^2) * (1 - cos(2*pi*k/n))  for k = 0..n-1
      k_indices[k] = k  (the mode-index)
    """
    k = np.arange(n)
    eigvals = (2.0 / radius**2) * (1.0 - np.cos(2.0 * math.pi * k / n))
    return eigvals, k


# ----------------------------------------------------------------------------
# Class E primitive — product Laplacian eigenvalue composition.
# This version tracks k-tuples (which mode-index in each factor produced
# each eigenvalue) so we can compute active-count per matched mode.
# ----------------------------------------------------------------------------
def product_eigenvalues_with_ktuples(
    factor_data: List[Tuple[np.ndarray, np.ndarray]], topN: int
) -> Tuple[np.ndarray, np.ndarray]:
    """Compute the smallest topN eigenvalues + their k-tuples.

    factor_data: list of (eigvals, k_indices) per factor.

    Returns (eigvals_sorted, ktuples_sorted):
      eigvals_sorted: shape (topN,)
      ktuples_sorted: shape (topN, K) where K = number of factors

    Uses Cartesian-product expansion with kept-smallest pruning each step.
    """
    eigs0, ks0 = factor_data[0]
    # Sort initial factor.
    order = np.argsort(eigs0)
    current_eigs = eigs0[order]
    current_ks = ks0[order].reshape(-1, 1)  # (n_0, 1) -- each row is a k-tuple

    for f_idx in range(1, len(factor_data)):
        eigs_f, ks_f = factor_data[f_idx]
        n_f = len(eigs_f)
        order_f = np.argsort(eigs_f)
        eigs_f_sorted = eigs_f[order_f]
        ks_f_sorted = ks_f[order_f]

        # Outer-sum with broadcasting.
        all_sums = current_eigs[:, None] + eigs_f_sorted[None, :]  # (M, n_f)
        flat = all_sums.ravel()
        flat_order = np.argsort(flat)
        # Cap.
        keep = min(len(flat), max(topN * 4, 64))
        keep_idx = flat_order[:keep]

        # Recover the (i, j) coords.
        i_idx = keep_idx // n_f
        j_idx = keep_idx % n_f

        new_eigs = flat[keep_idx]
        # Build new k-tuples: rows are concat(current_ks[i], ks_f_sorted[j]).
        new_ks = np.hstack([
            current_ks[i_idx],
            ks_f_sorted[j_idx].reshape(-1, 1)
        ])
        current_eigs = new_eigs
        current_ks = new_ks

    # Final sort by eigenvalue.
    final_order = np.argsort(current_eigs)[:topN]
    return current_eigs[final_order], current_ks[final_order]


# ----------------------------------------------------------------------------
# Subset-match (same algorithm as bonus 10) with k-tuple tracking.
# Returns the active-count of the matched 9 modes.
# ----------------------------------------------------------------------------
def subset_match_with_active_count(
    eigvals: np.ndarray,
    ktuples: np.ndarray,
    factor_ns: Tuple[int, ...],
    log10_target: np.ndarray,
    n_anchors: int = 20,
) -> Tuple[float, List[int], int]:
    """Greedy subset-match: return (score, selected_indices, active_count).

    active_count = number of factors with >=1 non-trivial k-index in the
    matched 9 modes (counting k_i != 0). NOTE: this is the greedy-tie-
    break-dependent count and is NOT reflection-invariant when the
    cascade has eigenvalue degeneracies (different k-tuples producing
    the same eigenvalue). Bonus 12 §5 acknowledged this dependency.

    For the cleaner active-count metric, use the optimised variant in
    subset_match_with_active_count_min() below, which over all
    eigenvalue-equivalent k-tuples picks the one minimising active-
    factor count (this is the lower-bound active-count claim — i.e.
    'is there ANY reflection-equivalent representation with this many
    silent factors?').
    """
    # Filter zero modes.
    mask = eigvals > 1e-12
    nonzero_eigs = eigvals[mask]
    nonzero_ks = ktuples[mask]
    if len(nonzero_eigs) < N_TARGET:
        return (np.inf, [], -1)

    log_eigs = np.log10(nonzero_eigs)
    best_score = np.inf
    best_indices: List[int] = []

    n_a = min(n_anchors, len(nonzero_eigs))
    for anchor_idx in range(n_a):
        anchor_log = log_eigs[anchor_idx]
        rel_log_eigs = log_eigs - anchor_log
        selected = [anchor_idx]
        used = {anchor_idx}
        valid = True
        for t_log in log10_target[1:]:
            best_j = -1
            best_d = np.inf
            for j in range(len(rel_log_eigs)):
                if j in used:
                    continue
                d = abs(rel_log_eigs[j] - t_log)
                if d < best_d:
                    best_d = d
                    best_j = j
            if best_j == -1:
                valid = False
                break
            used.add(best_j)
            selected.append(best_j)
        if not valid:
            continue
        sel_log_ratios = np.array([rel_log_eigs[i] for i in selected])
        diffs = sel_log_ratios - log10_target
        score = float(np.sqrt(np.sum(diffs**2)))
        if score < best_score:
            best_score = score
            best_indices = list(selected)

    if not best_indices:
        return (np.inf, [], -1)

    # Compute active-count: per factor, is there at least one matched mode
    # with k_i != 0?
    K = len(factor_ns)
    activations = np.zeros(K, dtype=int)
    for idx in best_indices:
        kt = nonzero_ks[idx]
        for f_i in range(K):
            if kt[f_i] != 0:
                activations[f_i] += 1
    active_count = int(np.sum(activations > 0))
    return best_score, best_indices, active_count


# ----------------------------------------------------------------------------
# Random cascade generator.
# ----------------------------------------------------------------------------
def random_cascade(
    k_factors: int, n_range: Tuple[int, int] = (2, 16),
    radius_decades: Tuple[float, float] = (0.0, 6.0)
) -> Tuple[Tuple[int, ...], Tuple[float, ...]]:
    """Generate a random cascade descriptor: (ns, rs).

    n_i ~ uniform integer in [n_range].
    log10(r_i) ~ uniform real in [radius_decades].
    """
    ns = tuple(int(RNG.integers(n_range[0], n_range[1] + 1)) for _ in range(k_factors))
    rs = tuple(float(10.0 ** RNG.uniform(radius_decades[0], radius_decades[1]))
               for _ in range(k_factors))
    return ns, rs


def random_log_target(span_dec: float = SM_TARGET_SPAN_DEC) -> np.ndarray:
    """Generate a random 9-element log-target spanning ~11 decades.

    Sorted ascending (like SM); anchor = 0.0. The remaining 8 values are
    log-uniform in [0, span_dec], sorted.
    """
    # Sample 8 random log values in [0, span_dec].
    upper = RNG.uniform(0.0, span_dec, size=N_TARGET - 1)
    upper.sort()
    out = np.concatenate([[0.0], upper])
    return out


# ----------------------------------------------------------------------------
# Probe driver.
# ----------------------------------------------------------------------------
@dataclass
class TrialResult:
    cascade_ns: Tuple[int, ...]
    cascade_rs: Tuple[float, ...]
    target_log: List[float]
    score: float
    active_count: int


def run_random_ensemble(
    n_cascades: int,
    targets_per_cascade: int,
    k_factors: int,
    topN: int = 200,
    radius_decades: Tuple[float, float] = (0.0, 6.0),
) -> List[TrialResult]:
    """Generate n_cascades random cascades, each tested against
    targets_per_cascade random targets. Return list of trial results.
    """
    results: List[TrialResult] = []
    for c_i in range(n_cascades):
        ns, rs = random_cascade(k_factors, radius_decades=radius_decades)
        factor_data = [cyclic_laplacian_spectrum(n, r) for n, r in zip(ns, rs)]
        eigs, kts = product_eigenvalues_with_ktuples(factor_data, topN=topN)
        for t_i in range(targets_per_cascade):
            tgt_log = random_log_target()
            score, sel, ac = subset_match_with_active_count(
                eigs, kts, ns, tgt_log
            )
            results.append(TrialResult(
                cascade_ns=ns,
                cascade_rs=rs,
                target_log=list(tgt_log),
                score=score,
                active_count=ac,
            ))
    return results


def active_count_distribution(results: List[TrialResult], max_score: Optional[float] = None) -> Dict[int, int]:
    """Histogram of active-counts (filtered to finite-score trials)."""
    hist: Dict[int, int] = {}
    for r in results:
        if not np.isfinite(r.score) or r.active_count < 0:
            continue
        if max_score is not None and r.score >= max_score:
            continue
        hist[r.active_count] = hist.get(r.active_count, 0) + 1
    return hist


def score_quality_stratified_distribution(results: List[TrialResult]) -> Dict[str, Dict]:
    """Stratify trials by score-band and report active-count hist per band."""
    bands = [(0.0, 1.0), (1.0, 2.0), (2.0, 3.0), (3.0, 100.0)]
    out: Dict[str, Dict] = {}
    for low, high in bands:
        label = f"score_[{low:.1f},{high:.1f})"
        sub = [r for r in results if np.isfinite(r.score) and r.active_count >= 0 and low <= r.score < high]
        hist = {}
        for r in sub:
            hist[r.active_count] = hist.get(r.active_count, 0) + 1
        n_tot = sum(hist.values())
        out[label] = {
            "n_trials": n_tot,
            "histogram": dict(sorted(hist.items())),
            "P_ac_eq_4": hist.get(4, 0) / n_tot if n_tot else None,
            "P_ac_in_34": (hist.get(3, 0) + hist.get(4, 0)) / n_tot if n_tot else None,
            "P_ac_in_345": (hist.get(3, 0) + hist.get(4, 0) + hist.get(5, 0)) / n_tot if n_tot else None,
        }
    return out


# ----------------------------------------------------------------------------
# Significance test.
# ----------------------------------------------------------------------------
def binomial_pvalue_ge_k(n: int, k: int, p: float) -> float:
    """Pr(X >= k | X ~ Binomial(n, p))."""
    from scipy.stats import binom
    # P(X >= k) = 1 - P(X <= k-1) = sf(k-1)
    return float(binom.sf(k - 1, n, p))


# ----------------------------------------------------------------------------
# Top-10 bonus-10 SM-cascade reproduction.
# ----------------------------------------------------------------------------
TOP10_BONUS_10 = [
    {"rank": 1, "ns": (2, 7, 4, 6, 16),
     "rs": (3659.03506590957, 1.0286749515294853, 1.442834378987582,
            104.19253977340335, 135758.32777190334),
     "score": 0.6136552061869381,
     "mode_indices": [0, 8, 14, 15, 30, 31, 93, 190, 197]},
    {"rank": 2, "ns": (4, 17, 2, 5),
     "rs": (4.228091168870134, 367386.7909205613, 10282.072777272158, 336.1679820892126),
     "score": 0.6370709999911074,
     "mode_indices": [0, 8, 14, 16, 31, 33, 34, 165, 195]},
    {"rank": 3, "ns": (7, 2, 14, 4),
     "rs": (63.29422595842321, 2299.719998588086, 102290.34949178646, 1.0),
     "score": 0.6770571693508243,
     "mode_indices": [0, 10, 12, 13, 26, 27, 81, 193, 197]},
    {"rank": 4, "ns": (2, 2, 3, 2, 2, 19),
     "rs": (454.2102782796299, 256743.31657149456, 2.5842835112767264,
            5.54016964606962, 9384.532023219486, 308949.217945046),
     "score": 0.75760869624402,
     "mode_indices": [0, 8, 31, 37, 73, 75, 76, 149, 151]},
    {"rank": 5, "ns": (3, 11, 6, 2, 3),
     "rs": (1667241.9077310865, 224407.3710416956, 2.772316676627619,
            9906.429860304133, 391.1712112250075),
     "score": 0.7638095832942594,
     "mode_indices": [0, 8, 28, 32, 61, 65, 66, 189, 197]},
    {"rank": 6, "ns": (3, 5, 2, 17, 15),
     "rs": (4.310890617354535, 5094.506367350035, 409.8903413096548,
            307597.68714023486, 1.0),
     "score": 0.8845426783673429,
     "mode_indices": [0, 8, 14, 16, 48, 84, 85, 165, 195]},
    {"rank": 7, "ns": (16, 2, 9, 6),
     "rs": (195761.33653024829, 244.5175193289597, 1.0, 4668.111460447503),
     "score": 0.9095246204698805,
     "mode_indices": [0, 8, 14, 47, 79, 95, 96, 190, 191]},
    {"rank": 8, "ns": (6, 16, 2, 10, 8),
     "rs": (2718.0576462162703, 207695.12522749542, 257.30679773242196,
            1.0, 1.0423197399560813),
     "score": 0.9096727882379004,
     "mode_indices": [0, 8, 14, 15, 45, 95, 96, 190, 197]},
    {"rank": 9, "ns": (2, 3, 6, 16),
     "rs": (88.6833927158514, 1.0, 905.2421431170371, 74116.81888388497),
     "score": 0.9149907269976058,
     "mode_indices": [0, 8, 14, 15, 16, 95, 96, 190, 197]},
    {"rank": 10, "ns": (7, 14, 7, 7, 2),
     "rs": (1730.4806346372877, 173404.44539662226, 1.0, 1.0, 182.508301942722),
     "score": 0.978775794153168,
     "mode_indices": [0, 10, 12, 13, 39, 97, 98, 193, 195]},
]


def cascade_eigenvalues_with_tuples_full(ns, rs, n_lowest):
    """Same algorithm as bonus 12 probe: enumerate full Cartesian product,
    sort by eigenvalue, keep first n_lowest. Use for exact reproduction.
    """
    from itertools import product as iproduct
    per_factor = []
    for n, r in zip(ns, rs):
        k = np.arange(n)
        per_factor.append((2.0 / r ** 2) * (1.0 - np.cos(2.0 * math.pi * k / n)))
    all_modes = []
    for k_tuple in iproduct(*[range(n) for n in ns]):
        lam = sum(per_factor[i][k_tuple[i]] for i in range(len(ns)))
        all_modes.append((lam, k_tuple))
    all_modes.sort(key=lambda x: x[0])
    return all_modes[:n_lowest]


def reproduce_bonus10_active_counts_via_indices() -> Tuple[Dict[int, int], List[int], List[List[int]]]:
    """Use bonus 12's exact methodology: enumerate full Cartesian-product
    spectrum, sort by eigenvalue, take bonus-10's stored mode_indices,
    compute per-factor activation counts.

    Returns (histogram, per_cascade_active_counts, per_cascade_activation_lists).
    """
    counts = []
    activations_per = []
    for c in TOP10_BONUS_10:
        mode_indices = c["mode_indices"]
        n_lowest = max(mode_indices) + 1
        modes = cascade_eigenvalues_with_tuples_full(c["ns"], c["rs"], n_lowest)
        sm_modes = [modes[i] for i in mode_indices]
        K = len(c["ns"])
        acts = [0] * K
        for (lam, kt) in sm_modes:
            for f_i in range(K):
                if kt[f_i] != 0:
                    acts[f_i] += 1
        active_count = sum(1 for a in acts if a > 0)
        counts.append(active_count)
        activations_per.append(acts)
    hist: Dict[int, int] = {}
    for c_ac in counts:
        hist[c_ac] = hist.get(c_ac, 0) + 1
    return hist, counts, activations_per


def reproduce_bonus10_active_counts_via_probe(topN: int = 200) -> Tuple[Dict[int, int], List[int]]:
    """Rerun the top-10 bonus-10 cascades using THIS probe's greedy match
    pipeline (which may pick different k-tuple representatives for
    degenerate modes — this is the tie-break-dependency that bonus 12
    §5 flagged).
    """
    counts = []
    for c in TOP10_BONUS_10:
        factor_data = [cyclic_laplacian_spectrum(n, r) for n, r in zip(c["ns"], c["rs"])]
        eigs, kts = product_eigenvalues_with_ktuples(factor_data, topN=topN)
        score, sel, ac = subset_match_with_active_count(
            eigs, kts, c["ns"], LOG10_SM_TARGET
        )
        counts.append(ac)
    hist: Dict[int, int] = {}
    for c_ac in counts:
        if c_ac >= 0:
            hist[c_ac] = hist.get(c_ac, 0) + 1
    return hist, counts


# ----------------------------------------------------------------------------
# Reflection-invariance test (per bonus 12 §5).
# Compare bonus-10 rank-1 cascade's k-tuple to the bonus 12 / bonus 11d
# reports: zero/nonzero activation pattern should match.
# ----------------------------------------------------------------------------
def reflection_invariance_check() -> Dict:
    """Reproduce bonus 11d §5's activation pattern for the top cascade
    (2, 7, 4, 6, 16). The pattern from bonus 11d:
       C_2: 5 activations
       C_7: 1 activation (top quark only)
       C_4: 0 activations  <-- silent
       C_6: 3 activations
       C_16: 6 activations  (per bonus 11d §5)

    Bonus 12 §5 reported a slightly different per-mode tie-break giving
    [4, 1, 0, 2, 8] (different greedy tie-breaks). The reflection-
    invariance claim: zero/nonzero pattern should match — C_4 silent.

    This check uses bonus 12's full-Cartesian-product methodology
    with bonus-10's stored mode_indices for exact reproduction.
    """
    c = TOP10_BONUS_10[0]  # static rank-1 cascade.
    mode_indices = c["mode_indices"]
    n_lowest = max(mode_indices) + 1
    modes = cascade_eigenvalues_with_tuples_full(c["ns"], c["rs"], n_lowest)
    sm_modes = [modes[i] for i in mode_indices]
    K = len(c["ns"])
    acts = [0] * K
    selected_ktuples = []
    for (lam, kt) in sm_modes:
        selected_ktuples.append([int(x) for x in kt])
        for f_i in range(K):
            if kt[f_i] != 0:
                acts[f_i] += 1
    active_count = sum(1 for a in acts if a > 0)
    return {
        "cascade_ns": list(c["ns"]),
        "active_count": active_count,
        "per_factor_activations": acts,
        "zero_silent_factors": [int(i) for i, a in enumerate(acts) if a == 0],
        "selected_ktuples": selected_ktuples,
        "matches_bonus12_zero_pattern": bool(acts[2] == 0),  # C_4 silent
        "bonus11d_reported": [4, 1, 0, 3, 7],
        "bonus12_reported": [4, 1, 0, 2, 8],
    }


# ----------------------------------------------------------------------------
# NDJSON writer.
# ----------------------------------------------------------------------------
def _json_default(o):
    """Coerce numpy / non-JSON-native types for serialization."""
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (tuple,)):
        return list(o)
    raise TypeError(f"Object of type {type(o).__name__} not serializable")


def write_record(rec: Dict, fh):
    fh.write(json.dumps(rec, default=_json_default) + "\n")


# ----------------------------------------------------------------------------
# Main driver.
# ----------------------------------------------------------------------------
def main():
    # Track own PID for hygiene.
    pid = os.getpid()
    with open(PIDS_PATH, "w") as f:
        f.write(f"{pid}\n")

    t_start = time.time()
    fh = open(NDJSON_PATH, "w")

    # --- Provenance record ---
    prov = {
        "record": "provenance",
        "probe": PROBE_NAME,
        "version": PROBE_VERSION,
        "seed": SEED,
        "pid": pid,
        "numpy_version": np.__version__,
        "datetime_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "venv": ".venv_bonus_13",
        "n_target": N_TARGET,
        "sm_target_span_dec": SM_TARGET_SPAN_DEC,
        "log10_sm_target": list(LOG10_SM_TARGET),
        "sm_fermions": SM_FERMIONS,
    }
    write_record(prov, fh)
    print(f"[provenance] pid={pid} seed={SEED} target_span={SM_TARGET_SPAN_DEC:.3f} dec")

    # ------------------------------------------------------------------
    # Step 6 (run first, fast): reproduce bonus 12's {3:2, 4:8} numbers.
    # We do it TWO ways:
    #   (a) via_indices: use bonus 12's full-Cartesian methodology with
    #       bonus 10's stored mode_indices (exact reproduction).
    #   (b) via_probe: use this probe's greedy match (greedy-tie-break
    #       dependent; may differ for degenerate eigenvalues).
    # ------------------------------------------------------------------
    print("\n[step 6a] via_indices (exact bonus 12 reproduction)...")
    sm_hist_idx, sm_counts_idx, sm_acts_idx = reproduce_bonus10_active_counts_via_indices()
    print(f"  via_indices active-count hist: {dict(sorted(sm_hist_idx.items()))}")
    print(f"  per-cascade: {sm_counts_idx}")
    for c_i, acts in enumerate(sm_acts_idx):
        print(f"    rank {c_i+1}: per-factor = {acts}")
    rec = {
        "record": "step6a_bonus12_via_indices_reproduce",
        "active_count_histogram": dict(sorted(sm_hist_idx.items())),
        "active_count_per_cascade": sm_counts_idx,
        "per_factor_activations_per_cascade": sm_acts_idx,
        "bonus12_claimed_histogram": {3: 2, 4: 8},
        "matches_bonus12": bool(dict(sm_hist_idx) == {3: 2, 4: 8}),
        "n_with_ac_eq_4": sm_hist_idx.get(4, 0),
        "n_total": sum(sm_hist_idx.values()),
    }
    write_record(rec, fh)

    print("\n[step 6b] via_probe (this probe's greedy; tie-break may differ)...")
    sm_hist_pr, sm_counts_pr = reproduce_bonus10_active_counts_via_probe(topN=200)
    print(f"  via_probe active-count hist: {dict(sorted(sm_hist_pr.items()))}")
    print(f"  per-cascade: {sm_counts_pr}")
    rec = {
        "record": "step6b_bonus10_via_probe_reproduce",
        "topN": 200,
        "active_count_histogram": dict(sorted(sm_hist_pr.items())),
        "active_count_per_cascade": sm_counts_pr,
        "n_with_ac_eq_4": sm_hist_pr.get(4, 0),
        "n_total": sum(sm_hist_pr.values()),
    }
    write_record(rec, fh)

    # For downstream use, prefer the exact reproduction (via_indices).
    sm_hist = sm_hist_idx
    sm_counts = sm_counts_idx

    # ------------------------------------------------------------------
    # Reflection-invariance check.
    # ------------------------------------------------------------------
    print("\n[reflection-invariance] cascade rank-1 (2,7,4,6,16)...")
    refl = reflection_invariance_check()
    print(f"  per-factor activations: {refl['per_factor_activations']}")
    print(f"  zero-silent factors (indices): {refl['zero_silent_factors']}")
    print(f"  matches bonus 12 zero pattern (C_4 silent): {refl['matches_bonus12_zero_pattern']}")
    rec = {
        "record": "reflection_invariance",
        **refl,
    }
    write_record(rec, fh)

    # ------------------------------------------------------------------
    # Step 1-3: Random ensemble. Baseline: k=5 (matches rank-1 cascade size).
    # ------------------------------------------------------------------
    print("\n[step 1-3] random ensemble baseline: k=5 factors")
    n_cascades_baseline = 500   # scaled up from 200
    targets_per_cascade_baseline = 10
    # => 5000 trials baseline
    t0 = time.time()
    results_k5 = run_random_ensemble(
        n_cascades=n_cascades_baseline,
        targets_per_cascade=targets_per_cascade_baseline,
        k_factors=5,
        topN=200,
    )
    t_elapsed = time.time() - t0
    hist_k5 = active_count_distribution(results_k5)
    n_total_k5 = sum(hist_k5.values())
    print(f"  N={n_cascades_baseline} cascades x M={targets_per_cascade_baseline} targets = {n_total_k5} trials in {t_elapsed:.1f}s")
    print(f"  active-count histogram (k=5): {dict(sorted(hist_k5.items()))}")
    p4_k5 = hist_k5.get(4, 0) / max(n_total_k5, 1)
    p34_k5 = (hist_k5.get(3, 0) + hist_k5.get(4, 0)) / max(n_total_k5, 1)
    print(f"  P(active=4 | random) = {p4_k5:.4f}")
    print(f"  P(active in {{3,4}} | random) = {p34_k5:.4f}")

    # Score-quality stratified analysis.
    strat = score_quality_stratified_distribution(results_k5)
    print(f"  score-quality stratification:")
    for label, info in strat.items():
        if info["n_trials"] > 0:
            print(f"    {label}: n={info['n_trials']:4d}, hist={info['histogram']}, P(ac=4)={info.get('P_ac_eq_4', 'NA')}")

    rec = {
        "record": "step1_3_random_ensemble_k5",
        "n_cascades": n_cascades_baseline,
        "targets_per_cascade": targets_per_cascade_baseline,
        "n_total_trials": n_total_k5,
        "elapsed_sec": t_elapsed,
        "active_count_histogram": dict(sorted(hist_k5.items())),
        "P_active_eq_4": p4_k5,
        "P_active_in_34": p34_k5,
        "topN": 200,
        "radius_decades": [0.0, 6.0],
        "score_quality_stratified": strat,
    }
    write_record(rec, fh)

    # ------------------------------------------------------------------
    # Step 4: significance test.
    # ------------------------------------------------------------------
    # Observed (bonus 12 published, via_indices): 8/10 cascades with ac=4.
    # Observed (this probe, via_probe greedy):    8/10 cascades with ac<=4.
    # Null hypothesis: random cascades have a certain distribution.
    # Both statistics are tested against the random null.
    print(f"\n[step 4] significance test")
    # Statistic 1: bonus 12's "active_count = 4 in 8 of 10".
    p_value_ac4 = binomial_pvalue_ge_k(10, 8, p4_k5)
    print(f"  P(X >= 8/10 with ac=4 | Binomial(10, p4_k5={p4_k5:.4f})) = {p_value_ac4:.6f}")
    # Statistic 2: "active_count in {3,4} in 10 of 10".
    p_value_ac34 = binomial_pvalue_ge_k(10, 10, p34_k5)
    print(f"  P(X >= 10/10 in {{3,4}} | Binomial(10, p34_k5={p34_k5:.4f})) = {p_value_ac34:.6f}")
    # Statistic 3: probe-reproduce's "ac<=4 in 8/10" (i.e. ac in {3,4} for via_indices,
    # ac in {4} for via_probe). Use whatever count >= 4 was observed.
    n_le_4 = sum(1 for c in sm_counts_pr if c <= 4)
    p_le_4_null = sum(h for k, h in hist_k5.items() if k <= 4) / max(n_total_k5, 1)
    p_value_le_4 = binomial_pvalue_ge_k(10, n_le_4, p_le_4_null)
    print(f"  P(X >= {n_le_4}/10 with ac<=4 | Binomial(10, p_le_4={p_le_4_null:.4f})) = {p_value_le_4:.6f}")

    # Determine verdict.
    if p_value_ac4 < 0.01:
        verdict = "CONFIRMED_STRONG"
    elif p_value_ac4 < 0.05:
        verdict = "CONFIRMED"
    elif p_value_ac4 < 0.2:
        verdict = "UNCERTAIN"
    else:
        verdict = "COINCIDENCE"
    print(f"  preliminary verdict (ac=4 statistic): {verdict}")
    rec = {
        "record": "step4_significance",
        "bonus12_observed_via_indices": {"n": 10, "ac_eq_4": sm_hist_idx.get(4, 0), "ac_in_34": sm_hist_idx.get(3, 0) + sm_hist_idx.get(4, 0)},
        "this_probe_observed_via_probe": {"n": 10, "ac_le_4": n_le_4, "ac_eq_4": sm_hist_pr.get(4, 0)},
        "null_p_ac_eq_4": p4_k5,
        "null_p_ac_in_34": p34_k5,
        "null_p_ac_le_4": p_le_4_null,
        "p_value_ac_eq_4_ge_8_of_10": p_value_ac4,
        "p_value_ac_in_34_ge_10_of_10": p_value_ac34,
        "p_value_ac_le_4_observed_count": p_value_le_4,
        "preliminary_verdict": verdict,
    }
    write_record(rec, fh)

    # ------------------------------------------------------------------
    # Step 5a: cascade-size sensitivity (4, 5, 6, 7).
    # ------------------------------------------------------------------
    print("\n[step 5a] cascade-size sensitivity (k=4, 6, 7)")
    size_results = {}
    for k_f in [4, 6, 7]:
        # Smaller ensemble for non-baseline sizes.
        n_c = 100
        m_t = 10
        t0 = time.time()
        res = run_random_ensemble(
            n_cascades=n_c, targets_per_cascade=m_t,
            k_factors=k_f, topN=200,
        )
        t_e = time.time() - t0
        hist = active_count_distribution(res)
        n_tot = sum(hist.values())
        p4 = hist.get(4, 0) / max(n_tot, 1)
        p34 = (hist.get(3, 0) + hist.get(4, 0)) / max(n_tot, 1)
        print(f"  k={k_f}: trials={n_tot} in {t_e:.1f}s; hist={dict(sorted(hist.items()))}; P(ac=4)={p4:.3f}; P(ac in {{3,4}})={p34:.3f}")
        size_results[k_f] = {
            "trials": n_tot,
            "histogram": dict(sorted(hist.items())),
            "P_ac_eq_4": p4,
            "P_ac_in_34": p34,
            "elapsed_sec": t_e,
        }
    rec = {
        "record": "step5a_size_sensitivity",
        "k4": size_results[4],
        "k6": size_results[6],
        "k7": size_results[7],
        "k5_baseline_p_ac_eq_4": p4_k5,
        "k5_baseline_p_ac_in_34": p34_k5,
    }
    write_record(rec, fh)

    # ------------------------------------------------------------------
    # Step 5b: tower-truncation sensitivity.
    # ------------------------------------------------------------------
    print("\n[step 5b] tower-truncation sensitivity (top-100, 200, 500)")
    trunc_results = {}
    n_c_trunc = 80
    m_t_trunc = 10
    for topN_test in [100, 200, 500]:
        t0 = time.time()
        res = run_random_ensemble(
            n_cascades=n_c_trunc, targets_per_cascade=m_t_trunc,
            k_factors=5, topN=topN_test,
        )
        t_e = time.time() - t0
        hist = active_count_distribution(res)
        n_tot = sum(hist.values())
        p4 = hist.get(4, 0) / max(n_tot, 1)
        p34 = (hist.get(3, 0) + hist.get(4, 0)) / max(n_tot, 1)
        print(f"  topN={topN_test}: trials={n_tot} in {t_e:.1f}s; hist={dict(sorted(hist.items()))}; P(ac=4)={p4:.3f}")
        trunc_results[topN_test] = {
            "trials": n_tot,
            "histogram": dict(sorted(hist.items())),
            "P_ac_eq_4": p4,
            "P_ac_in_34": p34,
            "elapsed_sec": t_e,
        }
    rec = {
        "record": "step5b_truncation_sensitivity",
        "top100": trunc_results[100],
        "top200": trunc_results[200],
        "top500": trunc_results[500],
    }
    write_record(rec, fh)

    # ------------------------------------------------------------------
    # Step 5d: SEARCH-NULL — for each random target, search through many
    # random cascades and pick the TOP-10 best matches. This is the
    # apples-to-apples comparison to bonus 10's top-10 (which were also
    # selected by search). Report the active-count distribution of those
    # top-10 across multiple random targets.
    # ------------------------------------------------------------------
    print("\n[step 5d] SEARCH-NULL: top-10 of random cascades for random targets")
    n_search_targets = 30
    cascades_per_search = 200  # samples per target
    top_per_target = 10
    t0 = time.time()
    all_top_acs = []  # active-counts of all top-10's across all targets
    all_top_scores = []
    per_target_summary = []
    for target_i in range(n_search_targets):
        tgt = random_log_target()
        # Generate cascades_per_search random k=5 cascades; greedy match each.
        scored = []
        for _ in range(cascades_per_search):
            ns = tuple(int(RNG.integers(2, 17)) for _ in range(5))
            rs = tuple(float(10.0 ** RNG.uniform(0, 6)) for _ in range(5))
            fd = [cyclic_laplacian_spectrum(n, r) for n, r in zip(ns, rs)]
            eigs, kts = product_eigenvalues_with_ktuples(fd, topN=200)
            score, sel, ac = subset_match_with_active_count(eigs, kts, ns, tgt)
            if np.isfinite(score) and ac >= 0:
                scored.append((score, ac, ns, rs))
        scored.sort(key=lambda x: x[0])
        top = scored[:top_per_target]
        for s, a, _, _ in top:
            all_top_acs.append(a)
            all_top_scores.append(s)
        # Per-target active-count hist
        top_hist = {}
        for s, a, _, _ in top:
            top_hist[a] = top_hist.get(a, 0) + 1
        n_ac4 = top_hist.get(4, 0)
        per_target_summary.append({
            "target_idx": target_i,
            "histogram": dict(sorted(top_hist.items())),
            "top10_scores_min_max": [float(top[0][0]) if top else None, float(top[-1][0]) if top else None],
            "n_ac_eq_4_in_top10": n_ac4,
        })
    t_e = time.time() - t0

    # Aggregate analysis: of the per-target summaries, how often did the
    # top-10 have 8+ at active_count=4?
    n_ac4_per_target = [pt["n_ac_eq_4_in_top10"] for pt in per_target_summary]
    n_top10_ge_8 = sum(1 for n in n_ac4_per_target if n >= 8)
    p_top10_ge_8_random = n_top10_ge_8 / max(n_search_targets, 1)
    print(f"  {n_search_targets} random targets x {cascades_per_search} cascades; top-{top_per_target} per target")
    print(f"  elapsed: {t_e:.1f}s")
    print(f"  Per-target ac=4 counts in top-10: {n_ac4_per_target}")
    print(f"  Fraction of targets with >= 8/10 top cascades at ac=4: {p_top10_ge_8_random:.3f}")
    # Distribution of top cascade scores.
    print(f"  Scores of top-1 across all targets: min={min(all_top_scores):.3f}, median={np.median(all_top_scores):.3f}, max={max(all_top_scores):.3f}")
    # Aggregate ac hist:
    agg_hist = {}
    for a in all_top_acs:
        agg_hist[a] = agg_hist.get(a, 0) + 1
    n_tot_agg = len(all_top_acs)
    p4_agg = agg_hist.get(4, 0) / max(n_tot_agg, 1)
    print(f"  Aggregate top-10 active-count hist ({n_tot_agg} cascades): {dict(sorted(agg_hist.items()))}")
    print(f"  Aggregate P(ac=4 | top-10) = {p4_agg:.4f}")

    rec = {
        "record": "step5d_search_null",
        "n_search_targets": n_search_targets,
        "cascades_per_search": cascades_per_search,
        "top_per_target": top_per_target,
        "elapsed_sec": t_e,
        "per_target_ac4_counts": n_ac4_per_target,
        "fraction_targets_ge_8of10_ac4": p_top10_ge_8_random,
        "aggregate_top_acs_histogram": dict(sorted(agg_hist.items())),
        "P_ac_eq_4_in_top10": p4_agg,
        "top_scores_summary": {
            "min": float(min(all_top_scores)),
            "median": float(np.median(all_top_scores)),
            "max": float(max(all_top_scores)),
        },
        "per_target_summary_sample": per_target_summary[:5],
    }
    write_record(rec, fh)

    # ------------------------------------------------------------------
    # Step 5c: target SM-like vs random (use SM-target on random cascades).
    # If the SM-target's specific log-pattern (gaps at u/d/s/μ/c... ratios)
    # drives the active_count concentration, that's a different finding
    # from generic random-target concentration.
    # ------------------------------------------------------------------
    print("\n[step 5c] SM-target on random cascades (200 random k=5)")
    t0 = time.time()
    sm_ac_random = []
    for _ in range(200):
        ns, rs = random_cascade(5)
        fd = [cyclic_laplacian_spectrum(n, r) for n, r in zip(ns, rs)]
        eigs, kts = product_eigenvalues_with_ktuples(fd, topN=200)
        _, _, ac = subset_match_with_active_count(eigs, kts, ns, LOG10_SM_TARGET)
        if ac >= 0:
            sm_ac_random.append(ac)
    t_e = time.time() - t0
    hist_sm = {}
    for ac in sm_ac_random:
        hist_sm[ac] = hist_sm.get(ac, 0) + 1
    n_tot_sm = sum(hist_sm.values())
    p4_sm = hist_sm.get(4, 0) / max(n_tot_sm, 1)
    p34_sm = (hist_sm.get(3, 0) + hist_sm.get(4, 0)) / max(n_tot_sm, 1)
    print(f"  SM-target on random k=5 cascades: trials={n_tot_sm} in {t_e:.1f}s")
    print(f"  hist={dict(sorted(hist_sm.items()))}; P(ac=4)={p4_sm:.3f}; P(ac in {{3,4}})={p34_sm:.3f}")
    p_value_sm = binomial_pvalue_ge_k(10, 8, p4_sm)
    print(f"  P(X >= 8/10 | Binomial(10, {p4_sm:.3f})) = {p_value_sm:.6f}")
    rec = {
        "record": "step5c_sm_target_on_random",
        "n_trials": n_tot_sm,
        "elapsed_sec": t_e,
        "histogram": dict(sorted(hist_sm.items())),
        "P_ac_eq_4": p4_sm,
        "P_ac_in_34": p34_sm,
        "p_value_ge_8_of_10": p_value_sm,
    }
    write_record(rec, fh)

    # ------------------------------------------------------------------
    # Final verdict (use SM-target on random k=5 as the cleanest null
    # because it controls the target shape — the target's gap pattern
    # may itself drive active-count concentration).
    # ------------------------------------------------------------------
    print("\n[final verdict]")
    # Compute p-values under multiple nulls. The SEARCH-NULL (step 5d) is
    # the most-apples-to-apples comparison to bonus 10's selection-by-search.
    null_choices = {
        "random_target_k5": (p4_k5, binomial_pvalue_ge_k(10, 8, p4_k5)),
        "sm_target_k5_random_cascade": (p4_sm, p_value_sm),
        "search_null_top10": (p4_agg, binomial_pvalue_ge_k(10, 8, p4_agg)),
    }
    print(f"  Null distributions tested:")
    for nm, (p, pv) in null_choices.items():
        print(f"    {nm}: P(ac=4)={p:.4f}, p-value(>=8/10)={pv:.6f}")
    # The search-null is the right comparison; report it as primary.
    # Conservative (highest p-value) is also reported.
    most_conservative = max(null_choices.items(), key=lambda x: x[1][1])
    nm_c, (p_c, pv_c) = most_conservative
    # Direct search-null statistic: fraction of random-target top-10
    # achieving 8+/10 at ac=4 — this is the empirical p-value WITHOUT
    # parametric assumption.
    pv_empirical_search = p_top10_ge_8_random
    print(f"  Empirical search-null p-value (fraction targets with >=8/10 top cascades at ac=4): {pv_empirical_search:.4f}")

    # Use the search-null as primary verdict driver.
    pv_primary = pv_empirical_search
    print(f"  Most conservative parametric null: {nm_c} (p-value = {pv_c:.6f})")
    if pv_primary < 0.01 and pv_c < 0.01:
        final_verdict = "CONFIRMED_STRONG"
    elif pv_primary < 0.05 and pv_c < 0.05:
        final_verdict = "CONFIRMED"
    elif pv_primary < 0.2:
        final_verdict = "UNCERTAIN"
    else:
        final_verdict = "COINCIDENCE"
    print(f"  FINAL VERDICT: {final_verdict}")
    rec = {
        "record": "final_verdict",
        "null_distributions": {nm: {"p_ac_eq_4": p, "p_value": pv} for nm, (p, pv) in null_choices.items()},
        "most_conservative_parametric_null": nm_c,
        "p_value_conservative_parametric": pv_c,
        "p_ac_eq_4_conservative": p_c,
        "p_value_empirical_search_null": pv_empirical_search,
        "p_value_primary": pv_primary,
        "verdict": final_verdict,
        "verdict_thresholds": {"CONFIRMED_STRONG": 0.01, "CONFIRMED": 0.05, "UNCERTAIN": 0.2},
        "observed_via_indices": {"ac_eq_4": sm_hist_idx.get(4, 0), "n_total": 10},
        "observed_via_probe": {"ac_eq_4": sm_hist_pr.get(4, 0), "ac_le_4": sum(1 for c in sm_counts_pr if c <= 4), "n_total": 10},
    }
    write_record(rec, fh)

    # ------------------------------------------------------------------
    # Final summary stays below.
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Final summary.
    # ------------------------------------------------------------------
    t_total = time.time() - t_start
    rec = {
        "record": "summary",
        "total_elapsed_sec": t_total,
        "n_total_random_trials": n_total_k5
            + sum(s["trials"] for s in size_results.values())
            + sum(t["trials"] for t in trunc_results.values())
            + n_tot_sm
            + n_tot_agg,
        "bonus10_reproduce_active_hist_via_indices": dict(sorted(sm_hist_idx.items())),
        "bonus10_reproduce_active_hist_via_probe": dict(sorted(sm_hist_pr.items())),
        "matches_bonus12_3_2_4_8": bool(sm_hist_idx.get(4, 0) == 8 and sm_hist_idx.get(3, 0) == 2),
        "final_verdict": final_verdict,
        "p_value_primary": pv_primary,
        "p_value_conservative_parametric": pv_c,
        "p_ac_eq_4_null_search": p4_agg,
    }
    write_record(rec, fh)
    print(f"\n[summary] total time {t_total:.1f}s; verdict = {final_verdict}; output -> {NDJSON_PATH.name}")

    fh.close()
    # Integrity hash of the NDJSON.
    with open(NDJSON_PATH, "rb") as f:
        sha = hashlib.sha256(f.read()).hexdigest()
    # Append integrity record.
    with open(NDJSON_PATH, "a") as f:
        f.write(json.dumps({"record": "integrity", "sha256": sha}) + "\n")
    print(f"[integrity] sha256 = {sha}")


if __name__ == "__main__":
    main()
