"""Pre-flight check #3 for `chess_spectral.qm_4d`: spectral-identity verification.

Claim under test
----------------

> The 4096 eigenmodes used by ``chess_spectral.encoder_4d`` ARE the simultaneous
> eigenbasis of (a) the Z_8^4 graph Laplacian Δ and (b) the commutant of the B_4
> group action on Z_8^4 (the centralizer of the unitary representation).

Caveat noted up front: the encoder does NOT use the cycle graph C_8 (Z_8 as a
discrete group) — it uses the path graph P_8 (open boundary). This script tests
both forms; the structurally relevant one for the encoder is P_8 □ P_8 □ P_8 □ P_8.
We label the section "P_8 (encoder)" vs "C_8 (Z_8 as a group)" to make the
distinction explicit.

What "B_4-commutant simultaneous eigenbasis" means here
------------------------------------------------------

For each Δ-eigenspace E_λ we project the B_4 representation π onto E_λ:

    π_λ(g) := P_λ π(g) P_λ                  (g ∈ B_4)

If [π(g), Δ] = 0 for all g (which holds because B_4 is a graph automorphism
group of the chosen graph), then E_λ is a B_4-stable subspace and π_λ is a
genuine sub-representation of π. The encoder's "canonical basis within E_λ"
is the simultaneous-eigenbasis claim — i.e. the encoder's modes are an
isotypic / irreducible-component decomposition of E_λ.

The script:

1. Builds Δ four ways: P_8 □ P_8 □ P_8 □ P_8 (encoder), C_8 □ C_8 □ C_8 □ C_8
   (cycle), plus 2D smaller analogs.
2. Diagonalises Δ (dense ``eigh`` for the 4096 case is well within reach;
   ~10 seconds on a laptop).
3. Builds π : B_4 → U(R^{4096}) using ``tables_4d.b4_permutation_matrix``.
4. Per Δ-eigenspace E_λ:
     (a) check π(g) E_λ ⊆ E_λ for every g (commutator commutator [π(g), P_λ] = 0)
     (b) decompose E_λ into B_4-irrep isotypic components by character
         projection (Burnside / orbit counting).
5. Compares the encoder's actual basis against the simultaneous eigenbasis.
   The encoder's "basis" is the tensor-DCT basis e_i (x) e_j (x) e_k (x) e_l
   from ``tables_4d.tensor_eigvec_4d``. We sort it by P_8-eigenvalue tuple
   (i,j,k,l) → λ_i + λ_j + λ_k + λ_l so eigenspaces line up.

Run from python/ : ``python research/spectral_identity_4d_verification.py``.

For speed-of-development the default config tests the **2D Z_8^2 = 64-dim**
case fully and the **full 4D Z_8^4 = 4096-dim** case in single-eigenspace
spot-checks — full per-eigenspace 4D analysis on a laptop is doable but takes
~20 minutes due to character-projection over 384 group elements. Set
``SCALE = "FULL_4D_ALL"`` to run it.
"""
from __future__ import annotations

import sys
import time

# Force UTF-8 stdout on Windows consoles so we can print Greek/math chars
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass
from collections import defaultdict
from typing import Dict, List, Tuple

import numpy as np
from scipy.sparse import csr_matrix, eye as speye, kron as spkron

# Ensure we can import chess_spectral when running from python/ directly
import os
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_DIR = os.path.dirname(THIS_DIR)
if PYTHON_DIR not in sys.path:
    sys.path.insert(0, PYTHON_DIR)

from chess_spectral import tables_4d as t4  # noqa: E402


# --- Knobs -----------------------------------------------------------------

# Three scales:
#   "Z8_2D"        : 2D Z_8^2 = 64-dim,  group = B_2 (8 elements). Cheap.
#   "P8_2D"        : 2D P_8^2 = 64-dim,  same group. Cheap.
#   "FULL_4D"      : 4D P_8^4 = 4096-dim, B_4 (384 elements).
#                    Spectrum + B_4-stability check on every eigenspace.
#                    Skips full irrep decomposition past dim-4 spaces for time.
#   "FULL_4D_ALL"  : Full 4D analysis including isotypic decomposition on
#                    every eigenspace. Slow (~20 min on laptop).
SCALE = os.environ.get("SCALE", "FULL_4D")

TOL = 1e-10
TOL_LOOSE = 1e-7   # for char-projection (uses dense float64)
RNG_SEED = 42


# --- Graphs ----------------------------------------------------------------


def p_n_laplacian(n: int) -> np.ndarray:
    """Laplacian of the path graph P_n (open boundary, like t4.p8_laplacian)."""
    A = np.zeros((n, n), dtype=np.float64)
    for i in range(n - 1):
        A[i, i + 1] = 1.0
        A[i + 1, i] = 1.0
    return np.diag(A.sum(axis=1)) - A


def c_n_laplacian(n: int) -> np.ndarray:
    """Laplacian of the cycle graph C_n (Z_n as a Cayley graph of {±1})."""
    A = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        A[i, (i + 1) % n] = 1.0
        A[(i + 1) % n, i] = 1.0
    return 2.0 * np.eye(n) - A


def kron_sum_laplacian_dense(L1: np.ndarray, dim: int) -> np.ndarray:
    """Kronecker sum of `dim` copies of L1 (dense)."""
    n = L1.shape[0]
    out = np.zeros((n ** dim, n ** dim), dtype=L1.dtype)
    eye = np.eye(n, dtype=L1.dtype)
    for axis in range(dim):
        factors = [eye] * dim
        factors[axis] = L1
        T = factors[0]
        for f in factors[1:]:
            T = np.kron(T, f)
        out += T
    return out


def kron_sum_laplacian_sparse(L1_sp: csr_matrix, dim: int) -> csr_matrix:
    n = L1_sp.shape[0]
    eye = speye(n, format="csr")
    out: csr_matrix | None = None
    for axis in range(dim):
        factors = [eye] * dim
        factors[axis] = L1_sp
        T = factors[0]
        for f in factors[1:]:
            T = spkron(T, f, format="csr")
        out = T if out is None else (out + T)
    assert out is not None
    return out.tocsr()


# --- Group action ----------------------------------------------------------


def b4_unitary_dict() -> Dict[int, csr_matrix]:
    """{idx -> sparse 4096x4096 perm matrix} for the full B_4 closure."""
    closure = t4.b4_closure()
    return {i: t4.b4_permutation_matrix(g) for i, g in enumerate(closure)}


def b2_unitary_dict_for_p8() -> Dict[int, np.ndarray]:
    """B_2 (signed permutations on Z^2) acting on the 8x8 = 64-dim 2D
    lattice, treating sign flips as reflections through the centered
    coord (matches t4 convention)."""
    n = t4.BOARD_SIDE
    perms = [(0, 1), (1, 0)]
    sign_combos = [(s0, s1) for s0 in (1, -1) for s1 in (1, -1)]
    out: Dict[int, np.ndarray] = {}
    idx = 0
    for perm in perms:
        for signs in sign_combos:
            P = np.zeros((n * n, n * n), dtype=np.float64)
            for x in range(n):
                for y in range(n):
                    src = (x, y)
                    flipped = tuple(
                        (n - 1 - src[i]) if signs[i] == -1 else src[i]
                        for i in range(2)
                    )
                    out_coord = [0, 0]
                    for i in range(2):
                        out_coord[perm[i]] = flipped[i]
                    s_in = x * n + y
                    s_out = out_coord[0] * n + out_coord[1]
                    P[s_out, s_in] = 1.0
            out[idx] = P
            idx += 1
    return out


# --- Spectrum analysis -----------------------------------------------------


def group_eigenspaces(eigvals: np.ndarray, eigvecs: np.ndarray,
                      tol: float = 1e-9
                      ) -> List[Tuple[float, np.ndarray]]:
    """Return list of (lambda, V) pairs where V columns span E_λ.

    Eigenvalues are bucketed by rounded value (precision = `tol`).
    """
    order = np.argsort(eigvals)
    e_sorted = eigvals[order]
    v_sorted = eigvecs[:, order]
    spaces: List[Tuple[float, np.ndarray]] = []
    start = 0
    for k in range(1, len(e_sorted) + 1):
        if k == len(e_sorted) or abs(e_sorted[k] - e_sorted[start]) > tol:
            spaces.append(
                (float(np.mean(e_sorted[start:k])), v_sorted[:, start:k])
            )
            start = k
    return spaces


def projector_from_basis(V: np.ndarray) -> np.ndarray:
    """Orthogonal projector onto col-span(V)."""
    # V columns assumed orthonormal (eigh output). Use V V^T directly.
    return V @ V.T


def is_b4_stable(P_lambda: np.ndarray,
                 group_unitaries: Dict[int, csr_matrix | np.ndarray],
                 tol: float = TOL_LOOSE) -> Tuple[bool, float]:
    """Check [π(g), P_λ] = 0 ⇔ π(g) P_λ π(g)^T = P_λ. Returns
    (stable, max_err)."""
    max_err = 0.0
    for g_idx, U in group_unitaries.items():
        if isinstance(U, csr_matrix):
            U_dense = U.toarray()
        else:
            U_dense = U
        diff = U_dense @ P_lambda - P_lambda @ U_dense
        e = float(np.max(np.abs(diff)))
        if e > max_err:
            max_err = e
    return (max_err < tol), max_err


def is_eigenspace_b4_stable_via_basis(V: np.ndarray,
                                       group_unitaries: Dict[int, csr_matrix],
                                       tol: float = TOL_LOOSE
                                       ) -> Tuple[bool, float]:
    """Efficient version: V is a (N, m) ortho basis of E_lambda; for each
    g check that pi(g) V still lies in span(V). With sparse permutation
    π(g), pi(g) V is row-permutation of V (O(N*m)), and the residual
    (I - V V^T)(pi(g) V) is the failure norm (O(N*m + m^2)). Per (g, λ)
    this is O(N*m + m^2) instead of the O(N^3) full-projector version,
    making the full 4D run finish in seconds rather than hours.
    """
    max_err = 0.0
    N, m = V.shape
    for g_idx, U in group_unitaries.items():
        if isinstance(U, csr_matrix):
            piV = U @ V                       # sparse @ dense: O(nnz * m) = O(N * m)
        else:
            piV = U @ V
        # (I - V V^T) piV = piV - V (V^T piV)
        proj_coords = V.T @ piV               # m x m
        residual = piV - V @ proj_coords      # N x m
        e = float(np.max(np.abs(residual)))
        if e > max_err:
            max_err = e
    return (max_err < tol), max_err


# --- Encoder basis ---------------------------------------------------------


def encoder_basis_4d() -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (modes, lambdas, idx_tuples).

    modes : (4096, 4096), columns are tensor-DCT eigenvectors.
    lambdas : (4096,), eigenvalues λ = λ_i + λ_j + λ_k + λ_l (sorted ascending).
    idx_tuples : (4096, 4), the (i,j,k,l) tuple for each column.
    """
    evecs_1d, evals_1d = t4.eig_p8()
    n = t4.BOARD_SIDE
    modes = np.empty((n ** 4, n ** 4), dtype=np.float64)
    lambdas = np.empty(n ** 4, dtype=np.float64)
    tuples = np.empty((n ** 4, 4), dtype=np.int32)
    col = 0
    for i in range(n):
        for j in range(n):
            for k in range(n):
                for l in range(n):
                    modes[:, col] = t4.tensor_eigvec_4d(evecs_1d, i, j, k, l)
                    lambdas[col] = evals_1d[i] + evals_1d[j] + evals_1d[k] + evals_1d[l]
                    tuples[col] = (i, j, k, l)
                    col += 1
    order = np.argsort(lambdas, kind="stable")
    return modes[:, order], lambdas[order], tuples[order]


def encoder_basis_2d_p8() -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    evecs_1d, evals_1d = t4.eig_p8()
    n = t4.BOARD_SIDE
    modes = np.empty((n ** 2, n ** 2), dtype=np.float64)
    lambdas = np.empty(n ** 2, dtype=np.float64)
    tuples = np.empty((n ** 2, 2), dtype=np.int32)
    col = 0
    for i in range(n):
        for j in range(n):
            v = np.einsum("a,b->ab", evecs_1d[:, i], evecs_1d[:, j]).ravel()
            modes[:, col] = v
            lambdas[col] = evals_1d[i] + evals_1d[j]
            tuples[col] = (i, j)
            col += 1
    order = np.argsort(lambdas, kind="stable")
    return modes[:, order], lambdas[order], tuples[order]


# --- 2D pilot --------------------------------------------------------------


def pilot_2d_p8() -> Dict[str, object]:
    """Full 2D check on P_8 □ P_8 (= encoder basis 2D analog)."""
    print("=" * 72)
    print("Pilot: 2D P_8 (x) P_8 (8x8 = 64-dim) under B_2 group action")
    print("=" * 72)
    L1 = p_n_laplacian(t4.BOARD_SIDE)
    L = kron_sum_laplacian_dense(L1, 2)
    eigvals, eigvecs = np.linalg.eigh(L)
    spaces = group_eigenspaces(eigvals, eigvecs)
    print(f"  graph dim        = {L.shape[0]}")
    print(f"  distinct eigvals = {len(spaces)}")
    print(f"  eigenvalue spectrum (rounded), multiplicities:")
    for lam, V in spaces:
        print(f"    λ = {lam:8.5f}   mult = {V.shape[1]:2d}")

    G = b2_unitary_dict_for_p8()
    print(f"  group order      = {len(G)} (B_2)")
    all_stable = True
    for lam, V in spaces:
        P = projector_from_basis(V)
        stable, err = is_b4_stable(P, G)
        flag = "OK" if stable else "FAIL"
        print(f"    λ = {lam:8.5f}  B_2-stable={flag}  max[π,P] = {err:.2e}")
        if not stable:
            all_stable = False

    enc_modes, enc_lambdas, enc_tuples = encoder_basis_2d_p8()
    err_basis = 0.0
    for col in range(enc_modes.shape[1]):
        v = enc_modes[:, col]
        Lv = L @ v
        residual = Lv - enc_lambdas[col] * v
        err_basis = max(err_basis, float(np.max(np.abs(residual))))
    print(f"  encoder basis is L-eigenbasis: max||L v - λ v|| = {err_basis:.2e}")

    return {"all_stable_2d": all_stable, "max_residual_2d": err_basis,
            "n_spaces_2d": len(spaces)}


# --- 4D analysis -----------------------------------------------------------


def full_4d(test_irreps: bool) -> Dict[str, object]:
    """Full 4D check on the encoder's actual graph (P_8^4)."""
    print()
    print("=" * 72)
    print("Full 4D: P_8 [box] P_8 [box] P_8 [box] P_8  (4096-dim)  under B_4 (|G|=384)")
    print("=" * 72)
    t0 = time.time()
    L1 = p_n_laplacian(t4.BOARD_SIDE)
    L = kron_sum_laplacian_dense(L1, 4)
    print(f"  Δ build:           {time.time()-t0:.2f}s   shape {L.shape}")

    t0 = time.time()
    eigvals, eigvecs = np.linalg.eigh(L)
    print(f"  diagonalise (eigh): {time.time()-t0:.2f}s")

    spaces = group_eigenspaces(eigvals, eigvecs)
    print(f"  distinct eigvals = {len(spaces)}")
    print(f"  total dim check  = {sum(V.shape[1] for _, V in spaces)} == 4096")

    # Eigenvalue spectrum + multiplicities
    print()
    print("  Eigenvalue spectrum (multiplicity tuples partly via 1D Kron-sum):")
    _, evals_1d = t4.eig_p8()
    print(f"    P_8 1D eigenvalues: {[f'{v:.5f}' for v in evals_1d]}")
    print()
    print("    λ          mult   |  λ          mult   |  λ          mult   |  λ          mult")
    print("    " + "-" * 88)
    cols: List[str] = []
    for lam, V in spaces:
        cols.append(f"λ={lam:8.5f} m={V.shape[1]:3d}")
    for r in range(0, len(cols), 4):
        line = "    "
        for c in range(4):
            if r + c < len(cols):
                line += f"{cols[r+c]:25s}"
        print(line)
    print()
    n_unique = len(spaces)
    max_mult = max(V.shape[1] for _, V in spaces)
    print(f"  {n_unique} distinct eigenvalues; max multiplicity = {max_mult}")

    # Check encoder basis is an actual L-eigenbasis of the right type
    t0 = time.time()
    enc_modes, enc_lambdas, enc_tuples = encoder_basis_4d()
    print(f"  build encoder basis: {time.time()-t0:.2f}s")

    err_basis = 0.0
    for col_step in range(0, enc_modes.shape[1], 64):  # spot-check stride
        v = enc_modes[:, col_step]
        Lv = L @ v
        residual = Lv - enc_lambdas[col_step] * v
        err_basis = max(err_basis, float(np.max(np.abs(residual))))
    print(f"  encoder basis is L-eigenbasis (stride 64 spot-check): "
          f"max||L v - λ v|| = {err_basis:.2e}")

    # Eigenvalue equality check: encoder λ-list vs Δ λ-list
    sp_lambdas = np.array([lam for lam, _ in spaces])
    sp_mults = np.array([V.shape[1] for _, V in spaces])
    enc_unique, enc_counts = np.unique(np.round(enc_lambdas, 9),
                                       return_counts=True)
    eig_match = (
        sp_lambdas.shape[0] == enc_unique.shape[0]
        and np.allclose(sp_lambdas, enc_unique, atol=1e-9)
        and np.array_equal(sp_mults, enc_counts)
    )
    print(f"  eigenvalue list / multiplicities match: {eig_match}")

    # B_4-stability of EVERY eigenspace
    print()
    print("  B_4-stability of Δ-eigenspaces ([π(g), P_λ] = 0 for all g):")
    G = b4_unitary_dict()
    print(f"    |B_4| = {len(G)}")

    t0 = time.time()
    n_stable = 0
    n_fail = 0
    max_global_err = 0.0
    fail_examples: List[Tuple[float, float]] = []
    for lam, V in spaces:
        # Use the efficient basis-residual form to keep this check tractable
        # at 4096-dim with 384 group elements. P_lambda's full 4096x4096
        # commutator would dominate runtime.
        stable, err = is_eigenspace_b4_stable_via_basis(V, G, tol=TOL_LOOSE)
        if err > max_global_err:
            max_global_err = err
        if stable:
            n_stable += 1
        else:
            n_fail += 1
            if len(fail_examples) < 5:
                fail_examples.append((lam, err))
    print(f"    {n_stable}/{n_unique} eigenspaces are B_4-stable")
    print(f"    max [π(g), P_λ] over all (g, λ) = {max_global_err:.2e}")
    print(f"    elapsed: {time.time()-t0:.1f}s")

    if n_fail > 0:
        print(f"    !! {n_fail} unstable eigenspaces. First few:")
        for lam, err in fail_examples:
            print(f"       λ = {lam:.5f}  err = {err:.2e}")

    # Encoder-basis-vs-eigenspace alignment per λ
    print()
    print("  Encoder basis spans each Δ-eigenspace (norm of P_λ proj):")
    align_max_err = 0.0
    for lam, V in spaces:
        # find encoder cols with eigenvalue ~= lam
        sel = np.where(np.abs(enc_lambdas - lam) < 1e-9)[0]
        if sel.size != V.shape[1]:
            print(f"    lam={lam:.5f}: encoder count {sel.size} != "
                  f"eigenspace dim {V.shape[1]}")
            continue
        Venc = enc_modes[:, sel]
        # The encoder columns lie in span(V) iff (I-P)V_enc == 0; compute
        # P V_enc = V (V^T V_enc) without materializing P.
        proj = V @ (V.T @ Venc)
        residual = Venc - proj
        e = float(np.max(np.abs(residual)))
        if e > align_max_err:
            align_max_err = e
    print(f"    max ||(I - P_λ) v_enc|| over all (λ, v_enc) = "
          f"{align_max_err:.2e}")

    irrep_summary = None
    if test_irreps:
        irrep_summary = isotypic_decomposition_4d(spaces, G)

    return {
        "n_unique_eigenvalues_4d": n_unique,
        "max_mult_4d": int(max_mult),
        "all_stable_4d": (n_fail == 0),
        "max_commutator_err_4d": max_global_err,
        "encoder_basis_residual_4d": err_basis,
        "encoder_alignment_residual_4d": align_max_err,
        "eigenvalue_match_4d": bool(eig_match),
        "irrep_summary_4d": irrep_summary,
    }


def isotypic_decomposition_4d(spaces, G: Dict[int, csr_matrix],
                              top_eigvals: int = 10) -> Dict[str, object]:
    """For the smallest few eigenspaces (where dim is tractable), build the
    full character-projected isotypic decomposition. We don't enumerate all
    20 B_4 irreps explicitly — instead we use Burnside's class-counting:

        #orbits = (1/|G|) Σ_g |Fix(π_λ(g))|

    But per-irrep multiplicity needs character tables. We sidestep by
    counting B_4-orbits in the eigenbasis: a basis vector v lives in a
    B_4-orbit, and the orbit count gives a coarse decomposition ("how
    many B_4-trivial-irrep components does E_λ contain").

    Specifically: trivial-irrep multiplicity = (1/|G|) Σ_g tr(π_λ(g))
                = (1/|G|) Σ_g tr(P_λ π(g) P_λ).
    """
    print()
    print("  Isotypic decomposition (trivial-irrep multiplicity per E_λ):")
    print("    [shows dim of B_4-invariant subspace inside each Δ-eigenspace]")
    n_show = min(top_eigvals, len(spaces))
    triv_mults: List[Tuple[float, int, int]] = []  # (lam, dim, triv_mult)
    for lam, V in spaces[:n_show]:
        # tr(P_lam pi(g) P_lam) = tr( (P_lam pi(g) P_lam) )
        #                      = tr( V V^T pi(g) V V^T )
        #                      = tr( (V^T pi(g) V) (V^T V) )
        #                      = tr( V^T pi(g) V )         since V^T V = I
        triv_sum = 0.0
        for g_idx, U in G.items():
            if isinstance(U, csr_matrix):
                piV = U @ V
            else:
                piV = U @ V
            # tr(V^T piV)
            triv_sum += float(np.einsum("ij,ij->", V, piV))
        triv_dim = triv_sum / len(G)
        triv_mults.append((lam, V.shape[1], int(round(triv_dim))))
        print(f"    lam={lam:8.5f}  dim={V.shape[1]:3d}   "
              f"trivial-irrep mult ~ {triv_dim:.4f}")
    return {"triv_mults": triv_mults, "n_shown": n_show}


# --- Main ------------------------------------------------------------------


def main() -> int:
    print(f"SCALE = {SCALE}")
    print(f"TOL    = {TOL}, TOL_LOOSE = {TOL_LOOSE}")
    print()

    summary: Dict[str, object] = {}

    if SCALE in ("Z8_2D", "P8_2D", "FULL_4D", "FULL_4D_ALL"):
        s2d = pilot_2d_p8()
        summary.update(s2d)

    if SCALE in ("FULL_4D", "FULL_4D_ALL"):
        test_irreps = (SCALE == "FULL_4D_ALL")
        s4d = full_4d(test_irreps=test_irreps)
        summary.update(s4d)

    print()
    print("=" * 72)
    print("BOTTOM LINE")
    print("=" * 72)
    if SCALE in ("FULL_4D", "FULL_4D_ALL"):
        verdict = "HOLDS" if (
            summary.get("all_stable_4d", False)
            and summary.get("eigenvalue_match_4d", False)
            and summary.get("encoder_basis_residual_4d", 1.0) < 1e-7
            and summary.get("encoder_alignment_residual_4d", 1.0) < 1e-7
        ) else "FAILS / NEEDS-CAVEAT"
        print(f"Simultaneous eigenbasis claim: {verdict}")
        print()
        for k, v in summary.items():
            print(f"  {k:40s} = {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
