"""chess_spectral.qm_4d_bridge - applyMoveQm bridge surface.

Per §17.1 of the chess-spectral research notebook, the consumer-side
QM bridge exposes ``applyMoveQm(state, move)`` (Python:
:func:`apply_move_qm`) for advancing a quantum state through a single
chess move. The full implementation requires per-channel move
unitaries for **all 11 channels** (A_1, STD4_X/Y/Z/W, FA_PAWN_W/Y,
FIB_SYM_1/2/3, FD_DIAG) — see ADR-003 §3.1's tiered plan and the
B[2..5] milestone roadmap.

Phase 4 milestones B1 + B3a + B3b + B3c + B3d/e + **B5** ship **all
11 channels** for **both non-capture and capture** moves via:

  * :func:`chess_spectral.qm_4d_dynamics.u_move_a1` (A_1),
  * :func:`chess_spectral.qm_4d_dynamics.u_move_std4` (STD4_*),
  * :func:`chess_spectral.qm_4d_dynamics.u_move_fa_pawn` (FA_PAWN_*),
  * :func:`chess_spectral.qm_4d_dynamics.u_move_fib_meas` (FIB_SYM_*),
  * :func:`chess_spectral.qm_4d_dynamics.u_move_fd_diag` (FD_DIAG).

After B5 the bridge **no longer raises** for ANY move type
(non-capture and capture both succeed) — :func:`apply_move_qm`
returns the assembled per-channel dict in all cases. The dict's
values are a mix of ``csr_matrix`` (strict-unitary same-orbit A_1 /
STD4_* same-orbit / FA_PAWN_* axis-flip on **non-capture moves**)
and marker dicts (cross-orbit / cross-parity-class / measurement-only
/ rank-1 / **capture-rank-1-with-renorm** /
**capture-partial-isometry** / **capture-measurement-only**). For
capture moves, ALL 11 channels return marker dicts (the all-marker-
dict variant); consumers dispatch on ``isinstance(value, dict)``.

Milestone status (post-B5):

  - **B1** A_1 channel — shipped.
  - **B2** Zeno-style evolution + H_0 — shipped (callable via
    :func:`chess_spectral.qm_4d_dynamics.evolve_under_h0`; not yet
    wired into ``apply_move_qm``'s ψ_post computation — see TODO
    below).
  - **B3a** STD4_X/Y/Z/W (strict-unitary same-orbit; cross-orbit
    returns measurement-only re-encode marker per ADR-003 amendment
    Option (a)) — shipped.
  - **B3b** FA_PAWN_W/Y (strict-unitary axis-flip; cross-parity
    returns marker) — shipped.
  - **B3c** FIB_SYM_1/2/3 (Phase 3.5 amendment: measurement-only
    re-encode per ADR-003 §3.3 fallback — best-effort linearization
    failed the Phase 3.5 Probe-2 acceptance gate by 50-500×) —
    shipped.
  - **B3d/e** FD_DIAG (rank-1 update + renormalization, cond p95 =
    8.60 < 100 acceptance gate; v1.5 ships Option A re-encode marker)
    — shipped.
  - **B5** capture handling — **shipped this milestone**. All 11
    channels handle captures via Option A re-encode (measurement-
    only): the bridge detects capture moves at the assembly layer
    and dispatches all per-channel builders with
    ``assume_non_capture=False``, which routes through the channels'
    new capture-path branches. Reason strings are channel-specific:
    A_1 / STD4 / FD_DIAG → ``'capture-rank-1-with-renorm'``; FA_PAWN
    → ``'capture-partial-isometry'`` (per ADR-003 §3.1 channels 8-9's
    captured-pawn 8-mode-block removal); FIB_SYM →
    ``'capture-measurement-only'`` (matches the Phase 3.5 amendment
    to ADR-003 §3.3). Explicit rank-1 / partial-isometry / Stinespring
    algebra is deferred to v1.7+ when profiling justifies the LOC.

Why a separate module?
----------------------

``qm_4d_dynamics.py`` holds the per-channel constructions
(``u_move_*``) and shared move-coercion helpers. ``qm_4d_bridge.py``
holds the **assembly** layer that ties channel unitaries together
into the §17.1 ``applyMoveQm`` API. Keeping them separate matches
the v1.5.0 architecture sketch: ``qm_4d_dynamics`` is the math, the
bridge is the consumer-facing API. After B5 the only future bridge
work is the §17.1 7-method bridge surface (M14.x dispatch logic for
the measurement-only re-encode) and the optional return_unitary
assembled-block-diagonal U_move.

Public API
----------
:func:`apply_move_qm`
    The §17.1 bridge entry-point. After B5 returns the assembled
    per-channel dict for **all** moves (non-capture and capture);
    no longer raises ``NotImplementedError`` for any case.
"""
from __future__ import annotations

from typing import Any, Dict

import scipy.sparse as sp
from scipy.sparse import csr_matrix

from chess_spectral import qm_4d_dynamics as _dyn


# Channel name -> milestone identifier. Used by the bridge's
# observability output. After B5 every channel handles both non-
# capture and capture moves; the milestone string reflects the latest
# work that touched that channel.
_CHANNEL_MILESTONES: Dict[str, str] = {
    'A1':         'B1 + B5 (shipped — capture: rank-1 with renorm)',
    'STD4_X':     'B3a + B5 (shipped — capture: rank-1 with renorm)',
    'STD4_Y':     'B3a + B5 (shipped — capture: rank-1 with renorm)',
    'STD4_Z':     'B3a + B5 (shipped — capture: rank-1 with renorm)',
    'STD4_W':     'B3a + B5 (shipped — capture: rank-1 with renorm)',
    'FIB_SYM_1':  'B3c + B5 (shipped — capture: measurement-only)',
    'FIB_SYM_2':  'B3c + B5 (shipped — capture: measurement-only)',
    'FIB_SYM_3':  'B3c + B5 (shipped — capture: measurement-only)',
    'FA_PAWN_W':  'B3b + B5 (shipped — capture: partial-isometry)',
    'FA_PAWN_Y':  'B3b + B5 (shipped — capture: partial-isometry)',
    'FD_DIAG':    'B3d/e + B5 (shipped — capture: rank-1 with renorm)',
}

# Channel names that have a shipped per-channel builder. After B5,
# all 11 channels handle BOTH non-capture and capture moves; the
# bridge no longer has any unshipped channel.
_SHIPPED_CHANNELS: frozenset = frozenset({
    'A1',
    'STD4_X', 'STD4_Y', 'STD4_Z', 'STD4_W',
    'FA_PAWN_W', 'FA_PAWN_Y',
    'FIB_SYM_1', 'FIB_SYM_2', 'FIB_SYM_3',
    'FD_DIAG',
})


def _bridge_is_capture(state: Any, move: Any) -> bool:
    """Detect whether ``move`` is a capture against ``state``'s
    pre-move position.

    Bridge-layer wrapper around :func:`qm_4d_dynamics._is_capture`
    that handles the move-coercion needed to go from a Move4D-like
    object / 2-tuple endpoint pair to the linear destination index.
    Used by :func:`apply_move_qm` to decide whether to dispatch the
    builders with ``assume_non_capture=False`` (B5 capture path) or
    ``assume_non_capture=True`` (the fast non-capture path).
    """
    # Re-use the dynamics module's helpers for move coercion + capture
    # detection so the capture-detection logic stays consistent across
    # the per-channel builders and the bridge.
    from_idx, to_idx = _dyn._coerce_move(move)
    return _dyn._is_capture(state, from_idx, to_idx)


def apply_move_qm(
    state: Any,
    move: Any,
    *,
    optional_return_unitary: bool = False,
) -> Dict[str, Any]:
    """Bridge surface for the §17.1 ``applyMoveQm`` API.

    **B5 status: returns assembled per-channel dict for ALL move
    types.** After B5 the bridge populates **all 11 channel entries**
    for both non-capture and capture moves via the per-channel
    builders in :mod:`chess_spectral.qm_4d_dynamics`. The bridge
    detects capture moves at the assembly layer
    (:func:`_bridge_is_capture`) and dispatches the builders with
    ``assume_non_capture=False`` for captures, routing them through
    the channels' B5 capture-path branches. The dict's values are a
    heterogeneous mix:

      * ``csr_matrix`` (4096×4096 sparse, complex128): the strict-
        unitary or sub-unitary projector-sandwich / similarity-
        transform operator. Returned **only for non-capture moves**:
          - ``A1`` (always — non-capture),
          - ``STD4_X/Y/Z/W`` for same-B_4-orbit non-capture moves
            (cross-orbit falls back to a marker dict),
          - ``FA_PAWN_W/Y`` (always — non-capture; sub-unitarity holds
            only for pure axis-flip moves but the operator is
            constructed unconditionally for non-captures).

      * marker dict (with at least ``strict_unitary`` / ``reason`` /
        ``channel`` keys; optionally ``psi_post_block``,
        ``captured_piece``): the measurement-only / rank-1 /
        cross-orbit / cross-parity-class / **capture** fallback.
        Returned by:
          - ``STD4_X/Y/Z/W`` for cross-B_4-orbit non-capture moves
            (``reason: 'cross-orbit'``; no ``psi_post_block``),
          - ``FIB_SYM_1/2/3`` for non-capture moves
            (``reason: 'measurement-only'`` + ``psi_post_block``),
          - ``FD_DIAG`` for non-capture moves
            (``reason: 'rank-1-update-with-renorm'`` +
            ``psi_post_block``),
          - **All 11 channels** for capture moves (B5 path):
              * A_1 / STD4_* / FD_DIAG:
                ``reason: 'capture-rank-1-with-renorm'``,
              * FA_PAWN_W/Y: ``reason: 'capture-partial-isometry'``,
              * FIB_SYM_1/2/3: ``reason: 'capture-measurement-only'``.
            All carry ``psi_post_block`` and ``captured_piece``.

    Consumers dispatch on ``isinstance(value, dict)`` to route each
    channel block: matrix entries multiply ``psi_pre[chan_block]``;
    marker entries with ``psi_post_block`` are spliced directly into
    ``psi_post`` (no matrix multiply); cross-orbit markers without
    ``psi_post_block`` route to a measurement-only re-encode at the
    bridge consumer layer (the marker just signals the intent).

    For capture moves the dispatch path is **uniform**: every channel
    returns a marker dict with ``psi_post_block``, so the consumer
    splices all 11 blocks directly into ``ψ_post`` (no per-channel
    matrix multiplications needed). This is the all-marker-dict
    variant.

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
        orbit / strict-unitary path on non-capture moves) or marker
        dicts (cross-orbit / measurement-only / rank-1 / cross-parity-
        class / capture paths). All 11 channel keys are present for
        ALL move types after B5. Capture moves return the all-marker-
        dict variant (every channel value is a marker dict).

    Raises
    ------
    None for valid moves (B5 closes the last NotImplementedError
    case). ``TypeError`` / ``ValueError`` may still surface from the
    underlying move-coercion / per-channel builders for malformed
    input (e.g., missing piece at ``from_sq``, out-of-range linear
    indices).

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
    # Detect capture at the bridge layer once; the per-channel
    # builders re-detect via _is_capture but the bridge-level decision
    # selects which branch to dispatch (assume_non_capture=False
    # routes through the new B5 capture-path builders).
    is_capture = _bridge_is_capture(state, move)

    # Build the per-channel dict by dispatching to each shipped
    # builder. Values are heterogeneous: csr_matrix (strict-unitary
    # on non-capture moves) OR marker dicts (cross-orbit /
    # measurement-only / rank-1 / capture). Consumers dispatch on
    # isinstance(value, dict).
    channels_unitaries: Dict[str, Any] = {}

    # ── A_1 channel (B1 + B5 — shipped) ─────────────────────────────
    # Non-capture: returns the projector-sandwich csr_matrix.
    # Capture: returns the B5 capture marker
    # ('capture-rank-1-with-renorm' + psi_post_block + captured_piece).
    channels_unitaries['A1'] = _dyn.u_move_a1(
        state, move, assume_non_capture=not is_capture,
    )

    # ── STD4_X/Y/Z/W (B3a + B5 — shipped) ───────────────────────────
    # Non-capture: csr_matrix (same-orbit) or cross-orbit marker.
    # Capture: B5 capture marker (rank-1-with-renorm + psi_post_block
    # + captured_piece). The capture path is independent of orbit
    # dichotomy — both same-orbit and cross-orbit captures route
    # through the same Option A re-encode marker.
    for axis in ('X', 'Y', 'Z', 'W'):
        channels_unitaries[f'STD4_{axis}'] = _dyn.u_move_std4(
            state, move, axis=axis,
            assume_non_capture=not is_capture,
        )

    # ── FA_PAWN_W/Y (B3b + B5 — shipped) ────────────────────────────
    # Non-capture: csr_matrix (the projector-sandwich; sub-unitary
    # only for pure axis-flip moves).
    # Capture: B5 capture marker ('capture-partial-isometry' +
    # psi_post_block + captured_piece) per ADR-003 §3.1 channels 8-9
    # (the captured pawn's 8-mode block is removed from the encoder
    # input, so ||U @ psi|| < ||psi||; renormalisation is folded
    # into state_to_psi).
    for axis in ('W', 'Y'):
        channels_unitaries[f'FA_PAWN_{axis}'] = _dyn.u_move_fa_pawn(
            state, move, axis=axis,
            assume_non_capture=not is_capture,
        )

    # ── FIB_SYM_1/2/3 (B3c + B5 — shipped) ──────────────────────────
    # Non-capture: 'measurement-only' marker per Phase 3.5 amendment
    # to ADR-003 §3.3.
    # Capture: 'capture-measurement-only' marker (same construction;
    # the captured piece is silently overwritten by the classical
    # apply_move_to_position helper, which matches the bilinear
    # encoder's input semantics — captures and non-captures both ship
    # via Option A re-encode).
    for fib_idx in (1, 2, 3):
        channels_unitaries[f'FIB_SYM_{fib_idx}'] = _dyn.u_move_fib_meas(
            state, move, fib_idx,
            assume_non_capture=not is_capture,
        )

    # ── FD_DIAG (B3d/e + B5 — shipped) ──────────────────────────────
    # Non-capture: 'rank-1-update-with-renorm' marker (the rank-1
    # update reduces to identity for non-captures; Option A
    # re-encode is mathematically equivalent and ships in v1.5).
    # Capture: 'capture-rank-1-with-renorm' marker (the rank-1 update
    # is non-trivial for captures — the destination's DIAG_DEV row
    # changes from the captured piece's row to the moving piece's row;
    # Option A re-encode reproduces this exactly via state_to_psi).
    channels_unitaries['FD_DIAG'] = _dyn.u_move_fd_diag(
        state, move, assume_non_capture=not is_capture,
    )

    # All 11 channels populated. Return the assembled dict directly.
    # After B5, the bridge does not raise NotImplementedError for ANY
    # case — non-captures and captures both produce well-defined
    # marker dicts (with optional csr_matrix entries on the strict-
    # unitary same-orbit non-capture paths).
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
