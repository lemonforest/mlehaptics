"""Spike #142 — Mermin tripartite Monte-Carlo with cascade observables.

EFFICIENT version: each register has only 2 basis states (labels {0,1}); we
precompute them once and reuse. Mermin observables are deterministic functions
of (label, axis); we precompute the 12-element lookup table:
  (subsystem in {ds, dg, dt}) x (label in {0,1}) x (axis in {1,2}) -> {-1,+1}
Then each trial is a label sample (or a triple-label for product baseline),
followed by 4 expectation computations as table lookups. Bootstrap is over
trial index arrays (fast).

Critical methodological note: since each register's observable is a
deterministic function of label, all expectations <A_i B_j C_k> for a
GHZ-style hidden-variable encoding are PRODUCTS of three deterministic
+/-1 values per shared label. This is the local-hidden-variable model
prediction; Mermin's theorem says |M| <= 2 strictly.

So we EXPECT M = 2 for this naive cascade encoding. That's the CLASSICAL
verdict. It's a meaningful finding because it discriminates the framework's
cascade-quantum-algorithm claim AT THE REPRESENTATION LEVEL — Hilbert-space
algebra gives M=4 (bit-exact, see spike142_mermin_hilbert.py), but cascade-
representation-as-encoded gives M=2.

If we want cascade-representation Mermin > 2, we'd need cascade observables
with non-commuting structure analogous to sigma_x vs sigma_y. The naive
similarity-projection observables COMMUTE trivially (they act on bytes
without algebraic interference). This itself is a research finding about
how the cascade-quantum-algorithm precedent generalizes.
"""

from __future__ import annotations

import math
import sys
import json
from pathlib import Path

WORKTREE_ROOT = Path(r"D:\GitHub\mlehaptics\.claude\worktrees\agent-ad0af059e53cd4257")
SRMECH_PYTHON = WORKTREE_ROOT / "docs" / "srmech" / "python"
sys.path.insert(0, str(SRMECH_PYTHON))

import numpy as np
from srmech.amsc import hdc as M
from srmech.amsc import format as A
from srmech.amsc import laplacian as L

D_BYTES = 128
SEED_BASE = 0xC0DE


def _ds_basis_state(label: int, seed_offset: int = 0) -> bytes:
    """3D_s state: Class A SHA-256-derived expansion (3D_s-pure)."""
    payload = f"3Ds_basis_{label}_seed_{seed_offset}".encode("utf-8")
    h = A.sha256_bytes(payload)
    h_bytes = bytes.fromhex(h)
    out = bytearray()
    counter = 0
    while len(out) < D_BYTES:
        chunk = A.sha256_bytes(h_bytes + counter.to_bytes(4, "big"))
        out.extend(bytes.fromhex(chunk))
        counter += 1
    return bytes(out[:D_BYTES])


def _dg_basis_state(label: int, seed_offset: int = 0) -> bytes:
    """7D_g state: Class L cyclic-graph eigenvector sign-pattern + Class A mix."""
    n_nodes = D_BYTES * 8
    k = label + 1
    j = np.arange(n_nodes)
    eigvec = np.cos(2.0 * np.pi * k * j / n_nodes)
    sign_bits = (eigvec >= 0).astype(np.uint8)
    out = np.packbits(sign_bits).tobytes()
    mix_seed = f"7Dg_mix_{label}_{seed_offset}".encode()
    mix_hash_hex = A.sha256_bytes(out + mix_seed)
    mix_hash = bytes.fromhex(mix_hash_hex)
    out_mixed = bytes(x ^ y for x, y in zip(out, (mix_hash * (D_BYTES // 32 + 1))[:D_BYTES]))
    return out_mixed[:D_BYTES]


def _dt_basis_state(label: int, seed_offset: int = 0) -> bytes:
    """1D_t state: Class I mod_pow + Class C cascade-orient (irreversible)."""
    p = (1 << 31) - 1
    g = 7
    exponent = (label + 1) * 17
    val = pow(g, exponent, p)
    val_bytes = val.to_bytes(4, "big")
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


# References for sigma_x and sigma_y axes — fixed across trials
_REF_AXIS_1 = _ds_basis_state(0, seed_offset=0xA1)
_REF_AXIS_2 = _ds_basis_state(0, seed_offset=0xA2)


def measure_sigma_x(state: bytes) -> int:
    return +1 if M.similarity(state, _REF_AXIS_1) >= 0 else -1


def measure_sigma_y(state: bytes) -> int:
    permuted = M.permute(_REF_AXIS_1, len(_REF_AXIS_1) * 4)
    bound = M.bind(state, permuted)
    return +1 if M.similarity(bound, _REF_AXIS_2) >= 0 else -1


def precompute_lookup(basis_fn, seed_offsets: list[int] = [42]) -> dict:
    """Precompute (label, axis) -> outcome for each register-encoding instance.

    Args:
        basis_fn: one of _ds_basis_state, _dg_basis_state, _dt_basis_state
        seed_offsets: list of seeds; each gives an independent register instance

    Returns:
        dict keyed by (seed_offset, label, axis) -> +/-1
    """
    table = {}
    for offset in seed_offsets:
        for label in (0, 1):
            state = basis_fn(label, seed_offset=offset)
            table[(offset, label, 1)] = measure_sigma_x(state)
            table[(offset, label, 2)] = measure_sigma_y(state)
    return table


def expectation_via_lookup(labels_array: np.ndarray,
                            table_a: dict, offset_a: int,
                            table_b: dict, offset_b: int,
                            table_c: dict, offset_c: int,
                            axes: tuple[int, int, int],
                            label_columns: tuple[int, int, int] = (0, 1, 2)) -> float:
    """Compute <A B C> using precomputed lookup.

    labels_array: shape (N, 3) with each row [label_a, label_b, label_c]
    """
    ax_a, ax_b, ax_c = axes
    col_a, col_b, col_c = label_columns

    vals_a = np.array([table_a[(offset_a, int(lbl), ax_a)] for lbl in labels_array[:, col_a]])
    vals_b = np.array([table_b[(offset_b, int(lbl), ax_b)] for lbl in labels_array[:, col_b]])
    vals_c = np.array([table_c[(offset_c, int(lbl), ax_c)] for lbl in labels_array[:, col_c]])

    return float(np.mean(vals_a * vals_b * vals_c))


def mermin_full(labels_array, table_a, offset_a, table_b, offset_b, table_c, offset_c,
                label_columns=(0, 1, 2)):
    """Full Mermin computation with decomposition."""
    e1 = expectation_via_lookup(labels_array, table_a, offset_a, table_b, offset_b, table_c, offset_c,
                                  (1, 1, 2), label_columns)
    e2 = expectation_via_lookup(labels_array, table_a, offset_a, table_b, offset_b, table_c, offset_c,
                                  (1, 2, 1), label_columns)
    e3 = expectation_via_lookup(labels_array, table_a, offset_a, table_b, offset_b, table_c, offset_c,
                                  (2, 1, 1), label_columns)
    e4 = expectation_via_lookup(labels_array, table_a, offset_a, table_b, offset_b, table_c, offset_c,
                                  (2, 2, 2), label_columns)
    M_val = abs(e1 + e2 + e3 - e4)
    return {"E_A1B1C2": e1, "E_A1B2C1": e2, "E_A2B1C1": e3, "E_A2B2C2": e4,
            "sum_with_signs": e1 + e2 + e3 - e4, "M": M_val}


def chsh_full(labels_array, table_a, offset_a, table_b, offset_b, label_columns=(0, 1)):
    """Bipartite CHSH computation."""
    col_a, col_b = label_columns

    def chsh_exp(ax_a, ax_b):
        vals_a = np.array([table_a[(offset_a, int(lbl), ax_a)] for lbl in labels_array[:, col_a]])
        vals_b = np.array([table_b[(offset_b, int(lbl), ax_b)] for lbl in labels_array[:, col_b]])
        return float(np.mean(vals_a * vals_b))

    e11 = chsh_exp(1, 1); e12 = chsh_exp(1, 2)
    e21 = chsh_exp(2, 1); e22 = chsh_exp(2, 2)
    chsh = abs(e11 + e12 + e21 - e22)
    return {"E_11": e11, "E_12": e12, "E_21": e21, "E_22": e22, "CHSH": chsh}


def bootstrap_mermin(labels_array, table_a, offset_a, table_b, offset_b, table_c, offset_c,
                      n_boot=1000, seed=0xB007, label_columns=(0, 1, 2)):
    rng = np.random.default_rng(seed)
    n = len(labels_array)
    boot_M = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        resampled = labels_array[idx]
        res = mermin_full(resampled, table_a, offset_a, table_b, offset_b, table_c, offset_c, label_columns)
        boot_M.append(res["M"])
    boot_arr = np.array(boot_M)
    return {
        "mean": float(boot_arr.mean()),
        "std": float(boot_arr.std()),
        "p2.5": float(np.percentile(boot_arr, 2.5)),
        "p97.5": float(np.percentile(boot_arr, 97.5)),
        "p_value_M_le_2": float(np.mean(boot_arr <= 2.0)),
    }


def verdict(M_val: float, ci_low: float = None, ci_high: float = None) -> str:
    if 1.95 < M_val < 2.05:
        if ci_low is not None and ci_high is not None:
            if ci_low > 2.05:
                return "GHZ-QUANTUM"
            if ci_high < 1.95:
                return "CLASSICAL"
            return "BOUNDARY-INCONCLUSIVE"
        return "BOUNDARY-INCONCLUSIVE"
    if M_val <= 2.05:
        return "CLASSICAL"
    if M_val <= 4.05:
        return "GHZ-QUANTUM"
    return "SUPER-QUANTUM"


def main():
    print("=" * 78, flush=True)
    print("Spike #142 — Mermin Monte Carlo (efficient lookup-table)", flush=True)
    print("=" * 78, flush=True)

    N_TRIALS = 100_000
    print(f"\nN_TRIALS = {N_TRIALS}", flush=True)
    print("Precomputing observables lookup tables...", flush=True)

    # Three subsystems with single seed each
    table_ds = precompute_lookup(_ds_basis_state, [42])
    table_dg = precompute_lookup(_dg_basis_state, [42])
    table_dt = precompute_lookup(_dt_basis_state, [42])

    print("Lookup tables ready:", flush=True)
    print(f"  3D_s (offset=42): {table_ds}", flush=True)
    print(f"  7D_g (offset=42): {table_dg}", flush=True)
    print(f"  1D_t (offset=42): {table_dt}", flush=True)

    all_results = []
    rng_master = np.random.default_rng(SEED_BASE)

    # ============== PHASE 1: GHZ-cascade primary test ==============
    print(f"\n[Phase 1] GHZ-cascade tripartite (3D_s ⊗ 7D_g ⊗ 1D_t)", flush=True)
    # GHZ encoding: 50% all-0, 50% all-1. So labels are (l,l,l)
    labels = rng_master.integers(0, 2, size=N_TRIALS)
    labels_ghz_tri = np.stack([labels, labels, labels], axis=1)
    res_ghz = mermin_full(labels_ghz_tri, table_ds, 42, table_dg, 42, table_dt, 42)
    print(f"  E_A1B1C2 = {res_ghz['E_A1B1C2']:+.6f}", flush=True)
    print(f"  E_A1B2C1 = {res_ghz['E_A1B2C1']:+.6f}", flush=True)
    print(f"  E_A2B1C1 = {res_ghz['E_A2B1C1']:+.6f}", flush=True)
    print(f"  E_A2B2C2 = {res_ghz['E_A2B2C2']:+.6f}", flush=True)
    print(f"  sum_with_signs = {res_ghz['sum_with_signs']:+.6f}", flush=True)
    print(f"  M = {res_ghz['M']:.6f}", flush=True)
    boot = bootstrap_mermin(labels_ghz_tri, table_ds, 42, table_dg, 42, table_dt, 42)
    print(f"  Bootstrap mean={boot['mean']:.4f}, 95% CI [{boot['p2.5']:.4f}, {boot['p97.5']:.4f}]", flush=True)
    v = verdict(res_ghz["M"], boot["p2.5"], boot["p97.5"])
    print(f"  VERDICT: {v}", flush=True)
    all_results.append({
        "phase": "ghz_tripartite_3ds_7dg_1dt",
        "N_trials": N_TRIALS,
        **res_ghz,
        "bootstrap": boot,
        "verdict": v,
    })

    # ============== PHASE 2: Product (Cartesian) baseline ==============
    print(f"\n[Phase 2] Product (Cartesian) baseline (independent labels)", flush=True)
    labels_prod = rng_master.integers(0, 2, size=(N_TRIALS, 3))
    res_prod = mermin_full(labels_prod, table_ds, 42, table_dg, 42, table_dt, 42)
    print(f"  M = {res_prod['M']:.6f}", flush=True)
    print(f"  Expected ~ 0 (independent factorising terms)", flush=True)
    boot = bootstrap_mermin(labels_prod, table_ds, 42, table_dg, 42, table_dt, 42)
    v = verdict(res_prod["M"], boot["p2.5"], boot["p97.5"])
    print(f"  Bootstrap CI [{boot['p2.5']:.4f}, {boot['p97.5']:.4f}]", flush=True)
    print(f"  VERDICT: {v}", flush=True)
    all_results.append({
        "phase": "product_baseline",
        "N_trials": N_TRIALS,
        **res_prod,
        "bootstrap": boot,
        "verdict": v,
    })

    # ============== PHASE 3: Within-set GHZ baselines ==============
    print(f"\n[Phase 3] Within-set GHZ baselines (each: 3 independent register-instances of same primitive)", flush=True)

    # 3D_s ⊗ 3D_s ⊗ 3D_s
    print("  (a) 3D_s ⊗ 3D_s ⊗ 3D_s (Class A primitive, 3 seed instances)", flush=True)
    table_ds_3 = precompute_lookup(_ds_basis_state, [0xD1, 0xD2, 0xD3])
    res = mermin_full(labels_ghz_tri, table_ds_3, 0xD1, table_ds_3, 0xD2, table_ds_3, 0xD3)
    boot = bootstrap_mermin(labels_ghz_tri, table_ds_3, 0xD1, table_ds_3, 0xD2, table_ds_3, 0xD3)
    v = verdict(res["M"], boot["p2.5"], boot["p97.5"])
    print(f"      E_A1B1C2 = {res['E_A1B1C2']:+.4f}, E_A1B2C1 = {res['E_A1B2C1']:+.4f}, "
          f"E_A2B1C1 = {res['E_A2B1C1']:+.4f}, E_A2B2C2 = {res['E_A2B2C2']:+.4f}", flush=True)
    print(f"      M = {res['M']:.6f}, Bootstrap CI [{boot['p2.5']:.4f}, {boot['p97.5']:.4f}], VERDICT: {v}", flush=True)
    all_results.append({"phase": "within_set_3Ds_3Ds_3Ds", "N_trials": N_TRIALS, **res, "bootstrap": boot, "verdict": v})

    # 7D_g ⊗ 7D_g ⊗ 7D_g
    print("  (b) 7D_g ⊗ 7D_g ⊗ 7D_g (Class L primitive, 3 seed instances)", flush=True)
    table_dg_3 = precompute_lookup(_dg_basis_state, [0xE1, 0xE2, 0xE3])
    res = mermin_full(labels_ghz_tri, table_dg_3, 0xE1, table_dg_3, 0xE2, table_dg_3, 0xE3)
    boot = bootstrap_mermin(labels_ghz_tri, table_dg_3, 0xE1, table_dg_3, 0xE2, table_dg_3, 0xE3)
    v = verdict(res["M"], boot["p2.5"], boot["p97.5"])
    print(f"      M = {res['M']:.6f}, Bootstrap CI [{boot['p2.5']:.4f}, {boot['p97.5']:.4f}], VERDICT: {v}", flush=True)
    all_results.append({"phase": "within_set_7Dg_7Dg_7Dg", "N_trials": N_TRIALS, **res, "bootstrap": boot, "verdict": v})

    # 1D_t ⊗ 1D_t ⊗ 1D_t
    print("  (c) 1D_t ⊗ 1D_t ⊗ 1D_t (Class C+I primitive, 3 seed instances)", flush=True)
    table_dt_3 = precompute_lookup(_dt_basis_state, [0xF1, 0xF2, 0xF3])
    res = mermin_full(labels_ghz_tri, table_dt_3, 0xF1, table_dt_3, 0xF2, table_dt_3, 0xF3)
    boot = bootstrap_mermin(labels_ghz_tri, table_dt_3, 0xF1, table_dt_3, 0xF2, table_dt_3, 0xF3)
    v = verdict(res["M"], boot["p2.5"], boot["p97.5"])
    print(f"      M = {res['M']:.6f}, Bootstrap CI [{boot['p2.5']:.4f}, {boot['p97.5']:.4f}], VERDICT: {v}", flush=True)
    all_results.append({"phase": "within_set_1Dt_1Dt_1Dt", "N_trials": N_TRIALS, **res, "bootstrap": boot, "verdict": v})

    # ============== PHASE 4: Bipartite CHSH sanity ==============
    print(f"\n[Phase 4] Bipartite CHSH (3D_s ⊗ 7D_g, Bell-pair source)", flush=True)
    # Bell pair: 50% |00>, 50% |11>
    labels_bell = labels_ghz_tri[:, :2]  # first two cols are matched
    res_chsh = chsh_full(labels_bell, table_ds, 42, table_dg, 42)
    print(f"  E_11 = {res_chsh['E_11']:+.4f}, E_12 = {res_chsh['E_12']:+.4f}, "
          f"E_21 = {res_chsh['E_21']:+.4f}, E_22 = {res_chsh['E_22']:+.4f}", flush=True)
    print(f"  CHSH = {res_chsh['CHSH']:.6f}", flush=True)
    print(f"  Classical bound: 2.0; Tsirelson: {2*math.sqrt(2):.6f}", flush=True)
    chsh_verdict = "CLASSICAL" if res_chsh["CHSH"] <= 2.05 else ("QUANTUM" if res_chsh["CHSH"] <= 2*math.sqrt(2) + 0.05 else "SUPER-QUANTUM")
    print(f"  VERDICT: {chsh_verdict}", flush=True)
    all_results.append({
        "phase": "bipartite_chsh_3Ds_7Dg",
        "N_trials": N_TRIALS,
        **res_chsh,
        "classical_bound": 2.0,
        "tsirelson_bound": 2 * math.sqrt(2),
        "verdict": chsh_verdict,
    })

    # ============== Summary ==============
    print("\n" + "=" * 78, flush=True)
    print("SUMMARY", flush=True)
    print("=" * 78, flush=True)
    for r in all_results:
        if r["phase"].startswith("bipartite"):
            print(f"  {r['phase']:42s}  CHSH = {r['CHSH']:.4f}  [{r['verdict']}]", flush=True)
        else:
            print(f"  {r['phase']:42s}  M = {r['M']:.4f}  [{r['verdict']}]", flush=True)

    out_path = WORKTREE_ROOT / "docs" / "srmech" / "notes" / "spike142" / "spike142_mermin_results.ndjson"
    with open(out_path, "w") as f:
        for r in all_results:
            f.write(json.dumps(r) + "\n")
    print(f"\nResults NDJSON: {out_path}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
