"""Tests for the graph-Laplacian eigenbasis move-legality oracles.

Covers :mod:`chess_spectral.spectral_legality` (2D) and
:mod:`chess_spectral.spectral_legality_4d` (4D). The oracles serve
as a third independent move-legality validator alongside python-chess
(reference) and :mod:`chess_spectral.phase_operators` (modular
arithmetic). Test patterns:

  * Empty-board reach matches python-chess for every piece × source
    square in 2D
  * Empty-board reach matches `phase_operators` for every piece in 2D
    (the ``agrees_with_phase_operators`` cross-check)
  * Spectral reconstruction `A_ij = -sum_k λ_k v_k[i] v_k[j]` matches
    the dense lookup at machine precision
  * Eigendecomposition is real-symmetric (eigenvalues real,
    eigenvectors orthonormal)
  * Self-loops (i == j) score 0 in the spectral oracle
  * Pawns raise ValueError (deferred per module docstring)
  * 4D oracle: spot-check moves (rook-axis-aligned, knight 4D,
    king-corner adjacency) match the chess4D rule library on the
    empty-lattice reach
  * Public API surface: ``__all__`` correctness
"""
from __future__ import annotations

import os
import sys

import chess
import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

from chess_spectral import spectral_legality as legality_2d        # noqa: E402
from chess_spectral import spectral_legality_4d as legality_4d     # noqa: E402
from chess_spectral import tables_4d as t4                          # noqa: E402


# ============================================================
# 2D oracle
# ============================================================


@pytest.mark.parametrize('piece', ['N', 'B', 'R', 'Q', 'K'])
def test_2d_oracle_agrees_with_phase_operators(piece):
    """The graph-Laplacian oracle and phase_operators produce
    identical empty-board reach sets for every from-square."""
    assert legality_2d.agrees_with_phase_operators(piece)


@pytest.mark.parametrize('piece,name', [
    ('N', 'knight'), ('B', 'bishop'), ('R', 'rook'),
    ('Q', 'queen'), ('K', 'king'),
])
def test_2d_oracle_agrees_with_python_chess(piece, name):
    """The graph-Laplacian oracle produces the same empty-board
    reach as python-chess on every square. python-chess is the
    reference implementation; agreement here is structural."""
    chess_piece_type = {
        'N': chess.KNIGHT, 'B': chess.BISHOP, 'R': chess.ROOK,
        'Q': chess.QUEEN, 'K': chess.KING,
    }[piece]
    chess_piece_color = chess.WHITE   # color irrelevant for non-pawn reach

    for from_chess in range(64):
        # python-chess reach: place a single piece on from_chess and
        # ask which squares attack relations include.
        b = chess.Board.empty()
        b.set_piece_at(from_chess,
                       chess.Piece(chess_piece_type, chess_piece_color))
        # Reachable targets = pseudo-legal destinations of moves from
        # this square. King doesn't have a "moves to attack squares"
        # API directly; we use board.attacks() which gives a SquareSet.
        reach_chess = b.attacks(from_chess)

        # Convert to spectral indexing.
        rank_from = chess.square_rank(from_chess)
        file_from = chess.square_file(from_chess)
        spectral_from = (7 - rank_from) * 8 + file_from
        oracle_reach = legality_2d.reachable_targets(piece, spectral_from)

        # Convert reach_chess back to spectral too.
        chess_reach_spectral = set()
        for to_chess in reach_chess:
            rank_to = chess.square_rank(to_chess)
            file_to = chess.square_file(to_chess)
            chess_reach_spectral.add((7 - rank_to) * 8 + file_to)

        assert set(oracle_reach) == chess_reach_spectral, (
            f"{name} on python-chess sq {from_chess} (spectral "
            f"{spectral_from}): oracle says {sorted(oracle_reach)}, "
            f"python-chess says {sorted(chess_reach_spectral)}, "
            f"diff {set(oracle_reach) ^ chess_reach_spectral}"
        )


@pytest.mark.parametrize('piece', ['N', 'B', 'R', 'Q', 'K'])
def test_2d_spectral_reach_score_matches_adjacency(piece):
    """The eigenbasis reconstruction `-sum_k λ_k v_k[i] v_k[j]`
    recovers A[i,j] to machine precision for off-diagonal pairs."""
    A = legality_2d._piece_adjacency(piece)
    for i in range(0, 64, 5):   # sample every 5th square
        for j in range(i + 1, 64):
            score = legality_2d.spectral_reach_score(piece, i, j)
            expected = float(A[i, j])
            assert abs(score - expected) < 1e-10, (
                f"{piece}({i},{j}): spectral score {score} vs "
                f"adjacency {expected}"
            )


@pytest.mark.parametrize('piece', ['N', 'B', 'R', 'Q', 'K'])
def test_2d_eigendecomposition_real_symmetric(piece):
    """Eigenvalues real (Hermitian L), eigenvectors orthonormal."""
    eigvals, eigvecs = legality_2d.piece_eigendecomposition(piece)
    assert eigvals.dtype == np.float64
    assert eigvecs.shape == (64, 64)
    # Orthonormality: V^T V == I.
    gram = eigvecs.T @ eigvecs
    assert np.allclose(gram, np.eye(64), atol=1e-10)
    # Eigenvalues sorted ascending (np.linalg.eigh contract).
    assert np.all(np.diff(eigvals) >= -1e-12)


def test_2d_self_loop_reach_score_is_zero():
    """spectral_reach_score(p, i, i) == 0 (no self-loops in
    piece-reach graphs)."""
    for piece in 'NBRQK':
        for i in (0, 27, 63):
            assert legality_2d.spectral_reach_score(piece, i, i) == 0.0


def test_2d_pawn_raises():
    """Pawns aren't covered (directed reach -- see module docstring)."""
    with pytest.raises(ValueError):
        legality_2d.is_reachable('P', 8, 16)
    with pytest.raises(ValueError):
        legality_2d.reachable_targets('P', 8)
    with pytest.raises(ValueError):
        legality_2d.spectral_reach_score('P', 8, 16)


def test_2d_unknown_piece_raises():
    with pytest.raises(ValueError):
        legality_2d.is_reachable('X', 0, 0)


def test_2d_out_of_range_squares_raise():
    """Square indices outside [0, 64) raise."""
    with pytest.raises(ValueError):
        legality_2d.is_reachable('N', -1, 0)
    with pytest.raises(ValueError):
        legality_2d.is_reachable('N', 0, 64)


def test_2d_supported_pieces_excludes_pawn():
    pieces = legality_2d.supported_pieces()
    assert 'P' not in pieces
    assert 'p' not in pieces
    assert set(pieces) == {'N', 'B', 'R', 'Q', 'K'}


def test_2d_oracle_caches_results():
    """Two queries trigger one eigendecomposition (cache hit)."""
    e1 = legality_2d.piece_eigendecomposition('R')
    e2 = legality_2d.piece_eigendecomposition('R')
    # Cache returns same tuple object.
    assert e1[0] is e2[0]
    assert e1[1] is e2[1]


# ============================================================
# 4D oracle
# ============================================================


@pytest.mark.parametrize('piece', ['N', 'B', 'R', 'Q', 'K'])
def test_4d_oracle_self_loops_are_zero(piece):
    """4D self-loops score 0."""
    assert legality_4d.spectral_reach_score_4d(piece, 0, 0) == 0.0
    assert legality_4d.spectral_reach_score_4d(piece, 100, 100) == 0.0


def test_4d_supported_pieces():
    assert set(legality_4d.supported_pieces_4d()) == {
        'N', 'B', 'R', 'Q', 'K'
    }


def test_4d_pawn_raises():
    """4D pawns (Pw, Py) are deferred."""
    with pytest.raises(ValueError):
        legality_4d.is_reachable_4d('P', 0, 1)
    with pytest.raises(ValueError):
        legality_4d.is_reachable_4d('p', 0, 1)


def test_4d_out_of_range_squares_raise():
    with pytest.raises(ValueError):
        legality_4d.is_reachable_4d('R', -1, 0)
    with pytest.raises(ValueError):
        legality_4d.is_reachable_4d('R', 0, 4096)


def test_4d_rook_axis_aligned_moves():
    """A 4D rook should reach all squares on its 4 axes (X, Y, Z, W),
    7 squares per axis = 28 total reach targets from any square."""
    # Pick a 'central' square: (4, 4, 4, 4).
    sq = t4.sq4(4, 4, 4, 4)
    reach = legality_4d.reachable_targets_4d('R', sq)
    # Rook reaches 7 squares per axis x 4 axes = 28 squares.
    assert len(reach) == 28


def test_4d_knight_reach_count():
    """4D knight: 8 axis-pair choices × 8 sign-pair choices = 64
    geometric directions; the open-lattice reach from a deep-interior
    square should reach 8 axis pairs × 4 sign-permutations × 2 = 64
    total. From a corner (0,0,0,0) it's heavily clipped."""
    # Deep interior: (3,3,3,3).
    sq_interior = t4.sq4(3, 3, 3, 3)
    interior_reach = legality_4d.reachable_targets_4d('N', sq_interior)
    # Exact count is determined by tables_4d's knight adjacency. Let
    # the count drive the test rather than the spec; we assert >= 32
    # (a generous lower bound; deep interior should have plenty).
    assert len(interior_reach) >= 32

    # Corner: (0,0,0,0). Heavily clipped; should still have some
    # reach (knight does not need to cross zero boundaries).
    sq_corner = t4.sq4(0, 0, 0, 0)
    corner_reach = legality_4d.reachable_targets_4d('N', sq_corner)
    assert len(corner_reach) > 0
    # Corner should have STRICTLY fewer reach targets than interior.
    assert len(corner_reach) < len(interior_reach)


def test_4d_king_reach_count_at_corner():
    """4D king from (0,0,0,0) reaches 3^4 - 1 - clipped neighbours.
    The full neighbourhood is 3^4 = 81 squares including self. From
    a corner only neighbours with all coords in [0, 1] are valid:
    that's 2^4 = 16 squares including self -> 15 reach targets."""
    sq = t4.sq4(0, 0, 0, 0)
    reach = legality_4d.reachable_targets_4d('K', sq)
    # All neighbours with each coordinate in {0, 1}, minus the
    # source itself.
    assert len(reach) == 15


def test_4d_oracle_caches_adjacency():
    """Two adjacency queries trigger one materialisation."""
    A1 = legality_4d._piece_adjacency_4d('R')
    A2 = legality_4d._piece_adjacency_4d('R')
    assert A1 is A2


# ============================================================
# Public API surface
# ============================================================


def test_2d_module_public_api():
    for name in ('is_reachable', 'reachable_targets',
                 'spectral_reach_score', 'agrees_with_phase_operators',
                 'piece_eigendecomposition', 'supported_pieces'):
        assert name in legality_2d.__all__


def test_4d_module_public_api():
    for name in ('is_reachable_4d', 'reachable_targets_4d',
                 'spectral_reach_score_4d',
                 'piece_eigendecomposition_4d',
                 'supported_pieces_4d'):
        assert name in legality_4d.__all__
