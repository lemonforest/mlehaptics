#!/usr/bin/env python3
"""direct_orthogonality.py -- raw-matrix orthogonality of piece Laplacians.

Answers the open question raised by the cross-piece SVD fiber result: is
knight/slider orthogonality INTRINSIC to the piece-type graph Laplacians,
or is it an artifact of the DCT basis projection used to build the fiber
bundle?

For each lattice (2D Z_8^2, 4D Z_8^4) we compute Frobenius cosines on
the raw 4096x4096 (or 64x64) Laplacians:

    cos(L_A, L_B) = tr(L_A^T L_B) / (||L_A||_F * ||L_B||_F)

Pairs reported:
    - knight-rook, knight-bishop, knight-queen  (slider tests)
    - knight-king                               (contrast: king not slider)
    - bishop-rook                               (slider-slider contrast)

If the knight-slider cosines are near zero on the RAW Laplacians, then
the rank-3 fiber basis we extracted in the DCT projection reflects a
property of the underlying graph geometry rather than the basis choice.

Usage:
    cd docs/chess-maths/chess-spectral/python
    python direct_orthogonality.py

Output: a per-dimension table + a flag for any surprising (non-small)
knight-slider product. The script DOES NOT project through any basis.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from chess_spectral import tables as t2
from chess_spectral import tables_4d as t4


PAIRS = [
    ('knight', 'rook'),    # slider
    ('knight', 'bishop'),  # slider
    ('knight', 'queen'),   # slider (queen = rook + bishop)
    ('knight', 'king'),    # contrast: king is not a slider
    ('bishop', 'rook'),    # slider-slider contrast
    ('bishop', 'queen'),   # queen = rook + bishop (expected large overlap)
    ('rook',   'queen'),   # queen = rook + bishop (expected large overlap)
]


def _build_2d_laplacians() -> dict[str, np.ndarray]:
    """Build 2D (64x64) piece Laplacians from the raw adjacency helpers.
    No DCT, no eigenbasis projection."""
    names = {
        'knight': t2.knight_targets,
        'bishop': t2.bishop_targets,
        'rook':   t2.rook_targets,
        'queen':  t2.queen_targets,
        'king':   t2.king_targets,
    }
    out = {}
    for name, fn in names.items():
        A = t2.build_adjacency(fn)
        out[name] = t2.graph_laplacian(A)
    return out


def _build_4d_laplacians() -> dict[str, np.ndarray]:
    """Build 4D (4096x4096) piece Laplacians as dense float64. Each uses
    ~128 MB; total ~640 MB peak."""
    names = {
        'knight': t4.knight4_targets,
        'bishop': t4.bishop4_targets,
        'rook':   t4.rook4_targets,
        'queen':  t4.queen4_targets,
        'king':   t4.king4_targets,
    }
    out = {}
    for name, fn in names.items():
        out[name] = t4._dense_laplacian(fn)
    return out


def _frob_cosine(A: np.ndarray, B: np.ndarray) -> tuple[float, float, float, float]:
    """Return (tr(A^T B), ||A||_F, ||B||_F, cosine). For symmetric L,
    tr(A^T B) = tr(A B) = sum_{i,j} A[i,j] * B[i,j]."""
    tr_ab = float(np.sum(A * B))
    nA = float(np.linalg.norm(A))
    nB = float(np.linalg.norm(B))
    denom = nA * nB
    cos = tr_ab / denom if denom > 0 else 0.0
    return tr_ab, nA, nB, cos


def _print_table(title: str, laps: dict[str, np.ndarray]) -> list[dict]:
    print(f'=== {title} ===')
    print(f'{"pair":22s} {"tr(L_A L_B)":>16s} {"||L_A||":>12s} '
          f'{"||L_B||":>12s} {"cos":>12s}')
    rows = []
    for a, b in PAIRS:
        tr_ab, nA, nB, cos = _frob_cosine(laps[a], laps[b])
        print(f'{a+"-"+b:22s} {tr_ab:16.4f} {nA:12.4f} {nB:12.4f} '
              f'{cos:12.6f}')
        rows.append({'pair': f'{a}-{b}', 'tr': tr_ab,
                     'norm_a': nA, 'norm_b': nB, 'cos': cos})
    print()
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog='direct_orthogonality',
        description=(
            'Compute raw (no DCT) Frobenius cosines between piece '
            'Laplacians on Z_8^2 and Z_8^4. Answers: is knight/slider '
            'orthogonality intrinsic or basis-dependent?'
        ),
    )
    ap.add_argument(
        '--flag', type=float, default=0.1,
        help='|cos| > this is flagged as surprising (default 0.1)',
    )
    ap.add_argument(
        '--skip-4d', action='store_true',
        help='skip the 4D case (uses ~640 MB peak)',
    )
    args = ap.parse_args(argv)

    print('Building 2D piece Laplacians on Z_8^2 (5 x 64x64)...')
    laps_2d = _build_2d_laplacians()
    rows_2d = _print_table('2D: Z_8^2 raw Laplacians', laps_2d)
    del laps_2d

    rows_4d = []
    if not args.skip_4d:
        print('Building 4D piece Laplacians on Z_8^4 (5 x 4096x4096, ~640 MB)...')
        laps_4d = _build_4d_laplacians()
        rows_4d = _print_table('4D: Z_8^4 raw Laplacians', laps_4d)
        del laps_4d

    print('=== interpretation ===')
    print(f'flagging |cos| > {args.flag}')
    any_surprise = False
    for label, rows in [('2D', rows_2d), ('4D', rows_4d)]:
        for r in rows:
            if 'knight' in r['pair'] and r['pair'] != 'knight-king':
                if abs(r['cos']) > args.flag:
                    print(f'  [{label}] SURPRISE: {r["pair"]} cos={r["cos"]:.6f} '
                          f'(knight-slider should be ~0 if rank-3 fiber '
                          f'is basis-independent)')
                    any_surprise = True

    if not any_surprise and (rows_2d or rows_4d):
        print('  knight-slider cosines are small in both lattices -->')
        print('  orthogonality is intrinsic to the piece-type graph')
        print('  structure, not a DCT-basis artifact. Rank-3 fiber bundle')
        print('  is a real geometric property.')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
