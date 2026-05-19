"""Path A LZ77 — closed-form sliding-window dictionary compression.

Identity per the implementation plan §1: LZ77 IS a Class A (SHA-256 content
addressing on canonical pattern handles) ∘ Class G (byte-pattern search in
the sliding window) ∘ Class B (TLV byte-canonical form on encoded tokens)
composition.

The closed-form reference is the canonical LZ77 with explicit
(offset, length, next-literal) token form.

Path B dual in Phase 6 (Path B SHA-256 + pattern + TLV in bound-vector
pipeline).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Ziv &
Lempel (1977) IEEE T-IT.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

OPERATION_NAME = "lz77"
CLASS_COMPOSITION = ("A", "G", "B")
PERFORMANCE_HINT = "shallow-cascade-window-amortise"
SSOT_CITATION = (
    "Ziv & Lempel (1977), 'A universal algorithm for sequential data "
    "compression', IEEE Trans. Inf. Theory 23(3), 337-343. DOI 10.1109/"
    "TIT.1977.1055714 (Crossref)."
)


def op(
    data,
    *,
    decode: bool = False,
    window_size: int = 4096,
    lookahead_size: int = 18,
    D: int = 8192,
):
    """LZ77 encode or decode ``data``.

    Encode emits tokens ``(offset, length, next_literal)``. Decode replays
    tokens to reconstruct the original byte stream.

    Parameters
    ----------
    data:
        Bytes-like (encode) or token list (decode).
    decode:
        If True, decode token list back to bytes.
    window_size:
        Sliding-window size (Class G search radius).
    lookahead_size:
        Lookahead buffer size (max match length).
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    Encode: list of ``(offset, length, next_literal)`` tuples.
    Decode: bytes of reconstructed input.
    """
    if decode:
        out = bytearray()
        for offset, length, literal in data:
            if length > 0:
                start = len(out) - offset
                for i in range(length):
                    out.append(out[start + i])
            if literal is not None:
                out.append(literal & 0xFF)
        return bytes(out)
    if isinstance(data, str):
        data = data.encode("utf-8")
    data_bytes = bytes(data)
    tokens: List[Tuple[int, int, Optional[int]]] = []
    i = 0
    n = len(data_bytes)
    while i < n:
        # Search backwards in window for longest match starting at i
        window_start = max(0, i - window_size)
        best_offset = 0
        best_length = 0
        max_match = min(lookahead_size, n - i)
        for ws in range(window_start, i):
            length = 0
            while (
                length < max_match
                and ws + length < i
                and data_bytes[ws + length] == data_bytes[i + length]
            ):
                length += 1
            if length > best_length:
                best_length = length
                best_offset = i - ws
        if best_length > 0 and i + best_length < n:
            tokens.append((best_offset, best_length, data_bytes[i + best_length]))
            i += best_length + 1
        elif best_length > 0:
            tokens.append((best_offset, best_length, None))
            i += best_length
        else:
            tokens.append((0, 0, data_bytes[i]))
            i += 1
    return tokens
