"""Hurwitz generator ``S(σ,θ)`` — the octonion-native matrix realisation.

The ``srmech.qm`` Rosetta peer of the numpy-free
:func:`srmech.amsc.cascade.the_one` (#887). It builds the SAME ``14×14``
block-diagonal operator

.. math::

    G(\\sigma,\\theta) \\;=\\; \\bigoplus_{n=1}^{3}\\big(\\,1 \\;\\oplus\\;
        \\sigma\\, R_n(\\theta)\\,\\big),\\qquad \\dim = 2+4+8 = 14,

but **derives** the Fano planes of each rotation ``R_n(θ)`` straight from
:func:`srmech.qm.octonion.octonion_mult_table` — not from a hardcoded list —
so the agreement with the cascade form is a genuine cross-derivation (the
two substrate-native languages, continuous-Hopf matrix vs discrete-cyclic
cascade, computing the same object two ways), not a restatement.

``R_n(θ)`` is the octonion-native rotation on ``Im 𝔸_n``: it fixes the axis
``Î_n = e_{2ⁿ-1}`` (the last imaginary unit) and turns every **Fano-triple
plane through ``Î_n``** by ``θ`` at once —

============  ====================  ====================================
``n``         planes turned by θ    Im-rotation eigenvalues
============  ====================  ====================================
1  (ℂ)        0  →  only ``σ``       ``{σ}``
2  (ℍ)        1                      ``{1, e^{±iθ}}``
3  (𝕆)        3 (Fano triples)       ``{1, e^{±iθ}, e^{±iθ}, e^{±iθ}}``
============  ====================  ====================================

A–N placement: the planes are read from the **Class A** attested octonion
convention (``octonion_mult_table``); ``cos θ`` / ``sin θ`` are the **Class
N** exact-rational Taylor partials; ``σ`` is **Class K** sign ∘ **Class C**
apply (never ``abs()``); the ``⨁`` over ``n`` is **Class I**. No new
primitive class.

Scientific tier (§22): ``srmech.qm`` requires numpy; the matrix entries are
``{0, ±1, ±cos θ, ±sin θ}`` built from the exact-rational cascade ``cos``/
``sin`` (float-cast at the boundary), so they are bit-exactly the entries of
:meth:`srmech.amsc.cascade.One.to_matrix`.

Canonical SSoT:
- Baez, J.C. (2002) *The Octonions*, Bull. Amer. Math. Soc. 39, 145-205
  (arXiv:math/0105155) — the Fano-plane multiplication convention.
- Hurwitz (1898) — the ``ℝ, ℂ, ℍ, 𝕆`` normed-division-algebra ladder.
"""

from __future__ import annotations

from typing import List, Tuple

import numpy as np

from srmech.amsc.rational import cos_series_truncate, sin_series_truncate
from srmech.qm.octonion import octonion_mult_table

#: The substrate dimension (2 + 4 + 8).
_DIM = 14

#: Imaginary dimensions of ℂ / ℍ / 𝕆; the rotation axis of block ``n`` is the
#: LAST imaginary unit ``e_{2ⁿ-1}`` (= ``e_{IMAG_DIMS[n-1]}``), the algebra
#: dimension is ``2ⁿ`` (= ``IMAG_DIMS[n-1] + 1``).
_IMAG_DIMS: Tuple[int, int, int] = (1, 3, 7)

#: Default Taylor depth for the exact-rational ``cos``/``sin``.
_DEFAULT_TERMS = 24


def _fano_planes(axis: int, dim: int) -> List[Tuple[int, int, int]]:
    """Oriented Fano planes ``(a, b, sign)`` through ``e_axis`` within
    ``e_0..e_{dim-1}``, derived from the attested octonion structure
    constants: ``e_a · e_b = sign · e_axis`` (``a < b``, both imaginary,
    both ``< dim``, neither the axis). Internal: the public
    :func:`hurwitz_planes` wraps the three algebra axes.
    """
    table = octonion_mult_table().astype(int)
    out: List[Tuple[int, int, int]] = []
    for a in range(1, dim):
        for b in range(a + 1, dim):
            if a == axis or b == axis:
                continue
            sign = int(table[a, b, axis])
            if sign != 0:
                out.append((a, b, sign))
    return out


def hurwitz_planes() -> Tuple[Tuple[Tuple[int, int, int], ...], ...]:
    """The oriented Fano planes per algebra (ℂ, ℍ, 𝕆), DERIVED from the
    octonion multiplication table.

    Returns a 3-tuple (one entry per ladder rung); each entry is the tuple
    of ``(a, b, sign)`` planes that block's rotation turns by θ — ``0 / 1 /
    3`` planes for ℂ / ℍ / 𝕆. These match
    :data:`srmech.amsc.cascade.one.FANO_PLANES` bit-for-bit (the cascade form
    hardcodes them; this reads them from the attested
    :func:`srmech.qm.octonion.octonion_mult_table`).

    Class A (content-addressing): the planes ARE the octonion convention.

    Returns:
        ``((), ((1,2,1),), ((1,6,-1),(2,5,1),(3,4,1)))`` for the fixed
        Cayley-Dickson-from-ℍ convention.
    """
    return tuple(
        tuple(_fano_planes(axis=d, dim=d + 1)) for d in _IMAG_DIMS
    )


def hurwitz_matrix(sigma: int,
                   theta_num: int,
                   theta_den: int = 1,
                   terms: int = _DEFAULT_TERMS) -> np.ndarray:
    """The ``14×14`` octonion-native operator ``G(σ,θ)`` of "the One" (#887).

    ``G = ⨁_n (1 ⊕ σ R_n(θ))``: the identity on each ``ℝ·1`` anchor and ``σ``
    times the octonion-native rotation ``R_n(θ)`` on each ``Im 𝔸_n`` — turn
    every Fano plane through ``Î_n`` by θ (planes derived from
    :func:`hurwitz_planes`), fixing ``Î_n``. For 𝕆 this is a genuine
    **3-plane** rotation (eigenvalues ``{1, e^{±iθ}×3}`` on the imaginary
    part). Bit-exactly equal to :meth:`srmech.amsc.cascade.One.to_matrix`
    (same exact-rational ``cos``/``sin``, same Fano planes).

    Class A (planes) ∘ Class N (rational ``cos``/``sin``) ∘ Class K·C (σ).

    Args:
        sigma: Chirality ``σ ∈ {+1, -1}``.
        theta_num, theta_den: Angle ``θ = theta_num / theta_den`` (radians);
            ``theta_den > 0``.
        terms: Class-N Taylor depth for ``cos``/``sin`` (default 24).

    Returns:
        A ``(14, 14)`` ``float64`` orthogonal-up-to-σ matrix.

    Raises:
        ValueError: if ``sigma ∉ {+1,-1}`` or ``theta_den <= 0``.
    """
    if sigma != 1 and sigma != -1:
        raise ValueError(f"sigma (chirality) must be +1 or -1; got {sigma!r}")
    if theta_den <= 0:
        raise ValueError(f"theta_den must be positive; got {theta_den}")

    cn, cd = cos_series_truncate(theta_num, theta_den, terms)
    sn, sd = sin_series_truncate(theta_num, theta_den, terms)
    cos_t = cn / cd
    sin_t = sn / sd
    s = sigma
    planes_per = hurwitz_planes()

    g = np.zeros((_DIM, _DIM), dtype=float)
    offset = 0
    for idx, d in enumerate(_IMAG_DIMS):     # d = 1, 3, 7
        g[offset, offset] = 1.0              # ℝ·1 anchor — fixed
        imo = offset + 1                     # imaginary axes e₁..e_d
        for i in range(d):                   # default σ·identity on Im
            g[imo + i, imo + i] = s
        for (a, b, sgn) in planes_per[idx]:  # turn each Fano plane by θ
            ia, ib = imo + (a - 1), imo + (b - 1)
            g[ia, ia] = s * cos_t
            g[ib, ib] = s * cos_t
            g[ib, ia] = s * sgn * sin_t      # e_a → cosθ e_a + sgn sinθ e_b
            g[ia, ib] = -s * sgn * sin_t     # e_b → -sgn sinθ e_a + cosθ e_b
        offset += 1 + d
    return g


__all__ = [
    "hurwitz_matrix",
    "hurwitz_planes",
]
