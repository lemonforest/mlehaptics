"""Path A Huffman coding — closed-form prefix-code construction + encode/decode.

Identity per the implementation plan §1: Huffman IS a Class E (sorted-key
catalog lookup: symbol -> code) ∘ Class B (TLV byte-canonical form for the
encoded bitstream) composition.

The closed-form reference builds the Huffman tree from a symbol-frequency
table and emits the canonical prefix-code table. Encode/decode round-trip
preserves the original byte stream bit-exactly.

Path B dual in Phase 6 (Huffman catalog as bound-vector address space).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Huffman
(1952) + Cormen et al. (2009) *Introduction to Algorithms* (3rd ed.) §16.3.
"""

from __future__ import annotations

import heapq
from typing import Dict, List, Optional, Tuple

OPERATION_NAME = "huffman"
CLASS_COMPOSITION = ("E", "B")
PERFORMANCE_HINT = "small-D-one-shot"
SSOT_CITATION = (
    "Huffman (1952), 'A method for the construction of minimum-redundancy "
    "codes', Proc. IRE 40(9), 1098-1101. DOI 10.1109/JRPROC.1952.273898 "
    "(Crossref). Cormen, Leiserson, Rivest & Stein (2009, 3rd ed.), "
    "'Introduction to Algorithms', MIT Press, §16.3."
)


def _build_codes(freq: Dict[int, int]) -> Dict[int, str]:
    """Build canonical prefix codes from a frequency table."""
    if not freq:
        return {}
    if len(freq) == 1:
        # Single-symbol special case: code is just "0"
        return {next(iter(freq)): "0"}
    heap: List[Tuple[int, int, Dict[int, str]]] = []
    counter = 0
    for sym, f in freq.items():
        heap.append((f, counter, {sym: ""}))
        counter += 1
    heapq.heapify(heap)
    while len(heap) > 1:
        f1, _, codes1 = heapq.heappop(heap)
        f2, _, codes2 = heapq.heappop(heap)
        merged = {}
        for s, c in codes1.items():
            merged[s] = "0" + c
        for s, c in codes2.items():
            merged[s] = "1" + c
        heapq.heappush(heap, (f1 + f2, counter, merged))
        counter += 1
    _, _, final = heap[0]
    return final


def op(
    data,
    *,
    decode: bool = False,
    codes: Optional[Dict[int, str]] = None,
    bit_length: Optional[int] = None,
    D: int = 8192,
):
    """Huffman encode or decode ``data``.

    Parameters
    ----------
    data:
        Byte sequence (encode) or string of '0'/'1' bits (decode).
    decode:
        If True, decode using ``codes`` (required); otherwise encode.
    codes:
        Symbol-to-bit-string mapping for decode. Ignored for encode.
    bit_length:
        Optional truncation length when decoding (in bits).
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    tuple
        Encode: ``(bit_string, codes)`` where ``bit_string`` is a string of
        '0'/'1' characters and ``codes`` is the symbol-to-bitstring table.
        Decode: ``bytes`` of recovered symbols.
    """
    if decode:
        if codes is None:
            raise ValueError("huffman decode requires 'codes' argument")
        # Build inverse table
        inv = {c: s for s, c in codes.items()}
        bits = str(data)
        if bit_length is not None:
            bits = bits[:bit_length]
        out = bytearray()
        buf = ""
        for b in bits:
            buf += b
            if buf in inv:
                out.append(inv[buf] & 0xFF)
                buf = ""
        return bytes(out)
    # Encode
    if isinstance(data, str):
        data = data.encode("utf-8")
    data_bytes = bytes(data)
    freq: Dict[int, int] = {}
    for b in data_bytes:
        freq[b] = freq.get(b, 0) + 1
    code_table = _build_codes(freq)
    out = "".join(code_table[b] for b in data_bytes)
    return out, code_table
