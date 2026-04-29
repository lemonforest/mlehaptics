"""chess_spectral.spatial_4d -- in-house bitboard-based 4D move generator.

Phase 6 (v1.6) infrastructure for 4D chess. Mirrors python-chess's
bitboard architecture for the 8^4 lattice, which is the canonical
fast-path approach for chess move generation.

Why this exists
---------------
The §16 search needs a fast 4D move generator. The two non-options
(promote python-chess4d-oana-chiru to a runtime dep -- circular dep;
use spectral_legality_4d -- only handles empty-board reach predicate)
forced us to build in-house. ADR-001 in
``docs/adr/spatial_4d/ADR-001-bitboard-architecture.md`` is the
design record.

Architecture
------------
* :class:`Bitboard4D` -- the 4096-bit set primitive (PR-7-B). Python
  int as canonical storage; np.uint64[64] projection for hot loops.
* attack tables (PR-7-C, PR-7-D, PR-7-E) -- precomputed per-piece
  per-square attack bitboards, magic-bitboard-style for sliding pieces.
* :class:`Board4D` (PR-7-F) -- game state with legal_moves, push/pop,
  check detection, FEN4 round-trip.
* draw-rule predicates (PR-7-G).
* corpus parity gate against python-chess4d-oana-chiru (PR-7-H).

Cross-validation
----------------
Three independent move-legality oracles cross-checked on a corpus:
1. python-chess4d-oana-chiru (upstream rule library, [test] extra)
2. chess_spectral.spatial_4d (this module, runtime fast path)
3. chess_spectral.spectral_legality_4d (graph-Laplacian eigenbasis,
   empty-board reach predicate only)

Three oracles converging on every move per ply is a strong
correctness signal.
"""
from __future__ import annotations

from .bitboard import Bitboard4D
from .attacks_nonsliding import (
    KNIGHT_ATTACKS_4D,
    KING_ATTACKS_4D,
    attacks_knight_4d,
    attacks_king_4d,
)
from .attacks_sliding import (
    attacks_rook_4d,
    attacks_bishop_4d,
    attacks_queen_4d,
)
from .rays import (
    ROOK_DIRECTIONS, BISHOP_DIRECTIONS, QUEEN_DIRECTIONS,
    ROOK_RAYS, BISHOP_RAYS, QUEEN_RAYS,
)
from .attacks_pawn import (
    pawn_pushes_4d,
    attacks_pawn_4d,
    PAWN_PUSH_W_WHITE, PAWN_PUSH_W_BLACK,
    PAWN_PUSH_Y_WHITE, PAWN_PUSH_Y_BLACK,
    PAWN_ATTACKS_W_WHITE, PAWN_ATTACKS_W_BLACK,
    PAWN_ATTACKS_Y_WHITE, PAWN_ATTACKS_Y_BLACK,
)

__all__ = [
    "Bitboard4D",
    # non-sliding
    "KNIGHT_ATTACKS_4D",
    "KING_ATTACKS_4D",
    "attacks_knight_4d",
    "attacks_king_4d",
    # sliding
    "attacks_rook_4d",
    "attacks_bishop_4d",
    "attacks_queen_4d",
    # rays / directions
    "ROOK_DIRECTIONS", "BISHOP_DIRECTIONS", "QUEEN_DIRECTIONS",
    "ROOK_RAYS", "BISHOP_RAYS", "QUEEN_RAYS",
    # pawn (axis-typed: w / y per Oana-Chiru Def 11)
    "pawn_pushes_4d", "attacks_pawn_4d",
    "PAWN_PUSH_W_WHITE", "PAWN_PUSH_W_BLACK",
    "PAWN_PUSH_Y_WHITE", "PAWN_PUSH_Y_BLACK",
    "PAWN_ATTACKS_W_WHITE", "PAWN_ATTACKS_W_BLACK",
    "PAWN_ATTACKS_Y_WHITE", "PAWN_ATTACKS_Y_BLACK",
]
