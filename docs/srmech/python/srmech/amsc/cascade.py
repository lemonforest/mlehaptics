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


def pin_slot_at_zero(x: float) -> Tuple[int, float]:
    """Class K pin-slot at zero: split ``x`` into (orientation, magnitude).

    The pin enters or exits the slot at the zero-crossing — sign-flip IS the
    canonical Class K phase-boundary per
    ``[[user_stance_epicycle_via_gear_plus_pin]]``. Expressing this as a
    named cascade (rather than Python ``abs()``) keeps the cascade-count
    claimed in line with the cascade-count executed.

    Args:
        x: A real value.

    Returns:
        ``(orientation, magnitude)`` where ``orientation ∈ {-1, 0, +1}`` and
        ``magnitude >= 0``. The origin maps to ``(0, 0.0)``.
    """
    if x > 0.0:
        return +1, x
    if x < 0.0:
        return -1, -x
    return 0, 0.0


def reorient(orientation: int, value):
    """Class C cascade-orientation: re-apply a captured orientation.

    Args:
        orientation: An orientation in ``{-1, 0, +1}`` (typically the first
            element of a :func:`pin_slot_at_zero` result).
        value: The magnitude (or magnitude-derived quantity) to re-sign.

    Returns:
        ``-value`` when ``orientation < 0``, otherwise ``value`` unchanged.
    """
    if orientation < 0:
        return -value
    return value


def magnitude(x: float) -> float:
    """Class K pin-slot at zero, magnitude only (orientation discarded).

    The cascade-honest replacement for Python ``abs()`` when only the
    magnitude is needed (spectral radius, eigenvalue-magnitude proxy, …).

    Args:
        x: A real value.

    Returns:
        ``|x|`` as the Class K pin-slot magnitude (always ``>= 0``).
    """
    return pin_slot_at_zero(x)[1]


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

    Args:
        x: A real value (the irrational/float to anchor).
        max_denominator: Class N small-denominator ceiling.
        fine_scale: Integer scale turning the float magnitude into the
            ``(numerator, denominator)`` pair ``best_rational`` consumes.

    Returns:
        ``(signed_numerator, denominator)`` — the Class N convergent of
        ``x`` with the Class C sign re-applied. The origin and sub-dead-band
        magnitudes map to ``(0, 1)``.

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


def cyclic_gcd(a: int, b: int) -> int:
    """Class I cyclic gcd. Delegates to ``srmech.amsc.cyclic.gcd``.

    A cascade-named alias so number-theoretic cascades reach for the Class I
    primitive by its cascade name rather than ``math.gcd``.
    """
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

    Args:
        op: A unary callable mapping a sequence to a sequence (an A–N
            operator's action on a signal).
        x: The input sequence.

    Returns:
        ``chiral_flip(op(chiral_flip(x)))`` — ``op`` evaluated in the
        reversed Class-C orientation.
    """
    return chiral_flip(op(chiral_flip(x)))


def net_chirality(orientations) -> int:
    """Class C net handedness of a cascade: the product of per-op orientations.

    A cascade built from operators each carrying a Class C orientation in
    ``{-1, 0, +1}`` has a *net* handedness — the conserved Class-C invariant a
    chiral cascade reads out (MFO §VIII.31.11 §(5d); the net-chirality of
    Spike #74 / #89). Computed by composing :func:`reorient`, not by ``abs``-
    free sign multiplication, so the cascade-count matches the cascade-shape.

    Args:
        orientations: Iterable of orientations in ``{-1, 0, +1}`` (typically
            the first element of each operator's :func:`pin_slot_at_zero`).

    Returns:
        ``+1`` (net even / right-handed), ``-1`` (net odd / left-handed), or
        ``0`` if any operator is orientation-neutral (a zero-crossing in the
        chain collapses net handedness).
    """
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
