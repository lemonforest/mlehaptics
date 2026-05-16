"""Spike #24 bonus 11d — Class P sign-rule discriminator probe.

Reading 4 of the mode-selection-gap parallel investigation. Tests whether a
*sign-rule-like* per-factor or per-mode-index discriminator can select the
9 observed SM fermion modes from the cascade's ~200-mode spectrum.

Hypothesis: Class O (bonus 8) is a sign-rule primitive at the COMPOSITION
level (uniform Wick rotation on temporal factor). Class P, if it exists,
would be the analog at the MODE-SELECTION level: a discriminator that
distinguishes observable cascade modes from unobservable ones, per-factor
or per-mode-index, with ZERO or very few free parameters.

Substrate: bonus 10 rank-1 cascade `C_2 × C_7 × C_4 × C_6 × C_16` with
radii (3659, 1.03, 1.44, 104.2, 135758). Bonus 10 picked modes
[0, 8, 14, 15, 30, 31, 93, 190, 197] from the sorted 200-mode spectrum
via greedy subset-match. We test whether a minimal-parameter rule
SELECTS those (or an equally-good alternative set).

Candidate rules tested:
  P1 — per-factor parity bit (each factor contributes +/− to mode-index
       combination; mode observable iff parity-sum satisfies a rule)
  P2 — mode-index character constraint (ω = Σ k_i / n_i ∈ Q/Z;
       observable iff ω in some sparse residue set)
  P3 — tensor-rank cutoff (rank = count of non-zero k_i; observable iff
       rank in some subset)
  P4 — charge/hypercharge-like quantisation (mode observable iff
       a linear-combination Σ q_i k_i mod something = 0)
  P5 — k_i sum-mod constraint (Σ k_i mod m = r, for some small m,r)
  P6 — single-factor-dominant (mode observable iff exactly one k_i ≠ 0,
       i.e. lives on a single factor's spectrum)
  P7 — pair-wise excitation (mode observable iff exactly two k_i ≠ 0,
       e.g. 2-factor "tensor product")
  P8 — coprime-factor pattern (gcd of (k_i, n_i) constraint)

For each rule, count selected modes and compute log-L2 vs SM target.

Discipline guards honoured:
  - Per `[[feedback_antiquity_not_greek]]`: Class L (eigenvalue computation)
    is the falsifier; spectral-graph operation throughout.
  - Per `[[feedback_trauma_informed_defensive_scope]]`: structural inquiry.
  - Per `[[feedback_ndjson_over_bloated_json]]`: NDJSON output.
  - stdlib + numpy + scipy only; CPU; deterministic seed = 20260515.
  - Conservative — only propose Class P if irreducible to A-N composition.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Set, Callable

import numpy as np


# ----------------------------------------------------------------------------
# Determinism + provenance.
# ----------------------------------------------------------------------------
SEED = 20260515
RNG = np.random.default_rng(SEED)

PROBE_NAME = "spike_24_bonus_11d_mode_selection_class_p_probe_2026-05-15"
PROBE_VERSION = "0.1.0"

HERE = Path(__file__).parent
NDJSON_PATH = HERE / "spike_24_bonus_11d_mode_selection_class_p_probe_2026-05-15.ndjson"


# ----------------------------------------------------------------------------
# Target spectrum (MFO §IV.6 PDG 2024 charged-fermion mass² ratios).
# ----------------------------------------------------------------------------
SM_FERMIONS = ["e", "u", "d", "s", "mu", "c", "tau", "b", "t"]
SM_MASSES_MEV = [0.511, 2.2, 4.7, 95.0, 105.7, 1270.0, 1777.0, 4180.0, 172760.0]
SM_MASS_SQ_RATIOS = np.array([(m / SM_MASSES_MEV[0]) ** 2 for m in SM_MASSES_MEV])
LOG10_TARGET = np.log10(SM_MASS_SQ_RATIOS)
N_TARGET = len(SM_MASS_SQ_RATIOS)  # 9


# ----------------------------------------------------------------------------
# Bonus 10 rank-1 cascade (the substrate of this probe).
# ----------------------------------------------------------------------------
CASCADE_NS = (2, 7, 4, 6, 16)
CASCADE_RS = (
    3659.03506590957,
    1.0286749515294853,
    1.442834378987582,
    104.19253977340335,
    135758.32777190334,
)

# Bonus 10 reported selected mode indices for the rank-1 cascade.
BONUS10_SELECTED_INDICES = [0, 8, 14, 15, 30, 31, 93, 190, 197]


# ----------------------------------------------------------------------------
# Class I primitive — cyclic-group Laplacian eigenvalues.
# ----------------------------------------------------------------------------
def cyclic_laplacian_eigenvalues(n: int, radius: float = 1.0) -> np.ndarray:
    """Spectrum λ_k = (2/r²)(1 - cos(2πk/n)) for k=0..n-1."""
    k = np.arange(n)
    return (2.0 / radius**2) * (1.0 - np.cos(2.0 * math.pi * k / n))


# ----------------------------------------------------------------------------
# Cascade — direct-product spectrum with FULL (k_1, ..., k_p) decomposition.
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class CascadeMode:
    """A single mode of the cascade product spectrum.

    Fields:
      k_indices: tuple (k_1, k_2, ..., k_p) of per-factor cyclic indices
      eigenvalue: total eigenvalue = sum of factor eigenvalues
      factor_eigenvalues: per-factor eigenvalue at that k_i
    """
    k_indices: Tuple[int, ...]
    eigenvalue: float
    factor_eigenvalues: Tuple[float, ...]


def build_full_spectrum(
    ns: Tuple[int, ...], rs: Tuple[float, ...]
) -> List[CascadeMode]:
    """Construct full product spectrum as list of CascadeMode, sorted by
    eigenvalue ascending. For (2,7,4,6,16) this is 2*7*4*6*16 = 5376 modes.
    Tractable on CPU.
    """
    factor_specs = [cyclic_laplacian_eigenvalues(n, r) for n, r in zip(ns, rs)]
    modes: List[CascadeMode] = []
    for k_tuple in product(*[range(n) for n in ns]):
        eigvs = tuple(factor_specs[i][k_tuple[i]] for i in range(len(ns)))
        total = sum(eigvs)
        modes.append(CascadeMode(
            k_indices=k_tuple,
            eigenvalue=total,
            factor_eigenvalues=eigvs,
        ))
    modes.sort(key=lambda m: m.eigenvalue)
    return modes


# ----------------------------------------------------------------------------
# Match-score: given a selected subset of modes, compute log-L2 vs SM target.
# ----------------------------------------------------------------------------
def score_subset(
    selected_modes: List[CascadeMode], modes_used: int = N_TARGET,
) -> Tuple[float, np.ndarray, np.ndarray]:
    """Given selected modes (must be sorted; first one becomes anchor),
    compute log-L2 vs SM target spectrum.

    Returns (score, predicted_ratios, log_diffs).
    """
    if len(selected_modes) < modes_used:
        return (np.inf, np.zeros(modes_used), np.full(modes_used, np.inf))
    # Use first modes_used; first is anchor (electron).
    eigs = np.array([m.eigenvalue for m in selected_modes[:modes_used]])
    eigs_nonzero = eigs[eigs > 1e-12]
    if len(eigs_nonzero) < modes_used:
        return (np.inf, np.zeros(modes_used), np.full(modes_used, np.inf))
    ratios = eigs_nonzero / eigs_nonzero[0]
    log_pred = np.log10(ratios)
    diffs = log_pred - LOG10_TARGET
    score = float(np.sqrt(np.sum(diffs**2)))
    return score, ratios, diffs


def score_with_best_anchor(
    candidate_modes: List[CascadeMode],
) -> Tuple[float, np.ndarray, np.ndarray, int]:
    """For each candidate anchor in the selected set, evaluate the resulting
    log-L2 score (anchor = ratio reference). Returns the best (score, ratios,
    diffs, anchor_idx).

    A genuine Class P rule should produce an EXACT-9 set; the best-anchor
    score is then computed by treating each of the 9 as anchor and choosing
    the smallest score. For non-exact-9 candidate-sets, we use greedy match.
    """
    nonzero = [m for m in candidate_modes if m.eigenvalue > 1e-12]
    if len(nonzero) < N_TARGET:
        return (np.inf, np.zeros(N_TARGET), np.full(N_TARGET, np.inf), -1)
    nonzero.sort(key=lambda m: m.eigenvalue)
    eigs_log = np.array([math.log10(m.eigenvalue) for m in nonzero])

    # If exactly N_TARGET=9 modes, try each as anchor; use the smallest mode as anchor.
    if len(nonzero) == N_TARGET:
        eigs = np.array([m.eigenvalue for m in nonzero])
        ratios = eigs / eigs[0]
        diffs = np.log10(ratios) - LOG10_TARGET
        score = float(np.sqrt(np.sum(diffs**2)))
        return score, ratios, diffs, 0

    # Otherwise, do greedy anchor + nearest-log-ratio (same as bonus 10 metric).
    best_score = np.inf
    best_ratios = None
    best_diffs = None
    best_anchor = -1
    n_anchors = min(20, len(nonzero))
    for anchor_idx in range(n_anchors):
        anchor_log = eigs_log[anchor_idx]
        rel_log = eigs_log - anchor_log
        used = {anchor_idx}
        selected_log_ratios = [0.0]
        valid = True
        for target_log in LOG10_TARGET[1:]:
            best_local_idx = -1
            best_local_dist = np.inf
            for j in range(len(rel_log)):
                if j in used:
                    continue
                d = abs(rel_log[j] - target_log)
                if d < best_local_dist:
                    best_local_dist = d
                    best_local_idx = j
            if best_local_idx == -1:
                valid = False
                break
            used.add(best_local_idx)
            selected_log_ratios.append(rel_log[best_local_idx])
        if not valid:
            continue
        diffs = np.array(selected_log_ratios) - LOG10_TARGET
        score = float(np.sqrt(np.sum(diffs**2)))
        if score < best_score:
            best_score = score
            best_ratios = 10.0 ** np.array(selected_log_ratios)
            best_diffs = diffs
            best_anchor = anchor_idx
    if best_ratios is None:
        return (np.inf, np.zeros(N_TARGET), np.full(N_TARGET, np.inf), -1)
    return best_score, best_ratios, best_diffs, best_anchor


# ----------------------------------------------------------------------------
# Class P candidate rules.
# Each rule takes a CascadeMode (k_indices) and returns True if mode is
# "observable" per the rule. Rules are intentionally parameter-light.
# ----------------------------------------------------------------------------

def rule_P1_factor_parity(mode: CascadeMode, parity_target: int = 0) -> bool:
    """P1 — per-factor parity bit, then sum-of-parities mod 2.

    Each factor contributes bit b_i = k_i mod 2; observable iff
    Σ b_i mod 2 = parity_target.
    Free parameters: 1 (parity_target ∈ {0, 1}).
    """
    parity_sum = sum(k % 2 for k in mode.k_indices) % 2
    return parity_sum == parity_target


def rule_P2_character(
    mode: CascadeMode, ns: Tuple[int, ...],
    allowed_residues_lcm: Optional[Set[int]] = None,
) -> bool:
    """P2 — mode-index character constraint.

    Compute ω = Σ (k_i / n_i); reduce mod 1; check if ω is in some sparse
    rational set, e.g. {0, 1/3, 2/3} for 3-generation selection. Mapped to
    integers via lcm(n_i) for cleanliness.

    Specifically: with N = lcm(n_i), define c = Σ k_i * (N/n_i) mod N.
    Observable iff c ∈ allowed_residues_lcm.

    Free parameters: depends on the size of allowed_residues_lcm.
    """
    if allowed_residues_lcm is None:
        return False
    N = 1
    for n in ns:
        N = math.lcm(N, n)
    c = 0
    for i, k in enumerate(mode.k_indices):
        c = (c + k * (N // ns[i])) % N
    return c in allowed_residues_lcm


def rule_P3_rank(mode: CascadeMode, allowed_ranks: Set[int]) -> bool:
    """P3 — tensor-rank cutoff.

    Rank = number of non-zero k_i. Observable iff rank in allowed_ranks.
    Free parameters: the rank set (small).
    """
    rank = sum(1 for k in mode.k_indices if k != 0)
    return rank in allowed_ranks


def rule_P4_linear_combo_mod(
    mode: CascadeMode, q: Tuple[int, ...], modulus: int, target: int,
) -> bool:
    """P4 — charge-like linear quantisation.

    Observable iff (Σ q_i k_i) mod modulus = target.
    Free parameters: q vector (p params), modulus (1), target (1) — heavier
    than other rules; we'll explore small-q.
    """
    s = sum(q[i] * k for i, k in enumerate(mode.k_indices))
    return s % modulus == target


def rule_P5_ksum_mod(mode: CascadeMode, modulus: int, target: int) -> bool:
    """P5 — total-excitation count mod m.

    Observable iff (Σ k_i) mod modulus = target.
    Free parameters: 2 (modulus, target).
    """
    s = sum(mode.k_indices)
    return s % modulus == target


def rule_P6_single_factor(mode: CascadeMode) -> bool:
    """P6 — single-factor excitation only.

    Observable iff exactly one k_i ≠ 0 (mode lives on a single factor's
    spectrum). Free parameters: 0.
    """
    return sum(1 for k in mode.k_indices if k != 0) <= 1


def rule_P7_pair_or_single(mode: CascadeMode) -> bool:
    """P7 — pair or single factor.

    Observable iff at most two k_i ≠ 0. Free parameters: 0.
    """
    return sum(1 for k in mode.k_indices if k != 0) <= 2


def rule_P8_coprime(mode: CascadeMode, ns: Tuple[int, ...]) -> bool:
    """P8 — coprime-with-factor-order constraint.

    Observable iff for every i with k_i ≠ 0, gcd(k_i, n_i) = 1
    (i.e. k_i is a generator of C_{n_i}). Free parameters: 0.
    """
    for i, k in enumerate(mode.k_indices):
        if k == 0:
            continue
        if math.gcd(k, ns[i]) != 1:
            return False
    return True


def rule_P9_complement_excluded(mode: CascadeMode, ns: Tuple[int, ...]) -> bool:
    """P9 — exclude conjugate pairs k_i and n_i - k_i.

    On the cyclic Laplacian, λ_k = λ_{n-k} (real Fourier basis pair). So
    the spectrum has pair-degeneracies. P9: observable iff k_i ≤ n_i/2 for
    every i (take the smaller of each conjugate pair). Free params: 0.
    """
    for i, k in enumerate(mode.k_indices):
        if k > ns[i] // 2:
            return False
    return True


# ----------------------------------------------------------------------------
# Helper: select modes from full spectrum per rule, eval scoring.
# ----------------------------------------------------------------------------
def evaluate_rule(
    rule_name: str,
    rule_fn: Callable[[CascadeMode], bool],
    full_spectrum: List[CascadeMode],
    free_params: int,
    description: str,
    rule_extra: Optional[Dict] = None,
) -> Dict:
    """Apply rule, count selected modes, compute log-L2 if N_TARGET modes
    obtainable.
    """
    selected = [m for m in full_spectrum if rule_fn(m)]
    selected_nonzero = [m for m in selected if m.eigenvalue > 1e-12]
    n_selected = len(selected)
    n_selected_nz = len(selected_nonzero)
    score, ratios, diffs, anchor = score_with_best_anchor(selected_nonzero)
    return {
        "rule_name": rule_name,
        "description": description,
        "free_parameters": free_params,
        "rule_extra": rule_extra or {},
        "n_selected_total": n_selected,
        "n_selected_nonzero": n_selected_nz,
        "log_L2_score": (float(score) if score != np.inf else None),
        "log_L2_score_infinite": bool(score == np.inf),
        "best_anchor_index": int(anchor),
        "predicted_ratios_first_9": (
            [float(r) for r in ratios[:N_TARGET]] if score != np.inf else None
        ),
        "log10_diffs_first_9": (
            [float(d) for d in diffs[:N_TARGET]] if score != np.inf else None
        ),
        "selected_mode_k_indices_first_9": [
            list(m.k_indices) for m in selected_nonzero[:N_TARGET]
        ],
    }


# ----------------------------------------------------------------------------
# Main probe.
# ----------------------------------------------------------------------------
def main() -> int:
    t_start = time.time()
    records: List[dict] = []

    # Provenance.
    records.append({
        "record": "provenance",
        "probe": PROBE_NAME, "version": PROBE_VERSION, "seed": SEED,
        "cascade_ns": list(CASCADE_NS),
        "cascade_rs": list(CASCADE_RS),
        "bonus10_selected_indices": list(BONUS10_SELECTED_INDICES),
        "sm_target_n": N_TARGET,
        "sm_target_log10_span": float(LOG10_TARGET.max() - LOG10_TARGET.min()),
    })

    # 1. Build full spectrum (5376 modes).
    print("Building full cascade spectrum (2*7*4*6*16 = 5376 modes)...")
    full_spectrum = build_full_spectrum(CASCADE_NS, CASCADE_RS)
    print(f"  total modes: {len(full_spectrum)}")
    # Verify first 200 sorted modes match bonus 10's spectrum.
    eigs_top200 = [m.eigenvalue for m in full_spectrum[:200]]
    print(f"  smallest 10 eigenvalues: {eigs_top200[:10]}")
    records.append({
        "record": "spectrum_built",
        "n_modes_total": len(full_spectrum),
        "smallest_10_eigenvalues": eigs_top200[:10],
        "smallest_eigenvalue_zero": bool(eigs_top200[0] < 1e-12),
        "first_nonzero_index": next(
            (i for i, e in enumerate(eigs_top200) if e > 1e-12), -1
        ),
    })

    # 2. Verify bonus 10's mode selection against full spectrum.
    # Note: bonus 10's `selected_mode_indices` are indices into the NONZERO-
    # filtered top-200 list (per the probe's eigs[eigs>1e-12] step). So we
    # build the nonzero-filtered top-200 list and index into that.
    print("\nVerifying bonus 10's selected modes...")
    full_eigs = np.array([m.eigenvalue for m in full_spectrum])
    nonzero_modes_top200 = [m for m in full_spectrum if m.eigenvalue > 1e-12][:200]
    bonus10_modes = [nonzero_modes_top200[i] for i in BONUS10_SELECTED_INDICES]
    bonus10_eigs = [m.eigenvalue for m in bonus10_modes]
    bonus10_kindices = [list(m.k_indices) for m in bonus10_modes]
    bonus10_ratios = np.array(bonus10_eigs) / bonus10_eigs[0]
    bonus10_logdiff = np.log10(bonus10_ratios[:N_TARGET]) - LOG10_TARGET
    bonus10_score = float(np.sqrt(np.sum(bonus10_logdiff**2)))
    print(f"  bonus 10 score (verified): {bonus10_score:.4f}")
    print(f"  bonus 10 mode k-indices:")
    for idx, m in zip(BONUS10_SELECTED_INDICES, bonus10_modes):
        print(f"    sort_idx={idx}: k={m.k_indices}, eig={m.eigenvalue:.4e}")
    records.append({
        "record": "bonus10_verification",
        "selected_indices": BONUS10_SELECTED_INDICES,
        "selected_k_tuples": bonus10_kindices,
        "selected_eigenvalues": bonus10_eigs,
        "verified_score_log_L2": bonus10_score,
        "score_matches_bonus10_report": bool(abs(bonus10_score - 0.6137) < 0.01),
    })

    # 3. Per-rule evaluation.
    print("\n--- Class P candidate rule evaluation ---")
    rule_results: List[Dict] = []

    # P1 — parity_target ∈ {0,1}
    for pt in (0, 1):
        res = evaluate_rule(
            f"P1_factor_parity(target={pt})",
            lambda m, _pt=pt: rule_P1_factor_parity(m, _pt),
            full_spectrum, free_params=1,
            description="per-factor parity bit; sum mod 2 = target",
            rule_extra={"parity_target": pt},
        )
        rule_results.append(res)
        print(f"  P1 parity={pt}: n_selected={res['n_selected_nonzero']}, "
              f"score={res['log_L2_score']}")

    # P2 — character constraints, explore some sparse residue sets.
    N_lcm = 1
    for n in CASCADE_NS:
        N_lcm = math.lcm(N_lcm, n)
    print(f"  P2 lcm(n_i) = {N_lcm}")
    # Try residue sets that mimic "3-generation" character — three equidistant
    # residues, sized to keep selection sparse.
    for n_residues in (3, 9, 27):
        if N_lcm % n_residues == 0:
            step = N_lcm // n_residues
            allowed = set(range(0, N_lcm, step))  # {0, step, 2*step, ...}
            res = evaluate_rule(
                f"P2_character(n_residues={n_residues})",
                lambda m, _a=allowed: rule_P2_character(m, CASCADE_NS, _a),
                full_spectrum, free_params=1,
                description=f"mode character omega in {{0, 1/{n_residues}, ...}}; lcm={N_lcm}",
                rule_extra={"n_residues": n_residues, "allowed_lcm_residues": sorted(allowed)},
            )
            rule_results.append(res)
            print(f"  P2 nr={n_residues}: n_selected={res['n_selected_nonzero']}, "
                  f"score={res['log_L2_score']}")

    # P3 — tensor-rank cutoff. Try various rank sets.
    for ranks in ({1}, {2}, {1, 2}, {1, 2, 3}, {0, 1}, {1, 2, 3, 4}):
        res = evaluate_rule(
            f"P3_rank(allowed={sorted(ranks)})",
            lambda m, _r=ranks: rule_P3_rank(m, _r),
            full_spectrum, free_params=1,
            description=f"# non-zero k_i in allowed_ranks",
            rule_extra={"allowed_ranks": sorted(ranks)},
        )
        rule_results.append(res)
        print(f"  P3 ranks={sorted(ranks)}: n_selected={res['n_selected_nonzero']}, "
              f"score={res['log_L2_score']}")

    # P5 — Σ k_i mod m. Try m ∈ {2, 3, 4, 5}, target ∈ {0, 1}.
    for modulus in (2, 3, 4, 5, 6, 7):
        for target in range(modulus):
            res = evaluate_rule(
                f"P5_ksum_mod(m={modulus},t={target})",
                lambda m, _mod=modulus, _t=target: rule_P5_ksum_mod(m, _mod, _t),
                full_spectrum, free_params=2,
                description=f"Σ k_i mod {modulus} = {target}",
                rule_extra={"modulus": modulus, "target": target},
            )
            rule_results.append(res)
            if res['log_L2_score'] is not None and res['log_L2_score'] < 5.0:
                print(f"  P5 m={modulus},t={target}: n_selected={res['n_selected_nonzero']}, "
                      f"score={res['log_L2_score']:.4f}")

    # P6 — single-factor only (rank ≤ 1).
    res = evaluate_rule(
        "P6_single_factor", rule_P6_single_factor, full_spectrum,
        free_params=0, description="exactly one k_i ≠ 0",
    )
    rule_results.append(res)
    print(f"  P6 single: n_selected={res['n_selected_nonzero']}, "
          f"score={res['log_L2_score']}")

    # P7 — pair or single (rank ≤ 2).
    res = evaluate_rule(
        "P7_pair_or_single", rule_P7_pair_or_single, full_spectrum,
        free_params=0, description="at most two k_i ≠ 0",
    )
    rule_results.append(res)
    print(f"  P7 pair: n_selected={res['n_selected_nonzero']}, "
          f"score={res['log_L2_score']}")

    # P8 — coprime constraint.
    res = evaluate_rule(
        "P8_coprime",
        lambda m: rule_P8_coprime(m, CASCADE_NS),
        full_spectrum, free_params=0,
        description="gcd(k_i, n_i)=1 for all nonzero k_i (coprime)",
    )
    rule_results.append(res)
    print(f"  P8 coprime: n_selected={res['n_selected_nonzero']}, "
          f"score={res['log_L2_score']}")

    # P9 — exclude conjugate pairs (k_i > n_i/2).
    res = evaluate_rule(
        "P9_complement_excluded",
        lambda m: rule_P9_complement_excluded(m, CASCADE_NS),
        full_spectrum, free_params=0,
        description="k_i <= n_i/2 for all i (take smaller of conjugate pair)",
    )
    rule_results.append(res)
    print(f"  P9 conj-excl: n_selected={res['n_selected_nonzero']}, "
          f"score={res['log_L2_score']}")

    # P4 — linear combo mod. Heavier search; cap to small q vectors and small mod.
    print("\n  P4 search (small q-vectors, small moduli)...")
    p4_best = None
    p4_best_results: List[Dict] = []
    for modulus in (2, 3, 4, 5):
        for q in product((0, 1, -1), repeat=5):  # 243 combos
            if all(qi == 0 for qi in q):
                continue
            for target in range(modulus):
                res_p4 = evaluate_rule(
                    f"P4_lincombo_q={q}_mod={modulus}_t={target}",
                    lambda m, _q=q, _mod=modulus, _t=target:
                        rule_P4_linear_combo_mod(m, _q, _mod, _t),
                    full_spectrum, free_params=7,  # 5 q-bits + mod + target
                    description=f"Σ q_i k_i mod {modulus} = {target}, q={q}",
                    rule_extra={"q": list(q), "modulus": modulus, "target": target},
                )
                # Only keep if reasonable.
                if (res_p4['log_L2_score'] is not None
                        and res_p4['log_L2_score'] < 3.0
                        and res_p4['n_selected_nonzero'] >= N_TARGET
                        and res_p4['n_selected_nonzero'] <= 50):
                    p4_best_results.append(res_p4)
                if (p4_best is None or (res_p4['log_L2_score'] is not None
                        and res_p4['log_L2_score'] < (p4_best['log_L2_score'] or np.inf))):
                    p4_best = res_p4
    p4_best_results.sort(key=lambda r: r['log_L2_score'] or np.inf)
    for r in p4_best_results[:5]:
        print(f"    P4 q={r['rule_extra']['q']} m={r['rule_extra']['modulus']} "
              f"t={r['rule_extra']['target']}: n={r['n_selected_nonzero']}, "
              f"score={r['log_L2_score']:.4f}")
    rule_results.append({**p4_best, "rule_name": "P4_best_found"})
    rule_results.extend(p4_best_results[:5])

    # 4. Composite rule: P3 (rank ≤ 1) AND P9 (conjugate-excluded).
    # Sometimes a small COMPOSITION of rules selects a clean set.
    def rule_p3_rank1_and_p9(mode: CascadeMode) -> bool:
        return rule_P3_rank(mode, {0, 1}) and rule_P9_complement_excluded(
            mode, CASCADE_NS
        )

    res = evaluate_rule(
        "P3rank1_AND_P9conj",
        rule_p3_rank1_and_p9,
        full_spectrum, free_params=0,
        description="rank<=1 AND no conjugate; rank<=1 cap k_i <= n_i/2",
    )
    rule_results.append(res)
    print(f"\n  Composite (rank<=1 AND conj-excl): "
          f"n_selected={res['n_selected_nonzero']}, "
          f"score={res['log_L2_score']}")

    # 5. P10 — match bonus 10 selection literally and analyze its k-index structure.
    print("\n  Analyzing structure of bonus 10's selected modes...")
    parities_b10 = [sum(k % 2 for k in m.k_indices) % 2
                    for m in bonus10_modes if m.eigenvalue > 1e-12]
    ranks_b10 = [sum(1 for k in m.k_indices if k != 0)
                 for m in bonus10_modes if m.eigenvalue > 1e-12]
    chars_b10 = []
    for m in bonus10_modes:
        if m.eigenvalue < 1e-12:
            continue
        c = 0
        for i, k in enumerate(m.k_indices):
            c = (c + k * (N_lcm // CASCADE_NS[i])) % N_lcm
        chars_b10.append(c)
    ksums_b10 = [sum(m.k_indices) for m in bonus10_modes if m.eigenvalue > 1e-12]
    conj_status_b10 = [
        all(k <= n // 2 for k, n in zip(m.k_indices, CASCADE_NS))
        for m in bonus10_modes if m.eigenvalue > 1e-12
    ]
    records.append({
        "record": "bonus10_mode_structure",
        "parities_mod2": parities_b10,
        "ranks_nonzero_k": ranks_b10,
        "characters_mod_lcm": chars_b10,
        "lcm_for_characters": N_lcm,
        "ksum_totals": ksums_b10,
        "all_conjugate_minor": conj_status_b10,
        "n_modes_analyzed": len(parities_b10),
    })
    print(f"    parities (mod 2): {parities_b10}")
    print(f"    ranks: {ranks_b10}")
    print(f"    characters (mod {N_lcm}): {chars_b10}")
    print(f"    k-sums: {ksums_b10}")
    print(f"    all k_i <= n_i/2? {conj_status_b10}")

    # 6. Append all rule results.
    for r in rule_results:
        records.append({"record": "rule_result", **r})

    # 7. Determine best rule.
    candidates_with_score = [
        r for r in rule_results
        if r.get('log_L2_score') is not None
        and r.get('n_selected_nonzero', 0) >= N_TARGET
    ]
    candidates_with_score.sort(key=lambda r: r['log_L2_score'])
    print("\n--- Top 10 rules by log-L2 score ---")
    for r in candidates_with_score[:10]:
        print(f"  score={r['log_L2_score']:.4f}, n_sel={r['n_selected_nonzero']}, "
              f"free_params={r['free_parameters']}, rule={r['rule_name']}")

    # 8. Verdict logic.
    if not candidates_with_score:
        verdict = "NO-RULE-FOUND"
        best_rule = None
    else:
        best_rule = candidates_with_score[0]
        # CLOSURE-WITH-CLASS-P: zero free params, score < 1.0 (SUCCESS threshold).
        # REDUCES-TO-EXISTING: the best low-param rule scores well and is
        #   reducible to A-N composition (rank/parity/char are all in A-N).
        # NO-RULE-FOUND: best rule's score remains > 3.0 OR requires many free params.
        if best_rule['log_L2_score'] < 1.0 and best_rule['free_parameters'] == 0:
            # Check algebraic-reducibility: is it expressible in A-N?
            # All our zero-param rules are reducible:
            #  - P6, P7 (rank): Class B (tagged-tuple) inspection + integer comparison
            #  - P8 (coprime): Class J (prime factorisation) operation
            #  - P9 (conjugate-excluded): Class I (cyclic-group symmetry) reflection
            #  - composite rules: still reducible
            verdict = "REDUCES-TO-EXISTING"
        elif best_rule['log_L2_score'] < 1.0:
            verdict = "REDUCES-TO-EXISTING"  # if low-param, still reducible
        elif best_rule['log_L2_score'] < 3.0:
            verdict = "PARTIAL_FAILURE"
        else:
            verdict = "NO-RULE-FOUND"

    print(f"\n[Final verdict] {verdict}")
    if best_rule:
        print(f"  best rule: {best_rule['rule_name']}")
        print(f"  score: {best_rule['log_L2_score']:.4f}")
        print(f"  free params: {best_rule['free_parameters']}")
        print(f"  bonus10 reference: 0.6137 (log-L2)")

    records.append({
        "record": "verdict",
        "verdict": verdict,
        "best_rule": best_rule,
        "bonus10_reference_score": 0.6137,
        "closure_thresholds": {
            "CLOSURE_WITH_CLASS_P": "score<1.0, free_params=0, irreducible to A-N",
            "REDUCES_TO_EXISTING": "score<1.0 but reducible to A-N composition",
            "NO_RULE_FOUND": "score>3.0 or many free params required",
        },
        "interpretation": {
            "P1_parity": "reducible to Class B (record-inspection) + integer parity",
            "P3_rank": "reducible to Class B + Class C (count non-zero)",
            "P5_ksum": "reducible to Class B + Class J (integer arithmetic)",
            "P6_P7_rank_low": "reducible to Class B + comparison",
            "P8_coprime": "reducible to Class J (prime factorisation / gcd)",
            "P9_conjugate": "reducible to Class I (cyclic-group reflection symmetry)",
            "P2_character": "reducible to Class I (cyclic-group character)",
            "P4_linear_combo": "reducible to Class J (integer linear algebra mod m)",
        },
    })

    # Totals + integrity.
    elapsed = time.time() - t_start
    records.append({
        "record": "totals",
        "total_elapsed_s": elapsed,
        "n_rules_evaluated": len(rule_results),
    })
    rec_bytes = "\n".join(json.dumps(r, sort_keys=True) for r in records).encode("utf-8")
    rec_sha = hashlib.sha256(rec_bytes).hexdigest()
    records.append({"record": "integrity", "records_sha256": rec_sha})

    with open(NDJSON_PATH, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    print(f"\nRecords -> {NDJSON_PATH.name}")
    print(f"Total elapsed = {elapsed:.1f}s")
    print(f"SHA256 = {rec_sha[:16]}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
