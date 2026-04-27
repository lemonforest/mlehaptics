"""Helpers for C ↔ Python encoder parity tests.

Why we compare channel ENERGIES, not raw float values
=====================================================

The C encoder uses lookup tables codegen'd-and-committed in
src/cs_tables_data*.c (originally from Windows scipy/MKL). The Python
encoder builds its tables at runtime via scipy.linalg.eigh, whose
choice of orthonormal basis for any DEGENERATE eigensubspace depends
on the BLAS backend (OpenBLAS on Linux, MKL on Windows, Accelerate on
macOS arm64). Different bases for the same subspace mean different
per-element projections — observed: up to ~1.0 in absolute float
value on macOS arm64 vs Windows for the same fiber channel.

But projection ENERGIES (||proj||² = sum of squares within each
channel block) ARE basis-invariant under orthonormal change of basis.
So even when C and Python pick different bases for a fiber subspace,
the channel energies must agree within float32 noise.

This is the meaningful cross-platform parity claim. Strict per-element
byte parity holds only on the codegen-source platform (Windows). v1.2.4
documents this as a known limit; a future release may codegen tables
on each target platform or have Python load the committed C tables.

Comparison strategy used by these helpers:
    - Header bytes (256 B):              byte-for-byte equal
    - Per-frame metadata (14 B):         byte-for-byte equal
    - Per-frame channel energies:        numerical, abs-tol on float32
    - Per-frame encoding (raw floats):   strict tol on Windows only
                                         (skipped elsewhere — see above)
"""
from __future__ import annotations

import gzip
import struct
import sys
from pathlib import Path

import numpy as np

# Cross-platform numerical tolerance for channel ENERGIES (basis-
# invariant). Picked at ~1e-2 to accommodate float32 round-off plus
# any small numerical drift in the energy calculation across BLAS
# backends. Empirical diffs in CI are bounded by < 1e-3; 1e-2 leaves
# comfortable headroom without making the test useless.
ENERGY_TOL = 1e-2

# Strict tolerance for raw per-element float comparison. Only valid
# on the codegen-source platform (Windows), where Python and C use
# the same scipy/MKL output for the encoder tables.
STRICT_FLOAT_TOL = 1e-4

# Whether the current platform is the codegen-source platform.
# Currently Windows; this detection should be replaced with a marker
# file or env var if the codegen workflow ever supports multiple
# source platforms.
ON_CODEGEN_PLATFORM = sys.platform == "win32"

# 4D format constants (mirror python/chess_spectral/frame_4d.py)
HEADER_SIZE_4D = 256
ENCODING_DIM_4D = 45056
N_CHANNELS_4D = 11
CHANNEL_BLOCK_4D = ENCODING_DIM_4D // N_CHANNELS_4D  # 4096
FRAME_TAIL_BYTES = 14
FRAME_BYTES_4D = ENCODING_DIM_4D * 4 + FRAME_TAIL_BYTES

# 2D format constants (mirror python/chess_spectral/frame.py)
HEADER_SIZE_2D = 256
ENCODING_DIM_2D = 640
N_CHANNELS_2D = 10
CHANNEL_BLOCK_2D = ENCODING_DIM_2D // N_CHANNELS_2D  # 64
FRAME_BYTES_2D = ENCODING_DIM_2D * 4 + 8  # 4 (ply) + 4 (move metadata)


def _channel_energies(enc: np.ndarray, n_channels: int,
                      block: int) -> np.ndarray:
    """Per-channel sum-of-squares (basis-invariant). Returns shape
    (n_channels,)."""
    enc64 = enc.astype(np.float64)
    return np.array([
        float(np.sum(enc64[c * block:(c + 1) * block] ** 2))
        for c in range(n_channels)
    ])


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
    energy_tol: float = ENERGY_TOL,
    strict_float_tol: float = STRICT_FLOAT_TOL,
) -> None:
    """Assert two .spectral4 / .spectralz4 files agree under the
    cross-platform parity contract:

      1. Header bytes (256 B):              byte-for-byte equal.
      2. Per-frame metadata (14 B):         byte-for-byte equal.
      3. Per-frame channel energies:        numerically equal within
                                            `energy_tol` (basis-
                                            invariant; cross-platform).
      4. Per-frame raw encoding floats:     numerically equal within
                                            `strict_float_tol` BUT ONLY
                                            on the codegen-source
                                            platform (Windows).
                                            Skipped elsewhere.

    `gz=True` decompresses both files first (compares the underlying
    .spectral4 payload, ignoring gzip wrapper bytes).

    See module docstring for why we don't compare raw floats
    cross-platform.
    """
    a = _read_file(path_a, gz=gz)
    b = _read_file(path_b, gz=gz)
    assert len(a) == len(b), (
        f"size mismatch: {Path(path_a).name}={len(a)} "
        f"{Path(path_b).name}={len(b)}"
    )

    # 1. Header byte-equal (pure ints — must hold cross-platform).
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
        enc_a = np.frombuffer(a[frame_off:frame_off + enc_size],
                              dtype=np.float32)
        enc_b = np.frombuffer(b[frame_off:frame_off + enc_size],
                              dtype=np.float32)

        # 3. Channel energies (basis-invariant — works cross-platform).
        E_a = _channel_energies(enc_a, N_CHANNELS_4D, CHANNEL_BLOCK_4D)
        E_b = _channel_energies(enc_b, N_CHANNELS_4D, CHANNEL_BLOCK_4D)
        max_E_diff = float(np.abs(E_a - E_b).max())
        assert max_E_diff <= energy_tol, (
            f"ply {p} channel energies diverge by {max_E_diff:.3e} "
            f"(tol {energy_tol:.3e}). Energies are basis-invariant, "
            f"so this is a real encoder bug — NOT the known cross-"
            f"platform table-skew issue."
        )

        # 4. Raw float comparison: only meaningful on codegen-source
        # platform (Windows). On other platforms, Python and C may use
        # different orthonormal bases for degenerate fiber subspaces,
        # so per-element values can diverge by ~O(1) even though
        # energies match.
        if ON_CODEGEN_PLATFORM:
            max_diff = float(np.abs(enc_a.astype(np.float64)
                                    - enc_b.astype(np.float64)).max())
            assert max_diff <= strict_float_tol, (
                f"ply {p} encoding floats diverge by {max_diff:.3e} "
                f"(tol {strict_float_tol:.3e}) on the codegen-source "
                f"platform. Strict per-element parity should hold here."
            )

        # 2. Metadata byte-equal (pure ints — cross-platform).
        meta_off = frame_off + enc_size
        meta_a = a[meta_off:meta_off + FRAME_TAIL_BYTES]
        meta_b = b[meta_off:meta_off + FRAME_TAIL_BYTES]
        assert meta_a == meta_b, (
            f"ply {p} metadata bytes differ "
            f"(ply/from/to/promo/flags must match exactly)"
        )
