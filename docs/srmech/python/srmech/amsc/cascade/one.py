"""The One — S(σ,θ): the single generator of the 1+3+7+3 = 14 substrate.

This module ships the unifying Hurwitz-ladder generator

.. math::

    S(\\sigma,\\theta) \\;=\\; \\bigoplus_{n=1}^{3}
        \\Big(\\, \\mathbb{R}\\cdot 1 \\;\\oplus\\;
                  \\sigma\\, e^{\\hat I_n\\theta}\\,\\mathrm{Im}\\,\\mathbb{A}_n \\,\\Big),
    \\qquad \\dim = \\sum_{n=1}^{3} 2^{n} = 2+4+8 = 14 .

with :math:`\\mathbb{A}_1=\\mathbb{C}` (dim 2, ``Im`` dim 1),
:math:`\\mathbb{A}_2=\\mathbb{H}` (dim 4, ``Im`` dim 3), and
:math:`\\mathbb{A}_3=\\mathbb{O}` (dim 8, ``Im`` dim 7) — the three normed
division algebras above :math:`\\mathbb{R}` (the Hurwitz ladder; the
parallelizable-sphere tower :math:`S^1, S^3, S^7`).

**This is "the One":** a single ``(σ, θ)``-parameterised object that holds
the entire 14-dimensional A–N substrate. The decomposition is *exactly* the
``1 + 3 + 7 + 3`` partition the framework discovered piecemeal:

============  ==================  ==================  ========================
``n``         ``ℝ·1`` (anchor)    ``Im 𝔸ₙ`` dim       A–N slots of ``Im 𝔸ₙ``
============  ==================  ==================  ========================
1  (ℂ)        1                   1                   ``A``
2  (ℍ)        1                   3                   ``I, C, J``
3  (𝕆)        1                   7                   ``D,E,F,G,K,L,M``
============  ==================  ==================  ========================

The three ``ℝ·1`` real units are the **+3 grammar** triad ``B, H, N`` — the
substrate-native language-translation operators between the continuous-Hopf
``e^{Îθ}`` description and the discrete-cyclic ``n=1,2,3`` enumeration (per
``[[user_stance_two_substrate_native_math_languages_11d_quantum_and_cyclic_algebra]]``).
``Σ Im = 1+3+7 = 11`` (the imaginary / operator substrate); ``+3`` grammar
units → ``14``.

**The rotation is the octonion-native epicycle.** ``e^{Î_n θ}`` is the
algebra's *own* rotation — conjugation by the unit ``cos(θ/2) + Î_n
sin(θ/2)`` — acting on ``Im 𝔸_n``. It fixes the axis ``Î_n`` (the last
imaginary unit ``e_{2ⁿ-1}``) and turns each **Fano-triple plane through
``Î_n``** by ``θ`` at once. The number of planes is ``(2ⁿ-1-1)/2`` —

============  ====================  ====================================
``n``         planes turned by θ    Im-rotation eigenvalues
============  ====================  ====================================
1  (ℂ)        0  →  only ``σ``       ``{σ}``
2  (ℍ)        1                      ``{1, e^{±iθ}}``
3  (𝕆)        3 (Fano triples)       ``{1, e^{±iθ}, e^{±iθ}, e^{±iθ}}``
============  ====================  ====================================

so the *single* θ-turn spins **three planes at once in 𝕆** (the ``1`` fixed
axis + ``3×2`` rotated split of the 7). The planes + orientations come from
the fixed Cayley–Dickson-from-ℍ Fano lines (Baez 2002 §2;
``srmech.qm.octonion``): ℍ's ``{1,2,3}`` → plane ``(e₁,e₂)``; 𝕆's
``{1,6,7},{2,5,7},{3,4,7}`` through ``Î₃=e₇`` → planes
``(e₁,e₆),(e₂,e₅),(e₃,e₄)`` (the first with reversed orientation,
``e₁e₆=-e₇``). The matrix realisation lives in :mod:`srmech.qm.hurwitz`,
which *derives* the same planes from ``octonion_mult_table`` — the bit-exact
Rosetta peer of this cascade form.

**Structural consequence — n=1 degenerates to σ.** At ``n=1`` the imaginary
part of ``ℂ`` is one-dimensional, so the seed ``e₁`` *is* the rotation axis
``Î₁`` and is fixed — ``θ`` does nothing and the **only** remaining freedom
is ``σ`` (``[[user_stance_epicycle_via_gear_plus_pin]]``: the epicycle *is*
the Class-K sign at the foundational algebra; richness then grows
``0 → 1 → 3`` planes up the ladder). ``σ ∈ {+1,-1}`` is the chirality — the
canonical **Class K pin-slot sign-flip** (never ``abs()``;
``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``) re-applied as
**Class C**.

Cascade decomposition (no new primitive class — a composition of A–N):

- ``⨁_{n=1}^{3}``  — the 3-fold grading            → **Class I** (cyclic enumerate)
- ``ℝ·1`` per block — the fixed real anchor          → the **B/H/N grammar** units
- ``e^{Î_n θ}``    — ``cos/sin`` exact rational      → **Class N** (``rational.*_series_truncate``)
- the Fano planes  — the algebra's own structure      → **Class A** (the attested octonion convention)
- ``σ``            — chirality                         → **Class K** (sign) ∘ **Class C** (apply)
- ``Im 𝔸_n``       — the 1:3:7 imaginary substrate

The generator is **numpy-free at import** and **exact-rational** in its core
(every entry a reduced ``(num, den)`` integer pair via the Class-N
``cos_series_truncate`` / ``sin_series_truncate`` Taylor partials). The
optional :meth:`One.to_numpy` / :meth:`One.to_matrix` float realisations
lazily import numpy (the ``srmech[scientific]`` tier, §22) — never at module
load (so the carrier ratchet must not count this module).

Canonical SSoT:
- Hurwitz (1898), *Über die Composition der quadratischen Formen* — the
  ``ℝ, ℂ, ℍ, 𝕆`` ladder is the complete list of normed division algebras.
- Baez, J.C. (2002) *The Octonions*, Bull. Amer. Math. Soc. 39, 145-205
  (arXiv:math/0105155) — the Fano-plane multiplication convention.
- ``[[user_stance_two_substrate_native_math_languages_11d_quantum_and_cyclic_algebra]]``
- ``[[user_stance_epicycle_via_gear_plus_pin]]``
- ``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from ..rational import (
    cos_series_truncate,
    sin_series_truncate,
    _reduce_rational,
)
from ..q import Q

# ──────────────────────────────────────────────────────────────────────
# Substrate constants — the 1+3+7+3 partition, named once.
# ──────────────────────────────────────────────────────────────────────

#: The three normed division algebras above ℝ (the Hurwitz ladder).
ALGEBRAS: Tuple[str, str, str] = ("C", "H", "O")

#: dim Im 𝔸ₙ = 2ⁿ − 1 for n = 1, 2, 3.
IMAG_DIMS: Tuple[int, int, int] = (1, 3, 7)

#: dim 𝔸ₙ = 2ⁿ for n = 1, 2, 3  (= ℝ·1 ⊕ Im).
BLOCK_DIMS: Tuple[int, int, int] = (2, 4, 8)

#: A–N class slots carried by each Im 𝔸ₙ (the 1 + 3 + 7 = 11 imaginary).
AN_IMAG_SLOTS: Tuple[Tuple[str, ...], ...] = (
    ("A",),                                  # Im ℂ  — foundational anchor
    ("I", "C", "J"),                         # Im ℍ  — substrate-projection triad
    ("D", "E", "F", "G", "K", "L", "M"),     # Im 𝕆  — cascade-detection heptad
)

#: The +3 grammar units — the three ℝ·1 reals (B/H/N translation operators).
GRAMMAR_SLOTS: Tuple[str, str, str] = ("B", "H", "N")

#: Oriented Fano planes through the rotation axis ``Î_n = e_{2ⁿ-1}``, WITHIN
#: each algebra 𝔸ₙ. Each ``(a, b, sign)`` means the imaginary units ``e_a``,
#: ``e_b`` (1-based; ``e_a → imag index a-1``) span a 2-plane that the
#: conjugation turns by θ, with ``e_a·e_b = sign·Î_n``. From the fixed
#: Cayley–Dickson-from-ℍ Fano lines (Baez 2002 §2; ``srmech.qm.octonion``):
#:   ℂ (axis e₁): none — Im is 1-D, only σ.
#:   ℍ (axis e₃): line {1,2,3} → (1,2,+1)                     — 1 plane.
#:   𝕆 (axis e₇): lines {1,6,7},{2,5,7},{3,4,7}
#:                → (1,6,−1),(2,5,+1),(3,4,+1)                — 3 planes.
#: ``srmech.qm.hurwitz`` derives this same tuple from ``octonion_mult_table``
#: (the bit-exact Rosetta cross-check).
FANO_PLANES: Tuple[Tuple[Tuple[int, int, int], ...], ...] = (
    (),                                          # n=1  ℂ
    ((1, 2, 1),),                                # n=2  ℍ
    ((1, 6, -1), (2, 5, 1), (3, 4, 1)),          # n=3  𝕆
)

#: The full dimension of the substrate: 2 + 4 + 8 = 14.
DIM: int = 14

#: Default Taylor truncation depth for ``e^{Îθ} = cos θ + Î sin θ``. The
#: Class-N series are exact-rational at any depth; 24 terms resolve θ across
#: ``[-π, π]`` to far below float epsilon. (Hard max is 50 per ``rational``.)
DEFAULT_TERMS: int = 24


def _chiral_scale(r: Tuple[int, int], sigma: int) -> Tuple[int, int]:
    """Apply the chirality σ ∈ {+1,-1} to a rational ``(num, den)``.

    This is the cascade-honest sign step: **Class K** validates the unit
    magnitude via explicit sign-branches (never an ALU ``abs()`` per
    ``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``) and
    **Class C** re-applies the orientation by negating the numerator.
    """
    if sigma != 1 and sigma != -1:
        raise ValueError(f"sigma (chirality) must be +1 or -1; got {sigma!r}")
    num, den = r
    if sigma == 1:
        return _reduce_rational(num, den)
    # Class C orientation reversal — negate the numerator, no abs().
    return _reduce_rational(-num, den)


@dataclass(frozen=True)
class Block:
    """One Hurwitz block ``ℝ·1 ⊕ σ e^{Î_n θ} Im 𝔸_n`` of ``S(σ,θ)``.

    Attributes
    ----------
    algebra : str
        ``"C"``, ``"H"`` or ``"O"``.
    n : int
        Ladder index ``1, 2, 3``.
    real : tuple[int, int]
        The ``ℝ·1`` anchor — always ``(1, 1)`` (the grammar unit, fixed by
        the rotation).
    imag : tuple[tuple[int, int], ...]
        The rotated seed ``σ e^{Î_n θ} e₁`` as exact rationals, length
        ``2ⁿ − 1`` — the orbit point of the first imaginary unit under the
        block's rotation (the full multi-plane rotation lives in
        :meth:`One.to_matrix`).
    an_imag_slots : tuple[str, ...]
        The A–N class slots labelling the imaginary axes.
    """

    algebra: str
    n: int
    real: Tuple[int, int]
    imag: Tuple[Tuple[int, int], ...]
    an_imag_slots: Tuple[str, ...]

    @property
    def dim(self) -> int:
        """``2ⁿ`` — the full algebra dimension (real anchor + imaginary)."""
        return 1 + len(self.imag)

    @property
    def grammar_slot(self) -> str:
        """The B/H/N grammar slot carried by this block's ``ℝ·1`` unit."""
        return GRAMMAR_SLOTS[self.n - 1]

    @property
    def rotated_planes(self) -> Tuple[Tuple[int, int, int], ...]:
        """The oriented Fano planes ``(a, b, sign)`` this block turns by θ.

        ``0 / 1 / 3`` planes for ℂ / ℍ / 𝕆 — the octonion-native epicycle
        structure (the single θ-turn spins all of them at once).
        """
        return FANO_PLANES[self.n - 1]


@dataclass(frozen=True)
class One:
    """The One — ``S(σ,θ)``, the single generator of the 14-D substrate.

    A numpy-free, exact-rational structured object. Build with
    :func:`the_one`. The three :class:`Block` instances tile the
    ``1+3+7+3 = 14`` A–N partition; :meth:`to_flat_rational` flattens to the
    14 exact rationals; :meth:`to_numpy` / :meth:`to_matrix` give the opt-in
    float realisations (the ``srmech[scientific]`` tier).
    """

    sigma: int
    theta: Tuple[int, int]
    terms: int
    blocks: Tuple[Block, Block, Block]

    # ── invariants (documentary + checkable) ──────────────────────────
    @property
    def dim(self) -> int:
        """The substrate dimension — always ``14`` (= 2 + 4 + 8)."""
        return DIM

    @property
    def imag_dims(self) -> Tuple[int, int, int]:
        """``(1, 3, 7)`` — the imaginary dimensions (the operator substrate)."""
        return IMAG_DIMS

    @property
    def partition(self) -> Tuple[int, int, int, int]:
        """``(1, 3, 7, 3)`` — the canonical A–N partition (imaginary + grammar)."""
        return (1, 3, 7, 3)

    @property
    def plane_counts(self) -> Tuple[int, int, int]:
        """``(0, 1, 3)`` — planes each block turns by θ (the octonion epicycle)."""
        return tuple(len(FANO_PLANES[i]) for i in range(3))

    @property
    def grammar_slots(self) -> Tuple[str, str, str]:
        """``('B', 'H', 'N')`` — the three ℝ·1 grammar / translation units."""
        return GRAMMAR_SLOTS

    @property
    def n1_is_sigma_only(self) -> bool:
        """``True`` — the structural prediction that θ is inert at ``n=1``.

        At ``n=1`` (``Im ℂ`` one-dimensional) the seed coincides with the
        rotation axis ``Î₁``, so the only freedom is the chirality ``σ``.
        Verified: the n=1 imaginary entry equals ``(σ, 1)`` independent of θ.
        """
        return self.blocks[0].imag == ((self.sigma, 1),)

    def to_flat_rational(self) -> Tuple[Tuple[int, int], ...]:
        """Flatten to the 14 exact rationals ``(num, den)`` of the state.

        Order: ``[ℝ·1, Im]`` per block, ℂ then ℍ then 𝕆 — length 14.
        """
        out = []
        for blk in self.blocks:
            out.append(blk.real)
            out.extend(blk.imag)
        return tuple(out)

    def to_matrix(self) -> "Mat":
        """The 14×14 block-diagonal operator ``G(σ,θ)`` as a numpy-free
        :class:`~srmech.amsc.mat.Mat` (real).

        ``G`` is ``⨁_n (1 ⊕ σ R_n(θ))`` — the identity on each ``ℝ·1`` axis
        and ``σ`` times the octonion-native rotation ``R_n(θ)`` on each
        ``Im 𝔸_n`` (turn every Fano plane through ``Î_n`` by θ; fix ``Î_n``
        and the real axis). Applying ``G`` to the canonical seed (real ``1``,
        imaginary ``e₁``) reproduces :meth:`to_flat_rational`. For 𝕆 this is
        a genuine **3-plane** rotation (eigenvalues ``{1, e^{±iθ}×3}`` on the
        imaginary part). This is the matrix the qm-peer
        :mod:`srmech.qm.hurwitz` must agree with (the Rosetta parity).
        """
        from srmech.amsc.mat import Mat

        cn, cd = cos_series_truncate(self.theta[0], self.theta[1], self.terms)
        sn, sd = sin_series_truncate(self.theta[0], self.theta[1], self.terms)
        cos_t = cn / cd
        sin_t = sn / sd
        s = float(self.sigma)
        g = [[0.0] * DIM for _ in range(DIM)]
        offset = 0
        for idx, d in enumerate(IMAG_DIMS):      # d = 1, 3, 7
            g[offset][offset] = 1.0              # ℝ·1 anchor — fixed
            imo = offset + 1                     # imaginary axes e₁..e_d
            for i in range(d):                   # default σ·identity on Im
                g[imo + i][imo + i] = s
            for (a, b, sgn) in FANO_PLANES[idx]:  # turn each Fano plane by θ
                ia, ib = imo + (a - 1), imo + (b - 1)
                g[ia][ia] = s * cos_t
                g[ib][ib] = s * cos_t
                g[ib][ia] = s * sgn * sin_t      # e_a → cosθ e_a + sgn sinθ e_b
                g[ia][ib] = -s * sgn * sin_t     # e_b → -sgn sinθ e_a + cosθ e_b
            offset += 1 + d
        return Mat.from_rows(g, is_complex=False)

    def to_scalar(self, mode: str = "trace", index: int = None,
                  *, as_float: bool = False):
        """Project the One down to a single scalar — the matrix→scalar member
        of the carrier's projection family (the scalar peer of
        :meth:`to_flat_rational`; the ``.to_scalar()`` read-out).

        EXACT by default and **numpy-free**: every mode returns a reduced
        ``(num, den)`` Class-N rational from integer arithmetic and the *same*
        ``cos_series_truncate`` the ``trigonometry`` / ``asymptotic_calculus``
        catalogs validate (no forked trig path — those catalogs are this
        scalar's target test). The exact ``(num, den)`` is the scalar peer of
        :meth:`to_flat_rational`. Float never ENTERS (the One's inputs are
        exact integers via :func:`the_one`); float only LEAVES, and only on
        request — ``as_float=True`` does the single terminal ``num/den`` cast
        to a **plain Python float with NO numpy** (the "return float sometimes"
        rule). *Unlike* :meth:`to_numpy` / :meth:`to_matrix` — the numpy-tier
        exports the carrier-removal arc (#564) is retiring — this float export
        needs no numpy at all. One boundary cast is not error summation; a
        *chain* of float ops would be
        (``[[feedback_no_numpy_rosetta_peer_continuous_float_error_collecting]]``).

        See the module-level :func:`to_scalar` for the full mode contract.
        """
        return to_scalar(self, mode=mode, index=index, as_float=as_float)

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return (
            f"One(sigma={self.sigma:+d}, theta={self.theta}, "
            f"terms={self.terms}, dim={self.dim}, partition={self.partition})"
        )


def the_one(sigma: int,
            theta_num: int,
            theta_den: int = 1,
            terms: int = DEFAULT_TERMS) -> One:
    """Build **the One** — ``S(σ,θ)`` — exact-rational and numpy-free.

    Parameters
    ----------
    sigma : int
        Chirality ``σ ∈ {+1, -1}`` — the Class-K pin-slot sign-flip.
    theta_num, theta_den : int
        The epicycle angle ``θ = theta_num / theta_den`` in radians
        (``theta_den`` defaults to ``1``; ``theta_den > 0``). ``e^{Î_n θ}``
        is built as the exact-rational ``cos θ + Î_n sin θ`` (the
        octonion-native conjugation rotation on ``Im 𝔸_n``).
    terms : int
        Class-N Taylor truncation depth for ``cos``/``sin`` (default
        :data:`DEFAULT_TERMS`; exact-rational at any depth).

    Returns
    -------
    One
        The structured generator: three :class:`Block` s tiling
        ``1+3+7+3 = 14``.

    Examples
    --------
    >>> s = the_one(+1, 0, 1)          # θ = 0  → the σ-seed (no rotation)
    >>> s.dim
    14
    >>> s.partition
    (1, 3, 7, 3)
    >>> s.plane_counts                 # 0/1/3 planes — the octonion epicycle
    (0, 1, 3)
    >>> s.blocks[0].imag               # n=1 (ℂ): θ-inert, pure σ
    ((1, 1),)
    >>> the_one(-1, 99, 100).n1_is_sigma_only   # n=1 = σ at any θ
    True
    """
    if sigma != 1 and sigma != -1:
        raise ValueError(f"sigma (chirality) must be +1 or -1; got {sigma!r}")
    if not isinstance(theta_num, int) or not isinstance(theta_den, int):
        raise TypeError("theta_num and theta_den must be int")
    if theta_den <= 0:
        raise ValueError(f"theta_den must be positive; got {theta_den}")

    # e^{Î_n θ} = cos θ + Î_n sin θ — exact-rational Class-N partials.
    cos_t = cos_series_truncate(theta_num, theta_den, terms)
    sin_t = sin_series_truncate(theta_num, theta_den, terms)

    blocks = []
    for idx, d in enumerate(IMAG_DIMS):          # d = 1, 3, 7  (n = idx+1)
        planes = FANO_PLANES[idx]
        imag = [(0, 1)] * d
        # The state is the seed e₁ (octonion index 1 → imag index 0) under
        # σ·R_n(θ). e₁ lies in exactly one Fano plane (a=1) — or, for ℂ, it
        # IS the rotation axis and is fixed (θ-inert; only σ).
        host = next(((a, b, s) for (a, b, s) in planes if a == 1), None)
        if host is None:
            imag[0] = _chiral_scale((1, 1), sigma)          # ℂ: σ only
        else:
            _, b, s = host                                   # e₁ → cosθ e₁ + s·sinθ e_b
            imag[0] = _chiral_scale(cos_t, sigma)            # σ cos θ on e₁
            imag[b - 1] = _chiral_scale(sin_t, sigma * s)    # σ·s sin θ on e_b
        blocks.append(Block(
            algebra=ALGEBRAS[idx],
            n=idx + 1,
            real=(1, 1),
            imag=tuple(imag),
            an_imag_slots=AN_IMAG_SLOTS[idx],
        ))

    return One(
        sigma=sigma,
        theta=_reduce_rational(theta_num, theta_den),
        terms=terms,
        blocks=(blocks[0], blocks[1], blocks[2]),
    )


#: ``S(σ,θ)`` — the formula-name alias for :func:`the_one`.
s_generator = the_one


def to_scalar(one: "One",
              mode: str = "trace",
              index: int = None,
              *,
              as_float: bool = False):
    """Project the exact :class:`One` down to a single scalar — the
    matrix/vector→scalar boundary of the carrier's projection family (the
    scalar peer of :meth:`One.to_flat_rational`), **numpy-free**.

    The math is EXACT and the inputs are EXACT: a One is built from integer
    ``(σ, θ_num, θ_den)`` (:func:`the_one`) — float never *enters*. Every mode
    returns a reduced ``(num, den)`` Class-N rational from integer arithmetic
    (the scalar peer of :meth:`One.to_flat_rational`). Float only *leaves*, and
    only on request: ``as_float=True`` does the single terminal ``num/den``
    cast to a **plain Python float — no numpy** (the "return float sometimes"
    rule). *Unlike* :meth:`One.to_numpy` / :meth:`One.to_matrix` (the numpy
    ``[scientific]``-tier exports the carrier-removal arc #564 is retiring),
    this float export needs no numpy. One boundary cast ≠ error summation; a
    *chain* of float ops would be
    (``[[feedback_no_numpy_rosetta_peer_continuous_float_error_collecting]]``).

    This is bindable as a TOML-class method op
    (``op = "srmech.amsc.cascade.to_scalar"``) so a class can chain
    matrix-math → scalar output (the genome-update class-from-TOML way).

    Parameters
    ----------
    one : One
    mode : {"trace", "sqnorm", "component"}, default "trace"
        - ``"trace"`` — the exact rotation character
          ``Tr G(σ,θ) = 3 + 3σ + 8σ·cos θ`` (the 0/1/3-plane diagonal of
          :meth:`One.to_matrix`). ``cos θ`` is the **same** Class-N
          ``cos_series_truncate`` the ``trigonometry`` / ``asymptotic_calculus``
          catalogs validate — those catalogs are this scalar's *target test*
          (no forked trig path).
        - ``"sqnorm"`` — the exact squared length ``Σ (num/den)²`` over the 14
          state rationals (pure integer arithmetic; no trig, no ``abs``/``sqrt``).
        - ``"component"`` — the ``index``-th of the 14 exact rationals (the
          literal scalar read-out; ``index`` required, ``0 ≤ index < 14``).
    index : int, optional
        Required for ``mode="component"``.
    as_float : bool, default False
        If True, return ``float(num/den)`` (the opt-in terminal export);
        otherwise the exact ``(num, den)``.

    Returns
    -------
    tuple[int, int] | float
        Exact ``(num, den)`` (default) or a Python float (``as_float=True``).
    """
    if not isinstance(one, One):
        raise TypeError(
            f"to_scalar expects a One; got {type(one).__name__}")
    if mode == "component":
        if index is None:
            raise ValueError("mode='component' requires index= (0..13)")
        flat = one.to_flat_rational()
        if not 0 <= index < len(flat):
            raise IndexError(
                f"index {index} out of range 0..{len(flat) - 1}")
        num, den = flat[index]
    elif mode == "sqnorm":
        # Σ (num/den)² — exact integer arithmetic; squaring is sign-free so no
        # Class-K branch is needed (a magnitude with no abs()/sqrt at this level).
        acc_num, acc_den = 0, 1
        for (n, d) in one.to_flat_rational():
            t_num, t_den = n * n, d * d
            acc_num, acc_den = _reduce_rational(
                acc_num * t_den + t_num * acc_den, acc_den * t_den)
        num, den = acc_num, acc_den
    elif mode == "trace":
        # Tr G(σ,θ) = 3 + 3σ + 8σ·cos θ — the rotation character. cos θ is the
        # SAME Class-N catalog primitive (trigonometry / asymptotic_calculus),
        # so this scalar is correct iff that catalog cos is correct.
        cn, cd = cos_series_truncate(one.theta[0], one.theta[1], one.terms)
        s = one.sigma
        num, den = _reduce_rational((3 + 3 * s) * cd + 8 * s * cn, cd)
    else:
        raise ValueError(
            f"mode must be 'trace', 'sqnorm' or 'component'; got {mode!r}")
    if as_float:
        return num / den          # the single terminal lossy cast (no numpy)
    # The exact scalar-rational carrier (F868 stay-rational): float never
    # enters, the value compares like a float, and the raw ``(num, den)`` is
    # always recoverable (``q.numerator`` / ``q.denominator`` / ``num, den = q``).
    # Replaces the awkward bare tuple this used to hand back.
    return Q(num, den)


# ──────────────────────────────────────────────────────────────────────
# Flat cascade-op accessors — the make_class two-layer binding surface.
#
# ``one.toml`` (the packaged ``[class] One``) binds its methods to these by
# dotted path — the genome **two-layer pattern**: ship each accessor as a
# module-level flat op, then bind it in the ``[class]`` TOML. Each takes the
# constructed :class:`One` as its sole bind (the descriptor's ``one`` field),
# mirroring the module-level :func:`to_scalar` above. They are reachable ONLY
# through the class TOML (a :func:`~srmech.dsl.make_class` method), NOT the MCP
# tool list — exempt in the tool-schema coverage gate exactly like
# :func:`to_scalar`. This realises "prefer config-driven ``[class]`` TOML over
# hand-coding domain classes" (``[[feedback_prefer_config_driven_toml_classes]]``)
# for the substrate generator itself: ``One`` becomes a declarative class whose
# accessors are cascade-op refs.
# ──────────────────────────────────────────────────────────────────────

def one_dim(one: "One") -> int:
    """Flat-op accessor — the substrate dimension (always 14). See :attr:`One.dim`."""
    return one.dim


def one_imag_dims(one: "One") -> Tuple[int, int, int]:
    """Flat-op accessor — ``(1, 3, 7)`` imaginary dims. See :attr:`One.imag_dims`."""
    return one.imag_dims


def one_partition(one: "One") -> Tuple[int, int, int, int]:
    """Flat-op accessor — the ``(1, 3, 7, 3)`` A–N partition. See :attr:`One.partition`."""
    return one.partition


def one_plane_counts(one: "One") -> Tuple[int, int, int]:
    """Flat-op accessor — ``(0, 1, 3)`` planes per block. See :attr:`One.plane_counts`."""
    return one.plane_counts


def one_grammar_slots(one: "One") -> Tuple[str, str, str]:
    """Flat-op accessor — ``('B','H','N')`` grammar units. See :attr:`One.grammar_slots`."""
    return one.grammar_slots


def one_flat_rational(one: "One") -> Tuple[Tuple[int, int], ...]:
    """Flat-op accessor — the 14 exact rationals. See :meth:`One.to_flat_rational`."""
    return one.to_flat_rational()


def one_matrix(one: "One"):
    """Flat-op accessor — the 14×14 numpy-free :class:`~srmech.amsc.mat.Mat`
    operator ``G(σ,θ)``. See :meth:`One.to_matrix`."""
    return one.to_matrix()


__all__ = [
    "ALGEBRAS",
    "IMAG_DIMS",
    "BLOCK_DIMS",
    "AN_IMAG_SLOTS",
    "GRAMMAR_SLOTS",
    "FANO_PLANES",
    "DIM",
    "DEFAULT_TERMS",
    "Block",
    "One",
    "the_one",
    "s_generator",
    "to_scalar",
    # flat cascade-op accessors — the one.toml ([class] One) binding surface
    "one_dim",
    "one_imag_dims",
    "one_partition",
    "one_plane_counts",
    "one_grammar_slots",
    "one_flat_rational",
    "one_matrix",
]
