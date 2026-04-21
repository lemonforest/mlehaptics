#!/usr/bin/env python3
"""
Emit C reference test vectors for the 640-dim spectral chess encoder.

Writes:  test/test_vectors.h

For each test position, emits:
  - board_signal() (64 doubles, using SPECTRAL_VALS)
  - 5 irrep projections (A1, A2, B1, B2, E), 64 doubles each
  - 3 symmetric fiber channels, 64 doubles each
  - antisymmetric pawn channel (64 doubles)
  - diagonal deviation channel (64 doubles)
  - full 640-dim encoding
  - reference 512-dim encoding (encode_512_spectral) for backward-compat

Positions covered:
  empty, single knight, KRK endgame, starting position, middlegame,
  pawns-only chain, a D4-rotated starting position (90° rotation),
  and a knight in a rotated location.
"""
import os
import sys
import io
import numpy as np

# Windows console: keep stdout on UTF-8 for consistency with emit_tables.py
# (prior codegen inherited this fix transitively from encoder_512's import).
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8',
                                  errors='replace')

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..'))
PKG_DIR = os.path.abspath(os.path.join(HERE, '..', 'python'))
TEST_DIR = os.path.join(REPO, 'test')

# Pull everything from the production chess_spectral package (same SSOT the
# C reference was derived from). No dependency on the archived encoder_512.
sys.path.insert(0, PKG_DIR)
from chess_spectral.tables import (
    SPECTRAL_VALS, SHORT_PFNS,
    LOCAL_FIBER_3D, LOCAL_ADJ_ROWS,
    PAWN_ANTI_FIBER, DIAG_DEV,
    board_signal, project_irrep,
)

# Fiber-piece index matches chess_spectral.tables construction order:
# LOCAL_FIBER_3D / LOCAL_ADJ_ROWS first axis is (N, B, R, Q, K).
_FIBER_IDX = {'N': 0, 'B': 1, 'R': 2, 'Q': 3, 'K': 4}

PIECE_TYPE_IDX = {'P': 0, 'N': 1, 'B': 2, 'R': 3, 'Q': 4, 'K': 5}


def _encode_512_spectral(pos):
    """Reference for the tp{i}_enc512 back-compat column.

    Identical math to the (archived) encoder_512.encode_512_spectral: 5 D4
    irreps + 3 symmetric fiber channels = 512 dims, using SPECTRAL_VALS.
    Kept inline so codegen does not depend on the archived module.
    """
    sig = board_signal(pos, vals=SPECTRAL_VALS)
    channels = [project_irrep(sig, n) for n in ('A1', 'A2', 'B1', 'B2', 'E')]
    for d in range(3):
        fc = np.zeros(64)
        for si, pchar in pos.items():
            pkey = pchar.upper()
            if pkey not in _FIBER_IDX:
                continue
            pidx = _FIBER_IDX[pkey]
            fib_d = LOCAL_FIBER_3D[pidx, si, d]
            adj_row = LOCAL_ADJ_ROWS[pidx, si]
            gradient = float(adj_row @ sig)
            fc += gradient * fib_d * adj_row
        channels.append(fc)
    return np.concatenate(channels)


def sq(r, c):
    return r * 8 + c


def parse_fen_placement(fen):
    """Parse FEN piece placement into {square: piece_char}.
    Convention: row 0 = rank 8 (black's back rank), matching encoder_512.
    """
    pos = {}
    placement = fen.split()[0]
    rows = placement.split('/')
    assert len(rows) == 8, f"Bad FEN placement: {fen}"
    for r, row in enumerate(rows):  # r=0 is rank 8
        c = 0
        for ch in row:
            if ch.isdigit():
                c += int(ch)
            else:
                pos[sq(r, c)] = ch
                c += 1
        assert c == 8, f"Bad FEN row: {row}"
    return pos


def rotate_position_90(pos):
    """Rotate the position 90° clockwise: new (r,c) = (c, 7-r) ; i.e. old (r,c) -> new (c, 7-r)."""
    new_pos = {}
    for s, p in pos.items():
        r, c = s // 8, s % 8
        nr, nc = c, 7 - r
        new_pos[sq(nr, nc)] = p
    return new_pos


# --- Test positions ----------------------------------------------------------

TEST_POSITIONS = [
    ("empty", {}),
    ("single_knight", {sq(4, 4): 'N'}),
    ("krk_endgame",
     parse_fen_placement("8/8/8/3k4/8/8/3K4/3R4 w - - 0 1")),
    ("starting",
     parse_fen_placement("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")),
    ("middlegame",
     parse_fen_placement("r1bq1rk1/pp2nppp/2n1p3/2bpP3/3P4/2NB1N2/PPP2PPP/R1BQ1RK1 w - - 0 1")),
    ("pawns_only",
     parse_fen_placement("8/pppppppp/8/8/8/8/PPPPPPPP/8 w - - 0 1")),
    ("rotated_start",
     rotate_position_90(parse_fen_placement("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"))),
    ("single_knight_rotated",
     rotate_position_90({sq(4, 4): 'N'})),
    ("single_rook",
     {sq(3, 3): 'R'}),
    ("pawn_single_white",
     {sq(6, 4): 'P'}),
]


# --- Reference computations --------------------------------------------------

def ref_signal(pos):
    return board_signal(pos, vals=SPECTRAL_VALS)


def ref_irrep(sig, name):
    return project_irrep(sig, name)


def ref_sym_fiber(pos, sig, d):
    fc = np.zeros(64)
    for si, pchar in pos.items():
        pkey = pchar.upper()
        if pkey not in SHORT_PFNS:
            continue
        pidx = _FIBER_IDX[pkey]
        fib_d = LOCAL_FIBER_3D[pidx, si, d]
        adj_row = LOCAL_ADJ_ROWS[pidx, si]
        gradient = float(adj_row @ sig)
        fc += gradient * fib_d * adj_row
    return fc


def ref_antisymmetric(pos):
    out = np.zeros(64)
    for si, pchar in pos.items():
        if pchar.upper() != 'P':
            continue
        sign = 1.0 if pchar == 'P' else -1.0  # white=+, black=-
        w = sign * SPECTRAL_VALS['P']  # SPECTRAL_VALS[P] unsigned part
        out += w * PAWN_ANTI_FIBER[si, :]
    return out


def ref_diagonal(pos, sig):
    out = np.zeros(64)
    for si, pchar in pos.items():
        t = PIECE_TYPE_IDX[pchar.upper()]
        w = sig[si]   # signed (color applied via signal)
        out += w * DIAG_DEV[t, :]
    return out


def ref_640(pos):
    sig = ref_signal(pos)
    parts = []
    for name in ('A1', 'A2', 'B1', 'B2', 'E'):
        parts.append(ref_irrep(sig, name))
    for d in range(3):
        parts.append(ref_sym_fiber(pos, sig, d))
    parts.append(ref_antisymmetric(pos))
    parts.append(ref_diagonal(pos, sig))
    return np.concatenate(parts)


def ref_512(pos):
    return _encode_512_spectral(pos)


# --- Emission ----------------------------------------------------------------

def fmt_d(x):
    return f"{float(x):.17e}"


def emit_array(fout, name, arr):
    flat = np.asarray(arr).reshape(-1)
    n = flat.size
    fout.write(f"static const double {name}[{n}] = {{\n    ")
    items_per_line = 4
    for i, v in enumerate(flat):
        fout.write(fmt_d(v))
        if i + 1 < n:
            fout.write(",")
            if (i + 1) % items_per_line == 0:
                fout.write("\n    ")
            else:
                fout.write(" ")
    fout.write("\n};\n\n")


def emit_position_occupancy(fout, name, pos):
    """Emit position occupancy as two parallel arrays: squares + piece codes.
       Piece code encoding:
         0=empty, +1=P, +2=N, +3=B, +4=R, +5=Q, +6=K (white),
                  -1=p, -2=n, -3=b, -4=r, -5=q, -6=k (black).
       The count is emitted as a #define so it is a constant expression in
       static initializers (MSVC does not treat `static const int` as one).
    """
    sqs = sorted(pos.keys())
    codes = []
    for s in sqs:
        ch = pos[s]
        idx = PIECE_TYPE_IDX[ch.upper()] + 1  # 1..6
        codes.append(idx if ch.isupper() else -idx)
    n = len(sqs)
    fout.write(f"#define {name.upper()}_COUNT {n}\n")
    if n == 0:
        fout.write(f"static const unsigned char {name}_squares[1] = {{0}};\n")
        fout.write(f"static const signed char {name}_pieces[1] = {{0}};\n\n")
    else:
        fout.write(f"static const unsigned char {name}_squares[{n}] = {{ ")
        fout.write(", ".join(str(s) for s in sqs))
        fout.write(" };\n")
        fout.write(f"static const signed char {name}_pieces[{n}] = {{ ")
        fout.write(", ".join(str(c) for c in codes))
        fout.write(" };\n\n")


def main():
    os.makedirs(TEST_DIR, exist_ok=True)
    path = os.path.join(TEST_DIR, 'test_vectors.h')

    with open(path, 'w', encoding='utf-8') as f:
        f.write("/* GENERATED by codegen/emit_test_vectors.py — DO NOT EDIT BY HAND */\n")
        f.write("#ifndef CS_TEST_VECTORS_H\n#define CS_TEST_VECTORS_H\n\n")
        f.write("/* Piece code convention:\n")
        f.write(" *   +1..+6 = white P,N,B,R,Q,K ;  -1..-6 = black p,n,b,r,q,k\n")
        f.write(" * The test harness decodes these into cs_position_t. */\n\n")
        f.write(f"#define CS_TEST_NUM_POSITIONS {len(TEST_POSITIONS)}\n\n")

        # Emit position metadata (names, occupancy)
        for i, (name, pos) in enumerate(TEST_POSITIONS):
            f.write(f"/* --- Position {i}: {name} --- */\n")
            emit_position_occupancy(f, f"tp{i}", pos)

        # Emit reference vectors per position
        for i, (name, pos) in enumerate(TEST_POSITIONS):
            sig = ref_signal(pos)
            emit_array(f, f"tp{i}_signal", sig)
            for j, irn in enumerate(('A1', 'A2', 'B1', 'B2', 'E')):
                emit_array(f, f"tp{i}_irrep{j}", ref_irrep(sig, irn))
            for d in range(3):
                emit_array(f, f"tp{i}_sym{d}", ref_sym_fiber(pos, sig, d))
            emit_array(f, f"tp{i}_anti", ref_antisymmetric(pos))
            emit_array(f, f"tp{i}_diag", ref_diagonal(pos, sig))
            emit_array(f, f"tp{i}_enc640", ref_640(pos))
            emit_array(f, f"tp{i}_enc512", ref_512(pos))

        # Position name array for test reporting
        f.write("static const char *const cs_test_position_names[CS_TEST_NUM_POSITIONS] = {\n")
        for i, (name, _) in enumerate(TEST_POSITIONS):
            f.write(f"    \"{name}\"{',' if i + 1 < len(TEST_POSITIONS) else ''}\n")
        f.write("};\n\n")

        # Aggregate table of pointers so the test harness can loop cleanly
        f.write("typedef struct {\n")
        f.write("    const char *name;\n")
        f.write("    int count;\n")
        f.write("    const unsigned char *squares;\n")
        f.write("    const signed char *pieces;\n")
        f.write("    const double *signal;\n")
        f.write("    const double *irrep[5];\n")
        f.write("    const double *sym[3];\n")
        f.write("    const double *anti;\n")
        f.write("    const double *diag;\n")
        f.write("    const double *enc640;\n")
        f.write("    const double *enc512;\n")
        f.write("} cs_test_vector_t;\n\n")

        f.write("static const cs_test_vector_t cs_test_vectors[CS_TEST_NUM_POSITIONS] = {\n")
        for i, (name, _) in enumerate(TEST_POSITIONS):
            f.write(f"    {{ \"{name}\", TP{i}_COUNT, tp{i}_squares, tp{i}_pieces,\n")
            f.write(f"      tp{i}_signal,\n")
            f.write(f"      {{ tp{i}_irrep0, tp{i}_irrep1, tp{i}_irrep2, tp{i}_irrep3, tp{i}_irrep4 }},\n")
            f.write(f"      {{ tp{i}_sym0, tp{i}_sym1, tp{i}_sym2 }},\n")
            f.write(f"      tp{i}_anti, tp{i}_diag, tp{i}_enc640, tp{i}_enc512 }}")
            f.write(",\n" if i + 1 < len(TEST_POSITIONS) else "\n")
        f.write("};\n\n")

        f.write("#endif /* CS_TEST_VECTORS_H */\n")

    print(f"Wrote {path}")
    print(f"Generated {len(TEST_POSITIONS)} test positions.")


if __name__ == '__main__':
    main()
