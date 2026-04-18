#!/usr/bin/env python3
"""staged_cosine.py -- localize where rank-3 fiber structure emerges.

Follow-up to direct_orthogonality.py. That script found that raw-Laplacian
Frobenius cosines between piece pairs are 0.83-0.97 in both 2D and 4D,
contradicting the hypothesis that the rank-3 fiber result from the DCT
cross-piece SVD reflects intrinsic Laplacian orthogonality.

This script runs the cosine comparison across FOUR progressive stages to
see where in the pipeline the rank-3 structure actually appears:

  Stage 1 -- raw Laplacian        L_p = D_p - A_p
  Stage 2 -- raw adjacency        A_p                 (removes diagonal D_p)
  Stage 3 -- centered adjacency   A_p - mean(A_p)     (removes DC-DC mode)
  Stage 4 -- DCT off-diagonal     off-diag(U^T L_p U) (full fiber-space view)

Each stage removes one more piece of structure. Where the cross-piece
cosines collapse from ~0.9 to near-zero is where the rank-3 fiber basis
actually lives.

Run:
    cd docs/chess-maths/chess-spectral/python
    python staged_cosine.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from chess_spectral import tables as t2
from chess_spectral import tables_4d as t4


PAIRS = [
    ('knight', 'rook'),
    ('knight', 'bishop'),
    ('knight', 'queen'),
    ('knight', 'king'),
    ('bishop', 'rook'),
    ('bishop', 'queen'),
    ('rook',   'queen'),
]

PIECES = ['knight', 'bishop', 'rook', 'queen', 'king']


def _targets_2d():
    return {
        'knight': t2.knight_targets,
        'bishop': t2.bishop_targets,
        'rook':   t2.rook_targets,
        'queen':  t2.queen_targets,
        'king':   t2.king_targets,
    }


def _targets_4d():
    return {
        'knight': t4.knight4_targets,
        'bishop': t4.bishop4_targets,
        'rook':   t4.rook4_targets,
        'queen':  t4.queen4_targets,
        'king':   t4.king4_targets,
    }


def _fro_cos(a: np.ndarray, b: np.ndarray) -> float:
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.sum(a * b)) / (na * nb)


def _center(M: np.ndarray) -> np.ndarray:
    """Subtract scalar mean from every entry. For an NxN matrix this
    removes the all-ones (J/N) component -- the DC-DC mode of any
    orthonormal basis whose first vector is the unit-constant vector.
    """
    return M - float(np.mean(M))


def _dct_off_diag_vec_2d(L: np.ndarray) -> np.ndarray:
    """For 2D: C = EVECS_GRID.T @ L @ EVECS_GRID, zero diagonal, return
    flattened upper-triangle."""
    C = t2.EVECS_GRID.T @ L @ t2.EVECS_GRID
    np.fill_diagonal(C, 0.0)
    idx = np.triu_indices(t2.BOARD_DIM, k=1)
    return C[idx]


def _dct_off_diag_vec_4d(L: np.ndarray, U: np.ndarray) -> np.ndarray:
    C = U.T @ L @ U
    np.fill_diagonal(C, 0.0)
    idx = np.triu_indices(t4.N_SQUARES, k=1)
    return C[idx]


def _cos_table(vecs: dict[str, np.ndarray], title: str) -> dict:
    print(f'=== {title} ===')
    print(f'{"pair":22s} {"cos":>10s}')
    table = {}
    for a, b in PAIRS:
        c = _fro_cos(vecs[a], vecs[b])
        table[f'{a}-{b}'] = c
        print(f'{a+"-"+b:22s} {c:10.6f}')
    print()
    return table


def run_2d() -> dict:
    print('--- 2D (Z_8^2) ---')
    tgts = _targets_2d()
    As = {n: t2.build_adjacency(fn) for n, fn in tgts.items()}
    Ls = {n: t2.graph_laplacian(A) for n, A in As.items()}
    As_c = {n: _center(A) for n, A in As.items()}
    Cs = {n: _dct_off_diag_vec_2d(L) for n, L in Ls.items()}
    print('  2D DCT off-diagonal norms:')
    for n in PIECES:
        print(f'    {n:8s} ||off-diag||_F = {np.linalg.norm(Cs[n]):.6e}')

    out = {
        'stage1_raw_L':      _cos_table(Ls, '2D stage 1: raw Laplacian L = D - A'),
        'stage2_raw_A':      _cos_table(As, '2D stage 2: raw adjacency A'),
        'stage3_centered_A': _cos_table(As_c, '2D stage 3: centered adjacency A - mean(A)'),
        'stage4_dct_off':    _cos_table(Cs, '2D stage 4: off-diag(U^T L U)'),
    }
    return out


def run_4d() -> dict:
    print('--- 4D (Z_8^4) ---')
    tgts = _targets_4d()
    print('  building 5 dense Laplacians (~640 MB)...')
    Ls = {n: t4._dense_laplacian(fn) for n, fn in tgts.items()}
    # A from L: A = D - L, and D is diag of L's column sums negated...
    # Simpler: A = -L with diagonal set to 0 (for undirected piece graphs
    # with no self-loops, L_ii = deg_i and L_ij = -A_ij for i != j).
    As = {}
    for n, L in Ls.items():
        A = -L.copy()
        np.fill_diagonal(A, 0.0)
        As[n] = A
    As_c = {n: _center(A) for n, A in As.items()}

    print('  building tensor-DCT U...')
    U = t4.build_u_tensor_4d()
    print('  projecting 5 L into DCT off-diagonal vectors...')
    Cs = {}
    for n in PIECES:
        Cs[n] = _dct_off_diag_vec_4d(Ls[n], U)
        print(f'    {n:8s} ||off-diag||_F = {np.linalg.norm(Cs[n]):.6e}')

    out = {
        'stage1_raw_L':      _cos_table(Ls, '4D stage 1: raw Laplacian L = D - A'),
        'stage2_raw_A':      _cos_table(As, '4D stage 2: raw adjacency A'),
        'stage3_centered_A': _cos_table(As_c, '4D stage 3: centered adjacency A - mean(A)'),
        'stage4_dct_off':    _cos_table(Cs, '4D stage 4: off-diag(U^T L U)'),
    }
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog='staged_cosine',
        description=(
            'Staged Frobenius-cosine progression across four matrix '
            'representations (raw L, raw A, centered A, DCT off-diag) '
            'to localize where piece-pair orthogonality emerges.'
        ),
    )
    ap.add_argument(
        '--skip-4d', action='store_true',
        help='skip 4D (uses ~1.5 GB peak)',
    )
    args = ap.parse_args(argv)

    res = {'2d': run_2d()}
    if not args.skip_4d:
        res['4d'] = run_4d()

    # Summary: one row per pair, columns = stages.
    print('=== progression summary ===')
    header = (f'{"pair":22s} '
              f'{"raw L":>10s} {"raw A":>10s} '
              f'{"cent. A":>10s} {"DCT off":>10s}')
    for dim in ('2d', '4d'):
        if dim not in res:
            continue
        print(f'-- {dim.upper()} --')
        print(header)
        for a, b in PAIRS:
            key = f'{a}-{b}'
            r = res[dim]
            print(f'{key:22s} '
                  f'{r["stage1_raw_L"][key]:10.4f} '
                  f'{r["stage2_raw_A"][key]:10.4f} '
                  f'{r["stage3_centered_A"][key]:10.4f} '
                  f'{r["stage4_dct_off"][key]:10.4f}')
        print()

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
