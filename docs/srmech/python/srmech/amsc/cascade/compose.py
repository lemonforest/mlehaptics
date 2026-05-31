"""Cascade **composites** — iterative algorithms over the atoms.

The two cascade ops in this tier are iterative *algorithms* built over
the silicon-able atoms in :mod:`srmech.amsc.cascade.atoms` — they are
NOT single 1:1 ISA intrinsics (per F208 / MS #20 forward-architecture):

- :func:`cyclic_gcd` — Euclid's algorithm (Class I; iterative remainder
  loop, delegating to ``srmech.amsc.cyclic.gcd``).
- :func:`best_rational_signed` — the Class K ∘ N ∘ C continued-fraction
  loop (sign-strip at the :func:`~srmech.amsc.cascade.atoms.pin_slot_at_zero`
  atom, Class N best-rational anchor of the magnitude, then re-sign at the
  :func:`~srmech.amsc.cascade.atoms.reorient` atom).

The 1:1 ISA intrinsics these compose over live in the sibling
:mod:`srmech.amsc.cascade.atoms` module.

**No ``abs()``** anywhere — sign is handled as the canonical Class K
pin-slot + Class C re-orientation per
``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``.

Each composite carries a dedicated C symbol in
``libsrmech.{so,dll,dylib}`` (the cascade ``cyclic_gcd`` wrapper is a
pure-delegation alias for the Class I ``srmech_gcd`` primitive; the
``best_rational_signed`` C peer delegates its Class N stage to
``srmech_best_rational``) AND a TOML descriptor under
``srmech/amsc/_research/cascade_catalog/``.
"""

from __future__ import annotations

import ctypes
import math
from typing import List, Sequence, Tuple

from srmech.amsc import _native
from srmech.amsc.cyclic import gcd as _cyclic_gcd
from srmech.amsc.rational import best_rational as _best_rational

from .atoms import pin_slot_at_zero, reorient, _ZERO_BAND

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

#: Default small-denominator ceiling for ``best_rational_signed`` (the
#: Class N rational anchor). Matches the precursor cascade-helper default.
DEFAULT_MAX_DENOMINATOR = 100

#: Default fine-scaling factor turning a float magnitude into the integer
#: pair ``srmech.amsc.rational.best_rational`` consumes.
DEFAULT_FINE_SCALE = 1_000_000


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
    if _is_pub(): _emit("cascade.best_rational_signed", class_="K∘N∘C", input_shape=_shape(x))
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
    if _is_pub(): _emit("cascade.cyclic_gcd", class_="I", input_shape=f"{_shape(a)}+{_shape(b)}")
    native = _try_native_cyclic_gcd(a, b)
    if native is not None:
        return native
    return _cyclic_gcd(a, b)


def _try_native_kuramoto_step(theta, omega, coupling, dt):
    """Native dispatch for the Kuramoto forward-Euler step.

    Returns ``list[float]`` on success or ``None`` to fall through to the
    Python composition path. Coerces ``theta`` / ``omega`` to float lists
    (numpy arrays, generators, etc. coerce via ``float(...)``); any
    coercion failure, a length mismatch, or a missing native symbol falls
    back to Python so the public behaviour is preserved exactly.
    """
    if not (_native.HAS_NATIVE and _native.LIB is not None):
        return None
    if not hasattr(_native.LIB, "srmech_cascade_kuramoto_step_f64"):
        return None
    try:
        th = [float(v) for v in theta]
        om = [float(v) for v in omega]
        k = float(coupling)
        h = float(dt)
    except (TypeError, ValueError):
        return None
    n = len(th)
    if len(om) != n:
        return None  # the Python path raises the ValueError with the message
    Arr = ctypes.c_double * n if n > 0 else ctypes.c_double * 1
    c_th = Arr(*th) if n > 0 else Arr()
    c_om = Arr(*om) if n > 0 else Arr()
    c_out = Arr()
    rc = _native.LIB.srmech_cascade_kuramoto_step_f64(
        ctypes.cast(c_th, ctypes.POINTER(ctypes.c_double)),
        ctypes.cast(c_om, ctypes.POINTER(ctypes.c_double)),
        ctypes.c_size_t(n),
        ctypes.c_double(k),
        ctypes.c_double(h),
        ctypes.cast(c_out, ctypes.POINTER(ctypes.c_double)),
    )
    if rc != _native.SRMECH_OK:
        return None
    return [float(c_out[i]) for i in range(n)]


def kuramoto_step(
    theta: Sequence[float],
    omega: Sequence[float],
    *,
    coupling: float = 1.0,
    dt: float = 0.01,
) -> List[float]:
    """Class I ∘ sin ∘ Σ ∘ C: one forward-Euler Kuramoto step.

    One forward-Euler step of the canonical Kuramoto coupled-oscillator
    model (Kuramoto 1975; Acebrón et al. 2005, *Rev. Mod. Phys.* 77:137)::

        theta_i <- theta_i + dt * ( omega_i
                                    + (coupling / n) * Σ_j sin(theta_j - theta_i) )

    The dispatch-clock / coupled-oscillator Euler step the spectral-research
    arc hand-rolled in Python (F141 / F231 / R-95 / F234) — now with a
    native C peer (``srmech_cascade_kuramoto_step_f64``) so srmech runs the
    Kuramoto step with **NO host Python** (the full-parity commitment). The
    O(n²) sin-coupling runs natively (libm sin, as ``srmech.amsc.kepler``
    does upstream).

    HONEST CASCADE SHAPE. This is a *composition* of existing class
    operations, NOT a new privileged primitive: Class I (the cyclic phase
    ``theta`` on the circle) + the sin coupling (asymptotic-calculus
    transcendental) + a sum-reduce over ``j`` + a Class-C Euler add
    (``theta + dt·f``). **No ``abs()``.**

    v0.6.0rc9: dispatches through the native C peer when ``HAS_NATIVE`` is
    True and ``theta`` / ``omega`` coerce to equal-length float sequences;
    pure-Python fallback otherwise. Parity is to **libm-trig tolerance**,
    NOT bit-exact across platforms (the kepler trig discipline) — the C
    peer and the Python fallback sum the coupling in the SAME index order.

    Args:
        theta: current phases (radians), length ``n``.
        omega: natural frequencies, length ``n`` (must match ``theta``).
        coupling: the global coupling constant ``K`` (default ``1.0``).
        dt: the forward-Euler time step (default ``0.01``).

    Returns:
        ``list[float]`` — the ``n`` phases after one forward-Euler step.
        ``n == 1`` is pure drift (the coupling sum ``sin(0)`` vanishes);
        ``n == 0`` is ``[]``.

    Raises:
        ValueError: if ``len(omega) != len(theta)``.
    """
    if _is_pub(): _emit("cascade.kuramoto_step", class_="I∘sin∘Σ∘C", input_shape=_shape(theta))
    theta_list = list(theta)
    omega_list = list(omega)
    n = len(theta_list)
    if len(omega_list) != n:
        raise ValueError(
            f"cascade.kuramoto_step: omega length {len(omega_list)} != "
            f"theta length {n}"
        )
    native = _try_native_kuramoto_step(theta_list, omega_list, coupling, dt)
    if native is not None:
        return native
    # Python fallback — the SAME composition + the SAME coupling-sum index
    # order as the C peer (so same-platform results match to the last bit).
    inv_n = (float(coupling) / n) if n > 0 else 0.0
    h = float(dt)
    out: List[float] = []
    for i in range(n):
        theta_i = float(theta_list[i])
        coupling_sum = 0.0
        for j in range(n):
            coupling_sum += math.sin(float(theta_list[j]) - theta_i)
        out.append(theta_i + h * (float(omega_list[i]) + inv_n * coupling_sum))
    return out


__all__ = [
    "DEFAULT_MAX_DENOMINATOR",
    "DEFAULT_FINE_SCALE",
    "cyclic_gcd",
    "best_rational_signed",
    "kuramoto_step",
]
