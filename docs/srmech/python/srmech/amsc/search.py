"""Class G — discovery / search (Task #217 Phase C1).

Single operation: :func:`byte_search` finds the first occurrence of
a byte ``needle`` in a byte ``haystack``, returning the offset or
``None`` if not found.

Class G at the Python ergonomic surface includes catalog discovery
(``register_attested_root`` / ``list_attested_sources`` in
``amsc.catalog``) — those stay Python-side as dictionary lookups
per srmech CLAUDE.md operational-scope-clarification. The C-level
primitive operation is the byte-pattern search used by lower-level
machinery (e.g., fingerprint scanning, descriptor lookup).
"""

from __future__ import annotations

import ctypes
from typing import Optional

from . import _native

__all__ = [
    "byte_search",
    "byte_search_backward",
]


def byte_search_backward(haystack: bytes, needle: bytes) -> Optional[int]:
    """Harmonic-2 chiral mirror of :func:`byte_search` (F150): the offset of
    the LAST occurrence of ``needle`` in ``haystack`` (mirrored search
    direction), or ``None`` if absent. Empty needle returns ``len(haystack)``
    (matches ``bytes.rfind(b"")``). Class G is harmonic-2 (chiral inverse) per
    F150 §6.1 — forward / backward are the period-2 mirror pair.
    """
    if not isinstance(haystack, (bytes, bytearray, memoryview)):
        raise TypeError(
            f"haystack must be bytes-like; got {type(haystack).__name__}"
        )
    if not isinstance(needle, (bytes, bytearray, memoryview)):
        raise TypeError(
            f"needle must be bytes-like; got {type(needle).__name__}"
        )
    h = bytes(haystack)
    n = bytes(needle)
    if len(h) > 0xFFFF_FFFF:
        raise ValueError(
            f"haystack length exceeds uint32 range; got {len(h)}"
        )
    if len(n) > 0xFFFF_FFFF:
        raise ValueError(
            f"needle length exceeds uint32 range; got {len(n)}"
        )
    if (
        _native.HAS_NATIVE
        and _native.LIB is not None
        and hasattr(_native.LIB, "srmech_byte_search_backward")
    ):
        h_ptr = (
            (ctypes.c_uint8 * len(h)).from_buffer_copy(h)
            if len(h) > 0
            else ctypes.cast(None, ctypes.POINTER(ctypes.c_uint8))
        )
        n_ptr = (
            (ctypes.c_uint8 * len(n)).from_buffer_copy(n)
            if len(n) > 0
            else ctypes.cast(None, ctypes.POINTER(ctypes.c_uint8))
        )
        out_offset = ctypes.c_uint32(0)
        rc = _native.LIB.srmech_byte_search_backward(
            h_ptr,
            ctypes.c_uint32(len(h)),
            n_ptr,
            ctypes.c_uint32(len(n)),
            ctypes.byref(out_offset),
        )
        if rc != _native.SRMECH_OK:
            raise RuntimeError(
                f"srmech_byte_search_backward returned non-OK status {rc}"
            )
        if out_offset.value == 0xFFFF_FFFF:
            return None
        return int(out_offset.value)
    # Pure-Python fallback: bytes.rfind returns -1 on miss.
    idx = h.rfind(n)
    return idx if idx >= 0 else None


def byte_search(haystack: bytes, needle: bytes) -> Optional[int]:
    """Return the offset of the first occurrence of ``needle`` in
    ``haystack``, or ``None`` if ``needle`` is not present.

    Empty needle returns ``0`` (matches Python's ``bytes.find(b"")``).

    Both C and Python paths produce byte-exact identical results;
    pinned by ``tests/test_search_parity.py``.
    """
    if not isinstance(haystack, (bytes, bytearray, memoryview)):
        raise TypeError(
            f"haystack must be bytes-like; got {type(haystack).__name__}"
        )
    if not isinstance(needle, (bytes, bytearray, memoryview)):
        raise TypeError(
            f"needle must be bytes-like; got {type(needle).__name__}"
        )
    h = bytes(haystack)
    n = bytes(needle)
    if len(h) > 0xFFFF_FFFF:
        raise ValueError(
            f"haystack length exceeds uint32 range; got {len(h)}"
        )
    if len(n) > 0xFFFF_FFFF:
        raise ValueError(
            f"needle length exceeds uint32 range; got {len(n)}"
        )
    if _native.HAS_NATIVE and _native.LIB is not None:
        h_ptr = (
            (ctypes.c_uint8 * len(h)).from_buffer_copy(h)
            if len(h) > 0
            else ctypes.cast(None, ctypes.POINTER(ctypes.c_uint8))
        )
        n_ptr = (
            (ctypes.c_uint8 * len(n)).from_buffer_copy(n)
            if len(n) > 0
            else ctypes.cast(None, ctypes.POINTER(ctypes.c_uint8))
        )
        out_offset = ctypes.c_uint32(0)
        rc = _native.LIB.srmech_byte_search(
            h_ptr,
            ctypes.c_uint32(len(h)),
            n_ptr,
            ctypes.c_uint32(len(n)),
            ctypes.byref(out_offset),
        )
        if rc != _native.SRMECH_OK:
            raise RuntimeError(
                f"srmech_byte_search returned non-OK status {rc}"
            )
        if out_offset.value == 0xFFFF_FFFF:
            return None
        return int(out_offset.value)
    # Pure-Python fallback: bytes.find returns -1 on miss.
    idx = h.find(n)
    return None if idx < 0 else idx
