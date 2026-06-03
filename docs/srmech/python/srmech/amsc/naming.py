"""Class E — catalog / naming primitive (Task #217 Phase C1).

Single operation: :func:`lookup` — given a search key and a sorted
list of (key, value) pairs, find the entry whose key equals the
search key and return its value bytes. Binary search over ascending
lexicographic keys.

Class E is the structured-key → canonical-value lookup primitive.
The existing ``srmech.amsc.catalog`` module is the application of
Class E to attested-source registries; this module exposes the bare
primitive so higher-level catalogs can be built on it (and so the
C path is reachable directly when a hot loop needs it).

API
---

- :func:`lookup(key, pairs)` — ``pairs`` is an iterable of
  ``(key_bytes, value_bytes)`` tuples. Caller is responsible for
  providing pairs sorted ascending lexicographic by key. Returns
  the matching ``value_bytes`` or ``None`` if not found.
"""

from __future__ import annotations

import ctypes
from typing import Iterable, Optional, Tuple

from . import _native

__all__ = ["lookup", "reverse_order"]


def reverse_order(sorted_pairs: Iterable[Tuple[bytes, bytes]]) -> list:
    """Harmonic-2 chiral mirror of a sorted Class-E catalog (F150): the
    order-reversed ``(key, value)`` list — a descending-key view of an
    ascending catalog. Class E is harmonic-2 (chiral inverse) per F150 §6.1;
    ``reverse_order(reverse_order(x)) == list(x)`` (period 2). The
    chirality-aware companion to :func:`lookup`.
    """
    pairs = list(sorted_pairs)
    n = len(pairs)
    if (
        _native.HAS_NATIVE
        and _native.LIB is not None
        and hasattr(_native.LIB, "srmech_reverse_order")
        and n <= 0xFFFF_FFFF
        and n > 0
    ):
        order = (ctypes.c_uint32 * n)()
        rc = _native.LIB.srmech_reverse_order(ctypes.c_uint32(n), order)
        if rc != _native.SRMECH_OK:
            raise RuntimeError(
                f"srmech_reverse_order returned non-OK status {rc}"
            )
        return [pairs[order[i]] for i in range(n)]
    return pairs[::-1]


def lookup(key: bytes,
           pairs: Iterable[Tuple[bytes, bytes]]) -> Optional[bytes]:
    """Binary-search a sorted (key, value) catalog for ``key``.

    Caller MUST pre-sort ``pairs`` ascending by lexicographic
    byte comparison (length-tiebreak: shorter < longer when
    prefix-equal). Returns the matching value bytes, or ``None``
    if ``key`` is not in the catalog.

    Both C and Python paths produce byte-exact identical results;
    pinned by ``tests/test_def_parity.py``.
    """
    if not isinstance(key, (bytes, bytearray, memoryview)):
        raise TypeError(f"key must be bytes-like; got {type(key).__name__}")
    pair_list = [(bytes(k), bytes(v)) for (k, v) in pairs]
    n_pairs = len(pair_list)
    key_b = bytes(key)
    if n_pairs == 0:
        return None
    if _native.HAS_NATIVE and _native.LIB is not None:
        keys_buf = bytearray()
        values_buf = bytearray()
        key_off = (ctypes.c_uint32 * n_pairs)()
        key_len = (ctypes.c_uint32 * n_pairs)()
        val_off = (ctypes.c_uint32 * n_pairs)()
        val_len = (ctypes.c_uint32 * n_pairs)()
        for i, (k, v) in enumerate(pair_list):
            key_off[i] = len(keys_buf)
            key_len[i] = len(k)
            keys_buf.extend(k)
            val_off[i] = len(values_buf)
            val_len[i] = len(v)
            values_buf.extend(v)
        keys_c = (
            (ctypes.c_uint8 * len(keys_buf)).from_buffer_copy(bytes(keys_buf))
            if len(keys_buf) > 0
            else ctypes.cast(None, ctypes.POINTER(ctypes.c_uint8))
        )
        vals_c = (
            (ctypes.c_uint8 * len(values_buf)).from_buffer_copy(bytes(values_buf))
            if len(values_buf) > 0
            else ctypes.cast(None, ctypes.POINTER(ctypes.c_uint8))
        )
        key_c = (
            (ctypes.c_uint8 * len(key_b)).from_buffer_copy(key_b)
            if len(key_b) > 0
            else ctypes.cast(None, ctypes.POINTER(ctypes.c_uint8))
        )
        out_found = ctypes.c_bool(False)
        out_v_off = ctypes.c_uint32(0)
        out_v_len = ctypes.c_uint32(0)
        # Note: srmech_catalog_lookup does not take values_buffer
        # (returns offsets only; caller already owns the values buffer).
        # We retain vals_c locally for slicing the result below.
        _ = vals_c
        rc = _native.LIB.srmech_catalog_lookup(
            key_c, ctypes.c_uint32(len(key_b)),
            keys_c, key_off, key_len,
            val_off, val_len,
            ctypes.c_uint32(n_pairs),
            ctypes.byref(out_found),
            ctypes.byref(out_v_off),
            ctypes.byref(out_v_len),
        )
        if rc != _native.SRMECH_OK:
            raise RuntimeError(f"srmech_catalog_lookup returned {rc}")
        if not out_found.value:
            return None
        start = int(out_v_off.value)
        length = int(out_v_len.value)
        return bytes(values_buf[start : start + length])
    # Pure-Python fallback: binary search by key lex compare.
    lo, hi = 0, n_pairs - 1
    while lo <= hi:
        mid = lo + (hi - lo) // 2
        mid_key, mid_value = pair_list[mid]
        if key_b == mid_key:
            return mid_value
        if key_b < mid_key:
            hi = mid - 1
        else:
            lo = mid + 1
    return None
