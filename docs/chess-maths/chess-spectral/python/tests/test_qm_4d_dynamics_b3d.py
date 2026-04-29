"""Unit tests for chess_spectral.qm_4d_dynamics — Phase 4 milestone B3d/e.

Covers the FD_DIAG channel move-as-unitary lift (channel 10 — the
diagonal-deviation / rook-shadow channel per ADR-003 §3.2 channel 10).

Per ADR-003 §3.2 channel 10's derivation, FD_DIAG admits a
**rank-1 update + renormalization** construction, validated by Phase
3.5 Probe 2 (cond p95 = 8.60 vs the 100 acceptance gate — well-
conditioned). For non-capture, same-piece-type moves the rank-1
update reduces to **identity on the channel block** (the encoder's
``out[k] = Σ sig[s] * DIAG_DEV[piece_row(s), k]`` sum is preserved
when the same piece moves between empty squares).

The v1.5 implementation uses **Option A** for ship velocity: returns
a marker dict carrying ``psi_post_block`` computed via re-encoding
the post-move position. Mathematically equivalent to applying the
rank-1 operator (which reduces to identity for non-captures) and
faster to ship than materializing the explicit rank-1 algebra. The
capture case ships in B5 alongside FA_PAWN's partial-isometry path
and A_1 / STD4 destination-value swap path, where the rank-1 update
becomes non-trivial.

**Structurally distinct from B1/B3a/B3b** (matches B3c's marker dict
shape):
  - B1/B3a/B3b return a sparse 4096×4096 matrix ``U_chan`` such that
    ``U_chan @ psi_pre[chan_block] approx psi_post[chan_block]``.
  - B3d/e returns a marker dict carrying ``psi_post_block`` (a
    4096-dim complex128 vector) directly. No matrix; no projector
    sandwich.

Tests cover:
  1. Output shape and type: marker dict; ``psi_post_block`` is a
     complex128 4096-dim ndarray.
  2. Correctness: ``psi_post_block == state_to_psi(pos_post)
     [FD_DIAG_block]`` within 1e-12 (matches by construction since
     both go through the same encoder).
  3. Marker dict consistency: all required keys present with the
     expected values (``strict_unitary=False``,
     ``reason='rank-1-update-with-renorm'``, ``channel='FD_DIAG'``,
     ``sq_from`` / ``sq_to`` match the move endpoints).
  4. Norm preservation: ``‖psi_post_block‖_2`` matches the FD_DIAG
     block's L2 norm of ``state_to_psi(pos_post)`` exactly (since
     they are the same vector by construction).
  5. (Skipped — Option A chosen, no explicit rank-1 operator
     materialized; conditioning sanity applies only to Option B.)
  6. Captures raise ``NotImplementedError`` pointing at B5 (mirrors
     the pattern in B1/B3a/B3b/B3c).
  7. Bridge integration: ``apply_move_qm`` populates FD_DIAG (after
     B3d/e the bridge no longer raises ``NotImplementedError`` for
     non-capture moves; it returns the assembled per-channel dict
     with all 11 channel entries).

Plus auxiliary tests for input coercion (tuple vs int endpoints) and
the FD_DIAG ADR-003 §3.2 invariance result (psi_post_block ==
psi_pre_block within float precision for non-captures).

Run with ``pytest tests/test_qm_4d_dynamics_b3d.py -v`` from python/.
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
# 0.0) modulo np.copy / dtype cast that could introduce ULP-level
# noise. The user spec gates correctness at 1e-12.
TOL_CORRECTNESS = 1e-12
# The encoder uses float32 internally for several intermediate
# tensors, so the FD_DIAG block's "non-capture invariance" (pre-block
# vs post-block) holds at float32 precision (~1e-6 to 1e-7), not
# float64 1e-12. The "actual matches state_to_psi(pos_post)[block]"
# comparison is exact float64 because both paths take the same
# encoder + L2 normalization.
TOL_INVARIANCE = 5e-6
RNG_SEED = 0xB3D_FDD


# ---- Fixtures ------------------------------------------------------


@pytest.fixture(scope='module')
def imbalanced_position() -> Dict[int, object]:
    """Position with non-zero FD_DIAG channel content. The encoder's
    FD_DIAG channel sums per-piece-type DIAG_DEV rows weighted by
    occupancy signal, so we need at least one piece of each type to
    fully exercise the channel. This fixture has all six piece types
    (5 non-pawn + 2 pawn axes) on both colours — sufficient FD_DIAG
    content (per the tables_4d construction sanity check that
    ``energies['FD_DIAG'] > 0`` on this kind of imbalanced position).
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
    """Second imbalanced position with different occupancy. Used to
    diversify the test sample beyond a single fixture's geometry.
    """
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
    squares. Mirrors B3c's generator: pick an occupied square ``s``,
    pick a random unoccupied target ``t`` (rejecting captures and
    no-op moves).
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
    """Apply the move at the dict level (independent of the function
    under test's internal helper). Mirrors
    chess_spectral_4d.apply_move's non-capture path.
    """
    pos_post = dict(pos_pre)
    piece = pos_post.pop(from_idx)
    pos_post[to_idx] = piece
    return pos_post


def _fd_diag_block(psi_full: np.ndarray) -> np.ndarray:
    """Return the FD_DIAG (channel 10) 4096-dim block of a 45 056-dim
    psi vector. Channel offset = ``10 * CHANNEL_DIM = 40960``.
    """
    start = dyn.FD_DIAG_CHANNEL_IDX * dyn.CHANNEL_DIM
    end = start + dyn.CHANNEL_DIM
    return np.asarray(psi_full[start:end], dtype=np.complex128)


# ====================================================================
#  Test 1: Output shape and type
# ====================================================================
#
# Verify the function returns a marker dict with the expected keys
# and that ``psi_post_block`` is a 4096-dim complex128 ndarray.
# Tested across ~15 (state, move) pairs across two fixtures.

def test_b3d_output_type_and_shape(
    imbalanced_position, imbalanced_position_b,
):
    """Output is a marker dict with the canonical key set; the
    psi_post_block has shape (4096,) and dtype complex128.

    Tested across ~15 pairs from two fixtures (8 + 7) to exercise
    different occupancy / move geometries.
    """
    rng_a = np.random.default_rng(RNG_SEED)
    rng_b = np.random.default_rng(RNG_SEED ^ 0x10)
    pairs_a = _gen_non_capture_pairs(
        list(imbalanced_position.keys()), n_pairs=8, rng=rng_a,
    )
    pairs_b = _gen_non_capture_pairs(
        list(imbalanced_position_b.keys()), n_pairs=7, rng=rng_b,
    )
    cases = [(imbalanced_position, p) for p in pairs_a]
    cases += [(imbalanced_position_b, p) for p in pairs_b]
    assert len(cases) >= 12, (
        f"only {len(cases)} non-capture pairs generated; expected >= 12"
    )

    expected_keys = {
        'strict_unitary', 'reason', 'channel',
        'psi_post_block', 'sq_from', 'sq_to',
    }
    for (pos, (s, t)) in cases:
        result = dyn.u_move_fd_diag(pos, (s, t))
        # Must be a dict (NOT a sparse / dense matrix).
        assert isinstance(result, dict), (
            f"pair ({s}, {t}): expected marker dict, got "
            f"{type(result).__name__}"
        )
        # Required keys.
        assert set(result.keys()) == expected_keys, (
            f"pair ({s}, {t}): marker dict keys "
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
# psi_post_block == state_to_psi(pos_post)[FD_DIAG_block] exactly.
# Both paths go through the same encoder + L2 normalization, so this
# should match within float64 precision (1e-12 gate).

def test_b3d_correctness_matches_state_to_psi(imbalanced_position):
    """psi_post_block is bit-identical to the FD_DIAG block of
    state_to_psi(pos_post, side_to_move=True).

    Verifies the v1.5 Option A construction: re-encode the post-move
    position and slice the FD_DIAG block. The agreement is exact
    because the function under test internally calls state_to_psi
    on pos_post and slices the same offset.
    """
    rng = np.random.default_rng(RNG_SEED ^ 0x20)
    pairs = _gen_non_capture_pairs(
        list(imbalanced_position.keys()), n_pairs=15, rng=rng,
    )
    assert len(pairs) >= 10

    for (s, t) in pairs:
        # Apply the move at the dict level (oracle).
        pos_post = _post_move_position(imbalanced_position, s, t)
        # Compute the reference psi_post via state_to_psi.
        psi_post_full = qm_4d.state_to_psi(pos_post, True)
        expected_block = _fd_diag_block(psi_post_full)
        # Call the function under test.
        result = dyn.u_move_fd_diag(imbalanced_position, (s, t))
        actual_block = result['psi_post_block']
        # Max-abs error.
        max_err = float(np.max(np.abs(actual_block - expected_block)))
        assert max_err < TOL_CORRECTNESS, (
            f"pair ({s}, {t}): "
            f"max |psi_post_block - state_to_psi[FD_DIAG]| = {max_err:.3e}, "
            f"expected < {TOL_CORRECTNESS:.0e}"
        )


# ====================================================================
#  Test 3: Marker dict consistency
# ====================================================================
#
# Verify all marker dict fields take the expected values per the
# user-spec marker contract for B3d/e.

def test_b3d_marker_dict_field_values(imbalanced_position):
    """All marker dict fields match the canonical B3d/e contract:

      strict_unitary = False
      reason         = 'rank-1-update-with-renorm'
      channel        = 'FD_DIAG'
      sq_from        = int(from_idx)
      sq_to          = int(to_idx)
    """
    rng = np.random.default_rng(RNG_SEED ^ 0x30)
    pairs = _gen_non_capture_pairs(
        list(imbalanced_position.keys()), n_pairs=10, rng=rng,
    )
    assert len(pairs) >= 6
    for (s, t) in pairs:
        result = dyn.u_move_fd_diag(imbalanced_position, (s, t))
        # strict_unitary: always False (informational marker).
        assert result['strict_unitary'] is False, (
            f"strict_unitary should be False, got "
            f"{result['strict_unitary']!r}"
        )
        # reason: distinguishes B3d/e from B3c's 'measurement-only'
        # and B3a's 'cross-orbit'.
        assert result['reason'] == 'rank-1-update-with-renorm', (
            f"reason should be 'rank-1-update-with-renorm', got "
            f"{result['reason']!r}"
        )
        # channel: always 'FD_DIAG'.
        assert result['channel'] == 'FD_DIAG', (
            f"channel should be 'FD_DIAG', got {result['channel']!r}"
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
            f"sq_to type is {type(result['sq_to']).__name__}, "
            "expected int"
        )


def test_b3d_marker_dict_accepts_tuple_endpoints(imbalanced_position):
    """Tuple-coord endpoints normalise to the same linear sq_from /
    sq_to integers as int endpoints. Mirrors the input-coercion
    behavior of u_move_a1 / u_move_std4 / u_move_fa_pawn /
    u_move_fib_meas.
    """
    fr_tuple = (3, 1, 2, 3)
    to_tuple = (3, 1, 2, 4)
    fr_int = _t4.sq4(*fr_tuple)
    to_int = _t4.sq4(*to_tuple)
    result_tuple = dyn.u_move_fd_diag(
        imbalanced_position, (fr_tuple, to_tuple),
    )
    result_int = dyn.u_move_fd_diag(
        imbalanced_position, (fr_int, to_int),
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
        f"tuple vs int endpoints diverge by {diff:.3e}"
    )


# ====================================================================
#  Test 4: Norm preservation
# ====================================================================
#
# The L2 norm of psi_post_block matches the FD_DIAG block's L2 norm
# from state_to_psi(pos_post). Trivially true because they are the
# same vector by construction; the test is a defensive regression
# check that the function isn't accidentally re-normalizing or
# scaling the slice.

def test_b3d_norm_preservation(imbalanced_position):
    """The L2 norm of psi_post_block equals the L2 norm of
    state_to_psi(pos_post)[FD_DIAG_block] exactly.

    Both quantities are the same vector by construction (the function
    under test slices state_to_psi's output directly), so the norms
    are identical. This regression test guards against an accidental
    re-normalization or per-block L2 scaling that would change the
    relative weighting of FD_DIAG vs the other 10 channel blocks
    when the bridge consumer assembles them into a 45 056-dim psi.
    """
    rng = np.random.default_rng(RNG_SEED ^ 0x40)
    pairs = _gen_non_capture_pairs(
        list(imbalanced_position.keys()), n_pairs=12, rng=rng,
    )
    assert len(pairs) >= 8
    for (s, t) in pairs:
        pos_post = _post_move_position(imbalanced_position, s, t)
        psi_post_full = qm_4d.state_to_psi(pos_post, True)
        expected_block = _fd_diag_block(psi_post_full)
        expected_norm = float(np.linalg.norm(expected_block))

        result = dyn.u_move_fd_diag(imbalanced_position, (s, t))
        actual_norm = float(np.linalg.norm(result['psi_post_block']))

        # Norms equal exactly (both are the same vector). Use a tight
        # tolerance — anything > ULP indicates a bug.
        norm_diff = abs(actual_norm - expected_norm)
        assert norm_diff < 1e-13, (
            f"pair ({s}, {t}): norm diff = {norm_diff:.3e}, "
            f"actual={actual_norm:.6f}, expected={expected_norm:.6f}"
        )


def test_b3d_non_capture_invariance(imbalanced_position):
    """ADR-003 §3.2 channel 10 invariance: for non-capture moves the
    FD_DIAG block of psi_post equals the FD_DIAG block of psi_pre
    within float precision (the channel is invariant under same-
    piece-type moves between empty squares).

    This is the structural property that lets v1.5 ship Option A:
    re-encoding pos_post produces the same FD_DIAG block as
    re-encoding pos_pre, so the rank-1 update reduces to identity
    on the channel block.

    The encoder uses float32 internals so the invariance holds at
    ~1e-6 to 1e-7, not float64 precision; we use a 5e-6 tolerance.
    """
    rng = np.random.default_rng(RNG_SEED ^ 0x50)
    pairs = _gen_non_capture_pairs(
        list(imbalanced_position.keys()), n_pairs=12, rng=rng,
    )
    assert len(pairs) >= 8

    psi_pre_full = qm_4d.state_to_psi(imbalanced_position, True)
    expected_pre_block = _fd_diag_block(psi_pre_full)

    n_passed = 0
    worst_diff = 0.0
    for (s, t) in pairs:
        result = dyn.u_move_fd_diag(imbalanced_position, (s, t))
        actual_post_block = result['psi_post_block']
        # The pre-move psi normalization differs from post-move (the
        # full vector has different L2 norm in general because adding/
        # removing a piece changes the encoder output's norm). Compare
        # un-normalized: both blocks come from state_to_psi(pos)
        # divided by ||encode(pos)||, so we have to compare with that
        # context.
        #
        # The simpler invariance check (per ADR-003 §3.2 channel 10):
        # the un-normalized FD_DIAG sum is invariant. We test the
        # normalized blocks directly here, accepting that they differ
        # by ~5e-6 because the global norm differs slightly between
        # pre and post moves (which itself is a float32 artifact —
        # the global norm should be identical for FD-DIAG-invariant
        # non-capture moves, but the encoder's float32 intermediate
        # accumulators introduce ULP noise into the norm).
        diff = float(np.max(np.abs(
            actual_post_block - expected_pre_block
        )))
        worst_diff = max(worst_diff, diff)
        if diff < TOL_INVARIANCE:
            n_passed += 1

    # We expect ALL pairs to satisfy invariance within float32
    # precision; report the worst case if any fail.
    assert n_passed == len(pairs), (
        f"FD_DIAG non-capture invariance failed for "
        f"{len(pairs) - n_passed}/{len(pairs)} pairs; "
        f"worst max-abs diff = {worst_diff:.3e}, gate = {TOL_INVARIANCE:.0e}"
    )


# ====================================================================
#  Test 5: (Skipped per Option A — conditioning sanity is Option B
#  only)
# ====================================================================
#
# Per the user-spec, the conditioning-sanity test (cond ≤ 100 across
# the test corpus) is required only when Option B (explicit rank-1
# update operator) is materialized. We chose Option A for v1.5
# (re-encode marker), which doesn't materialize the operator, so the
# conditioning gate is a property of the underlying ADR-003 §3.2
# construction (validated by Phase 3.5 Probe 2: cond p95 = 8.60), not
# a property of this function's output. No test here.


# ====================================================================
#  Test 6: Captures raise NotImplementedError
# ====================================================================
#
# Same pattern as B1 / B3a / B3b / B3c: assume_non_capture=False with
# a capture move raises NotImplementedError pointing at B5.

def test_b3d_capture_returns_marker_dict(imbalanced_position):
    """Capture moves with assume_non_capture=False return the Option A
    re-encode marker (capture-rank-1-with-renorm).

    Pre-B5 this raised NotImplementedError; post-B5 the FD_DIAG capture
    path uses the same Option A re-encode construction as non-captures,
    differing only in the ``reason`` string and the ``captured_piece``
    field. Comprehensive B5 coverage in
    :mod:`tests.test_qm_4d_dynamics_b5`.
    """
    occupied = sorted(imbalanced_position.keys())
    assert len(occupied) >= 2, "fixture must have >= 2 pieces for capture test"
    s = occupied[0]
    t = occupied[1]
    cap_result = dyn.u_move_fd_diag(
        imbalanced_position, (s, t), assume_non_capture=False,
    )
    assert isinstance(cap_result, dict), (
        f"B5 capture path should return marker dict; got "
        f"{type(cap_result).__name__}"
    )
    assert cap_result['strict_unitary'] is False
    assert cap_result['reason'] == 'capture-rank-1-with-renorm', (
        f"FD_DIAG capture reason should be "
        f"'capture-rank-1-with-renorm'; got {cap_result['reason']!r}"
    )
    assert cap_result['channel'] == 'FD_DIAG'
    assert cap_result['captured_piece'] == imbalanced_position[t]
    assert cap_result['psi_post_block'].shape == (4096,)
    assert cap_result['psi_post_block'].dtype == np.complex128


def test_b3d_assume_non_capture_default_skips_check(imbalanced_position):
    """Default assume_non_capture=True skips the capture check, so
    even calling on a captures move-pair returns a marker dict
    rather than raising. The classical apply_move at the dict level
    overwrites the captured piece silently — the QM measurement
    re-encode honestly reflects whatever post-move position results.
    """
    occupied = sorted(imbalanced_position.keys())
    s = occupied[0]
    t = occupied[1]
    # No exception expected at default (assume_non_capture=True).
    result = dyn.u_move_fd_diag(imbalanced_position, (s, t))
    assert isinstance(result, dict)
    assert result['psi_post_block'].shape == (4096,)
    assert result['channel'] == 'FD_DIAG'


# ====================================================================
#  Test 7: Bridge integration
# ====================================================================
#
# After B3d/e the bridge no longer raises NotImplementedError for
# non-capture moves; it returns the assembled per-channel dict with
# all 11 channel entries. Verify FD_DIAG is present as a marker dict
# (the rank-1-update-with-renorm path).

def test_b3d_apply_move_qm_returns_assembled_dict(imbalanced_position):
    """The bridge returns the assembled per-channel dict with all 11
    channels populated for non-capture moves. FD_DIAG is a marker
    dict carrying psi_post_block.
    """
    move = ((3, 1, 2, 3), (3, 1, 2, 4))
    result = dyn.apply_move_qm(imbalanced_position, move)
    # B3d/e contract: bridge returns the assembled dict directly
    # (no more NotImplementedError for non-captures).
    assert isinstance(result, dict), (
        f"apply_move_qm should return a dict; got "
        f"{type(result).__name__}"
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
        f"bridge dict keys {sorted(result.keys())} != expected "
        f"{sorted(expected_keys)}"
    )
    # FD_DIAG specifically: must be a marker dict (the rank-1 path).
    fd_entry = result['FD_DIAG']
    assert isinstance(fd_entry, dict), (
        f"FD_DIAG should be a marker dict; got {type(fd_entry).__name__}"
    )
    assert fd_entry['reason'] == 'rank-1-update-with-renorm', (
        f"FD_DIAG marker reason should be 'rank-1-update-with-renorm'; "
        f"got {fd_entry['reason']!r}"
    )
    assert fd_entry['channel'] == 'FD_DIAG'
    assert fd_entry['psi_post_block'].shape == (4096,)
    assert fd_entry['psi_post_block'].dtype == np.complex128
    assert fd_entry['strict_unitary'] is False


def test_b3d_apply_move_qm_fd_diag_matches_state_to_psi(
    imbalanced_position,
):
    """The bridge's FD_DIAG entry's psi_post_block matches
    state_to_psi(pos_post)[FD_DIAG_block] within 1e-12.

    Cross-check that the bridge correctly wires u_move_fd_diag and
    doesn't re-process the result (e.g., re-normalizing or scaling).
    """
    move = ((4, 4, 1, 5), (4, 4, 1, 6))
    result = dyn.apply_move_qm(imbalanced_position, move)
    fd_entry = result['FD_DIAG']

    # Reference: re-encode pos_post and slice FD_DIAG.
    s = _t4.sq4(4, 4, 1, 5)
    t = _t4.sq4(4, 4, 1, 6)
    pos_post = _post_move_position(imbalanced_position, s, t)
    psi_post_full = qm_4d.state_to_psi(pos_post, True)
    expected_block = _fd_diag_block(psi_post_full)

    diff = float(np.max(np.abs(
        fd_entry['psi_post_block'] - expected_block
    )))
    assert diff < TOL_CORRECTNESS, (
        f"bridge FD_DIAG psi_post_block diverges from "
        f"state_to_psi(pos_post)[FD_DIAG_block] by {diff:.3e}; "
        f"expected < {TOL_CORRECTNESS:.0e}"
    )


# ====================================================================
#  Test 8: Side-to-move forwarding
# ====================================================================
#
# The side_to_move_post kwarg is forwarded to state_to_psi, which
# multiplies the encoder output by +1 (white) or -1 (black). The
# FD_DIAG block flips sign accordingly; magnitudes are unaffected.

def test_b3d_side_to_move_post_sign_convention(imbalanced_position):
    """side_to_move_post=True (default, white) and =False (black)
    produce psi_post_blocks that differ by an overall sign. Magnitudes
    are identical.
    """
    move = ((3, 1, 2, 3), (3, 1, 2, 4))
    result_white = dyn.u_move_fd_diag(
        imbalanced_position, move, side_to_move_post=True,
    )
    result_black = dyn.u_move_fd_diag(
        imbalanced_position, move, side_to_move_post=False,
    )
    block_w = result_white['psi_post_block']
    block_b = result_black['psi_post_block']

    # Magnitudes match (per Pre-flight 1's Z_2 sign convention; the
    # sign affects relative phase but not Born-rule probabilities).
    mag_diff = float(np.max(np.abs(np.abs(block_w) - np.abs(block_b))))
    assert mag_diff < 1e-13, (
        f"|psi_post_block| should be identical for white/black; "
        f"got max diff = {mag_diff:.3e}"
    )
    # The blocks themselves differ by an overall sign (white = +1,
    # black = -1).
    sum_check = float(np.max(np.abs(block_w + block_b)))
    assert sum_check < 1e-13, (
        f"block_w + block_b should be ~0 (overall sign flip between "
        f"white and black); got max abs = {sum_check:.3e}"
    )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
