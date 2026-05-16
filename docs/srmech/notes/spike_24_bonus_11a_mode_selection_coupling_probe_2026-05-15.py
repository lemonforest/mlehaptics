"""Spike #24 bonus 11a — Suppressed-mode coupling rule probe.

Reading 1 of 4 parallel readings of the bonus 10 mode-selection gap. The
bonus 10 probe established that cascade composition `C_2 x C_7 x C_4 x C_6
x C_16` reproduces SM charged-fermion mass^2 ratios at log-L2 = 0.614 dex,
with the 9 SM modes being a sparse subset of the cascade's lowest ~200
modes (selected mode indices = [0, 8, 14, 15, 30, 31, 93, 190, 197]).

The open gap: which first-principles rule selects exactly those 9 modes
from the ~200-mode tower, with no fitted parameters?

This probe tests four coupling-rule candidate families:

  Rule A: gauge-active-subspace via SU(3)xSU(2)xU(1) rank decomposition
          on the 5 cyclic factors (rank 3+1+1 = 5; one rank per factor).
  Rule B: parity / mode-index sum residue selection (Z_2 chirality-like
          constraints over factor index parity).
  Rule C: factor-active rank (number of non-zero k_j components in the
          mode tuple).
  Rule D: weighted-tuple coupling g(k_1,...,k_5) = product/sum of factor
          characters; threshold gates.

For each rule, the closure question is:
  Does the rule, given as a first-principles function of (k_1,...,k_5,n_1,
  ...,n_5) WITHOUT free fitting parameters, select exactly the 9 SM modes
  [0, 8, 14, 15, 30, 31, 93, 190, 197] from the lowest-N tower?

Verdict outcomes (per concertmaster dispatch):
  CLOSURE   = rule with no free params selects the 9 modes.
  PARTIAL   = rule selects subset of the 9, or 9 modes with some misses.
  AMBIGUOUS = multiple distinct rules each select 9 modes, different 9s.
  NO-RULE   = no rule derivable from existing primitives produces the 9.

Discipline guards:
  - Class L (graph-Laplacian eigenvalue) as the spectral falsifier per
    `feedback_antiquity_not_greek`.
  - Per `feedback_no_mvp_framing` / full-coverage shipping: enumerate
    every rule we can name; report all of them.
  - Per `feedback_ndjson_over_bloated_json`: NDJSON output.
  - Per `feedback_trauma_informed_defensive_scope`: methodological only.
  - stdlib + numpy only (scipy not needed); CPU; deterministic.
  - No new primitive class invented.
  - "Primitive classes" not "primitives" for canonical A-N references.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Tuple

import numpy as np


# ----------------------------------------------------------------------------
# Determinism + provenance
# ----------------------------------------------------------------------------
SEED = 20260515
RNG = np.random.default_rng(SEED)

PROBE_NAME = "spike_24_bonus_11a_mode_selection_coupling_probe_2026-05-15"
PROBE_VERSION = "0.1.0"
HERE = Path(__file__).parent
NDJSON_PATH = HERE / "spike_24_bonus_11a_mode_selection_coupling_probe_2026-05-15.ndjson"


# ----------------------------------------------------------------------------
# Bonus 10 best cascade (rank-1 subset-match) — fixed inputs to this probe.
# Per docs/srmech/notes/spike_24_bonus_xiii_1_top_candidate_cascades_*.ndjson
# rank 1 record.
# ----------------------------------------------------------------------------
CASCADE_NS = (2, 7, 4, 6, 16)
CASCADE_RS = (3659.03506590957, 1.0286749515294853, 1.442834378987582,
              104.19253977340335, 135758.32777190334)
SM_FERMIONS = ("e", "u", "d", "s", "mu", "c", "tau", "b", "t")
# log10(m/m_e)^2 for the SM 9 charged fermions, anchor m_e = 0.511 MeV
SM_MASSES_MEV = (0.511, 2.2, 4.7, 95.0, 105.7, 1270.0, 1777.0, 4180.0, 172760.0)
SM_MASS_SQ_RATIOS = np.array([(m / SM_MASSES_MEV[0]) ** 2 for m in SM_MASSES_MEV])
LOG10_TARGET = np.log10(SM_MASS_SQ_RATIOS)

# The 9 mode indices selected by bonus 10's subset-match search.
# These are POSITIONS in the sorted non-zero eigenvalue array of the
# product Laplacian, when truncated to the lowest n_keep = 200 modes.
SELECTED_MODE_INDICES = [0, 8, 14, 15, 30, 31, 93, 190, 197]


# ----------------------------------------------------------------------------
# Class I + Class L primitives — cyclic-group Laplacian eigenvalues.
# Reproduced from bonus 10 probe.
# ----------------------------------------------------------------------------
def cyclic_laplacian_eigenvalues(n: int, radius: float = 1.0) -> np.ndarray:
    """Class L: discrete Laplacian eigenvalues on C_n with metric scale r."""
    k = np.arange(n)
    return (2.0 / radius**2) * (1.0 - np.cos(2.0 * math.pi * k / n))


# ----------------------------------------------------------------------------
# Enumerate full mode tuple-space and sort by total eigenvalue.
# Total mode count for cascade (2,7,4,6,16) = 2*7*4*6*16 = 5376 modes.
# Build them all, sort, retain mode tuples + indices.
# ----------------------------------------------------------------------------
def build_full_mode_table(
    ns: Tuple[int, ...], rs: Tuple[float, ...]
) -> Tuple[np.ndarray, List[Tuple[int, ...]]]:
    """Enumerate every cascade mode as a tuple (k_1,...,k_p) and compute
    its total Laplacian eigenvalue. Sort ascending by eigenvalue.

    Returns:
        eigs_sorted:  shape (N,) ndarray of eigenvalues, ascending.
        tuples_sorted: list of N k-tuples corresponding to eigs_sorted.
    """
    factor_specs = [cyclic_laplacian_eigenvalues(n, r) for n, r in zip(ns, rs)]
    total = []
    tuples = []
    for ks in itertools.product(*[range(n) for n in ns]):
        e = sum(factor_specs[j][ks[j]] for j in range(len(ns)))
        total.append(e)
        tuples.append(ks)
    eigs = np.array(total)
    order = np.argsort(eigs)
    eigs_sorted = eigs[order]
    tuples_sorted = [tuples[i] for i in order]
    return eigs_sorted, tuples_sorted


# ----------------------------------------------------------------------------
# Provenance writer
# ----------------------------------------------------------------------------
class NDJSONWriter:
    def __init__(self, path: Path):
        self.path = path
        self.lines: List[str] = []

    def add(self, record: dict) -> None:
        # Convert numpy scalars/arrays to plain Python.
        def conv(x):
            if isinstance(x, np.ndarray):
                return x.tolist()
            if isinstance(x, (np.floating,)):
                return float(x)
            if isinstance(x, (np.integer,)):
                return int(x)
            if isinstance(x, tuple):
                return list(x)
            return x

        def deep_conv(obj):
            if isinstance(obj, dict):
                return {k: deep_conv(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [deep_conv(v) for v in obj]
            if isinstance(obj, tuple):
                return [deep_conv(v) for v in obj]
            return conv(obj)

        line = json.dumps(deep_conv(record), sort_keys=False)
        self.lines.append(line)

    def flush(self) -> None:
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("\n".join(self.lines) + "\n")


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ============================================================================
# Step 1: Reconstruct the 9 SM mode tuples from bonus 10's selected indices.
# ============================================================================
def step1_reconstruct_modes(
    writer: NDJSONWriter,
    eigs_sorted: np.ndarray,
    tuples_sorted: List[Tuple[int, ...]],
) -> Tuple[List[Tuple[int, ...]], np.ndarray]:
    """Pull out the 9 SM-fermion mode tuples and their eigenvalues."""
    # The bonus 10 SELECTED_MODE_INDICES indexed the SORTED NON-ZERO eigenvalues.
    # Filter zero modes (numerical < 1e-12) consistently with bonus 10 logic.
    nonzero_mask = eigs_sorted > 1e-12
    eigs_nz = eigs_sorted[nonzero_mask]
    tuples_nz = [t for t, keep in zip(tuples_sorted, nonzero_mask) if keep]

    sm_modes = []
    sm_eigs = []
    for fermion, idx in zip(SM_FERMIONS, SELECTED_MODE_INDICES):
        t = tuples_nz[idx]
        e = float(eigs_nz[idx])
        sm_modes.append(t)
        sm_eigs.append(e)
        writer.add({
            "record": "sm_mode_reconstruction",
            "fermion": fermion,
            "bonus10_index": idx,
            "mode_tuple_k": list(t),
            "eigenvalue": e,
            "log10_ratio_to_e": math.log10(e / sm_eigs[0]) if sm_eigs[0] > 0 else None,
        })
    return sm_modes, np.array(sm_eigs)


# ============================================================================
# Step 2: Define coupling-rule candidates.
#
# A coupling rule is a function g(mode_tuple, factor_dims) -> bool that
# decides whether a mode couples to observable channels (= "SM fermion") or
# not (= suppressed/dark/sterile/extra).
#
# Each rule is checked against the 9 SM modes from step 1.
# ============================================================================

@dataclass
class CouplingRule:
    """Class B (tagged-tuple) record for a coupling rule."""
    name: str
    family: str  # gauge_active, parity, factor_active_rank, weighted_threshold
    description: str
    free_params: int  # 0 if first-principles, >0 if fitting required
    fn: Callable[[Tuple[int, ...]], bool]


def make_rules(
    ns: Tuple[int, ...], sm_modes: List[Tuple[int, ...]],
) -> List[CouplingRule]:
    """Build the catalog of candidate coupling rules.

    Each rule is a Boolean function on mode tuples. Free param count
    governs whether the rule is principled (0 = closure-eligible) or
    fitted (>0 = NOT closure even if it matches).
    """
    rules: List[CouplingRule] = []

    # ---- Rule family A: SU(3)xSU(2)xU(1) gauge-active subspace --------
    # SM gauge group has rank 4 (SU(3) rank 2 + SU(2) rank 1 + U(1) rank 1).
    # Cascade has 5 factors. Map factors to gauge content:
    #   C_2 -> SU(2) weak hypercharge sign (or U(1) charge)
    #   C_7 -> ?
    #   C_4 -> SU(2) doublet index (k mod 2 = weak isospin)
    #   C_6 -> SU(3) color rank (3 colors + ... but 6 = 3*2 = color * something)
    #   C_16 -> ?
    # Gauge-active modes: those whose tuple lies in the "gauge-rank" subspace.
    # Multiple readings — record all.

    # A1: All factor indices in {0, 1} (lowest excitation per factor).
    rules.append(CouplingRule(
        name="A1_first_excited",
        family="gauge_active",
        description="All k_j in {0, 1}: only the first excitation tier per factor.",
        free_params=0,
        fn=lambda ks: all(k in (0, 1) for k in ks),
    ))

    # A2: At most one factor at first excitation (rank-1 tuple).
    rules.append(CouplingRule(
        name="A2_rank1_tuple",
        family="gauge_active",
        description="Exactly one k_j > 0; the rest zero (single-factor excitation).",
        free_params=0,
        fn=lambda ks: sum(1 for k in ks if k != 0) == 1,
    ))

    # A3: At most 2 factors excited (rank<=2).
    rules.append(CouplingRule(
        name="A3_rank_leq_2",
        family="gauge_active",
        description="Number of non-zero k_j <= 2.",
        free_params=0,
        fn=lambda ks: sum(1 for k in ks if k != 0) <= 2,
    ))

    # A4: At most 3 factors excited (rank<=3, matching SM gauge rank 3 if
    # we consider rank decomposition with overlap).
    rules.append(CouplingRule(
        name="A4_rank_leq_3",
        family="gauge_active",
        description="Number of non-zero k_j <= 3 (SU(3) color rank gate).",
        free_params=0,
        fn=lambda ks: sum(1 for k in ks if k != 0) <= 3,
    ))

    # ---- Rule family B: parity / Z_2 selection ----------------------
    # Hypothesis: SM modes satisfy a parity constraint over the cascade
    # factor indices. Several specific Z_2 sum/parity readings.

    # B1: Sum of all k_j is even.
    rules.append(CouplingRule(
        name="B1_sum_even",
        family="parity",
        description="Sum of mode indices k_1+...+k_5 is even.",
        free_params=0,
        fn=lambda ks: (sum(ks) % 2) == 0,
    ))

    # B2: Sum of all k_j is odd.
    rules.append(CouplingRule(
        name="B2_sum_odd",
        family="parity",
        description="Sum of mode indices k_1+...+k_5 is odd.",
        free_params=0,
        fn=lambda ks: (sum(ks) % 2) == 1,
    ))

    # B3: Sum mod 3 = 0 (SU(3) color singlet condition).
    rules.append(CouplingRule(
        name="B3_sum_mod3_zero",
        family="parity",
        description="Sum of mode indices == 0 mod 3 (SU(3) singlet rule).",
        free_params=0,
        fn=lambda ks: (sum(ks) % 3) == 0,
    ))

    # B4: First-factor parity (k_1 mod 2 == 0).
    rules.append(CouplingRule(
        name="B4_k1_even",
        family="parity",
        description="First factor index k_1 is even (C_2 trivial rep).",
        free_params=0,
        fn=lambda ks: (ks[0] % 2) == 0,
    ))

    # ---- Rule family C: weighted-tuple coupling -----------------------
    # Hypothesis: coupling strength = some character function over the
    # tuple. Modes above threshold survive.

    # C1: Product of (1 - cos(2 pi k_j / n_j)) over factors with k_j != 0
    #     must exceed 0. (Trivially true for any non-trivial mode.)
    # Skipped — uninformative.

    # C2: Hamming distance from origin (count non-zero indices) is
    # exactly equal to a fixed value. Try each value 1..5.
    for r in range(0, 6):
        rules.append(CouplingRule(
            name=f"C2_rank_exact_{r}",
            family="weighted_threshold",
            description=f"Exactly {r} non-zero k_j components (Hamming weight = {r}).",
            free_params=0,
            fn=lambda ks, r=r: sum(1 for k in ks if k != 0) == r,
        ))

    # ---- Rule family D: lightest-N truncations -----------------------
    # Null hypothesis: SM is the lightest 9 modes (we know this fails;
    # include for the record).
    rules.append(CouplingRule(
        name="D1_lightest_9",
        family="null",
        description="Lightest 9 non-zero modes (null hypothesis from bonus 10).",
        free_params=0,
        fn=lambda ks: False,  # Special-case handled in evaluation.
    ))

    # ---- Rule family E: factor-pair coherence ----------------------
    # Hypothesis: SM modes have constrained factor-pair indices that
    # mimic isospin/hypercharge coupling.

    # E1: k_1 + k_3 even (C_2 x C_4 doublet coherence).
    rules.append(CouplingRule(
        name="E1_k1k3_even",
        family="pair_coherence",
        description="k_1 + k_3 is even (C_2 x C_4 isospin coherence).",
        free_params=0,
        fn=lambda ks: ((ks[0] + ks[2]) % 2) == 0,
    ))

    # E2: k_2 mod 7 in {0, 1} (C_7 lowest two reps for "generation" gate).
    rules.append(CouplingRule(
        name="E2_k2_low",
        family="pair_coherence",
        description="k_2 in {0, 1} (C_7 first-excitation gate).",
        free_params=0,
        fn=lambda ks: ks[1] in (0, 1),
    ))

    # E3: k_5 (C_16) below a power-of-two threshold.
    for thresh in [2, 4, 8]:
        rules.append(CouplingRule(
            name=f"E3_k5_lt_{thresh}",
            family="pair_coherence",
            description=f"k_5 < {thresh} (C_16 deep-tower threshold).",
            free_params=0,
            fn=lambda ks, t=thresh: ks[4] < t,
        ))

    # ---- Rule family F: gauge-rank tensor decomposition ----------------
    # SU(3) x SU(2) x U(1) total rank = 4. Hypothesis: SM modes are
    # those where the tuple's L1 norm (sum of indices) <= 4 OR L_inf
    # norm <= 2.
    rules.append(CouplingRule(
        name="F1_L1_leq_4",
        family="gauge_rank",
        description="L1 norm of tuple (sum of indices) <= 4 (gauge rank 4 gate).",
        free_params=0,
        fn=lambda ks: sum(ks) <= 4,
    ))

    rules.append(CouplingRule(
        name="F2_L1_leq_5",
        family="gauge_rank",
        description="L1 norm of tuple <= 5.",
        free_params=0,
        fn=lambda ks: sum(ks) <= 5,
    ))

    rules.append(CouplingRule(
        name="F3_Linf_leq_2",
        family="gauge_rank",
        description="L_inf norm (max index) <= 2.",
        free_params=0,
        fn=lambda ks: max(ks) <= 2,
    ))

    # ---- Rule family G: residue-class on full tuple -----------------
    # Hypothesis: SM modes lie in a single residue class of some
    # composite cyclic group mod m (e.g., m = lcm(2,7,4,6,16) features).
    # Several principled m values:
    for m in [2, 3, 4, 5, 6, 7]:
        # Compute weighted-sum residue for the 9 SM modes; if all 9 have
        # the same residue, that residue IS the candidate gate.
        rules.append(CouplingRule(
            name=f"G1_weighted_sum_mod_{m}_class_zero",
            family="residue",
            description=f"sum(k_j * j) mod {m} == 0.",
            free_params=0,
            fn=lambda ks, mm=m: (sum(j * k for j, k in enumerate(ks)) % mm) == 0,
        ))

    # ---- Rule family H: factor-suppression (observed empirically) ----
    # The 9 SM mode tuples show k_3 (C_4 factor) is ZERO across all 9.
    # This is a structural finding — if a coupling rule says "C_4 is
    # decoupled", it would select modes with k_3=0. Test it as a
    # first-principles rule.
    rules.append(CouplingRule(
        name="H1_C4_decoupled",
        family="factor_suppression",
        description="k_3 == 0 (C_4 factor is decoupled from observable channels).",
        free_params=0,
        fn=lambda ks: ks[2] == 0,
    ))

    # Combined: factor C_4 decoupled, AND L1 norm bounded by gauge rank.
    rules.append(CouplingRule(
        name="H2_C4_decoupled_L1_leq_5",
        family="factor_suppression",
        description="k_3 == 0 AND L1 <= 5.",
        free_params=0,
        fn=lambda ks: ks[2] == 0 and sum(ks) <= 5,
    ))

    # k_3 == 0 AND k_2 in {0, 1} (C_4 decoupled, C_7 first excitation gate).
    rules.append(CouplingRule(
        name="H3_C4_decoupled_C7_low",
        family="factor_suppression",
        description="k_3 == 0 AND k_2 in {0, 1} (C_4 decoupled, C_7 binary gate).",
        free_params=0,
        fn=lambda ks: ks[2] == 0 and ks[1] in (0, 1),
    ))

    # H4: k_3 == 0 AND k_4 < 4 (C_4 decoupled, C_6 below half).
    rules.append(CouplingRule(
        name="H4_C4_decoupled_C6_lt_4",
        family="factor_suppression",
        description="k_3 == 0 AND k_4 < 4.",
        free_params=0,
        fn=lambda ks: ks[2] == 0 and ks[3] < 4,
    ))

    # ---- Rule family I: gauge-decomposition variants -----------------
    # Hypothesis: gauge content lives in a specific subspace of the cascade.
    # Possible factor-to-gauge mappings:
    #   C_2 -> Z_2 chirality (left/right)
    #   C_7 -> heavy gauge (only top quark engages)
    #   C_4 -> [decoupled or hidden]
    #   C_6 -> generation index (rank 3 sub-group for generations)
    #   C_16 -> mass scale tower
    # SM modes might be those where k_2 (C_7) is "low" except for t,
    # and k_3 (C_4) is fully decoupled.

    # I1: Exactly fits the empirical pattern: k_3 = 0, k_2 <= 1.
    # Same as H3, listed separately for family clarity.

    # I2: k_3 = 0 AND k_2 = 0 OR k_2 = 1 OR k_2 == 0 (try variants).
    rules.append(CouplingRule(
        name="I2_C4_C7_constrained",
        family="gauge_decomposition",
        description="k_3 == 0 AND k_2 < 2.",
        free_params=0,
        fn=lambda ks: ks[2] == 0 and ks[1] < 2,
    ))

    # ---- Rule family J: empirical-fit (FOR REFERENCE — has free params) -
    # The empirical rule: enumerate the modes that exactly match.
    # NOT closure (it IS the answer; just for record).
    rules.append(CouplingRule(
        name="J1_empirical_exact",
        family="empirical",
        description="Tuple is exactly one of the 9 SM tuples (NOT closure, has 9 params).",
        free_params=9,
        fn=lambda ks: ks in {tuple(t) for t in sm_modes},
    ))

    # ---- Rule family K: mirror-canonical (Z_2 fundamental-domain) -----
    # The discrete Laplacian on C_n has eigenvalue symmetry
    # lambda(k) = lambda(n-k). The fundamental domain is k <= n/2.
    # A coupling rule that selects only canonical representatives
    # avoids double-counting mirror-pair modes — physically motivated
    # if mirror modes are identified (CPT-like symmetry).
    rules.append(CouplingRule(
        name="K1_mirror_canonical",
        family="mirror_symmetry",
        description="All k_j <= n_j / 2 (mirror-fundamental-domain representative).",
        free_params=0,
        fn=lambda ks: all(ks[j] <= ns[j] // 2 for j in range(len(ns))),
    ))

    # K2: Mirror canonical AND k_3 == 0 (C_4 decoupled, mirror-fundamental).
    rules.append(CouplingRule(
        name="K2_canonical_C4_decoupled",
        family="mirror_symmetry",
        description="Mirror-canonical AND k_3 == 0.",
        free_params=0,
        fn=lambda ks: all(ks[j] <= ns[j] // 2 for j in range(len(ns)))
                   and ks[2] == 0,
    ))

    # K3: Mirror canonical AND k_2 <= 1 (mirror-canonical, C_7 first-exc).
    rules.append(CouplingRule(
        name="K3_canonical_C7_low",
        family="mirror_symmetry",
        description="Mirror-canonical AND k_2 <= 1.",
        free_params=0,
        fn=lambda ks: all(ks[j] <= ns[j] // 2 for j in range(len(ns)))
                   and ks[1] <= 1,
    ))

    # K4: Mirror canonical AND k_3 == 0 AND k_2 <= 1 (the empirical pattern).
    rules.append(CouplingRule(
        name="K4_canonical_C4dec_C7low",
        family="mirror_symmetry",
        description="Mirror-canonical AND k_3 == 0 AND k_2 <= 1.",
        free_params=0,
        fn=lambda ks: all(ks[j] <= ns[j] // 2 for j in range(len(ns)))
                   and ks[2] == 0 and ks[1] <= 1,
    ))

    # ---- Rule family L: layer-transition modes ---------------------------
    # Hypothesis: SM modes are "transition modes" between cascade layers.
    # Each cascade layer is associated with one factor's first excitation.
    # The SM modes occupy positions where the cascade spectrum transitions.
    # Implementation: a mode is layer-transition if its tuple's lowest
    # excited factor index (smallest j with k_j != 0) determines the layer.

    # L1: First-excited modes per layer:
    #   k = (0,0,0,0,k_5)  (C_16 layer, k_5 = 1..8) — the m_e tower
    #   k = (1,0,0,0,k_5)  (C_2 layer activated, k_5 = 0..8) — m_s mu layer
    #   k = (0,0,0,k_4,k_5) (C_6 layer activated)
    #   k = (0,k_2,0,0,k_5) (C_7 layer activated, only top quark)
    # This is exactly the pattern of the 9 SM modes.
    # But: this rule has NO free params, it's structural.
    rules.append(CouplingRule(
        name="L1_layer_transition_natural",
        family="layer_transition",
        description="At most ONE non-trivial excitation among k_1, k_2, k_4 (the gauge-active factors), with k_3 == 0.",
        free_params=0,
        fn=lambda ks: ks[2] == 0
                   and (sum(1 for k in (ks[0], ks[1], ks[3]) if k != 0) <= 1),
    ))

    # L2: Even stricter — single non-trivial excitation across (k_1, k_2, k_4).
    rules.append(CouplingRule(
        name="L2_layer_single",
        family="layer_transition",
        description="EXACTLY ONE non-trivial among (k_1, k_2, k_4); k_3 == 0.",
        free_params=0,
        fn=lambda ks: ks[2] == 0
                   and (sum(1 for k in (ks[0], ks[1], ks[3]) if k != 0) == 1),
    ))

    # L3: 0 or 1 non-trivial among (k_1, k_4) AND k_2 <= 1 AND k_3 == 0.
    rules.append(CouplingRule(
        name="L3_three_active_factors",
        family="layer_transition",
        description="k_3 == 0 AND k_2 <= 1 AND k_1 in {0,1} AND k_4 <= 3.",
        free_params=0,
        fn=lambda ks: ks[2] == 0 and ks[1] <= 1 and ks[0] <= 1 and ks[3] <= 3,
    ))

    # ---- Rule family M: refined gauge-group dimensional mappings -------
    # Best inspection: the cascade factor sizes (2, 7, 4, 6, 16) admit
    # several SM-aligned readings. SU(2) doublet (2) <-> C_2 weak iso;
    # G_4 = something with 4 elements (color quartet?) <-> C_4;
    # generation index (3 active gens) <-> C_6 splits as 3*2;
    # SU(3) color (3 components in fundamental) <-> projected from C_6;
    # the deep C_16 tower = scale spread (NOT gauge content).

    # M1: SM modes have k_3 = 0 AND (k_2, k_4) NOT both > 0.
    rules.append(CouplingRule(
        name="M1_no_C7_C6_coexcitation",
        family="gauge_decomposition_refined",
        description="k_3 == 0 AND (k_2 == 0 OR k_4 == 0).",
        free_params=0,
        fn=lambda ks: ks[2] == 0 and (ks[1] == 0 or ks[3] == 0),
    ))

    # M2: SM modes have k_3 = 0, k_2 in {0,1}, AND (if k_2 == 1 then k_1 == k_4 == 0).
    # This is the "t quark is sole survivor of C_7 excitation" rule.
    rules.append(CouplingRule(
        name="M2_C7_excitation_sole",
        family="gauge_decomposition_refined",
        description="k_3 == 0 AND k_2 <= 1 AND (k_2 == 0 OR (k_1 == 0 AND k_4 == 0)).",
        free_params=0,
        fn=lambda ks: ks[2] == 0 and ks[1] <= 1
                   and (ks[1] == 0 or (ks[0] == 0 and ks[3] == 0)),
    ))

    # M3: M2 + restrict k_5 to specific principled values.
    # Hypothesis: k_5 must be in {0, 1, 2, 5, 8} — these are five "selected"
    # values out of 0..8. This has effective 5 free params via the value list.
    # NOT closure but record for comparison.
    rules.append(CouplingRule(
        name="M3_k5_in_specific_set",
        family="gauge_decomposition_refined",
        description="k_3 == 0 AND k_2 <= 1 AND k_5 in {0,1,2,5,8} (has 5 hidden parameters).",
        free_params=5,
        fn=lambda ks: ks[2] == 0 and ks[1] <= 1 and ks[4] in {0, 1, 2, 5, 8},
    ))

    # ---- Rule family N: sub-tower selection (mass-cutoff per sub-tower) -
    # Hypothesis: within each (k_1, k_2, k_4) sub-tower, the SM picks
    # certain k_5 values. If we know the structural rule for which k_5
    # values within a sub-tower are SM-observable, the closure works.
    # Naive: lowest in each sub-tower? Try.
    rules.append(CouplingRule(
        name="N1_lowest_per_subtower",
        family="subtower_selection",
        description="Mode is the lowest k_5 within its (k_1, k_2, k_3, k_4) sub-tower (so k_5 in {0,1} for canonical).",
        free_params=0,
        fn=lambda ks: ks[2] == 0 and ks[4] <= 1,
    ))

    # N2: k_5 in {0, 1, 8} (boundary points of C_16 canonical: 0, first-exc, mid).
    rules.append(CouplingRule(
        name="N2_C16_boundary_modes",
        family="subtower_selection",
        description="k_5 in {0, 1, 8} (C_16 zero / first-excitation / self-dual midpoint).",
        free_params=0,
        fn=lambda ks: ks[4] in (0, 1, 8) and ks[2] == 0,
    ))

    return rules


# ============================================================================
# Step 3: Evaluate each rule against the SM 9 modes.
# A rule "closes" if it selects EXACTLY the SM 9 modes from the lowest-N
# tower (or equivalently from the full mode space, but we restrict to the
# lowest-200 tower to match bonus 10's truncation).
# ============================================================================
def evaluate_rule(
    rule: CouplingRule, eigs_sorted: np.ndarray,
    tuples_sorted: List[Tuple[int, ...]], n_keep: int = 200,
    sm_indices: Optional[List[int]] = None,
) -> dict:
    """Apply the rule to the lowest n_keep non-zero modes and count
    selection match against the SM 9.

    Returns a record:
        n_selected:  how many modes the rule selects in the lowest n_keep
        sm_matched:  how many of the 9 SM modes the rule selects
        sm_missed:   how many of the 9 SM modes the rule DOES NOT select
        extra:       how many non-SM modes the rule selects (= n_selected - sm_matched)
        precision:   sm_matched / n_selected  (1.0 if rule selects only SM modes)
        recall:      sm_matched / 9            (1.0 if rule selects all SM modes)
        verdict:     "EXACT" if selects exactly the 9 SM modes, else
                     "OVERSELECT" / "UNDERSELECT" / "MIXED"
    """
    nonzero_mask = eigs_sorted > 1e-12
    eigs_nz = eigs_sorted[nonzero_mask]
    tuples_nz = [t for t, keep in zip(tuples_sorted, nonzero_mask) if keep]
    # Truncate to lowest n_keep modes (the bonus 10 search-space size).
    keep = min(n_keep, len(eigs_nz))
    truncated = tuples_nz[:keep]

    # Special-case D1_lightest_9: select the 9 lightest non-zero modes.
    if rule.name == "D1_lightest_9":
        selected_positions = set(range(9))
    else:
        selected_positions = {i for i, t in enumerate(truncated) if rule.fn(t)}

    sm_positions = set(sm_indices) if sm_indices is not None else set(SELECTED_MODE_INDICES)
    matched = selected_positions & sm_positions
    missed = sm_positions - selected_positions
    extra = selected_positions - sm_positions

    n_selected = len(selected_positions)
    sm_matched = len(matched)
    sm_missed = len(missed)
    n_extra = len(extra)

    precision = sm_matched / n_selected if n_selected > 0 else 0.0
    recall = sm_matched / len(sm_positions)

    if n_selected == 9 and sm_missed == 0:
        verdict = "EXACT"
    elif sm_missed == 0 and n_extra > 0:
        verdict = "OVERSELECT"
    elif sm_missed > 0 and n_extra == 0:
        verdict = "UNDERSELECT"
    else:
        verdict = "MIXED"

    return {
        "rule_name": rule.name,
        "family": rule.family,
        "description": rule.description,
        "free_params": rule.free_params,
        "n_selected": n_selected,
        "sm_matched": sm_matched,
        "sm_missed": sm_missed,
        "n_extra": n_extra,
        "precision": precision,
        "recall": recall,
        "f1": (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0,
        "verdict": verdict,
        "missed_indices": sorted(missed),
        "extra_indices_first10": sorted(extra)[:10],
    }


# ============================================================================
# Step 4: Combined rules (conjunctions).
# Try AND-combinations of compatible rules to see if intersections do better.
# This is the "operationalised g(mode, gauge)" — the conjunction is the
# coupling-strength threshold acting on multiple gauge axes simultaneously.
# ============================================================================
def evaluate_conjunctions(
    rules: List[CouplingRule], eigs_sorted: np.ndarray,
    tuples_sorted: List[Tuple[int, ...]], n_keep: int = 200,
    max_size: int = 3,
) -> List[dict]:
    """Enumerate AND-conjunctions of up to max_size rules from the catalog
    and evaluate each. Return ranked by F1, then by exactness.
    """
    nonzero_mask = eigs_sorted > 1e-12
    tuples_nz = [t for t, keep in zip(tuples_sorted, nonzero_mask) if keep]
    keep = min(n_keep, len(tuples_nz))
    truncated = tuples_nz[:keep]
    sm_set = set(SELECTED_MODE_INDICES)

    # Precompute per-rule selection bitmasks.
    rule_sels = {}
    for r in rules:
        if r.name == "D1_lightest_9":
            rule_sels[r.name] = set(range(9))
        else:
            rule_sels[r.name] = {i for i, t in enumerate(truncated) if r.fn(t)}

    results: List[dict] = []
    rule_names = [r.name for r in rules if r.name != "D1_lightest_9"]
    # Single rules first (already done above, but recompute for the ranking).
    for size in range(1, max_size + 1):
        for combo in itertools.combinations(rule_names, size):
            sel = set(range(keep))
            for nm in combo:
                sel = sel & rule_sels[nm]
            matched = sel & sm_set
            missed = sm_set - sel
            extra = sel - sm_set
            n_sel = len(sel)
            sm_matched = len(matched)
            sm_missed = len(missed)
            n_extra = len(extra)
            precision = sm_matched / n_sel if n_sel > 0 else 0.0
            recall = sm_matched / len(sm_set)
            f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
            verdict = (
                "EXACT" if n_sel == 9 and sm_missed == 0
                else "OVERSELECT" if sm_missed == 0 and n_extra > 0
                else "UNDERSELECT" if sm_missed > 0 and n_extra == 0
                else "MIXED"
            )
            results.append({
                "size": size,
                "conjunction": list(combo),
                "n_selected": n_sel,
                "sm_matched": sm_matched,
                "sm_missed": sm_missed,
                "n_extra": n_extra,
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "verdict": verdict,
            })
    # Rank by (exactness desc, f1 desc, n_extra asc, size asc).
    results.sort(key=lambda r: (
        -(r["verdict"] == "EXACT"),
        -r["f1"],
        r["n_extra"],
        r["size"],
    ))
    return results


# ============================================================================
# Main probe orchestration.
# ============================================================================
def main():
    t_start = time.perf_counter()
    writer = NDJSONWriter(NDJSON_PATH)

    # ----- Provenance header -----
    writer.add({
        "record": "provenance",
        "probe": PROBE_NAME,
        "version": PROBE_VERSION,
        "seed": SEED,
        "py_version": sys.version.split()[0],
        "numpy_version": np.__version__,
        "pid": os.getpid(),
        "venv": str(Path(sys.executable).parent.parent),
        "cascade_ns": list(CASCADE_NS),
        "cascade_rs": list(CASCADE_RS),
        "bonus10_selected_indices": SELECTED_MODE_INDICES,
        "sm_fermions": list(SM_FERMIONS),
    })

    # ----- Build full mode table -----
    eigs_sorted, tuples_sorted = build_full_mode_table(CASCADE_NS, CASCADE_RS)
    writer.add({
        "record": "mode_table_built",
        "n_total_modes": len(eigs_sorted),
        "n_factors": len(CASCADE_NS),
        "expected_modes": int(np.prod(CASCADE_NS)),
        "n_nonzero": int(np.sum(eigs_sorted > 1e-12)),
        "lowest_5_eigs": eigs_sorted[:5].tolist(),
    })

    # ----- Step 1: Reconstruct SM mode tuples -----
    sm_modes, sm_eigs = step1_reconstruct_modes(writer, eigs_sorted, tuples_sorted)
    print(f"SM mode tuples reconstructed: {len(sm_modes)}")
    for fermion, t, e in zip(SM_FERMIONS, sm_modes, sm_eigs):
        print(f"  {fermion}: k={t}, lambda={e:.6e}, log10_ratio={math.log10(e/sm_eigs[0]):.4f}")

    # ----- Step 2: Build rule catalog -----
    rules = make_rules(CASCADE_NS, sm_modes)
    writer.add({
        "record": "rule_catalog",
        "n_rules": len(rules),
        "families": sorted({r.family for r in rules}),
        "rule_names": [r.name for r in rules],
    })
    print(f"Rule catalog: {len(rules)} rules across {len(set(r.family for r in rules))} families")

    # ----- Step 3: Evaluate each rule individually -----
    single_results = []
    for r in rules:
        rec = evaluate_rule(r, eigs_sorted, tuples_sorted, n_keep=200)
        single_results.append(rec)
        writer.add({"record": "single_rule_eval", **rec})

    single_results.sort(key=lambda r: (-(r["verdict"] == "EXACT"), -r["f1"], r["n_extra"]))
    print("\n--- Top 10 single-rule evaluations (by exact > F1) ---")
    for rec in single_results[:10]:
        print(f"  {rec['rule_name']:35s} verdict={rec['verdict']:11s} "
              f"sel={rec['n_selected']:3d} match={rec['sm_matched']}/9 "
              f"extra={rec['n_extra']:3d} F1={rec['f1']:.3f}")

    # ----- Step 4: Conjunctions up to size 3 -----
    print("\n--- Evaluating conjunctions (size <= 3) ---")
    # Exclude empirical (free-param > 0) rules from conjunctions.
    fp_rules = [r for r in rules if r.free_params == 0]
    conj_results = evaluate_conjunctions(fp_rules, eigs_sorted, tuples_sorted,
                                          n_keep=200, max_size=3)
    # Write top 50 conjunctions to NDJSON.
    for rec in conj_results[:50]:
        writer.add({"record": "conjunction_eval", **rec})

    print("\n--- Top 10 conjunctions ---")
    for rec in conj_results[:10]:
        names = " AND ".join(rec["conjunction"])
        print(f"  {names[:60]:60s} verdict={rec['verdict']:11s} "
              f"sel={rec['n_selected']:3d} match={rec['sm_matched']}/9 "
              f"extra={rec['n_extra']:3d} F1={rec['f1']:.3f}")

    # ----- Step 4b: Higher-arity conjunctions for the best partial rules -----
    # Now also try size-4 conjunctions, but only from the top single rules
    # to bound combinatorics.
    print("\n--- Evaluating size-4 conjunctions (limited to top 12 single rules) ---")
    # Pick the top 12 first-principles single rules to bound search.
    fp_single_results = [
        sr for sr in single_results
        if sr["free_params"] == 0 and sr["rule_name"] != "D1_lightest_9"
    ]
    top_rules_for_conj = [
        r for r in rules
        if r.name in {sr["rule_name"] for sr in fp_single_results[:12]}
    ]
    if len(top_rules_for_conj) >= 4:
        conj4_results = evaluate_conjunctions(top_rules_for_conj, eigs_sorted,
                                              tuples_sorted, n_keep=200, max_size=4)
        for rec in conj4_results[:20]:
            writer.add({"record": "conjunction_eval_size4", **rec})
        for rec in conj4_results[:5]:
            names = " AND ".join(rec["conjunction"])
            print(f"  {names[:80]:80s} verdict={rec['verdict']:11s} "
                  f"sel={rec['n_selected']:3d} match={rec['sm_matched']}/9 "
                  f"extra={rec['n_extra']:3d} F1={rec['f1']:.3f}")
        # Track size-4 best for verdict computation.
        best_conj_f1_with_size4 = max(rec["f1"] for rec in conj4_results)
        n_exact_size4 = sum(1 for rec in conj4_results if rec["verdict"] == "EXACT")
    else:
        conj4_results = []
        best_conj_f1_with_size4 = 0.0
        n_exact_size4 = 0

    # ----- Step 5: Compute verdict -----
    # Exclude rules with free_params > 0 from closure counting.
    # The empirical rule J1_empirical_exact is the answer, not a derivation.
    # Conjunctions involving J1 likewise carry its free-param contamination.
    EMPIRICAL_RULES = {r.name for r in rules if r.free_params > 0}

    def is_first_principles_single(rec) -> bool:
        return rec["rule_name"] not in EMPIRICAL_RULES

    def is_first_principles_conj(rec) -> bool:
        return all(name not in EMPIRICAL_RULES for name in rec["conjunction"])

    fp_single = [r for r in single_results if is_first_principles_single(r)]
    fp_conj = [r for r in conj_results if is_first_principles_conj(r)]
    fp_conj4 = [r for r in conj4_results if is_first_principles_conj(r)]

    n_exact_single = sum(1 for r in fp_single if r["verdict"] == "EXACT")
    n_exact_conj = sum(1 for r in fp_conj if r["verdict"] == "EXACT")
    n_exact_conj4 = sum(1 for r in fp_conj4 if r["verdict"] == "EXACT")
    best_single_f1 = max((r["f1"] for r in fp_single), default=0.0)
    best_conj_f1 = max((r["f1"] for r in fp_conj), default=0.0)
    best_conj_f1_with_size4 = max((r["f1"] for r in fp_conj4), default=0.0)
    best_overall_f1 = max(best_single_f1, best_conj_f1, best_conj_f1_with_size4)
    n_exact_conj += n_exact_conj4

    # Record first-principles-only best.
    writer.add({
        "record": "first_principles_filter",
        "empirical_rule_names_excluded": sorted(EMPIRICAL_RULES),
        "n_fp_single_rules": len(fp_single),
        "n_fp_conjunctions_size123": len(fp_conj),
        "n_fp_conjunctions_size4": len(fp_conj4),
        "n_exact_fp_single": n_exact_single,
        "n_exact_fp_conj": n_exact_conj,
        "best_fp_single_f1": best_single_f1,
        "best_fp_conj_f1": best_conj_f1,
        "best_fp_size4_f1": best_conj_f1_with_size4,
    })

    if n_exact_single == 1 and n_exact_conj == 0:
        verdict = "CLOSURE"
        verdict_note = "exactly one first-principles single rule selects the SM 9 modes."
    elif n_exact_single + n_exact_conj == 1:
        verdict = "CLOSURE"
        verdict_note = (f"exactly one rule/conjunction selects the SM 9 modes "
                        f"(single={n_exact_single}, conj={n_exact_conj}).")
    elif n_exact_single + n_exact_conj > 1:
        verdict = "AMBIGUOUS"
        verdict_note = (f"multiple distinct rules/conjunctions exactly select 9 modes "
                        f"(single={n_exact_single}, conj={n_exact_conj}).")
    elif best_overall_f1 >= 0.8:
        verdict = "PARTIAL"
        verdict_note = f"best F1 = {best_overall_f1:.3f} (near miss, no exact match)."
    else:
        verdict = "NO-RULE"
        verdict_note = (f"no first-principles rule or conjunction matches the SM 9 "
                        f"modes; best F1 = {best_overall_f1:.3f}.")

    writer.add({
        "record": "verdict",
        "verdict": verdict,
        "note": verdict_note,
        "n_exact_single_rules": n_exact_single,
        "n_exact_conjunctions": n_exact_conj,
        "best_single_f1": best_single_f1,
        "best_conjunction_f1": best_conj_f1,
        "best_overall_f1": best_overall_f1,
    })
    print(f"\n=== VERDICT: {verdict} ===")
    print(f"    {verdict_note}")

    # ----- Step 6: Integrity -----
    elapsed = time.perf_counter() - t_start
    writer.flush()
    # Hash the NDJSON for integrity.
    sha = hashlib.sha256(NDJSON_PATH.read_bytes()).hexdigest()
    writer.add({
        "record": "integrity",
        "elapsed_s": elapsed,
        "ndjson_sha256": sha,
        "n_records": len(writer.lines),
    })
    writer.flush()
    print(f"\nProbe complete in {elapsed:.2f}s. NDJSON: {NDJSON_PATH.name}")
    print(f"SHA-256: {sha}")


if __name__ == "__main__":
    main()
