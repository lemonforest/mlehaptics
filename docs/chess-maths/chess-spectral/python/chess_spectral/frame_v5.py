"""v5 unified .spectral[z] / .spectralz4 wire format I/O.

v5 supersedes v2 (2D, .spectralz) and v4 (4D, .spectralz4) for new
writes; readers for the older versions stay forever for backward
compat with files already on disk. The unification is by way of two
new fields in the header that earlier versions implicitly carried:

    encoding_mode   uint8   0=dense, 1=per-channel, 2=XOR-stream
    n_dimensions    uint32  2 or 4 (was implicit per file extension)

A v5 reader auto-detects the dimension via the header's
``n_dimensions`` field and the frame body via ``encoding_mode``.

Header layout (256 bytes total, little-endian)::

    char[8]   magic           "LARTPSEC"  (unchanged from v2/v4)
    uint32    version         5
    uint32    encoding_dim    640 (2D) | 45056 (4D)
    uint32    frame_bytes     dense-equivalent frame size
    uint32    n_plies
    uint32    board_dim_side  8 (always)
    uint32    n_dimensions    2 or 4
    uint8     encoding_mode   0=dense, 1=per-channel, 2=XOR-stream
    uint8[223] reserved       zero-filled

Total = 8 + 6*4 + 1 + 223 = 256 bytes — slots into the existing
header geometry exactly.

PR-B scope (this module):
    * v5 header pack/unpack
    * Dense-mode (encoding_mode=0) frame I/O for both 2D and 4D
    * read_any() dispatcher: routes v2 → frame.py, v4 → frame_4d.py,
      v5-mode-0 → here.

PR-C scope (follow-up): mode 1 (per-channel replacement).
PR-D scope (follow-up): mode 2 (XOR-stream).
PR-E: C-side mirror.
PR-F: CLI wiring of ``--encoding={xor,channel,full}`` flags.

Reference: docs/adr/wire_format/ADR-001-v5-unified-encoding-modes.md
"""
from __future__ import annotations

import gzip
import io
import os
import struct
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterable, Iterator, List, Tuple

import numpy as np


# ─── Constants ──────────────────────────────────────────────────────

V5_MAGIC = b"LARTPSEC"
V5_VERSION = 5
V5_HEADER_SIZE = 256
V5_BOARD_SIDE = 8

# Encoding modes (header byte at offset 32)
MODE_DENSE = 0          # current v2/v4 frame body, just under v5 header
MODE_PER_CHANNEL = 1    # variable-size frames; only changed channels (PR-C)
MODE_XOR_STREAM = 2     # frame_N = stored[N] XOR frame_{N-1} (PR-D)
_ALL_MODES = (MODE_DENSE, MODE_PER_CHANNEL, MODE_XOR_STREAM)

# Per-dimension dense encoding sizes
_ENC_DIM_2D = 640
_ENC_DIM_4D = 45056
_FRAME_BYTES_2D = _ENC_DIM_2D * 4 + 8         # encoding + ply(4) + 4*u8 move
_FRAME_BYTES_4D = _ENC_DIM_4D * 4 + 14        # encoding + ply(4) + 8*u8 + 2

# Offsets within the 256-byte v5 header
_HDR_MAGIC_OFF = 0
_HDR_VERSION_OFF = 8
_HDR_ENCODING_DIM_OFF = 12
_HDR_FRAME_BYTES_OFF = 16
_HDR_N_PLIES_OFF = 20
_HDR_BOARD_SIDE_OFF = 24
_HDR_N_DIMENSIONS_OFF = 28
_HDR_ENCODING_MODE_OFF = 32

_HEADER_PACK = struct.Struct("<8sIIIIIIB")    # 8 + 6*4 + 1 = 33 bytes (rest is reserved)
assert _HEADER_PACK.size == 33


# ─── Header dataclass ───────────────────────────────────────────────


@dataclass
class HeaderV5:
    encoding_dim: int
    n_plies: int
    n_dimensions: int               # 2 or 4
    encoding_mode: int = MODE_DENSE
    frame_bytes: int = 0            # dense-equivalent frame body size; auto when 0
    board_dim_side: int = V5_BOARD_SIDE
    magic: bytes = V5_MAGIC
    version: int = V5_VERSION

    def __post_init__(self):
        if self.n_dimensions not in (2, 4):
            raise ValueError(f"n_dimensions must be 2 or 4, got {self.n_dimensions}")
        if self.encoding_mode not in _ALL_MODES:
            raise ValueError(
                f"encoding_mode must be one of {_ALL_MODES}, got {self.encoding_mode}"
            )
        if self.frame_bytes == 0:
            self.frame_bytes = (
                _FRAME_BYTES_2D if self.n_dimensions == 2 else _FRAME_BYTES_4D
            )
        # Sanity-check encoding_dim against n_dimensions
        expected = _ENC_DIM_2D if self.n_dimensions == 2 else _ENC_DIM_4D
        if self.encoding_dim != expected:
            raise ValueError(
                f"encoding_dim={self.encoding_dim} doesn't match "
                f"n_dimensions={self.n_dimensions} (expected {expected})"
            )

    def pack(self) -> bytes:
        buf = bytearray(V5_HEADER_SIZE)
        head = _HEADER_PACK.pack(
            self.magic, self.version, self.encoding_dim, self.frame_bytes,
            self.n_plies, self.board_dim_side, self.n_dimensions,
            self.encoding_mode,
        )
        buf[: len(head)] = head
        return bytes(buf)

    @classmethod
    def unpack(cls, buf: bytes) -> "HeaderV5":
        if len(buf) < V5_HEADER_SIZE:
            raise ValueError(
                f"v5 header: need {V5_HEADER_SIZE} bytes, got {len(buf)}"
            )
        magic, version, enc_dim, frame_bytes, n_plies, bdim, ndim, mode = (
            _HEADER_PACK.unpack(buf[: _HEADER_PACK.size])
        )
        if magic != V5_MAGIC:
            raise ValueError(f"v5 header: bad magic {magic!r}")
        if version != V5_VERSION:
            raise ValueError(
                f"v5 header: bad version {version} (expected {V5_VERSION}); "
                f"older v2/v4 files should be read via the legacy reader"
            )
        if mode not in _ALL_MODES:
            raise ValueError(f"v5 header: bad encoding_mode {mode}")
        return cls(
            encoding_dim=enc_dim, n_plies=n_plies, n_dimensions=ndim,
            encoding_mode=mode, frame_bytes=frame_bytes,
            board_dim_side=bdim,
        )


# ─── Dense-mode (mode 0) frame I/O — 2D ─────────────────────────────
#
# Layout: float32 encoding[640] + ply(u32) + move_from(u8) + move_to(u8)
#         + move_promo(u8) + move_flags(u8) = 2568 bytes
# Identical to v2 frame body. We re-pack it here under the v5 header.


_FRAME_2D_PACK = struct.Struct(f"<{_ENC_DIM_2D}fI4B")
assert _FRAME_2D_PACK.size == _FRAME_BYTES_2D


def pack_frame_2d_dense(encoding: np.ndarray, ply: int,
                        move_from: int, move_to: int,
                        move_promo: int, move_flags: int) -> bytes:
    if encoding.dtype != np.float32:
        encoding = encoding.astype(np.float32, copy=False)
    if encoding.shape != (_ENC_DIM_2D,):
        raise ValueError(
            f"2D encoding must have shape ({_ENC_DIM_2D},); got {encoding.shape}"
        )
    return _FRAME_2D_PACK.pack(
        *encoding.tolist(),
        int(ply) & 0xFFFFFFFF,
        int(move_from) & 0xFF, int(move_to) & 0xFF,
        int(move_promo) & 0xFF, int(move_flags) & 0xFF,
    )


def unpack_frame_2d_dense(buf: bytes) -> Tuple[np.ndarray, int, int, int, int, int]:
    if len(buf) != _FRAME_BYTES_2D:
        raise ValueError(
            f"2D dense frame: got {len(buf)} bytes, expected {_FRAME_BYTES_2D}"
        )
    vals = _FRAME_2D_PACK.unpack(buf)
    enc = np.asarray(vals[:_ENC_DIM_2D], dtype=np.float32)
    ply, mfrom, mto, mpromo, mflags = vals[_ENC_DIM_2D:]
    return enc, ply, mfrom, mto, mpromo, mflags


# ─── Dense-mode (mode 0) frame I/O — 4D ─────────────────────────────
#
# Layout: float32 encoding[45056] + ply(u32) + 4*u8 from + 4*u8 to
#         + promo(u8) + flags(u8) = 45056*4 + 14 = 180238 bytes
# Identical to v4 frame body.


def pack_frame_4d_dense(encoding: np.ndarray, ply: int,
                        from_sq: Tuple[int, int, int, int],
                        to_sq: Tuple[int, int, int, int],
                        promo: int, flags: int) -> bytes:
    if encoding.dtype != np.float32:
        encoding = encoding.astype(np.float32, copy=False)
    if encoding.shape != (_ENC_DIM_4D,):
        raise ValueError(
            f"4D encoding must have shape ({_ENC_DIM_4D},); got {encoding.shape}"
        )
    buf = bytearray(encoding.tobytes())
    buf.extend(struct.pack("<I", int(ply) & 0xFFFFFFFF))
    buf.extend(bytes([
        int(from_sq[0]) & 0xFF, int(from_sq[1]) & 0xFF,
        int(from_sq[2]) & 0xFF, int(from_sq[3]) & 0xFF,
        int(to_sq[0]) & 0xFF, int(to_sq[1]) & 0xFF,
        int(to_sq[2]) & 0xFF, int(to_sq[3]) & 0xFF,
        int(promo) & 0xFF, int(flags) & 0xFF,
    ]))
    return bytes(buf)


def unpack_frame_4d_dense(buf: bytes) -> Tuple[
    np.ndarray, int, Tuple[int, int, int, int], Tuple[int, int, int, int], int, int
]:
    if len(buf) != _FRAME_BYTES_4D:
        raise ValueError(
            f"4D dense frame: got {len(buf)} bytes, expected {_FRAME_BYTES_4D}"
        )
    enc = np.frombuffer(buf[: _ENC_DIM_4D * 4], dtype=np.float32).copy()
    off = _ENC_DIM_4D * 4
    (ply,) = struct.unpack_from("<I", buf, off)
    off += 4
    from_sq = (buf[off], buf[off + 1], buf[off + 2], buf[off + 3])
    off += 4
    to_sq = (buf[off], buf[off + 1], buf[off + 2], buf[off + 3])
    off += 4
    promo = buf[off]
    flags = buf[off + 1]
    return enc, ply, from_sq, to_sq, promo, flags


# ─── Transparent gzip read (mirrors frame.open_read_transparent) ────


def open_read_transparent(path: str | os.PathLike) -> BinaryIO:
    """Open a .spectral[z] / .spectralz4 file and return a BinaryIO that
    yields raw uncompressed bytes. Detects gzip magic (0x1F 0x8B) by
    peeking; otherwise returns the raw fp.
    """
    fp = open(path, "rb")
    magic = fp.read(2)
    fp.seek(0)
    if magic == b"\x1f\x8b":
        with gzip.GzipFile(fileobj=fp, mode="rb") as gz:
            tmp = tempfile.TemporaryFile(mode="w+b")
            while True:
                chunk = gz.read(1 << 20)
                if not chunk:
                    break
                tmp.write(chunk)
        fp.close()
        tmp.seek(0)
        return tmp
    return fp


# ─── Version-dispatching reader ─────────────────────────────────────


def peek_version(path: str | os.PathLike) -> int:
    """Read just the first 12 bytes of `path` (transparently
    decompressing gzip if present) and return the version field. Raises
    ValueError on bad magic.
    """
    fp = open_read_transparent(path)
    try:
        head = fp.read(12)
    finally:
        fp.close()
    if len(head) < 12:
        raise ValueError(f"truncated header: only {len(head)} bytes")
    magic = head[:8]
    if magic != V5_MAGIC:
        raise ValueError(f"bad magic: {magic!r}")
    (version,) = struct.unpack_from("<I", head, 8)
    return version


def read_v5_header(fp: BinaryIO) -> HeaderV5:
    buf = fp.read(V5_HEADER_SIZE)
    if len(buf) != V5_HEADER_SIZE:
        raise IOError(f"truncated v5 header: got {len(buf)} of {V5_HEADER_SIZE}")
    return HeaderV5.unpack(buf)


def iter_v5_frames_dense(fp: BinaryIO, hdr: HeaderV5) -> Iterator[bytes]:
    """Yield raw frame bytes (n_plies of them) for a v5 dense file.
    The caller decides how to decode (use ``unpack_frame_2d_dense`` or
    ``unpack_frame_4d_dense`` based on ``hdr.n_dimensions``)."""
    if hdr.encoding_mode != MODE_DENSE:
        raise ValueError(
            f"iter_v5_frames_dense expects encoding_mode=0; got {hdr.encoding_mode}"
        )
    fb = hdr.frame_bytes
    for _ in range(hdr.n_plies):
        chunk = fp.read(fb)
        if len(chunk) != fb:
            raise IOError(
                f"truncated v5 frame: got {len(chunk)} of {fb} bytes"
            )
        yield chunk


# ─── Writer (mode 0 only, PR-B scope) ──────────────────────────────


def write_v5_dense_2d(
    path: str | os.PathLike,
    frames: Iterable[Tuple[np.ndarray, int, int, int, int, int]],
    *,
    compress: bool = False,
) -> int:
    """Write a v5 .spectralz file (2D) in dense mode (encoding_mode=0).

    `frames` yields ``(encoding, ply, move_from, move_to, move_promo,
    move_flags)`` tuples.

    Produces the same frame body as v2 ``frame.write_file()`` but with
    a v5 header (version=5, n_dimensions=2, encoding_mode=0). Equivalent
    to ``--encoding=full`` on the eventual v5 CLI.

    Returns the number of frames written.
    """
    return _write_v5_dense_common(
        path, frames, n_dimensions=2,
        pack_fn=lambda f: pack_frame_2d_dense(*f),
        compress=compress,
    )


def write_v5_dense_4d(
    path: str | os.PathLike,
    frames: Iterable[Tuple[
        np.ndarray, int, Tuple[int, int, int, int],
        Tuple[int, int, int, int], int, int,
    ]],
    *,
    compress: bool = False,
) -> int:
    """Write a v5 .spectralz4 file (4D) in dense mode. See
    ``write_v5_dense_2d`` for shape/semantics; the only differences
    are the 4D encoding length (45056) and the move-coordinate width
    (4×u8 per from/to)."""
    return _write_v5_dense_common(
        path, frames, n_dimensions=4,
        pack_fn=lambda f: pack_frame_4d_dense(*f),
        compress=compress,
    )


def _write_v5_dense_common(
    path: str | os.PathLike,
    frames: Iterable,
    *,
    n_dimensions: int,
    pack_fn,
    compress: bool,
) -> int:
    encoding_dim = _ENC_DIM_2D if n_dimensions == 2 else _ENC_DIM_4D

    tmp_fd, tmp_path = tempfile.mkstemp(prefix="csv_v5_", suffix=".tmp")
    os.close(tmp_fd)
    count = 0
    try:
        with open(tmp_path, "wb") as out:
            # Placeholder header; backfill n_plies after counting.
            out.write(HeaderV5(
                encoding_dim=encoding_dim, n_plies=0,
                n_dimensions=n_dimensions, encoding_mode=MODE_DENSE,
            ).pack())
            for fr in frames:
                out.write(pack_fn(fr))
                count += 1
            # Backfill n_plies in the header.
            out.seek(0)
            out.write(HeaderV5(
                encoding_dim=encoding_dim, n_plies=count,
                n_dimensions=n_dimensions, encoding_mode=MODE_DENSE,
            ).pack())

        if compress:
            with open(tmp_path, "rb") as src, \
                 open(path, "wb") as raw, \
                 gzip.GzipFile(filename="", fileobj=raw,
                               mode="wb", compresslevel=6, mtime=0) as dst:
                while True:
                    chunk = src.read(1 << 20)
                    if not chunk:
                        break
                    dst.write(chunk)
        else:
            os.replace(tmp_path, path)
            tmp_path = None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
    return count


__all__ = [
    "V5_MAGIC", "V5_VERSION", "V5_HEADER_SIZE",
    "MODE_DENSE", "MODE_PER_CHANNEL", "MODE_XOR_STREAM",
    "HeaderV5",
    "pack_frame_2d_dense", "unpack_frame_2d_dense",
    "pack_frame_4d_dense", "unpack_frame_4d_dense",
    "open_read_transparent", "peek_version",
    "read_v5_header", "iter_v5_frames_dense",
    "write_v5_dense_2d", "write_v5_dense_4d",
]
