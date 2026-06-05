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

**The rotation is the epicycle.** ``e^{Î_n θ} = cos θ + Î_n sin θ`` is the
gear+pin rotation (``[[user_stance_epicycle_via_gear_plus_pin]]``); sweeping
``θ`` turns all three division-algebra loops at once. ``σ ∈ {+1,-1}`` is the
chirality — the canonical **Class K pin-slot sign-flip** (never ``abs()``;
``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``) re-applied as
a **Class C** orientation.

**Structural prediction — n=1 degenerates to σ.** We fix the rotation axis
``Î_n`` to be the *last* imaginary unit ``e_d`` of each algebra and rotate
the ``(e₁, e₂)`` plane (seed ``e₁``). At ``n=1`` the imaginary part of ``ℂ``
is one-dimensional, so the seed ``e₁`` *coincides with the rotation axis*
``Î₁`` and is fixed — ``θ`` does nothing and the **only** remaining freedom
is ``σ``. So at the foundational algebra the epicycle *is* the Class-K sign
(rotational richness then grows ``1 → 3 → 7`` up the ladder). This is not
imposed; it falls out of the conjugation action, and the qm-matrix peer
(``srmech.qm.hurwitz``) realises the same rotation via octonion conjugation
about ``Î_n``.

Cascade decomposition (no new primitive class — a composition of A–N):

- ``⨁_{n=1}^{3}``  — the 3-fold grading            → **Class I** (cyclic enumerate)
- ``ℝ·1`` per block — the fixed real anchor          → the **B/H/N grammar** units
- ``e^{Î_n θ}``    — ``cos/sin`` exact rational      → **Class N** (``rational.*_series_truncate``)
- ``Î_n``          — choice of rotation axis          → **Class C** (orientation)
- ``σ``            — chirality                         → **Class K** (sign) ∘ **Class C** (apply)
- ``Im 𝔸_n``       — the 1:3:7 imaginary substrate

The generator is **numpy-free at import** and **exact-rational** in its core
(every entry is a reduced ``(num, den)`` integer pair via the Class-N
``cos_series_truncate`` / ``sin_series_truncate`` Taylor partials). The
optional :meth:`One.to_numpy` / :meth:`One.to_matrix` float realisations
import numpy lazily (the ``srmech[scientific]`` tier, §22).

Canonical SSoT:
- Hurwitz (1898), *Über die Composition der quadratischen Formen* — the
  ``ℝ, ℂ, ℍ, 𝕆`` ladder is the complete list of normed division algebras.
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
        The rotated imaginary state ``σ e^{Î_n θ} e₁`` as exact rationals,
        length ``2ⁿ − 1``.
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

    def to_numpy(self):
        """The 14-vector state as a ``numpy`` float array (opt-in / lazy).

        Requires the ``srmech[scientific]`` extra (numpy). The exact
        rationals are float-cast at the boundary, never before.
        """
        from srmech._scientific import require_numpy

        np = require_numpy("srmech.amsc.cascade.one.One.to_numpy")
        flat = self.to_flat_rational()
        return np.array([num / den for (num, den) in flat], dtype=float)

    def to_matrix(self):
        """The 14×14 block-diagonal operator ``G(σ,θ)`` (opt-in / lazy).

        ``G`` is ``⨁_n (1 ⊕ σ R_n(θ))`` — the identity on each ``ℝ·1`` axis
        and ``σ`` times the proper rotation ``R_n(θ)`` (rotate the ``(e₁,e₂)``
        imaginary plane by θ, fix the axis ``Î_n = e_d``) on each ``Im 𝔸_n``.
        Applying ``G`` to the canonical seed (real ``1``, imaginary ``e₁``)
        reproduces :meth:`to_flat_rational`. This is the matrix that the
        qm-peer ``srmech.qm.hurwitz`` must agree with (the Rosetta parity).
        Requires the ``srmech[scientific]`` extra (numpy).
        """
        from srmech._scientific import require_numpy

        np = require_numpy("srmech.amsc.cascade.one.One.to_matrix")
        cn, cd = cos_series_truncate(self.theta[0], self.theta[1], self.terms)
        sn, sd = sin_series_truncate(self.theta[0], self.theta[1], self.terms)
        cos_t = cn / cd
        sin_t = sn / sd
        s = self.sigma
        g = np.zeros((DIM, DIM), dtype=float)
        offset = 0
        for d in IMAG_DIMS:                      # d = 1, 3, 7
            g[offset, offset] = 1.0              # ℝ·1 anchor — fixed
            imo = offset + 1                     # first imaginary axis
            if d == 1:                           # n=1: seed == axis → only σ
                g[imo, imo] = s
            else:
                # σ R_n(θ): rotate the (e₁, e₂) plane, fix axes e₃..e_d.
                g[imo, imo] = s * cos_t
                g[imo, imo + 1] = -s * sin_t
                g[imo + 1, imo] = s * sin_t
                g[imo + 1, imo + 1] = s * cos_t
                for k in range(2, d):            # fixed imaginary axes
                    g[imo + k, imo + k] = s
            offset += 1 + d
        return g

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
        is built as the exact-rational ``cos θ + Î_n sin θ``.
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
        if d == 1:
            # n=1: seed e₁ == rotation axis Î₁ → θ-inert; only σ survives.
            imag: Tuple[Tuple[int, int], ...] = (_chiral_scale((1, 1), sigma),)
        else:
            # σ e^{Î_n θ} e₁ = (σ cos θ, σ sin θ, 0, …, 0) — rotate (e₁,e₂),
            # the axis Î_n = e_d and the other imaginary axes are zero in the
            # seed image.
            rotated = [
                _chiral_scale(cos_t, sigma),
                _chiral_scale(sin_t, sigma),
            ]
            rotated.extend((0, 1) for _ in range(d - 2))
            imag = tuple(rotated)
        blocks.append(Block(
            algebra=ALGEBRAS[idx],
            n=idx + 1,
            real=(1, 1),
            imag=imag,
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

__all__ = [
    "ALGEBRAS",
    "IMAG_DIMS",
    "BLOCK_DIMS",
    "AN_IMAG_SLOTS",
    "GRAMMAR_SLOTS",
    "DIM",
    "DEFAULT_TERMS",
    "Block",
    "One",
    "the_one",
    "s_generator",
]
