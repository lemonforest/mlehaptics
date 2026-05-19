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

from typing import Dict, List, Optional, Tuple

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
