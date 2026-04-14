"""D4 irrep projection on an 8x8 grid — self-contained.

Inlined from `chess_spectral.tables` so this spike has no out-of-tree
dependencies. The numerics are byte-identical to the chess-spectral
version (same permutation construction, same character table, same
Serre projection formula) so iteration-1 CSV numbers reproduce exactly.

D4 has 8 elements:
    0: identity                        (r, c)
    1: rotate 90° CCW                  (c, 7-r)
    2: rotate 180°                     (7-r, 7-c)
    3: rotate 270° CCW                 (7-c, r)
    4: mirror across vertical axis     (r, 7-c)
    5: mirror across horizontal axis   (7-r, c)
    6: mirror across main diagonal     (c, r)
    7: mirror across anti-diagonal     (7-c, 7-r)

Irrep characters (rows of D4 character table):
        e   r90 r180 r270 mv  mh  md  ma
    A1: 1   1   1    1    1   1   1   1
    A2: 1   1   1    1   -1  -1  -1  -1
    B1: 1  -1   1   -1    1  -1   1  -1
    B2: 1  -1   1   -1   -1   1  -1   1
    E:  2   0  -2    0    0   0   0   0   (2-dimensional)

Serre projection: P_R sig = (dim_R / |G|) Σ_g χ_R(g) ρ(g) sig.
"""
from __future__ import annotations

import numpy as np


BOARD_DIM = 64
IRREP_NAMES = ("A1", "A2", "B1", "B2", "E")


def _sq(r: int, c: int) -> int:
    return r * 8 + c


def _make_perm(g: int) -> np.ndarray:
    """Return the 64-length index permutation for D4 element `g`.

    `sig[_make_perm(g)]` applies group element g to the flattened grid.
    """
    p = np.zeros(BOARD_DIM, dtype=np.int64)
    for r in range(8):
        for c in range(8):
            if   g == 0: nr, nc = r, c
            elif g == 1: nr, nc = c, 7 - r
            elif g == 2: nr, nc = 7 - r, 7 - c
            elif g == 3: nr, nc = 7 - c, r
            elif g == 4: nr, nc = r, 7 - c
            elif g == 5: nr, nc = 7 - r, c
            elif g == 6: nr, nc = c, r
            elif g == 7: nr, nc = 7 - c, 7 - r
            p[_sq(r, c)] = _sq(nr, nc)
    return p


D4_PERMS = np.stack([_make_perm(g) for g in range(8)])  # (8, 64)

CHARS = {
    'A1': [ 1,  1,  1,  1,  1,  1,  1,  1],
    'A2': [ 1,  1,  1,  1, -1, -1, -1, -1],
    'B1': [ 1, -1,  1, -1,  1, -1,  1, -1],
    'B2': [ 1, -1,  1, -1, -1,  1, -1,  1],
    'E':  [ 2,  0, -2,  0,  0,  0,  0,  0],
}


def project_irrep(sig: np.ndarray, irrep_name: str) -> np.ndarray:
    """Project 64-dim board signal onto a D4 irrep via Serre's formula.

    `irrep_name` is one of 'A1', 'A2', 'B1', 'B2', 'E'. Returns a
    64-dim vector that is the component of `sig` lying in the named
    isotypic subspace.
    """
    chars = CHARS[irrep_name]
    dim_mu = 2 if irrep_name == 'E' else 1
    projected = np.zeros(BOARD_DIM)
    for g_idx, perm in enumerate(D4_PERMS):
        projected += chars[g_idx] * sig[perm]
    return (dim_mu / 8) * projected
