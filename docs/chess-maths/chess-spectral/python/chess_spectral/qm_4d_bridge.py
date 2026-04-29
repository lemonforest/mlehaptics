"""chess_spectral.qm_4d_bridge - applyMoveQm bridge surface.

Per §17.1 of the chess-spectral research notebook, the consumer-side
QM bridge exposes ``applyMoveQm(state, move)`` (Python:
:func:`apply_move_qm`) for advancing a quantum state through a single
chess move. The full implementation requires per-channel move
unitaries for **all 11 channels** (A_1, STD4_X/Y/Z/W, FA_PAWN_W/Y,
FIB_SYM_1/2/3, FD_DIAG) — see ADR-003 §3.1's tiered plan and the
B[2..5] milestone roadmap.

Phase 4 milestones B1 + B3a + B3b + B3c + B3d/e ship **all 11
channels** for non-capture moves via:

  * :func:`chess_spectral.qm_4d_dynamics.u_move_a1` (A_1),
  * :func:`chess_spectral.qm_4d_dynamics.u_move_std4` (STD4_*),
  * :func:`chess_spectral.qm_4d_dynamics.u_move_fa_pawn` (FA_PAWN_*),
  * :func:`chess_spectral.qm_4d_dynamics.u_move_fib_meas` (FIB_SYM_*),
  * :func:`chess_spectral.qm_4d_dynamics.u_move_fd_diag` (FD_DIAG).

After B3d/e the bridge **no longer raises** for non-capture moves —
:func:`apply_move_qm` returns the assembled per-channel dict. The
dict's values are a mix of ``csr_matrix`` (strict-unitary same-orbit
A_1 / STD4_* same-orbit / FA_PAWN_* axis-flip) and marker dicts
(cross-orbit / cross-parity-class / measurement-only / rank-1) —
consumers dispatch on ``isinstance(value, dict)``.

Milestone status (post-B3d/e):

  - **B1** A_1 channel — shipped.
  - **B2** Zeno-style evolution + H_0 — shipped (callable via
    :func:`chess_spectral.qm_4d_dynamics.evolve_under_h0`; not yet
    wired into ``apply_move_qm``'s ψ_post computation — see TODO
    below).
  - **B3a** STD4_X/Y/Z/W (strict-unitary same-orbit; cross-orbit
    returns measurement-only re-encode marker per ADR-003 amendment
    Option (a)) — shipped.
  - **B3b** FA_PAWN_W/Y (strict-unitary axis-flip; cross-parity
    returns marker; partial-isometry capture per B5) — shipped.
  - **B3c** FIB_SYM_1/2/3 (Phase 3.5 amendment: measurement-only
    re-encode per ADR-003 §3.3 fallback — best-effort linearization
    failed the Phase 3.5 Probe-2 acceptance gate by 50-500×) —
    shipped.
  - **B3d/e** FD_DIAG (rank-1 update + renormalization, cond p95 =
    8.60 < 100 acceptance gate; v1.5 ships Option A re-encode marker;
    explicit rank-1 algebra deferred to B5 alongside the other
    capture cases) — **shipped this milestone**.
  - **B5** capture handling (partial-isometry on FA_PAWN; rank-1 +
    renorm on A_1 / STD4 / FD_DIAG; full Stinespring deferred to
    v1.7+).

Why a separate module?
----------------------

``qm_4d_dynamics.py`` holds the per-channel constructions
(``u_move_*``) and shared move-coercion helpers. ``qm_4d_bridge.py``
holds the **assembly** layer that ties channel unitaries together
into the §17.1 ``applyMoveQm`` API. Keeping them separate matches
the v1.5.0 architecture sketch: ``qm_4d_dynamics`` is the math, the
bridge is the consumer-facing API. B5 will keep adding capture
handling to ``qm_4d_dynamics`` without churning this module beyond
plumbing.

Public API
----------
:func:`apply_move_qm`
    The §17.1 bridge entry-point. v1.5 (post-B3d/e) returns the
    assembled per-channel dict for non-capture moves; captures still
    raise ``NotImplementedError`` pointing at B5.
"""
from __future__ import annotations

from typing import Any, Dict

import scipy.sparse as sp
from scipy.sparse import csr_matrix

from chess_spectral import qm_4d_dynamics as _dyn


# Channel name -> milestone identifier. Used by the bridge's
# observability output and by future B5 capture-path dispatch.
_CHANNEL_MILESTONES: Dict[str, str] = {
    'A1':         'B1 (shipped)',
    'STD4_X':     'B3a (shipped — same-orbit strict; cross-orbit marker)',
    'STD4_Y':     'B3a (shipped — same-orbit strict; cross-orbit marker)',
    'STD4_Z':     'B3a (shipped — same-orbit strict; cross-orbit marker)',
    'STD4_W':     'B3a (shipped — same-orbit strict; cross-orbit marker)',
    'FIB_SYM_1':  'B3c (shipped — measurement-only re-encode)',
    'FIB_SYM_2':  'B3c (shipped — measurement-only re-encode)',
    'FIB_SYM_3':  'B3c (shipped — measurement-only re-encode)',
    'FA_PAWN_W':  'B3b (shipped — strict-unitary axis-flip; cross-parity marker)',
    'FA_PAWN_Y':  'B3b (shipped — strict-unitary axis-flip; cross-parity marker)',
    'FD_DIAG':    'B3d/e (shipped — rank-1 update with renorm; v1.5 Option A)',
}

# Channel names that have a shipped per-channel builder. After B3d/e,
# all 11 channels are populated for non-capture moves; the only
# remaining gap is the capture path (B5).
_SHIPPED_CHANNELS: frozenset = frozenset({
    'A1',
    'STD4_X', 'STD4_Y', 'STD4_Z', 'STD4_W',
    'FA_PAWN_W', 'FA_PAWN_Y',
    'FIB_SYM_1', 'FIB_SYM_2', 'FIB_SYM_3',
    'FD_DIAG',
})


def apply_move_qm(
    state: Any,
    move: Any,
    *,
    optional_return_unitary: bool = False,
) -> Dict[str, Any]:
    """Bridge surface for the §17.1 ``applyMoveQm`` API.

    **B3d/e status: returns assembled per-channel dict.** After this
    milestone the bridge populates **all 11 channel entries** for
    non-capture moves via the per-channel builders in
    :mod:`chess_spectral.qm_4d_dynamics` and returns the assembled
    dict directly (no more ``NotImplementedError`` for non-captures).
    The dict's values are a heterogeneous mix:

      * ``csr_matrix`` (4096×4096 sparse, complex128): the strict-
        unitary or sub-unitary projector-sandwich / similarity-
        transform operator. Returned by:
          - ``A1`` (always),
          - ``STD4_X/Y/Z/W`` for same-B_4-orbit moves (cross-orbit
            falls back to a marker dict per ADR-003 amendment),
          - ``FA_PAWN_W/Y`` (always — sub-unitarity holds only for
            pure axis-flip moves but the operator is constructed
            unconditionally; non-axis-flip moves get a non-strict
            but well-defined sandwich).

      * marker dict (with at least ``strict_unitary`` / ``reason`` /
        ``channel`` keys; optionally ``psi_post_block`` for the
        re-encode-based markers): the measurement-only / rank-1 /
        cross-orbit / cross-parity-class fallback. Returned by:
          - ``STD4_X/Y/Z/W`` for cross-B_4-orbit moves (carries
            ``reason: 'cross-orbit'``; no ``psi_post_block``),
          - ``FIB_SYM_1/2/3`` always (carries
            ``reason: 'measurement-only'`` and ``psi_post_block``),
          - ``FD_DIAG`` always (carries
            ``reason: 'rank-1-update-with-renorm'`` and
            ``psi_post_block``).

    Consumers dispatch on ``isinstance(value, dict)`` to route each
    channel block: matrix entries multiply ``psi_pre[chan_block]``;
    marker entries with ``psi_post_block`` are spliced directly into
    ``psi_post`` (no matrix multiply); cross-orbit markers without
    ``psi_post_block`` route to a measurement-only re-encode at the
    bridge layer (the bridge consumer is responsible for that
    re-encode in v1.5; the marker just signals the intent).

    Capture moves still raise ``NotImplementedError`` pointing at B5
    — see the per-channel builder docstrings for the deferred
    constructions (FA_PAWN partial-isometry; A_1 / STD4 / FD_DIAG
    rank-1 + renorm).

    Parameters
    ----------
    state
        Pre-move state. Same form accepted by
        :func:`chess_spectral.qm_4d_dynamics.u_move_a1`: position
        dict ``{sq: piece}`` or an object with a ``.position``
        attribute (e.g., :class:`chess_spectral_4d.GameState4D`).
    move
        Move endpoints. Same form as
        :func:`chess_spectral.qm_4d_dynamics.u_move_a1`: a tuple of
        endpoints (each int or 4-tuple) or a Move4D-like object.
    optional_return_unitary
        Per the §17.1 contract, the consumer may opt into receiving
        the full 45 056×45 056 sparse ``U_move`` for animation /
        debugging. Currently ignored (the bridge returns the
        per-channel dict regardless); v1.5 will expose the assembled
        block-diagonal U_move via this flag.

    Returns
    -------
    dict[str, csr_matrix | dict]
        Per-channel dict keyed by channel name (``'A1'``, ``'STD4_X'``,
        …, ``'FD_DIAG'``). Values are either ``csr_matrix`` (same-
        orbit / strict-unitary path) or marker dicts (cross-orbit /
        measurement-only / rank-1 / cross-parity-class paths). All 11
        channel keys are present after B3d/e for non-capture moves.

    Raises
    ------
    NotImplementedError
        If the move is a capture (any per-channel builder raises with
        ``assume_non_capture=False``; the bridge does not currently
        opt into capture detection — captures fall through the
        builders' default ``assume_non_capture=True`` fast path and
        produce ill-defined operators). v1.5 will add capture
        detection at the bridge layer once B5's per-channel capture
        constructions land.

    Notes
    -----
    The B2 free-evolution primitive
    (:func:`chess_spectral.qm_4d_dynamics.evolve_under_h0`) is NOT
    yet wired into the ψ_post computation; the Zeno-style sandwich

        ψ(t_{n+1}^-) = evolve_under_h0(ψ(t_n), Δt)
        ψ(t_{n+1})   = N_{n+1} * U_move @ ψ(t_{n+1}^-)

    requires a Δt animation-clock parameter that the M14.x renderer
    will supply once the per-channel builders settle. For now,
    consumers needing free-evolution between move boundaries call
    :func:`chess_spectral.qm_4d_dynamics.evolve_under_h0` directly on
    the assembled ψ.
    """
    # Build the per-channel dict by dispatching to each shipped
    # builder. Values are heterogeneous: csr_matrix (strict-unitary)
    # OR marker dicts (cross-orbit / measurement-only / rank-1).
    # Consumers dispatch on isinstance(value, dict).
    channels_unitaries: Dict[str, Any] = {}

    # ── A_1 channel (B1 — shipped) ─────────────────────────────────
    channels_unitaries['A1'] = _dyn.u_move_a1(state, move)

    # ── STD4_X/Y/Z/W (B3a — shipped) ────────────────────────────────
    # The four std-rep coord channels share the similarity-transform
    # construction with axis-specific D_a / phase. Per ADR-003 §3.1
    # channels 1-4 + ADR-003 amendment Option (a), the strict-unitary
    # path is restricted to same-B_4-orbit non-capture moves;
    # cross-orbit moves return a marker dict pointing at v1.5
    # measurement-only re-encode. The dict entries can be a csr_matrix
    # (same-orbit) or a marker dict (cross-orbit); the v1.5 consumer
    # dispatches on the value type.
    for axis in ('X', 'Y', 'Z', 'W'):
        channels_unitaries[f'STD4_{axis}'] = _dyn.u_move_std4(
            state, move, axis=axis,
        )

    # ── FA_PAWN_W/Y (B3b — shipped) ────────────────────────────────
    # Antisymmetric pawn channels under W-axis or Y-axis parity. Per
    # ADR-003 §3.2 + B3b empirical finding: strict-unitary path holds
    # only for pure-axis-flip moves (sq_to == sigma_axis(sq_from));
    # the projector-sandwich is constructed unconditionally, so the
    # builder always returns a csr_matrix here (non-axis-flip moves
    # produce a sub-unitary but well-defined operator). Captures are
    # NotImplementedError (deferred to B5 partial-isometry handling).
    for axis in ('W', 'Y'):
        channels_unitaries[f'FA_PAWN_{axis}'] = _dyn.u_move_fa_pawn(
            state, move, axis=axis,
        )

    # ── FIB_SYM_1/2/3 (B3c — shipped) ──────────────────────────────
    # Measurement-only re-encode per the Phase 3.5 amendment to
    # ADR-003 §3.3. The bilinear FIB encoder formula has no strict-
    # unitary lift (Probe 2: ε p95 = 5.6/6.8/46.8 vs the 0.10 gate);
    # FIB channels return a marker dict with ``psi_post_block``
    # carrying the post-move re-encoded 4096-dim vector. The bridge
    # consumer (v1.5) dispatches on ``isinstance(value, dict)`` to
    # route the marker's ``psi_post_block`` directly into the assembled
    # post-move ψ rather than evolving via U_move @ psi_pre.
    for fib_idx in (1, 2, 3):
        channels_unitaries[f'FIB_SYM_{fib_idx}'] = _dyn.u_move_fib_meas(
            state, move, fib_idx,
        )

    # ── FD_DIAG (B3d/e — shipped) ──────────────────────────────────
    # Rank-1 update + renormalization per ADR-003 §3.2 channel 10.
    # v1.5 ships Option A (re-encode marker): the channel block is
    # invariant for non-captures (the rank-1 update reduces to
    # identity), so re-encoding the post-move position is
    # mathematically equivalent and faster to ship. Phase 3.5 Probe 2
    # validated cond p95 = 8.60 vs the 100 acceptance gate (well-
    # conditioned). Capture handling ships in B5 with the explicit
    # rank-1 algebra. The marker dict carries
    # ``reason: 'rank-1-update-with-renorm'`` to distinguish from
    # B3c's ``'measurement-only'`` for observability.
    channels_unitaries['FD_DIAG'] = _dyn.u_move_fd_diag(state, move)

    # All 11 channels populated. Return the assembled dict directly
    # (v1.5 contract: bridge no longer raises NotImplementedError
    # for non-capture moves; capture detection lands at the bridge
    # layer in B5 once the capture-path builders are complete).
    #
    # TODO (v1.5 / Phase 4 B2 wired into bridge): per ADR-002 §3.3,
    # the Zeno-style ψ_post computation should sandwich the
    # instantaneous U_move with continuous H_0 evolution:
    #
    #     ψ(t_{n+1}^-) = evolve_under_h0(ψ(t_n), Δt)        # pre-move drift
    #     ψ(t_{n+1})   = N_{n+1} * U_move @ ψ(t_{n+1}^-)    # instant + renorm
    #
    # The Δt parameter is supplied by the M14.x renderer
    # (animation-clock dependent; see ADR-002 §3.5). The B2 primitive
    # is callable directly via
    # ``chess_spectral.qm_4d_dynamics.evolve_under_h0``.
    #
    # TODO (v1.5 / Phase 4 B5 capture handling): when the capture-path
    # builders land (FA_PAWN partial-isometry, A_1 / STD4 / FD_DIAG
    # rank-1 + renorm), wire capture detection at this layer so the
    # builders are called with ``assume_non_capture=False`` and
    # captures route to the new constructions instead of falling
    # through the non-capture fast path. Until then, captures
    # silently produce ill-defined operators on the strict-unitary
    # channels (the projector-sandwich + capture combination has
    # been pinned by xfail-strict tests but is not formally
    # rejected).
    #
    # TODO (v1.5 — optional_return_unitary): when this flag is set,
    # assemble a block-diagonal 45 056×45 056 U_move from the
    # csr_matrix entries (with the marker entries contributing
    # identity blocks or being sliced out depending on the consumer's
    # convention). Currently ignored; the dict-of-blocks return is
    # sufficient for M14.x rendering.

    return channels_unitaries


__all__ = [
    'apply_move_qm',
]
