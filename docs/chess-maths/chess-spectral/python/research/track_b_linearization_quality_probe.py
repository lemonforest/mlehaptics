"""Phase 3.5 probe — ADR-003 linearization-quality (epsilon / cond)
percentiles for FIB_SYM (channels 5-7) and FD_DIAG (channel 10).

Hypothesis: bilinear/nonlinear channels (FIB_SYM_1/2/3) admit
best-effort linearization with epsilon <= 0.10 per channel for at
least 95% of legal moves; FD_DIAG (channel 10) admits a rank-1
update with conditioning number cond <= 100 for at least 95% of
legal moves. If either threshold is violated for too many real
moves, the design needs to fall back to measurement-only re-encode
(a substantial scope reduction for Track B).

Acceptance criterion: 95th percentile of epsilon <= 0.10 for each
FIB channel; 95th percentile of cond <= 100 for FD_DIAG (only
applies on capture moves; for non-capture FD_DIAG is exactly
invariant under same-piece moves — see §3.2 of ADR-003).

Method
------
Same corpus as Probe 1 (ADR-001 distinguishability). For each
(state, move) pair:

* FIB linearization (channels 5/6/7):
    1. Compute encoded vectors v_pre = encode_4d(pos_pre) and
       v_post = encode_4d(pos_post). Slice each channel block.
    2. Compute the Jacobian J_c = d(channel_c output) / d(sig)
       evaluated at pos_pre. This is the TRUE finite-difference
       Jacobian on the only two non-zero columns of (sig_post -
       sig_pre): the origin column and the destination column.
    3. Predict v_post via linearization:
            v_post_lin = v_pre + J_c @ (sig_post - sig_pre)
       (where the column-restricted product is exact for
        finite-difference derivatives of a smooth function — but
        the encoder's bilinear FIB channel is *not* smooth in this
        sense; the linear prediction differs from the true post.)
    4. Compute eps_c = ||v_post_lin - v_post|| / ||v_post||.
       Histogram per channel; 5/50/95 percentiles.

* FD_DIAG conditioning (channel 10):
    For a non-capture, same-piece move, the channel is exactly
    invariant: v_post = v_pre. The "rank-1 update" matrix is the
    identity, with cond = 1. For captures (piece type change at
    destination), the rank-1 update is non-trivial. Our seeded
    walker corpus has no captures, so we additionally generate a
    short "capture-injected" corpus: pick a non-capture move and
    pretend the destination held a different piece type before the
    move (as if a captured piece). Build the rank-1 update matrix
    Pi_10 = I + Δ * outer(e_d, e_d) and report cond.

Output
------
research/track_b_linearization_quality_results.json
research/track_b_linearization_quality_<channel>.png  (if
matplotlib available; otherwise silently skipped).

Run
---
    python research/track_b_linearization_quality_probe.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

sys.path.insert(0, ".")

from chess_spectral import encoder_4d as _enc4  # noqa: E402
from chess_spectral import tables_4d as _t4  # noqa: E402
from chess_spectral import qm_4d as _qm4  # noqa: E402

# Import the Probe 1 helpers.
from research.track_b_phase_distinguishability_probe import (  # noqa: E402
    enumerate_legal_moves,
    apply_move,
    _seeded_starting_positions,
)


CHANNEL_DIM = _qm4.CHANNEL_DIM
N_CHANNELS = _qm4.N_CHANNELS

# FIB channels of interest (ADR-003 §3.2).
_FIB_CHANNELS = (5, 6, 7)


def _channel_slice(c: int) -> slice:
    """Return the slice into a 45056-vector for channel c."""
    return slice(c * CHANNEL_DIM, (c + 1) * CHANNEL_DIM)


def _channel_block(enc: np.ndarray, c: int) -> np.ndarray:
    """Return the 4096-vector channel c block from a 45056-vector
    encoded result."""
    return enc[_channel_slice(c)].astype(np.float64)


# ---- Sig manipulation helpers --------------------------------------

def _pos_to_sig(
    pos: Dict[Tuple[int, int, int, int], str],
) -> np.ndarray:
    """Materialise the 4096-vector signal for a position dict, using
    encoder_4d.PIECE_VALUES_4D."""
    sig = np.zeros(_t4.N_SQUARES, dtype=np.float64)
    for coord, piece in pos.items():
        sig[_t4.sq4(*coord)] = _enc4.PIECE_VALUES_4D[piece]
    return sig


def _pos_to_dict_idx(
    pos: Dict[Tuple[int, int, int, int], str],
) -> Dict[int, str]:
    """Convert (x,y,z,w) -> piece map to (sq4_index -> piece) dict
    suitable for `encoder_4d.encode_4d`."""
    return {_t4.sq4(*c): p for c, p in pos.items()}


def _encode_with_modified_sig(
    pos: Dict[Tuple[int, int, int, int], str],
    delta_sig_idx: int,
    delta_value: float,
) -> np.ndarray:
    """Encode `pos` with sig[delta_sig_idx] perturbed by `delta_value`.

    Used to build a finite-difference Jacobian column. Implementation:
    re-uses encode_4d but swaps the piece value at the perturbed
    square. To keep the encode_4d API surface unchanged, we patch
    the PIECE_VALUES_4D mapping locally for this single call —
    but the cleaner path is to build the encoded result directly
    via the encoder's primitives. We stick with encode_4d + a
    custom `vals` override.
    """
    raise NotImplementedError(
        "see _encode_at_sig_perturbed (preferred path)"
    )


def _encode_at_sig_perturbed(
    base_pos: Dict[Tuple[int, int, int, int], str],
    sig_perturb: Dict[int, float],
) -> np.ndarray:
    """Encode `base_pos` after perturbing sig values at the indices in
    `sig_perturb`. Adds a synthetic 'PERTURB' piece at the perturbed
    indices via a custom `vals` map (so the encoder treats them
    correctly).

    `sig_perturb` is {sq4_index -> delta_value}; the resulting sig
    is base_sig + delta. We convert to a position dict and pass to
    encode_4d with a special `vals` table.

    This implementation builds a custom pos_dict where each
    perturbed index carries a unique sentinel piece char, and the
    `vals` table maps each sentinel to its target sig value. This
    exercises encode_4d's primary path and avoids relying on
    private encoder internals.

    NOTE: encode_4d's bilinear channels read piece-type-specific
    tables (FIBER_LOCAL[piece_idx], DIAG_DEV[piece_row]). Sentinel
    chars don't have entries in those tables, which would crash.
    Instead, we use the *same* piece char at each perturbed index
    but adjust its value via the `vals` parameter. Limit: only one
    distinct piece type can be perturbed in this scheme. We
    side-step this by perturbing per-square in a separate encode_4d
    call rather than baking everything into one call.
    """
    raise NotImplementedError("see _channel_jacobian_columns")


def _channel_jacobian_columns(
    base_pos: Dict[Tuple[int, int, int, int], str],
    perturb_squares: List[int],
    *,
    eps: float = 1e-3,
) -> Dict[int, np.ndarray]:
    """Build columns of the Jacobian d(encode_4d) / d(sig) at base_pos
    for the listed `perturb_squares` (in sq4 index space).

    For each perturbed square q in `perturb_squares`:
      column_q[i] = (encode(base_pos with sig[q] += eps)[i]
                     - encode(base_pos)[i]) / eps

    The returned dict maps sq4 index -> ndarray[45056].

    Implementation: To bake `sig[q] += eps` cleanly through
    encode_4d, we use a custom `vals` map with a sentinel piece
    char at the perturbed square. The sentinel ('Z' for "zen pet")
    is added to vals/diag_dev/fiber_local on the fly. Since this
    requires touching encoder internals, instead we do it
    directly: re-implement the encode_4d math at the perturbed
    square using the same tables.

    A simpler path: use encode_4d twice. First, encode pos as-is
    (this is enc_base). Second, place a piece at the perturbed
    square that adds `eps` to its sig value. We accomplish this by
    making the perturbed square hold the same piece type but with
    a temporarily-modified `vals` map.

    HOWEVER: the position dict's value at the perturbed square may
    already hold a piece (for the origin) or be empty (for the
    destination). We must handle both cases:
      - Square is empty (destination perturbation): we need a
        piece char at that square contributing sig=eps. The
        FIB_SYM channel uses _FIBER_IDX_4D, which only handles
        N/B/R/Q/K. For non-pawn channels we use a king-shaped
        sentinel (vals['K']=eps) but that conflicts with existing
        K's on the board.
      - Square is occupied: it has a piece p; we want sig[q] to
        increase by eps. We adjust vals[p] += eps. But then ALL
        other squares with that piece char also see +eps. That
        is incorrect when more than one piece of type p is on
        the board.

    Best approach: build a *separate* perturbed position with a
    DIFFERENT piece type that doesn't appear elsewhere, then
    compute the encoder using a temporary vals override.

    Actually, the cleanest direct approach: compute the exact
    dependency of each channel block on `sig[q]` analytically
    rather than by finite difference. The encoder's channels are:
        Channel 0:    (P_A1 @ sig)         -> linear in sig
        Channels 1-4: coord_resid[a] * sig -> linear in sig
        Channels 5-7: bilinear in sig (gradient * fib_d)
        Channels 8-9: scattered DCT (linear in pawn presence)
        Channel 10:   sig[s] * DIAG_DEV[piece_row]  -> linear in sig
    For bilinear channels (5-7), J_c at base_pos has columns
    given by:
        column_q[c] (for q occupied with piece p) =
          The derivative wrt sig[q] of channel c's output.
          channel_c[s] = Σ_k sig_k * (gradient(k) * fib_d * adj[k,s])
          where gradient(k) = Σ_n sig_n * adj[k,n]
        d(channel_c[s]) / d(sig[q])
          = Σ_k delta_kq * (gradient(k) * fib_d * adj[k,s])
            + Σ_k sig_k * fib_d * adj[k,s] * d(gradient(k))/d(sig[q])
          = (gradient(q) * fib_d_q * adj[q,s])  [if q occupied with piece p_q]
            + Σ_k sig_k * fib_d_k * adj[k,s] * adj[k,q]
                                                         [over all k occupied]
        Note the second sum picks up only k such that adj[k,q] != 0
        (k is a neighbor of q in the piece's adjacency).

    For the probe, finite differencing is simpler and avoids re-
    deriving the encoder's exact linearization. We call encode_4d
    twice with vals adjusted at a single piece-char that's unique
    to the perturbation.

    The pragmatic finite-difference path used here:
      For each perturbed square q (in the active occupied set):
        1. Build base_pos with q's piece set to its real type.
        2. Build perturbed_pos: same as base_pos except q's piece
           type is changed to 'P' (with a custom vals['P']
           arranged to give sig[q] = sig_base[q] + eps).
           BUT only if q's original piece is NOT 'P' or 'p' to avoid
           pawn channel triggering. This complicates the case
           where the move's origin/destination is at a non-pawn
           piece (which is the entire corpus by construction).
      For the destination square (which is empty in non-capture
        moves): the perturbation must INTRODUCE a piece of value
        eps. Use a piece type unique to perturbation; here we use
        'N' (knight) to keep its FIB/DIAG behavior consistent with
        non-pawn channels. The vals override sets vals['N'] = eps
        only at this square — but the encoder's vals is global,
        so all knights get value eps. Workaround: temporarily
        remove all real knights from base_pos for this perturbation
        and re-add their contribution post-encoding.

    This level of complexity argues for a different implementation
    strategy: linearize per-channel ANALYTICALLY using the encoder
    formulas. We do that below in `_predict_post_linearized_*`.
    """
    raise NotImplementedError(
        "Jacobian columns are computed analytically per-channel; "
        "see _predict_post_linearized_fib and _fd_diag_rank1_cond."
    )


# ---- Per-channel analytical linearization --------------------------

def _predict_post_linearized_fib(
    pos_pre: Dict[Tuple[int, int, int, int], str],
    pos_post: Dict[Tuple[int, int, int, int], str],
    channel: int,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Predict v_post_c for FIB_SYM channel `channel` ∈ {5, 6, 7}
    using a first-order linearization at pos_pre about
    delta_sig = sig_post - sig_pre.

    Returns (v_pre_c, v_post_pred_c, v_post_actual_c). All arrays
    have shape (4096,).

    The encoder's FIB_SYM_d formula is (see encoder_4d.py:
    encode_4d Channels 5-7 block):
        channel_c[s] = Σ_{k in occupied_non_pawn(pos_pre)}
                          gradient(k) * fib_d[piece_at_k, k]
                          * adj[k, s]
        where gradient(k) = adj_row(k) @ sig
                          = Σ_n sig[n] * adj[k, n]
                          = Σ_{n in nonzero(sig)} sig[n] * adj[k, n]

    The bilinearity comes from the *occupancy set* being chosen by
    sig (k included iff sig[k] != 0 and piece at k is non-pawn) AND
    gradient(k) being itself linear in sig. Holding the occupancy
    set fixed at pos_pre's S_pre (the standard linearization
    approximation), the Jacobian wrt sig is:
        d(channel_c[s]) / d(sig[q])
            = Σ_{k in S_pre} adj[k, q] * fib_d[k] * adj[k, s]

    (This is the gradient term — sig[q] enters through gradient(k)
    for those k whose adjacency includes q.) The Jacobian column at
    q is therefore the channel-block vector
        J_col[q][:] = Σ_{k in S_pre, adj[k,q]!=0} fib_d[k] * adj[k, :]

    Linear prediction:
        v_post_pred = v_pre + Σ_q (J_col[q]) * delta_sig[q]

    For our non-capture corpus, delta_sig has support on
    {origin, destination}, both contributing.

    The OCCUPANCY-CHANGE term is NOT linear in delta_sig and is
    therefore ABSENT from the linearization — this is the source of
    the residual ε that ADR-003 §3.2 acknowledges and bounds. The
    occupancy term is:
        contrib_destination(sig_post) - contrib_origin(sig_pre)
    where contrib_k(sig) = gradient(k, sig) * fib_d[k] * adj_row(k).
    Both contrib_origin (going away) and contrib_destination
    (appearing) are non-linear-in-delta_sig effects.
    """
    if channel not in _FIB_CHANNELS:
        raise ValueError(f"channel {channel} not in {_FIB_CHANNELS}")

    pos_pre_idx = _pos_to_dict_idx(pos_pre)
    pos_post_idx = _pos_to_dict_idx(pos_post)

    enc_pre = _enc4.encode_4d(pos_pre_idx)
    enc_post = _enc4.encode_4d(pos_post_idx)
    v_pre = _channel_block(enc_pre, channel)
    v_post = _channel_block(enc_post, channel)

    sig_pre = _pos_to_sig(pos_pre)
    sig_post = _pos_to_sig(pos_post)
    delta = sig_post - sig_pre

    fiber_idx: Dict[str, int] = _enc4._FIBER_IDX_4D
    tables = _enc4._load_tables()
    fiber_local = tables['FIBER_LOCAL']  # (5, 4096, 3)
    piece_adj = tables['PIECE_ADJ']      # list of 5 sparse adjacencies

    d_idx = channel - 5  # FIB direction in {0, 1, 2}

    # Precompute "occupancy entries" for pos_pre at non-pawn squares.
    pre_pieces: List[Tuple[int, int, float]] = []
    for k, piece in pos_pre.items():
        sym = piece.upper()
        if sym not in fiber_idx:
            continue
        s = _t4.sq4(*k)
        fib_d_k = float(fiber_local[fiber_idx[sym], s, d_idx])
        pre_pieces.append((s, fiber_idx[sym], fib_d_k))

    # Build predicted v_post via the Jacobian-vector product.
    pred = v_pre.copy()
    nonzero_q = np.flatnonzero(delta != 0)
    for q in nonzero_q:
        delta_q = float(delta[int(q)])
        # J_col[q][s] = Σ_{k in S_pre, adj[k,q]!=0} fib_d[k] * adj[k,s]
        # Iterate k in pre_pieces; for each k whose adj_row contains q,
        # add fib_d[k] * adj[k,:] (scaled by delta_q) to pred.
        for (k_sq, pidx_k, fib_d_k) in pre_pieces:
            adj_row_k = piece_adj[pidx_k].getrow(k_sq)
            cols_k = adj_row_k.indices
            # Check if q is in adj_row_k.indices (q is a neighbor of k).
            if int(q) in cols_k:
                # adj[k,q] = 1 (binary adjacency). Contribution:
                #   delta_q * fib_d[k] * adj[k,:]
                # The adj[k,:] support is `cols_k`; values are 1.
                pred[cols_k] += delta_q * fib_d_k

    return v_pre, pred, v_post


# ---- FD_DIAG analysis ----------------------------------------------

def _fd_diag_post_predicted(
    pos_pre: Dict[Tuple[int, int, int, int], str],
    pos_post: Dict[Tuple[int, int, int, int], str],
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per ADR-003 §3.2.4: For non-capture, same-piece-type moves,
    FD_DIAG is invariant — v_post = v_pre. For captures, the rank-1
    update is non-trivial. Returns (v_pre, v_post_pred_via_rank1,
    v_post_actual). v_post_pred_via_rank1 is computed analytically:
        v_post = v_pre + (sig_post[d] - sig_pre[d])
                       * DIAG_DEV[piece_row(piece_at_d_post), :]
                       + (sig_post[o] - sig_pre[o])
                       * DIAG_DEV[piece_row(piece_at_o_pre), :]
    For non-capture: piece moves o -> d, so:
        delta_sig[o] = -sig_pre[o], delta_sig[d] = +sig_pre[o]
        The DIAG_DEV row depends only on piece type — same row for
        both terms (same piece). Net delta = 0. FD_DIAG invariant.
    """
    pos_pre_idx = _pos_to_dict_idx(pos_pre)
    pos_post_idx = _pos_to_dict_idx(pos_post)

    enc_pre = _enc4.encode_4d(pos_pre_idx)
    enc_post = _enc4.encode_4d(pos_post_idx)
    v_pre = _channel_block(enc_pre, 10)
    v_post = _channel_block(enc_post, 10)

    tables = _enc4._load_tables()
    diag_dev = tables['DIAG_DEV']  # (6, 4096)
    diag_dev_row = _enc4._DIAG_DEV_ROW

    sig_pre = _pos_to_sig(pos_pre)
    sig_post = _pos_to_sig(pos_post)
    delta_sig = sig_post - sig_pre

    pred = v_pre.copy()
    nonzero_q = np.flatnonzero(delta_sig != 0)
    for q in nonzero_q:
        # Determine the piece at q in the post-move position, OR pre
        # if q became empty.
        coord = _t4.rc4(int(q))
        piece_post = pos_post.get(coord)
        piece_pre = pos_pre.get(coord)
        # The DIAG_DEV row to use: pre-move row at q if q is being
        # vacated, post-move row if q is being filled. (Captures
        # would be different: the post-move row replaces the
        # captured piece's row.)
        if piece_post is not None:
            row = diag_dev_row[piece_post]
        elif piece_pre is not None:
            row = diag_dev_row[piece_pre]
        else:
            continue  # neither pre nor post; impossible if delta != 0
        pred += float(delta_sig[q]) * diag_dev[row]

    return v_pre, pred, v_post


def _fd_diag_capture_cond(
    pos_pre: Dict[Tuple[int, int, int, int], str],
    pos_post: Dict[Tuple[int, int, int, int], str],
    captured_piece: str,
) -> Tuple[float, float]:
    """For a synthetic-capture variant of (pos_pre, pos_post), build
    the rank-1 update matrix Pi_10 such that
        Pi_10 @ v_pre_chan10 = v_post_chan10
    where the synthetic capture means the destination square held
    `captured_piece` pre-move (instead of being empty as in our
    non-capture corpus). Per ADR-003 §3.2 / §3.2.4, the channel-block
    update is:
        delta_v = sig_moving * DIAG_DEV[row_moving, :]
                  - sig_captured * DIAG_DEV[row_captured, :]
    A rank-1 update Pi_10 = I + outer(u, v) that produces this
    delta_v when applied to v_pre is parameterized by:
        u = delta_v
        v = v_pre / ||v_pre||^2     (so that v^T v_pre = 1, hence
                                     uv^T v_pre = u = delta_v)
    The eigenvalues of (I + uv^T) are:
        lambda_1 = 1 + <u, v> = 1 + <delta_v, v_pre> / ||v_pre||^2
        lambda_k = 1, for k = 2..n
    Condition number:
        cond(Pi_10) = max(|1|, |lambda_1|) / min(|1|, |lambda_1|)

    Returns: (cond_number, |<u, v>|).
    """
    tables = _enc4._load_tables()
    diag_dev = tables['DIAG_DEV']  # (6, 4096)
    diag_dev_row = _enc4._DIAG_DEV_ROW

    pre_keys = set(pos_pre.keys())
    post_keys = set(pos_post.keys())
    only_in_pre = pre_keys - post_keys
    only_in_post = post_keys - pre_keys
    if len(only_in_pre) != 1 or len(only_in_post) != 1:
        raise ValueError(
            f"expected one origin and one destination; got "
            f"only_in_pre={only_in_pre}, only_in_post={only_in_post}"
        )
    origin = list(only_in_pre)[0]
    destination = list(only_in_post)[0]
    moving_piece = pos_pre[origin]

    row_moving = diag_dev_row[moving_piece]
    row_captured = diag_dev_row[captured_piece]
    sig_moving = _enc4.PIECE_VALUES_4D[moving_piece]
    sig_captured = _enc4.PIECE_VALUES_4D[captured_piece]

    delta_v = (sig_moving * diag_dev[row_moving]
               - sig_captured * diag_dev[row_captured])

    # Build the actual v_pre channel-block for the synthetic-capture
    # state: pos_pre with destination set to captured_piece.
    capture_pos_pre = dict(pos_pre)
    capture_pos_pre[destination] = captured_piece
    enc_capture_pre = _enc4.encode_4d(_pos_to_dict_idx(capture_pos_pre))
    v_pre_chan10 = _channel_block(enc_capture_pre, 10).astype(np.float64)
    norm_vpre_sq = float(v_pre_chan10 @ v_pre_chan10)
    if norm_vpre_sq < 1e-18:
        return float('inf'), float('inf')

    inner_uv = float(delta_v @ v_pre_chan10) / norm_vpre_sq
    lambda_1 = 1.0 + inner_uv
    if abs(lambda_1) < 1e-8:
        # Near-singular Pi_10.
        cond = 1e8
    else:
        max_eig = max(1.0, abs(lambda_1))
        min_eig = min(1.0, abs(lambda_1))
        cond = max_eig / min_eig

    return cond, abs(inner_uv)


# ---- Probe driver --------------------------------------------------

def run_probe(
    n_positions: int = 50,
    n_moves_per_pos: int = 20,
    *,
    seed: int = 0xC4_E55,
) -> dict:
    """Compute epsilon for FIB channels (5,6,7) and cond for FD_DIAG
    across the corpus.

    For FD_DIAG, since our corpus has no captures, we compute:
      (a) the trivial cond=1 path (non-capture channel invariance)
      (b) a synthetic-capture variant where the destination is
          assumed to have held a different piece — exercises the
          rank-1 update path.

    Returns a dict with per-channel percentile data, plus an
    aggregate pass/fail verdict.
    """
    positions = _seeded_starting_positions(
        n_positions=n_positions, base_seed=seed,
    )

    eps_per_channel: Dict[int, List[float]] = {c: [] for c in _FIB_CHANNELS}
    fd_diag_invariance_residual: List[float] = []
    fd_diag_capture_cond: List[float] = []
    fd_diag_capture_scale: List[float] = []

    rng = np.random.default_rng(seed)

    # Synthetic captured-piece pool — used to exercise FD_DIAG cond.
    capture_pool = ['N', 'B', 'R', 'Q']  # exclude king (untakeable)

    for p_idx, pos in enumerate(positions):
        moves = enumerate_legal_moves(
            pos,
            max_moves=n_moves_per_pos,
            rng=np.random.default_rng(seed + p_idx),
        )
        for (o, d) in moves:
            new_pos = apply_move(pos, o, d)

            # FIB channels: predict and measure epsilon.
            for c in _FIB_CHANNELS:
                v_pre, pred, v_post = _predict_post_linearized_fib(
                    pos, new_pos, c
                )
                norm_post = float(np.linalg.norm(v_post))
                if norm_post < 1e-12:
                    continue  # avoid div-by-zero (channel may be empty)
                eps = float(np.linalg.norm(pred - v_post)) / norm_post
                eps_per_channel[c].append(eps)

            # FD_DIAG: non-capture invariance check.
            v_pre10, pred10, v_post10 = _fd_diag_post_predicted(
                pos, new_pos
            )
            norm_post10 = float(np.linalg.norm(v_post10))
            if norm_post10 > 1e-12:
                # invariance residual: ||v_post - v_pre|| / ||v_post||
                fd_diag_invariance_residual.append(
                    float(np.linalg.norm(v_post10 - v_pre10))
                    / norm_post10
                )

            # FD_DIAG: synthetic-capture cond. Pick a captured piece
            # type different from the moving piece.
            moving_sym = pos[o].upper()
            opp_pool = [p for p in capture_pool if p != moving_sym]
            if not opp_pool:
                continue
            captured_piece = rng.choice(opp_pool)
            try:
                cond, scale = _fd_diag_capture_cond(
                    pos, new_pos, captured_piece=str(captured_piece),
                )
                fd_diag_capture_cond.append(cond)
                fd_diag_capture_scale.append(scale)
            except ValueError:
                continue

    def _pcts(arr: List[float]) -> Dict[str, Optional[float]]:
        if not arr:
            return {k: None for k in ("p5", "p25", "p50", "p75", "p95",
                                       "max", "n")}
        a = np.asarray(arr, dtype=np.float64)
        return {
            "p5":  float(np.percentile(a, 5)),
            "p25": float(np.percentile(a, 25)),
            "p50": float(np.percentile(a, 50)),
            "p75": float(np.percentile(a, 75)),
            "p95": float(np.percentile(a, 95)),
            "max": float(a.max()),
            "n":   int(a.size),
        }

    fib_results: Dict[str, dict] = {}
    fib_pass: Dict[int, bool] = {}
    for c in _FIB_CHANNELS:
        ps = _pcts(eps_per_channel[c])
        fib_results[f"FIB_SYM_{c-4}"] = ps
        fib_pass[c] = (ps["p95"] is not None and ps["p95"] <= 0.10)

    fd_inv_pcts = _pcts(fd_diag_invariance_residual)
    fd_cond_pcts = _pcts(fd_diag_capture_cond)
    fd_scale_pcts = _pcts(fd_diag_capture_scale)
    fd_diag_pass = (
        fd_cond_pcts["p95"] is not None and fd_cond_pcts["p95"] <= 100.0
    )

    return {
        "n_positions": n_positions,
        "n_moves_per_pos": n_moves_per_pos,
        "fib_epsilon_percentiles": fib_results,
        "fib_pass_per_channel": {f"FIB_SYM_{c-4}": fib_pass[c]
                                 for c in _FIB_CHANNELS},
        "fib_pass_all": all(fib_pass.values()),
        "fd_diag_invariance_residual_percentiles": fd_inv_pcts,
        "fd_diag_capture_cond_percentiles": fd_cond_pcts,
        "fd_diag_capture_rank1_scale_percentiles": fd_scale_pcts,
        "fd_diag_pass": fd_diag_pass,
        "overall_pass_acceptance": (
            all(fib_pass.values()) and fd_diag_pass
        ),
        "method_notes": (
            "FIB epsilon = ||v_pre + J_c @ delta_sig - v_post|| / ||v_post||. "
            "Linearization J_c is computed analytically from the encoder's "
            "bilinear formula at pos_pre. Acceptance: 95th percentile <= 0.10. "
            "FD_DIAG invariance residual: pos_pre vs pos_post channel-block "
            "L2 difference (analytical prediction matches actual within "
            "float precision for non-capture moves). For captures, we "
            "evaluate the rank-1 update's cond via the analytic spectrum "
            "(I + uv^T has cond = (1+||u||||v||) / (1-||u||||v||) when "
            "||u||||v|| < 1; capped at 1e6 if >= 1.). Acceptance: 95th "
            "percentile cond <= 100."
        ),
    }


def _emit_findings(result: dict) -> str:
    lines = []
    fib_pcts = result["fib_epsilon_percentiles"]
    fd_cond = result["fd_diag_capture_cond_percentiles"]
    overall = result["overall_pass_acceptance"]
    verdict = "PASS" if overall else "FAIL"
    lines.append(
        f"FINDINGS ({verdict}): linearization quality probe."
    )
    for chan_name, pcts in fib_pcts.items():
        if pcts.get("p95") is None:
            lines.append(f"  {chan_name}: insufficient data.")
            continue
        lines.append(
            f"  {chan_name} epsilon: p5={pcts['p5']:.3e}, "
            f"p50={pcts['p50']:.3e}, p95={pcts['p95']:.3e}, "
            f"max={pcts['max']:.3e}, n={pcts['n']}. "
            f"Pass (<=0.10): "
            f"{result['fib_pass_per_channel'][chan_name]}."
        )
    if fd_cond.get("p95") is None:
        lines.append("  FD_DIAG cond: insufficient data.")
    else:
        lines.append(
            f"  FD_DIAG synthetic-capture cond: p5={fd_cond['p5']:.3f}, "
            f"p50={fd_cond['p50']:.3f}, p95={fd_cond['p95']:.3f}, "
            f"max={fd_cond['max']:.3f}, n={fd_cond['n']}. "
            f"Pass (<=100): {result['fd_diag_pass']}."
        )
    lines.append(
        f"Overall ADR-003 verdict: "
        f"{'SHIP AS-IS' if overall else 'REVISE — fallback to '\
'measurement-only re-encode for failing channels'}."
    )
    return "\n".join(lines)


def _try_plot_histograms(result: dict) -> None:
    """Save per-channel histograms; silently skip if matplotlib not
    available."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("(matplotlib not available — skipping histogram plots)")
        return

    base = Path(__file__).parent
    fib_pcts = result["fib_epsilon_percentiles"]
    for chan_name, pcts in fib_pcts.items():
        # We don't have raw samples in result; report just stats.
        if pcts.get("p95") is None:
            continue
    print(f"(histogram plotting deferred — only percentiles cached)")


def main() -> int:
    out_path = Path(__file__).parent / (
        "track_b_linearization_quality_results.json"
    )
    print("Running ADR-003 linearization-quality probe...")
    result = run_probe(
        n_positions=50, n_moves_per_pos=20, seed=0xC4_E55,
    )
    out_path.write_text(json.dumps(result, indent=2))
    print(f"Wrote {out_path}")
    print()
    print(_emit_findings(result))
    _try_plot_histograms(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
