"""srmech.amsc.complex128 — the framework-native double-precision complex scalar
carrier (``Complex128``).

The complex sibling of :class:`srmech.amsc.q.Q`. Where ``Q`` carries an **exact**
real scalar (a reduced ``(num, den)`` rational that collapses to a decimal only
at ``float(q)``), ``Complex128`` carries a **float** complex scalar — the
display-boundary type for values that are genuinely complex *and* irrational
(``e^{iθ}``, an eigenvalue, a ``the_one`` component) and so cannot be held as an
exact rational. ``Complex128`` is to a complex value what ``float`` is to a real
one: the place the cascade collapses when the value leaves the rationals.

Why a framework-owned handle and not the builtin ``complex``: identical reason to
``Mat``/``Vec``/``HV`` over ``numpy.ndarray`` — a builtin-``complex`` value
invites ad-hoc float math on it; a ``Complex128`` handle keeps complex scalars
inside the srmech carrier family (introspection, attestation, the cascade) and
maps **1:1 to C99 ``double _Complex``** — re and im are two ``float64``, the same
interleaved ``(re, im)`` the ``Mat``/``Vec``/``HV`` carriers and the native
kernels already speak, which closes the scalar-complex C-parity. Internally it
wraps a Python ``complex`` (which *is* two ``float64``); ``complex(z)`` is the
boundary collapse back to the builtin.
"""

from __future__ import annotations

import numbers

from . import rational as _rational

__all__ = ["Complex128"]


def _coerce(value):
    """Coerce to a Python ``complex``, or ``None`` if ``value`` is a type
    ``Complex128`` cannot exactly combine/compare with (so the dunder returns
    ``NotImplemented`` and Python tries the reflected op)."""
    if isinstance(value, Complex128):
        return value._z
    if isinstance(value, (int, float, complex)):
        return complex(value)
    # A Q (exact real) is a real complex value.
    if hasattr(value, "as_pair") and hasattr(value, "__float__"):
        try:
            return complex(float(value))
        except (TypeError, ValueError):
            return None
    # Any other ``numbers.Complex`` carrier — notably the EXACT ``Qi`` — collapses
    # to the float boundary here. ``Complex128`` is the documented sink for a value
    # that leaves the rationals, so ``Qi`` (exact) combined with a ``Complex128``
    # (float) yields a ``Complex128`` — exact-meets-float → float, the same
    # direction as ``Fraction(1, 2) + 0.5 → 1.0``. This makes ``Complex128`` a
    # consumer surface for every framework-native complex carrier.
    if isinstance(value, numbers.Complex):
        try:
            return complex(value)
        except (TypeError, ValueError, OverflowError):
            return None
    return None


class Complex128:
    """A double-precision complex scalar — two ``float64`` (re, im), the
    framework-native carrier for genuinely-complex values. Collapses to the
    builtin ``complex`` only via ``complex(z)``. See the module docstring."""

    __slots__ = ("_z",)

    def __init__(self, re=0.0, im=0.0) -> None:
        if isinstance(re, Complex128):
            self._z = re._z
        elif isinstance(re, complex):
            # Complex128(some_complex) — im is the default 0.0 sentinel.
            self._z = re
        else:
            self._z = complex(float(re), float(im))

    # ── construction helpers ────────────────────────────────────────────────
    @classmethod
    def from_complex(cls, z: complex) -> "Complex128":
        return cls(complex(z))

    # ── components (always recoverable as float64) ──────────────────────────
    @property
    def real(self) -> float:
        return self._z.real

    @property
    def imag(self) -> float:
        return self._z.imag

    def as_pair(self):
        """The ``(re, im)`` float64 pair."""
        return (self._z.real, self._z.imag)

    def __iter__(self):
        """Unpack as ``re, im = z``."""
        yield self._z.real
        yield self._z.imag

    # ── the boundary collapse to the builtin complex ────────────────────────
    def __complex__(self) -> complex:
        return self._z

    # ── reprs ───────────────────────────────────────────────────────────────
    def __repr__(self) -> str:
        return f"Complex128({self._z.real!r}, {self._z.imag!r})"

    def __str__(self) -> str:
        return str(self._z)

    def __bool__(self) -> bool:
        return self._z != 0

    def __hash__(self) -> int:
        # Mirror builtin complex hashing so Complex128(1, 2) hashes equal to the
        # builtin 1+2j it == 's (data-model invariant).
        return hash(self._z)

    def __eq__(self, other) -> bool:
        z = _coerce(other)
        return NotImplemented if z is None else self._z == z

    def __ne__(self, other) -> bool:
        z = _coerce(other)
        return NotImplemented if z is None else self._z != z

    # ── arithmetic (builtin complex float ops — no `math` module) ───────────
    def _combine(self, other, op):
        z = _coerce(other)
        if z is None:
            return NotImplemented
        return Complex128(op(self._z, z))

    def __add__(self, other):
        return self._combine(other, lambda a, b: a + b)

    def __radd__(self, other):
        return self._combine(other, lambda a, b: b + a)

    def __sub__(self, other):
        return self._combine(other, lambda a, b: a - b)

    def __rsub__(self, other):
        return self._combine(other, lambda a, b: b - a)

    def __mul__(self, other):
        return self._combine(other, lambda a, b: a * b)

    def __rmul__(self, other):
        return self._combine(other, lambda a, b: b * a)

    def __truediv__(self, other):
        return self._combine(other, lambda a, b: a / b)

    def __rtruediv__(self, other):
        return self._combine(other, lambda a, b: b / a)

    def __neg__(self) -> "Complex128":
        return Complex128(-self._z)

    def __pos__(self) -> "Complex128":
        return Complex128(self._z)

    def __pow__(self, other):
        """``z ** w`` — the builtin float-complex power (this is the float boundary
        carrier; an integer ``w`` is repeated multiply, a general ``w`` rides the
        builtin ``complex`` exp/log). Part of the :class:`numbers.Complex` contract."""
        return self._combine(other, lambda a, b: a ** b)

    def __rpow__(self, other):
        return self._combine(other, lambda a, b: b ** a)

    # ── complex-specific ────────────────────────────────────────────────────
    def conjugate(self) -> "Complex128":
        """Complex conjugate — Class-K sign-flip on the imaginary part (never an
        ALU abs)."""
        return Complex128(self._z.real, -self._z.imag)

    def norm_sq(self) -> float:
        """``|z|² = re² + im²`` — the exact-if-rational squared modulus (pure
        float mult/add; no transcendental, no ``math``)."""
        re, im = self._z.real, self._z.imag
        return re * re + im * im

    def __abs__(self):
        """Modulus ``|z| = √(re² + im²)`` via the srmech Class-N
        :func:`srmech.amsc.rational.sqrt` (not ``math.hypot``/``math.sqrt``).
        Genuinely irrational → the exact-rational :class:`~srmech.amsc.q.Q` boundary
        (itself a :class:`numbers.Real`, so ``abs(z)`` is a Real, as the
        :class:`numbers.Complex` contract requires)."""
        return _rational.sqrt(self.norm_sq())


# ``Complex128`` implements the full :class:`numbers.Complex` surface — ``real`` /
# ``imag`` / ``conjugate`` / ``__complex__`` / ``__abs__`` / ``__bool__`` / ``==``
# / the arithmetic ring incl. ``__pow__`` / ``__rpow__`` — so it IS a genuine
# ``numbers.Complex`` (hence ``numbers.Number``). Registering makes
# ``isinstance(z, numbers.Complex)`` True, the scalar-carrier peer of ``Q``'s
# ``numbers.Rational`` registration.
numbers.Complex.register(Complex128)
