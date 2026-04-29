"""Unit tests for chess_spectral.qm_4d_dynamics — Phase 4 milestone B3b.

Covers the FA_PAWN_W / FA_PAWN_Y channel move-as-unitary lifts (the
two pawn-axis antisymmetric channels per ADR-003 §3.1 channels 8-9):

  1. Sub-unitarity within each FA_PAWN_axis subspace:
     ``U^H @ U == P_FA_PAWN_axis`` at machine precision iff the swap
     commutes with sigma_axis (the axis-flip permutation).
     Empirically: this holds iff the move is a *pure axis flip*
     (only the relevant axis coordinate changes, with
     ``axis_to == 7 - axis_from``).
  2. Antisymmetry: ``U @ psi`` lies in the axis-parity-odd subspace
     of ``C^4096`` for any input psi.
  3. ADR-001 §3.1 phase formula sanity:
     ``e^{i * (pi/2) * sgn(delta_axis)}`` with ``delta_axis`` the
     change in the relevant axis coordinate.
  4. ADR-004 §3.4 amendment compliance: U_move is NOT required to
     anti-commute with J_op (Z_2 sector flip happens at
     ``state_to_psi``, not at the operator level).
  5. FA_PAWN_W / FA_PAWN_Y isolation: each channel's lift acts on
     its own block; the two are constructed orthogonally per
     Oana & Chiru's pawn-axis tensor factorisation.
  6. Capture-move ``NotImplementedError`` (B5 deferral).
  7. Cross-parity-class behavior (xfail-strict) — explicitly
     documents the orbit-style restriction discovered for FA_PAWN.

Phase 3.5 / ADR amendments hard-coded into the spec:

  * ADR-001 §3.1 — FA_PAWN_W phase = ``(pi/2) * sgn(w' - w)``,
    FA_PAWN_Y phase = ``(pi/2) * sgn(y' - y)``.
  * ADR-003 §3.1 — strict-unitary path uses the projector-sandwich
    ``U = P @ U_swap @ P`` with ``P = (I - sigma_axis) / 2`` projecting
    onto the axis-parity-odd subspace.
  * ADR-003 amendment — orbit / parity restriction. **B3b finding: the
    restriction for FA_PAWN_axis is much narrower than B1's same-orbit
    restriction**: only "pure axis-flip" moves (``sq_to ==
    sigma_axis(sq_from)``) satisfy strict sub-unitarity. The structural
    reason is that ``sigma_axis`` has no fixed points on the integer
    lattice (``c == 7 - c`` would require non-integer ``c = 3.5``),
    so only involution-pair moves preserve ``[U_swap, sigma_axis] = 0``.
  * ADR-004 §3.4 — sector-flip-via-state_to_psi (Probe-4 amendment).
    Operator-level anti-commutation ``{U_move, J_op} = 0`` is **not**
    required.

Empirical determination of the parity / orbit condition for FA_PAWN
-------------------------------------------------------------------

The B1 milestone discovered that the projector-sandwich ``P @ swap @ P``
is sub-unitary on ``range(P)`` iff the swap commutes with P, which for
A_1 (the orbit-mean projector) holds iff ``sq_from`` and ``sq_to`` lie
in the same B_4 orbit. The orbit decomposition of ``Z_8^4`` has 35
orbits of sizes ``{16, 64, 96, 192, 384}``, so a substantial fraction
of move pairs are same-orbit.

For FA_PAWN_axis the projector is ``(I - sigma_axis) / 2`` where
sigma_axis is a single-axis order-2 permutation. The
swap-projector commutator vanishes iff:

  (a) Both ``sq_from`` and ``sq_to`` are sigma-fixed
      (``sigma(s) == s``); or
  (b) ``sigma(sq_from) == sq_to`` (the involution pair).

sigma_axis has NO fixed points on the 8-lattice (``c == 7 - c``
requires ``c = 3.5``, not an integer), so only condition (b) applies:
the move must be a "pure axis flip". This is much narrower than B1's
35-orbit dichotomy. The test surface pins this empirical finding via
xfail-strict markers on the cross-parity-class sample.

Run with ``pytest tests/test_qm_4d_dynamics_b3b.py -v`` from python/.
"""
from __future__ import annotations

import math
import os
import sys
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


# ---- Tolerances -----------------------------------------------------

TOL = 1e-10
RNG_SEED = 0xB3B_5A


# ---- Frobenius helper ----------------------------------------------


def _frob(M: sp.spmatrix | np.ndarray) -> float:
    """Frobenius norm. Works on both sparse and dense matrices."""
    if sp.issparse(M):
        return float(sp.linalg.norm(M))
    return float(np.linalg.norm(np.asarray(M)))


# ---- Position fixtures --------------------------------------------


@pytest.fixture(scope='module')
def imbalanced_position():
    """Pawn-rich position to exercise FA_PAWN_W/Y axes simultaneously.
    Pawns on both axes plus a few non-pawns for capture-detection
    fixtures.
    """
    coords = {
        # W-axis pawns
        (1, 2, 3, 4): ('P', 'w'),
        (5, 6, 7, 1): ('p', 'w'),
        # Y-axis pawns
        (0, 3, 1, 2): ('P', 'y'),
        (7, 4, 6, 5): ('p', 'y'),
        # Non-pawns for capture-detection / general moves
        (0, 0, 0, 0): 'K',
        (7, 7, 7, 7): 'k',
        (3, 3, 3, 3): 'Q',
        (4, 4, 4, 4): 'R',
    }
    return {_t4.sq4(*c): p for c, p in coords.items()}


@pytest.fixture(scope='module')
def imbalanced_position_b():
    """Second imbalanced position to vary the test sample (different
    occupancy and parity-class layout).
    """
    coords = {
        (2, 5, 1, 3): ('P', 'w'),
        (6, 0, 5, 4): ('p', 'w'),
        (4, 1, 7, 0): ('P', 'y'),
        (1, 6, 2, 6): ('p', 'y'),
        (3, 3, 3, 3): 'K', (4, 4, 4, 4): 'k',
        (0, 1, 2, 3): 'Q', (7, 6, 5, 4): 'N',
        (5, 2, 0, 6): 'B', (1, 6, 7, 0): 'R',
    }
    return {_t4.sq4(*c): p for c, p in coords.items()}


# ---- Pair generators (axis-flip vs cross-parity) -------------------


def _axis_index(axis: str) -> int:
    """Return the 4-tuple position index (0..3) for ``axis``."""
    return {'W': 3, 'Y': 1}[axis]


def _flip_axis_coord(s: int, axis: str) -> int:
    """Return ``sigma_axis(s)``: the linear index of the square whose
    relevant axis coord has been flipped (``c -> 7 - c``).
    """
    coords = list(_t4.rc4(s))
    idx = _axis_index(axis)
    coords[idx] = 7 - coords[idx]
    return _t4.sq4(*coords)


def _gen_axis_flip_pairs(
    position_keys, axis: str, *, n_pairs: int,
    rng: np.random.Generator,
) -> List[Tuple[int, int]]:
    """Generate non-capture (from, to) pairs that are *pure axis-flips*:
    ``to = sigma_axis(from)``. These are the cases where the
    projector-sandwich satisfies strict sub-unitarity.

    Strategy: pick an occupied square s; the corresponding flip target
    is ``sigma_axis(s)``. If that square is unoccupied, accept the
    pair. We also include random pure-flip pairs (not anchored to
    occupied squares) since the sub-unitarity claim is a property of
    the unitary lift itself, not of the position.
    """
    occupied = set(position_keys)
    pairs: List[Tuple[int, int]] = []
    seen = set()

    # Anchored to occupied squares first (typical chess move).
    for s in sorted(occupied):
        t = _flip_axis_coord(s, axis)
        if t == s:
            continue  # No fixed points expected, but defensive.
        if t in occupied:
            continue  # Capture — skip per non-capture scope.
        if (s, t) in seen:
            continue
        pairs.append((s, t))
        seen.add((s, t))
        if len(pairs) >= n_pairs:
            return pairs

    # Fill the remainder with random pure-flip pairs from the
    # 4096 / 2 = 2048 possible pairs.
    max_attempts = max(64, 8 * n_pairs)
    attempts = 0
    while len(pairs) < n_pairs and attempts < max_attempts:
        attempts += 1
        s = int(rng.integers(0, _t4.N_SQUARES))
        t = _flip_axis_coord(s, axis)
        if t == s:
            continue
        if s in occupied and t in occupied:
            continue  # Treat as capture; skip.
        if (s, t) in seen:
            continue
        pairs.append((s, t))
        seen.add((s, t))

    return pairs


def _gen_cross_parity_pairs(
    position_keys, axis: str, *, n_pairs: int,
    rng: np.random.Generator,
) -> List[Tuple[int, int]]:
    """Generate non-capture (from, to) pairs that are NOT pure axis-flips
    (i.e., ``to != sigma_axis(from)``). Such pairs do NOT satisfy
    ``[U_swap, sigma_axis] = 0`` and are expected to fail strict
    sub-unitarity.
    """
    occupied = set(position_keys)
    occ_list = sorted(occupied)
    pairs: List[Tuple[int, int]] = []
    seen = set()
    max_attempts = max(64, 8 * n_pairs)
    attempts = 0
    while len(pairs) < n_pairs and attempts < max_attempts:
        attempts += 1
        s = int(rng.choice(occ_list))
        t = int(rng.integers(0, _t4.N_SQUARES))
        if t == s:
            continue
        if t == _flip_axis_coord(s, axis):
            continue  # That's the pure-flip case; we want non-flip.
        if t in occupied:
            continue
        if (s, t) in seen:
            continue
        pairs.append((s, t))
        seen.add((s, t))
    return pairs


# ====================================================================
#  Test 1: Sub-unitarity within each FA_PAWN_axis subspace
# ====================================================================
#
# The user-spec says U^H U == P_FA_PAWN_axis within 1e-10. This holds
# at machine precision iff the underlying swap commutes with
# sigma_axis, which (lacking sigma fixed points on the integer
# lattice) holds iff the move is a pure axis-flip
# ``(sq_to == sigma_axis(sq_from))``.

@pytest.mark.parametrize("axis", ["W", "Y"])
def test_b3b_subunitarity_axis_flip_pure(
    axis, imbalanced_position, imbalanced_position_b,
):
    """Sub-unitarity of U_fa_pawn holds exactly for pure axis-flip
    non-capture moves on each FA_PAWN_axis (W and Y).

    For each pair: build U; compute residual =
    ``||U^H @ U - P_FA_PAWN_axis||_F``; assert below 1e-10.
    """
    P = dyn._get_p_fa_pawn(axis)
    rng = np.random.default_rng(RNG_SEED ^ (abs(hash(axis)) & 0xFFFFFFFF))

    pos_a = imbalanced_position
    pos_b = imbalanced_position_b
    pairs_a = _gen_axis_flip_pairs(
        list(pos_a.keys()), axis, n_pairs=15, rng=rng,
    )
    pairs_b = _gen_axis_flip_pairs(
        list(pos_b.keys()), axis, n_pairs=15, rng=rng,
    )
    cases = [(pos_a, p) for p in pairs_a] + [(pos_b, p) for p in pairs_b]
    assert len(cases) >= 10, (
        f"only {len(cases)} pure-axis-flip cases generated for axis "
        f"{axis!r}; expected >= 10"
    )

    residuals: List[float] = []
    for (pos, (s, t)) in cases:
        U = dyn.u_move_fa_pawn(pos, (s, t), axis=axis)
        prod = U.conj().T @ U
        diff = prod - P
        diff.eliminate_zeros()
        r = _frob(diff)
        residuals.append(r)
        assert r < TOL, (
            f"sub-unitarity residual {r:.3e} > {TOL} for pure-axis-flip "
            f"swap ({s}, {t}) on FA_PAWN_{axis}"
        )

    assert max(residuals) < TOL, (
        f"worst pure-axis-flip residual on FA_PAWN_{axis} = "
        f"{max(residuals):.3e}"
    )


@pytest.mark.parametrize("axis", ["W", "Y"])
@pytest.mark.xfail(
    strict=True,
    reason=(
        "B3b finding (parity-class restriction): U_fa_pawn^H @ "
        "U_fa_pawn == P_FA_PAWN_axis does NOT hold for cross-parity "
        "swaps (i.e., moves where sq_to != sigma_axis(sq_from)). "
        "The projector-sandwich is sub-unitary only when [U_swap, "
        "sigma_axis] = 0; sigma has no fixed points on the integer "
        "lattice, so only pure axis-flip pairs (the involution image) "
        "satisfy this. The restriction is much narrower than B1's "
        "same-orbit restriction (which spans 35 B_4 orbits of sizes "
        "16-384). Cross-parity-class moves drop to the measurement-"
        "only re-encode path per the ADR-003 amendment."
    ),
)
def test_b3b_subunitarity_cross_parity_xfail(
    axis, imbalanced_position,
):
    """Cross-parity sub-unitarity (EXPECTED FAIL).

    Documents the B3b finding that for non-axis-flip moves the
    sub-unitarity claim fails by O(1) in Frobenius norm. Marked
    xfail-strict so an unexpected pass would surface (e.g., if the
    lift is later redesigned).
    """
    P = dyn._get_p_fa_pawn(axis)
    rng = np.random.default_rng(
        RNG_SEED ^ (abs(hash(("cross", axis))) & 0xFFFFFFFF)
    )
    pairs = _gen_cross_parity_pairs(
        list(imbalanced_position.keys()), axis, n_pairs=12, rng=rng,
    )
    assert len(pairs) >= 5
    for (s, t) in pairs:
        U = dyn.u_move_fa_pawn(imbalanced_position, (s, t), axis=axis)
        prod = U.conj().T @ U
        diff = prod - P
        diff.eliminate_zeros()
        # Strict: assert tightly so the natural non-zero residual
        # converts the test to xfail-PASS via the marker.
        assert _frob(diff) < TOL


# ====================================================================
#  Test 2: Antisymmetry verification
# ====================================================================
#
# For ANY non-capture move, ``U @ psi`` lies in the axis-parity-odd
# subspace (the range of P_FA_PAWN_axis). This is structural — the
# leftmost factor in U = P @ swap @ P puts the result in range(P).
# Holds for both axis-flip and cross-parity moves (no parity-class
# restriction at the sandwich level).

@pytest.mark.parametrize("axis", ["W", "Y"])
def test_b3b_antisymmetry_after_lift(axis, imbalanced_position):
    """For any non-capture move, ``U @ psi`` is in the axis-parity-odd
    subspace: ``P @ U @ psi == U @ psi`` to machine precision.

    Verified on a mix of pure-axis-flip and cross-parity moves to
    confirm the antisymmetry property holds independent of the
    sub-unitarity dichotomy.
    """
    P = dyn._get_p_fa_pawn(axis)
    sigma = dyn._get_sigma_fa_pawn(axis)
    rng = np.random.default_rng(
        RNG_SEED ^ (abs(hash(("anti", axis))) & 0xFFFFFFFF)
    )

    flip_pairs = _gen_axis_flip_pairs(
        list(imbalanced_position.keys()), axis, n_pairs=4, rng=rng,
    )
    cross_pairs = _gen_cross_parity_pairs(
        list(imbalanced_position.keys()), axis, n_pairs=6, rng=rng,
    )
    pairs = flip_pairs + cross_pairs
    assert len(pairs) >= 6

    # Random-state probe vector
    psi = rng.standard_normal(4096) + 1j * rng.standard_normal(4096)
    psi = psi.astype(np.complex128)

    for (s, t) in pairs:
        U = dyn.u_move_fa_pawn(imbalanced_position, (s, t), axis=axis)
        # Apply U to psi
        out = U @ psi
        # P @ out should equal out (out is in range(P))
        out_after = P @ out
        residual = float(np.linalg.norm(out - out_after))
        assert residual < TOL, (
            f"U @ psi not in range(P_FA_PAWN_{axis}) for swap "
            f"({s}, {t}); ||out - P @ out|| = {residual:.3e}"
        )
        # And sigma_axis @ out = -out (axis-parity-odd characterisation)
        # since P = (I - sigma) / 2 means range(P) is the eigenspace
        # of sigma at eigenvalue -1.
        sigma_out = sigma @ out
        anti_residual = float(np.linalg.norm(sigma_out + out))
        assert anti_residual < TOL, (
            f"U @ psi not eigenvector of sigma_{axis} at -1 for swap "
            f"({s}, {t}); ||sigma @ out + out|| = {anti_residual:.3e}"
        )


# ====================================================================
#  Test 3: ADR-001 §3.1 phase formula sanity
# ====================================================================

@pytest.mark.parametrize("axis", ["W", "Y"])
def test_b3b_adr001_phase_formula(axis):
    """Phase factor matches ``e^{i * (pi/2) * sgn(delta_axis)}`` for
    each direction case (positive, zero, negative axis displacement).

    Direct check against the closed-form:

      delta_axis > 0  ->  phase = +i   (e^{i*pi/2})
      delta_axis == 0 ->  phase = 1    (e^{i*0})
      delta_axis < 0  ->  phase = -i   (e^{-i*pi/2})
    """
    coord_idx = _axis_index(axis)

    # Build representative from/to pairs that exercise each delta sign.
    # Use base coord 4 so we can go +1, -1, 0 from there for the
    # given axis; vary the OTHER axes to confirm the phase only depends
    # on the relevant axis.
    base_from = [3, 3, 3, 3]
    cases = []
    # Positive direction
    to_pos = list(base_from)
    to_pos[coord_idx] += 1
    cases.append(("delta > 0", base_from, to_pos, 1.0j))
    # Negative direction
    to_neg = list(base_from)
    to_neg[coord_idx] -= 1
    cases.append(("delta < 0", base_from, to_neg, -1.0j))
    # Zero on this axis (move along a different axis)
    to_zero = list(base_from)
    other_idx = (coord_idx + 1) % 4
    to_zero[other_idx] += 1
    cases.append(("delta == 0", base_from, to_zero, 1.0 + 0.0j))

    for label, fr, to, expected_phase in cases:
        f_idx = _t4.sq4(*fr)
        t_idx = _t4.sq4(*to)
        actual = dyn._channel_phase_fa_pawn(f_idx, t_idx, axis)
        residual = abs(actual - expected_phase)
        assert residual < 1e-12, (
            f"FA_PAWN_{axis} phase for {label} (from {fr}, to {to}): "
            f"got {actual}, expected {expected_phase}, residual "
            f"{residual:.3e}"
        )


@pytest.mark.parametrize("axis", ["W", "Y"])
def test_b3b_phase_is_axis_specific(axis):
    """The FA_PAWN_axis phase depends ONLY on the relevant axis
    coordinate; varying the other 3 axes leaves the phase unchanged.

    Regression check that we didn't accidentally pull all 4
    components into the phase formula.
    """
    coord_idx = _axis_index(axis)
    # Keep the relevant axis fixed at delta = +1; vary the others
    base_from = (1, 2, 3, 4)
    base_to = list(base_from)
    base_to[coord_idx] += 1
    f0 = _t4.sq4(*base_from)
    t0 = _t4.sq4(*base_to)
    p0 = dyn._channel_phase_fa_pawn(f0, t0, axis)

    # Vary another axis only
    for offset in (1, 2, 3):
        other = (coord_idx + offset) % 4
        new_from = list(base_from)
        new_from[other] = (new_from[other] + 1) % 8
        new_to = list(base_to)
        new_to[other] = (new_to[other] + 1) % 8
        f1 = _t4.sq4(*new_from)
        t1 = _t4.sq4(*new_to)
        p1 = dyn._channel_phase_fa_pawn(f1, t1, axis)
        assert abs(p0 - p1) < 1e-12, (
            f"FA_PAWN_{axis} phase depends on axis {other} (varied): "
            f"{p0} vs {p1}; phase should depend only on axis {coord_idx}"
        )


def test_b3b_phase_distinguishes_w_y_axes():
    """A move that has nonzero W-displacement and nonzero
    Y-displacement should produce DIFFERENT phases on FA_PAWN_W and
    FA_PAWN_Y. Confirms the per-channel phase routing is correctly
    axis-aware.
    """
    fr = (1, 2, 3, 4)
    to = (1, 5, 3, 6)  # delta_y = +3, delta_w = +2 -> both > 0
    f = _t4.sq4(*fr)
    t = _t4.sq4(*to)
    p_w = dyn._channel_phase_fa_pawn(f, t, 'W')
    p_y = dyn._channel_phase_fa_pawn(f, t, 'Y')
    # Both should be +i (delta > 0 on both axes), so they happen to
    # match for this specific move; pick another with different signs:
    fr2 = (1, 5, 3, 4)
    to2 = (1, 2, 3, 6)  # delta_y = -3 (sign -1), delta_w = +2 (sign +1)
    f2 = _t4.sq4(*fr2)
    t2 = _t4.sq4(*to2)
    p_w2 = dyn._channel_phase_fa_pawn(f2, t2, 'W')
    p_y2 = dyn._channel_phase_fa_pawn(f2, t2, 'Y')
    assert abs(p_w2 - 1.0j) < 1e-12, f"W phase = {p_w2}, expected +i"
    assert abs(p_y2 - (-1.0j)) < 1e-12, f"Y phase = {p_y2}, expected -i"
    assert abs(p_w2 - p_y2) > 1e-3, (
        f"Distinct-sign axes should give distinct phases: W={p_w2}, "
        f"Y={p_y2}"
    )


@pytest.mark.parametrize("axis", ["W", "Y"])
def test_b3b_phase_factor_reflects_in_built_unitary(
    axis, imbalanced_position,
):
    """Internal regression: the phase factor multiplies the
    sandwich; explicit comparison against the un-phased build.

    Builds U via :func:`u_move_fa_pawn` and the un-phased
    ``P @ swap @ P``; asserts the phase scaling matches.
    """
    coord_idx = _axis_index(axis)
    # Pick a move with non-zero axis displacement so the phase
    # is non-unit.
    fr = (2, 3, 4, 5)
    to = list(fr)
    to[coord_idx] = (to[coord_idx] + 1) % 8
    f = _t4.sq4(*fr)
    t = _t4.sq4(*to)
    expected_phase = dyn._channel_phase_fa_pawn(f, t, axis)
    assert abs(expected_phase - 1.0) > 0.5, (
        "test relies on a non-unit phase; revise the move geometry "
        "if this fails"
    )

    # Built unitary (with phase multiplied in)
    U_actual = dyn.u_move_fa_pawn(imbalanced_position, (f, t), axis=axis)

    # Reference: un-phased projector sandwich
    P = dyn._get_p_fa_pawn(axis)
    U_swap = dyn._build_swap_4096(f, t)
    U_unphased = (P @ U_swap @ P).tocsr()
    U_expected = (expected_phase * U_unphased).tocsr()
    diff = (U_actual - U_expected).tocsr()
    diff.eliminate_zeros()
    residual = _frob(diff)
    assert residual < 1e-12, (
        f"Phase factor mismatch on FA_PAWN_{axis} for ({fr}, {tuple(to)}): "
        f"||U_actual - phase * P @ swap @ P||_F = {residual:.3e}"
    )


# ====================================================================
#  Test 4: ADR-004 §3.4 amendment compliance
# ====================================================================
#
# The Phase 3.5 Probe-4 amendment to ADR-004 §3.4 dropped the
# operator-anti-commutation requirement. The Z_2 sector flip is at
# the state-vector level via state_to_psi's sign multiplier, NOT at
# U_move's algebraic relationship to J_op. Regression-check that
# nobody accidentally re-imposes the rejected requirement.

@pytest.mark.parametrize("axis", ["W", "Y"])
def test_b3b_no_anti_commutation_with_J_op(axis, imbalanced_position):
    """U_fa_pawn does NOT anti-commute with J_op (Phase 3.5 Probe-4
    amendment to ADR-004 §3.4).

    Builds J_op as central-inversion permutation on C^4096; computes
    ``{J_op, U_fa_pawn} = J_op @ U + U @ J_op``; asserts non-zero.
    """
    # Build J_op (central inversion)
    rows = np.empty(_t4.N_SQUARES, dtype=np.int64)
    cols = np.empty(_t4.N_SQUARES, dtype=np.int64)
    for s in range(_t4.N_SQUARES):
        x, y, z, w = _t4.rc4(s)
        rows[s] = _t4.sq4(7 - x, 7 - y, 7 - z, 7 - w)
        cols[s] = s
    data = np.ones(_t4.N_SQUARES, dtype=np.complex128)
    J_op = sp.csr_matrix(
        (data, (rows, cols)),
        shape=(_t4.N_SQUARES, _t4.N_SQUARES),
    )
    # Sanity: J_op^2 = I
    JJ = (J_op @ J_op).tocsr()
    I = sp.eye(_t4.N_SQUARES, format='csr', dtype=np.complex128)
    JJ_minus_I = (JJ - I)
    JJ_minus_I.eliminate_zeros()
    assert JJ_minus_I.nnz == 0, "J_op is not order-2"

    # Generic non-pure-axis-flip move (so the phase is non-trivial
    # and the sandwich is generic).
    move = ((1, 2, 3, 4), (1, 2, 3, 5))
    U = dyn.u_move_fa_pawn(imbalanced_position, move, axis=axis)

    AC = (U @ J_op + J_op @ U).tocsr()
    AC.eliminate_zeros()
    ac_residual = _frob(AC)
    assert ac_residual > 1e-3, (
        f"FA_PAWN_{axis} anti-commutator residual = {ac_residual:.3e}; "
        "if this is near zero, the rejected ADR-004 §3.4 requirement "
        "may have been accidentally re-imposed."
    )


# ====================================================================
#  Test 5: FA_PAWN_W / FA_PAWN_Y isolation
# ====================================================================

def test_b3b_W_and_Y_unitaries_differ(imbalanced_position):
    """For a move with nonzero W and nonzero Y displacement, the
    FA_PAWN_W and FA_PAWN_Y unitaries differ structurally.

    The two channels live on different tensor factors of the encoder
    (per Oana & Chiru); the projector-sandwich constructions use
    different sigma_axis permutations and may use different phases,
    so the resulting unitaries should not coincide.
    """
    move = ((1, 2, 3, 4), (1, 5, 3, 6))  # delta_y = +3, delta_w = +2
    U_W = dyn.u_move_fa_pawn(imbalanced_position, move, axis='W')
    U_Y = dyn.u_move_fa_pawn(imbalanced_position, move, axis='Y')
    diff = (U_W - U_Y).tocsr()
    diff.eliminate_zeros()
    assert _frob(diff) > 1e-3, (
        "FA_PAWN_W and FA_PAWN_Y unitaries identical; the sigma_W "
        "vs sigma_Y projectors should produce different sandwiches."
    )


def test_b3b_W_projector_orthogonal_to_Y_projector_difference():
    """Sanity: the W and Y axis-flip permutations differ, so their
    parity projectors differ.

    ``sigma_W`` flips the w coordinate; ``sigma_Y`` flips y.
    """
    sigma_W = dyn._get_sigma_fa_pawn('W')
    sigma_Y = dyn._get_sigma_fa_pawn('Y')
    diff = (sigma_W - sigma_Y).tocsr()
    diff.eliminate_zeros()
    assert _frob(diff) > 1.0, (
        "sigma_W and sigma_Y permutations identical; the axis "
        "selection in _build_sigma_fa_pawn is broken."
    )


@pytest.mark.parametrize("axis", ["W", "Y"])
def test_b3b_projector_properties(axis):
    """``P_FA_PAWN_axis`` is real-symmetric, idempotent, and rank
    2048 (= 4096 / 2).

    Tests the structural claim: P = (I - sigma) / 2 with sigma an
    order-2 permutation that has no fixed points on the 8-lattice.
    """
    P = dyn._get_p_fa_pawn(axis)
    # Real-symmetric (note: stored as complex128 with zero imaginary)
    diff_sym = (P - P.conj().T).tocsr()
    diff_sym.eliminate_zeros()
    assert diff_sym.nnz == 0, (
        f"P_FA_PAWN_{axis} not Hermitian: nnz of P - P^H = {diff_sym.nnz}"
    )
    # Idempotent: P @ P == P
    PP = P @ P
    diff_idem = (PP - P).tocsr()
    diff_idem.eliminate_zeros()
    assert _frob(diff_idem) < 1e-13, (
        f"P_FA_PAWN_{axis} not idempotent: ||P @ P - P||_F = "
        f"{_frob(diff_idem):.3e}"
    )
    # Rank = trace = 2048 (no sigma fixed points -> half the dimension)
    rank = float(P.diagonal().sum().real)
    assert abs(rank - 2048.0) < 1e-10, (
        f"P_FA_PAWN_{axis} trace = {rank}, expected 2048.0"
    )


# ====================================================================
#  Test 6: Capture-move handling (B5 — Option A partial-isometry)
# ====================================================================
#
# Pre-B5: ``u_move_fa_pawn(state, capture_move, axis,
# assume_non_capture=False)`` raised ``NotImplementedError``.
# Post-B5: returns the Option A re-encode marker with
# ``reason='capture-partial-isometry'`` (per ADR-003 §3.1 channels
# 8-9: the captured pawn's 8-mode block is removed by the swap, so
# ``||U @ psi|| < ||psi||``; renormalisation is folded into
# state_to_psi). Comprehensive B5 coverage in
# :mod:`tests.test_qm_4d_dynamics_b5`.

@pytest.mark.parametrize("axis", ["W", "Y"])
def test_b3b_capture_move_returns_marker_dict(
    axis, imbalanced_position,
):
    """``u_move_fa_pawn(state, capture_move, axis,
    assume_non_capture=False)`` after B5 returns a marker dict
    (partial-isometry semantics; captured pawn 8-mode block dropped)."""
    pos = imbalanced_position
    occ = sorted(pos.keys())
    assert len(occ) >= 2
    f_idx, t_idx = occ[0], occ[1]

    # Default assume_non_capture=True: build succeeds (capture not
    # checked, fast path)
    U = dyn.u_move_fa_pawn(pos, (f_idx, t_idx), axis=axis)
    assert sp.isspmatrix_csr(U) or hasattr(U, 'shape'), (
        f"non-capture-mode default should return csr_matrix"
    )
    assert U.shape == (4096, 4096)

    # B5 capture path: returns the Option A re-encode marker.
    cap_result = dyn.u_move_fa_pawn(
        pos, (f_idx, t_idx), axis=axis, assume_non_capture=False,
    )
    assert isinstance(cap_result, dict), (
        f"B5 capture path should return marker dict; got "
        f"{type(cap_result).__name__}"
    )
    assert cap_result['strict_unitary'] is False
    assert cap_result['reason'] == 'capture-partial-isometry', (
        f"FA_PAWN_{axis} capture reason should be "
        f"'capture-partial-isometry'; got {cap_result['reason']!r}"
    )
    assert cap_result['channel'] == f'FA_PAWN_{axis}'
    assert cap_result['captured_piece'] == pos[t_idx]
    assert cap_result['psi_post_block'].shape == (4096,)
    assert cap_result['psi_post_block'].dtype == np.complex128


# ====================================================================
#  Test 7: Cross-parity-class behavior (re-encoding match)
# ====================================================================
#
# This is the FA_PAWN analog of B1's
# `test_b1_re_encoding_match_cross_orbit_xfail`. For non-axis-flip
# moves, the projector-sandwich does NOT reproduce the encoder's
# post-move FA_PAWN_axis block. The cross-parity restriction is a
# narrower analog of B1's same-orbit dichotomy.
#
# This test is marked xfail-strict to pin the empirical finding.

@pytest.mark.xfail(
    strict=True,
    reason=(
        "B3b finding: the projector-sandwich does NOT reproduce the "
        "encoder's post-move FA_PAWN_axis block for cross-parity "
        "moves. The encoder's FA_PAWN_axis transformation under a "
        "move is C_axis @ swap @ C_axis^{-1} where C_axis = I (x) "
        "I (x) I (x) W_ANTI_DCT (or analogous for Y); this is a "
        "non-unitary similarity transform. The strict-unitary lift "
        "via projector-sandwich matches the encoder ONLY on "
        "axis-flip-pure pairs; otherwise cross-parity moves drop "
        "to measurement-only re-encode per the ADR-003 amendment."
    ),
)
def test_b3b_re_encoding_match_cross_parity_xfail(
    imbalanced_position,
):
    """Cross-parity re-encoding match (EXPECTED FAIL).

    Documents that for non-axis-flip moves the strict-unitary lift
    does not match the encoder's FA_PAWN_W block transformation. The
    encoder's transformation is non-unitary (C_W is not unitary —
    its singular values are 0.94, 0.94, 0.77, 0.77, 0.5, 0.5, 0.17,
    0.17 from the W_ANTI_DCT 8x8 block), so no strict-unitary lift
    can match it for general moves.
    """
    pos = imbalanced_position
    # Generate cross-parity pawn moves (delta_w = +/- 1, not the
    # involution image)
    pawn_squares = [
        s for s, v in pos.items()
        if _enc4._is_pawn(v) and _enc4._pawn_axis(v) == 'w'
    ]
    assert len(pawn_squares) >= 1
    s = pawn_squares[0]
    x, y, z, w = _t4.rc4(s)
    # Move w by +1 (which is NOT 7-w unless w=3; check)
    w_new = (w + 1) % 8
    if w_new == 7 - w:
        w_new = (w + 2) % 8
    t = _t4.sq4(x, y, z, w_new)
    if t in pos:
        # Capture; pick another
        t = _t4.sq4(x, (y + 1) % 8, z, w)

    # Apply move classically
    post = dict(pos)
    piece = post.pop(s)
    post[t] = piece

    # Encode pre and post
    enc_pre = _enc4.encode_4d(pos).astype(np.complex128)
    enc_post = _enc4.encode_4d(post).astype(np.complex128)
    n_pre = float(np.linalg.norm(enc_pre))
    n_post = float(np.linalg.norm(enc_post))
    assert n_pre > 0 and n_post > 0

    # Extract FA_PAWN_W blocks (channel 8)
    block_start = dyn.FA_PAWN_W_CHANNEL_IDX * dyn.CHANNEL_DIM
    block_end = block_start + dyn.CHANNEL_DIM
    psi_W_pre = enc_pre[block_start:block_end] / n_pre
    psi_W_post = enc_post[block_start:block_end] / n_post

    # Apply unitary
    U = dyn.u_move_fa_pawn(pos, (s, t), axis='W')
    psi_W_via = U @ psi_W_pre

    diff = float(np.linalg.norm(psi_W_via - psi_W_post))
    assert diff < TOL


# ====================================================================
#  Test 8: Sigma involution and structural sanity
# ====================================================================

@pytest.mark.parametrize("axis", ["W", "Y"])
def test_b3b_sigma_is_order2_no_fixed_points(axis):
    """sigma_axis is an order-2 permutation with NO fixed points.

    Structural check: ``c == 7 - c`` requires ``c = 3.5``, which is
    not an integer in [0, 7]. Hence sigma's cycles are all
    transpositions on the 4096 squares, giving a clean 2048-pair
    structure that translates directly to the parity-odd subspace
    rank.
    """
    sigma = dyn._get_sigma_fa_pawn(axis)
    # Order 2: sigma^2 == I
    sigma_sq = (sigma @ sigma).tocsr()
    I = sp.eye(_t4.N_SQUARES, format='csr', dtype=np.complex128)
    diff = (sigma_sq - I).tocsr()
    diff.eliminate_zeros()
    assert diff.nnz == 0, (
        f"sigma_{axis}^2 != I: nnz of diff = {diff.nnz}"
    )
    # No fixed points: sigma has no entry on the diagonal
    diag_nnz = int((sigma.diagonal() != 0).sum())
    assert diag_nnz == 0, (
        f"sigma_{axis} has {diag_nnz} fixed points; expected 0"
    )


@pytest.mark.parametrize("axis", ["W", "Y"])
def test_b3b_shape_and_dtype(axis, imbalanced_position):
    """Output shape and dtype invariants."""
    move = ((1, 2, 3, 4), (1, 2, 3, 5))
    U = dyn.u_move_fa_pawn(imbalanced_position, move, axis=axis)
    assert U.shape == (4096, 4096)
    assert U.dtype == np.complex128
    assert sp.isspmatrix_csr(U)


# ====================================================================
#  Test 9: Input validation
# ====================================================================

def test_b3b_invalid_axis_raises(imbalanced_position):
    """``axis`` other than 'W' or 'Y' raises ValueError."""
    move = ((1, 2, 3, 4), (1, 2, 3, 5))
    with pytest.raises(ValueError, match="FA_PAWN axis"):
        dyn.u_move_fa_pawn(imbalanced_position, move, axis='X')
    with pytest.raises(ValueError, match="FA_PAWN axis"):
        dyn.u_move_fa_pawn(imbalanced_position, move, axis='Z')


@pytest.mark.parametrize("axis", ["W", "Y"])
def test_b3b_move_accepts_tuple_and_int_endpoints(axis, imbalanced_position):
    """Both 4-tuple coords and linear int indices are accepted."""
    move_tuple = ((1, 2, 3, 4), (1, 2, 3, 5))
    move_int = (_t4.sq4(1, 2, 3, 4), _t4.sq4(1, 2, 3, 5))
    U_tuple = dyn.u_move_fa_pawn(imbalanced_position, move_tuple, axis=axis)
    U_int = dyn.u_move_fa_pawn(imbalanced_position, move_int, axis=axis)
    diff = (U_tuple - U_int).tocsr()
    diff.eliminate_zeros()
    assert _frob(diff) < 1e-15


# ====================================================================
#  Test 10: Bridge integration
# ====================================================================

def test_b3b_apply_move_qm_includes_pawn_channels(imbalanced_position):
    """After B3d/e the bridge returns the assembled dict including
    A_1 + FA_PAWN_W + FA_PAWN_Y entries.

    Verifies the bridge wires in the FA_PAWN builders correctly. The
    test inspects the returned dict to confirm both FA_PAWN axes are
    populated as csr_matrix entries (the projector-sandwich is built
    unconditionally for non-captures regardless of axis-flip status).
    """
    move = ((1, 2, 3, 4), (1, 2, 3, 5))
    result = dyn.apply_move_qm(imbalanced_position, move)
    # B3d/e contract: bridge returns the assembled dict directly.
    assert isinstance(result, dict), (
        f"apply_move_qm should return a dict; got {type(result).__name__}"
    )
    # FA_PAWN_W/Y entries should be csr_matrix (the projector-sandwich
    # is built for all non-capture moves; cross-parity-class doesn't
    # short-circuit to a marker like cross-orbit does for STD4).
    for axis in ('W', 'Y'):
        key = f'FA_PAWN_{axis}'
        assert key in result, (
            f"FA_PAWN_{axis} missing from bridge dict; got keys "
            f"{sorted(result.keys())}"
        )
        val = result[key]
        assert sp.isspmatrix_csr(val), (
            f"FA_PAWN_{axis} should be csr_matrix; got "
            f"{type(val).__name__}"
        )
    # A_1 should also be present and csr_matrix.
    assert 'A1' in result
    assert sp.isspmatrix_csr(result['A1'])


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
