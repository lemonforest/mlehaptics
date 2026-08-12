"""Class I — cyclic-group / modular-arithmetic primitive.

Public Python surface for the six load-bearing modular-arithmetic
operations that underlie cyclic-cascade composition. Each operation
dispatches to the native C implementation when ``srmech._native``
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
- :func:`bigint_mul` — the Class-I family's **uncapped** integer product
  ``a * b`` (arbitrary precision) routed through srmech's own C bignum
  ``srmech_bigint_mul``; the building block the wide modular multiply composes.
- :func:`mod_mul_wide` — ``(a * b) mod n`` with **no uint64 cap** (the
  128-bit-capable modular multiply; e.g. the PCG64 LCG step at ``n = 2**128``),
  the product taken on the C bignum and reduced mod ``n``.

The six capped operations (``gcd``/``lcm``/``mod_add``/``mod_mul``/``mod_pow``/
``mod_inv``) take non-negative ``int`` (Python) / ``uint64`` (C); the native C
surface is bounded by ``uint64`` range and the pure-Python fallback inherits
Python's arbitrary-precision semantics, but the parity test exercises only
``uint64`` inputs to keep the two paths byte-exact. ``mod_mul`` in particular is
deliberately capped: it binds the fixed-64-bit ABI ``srmech_mod_mul`` and MUST
stay so — :func:`mod_mul_wide` is the uncapped companion, not a widening of the
guard. It is ERGONOMIC packaging of an existing capability (the raw
``srmech_bigint_mul`` product + a Python reduce), not a new one.
"""

from __future__ import annotations

import ctypes

from .. import _native

__all__ = [
    "gcd",
    "lcm",
    "mod_add",
    "mod_mul",
    "mod_pow",
    "mod_inv",
    "bigint_mul",
    "mod_mul_wide",
    "three_cycle",
    "primitive_integer_vector",
    "mod_mul_arrow",
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


def bigint_mul(a: int, b: int) -> int:
    """The Class-I family's **uncapped** integer product ``a * b``.

    Unlike :func:`mod_mul` (bounded by the fixed-64-bit ABI ``srmech_mod_mul``),
    this is the arbitrary-precision multiply: it dispatches the product to
    srmech's OWN caller-arena C bignum (``srmech_bigint_mul`` / the rc168
    Karatsuba-arena entry) via ``_native.bigint_mul_c`` when the native library
    is present, and falls back to CPython's arbitrary-precision ``a * b``
    (itself a C ``PyLong`` multiply) — the COMPLETE alternative — otherwise.
    Byte-identical both ways (the integer product is unique).

    This is the building block the wide modular multiply composes: a modular
    cascade over a > 64-bit modulus (the PCG64 128-bit LCG step) needs the raw
    product before the mod-reduce, and that product must not overflow a
    fixed-width register. srmech ships its own bignum in C precisely so this
    stays a C path with NO Python-bignum dependency (the standalone-C
    self-hosting discipline).

    Args:
        a: an ``int`` (signed; ``srmech_bigint`` carries the sign).
        b: an ``int`` (signed).

    Returns:
        The exact product ``a * b`` (arbitrary precision).

    Raises:
        TypeError: if ``a`` or ``b`` is not an ``int`` (``bool`` is rejected —
            it is a subclass of ``int`` but not a cyclic-arithmetic operand).
    """
    if type(a) is not int or type(b) is not int:
        raise TypeError(
            f"bigint_mul: a and b must be int (not bool); "
            f"got {type(a).__name__}, {type(b).__name__}"
        )
    if _native.HAS_NATIVE and _native.LIB is not None:
        prod = _native.bigint_mul_c(a, b)
        if prod is not None:
            return prod
    return a * b


def mod_mul_wide(a: int, b: int, n: int) -> int:
    """``(a * b) mod n`` with **no uint64 cap** — the 128-bit-capable multiply.

    The uncapped companion to :func:`mod_mul`. ``mod_mul`` is bounded to
    ``uint64`` because it binds the fixed-64-bit C ABI ``srmech_mod_mul``, and
    that guard is deliberate; ``mod_mul_wide`` does NOT weaken it. Instead it
    routes the product through :func:`bigint_mul` (srmech's own C bignum,
    ``srmech_bigint_mul``) and reduces the result mod ``n``. So it is a
    ``composition_of_c`` op — packaging the EXISTING bignum-multiply capability
    for wide moduli, not inventing a new one.

    Worked instance — the raw PCG64 LCG step is
    ``state <- (state * MULT + INC) mod 2**128``: the multiply-and-reduce half
    is exactly ``mod_mul_wide(state, MULT, 2**128)``. (numpy's PCG64 default
    multiplier ``0x2360ed051fc65da44385df649fccf645`` overflows any 64-bit
    register, so the capped ``mod_mul`` cannot express it — this can.)

    Args:
        a: a non-negative ``int`` of ANY width (e.g. a 128-bit LCG state).
        b: a non-negative ``int`` of ANY width (e.g. a 128-bit multiplier).
        n: the modulus, a positive ``int`` of ANY width (e.g. ``2**128``).

    Returns:
        ``(a * b) mod n`` in ``[0, n)``.

    Raises:
        TypeError: if any argument is not an ``int`` (``bool`` rejected).
        ValueError: if ``n <= 0`` or if ``a`` / ``b`` is negative.
    """
    for name, value in (("a", a), ("b", b), ("n", n)):
        if type(value) is not int:
            raise TypeError(
                f"mod_mul_wide: {name} must be int (not bool); "
                f"got {type(value).__name__}"
            )
    if n <= 0:
        raise ValueError(f"mod_mul_wide requires n > 0; got {n}")
    if a < 0 or b < 0:
        raise ValueError(
            f"mod_mul_wide: a and b must be non-negative; got {a}, {b}"
        )
    return bigint_mul(a, b) % n


# ──────────────────────────────────────────────────────────────────────────
# Class I ∘ K ∘ C — the smallest integer vector on a rational vector's ray
# (0.9.0rc378, `#T1049`). The keystone the chemistry domain (`#T1050`,
# balancing a reaction = the integer nullspace of the stoichiometric matrix)
# consumes: turn an exact ℚ-vector — e.g. a kernel column from
# ``QMat.nullspace`` (:meth:`srmech.math.qmat.QMat.nullspace`) — into the
# smallest integer vector pointing the SAME way, in the canonical
# first-nonzero-positive orientation.
# ──────────────────────────────────────────────────────────────────────────

_INT64_MIN = -(1 << 63)
_INT64_MAX = (1 << 63) - 1


# Class-K magnitude branch (``x if x >= 0 else -x``), NEVER the ALU ``abs``.
# Sign-flip IS the canonical Class-K pin-slot phase-boundary; this file's
# ``gcd`` takes non-negative operands, so the magnitude is re-applied here as
# a Class-K pin-slot ∘ Class-C reorient, matching ``_ipoly_primitive`` /
# ``_primitive`` in the cascade package (per
# ``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``).
def _pin_magnitude(x: int) -> int:
    return x if x >= 0 else -x


# Class-K pin-slot at zero → the orientation alone, in {-1, 0, +1}.
def _pin_orientation(x: int) -> int:
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


# Class-C reorient: re-apply a captured orientation (``-x`` for a negative
# orientation, ``x`` otherwise). No ``abs()``; the sign is the pin-slot.
def _reorient(x: int, orientation: int) -> int:
    return -x if orientation < 0 else x


def _lcm_uncapped(a: int, b: int) -> int:
    """LCM of two POSITIVE ints via the Class-I gcd, with NO uint64 cap.

    :func:`lcm` binds the fixed-64-bit ABI ``srmech_lcm`` and rejects operands
    (or a result) beyond ``2⁶⁴-1``; a ℚ-vector cleared of denominators from an
    exact ``QMat.nullspace`` grows bignum, so the vector op composes the
    arbitrary-precision :func:`gcd` directly — the SAME "uncapped companion to
    the capped scalar op" relationship :func:`mod_mul_wide` has to
    :func:`mod_mul`. Both ``a`` and ``b`` must be ``> 0``.
    """
    return a // gcd(a, b) * b


def _to_pairs(vec) -> "list[tuple[int, int]]":
    """Coerce the accepted input shapes to a list of ``(num, den)`` int pairs
    with every ``den > 0`` (a negative denominator's sign is folded into the
    numerator as a Class-K pin-slot ∘ Class-C reorient, never ``abs()``).

    Accepts a ``QMat`` row/column vector, a ``list``/``tuple`` of ``Q`` (or any
    object exposing ``.numerator`` / ``.denominator`` — ``Q``, ``Fraction``,
    plain ``int``), and a ``list``/``tuple`` of ``(num, den)`` pairs.
    """
    # Duck-typed QMat (avoid importing qmat → cyclic is imported by it).
    if hasattr(vec, "n_rows") and hasattr(vec, "n_cols"):
        n_rows, n_cols = vec.n_rows, vec.n_cols
        if n_rows != 1 and n_cols != 1:
            raise ValueError(
                "primitive_integer_vector: a QMat input must be a row or column "
                f"vector; got shape {(n_rows, n_cols)}"
            )
        entries = [entry for row in vec for entry in row]
    elif isinstance(vec, (list, tuple)):
        entries = list(vec)
    else:
        raise TypeError(
            "primitive_integer_vector: input must be a QMat vector, a list of Q "
            f"(or int / Fraction), or a list of (num, den) pairs; got "
            f"{type(vec).__name__}"
        )

    pairs: "list[tuple[int, int]]" = []
    for e in entries:
        if isinstance(e, (tuple, list)):
            if len(e) != 2:
                raise ValueError(
                    "primitive_integer_vector: a pair entry must be (num, den); "
                    f"got a length-{len(e)} entry"
                )
            num, den = int(e[0]), int(e[1])
        else:
            enum = getattr(e, "numerator", None)
            eden = getattr(e, "denominator", None)
            if enum is None or eden is None:
                raise TypeError(
                    "primitive_integer_vector: each entry must be a Q / int / "
                    "Fraction (with .numerator/.denominator) or a (num, den) "
                    f"pair; got {type(e).__name__}"
                )
            num, den = int(enum), int(eden)
        if den == 0:
            raise ValueError(
                "primitive_integer_vector: a zero denominator is not a rational"
            )
        if den < 0:                       # Class-K pin-slot ∘ Class-C reorient
            num, den = _reorient(num, orientation=-1), _reorient(den, orientation=-1)
        pairs.append((num, den))
    return pairs


def _primitive_integer_vector_pure(pairs):
    """The complete, arbitrary-precision body: ``(cleared, content, primitive)``
    where ``cleared[i] == content * primitive[i]`` and ``cleared`` is the
    denominator-cleared integer vector ``L·v``."""
    # Class-I: clear denominators by the LCM of the (positive) denominators.
    denom_lcm = 1
    for _num, den in pairs:
        denom_lcm = _lcm_uncapped(denom_lcm, den)
    cleared = [num * (denom_lcm // den) for num, den in pairs]

    # Class-I: strip the content = gcd of the entry MAGNITUDES (Class-K).
    content_mag = 0
    for c in cleared:
        content_mag = gcd(content_mag, _pin_magnitude(c))
    if content_mag == 0:                          # the all-zero ray
        return cleared, 0, [0 for _ in cleared]

    # Class-K pin-slot ∘ Class-C reorient: first nonzero entry made positive.
    orientation = 1
    for c in cleared:
        o = _pin_orientation(c)
        if o != 0:
            orientation = o
            break
    primitive = [_reorient(c // content_mag, orientation=orientation)
                 for c in cleared]
    content_signed = _reorient(content_mag, orientation=orientation)
    return cleared, content_signed, primitive


def primitive_integer_vector(vec, *, with_content: bool = False):
    """The smallest integer vector on the same ray as an exact ℚ-vector.

    Turns a rational vector — a ``QMat`` row/column (what
    :meth:`srmech.math.qmat.QMat.nullspace` returns), a ``list`` of ``Q`` /
    ``int`` / ``Fraction``, or a ``list`` of ``(num, den)`` pairs — into the
    **primitive integer vector** (content 1) pointing the same way, in the
    canonical convention that the **first nonzero entry is positive**. The
    all-zero vector maps to all-zeros.

    This is the keystone the chemistry domain (`#T1050`, balancing a reaction =
    the integer nullspace of the stoichiometric matrix) consumes: a kernel
    column over ℚ becomes the integer stoichiometric coefficients.

    Algorithm — exact, integer-only, an A–N cascade with NO Python ``abs()``:

    1. **Clear denominators** (Class I): multiply through by the LCM of the
       denominators (composing the arbitrary-precision :func:`gcd`; see
       :func:`_lcm_uncapped` for why the uint64-capped :func:`lcm` is not used).
    2. **Strip content** (Class I): divide by the GCD of the entries'
       magnitudes → content 1.
    3. **Pin the sign** (Class K ∘ Class C): make the first nonzero entry
       positive — the canonical primitive-representative. Sign handling is the
       Class-K pin-slot + Class-C reorient, never ``abs()`` (per
       ``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``), mirroring
       ``_ipoly_primitive`` / ``_primitive`` in :mod:`srmech.cascade`.

    Args:
        vec: the rational vector (``QMat`` vector, ``list[Q]`` / ``list[int]`` /
            ``list[Fraction]``, or ``list[(num, den)]``).
        with_content: when ``True``, return ``(content_signed, primitive)`` with
            ``content_signed`` the signed integer such that
            ``content_signed * primitive[i]`` reconstructs the
            denominator-cleared integer vector ``L·v`` for every ``i`` (the
            reduction is reversible). ``content_signed`` carries the orientation
            so ``content_signed * primitive`` — not ``|content| * primitive`` —
            is the cleared vector, exactly as ``_ipoly_primitive`` returns.

    Returns:
        ``list[int]`` (the primitive integer vector), or
        ``(content_signed: int, primitive: list[int])`` when ``with_content``.

    Raises:
        TypeError: on an unsupported input shape / entry type.
        ValueError: on a QMat that is not a vector, a malformed pair, or a zero
            denominator.

    Dispatches to the native ``srmech_primitive_integer_vector`` when every
    entry fits the signed-int64 fast-path domain; the pure-Python body is the
    complete, byte-identical arbitrary-precision alternative (and the parity
    oracle) — a bignum entry, or an int64 intermediate overflow, takes it.
    """
    pairs = _to_pairs(vec)
    if not pairs:
        return (0, []) if with_content else []

    native = _primitive_integer_vector_c(pairs)
    if native is not None:
        content_signed, primitive = native
    else:
        _cleared, content_signed, primitive = _primitive_integer_vector_pure(pairs)
    return (content_signed, primitive) if with_content else primitive


_INT64_MIN = -(1 << 63)
_INT64_MAX = (1 << 63) - 1


def _primitive_integer_vector_c(pairs):
    """Native fast path over signed int64 num/den pairs → ``(content_signed,
    primitive)`` or ``None`` when the native symbol is absent OR any entry /
    intermediate leaves the int64 domain (the pure-Python body is the complete
    bignum fallback). ``INT64_MIN`` is excluded so every internal negation is
    representable."""
    if not _native.has_native_primitive_integer_vector():
        return None
    n = len(pairs)
    nums = [p[0] for p in pairs]
    dens = [p[1] for p in pairs]
    for v in nums:
        if v <= _INT64_MIN or v > _INT64_MAX:
            return None
    for v in dens:
        if v <= _INT64_MIN or v > _INT64_MAX:   # dens are already > 0 here
            return None
    num_arr = (ctypes.c_int64 * n)(*nums)
    den_arr = (ctypes.c_int64 * n)(*dens)
    out_arr = (ctypes.c_int64 * n)()
    out_content = ctypes.c_int64(0)
    rc = _native.LIB.srmech_primitive_integer_vector(
        ctypes.cast(num_arr, ctypes.POINTER(ctypes.c_int64)),
        ctypes.cast(den_arr, ctypes.POINTER(ctypes.c_int64)),
        ctypes.c_size_t(n),
        ctypes.cast(out_arr, ctypes.POINTER(ctypes.c_int64)),
        ctypes.byref(out_content),
    )
    if rc == _native.SRMECH_ERR_OVERFLOW:
        return None                              # bignum — pure path is exact
    if rc != _native.SRMECH_OK:
        raise RuntimeError(
            f"srmech_primitive_integer_vector returned non-OK status {rc}")
    return int(out_content.value), [int(out_arr[i]) for i in range(n)]


# ──────────────────────────────────────────────────────────────────────
# The DIRECTIONAL GENERATOR on Z/n — Class I (cyclic) then Class L
# (kernel / rank read).  rc427 (`#T1130`).
#
# CLASS NOTE, stated because the first spec got it wrong: this op was
# proposed as Class K.  It is not.  Class K is the SIGN-FLIP pin-slot, and
# nothing here flips a sign.  The shipped precedent for the SAME object —
# "what does multiply-by-a-fixed-element destroy" — is
# `srmech.cascade.left_mult_kernel`, which is Class L, and the quantity
# returned here is the same one: the ORDER of a kernel.  So: Class I for
# the modular arithmetic, then Class L for the kernel read.
# ──────────────────────────────────────────────────────────────────────

def mod_mul_arrow(c: int, n: int) -> "dict":
    """The eventual SHAPE of the self-map ``T_c(x) = (c·x) mod n`` — an
    ARROW on ℤ/n when ``gcd(c, n) > 1``, closed form, exact integers.

    ``T_c`` iterated is a finite semiflow: a TRANSIENT of ``index`` steps
    during which the image strictly shrinks, then a PERMUTATION of the
    surviving subgroup forever after.  This op returns both halves without
    iterating anything.

    Closed form (all integer, no search)::

        kernel_order    = gcd(c, n)
        index           = max over p | gcd(c, n) of ceil(v_p(n) / v_p(c))
        consumed_order  = prod over p | gcd(c, n) of p^v_p(n)
        eventual_modulus= n / consumed_order
        period          = cyclic_period(c mod m, m)   for m >= 2, else 1

    Args:
        c: the multiplier.  Read mod ``n``.
        n: the modulus, ``>= 2``.

    Returns:
        A dict with ``c`` · ``n`` · ``kernel_order`` (the order of
        ``ker T_c = {x : c·x ≡ 0}``, a subgroup) · ``index`` (the transient
        length; ``0`` iff ``T_c`` is already a permutation) · ``consumed_order``
        (the total order consumed over the whole transient, ``= g*``) ·
        ``eventual_modulus`` and ``eventual_size`` (both ``n / g*``; the
        surviving image is the stride-``g*`` subgroup) · ``period`` (the
        multiplicative order of ``c`` on that survivor) · ``is_permutation``.

    **What it deliberately does NOT return, and why.**  Each step destroys a
    COSET of ``ker T_c``.  srmech's shipped doctrine for a lossy op is CARRY
    THE COMPLEMENT (``lossy_projection_record``) — but applied to an arrow
    that doctrine ANNIHILATES it: measured, ``(image, coset index)``
    reconstructs the input bijectively, so an op that returns the coset index
    has no arrow left.  Legibility and irreversibility cannot both be
    maximised.  This op therefore reports the **shape and ORDER** of what was
    consumed and never the element: *"this step consumed a coset of an
    order-g subgroup"* is legible and still irreversible.

    **The gap this fills.**  ``srmech.math.primes.cyclic_period`` refuses a
    non-unit outright (``gcd != 1; a not in (Z/nZ)*``), so the eventual period
    of a non-unit multiplier was unreachable through shipped surface.  The
    ``n / g* == 1`` guard below is NOT decorative: every NILPOTENT multiplier
    lands there — ``mod_mul_arrow(2, 64)`` has ``g* = 64`` — and
    ``cyclic_period`` also refuses ``n < 2``.  A spec that omits the guard
    raises on its own headline example.

    Validated over every ``(n, c)`` with ``2 <= n <= 60``, ``0 <= c < n``
    (1,829 cells) against an independent enumeration oracle: 0 disagreements
    on index, period and eventual size, and the eventual image compared as a
    SET against ``g*·ℤ/n`` with 0 membership mismatches.

    Note:
        No ``abs()``; sign never arises (every quantity is a non-negative
        order).  Pure integer; no C peer (composition of shipped C peers).
    """
    c = _ensure_uint64("c", c)
    n = _ensure_uint64("n", n)
    if n < 2:
        raise ValueError(f"mod_mul_arrow requires n >= 2; got {n}")
    # Function-local because ``primes`` imports ``cyclic`` at module level; the
    # cycle is real and this is how the tree breaks it. Written ABSOLUTE rather
    # than as ``from .primes import …`` deliberately: the `composes` derivation
    # instrument (``tests/composes_derive.py:192``) resolves a function-local
    # ``ImportFrom`` only when ``not sub.level``, so a RELATIVE local import is
    # invisible to it and this op's two other declared sub-ops would read as
    # uncalled. The declaration is true either way; the absolute spelling is
    # what makes it CHECKABLE.
    from srmech.math.primes import cyclic_period, factor

    c %= n
    kernel_order = gcd(c, n)
    prime_powers = factor(n)
    index = 1 if c == 0 else 0
    consumed_order = n if c == 0 else 1
    if c != 0:
        for p, e_n in prime_powers:
            e_c, rest = 0, c
            while rest % p == 0:
                rest //= p
                e_c += 1
            if e_c == 0:
                continue                     # p never enters the kernel
            steps = -(-e_n // e_c)           # ceil(e_n / e_c), integer-only
            if steps > index:
                index = steps
            consumed_order *= p ** e_n
    eventual_modulus = n // consumed_order
    period = 1
    if eventual_modulus >= 2:
        period = cyclic_period(c % eventual_modulus, eventual_modulus)
    return {
        "c": c,
        "n": n,
        "kernel_order": kernel_order,
        "index": index,
        "consumed_order": consumed_order,
        "eventual_modulus": eventual_modulus,
        "eventual_size": eventual_modulus,
        "period": period,
        "is_permutation": kernel_order == 1,
    }
