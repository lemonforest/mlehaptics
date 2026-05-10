#!/usr/bin/env python3
"""
Emit C const tables for the 640-dim spectral chess encoder.

Writes:
  include/cs_tables.h           - small declarations (D4_PERMS, CHARS, VALS, dims)
  include/cs_fiber_tables.h     - extern declarations for LOCAL_* and NEW tables
  src/cs_tables_data.c          - GENERATED large arrays (extern const definitions)

Tables emitted (all double unless noted):
  D4_PERMS[8][64]            uint8
  CHARS[5][8]                int8
  SPECTRAL_VALS[6]           piece values (P,N,B,R,Q,K), unsigned
  TRAD_VALS[6]               traditional values (P=1, N=3, B=3.5, R=5, Q=9, K=100)
  LOCAL_FIBER_3D[5][64][3]   per-piece (N,B,R,Q,K) per-square fiber coords
  LOCAL_ADJ_ROWS[5][64][64]  per-piece per-square local adjacency row
  PAWN_ANTI_FIBER[64][64]    in eigenbasis: EVECSᵀ · A_anti · EVECS
  DIAG_DEV[6][64]            per-piece diagonal-deviation from grid eigenvalues

Coprime check: 67, 7, 131 are all coprime to 640 = 2^7 * 5.
All 64 spatial offsets (r*67 + c*7) mod 640 must be distinct.
"""
import os
import sys
import io
import math
import numpy as np

# Windows console: the printout uses a checkmark glyph; default cp1252 cannot
# encode it. Reconfigure stdout to UTF-8 (errors='replace' so a mis-configured
# terminal still gets a sensible byte, just without the tick).
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                                  errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..'))
PKG_DIR = os.path.abspath(os.path.join(HERE, '..', 'python'))
INC_DIR = os.path.join(REPO, 'include')
SRC_DIR = os.path.join(REPO, 'src')

# Pull all tables and helpers from the production chess_spectral package —
# same SSOT the C reference was derived from (verified bit-identical).
sys.path.insert(0, PKG_DIR)
from chess_spectral.tables import (
    SPECTRAL_VALS as _SV_DICT,
    VALS as _VALS_DICT,
    D4_PERMS as _D4_PERMS,
    CHARS as _CHARS,
    LOCAL_FIBER_3D as _LOCAL_FIBER_3D,
    LOCAL_ADJ_ROWS as _LOCAL_ADJ_ROWS,
    PAWN_ANTI_FIBER,
    DIAG_DEV,
    white_pawn_targets,
    build_directed_adjacency,
)

# --- Derived objects ---------------------------------------------------------

# Piece order for fiber channels (5 pieces: N,B,R,Q,K) — matches
# chess_spectral.tables construction order.
FIBER_PIECES = ['N', 'B', 'R', 'Q', 'K']
# Piece order for diagonal channel (6 pieces: P,N,B,R,Q,K)
DIAG_PIECE_NAMES = ['Pawn', 'Knight', 'Bishop', 'Rook', 'Queen', 'King']

SPECTRAL_VALS = [float(_SV_DICT[c]) for c in ('P', 'N', 'B', 'R', 'Q', 'K')]
TRAD_VALS = [float(_VALS_DICT[c]) for c in ('P', 'N', 'B', 'R', 'Q', 'K')]

# Sanity printouts: reconstruct A_anti locally (cheap) so we can still report
# its norm alongside PAWN_ANTI_FIBER. The imported PAWN_ANTI_FIBER is the
# authoritative table used in the C emission.
_A_white = build_directed_adjacency(white_pawn_targets)
_A_anti = 0.5 * (_A_white - _A_white.T)

# Rook's diagonal deviation norm should be ~88.05 (chess_rook_shadow.py).
# chess_spectral.tables asserts this internally on build; we re-check here
# as a belt-and-suspenders guard against a stale on-disk cache.
rook_diag_norm = float(np.linalg.norm(DIAG_DEV[3]))
assert 87.0 < rook_diag_norm < 89.0, (
    f"Rook diag-dev norm = {rook_diag_norm:.3f}, expected ~88.05")

# --- Coprime check ------------------------------------------------------------
COPRIME_ROW = 67
COPRIME_COL = 7
COPRIME_TIME = 131
DIM = 640
assert math.gcd(COPRIME_ROW, DIM) == 1, "67 not coprime to 640"
assert math.gcd(COPRIME_COL, DIM) == 1, "7 not coprime to 640"
assert math.gcd(COPRIME_TIME, DIM) == 1, "131 not coprime to 640"
# All 64 (r,c) offsets distinct
offsets = set()
for r in range(8):
    for c in range(8):
        offsets.add((r * COPRIME_ROW + c * COPRIME_COL) % DIM)
assert len(offsets) == 64, f"Spatial offsets not distinct: {len(offsets)}/64"


# ============================================================================
# EMISSION HELPERS
# ============================================================================

def _fmt_d(x):
    """Emit a double in full precision."""
    return f"{float(x):.17e}"


def emit_u8_2d(fout, name, arr, dim0, dim1):
    fout.write(f"const uint8_t {name}[{dim0}][{dim1}] = {{\n")
    for i in range(dim0):
        fout.write("    {")
        fout.write(", ".join(str(int(arr[i][j])) for j in range(dim1)))
        fout.write(f"}}{',' if i + 1 < dim0 else ''}\n")
    fout.write("};\n\n")


def emit_i8_2d(fout, name, arr, dim0, dim1):
    fout.write(f"const int8_t {name}[{dim0}][{dim1}] = {{\n")
    for i in range(dim0):
        fout.write("    {")
        fout.write(", ".join(str(int(arr[i][j])) for j in range(dim1)))
        fout.write(f"}}{',' if i + 1 < dim0 else ''}\n")
    fout.write("};\n\n")


def emit_f64_1d(fout, name, arr, dim0):
    fout.write(f"const double {name}[{dim0}] = {{\n    ")
    fout.write(", ".join(_fmt_d(arr[i]) for i in range(dim0)))
    fout.write("\n};\n\n")


def emit_f64_2d(fout, name, arr, dim0, dim1):
    fout.write(f"const double {name}[{dim0}][{dim1}] = {{\n")
    for i in range(dim0):
        fout.write("    {")
        fout.write(", ".join(_fmt_d(arr[i][j]) for j in range(dim1)))
        fout.write(f"}}{',' if i + 1 < dim0 else ''}\n")
    fout.write("};\n\n")


def emit_f64_3d(fout, name, arr, dim0, dim1, dim2):
    fout.write(f"const double {name}[{dim0}][{dim1}][{dim2}] = {{\n")
    for i in range(dim0):
        fout.write("    {\n")
        for j in range(dim1):
            fout.write("        {")
            fout.write(", ".join(_fmt_d(arr[i][j][k]) for k in range(dim2)))
            fout.write(f"}}{',' if j + 1 < dim1 else ''}\n")
        fout.write(f"    }}{',' if i + 1 < dim0 else ''}\n")
    fout.write("};\n\n")


# ============================================================================
# WRITE cs_tables.h (small/public constants)
# ============================================================================

def write_cs_tables_h():
    path = os.path.join(INC_DIR, 'cs_tables.h')
    with open(path, 'w', encoding='utf-8') as f:
        f.write("/* GENERATED by codegen/emit_tables.py — DO NOT EDIT BY HAND */\n")
        f.write("#ifndef CS_TABLES_H\n#define CS_TABLES_H\n\n")
        f.write("#include <stdint.h>\n\n")
        f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
        f.write("/* Encoding dimensions */\n")
        f.write("#define CS_BOARD_DIM      64\n")
        f.write("#define CS_NUM_IRREPS     5\n")
        f.write("#define CS_NUM_SYM_FIBER  3\n")
        f.write("#define CS_NUM_CHANNELS   10\n")
        f.write("#define CS_ENCODING_DIM   640\n\n")
        f.write("/* Coprime generators for temporal/spatial binding (all coprime to 640) */\n")
        f.write("#define CS_COPRIME_ROW    67\n")
        f.write("#define CS_COPRIME_COL    7\n")
        f.write("#define CS_COPRIME_TIME   131\n\n")
        f.write("/* D4 permutations, character table */\n")
        f.write("extern const uint8_t D4_PERMS[8][64];\n")
        f.write("extern const int8_t  CHARS[5][8];\n\n")
        f.write("/* Piece-value tables (P=0, N=1, B=2, R=3, Q=4, K=5) */\n")
        f.write("extern const double SPECTRAL_VALS[6];\n")
        f.write("extern const double TRAD_VALS[6];\n\n")
        f.write("#ifdef __cplusplus\n}\n#endif\n\n")
        f.write("#endif /* CS_TABLES_H */\n")
    print(f"Wrote {path}")


# ============================================================================
# WRITE cs_fiber_tables.h (extern decls for large arrays)
# ============================================================================

def write_cs_fiber_tables_h():
    path = os.path.join(INC_DIR, 'cs_fiber_tables.h')
    with open(path, 'w', encoding='utf-8') as f:
        f.write("/* GENERATED by codegen/emit_tables.py — DO NOT EDIT BY HAND */\n")
        f.write("#ifndef CS_FIBER_TABLES_H\n#define CS_FIBER_TABLES_H\n\n")
        f.write("#include \"cs_tables.h\"\n\n")
        f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")
        f.write("/* Fiber tables — fiber-piece index: 0=N, 1=B, 2=R, 3=Q, 4=K. */\n")
        f.write("extern const double LOCAL_FIBER_3D[5][64][3];\n")
        f.write("extern const double LOCAL_ADJ_ROWS[5][64][64];\n\n")
        f.write("/* Antisymmetric pawn fiber in eigenbasis: EVECS^T * A_anti * EVECS. */\n")
        f.write("extern const double PAWN_ANTI_FIBER[64][64];\n\n")
        f.write("/* Per-piece diagonal deviation from grid eigenvalues.\n")
        f.write(" * Indexed [piece_type][k]; piece_type: P=0, N=1, B=2, R=3, Q=4, K=5. */\n")
        f.write("extern const double DIAG_DEV[6][64];\n\n")
        f.write("#ifdef __cplusplus\n}\n#endif\n\n")
        f.write("#endif /* CS_FIBER_TABLES_H */\n")
    print(f"Wrote {path}")


# ============================================================================
# WRITE src/cs_tables_data.c (definitions)
# ============================================================================

def write_cs_tables_data_c():
    path = os.path.join(SRC_DIR, 'cs_tables_data.c')

    # D4_PERMS is shape (8, 64) int8 in the package; emit helper coerces to int.
    d4 = np.asarray(_D4_PERMS)

    chars = np.zeros((5, 8), dtype=np.int32)
    for i, name in enumerate(('A1', 'A2', 'B1', 'B2', 'E')):
        chars[i] = _CHARS[name]

    # LOCAL_FIBER_3D is already shape (5, 64, 3) indexed as piece=(N,B,R,Q,K);
    # LOCAL_ADJ_ROWS already shape (5, 64, 64). No repacking needed.
    lf3d = _LOCAL_FIBER_3D
    lar = _LOCAL_ADJ_ROWS

    with open(path, 'w', encoding='utf-8') as f:
        f.write("/* GENERATED by codegen/emit_tables.py — DO NOT EDIT BY HAND */\n")
        f.write("#include \"cs_tables.h\"\n")
        f.write("#include \"cs_fiber_tables.h\"\n\n")

        emit_u8_2d(f, "D4_PERMS", d4, 8, 64)
        emit_i8_2d(f, "CHARS", chars, 5, 8)
        emit_f64_1d(f, "SPECTRAL_VALS", SPECTRAL_VALS, 6)
        emit_f64_1d(f, "TRAD_VALS", TRAD_VALS, 6)
        emit_f64_3d(f, "LOCAL_FIBER_3D", lf3d, 5, 64, 3)
        emit_f64_3d(f, "LOCAL_ADJ_ROWS", lar, 5, 64, 64)
        emit_f64_2d(f, "PAWN_ANTI_FIBER", PAWN_ANTI_FIBER, 64, 64)
        emit_f64_2d(f, "DIAG_DEV", DIAG_DEV, 6, 64)

    print(f"Wrote {path}")


# ============================================================================
# MAIN
# ============================================================================

def write_committed_tables_npz():
    """Write the same table values that go into ``cs_tables_data.c``
    out as a numpy ``.npz`` so the Python encoder can load identical
    values at runtime — eliminating the cross-platform skew that arose
    when Python computed its own tables via scipy/LAPACK on each
    machine. See `chess_spectral.tables._committed_tables_path`.

    Source values: imported at the top of this script from
    `chess_spectral.tables`, which is the same single-source-of-truth
    we pull C-side numbers from. Both outputs are therefore guaranteed
    bit-identical to each other when this script runs."""
    out_dir = os.path.join(PKG_DIR, 'chess_spectral')
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, '_committed_tables.npz')
    # Pull the same in-memory values codegen used. EVALS_GRID,
    # EVECS_GRID, FIBER_BASIS aren't emitted into the C table file
    # (they're internal to Python's encoder) but must be saved here
    # so Python doesn't fall through to the recompute path.
    from chess_spectral.tables import (
        EVALS_GRID, EVECS_GRID, FIBER_BASIS,
        LOCAL_FIBER_3D, LOCAL_ADJ_ROWS,
        PAWN_ANTI_FIBER, DIAG_DEV, VERSION as TABLES_VERSION,
    )
    np.savez_compressed(
        path,
        version=np.str_(TABLES_VERSION),
        EVALS_GRID=EVALS_GRID,
        EVECS_GRID=EVECS_GRID,
        FIBER_BASIS=FIBER_BASIS,
        LOCAL_FIBER_3D=LOCAL_FIBER_3D,
        LOCAL_ADJ_ROWS=LOCAL_ADJ_ROWS,
        PAWN_ANTI_FIBER=PAWN_ANTI_FIBER,
        DIAG_DEV=DIAG_DEV,
    )
    print(f"Wrote {path} ({os.path.getsize(path) / 1024:.1f} KB)")


# ============================================================================
# 1.19.0+ — pure-phase 2D integer tables (B-spike-4 / chess2d C port)
# ============================================================================
#
# Mirror of ``chess_spectral.encoder_pure_phase`` quantization. Emit
# the integer tables the C-side pure-phase 2D encoder consumes:
#
#   SIGNED_VALS_INT_2D[12]                   int16  (one per piece char)
#   LOCAL_FIBER_3D_INT16[5][64][3]           int16  (+ scale double)
#   LOCAL_ADJ_ROWS_INT8[5][64][64]           int8
#   PAWN_ANTI_FIBER_INT16[64][64]            int16  (+ scale double)
#   DIAG_DEV_INT16_2D[6][64]                 int16  (+ scale double)
#   CHANNEL_DEQUANT_SCALES_2D[10]            double
#
# All quantization parameters are SSOT'd against the Python module
# (chess_spectral.encoder_pure_phase) so a build-time mismatch is
# surfaced at codegen time, not in CI parity tests.

from chess_spectral.encoder_pure_phase import (   # noqa: E402
    _VALS_INT_SCALE,
    _FIBER_QUANT_BITS,
    _FIBER_QUANT_MAX,
    _SIGNED_VALS_INT,
    _SCALE_LOCAL_FIBER_3D,
    _SCALE_PAWN_ANTI,
    _SCALE_DIAG_DEV,
    LOCAL_FIBER_3D_INT16 as _PP_LOCAL_FIBER_INT16,
    LOCAL_ADJ_ROWS_INT8 as _PP_LOCAL_ADJ_INT8,
    PAWN_ANTI_FIBER_INT16 as _PP_PAWN_ANTI_INT16,
    DIAG_DEV_INT16 as _PP_DIAG_DEV_INT16,
    CHANNEL_DEQUANT_SCALES as _PP_CHANNEL_DEQUANT_SCALES,
)

# Piece-char ordering for the C-side SIGNED_VALS_INT_2D table. Order
# matches the indexing convention in the C encoder: the row is
# determined per-piece by looking up the char into a switch (see
# cs_pure_phase_signal_2d.c). We emit a 12-entry table indexed by a
# helper function in the C source.
_PIECE_CHARS_2D = ('P', 'N', 'B', 'R', 'Q', 'K',
                   'p', 'n', 'b', 'r', 'q', 'k')

PURE_PHASE_SIGNED_VALS_INT_2D = np.asarray(
    [_SIGNED_VALS_INT[c] for c in _PIECE_CHARS_2D], dtype=np.int16
)
assert PURE_PHASE_SIGNED_VALS_INT_2D.shape == (12,)

# Bit-exact copies of the Python int-quantized fiber tables. We
# re-pack as the appropriate numpy dtype to match the C extern
# declarations exactly.
PURE_PHASE_LOCAL_FIBER_INT16_2D = np.asarray(
    _PP_LOCAL_FIBER_INT16, dtype=np.int16
)
assert PURE_PHASE_LOCAL_FIBER_INT16_2D.shape == (5, 64, 3)

PURE_PHASE_LOCAL_ADJ_INT8_2D = np.asarray(
    _PP_LOCAL_ADJ_INT8, dtype=np.int8
)
assert PURE_PHASE_LOCAL_ADJ_INT8_2D.shape == (5, 64, 64)

PURE_PHASE_PAWN_ANTI_INT16_2D = np.asarray(
    _PP_PAWN_ANTI_INT16, dtype=np.int16
)
assert PURE_PHASE_PAWN_ANTI_INT16_2D.shape == (64, 64)

PURE_PHASE_DIAG_DEV_INT16_2D = np.asarray(
    _PP_DIAG_DEV_INT16, dtype=np.int16
)
assert PURE_PHASE_DIAG_DEV_INT16_2D.shape == (6, 64)

# Per-channel dequantization scales in CHANNELS order
# (A1, A2, B1, B2, E, F1, F2, F3, FA, FD).
_CHANNEL_NAMES_2D = (
    'A1', 'A2', 'B1', 'B2', 'E',
    'F1', 'F2', 'F3', 'FA', 'FD',
)
PURE_PHASE_DEQUANT_SCALES_2D = np.asarray(
    [_PP_CHANNEL_DEQUANT_SCALES[name] for name in _CHANNEL_NAMES_2D],
    dtype=np.float64,
)
assert PURE_PHASE_DEQUANT_SCALES_2D.shape == (10,)


def _emit_i8_2d_2d(fout, name, arr, dim0, dim1):
    fout.write(f"const int8_t {name}[{dim0}][{dim1}] = {{\n")
    for i in range(dim0):
        fout.write("    {")
        fout.write(", ".join(str(int(arr[i][j])) for j in range(dim1)))
        fout.write(f"}}{',' if i + 1 < dim0 else ''}\n")
    fout.write("};\n\n")


def _emit_i8_3d_2d(fout, name, arr, dim0, dim1, dim2):
    fout.write(f"const int8_t {name}[{dim0}][{dim1}][{dim2}] = {{\n")
    for i in range(dim0):
        fout.write("    {\n")
        for j in range(dim1):
            fout.write("        {")
            fout.write(", ".join(str(int(arr[i][j][k])) for k in range(dim2)))
            fout.write(f"}}{',' if j + 1 < dim1 else ''}\n")
        fout.write(f"    }}{',' if i + 1 < dim0 else ''}\n")
    fout.write("};\n\n")


def _emit_i16_1d_2d(fout, name, arr, dim0):
    fout.write(f"const int16_t {name}[{dim0}] = {{\n    ")
    cols = 16
    for i in range(dim0):
        fout.write(str(int(arr[i])))
        if i + 1 < dim0:
            fout.write(",")
        if (i + 1) % cols == 0 and i + 1 < dim0:
            fout.write("\n    ")
        elif i + 1 < dim0:
            fout.write(" ")
    fout.write("\n};\n\n")


def _emit_i16_2d_2d(fout, name, arr, dim0, dim1):
    fout.write(f"const int16_t {name}[{dim0}][{dim1}] = {{\n")
    for i in range(dim0):
        fout.write("    {")
        fout.write(", ".join(str(int(arr[i][j])) for j in range(dim1)))
        fout.write(f"}}{',' if i + 1 < dim0 else ''}\n")
    fout.write("};\n\n")


def _emit_i16_3d_2d(fout, name, arr, dim0, dim1, dim2):
    fout.write(f"const int16_t {name}[{dim0}][{dim1}][{dim2}] = {{\n")
    for i in range(dim0):
        fout.write("    {\n")
        for j in range(dim1):
            fout.write("        {")
            fout.write(", ".join(str(int(arr[i][j][k])) for k in range(dim2)))
            fout.write(f"}}{',' if j + 1 < dim1 else ''}\n")
        fout.write(f"    }}{',' if i + 1 < dim0 else ''}\n")
    fout.write("};\n\n")


def write_cs_pure_phase_tables_2d_h():
    """Public header for the pure-phase 2D integer tables."""
    path = os.path.join(INC_DIR, 'cs_pure_phase_tables_2d.h')
    with open(path, 'w', encoding='utf-8') as f:
        f.write("/* GENERATED by codegen/emit_tables.py - DO NOT EDIT */\n")
        f.write("#ifndef CS_PURE_PHASE_TABLES_2D_H\n")
        f.write("#define CS_PURE_PHASE_TABLES_2D_H\n\n")
        f.write("#include <stdint.h>\n")
        f.write("#include \"cs_tables.h\"\n\n")
        f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")

        f.write("/* Pure-phase quantization parameters (mirrors\n")
        f.write(" * chess_spectral.encoder_pure_phase, 1.19.0+).\n")
        f.write(" *\n")
        f.write(" * Signal values scaled by CS_VALS_INT_SCALE_2D=2 to\n")
        f.write(" * represent the half-integer bishop value (B=3.5 in VALS)\n")
        f.write(" * as exact integer 7. King K=100 → 200 fits int16.\n")
        f.write(" *\n")
        f.write(" * D4 character formula is integer-valued throughout (no\n")
        f.write(" * scale-by-LCM trick needed; CHARS entries are ±1, ±2, 0).\n")
        f.write(" * The dim_mu/8 factor is absorbed in CHANNEL_DEQUANT_SCALES_2D.\n")
        f.write(" *\n")
        f.write(" * Fiber tables quantized to int16 with abs-max scaling\n")
        f.write(" * (15 magnitude bits + 1 sign). LOCAL_ADJ_ROWS is\n")
        f.write(" * naturally 0/1 → int8. */\n")
        f.write(f"#define CS_VALS_INT_SCALE_2D       {_VALS_INT_SCALE}\n")
        f.write(f"#define CS_FIBER_QUANT_BITS_2D     {_FIBER_QUANT_BITS}\n")
        f.write(f"#define CS_FIBER_QUANT_MAX_2D      {_FIBER_QUANT_MAX}\n\n")

        f.write("/* Number of fiber-piece types (N, B, R, Q, K). */\n")
        f.write("#define CS_NUM_FIBER_PIECES        5\n\n")

        f.write("/* Number of diag-piece types (P, N, B, R, Q, K). */\n")
        f.write("#define CS_NUM_DIAG_PIECES         6\n\n")

        f.write("/* Number of distinct piece chars (white + black). */\n")
        f.write("#define CS_NUM_PIECE_CHARS         12\n\n")

        f.write("/* Output dimensions. */\n")
        f.write("#define CS_PURE_PHASE_DIM_2D       640\n\n")

        f.write("/* Channel offsets (cell index of each channel block). */\n")
        f.write("#define CS_CHANNEL_A1_OFFSET_2D    0\n")
        f.write("#define CS_CHANNEL_A2_OFFSET_2D    64\n")
        f.write("#define CS_CHANNEL_B1_OFFSET_2D    128\n")
        f.write("#define CS_CHANNEL_B2_OFFSET_2D    192\n")
        f.write("#define CS_CHANNEL_E_OFFSET_2D     256\n")
        f.write("#define CS_CHANNEL_F1_OFFSET_2D    320\n")
        f.write("#define CS_CHANNEL_F2_OFFSET_2D    384\n")
        f.write("#define CS_CHANNEL_F3_OFFSET_2D    448\n")
        f.write("#define CS_CHANNEL_FA_OFFSET_2D    512\n")
        f.write("#define CS_CHANNEL_FD_OFFSET_2D    576\n\n")

        f.write("/* Signed integer piece values, scaled by CS_VALS_INT_SCALE_2D.\n")
        f.write(" * Index: 0=P, 1=N, 2=B, 3=R, 4=Q, 5=K (white),\n")
        f.write(" *        6=p, 7=n, 8=b, 9=r, 10=q, 11=k (black). */\n")
        f.write("extern const int16_t SIGNED_VALS_INT_2D[CS_NUM_PIECE_CHARS];\n\n")

        f.write("/* Quantized symmetric fiber-local table (int16), per\n")
        f.write(" * (fiber_piece, square, direction). Fiber-piece order:\n")
        f.write(" * 0=N, 1=B, 2=R, 3=Q, 4=K. Dequantize via LOCAL_FIBER_SCALE_2D. */\n")
        f.write("extern const int16_t LOCAL_FIBER_3D_INT16[CS_NUM_FIBER_PIECES][CS_BOARD_DIM][3];\n")
        f.write("extern const double LOCAL_FIBER_SCALE_2D;\n\n")

        f.write("/* Dense per-(fiber_piece, square) adjacency rows in {0,1}.\n")
        f.write(" * Stored as int8 for SIMD-friendliness. */\n")
        f.write("extern const int8_t LOCAL_ADJ_ROWS_INT8[CS_NUM_FIBER_PIECES][CS_BOARD_DIM][CS_BOARD_DIM];\n\n")

        f.write("/* Antisymmetric pawn fiber in eigenbasis, quantized to int16. */\n")
        f.write("extern const int16_t PAWN_ANTI_FIBER_INT16[CS_BOARD_DIM][CS_BOARD_DIM];\n")
        f.write("extern const double PAWN_ANTI_SCALE_2D;\n\n")

        f.write("/* Per-piece diagonal-deviation table, quantized to int16.\n")
        f.write(" * Indexed [piece_type][k]; piece_type: 0=P, 1=N, 2=B, 3=R, 4=Q, 5=K. */\n")
        f.write("extern const int16_t DIAG_DEV_INT16_2D[CS_NUM_DIAG_PIECES][CS_BOARD_DIM];\n")
        f.write("extern const double DIAG_DEV_SCALE_2D;\n\n")

        f.write("/* Per-channel dequantization scales (CS_NUM_CHANNELS=10).\n")
        f.write(" * Multiply int32 channel output by the scale to recover\n")
        f.write(" * the float64 value comparable to encode_640(pos, vals=VALS).\n")
        f.write(" * Order matches CHANNELS: A1, A2, B1, B2, E, F1, F2, F3, FA, FD. */\n")
        f.write("extern const double CHANNEL_DEQUANT_SCALES_2D[CS_NUM_CHANNELS];\n\n")

        f.write("#ifdef __cplusplus\n}\n#endif\n\n")
        f.write("#endif /* CS_PURE_PHASE_TABLES_2D_H */\n")
    print(f"Wrote {path}")


def write_cs_pure_phase_tables_data_2d_c():
    """Definitions for the pure-phase 2D integer tables."""
    path = os.path.join(SRC_DIR, 'cs_pure_phase_tables_data_2d.c')
    with open(path, 'w', encoding='utf-8') as f:
        f.write("/* GENERATED by codegen/emit_tables.py - DO NOT EDIT */\n")
        f.write("#include \"cs_pure_phase_tables_2d.h\"\n\n")

        _emit_i16_1d_2d(f, "SIGNED_VALS_INT_2D",
                        PURE_PHASE_SIGNED_VALS_INT_2D, 12)

        _emit_i16_3d_2d(f, "LOCAL_FIBER_3D_INT16",
                        PURE_PHASE_LOCAL_FIBER_INT16_2D, 5, 64, 3)
        f.write("const double LOCAL_FIBER_SCALE_2D = ")
        f.write(f"{_fmt_d(_SCALE_LOCAL_FIBER_3D)};\n\n")

        _emit_i8_3d_2d(f, "LOCAL_ADJ_ROWS_INT8",
                       PURE_PHASE_LOCAL_ADJ_INT8_2D, 5, 64, 64)

        _emit_i16_2d_2d(f, "PAWN_ANTI_FIBER_INT16",
                        PURE_PHASE_PAWN_ANTI_INT16_2D, 64, 64)
        f.write("const double PAWN_ANTI_SCALE_2D = ")
        f.write(f"{_fmt_d(_SCALE_PAWN_ANTI)};\n\n")

        _emit_i16_2d_2d(f, "DIAG_DEV_INT16_2D",
                        PURE_PHASE_DIAG_DEV_INT16_2D, 6, 64)
        f.write("const double DIAG_DEV_SCALE_2D = ")
        f.write(f"{_fmt_d(_SCALE_DIAG_DEV)};\n\n")

        f.write("const double CHANNEL_DEQUANT_SCALES_2D[10] = {\n    ")
        f.write(", ".join(_fmt_d(s) for s in PURE_PHASE_DEQUANT_SCALES_2D))
        f.write("\n};\n")
    print(f"Wrote {path}")


def main():
    os.makedirs(INC_DIR, exist_ok=True)
    os.makedirs(SRC_DIR, exist_ok=True)
    write_cs_tables_h()
    write_cs_fiber_tables_h()
    write_cs_tables_data_c()
    write_committed_tables_npz()
    # 1.19.0+ pure-phase 2D integer tables for the C-port encoder.
    write_cs_pure_phase_tables_2d_h()
    write_cs_pure_phase_tables_data_2d_c()
    print()
    print(f"SPECTRAL_VALS (P,N,B,R,Q,K) = {SPECTRAL_VALS}")
    print(f"TRAD_VALS     (P,N,B,R,Q,K) = {TRAD_VALS}")
    print(f"||DIAG_DEV[Rook]||         = {rook_diag_norm:.4f} (expected ~88.05)")
    print(f"||A_anti||                 = {float(np.linalg.norm(_A_anti)):.4f}")
    print(f"||PAWN_ANTI_FIBER||        = {float(np.linalg.norm(PAWN_ANTI_FIBER)):.4f}")
    print(f"Spatial offsets distinct   = {len(offsets)}/64 ✓")
    print(f"PP signed VALS scaled       = "
          f"{PURE_PHASE_SIGNED_VALS_INT_2D.tolist()}")
    print(f"PP fiber-local scale       = {_SCALE_LOCAL_FIBER_3D:.6e}")
    print(f"PP pawn-anti scale         = {_SCALE_PAWN_ANTI:.6e}")
    print(f"PP diag-dev scale          = {_SCALE_DIAG_DEV:.6e}")
    print("All tables emitted successfully.")


if __name__ == '__main__':
    main()
