"""Ray Laplacians on the 8x8 Othello lattice.

The 8 compass directions {N, NE, E, SE, S, SW, W, NW} define the
flank-influence structure of Othello (section 10.1, section 10.4).
For each direction d this module constructs:

- L_ray_undirected(d) : standard symmetric graph Laplacian whose edges
  are nearest-neighbour steps (r,c) <-> (r+dr, c+dc).  By construction
  L_d = L_{-d}, so the 8 labelled directions collapse to 4 distinct
  symmetric operators (N/S, E/W, NE/SW, NW/SE).  This is the natural
  self-adjoint object for spectral analysis.

- L_ray_directed(d) : directed path Laplacian whose adjacency records
  only forward steps (r,c) -> (r+dr, c+dc).  Non-symmetric; 8 genuinely
  distinct operators.  Used by the H6 fiber-rank probe where the
  prompt's rank-8 candidate requires 8 linearly independent matrices.

Also provided:

- L_ortho = L_N + L_E + L_S + L_W
- L_diag  = L_NE + L_SE + L_SW + L_NW
- L_rays  = sum of all 8 undirected ray Laplacians (= 2 * sum of
  the 4 distinct ones)
- 8-dim ray-indicator representation of D4 (see section 10.4).  The
  action of D4 permutes the 8 directions, and we expose its character
  decomposition so H2 can verify Gamma_8 = 2 A1 + B1 + B2 + 2 E.
"""

from __future__ import annotations

import numpy as np
from typing import Callable

from othello_utils import (
    BOARD_SIZE,
    N,
    RAY_NAMES,
    RAY_OFFSETS,
    ORTHO_RAYS,
    DIAG_RAYS,
    in_bounds,
    rc_to_idx,
)


# ---------------------------------------------------------------------------
# Per-direction Laplacians
# ---------------------------------------------------------------------------


def ray_laplacian_undirected(direction: str) -> np.ndarray:
    """Standard symmetric graph Laplacian for nearest-neighbour
    edges along direction ``direction`` (and implicitly its inverse,
    since graph edges are unordered).  Returns a 64x64 matrix.
    """
    dr, dc = RAY_OFFSETS[direction]
    L = np.zeros((N, N), dtype=float)
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            i = rc_to_idx(r, c)
            rr, cc = r + dr, c + dc
            if in_bounds(rr, cc):
                j = rc_to_idx(rr, cc)
                # Add the undirected edge {i, j}.  Each call only
                # adds this edge once (we do NOT also add it from j
                # because the reverse offset would produce the same
                # edge from j's perspective when we iterate to (rr, cc)
                # — we therefore only add here from the originating
                # side and let the transpose happen by symmetrising
                # afterwards).  To stay simple: build adjacency first,
                # then convert.
                L[i, j] -= 1.0
    # Symmetrise (since we added one direction only) and populate
    # diagonal = degree.
    A = -L  # adjacency so far (only forward edges)
    A = A + A.T  # both directions
    D = np.diag(A.sum(axis=1))
    return D - A


def ray_laplacian_directed(direction: str) -> np.ndarray:
    """Directed path Laplacian: edges (r,c) -> (r+dr, c+dc) only.

    Non-symmetric: L_d != L_{-d} in general.  Used for the rank-8
    fiber probe.  Defined as ``D_out - A_directed`` where
    ``A_directed[i,j] = 1`` iff there is a forward step from i to j
    and ``D_out[i,i]`` is the out-degree of i (0 or 1).
    """
    dr, dc = RAY_OFFSETS[direction]
    A = np.zeros((N, N), dtype=float)
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            i = rc_to_idx(r, c)
            rr, cc = r + dr, c + dc
            if in_bounds(rr, cc):
                j = rc_to_idx(rr, cc)
                A[i, j] = 1.0
    D = np.diag(A.sum(axis=1))
    return D - A


# ---------------------------------------------------------------------------
# Collections
# ---------------------------------------------------------------------------


def build_ray_laplacians(
    directed: bool = False,
) -> dict[str, np.ndarray]:
    builder: Callable[[str], np.ndarray] = (
        ray_laplacian_directed if directed else ray_laplacian_undirected
    )
    return {name: builder(name) for name in RAY_NAMES}


def orbit_laplacians(
    directed: bool = False,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(L_ortho, L_diag, L_rays_total)."""
    rays = build_ray_laplacians(directed=directed)
    L_ortho = sum(rays[r] for r in ORTHO_RAYS)
    L_diag = sum(rays[r] for r in DIAG_RAYS)
    L_all = L_ortho + L_diag
    return L_ortho, L_diag, L_all


# ---------------------------------------------------------------------------
# 8-dim ray-indicator representation of D4
# ---------------------------------------------------------------------------
# D4 permutes the 8 compass directions.  Under the permutation
# associated with each of the 8 group elements, each direction maps to
# another direction.  The character of the resulting 8-dim
# representation is the number of fixed points (trace of the
# permutation matrix) at each group element.

# Permutation of directions under D4 elements, using the same element
# numbering as d4_z2.D4_PERMS (E, C4, C2, C4^-1, sigma_axis_v,
# sigma_axis_h, sigma_diag_main, sigma_diag_anti).  Each row lists the
# image of (N, NE, E, SE, S, SW, W, NW) under g.  Derived by applying
# the 2x2 transform for g to each unit direction vector.
_DIR_VECS: dict[str, tuple[int, int]] = RAY_OFFSETS


def _transform_dir(
    vec: tuple[int, int], g: int
) -> tuple[int, int]:
    dr, dc = vec
    # Use the *direction* version of the transform: rotations and
    # reflections of unit vectors, NOT of lattice sites.  The mapping
    # is the same functional form as d4_z2._make_perm, applied to
    # (dr, dc).
    if g == 0:
        return (dr, dc)
    if g == 1:  # 90 CCW
        return (dc, -dr)
    if g == 2:  # 180
        return (-dr, -dc)
    if g == 3:  # 270 CCW
        return (-dc, dr)
    if g == 4:  # reflect vertical axis (col-flip): (dr, dc) -> (dr, -dc)
        return (dr, -dc)
    if g == 5:  # reflect horizontal axis (row-flip)
        return (-dr, dc)
    if g == 6:  # main diagonal: (dr,dc) -> (dc,dr)
        return (dc, dr)
    if g == 7:  # anti-diagonal
        return (-dc, -dr)
    raise ValueError(g)


def direction_permutations() -> list[np.ndarray]:
    """Return list of 8 permutations (length-8 int arrays) giving the
    action of each D4 element on the 8 compass directions in
    ``RAY_NAMES`` order.  ``perm[i]`` is the index of the image of
    direction i under g."""
    names = RAY_NAMES
    vec_to_name = {v: k for k, v in _DIR_VECS.items()}
    perms: list[np.ndarray] = []
    for g in range(8):
        p = np.zeros(8, dtype=int)
        for i, name in enumerate(names):
            v = _DIR_VECS[name]
            vp = _transform_dir(v, g)
            p[i] = names.index(vec_to_name[vp])
        perms.append(p)
    return perms


def ray_indicator_character() -> np.ndarray:
    """Length-8 character chi_Gamma8 of the 8-dim ray-indicator rep
    under the 8 D4 elements.  chi(g) = # fixed directions under g."""
    perms = direction_permutations()
    chi = np.zeros(8, dtype=float)
    for g, p in enumerate(perms):
        chi[g] = float(np.sum(p == np.arange(8)))
    return chi


def ray_indicator_irrep_decomposition() -> dict[str, int]:
    """Multiplicity of each D4 irrep in Gamma_8 via

        m_mu = (1/|G|) sum_g chi_mu(g) chi_Gamma8(g)
    """
    from d4_z2 import D4_CHARS

    chi_g = ray_indicator_character()
    mults: dict[str, int] = {}
    for mu, chi_mu in D4_CHARS.items():
        m = float(np.dot(chi_mu, chi_g)) / 8.0
        mults[mu] = int(round(m))
    return mults


# ---------------------------------------------------------------------------
# Sanity checks
# ---------------------------------------------------------------------------


def sanity_ray_spectra_finite() -> dict:
    rays = build_ray_laplacians()
    out = {}
    for name, L in rays.items():
        w = np.linalg.eigvalsh(L)
        out[name] = {
            "lambda_min": float(w.min()),
            "lambda_max": float(w.max()),
            "mean_degree": float(np.trace(L) / N),
        }
    # All eigenvalues should be non-negative (real PSD Laplacians)
    all_psd = all(
        out[name]["lambda_min"] > -1e-10 for name in RAY_NAMES
    )
    return {"per_ray": out, "all_psd": all_psd, "pass": all_psd}


def sanity_N_equals_S() -> dict:
    """Undirected N-ray Laplacian should equal S-ray Laplacian."""
    LN = ray_laplacian_undirected("N")
    LS = ray_laplacian_undirected("S")
    err = float(np.max(np.abs(LN - LS)))
    return {"err": err, "pass": err < 1e-12}


def sanity_h2_irrep_decomposition() -> dict:
    """H2 prediction: Gamma_8 = 2 A1 + 0 A2 + B1 + B2 + 2 E."""
    m = ray_indicator_irrep_decomposition()
    expected = {"A1": 2, "A2": 0, "B1": 1, "B2": 1, "E": 2}
    ok = all(m[k] == v for k, v in expected.items())
    return {"multiplicities": m, "expected": expected, "pass": ok}


if __name__ == "__main__":
    print("=== ray_laplacians sanity ===")
    r = sanity_ray_spectra_finite()
    print(f"ray spectra non-negative: PASS = {r['pass']}")
    for name in RAY_NAMES:
        info = r["per_ray"][name]
        print(
            f"  {name:3s}: lambda in [{info['lambda_min']:7.3f},"
            f" {info['lambda_max']:7.3f}], mean deg = "
            f"{info['mean_degree']:.3f}"
        )
    r = sanity_N_equals_S()
    print(
        f"L_N == L_S (undirected): max abs diff = {r['err']:.3e}, "
        f"PASS = {r['pass']}"
    )
    r = sanity_h2_irrep_decomposition()
    print(
        f"H2 Gamma_8 decomposition: measured = {r['multiplicities']},"
        f" expected = {r['expected']}, PASS = {r['pass']}"
    )
