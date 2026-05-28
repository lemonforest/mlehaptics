"""TLV framing over a byte stream for srmech.bus.

Per spec rc1: 4-byte big-endian length prefix + payload bytes.
Simpler than the 5-byte ``[tag][len BE-u32][value]`` format used by
:mod:`srmech.amsc.tlv` (which is for tagged-record hashing) — the bus
needs only framing-on-a-byte-stream, no tag dimension; the
:class:`~srmech.bus._event.Event` carries the type discriminator in
its JSON payload.

The C peer ships in rc2 (per user direction 2026-05-28); the rc1
Python wrapper here is the SSOT until then.

Framework reading: Class B (TLV / type-length-value framing)
projected onto a byte-stream transport. The 4-byte big-endian length
is the conventional wire-format byte order for tagged records;
matches the length-field byte order in
:func:`srmech.amsc.tlv.tlv_pack`.
"""

from __future__ import annotations

import io
import struct
from typing import Optional

#: Length-prefix size in bytes (big-endian unsigned 32-bit).
FRAME_PREFIX_BYTES: int = 4

#: Maximum allowed payload size (defends against runaway allocations
#: from a malformed or hostile peer). 64 MiB is plenty for any
#: bus event we currently emit.
MAX_FRAME_PAYLOAD_BYTES: int = 64 * 1024 * 1024


class FramingError(Exception):
    """Raised on malformed framing (bad length / short read)."""


def pack_frame(payload: bytes) -> bytes:
    """Wrap ``payload`` in a length-prefixed frame.

    Frame layout:

    ::

        [length BE-u32][payload bytes]

    Parameters
    ----------
    payload
        Raw bytes to frame. Length must fit in unsigned 32 bits
        AND be ``<= MAX_FRAME_PAYLOAD_BYTES``.

    Returns
    -------
    bytes
        ``4 + len(payload)`` bytes ready for ``socket.sendall``.
    """
    if not isinstance(payload, (bytes, bytearray, memoryview)):
        raise TypeError(
            f"payload must be bytes-like; got {type(payload).__name__}"
        )
    payload_bytes = bytes(payload)
    n = len(payload_bytes)
    if n > MAX_FRAME_PAYLOAD_BYTES:
        raise ValueError(
            f"payload {n} bytes exceeds MAX_FRAME_PAYLOAD_BYTES "
            f"({MAX_FRAME_PAYLOAD_BYTES})"
        )
    if n > 0xFFFF_FFFF:
        raise ValueError(
            f"payload {n} bytes exceeds uint32 range"
        )
    return struct.pack(">I", n) + payload_bytes


def _read_exact(reader, n: int) -> Optional[bytes]:
    """Read exactly ``n`` bytes from ``reader``.

    ``reader`` is an object exposing ``.recv(n)`` (socket) OR
    ``.read(n)`` (file-like). Returns ``None`` on a clean EOF before
    any bytes are read; raises :class:`FramingError` on a short read
    after some bytes have arrived.
    """
    buf = bytearray()
    while len(buf) < n:
        want = n - len(buf)
        if hasattr(reader, "recv"):
            chunk = reader.recv(want)
        else:
            chunk = reader.read(want)
        if not chunk:
            if not buf:
                return None
            raise FramingError(
                f"short read: wanted {n} bytes, got {len(buf)}"
            )
        buf.extend(chunk)
    return bytes(buf)


def unpack_frame(reader) -> Optional[bytes]:
    """Read one length-prefixed frame from ``reader``.

    ``reader`` is an object with ``.recv(n) -> bytes`` (socket) or
    ``.read(n) -> bytes`` (file-like / pipe wrapper).

    Returns
    -------
    bytes | None
        The unwrapped payload, or ``None`` on clean EOF before any
        bytes were read (peer closed cleanly).

    Raises
    ------
    FramingError
        On a short read after framing-bytes started arriving, or on
        a length-field that exceeds :data:`MAX_FRAME_PAYLOAD_BYTES`.
    """
    header = _read_exact(reader, FRAME_PREFIX_BYTES)
    if header is None:
        return None
    (n,) = struct.unpack(">I", header)
    if n > MAX_FRAME_PAYLOAD_BYTES:
        raise FramingError(
            f"frame length {n} exceeds MAX_FRAME_PAYLOAD_BYTES "
            f"({MAX_FRAME_PAYLOAD_BYTES})"
        )
    if n == 0:
        return b""
    payload = _read_exact(reader, n)
    if payload is None:
        raise FramingError(
            f"unexpected EOF in payload (length={n}, got 0 bytes)"
        )
    return payload


def iter_frames(reader):
    """Generator yielding successive frames from ``reader`` until EOF."""
    while True:
        frame = unpack_frame(reader)
        if frame is None:
            return
        yield frame


__all__ = [
    "FRAME_PREFIX_BYTES",
    "FramingError",
    "MAX_FRAME_PAYLOAD_BYTES",
    "iter_frames",
    "pack_frame",
    "unpack_frame",
]
