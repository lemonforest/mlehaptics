"""Unit tests for chess_spectral.qm_4d_dynamics — Phase 4 milestone B3c.

Covers the FIB_SYM_1 / FIB_SYM_2 / FIB_SYM_3 channel move handling via
the **measurement-only re-encode** fallback path (Phase 3.5 amendment
to ADR-003 §3.3).

Per Phase 3.5 Probe 2 findings (track_b_linearization_quality_probe),
the bilinear FIB encoder formula's "best-effort linearization" path
fails the ε ≤ 0.10 acceptance gate by 50-500×:

  | Channel    | Acceptance gate | Probe 2 p95 | Outcome           |
  |------------|-----------------|-------------|-------------------|
  | FIB_SYM_1  | ε ≤ 0.10        | 5.64        | ❌ FAIL by ~56×   |
  | FIB_SYM_2  | ε ≤ 0.10        | 6.82        | ❌ FAIL by ~68×   |
  | FIB_SYM_3  | ε ≤ 0.10        | 46.76       | ❌ FAIL by ~468×  |

The structural reason: the channel value at ``s in adj(k)`` is
``gradient(k) * fib_d[piece(k), k, c-5]`` where ``gradient(k) =
sum_{n in adj(k)} sig[n]``. A move is non-smooth in ``delta_sig``
(occupancy change at origin and destination is piecewise) so no
Jacobian J_c can capture origin-to-destination piece migration.

Per the amendment, B3c ships under ADR-003 §3.3's measurement-only
re-encode fallback: apply the move classically, re-encode the post-
move position, and project channel-wise. This is honest within the
QM formalism (a measurement-then-evolution sequence consistent with
ADR-002's Zeno semantics).

**Structurally distinct from B1/B3a/B3b**:
  - B1/B3a/B3b return a sparse 4096x4096 matrix ``U_chan`` such that
    ``U_chan @ psi_pre[chan_block] approx psi_post[chan_block]``.
  - B3c returns a marker dict carrying ``psi_post_block`` (a 4096-dim
    complex128 vector) directly. No matrix; no projector sandwich.

Tests cover:
  1. Output type and shape: marker dict with the right keys; the
     ``psi_post_block`` is a complex128 4096-dim ndarray.
  2. Correctness: ``psi_post_block == state_to_psi(pos_post)
     [FIB_SYM_<idx>_block]`` exactly (1e-12 — should match within
     float-rounding because both go through the same encoder).
  3. Marker dict consistency: all required keys present with the
     expected values (strict_unitary=False, reason='measurement-only',
     channel name correct, sq_from / sq_to match the move endpoints).
  4. Captures raise NotImplementedError pointing at B5 (same pattern
     as B1/B3a/B3b).
  5. Independence from pre-move ψ: two different starting positions
     that yield the same post-move position produce identical
     ``psi_post_block`` outputs. This is the structural marker of
     "measurement" in the QM formalism.
  6. Three FIB indices isolated: ``fib_idx=1`` returns the FIB_SYM_1
     block, ``fib_idx=2`` returns FIB_SYM_2, ``fib_idx=3`` returns
     FIB_SYM_3. Cross-checked via state_to_psi slicing.

Run with ``pytest tests/test_qm_4d_dynamics_b3c.py -v`` from python/.
"""
from __future__ import annotations

import os
import sys
from typing import Dict, List, Tuple

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

from chess_spectral import qm_4d                  # noqa: E402
from chess_spectral import qm_4d_dynamics as dyn  # noqa: E402
from chess_spectral import tables_4d as _t4       # noqa: E402


# ---- Tolerances -----------------------------------------------------

# state_to_psi normalises the encoder output by its L2 norm; the slice
# operation is a no-op view. The comparison should be EXACT (max error
# 0.0) modulo any np.copy / dtype cast that could introduce ULP-level
# noise. We use 1e-12 as the gate per the user spec.
TOL_CORRECTNESS = 1e-12
RNG_SEED = 0xB3C_F1B


# ---- Fixtures ------------------------------------------------------


@pytest.fixture(scope='module')
def imbalanced_position() -> Dict[int, object]:
    """Position with non-zero FIB_SYM channel content. The encoder's
    FIB channels need at least one non-pawn piece (knight / bishop /
    rook / queen / king) since the FIBER_LOCAL table is indexed by
    piece type. This fixture has all five non-pawn types plus a few
    pawns to also exercise the FA_PAWN channels (used in test 6 to
    confirm the FIB blocks are isolated).
    """
    coords = {
        (0, 0, 0, 0): 'K', (7, 7, 7, 7): 'k',
        (1, 2, 3, 4): 'Q', (4, 3, 2, 1): 'q',
        (3, 1, 2, 3): 'B', (5, 6, 4, 2): 'b',
        (2, 5, 0, 1): 'N', (5, 1, 6, 7): 'n',
        (4, 4, 1, 5): 'R', (3, 5, 7, 6): 'r',
        (6, 2, 5, 0): ('P', 'w'), (1, 5, 0, 7): ('p', 'w'),
        (0, 4, 4, 4): ('P', 'y'), (7, 3, 3, 3): ('p', 'y'),
    }
    return {_t4.sq4(*c): p for c, p in coords.items()}


@pytest.fixture(scope='module')
def imbalanced_position_b() -> Dict[int, object]:
    """A second imbalanced position with different occupancy. Used in
    test 5 to construct a "two pre-states yielding the same post-
    state" scenario."""
    coords = {
        (1, 1, 1, 1): 'K', (6, 6, 6, 6): 'k',
        (2, 4, 5, 1): 'Q', (5, 3, 2, 6): 'q',
        (3, 6, 0, 4): 'B', (4, 1, 7, 3): 'b',
        (0, 3, 4, 7): 'N', (7, 4, 3, 0): 'n',
        (5, 0, 6, 2): 'R', (2, 7, 1, 5): 'r',
    }
    return {_t4.sq4(*c): p for c, p in coords.items()}


def _gen_non_capture_pairs(
    position_keys: List[int],
    *, n_pairs: int,
    rng: np.random.Generator,
) -> List[Tuple[int, int]]:
    """Generate non-capture (from, to) pairs anchored to occupied
    squares. Strategy: pick an occupied square ``s``, pick a random
    target ``t``; reject if ``t`` is occupied or ``t == s``.
    """
    occupied = set(position_keys)
    occ_list = sorted(occupied)
    pairs: List[Tuple[int, int]] = []
    seen = set()
    max_attempts = max(64, 16 * n_pairs)
    attempts = 0
    while len(pairs) < n_pairs and attempts < max_attempts:
        attempts += 1
        s = int(rng.choice(occ_list))
        t = int(rng.integers(0, _t4.N_SQUARES))
        if t == s:
            continue
        if t in occupied:
            continue  # Capture — skip per non-capture scope.
        if (s, t) in seen:
            continue
        pairs.append((s, t))
        seen.add((s, t))
    return pairs


def _post_move_position(
    pos_pre: Dict[int, object], from_idx: int, to_idx: int,
) -> Dict[int, object]:
    """Apply the move at the dict level (mirrors the function under
    test's _apply_move_to_position helper, used independently as a
    reference oracle in tests).
    """
    pos_post = dict(pos_pre)
    piece = pos_post.pop(from_idx)
    pos_post[to_idx] = piece
    return pos_post


def _channel_block(psi_full: np.ndarray, fib_idx: int) -> np.ndarray:
    """Return the FIB_SYM_<fib_idx> 4096-dim block of a 45 056-dim
    psi vector. fib_idx in {1, 2, 3} -> channel index in {5, 6, 7}.
    """
    chan_idx = 4 + fib_idx  # FIB_SYM_1 -> channel 5, etc.
    start = chan_idx * dyn.CHANNEL_DIM
    end = start + dyn.CHANNEL_DIM
    return np.asarray(psi_full[start:end], dtype=np.complex128)


# ====================================================================
#  Test 1: Output type and shape
# ====================================================================
#
# Verify the function returns a marker dict with the expected keys
# and that ``psi_post_block`` is a 4096-dim complex128 ndarray. Tested
# across all three FIB indices on a sample of (state, move) pairs.

@pytest.mark.parametrize("fib_idx", [1, 2, 3])
def test_b3c_output_type_and_shape(fib_idx, imbalanced_position):
    """Output is a marker dict with the canonical key set; the
    psi_post_block has shape (4096,) and dtype complex128.
    """
    rng = np.random.default_rng(RNG_SEED ^ fib_idx)
    pairs = _gen_non_capture_pairs(
        list(imbalanced_position.keys()), n_pairs=10, rng=rng,
    )
    assert len(pairs) >= 8, (
        f"only {len(pairs)} non-capture pairs generated for fib_idx="
        f"{fib_idx}; expected >= 8"
    )

    for (s, t) in pairs:
        result = dyn.u_move_fib_meas(
            imbalanced_position, (s, t), fib_idx=fib_idx,
        )
        # Type must be a dict (NOT a sparse / dense matrix).
        assert isinstance(result, dict), (
            f"fib_idx={fib_idx} pair ({s}, {t}): expected marker dict, "
            f"got {type(result).__name__}"
        )
        # Required keys.
        expected_keys = {
            'strict_unitary', 'reason', 'channel',
            'psi_post_block', 'sq_from', 'sq_to',
        }
        assert set(result.keys()) == expected_keys, (
            f"fib_idx={fib_idx} pair ({s}, {t}): marker dict keys "
            f"{set(result.keys())} != expected {expected_keys}"
        )
        # psi_post_block: shape (4096,), dtype complex128.
        block = result['psi_post_block']
        assert isinstance(block, np.ndarray), (
            f"psi_post_block is {type(block).__name__}, not ndarray"
        )
        assert block.shape == (4096,), (
            f"psi_post_block.shape = {block.shape}, expected (4096,)"
        )
        assert block.dtype == np.complex128, (
            f"psi_post_block.dtype = {block.dtype}, expected complex128"
        )


# ====================================================================
#  Test 2: Correctness — psi_post_block matches state_to_psi
# ====================================================================
#
# The user-spec correctness criterion: psi_post_block ==
# state_to_psi(pos_post)[FIB_SYM_<idx>_block] within 1e-12. This
# should hold EXACTLY (max error 0.0) since both paths go through
# the same encoder + L2 normalization, but we use 1e-12 as the gate
# per the user spec.

@pytest.mark.parametrize("fib_idx", [1, 2, 3])
def test_b3c_correctness_matches_state_to_psi(
    fib_idx, imbalanced_position,
):
    """psi_post_block is bit-identical to the FIB_SYM_<fib_idx> block
    of state_to_psi(pos_post, side_to_move=True).
    """
    rng = np.random.default_rng(RNG_SEED ^ (0xC0 + fib_idx))
    pairs = _gen_non_capture_pairs(
        list(imbalanced_position.keys()), n_pairs=10, rng=rng,
    )
    assert len(pairs) >= 8

    for (s, t) in pairs:
        # Apply the move at the dict level (oracle).
        pos_post = _post_move_position(imbalanced_position, s, t)
        # Compute the reference psi_post via state_to_psi.
        psi_post_full = qm_4d.state_to_psi(pos_post, True)
        expected_block = _channel_block(psi_post_full, fib_idx)
        # Call the function under test.
        result = dyn.u_move_fib_meas(
            imbalanced_position, (s, t), fib_idx=fib_idx,
        )
        actual_block = result['psi_post_block']
        # Max-abs error between actual and expected.
        max_err = float(np.max(np.abs(actual_block - expected_block)))
        assert max_err < TOL_CORRECTNESS, (
            f"fib_idx={fib_idx} pair ({s}, {t}): "
            f"max |psi_post_block - state_to_psi[block]| = {max_err:.3e}, "
            f"expected < {TOL_CORRECTNESS:.0e}"
        )


# ====================================================================
#  Test 3: Marker dict consistency
# ====================================================================
#
# Verify all marker dict fields take the expected values (in addition
# to test 1's structural shape check). Tests strict_unitary=False,
# reason='measurement-only', channel name reflects fib_idx,
# sq_from/sq_to match the input move endpoints.

@pytest.mark.parametrize("fib_idx", [1, 2, 3])
def test_b3c_marker_dict_field_values(fib_idx, imbalanced_position):
    """All marker dict fields take the canonical values per the
    user-spec marker contract.
    """
    rng = np.random.default_rng(RNG_SEED ^ (0xD0 + fib_idx))
    pairs = _gen_non_capture_pairs(
        list(imbalanced_position.keys()), n_pairs=8, rng=rng,
    )
    assert len(pairs) >= 6
    for (s, t) in pairs:
        result = dyn.u_move_fib_meas(
            imbalanced_position, (s, t), fib_idx=fib_idx,
        )
        # strict_unitary: always False (informational marker).
        assert result['strict_unitary'] is False, (
            f"strict_unitary should be False, got {result['strict_unitary']!r}"
        )
        # reason: distinguishes B3c from B3a's 'cross-orbit'.
        assert result['reason'] == 'measurement-only', (
            f"reason should be 'measurement-only', got "
            f"{result['reason']!r}"
        )
        # channel: reflects the fib_idx selection.
        assert result['channel'] == f'FIB_SYM_{fib_idx}', (
            f"channel should be 'FIB_SYM_{fib_idx}', got "
            f"{result['channel']!r}"
        )
        # sq_from / sq_to: match the input move endpoints (ints).
        assert result['sq_from'] == s, (
            f"sq_from should be {s}, got {result['sq_from']!r}"
        )
        assert result['sq_to'] == t, (
            f"sq_to should be {t}, got {result['sq_to']!r}"
        )
        assert isinstance(result['sq_from'], int), (
            f"sq_from type is {type(result['sq_from']).__name__}, "
            "expected int"
        )
        assert isinstance(result['sq_to'], int), (
            f"sq_to type is {type(result['sq_to']).__name__}, expected int"
        )


def test_b3c_marker_dict_accepts_tuple_endpoints(imbalanced_position):
    """Tuple-coord endpoints normalise to the same linear sq_from /
    sq_to integers as int endpoints. Mirrors the input-coercion
    behavior of u_move_a1 / u_move_std4 / u_move_fa_pawn.
    """
    fr_tuple = (3, 1, 2, 3)
    to_tuple = (3, 1, 2, 4)
    fr_int = _t4.sq4(*fr_tuple)
    to_int = _t4.sq4(*to_tuple)
    for fib_idx in (1, 2, 3):
        result_tuple = dyn.u_move_fib_meas(
            imbalanced_position, (fr_tuple, to_tuple), fib_idx=fib_idx,
        )
        result_int = dyn.u_move_fib_meas(
            imbalanced_position, (fr_int, to_int), fib_idx=fib_idx,
        )
        assert result_tuple['sq_from'] == fr_int
        assert result_tuple['sq_to'] == to_int
        assert result_int['sq_from'] == fr_int
        assert result_int['sq_to'] == to_int
        # Both routes must produce identical psi_post_blocks.
        diff = float(np.max(np.abs(
            result_tuple['psi_post_block'] - result_int['psi_post_block']
        )))
        assert diff < 1e-15, (
            f"fib_idx={fib_idx}: tuple vs int endpoints diverge by "
            f"{diff:.3e}"
        )


# ====================================================================
#  Test 4: Captures handled (B5 — Option A measurement-only re-encode)
# ====================================================================
#
# Pre-B5: ``u_move_fib_meas(..., assume_non_capture=False)`` raised
# NotImplementedError on captures.
# Post-B5: returns the same Option A re-encode marker as non-captures,
# but with ``reason='capture-measurement-only'`` and a
# ``captured_piece`` field. Comprehensive B5 coverage in
# :mod:`tests.test_qm_4d_dynamics_b5`.

@pytest.mark.parametrize("fib_idx", [1, 2, 3])
def test_b3c_capture_returns_marker_dict(fib_idx, imbalanced_position):
    """Capture moves with assume_non_capture=False return the Option A
    re-encode marker (capture-measurement-only)."""
    # Pick a from-square that is occupied; pick a to-square that is
    # also occupied. This is a capture per _is_capture's definition.
    occupied = sorted(imbalanced_position.keys())
    assert len(occupied) >= 2, "fixture must have >= 2 pieces for capture test"
    s = occupied[0]
    t = occupied[1]
    cap_result = dyn.u_move_fib_meas(
        imbalanced_position, (s, t),
        fib_idx=fib_idx, assume_non_capture=False,
    )
    assert isinstance(cap_result, dict), (
        f"B5 capture path should return marker dict; got "
        f"{type(cap_result).__name__}"
    )
    assert cap_result['strict_unitary'] is False
    assert cap_result['reason'] == 'capture-measurement-only', (
        f"FIB_SYM_{fib_idx} capture reason should be "
        f"'capture-measurement-only'; got {cap_result['reason']!r}"
    )
    assert cap_result['channel'] == f'FIB_SYM_{fib_idx}'
    assert cap_result['captured_piece'] == imbalanced_position[t]
    assert cap_result['psi_post_block'].shape == (4096,)
    assert cap_result['psi_post_block'].dtype == np.complex128


@pytest.mark.parametrize("fib_idx", [1, 2, 3])
def test_b3c_assume_non_capture_default_skips_check(
    fib_idx, imbalanced_position,
):
    """Default assume_non_capture=True skips the capture check, so
    even calling on a "captures" move-pair returns a marker dict
    rather than raising. (The classical apply_move at the dict level
    will overwrite the captured piece silently — the QM measurement-
    only path is honest about this: it re-encodes whatever post-move
    position results.)
    """
    occupied = sorted(imbalanced_position.keys())
    s = occupied[0]
    t = occupied[1]
    # No exception expected at default (assume_non_capture=True).
    result = dyn.u_move_fib_meas(
        imbalanced_position, (s, t), fib_idx=fib_idx,
    )
    assert isinstance(result, dict)
    assert result['psi_post_block'].shape == (4096,)


def test_b3c_invalid_fib_idx_raises_value_error(imbalanced_position):
    """fib_idx must be in {1, 2, 3}; other values raise ValueError."""
    occupied = sorted(imbalanced_position.keys())
    s = occupied[0]
    # Find a non-occupied target.
    t = next(
        sq for sq in range(_t4.N_SQUARES)
        if sq not in imbalanced_position and sq != s
    )
    for bad_idx in (0, 4, 5, -1, 7):
        with pytest.raises(ValueError) as excinfo:
            dyn.u_move_fib_meas(
                imbalanced_position, (s, t), fib_idx=bad_idx,
            )
        msg = str(excinfo.value)
        assert 'fib_idx' in msg.lower() or '1' in msg, (
            f"ValueError for fib_idx={bad_idx} should reference fib_idx "
            f"or list valid values; got: {msg}"
        )


# ====================================================================
#  Test 5: Independence from pre-move ψ
# ====================================================================
#
# Construct two distinct pre-move positions that, after applying their
# respective moves, yield the SAME post-move position. Calling
# u_move_fib_meas on each should produce identical psi_post_blocks.
# This verifies the function depends only on the post-move position
# (the structural marker of "measurement" in the QM formalism).

@pytest.mark.parametrize("fib_idx", [1, 2, 3])
def test_b3c_independence_from_pre_move_psi(fib_idx):
    """Two different pre-states that produce the same post-state
    return identical psi_post_blocks. This is the structural marker
    of "measurement-only": the output depends on the post-projection
    basis, not on the pre-projection amplitude.
    """
    # Pre-state A: piece at (3, 3, 3, 3); other pieces around.
    # Pre-state B: piece at a DIFFERENT origin square; same other pieces;
    # the move from B's origin lands the piece at the SAME destination.
    common_others = {
        _t4.sq4(0, 0, 0, 0): 'K',
        _t4.sq4(7, 7, 7, 7): 'k',
        _t4.sq4(2, 5, 0, 1): 'N',
        _t4.sq4(5, 6, 4, 2): 'b',
    }
    # Pre-state A: queen at (3, 3, 3, 3)
    pre_a = dict(common_others)
    pre_a[_t4.sq4(3, 3, 3, 3)] = 'Q'
    move_a = ((3, 3, 3, 3), (3, 3, 3, 4))

    # Pre-state B: queen at (3, 3, 3, 5)
    pre_b = dict(common_others)
    pre_b[_t4.sq4(3, 3, 3, 5)] = 'Q'
    move_b = ((3, 3, 3, 5), (3, 3, 3, 4))

    # Sanity: the post-states must coincide before we test indistinguishability.
    post_a = _post_move_position(pre_a, _t4.sq4(*move_a[0]), _t4.sq4(*move_a[1]))
    post_b = _post_move_position(pre_b, _t4.sq4(*move_b[0]), _t4.sq4(*move_b[1]))
    assert post_a == post_b, (
        "test setup error: post-states must coincide for the "
        "independence assertion to be meaningful"
    )

    res_a = dyn.u_move_fib_meas(pre_a, move_a, fib_idx=fib_idx)
    res_b = dyn.u_move_fib_meas(pre_b, move_b, fib_idx=fib_idx)

    diff = float(np.max(np.abs(
        res_a['psi_post_block'] - res_b['psi_post_block']
    )))
    assert diff < TOL_CORRECTNESS, (
        f"fib_idx={fib_idx}: identical post-states should give "
        f"identical psi_post_blocks; got max|diff|={diff:.3e}. "
        f"This indicates u_move_fib_meas depends on pre-move ψ, "
        "violating the measurement-only contract."
    )


def test_b3c_independence_with_distinct_imbalanced_positions(
    imbalanced_position, imbalanced_position_b,
):
    """Stronger version of test 5: two completely distinct pre-states
    with the same FIB_SYM block result for the same destination —
    impossible in general for distinct pre-states, but the property
    we want is that **the function doesn't accidentally use pre-move
    psi**. Verify by checking the marker dict's psi_post_block is
    EXACTLY the post-move state's encoding (already verified in
    test 2 against state_to_psi; here we double-check with two
    distinct pre-positions that share an occupied destination after
    the move).
    """
    # Find a square unoccupied in both fixtures.
    free_sq = next(
        sq for sq in range(_t4.N_SQUARES)
        if sq not in imbalanced_position
        and sq not in imbalanced_position_b
    )
    # Pick origins from each fixture that have a piece, then move it
    # to the common free square. Both produce a different post-state
    # (the rest of the position differs), so test 5's literal scenario
    # doesn't apply — but we verify each call's output independently
    # matches its own post-move state's state_to_psi block.
    occ_a = sorted(imbalanced_position.keys())[0]
    occ_b = sorted(imbalanced_position_b.keys())[0]

    for fib_idx in (1, 2, 3):
        for (pre, src) in [
            (imbalanced_position, occ_a),
            (imbalanced_position_b, occ_b),
        ]:
            result = dyn.u_move_fib_meas(
                pre, (src, free_sq), fib_idx=fib_idx,
            )
            pos_post = _post_move_position(pre, src, free_sq)
            expected = _channel_block(
                qm_4d.state_to_psi(pos_post, True), fib_idx,
            )
            diff = float(np.max(np.abs(
                result['psi_post_block'] - expected
            )))
            assert diff < TOL_CORRECTNESS, (
                f"fib_idx={fib_idx} from pre dict: max diff vs "
                f"state_to_psi(pos_post) = {diff:.3e}"
            )


# ====================================================================
#  Test 6: Three FIB indices isolated
# ====================================================================
#
# Verify that fib_idx=1/2/3 select the FIB_SYM_1 / FIB_SYM_2 /
# FIB_SYM_3 blocks respectively, and that those blocks are the right
# slices of state_to_psi. Also verify the three blocks are generally
# distinct (no accidental cross-wiring).

def test_b3c_three_fib_indices_select_distinct_blocks(imbalanced_position):
    """Calling u_move_fib_meas with fib_idx=1/2/3 returns the
    FIB_SYM_1/2/3 blocks of state_to_psi. The three blocks differ
    from each other (the encoder produces distinct content per FIB
    direction).
    """
    rng = np.random.default_rng(RNG_SEED ^ 0xE0)
    pairs = _gen_non_capture_pairs(
        list(imbalanced_position.keys()), n_pairs=5, rng=rng,
    )
    assert len(pairs) >= 4

    for (s, t) in pairs:
        # Compute reference: full state_to_psi vector once.
        pos_post = _post_move_position(imbalanced_position, s, t)
        psi_full = qm_4d.state_to_psi(pos_post, True)

        blocks_actual = {}
        for fib_idx in (1, 2, 3):
            result = dyn.u_move_fib_meas(
                imbalanced_position, (s, t), fib_idx=fib_idx,
            )
            blocks_actual[fib_idx] = result['psi_post_block']
            # Check it matches the right slice of state_to_psi.
            expected = _channel_block(psi_full, fib_idx)
            diff = float(np.max(np.abs(
                blocks_actual[fib_idx] - expected
            )))
            assert diff < TOL_CORRECTNESS, (
                f"fib_idx={fib_idx} block at pair ({s}, {t}): "
                f"max diff vs state_to_psi[FIB_SYM_{fib_idx}_block] = "
                f"{diff:.3e}"
            )

        # Pairwise distinctness: the three blocks are generally
        # distinct (no accidental cross-wiring of indices).
        for i in (1, 2, 3):
            for j in (1, 2, 3):
                if i >= j:
                    continue
                # Frobenius distance between blocks i and j; for any
                # imbalanced position the encoder's three FIB blocks
                # have different values (distinct FIBER_LOCAL[*, *, d]
                # rows). Threshold: > 1e-6 is conservative.
                cross_diff = float(np.linalg.norm(
                    blocks_actual[i] - blocks_actual[j]
                ))
                # Also handle the all-zero case (if both blocks are
                # zero, they trivially agree; the assertion would
                # fail spuriously). Skip if either block is near-zero.
                if (np.linalg.norm(blocks_actual[i]) < 1e-12
                        or np.linalg.norm(blocks_actual[j]) < 1e-12):
                    continue
                assert cross_diff > 1e-6, (
                    f"FIB_SYM_{i} and FIB_SYM_{j} blocks coincide at "
                    f"pair ({s}, {t}) (||diff||={cross_diff:.3e}); "
                    "indicates a possible cross-wiring of fib_idx -> "
                    "channel mapping."
                )


def test_b3c_fib_indices_match_encoder_layout(imbalanced_position):
    """The FIB_SYM_<fib_idx> channel name in the marker dict matches
    the encoder's CHANNELS_4D layout: FIB_SYM_1 -> offset 5*4096,
    FIB_SYM_2 -> 6*4096, FIB_SYM_3 -> 7*4096.
    """
    from chess_spectral import encoder_4d as _enc4
    expected_offsets = dict(_enc4.CHANNELS_4D)
    s = next(iter(imbalanced_position.keys()))
    # Find a non-occupied target.
    t = next(
        sq for sq in range(_t4.N_SQUARES)
        if sq not in imbalanced_position and sq != s
    )
    for fib_idx in (1, 2, 3):
        result = dyn.u_move_fib_meas(
            imbalanced_position, (s, t), fib_idx=fib_idx,
        )
        chan_name = f'FIB_SYM_{fib_idx}'
        # Encoder offset for this channel; expected start = (4 +
        # fib_idx) * CHANNEL_DIM.
        expected_start = (4 + fib_idx) * dyn.CHANNEL_DIM
        assert expected_offsets[chan_name] == expected_start, (
            f"encoder CHANNELS_4D offset for {chan_name} = "
            f"{expected_offsets[chan_name]}, expected {expected_start}"
        )
        assert result['channel'] == chan_name


# ====================================================================
#  Test 7: Bridge integration
# ====================================================================
#
# After B3c, FIB_SYM_{1,2,3} should be listed as shipped in the
# bridge stub's NotImplementedError message. Only FD_DIAG should
# remain pending.

def test_b3c_apply_move_qm_lists_fib_as_shipped(imbalanced_position):
    """After B3d/e the bridge returns the assembled per-channel dict
    rather than raising NIE. Verify FIB_SYM_1/2/3 entries are present
    as marker dicts (the measurement-only path).
    """
    move = ((3, 1, 2, 3), (3, 1, 2, 4))
    result = dyn.apply_move_qm(imbalanced_position, move)
    # B3d/e contract: bridge returns the assembled dict directly.
    assert isinstance(result, dict), (
        f"apply_move_qm should return a dict; got {type(result).__name__}"
    )
    # All three FIB_SYM entries should be present and be marker dicts
    # (the measurement-only re-encode path; never a sparse matrix).
    for fib_idx in (1, 2, 3):
        key = f'FIB_SYM_{fib_idx}'
        assert key in result, (
            f"FIB_SYM_{fib_idx} missing from bridge dict; got keys "
            f"{sorted(result.keys())}"
        )
        val = result[key]
        assert isinstance(val, dict), (
            f"FIB_SYM_{fib_idx} should be a marker dict; got "
            f"{type(val).__name__}"
        )
        assert val['reason'] == 'measurement-only', (
            f"FIB_SYM_{fib_idx} marker reason should be "
            f"'measurement-only'; got {val['reason']!r}"
        )
        assert val['channel'] == key
        assert val['psi_post_block'].shape == (4096,)
    # FD_DIAG should also be present (B3d/e shipped this milestone).
    assert 'FD_DIAG' in result


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
