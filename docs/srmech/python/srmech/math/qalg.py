"""srmech.math.qalg — the framework-native EXACT number-field carrier (``Qalg``).

The generalisation of :class:`srmech.math.qi.Qi`. Where ``Qi`` carries an exact
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
* ``coords`` — a tuple of exact ``Q`` of length ``n``.
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
carrier with just the dunders documented here. No ``math`` module, no
``float`` in the algebra (only at the terminal projection).

**Cyclotomic trigonometry (v0.9.0rc463, `#T1188`).** The module also ships the
two named constructors :func:`cos_2pi_over_n` and :func:`sin_2pi_over_n`, which
return ``cos(2π/n)`` and ``sin(2π/n)`` as EXACT ``Qalg`` elements over a
cyclotomic minimal polynomial ``Φ`` — no float, no series truncation, no
``math`` module. They are the bottom-up carrier-native answer to the
``math.cos(2*pi/n)`` shortcut: the value is not approximated and then
rationalised, it is CONSTRUCTED in the field where it already lives.
"""

from __future__ import annotations

from .cyclic import gcd as _gcd
from .poly import cyclotomic_polynomial
from .q import Q

__all__ = [
    "MAX_CYCLOTOMIC_INDEX",
    "Qalg",
    "cos_2pi_over_n",
    "sin_2pi_over_n",
]

#: The measured index cap shared by :func:`cos_2pi_over_n` and
#: :func:`sin_2pi_over_n`. The cost of both ops is set by the DEGREE of the
#: field they build (``φ`` of the cyclotomic index), and exact ``Q``
#: multiplication in a degree-``d`` field is ``O(d²)`` rational operations.
#: Measured on this tree at the cap: ``cos_2pi_over_n`` worst case ``n = 255``
#: at 0.06 s; ``sin_2pi_over_n`` worst case ``n = 251`` (field ``Φ_1004``,
#: degree 500) at 1.20 s. One index above the cap, ``n = 257``, already puts
#: ``sin`` in a degree-512 field at 1.64 s, and ``n = 509`` at 6.40 s. The cap
#: matches the sibling ``srmech.math.laplacian.cyclic_laplacian_spectrum``,
#: which bounds the SAME ℚ(ζ_n) carrier at the same 256 for the same reason.
MAX_CYCLOTOMIC_INDEX = 256

_Q_ZERO = Q(0, 1)
_Q_ONE = Q(1, 1)


def _to_q(value):
    """Coerce ``value`` to an exact ``Q``, or ``None`` if it
    is not an exact-rational-coercible scalar (mirrors ``qi._to_q``)."""
    if isinstance(value, Q):
        return value
    if isinstance(value, bool):
        return Q(int(value), 1)
    if isinstance(value, int):
        return Q(value, 1)
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

    def is_rational(self) -> bool:
        """True when this element lies in the prime field ℚ ⊂ ℚ[x]/(m) — i.e.
        every coordinate above ``α⁰`` vanishes, so the element IS its own
        ``coords[0]``.

        **The decidable oracle.** Membership in ℚ is a FIELD-THEORETIC property,
        not a presentation artefact: ℚ is the unique degree-1 subfield of ℚ(α),
        so "is this element rational" survives any change of ℚ-basis. It is the
        exact test the ``srmech.music`` domain slice uses to return a commensurability
        verdict that CAN say *inharmonic* — Class-I gcd/lcm structurally cannot,
        because a finite lcm always exists (v0.9.0rc362).
        """
        return all(c == 0 for c in self._coords[1:])

    def as_rational(self):
        """This element's ``Q`` value when
        :meth:`is_rational`, else ``None`` — the exact projection down to the
        prime field, with NO float and NO approximation anywhere."""
        return self._coords[0] if self.is_rational() else None

    def __eq__(self, other) -> bool:
        """Exact field equality, with ``int`` / ``Q`` / ``Fraction`` COERCED into
        the field first.

        v0.9.0rc362 (`#T1041`) fixes a coercion defect: ``__mul__`` / ``__add__``
        already coerce an exact-rational scalar into the field (via
        :meth:`rational`), but ``__eq__`` returned ``NotImplemented`` for
        anything that was not already a ``Qalg``. Python then fell back to
        identity, so ``Qalg.alpha([-2, 0, 1]) ** 2`` — coords ``(Q(2,1), Q(0,1))``,
        the field element 2 — compared **False** against both ``2`` and
        ``Q(2, 1)`` while comparing **True** against ``Qalg.rational(2, m)``.
        The same value, three spellings, two answers. A scalar now coerces on
        comparison exactly as it does under the ring ops.

        A ``Qalg`` from a DIFFERENT field is unequal rather than an error: ``==``
        is a total predicate (unlike ``+`` / ``*``, which legitimately raise via
        :meth:`_same_field` because the *result* would be ill-defined).
        """
        if isinstance(other, Qalg):
            return self._m == other._m and self._coords == other._coords
        q = _to_q(other)
        if q is None:
            return NotImplemented
        # A scalar equals this element iff the element is rational AND that
        # rational is the scalar. No field is constructed — the coordinate
        # read is the whole test.
        return self.is_rational() and self._coords[0] == q

    def __ne__(self, other) -> bool:
        eq = self.__eq__(other)
        return eq if eq is NotImplemented else not eq

    def __hash__(self) -> int:
        """Hash consistent with :meth:`__eq__` (the Python data-model invariant:
        equal objects hash equal). A RATIONAL element now hashes as its ``Q``
        does — so ``Qalg.rational(2, m)``, ``Q(2, 1)`` and ``2`` share a hash
        bucket, matching the rc362 coercion. A non-rational element cannot equal
        any scalar, so it keeps the ``(m, coords)`` pair hash."""
        if self.is_rational():
            return hash(self._coords[0])
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


# ── cyclotomic trigonometry (rc463, `#T1188`) ────────────────────────────────
def _validated_index(n, where: str) -> int:
    """The shared Class-J index guard for the cyclotomic trig constructors.

    ``n`` must be a plain ``int`` (``bool`` is refused — ``True`` is not the
    index 1), at least 1, and at most :data:`MAX_CYCLOTOMIC_INDEX`. Returns
    ``n`` so the caller can use the guard inline."""
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError(
            f"{where}: n must be a plain int (the cyclotomic index); "
            f"got {type(n).__name__}")
    if n < 1:
        raise ValueError(f"{where} requires n >= 1; got {n}")
    if n > MAX_CYCLOTOMIC_INDEX:
        raise ValueError(
            f"{where} requires n <= {MAX_CYCLOTOMIC_INDEX} "
            f"(the measured field-degree cap); got {n}")
    return n


def _cyclotomic_m(index: int):
    """The monic ℤ[x] minimal polynomial ``Φ_index`` as the ASCENDING int tuple
    ``Qalg`` wants for its ``m`` — Class J, the divisor-lattice construction in
    :func:`srmech.math.poly.cyclotomic_polynomial`."""
    return tuple(cyclotomic_polynomial(index)["coefficients"])


def cos_2pi_over_n(n: int) -> "Qalg":
    """``cos(2π/n)`` as an EXACT :class:`Qalg` element of ℚ(ζ_n) = ℚ[x]/(Φ_n).

    The returned element IS the cosine — no float, no series, no rational
    approximation. With ``α = ζ_n`` the class of ``x`` in ℚ[x]/(Φ_n),

        ``cos(2π/n) = (ζ + ζ⁻¹) / 2``  and  ``ζ⁻¹ = ζ^(n−1)``,

    so the whole construction is one power, one add and one exact halving in
    the ``Q`` coordinate ring. The minimal polynomial of the returned element
    is ``Φ_n`` and its ``.coords`` are ``φ(n)`` exact ``Q`` in the ``α`` power
    basis, ASCENDING.

    **Cascade composition.** Class J (the cyclotomic divisor lattice that
    builds ``Φ_n``) ∘ Class N (the exact rational coordinates the value is
    carried in) ∘ Class C (the ζ rotation — ``ζ`` and ``ζ⁻¹`` are the two
    chiralities of the same turn, and the cosine is their symmetric part).
    No ``abs`` anywhere: the ``−1/2`` coordinates below are ordinary field
    coordinates, not a stripped sign.

    Args:
        n: the cyclotomic index, ``1 <= n <= MAX_CYCLOTOMIC_INDEX`` (256).
            ``TypeError`` for a non-``int`` (``bool`` included);
            ``ValueError`` outside the range.

    Returns:
        ``Qalg`` over ``m = Φ_n``, with ``root=None`` — no embedding is
        attached, because computing ``e^(2πi/n)`` would need exactly the FPU
        transcendental this op exists to avoid. Attach one yourself with
        ``.with_root(...)`` when you want the terminal projection.

    Worked anchors::

        cos_2pi_over_n(8)
        # -> Qalg((1, 0, 0, 0, 1), (Q(0, 1), Q(1, 2), Q(0, 1), Q(-1, 2)))
        #    i.e. (ζ₈ − ζ₈³)/2 = √2/2, over Φ₈ = x⁴ + 1
        cos_2pi_over_n(3).as_rational()
        # -> Q(-1, 2)
        cos_2pi_over_n(5).is_rational()
        # -> False

    **The rationality verdict is decidable, and it is Niven's theorem.**
    ``cos_2pi_over_n(n).is_rational()`` is ``True`` for exactly
    ``n ∈ {1, 2, 3, 4, 6}`` — measured over ``n = 1..24``, not asserted — which
    is precisely the classical statement that the only rational cosines of
    rational multiples of ``2π`` are ``0, ±1/2, ±1``. A float cosine plus a
    tolerance cannot return that verdict; this element can.

    See also:
        :func:`sin_2pi_over_n` — the sine peer. Read its field note first: it
        does NOT return over ``Φ_n`` unless ``4 | n``.

    Note:
        Exact ``Q`` throughout; no ``abs``; no ``math``; no float.
    """
    _validated_index(n, "cos_2pi_over_n")
    zeta = Qalg.alpha(_cyclotomic_m(n))
    # Class C: the +turn and the −turn of the same rotation. ζ⁻¹ = ζ^(n−1)
    # because ζⁿ = 1; at n = 1 that is ζ⁰ = 1, which is also ζ itself.
    return (zeta + zeta ** (n - 1)) * Q(1, 2)


def sin_2pi_over_n(n: int) -> "Qalg":
    """``sin(2π/n)`` as an EXACT :class:`Qalg` element of ℚ(ζ_N), **where
    N = lcm(n, 4)** — the returned value is the sine ITSELF, not ``i·sin``.

    ⚠️ **Read the field.** The sine of ``2π/n`` is generally NOT an element of
    ℚ(ζ_n). ``sin(2π/n) = (ζ − ζ⁻¹)/(2i)``, and ``i ∈ ℚ(ζ_n)`` only when
    ``4 | n``; when it is absent, ``(ζ − ζ⁻¹)/2`` lies in ℚ(ζ_n) but the sine
    does not (if ``x`` and ``x/i`` were both in a field ``K`` then ``i`` would
    be too). So this op works over ``N = lcm(n, 4)``, the cyclotomic index that
    carries ``ζ_n`` AND ``i = ζ_4`` at once. With ``ω = ζ_N``::

        ζ_n = ω^(N/n),   i = ω^(N/4),   sin(2π/n) = (ω^(N/n) − ω^(−N/n)) / (2i)

    Every factor is inside ℚ(ζ_N), so the ``1/i`` is DIVIDED OUT rather than
    carried, and what comes back is the real number ``sin(2π/n)``: its minimal
    polynomial is ``Φ_N``, its ``.coords`` are ``φ(N)`` exact ``Q``. The
    alternative — returning ``(ζ − ζ⁻¹)/2 = i·sin(2π/n)`` over ``Φ_n``, which
    is cheaper for ``4 ∤ n`` — was measured and REJECTED: a function named
    ``sin`` must not answer ``i·sin``, and the saving is at most one factor of
    two in the field degree (``φ(lcm(n, 4)) = 2·φ(n)`` when ``4 ∤ n``, and
    ``= φ(n)`` when ``4 | n``).

    **This op never refuses on constructibility.** ``sin(2π/n)`` is an
    algebraic number in a cyclotomic field for EVERY ``n >= 1``, so there is no
    "n that admits it" and no n that does not. The only refusals are the shared
    index guard's: type, ``n < 1``, and the degree cap.

    **Composing with the cosine.** :func:`cos_2pi_over_n` returns over ``Φ_n``.
    The two fields COINCIDE exactly when ``4 | n``, and there
    ``cos_2pi_over_n(n)**2 + sin_2pi_over_n(n)**2 == 1`` composes directly.
    When ``4 ∤ n`` they are different fields and ``Qalg``'s ``_same_field``
    guard will (correctly) raise on a mixed binary op — lift the cosine into
    ℚ(ζ_N) yourself as ``(ω^(N/n) + ω^(−N/n))/2`` first. Measured: the
    Pythagorean identity then holds exactly for every ``n`` tested.

    **Cascade composition.** Class J (the divisor lattice building ``Φ_N``, and
    the ``lcm`` that chooses ``N``) ∘ Class N (the exact rational coordinates)
    ∘ Class C (the ζ rotation — the sine is the ANTI-symmetric part of the two
    chiralities, which is why the ``1/i`` appears at all). No ``abs``.

    Args:
        n: the cyclotomic index, ``1 <= n <= MAX_CYCLOTOMIC_INDEX`` (256).
            ``TypeError`` for a non-``int`` (``bool`` included);
            ``ValueError`` outside the range.

    Returns:
        ``Qalg`` over ``m = Φ_{lcm(n, 4)}``, with ``root=None`` (see
        :func:`cos_2pi_over_n` on why no embedding is attached).

    Worked anchors::

        sin_2pi_over_n(8)
        # -> Qalg((1, 0, 0, 0, 1), (Q(0, 1), Q(1, 2), Q(0, 1), Q(-1, 2)))
        #    lcm(8, 4) = 8, so this shares Φ₈ with the cosine — and at n = 8
        #    the two values coincide: sin(π/4) = cos(π/4) = √2/2.
        sin_2pi_over_n(12).as_rational()
        # -> Q(1, 2)     sin(π/6) = 1/2, over Φ₁₂
        sin_2pi_over_n(5).degree
        # -> 8           lcm(5, 4) = 20, φ(20) = 8

    **The rationality verdict, measured over ``n = 1..24``:**
    ``sin_2pi_over_n(n).is_rational()`` is ``True`` for exactly
    ``n ∈ {1, 2, 4, 12}`` — the sine values ``0, 0, 1, 1/2``. Note this is a
    DIFFERENT set from the cosine's ``{1, 2, 3, 4, 6}``; ``n = 12`` is rational
    for the sine and irrational for the cosine (``√3/2``), and ``n = 3`` and
    ``n = 6`` are the other way round.

    Note:
        Exact ``Q`` throughout; no ``abs``; no ``math``; no float.
    """
    _validated_index(n, "sin_2pi_over_n")
    # Class J: N = lcm(n, 4), the smallest index whose field carries BOTH the
    # n-th root of unity and i. gcd is the shipped Class-I op.
    index = 4 * n // _gcd(n, 4)
    omega = Qalg.alpha(_cyclotomic_m(index))
    zeta = omega ** (index // n)                    # ζ_n  (exponent ∈ {1,2,4})
    imag_unit = omega ** (index // 4)               # i = ζ_4
    # Class C: (ζ − ζ⁻¹) is the anti-symmetric part of the two chiralities;
    # dividing by i turns that imaginary quantity into the real sine, inside
    # the field. inverse() IS ζ^(N−k) here — the cheaper spelling of the same
    # element (verified equal for every n tested).
    return (zeta - zeta.inverse()) * imag_unit.inverse() * Q(1, 2)
