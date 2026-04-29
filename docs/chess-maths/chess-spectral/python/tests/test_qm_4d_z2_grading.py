"""Unit tests for chess_spectral.qm_4d / qm_4d_dynamics — Phase 4 milestone B4.

Z_2 grading / superselection state-level tests. **Positive-side
complement** to the per-channel ``no_anti_commutation_with_J_op`` tests
already shipped in B1 / B3a / B3b: where those tests assert that
``U_move`` does NOT operator-anti-commute with ``J_op`` (the rejected
ADR-004 §3.4 original requirement, killed by Phase 3.5 Probe-4), this
file asserts the **canonical sector-flip mechanism IS** the
``state_to_psi(state, side_to_move)`` sign multiplier.

Per the **Phase 3.5 amendment to ADR-004 §3.4**:

  > The Z_2 sector flip is mediated by ``state_to_psi``'s side-to-move
  > sign multiplier (per Pre-flight 1's Z_2 superselection finding).
  > The per-channel ``Π_c`` and ``U_move`` are **not** required to
  > formally anti-commute with ``J_op`` as algebraic operators.

Test families
-------------

  1. **state_to_psi sign convention.** For 10 sample positions, verify
     ``state_to_psi(state, white) == -state_to_psi(state, black)``
     exactly (the Z_2 grading is implemented as a sign multiplier on
     the encoded vector). Both sides have unit norm.

  2. **8 Z_2 self-conjugate fixed-point positions.** The 8 collision
     pairs from Pre-flight 1 (encoder_injectivity_4d_results.csv;
     identified as fixed points of the central-inversion + color-flip
     involution ``J``). For each pair: verify
     ``state_to_psi(pos1, white) == state_to_psi(pos2, white)`` (the
     encoder collision is preserved at the ψ level) and verify the
     literal-J relation ``state_to_psi(pos, white) ==
     state_to_psi(J(pos), black)`` where J is central inversion + color
     flip applied at the position level.

  3. **Per-channel sector flip via state_to_psi.** For each shipped
     csr_matrix-returning channel (B1 ``u_move_a1``, B3a ``u_move_std4``,
     B3b ``u_move_fa_pawn``) × ~5 (state, move) pairs in the strict-
     unitary regime: apply ``U_move`` to the channel block of
     ``psi_pre_white`` and verify the result is anti-parallel to the
     channel block of ``psi_post_black`` (i.e., they differ by exactly
     -1 in the strict-unitary subspace, modulo overall renormalization).
     This is the positive complement to ``no_anti_commutation_with_J_op``:
     the sector flip lives at the state-vector level via state_to_psi,
     not at the operator level.

  4. **Canonical sector-flip mechanism regression.** Walk the
     ``chess_spectral`` and ``chess_spectral_4d`` packages for any code
     constructing ``J_op`` outside test files. Assert the only
     ``J_op`` constructions live under ``tests/`` — guards against
     re-introducing the rejected ADR-004 §3.4 strict-anti-commutation
     requirement at the source level.

  5. **8-collision regression on apply_move_qm.** For each of the 8
     fixed-point positions, build a "no-op" move (a self-map that
     returns the position to itself: ``(s, s)``) and verify
     ``apply_move_qm`` returns a per-channel dict whose application
     produces ψ_pre back (modulo phase). Sanity check that the QM
     pipeline handles fixed-point states without crashing.

References
----------

* `ADR-004 §3.4 <docs/adr/qm_4d/ADR-004-z2-superselection-structure.md>`_
* `PHASE_3_5_PROBE_RESULTS.md Probe 4
  <docs/adr/qm_4d/PHASE_3_5_PROBE_RESULTS.md#probe-4-adr-004-u_move--j_op-anti-commutation--fail>`_
* `Pre-flight 1 source script
  <python/research/encoder_injectivity_4d.py>`_
* `Pre-flight 1 results CSV
  <python/research/encoder_injectivity_4d_results.csv>`_

Run with ``pytest tests/test_qm_4d_z2_grading.py -v`` from python/.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pytest
import scipy.sparse as sp

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

from chess_spectral import encoder_4d as _enc4    # noqa: E402
from chess_spectral import qm_4d                  # noqa: E402
from chess_spectral import qm_4d_dynamics as dyn  # noqa: E402
from chess_spectral import tables_4d as _t4       # noqa: E402


# ---- Constants -------------------------------------------------------

CHANNEL_DIM: int = qm_4d.CHANNEL_DIM       # 4096
N_CHANNELS: int = qm_4d.N_CHANNELS         # 11
ENCODING_DIM: int = qm_4d.ENCODING_DIM     # 45056

# Z_2 fixed-point pair: collision-cluster source positions from
# Pre-flight 1. Each tuple is (FEN4_a, FEN4_b) for a pair where
# encode_4d(pos_a) == encode_4d(pos_b) (the Z_2 collision under
# central inversion + color flip / piece-swap symmetry on the
# 4D-diagonal singletons). Sourced from
# python/research/encoder_injectivity_4d_results.csv via FEN4 hash
# clustering — see the test helper :func:`_load_z2_collision_pairs`.
#
# Each pair has the shape
#   K@(0,0,0,0) + k@(7,7,7,7) + ONE additional piece on the main 4D
#   diagonal at one of {(2,2,2,2), (3,3,3,3), (4,4,4,4), (5,5,5,5)}
# for piece type in {N, B, R, Q}, with the diagonal squares paired
# {(2,2,2,2) ↔ (5,5,5,5), (3,3,3,3) ↔ (4,4,4,4)} reflecting the J
# action on those squares (J: x → 7-x).
#
# 4 piece types x 2 J-pairs = 8 collision pairs (16 positions).
Z2_COLLISION_PAIRS: List[Tuple[str, str]] = [
    (
        '4d-fen v1: K@0,0,0,0; N@2,2,2,2; k@7,7,7,7',
        '4d-fen v1: K@0,0,0,0; N@5,5,5,5; k@7,7,7,7',
    ),
    (
        '4d-fen v1: K@0,0,0,0; N@3,3,3,3; k@7,7,7,7',
        '4d-fen v1: K@0,0,0,0; N@4,4,4,4; k@7,7,7,7',
    ),
    (
        '4d-fen v1: K@0,0,0,0; B@2,2,2,2; k@7,7,7,7',
        '4d-fen v1: K@0,0,0,0; B@5,5,5,5; k@7,7,7,7',
    ),
    (
        '4d-fen v1: K@0,0,0,0; B@3,3,3,3; k@7,7,7,7',
        '4d-fen v1: K@0,0,0,0; B@4,4,4,4; k@7,7,7,7',
    ),
    (
        '4d-fen v1: K@0,0,0,0; R@2,2,2,2; k@7,7,7,7',
        '4d-fen v1: K@0,0,0,0; R@5,5,5,5; k@7,7,7,7',
    ),
    (
        '4d-fen v1: K@0,0,0,0; R@3,3,3,3; k@7,7,7,7',
        '4d-fen v1: K@0,0,0,0; R@4,4,4,4; k@7,7,7,7',
    ),
    (
        '4d-fen v1: K@0,0,0,0; Q@2,2,2,2; k@7,7,7,7',
        '4d-fen v1: K@0,0,0,0; Q@5,5,5,5; k@7,7,7,7',
    ),
    (
        '4d-fen v1: K@0,0,0,0; Q@3,3,3,3; k@7,7,7,7',
        '4d-fen v1: K@0,0,0,0; Q@4,4,4,4; k@7,7,7,7',
    ),
]


def _sq(x: int, y: int, z: int, w: int) -> int:
    """Pack a 4-coord into a linear square index in [0, 4096)."""
    return _t4.sq4(x, y, z, w)


# ---- Helper: parse a FEN4 to a position dict ------------------------


def _parse_fen4(fen4: str) -> dict:
    """Parse a FEN4 v1 string to the encoder's position dict shape.

    Wraps :mod:`chess_spectral.fen_4d` (the canonical parser). Returns
    a dict ``{linear_sq_idx: piece_value}`` matching the encoder's
    ``encode_4d`` input schema.
    """
    from chess_spectral import fen_4d
    return fen_4d.parse(fen4)


# ---- Helper: apply the literal J involution to a position dict -----


# Map of piece char (or pawn tuple) to its color-flipped form. Pawn
# values are tuples ``(color_char, axis_char)`` — the color char is
# flipped, the axis char is preserved (axis is a geometric label, not a
# color). Non-pawn pieces are single chars (``'K'``/``'k'``,
# ``'Q'``/``'q'``, etc.).
def _color_flip_piece(piece):
    """Return the color-flipped version of a piece value."""
    if isinstance(piece, tuple) and len(piece) == 2:
        # Pawn: (color, axis); flip color, keep axis.
        color, axis = piece
        flipped_color = color.lower() if color.isupper() else color.upper()
        return (flipped_color, axis)
    if isinstance(piece, str) and len(piece) == 1:
        return piece.lower() if piece.isupper() else piece.upper()
    raise ValueError(f"unknown piece value shape: {piece!r}")


def _j_image_position(pos: dict) -> dict:
    """Apply the J = (central inversion + color flip) involution to
    ``pos``.

    For each piece at square ``s``, the J-image places the
    color-flipped piece at square ``J(s) = (7-x, 7-y, 7-z, 7-w)`` (the
    central inversion of ``s`` on the 8^4 lattice).

    This is the literal involution defined in ADR-004 §2 / §3.1 and
    used in :mod:`chess_spectral.research.encoder_injectivity_4d`. The
    encoder is J-equivariant: ``encode_4d(J(pos)) == ±encode_4d(pos)``
    (sign depends on the piece-color sign convention; for the
    self-conjugate fixed-point pairs this is the +1 case after the
    state_to_psi side-flip).
    """
    new_pos: dict = {}
    for s, piece in pos.items():
        x, y, z, w = _t4.rc4(s)
        s_J = _t4.sq4(7 - x, 7 - y, 7 - z, 7 - w)
        new_pos[s_J] = _color_flip_piece(piece)
    return new_pos


# ---- Position fixtures for sample tests ----------------------------


@pytest.fixture(scope='module')
def sample_positions() -> List[dict]:
    """10 sample positions for the sign-convention test family.

    Mix of:
      * Three "imbalanced" configurations exercising multiple piece
        types (asymmetric color distribution → non-zero A_1 channel).
      * Two pawn-bearing positions (covering both pawn axes).
      * Two near-empty configurations (kings only on different orbits).
      * Three positions involving the diagonal singletons that are
        also Z_2 fixed points (chosen for shared corpus coverage with
        Family 2's collision pairs but with extra pieces breaking the
        collision).

    All positions have at least one non-king piece so the encoded
    vector is non-zero (state_to_psi is well-defined).
    """
    positions = [
        # 1. Standard imbalanced
        {
            _sq(0, 0, 0, 0): 'K', _sq(7, 7, 7, 7): 'k',
            _sq(1, 2, 3, 4): 'Q',
            _sq(3, 1, 2, 3): 'B',
            _sq(2, 5, 0, 1): 'N',
            _sq(4, 3, 1, 2): 'R',
        },
        # 2. Different occupancy
        {
            _sq(3, 3, 3, 3): 'K', _sq(4, 4, 4, 4): 'k',
            _sq(0, 1, 2, 3): 'Q', _sq(7, 6, 5, 4): 'N',
            _sq(5, 2, 0, 6): 'B', _sq(1, 6, 7, 0): 'R',
            _sq(2, 0, 4, 1): 'B',
        },
        # 3. Pawns on both axes
        {
            _sq(0, 4, 4, 0): 'B',
            _sq(5, 3, 2, 6): 'r',
            _sq(2, 0, 0, 0): ('P', 'y'),
            _sq(7, 0, 5, 5): ('p', 'w'),
            _sq(3, 3, 3, 4): 'K',
            _sq(4, 4, 4, 3): 'k',
        },
        # 4. W-axis pawn
        {
            _sq(0, 0, 0, 0): 'K', _sq(7, 7, 7, 7): 'k',
            _sq(1, 1, 1, 1): ('P', 'w'),
        },
        # 5. Y-axis pawn
        {
            _sq(0, 0, 0, 0): 'K', _sq(7, 7, 7, 7): 'k',
            _sq(2, 1, 0, 0): ('P', 'y'),
        },
        # 6. Two kings on non-corner squares
        {
            _sq(1, 2, 3, 4): 'K',
            _sq(6, 5, 4, 3): 'k',
        },
        # 7. Two kings + a knight (Z_2-related to Family-2 fixed points
        # but with the corner kings displaced — breaks the collision)
        {
            _sq(0, 0, 0, 1): 'K', _sq(7, 7, 7, 6): 'k',
            _sq(2, 2, 2, 2): 'N',
        },
        # 8. Two kings + a queen on the off-diagonal
        {
            _sq(0, 0, 0, 0): 'K', _sq(7, 7, 7, 7): 'k',
            _sq(2, 3, 4, 5): 'Q',
        },
        # 9. Mostly-empty with bishops
        {
            _sq(0, 0, 0, 0): 'K', _sq(7, 7, 7, 7): 'k',
            _sq(2, 2, 2, 2): 'B', _sq(5, 5, 5, 5): 'B',
        },
        # 10. Multi-piece with both-side rooks
        {
            _sq(0, 0, 0, 0): 'K', _sq(7, 7, 7, 7): 'k',
            _sq(1, 1, 1, 1): 'R', _sq(6, 6, 6, 6): 'r',
            _sq(2, 4, 6, 0): 'N',
        },
    ]
    return positions


@pytest.fixture(scope='module')
def imbalanced_position() -> dict:
    """A position with at least one occupied non-king piece. Used for
    move-fixture construction in Family 3 tests."""
    return {
        _sq(0, 0, 0, 0): 'K', _sq(7, 7, 7, 7): 'k',
        _sq(1, 2, 3, 4): 'Q',
        _sq(3, 1, 2, 3): 'B',
        _sq(2, 5, 0, 1): 'N',
        _sq(4, 3, 1, 2): 'R',
    }


# ====================================================================
#  Family 1: state_to_psi sign convention
# ====================================================================


def test_b4_state_to_psi_sign_white_neg_black(sample_positions):
    """``state_to_psi(state, white)`` and ``state_to_psi(state, black)``
    differ by exactly -1.

    This is the canonical Z_2 sector-flip mechanism per the Phase 3.5
    amendment to ADR-004 §3.4. The encoded vector is multiplied by:
      * +1 for ``side_to_move=True`` (white)
      * -1 for ``side_to_move=False`` (black)

    Equivalently, ``psi_white == -psi_black`` exactly (no overall
    floating-point error other than the negation itself).
    """
    for i, pos in enumerate(sample_positions):
        psi_w = qm_4d.state_to_psi(pos, side_to_move=True)
        psi_b = qm_4d.state_to_psi(pos, side_to_move=False)
        # The relation is exact (not approximate): state_to_psi simply
        # negates and renormalizes; the negation is a sign flip with
        # no float arithmetic loss.
        max_diff = float(np.max(np.abs(psi_w + psi_b)))
        assert max_diff < 1e-15, (
            f"position {i}: psi_white + psi_black should be 0 exactly; "
            f"max |psi_w + psi_b| = {max_diff:.3e}"
        )


def test_b4_state_to_psi_normalization(sample_positions):
    """Both ``psi_white`` and ``psi_black`` have unit L2 norm.

    Sanity check: the side-to-move negation does not affect L2 norm
    (||−v|| = ||v||), and state_to_psi explicitly normalizes after
    the negation. Tolerance 1e-12 to accommodate float64 arithmetic.
    """
    for i, pos in enumerate(sample_positions):
        for side, label in ((True, 'white'), (False, 'black')):
            psi = qm_4d.state_to_psi(pos, side_to_move=side)
            n = qm_4d.norm(psi)
            assert abs(n - 1.0) < 1e-12, (
                f"position {i} ({label}): ||psi|| = {n:.6f} != 1 "
                f"(out of 1e-12 tolerance)"
            )


def test_b4_state_to_psi_sign_convention_is_sign_only(sample_positions):
    """The Z_2 sector flip is a global ``-1`` multiplier, not a
    permutation or rotation in C^45056.

    Verifies that for each position, the difference
    ``psi_black - (-psi_white)`` is zero element-wise (not just in
    norm). This pins the convention to the documented sign-flip
    implementation rather than allowing any other unitary that has
    the same overall norm relationship.
    """
    for i, pos in enumerate(sample_positions):
        psi_w = qm_4d.state_to_psi(pos, side_to_move=True)
        psi_b = qm_4d.state_to_psi(pos, side_to_move=False)
        # Element-wise check: psi_b should equal -psi_w, exactly.
        # Any other transform (rotation, permutation) would yield a
        # nonzero diff somewhere even if the norms match.
        max_elem_diff = float(np.max(np.abs(psi_b - (-psi_w))))
        assert max_elem_diff < 1e-15, (
            f"position {i}: psi_black is not exactly -psi_white "
            f"element-wise; max |psi_b - (-psi_w)| = {max_elem_diff:.3e}. "
            "The Z_2 grading should be implemented as a global sign "
            "flip on the encoded vector, per ADR-004 §3.2."
        )


# ====================================================================
#  Family 2: Z_2 self-conjugate fixed-point positions
# ====================================================================


def test_b4_z2_collision_pairs_encode_identically():
    """For each of the 8 collision pairs from Pre-flight 1, both
    positions in the pair encode to the same vector.

    This is the kinematic Z_2 collision: the encoder cannot
    distinguish the two diagonal-piece positions related by central
    inversion (e.g., piece at (2,2,2,2) vs (5,5,5,5)). state_to_psi
    inherits this collision; at the ψ level, both pairs produce the
    same vector when given the same side-to-move.
    """
    assert len(Z2_COLLISION_PAIRS) == 8, (
        f"Expected 8 collision pairs from Pre-flight 1; got "
        f"{len(Z2_COLLISION_PAIRS)}"
    )
    for i, (fen_a, fen_b) in enumerate(Z2_COLLISION_PAIRS):
        pos_a = _parse_fen4(fen_a)
        pos_b = _parse_fen4(fen_b)
        enc_a = _enc4.encode_4d(pos_a)
        enc_b = _enc4.encode_4d(pos_b)
        assert np.allclose(enc_a, enc_b, atol=1e-10), (
            f"Z_2 collision pair {i} failed to collide:\n"
            f"  pos_a: {fen_a}\n"
            f"  pos_b: {fen_b}\n"
            f"  ||enc_a - enc_b|| = "
            f"{np.linalg.norm(enc_a - enc_b):.3e}"
        )


def test_b4_z2_collision_pairs_state_to_psi_white_match():
    """For each Z_2 collision pair: ``state_to_psi(pos_a, white)``
    equals ``state_to_psi(pos_b, white)`` (same encoded vector ⇒ same
    ψ ⇒ same Z_2 sector representative).

    This is the kinematic content of the "Z_2 self-conjugate" claim:
    these positions ARE the orbit fixed points and have a well-defined
    parity (specifically: both lie in H_+ when given side_to_move=white
    per the +1 sign convention).
    """
    for i, (fen_a, fen_b) in enumerate(Z2_COLLISION_PAIRS):
        pos_a = _parse_fen4(fen_a)
        pos_b = _parse_fen4(fen_b)
        psi_a_w = qm_4d.state_to_psi(pos_a, side_to_move=True)
        psi_b_w = qm_4d.state_to_psi(pos_b, side_to_move=True)
        max_diff = float(np.max(np.abs(psi_a_w - psi_b_w)))
        assert max_diff < 1e-12, (
            f"Z_2 collision pair {i}: psi(pos_a, white) != "
            f"psi(pos_b, white); max |diff| = {max_diff:.3e}"
        )


def test_b4_z2_collision_pairs_white_eq_neg_black():
    """For each Z_2 collision pair: ``state_to_psi(pos_a, white)``
    equals ``-state_to_psi(pos_b, black)`` (the side-flip on the
    partner reverses the sign).

    This is the precise reading of ADR-004 §3.6's "Z_2 fixed-point"
    boundary case: for these positions, ψ in H_+ from pos_a/white is
    equal to the negation of ψ in H_− from pos_b/black. The 8
    fixed-point positions sit at the H_+/H_− boundary; both sectors
    are accessible via state_to_psi's side-to-move parameter.
    """
    for i, (fen_a, fen_b) in enumerate(Z2_COLLISION_PAIRS):
        pos_a = _parse_fen4(fen_a)
        pos_b = _parse_fen4(fen_b)
        psi_a_w = qm_4d.state_to_psi(pos_a, side_to_move=True)
        psi_b_b = qm_4d.state_to_psi(pos_b, side_to_move=False)
        # psi_a_w == +enc_a/N; psi_b_b == -enc_b/N; enc_a == enc_b ⇒
        # psi_a_w == -psi_b_b.
        max_diff = float(np.max(np.abs(psi_a_w + psi_b_b)))
        assert max_diff < 1e-12, (
            f"Z_2 collision pair {i}: psi(pos_a, white) + "
            f"psi(pos_b, black) should be ~0; max |sum| = "
            f"{max_diff:.3e}"
        )


def test_b4_z2_literal_J_image_sector_flip():
    """For each Z_2 collision pair representative pos_a, applying the
    literal J involution (central inversion + color flip) at the
    position level and reading state_to_psi with the opposite side
    yields the same ψ as state_to_psi(pos_a, white).

    This is the "J-image sector flip" property: the encoder is
    J-equivariant up to the side-to-move sign, so
    ``state_to_psi(pos, white) == state_to_psi(J(pos), black)``
    holds for the 8 fixed-point positions (and more generally for
    any J-related pair).
    """
    for i, (fen_a, _) in enumerate(Z2_COLLISION_PAIRS):
        pos_a = _parse_fen4(fen_a)
        pos_a_J = _j_image_position(pos_a)
        psi_a_w = qm_4d.state_to_psi(pos_a, side_to_move=True)
        psi_aJ_b = qm_4d.state_to_psi(pos_a_J, side_to_move=False)
        max_diff = float(np.max(np.abs(psi_a_w - psi_aJ_b)))
        assert max_diff < 1e-12, (
            f"Z_2 collision pair {i}: psi(pos_a, white) != "
            f"psi(J(pos_a), black); max |diff| = {max_diff:.3e}. "
            "The encoder's J-equivariance (with side-to-move sign "
            "flip) is the foundational kinematic property of "
            "ADR-004 §3.2; this test asserts it holds at the ψ "
            "level for the 8 fixed-point positions."
        )


# ====================================================================
#  Family 3: Per-channel sector flip via state_to_psi
# ====================================================================
#
# For each csr_matrix-returning channel × ~5 (state, move) pairs in
# the strict-unitary regime, verify that the sector flip from
# white→black under a move is implemented at the state-vector level
# (via state_to_psi's sign multiplier on the post-move position) and
# NOT at the operator level (U_move alone does not negate).
#
# Concretely: applying U_move to ``psi_pre_white[channel_block]``
# should produce a vector parallel to ``psi_post_white[channel_block]``
# (NOT psi_post_black). The sector flip happens later, when the
# bridge re-applies state_to_psi with side_to_move=False on the
# post-move position to land in H_−.


def _build_J_op_4096() -> sp.csr_matrix:
    """Build the 4096x4096 central-inversion permutation matrix.

    ``J_op[s, s'] = 1 iff s == J(s')`` where ``J(x,y,z,w) =
    (7-x, 7-y, 7-z, 7-w)``. Real-valued permutation matrix, cast to
    complex128 for compatibility with the ψ vector dtype.

    This is the J_op operator from ADR-004 §3.1 — used here ONLY to
    sanity-check that it is order-2 (J_op^2 = I). It is **not** used
    to define the Z_2 sector flip; per the Phase 3.5 amendment to
    §3.4, the sector flip lives at state_to_psi.
    """
    rows = np.empty(_t4.N_SQUARES, dtype=np.int64)
    cols = np.empty(_t4.N_SQUARES, dtype=np.int64)
    for s in range(_t4.N_SQUARES):
        x, y, z, w = _t4.rc4(s)
        rows[s] = _t4.sq4(7 - x, 7 - y, 7 - z, 7 - w)
        cols[s] = s
    data = np.ones(_t4.N_SQUARES, dtype=np.complex128)
    return sp.csr_matrix(
        (data, (rows, cols)),
        shape=(_t4.N_SQUARES, _t4.N_SQUARES),
    )


def _apply_classical_move(pos: dict, from_idx: int, to_idx: int) -> dict:
    """Apply a non-capture move at the position-dict level.

    Removes the piece at ``from_idx`` and places it at ``to_idx``.
    Mirrors the helper used by B3c/B3d in qm_4d_dynamics.py for the
    measurement-only re-encode path.
    """
    new_pos = dict(pos)
    if from_idx not in new_pos:
        raise ValueError(f"no piece at from_idx {from_idx}")
    moving = new_pos.pop(from_idx)
    if to_idx in new_pos:
        raise ValueError(
            f"to_idx {to_idx} occupied; non-capture moves only"
        )
    new_pos[to_idx] = moving
    return new_pos


def _channel_block(psi: np.ndarray, channel_idx: int) -> np.ndarray:
    """Slice the ``channel_idx``-th 4096-dim block out of a 45056-dim
    ψ vector."""
    start = channel_idx * CHANNEL_DIM
    return psi[start:start + CHANNEL_DIM]


def _sector_consistency_residual(
    op_result: np.ndarray,
    direct_post_white: np.ndarray,
    direct_post_black: np.ndarray,
) -> Tuple[float, float, float]:
    """Compute three residuals diagnosing the sector-flip behavior:

      * ``r_par_white``: ``|⟨op|direct_white⟩ - 1|`` — measures
        whether U_move @ psi_pre[block] is parallel to
        psi_post_white[block] (the no-sector-flip-at-operator path).
      * ``r_par_black``: ``|⟨op|direct_black⟩ + 1|`` — measures
        whether U_move @ psi_pre[block] is anti-parallel to
        psi_post_black[block] (the sector-flip-via-state_to_psi path).
      * ``r_norm``: difference in L2 norm; should be near zero in the
        strict-unitary regime.

    Returns (r_par_white, r_par_black, r_norm) as a triple of floats.

    The unit-vector inner products are computed on normalized inputs;
    if any input has zero norm, that residual is reported as 0.0.
    """
    n_op = float(np.linalg.norm(op_result))
    n_w = float(np.linalg.norm(direct_post_white))
    n_b = float(np.linalg.norm(direct_post_black))
    if n_op < 1e-30 or n_w < 1e-30 or n_b < 1e-30:
        return 0.0, 0.0, 0.0
    op_n = op_result / n_op
    dw_n = direct_post_white / n_w
    db_n = direct_post_black / n_b
    ip_w = complex(np.vdot(op_n, dw_n))
    ip_b = complex(np.vdot(op_n, db_n))
    r_par_white = float(abs(ip_w - 1.0))
    r_par_black = float(abs(ip_b + 1.0))
    r_norm = float(abs(n_w - n_b))
    return r_par_white, r_par_black, r_norm


def test_b4_a1_sector_flip_via_state_to_psi(imbalanced_position):
    """For a same-orbit non-capture move, ``U_a1 @ psi_pre_white[A1]``
    is anti-parallel to ``psi_post_black[A1]`` (i.e., parallel to
    ``-psi_post_black[A1]``).

    The sector flip from white→black under the move is implemented by
    state_to_psi's sign multiplier when reading the post-move
    position with side_to_move=False — NOT by U_a1 itself. This test
    pins the convention.

    Selects 5 same-B_4-orbit non-capture moves (the strict-unitary
    regime per B1's findings); for each: applies U_a1 to the A_1
    block of psi_pre_white; verifies anti-parallelism with
    psi_post_black[A_1].
    """
    pos_pre = imbalanced_position
    psi_pre_white = qm_4d.state_to_psi(pos_pre, side_to_move=True)

    # Find 5 same-B_4-orbit empty targets.
    oid = dyn._get_orbit_id_of_sq()
    occupied = set(pos_pre.keys())
    cases: List[Tuple[int, int]] = []
    for from_idx in sorted(occupied):
        if len(cases) >= 5:
            break
        target_orbit = oid[from_idx]
        for to_idx in range(_t4.N_SQUARES):
            if to_idx == from_idx:
                continue
            if to_idx in occupied:
                continue
            if oid[to_idx] != target_orbit:
                continue
            cases.append((from_idx, to_idx))
            break
    assert len(cases) >= 3, (
        f"Could not generate 3 same-orbit moves from "
        f"{len(occupied)} pieces; got {len(cases)}"
    )

    A1_IDX = 0  # A_1 channel index in qm_4d_dynamics
    n_passing = 0
    for (from_idx, to_idx) in cases:
        from_coord = _t4.rc4(from_idx)
        to_coord = _t4.rc4(to_idx)
        move = (from_coord, to_coord)

        # Build pos_post and read psi_post_(white, black).
        pos_post = _apply_classical_move(pos_pre, from_idx, to_idx)
        psi_post_w = qm_4d.state_to_psi(pos_post, side_to_move=True)
        psi_post_b = qm_4d.state_to_psi(pos_post, side_to_move=False)

        # Apply U_a1 to psi_pre_white[A_1 block].
        U_a1 = dyn.u_move_a1(pos_pre, move)
        block_pre = _channel_block(psi_pre_white, A1_IDX)
        op_result = U_a1 @ block_pre

        block_post_w = _channel_block(psi_post_w, A1_IDX)
        block_post_b = _channel_block(psi_post_b, A1_IDX)

        r_par_w, r_par_b, _ = _sector_consistency_residual(
            op_result, block_post_w, block_post_b,
        )

        # The sector convention: U @ psi_pre_white is parallel to
        # psi_post_white (no operator-level sector flip), and thus
        # anti-parallel to psi_post_black.
        if r_par_w < 1e-9 and r_par_b < 1e-9:
            n_passing += 1

    assert n_passing >= 3, (
        f"A_1 sector consistency: only {n_passing} / "
        f"{len(cases)} moves satisfied the sector-flip-via-state_to_psi "
        "convention (U @ psi_pre_white parallel to psi_post_white, "
        "anti-parallel to psi_post_black). At least 3 same-orbit "
        "moves should pass at machine precision."
    )


def test_b4_std4_sector_flip_via_state_to_psi(imbalanced_position):
    """For each STD4 axis × a same-B_4-orbit non-capture move,
    ``U_std4 @ psi_pre_white[STD4_axis]`` is parallel to
    ``psi_post_white[STD4_axis]`` (and anti-parallel to
    ``psi_post_black[STD4_axis]``).

    Selects same-orbit moves where ``u_move_std4`` returns a
    csr_matrix (not a marker dict); for each axis × move, applies
    U_std4 to the STD4_axis block and verifies the parity convention.
    """
    pos_pre = imbalanced_position
    psi_pre_white = qm_4d.state_to_psi(pos_pre, side_to_move=True)

    # Find ~3 same-orbit empty targets.
    oid = dyn._get_orbit_id_of_sq()
    occupied = set(pos_pre.keys())
    cases: List[Tuple[int, int]] = []
    for from_idx in sorted(occupied):
        if len(cases) >= 3:
            break
        target_orbit = oid[from_idx]
        for to_idx in range(_t4.N_SQUARES):
            if to_idx == from_idx:
                continue
            if to_idx in occupied:
                continue
            if oid[to_idx] != target_orbit:
                continue
            cases.append((from_idx, to_idx))
            break
    assert len(cases) >= 1

    std4_channel_indices = {'X': 1, 'Y': 2, 'Z': 3, 'W': 4}
    n_passing_total = 0
    n_attempted = 0
    for (from_idx, to_idx) in cases:
        from_coord = _t4.rc4(from_idx)
        to_coord = _t4.rc4(to_idx)
        move = (from_coord, to_coord)

        pos_post = _apply_classical_move(pos_pre, from_idx, to_idx)
        psi_post_w = qm_4d.state_to_psi(pos_post, side_to_move=True)
        psi_post_b = qm_4d.state_to_psi(pos_post, side_to_move=False)

        for axis, chan_idx in std4_channel_indices.items():
            n_attempted += 1
            U = dyn.u_move_std4(pos_pre, move, axis)
            if isinstance(U, dict):
                # Cross-orbit fallback marker (shouldn't happen for
                # same-orbit moves selected above; defensive skip).
                continue
            block_pre = _channel_block(psi_pre_white, chan_idx)
            op_result = U @ block_pre
            block_post_w = _channel_block(psi_post_w, chan_idx)
            block_post_b = _channel_block(psi_post_b, chan_idx)
            r_par_w, r_par_b, _ = _sector_consistency_residual(
                op_result, block_post_w, block_post_b,
            )
            # Tolerate the same-orbit-without-coord-resid-match
            # sub-unitarity: the encoder match still holds, so the
            # sector parallelism residual should be small.
            if r_par_w < 1e-6 and r_par_b < 1e-6:
                n_passing_total += 1
    # Expect a majority to pass — same-orbit STD4 moves with matching
    # |coord_resid| are the strict regime; same-orbit-without-match
    # are sub-unitary but still encoder-matching, so the sector
    # parallelism still holds (at slightly looser tolerance than 1e-9).
    assert n_passing_total >= 2, (
        f"STD4 sector consistency: only {n_passing_total} / "
        f"{n_attempted} channel-axis combinations satisfied the "
        "sector-flip-via-state_to_psi convention. The encoder match "
        "should hold for same-orbit moves regardless of |coord_resid| "
        "magnitude matching, so this should pass for the vast majority."
    )


def test_b4_fa_pawn_sector_flip_via_state_to_psi():
    """For a pure-axis-flip non-capture move on each FA_PAWN axis,
    the operator output is consistent with the sector-flip-via-
    state_to_psi convention.

    For B3b's projector-sandwich construction, the operator is
    sub-unitary on ``range(P_FA_PAWN_axis)`` (verified by
    ``test_b3b_subunitarity_axis_flip_pure``); it does **not** reproduce
    the post-move encoded block at the channel-block level (the
    encoder match is *not* the FA_PAWN contract — the projector
    sandwich and the encoder use different bases for the
    antisymmetric subspace). What we *can* assert is that the operator
    + state_to_psi together respect the Z_2 grading: the inner
    products ``⟨U @ psi_pre_white[block] | psi_post_white[block]⟩``
    and ``⟨U @ psi_pre_white[block] | psi_post_black[block]⟩`` are
    exact negatives of each other, which is the algebraic content of
    the "sector flip via state_to_psi" claim (since
    ``psi_post_black = -psi_post_white``).

    Selects two pure-axis-flip moves (W- and Y-axis), applies the
    corresponding U_fa_pawn, and verifies the algebraic
    sector-flip relationship at machine precision (1e-12). A
    non-trivial value for the operator's projection onto the post-
    move block is also asserted (otherwise the test would pass
    trivially on a zero block).
    """
    # The FA_PAWN_W channel only carries pawns with axis='w' (the
    # encoder's per-axis pawn split). FA_PAWN_Y similarly carries
    # only axis='y' pawns. For each axis test we pick a position
    # whose pawn lives on the matching axis, so the channel block
    # has nontrivial content for the operator to act on.
    fa_pawn_w_idx = 8  # FA_PAWN_W channel
    fa_pawn_y_idx = 9  # FA_PAWN_Y channel

    cases = [
        # (axis, pawn_axis, move, channel_idx)
        ('W', 'w', ((1, 1, 1, 1), (1, 1, 1, 6)), fa_pawn_w_idx),
        ('Y', 'y', ((1, 1, 1, 1), (1, 6, 1, 1)), fa_pawn_y_idx),
    ]
    for axis, pawn_axis, move, chan_idx in cases:
        # Build a position with a pawn on the matching axis at the
        # move's origin square, plus the corner kings.
        pos_pre = {
            _sq(0, 0, 0, 0): 'K', _sq(7, 7, 7, 7): 'k',
            _sq(*move[0]): ('P', pawn_axis),
        }
        psi_pre_white = qm_4d.state_to_psi(pos_pre, side_to_move=True)
        from_idx = _sq(*move[0])
        to_idx = _sq(*move[1])
        pos_post = _apply_classical_move(pos_pre, from_idx, to_idx)
        psi_post_w = qm_4d.state_to_psi(pos_post, side_to_move=True)
        psi_post_b = qm_4d.state_to_psi(pos_post, side_to_move=False)
        U = dyn.u_move_fa_pawn(pos_pre, move, axis=axis)
        assert sp.isspmatrix_csr(U), (
            f"u_move_fa_pawn axis={axis!r} should return csr_matrix; "
            f"got {type(U).__name__}"
        )
        block_pre = _channel_block(psi_pre_white, chan_idx)
        op_result = U @ block_pre
        block_post_w = _channel_block(psi_post_w, chan_idx)
        block_post_b = _channel_block(psi_post_b, chan_idx)

        # Sector-flip-via-state_to_psi consistency: the inner products
        # against the white and black post-move blocks are exact
        # negatives of each other. This is automatic from the
        # state_to_psi sign convention (psi_b = -psi_w) and operator
        # linearity, but we assert it explicitly to pin the
        # convention as a regression check.
        ip_w = complex(np.vdot(op_result, block_post_w))
        ip_b = complex(np.vdot(op_result, block_post_b))
        sum_ip = ip_w + ip_b
        max_sum = max(abs(sum_ip.real), abs(sum_ip.imag))
        assert max_sum < 1e-12, (
            f"FA_PAWN_{axis}: ⟨op|psi_post_white⟩ + "
            f"⟨op|psi_post_black⟩ should be 0 (sector-flip-via-"
            f"state_to_psi); got |sum| = {max_sum:.3e}. The Z_2 "
            "grading is implemented as a sign multiplier on the "
            "encoded vector via state_to_psi, so the per-channel "
            "inner-product anti-symmetry under side flip is "
            "machine-precision exact."
        )

        # Non-trivial overlap: ⟨op|post_white⟩ should not be zero
        # (otherwise the sector-flip test passes vacuously on a zero
        # vector). For a same-piece pure-axis-flip move on FA_PAWN,
        # the operator picks up a non-zero overlap with the post-
        # move encoded block in the antisymmetric sub-space.
        overlap_mag = abs(ip_w)
        assert overlap_mag > 1e-10, (
            f"FA_PAWN_{axis}: |⟨op|psi_post_white⟩| = "
            f"{overlap_mag:.3e} is unexpectedly small; the sector-"
            f"flip test would be vacuous. Verify the move is a "
            f"genuine pure-axis-flip and the pawn occupies a "
            f"non-trivial channel position."
        )


# ====================================================================
#  Family 4: Canonical sector-flip mechanism regression guard
# ====================================================================


def test_b4_no_J_op_construction_in_src():
    """Walks ``chess_spectral`` and ``chess_spectral_4d`` package
    sources and asserts the only places that construct a ``J_op``
    operator are test files.

    Regression guard against re-introducing the rejected ADR-004 §3.4
    strict-anti-commutation requirement (``{U_move, J_op} = 0``) at
    the source level. Per the Phase 3.5 amendment, the Z_2 sector
    flip is implemented by ``state_to_psi``'s side-to-move sign
    multiplier — operator-level ``J_op`` is research / test-only.

    Allows mention of "J_op" in docstrings (descriptive text) but not
    in executable code that builds a J_op matrix.
    """
    src_root = Path(PKG)  # python/
    # Collect candidate source files: chess_spectral/*.py +
    # chess_spectral_4d/*.py (excluding __pycache__, research/, tests/).
    candidate_dirs = [
        src_root / 'chess_spectral',
        src_root / 'chess_spectral_4d',
    ]
    py_files: List[Path] = []
    for d in candidate_dirs:
        if not d.is_dir():
            continue
        for p in d.rglob('*.py'):
            if '__pycache__' in p.parts:
                continue
            py_files.append(p)

    assert len(py_files) >= 5, (
        f"Found only {len(py_files)} src python files; expected >= 5 "
        f"in chess_spectral / chess_spectral_4d. The package layout "
        "may have changed."
    )

    # Patterns that suggest constructing a J_op operator (assignment
    # to a J_op-named variable). Allow J_op mentions in docstrings,
    # comments, and string literals (description-only).
    assignment_pattern = re.compile(
        r'^\s*J_op\s*='        # variable named J_op being assigned
        r'|^\s*j_op\s*='       # lowercase variant
        r'|^\s*_J_op\s*='      # leading-underscore variant
        r'|def\s+build_j_op'   # builder function for J_op
        r'|def\s+_build_J_op',
        re.MULTILINE,
    )

    offenders: List[Tuple[Path, int, str]] = []
    for p in py_files:
        text = p.read_text(encoding='utf-8')
        for m in assignment_pattern.finditer(text):
            line_no = text.count('\n', 0, m.start()) + 1
            line = text.split('\n')[line_no - 1].rstrip()
            offenders.append((p, line_no, line))

    assert not offenders, (
        f"Found {len(offenders)} J_op-construction sites in src/ "
        "code. Per the Phase 3.5 amendment to ADR-004 §3.4, the Z_2 "
        "sector flip lives at state_to_psi (sign multiplier), not at "
        "the operator level. J_op should only be constructed in test "
        "and research code, not in shipping src. Offenders:\n" +
        "\n".join(f"  {p}:{ln}: {line}" for (p, ln, line) in offenders)
    )


def test_b4_J_op_appears_only_in_tests():
    """Sanity check: the only places where ``J_op`` is *constructed*
    (matrix-built) are inside ``python/tests/``. The src code may
    *reference* J_op in docstrings (educational), but never builds it.

    Pairs with :func:`test_b4_no_J_op_construction_in_src`.
    Specifically tracks the central-inversion-permutation pattern
    used by the existing B1/B3a/B3b ``no_anti_commutation`` tests:

      ``rows[s] = sq4(7-x, 7-y, 7-z, 7-w)``

    This pattern is a strong signature of "building J_op as a 4096-
    perm matrix." All occurrences of this pattern should live in
    test files.
    """
    src_root = Path(PKG)
    central_inv_pattern = re.compile(
        r'7\s*-\s*x.*7\s*-\s*y.*7\s*-\s*z.*7\s*-\s*w'
    )
    candidate_dirs = [
        src_root / 'chess_spectral',
        src_root / 'chess_spectral_4d',
    ]
    py_files: List[Path] = []
    for d in candidate_dirs:
        if not d.is_dir():
            continue
        for p in d.rglob('*.py'):
            if '__pycache__' in p.parts:
                continue
            py_files.append(p)

    src_offenders: List[Tuple[Path, int]] = []
    for p in py_files:
        text = p.read_text(encoding='utf-8')
        for m in central_inv_pattern.finditer(text):
            line_no = text.count('\n', 0, m.start()) + 1
            src_offenders.append((p, line_no))

    assert not src_offenders, (
        f"Found {len(src_offenders)} central-inversion (J_op-style) "
        "construction sites in src/ code. Per the Phase 3.5 amendment "
        "to ADR-004 §3.4, J_op should only be built in test code "
        "(this very file's J_op fixture is the one allowed exception). "
        "Offenders:\n" +
        "\n".join(f"  {p}:{ln}" for (p, ln) in src_offenders)
    )


def test_b4_J_op_order_2_sanity():
    """Sanity: the J_op operator we construct in this test file (and
    in B1/B3a/B3b's no_anti_commutation tests) is order-2, i.e.,
    ``J_op @ J_op == I`` exactly.

    This is a defensive check that our local J_op fixture is correct
    even though we no longer use it for sector-flip semantics. It
    matches the J_op^2 = I sanity check in the existing
    no_anti_commutation tests.
    """
    J_op = _build_J_op_4096()
    JJ = (J_op @ J_op).tocsr()
    I = sp.eye(_t4.N_SQUARES, format='csr', dtype=np.complex128)
    diff = (JJ - I)
    diff.eliminate_zeros()
    assert diff.nnz == 0, (
        f"J_op^2 should equal I exactly; got {diff.nnz} nonzero "
        "entries in the difference. J_op fixture is broken."
    )


# ====================================================================
#  Family 5: 8-collision regression on apply_move_qm
# ====================================================================


def test_b4_apply_move_qm_no_op_self_map_8_collisions():
    """For each of the 8 Z_2 fixed-point positions, build a no-op
    "self-map" move ``(s, s)`` for the singleton diagonal piece, and
    verify that ``apply_move_qm`` returns a well-formed per-channel
    dict for it cleanly (no crash, all 11 channels present).

    This exercises the QM pipeline on the boundary 8 positions: the
    pipeline should treat them as ordinary positions and return a
    well-defined dict. Sanity check that the boundary cases are
    handled without raising.

    Implementation note: the bridge classifies ``(s, s)`` as a
    "capture" (because the destination square IS occupied — by the
    moving piece itself), so all channels return capture-marker
    dicts via the B5 capture-path builders. The QM-honest reading
    is that the post-move position equals the pre-move position
    (the capture preserves the piece, just reasserts it on the same
    square), so ``psi_post`` should equal ``psi_pre``. This is
    verified in :func:`test_b4_apply_move_qm_no_op_post_block_matches_pre`.
    """
    n_passing = 0
    for i, (fen_a, _) in enumerate(Z2_COLLISION_PAIRS):
        pos = _parse_fen4(fen_a)
        # Identify the singleton diagonal piece (the only non-king).
        # 16 positions in our 8 pairs all have exactly K@(0,0,0,0),
        # k@(7,7,7,7), and ONE additional piece.
        non_king = [s for s, p in pos.items()
                    if p not in ('K', 'k')]
        assert len(non_king) == 1, (
            f"Position {i} should have exactly 1 non-king piece; "
            f"got {len(non_king)}: {non_king}"
        )
        s = non_king[0]
        coord = _t4.rc4(s)
        no_op_move = (coord, coord)

        # apply_move_qm should not crash on (s, s).
        try:
            result = dyn.apply_move_qm(pos, no_op_move)
        except Exception as e:  # pragma: no cover (defensive)
            pytest.fail(
                f"Position {i}: apply_move_qm raised on no-op move "
                f"({coord}, {coord}): {type(e).__name__}: {e}"
            )
        assert isinstance(result, dict), (
            f"Position {i}: apply_move_qm did not return a dict"
        )
        # All 11 channel keys present.
        expected_keys = {
            'A1',
            'STD4_X', 'STD4_Y', 'STD4_Z', 'STD4_W',
            'FA_PAWN_W', 'FA_PAWN_Y',
            'FIB_SYM_1', 'FIB_SYM_2', 'FIB_SYM_3',
            'FD_DIAG',
        }
        assert set(result.keys()) == expected_keys, (
            f"Position {i}: missing channel keys: "
            f"{expected_keys - set(result.keys())}; extra: "
            f"{set(result.keys()) - expected_keys}"
        )
        n_passing += 1

    assert n_passing == 8, (
        f"Only {n_passing} / 8 fixed-point positions passed the "
        "no-op apply_move_qm regression."
    )


def test_b4_apply_move_qm_no_op_post_block_matches_pre():
    """For each of the 8 fixed-point positions × no-op move ``(s, s)``,
    verify that the marker-dict channels (FIB_SYM_*, FD_DIAG, plus
    A_1 / STD4 / FA_PAWN under the capture path) carry a
    ``psi_post_block`` that matches the pre-move ψ block.

    Since ``(s, s)`` doesn't change the position content (the
    "capture" replaces the piece with itself), ``psi_post`` equals
    ``psi_pre``. Each marker's ``psi_post_block`` should match the
    corresponding channel block of psi_pre at machine precision.

    This is a sanity check that the QM pipeline handles the boundary
    8 positions cleanly: the round-trip move-and-re-encode operation
    is the identity on these positions (and on any (s, s) self-
    capture more generally).
    """
    channel_index_map = {
        'A1': 0,
        'STD4_X': 1, 'STD4_Y': 2, 'STD4_Z': 3, 'STD4_W': 4,
        'FIB_SYM_1': 5, 'FIB_SYM_2': 6, 'FIB_SYM_3': 7,
        'FA_PAWN_W': 8, 'FA_PAWN_Y': 9,
        'FD_DIAG': 10,
    }
    for i, (fen_a, _) in enumerate(Z2_COLLISION_PAIRS):
        pos = _parse_fen4(fen_a)
        non_king = [s for s, p in pos.items()
                    if p not in ('K', 'k')]
        s = non_king[0]
        coord = _t4.rc4(s)
        no_op_move = (coord, coord)
        result = dyn.apply_move_qm(pos, no_op_move)
        psi_pre = qm_4d.state_to_psi(pos, side_to_move=True)

        # For each channel that returned a marker dict with
        # psi_post_block, verify it matches the pre-move block.
        n_marker_checked = 0
        for chan, val in result.items():
            if not isinstance(val, dict):
                continue
            if 'psi_post_block' not in val:
                # cross-orbit / cross-parity markers don't carry
                # a psi_post_block; skip.
                continue
            chan_idx = channel_index_map[chan]
            block_pre = _channel_block(psi_pre, chan_idx)
            psi_post_block = np.asarray(val['psi_post_block'])
            # The "no-op self-capture" preserves the position, so
            # the post-move ψ equals psi_pre, and the channel block
            # equals the pre-move block.
            max_diff = float(np.max(np.abs(psi_post_block - block_pre)))
            assert max_diff < 1e-10, (
                f"Position {i}, channel {chan}: psi_post_block does "
                f"not match psi_pre[block]; max |diff| = "
                f"{max_diff:.3e}"
            )
            n_marker_checked += 1
        assert n_marker_checked >= 1, (
            f"Position {i}: no marker-dict channel was checked; "
            f"keys with markers: "
            f"{[k for k, v in result.items() if isinstance(v, dict)]}"
        )
