"""srmech.amsc.riemann_theta — ``RiemannTheta``, the FIRST RUNG of the GENUS axis.

THE NEW AXIS
============

The operand carrier ladder so far is graded by a SINGLE elliptic torus: the
elliptic / theta carriers (:class:`~srmech.amsc.ellbase.EllRatio`,
:class:`~srmech.amsc.thetasum.ThetaSum`, :class:`~srmech.amsc.unary_theta.UnaryTheta`)
all live on a genus-1 curve (one period τ, the upper-half-plane ``H₁``). That is a
real ceiling: a genus-2 abelian variety — the Jacobian of a genus-2 curve — carries
a theta function of TWO complex variables over a 2×2 Riemann matrix ``Ω ∈ H₂`` (the
Siegel upper half space), and NO genus-1 carrier can hold it (the cross-period
``Ω₁₂`` coupling has no genus-1 representative). ``RiemannTheta`` augments the ladder
with a **genus axis** and makes the genus-2 Riemann theta-constant a finite exact
object in-carrier — the first rung of the new axis.

THE OBJECT
==========

The genus-2 Riemann theta function with a binary characteristic ``[ε'; ε]`` is

    θ[ε'; ε](z | Ω) = Σ_{n ∈ ℤ²} exp{ iπ (n+½ε')ᵀ Ω (n+½ε')
                                       + 2πi (z + ½ε)ᵀ (n + ½ε') }

(Grushevsky, "The Schottky Problem", arXiv:1009.0369, eq. (1), the Riemann theta
on the Siegel space ``H_g``; Eilers, "Rosenhain–Thomae Formulae for Higher Genera
Hyperelliptic Curves", arXiv:1707.08855, eq. (1.2), the genus-2 theta-constant with
the binary characteristic ``[ε'₁ε'₂; ε₁ε₂]``, entries ``∈ {0,1}``). For genus 2
there are 16 characteristics — **10 even + 6 odd** (Eilers p. 2); a characteristic
is even iff ``ε'·ε ≡ 0 (mod 2)``.

EXACT NOME-LATTICE REPRESENTATION (no float on the decision path)
================================================================

The carrier represents the theta-CONSTANT (``z = 0``) as an EXACT INTEGER exponent
lattice over the nome alphabet

    q₁ = e^{iπ Ω₁₁}, q₂ = e^{iπ Ω₂₂}, q₁₂ = e^{2iπ Ω₁₂} ,

cleared to integer exponents in the QUARTER-nome base ``Q₁ = q₁^{1/4}``,
``Q₂ = q₂^{1/4}``, ``Q₁₂ = q₁₂^{1/4} = e^{iπ Ω₁₂/2}``. With ``mᵢ = nᵢ + ½ε'ᵢ`` the
quadratic form ``mᵀΩm`` over ``iπ`` expands as ``m₁²Ω₁₁ + 2m₁m₂Ω₁₂ + m₂²Ω₂₂``, and
clearing the half-integers (``ε'ᵢ ∈ {0,1}``) gives a term

    Q₁^A · Q₂^B · Q₁₂^C · (−1)^{ε₁n₁ + ε₂n₂}

with EXACT INTEGER exponents

    A = 4n₁² + 4n₁ε'₁ + ε'₁²
    B = 4n₂² + 4n₂ε'₂ + ε'₂²
    C = 4n₁n₂ + 2n₁ε'₂ + 2n₂ε'₁ + ε'₁ε'₂          ← THE CROSS-TERM (denominator 4)

THE CROSS-TERM ``C`` is the genuinely new, hardest part: ``m₁m₂`` is a PRODUCT of
two half-integers, so it carries a denominator 4 in the cleared integer lattice (the
genus-1 carrier never saw this coupling — there is no ``n₁n₂`` cross-period in genus
1). The lower characteristic ``ε`` contributes a per-term SIGN ``(−1)^{ε·n}`` — the
**Class-K** pin-slot via an explicit ``±1`` branch, never an ALU ``abs()`` (the
common constant phase ``i^{ε·ε'}`` is the same for every term and factors out; for
an even characteristic ``ε·ε' ≡ 0`` so it is a real ``±1`` and is suppressed in the
constant). Each lattice coefficient is an exact INTEGER (a sum of ``±1`` lattice
counts), so the carrier is exact-integer all the way (no float, no ``math``, no
numpy). The lattice is truncated to a box ``|nᵢ| ≤ box`` — the finite generating
rule; the box is pinned by the requested truncation degree (a wrong box makes the
gates fail loudly, never silently — the gate compares ONLY the safe inner region the
box provably resolves).

THE BUILD GATES
===============

  * **collapse (primary):** :meth:`collapse_g1` of the trivial even characteristic
    ``[0,0; 0,0]`` equals the rc70 genus-1 Jacobi theta ``θ₃`` EXACTLY — bit-exact
    vs the existing rung (set ``n₂ = 0``, ``Ω₁₂ = Ω₂₂ = 0`` ⇒ ``q₂ = q₁₂ = 1`` and
    only the ``q₁`` slice survives: ``Σ_{n₁} q₁^{n₁²}`` = θ₃). THE foundation gate.

  * **formal genus-2 theta-null identity (secondary):** the genus-g Gauss /
    duplication identity

        θ[0; 0](0 | Ω)²  =  Σ_{c ∈ (½ℤ²/ℤ²)} θ[c; 0](0 | 2Ω)²

    (the ``z = w = 0``, ``a = b = 0`` specialization of the generalized Riemann theta
    identity — Chai, "Riemann's theta formula" (2014), Thm 1.2 example (b); classically
    Mumford, *Tata Lectures on Theta I* (1983), the genus-g duplication). It holds for
    ALL ``Ω`` — exactly checkable as a truncated exact-integer multivariate q-series,
    NO transcendental evaluation. The four ``θ[c; 0]`` (``c ∈ {0,½}²``) are all even
    theta-nulls, and the sum genuinely exercises the cross-term ``q₁₂`` (the (½,½)
    and mixed characteristics have ``C ≠ 0``), so it proves the carrier computes
    genuine genus-2 theta-constants, not just the genus-1 slice. See
    :meth:`duplication_lhs` / :meth:`duplication_rhs` / :meth:`duplication_holds`.

THE REPRESENTABILITY BOUNDARY (the named operand-side OPEN)
==========================================================

The carrier is REPRESENTABLE (a finite exact decision): the canonical nome-monomial
form + the finite Riemann relations, box pinned by the polarization level. The
genus-axis OPEN is the **SCHOTTKY PROBLEM** — which ``Ω ∈ H_g`` are Jacobians of
curves (``dim M_g = 3g−3`` vs ``dim A_g = g(g+1)/2``; they coincide for ``g ≤ 3``,
so the Jacobian locus is everything for ``g ≤ 3``; ``g = 4`` is the first non-trivial
case, solved by Schottky; ``g ≥ 5`` is genuinely open — Grushevsky, arXiv:1009.0369,
p. 5 + Open Problem 1, p. 6). **Genus 2 is CLEAN** (no Schottky obstruction:
``dim M_2 = 3 = dim A_2``), which is exactly why it is the first representable rung.
This is the operand-side OPEN this carrier names — the dual of an operator-side
honest ``None`` (the F929 operand program: enlarge the carrier to turn a former
irrepresentable into a finite exact reduction).

HYPERELLIPTIC / THOMAE (the MOTIVATION + the rc74 target — NOT this rung's gate)
==============================================================================

A genus-2 Jacobian carries this Riemann theta, and Thomae's formula (Eilers eq.
(2.30) / Cor. 2.4) is the geometric bridge from the even theta-nulls to the branch
points of the hyperelliptic curve ``y² = x(x−1)(x−a₁)(x−a₂)(x−a₃)``. That is the
MOTIVATION and the rc74 target. It is NOT an exact gate here: verifying Thomae
requires evaluating theta-constants at a curve's transcendental PERIOD MATRIX ``Ω``
(only checkable to ``N`` digits = float on the decision path), which the discipline
forbids. rc74 handles it via the FORMAL Rosenhain/Göpel algebraic relations among
the theta-nulls + a DOCUMENTED (not numerically-evaluated) transcendental λ-map.

THE C PEER
==========

The C peer ``srmech_riemann_theta`` (``c/src/srmech_riemann_theta.c``) mirrors the
genuinely-new computation — the EXACT INTEGER ``(A, B, C)`` exponent lattice with
the cross-term denominator-4 clearing + the per-term Class-K sign — over a caller
arena (malloc-free, JPL-clean). The theta-constant coefficients are small integers
(``±1`` lattice counts), so the lattice rides ``int64`` triples + an ``int64``
coefficient (no bignum needed for a genus-2 theta-CONSTANT). The pure-Python body
here is the COMPLETE alternative + the C peer's parity oracle — both emit the
byte-identical exact integer lattice.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from .q import Q
from .unary_theta import UnaryTheta, unary_theta

__all__ = ["RiemannTheta"]

# the (A, B, C) integer exponent triple in the quarter-nome base
_Triple = Tuple[int, int, int]


def _native():
    """The native ``_native`` module IF the rc72 ``srmech_riemann_theta`` peer is
    present and bound, else ``None`` — so the carrier dispatches the exact-integer
    ``(A, B, C)`` lattice to C when available and falls cleanly to the pure-Python
    body (the complete alternative + the parity oracle). Imported lazily to avoid a
    bootstrap cycle."""
    try:
        from . import _native as nat
    except ImportError:
        return None
    probe = getattr(nat, "has_native_riemann_theta", None)
    return nat if (probe is not None and probe()) else None


def _bit(name: str, v: int) -> int:
    """Coerce a characteristic entry to a bit ``∈ {0, 1}`` (a half-integer
    characteristic ``½ε`` with ``ε ∈ {0, 1}``); reject anything else loudly."""
    iv = int(v)
    if iv not in (0, 1):
        raise ValueError(
            f"characteristic entry {name} must be 0 or 1 (the doubled half-integer "
            f"½ε with ε ∈ {{0,1}}); got {v!r}")
    return iv


class RiemannTheta:
    """A numpy-free EXACT genus-2 Riemann theta-CONSTANT

        θ[ε'; ε](0 | Ω) = Σ_{n ∈ ℤ²} (−1)^{ε·n} · Q₁^A Q₂^B Q₁₂^C ,
        A = 4n₁²+4n₁ε'₁+ε'₁², B = 4n₂²+4n₂ε'₂+ε'₂²,
        C = 4n₁n₂+2n₁ε'₂+2n₂ε'₁+ε'₁ε'₂      (the cross-term, denominator 4)

    — the FIRST RUNG of the GENUS axis (genus 2). Immutable. Holds the binary
    characteristic ``[ε'; ε]`` (four bits in ``{0,1}``; the doubled half-integer
    characteristic). The exact integer exponent lattice (:meth:`lattice`) is the
    carrier's representable core; see the module docstring for the collapse / formal
    theta-null build gates and the Schottky-problem operand-side OPEN.

    Construct via :meth:`theta_constant` (the public entry) or the named even
    even-characteristic helpers. ``box`` (the lattice-box truncation ``|nᵢ| ≤ box``)
    is the finite generating rule, pinned by the requested truncation degree."""

    __slots__ = ("_ep1", "_ep2", "_e1", "_e2")

    def __init__(self, ep1: int, ep2: int, e1: int, e2: int) -> None:
        self._ep1 = _bit("ε'₁", ep1)
        self._ep2 = _bit("ε'₂", ep2)
        self._e1 = _bit("ε₁", e1)
        self._e2 = _bit("ε₂", e2)

    # ── construction ──────────────────────────────────────────────────────────
    @classmethod
    def theta_constant(cls, eps_prime: Tuple[int, int],
                       eps: Tuple[int, int]) -> "RiemannTheta":
        """The genus-2 theta-constant ``θ[ε'; ε](0 | Ω)`` for a binary characteristic
        ``[ε'; ε]`` — ``eps_prime = (ε'₁, ε'₂)`` (the upper / lattice-shift half-integer
        characteristic) and ``eps = (ε₁, ε₂)`` (the lower / sign characteristic), each
        entry in ``{0, 1}``. The trivial even characteristic is
        ``theta_constant((0,0), (0,0))`` (= θ[0;0], the one that collapses to θ₃)."""
        return cls(eps_prime[0], eps_prime[1], eps[0], eps[1])

    @classmethod
    def even_characteristics(cls) -> "List[RiemannTheta]":
        """The 10 EVEN genus-2 theta-constants (the even theta-nulls): all 16 binary
        characteristics ``[ε'; ε]`` with ``ε'·ε ≡ 0 (mod 2)`` (Eilers p. 2: 10 even,
        6 odd). The order is deterministic (lexicographic in ``ε'₁ε'₂ε₁ε₂``)."""
        out: List[RiemannTheta] = []
        for ep1 in (0, 1):
            for ep2 in (0, 1):
                for e1 in (0, 1):
                    for e2 in (0, 1):
                        if (ep1 * e1 + ep2 * e2) % 2 == 0:   # even characteristic
                            out.append(cls(ep1, ep2, e1, e2))
        return out

    # ── accessors ─────────────────────────────────────────────────────────────
    @property
    def characteristic(self) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """The binary characteristic ``((ε'₁, ε'₂), (ε₁, ε₂))``."""
        return ((self._ep1, self._ep2), (self._e1, self._e2))

    @property
    def is_even(self) -> bool:
        """True iff the characteristic is EVEN (``ε'·ε ≡ 0 mod 2``) — i.e. an even
        theta-null (a non-vanishing theta-constant). 10 of the 16 are even."""
        return (self._ep1 * self._e1 + self._ep2 * self._e2) % 2 == 0

    @property
    def genus(self) -> int:
        """The genus — 2 for this carrier (the first rung of the genus axis)."""
        return 2

    # ── the exact integer exponent lattice (the representable core) ────────────
    def lattice(self, box: int) -> "Dict[_Triple, int]":
        """The EXACT INTEGER exponent lattice ``{(A, B, C): coeff}`` of the
        theta-constant, truncated to the box ``|nᵢ| ≤ box`` — the carrier's
        representable core. ``(A, B, C)`` are the integer exponents in the quarter-nome
        base ``(Q₁, Q₂, Q₁₂)`` (see the module docstring), ``coeff`` is the exact
        integer ``Σ (−1)^{ε·n}`` over the ``n`` landing on that monomial. The
        cross-term ``C`` carries the denominator-4 clearing (``m₁m₂`` is a product of
        half-integers). DISPATCHES to the native ``srmech_riemann_theta`` C peer when
        loaded (a 1:1 exact-integer mirror — the C lattice EQUALS the Python lattice,
        trusted only on a native hit); else the pure-Python :meth:`_lattice_py` body
        (the COMPLETE alternative + the parity oracle). No float, no ``abs()`` (the
        ``(−1)^{ε·n}`` sign is the Class-K pin-slot), no numpy / ``math``."""
        if not isinstance(box, int) or box < 0:
            raise ValueError(f"box must be a non-negative int; got {box!r}")
        nat = _native()
        if nat is not None:
            try:
                got = nat.riemann_theta_lattice_c(
                    self._ep1, self._ep2, self._e1, self._e2, box)
                if got is not None:
                    return got
            except (RuntimeError, OverflowError, ValueError):
                pass   # fall to the pure path
        return self._lattice_py(box)

    def _lattice_py(self, box: int) -> "Dict[_Triple, int]":
        """The COMPLETE pure-Python exponent lattice (the parity oracle for the C
        peer): exact integer ``(A, B, C) → coeff`` over the box ``|nᵢ| ≤ box``. The
        cross-term ``C = 4n₁n₂ + 2n₁ε'₂ + 2n₂ε'₁ + ε'₁ε'₂`` is the genus-2
        denominator-4 clearing; the sign ``(−1)^{ε·n}`` is the Class-K pin-slot (an
        explicit ``+1/−1`` branch, never an ALU ``abs()``). A bounded double loop over
        the box (JPL Rule 2)."""
        ep1, ep2, e1, e2 = self._ep1, self._ep2, self._e1, self._e2
        out: Dict[_Triple, int] = {}
        for n1 in range(-box, box + 1):
            for n2 in range(-box, box + 1):
                a = 4 * n1 * n1 + 4 * n1 * ep1 + ep1 * ep1
                b = 4 * n2 * n2 + 4 * n2 * ep2 + ep2 * ep2
                c = 4 * n1 * n2 + 2 * n1 * ep2 + 2 * n2 * ep1 + ep1 * ep2
                # the per-term sign (−1)^{ε₁n₁+ε₂n₂}: Class-K pin-slot (a stored ±1)
                parity = (e1 * n1 + e2 * n2) % 2
                sign = 1 if parity == 0 else -1      # never abs(); explicit ± branch
                key = (a, b, c)
                out[key] = out.get(key, 0) + sign
        return {k: v for k, v in out.items() if v != 0}

    # ── the genus-1 collapse (the foundation gate) ────────────────────────────
    def collapse_g1(self) -> UnaryTheta:
        """The genus-1 COLLAPSE: set ``Ω₁₂ = Ω₂₂ = 0`` (⇒ ``q₂ = q₁₂ = 1``) and
        ``n₂ = 0`` (drop the second lattice direction). For the trivial even
        characteristic ``[0,0; 0,0]`` the surviving slice is
        ``Σ_{n₁ ∈ ℤ} q₁^{n₁²}`` = the genus-1 Jacobi theta ``θ₃`` — returned as the
        rc70 :class:`~srmech.amsc.unary_theta.UnaryTheta`
        ``unary_theta('trivial', j=0, a=1, b=0, D=1, support='all')`` (so the collapse
        is BIT-EXACT vs the existing rung; see the build gate). Only the trivial even
        characteristic ``[0,0; 0,0]`` collapses to ``θ₃``; any other characteristic
        is rejected (its genus-1 slice is a SHIFTED / signed theta that is not the
        plain ``θ₃`` rung — an honest boundary, not a fabricated reduction)."""
        if (self._ep1, self._ep2, self._e1, self._e2) != (0, 0, 0, 0):
            raise ValueError(
                "collapse_g1 is the θ₃ foundation gate: only the trivial even "
                "characteristic [0,0; 0,0] collapses to the rc70 θ₃ rung. The "
                f"characteristic {self.characteristic} has a non-trivial genus-1 "
                "slice (a shifted/signed theta), not the plain θ₃ — an honest "
                "boundary, not a fabricated reduction.")
        # θ₃ = Σ_{n∈ℤ} q^{n²}: the rc70 UnaryTheta (trivial χ, j=0, exp n²/1, all-n)
        return unary_theta("trivial", 0, 1, 0, 1, support="all")

    def collapse_g1_q_series(self, N: int) -> "List[int]":
        """The genus-1 collapse's exact INTEGER q-series to order ``N`` (in the ``q₁``
        nome, NOT the quarter-nome ``Q₁``): ``[1, 2, 0, 0, 2, …]`` = ``Σ q₁^{n₁²}`` for
        the trivial characteristic. Equals :meth:`collapse_g1`.q_series exactly — the
        bit-exact bridge to the rc70 θ₃ rung."""
        return self.collapse_g1().q_series(N)

    # ── equality / repr ───────────────────────────────────────────────────────
    def __eq__(self, other) -> bool:
        if isinstance(other, RiemannTheta):
            return ((self._ep1, self._ep2, self._e1, self._e2)
                    == (other._ep1, other._ep2, other._e1, other._e2))
        return NotImplemented

    def __ne__(self, other):
        r = self.__eq__(other)
        return r if r is NotImplemented else (not r)

    def __hash__(self) -> int:
        return hash((self._ep1, self._ep2, self._e1, self._e2))

    def __repr__(self) -> str:
        return (f"RiemannTheta(genus=2, eps_prime=({self._ep1},{self._ep2}), "
                f"eps=({self._e1},{self._e2}), even={self.is_even})")

    # ── the formal genus-2 theta-null identity gate (Gauss duplication) ────────
    @staticmethod
    def _square_lattice(lat: "Dict[_Triple, int]") -> "Dict[_Triple, int]":
        """The exact-integer square ``lat · lat`` of an ``(A, B, C) → coeff`` lattice
        (a bounded convolution over the exponent triples; JPL Rule 2). All-integer, no
        float."""
        out: Dict[_Triple, int] = {}
        items = list(lat.items())
        for (a1, b1, c1), v1 in items:
            for (a2, b2, c2), v2 in items:
                key = (a1 + a2, b1 + b2, c1 + c2)
                out[key] = out.get(key, 0) + v1 * v2
        return {k: v for k, v in out.items() if v != 0}

    @staticmethod
    def _double_exps(lat: "Dict[_Triple, int]") -> "Dict[_Triple, int]":
        """Re-express a lattice computed at ``2Ω`` in the ``Ω``-nome alphabet: every
        quarter-nome exponent DOUBLES (``Q₁(2Ω) = Q₁(Ω)²``), so ``(A, B, C) ↦
        (2A, 2B, 2C)``. Exact integer relabel, no float."""
        return {(2 * a, 2 * b, 2 * c): v for (a, b, c), v in lat.items()}

    @classmethod
    def duplication_lhs(cls, box: int) -> "Dict[_Triple, int]":
        """The LEFT side of the genus-2 Gauss/duplication theta-null identity
        ``θ[0; 0](0 | Ω)²`` (in the ``Ω`` quarter-nome alphabet) — the exact-integer
        square of the trivial even theta-constant's lattice. See :meth:`duplication_holds`."""
        t00 = cls.theta_constant((0, 0), (0, 0)).lattice(box)
        return cls._square_lattice(t00)

    @classmethod
    def duplication_rhs(cls, box: int) -> "Dict[_Triple, int]":
        """The RIGHT side of the genus-2 Gauss/duplication theta-null identity
        ``Σ_{c ∈ (½ℤ²/ℤ²)} θ[c; 0](0 | 2Ω)²`` (re-expressed in the ``Ω`` quarter-nome
        alphabet via :meth:`_double_exps`, since each summand is at ``2Ω``). The four
        ``c`` are the half-characteristics ``{(0,0),(1,0),(0,1),(1,1)}`` (upper char
        ``c``, lower char ``0`` — all even). See :meth:`duplication_holds`."""
        rhs: Dict[_Triple, int] = {}
        for c1 in (0, 1):
            for c2 in (0, 1):
                tc = cls.theta_constant((c1, c2), (0, 0)).lattice(box)
                tc2 = cls._double_exps(tc)         # the summand is at 2Ω
                sq = cls._square_lattice(tc2)
                for k, v in sq.items():
                    rhs[k] = rhs.get(k, 0) + v
        return {k: v for k, v in rhs.items() if v != 0}

    @classmethod
    def duplication_holds(cls, box: int = 8) -> bool:
        """The FORMAL genus-2 theta-null identity gate (the secondary build gate): the
        genus-g Gauss / duplication identity

            θ[0; 0](0 | Ω)²  =  Σ_{c ∈ (½ℤ²/ℤ²)} θ[c; 0](0 | 2Ω)²

        holds EXACTLY as a truncated exact-integer multivariate q-series, for ALL ``Ω``
        (no transcendental evaluation). The ``z = w = 0``, ``a = b = 0`` specialization of
        the generalized Riemann theta identity (Chai, "Riemann's theta formula" (2014),
        Thm 1.2 example (b); classically Mumford, *Tata Lectures on Theta I* (1983), the
        genus-g duplication). This compares the two sides on the SAFE INNER REGION the box
        ``|nᵢ| ≤ box`` provably resolves (a box-``box`` theta omits only terms with a
        quarter-nome exponent ``≥ 4(box+1)²``, so monomials with ``A, B, |C| ≤ 4·box²`` are
        fully accumulated). Because the four ``θ[c; 0]`` include the (½,½) and mixed
        characteristics with ``C ≠ 0``, the identity genuinely exercises the cross-term
        ``q₁₂`` — it proves the carrier computes genuine genus-2 theta-constants, not just
        the genus-1 slice. Returns ``True`` iff the two sides agree exactly on the safe
        region (and the region is non-trivially populated with cross-term monomials).

        A CARRIER METHOD (the carrier's own build gate), not a public module-level op —
        ``tools.total`` is unchanged (matches the rc69/70/71 carrier precedent, whose
        identity / verification checks are carrier methods, not registered ops)."""
        if not isinstance(box, int) or box < 2:
            raise ValueError(
                f"box must be an int ≥ 2 for the duplication gate; got {box!r}")
        lhs = cls.duplication_lhs(box)
        rhs = cls.duplication_rhs(box)
        safe = 4 * box * box
        babs = safe                                # |C| bound (Class-K magnitude)

        def restrict(lat: "Dict[_Triple, int]") -> "Dict[_Triple, int]":
            kept: Dict[_Triple, int] = {}
            for (a, b, c), v in lat.items():
                cmag = c if c >= 0 else -c         # Class-K magnitude, no abs()
                if a <= safe and b <= safe and cmag <= babs:
                    kept[(a, b, c)] = v
            return kept

        lhs_s = restrict(lhs)
        rhs_s = restrict(rhs)
        if lhs_s != rhs_s:
            return False
        # the gate must genuinely touch the cross-term (else only the genus-1 slice)
        has_cross = any(c != 0 for (_a, _b, c) in lhs_s)
        return has_cross
