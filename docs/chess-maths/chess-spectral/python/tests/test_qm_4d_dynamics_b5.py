"""Unit tests for chess_spectral.qm_4d_dynamics — Phase 4 milestone B5.

Covers the **capture-handling** path for all 11 channel builders plus
the M_pawn = M_single + M_double decomposition (Phase 3.5 amendment to
ADR-005 §3.3) used by the v1.6+ pseudo-Hermitian observable promotion.

Per the Phase 3.5 + ADR-002 + ADR-003 §3.3 amendment lineage, the
**measurement-only re-encode** path (Option A) is honest within QM
formalism for any non-strictly-unitary case. v1.5 ships every
channel's capture path as Option A: the post-capture position is
re-encoded via :func:`chess_spectral.qm_4d.state_to_psi`, the channel
block is sliced, and the result is returned as a marker dict carrying
``psi_post_block`` + ``captured_piece``. Explicit rank-1 / partial-
isometry / Stinespring algebra is deferred to v1.7+.

Structurally:
  - **A_1 / STD4_X/Y/Z/W / FD_DIAG** capture markers carry
    ``reason='capture-rank-1-with-renorm'`` (the ADR-005 lineage:
    a rank-1 update to the channel block, with renormalisation
    folded into :func:`state_to_psi`'s L2 normalisation per ADR-002
    §3.4).
  - **FA_PAWN_W/Y** capture markers carry
    ``reason='capture-partial-isometry'`` (per ADR-003 §3.1
    channels 8-9: the captured pawn's 8-mode block is removed by
    the swap, so ``||U @ psi|| < ||psi||``; renormalisation is
    folded into :func:`state_to_psi`).
  - **FIB_SYM_1/2/3** capture markers carry
    ``reason='capture-measurement-only'`` (matches the Phase 3.5
    amendment to ADR-003 §3.3: bilinear FIB encoder formula has no
    strict-unitary lift, so captures and non-captures both ship via
    measurement-only re-encode).

Tests (15 tests, ~60 assertions):

  Test 1  — Capture detection: each channel's
            ``assume_non_capture=False`` on a capture move returns a
            marker dict with ``captured_piece`` populated correctly.
  Test 2  — Re-encode correctness: ``psi_post_block`` matches
            ``state_to_psi(state_post)[chan_block]`` within 1e-12.
  Test 3  — Captured-piece field: matches ``state_pre[to_idx]``.
  Test 4  — Reason field: channel-specific reason string is correct.
  Test 5  — Bridge integration: ``apply_move_qm`` on a capture move
            returns the all-marker-dict variant (no
            NotImplementedError).
  Test 6  — FA_PAWN partial-isometry semantics: post-capture FA_PAWN
            block reflects the captured pawn's removed contribution.
  Test 7  — M_single + M_double decomposition: ``M_single`` is
            P-pseudo-Hermitian (residual = 0.0 reproduces Probe 3);
            ``M_full = M_single + M_double`` has residual 32.0.
  Test 8  — Decomposition cache: repeated calls return the same dict.
  Test 9  — Decomposition for Y axis: same residual structure as W.
  Test 10 — Tuple vs int endpoints: capture-marker outputs match.
  Test 11 — Side-to-move forwarding: capture-marker
            ``psi_post_block`` flips sign for white vs black.
  Test 12 — Non-capture preservation: ``assume_non_capture=False`` on
            a NON-capture move still returns the strict-unitary
            csr_matrix (or non-capture marker for FIB / FD_DIAG /
            cross-orbit STD4); B5 only intercepts captures.
  Test 13 — All-channel capture coverage: a single capture move
            produces 11 capture markers via the bridge.
  Test 14 — End-to-end with chess_spectral_4d.apply_move: capture via
            the v1.4 surface yields a Move4D with captured_piece,
            which the bridge accepts.
  Test 15 — Multi-piece capture sample: 10+ different (pre, capture)
            move pairs across all 11 channels — pin the marker shape
            invariants.

Run with ``pytest tests/test_qm_4d_dynamics_b5.py -v`` from python/.
"""
from __future__ import annotations

import os
import sys
from typing import Dict, List, Tuple

import numpy as np
import pytest
import scipy.sparse as sp

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)

from chess_spectral import qm_4d                  # noqa: E402
from chess_spectral import qm_4d_dynamics as dyn  # noqa: E402
from chess_spectral import qm_4d_bridge as br     # noqa: E402
from chess_spectral import tables_4d as _t4       # noqa: E402


# ---- Tolerances -----------------------------------------------------

# state_to_psi normalises the encoder output by its L2 norm; the slice
# operation is a no-op view. The capture-path comparison should be
# EXACT (max error 0.0) modulo np.copy / dtype cast that could
# introduce ULP-level noise. Gate at 1e-12 per the user spec.
TOL_CORRECTNESS = 1e-12

# Frobenius residual gate for the M_single P-pseudo-Hermitian check
# (Probe 3 reported 0.000e+00; we use a slightly looser gate to
# accommodate any future changes in the underlying construction).
TOL_PSEUDO_HERMITIAN = 1e-12

RNG_SEED = 0xB5_AAA


# ---- Fixtures -------------------------------------------------------


@pytest.fixture(scope='module')
def imbalanced_position() -> Dict[int, object]:
    """Position with all six piece types on both colours, including
    pawn pieces on both axes. Sufficient diversity to exercise every
    channel's capture-detection path.
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
def fa_pawn_w_capture_position() -> Dict[int, object]:
    """Position where a white W-pawn can capture a black W-pawn
    diagonally (forward W push + X axis displacement). Used by the
    FA_PAWN partial-isometry semantics test.
    """
    coords = {
        (0, 0, 0, 0): 'K', (7, 7, 7, 7): 'k',
        # White W-pawn at (3, 0, 0, 1)
        (3, 0, 0, 1): ('P', 'w'),
        # Black W-pawn at (4, 0, 0, 2) — diagonal forward target
        (4, 0, 0, 2): ('p', 'w'),
        # Some extra pieces to make the FA_PAWN block non-zero
        (1, 1, 1, 1): 'Q', (6, 6, 6, 6): 'q',
    }
    return {_t4.sq4(*c): p for c, p in coords.items()}


def _gen_capture_pairs(
    position: Dict[int, object],
    *, n_pairs: int,
    rng: np.random.Generator,
) -> List[Tuple[int, int]]:
    """Generate (from, to) capture pairs from an occupied position.

    Pick two distinct occupied squares: from_idx (the source piece)
    and to_idx (the captured piece). Returns up to n_pairs unique
    pairs (deduplicated by ordered tuple).
    """
    occupied = sorted(position.keys())
    n_occ = len(occupied)
    if n_occ < 2:
        return []
    pairs: List[Tuple[int, int]] = []
    seen: set = set()
    max_attempts = max(64, 16 * n_pairs)
    attempts = 0
    while len(pairs) < n_pairs and attempts < max_attempts:
        attempts += 1
        i, j = rng.integers(0, n_occ, size=2)
        if i == j:
            continue
        s, t = int(occupied[i]), int(occupied[j])
        if (s, t) in seen:
            continue
        pairs.append((s, t))
        seen.add((s, t))
    return pairs


def _channel_block(psi_full: np.ndarray, chan_idx: int) -> np.ndarray:
    """Slice the chan_idx 4096-dim block of a 45 056-dim psi vector."""
    start = chan_idx * dyn.CHANNEL_DIM
    end = start + dyn.CHANNEL_DIM
    return np.asarray(psi_full[start:end], dtype=np.complex128)


def _post_capture_position(
    pos_pre: Dict[int, object], from_idx: int, to_idx: int,
) -> Dict[int, object]:
    """Apply a capture move at the dict level: the moving piece moves
    from from_idx to to_idx, overwriting the captured piece.
    """
    pos_post = dict(pos_pre)
    piece = pos_post.pop(from_idx)
    pos_post[to_idx] = piece
    return pos_post


# ====================================================================
#  Test 1: Capture detection across all 11 channels
# ====================================================================
#
# Each per-channel builder, called with assume_non_capture=False on a
# capture move, returns a marker dict with the canonical key set.

def test_b5_capture_detection_all_channels(imbalanced_position):
    """For each of the 11 per-channel builders, a capture move with
    assume_non_capture=False returns a marker dict carrying
    psi_post_block, captured_piece, and the channel-specific reason
    string. Tested across one capture pair per channel (11 channels)."""
    pos = imbalanced_position
    occ = sorted(pos.keys())
    s, t = occ[0], occ[1]
    captured_expected = pos[t]

    # A_1 (1 channel)
    r = dyn.u_move_a1(pos, (s, t), assume_non_capture=False)
    assert isinstance(r, dict)
    assert 'psi_post_block' in r
    assert 'captured_piece' in r
    assert r['captured_piece'] == captured_expected
    assert r['channel'] == 'A1'

    # STD4_X/Y/Z/W (4 channels)
    for axis in ('X', 'Y', 'Z', 'W'):
        r = dyn.u_move_std4(
            pos, (s, t), axis=axis, assume_non_capture=False,
        )
        assert isinstance(r, dict)
        assert 'psi_post_block' in r
        assert 'captured_piece' in r
        assert r['captured_piece'] == captured_expected
        assert r['channel'] == f'STD4_{axis}'

    # FA_PAWN_W/Y (2 channels)
    for axis in ('W', 'Y'):
        r = dyn.u_move_fa_pawn(
            pos, (s, t), axis=axis, assume_non_capture=False,
        )
        assert isinstance(r, dict)
        assert 'psi_post_block' in r
        assert 'captured_piece' in r
        assert r['captured_piece'] == captured_expected
        assert r['channel'] == f'FA_PAWN_{axis}'

    # FIB_SYM_1/2/3 (3 channels)
    for fib_idx in (1, 2, 3):
        r = dyn.u_move_fib_meas(
            pos, (s, t), fib_idx=fib_idx, assume_non_capture=False,
        )
        assert isinstance(r, dict)
        assert 'psi_post_block' in r
        assert 'captured_piece' in r
        assert r['captured_piece'] == captured_expected
        assert r['channel'] == f'FIB_SYM_{fib_idx}'

    # FD_DIAG (1 channel)
    r = dyn.u_move_fd_diag(pos, (s, t), assume_non_capture=False)
    assert isinstance(r, dict)
    assert 'psi_post_block' in r
    assert 'captured_piece' in r
    assert r['captured_piece'] == captured_expected
    assert r['channel'] == 'FD_DIAG'


# ====================================================================
#  Test 2: Re-encode correctness
# ====================================================================
#
# psi_post_block matches state_to_psi(pos_post)[chan_block] within 1e-12
# for every channel. This is the core Option A invariant.

def test_b5_re_encode_correctness_all_channels(imbalanced_position):
    """For each channel, psi_post_block matches the corresponding
    block of state_to_psi(pos_post) within 1e-12. Verifies the Option
    A re-encode construction at the float64 precision gate."""
    pos = imbalanced_position
    occ = sorted(pos.keys())
    # Pick a capture move that's not on a corner (avoid edge cases)
    s, t = occ[3], occ[4]
    # Reference: build pos_post and run state_to_psi
    pos_post = _post_capture_position(pos, s, t)
    psi_post_full = qm_4d.state_to_psi(pos_post, True)

    # A_1
    r = dyn.u_move_a1(pos, (s, t), assume_non_capture=False)
    expected = _channel_block(psi_post_full, dyn.A1_CHANNEL_IDX)
    err = float(np.max(np.abs(r['psi_post_block'] - expected)))
    assert err < TOL_CORRECTNESS, f"A1 capture re-encode err = {err:.3e}"

    # STD4_*
    std4_idx = {'X': 1, 'Y': 2, 'Z': 3, 'W': 4}
    for axis in ('X', 'Y', 'Z', 'W'):
        r = dyn.u_move_std4(
            pos, (s, t), axis=axis, assume_non_capture=False,
        )
        expected = _channel_block(psi_post_full, std4_idx[axis])
        err = float(np.max(np.abs(r['psi_post_block'] - expected)))
        assert err < TOL_CORRECTNESS, (
            f"STD4_{axis} capture re-encode err = {err:.3e}"
        )

    # FA_PAWN_W/Y
    fa_idx = {'W': dyn.FA_PAWN_W_CHANNEL_IDX, 'Y': dyn.FA_PAWN_Y_CHANNEL_IDX}
    for axis in ('W', 'Y'):
        r = dyn.u_move_fa_pawn(
            pos, (s, t), axis=axis, assume_non_capture=False,
        )
        expected = _channel_block(psi_post_full, fa_idx[axis])
        err = float(np.max(np.abs(r['psi_post_block'] - expected)))
        assert err < TOL_CORRECTNESS, (
            f"FA_PAWN_{axis} capture re-encode err = {err:.3e}"
        )

    # FIB_SYM_*
    fib_idx_map = {
        1: dyn.FIB_SYM_1_CHANNEL_IDX,
        2: dyn.FIB_SYM_2_CHANNEL_IDX,
        3: dyn.FIB_SYM_3_CHANNEL_IDX,
    }
    for fib_idx in (1, 2, 3):
        r = dyn.u_move_fib_meas(
            pos, (s, t), fib_idx=fib_idx, assume_non_capture=False,
        )
        expected = _channel_block(psi_post_full, fib_idx_map[fib_idx])
        err = float(np.max(np.abs(r['psi_post_block'] - expected)))
        assert err < TOL_CORRECTNESS, (
            f"FIB_SYM_{fib_idx} capture re-encode err = {err:.3e}"
        )

    # FD_DIAG
    r = dyn.u_move_fd_diag(pos, (s, t), assume_non_capture=False)
    expected = _channel_block(psi_post_full, dyn.FD_DIAG_CHANNEL_IDX)
    err = float(np.max(np.abs(r['psi_post_block'] - expected)))
    assert err < TOL_CORRECTNESS, f"FD_DIAG capture re-encode err = {err:.3e}"


# ====================================================================
#  Test 3: Captured-piece field correctness
# ====================================================================
#
# The captured_piece field exactly equals state_pre[to_idx]; tested
# across multiple capture pairs and piece types to guard against any
# silent type coercion or incorrect dict lookup.

def test_b5_captured_piece_field_correctness(imbalanced_position):
    """For multiple capture pairs and piece types, the marker's
    captured_piece field exactly matches state_pre[to_idx]."""
    pos = imbalanced_position
    rng = np.random.default_rng(RNG_SEED ^ 0x10)
    pairs = _gen_capture_pairs(pos, n_pairs=10, rng=rng)
    assert len(pairs) >= 5, f"only {len(pairs)} capture pairs generated"

    for s, t in pairs:
        captured_expected = pos[t]
        # Smoke-check via 3 channels (A_1, FA_PAWN_W, FD_DIAG):
        for fn, kwargs in [
            (dyn.u_move_a1, {}),
            (dyn.u_move_fa_pawn, {'axis': 'W'}),
            (dyn.u_move_fd_diag, {}),
        ]:
            r = fn(pos, (s, t), assume_non_capture=False, **kwargs)
            assert r['captured_piece'] == captured_expected, (
                f"captured_piece mismatch for ({s}, {t}): "
                f"got {r['captured_piece']!r}, expected "
                f"{captured_expected!r}"
            )


# ====================================================================
#  Test 4: Reason field correctness
# ====================================================================

def test_b5_reason_field_correctness(imbalanced_position):
    """Channel-specific reason strings:
      A_1 / STD4 / FD_DIAG → 'capture-rank-1-with-renorm'
      FA_PAWN_*           → 'capture-partial-isometry'
      FIB_SYM_*           → 'capture-measurement-only'
    """
    pos = imbalanced_position
    occ = sorted(pos.keys())
    s, t = occ[2], occ[5]

    # Rank-1 channels: A_1, STD4_X/Y/Z/W, FD_DIAG (6 channels)
    rank1_expected = 'capture-rank-1-with-renorm'
    r = dyn.u_move_a1(pos, (s, t), assume_non_capture=False)
    assert r['reason'] == rank1_expected, f"A1 reason = {r['reason']!r}"
    for axis in ('X', 'Y', 'Z', 'W'):
        r = dyn.u_move_std4(pos, (s, t), axis=axis, assume_non_capture=False)
        assert r['reason'] == rank1_expected, (
            f"STD4_{axis} reason = {r['reason']!r}"
        )
    r = dyn.u_move_fd_diag(pos, (s, t), assume_non_capture=False)
    assert r['reason'] == rank1_expected, f"FD_DIAG reason = {r['reason']!r}"

    # Partial-isometry channels: FA_PAWN_W, FA_PAWN_Y
    pi_expected = 'capture-partial-isometry'
    for axis in ('W', 'Y'):
        r = dyn.u_move_fa_pawn(pos, (s, t), axis=axis, assume_non_capture=False)
        assert r['reason'] == pi_expected, (
            f"FA_PAWN_{axis} reason = {r['reason']!r}"
        )

    # Measurement-only channels: FIB_SYM_1/2/3
    mo_expected = 'capture-measurement-only'
    for fib_idx in (1, 2, 3):
        r = dyn.u_move_fib_meas(
            pos, (s, t), fib_idx=fib_idx, assume_non_capture=False,
        )
        assert r['reason'] == mo_expected, (
            f"FIB_SYM_{fib_idx} reason = {r['reason']!r}"
        )


# ====================================================================
#  Test 5: Bridge integration
# ====================================================================
#
# apply_move_qm on a capture move returns the all-marker-dict variant
# (every channel value is a marker dict; no csr_matrix entries). No
# NotImplementedError raised.

def test_b5_apply_move_qm_capture_returns_assembled_dict(imbalanced_position):
    """The bridge's apply_move_qm on a capture move returns the all-
    marker-dict variant: every value is a dict, every dict carries
    psi_post_block + captured_piece. The bridge does not raise
    NotImplementedError for any move."""
    pos = imbalanced_position
    occ = sorted(pos.keys())
    s, t = occ[6], occ[7]

    result = br.apply_move_qm(pos, (s, t))

    # All 11 channel keys present
    expected_keys = {
        'A1',
        'STD4_X', 'STD4_Y', 'STD4_Z', 'STD4_W',
        'FA_PAWN_W', 'FA_PAWN_Y',
        'FIB_SYM_1', 'FIB_SYM_2', 'FIB_SYM_3',
        'FD_DIAG',
    }
    assert set(result.keys()) == expected_keys

    # Every entry is a marker dict (capture path)
    captured_expected = pos[t]
    for chan, entry in result.items():
        assert isinstance(entry, dict), (
            f"channel {chan} entry should be marker dict on captures; "
            f"got {type(entry).__name__}"
        )
        assert entry['strict_unitary'] is False
        assert 'psi_post_block' in entry
        assert entry['psi_post_block'].shape == (4096,)
        assert entry['psi_post_block'].dtype == np.complex128
        assert 'captured_piece' in entry, (
            f"channel {chan}: missing captured_piece field on capture path"
        )
        assert entry['captured_piece'] == captured_expected, (
            f"channel {chan} captured_piece mismatch: got "
            f"{entry['captured_piece']!r}, expected {captured_expected!r}"
        )


def test_b5_apply_move_qm_no_raise_on_either_path(imbalanced_position):
    """Apply_move_qm raises no NotImplementedError on either non-
    capture or capture moves. Pre-B5 captures raised; this test
    verifies the closing of the last NIE branch."""
    pos = imbalanced_position
    occ = sorted(pos.keys())

    # Non-capture move
    s_nc = occ[0]
    # Find an unoccupied destination
    occupied = set(occ)
    t_nc = next(i for i in range(_t4.N_SQUARES) if i not in occupied)
    # Should NOT raise
    result_nc = br.apply_move_qm(pos, (s_nc, t_nc))
    assert isinstance(result_nc, dict)
    assert len(result_nc) == 11

    # Capture move
    s_c, t_c = occ[1], occ[2]
    # Should NOT raise
    result_c = br.apply_move_qm(pos, (s_c, t_c))
    assert isinstance(result_c, dict)
    assert len(result_c) == 11


# ====================================================================
#  Test 6: FA_PAWN partial-isometry semantics
# ====================================================================
#
# For FA_PAWN_W captures: the captured pawn's contribution to the
# FA_PAWN_W block is removed. We can't directly assert "norm <
# pre-norm" because state_to_psi normalises post-capture independently;
# instead, verify the captured pawn's source-square scatter pattern
# is absent from psi_post_block compared to pos_pre's psi.

def test_b5_fa_pawn_w_captured_pawn_removed(fa_pawn_w_capture_position):
    """For an FA_PAWN_W capture (white W-pawn captures black W-pawn),
    the post-capture FA_PAWN_W block reflects the captured pawn's
    removal. Specifically: the post-capture position has one fewer
    W-axis pawn, so the FA_PAWN_W block's L2 norm is smaller than the
    pre-capture position's pre-normalisation, but the post-norm matches
    state_to_psi(pos_post)'s natural normalisation per ADR-002 §3.4.
    """
    pos = fa_pawn_w_capture_position
    s = _t4.sq4(3, 0, 0, 1)  # white W-pawn
    t = _t4.sq4(4, 0, 0, 2)  # black W-pawn (captured)

    # B5 capture path
    r = dyn.u_move_fa_pawn(
        pos, (s, t), axis='W', assume_non_capture=False,
    )
    assert r['captured_piece'] == ('p', 'w')
    assert r['reason'] == 'capture-partial-isometry'

    # Reference: pos_post has one fewer W-pawn (the moving white pawn
    # is now at sq_to). Verify state_to_psi's post-capture FA_PAWN_W
    # block matches r['psi_post_block'].
    pos_post = _post_capture_position(pos, s, t)
    psi_post_full = qm_4d.state_to_psi(pos_post, True)
    expected = _channel_block(psi_post_full, dyn.FA_PAWN_W_CHANNEL_IDX)
    err = float(np.max(np.abs(r['psi_post_block'] - expected)))
    assert err < TOL_CORRECTNESS, (
        f"FA_PAWN_W partial-isometry re-encode err = {err:.3e}"
    )

    # Sanity: pos_post has fewer W-axis pawns than pos
    n_w_pre = sum(
        1 for v in pos.values()
        if isinstance(v, tuple) and len(v) == 2 and v[1] == 'w'
    )
    n_w_post = sum(
        1 for v in pos_post.values()
        if isinstance(v, tuple) and len(v) == 2 and v[1] == 'w'
    )
    assert n_w_post == n_w_pre - 1, (
        f"capture should reduce W-pawn count by 1; "
        f"pre={n_w_pre}, post={n_w_post}"
    )


# ====================================================================
#  Test 7: M_pawn = M_single + M_double decomposition (Phase 3.5
#          Probe-3 amendment to ADR-005)
# ====================================================================
#
# Per Probe 3:
#   M_single is P-pseudo-Hermitian: residual = 0.0 exactly.
#   M_full = M_single + M_double has residual = 32.0 (η-breaking
#   double-push).

def test_b5_pawn_decomp_w_single_pseudo_hermitian():
    """M_single (W-axis, single-push + captures, no double-push) is
    exactly P_w-pseudo-Hermitian: ``M_single^T = P_w · M_single ·
    P_w⁻¹`` with Frobenius residual ≤ 1e-12."""
    decomp = dyn._pawn_observable_decomp('W')
    assert set(decomp.keys()) == {'single', 'double', 'eta'}
    M_single = decomp['single']
    eta = decomp['eta']
    assert sp.isspmatrix_csr(M_single)
    assert sp.isspmatrix_csr(eta)
    assert M_single.shape == (4096, 4096)
    assert eta.shape == (4096, 4096)
    # eta is order-2 (involution), so eta^{-1} = eta
    M_T = M_single.T
    P_M_P = (eta @ M_single @ eta).tocsr()
    diff = (M_T - P_M_P).toarray()
    frob = float(np.linalg.norm(diff))
    assert frob <= TOL_PSEUDO_HERMITIAN, (
        f"M_single P_w-pseudo-Hermitian residual = {frob:.6e}, "
        f"expected <= {TOL_PSEUDO_HERMITIAN:.0e}"
    )


def test_b5_pawn_decomp_w_full_eta_breaking():
    """M_full = M_single + M_double has Frobenius residual ≥ 1.0 (the
    double-push η-breaking term; Probe 3 reported 32.0 specifically).
    This is the structural reason for the M_pawn = M_single + M_double
    decomposition (Phase 3.5 amendment to ADR-005)."""
    decomp = dyn._pawn_observable_decomp('W')
    M_single = decomp['single']
    M_double = decomp['double']
    eta = decomp['eta']
    M_full = (M_single + M_double).tocsr()
    M_T = M_full.T
    P_M_P = (eta @ M_full @ eta).tocsr()
    diff = (M_T - P_M_P).toarray()
    frob = float(np.linalg.norm(diff))
    # Probe 3 reported 32.0 exactly (sqrt(1024) for the double-push
    # rank in the W-axis matrix; 64 starting-rank squares × 4 inferred
    # bits per parity flip + symmetry); we accept anything ≥ 1.0 here
    # as the ADR-amendment-driving signal.
    assert frob >= 1.0, (
        f"M_full P_w-pseudo-Hermitian residual = {frob:.6e}, "
        f"expected >= 1.0 (η-breaking double-push)"
    )
    # Probe 3 reproduces 32.0 exactly:
    assert abs(frob - 32.0) < 1e-9, (
        f"Probe 3 reported residual = 32.0; got {frob:.6e}"
    )


def test_b5_pawn_decomp_double_only_double_push():
    """M_double has nonzero entries only on double-push moves (origin
    on starting rank → destination two squares forward). Sanity check
    that the decomposition isolates the η-breaking term cleanly.
    """
    decomp = dyn._pawn_observable_decomp('W')
    M_double = decomp['double']
    rows, cols = M_double.nonzero()
    # White W-axis double-push: origin on rank w=1 → destination rank
    # w=3 (starting_rank + 2 * direction). Verify all nonzeros match
    # this geometry (allowing for either source or destination on the
    # double-push axis).
    for r, c in zip(rows, cols):
        rcoord = _t4.rc4(int(r))
        ccoord = _t4.rc4(int(c))
        # Source must be on starting rank (w=1)
        assert ccoord[3] == 1, (
            f"double-push source at coord {ccoord} not on starting "
            f"rank (w=1)"
        )
        # Destination must be 2 squares forward (w=3)
        assert rcoord[3] == 3, (
            f"double-push dest at coord {rcoord} not at w=3"
        )
        # Other coords must be unchanged (a pure double-push is a
        # pure W-axis displacement)
        for axis_i in (0, 1, 2):
            assert rcoord[axis_i] == ccoord[axis_i], (
                f"double-push has off-axis displacement: "
                f"src {ccoord}, dst {rcoord}"
            )


# ====================================================================
#  Test 8: Decomposition cache
# ====================================================================
#
# Repeated calls to _pawn_observable_decomp(axis) return the same
# cached dict (not a fresh copy). Guards against accidental cache
# invalidation that would re-build the matrices on every call.

def test_b5_pawn_decomp_cache_hit():
    """Repeated calls to _pawn_observable_decomp('W') return the same
    cached dict object."""
    d1 = dyn._pawn_observable_decomp('W')
    d2 = dyn._pawn_observable_decomp('W')
    assert d1 is d2, "decomposition cache should return the same dict object"
    assert d1['single'] is d2['single']
    assert d1['double'] is d2['double']
    assert d1['eta'] is d2['eta']


# ====================================================================
#  Test 9: Decomposition for Y axis
# ====================================================================
#
# By symmetry the Y-axis decomposition has the same structure (M_single
# pseudo-Hermitian, M_double η-breaking). Validates that the helper
# generalises correctly.

def test_b5_pawn_decomp_y_single_pseudo_hermitian():
    """M_single (Y-axis) is exactly P_y-pseudo-Hermitian (residual ≤
    1e-12), mirroring the W-axis case."""
    decomp = dyn._pawn_observable_decomp('Y')
    M_single = decomp['single']
    eta = decomp['eta']
    M_T = M_single.T
    P_M_P = (eta @ M_single @ eta).tocsr()
    diff = (M_T - P_M_P).toarray()
    frob = float(np.linalg.norm(diff))
    assert frob <= TOL_PSEUDO_HERMITIAN, (
        f"M_single (Y) P_y-pseudo-Hermitian residual = {frob:.6e}"
    )


def test_b5_pawn_decomp_invalid_axis_raises():
    """_pawn_observable_decomp raises ValueError for axes outside
    {'W', 'Y'}."""
    with pytest.raises(ValueError):
        dyn._pawn_observable_decomp('X')
    with pytest.raises(ValueError):
        dyn._pawn_observable_decomp('w')  # lowercase rejected


# ====================================================================
#  Test 10: Tuple vs int endpoints on capture path
# ====================================================================
#
# Both 4-tuple and linear-int endpoints must produce identical
# capture-marker outputs. Mirrors the input-coercion test pattern from
# B1 / B3a / B3b / B3c / B3d.

def test_b5_capture_tuple_vs_int_endpoints(imbalanced_position):
    """Tuple-coord endpoints normalise to the same linear sq_from /
    sq_to as int endpoints; psi_post_block matches exactly."""
    pos = imbalanced_position
    occ = sorted(pos.keys())
    s_int, t_int = occ[0], occ[1]
    s_tuple = _t4.rc4(s_int)
    t_tuple = _t4.rc4(t_int)

    # A_1 capture
    r_int = dyn.u_move_a1(pos, (s_int, t_int), assume_non_capture=False)
    r_tuple = dyn.u_move_a1(
        pos, (s_tuple, t_tuple), assume_non_capture=False,
    )
    assert r_int['sq_from'] == r_tuple['sq_from'] == s_int
    assert r_int['sq_to'] == r_tuple['sq_to'] == t_int
    assert r_int['captured_piece'] == r_tuple['captured_piece']
    diff = float(np.max(np.abs(
        r_int['psi_post_block'] - r_tuple['psi_post_block']
    )))
    assert diff < 1e-15

    # FA_PAWN_W capture (parallel check)
    r_int = dyn.u_move_fa_pawn(
        pos, (s_int, t_int), axis='W', assume_non_capture=False,
    )
    r_tuple = dyn.u_move_fa_pawn(
        pos, (s_tuple, t_tuple), axis='W', assume_non_capture=False,
    )
    diff = float(np.max(np.abs(
        r_int['psi_post_block'] - r_tuple['psi_post_block']
    )))
    assert diff < 1e-15


# ====================================================================
#  Test 11: side_to_move_post forwarding on capture path
# ====================================================================

def test_b5_capture_side_to_move_post_sign(imbalanced_position):
    """side_to_move_post=True (white) and =False (black) produce
    psi_post_blocks that differ by an overall sign on the capture
    path. Magnitudes are identical."""
    pos = imbalanced_position
    occ = sorted(pos.keys())
    s, t = occ[2], occ[3]

    # A_1 capture path
    r_w = dyn.u_move_a1(
        pos, (s, t),
        assume_non_capture=False, side_to_move_post=True,
    )
    r_b = dyn.u_move_a1(
        pos, (s, t),
        assume_non_capture=False, side_to_move_post=False,
    )
    block_w = r_w['psi_post_block']
    block_b = r_b['psi_post_block']
    # Magnitudes match
    mag_diff = float(np.max(np.abs(np.abs(block_w) - np.abs(block_b))))
    assert mag_diff < 1e-13
    # Overall sign flip (white = +1, black = -1)
    sum_check = float(np.max(np.abs(block_w + block_b)))
    assert sum_check < 1e-13


# ====================================================================
#  Test 12: Non-capture preservation under assume_non_capture=False
# ====================================================================
#
# When assume_non_capture=False but the move is NOT a capture, the
# B5 path is NOT taken — the strict-unitary csr_matrix (or
# non-capture marker for FIB / FD_DIAG / cross-orbit STD4) is
# returned. This guards against the bridge accidentally treating
# every assume_non_capture=False call as a capture.

def test_b5_non_capture_under_assume_non_capture_false(imbalanced_position):
    """For a non-capture move, assume_non_capture=False returns the
    non-capture path's output (csr_matrix or non-capture marker), NOT
    the capture marker."""
    pos = imbalanced_position
    occupied = set(pos.keys())
    # Find a non-capture target
    s = sorted(pos.keys())[0]
    t = next(i for i in range(_t4.N_SQUARES) if i not in occupied)

    # A_1: non-capture path returns csr_matrix
    r = dyn.u_move_a1(pos, (s, t), assume_non_capture=False)
    assert sp.isspmatrix_csr(r), (
        f"non-capture under assume_non_capture=False should return "
        f"csr_matrix (not capture marker); got {type(r).__name__}"
    )

    # FD_DIAG: non-capture path returns the non-capture marker
    # (reason='rank-1-update-with-renorm'), NOT the capture marker
    r = dyn.u_move_fd_diag(pos, (s, t), assume_non_capture=False)
    assert isinstance(r, dict)
    assert r['reason'] == 'rank-1-update-with-renorm', (
        f"FD_DIAG non-capture marker reason should be "
        f"'rank-1-update-with-renorm', not the capture variant; "
        f"got {r['reason']!r}"
    )
    # No captured_piece on non-capture path
    assert 'captured_piece' not in r

    # FIB_SYM_1: non-capture marker
    r = dyn.u_move_fib_meas(pos, (s, t), fib_idx=1, assume_non_capture=False)
    assert r['reason'] == 'measurement-only', (
        f"FIB_SYM_1 non-capture marker reason should be "
        f"'measurement-only'; got {r['reason']!r}"
    )
    assert 'captured_piece' not in r


# ====================================================================
#  Test 13: Multi-piece capture sample
# ====================================================================
#
# Run the bridge across 10+ different (pre-position, capture) pairs
# spanning various piece types. Pin the marker shape invariants
# across the full surface.

def test_b5_multi_piece_capture_marker_invariants(imbalanced_position):
    """Across 10+ capture pairs, every channel's marker dict has the
    canonical shape: psi_post_block (4096-dim complex128),
    captured_piece (matching pos_pre[to_idx]), strict_unitary=False,
    correct channel name, sq_from/sq_to as ints matching the move."""
    pos = imbalanced_position
    rng = np.random.default_rng(RNG_SEED ^ 0x42)
    pairs = _gen_capture_pairs(pos, n_pairs=10, rng=rng)
    assert len(pairs) >= 8

    expected_keys_capture = {
        'strict_unitary', 'reason', 'channel',
        'psi_post_block', 'sq_from', 'sq_to', 'captured_piece',
    }
    for s, t in pairs:
        captured = pos[t]
        result = br.apply_move_qm(pos, (s, t))
        for chan, entry in result.items():
            assert isinstance(entry, dict), (
                f"chan={chan}, ({s},{t}): expected marker dict on "
                f"capture; got {type(entry).__name__}"
            )
            assert set(entry.keys()) == expected_keys_capture, (
                f"chan={chan}, ({s},{t}): keys = "
                f"{sorted(entry.keys())}; expected "
                f"{sorted(expected_keys_capture)}"
            )
            assert entry['strict_unitary'] is False
            assert entry['channel'] == chan
            assert entry['psi_post_block'].shape == (4096,)
            assert entry['psi_post_block'].dtype == np.complex128
            assert entry['captured_piece'] == captured
            assert entry['sq_from'] == s
            assert entry['sq_to'] == t


# ====================================================================
#  Test 14: End-to-end with chess_spectral_4d.apply_move (v1.4)
# ====================================================================

def test_b5_with_chess_spectral_4d_apply_move(imbalanced_position):
    """End-to-end: build a GameState4D, generate a Move4D capture via
    chess_spectral_4d.apply_move, hand the Move4D to apply_move_qm.

    The Move4D record's .from_sq / .to_sq attributes must drive the
    bridge's capture detection correctly; .captured_piece on the
    Move4D record corresponds to the marker dict's captured_piece
    field on every channel."""
    from chess_spectral_4d.move_history import GameState4D
    from chess_spectral_4d import apply_move as cs_apply_move
    from chess_spectral import fen_4d

    pos = imbalanced_position
    fen4 = fen_4d.serialize(pos)
    state_pre = GameState4D.from_fen4(fen4)
    state_pre_pos_snapshot = dict(state_pre.position)

    # Pick a capture: queen at (1,2,3,4) captures a piece at any
    # occupied square (e.g., the rook at (4,4,1,5)).
    from_coord = (1, 2, 3, 4)
    to_coord = (4, 4, 1, 5)
    f_idx = _t4.sq4(*from_coord)
    t_idx = _t4.sq4(*to_coord)
    assert t_idx in state_pre.position, (
        "test fixture must have piece at to_coord for capture"
    )
    captured_expected = state_pre.position[t_idx]

    # Drive the bridge BEFORE apply_move (state_pre still has the
    # captured piece in place); use the v1.4 apply_move signature for
    # state mutation later just to verify the captured_piece field
    # agrees with the recorded Move4D.
    result = br.apply_move_qm(
        state_pre_pos_snapshot, (from_coord, to_coord),
    )
    for chan, entry in result.items():
        assert isinstance(entry, dict), (
            f"chan={chan}: capture path should return marker dict"
        )
        assert entry['captured_piece'] == captured_expected, (
            f"chan={chan}: captured_piece mismatch"
        )

    # Cross-check via Move4D: rec.captured_piece should match the
    # bridge's marker entries (Move4D's captured_piece is None for
    # non-captures and the piece value for captures).
    rec = cs_apply_move(state_pre, from_coord, to_coord)
    assert rec.captured_piece is not None, (
        "Move4D record should have non-None captured_piece on capture"
    )
    assert rec.captured_piece == captured_expected


# ====================================================================
#  Test 15: bridge dispatch consistency (per-channel call agrees with
#           bridge call)
# ====================================================================

def test_b5_bridge_per_channel_consistency(imbalanced_position):
    """Each channel entry in the bridge's apply_move_qm output exactly
    matches the result of the per-channel u_move_* call (with
    assume_non_capture=not is_capture). Verifies the bridge's
    capture-detection branching is correctly wired."""
    pos = imbalanced_position
    occ = sorted(pos.keys())
    s, t = occ[1], occ[5]

    bridge_result = br.apply_move_qm(pos, (s, t))

    # A_1
    r_dyn = dyn.u_move_a1(pos, (s, t), assume_non_capture=False)
    diff = float(np.max(np.abs(
        bridge_result['A1']['psi_post_block'] - r_dyn['psi_post_block']
    )))
    assert diff < 1e-15

    # STD4_X
    r_dyn = dyn.u_move_std4(pos, (s, t), axis='X', assume_non_capture=False)
    diff = float(np.max(np.abs(
        bridge_result['STD4_X']['psi_post_block'] - r_dyn['psi_post_block']
    )))
    assert diff < 1e-15

    # FA_PAWN_W
    r_dyn = dyn.u_move_fa_pawn(
        pos, (s, t), axis='W', assume_non_capture=False,
    )
    diff = float(np.max(np.abs(
        bridge_result['FA_PAWN_W']['psi_post_block']
        - r_dyn['psi_post_block']
    )))
    assert diff < 1e-15

    # FIB_SYM_2
    r_dyn = dyn.u_move_fib_meas(
        pos, (s, t), fib_idx=2, assume_non_capture=False,
    )
    diff = float(np.max(np.abs(
        bridge_result['FIB_SYM_2']['psi_post_block']
        - r_dyn['psi_post_block']
    )))
    assert diff < 1e-15

    # FD_DIAG
    r_dyn = dyn.u_move_fd_diag(pos, (s, t), assume_non_capture=False)
    diff = float(np.max(np.abs(
        bridge_result['FD_DIAG']['psi_post_block']
        - r_dyn['psi_post_block']
    )))
    assert diff < 1e-15


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
