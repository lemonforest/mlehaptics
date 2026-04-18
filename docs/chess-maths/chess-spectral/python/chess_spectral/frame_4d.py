"""spectralz v3 frame format (4D encoder output container).

Header layout (256 bytes, little-endian):
    uint64 magic           "LARTPSEC" (= bytes b'LARTPSEC'; same as v2)
    uint32 version         3
    uint32 encoding_dim    40960 for v1 4D encoder
    uint32 frame_bytes     encoding_dim * 4 + 14
    uint32 n_plies         number of frames that follow
    uint32 board_dim_side  8
    uint32 n_dimensions    4
    uint8  pad[224]        zero-filled

Frame layout (encoding_dim * 4 + 14 bytes):
    float32 encoding[encoding_dim]
    uint32 ply
    uint8  from_x, from_y, from_z, from_w
    uint8  to_x, to_y, to_z, to_w
    uint8  promo
    uint8  flags

The 2D encoder already uses "LARTPSEC" with version=2 (see
[frame.py]); we keep the magic but bump the version so readers can
dispatch.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterable, List, Tuple

import numpy as np


SPECTRALZ_V3_MAGIC = b"LARTPSEC"
SPECTRALZ_VERSION = 3
HEADER_SIZE = 256
BOARD_SIDE = 8
N_DIMENSIONS = 4
ENCODING_DIM_4D = 40960       # 10 channels x 4096 eigenmodes
FRAME_TAIL_BYTES = 14         # ply(4) + from(4) + to(4) + promo(1) + flags(1)

Coord4 = Tuple[int, int, int, int]


@dataclass
class Header4D:
    magic: bytes
    version: int
    encoding_dim: int
    frame_bytes: int
    n_plies: int
    board_dim_side: int
    n_dimensions: int


@dataclass
class Frame4D:
    encoding: np.ndarray        # float32, shape (encoding_dim,)
    ply: int                    # uint32
    from_sq: Coord4             # four uint8
    to_sq: Coord4               # four uint8
    promo: int                  # uint8
    flags: int                  # uint8


def pack_header(encoding_dim: int, frame_bytes: int, n_plies: int
                ) -> bytes:
    """Return the 256-byte v3 header bytes. Pad is zeroed."""
    buf = bytearray(HEADER_SIZE)
    buf[0:8] = SPECTRALZ_V3_MAGIC
    struct.pack_into(
        "<IIIIII", buf, 8,
        SPECTRALZ_VERSION,
        encoding_dim,
        frame_bytes,
        n_plies,
        BOARD_SIDE,
        N_DIMENSIONS,
    )
    return bytes(buf)


def unpack_header(data: bytes) -> Header4D:
    if len(data) < HEADER_SIZE:
        raise ValueError(
            f"header: need {HEADER_SIZE} bytes, got {len(data)}"
        )
    magic = bytes(data[0:8])
    if magic != SPECTRALZ_V3_MAGIC:
        raise ValueError(f"bad magic: {magic!r}")
    version, enc_dim, frame_bytes, n_plies, bdim, ndim = struct.unpack_from(
        "<IIIIII", data, 8
    )
    return Header4D(
        magic=magic, version=version,
        encoding_dim=enc_dim, frame_bytes=frame_bytes,
        n_plies=n_plies, board_dim_side=bdim,
        n_dimensions=ndim,
    )


def pack_frame(enc: np.ndarray, ply: int,
               from_sq: Coord4, to_sq: Coord4,
               promo: int, flags: int) -> bytes:
    """Pack a single frame. `enc` must be float32 with length encoding_dim."""
    if enc.dtype != np.float32:
        raise TypeError(f"encoding must be float32, got {enc.dtype}")
    if enc.shape != (ENCODING_DIM_4D,):
        raise ValueError(
            f"encoding shape {enc.shape}, expected ({ENCODING_DIM_4D},)"
        )
    buf = bytearray(enc.tobytes())
    buf.extend(struct.pack("<I", int(ply) & 0xFFFFFFFF))
    buf.extend(bytes([
        int(from_sq[0]) & 0xFF, int(from_sq[1]) & 0xFF,
        int(from_sq[2]) & 0xFF, int(from_sq[3]) & 0xFF,
        int(to_sq[0]) & 0xFF, int(to_sq[1]) & 0xFF,
        int(to_sq[2]) & 0xFF, int(to_sq[3]) & 0xFF,
        int(promo) & 0xFF, int(flags) & 0xFF,
    ]))
    return bytes(buf)


def unpack_frame(data: bytes, encoding_dim: int = ENCODING_DIM_4D
                 ) -> Frame4D:
    want = encoding_dim * 4 + FRAME_TAIL_BYTES
    if len(data) != want:
        raise ValueError(f"frame: got {len(data)} bytes, expected {want}")
    enc = np.frombuffer(data[:encoding_dim * 4], dtype=np.float32).copy()
    off = encoding_dim * 4
    (ply,) = struct.unpack_from("<I", data, off)
    off += 4
    from_sq = (data[off], data[off + 1], data[off + 2], data[off + 3])
    off += 4
    to_sq = (data[off], data[off + 1], data[off + 2], data[off + 3])
    off += 4
    promo = data[off]
    flags = data[off + 1]
    return Frame4D(
        encoding=enc, ply=ply,
        from_sq=from_sq, to_sq=to_sq,
        promo=promo, flags=flags,
    )


def write_spectralz_v3(path: str | Path,
                       frames: Iterable[Frame4D],
                       encoding_dim: int = ENCODING_DIM_4D) -> int:
    """Write a list of Frame4D objects to `path` with v3 header. Returns
    total bytes written."""
    frames = list(frames)
    frame_bytes = encoding_dim * 4 + FRAME_TAIL_BYTES
    total = HEADER_SIZE + frame_bytes * len(frames)
    with open(path, "wb") as f:
        f.write(pack_header(encoding_dim, frame_bytes, len(frames)))
        for fr in frames:
            f.write(pack_frame(
                fr.encoding, fr.ply, fr.from_sq, fr.to_sq,
                fr.promo, fr.flags,
            ))
    return total


def read_spectralz_v3(path: str | Path) -> Tuple[Header4D, List[Frame4D]]:
    """Read a v3 file and return (header, frames)."""
    with open(path, "rb") as f:
        data = f.read()
    header = unpack_header(data[:HEADER_SIZE])
    if header.version != SPECTRALZ_VERSION:
        raise ValueError(
            f"version mismatch: file is v{header.version}, reader is v3"
        )
    frames: List[Frame4D] = []
    off = HEADER_SIZE
    for _ in range(header.n_plies):
        frames.append(unpack_frame(
            data[off:off + header.frame_bytes], header.encoding_dim
        ))
        off += header.frame_bytes
    return header, frames


def read_header_any(fp: BinaryIO):
    """Dispatch shim for 2D+4D coexistence. Peek the magic+version from
    a file handle, rewind, and return either a v2 Header (from frame.py)
    or a v3 Header4D. The 2D reader's existing callers keep working --
    this function is what changes when the 2D frame module gets its
    dispatch edit.

    Returns one of:
      Header4D, "v3"
      <opaque v2 header>, "v2"
    """
    peek = fp.read(16)
    fp.seek(0)
    if len(peek) < 16:
        raise ValueError("short read on header peek")
    magic = peek[0:8]
    if magic != SPECTRALZ_V3_MAGIC:
        raise ValueError(f"unknown magic: {magic!r}")
    version = int.from_bytes(peek[8:12], "little")
    if version == 3:
        raw = fp.read(HEADER_SIZE)
        return unpack_header(raw), "v3"
    # v2 (or older): defer to chess_spectral.frame.read_header
    from chess_spectral import frame as frame2d
    hdr = frame2d.read_header(fp)
    return hdr, "v2"
