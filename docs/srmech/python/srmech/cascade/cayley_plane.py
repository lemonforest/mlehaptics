"""The octonion Cayley plane 𝕆P² — carrier-native (rc399, `#T1064` Tier 2).

§3.41.7 shipped the octonion **Moufang loop** (Tier 1, rc398) and REFUTED the
Moufang-*polygon* connection, keeping only the **n = 3** same-cause FORM echo:
the Moufang **plane** 𝕆P². This module builds that plane as a carrier-native
coherence object, one rung ABOVE the quaternionic ``ℍP¹ ≅ S⁴`` base that
:func:`srmech.cascade.cayley_dickson.octonion_frame_read` stops at — NOT as a
bridge that resolves the §3.41.6 frame-read ceiling. It is FORM, not identity
(`[[user_stance_cascade_matching_substrate_blind_form_not_identity]]`).

**The carrier.** A point of 𝕆P² is a rank-1, trace-1 idempotent of the
**Albert algebra** ``J₃(𝕆)`` — the 3×3 octonionic-Hermitian matrices under the
Jordan product ``A∘B = (AB+BA)/2`` (``dim = 3·1 + 3·8 = 27``). We do NOT register
a full Albert-algebra carrier; every op here is a **composition over the
octonion product srmech already ships** (``cd_mult`` / ``cd_conjugate`` /
``cd_norm_sq`` — each C-dispatched), so ``composition_of_c``, NO new C symbol,
``SRMECH_ABI_VERSION`` unchanged.

**J₃(𝕆) element ↔ flat 27-vector.** In the Freudenthal / Springer–Veldkamp
layout::

        [ d₁   x₃   x₂* ]
    X = [ x₃*  d₂   x₁  ]        dᵢ ∈ ℝ,  xᵢ ∈ 𝕆,  * = octonion conjugate
        [ x₂   x₁*  d₃  ]

a J₃(𝕆) element is carried as the flat exact-ℚ vector
``[d₁, d₂, d₃] + x₁(8) + x₂(8) + x₃(8)`` (length 27). Hermitian by construction.

**Honesty (load-bearing).** ``cd_mult`` on 𝕆 is NON-associative, so the rank-1
idempotent identity ``P∘P = P`` holds only when the Veronese vector's entries
**pairwise associate** (the octonionic projective-coordinate condition — e.g.
two of three entries real, or all three inside a common ℍ subalgebra). Beyond
that, ``cayley_plane_point`` returns a NONZERO ``idempotent_defect`` — the
instrument can return otherwise; the boundary is the plane's non-Desarguesian
nature itself. Likewise the "line through two points" cross-product construction
closes only on the Desarguesian (associating-coordinate) subplane; the
always-well-defined :func:`cayley_plane_incidence` (the Jordan **trace form**
``Tr(A∘B)``, linear, so associativity-blind) is the incidence primitive.

Canonical SSoT (cited technically, no lineage claims per
`[[feedback_no_lineage_claims_in_notebook]]`):
- T.A. Springer & F.D. Veldkamp (2000), *Octonions, Jordan Algebras and
  Exceptional Groups*, Springer Monographs in Mathematics — the Albert algebra
  ``J₃(𝕆)``, rank-1 idempotents and 𝕆P² (already cited in-tree in
  ``cayley_dickson.py``).
- J.C. Baez (2002), *The Octonions*, Bull. AMS **39** 145–205,
  arXiv:math/0105155, §3 (the exceptional Jordan algebra) + §4.2 (the Cayley
  plane 𝕆P², the octonionic Hopf fibration ``S⁷ ↪ S¹⁵ ↠ S⁸``, ``𝕆P¹ ≅ S⁸``).
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence, Tuple

from srmech.math.q import Q

from .cayley_dickson import (
    _as_elem,
    _coerce_frac,
    cd_conjugate,
    cd_mult,
    cd_norm_sq,
)

__all__ = [
    "jordan_product",
    "cayley_plane_point",
    "cayley_plane_incidence",
    "octonion_hopf_base",
]

_Z = Q(0, 1)
_HALF = Q(1, 2)
_TWO = Q(2, 1)
_ZERO8: Tuple[Q, ...] = tuple(_Z for _ in range(8))


# ── octonion-scalar helpers (exact ℚ; composed over the shipped C-backed ops) ──
def _oadd(a: Sequence[Q], b: Sequence[Q]) -> Tuple[Q, ...]:
    return tuple(p + q for p, q in zip(a, b))


def _osub(a: Sequence[Q], b: Sequence[Q]) -> Tuple[Q, ...]:
    return tuple(p - q for p, q in zip(a, b))


def _oscal(s: Q, a: Sequence[Q]) -> Tuple[Q, ...]:
    return tuple(s * p for p in a)


def _oct(seq: Sequence[Any]) -> Tuple[Q, ...]:
    """Coerce a length-8 sequence to an exact-ℚ octonion (Class-M carrier)."""
    el = _as_elem(seq)
    if len(el) != 8:
        raise ValueError(f"expected a length-8 octonion; got length {len(el)}")
    return el


# ── J₃(𝕆) ↔ flat-27 marshalling + the full octonionic 3×3 matmul ──
def _j3_unpack(v: Sequence[Any]) -> "Tuple[Tuple[Q, Q, Q], Tuple[Tuple[Q, ...], ...]]":
    """flat-27 → ((d₁,d₂,d₃), (x₁,x₂,x₃)); dᵢ real ``Q``, xᵢ octonion 8-tuples."""
    el = tuple(_coerce_frac(c) for c in v)
    if len(el) != 27:
        raise ValueError(
            f"a J₃(𝕆) element is a flat 27-vector "
            f"[d₁,d₂,d₃] + x₁(8) + x₂(8) + x₃(8); got length {len(el)}")
    diag = (el[0], el[1], el[2])
    off = (el[3:11], el[11:19], el[19:27])
    return diag, off


def _j3_pack(diag: Sequence[Q], off: Sequence[Sequence[Q]]) -> Tuple[Q, ...]:
    """((d₁,d₂,d₃), (x₁,x₂,x₃)) → flat-27 exact-ℚ vector."""
    return tuple(diag) + tuple(off[0]) + tuple(off[1]) + tuple(off[2])


def _j3_matrix(diag: Sequence[Q], off: Sequence[Sequence[Q]]) -> List[List[Tuple[Q, ...]]]:
    """Expand to the full 3×3 octonion matrix (Freudenthal layout above)."""
    d1, d2, d3 = diag
    x1, x2, x3 = off
    D1 = (d1,) + _ZERO8[1:]
    D2 = (d2,) + _ZERO8[1:]
    D3 = (d3,) + _ZERO8[1:]
    return [
        [D1, x3, cd_conjugate(x2)],
        [cd_conjugate(x3), D2, x1],
        [x2, cd_conjugate(x1), D3],
    ]


def _mat_mul(A: List[List[Tuple[Q, ...]]],
             B: List[List[Tuple[Q, ...]]]) -> List[List[Tuple[Q, ...]]]:
    """Full 3×3 octonionic matrix product — NO reassociation (𝕆 is
    non-associative; every entry product is the shipped ``cd_mult``)."""
    C = [[_ZERO8, _ZERO8, _ZERO8] for _ in range(3)]
    for i in range(3):
        for j in range(3):
            acc = _ZERO8
            for k in range(3):
                acc = _oadd(acc, cd_mult(A[i][k], B[k][j]))
            C[i][j] = acc
    return C


def _mat_to_j3(M: List[List[Tuple[Q, ...]]]) -> Tuple[Q, ...]:
    """Read a Hermitian 3×3 octonion matrix back into the compact flat-27 form
    (the diagonal real parts + the upper off-diagonal x₁,x₂,x₃)."""
    diag = (M[0][0][0], M[1][1][0], M[2][2][0])
    off = (M[1][2], M[2][0], M[0][1])
    return _j3_pack(diag, off)


def jordan_product(a: Sequence[Any], b: Sequence[Any]) -> Tuple[Q, ...]:
    """The JORDAN PRODUCT ``A∘B = (AB + BA)/2`` of two Albert-algebra elements
    ``A, B ∈ J₃(𝕆)`` — the commutative (non-associative) product that makes the
    27-dim 3×3 octonionic-Hermitian matrices a Jordan algebra (rc399, `#T1064`).

    Both operands are flat 27-vectors ``[d₁,d₂,d₃] + x₁(8) + x₂(8) + x₃(8)`` in
    the Freudenthal layout (see the module docstring). The Jordan product of two
    Hermitian matrices is Hermitian regardless of octonion associativity
    (``(A∘B)* = A∘B``), so the result re-packs into the same compact 27-form.

    Args:
        a, b: J₃(𝕆) elements, each a length-27 exact-rational sequence (every
            scalar :func:`cd_mult` accepts — ``int`` / ``Q`` / ``Fraction`` /
            ``float`` → its EXACT ratio / ``(num, den)``).

    Returns:
        The flat-27 :class:`~srmech.math.q.Q` vector of ``A∘B``.

    Note:
        Exact end to end — no float, no epsilon, no ``abs()``. NO new C symbol
        — ``composition_of_c`` over the c_dispatched ``srmech_cd_mult`` /
        ``srmech_cd_qconjugate``. Class M (bilinear octonion bind) ∘ K (the
        ``/2`` and the sign-free Hermitian symmetrisation).

    Canonical SSoT: Springer & Veldkamp (2000), *Octonions, Jordan Algebras and
    Exceptional Groups*, ch. 5 — the Jordan product on ``J₃(𝕆)``; Baez (2002),
    arXiv:math/0105155, §3.
    """
    da, oa = _j3_unpack(a)
    db, ob = _j3_unpack(b)
    A = _j3_matrix(da, oa)
    B = _j3_matrix(db, ob)
    AB = _mat_mul(A, B)
    BA = _mat_mul(B, A)
    S = [[_oscal(_HALF, _oadd(AB[i][j], BA[i][j])) for j in range(3)]
         for i in range(3)]
    return _mat_to_j3(S)


def cayley_plane_point(x1: Sequence[Any],
                       x2: Sequence[Any],
                       x3: Sequence[Any]) -> Dict[str, Any]:
    """A POINT of the Cayley plane 𝕆P² — the rank-1, trace-1 idempotent
    ``P = v v* / ⟨v,v⟩`` built from a Veronese vector ``v = (x₁,x₂,x₃) ∈ 𝕆³``
    (rc399, `#T1064`).

    ``P`` is the Hermitian rank-1 projector onto the octonionic line ``[v]``: its
    diagonal is ``(|x₁|², |x₂|², |x₃|²)/⟨v,v⟩`` (so ``tr P = 1`` EXACTLY) and its
    off-diagonal is the outer product ``xᵢ x̄ⱼ / ⟨v,v⟩``. A genuine point of 𝕆P²
    is a rank-1 idempotent (``P∘P = P``).

    ⚠️ **The associativity boundary (honest).** Because 𝕆 is non-associative,
    ``P∘P = P`` holds **iff v's entries pairwise associate** — e.g. two of three
    entries real, or all three in a common ℍ subalgebra. This op therefore
    returns ``idempotent_defect`` = the exact ⟨P∘P − P, ·⟩ total magnitude²;
    ``is_point`` is ``True`` iff it is 0. MEASURED: ``(1,e₁,e₂)`` (quaternionic)
    → 0; ``(e₁,e₂,e₄)`` (three non-associating imaginary units) → ``8/27`` ≠ 0.
    The nonzero case is the plane's **non-Desarguesian nature**, not a bug — the
    instrument can return otherwise (`[[feedback_an_instrument_that_cannot_return
    _otherwise_is_not_a_measurement]]`).

    Args:
        x1, x2, x3: the three octonion coordinates, each a length-8
            exact-rational sequence. ``v`` must be nonzero (``⟨v,v⟩ > 0``).

    Returns:
        A ``dict`` with:

        * ``point`` — the flat-27 J₃(𝕆) element ``P``;
        * ``trace`` (``Q``) — ``tr P``, exactly ``1`` for any nonzero ``v``;
        * ``inner`` (``Q``) — ``⟨v,v⟩ = Σ|xᵢ|²``, the normalising scalar;
        * ``idempotent_defect`` (``Q``) — ``⟨P∘P − P, ·⟩`` total magnitude²;
          ``0`` ⟺ genuine 𝕆P² point;
        * ``is_point`` (bool) — ``idempotent_defect == 0``.

    Raises:
        ValueError: a coordinate is not length-8, or ``v == 0``.

    Note:
        Exact end to end — no float, no ``abs()`` (``idempotent_defect`` and
        ``inner`` are Class-K ⟨v,v⟩ magnitude²). ``composition_of_c`` over
        ``cd_mult`` / ``cd_conjugate`` / ``cd_norm_sq``; NO new C symbol. Class
        M (outer bind) ∘ C (conjugation) ∘ K (magnitude²).

    Canonical SSoT: Springer & Veldkamp (2000), ch. 5 (rank-1 idempotents of
    ``J₃(𝕆)`` = points of 𝕆P²); Baez (2002), arXiv:math/0105155, §4.2.
    """
    v1, v2, v3 = _oct(x1), _oct(x2), _oct(x3)
    n1, n2, n3 = cd_norm_sq(v1), cd_norm_sq(v2), cd_norm_sq(v3)
    inner = n1 + n2 + n3
    if inner == 0:
        raise ValueError("cayley_plane_point: the Veronese vector v is zero")
    inv = Q(1, 1) / inner
    diag = (n1 * inv, n2 * inv, n3 * inv)
    x_1 = _oscal(inv, cd_mult(v2, cd_conjugate(v3)))   # M[1][2]
    x_2 = _oscal(inv, cd_mult(v3, cd_conjugate(v1)))   # M[2][0]
    x_3 = _oscal(inv, cd_mult(v1, cd_conjugate(v2)))   # M[0][1]
    P = _j3_pack(diag, (x_1, x_2, x_3))
    # idempotent defect  ⟨P∘P − P, ·⟩  (exact ℚ; the associativity boundary)
    PP = jordan_product(P, P)
    defect = sum(((p - q) * (p - q) for p, q in zip(PP, P)), _Z)
    trace = diag[0] + diag[1] + diag[2]
    return {
        "point": P,
        "trace": trace,
        "inner": inner,
        "idempotent_defect": defect,
        "is_point": defect == 0,
    }


def cayley_plane_incidence(a: Sequence[Any], b: Sequence[Any]) -> Q:
    """The INCIDENCE pairing of two Cayley-plane elements — the Jordan **trace
    form** ``Tr(A∘B)`` on ``J₃(𝕆)`` (rc399, `#T1064`).

    The Cayley plane is **self-dual** (a polarity swaps points and lines), so the
    single symmetric bilinear form ``⟨A,B⟩ = Tr(A∘B)`` reads both point–point
    polarity and point–line incidence: a point ``P`` and a line ``L`` (each a
    rank-1 idempotent) are **incident iff ``Tr(P∘L) = 0``** — the two idempotents
    are Jordan-orthogonal. Because the trace is LINEAR, this form is
    associativity-blind and therefore **always exact and well-defined**, unlike
    the cross-product "line through two points" construction, which closes only
    on the Desarguesian (associating-coordinate) subplane.

    MEASURED on the coordinate triangle ``E₁=[1,0,0], E₂=[0,1,0], E₃=[0,0,1]``
    and the unit point ``U=[1,1,1]``: ``Tr(Eᵢ∘Eⱼ) = δᵢⱼ`` (a projective
    triangle — distinct, pairwise Jordan-orthogonal) and ``Tr(Eᵢ∘U) = 1/3``
    (``U`` lies off all three coordinate lines). ``Tr(P∘P) = 1`` for any point
    (idempotent).

    Args:
        a, b: J₃(𝕆) elements (points and/or lines), each a length-27
            exact-rational sequence.

    Returns:
        The exact :class:`~srmech.math.q.Q` scalar ``Tr(A∘B)`` — ``0`` ⟺
        incident / Jordan-orthogonal.

    Note:
        Exact end to end — no float, no ``abs()``. ``composition_of_c`` over
        :func:`jordan_product` (hence ``cd_mult`` / ``cd_conjugate``); NO new C
        symbol. Class M ∘ K.

    Canonical SSoT: Springer & Veldkamp (2000), ch. 5 (the trace form on
    ``J₃(𝕆)`` and the polarity of 𝕆P²); Baez (2002), arXiv:math/0105155, §4.2.
    """
    prod = jordan_product(a, b)
    return prod[0] + prod[1] + prod[2]


def octonion_hopf_base(x: Sequence[Any]) -> Dict[str, Any]:
    """The octonionic Hopf base ``𝕆P¹ ≅ S⁸`` — the direct carrier-native rung-UP
    from :func:`~srmech.cascade.cayley_dickson.octonion_frame_read`'s
    quaternionic ``ℍP¹ ≅ S⁴`` (rc399, `#T1064`).

    ``octonion_frame_read`` reads ONE octonion ``(q₀,q₁) ∈ ℍ²`` onto the
    quaternionic Hopf base ``S³ ↪ S⁷ ↠ S⁴``. One rung above lives the
    **octonionic** Hopf fibration ``S⁷ ↪ S¹⁵ ↠ S⁸`` with base ``𝕆P¹ ≅ S⁸`` —
    the genuine "missing object between the frame-committed ℍ base and the full
    plane 𝕆P²." This op reads ``x = (a,b) ∈ 𝕆²`` (a 16-vector) onto it::

        base_O = 2·a·conj(b)          (8 comps, the 𝕆 off-diagonal)
        base_R = |a|² − |b|²           (1 scalar, the ℝ diagonal; Class-K, no abs())

    **Lands on S⁸ — exactly.** ``|base_O|² + base_R² == norm_sq²`` where
    ``norm_sq = |a|² + |b|² = |x|²`` (a unit ``x ∈ S¹⁵`` maps to a unit
    ``S⁸`` point). MEASURED bit-exact.

    **Rung-down reduction.** Restricting ``x`` to ``ℍ²`` (``a,b ∈ ℍ``) collapses
    ``base_O`` into ℍ — its seam half ``(e₄..e₇)`` vanishes — recovering the
    quaternionic-shaped base of ``octonion_frame_read``.

    ⚠️ **The §3.41 ceiling — the octonionic base is NOT frame-free under the
    ``S⁷`` fiber** (unlike the quaternionic one). Under a unit-octonion
    right-multiply ``(a,b) → (a·λ, b·λ)``, the base is invariant ONLY when ``λ``
    lies in a subalgebra that associates with ``a,b``; a seam-crossing ``λ``
    MOVES it (``2·(aλ)·conj(bλ) ≠ 2·a·conj(b)`` — the reassociation
    ``(aλ)(λ̄b̄) = a(λλ̄)b̄`` fails at 𝕆). This is exactly §3.41.6's "no
    frame-free 𝕆 invariant" made geometric; the op reports both witnesses via
    ``fiber_invariant_note``. FORM, not identity.

    Args:
        x: a length-16 vector ``(a,b) ∈ 𝕆²`` (``a = x[:8]``, ``b = x[8:]``);
            every exact-rational scalar :func:`cd_mult` accepts.

    Returns:
        A ``dict`` with:

        * ``a`` / ``b`` — the two octonion halves (8-tuples of ``Q``);
        * ``base_O`` (8 ``Q``) — the ``𝕆`` off-diagonal ``2·a·conj(b)``;
        * ``base_R`` (``Q``) — the ``ℝ`` diagonal ``|a|² − |b|²``;
        * ``norm_sq`` (``Q``) — ``|a|² + |b|² = |x|²``; the base lies on the
          radius-``norm_sq`` eight-sphere ``|base_O|² + base_R² == norm_sq²``;
        * ``on_s8`` (bool) — the exact ``S⁸`` norm identity holds (always
          ``True``);
        * ``reduces_to_h`` (bool) — ``base_O``'s seam half is zero (``a,b ∈ ℍ``);
        * ``base_norm_sq`` (``Q``) — ``|base_O|²`` (the fiber note's scale).

    Raises:
        ValueError: ``x`` is not a 16-vector.

    Note:
        Exact end to end — no float, no ``abs()`` (``base_R`` is the Class-K
        pin-slot difference; the conjugation is Class C). ``composition_of_c``
        over ``cd_mult`` / ``cd_conjugate`` / ``cd_norm_sq``; NO new C symbol.
        Class M ∘ C ∘ K.

    Canonical SSoT: Baez (2002), *The Octonions*, arXiv:math/0105155, §4.1–§4.2
    (the octonionic Hopf fibration ``S⁷ ↪ S¹⁵ ↠ S⁸`` and ``𝕆P¹ ≅ S⁸``);
    Springer & Veldkamp (2000), ch. 5.
    """
    el = _as_elem(x)
    if len(el) != 16:
        raise ValueError(
            f"octonion_hopf_base: x must be a 16-vector (a,b) ∈ 𝕆²; got "
            f"length {len(el)}")
    a = el[:8]
    b = el[8:]
    base_O = _oscal(_TWO, cd_mult(a, cd_conjugate(b)))
    na = cd_norm_sq(a)
    nb = cd_norm_sq(b)
    base_R = na - nb                       # Class-K pin-slot difference; no abs()
    norm_sq = na + nb
    base_norm_sq = cd_norm_sq(base_O)
    on_s8 = (base_norm_sq + base_R * base_R) == (norm_sq * norm_sq)
    reduces_to_h = all(base_O[i] == 0 for i in range(4, 8))
    return {
        "a": a,
        "b": b,
        "base_O": base_O,
        "base_R": base_R,
        "norm_sq": norm_sq,
        "base_norm_sq": base_norm_sq,
        "on_s8": on_s8,
        "reduces_to_h": reduces_to_h,
    }
