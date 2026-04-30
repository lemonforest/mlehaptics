"""chess_spectral.qm_2d_bridge — the §17.2 v1.6.x bridge surface.

The 2D analogue of :mod:`chess_spectral.qm_4d_bridge` (which ships the
§17.1 + §17.5 methods for the 4D side). v1.5 shipped the 4D bridge;
v1.6 shipped 2D kinematics (``qm_2d``) and v1.6.x PR-A/B added the
2D Track B Zeno layer + A_1 channel u_move. This module wires them
into a Pyodide-JSON-friendly call surface so 2D consumers (the
upcoming chess2d Pyodide consumer + the web visualizer) can call
into the 2D QM extension the same way chess4d-OC calls the 4D side.

Note on naming: there is no "Oana-Chiru" ruleset for 2D chess —
standard chess rules are standard, no paper-specific variant.
"chess4d-OC" is short for "chess4d-oana-chiru", the specific 4D
ruleset from Oana & Chiru (AppliedMath 6(3):48, 2026). The 2D
consumer is just "chess2d" or "the 2D consumer"; it has no -OC
suffix.

Per §17.2, this module exposes capabilities; the consumer chooses
how to use them. Anything UI-flavored, persistence-flavored, or
consumer-architecture-flavored stays consumer-side.

Methods shipped in PR-C (this skeleton)
---------------------------------------

§17.5 dev/debug surface (5 methods, all trivially backed by the
already-shipped v1.6 kinematic layer):

  * :func:`get_version` — semver from ``importlib.metadata``
  * :func:`get_encoder_shape` — 640-dim, 10 channels x 64 modes
  * :func:`get_fen_state` — current state as FEN string
  * :func:`load_fen` — parse FEN -> position dict
  * :func:`has_legal_moves` — python-chess legal-move count > 0

§17.2 consumer surface (3 methods, kinematic-only):

  * :func:`get_qm_state` — ψ as interleaved Float32 (M14.x renderer)
  * :func:`get_qm_density` — ``|ψ|²`` per cell across 10 channels
  * :func:`get_qm_expectation` — Born-rule expectations for the 5
    Hermitian piece-reach observables (rook / bishop / queen / king
    / knight)

Methods deferred to PR-D / PR-E
-------------------------------

Methods that require the full per-channel u_move dynamics (still in
flight as Track 1 Track 1):

  * ``apply_move_qm`` — the §17.2 #3 ``applyMoveQm`` move-as-unitary
    dispatch. Requires per-channel builders for all 10 channels (PR-C
    revised scope: u_move_a1_2d ships in PR-B; the other 9 channels
    use the measurement-only re-encode pattern via state_to_psi in
    PR-E's bridge integration).

Per-method §17.2 contract
-------------------------

Each method returns a Pyodide-JSON-serializable dict with at least an
``ok`` key. Failures raise (``NotImplementedError`` for v1.7+
deferrals; ``TypeError`` / ``ValueError`` for malformed input). Numpy
arrays in return values are real-valued (``Float32`` for ψ-amplitude
payloads, per the §17.1 interleaved-real+imag convention) so Pyodide
can hand them to JavaScript ``Float32Array`` without conversion.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np


# ---- §17.5 #1: get_version ----------------------------------------


def get_version() -> Dict[str, Any]:
    """§17.5 ``getVersion``: package version + bridge surface version.

    Returns
    -------
    dict with keys:

      * ``ok`` (bool): always ``True``.
      * ``version`` (str): ``importlib.metadata`` version of the
        installed ``chess-spectral`` dist (e.g. ``'1.6.1'``). Returns
        ``'unknown'`` if the package is not installed (sys.path
        bootstrap mode).
      * ``bridge`` (str): bridge surface name (``'qm_2d_bridge'``).
      * ``surface`` (str): the §17.2 surface tag.
    """
    try:
        from importlib.metadata import version as _mv
        v = _mv("chess-spectral")
    except Exception:
        v = "unknown"
    return {
        "ok": True,
        "version": v,
        "bridge": "qm_2d_bridge",
        "surface": "§17.2",
    }


# ---- §17.5 #2: get_encoder_shape ----------------------------------


def get_encoder_shape() -> Dict[str, Any]:
    """§17.5 ``getEncoderShape``: dimensions of the 2D encoder output.

    Returns
    -------
    dict with keys:

      * ``ok`` (bool): always ``True``.
      * ``encodingDim`` (int): 640.
      * ``nChannels`` (int): 10.
      * ``channelDim`` (int): 64 (per-channel mode count == 8×8 board).
      * ``boardSide`` (int): 8.
      * ``channelNames`` (list[str]): the 10 channel names in encoder
        order (``['A1', 'A2', 'B1', 'B2', 'E', 'F1', 'F2', 'F3',
        'FA', 'FD']``).
    """
    from chess_spectral.encoder import CHANNELS, ENCODING_DIM, N_CHANNELS
    return {
        "ok": True,
        "encodingDim": int(ENCODING_DIM),
        "nChannels": int(N_CHANNELS),
        "channelDim": int(ENCODING_DIM // N_CHANNELS),
        "boardSide": 8,
        "channelNames": [name for name, _ in CHANNELS],
    }


# ---- §17.5 #3: get_fen_state --------------------------------------


def _cs_sq_to_chess_sq(sq: int) -> int:
    """Translate a chess_spectral square index (row 0 = rank 8) to a
    python-chess square index (row 0 = rank 1). Equivalent to
    flipping the rank: ``chess_sq = (7-row)*8 + col``.
    """
    row, col = divmod(int(sq), 8)
    return (7 - row) * 8 + col


def get_fen_state(state: Any) -> Dict[str, Any]:
    """§17.5 ``getFenState``: serialise the current position to FEN.

    Parameters
    ----------
    state
        Either a :class:`chess.Board` or a position dict
        ``{sq: piece_char}`` using the chess_spectral convention
        (``sq = row*8 + col`` with row 0 = rank 8). For the dict form,
        only the placement and side-to-move portions of the FEN are
        reconstructed (no en-passant, castling rights, halfmove or
        fullmove counters — those need a full :class:`chess.Board`).

    Returns
    -------
    dict with keys:

      * ``ok`` (bool): always ``True``.
      * ``fen`` (str): standard FEN string for the position.
    """
    import chess as _chess  # noqa: F401
    if hasattr(state, "fen") and callable(state.fen):
        return {"ok": True, "fen": state.fen()}
    # Position-dict form: rebuild a minimal Board with the encoder's
    # square convention translated to python-chess's convention.
    b = _chess.Board.empty()
    for sq, piece_char in state.items():
        chess_sq = _cs_sq_to_chess_sq(sq)
        b.set_piece_at(chess_sq, _chess.Piece.from_symbol(piece_char))
    return {"ok": True, "fen": b.fen()}


# ---- §17.5 #4: load_fen -------------------------------------------


def load_fen(fen: str) -> Dict[str, Any]:
    """§17.5 ``loadFen``: parse a FEN into a 2D position dict.

    Returns the dict the encoder expects (``{sq_index: piece_char}``)
    plus a few derived attributes useful to consumers.

    Parameters
    ----------
    fen : str
        Standard chess FEN. Only the placement and side-to-move
        portions are consulted; castling rights / en passant /
        clocks are ignored.

    Returns
    -------
    dict with keys:

      * ``ok`` (bool): always ``True``.
      * ``position`` (dict[int, str]): ``{0..63: 'P'|...|'k'}``
        with empty squares omitted.
      * ``sideToMove`` (bool): ``True`` = white to move.
      * ``fen`` (str): the input FEN echoed back (canonicalized via
        ``chess.Board(fen).fen()``).
    """
    from chess_spectral import fen_to_pos
    import chess as _chess
    b = _chess.Board(fen)
    pos = fen_to_pos(fen)
    return {
        "ok": True,
        "position": dict(pos),
        "sideToMove": bool(b.turn),
        "fen": b.fen(),
    }


# ---- §17.5 #5: has_legal_moves ------------------------------------


def has_legal_moves(state: Any, *, side_to_move: Optional[bool] = None
                    ) -> Dict[str, Any]:
    """§17.5 ``hasLegalMoves``: is the side-to-move in stalemate /
    checkmate?

    Returns ``{'ok': True, 'hasLegalMoves': bool, 'count': int,
    'inCheck': bool}``. Used by consumers to decide whether to keep
    asking for moves at the current position.

    Parameters
    ----------
    state
        Either a :class:`chess.Board` or a position dict (which is
        materialized to a :class:`chess.Board` via
        :func:`get_fen_state` first).
    side_to_move : bool, optional
        Forced side-to-move override; defaults to whatever the input
        carries.
    """
    import chess as _chess
    if hasattr(state, "fen") and callable(state.fen):
        b = _chess.Board(state.fen())
    else:
        # Position dict — round-trip through FEN.
        result = get_fen_state(state)
        b = _chess.Board(result["fen"])
    if side_to_move is not None:
        b.turn = bool(side_to_move)
    legal = list(b.legal_moves)
    return {
        "ok": True,
        "hasLegalMoves": len(legal) > 0,
        "count": len(legal),
        "inCheck": bool(b.is_check()),
    }


# ---- Pyodide-bridge serialization helper --------------------------


def complex_to_interleaved_float32(psi: np.ndarray) -> np.ndarray:
    """Serialize a complex ψ to a Float32 array of interleaved
    real+imag pairs. Same on-the-wire format as
    :func:`chess_spectral.qm_4d_bridge.complex_to_interleaved_float32`
    (the chess4D-OC consumer reads either via ``Float32Array``).

    For a complex array of length N, returns a Float32 array of
    length 2N with ``out[0::2] = ψ.real`` and ``out[1::2] = ψ.imag``.
    """
    p = np.ascontiguousarray(psi, dtype=np.complex128)
    out = np.empty(2 * p.size, dtype=np.float32)
    out[0::2] = p.real.astype(np.float32, copy=False)
    out[1::2] = p.imag.astype(np.float32, copy=False)
    return out


# ---- §17.2 #1: get_qm_state ---------------------------------------


def get_qm_state(state: Any, *, side_to_move: bool = True) -> Dict[str, Any]:
    """§17.2 ``getQmState``: current ψ as Float32 interleaved real+imag.

    The 2D analogue of :func:`qm_4d_bridge.get_qm_state`. Drives the
    M14.x raw-amplitude / phase-as-color / trajectory render in the
    2D consumer (chess4d-OC's 2D sibling).

    Parameters
    ----------
    state
        Position dict ``{sq: piece}`` or :class:`chess.Board` (its
        ``.fen()`` is parsed back into a position dict).
    side_to_move : bool, optional
        ``True`` = white to move (default); forwarded to
        :func:`chess_spectral.qm_2d.state_to_psi`.

    Returns
    -------
    dict with keys:

      * ``ok`` (bool): always ``True`` for valid input.
      * ``psi`` (ndarray[float32, (1280,)]): real+imag interleaved
        Float32 of the 640-dim complex ψ.
      * ``basisDim`` (int): always ``640``.
      * ``normSq`` (float): ``⟨ψ|ψ⟩``. Equals ``1.0`` within float
        rounding for any non-empty position.
    """
    from chess_spectral import qm_2d as _qm2
    pos = _state_to_position_dict(state)
    psi = _qm2.state_to_psi(pos, bool(side_to_move))
    return {
        "ok": True,
        "psi": complex_to_interleaved_float32(psi),
        "basisDim": int(_qm2.ENCODING_DIM),
        "normSq": float(np.vdot(psi, psi).real),
    }


# ---- §17.2 #2: get_qm_density -------------------------------------


def get_qm_density(state: Any, *, side_to_move: bool = True) -> Dict[str, Any]:
    """§17.2 ``getQmDensity``: ``|ψ|²`` per cell on the 64-cell lattice
    (full-position, summed across 10 channels).

    Per-piece marginals (``piece_id`` arg in 4D) require partial-trace
    machinery and are deferred to v1.7+; this 2D bridge only ships the
    full-position density.

    Returns
    -------
    dict with keys:

      * ``ok`` (bool): always ``True``.
      * ``density`` (ndarray[float32, (64,)]): per-cell sum of
        ``|ψ_chan(cell)|²`` across the 10 channels. For a normalized
        ψ, ``density.sum() == 1.0`` within float rounding.
    """
    from chess_spectral import qm_2d as _qm2
    pos = _state_to_position_dict(state)
    psi = _qm2.state_to_psi(pos, bool(side_to_move))
    # Reshape (640,) -> (10 channels, 64 cells); per-cell sum-of-|·|²
    # across channels = total density per cell.
    block = psi.reshape(10, 64)
    density = (np.abs(block) ** 2).sum(axis=0).astype(np.float32)
    return {"ok": True, "density": density}


# ---- §17.2 #3: get_qm_expectation ---------------------------------


def get_qm_expectation(
    state: Any,
    observable: str,
    *,
    side_to_move: bool = True,
) -> Dict[str, Any]:
    """§17.2 ``getQmExpectation``: ``⟨ψ|(I_{10} ⊗ H_p)|ψ⟩`` for a
    Hermitian piece-reach observable ``H_p``.

    The 2D analogue of :func:`qm_4d_bridge.get_qm_expectation`. Uses
    :func:`chess_spectral.qm_2d.expectation` per-channel and sums.

    Parameters
    ----------
    state
        Position dict or :class:`chess.Board`.
    observable : str
        One of ``'rook'``, ``'bishop'``, ``'queen'``, ``'king'``,
        ``'knight'`` (case-insensitive). ``'pawn'`` raises ``ValueError``
        — the pawn observable's directed reach breaks Hermiticity, same
        constraint as the 4D side.
    side_to_move : bool, optional
        Forwarded to :func:`state_to_psi`.

    Returns
    -------
    dict with keys:

      * ``ok`` (bool): always ``True`` for valid input.
      * ``observable`` (str): canonical name.
      * ``expectation`` (float): real-valued ``⟨ψ|H_full|ψ⟩`` summed
        across the 10 channels.
    """
    from chess_spectral import qm_2d as _qm2
    name = observable.strip().lower()
    pieces = {
        "rook": _qm2.H_rook_2,
        "bishop": _qm2.H_bishop_2,
        "queen": _qm2.H_queen_2,
        "king": _qm2.H_king_2,
        "knight": _qm2.H_knight_2,
    }
    if name == "pawn":
        raise ValueError(
            "pawn observable not available: directed reach breaks "
            "Hermiticity. Same constraint as the 4D side."
        )
    if name not in pieces:
        raise ValueError(
            f"unknown observable {observable!r}; expected one of "
            f"{sorted(pieces)} (case-insensitive)"
        )
    H = pieces[name]
    pos = _state_to_position_dict(state)
    psi = _qm2.state_to_psi(pos, bool(side_to_move))
    # Sum the per-channel expectation values: ψ has 10 channel blocks
    # of 64; H acts on each block via I_{10} ⊗ H, so the total is just
    # sum_c <psi_c | H | psi_c>.
    total = 0.0
    block = psi.reshape(10, 64)
    for c in range(10):
        total += float(_qm2.expectation(H, block[c]))
    return {
        "ok": True,
        "observable": name,
        "expectation": total,
    }


# ---- Internal helpers --------------------------------------------


def _state_to_position_dict(state: Any) -> Dict[int, str]:
    """Coerce ``state`` to a 2D position dict {sq: piece_char}.

    Accepts:
      * :class:`chess.Board` — round-tripped through ``state_to_psi``'s
        ``fen_to_pos(board.fen())`` form.
      * Object with ``.position`` attribute (e.g., a future
        ``GameState2D``).
      * Position dict — passed through unchanged.
    """
    if hasattr(state, "fen") and callable(state.fen):
        from chess_spectral import fen_to_pos
        return dict(fen_to_pos(state.fen()))
    if hasattr(state, "position"):
        return dict(state.position)
    return dict(state)


# ---- §17.2 #4: apply_move_qm --------------------------------------


def apply_move_qm(
    pre_state: Any,
    post_state: Any,
    *,
    from_sq: Optional[int] = None,
    to_sq: Optional[int] = None,
    side_to_move_post: bool = True,
    return_per_channel: bool = False,
) -> Dict[str, Any]:
    """§17.2 ``applyMoveQm``: assemble the post-move ψ from pre-move
    ψ + the move endpoints + the post-move position.

    The 2D analogue of :func:`qm_4d_bridge.apply_move_qm`. Strategy:

      * **A_1 channel** (channel 0): if ``from_sq`` and ``to_sq`` are
        given AND the move is a non-capture (assertion: ``post_state``
        has the same set of squares occupied as ``pre_state`` minus
        ``from_sq`` plus ``to_sq``), apply the strict-unitary
        :func:`qm_2d_dynamics.u_move_a1_2d` operator directly:
        ``psi_post[0:64] = U_a1 @ psi_pre[0:64]``.

      * **All other channels** (1..9): re-encode the post-move
        position via :func:`qm_2d.state_to_psi` and slice the
        relevant 64-block. This is the **measurement-only re-encode
        pattern** that the 4D side uses for FIB_SYM_* channels — it's
        a known v1.5 fallback that produces correct post-move ψ
        without requiring per-channel u_move dynamics.

      * **Fallback**: if ``from_sq`` / ``to_sq`` are not provided, the
        entire post-ψ is re-encoded via ``state_to_psi(post_state)``.
        This is the pure measurement-only path; loses the per-channel
        detail but ships a correct post-move state.

    Parameters
    ----------
    pre_state, post_state
        Position dicts or objects with ``.position`` / ``.fen()``.
        ``post_state`` should already have the move applied (the
        bridge does NOT compute move semantics — caller uses
        python-chess to apply the move).
    from_sq, to_sq : int, optional
        Move endpoints in the chess_spectral square convention
        (``sq = row*8 + col``, row 0 = rank 8). When both are
        provided AND the move is a non-capture, the A_1 channel uses
        the strict-unitary path; otherwise the A_1 channel falls
        through to the re-encode path.
    side_to_move_post : bool, optional
        Side to move AFTER the move. Forwarded to
        :func:`qm_2d.state_to_psi` to set the Z_2 superselection
        sign on the re-encoded ψ.
    return_per_channel : bool, optional
        If ``True``, the return dict carries an extra
        ``per_channel`` entry with each channel's contribution to
        the post-ψ assembly (a mix of csr_matrix for A_1 strict-path
        and marker dicts for re-encode channels). Default ``False``
        keeps the return shape compact.

    Returns
    -------
    dict with keys:

      * ``ok`` (bool): always ``True`` for valid input.
      * ``psi_post`` (ndarray[float32, (1280,)]): assembled
        post-move ψ as interleaved real+imag.
      * ``basisDim`` (int): always ``640``.
      * ``normSq`` (float): ``⟨ψ_post|ψ_post⟩``. Equals ``1.0``
        within float rounding for any non-empty post-position.
      * ``per_channel`` (dict, optional): present iff
        ``return_per_channel=True``. Maps channel name (``'A1'``,
        ..., ``'FD'``) to either a 64×64 csr_matrix (the A_1
        strict-path operator, when applicable) or a marker dict
        with ``reason='measurement-only'`` and ``psi_post_block``
        (the re-encoded slice).
    """
    from chess_spectral import qm_2d as _qm2

    pre_pos = _state_to_position_dict(pre_state)
    post_pos = _state_to_position_dict(post_state)

    # The post-ψ assembly comes from re-encoding post_pos. This is the
    # measurement-only baseline: it's correct for all 10 channels.
    # The A_1 strict-path overlay is an optional refinement for
    # animation use cases.
    psi_post = _qm2.state_to_psi(post_pos, bool(side_to_move_post))

    use_strict_a1 = (
        from_sq is not None
        and to_sq is not None
        and 0 <= int(from_sq) < 64
        and 0 <= int(to_sq) < 64
        and int(from_sq) != int(to_sq)
        and _is_non_capture(pre_pos, post_pos, int(from_sq), int(to_sq))
    )

    per_channel: Dict[str, Any] = {}

    if use_strict_a1:
        # Build the strict A_1 unitary and verify its application
        # against the re-encoded baseline. The two should agree on
        # range(P_A1); they may differ off P_A1 but the re-encode is
        # also confined to range(P_A1) so they match either way.
        from chess_spectral.qm_2d_dynamics import u_move_a1_2d
        U_a1 = u_move_a1_2d(int(from_sq), int(to_sq))
        psi_pre = _qm2.state_to_psi(pre_pos, bool(side_to_move_post))
        psi_post_a1 = U_a1 @ psi_pre[0:64]
        # Splice the strict-path A_1 block into the assembled post-ψ.
        psi_post = psi_post.copy()
        psi_post[0:64] = psi_post_a1
        # Renormalise; the projector-sandwich U_a1 is sub-unitary on
        # cross-orbit moves so the assembled ψ may not be exactly
        # unit norm.
        n = float(np.linalg.norm(psi_post))
        if n > 0:
            psi_post = psi_post / n

        if return_per_channel:
            per_channel["A1"] = U_a1
    else:
        if return_per_channel:
            per_channel["A1"] = {
                "reason": "measurement-only",
                "psi_post_block": psi_post[0:64].copy(),
            }

    if return_per_channel:
        # Channels 1..9 are always measurement-only (re-encode-derived).
        from chess_spectral.encoder import CHANNELS
        for name, start in CHANNELS:
            if name == "A1":
                continue
            per_channel[name] = {
                "reason": "measurement-only",
                "psi_post_block": psi_post[start:start + 64].copy(),
            }

    out = {
        "ok": True,
        "psi_post": complex_to_interleaved_float32(psi_post),
        "basisDim": int(_qm2.ENCODING_DIM),
        "normSq": float(np.vdot(psi_post, psi_post).real),
    }
    if return_per_channel:
        out["per_channel"] = per_channel
    return out


def _is_non_capture(pre_pos: Dict[int, str], post_pos: Dict[int, str],
                    from_sq: int, to_sq: int) -> bool:
    """Detect whether the (from_sq, to_sq) move on (pre_pos, post_pos)
    was a non-capture. Defined as: every square in pre_pos is also in
    post_pos UNLESS it's the source square; AND the destination square
    moved from ``not in pre_pos`` to ``in post_pos``."""
    pre_squares = set(pre_pos.keys())
    post_squares = set(post_pos.keys())
    # Symmetric difference: squares whose occupancy changed.
    changed = pre_squares.symmetric_difference(post_squares)
    # For a non-capture move, exactly two squares change occupancy:
    # from_sq (was occupied, now empty) and to_sq (was empty, now
    # occupied).
    return changed == {from_sq, to_sq} and from_sq in pre_pos and to_sq in post_pos


__all__ = [
    "get_version", "get_encoder_shape",
    "get_fen_state", "load_fen", "has_legal_moves",
    "complex_to_interleaved_float32",
    "get_qm_state", "get_qm_density", "get_qm_expectation",
    "apply_move_qm",
]
