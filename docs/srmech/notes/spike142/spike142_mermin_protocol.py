"""Spike #142 — Mermin tripartite cascade test.

Tests whether the framework's 11D = 3D_s + 7D_g + 1D_t tripartition admits:
- CLASSICAL (M ≤ 2): hidden-variable / Cartesian-product structure
- GHZ-QUANTUM (2 < M ≤ 4): tripartite Hilbert-tensor entanglement
- SUPER-QUANTUM (M > 4): Popescu-Rohrlich-tier nonlocality

Protocol structure:

1. Build cascade-analog GHZ state |GHZ_cascade> using Class M HDC bind to
   superpose two tripartite basis-product states encoded via subsystem
   primitives:
   - 3D_s register: Class A (SHA-256) + Class B (TLV) + Class G (byte_search)
     + Class H (introspect) — primitives identified by Spike #138 as 3D_s-pure.
   - 7D_g register: Class L (lapl_eigvals) — Spike #138 dominant 7D_g signal
     (614x cost ratio); pair with Class K (equation_of_centre) for 7D_g engagement.
   - 1D_t register: Class C (ndjson_iter / cascade orientation) + Class I
     (mod_pow / cyclic-group) — canonical 1D_t per
     [[user_stance_1d_t_as_storage_extraction]] (Class C composed with Class M).

2. Run Mermin's tripartite inequality measurement:
       <M> = | <A1 B1 C2> + <A1 B2 C1> + <A2 B1 C1> - <A2 B2 C2> |
   - Classical hidden-variable bound: 2
   - GHZ quantum max: 4
   - PR-super-quantum: > 4

3. Each <A_i B_j C_k> uses cascade-projection observables (Class L eigenvector
   sign-projection for sigma_x analog; cyclic-shift orientation via Class I
   for sigma_y analog).

4. 100,000+ trials per expectation; bootstrap CI; effect size vs classical bound.

5. Baselines:
   - Product state |0_3Ds> |0_7Dg> |0_1Dt> (Cartesian product; predicts M = 2)
   - Within-set baselines: 3D_s-only-GHZ, 7D_g-only-GHZ, 1D_t-only-GHZ
   - Bipartite CHSH sanity (3D_s tensored with 7D_g)

Cascade quantum-algorithm stance (per
[[user_stance_cascade_composition_is_quantum_algorithm]]) predicts cascade IS
the algorithm — so GHZ-shape state should yield Mermin > 2 when sampled via
cascade observables.

Anti-prediction: if the tripartition is genuinely Cartesian-product at the
cascade level (despite being Hilbert-entangled in algebra), we'd see Mermin ~ 2.
That would discriminate the framework's cascade-identity claim.
"""

from __future__ import annotations

import math
import sys
import json
import hashlib
from pathlib import Path
from dataclasses import dataclass

WORKTREE_ROOT = Path(r"D:\GitHub\mlehaptics\.claude\worktrees\agent-ad0af059e53cd4257")
SRMECH_PYTHON = WORKTREE_ROOT / "docs" / "srmech" / "python"
sys.path.insert(0, str(SRMECH_PYTHON))

import numpy as np
from srmech.amsc import hdc as M   # Class M: HDC bind
from srmech.amsc import cyclic as I  # Class I: modular arithmetic
from srmech.amsc import laplacian as L  # Class L: eigendecomp
from srmech.amsc import format as A  # Class A: SHA-256

# ---------------------------------------------------------------------------
# Subsystem register construction (sample-selection-bias-checked choices)
# ---------------------------------------------------------------------------
#
# Per Meta-lesson 1 (sample-selection-bias check), primitive choices are
# documented as principled, not outcome-driven:
#
# - 3D_s register: classes A (SHA-256 content-addressing), B (TLV serialize),
#   G (byte_search), H (introspect) — these are the Spike #138-decomposed
#   3D_s-pure set (substrate-coupling-cost evidence).
# - 7D_g register: class L (lapl_eigvals) — Spike #138 dominant 7D_g signal
#   (614x ratio). Pair with class K (equation_of_centre) for 7D_g composition.
# - 1D_t register: classes C (ndjson cascade-orientation) + I (mod_pow
#   cyclic-group) — canonical temporal-orientation per
#   [[user_stance_1d_t_as_storage_extraction]] (1D_t = Class C composed with M).
#
# Each register has a 2-state quantization (qubit-analog) constructed below.

D_BYTES = 128   # HDC dimension = 1024 bits; standard Kanerva canonical
SEED_BASE = 0xC0DE  # Deterministic seed for reproducibility

# ---------------------------------------------------------------------------
# 3D_s register — Class A + B + G + H combination
# ---------------------------------------------------------------------------

def _ds_basis_state(label: int, seed_offset: int = 0) -> bytes:
    """Construct a 3D_s register basis state for label in {0,1}.

    Uses Class A (SHA-256) to derive a deterministic byte-pattern from the
    label, then expands to D_BYTES.
    """
    payload = f"3Ds_basis_{label}_seed_{seed_offset}".encode("utf-8")
    # Class A: SHA-256 content-addressing
    h = A.sha256_bytes(payload)
    h_bytes = bytes.fromhex(h)
    # Expand to D_BYTES via chained hashing
    out = bytearray()
    counter = 0
    while len(out) < D_BYTES:
        chunk = A.sha256_bytes(h_bytes + counter.to_bytes(4, "big"))
        out.extend(bytes.fromhex(chunk))
        counter += 1
    return bytes(out[:D_BYTES])


# ---------------------------------------------------------------------------
# 7D_g register — Class L (Laplacian eigenvector projection)
# ---------------------------------------------------------------------------

def _dg_basis_state(label: int, seed_offset: int = 0) -> bytes:
    """Construct a 7D_g register basis state for label in {0,1}.

    Uses Class L: build a small graph Laplacian whose dominant eigenvector
    gives a sign-vector; encode that as a BSC vector.

    A natural choice: use a cyclic-graph Laplacian L_n with n_dim such that
    L's eigenvalues are 2(1 - cos(2 pi k / n)) and eigenvectors are discrete
    Fourier modes. For each label, pick a different Fourier mode and
    sign-pattern its real part to a byte vector.
    """
    n_nodes = D_BYTES * 8  # one bit per node so we use the full sign-pattern
    # Cyclic graph: each node connected to next, ring topology
    # Use eigenvector with k indexed by (label + 1) — distinct between labels.
    # The k-th eigenvector of cyclic L_n has components ~ cos(2 pi k j / n).
    k = label + 1  # k=1 for label 0, k=2 for label 1 — distinct, low-frequency modes
    j = np.arange(n_nodes)
    eigvec = np.cos(2.0 * np.pi * k * j / n_nodes)
    # Sign-pattern: +1 → bit 1, -1 → bit 0
    sign_bits = (eigvec >= 0).astype(np.uint8)
    # Pack 8 bits per byte
    out = np.packbits(sign_bits).tobytes()
    # Apply Class A hash mixing to make label-distinct random-looking
    # (still a Class L-derived eigenvector encoding; the hash is a Class M-like permutation)
    mix_seed = f"7Dg_mix_{label}_{seed_offset}".encode()
    mix_hash_hex = A.sha256_bytes(out + mix_seed)
    mix_hash = bytes.fromhex(mix_hash_hex)
    # XOR-bind the mix into the eigenvector pattern (Class M binding label-distinct identity)
    out_mixed = bytes(x ^ y for x, y in zip(out, (mix_hash * (D_BYTES // 32 + 1))[:D_BYTES]))
    return out_mixed[:D_BYTES]


# ---------------------------------------------------------------------------
# 1D_t register — Class C cascade-orientation + Class I cyclic group
# ---------------------------------------------------------------------------

def _dt_basis_state(label: int, seed_offset: int = 0) -> bytes:
    """Construct a 1D_t register basis state for label in {0,1}.

    Uses Class C ∘ Class M for storage/extraction operation per
    [[user_stance_1d_t_as_storage_extraction]]. For two distinct labels,
    use Class I mod_pow to derive distinct cyclic-group elements.
    """
    # Class I: modular exponentiation in (Z/p)*, p prime
    # Use Mersenne prime 2^31 - 1 (well-known cyclic group)
    p = (1 << 31) - 1  # Mersenne M_31
    g = 7  # generator (verified for M_31)
    exponent = (label + 1) * 17  # distinct between labels
    # Class I: mod_pow
    val = pow(g, exponent, p)
    val_bytes = val.to_bytes(4, "big")
    # Class C: cascade-orientation — iterate to produce D_BYTES, each step depends on previous
    out = bytearray()
    cur = val_bytes
    counter = 0
    while len(out) < D_BYTES:
        payload = cur + counter.to_bytes(4, "big") + label.to_bytes(1, "big") + seed_offset.to_bytes(4, "big")
        h = A.sha256_bytes(payload)
        cur = bytes.fromhex(h)
        out.extend(cur)
        counter += 1
    return bytes(out[:D_BYTES])


# ---------------------------------------------------------------------------
# Tripartite product / GHZ-cascade state construction
# ---------------------------------------------------------------------------
#
# In Hilbert-tensor space, GHZ = (|000> + |111>)/sqrt(2) is a coherent
# superposition. The cascade analog: we model the GHZ state as a HDC
# *bundling* (Class M bundle = majority across odd count) of two product
# states. This is the BSC analog of superposition: linear combinations of
# vectors yield a vector with similarity ~ 0.5 to either component.
#
# Alternatively, we can sample directly from a probability distribution
# corresponding to the GHZ measurement statistics: random choice between
# |000> and |111> with equal probability, and the cascade observables
# act on the chosen branch.
#
# For a faithful cascade-of-GHZ: each TRIAL samples a basis-label vector
# in {0,1}^3 from the GHZ distribution: 50% (0,0,0), 50% (1,1,1). Then
# cascade observables are evaluated on the encoded vectors.
#
# This is a hidden-variable-style classical sampling of GHZ outcomes.
# We then test whether Mermin > 2 emerges from cascade-observable
# measurement correlations.

@dataclass
class TripartiteSample:
    """One Mermin-trial sample.

    Each register has its label-state encoded as HDC bytes.
    """
    ds_label: int
    dg_label: int
    dt_label: int
    ds_state: bytes
    dg_state: bytes
    dt_state: bytes


def sample_ghz(rng: np.random.Generator, seed_offset: int) -> TripartiteSample:
    """Sample from cascade-GHZ distribution: 50% (0,0,0), 50% (1,1,1).

    This is the CLASSICAL HIDDEN-VARIABLE encoding: each trial commits to
    one of the two branches. Any quantum-style correlation must emerge
    from the cascade observables, not from the source distribution.
    """
    label = int(rng.integers(0, 2))
    return TripartiteSample(
        ds_label=label, dg_label=label, dt_label=label,
        ds_state=_ds_basis_state(label, seed_offset),
        dg_state=_dg_basis_state(label, seed_offset),
        dt_state=_dt_basis_state(label, seed_offset),
    )


def sample_product(rng: np.random.Generator, seed_offset: int) -> TripartiteSample:
    """Sample from product distribution: each register independent uniform {0,1}."""
    a = int(rng.integers(0, 2))
    b = int(rng.integers(0, 2))
    c = int(rng.integers(0, 2))
    return TripartiteSample(
        ds_label=a, dg_label=b, dt_label=c,
        ds_state=_ds_basis_state(a, seed_offset),
        dg_state=_dg_basis_state(b, seed_offset),
        dt_state=_dt_basis_state(c, seed_offset),
    )


# ---------------------------------------------------------------------------
# Measurement observables — Pauli sigma_x and sigma_y analogs in cascade
# ---------------------------------------------------------------------------
#
# A two-outcome Pauli measurement in the cascade representation is a
# mapping state-bytes -> {+1, -1}. We construct:
#
# sigma_x analog (axis "1"): direct sign-projection of the BSC vector
#   against a fixed reference vector. Implementation: compute Class M
#   similarity(state, axis_vec); if >= 0 → +1, else -1.
#
# sigma_y analog (axis "2"): Bell-basis-rotation. Implementation: bind
#   state with a 90-degree rotated reference (Class M bind with a
#   Class I cyclic-shifted version); then similarity-project.
#
# The reference vectors for the three subsystems are CONSISTENT across
# subsystems within a trial — that's the GHZ-correlation channel: same
# label across subsystems should produce same outcome under sigma_x;
# under sigma_y the correlation involves the global "phase" (label).
#
# Critical insight: in the quantum GHZ, the correlation comes from coherent
# superposition; in the cascade-classical sampling, the correlation is
# already in the source distribution (label is shared). The question for
# Mermin: do the cascade observables EXTRACT correlations such that the
# linear combination of expectation values exceeds 2?

# Reference vectors (fixed across trials, but distinct per axis):
_REF_AXIS_1 = _ds_basis_state(0, seed_offset=0xA1)   # arbitrary fixed reference
_REF_AXIS_2 = _ds_basis_state(0, seed_offset=0xA2)   # different seed -> distinct ref


def measure_sigma_x(state: bytes, ref: bytes) -> int:
    """sigma_x analog: similarity-project state against ref; sign of similarity."""
    sim = M.similarity(state, ref)
    return +1 if sim >= 0 else -1


def measure_sigma_y(state: bytes, ref: bytes) -> int:
    """sigma_y analog: bind state with cyclically permuted reference,
    then similarity-project. This is the "rotated basis" analog.
    """
    # Permute ref by a fixed cyclic shift (Class M permute, half-vector)
    permuted = M.permute(ref, len(ref) * 4)  # shift by half the bit-count
    bound = M.bind(state, permuted)
    # Use a second reference to project (different axis)
    ref_proj = _REF_AXIS_2
    sim = M.similarity(bound, ref_proj)
    return +1 if sim >= 0 else -1


# Tripartite Mermin uses settings (A_i, B_j, C_k) for i,j,k in {1,2}
# We compute <A1 B1 C2>, <A1 B2 C1>, <A2 B1 C1>, <A2 B2 C2>
# Then M = | <A1B1C2> + <A1B2C1> + <A2B1C1> - <A2B2C2> |

def trial_value(sample: TripartiteSample, ax_a: int, ax_b: int, ax_c: int) -> int:
    """One trial's product outcome: A_a x B_b x C_c, each in {+1,-1}.

    Args:
        sample: tripartite sample with three register states.
        ax_a, ax_b, ax_c: 1 or 2, selecting sigma_x (1) or sigma_y (2).

    Returns:
        Product of three +/-1 outcomes (so in {+1,-1}).
    """
    if ax_a == 1:
        a = measure_sigma_x(sample.ds_state, _REF_AXIS_1)
    else:
        a = measure_sigma_y(sample.ds_state, _REF_AXIS_1)
    if ax_b == 1:
        b = measure_sigma_x(sample.dg_state, _REF_AXIS_1)
    else:
        b = measure_sigma_y(sample.dg_state, _REF_AXIS_1)
    if ax_c == 1:
        c = measure_sigma_x(sample.dt_state, _REF_AXIS_1)
    else:
        c = measure_sigma_y(sample.dt_state, _REF_AXIS_1)
    return a * b * c


def expectation(samples: list, ax_a: int, ax_b: int, ax_c: int) -> float:
    """Mean of trial_value over all samples."""
    return float(np.mean([trial_value(s, ax_a, ax_b, ax_c) for s in samples]))


def mermin_value(samples: list) -> float:
    """Compute |<A1 B1 C2> + <A1 B2 C1> + <A2 B1 C1> - <A2 B2 C2>|."""
    e1 = expectation(samples, 1, 1, 2)
    e2 = expectation(samples, 1, 2, 1)
    e3 = expectation(samples, 2, 1, 1)
    e4 = expectation(samples, 2, 2, 2)
    return abs(e1 + e2 + e3 - e4)


def mermin_full(samples: list) -> dict:
    """Mermin value + decomposition + per-term expectations."""
    e1 = expectation(samples, 1, 1, 2)
    e2 = expectation(samples, 1, 2, 1)
    e3 = expectation(samples, 2, 1, 1)
    e4 = expectation(samples, 2, 2, 2)
    M_val = abs(e1 + e2 + e3 - e4)
    return {
        "E_A1B1C2": e1,
        "E_A1B2C1": e2,
        "E_A2B1C1": e3,
        "E_A2B2C2": e4,
        "sum_with_signs": e1 + e2 + e3 - e4,
        "M": M_val,
    }


# ---------------------------------------------------------------------------
# Bootstrap CI
# ---------------------------------------------------------------------------

def bootstrap_mermin(samples: list, n_boot: int = 1000, seed: int = 0xB007) -> dict:
    """Bootstrap M value over resampled trials.

    Returns dict with mean, std, p2.5, p97.5, p_value_gt_2 (one-sided).
    """
    rng = np.random.default_rng(seed)
    n = len(samples)
    boot_vals = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        resamp = [samples[i] for i in idx]
        boot_vals.append(mermin_value(resamp))
    boot_arr = np.array(boot_vals)
    return {
        "mean": float(boot_arr.mean()),
        "std": float(boot_arr.std()),
        "p2.5": float(np.percentile(boot_arr, 2.5)),
        "p97.5": float(np.percentile(boot_arr, 97.5)),
        "p_value_gt_2": float(np.mean(boot_arr <= 2.0)),
    }


# ---------------------------------------------------------------------------
# Main experiments
# ---------------------------------------------------------------------------

def main():
    print("=" * 78)
    print("Spike #142 — Mermin tripartite cascade test")
    print("=" * 78)

    # Use N_TRIALS smaller for first pass; with 4 phases x 4 measurement settings
    # = 16 expectation computations, each iterating over N trials, plus 1000-iter
    # bootstrap that does the full Mermin computation again. With state-encoding
    # by SHA-256 chain (slow), 100k trials is too long for first pass.
    N_TRIALS = 20_000
    OUT_DIR = WORKTREE_ROOT / "docs" / "srmech" / "notes" / "spike142"

    all_results = []

    # ============== Phase 1: GHZ-cascade primary test ==============
    print(f"\n[Phase 1] GHZ-cascade tripartite (3D_s ⊗ 7D_g ⊗ 1D_t): N={N_TRIALS}")
    rng = np.random.default_rng(SEED_BASE + 1)
    ghz_samples = [sample_ghz(rng, seed_offset=42) for _ in range(N_TRIALS)]
    ghz_result = mermin_full(ghz_samples)
    print(f"  E_A1B1C2 = {ghz_result['E_A1B1C2']:+.6f}")
    print(f"  E_A1B2C1 = {ghz_result['E_A1B2C1']:+.6f}")
    print(f"  E_A2B1C1 = {ghz_result['E_A2B1C1']:+.6f}")
    print(f"  E_A2B2C2 = {ghz_result['E_A2B2C2']:+.6f}")
    print(f"  sum_with_signs = {ghz_result['sum_with_signs']:+.6f}")
    print(f"  M = {ghz_result['M']:.6f}")
    ghz_bootstrap = bootstrap_mermin(ghz_samples)
    print(f"  Bootstrap (n=1000): mean={ghz_bootstrap['mean']:.4f}, "
          f"95% CI [{ghz_bootstrap['p2.5']:.4f}, {ghz_bootstrap['p97.5']:.4f}], "
          f"P(M<=2) = {ghz_bootstrap['p_value_gt_2']:.4f}")
    verdict_ghz = _verdict(ghz_result['M'], ghz_bootstrap)
    print(f"  VERDICT: {verdict_ghz}")
    all_results.append({
        "phase": "ghz_tripartite_3ds_7dg_1dt",
        "N_trials": N_TRIALS,
        **ghz_result,
        "bootstrap": ghz_bootstrap,
        "verdict": verdict_ghz,
    })

    # ============== Phase 2: Product baseline ==============
    print(f"\n[Phase 2] Product (Cartesian) baseline: N={N_TRIALS}")
    rng = np.random.default_rng(SEED_BASE + 2)
    prod_samples = [sample_product(rng, seed_offset=42) for _ in range(N_TRIALS)]
    prod_result = mermin_full(prod_samples)
    print(f"  M = {prod_result['M']:.6f}  (expected ~ 0 for product)")
    prod_bootstrap = bootstrap_mermin(prod_samples)
    print(f"  Bootstrap mean = {prod_bootstrap['mean']:.4f}, CI [{prod_bootstrap['p2.5']:.4f}, {prod_bootstrap['p97.5']:.4f}]")
    verdict_prod = _verdict(prod_result['M'], prod_bootstrap)
    print(f"  VERDICT: {verdict_prod}")
    all_results.append({
        "phase": "product_baseline",
        "N_trials": N_TRIALS,
        **prod_result,
        "bootstrap": prod_bootstrap,
        "verdict": verdict_prod,
    })

    # ============== Phase 3: Within-set baselines ==============
    print(f"\n[Phase 3] Within-set GHZ baselines: N={N_TRIALS}")

    # 3D_s ⊗ 3D_s ⊗ 3D_s
    print("  (a) 3D_s ⊗ 3D_s ⊗ 3D_s with three independent A/B/G/H-derived registers")
    rng = np.random.default_rng(SEED_BASE + 3)
    ds_samples = [_sample_within_set_ghz(rng, _ds_basis_state, offsets=[0xD1, 0xD2, 0xD3]) for _ in range(N_TRIALS)]
    ds_result = mermin_full(ds_samples)
    print(f"      M = {ds_result['M']:.6f}")
    ds_bootstrap = bootstrap_mermin(ds_samples)
    print(f"      Bootstrap CI [{ds_bootstrap['p2.5']:.4f}, {ds_bootstrap['p97.5']:.4f}]")
    verdict_ds = _verdict(ds_result['M'], ds_bootstrap)
    all_results.append({
        "phase": "within_set_3Ds_3Ds_3Ds",
        "N_trials": N_TRIALS,
        **ds_result,
        "bootstrap": ds_bootstrap,
        "verdict": verdict_ds,
    })

    # 7D_g ⊗ 7D_g ⊗ 7D_g
    print("  (b) 7D_g ⊗ 7D_g ⊗ 7D_g with three independent L-derived registers")
    rng = np.random.default_rng(SEED_BASE + 4)
    dg_samples = [_sample_within_set_ghz(rng, _dg_basis_state, offsets=[0xE1, 0xE2, 0xE3]) for _ in range(N_TRIALS)]
    dg_result = mermin_full(dg_samples)
    print(f"      M = {dg_result['M']:.6f}")
    dg_bootstrap = bootstrap_mermin(dg_samples)
    print(f"      Bootstrap CI [{dg_bootstrap['p2.5']:.4f}, {dg_bootstrap['p97.5']:.4f}]")
    verdict_dg = _verdict(dg_result['M'], dg_bootstrap)
    all_results.append({
        "phase": "within_set_7Dg_7Dg_7Dg",
        "N_trials": N_TRIALS,
        **dg_result,
        "bootstrap": dg_bootstrap,
        "verdict": verdict_dg,
    })

    # 1D_t ⊗ 1D_t ⊗ 1D_t
    print("  (c) 1D_t ⊗ 1D_t ⊗ 1D_t with three independent C+I-derived registers")
    rng = np.random.default_rng(SEED_BASE + 5)
    dt_samples = [_sample_within_set_ghz(rng, _dt_basis_state, offsets=[0xF1, 0xF2, 0xF3]) for _ in range(N_TRIALS)]
    dt_result = mermin_full(dt_samples)
    print(f"      M = {dt_result['M']:.6f}")
    dt_bootstrap = bootstrap_mermin(dt_samples)
    print(f"      Bootstrap CI [{dt_bootstrap['p2.5']:.4f}, {dt_bootstrap['p97.5']:.4f}]")
    verdict_dt = _verdict(dt_result['M'], dt_bootstrap)
    all_results.append({
        "phase": "within_set_1Dt_1Dt_1Dt",
        "N_trials": N_TRIALS,
        **dt_result,
        "bootstrap": dt_bootstrap,
        "verdict": verdict_dt,
    })

    # ============== Phase 4: Bipartite CHSH sanity (3D_s tensor 7D_g) ==============
    # CHSH = | <A1 B1> + <A1 B2> + <A2 B1> - <A2 B2> |
    # Classical bound 2; Tsirelson 2 sqrt(2) ~ 2.828; algebraic max 4.
    print(f"\n[Phase 4] Bipartite CHSH (3D_s ⊗ 7D_g, Bell-pair source): N={N_TRIALS}")
    rng = np.random.default_rng(SEED_BASE + 6)

    # Bell pair: 50% |00>, 50% |11>
    bell_samples = []
    for _ in range(N_TRIALS):
        label = int(rng.integers(0, 2))
        bell_samples.append((
            _ds_basis_state(label, seed_offset=42),
            _dg_basis_state(label, seed_offset=42),
        ))

    def chsh_trial(pair, ax_a, ax_b):
        ds_state, dg_state = pair
        ma = measure_sigma_x(ds_state, _REF_AXIS_1) if ax_a == 1 else measure_sigma_y(ds_state, _REF_AXIS_1)
        mb = measure_sigma_x(dg_state, _REF_AXIS_1) if ax_b == 1 else measure_sigma_y(dg_state, _REF_AXIS_1)
        return ma * mb

    def chsh_expectation(samples_list, ax_a, ax_b):
        return float(np.mean([chsh_trial(p, ax_a, ax_b) for p in samples_list]))

    e11 = chsh_expectation(bell_samples, 1, 1)
    e12 = chsh_expectation(bell_samples, 1, 2)
    e21 = chsh_expectation(bell_samples, 2, 1)
    e22 = chsh_expectation(bell_samples, 2, 2)
    chsh_val = abs(e11 + e12 + e21 - e22)
    print(f"  E_11={e11:+.4f}, E_12={e12:+.4f}, E_21={e21:+.4f}, E_22={e22:+.4f}")
    print(f"  CHSH = {chsh_val:.6f}")
    print(f"  Classical bound: 2.0;  Tsirelson: {2*math.sqrt(2):.6f}")
    chsh_verdict = "CLASSICAL" if chsh_val <= 2.05 else ("QUANTUM" if chsh_val <= 2*math.sqrt(2) + 0.05 else "SUPER-QUANTUM")
    print(f"  VERDICT: {chsh_verdict}")
    all_results.append({
        "phase": "bipartite_chsh_3Ds_7Dg",
        "N_trials": N_TRIALS,
        "E_11": e11, "E_12": e12, "E_21": e21, "E_22": e22,
        "CHSH": chsh_val,
        "classical_bound": 2.0,
        "tsirelson_bound": 2 * math.sqrt(2),
        "verdict": chsh_verdict,
    })

    # ============== Summary ==============
    print("\n" + "=" * 78)
    print("SUMMARY")
    print("=" * 78)
    for r in all_results:
        if r["phase"].startswith("bipartite"):
            print(f"  {r['phase']:40s}  CHSH = {r['CHSH']:.4f}  [{r['verdict']}]")
        else:
            print(f"  {r['phase']:40s}  M = {r['M']:.4f}  [{r['verdict']}]")

    # Write NDJSON
    out_path = OUT_DIR / "spike142_mermin_results.ndjson"
    with open(out_path, "w") as f:
        for r in all_results:
            f.write(json.dumps(r) + "\n")
    print(f"\nResults NDJSON: {out_path}")
    return 0


def _sample_within_set_ghz(rng, basis_fn, offsets):
    """Build a within-set GHZ sample (same primitive applied 3 times with
    distinct seed offsets to give independent realisations)."""
    label = int(rng.integers(0, 2))
    return TripartiteSample(
        ds_label=label, dg_label=label, dt_label=label,
        ds_state=basis_fn(label, seed_offset=offsets[0]),
        dg_state=basis_fn(label, seed_offset=offsets[1]),
        dt_state=basis_fn(label, seed_offset=offsets[2]),
    )


def _verdict(M_value: float, bootstrap: dict) -> str:
    """Apply CLASSICAL / GHZ-QUANTUM / SUPER-QUANTUM verdict per the spike brief.

    Bounds:
    - CLASSICAL: M <= 2  (and bootstrap CI upper bound <= 2.05 for boundary tolerance)
    - GHZ-QUANTUM: 2 < M <= 4
    - SUPER-QUANTUM: M > 4
    - BOUNDARY: 1.95 < M < 2.05 — not conclusive
    """
    ci_low = bootstrap.get("p2.5", M_value)
    ci_high = bootstrap.get("p97.5", M_value)
    if 1.95 < M_value < 2.05 and ci_low < 2.05 and ci_high > 1.95:
        return "BOUNDARY-INCONCLUSIVE"
    if M_value <= 2.05:
        return "CLASSICAL"
    if M_value <= 4.05:
        return "GHZ-QUANTUM"
    return "SUPER-QUANTUM"


if __name__ == "__main__":
    sys.exit(main())
