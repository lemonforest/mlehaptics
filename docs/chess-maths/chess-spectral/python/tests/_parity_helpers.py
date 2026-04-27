"""Helpers for C ↔ Python encoder parity tests.

Parity model (v1.2.4 with committed tables — fix path (b) shipped)
==================================================================

The C encoder and the Python encoder both load lookup tables from
committed source: C from ``src/cs_tables_data*.c``, Python from
``python/chess_spectral/_committed_tables*.npz``. Both files are
written in lockstep by ``codegen/emit_tables*.py`` — same in-memory
computation, same values. Cross-platform parity therefore holds:
no scipy/LAPACK basis-choice skew because Python doesn't recompute
tables at runtime when the committed npz is present.

Strict byte-for-byte parity is the contract:
    - Header bytes (256 B):              byte-for-byte equal
    - Per-frame metadata (14 B):         byte-for-byte equal
    - Per-frame encoding (raw floats):   numerical within 1e-10
                                         (only float-summation order
                                         drift between Python's numpy
                                         loops and C's serial loops)

To regenerate tables (e.g. when the math definition changes):
    python codegen/regenerate.py
Then commit ALL the regenerated files together — partial commits leave
Python and C disagreeing about the encoder.
"""
from __future__ import annotations

import gzip
import struct
from pathlib import Path

import numpy as np

# Strict cross-platform parity tolerance now that Python loads the
# committed C tables. The only remaining drift is float-summation
# order between Python's numpy loops and C's serial loops, which on
# float32 stays under ~1e-10 absolute difference for the magnitudes
# the encoder produces.
ENCODING_TOL = 1e-10

# 4D format constants (mirror python/chess_spectral/frame_4d.py)
HEADER_SIZE_4D = 256
ENCODING_DIM_4D = 45056
FRAME_TAIL_BYTES = 14
FRAME_BYTES_4D = ENCODING_DIM_4D * 4 + FRAME_TAIL_BYTES


def _read_file(path: Path | str, gz: bool = False) -> bytes:
    """Read a file, optionally gzip-decompressing first."""
    if gz:
        return gzip.open(str(path), "rb").read()
    return Path(path).read_bytes()


def assert_spectral4d_close(
    path_a: str | Path,
    path_b: str | Path,
    *,
    gz: bool = False,
    tol: float = ENCODING_TOL,
) -> None:
    """Assert two .spectral4 / .spectralz4 files agree:
      - byte-for-byte on the 256-byte header
      - byte-for-byte on per-frame metadata (14 B/frame)
      - numerically within `tol` (max abs diff) on per-frame encoding
        floats — typically ~1e-10 since both sides load identical
        committed tables and the only drift is float-summation order

    `gz=True` decompresses both files first (compares the underlying
    .spectral4 payload, ignoring gzip wrapper bytes).
    """
    a = _read_file(path_a, gz=gz)
    b = _read_file(path_b, gz=gz)
    assert len(a) == len(b), (
        f"size mismatch: {Path(path_a).name}={len(a)} "
        f"{Path(path_b).name}={len(b)}"
    )

    # 1. Header byte-equal.
    assert a[:HEADER_SIZE_4D] == b[:HEADER_SIZE_4D], (
        "header bytes differ — format-version / encoding_dim / n_plies "
        "mismatch is not a tolerable cross-platform difference"
    )

    # Header layout (frame_4d.py): magic[8] + version + encoding_dim +
    # frame_bytes + n_plies + board_dim_side + n_dimensions. n_plies is
    # the 4th uint32 → offset 20.
    n_plies = struct.unpack_from("<I", a, 20)[0]
    expected_size = HEADER_SIZE_4D + n_plies * FRAME_BYTES_4D
    assert len(a) == expected_size, (
        f"file size {len(a)} != expected {expected_size} "
        f"for n_plies={n_plies}"
    )

    enc_size = ENCODING_DIM_4D * 4
    for p in range(n_plies):
        frame_off = HEADER_SIZE_4D + p * FRAME_BYTES_4D
        # Encoding (numerical compare).
        enc_a = np.frombuffer(a[frame_off:frame_off + enc_size],
                              dtype=np.float32)
        enc_b = np.frombuffer(b[frame_off:frame_off + enc_size],
                              dtype=np.float32)
        max_diff = float(np.abs(enc_a.astype(np.float64)
                                - enc_b.astype(np.float64)).max())
        assert max_diff <= tol, (
            f"ply {p} encoding floats diverge by {max_diff:.3e} "
            f"(tol {tol:.3e}). With committed tables both sides should "
            f"agree to within float-summation drift."
        )
        # Metadata (byte-equal).
        meta_off = frame_off + enc_size
        meta_a = a[meta_off:meta_off + FRAME_TAIL_BYTES]
        meta_b = b[meta_off:meta_off + FRAME_TAIL_BYTES]
        assert meta_a == meta_b, (
            f"ply {p} metadata bytes differ "
            f"(ply/from/to/promo/flags must match exactly)"
        )
