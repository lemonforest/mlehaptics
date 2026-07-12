"""Class I — cyclic-group / modular-arithmetic primitive.

Public Python surface for the six load-bearing modular-arithmetic
operations that underlie cyclic-cascade composition. Each operation
dispatches to the native C implementation when ``srmech.amsc._native``
loaded successfully (``HAS_NATIVE = True``) and falls back to a
pure-Python implementation otherwise. Both paths produce byte-exact
identical results — pinned by ``tests/test_cyclic_parity.py``.

Class I appears in Spike #24's cumulative cross-substrate audit at five
of six bonus substrates (tactical / SHA-256 / MFO 3+7+1 / RNG / cascade
composition); it is the foundation primitive for Task #218 Phase C2's
cascade-composition operations.

API
---

- :func:`gcd` — Euclidean greatest common divisor.
- :func:`lcm` — least common multiple (overflow-checked).
- :func:`mod_add` — ``(a + b) mod n``.
- :func:`mod_mul` — ``(a * b) mod n`` (overflow-safe via russian-peasant in C; Python's arbitrary-precision int handles this trivially in fallback).
- :func:`mod_pow` — ``a ** k mod n`` via square-and-multiply.
- :func:`mod_inv` — modular inverse via extended Euclidean (raises ``ValueError`` if no inverse exists).

All inputs are non-negative ``int`` (Python) / ``uint64`` (C). The
native C surface is bounded by ``uint64`` range; the pure-Python
fallback inherits Python's arbitrary-precision semantics but the
parity test exercises only ``uint64`` inputs to keep the two paths
byte-exact.
"""

from __future__ import annotations

import ctypes

from . import _native

__all__ = [
    "gcd",
    "lcm",
    "mod_add",
    "mod_mul",
    "mod_pow",
    "mod_inv",
    "three_cycle",
]


def three_cycle(value: int) -> int:
    """Harmonic-3 Z/3 cyclic shift (F150): the order-3 generator on Z/3 —
    ``(value + 1) % 3``. ``value`` is any non-negative int, read mod 3 (so the
    three residue classes 0/1/2 cycle 0→1→2→0). Class I is harmonic-3 (chiral
    rotation) per F150 §6.1; applying ``three_cycle`` THREE times is the
    identity on each residue (period 3) — the order-3 triality companion to the
    modular Class-I primitives.
    """
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"value must be int; got {type(value).__name__}")
    if value < 0:
        raise ValueError(f"three_cycle: value must be non-negative; got {value}")
    if (
        _native.HAS_NATIVE
        and _native.LIB is not None
        and hasattr(_native.LIB, "srmech_three_cycle")
        and value <= 0xFFFF_FFFF_FFFF_FFFF
    ):
        out = ctypes.c_uint64(0)
        rc = _native.LIB.srmech_three_cycle(
            ctypes.c_uint64(value),
            ctypes.byref(out),
        )
        if rc != _native.SRMECH_OK:
            raise RuntimeError(
                f"srmech_three_cycle returned non-OK status {rc}"
            )
        return int(out.value)
    return (value + 1) % 3


def _ensure_uint64(name: str, value: int) -> int:
    if not isinstance(value, int):
        raise TypeError(f"{name} must be int, got {type(value).__name__}")
    if value < 0:
        raise ValueError(f"{name} must be non-negative; got {value}")
    if value > 0xFFFF_FFFF_FFFF_FFFF:
        raise ValueError(
            f"{name} exceeds uint64 range; got {value} "
            f"(parity surface is bounded by 2^64 - 1)"
        )
    return value


_UINT64_MAX = 0xFFFF_FFFF_FFFF_FFFF

# 0.9.0rc167 (#765): the size-adaptive threshold (max operand bit-length) at
# which the beyond-u64 gcd dispatches to srmech's own C bignum Euclid
# (`_native.bigint_gcd_c`) instead of the pure-Python loop. Attested-to-
# measurement — see the comment at the dispatch site in `gcd` below.
_GCD_NATIVE_MIN_BITS: int = 1024


def gcd(a: int, b: int) -> int:
    """Class-I Euclidean GCD. ``gcd(0, 0)`` is ``0``; ``gcd(a, 0)`` is ``a``.

    **No upper cap (arbitrary precision).** The native C ``srmech_gcd`` serves
    its representable domain (``uint64``); inputs beyond ``2⁶⁴-1`` (e.g. the
    ~100-digit numerators of ``One``-scale rationals) take the big-int Euclid
    below — the *complete* pure-Python alternative, not a fallback. Removing the
    compiled-in ``2⁶⁴`` rejection is the standalone-honor "no compiled-in caps"
    discipline (`[[feedback_c_must_be_standalone_complete_no_python_fallback]]`,
    `[[project_c_standalone_honor_drift_backlog]]`): a fixed-width-int's full
    domain IS its width; arbitrary precision is a different numeric domain the
    pure path owns. Non-negative integer domain (gcd of magnitudes)."""
    if not isinstance(a, int) or not isinstance(b, int):
        raise TypeError("gcd: a and b must be int")
    if a < 0 or b < 0:
        raise ValueError(f"gcd: a and b must be non-negative; got {a}, {b}")
    if (_native.HAS_NATIVE and _native.LIB is not None
            and a <= _UINT64_MAX and b <= _UINT64_MAX):
        out = ctypes.c_uint64(0)
        rc = _native.LIB.srmech_gcd(
            ctypes.c_uint64(a),
            ctypes.c_uint64(b),
            ctypes.byref(out),
        )
        if rc != _native.SRMECH_OK:
            raise RuntimeError(f"srmech_gcd returned non-OK status {rc}")
        return int(out.value)
    # 0.9.0rc167 (#765): at/above the measured threshold the whole Euclid loop
    # runs on srmech's own caller-arena C bignum (`srmech_bigint_gcd`),
    # byte-identical (gcd is unique). Attested-to-measurement (Class B): WSL2
    # gcc -O2, Python 3.12, binary limb marshal — BELOW 1024 bits the native
    # loop LOSES (0.36–0.73× at 128–512 bits: call + marshal overhead); from
    # 1024 bits up it is measured COST-PARITY (0.85–1.22× across 1k–65k bits —
    # the per-iteration `a % b` in the pure loop is already CPython's C
    # divmod, so there is no interpreter-loop win to harvest). 1024 is the
    # parity onset; dispatching above it buys the #765 self-hosting substrate
    # at ≈cost-neutral. Measured table: tests/test_q_native_dispatch_rc167.py
    # + CHANGELOG 0.9.0rc167. The pure loop below stays the complete
    # below-threshold / no-native alternative.
    if _GCD_NATIVE_MIN_BITS <= max(a.bit_length(), b.bit_length()):
        g = _native.bigint_gcd_c(a, b)
        if g is not None:
            return g
    while b != 0:
        a, b = b, a % b
    return a


def lcm(a: int, b: int) -> int:
    """LCM via ``a / gcd(a, b) * b``. Raises ``OverflowError`` if the
    result exceeds uint64 range (matches the C side's ERR_OVERFLOW).
    """
    a = _ensure_uint64("a", a)
    b = _ensure_uint64("b", b)
    if _native.HAS_NATIVE and _native.LIB is not None:
        out = ctypes.c_uint64(0)
        rc = _native.LIB.srmech_lcm(
            ctypes.c_uint64(a),
            ctypes.c_uint64(b),
            ctypes.byref(out),
        )
        if rc == _native.SRMECH_ERR_OVERFLOW:
            raise OverflowError(
                f"srmech_lcm({a}, {b}) overflows uint64"
            )
        if rc != _native.SRMECH_OK:
            raise RuntimeError(f"srmech_lcm returned non-OK status {rc}")
        return int(out.value)
    if a == 0 or b == 0:
        return 0
    g = gcd(a, b)
    a_over_g = a // g
    result = a_over_g * b
    if result > 0xFFFF_FFFF_FFFF_FFFF:
        raise OverflowError(f"lcm({a}, {b}) overflows uint64")
    return result


def mod_add(a: int, b: int, n: int) -> int:
    """``(a + b) mod n``. Raises ``ValueError`` if ``n == 0``."""
    a = _ensure_uint64("a", a)
    b = _ensure_uint64("b", b)
    n = _ensure_uint64("n", n)
    if n == 0:
        raise ValueError("mod_add requires n > 0")
    if _native.HAS_NATIVE and _native.LIB is not None:
        out = ctypes.c_uint64(0)
        rc = _native.LIB.srmech_mod_add(
            ctypes.c_uint64(a),
            ctypes.c_uint64(b),
            ctypes.c_uint64(n),
            ctypes.byref(out),
        )
        if rc != _native.SRMECH_OK:
            raise RuntimeError(f"srmech_mod_add returned non-OK status {rc}")
        return int(out.value)
    return (a + b) % n


def mod_mul(a: int, b: int, n: int) -> int:
    """``(a * b) mod n``. Raises ``ValueError`` if ``n == 0``."""
    a = _ensure_uint64("a", a)
    b = _ensure_uint64("b", b)
    n = _ensure_uint64("n", n)
    if n == 0:
        raise ValueError("mod_mul requires n > 0")
    if _native.HAS_NATIVE and _native.LIB is not None:
        out = ctypes.c_uint64(0)
        rc = _native.LIB.srmech_mod_mul(
            ctypes.c_uint64(a),
            ctypes.c_uint64(b),
            ctypes.c_uint64(n),
            ctypes.byref(out),
        )
        if rc != _native.SRMECH_OK:
            raise RuntimeError(f"srmech_mod_mul returned non-OK status {rc}")
        return int(out.value)
    return (a * b) % n


def mod_pow(a: int, k: int, n: int) -> int:
    """``a ** k mod n`` via square-and-multiply. Raises ``ValueError``
    if ``n == 0``. Returns ``0`` for ``n == 1`` (everything is 0 mod 1).
    """
    a = _ensure_uint64("a", a)
    k = _ensure_uint64("k", k)
    n = _ensure_uint64("n", n)
    if n == 0:
        raise ValueError("mod_pow requires n > 0")
    if _native.HAS_NATIVE and _native.LIB is not None:
        out = ctypes.c_uint64(0)
        rc = _native.LIB.srmech_mod_pow(
            ctypes.c_uint64(a),
            ctypes.c_uint64(k),
            ctypes.c_uint64(n),
            ctypes.byref(out),
        )
        if rc != _native.SRMECH_OK:
            raise RuntimeError(f"srmech_mod_pow returned non-OK status {rc}")
        return int(out.value)
    return pow(a, k, n)


def mod_inv(a: int, n: int) -> int:
    """Modular inverse via extended Euclidean. Raises ``ValueError`` if
    no inverse exists (``gcd(a, n) != 1``) or if ``n in {0, 1}``.

    The native C surface is bounded by ``n <= INT64_MAX`` (the
    int64 intermediates used in extended Euclidean). The pure-Python
    fallback uses Python's built-in ``pow(a, -1, n)`` which has no
    such bound. Parity tests exercise only ``n <= INT64_MAX``.
    """
    a = _ensure_uint64("a", a)
    n = _ensure_uint64("n", n)
    if n in (0, 1):
        raise ValueError(f"mod_inv requires n >= 2; got {n}")
    if _native.HAS_NATIVE and _native.LIB is not None:
        out = ctypes.c_uint64(0)
        rc = _native.LIB.srmech_mod_inv(
            ctypes.c_uint64(a),
            ctypes.c_uint64(n),
            ctypes.byref(out),
        )
        if rc == _native.SRMECH_ERR_BAD_INPUT:
            raise ValueError(
                f"mod_inv({a}, {n}): no inverse (gcd != 1)"
            )
        if rc == _native.SRMECH_ERR_OVERFLOW:
            raise OverflowError(
                f"mod_inv({a}, {n}): n exceeds INT64_MAX for C path"
            )
        if rc != _native.SRMECH_OK:
            raise RuntimeError(f"srmech_mod_inv returned non-OK status {rc}")
        return int(out.value)
    try:
        return pow(a, -1, n)
    except ValueError as exc:
        raise ValueError(f"mod_inv({a}, {n}): no inverse (gcd != 1)") from exc
