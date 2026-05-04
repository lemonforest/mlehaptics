"""Non-Markovian sheet aux block (1.9.0 — representation completeness).

The base 640-dim 2D and 45056-dim 4D encoders are functions of the
*current position only*. They cannot represent the four chess facts
that live in the game's history rather than its current placement:

  1. Castling rights (4 bits: white kingside / queenside, black ks / qs)
  2. En-passant target square (5 bits: file 0-7 + an "EP active" flag)
  3. Side to move (1 bit)
  4. Half-move clock (Z_101, encoded as a Fourier carrier)
  5. Repetition count of the current position (2 bits, threshold 3)

This module ships an 11-dim aux block that carries all five facts
alongside an encoder vector, so downstream consumers of *saved* or
*transmitted* vectors don't need to also marshal a python-chess Board
or GameState4D alongside.

**Representation only — this is NOT a speed feature.** The §19 spike
in [chess_spectral_research_notebook.md](../../../chess_spectral_research_notebook.md)
documents the mathematical analysis and the Phase 1 minimal sheet
proposal. The empirical bound (§19.10) confirms that single-position
queries against bitboards (python-chess `has_castling_rights`, the
1-int-AND attribute access on Board4D's `halfmove_clock`, the hash-
table lookup for repetition) cannot be undercut by float-numpy slice
+ decode. The sheet block is shipped to make encoder vectors *self-
sufficient* — for save/load roundtrip, batched retrieval over saved
corpora, and Pyodide / chess4D-OC consumers that want to reason about
non-Markov state without reconstructing a board.

Layout (11 dims, indexed from offset 640 in 2D, offset 45056 in 4D):

  aux[0]   castling_wk      ∈ {0.0, 1.0}    white kingside right
  aux[1]   castling_wq      ∈ {0.0, 1.0}    white queenside right
  aux[2]   castling_bk      ∈ {0.0, 1.0}    black kingside right
  aux[3]   castling_bq      ∈ {0.0, 1.0}    black queenside right
  aux[4]   ep_active        ∈ {0.0, 1.0}    1 iff EP target exists
  aux[5]   ep_file          ∈ [0.0, 7.0]    file index (0=a..7=h); 0 if not active
  aux[6]   side_to_move     ∈ {0.0, 1.0}    0=white, 1=black
  aux[7]   repetition_count ∈ [0.0, 2.0]    times current position seen before (claim threshold = 3)
  aux[8]   halfmove_cos     ∈ [-1.0, 1.0]   cos(2π · halfmove / 101)
  aux[9]   halfmove_sin     ∈ [-1.0, 1.0]   sin(2π · halfmove / 101)
  aux[10]  reserved         ∈ {0.0}         reserved for 1.10+; consumers should not assume any value

For 4D-OC positions, slots 0-5 are zero (castling and EP are not part
of the Oana-Chiru ruleset; see [spatial_4d/board.py](spatial_4d/board.py)
header comment). The remaining slots (side_to_move, repetition_count,
halfmove cos/sin) are populated as for 2D.

**Half-move clock encoding.** The cos/sin pair is a Z_101 Fourier
carrier preserving clock-distance fidelity (clocks 50 and 51 map to
adjacent points on the unit circle). The 50-move-rule threshold (100)
is handled at the consumer side: integer halfmove >= 100 is the
practical check, and integer recovery from the cos/sin pair via
``decode_halfmove_clock`` rounds to the nearest of [0, 100]. Consumers
who need exact threshold detection should track halfmove explicitly;
the sheet block is for representation, not arithmetic precision.

The aux block is opt-in via the ``sheets=`` kwarg to ``encode_640`` and
``encode_4d``. Without it, encoder output is byte-identical to pre-
1.9.0 versions and to the C encoder, preserving the reproducibility
contract enforced by ``test_c_py_parity*``.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

import numpy as np

if TYPE_CHECKING:
    import chess
    from chess_spectral_4d.move_history import GameState4D


# ─── Public layout constants ────────────────────────────────────────

SHEET_AUX_DIM: int = 11
"""Number of dimensions added to the encoder output when ``sheets=`` is supplied."""

SHEET_OFFSET_2D: int = 640
"""Offset where the aux block starts in a 2D encoded vector with sheets."""

SHEET_OFFSET_4D: int = 45056
"""Offset where the aux block starts in a 4D encoded vector with sheets."""

HALFMOVE_PERIOD: int = 101
"""Cyclic period for the halfmove Fourier carrier (covers [0, 100], inclusive)."""

REPETITION_CLAIM_THRESHOLD: int = 3
"""FIDE-canonical threefold-repetition claim threshold."""

FIFTY_MOVE_THRESHOLD: int = 100
"""FIDE-canonical fifty-move rule threshold (in half-moves)."""

# Indexed slot positions within the 11-dim aux block (offset from
# whichever SHEET_OFFSET_* applies). Use these named indices instead
# of magic numbers; the positions are part of the wire contract and
# should not move without a notebook §19 spec update + version bump.
SLOT_CASTLING_WK: int = 0
SLOT_CASTLING_WQ: int = 1
SLOT_CASTLING_BK: int = 2
SLOT_CASTLING_BQ: int = 3
SLOT_EP_ACTIVE: int = 4
SLOT_EP_FILE: int = 5
SLOT_SIDE_TO_MOVE: int = 6
SLOT_REPETITION: int = 7
SLOT_HALFMOVE_COS: int = 8
SLOT_HALFMOVE_SIN: int = 9
SLOT_RESERVED: int = 10


# ─── SheetState dataclass ───────────────────────────────────────────


@dataclass(frozen=True)
class SheetState:
    """Non-Markovian state to ride alongside the spectral encoder vector.

    All fields default to "neutral" values: no castling rights, no EP
    target, white to move, no repetition, halfmove=0. Construct
    directly for synthetic positions, or use the ``from_*`` factories
    to lift state from the project's existing position types.
    """

    castling_wk: bool = False
    castling_wq: bool = False
    castling_bk: bool = False
    castling_bq: bool = False
    ep_file: Optional[int] = None
    """File index 0-7 of the en-passant target, or None if no EP target."""
    side_to_move_white: bool = True
    """True if it is white to move; False otherwise."""
    halfmove_clock: int = 0
    """Half-move counter for the 50-move rule. Range [0, 100]; values
    above are clamped to 100 for the cos/sin encoding (50-move rule
    has triggered)."""
    repetition_count: int = 0
    """Count of how many times the current position has occurred
    earlier in the game. 0 = first occurrence; 2 = third occurrence
    (a draw can be claimed). Clamped to [0, 2] in the aux block."""

    # ─── Factories ────────────────────────────────────────────────

    @classmethod
    def from_chess_board(cls, board: "chess.Board") -> "SheetState":
        """Lift state from a python-chess :class:`chess.Board`.

        Repetition count is set to 0 for boards-without-history; pass
        a board that has had moves played through it to capture the
        actual repetition state, OR set ``repetition_count`` manually
        via :meth:`with_repetition`.
        """
        import chess
        ep_file: Optional[int] = None
        if board.ep_square is not None:
            ep_file = chess.square_file(board.ep_square)
        # python-chess: board.is_repetition(2) means current position
        # has been seen at least twice before; (3) means three-fold.
        # We map to the 0/1/2 bucketing of the aux block.
        rep = 0
        try:
            if board.is_repetition(3):
                rep = 2
            elif board.is_repetition(2):
                rep = 1
        except Exception:
            # is_repetition can fail on artificially-constructed boards
            # without move history; leave rep=0 in that case.
            rep = 0
        return cls(
            castling_wk=bool(board.has_kingside_castling_rights(chess.WHITE)),
            castling_wq=bool(board.has_queenside_castling_rights(chess.WHITE)),
            castling_bk=bool(board.has_kingside_castling_rights(chess.BLACK)),
            castling_bq=bool(board.has_queenside_castling_rights(chess.BLACK)),
            ep_file=ep_file,
            side_to_move_white=bool(board.turn == chess.WHITE),
            halfmove_clock=int(board.halfmove_clock),
            repetition_count=rep,
        )

    @classmethod
    def from_game_state_4d(cls, state: "GameState4D") -> "SheetState":
        """Lift state from a :class:`chess_spectral_4d.GameState4D`.

        4D-OC has no castling and no en-passant per the ruleset
        (see ``spatial_4d/board.py`` header). Castling slots and EP
        are forced to neutral values; halfmove clock, side to move,
        and repetition count are populated from the GameState.
        """
        # Lazy import to avoid a hard dep — this module is importable
        # without chess_spectral_4d available.
        from chess_spectral_4d.move_history import SIDE_WHITE
        rep = 0
        try:
            n = state.history.repetition_count(state.position)
            # repetition_count returns total occurrences including
            # current; bucket to (0, 1, 2) for "times seen before".
            rep = max(0, min(2, n - 1))
        except Exception:
            rep = 0
        return cls(
            castling_wk=False,
            castling_wq=False,
            castling_bk=False,
            castling_bq=False,
            ep_file=None,
            side_to_move_white=(state.side_to_move == SIDE_WHITE),
            halfmove_clock=int(state.history.half_move_clock),
            repetition_count=rep,
        )

    # ─── Convenience updaters ─────────────────────────────────────

    def with_repetition(self, count: int) -> "SheetState":
        """Return a copy with ``repetition_count`` set explicitly.

        Useful when consuming a python-chess Board that hasn't tracked
        history but the consumer knows the count from elsewhere.
        """
        return SheetState(
            castling_wk=self.castling_wk,
            castling_wq=self.castling_wq,
            castling_bk=self.castling_bk,
            castling_bq=self.castling_bq,
            ep_file=self.ep_file,
            side_to_move_white=self.side_to_move_white,
            halfmove_clock=self.halfmove_clock,
            repetition_count=max(0, min(2, count)),
        )


# ─── Encode ─────────────────────────────────────────────────────────


def encode_aux_block(state: SheetState) -> np.ndarray:
    """Serialize a :class:`SheetState` to the 11-dim aux block.

    Returns a fresh ``np.ndarray`` of shape ``(11,)`` and dtype
    ``float64`` (matching the base encoder's dtype). The output is
    deterministic and bit-stable for byte-identical inputs across
    runs (no random seeding involved).
    """
    aux = np.zeros(SHEET_AUX_DIM, dtype=np.float64)
    aux[SLOT_CASTLING_WK] = 1.0 if state.castling_wk else 0.0
    aux[SLOT_CASTLING_WQ] = 1.0 if state.castling_wq else 0.0
    aux[SLOT_CASTLING_BK] = 1.0 if state.castling_bk else 0.0
    aux[SLOT_CASTLING_BQ] = 1.0 if state.castling_bq else 0.0
    if state.ep_file is not None:
        aux[SLOT_EP_ACTIVE] = 1.0
        aux[SLOT_EP_FILE] = float(int(state.ep_file) & 0x7)
    else:
        aux[SLOT_EP_ACTIVE] = 0.0
        aux[SLOT_EP_FILE] = 0.0
    aux[SLOT_SIDE_TO_MOVE] = 0.0 if state.side_to_move_white else 1.0
    aux[SLOT_REPETITION] = float(max(0, min(2, state.repetition_count)))
    # Halfmove Fourier carrier. Clamp to [0, FIFTY_MOVE_THRESHOLD]
    # before encoding — values above 100 mean the rule has triggered
    # and the exact value no longer matters for play.
    h = max(0, min(FIFTY_MOVE_THRESHOLD, int(state.halfmove_clock)))
    theta = 2.0 * math.pi * h / float(HALFMOVE_PERIOD)
    aux[SLOT_HALFMOVE_COS] = math.cos(theta)
    aux[SLOT_HALFMOVE_SIN] = math.sin(theta)
    aux[SLOT_RESERVED] = 0.0
    return aux


# ─── Decode (round-trip getters) ────────────────────────────────────


def _slot(vec: np.ndarray, slot: int, offset: int) -> float:
    """Read a single aux slot as a python float, with bounds-check."""
    idx = offset + slot
    if idx < 0 or idx >= len(vec):
        raise IndexError(
            f"sheet slot {slot} at offset {offset} (idx {idx}) is "
            f"out of bounds for vector of length {len(vec)}"
        )
    return float(vec[idx])


def decode_castling_rights(
    vec: np.ndarray, offset: int = SHEET_OFFSET_2D,
) -> tuple[bool, bool, bool, bool]:
    """Read (white-kingside, white-queenside, black-kingside,
    black-queenside) castling rights from a sheet-aware encoded vector.

    ``offset`` defaults to 640 (2D); pass ``SHEET_OFFSET_4D`` (45056)
    for a 4D vector.
    """
    return (
        _slot(vec, SLOT_CASTLING_WK, offset) >= 0.5,
        _slot(vec, SLOT_CASTLING_WQ, offset) >= 0.5,
        _slot(vec, SLOT_CASTLING_BK, offset) >= 0.5,
        _slot(vec, SLOT_CASTLING_BQ, offset) >= 0.5,
    )


def decode_ep_file(
    vec: np.ndarray, offset: int = SHEET_OFFSET_2D,
) -> Optional[int]:
    """Read the EP-target file from a sheet-aware encoded vector.

    Returns the file index 0-7 if EP is active, or ``None`` if not.
    """
    if _slot(vec, SLOT_EP_ACTIVE, offset) < 0.5:
        return None
    return int(round(_slot(vec, SLOT_EP_FILE, offset))) & 0x7


def decode_side_to_move_white(
    vec: np.ndarray, offset: int = SHEET_OFFSET_2D,
) -> bool:
    """Read the side-to-move flag. ``True`` for white, ``False`` for black."""
    return _slot(vec, SLOT_SIDE_TO_MOVE, offset) < 0.5


def decode_repetition_count(
    vec: np.ndarray, offset: int = SHEET_OFFSET_2D,
) -> int:
    """Read the repetition count (0, 1, or 2) of the current position."""
    return max(0, min(2, int(round(_slot(vec, SLOT_REPETITION, offset)))))


def decode_halfmove_clock(
    vec: np.ndarray, offset: int = SHEET_OFFSET_2D,
) -> int:
    """Recover the half-move clock as an integer in [0, 100].

    Inverts the Z_101 Fourier carrier via ``atan2``. Round-trip exact
    for integer halfmove inputs in [0, 100] (verified by
    ``test_sheets_aux_block.py``).
    """
    c = _slot(vec, SLOT_HALFMOVE_COS, offset)
    s = _slot(vec, SLOT_HALFMOVE_SIN, offset)
    theta = math.atan2(s, c)
    if theta < 0:
        theta += 2.0 * math.pi
    h = int(round(theta * float(HALFMOVE_PERIOD) / (2.0 * math.pi)))
    return max(0, min(FIFTY_MOVE_THRESHOLD, h))


def decode_sheet_state(
    vec: np.ndarray, offset: int = SHEET_OFFSET_2D,
) -> SheetState:
    """Read all sheet fields back into a :class:`SheetState` in one call.

    Equivalent to calling each ``decode_*`` getter individually but
    avoids the bounds-check overhead per slot.
    """
    cwk, cwq, cbk, cbq = decode_castling_rights(vec, offset)
    return SheetState(
        castling_wk=cwk,
        castling_wq=cwq,
        castling_bk=cbk,
        castling_bq=cbq,
        ep_file=decode_ep_file(vec, offset),
        side_to_move_white=decode_side_to_move_white(vec, offset),
        halfmove_clock=decode_halfmove_clock(vec, offset),
        repetition_count=decode_repetition_count(vec, offset),
    )


# ─── Module exports ─────────────────────────────────────────────────


__all__ = [
    # Layout constants
    "SHEET_AUX_DIM",
    "SHEET_OFFSET_2D",
    "SHEET_OFFSET_4D",
    "HALFMOVE_PERIOD",
    "REPETITION_CLAIM_THRESHOLD",
    "FIFTY_MOVE_THRESHOLD",
    # Slot indices
    "SLOT_CASTLING_WK", "SLOT_CASTLING_WQ",
    "SLOT_CASTLING_BK", "SLOT_CASTLING_BQ",
    "SLOT_EP_ACTIVE", "SLOT_EP_FILE",
    "SLOT_SIDE_TO_MOVE", "SLOT_REPETITION",
    "SLOT_HALFMOVE_COS", "SLOT_HALFMOVE_SIN",
    "SLOT_RESERVED",
    # Dataclass + factories
    "SheetState",
    # Encode
    "encode_aux_block",
    # Decode
    "decode_castling_rights",
    "decode_ep_file",
    "decode_side_to_move_white",
    "decode_repetition_count",
    "decode_halfmove_clock",
    "decode_sheet_state",
]
