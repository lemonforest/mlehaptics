"""chess_spectral_4d — 4D extension of the spectral chess encoder.

Separate package from chess_spectral so the 2D reference (640-dim, 8x8)
stays untouched. The 4D encoder targets 11 channels x 4096 eigenmodes
= 45 056-dim float32 vectors on the Z_8^4 hypercubic lattice, per the
B_4 hyperoctahedral symmetry group and the ruleset of Oana & Chiru
(AppliedMath 6(3):48, 2026).

v1.1.1 splits the pawn antisymmetric channel into W-axis (FA_PAWN_W)
and Y-axis (FA_PAWN_Y) sub-channels per Oana & Chiru Definition 11;
encoding_dim grew from 40 960 (v1.0) to 45 056, and the spectralz
frame format bumped from v3 to v4. See [ROADMAP.md](../../ROADMAP.md)
for the current command surface and
docs/chess-maths/chess_spectral_4d_notebook.md for design notes.

Discover the CLI with:

    python -m chess_spectral_4d.cli --help
"""

VERSION = "1.1.3"
__version__ = VERSION  # PEP 396 alias; VERSION kept for cli.py back-compat
ENCODING_DIM_4D = 45056   # 11 channels x 4096 eigenmodes (v1.1.1)
N_CHANNELS_4D = 11
BOARD_SIDE_4D = 8
N_DIMENSIONS_4D = 4
N_SQUARES_4D = BOARD_SIDE_4D ** N_DIMENSIONS_4D  # 4096

# Pawn axis channel names. FA_PAWN_W mirrors v1.0 FA_PAWN (W-only);
# FA_PAWN_Y is the new Y-axis sub-channel; FD_DIAG shifted from slot 9
# to slot 10. See chess_spectral.encoder_4d.CHANNELS_4D for the full
# layout including the non-pawn channels.
FA_PAWN_W_OFFSET = 8 * N_SQUARES_4D    # 32768
FA_PAWN_Y_OFFSET = 9 * N_SQUARES_4D    # 36864
FD_DIAG_OFFSET = 10 * N_SQUARES_4D     # 40960

# Facade re-exports. The 4D encoder and spectralz I/O currently live in
# chess_spectral.{encoder_4d,frame_4d} for historical reasons; surfacing
# them here lets downstream code write `from chess_spectral_4d import
# encode_4d, frame_4d, write_spectralz_v4` without caring about the
# physical module layout.
from chess_spectral.encoder_4d import (
    encode_4d,
    channel_energies_4d,
    board_signal_4d,
)
from chess_spectral import frame_4d
from chess_spectral.frame_4d import (
    Frame4D,
    Header4D,
    write_spectralz_v4,
    read_spectralz_v4,
    SPECTRALZ_MAGIC,
    SPECTRALZ_VERSION,
)

__all__ = [
    # Version + constants
    "VERSION",
    "ENCODING_DIM_4D",
    "N_CHANNELS_4D",
    "BOARD_SIDE_4D",
    "N_DIMENSIONS_4D",
    "N_SQUARES_4D",
    "FA_PAWN_W_OFFSET",
    "FA_PAWN_Y_OFFSET",
    "FD_DIAG_OFFSET",
    # Encoder
    "encode_4d",
    "channel_energies_4d",
    "board_signal_4d",
    # Frame I/O
    "frame_4d",
    "Frame4D",
    "Header4D",
    "write_spectralz_v4",
    "read_spectralz_v4",
    "SPECTRALZ_MAGIC",
    "SPECTRALZ_VERSION",
]
