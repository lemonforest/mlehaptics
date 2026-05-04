"""ALU-native phase-operator move generator (1.11.0 — B-spike-1b).

The §11 phase-operator engine has always been integer-arithmetic at
the core (every operator works on ``Z_640`` modular integer phases),
but until 1.11.0 the public entry points
(:func:`occupation_aware_moves_a/b/c`) all required a
``python-chess.Board`` argument because that's where the
occupation field, EP square, and castling-rights state lived. That
constraint is unnecessary for everything except castling — Solutions
B and C of §11.4 are pure phase-arithmetic operations on
``dict[phase, charge]`` occupation fields.

This module provides the **ALU-native integration entry point**:
:func:`phase_only_pseudo_legal_moves`. It takes the encoder's
standard position dict and emits pseudo-legal moves in encoder-sq
form, with no python-chess dependency. Suitable for Pyodide / WASM
consumers and for downstream pipelines that don't want to drag a
Board object alongside the position vector.

Status — what's covered in 1.11.0
---------------------------------

  * **Per-piece destination geometry** for all six piece types
    (rook, bishop, queen, king, knight, pawn). Reuses Solution B's
    ray-walk for sliding pieces; reuses
    :func:`king_destinations` / :func:`knight_destinations` /
    :func:`pawn_destinations` for non-sliders.
  * **Occupation-aware blocking and capture**. Identical semantics
    to :func:`occupation_aware_moves_b`; uses the same underlying
    phase-arithmetic, just without the Board ↔ phase conversion
    step.
  * **En passant** when ``ep_file`` is supplied. The ep target's
    phase is derived from the file + side-to-move via
    :func:`ep_phase_from_ep_file`.
  * **Pawn promotion**. Pawn moves landing on the promotion rank
    expand into four moves (one per target piece type:
    ``Q / R / B / N``).

Status — what's deferred to a future minor (B-spike-1b follow-up)
-----------------------------------------------------------------

  * **Castling**. §20.13's review noted that castling needs an
    attack map (for the "king does not pass through attacked
    square" check), which is more state than this module currently
    builds. Pure-phase castling generation is doable — both the
    rook + king phase shifts and the attack-map check are
    representable in ``Z_640`` integer arithmetic — but it's a
    larger lift. A 1.12.0+ follow-up.
  * **Check filter**. :func:`phasecast_is_check` already does
    pure-phase check detection but takes a ``python-chess.Board``
    input (could be refactored to take an occupation-by-piece-type
    dict). Until that refactor lands,
    :func:`phase_only_pseudo_legal_moves` returns moves that are
    pseudo-legal in the python-chess sense (caller is responsible
    for filtering moves that leave own king in check).

Acceptance — what 1.11.0 verifies
---------------------------------

  * Move-set parity with :func:`occupation_aware_moves_b` on a test
    corpus of positions: for every position, every (origin_sq,
    piece_char) pair, the destination set returned via the
    ALU-native path equals the destination set returned via the
    Board-fronted Solution B path. Modulo castling
    (deferred above), modulo check filtering (also deferred).
  * Cross-validates against ``board.pseudo_legal_moves`` after
    excluding castles. This is the load-bearing 1.11.0 acceptance
    gate.
  * Documented Pyodide-relevant speedup vs python-chess on the
    benchmark in :mod:`tests.bench_phase_operator_movegen`.

The Z_640 contract
------------------

For the explicit module-level wire contract (modulus, generators,
shift constants), see :mod:`chess_spectral.phase_operators.phase_operators`.
The ``Z_640`` group is **not** a power-of-2 cyclic group, so the
modular arithmetic doesn't enjoy the "free" overflow semantics
that BIP encoding gets in ``Z_{2^32}`` (notebook §20.11). Each
``(a + b) % MODULUS`` is an explicit modulo op. Cheap, but not
zero — bounds the per-operation speedup vs ``Z_{2^32}`` BIP.

Notebook §20.13 covers the structural relationship between this
``Z_640`` engine and the BIP-encoded sheet block (§20.14, shipped
as 1.10.0): they are **two distinct ALU-native opportunities** at
different layers of the encoder stack, sharing only the high-level
"integer arithmetic over a finite cyclic group" pattern.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

# Re-use Solution B's sliding-ray internals + the rays themselves.
# These are submodule-private (underscore prefix) but package-internal
# is a fine boundary for our own re-use; keeping the duplication out
# of this module preserves the single source of truth for ray-walking
# semantics.
from .occupation_aware_b import (
    _ROOK_RAYS, _BISHOP_RAYS, _QUEEN_RAYS,
    _sliding_destinations_b,
)
from .occupation_field import (
    WHITE_CHARGE, BLACK_CHARGE,
    occupation_field_from_pos_dict,
    ep_phase_from_ep_file,
    _encoder_sq_to_chess_rc,
    _chess_rc_to_encoder_sq,
    king_destinations,
    knight_destinations,
    pawn_destinations,
)
from .phase_operators import phi


# Promotion rank by side. White pawns reaching rank 7 promote;
# black pawns reaching rank 0 promote. Stored explicitly so the
# promotion check in the move generator is trivially fast.
_WHITE_PROMOTION_RANK: int = 7
_BLACK_PROMOTION_RANK: int = 0

# Promotion target piece chars (uppercase regardless of moving
# color; the moving pawn's color is always known at the call site).
PROMOTION_TARGETS: Tuple[str, ...] = ('Q', 'R', 'B', 'N')


def phase_only_pseudo_legal_moves(
    pos: "Dict[int, str] | Dict[str, str]",
    side_to_move_white: bool,
    *,
    ep_file: Optional[int] = None,
) -> List[Tuple[int, int, Optional[str]]]:
    """ALU-native pseudo-legal move generator on Z_640.

    Iterates the side to move's pieces, computes each piece's
    destination set via Solution B's phase-arithmetic, and returns a
    flat list of ``(from_sq, to_sq, promotion_char)`` tuples in
    encoder sq convention.

    Parameters
    ----------
    pos
        Encoder-format position dict (``{sq: piece_char}``, sq is
        row-major from a8=0; piece_char uppercase = white). Accepts
        both int-keyed and str-keyed dicts (NDJSON convention via
        :func:`chess_spectral.normalize_pos`).
    side_to_move_white
        ``True`` if it is white to move, ``False`` for black.
    ep_file
        File index 0..7 of the EP target square, or ``None`` if no
        EP target on the current ply. Matches the
        :class:`chess_spectral.SheetState` ``ep_file`` semantics.

    Returns
    -------
    list of (from_sq, to_sq, promotion_char) tuples
        Each tuple represents one pseudo-legal move. ``from_sq``
        and ``to_sq`` are encoder sq integers in [0, 64).
        ``promotion_char`` is ``None`` for non-promotion moves;
        for pawn moves landing on the promotion rank, four tuples
        are emitted, one per promotion target (``Q``, ``R``, ``B``,
        ``N``).

    Pseudo-legal in the python-chess sense
    --------------------------------------

    The returned moves respect:

      * piece geometry (rook stops at first blocker; bishop on
        diagonal; etc.)
      * occupation (cannot land on own piece; capture iff
        opposite-charge destination)
      * pawn double-push (only from rank 1 / rank 6)
      * en passant (when ``ep_file`` is supplied)
      * pawn promotion (one move per target piece type)

    They do NOT include:

      * castling (deferred; see module docstring)
      * filter for moves that leave own king in check (caller's
        responsibility — use a downstream check-detection pass)
    """
    occupation = occupation_field_from_pos_dict(pos)
    mover_charge = WHITE_CHARGE if side_to_move_white else BLACK_CHARGE
    ep_phase = ep_phase_from_ep_file(ep_file, side_to_move_white)
    promotion_rank = (_WHITE_PROMOTION_RANK if side_to_move_white
                      else _BLACK_PROMOTION_RANK)

    moves: List[Tuple[int, int, Optional[str]]] = []
    for sq, piece_char in pos.items():
        sq_int = int(sq) if isinstance(sq, str) else sq

        # Filter to side-to-move's pieces. White uppercase, black
        # lowercase per the encoder convention.
        is_white_piece = piece_char.isupper()
        if is_white_piece != side_to_move_white:
            continue

        rank, file = _encoder_sq_to_chess_rc(sq_int)
        origin_phi = phi(rank, file)
        pc = piece_char.upper()

        # Per-piece destination geometry. Mirrors
        # occupation_aware_moves_b's dispatch.
        if pc == "R":
            dests = _sliding_destinations_b(
                origin_phi, _ROOK_RAYS, occupation, mover_charge)
        elif pc == "B":
            dests = _sliding_destinations_b(
                origin_phi, _BISHOP_RAYS, occupation, mover_charge)
        elif pc == "Q":
            dests = _sliding_destinations_b(
                origin_phi, _QUEEN_RAYS, occupation, mover_charge)
        elif pc == "K":
            # Note: castling intentionally excluded here; this
            # module's contract is pseudo-legal-without-castling.
            dests = king_destinations(origin_phi, occupation, mover_charge)
        elif pc == "N":
            dests = knight_destinations(origin_phi, occupation, mover_charge)
        elif pc == "P":
            dests = pawn_destinations(
                rank, file, occupation, mover_charge, ep_phase=ep_phase)
        else:
            # Unknown piece char (defensive — shouldn't happen with
            # encoder-format input). Skip rather than raise so a
            # consumer with malformed pos still gets the legal moves
            # of well-formed pieces.
            continue

        # Convert (rank, file) destinations back to encoder sq, with
        # promotion expansion for pawns.
        for (dest_rank, dest_file) in dests:
            to_sq = _chess_rc_to_encoder_sq(dest_rank, dest_file)
            if pc == "P" and dest_rank == promotion_rank:
                # Promotion: expand into four moves.
                for promo in PROMOTION_TARGETS:
                    moves.append((sq_int, to_sq, promo))
            else:
                moves.append((sq_int, to_sq, None))

    return moves


# ─── Module exports ─────────────────────────────────────────────────


__all__ = [
    "phase_only_pseudo_legal_moves",
    "PROMOTION_TARGETS",
]
