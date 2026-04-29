"""Materialise P_rook4 as a 4096x4096 matrix on the board image and
probe Hermiticity / pseudo-Hermiticity under a diagonal metric.

Construction.
    Basis: |phi> for each phi in PHI_TO_XYZW (4096 board phases).
    Matrix entry M[a, b] = 1 iff a in P_rook4(b) AND a is on-board.
    (Off-board destinations are dropped via PHI_TO_XYZW membership.)

This is the natural lift of the predicate P_rook4: bool to a
linear operator. If it were Hermitian we would have M = M^T (entries
are 0/1, real). The rook reach is symmetric under swap of source
and destination at the geometric level (k-step axis hop is
reversible at k steps), but the on-board boundary clipping can
break that symmetry near the [0,7]^4 boundary.

Probe checks:
    1. Is M = M.T (real-Hermitian)?
    2. Eigenvalue spectrum: real?
    3. If non-Hermitian, search a positive diagonal metric eta = diag(g)
       solving M^T diag(g) - diag(g) M = 0 entry-wise. Reduces to a
       homogeneous linear system; check if a strictly-positive solution
       exists in the kernel.

Run from python/ working directory.
"""
from __future__ import annotations
import sys
import numpy as np

# Ensure the in-tree package is importable.
sys.path.insert(0, ".")

from chess_spectral.phase_operators_4d import (  # noqa: E402
    P_rook4, phi4,
)
from chess_spectral.phase_operators_4d.phase_to_coords_4d import (  # noqa: E402
    PHI_TO_XYZW,
)


def materialise_p_rook4() -> tuple[np.ndarray, list[int]]:
    """Build the 4096x4096 incidence matrix of P_rook4 on the board image.

    Returns the dense matrix M and the ordered list of basis phases.
    M[i, j] = 1 iff basis_phases[i] in P_rook4(basis_phases[j]) AND
    basis_phases[i] is on-board (i.e., in PHI_TO_XYZW).
    """
    basis_phases = sorted(PHI_TO_XYZW.keys())
    n = len(basis_phases)
    phase_to_idx = {p: i for i, p in enumerate(basis_phases)}

    M = np.zeros((n, n), dtype=np.float64)
    for j, origin_phi in enumerate(basis_phases):
        dests = P_rook4(origin_phi)
        for d in dests:
            i = phase_to_idx.get(d)
            if i is not None:  # on-board
                M[i, j] = 1.0
    return M, basis_phases


def probe_hermiticity(M: np.ndarray) -> dict:
    """Run the full Hermitian / pseudo-Hermitian probe."""
    n = M.shape[0]
    out: dict = {"n": n}

    out["nnz"] = int(np.count_nonzero(M))
    out["is_real_symmetric"] = bool(np.allclose(M, M.T))
    out["asym_count"] = int(np.count_nonzero(M - M.T))
    out["max_asym_abs"] = float(np.max(np.abs(M - M.T)))

    # Eigenvalues. M is dense 4096x4096 — feasible but ~1-2 minutes.
    # Use a smaller probe (single rank-direction projection) to keep
    # the run fast: restrict to the 8x8x8x8 subblock x=0 (z-w-y plane
    # at fixed x=0) and look at moves *within* that subblock — but
    # rook moves change one coord at a time, so the x=0 slab is closed
    # under the y/z/w-axis components of the rook only. Lift the full
    # 4096 instead; 1 minute is fine.
    eigs = np.linalg.eigvals(M)
    max_im = float(np.max(np.abs(eigs.imag)))
    real_part_extrema = (float(eigs.real.min()), float(eigs.real.max()))
    out["max_imag_eig"] = max_im
    out["real_eigs_in_tol"] = max_im < 1e-9
    out["eig_real_range"] = real_part_extrema
    out["sample_eigs"] = [
        complex(e) for e in eigs[: min(8, len(eigs))]
    ]
    return out


def probe_diagonal_metric(M: np.ndarray) -> dict:
    """Search for a positive diagonal metric eta = diag(g), g > 0,
    such that M^T diag(g) = diag(g) M.

    Entry-wise: M[j,i] * g[j] = g[i] * M[i,j], i.e.,
    if M[i,j] != 0 or M[j,i] != 0:
        M[j,i] * g[j] - M[i,j] * g[i] = 0
    A strictly positive g exists iff the constraint graph is
    consistent (cycle conditions hold). We solve as a linear system
    in log space: log g[j] - log g[i] = log(M[i,j] / M[j,i]) when
    both are nonzero. For 0/1 matrices that means M[i,j] = M[j,i]
    on the support — i.e., already symmetric on the support — or
    one side is 0 (forcing the corresponding g to 0, breaking
    positivity).
    """
    n = M.shape[0]
    out: dict = {}

    # Find any (i, j) with exactly one of M[i,j], M[j,i] nonzero.
    # If that exists, no strictly-positive diagonal metric solves
    # the pseudo-Hermiticity equation: it would force g[i] = 0 or
    # g[j] = 0.
    asym_one_sided = 0
    for i, j in zip(*np.nonzero(M)):
        if i == j:
            continue
        if M[j, i] == 0.0:
            asym_one_sided += 1
    out["one_sided_offdiag_count"] = asym_one_sided
    out["diagonal_metric_admissible"] = (asym_one_sided == 0)
    return out


def main() -> int:
    print("Materialising P_rook4 on the 4096-element board image...")
    M, basis = materialise_p_rook4()

    print("Probing Hermiticity / spectrum...")
    h = probe_hermiticity(M)

    print("Probing diagonal pseudo-Hermitian metric admissibility...")
    p = probe_diagonal_metric(M)

    print()
    print("=== P_rook4 materialisation probe ===")
    print(f"basis size n         = {h['n']}")
    print(f"nnz                  = {h['nnz']}")
    print(f"is real symmetric?   = {h['is_real_symmetric']}")
    print(f"#(M - M^T) != 0      = {h['asym_count']}")
    print(f"max |M_ij - M_ji|    = {h['max_asym_abs']}")
    print(f"max |Im(eig)|        = {h['max_imag_eig']}")
    print(f"all eigs real (1e-9)? = {h['real_eigs_in_tol']}")
    print(f"Re(eig) range        = {h['eig_real_range']}")
    print(f"first 8 eigs         = {h['sample_eigs']}")
    print(f"one-sided offdiag    = {p['one_sided_offdiag_count']}")
    print(f"diag metric admiss?  = {p['diagonal_metric_admissible']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
