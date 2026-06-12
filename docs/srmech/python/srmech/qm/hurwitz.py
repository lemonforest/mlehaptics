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
    table = octonion_mult_table()  # rc122: nested list — index [a][b][axis], not [a,b,axis]
    out: List[Tuple[int, int, int]] = []
    for a in range(1, dim):
        for b in range(a + 1, dim):
            if a == axis or b == axis:
                continue
            sign = int(table[a][b][axis])
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


__all__ = [
    "hurwitz_planes",
]
