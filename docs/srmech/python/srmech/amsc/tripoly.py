"""srmech.amsc.tripoly — the framework-native EXACT-rational TRIVARIATE polynomial
carrier (``TriPoly``), the foundation of the multivariate "sums of sums" creative-
telescoping row (the rc53 ``apagodu_zeilberger`` op consumes it).

The 3-variable sibling of the bivariate :class:`srmech.amsc.zeilberger.BiPoly`.
Where ``BiPoly`` carries an exact-``ℚ[n,k]`` polynomial (a polynomial in the
summation variable ``k`` whose coefficients are :class:`~srmech.amsc.poly.Poly`
in the free variable ``n``), ``TriPoly`` carries an exact-``ℚ[n,j,k]`` polynomial
in the free/recurrence variable ``n`` and **two** summation variables ``j`` and
``k`` — the substrate a double definite sum ``f(n) = Σ_j Σ_k F(n,j,k)`` rides.

Representation (BiPoly's pattern recursed exactly one level). ``BiPoly`` is a
``k``-ascending tuple of ``Poly``-in-``n``; ``TriPoly`` is a **``j``-ascending
tuple of** :class:`~srmech.amsc.zeilberger.BiPoly` **in ``(n,k)``** — ``blocks[d]``
is the coefficient of ``j**d`` and is itself a ``BiPoly`` over ``ℚ[n,k]``.
Trailing-zero (high-``j``-degree) ``BiPoly`` coefficients are trimmed, so the zero
``TriPoly`` is the empty block list and the ``j``-degree is ``len(blocks) - 1``
(``-1`` for the zero polynomial). One level down, each ``BiPoly`` trims its
trailing-zero ``k``-coefficients, and each ``Poly``-in-``n`` trims its trailing-
zero ``n``-coefficients — so the canonical form is exact at every level and two
``TriPoly`` are equal iff their trimmed block tuples are equal.

Everything stays exact ``ℚ`` over Python-``int`` bigint (so **no magnitude
ceiling**: a coefficient numerator or denominator may freely exceed ``2⁶⁴``,
unlike a native int64 / Q61 fixed-point path). ``+`` / ``−`` / ``−x`` / scalar-``ℚ``
``*`` / trivariate ``*`` ride the ``BiPoly`` → ``Poly`` → ``Q`` Class-N rational
arithmetic; sign is the **Class-K** pin-slot via the ``Q`` sign-branch (the
reduced ``Q`` denominator is positive, so the numerator carries the sign), never
an ALU ``abs()``. No ``math`` module, no numpy — like ``Poly`` / ``BiPoly`` /
``QMat``.

The **shift / difference operators** are the rc53 Apagodu–Zeilberger payload.
:meth:`shift_n` / :meth:`shift_j` / :meth:`shift_k` substitute the named variable
``var → var + s`` (``s`` an int); :meth:`delta_j` / :meth:`delta_k` are the
forward differences ``Δ_j f = f(…, j+1, …) − f`` and ``Δ_k f = f(…, k+1, …) − f``.
A joint-certificate solver expresses a creative-telescoping identity as
``Σ_i a_i(n)·F(n+i, j, k) = Δ_j G_j + Δ_k G_k`` — :meth:`shift_n` builds the
``F(n+i, …)`` ladder, :meth:`delta_j` / :meth:`delta_k` build the telescoping
right-hand side, and the ``+`` / ``−`` / ``*`` algebra assembles the linear system
over the unknown ``a_i(n)`` and the ``G_j`` / ``G_k`` certificate coefficients.

This is a **carrier** (a peer of ``Poly`` / ``BiPoly`` / ``QMat``), NOT a
ToolEntry — it ships with its algebra, like every srmech carrier, but does not add
to ``describe()["tools"]["total"]``. The C peer ``srmech_tripoly_*`` (add / sub /
mul + ``ws_bound``) mirrors the ``srmech_poly_*`` arena/overflow discipline over
caller-arena bignum (OVERFLOW-not-wrap); ``TriPoly`` routes its add/sub/mul through
it when ``HAS_NATIVE`` (:func:`srmech.amsc._native.has_native_tripoly`), with the
pure-Python body here the COMPLETE alternative (and the byte-identical parity
oracle). The shift / difference operators are pure-Python compositions over the
native-accelerated add/sub/mul (mirroring how ``Poly.shift`` rides ``poly_mul`` /
``poly_add``).
"""

from __future__ import annotations

from typing import List, Sequence, Tuple

from .poly import Poly
from .q import Q
from .zeilberger import BiPoly

__all__ = ["TriPoly", "tripoly_from_coeffs"]

_Q_ZERO = Q(0, 1)
_Q_ONE = Q(1, 1)


def _native():
    """The native ``_native`` module IF the ``srmech_tripoly_*`` peer is present
    and bound, else ``None`` — so the carrier dispatches to C when available and
    falls cleanly to the pure-Python body (the complete alternative + the parity
    oracle) otherwise. Imported lazily to avoid a bootstrap cycle."""
    try:
        from . import _native as nat
    except ImportError:
        return None
    probe = getattr(nat, "has_native_tripoly", None)
    return nat if (probe is not None and probe()) else None


def _tri_trim(cells: Sequence[BiPoly]) -> Tuple[BiPoly, ...]:
    """Drop trailing-zero (high-``j``-degree) ``BiPoly`` coefficients → canonical
    form. The zero ``TriPoly`` trims to the empty tuple ``()``."""
    n = len(cells)
    while n > 0 and cells[n - 1].is_zero:
        n -= 1
    return tuple(cells[:n])


def _as_biblock(value) -> BiPoly:
    """Coerce one ``j``-degree block to a :class:`~srmech.amsc.zeilberger.BiPoly`
    in ``(n,k)``. A ``BiPoly`` passes through; a :class:`~srmech.amsc.poly.Poly`
    is read as a polynomial in ``k`` alone (per ``BiPoly.coerce``); anything else
    is handed to ``BiPoly.coerce`` (a ``k``-ascending sequence of ``Poly``-in-n)."""
    if isinstance(value, BiPoly):
        return value
    return BiPoly.coerce(value)


# ── the wire form for the C bridge ────────────────────────────────────────────
#
# A TriPoly → a (j,k) grid of n-Poly coefficient runs. The bridge form is a
# j-ascending list, each entry a k-ascending list, each entry an ascending-n list
# of (num, den) int pairs — i.e. [[ [(num,den),…]_n ]_k ]_j. The C peer flattens
# this row-major over (j,k) with the per-cell n-Poly run carried alongside.


def _tri_pairs(t: "TriPoly") -> List[List[List[Tuple[int, int]]]]:
    """A ``TriPoly`` → the nested ``[[[(num, den), …]_n]_k]_j`` bridge form (j-major,
    then k, then ascending-n ``Poly`` coefficients) the C peer consumes."""
    out: List[List[List[Tuple[int, int]]]] = []
    for bib in t._b:
        kgrid: List[List[Tuple[int, int]]] = []
        for kp in bib.terms:
            kgrid.append([(c.numerator, c.denominator) for c in kp.coeffs])
        out.append(kgrid)
    return out


def _tri_from_pairs(blocks) -> "TriPoly":
    """Rebuild a ``TriPoly`` from the nested ``[[[(num, den), …]_n]_k]_j`` bridge
    form (from the C peer; each leaf already reduced)."""
    cells: List[BiPoly] = []
    for kgrid in blocks:
        terms = [Poly.from_coeffs([Q(int(n), int(d)) for n, d in run])
                 for run in kgrid]
        cells.append(BiPoly(terms))
    return TriPoly._wrap(_tri_trim(cells))


class TriPoly:
    """A numpy-free EXACT-rational TRIVARIATE polynomial over ``ℚ`` in the free
    variable ``n`` and two summation variables ``j``, ``k``: a trimmed tuple of
    :class:`~srmech.amsc.zeilberger.BiPoly` in ``(n,k)`` indexed by ``j``-degree,
    immutable. The 3-variable sibling of ``BiPoly`` and the foundation of the
    rc53 ``apagodu_zeilberger`` op. See the module docstring."""

    __slots__ = ("_b",)

    def __init__(self, blocks: Sequence[BiPoly] = ()) -> None:
        cells: List[BiPoly] = [_as_biblock(b) for b in blocks]
        self._b = _tri_trim(cells)

    # ── construction ───────────────────────────────────────────────────────
    @classmethod
    def _wrap(cls, trimmed: Tuple[BiPoly, ...]) -> "TriPoly":
        """Internal: wrap an ALREADY-trimmed tuple of ``BiPoly`` with no re-coerce."""
        t = cls.__new__(cls)
        t._b = trimmed
        return t

    @classmethod
    def from_coeffs(cls, blocks) -> "TriPoly":
        """Build a ``TriPoly`` from a ``j``-ascending sequence of ``j``-degree
        blocks (the canonical constructor). Each block is coerced to a
        :class:`~srmech.amsc.zeilberger.BiPoly` in ``(n,k)`` — a ``BiPoly`` passes
        through, a :class:`~srmech.amsc.poly.Poly` is read as a polynomial in ``k``
        alone, a ``k``-ascending coefficient sequence is wrapped term-by-term."""
        return cls(blocks)

    @classmethod
    def from_dict(cls, terms) -> "TriPoly":
        """Build from a sparse ``{(dn, dj, dk): coeff}`` mapping — ``coeff`` is the
        exact-``ℚ`` coefficient (``Q`` / ``int`` / ``(num, den)`` / ``Fraction``)
        of the monomial ``n**dn · j**dj · k**dk``. The natural constructor for a
        term ratio written monomial-by-monomial. A ``float`` coefficient is
        rejected (exact-rational only); a negative degree is rejected."""
        max_j = -1
        grid = {}
        for key, coeff in terms.items():
            dn, dj, dk = key
            if not (isinstance(dn, int) and isinstance(dj, int)
                    and isinstance(dk, int)):
                raise TypeError("TriPoly.from_dict keys must be (dn, dj, dk) ints")
            if dn < 0 or dj < 0 or dk < 0:
                raise ValueError("TriPoly.from_dict: degrees must be non-negative")
            q = _to_q(coeff)
            if q is None:
                raise TypeError(
                    "TriPoly.from_dict coefficients must be exact-rational "
                    f"(Q / int / (num, den) / Fraction); got {coeff!r}")
            if dj > max_j:
                max_j = dj
            grid[(dn, dj, dk)] = grid.get((dn, dj, dk), _Q_ZERO) + q
        if max_j < 0:
            return cls._wrap(())
        # assemble each j-block as a BiPoly: k-ascending Poly-in-n.
        cells: List[BiPoly] = []
        for dj in range(max_j + 1):
            # gather {(dn, dk): q} for this j into a BiPoly.
            max_k = -1
            for (dn, jj, dk) in grid:
                if jj == dj and dk > max_k:
                    max_k = dk
            k_terms: List[Poly] = []
            for dk in range(max_k + 1):
                # the Poly-in-n at (dj, dk).
                max_n = -1
                for (dn, jj, kk) in grid:
                    if jj == dj and kk == dk and dn > max_n:
                        max_n = dn
                n_coeffs = [grid.get((dn, dj, dk), _Q_ZERO) for dn in range(max_n + 1)]
                k_terms.append(Poly.from_coeffs(n_coeffs) if n_coeffs else Poly.zero())
            cells.append(BiPoly(k_terms))
        return cls._wrap(_tri_trim(cells))

    @classmethod
    def zero(cls) -> "TriPoly":
        """The zero trivariate polynomial (empty block tuple; ``j``-degree ``-1``)."""
        return cls._wrap(())

    @classmethod
    def one(cls) -> "TriPoly":
        """The constant trivariate polynomial ``1``."""
        return cls._wrap((BiPoly.one(),))

    @classmethod
    def from_n_poly(cls, p: Poly) -> "TriPoly":
        """A polynomial in ``n`` ALONE → the constant-in-``(j,k)`` ``TriPoly``."""
        return cls._wrap(() if p.is_zero else (BiPoly.from_n_poly(p),))

    @classmethod
    def from_bipoly(cls, b: BiPoly) -> "TriPoly":
        """A ``BiPoly`` in ``(n,k)`` ALONE (no ``j``) → the constant-in-``j``
        ``TriPoly`` (the ``j**0`` block is the whole ``BiPoly``)."""
        return cls._wrap(() if b.is_zero else (b,))

    @classmethod
    def monomial(cls, dn: int, dj: int, dk: int, coeff=_Q_ONE) -> "TriPoly":
        """The single-term ``coeff · n**dn · j**dj · k**dk`` (all degrees ≥ 0)."""
        if not (isinstance(dn, int) and isinstance(dj, int) and isinstance(dk, int)):
            raise TypeError("TriPoly.monomial: dn, dj, dk must be ints")
        if dn < 0 or dj < 0 or dk < 0:
            raise ValueError("TriPoly.monomial: degrees must be non-negative")
        q = _to_q(coeff)
        if q is None:
            raise TypeError(f"TriPoly.monomial: coeff not exact-rational: {coeff!r}")
        if q == 0:
            return cls._wrap(())
        # the (dj) block is a BiPoly whose (dk) term is the Poly n**dn · coeff.
        k_terms = [Poly.zero()] * dk + [Poly.monomial(dn, q)]
        bib = BiPoly(k_terms)
        blocks = [BiPoly.zero()] * dj + [bib]
        return cls._wrap(_tri_trim(blocks))

    # ── accessors ──────────────────────────────────────────────────────────
    @property
    def blocks(self) -> Tuple[BiPoly, ...]:
        """The trimmed ``j``-ascending tuple of ``BiPoly``-in-``(n,k)`` coefficients."""
        return self._b

    @property
    def j_degree(self) -> int:
        """The degree in ``j`` (``-1`` for the zero polynomial)."""
        return len(self._b) - 1

    @property
    def k_degree(self) -> int:
        """The max degree in ``k`` across all ``j``-blocks (``-1`` for zero)."""
        d = -1
        for bib in self._b:
            if bib.k_degree > d:
                d = bib.k_degree
        return d

    @property
    def n_degree(self) -> int:
        """The max degree in ``n`` across every ``(j,k)`` coefficient (``-1`` for
        the zero polynomial)."""
        d = -1
        for bib in self._b:
            for kp in bib.terms:
                if kp.degree > d:
                    d = kp.degree
        return d

    @property
    def is_zero(self) -> bool:
        """True iff this is the zero polynomial (empty block tuple)."""
        return len(self._b) == 0

    def block(self, dj: int) -> BiPoly:
        """The ``BiPoly``-in-``(n,k)`` coefficient of ``j**dj`` (zero ``BiPoly``
        past the ``j``-degree)."""
        return self._b[dj] if 0 <= dj < len(self._b) else BiPoly.zero()

    def coeff(self, dn: int, dj: int, dk: int) -> Q:
        """The exact-``ℚ`` coefficient of the monomial ``n**dn · j**dj · k**dk``
        (``Q(0)`` past any degree)."""
        bib = self.block(dj)
        return bib.coeff(dk)[dn]

    def __eq__(self, other) -> bool:
        """Exact equality. Accepts another ``TriPoly`` or a coercible block
        sequence."""
        if other is self:
            return True
        if isinstance(other, TriPoly):
            return self._b == other._b
        try:
            o = TriPoly.from_coeffs(other)
        except (TypeError, ValueError):
            return NotImplemented
        return self._b == o._b

    def __ne__(self, other):
        result = self.__eq__(other)
        return result if result is NotImplemented else (not result)

    def __hash__(self) -> int:
        # Immutable (trimmed tuple of BiPoly); equal polynomials hash equal.
        return hash(self._b)

    def __repr__(self) -> str:
        return (f"TriPoly(j_degree={self.j_degree}, k_degree={self.k_degree}, "
                f"n_degree={self.n_degree}, exact-ℚ[n,j,k])")

    # ── exact arithmetic over ℚ[n,j,k] (Class-K sign via BiPoly/Poly/Q) ─────
    def _as_tripoly(self, other) -> "TriPoly | None":
        """Coerce ``other`` to a ``TriPoly`` (a ``TriPoly`` passes through; a
        ``BiPoly`` / ``Poly`` / ``Q`` / scalar is lifted), or ``None`` if not
        coercible."""
        if isinstance(other, TriPoly):
            return other
        if isinstance(other, BiPoly):
            return TriPoly.from_bipoly(other)
        if isinstance(other, Poly):
            return TriPoly.from_bipoly(BiPoly.from_k_poly(other))
        q = _to_q(other)
        if q is not None:
            return TriPoly._wrap(() if q == 0 else (BiPoly.from_n_poly(Poly.from_coeffs([q])),))
        try:
            return TriPoly.from_coeffs(other)
        except (TypeError, ValueError):
            return None

    def __add__(self, other):
        o = self._as_tripoly(other)
        if o is None:
            return NotImplemented
        nat = _native()
        if nat is not None:
            try:
                blocks = nat.tripoly_add_c(_tri_pairs(self), _tri_pairs(o))
                if blocks is not None:
                    return _tri_from_pairs(blocks)
            except (RuntimeError, OverflowError, ValueError):
                pass                                 # fall to the pure path
        m = max(len(self._b), len(o._b))
        out = [self.block(d) + o.block(d) for d in range(m)]
        return TriPoly._wrap(_tri_trim(out))

    __radd__ = __add__

    def __neg__(self) -> "TriPoly":
        # The Class-K sign-flip over every BiPoly block (no ALU abs).
        return TriPoly._wrap(tuple(-b for b in self._b))

    def __sub__(self, other):
        o = self._as_tripoly(other)
        if o is None:
            return NotImplemented
        nat = _native()
        if nat is not None:
            try:
                blocks = nat.tripoly_sub_c(_tri_pairs(self), _tri_pairs(o))
                if blocks is not None:
                    return _tri_from_pairs(blocks)
            except (RuntimeError, OverflowError, ValueError):
                pass
        m = max(len(self._b), len(o._b))
        out = [self.block(d) - o.block(d) for d in range(m)]
        return TriPoly._wrap(_tri_trim(out))

    def __rsub__(self, other):
        o = self._as_tripoly(other)
        if o is None:
            return NotImplemented
        return o.__sub__(self)

    def __mul__(self, other):
        """Scalar-``ℚ`` multiply (``Q`` / ``int`` / ``Fraction`` / ``(num, den)``),
        OR the trivariate polynomial product when ``other`` is a ``TriPoly`` /
        ``BiPoly`` / ``Poly`` / coercible block sequence."""
        q = _to_q(other)
        if q is not None:
            if q == 0:
                return TriPoly._wrap(())
            # scalar-ℚ scale = scale every BiPoly block by the constant Poly q.
            scale = Poly.from_coeffs([q])
            return TriPoly._wrap(_tri_trim([b.scale_n(scale) for b in self._b]))
        o = self._as_tripoly(other)
        if o is None:
            return NotImplemented
        return self._mul_tri(o)

    __rmul__ = __mul__

    def _mul_tri(self, other: "TriPoly") -> "TriPoly":
        """The exact trivariate product (``j``-convolution of ``BiPoly`` blocks,
        each ``BiPoly`` product itself an exact ``ℚ[n,k]`` multiply)."""
        if self.is_zero or other.is_zero:
            return TriPoly._wrap(())
        nat = _native()
        if nat is not None:
            try:
                blocks = nat.tripoly_mul_c(_tri_pairs(self), _tri_pairs(other))
                if blocks is not None:
                    return _tri_from_pairs(blocks)
            except (RuntimeError, OverflowError, ValueError):
                pass
        a, b = self._b, other._b
        out = [BiPoly.zero()] * (len(a) + len(b) - 1)
        for i, ai in enumerate(a):
            if ai.is_zero:
                continue
            for jj, bj in enumerate(b):
                if bj.is_zero:
                    continue
                out[i + jj] = out[i + jj] + ai * bj     # BiPoly-in-(n,k) product
        return TriPoly._wrap(_tri_trim(out))

    def scale_n(self, p: Poly) -> "TriPoly":
        """Multiply every ``(j,k)`` coefficient by a ``Poly``-in-``n`` ``p`` (exact)."""
        if p.is_zero or self.is_zero:
            return TriPoly._wrap(())
        return TriPoly._wrap(_tri_trim([b.scale_n(p) for b in self._b]))

    # ── evaluation ──────────────────────────────────────────────────────────
    def eval(self, n, j, k) -> Q:
        """Evaluate at ``(n, j, k)`` (each an exact ``Q`` / ``int`` / ``(num, den)``
        / ``Fraction``) → an exact ``Q``. Substitutes all three variables by exact
        Horner in ``j`` over the ``BiPoly`` blocks, each itself evaluated by Horner
        in ``k`` over its ``Poly``-in-``n`` (evaluated by Horner in ``n``). The zero
        polynomial evaluates to ``Q(0)``."""
        qn = _to_q(n)
        qj = _to_q(j)
        qk = _to_q(k)
        if qn is None or qj is None or qk is None:
            raise TypeError(
                f"TriPoly.eval: n, j, k must be exact-rational; got {n!r}, {j!r}, {k!r}")
        if self.is_zero:
            return _Q_ZERO
        # Horner in j: acc = acc*j + block.eval_nk(n, k).
        acc = _Q_ZERO
        for bib in reversed(self._b):
            acc = acc * qj + _bipoly_eval(bib, qn, qk)
        return acc

    # ── shift operators (var → var + s) ──────────────────────────────────────
    def shift_n(self, s: int) -> "TriPoly":
        """``TriPoly(n, j, k) → TriPoly(n+s, j, k)`` — shift the free variable
        ``n`` by ``+s`` in every ``(j,k)`` coefficient (the ``BiPoly.shift_n``
        dispersion). ``s`` is an int. Builds the ``F(n+s, j, k)`` ladder a
        recurrence-finder needs."""
        if not isinstance(s, int):
            raise TypeError("TriPoly.shift_n: s must be an int")
        if s == 0 or self.is_zero:
            return self
        return TriPoly._wrap(_tri_trim([b.shift_n(s) for b in self._b]))

    def shift_k(self, s: int) -> "TriPoly":
        """``TriPoly(n, j, k) → TriPoly(n, j, k+s)`` — substitute ``k → k+s`` in
        every ``j``-block (the ``BiPoly.shift_k`` substitution). ``s`` is an int."""
        if not isinstance(s, int):
            raise TypeError("TriPoly.shift_k: s must be an int")
        if s == 0 or self.is_zero:
            return self
        return TriPoly._wrap(_tri_trim([b.shift_k(s) for b in self._b]))

    def shift_j(self, s: int) -> "TriPoly":
        """``TriPoly(n, j, k) → TriPoly(n, j+s, k)`` — substitute ``j → j+s`` by
        exact synthetic Horner on the linear ``(j + s)`` over the ``BiPoly`` blocks
        (mirrors ``Poly.shift`` / ``BiPoly.shift_k`` one level up). ``s`` is an
        int."""
        if not isinstance(s, int):
            raise TypeError("TriPoly.shift_j: s must be an int")
        if s == 0 or self.is_zero:
            return self
        # synthetic Horner over the linear (j + s): acc = acc*(j+s) + block.
        # (j + s) as a TriPoly: j**1 + s·j**0.
        js = TriPoly._wrap((TriPoly._scalar_bipoly(Q(s, 1)), BiPoly.one()))
        acc = TriPoly._wrap(())
        for bib in reversed(self._b):
            acc = acc._mul_tri(js) + TriPoly.from_bipoly(bib)
        return acc

    @staticmethod
    def _scalar_bipoly(q: Q) -> BiPoly:
        """The constant ``BiPoly`` carrying the exact scalar ``q`` (zero → the zero
        BiPoly)."""
        return BiPoly.zero() if q == 0 else BiPoly.from_n_poly(Poly.from_coeffs([q]))

    # ── difference operators (the Apagodu–Zeilberger payload) ────────────────
    def delta_j(self) -> "TriPoly":
        """The forward difference in ``j``: ``Δ_j f = f(n, j+1, k) − f(n, j, k)``
        (``= shift_j(1) − self``). The ``j``-summation telescoping operator: a
        joint certificate ``G_j`` satisfies ``Σ_{j=0}^{m} Δ_j G_j = G_j(…, m+1, …)
        − G_j(…, 0, …)``, so a creative-telescoping identity writes its ``j``-half
        of the right-hand side as ``delta_j`` of the certificate."""
        return self.shift_j(1) - self

    def delta_k(self) -> "TriPoly":
        """The forward difference in ``k``: ``Δ_k f = f(n, j, k+1) − f(n, j, k)``
        (``= shift_k(1) − self``). The ``k``-summation telescoping operator (the
        ``k``-half partner of :meth:`delta_j`)."""
        return self.shift_k(1) - self

    # ── the boundary collapse — the ONE rotation (ALU → FPU) ─────────────────
    def to_floats(self):
        """Collapse to a nested ``[[[float, …]_n]_k]_j`` list — the single ALU→FPU
        rotation / "rotation last" (the body stayed exact ``Q`` until here). This
        is the ONLY place ``float()`` appears in the carrier, the exact analogue of
        :meth:`srmech.amsc.poly.Poly.to_floats` / :meth:`srmech.amsc.qmat.QMat.to_mat`
        — the opt-in display boundary. The zero polynomial returns an empty list."""
        out = []
        for bib in self._b:
            kgrid = []
            for kp in bib.terms:
                kgrid.append([float(c) for c in kp.coeffs])
            out.append(kgrid)
        return out


# ── exact BiPoly evaluation (Horner in k over Poly-in-n, then Horner in n) ─────
def _bipoly_eval(bib: BiPoly, qn: Q, qk: Q) -> Q:
    """Evaluate a :class:`~srmech.amsc.zeilberger.BiPoly` at ``(n, k) = (qn, qk)``
    by exact Horner in ``k`` over its ``Poly``-in-``n`` coefficients (each evaluated
    by exact Horner in ``n``). Exact ``Q``; the zero ``BiPoly`` → ``Q(0)``. Kept
    module-level (BiPoly carries no scalar (n,k)-eval of its own)."""
    if bib.is_zero:
        return _Q_ZERO
    acc = _Q_ZERO
    for kp in reversed(bib.terms):
        acc = acc * qk + kp.eval(qn)
    return acc


# ── exact-rational coercion (mirrors poly._to_q) ──────────────────────────────
def _to_q(value):
    """Coerce ``value`` to an exact :class:`~srmech.amsc.q.Q`, or ``None`` if it is
    not an exact-rational-coercible scalar (mirrors ``poly._to_q``). A ``float`` is
    REJECTED (returns ``None``) — a ``TriPoly`` coefficient must be exact."""
    if isinstance(value, Q):
        return value
    if isinstance(value, bool):
        return Q(int(value), 1)
    if isinstance(value, int):
        return Q(value, 1)
    from fractions import Fraction
    if isinstance(value, Fraction):
        return Q(value.numerator, value.denominator)
    if isinstance(value, float):
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


# ── the PROSE-SIDE constructor (rc116; #1248 / F1038; the ORPHAN FIX) ──────────
def tripoly_from_coeffs(coeffs) -> "TriPoly":
    """Build the exact-``ℚ[n,j,k]`` trivariate carrier :class:`TriPoly` from a
    ``j``-ascending list of ``k``-ascending lists of INTEGER-LEAF
    ``n``-coefficient lists — the PROSE-SIDE constructor ToolEntry (rc116;
    issue #1248 / F1038). ``coeffs[dj]`` is the ``j**dj`` block (a
    :class:`~srmech.amsc.zeilberger.BiPoly` in ``(n,k)``); ``coeffs[dj][dk]``
    is that block's ``k**dk`` coefficient, an ascending-``n``-degree integer
    list (a :class:`~srmech.amsc.poly.Poly` in ``n``). So
    ``tripoly_from_coeffs([[[0, 1]], [[1]]])`` is ``n + j`` (``j**0`` block =
    the BiPoly ``n``, ``j**1`` block = the BiPoly ``1``) — the multivariate
    "sums-of-sums" term-ratio building blocks the ``apagodu_zeilberger`` op
    consumes.

    Why it exists: the ``tool_schema`` producer/consumer census (#1248) found
    ``TriPoly`` an ORPHAN — CONSUMED by ``apagodu_zeilberger`` but never
    PRODUCED from the registry, so the double-sum row could not be built by
    prose. This closes that gap (the ``bipoly_from_coeffs`` grammar recursed
    exactly one level — each ``j``-block follows the
    :func:`srmech.amsc.zeilberger.bipoly_from_coeffs` cell grammar). A
    **non_compute BUILDER** (the ``coupling.from_bodies`` /
    ``text.cooccurrence_edges`` precedent): it constructs an operand; every
    computation lives in the ops that consume it.

    Ints only (a ``bool`` / ``float`` / ``str`` leaf is an honest
    ``TypeError`` — the exact-``ℚ`` prose discipline; integers are exact). No
    float, no ``abs()``, no numpy / ``math``."""
    from .poly import _prose_int
    if isinstance(coeffs, tuple):
        coeffs = list(coeffs)
    if not isinstance(coeffs, list):
        raise TypeError(
            "tripoly_from_coeffs: coeffs must be a j-ascending list of "
            f"j-blocks (each a k-ascending list of n-lists); got "
            f"{type(coeffs).__name__}")
    blocks: List[BiPoly] = []
    for dj, jblock in enumerate(coeffs):
        if isinstance(jblock, tuple):
            jblock = list(jblock)
        if not isinstance(jblock, list):
            raise TypeError(
                f"tripoly_from_coeffs: j-block {dj} must be a k-ascending list "
                f"of ascending-n integer lists (the BiPoly in (n,k) of j**{dj}); "
                f"got {type(jblock).__name__}")
        k_terms: List[Poly] = []
        for dk, kcell in enumerate(jblock):
            if isinstance(kcell, tuple):
                kcell = list(kcell)
            if not isinstance(kcell, list):
                raise TypeError(
                    f"tripoly_from_coeffs: (j-block {dj}, k-cell {dk}) must be an "
                    f"ascending-n list of ints (the Poly-in-n coefficient of "
                    f"j**{dj}·k**{dk}); got {type(kcell).__name__}")
            k_terms.append(Poly.from_coeffs(
                [_prose_int(v, where=f"tripoly_from_coeffs (j-block {dj}, k-cell {dk})")
                 for v in kcell]))
        blocks.append(BiPoly(k_terms))
    return TriPoly(blocks)
