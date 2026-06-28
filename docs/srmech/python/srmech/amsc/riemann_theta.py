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

THE rc73 EXTENSIONS — the SECOND GENUS RUNG (transformation + addition)
=====================================================================

rc73 adds the two structures that turn the genus-2 theta-constant from an isolated
object into a carrier with a *group action* and a *genuine two-argument identity*:

  * **(A) the Sp(4, ℤ) TRANSFORMATION** (:meth:`transform`, :meth:`sp4_translation`
    / :meth:`sp4_gl_twist` / :meth:`sp4_inversion`). The genus-2 modular group
    ``Sp(2g, ℤ) = Sp(4, ℤ)`` acts on the binary characteristic ``m = [ε'; ε]`` by an
    EXACT affine-linear map (integer / mod-2 arithmetic — DLMF §21.5, eq. 21.5.9;
    Igusa, *Theta Functions* (1972) §V.1):

        ε' ↦ D·ε' − C·ε + diag(C·Dᵀ)        (mod 2 for the bit)
        ε  ↦ −B·ε' + A·ε + diag(A·Bᵀ)

    The parity (even ⇄ even, odd ⇄ odd) is PRESERVED (the action factors through
    ``Sp(4, ℤ₂)`` — Bruinier et al., *The 1-2-3 of Modular Forms*; the level-2 theory).
    The theta-constant picks up an 8th-root-of-unity multiplier ``κ(γ)`` (``ζ₈^k``,
    ``ε⁸ = 1``) carried as the EXACT integer exponent ``k ∈ ℤ/8`` from the Igusa
    phase ``φ_m(γ)`` (a rational with denominator dividing 8 → ``8·φ_m ∈ ℤ``, EXACT
    on the decision path). The TRANSCENDENTAL automorphy factor ``det(CΩ+D)^{1/2}``
    is NEVER evaluated — it is carried SYMBOLICALLY (:meth:`automorphy_factor`), off
    every gate, exactly as the rc72 review demanded.

  * **(B) the ADDITION relation** (:meth:`addition_holds`) — the GENUINE two-argument
    genus-2 theta addition theorem (DLMF §21.6, eq. 21.6.8, the ``z₁ = z₂ = 0``,
    two-independent-characteristic specialization), a within-carrier EXACT identity
    GENUINELY DISTINCT from rc72's duplication. Where duplication squares a SINGLE
    even theta-null (``θ[0;0]² = Σ_c θ[c;0](2Ω)²``), the addition relation is the
    BILINEAR product of TWO DIFFERENT theta-nulls

        θ[a; 0](0|Ω) · θ[b; 0](0|Ω)
          = Σ_{r ∈ (ℤ/2)²} θ[(2r+a+b)/2; 0](0|2Ω) · θ[(2r+a−b)/2; 0](0|2Ω) ,

    which duplication alone cannot produce (it never holds a product of two
    *distinct* nulls). The right side carries DIFFERENT characteristics
    ``2r+a+b`` vs ``2r+a−b`` per summand — the genuinely-new content; only the
    degenerate ``a = b`` collapse recovers duplication. It holds for ALL ``Ω`` (a
    FORMAL identity) → exactly checkable as a truncated exact-integer multivariate
    q-series (no transcendental evaluation, no float, no tolerance). See
    :meth:`addition_lhs` / :meth:`addition_rhs` / :meth:`addition_holds` and the
    constructive sum/difference (``M = m+m'``, ``M' = m−m'``) re-indexing proof in
    the method docstrings; the common alphabet is the EIGHTH-nome
    ``Q₈ = q^{1/8}`` (so theta at Ω AND theta at 2Ω clear to ONE integer lattice).

THE C PEER
==========

The C peer ``srmech_riemann_theta`` (``c/src/srmech_riemann_theta.c``) mirrors the
genuinely-new computation — the EXACT INTEGER ``(A, B, C)`` exponent lattice with
the cross-term denominator-4 clearing + the per-term Class-K sign — over a caller
arena (malloc-free, JPL-clean). The theta-constant coefficients are small integers
(``±1`` lattice counts), so the lattice rides ``int64`` triples + an ``int64``
coefficient (no bignum needed for a genus-2 theta-CONSTANT). The pure-Python body
here is the COMPLETE alternative + the C peer's parity oracle — both emit the
byte-identical exact integer lattice. rc73 adds two mirrored peers:
``srmech_riemann_theta_sp4_char`` (the EXACT integer characteristic transformation
+ the κ exponent) and ``srmech_riemann_theta_eighth_lattice`` (the EIGHTH-nome
lattice at Ω or 2Ω that the addition gate convolves) — both caller-arena, int64,
JPL-clean; the Python bodies are their complete alternatives + parity oracles.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from .q import Q
from .unary_theta import UnaryTheta, unary_theta

__all__ = ["RiemannTheta", "RiemannThetaG3"]

# the (A, B, C) integer exponent triple in the quarter-nome base
_Triple = Tuple[int, int, int]

# the genus-3 (A₁, A₂, A₃, C₁₂, C₁₃, C₂₃) integer exponent SEXTUPLE — 3 diagonal
# nome exponents + the 3 cross-terms (vs genus-2's ONE cross-term); quarter-nome base
_Sextuple = Tuple[int, int, int, int, int, int]

# a 2×2 integer matrix (a row-major tuple of 2-tuples) — the genus-2 building block
_Mat2 = Tuple[Tuple[int, int], Tuple[int, int]]
# an Sp(4, ℤ) element as the four 2×2 integer blocks (A, B, C, D)
_Sp4 = Tuple[_Mat2, _Mat2, _Mat2, _Mat2]


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

    # ══════════════════════════════════════════════════════════════════════════
    # rc73 (A): the Sp(4, ℤ) TRANSFORMATION (the modular action on characteristics)
    # ══════════════════════════════════════════════════════════════════════════

    # ── exact 2×2 integer matrix algebra (no numpy; integer / mod-2 only) ───────
    @staticmethod
    def _m_matvec(m: "_Mat2", v: "Tuple[int, int]") -> "List[int]":
        """The exact integer matrix·vector ``M·v`` for a 2×2 ``M`` and a length-2
        ``v`` (a bounded 2×2 multiply — JPL Rule 2). All-integer, no float."""
        return [m[0][0] * v[0] + m[0][1] * v[1],
                m[1][0] * v[0] + m[1][1] * v[1]]

    @staticmethod
    def _m_matmul(p: "_Mat2", q: "_Mat2") -> "_Mat2":
        """The exact integer 2×2 matrix product ``P·Q``."""
        return ((p[0][0] * q[0][0] + p[0][1] * q[1][0],
                 p[0][0] * q[0][1] + p[0][1] * q[1][1]),
                (p[1][0] * q[0][0] + p[1][1] * q[1][0],
                 p[1][0] * q[0][1] + p[1][1] * q[1][1]))

    @staticmethod
    def _m_transpose(m: "_Mat2") -> "_Mat2":
        """The exact 2×2 transpose ``Mᵀ``."""
        return ((m[0][0], m[1][0]), (m[0][1], m[1][1]))

    @staticmethod
    def _m_add(p: "_Mat2", q: "_Mat2") -> "_Mat2":
        """The exact 2×2 sum ``P + Q``."""
        return ((p[0][0] + q[0][0], p[0][1] + q[0][1]),
                (p[1][0] + q[1][0], p[1][1] + q[1][1]))

    @classmethod
    def _m_diag_of_prod(cls, p: "_Mat2", q: "_Mat2") -> "List[int]":
        """``diag(P·Qᵀ)`` as a length-2 vector — the diagonal of ``P·Qᵀ`` (the
        ``½diag[C·Dᵀ]`` / ``½diag[A·Bᵀ]`` terms of the Igusa characteristic
        transformation, here returned UN-halved as the integer ``diag(C·Dᵀ)`` since
        the doubled-half-integer characteristic absorbs the ½). Exact integer."""
        pqt = cls._m_matmul(p, cls._m_transpose(q))
        return [pqt[0][0], pqt[1][1]]

    # ── the standard Sp(4, ℤ) generators ───────────────────────────────────────
    @staticmethod
    def sp4_translation(b: "_Mat2") -> "_Sp4":
        """The Sp(4, ℤ) TRANSLATION generator ``γ = [[I, B], [0, I]]`` for a SYMMETRIC
        integer 2×2 ``B`` (DLMF §21.5, eq. 21.5.6 — ``θ(z | Ω+B)``; the ``Ω ↦ Ω+B``
        shift). ``B`` must be symmetric (else not symplectic) — rejected loudly
        otherwise. Returned as the four blocks ``(A, B, C, D) = (I, B, 0, I)``."""
        if not (isinstance(b, tuple) and len(b) == 2):
            raise ValueError(f"B must be a 2×2 integer matrix; got {b!r}")
        b = ((int(b[0][0]), int(b[0][1])), (int(b[1][0]), int(b[1][1])))
        if b[0][1] != b[1][0]:
            raise ValueError(
                f"the translation block B must be SYMMETRIC (Sp(4,ℤ) condition); "
                f"got B = {b!r} (B₁₂={b[0][1]} ≠ B₂₁={b[1][0]})")
        return (((1, 0), (0, 1)), b, ((0, 0), (0, 0)), ((1, 0), (0, 1)))

    @classmethod
    def sp4_gl_twist(cls, a: "_Mat2") -> "_Sp4":
        """The Sp(4, ℤ) GL-TWIST generator ``γ = [[A, 0], [0, (Aᵀ)⁻¹]]`` for
        ``A ∈ GL(2, ℤ)`` (DLMF §21.5, eq. 21.5.5 — ``θ(Az | A Ω Aᵀ)``; the basis
        change). ``A`` must have ``det A = ±1`` so ``(Aᵀ)⁻¹`` is integer — rejected
        loudly otherwise (an honest boundary, not a fabricated reduction). Returned
        as ``(A, 0, 0, (Aᵀ)⁻¹)``."""
        if not (isinstance(a, tuple) and len(a) == 2):
            raise ValueError(f"A must be a 2×2 integer matrix; got {a!r}")
        a = ((int(a[0][0]), int(a[0][1])), (int(a[1][0]), int(a[1][1])))
        det = a[0][0] * a[1][1] - a[0][1] * a[1][0]
        if det not in (1, -1):
            raise ValueError(
                f"the GL-twist block A must be in GL(2,ℤ) (det = ±1) so (Aᵀ)⁻¹ is "
                f"integer; got A = {a!r} with det = {det} — an honest boundary, not "
                "a fabricated reduction.")
        # A⁻¹ = (1/det)·adj(A); det = ±1 so this is exact integer
        a_inv = ((a[1][1] // det, -a[0][1] // det),
                 (-a[1][0] // det, a[0][0] // det))
        d = cls._m_transpose(a_inv)        # (Aᵀ)⁻¹ = (A⁻¹)ᵀ
        return (a, ((0, 0), (0, 0)), ((0, 0), (0, 0)), d)

    @staticmethod
    def sp4_inversion() -> "_Sp4":
        """The Sp(4, ℤ) INVERSION generator ``γ = [[0, −I], [I, 0]]`` (DLMF §21.5,
        eq. 21.5.8 — the genus-2 ``Ω ↦ −Ω⁻¹``; the ``J`` matrix). It carries the
        TRANSCENDENTAL automorphy factor ``det(−iΩ)^{1/2}`` (off every decision path;
        :meth:`automorphy_factor`). Returned as ``(0, −I, I, 0)``."""
        return (((0, 0), (0, 0)), ((-1, 0), (0, -1)),
                ((1, 0), (0, 1)), ((0, 0), (0, 0)))

    @classmethod
    def sp4_is_symplectic(cls, gamma: "_Sp4") -> bool:
        """True iff ``γ = (A, B, C, D)`` is genuinely symplectic — ``γ·J·γᵀ = J``
        with ``J = [[0, −I], [I, 0]]`` (DLMF §21.5, eq. 21.5.2). The exact integer
        block conditions are ``AᵀC = CᵀA``, ``BᵀD = DᵀB``, ``AᵀD − CᵀB = I``. A pure
        integer check (no float)."""
        a, b, c, d = cls._validate_gamma(gamma)
        at, bt, ct, dt = (cls._m_transpose(a), cls._m_transpose(b),
                          cls._m_transpose(c), cls._m_transpose(d))
        i2 = ((1, 0), (0, 1))
        cond1 = cls._m_matmul(at, c) == cls._m_matmul(ct, a)           # AᵀC sym
        cond2 = cls._m_matmul(bt, d) == cls._m_matmul(dt, b)           # BᵀD sym
        atd = cls._m_matmul(at, d)
        ctb = cls._m_matmul(ct, b)
        cond3 = ((atd[0][0] - ctb[0][0], atd[0][1] - ctb[0][1]),
                 (atd[1][0] - ctb[1][0], atd[1][1] - ctb[1][1])) == i2  # AᵀD−CᵀB=I
        return cond1 and cond2 and cond3

    @classmethod
    def sp4_compose(cls, g2: "_Sp4", g1: "_Sp4") -> "_Sp4":
        """The Sp(4, ℤ) group law ``g2 · g1`` (the block matrix product) — exact
        integer 2×2 block arithmetic. The characteristic action composes the SAME
        way (``transform(g2·g1) == transform(g2) ∘ transform(g1)``; the gate)."""
        a2, b2, c2, d2 = cls._validate_gamma(g2)
        a1, b1, c1, d1 = cls._validate_gamma(g1)
        mm, ad = cls._m_matmul, cls._m_add
        a = ad(mm(a2, a1), mm(b2, c1))
        b = ad(mm(a2, b1), mm(b2, d1))
        c = ad(mm(c2, a1), mm(d2, c1))
        d = ad(mm(c2, b1), mm(d2, d1))
        return (a, b, c, d)

    @staticmethod
    def _validate_gamma(gamma: "_Sp4") -> "_Sp4":
        """Coerce / validate an ``Sp(4, ℤ)`` element ``(A, B, C, D)`` to a tuple of
        four exact-integer 2×2 blocks; reject a malformed shape loudly."""
        if not (isinstance(gamma, (tuple, list)) and len(gamma) == 4):
            raise ValueError(
                f"γ must be (A, B, C, D), four 2×2 integer matrices; got {gamma!r}")
        out = []
        for blk in gamma:
            if not (isinstance(blk, (tuple, list)) and len(blk) == 2
                    and all(isinstance(row, (tuple, list)) and len(row) == 2
                            for row in blk)):
                raise ValueError(f"each γ block must be 2×2; got {blk!r}")
            out.append(((int(blk[0][0]), int(blk[0][1])),
                        (int(blk[1][0]), int(blk[1][1]))))
        return (out[0], out[1], out[2], out[3])

    # ── the EXACT characteristic action + the κ 8th-root multiplier ─────────────
    @classmethod
    def _char_transform_int(cls, gamma: "_Sp4", ep_prime: "Tuple[int, int]",
                            eps: "Tuple[int, int]") -> "Tuple[List[int], List[int]]":
        """The Igusa / DLMF-21.5.9 characteristic action, as INTEGER vectors (the
        caller reduces mod 2 for the bit): ``ε' ↦ D·ε' − C·ε + diag(C·Dᵀ)`` and
        ``ε ↦ −B·ε' + A·ε + diag(A·Bᵀ)``. Exact integer 2×2 arithmetic, no float."""
        a, b, c, d = cls._validate_gamma(gamma)
        d_epp = cls._m_matvec(d, ep_prime)
        c_eps = cls._m_matvec(c, eps)
        diag_cd = cls._m_diag_of_prod(c, d)
        new_epp = [d_epp[i] - c_eps[i] + diag_cd[i] for i in range(2)]
        a_eps = cls._m_matvec(a, eps)
        b_epp = cls._m_matvec(b, ep_prime)
        diag_ab = cls._m_diag_of_prod(a, b)
        new_eps = [a_eps[i] - b_epp[i] + diag_ab[i] for i in range(2)]
        return new_epp, new_eps

    @classmethod
    def _kappa_exp8(cls, gamma: "_Sp4", ep_prime: "Tuple[int, int]",
                    eps: "Tuple[int, int]") -> int:
        """The EXACT 8th-root multiplier exponent ``k ∈ ℤ/8`` (the multiplier is
        ``ζ₈^k = e^{2πik/8}``) — the CHARACTERISTIC-DEPENDENT Igusa phase ``φ_m(γ)``
        of the theta-constant transformation

            φ_m(γ) = −½·ε'ᵀ·B·Dᵀ·ε' + εᵀ·Aᵀ·C·ε − 2·ε'ᵀ·Bᵀ·C·ε
                     − diag(A·Bᵀ)ᵀ·(D·ε' − C·ε)

        (Igusa, *Theta Functions* (1972), §V.1; the full transformation multiplier is
        ``κ₀(γ)·exp(2πi·φ_m(γ))``, an 8th root of unity for theta-constants). This
        method returns the ``exp(2πi·φ_m)`` part — the piece that is EXACTLY
        computable on the decision path: the phase is rational with denominator
        dividing 8, so ``8·φ_m`` is an EXACT integer → ``k = (8·φ_m) mod 8`` is exact
        (no float). The remaining ``γ``-only factor ``κ₀(γ)`` (an 8th root tied to the
        Maslov / Weil cocycle — e.g. the ``−i`` on the genus-1 inversion ``J``) is
        BOUND to the TRANSCENDENTAL automorphy factor ``det(C·Ω+D)^{1/2}`` (the
        branch of the square root), so it is NOT placed on the decision path — it is
        carried SYMBOLICALLY with that factor (:meth:`automorphy_factor`; the rc72
        review lesson). What this exponent IS exactly is the characteristic-phase
        ``φ_m`` — bit-exact, and the genuinely-new genus-2 content (the lattice-shift
        sign of the theta-constant under ``γ``). The doubled-half characteristic
        absorbs the ½'s; we carry ``8·φ_m`` as an integer throughout:

            8·φ_m = −4·ε'ᵀ(B·Dᵀ)ε' + 8·εᵀ(AᵀC)ε − 16·ε'ᵀ(BᵀC)ε
                    − 8·diag(A·Bᵀ)ᵀ(D·ε' − C·ε)
        """
        a, b, c, d = cls._validate_gamma(gamma)
        epp = (int(ep_prime[0]), int(ep_prime[1]))
        eps = (int(eps[0]), int(eps[1]))
        # term 1: −4·ε'ᵀ(B·Dᵀ)ε'   (the −½ becomes −4 after ×8)
        bdt = cls._m_matmul(b, cls._m_transpose(d))
        t1 = -4 * cls._dot2(epp, cls._m_matvec(bdt, epp))
        # term 2: +8·εᵀ(AᵀC)ε
        atc = cls._m_matmul(cls._m_transpose(a), c)
        t2 = 8 * cls._dot2(eps, cls._m_matvec(atc, eps))
        # term 3: −16·ε'ᵀ(BᵀC)ε
        btc = cls._m_matmul(cls._m_transpose(b), c)
        t3 = -16 * cls._dot2(epp, cls._m_matvec(btc, eps))
        # term 4: −8·diag(A·Bᵀ)ᵀ(D·ε' − C·ε)
        diag_ab = cls._m_diag_of_prod(a, b)
        d_epp = cls._m_matvec(d, epp)
        c_eps = cls._m_matvec(c, eps)
        arg = [d_epp[i] - c_eps[i] for i in range(2)]
        t4 = -8 * cls._dot2(diag_ab, arg)
        eight_phi = t1 + t2 + t3 + t4
        return eight_phi % 8                       # exact k ∈ {0,…,7}

    @staticmethod
    def _dot2(u: "Tuple[int, int]", v: "Tuple[int, int]") -> int:
        """The exact integer dot product ``u·v`` of two length-2 vectors."""
        return u[0] * v[0] + u[1] * v[1]

    def transform(self, gamma: "_Sp4") -> "Tuple[RiemannTheta, int]":
        """The EXACT Sp(4, ℤ) modular action on THIS theta-characteristic: returns
        the transformed :class:`RiemannTheta` ``θ[γ·m]`` and the 8th-root multiplier
        exponent ``k ∈ ℤ/8`` (the multiplier is ``ζ₈^k``). The characteristic map
        (DLMF §21.5.9) is bit-exact (integer / mod-2); the multiplier rides the exact
        Igusa phase (:meth:`_kappa_exp8`). The transcendental automorphy factor
        ``det(C·Ω+D)^{1/2}`` is NOT applied — it is carried symbolically
        (:meth:`automorphy_factor`), off the decision path.

        DISPATCHES the exact-integer characteristic + κ computation to the native
        ``srmech_riemann_theta_sp4_char`` C peer when loaded (a 1:1 mirror — the C
        result EQUALS the Python result, trusted only on a native hit); else the pure
        body (the COMPLETE alternative + the parity oracle). ``γ`` must be symplectic
        — rejected loudly otherwise (an honest boundary). Parity (even ⇄ even,
        odd ⇄ odd) is preserved by construction."""
        if not self.sp4_is_symplectic(gamma):
            raise ValueError(
                "transform requires a symplectic γ (γ·J·γᵀ = J); the given (A,B,C,D) "
                "is not in Sp(4,ℤ) — an honest boundary, not a fabricated reduction.")
        nat = _native()
        if nat is not None:
            try:
                g = self._validate_gamma(gamma)
                got = nat.riemann_theta_sp4_char_c(
                    g, self._ep1, self._ep2, self._e1, self._e2)
                if got is not None:
                    (npp1, npp2, ne1, ne2), kexp = got
                    return RiemannTheta(npp1, npp2, ne1, ne2), kexp % 8
            except (RuntimeError, OverflowError, ValueError):
                pass                                  # fall to the pure path
        new_epp, new_eps = self._char_transform_int(
            gamma, (self._ep1, self._ep2), (self._e1, self._e2))
        kexp = self._kappa_exp8(
            gamma, (self._ep1, self._ep2), (self._e1, self._e2))
        return (RiemannTheta(new_epp[0] % 2, new_epp[1] % 2,
                             new_eps[0] % 2, new_eps[1] % 2), kexp)

    @staticmethod
    def automorphy_factor(gamma: "_Sp4") -> str:
        """The TRANSCENDENTAL automorphy factor ``det(C·Ω+D)^{1/2}`` of the Sp(4, ℤ)
        action — returned as a SYMBOLIC string, NEVER numerically evaluated (it
        depends on the transcendental period matrix ``Ω`` and is a square root: not a
        finite exact object, so it stays OFF every decision path; the rc72 review
        lesson). The honest, exact part of the transformation is the characteristic
        map + the κ 8th root (:meth:`transform`); this factor is the documented
        not-evaluated companion."""
        a, b, c, d = RiemannTheta._validate_gamma(gamma)
        return (f"det([[{c[0][0]},{c[0][1]}],[{c[1][0]},{c[1][1]}]]·Ω + "
                f"[[{d[0][0]},{d[0][1]}],[{d[1][0]},{d[1][1]}]])^(1/2)")

    # ══════════════════════════════════════════════════════════════════════════
    # rc73 (B): the genus-2 ADDITION relation (genuine; distinct from duplication)
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _theta_omega_eighth(a1: int, a2: int, e1: int, e2: int,
                            box: int) -> "Dict[_Triple, int]":
        """The genus-2 theta-constant ``θ[(a₁,a₂); (e₁,e₂)](0 | Ω)`` in the COMMON
        EIGHTH-nome base ``Q₈ = q^{1/8}`` (so it shares ONE integer lattice with the
        ``2Ω`` thetas of the addition right side). With ``mᵢ = nᵢ + aᵢ/2`` the q₁
        exponent ``m₁²`` rides ``Q₈^{8m₁²} = Q₈^{2(2n₁+a₁)²}``, the cross
        ``m₁m₂`` rides ``Q₈^{8m₁m₂} = Q₈^{2(2n₁+a₁)(2n₂+a₂)}``:

            A = 2(2n₁+a₁)², B = 2(2n₂+a₂)², C = 2(2n₁+a₁)(2n₂+a₂)

        sign ``(−1)^{e·n}`` is the Class-K pin-slot (explicit ±1 branch, never
        ``abs()``). Exact integer, no float / numpy / ``math``. ``a₁, a₂`` are the
        DOUBLED upper characteristic (in {0,1} for an integer characteristic, but the
        helper accepts any integer so the right side's ``2r±(a∓b)`` cases work).
        DISPATCHES to the native ``srmech_riemann_theta_eighth_lattice`` (at Ω) when
        loaded — a 1:1 exact-integer mirror, trusted only on a native hit."""
        nat = _native()
        if nat is not None and getattr(nat, "has_native_riemann_theta_eighth",
                                       lambda: False)():
            try:
                got = nat.riemann_theta_eighth_lattice_c(
                    a1, a2, e1, e2, False, box)
                if got is not None:
                    return got
            except (RuntimeError, OverflowError, ValueError):
                pass
        out: Dict[_Triple, int] = {}
        for n1 in range(-box, box + 1):
            for n2 in range(-box, box + 1):
                u = 2 * n1 + a1
                v = 2 * n2 + a2
                key = (2 * u * u, 2 * v * v, 2 * u * v)
                parity = (e1 * n1 + e2 * n2) % 2
                sign = 1 if parity == 0 else -1       # never abs(); explicit ±
                out[key] = out.get(key, 0) + sign
        return {k: w for k, w in out.items() if w != 0}

    @staticmethod
    def _theta_two_omega_eighth(s1: int, s2: int, e1: int, e2: int,
                                box: int) -> "Dict[_Triple, int]":
        """The genus-2 theta-constant ``θ[(s₁/2, s₂/2); (e₁,e₂)](0 | 2Ω)`` in the
        SAME EIGHTH-nome base. The constructive sum/difference re-indexing
        (``M = m+m'``, ``M' = m−m'``) puts the addition right side here: each ``M``
        ranges over a coset of ``2ℤ²`` shifted by ``s/2``, so ``M = 2N + s/2`` and
        the q-exponent ``M²`` rides ``Q₈^{8·(2·M²/... )}`` — concretely the eighth-nome
        exponent of ``θ`` at ``2Ω`` is ``(4N+s)²`` (and cross ``(4N₁+s₁)(4N₂+s₂)``):

            A = (4n₁+s₁)², B = (4n₂+s₂)², C = (4n₁+s₁)(4n₂+s₂)

        sign ``(−1)^{e·n}`` the Class-K pin-slot. ``s₁, s₂`` are the DOUBLED upper
        characteristic of the ``2Ω`` theta (an integer; odd ⟺ a genuine half-integer
        characteristic). Exact integer, no float. DISPATCHES to the native
        ``srmech_riemann_theta_eighth_lattice`` (at 2Ω) when loaded — a 1:1
        exact-integer mirror, trusted only on a native hit."""
        nat = _native()
        if nat is not None and getattr(nat, "has_native_riemann_theta_eighth",
                                       lambda: False)():
            try:
                got = nat.riemann_theta_eighth_lattice_c(
                    s1, s2, e1, e2, True, box)
                if got is not None:
                    return got
            except (RuntimeError, OverflowError, ValueError):
                pass
        out: Dict[_Triple, int] = {}
        for n1 in range(-box, box + 1):
            for n2 in range(-box, box + 1):
                u = 4 * n1 + s1
                v = 4 * n2 + s2
                key = (u * u, v * v, u * v)
                parity = (e1 * n1 + e2 * n2) % 2
                sign = 1 if parity == 0 else -1
                out[key] = out.get(key, 0) + sign
        return {k: w for k, w in out.items() if w != 0}

    @classmethod
    def addition_lhs(cls, a: "Tuple[int, int]", b: "Tuple[int, int]",
                     box: int) -> "Dict[_Triple, int]":
        """The LEFT side of the genus-2 addition identity — the BILINEAR product of
        TWO theta-nulls ``θ[a; 0](0|Ω) · θ[b; 0](0|Ω)`` (in the common eighth-nome
        base), the exact-integer lattice convolution. ``a, b`` are the upper
        characteristics (each in {0,1}²). When ``a ≠ b`` this is a product of two
        DISTINCT nulls — the content duplication cannot produce. See
        :meth:`addition_holds`."""
        la = cls._theta_omega_eighth(a[0], a[1], 0, 0, box)
        lb = cls._theta_omega_eighth(b[0], b[1], 0, 0, box)
        return cls._square_lattice_pair(la, lb)

    @classmethod
    def addition_rhs(cls, a: "Tuple[int, int]", b: "Tuple[int, int]",
                     box: int) -> "Dict[_Triple, int]":
        """The RIGHT side of the genus-2 addition identity

            Σ_{r ∈ (ℤ/2)²} θ[(2r+a+b)/2; 0](0|2Ω) · θ[(2r+a−b)/2; 0](0|2Ω)

        (in the common eighth-nome base). Each summand is a product of two ``2Ω``
        theta-nulls with the DISTINCT doubled characteristics ``2r+a+b`` vs
        ``2r+a−b`` — the genuinely-new content; the ``a = b`` collapse recovers
        rc72's duplication ``Σ_r θ[r;0](2Ω)²``. See :meth:`addition_holds`."""
        rhs: Dict[_Triple, int] = {}
        for r1 in (0, 1):
            for r2 in (0, 1):
                sp1 = 2 * r1 + a[0] + b[0]
                sp2 = 2 * r2 + a[1] + b[1]
                sm1 = 2 * r1 + a[0] - b[0]
                sm2 = 2 * r2 + a[1] - b[1]
                l1 = cls._theta_two_omega_eighth(sp1, sp2, 0, 0, box)
                l2 = cls._theta_two_omega_eighth(sm1, sm2, 0, 0, box)
                term = cls._square_lattice_pair(l1, l2)
                for k, v in term.items():
                    rhs[k] = rhs.get(k, 0) + v
        return {k: v for k, v in rhs.items() if v != 0}

    @staticmethod
    def _square_lattice_pair(la: "Dict[_Triple, int]",
                             lb: "Dict[_Triple, int]") -> "Dict[_Triple, int]":
        """The exact-integer product ``la · lb`` of two ``(A, B, C) → coeff``
        lattices (a bounded convolution over the exponent triples; JPL Rule 2).
        All-integer, no float. (The two-lattice peer of :meth:`_square_lattice`,
        which squares a single lattice.)"""
        out: Dict[_Triple, int] = {}
        items_a = list(la.items())
        items_b = list(lb.items())
        for (a1, b1, c1), v1 in items_a:
            for (a2, b2, c2), v2 in items_b:
                key = (a1 + a2, b1 + b2, c1 + c2)
                out[key] = out.get(key, 0) + v1 * v2
        return {k: v for k, v in out.items() if v != 0}

    @classmethod
    def addition_holds(cls, box: int = 8) -> bool:
        """The genus-2 ADDITION identity gate (the rc73 (B) build gate) — the GENUINE
        two-argument genus-2 theta addition theorem (DLMF §21.6, eq. 21.6.8, the
        ``z₁ = z₂ = 0``, two-independent-characteristic specialization),

            θ[a; 0](0|Ω)·θ[b; 0](0|Ω)
              = Σ_{r ∈ (ℤ/2)²} θ[(2r+a+b)/2; 0](0|2Ω)·θ[(2r+a−b)/2; 0](0|2Ω) ,

        holds EXACTLY as a truncated exact-integer multivariate q-series, for ALL
        ``Ω`` (no transcendental evaluation, no float, no tolerance). The identity is
        proved CONSTRUCTIVELY by the sum/difference re-indexing ``M = m+m'``,
        ``M' = m−m'`` of the double lattice sum (see :meth:`_theta_two_omega_eighth`);
        it is an instance of the genus-2 addition theorem.

        GENUINELY DISTINCT FROM rc72's duplication: duplication squares a SINGLE even
        theta-null (``θ[0;0]² = Σ_c θ[c;0](2Ω)²``); this addition relation is the
        BILINEAR product of TWO DIFFERENT nulls ``θ[a]·θ[b]`` (``a ≠ b``), and the
        right side carries DISTINCT characteristics ``2r+a+b`` vs ``2r+a−b`` per
        summand — content duplication alone never produces (it never holds a product
        of two distinct nulls). The gate VERIFIES the non-trivial ``a ≠ b`` cases
        (and confirms they differ from the ``a = b`` duplication collapse), so it is
        the GENUINE addition theorem, not a relabeled duplication.

        Compares the two sides on the SAFE INNER REGION the box ``|nᵢ| ≤ box``
        provably resolves. Returns ``True`` iff every checked ``(a, b)`` pair agrees
        exactly on the safe region, at least one genuine ``a ≠ b`` pair is checked,
        and the safe region is non-trivially populated with cross-term (``C ≠ 0``)
        monomials (so the genus-2 coupling is genuinely exercised).

        A CARRIER METHOD (the carrier's own build gate), not a public module-level op
        — ``tools.total`` is UNCHANGED (the rc72 ``duplication_holds`` precedent)."""
        if not isinstance(box, int) or box < 2:
            raise ValueError(
                f"box must be an int ≥ 2 for the addition gate; got {box!r}")
        # the safe inner region: the eighth-nome theta at Ω reaches exponent
        # 2·(2·box)² and at 2Ω reaches (4·box)²; a box-`box` truncation fully
        # resolves monomials with A, B, |C| ≤ 2·box² (a conservative inner bound).
        safe = 2 * box * box
        # the (a, b) pairs to verify: the duplication collapse (a==b) PLUS genuine
        # distinct pairs (a != b) — the latter is what makes it the real addition.
        pairs = [((0, 0), (0, 0)),                       # duplication collapse
                 ((1, 0), (0, 0)), ((1, 1), (0, 0)),     # genuine a ≠ b
                 ((1, 0), (0, 1)), ((1, 1), (1, 0)),
                 ((0, 1), (1, 1))]

        def restrict(lat: "Dict[_Triple, int]") -> "Dict[_Triple, int]":
            kept: Dict[_Triple, int] = {}
            for (aa, bb, cc), v in lat.items():
                cmag = cc if cc >= 0 else -cc          # Class-K magnitude, no abs()
                if aa <= safe and bb <= safe and cmag <= safe:
                    kept[(aa, bb, cc)] = v
            return kept

        saw_genuine = False
        saw_cross = False
        for (a, b) in pairs:
            lhs = restrict(cls.addition_lhs(a, b, box))
            rhs = restrict(cls.addition_rhs(a, b, box))
            if lhs != rhs:
                return False
            if a != b:
                saw_genuine = True
            if any(cc != 0 for (_a, _b, cc) in lhs):
                saw_cross = True
        return saw_genuine and saw_cross

    @classmethod
    def addition_is_distinct_from_duplication(cls, box: int = 8) -> bool:
        """PROVES the addition relation is GENUINELY DISTINCT from duplication: for a
        genuine ``a ≠ b`` pair the addition LEFT side ``θ[a]·θ[b]`` is a product of
        two DIFFERENT theta-nulls, which is NOT equal to ANY duplication left side
        ``θ[c]²`` (a single null squared). Returns ``True`` iff the genuine addition
        LHS (``a=(1,0)``, ``b=(0,0)``) differs from every ``θ[c;0]²`` over the four
        even ``c`` — the no-shell proof that it is not a relabeled duplication."""
        if not isinstance(box, int) or box < 2:
            raise ValueError(f"box must be an int ≥ 2; got {box!r}")
        genuine = cls.addition_lhs((1, 0), (0, 0), box)   # θ[(1,0)]·θ[(0,0)]
        for c1 in (0, 1):
            for c2 in (0, 1):
                tc = cls._theta_omega_eighth(c1, c2, 0, 0, box)
                sq = cls._square_lattice_pair(tc, tc)     # θ[c;0]²
                if genuine == sq:
                    return False                          # would be a duplication
        return True

    # ══════════════════════════════════════════════════════════════════════════
    # rc74: the GENUS-AXIS CAPSTONE — the Thomae / Rosenhain bridge
    #   (A) the FROBENIUS / GÖPEL quadratic syzygy among the even theta-NULLS
    #       (genuine NEW exact relation; distinct from duplication + addition),
    #   (B) the SYMBOLIC Rosenhain λ-map (the 3 Rosenhain moduli as formal
    #       theta-null RATIOS — NOT numerical values),
    #   (C) the documented operand-side OPEN (numerical branch-point recovery
    #       needs the transcendental period map).
    # ══════════════════════════════════════════════════════════════════════════

    # ── the Eilers genus-2 η-map: branch-point index set → characteristic ───────
    #
    # Eilers, "Rosenhain–Thomae Formulae for Higher Genera Hyperelliptic Curves"
    # (arXiv:1707.08855), §4, eqs (4.2)–(4.4). For the genus-2 curve with branch
    # points e₁ < … < e₅ < e₆ = ∞ in the homology basis of Fig. 1, the Abelian
    # images carry the EXACT (mod-2) characteristics [𝔄_k] (eq 4.2), the vector of
    # Riemann constants is [K∞] = [𝔄₂]+[𝔄₄]+[𝔄₆] (eq 4.3), and the characteristic
    # of a branch-point index set I is
    #
    #     [ε(I)] = Σ_{k ∈ I} [𝔄_k] − [K∞]   (mod 2)        (eq 4.4)
    #
    # The 6 SINGLE indices give the 6 ODD characteristics (branch points ↔ odd
    # chars); the 10 PAIRS of FINITE indices {1,…,5} give the 10 EVEN theta-nulls.
    # All exact integer / mod-2 — no float, no abs() (Class-K is not even needed; the
    # map is pure GF(2) linear algebra). The carrier verifies this assignment is
    # internally consistent (10 even, 6 odd) at build time.

    # [𝔄_k] for k = 1..6 (e₆ = ∞), as ((ε'₁,ε'₂),(ε₁,ε₂)) — Eilers eq (4.2)
    _EILERS_A = {
        1: ((1, 0), (0, 0)),
        2: ((1, 0), (1, 0)),
        3: ((0, 1), (1, 0)),
        4: ((0, 1), (1, 1)),
        5: ((0, 0), (1, 1)),
        6: ((0, 0), (0, 0)),
    }

    @classmethod
    def _char_add_mod2(cls, *chars: "Tuple[Tuple[int, int], Tuple[int, int]]"
                       ) -> "Tuple[Tuple[int, int], Tuple[int, int]]":
        """The exact GF(2) sum of binary characteristics ``Σ [εᵢ] (mod 2)`` — pure
        integer / mod-2 (the characteristic group is (ℤ/2)⁴). No float, no abs()."""
        ep1 = ep2 = e1 = e2 = 0
        for (epp, eps) in chars:
            ep1 += epp[0]
            ep2 += epp[1]
            e1 += eps[0]
            e2 += eps[1]
        return ((ep1 % 2, ep2 % 2), (e1 % 2, e2 % 2))

    @classmethod
    def riemann_constant(cls) -> "Tuple[Tuple[int, int], Tuple[int, int]]":
        """The genus-2 vector of Riemann constants characteristic
        ``[K∞] = [𝔄₂]+[𝔄₄]+[𝔄₆] (mod 2)`` in the Eilers Fig.-1 homology basis
        (arXiv:1707.08855, eq 4.3) — an EXACT GF(2) characteristic ``((1,1),(0,1))``.
        Used by the η-map :meth:`branch_set_characteristic`."""
        return cls._char_add_mod2(cls._EILERS_A[2], cls._EILERS_A[4],
                                  cls._EILERS_A[6])

    @classmethod
    def branch_set_characteristic(cls, indices: "Tuple[int, ...]"
                                  ) -> "Tuple[Tuple[int, int], Tuple[int, int]]":
        """The Eilers genus-2 η-map (arXiv:1707.08855, eq 4.4): the EXACT (mod-2)
        characteristic ``[ε(I)] = Σ_{k∈I} [𝔄_k] − [K∞]`` of a branch-point index set
        ``I ⊆ {1,…,6}`` (``e₆ = ∞``). A SINGLE index → an ODD characteristic (branch
        points ↔ odd chars); a PAIR of finite indices ``{i,j} ⊂ {1,…,5}`` → an EVEN
        theta-null. Pure GF(2) linear algebra — exact integer / mod-2, no float, no
        abs(). Indices must lie in ``{1,…,6}`` (rejected loudly otherwise).

        DISPATCHES to the native ``srmech_riemann_theta_eta_char`` C peer when loaded
        (a 1:1 exact GF(2) mirror — the C characteristic EQUALS the Python one,
        trusted only on a native hit); else the pure-Python body (the COMPLETE
        alternative + the parity oracle)."""
        idx = tuple(int(i) for i in indices)
        for i in idx:
            if i < 1 or i > 6:
                raise ValueError(
                    f"branch-point index {i} out of range {{1,…,6}} (e₆ = ∞); an "
                    "honest boundary, not a fabricated reduction.")
        nat = _native()
        if nat is not None:
            try:
                got = nat.riemann_theta_eta_char_c(idx)
                if got is not None:
                    return got
            except (RuntimeError, OverflowError, ValueError):
                pass                                   # fall to the pure path
        return cls._eta_char_py(idx)

    @classmethod
    def _eta_char_py(cls, idx: "Tuple[int, ...]"
                     ) -> "Tuple[Tuple[int, int], Tuple[int, int]]":
        """The COMPLETE pure-Python Eilers η-map (the parity oracle for the C peer):
        ``[ε(I)] = Σ_{k∈I} [𝔄_k] − [K∞] (mod 2)``. ``− [K∞] (mod 2)`` equals
        ``+ [K∞] (mod 2)`` — the GF(2) group ``(ℤ/2)⁴`` is its own inverse, so
        subtraction IS addition (no sign / Class-K branch needed). Exact integer."""
        terms = [cls._EILERS_A[i] for i in idx]
        return cls._char_add_mod2(*(terms + [cls.riemann_constant()]))

    # ── (A) the FROBENIUS / GÖPEL quadratic syzygy among the even theta-NULLS ────

    @classmethod
    def goepel_syzygy_triple(cls) -> "Tuple[Tuple[..., ...], ...]":
        """The canonical genus-2 FROBENIUS / GÖPEL quadratic syzygy among the even
        theta-NULLS — three PAIRS of even characteristics

            ( θ²[a]θ²[b] ,  θ²[c]θ²[d] ,  θ²[e]θ²[f] )

        satisfying ``θ²[a]θ²[b] = θ²[c]θ²[d] − θ²[e]θ²[f]`` (see :meth:`goepel_holds`).
        Returned as a 3-tuple of pairs of characteristics ``((a,b),(c,d),(e,f))``.

        The six characteristics are DISTINCT even theta-nulls; the three pairs share
        ONE common GF(2) characteristic sum (the **Göpel-system / syzygy** invariant
        — :meth:`goepel_is_syzygous`), which is the structural fingerprint of the
        Riemann theta relation (the genus-2 specialization of the quartic Riemann
        relation, DLMF §21.6, eq 21.6.6/21.6.7; Mumford, *Tata Lectures on Theta II*,
        the genus-2 Göpel/Frobenius relations among even theta-nulls; Igusa, *Theta
        Functions* (1972) §IV). The canonical representative pairs

            a=[0,0;0,0]  b=[1,1;1,1] | c=[0,0;1,1]  d=[1,1;0,0] | e=[0,1;1,0]  f=[1,0;0,1]

        all sum to the common characteristic ``[1,1;1,1]``."""
        return (
            (((0, 0), (0, 0)), ((1, 1), (1, 1))),
            (((0, 0), (1, 1)), ((1, 1), (0, 0))),
            (((0, 1), (1, 0)), ((1, 0), (0, 1))),
        )

    @classmethod
    def goepel_is_syzygous(cls) -> bool:
        """True iff the canonical Göpel triple is genuinely SYZYGOUS — the three
        pairs all share ONE common GF(2) characteristic sum, and the six even
        theta-nulls are DISTINCT and all EVEN. This is the structural fingerprint
        that the relation is a genus-2 Göpel/Frobenius syzygy (a Göpel system), not
        an accidental coincidence. Pure GF(2) algebra — exact, no float."""
        triple = cls.goepel_syzygy_triple()
        sums = [cls._char_add_mod2(p[0], p[1]) for p in triple]
        if not (sums[0] == sums[1] == sums[2]):
            return False
        involved = [c for p in triple for c in p]
        if len(set(involved)) != 6:                    # six DISTINCT nulls
            return False
        for (epp, eps) in involved:                    # all EVEN
            if (epp[0] * eps[0] + epp[1] * eps[1]) % 2 != 0:
                return False
        return True

    @classmethod
    def _theta_null_fourth_product(cls, pair, box: int) -> "Dict[_Triple, int]":
        """The exact-integer lattice of ``θ²[a]·θ²[b]`` (a product of the SQUARES of
        two even theta-nulls at the SAME Ω) for ``pair = (a, b)`` — the 4-fold
        convolution of the two rc72 theta-null lattices, in the quarter-nome base.
        All-integer, no float (the per-term sign is already the Class-K pin-slot
        baked into :meth:`lattice`)."""
        a, b = pair
        la = cls.theta_constant(a[0], a[1]).lattice(box)
        lb = cls.theta_constant(b[0], b[1]).lattice(box)
        sa = cls._square_lattice(la)
        sb = cls._square_lattice(lb)
        return cls._square_lattice_pair(sa, sb)

    @classmethod
    def goepel_lhs(cls, box: int) -> "Dict[_Triple, int]":
        """The LEFT side ``θ²[a]·θ²[b]`` of the canonical Göpel syzygy (the product
        of two SQUARED even theta-nulls at the SAME Ω). See :meth:`goepel_holds`."""
        return cls._theta_null_fourth_product(cls.goepel_syzygy_triple()[0], box)

    @classmethod
    def goepel_rhs(cls, box: int) -> "Dict[_Triple, int]":
        """The RIGHT side ``θ²[c]·θ²[d] − θ²[e]·θ²[f]`` of the canonical Göpel syzygy
        (the exact-integer lattice difference of two products of squared even
        theta-nulls). The subtraction is exact-integer coefficient subtraction (the
        Class-K sign lives inside each theta-null lattice already). See
        :meth:`goepel_holds`."""
        triple = cls.goepel_syzygy_triple()
        cd = cls._theta_null_fourth_product(triple[1], box)
        ef = cls._theta_null_fourth_product(triple[2], box)
        out: Dict[_Triple, int] = dict(cd)
        for k, v in ef.items():
            out[k] = out.get(k, 0) - v
        return {k: v for k, v in out.items() if v != 0}

    @classmethod
    def goepel_holds(cls, box: int = 5) -> bool:
        """rc74's EXACT CORE — the genus-2 FROBENIUS / GÖPEL quadratic theta-null
        syzygy

            θ²[a]·θ²[b]  =  θ²[c]·θ²[d]  −  θ²[e]·θ²[f]

        holds EXACTLY as a truncated exact-integer multivariate q-series, for ALL
        ``Ω`` (the genus-2 specialization of the quartic Riemann theta relation —
        DLMF §21.6, eq 21.6.6/21.6.7; Mumford, *Tata Lectures on Theta II*, the
        genus-2 Göpel/Frobenius relations; Igusa, *Theta Functions* (1972) §IV).
        No transcendental evaluation, no float, no tolerance.

        GENUINELY NEW — DISTINCT FROM rc72 DUPLICATION AND rc73 ADDITION: this is a
        relation among even theta-nulls all at the SAME Ω (no Ω-doubling), whereas
        BOTH duplication (``θ[0;0]² = Σ_c θ[c;0](2Ω)²``) and addition
        (``θ[a]θ[b] = Σ_r θ[…](2Ω)θ[…](2Ω)``) relate the nulls at Ω to nulls at 2Ω.
        See :meth:`goepel_is_distinct_from_duplication_and_addition` for the no-shell
        proof.

        The two sides are compared on the SAFE INNER REGION the box ``|nᵢ| ≤ box``
        provably resolves. A product of four theta-null lattices has each monomial's
        ``A``/``B`` exponent a sum of squares ``(2nᵢ+ε'ᵢ)²``; the smallest exponent a
        box-``box`` truncation can OMIT comes from a factor at ``|nᵢ| = box+1``,
        i.e. ``≥ (2·box+1)²``, so monomials with ``A, B, |C| ≤ box²`` (well below
        ``(2·box+1)²``) are FULLY accumulated — an inner region empirically verified
        box-STABLE (identical across box = 4, 5, 6). Returns ``True`` iff the two
        sides agree exactly on that region, the triple is genuinely syzygous
        (:meth:`goepel_is_syzygous`), and the region is non-trivially populated with
        cross-term (``C ≠ 0``) monomials (so the genus-2 coupling is genuinely
        exercised — this is not the genus-1 slice).

        A CARRIER METHOD (the carrier's own build gate), not a public module-level op
        — ``tools.total`` is UNCHANGED (the rc72 ``duplication_holds`` / rc73
        ``addition_holds`` precedent)."""
        if not isinstance(box, int) or box < 4:
            raise ValueError(
                f"box must be an int ≥ 4 for the Göpel gate (the inner region is "
                f"box-stable from box=4); got {box!r}")
        if not cls.goepel_is_syzygous():
            return False
        safe = box * box                               # the box-stable inner bound

        def restrict(lat: "Dict[_Triple, int]") -> "Dict[_Triple, int]":
            kept: Dict[_Triple, int] = {}
            for (a, b, c), v in lat.items():
                cmag = c if c >= 0 else -c             # Class-K magnitude, no abs()
                if a <= safe and b <= safe and cmag <= safe:
                    kept[(a, b, c)] = v
            return kept

        lhs = restrict(cls.goepel_lhs(box))
        rhs = restrict(cls.goepel_rhs(box))
        if lhs != rhs:
            return False
        return any(c != 0 for (_a, _b, c) in lhs)      # genuinely cross-term

    @classmethod
    def goepel_is_distinct_from_duplication_and_addition(
            cls, box: int = 5) -> bool:
        """THE rc74 NO-SHELL PROOF: the Göpel syzygy is GENUINELY DISTINCT from BOTH
        rc72 duplication AND rc73 addition.

        STRUCTURAL: duplication and addition are Ω-vs-2Ω identities (their right
        sides live at 2Ω, carried in the quarter/eighth-nome with DOUBLED exponents
        via :meth:`_double_exps` / the eighth-nome at-2Ω lattice). The Göpel syzygy
        is purely at Ω — every factor is a theta-null at Ω, NO Ω-doubling appears.

        EXACT: the proof here is no-shell — the Göpel LEFT side ``θ²[a]θ²[b]`` (a
        product of squares of two DISTINCT even nulls at Ω) is checked NOT EQUAL to
        either the duplication LHS ``θ[0;0]²`` re-shaped, or the addition LHS, on the
        safe region. Concretely: the Göpel LHS is a DEGREE-4 monomial product
        (four theta-nulls) whereas the addition LHS ``θ[a]θ[b]`` is DEGREE-2 (two
        nulls) and the duplication LHS ``θ[0;0]²`` is DEGREE-2 — so the Göpel LHS
        cannot equal either (different total theta-degree). We verify this exactly by
        a lattice comparison: the Göpel LHS differs from the duplication LHS lattice
        and from every checked addition LHS lattice. Returns ``True`` iff distinct
        from both."""
        if not isinstance(box, int) or box < 4:
            raise ValueError(f"box must be an int ≥ 4; got {box!r}")
        goepel_lhs = cls.goepel_lhs(box)               # degree-4 (four nulls)
        # vs duplication LHS θ[0;0]² (degree-2): must differ
        dup_lhs = cls.duplication_lhs(box)
        if goepel_lhs == dup_lhs:
            return False
        # vs every addition LHS θ[a]·θ[b] (degree-2): must differ
        for a1 in (0, 1):
            for a2 in (0, 1):
                for b1 in (0, 1):
                    for b2 in (0, 1):
                        add_lhs = cls.addition_lhs((a1, a2), (b1, b2), box)
                        if goepel_lhs == add_lhs:
                            return False
        return True

    # ── (B) the SYMBOLIC Rosenhain λ-map (formal theta-null ratios, NOT numbers) ─

    @classmethod
    def rosenhain_lambda_map(cls) -> "Dict[str, Dict[str, object]]":
        """The genus-2 SYMBOLIC Rosenhain λ-map — the 3 Rosenhain moduli
        ``(λ₁, λ₂, λ₃)`` of the curve ``y² = x(x−1)(x−λ₁)(x−λ₂)(x−λ₃)`` expressed as
        FORMAL theta-null RATIOS (NOT numerical values).

        Each Rosenhain modulus is a CROSS-RATIO of branch points (Eilers,
        arXiv:1707.08855, Cor 2.4 eq 2.18; Rosenhain's modular representation, eqs
        1.4–1.7): for the curve normalized with branch points ``{e₁,…,e₆}`` (here
        ``e₁=0, e₂=1, e₆=∞`` and ``e₃,e₄,e₅`` the three moduli), the cross-ratio of
        four branch points equals a ratio of squared even theta-NULLS

            (e_l − e_m)/(e_k − e_m) = ± θ²[ε(k,S)]·θ²[ε(k,T)]
                                        / ( θ²[ε(l,S)]·θ²[ε(l,T)] )

        where ``S, T`` are disjoint index pairs, ``m`` the remaining index, and
        ``ε(·)`` the η-map :meth:`branch_set_characteristic`. Each λ is represented
        SYMBOLICALLY as a theta-null-ratio object — a dict with

            ``num`` : the list of even-null characteristics in the NUMERATOR
                      (the product of squared nulls θ²[·]θ²[·]),
            ``den`` : the list of even-null characteristics in the DENOMINATOR,
            ``branch_indices`` : the (k, l, m, S, T) branch-point index data,
            ``cross_ratio`` : the symbolic cross-ratio string it equals.

        This is a FORMAL exact-q-series-ratio DEFINITION (the numerator / denominator
        are :meth:`lattice`-computable exact-integer products), NOT a number: turning
        it into a NUMERICAL λ requires evaluating the theta-nulls at the curve's
        TRANSCENDENTAL period matrix Ω — the documented operand-side OPEN
        (:meth:`rosenhain_branch_point_recovery_is_open`). All characteristics here
        are EVEN (verified by :meth:`rosenhain_lambda_map_is_well_formed`).

        Branch-point labelling: ``e₁=0`` (idx 1), ``e₂=1`` (idx 2), ``e₃=λ₁`` (idx 3),
        ``e₄=λ₂`` (idx 4), ``e₅=λ₃`` (idx 5), ``e₆=∞`` (idx 6). λᵢ = e_{i+2} is the
        cross-ratio ``(e_{i+2} − e₁)/(e_{i+2} − e₆ … )`` made finite by the η-map;
        we use the symmetric cross-ratio ``λᵢ = (e_{i+2} − 0)/( (e_{i+2}) ) ·`` … —
        concretely the Eilers Cor 2.4 assignment with ``k = i+2``, ``l = 2`` (the
        ``e₂=1`` normaliser), ``m = 1`` (the ``e₁=0`` normaliser), and ``S, T`` the
        two disjoint pairs from the remaining finite indices.

        DISCIPLINE: returns the SYMBOLIC ratio object; NEVER a numerical λ (the rc72
        review lesson — the transcendental period map is not on any decision path)."""
        lam: Dict[str, Dict[str, object]] = {}
        # λᵢ = e_{i+2}; normalise with m=1 (e₁=0), l=2 (e₂=1); k=i+2. The remaining
        # finite indices {3,4,5}\{k} ∪ {2}-ish split into the disjoint pairs S, T.
        # Per Eilers Cor 2.4 (eq 2.18): the cross-ratio (e_l−e_m)/(e_k−e_m) equals
        # θ²{k,S}θ²{k,T} / (θ²{l,S}θ²{l,T}) with S,T,k,l,m mutually disjoint, S∪T∪
        # {k,l,m} ⊆ the finite branch indices. For g=2 the finite indices are
        # {1,2,3,4,5}; S,T are the two leftover single indices (|S|=|T|=1).
        for i, k in ((1, 3), (2, 4), (3, 5)):
            l, m = 2, 1
            rest = [j for j in (1, 2, 3, 4, 5) if j not in (k, l, m)]
            # rest has exactly 2 entries → S, T (Eilers Cor 2.4: |S|=|T|=1)
            s_idx, t_idx = rest[0], rest[1]
            num = [cls.branch_set_characteristic((k, s_idx)),
                   cls.branch_set_characteristic((k, t_idx))]
            den = [cls.branch_set_characteristic((l, s_idx)),
                   cls.branch_set_characteristic((l, t_idx))]
            lam[f"lambda{i}"] = {
                "num": num,                       # θ²[·]θ²[·] numerator chars
                "den": den,                       # θ²[·]θ²[·] denominator chars
                "branch_indices": {"k": k, "l": l, "m": m,
                                   "S": s_idx, "T": t_idx},
                "cross_ratio": f"(e{l} - e{m})/(e{k} - e{m})",
            }
        return lam

    @classmethod
    def rosenhain_lambda_map_is_well_formed(cls) -> bool:
        """Verifies the SYMBOLIC Rosenhain λ-map is structurally correct (the exact,
        formal part that IS checkable without the transcendental Ω):

          * all numerator / denominator characteristics are EVEN theta-nulls (a
            Rosenhain cross-ratio is a ratio of squared EVEN nulls — Eilers Cor 2.4);
          * each λᵢ uses the correct η-map characteristics ``ε(k,S), ε(k,T)`` /
            ``ε(l,S), ε(l,T)`` for its branch-index data (the assignment matches
            :meth:`branch_set_characteristic` exactly — no fabricated characteristic);
          * the three λᵢ use DISTINCT k indices (the three distinct moduli e₃,e₄,e₅).

        Returns ``True`` iff well-formed. (This is the exact, formal consistency — it
        does NOT evaluate any theta-null at a numerical Ω; see
        :meth:`rosenhain_branch_point_recovery_is_open` for the OPEN.)"""
        lam = cls.rosenhain_lambda_map()
        if set(lam) != {"lambda1", "lambda2", "lambda3"}:
            return False
        ks = set()
        for name, obj in lam.items():
            bi = obj["branch_indices"]                 # type: ignore[index]
            k, l = bi["k"], bi["l"]                     # type: ignore[index]
            s_idx, t_idx = bi["S"], bi["T"]            # type: ignore[index]
            ks.add(k)
            # the characteristics must match the η-map exactly (no fabrication)
            want_num = [cls.branch_set_characteristic((k, s_idx)),
                        cls.branch_set_characteristic((k, t_idx))]
            want_den = [cls.branch_set_characteristic((l, s_idx)),
                        cls.branch_set_characteristic((l, t_idx))]
            if obj["num"] != want_num or obj["den"] != want_den:  # type: ignore[index]
                return False
            # every characteristic in the ratio is an EVEN theta-null
            for ch in want_num + want_den:
                (epp, eps) = ch
                if (epp[0] * eps[0] + epp[1] * eps[1]) % 2 != 0:
                    return False
        return len(ks) == 3                            # three distinct moduli

    # ── (C) the documented operand-side OPEN ────────────────────────────────────

    @staticmethod
    def rosenhain_branch_point_recovery_is_open() -> str:
        """The DOCUMENTED operand-side OPEN: recovering NUMERICAL branch points / a
        numerical Rosenhain modulus λ from the theta-nulls at a curve's period matrix
        Ω is NOT a finite exact (representable) operation — it needs the
        TRANSCENDENTAL period map (the theta-nulls evaluated at the curve's Ω ∈ H₂,
        which is transcendental and only knowable to N digits = float on the decision
        path). The carrier therefore provides the SYMBOLIC λ-map (formal theta-null
        ratios — :meth:`rosenhain_lambda_map`) and the FORMAL Göpel syzygy
        (:meth:`goepel_holds`), both exact for ALL Ω, but REFUSES to fabricate a
        numerical λ (the rc72 review lesson). Returns the honest OPEN statement (a
        documentation string), never a number."""
        return (
            "OPEN (operand-side, transcendental period map): the numerical "
            "branch-point / Rosenhain-λ recovery — evaluating the genus-2 even "
            "theta-nulls at the curve's transcendental period matrix Ω ∈ H₂ and "
            "reading off exact-ℚ branch points (Thomae's formula, Eilers Cor 2.4) "
            "— is NOT a finite exact carrier operation. It requires the "
            "transcendental theta evaluation at Ω (only knowable to N digits = "
            "float on the decision path), which the discipline forbids. The carrier "
            "provides the FORMAL exact content (the symbolic theta-null-ratio λ-map "
            "+ the Frobenius/Göpel syzygy, both exact for ALL Ω); the numerical "
            "λ-recovery is the documented operand-side OPEN — the framework refuses "
            "to fabricate a number here."
        )


def _native_g3():
    """The native ``_native`` module IF the rc75 ``srmech_riemann_theta_g3`` peer is
    present and bound, else ``None`` — so the genus-3 carrier dispatches the
    exact-integer ``(A₁,A₂,A₃,C₁₂,C₁₃,C₂₃)`` sextuple lattice to C when available and
    falls cleanly to the pure-Python body (the complete alternative + the parity
    oracle). Imported lazily to avoid a bootstrap cycle."""
    try:
        from . import _native as nat
    except ImportError:
        return None
    probe = getattr(nat, "has_native_riemann_theta_g3", None)
    return nat if (probe is not None and probe()) else None


class RiemannThetaG3:
    """A numpy-free EXACT genus-3 Riemann theta-CONSTANT

        θ[ε'; ε](0 | Ω) = Σ_{n ∈ ℤ³} (−1)^{ε·n} · Q₁^{A₁} Q₂^{A₂} Q₃^{A₃}
                                       · Q₁₂^{C₁₂} Q₁₃^{C₁₃} Q₂₃^{C₂₃} ,
        Aᵢ = (2nᵢ+ε'ᵢ)² ,   C_ij = (2nᵢ+ε'ᵢ)(2nⱼ+ε'ⱼ)   (THREE cross-terms, denom 4)

    — the NEXT RUNG of the GENUS axis (genus 3; the genus-3 analog of the rc72
    genus-2 :class:`RiemannTheta`). Immutable. Holds the binary characteristic
    ``[ε'; ε]`` (six bits in ``{0,1}``; the doubled half-integer characteristic over
    ``Ω ∈ H₃``, the genus-3 Siegel upper half space, ``Ω`` symmetric 3×3, dim
    ``g(g+1)/2 = 6``).

    THE OBJECT (Grushevsky, "The Schottky Problem", arXiv:1009.0369, eq. (1), the
    Riemann theta on the Siegel space ``H_g``; the genus-3 specialization ``g = 3``).
    There are **64 binary characteristics — 36 EVEN + 28 ODD** (Grushevsky p.: "there
    are ``2^{g-1}(2^g+1)`` even theta constants" → ``g=3`` gives ``4·9 = 36`` even and
    ``4·7 = 28`` odd; the empty-set even null ``[0,0,0;0,0,0]`` is the distinguished
    singular one). A characteristic is even iff ``ε'·ε ≡ 0 (mod 2)``.

    EXACT NOME-LATTICE REPRESENTATION (no float on the decision path). The carrier
    represents the theta-CONSTANT (``z = 0``) as an EXACT INTEGER exponent lattice
    over the nome alphabet (3 diagonal nomes + 3 cross-terms — vs genus-2's ONE
    cross-term, **the hardest part of genus 3**)

        q₁=e^{iπΩ₁₁}, q₂=e^{iπΩ₂₂}, q₃=e^{iπΩ₃₃} ,
        q₁₂=e^{2iπΩ₁₂}, q₁₃=e^{2iπΩ₁₃}, q₂₃=e^{2iπΩ₂₃} ,

    cleared to integer exponents in the QUARTER-nome base ``Qᵢ = qᵢ^{1/4}``,
    ``Q_ij = q_ij^{1/4}``. With ``mᵢ = nᵢ + ½ε'ᵢ`` the quadratic form ``mᵀΩm`` over
    ``iπ`` expands as ``Σᵢ mᵢ²Ωᵢᵢ + 2Σ_{i<j} mᵢmⱼΩᵢⱼ`` and clearing the half-integers
    gives a term ``Π Qᵢ^{Aᵢ} · Π Q_ij^{C_ij} · (−1)^{ε·n}`` with EXACT INTEGER
    exponents ``Aᵢ = (2nᵢ+ε'ᵢ)²`` and ``C_ij = (2nᵢ+ε'ᵢ)(2nⱼ+ε'ⱼ)``. Each cross-term
    ``C_ij`` is a PRODUCT of two half-integers → a denominator-4 integer-lattice
    clearing, now across THREE coupled pairs (the genuinely-new genus-3 content). The
    lattice is truncated to a box ``|nᵢ| ≤ box`` → ``(2·box+1)³`` monomial terms; each
    lattice coefficient is an exact INTEGER (a sum of ``±1`` lattice counts). The sign
    ``(−1)^{ε·n}`` is the **Class-K** pin-slot (an explicit ``±1`` branch, never an ALU
    ``abs()``).

    THE BUILD GATES (the genus-3 analogs of rc72's genus-2 first rung):

      * **collapse g3→g2 (primary):** :meth:`collapse_g2` of the trivial even
        characteristic ``[0,0,0; 0,0,0]`` collapses EXACTLY to the rc72 genus-2
        :class:`RiemannTheta` ``[0,0; 0,0]`` (set ``n₃ = 0``, ``q₃ = q₁₃ = q₂₃ = 1``,
        ``ε'₃ = ε₃ = 0``) — bit-exact vs the existing rung; and the all-trivial chain
        ``→`` genus-1 θ₃ (:meth:`collapse_g1_q_series`). A characteristic with a
        NON-trivial 3rd component HONESTLY REFUSES to collapse (raises — the rc72
        collapse pattern, an honest boundary, not a fabricated reduction). THE
        foundation gate.

      * **formal genus-3 theta-null identity (secondary):** the genus-3 Gauss /
        duplication identity

            θ[0;0](0 | Ω)²  =  Σ_{c ∈ (½ℤ³/ℤ³)} θ[c; 0](0 | 2Ω)²     (8 summands)

        (Chai, "Riemann's theta formula" (2014), Thm 1.2 example (b), the
        ``a = b = 0``, ``z = w = 0`` specialization of the generalized Riemann theta
        identity, valid for ALL ``g`` — the ``2^{-g}`` sum over ``c ∈ 2^{-1}ℤ^g/ℤ^g``;
        for ``g = 3`` the eight ``c ∈ {0,½}³``; classically Mumford, *Tata Lectures
        on Theta I* (1983), the genus-g duplication). It holds for ALL ``Ω`` —
        exactly checkable as a truncated exact-integer multivariate q-series, NO
        transcendental evaluation. The eight ``θ[c; 0]`` include the (½,½,½) and mixed
        characteristics with ``C₁₃ ≠ 0``/``C₂₃ ≠ 0``, so the identity genuinely
        exercises ALL THREE cross-terms — it proves the carrier computes genuine
        genus-3 theta-constants, not just the genus-2 / genus-1 slice. See
        :meth:`duplication_lhs` / :meth:`duplication_rhs` / :meth:`duplication_holds`.

    THE GENUS-3 NEW STRUCTURE (the honest boundary; the full op is rc76, NOT this
    rung). Unlike genus 2 (where EVERY curve is hyperelliptic), the GENERIC genus-3
    curve is NON-hyperelliptic (a smooth plane quartic); the HYPERELLIPTIC locus is
    cut out by a VANISHING even theta-null (an Igusa-type modular form vanishing on
    the hyperelliptic locus — Poor [Poo96], Grushevsky arXiv:1009.0369 Thm 3.9/5.2).
    The numerical "is this Ω hyperelliptic" test is a POINT-EVALUATION of a theta-null
    at a transcendental Ω → NOT a finite exact carrier op → the operand-side OPEN
    (:meth:`hyperelliptic_locus_is_open` — the rc74
    ``rosenhain_branch_point_recovery_is_open`` pattern).

    THE REPRESENTABILITY BOUNDARY / SCHOTTKY. The carrier is REPRESENTABLE (a finite
    exact decision): the canonical nome-monomial form + the finite Riemann relations,
    box pinned by the polarization level. **Genus 3 is STILL CLEAN** for the Schottky
    problem (``dim M₃ = 3g−3 = 6 = g(g+1)/2 = dim A₃``; ``J₃ = A₃^ind`` — every
    indecomposable genus-3 ppav is a Jacobian, Grushevsky arXiv:1009.0369 p.: "the
    dimensions coincide for ``g ≤ 3``, and in fact the Jacobian locus ``J_g`` is equal
    to ``A_g^ind`` iff ``g ≤ 3``"). The Schottky FRONTIER OPEN stays at ``g ≥ 4``
    (``g = 4`` is Schottky's case; ``g ≥ 5`` genuinely open).

    Construct via :meth:`theta_constant` (the public entry). ``box`` (the lattice-box
    truncation ``|nᵢ| ≤ box``) is the finite generating rule, pinned by the requested
    truncation degree."""

    __slots__ = ("_ep1", "_ep2", "_ep3", "_e1", "_e2", "_e3")

    def __init__(self, ep1: int, ep2: int, ep3: int,
                 e1: int, e2: int, e3: int) -> None:
        self._ep1 = _bit("ε'₁", ep1)
        self._ep2 = _bit("ε'₂", ep2)
        self._ep3 = _bit("ε'₃", ep3)
        self._e1 = _bit("ε₁", e1)
        self._e2 = _bit("ε₂", e2)
        self._e3 = _bit("ε₃", e3)

    # ── construction ──────────────────────────────────────────────────────────
    @classmethod
    def theta_constant(cls, eps_prime: Tuple[int, int, int],
                       eps: Tuple[int, int, int]) -> "RiemannThetaG3":
        """The genus-3 theta-constant ``θ[ε'; ε](0 | Ω)`` for a binary characteristic
        ``[ε'; ε]`` — ``eps_prime = (ε'₁, ε'₂, ε'₃)`` (the upper / lattice-shift
        half-integer characteristic) and ``eps = (ε₁, ε₂, ε₃)`` (the lower / sign
        characteristic), each entry in ``{0, 1}``. The trivial even characteristic is
        ``theta_constant((0,0,0), (0,0,0))`` (= θ[0;0], the singular even null that
        collapses to the genus-2 trivial null and on to θ₃)."""
        return cls(eps_prime[0], eps_prime[1], eps_prime[2],
                   eps[0], eps[1], eps[2])

    @classmethod
    def even_characteristics(cls) -> "List[RiemannThetaG3]":
        """The 36 EVEN genus-3 theta-constants (the even theta-nulls): all 64 binary
        characteristics ``[ε'; ε]`` with ``ε'·ε ≡ 0 (mod 2)`` (Grushevsky: ``2^{g-1}
        (2^g+1) = 36`` even). The order is deterministic (lexicographic in
        ``ε'₁ε'₂ε'₃ε₁ε₂ε₃``)."""
        out: List[RiemannThetaG3] = []
        for ep1 in (0, 1):
            for ep2 in (0, 1):
                for ep3 in (0, 1):
                    for e1 in (0, 1):
                        for e2 in (0, 1):
                            for e3 in (0, 1):
                                if (ep1 * e1 + ep2 * e2 + ep3 * e3) % 2 == 0:
                                    out.append(cls(ep1, ep2, ep3, e1, e2, e3))
        return out

    # ── accessors ─────────────────────────────────────────────────────────────
    @property
    def characteristic(self) -> "Tuple[Tuple[int, int, int], Tuple[int, int, int]]":
        """The binary characteristic ``((ε'₁, ε'₂, ε'₃), (ε₁, ε₂, ε₃))``."""
        return ((self._ep1, self._ep2, self._ep3),
                (self._e1, self._e2, self._e3))

    @property
    def is_even(self) -> bool:
        """True iff the characteristic is EVEN (``ε'·ε ≡ 0 mod 2``) — i.e. an even
        theta-null. 36 of the 64 are even."""
        return (self._ep1 * self._e1 + self._ep2 * self._e2
                + self._ep3 * self._e3) % 2 == 0

    @property
    def genus(self) -> int:
        """The genus — 3 for this carrier (the next rung of the genus axis)."""
        return 3

    # ── the exact integer exponent lattice (the representable core) ────────────
    def lattice(self, box: int) -> "Dict[_Sextuple, int]":
        """The EXACT INTEGER exponent lattice ``{(A₁,A₂,A₃,C₁₂,C₁₃,C₂₃): coeff}`` of
        the genus-3 theta-constant, truncated to the box ``|nᵢ| ≤ box`` — the carrier's
        representable core. ``Aᵢ = (2nᵢ+ε'ᵢ)²`` are the diagonal integer exponents in
        the quarter-nome base ``Qᵢ``; ``C_ij = (2nᵢ+ε'ᵢ)(2nⱼ+ε'ⱼ)`` are the THREE
        cross-term exponents (each the genus-3 denominator-4 clearing of a half-integer
        product); ``coeff`` is the exact integer ``Σ (−1)^{ε·n}`` over the ``n``
        landing on that monomial. DISPATCHES to the native ``srmech_riemann_theta_g3``
        C peer when loaded (a 1:1 exact-integer mirror — the C lattice EQUALS the
        Python lattice, trusted only on a native hit); else the pure-Python
        :meth:`_lattice_py` body (the COMPLETE alternative + the parity oracle). No
        float, no ``abs()`` (the ``(−1)^{ε·n}`` sign is the Class-K pin-slot), no
        numpy / ``math``."""
        if not isinstance(box, int) or box < 0:
            raise ValueError(f"box must be a non-negative int; got {box!r}")
        nat = _native_g3()
        if nat is not None:
            try:
                got = nat.riemann_theta_g3_lattice_c(
                    self._ep1, self._ep2, self._ep3,
                    self._e1, self._e2, self._e3, box)
                if got is not None:
                    return got
            except (RuntimeError, OverflowError, ValueError):
                pass   # fall to the pure path
        return self._lattice_py(box)

    def _lattice_py(self, box: int) -> "Dict[_Sextuple, int]":
        """The COMPLETE pure-Python exponent lattice (the parity oracle for the C
        peer): exact integer ``(A₁,A₂,A₃,C₁₂,C₁₃,C₂₃) → coeff`` over the box
        ``|nᵢ| ≤ box``. Each cross-term ``C_ij = (2nᵢ+ε'ᵢ)(2nⱼ+ε'ⱼ)`` is the genus-3
        denominator-4 clearing; the sign ``(−1)^{ε·n}`` is the Class-K pin-slot (an
        explicit ``+1/−1`` branch, never an ALU ``abs()``). A bounded triple loop over
        the box (JPL Rule 2)."""
        ep1, ep2, ep3 = self._ep1, self._ep2, self._ep3
        e1, e2, e3 = self._e1, self._e2, self._e3
        out: Dict[_Sextuple, int] = {}
        for n1 in range(-box, box + 1):
            u1 = 2 * n1 + ep1
            for n2 in range(-box, box + 1):
                u2 = 2 * n2 + ep2
                for n3 in range(-box, box + 1):
                    u3 = 2 * n3 + ep3
                    a1 = u1 * u1
                    a2 = u2 * u2
                    a3 = u3 * u3
                    c12 = u1 * u2
                    c13 = u1 * u3
                    c23 = u2 * u3
                    # the per-term sign (−1)^{ε·n}: Class-K pin-slot (a stored ±1)
                    parity = (e1 * n1 + e2 * n2 + e3 * n3) % 2
                    sign = 1 if parity == 0 else -1   # never abs(); explicit ± branch
                    key = (a1, a2, a3, c12, c13, c23)
                    out[key] = out.get(key, 0) + sign
        return {k: v for k, v in out.items() if v != 0}

    # ── the genus-2 collapse (the foundation gate) ────────────────────────────
    def collapse_g2(self) -> "RiemannTheta":
        """The genus-2 COLLAPSE (the primary foundation gate): set ``Ω₃₃ = Ω₁₃ =
        Ω₂₃ = 0`` (⇒ ``q₃ = q₁₃ = q₂₃ = 1``) and ``n₃ = 0`` (drop the third lattice
        direction). For the trivial even characteristic ``[0,0,0; 0,0,0]`` the
        surviving slice is the genus-2 trivial theta-null, returned as the rc72
        :class:`RiemannTheta` ``[0,0; 0,0]`` (so the collapse is BIT-EXACT vs the
        existing rung — see the build gate; verify with
        :meth:`collapse_g2_lattice_matches`). Only the trivial even characteristic
        ``[0,0,0; 0,0,0]`` collapses to the plain genus-2 trivial null; any
        characteristic with a NON-trivial 3rd component (``ε'₃`` or ``ε₃`` set) is
        rejected — its genus-2 slice is a shifted/signed theta, not the plain rung (an
        honest boundary, not a fabricated reduction — the rc72 collapse pattern)."""
        if (self._ep1, self._ep2, self._ep3,
                self._e1, self._e2, self._e3) != (0, 0, 0, 0, 0, 0):
            raise ValueError(
                "collapse_g2 is the genus-2 foundation gate: only the trivial even "
                "characteristic [0,0,0; 0,0,0] collapses to the rc72 genus-2 trivial "
                f"theta-null. The characteristic {self.characteristic} has a "
                "non-trivial 3rd / signed component (a shifted/signed theta), not the "
                "plain genus-2 rung — an honest boundary, not a fabricated reduction.")
        return RiemannTheta(0, 0, 0, 0)

    def collapse_g2_lattice_matches(self, box: int = 4) -> bool:
        """PROVES the genus-2 collapse is GENUINE — it derives from the genus-3 lattice
        itself, not a hardcoded return. The genus-2 degeneration ``q₃ → 0`` /
        ``q₁₃, q₂₃ → 1`` keeps ONLY the ``n₃ = 0`` slice (for the trivial
        characteristic ``A₃ = (2n₃)² = 0 ⟺ n₃ = 0``, and then ``C₁₃ = C₂₃ = 0``
        automatically), so projecting the genus-3 trivial lattice onto its
        ``A₃ = C₁₃ = C₂₃ = 0`` slice and reading ``(A₁, A₂, C₁₂)`` reproduces the rc72
        genus-2 trivial lattice EXACTLY. Returns ``True`` iff bit-exact (the no-shell
        collapse proof). Pure exact-integer comparison, no float."""
        if not isinstance(box, int) or box < 0:
            raise ValueError(f"box must be a non-negative int; got {box!r}")
        if (self._ep1, self._ep2, self._ep3,
                self._e1, self._e2, self._e3) != (0, 0, 0, 0, 0, 0):
            raise ValueError(
                "collapse_g2_lattice_matches is the trivial-null foundation gate; "
                f"the characteristic {self.characteristic} does not collapse.")
        g3 = self.lattice(box)
        projected: Dict[_Triple, int] = {}
        for (a1, a2, a3, c12, c13, c23), v in g3.items():
            if a3 == 0 and c13 == 0 and c23 == 0:        # the n₃ = 0 slice
                key = (a1, a2, c12)
                projected[key] = projected.get(key, 0) + v
        projected = {k: v for k, v in projected.items() if v != 0}
        g2 = RiemannTheta(0, 0, 0, 0).lattice(box)
        return projected == g2

    def collapse_g1_q_series(self, N: int) -> "List[int]":
        """The all-trivial genus-3 → genus-1 collapse's exact INTEGER q-series to order
        ``N``: ``[1, 2, 0, 0, 2, …]`` = ``θ₃``. The chain is genus-3 → genus-2
        (:meth:`collapse_g2`) → genus-1 (the rc72
        :meth:`RiemannTheta.collapse_g1_q_series`); bit-exact vs the rc70 θ₃ rung. Only
        the trivial even characteristic collapses the whole way (else
        :meth:`collapse_g2` raises — the honest boundary)."""
        return self.collapse_g2().collapse_g1_q_series(N)

    # ── equality / repr ───────────────────────────────────────────────────────
    def __eq__(self, other) -> bool:
        if isinstance(other, RiemannThetaG3):
            return ((self._ep1, self._ep2, self._ep3,
                     self._e1, self._e2, self._e3)
                    == (other._ep1, other._ep2, other._ep3,
                        other._e1, other._e2, other._e3))
        return NotImplemented

    def __ne__(self, other):
        r = self.__eq__(other)
        return r if r is NotImplemented else (not r)

    def __hash__(self) -> int:
        return hash((self._ep1, self._ep2, self._ep3,
                     self._e1, self._e2, self._e3))

    def __repr__(self) -> str:
        return (f"RiemannThetaG3(genus=3, "
                f"eps_prime=({self._ep1},{self._ep2},{self._ep3}), "
                f"eps=({self._e1},{self._e2},{self._e3}), even={self.is_even})")

    # ── the formal genus-3 theta-null identity gate (Gauss duplication) ────────
    @staticmethod
    def _square_lattice(lat: "Dict[_Sextuple, int]") -> "Dict[_Sextuple, int]":
        """The exact-integer square ``lat · lat`` of a genus-3
        ``(A₁,A₂,A₃,C₁₂,C₁₃,C₂₃) → coeff`` lattice (a bounded convolution over the
        exponent sextuples; JPL Rule 2). All-integer, no float."""
        out: Dict[_Sextuple, int] = {}
        items = list(lat.items())
        for k1, v1 in items:
            for k2, v2 in items:
                key = (k1[0] + k2[0], k1[1] + k2[1], k1[2] + k2[2],
                       k1[3] + k2[3], k1[4] + k2[4], k1[5] + k2[5])
                out[key] = out.get(key, 0) + v1 * v2
        return {k: v for k, v in out.items() if v != 0}

    @staticmethod
    def _double_exps(lat: "Dict[_Sextuple, int]") -> "Dict[_Sextuple, int]":
        """Re-express a genus-3 lattice computed at ``2Ω`` in the ``Ω``-nome alphabet:
        every quarter-nome exponent DOUBLES (``Qᵢ(2Ω) = Qᵢ(Ω)²``), so the whole
        sextuple ``↦ 2·sextuple``. Exact integer relabel, no float."""
        return {tuple(2 * x for x in k): v for k, v in lat.items()}  # type: ignore[misc]

    @classmethod
    def duplication_lhs(cls, box: int) -> "Dict[_Sextuple, int]":
        """The LEFT side of the genus-3 Gauss/duplication theta-null identity
        ``θ[0; 0](0 | Ω)²`` (in the ``Ω`` quarter-nome alphabet) — the exact-integer
        square of the trivial even theta-constant's genus-3 lattice. See
        :meth:`duplication_holds`."""
        t000 = cls.theta_constant((0, 0, 0), (0, 0, 0)).lattice(box)
        return cls._square_lattice(t000)

    @classmethod
    def duplication_rhs(cls, box: int) -> "Dict[_Sextuple, int]":
        """The RIGHT side of the genus-3 Gauss/duplication theta-null identity
        ``Σ_{c ∈ (½ℤ³/ℤ³)} θ[c; 0](0 | 2Ω)²`` (re-expressed in the ``Ω`` quarter-nome
        alphabet via :meth:`_double_exps`, since each summand is at ``2Ω``). The EIGHT
        ``c`` are the half-characteristics ``{0,1}³`` (upper char ``c``, lower char
        ``0`` — all even). See :meth:`duplication_holds`."""
        rhs: Dict[_Sextuple, int] = {}
        for c1 in (0, 1):
            for c2 in (0, 1):
                for c3 in (0, 1):
                    tc = cls.theta_constant((c1, c2, c3), (0, 0, 0)).lattice(box)
                    tc2 = cls._double_exps(tc)         # the summand is at 2Ω
                    sq = cls._square_lattice(tc2)
                    for k, v in sq.items():
                        rhs[k] = rhs.get(k, 0) + v
        return {k: v for k, v in rhs.items() if v != 0}

    @classmethod
    def duplication_holds(cls, box: int = 4) -> bool:
        """The FORMAL genus-3 theta-null identity gate (the secondary build gate): the
        genus-3 Gauss / duplication identity

            θ[0; 0](0 | Ω)²  =  Σ_{c ∈ (½ℤ³/ℤ³)} θ[c; 0](0 | 2Ω)²     (8 summands)

        holds EXACTLY as a truncated exact-integer multivariate q-series, for ALL ``Ω``
        (no transcendental evaluation). The ``a = b = 0``, ``z = w = 0``, ``g = 3``
        specialization of the generalized Riemann theta identity (Chai, "Riemann's
        theta formula" (2014), Thm 1.2 example (b) — the ``2^{-g}`` sum over
        ``c ∈ 2^{-1}ℤ^g/ℤ^g``, here the eight ``c ∈ {0,½}³``; classically Mumford,
        *Tata Lectures on Theta I* (1983), the genus-g duplication). This compares the
        two sides on the SAFE INNER REGION the box ``|nᵢ| ≤ box`` provably resolves (a
        box-``box`` theta omits only terms with a diagonal quarter-nome exponent
        ``≥ 4(box+1)²``, so monomials with each ``Aᵢ, |C_ij| ≤ 4·box²`` are fully
        accumulated). Because the eight ``θ[c; 0]`` include the (½,½,½) and mixed
        characteristics with ``C₁₃ ≠ 0``/``C₂₃ ≠ 0``, the identity genuinely exercises
        ALL THREE cross-terms — it proves the carrier computes genuine genus-3
        theta-constants, not just the genus-2 / genus-1 slice. Returns ``True`` iff the
        two sides agree exactly on the safe region (and the region is non-trivially
        populated with a genuine genus-3 cross-term ``C₁₃`` or ``C₂₃`` monomial).

        A CARRIER METHOD (the carrier's own build gate), not a public module-level op —
        ``tools.total`` is unchanged (the rc72 ``duplication_holds`` precedent)."""
        if not isinstance(box, int) or box < 2:
            raise ValueError(
                f"box must be an int ≥ 2 for the duplication gate; got {box!r}")
        lhs = cls.duplication_lhs(box)
        rhs = cls.duplication_rhs(box)
        safe = 4 * box * box

        def restrict(lat: "Dict[_Sextuple, int]") -> "Dict[_Sextuple, int]":
            kept: Dict[_Sextuple, int] = {}
            for k, v in lat.items():
                a1, a2, a3, c12, c13, c23 = k
                # Class-K magnitudes, no abs()
                m12 = c12 if c12 >= 0 else -c12
                m13 = c13 if c13 >= 0 else -c13
                m23 = c23 if c23 >= 0 else -c23
                if (a1 <= safe and a2 <= safe and a3 <= safe
                        and m12 <= safe and m13 <= safe and m23 <= safe):
                    kept[k] = v
            return kept

        lhs_s = restrict(lhs)
        rhs_s = restrict(rhs)
        if lhs_s != rhs_s:
            return False
        # the gate must genuinely touch a 3-way (genus-3) cross-term C₁₃ or C₂₃ —
        # else only the genus-2 (C₁₂) slice would be exercised
        has_g3_cross = any((c13 != 0 or c23 != 0)
                           for (_a1, _a2, _a3, _c12, c13, c23) in lhs_s)
        return has_g3_cross

    # ── the documented operand-side OPEN (genus-3 new structure; full op = rc76) ─
    @classmethod
    def even_null_count(cls) -> "Tuple[int, int]":
        """The genus-3 even / odd theta-null counts ``(36, 28)`` — DERIVED from the
        enumeration (``2^{g-1}(2^g±1)`` for ``g = 3``: even ``4·9 = 36``, odd
        ``4·7 = 28``; Grushevsky arXiv:1009.0369). The distinguished singular even
        null is the empty-set characteristic ``[0,0,0; 0,0,0]`` (see
        :meth:`singular_even_null`). Exact integer, no float."""
        even = cls.even_characteristics()
        n_even = len(even)
        n_odd = 64 - n_even
        return (n_even, n_odd)

    @classmethod
    def singular_even_null(cls) -> "RiemannThetaG3":
        """The distinguished SINGULAR even theta-null — the empty-set characteristic
        ``[0,0,0; 0,0,0]`` (the trivial even null, the one that collapses to the
        genus-2 trivial null and on to θ₃). Among the 36 even nulls it is the
        distinguished one (Grushevsky / Igusa)."""
        return cls.theta_constant((0, 0, 0), (0, 0, 0))

    @staticmethod
    def hyperelliptic_locus_is_open() -> str:
        """The DOCUMENTED operand-side OPEN (the genus-3 NEW structure; the full
        numerical op is rc76, NOT this rung). Unlike genus 2 (where EVERY curve is
        hyperelliptic), the GENERIC genus-3 curve is NON-hyperelliptic (a smooth plane
        quartic); the HYPERELLIPTIC locus inside ``A₃`` is cut out by a VANISHING even
        theta-null — an Igusa-type modular form vanishing on the hyperelliptic locus
        (Poor [Poo96]; Grushevsky arXiv:1009.0369 Thm 3.9/5.2). DECIDING "is this Ω
        hyperelliptic" is a POINT-EVALUATION of that theta-null at a transcendental
        ``Ω ∈ H₃`` (only knowable to N digits = float on the decision path), which the
        discipline forbids → it is NOT a finite exact (representable) carrier
        operation. The carrier provides the FORMAL exact content (the genus-3 even-null
        enumeration :meth:`even_null_count`, the singular even null
        :meth:`singular_even_null`, the exact duplication relation
        :meth:`duplication_holds`) but REFUSES to fabricate a numerical hyperelliptic
        decision (the rc74 ``rosenhain_branch_point_recovery_is_open`` pattern).
        Returns the honest OPEN statement (a documentation string), never a verdict."""
        return (
            "OPEN (operand-side, transcendental period map): the numerical genus-3 "
            "HYPERELLIPTIC-locus decision — evaluating the vanishing even theta-null "
            "(the Igusa-type modular form that cuts out the hyperelliptic locus in A₃; "
            "Poor 1996, Grushevsky arXiv:1009.0369 Thm 3.9/5.2) at a curve's "
            "transcendental period matrix Ω ∈ H₃ and testing it against zero — is NOT "
            "a finite exact carrier operation. The GENERIC genus-3 curve is "
            "NON-hyperelliptic (a smooth plane quartic), unlike genus 2 where every "
            "curve is hyperelliptic; the hyperelliptic locus is a positive-codimension "
            "vanishing-null condition that needs the transcendental theta evaluation "
            "at Ω (only knowable to N digits = float on the decision path), which the "
            "discipline forbids. The carrier provides the FORMAL exact content (the "
            "36-even / 28-odd null enumeration, the singular even null, the genus-3 "
            "duplication relation, all exact for ALL Ω); the numerical "
            "hyperelliptic-decision is the documented operand-side OPEN — the "
            "framework refuses to fabricate a verdict here. (Schottky: genus 3 is "
            "STILL clean — dim M₃ = 6 = dim A₃, J₃ = A₃^ind; the Schottky frontier "
            "OPEN stays at g ≥ 4.)"
        )
