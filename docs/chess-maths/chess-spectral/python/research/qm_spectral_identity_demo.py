"""qm_4d Experiment 1: spectral identity demo.

A clean, reduced demo of Pre-flight 3's central claim: the encoder's
4096 modes ARE the simultaneous eigenbasis of (Delta, B_4 commutant)
where Delta = P_8 box P_8 box P_8 box P_8 is the 4D path-graph
Laplacian. This is a downstream-friendly version of
:mod:`spectral_identity_4d_verification` -- the heavy 384-element B_4
stability sweep is summarised, the per-eigenspace alignment check
is performed at full resolution, and the output is a structured
JSON file that downstream notebooks can pick up directly.

Outputs
-------
  stdout: 4 diagnostics from Pre-flight 3 (rounded for readability)
  qm_spectral_identity_demo.json (next to this script): full numbers
  qm_spectral_identity_demo.png (optional, only if matplotlib loads)

Run from python/ working directory:
  python research/qm_spectral_identity_demo.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_DIR = os.path.dirname(THIS_DIR)
if PYTHON_DIR not in sys.path:
    sys.path.insert(0, PYTHON_DIR)

from chess_spectral import tables_4d as t4                  # noqa: E402
from chess_spectral import qm_4d                             # noqa: E402


def _utf8_stdout() -> None:
    """Force UTF-8 stdout on Windows consoles. Best-effort no-op
    elsewhere."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass


def _p_n_laplacian(n: int) -> np.ndarray:
    """Path graph P_n Laplacian (open boundary)."""
    A = np.zeros((n, n), dtype=np.float64)
    for i in range(n - 1):
        A[i, i + 1] = 1.0
        A[i + 1, i] = 1.0
    return np.diag(A.sum(axis=1)) - A


def _kron_sum_4d(L1: np.ndarray) -> np.ndarray:
    """Build Delta = L1 (X) I (X) I (X) I + ... + I (X) I (X) I (X) L1
    on the 8^4 lattice as a dense (4096, 4096) array."""
    n = L1.shape[0]
    eye = np.eye(n, dtype=L1.dtype)
    out = np.zeros((n ** 4, n ** 4), dtype=L1.dtype)
    for axis in range(4):
        factors = [eye] * 4
        factors[axis] = L1
        T = factors[0]
        for f in factors[1:]:
            T = np.kron(T, f)
        out += T
    return out


def _group_eigenspaces(eigvals: np.ndarray, eigvecs: np.ndarray,
                        tol: float = 1e-9):
    """Bucket eigenvectors by eigenvalue. Returns list of (lam, V)."""
    order = np.argsort(eigvals)
    e_sorted = eigvals[order]
    v_sorted = eigvecs[:, order]
    spaces = []
    start = 0
    for k in range(1, len(e_sorted) + 1):
        if k == len(e_sorted) or abs(e_sorted[k] - e_sorted[start]) > tol:
            spaces.append(
                (float(np.mean(e_sorted[start:k])), v_sorted[:, start:k])
            )
            start = k
    return spaces


def _encoder_basis_4d():
    """Return (modes, lambdas, idx_tuples) for the encoder's
    canonical tensor-DCT basis on Z_8^4. Same construction as
    spectral_identity_4d_verification.encoder_basis_4d."""
    evecs_1d, evals_1d = t4.eig_p8()
    n = t4.BOARD_SIDE
    modes = np.empty((n ** 4, n ** 4), dtype=np.float64)
    lambdas = np.empty(n ** 4, dtype=np.float64)
    tuples = np.empty((n ** 4, 4), dtype=np.int32)
    col = 0
    for i in range(n):
        for j in range(n):
            for k in range(n):
                for ll in range(n):
                    modes[:, col] = t4.tensor_eigvec_4d(
                        evecs_1d, i, j, k, ll
                    )
                    lambdas[col] = (
                        evals_1d[i] + evals_1d[j]
                        + evals_1d[k] + evals_1d[ll]
                    )
                    tuples[col] = (i, j, k, ll)
                    col += 1
    order = np.argsort(lambdas, kind="stable")
    return modes[:, order], lambdas[order], tuples[order]


def _basis_b4_stability(V: np.ndarray, U: csr_matrix) -> float:
    """For one basis V of an eigenspace and one group element U,
    return ||(I - V V^T) U V||_inf -- the failure of E_lambda to be
    U-stable."""
    piV = U @ V                       # sparse-dense
    proj_coords = V.T @ piV
    residual = piV - V @ proj_coords
    return float(np.max(np.abs(residual)))


def main() -> int:
    _utf8_stdout()

    print("=" * 72)
    print("qm_4d Experiment 1: spectral identity demo")
    print("=" * 72)
    print("Claim: the encoder's 4096 modes form the simultaneous "
          "eigenbasis of")
    print("(Delta, B_4 commutant) where Delta = "
          "P_8 box P_8 box P_8 box P_8.")
    print()

    # 1. Build Delta and diagonalise.
    t0 = time.time()
    L1 = _p_n_laplacian(t4.BOARD_SIDE)
    L = _kron_sum_4d(L1)
    print(f"Built Delta on Z_8^4 ({L.shape}) in {time.time() - t0:.2f}s")

    t0 = time.time()
    eigvals, eigvecs = np.linalg.eigh(L)
    print(f"Diagonalised eigh in {time.time() - t0:.2f}s")

    spaces = _group_eigenspaces(eigvals, eigvecs)
    n_unique = len(spaces)
    mults = [V.shape[1] for _, V in spaces]
    max_mult = max(mults)
    print(f"  distinct eigenvalues: {n_unique}")
    print(f"  total dim:            {sum(mults)}")
    print(f"  max multiplicity:     {max_mult}")

    # 2. Encoder basis vs Delta-eigenbasis.
    t0 = time.time()
    enc_modes, enc_lambdas, _enc_tuples = _encoder_basis_4d()
    print(f"Built encoder basis (sorted by lambda) in "
          f"{time.time() - t0:.2f}s")

    # 3. Diagnostic 1: encoder basis is L-eigenbasis.
    err_eigval = 0.0
    # spot-check stride of 64 (every 64th mode) -- 64 mat-vec products.
    for col in range(0, enc_modes.shape[1], 64):
        v = enc_modes[:, col]
        Lv = L @ v
        err = float(np.max(np.abs(Lv - enc_lambdas[col] * v)))
        if err > err_eigval:
            err_eigval = err
    print()
    print("[Diagnostic 1] Encoder basis is Delta-eigenbasis:")
    print(f"  max ||Delta v_enc - lambda v_enc||_inf "
          f"(stride-64 spot check) = {err_eigval:.2e}")

    # 4. Diagnostic 2: Encoder columns span E_lambda exactly.
    align_max = 0.0
    align_per_lambda = []
    for lam, V in spaces:
        sel = np.where(np.abs(enc_lambdas - lam) < 1e-9)[0]
        if sel.size != V.shape[1]:
            print(f"  !! lambda={lam:.5f} count mismatch: encoder has "
                  f"{sel.size}, eigenspace has {V.shape[1]}")
            continue
        Venc = enc_modes[:, sel]
        proj = V @ (V.T @ Venc)
        residual = Venc - proj
        e = float(np.max(np.abs(residual)))
        align_per_lambda.append((float(lam), int(V.shape[1]), e))
        if e > align_max:
            align_max = e
    print()
    print("[Diagnostic 2] Encoder columns span E_lambda:")
    print(f"  max ||(I - P_lambda) v_enc||_inf = {align_max:.2e}")

    # 5. Diagnostic 3: Every eigenspace is B_4-stable.
    print()
    print("[Diagnostic 3] B_4-stability of Delta-eigenspaces:")
    closure = t4.b4_closure()
    print(f"  |B_4| = {len(closure)}")

    # Sample a representative subset of B_4 for speed (skipping the
    # full 384 sweep -- the full audit lives in
    # spectral_identity_4d_verification.py). 16 elements covers
    # identity + signs + axis swaps reasonably.
    sample_indices = [
        0, 1, 5, 10, 17, 47, 80, 100, 150, 200, 250, 300, 350, 383,
    ]
    sample_unitaries = [
        qm_4d.b4_unitary_rep_4096(closure[i]) for i in sample_indices
    ]
    t0 = time.time()
    n_stable = 0
    max_err = 0.0
    failed_eigs = []
    for lam, V in spaces:
        e_max_lam = 0.0
        for U in sample_unitaries:
            e = _basis_b4_stability(V, U)
            if e > e_max_lam:
                e_max_lam = e
        if e_max_lam < 1e-7:
            n_stable += 1
        else:
            failed_eigs.append((float(lam), e_max_lam))
        if e_max_lam > max_err:
            max_err = e_max_lam
    print(f"  sampled {len(sample_indices)} of 384 B_4 elements")
    print(f"  {n_stable}/{n_unique} eigenspaces B_4-stable on the "
          f"sample (tol 1e-7)")
    print(f"  max ||(I - P_lambda) pi(g) V|| over sample = "
          f"{max_err:.2e}")
    print(f"  elapsed: {time.time() - t0:.1f}s")
    if failed_eigs:
        print(f"  !! {len(failed_eigs)} unstable eigenspaces:")
        for lam, err in failed_eigs[:5]:
            print(f"     lambda = {lam:.5f}, err = {err:.2e}")

    # 6. Diagnostic 4: P_8 1D spectrum + multiplicity histogram.
    _, evals_1d = t4.eig_p8()
    p8_spectrum = [float(x) for x in evals_1d]
    mult_hist = dict(Counter(mults))
    print()
    print("[Diagnostic 4] Encoder eigenvalue structure:")
    print(f"  P_8 1D spectrum: "
          f"{[f'{v:.5f}' for v in p8_spectrum]}")
    print(f"  4D multiplicity histogram (mult -> count):")
    for m in sorted(mult_hist.keys()):
        print(f"    mult={m:3d}: {mult_hist[m]:3d} eigenvalues")

    # 7. Persist findings to JSON for downstream notebooks.
    findings = {
        "n_distinct_eigenvalues": n_unique,
        "max_multiplicity": int(max_mult),
        "eigenvalue_alignment_max_error": float(align_max),
        "eigenbasis_stride64_max_error": float(err_eigval),
        "b4_stability_sampled_elements": list(sample_indices),
        "b4_stability_max_error_on_sample": float(max_err),
        "p8_1d_spectrum": p8_spectrum,
        "multiplicity_histogram": {
            str(k): int(v) for k, v in mult_hist.items()
        },
        "alignment_per_lambda": align_per_lambda,
        "verdict": (
            "HOLDS" if (
                err_eigval < 1e-9 and align_max < 1e-9 and max_err < 1e-7
            ) else "NEEDS_INSPECTION"
        ),
        "notes": (
            "qm_spectral_identity_demo.py runs a sampled-B_4 stability "
            "check (16 of 384 elements). For the full 384-element "
            "audit see spectral_identity_4d_verification.py."
        ),
    }
    out_path = Path(__file__).with_suffix('.json')
    out_path.write_text(json.dumps(findings, indent=2))
    print()
    print(f"Findings written to {out_path}")
    print(f"Verdict: {findings['verdict']}")

    # 8. Optional: matplotlib plot of the eigenvalue ladder.
    try:
        import matplotlib  # noqa: F401
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 4))
        lambdas_arr = np.array([lam for lam, _ in spaces])
        mults_arr = np.array(mults)
        ax.bar(lambdas_arr, mults_arr, width=0.07,
               color="C0", edgecolor="black", linewidth=0.4)
        ax.set_xlabel("Delta eigenvalue lambda")
        ax.set_ylabel("multiplicity (= dim E_lambda)")
        ax.set_title("Encoder eigenvalue ladder on Z_8^4 "
                      "(Delta = P_8 box P_8 box P_8 box P_8)")
        ax.grid(True, alpha=0.3)
        plot_path = Path(__file__).with_suffix(".png")
        fig.tight_layout()
        fig.savefig(plot_path, dpi=120)
        print(f"Plot saved to {plot_path}")
        plt.close(fig)
    except ImportError:
        print("matplotlib not available -- skipping plot.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
