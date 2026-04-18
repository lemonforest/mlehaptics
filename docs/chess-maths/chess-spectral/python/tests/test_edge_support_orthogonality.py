"""Edge-support orthogonality between piece adjacencies.

Part 3b gate for the v1.1 fiber investigation. Asserts the two-level
structural decomposition of chess piece movement graphs on Z_8^d
(d in {2, 4}):

  Primitives. {knight, bishop, rook} have mutually-disjoint edge
  supports. No two share any edge.

  Knight is additionally disjoint from king: the (2,1)-leap never
  coincides with a one-step move.

  Sums. Queen is a compound piece whose edges partition exactly:
      <A_queen, A_queen> = <A_queen, A_bishop> + <A_queen, A_rook>
  Queen sums bishop + rook edges at all distances.

  King dimension-sensitivity. In 2D the king is Chebyshev-1 and every
  king edge is either a one-step bishop or a one-step rook, so
      <A_king, A_king> = <A_king, A_bishop> + <A_king, A_rook>    (2D)
  In 4D the king includes Hamming-distance 3 and 4 unit moves
  (3-axis and 4-axis simultaneous ±1 steps) that no named piece in
  the codebase covers. The partition therefore splits into four
  classes:
      <A_king, A_king> = <A_king, A_bishop>   (HD=2, one-step)
                       + <A_king, A_rook>     (HD=1, one-step)
                       + <A_king, A_king_hd3> (HD=3, one-step)
                       + <A_king, A_king_hd4> (HD=4, one-step)
  where A_king_hd3 / A_king_hd4 are constructed directly from the
  king target function filtered by Hamming distance. This asymmetry
  between 2D and 4D is captured as a test-enforced fact.

Because each adjacency is a binary {0,1} matrix, the Frobenius inner
product <A_p, A_q> = sum(A_p * A_q) counts shared edges. Disjoint
edge sets therefore give exact integer zeros (not floating-point
near-zeros) independent of representation or basis.

This is the graph-theoretic ground truth that underwrites the staged-
cosine stage-2 collapse we documented in the notebook: raw-adjacency
knight/slider cosines are zero because the edges never coincide, not
because anything lives in a shared spectral subspace.

Run via `python -m pytest tests/test_edge_support_orthogonality.py`
from the python/ directory.
"""
from __future__ import annotations

import os
import sys
from itertools import combinations

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

from chess_spectral import tables as t2                  # noqa: E402
from chess_spectral import tables_4d as t4               # noqa: E402


DISJOINT_PIECES = ['knight', 'bishop', 'rook']


def _fro_inner(A: np.ndarray, B: np.ndarray) -> int:
    """Frobenius inner product as an exact integer.

    Adjacency matrices are binary {0,1}; element-wise product is also
    binary and its sum is an integer. We cast to int64 to avoid any
    accidental float path.
    """
    return int(np.sum(A.astype(np.int64) * B.astype(np.int64)))


def _hamming(src, dst) -> int:
    """Number of coordinates that differ between two 4D positions."""
    return int(sum(1 for a, b in zip(src, dst) if a != b))


def _king4_hd_targets(hd_set: set[int]):
    """Build a king4 target function restricted to moves whose
    source-to-target Hamming distance is in `hd_set`. Used to build
    subgraphs of the 4D king corresponding to HD-classified moves
    (HD=3 'trihedral stepper', HD=4 'tetrahedral stepper')."""
    def fn(x, y, z, w):
        src = (x, y, z, w)
        for tgt in t4.king4_targets(x, y, z, w):
            if _hamming(src, tgt) in hd_set:
                yield tgt
    return fn


@pytest.fixture(scope='module')
def adj_2d() -> dict[str, np.ndarray]:
    tgts = {
        'knight': t2.knight_targets,
        'bishop': t2.bishop_targets,
        'rook':   t2.rook_targets,
        'queen':  t2.queen_targets,
        'king':   t2.king_targets,
    }
    return {name: t2.build_adjacency(fn).astype(np.int64)
            for name, fn in tgts.items()}


@pytest.fixture(scope='module')
def adj_4d() -> dict[str, np.ndarray]:
    tgts = {
        'knight': t4.knight4_targets,
        'bishop': t4.bishop4_targets,
        'rook':   t4.rook4_targets,
        'queen':  t4.queen4_targets,
        'king':   t4.king4_targets,
    }
    out = {}
    for name, fn in tgts.items():
        A = t4.build_adjacency_4d(fn).toarray().astype(np.int64)
        out[name] = A
    return out


# ---- 2D: Z_8^2 -------------------------------------------------------

@pytest.mark.parametrize('a,b', list(combinations(DISJOINT_PIECES, 2)))
def test_2d_primitives_disjoint(adj_2d, a, b):
    """<A_a, A_b> = 0 exactly for a, b in {knight, bishop, rook}.

    The three primitive pieces have mutually-disjoint edge supports.
    """
    ip = _fro_inner(adj_2d[a], adj_2d[b])
    assert ip == 0, (
        f'2D edge-support overlap between {a} and {b}: expected 0, got {ip}'
    )


def test_2d_knight_disjoint_from_king(adj_2d):
    """Knight is edge-disjoint from king: leap vs. step are topologically
    separate. Knight is the only piece whose movement cannot be expressed
    as a sum of edge-disjoint distance-1 components."""
    ip = _fro_inner(adj_2d['knight'], adj_2d['king'])
    assert ip == 0, f'2D knight-king overlap: expected 0, got {ip}'


def test_2d_queen_contains_bishop(adj_2d):
    assert _fro_inner(adj_2d['bishop'], adj_2d['queen']) > 0


def test_2d_queen_contains_rook(adj_2d):
    assert _fro_inner(adj_2d['rook'], adj_2d['queen']) > 0


def test_2d_queen_edges_partition(adj_2d):
    """Queen = Bishop + Rook exactly, as edge sets (all distances).

    <B, Q> + <R, Q> = <Q, Q> because every queen edge is either a
    bishop edge or a rook edge, and bishop/rook edges are disjoint.
    """
    lhs = (_fro_inner(adj_2d['bishop'], adj_2d['queen'])
           + _fro_inner(adj_2d['rook'], adj_2d['queen']))
    rhs = _fro_inner(adj_2d['queen'], adj_2d['queen'])
    assert lhs == rhs, f'2D queen-edge partition failed: {lhs} != {rhs}'


def test_2d_king_edges_partition(adj_2d):
    """King = one-step Bishop + one-step Rook exactly, as edge sets.

    <B, K> + <R, K> = <K, K> because every king edge is either a
    distance-1 diagonal (bishop edge) or a distance-1 orthogonal
    (rook edge), and those two sets are disjoint.
    """
    lhs = (_fro_inner(adj_2d['bishop'], adj_2d['king'])
           + _fro_inner(adj_2d['rook'], adj_2d['king']))
    rhs = _fro_inner(adj_2d['king'], adj_2d['king'])
    assert lhs == rhs, f'2D king-edge partition failed: {lhs} != {rhs}'


# ---- 4D: Z_8^4 -------------------------------------------------------

@pytest.mark.parametrize('a,b', list(combinations(DISJOINT_PIECES, 2)))
def test_4d_primitives_disjoint(adj_4d, a, b):
    ip = _fro_inner(adj_4d[a], adj_4d[b])
    assert ip == 0, (
        f'4D edge-support overlap between {a} and {b}: expected 0, got {ip}'
    )


def test_4d_knight_disjoint_from_king(adj_4d):
    ip = _fro_inner(adj_4d['knight'], adj_4d['king'])
    assert ip == 0, f'4D knight-king overlap: expected 0, got {ip}'


def test_4d_queen_contains_bishop(adj_4d):
    assert _fro_inner(adj_4d['bishop'], adj_4d['queen']) > 0


def test_4d_queen_contains_rook(adj_4d):
    assert _fro_inner(adj_4d['rook'], adj_4d['queen']) > 0


def test_4d_queen_edges_partition(adj_4d):
    lhs = (_fro_inner(adj_4d['bishop'], adj_4d['queen'])
           + _fro_inner(adj_4d['rook'], adj_4d['queen']))
    rhs = _fro_inner(adj_4d['queen'], adj_4d['queen'])
    assert lhs == rhs, f'4D queen-edge partition failed: {lhs} != {rhs}'


def test_4d_king_strictly_contains_one_step_primitives(adj_4d):
    """In 4D the king has HD=3 and HD=4 unit-step edges that no named
    primitive covers, so bishop + rook strictly undercount king edges.
    """
    bishop_rook = (_fro_inner(adj_4d['bishop'], adj_4d['king'])
                   + _fro_inner(adj_4d['rook'], adj_4d['king']))
    king_self = _fro_inner(adj_4d['king'], adj_4d['king'])
    assert _fro_inner(adj_4d['bishop'], adj_4d['king']) > 0
    assert _fro_inner(adj_4d['rook'], adj_4d['king']) > 0
    assert bishop_rook < king_self, (
        f'4D king should strictly contain 1-step bishop + 1-step rook, '
        f'got {bishop_rook} >= {king_self}'
    )


@pytest.fixture(scope='module')
def king_hd_adj_4d() -> dict[int, np.ndarray]:
    """4D king subgraphs split by per-edge Hamming distance."""
    out = {}
    for hd in (1, 2, 3, 4):
        fn = _king4_hd_targets({hd})
        A = t4.build_adjacency_4d(fn).toarray().astype(np.int64)
        out[hd] = A
    return out


def test_4d_king_hd_partition_exact(adj_4d, king_hd_adj_4d):
    """The 4D king's edges partition exactly by Hamming distance of
    the move displacement into four classes (HD=1..4):

        <A_king, A_king> = sum_{hd=1..4} <A_king, A_king_hd>

    This is the correct generalization of the 2D king-edge partition
    to 4D. HD=1 and HD=2 subgraphs are the one-step rook and one-step
    bishop respectively; HD=3 and HD=4 are currently un-named move
    classes.
    """
    king_self = _fro_inner(adj_4d['king'], adj_4d['king'])
    parts = sum(_fro_inner(adj_4d['king'], king_hd_adj_4d[hd])
                for hd in (1, 2, 3, 4))
    assert parts == king_self, (
        f'4D king HD partition failed: sum_hd <K, K_hd> = {parts} '
        f'vs <K, K> = {king_self}'
    )


def test_4d_king_hd1_equals_one_step_rook(adj_4d, king_hd_adj_4d):
    """HD=1 king subgraph is exactly the one-step rook subgraph, so
    it agrees with the rook on the edges they share."""
    assert (_fro_inner(adj_4d['rook'], king_hd_adj_4d[1])
            == _fro_inner(king_hd_adj_4d[1], king_hd_adj_4d[1]))


def test_4d_king_hd2_equals_one_step_bishop(adj_4d, king_hd_adj_4d):
    """HD=2 king subgraph is exactly the one-step bishop subgraph."""
    assert (_fro_inner(adj_4d['bishop'], king_hd_adj_4d[2])
            == _fro_inner(king_hd_adj_4d[2], king_hd_adj_4d[2]))


def test_4d_king_hd_residual_disjoint_from_primitives(adj_4d,
                                                      king_hd_adj_4d):
    """The HD=3 and HD=4 king subgraphs (candidate 'trihedral' and
    'tetrahedral steppers') share no edges with any named primitive
    piece. This is the 4D structural gap the primitives-plus-sums
    decomposition needs future pieces to close."""
    for hd in (3, 4):
        A = king_hd_adj_4d[hd]
        for name in ('knight', 'bishop', 'rook'):
            ip = _fro_inner(A, adj_4d[name])
            assert ip == 0, (
                f'HD={hd} king residual shares edges with {name}: {ip}'
            )


if __name__ == '__main__':
    import subprocess
    subprocess.run([sys.executable, '-m', 'pytest', __file__, '-v'],
                   check=False)
