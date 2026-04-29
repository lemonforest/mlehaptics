"""chess_spectral_4d.bridge — Pyodide-bridge surface for v1.4.0.

This module is the consumer-facing entry point that the ``chess4D-OC``
worker (running chess-spectral inside Pyodide) calls into. Every
method here returns a plain Python value or a plain dict; nothing
here uses numpy, scipy, or sparse-matrix internals on its return path
so the cross-WASM boundary stays cheap.

Methods added in v1.4.0 (see notebook §17.3):

    * :func:`load_state`        — re-import a FEN4 placement literal.
    * :func:`get_draw_status`   — classify the current draw condition.
    * :func:`get_move_history`  — full ply history as plain dicts.
    * :func:`is_insufficient_material_2d`
                                 — 2D K-vs-K, K+B-vs-K, K+N-vs-K.

Methods deferred from v1.4.0 (will ship in later minors):

    * Stalemate detection — needs the QM/legal-moves observable
      currently being built in Track A's ``qm_4d`` work. Until then,
      :func:`get_draw_status` raises ``NotImplementedError`` for any
      stalemate query; callers should pass a pre-computed
      ``has_legal_moves=True`` to skip the stalemate branch.
    * 4D insufficient-material classification — open design question
      (4D K vs K is still drawn, but K+B vs K depends on bishop
      "color class" which is more nuanced on Z_8^4). v1.4.0 ships the
      2D version + ``NotImplementedError`` for 4D until a follow-up
      ADR resolves the rule.

Bridge contract: every function here returns either:
    * a plain dict ``{"ok": True, ...}`` for success cases, or
    * a plain dict ``{"ok": False, "error": "..."}`` for caller-side
      input errors (so the worker doesn't have to translate Python
      exceptions across the WASM boundary).
"""

from __future__ import annotations

from typing import Dict, List, Optional, Union

from chess_spectral import fen_4d as _fen_4d

from chess_spectral_4d.move_history import (
    GameState4D,
    Position4D,
    SIDE_BLACK,
    SIDE_WHITE,
)


# ─── Threefold + 50-move thresholds ─────────────────────────────────

THREEFOLD_THRESHOLD: int = 3
"""FIDE Article 9.2: a position repeated three times is a draw."""

FIFTY_MOVE_THRESHOLD: int = 100
"""FIDE Article 9.3: 50 full moves without a pawn move or capture is
a draw — i.e. half_move_clock >= 100 ⇒ draw."""


# ─── load_state ─────────────────────────────────────────────────────

def load_state(
    fen4: str,
    side_to_move: int = SIDE_WHITE,
) -> Dict[str, object]:
    """Re-import a FEN4 v1 placement literal into a fresh
    :class:`GameState4D`.

    The consumer calls this when transferring a position from JS-side
    storage (or pasting a literal from the user) into the Pyodide
    worker — it's the inverse of :meth:`GameState4D.to_fen4`.

    Parameters
    ----------
    fen4
        Placement literal accepted by :func:`chess_spectral.fen_4d.parse`.
    side_to_move
        ``SIDE_WHITE`` (0) or ``SIDE_BLACK`` (1). Defaults to White
        per FIDE Article 4.7. FEN4 v1 does not encode side-to-move
        on the wire (intentionally — keeps the placement literal
        side-symmetric for fixture comparisons).

    Returns
    -------
    dict
        ``{"ok": True, "state": GameState4D}`` on success, or
        ``{"ok": False, "error": "<msg>"}`` if the FEN4 doesn't parse.
    """
    try:
        state = GameState4D.from_fen4(fen4, side_to_move=side_to_move)
    except _fen_4d.Fen4ParseError as e:
        return {"ok": False, "error": str(e)}
    except (ValueError, TypeError) as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}
    return {"ok": True, "state": state}


# ─── 2D insufficient material classification ────────────────────────

def is_insufficient_material_2d(
    pos_2d: Dict[int, str],
) -> bool:
    """Detect insufficient-material draws on the 2D board (8×8).

    Returns ``True`` for the FIDE/USCF "obvious draw" set:
        * K vs K
        * K + B vs K (regardless of bishop color)
        * K + N vs K
        * K + B vs K + B with bishops on the same color squares
          (matches python-chess's classification — the lone-bishop
          case below covers the non-same-color case as "not
          insufficient" because the side with two opposite-color
          bishops can still mate, but two same-color bishops cannot).

    Returns ``False`` whenever a side has more than one minor piece
    of opposite colors, any pawn, any rook, or any queen.

    Parameters
    ----------
    pos_2d
        Dict mapping ``square_index → piece_char`` (the 2D encoder's
        position format). Square index = ``row * 8 + col``.
    """
    # Tally by uppercased piece type, splitting by case for color.
    white_minors: List[int] = []
    black_minors: List[int] = []
    has_heavy_or_pawn = False
    bishop_squares_white: List[int] = []
    bishop_squares_black: List[int] = []

    for sq, piece in pos_2d.items():
        if piece in ("K", "k"):
            continue
        if piece in ("P", "p", "R", "r", "Q", "q"):
            has_heavy_or_pawn = True
            break
        if piece in ("N", "B"):
            white_minors.append(sq)
            if piece == "B":
                bishop_squares_white.append(sq)
        elif piece in ("n", "b"):
            black_minors.append(sq)
            if piece == "b":
                bishop_squares_black.append(sq)
        else:
            # Unknown piece — be conservative and call it sufficient.
            has_heavy_or_pawn = True
            break

    if has_heavy_or_pawn:
        return False

    # K vs K — definitely insufficient.
    if not white_minors and not black_minors:
        return True

    # K + (single minor) vs K — one bishop or one knight cannot
    # force mate against a lone king. Order matters: must be the
    # *only* minor on its side, with the other side bare.
    if len(white_minors) <= 1 and len(black_minors) == 0:
        return True
    if len(black_minors) <= 1 and len(white_minors) == 0:
        return True

    # K + B vs K + B with bishops on same color squares — neither
    # side can force mate (their bishops are confined to opposite
    # color complements of the same color class). Opposite-color
    # bishops + lone kings is technically still drawable in most
    # positions, but the formal rule says "sufficient" (matches
    # python-chess).
    if (len(bishop_squares_white) == 1 and len(bishop_squares_black) == 1
            and len(white_minors) == 1 and len(black_minors) == 1):
        # 2D square color = (row + col) % 2 = (sq // 8 + sq % 8) % 2
        wsq = bishop_squares_white[0]
        bsq = bishop_squares_black[0]
        wcol = (wsq // 8 + wsq % 8) % 2
        bcol = (bsq // 8 + bsq % 8) % 2
        if wcol == bcol:
            return True

    return False


def is_insufficient_material_4d(pos: Position4D) -> bool:
    """Detect insufficient-material draws on the 4D board.

    Currently raises :class:`NotImplementedError`; the 4D analog
    requires deciding on the bishop "color class" rule on Z_8^4 (an
    open design question — see notebook §17.3). v1.4.0 ships this as
    a placeholder so the bridge surface is complete; v1.5.x or v1.6.x
    will resolve it via a dedicated ADR.

    Parameters
    ----------
    pos
        4D position dict (live ``GameState4D.position``).
    """
    raise NotImplementedError(
        "4D insufficient-material classification is deferred — "
        "the rule for the 4D bishop color class on Z_8^4 is an open "
        "design question (see notebook §17.3 / pending ADR). v1.4.0 "
        "ships the 2D version (is_insufficient_material_2d) only."
    )


# ─── get_draw_status ────────────────────────────────────────────────

DrawStatus = str  # 'none' | 'threefold' | 'fifty-move' | 'insufficient' | 'stalemate'


def get_draw_status(
    state: GameState4D,
    *,
    has_legal_moves: Optional[bool] = None,
) -> Dict[str, object]:
    """Classify the current draw condition.

    Returns a single string from
    ``{'none', 'threefold', 'fifty-move', 'insufficient', 'stalemate'}``.
    Detection order (matches python-chess):

        1. threefold repetition (fastest — hash-table lookup)
        2. fifty-move rule (clock check)
        3. insufficient material (currently 2D-only — raises
           :class:`NotImplementedError` for 4D positions until the
           4D rule is fixed)
        4. stalemate (requires legal-move generation)

    Parameters
    ----------
    state
        Live :class:`GameState4D`.
    has_legal_moves
        Optional bypass for the stalemate check. If ``None`` (default),
        and the threefold/50-move/insufficient checks all return
        'none', this function raises :class:`NotImplementedError` to
        signal that the consumer needs to wire up legal-move
        generation. If a boolean is supplied:
            * ``True``: never returns 'stalemate' (skips the check).
            * ``False``: returns 'stalemate' if no other draw fires.

    Returns
    -------
    dict
        ``{"ok": True, "status": <DrawStatus>}`` on classification, or
        ``{"ok": False, "error": "..."}`` on an internal error.
    """
    # 1) Threefold.
    if state.history.repetition_count(state.position) >= THREEFOLD_THRESHOLD:
        return {"ok": True, "status": "threefold"}

    # 2) Fifty-move rule.
    if state.history.half_move_clock >= FIFTY_MOVE_THRESHOLD:
        return {"ok": True, "status": "fifty-move"}

    # 3) Insufficient material — 4D placeholder raises.
    try:
        if is_insufficient_material_4d(state.position):
            return {"ok": True, "status": "insufficient"}
    except NotImplementedError:
        # 4D classification deferred. Fall through; we still return
        # 'none' / 'stalemate' / threefold / 50-move correctly.
        pass

    # 4) Stalemate — needs legal-move generation.
    if has_legal_moves is False:
        return {"ok": True, "status": "stalemate"}
    if has_legal_moves is None:
        # Caller didn't tell us; we can't decide. Refuse rather than
        # silently mis-classify a stalemate as 'none'.
        raise NotImplementedError(
            "stalemate detection requires a no-legal-moves check; "
            "pass has_legal_moves=True/False explicitly. 4D legal-move "
            "generation is wired in v1.5+ (the QM observable in the "
            "Track A roadmap). For 2D callers, evaluate stalemate via "
            "python-chess and pass the boolean through."
        )

    return {"ok": True, "status": "none"}


# ─── get_move_history ───────────────────────────────────────────────

def get_move_history(
    state: GameState4D,
) -> Dict[str, object]:
    """Return the full ply-by-ply move history as plain dicts.

    Each entry uses the schema from
    :meth:`chess_spectral_4d.move_history.Move4D.to_dict`:

        {"ply": int, "from": [x,y,z,w], "to": [x,y,z,w],
         "piece": str, "halfMoveClock": int,
         "promoteTo"?: str, "capturedPiece"?: str}

    Parameters
    ----------
    state
        Live :class:`GameState4D`.

    Returns
    -------
    dict
        ``{"ok": True, "moves": [...]}``. ``moves`` is a list of
        plain dicts; an empty game returns an empty list.
    """
    return {"ok": True, "moves": state.history.to_list()}
