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

**Cyclotomic trigonometry (v0.9.0rc463, `#T1188`; ONE constructor since
rc468).** The module also ships :func:`cos_sin_2pi_k_over_n`, which returns
``(cos(2πk/n), sin(2πk/n))`` as an EXACT pair over one cyclotomic minimal
polynomial ``Φ`` — no float, no series truncation, no ``math`` module. It is
the bottom-up carrier-native answer to the ``math.cos(2*pi/n)`` shortcut: the
value is not approximated and then rationalised, it is CONSTRUCTED in the field
where it already lives.

rc463 shipped this surface as TWO ops, ``cos_2pi_over_n`` over ``Φ_n`` and
``sin_2pi_over_n`` over ``Φ_lcm(n,4)``, and rc468 added the general-turn
constructor beside them. **rc468 then REMOVED both** (`#T1188`): with ``k``
defaulting to 1 the general op IS the two, so keeping them was a duplicate op,
not a convenience. They were also the WORSE spelling of the same values — they
answered in two DIFFERENT fields whenever ``4 ∤ n``, so ``Qalg``'s
``_same_field`` guard correctly refused to add a cosine to its own sine.
There is no alias and no deprecation shim: ``cos_2pi_over_n(n)`` is
``cos_sin_2pi_k_over_n(n)[0]`` and ``sin_2pi_over_n(n)`` is
``cos_sin_2pi_k_over_n(n)[1]``, both now over the ONE field ``Φ_lcm(n,4)``.
"""

from __future__ import annotations

from .cyclic import gcd as _gcd
from .poly import cyclotomic_polynomial
from .primes import factor as _factor
from .q import Q

__all__ = [
    "MAX_CYCLOTOMIC_DEGREE",
    "Qalg",
    "cos_sin_2pi_k_over_n",
]

#: The measured field-**DEGREE** cap of :func:`cos_sin_2pi_k_over_n` and of the
#: exact twiddle routes built on it — an upper bound on
#: ``φ(M) = deg Φ_M``, never on the index ``M`` itself.
#:
#: **Why the DEGREE and not the index (0.9.0rc478, `#T1188`).** Everything the
#: cap exists to bound is a function of ``d = φ(M)`` and NONE of it is a
#: function of ``M``: the coordinate-vector length is ``d``, an exact ``Q``
#: multiply in the field is ``O(d²)`` rational operations, and the answer's
#: resident size is ``d``-linear (MEASURED at ``0.000793–0.000808`` MiB per
#: degree on the ``1/√7`` axis at two degrees). Bounding ``M`` therefore
#: refused and admitted the wrong objects in BOTH directions, measured on this
#: tree at the rc477 constant ``MAX_CYCLOTOMIC_INDEX = 256``:
#: ``cos_sin_2pi_k_over_n(251)`` was ADMITTED into ``Φ_1004`` at degree
#: **500**, while ``n = 23`` on the ``1/√3`` axis (``Φ_276``, degree **88** —
#: five times smaller, and measured faster) was REFUSED. :func:`_cyclotomic_degree`
#: is the quantity this constant bounds, and the guard computes it from the
#: factorisation without ever building ``Φ_M``.
#:
#: **Why 888 — derived, not preferred.** ``888 = φ(2676) = φ(lcm(669, 4)) =
#: φ(lcm(669, 12))`` is exactly the degree of the **Exeligmos** field (the
#: 669-year Antikythera back-panel period), which is also the **Saros** field
#: on the quaternion body diagonal. It is the SMALLEST bound that admits it:
#: at ``φ ≤ 864`` Exeligmos still refuses on every axis. Rounding up to 1024
#: covers nothing further that is asked for and makes the dearest admitted
#: call **3.30× dearer** — MEASURED, interleaved and non-overlapping: the
#: worst admitted ``axis_k = 7`` row goes from 44.7 s at ``φ ≤ 888`` to
#: 147.4 s at ``φ ≤ 1024``.
#:
#: **What it admits.** All four canonical Antikythera dial periods — Saros
#: 223, Metonic 235, Callippic 940 and Exeligmos 669 — on BOTH cheap axes
#: (``axis_k`` 1 and 3), and 128 of 128 ``n ≤ 128`` on those two axes (114 of
#: 128 on ``axis_k = 7``). Against the rc477 predicate the change is a STRICT
#: widening: **0 of 12288** ``(n ≤ 4096) × (axis_k ∈ {1,3,7})`` rows lost,
#: 2118 gained.
#:
#: **What it still refuses, named.** Exeligmos on the equal-weight octonion
#: axis: ``octonion_twiddle(1, 1, 669, mu="diagonal", exact=True)`` builds
#: ``Φ_18732`` at degree **5328** — six times the degree, because that index
#: carries a factor 7 the cheap axes do not — and the refusal says so. A named
#: refusal with its degree in it, never a silent demotion to the float route.
#:
#: **φ bounds the OBJECT and NOT the clock.** At one IDENTICAL degree the
#: admitted cost still spans **98×** (MEASURED, ``axis_k = 7``, ``φ = 768``
#: both: ``n = 256`` at 7 terms → 0.36 s against ``n = 85`` at 253 terms →
#: 35.7 s), because the sparsity of ``Φ_M`` is not a function of its degree. A
#: SECOND admission criterion was measured and REJECTED for exactly that
#: reason — a per-axis degree bound would have to refuse that 0.36 s answer in
#: order to block the 35.7 s one.
#:
#: **The sibling constant is a DIFFERENT quantity and does not move.**
#: ``srmech.math.laplacian.MAX_CYCLIC_SPECTRUM_N = 256`` bounds ``n`` for
#: ``cyclic_laplacian_spectrum``, whose field is ``Φ_n`` at degree ``φ(n)``;
#: this one bounds ``φ(lcm(n, base))`` for ``base ∈ {4, 12, 28}``. Through
#: rc477 this block claimed the two "match at the same 256 for the same
#: reason" — they never bounded the same quantity, and the raise makes the
#: sentence false as well as imprecise, so it is RETRACTED here rather than
#: renumbered.
MAX_CYCLOTOMIC_DEGREE = 888

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

    # ── ORDER, exactly where one EXISTS (rc479, `#T1188`) ──────────────────
    #
    # ⚠️ THIS IS NOT A TOTAL ORDER, AND IT MUST NOT BECOME ONE. A general
    # element of ℚ(α) is COMPLEX — every cyclotomic field above ℚ(ζ₄) has
    # non-real elements — and "<" is not merely hard for a complex number, it
    # is UNDEFINED. So the order is implemented exactly where it exists (the
    # element lies in the prime field ℚ, where it IS a real rational and its
    # order is that rational's) and REFUSES otherwise, naming why.
    #
    # WHY IT IS NEEDED AT ALL. Through rc478 a `Qalg` never reached a public
    # wrapper's OUTPUT: the DFT transforms cast to float at their own entry.
    # rc479's M2/M3 removed that cast, so an EXACT sample now returns `Qalg`
    # leaves — and `quaternion_dft`'s own SHIPPED worked example, which a user
    # copies, computes a round-trip residue and asks `d >= 0` for the Class-K
    # sign branch. Measured on that snippet: all 32 residues are RATIONAL and
    # exactly ZERO, so the rational arm closes it completely and exactly,
    # with no projection and no tolerance anywhere. It is the `Q` carrier's
    # rc479 non-finite repair one rung up: the gap is at the CARRIER, so the
    # repair is too.
    #
    # `float(Qalg)` is deliberately NOT the fallback. `to_float` needs an
    # attached embedding root and raises without one, and using it would make
    # a comparison depend on a rounding — which is the defect this whole
    # release removes.

    def _order_pair(self, other):
        """``(self_q, other_q)`` as exact ``Q``s when BOTH sides are rational,
        else ``None``. No field is constructed and nothing is projected."""
        if not self.is_rational():
            return None
        if isinstance(other, Qalg):
            if not other.is_rational():
                return None
            return (self._coords[0], other._coords[0])
        q = _to_q(other)
        if q is None:
            return None
        return (self._coords[0], q)

    def _order_refusal(self, other, op):
        return TypeError(
            f"'{op}' is undefined between {type(self).__name__} and "
            f"{type(other).__name__} unless BOTH lie in the prime field ℚ. A "
            f"general element of ℚ(alpha) is COMPLEX, and a complex number "
            f"has no order — this refuses rather than inventing one from a "
            f"float embedding. Use .is_rational() / .as_rational() to take "
            f"the exact rational when there is one, or compare a derived "
            f"real quantity instead.")

    def __lt__(self, other) -> bool:
        pair = self._order_pair(other)
        if pair is None:
            raise self._order_refusal(other, "<")
        return pair[0] < pair[1]

    def __le__(self, other) -> bool:
        pair = self._order_pair(other)
        if pair is None:
            raise self._order_refusal(other, "<=")
        return pair[0] <= pair[1]

    def __gt__(self, other) -> bool:
        pair = self._order_pair(other)
        if pair is None:
            raise self._order_refusal(other, ">")
        return pair[0] > pair[1]

    def __ge__(self, other) -> bool:
        pair = self._order_pair(other)
        if pair is None:
            raise self._order_refusal(other, ">=")
        return pair[0] >= pair[1]

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
def _cyclotomic_degree(index: int) -> int:
    """``deg Φ_index = φ(index)`` — the DEGREE of the cyclotomic field
    ``ℚ(ζ_index)``, and the quantity :data:`MAX_CYCLOTOMIC_DEGREE` bounds.

    Computed from the factorisation alone,
    ``φ(∏ pᵢ^eᵢ) = ∏ pᵢ^(eᵢ−1)·(pᵢ − 1)``, so it costs one
    :func:`srmech.math.primes.factor` call and **never builds** ``Φ_index``.
    That is the whole point of it: an admission guard has to answer *"how big
    is the object this call would construct?"* BEFORE paying for it, and
    :func:`~srmech.math.poly.cyclotomic_polynomial` at index 18732 is
    precisely the cost the guard exists to refuse. MEASURED at rc478: 2.1 µs
    per call at index 18732, against a polynomial build of that degree.

    **NOT a registered op, and PRIVATE, deliberately** — the same ruling
    :func:`_inv_sqrt_k` records for itself, on the same two grounds. It is
    sugar over :func:`srmech.math.primes.factor` and one multiplicative loop;
    and the number it returns is ALREADY published on the registered surface,
    as :func:`~srmech.math.poly.cyclotomic_polynomial`'s ``"degree"`` key. A
    public ``cyclotomic_degree`` would therefore be a second op for a
    quantity that already ships, which is the duplicate shape this tree
    removes rather than adds. What rc478 (`#T1188`) needed was not a new
    published quantity but a CHEAP ROUTE to an existing one, for a guard that
    must not pay for the polynomial — so it lands beside
    :func:`_cyclotomic_m` and :func:`_turn_field_index` as module-private
    arithmetic. (The registry-completeness ratchet,
    ``tests/test_registry_completeness_rc416.py``, is what makes that a
    decision rather than an omission: a public ``__all__`` callable with no
    ``ToolEntry`` goes red, so the surface cannot trickle.)

    ``_cyclotomic_degree(1) == 1`` (``Φ_1 = x − 1``). MEASURED agreement with
    ``len(cyclotomic_polynomial(M)) - 1`` over ``M = 1..1200``: 1200 of 1200,
    0 disagreements; the same comparison against a shifted index disagrees at
    193 of 198, so the instrument can return otherwise.

    Class J (the prime factorisation) ∘ Class I (the multiplicative product).
    No float, no series, no ``abs``.

    Args:
        index: the cyclotomic index ``M >= 1``.

    Returns:
        ``φ(M)`` as an ``int`` — the ℚ-dimension of ``ℚ(ζ_M)``.

    Raises:
        TypeError: if ``index`` is not a plain ``int`` (``bool`` included —
            ``True`` is not the index 1).
        ValueError: if ``index < 1``.
    """
    if isinstance(index, bool) or not isinstance(index, int):
        raise TypeError(
            "_cyclotomic_degree: index must be a plain int (the cyclotomic "
            f"index); got {type(index).__name__}")
    if index < 1:
        raise ValueError(f"_cyclotomic_degree requires index >= 1; got {index}")
    degree = 1
    for prime, power in _factor(index):
        degree *= (prime - 1) * prime ** (power - 1)
    return degree


#: The index above which a field is CERTAINLY over the degree cap, so the
#: guard can refuse it without factoring. ``φ(M) ≥ √(M/2)`` for every
#: ``M ≥ 1``, so ``φ(M) ≤ P`` forces ``M ≤ 2P²``.
#:
#: **Why this exists (0.9.0rc478, `#T1188`) — it repairs a regression this
#: same rc introduced.** Moving the criterion from the index to the degree
#: means the guard must SIZE the field before refusing it, and sizing means
#: factoring. ``srmech.math.primes.factor`` is trial division, so the refusal
#: cost grew as ``√n``: MEASURED on this tree, `cos_sin_2pi_k_over_n` refused
#: ``n = 10¹¹`` in 55 ms, ``n = 10¹⁵`` in 2.36 s and ``n = 2⁶² − 57`` in
#: **211.8 s** — where rc477's index comparison refused all three in
#: microseconds. Nothing is wrong with the ANSWER; what regressed is how long
#: a refusal takes, and a three-minute refusal on a public op is a defect
#: whether or not anyone passes that ``n``. The two twiddle routes were far
#: less exposed and the reason is worth recording rather than glossing: their
#: own ``_TWIDDLE_N_MAX = 2**32`` refuses first, capping their worst
#: factorisation at ``√(28·2³²)`` and their worst refusal at tens of ms. The
#: routes that could actually reach the pathological case were
#: :func:`cos_sin_2pi_k_over_n` and ``hypercomplex_exp``'s ``turn=``, neither
#: of which bounds ``n`` at all.
#:
#: Refusing above ``2P²`` restores a constant-time refusal for every large
#: ``n`` and **cannot change a verdict**: no admissible index reaches it. That
#: is checked two ways rather than asserted — the inequality is verified
#: directly over the whole range, and ``max{M : φ(M) ≤ P}`` is measured to be
#: **3990**, which is 395× below this bound.
_DEGREE_CERTAIN_INDEX_MAX = 2 * MAX_CYCLOTOMIC_DEGREE * MAX_CYCLOTOMIC_DEGREE


def _field_too_big(index: int):
    """``None`` when ``Φ_index`` is inside :data:`MAX_CYCLOTOMIC_DEGREE`, else
    the phrase naming what exceeded it — the SHARED refusal vocabulary of all
    six admission guards, so they cannot drift apart.

    Two shapes, and the difference is honest rather than cosmetic. Below
    :data:`_DEGREE_CERTAIN_INDEX_MAX` the degree is COMPUTED and named
    exactly. Above it the degree is not computed at all — factoring is what
    costs — so the phrase says the degree is over the cap and names the
    certificate instead of inventing a number.

    Class J (the factorisation, when it is worth doing at all)."""
    if index > _DEGREE_CERTAIN_INDEX_MAX:
        return (f"of a degree above the measured "
                f"MAX_CYCLOTOMIC_DEGREE={MAX_CYCLOTOMIC_DEGREE} field cap "
                f"(certified without factoring: phi(M) >= sqrt(M/2), so an "
                f"admitted index cannot exceed "
                f"{_DEGREE_CERTAIN_INDEX_MAX}, and the largest one that "
                f"actually is admitted is 3990)")
    degree = _cyclotomic_degree(index)
    if degree > MAX_CYCLOTOMIC_DEGREE:
        return (f"of degree {degree}, above the measured "
                f"MAX_CYCLOTOMIC_DEGREE={MAX_CYCLOTOMIC_DEGREE} field cap")
    return None


def _validated_index(n, where: str) -> int:
    """The shared Class-J DEGREE guard for the cyclotomic trig constructors.

    ``n`` must be a plain ``int`` (``bool`` is refused — ``True`` is not the
    index 1) and at least 1, and the field the caller then builds —
    ``Φ_lcm(n, 4)``, the one field :func:`cos_sin_2pi_k_over_n` answers over —
    must have degree at most :data:`MAX_CYCLOTOMIC_DEGREE`.

    **The bound is on the DEGREE, not on ``n`` (0.9.0rc478, `#T1188`).**
    Through rc477 this guard read ``n > MAX_CYCLOTOMIC_INDEX``, which is a
    bound on a quantity no cost depends on; ``n`` itself is now unbounded
    above and what refuses is the SIZE of the object. The refusal names the
    index it would have built and its degree, so a caller can see what bound.

    Returns ``n`` so the caller can use the guard inline."""
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError(
            f"{where}: n must be a plain int (the cyclotomic index); "
            f"got {type(n).__name__}")
    if n < 1:
        raise ValueError(f"{where} requires n >= 1; got {n}")
    index = 4 * n // _gcd(n, 4)
    too_big = _field_too_big(index)
    if too_big is not None:
        raise ValueError(
            f"{where}: n={n} builds Q(zeta_{index}) {too_big}")
    return n


#: The ``Φ`` memo — a plain dict rather than ``functools.lru_cache``, and the
#: difference is load-bearing rather than stylistic. The decorator replaces the
#: function object with a wrapper, and ``tests/composes_derive.py`` resolves a
#: declared ``composes`` edge by walking the AST of the CALLER and then
#: descending into the callee it resolves; a wrapper is not the ``FunctionDef``
#: it looks for, so decorating this function silently broke the shipped
#: ``composes=("...cyclotomic_polynomial",)`` declaration of the op that
#: reaches ``cyclotomic_polynomial`` through it. MEASURED at rc468
#: (`#T1188`): the decorated form failed
#: ``test_every_declared_sub_op_is_actually_called``. Same memo, same cost,
#: visible call.
_PHI_CACHE: dict = {}


def _cyclotomic_m(index: int):
    """The monic ℤ[x] minimal polynomial ``Φ_index`` as the ASCENDING int tuple
    ``Qalg`` wants for its ``m`` — Class J, the divisor-lattice construction in
    :func:`srmech.math.poly.cyclotomic_polynomial`.

    MEMOISED since rc468 (`#T1188`): the exact twiddle routes
    (:func:`cos_sin_2pi_k_over_n` and its callers in
    ``srmech.physics.qm.quaternion`` / ``.octonion`` /
    ``srmech.cascade.hypercomplex_dft``) rebuild the SAME ``Φ_M`` once per
    turn across a whole transform, and the modulus is an immutable int tuple
    with no other state. Measured on this tree: a 64-turn sweep at ``n = 64``
    halves, 0.025 s → 0.013 s. The cache is keyed by index alone; the returned
    tuple is immutable, so no caller can perturb another's copy."""
    hit = _PHI_CACHE.get(index)
    if hit is not None:
        return hit
    m = tuple(cyclotomic_polynomial(index)["coefficients"])
    _PHI_CACHE[index] = m
    return m


# ── the general rational turn (rc468, `#T1188`) ──────────────────────────────
#: The cyclotomic index whose field carries ``1/√k`` for each equal-weight
#: hypercomplex axis width ``k``. ``k = 1`` is a single basis axis (already
#: rational, so the field needs only ``i``); ``k = 3`` is the quaternion body
#: diagonal ``(i+j+k)/√3`` and ``√3 = ζ₁₂ + ζ₁₂⁻¹``; ``k = 7`` is the
#: equal-weight octonion axis and ``√7 = g/i`` with ``g`` the quadratic Gauss
#: sum ``Σ_{a=1..6} (a|7)·ζ₇^a`` (``g² = −7``, so ``√7`` needs ``ζ₇`` AND ``i``
#: — index ``lcm(7, 4) = 28``). Both are MEASURED exactly, not asserted:
#: ``r*r == k`` and ``r * r.inverse() == 1`` hold in the field.
_AXIS_SCALE_INDEX = {1: 4, 3: 12, 7: 28}

#: The quadratic residues mod 7 — the Legendre-symbol ``(a|7) = +1`` set, the
#: only table the ``√7`` Gauss sum needs (Class J).
_QR7 = frozenset((1, 2, 4))


def _isqrt_floor(x: int) -> int:
    """``floor(√x)`` for a non-negative ``int``. Newton on ints — no
    ``math.isqrt`` (``math`` is a BANNED_ENGINE in this tree), no float, no
    ``abs``. The ONE integer-root kernel this module has; :func:`_isqrt` is its
    perfect-square projection and :func:`_axis_q61` its rounding one, so the
    Newton loop is written once (rc477, `#T1188`)."""
    if x < 2:
        return x
    r = 1 << ((x.bit_length() + 1) // 2)             # a bound above the root
    while True:
        nxt = (r + x // r) // 2
        if nxt >= r:
            break
        r = nxt
    return r


def _isqrt(x: int):
    """The exact integer square root of a non-negative ``int``, or ``None`` if
    ``x`` is not a perfect square. Newton on ints — no ``math.isqrt`` (``math``
    is a BANNED_ENGINE in this tree), no float, no ``abs``."""
    if x < 0:
        return None
    r = _isqrt_floor(x)
    return r if r * r == x else None


def _rational_sqrt_exact(q: "Q"):
    """The exact rational ``√q`` when ``q`` is a square of a rational, else
    ``None`` — Class J on the numerator and denominator separately (a reduced
    ``p/d`` is a rational square iff BOTH ``p`` and ``d`` are integer
    squares)."""
    num, den = q.numerator, q.denominator
    if num < 0:
        return None
    rn = _isqrt(num)
    rd = _isqrt(den)
    if rn is None or rd is None:
        return None
    return Q(rn, rd)


def _exact_axis(weights):
    """``(unit_weights, axis_k)`` — the EXACTLY-normalisable reading of a
    rational pure-imaginary direction, or ``None`` when the shipped cyclotomic
    fields cannot hold its normaliser.

    ``weights`` is a list of exact :class:`~srmech.math.q.Q` with
    ``weights[0] == 0``. Writing ``‖w‖² = k·t²`` with ``k ∈ {1, 3, 7}`` and
    ``t`` rational, the unit direction is ``w/t`` scaled by ``1/√k`` — so the
    rational part of the normaliser is folded into the returned weights and
    only the irrational part ``1/√k`` is left for :func:`_inv_sqrt_k`. That
    covers every basis axis (``k = 1``), the quaternion body diagonal
    ``(0,1,1,1)`` (``‖w‖² = 3``) and the equal-weight octonion axis
    ``(0,1,…,1)`` (``‖w‖² = 7``) — and it REFUSES, rather than rounding, a
    direction like ``(0,1,2,0)`` whose ``‖w‖² = 5`` needs ``√5`` and hence a
    field this rc does not build. Class J ∘ N; no float, no ``abs``."""
    zero = Q(0, 1)
    if not weights or weights[0] != zero:
        return None
    nsq = zero
    for w in weights[1:]:
        nsq = nsq + w * w
    if nsq == zero:
        return None
    for k in (1, 3, 7):
        t = _rational_sqrt_exact(nsq / Q(k, 1))
        if t is None:
            continue
        inv_t = Q(t.denominator, t.numerator)
        return [w * inv_t for w in weights], k
    return None


#: The Q61 fixed-point one, as the exponent the axis words are taken at. Kept
#: here as a bit count rather than imported so this module stays free of
#: :mod:`srmech.cascade`.
_Q61_BITS = 61


def _integer_direction(weights):
    """``(w, S)`` — an exact rational direction read as an INTEGER direction
    ``w`` and its squared length ``S = Σ wᵢ²`` (rc477, `#T1188`).

    ``weights`` is a sequence of exact :class:`~srmech.math.q.Q`. Every
    component is put over the common denominator ``lcm(dᵢ)`` (Class I
    :func:`~srmech.math.cyclic.gcd`), which **cancels out of** ``wᵢ/√S`` — so
    the pair is the direction alone, carrying no scale to round.

    This is the reader the three float axis resolvers share. Before rc477 each
    of them normalised in float — ``1.0 / float(sqrt(‖v‖²))`` then a multiply,
    three roundings — and landed **179 Q61 words** above the nearest word on
    the body diagonal and **68 below** on the octonion diagonal (measured; the
    norm residue is ``+619.62`` and ``−361.50`` grid units). Reading the
    direction as integers is what makes :func:`_axis_q61` and
    :func:`_axis_float` decidable at all.

    No ``abs()``: ``S`` is built from ``wᵢ * wᵢ``, which is sign-free by
    construction rather than by a magnitude call."""
    den = 1
    pairs = []
    for c in weights:
        q = _to_q(c)
        n, d = q.numerator, q.denominator
        pairs.append((n, d))
        den = den // _gcd(den, d) * d                      # lcm (Class I)
    w = [n * (den // d) for n, d in pairs]
    return w, sum(x * x for x in w)


def _axis_q61(w, S):
    """The NEAREST Q61 word of ``sign(wᵢ)·√(wᵢ²/S)``, per component — decided
    entirely in integers (rc477, `#T1188`).

    ``uᵢ`` is the integer nearest ``2⁶¹·√(wᵢ²/S)``, which is certified by

    ::

        (2uᵢ − 1)²·S  <  wᵢ²·2¹²⁴  <  (2uᵢ + 1)²·S

    — the inequality ``tests/test_axis_words_are_nearest_rc477.py`` asserts,
    with a can-fail control that must reject both neighbours. The sign is a
    Class-K pin-slot read off ``wᵢ`` and re-applied as Class C; the magnitude
    runs on ``wᵢ * wᵢ``. **Never ``abs()``.**

    For ``w = (0,1,1,1)``, ``S = 3`` this returns exactly the in-file
    ``_HC_INV_Q61[3]`` the coupler's exact Q61 arm has always used, and
    likewise at ``S = 7`` — the shipped anchor is ABSORBED here rather than
    duplicated, and a general direction gets the same treatment for free."""
    if S <= 0:
        raise ValueError("_axis_q61: S must be positive (a non-zero direction)")
    out = []
    for wi in w:
        sign = 1 if wi > 0 else (-1 if wi < 0 else 0)       # Class K pin-slot
        if sign == 0:
            out.append(0)
            continue
        a = (wi * wi) << (2 * _Q61_BITS)
        f = _isqrt_floor(a // S)
        u = f + 1 if (2 * f + 1) ** 2 * S < (a << 2) else f   # round-half-up
        out.append(sign * u)                                  # Class C reorient
    return out


def _axis_float(w, S):
    """The CORRECTLY ROUNDED double of ``sign(wᵢ)·√(wᵢ²/S)``, per component
    (rc477, `#T1188`).

    The root is taken on the exact rational ``Q(wᵢ², S)`` by the Class-N
    :func:`srmech.math.rational.sqrt` cascade and projected ONCE. The shipped
    spelling it replaces — ``1.0 / float(sqrt(‖v‖²))`` then a multiply — misses
    the correctly rounded double on **101 of the 399** integers ``k`` in
    ``2..400`` where this one misses **0**; ``1/√3`` was served
    ``0.5773502691896258`` for a correctly rounded ``0.5773502691896257``.

    An exactly-representable unit survives as itself: ``(0,3,4,0)`` returns
    ``0.6`` and ``0.8``, where the float detour served ``0.6000000000000001``.

    Class K pin-slot on the sign, Class C to re-apply it. **Never ``abs()``.**"""
    from . import rational as _rational                  # Class N (cycle-free)
    if S <= 0:
        raise ValueError("_axis_float: S must be positive (a non-zero direction)")
    out = []
    for wi in w:
        sign = 1 if wi > 0 else (-1 if wi < 0 else 0)       # Class K pin-slot
        if sign == 0:
            out.append(0.0)
            continue
        mag = float(_rational.sqrt(Q(wi * wi, S)))
        out.append(mag if sign > 0 else -mag)               # Class C reorient
    return out


def _turn_field_index(n: int, axis_k: int = 1) -> int:
    """The cyclotomic index ``M`` of the field carrying ``ζ_n``, ``i`` AND the
    axis scale ``1/√axis_k`` at once — ``lcm(n, 4)`` for a rational axis,
    ``lcm(n, 12)`` for the ``1/√3`` body diagonal, ``lcm(n, 28)`` for the
    ``1/√7`` equal-weight octonion axis. Class J (two ``lcm``s over the shipped
    Class-I :func:`~srmech.math.cyclic.gcd`)."""
    base = _AXIS_SCALE_INDEX[axis_k]
    m = 4 * n // _gcd(n, 4)
    return m * base // _gcd(m, base)


def _cos_sin_in_field(index: int, n: int, k: int):
    """``(cos(2πk/n), sin(2πk/n))`` as a pair of exact :class:`Qalg` over
    ``Φ_index`` — the shared worker of :func:`cos_sin_2pi_k_over_n` and of the
    exact twiddle routes, which need the SAME two values in a LARGER field
    than ``lcm(n, 4)`` whenever the axis carries an irrational scale.

    Requires ``n | index`` and ``4 | index`` (:func:`_turn_field_index`
    guarantees both). With ``ω = ζ_index``, ``ζ = ω^(index·k/n)`` and
    ``i = ω^(index/4)``::

        cos = (ζ + ζ⁻¹)/2        sin = (ζ − ζ⁻¹)/(2i)

    — the two classical constructions, both lifted into the one common field
    so they COMPOSE. Through rc467 they were two separate ops, each answering
    over its own field; rc468 removed that split rather than documenting it.
    No float, no ``abs``."""
    omega = Qalg.alpha(_cyclotomic_m(index))
    zeta = omega ** (((index // n) * (k % n)) % index)
    zeta_inv = zeta.inverse()
    half = Q(1, 2)
    cos = (zeta + zeta_inv) * half
    sin = (zeta - zeta_inv) * (omega ** (index // 4)).inverse() * half
    return cos, sin


#: The ``1/√k`` memo — keyed ``(k, index)``, and a plain dict for the SAME
#: load-bearing reason :data:`_PHI_CACHE` is one: ``functools.lru_cache``
#: replaces the function object with a wrapper, and ``tests/composes_derive.py``
#: resolves a declared ``composes`` edge by walking the AST of the caller and
#: descending into the callee it resolves — a wrapper is not the ``FunctionDef``
#: it looks for. ``hypercomplex_dft._exact_turn_pair``'s ``lru_cache`` is the
#: shape that must not be copied here.
#:
#: ``Qalg`` is immutable (``__slots__``, a tuple of ``Q`` coordinates), so the
#: memo hands back the SAME object rather than a copy, and the memoised and
#: unmemoised values are equal under both ``==`` and ``is``.
#:
#: **Why it ships in the same commit as the degree cap (0.9.0rc478, `#T1188`).**
#: ``_inv_sqrt_k`` is a pure function of two ints that the turn loop
#: recomputes on EVERY turn, and MEASURED on this tree it is where the cost of
#: a raised cap actually lives: 0.0 % of the whole twiddle at ``axis_k = 1``
#: (it is not called at all — see :func:`_turn_scalars`), 56.7 % at the
#: Exeligmos ``axis_k = 3`` row and **69.9 %** at the dearest admitted row.
#: Per turn after the first that is a saving of **0 % (the k=1 control) /
#: 53.5 % (Exeligmos on the body diagonal) / 80.2 % (the dearest admitted
#: row)**. Residency is bounded and small: at ``φ ≤ 888`` the worst case is
#: **345 keys** (249 with ``12 | M``, 96 with ``28 | M``) at a measured
#: 52.6–64.5 bytes per degree, so no eviction policy is needed.
_INV_SQRT_K_CACHE: dict = {}


def _inv_sqrt_k(k: int, index: int) -> "Qalg":
    """``1/√k`` for ``k ∈ {1, 3, 7}`` as an exact :class:`Qalg` over
    ``Φ_index`` — the equal-weight hypercomplex axis normaliser, EXACT where
    the shipped float axes carry ``1.0 / float(rational.sqrt(k))``.

    ``k = 1`` is the field one. ``k = 3`` uses ``√3 = ζ₁₂ + ζ₁₂⁻¹`` (twice the
    cosine of a twelfth turn). ``k = 7`` uses the quadratic Gauss sum
    ``g = Σ_{a=1..6} (a|7)·ζ₇^a``, for which ``g² = −7`` (because ``7 ≡ 3 mod
    4``), so ``√7 = g/i``. Both need ``index`` divisible by the matching entry
    of :data:`_AXIS_SCALE_INDEX`.

    NOT a registered op, deliberately: it is sugar over :meth:`Qalg.alpha` and
    ``**``, it is meaningful only for the three axis widths ``{1, 3, 7}`` the
    Hurwitz ladder supplies, and a general ``sqrt_in_cyclotomic`` would have to
    answer for every ``k`` — a different, larger op. The exactness it delivers
    IS reachable through the ops that do ship
    (``quaternion_twiddle(..., exact=True)``,
    ``octonion_twiddle(..., exact=True)``,
    ``hypercomplex_exp(k_axes=..., turn=(k, n))``).

    MEMOISED on ``(k, index)`` through :data:`_INV_SQRT_K_CACHE` since
    0.9.0rc478 (`#T1188`) — a pure function of two ints that the turn loop
    would otherwise rebuild on every turn, and MEASURED as 56.7–77.8 % of the
    whole exact twiddle on the two scaled axes. The memo cannot shorten the
    FIRST call, because the first call is the one that builds it.

    Class J ∘ N; the Legendre sign is a Class-K pin-slot, never ``abs``."""
    memo_key = (k, index)
    hit = _INV_SQRT_K_CACHE.get(memo_key)
    if hit is not None:
        return hit
    omega = Qalg.alpha(_cyclotomic_m(index))
    if k == 1:
        one = omega.one()
        _INV_SQRT_K_CACHE[memo_key] = one
        return one
    if k == 3:
        z12 = omega ** (index // 12)
        root = z12 + z12.inverse()                  # √3 = 2·cos(2π/12)
    elif k == 7:
        z7 = omega ** (index // 7)
        root = None
        for a in range(1, 7):                       # Class J: the Legendre sum
            term = z7 ** a
            term = term if a in _QR7 else -term     # Class K sign, not abs
            root = term if root is None else root + term
        root = root * (omega ** (index // 4)).inverse()      # g/i = √7
    else:
        raise ValueError(f"_inv_sqrt_k: k must be 1, 3 or 7; got {k!r}")
    inv = root.inverse()
    _INV_SQRT_K_CACHE[memo_key] = inv
    return inv


def _narrow(v):
    """The NARROWEST exact carrier holding ``v``: a plain
    :class:`~srmech.math.q.Q` when the field element is rational, else the
    :class:`Qalg` itself.

    The election is by VALUE, not by a flag — both arms are exact and equal as
    numbers. It is what keeps the QUARTER turns (where ``cos`` and ``sin`` are
    both in ``{0, ±1}``) on the ``Q`` carrier their callers and census rows
    already read, while leaving every other turn on the field carrier that can
    actually hold it."""
    return v.as_rational() if v.is_rational() else v


def _turn_twiddle(dim: int, weights, axis_k: int, n: int, r: int, sigma: int):
    """The EXACT unit twiddle ``cos(σ·2πr/n)·1 + sin(σ·2πr/n)·μ̂`` as a
    ``dim``-component list — ``list[Q]`` when every component is rational, else
    ``list[Qalg]`` over ``Φ_{_turn_field_index(n, axis_k)}``.

    ``weights`` is the axis direction as ``dim`` exact ``Q`` with
    ``weights[0] == 0`` (a pure imaginary), and ``axis_k`` is the scale width:
    the axis is ``μ̂ = weights / √axis_k``, so an equal-weight ``(0,1,1,1)`` at
    ``axis_k = 3`` IS the unit body diagonal with no float anywhere. ``σ`` is
    the Class-C orientation and enters as the sine's sign — the whole of the
    ``σ`` dependence, since the cosine is even.

    The carrier is elected ONCE for the whole list, by
    :func:`_turn_scalars`: a rational cosine beside an irrational sine
    (``n = 3`` at ``axis_k = 1``) keeps BOTH on ``Qalg``, because a list
    carrying ``Q`` in one slot and ``Qalg`` in another is the mixed-carrier
    shape rc463 names as the defect, not a saving. Note the election reads the
    SCALED sine ``sin/√axis_k``, not the bare one, which is why ``n = 3`` at
    ``axis_k = 3`` collapses to ``Q`` (``sin(2π/3)/√3 = 1/2``) where the same
    turn at ``axis_k = 1`` does not.

    This is the ONE construction all three exact twiddle surfaces share
    (``quaternion_twiddle`` / ``octonion_twiddle`` at ``exact=True``, and
    ``hypercomplex_exp`` at ``turn=(k, n)``). No ``abs``: the ``σ`` negation
    is a Class-K
    pin-slot on the sine coordinate, applied by ``Qalg.__neg__``."""
    cos, sin = _turn_scalars(axis_k, n, r, sigma)
    zero = Q(0, 1)
    field_zero = zero if isinstance(cos, Q) else cos - cos
    return [cos] + [(sin * weights[i]) if weights[i] != zero else field_zero
                    for i in range(1, dim)]


def _turn_scalars(axis_k: int, n: int, r: int, sigma: int):
    """``(cos(σ·2πr/n), sin(σ·2πr/n)/√axis_k)`` — the TWO scalars every exact
    twiddle in this tree is built from, jointly narrowed to
    :class:`~srmech.math.q.Q` when both are rational and left as
    :class:`Qalg` over ``Φ_{_turn_field_index(n, axis_k)}`` otherwise.

    Narrowed JOINTLY, never per-component: a rational cosine beside an
    irrational sine (``n = 3`` at ``axis_k = 1``) keeps BOTH on ``Qalg``,
    because a value carrying ``Q`` in one slot and ``Qalg`` in another is the
    mixed-carrier shape rc463 names as the defect, not a saving. ⚠️ The
    election reads the SCALED sine ``sin/√axis_k``, not the bare one, and that
    is load-bearing rather than incidental: ``n = 3`` at ``axis_k = 3``
    collapses to ``Q`` (``sin(2π/3)/√3 = 1/2``) where the SAME turn at
    ``axis_k = 1`` does not. So "the rational set is the quarter turns" is true
    only for ``axis_k = 1``. ``σ`` enters only as the sine's sign — the whole of the ``σ`` dependence, since the cosine is even —
    and it is a Class-K pin-slot via ``__neg__``, never an ``abs``."""
    index = _turn_field_index(n, axis_k)
    cos, sin = _cos_sin_in_field(index, n, r)
    if sigma < 0:                                   # Class C: the other chirality
        sin = -sin
    if axis_k != 1:
        sin = sin * _inv_sqrt_k(axis_k, index)
    if cos.is_rational() and sin.is_rational():
        return cos.as_rational(), sin.as_rational()
    return cos, sin


def cos_sin_2pi_k_over_n(n: int, k: int = 1) -> "tuple":
    """``(cos(2πk/n), sin(2πk/n))`` as an EXACT pair of :class:`Qalg`, BOTH over
    the ONE field ``ℚ(ζ_N)`` with ``N = lcm(n, 4)`` — **the module's only
    cyclotomic trig constructor**, and the one every exact twiddle in this tree
    is built from.

    **It ABSORBED two ops rather than joining them (0.9.0rc468, `#T1188`).**
    rc463 shipped ``cos_2pi_over_n(n)`` over ``Φ_n`` and ``sin_2pi_over_n(n)``
    over ``Φ_lcm(n,4)``; this op arrived beside them and, with ``k`` defaulting
    to 1, simply IS them. Both are REMOVED — no alias, no deprecation wrapper:
    ``cos_sin_2pi_k_over_n(n)`` is the pair they used to return separately.
    Two things it does that they could not, and both are why the exact
    twiddle routes could not be written on them:

    * **a general turn.** They answered only at ``k = 1``. A DFT twiddle
      needs ``2π·((j·k) mod N)/N`` — every turn, not one.
    * **ONE field.** The cosine answered over ``Φ_n`` and the sine over
      ``Φ_lcm(n,4)``, so for ``4 ∤ n`` they lived in
      different fields and ``Qalg`` correctly REFUSED to add them — a cosine
      that could not be added to its own sine. Both values
      here are built over ``Φ_lcm(n,4)``, so they compose: ``c*c + s*s == 1``
      exactly at every ``n`` — MEASURED (not asserted) at
      ``n ∈ {3, 5, 7, 8, 12, 16, 64}`` — and ``(c + s·i)**n == 1`` exactly
      with ``i = ζ_N^(N/4)``.

    **The rational-collapse verdict is decidable, and it is exactly the QUARTER
    TURNS.** ``c`` and ``s`` are BOTH rational precisely when ``4·k ≡ 0
    (mod n)`` — measured over every turn of every ``n ≤ 16``, not assumed.
    That is why the exact twiddle routes return ``list[Q]`` on the quarter
    turns and ``list[Qalg]`` elsewhere: the carrier is elected by the VALUE.

    **Cascade composition.** Class J (the divisor lattice building ``Φ_N`` and
    the ``lcm`` choosing ``N``) ∘ Class I (``k mod n`` — the turn is reduced in
    ``Z_n`` FIRST, exactly, so ``k`` may be any int) ∘ Class N (the exact
    rational coordinates) ∘ Class C (the ``ζ`` rotation; the cosine is the
    symmetric part of the two chiralities, the sine the anti-symmetric part).
    No ``abs``, no ``math``, no float, no series.

    Args:
        n: the turn denominator, ``n >= 1``, admitted when the field it
            builds is small enough:
            ``cyclotomic_degree(lcm(n, 4)) <= MAX_CYCLOTOMIC_DEGREE`` (888).
            **That is a SIEVE over ``n``, not a ceiling** — the largest
            admitted ``n`` is 3780, and some smaller ``n`` above it refuse
            while larger ones do not. ``TypeError`` for a non-``int``
            (``bool`` included); ``ValueError`` for ``n < 1`` or for a field
            above the degree cap, naming the index and the degree.
        k: the turn numerator (any ``int``; reduced mod ``n``). Default ``1``,
            which is the plain ``2π/n`` turn the two removed rc463
            constructors answered at.

    Returns:
        ``(cos, sin)`` — two ``Qalg`` over ``m = Φ_lcm(n, 4)``, both with
        ``root=None`` — no embedding is attached, because computing
        ``e^(2πi/N)`` would need exactly the FPU transcendental this op exists
        to avoid. Attach one yourself with ``.with_root(...)`` when you want
        the terminal projection.

    Worked anchors::

        c, s = cos_sin_2pi_k_over_n(8, 1)
        c * c + s * s == c.one()
        # -> True        exactly, over Phi_8

        c, s = cos_sin_2pi_k_over_n(4, 1)      # a QUARTER turn
        (c.as_rational(), s.as_rational())
        # -> (Q(0, 1), Q(1, 1))                cos = 0, sin = 1, both rational

        c, s = cos_sin_2pi_k_over_n(3, 1)
        c.as_rational()
        # -> Q(-1, 2)                          cos(2 pi / 3) = -1/2 exactly
        s.is_rational()
        # -> False                             sin = sqrt(3) / 2

    Cost is set by the DEGREE ``φ(lcm(n, 4))`` — one turn measured on this
    tree: ``n = 8`` 0.6 ms, ``n = 64`` 2.0 ms, ``n = 128`` 3.4 ms,
    ``n = 256`` 7.1 ms. ``Φ`` itself is memoised (:func:`_cyclotomic_m`).

    See also:
        :func:`srmech.physics.qm.quaternion.quaternion_twiddle` and
        :func:`srmech.physics.qm.octonion.octonion_twiddle` at ``exact=True``,
        and :func:`srmech.cascade.hypercomplex_exp` at ``turn=(k, n)`` — the
        three hypercomplex surfaces this constructor makes exact.

    Note:
        Exact ``Q`` throughout; no ``abs``; no ``math``; no float.
    """
    _validated_index(n, "cos_sin_2pi_k_over_n")
    if isinstance(k, bool) or not isinstance(k, int):
        raise TypeError(
            f"cos_sin_2pi_k_over_n: k must be a plain int (the turn "
            f"numerator); got {type(k).__name__}")
    return _cos_sin_in_field(4 * n // _gcd(n, 4), n, k)
