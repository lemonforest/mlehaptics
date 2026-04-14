"""chess_spectral — Python reference for the 640-dim spectral chess
encoder. Sibling of the C17 port in ../src/. Use this for REPL / LLM
analysis; use the C binary for batch throughput.

Quick start:

    >>> from chess_spectral import encode_640, channel_energies
    >>> from pgn_bridge import fen_to_pos
    >>> pos = fen_to_pos("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    >>> enc = encode_640(pos)
    >>> enc.shape
    (640,)
    >>> channel_energies(enc)
    {'A1': 0.0, 'A2': 19.845, ...}

Reading a game file produced by either the C or Python encoder:

    >>> from chess_spectral import read_all, read_encodings
    >>> hdr, arr = read_encodings("game.spectralz")   # transparent gzip
    >>> arr.shape
    (161, 640)
"""

from .encoder import (
    encode_640,
    channel_energies,
    normalize_pos,
    CHANNELS,
    BOARD_DIM,
    ENCODING_DIM,
    SPECTRAL_VALS,
    VALS,
    PAWN_ANTI_FIBER,
    DIAG_DEV,
)
from .frame import (
    Frame,
    Header,
    read_header,
    read_frame,
    iter_frames,
    seek_frame,
    read_all,
    read_encodings,
    open_read_transparent,
    write_file,
    FILE_MAGIC,
    FILE_VERSION,
    HEADER_BYTES,
    FRAME_BYTES,
)
from .csv_export import write_csv, iter_rows, fmt_num, fmt_cos
from .safety_field import compute_safety_field, side_most_exposed

__all__ = [
    # Encoder
    "encode_640", "channel_energies", "normalize_pos", "CHANNELS",
    "BOARD_DIM", "ENCODING_DIM", "SPECTRAL_VALS", "VALS",
    "PAWN_ANTI_FIBER", "DIAG_DEV",
    # Frame I/O
    "Frame", "Header", "read_header", "read_frame", "iter_frames",
    "seek_frame", "read_all", "read_encodings", "open_read_transparent",
    "write_file", "FILE_MAGIC", "FILE_VERSION", "HEADER_BYTES",
    "FRAME_BYTES",
    # CSV
    "write_csv", "iter_rows", "fmt_num", "fmt_cos",
    # Safety field
    "compute_safety_field", "side_most_exposed",
]
