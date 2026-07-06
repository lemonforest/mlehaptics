"""Path A arithmetic coding — closed-form Class N rational interval narrowing.

Identity per the implementation plan §1: arithmetic coding IS a Class N
(rational ``[lo/q, hi/q)`` interval) narrowing operation; each symbol shrinks
the rational interval per the symbol's probability mass.

The closed-form reference implements integer-arithmetic coding (range coder)
with rational probability ratios; encode/decode round-trip is bit-exact.

Path B dual in Phase 6 (Path B Class N rational interval as bound vectors).

Canonical SSoT per ``[[feedback_science_is_ssot_not_project]]``: Rissanen
(1976) + Witten, Neal & Cleary (1987) *Arithmetic Coding for Data
Compression* CACM 30(6).
"""

from __future__ import annotations

import ctypes
from typing import Dict, List, Optional, Tuple

from srmech.amsc import _native

OPERATION_NAME = "arithmetic_coding"
CLASS_COMPOSITION = ("N",)
PERFORMANCE_HINT = "small-D-one-shot"
SSOT_CITATION = (
    "Rissanen (1976), 'Generalized Kraft inequality and arithmetic coding', "
    "IBM J. Res. Dev. 20(3), 198-203. Witten, Neal & Cleary (1987), "
    "'Arithmetic coding for data compression', Commun. ACM 30(6), 520-540. "
    "DOI 10.1145/214762.214771 (Crossref)."
)


def _cumulative(freq: Dict[int, int]) -> Tuple[Dict[int, Tuple[int, int]], int]:
    """Return (cum_table, total) where cum_table[sym] = (lo_cum, hi_cum)."""
    total = 0
    table: Dict[int, Tuple[int, int]] = {}
    for sym in sorted(freq):
        f = freq[sym]
        table[sym] = (total, total + f)
        total += f
    return table, total


def _encode_native(data_bytes, cum, total):
    """Native exact-rational encode → the narrowed ``(lo, hi)`` Fraction pair
    (byte-identical to the pure ``fractions.Fraction`` encode) or ``None`` (rc144
    §B6b). The C peer carries a COMMON DENOMINATOR ``total**k`` so the whole
    interval-narrowing loop is exact ``srmech_bigint`` integer arithmetic + a
    single terminal gcd reduction; a reduced fraction is canonical, so the
    ``(num, den)`` pair equals the Python Fraction exactly. Returns ``None`` (→
    pure) on an out-of-table symbol (the pure path raises the same ValueError),
    an unbuildable total, or an arena overflow on a pathologically long input."""
    from fractions import Fraction

    if not _native.has_native_arithmetic_encode():
        return None
    n = len(data_bytes)
    if n == 0 or total <= 0 or total >= (1 << 63):
        return None
    clo = (ctypes.c_uint32 * n)()
    chi = (ctypes.c_uint32 * n)()
    for i, b in enumerate(data_bytes):
        cc = cum.get(b)
        if cc is None:                        # out-of-table symbol → pure raises
            return None
        clo[i], chi[i] = cc[0], cc[1]
    lt = max(1, (int(total).bit_length() + 31) // 32)
    cap = lt * n + 16
    words = 24 * cap + 1024
    str_cap = cap * 10 + 32
    ws = (ctypes.c_uint32 * words)()
    lo_num = ctypes.create_string_buffer(str_cap)
    lo_den = ctypes.create_string_buffer(str_cap)
    hi_num = ctypes.create_string_buffer(str_cap)
    hi_den = ctypes.create_string_buffer(str_cap)
    lnl, lnd = ctypes.c_size_t(0), ctypes.c_size_t(0)
    hnl, hnd = ctypes.c_size_t(0), ctypes.c_size_t(0)
    rc = _native.LIB.srmech_arithmetic_encode(
        clo, chi, ctypes.c_uint32(n), ctypes.c_uint64(total),
        lo_num, lo_den, hi_num, hi_den, ctypes.c_size_t(str_cap),
        ctypes.byref(lnl), ctypes.byref(lnd), ctypes.byref(hnl), ctypes.byref(hnd),
        ctypes.cast(ws, ctypes.c_void_p), ctypes.c_size_t(words * 4))
    if rc != _native.SRMECH_OK:
        return None
    lo = Fraction(int(lo_num.value.decode("ascii")), int(lo_den.value.decode("ascii")))
    hi = Fraction(int(hi_num.value.decode("ascii")), int(hi_den.value.decode("ascii")))
    return lo, hi


def op(
    data,
    *,
    decode: bool = False,
    freq: Optional[Dict[int, int]] = None,
    length: Optional[int] = None,
    D: int = 8192,
):
    """Arithmetic encode or decode using integer rational-interval narrowing.

    Phase 2 ships the simplest closed-form reference: rational-interval
    narrowing using Python ``fractions.Fraction``. The output is a fraction
    in the final narrowed interval; decode parses the fraction back into
    symbols via the same frequency table.

    Parameters
    ----------
    data:
        Bytes-like (encode) or Fraction-or-tuple (decode).
    decode:
        If True, decode using ``freq`` + ``length``.
    freq:
        Symbol frequency table (required for both encode + decode).
    length:
        Number of symbols to decode (required for decode).
    D:
        Path B dimensionality (Path A unused).

    Returns
    -------
    Encode: ``(lo, hi, freq)`` — narrowed rational interval as Fraction pair.
    Decode: ``bytes`` of recovered symbols.
    """
    from fractions import Fraction

    if decode:
        if freq is None or length is None:
            raise ValueError(
                "arithmetic_coding decode requires 'freq' and 'length'"
            )
        cum, total = _cumulative(freq)
        # data should be a Fraction representing a point in [lo, hi)
        if isinstance(data, tuple) and len(data) == 2:
            point = (Fraction(data[0]) + Fraction(data[1])) / 2
        else:
            point = Fraction(data)
        out = bytearray()
        lo = Fraction(0)
        hi = Fraction(1)
        for _ in range(length):
            span = hi - lo
            # Find which symbol's cum range contains (point - lo) / span * total
            target = (point - lo) * total / span
            chosen_sym = None
            for sym, (c_lo, c_hi) in cum.items():
                if Fraction(c_lo) <= target < Fraction(c_hi):
                    chosen_sym = sym
                    break
            if chosen_sym is None:
                # Edge: target == total; pick last
                chosen_sym = max(cum.keys())
            out.append(chosen_sym & 0xFF)
            c_lo, c_hi = cum[chosen_sym]
            new_lo = lo + span * Fraction(c_lo, total)
            new_hi = lo + span * Fraction(c_hi, total)
            lo, hi = new_lo, new_hi
        return bytes(out)

    # Encode
    if freq is None:
        if isinstance(data, str):
            data = data.encode("utf-8")
        data_bytes = bytes(data)
        freq = {}
        for b in data_bytes:
            freq[b] = freq.get(b, 0) + 1
    else:
        if isinstance(data, str):
            data = data.encode("utf-8")
        data_bytes = bytes(data)
    cum, total = _cumulative(freq)
    native = _encode_native(data_bytes, cum, total)     # rc144 §B6b
    if native is not None:
        return native[0], native[1], dict(freq)
    lo = Fraction(0)
    hi = Fraction(1)
    for b in data_bytes:
        if b not in cum:
            raise ValueError(f"symbol {b} not in frequency table")
        c_lo, c_hi = cum[b]
        span = hi - lo
        new_lo = lo + span * Fraction(c_lo, total)
        new_hi = lo + span * Fraction(c_hi, total)
        lo, hi = new_lo, new_hi
    return lo, hi, dict(freq)
