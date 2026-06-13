"""Class B — tagged-tuple (TLV) byte-canonical form (Task #217 Phase C1).

:func:`tlv_pack` produces a deterministic ``[tag][length BE-u32][value]``
byte sequence suitable for hashing / fingerprinting tagged records;
:func:`tlv_unpack` is its inverse reader (returns ``(tag, value,
next_offset)`` so a concatenation of frames is walked frame-by-frame).

Format
------

- 1 byte: ``tag`` (uint8, 0-255)
- 4 bytes: ``len(value)`` as big-endian unsigned 32-bit integer
- ``len(value)`` bytes: the value verbatim

Total prefix is 5 bytes. Big-endian length follows the conventional
wire-format byte order for tagged records.

Class B at the Python ergonomic surface remains JSON-side
(``MPRRecord.from_json_line`` in ``amsc.format``); :func:`tlv_pack`
is the C-level primitive operation, used for stable byte
fingerprints of typed records.
"""

from __future__ import annotations

import ctypes
import struct

from . import _native

__all__ = [
    "tlv_pack",
    "tlv_unpack",
    "TLV_PREFIX_BYTES",
]

TLV_PREFIX_BYTES: int = 5


def tlv_pack(tag: int, value: bytes) -> bytes:
    """Pack ``(tag, value)`` into a deterministic TLV byte sequence.

    ``tag`` must be ``0 <= tag <= 255``. ``value`` must be ``bytes``
    of length ``≤ 2**32 - 1``. Returns the 5-byte prefix + ``value``.

    Both C and Python paths produce byte-exact identical results;
    pinned by ``tests/test_tlv_parity.py``.
    """
    if not isinstance(tag, int):
        raise TypeError(f"tag must be int; got {type(tag).__name__}")
    if not (0 <= tag <= 0xFF):
        raise ValueError(f"tag must be in [0, 255]; got {tag}")
    if not isinstance(value, (bytes, bytearray, memoryview)):
        raise TypeError(
            f"value must be bytes-like; got {type(value).__name__}"
        )
    value_bytes = bytes(value)
    if len(value_bytes) > 0xFFFF_FFFF:
        raise ValueError(
            f"value length exceeds uint32 range; got {len(value_bytes)}"
        )
    if _native.HAS_NATIVE and _native.LIB is not None:
        out_capacity = TLV_PREFIX_BYTES + len(value_bytes)
        out_buffer = (ctypes.c_uint8 * out_capacity)()
        out_written = ctypes.c_uint32(0)
        value_ptr = (
            (ctypes.c_uint8 * len(value_bytes)).from_buffer_copy(value_bytes)
            if len(value_bytes) > 0
            else ctypes.cast(None, ctypes.POINTER(ctypes.c_uint8))
        )
        rc = _native.LIB.srmech_tlv_pack(
            ctypes.c_uint8(tag),
            value_ptr,
            ctypes.c_uint32(len(value_bytes)),
            out_buffer,
            ctypes.c_uint32(out_capacity),
            ctypes.byref(out_written),
        )
        if rc != _native.SRMECH_OK:
            raise RuntimeError(f"srmech_tlv_pack returned non-OK status {rc}")
        return bytes(out_buffer[: out_written.value])
    # Pure-Python fallback: struct.pack big-endian length + value.
    return struct.pack(">BI", tag, len(value_bytes)) + value_bytes


def tlv_unpack(buffer: bytes, offset: int = 0) -> "tuple[int, bytes, int]":
    """Read one TLV frame back out — the inverse of :func:`tlv_pack` (Class B).

    Reads the ``[tag][length BE-u32][value]`` frame that begins at ``offset``
    in ``buffer`` and returns ``(tag, value, next_offset)`` where
    ``next_offset`` is the index just past this frame — so a concatenation of
    frames is walked by feeding ``next_offset`` back in::

        off = 0
        while off < len(buf):
            tag, value, off = tlv_unpack(buf, off)
            ...

    ``tlv_pack`` ships the writer half; this is its missing reader. Exact
    round-trip: ``tlv_unpack(tlv_pack(t, v)) == (t, v, 5 + len(v))``. Raises
    ``ValueError`` on a truncated prefix or a length that runs past the end of
    ``buffer`` (a malformed / clipped frame), never returning partial data.
    """
    if not isinstance(buffer, (bytes, bytearray, memoryview)):
        raise TypeError(
            f"buffer must be bytes-like; got {type(buffer).__name__}"
        )
    if not isinstance(offset, int) or isinstance(offset, bool):
        raise TypeError(f"offset must be a plain int; got {offset!r}")
    buf = bytes(buffer)
    if offset < 0 or offset > len(buf):
        raise ValueError(f"offset {offset} out of range [0, {len(buf)}]")
    if len(buf) - offset < TLV_PREFIX_BYTES:
        raise ValueError(
            f"truncated TLV prefix: need {TLV_PREFIX_BYTES} bytes at "
            f"offset {offset}, have {len(buf) - offset}"
        )
    tag = buf[offset]
    (length,) = struct.unpack_from(">I", buf, offset + 1)
    value_start = offset + TLV_PREFIX_BYTES
    value_end = value_start + length
    if value_end > len(buf):
        raise ValueError(
            f"truncated TLV value: frame claims {length} bytes but only "
            f"{len(buf) - value_start} remain after offset {offset}"
        )
    return tag, buf[value_start:value_end], value_end
