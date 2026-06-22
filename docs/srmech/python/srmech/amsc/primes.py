"""Class J — prime-factorisation / period primitive (Task #217 Phase C1).

Public Python surface for three integer-structure operations
complementing Class I (modular arithmetic):

- :func:`is_prime` — trial-division primality test.
- :func:`factor` — prime factorisation returning ``[(p, e), ...]``.
- :func:`cyclic_period` — multiplicative order of ``a`` in
  ``(Z/nZ)*`` (smallest ``k > 0`` with ``a^k ≡ 1 mod n``).

Each operation dispatches to the native C implementation when
``srmech.amsc._native`` loaded successfully (``HAS_NATIVE = True``)
and falls back to a pure-Python implementation otherwise. Both paths
produce byte-exact identical results — pinned by
``tests/test_primes_parity.py``.

All inputs are non-negative ``int`` (Python) / ``uint64`` (C). Class J
is integer-only; no numpy dependency at this module level.
"""

from __future__ import annotations

import ctypes
from typing import List, Tuple

from . import _native
from .cyclic import gcd as _gcd

__all__ = [
    "is_prime",
    "factor",
    "cyclic_period",
    "FACTOR_MAX_DISTINCT_PRIMES",
]

# uint64 max distinct prime factors: product of first 15 primes
# (2*3*5*7*11*13*17*19*23*29*31*37*41*43*47) = 6.14e17 < 2^64 < product
# of first 16. So uint64 has at most 15 distinct prime factors; 64 is
# a comfortable upper bound.
FACTOR_MAX_DISTINCT_PRIMES: int = 64


def _ensure_uint64(name: str, value: int) -> int:
    if not isinstance(value, int):
        raise TypeError(f"{name} must be int, got {type(value).__name__}")
    if value < 0:
        raise ValueError(f"{name} must be non-negative; got {value}")
    if value > 0xFFFF_FFFF_FFFF_FFFF:
        raise ValueError(
            f"{name} exceeds uint64 range; got {value}"
        )
    return value


def is_prime(n: int) -> bool:
    """Return True iff ``n`` is prime.

    Trial division up to ``sqrt(n)``; bounded for ``uint64`` inputs.
    """
    n = _ensure_uint64("n", n)
    if _native.HAS_NATIVE and _native.LIB is not None:
        out = ctypes.c_bool(False)
        rc = _native.LIB.srmech_is_prime(
            ctypes.c_uint64(n), ctypes.byref(out)
        )
        if rc != _native.SRMECH_OK:
            raise RuntimeError(f"srmech_is_prime returned non-OK status {rc}")
        return bool(out.value)
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0:
        return False
    d = 3
    while d * d <= n:
        if n % d == 0:
            return False
        d += 2
    return True


def factor(n: int) -> List[Tuple[int, int]]:
    """Return ``[(p_1, e_1), (p_2, e_2), ...]`` with ``n = ∏ p_i^e_i``.

    Primes are sorted ascending. Returns ``[]`` for ``n < 2``. Raises
    ``OverflowError`` if the C path's fixed buffer (`FACTOR_MAX_DISTINCT_PRIMES`)
    is exceeded; this cannot happen for valid ``uint64`` inputs (≤15
    distinct primes) but the safety guard is documented.
    """
    n = _ensure_uint64("n", n)
    if _native.HAS_NATIVE and _native.LIB is not None:
        primes = (ctypes.c_uint64 * FACTOR_MAX_DISTINCT_PRIMES)()
        exps = (ctypes.c_uint8 * FACTOR_MAX_DISTINCT_PRIMES)()
        count = ctypes.c_uint32(0)
        rc = _native.LIB.srmech_factor(
            ctypes.c_uint64(n),
            primes,
            exps,
            ctypes.c_uint32(FACTOR_MAX_DISTINCT_PRIMES),
            ctypes.byref(count),
        )
        if rc == _native.SRMECH_ERR_OVERFLOW:
            raise OverflowError(
                f"factor({n}): exceeds FACTOR_MAX_DISTINCT_PRIMES "
                f"= {FACTOR_MAX_DISTINCT_PRIMES}"
            )
        if rc != _native.SRMECH_OK:
            raise RuntimeError(f"srmech_factor returned non-OK status {rc}")
        return [(int(primes[i]), int(exps[i])) for i in range(count.value)]
    if n < 2:
        return []
    result: List[Tuple[int, int]] = []
    if n % 2 == 0:
        e = 0
        while n % 2 == 0:
            n //= 2
            e += 1
        result.append((2, e))
    d = 3
    while d * d <= n:
        if n % d == 0:
            e = 0
            while n % d == 0:
                n //= d
                e += 1
            result.append((d, e))
        d += 2
    if n > 1:
        result.append((int(n), 1))
    return result


def cyclic_period(a: int, n: int, max_k: int = 0) -> int:
    """Return the multiplicative order of ``a`` in ``(Z/nZ)*``.

    The smallest ``k > 0`` with ``a^k ≡ 1 (mod n)``. Requires
    ``gcd(a mod n, n) == 1`` and ``n >= 2``; raises ``ValueError``
    otherwise.

    ``max_k`` caps the trial iteration. ``0`` (default) means "use
    ``n`` as the bound" (Lagrange's theorem: order divides ``φ(n) ≤ n``,
    so this is always sufficient).

    Raises ``OverflowError`` if the period exceeds ``max_k`` (the C
    path raises ``SRMECH_ERR_OVERFLOW`` in this case).
    """
    a = _ensure_uint64("a", a)
    n = _ensure_uint64("n", n)
    max_k = _ensure_uint64("max_k", max_k)
    if n < 2:
        raise ValueError(f"cyclic_period requires n >= 2; got {n}")
    if _gcd(a % n, n) != 1:
        raise ValueError(
            f"cyclic_period({a}, {n}): gcd != 1; a not in (Z/nZ)*"
        )
    if max_k == 0:
        max_k = n
    if _native.HAS_NATIVE and _native.LIB is not None:
        out = ctypes.c_uint64(0)
        rc = _native.LIB.srmech_cyclic_period(
            ctypes.c_uint64(a),
            ctypes.c_uint64(n),
            ctypes.c_uint64(max_k),
            ctypes.byref(out),
        )
        if rc == _native.SRMECH_ERR_OVERFLOW:
            raise OverflowError(
                f"cyclic_period({a}, {n}): period > max_k = {max_k}"
            )
        if rc != _native.SRMECH_OK:
            raise RuntimeError(
                f"srmech_cyclic_period returned non-OK status {rc}"
            )
        return int(out.value)
    a_mod = a % n
    cur = 1
    for k in range(1, int(max_k) + 1):
        cur = (cur * a_mod) % n
        if cur == 1:
            return k
    raise OverflowError(f"cyclic_period({a}, {n}): period > max_k = {max_k}")
