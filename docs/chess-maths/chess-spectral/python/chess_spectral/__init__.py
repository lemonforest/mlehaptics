"""chess_spectral — Python reference for the spectral chess encoder.
Sibling of the C17 port in ../src/. Use this for REPL / LLM analysis;
use the C binary for batch throughput.

Quick start (2D, 640-dim spectral payload):

    >>> from chess_spectral import encode_2d, channel_energies, fen_to_pos
    >>> pos = fen_to_pos("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    >>> enc = encode_2d(pos)
    >>> enc.shape
    (640,)
    >>> channel_energies(enc)
    {'A1': 0.0, 'A2': 19.845, ...}

Reading a game file produced by either the C or Python encoder:

    >>> from chess_spectral import read_all, read_encodings
    >>> hdr, arr = read_encodings("game.spectralz")   # transparent gzip
    >>> arr.shape
    (161, 640)

What's in the package (1.12.0):

  * 2D encoder (10 channels × 64 dims = 640) and 4D encoder
    (11 channels × 4096 dims = 45,056). Use ``encode_2d`` (1.9.0+
    future-proof alias of ``encode_640``) and ``encode_4d``. Query
    ``ENCODING_DIM`` / ``enc.shape[0]`` rather than hardcoding the
    dim count — see notebook §19.11.
  * **Sheet aux block** (1.9.0+): non-Markovian state (castling,
    EP, halfmove clock, repetition, side-to-move). Float64 path:
    ``encode_2d(pos, sheets=...)`` extends the vector by 11 dims.
    BIP-encoded path (1.10.0+): ``SheetStateBIP`` packs the same
    content into 3 bytes (uint16 + uint8). 29× compression with
    bit-exact round trip.
  * **ALU-native phase-operator engine** (1.11.0+):
    ``phase_only_pseudo_legal_moves(pos, side_to_move_white,
    ep_file=...)`` for Pyodide / WASM consumers. Pure integer
    arithmetic over Z_640; no python-chess dependency.
  * **Encoder BIP-hybrid** (1.12.0+): ``encode_2d_bip_hybrid`` /
    ``encode_4d_bip_hybrid`` factor each dim as sign × magnitude.
    3.4× compression at 8-bit, 5.8× at 4-bit. Cosine-sim ≥99.99%
    on acceptance corpus; suitable for Pyodide / batched corpora.

The notebook ``docs/chess-maths/chess_spectral_research_notebook.md``
has the full theory; §19, §20 cover the BIP / sheet / ALU work.
"""

# Derive the package version from the installed dist's metadata
# rather than hardcoding it. Hardcoding drifts: between v1.2.3 and
# v1.3.1, six version bumps to pyproject.toml landed without
# updating this string, so `chess_spectral.__version__` claimed
# "1.2.3" while `importlib.metadata.version("chess-spectral")`
# correctly reported the actual installed version. Dynamic
# derivation makes the two impossible to disagree.
#
# Editable / development checkouts that haven't been `pip install
# -e .`'d still get a sentinel string rather than crashing.
from importlib.metadata import (
    PackageNotFoundError as _PkgNotFound,
    version as _pkg_version,
)
try:
    __version__ = _pkg_version("chess-spectral")
except _PkgNotFound:
    __version__ = "0.0.0+unknown"
del _pkg_version, _PkgNotFound

from .encoder import (
    encode_640,
    encode_2d,  # 1.9.0 — future-proof alias of encode_640 (see §19.11)
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
from .fen import fen_to_pos, uci_to_indices
from .corpus import (
    process_game, extract_features,
    parse_local_pgn, iter_local_pgn_games,
    write_index_csv, write_summary_md,
    row_for_csv, INDEX_COLUMNS,
)
from .phase_operators import (
    phi,
    P_knight, P_king, P_rook, P_bishop, P_queen,
    P_pawn_white, P_pawn_black,
    invert,
    occupation_aware_moves_a,
    occupation_aware_moves_b,
    occupation_aware_moves_c,
    available_castles,
    phasecast_is_check,
    move_leaves_king_in_check,
    # 1.11.0 — ALU-native phase-operator engine (B-spike-1b)
    occupation_field_from_pos_dict,
    ep_phase_from_ep_file,
    phase_only_pseudo_legal_moves,
    PROMOTION_TARGETS,
)

# 1.9.0 — non-Markovian sheet aux block (representation completeness;
# no speed claim — see notebook §19.10 for the empirical depth-1
# bitboard floor that closes the speed thesis). The aux block carries
# castling rights, EP target, side-to-move, halfmove clock, and
# repetition count for downstream consumers of saved/transmitted
# vectors.
from .sheets import (
    SheetState,
    SHEET_AUX_DIM,
    SHEET_OFFSET_2D,
    SHEET_OFFSET_4D,
    HALFMOVE_PERIOD,
    REPETITION_CLAIM_THRESHOLD,
    FIFTY_MOVE_THRESHOLD,
    encode_aux_block,
    decode_castling_rights,
    decode_ep_file,
    decode_side_to_move_white,
    decode_repetition_count,
    decode_halfmove_clock,
    decode_sheet_state,
)

# 1.12.0 — Encoder BIP-hybrid (notebook §20.18). Sign × magnitude
# factoring per channel: sign packs as 1 bit per dim (algebraically
# exact); magnitude quantizes to 4 or 8 bits per dim with per-channel
# scaling. ~3.4× compression at 8-bit, ~5.8× at 4-bit (2D);
# correspondingly for 4D. Cosine-sim ≥99.99% at 8-bit on the
# acceptance corpus; 4D 4-bit research finding documented in §20.18.
from .encoder_bip_hybrid import (
    SpectralBIPHybrid2D,
    SpectralBIPHybrid4D,
    encode_2d_bip_hybrid,
    decode_2d_bip_hybrid,
    encode_4d_bip_hybrid,
    decode_4d_bip_hybrid,
    cosine_similarity_hybrid_2d,
    cosine_similarity_hybrid_4d,
    round_trip_cosine_sim_2d,
    round_trip_cosine_sim_4d,
    storage_bytes_2d as bip_hybrid_storage_bytes_2d,
    storage_bytes_4d as bip_hybrid_storage_bytes_4d,
    DEFAULT_MAGNITUDE_BITS,
    VALID_MAGNITUDE_BITS,
)

# 1.10.0 — Bit-Interleaved Phases (BIP) encoding for the sheet block
# (notebook §20.14, §20.16). Round-trip exact integer-native form:
# uint16 categorical + uint8 halfmove = 3 bytes per position vs the
# 1.9.0 float64 path's 88 bytes (29× compression). Operator fast
# paths via single integer ops; Hamming-distance metrics for corpus
# similarity. Pyodide / batch / wire-format wins; depth-1 floor
# (§19.10) still applies for single-position queries.
from .sheets_bip import (
    SheetStateBIP,
    encode_sheet_state_bip,
    decode_sheet_state_bip,
    # Operator fast paths
    castling_alive,
    kingside_castling_alive,
    queenside_castling_alive,
    white_castling_alive,
    black_castling_alive,
    ep_target_active,
    ep_file as ep_file_from_bip,
    side_to_move_white as side_to_move_white_from_bip,
    repetition_count as repetition_count_from_bip,
    fifty_move_rule_triggered,
    threefold_claimable,
    # Distance metrics
    hamming_distance_categorical,
    halfmove_distance,
)

# 1.7.0 D2: native fast-path availability flag, re-exported from
# chess_spectral.spatial_4d.bitboard so downstream consumers (the
# chess4D-OC visualizer and similar) can do
#   ``from chess_spectral import HAS_NATIVE_BITBOARD``
# to badge "native fast-path active" / fall back to a slower-but-
# correct UI path when native isn't available (sdist install with
# no C toolchain, Pyodide / micropip, ABI mismatch).
from .spatial_4d.bitboard import HAS_NATIVE_BITBOARD

__all__ = [
    # Encoder
    "encode_640", "encode_2d",
    "channel_energies", "normalize_pos", "CHANNELS",
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
    # FEN helpers
    "fen_to_pos", "uci_to_indices",
    # Corpus primitives
    "process_game", "extract_features",
    "parse_local_pgn", "iter_local_pgn_games",
    "write_index_csv", "write_summary_md",
    "row_for_csv", "INDEX_COLUMNS",
    # Phase operators (curated re-exports; full API at
    # chess_spectral.phase_operators.*)
    "phi",
    "P_knight", "P_king", "P_rook", "P_bishop", "P_queen",
    "P_pawn_white", "P_pawn_black",
    "invert",
    "occupation_aware_moves_a",
    "occupation_aware_moves_b",
    "occupation_aware_moves_c",
    "available_castles",
    "phasecast_is_check",
    "move_leaves_king_in_check",
    # 1.11.0 — ALU-native phase-operator engine (B-spike-1b)
    "occupation_field_from_pos_dict",
    "ep_phase_from_ep_file",
    "phase_only_pseudo_legal_moves",
    "PROMOTION_TARGETS",
    # 1.12.0 — Encoder BIP-hybrid
    "SpectralBIPHybrid2D",
    "SpectralBIPHybrid4D",
    "encode_2d_bip_hybrid",
    "decode_2d_bip_hybrid",
    "encode_4d_bip_hybrid",
    "decode_4d_bip_hybrid",
    "cosine_similarity_hybrid_2d",
    "cosine_similarity_hybrid_4d",
    "round_trip_cosine_sim_2d",
    "round_trip_cosine_sim_4d",
    "bip_hybrid_storage_bytes_2d",
    "bip_hybrid_storage_bytes_4d",
    "DEFAULT_MAGNITUDE_BITS",
    "VALID_MAGNITUDE_BITS",
    # 1.7.0 D2: native fast-path availability (downstream consumer flag).
    "HAS_NATIVE_BITBOARD",
    # 1.9.0 — non-Markovian sheet aux block (representation completeness)
    "SheetState",
    "SHEET_AUX_DIM",
    "SHEET_OFFSET_2D",
    "SHEET_OFFSET_4D",
    "HALFMOVE_PERIOD",
    "REPETITION_CLAIM_THRESHOLD",
    "FIFTY_MOVE_THRESHOLD",
    "encode_aux_block",
    "decode_castling_rights",
    "decode_ep_file",
    "decode_side_to_move_white",
    "decode_repetition_count",
    "decode_halfmove_clock",
    "decode_sheet_state",
    # 1.10.0 — BIP-encoded sheet block (uint16 + uint8, 3 bytes total)
    "SheetStateBIP",
    "encode_sheet_state_bip",
    "decode_sheet_state_bip",
    "castling_alive",
    "kingside_castling_alive",
    "queenside_castling_alive",
    "white_castling_alive",
    "black_castling_alive",
    "ep_target_active",
    "ep_file_from_bip",
    "side_to_move_white_from_bip",
    "repetition_count_from_bip",
    "fifty_move_rule_triggered",
    "threefold_claimable",
    "hamming_distance_categorical",
    "halfmove_distance",
]
