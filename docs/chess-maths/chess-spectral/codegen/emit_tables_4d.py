#!/usr/bin/env python3
"""Emit C const tables for the 40960-dim 4D spectral chess encoder.

Writes:
  include/cs_tables_4d.h          - constants + piece enum + small table externs
  include/cs_fiber_tables_4d.h    - extern decls for FIBER_LOCAL / W_ANTI_DCT /
                                    DIAG_DEV_4D (populated across P1a + P4)
  src/cs_tables_data_4d.c         - GENERATED table definitions

Tables emitted in P1a (this script):
  P8_EVECS[8][8]                  double
  W_ANTI_DCT[8][8]                double (factored 8x8 pawn-antisym block)
  COORD_RESID[4][4096]            double (std-4D coord residual masks)
  ORBIT_OF[4096]                  uint16 (B_4 orbit label per square)
  ORBIT_MEMBERS[4096]             uint16 (CSR-packed orbit member list)
  ORBIT_OFFSETS[N_ORBITS+1]       uint16 (CSR row pointers)
  ORBIT_INV_SIZE[N_ORBITS]        double (1/|orbit|)
  DIAG_DEV_4D[6][4096]            double (pawn_sym, N, B, R, Q, K)
  PIECE_VALUES_4D[6]              double (nominal P,N,B,R,Q,K values)

FIBER_LOCAL_4D and sparse piece adjacencies are emitted in P4 (not P1a).
See plan: "when-we-need-to-spicy-seahorse" (C:\\Users\\sckir\\.claude\\plans\\).
"""
from __future__ import annotations

import os
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..'))
PY_DIR = os.path.abspath(os.path.join(HERE, '..', 'python'))
INC_DIR = os.path.join(REPO, 'include')
SRC_DIR = os.path.join(REPO, 'src')

sys.path.insert(0, PY_DIR)
from chess_spectral import tables_4d as t4       # noqa: E402
from chess_spectral import encoder_4d as enc4    # noqa: E402


# ─── Piece tables (mirror encoder_4d.PIECE_VALUES_4D / diag_dev row order) ──

# Diag-dev row order must match t4.diag_dev_4d construction:
#   pawn_sym=0, knight=1, bishop=2, rook=3, queen=4, king=5
DIAG_PIECE_CHARS = ['P', 'N', 'B', 'R', 'Q', 'K']

# Nominal piece values — |value| for positive (white) pieces; the encoder
# flips sign for black. Same magnitudes as encoder_4d.PIECE_VALUES_4D.
PIECE_VALUES_4D = [float(enc4.PIECE_VALUES_4D[c]) for c in DIAG_PIECE_CHARS]

# Fiber piece order (matches _PIECE_TARGETS_4D in tables_4d): N, B, R, Q, K.
FIBER_PIECE_CHARS = [c for c, _ in t4._PIECE_TARGETS_4D]
assert FIBER_PIECE_CHARS == ['N', 'B', 'R', 'Q', 'K'], \
    f"unexpected fiber piece order: {FIBER_PIECE_CHARS}"


# ─── P8 eigenbasis (1D DCT factor) ──────────────────────────────────────────

P8_EVECS, P8_EVALS = t4.eig_p8()
assert P8_EVECS.shape == (8, 8)
assert P8_EVALS.shape == (8,)


# ─── W_ANTI_DCT (factored 8x8 pawn antisym block in DCT basis) ──────────────

W_ANTI_DCT = t4.w_anti_dct_block()
assert W_ANTI_DCT.shape == (8, 8)
# Sanity: antisymmetric in the DCT basis as well (similarity by orthogonal U).
assert np.allclose(W_ANTI_DCT, -W_ANTI_DCT.T, atol=1e-12)


# ─── COORD_RESID (std-4D coord residual masks) ──────────────────────────────

COORD_RESID = np.zeros((t4.N_DIMS, t4.N_SQUARES), dtype=np.float64)
for s in range(t4.N_SQUARES):
    c = np.array(t4.rc4(s), dtype=np.float64) - 3.5
    mean_c = c.mean()  # identically 0 on the centered lattice
    for a in range(t4.N_DIMS):
        COORD_RESID[a, s] = c[a] - mean_c


# ─── B_4 orbit partition (for A_1 channel) ──────────────────────────────────
#
# Avoid materializing the 4096x4096 sparse projector; we only need the
# partition + members list.
CLOSURE = t4.b4_closure()
assert len(CLOSURE) == 384, f"B_4 closure size {len(CLOSURE)} != 384"

ORBIT_OF = -np.ones(t4.N_SQUARES, dtype=np.int64)
_orbits = []
for s in range(t4.N_SQUARES):
    if ORBIT_OF[s] >= 0:
        continue
    x, y, z, w = t4.rc4(s)
    orb_set = set()
    for g in CLOSURE:
        orb_set.add(t4.sq4(*t4._apply_b4_to_square(g, x, y, z, w)))
    orb_id = len(_orbits)
    for t_sq in orb_set:
        ORBIT_OF[t_sq] = orb_id
    _orbits.append(sorted(orb_set))

N_ORBITS = len(_orbits)
assert np.all(ORBIT_OF >= 0), "some square has no orbit label"
# Sanity: orbit sizes divide 384.
for orb in _orbits:
    assert 384 % len(orb) == 0, f"orbit size {len(orb)} does not divide 384"

ORBIT_OFFSETS = np.zeros(N_ORBITS + 1, dtype=np.int64)
for i, orb in enumerate(_orbits):
    ORBIT_OFFSETS[i + 1] = ORBIT_OFFSETS[i] + len(orb)
assert ORBIT_OFFSETS[-1] == t4.N_SQUARES

ORBIT_MEMBERS = np.zeros(t4.N_SQUARES, dtype=np.int64)
for i, orb in enumerate(_orbits):
    ORBIT_MEMBERS[ORBIT_OFFSETS[i]:ORBIT_OFFSETS[i + 1]] = orb

ORBIT_INV_SIZE = np.array([1.0 / len(orb) for orb in _orbits], dtype=np.float64)

# All uint16 storage: square indices go up to 4095, N_ORBITS is small (tens).
assert t4.N_SQUARES <= 0xFFFF, "uint16 too narrow for N_SQUARES"
assert N_ORBITS <= 0xFFFF, "uint16 too narrow for N_ORBITS"


# ─── DIAG_DEV_4D (6 x 4096) ─────────────────────────────────────────────────
#
# Heavy compute: builds the 128 MB dense U tensor and runs einsum over six
# 4096x4096 Laplacians. ~20-30 s on a modern laptop. Runs once per codegen.

print("Building U tensor + DIAG_DEV_4D (heavy; ~30 s) ...", flush=True)
U_TENSOR = t4.build_u_tensor_4d()
DIAG_DEV_4D = t4.diag_dev_4d(U=U_TENSOR)
assert DIAG_DEV_4D.shape == (6, t4.N_SQUARES)
# Rook row (idx 3) must be nonzero (does-not-commute-with-grid witness).
rook_norm = float(np.linalg.norm(DIAG_DEV_4D[3]))
assert rook_norm > 1.0, f"rook diag-dev norm {rook_norm} unexpectedly small"
del U_TENSOR  # free 128 MB


# ─── Emission helpers ───────────────────────────────────────────────────────

def _fmt_d(x: float) -> str:
    """Emit a double in full float64 precision."""
    return f"{float(x):.17e}"


def emit_u16_1d(fout, name: str, arr, dim0: int) -> None:
    fout.write(f"const uint16_t {name}[{dim0}] = {{\n    ")
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


def emit_f64_1d(fout, name: str, arr, dim0: int) -> None:
    fout.write(f"const double {name}[{dim0}] = {{\n    ")
    fout.write(", ".join(_fmt_d(arr[i]) for i in range(dim0)))
    fout.write("\n};\n\n")


def emit_f64_2d(fout, name: str, arr, dim0: int, dim1: int) -> None:
    fout.write(f"const double {name}[{dim0}][{dim1}] = {{\n")
    for i in range(dim0):
        fout.write("    {")
        fout.write(", ".join(_fmt_d(arr[i][j]) for j in range(dim1)))
        fout.write(f"}}{',' if i + 1 < dim0 else ''}\n")
    fout.write("};\n\n")


# ─── cs_tables_4d.h — public constants + piece enum + small externs ─────────

def write_cs_tables_4d_h() -> None:
    path = os.path.join(INC_DIR, 'cs_tables_4d.h')
    with open(path, 'w', encoding='utf-8') as f:
        f.write("/* GENERATED by codegen/emit_tables_4d.py - DO NOT EDIT BY HAND */\n")
        f.write("#ifndef CS_TABLES_4D_H\n#define CS_TABLES_4D_H\n\n")
        f.write("#include <stdint.h>\n\n")
        f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")

        f.write("/* 4D encoding dimensions (Z_8^4 lattice) */\n")
        f.write(f"#define CS_BOARD_SIDE_4D      {t4.BOARD_SIDE}\n")
        f.write(f"#define CS_N_DIMS             {t4.N_DIMS}\n")
        f.write(f"#define CS_N_SQUARES_4D       {t4.N_SQUARES}\n")
        f.write(f"#define CS_N_CHANNELS_4D      {enc4.N_CHANNELS_4D}\n")
        f.write(f"#define CS_ENCODING_DIM_4D    {enc4.ENCODING_DIM_4D}\n\n")

        f.write("/* B_4 group order and orbit count on Z_8^4. */\n")
        f.write("#define CS_B4_ORDER           384\n")
        f.write(f"#define CS_N_ORBITS_4D        {N_ORBITS}\n\n")

        f.write("/* Fiber basis rank (cross-piece SVD of off-diag piece Laplacians) */\n")
        f.write("#define CS_N_SYM_FIBER_4D     3\n\n")

        f.write("/* Diag-dev row order: P=0, N=1, B=2, R=3, Q=4, K=5 (6 pieces). */\n")
        f.write("typedef enum {\n")
        for i, ch in enumerate(DIAG_PIECE_CHARS):
            f.write(f"    CS_PIECE_4D_{ch} = {i},\n")
        f.write("    CS_PIECE_4D_COUNT = 6\n")
        f.write("} cs_piece_4d_t;\n\n")

        f.write("/* Fiber-piece row order: N=0, B=1, R=2, Q=3, K=4 (5 pieces; no pawn). */\n")
        f.write("typedef enum {\n")
        for i, ch in enumerate(FIBER_PIECE_CHARS):
            f.write(f"    CS_FIBER_PIECE_4D_{ch} = {i},\n")
        f.write("    CS_FIBER_PIECE_4D_COUNT = 5\n")
        f.write("} cs_fiber_piece_4d_t;\n\n")

        f.write("/* P_8 eigenbasis (DCT-II factor) and P_8 Laplacian spectrum. */\n")
        f.write("extern const double P8_EVECS[8][8];\n")
        f.write("extern const double P8_EVALS[8];\n\n")

        f.write("/* std-4D coordinate residual masks: (I_4 - (1/4) J_4) applied\n")
        f.write(" * to centered coordinates, indexed [axis][square]. */\n")
        f.write("extern const double COORD_RESID[4][4096];\n\n")

        f.write("/* B_4 A_1 orbit partition, stored as CSR.\n")
        f.write(" *   ORBIT_OF[s]                  orbit index for square s\n")
        f.write(" *   ORBIT_MEMBERS[ORBIT_OFFSETS[o] .. ORBIT_OFFSETS[o+1])\n")
        f.write(" *                                squares in orbit o, ascending\n")
        f.write(" *   ORBIT_INV_SIZE[o]            1/|orbit_o|\n")
        f.write(" */\n")
        f.write("extern const uint16_t ORBIT_OF[4096];\n")
        f.write("extern const uint16_t ORBIT_MEMBERS[4096];\n")
        f.write(f"extern const uint16_t ORBIT_OFFSETS[{N_ORBITS + 1}];\n")
        f.write(f"extern const double   ORBIT_INV_SIZE[{N_ORBITS}];\n\n")

        f.write("/* Nominal piece values (signed-magnitude; encoder flips sign for black). */\n")
        f.write("extern const double PIECE_VALUES_4D[6];\n\n")

        f.write("#ifdef __cplusplus\n}\n#endif\n\n")
        f.write("#endif /* CS_TABLES_4D_H */\n")
    print(f"Wrote {path}")


# ─── cs_fiber_tables_4d.h — externs for fiber / pawn-antisym / diag-dev ─────

def write_cs_fiber_tables_4d_h() -> None:
    path = os.path.join(INC_DIR, 'cs_fiber_tables_4d.h')
    with open(path, 'w', encoding='utf-8') as f:
        f.write("/* GENERATED by codegen/emit_tables_4d.py - DO NOT EDIT BY HAND */\n")
        f.write("#ifndef CS_FIBER_TABLES_4D_H\n#define CS_FIBER_TABLES_4D_H\n\n")
        f.write("#include \"cs_tables_4d.h\"\n\n")
        f.write("#ifdef __cplusplus\nextern \"C\" {\n#endif\n\n")

        f.write("/* Pawn antisymmetric fiber, factored form.\n")
        f.write(" *   A_anti = I (x) I (x) I (x) A_w_anti  (Kronecker identity)\n")
        f.write(" *   U^T A_anti U = I (x) I (x) I (x) (U_P8^T A_w_anti U_P8)\n")
        f.write(" * so the 4096x4096 DCT-basis matrix is block-diagonal over (x,y,z)\n")
        f.write(" * with this single 8x8 block on the w-axis. */\n")
        f.write("extern const double W_ANTI_DCT[8][8];\n\n")

        f.write("/* Per-piece diagonal deviation from grid spectrum, mode space.\n")
        f.write(" * Indexed [cs_piece_4d_t][k]. */\n")
        f.write("extern const double DIAG_DEV_4D[6][4096];\n\n")

        f.write("/* FIBER_LOCAL_4D and piece-adjacency CSR arrays emitted in P4. */\n")
        f.write("/* extern const float FIBER_LOCAL_4D[5][4096][3]; */\n\n")

        f.write("#ifdef __cplusplus\n}\n#endif\n\n")
        f.write("#endif /* CS_FIBER_TABLES_4D_H */\n")
    print(f"Wrote {path}")


# ─── cs_tables_data_4d.c — definitions ──────────────────────────────────────

def write_cs_tables_data_4d_c() -> None:
    path = os.path.join(SRC_DIR, 'cs_tables_data_4d.c')
    with open(path, 'w', encoding='utf-8') as f:
        f.write("/* GENERATED by codegen/emit_tables_4d.py - DO NOT EDIT BY HAND */\n")
        f.write("#include \"cs_tables_4d.h\"\n")
        f.write("#include \"cs_fiber_tables_4d.h\"\n\n")

        emit_f64_2d(f, "P8_EVECS", P8_EVECS, 8, 8)
        emit_f64_1d(f, "P8_EVALS", P8_EVALS, 8)
        emit_f64_2d(f, "W_ANTI_DCT", W_ANTI_DCT, 8, 8)
        emit_f64_2d(f, "COORD_RESID", COORD_RESID, t4.N_DIMS, t4.N_SQUARES)
        emit_u16_1d(f, "ORBIT_OF", ORBIT_OF, t4.N_SQUARES)
        emit_u16_1d(f, "ORBIT_MEMBERS", ORBIT_MEMBERS, t4.N_SQUARES)
        emit_u16_1d(f, "ORBIT_OFFSETS", ORBIT_OFFSETS, N_ORBITS + 1)
        emit_f64_1d(f, "ORBIT_INV_SIZE", ORBIT_INV_SIZE, N_ORBITS)
        emit_f64_2d(f, "DIAG_DEV_4D", DIAG_DEV_4D, 6, t4.N_SQUARES)
        emit_f64_1d(f, "PIECE_VALUES_4D", PIECE_VALUES_4D, 6)
    print(f"Wrote {path}")


# ─── Main ───────────────────────────────────────────────────────────────────

def main() -> None:
    os.makedirs(INC_DIR, exist_ok=True)
    os.makedirs(SRC_DIR, exist_ok=True)
    write_cs_tables_4d_h()
    write_cs_fiber_tables_4d_h()
    write_cs_tables_data_4d_c()
    print()
    orbit_sizes = sorted({len(orb) for orb in _orbits})
    print(f"B_4 orbits:          {N_ORBITS} classes, sizes {orbit_sizes}")
    print(f"PIECE_VALUES_4D:     {PIECE_VALUES_4D}")
    print(f"||DIAG_DEV[Rook]||:  {rook_norm:.4f} (expected ~nonzero witness)")
    print(f"||W_ANTI_DCT||:      {float(np.linalg.norm(W_ANTI_DCT)):.4f}")
    total_bytes = (
        # binary payload, not source
        8 * 8 * 8                               # P8_EVECS
        + 8 * 8                                 # P8_EVALS
        + 8 * 8 * 8                             # W_ANTI_DCT
        + 4 * 4096 * 8                          # COORD_RESID
        + 4096 * 2                              # ORBIT_OF
        + 4096 * 2                              # ORBIT_MEMBERS
        + (N_ORBITS + 1) * 2                    # ORBIT_OFFSETS
        + N_ORBITS * 8                          # ORBIT_INV_SIZE
        + 6 * 4096 * 8                          # DIAG_DEV_4D
        + 6 * 8                                 # PIECE_VALUES_4D
    )
    print(f"Binary table size:   {total_bytes} bytes (~{total_bytes / 1024:.1f} KB)")
    print("All P1a tables emitted successfully.")


if __name__ == '__main__':
    main()
