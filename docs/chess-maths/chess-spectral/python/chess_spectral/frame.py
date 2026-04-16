"""
v2 .spectral binary format I/O.

File layout (matches cs_frame.h):

    Header : 256 B
        magic        u64   = 0x434553505452414C ("LARTPSEC" little-endian)
        version      u32   = 2
        encoding_dim u32   = 640
        frame_bytes  u32   = 2568
        n_plies      u32
        _pad[232]    bytes

    Frame  : 2568 B (× n_plies)
        encoding[640] f32 (little-endian)
        ply           u32
        move_from     u8
        move_to       u8
        move_promo    u8
        move_flags    u8

Transparent gzip: a `.spectralz` file is just gzip(.spectral). The
reader peeks the first two bytes; if 0x1F 0x8B, it decompresses into a
temp file and reads from that. No format change.
"""
from __future__ import annotations

import gzip
import io
import os
import struct
import tempfile
from dataclasses import dataclass, field
from typing import BinaryIO, Iterable, Iterator

import numpy as np

FILE_MAGIC   = 0x434553505452414C
FILE_VERSION = 2
ENCODING_DIM = 640
FRAME_BYTES  = 2568
HEADER_BYTES = 256
FRAME_PAD    = 232  # header reserved bytes

_HEADER_STRUCT = struct.Struct("<QIIII232s")      # 256 B
assert _HEADER_STRUCT.size == HEADER_BYTES
_FRAME_STRUCT  = struct.Struct(f"<{ENCODING_DIM}fI4B")  # 2568 B
assert _FRAME_STRUCT.size == FRAME_BYTES


@dataclass
class Frame:
    """One ply's encoding + minimal move metadata. `encoding` is always
    a float32 numpy array of length 640 so round-trip byte equality is
    preserved with the C writer."""
    encoding: np.ndarray
    ply: int = 0
    move_from: int = 0xFF
    move_to: int = 0xFF
    move_promo: int = 0
    move_flags: int = 0

    def __post_init__(self):
        arr = np.asarray(self.encoding)
        if arr.shape != (ENCODING_DIM,):
            raise ValueError(f"encoding must be shape ({ENCODING_DIM},); got {arr.shape}")
        self.encoding = arr.astype(np.float32, copy=False)


@dataclass
class Header:
    n_plies: int = 0
    magic: int = FILE_MAGIC
    version: int = FILE_VERSION
    encoding_dim: int = ENCODING_DIM
    frame_bytes: int = FRAME_BYTES

    def pack(self) -> bytes:
        return _HEADER_STRUCT.pack(
            self.magic, self.version, self.encoding_dim,
            self.frame_bytes, self.n_plies, b"\x00" * FRAME_PAD,
        )

    @classmethod
    def unpack(cls, buf: bytes) -> "Header":
        if len(buf) != HEADER_BYTES:
            raise ValueError(f"header buffer must be {HEADER_BYTES} B; got {len(buf)}")
        magic, version, enc_dim, frame_bytes, n_plies, _pad = _HEADER_STRUCT.unpack(buf)
        if magic != FILE_MAGIC:
            raise ValueError(f"bad magic: 0x{magic:016x}")
        if version != FILE_VERSION:
            raise ValueError(f"unsupported version: {version}")
        if enc_dim != ENCODING_DIM:
            raise ValueError(f"encoding_dim mismatch: file={enc_dim} expected={ENCODING_DIM}")
        if frame_bytes != FRAME_BYTES:
            raise ValueError(f"frame_bytes mismatch: file={frame_bytes} expected={FRAME_BYTES}")
        return cls(n_plies=n_plies)


# ─── Low-level frame pack/unpack ────────────────────────────────────────

def _pack_frame(fr: Frame) -> bytes:
    return _FRAME_STRUCT.pack(
        *fr.encoding.tolist(),
        int(fr.ply),
        int(fr.move_from) & 0xFF,
        int(fr.move_to)   & 0xFF,
        int(fr.move_promo) & 0xFF,
        int(fr.move_flags) & 0xFF,
    )


def _unpack_frame(buf: bytes) -> Frame:
    vals = _FRAME_STRUCT.unpack(buf)
    enc = np.asarray(vals[:ENCODING_DIM], dtype=np.float32)
    ply, mfrom, mto, mpromo, mflags = vals[ENCODING_DIM:]
    return Frame(
        encoding=enc, ply=ply,
        move_from=mfrom, move_to=mto,
        move_promo=mpromo, move_flags=mflags,
    )


# ─── Transparent gzip read ──────────────────────────────────────────────

def open_read_transparent(path: str | os.PathLike) -> BinaryIO:
    """Open a .spectral or .spectralz file and return a BinaryIO that
    yields the raw (uncompressed) bytes. Caller is responsible for
    closing. Peeks the first two bytes to detect gzip magic (0x1F 0x8B);
    otherwise returns the raw file pointer.

    For gzipped input the whole stream is decompressed to a spooled
    tempfile so random-access fseek still works.
    """
    fp = open(path, "rb")
    magic = fp.read(2)
    fp.seek(0)
    if magic == b"\x1f\x8b":
        # Slurp-and-decompress; return a tempfile so downstream code can
        # seek freely (random frame access).
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


# ─── Streaming reader / writer ──────────────────────────────────────────

def read_header(fp: BinaryIO) -> Header:
    buf = fp.read(HEADER_BYTES)
    if len(buf) != HEADER_BYTES:
        raise IOError("truncated header")
    return Header.unpack(buf)


def read_frame(fp: BinaryIO) -> Frame:
    buf = fp.read(FRAME_BYTES)
    if len(buf) != FRAME_BYTES:
        raise IOError("truncated frame")
    return _unpack_frame(buf)


def iter_frames(fp: BinaryIO, n_plies: int) -> Iterator[Frame]:
    """Yield n_plies frames from fp (already positioned after header)."""
    for _ in range(n_plies):
        yield read_frame(fp)


def seek_frame(fp: BinaryIO, ply: int) -> None:
    """Position fp at the start of the given ply's frame (0-indexed)."""
    fp.seek(HEADER_BYTES + ply * FRAME_BYTES, 0)


def read_all(path: str | os.PathLike) -> tuple[Header, list[Frame]]:
    """Convenience: open (transparent gzip), read everything, close.
    Returns (header, list[Frame])."""
    fp = open_read_transparent(path)
    try:
        hdr = read_header(fp)
        frames = list(iter_frames(fp, hdr.n_plies))
        return hdr, frames
    finally:
        fp.close()


def read_encodings(path: str | os.PathLike) -> tuple[Header, np.ndarray]:
    """Even more convenient for analysis: return (header, stacked
    float32 array of shape (n_plies, 640))."""
    hdr, frames = read_all(path)
    if not frames:
        return hdr, np.zeros((0, ENCODING_DIM), dtype=np.float32)
    arr = np.stack([fr.encoding for fr in frames], axis=0)
    return hdr, arr


# ─── Writer ─────────────────────────────────────────────────────────────

def write_file(
    path: str | os.PathLike,
    frames: Iterable[Frame],
    *,
    compress: bool = False,
) -> int:
    """Write `frames` to `path`. When compress=True, the output is
    gzipped in-place — no separate `.spectralz` suffix is enforced
    (caller picks the name). Returns n_plies written.

    Implementation: write uncompressed to a tempfile so we can backfill
    n_plies in the header after counting. Then either rename to path or
    compress into path.
    """
    tmp_fd, tmp_path = tempfile.mkstemp(prefix="csv_spectral_", suffix=".tmp")
    os.close(tmp_fd)
    count = 0
    try:
        with open(tmp_path, "wb") as out:
            # Placeholder header; we backfill n_plies after counting.
            out.write(Header(n_plies=0).pack())
            for fr in frames:
                out.write(_pack_frame(fr))
                count += 1
            # Backfill n_plies.
            out.seek(0)
            out.write(Header(n_plies=count).pack())

        if compress:
            # gzip.open() doesn't accept mtime; use GzipFile directly so
            # we can zero the timestamp (deterministic output → stable
            # hashes, reproducible builds).
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
            # Move into place (handles Windows same-drive rename).
            os.replace(tmp_path, path)
            tmp_path = None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
    return count
