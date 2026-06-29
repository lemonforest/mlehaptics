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

__all__ = ["RiemannTheta", "RiemannThetaG3", "RiemannThetaG4", "SchottkyFormG4"]

# the (A, B, C) integer exponent triple in the quarter-nome base
_Triple = Tuple[int, int, int]

# the genus-3 (A₁, A₂, A₃, C₁₂, C₁₃, C₂₃) integer exponent SEXTUPLE — 3 diagonal
# nome exponents + the 3 cross-terms (vs genus-2's ONE cross-term); quarter-nome base
_Sextuple = Tuple[int, int, int, int, int, int]

# the genus-4 (A₁,A₂,A₃,A₄, C₁₂,C₁₃,C₁₄,C₂₃,C₂₄,C₃₄) integer exponent 10-TUPLE — 4
# diagonal nome exponents + the SIX cross-terms (vs genus-3's THREE cross-terms — the
# genus-4 scaling difficulty; one per pair {12,13,14,23,24,34}); quarter-nome base
_Tentuple = Tuple[int, int, int, int, int, int, int, int, int, int]

# a 2×2 integer matrix (a row-major tuple of 2-tuples) — the genus-2 building block
_Mat2 = Tuple[Tuple[int, int], Tuple[int, int]]
# an Sp(4, ℤ) element as the four 2×2 integer blocks (A, B, C, D)
_Sp4 = Tuple[_Mat2, _Mat2, _Mat2, _Mat2]

# a 3×3 integer matrix (a row-major tuple of 3-tuples) — the genus-3 building block
_Mat3 = Tuple[Tuple[int, int, int], Tuple[int, int, int], Tuple[int, int, int]]
# an Sp(6, ℤ) element as the four 3×3 integer blocks (A, B, C, D)
_Sp6 = Tuple[_Mat3, _Mat3, _Mat3, _Mat3]


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


def _iter_signs(k: int) -> "List[Tuple[int, ...]]":
    """All ``2^k`` sign tuples in ``{+1, −1}^k`` (for the E₈ half-integer-glue
    enumeration in :class:`SchottkyFormG4`). A bounded build (JPL Rule 2; ``k = 8`` →
    256 tuples), pure integer, no float / itertools on the decision path."""
    out: "List[Tuple[int, ...]]" = [()]
    for _ in range(k):
        out = [t + (s,) for t in out for s in (1, -1)]
    return out


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


def _native_g3_chi18():
    """The native ``_native`` module IF the rc76 ``srmech_riemann_theta_g3_chi18`` peer
    (Igusa's χ₁₈ leading-part = product of the 36 even theta-nulls) is present and bound,
    else ``None`` — so the genus-3 carrier dispatches the exact-integer χ₁₈ leading-part
    lattice to C when available and falls cleanly to the pure-Python body (the complete
    alternative + the parity oracle). Imported lazily to avoid a bootstrap cycle."""
    try:
        from . import _native as nat
    except ImportError:
        return None
    probe = getattr(nat, "has_native_riemann_theta_g3_chi18", None)
    return nat if (probe is not None and probe()) else None


def _native_g3_goepel():
    """The native ``_native`` module IF the rc78 ``srmech_riemann_theta_g3_goepel`` peer
    (the genus-3 Göpel/Frobenius quadratic theta-null syzygy gate) is present and bound,
    else ``None`` — so the genus-3 carrier dispatches the EXACT-INTEGER Göpel-syzygy
    equality decision (LHS == RHS on the safe region + a genuine genus-3 cross-term
    present) to C when available and falls cleanly to the pure-Python body (the complete
    alternative + the parity oracle). Imported lazily to avoid a bootstrap cycle."""
    try:
        from . import _native as nat
    except ImportError:
        return None
    probe = getattr(nat, "has_native_riemann_theta_g3_goepel", None)
    return nat if (probe is not None and probe()) else None


def _native_g4():
    """The native ``_native`` module IF the rc80 ``srmech_riemann_theta_g4`` peer is
    present and bound, else ``None`` — so the genus-4 carrier dispatches the
    exact-integer ``(A₁,A₂,A₃,A₄,C₁₂,C₁₃,C₁₄,C₂₃,C₂₄,C₃₄)`` 10-tuple lattice to C when
    available and falls cleanly to the pure-Python body (the complete alternative + the
    parity oracle). Imported lazily to avoid a bootstrap cycle."""
    try:
        from . import _native as nat
    except ImportError:
        return None
    probe = getattr(nat, "has_native_riemann_theta_g4", None)
    return nat if (probe is not None and probe()) else None


def _native_g4_schottky():
    """The native ``_native`` module IF the rc81 ``srmech_riemann_theta_g4_schottky`` peer
    (the genus-4 Schottky form J = θ⁴(E₈⊕E₈) − θ⁴(E₁₆) lattice-theta-difference
    representation-number COUNTER) is present and bound, else ``None`` — so the
    :class:`SchottkyFormG4` carrier dispatches the heavy exact-integer minimal-shell
    g-tuple representation count (the leading part of J) to C when available and falls
    cleanly to the pure-Python body (the complete alternative + the parity oracle).
    Imported lazily to avoid a bootstrap cycle."""
    try:
        from . import _native as nat
    except ImportError:
        return None
    probe = getattr(nat, "has_native_riemann_theta_g4_schottky", None)
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

    # ══════════════════════════════════════════════════════════════════════════
    # rc77 (A): the genus-3 Sp(6, ℤ) TRANSFORMATION (the modular action on the
    # genus-3 binary characteristic — the g=2→g=3 parametric extension of rc73's
    # Sp(4, ℤ) action; DLMF §21.5.9 holds for GENERAL genus g with g×g blocks).
    # ══════════════════════════════════════════════════════════════════════════

    # ── exact 3×3 integer matrix algebra (no numpy; integer / mod-2 only) ───────
    @staticmethod
    def _m3_matvec(m: "_Mat3", v: "Tuple[int, int, int]") -> "List[int]":
        """The exact integer matrix·vector ``M·v`` for a 3×3 ``M`` and a length-3
        ``v`` (a bounded 3×3 multiply — JPL Rule 2). All-integer, no float."""
        return [m[r][0] * v[0] + m[r][1] * v[1] + m[r][2] * v[2] for r in range(3)]

    @staticmethod
    def _m3_matmul(p: "_Mat3", q: "_Mat3") -> "_Mat3":
        """The exact integer 3×3 matrix product ``P·Q``. All-integer, no float."""
        return tuple(  # type: ignore[return-value]
            tuple(p[i][0] * q[0][j] + p[i][1] * q[1][j] + p[i][2] * q[2][j]
                  for j in range(3))
            for i in range(3))

    @staticmethod
    def _m3_transpose(m: "_Mat3") -> "_Mat3":
        """The exact 3×3 transpose ``Mᵀ``."""
        return tuple(tuple(m[r][c] for r in range(3))  # type: ignore[return-value]
                     for c in range(3))

    @staticmethod
    def _m3_add(p: "_Mat3", q: "_Mat3") -> "_Mat3":
        """The exact 3×3 sum ``P + Q``."""
        return tuple(tuple(p[i][j] + q[i][j] for j in range(3))  # type: ignore[return-value]
                     for i in range(3))

    @classmethod
    def _m3_diag_of_prod(cls, p: "_Mat3", q: "_Mat3") -> "List[int]":
        """``diag(P·Qᵀ)`` as a length-3 vector — the diagonal of ``P·Qᵀ`` (the
        ``½diag[C·Dᵀ]`` / ``½diag[A·Bᵀ]`` terms of the Igusa genus-3 characteristic
        transformation, returned UN-halved as the integer ``diag(P·Qᵀ)`` since the
        doubled-half-integer characteristic absorbs the ½). Exact integer
        (``diag(P·Qᵀ)_i = Σ_k P[i][k]·Q[i][k]`` — the row-row dot)."""
        return [p[i][0] * q[i][0] + p[i][1] * q[i][1] + p[i][2] * q[i][2]
                for i in range(3)]

    @staticmethod
    def _i3() -> "_Mat3":
        """The 3×3 identity matrix (the genus-3 ``I``)."""
        return ((1, 0, 0), (0, 1, 0), (0, 0, 1))

    @staticmethod
    def _z3() -> "_Mat3":
        """The 3×3 zero matrix (the genus-3 ``0`` block)."""
        return ((0, 0, 0), (0, 0, 0), (0, 0, 0))

    # ── the standard Sp(6, ℤ) generators ───────────────────────────────────────
    @classmethod
    def sp6_translation(cls, b: "_Mat3") -> "_Sp6":
        """The Sp(6, ℤ) TRANSLATION generator ``γ = [[I, B], [0, I]]`` for a SYMMETRIC
        integer 3×3 ``B`` (the genus-3 ``Ω ↦ Ω+B`` shift — DLMF §21.5, the general-g
        translation). ``B`` must be symmetric (else not symplectic) — rejected loudly
        otherwise. Returned as the four 3×3 blocks ``(A, B, C, D) = (I, B, 0, I)``."""
        b = cls._coerce_mat3(b, "B")
        for i in range(3):
            for j in range(i + 1, 3):
                if b[i][j] != b[j][i]:
                    raise ValueError(
                        "the translation block B must be SYMMETRIC (Sp(6,ℤ) "
                        f"condition); got B = {b!r} (B[{i}][{j}]={b[i][j]} ≠ "
                        f"B[{j}][{i}]={b[j][i]})")
        return (cls._i3(), b, cls._z3(), cls._i3())

    @classmethod
    def sp6_gl_twist(cls, a: "_Mat3") -> "_Sp6":
        """The Sp(6, ℤ) GL-TWIST generator ``γ = [[A, 0], [0, (Aᵀ)⁻¹]]`` for
        ``A ∈ GL(3, ℤ)`` (the genus-3 basis change ``θ(Az | A Ω Aᵀ)``). ``A`` must have
        ``det A = ±1`` so ``(Aᵀ)⁻¹`` is integer — rejected loudly otherwise (an honest
        boundary, not a fabricated reduction). Returned as ``(A, 0, 0, (Aᵀ)⁻¹)``."""
        a = cls._coerce_mat3(a, "A")
        det = cls._det3(a)
        if det not in (1, -1):
            raise ValueError(
                f"the GL-twist block A must be in GL(3,ℤ) (det = ±1) so (Aᵀ)⁻¹ is "
                f"integer; got A = {a!r} with det = {det} — an honest boundary, not "
                "a fabricated reduction.")
        a_inv = cls._inv3_unimodular(a, det)
        d = cls._m3_transpose(a_inv)        # (Aᵀ)⁻¹ = (A⁻¹)ᵀ
        return (a, cls._z3(), cls._z3(), d)

    @classmethod
    def sp6_inversion(cls) -> "_Sp6":
        """The Sp(6, ℤ) INVERSION generator ``γ = [[0, −I], [I, 0]]`` (the genus-3
        ``Ω ↦ −Ω⁻¹``; the ``J`` matrix). It carries the TRANSCENDENTAL automorphy
        factor ``det(−iΩ)^{1/2}`` (off every decision path; :meth:`automorphy_factor`).
        Returned as ``(0, −I, I, 0)``."""
        neg_i = ((-1, 0, 0), (0, -1, 0), (0, 0, -1))
        return (cls._z3(), neg_i, cls._i3(), cls._z3())

    @staticmethod
    def _det3(m: "_Mat3") -> int:
        """The exact integer determinant of a 3×3 matrix (Sarrus / cofactor). No
        float."""
        return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
                - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
                + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))

    @classmethod
    def _inv3_unimodular(cls, m: "_Mat3", det: int) -> "_Mat3":
        """The exact integer inverse ``M⁻¹ = (1/det)·adj(M)`` of a UNIMODULAR 3×3 ``M``
        (``det = ±1`` so the adjugate divided by det is exact integer). The adjugate is
        the transpose of the cofactor matrix. No float; the divisions are exact (det is
        ±1, so this is a sign-multiply — Class-K, never an ALU abs())."""
        # cofactor C[i][j] = (−1)^{i+j} · minor(i,j); adj = Cᵀ; M⁻¹ = adj / det
        cof = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        for i in range(3):
            for j in range(3):
                rows = [r for r in range(3) if r != i]
                cols = [c for c in range(3) if c != j]
                minor = (m[rows[0]][cols[0]] * m[rows[1]][cols[1]]
                         - m[rows[0]][cols[1]] * m[rows[1]][cols[0]])
                sign = 1 if (i + j) % 2 == 0 else -1     # Class-K, no abs()
                cof[i][j] = sign * minor
        # M⁻¹ = adj / det = (cofᵀ) · det   (det = ±1, so /det == ·det)
        return tuple(tuple(cof[j][i] * det for j in range(3))  # type: ignore[return-value]
                     for i in range(3))

    @staticmethod
    def _coerce_mat3(m: "_Mat3", name: str) -> "_Mat3":
        """Coerce / validate a 3×3 integer matrix; reject a malformed shape loudly."""
        if not (isinstance(m, (tuple, list)) and len(m) == 3
                and all(isinstance(row, (tuple, list)) and len(row) == 3
                        for row in m)):
            raise ValueError(f"{name} must be a 3×3 integer matrix; got {m!r}")
        return tuple(tuple(int(m[i][j]) for j in range(3))  # type: ignore[return-value]
                     for i in range(3))

    @classmethod
    def _validate_gamma6(cls, gamma: "_Sp6") -> "_Sp6":
        """Coerce / validate an ``Sp(6, ℤ)`` element ``(A, B, C, D)`` to a tuple of
        four exact-integer 3×3 blocks; reject a malformed shape loudly."""
        if not (isinstance(gamma, (tuple, list)) and len(gamma) == 4):
            raise ValueError(
                f"γ must be (A, B, C, D), four 3×3 integer matrices; got {gamma!r}")
        return (cls._coerce_mat3(gamma[0], "A"), cls._coerce_mat3(gamma[1], "B"),
                cls._coerce_mat3(gamma[2], "C"), cls._coerce_mat3(gamma[3], "D"))

    @classmethod
    def sp6_is_symplectic(cls, gamma: "_Sp6") -> bool:
        """True iff ``γ = (A, B, C, D)`` (3×3 blocks) is genuinely symplectic —
        ``γ·J·γᵀ = J`` with ``J = [[0, −I], [I, 0]]`` (the genus-3 symplectic form). The
        exact integer block conditions are ``AᵀC = CᵀA`` (symmetric), ``BᵀD = DᵀB``
        (symmetric), ``AᵀD − CᵀB = I``. A pure integer check (no float)."""
        a, b, c, d = cls._validate_gamma6(gamma)
        tr = cls._m3_transpose
        mm = cls._m3_matmul
        atc = mm(tr(a), c)
        btd = mm(tr(b), d)
        if atc != cls._m3_transpose(atc):                 # AᵀC symmetric
            return False
        if btd != cls._m3_transpose(btd):                 # BᵀD symmetric
            return False
        atd = mm(tr(a), d)
        ctb = mm(tr(c), b)
        diff = tuple(tuple(atd[i][j] - ctb[i][j] for j in range(3))
                     for i in range(3))
        return diff == cls._i3()                           # AᵀD − CᵀB = I

    @classmethod
    def sp6_compose(cls, g2: "_Sp6", g1: "_Sp6") -> "_Sp6":
        """The Sp(6, ℤ) group law ``g2 · g1`` (the block matrix product) — exact
        integer 3×3 block arithmetic. The characteristic action composes the SAME way
        (``transform(g2·g1) == transform(g2) ∘ transform(g1)``; the gate)."""
        a2, b2, c2, d2 = cls._validate_gamma6(g2)
        a1, b1, c1, d1 = cls._validate_gamma6(g1)
        mm, ad = cls._m3_matmul, cls._m3_add
        a = ad(mm(a2, a1), mm(b2, c1))
        b = ad(mm(a2, b1), mm(b2, d1))
        c = ad(mm(c2, a1), mm(d2, c1))
        d = ad(mm(c2, b1), mm(d2, d1))
        return (a, b, c, d)

    # ── the EXACT characteristic action + the κ 8th-root multiplier ─────────────
    @classmethod
    def _char_transform_int(cls, gamma: "_Sp6", ep_prime: "Tuple[int, int, int]",
                            eps: "Tuple[int, int, int]"
                            ) -> "Tuple[List[int], List[int]]":
        """The Igusa / DLMF-21.5.9 characteristic action at genus 3, as INTEGER vectors
        (the caller reduces mod 2 for the bit): ``ε' ↦ D·ε' − C·ε + diag(C·Dᵀ)`` and
        ``ε ↦ −B·ε' + A·ε + diag(A·Bᵀ)`` (DLMF §21.5.9 holds for general genus g; here
        3×3 blocks / 3-vectors). Exact integer 3×3 arithmetic, no float."""
        a, b, c, d = cls._validate_gamma6(gamma)
        d_epp = cls._m3_matvec(d, ep_prime)
        c_eps = cls._m3_matvec(c, eps)
        diag_cd = cls._m3_diag_of_prod(c, d)
        new_epp = [d_epp[i] - c_eps[i] + diag_cd[i] for i in range(3)]
        a_eps = cls._m3_matvec(a, eps)
        b_epp = cls._m3_matvec(b, ep_prime)
        diag_ab = cls._m3_diag_of_prod(a, b)
        new_eps = [a_eps[i] - b_epp[i] + diag_ab[i] for i in range(3)]
        return new_epp, new_eps

    @staticmethod
    def _dot3(u: "Tuple[int, int, int]", v: "Tuple[int, int, int]") -> int:
        """The exact integer dot product ``u·v`` of two length-3 vectors."""
        return u[0] * v[0] + u[1] * v[1] + u[2] * v[2]

    @classmethod
    def _kappa_exp8(cls, gamma: "_Sp6", ep_prime: "Tuple[int, int, int]",
                    eps: "Tuple[int, int, int]") -> int:
        """The EXACT 8th-root multiplier exponent ``k ∈ ℤ/8`` (the multiplier is
        ``ζ₈^k = e^{2πik/8}``) — the genus-3 CHARACTERISTIC-DEPENDENT Igusa phase
        ``φ_m(γ)`` of the theta-constant transformation. The Igusa φ_m is stated for
        GENERAL genus g (a sum over ``k,l = 1..g``; the SAME expression at every g —
        verified MPM):

            φ_m(γ) = −½·ε'ᵀ·(B·Dᵀ)·ε' + εᵀ·(AᵀC)·ε − 2·ε'ᵀ·(BᵀC)·ε
                     − diag(A·Bᵀ)ᵀ·(D·ε' − C·ε)

        This returns the ``exp(2πi·φ_m)`` part — the piece EXACTLY computable on the
        decision path: the phase is rational with denominator dividing 8, so ``8·φ_m``
        is an EXACT integer → ``k = (8·φ_m) mod 8`` is exact (no float). The remaining
        ``γ``-only factor ``κ₀(γ)`` (the Maslov / Weil cocycle 8th root) is BOUND to
        the TRANSCENDENTAL automorphy factor ``det(C·Ω+D)^{1/2}`` (the branch of the
        square root), so it is NOT placed on the decision path — carried SYMBOLICALLY
        (:meth:`automorphy_factor`; the rc72 review lesson). The doubled-half
        characteristic absorbs the ½'s; we carry ``8·φ_m`` as an integer throughout
        (the g=2 ``RiemannTheta._kappa_exp8`` expression, parametrically extended to
        3-vectors / 3×3 blocks):

            8·φ_m = −4·ε'ᵀ(B·Dᵀ)ε' + 8·εᵀ(AᵀC)ε − 16·ε'ᵀ(BᵀC)ε
                    − 8·diag(A·Bᵀ)ᵀ(D·ε' − C·ε)
        """
        a, b, c, d = cls._validate_gamma6(gamma)
        epp = (int(ep_prime[0]), int(ep_prime[1]), int(ep_prime[2]))
        eps = (int(eps[0]), int(eps[1]), int(eps[2]))
        tr, mm = cls._m3_transpose, cls._m3_matmul
        # term 1: −4·ε'ᵀ(B·Dᵀ)ε'   (the −½ becomes −4 after ×8)
        bdt = mm(b, tr(d))
        t1 = -4 * cls._dot3(epp, cls._m3_matvec(bdt, epp))
        # term 2: +8·εᵀ(AᵀC)ε
        atc = mm(tr(a), c)
        t2 = 8 * cls._dot3(eps, cls._m3_matvec(atc, eps))
        # term 3: −16·ε'ᵀ(BᵀC)ε
        btc = mm(tr(b), c)
        t3 = -16 * cls._dot3(epp, cls._m3_matvec(btc, eps))
        # term 4: −8·diag(A·Bᵀ)ᵀ(D·ε' − C·ε)
        diag_ab = cls._m3_diag_of_prod(a, b)
        d_epp = cls._m3_matvec(d, epp)
        c_eps = cls._m3_matvec(c, eps)
        arg = [d_epp[i] - c_eps[i] for i in range(3)]
        t4 = -8 * cls._dot3(tuple(diag_ab), tuple(arg))
        eight_phi = t1 + t2 + t3 + t4
        return eight_phi % 8                       # exact k ∈ {0,…,7}

    def transform(self, gamma: "_Sp6") -> "Tuple[RiemannThetaG3, int]":
        """The EXACT genus-3 Sp(6, ℤ) modular action on THIS theta-characteristic:
        returns the transformed :class:`RiemannThetaG3` ``θ[γ·m]`` and the 8th-root
        multiplier exponent ``k ∈ ℤ/8`` (the multiplier is ``ζ₈^k``). The characteristic
        map (DLMF §21.5.9, general genus g; here 3×3 blocks) is bit-exact (integer /
        mod-2); the multiplier rides the exact Igusa phase (:meth:`_kappa_exp8`). The
        transcendental automorphy factor ``det(C·Ω+D)^{1/2}`` is NOT applied — it is
        carried symbolically (:meth:`automorphy_factor`), off the decision path.

        DISPATCHES the exact-integer characteristic + κ computation to the native
        ``srmech_riemann_theta_g3_sp6_char`` C peer when loaded (a 1:1 mirror — the C
        result EQUALS the Python result, trusted only on a native hit); else the pure
        body (the COMPLETE alternative + the parity oracle). ``γ`` must be symplectic —
        rejected loudly otherwise (an honest boundary). Parity (even ⇄ even,
        odd ⇄ odd) is preserved by construction."""
        if not self.sp6_is_symplectic(gamma):
            raise ValueError(
                "transform requires a symplectic γ (γ·J·γᵀ = J); the given (A,B,C,D) "
                "is not in Sp(6,ℤ) — an honest boundary, not a fabricated reduction.")
        nat = _native_g3()
        if nat is not None and getattr(nat, "has_native_riemann_theta_g3_sp6",
                                       lambda: False)():
            try:
                g = self._validate_gamma6(gamma)
                got = nat.riemann_theta_g3_sp6_char_c(
                    g, self._ep1, self._ep2, self._ep3,
                    self._e1, self._e2, self._e3)
                if got is not None:
                    (n1, n2, n3, m1, m2, m3), kexp = got
                    return RiemannThetaG3(n1, n2, n3, m1, m2, m3), kexp % 8
            except (RuntimeError, OverflowError, ValueError):
                pass                                  # fall to the pure path
        new_epp, new_eps = self._char_transform_int(
            gamma, (self._ep1, self._ep2, self._ep3),
            (self._e1, self._e2, self._e3))
        kexp = self._kappa_exp8(
            gamma, (self._ep1, self._ep2, self._ep3),
            (self._e1, self._e2, self._e3))
        return (RiemannThetaG3(new_epp[0] % 2, new_epp[1] % 2, new_epp[2] % 2,
                               new_eps[0] % 2, new_eps[1] % 2, new_eps[2] % 2),
                kexp)

    @staticmethod
    def automorphy_factor(gamma: "_Sp6") -> str:
        """The TRANSCENDENTAL automorphy factor ``det(C·Ω+D)^{1/2}`` of the Sp(6, ℤ)
        action — returned as a SYMBOLIC string, NEVER numerically evaluated (it depends
        on the transcendental period matrix ``Ω ∈ H₃`` and is a square root: not a
        finite exact object, so it stays OFF every decision path; the rc72 review
        lesson). The honest, exact part of the transformation is the characteristic map
        + the κ 8th root (:meth:`transform`); this factor is the documented
        not-evaluated companion."""
        a, b, c, d = RiemannThetaG3._validate_gamma6(gamma)

        def _rows(m: "_Mat3") -> str:
            return "[" + ",".join(
                "[" + ",".join(str(m[i][j]) for j in range(3)) + "]"
                for i in range(3)) + "]"
        return f"det({_rows(c)}·Ω + {_rows(d)})^(1/2)"

    # ══════════════════════════════════════════════════════════════════════════
    # rc77 (B): the genus-3 ADDITION relation (genuine; distinct from rc75
    # duplication — DLMF §21.6.8 at g=3, the two-argument theorem, sum over (ℤ/2)³).
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _theta_omega_eighth(a1: int, a2: int, a3: int, e1: int, e2: int, e3: int,
                            box: int) -> "Dict[_Sextuple, int]":
        """The genus-3 theta-constant ``θ[(a₁,a₂,a₃); (e₁,e₂,e₃)](0 | Ω)`` in the COMMON
        EIGHTH-nome base ``Q₈ = q^{1/8}`` (so it shares ONE integer lattice with the
        ``2Ω`` thetas of the addition right side). With ``mᵢ = nᵢ + aᵢ/2`` the q exponent
        ``mᵢ²`` rides ``Q₈^{8mᵢ²} = Q₈^{2(2nᵢ+aᵢ)²}``, the cross ``mᵢmⱼ`` rides
        ``Q₈^{2(2nᵢ+aᵢ)(2nⱼ+aⱼ)}``:

            Aᵢ = 2(2nᵢ+aᵢ)²,   C_ij = 2(2nᵢ+aᵢ)(2nⱼ+aⱼ)

        sign ``(−1)^{e·n}`` is the Class-K pin-slot (explicit ±1 branch, never
        ``abs()``). Exact integer, no float / numpy / ``math``. ``a₁, a₂, a₃`` are the
        DOUBLED upper characteristic (the helper accepts any integer so the right
        side's ``2r±(a∓b)`` cases work). DISPATCHES to the native
        ``srmech_riemann_theta_g3_eighth_lattice`` (at Ω) when loaded — a 1:1
        exact-integer mirror, trusted only on a native hit."""
        nat = _native_g3()
        if nat is not None and getattr(nat, "has_native_riemann_theta_g3_eighth",
                                       lambda: False)():
            try:
                got = nat.riemann_theta_g3_eighth_lattice_c(
                    a1, a2, a3, e1, e2, e3, False, box)
                if got is not None:
                    return got
            except (RuntimeError, OverflowError, ValueError):
                pass
        out: Dict[_Sextuple, int] = {}
        for n1 in range(-box, box + 1):
            u1 = 2 * n1 + a1
            for n2 in range(-box, box + 1):
                u2 = 2 * n2 + a2
                for n3 in range(-box, box + 1):
                    u3 = 2 * n3 + a3
                    key = (2 * u1 * u1, 2 * u2 * u2, 2 * u3 * u3,
                           2 * u1 * u2, 2 * u1 * u3, 2 * u2 * u3)
                    parity = (e1 * n1 + e2 * n2 + e3 * n3) % 2
                    sign = 1 if parity == 0 else -1   # never abs(); explicit ±
                    out[key] = out.get(key, 0) + sign
        return {k: w for k, w in out.items() if w != 0}

    @staticmethod
    def _theta_two_omega_eighth(s1: int, s2: int, s3: int, e1: int, e2: int, e3: int,
                                box: int) -> "Dict[_Sextuple, int]":
        """The genus-3 theta-constant ``θ[(s₁/2,s₂/2,s₃/2); (e₁,e₂,e₃)](0 | 2Ω)`` in the
        SAME EIGHTH-nome base. The constructive sum/difference re-indexing puts the
        addition right side here: the eighth-nome exponent of ``θ`` at ``2Ω`` is
        ``(4nᵢ+sᵢ)²`` (and cross ``(4nᵢ+sᵢ)(4nⱼ+sⱼ)``):

            Aᵢ = (4nᵢ+sᵢ)²,   C_ij = (4nᵢ+sᵢ)(4nⱼ+sⱼ)

        sign ``(−1)^{e·n}`` the Class-K pin-slot. ``s₁, s₂, s₃`` are the DOUBLED upper
        characteristic of the ``2Ω`` theta (an integer; odd ⟺ a genuine half-integer
        characteristic). Exact integer, no float. DISPATCHES to the native
        ``srmech_riemann_theta_g3_eighth_lattice`` (at 2Ω) when loaded — a 1:1
        exact-integer mirror, trusted only on a native hit."""
        nat = _native_g3()
        if nat is not None and getattr(nat, "has_native_riemann_theta_g3_eighth",
                                       lambda: False)():
            try:
                got = nat.riemann_theta_g3_eighth_lattice_c(
                    s1, s2, s3, e1, e2, e3, True, box)
                if got is not None:
                    return got
            except (RuntimeError, OverflowError, ValueError):
                pass
        out: Dict[_Sextuple, int] = {}
        for n1 in range(-box, box + 1):
            u1 = 4 * n1 + s1
            for n2 in range(-box, box + 1):
                u2 = 4 * n2 + s2
                for n3 in range(-box, box + 1):
                    u3 = 4 * n3 + s3
                    key = (u1 * u1, u2 * u2, u3 * u3,
                           u1 * u2, u1 * u3, u2 * u3)
                    parity = (e1 * n1 + e2 * n2 + e3 * n3) % 2
                    sign = 1 if parity == 0 else -1
                    out[key] = out.get(key, 0) + sign
        return {k: w for k, w in out.items() if w != 0}

    @staticmethod
    def _square_lattice_pair(la: "Dict[_Sextuple, int]",
                             lb: "Dict[_Sextuple, int]") -> "Dict[_Sextuple, int]":
        """The exact-integer product ``la · lb`` of two genus-3
        ``(A₁,A₂,A₃,C₁₂,C₁₃,C₂₃) → coeff`` lattices (a bounded convolution over the
        exponent sextuples; JPL Rule 2). All-integer, no float."""
        out: Dict[_Sextuple, int] = {}
        items_a = list(la.items())
        items_b = list(lb.items())
        for k1, v1 in items_a:
            for k2, v2 in items_b:
                key = (k1[0] + k2[0], k1[1] + k2[1], k1[2] + k2[2],
                       k1[3] + k2[3], k1[4] + k2[4], k1[5] + k2[5])
                out[key] = out.get(key, 0) + v1 * v2
        return {k: v for k, v in out.items() if v != 0}

    @classmethod
    def addition_lhs(cls, a: "Tuple[int, int, int]", b: "Tuple[int, int, int]",
                     box: int) -> "Dict[_Sextuple, int]":
        """The LEFT side of the genus-3 addition identity — the BILINEAR product of TWO
        theta-nulls ``θ[a; 0](0|Ω) · θ[b; 0](0|Ω)`` (in the common eighth-nome base),
        the exact-integer lattice convolution. ``a, b`` are the upper characteristics
        (each in {0,1}³). When ``a ≠ b`` this is a product of two DISTINCT nulls — the
        content rc75 duplication cannot produce. See :meth:`addition_holds`."""
        la = cls._theta_omega_eighth(a[0], a[1], a[2], 0, 0, 0, box)
        lb = cls._theta_omega_eighth(b[0], b[1], b[2], 0, 0, 0, box)
        return cls._square_lattice_pair(la, lb)

    @classmethod
    def addition_rhs(cls, a: "Tuple[int, int, int]", b: "Tuple[int, int, int]",
                     box: int) -> "Dict[_Sextuple, int]":
        """The RIGHT side of the genus-3 addition identity (DLMF §21.6.8 at z=0, lower
        chars 0, g=3 — sum over ``r ∈ (ℤ/2)³``, EIGHT terms)

            Σ_{r ∈ (ℤ/2)³} θ[(2r+a+b)/2; 0](0|2Ω) · θ[(2r+a−b)/2; 0](0|2Ω)

        (in the common eighth-nome base). Each summand is a product of two ``2Ω``
        theta-nulls with the DISTINCT doubled characteristics ``2r+a+b`` vs ``2r+a−b``
        — the genuinely-new content; the ``a = b`` collapse recovers rc75's duplication
        ``Σ_r θ[r;0](2Ω)²``. See :meth:`addition_holds`."""
        rhs: Dict[_Sextuple, int] = {}
        for r1 in (0, 1):
            for r2 in (0, 1):
                for r3 in (0, 1):
                    sp1 = 2 * r1 + a[0] + b[0]
                    sp2 = 2 * r2 + a[1] + b[1]
                    sp3 = 2 * r3 + a[2] + b[2]
                    sm1 = 2 * r1 + a[0] - b[0]
                    sm2 = 2 * r2 + a[1] - b[1]
                    sm3 = 2 * r3 + a[2] - b[2]
                    l1 = cls._theta_two_omega_eighth(sp1, sp2, sp3, 0, 0, 0, box)
                    l2 = cls._theta_two_omega_eighth(sm1, sm2, sm3, 0, 0, 0, box)
                    term = cls._square_lattice_pair(l1, l2)
                    for k, v in term.items():
                        rhs[k] = rhs.get(k, 0) + v
        return {k: v for k, v in rhs.items() if v != 0}

    @classmethod
    def addition_holds(cls, box: int = 6) -> bool:
        """The genus-3 ADDITION identity gate (the rc77 (B) build gate) — the GENUINE
        two-argument genus-3 theta addition theorem (DLMF §21.6.8, the ``z₁ = z₂ = 0``,
        lower-characteristics-0, ``g = 3`` specialization — the sum runs over
        ``r ∈ (ℤ/2)³``, EIGHT terms),

            θ[a; 0](0|Ω)·θ[b; 0](0|Ω)
              = Σ_{r ∈ (ℤ/2)³} θ[(2r+a+b)/2; 0](0|2Ω)·θ[(2r+a−b)/2; 0](0|2Ω) ,

        holds EXACTLY as a truncated exact-integer multivariate q-series, for ALL ``Ω``
        (no transcendental evaluation, no float, no tolerance). The identity is proved
        CONSTRUCTIVELY by the sum/difference re-indexing of the double lattice sum (see
        :meth:`_theta_two_omega_eighth`); it is the genus-3 instance of the addition
        theorem (DLMF §21.6.8 is stated for general genus g).

        GENUINELY DISTINCT FROM rc75's DUPLICATION: duplication squares a SINGLE even
        theta-null (``θ[0;0]² = Σ_c θ[c;0](2Ω)²``, 8 summands); this addition relation
        is the BILINEAR product of TWO DIFFERENT nulls ``θ[a]·θ[b]`` (``a ≠ b``), and
        the right side carries DISTINCT characteristics ``2r+a+b`` vs ``2r+a−b`` per
        summand — content duplication alone never produces (it never holds a product of
        two distinct nulls). The gate VERIFIES the non-trivial ``a ≠ b`` cases (and
        :meth:`addition_is_distinct_from_duplication` confirms they differ from the
        ``a = b`` duplication collapse), so it is the GENUINE addition theorem, not a
        relabeled duplication.

        Compares the two sides on the SAFE INNER REGION the box ``|nᵢ| ≤ box`` provably
        resolves. The eighth-nome theta at Ω reaches exponent ``2·(2·box)²`` and at 2Ω
        reaches ``(4·box)²``; a box-``box`` truncation fully resolves monomials with
        ``Aᵢ, |C_ij| ≤ 2·box²`` (a conservative inner bound). Returns ``True`` iff every
        checked ``(a, b)`` pair agrees exactly on the safe region, at least one genuine
        ``a ≠ b`` pair is checked, and the safe region is non-trivially populated with a
        genuine genus-3 cross-term (``C₁₃`` or ``C₂₃`` ≠ 0) monomial (so the genus-3
        coupling is genuinely exercised, not just the genus-2 / genus-1 slice).

        A CARRIER METHOD (the carrier's own build gate), not a public module-level op —
        ``tools.total`` is UNCHANGED (the rc72/73/75 ``*_holds`` precedent)."""
        if not isinstance(box, int) or box < 2:
            raise ValueError(
                f"box must be an int ≥ 2 for the genus-3 addition gate; got {box!r}")
        safe = 2 * box * box
        # the (a, b) pairs to verify: the duplication collapse (a==b) PLUS genuine
        # distinct pairs (a != b) — the latter is what makes it the real addition; the
        # distinct pairs are chosen to exercise the THREE genus-3 cross-terms.
        pairs = [((0, 0, 0), (0, 0, 0)),                         # dup collapse
                 ((1, 0, 0), (0, 0, 0)), ((0, 0, 1), (0, 0, 0)),  # genuine a ≠ b
                 ((1, 0, 1), (0, 0, 0)), ((1, 1, 0), (0, 0, 1)),
                 ((0, 1, 1), (1, 0, 0)), ((1, 1, 1), (0, 1, 1))]

        def restrict(lat: "Dict[_Sextuple, int]") -> "Dict[_Sextuple, int]":
            kept: Dict[_Sextuple, int] = {}
            for k, v in lat.items():
                a1, a2, a3, c12, c13, c23 = k
                m12 = c12 if c12 >= 0 else -c12       # Class-K magnitude, no abs()
                m13 = c13 if c13 >= 0 else -c13
                m23 = c23 if c23 >= 0 else -c23
                if (a1 <= safe and a2 <= safe and a3 <= safe
                        and m12 <= safe and m13 <= safe and m23 <= safe):
                    kept[k] = v
            return kept

        saw_genuine = False
        saw_g3_cross = False
        for (a, b) in pairs:
            lhs = restrict(cls.addition_lhs(a, b, box))
            rhs = restrict(cls.addition_rhs(a, b, box))
            if lhs != rhs:
                return False
            if a != b:
                saw_genuine = True
            if any((c13 != 0 or c23 != 0)
                   for (_a1, _a2, _a3, _c12, c13, c23) in lhs):
                saw_g3_cross = True
        return saw_genuine and saw_g3_cross

    @classmethod
    def addition_is_distinct_from_duplication(cls, box: int = 6) -> bool:
        """PROVES the genus-3 addition relation is GENUINELY DISTINCT from the rc75
        duplication: for a genuine ``a ≠ b`` pair the addition LEFT side ``θ[a]·θ[b]``
        is a product of two DIFFERENT theta-nulls, which is NOT equal to ANY duplication
        left side ``θ[c]²`` (a single even null squared). Returns ``True`` iff the
        genuine addition LHS (``a=(1,0,0)``, ``b=(0,0,0)``) differs from every
        ``θ[c;0]²`` over the eight even ``c ∈ {0,1}³`` (upper char ``c``, lower 0 — all
        even) — the no-shell proof that it is not a relabeled duplication."""
        if not isinstance(box, int) or box < 2:
            raise ValueError(f"box must be an int ≥ 2; got {box!r}")
        genuine = cls.addition_lhs((1, 0, 0), (0, 0, 0), box)   # θ[(1,0,0)]·θ[(0,0,0)]
        for c1 in (0, 1):
            for c2 in (0, 1):
                for c3 in (0, 1):
                    tc = cls._theta_omega_eighth(c1, c2, c3, 0, 0, 0, box)
                    sq = cls._square_lattice_pair(tc, tc)        # θ[c;0]²
                    if genuine == sq:
                        return False                            # would be duplication
        return True

    # ══════════════════════════════════════════════════════════════════════════
    # rc76: IGUSA'S χ₁₈ — the EXACT product of the 36 even theta-nulls (the genus-3
    # hyperelliptic / vanishing-theta-null structure as an exact FORMAL q-series)
    # ══════════════════════════════════════════════════════════════════════════

    @classmethod
    def chi18_even_null_factors(cls) -> "List[RiemannThetaG3]":
        """The 36 EVEN theta-nulls whose product is Igusa's χ₁₈ — exactly the 36 even
        genus-3 theta-constants ``θ[ε](0|Ω)`` (:meth:`even_characteristics`). Igusa's
        χ₁₈ ∈ S₁₈(Γ₃) is the scalar-valued Siegel cusp form of weight 18 and degree 3
        DEFINED AS THE PRODUCT OF ALL 36 EVEN THETA-CONSTANTS (each θ-null a modular
        form of weight ½, so 36·½ = 18; Bernatska–Kopeliovich, arXiv:2306.14889, p.1,
        the genus-3 exact sequence ``0 → χ₁₈𝔄(Γ₃) → 𝔄(Γ₃) →^ρ 𝒮(2,8)`` with "χ₁₈ the
        cusp form of weight 18, defined as the product of all even theta constants"; van
        der Geer / Cléry–Faber, the degree-3 χ₁₈ as ∏₃₆ even theta-nulls). This returns
        the EXACT factor list (each an even :class:`RiemannThetaG3`) — the operand-side
        construction; the divisor of χ₁₈ is ``H₃ + 2D`` (H₃ the hyperelliptic locus, D
        the divisor at infinity), so χ₁₈ vanishes EXACTLY on the genus-3 hyperelliptic
        locus (the numerical vanishing-decision is the operand-side OPEN —
        :meth:`hyperelliptic_locus_is_open`). A pure exact carrier object (no float)."""
        return cls.even_characteristics()

    @classmethod
    def chi18_leading_order_quarter(cls) -> int:
        """The EXACT leading (minimal) DIAGONAL q-order of χ₁₈ in the QUARTER-nome base
        ``Qᵢ = qᵢ^{1/4}`` — the cusp-vanishing structure of the 36-even-null product.
        Each even null θ[ε] has leading diagonal quarter-order
        ``min Σᵢ (2nᵢ+ε'ᵢ)² = Σᵢ ε'ᵢ² = wt(ε')`` (achieved at ``n = 0``), the number of
        set bits of the upper characteristic ε'. The product's leading diagonal order is
        the SUM of the factors' leading orders (the leading-order coefficient is NONZERO
        — verified in :meth:`chi18_leading_part`, so no cancellation drops the order).
        Summed over the 36 even nulls (8 of wt 0, 12 of wt 1, 12 of wt 2, 4 of wt 3):
        ``0·8 + 1·12 + 2·12 + 3·4 = 48`` quarter-nome units = ``48/4 = 12`` in the
        diagonal nome ``qᵢ``. EXACT integer, derived from the enumeration (no float)."""
        order = 0
        for rt in cls.even_characteristics():
            (ep1, ep2, ep3), _ = rt.characteristic
            order += ep1 + ep2 + ep3              # wt(ε') = min diagonal quarter-order
        return order

    @classmethod
    def chi18_leading_order_nome(cls) -> int:
        """The EXACT leading diagonal q-order of χ₁₈ in the DIAGONAL nome ``qᵢ`` (=
        ``Qᵢ^4``): :meth:`chi18_leading_order_quarter` ``// 4 = 48 // 4 = 12``. EXACT
        integer (the quarter-order is divisible by 4 — all four ``n`` clearings keep the
        quarter-order ≡ 0 mod 4 on the diagonal). No float."""
        q = cls.chi18_leading_order_quarter()
        if q % 4 != 0:                            # honest guard, never silently round
            raise ValueError(
                f"χ₁₈ leading quarter-order {q} is not divisible by 4 — the diagonal "
                "nome order is not integral (would indicate a clearing bug, not a ship).")
        return q // 4

    @classmethod
    def _chi18_leading_part_py(cls, box: int = 2) -> "Dict[_Sextuple, int]":
        """The COMPLETE pure-Python χ₁₈ leading-order HOMOGENEOUS PART (the parity oracle
        for the C peer): the exact-integer ``(A₁,A₂,A₃,C₁₂,C₁₃,C₂₃) → coeff`` lattice of
        the 36-even-null product restricted to its minimal DIAGONAL order
        (:meth:`chi18_leading_order_quarter`). Each factor is restricted to its own
        leading diagonal slice (the monomials at ``Σ Aᵢ = wt(ε')``) and the 36 leading
        slices are convolved exactly (a bounded sparse multivariate multiply; JPL Rule
        2). The result is the exact leading part of χ₁₈ — NONZERO (so χ₁₈ ≠ 0 and its
        leading order is exactly the sum). All-integer, no float / numpy / ``math`` /
        ``abs()``."""
        if not isinstance(box, int) or box < 1:
            raise ValueError(f"box must be an int ≥ 1 for χ₁₈; got {box!r}")
        prod: Dict[_Sextuple, int] = {(0, 0, 0, 0, 0, 0): 1}
        for rt in cls.even_characteristics():
            lat = rt.lattice(box)
            # this factor's own leading diagonal slice (minimal Σ Aᵢ)
            min_diag = min(k[0] + k[1] + k[2] for k in lat)
            lead = {k: v for k, v in lat.items()
                    if k[0] + k[1] + k[2] == min_diag}
            nxt: Dict[_Sextuple, int] = {}
            for k1, v1 in prod.items():
                for k2, v2 in lead.items():
                    key = (k1[0] + k2[0], k1[1] + k2[1], k1[2] + k2[2],
                           k1[3] + k2[3], k1[4] + k2[4], k1[5] + k2[5])
                    nxt[key] = nxt.get(key, 0) + v1 * v2
            prod = {k: v for k, v in nxt.items() if v != 0}
        return prod

    @classmethod
    def chi18_leading_part(cls, box: int = 2) -> "Dict[_Sextuple, int]":
        """Igusa's χ₁₈ leading-order HOMOGENEOUS PART — the exact-integer
        ``(A₁,A₂,A₃,C₁₂,C₁₃,C₂₃) → coeff`` lattice of the product of all 36 even
        theta-nulls, restricted to the minimal diagonal q-order (the cusp-vanishing
        structure). This is the EXACT, finite, load-bearing part of the χ₁₈ formal
        q-series: it is NONZERO (so χ₁₈ ≢ 0), it lives at diagonal quarter-order
        :meth:`chi18_leading_order_quarter` ``= 48`` (= 12 in qᵢ), and it is genuinely
        the product of EXACTLY 36 even-null factors (:meth:`chi18_even_null_factors`).
        DISPATCHES to the native ``srmech_riemann_theta_g3_chi18`` C peer when loaded (a
        1:1 exact-integer mirror — the C lattice EQUALS the Python lattice, trusted only
        on a native hit); else the pure-Python :meth:`_chi18_leading_part_py` body (the
        COMPLETE alternative + the parity oracle). No float, no ``abs()`` (the per-term
        ``(−1)^{ε·n}`` signs are the Class-K pin-slot inside each factor's lattice), no
        numpy / ``math``.

        MPM: Igusa χ₁₈ ∈ S₁₈(Γ₃), weight 18, degree 3, div = H₃ + 2D (Bernatska–
        Kopeliovich arXiv:2306.14889 p.1; van der Geer SMF Degree 2&3 + Invariant
        Theory). The NUMERICAL vanishing decision (is THIS Ω hyperelliptic) is a
        transcendental point-evaluation → the operand-side OPEN
        (:meth:`hyperelliptic_locus_is_open`); the carrier provides only the exact
        FORMAL construction here, never a numerical hyperelliptic verdict."""
        if not isinstance(box, int) or box < 1:
            raise ValueError(f"box must be an int ≥ 1 for χ₁₈; got {box!r}")
        nat = _native_g3_chi18()
        if nat is not None:
            try:
                got = nat.riemann_theta_g3_chi18_c(box)
                if got is not None:
                    return got
            except (RuntimeError, OverflowError, ValueError):
                pass   # fall to the pure path
        return cls._chi18_leading_part_py(box)

    @classmethod
    def chi18_is_nonzero(cls, box: int = 2) -> bool:
        """PROVES Igusa's χ₁₈ is a NONZERO formal q-series — its leading-order part
        (:meth:`chi18_leading_part`) is non-empty with at least one nonzero coefficient.
        Because χ₁₈ = ∏₃₆ even theta-nulls and the leading-order coefficient does NOT
        cancel, χ₁₈ ≢ 0 (a well-defined weight-18 cusp form, NOT the zero form). Returns
        ``True``; exact-integer, no float."""
        lead = cls.chi18_leading_part(box)
        return bool(lead) and any(v != 0 for v in lead.values())

    @classmethod
    def chi18_leading_part_is_at_order_48(cls, box: int = 2) -> bool:
        """PROVES the χ₁₈ leading part lives EXACTLY at diagonal quarter-order 48 (= 12
        in qᵢ) — every monomial of :meth:`chi18_leading_part` has
        ``A₁+A₂+A₃ == 48 == :meth:`chi18_leading_order_quarter```, and the part is
        nonzero. The exact cusp-vanishing-order gate. Exact-integer, no float."""
        target = cls.chi18_leading_order_quarter()
        lead = cls.chi18_leading_part(box)
        if not lead:
            return False
        return all(k[0] + k[1] + k[2] == target for k in lead)

    @classmethod
    def chi18_factor_count_is_36_even(cls) -> bool:
        """PROVES χ₁₈ is the product of EXACTLY 36 factors, each a genuine even
        theta-null — the combinatorics gate. Verifies ``len == 36`` and every factor
        ``is_even`` and the singular even null (empty-set characteristic) is among them.
        Exact, no float."""
        factors = cls.chi18_even_null_factors()
        if len(factors) != 36:
            return False
        if not all(f.is_even for f in factors):
            return False
        return cls.singular_even_null() in factors

    @staticmethod
    def hyperelliptic_locus_is_open() -> str:
        """The DOCUMENTED operand-side OPEN — the genus-3 vanishing-theta-null structure
        is now NAMED EXPLICITLY as Igusa's **χ₁₈** (rc76). Unlike genus 2 (where EVERY
        curve is hyperelliptic), the GENERIC genus-3 curve is NON-hyperelliptic (a smooth
        plane quartic); the HYPERELLIPTIC locus inside ``A₃`` is cut out by the VANISHING
        of **χ₁₈ = ∏ over the 36 even theta-nulls θ[ε](0|Ω)** — Igusa's weight-18 degree-3
        Siegel cusp form whose divisor is ``H₃ + 2D`` (H₃ the hyperelliptic locus, D the
        divisor at infinity); χ₁₈ vanishes EXACTLY on the genus-3 hyperelliptic locus
        (Bernatska–Kopeliovich, arXiv:2306.14889, p.1 — the exact sequence
        ``0 → χ₁₈𝔄(Γ₃) → 𝔄(Γ₃) →^ρ 𝒮(2,8)``, "χ₁₈ the cusp form of weight 18, defined
        as the product of all even theta constants"; van der Geer, *SMF Degree 2&3 +
        Invariant Theory*; classically Poor 1996, Grushevsky arXiv:1009.0369 Thm
        3.9/5.2). rc76 BUILDS χ₁₈ as the exact FORMAL q-series (the product of the 36
        even nulls — :meth:`chi18_leading_part` / :meth:`chi18_even_null_factors` /
        :meth:`chi18_leading_order_quarter`). What STAYS OPEN is the NUMERICAL decision:
        DECIDING "is THIS Ω hyperelliptic" is the POINT-EVALUATION ``χ₁₈(Ω) = 0`` at a
        transcendental ``Ω ∈ H₃`` (only knowable to N digits = float on the decision
        path), which the discipline forbids → NOT a finite exact (representable) carrier
        operation. The carrier provides the exact FORM (the construction χ₁₈ = the
        36-even-null product, its nonzero leading order, the genus-3 even-null
        enumeration :meth:`even_null_count`, the singular even null
        :meth:`singular_even_null`, the exact duplication relation
        :meth:`duplication_holds`) but REFUSES to fabricate a numerical hyperelliptic
        decision (the rc74 ``rosenhain_branch_point_recovery_is_open`` pattern).
        Returns the honest OPEN statement (a documentation string), never a verdict."""
        return (
            "OPEN (operand-side, transcendental period map): the numerical genus-3 "
            "HYPERELLIPTIC-locus decision — evaluating Igusa's χ₁₈ (the weight-18 "
            "degree-3 Siegel cusp form χ₁₈ = ∏ over the 36 even theta-nulls θ[ε](0|Ω), "
            "the modular form that cuts out the hyperelliptic locus in A₃, with divisor "
            "χ₁₈ = H₃ + 2D; Bernatska–Kopeliovich arXiv:2306.14889 p.1, van der Geer "
            "SMF Degree 2&3 + Invariant Theory, Poor 1996, Grushevsky arXiv:1009.0369 "
            "Thm 3.9/5.2) at a curve's transcendental period matrix Ω ∈ H₃ and testing "
            "χ₁₈(Ω) against zero — is NOT a finite exact carrier operation. The GENERIC "
            "genus-3 curve is NON-hyperelliptic (a smooth plane quartic), unlike genus 2 "
            "where every curve is hyperelliptic; the hyperelliptic locus is the "
            "vanishing even theta-null condition χ₁₈ = 0 (one of the 36 even nulls "
            "vanishes), which needs the transcendental "
            "theta evaluation at Ω (only knowable to N digits = float on the decision "
            "path), which the discipline forbids. The carrier BUILDS the FORMAL exact "
            "content (χ₁₈ as the exact product of the 36 even nulls — its nonzero "
            "leading q-order is 48 quarter-nome units = 12 in qᵢ; the 36-even / 28-odd "
            "null enumeration; the singular even null; the genus-3 duplication relation, "
            "all exact for ALL Ω); the numerical χ₁₈-vanishing / hyperelliptic decision "
            "is the documented operand-side OPEN — the framework refuses to fabricate a "
            "verdict here. (Schottky: genus 3 is STILL clean — dim M₃ = 6 = dim A₃, "
            "J₃ = A₃^ind; the Schottky frontier OPEN stays at g ≥ 4.)"
        )

    # ══════════════════════════════════════════════════════════════════════════
    # rc78: the genus-3 GÖPEL / FROBENIUS quadratic theta-null SYZYGY (the genus-3
    # analog of the rc74 genus-2 Göpel quadratic syzygy — completes the genus-3
    # rung-set: carrier rc75 → χ₁₈ rc76 → transform+addition rc77 → syzygy rc78)
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _g3_char_add_mod2(*chars: "Tuple[Tuple[int, int, int], Tuple[int, int, int]]"
                          ) -> "Tuple[Tuple[int, int, int], Tuple[int, int, int]]":
        """The exact GF(2) sum of genus-3 binary characteristics ``Σ [εᵢ] (mod 2)`` —
        pure integer / mod-2 (the characteristic group is ``(ℤ/2)⁶``). The genus-3
        analog of the genus-2 :meth:`RiemannTheta._char_add_mod2`. No float, no abs()
        (the group is its own inverse so subtraction IS addition; no sign branch)."""
        ep1 = ep2 = ep3 = e1 = e2 = e3 = 0
        for (epp, eps) in chars:
            ep1 += epp[0]
            ep2 += epp[1]
            ep3 += epp[2]
            e1 += eps[0]
            e2 += eps[1]
            e3 += eps[2]
        return ((ep1 % 2, ep2 % 2, ep3 % 2), (e1 % 2, e2 % 2, e3 % 2))

    @classmethod
    def goepel_syzygy_quad(cls) -> "Tuple[Tuple[..., ...], ...]":
        """The canonical genus-3 GÖPEL / FROBENIUS quadratic syzygy among the even
        theta-NULLS — FOUR PAIRS of even characteristics

            ( θ²[a]θ²[b], θ²[c]θ²[d], θ²[e]θ²[f], θ²[g]θ²[h] )

        satisfying the 4-term relation ``θ²[a]θ²[b] = θ²[c]θ²[d] + θ²[e]θ²[f]
        − θ²[g]θ²[h]`` (see :meth:`goepel_holds`). Returned as a 4-tuple of pairs of
        characteristics ``((a,b),(c,d),(e,f),(g,h))``.

        THE GENUS-3 SHAPE IS GENUINELY DIFFERENT FROM GENUS 2. The rc74 genus-2 Göpel
        syzygy is a 3-PAIR / 6-NULL relation (``θ²[a]θ²[b] = θ²[c]θ²[d] − θ²[e]θ²[f]``);
        the genus-3 relation among the even theta-nulls is a **4-PAIR / 8-NULL** relation.
        This is NOT a stylistic choice — the naive genus-2-style 3-pair / 6-null lift
        does NOT hold for genus 3 (an EXHAUSTIVE search over all 63 GF(2)-sum classes ×
        all 6-null common-sum triples finds NO 3-term genus-3 relation; the MINIMAL
        common-sum relation among the genus-3 ``θ²[m]θ²[m+s]`` products is 4-term, the
        nullspace's sparsest dependency). The extra term is the genuine genus-3 content
        — the third lattice direction's cross-terms ``C₁₃, C₂₃`` couple in.

        The eight characteristics are DISTINCT even theta-nulls; the four pairs share
        ONE common GF(2) characteristic sum ``[1,1,1; 1,1,1]`` (the genus-3
        Göpel-system / azygetic-configuration invariant — :meth:`goepel_is_syzygous`),
        the structural fingerprint of the Frobenius/Göpel relation (the genus-3
        specialization of the Riemann theta relation among theta squares — Glass, "Theta
        constants of genus three", *Compositio Mathematica* 40 (1980), §3, the **type-(2)
        "products of squares of theta constants"** degree-4 relations with coefficients
        ±1; Fiorentino–Salvati Manni, "On Frobenius' Theta Formula", *SIGMA* 16 (2020)
        057, §1–2 — the azygetic Göpel structure + the biquadratic Riemann relations
        eq. 2.1/2.3; Igusa, *Theta Functions* (1972) §IV/V; van der Geer, *Siegel Modular
        Forms of Degree Two and Three*). The canonical representative pairs

            a=[000;001] b=[111;110] | c=[000;010] d=[111;101]
            e=[001;000] f=[110;111] | g=[010;000] h=[101;111]

        all sum to the common characteristic ``[1,1,1; 1,1,1]``."""
        return (
            (((0, 0, 0), (0, 0, 1)), ((1, 1, 1), (1, 1, 0))),   # a, b  (+)
            (((0, 0, 0), (0, 1, 0)), ((1, 1, 1), (1, 0, 1))),   # c, d  (+)
            (((0, 0, 1), (0, 0, 0)), ((1, 1, 0), (1, 1, 1))),   # e, f  (+)
            (((0, 1, 0), (0, 0, 0)), ((1, 0, 1), (1, 1, 1))),   # g, h  (−)
        )

    @classmethod
    def goepel_is_syzygous(cls) -> bool:
        """True iff the canonical genus-3 Göpel quad is genuinely SYZYGOUS — the four
        pairs all share ONE common GF(2) characteristic sum, and the eight even
        theta-nulls are DISTINCT and all EVEN. This is the structural fingerprint that
        the relation is a genus-3 Göpel/Frobenius syzygy (a genus-3 Göpel system), not
        an accidental coincidence. Pure GF(2) algebra — exact, no float."""
        quad = cls.goepel_syzygy_quad()
        sums = [cls._g3_char_add_mod2(p[0], p[1]) for p in quad]
        if not all(s == sums[0] for s in sums):
            return False
        involved = [c for p in quad for c in p]
        if len(set(involved)) != 8:                    # eight DISTINCT nulls
            return False
        for (epp, eps) in involved:                    # all EVEN
            if (epp[0] * eps[0] + epp[1] * eps[1] + epp[2] * eps[2]) % 2 != 0:
                return False
        return True

    @staticmethod
    def _diag_restrict(lat: "Dict[_Sextuple, int]", bound: int) -> "Dict[_Sextuple, int]":
        """Keep ONLY the monomials whose DIAGONAL exponents ``A₁,A₂,A₃`` are each
        ``≤ bound`` — an exact, SOUND pre-filter for the safe-region Göpel comparison.
        Because the diagonal ``Aᵢ`` exponents are NON-NEGATIVE and ADD under the pair
        product (``Aᵢ(a²·b²) = Aᵢ(a²) + Aᵢ(b²)``), any product monomial with final
        ``Aᵢ ≤ bound`` can ONLY come from factors each with ``Aᵢ ≤ bound`` — so
        pre-restricting each squared factor by its diagonal A leaves the
        safe-region-restricted product BIT-IDENTICAL while skipping terms that can never
        survive. The cross-terms ``C_ij`` are left untouched here (the final restrict
        handles them). Exact integer, no float."""
        return {k: v for k, v in lat.items()
                if k[0] <= bound and k[1] <= bound and k[2] <= bound}

    @classmethod
    def _theta_null_g3_fourth_product(cls, pair, box: int) -> "Dict[_Sextuple, int]":
        """The exact-integer genus-3 lattice of ``θ²[a]·θ²[b]`` (a product of the
        SQUARES of two even genus-3 theta-nulls at the SAME Ω) for ``pair = (a, b)`` —
        the 4-fold convolution of the two rc75 genus-3 theta-null lattices, in the
        quarter-nome base, **pre-restricted on the diagonal A-exponents to the
        box-stable safe bound ``box²``** (sound — see :meth:`_diag_restrict`; the result
        is bit-identical to the unrestricted product after the final safe-region cut, but
        the pre-filter keeps the pure-Python convolution tractable). All-integer, no
        float (the per-term sign is the Class-K pin-slot baked into :meth:`lattice`)."""
        a, b = pair
        bound = box * box
        la = cls.theta_constant(a[0], a[1]).lattice(box)
        lb = cls.theta_constant(b[0], b[1]).lattice(box)
        sa = cls._diag_restrict(cls._square_lattice(la), bound)
        sb = cls._diag_restrict(cls._square_lattice(lb), bound)
        return cls._square_lattice_pair(sa, sb)

    @classmethod
    def goepel_lhs(cls, box: int) -> "Dict[_Sextuple, int]":
        """The LEFT side ``θ²[a]·θ²[b]`` of the canonical genus-3 Göpel syzygy (the
        product of two SQUARED even genus-3 theta-nulls at the SAME Ω). See
        :meth:`goepel_holds`."""
        return cls._theta_null_g3_fourth_product(cls.goepel_syzygy_quad()[0], box)

    @classmethod
    def goepel_rhs(cls, box: int) -> "Dict[_Sextuple, int]":
        """The RIGHT side ``θ²[c]·θ²[d] + θ²[e]·θ²[f] − θ²[g]·θ²[h]`` of the canonical
        genus-3 Göpel syzygy (the exact-integer lattice combination of three products of
        squared even genus-3 theta-nulls). The add/subtract is exact-integer coefficient
        arithmetic (the Class-K sign lives inside each theta-null lattice already). See
        :meth:`goepel_holds`."""
        quad = cls.goepel_syzygy_quad()
        cd = cls._theta_null_g3_fourth_product(quad[1], box)
        ef = cls._theta_null_g3_fourth_product(quad[2], box)
        gh = cls._theta_null_g3_fourth_product(quad[3], box)
        out: Dict[_Sextuple, int] = dict(cd)
        for k, v in ef.items():
            out[k] = out.get(k, 0) + v
        for k, v in gh.items():
            out[k] = out.get(k, 0) - v
        return {k: v for k, v in out.items() if v != 0}

    @classmethod
    def goepel_holds(cls, box: int = 3) -> bool:
        """rc78's EXACT CORE — the genus-3 FROBENIUS / GÖPEL quadratic theta-null syzygy

            θ²[a]·θ²[b]  =  θ²[c]·θ²[d]  +  θ²[e]·θ²[f]  −  θ²[g]·θ²[h]

        holds EXACTLY as a truncated exact-integer multivariate q-series, for ALL ``Ω``
        (the genus-3 specialization of the Riemann theta relation among theta squares —
        Glass, *Compositio Mathematica* 40 (1980) §3, the type-(2) "products of squares
        of theta constants" relations, coefficients ±1; Fiorentino–Salvati Manni, *SIGMA*
        16 (2020) 057, §1–2; Igusa, *Theta Functions* (1972) §IV/V). No transcendental
        evaluation, no float, no tolerance. It DISPATCHES the exact comparison to the
        native ``srmech_riemann_theta_g3_goepel`` C peer when loaded (a 1:1 exact-integer
        mirror, trusted only on a native hit); else the pure-Python body (the COMPLETE
        alternative + the parity oracle).

        GENUINELY NEW — DISTINCT FROM rc75 DUPLICATION, rc77 ADDITION, AND rc76 χ₁₈ (see
        :meth:`goepel_is_distinct_from_duplication_addition_and_chi18` for the no-shell
        proof). This is a relation among even theta-nulls all at the SAME Ω (no
        Ω-doubling), whereas BOTH duplication (``θ[0;0]² = Σ_c θ[c;0](2Ω)²``) and
        addition (``θ[a]θ[b] = Σ_r θ[…](2Ω)θ[…](2Ω)``) relate the nulls at Ω to nulls at
        2Ω; and it is a POLYNOMIAL relation among a SUBSET (8) of the even nulls, NOT the
        full 36-null χ₁₈ product.

        THE GENUS-3 SHAPE: a 4-PAIR / 8-NULL relation (vs genus-2's 3-pair / 6-null) —
        the genus-2-style 6-null lift does NOT hold for genus 3 (exhaustively checked),
        so the 4-term form is the genuine MINIMAL genus-3 syzygy.

        The two sides are compared on the SAFE INNER REGION the box ``|nᵢ| ≤ box``
        provably resolves. A product of four genus-3 theta-null lattices has each
        monomial's ``Aᵢ`` exponent a sum of squares ``(2nᵢ+ε'ᵢ)²``; a box-``box``
        truncation OMITS only terms from a factor at ``|nᵢ| = box+1``, i.e.
        ``≥ (2·box+1)²``, so monomials with each ``Aᵢ, |C_ij| ≤ box²`` (well below
        ``(2·box+1)²``) are FULLY accumulated — an inner region empirically box-STABLE
        (identical across box = 3, 4, 5). Returns ``True`` iff the two sides agree
        exactly on that region, the quad is genuinely syzygous
        (:meth:`goepel_is_syzygous`), and the region is non-trivially populated with a
        genuine genus-3 cross-term (``C₁₃`` or ``C₂₃`` ≠ 0) monomial (so the genus-3
        coupling is genuinely exercised — not the genus-2 / genus-1 slice).

        A CARRIER METHOD (the carrier's own build gate), not a public module-level op —
        ``tools.total`` is UNCHANGED (the rc72–rc77 ``*_holds`` precedent)."""
        if not isinstance(box, int) or box < 3:
            raise ValueError(
                f"box must be an int ≥ 3 for the genus-3 Göpel gate (the inner region "
                f"is box-stable from box=3); got {box!r}")
        if not cls.goepel_is_syzygous():
            return False
        safe = box * box                               # the box-stable inner bound

        def restrict(lat: "Dict[_Sextuple, int]") -> "Dict[_Sextuple, int]":
            kept: Dict[_Sextuple, int] = {}
            for k, v in lat.items():
                a1, a2, a3, c12, c13, c23 = k
                m12 = c12 if c12 >= 0 else -c12       # Class-K magnitude, no abs()
                m13 = c13 if c13 >= 0 else -c13
                m23 = c23 if c23 >= 0 else -c23
                if (a1 <= safe and a2 <= safe and a3 <= safe
                        and m12 <= safe and m13 <= safe and m23 <= safe):
                    kept[k] = v
            return kept

        nat = _native_g3_goepel()
        if nat is not None:
            try:
                got = nat.riemann_theta_g3_goepel_c(box)
                if got is not None:
                    holds, has_cross = got
                    return bool(holds) and bool(has_cross)
            except (RuntimeError, OverflowError, ValueError):
                pass                                   # fall to the pure path

        lhs = restrict(cls.goepel_lhs(box))
        rhs = restrict(cls.goepel_rhs(box))
        if lhs != rhs:
            return False
        return any((c13 != 0 or c23 != 0)              # genuine genus-3 cross-term
                   for (_a1, _a2, _a3, _c12, c13, c23) in lhs)

    @classmethod
    def goepel_is_distinct_from_duplication_addition_and_chi18(
            cls, box: int = 3) -> bool:
        """THE rc78 NO-SHELL PROOF: the genus-3 Göpel syzygy is GENUINELY DISTINCT from
        ALL THREE prior genus-3 relations — rc75 DUPLICATION, rc77 ADDITION, and rc76
        χ₁₈.

        STRUCTURAL: duplication and addition are Ω-vs-2Ω identities (their right sides
        live at 2Ω, carried with DOUBLED exponents via :meth:`_double_exps` / the
        eighth-nome-at-2Ω lattice). The Göpel syzygy is purely at Ω — every factor is a
        theta-null at Ω, NO Ω-doubling. χ₁₈ is the PRODUCT of ALL 36 even nulls (a
        weight-18 single object); the Göpel syzygy is a same-Ω POLYNOMIAL relation among
        a SUBSET of 8 even nulls (degree-4 in θ per term), not the 36-null product.

        EXACT (no-shell): (1) the Göpel LEFT side ``θ²[a]θ²[b]`` (a product of squares of
        two DISTINCT even nulls at Ω, degree-4) is checked NOT EQUAL to the duplication
        LHS ``θ[0;0]²`` (degree-2) NOR to ANY addition LHS ``θ[a]θ[b]`` (degree-2) on the
        safe region — different total theta-degree. (2) The Göpel LHS uses exactly 2 of
        the 8 syzygy nulls; the 8 syzygy nulls are a PROPER SUBSET of the 36 χ₁₈ factors
        (``8 < 36``) and the Göpel relation is a same-Ω sum, not a product — so it is not
        χ₁₈ nor any of its sub-structure. Returns ``True`` iff distinct from all three."""
        if not isinstance(box, int) or box < 3:
            raise ValueError(f"box must be an int ≥ 3; got {box!r}")
        bound = box * box
        goepel_lhs = cls._diag_restrict(cls.goepel_lhs(box), bound)  # deg-4, diag-bound
        # vs duplication LHS θ[0;0]² (degree-2), same diagonal bound: must differ
        if goepel_lhs == cls._diag_restrict(cls.duplication_lhs(box), bound):
            return False
        # vs every addition LHS θ[a]·θ[b] (degree-2), same diagonal bound: must differ
        for a1 in (0, 1):
            for a2 in (0, 1):
                for a3 in (0, 1):
                    for b1 in (0, 1):
                        for b2 in (0, 1):
                            for b3 in (0, 1):
                                add_lhs = cls._diag_restrict(
                                    cls.addition_lhs((a1, a2, a3), (b1, b2, b3), box),
                                    bound)
                                if goepel_lhs == add_lhs:
                                    return False
        # vs χ₁₈: the 8 syzygy nulls are a PROPER SUBSET of the 36 χ₁₈ factors, and the
        # Göpel relation is a same-Ω SUM (not the 36-null product) — structural distinct.
        syzygy_nulls = {c for p in cls.goepel_syzygy_quad() for c in p}
        chi18_factors = {f.characteristic for f in cls.chi18_even_null_factors()}
        if len(syzygy_nulls) != 8:
            return False
        if not syzygy_nulls.issubset(chi18_factors):
            return False                                # nulls must be genuine even nulls
        if len(chi18_factors) != 36 or len(syzygy_nulls) >= len(chi18_factors):
            return False                                # proper subset (8 < 36)
        return True


class RiemannThetaG4:
    """A numpy-free EXACT genus-4 Riemann theta-CONSTANT

        θ[ε'; ε](0 | Ω) = Σ_{n ∈ ℤ⁴} (−1)^{ε·n}
                            · Q₁^{A₁} Q₂^{A₂} Q₃^{A₃} Q₄^{A₄}
                            · Q₁₂^{C₁₂} Q₁₃^{C₁₃} Q₁₄^{C₁₄}
                              Q₂₃^{C₂₃} Q₂₄^{C₂₄} Q₃₄^{C₃₄} ,
        Aᵢ = (2nᵢ+ε'ᵢ)² ,   C_ij = (2nᵢ+ε'ᵢ)(2nⱼ+ε'ⱼ)   (SIX cross-terms, denom 4)

    — the NEXT RUNG of the GENUS axis (genus 4; the genus-4 analog of the rc75 genus-3
    :class:`RiemannThetaG3`), RESUMING the genus axis into the SCHOTTKY FRONTIER.
    Immutable. Holds the binary characteristic ``[ε'; ε]`` (eight bits in ``{0,1}``;
    the doubled half-integer characteristic over ``Ω ∈ H₄``, the genus-4 Siegel upper
    half space, ``Ω`` symmetric 4×4, dim ``g(g+1)/2 = 10``).

    THE OBJECT (Grushevsky, "The Schottky Problem", arXiv:1009.0369, eq. (1), the
    Riemann theta on the Siegel space ``H_g``; the genus-4 specialization ``g = 4``).
    There are **256 binary characteristics — 136 EVEN + 120 ODD** (``2^{g-1}(2^g±1)``
    for ``g = 4``: even ``8·17 = 136``, odd ``8·15 = 120``; ``136 + 120 = 256 = 4^g``;
    the empty-set even null ``[0,0,0,0;0,0,0,0]`` is the distinguished singular one). A
    characteristic is even iff ``ε'·ε ≡ 0 (mod 2)``.

    EXACT NOME-LATTICE REPRESENTATION (no float on the decision path). The carrier
    represents the theta-CONSTANT (``z = 0``) as an EXACT INTEGER exponent lattice over
    the nome alphabet (4 diagonal nomes + **SIX cross-terms** — vs genus-3's THREE
    cross-terms, **the genus-4 SCALING DIFFICULTY**)

        q₁=e^{iπΩ₁₁}, q₂=e^{iπΩ₂₂}, q₃=e^{iπΩ₃₃}, q₄=e^{iπΩ₄₄} ,
        q₁₂=e^{2iπΩ₁₂}, q₁₃=e^{2iπΩ₁₃}, q₁₄=e^{2iπΩ₁₄},
        q₂₃=e^{2iπΩ₂₃}, q₂₄=e^{2iπΩ₂₄}, q₃₄=e^{2iπΩ₃₄} ,

    cleared to integer exponents in the QUARTER-nome base ``Qᵢ = qᵢ^{1/4}``,
    ``Q_ij = q_ij^{1/4}``. With ``mᵢ = nᵢ + ½ε'ᵢ`` the quadratic form ``mᵀΩm`` over
    ``iπ`` expands as ``Σᵢ mᵢ²Ωᵢᵢ + 2Σ_{i<j} mᵢmⱼΩᵢⱼ`` and clearing the half-integers
    gives a term ``Π Qᵢ^{Aᵢ} · Π Q_ij^{C_ij} · (−1)^{ε·n}`` with EXACT INTEGER
    exponents ``Aᵢ = (2nᵢ+ε'ᵢ)²`` and ``C_ij = (2nᵢ+ε'ᵢ)(2nⱼ+ε'ⱼ)``. Each cross-term
    ``C_ij`` is a PRODUCT of two half-integers → a denominator-4 integer-lattice
    clearing, now across SIX coupled pairs ``{12,13,14,23,24,34}`` (the genuinely-new
    genus-4 content). The lattice is truncated to a box ``|nᵢ| ≤ box`` → ``(2·box+1)⁴``
    monomial terms — KEPT SMALL (``box = 2`` or ``3``); ``(2N+1)⁴`` grows fast, but the
    formal relations are box-stable. Each lattice coefficient is an exact INTEGER (a sum
    of ``±1`` lattice counts). The sign ``(−1)^{ε·n}`` is the **Class-K** pin-slot (an
    explicit ``±1`` branch, never an ALU ``abs()``).

    THE BUILD GATES (the genus-4 analogs of rc75's genus-3 first rung):

      * **collapse g4→g3 (primary):** :meth:`collapse_g3` of the trivial even
        characteristic ``[0,0,0,0; 0,0,0,0]`` collapses EXACTLY to the rc75 genus-3
        :class:`RiemannThetaG3` ``[0,0,0; 0,0,0]`` (set ``n₄ = 0``,
        ``q₄ = q₁₄ = q₂₄ = q₃₄ = 1``, ``ε'₄ = ε₄ = 0``) — bit-exact vs the existing
        rung; and the all-trivial chain ``→`` genus-3 → genus-2 → genus-1 θ₃
        (:meth:`collapse_g1_q_series`, ``[1,2,0,0,2,…]``). A characteristic with a
        NON-trivial 4th component HONESTLY REFUSES to collapse (raises — the rc75
        ``collapse_g2`` pattern, an honest boundary, not a fabricated reduction). THE
        foundation gate.

      * **formal genus-4 theta-null identity (secondary):** the genus-4 Gauss /
        duplication identity

            θ[0;0](0 | Ω)²  =  Σ_{c ∈ (½ℤ⁴/ℤ⁴)} θ[c; 0](0 | 2Ω)²     (16 summands)

        holds EXACTLY as a truncated exact-integer multivariate q-series, for ALL ``Ω``
        (no transcendental evaluation). The ``z₁ = z₂ = 0``, all-zero-characteristic
        specialization of the DLMF §21.6 addition formula with characteristics (DLMF
        eq. 21.6.8, the ``2^{-g}`` sum over ``ν ∈ ℤ^g/2ℤ^g`` of theta products at
        ``2Ω``; setting ``α=β=γ=δ=0`` and ``z₁=z₂=0`` collapses the two factors to one
        square and the sum to the ``2^g`` half-characteristics ``c = ½ν``, ``ν ∈
        {0,1}^g``; classically Mumford, *Tata Lectures on Theta I* (1983), the genus-g
        duplication; Chai, "Riemann's theta formula" (2014), Thm 1.2 example (b)). For
        ``g = 4`` the sixteen ``c ∈ {0,½}⁴`` — the sum includes (½,½,½,½) and mixed
        characteristics with ``C₁₄ ≠ 0``/``C₂₄ ≠ 0``/``C₃₄ ≠ 0``, so the identity
        genuinely exercises ALL SIX cross-terms (the genuinely-new genus-4 content), not
        just the genus-3 slice. See :meth:`duplication_lhs` / :meth:`duplication_rhs` /
        :meth:`duplication_holds`.

    THE SCHOTTKY FRONTIER (genus 4 turns it ON — the documented operand-side OPEN).
    Genus 4 is the FIRST genus where the Jacobian locus ``J₄`` is a PROPER subvariety of
    ``A₄`` (``dim M₄ = 3g−3 = 9 < dim A₄ = g(g+1)/2 = 10``) — the SCHOTTKY problem turns
    on. The cutter is the **Schottky form J** (a weight-8 degree-4 Siegel cusp form;
    Schottky 1888 = a degree-16 polynomial in the 136 even theta-nulls; Igusa 1981:
    ``J ∝ θ⁴(E₈⊕E₈) − θ⁴(E₁₆)``, the difference of the two rank-16 even-unimodular
    lattice theta-series that AGREE for ``g ≤ 3`` and first DIFFER at ``g = 4``; Poor &
    Yuen 1996: J generates the 1-dimensional space of level-1 genus-4 weight-8 cusp
    forms). ``J`` vanishes exactly on ``J₄``. The numerical "is THIS Ω a Jacobian"
    decision is a POINT-EVALUATION of J at a transcendental ``Ω ∈ H₄`` (only knowable to
    ``N`` digits = float on the decision path), which the discipline forbids → the
    operand-side OPEN (:meth:`schottky_locus_is_open` — the rc76
    ``hyperelliptic_locus_is_open`` pattern). rc80 DOCUMENTS this frontier; it does NOT
    build J or a numerical Jacobian decision (that is the rc81 capstone: the exact
    formal-q-series J via the ``E₈⊕E₈ − E₁₆`` lattice-theta difference, with the
    decision OPEN).

    THE REPRESENTABILITY BOUNDARY. The carrier is REPRESENTABLE (a finite exact
    decision): the canonical nome-monomial form + the finite Riemann relations, box
    pinned by the polarization level. What STAYS OPEN is the numerical Schottky / Jacobian
    decision (the transcendental point-evaluation above) — the operand-side OPEN this
    carrier names.

    Construct via :meth:`theta_constant` (the public entry). ``box`` (the lattice-box
    truncation ``|nᵢ| ≤ box``) is the finite generating rule, pinned by the requested
    truncation degree — KEEP IT SMALL (``(2·box+1)⁴`` grows fast)."""

    __slots__ = ("_ep1", "_ep2", "_ep3", "_ep4",
                 "_e1", "_e2", "_e3", "_e4")

    def __init__(self, ep1: int, ep2: int, ep3: int, ep4: int,
                 e1: int, e2: int, e3: int, e4: int) -> None:
        self._ep1 = _bit("ε'₁", ep1)
        self._ep2 = _bit("ε'₂", ep2)
        self._ep3 = _bit("ε'₃", ep3)
        self._ep4 = _bit("ε'₄", ep4)
        self._e1 = _bit("ε₁", e1)
        self._e2 = _bit("ε₂", e2)
        self._e3 = _bit("ε₃", e3)
        self._e4 = _bit("ε₄", e4)

    # ── construction ──────────────────────────────────────────────────────────
    @classmethod
    def theta_constant(cls, eps_prime: "Tuple[int, int, int, int]",
                       eps: "Tuple[int, int, int, int]") -> "RiemannThetaG4":
        """The genus-4 theta-constant ``θ[ε'; ε](0 | Ω)`` for a binary characteristic
        ``[ε'; ε]`` — ``eps_prime = (ε'₁, ε'₂, ε'₃, ε'₄)`` (the upper / lattice-shift
        half-integer characteristic) and ``eps = (ε₁, ε₂, ε₃, ε₄)`` (the lower / sign
        characteristic), each entry in ``{0, 1}``. The trivial even characteristic is
        ``theta_constant((0,0,0,0), (0,0,0,0))`` (= θ[0;0], the singular even null that
        collapses to the genus-3 trivial null and on to θ₃)."""
        return cls(eps_prime[0], eps_prime[1], eps_prime[2], eps_prime[3],
                   eps[0], eps[1], eps[2], eps[3])

    @classmethod
    def even_characteristics(cls) -> "List[RiemannThetaG4]":
        """The 136 EVEN genus-4 theta-constants (the even theta-nulls): all 256 binary
        characteristics ``[ε'; ε]`` with ``ε'·ε ≡ 0 (mod 2)`` (``2^{g-1}(2^g+1) = 136``
        even for ``g = 4``). The order is deterministic (lexicographic in
        ``ε'₁ε'₂ε'₃ε'₄ε₁ε₂ε₃ε₄``)."""
        out: List[RiemannThetaG4] = []
        for ep1 in (0, 1):
            for ep2 in (0, 1):
                for ep3 in (0, 1):
                    for ep4 in (0, 1):
                        for e1 in (0, 1):
                            for e2 in (0, 1):
                                for e3 in (0, 1):
                                    for e4 in (0, 1):
                                        if (ep1 * e1 + ep2 * e2 + ep3 * e3
                                                + ep4 * e4) % 2 == 0:
                                            out.append(cls(ep1, ep2, ep3, ep4,
                                                           e1, e2, e3, e4))
        return out

    # ── accessors ─────────────────────────────────────────────────────────────
    @property
    def characteristic(self) -> ("Tuple[Tuple[int, int, int, int], "
                                 "Tuple[int, int, int, int]]"):
        """The binary characteristic ``((ε'₁,ε'₂,ε'₃,ε'₄), (ε₁,ε₂,ε₃,ε₄))``."""
        return ((self._ep1, self._ep2, self._ep3, self._ep4),
                (self._e1, self._e2, self._e3, self._e4))

    @property
    def is_even(self) -> bool:
        """True iff the characteristic is EVEN (``ε'·ε ≡ 0 mod 2``) — i.e. an even
        theta-null. 136 of the 256 are even."""
        return (self._ep1 * self._e1 + self._ep2 * self._e2
                + self._ep3 * self._e3 + self._ep4 * self._e4) % 2 == 0

    @property
    def genus(self) -> int:
        """The genus — 4 for this carrier (the Schottky-frontier rung of the genus
        axis)."""
        return 4

    # ── the exact integer exponent lattice (the representable core) ────────────
    def lattice(self, box: int) -> "Dict[_Tentuple, int]":
        """The EXACT INTEGER exponent lattice
        ``{(A₁,A₂,A₃,A₄,C₁₂,C₁₃,C₁₄,C₂₃,C₂₄,C₃₄): coeff}`` of the genus-4 theta-constant,
        truncated to the box ``|nᵢ| ≤ box`` — the carrier's representable core. ``Aᵢ =
        (2nᵢ+ε'ᵢ)²`` are the diagonal integer exponents in the quarter-nome base ``Qᵢ``;
        ``C_ij = (2nᵢ+ε'ᵢ)(2nⱼ+ε'ⱼ)`` are the SIX cross-term exponents (each the genus-4
        denominator-4 clearing of a half-integer product); ``coeff`` is the exact integer
        ``Σ (−1)^{ε·n}`` over the ``n`` landing on that monomial. DISPATCHES to the native
        ``srmech_riemann_theta_g4`` C peer when loaded (a 1:1 exact-integer mirror — the C
        lattice EQUALS the Python lattice, trusted only on a native hit); else the
        pure-Python :meth:`_lattice_py` body (the COMPLETE alternative + the parity
        oracle). No float, no ``abs()`` (the ``(−1)^{ε·n}`` sign is the Class-K pin-slot),
        no numpy / ``math``."""
        if not isinstance(box, int) or box < 0:
            raise ValueError(f"box must be a non-negative int; got {box!r}")
        nat = _native_g4()
        if nat is not None:
            try:
                got = nat.riemann_theta_g4_lattice_c(
                    self._ep1, self._ep2, self._ep3, self._ep4,
                    self._e1, self._e2, self._e3, self._e4, box)
                if got is not None:
                    return got
            except (RuntimeError, OverflowError, ValueError):
                pass   # fall to the pure path
        return self._lattice_py(box)

    def _lattice_py(self, box: int) -> "Dict[_Tentuple, int]":
        """The COMPLETE pure-Python exponent lattice (the parity oracle for the C peer):
        exact integer ``(A₁,A₂,A₃,A₄,C₁₂,C₁₃,C₁₄,C₂₃,C₂₄,C₃₄) → coeff`` over the box
        ``|nᵢ| ≤ box``. Each cross-term ``C_ij = (2nᵢ+ε'ᵢ)(2nⱼ+ε'ⱼ)`` is the genus-4
        denominator-4 clearing (SIX of them); the sign ``(−1)^{ε·n}`` is the Class-K
        pin-slot (an explicit ``+1/−1`` branch, never an ALU ``abs()``). A bounded
        quadruple loop over the box (JPL Rule 2)."""
        ep1, ep2, ep3, ep4 = self._ep1, self._ep2, self._ep3, self._ep4
        e1, e2, e3, e4 = self._e1, self._e2, self._e3, self._e4
        out: Dict[_Tentuple, int] = {}
        for n1 in range(-box, box + 1):
            u1 = 2 * n1 + ep1
            for n2 in range(-box, box + 1):
                u2 = 2 * n2 + ep2
                for n3 in range(-box, box + 1):
                    u3 = 2 * n3 + ep3
                    for n4 in range(-box, box + 1):
                        u4 = 2 * n4 + ep4
                        a1 = u1 * u1
                        a2 = u2 * u2
                        a3 = u3 * u3
                        a4 = u4 * u4
                        c12 = u1 * u2
                        c13 = u1 * u3
                        c14 = u1 * u4
                        c23 = u2 * u3
                        c24 = u2 * u4
                        c34 = u3 * u4
                        # the per-term sign (−1)^{ε·n}: Class-K pin-slot (a stored ±1)
                        parity = (e1 * n1 + e2 * n2 + e3 * n3 + e4 * n4) % 2
                        sign = 1 if parity == 0 else -1   # never abs(); explicit ±
                        key = (a1, a2, a3, a4, c12, c13, c14, c23, c24, c34)
                        out[key] = out.get(key, 0) + sign
        return {k: v for k, v in out.items() if v != 0}

    # ── the genus-3 collapse (the foundation gate) ─────────────────────────────
    def collapse_g3(self) -> "RiemannThetaG3":
        """The genus-3 COLLAPSE (the primary foundation gate): set ``Ω₄₄ = Ω₁₄ = Ω₂₄ =
        Ω₃₄ = 0`` (⇒ ``q₄ = q₁₄ = q₂₄ = q₃₄ = 1``) and ``n₄ = 0`` (drop the fourth
        lattice direction). For the trivial even characteristic ``[0,0,0,0; 0,0,0,0]`` the
        surviving slice is the genus-3 trivial theta-null, returned as the rc75
        :class:`RiemannThetaG3` ``[0,0,0; 0,0,0]`` (so the collapse is BIT-EXACT vs the
        existing rung — verify with :meth:`collapse_g3_lattice_matches`). Only the trivial
        even characteristic collapses to the plain genus-3 trivial null; any
        characteristic with a NON-trivial 4th component (``ε'₄`` or ``ε₄`` set) is rejected
        — its genus-3 slice is a shifted/signed theta, not the plain rung (an honest
        boundary, not a fabricated reduction — the rc75 collapse pattern)."""
        if (self._ep1, self._ep2, self._ep3, self._ep4,
                self._e1, self._e2, self._e3, self._e4) != (0, 0, 0, 0, 0, 0, 0, 0):
            raise ValueError(
                "collapse_g3 is the genus-3 foundation gate: only the trivial even "
                "characteristic [0,0,0,0; 0,0,0,0] collapses to the rc75 genus-3 "
                f"trivial theta-null. The characteristic {self.characteristic} has a "
                "non-trivial 4th / signed component (a shifted/signed theta), not the "
                "plain genus-3 rung — an honest boundary, not a fabricated reduction.")
        return RiemannThetaG3(0, 0, 0, 0, 0, 0)

    def collapse_g3_lattice_matches(self, box: int = 3) -> bool:
        """PROVES the genus-3 collapse is GENUINE — it derives from the genus-4 lattice
        itself, not a hardcoded return. The genus-3 degeneration ``q₄ → 0`` /
        ``q₁₄, q₂₄, q₃₄ → 1`` keeps ONLY the ``n₄ = 0`` slice (for the trivial
        characteristic ``A₄ = (2n₄)² = 0 ⟺ n₄ = 0``, and then ``C₁₄ = C₂₄ = C₃₄ = 0``
        automatically), so projecting the genus-4 trivial lattice onto its
        ``A₄ = C₁₄ = C₂₄ = C₃₄ = 0`` slice and reading
        ``(A₁,A₂,A₃,C₁₂,C₁₃,C₂₃)`` reproduces the rc75 genus-3 trivial lattice EXACTLY.
        Returns ``True`` iff bit-exact (the no-shell collapse proof). Pure exact-integer
        comparison, no float."""
        if not isinstance(box, int) or box < 0:
            raise ValueError(f"box must be a non-negative int; got {box!r}")
        if (self._ep1, self._ep2, self._ep3, self._ep4,
                self._e1, self._e2, self._e3, self._e4) != (0, 0, 0, 0, 0, 0, 0, 0):
            raise ValueError(
                "collapse_g3_lattice_matches is the trivial-null foundation gate; "
                f"the characteristic {self.characteristic} does not collapse.")
        g4 = self.lattice(box)
        projected: Dict[_Sextuple, int] = {}
        for (a1, a2, a3, a4, c12, c13, c14, c23, c24, c34), v in g4.items():
            if a4 == 0 and c14 == 0 and c24 == 0 and c34 == 0:   # the n₄ = 0 slice
                key = (a1, a2, a3, c12, c13, c23)
                projected[key] = projected.get(key, 0) + v
        projected = {k: v for k, v in projected.items() if v != 0}
        g3 = RiemannThetaG3(0, 0, 0, 0, 0, 0).lattice(box)
        return projected == g3

    def collapse_g1_q_series(self, N: int) -> "List[int]":
        """The all-trivial genus-4 → genus-1 collapse's exact INTEGER q-series to order
        ``N``: ``[1, 2, 0, 0, 2, …]`` = ``θ₃``. The chain is genus-4 → genus-3
        (:meth:`collapse_g3`) → genus-2 → genus-1 (the rc75
        :meth:`RiemannThetaG3.collapse_g1_q_series`); bit-exact vs the rc70 θ₃ rung. Only
        the trivial even characteristic collapses the whole way (else :meth:`collapse_g3`
        raises — the honest boundary)."""
        return self.collapse_g3().collapse_g1_q_series(N)

    # ── equality / repr ───────────────────────────────────────────────────────
    def __eq__(self, other) -> bool:
        if isinstance(other, RiemannThetaG4):
            return ((self._ep1, self._ep2, self._ep3, self._ep4,
                     self._e1, self._e2, self._e3, self._e4)
                    == (other._ep1, other._ep2, other._ep3, other._ep4,
                        other._e1, other._e2, other._e3, other._e4))
        return NotImplemented

    def __ne__(self, other):
        r = self.__eq__(other)
        return r if r is NotImplemented else (not r)

    def __hash__(self) -> int:
        return hash((self._ep1, self._ep2, self._ep3, self._ep4,
                     self._e1, self._e2, self._e3, self._e4))

    def __repr__(self) -> str:
        return (f"RiemannThetaG4(genus=4, "
                f"eps_prime=({self._ep1},{self._ep2},{self._ep3},{self._ep4}), "
                f"eps=({self._e1},{self._e2},{self._e3},{self._e4}), "
                f"even={self.is_even})")

    # ── the formal genus-4 theta-null identity gate (Gauss duplication) ────────
    @staticmethod
    def _square_lattice(lat: "Dict[_Tentuple, int]") -> "Dict[_Tentuple, int]":
        """The exact-integer square ``lat · lat`` of a genus-4
        ``(A₁,A₂,A₃,A₄,C₁₂,C₁₃,C₁₄,C₂₃,C₂₄,C₃₄) → coeff`` lattice (a bounded convolution
        over the exponent 10-tuples; JPL Rule 2). All-integer, no float."""
        out: Dict[_Tentuple, int] = {}
        items = list(lat.items())
        for k1, v1 in items:
            for k2, v2 in items:
                key = (k1[0] + k2[0], k1[1] + k2[1], k1[2] + k2[2], k1[3] + k2[3],
                       k1[4] + k2[4], k1[5] + k2[5], k1[6] + k2[6],
                       k1[7] + k2[7], k1[8] + k2[8], k1[9] + k2[9])
                out[key] = out.get(key, 0) + v1 * v2
        return {k: v for k, v in out.items() if v != 0}

    @staticmethod
    def _double_exps(lat: "Dict[_Tentuple, int]") -> "Dict[_Tentuple, int]":
        """Re-express a genus-4 lattice computed at ``2Ω`` in the ``Ω``-nome alphabet:
        every quarter-nome exponent DOUBLES (``Qᵢ(2Ω) = Qᵢ(Ω)²``), so the whole 10-tuple
        ``↦ 2·10-tuple``. Exact integer relabel, no float."""
        return {tuple(2 * x for x in k): v for k, v in lat.items()}  # type: ignore[misc]

    @classmethod
    def duplication_lhs(cls, box: int) -> "Dict[_Tentuple, int]":
        """The LEFT side of the genus-4 Gauss/duplication theta-null identity
        ``θ[0; 0](0 | Ω)²`` (in the ``Ω`` quarter-nome alphabet) — the exact-integer square
        of the trivial even theta-constant's genus-4 lattice. See
        :meth:`duplication_holds`."""
        t0 = cls.theta_constant((0, 0, 0, 0), (0, 0, 0, 0)).lattice(box)
        return cls._square_lattice(t0)

    @classmethod
    def duplication_rhs(cls, box: int) -> "Dict[_Tentuple, int]":
        """The RIGHT side of the genus-4 Gauss/duplication theta-null identity
        ``Σ_{c ∈ (½ℤ⁴/ℤ⁴)} θ[c; 0](0 | 2Ω)²`` (re-expressed in the ``Ω`` quarter-nome
        alphabet via :meth:`_double_exps`, since each summand is at ``2Ω``). The SIXTEEN
        ``c`` are the half-characteristics ``{0,1}⁴`` (upper char ``c``, lower char ``0``
        — all even). See :meth:`duplication_holds`."""
        rhs: Dict[_Tentuple, int] = {}
        for c1 in (0, 1):
            for c2 in (0, 1):
                for c3 in (0, 1):
                    for c4 in (0, 1):
                        tc = cls.theta_constant((c1, c2, c3, c4),
                                                (0, 0, 0, 0)).lattice(box)
                        tc2 = cls._double_exps(tc)      # the summand is at 2Ω
                        sq = cls._square_lattice(tc2)
                        for k, v in sq.items():
                            rhs[k] = rhs.get(k, 0) + v
        return {k: v for k, v in rhs.items() if v != 0}

    @classmethod
    def duplication_holds(cls, box: int = 2) -> bool:
        """The FORMAL genus-4 theta-null identity gate (the secondary build gate): the
        genus-4 Gauss / duplication identity

            θ[0; 0](0 | Ω)²  =  Σ_{c ∈ (½ℤ⁴/ℤ⁴)} θ[c; 0](0 | 2Ω)²     (16 summands)

        holds EXACTLY as a truncated exact-integer multivariate q-series, for ALL ``Ω``
        (no transcendental evaluation). The ``z₁ = z₂ = 0``, all-zero-characteristic
        specialization of the DLMF §21.6 addition formula with characteristics (DLMF
        eq. 21.6.8 — the sum over ``ν ∈ ℤ^g/2ℤ^g`` of theta products at ``2Ω``; the
        all-zero / ``z = 0`` specialization collapses the two factors to one square and
        the sum to the ``2^g`` half-characteristics ``c = ½ν``, ``ν ∈ {0,1}^g``;
        classically Mumford, *Tata Lectures on Theta I* (1983), the genus-g duplication;
        Chai, "Riemann's theta formula" (2014), Thm 1.2 example (b)). This compares the
        two sides on the SAFE INNER REGION the box ``|nᵢ| ≤ box`` provably resolves (a
        box-``box`` theta omits only terms with a diagonal quarter-nome exponent
        ``≥ 4(box+1)²``, so monomials with each ``Aᵢ, |C_ij| ≤ 4·box²`` are fully
        accumulated). Because the sixteen ``θ[c; 0]`` include the (½,½,½,½) and mixed
        characteristics with ``C₁₄ ≠ 0``/``C₂₄ ≠ 0``/``C₃₄ ≠ 0``, the identity genuinely
        exercises ALL SIX cross-terms — it proves the carrier computes genuine genus-4
        theta-constants, not just the genus-3 slice. Returns ``True`` iff the two sides
        agree exactly on the safe region (and the region is non-trivially populated with a
        genuine genus-4 cross-term ``C₁₄``/``C₂₄``/``C₃₄`` monomial).

        A CARRIER METHOD (the carrier's own build gate), not a public module-level op —
        ``tools.total`` is unchanged (the rc75 ``duplication_holds`` precedent). NOTE: the
        box is kept SMALL (default 2) because ``(2·box+1)⁴`` grows fast — the formal
        identity is box-stable."""
        if not isinstance(box, int) or box < 2:
            raise ValueError(
                f"box must be an int ≥ 2 for the duplication gate; got {box!r}")
        lhs = cls.duplication_lhs(box)
        rhs = cls.duplication_rhs(box)
        safe = 4 * box * box

        def restrict(lat: "Dict[_Tentuple, int]") -> "Dict[_Tentuple, int]":
            kept: Dict[_Tentuple, int] = {}
            for k, v in lat.items():
                a1, a2, a3, a4, c12, c13, c14, c23, c24, c34 = k
                # Class-K magnitudes, no abs()
                mags = [c if c >= 0 else -c
                        for c in (c12, c13, c14, c23, c24, c34)]
                if (a1 <= safe and a2 <= safe and a3 <= safe and a4 <= safe
                        and all(m <= safe for m in mags)):
                    kept[k] = v
            return kept

        lhs_s = restrict(lhs)
        rhs_s = restrict(rhs)
        if lhs_s != rhs_s:
            return False
        # the gate must genuinely touch a genus-4 cross-term C₁₄/C₂₄/C₃₄ — else only the
        # genus-3 (C₁₂/C₁₃/C₂₃) slice would be exercised
        has_g4_cross = any(
            (c14 != 0 or c24 != 0 or c34 != 0)
            for (_a1, _a2, _a3, _a4, _c12, _c13, c14, _c23, c24, c34) in lhs_s)
        return has_g4_cross

    # ── the genus-4 enumeration + the documented Schottky-frontier OPEN ────────
    @classmethod
    def even_null_count(cls) -> "Tuple[int, int]":
        """The genus-4 even / odd theta-null counts ``(136, 120)`` — DERIVED from the
        enumeration (``2^{g-1}(2^g±1)`` for ``g = 4``: even ``8·17 = 136``, odd
        ``8·15 = 120``; ``136 + 120 = 256``; Grushevsky arXiv:1009.0369). The
        distinguished singular even null is the empty-set characteristic
        ``[0,0,0,0; 0,0,0,0]`` (see :meth:`singular_even_null`). Exact integer, no
        float."""
        even = cls.even_characteristics()
        n_even = len(even)
        n_odd = 256 - n_even
        return (n_even, n_odd)

    @classmethod
    def singular_even_null(cls) -> "RiemannThetaG4":
        """The distinguished SINGULAR even theta-null — the empty-set characteristic
        ``[0,0,0,0; 0,0,0,0]`` (the trivial even null, the one that collapses to the
        genus-3 trivial null and on to θ₃). Among the 136 even nulls it is the
        distinguished one (Grushevsky / Igusa)."""
        return cls.theta_constant((0, 0, 0, 0), (0, 0, 0, 0))

    @staticmethod
    def schottky_locus_is_open() -> str:
        """The DOCUMENTED operand-side OPEN — genus 4 TURNS ON the SCHOTTKY problem (the
        genus-axis frontier). Unlike ``g ≤ 3`` (where the Jacobian locus is everything —
        ``dim M_g = dim A_g``, ``J_g = A_g^ind``), genus 4 is the FIRST genus where the
        Jacobian locus ``J₄`` is a PROPER subvariety of ``A₄``: ``dim M₄ = 3g−3 = 9 <
        dim A₄ = g(g+1)/2 = 10``. The cutter is the **Schottky form J** — a weight-8
        degree-4 Siegel cusp form, Schottky's (1888) degree-16 polynomial in the 136 even
        theta-nulls; Igusa (1981) identified ``J ∝ θ⁴(E₈⊕E₈) − θ⁴(E₁₆)``, the difference
        of the genus-4 theta-series of the two rank-16 even-unimodular lattices (which
        AGREE for ``g ≤ 3`` and first DIFFER at ``g = 4``), with irreducible divisor of
        zeros; Poor & Yuen (1996) showed J generates the 1-dimensional space of level-1
        genus-4 weight-8 cusp forms. ``J`` vanishes EXACTLY on the Jacobian locus ``J₄``
        (Grushevsky arXiv:1009.0369; "Schottky form" — Schottky 1888, Igusa 1981, Poor &
        Yuen 1996). What STAYS OPEN is the NUMERICAL decision: DECIDING "is THIS Ω a
        Jacobian" is the POINT-EVALUATION ``J(Ω) = 0`` at a transcendental ``Ω ∈ H₄``
        (only knowable to N digits = float on the decision path), which the discipline
        forbids → NOT a finite exact (representable) carrier operation. rc80 BUILDS the
        exact genus-4 carrier (the lattice, the g4→g3 collapse, the genus-4 duplication
        relation, the 136-even / 120-odd enumeration, the singular even null) but DOCUMENTS
        (does not build) the Schottky form J and REFUSES to fabricate a numerical Jacobian
        decision (the rc76 ``hyperelliptic_locus_is_open`` pattern). The exact formal
        q-series J (via the ``E₈⊕E₈ − E₁₆`` lattice-theta difference) is the rc81 capstone,
        with the numerical decision the documented operand-side OPEN. Returns the honest
        OPEN statement (a documentation string), never a verdict."""
        return (
            "OPEN (operand-side, transcendental period map): the numerical genus-4 "
            "SCHOTTKY / JACOBIAN decision — evaluating the Schottky form J (the weight-8 "
            "degree-4 Siegel cusp form, Schottky's 1888 degree-16 polynomial in the 136 "
            "even theta-nulls; Igusa 1981: J ∝ θ⁴(E₈⊕E₈) − θ⁴(E₁₆), the difference of the "
            "two rank-16 even-unimodular lattice theta-series, irreducible divisor; Poor & "
            "Yuen 1996: J spans the 1-dim level-1 genus-4 weight-8 cusp-form space) at a "
            "transcendental period matrix Ω ∈ H₄ and testing J(Ω) against zero — is NOT a "
            "finite exact carrier operation. Genus 4 is the FIRST genus where the Schottky "
            "problem turns on: the Jacobian locus J₄ is a PROPER subvariety of A₄ "
            "(dim M₄ = 3g−3 = 9 < dim A₄ = g(g+1)/2 = 10), unlike g ≤ 3 where J_g = A_g^ind "
            "is everything; J vanishes exactly on J₄. Deciding it needs the transcendental "
            "theta evaluation at Ω (only knowable to N digits = float on the decision path), "
            "which the discipline forbids. rc80 BUILDS the exact genus-4 carrier content "
            "(the 4-diagonal + SIX-cross-term exponent lattice for all 256 characteristics; "
            "the g4→g3 collapse → genus-1 θ₃; the genus-4 duplication relation exercising "
            "all six cross-terms; the 136-even / 120-odd null enumeration; the singular even "
            "null — all exact for ALL Ω) but DOCUMENTS (does not build) the Schottky form J "
            "— the exact formal-q-series J via the E₈⊕E₈ − E₁₆ lattice-theta difference is "
            "the rc81 capstone; the numerical Schottky / Jacobian decision is the documented "
            "operand-side OPEN — the framework refuses to fabricate a verdict here. "
            "(Schottky frontier: g = 4 ON, solved by Schottky; g ≥ 5 genuinely OPEN.)"
        )


# the genus-g Gram key of a g-tuple of (doubled) lattice vectors — the upper-triangular
# doubled inner products (i ≤ j), an exact-integer tuple; the natural q-series exponent
# of the lattice theta-series (the diagonal q_i exponents + the off-diagonal q_ij)
_GramKey = Tuple[int, ...]


class SchottkyFormG4:
    """The genus-4 SCHOTTKY FORM **J** — the GENUS-4 CAPSTONE (the χ₁₈-analog at g = 4,
    the Siegel cusp form whose vanishing cuts the genus-4 Jacobian locus ``J₄ ⊂ A₄``;
    the SCHOTTKY PROBLEM's g = 4 solution: Schottky 1888 / Igusa 1981 / Poor–Yuen 1996).

    THE EXACT CONSTRUCTION (the lattice-theta-difference route)
    ==========================================================

    ``J`` is the weight-8 degree-4 level-1 Siegel CUSP form

        J  ∝  θ_{E₈⊕E₈}^{(4)}(Ω)  −  θ_{E₁₆}^{(4)}(Ω)

    — the DIFFERENCE of the genus-4 theta-SERIES of the TWO rank-16 even-unimodular
    lattices ``E₈⊕E₈`` and ``E₁₆ = D₁₆⁺`` (Wikipedia "Schottky form"; Igusa, "Schottky's
    invariant and quadratic forms", *Christoffel Symposium* (1981) — ``J ∝ θ⁴(E₈⊕E₈) −
    θ⁴(E₁₆)``; Poor & Yuen, *Math. Ann.* 1996 — J spans the 1-dimensional space of level-1
    genus-4 weight-8 Siegel cusp forms). Both are weight-``rank/2 = 8`` genus-4 Siegel
    modular forms; by Witt (1941) the two genus-g lattice theta-series are EQUAL for
    ``g ≤ 3`` and FIRST DIFFER at ``g = 4``, so their difference is the NONZERO Schottky
    cusp form J (the first-genus-4 obstruction). The lattices (Conway–Sloane SPLAG):

        E₈   = { x ∈ ℤ⁸  ∪ (ℤ+½)⁸  : Σxᵢ ≡ 0 (mod 2) }   (240 roots; even unimodular)
        E₁₆  = D₁₆⁺ = { x ∈ ℤ¹⁶ ∪ (ℤ+½)¹⁶ : Σxᵢ ≡ 0 (mod 2) }  (480 roots; even unimodular)

    both even (⟨v,v⟩ ∈ 2ℤ) and unimodular (det 1; E₈ via its Cartan-matrix Gram — even
    diagonal, det 1; D₁₆⁺ via the index argument ``det = det(D₁₆)/[D₁₆⁺:D₁₆]² = 4/4 = 1``).

    THE EXACT q-SERIES (no float on the decision path)
    ==================================================

    The genus-g lattice theta-series is the EXACT formal q-series

        θ_L^{(g)}(Ω) = Σ_{(v₁,…,v_g) ∈ L^g}  exp(iπ Σ_{i,j} ⟨vᵢ,vⱼ⟩ Ωᵢⱼ)

    Organized by the GRAM MATRIX ``T_ij = ⟨vᵢ,vⱼ⟩`` of the g-tuple, the coefficient of the
    monomial ``q^T`` is the EXACT INTEGER representation number ``r_L(T) =
    #{(v₁,…,v_g) ∈ L^g : Gram = T}``. So ``J``'s coefficient at ``T`` is the exact integer
    ``r_{E₈⊕E₈}(T) − r_{E₁₆}(T)`` — a numpy-free integer count, never a float. (In the
    RiemannThetaG4 quarter-nome base ``Qᵢ = qᵢ^{1/4}``, ``Q_ij = q_ij^{1/4}`` the exponents
    are ``Aᵢ = 4⟨vᵢ,vᵢ⟩``, ``C_ij = 4⟨vᵢ,vⱼ⟩`` — consistent with the rc80 carrier; the
    carrier works in the DOUBLED-vector integer model, where the doubled inner product
    ``⟨2vᵢ,2vⱼ⟩ = 4⟨vᵢ,vⱼ⟩`` IS exactly ``C_ij`` and the diagonal is ``Aᵢ``, so half-integer
    lattice coordinates become EXACT odd integers — no float anywhere.)

    THE LEADING SHELL (the exact, finite, load-bearing part — the χ₁₈ leading-part pattern)
    =====================================================================================

    ``J`` is a CUSP form: by Witt the Siegel Φ-operator (restriction to genus 3) kills it
    (``Φ(J) = θ³(E₈⊕E₈) − θ³(E₁₆) = 0``), so ``J``'s Fourier expansion starts at positive-
    definite (rank-4) ``T``. The exact, finite, no-float handle is the MINIMAL SHELL: at the
    leading order all g vectors are MINIMAL (norm 2; the 480 / 480 roots), and the Gram
    ``T`` is a g×g even positive-semidefinite integer matrix with diagonal 2 and off-diagonal
    in ``{−2,−1,0,1,2}`` (Cauchy–Schwarz). This carrier builds the genus-g minimal-shell
    representation numbers EXACTLY (:meth:`lattice_theta_minimal` / :meth:`J_minimal`) — the
    leading part of J. (Higher shells exist but the leading shell is the exact, finite,
    box-stable proof, exactly like the rc76 χ₁₈ leading part.)

    THE DEFINING SCHOTTKY GATE (gorgeous, no-shell — the first-genus-4 obstruction)
    ==============================================================================

      * **J VANISHES below genus 4** (:meth:`collapses_below_genus4`): the genus-1, genus-2
        AND genus-3 minimal-shell theta-series of ``E₈⊕E₈`` and ``E₁₆`` are EXACTLY EQUAL
        (every Gram's representation number agrees), so ``J|_{g≤3} ≡ 0`` (exact). This IS
        Witt 1941 made executable; it is also why ``J`` is a CUSP form.
      * **J IS NONZERO at genus 4** (:meth:`is_nonzero_at_genus4`): the genus-4 minimal-shell
        theta-series DIFFER — ``r_{E₈⊕E₈}(T) ≠ r_{E₁₆}(T)`` for a rank-4 Gram ``T`` (e.g. the
        D₄-star Gram ``T`` with ⟨1,2⟩=⟨1,3⟩=⟨1,4⟩=−1 rest 0: ``7 257 600 − 2 096 640 =
        5 160 960 ≠ 0``; and the orthogonal frame ``T = 2·I₄``: ``9 064 742 400 −
        8 858 304 000 = 206 438 400 ≠ 0`` — the famous genus-4 first difference).

    Both are EXACT integer counts (no float, no tolerance). Together they are the defining
    property of the Schottky form: the FIRST genus where the two theta-series part ways. The
    genus-4 orthogonal-frame difference 206 438 400 is computed by the C peer (the pure-Python
    body computes it too but the dense orthogonality graph is slow; the fast pure-Python
    certificate is the D₄-star Gram).

    THE WEIGHT-8 DEGREE-4 CUSP STRUCTURE (Igusa 1981, Poor–Yuen 1996)
    ================================================================

    ``J`` is weight ``rank/2 = 8``, degree (genus) 4, and — being killed by Φ (the genus-3
    restriction is 0) — a CUSP form; Poor & Yuen 1996 show it SPANS the 1-dimensional space
    ``S₈(Γ₄)`` of level-1 genus-4 weight-8 Siegel cusp forms (:meth:`weight`,
    :meth:`degree`, :meth:`is_cusp_form_structure`, :meth:`cusp_space_dimension`).

    THE OPERAND-SIDE OPEN (preserved; the rc80 ``schottky_locus_is_open`` upgraded)
    =============================================================================

    The numerical "is THIS Ω a Jacobian" decision — testing ``J(Ω) = 0`` at a transcendental
    period matrix ``Ω ∈ H₄`` (only knowable to N digits = float on the decision path) — STAYS
    the operand-side OPEN (the Schottky problem). This carrier BUILDS the exact FORM J (the
    lattice-theta difference, its exact leading-shell coefficients, the vanishing-below-g4 /
    nonzero-at-g4 gates) but REFUSES to fabricate a numerical Jacobian verdict
    (:meth:`jacobian_decision_is_open`). The exact FORM is representable; the transcendental
    point-evaluation is the OPEN — the dual faces of the operand program.

    THE C PEER (everything-mirrors, same-rc)
    ========================================

    ``srmech_riemann_theta_g4_schottky`` (``c/src/srmech_riemann_theta.c``) mirrors the heavy
    exact-integer minimal-shell g-tuple representation COUNT — a malloc-free, caller-arena,
    JPL-clean bitset count of ordered g-tuples of minimal (doubled) vectors with a prescribed
    doubled-Gram — for genus 2/3/4 over either lattice. The pure-Python body here is its
    COMPLETE alternative + parity oracle (both emit the byte-identical exact integer count).
    No new division algebra, no float, no ``abs()`` (the lattice is a pure integer count)."""

    __slots__ = ()

    # the canonical first-difference Gram (the orthogonal frame T = 2·I₄, doubled
    # off-diagonal all 0) and a FAST pure-Python differing Gram (the D₄-star, doubled
    # ⟨1,2⟩=⟨1,3⟩=⟨1,4⟩=−4 i.e. real −1, rest 0). Doubled inners: self 8, off ∈
    # {−8,−4,0,4,8}.
    _G4_ORTHO_FRAME = (0, 0, 0, 0, 0, 0)          # 2·I₄  (doubled off-diag, order 12,13,14,23,24,34)
    _G4_D4_STAR = (-4, -4, -4, 0, 0, 0)           # the fast pure-Python differing Gram

    # ── the two rank-16 even-unimodular lattices (minimal-vector shells) ───────────
    @staticmethod
    def _e8_minimal_doubled() -> "List[Tuple[int, ...]]":
        """The 240 minimal (norm-2 = root) vectors of E₈, in the DOUBLED-integer model
        (real coordinates ×2, so the all-half-integer roots become all-odd integers and
        nothing is a float). E₈ = {ℤ⁸ ∪ (ℤ+½)⁸, even coordinate sum}; the norm-2 vectors
        are (a) the 112 integer ``(±1,±1,0⁶)`` permutations [doubled ``(±2,±2,0⁶)``] and
        (b) the 128 half-integer ``(±½)⁸`` with an EVEN number of minus signs [doubled
        ``(±1)⁸``, even #minus]. Exact integer, no float."""
        vs: List[Tuple[int, ...]] = []
        for i in range(8):
            for j in range(i + 1, 8):
                for si in (1, -1):
                    for sj in (1, -1):
                        v = [0] * 8
                        v[i] = 2 * si
                        v[j] = 2 * sj
                        vs.append(tuple(v))
        for signs in _iter_signs(8):
            # even number of −1 (the E₈ glue parity); doubled half-int = the sign itself
            if sum(1 for s in signs if s == -1) % 2 == 0:
                vs.append(tuple(signs))
        return vs

    @classmethod
    def e8e8_minimal_doubled(cls) -> "List[Tuple[int, ...]]":
        """The 480 minimal (norm-2) vectors of ``E₈⊕E₈``, in the DOUBLED-integer model:
        a root of the first E₈ padded with eight zeros, or eight zeros then a root of the
        second E₈ (the 240 + 240 split; an E₈⊕E₈ minimal vector is minimal in exactly one
        summand). Exact integer, no float."""
        e8 = cls._e8_minimal_doubled()
        z8 = (0,) * 8
        out: List[Tuple[int, ...]] = []
        for r in e8:
            out.append(tuple(r) + z8)
        for r in e8:
            out.append(z8 + tuple(r))
        return out

    @staticmethod
    def e16_minimal_doubled() -> "List[Tuple[int, ...]]":
        """The 480 minimal (norm-2) vectors of ``E₁₆ = D₁₆⁺``, in the DOUBLED-integer
        model. D₁₆⁺ = {ℤ¹⁶ ∪ (ℤ+½)¹⁶, even coordinate sum}; the norm-2 vectors are exactly
        the 480 integer ``(±1,±1,0¹⁴)`` permutations [doubled ``(±2,±2,0¹⁴)``] — the
        half-integer glue coset ``(±½)¹⁶`` has minimum norm 16·¼ = 4 > 2, so it contributes
        NO minimal vectors. Exact integer, no float."""
        vs: List[Tuple[int, ...]] = []
        for i in range(16):
            for j in range(i + 1, 16):
                for si in (1, -1):
                    for sj in (1, -1):
                        v = [0] * 16
                        v[i] = 2 * si
                        v[j] = 2 * sj
                        vs.append(tuple(v))
        return vs

    # ── exact-integer minimal-shell representation counting (the carrier core) ─────
    @staticmethod
    def _doubled_inner(u: "Tuple[int, ...]", v: "Tuple[int, ...]") -> int:
        """The exact-integer DOUBLED inner product ``⟨2u_real, 2v_real⟩ = 4⟨u,v⟩`` of two
        doubled vectors — the q_ij exponent (off-diagonal) / q_i exponent (diagonal) in the
        RiemannThetaG4 quarter-nome base. A bounded dot product (JPL Rule 2), all integer,
        no float."""
        return sum(a * b for a, b in zip(u, v))

    @classmethod
    def _build_inner_bitsets(cls, vs: "List[Tuple[int, ...]]"
                             ) -> "Tuple[List[List[int]], int]":
        """Build, for each vector ``i`` and each doubled inner-product value ``t``, the
        BITSET ``S[i][t+8]`` of indices ``j`` with ``⟨2vᵢ,2vⱼ⟩ = t``. For minimal vectors
        ``t ∈ {−8,−4,0,4,8}`` (real ∈ {−2,−1,0,1,2}), so the 17-wide row ``t+8 ∈ 0..16``
        holds it. The bitset (a Python big-int) is the Class-L adjacency-by-inner-value the
        g-tuple count walks; exact, no float."""
        n = len(vs)
        S = [[0] * 17 for _ in range(n)]
        for i in range(n):
            vi = vs[i]
            for j in range(n):
                t = cls._doubled_inner(vi, vs[j])
                idx = t + 8
                if 0 <= idx <= 16:                # minimal-shell inner ∈ {−8..8}
                    S[i][idx] |= (1 << j)
        return S, n

    @staticmethod
    def _bit(S: "List[List[int]]", i: int, t: int) -> int:
        """The bitset ``S[i][t+8]`` (the indices ``j`` with doubled inner ``t``), or 0 if
        ``t`` is outside the minimal-shell range. Exact, no float."""
        idx = t + 8
        return S[i][idx] if 0 <= idx <= 16 else 0

    @classmethod
    def _count_gram_py(cls, S: "List[List[int]]", n: int,
                       gram_off: "Tuple[int, ...]") -> int:
        """The COMPLETE pure-Python exact count (the parity oracle for the C peer) of
        ordered g-tuples of minimal (doubled) vectors whose OFF-DIAGONAL doubled Gram is
        ``gram_off`` (the diagonal is all 8 = norm 2 by construction). ``gram_off`` length
        selects the genus: ``()`` → g=1 (just ``n``), ``(a₁₂,)`` → g=2,
        ``(a₁₂,a₁₃,a₂₃)`` → g=3, ``(a₁₂,a₁₃,a₁₄,a₂₃,a₂₄,a₃₄)`` → g=4. Counts via the
        inner-value bitsets (intersection + popcount — the Class-L adjacency walk; the sign
        never enters, it is a pure non-negative integer count, so NO ``abs()``). Bounded
        nested loops (JPL Rule 2), all-integer, no float / numpy / ``math``."""
        pc = int.bit_count
        m = len(gram_off)
        if m == 0:                                       # genus 1: every minimal vector
            return n
        if m == 1:                                       # genus 2
            a = gram_off[0]
            total = 0
            for i in range(n):
                total += pc(cls._bit(S, i, a))
            return total
        if m == 3:                                       # genus 3
            a, b, c = gram_off
            total = 0
            for i in range(n):
                bj = cls._bit(S, i, a)
                while bj:
                    j = (bj & -bj).bit_length() - 1
                    bj &= bj - 1
                    total += pc(cls._bit(S, i, b) & cls._bit(S, j, c))
            return total
        if m == 6:                                       # genus 4
            a, b, c, d, e, f = gram_off
            total = 0
            for i in range(n):
                bj = cls._bit(S, i, a)
                while bj:
                    j = (bj & -bj).bit_length() - 1
                    bj &= bj - 1
                    kk = cls._bit(S, i, b) & cls._bit(S, j, d)
                    while kk:
                        k = (kk & -kk).bit_length() - 1
                        kk &= kk - 1
                        total += pc(cls._bit(S, i, c)
                                    & cls._bit(S, j, e) & cls._bit(S, k, f))
            return total
        raise ValueError(
            f"gram_off must have length 0/1/3/6 (genus 1/2/3/4); got {m}")

    @classmethod
    def _count_gram(cls, vs: "List[Tuple[int, ...]]",
                    gram_off: "Tuple[int, ...]") -> int:
        """The exact count of ordered g-tuples of minimal vectors with off-diagonal doubled
        Gram ``gram_off`` — DISPATCHES to the native ``srmech_riemann_theta_g4_schottky``
        peer when loaded (a 1:1 exact-integer mirror — the C count EQUALS the Python count,
        trusted only on a native hit); else the pure-Python :meth:`_count_gram_py` body (the
        COMPLETE alternative + the parity oracle). Exact integer, no float."""
        nat = _native_g4_schottky()
        if nat is not None:
            try:
                got = nat.riemann_theta_g4_schottky_count_c(vs, gram_off)
                if got is not None:
                    return got
            except (RuntimeError, OverflowError, ValueError):
                pass                                     # fall to the pure path
        S, n = cls._build_inner_bitsets(vs)
        return cls._count_gram_py(S, n, gram_off)

    @classmethod
    def _full_shell_grams_py(cls, S: "List[List[int]]", n: int,
                             genus: int) -> "Dict[Tuple[int, ...], int]":
        """The COMPLETE pure-Python SINGLE-PASS minimal-shell Gram histogram (the parity
        oracle for the C peer): ``{off_gram (doubled, i<j): count}`` over ALL ordered
        g-tuples of minimal vectors, accumulated in ONE bitset walk (far faster than
        per-Gram enumeration). For genus 3 / 4 it enumerates the lower vectors and reads the
        upper vector's inner-product class from the bitsets; exact integer, no float / numpy
        / ``math`` / ``abs()`` (a pure non-negative count). Bounded nested loops (JPL Rule
        2)."""
        pc = int.bit_count
        out: Dict[Tuple[int, ...], int] = {}
        vals = (-8, -4, 0, 4, 8)
        if genus == 1:
            return {(): n}
        if genus == 2:
            for i in range(n):
                Si = S[i]
                for a in vals:
                    c = pc(Si[a + 8])
                    if c:
                        out[(a,)] = out.get((a,), 0) + c
            return out
        if genus == 3:
            for i in range(n):
                Si = S[i]
                for a in vals:                            # a = ⟨i,j⟩
                    bj = Si[a + 8]
                    while bj:
                        j = (bj & -bj).bit_length() - 1
                        bj &= bj - 1
                        Sj = S[j]
                        for b in vals:                    # b = ⟨i,k⟩
                            sib = Si[b + 8]
                            if not sib:
                                continue
                            for c in vals:                # c = ⟨j,k⟩
                                cnt = pc(sib & Sj[c + 8])
                                if cnt:
                                    key = (a, b, c)
                                    out[key] = out.get(key, 0) + cnt
            return out
        if genus == 4:
            for i in range(n):
                Si = S[i]
                for a in vals:                            # a = ⟨i,j⟩
                    bj = Si[a + 8]
                    while bj:
                        j = (bj & -bj).bit_length() - 1
                        bj &= bj - 1
                        Sj = S[j]
                        for b in vals:                    # b = ⟨i,k⟩
                            sib = Si[b + 8]
                            if not sib:
                                continue
                            for d in vals:                # d = ⟨j,k⟩
                                kk = sib & Sj[d + 8]
                                while kk:
                                    k = (kk & -kk).bit_length() - 1
                                    kk &= kk - 1
                                    Sk = S[k]
                                    for c in vals:        # c = ⟨i,l⟩
                                        sic = Si[c + 8]
                                        if not sic:
                                            continue
                                        for e in vals:    # e = ⟨j,l⟩
                                            base = sic & Sj[e + 8]
                                            if not base:
                                                continue
                                            for f in vals:    # f = ⟨k,l⟩
                                                cnt = pc(base & Sk[f + 8])
                                                if cnt:
                                                    key = (a, b, c, d, e, f)
                                                    out[key] = out.get(key, 0) + cnt
            return out
        raise ValueError(f"genus must be 1, 2, 3 or 4; got {genus!r}")

    @classmethod
    def lattice_theta_minimal(cls, which: str, genus: int) -> "Dict[_GramKey, int]":
        """The genus-``genus`` MINIMAL-SHELL lattice theta-series of one lattice, organized
        by Gram — ``{T_uppertri (doubled): r_L(T)}`` over ALL g-tuples of minimal vectors.
        ``which`` is ``"e8e8"`` (``E₈⊕E₈``) or ``"e16"`` (``E₁₆ = D₁₆⁺``); ``genus ∈
        {1,2,3,4}``. ``T_uppertri`` is the upper-triangular (i ≤ j) doubled-inner-product
        tuple (the diagonal entries are all 8 = norm 2; the off-diagonals are the q_ij
        exponents). This is the EXACT leading part of the genus-g lattice theta-series — a
        numpy-free integer representation-number map (no float). DISPATCHES the heavy
        single-pass Gram histogram to the native ``srmech_riemann_theta_g4_schottky_shell``
        peer when loaded (a 1:1 exact-integer mirror — trusted only on a native hit); else
        the pure-Python :meth:`_full_shell_grams_py` body (the COMPLETE alternative + the
        parity oracle). Built by the bitset g-tuple walk (the same engine the gates use)."""
        if genus not in (1, 2, 3, 4):
            raise ValueError(f"genus must be 1, 2, 3 or 4; got {genus!r}")
        vs = cls._lattice_vectors(which)
        off = None
        nat = _native_g4_schottky()
        if nat is not None and getattr(
                nat, "has_native_riemann_theta_g4_schottky_shell", lambda: False)():
            try:
                off = nat.riemann_theta_g4_schottky_shell_c(vs, genus)
            except (RuntimeError, OverflowError, ValueError):
                off = None
        if off is None:
            S, n = cls._build_inner_bitsets(vs)
            off = cls._full_shell_grams_py(S, n, genus)
        return {cls._gram_key(genus, k): v for k, v in off.items() if v != 0}

    @staticmethod
    def _lattice_vectors(which: str) -> "List[Tuple[int, ...]]":
        """The minimal (doubled) vectors of the named lattice — ``"e8e8"`` → ``E₈⊕E₈``,
        ``"e16"`` → ``E₁₆ = D₁₆⁺``. Rejects an unknown name loudly (an honest boundary)."""
        if which == "e8e8":
            return SchottkyFormG4.e8e8_minimal_doubled()
        if which == "e16":
            return SchottkyFormG4.e16_minimal_doubled()
        raise ValueError(
            f"which must be 'e8e8' (E₈⊕E₈) or 'e16' (E₁₆ = D₁₆⁺); got {which!r}")

    @staticmethod
    def _gram_key(genus: int, gram_off: "Tuple[int, ...]") -> "_GramKey":
        """The full upper-triangular doubled-Gram key ``(T₁₁,T₁₂,…,T_gg)`` (i ≤ j) from the
        off-diagonal pattern (the diagonal is all 8 for minimal vectors). Exact integer."""
        key: List[int] = []
        off = list(gram_off)
        p = 0
        for a in range(genus):
            for b in range(a, genus):
                if a == b:
                    key.append(8)                        # norm-2 diagonal (doubled)
                else:
                    key.append(off[p])
                    p += 1
        return tuple(key)

    @classmethod
    def J_minimal(cls, genus: int) -> "Dict[_GramKey, int]":
        """The genus-``genus`` MINIMAL-SHELL part of the Schottky form **J** — the EXACT
        INTEGER difference ``{T : r_{E₈⊕E₈}(T) − r_{E₁₆}(T)}`` over all g-tuple Grams ``T``
        of minimal vectors (the leading part of ``J = θ⁴(E₈⊕E₈) − θ⁴(E₁₆)``). For ``genus
        ≤ 3`` this is EMPTY (J vanishes below genus 4 — Witt 1941); for ``genus = 4`` it is
        NONZERO (the first-genus-4 obstruction). Exact integer, no float — the dict holds
        only the nonzero difference coefficients (the Gram monomials where the two
        theta-series part ways)."""
        a = cls.lattice_theta_minimal("e8e8", genus)
        b = cls.lattice_theta_minimal("e16", genus)
        keys = set(a) | set(b)
        out: Dict[_GramKey, int] = {}
        for k in keys:
            d = a.get(k, 0) - b.get(k, 0)
            if d != 0:
                out[k] = d
        return out

    # ── THE DEFINING SCHOTTKY GATE (no-shell; the first-genus-4 obstruction) ───────
    @classmethod
    def collapses_below_genus4(cls, max_genus: int = 3) -> bool:
        """THE DEFINING GATE (first half): ``J`` VANISHES identically below genus 4 — the
        genus-1, genus-2 AND genus-3 minimal-shell theta-series of ``E₈⊕E₈`` and ``E₁₆``
        agree EXACTLY (every Gram's representation number is equal), so ``J|_{g≤3} ≡ 0``.
        This is Witt's 1941 theorem made executable AND the reason ``J`` is a CUSP form (the
        Siegel Φ-operator, restriction to genus 3, kills it). Returns ``True`` iff the
        genus-1 … genus-``max_genus`` (default 3) minimal-shell theta-series are
        bit-exact-equal between the two lattices (equivalently :meth:`J_minimal` is EMPTY for
        each ``g ≤ max_genus``). Exact-integer comparison, no float.

        ``max_genus`` (≤ 3) lets a fast test check the cheap genus-1/2 vanishing without the
        heavier genus-3 pass; the DEFAULT 3 is the full ``J|_{g≤3} = 0`` proof.

        A CARRIER METHOD (the carrier's own build gate), not a public module-level op —
        ``tools.total`` is unchanged (the rc76 χ₁₈ / rc80 RiemannThetaG4 precedent)."""
        if max_genus not in (1, 2, 3):
            raise ValueError(
                f"max_genus must be 1, 2 or 3 (J's vanishing is below genus 4); "
                f"got {max_genus!r}")
        for g in range(1, max_genus + 1):
            if cls.J_minimal(g):                          # any nonzero difference ⇒ fail
                return False
        return True

    @classmethod
    def is_nonzero_at_genus4(cls) -> bool:
        """THE DEFINING GATE (second half): ``J`` is NONZERO at genus 4 — the genus-4
        minimal-shell theta-series of ``E₈⊕E₈`` and ``E₁₆`` DIFFER (some rank-4 Gram has
        ``r_{E₈⊕E₈}(T) ≠ r_{E₁₆}(T)``). This is the first-genus-4 obstruction — the FAMOUS
        first difference of the two genus-4 theta-series (the Schottky form's defining
        property). Returns ``True`` iff the FAST canonical differing Gram (the D₄-star
        :data:`_G4_D4_STAR`) has a nonzero ``E₈⊕E₈ − E₁₆`` count (so ``J ≠ 0`` at genus 4).
        Exact integer, no float — a pure non-negative count difference (no ``abs()``).

        (The full :meth:`J_minimal(4)` is also nonempty; this gate uses the single FAST
        certificate Gram to stay tractable in pure Python — the orthogonal-frame difference
        206 438 400 is the C-peer / :meth:`first_difference_orthogonal_frame` companion.)"""
        ca = cls._count_gram(cls.e8e8_minimal_doubled(), cls._G4_D4_STAR)
        cb = cls._count_gram(cls.e16_minimal_doubled(), cls._G4_D4_STAR)
        return (ca - cb) != 0

    @classmethod
    def genus4_first_difference_d4star(cls) -> "Tuple[int, int, int]":
        """The EXACT genus-4 minimal-shell representation counts at the D₄-star Gram (the
        FAST pure-Python differing certificate: doubled off-diagonal
        ⟨1,2⟩=⟨1,3⟩=⟨1,4⟩=−4, i.e. real −1, rest 0) — returns
        ``(r_{E₈⊕E₈}, r_{E₁₆}, difference)`` = ``(7 257 600, 2 096 640, 5 160 960)``. The
        nonzero difference is the no-shell witness ``J ≠ 0`` at genus 4. Exact integer."""
        ca = cls._count_gram(cls.e8e8_minimal_doubled(), cls._G4_D4_STAR)
        cb = cls._count_gram(cls.e16_minimal_doubled(), cls._G4_D4_STAR)
        return (ca, cb, ca - cb)

    @classmethod
    def first_difference_orthogonal_frame(cls) -> "Tuple[int, int, int]":
        """The EXACT genus-4 minimal-shell representation counts at the ORTHOGONAL FRAME
        Gram ``T = 2·I₄`` (four mutually-orthogonal norm-2 vectors; doubled off-diagonal all
        0) — returns ``(r_{E₈⊕E₈}, r_{E₁₆}, difference)`` = ``(9 064 742 400,
        8 858 304 000, 206 438 400)``, the FAMOUS genus-4 first difference of the two rank-16
        even-unimodular lattice theta-series. Exact integer. DISPATCHES to the C peer for
        speed (the dense orthogonality graph is slow in pure Python; the pure body is the
        complete alternative + parity oracle, computing the identical exact integer)."""
        ca = cls._count_gram(cls.e8e8_minimal_doubled(), cls._G4_ORTHO_FRAME)
        cb = cls._count_gram(cls.e16_minimal_doubled(), cls._G4_ORTHO_FRAME)
        return (ca, cb, ca - cb)

    @classmethod
    def schottky_gate_holds(cls) -> bool:
        """The COMBINED defining Schottky gate — ``True`` iff BOTH halves hold:
        :meth:`collapses_below_genus4` (``J|_{g≤3} ≡ 0``, exact) AND
        :meth:`is_nonzero_at_genus4` (``J|_{g=4} ≠ 0``, exact). This is the no-shell proof
        that ``J`` is the genuine genus-4 Schottky cusp form (the first-genus-4 obstruction),
        not a thin shell. Exact integer, no float."""
        return cls.collapses_below_genus4() and cls.is_nonzero_at_genus4()

    # ── the weight-8 degree-4 cusp-form structure (Igusa 1981, Poor–Yuen 1996) ─────
    @staticmethod
    def weight() -> int:
        """The weight of ``J`` — ``rank/2 = 16/2 = 8`` (a theta-series of a rank-16 lattice
        is a weight-8 modular form; the difference of two such is weight 8). Exact integer."""
        return 8

    @staticmethod
    def degree() -> int:
        """The degree (genus) of ``J`` — 4 (a genus-4 Siegel modular form). Exact integer."""
        return 4

    @classmethod
    def is_cusp_form_structure(cls) -> bool:
        """PROVES ``J`` has CUSP-FORM structure — the Siegel Φ-operator (restriction to
        genus 3) kills it: ``Φ(J) = θ³(E₈⊕E₈) − θ³(E₁₆) = 0`` (the genus-3 theta-series are
        equal — :meth:`collapses_below_genus4`), so ``J`` vanishes at the genus-4 cusp.
        Returns ``True`` iff the genus-3 restriction is exactly zero (J is a cusp form).
        Exact-integer, no float (Igusa 1981; Poor–Yuen 1996)."""
        return not cls.J_minimal(3)                       # Φ(J) = 0 ⟺ genus-3 diff empty

    @staticmethod
    def cusp_space_dimension() -> int:
        """The dimension of the level-1 genus-4 weight-8 Siegel CUSP-form space ``S₈(Γ₄)``
        — ``1`` (Poor & Yuen, *Math. Ann.* 1996: ``J`` SPANS this 1-dimensional space). An
        attested structural constant (the source of truth is Poor–Yuen 1996), not a magic
        number. Exact integer."""
        return 1

    # ── the documented operand-side OPEN (the Jacobian / Schottky decision) ────────
    @staticmethod
    def jacobian_decision_is_open() -> str:
        """The DOCUMENTED operand-side OPEN — the rc80 ``schottky_locus_is_open`` pattern,
        now upgraded to reference the BUILT J. The carrier BUILDS the exact FORM ``J`` (the
        ``E₈⊕E₈ − E₁₆`` lattice-theta difference; its exact leading-shell coefficients; the
        vanishing-below-g4 / nonzero-at-g4 gates; the weight-8 degree-4 cusp structure), but
        the NUMERICAL "is THIS Ω a Jacobian" decision — testing ``J(Ω) = 0`` at a
        transcendental period matrix ``Ω ∈ H₄`` (only knowable to N digits = float on the
        decision path) — STAYS the operand-side OPEN (the Schottky problem). The framework
        refuses to fabricate a numerical Jacobian verdict. Returns the honest OPEN statement
        (a documentation string), never a verdict."""
        return (
            "OPEN (operand-side, transcendental period map): the numerical genus-4 "
            "SCHOTTKY / JACOBIAN decision. rc81 BUILDS the exact Schottky form J as the "
            "lattice-theta difference J ∝ θ⁴(E₈⊕E₈) − θ⁴(E₁₆) (the two rank-16 even-"
            "unimodular lattices; Igusa 1981; Poor & Yuen 1996 — J spans the 1-dim level-1 "
            "genus-4 weight-8 Siegel cusp space) — the exact leading-shell representation-"
            "number coefficients, the DEFINING gate that J|_{g≤3} ≡ 0 (Witt 1941: the "
            "genus ≤ 3 theta-series are equal, so Φ(J) = 0 and J is a cusp form) AND "
            "J|_{g=4} ≠ 0 (the first-genus-4 obstruction: the orthogonal-frame counts "
            "9 064 742 400 − 8 858 304 000 = 206 438 400 ≠ 0), all EXACT integer counts. "
            "What STAYS OPEN is DECIDING 'is THIS Ω a Jacobian' — the POINT-EVALUATION "
            "J(Ω) = 0 at a transcendental Ω ∈ H₄ (only knowable to N digits = float on the "
            "decision path), which the discipline forbids → NOT a finite exact carrier "
            "operation. Genus 4 is the FIRST genus where J₄ is a PROPER subvariety of A₄ "
            "(dim M₄ = 9 < dim A₄ = 10); J vanishes exactly on J₄. The carrier provides "
            "the exact FORM; the numerical Jacobian decision is the documented operand-side "
            "OPEN — the framework refuses to fabricate a verdict here. (Schottky frontier: "
            "g = 4 ON, solved by Schottky; g ≥ 5 genuinely OPEN.)"
        )

    def __repr__(self) -> str:
        return ("SchottkyFormG4(weight=8, degree=4, "
                "J ∝ θ⁴(E₈⊕E₈) − θ⁴(E₁₆), cusp_space_dim=1)")
