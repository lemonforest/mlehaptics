"""chess_spectral_4d — 4D extension of the spectral chess encoder.

Separate package from chess_spectral so the 2D reference (640-dim, 8x8)
stays untouched. The 4D encoder targets 10 channels x 4096 eigenmodes
= 40 960-dim float32 vectors on the Z_8^4 hypercubic lattice, per the
B_4 hyperoctahedral symmetry group and the ruleset of Oana & Chiru
(AppliedMath 6(3):48, 2026).

Scope of v1 is Python-only; a C port follows in v1.1. See plan file
`when-we-need-to-spicy-seahorse.md` and docs/chess-maths/
chess_spectral_4d_notebook.md for design notes.

Discover the CLI with:

    python -m chess_spectral_4d.cli --help
"""

VERSION = "0.1.0-dev"
ENCODING_DIM_4D = 40960   # 10 channels x 4096 eigenmodes
BOARD_SIDE_4D = 8
N_DIMENSIONS_4D = 4
N_SQUARES_4D = BOARD_SIDE_4D ** N_DIMENSIONS_4D  # 4096

__all__ = [
    "VERSION",
    "ENCODING_DIM_4D",
    "BOARD_SIDE_4D",
    "N_DIMENSIONS_4D",
    "N_SQUARES_4D",
]
