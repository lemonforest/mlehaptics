#!/usr/bin/env python3
"""analyze_fiber_rank_4d.py -- empirical fiber rank on Z_8^4.

Research question: in 2D the rank-5 fiber bundle has singular-value
spectrum (1.70, 0.82, 0.65, ...). Is rank 5 an invariant of the piece
Laplacian structure, or does 4D geometry add independent fiber
dimensions? This script answers it empirically by running two SVDs on
the per-piece fiber coupling tensors.

  1. Cross-piece SVD (2D-analogous). Stack normalized upper-triangles
     of C_p = U^T L_p U for p in {N, B, R, Q, K}. Thin SVD gives
     min(5, M) singular values. Rank tells us how many shared fiber
     directions exist across pieces.

  2. Per-piece SVD. Each C_p is a 4096x4096 matrix with block structure
     induced by the tensor-DCT basis. Its singular spectrum says how
     many principal modes each piece's coupling actually needs.

The 2.6 GB figure from the notebook is the cost of a naive per-square
table port (5 x 4096 x 4096 adjacency rows). This script's answer is
the compressed storage we actually want: SVD truncation to k modes
where the singular values have decayed to ~1% of the leading value.

Runtime: ~2-5 minutes on a typical laptop. Peak memory ~600 MB
(one C_piece at a time = 128 MB, plus U_tensor = 128 MB).

Usage:
    cd docs/chess-maths/chess-spectral/python
    python analyze_fiber_rank_4d.py [--tol 0.01] [--top 10]

Exit codes:
    0   success
    3   runtime error
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from chess_spectral import tables_4d as t4


PIECES = [
    ('knight', t4.knight4_targets),
    ('bishop', t4.bishop4_targets),
    ('rook',   t4.rook4_targets),
    ('queen',  t4.queen4_targets),
    ('king',   t4.king4_targets),
]


def _fmt_sv(sv: np.ndarray, top: int) -> str:
    shown = sv[:top]
    return ', '.join(f'{s:.4f}' for s in shown)


def _rank_at_tol(sv: np.ndarray, tol: float) -> int:
    """Count singular values >= tol * sv[0]. Assumes sv is sorted
    descending (numpy's svd returns sorted)."""
    if sv.size == 0 or sv[0] == 0.0:
        return 0
    cutoff = tol * sv[0]
    return int(np.sum(sv >= cutoff))


def run_cross_piece_svd(U: np.ndarray, top: int, tol: float,
                         zero_tol: float = 1e-6) -> dict:
    """Stack normalized upper-triangles of C_piece for all pieces, SVD,
    return singular values and rank summary.

    Handles the 4D rook specially: its Laplacian is a Kronecker sum of
    four K_8 Laplacians, which is exactly diagonal in the P_8-tensor-DCT
    basis, so its off-diagonal fiber is structurally zero. Naive
    normalization by a near-zero norm would amplify float64 round-off
    into a spurious basis direction. We drop any piece whose
    ||C_off||_F is below `zero_tol * max(||C_off||_F)`.
    """
    upper_idx = np.triu_indices(t4.N_SQUARES, k=1)
    m = upper_idx[0].size

    print(f'[cross] computing ||C_off||_F for {len(PIECES)} pieces'
          f' x {m} upper-triangle entries')
    t0 = time.perf_counter()

    raw_rows = []
    raw_norms = []
    for name, fn in PIECES:
        t_piece = time.perf_counter()
        L = t4._dense_laplacian(fn)
        C = U.T @ L @ U
        np.fill_diagonal(C, 0.0)
        v = C[upper_idx]
        nv = float(np.linalg.norm(v))
        raw_rows.append((name, v, nv))
        raw_norms.append(nv)
        dt = time.perf_counter() - t_piece
        print(f'  {name:8s}: ||C_off||_F = {nv:12.4f}  ({dt:.1f}s)')
        del L, C

    n_max = max(raw_norms) if raw_norms else 0.0
    threshold = zero_tol * n_max
    kept = [(name, v, nv) for name, v, nv in raw_rows if nv > threshold]
    dropped = [name for name, _, nv in raw_rows if nv <= threshold]
    if dropped:
        print(f'[cross] dropped zero-fiber pieces '
              f'(||C_off||_F < {threshold:.3e}): {dropped}')

    rows = np.zeros((len(kept), m), dtype=np.float32)
    for idx, (_, v, nv) in enumerate(kept):
        rows[idx] = (v / nv).astype(np.float32)
    del raw_rows

    _, sv_cross, _ = np.linalg.svd(rows, full_matrices=False)
    r_01 = _rank_at_tol(sv_cross, 0.1)
    r_tol = _rank_at_tol(sv_cross, tol)
    dt = time.perf_counter() - t0
    print(f'[cross] SVD of {len(kept)}xM in {dt:.1f}s')
    return {
        'sv': sv_cross,
        'n_kept': len(kept),
        'dropped': dropped,
        'rank_at_10pct': r_01,
        f'rank_at_{int(tol*100)}pct': r_tol,
        'top': sv_cross[:top].tolist(),
    }


def run_per_piece_svd(U: np.ndarray, top: int, tol: float) -> dict:
    """SVD of each 4096x4096 off-diagonal C_piece directly. Full SVD
    on a 4096x4096 matrix takes ~30-90s per piece; total ~5 min."""
    results = {}
    for name, fn in PIECES:
        t_piece = time.perf_counter()
        L = t4._dense_laplacian(fn)
        C = U.T @ L @ U
        np.fill_diagonal(C, 0.0)
        # Full SVD of 4096x4096 is O(n^3) ~ 70G ops; ~30-60s.
        sv = np.linalg.svd(C, compute_uv=False)
        r_01 = _rank_at_tol(sv, 0.1)
        r_tol = _rank_at_tol(sv, tol)
        frob = float(np.linalg.norm(C))
        results[name] = {
            'sv_top': sv[:top].tolist(),
            'rank_at_10pct': r_01,
            f'rank_at_{int(tol*100)}pct': r_tol,
            'frobenius': frob,
            'sv_leading': float(sv[0]),
            'sv_100': float(sv[min(99, sv.size - 1)]),
        }
        dt = time.perf_counter() - t_piece
        print(f'[per]   {name:8s}: sv[0]={sv[0]:10.4f}  '
              f'rank@10%={r_01:4d}  rank@{int(tol*100)}%={r_tol:4d}  '
              f'||F={frob:10.4f}  ({dt:.1f}s)')
        del L, C, sv
    return results


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog='analyze_fiber_rank_4d',
        description=(
            'Run per-piece and cross-piece SVD on Z_8^4 fiber couplings. '
            'Report singular-value spectra to inform the v1.1 fiber-sym '
            'truncation rank.'
        ),
    )
    ap.add_argument(
        '--tol', type=float, default=0.01,
        help='singular-value cutoff as fraction of leading sv (default 0.01)',
    )
    ap.add_argument(
        '--top', type=int, default=10,
        help='number of leading singular values to print (default 10)',
    )
    ap.add_argument(
        '--skip-per-piece', action='store_true',
        help='skip the expensive per-piece SVD (~5 min)',
    )
    ap.add_argument(
        '--skip-cross', action='store_true',
        help='skip the cross-piece SVD',
    )
    args = ap.parse_args(argv)

    print('building tensor-DCT basis U (4096 x 4096, 128 MB)...')
    t0 = time.perf_counter()
    U = t4.build_u_tensor_4d()
    print(f'  built in {time.perf_counter() - t0:.1f}s')

    report = {}
    if not args.skip_cross:
        print()
        print('=== cross-piece SVD (2D-analogous, shared basis) ===')
        report['cross'] = run_cross_piece_svd(U, args.top, args.tol)

    if not args.skip_per_piece:
        print()
        print('=== per-piece SVD (intrinsic rank per coupling) ===')
        report['per_piece'] = run_per_piece_svd(U, args.top, args.tol)

    print()
    print('=== summary ===')
    if 'cross' in report:
        c = report['cross']
        print(f'cross-piece top-{args.top} singular values:')
        print('  ' + _fmt_sv(c["sv"], args.top))
        print(f'  rank at >=10% of leading:      {c["rank_at_10pct"]}')
        print(f'  rank at >={int(args.tol*100)}% of leading:       '
              f'{c[f"rank_at_{int(args.tol*100)}pct"]}')

    if 'per_piece' in report:
        print()
        print('per-piece:')
        print(f'{"piece":10s} {"sv[0]":>12s} {"sv[100]":>12s} '
              f'{"rank@10%":>10s} {"rank@" + str(int(args.tol*100)) + "%":>10s}')
        for name, r in report['per_piece'].items():
            print(f'{name:10s} {r["sv_leading"]:12.4f} {r["sv_100"]:12.4f} '
                  f'{r["rank_at_10pct"]:10d} '
                  f'{r[f"rank_at_{int(args.tol*100)}pct"]:10d}')

    print()
    print('interpretation:')
    print('  - cross-piece rank tells us how many shared fiber')
    print('    directions exist across pieces (5 pieces -> rank <= 5).')
    print('    In 2D with 4 pieces this was rank 3 (per tables.py).')
    print('  - per-piece rank tells us the intrinsic dimensionality of')
    print('    each piece\'s fiber coupling. If these are small (<100)')
    print('    the truncated basis is the right storage format for v1.1.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
