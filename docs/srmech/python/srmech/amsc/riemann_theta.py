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

__all__ = ["RiemannTheta"]

# the (A, B, C) integer exponent triple in the quarter-nome base
_Triple = Tuple[int, int, int]

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
