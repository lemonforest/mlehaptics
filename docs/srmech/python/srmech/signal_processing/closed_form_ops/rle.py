"""Path A run-length encoding — closed-form repeat-byte counter compression.

Identity per the implementation plan §1: RLE IS a Class B (TLV byte-canonical
form: ``(symbol, count)`` records) ∘ Class G (byte-pattern run detection)
composition.

The closed-form reference emits ``(symbol, count)`` pairs; decode replays
the pairs to reconstruct the original byte stream bit-exactly.

Path B dual in Phase 6 (Path B byte-pattern + TLV in bound-vector pipeline).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Salomon
(2007) *Data Compression: The Complete Reference* (4th ed.), §1.4.
"""

from __future__ import annotations

import ctypes
from typing import List, Tuple

from srmech.amsc import _native

OPERATION_NAME = "rle"
CLASS_COMPOSITION = ("B", "G")
PERFORMANCE_HINT = "single-token-fast"
SSOT_CITATION = (
    "Salomon (2007), 'Data Compression: The Complete Reference' (4th ed.), "
    "Springer, §1.4 (run-length encoding). ITU-T T.4 (1980) fax-encoding "
    "standard — first widely-deployed RLE format."
)


def _rle_encode_native(data_bytes, max_run):
    """Native run-length encode → ``list[(symbol, count)]`` (byte-identical to the
    pure run-scan) or ``None`` (rc143 §B6a). Pure integer; run boundaries match
    the Python loop exactly (symbol change or ``count == max_run``)."""
    if not _native.has_native_rle_encode():
        return None
    n = len(data_bytes)
    if n == 0:
        return []
    cdata = (ctypes.c_uint8 * n).from_buffer_copy(bytes(data_bytes))
    out_sym = (ctypes.c_uint8 * n)()
    out_count = (ctypes.c_uint32 * n)()
    npairs = ctypes.c_uint32(0)
    rc = _native.LIB.srmech_rle_encode(
        cdata, ctypes.c_uint32(n), ctypes.c_uint32(max_run),
        out_sym, out_count, ctypes.byref(npairs))
    if rc != _native.SRMECH_OK:
        return None
    m = npairs.value
    return [(int(out_sym[i]), int(out_count[i])) for i in range(m)]


def op(data, *, decode: bool = False, max_run: int = 255, D: int = 8192):
    """Run-length encode or decode ``data``.

    Parameters
    ----------
    data:
        Bytes-like (encode) or list of ``(symbol, count)`` tuples (decode).
    decode:
        If True, decode tuple list back to bytes.
    max_run:
        Maximum count per record; longer runs split across multiple records.
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    Encode: list of ``(symbol, count)`` tuples.
    Decode: bytes.
    """
    if decode:
        out = bytearray()
        for sym, count in data:
            out.extend([sym & 0xFF] * count)
        return bytes(out)
    if isinstance(data, str):
        data = data.encode("utf-8")
    data_bytes = bytes(data)
    native = _rle_encode_native(data_bytes, max_run)   # rc143 §B6a
    if native is not None:
        return native
    out: List[Tuple[int, int]] = []
    i = 0
    n = len(data_bytes)
    while i < n:
        sym = data_bytes[i]
        count = 1
        while i + count < n and data_bytes[i + count] == sym and count < max_run:
            count += 1
        out.append((sym, count))
        i += count
    return out
