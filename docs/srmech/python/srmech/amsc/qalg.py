"""srmech.amsc.qalg — the framework-native EXACT number-field carrier (``Qalg``).

The generalisation of :class:`srmech.amsc.qi.Qi`. Where ``Qi`` carries an exact
element of the ONE number field **ℚ[x]/(x²+1)** (the Gaussian rationals — exact
ℂ over ℚ), ``Qalg`` carries an exact element of **ℚ[x]/(m(x))** for ANY monic
irreducible ``m ∈ ℤ[x]`` — an exact element of the algebraic number field ℚ(α),
where α is a root of ``m``. ``Qi`` is literally ``Qalg`` specialised to
``m(x) = x²+1`` (the headline equivalence test): the Gaussian-rational product
``(a+bi)(c+di) = (ac−bd)+(ad+bc)i`` IS polynomial-multiply-then-reduce-mod-(x²+1),
and that is exactly what ``Qalg.__mul__`` does for the general ``m``.

This is the exact-substrate carrier for algebraic numbers — the rotation-last
roadmap's rc-C, the foundation for exact eigenvectors (rc-D). The whole body
stays exact ``Q`` (Class-N rational) arithmetic; there is exactly ONE terminal
rotation — :meth:`to_complex` / :meth:`to_float` — a Horner evaluation of the
exact coordinate polynomial at a caller-supplied embedding ``root`` (the single
FPU lift, the "rotation last"). The algebra itself NEVER touches ``root``; an
element with ``root=None`` is a perfectly valid field element you simply cannot
project to a float until you give it an embedding.

**State.** An element is ``Σ_{i<n} coords[i]·αⁱ`` with ``n = deg(m)``:

* ``m`` — the minimal polynomial as a tuple of ``int`` coefficients **low→high,
  MONIC**: ``m = (m₀, m₁, …, m_{n−1}, 1)``, length ``n+1``, leading coeff 1.
* ``coords`` — a tuple of exact :class:`~srmech.amsc.q.Q` of length ``n``.
* ``root`` — an OPTIONAL explicit embedding root (a Python ``float`` or
  ``complex``), used ONLY by the terminal projection. The exact field arithmetic
  is embedding-agnostic.

**Exact field algebra (pure ``Q``).** ``+`` / ``−`` / ``−x`` are coordinatewise
(Class-K sign for negation / subtraction — never an ALU ``abs``). ``*`` convolves
the two coordinate tuples (degree ≤ 2n−2) then **reduces mod m** using the monic
relation ``αⁿ = −Σ_{i<n} m[i]·αⁱ`` (fold the top coefficient down repeatedly).
``inverse`` / ``/`` run the extended Euclidean algorithm on the coordinate
polynomial ``b(x)`` and ``m(x)`` in ℚ[x] — ``m`` irreducible + ``b ≠ 0``, deg < n
⇒ coprime ⇒ ``gcd`` is a nonzero constant ``g``, and ``u·b + v·m = g`` gives the
inverse ``(u/g) mod m``. ``**`` is integer-exponent square-and-multiply (negative
via :meth:`inverse`, ``k == 0`` → the field one). Scalar ``*`` by ``Q`` / ``int``
/ ``Fraction`` is supported.

A ``_same_field`` guard requires equal ``m`` on every binary op (``ValueError``
on mismatch). ``Qalg`` is NOT registered with ``numbers.Complex`` /
``numbers.Number`` — registering a numeric ABC obligates the FULL dunder protocol
(the rc10/rc11 ``Fraction``-protocol trap), so ``Qalg`` stays a standalone exact
carrier with just the dunders documented here. No ``math`` module, no numpy, no
``float`` in the algebra (only at the terminal projection).
"""

from __future__ import annotations

from fractions import Fraction

from .q import Q

__all__ = ["Qalg"]

_Q_ZERO = Q(0, 1)
_Q_ONE = Q(1, 1)


def _to_q(value):
    """Coerce ``value`` to an exact :class:`~srmech.amsc.q.Q`, or ``None`` if it
    is not an exact-rational-coercible scalar (mirrors ``qi._to_q``)."""
    if isinstance(value, Q):
        return value
    if isinstance(value, bool):
        return Q(int(value), 1)
    if isinstance(value, int):
        return Q(value, 1)
    if isinstance(value, Fraction):
        return Q(value.numerator, value.denominator)
    if isinstance(value, float):
        try:
            return Q.from_float(value)               # exact ratio of the float
        except (OverflowError, ValueError):
            return None
    if (isinstance(value, (tuple, list)) and len(value) == 2
            and isinstance(value[0], int) and isinstance(value[1], int)
            and value[1] != 0):
        return Q(value[0], value[1])
    pair = getattr(value, "as_pair", None) or getattr(value, "as_integer_ratio", None)
    if pair is not None:
        try:
            n, d = pair()
            return Q(int(n), int(d))
        except (TypeError, ValueError, ZeroDivisionError):
            return None
    return None


def _int_exponent(exp):
    """The int value of ``exp`` if it is an integer-valued exponent (a plain
    ``int``, ``bool`` excluded, or a rational with denominator 1), else ``None``
    — matching ``Qi`` / ``fractions.Fraction`` (``** 2.0`` is a float)."""
    if isinstance(exp, bool):
        return None
    if isinstance(exp, int):
        return exp
    den = getattr(exp, "denominator", None)
    num = getattr(exp, "numerator", None)
    if den is not None and num is not None:
        try:
            if den == 1:
                return int(num)
        except (TypeError, ValueError):
            return None
    return None


def _validate_m(m):
    """Coerce / validate the minimal polynomial ``m`` to a tuple of ``int``,
    low→high, monic (leading coeff 1), degree ≥ 1. Returns the int tuple."""
    if not isinstance(m, (tuple, list)) or len(m) < 2:
        raise ValueError(
            "Qalg m must be a coefficient sequence low→high of length n+1 "
            f"(deg ≥ 1); got {m!r}")
    coeffs = tuple(m)
    for c in coeffs:
        if not isinstance(c, int) or isinstance(c, bool):
            raise ValueError(
                f"Qalg m coefficients must be plain ints (monic ℤ[x]); got {c!r}")
    if coeffs[-1] != 1:
        raise ValueError(
            f"Qalg m must be MONIC (leading coeff 1, low→high); got {coeffs!r}")
    return coeffs


# ── exact polynomial helpers over Q (low→high coefficient lists) ────────────
def _poly_trim(p):
    """Drop trailing ``Q`` zeros (normalise a coefficient list to its degree)."""
    i = len(p)
    while i > 0 and p[i - 1] == 0:
        i -= 1
    return p[:i]


def _poly_divmod(a, b):
    """Exact polynomial long division ``a = q·b + r`` over ℚ (coeff lists of
    ``Q``, low→high). ``b`` must be nonzero. Returns ``(q, r)``."""
    a = _poly_trim(list(a))
    b = _poly_trim(list(b))
    if not b:
        raise ZeroDivisionError("Qalg polynomial division by the zero polynomial")
    q = [_Q_ZERO] * max(0, len(a) - len(b) + 1)
    r = list(a)
    lead = b[-1]
    while len(r) >= len(b) and _poly_trim(r):
        deg_diff = len(r) - len(b)
        factor = r[-1] / lead
        q[deg_diff] = factor
        for i, bc in enumerate(b):
            r[deg_diff + i] = r[deg_diff + i] - factor * bc
        r = _poly_trim(r)
    return q, r


def _poly_ext_gcd(a, b):
    """Extended Euclidean algorithm over ℚ[x]: returns ``(g, u, v)`` with
    ``u·a + v·b = g`` (coeff lists of ``Q``, low→high). ``g`` is the (unnormalised)
    gcd — a nonzero constant when ``a``, ``b`` are coprime."""
    old_r, r = _poly_trim(list(a)), _poly_trim(list(b))
    old_u, u = [_Q_ONE], [_Q_ZERO]
    old_v, v = [_Q_ZERO], [_Q_ONE]
    while _poly_trim(r):
        quot, _ = _poly_divmod(old_r, r)
        old_r, r = r, _poly_trim(_poly_sub(old_r, _poly_mul(quot, r)))
        old_u, u = u, _poly_trim(_poly_sub(old_u, _poly_mul(quot, u)))
        old_v, v = v, _poly_trim(_poly_sub(old_v, _poly_mul(quot, v)))
    return old_r, old_u, old_v


def _poly_mul(a, b):
    """Exact polynomial multiply over ℚ (coeff lists of ``Q``, low→high)."""
    a = _poly_trim(list(a))
    b = _poly_trim(list(b))
    if not a or not b:
        return []
    out = [_Q_ZERO] * (len(a) + len(b) - 1)
    for i, ac in enumerate(a):
        if ac == 0:
            continue
        for j, bc in enumerate(b):
            out[i + j] = out[i + j] + ac * bc
    return out


def _poly_sub(a, b):
    """Exact polynomial subtract ``a − b`` over ℚ (coeff lists of ``Q``)."""
    n = max(len(a), len(b))
    out = []
    for i in range(n):
        ai = a[i] if i < len(a) else _Q_ZERO
        bi = b[i] if i < len(b) else _Q_ZERO
        out.append(ai - bi)
    return out


class Qalg:
    """An exact element ``Σ coords[i]·αⁱ`` of the number field ℚ[x]/(m), where α
    is a root of the monic irreducible ``m``. The exact-substrate carrier for
    algebraic numbers; ``Qi`` is ``Qalg`` over ``x²+1``. See the module
    docstring."""

    __slots__ = ("_m", "_coords", "_root")

    def __init__(self, m, coords, root=None) -> None:
        mm = _validate_m(m)
        n = len(mm) - 1
        if not isinstance(coords, (tuple, list)):
            raise TypeError(
                f"Qalg coords must be a sequence of length deg(m)={n}; "
                f"got {type(coords).__name__}")
        if len(coords) != n:
            raise ValueError(
                f"Qalg coords must have length deg(m)={n}; got {len(coords)}")
        cs = []
        for c in coords:
            q = _to_q(c)
            if q is None:
                raise TypeError(
                    f"Qalg coords must be exact-rational (Q/int/Fraction/pair); "
                    f"got {type(c).__name__}")
            cs.append(q)
        self._m = mm
        self._coords = tuple(cs)
        self._root = root

    # ── constructors ────────────────────────────────────────────────────────
    @classmethod
    def alpha(cls, m, root=None) -> "Qalg":
        """The field generator α (coords ``[0, 1, 0, …]``)."""
        n = len(_validate_m(m)) - 1
        coords = [_Q_ZERO] * n
        if n >= 2:
            coords[1] = _Q_ONE
        elif n == 1:
            # ℚ[x]/(x − r): α is the constant r itself = −m₀ (m = (m₀, 1)).
            coords[0] = -_to_q(m[0])
        return cls(m, coords, root=root)

    @classmethod
    def rational(cls, q, m, root=None) -> "Qalg":
        """A constant element ``q`` (coords ``[q, 0, …]``)."""
        n = len(_validate_m(m)) - 1
        qq = _to_q(q)
        if qq is None:
            raise TypeError(f"Qalg.rational q must be exact-rational; got {q!r}")
        coords = [_Q_ZERO] * n
        coords[0] = qq
        return cls(m, coords, root=root)

    def one(self) -> "Qalg":
        """The field multiplicative identity in this element's field (coords
        ``[1, 0, …]``), carrying this element's ``m`` + ``root``."""
        return Qalg.rational(_Q_ONE, self._m, root=self._root)

    # ── exact accessors ─────────────────────────────────────────────────────
    @property
    def m(self):
        return self._m

    @property
    def coords(self):
        return self._coords

    @property
    def root(self):
        return self._root

    @property
    def degree(self) -> int:
        return len(self._m) - 1

    def with_root(self, root) -> "Qalg":
        """Same exact element with an embedding ``root`` attached (for the
        terminal projection); the algebra is unchanged."""
        return Qalg(self._m, self._coords, root=root)

    # ── field guard ─────────────────────────────────────────────────────────
    def _same_field(self, other: "Qalg") -> None:
        if not isinstance(other, Qalg):
            raise ValueError("Qalg binary op requires another Qalg")
        if self._m != other._m:
            raise ValueError(
                f"Qalg binary op requires equal m; got {self._m!r} vs {other._m!r}")

    def _pick_root(self, other: "Qalg"):
        """The embedding root to carry on a binary-op result — prefer self's,
        fall back to other's (the algebra itself is root-agnostic)."""
        return self._root if self._root is not None else other._root

    # ── reprs / equality ────────────────────────────────────────────────────
    def __repr__(self) -> str:
        return f"Qalg({self._m!r}, {self._coords!r})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Qalg):
            return NotImplemented
        return self._m == other._m and self._coords == other._coords

    def __ne__(self, other) -> bool:
        eq = self.__eq__(other)
        return eq if eq is NotImplemented else not eq

    def __hash__(self) -> int:
        return hash((self._m, self._coords))

    def __bool__(self) -> bool:
        return any(c != 0 for c in self._coords)

    # ── additive group (coordinatewise; Class-K sign) ───────────────────────
    def __add__(self, other):
        if isinstance(other, Qalg):
            self._same_field(other)
            coords = tuple(a + b for a, b in zip(self._coords, other._coords))
            return Qalg(self._m, coords, root=self._pick_root(other))
        q = _to_q(other)
        if q is None:
            return NotImplemented
        return self + Qalg.rational(q, self._m, root=self._root)

    __radd__ = __add__

    def __sub__(self, other):
        if isinstance(other, Qalg):
            self._same_field(other)
            coords = tuple(a - b for a, b in zip(self._coords, other._coords))
            return Qalg(self._m, coords, root=self._pick_root(other))
        q = _to_q(other)
        if q is None:
            return NotImplemented
        return self - Qalg.rational(q, self._m, root=self._root)

    def __rsub__(self, other):
        q = _to_q(other)
        if q is None:
            return NotImplemented
        return Qalg.rational(q, self._m, root=self._root) - self

    def __neg__(self) -> "Qalg":
        return Qalg(self._m, tuple(-c for c in self._coords), root=self._root)

    def __pos__(self) -> "Qalg":
        return Qalg(self._m, self._coords, root=self._root)

    # ── multiplicative group (convolve then reduce mod m) ───────────────────
    def _reduce(self, conv):
        """Reduce a degree ≤ 2n−2 coefficient list ``conv`` (list of ``Q``) mod
        ``m`` using the monic relation ``αⁿ = −Σ_{i<n} m[i]·αⁱ``. Returns a tuple
        of ``Q`` of length n."""
        n = self.degree
        work = list(conv)
        # Fold every coefficient at index ≥ n down into indices [0, n).
        for idx in range(len(work) - 1, n - 1, -1):
            top = work[idx]
            if top == 0:
                continue
            work[idx] = _Q_ZERO
            # αⁱᵈˣ = αⁱᵈˣ⁻ⁿ · αⁿ = αⁱᵈˣ⁻ⁿ · (−Σ m[j]·αʲ)
            base = idx - n
            for j in range(n):                     # m[j] is the int coeff
                if self._m[j] != 0:
                    work[base + j] = work[base + j] - top * self._m[j]
        return tuple(work[:n])

    def __mul__(self, other):
        if isinstance(other, Qalg):
            self._same_field(other)
            n = self.degree
            conv = [_Q_ZERO] * (2 * n - 1)
            for i, a in enumerate(self._coords):
                if a == 0:
                    continue
                for j, b in enumerate(other._coords):
                    if b == 0:
                        continue
                    conv[i + j] = conv[i + j] + a * b
            return Qalg(self._m, self._reduce(conv), root=self._pick_root(other))
        # scalar multiply by an exact rational
        q = _to_q(other)
        if q is None:
            return NotImplemented
        return Qalg(self._m, tuple(c * q for c in self._coords), root=self._root)

    __rmul__ = __mul__

    def inverse(self) -> "Qalg":
        """The exact multiplicative inverse in ℚ[x]/(m), via the extended
        Euclidean algorithm on the coordinate polynomial ``b(x)`` and ``m(x)``:
        ``u·b + v·m = g`` (a nonzero constant since ``m`` is irreducible and
        ``b ≠ 0``), so the inverse is ``(u / g) mod m``. Raises
        ``ZeroDivisionError`` on the zero element."""
        b = list(self._coords)
        if not _poly_trim(b):
            raise ZeroDivisionError("Qalg: cannot invert the zero element")
        m_poly = [Q(c, 1) for c in self._m]
        g, u, _v = _poly_ext_gcd(b, m_poly)
        g = _poly_trim(g)
        if len(g) != 1:
            # m irreducible + 0 < deg(b) < deg(m) ⇒ gcd is a nonzero constant;
            # a non-constant gcd means m was not actually irreducible.
            raise ZeroDivisionError(
                "Qalg: non-invertible element (m not irreducible over this b?)")
        g0 = g[0]
        inv_coords = [c / g0 for c in u]
        # (u / g) may have degree < or, defensively, ≥ n: reduce mod m.
        n = self.degree
        if len(inv_coords) < n:
            inv_coords = inv_coords + [_Q_ZERO] * (n - len(inv_coords))
        return Qalg(self._m, self._reduce(inv_coords), root=self._root)

    def __truediv__(self, other):
        if isinstance(other, Qalg):
            self._same_field(other)
            return self * other.inverse()
        q = _to_q(other)
        if q is None:
            return NotImplemented
        if q == 0:
            raise ZeroDivisionError("Qalg division by zero scalar")
        return Qalg(self._m, tuple(c / q for c in self._coords), root=self._root)

    def __rtruediv__(self, other):
        q = _to_q(other)
        if q is None:
            return NotImplemented
        return Qalg.rational(q, self._m, root=self._root) * self.inverse()

    def __pow__(self, exp):
        """Integer-exponent power (``bool`` excluded). ``k ≥ 0`` is
        square-and-multiply over :meth:`__mul__`; ``k < 0`` via :meth:`inverse`;
        ``k == 0`` → the field one."""
        e = _int_exponent(exp)
        if e is None:
            return NotImplemented
        if e == 0:
            return self.one()
        base = self if e > 0 else self.inverse()
        k = e if e > 0 else -e
        result = self.one()
        while k:
            if k & 1:
                result = result * base
            k >>= 1
            if k:
                base = base * base
        return result

    # ── terminal projection — the ONE rotation (requires root) ──────────────
    def to_complex(self) -> complex:
        """Horner-evaluate the exact coordinate polynomial at ``self.root`` and
        return a builtin ``complex``. This is the single FPU lift / "rotation
        last" — the body stayed exact ``Q`` until here. Requires an embedding
        ``root`` (a Python ``float`` or ``complex``); exact root isolation /
        refinement is deliberately rc-E, so for rc-C the caller supplies it."""
        if self._root is None:
            raise ValueError(
                "Qalg.to_complex requires an embedding root; attach one with "
                "Qalg(m, coords, root=...) or .with_root(root)")
        r = complex(self._root)
        acc = 0j
        for c in reversed(self._coords):            # Horner, high→low
            acc = acc * r + complex(float(c))
        return acc

    def to_float(self) -> float:
        """Horner-evaluate at a REAL ``self.root`` and return a builtin ``float``.
        Raises ``ValueError`` if ``root`` is non-real or the evaluated value has a
        nonzero imaginary part."""
        if self._root is None:
            raise ValueError(
                "Qalg.to_float requires a (real) embedding root; attach one with "
                "Qalg(m, coords, root=...) or .with_root(root)")
        if isinstance(self._root, complex) and self._root.imag != 0:
            raise ValueError(
                f"Qalg.to_float requires a real root; got complex {self._root!r}")
        z = self.to_complex()
        if z.imag != 0:
            raise ValueError(
                f"Qalg.to_float: value has a nonzero imaginary part ({z!r})")
        return z.real
