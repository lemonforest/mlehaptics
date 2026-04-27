"""Helpers for C ↔ Python encoder parity tests.

Why we don't use byte equality for the encoding floats
======================================================

The C encoder uses lookup tables that are codegen'd-and-committed in
src/cs_tables_data*.c. Those tables came from one specific platform's
scipy/LAPACK output (Windows MKL, on the maintainer's machine).

The Python encoder builds its tables at runtime via scipy.linalg.eigh
on each call. When eigenvalues are degenerate, the orthogonal basis
chosen for the degenerate subspace depends on the BLAS backend
(OpenBLAS on Linux, MKL on Windows, Accelerate on macOS) — so the
fiber-channel projections can differ by a few ulp, which on float32
turns into byte-level diffs in the encoded output.

The Python encoder therefore agrees with the C encoder *byte-for-byte*
only on the codegen-source platform (Windows). Elsewhere, agreement
is numerical-within-tolerance, not byte-for-byte. v1.2.4 documents
this as a known limit and uses a 1e-4 absolute tolerance on float32
encoding values (~4 ulp at the magnitudes typical of channel
projections). A future release may codegen tables on each target
platform, or have Python load the committed C tables to restore
strict byte parity.

Comparison strategy used by these helpers:
    - Header bytes (256 B):           byte-for-byte equal (no FP)
    - Per-frame metadata (14 B):      byte-for-byte equal (ints only)
    - Per-frame encoding (float32[]): numerical equality within TOL
"""
from __future__ import annotations

import struct
from pathlib import Path
import gzip

import numpy as np

# Float32 numerical tolerance for cross-platform encoder agreement.
# Picked at ~4 ulp for typical channel-projection magnitudes (O(0.1)
# to O(10)). Empirical cross-platform diffs observed in CI are
# bounded by ~1e-5; 1e-4 leaves comfortable headroom.
ENCODING_TOL = 1e-4

# 4D format constants (mirror python/chess_spectral/frame_4d.py)
HEADER_SIZE_4D = 256
ENCODING_DIM_4D = 45056
FRAME_TAIL_BYTES = 14
FRAME_BYTES_4D = ENCODING_DIM_4D * 4 + FRAME_TAIL_BYTES

# 2D format constants (mirror python/chess_spectral/frame.py)
HEADER_SIZE_2D = 256
ENCODING_DIM_2D = 640
FRAME_BYTES_2D = ENCODING_DIM_2D * 4 + 8  # 4 (ply) + 4 (move metadata)


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
      - byte-for-byte on the header (256 B)
      - byte-for-byte on per-frame metadata (14 B/frame)
      - numerically within `tol` (max abs diff) on per-frame encoding
        floats (45056 float32 per frame)

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

    # 2-3. Per-frame: encoding numerical, metadata byte-equal.
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
            f"(tol {tol:.3e}). This is the known cross-platform "
            f"Python-table-vs-committed-C-table skew; if it's much "
            f"larger than 1e-4, it indicates a real encoder bug."
        )
        # Metadata (byte-equal).
        meta_off = frame_off + enc_size
        meta_a = a[meta_off:meta_off + FRAME_TAIL_BYTES]
        meta_b = b[meta_off:meta_off + FRAME_TAIL_BYTES]
        assert meta_a == meta_b, (
            f"ply {p} metadata bytes differ "
            f"(ply/from/to/promo/flags must match exactly)"
        )
