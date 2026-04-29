"""chess_spectral.qm_4d_bridge - applyMoveQm bridge surface (v1.5
placeholder).

Per §17.1 of the chess-spectral research notebook, the consumer-side
QM bridge exposes ``applyMoveQm(state, move)`` (Python:
:func:`apply_move_qm`) for advancing a quantum state through a single
chess move. The full implementation requires per-channel move
unitaries for **all 11 channels** (A_1, STD4_X/Y/Z/W, FA_PAWN_W/Y,
FIB_SYM_1/2/3, FD_DIAG) — see ADR-003 §3.1's tiered plan and the
B[2..5] milestone roadmap.

Phase 4 milestone B1 ships only the A_1 channel via
:func:`chess_spectral.qm_4d_dynamics.u_move_a1`; this module's
:func:`apply_move_qm` is a **stub** that assembles the per-channel
dictionary skeleton and raises ``NotImplementedError``. B2-B5 will
fill in the remaining channels:

  - **B3a** STD4_X/Y/Z/W (strict-unitary, per-axis phase per ADR-001).
  - **B3b** FA_PAWN_W/Y (strict-unitary non-capture; partial-isometry
    capture per B5).
  - **B3c** FIB_SYM_1/2/3 (Phase 3.5 amendment: measurement-only
    re-encode per ADR-003 §3.3 fallback — best-effort linearization
    failed the Phase 3.5 Probe-2 acceptance gate).
  - **B3d/e** FD_DIAG (rank-1 update + renormalization).
  - **B5** capture handling (partial-isometry / rank-1 / Stinespring
    deferred).

Why a separate module?
----------------------

``qm_4d_dynamics.py`` holds the per-channel constructions
(``u_move_*``) and shared move-coercion helpers. ``qm_4d_bridge.py``
holds the **assembly** layer that ties channel unitaries together
into the §17.1 ``applyMoveQm`` API. Keeping them separate matches
the v1.5.0 architecture sketch: ``qm_4d_dynamics`` is the math, the
bridge is the consumer-facing API. B2-B5 will keep adding channels
to ``qm_4d_dynamics`` without churning this module beyond plumbing.

Public API
----------
:func:`apply_move_qm`
    The §17.1 bridge entry-point. B1 raises
    ``NotImplementedError``; v1.5 will return either a sparse
    45 056×45 056 ``U_move`` matrix or a normalised ``ψ_post`` vector
    depending on the ``optional_return_unitary`` flag.
"""
from __future__ import annotations

from typing import Any, Dict

import scipy.sparse as sp
from scipy.sparse import csr_matrix

from chess_spectral import qm_4d_dynamics as _dyn


# Channel name -> milestone identifier. Used by the bridge stub's
# error message and by future B2-B5 dispatch.
_CHANNEL_MILESTONES: Dict[str, str] = {
    'A1':         'B1',          # shipped (this milestone)
    'STD4_X':     'B3a',
    'STD4_Y':     'B3a',
    'STD4_Z':     'B3a',
    'STD4_W':     'B3a',
    'FIB_SYM_1':  'B3c (measurement-only re-encode)',
    'FIB_SYM_2':  'B3c (measurement-only re-encode)',
    'FIB_SYM_3':  'B3c (measurement-only re-encode)',
    'FA_PAWN_W':  'B3b',
    'FA_PAWN_Y':  'B3b',
    'FD_DIAG':    'B3d/e',
}


def apply_move_qm(
    state: Any,
    move: Any,
    *,
    optional_return_unitary: bool = False,
) -> Any:
    """Bridge surface for the §17.1 ``applyMoveQm`` API.

    **B1 status: stub.** Builds the channel-unitary skeleton with the
    A_1 entry populated via :func:`chess_spectral.qm_4d_dynamics.u_move_a1`,
    then raises ``NotImplementedError`` until B2-B5 land the remaining
    10 channels.

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
        debugging. Currently ignored; v1.5 will respect it.

    Returns
    -------
    Never returns successfully in B1; ``NotImplementedError`` is
    raised. v1.5 will return a normalised ψ_post vector (or the
    ``(ψ_post, U_move)`` pair when ``optional_return_unitary=True``).

    Raises
    ------
    NotImplementedError
        Always (B1 milestone). The error message lists the
        outstanding channels and their milestone targets.
    """
    # Build what we have so the assembly skeleton is exercised.
    # B2-B5 will replace each ``raise`` with the channel's
    # ``u_move_<chan>`` builder.
    channels_unitaries: Dict[str, csr_matrix] = {}

    # ── A_1 channel (B1 — shipped) ─────────────────────────────────
    channels_unitaries['A1'] = _dyn.u_move_a1(state, move)

    # ── STD4_X/Y/Z/W (B3a — pending) ───────────────────────────────
    # for axis in ('X', 'Y', 'Z', 'W'):
    #     channels_unitaries[f'STD4_{axis}'] = u_move_std4(state, move, axis)
    #
    # ── FA_PAWN_W/Y (B3b — pending; partial-isometry on capture) ───
    # channels_unitaries['FA_PAWN_W'] = u_move_pawn_w(state, move)
    # channels_unitaries['FA_PAWN_Y'] = u_move_pawn_y(state, move)
    #
    # ── FIB_SYM_1/2/3 (B3c — measurement-only re-encode per Phase ──
    #   3.5 amendment to ADR-003 §3.3) ────────────────────────────
    # for fib_idx in (1, 2, 3):
    #     channels_unitaries[f'FIB_SYM_{fib_idx}'] = u_move_fib_meas(
    #         state, move, fib_idx,
    #     )
    #
    # ── FD_DIAG (B3d/e — rank-1 update) ────────────────────────────
    # channels_unitaries['FD_DIAG'] = u_move_fd_diag(state, move)

    # The full bridge would then assemble these into a single
    # 45 056×45 056 sparse U_move via sp.block_diag(...) and apply
    # it to state_to_psi(state) — modulo the FIB_SYM measurement-only
    # path which projects rather than evolves.

    pending = sorted(
        f"{name} (target: {ms})"
        for name, ms in _CHANNEL_MILESTONES.items()
        if name != 'A1'
    )
    raise NotImplementedError(
        "Full applyMoveQm bridge requires B2-B5 channel unitaries; "
        "B1 ships A_1 only (see chess_spectral.qm_4d_dynamics."
        "u_move_a1). Pending channels: " + "; ".join(pending) + ". "
        "See docs/adr/qm_4d/PHASE_3_5_PROBE_RESULTS.md for the v1.5 "
        "scope decision."
    )


__all__ = [
    'apply_move_qm',
]
