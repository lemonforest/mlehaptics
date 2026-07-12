"""srmech.amsc.qprime — the framework-native EXACT prime-coordinate carrier (``Qprime``).

The Class-J peer of the exact-carrier family. Where :class:`srmech.amsc.qi.Qi`
carries an exact Gaussian rational and :class:`srmech.amsc.qalg.Qalg` an exact
algebraic-number-field element, ``Qprime`` carries a positive integer in its
**prime-coordinate** representation — the exponent vector
``{p₁: e₁, p₂: e₂, …}`` of the fundamental theorem of arithmetic
``n = ∏ pᵢ^eᵢ`` (every ``n ≥ 1`` has a UNIQUE such factorisation). This is the
exact-substrate carrier for **Class J** (primes / factorisation /
multiplicative-period structure) — the F923 / UPSTREAM §74 capstone that closes
the LAST open harmonic-ladder rung.

**The lens — multiplication is addition in prime-coordinates.** A positive
integer factored into ``∏ pᵢ^eᵢ`` IS a vector over the (infinite) prime basis
with the exponents as coordinates. In that basis the multiplicative monoid of
the positive integers becomes the ADDITIVE monoid of exponent vectors:
``a·b`` adds exponents elementwise, ``gcd`` takes the elementwise MIN over the
shared support, ``lcm`` the elementwise MAX over the union. So ``Qprime`` is the
exact carrier that makes the multiplicative structure of ℤ⁺ *linear*. (The
classic ``log`` is the float-projection of exactly this — but ``Qprime`` stays
exact integers, never lifting to a float.)

**State.** A read-only exponent dict ``coords = {prime: exponent}`` with every
prime an actual prime, every exponent a positive int (zero exponents are NOT
stored — an absent prime IS exponent 0). ``Qprime(1)`` is the EMPTY vector (the
multiplicative identity). Construction is via the Class-J
:func:`srmech.amsc.primes.factor`; reconstruction (:meth:`to_int`) is
``∏ pᵉ``.

**The exact operations (composes Class J + Class I, no new C).**

* ``*`` [Class J] — multiply = ADD exponents elementwise. Equal to
  ``factor(a·b)`` by the FTA (the headline lens).
* :meth:`gcd` — elementwise MIN over the shared primes. Equal to
  :func:`srmech.amsc.cyclic.gcd` (Class I) on the reconstructed ints.
* :meth:`lcm` — elementwise MAX over the prime union. Equal to
  :func:`srmech.amsc.cyclic.lcm` (Class I).
* :meth:`similarity` — the EXACT shared-factor overlap: the cosine of the two
  exponent vectors, **squared**, as an exact :class:`~srmech.amsc.q.Q`
  (``Q(dot², ‖a‖²·‖b‖²)``). 0 for a coprime pair (disjoint support).
  Float only at the display boundary.
* :meth:`period` [Class J period structure] — the multiplicative order
  ``ord_modulus(self.to_int())`` (smallest ``k > 0`` with ``nᵏ ≡ 1 mod m``),
  the "repeating-decimal period of ``1/m`` in base ``n``" lens. Routes through
  the Class-J :func:`srmech.amsc.primes.cyclic_period`; the order is defined
  only when ``gcd(n, modulus) == 1`` (raises a clear ``ValueError`` otherwise).

It is a CARRIER (a single-class module, ``__all__ = ["Qprime"]``, ``Q``-based),
NOT a ToolEntry — mirroring ``Qi`` / ``Qalg``. No ``math`` module, no numpy; the
whole body is exact integer / exact ``Q`` arithmetic over the existing Class-J
(``primes``) + Class-I (``cyclic``) primitives, which already carry native C.

References
----------
The fundamental theorem of arithmetic (unique prime factorisation) and the
multiplicative-order / period structure of ``(ℤ/mℤ)*`` are the canonical
number-theory ground (e.g. Hardy & Wright, *An Introduction to the Theory of
Numbers*, §1.3 unique factorisation + §6.8 the order of ``a (mod m)``).
"""

from __future__ import annotations

from typing import Dict

from . import cyclic as _cyclic
from . import primes as _primes
from .q import Q

__all__ = ["Qprime"]


class Qprime:
    """A positive integer in its EXACT prime-coordinate representation — the
    exponent vector ``{prime: exponent}`` of ``n = ∏ pᵉ``. The Class-J exact
    carrier; multiply = add-exponents, gcd = min, lcm = max. See the module
    docstring."""

    __slots__ = ("_coords",)

    def __init__(self, n: int) -> None:
        """Construct from a positive int ``n ≥ 1`` via the Class-J
        :func:`srmech.amsc.primes.factor`. Raises ``ValueError`` for ``n < 1``
        (0 and negatives have no prime-coordinate vector); ``TypeError`` for a
        non-int (``bool`` excluded)."""
        if isinstance(n, bool) or not isinstance(n, int):
            raise TypeError(
                f"Qprime(n) takes a positive int; got {type(n).__name__}")
        if n < 1:
            raise ValueError(
                f"Qprime requires a positive int n >= 1; got {n}")
        # factor(1) == [] (the empty vector / identity); factor(n) is the
        # canonical ascending [(p, e), ...] with n = ∏ p^e (FTA).
        self._coords = {p: e for p, e in _primes.factor(n)}

    # ── constructors ────────────────────────────────────────────────────────
    @classmethod
    def from_vec(cls, vec: Dict[int, int]) -> "Qprime":
        """Build directly from a ``{prime: exponent}`` exponent vector (the
        inverse of :attr:`coords`). Every key must be an actual prime and every
        value a positive int; a zero/absent exponent is simply omitted. The
        empty dict is :class:`Qprime` of 1 (the identity)."""
        if not isinstance(vec, dict):
            raise TypeError(
                f"Qprime.from_vec takes a {{prime: exponent}} dict; "
                f"got {type(vec).__name__}")
        coords: Dict[int, int] = {}
        for p, e in vec.items():
            if isinstance(p, bool) or not isinstance(p, int):
                raise TypeError(f"Qprime.from_vec prime keys must be int; got {p!r}")
            if isinstance(e, bool) or not isinstance(e, int):
                raise TypeError(f"Qprime.from_vec exponents must be int; got {e!r}")
            if e == 0:
                continue                       # exponent-0 == absent prime
            if e < 0:
                raise ValueError(
                    f"Qprime.from_vec exponents must be non-negative; got {e}")
            if not _primes.is_prime(p):
                raise ValueError(
                    f"Qprime.from_vec keys must be prime; {p} is not prime")
            coords[p] = e
        obj = cls.__new__(cls)
        obj._coords = coords
        return obj

    @classmethod
    def _from_coords_unchecked(cls, coords: Dict[int, int]) -> "Qprime":
        """Internal: wrap an already-validated exponent dict (the result of an
        op over two validated carriers) with no re-factor / re-prime-check."""
        obj = cls.__new__(cls)
        obj._coords = {p: e for p, e in coords.items() if e != 0}
        return obj

    # ── exact accessors ─────────────────────────────────────────────────────
    @property
    def coords(self) -> Dict[int, int]:
        """The exponent vector ``{prime: exponent}`` as a read-only COPY (a
        fresh dict each call, so the carrier's state cannot be mutated through
        it). Absent primes are exponent 0."""
        return dict(self._coords)

    def to_int(self) -> int:
        """Reconstruct the positive int ``∏ pᵉ`` (the inverse of the
        constructor). ``Qprime(1).to_int() == 1`` (the empty product)."""
        result = 1
        for p, e in self._coords.items():
            result *= p ** e
        return result

    # ── reprs / equality ────────────────────────────────────────────────────
    def __repr__(self) -> str:
        # Sorted by prime for a canonical, deterministic repr.
        items = ", ".join(f"{p}: {e}" for p, e in sorted(self._coords.items()))
        return f"Qprime.from_vec({{{items}}})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Qprime):
            return NotImplemented
        return self._coords == other._coords

    def __ne__(self, other) -> bool:
        eq = self.__eq__(other)
        return eq if eq is NotImplemented else not eq

    def __hash__(self) -> int:
        # Equal carriers (same exponent vector) hash equal; key on the canonical
        # sorted (prime, exponent) tuple so two Qprime of the same int agree.
        return hash(tuple(sorted(self._coords.items())))

    def __bool__(self) -> bool:
        # Qprime(1) (the empty vector) is the multiplicative identity, not zero —
        # there is no "zero" in prime-coordinates (0 has no factorisation), so
        # every Qprime is truthy. (to_int() >= 1 always.)
        return True

    # ── Class J: multiply = ADD exponents elementwise ───────────────────────
    def __mul__(self, other) -> "Qprime":
        """[Class J] Multiply = ADD the two exponent vectors elementwise. By the
        fundamental theorem of arithmetic this equals ``factor(a·b)`` — the
        headline lens that multiplication is addition in prime-coordinates."""
        if not isinstance(other, Qprime):
            return NotImplemented
        out = dict(self._coords)
        for p, e in other._coords.items():
            out[p] = out.get(p, 0) + e
        return Qprime._from_coords_unchecked(out)

    # ── Class I: gcd = elementwise MIN over the shared support ───────────────
    def gcd(self, other: "Qprime") -> "Qprime":
        """Elementwise MIN over the SHARED primes — the greatest common divisor
        in prime-coordinates. Equals :func:`srmech.amsc.cyclic.gcd` (Class I) on
        the reconstructed ints. A prime absent from either side is exponent 0
        there, so MIN drops it (only the shared support survives)."""
        if not isinstance(other, Qprime):
            raise TypeError("Qprime.gcd requires another Qprime")
        out: Dict[int, int] = {}
        for p, e in self._coords.items():
            f = other._coords.get(p)
            if f is not None:
                out[p] = e if e <= f else f     # min(e, f), no ALU branch hidden
        return Qprime._from_coords_unchecked(out)

    # ── Class I: lcm = elementwise MAX over the prime UNION ──────────────────
    def lcm(self, other: "Qprime") -> "Qprime":
        """Elementwise MAX over the prime UNION — the least common multiple in
        prime-coordinates. Equals :func:`srmech.amsc.cyclic.lcm` (Class I) on the
        reconstructed ints. Every prime in either support survives at its larger
        exponent."""
        if not isinstance(other, Qprime):
            raise TypeError("Qprime.lcm requires another Qprime")
        out = dict(self._coords)
        for p, f in other._coords.items():
            e = out.get(p, 0)
            out[p] = e if e >= f else f         # max(e, f)
        return Qprime._from_coords_unchecked(out)

    # ── exact shared-factor overlap (cosine²) ────────────────────────────────
    def similarity(self, other: "Qprime") -> Q:
        """The EXACT shared-factor overlap — the cosine of the two exponent
        vectors, **squared**, as an exact :class:`~srmech.amsc.q.Q`:
        ``Q(dot², ‖a‖²·‖b‖²)``. The dot product / squared norms are over
        the integer exponents, so the result is an exact rational; only at the
        display boundary (``float(...)``) does it become a decimal. A coprime
        pair (disjoint support ⇒ ``dot == 0``) is exactly ``Q(0)``; equal vectors
        are exactly ``Q(1)``. (Verified: ``similarity(12, 18) == 16/25``.)"""
        if not isinstance(other, Qprime):
            raise TypeError("Qprime.similarity requires another Qprime")
        dot = 0
        for p, e in self._coords.items():
            f = other._coords.get(p)
            if f is not None:
                dot += e * f
        na_sq = sum(e * e for e in self._coords.values())
        nb_sq = sum(f * f for f in other._coords.values())
        denom = na_sq * nb_sq
        if denom == 0:
            # An empty vector (Qprime(1)) has zero norm — the overlap with it is
            # undefined (0/0); define it as 0 (no shared multiplicative content).
            return Q(0, 1)
        # cos² = dot² / (‖a‖²·‖b‖²) — exact rational straight on the Q carrier
        # (rc167 #765: no Fraction detour; Q's Class-N reduce IS the same
        # lowest-terms/positive-den canonicalisation, and its big-component
        # arithmetic dispatches to srmech's own C bignum). Byte-identical.
        return Q(dot * dot, denom)

    # ── Class J period structure: the multiplicative order ───────────────────
    def period(self, modulus: int) -> int:
        """[Class J period structure] The multiplicative ORDER of ``self.to_int()``
        modulo ``modulus`` — the smallest ``k > 0`` with ``nᵏ ≡ 1 (mod modulus)``.
        This is the "period of the repeating expansion of ``1/modulus`` in base
        ``n``" lens (``ord₇(10) == 6`` ⇔ ``1/7 = 0.142857…`` has period 6).

        Routes through the Class-J :func:`srmech.amsc.primes.cyclic_period`. The
        order is defined ONLY when ``gcd(n, modulus) == 1`` (``n`` a unit in
        ``(ℤ/modulusℤ)*``) and ``modulus >= 2``; both are checked there and raise
        a clear ``ValueError`` otherwise."""
        n = self.to_int()
        # cyclic_period handles the gcd!=1 / modulus<2 guards (raises ValueError);
        # it reads n mod modulus internally.
        return _primes.cyclic_period(n, modulus)


# ``Qprime`` is the exact Class-J carrier — the prime-coordinate exponent vector
# with multiply=add-exponents (== factor(a·b)), gcd=min, lcm=max, exact cosine²
# similarity, and the multiplicative-order period. It is NOT registered with any
# ``numbers`` ABC (it is the multiplicative monoid of ℤ⁺ in exponent-space, not a
# field element), staying a standalone exact carrier like ``Qalg``.
