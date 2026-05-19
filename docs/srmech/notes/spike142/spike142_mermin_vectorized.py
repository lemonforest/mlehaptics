"""Spike #142 — Mermin Monte Carlo (numpy-vectorized, FAST).

Since each cascade observable is a deterministic function of (subsystem,
label, axis) with only 2×2 = 4 inputs per subsystem, store the lookup as
a 2×2 numpy array and do vectorized arithmetic on label arrays.

This converts the expectation computation from O(N) dict lookups to a
single multiplication of three N-length vectors → fast enough to scale
to N = 1,000,000+.

Methodological discipline: even with this speedup, the prediction is M = 2
exactly (Bell's theorem / local-hidden-variable bound). The cascade-
observable encoding presented here is LHV-equivalent because each register's
outcome is a deterministic function of the shared label. So we expect:
- GHZ-cascade tripartite: M = 2 (CLASSICAL)
- Product baseline: M = 0 (independent factor terms cancel)
- Within-set baselines: variable, depending on how distinct seed instances
  encode different sign-tables. May be M < 2 or M = 2.
- Bipartite CHSH: <= 2 (also LHV)

The finding is a NEGATIVE finding in the canonical Mermin sense — at the
cascade-representation level, the tripartition stays CLASSICAL. This is a
discriminating answer to the spike's question.
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

D_BYTES = 128
SEED_BASE = 0xC0DE


def _ds_basis_state(label: int, seed_offset: int = 0) -> bytes:
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


_REF_AXIS_1 = _ds_basis_state(0, seed_offset=0xA1)
_REF_AXIS_2 = _ds_basis_state(0, seed_offset=0xA2)


def measure_sigma_x(state: bytes) -> int:
    return +1 if M.similarity(state, _REF_AXIS_1) >= 0 else -1


def measure_sigma_y(state: bytes) -> int:
    permuted = M.permute(_REF_AXIS_1, len(_REF_AXIS_1) * 4)
    bound = M.bind(state, permuted)
    return +1 if M.similarity(bound, _REF_AXIS_2) >= 0 else -1


def precompute_table(basis_fn, seed_offset: int) -> np.ndarray:
    """Return 2x2 numpy array: rows=label, cols=axis (0->sigma_x, 1->sigma_y).
    Values are +/-1.
    """
    arr = np.zeros((2, 2), dtype=np.int8)
    for lbl in (0, 1):
        s = basis_fn(lbl, seed_offset=seed_offset)
        arr[lbl, 0] = measure_sigma_x(s)
        arr[lbl, 1] = measure_sigma_y(s)
    return arr


def expectation(labels_array: np.ndarray, tables: list, axes: tuple) -> float:
    """labels_array: (N,3); tables: list of 3 (2,2) tables; axes: (i,j,k) in {0,1}."""
    vals_a = tables[0][labels_array[:, 0], axes[0]]
    vals_b = tables[1][labels_array[:, 1], axes[1]]
    vals_c = tables[2][labels_array[:, 2], axes[2]]
    return float(np.mean(vals_a * vals_b * vals_c))


def mermin_full(labels, tables):
    """Mermin tripartite. axes use 1-based naming; convert to 0-based for table index.
    A_1=sigma_x->axis index 0; A_2=sigma_y->axis index 1.
    """
    e1 = expectation(labels, tables, (0, 0, 1))  # A1 B1 C2
    e2 = expectation(labels, tables, (0, 1, 0))  # A1 B2 C1
    e3 = expectation(labels, tables, (1, 0, 0))  # A2 B1 C1
    e4 = expectation(labels, tables, (1, 1, 1))  # A2 B2 C2
    return {
        "E_A1B1C2": e1, "E_A1B2C1": e2, "E_A2B1C1": e3, "E_A2B2C2": e4,
        "sum_with_signs": e1 + e2 + e3 - e4,
        "M": abs(e1 + e2 + e3 - e4),
    }


def chsh_full(labels_bell: np.ndarray, table_a: np.ndarray, table_b: np.ndarray):
    """labels_bell: (N,2). CHSH = |E_11 + E_12 + E_21 - E_22|."""
    def chsh_exp(ax_a, ax_b):
        return float(np.mean(table_a[labels_bell[:, 0], ax_a] * table_b[labels_bell[:, 1], ax_b]))
    e11 = chsh_exp(0, 0); e12 = chsh_exp(0, 1)
    e21 = chsh_exp(1, 0); e22 = chsh_exp(1, 1)
    return {"E_11": e11, "E_12": e12, "E_21": e21, "E_22": e22, "CHSH": abs(e11 + e12 + e21 - e22)}


def bootstrap_mermin(labels, tables, n_boot=1000, seed=0xB007):
    rng = np.random.default_rng(seed)
    n = len(labels)
    boot_M = np.zeros(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        resampled = labels[idx]
        r = mermin_full(resampled, tables)
        boot_M[i] = r["M"]
    return {
        "mean": float(boot_M.mean()),
        "std": float(boot_M.std()),
        "p2.5": float(np.percentile(boot_M, 2.5)),
        "p97.5": float(np.percentile(boot_M, 97.5)),
        "p_value_M_le_2": float(np.mean(boot_M <= 2.0)),
    }


def verdict(M_val, ci_low=None, ci_high=None):
    if 1.95 < M_val < 2.05:
        return "BOUNDARY-INCONCLUSIVE"
    if M_val <= 2.05:
        return "CLASSICAL"
    if M_val <= 4.05:
        return "GHZ-QUANTUM"
    return "SUPER-QUANTUM"


def main():
    print("=" * 78, flush=True)
    print("Spike #142 — Mermin Monte Carlo (vectorized)", flush=True)
    print("=" * 78, flush=True)

    N_TRIALS = 1_000_000
    print(f"\nN_TRIALS = {N_TRIALS}", flush=True)
    print("Precomputing observable tables...", flush=True)

    t_ds = precompute_table(_ds_basis_state, 42)
    t_dg = precompute_table(_dg_basis_state, 42)
    t_dt = precompute_table(_dt_basis_state, 42)

    print(f"  3D_s table (rows=label, cols=axis):\n{t_ds}", flush=True)
    print(f"  7D_g table:\n{t_dg}", flush=True)
    print(f"  1D_t table:\n{t_dt}", flush=True)

    all_results = []
    rng = np.random.default_rng(SEED_BASE)

    # =========== Phase 1: GHZ-tripartite primary test ===========
    print(f"\n[Phase 1] GHZ-cascade tripartite (3D_s ⊗ 7D_g ⊗ 1D_t)", flush=True)
    labels_ghz = rng.integers(0, 2, size=N_TRIALS)
    labels_tri = np.stack([labels_ghz, labels_ghz, labels_ghz], axis=1)
    res = mermin_full(labels_tri, [t_ds, t_dg, t_dt])
    print(f"  E_A1B1C2 = {res['E_A1B1C2']:+.6f}", flush=True)
    print(f"  E_A1B2C1 = {res['E_A1B2C1']:+.6f}", flush=True)
    print(f"  E_A2B1C1 = {res['E_A2B1C1']:+.6f}", flush=True)
    print(f"  E_A2B2C2 = {res['E_A2B2C2']:+.6f}", flush=True)
    print(f"  sum_with_signs = {res['sum_with_signs']:+.6f}", flush=True)
    print(f"  M = {res['M']:.6f}", flush=True)
    boot = bootstrap_mermin(labels_tri, [t_ds, t_dg, t_dt], n_boot=200)
    print(f"  Bootstrap (200) mean={boot['mean']:.6f}, 95% CI [{boot['p2.5']:.6f}, {boot['p97.5']:.6f}]", flush=True)
    v = verdict(res['M'], boot['p2.5'], boot['p97.5'])
    print(f"  VERDICT: {v}", flush=True)
    all_results.append({"phase": "ghz_tripartite_3ds_7dg_1dt", "N": N_TRIALS, **res, "bootstrap": boot, "verdict": v})

    # =========== Phase 2: Product baseline ===========
    print(f"\n[Phase 2] Product (Cartesian) baseline", flush=True)
    labels_prod = rng.integers(0, 2, size=(N_TRIALS, 3))
    res_p = mermin_full(labels_prod, [t_ds, t_dg, t_dt])
    print(f"  M = {res_p['M']:.6f}  (expected ~ 0)", flush=True)
    boot_p = bootstrap_mermin(labels_prod, [t_ds, t_dg, t_dt], n_boot=200)
    vp = verdict(res_p['M'], boot_p['p2.5'], boot_p['p97.5'])
    print(f"  Bootstrap CI [{boot_p['p2.5']:.6f}, {boot_p['p97.5']:.6f}], VERDICT: {vp}", flush=True)
    all_results.append({"phase": "product_baseline", "N": N_TRIALS, **res_p, "bootstrap": boot_p, "verdict": vp})

    # =========== Phase 3: Within-set baselines ===========
    print(f"\n[Phase 3] Within-set GHZ baselines (3 independent seed-instances of same primitive)", flush=True)

    # 3D_s × 3D_s × 3D_s
    t_ds_1 = precompute_table(_ds_basis_state, 0xD1)
    t_ds_2 = precompute_table(_ds_basis_state, 0xD2)
    t_ds_3 = precompute_table(_ds_basis_state, 0xD3)
    res_ds = mermin_full(labels_tri, [t_ds_1, t_ds_2, t_ds_3])
    print(f"  (a) 3D_s ⊗ 3D_s ⊗ 3D_s:", flush=True)
    print(f"      Tables: 1={t_ds_1.tolist()}, 2={t_ds_2.tolist()}, 3={t_ds_3.tolist()}", flush=True)
    print(f"      M = {res_ds['M']:.6f}", flush=True)
    boot_ds = bootstrap_mermin(labels_tri, [t_ds_1, t_ds_2, t_ds_3], n_boot=200)
    v_ds = verdict(res_ds['M'], boot_ds['p2.5'], boot_ds['p97.5'])
    print(f"      Bootstrap CI [{boot_ds['p2.5']:.6f}, {boot_ds['p97.5']:.6f}], VERDICT: {v_ds}", flush=True)
    all_results.append({"phase": "within_set_3Ds_3Ds_3Ds", "N": N_TRIALS, **res_ds, "bootstrap": boot_ds, "verdict": v_ds})

    # 7D_g × 7D_g × 7D_g
    t_dg_1 = precompute_table(_dg_basis_state, 0xE1)
    t_dg_2 = precompute_table(_dg_basis_state, 0xE2)
    t_dg_3 = precompute_table(_dg_basis_state, 0xE3)
    res_dg = mermin_full(labels_tri, [t_dg_1, t_dg_2, t_dg_3])
    print(f"  (b) 7D_g ⊗ 7D_g ⊗ 7D_g:", flush=True)
    print(f"      Tables: 1={t_dg_1.tolist()}, 2={t_dg_2.tolist()}, 3={t_dg_3.tolist()}", flush=True)
    print(f"      M = {res_dg['M']:.6f}", flush=True)
    boot_dg = bootstrap_mermin(labels_tri, [t_dg_1, t_dg_2, t_dg_3], n_boot=200)
    v_dg = verdict(res_dg['M'], boot_dg['p2.5'], boot_dg['p97.5'])
    print(f"      Bootstrap CI [{boot_dg['p2.5']:.6f}, {boot_dg['p97.5']:.6f}], VERDICT: {v_dg}", flush=True)
    all_results.append({"phase": "within_set_7Dg_7Dg_7Dg", "N": N_TRIALS, **res_dg, "bootstrap": boot_dg, "verdict": v_dg})

    # 1D_t × 1D_t × 1D_t
    t_dt_1 = precompute_table(_dt_basis_state, 0xF1)
    t_dt_2 = precompute_table(_dt_basis_state, 0xF2)
    t_dt_3 = precompute_table(_dt_basis_state, 0xF3)
    res_dt = mermin_full(labels_tri, [t_dt_1, t_dt_2, t_dt_3])
    print(f"  (c) 1D_t ⊗ 1D_t ⊗ 1D_t:", flush=True)
    print(f"      Tables: 1={t_dt_1.tolist()}, 2={t_dt_2.tolist()}, 3={t_dt_3.tolist()}", flush=True)
    print(f"      M = {res_dt['M']:.6f}", flush=True)
    boot_dt = bootstrap_mermin(labels_tri, [t_dt_1, t_dt_2, t_dt_3], n_boot=200)
    v_dt = verdict(res_dt['M'], boot_dt['p2.5'], boot_dt['p97.5'])
    print(f"      Bootstrap CI [{boot_dt['p2.5']:.6f}, {boot_dt['p97.5']:.6f}], VERDICT: {v_dt}", flush=True)
    all_results.append({"phase": "within_set_1Dt_1Dt_1Dt", "N": N_TRIALS, **res_dt, "bootstrap": boot_dt, "verdict": v_dt})

    # =========== Phase 4: Bipartite CHSH ===========
    print(f"\n[Phase 4] Bipartite CHSH (3D_s ⊗ 7D_g, Bell-pair source)", flush=True)
    res_chsh = chsh_full(labels_tri[:, :2], t_ds, t_dg)
    print(f"  E_11={res_chsh['E_11']:+.4f}, E_12={res_chsh['E_12']:+.4f}, "
          f"E_21={res_chsh['E_21']:+.4f}, E_22={res_chsh['E_22']:+.4f}", flush=True)
    print(f"  CHSH = {res_chsh['CHSH']:.6f}", flush=True)
    print(f"  Classical bound: 2.0; Tsirelson: {2*math.sqrt(2):.6f}", flush=True)
    chsh_v = "CLASSICAL" if res_chsh["CHSH"] <= 2.05 else ("QUANTUM" if res_chsh["CHSH"] <= 2*math.sqrt(2)+0.05 else "SUPER-QUANTUM")
    print(f"  VERDICT: {chsh_v}", flush=True)
    all_results.append({"phase": "bipartite_chsh_3Ds_7Dg", "N": N_TRIALS, **res_chsh,
                        "classical_bound": 2.0, "tsirelson_bound": 2*math.sqrt(2), "verdict": chsh_v})

    # =========== Summary ===========
    print("\n" + "=" * 78, flush=True)
    print("SUMMARY", flush=True)
    print("=" * 78, flush=True)
    for r in all_results:
        if r["phase"].startswith("bipartite"):
            print(f"  {r['phase']:42s}  CHSH = {r['CHSH']:.4f}  [{r['verdict']}]", flush=True)
        else:
            print(f"  {r['phase']:42s}  M = {r['M']:.4f}  [{r['verdict']}]", flush=True)

    out_path = WORKTREE_ROOT / "docs" / "srmech" / "notes" / "spike142" / "spike142_mermin_results_vectorized.ndjson"
    with open(out_path, "w") as f:
        for r in all_results:
            f.write(json.dumps(r) + "\n")
    print(f"\nResults NDJSON: {out_path}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
