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

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..'))
PY_DIR = os.path.abspath(os.path.join(HERE, '..', '..'))
INC_DIR = os.path.join(REPO, 'include')
SRC_DIR = os.path.join(REPO, 'src')

# Just import; encoder_512 prints one module-level status line which is fine.
sys.path.insert(0, PY_DIR)
import encoder_512 as enc
from chess_pawn_laplacian import (
    white_pawn_targets, build_directed_adjacency,
)

# --- Derived objects ---------------------------------------------------------

# Piece order for fiber channels (5 pieces: N,B,R,Q,K)
FIBER_PIECES = ['N', 'B', 'R', 'Q', 'K']
# Piece order for diagonal channel (6 pieces: P,N,B,R,Q,K)
DIAG_PIECE_NAMES = ['Pawn', 'Knight', 'Bishop', 'Rook', 'Queen', 'King']

# Long-name lookup for PIECE_FNS
LONG_NAME = {'N': 'Knight', 'B': 'Bishop', 'R': 'Rook', 'Q': 'Queen', 'K': 'King'}

SPECTRAL_VALS_P = float(enc.SPECTRAL_VALS['P'])
SPECTRAL_VALS_N = float(enc.SPECTRAL_VALS['N'])
SPECTRAL_VALS_B = float(enc.SPECTRAL_VALS['B'])
SPECTRAL_VALS_R = float(enc.SPECTRAL_VALS['R'])
SPECTRAL_VALS_Q = float(enc.SPECTRAL_VALS['Q'])
SPECTRAL_VALS_K = float(enc.SPECTRAL_VALS['K'])
SPECTRAL_VALS = [SPECTRAL_VALS_P, SPECTRAL_VALS_N, SPECTRAL_VALS_B,
                 SPECTRAL_VALS_R, SPECTRAL_VALS_Q, SPECTRAL_VALS_K]
TRAD_VALS = [float(enc.VALS[c]) for c in ('P', 'N', 'B', 'R', 'Q', 'K')]

# --- Build PAWN_ANTI_FIBER (in eigenbasis) -----------------------------------
A_white = build_directed_adjacency(white_pawn_targets)
A_anti = 0.5 * (A_white - A_white.T)
assert np.allclose(A_anti, -A_anti.T, atol=1e-12), "A_anti must be antisymmetric"
assert np.linalg.norm(A_anti + A_anti.T) < 1e-12, "A_anti antisymmetry check failed"
PAWN_ANTI_FIBER = enc.EVECS_GRID.T @ A_anti @ enc.EVECS_GRID   # (64, 64)

# --- Build DIAG_DEV[6][64] ----------------------------------------------------
DIAG_DEV = np.zeros((6, 64), dtype=np.float64)

# Pawn: symmetric part of directed pawn Laplacian
A_sym_pawn = 0.5 * (A_white + A_white.T)
L_pawn_sym = enc.graph_laplacian(A_sym_pawn)
C_pawn = enc.EVECS_GRID.T @ L_pawn_sym @ enc.EVECS_GRID
DIAG_DEV[0] = np.diag(C_pawn) - enc.EVALS_GRID

# N, B, R, Q, K
for idx, ch in enumerate(FIBER_PIECES):
    pname = LONG_NAME[ch]
    A = enc.build_adjacency(enc.PIECE_FNS[pname])
    L = enc.graph_laplacian(A)
    C = enc.EVECS_GRID.T @ L @ enc.EVECS_GRID
    DIAG_DEV[idx + 1] = np.diag(C) - enc.EVALS_GRID

# Verify: Rook's diagonal deviation norm should be ~88.05 (chess_rook_shadow.py)
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

    # Pack D4_PERMS into a numpy array
    d4 = np.zeros((8, 64), dtype=np.int32)
    for g in range(8):
        d4[g] = enc.D4_PERMS[g]

    chars = np.zeros((5, 8), dtype=np.int32)
    for i, name in enumerate(('A1', 'A2', 'B1', 'B2', 'E')):
        chars[i] = enc.CHARS[name]

    # LOCAL_FIBER_3D[5][64][3] and LOCAL_ADJ_ROWS[5][64][64]
    lf3d = np.zeros((5, 64, 3), dtype=np.float64)
    lar = np.zeros((5, 64, 64), dtype=np.float64)
    for idx, ch in enumerate(FIBER_PIECES):
        for s in range(64):
            lf3d[idx, s, :] = enc.LOCAL_FIBER_3D[(ch, s)]
            lar[idx, s, :] = enc.LOCAL_ADJ_ROWS[(ch, s)]

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

def main():
    os.makedirs(INC_DIR, exist_ok=True)
    os.makedirs(SRC_DIR, exist_ok=True)
    write_cs_tables_h()
    write_cs_fiber_tables_h()
    write_cs_tables_data_c()
    print()
    print(f"SPECTRAL_VALS (P,N,B,R,Q,K) = {SPECTRAL_VALS}")
    print(f"TRAD_VALS     (P,N,B,R,Q,K) = {TRAD_VALS}")
    print(f"||DIAG_DEV[Rook]||         = {rook_diag_norm:.4f} (expected ~88.05)")
    print(f"||A_anti||                 = {float(np.linalg.norm(A_anti)):.4f}")
    print(f"||PAWN_ANTI_FIBER||        = {float(np.linalg.norm(PAWN_ANTI_FIBER)):.4f}")
    print(f"Spatial offsets distinct   = {len(offsets)}/64 ✓")
    print("All tables emitted successfully.")


if __name__ == '__main__':
    main()
