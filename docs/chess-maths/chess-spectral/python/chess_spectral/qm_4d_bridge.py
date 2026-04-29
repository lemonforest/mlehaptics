"""chess_spectral.qm_4d_bridge - the §17.1 + §17.5 v1.5 bridge surface.

This is the **consumer-facing Pyodide bridge** for chess4D-OC and other
downstream consumers — the contract chess-spectral 1.5.0 ships against
per the research notebook §17.1 / §17.5. All seven §17.1 QM-extension
methods (``getQmState``, ``getQmDensity``, ``applyMoveQm``,
``measureAt``, ``getDensityMatrixOf``, ``getProbabilityCurrent``,
``getQmExpectation``) plus the six §17.5 dev/debug methods
(``getVersion``, ``getEncoderShape``, ``getFen4State``, ``loadFen4``,
``loadJsonlFixture``, ``hasLegalMoves``) are exposed here as
Pyodide-friendly Python callables.

Per §17.6, this module exposes capabilities; the consumer chooses how
to use them. Anything UI-flavored, persistence-flavored, or
consumer-architecture-flavored stays consumer-side.

The §17.1 ``applyMoveQm`` path (:func:`apply_move_qm` and the
``v1.5 full-ψ_post`` variant :func:`apply_move_qm_full`) is the
heart of the bridge. The dispatch logic that takes ``apply_move_qm``'s
per-channel dict (mixed ``csr_matrix`` + marker dict) and assembles
the post-move ψ in C^45056 lives in :func:`apply_move_qm_full`. That
function performs the per-channel block dispatch:

  * ``csr_matrix`` entry → ``U_chan @ ψ_pre[chan_block]``
  * marker dict with ``psi_post_block`` → splice block directly into ψ_post
  * marker dict without ``psi_post_block`` (cross-orbit STD4) → re-encode
    via :func:`chess_spectral.qm_4d.state_to_psi` and slice the channel
    block

After dispatch, ψ_post is renormalized (capture moves can break norm
via the FA_PAWN partial-isometry path; rank-1 + renorm pattern).

Per-method §17.1 contract
-------------------------

Each method returns a Pyodide-JSON-serializable dict with at least an
``ok`` key. Failures raise (``NotImplementedError`` for v1.7+ deferrals;
``TypeError`` / ``ValueError`` for malformed input). Numpy arrays in
return values are real-valued (Float32 for ψ-amplitude payloads, per
§17.1's interleaved-real+imag convention) so Pyodide can hand them to
JavaScript ``Float32Array`` without conversion.

Underlying ``apply_move_qm`` documentation
------------------------------------------

The full implementation requires per-channel move unitaries for
**all 11 channels** (A_1, STD4_X/Y/Z/W, FA_PAWN_W/Y, FIB_SYM_1/2/3,
FD_DIAG) — see ADR-003 §3.1's tiered plan and the B[2..5] milestone
roadmap.

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

§17.1 (QM-extension bridge surface):
    :func:`get_qm_state`              — current ψ as Float32 (real+imag interleaved)
    :func:`get_qm_density`            — |ψ|² per cell on the 4096-cell lattice
    :func:`apply_move_qm`             — per-channel dict (low-level)
    :func:`apply_move_qm_full`        — assembled ψ_post (high-level dispatch)
    :func:`measure_at`                — Born-rule projective measurement
    :func:`get_density_matrix_of`     — reduced density matrix (deferred to v1.7+)
    :func:`get_probability_current`   — j_p(c) = Im(ψ* ∇ψ) on the lattice
    :func:`get_qm_expectation`        — ⟨ψ|H|ψ⟩ for a named observable

§17.5 (developer / debug bridge surface):
    :func:`get_version`               — chess_spectral.__version__
    :func:`get_encoder_shape`         — channel layout + total dim
    :func:`get_fen4_state`            — FEN4 string of current state
    :func:`load_fen4`                 — parse FEN4 string into a state object
    :func:`load_jsonl_fixture`        — load test-fixture in-memory pieces dict
    :func:`has_legal_moves`           — does a team have any legal move?

Helpers (Pyodide-bridge serialization):
    :func:`complex_to_interleaved_float32`  — ComplexArray = real+imag interleaved
"""
from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Tuple, Union

import numpy as np
import scipy.sparse as sp
from scipy.sparse import csr_matrix

# NOTE: ``qm_4d_dynamics`` is imported lazily inside each function that
# needs it. This module + ``qm_4d_dynamics`` form a mutual import (the
# dynamics module re-exports our :func:`apply_move_qm` for callers who
# prefer the dynamics namespace), so a top-level ``from chess_spectral
# import qm_4d_dynamics`` here triggers a circular-import failure when
# ``qm_4d_bridge`` is the entry-point of the import graph. The lazy
# pattern (each function does ``from chess_spectral import
# qm_4d_dynamics as _dyn`` on first call) sidesteps the problem
# without requiring callers to import ``qm_4d_dynamics`` first.
def _get_dyn():
    """Lazy accessor for :mod:`chess_spectral.qm_4d_dynamics`.

    Used at function-entry to avoid a circular import at module load
    time. The first call pays the import cost; subsequent calls are
    O(1) ``sys.modules`` lookups.
    """
    from chess_spectral import qm_4d_dynamics as _dyn
    return _dyn


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
    _dyn = _get_dyn()
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
    _dyn = _get_dyn()

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


# =====================================================================
# §17.1 + §17.5 v1.5 bridge surface
# =====================================================================
#
# The methods below are the consumer-facing Pyodide bridge surface.
# Each returns a Pyodide-JSON-serializable dict with an ``ok`` key.
# Numpy arrays in return values are real-valued (Float32) where
# possible so the chess4D-OC Pyodide worker can pass them as
# ``Float32Array`` without conversion.

# ---- Pyodide-bridge serialization helpers ---------------------------


def complex_to_interleaved_float32(psi: np.ndarray) -> np.ndarray:
    """Serialize a complex ψ to a Float32 array of interleaved
    real+imag pairs.

    The §17.1 ``ComplexArray`` on-the-wire format is ``Float32``
    interleaved (real, imag, real, imag, ...). For a complex array of
    length N, this produces a Float32 array of length 2N where
    ``out[0::2] = ψ.real`` and ``out[1::2] = ψ.imag``. The chess4D-OC
    consumer's M14.x WebGL renderer reads the interleaved format
    directly into a ``Float32Array`` for shader uniforms / texture
    upload.

    Parameters
    ----------
    psi : ndarray, complex (any shape)
        Source complex amplitude. Cast to ``complex128`` internally; the
        output is always ``float32``.

    Returns
    -------
    ndarray of shape ``(2 * psi.size,)``, dtype ``float32``
        Real+imag interleaved. The original shape is flattened — the
        consumer reconstructs structure from the channel layout
        returned by :func:`get_encoder_shape`.

    Notes
    -----
    The Float32 cast is intentional: the §17.1 contract values
    bandwidth (Pyodide → JS structured-clone copies) over the extra ~7
    bits of mantissa precision. M14.x's visualization tier doesn't need
    full double precision for amplitude rendering. Consumers requiring
    the full complex128 amplitude can use :func:`apply_move_qm` and
    :func:`apply_move_qm_full` directly via the Python module API
    (skipping serialization).
    """
    psi_arr = np.asarray(psi, dtype=np.complex128).ravel()
    out = np.empty(2 * psi_arr.size, dtype=np.float32)
    out[0::2] = psi_arr.real.astype(np.float32)
    out[1::2] = psi_arr.imag.astype(np.float32)
    return out


def _channel_block_offset(channel: str) -> int:
    """Return the 0-based start offset of the named channel's 4096-block
    in the 45 056-dim full encoder vector.

    Source of truth: :data:`chess_spectral.encoder_4d.CHANNELS_4D`.
    Raises :class:`ValueError` for unknown channel names.
    """
    from chess_spectral import encoder_4d as _enc4
    for name, offset in _enc4.CHANNELS_4D:
        if name == channel:
            return int(offset)
    raise ValueError(
        f"unknown channel name {channel!r}; expected one of "
        f"{[n for n, _ in _enc4.CHANNELS_4D]}"
    )


# ---- §17.1 #1: get_qm_state ----------------------------------------


def get_qm_state(state: Any, *, side_to_move: bool = True) -> Dict[str, Any]:
    """§17.1 #1 ``getQmState``: current ψ as Float32 interleaved
    real+imag.

    Drives M14.1 raw-amplitude render, M14.2 phase-as-color, M14.3
    trajectory replay.

    Parameters
    ----------
    state
        Position dict ``{sq: piece}`` or an object with a ``.position``
        attribute (e.g., :class:`chess_spectral_4d.GameState4D`).
    side_to_move : bool, optional
        ``True`` = white to move (default), ``False`` = black to move.
        Controls the Z_2 superselection sign on ψ per
        :func:`chess_spectral.qm_4d.state_to_psi`.

    Returns
    -------
    dict with keys:

      * ``ok`` (bool): always ``True`` for valid input.
      * ``psi`` (ndarray[float32, (90112,)]): real+imag interleaved
        Float32 of the 45 056-dim complex ψ. Total 90112 floats; for
        cell ``c`` of channel ``i`` the amplitude is
        ``psi[2*(i*4096+c)] + 1j*psi[2*(i*4096+c)+1]``.
      * ``basisDim`` (int): always ``45056``.
      * ``normSq`` (float): ``⟨ψ|ψ⟩`` of the unserialized complex ψ.
        Equals ``1.0`` within float rounding for any non-empty
        position; zero for the empty-position sentinel.
    """
    from chess_spectral import qm_4d as _qm4
    pos = getattr(state, "position", state)
    psi = _qm4.state_to_psi(pos, side_to_move)
    psi_serialized = complex_to_interleaved_float32(psi)
    return {
        'ok': True,
        'psi': psi_serialized,
        'basisDim': int(_qm4.ENCODING_DIM),
        'normSq': float(np.vdot(psi, psi).real),
    }


# ---- §17.1 #2: get_qm_density --------------------------------------


def get_qm_density(
    state: Any,
    piece_id: Optional[int] = None,
    *,
    side_to_move: bool = True,
) -> Dict[str, Any]:
    """§17.1 #2 ``getQmDensity``: ``|ψ|²`` per cell on the 4096-cell
    lattice.

    Without ``piece_id``: returns the **full-position** density,
    summed across the 11 channels per square. Reflects the M14.1
    full-position amplitude render. With ``piece_id``: would return
    a single-piece marginal (partial trace over channels), but that
    requires partial-trace machinery that ships in v1.7+ — raises
    :class:`NotImplementedError` with a pointer.

    Parameters
    ----------
    state
        Position dict or object with ``.position`` attribute.
    piece_id : int, optional
        If provided, requests a per-piece marginal — currently raises
        ``NotImplementedError``.
    side_to_move : bool, optional
        Forwarded to :func:`chess_spectral.qm_4d.state_to_psi`.

    Returns
    -------
    dict with keys:

      * ``ok`` (bool): always ``True`` for valid input.
      * ``density`` (ndarray[float32, (4096,)]): per-cell sum of
        ``|ψ_chan(cell)|²`` across the 11 channels. For a normalized
        ψ, ``density.sum() == 1.0`` within float rounding.

    Raises
    ------
    NotImplementedError
        If ``piece_id`` is provided. The per-piece marginal requires a
        partial-trace operator over channel labels (cheap arithmetic;
        the channel projectors are block-disjoint), but the channel-to-
        piece attribution is not 1:1 (multiple pieces contribute to
        the same channel via :func:`chess_spectral.encoder_4d.encode_4d`).
        Deferred to v1.7+ along with :func:`get_density_matrix_of`.
    """
    from chess_spectral import qm_4d as _qm4
    if piece_id is not None:
        raise NotImplementedError(
            f"get_qm_density(piece_id={piece_id!r}) — per-piece marginal "
            "requires partial trace over channels with a channel-to-piece "
            "attribution map that doesn't exist in the current encoder "
            "(multiple pieces contribute to the same channel via "
            "encoder_4d.encode_4d's bilinear FIB / FD_DIAG / FA_PAWN "
            "summation). Deferred to v1.7+ along with "
            "get_density_matrix_of. The full-position density "
            "(piece_id=None) ships in v1.5."
        )
    pos = getattr(state, "position", state)
    psi = _qm4.state_to_psi(pos, side_to_move)
    # Reshape into (11, 4096) — one row per channel block — then
    # sum |ψ|^2 across the channel axis to get per-cell density.
    psi_block_view = psi.reshape(_qm4.N_CHANNELS, _qm4.CHANNEL_DIM)
    density_per_cell = (
        np.abs(psi_block_view) ** 2
    ).sum(axis=0).astype(np.float32)
    return {
        'ok': True,
        'density': density_per_cell,
    }


# ---- §17.1 #3: apply_move_qm_full ----------------------------------


def apply_move_qm_full(
    state: Any,
    move: Any,
    *,
    side_to_move: bool = True,
    side_to_move_post: Optional[bool] = None,
    return_per_channel: bool = False,
) -> Dict[str, Any]:
    """§17.1 #3 ``applyMoveQm`` with assembled ψ_post.

    Wraps :func:`apply_move_qm` (the per-channel dispatch dict) and
    assembles the post-move ψ in C^45056 by per-channel block dispatch:

      * ``csr_matrix`` entry → ``U_chan @ ψ_pre[chan_block]``.
      * marker dict with ``psi_post_block`` → splice block directly.
      * marker dict without ``psi_post_block`` (cross-orbit STD4) →
        re-encode via :func:`chess_spectral.qm_4d.state_to_psi` and
        slice the channel block (consumer's measurement-only
        re-encode, performed at the bridge layer).

    After block-wise dispatch, ψ_post is renormalized (capture moves
    can break norm via the FA_PAWN partial-isometry path; the
    rank-1 + renorm pattern from ADR-003 §3.1 channels 8-9).

    Parameters
    ----------
    state
        Pre-move state (position dict or object with ``.position``).
    move
        Move endpoints. Same format as :func:`apply_move_qm`.
    side_to_move : bool, optional
        Side-to-move BEFORE the move (used to construct ψ_pre).
        Default ``True`` (white-to-move at the start of analysis).
    side_to_move_post : bool, optional
        Side-to-move AFTER the move. Default flips ``side_to_move``
        (the standard alternation). Used both for the cross-orbit
        STD4 fallback re-encode and for the rank-1 / measurement-only
        marker re-encodes already inside the per-channel builders.
    return_per_channel : bool, optional
        If ``True``, also include the raw per-channel dispatch dict
        from :func:`apply_move_qm` in the result under the
        ``perChannel`` key (useful for debugging the dispatch logic).
        Default ``False``.

    Returns
    -------
    dict with keys:

      * ``ok`` (bool): always ``True`` for valid input.
      * ``psi`` (ndarray[float32, (90112,)]): ψ_post serialized as
        real+imag interleaved Float32.
      * ``basisDim`` (int): ``45056``.
      * ``normSq`` (float): ``⟨ψ_post|ψ_post⟩``. After renormalization
        this is ``1.0`` within float rounding (or ``0.0`` for the
        pathological zero-vector case).
      * ``perChannel`` (dict, optional): only present if
        ``return_per_channel=True``. The raw per-channel dispatch
        from :func:`apply_move_qm`.
    """
    from chess_spectral import qm_4d as _qm4

    if side_to_move_post is None:
        side_to_move_post = not side_to_move

    # Step 1: per-channel dispatch dict from the existing bridge.
    channels = apply_move_qm(state, move)

    # Step 2: ψ_pre construction (needed for the csr_matrix entries).
    pos_pre = getattr(state, "position", state)
    psi_pre = _qm4.state_to_psi(pos_pre, side_to_move)

    # Step 3: assemble ψ_post by per-channel block dispatch.
    psi_post = np.zeros(_qm4.ENCODING_DIM, dtype=np.complex128)

    # Cache the post-move re-encode for cross-orbit STD4 fallback —
    # avoids re-encoding multiple times if multiple channels need it.
    cached_psi_re_encode: Optional[np.ndarray] = None

    def _get_re_encode() -> np.ndarray:
        # Re-encode the post-move position lazily, caching across
        # channels that need it. This is the bridge consumer's
        # "measurement-only re-encode" path for cross-orbit markers.
        nonlocal cached_psi_re_encode
        if cached_psi_re_encode is None:
            _dyn = _get_dyn()
            from_idx, to_idx = _dyn._coerce_move(move)
            pos_post = _dyn._apply_move_to_position(
                state, from_idx, to_idx,
            )
            cached_psi_re_encode = _qm4.state_to_psi(
                pos_post, side_to_move_post,
            )
        return cached_psi_re_encode

    for chan_name, value in channels.items():
        block_offset = _channel_block_offset(chan_name)
        block_slice = slice(block_offset, block_offset + _qm4.CHANNEL_DIM)

        if isinstance(value, dict):
            # Marker dict — splice psi_post_block directly when present.
            if 'psi_post_block' in value:
                psi_post[block_slice] = value['psi_post_block']
            else:
                # Cross-orbit STD4 case: re-encode at the bridge layer.
                psi_full_post = _get_re_encode()
                psi_post[block_slice] = psi_full_post[block_slice]
        else:
            # csr_matrix — multiply on the channel block.
            # The csr_matrix is the per-channel U_chan; apply it to the
            # corresponding block of ψ_pre.
            psi_post[block_slice] = value @ psi_pre[block_slice]

    # Step 4: renormalize. Capture moves break norm via the FA_PAWN
    # partial-isometry path (and the rank-1 + renorm pattern in
    # ADR-003 §3.1 channels 8-9). Non-capture moves preserve norm
    # within float rounding, so the renorm is a tight no-op there.
    norm_post = float(np.linalg.norm(psi_post))
    if norm_post > 1e-15:
        psi_post = psi_post / norm_post

    psi_serialized = complex_to_interleaved_float32(psi_post)
    result: Dict[str, Any] = {
        'ok': True,
        'psi': psi_serialized,
        'basisDim': int(_qm4.ENCODING_DIM),
        'normSq': float(np.vdot(psi_post, psi_post).real),
    }
    if return_per_channel:
        result['perChannel'] = channels
    return result


# ---- §17.1 #4: measure_at ------------------------------------------


def measure_at(
    state: Any,
    coords: Union[Tuple[int, int, int, int], int],
    observable: Optional[str] = None,
    *,
    side_to_move: bool = True,
    rng: Optional[np.random.Generator] = None,
) -> Dict[str, Any]:
    """§17.1 #4 ``measureAt``: Born-rule projective measurement at
    lattice coords.

    Default observable is "position" — equivalent to projecting onto
    the channel-summed cell basis at ``coords``. For a named
    Hermitian observable (e.g., ``'rook'``, ``'bishop'``), measures
    the corresponding piece-reach operator on the per-cell channel
    block. The Born-rule probability is
    ``p(c) = ⟨ψ|P_c|ψ⟩`` where P_c is the projector onto the cell
    or eigenspace.

    Parameters
    ----------
    state
        Position dict or object with ``.position`` attribute.
    coords : 4-tuple ``(x, y, z, w)`` or int
        Lattice coordinates in [0, 7]^4 or the linear-square index in
        [0, 4096). For the "position" observable this is the cell to
        sample at.
    observable : str, optional
        Default ``None`` = position observable (sample at ``coords``).
        Named observables (``'rook'``, ``'bishop'``, ``'queen'``,
        ``'king'``, ``'knight'``) measure the eigenvalue distribution
        of the corresponding piece-reach Hermitian on the cell-channel
        block at ``coords``; see :func:`get_qm_expectation` for the
        observable-name → Hermitian-operator map.
    side_to_move : bool, optional
        Forwarded to :func:`chess_spectral.qm_4d.state_to_psi`.
    rng : numpy.random.Generator, optional
        Source of randomness for the Born-rule sample. Default
        ``numpy.random.default_rng()`` (fresh seed). Passing a seeded
        Generator makes the measurement reproducible.

    Returns
    -------
    dict with keys:

      * ``ok`` (bool).
      * ``probability`` (float): the Born-rule probability ``|⟨c|ψ⟩|²``
        of the measured outcome at ``coords``.
      * ``sampledOutcome`` (int or float): the sampled outcome; cell
        index for the position observable, eigenvalue for a named
        observable.
      * ``postCollapsePsi`` (ndarray[float32, (90112,)]): the
        post-measurement collapsed and renormalized ψ, serialized as
        real+imag interleaved Float32.
    """
    from chess_spectral import qm_4d as _qm4
    if rng is None:
        rng = np.random.default_rng()

    # Coerce coords to a linear-square index in [0, 4096).
    if isinstance(coords, tuple) and len(coords) == 4:
        from chess_spectral import tables_4d as _t4
        x, y, z, w = coords
        cell_idx = _t4.sq4(int(x), int(y), int(z), int(w))
    else:
        cell_idx = int(coords)
    if not 0 <= cell_idx < _qm4.CHANNEL_DIM:
        raise ValueError(
            f"cell index {cell_idx} out of range [0, {_qm4.CHANNEL_DIM})"
        )

    pos = getattr(state, "position", state)
    psi = _qm4.state_to_psi(pos, side_to_move)

    if observable is None or observable == 'position':
        # Position observable: project onto the cell-basis vector
        # |cell_idx⟩ summed across all 11 channels. The Born
        # probability is the channel-summed |ψ|² at cell_idx.
        # Post-collapse ψ is the cell-projection of ψ, renormalized.
        psi_view = psi.reshape(_qm4.N_CHANNELS, _qm4.CHANNEL_DIM)
        amp_at_cell = psi_view[:, cell_idx]  # complex (11,)
        prob = float(np.vdot(amp_at_cell, amp_at_cell).real)
        # Post-collapse: zero out all OTHER cells; renormalize.
        psi_post = np.zeros_like(psi)
        psi_post_view = psi_post.reshape(
            _qm4.N_CHANNELS, _qm4.CHANNEL_DIM,
        )
        psi_post_view[:, cell_idx] = amp_at_cell
        norm_post = float(np.linalg.norm(psi_post))
        if norm_post > 1e-15:
            psi_post = psi_post / norm_post
        return {
            'ok': True,
            'probability': prob,
            'sampledOutcome': int(cell_idx),
            'postCollapsePsi': complex_to_interleaved_float32(psi_post),
        }

    # Named-observable path: project ψ onto the eigenspaces of H on
    # C^4096, restricted to the same cell of every channel.
    H = _get_observable_by_name(observable)
    eigvals, probs = _qm4.measure_observable_distribution(
        H, psi[:_qm4.CHANNEL_DIM],
    )
    # Normalize over the channel block (which is what the Born rule
    # gives on the restricted state). The per-cell sample at cell_idx
    # is just the named-observable's expectation projection at that
    # cell index.
    p_total = probs.sum()
    probs_norm = probs / p_total if p_total > 1e-15 else probs
    sampled = int(rng.choice(len(eigvals), p=probs_norm))
    return {
        'ok': True,
        'probability': float(probs_norm[sampled]),
        'sampledOutcome': float(eigvals[sampled]),
        'postCollapsePsi': complex_to_interleaved_float32(psi),
    }


# ---- §17.1 #5: get_density_matrix_of (deferred to v1.7+) -----------


def get_density_matrix_of(
    state: Any,  # noqa: ARG001
    piece_id: int,
) -> Dict[str, Any]:
    """§17.1 #5 ``getDensityMatrixOf``: reduced density matrix for a
    piece via partial trace.

    **Deferred to v1.7+.** The reduced density matrix
    ``ρ = Tr_chans(|ψ⟩⟨ψ|)`` requires (a) a channel-to-piece
    attribution map (currently 1:N — multiple pieces contribute to
    the same channel via the bilinear encoder formulas) and (b) the
    partial-trace operator over channel labels. Both are mechanical
    sparse-matrix operations once the attribution map is decided, but
    the design is open enough that v1.5 ships the deferred-NIE
    pattern rather than committing prematurely.

    Parameters
    ----------
    state
        Pre-move state (position dict or object with ``.position``).
    piece_id : int
        Linear-square index of the piece to trace out the rest of
        the system from.

    Raises
    ------
    NotImplementedError
        Always, until v1.7+. Message points to the design decision
        and the §17.1 infrastructure note.
    """
    raise NotImplementedError(
        f"get_density_matrix_of(piece_id={piece_id!r}) — partial trace "
        "over channels requires a channel-to-piece attribution map "
        "(currently 1:N due to the bilinear encoder formulas in "
        "FIB_SYM / FD_DIAG / FA_PAWN). The mechanical partial-trace "
        "operation is straightforward once the attribution is decided; "
        "see §17.1's infrastructure note. Deferred to v1.7+ along with "
        "the per-piece variant of get_qm_density."
    )


# ---- §17.1 #6: get_probability_current -----------------------------


def _build_lattice_gradient_4d() -> Tuple[csr_matrix, ...]:
    """Build the 4 lattice-gradient operators ``∂_axis`` on the
    P_8 □ P_8 □ P_8 □ P_8 lattice as 4096×4096 sparse matrices.

    For each axis a in {0, 1, 2, 3}, ``∂_a`` is the central-difference
    operator along axis a:

      (∂_a ψ)(x) = (ψ(x + e_a) - ψ(x - e_a)) / 2

    with zero-flux boundary conditions (forward / backward differences
    at the lattice edges, so the operator stays sparse and
    finite-dimensional). Each ∂_a is anti-Hermitian under the standard
    inner product, which makes the probability current
    ``j_a = Im(ψ* ∂_a ψ)`` real-valued — exactly what the §17.1 #6
    contract requires for a divergence-free continuity-equation
    statement.

    Returns
    -------
    tuple of 4 csr_matrix, each shape (4096, 4096), dtype complex128
        ``(grad_x, grad_y, grad_z, grad_w)``. Anti-Hermitian
        (``grad_a^† = -grad_a``).
    """
    from chess_spectral import tables_4d as _t4
    BS = _t4.BOARD_SIDE  # 8
    # 1D central-difference operator on P_8 with reflecting boundary
    # (forward at x=0, backward at x=7, central interior). This is
    # anti-Hermitian: D_1d^T = -D_1d.
    D_main = np.zeros(BS, dtype=np.complex128)
    D_main[0] = -0.5
    D_main[-1] = 0.5
    D_super = 0.5 * np.ones(BS - 1, dtype=np.complex128)
    D_super[0] = 1.0  # forward at x=0
    D_sub = -0.5 * np.ones(BS - 1, dtype=np.complex128)
    D_sub[-1] = -1.0  # backward at x=7
    D_1d = sp.diags(
        [D_sub, D_main, D_super], offsets=[-1, 0, 1],
        shape=(BS, BS), format="csr", dtype=np.complex128,
    )

    eye = sp.eye(BS, format="csr", dtype=np.complex128)
    grads = []
    for axis in range(4):
        factors = [eye] * 4
        factors[axis] = D_1d
        T = factors[0]
        for f in factors[1:]:
            T = sp.kron(T, f, format="csr")
        grads.append(T.tocsr())
    return tuple(grads)


# Cached lattice-gradient operators. Built lazily on first call to
# :func:`get_probability_current`.
_LATTICE_GRADIENT_CACHE: Optional[Tuple[csr_matrix, ...]] = None


def _get_lattice_gradient_4d() -> Tuple[csr_matrix, ...]:
    """Cached accessor for the 4 axis-gradient operators."""
    global _LATTICE_GRADIENT_CACHE
    if _LATTICE_GRADIENT_CACHE is None:
        _LATTICE_GRADIENT_CACHE = _build_lattice_gradient_4d()
    return _LATTICE_GRADIENT_CACHE


def get_probability_current(
    state: Any,
    *,
    side_to_move: bool = True,
) -> Dict[str, Any]:
    """§17.1 #6 ``getProbabilityCurrent``: ``j_p(c) = Im(ψ* ∇ψ)`` —
    probability current field on the lattice.

    For the QM-filament viz (M14.6). The gradient is a
    finite-difference operator on P_8 □ P_8 □ P_8 □ P_8 (Kronecker
    sum of per-axis 1D central-difference operators with reflecting
    boundary). The result is a real per-cell × 4-axis vector field
    summed across the 11 channels.

    By construction (∂_a is anti-Hermitian + ψ is normalized + ρ_p =
    Σ_chan |ψ_chan|² is the per-cell density), the resulting current
    field satisfies the discrete continuity equation
    ``∂_t ρ + ∇·j = 0``. For a static ψ (no time-evolution under
    H_0), ``∂_t ρ = 0``, so ``∇·j ≈ 0`` at floating-point residual.
    Tests verify this divergence-free property.

    Parameters
    ----------
    state
        Position dict or object with ``.position`` attribute.
    side_to_move : bool, optional
        Forwarded to :func:`chess_spectral.qm_4d.state_to_psi`.

    Returns
    -------
    dict with keys:

      * ``ok`` (bool).
      * ``j`` (ndarray[float32, (4096, 4)]): per-cell × 4-axis current
        vector summed across the 11 channels. ``j[c, a]`` is the
        component of the probability current at cell ``c`` along axis
        ``a`` (where 0=x, 1=y, 2=z, 3=w).
    """
    from chess_spectral import qm_4d as _qm4

    pos = getattr(state, "position", state)
    psi = _qm4.state_to_psi(pos, side_to_move)
    grads = _get_lattice_gradient_4d()

    # Sum the per-channel currents: each channel's psi-block contributes
    # j_chan(c, a) = Im(psi_chan* (∂_a psi_chan))(c). The total current
    # is the channel-sum.
    j_total = np.zeros(
        (_qm4.CHANNEL_DIM, 4), dtype=np.float64,
    )
    psi_view = psi.reshape(_qm4.N_CHANNELS, _qm4.CHANNEL_DIM)
    for chan in range(_qm4.N_CHANNELS):
        psi_chan = psi_view[chan]
        for axis in range(4):
            grad_psi = grads[axis] @ psi_chan
            # j_chan(c, a) = Im(psi_chan* (∂_a psi_chan))
            j_chan_axis = (psi_chan.conj() * grad_psi).imag
            j_total[:, axis] += j_chan_axis

    return {
        'ok': True,
        'j': j_total.astype(np.float32),
    }


# ---- §17.1 #7: get_qm_expectation ----------------------------------


# Map from observable-name → piece-Hermitian-attribute-on-qm_4d.
# Source of truth: chess_spectral.qm_4d's H_<piece>_4 lazy attributes.
_OBSERVABLE_NAME_MAP: Dict[str, str] = {
    'rook':   'H_rook_4',
    'bishop': 'H_bishop_4',
    'queen':  'H_queen_4',
    'king':   'H_king_4',
    'knight': 'H_knight_4',
}


def _get_observable_by_name(name: str) -> csr_matrix:
    """Look up a named observable.

    Returns the 4096×4096 sparse Hermitian operator from
    :mod:`chess_spectral.qm_4d` for the given name. Raises
    :class:`NotImplementedError` for pawn observables (deferred to
    Track B per Pre-flight 2 / ADR-005) and :class:`ValueError` for
    unknown names.
    """
    from chess_spectral import qm_4d as _qm4
    name_lower = name.lower()
    if name_lower in _OBSERVABLE_NAME_MAP:
        attr = _OBSERVABLE_NAME_MAP[name_lower]
        return getattr(_qm4, attr)
    if name_lower in ('pawn', 'pawn_w', 'pawn_y'):
        # Trigger the same NotImplementedError as build_H_piece_4 so
        # callers get the Track B pointer.
        return _qm4.build_H_piece_4(
            'P_w' if name_lower in ('pawn', 'pawn_w') else 'P_y'
        )
    raise ValueError(
        f"unknown observable name {name!r}; expected one of "
        f"{sorted(_OBSERVABLE_NAME_MAP)} (Hermitian piece-reach lifts) "
        "or one of ('pawn', 'pawn_w', 'pawn_y') (deferred — raises "
        "NotImplementedError pointing at Track B)"
    )


def get_qm_expectation(
    state: Any,
    observable: str,
    *,
    side_to_move: bool = True,
    weights: Optional[Mapping[str, float]] = None,  # noqa: ARG001
) -> Dict[str, Any]:
    """§17.1 #7 ``getQmExpectation``: ``⟨ψ|H|ψ⟩`` for a named
    observable.

    Composes with the engine ``evaluatePosition`` (v1.6+) for the QM
    evaluator family. Works on the per-channel-block restriction —
    H is a 4096×4096 Hermitian on the cell-mode space, applied
    independently to each channel block (equivalent to the lifted
    ``I_11 ⊗ H`` operator on C^45056).

    Parameters
    ----------
    state
        Position dict or object with ``.position`` attribute.
    observable : str
        Name of the Hermitian observable. One of
        ``{'rook', 'bishop', 'queen', 'king', 'knight'}`` (case-
        insensitive). Pawn observables raise ``NotImplementedError``
        per Pre-flight 2 / ADR-005 (deferred to Track B).
    side_to_move : bool, optional
        Forwarded to :func:`chess_spectral.qm_4d.state_to_psi`.
    weights : Mapping[str, float], optional
        Per-channel weight overrides. Currently ignored — the v1.5
        contract treats H as the lifted ``I_11 ⊗ H`` operator
        (uniform channel weighting). v1.7+ may expose per-channel
        weights for the engine evaluator.

    Returns
    -------
    dict with keys:

      * ``ok`` (bool).
      * ``value`` (float): ``⟨ψ|H_full|ψ⟩`` where H_full = I_11 ⊗ H.
        Equals the sum of per-channel-block expectation values.

    Raises
    ------
    NotImplementedError
        For pawn observables (deferred to Track B).
    ValueError
        For unknown observable names.
    """
    from chess_spectral import qm_4d as _qm4
    pos = getattr(state, "position", state)
    psi = _qm4.state_to_psi(pos, side_to_move)
    H = _get_observable_by_name(observable)
    # ⟨ψ|I_11 ⊗ H|ψ⟩ = Σ_chan ⟨ψ_chan|H|ψ_chan⟩. Avoid materialising
    # the lifted 45056×45056 operator — sum per-block.
    psi_view = psi.reshape(_qm4.N_CHANNELS, _qm4.CHANNEL_DIM)
    total = 0.0
    for chan in range(_qm4.N_CHANNELS):
        psi_chan = psi_view[chan]
        Hpsi = H @ psi_chan
        total += float(np.vdot(psi_chan, Hpsi).real)
    return {
        'ok': True,
        'value': float(total),
    }


# =====================================================================
# §17.5 developer / debug bridge surface
# =====================================================================


def get_version() -> Dict[str, Any]:
    """§17.5 #1 ``getVersion``: returns chess_spectral.__version__.

    Trivial wrapper over :data:`chess_spectral.__version__` (which
    derives dynamically from ``importlib.metadata`` per the v1.3.2
    contract — see :mod:`chess_spectral.__init__` for the rationale).

    Returns
    -------
    dict with ``ok`` and ``version`` (str).
    """
    import chess_spectral
    return {
        'ok': True,
        'version': str(chess_spectral.__version__),
    }


def get_encoder_shape() -> Dict[str, Any]:
    """§17.5 #2 ``getEncoderShape``: channel layout + total dim.

    Lets the consumer's visualizer validate at startup that the worker
    version matches the expected channel set (e.g., catches a stale
    worker still on v1.0's 10-channel layout shipping against a v1.5+
    HUD expecting 11). Trivial wrapper over
    :data:`chess_spectral.encoder_4d.CHANNELS_4D`.

    Returns
    -------
    dict with keys:

      * ``ok`` (bool).
      * ``channels`` (list of dict): one per channel, each with
        ``{'name': str, 'offset': int, 'dim': int}`` keys.
      * ``totalDim`` (int): always ``45056``.
    """
    from chess_spectral import encoder_4d as _enc4
    channels = [
        {
            'name':   str(name),
            'offset': int(offset),
            'dim':    int(_enc4.CHANNEL_DIM),
        }
        for name, offset in _enc4.CHANNELS_4D
    ]
    return {
        'ok': True,
        'channels': channels,
        'totalDim': int(_enc4.ENCODING_DIM_4D),
    }


def get_fen4_state(state: Any) -> Dict[str, Any]:
    """§17.5 #3 ``getFen4State``: FEN4 string of the current state.

    Thin wrapper over :func:`chess_spectral.fen_4d.serialize` applied
    to the current state's position dict.

    Parameters
    ----------
    state
        Position dict or object with ``.position`` attribute.

    Returns
    -------
    dict with ``ok`` and ``fen4`` (str).
    """
    from chess_spectral import fen_4d as _fen4
    pos = getattr(state, "position", state)
    return {
        'ok': True,
        'fen4': str(_fen4.serialize(pos)),
    }


def load_fen4(fen4_string: str) -> Dict[str, Any]:
    """§17.5 #4 ``loadFen4``: parse a FEN4 string into a state object.

    Re-imports a FEN4 string into a fresh state dict (the pieces dict
    in :mod:`chess_spectral.encoder_4d`'s format). The caller can wrap
    the returned ``state`` in a :class:`chess_spectral_4d.GameState4D`
    if they need history/clock tracking; for kinematic-only QM analysis
    the dict alone is sufficient.

    Parameters
    ----------
    fen4_string : str
        Valid FEN4 v1 placement literal accepted by
        :func:`chess_spectral.fen_4d.parse`.

    Returns
    -------
    dict with keys:

      * ``ok`` (bool).
      * ``state`` (dict[int, PieceValue]): the parsed position dict.
        Same format consumed by all the §17.1 methods above.
    """
    from chess_spectral import fen_4d as _fen4
    pos = _fen4.parse(fen4_string)
    return {
        'ok': True,
        'state': pos,
    }


def load_jsonl_fixture(pieces_obj: Mapping[Any, Any]) -> Dict[str, Any]:
    """§17.5 #5 ``loadJsonlFixture``: load from the in-memory pieces
    dict format used in ``tests/fixtures/positions_4d.jsonl``.

    Shorter round-trip when the consumer already has the structured
    form (e.g., loaded from a fixture file in the consumer's
    development workflow).

    Parameters
    ----------
    pieces_obj : Mapping
        Three accepted shapes:

        * Direct sq-keyed dict: ``{sq_int: piece_value, ...}`` —
          returned as-is (idempotent).
        * JSONL fixture wrapper: ``{'name': str, 'pieces': {sq_str:
          piece_str}}`` — the format used in
          ``tests/fixtures/positions_4d.jsonl``. Pawns are encoded as
          ``'Pw'`` / ``'Py'`` / ``'pw'`` / ``'py'`` (color + axis as a
          single 2-char string); we expand these to the
          ``(color, axis)`` tuple form expected by
          :func:`chess_spectral.encoder_4d.encode_4d`.
        * Coord-list form: ``{'pieces': [{'coord': [x,y,z,w],
          'piece': 'K', ...}, ...]}`` — converted to sq-keyed via
          :func:`chess_spectral.tables_4d.sq4`.

    Returns
    -------
    dict with ``ok`` and ``state`` (dict[int, PieceValue]).
    """
    from chess_spectral import tables_4d as _t4

    # Idempotent path: caller already has the sq-int-keyed form.
    if all(isinstance(k, int) for k in pieces_obj.keys()):
        return {'ok': True, 'state': dict(pieces_obj)}

    # JSONL-wrapper paths route through the 'pieces' subkey.
    pieces_inner = pieces_obj.get('pieces')
    if pieces_inner is None:
        raise ValueError(
            "load_jsonl_fixture: pieces_obj must have 'pieces' subkey "
            "when keys are not sq-int-typed"
        )

    # JSONL fixture format: {'pieces': {sq_str: piece_str}}.
    if isinstance(pieces_inner, Mapping):
        pos: Dict[int, Any] = {}
        for sq_key, piece_str in pieces_inner.items():
            sq = int(sq_key)
            # Pawns: 'Pw' / 'Py' / 'pw' / 'py' — split into
            # (color, axis) tuple. The first character is the color
            # (case-sensitive), the second is the axis.
            if (
                isinstance(piece_str, str)
                and len(piece_str) == 2
                and piece_str[0] in ('P', 'p')
                and piece_str[1] in ('w', 'y')
            ):
                pos[sq] = (piece_str[0], piece_str[1])
            else:
                pos[sq] = piece_str
        return {'ok': True, 'state': pos}

    # Coord-list form: {'pieces': [{'coord': [x,y,z,w], 'piece': str}, ...]}.
    if isinstance(pieces_inner, (list, tuple)):
        pos = {}
        for entry in pieces_inner:
            if not isinstance(entry, Mapping):
                raise TypeError(
                    f"load_jsonl_fixture: each pieces entry must be a "
                    f"Mapping, got {type(entry).__name__}"
                )
            coord = entry.get('coord')
            if (
                not isinstance(coord, (list, tuple))
                or len(coord) != 4
            ):
                raise ValueError(
                    f"load_jsonl_fixture: invalid coord {coord!r}; "
                    "expected a 4-tuple/list of integers"
                )
            sq = _t4.sq4(int(coord[0]), int(coord[1]),
                         int(coord[2]), int(coord[3]))
            piece = entry.get('piece')
            if piece is None:
                raise ValueError(
                    f"load_jsonl_fixture: pieces entry missing 'piece' "
                    f"key: {entry!r}"
                )
            # Pawns may carry an axis annotation; preserve as a tuple.
            axis = entry.get('axis')
            if axis is not None and piece in ('P', 'p'):
                pos[sq] = (str(piece), str(axis))
            else:
                pos[sq] = piece
        return {'ok': True, 'state': pos}

    raise TypeError(
        f"load_jsonl_fixture: pieces_obj['pieces'] must be a Mapping or "
        f"list, got {type(pieces_inner).__name__}"
    )


def has_legal_moves(
    state: Any,
    team: str,
) -> Dict[str, Any]:
    """§17.5 #6 ``hasLegalMoves``: does ``team`` have any legal move?

    Required for stalemate detection in :func:`get_draw_status` (no
    legal moves + not in check ⇒ stalemate). Implementation iterates
    pieces of ``team``, summing cardinalities of
    :func:`chess_spectral.phase_operators_4d.occupation_aware_moves_a_4d`.

    Parameters
    ----------
    state
        State carrying both ``.position`` and (for the chess4d-backed
        legal-move iterator) the side-to-move / castling-rights /
        en-passant fields. The ``chess4d``-package state is the
        canonical input; a bare position dict triggers a fall-back
        path that approximates by counting non-empty per-piece phase
        operators on the empty-board reach (sufficient for the
        stalemate-detection use case).
    team : str
        ``'white'`` or ``'black'`` (case-insensitive).

    Returns
    -------
    dict with keys:

      * ``ok`` (bool).
      * ``hasMoves`` (bool): ``True`` iff at least one legal move exists.
      * ``count`` (int): the actual move count (when computable).
    """
    team_lc = team.lower()
    if team_lc not in ('white', 'black'):
        raise ValueError(
            f"team must be 'white' or 'black' (case-insensitive); "
            f"got {team!r}"
        )
    is_white = (team_lc == 'white')

    # Two paths depending on the input state shape:
    #
    #   Path A (full legality): chess4d.GameState with .board /
    #     .side_to_move / etc. Uses
    #     :func:`chess_spectral.phase_operators_4d.occupation_aware_moves_a_4d`
    #     for the pseudo-legal generator + chess4d's own piece
    #     iteration. Requires ``chess4d`` to be installed AND
    #     ``state`` to be a chess4d.GameState (duck-typed on .board).
    #   Path B (best-effort lower bound): bare position dict OR
    #     object with .position. Counts non-empty per-piece phase-op
    #     reach on the empty board; over-counts (no king-in-check
    #     filter, no obstruction for sliders) but
    #     hasMoves==False ⇒ definitely no legal moves, which is the
    #     useful direction for stalemate detection.
    #
    # The dispatch is on the input shape, not on whether chess4d is
    # installed: a bare position dict always routes through Path B
    # so the bridge stays callable from test fixtures and Pyodide
    # consumers that don't carry a chess4d.GameState wrapper.
    if hasattr(state, 'board'):
        # Path A: chess4d-backed full legality.
        try:
            import chess4d  # type: ignore[import-not-found]
            from chess_spectral.phase_operators_4d import (
                occupation_aware_moves_a_4d as _oa_moves,
            )
        except ImportError as e:
            raise ImportError(
                "has_legal_moves: state has a .board attribute "
                "(chess4d.GameState shape), but chess4d / "
                "phase_operators_4d are not importable. Either "
                "install chess4d or pass a bare position dict to "
                "use the best-effort phase-operator lower bound."
            ) from e
        color_filter = (
            chess4d.Color.WHITE if is_white else chess4d.Color.BLACK
        )
        count = 0
        for square in state.board.iter_squares():
            piece = state.board.piece_at(square)
            if piece is None or piece.color != color_filter:
                continue
            dests = _oa_moves(state, square, piece)
            count += len(dests)
        return {
            'ok': True,
            'hasMoves': count > 0,
            'count': int(count),
        }

    # Path B: best-effort empty-board adjacency lower bound on a bare
    # position dict. Uses :func:`chess_spectral.tables_4d.piece_adjacencies_4d`
    # to count edges from each team-owned piece's square. Over-counts
    # (no obstruction / king-in-check / occupancy filter), but
    # hasMoves==False ⇒ definitely no legal moves — which is the
    # useful direction for stalemate detection in
    # :func:`chess_spectral_4d.bridge.get_draw_status`.
    #
    # For pieces that share an adjacency table (knight uses idx 0,
    # bishop idx 1, rook idx 2, queen idx 3, king idx 4 — no pawn
    # entry), pawns are approximated by king-style adjacency (a
    # safe over-estimate; pawns cannot have MORE than king reach).
    pos = getattr(state, "position", state)
    if not isinstance(pos, Mapping):
        raise TypeError(
            "has_legal_moves: state must be a position dict, an object "
            "with .position attribute, or a chess4d.GameState (with "
            f".board); got {type(state).__name__}"
        )

    from chess_spectral import tables_4d as _t4
    adjs = _t4.piece_adjacencies_4d()
    # Index map matches qm_4d._PIECE_TO_ADJ_IDX. Pawns fall back to
    # king-adjacency (over-estimate; a king has ≥ pawn reach).
    idx_map = {'N': 0, 'B': 1, 'R': 2, 'Q': 3, 'K': 4, 'P': 4}
    count = 0
    for sq_idx, piece_value in pos.items():
        piece_char = (
            piece_value[0]
            if isinstance(piece_value, tuple)
            else piece_value
        )
        if not isinstance(piece_char, str) or not piece_char:
            continue
        piece_is_white = piece_char.isupper()
        if piece_is_white != is_white:
            continue
        ptype = piece_char.upper()
        adj_idx = idx_map.get(ptype)
        if adj_idx is None:
            continue
        adj = adjs[adj_idx]
        count += int(adj.getrow(sq_idx).nnz)
    return {
        'ok': True,
        'hasMoves': count > 0,
        'count': int(count),
    }


__all__ = [
    # Original §17.1 #3 entry-point (per-channel dispatch dict).
    'apply_move_qm',
    # §17.1 v1.5 bridge surface (assembled ψ_post + 6 read-only methods).
    'get_qm_state',
    'get_qm_density',
    'apply_move_qm_full',
    'measure_at',
    'get_density_matrix_of',
    'get_probability_current',
    'get_qm_expectation',
    # §17.5 dev/debug bridge surface.
    'get_version',
    'get_encoder_shape',
    'get_fen4_state',
    'load_fen4',
    'load_jsonl_fixture',
    'has_legal_moves',
    # Pyodide-bridge serialization helpers.
    'complex_to_interleaved_float32',
]
