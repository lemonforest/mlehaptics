"""Foundational cross-domain cascade catalog.

The cascades that recur across **every / most** domains the framework has
examined — promoted into srmech so a named cascade is the default and a
math-library call is the exception. Per the project discipline: *being
forced to reach for a math library is the signal that a cascade is waiting
to be found.* `abs()` told us to find the Class-K pin-slot; `fractions`
told us to find the Class-N rational anchor; `math.gcd` told us to find the
Class-I cyclic gcd. This module is where those answers live.

Scale-invariance is the load-bearing reason these belong in srmech: the
A–N class operators are substrate-universal vocabulary that applies at
every discipline and every scale (per
``[[user_stance_cross_substrate_cascade_matching_as_research_method]]``).
The same **Class K pin-slot at zero** operates at bronze-gear engagement
(Antikythera), atomic shell-boundary sign-flip, biological membrane
zero-crossing, quantum tunnelling, and prime-cyclic Laplacian residue
exclusion. The same **Class N** rational anchor lands the GUE spacing-ratio
at 20/17, the Balmer line-ratios, the CMB peak spacing. This catalog is the
explicit home of that recurrence — the precursor
``docs/unsolved-maths/_cascade_helpers.py`` (imported across 20+ cascade
scripts spanning mandelbrot / chromatic / atomic / nuclear / QCD /
planetary / turbulence / black-hole / biomacromolecule / large-scale-
structure domains) graduates here.

**Full C/Python parity** — each cascade op carries a dedicated C symbol in
``libsrmech.{so,dll,dylib}`` (the cascade catalog is no longer Python-only
per the v0.4.5rc1 carve-out correction) AND a TOML descriptor under
``srmech/amsc/_research/cascade_catalog/`` declaring the cascade structure
declaratively. The Python module dispatches through native when ``HAS_NATIVE``
is True and the input shape matches a typed C variant; falls back to Python
for sequence types the C ABI doesn't cover (strings, mixed-type lists, etc).

**No new primitive class** — every callable is a *composition* of the
existing 14-class A–N primitives (the vocabulary is intact per
``[[feedback_no_privileged_primitive_classes]]``). Class I
(``srmech.amsc.cyclic.gcd``) and Class N
(``srmech.amsc.rational.best_rational``) supply the cyclic / rational
anchor primitives; the cascades sequence them in Python (with inline
Class K / Class C signed arithmetic) plus the dedicated cascade-op C
symbols for the hot value-sequence cascades (``chiral_flip`` in
v0.4.5rc1; the remaining ops follow in subsequent rcs). **No ``abs()``**
anywhere — sign is handled as the canonical Class K pin-slot + Class C
re-orientation per
``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``.

Naming: the clean public names (``pin_slot_at_zero``, ``reorient``,
``magnitude``, ``best_rational_signed``, ``cyclic_gcd``) are canonical; the
precursor's ``class_<X>_<name>`` call-site names are kept as back-compat
aliases so existing cascade scripts migrate with a pure import swap.

Canonical SSoT:
- ``[[user_stance_epicycle_via_gear_plus_pin]]`` — sign-flip IS the Class K
  pin-slot phase-boundary.
- Khinchin (1964), *Continued Fractions* — the Class N best-rational anchor
  (via ``srmech.amsc.rational.best_rational``).
- Euclid, *Elements* VII.1–2 — the Class I gcd (via ``srmech.amsc.cyclic.gcd``).
"""

from __future__ import annotations

import ctypes
from typing import Tuple

from srmech.amsc import _native
from srmech.amsc.cyclic import gcd as _cyclic_gcd
from srmech.amsc.rational import best_rational as _best_rational

#: Default small-denominator ceiling for ``best_rational_signed`` (the
#: Class N rational anchor). Matches the precursor cascade-helper default.
DEFAULT_MAX_DENOMINATOR = 100

#: Default fine-scaling factor turning a float magnitude into the integer
#: pair ``srmech.amsc.rational.best_rational`` consumes.
DEFAULT_FINE_SCALE = 1_000_000

#: A magnitude below this is treated as the Class K dead-band (origin).
_ZERO_BAND = 1e-12


def _try_native_pin_slot_at_zero(x):
    """Native dispatch for float ``pin_slot_at_zero``.

    Returns ``(int, float)`` on success or ``None`` to signal the caller
    should fall through to the Python path. Only Python ``float`` inputs
    dispatch through native — ``int`` (and bool, Decimal, etc.) stay on
    the Python path so the int-in / int-magnitude-out type contract is
    preserved (the native f64 path would coerce ``5`` to ``5.0`` and
    return ``(1, 5.0)``, a type-change downstream callers rely on not
    happening).
    """
    if not (_native.HAS_NATIVE and _native.LIB is not None):
        return None
    # Strict isinstance check — bool is a subclass of int and must NOT
    # take the native path; non-float numerics (int / Decimal / Fraction /
    # numpy scalars) also stay on Python.
    if type(x) is not float:
        return None
    if not hasattr(_native.LIB, "srmech_cascade_pin_slot_at_zero_f64"):
        return None
    orient = ctypes.c_int8(0)
    mag = ctypes.c_double(0.0)
    rc = _native.LIB.srmech_cascade_pin_slot_at_zero_f64(
        ctypes.c_double(x),
        ctypes.byref(orient),
        ctypes.byref(mag),
    )
    if rc != _native.SRMECH_OK:
        return None
    return int(orient.value), float(mag.value)


def pin_slot_at_zero(x: float) -> Tuple[int, float]:
    """Class K pin-slot at zero: split ``x`` into (orientation, magnitude).

    The pin enters or exits the slot at the zero-crossing — sign-flip IS the
    canonical Class K phase-boundary per
    ``[[user_stance_epicycle_via_gear_plus_pin]]``. Expressing this as a
    named cascade (rather than Python ``abs()``) keeps the cascade-count
    claimed in line with the cascade-count executed.

    v0.4.5rc2: dispatches through the native C variant
    ``srmech_cascade_pin_slot_at_zero_f64`` when ``HAS_NATIVE`` is True
    and ``x`` is a Python ``float``. Python ``int`` (and other numeric
    types) stay on the Python fallback so the int-in / int-magnitude-out
    type contract is preserved bit-identically.

    Args:
        x: A real value.

    Returns:
        ``(orientation, magnitude)`` where ``orientation ∈ {-1, 0, +1}`` and
        ``magnitude >= 0``. The origin and NaN both map to ``(0, 0.0)``;
        ``+inf`` / ``-inf`` map to ``(+/-1, +inf)``.
    """
    native = _try_native_pin_slot_at_zero(x)
    if native is not None:
        return native
    if x > 0.0:
        return +1, x
    if x < 0.0:
        return -1, -x
    return 0, 0.0


def _try_native_reorient(orientation, value):
    """Native dispatch for reorient (Class C re-orientation).

    Routes:
      - int orientation (int8 range, not bool) + int value (int64 range,
        not bool, not INT64_MIN) → reorient_i64
      - int orientation (int8 range, not bool) + float value → reorient_f64
      - else (numpy scalars, lists, ndarrays, mixed-type, bool orientation,
        out-of-range orientation, INT64_MIN int value, out-of-int64 bigint)
        → None (Python fallback)

    INT64_MIN is explicitly excluded from the i64 path: negating it would
    overflow under fixed-width two's complement. Python ints are
    arbitrary precision, so `-(-(2**63))` is well-defined Python-side
    (returns ``2**63``) — the Python fallback handles this without
    overflow.
    """
    if not (_native.HAS_NATIVE and _native.LIB is not None):
        return None
    # Orientation must be a pure Python int in int8 range (not bool).
    if type(orientation) is not int or isinstance(orientation, bool):
        return None
    if orientation < -128 or orientation > 127:
        return None
    # Value: pure Python int or float (no bool, no numpy scalars, no Decimal).
    if type(value) is int:
        INT64_MIN = -(2 ** 63)
        INT64_MAX = (2 ** 63) - 1
        # Range check for int64; INT64_MIN explicitly excluded (negation
        # would overflow — Python fallback handles via arbitrary precision).
        if value <= INT64_MIN or value > INT64_MAX:
            return None
        if not hasattr(_native.LIB, "srmech_cascade_reorient_i64"):
            return None
        out = ctypes.c_int64(0)
        rc = _native.LIB.srmech_cascade_reorient_i64(
            ctypes.c_int8(orientation),
            ctypes.c_int64(value),
            ctypes.byref(out),
        )
        if rc != _native.SRMECH_OK:
            return None
        return int(out.value)
    if type(value) is float:
        if not hasattr(_native.LIB, "srmech_cascade_reorient_f64"):
            return None
        out = ctypes.c_double(0.0)
        rc = _native.LIB.srmech_cascade_reorient_f64(
            ctypes.c_int8(orientation),
            ctypes.c_double(value),
            ctypes.byref(out),
        )
        if rc != _native.SRMECH_OK:
            return None
        return float(out.value)
    return None


def reorient(orientation: int, value):
    """Class C cascade-orientation: re-apply a captured orientation.

    v0.4.5rc4: dispatches through the native C variants
    ``srmech_cascade_reorient_i64`` / ``srmech_cascade_reorient_f64``
    when ``HAS_NATIVE`` is True, ``orientation`` is a pure Python ``int``
    in int8 range (not bool), and ``value`` is a pure Python ``int`` (in
    int64 range, not INT64_MIN, not bool) or pure Python ``float``. Falls
    back to the Python ``-value`` / ``value`` path for numpy scalars,
    ndarrays, lists, mixed-type values, bool orientation, out-of-int8
    orientation, INT64_MIN integer values (Python's arbitrary precision
    handles this without overflow), and out-of-int64 bigint values. The
    op is type-preserving: int in → int out, float in → float out.

    Args:
        orientation: An orientation in ``{-1, 0, +1}`` (typically the first
            element of a :func:`pin_slot_at_zero` result).
        value: The magnitude (or magnitude-derived quantity) to re-sign.

    Returns:
        ``-value`` when ``orientation < 0``, otherwise ``value`` unchanged.
    """
    native = _try_native_reorient(orientation, value)
    if native is not None:
        return native
    if orientation < 0:
        return -value
    return value


def _try_native_magnitude(x):
    """Native dispatch for float ``magnitude``.

    Returns ``float`` on success or ``None`` to signal the caller to fall
    through to the Python composition path. Only Python ``float`` inputs
    dispatch through native — ``int`` (and bool, Decimal, numpy scalars,
    etc.) stay on the Python path so the int-in / int-magnitude-out type
    contract is preserved (matches the rc2 ``pin_slot_at_zero``
    discipline; the Python composition fallback returns
    ``pin_slot_at_zero(x)[1]`` which itself stays on Python for int).
    """
    if not (_native.HAS_NATIVE and _native.LIB is not None):
        return None
    # Strict isinstance check — bool is a subclass of int and must NOT
    # take the native path; non-float numerics (int / Decimal / Fraction /
    # numpy scalars) also stay on Python.
    if type(x) is not float:
        return None
    if not hasattr(_native.LIB, "srmech_cascade_magnitude_f64"):
        return None
    out = ctypes.c_double(0.0)
    rc = _native.LIB.srmech_cascade_magnitude_f64(
        ctypes.c_double(x),
        ctypes.byref(out),
    )
    if rc != _native.SRMECH_OK:
        return None
    return float(out.value)


def magnitude(x: float) -> float:
    """Class K pin-slot at zero, magnitude only (orientation discarded).

    The cascade-honest replacement for Python ``abs()`` when only the
    magnitude is needed (spectral radius, eigenvalue-magnitude proxy, …).

    v0.4.5rc3: dispatches through the native C variant
    ``srmech_cascade_magnitude_f64`` when ``HAS_NATIVE`` is True and ``x``
    is a pure Python ``float``. Falls back to composing
    :func:`pin_slot_at_zero` (which itself dispatches through native in
    v0.4.5rc2 for ``float`` inputs) for ``int`` / numpy-scalar / other
    numeric types. NaN maps to ``0.0`` (the Class K dead-band) in both
    paths.

    Args:
        x: A real value.

    Returns:
        ``|x|`` as the Class K pin-slot magnitude (always ``>= 0``).
    """
    native = _try_native_magnitude(x)
    if native is not None:
        return native
    return pin_slot_at_zero(x)[1]


def _try_native_best_rational_signed(x, max_denominator, fine_scale):
    """Native dispatch for the Class K ∘ Class N ∘ Class C cascade.

    Returns ``(int, int)`` on success or ``None`` to signal the caller
    should fall through to the Python composition path. Only pure-Python
    ``float`` ``x`` + pure-Python ``int`` kwargs (not bool) within int64
    range dispatch through native. Out-of-range kwargs or non-float ``x``
    (int, numpy scalar, Decimal, ...) stay on the Python path so the
    public API behaviour is preserved exactly.

    Banker's-rounding parity: the C peer uses ``llrint()`` under the
    default IEEE-754 ``FE_TONEAREST`` mode (round-half-to-even), which
    matches Python's built-in ``round()`` at the ``.5`` boundary
    bit-exactly. C99 ``round()`` would diverge (round-half-AWAY-from-
    zero); the cascade wrapper deliberately avoids C99 ``round()``.
    """
    if not (_native.HAS_NATIVE and _native.LIB is not None):
        return None
    # Strict type check — bool is a subclass of int and must NOT take
    # the native path (matches the cascade-dispatch discipline). Only
    # pure Python float dispatches through native.
    if type(x) is not float:
        return None
    if type(max_denominator) is not int or isinstance(max_denominator, bool):
        return None
    if type(fine_scale) is not int or isinstance(fine_scale, bool):
        return None
    if max_denominator < 1 or fine_scale < 1:
        # Let the caller hit the Python path which raises ValueError
        # with the proper message.
        return None
    INT64_MAX = (2 ** 63) - 1
    if max_denominator > INT64_MAX or fine_scale > INT64_MAX:
        return None
    if not hasattr(_native.LIB, "srmech_cascade_best_rational_signed_f64"):
        return None
    out_num = ctypes.c_int64(0)
    out_den = ctypes.c_int64(0)
    rc = _native.LIB.srmech_cascade_best_rational_signed_f64(
        ctypes.c_double(x),
        ctypes.c_int64(max_denominator),
        ctypes.c_int64(fine_scale),
        ctypes.byref(out_num),
        ctypes.byref(out_den),
    )
    if rc != _native.SRMECH_OK:
        return None
    return int(out_num.value), int(out_den.value)


def best_rational_signed(
    x: float,
    *,
    max_denominator: int = DEFAULT_MAX_DENOMINATOR,
    fine_scale: int = DEFAULT_FINE_SCALE,
) -> Tuple[int, int]:
    """Class K ∘ Class N ∘ Class C: float → signed small-denominator rational.

    The full cross-domain anchor cascade: strip the sign at the Class K
    pin-slot, find the Class N best-rational of the non-negative magnitude
    (via ``srmech.amsc.rational.best_rational``, which takes an integer pair),
    then re-apply the sign as Class C. No ``abs()``; the sign lives in the
    Class K / Class C pair end-to-end.

    v0.4.5rc7: dispatches through the native C variant
    ``srmech_cascade_best_rational_signed_f64`` when ``HAS_NATIVE`` is
    True, ``x`` is a pure-Python ``float``, and ``max_denominator`` /
    ``fine_scale`` are pure-Python ``int`` (not bool) in int64 range. The
    C peer delegates the Class N stage to the existing
    ``srmech_best_rational`` primitive; the Class K + Class C stages are
    inlined (one comparison branch + one sign flip each). Python fallback
    handles numpy scalars, Decimal, larger-than-int64 kwargs, and any
    other shape the strict native ABI doesn't cover.

    Banker's-rounding parity: the C peer uses ``llrint()`` under the
    default IEEE-754 ``FE_TONEAREST`` mode (round-half-to-even), so the
    ``round(magnitude * fine_scale)`` step matches Python's built-in
    ``round()`` at the ``.5`` boundary bit-exactly.

    Args:
        x: A real value (the irrational/float to anchor).
        max_denominator: Class N small-denominator ceiling.
        fine_scale: Integer scale turning the float magnitude into the
            ``(numerator, denominator)`` pair ``best_rational`` consumes.

    Returns:
        ``(signed_numerator, denominator)`` — the Class N convergent of
        ``x`` with the Class C sign re-applied. The origin and sub-dead-band
        magnitudes map to ``(0, 1)``. NaN also maps to ``(0, 1)`` via the
        Class K dead-band.

    Raises:
        ValueError: if ``max_denominator < 1`` or ``fine_scale < 1``.
    """
    if max_denominator < 1:
        raise ValueError(
            f"cascade.best_rational_signed: max_denominator must be >= 1; "
            f"got {max_denominator}"
        )
    if fine_scale < 1:
        raise ValueError(
            f"cascade.best_rational_signed: fine_scale must be >= 1; "
            f"got {fine_scale}"
        )
    native = _try_native_best_rational_signed(x, max_denominator, fine_scale)
    if native is not None:
        return native
    # Python fallback path.
    # Class K — pin-slot at zero (sign-strip).
    orientation, mag = pin_slot_at_zero(x)
    if orientation == 0 or mag < _ZERO_BAND:
        return 0, 1
    num_pos = int(round(mag * fine_scale))
    if num_pos == 0:
        return 0, 1
    # Class N — best-rational anchor of the non-negative magnitude.
    nf, df = _best_rational(num_pos, fine_scale, max_denominator)
    # Class C — re-apply the captured orientation.
    return reorient(orientation, int(nf)), int(df)


def _try_native_cyclic_gcd(a, b):
    """Native dispatch for cyclic_gcd via the cascade-namespace wrapper.

    The cascade wrapper ``srmech_cascade_cyclic_gcd_u64`` is itself a
    pure-delegation alias for the Class I primitive ``srmech_gcd``; we
    dispatch through the cascade-namespace symbol (not the Class I
    primitive directly) so the cascade-catalog naming stays uniform per
    the v0.4.5rc6 directive *"delegate to A-N C peers; cascade-level C
    wrapper + TOML"*. The Python ``srmech.amsc.cyclic.gcd`` reaches the
    same C primitive through its OWN ctypes binding — both surfaces
    coexist in libsrmech.

    Returns ``int`` on success or ``None`` to signal the caller should
    fall through to the Python path. Only pure Python ``int`` inputs in
    ``[0, 2**64 - 1]`` (the uint64 range matched by the cascade C ABI)
    dispatch through native — bool is rejected by ``type(x) is int``,
    and negatives / out-of-uint64 bigints fall through to the Python
    fallback which itself raises ``ValueError`` (mirroring the Python
    ref ``srmech.amsc.cyclic.gcd`` behaviour exactly).
    """
    if not (_native.HAS_NATIVE and _native.LIB is not None):
        return None
    # Strict isinstance check — bool is a subclass of int and must NOT
    # take the native path (matches the rcN cascade-dispatch discipline).
    if type(a) is not int or isinstance(a, bool):
        return None
    if type(b) is not int or isinstance(b, bool):
        return None
    UINT64_MAX = (2 ** 64) - 1
    if a < 0 or b < 0:
        return None
    if a > UINT64_MAX or b > UINT64_MAX:
        return None
    if not hasattr(_native.LIB, "srmech_cascade_cyclic_gcd_u64"):
        return None
    out = ctypes.c_uint64(0)
    rc = _native.LIB.srmech_cascade_cyclic_gcd_u64(
        ctypes.c_uint64(a),
        ctypes.c_uint64(b),
        ctypes.byref(out),
    )
    if rc != _native.SRMECH_OK:
        return None
    return int(out.value)


def cyclic_gcd(a: int, b: int) -> int:
    """Class I cyclic gcd. Delegates to ``srmech.amsc.cyclic.gcd``.

    A cascade-named alias so number-theoretic cascades reach for the Class I
    primitive by its cascade name rather than ``math.gcd``. The cascade-
    catalog entry IS the Class I primitive (Euclid's algorithm); the
    wrapper exists for namespace consistency, not for additional math.

    v0.4.5rc6: dispatches through the native cascade-namespace wrapper
    ``srmech_cascade_cyclic_gcd_u64`` when ``HAS_NATIVE`` is True, both
    inputs are pure Python ``int`` (not bool) in the uint64 range
    ``[0, 2**64 - 1]``. Falls back to the Python ``srmech.amsc.cyclic.gcd``
    path for bool, negative, and out-of-uint64 inputs — which itself
    raises ``ValueError`` for negative / oversized inputs, preserving the
    pre-rc6 public API exactly. The cascade wrapper is a pure-delegation
    alias for the Class I primitive ``srmech_gcd``; dispatching through
    the cascade-namespace symbol keeps the cascade-catalog naming uniform
    per the rc6 directive *"delegate to A-N C peers; cascade-level C
    wrapper + TOML"*.

    Args:
        a: non-negative ``int`` in uint64 range.
        b: non-negative ``int`` in uint64 range.

    Returns:
        The Euclidean ``gcd(a, b)`` (non-negative). ``gcd(0, 0)`` is
        ``0`` (the gcd identity); ``gcd(a, 0)`` is ``a``.

    Raises:
        ValueError: forwarded from ``srmech.amsc.cyclic.gcd`` for negative
            inputs or inputs exceeding the uint64 parity surface.
    """
    native = _try_native_cyclic_gcd(a, b)
    if native is not None:
        return native
    return _cyclic_gcd(a, b)


def _try_native_chiral_flip_ndarray(arr):
    """Native dispatch for numpy int64 / float64 ndarrays.

    Returns the reversed ndarray on success, or ``None`` if the native
    path is unavailable / the dtype is unsupported / a status error
    surfaced (in which case the caller falls back to Python).
    """
    if not (_native.HAS_NATIVE and _native.LIB is not None):
        return None
    if not (hasattr(arr, "dtype") and hasattr(arr, "ndim")):
        return None
    if arr.ndim != 1:
        return None
    dtype = arr.dtype
    if dtype.itemsize != 8 or dtype.kind not in ("i", "f"):
        return None
    # numpy is a hard dep from v0.4.0rc2 onward; import is safe here.
    import numpy as _np
    if dtype.kind == "i" and dtype != _np.int64:
        return None
    if dtype.kind == "f" and dtype != _np.float64:
        return None
    if not hasattr(_native.LIB, "srmech_cascade_chiral_flip_i64"):
        return None
    n = int(arr.shape[0])
    # Ensure C-contiguous so the ctypes pointer addresses element-stride
    # rather than the original (potentially non-contiguous) layout.
    src = _np.ascontiguousarray(arr)
    out = _np.empty_like(src)
    if dtype.kind == "i":
        c_in = src.ctypes.data_as(ctypes.POINTER(ctypes.c_int64))
        c_out = out.ctypes.data_as(ctypes.POINTER(ctypes.c_int64))
        rc = _native.LIB.srmech_cascade_chiral_flip_i64(
            c_in, ctypes.c_size_t(n), c_out,
        )
    else:
        c_in = src.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
        c_out = out.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
        rc = _native.LIB.srmech_cascade_chiral_flip_f64(
            c_in, ctypes.c_size_t(n), c_out,
        )
    if rc != _native.SRMECH_OK:
        return None
    return out


def _try_native_chiral_flip_list(seq):
    """Native dispatch for homogeneous list[int] / list[float] / tuple.

    Returns a list (or tuple, if the caller passed a tuple) of reversed
    values on success, or ``None`` if the native path is unavailable or
    the input isn't a homogeneous int64 / float64 sequence.
    """
    if not (_native.HAS_NATIVE and _native.LIB is not None):
        return None
    if not isinstance(seq, (list, tuple)):
        return None
    n = len(seq)
    if n == 0:
        # Empty: cheap; preserve input type without touching native.
        return type(seq)()
    # Classify the homogeneous int64 / float64 case. Python int can be
    # arbitrarily large; only dispatch when every element fits int64.
    INT64_MIN = -(2 ** 63)
    INT64_MAX = (2 ** 63) - 1
    all_int = all(isinstance(v, int) and not isinstance(v, bool) for v in seq)
    all_float = all(isinstance(v, float) for v in seq)
    if all_int:
        if not all(INT64_MIN <= v <= INT64_MAX for v in seq):
            return None
        if not hasattr(_native.LIB, "srmech_cascade_chiral_flip_i64"):
            return None
        ArrT = ctypes.c_int64 * n
        c_in = ArrT(*seq)
        c_out = ArrT()
        rc = _native.LIB.srmech_cascade_chiral_flip_i64(
            ctypes.cast(c_in, ctypes.POINTER(ctypes.c_int64)),
            ctypes.c_size_t(n),
            ctypes.cast(c_out, ctypes.POINTER(ctypes.c_int64)),
        )
        if rc != _native.SRMECH_OK:
            return None
        result = [int(c_out[i]) for i in range(n)]
        return tuple(result) if isinstance(seq, tuple) else result
    if all_float:
        if not hasattr(_native.LIB, "srmech_cascade_chiral_flip_f64"):
            return None
        ArrT = ctypes.c_double * n
        c_in = ArrT(*seq)
        c_out = ArrT()
        rc = _native.LIB.srmech_cascade_chiral_flip_f64(
            ctypes.cast(c_in, ctypes.POINTER(ctypes.c_double)),
            ctypes.c_size_t(n),
            ctypes.cast(c_out, ctypes.POINTER(ctypes.c_double)),
        )
        if rc != _native.SRMECH_OK:
            return None
        result = [float(c_out[i]) for i in range(n)]
        return tuple(result) if isinstance(seq, tuple) else result
    return None


def chiral_flip(seq):
    """Class C orientation reversal: traverse the cascade the other way.

    The value-level Class C cascade-orientation operator — it reverses the
    traversal order of a sequence. Reversing a real signal is the FFT-level
    chirality operator (same magnitude spectrum, orientation-flipped phase)
    per MFO §VIII.31.11 §(5b): the chiral dual is "same shape, inverse".

    v0.4.5rc1: dispatches through the native C variants
    ``srmech_cascade_chiral_flip_i64`` / ``srmech_cascade_chiral_flip_f64``
    when ``HAS_NATIVE`` is True and ``seq`` is a homogeneous int64 /
    float64 ``list`` / ``tuple`` / 1-D ``ndarray``. Falls back to the
    Python ``seq[::-1]`` path for any sequence shape the native ABI
    doesn't cover (strings, mixed-type lists, larger-than-int64 ints,
    non-contiguous / multi-dimensional ndarrays, etc) so the public API
    stays unchanged.

    Args:
        seq: Any sliceable sequence (list / tuple / str / ndarray).

    Returns:
        ``seq[::-1]`` — the orientation-reversed sequence, type preserved.
    """
    # Native path 1: numpy ndarray. Detect via duck-typing on dtype/ndim so
    # we don't pay an unconditional numpy import for non-array callers.
    if hasattr(seq, "dtype") and hasattr(seq, "ndim"):
        native = _try_native_chiral_flip_ndarray(seq)
        if native is not None:
            return native
    # Native path 2: homogeneous int64 / float64 list / tuple.
    elif isinstance(seq, (list, tuple)):
        native = _try_native_chiral_flip_list(seq)
        if native is not None:
            return native
    # Python fallback — preserves the original public API exactly.
    return seq[::-1]


def _try_native_chiral_dual(op, x):
    """Native dispatch for chiral_dual (Class C ∘ op ∘ Class C).

    Dispatches through the rc8 callback ABI when ``x`` is a homogeneous
    float64 sequence (list / tuple / 1-D ndarray). The Python ``op``
    callable is wrapped as a ctypes CFUNCTYPE; the callback marshals
    Python ↔ C via numpy view + ctypes.memmove.

    Returns the chirally-dual result on success or ``None`` to signal
    the caller to fall through to the Python composition path. If the
    Python op raises an exception inside the callback, the exception is
    captured and re-raised on the Python side (after the C function
    returns); the native path is NOT silently treated as a fall-through
    in that case.
    """
    if not (_native.HAS_NATIVE and _native.LIB is not None):
        return None
    if not hasattr(_native.LIB, "srmech_cascade_chiral_dual_f64"):
        return None
    if not callable(op):
        return None
    # Detect 1-D float64 ndarray input.
    is_ndarray = hasattr(x, "dtype") and hasattr(x, "ndim")
    if is_ndarray:
        import numpy as _np
        if x.ndim != 1 or x.dtype != _np.float64:
            return None
        n = int(x.shape[0])
        in_buf = _np.ascontiguousarray(x, dtype=_np.float64)
    elif isinstance(x, (list, tuple)):
        # Homogeneous float-only sequences route through native; mixed
        # int+float and other shapes fall through to Python.
        if not all(isinstance(v, float) for v in x):
            return None
        import numpy as _np
        n = len(x)
        in_buf = _np.asarray(x, dtype=_np.float64)
    else:
        return None

    import numpy as _np
    workspace = _np.empty(n, dtype=_np.float64)
    out_buf = _np.empty(n, dtype=_np.float64)

    # Callback: marshal C pointer + length back into a numpy view,
    # invoke the Python op, copy result into the C output buffer. The
    # GIL is held inside CFUNCTYPE callbacks automatically; no extra
    # threading discipline needed.
    callback_error: list = [None]

    def _op_trampoline(in_ptr, in_n, out_ptr, _user_data):
        try:
            # Wrap C in/out buffers as numpy views (no copy).
            in_view = _np.ctypeslib.as_array(in_ptr, shape=(int(in_n),))
            out_view = _np.ctypeslib.as_array(out_ptr, shape=(int(in_n),))
            result = op(in_view)
            # Coerce to ndarray; verify length matches.
            result_arr = _np.asarray(result, dtype=_np.float64).ravel()
            if result_arr.shape != (int(in_n),):
                callback_error[0] = ValueError(
                    f"chiral_dual callback returned length "
                    f"{result_arr.shape[0]}; expected {int(in_n)}"
                )
                return -1  # any nonzero status; reported via callback_error
            out_view[:] = result_arr
            return 0  # SRMECH_OK
        except Exception as exc:
            callback_error[0] = exc
            return -1

    c_callback = _native.CASCADE_OP_CALLBACK_F64(_op_trampoline)

    rc = _native.LIB.srmech_cascade_chiral_dual_f64(
        c_callback,
        None,  # user_data unused (the Python op is captured by closure)
        in_buf.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        ctypes.c_size_t(n),
        out_buf.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        workspace.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
    )
    # If the Python op raised, surface it — never silently fall back to
    # Python composition (which would re-execute the failing op).
    if callback_error[0] is not None:
        raise callback_error[0]
    if rc != _native.SRMECH_OK:
        return None
    if is_ndarray:
        return out_buf
    return out_buf.tolist() if isinstance(x, list) else tuple(out_buf.tolist())


def chiral_dual(op, x):
    """Class C ∘ op ∘ Class C: run ``op`` in the opposite Class-C orientation.

    The chiral-dual cascade. Conjugating any operator by the Class C
    orientation reversal (:func:`chiral_flip`) produces its chiral dual —
    empirically (MFO §VIII.31.11 §(5b)/(5c), committed spike
    ``docs/srmech/notes/spike_chiral_an_spectral_shape.py``) this preserves
    the spectral *shape* (magnitude) and inverts the *orientation* (phase).
    For the rotation/fiber operators it is the orientation-inverse; for the
    explicit sign/orientation operators (Class C, Class N) it reduces to the
    bare Class K ``-1``; for real-symmetric operators (Class L) it is the
    identity. **No new class** — this is Class C composed with ``op``.

    v0.4.5rc8: HIGHER-ORDER cascade — dispatches through the native C
    variant ``srmech_cascade_chiral_dual_f64`` when ``HAS_NATIVE`` is
    True and ``x`` is a homogeneous float64 sequence (1-D ndarray
    float64, or list / tuple of pure Python floats). The C peer uses a
    function-pointer callback ABI (``srmech_cascade_op_callback_f64_t``)
    so arbitrary Python ``op`` callables are supported without
    restricting to known A–N srmech ops — the cascade-catalog public API
    contract per the project discipline. Workspace is caller-allocated
    per JPL Rule 3 (no malloc inside libsrmech). Falls back to the pure
    Python ``chiral_flip(op(chiral_flip(x)))`` composition for strings,
    mixed-type sequences, non-callable ``op``, multi-arg ``op``, and
    any other shape the strict native ABI doesn't cover. Python
    exceptions raised by ``op`` propagate correctly through the
    callback trampoline (never silently swallowed). CLOSES the cascade-
    catalog C-parity + TOML retrofit arc at 8 of 8.

    Args:
        op: A unary callable mapping a sequence to a sequence (an A–N
            operator's action on a signal).
        x: The input sequence.

    Returns:
        ``chiral_flip(op(chiral_flip(x)))`` — ``op`` evaluated in the
        reversed Class-C orientation.
    """
    native = _try_native_chiral_dual(op, x)
    if native is not None:
        return native
    return chiral_flip(op(chiral_flip(x)))


def _try_native_net_chirality(orientations):
    """Native dispatch for net_chirality.

    Accepts:
      - list / tuple of pure-Python ints (every element in int8 range,
        no bools)
      - 1-D ndarray with integer dtype, each value in int8 range

    Returns ``int`` on success or ``None`` to signal the caller should
    fall through to the Python path. Generators (non-len-able iterables),
    bool elements (False == 0 in Python iteration), mixed types
    (int + float / numpy scalar), and out-of-int8 values all fall
    through to Python.
    """
    if not (_native.HAS_NATIVE and _native.LIB is not None):
        return None
    if not hasattr(_native.LIB, "srmech_cascade_net_chirality_i8"):
        return None

    # Path A: ndarray.
    if hasattr(orientations, "dtype") and hasattr(orientations, "ndim"):
        import numpy as _np
        if orientations.ndim != 1:
            return None
        if orientations.dtype.kind not in ("i", "u"):
            return None
        # Bound-check: every value must fit in int8 (we use int8 ABI
        # so values outside [-128, 127] would silently wrap).
        if orientations.size > 0:
            mn = int(orientations.min())
            mx = int(orientations.max())
            if mn < -128 or mx > 127:
                return None
        # Convert to int8 contiguous buffer.
        buf = _np.ascontiguousarray(orientations, dtype=_np.int8)
        n = int(buf.size)
        c_in = buf.ctypes.data_as(ctypes.POINTER(ctypes.c_int8))
        out_val = ctypes.c_int8(0)
        rc = _native.LIB.srmech_cascade_net_chirality_i8(
            c_in, ctypes.c_size_t(n), ctypes.byref(out_val),
        )
        if rc != _native.SRMECH_OK:
            return None
        return int(out_val.value)

    # Path B: list / tuple of pure-Python ints (no bools).
    if isinstance(orientations, (list, tuple)):
        n = len(orientations)
        if n == 0:
            # Empty: short-circuit; native ABI returns +1 too, but we can
            # avoid the call.
            return 1
        # Validate every element is a pure Python int in int8 range.
        for o in orientations:
            if type(o) is not int:  # rejects bool, float, numpy scalars
                return None
            if o < -128 or o > 127:
                return None
        ArrT = ctypes.c_int8 * n
        c_in = ArrT(*orientations)
        out_val = ctypes.c_int8(0)
        rc = _native.LIB.srmech_cascade_net_chirality_i8(
            ctypes.cast(c_in, ctypes.POINTER(ctypes.c_int8)),
            ctypes.c_size_t(n),
            ctypes.byref(out_val),
        )
        if rc != _native.SRMECH_OK:
            return None
        return int(out_val.value)

    return None


def net_chirality(orientations) -> int:
    """Class C net handedness of a cascade: the product of per-op orientations.

    A cascade built from operators each carrying a Class C orientation in
    ``{-1, 0, +1}`` has a *net* handedness — the conserved Class-C invariant a
    chiral cascade reads out (MFO §VIII.31.11 §(5d); the net-chirality of
    Spike #74 / #89). Computed by composing :func:`reorient`, not by ``abs``-
    free sign multiplication, so the cascade-count matches the cascade-shape.

    v0.4.5rc5: dispatches through the native C variant
    ``srmech_cascade_net_chirality_i8`` when ``HAS_NATIVE`` is True and the
    input is a ``list`` / ``tuple`` of pure-Python ints in int8 range (no
    bools) or a 1-D integer ``ndarray`` with every value in int8 range.
    Falls back to the Python iteration path for generators (non-len-able
    iterables), bool elements (``False == 0`` short-circuits via the
    Python loop), mixed-type sequences, and out-of-int8 values.

    Args:
        orientations: Iterable of orientations in ``{-1, 0, +1}`` (typically
            the first element of each operator's :func:`pin_slot_at_zero`).

    Returns:
        ``+1`` (net even / right-handed), ``-1`` (net odd / left-handed), or
        ``0`` if any operator is orientation-neutral (a zero-crossing in the
        chain collapses net handedness).
    """
    native = _try_native_net_chirality(orientations)
    if native is not None:
        return native
    net = 1
    for o in orientations:
        if o == 0:
            return 0
        net = reorient(o, net)
    return net


# ── Back-compat aliases (the precursor's call-site names) ──────────────
# Existing cascade scripts in docs/unsolved-maths/ import these names from
# the local _cascade_helpers; the alias lets them migrate to
# ``from srmech.amsc.cascade import ...`` without changing call sites.
class_k_pin_slot_at_zero = pin_slot_at_zero
class_c_reorient = reorient
best_rat_signed = best_rational_signed

#: Registry of the foundational cascade op names (documentary; consumers
#: iterate by name). Each maps to its A–N class composition in the docs.
CASCADE_OPS: Tuple[str, ...] = (
    "pin_slot_at_zero",        # Class K
    "reorient",                # Class C
    "magnitude",               # Class K (magnitude-only)
    "best_rational_signed",    # Class K ∘ N ∘ C
    "cyclic_gcd",              # Class I
    "chiral_flip",             # Class C (orientation reversal)
    "chiral_dual",             # Class C ∘ op ∘ Class C (chiral-dual conjugation)
    "net_chirality",           # Class C (net handedness invariant)
)

__all__ = [
    "DEFAULT_MAX_DENOMINATOR",
    "DEFAULT_FINE_SCALE",
    "CASCADE_OPS",
    "pin_slot_at_zero",
    "reorient",
    "magnitude",
    "best_rational_signed",
    "cyclic_gcd",
    "chiral_flip",
    "chiral_dual",
    "net_chirality",
    # back-compat aliases
    "class_k_pin_slot_at_zero",
    "class_c_reorient",
    "best_rat_signed",
]
