"""Cascade **atoms** — the silicon-able 1:1 ISA intrinsics.

The six cascade ops in this tier each map 1:1 onto a single (future)
ISA intrinsic — they are the *atoms* of the lean A–N cascade ISA core
(per F208 / MS #20 forward-architecture). Each is a primitive
sign/orientation/handedness operation, not an iterative algorithm:

- :func:`pin_slot_at_zero` — Class K pin-slot at zero (sign-split).
- :func:`reorient` — Class C re-orientation (re-apply a captured sign).
- :func:`magnitude` — Class K pin-slot magnitude (orientation discarded).
- :func:`chiral_flip` — Class C orientation reversal (traverse the other way).
- :func:`chiral_dual` — Class C ∘ op ∘ Class C (chiral-dual conjugation).
- :func:`net_chirality` — Class C net handedness (product of orientations).

The iterative algorithms built *over* these atoms (Euclid's
``cyclic_gcd``, the continued-fraction ``best_rational_signed`` loop)
live in the sibling :mod:`srmech.amsc.cascade.compose` module.

**No ``abs()``** anywhere — sign is handled as the canonical Class K
pin-slot + Class C re-orientation per
``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``.

Each atom carries a dedicated C symbol in ``libsrmech.{so,dll,dylib}``
and a TOML descriptor under ``srmech/amsc/_research/cascade_catalog/``;
the Python wrapper dispatches through native when ``HAS_NATIVE`` is True
and the input shape matches a typed C variant, falling back to Python
for sequence types the C ABI doesn't cover.
"""

from __future__ import annotations

import ctypes
from typing import Tuple

from srmech.amsc import _native

# v0.4.6rc2 — introspection emit hook. Zero-cost when not publishing.
# We use ``_is_publishing()`` (a single thread-local attribute lookup)
# as the gate so the per-op ``describe_shape()`` cost only fires when
# a publishing context is active. ``emit_if_publishing()`` itself does
# the same check internally, but routing through the explicit gate
# here lets us skip the kwarg-bundle + the shape evaluation entirely.
from srmech.introspect._writer import (
    _is_publishing as _is_pub,
    emit_if_publishing as _emit,
)
from srmech.introspect._event import describe_shape as _shape

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
    if _is_pub(): _emit("cascade.pin_slot_at_zero", class_="K", input_shape=_shape(x))
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
    if _is_pub(): _emit("cascade.reorient", class_="C", input_shape=f"{_shape(orientation)}+{_shape(value)}")
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
    if _is_pub(): _emit("cascade.magnitude", class_="K", input_shape=_shape(x))
    native = _try_native_magnitude(x)
    if native is not None:
        return native
    return pin_slot_at_zero(x)[1]


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
    if _is_pub(): _emit("cascade.chiral_flip", class_="C", input_shape=_shape(seq))
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
    if _is_pub(): _emit("cascade.chiral_dual", class_="C∘op∘C", input_shape=_shape(x))
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
    if _is_pub(): _emit("cascade.net_chirality", class_="C", input_shape=_shape(orientations))
    native = _try_native_net_chirality(orientations)
    if native is not None:
        return native
    net = 1
    for o in orientations:
        if o == 0:
            return 0
        net = reorient(o, net)
    return net


__all__ = [
    "pin_slot_at_zero",
    "reorient",
    "magnitude",
    "chiral_flip",
    "chiral_dual",
    "net_chirality",
]
