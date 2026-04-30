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

# Per-dimension channel layout (for mode 1 = per-channel replacement)
_N_CHANNELS_2D = 10                            # see qm_2d._H_CHANNELS
_N_CHANNELS_4D = 11                            # see encoder_4d._CHANNEL_NAMES
_CHANNEL_DIM_2D = _ENC_DIM_2D // _N_CHANNELS_2D    # 64
_CHANNEL_DIM_4D = _ENC_DIM_4D // _N_CHANNELS_4D    # 4096

# Move-metadata tail sizes (same across modes 0 / 1 / 2)
_MOVE_TAIL_2D = 8                              # ply(4) + 4*u8
_MOVE_TAIL_4D = 14                             # ply(4) + 8*u8 + 2

# Per-channel mode flags (single u8; bit 0 = full-frame independent flag)
PC_FLAG_FULL = 0x01

# Per-channel header is u32 body_size + u8 flags + u8 n_channels = 6 bytes
_PC_HEADER_PACK = struct.Struct("<IBB")
assert _PC_HEADER_PACK.size == 6
# Per-channel block prefix: u8 channel_idx + u8 reserved = 2 bytes
_PC_BLOCK_PREFIX_PACK = struct.Struct("<BB")
assert _PC_BLOCK_PREFIX_PACK.size == 2

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


# NOTE: We intentionally do NOT use a struct.Struct(f"<{640}fI4B") packer
# for the encoding part. struct's "f" format goes through Python float
# (float64) on pack and unpack, which silently normalizes NaN bit
# patterns. XOR-streamed (mode 2) frames can produce NaN-like bit
# patterns as legitimate stored payload — those must round-trip
# bit-exactly. We therefore use ``ndarray.tobytes()`` (byte copy) for
# pack and ``np.frombuffer(..., dtype=np.float32).copy()`` for unpack,
# both of which preserve all 2^32 bit patterns including NaNs.
_MOVE_TAIL_2D_PACK = struct.Struct("<I4B")
assert _MOVE_TAIL_2D_PACK.size == _MOVE_TAIL_2D


def pack_frame_2d_dense(encoding: np.ndarray, ply: int,
                        move_from: int, move_to: int,
                        move_promo: int, move_flags: int) -> bytes:
    if encoding.dtype != np.float32:
        encoding = encoding.astype(np.float32, copy=False)
    if encoding.shape != (_ENC_DIM_2D,):
        raise ValueError(
            f"2D encoding must have shape ({_ENC_DIM_2D},); got {encoding.shape}"
        )
    enc_bytes = encoding.tobytes()         # bit-exact float32 bytes
    tail = _MOVE_TAIL_2D_PACK.pack(
        int(ply) & 0xFFFFFFFF,
        int(move_from) & 0xFF, int(move_to) & 0xFF,
        int(move_promo) & 0xFF, int(move_flags) & 0xFF,
    )
    return enc_bytes + tail


def unpack_frame_2d_dense(buf: bytes) -> Tuple[np.ndarray, int, int, int, int, int]:
    if len(buf) != _FRAME_BYTES_2D:
        raise ValueError(
            f"2D dense frame: got {len(buf)} bytes, expected {_FRAME_BYTES_2D}"
        )
    enc = np.frombuffer(buf[: _ENC_DIM_2D * 4], dtype=np.float32).copy()
    ply, mfrom, mto, mpromo, mflags = _MOVE_TAIL_2D_PACK.unpack(
        buf[_ENC_DIM_2D * 4 :]
    )
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


# ─── Mode 1: per-channel replacement (PR-C scope) ───────────────────
#
# The per-channel encoder writes only the channels that changed since
# the previous frame (or, in `full` flag mode, the entire frame as an
# independent block). Wins on workloads where most channels are stable
# across plies — the empirical chess spike measured 4D 2.84x compression
# vs dense gzipped on a 50-ply knight-tour fixture.
#
# Body layout per ply::
#
#     u32 body_size_bytes        // length of this body (excluding own size field)
#     u8  flags                  // bit 0 (PC_FLAG_FULL): independent frame
#     u8  n_channels_present     // 0..N_channels
#     [u8 channel_idx, u8 reserved, float32 buffer[channel_dim]]
#         × n_channels_present
#     <move-metadata tail>       // 8 B (2D) or 14 B (4D); same as mode 0


def _pack_channels_block(channels: List[Tuple[int, np.ndarray]],
                         channel_dim: int) -> bytes:
    """Pack a sequence of (channel_idx, channel_buffer) blocks. Each
    block is u8 idx + u8 reserved + float32 buffer[channel_dim]."""
    parts: List[bytes] = []
    for idx, buf in channels:
        if not 0 <= idx <= 255:
            raise ValueError(f"channel index {idx} out of u8 range")
        if buf.dtype != np.float32:
            buf = buf.astype(np.float32, copy=False)
        if buf.shape != (channel_dim,):
            raise ValueError(
                f"channel {idx}: shape {buf.shape}, expected ({channel_dim},)"
            )
        parts.append(_PC_BLOCK_PREFIX_PACK.pack(idx, 0))
        parts.append(buf.tobytes())
    return b"".join(parts)


def _channels_diff(prev: np.ndarray, curr: np.ndarray, channel_dim: int
                   ) -> List[Tuple[int, np.ndarray]]:
    """Return (channel_idx, channel_buffer) for every channel where
    ``curr`` differs from ``prev``. Both arrays must be flat with length
    n_channels * channel_dim. Comparison is bit-exact (np.array_equal on
    float32 reinterpretations) so reconstruction is lossless."""
    if prev.shape != curr.shape:
        raise ValueError(f"shape mismatch: prev={prev.shape} curr={curr.shape}")
    n = curr.shape[0] // channel_dim
    p2 = prev.reshape(n, channel_dim)
    c2 = curr.reshape(n, channel_dim)
    out: List[Tuple[int, np.ndarray]] = []
    for i in range(n):
        if not np.array_equal(p2[i].view(np.uint32), c2[i].view(np.uint32)):
            out.append((i, c2[i].copy()))
    return out


def pack_frame_per_channel(
    encoding: np.ndarray,
    move_tail: bytes,
    *,
    channel_dim: int,
    n_channels: int,
    prev_encoding: np.ndarray | None = None,
    full_frame: bool = False,
) -> bytes:
    """Encode one frame in mode 1.

    If ``full_frame`` or ``prev_encoding is None``: emit all changed
    channels (or all channels for the very first frame) as an
    independent ('full') block. Else emit only channels that differ
    from prev_encoding.

    ``move_tail`` is the move-metadata bytes (8 for 2D, 14 for 4D),
    appended verbatim after the channels block. The caller is
    responsible for packing it (use ``pack_frame_2d_dense`` /
    ``pack_frame_4d_dense`` for the same tail layout, then slice
    ``encoding_dim*4:`` to extract just the tail).
    """
    if encoding.dtype != np.float32:
        encoding = encoding.astype(np.float32, copy=False)
    expected_dim = n_channels * channel_dim
    if encoding.shape != (expected_dim,):
        raise ValueError(
            f"encoding shape {encoding.shape}, expected ({expected_dim},)"
        )

    if full_frame or prev_encoding is None:
        flags = PC_FLAG_FULL
        # Collect all channels that aren't bit-identical to zero — wait,
        # for FULL frames we emit ALL channels (since the reader has no
        # prior state to reconstruct from).
        view = encoding.reshape(n_channels, channel_dim)
        channels = [(i, view[i].copy()) for i in range(n_channels)]
    else:
        flags = 0
        channels = _channels_diff(prev_encoding, encoding, channel_dim)

    blocks_bytes = _pack_channels_block(channels, channel_dim)
    body_payload = blocks_bytes + move_tail
    # body_size is the length of [flags, n_chan, blocks, tail], i.e.,
    # everything except the leading u32 body_size itself.
    body_size = 1 + 1 + len(body_payload)  # flags(u8) + n_chan(u8) + payload
    head = _PC_HEADER_PACK.pack(body_size, flags, len(channels))
    return head + body_payload


def unpack_frame_per_channel(
    fp: BinaryIO,
    *,
    channel_dim: int,
    n_channels: int,
    move_tail_bytes: int,
    prev_encoding: np.ndarray | None,
) -> Tuple[np.ndarray, bytes, bool]:
    """Read and reconstruct one mode-1 frame from the stream.

    Returns (encoding, move_tail, was_full_frame). The encoding is the
    full reconstructed frame (n_channels * channel_dim float32). The
    move_tail is the raw bytes the caller can decode with
    ``unpack_frame_2d_dense`` / ``unpack_frame_4d_dense`` patterns.
    """
    # Read u32 body_size first, then the rest of the header.
    head_bytes = fp.read(_PC_HEADER_PACK.size)
    if len(head_bytes) != _PC_HEADER_PACK.size:
        raise IOError(
            f"truncated per-channel frame header: got {len(head_bytes)} bytes"
        )
    body_size, flags, n_present = _PC_HEADER_PACK.unpack(head_bytes)
    is_full = bool(flags & PC_FLAG_FULL)
    # Remaining body bytes after the [flags, n_chan] u8 pair we just read.
    remaining = body_size - 2
    body = fp.read(remaining)
    if len(body) != remaining:
        raise IOError(
            f"truncated per-channel body: got {len(body)} of {remaining} bytes"
        )

    # Parse `n_present` channel blocks, then the move tail.
    block_size = _PC_BLOCK_PREFIX_PACK.size + channel_dim * 4
    channels: List[Tuple[int, np.ndarray]] = []
    off = 0
    for _ in range(n_present):
        if off + block_size > len(body):
            raise ValueError(
                f"per-channel: block extends past body (off={off}, body={len(body)})"
            )
        idx, _reserved = _PC_BLOCK_PREFIX_PACK.unpack_from(body, off)
        if not 0 <= idx < n_channels:
            raise ValueError(f"per-channel: bad channel_idx {idx}")
        off += _PC_BLOCK_PREFIX_PACK.size
        buf = np.frombuffer(body[off : off + channel_dim * 4],
                            dtype=np.float32).copy()
        channels.append((idx, buf))
        off += channel_dim * 4

    move_tail = body[off : off + move_tail_bytes]
    if len(move_tail) != move_tail_bytes:
        raise ValueError(
            f"per-channel: move tail expected {move_tail_bytes}, got {len(move_tail)}"
        )

    # Reconstruct the encoding.
    if is_full:
        if n_present != n_channels:
            raise ValueError(
                f"per-channel FULL frame expected all {n_channels} channels; "
                f"got {n_present}"
            )
        encoding = np.empty(n_channels * channel_dim, dtype=np.float32)
        view = encoding.reshape(n_channels, channel_dim)
        for idx, buf in channels:
            view[idx] = buf
    else:
        if prev_encoding is None:
            raise ValueError(
                "per-channel delta frame requires prev_encoding (the previous "
                "reconstructed frame); was the leading frame's FULL flag dropped?"
            )
        encoding = prev_encoding.copy()
        view = encoding.reshape(n_channels, channel_dim)
        for idx, buf in channels:
            view[idx] = buf

    return encoding, move_tail, is_full


def iter_v5_frames_per_channel(fp: BinaryIO, hdr: HeaderV5
                               ) -> Iterator[Tuple[np.ndarray, bytes, bool]]:
    """Stream-decode all frames in a v5 mode-1 file.

    Yields (encoding, move_tail, was_full_frame) for each ply, applying
    the per-channel reconstruction iteratively. Caller can decode the
    move tail using its own ``unpack_frame_*_dense`` machinery (the
    tail layout is identical to mode 0).
    """
    if hdr.encoding_mode != MODE_PER_CHANNEL:
        raise ValueError(
            f"iter_v5_frames_per_channel expects encoding_mode=1; "
            f"got {hdr.encoding_mode}"
        )
    if hdr.n_dimensions == 2:
        n_channels = _N_CHANNELS_2D
        channel_dim = _CHANNEL_DIM_2D
        move_tail = _MOVE_TAIL_2D
    elif hdr.n_dimensions == 4:
        n_channels = _N_CHANNELS_4D
        channel_dim = _CHANNEL_DIM_4D
        move_tail = _MOVE_TAIL_4D
    else:
        raise ValueError(f"unsupported n_dimensions: {hdr.n_dimensions}")

    prev: np.ndarray | None = None
    for _ in range(hdr.n_plies):
        enc, tail, was_full = unpack_frame_per_channel(
            fp,
            channel_dim=channel_dim,
            n_channels=n_channels,
            move_tail_bytes=move_tail,
            prev_encoding=prev,
        )
        yield enc, tail, was_full
        prev = enc


# ─── Mode 2: XOR-streamed (PR-D scope) ──────────────────────────────
#
# Frame body is fixed-size, identical to mode 0 (dense): a float32
# encoding[encoding_dim] + move-metadata tail. The DIFFERENCE is what
# the bytes contain: each frame's float32 array is the bit-XOR of the
# real frame's encoding with the *previous reconstructed* frame's
# encoding, treated as uint32 arrays. Frame 0 is XOR'd against zero,
# which yields the original frame 0 verbatim.
#
# Reconstruction: ``frame_N = stored[N] XOR frame_{N-1}`` (uint32 view).
# Bit-exact, lossless. Wins because chess-encoder hypervectors are
# largely stable per ply -- XOR produces long runs of zero bytes where
# nothing changed, and gzip eats those runs essentially for free.
# Empirical 4D spike: 7.23x compression on a 50-ply knight-tour fixture.


def _xor_float32(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Bit-XOR two float32 arrays via their uint32 reinterpretations.
    Returns a float32 array of the same shape whose bit pattern is the
    XOR of the two inputs. Self-inverse: ``a XOR (a XOR b) == b``."""
    if a.dtype != np.float32 or b.dtype != np.float32:
        raise TypeError("xor: both arrays must be float32")
    if a.shape != b.shape:
        raise ValueError(f"xor: shape mismatch a={a.shape} b={b.shape}")
    out_u32 = a.view(np.uint32) ^ b.view(np.uint32)
    return out_u32.view(np.float32).copy()


def pack_frame_xor_2d(encoding: np.ndarray, ply: int,
                      move_from: int, move_to: int,
                      move_promo: int, move_flags: int,
                      *, prev_encoding: np.ndarray | None) -> bytes:
    """Pack one mode-2 (XOR-stream) frame for 2D.

    The stored encoding bytes = encoding XOR prev_encoding (uint32-wise).
    For the very first frame, prev_encoding=None means XOR-with-zero =
    encoding itself (no transform).
    """
    if prev_encoding is None:
        stored = encoding.astype(np.float32, copy=False)
    else:
        stored = _xor_float32(
            encoding.astype(np.float32, copy=False),
            prev_encoding.astype(np.float32, copy=False),
        )
    return pack_frame_2d_dense(stored, ply, move_from, move_to,
                               move_promo, move_flags)


def pack_frame_xor_4d(encoding: np.ndarray, ply: int,
                      from_sq: Tuple[int, int, int, int],
                      to_sq: Tuple[int, int, int, int],
                      promo: int, flags: int,
                      *, prev_encoding: np.ndarray | None) -> bytes:
    """Pack one mode-2 (XOR-stream) frame for 4D."""
    if prev_encoding is None:
        stored = encoding.astype(np.float32, copy=False)
    else:
        stored = _xor_float32(
            encoding.astype(np.float32, copy=False),
            prev_encoding.astype(np.float32, copy=False),
        )
    return pack_frame_4d_dense(stored, ply, from_sq, to_sq, promo, flags)


def iter_v5_frames_xor_stream(fp: BinaryIO, hdr: HeaderV5
                              ) -> Iterator[Tuple[np.ndarray, bytes]]:
    """Stream-decode all frames in a v5 mode-2 file.

    Yields (encoding, move_tail_bytes) for each ply. `encoding` is the
    fully reconstructed real frame (cumulative XOR applied); the caller
    decodes the move tail with the existing dense-frame unpackers.
    """
    if hdr.encoding_mode != MODE_XOR_STREAM:
        raise ValueError(
            f"iter_v5_frames_xor_stream expects encoding_mode=2; "
            f"got {hdr.encoding_mode}"
        )
    if hdr.n_dimensions == 2:
        encoding_dim = _ENC_DIM_2D
        move_tail = _MOVE_TAIL_2D
        frame_bytes = _FRAME_BYTES_2D
    elif hdr.n_dimensions == 4:
        encoding_dim = _ENC_DIM_4D
        move_tail = _MOVE_TAIL_4D
        frame_bytes = _FRAME_BYTES_4D
    else:
        raise ValueError(f"unsupported n_dimensions: {hdr.n_dimensions}")

    prev: np.ndarray | None = None
    for _ in range(hdr.n_plies):
        chunk = fp.read(frame_bytes)
        if len(chunk) != frame_bytes:
            raise IOError(
                f"truncated XOR frame: got {len(chunk)} of {frame_bytes} bytes"
            )
        # Slice off the encoding part; the rest is the move tail.
        enc_bytes = chunk[: encoding_dim * 4]
        tail = chunk[encoding_dim * 4 :]
        stored_enc = np.frombuffer(enc_bytes, dtype=np.float32).copy()
        if prev is None:
            real_enc = stored_enc
        else:
            real_enc = _xor_float32(stored_enc, prev)
        yield real_enc, tail
        prev = real_enc


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


# ─── Writer (mode 1, PR-C scope) ────────────────────────────────────


def write_v5_per_channel_2d(
    path: str | os.PathLike,
    frames: Iterable[Tuple[np.ndarray, int, int, int, int, int]],
    *,
    compress: bool = False,
) -> int:
    """Write a v5 .spectralz file (2D) in per-channel mode (encoding_mode=1).

    `frames` yields ``(encoding, ply, move_from, move_to, move_promo,
    move_flags)`` tuples — same shape as the dense writer for
    interface parity. The encoder compares each frame against the
    previous one and emits only the channels that differ. The first
    frame is always emitted as a FULL block.

    Returns n_plies written. The eventual ``--encoding=channel`` CLI
    flag will route here.
    """
    return _write_v5_per_channel_common(
        path, frames, n_dimensions=2,
        pack_tail=lambda f: _pack_2d_move_tail(*f[1:]),
        compress=compress,
    )


def write_v5_per_channel_4d(
    path: str | os.PathLike,
    frames: Iterable[Tuple[
        np.ndarray, int, Tuple[int, int, int, int],
        Tuple[int, int, int, int], int, int,
    ]],
    *,
    compress: bool = False,
) -> int:
    """Write a v5 .spectralz4 file (4D) in per-channel mode."""
    return _write_v5_per_channel_common(
        path, frames, n_dimensions=4,
        pack_tail=lambda f: _pack_4d_move_tail(*f[1:]),
        compress=compress,
    )


def _pack_2d_move_tail(ply: int, move_from: int, move_to: int,
                       move_promo: int, move_flags: int) -> bytes:
    return struct.pack(
        "<I4B",
        int(ply) & 0xFFFFFFFF,
        int(move_from) & 0xFF, int(move_to) & 0xFF,
        int(move_promo) & 0xFF, int(move_flags) & 0xFF,
    )


def _pack_4d_move_tail(ply: int, from_sq: Tuple[int, int, int, int],
                       to_sq: Tuple[int, int, int, int],
                       promo: int, flags: int) -> bytes:
    out = bytearray(struct.pack("<I", int(ply) & 0xFFFFFFFF))
    out.extend(bytes([
        int(from_sq[0]) & 0xFF, int(from_sq[1]) & 0xFF,
        int(from_sq[2]) & 0xFF, int(from_sq[3]) & 0xFF,
        int(to_sq[0]) & 0xFF, int(to_sq[1]) & 0xFF,
        int(to_sq[2]) & 0xFF, int(to_sq[3]) & 0xFF,
        int(promo) & 0xFF, int(flags) & 0xFF,
    ]))
    return bytes(out)


def _write_v5_per_channel_common(
    path: str | os.PathLike,
    frames: Iterable,
    *,
    n_dimensions: int,
    pack_tail,
    compress: bool,
) -> int:
    encoding_dim = _ENC_DIM_2D if n_dimensions == 2 else _ENC_DIM_4D
    n_channels = _N_CHANNELS_2D if n_dimensions == 2 else _N_CHANNELS_4D
    channel_dim = _CHANNEL_DIM_2D if n_dimensions == 2 else _CHANNEL_DIM_4D

    tmp_fd, tmp_path = tempfile.mkstemp(prefix="csv_v5_pc_", suffix=".tmp")
    os.close(tmp_fd)
    count = 0
    prev_encoding: np.ndarray | None = None

    try:
        with open(tmp_path, "wb") as out:
            # Placeholder header; backfill after counting.
            out.write(HeaderV5(
                encoding_dim=encoding_dim, n_plies=0,
                n_dimensions=n_dimensions,
                encoding_mode=MODE_PER_CHANNEL,
            ).pack())

            for fr in frames:
                encoding = fr[0]
                tail = pack_tail(fr)
                body = pack_frame_per_channel(
                    encoding, tail,
                    channel_dim=channel_dim,
                    n_channels=n_channels,
                    prev_encoding=prev_encoding,
                    full_frame=(prev_encoding is None),
                )
                out.write(body)
                count += 1
                # The reconstructed encoding becomes the next frame's prev.
                if encoding.dtype != np.float32:
                    encoding = encoding.astype(np.float32, copy=False)
                prev_encoding = encoding

            # Backfill n_plies in the header.
            out.seek(0)
            out.write(HeaderV5(
                encoding_dim=encoding_dim, n_plies=count,
                n_dimensions=n_dimensions,
                encoding_mode=MODE_PER_CHANNEL,
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


# ─── Writer (mode 2: XOR-stream, PR-D scope) ────────────────────────


def write_v5_xor_2d(
    path: str | os.PathLike,
    frames: Iterable[Tuple[np.ndarray, int, int, int, int, int]],
    *,
    compress: bool = False,
) -> int:
    """Write a v5 .spectralz file (2D) in XOR-stream mode (encoding_mode=2).

    `frames` yields ``(encoding, ply, move_from, move_to, move_promo,
    move_flags)`` tuples (same shape as dense / per-channel for parity).
    Each frame's encoding is XOR'd with the previous frame's encoding
    (uint32-wise) before being written. Frame 0 is written verbatim
    (XOR-with-zero baseline).

    The eventual ``--encoding=xor`` CLI flag (default for new writes
    per ADR-001) routes here.
    """
    return _write_v5_xor_common(
        path, frames, n_dimensions=2,
        pack_fn=lambda f, prev: pack_frame_xor_2d(*f, prev_encoding=prev),
        compress=compress,
    )


def write_v5_xor_4d(
    path: str | os.PathLike,
    frames: Iterable[Tuple[
        np.ndarray, int, Tuple[int, int, int, int],
        Tuple[int, int, int, int], int, int,
    ]],
    *,
    compress: bool = False,
) -> int:
    """Write a v5 .spectralz4 file (4D) in XOR-stream mode."""
    return _write_v5_xor_common(
        path, frames, n_dimensions=4,
        pack_fn=lambda f, prev: pack_frame_xor_4d(*f, prev_encoding=prev),
        compress=compress,
    )


def _write_v5_xor_common(
    path: str | os.PathLike,
    frames: Iterable,
    *,
    n_dimensions: int,
    pack_fn,
    compress: bool,
) -> int:
    encoding_dim = _ENC_DIM_2D if n_dimensions == 2 else _ENC_DIM_4D

    tmp_fd, tmp_path = tempfile.mkstemp(prefix="csv_v5_xor_", suffix=".tmp")
    os.close(tmp_fd)
    count = 0
    prev_enc: np.ndarray | None = None
    try:
        with open(tmp_path, "wb") as out:
            out.write(HeaderV5(
                encoding_dim=encoding_dim, n_plies=0,
                n_dimensions=n_dimensions, encoding_mode=MODE_XOR_STREAM,
            ).pack())

            for fr in frames:
                out.write(pack_fn(fr, prev_enc))
                count += 1
                # Save the *real* (pre-XOR) encoding for the next frame.
                enc = fr[0]
                if enc.dtype != np.float32:
                    enc = enc.astype(np.float32, copy=False)
                prev_enc = enc

            out.seek(0)
            out.write(HeaderV5(
                encoding_dim=encoding_dim, n_plies=count,
                n_dimensions=n_dimensions, encoding_mode=MODE_XOR_STREAM,
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
    "PC_FLAG_FULL",
    "HeaderV5",
    "pack_frame_2d_dense", "unpack_frame_2d_dense",
    "pack_frame_4d_dense", "unpack_frame_4d_dense",
    "pack_frame_per_channel", "unpack_frame_per_channel",
    "pack_frame_xor_2d", "pack_frame_xor_4d",
    "open_read_transparent", "peek_version",
    "read_v5_header",
    "iter_v5_frames_dense", "iter_v5_frames_per_channel",
    "iter_v5_frames_xor_stream",
    "write_v5_dense_2d", "write_v5_dense_4d",
    "write_v5_per_channel_2d", "write_v5_per_channel_4d",
    "write_v5_xor_2d", "write_v5_xor_4d",
]
