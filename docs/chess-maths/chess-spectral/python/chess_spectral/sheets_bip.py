"""Bit-Interleaved Phases (BIP) encoding for the non-Markovian sheet
block (1.10.0 — representation completeness, integer-native form).

The 1.9.0 sheet block (:mod:`chess_spectral.sheets`) ships an 11-dim
``float64`` aux block — 88 bytes per position — that is overwhelmingly
*categorical* in content (4 castling bits + 1 EP-active bit + 3
EP-file bits + 1 side-to-move bit + 2 repetition-count bits + a Z₁₀₁
half-move-clock element). 1.10.0 adds a parallel **BIP-encoded**
representation that packs the same content into **3 bytes** —
``uint16`` categorical + ``uint8`` half-move clock — round-trip exact
for every legal state tuple.

Why this exists
---------------

Notebook §20.14 documents the rationale; in brief, the BIP encoding:

  * Is **algebraically exact** for the 11 categorical bits (each is
    its own ``Z_2`` group element; HDC binding via integer XOR is a
    group isomorphism with the 1.9.0 float ``{0.0, 1.0}`` semantics).
  * Preserves the §19.4 "XOR-lite + Z_n-spectral split is structural"
    finding by keeping half-move-clock as its own ``uint8`` (Z₁₀₁
    embedded as raw integer with explicit modulo for evolution ops),
    rather than embedding it into ``Z_{128}`` with a wrap-discontinuity.
  * Yields ~29× compression (88 bytes → 3 bytes per position).
  * Enables operator fast paths via single integer ops:
    ``castling_alive``, ``kingside_castling_alive``,
    ``fifty_move_rule_triggered``, ``threefold_claimable``, etc.
  * Supports **Hamming-distance similarity** on the categorical
    portion — sharper than float-cosine-sim for binary state.
  * Does **not** beat python-chess's ``has_castling_rights`` at
    single-position depth-1 latency (per §19.10's depth-1 floor) —
    BIP's wins are at scale (Pyodide / batch retrieval / wire
    format), not at single-call latency.

Public API
----------

The 1.9.0 :class:`chess_spectral.sheets.SheetState` is the canonical
in-memory shape. This module provides:

  * :class:`SheetStateBIP` — the integer-encoded form.
  * :func:`encode_sheet_state_bip` — ``SheetState → SheetStateBIP``.
  * :func:`decode_sheet_state_bip` — ``SheetStateBIP → SheetState``.
  * Operator fast paths (``castling_alive``, etc.).
  * Distance metrics
    (:func:`hamming_distance_categorical`, :func:`halfmove_distance`).

Round-trip exactness
--------------------

For every legal ``SheetState`` (864 categorical × 101 half-move = 87,264
states), ``decode_sheet_state_bip(encode_sheet_state_bip(s)) == s``
holds bit-exactly. The :mod:`tests.test_sheets_bip` immolation suite
verifies this exhaustively.

The narrow edge cases:

  * ``halfmove_clock > 100`` is clamped to 100 in both 1.9.0 and BIP
    paths (50-move rule has triggered; the exact value above the
    threshold doesn't matter for play).
  * ``repetition_count > 2`` is clamped to 2 in both paths (a draw
    can already be claimed; saturation is fine).
  * ``ep_file is None`` and ``ep_file == 0`` with ``ep_active == 0``
    are the same on the wire; the BIP form follows the 1.9.0
    convention of storing ``ep_file = 0`` in the no-EP case.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .sheets import SheetState


# ─── Bit-layout constants ───────────────────────────────────────────
#
# These are part of the wire contract for the BIP aux block. See
# notebook §20.14. The layout is fixed-form starting in 1.10.0;
# changing any slot position is a breaking change.

BIT_CASTLING_WK: int = 0
BIT_CASTLING_WQ: int = 1
BIT_CASTLING_BK: int = 2
BIT_CASTLING_BQ: int = 3
BIT_EP_ACTIVE: int = 4
EP_FILE_LSB: int = 5
EP_FILE_MSB: int = 7  # bits[5:8] inclusive of LSB, exclusive of MSB+1
BIT_SIDE_TO_MOVE: int = 8
REPETITION_LSB: int = 9
REPETITION_MSB: int = 10  # bits[9:11] inclusive
RESERVED_LSB: int = 12  # bits[12:16] reserved, must be zero

CATEGORICAL_BITS_USED: int = 12  # bits[0:12] occupied; bits[12:16] reserved

# Convenience masks for the operator fast paths.
MASK_CASTLING: int = 0b1111  # bits[0:4]
MASK_KINGSIDE_CASTLING: int = 0b0101  # bits 0 (wk) + 2 (bk)
MASK_QUEENSIDE_CASTLING: int = 0b1010  # bits 1 (wq) + 3 (bq)
MASK_EP_ACTIVE: int = 1 << BIT_EP_ACTIVE
MASK_EP_FILE: int = 0b111 << EP_FILE_LSB
MASK_SIDE_TO_MOVE: int = 1 << BIT_SIDE_TO_MOVE
MASK_REPETITION: int = 0b11 << REPETITION_LSB
MASK_RESERVED: int = 0b1111 << RESERVED_LSB
MASK_CATEGORICAL_USED: int = (1 << CATEGORICAL_BITS_USED) - 1  # bits[0:12]

# Half-move clock semantics. Same as 1.9.0 sheets.py.
HALFMOVE_MIN: int = 0
HALFMOVE_MAX: int = 100  # 50-move rule threshold; values above clamp here

# Repetition count saturates at this value (claim is already available).
REPETITION_SATURATION: int = 2


# ─── SheetStateBIP dataclass ────────────────────────────────────────


@dataclass(frozen=True)
class SheetStateBIP:
    """BIP-encoded non-Markovian state (1.10.0+).

    Two integer fields per position, total 3 bytes:

      * ``categorical`` — ``uint16``-equivalent (Python int, but only
        bits[0:12] are populated; bits[12:16] are reserved and must
        read as zero). Holds the 11 categorical bits packed into the
        layout documented in :mod:`chess_spectral.sheets_bip`.
      * ``halfmove_clock`` — ``uint8``-equivalent (Python int; values
        in [0, 100]). Held separately because half-move is a Z₁₀₁
        element (non-power-of-2 cyclic group); embedding into
        ``Z_{128}`` would introduce a wrap-discontinuity that breaks
        the §19.4 "structural split" finding.

    The dataclass is frozen — all transformations produce a new
    ``SheetStateBIP``. This matches the 1.9.0
    :class:`chess_spectral.sheets.SheetState` contract.
    """

    categorical: int = 0
    halfmove_clock: int = 0

    def __post_init__(self) -> None:
        # Bounds-check both fields. We never want a SheetStateBIP with
        # garbage in the reserved bits or out-of-range half-move.
        if self.categorical < 0 or self.categorical > 0xFFFF:
            raise ValueError(
                f"SheetStateBIP.categorical={self.categorical} is out of "
                f"uint16 range [0, 65535]"
            )
        if self.categorical & MASK_RESERVED:
            raise ValueError(
                f"SheetStateBIP.categorical={self.categorical:#06x} has "
                f"non-zero reserved bits (mask={MASK_RESERVED:#06x}); "
                f"consumers must zero bits[12:16]"
            )
        if self.halfmove_clock < HALFMOVE_MIN or self.halfmove_clock > HALFMOVE_MAX:
            raise ValueError(
                f"SheetStateBIP.halfmove_clock={self.halfmove_clock} is out "
                f"of legal range [{HALFMOVE_MIN}, {HALFMOVE_MAX}]; values "
                f"above {HALFMOVE_MAX} should be clamped at encode time"
            )


# ─── Encode / decode (round-trip exact on the legal state space) ────


def encode_sheet_state_bip(state: "SheetState") -> SheetStateBIP:
    """Convert a 1.9.0 :class:`SheetState` to its BIP-encoded form.

    Round-trip exact: ``decode_sheet_state_bip(encode_sheet_state_bip(s))``
    equals ``s`` for every legal SheetState (864 categorical × 101
    half-move = 87,264 cases verified by the immolation suite).

    Edge cases:

      * ``state.ep_file is None`` is encoded as ``ep_active=0,
        ep_file=0`` (matches the 1.9.0 float-aux convention).
      * ``state.halfmove_clock > 100`` is clamped to 100.
      * ``state.repetition_count > 2`` is clamped to 2.
    """
    categorical = 0
    if state.castling_wk:
        categorical |= 1 << BIT_CASTLING_WK
    if state.castling_wq:
        categorical |= 1 << BIT_CASTLING_WQ
    if state.castling_bk:
        categorical |= 1 << BIT_CASTLING_BK
    if state.castling_bq:
        categorical |= 1 << BIT_CASTLING_BQ
    if state.ep_file is not None:
        categorical |= MASK_EP_ACTIVE
        categorical |= (int(state.ep_file) & 0x7) << EP_FILE_LSB
    if not state.side_to_move_white:
        categorical |= MASK_SIDE_TO_MOVE
    rep = max(0, min(REPETITION_SATURATION, int(state.repetition_count)))
    categorical |= rep << REPETITION_LSB
    halfmove = max(HALFMOVE_MIN, min(HALFMOVE_MAX, int(state.halfmove_clock)))
    return SheetStateBIP(categorical=categorical, halfmove_clock=halfmove)


def decode_sheet_state_bip(packed: SheetStateBIP) -> "SheetState":
    """Convert a :class:`SheetStateBIP` back to a 1.9.0
    :class:`SheetState`. Lossless round-trip from
    :func:`encode_sheet_state_bip`.

    The returned ``SheetState.ep_file`` is ``None`` when the EP-active
    bit is clear; otherwise the file index 0..7.
    """
    # Lazy import to avoid a circular dependency at module-load time —
    # sheets.py imports from this module (for the alias re-exports),
    # and this module needs SheetState only inside the body.
    from .sheets import SheetState

    cat = packed.categorical
    ep_file: Optional[int] = None
    if cat & MASK_EP_ACTIVE:
        ep_file = (cat >> EP_FILE_LSB) & 0x7
    return SheetState(
        castling_wk=bool(cat & (1 << BIT_CASTLING_WK)),
        castling_wq=bool(cat & (1 << BIT_CASTLING_WQ)),
        castling_bk=bool(cat & (1 << BIT_CASTLING_BK)),
        castling_bq=bool(cat & (1 << BIT_CASTLING_BQ)),
        ep_file=ep_file,
        side_to_move_white=not bool(cat & MASK_SIDE_TO_MOVE),
        halfmove_clock=int(packed.halfmove_clock),
        repetition_count=int((cat & MASK_REPETITION) >> REPETITION_LSB),
    )


# ─── Operator fast paths (single-integer ops, no FPU) ───────────────


def castling_alive(packed: SheetStateBIP) -> bool:
    """True if any castling right is still alive (any of WK/WQ/BK/BQ)."""
    return (packed.categorical & MASK_CASTLING) != 0


def kingside_castling_alive(packed: SheetStateBIP) -> bool:
    """True if either side's kingside castling right is alive."""
    return (packed.categorical & MASK_KINGSIDE_CASTLING) != 0


def queenside_castling_alive(packed: SheetStateBIP) -> bool:
    """True if either side's queenside castling right is alive."""
    return (packed.categorical & MASK_QUEENSIDE_CASTLING) != 0


def white_castling_alive(packed: SheetStateBIP) -> bool:
    """True if white retains either kingside or queenside castling."""
    return (packed.categorical & 0b0011) != 0  # bits 0 + 1


def black_castling_alive(packed: SheetStateBIP) -> bool:
    """True if black retains either kingside or queenside castling."""
    return (packed.categorical & 0b1100) != 0  # bits 2 + 3


def ep_target_active(packed: SheetStateBIP) -> bool:
    """True if there's an en-passant target on the current ply."""
    return (packed.categorical & MASK_EP_ACTIVE) != 0


def ep_file(packed: SheetStateBIP) -> Optional[int]:
    """Return the EP target file 0..7 if active, else ``None``."""
    if not ep_target_active(packed):
        return None
    return (packed.categorical >> EP_FILE_LSB) & 0x7


def side_to_move_white(packed: SheetStateBIP) -> bool:
    """True if it is white to move, False otherwise."""
    return (packed.categorical & MASK_SIDE_TO_MOVE) == 0


def repetition_count(packed: SheetStateBIP) -> int:
    """Return the repetition count of the current position (0, 1, or 2)."""
    return (packed.categorical & MASK_REPETITION) >> REPETITION_LSB


def fifty_move_rule_triggered(packed: SheetStateBIP) -> bool:
    """True iff the half-move clock has reached the 50-move threshold."""
    return packed.halfmove_clock >= HALFMOVE_MAX


def threefold_claimable(packed: SheetStateBIP) -> bool:
    """True iff the current position has been seen ≥ 2 times before
    (a third occurrence triggers the FIDE 9.2 threefold claim)."""
    return repetition_count(packed) >= REPETITION_SATURATION


# ─── Distance metrics ───────────────────────────────────────────────


def hamming_distance_categorical(a: SheetStateBIP, b: SheetStateBIP) -> int:
    """Hamming distance over the 11 categorical bits.

    Equivalent to ``popcount(a.categorical ^ b.categorical)`` restricted
    to bits[0:11] (reserved bits are masked out before counting).

    Useful as a similarity metric over saved corpora — two positions
    with identical castling/EP/side but differing only in repetition
    count differ by 2 bits; an entirely different rights state
    differs by up to 9 bits (4 castling + 1 ep_active + 3 ep_file + 1
    side; the 2 repetition bits add up to 2 more).
    """
    diff = (a.categorical ^ b.categorical) & MASK_CATEGORICAL_USED
    # Python 3.10+: int.bit_count is fast and intrinsic.
    return diff.bit_count()


def halfmove_distance(a: SheetStateBIP, b: SheetStateBIP) -> int:
    """Absolute integer difference of half-move clocks.

    Returned as a non-negative integer in [0, 100]. This is the
    natural metric on Z₁₀₁ for chess (clocks 50 and 51 are 1 apart;
    clocks 50 and 0 are 50 apart). For applications that need cyclic
    distance, the caller should compute
    ``min(d, HALFMOVE_PERIOD - d)`` themselves, but cyclic distance
    is rarely the right metric for chess (the 50-move threshold is
    one-sided).
    """
    return abs(int(a.halfmove_clock) - int(b.halfmove_clock))


# ─── Module exports ─────────────────────────────────────────────────


__all__ = [
    # Layout constants
    "BIT_CASTLING_WK",
    "BIT_CASTLING_WQ",
    "BIT_CASTLING_BK",
    "BIT_CASTLING_BQ",
    "BIT_EP_ACTIVE",
    "EP_FILE_LSB",
    "EP_FILE_MSB",
    "BIT_SIDE_TO_MOVE",
    "REPETITION_LSB",
    "REPETITION_MSB",
    "RESERVED_LSB",
    "CATEGORICAL_BITS_USED",
    "MASK_CASTLING",
    "MASK_KINGSIDE_CASTLING",
    "MASK_QUEENSIDE_CASTLING",
    "MASK_EP_ACTIVE",
    "MASK_EP_FILE",
    "MASK_SIDE_TO_MOVE",
    "MASK_REPETITION",
    "MASK_RESERVED",
    "MASK_CATEGORICAL_USED",
    "HALFMOVE_MIN",
    "HALFMOVE_MAX",
    "REPETITION_SATURATION",
    # Dataclass
    "SheetStateBIP",
    # Encode / decode
    "encode_sheet_state_bip",
    "decode_sheet_state_bip",
    # Operator fast paths
    "castling_alive",
    "kingside_castling_alive",
    "queenside_castling_alive",
    "white_castling_alive",
    "black_castling_alive",
    "ep_target_active",
    "ep_file",
    "side_to_move_white",
    "repetition_count",
    "fifty_move_rule_triggered",
    "threefold_claimable",
    # Distance metrics
    "hamming_distance_categorical",
    "halfmove_distance",
]
