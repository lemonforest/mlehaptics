"""Spike #24 bonus 11d FOLLOWUP — exact-9-mode rule search.

The main probe established that NO low-parameter rule beats the bonus 10
floor of ~0.6 log-L2 — every "nice" rule (P9 conjugate, P3 rank≤2, P7 pair,
etc.) bottoms out at ~0.6013 because the bonus 10 greedy subset-match is
already restricted to the conjugate-half spectrum.

This followup tests the STRONGER question: is there a rule that selects
EXACTLY 9 modes (not "selects 332 modes, of which 9 happen to fit")? An
exact-9-mode rule with zero free parameters would be a genuine Class P
candidate; the cascade itself "naturally" picks out the 9 SM fermions.

Approach:
  1. Enumerate small rules that select small numbers of modes
  2. Filter to those that select 9-15 modes
  3. Compute best 9-mode score; check if < 1.0 dex
"""
from __future__ import annotations

import json
import math
import sys
import time
from itertools import product, combinations
from pathlib import Path
from typing import List, Tuple, Dict, Set

import numpy as np


SEED = 20260515
PROBE_NAME = "spike_24_bonus_11d_mode_selection_class_p_followup_2026-05-15"

HERE = Path(__file__).parent
NDJSON_PATH = HERE / "spike_24_bonus_11d_mode_selection_class_p_followup_2026-05-15.ndjson"

SM_FERMIONS = ["e", "u", "d", "s", "mu", "c", "tau", "b", "t"]
SM_MASSES_MEV = [0.511, 2.2, 4.7, 95.0, 105.7, 1270.0, 1777.0, 4180.0, 172760.0]
SM_MASS_SQ_RATIOS = np.array([(m / SM_MASSES_MEV[0]) ** 2 for m in SM_MASSES_MEV])
LOG10_TARGET = np.log10(SM_MASS_SQ_RATIOS)
N_TARGET = 9

CASCADE_NS = (2, 7, 4, 6, 16)
CASCADE_RS = (
    3659.03506590957,
    1.0286749515294853,
    1.442834378987582,
    104.19253977340335,
    135758.32777190334,
)


def cyclic_laplacian_eigenvalues(n: int, radius: float = 1.0) -> np.ndarray:
    k = np.arange(n)
    return (2.0 / radius**2) * (1.0 - np.cos(2.0 * math.pi * k / n))


def build_full_spectrum_keyed(ns, rs):
    factor_specs = [cyclic_laplacian_eigenvalues(n, r) for n, r in zip(ns, rs)]
    out = []
    for k_tuple in product(*[range(n) for n in ns]):
        eigvs = tuple(factor_specs[i][k_tuple[i]] for i in range(len(ns)))
        total = sum(eigvs)
        out.append((k_tuple, total))
    out.sort(key=lambda x: x[1])
    return out


def score_9_modes(modes_with_eigs):
    """Sort by eigenvalue, take anchor=lowest, compute log-L2."""
    nz = [(k, e) for k, e in modes_with_eigs if e > 1e-12]
    if len(nz) < N_TARGET:
        return np.inf
    nz.sort(key=lambda x: x[1])
    nz = nz[:N_TARGET]
    if len(nz) != N_TARGET:
        return np.inf
    eigs = np.array([e for _, e in nz])
    ratios = eigs / eigs[0]
    if np.any(ratios <= 0):
        return np.inf
    diffs = np.log10(ratios) - LOG10_TARGET
    return float(np.sqrt(np.sum(diffs**2)))


def main() -> int:
    t_start = time.time()
    records = []

    print("Building spectrum...")
    full = build_full_spectrum_keyed(CASCADE_NS, CASCADE_RS)
    print(f"  {len(full)} modes built")

    # Filter to conjugate-half (P9) since these are the irredundant modes.
    p9_modes = [(k, e) for k, e in full
                if all(ki <= ni // 2 for ki, ni in zip(k, CASCADE_NS))]
    p9_modes_nz = [(k, e) for k, e in p9_modes if e > 1e-12]
    print(f"  P9 conj-half modes: {len(p9_modes)} ({len(p9_modes_nz)} nonzero)")

    # ----------------------------------------------------------------------
    # Test 1: rule "exactly 9 nonzero modes" via VARIOUS sparse cuts.
    # ----------------------------------------------------------------------
    print("\n--- Test 1: rules that select exactly 9 modes ---")
    sparse_rules: List[Tuple[str, callable]] = []

    # Rule: only single-factor modes with k_i <= small_cap.
    # In conjugate-half: factor i contributes ni//2 distinct modes.
    # n=(2,7,4,6,16) -> ni//2 = (1,3,2,3,8) -> 17 single-factor nonzero modes.
    # That's 17, not 9.
    rank_le1_p9 = [(k, e) for k, e in p9_modes_nz
                   if sum(1 for ki in k if ki != 0) <= 1]
    print(f"  rank<=1 & P9: {len(rank_le1_p9)} modes")
    if len(rank_le1_p9) == N_TARGET:
        s = score_9_modes(rank_le1_p9)
        print(f"    -> EXACTLY 9 modes. score = {s:.4f}")
    else:
        print(f"    -> not 9 ({len(rank_le1_p9)}); first 9 score:")
        rank_le1_p9.sort(key=lambda x: x[1])
        s = score_9_modes(rank_le1_p9[:9])
        print(f"    first-9 score = {s:.4f}")

    # Rule: rank<=1 AND k_i must be a unit of C_{n_i} (coprime). For n=2 the only
    # nonzero unit is 1; for n=4 only 1,3 -> in conj-half only 1; for n=6 only
    # 1,5 -> in conj-half only 1; for n=16 odd k from 1..7 = 4 values; for n=7
    # all nonzero k from 1..3 are units = 3 values. So 1+1+1+4+3 = 10.
    def is_unit(k, n):
        return k != 0 and math.gcd(k, n) == 1

    rank_le1_unit_p9 = [
        (k, e) for k, e in p9_modes_nz
        if sum(1 for ki in k if ki != 0) <= 1
        and (all(ki == 0 for ki in k) or
             any(is_unit(ki, CASCADE_NS[i]) for i, ki in enumerate(k) if ki != 0))
    ]
    print(f"  rank<=1 & P9 & coprime: {len(rank_le1_unit_p9)} modes")

    # Rule: per-factor k_i ∈ {0, 1} only (the "first harmonic per factor").
    first_harmonic_only = [(k, e) for k, e in p9_modes_nz
                           if all(ki in (0, 1) for ki in k)]
    print(f"  k_i in {{0,1}} only: {len(first_harmonic_only)} modes")

    # Rule: at most one factor has k_i > 1; i.e., max-one "deep excitation"
    one_deep_only = [(k, e) for k, e in p9_modes_nz
                     if sum(1 for ki in k if ki > 1) <= 1]
    print(f"  at most one k_i > 1: {len(one_deep_only)} modes")

    # Rule: lattice "shell" — sum of k_i = small fixed value
    for ksum in range(1, 8):
        shell = [(k, e) for k, e in p9_modes_nz if sum(k) == ksum]
        if len(shell) >= N_TARGET:
            s = score_9_modes(shell[:N_TARGET])
            if s != np.inf and s < 5.0:
                print(f"  ksum=={ksum}: {len(shell)} modes; first-9 score = {s:.4f}")
        elif len(shell) > 0:
            print(f"  ksum=={ksum}: {len(shell)} modes (insufficient)")

    # Rule: at most one factor activated AND that factor's order is in a small set.
    # (Allowing only k_i nonzero on factor index in some allowed set.)
    print("\n  Single-factor restricted-factor rules:")
    for allowed_factors in (
        {0}, {1}, {2}, {3}, {4},
        {0, 1}, {0, 2}, {0, 3}, {0, 4}, {1, 4}, {3, 4}, {0, 3, 4},
    ):
        modes = [(k, e) for k, e in p9_modes_nz
                 if sum(1 for ki in k if ki != 0) == 1
                 and next(i for i, ki in enumerate(k) if ki != 0) in allowed_factors]
        if len(modes) == N_TARGET:
            s = score_9_modes(modes)
            print(f"    factors={allowed_factors}: EXACT-9; score={s:.4f}")
        elif len(modes) >= 5:
            print(f"    factors={allowed_factors}: {len(modes)} modes")

    # ----------------------------------------------------------------------
    # Test 2: search ALL EXACT-9 subsets of the lightest ~30 P9 modes,
    # find the best score, and check what algebraic property they share.
    # ----------------------------------------------------------------------
    print("\n--- Test 2: brute search of 9-subsets in lightest 30 P9 modes ---")
    p9_modes_nz.sort(key=lambda x: x[1])
    candidate_pool = p9_modes_nz[:30]
    print(f"  pool of 30 candidates; combinations = C(30,9) = {math.comb(30, 9)}")
    best_score = np.inf
    best_subset_indices = None
    best_subset_modes = None
    n_evals = 0
    for combo in combinations(range(len(candidate_pool)), N_TARGET):
        modes_subset = [candidate_pool[i] for i in combo]
        s = score_9_modes(modes_subset)
        n_evals += 1
        if s < best_score:
            best_score = s
            best_subset_indices = combo
            best_subset_modes = modes_subset
    print(f"  brute-force best score: {best_score:.4f}")
    if best_subset_modes:
        print("  best 9 k-tuples:")
        for k, e in best_subset_modes:
            print(f"    k={k}, eig={e:.4e}")
        # Algebraic properties.
        ks = [k for k, _ in best_subset_modes]
        ranks = [sum(1 for ki in k if ki != 0) for k in ks]
        parities = [sum(ki % 2 for ki in k) % 2 for k in ks]
        ksums = [sum(k) for k in ks]
        chars = []
        N_lcm = 1
        for n in CASCADE_NS:
            N_lcm = math.lcm(N_lcm, n)
        for k in ks:
            c = 0
            for i, ki in enumerate(k):
                c = (c + ki * (N_lcm // CASCADE_NS[i])) % N_lcm
            chars.append(c)
        print(f"  ranks: {ranks}")
        print(f"  parities: {parities}")
        print(f"  k-sums: {ksums}")
        print(f"  characters mod {N_lcm}: {chars}")
    records.append({
        "record": "brute_9_subset",
        "n_evals": n_evals,
        "pool_size": len(candidate_pool),
        "best_score": best_score,
        "best_subset_k_tuples": [list(k) for k, _ in (best_subset_modes or [])],
        "best_subset_eigenvalues": [e for _, e in (best_subset_modes or [])],
        "ranks": [sum(1 for ki in k if ki != 0) for k, _ in (best_subset_modes or [])],
        "parities": [sum(ki % 2 for ki in k) % 2 for k, _ in (best_subset_modes or [])],
        "ksums": [sum(k) for k, _ in (best_subset_modes or [])],
    })

    # ----------------------------------------------------------------------
    # Test 3: extend pool to lightest 60 for stronger lower-bound.
    # ----------------------------------------------------------------------
    print("\n--- Test 3: brute search over lightest 60 (C(60,9)=14M, sampled) ---")
    candidate_pool2 = p9_modes_nz[:60]
    print(f"  pool of 60; C(60,9) = {math.comb(60, 9):,}")
    # Random sample 200k.
    rng = np.random.default_rng(SEED)
    best_score2 = np.inf
    best_subset_modes2 = None
    n_samples = 200_000
    for _ in range(n_samples):
        combo = rng.choice(60, size=N_TARGET, replace=False)
        modes_subset = [candidate_pool2[i] for i in combo]
        s = score_9_modes(modes_subset)
        if s < best_score2:
            best_score2 = s
            best_subset_modes2 = modes_subset
    print(f"  sampled best: {best_score2:.4f}")
    if best_subset_modes2:
        ks2 = [k for k, _ in best_subset_modes2]
        ranks2 = [sum(1 for ki in k if ki != 0) for k in ks2]
        print(f"  ranks of best-60 subset: {ranks2}")
        # Greedy search around it for further improvement.
        improved = best_subset_modes2[:]
        for outer in range(20):
            changed = False
            for swap_in_idx in range(len(p9_modes_nz)):
                # Try replacing each current element.
                for swap_out_pos in range(N_TARGET):
                    candidate = improved[:]
                    cm = p9_modes_nz[swap_in_idx]
                    if cm in candidate:
                        continue
                    candidate[swap_out_pos] = cm
                    s = score_9_modes(candidate)
                    if s < best_score2:
                        best_score2 = s
                        improved = candidate
                        changed = True
            if not changed:
                break
        print(f"  after greedy: {best_score2:.4f}")
        records.append({
            "record": "brute_60_then_greedy",
            "pool_size": 60,
            "best_score_after_greedy": best_score2,
            "best_k_tuples": [list(k) for k, _ in improved],
        })

    elapsed = time.time() - t_start
    records.append({"record": "totals", "elapsed_s": elapsed})

    with open(NDJSON_PATH, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, default=float) + "\n")
    print(f"\nRecords -> {NDJSON_PATH.name}")
    print(f"elapsed = {elapsed:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
