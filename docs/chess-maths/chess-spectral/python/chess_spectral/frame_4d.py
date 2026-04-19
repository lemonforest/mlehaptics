"""spectralz v3 / v4 frame format (4D encoder output container).

Header layout (256 bytes, little-endian), identical across v3 and v4:
    uint64 magic           "LARTPSEC" (= bytes b'LARTPSEC'; same as v2)
    uint32 version         3 (v1.0 encoder) or 4 (v1.1.1 encoder)
    uint32 encoding_dim    40960 for v3; 45056 for v4 (11 channels)
    uint32 frame_bytes     encoding_dim * 4 + 14
    uint32 n_plies         number of frames that follow
    uint32 board_dim_side  8
    uint32 n_dimensions    4
    uint8  pad[224]        zero-filled

Frame layout (encoding_dim * 4 + 14 bytes, identical across v3/v4):
    float32 encoding[encoding_dim]
    uint32 ply
    uint8  from_x, from_y, from_z, from_w
    uint8  to_x, to_y, to_z, to_w
    uint8  promo
    uint8  flags

v1.1.1 bumps version 3 -> 4 because `encoding_dim` changes with the
pawn antisymmetric channel split (one W-axis + one Y-axis). The 2D
encoder uses the same magic at version=2; readers should dispatch on
the version field via `read_header_any`.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterable, List, Tuple

import numpy as np


SPECTRALZ_MAGIC = b"LARTPSEC"
SPECTRALZ_V3_MAGIC = SPECTRALZ_MAGIC         # retained: same magic across versions
SPECTRALZ_VERSION = 4                        # current (v1.1.1)
SPECTRALZ_VERSION_V3 = 3                     # legacy (v1.0)
HEADER_SIZE = 256
BOARD_SIDE = 8
N_DIMENSIONS = 4
ENCODING_DIM_4D = 45056       # 11 channels x 4096 eigenmodes (v1.1.1)
ENCODING_DIM_4D_V3 = 40960    # 10 channels x 4096 eigenmodes (v1.0, legacy)
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


def _pack_header_with_version(version: int, encoding_dim: int,
                              frame_bytes: int, n_plies: int) -> bytes:
    buf = bytearray(HEADER_SIZE)
    buf[0:8] = SPECTRALZ_MAGIC
    struct.pack_into(
        "<IIIIII", buf, 8,
        version,
        encoding_dim,
        frame_bytes,
        n_plies,
        BOARD_SIDE,
        N_DIMENSIONS,
    )
    return bytes(buf)


def pack_header(encoding_dim: int, frame_bytes: int, n_plies: int
                ) -> bytes:
    """Return the 256-byte v4 header bytes. Pad is zeroed."""
    return _pack_header_with_version(
        SPECTRALZ_VERSION, encoding_dim, frame_bytes, n_plies,
    )


def pack_header_v3(encoding_dim: int, frame_bytes: int, n_plies: int
                   ) -> bytes:
    """Return a 256-byte legacy v3 header. Kept for backward-compat
    test fixtures; new writes should use `pack_header`."""
    return _pack_header_with_version(
        SPECTRALZ_VERSION_V3, encoding_dim, frame_bytes, n_plies,
    )


def unpack_header(data: bytes) -> Header4D:
    if len(data) < HEADER_SIZE:
        raise ValueError(
            f"header: need {HEADER_SIZE} bytes, got {len(data)}"
        )
    magic = bytes(data[0:8])
    if magic != SPECTRALZ_MAGIC:
        raise ValueError(f"bad magic: {magic!r}")
    version, enc_dim, frame_bytes, n_plies, bdim, ndim = struct.unpack_from(
        "<IIIIII", data, 8
    )
    if version not in (SPECTRALZ_VERSION_V3, SPECTRALZ_VERSION):
        raise ValueError(
            f"unsupported spectralz version: {version} "
            f"(expected {SPECTRALZ_VERSION_V3} or {SPECTRALZ_VERSION})"
        )
    return Header4D(
        magic=magic, version=version,
        encoding_dim=enc_dim, frame_bytes=frame_bytes,
        n_plies=n_plies, board_dim_side=bdim,
        n_dimensions=ndim,
    )


def pack_frame(enc: np.ndarray, ply: int,
               from_sq: Coord4, to_sq: Coord4,
               promo: int, flags: int,
               encoding_dim: int = ENCODING_DIM_4D) -> bytes:
    """Pack a single frame. `enc` must be float32 with length
    `encoding_dim`. Default encoding_dim is the v4 value (45056);
    callers writing legacy v3 frames must pass ENCODING_DIM_4D_V3."""
    if enc.dtype != np.float32:
        raise TypeError(f"encoding must be float32, got {enc.dtype}")
    if enc.shape != (encoding_dim,):
        raise ValueError(
            f"encoding shape {enc.shape}, expected ({encoding_dim},)"
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


def write_spectralz_v4(path: str | Path,
                       frames: Iterable[Frame4D],
                       encoding_dim: int = ENCODING_DIM_4D) -> int:
    """Write a list of Frame4D objects to `path` with a v4 header.
    Returns total bytes written."""
    frames = list(frames)
    frame_bytes = encoding_dim * 4 + FRAME_TAIL_BYTES
    total = HEADER_SIZE + frame_bytes * len(frames)
    with open(path, "wb") as f:
        f.write(pack_header(encoding_dim, frame_bytes, len(frames)))
        for fr in frames:
            f.write(pack_frame(
                fr.encoding, fr.ply, fr.from_sq, fr.to_sq,
                fr.promo, fr.flags, encoding_dim=encoding_dim,
            ))
    return total


def write_spectralz_v3(path: str | Path,
                       frames: Iterable[Frame4D],
                       encoding_dim: int = ENCODING_DIM_4D_V3) -> int:
    """Write a legacy v3 file. Retained so fixtures / tests can still
    produce v3 blobs for backward-read verification. Default
    encoding_dim is the v3 value (40960)."""
    frames = list(frames)
    frame_bytes = encoding_dim * 4 + FRAME_TAIL_BYTES
    total = HEADER_SIZE + frame_bytes * len(frames)
    with open(path, "wb") as f:
        f.write(pack_header_v3(encoding_dim, frame_bytes, len(frames)))
        for fr in frames:
            f.write(pack_frame(
                fr.encoding, fr.ply, fr.from_sq, fr.to_sq,
                fr.promo, fr.flags, encoding_dim=encoding_dim,
            ))
    return total


def _read_frames(data: bytes, header: Header4D) -> List[Frame4D]:
    frames: List[Frame4D] = []
    off = HEADER_SIZE
    for _ in range(header.n_plies):
        frames.append(unpack_frame(
            data[off:off + header.frame_bytes], header.encoding_dim
        ))
        off += header.frame_bytes
    return frames


def read_spectralz_v4(path: str | Path) -> Tuple[Header4D, List[Frame4D]]:
    """Read a v4 file and return (header, frames)."""
    with open(path, "rb") as f:
        data = f.read()
    header = unpack_header(data[:HEADER_SIZE])
    if header.version != SPECTRALZ_VERSION:
        raise ValueError(
            f"version mismatch: file is v{header.version}, reader is v4"
        )
    return header, _read_frames(data, header)


def read_spectralz_v3(path: str | Path) -> Tuple[Header4D, List[Frame4D]]:
    """Read a legacy v3 file and return (header, frames). Retained for
    backward-compat; prefer `read_spectralz_v4` or `read_header_any`
    for new writes."""
    with open(path, "rb") as f:
        data = f.read()
    header = unpack_header(data[:HEADER_SIZE])
    if header.version != SPECTRALZ_VERSION_V3:
        raise ValueError(
            f"version mismatch: file is v{header.version}, reader is v3"
        )
    return header, _read_frames(data, header)


def read_header_any(fp: BinaryIO):
    """Dispatch shim for 2D+4D coexistence. Peek the magic+version from
    a file handle, rewind, and return either a v2 Header (from
    frame.py) or a v3 / v4 Header4D.

    Returns one of:
      Header4D, "v4"
      Header4D, "v3"
      <opaque v2 header>, "v2"
    """
    peek = fp.read(16)
    fp.seek(0)
    if len(peek) < 16:
        raise ValueError("short read on header peek")
    magic = peek[0:8]
    if magic != SPECTRALZ_MAGIC:
        raise ValueError(f"unknown magic: {magic!r}")
    version = int.from_bytes(peek[8:12], "little")
    if version == SPECTRALZ_VERSION:
        raw = fp.read(HEADER_SIZE)
        return unpack_header(raw), "v4"
    if version == SPECTRALZ_VERSION_V3:
        raw = fp.read(HEADER_SIZE)
        return unpack_header(raw), "v3"
    # v2 (or older): defer to chess_spectral.frame.read_header
    from chess_spectral import frame as frame2d
    hdr = frame2d.read_header(fp)
    return hdr, "v2"
