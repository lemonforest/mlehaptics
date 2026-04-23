"""Static ray fiber bundle and holonomy probe (H5).

Construction parallels chess's ``chess_connection.py``.  At each
lattice site s we build a local fiber vector by stacking the
rows of the 8 ray Laplacians:

    F(s) = [row_s(L_N), row_s(L_NE), ..., row_s(L_NW)]  in R^{8 x 64}

Flattened to R^{512}, this is the per-site "rule content" contributed
by the 8 ray directions.  We then parallel-transport this vector
around a closed loop on the board by sign-matched alignment at each
step, and report the holonomy cos(F_start, F_end_after_transport).

Non-trivial holonomy (|cos - 1| > 0.01) for any tested loop is the
H5 pass criterion.

Note on interpretation.  Because the undirected ray Laplacians
collapse in pairs (L_N = L_S etc), half the stacked rows duplicate.
We keep all 8 to match the prompt's construction; the measurement
probes the geometry of the loop itself, not the rank of the fiber.
"""

from __future__ import annotations

import numpy as np

from othello_utils import BOARD_SIZE, N, RAY_NAMES, rc_to_idx
from ray_laplacians import build_ray_laplacians


def local_fibers() -> np.ndarray:
    """Return (64, 8, 64) tensor F where F[s, k, :] is row s of
    the k-th ray Laplacian (by RAY_NAMES order)."""
    rays = build_ray_laplacians()
    stacked = np.stack([rays[name] for name in RAY_NAMES], axis=0)
    # stacked: (8, 64, 64).  Per-site local fiber at s is stacked[:, s, :].
    # Reorder to (64, 8, 64):
    return np.transpose(stacked, (1, 0, 2))


def flat_fiber(s: int, fibers: np.ndarray | None = None) -> np.ndarray:
    if fibers is None:
        fibers = local_fibers()
    return fibers[s].reshape(-1)


def parallel_transport_cos(path: list[int]) -> dict:
    """Walk a closed or open path of site indices.  At each step
    align the running fiber with the destination fiber by sign
    (flip sign if inner product is negative) and record the cosine
    against the starting fiber when the path closes.

    Returns dict with loop cosine, accumulated sign flips, path
    description.
    """
    fibers = local_fibers()
    f0 = flat_fiber(path[0], fibers)
    current = f0.copy()
    flips = 0
    for s in path[1:]:
        target = flat_fiber(s, fibers)
        c = float(np.dot(current, target) / (
            np.linalg.norm(current) * np.linalg.norm(target) + 1e-30
        ))
        if c < 0:
            target = -target
            flips += 1
        current = target
    final_cos = float(
        np.dot(f0, current) / (
            np.linalg.norm(f0) * np.linalg.norm(current) + 1e-30
        )
    )
    return {
        "path": path,
        "loop_cosine": final_cos,
        "sign_flips": flips,
        "len_path": len(path),
    }


def default_loops() -> list[list[int]]:
    """A handful of small closed loops on the 8x8 board, returned as
    lists of site indices (first == last to signal closure)."""
    loops_rc = [
        # small plaquette in the centre
        [(3, 3), (3, 4), (4, 4), (4, 3), (3, 3)],
        # 3x3 loop in top-left
        [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2),
         (2, 1), (2, 0), (1, 0), (0, 0)],
        # triangle via main diagonal
        [(0, 0), (0, 7), (7, 0), (0, 0)],
        # rectangle across edge
        [(0, 0), (0, 3), (1, 3), (1, 0), (0, 0)],
    ]
    return [[rc_to_idx(r, c) for r, c in loop] for loop in loops_rc]


def run_h5(tol: float = 0.01) -> dict:
    loops = default_loops()
    results = [parallel_transport_cos(lp) for lp in loops]
    # PASS if any loop cosine differs from 1.0 by more than tol
    nontrivial = [
        r for r in results if abs(r["loop_cosine"] - 1.0) > tol
    ]
    return {
        "per_loop": results,
        "n_loops": len(results),
        "n_nontrivial": len(nontrivial),
        "pass": len(nontrivial) > 0,
    }


if __name__ == "__main__":
    r = run_h5()
    print(f"H5 static fiber holonomy: {r['n_nontrivial']}/"
          f"{r['n_loops']} loops non-trivial, PASS = {r['pass']}")
    for lr in r["per_loop"]:
        print(
            f"  path len {lr['len_path']}, cos = "
            f"{lr['loop_cosine']:+.6f}, sign flips = {lr['sign_flips']}"
        )
