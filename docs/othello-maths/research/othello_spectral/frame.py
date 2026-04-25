"""Binary frame format for Othello spectral encodings.

Modeled after docs/chess-maths/chess-spectral/python/chess_spectral/frame.py:
compact little-endian float32 serialisation designed to match the
future ANSI C17 encoder's output byte-for-byte.

File layout (v1)
----------------

    HEADER (256 bytes)
      magic          : 8 bytes   ASCII "OTHSPC\x00\x00"
      version        : u32       format version (=1)
      encoding_dim   : u32       =768 at v0.1.0
      n_frames       : u32       number of frames in the file
      bytes_per_frame: u32       =772 at v0.1.0 (768*f32 + u32 ply)
      metadata       : 232 bytes zero-padded ASCII, free-form text
                                  (e.g. corpus name, encoder VERSION).

    FRAMES (n_frames * bytes_per_frame)
      data_768       : 768 x f32 little-endian
      ply            : u32 little-endian

Both the header and frame layouts use explicit ``struct`` packing
with little-endian byte order so the output is identical on any
platform.  All floats are stored as float32 even though the encoder
works in float64 internally; the final downcast is a single
``astype(np.float32)`` call and matches the chess-spectral
convention.

Usage
-----

    from othello_spectral.frame import write_file, read_file, Frame

    frames = [Frame(data=encode_768(state_i), ply=i) for i, state_i in ...]
    write_file(path, frames, metadata="my_corpus run_id=x seed=42")

    hdr, frames = read_file(path)
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np

from .tables import ENCODING_DIM


FORMAT_VERSION: int = 1
MAGIC: bytes = b"OTHSPC\x00\x00"  # 8 bytes
HEADER_META_BYTES: int = 232
HEADER_STRUCT = "<8sIIII232s"  # 8 + 4 + 4 + 4 + 4 + 232 = 256 bytes
HEADER_BYTES: int = struct.calcsize(HEADER_STRUCT)
assert HEADER_BYTES == 256, HEADER_BYTES

FRAME_DATA_STRUCT = f"<{ENCODING_DIM}f"     # 768 float32
FRAME_TAIL_STRUCT = "<I"                    # u32 ply
FRAME_BYTES: int = (
    struct.calcsize(FRAME_DATA_STRUCT)
    + struct.calcsize(FRAME_TAIL_STRUCT)
)


@dataclass(frozen=True)
class Header:
    format_version: int
    encoding_dim: int
    n_frames: int
    bytes_per_frame: int
    metadata: str


@dataclass(frozen=True)
class Frame:
    data: np.ndarray  # shape (ENCODING_DIM,), cast to float32 on write
    ply: int

    def __post_init__(self) -> None:
        arr = np.asarray(self.data)
        if arr.shape != (ENCODING_DIM,):
            raise ValueError(
                f"Frame.data must have shape ({ENCODING_DIM},), "
                f"got {arr.shape}"
            )


def _pack_metadata(metadata: str) -> bytes:
    raw = metadata.encode("utf-8")[:HEADER_META_BYTES]
    return raw + b"\x00" * (HEADER_META_BYTES - len(raw))


def write_file(
    path: Path | str, frames: Iterable[Frame], metadata: str = "",
) -> None:
    """Write frames to a binary .spectralz file.  The frames iterable
    is materialised once to count the frames and stream bytes."""
    frames = list(frames)
    n_frames = len(frames)
    header_bytes = struct.pack(
        HEADER_STRUCT,
        MAGIC,
        FORMAT_VERSION,
        ENCODING_DIM,
        n_frames,
        FRAME_BYTES,
        _pack_metadata(metadata),
    )
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("wb") as f:
        f.write(header_bytes)
        for frame in frames:
            arr32 = np.asarray(frame.data, dtype=np.float32)
            f.write(struct.pack(FRAME_DATA_STRUCT, *arr32))
            f.write(struct.pack(FRAME_TAIL_STRUCT, int(frame.ply)))


def read_file(path: Path | str) -> tuple[Header, list[Frame]]:
    """Read a .spectralz file and return (Header, list[Frame]).

    Frames have ``data`` as float32 arrays; callers needing float64
    should cast explicitly.
    """
    with Path(path).open("rb") as f:
        hbytes = f.read(HEADER_BYTES)
        if len(hbytes) != HEADER_BYTES:
            raise ValueError(
                f"file too short for header: {len(hbytes)} < {HEADER_BYTES}"
            )
        magic, ver, enc_dim, n_frames, bpf, meta = struct.unpack(
            HEADER_STRUCT, hbytes,
        )
        if magic != MAGIC:
            raise ValueError(
                f"bad magic: {magic!r} (expected {MAGIC!r})"
            )
        if ver != FORMAT_VERSION:
            raise ValueError(
                f"unsupported format version {ver} "
                f"(runtime expects {FORMAT_VERSION})"
            )
        if enc_dim != ENCODING_DIM:
            raise ValueError(
                f"encoding_dim mismatch: file={enc_dim}, "
                f"runtime={ENCODING_DIM}"
            )
        if bpf != FRAME_BYTES:
            raise ValueError(
                f"bytes_per_frame mismatch: file={bpf}, "
                f"runtime={FRAME_BYTES}"
            )
        metadata = meta.rstrip(b"\x00").decode("utf-8", errors="replace")
        header = Header(
            format_version=ver,
            encoding_dim=enc_dim,
            n_frames=n_frames,
            bytes_per_frame=bpf,
            metadata=metadata,
        )
        frames: list[Frame] = []
        for _ in range(n_frames):
            data_bytes = f.read(struct.calcsize(FRAME_DATA_STRUCT))
            tail_bytes = f.read(struct.calcsize(FRAME_TAIL_STRUCT))
            arr = np.array(
                struct.unpack(FRAME_DATA_STRUCT, data_bytes),
                dtype=np.float32,
            )
            (ply,) = struct.unpack(FRAME_TAIL_STRUCT, tail_bytes)
            frames.append(Frame(data=arr, ply=int(ply)))
        return header, frames


__all__ = [
    "Header", "Frame",
    "MAGIC", "FORMAT_VERSION", "FRAME_BYTES", "HEADER_BYTES",
    "write_file", "read_file",
]
