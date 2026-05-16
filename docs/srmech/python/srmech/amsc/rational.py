"""Class N — rational-approximation primitive (Task #217 Phase C1).

Two operations:

- :func:`continued_fraction(p, q)` — simple continued-fraction expansion
  of ``p/q`` as a list of integer terms ``[a_0, a_1, a_2, ...]``.
- :func:`best_rational(p, q, max_denominator)` — best rational
  ``p'/q'`` with ``q' <= max_denominator`` approximating ``p/q`` via
  continued-fraction convergents.

Class N is the third pure-integer primitive (after I — modular
arithmetic, J — prime factorisation / period). All operations on
``uint64`` inputs; native C path via ``srmech_rational.c`` with
pure-Python fallback.
"""

from __future__ import annotations

import ctypes
from typing import List, Tuple

from . import _native

__all__ = ["continued_fraction", "best_rational"]

# Max terms a uint64 continued fraction can produce is Fibonacci-worst-
# case ~91 iterations; 128 is the C-side cap and a safe Python ceiling.
_MAX_TERMS: int = 128


def _ensure_uint64(name: str, value: int) -> int:
    if not isinstance(value, int):
        raise TypeError(f"{name} must be int; got {type(value).__name__}")
    if value < 0:
        raise ValueError(f"{name} must be non-negative; got {value}")
    if value > 0xFFFF_FFFF_FFFF_FFFF:
        raise ValueError(f"{name} exceeds uint64 range; got {value}")
    return value


def continued_fraction(numerator: int, denominator: int) -> List[int]:
    """Return the simple continued-fraction expansion of ``p/q``.

    For ``p/q = [a_0; a_1, a_2, ...]``, returns ``[a_0, a_1, a_2, ...]``.
    Raises ``ValueError`` if ``denominator == 0``.

    Both C and Python paths produce byte-exact identical results;
    pinned by ``tests/test_rational_parity.py``.
    """
    p = _ensure_uint64("numerator", numerator)
    q = _ensure_uint64("denominator", denominator)
    if q == 0:
        raise ValueError("continued_fraction requires denominator > 0")
    if _native.HAS_NATIVE and _native.LIB is not None:
        terms = (ctypes.c_uint64 * _MAX_TERMS)()
        out_count = ctypes.c_uint32(0)
        rc = _native.LIB.srmech_continued_fraction(
            ctypes.c_uint64(p),
            ctypes.c_uint64(q),
            terms,
            ctypes.c_uint32(_MAX_TERMS),
            ctypes.byref(out_count),
        )
        if rc != _native.SRMECH_OK:
            raise RuntimeError(
                f"srmech_continued_fraction returned non-OK status {rc}"
            )
        return [int(terms[i]) for i in range(out_count.value)]
    # Pure-Python fallback: Euclidean expansion.
    result: List[int] = []
    while q != 0:
        result.append(p // q)
        p, q = q, p % q
    return result


def best_rational(numerator: int,
                  denominator: int,
                  max_denominator: int) -> Tuple[int, int]:
    """Return the best rational ``(p', q')`` with ``q' <= max_denominator``
    approximating ``numerator / denominator``.

    Uses continued-fraction convergents (Stern-Brocot path through the
    mediant tree). Returns ``(0, 1)`` if no non-trivial convergent fits
    within ``max_denominator``. Raises ``ValueError`` for invalid inputs.

    Both C and Python paths produce byte-exact identical results;
    pinned by ``tests/test_rational_parity.py``.
    """
    p = _ensure_uint64("numerator", numerator)
    q = _ensure_uint64("denominator", denominator)
    max_q = _ensure_uint64("max_denominator", max_denominator)
    if q == 0:
        raise ValueError("best_rational requires denominator > 0")
    if max_q == 0:
        raise ValueError("best_rational requires max_denominator > 0")
    if _native.HAS_NATIVE and _native.LIB is not None:
        out_p = ctypes.c_uint64(0)
        out_q = ctypes.c_uint64(0)
        rc = _native.LIB.srmech_best_rational(
            ctypes.c_uint64(p),
            ctypes.c_uint64(q),
            ctypes.c_uint64(max_q),
            ctypes.byref(out_p),
            ctypes.byref(out_q),
        )
        if rc != _native.SRMECH_OK:
            raise RuntimeError(
                f"srmech_best_rational returned non-OK status {rc}"
            )
        return int(out_p.value), int(out_q.value)
    # Pure-Python fallback: walk convergents.
    h_prev, h_curr = 1, 0
    k_prev, k_curr = 0, 1
    best_p, best_q = 0, 1
    while q != 0:
        a = p // q
        # Overflow guard mirrors the C path.
        if h_prev > 0 and a > (0xFFFF_FFFF_FFFF_FFFF - h_curr) // h_prev:
            break
        if k_prev > 0 and a > (0xFFFF_FFFF_FFFF_FFFF - k_curr) // k_prev:
            break
        h_next = a * h_prev + h_curr
        k_next = a * k_prev + k_curr
        if k_next > max_q:
            break
        best_p, best_q = h_next, k_next
        h_curr, h_prev = h_prev, h_next
        k_curr, k_prev = k_prev, k_next
        p, q = q, p % q
    return best_p, best_q
