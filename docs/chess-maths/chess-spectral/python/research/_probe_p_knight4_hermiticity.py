"""Cross-check probe: P_knight4 lifted to a 4096x4096 incidence matrix.

Same shape as _probe_p_rook4_hermiticity.py. Knight moves are pure
leapers with shift set {+/-2 g_i +/- g_j : i != j} — geometrically
involutive (k=1 knight hop is reversible at k=1). On-board boundary
clipping should still preserve symmetry, so we expect another
real-symmetric Hermitian operator with integer spectrum.

Run from python/ working directory.
"""
from __future__ import annotations
import sys
import numpy as np

sys.path.insert(0, ".")

from chess_spectral.phase_operators_4d import P_knight4  # noqa: E402
from chess_spectral.phase_operators_4d.phase_to_coords_4d import (  # noqa: E402
    PHI_TO_XYZW,
)


def main() -> int:
    basis_phases = sorted(PHI_TO_XYZW.keys())
    n = len(basis_phases)
    phase_to_idx = {p: i for i, p in enumerate(basis_phases)}

    M = np.zeros((n, n), dtype=np.float64)
    for j, origin_phi in enumerate(basis_phases):
        for d in P_knight4(origin_phi):
            i = phase_to_idx.get(d)
            if i is not None:
                M[i, j] = 1.0

    is_sym = bool(np.allclose(M, M.T))
    asym_count = int(np.count_nonzero(M - M.T))
    max_asym = float(np.max(np.abs(M - M.T)))

    eigs = np.linalg.eigvals(M)
    max_im = float(np.max(np.abs(eigs.imag)))
    re_range = (float(eigs.real.min()), float(eigs.real.max()))

    print("=== P_knight4 materialisation probe ===")
    print(f"n = {n}, nnz = {int(np.count_nonzero(M))}")
    print(f"real symmetric?       {is_sym}")
    print(f"#(M - M^T) != 0       {asym_count}")
    print(f"max |M - M^T|         {max_asym}")
    print(f"max |Im(eig)|         {max_im}")
    print(f"Re(eig) range         {re_range}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
