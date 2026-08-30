"""``srmech.math.weight_lattice`` — the EXACT A2 weight-label stratum
(rc460): labels, weight systems, and tensor-product fusion, all as SIGNED
INTEGER COUNTS indexed by a LATTICE.

WHY THIS IS A PEER OF ``srmech.math.groups`` AND NOT A PART OF IT
=================================================================
:mod:`srmech.math.groups` is 3000+ lines and its instrument is a **count
off a Cayley table** — indexed by group ELEMENTS.  This module's
instrument is a **signed count off a lattice** — indexed by WEIGHTS.  Same
class of nativity, different index; two modules, not one.

THE CORRECTION THIS MODULE IS
=============================
Lie-algebra fusion is routinely phrased as *"a convolution of orbital
measures against Haar — an INTEGRAL"*, and that phrasing is the
**spacetime shadow** of a bottom-up-closed-form object.  Racah–Speiser
computes the SAME coefficients as a **signed integer count**: take the
weight system of one factor, translate by ``a + rho``, signed-fold into
the dominant chamber under the 6-element Weyl group, and count with
signs.  There is no measure, no integral, and no float anywhere in the
derivation — it is the same instrument CLASS as
:func:`srmech.math.groups.character_table`'s step-4 structure-constant
count ("by integer counting off the table"), with a LATTICE where that op
has a table.

THE A-N READING, AND THE NON-CLAIMS THAT GO WITH IT
===================================================
* :func:`dominant_weight` — **Class A** primary (it MINTS the stored
  content address of a label-plus-gauge object), with a Class-I stage
  (the Z/3 N-ality grading) and a Class-N stage (the guarded ``/2`` in
  the dimension formula).
* :func:`weight_multiplicities` — **Class E** primary (catalog
  enumeration of the weight system), with Class C (Weyl reflection to
  the dominant representative — orientation, which-way) and Class N (the
  guarded Freudenthal division).  ⚠️ **Explicit non-claim: this op is
  NOT Class K.**  Freudenthal's recursion is sign-free; no phase
  boundary is crossed, and claiming K here would assert an instrument
  the op never runs.
* :func:`tensor_product_multiplicities` — **Class K** primary: the +-1
  ledger at the reflection walls IS the instrument, and it is exactly
  where a sign count becomes a fusion coefficient.  Internal stages:
  Class C (reflection direction), Class I (translation by rho; the mod-3
  grading), Class E (orbit enumeration), Class N (the guards).
  ⚠️ **Explicit non-claim: this op is NOT Class L.**  Its finite-group
  sibling :func:`srmech.math.groups.fusion_multiplicities` is Class L
  *because* it contracts against the class-algebra eigenbasis.  This op
  builds no eigenbasis and projects onto nothing.

THE GAUGE THE GENERATOR DOES NOT FIX (why the payload carries one)
==================================================================
The Cartan matrix ``((2, -1), (-1, 2))`` is INVARIANT under the diagram
flip, so it cannot tell ``3`` from ``3-bar``: every invariant derived
from it alone (dimension, multiplicity multiset, self-fusion shape)
coincides for a label and its conjugate.  Only the label ORDER separates
them, and that order is a Z/2 **Class-C chirality** choice the generator
does not make.  Second, ``det(Cartan) = 3 = |P/Q|`` fixes the INDEX of
the root lattice in the weight lattice but not WHICH of the two the
global form uses (SU(3) vs PSU(3)).  Third, the bilinear form is
integral only after clearing 3, so the metric normalisation is a stored
convention.  Accordingly the stored SSoT is **label + chirality bit +
global-form choice + metric scale + procedure hash**, and
:func:`dominant_weight`'s ``label_sha256`` binds all five — a label-only
address would collide across two rcs deriving under different
conventions.

CARRIER
=======
Plain ``int`` and tuples of ``int`` for labels, multiplicities and
weight coordinates; :class:`srmech.math.qmat.QMat` for the six Weyl
reflections (all integer 2x2, closed under product, so ``QMat`` holds
them exactly).  **No new carrier TYPE** — nothing here widens a
discriminator set, so there is no C obligation and no ABI move.

Exact arithmetic ONLY: no float, no ``abs``.  The single sign-handling
site is the Weyl ledger in :func:`tensor_product_multiplicities`, which
is an explicit +-1 determinant read (Class K pin-slot at the reflection
wall, Class C re-application on the folded label) and never an ALU
magnitude call.  Every division routes through :func:`_exact_div` — a
remainder RAISES, because a guard that fires is evidence.  All content
addresses route through :func:`srmech.amsc.format.sha256_bytes`.

C-parity (ADR-0009, recorded): this module has no C peer; the
weight-lattice stratum ships Python-first under the noted-disparity
ruling, the same sentence the representation stratum already carries.

⚠️ ATTESTATION GAP, RECORDED AND STILL OPEN (rc461 part 3). This module
names Kac-Walton / Kac-Peterson / Verlinde in prose that ships into
``describe()``, the MCP tool list and the compiled C registry, with no
literature anchor — while its sibling ``so8`` build in the SAME rc
attests every op to a query-verified arXiv ID. An anchor was located and
verified BY QUERY (Fuchs, J. (1994) *Fusion rules in conformal field
theory*, Fortschr. Phys. **42**, 1-48, arXiv:hep-th/9306162 — open
access, title and author confirmed against the returned record) and then
NOT shipped, because adding it moves the citation-manifest coverage
surface and ``tests/test_citation_manifest_rc428.py`` cannot be measured
from a session worktree (the corpus scopes to zero there, a known false
red). Shipping a manifest edit that could not be validated would be
worse than the gap. The mitigating fact is unchanged and is the reason
this is a gap rather than a defect: NOTHING here is recalled from a
table. The marks come from the highest root, ``h_vee`` is cross-checked
twice, the cyclotomic ring is measured by gcd-reduction, and the
S-matrix normalisation is read off unitarity — so there is no numeric
attestation to carry, only theorem NAMES.
"""

from __future__ import annotations

from srmech.math.q import Q
from functools import lru_cache
from itertools import product as _cartesian_product
from typing import Any, Dict, List, Optional, Sequence, Tuple

from srmech.amsc.format import sha256_bytes
from srmech.math.cyclic import gcd
from srmech.math.groups import zeta_mul
from srmech.math.poly import cyclotomic_polynomial
from srmech.math.qalg import Qalg
from srmech.math.qmat import QMat

__all__ = [
    "affine_fusion_multiplicities",
    "affine_modular_s_matrix",
    "alcove_fold",
    "dominant_weight",
    "integrable_weights",
    "tensor_product_multiplicities",
    "verlinde_fusion_multiplicities",
    "weight_multiplicities",
]


# ──────────────────────────────────────────────────────────────────────
# the A2 data, stated once — every derived quantity below is computed
# FROM these constants, never re-spelled beside them
# ──────────────────────────────────────────────────────────────────────

#: The A2 Cartan matrix.  Its rows ARE the simple roots in the
#: fundamental-weight ("Dynkin label") basis, which is why
#: :data:`A2_SIMPLE_ROOTS` is derived from it rather than written twice.
A2_CARTAN: Tuple[Tuple[int, int], Tuple[int, int]] = ((2, -1), (-1, 2))

#: The simple roots in the fundamental-weight basis — row ``i`` of the
#: Cartan matrix is ``alpha_i`` expressed in that basis.
A2_SIMPLE_ROOTS: Tuple[Tuple[int, int], ...] = A2_CARTAN

#: The three positive roots: ``alpha_1``, ``alpha_2``, ``alpha_1 +
#: alpha_2``.  A2 has THREE, not two — the fold in
#: :func:`tensor_product_multiplicities` must test all three walls, and
#: testing only the two SIMPLE ones is a proven-red perturbation (it
#: leaks weights such as ``(2, -2)`` that sit on the third wall, folds
#: them onto it and mints non-dominant labels, with no crash).
A2_POSITIVE_ROOTS: Tuple[Tuple[int, int], ...] = (
    A2_SIMPLE_ROOTS[0],
    A2_SIMPLE_ROOTS[1],
    (A2_SIMPLE_ROOTS[0][0] + A2_SIMPLE_ROOTS[1][0],
     A2_SIMPLE_ROOTS[0][1] + A2_SIMPLE_ROOTS[1][1]),
)

#: The Weyl vector ``rho`` — the sum of the fundamental weights, i.e.
#: the all-ones label.
A2_RHO: Tuple[int, int] = (1, 1)

#: The metric scale.  The A2 bilinear form on the fundamental-weight
#: basis is ``(1/3)·((2, 1), (1, 2))``; carrying the SCALED form keeps
#: the Freudenthal recursion inside the integers end to end (the factor
#: cancels because the recursion is a RATIO of two form values).
A2_METRIC_SCALE: int = 3

#: The 3-scaled Gram matrix of the fundamental-weight basis.
A2_GRAM_SCALED: Tuple[Tuple[int, int], Tuple[int, int]] = ((2, 1), (1, 2))

#: The gauge the generator provably does not fix, as an ordered item
#: list (a tuple, not a dict, so the module cannot hand out a mutable
#: shared constant and so the content-address serialisation has ONE
#: order).  ``chirality`` is the Z/2 Class-C bit the diagram flip leaves
#: free; ``global_form`` names which lattice between root and weight the
#: group uses; ``metric_scale`` is the stored normalisation convention.
A2_GAUGE_ITEMS: Tuple[Tuple[str, Any], ...] = (
    ("chirality", "fundamental_first"),
    ("global_form", "SU(3)"),
    ("metric_scale", A2_METRIC_SCALE),
)

#: The algebra name the CLASSICAL payloads carry.  A2 is the only algebra
#: the classical stratum above ships.
#:
#: ⚠️ **This comment read "A2 is the only algebra this module ships" until
#: rc461 and is now false**: the affine stratum below ships A1, A2 and D4.
#: The classical ops (:func:`dominant_weight`,
#: :func:`weight_multiplicities`, :func:`tensor_product_multiplicities`)
#: are still A2-only and still hard-code this name; the affine ops take an
#: ``algebra`` argument and carry whichever name they were asked for.
A2_NAME = "A2"


# ──────────────────────────────────────────────────────────────────────
# private helpers — exact integer arithmetic on the lattice
# ──────────────────────────────────────────────────────────────────────


def _exact_div(op: str, numerator: int, denominator: int, what: str) -> int:
    """Exact integer division via ``divmod`` with a remainder-must-be-zero
    guard — the corruption detector of every derivation in this module
    (the :func:`srmech.math.groups._exact_div` shape).  Raises; never
    rounds, never floors."""
    if denominator == 0:
        raise ValueError(
            f"{op}: {what} would divide by zero - the lattice derivation "
            f"does not cohere (divisibility law; a guard that fires is "
            f"evidence)")
    quotient, remainder = divmod(numerator, denominator)
    if remainder != 0:
        raise ValueError(
            f"{op}: {what} = {numerator} is not divisible by "
            f"{denominator} - an exact lattice quantity is an integer "
            f"(divisibility law; a guard that fires is evidence)")
    return quotient


def _check_label(op: str, label: Sequence[int]) -> Tuple[int, int]:
    """Validate a DOMINANT A2 label — a length-2 sequence of non-negative
    plain ints (a ``bool`` is REJECTED: ``True == 1`` would otherwise ride
    the integer lane silently).  Raises ``ValueError`` naming the failing
    law."""
    values = list(label)
    if len(values) != 2:
        raise ValueError(
            f"{op}: an A2 label is a (p, q) pair; got {len(values)} "
            f"coordinate(s) (label-shape law)")
    for i, value in enumerate(values):
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(
                f"{op}: label[{i}] carries a {type(value).__name__}; "
                f"Dynkin labels are plain ints (plain-int law)")
        if value < 0:
            raise ValueError(
                f"{op}: label[{i}] = {value} is negative; this stratum is "
                f"indexed by DOMINANT weights (dominance law)")
    return (values[0], values[1])


def _bilinear(x: Sequence[int], y: Sequence[int]) -> int:
    """The 3-scaled A2 bilinear form on the fundamental-weight basis —
    ``A2_METRIC_SCALE * <x, y>``, an exact integer.  The scale cancels in
    every ratio this module takes, which is precisely why it is carried
    rather than divided out."""
    return (A2_GRAM_SCALED[0][0] * x[0] * y[0]
            + A2_GRAM_SCALED[0][1] * x[0] * y[1]
            + A2_GRAM_SCALED[1][0] * x[1] * y[0]
            + A2_GRAM_SCALED[1][1] * x[1] * y[1])


def _coroot_pairing(op: str, weight: Sequence[int],
                    root: Sequence[int]) -> int:
    """``<weight, root^vee> = 2·<weight, root> / <root, root>``, DERIVED
    from the stored Gram matrix rather than re-spelled as a coordinate
    read.  The metric scale cancels between numerator and denominator, so
    the result is scale-free.

    ⚠️ **The guard here CANNOT FIRE on A2, and saying otherwise would be
    claiming a measurement that no input can move.**  This docstring read
    "the guarded division is what makes that a measurement rather than an
    assertion"; measured over ``[-40, 40]^2`` x the three positive roots
    (19683 pairs), the remainder is 0 every time and the residue SET is
    ``{0}`` — not mostly-zero, identically zero.  The algebra says why:
    with the shipped 3-scaled Gram ``((2,1),(1,2))`` and ``alpha_1 =
    (2,-1)``, ``2<w, alpha_1> = 6·w[0]`` while ``<alpha_1, alpha_1> = 6``,
    so the quotient IS the Dynkin coordinate ``w[0]`` — a polynomial
    identity, and likewise ``w[1]`` and ``w[0]+w[1]`` for the other two
    roots.  The division is exact BY CONSTRUCTION on this algebra.

    The guard is still worth its line, but for the honest reason: it is a
    CORRUPTION detector on the stored constants, and it is the check that
    has to be live if the module is ever widened past A2, where
    non-simply-laced roots make the division genuinely non-trivial.  Both
    of those are MEASURED, not supposed — over ``[-8, 8]^2`` x the three
    roots: shipped Gram **0** fires, a single mistyped Gram entry
    (``((2,1),(1,3))`` or ``((3,1),(1,2))``) **494**, and a non-A2 root
    ``(2,-3)`` **248**.  So the guard is live against the thing it can
    actually catch, and vacuous about the arithmetic this rc performs."""
    return _exact_div(op, 2 * _bilinear(weight, root),
                      _bilinear(root, root),
                      f"the coroot pairing of {tuple(weight)} with "
                      f"{tuple(root)}")


def _reflect(index: int, weight: Tuple[int, int]) -> Tuple[int, int]:
    """The simple reflection ``s_i(w) = w - <w, alpha_i^vee>·alpha_i``.
    In the fundamental-weight basis ``<w, alpha_i^vee>`` IS the ``i``-th
    Dynkin coordinate — this function is the SSoT of the Weyl action, and
    the six matrices below are derived FROM it (never written down beside
    it, which is the transposition trap this module refuses to walk
    into)."""
    coefficient = weight[index]
    root = A2_SIMPLE_ROOTS[index]
    return (weight[0] - coefficient * root[0],
            weight[1] - coefficient * root[1])


def _apply(matrix: Tuple[Tuple[int, int], Tuple[int, int]],
           weight: Sequence[int]) -> Tuple[int, int]:
    """Apply a 2x2 integer matrix to a weight, column-vector convention."""
    return (matrix[0][0] * weight[0] + matrix[0][1] * weight[1],
            matrix[1][0] * weight[0] + matrix[1][1] * weight[1])


def _matmul2(a: Tuple[Tuple[int, int], Tuple[int, int]],
             b: Tuple[Tuple[int, int], Tuple[int, int]]
             ) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """The 2x2 integer matrix product — the closure step of the Weyl
    group build."""
    return (
        (a[0][0] * b[0][0] + a[0][1] * b[1][0],
         a[0][0] * b[0][1] + a[0][1] * b[1][1]),
        (a[1][0] * b[0][0] + a[1][1] * b[1][0],
         a[1][0] * b[0][1] + a[1][1] * b[1][1]),
    )


def _reflection_matrix(index: int) -> Tuple[Tuple[int, int],
                                            Tuple[int, int]]:
    """The matrix of ``s_i`` DERIVED by applying :func:`_reflect` to the
    basis weights: column ``j`` is ``s_i(e_j)``.  Deriving rather than
    transcribing is the mitigation for a measured live trap — a
    hand-written TRANSPOSED Weyl family produces a WELL-FORMED WRONG
    ANSWER (``3 (x) 3`` and ``3 (x) 3-bar`` come out identical, no
    crash)."""
    first = _reflect(index, (1, 0))
    second = _reflect(index, (0, 1))
    return ((first[0], second[0]), (first[1], second[1]))


def _int_determinant(matrix: Tuple[Tuple[int, int], Tuple[int, int]]) -> int:
    """The determinant of an integer 2x2, read through the exact-Q
    :class:`~srmech.math.qmat.QMat` carrier (the sign of a Weyl element
    IS its determinant, so this is the +-1 ledger's SOURCE and not a
    convenience).  Raises if the value is not an integer +-1 — a Weyl
    element is an isometry of the lattice."""
    value = QMat([[matrix[0][0], matrix[0][1]],
                  [matrix[1][0], matrix[1][1]]]).det()
    if value.denominator != 1 or value.numerator not in (-1, 1):
        raise ValueError(
            f"weight_lattice: Weyl element {matrix} has determinant "
            f"{value.numerator}/{value.denominator}, not +-1 - a Weyl "
            f"element is a lattice isometry (Weyl-sign law; a guard that "
            f"fires is evidence)")
    return value.numerator


def _build_weyl_group() -> Tuple[Tuple[Tuple[Tuple[int, int],
                                             Tuple[int, int]], int], ...]:
    """The six-element Weyl group ``W(A2) = S3`` built by CLOSURE from
    the two derived simple reflections, each paired with its ``+-1``
    determinant sign.  Ordered canonically by ``(sign descending, matrix
    lexicographic)`` so the procedure content address is stable across
    interpreters.

    Two coherence guards run here, both raises: every element must agree
    with the composition of :func:`_reflect` calls that generated it (the
    derive-and-assert mitigation), and the closure must terminate at
    exactly six elements."""
    generators = [_reflection_matrix(0), _reflection_matrix(1)]
    identity = ((1, 0), (0, 1))
    elements = {identity}
    frontier = [identity]
    while frontier:
        current = frontier.pop()
        for generator in generators:
            product = _matmul2(generator, current)
            if product not in elements:
                elements.add(product)
                frontier.append(product)
    if len(elements) != 6:
        raise ValueError(
            f"weight_lattice: the Weyl closure produced {len(elements)} "
            f"elements, expected 6 = |S3| (Weyl-order law; a guard that "
            f"fires is evidence)")
    for index in (0, 1):
        matrix = _reflection_matrix(index)
        for probe in ((1, 0), (0, 1), (1, 1), (2, 3), (-1, 4)):
            if _apply(matrix, probe) != _reflect(index, probe):
                raise ValueError(
                    f"weight_lattice: the derived matrix of s_{index} "
                    f"disagrees with the reflection function at {probe} "
                    f"(Weyl-coherence law; a guard that fires is "
                    f"evidence)")
    ordered = sorted(elements, key=lambda m: (-_int_determinant(m), m))
    return tuple((matrix, _int_determinant(matrix)) for matrix in ordered)


#: The Weyl group, derived once at import.
_WEYL = _build_weyl_group()


def _procedure_bytes() -> bytes:
    """The canonical serialisation of the DERIVATION PROCEDURE — algebra
    name, Cartan matrix, positive roots, ``rho``, the scaled Gram matrix
    and the derived Weyl family with signs.  This is what
    ``procedure_sha256`` addresses: two rcs deriving the same label under
    different conventions must not share a content address."""
    parts: List[str] = [
        A2_NAME,
        "cartan=" + ";".join(",".join(str(v) for v in row)
                             for row in A2_CARTAN),
        "positive_roots=" + ";".join(",".join(str(v) for v in root)
                                     for root in A2_POSITIVE_ROOTS),
        "rho=" + ",".join(str(v) for v in A2_RHO),
        "gram_scaled=" + ";".join(",".join(str(v) for v in row)
                                  for row in A2_GRAM_SCALED),
        "metric_scale=" + str(A2_METRIC_SCALE),
        "weyl=" + ";".join(
            "{}|{}".format(",".join(str(v) for row in matrix for v in row),
                           sign)
            for matrix, sign in _WEYL),
        "weights=freudenthal_recursion",
        "fusion=racah_speiser_signed_fold",
    ]
    return "\n".join(parts).encode("utf-8")


def _procedure_sha256() -> str:
    """The Class-A content address of the derivation procedure."""
    return sha256_bytes(_procedure_bytes())


def _weyl_orbit(weight: Sequence[int]) -> Tuple[Tuple[int, int], ...]:
    """The DISTINCT Weyl images of a weight, sorted — the orbit as a
    catalog, from which the orbit SIZE is read rather than asserted from
    a coordinate-vanishing rule."""
    images = {_apply(matrix, weight) for matrix, _ in _WEYL}
    return tuple(sorted(images))


def _dominant_conjugate(op: str, weight: Sequence[int]) -> Tuple[int, int]:
    """The unique dominant weight in a weight's Weyl orbit, found by
    scanning the six elements (never by an unbounded fold loop, whose
    termination would be an assumption rather than a measurement)."""
    for matrix, _ in _WEYL:
        image = _apply(matrix, weight)
        if image[0] >= 0 and image[1] >= 0:
            return image
    raise ValueError(
        f"{op}: weight {tuple(weight)} has no dominant Weyl conjugate - "
        f"every orbit meets the closed dominant chamber "
        f"(chamber law; a guard that fires is evidence)")


def _strictly_dominant_fold(op: str, weight: Sequence[int]
                            ) -> Tuple[Tuple[int, int], int]:
    """The signed fold of a REGULAR weight into the OPEN dominant
    chamber: the unique ``w`` with ``w(weight)`` strictly dominant,
    returned with its ``+-1`` sign.  Raises unless exactly one element
    qualifies — on a wall there are none, and the caller is required to
    have removed wall weights first (that removal, not this guard, is
    where the ``0`` contribution of a wall is decided)."""
    found: List[Tuple[Tuple[int, int], int]] = []
    for matrix, sign in _WEYL:
        image = _apply(matrix, weight)
        if image[0] > 0 and image[1] > 0:
            found.append((image, sign))
    if len(found) != 1:
        raise ValueError(
            f"{op}: weight {tuple(weight)} has {len(found)} strictly "
            f"dominant Weyl images, expected exactly 1 - a regular weight "
            f"has one (regularity law; a guard that fires is evidence)")
    return found[0]


def _on_a_wall(op: str, weight: Sequence[int]) -> bool:
    """True when a weight is fixed by some reflection — i.e. its coroot
    pairing with SOME positive root vanishes.  All THREE positive roots
    are tested; A2 has three and only two of them are simple."""
    for root in A2_POSITIVE_ROOTS:
        if _coroot_pairing(op, weight, root) == 0:
            return True
    return False


def _dominant_levels(p: int, q: int) -> Dict[Tuple[int, int],
                                             Tuple[int, int]]:
    """Every DOMINANT weight of ``V_(p,q)`` mapped to its level ``(m,
    n)``, where the weight is ``lambda - m·alpha_1 - n·alpha_2``.

    The level map is linear with determinant ``3 != 0``, so it is
    injective — each dominant weight has ONE level, which is what lets
    the Freudenthal recursion below be ordered by ``m + n`` with every
    lookup already resolved."""
    span = p + q
    levels: Dict[Tuple[int, int], Tuple[int, int]] = {}
    for m in range(span + 1):
        for n in range(span + 1):
            a = p - m * A2_SIMPLE_ROOTS[0][0] - n * A2_SIMPLE_ROOTS[1][0]
            b = q - m * A2_SIMPLE_ROOTS[0][1] - n * A2_SIMPLE_ROOTS[1][1]
            if a >= 0 and b >= 0:
                levels[(a, b)] = (m, n)
    return levels


def _freudenthal(op: str, p: int, q: int
                 ) -> Tuple[Dict[Tuple[int, int], int],
                            Dict[Tuple[int, int], Tuple[int, int]]]:
    """The multiplicity of every dominant weight of ``V_(p,q)`` by the
    Freudenthal recursion, in exact integers.

    ``m(mu)·[<lam+rho, lam+rho> - <mu+rho, mu+rho>] = 2·sum_{alpha>0}
    sum_{k>=1} m(mu + k·alpha)·<mu + k·alpha, alpha>``

    Both sides carry the 3-scaled form, so the scale cancels and the
    recursion never leaves the integers.  Non-dominant weights are read
    through :func:`_dominant_conjugate` (Weyl invariance of
    multiplicities); ``k`` is bounded by the LEVEL, so the sum is finite
    by construction rather than by a convergence argument."""
    levels = _dominant_levels(p, q)
    highest = (p, q)
    shifted_highest = (p + A2_RHO[0], q + A2_RHO[1])
    highest_norm = _bilinear(shifted_highest, shifted_highest)
    multiplicities: Dict[Tuple[int, int], int] = {}
    ordering = sorted(levels,
                      key=lambda lab: (levels[lab][0] + levels[lab][1], lab))
    for label in ordering:
        if label == highest:
            multiplicities[label] = 1
            continue
        m, n = levels[label]
        bounds = (m, n, m if m < n else n)
        shifted = (label[0] + A2_RHO[0], label[1] + A2_RHO[1])
        denominator = highest_norm - _bilinear(shifted, shifted)
        total = 0
        for root_index, root in enumerate(A2_POSITIVE_ROOTS):
            for step in range(1, bounds[root_index] + 1):
                probe = (label[0] + step * root[0],
                         label[1] + step * root[1])
                conjugate = _dominant_conjugate(op, probe)
                found = multiplicities.get(conjugate, 0)
                if found:
                    total += found * _bilinear(probe, root)
        multiplicities[label] = _exact_div(
            op, 2 * total, denominator,
            f"the Freudenthal numerator at {label}")
    return multiplicities, levels


def _dimension(op: str, p: int, q: int) -> int:
    """The Weyl dimension of ``V_(p,q)`` — ``(p+1)(q+1)(p+q+2)/2``, with
    the ``/2`` guarded (the Class-N stage; the product of two consecutive
    integers is even, and a guard that fires is evidence)."""
    return _exact_div(op, (p + 1) * (q + 1) * (p + q + 2), 2,
                      f"the Weyl dimension numerator of {(p, q)}")


# ──────────────────────────────────────────────────────────────────────
# the ops
# ──────────────────────────────────────────────────────────────────────


def dominant_weight(p: int, q: int) -> Dict[str, Any]:
    """The stored A2 label object — **Class A**, the content-address mint
    whose product IS the SSoT this stratum stores.

    Everything else in this module DERIVES from the label, and derivation
    is measurably SUBLINEAR in the object derived: ``(24, 24)`` has
    dimension 15625 but only 313 dominant weights.  So the procedural
    form is not merely acceptable, it is cheaper than the coordinate
    form.  What it does NOT do is close: the generator is the Cartan
    matrix, and the Cartan matrix is invariant under the diagram flip, so
    it cannot tell ``3`` from ``3-bar`` (see the module docstring).  That
    is why the payload carries an explicit ``gauge`` block and why
    ``label_sha256`` binds the label AND the gauge AND
    ``procedure_sha256`` rather than hashing the label alone.

    Args:
        p: the first Dynkin label, ``>= 0``.
        q: the second Dynkin label, ``>= 0``.

    Returns:
        ``{"algebra"`` (``"A2"``), ``"label"`` (the ``(p, q)`` pair),
        ``"dimension"``, ``"conjugate"`` (``(q, p)`` — the Class-C
        chirality partner), ``"n_ality"`` (``(p - q) % 3``, the Class-I
        Z/3 grading fusion conserves), ``"cartan"``, ``"gauge"`` (the
        three bits the generator does not fix), ``"procedure_sha256"``,
        ``"label_sha256"}``.

    Worked examples: ``dominant_weight(1, 0)`` is the ``3`` — dimension
    3, conjugate ``(0, 1)``, N-ality 1.  ``dominant_weight(1, 1)`` is the
    adjoint ``8`` — self-conjugate, N-ality 0.  ``(3, 0)`` is the 10;
    ``(2, 2)`` is the 27.

    C-parity (ADR-0009, recorded): no C peer; the weight-lattice stratum
    ships Python-first under the noted-disparity ruling.

    Note:
        Exact integers; no float; no ``abs``.
    """
    label = _check_label("dominant_weight", (p, q))
    dimension = _dimension("dominant_weight", label[0], label[1])
    procedure = _procedure_sha256()
    gauge = dict(A2_GAUGE_ITEMS)
    body = "\n".join([
        A2_NAME,
        "label=" + ",".join(str(v) for v in label),
        "gauge=" + ";".join(f"{key}={value}" for key, value in
                            A2_GAUGE_ITEMS),
        "procedure=" + procedure,
    ]).encode("utf-8")
    return {
        "algebra": A2_NAME,
        "label": label,
        "dimension": dimension,
        "conjugate": (label[1], label[0]),
        "n_ality": (label[0] - label[1]) % 3,
        "cartan": A2_CARTAN,
        "gauge": gauge,
        "procedure_sha256": procedure,
        "label_sha256": sha256_bytes(body),
    }


def weight_multiplicities(p: int, q: int) -> Dict[str, Any]:
    """The weight system of ``V_(p,q)`` — **Class E**, the catalog
    enumeration, carried as DOMINANT REPRESENTATIVES with orbit sizes so
    the payload is ``O(dim^(2/3))`` rather than ``O(dim)``.

    The multiplicities come from the Freudenthal recursion over the
    3-scaled Gram matrix, which keeps every intermediate an exact integer
    (measured on the ``[0, 11]^2`` window: 6135 divisions, 0 inexact).
    Orbit sizes are read as the cardinality of the DERIVED Weyl orbit,
    not asserted from a coordinate-vanishing rule.

    ⚠️ **Explicit class non-claim: this op is NOT Class K.**  Freudenthal's
    recursion is sign-free; the signs of this module all live in
    :func:`tensor_product_multiplicities`, and claiming K here would assert
    a phase boundary this op never crosses.

    Args:
        p: the first Dynkin label, ``>= 0``.
        q: the second Dynkin label, ``>= 0``.

    Returns:
        ``{"algebra", "label", "dimension", "dominant"`` (a tuple of
        ``(a, b, multiplicity)`` triples, sorted), ``"orbit_sizes"``
        (parallel to ``dominant``), ``"n_dominant"``, ``"n_weights"``
        (the total weight count WITH multiplicity, which the dimension
        law below equates to the dimension), ``"procedure_sha256"``,
        ``"weights_sha256"}``.

    In-op guard, a raise: the **dimension law** ``sum_nu
    m(nu)·|orbit(nu)| == dim(p, q)`` — the weight system reproduces the
    dimension the label formula gives, or the payload does not cohere.

    Worked example: ``weight_multiplicities(1, 1)`` returns ``dominant =
    ((0, 0, 2), (1, 1, 1))`` with ``orbit_sizes = (1, 6)`` — the
    adjoint's zero weight has multiplicity **2**, visible on the face of
    the payload, and that 2 is the RANK of su(3).

    C-parity (ADR-0009, recorded): no C peer; Python-first under the
    noted-disparity ruling.

    Note:
        Exact integers; no float; no ``abs``.
    """
    label = _check_label("weight_multiplicities", (p, q))
    anchor = dominant_weight(label[0], label[1])
    dimension = anchor["dimension"]
    multiplicities, _levels = _freudenthal(
        "weight_multiplicities", label[0], label[1])
    dominant: List[Tuple[int, int, int]] = []
    orbit_sizes: List[int] = []
    total = 0
    for weight in sorted(multiplicities):
        found = multiplicities[weight]
        orbit = len(_weyl_orbit(weight))
        dominant.append((weight[0], weight[1], found))
        orbit_sizes.append(orbit)
        total += found * orbit
    if total != dimension:
        raise ValueError(
            f"weight_multiplicities: sum of m(nu)·|orbit(nu)| = {total} "
            f"!= dim{label} = {dimension} - the weight system must "
            f"reproduce the dimension (dimension law; a guard that fires "
            f"is evidence)")
    body = ";".join(
        f"{a},{b},{m},{o}"
        for (a, b, m), o in zip(dominant, orbit_sizes)).encode("utf-8")
    return {
        "algebra": A2_NAME,
        "label": label,
        "dimension": dimension,
        "dominant": tuple(dominant),
        "orbit_sizes": tuple(orbit_sizes),
        "n_dominant": len(dominant),
        "n_weights": total,
        "procedure_sha256": anchor["procedure_sha256"],
        "weights_sha256": sha256_bytes(body),
    }


def tensor_product_multiplicities(a: Sequence[int],
                                  b: Sequence[int]) -> Dict[str, Any]:
    """The A2 tensor-product multiplicities ``N_ab^c`` by Racah–Speiser —
    **Class K**, the ``+-1`` ledger at the reflection walls, which is
    exactly where a sign count becomes a fusion coefficient.

    The instrument, stated as the count it is: take the weight system of
    ``V_b`` with multiplicities, translate every weight by ``a + rho``,
    DISCARD the translates that land on a reflection wall (they
    contribute exactly zero), fold the rest into the open dominant
    chamber under the 6-element Weyl group carrying the element's ``+-1``
    determinant, and accumulate ``sign · m(nu)`` against ``w(mu) - rho``.
    There is no integral and no measure anywhere in that sentence.  The
    "convolution of orbital measures against Haar" phrasing is the
    continuum shadow of this signed integer count.

    ⚠️ **Explicit class non-claim: this op is NOT Class L.**  Its
    finite-group sibling
    :func:`srmech.math.groups.fusion_multiplicities` is Class L *because*
    it contracts against the class-algebra eigenbasis; this op builds no
    eigenbasis and projects onto nothing.  That distinction is the whole
    point of the rc.

    ⚠️ **All THREE positive roots are tested for the wall.** A2 has three
    and only two are simple; testing the two simple walls alone is a
    measured, well-formed WRONG ANSWER — translates such as ``(2, -2)``
    survive, fold onto a wall and mint NON-DOMINANT labels, with no
    crash.  The two-wall variant ships as a proven-red perturbation in
    the tests.

    Args:
        a: a dominant A2 label ``(p1, q1)``.
        b: a dominant A2 label ``(p2, q2)``.

    Returns:
        ``{"algebra", "a", "b", "constituents"`` (a tuple of ``(p, q,
        multiplicity)`` triples sorted by ``(dimension, label)``),
        ``"dim_a", "dim_b", "dim_check"`` (``dim_a·dim_b``),
        ``"singlet_multiplicity"`` (surfaced deliberately — it makes the
        "is the singlet present" question readable straight off the
        payload), ``"n_constituents"``, ``"procedure_sha256"``,
        ``"fusion_sha256"}``.

    ⚠️ ``fusion_sha256`` addresses the **ANSWER, not the operation** — it
    is minted over the ``constituents`` tuple ALONE.  It is deliberately a
    WEAKER object than :func:`dominant_weight`'s ``label_sha256``, which
    binds label AND gauge AND procedure; do not read the two as peers just
    because they sit in sibling payloads.  Measured over the ``[0,3]^2``
    window: 256 pairs mint **136** distinct addresses, so 120 pairs SHARE
    one — and in every shared case the constituent tuple is identical (0
    shares with a differing answer), which is the address behaving
    correctly for what it addresses.  ``(0,0) (x) (0,1)`` and ``(0,1) (x)
    (0,0)`` collide because fusion is commutative and the answer really is
    the same object.  If you need to bind the operands, they are right
    there in the payload as ``a`` and ``b``, and the convention under
    which they were derived is in ``procedure_sha256``.

    In-op guards, each a raise: **non-negativity after cancellation** (a
    surviving negative is a BUG DETECTOR, never a result), **strict
    dominance** of every folded label, and the **dimension law**
    ``sum_c N·d(c) == d(a)·d(b)``.

    Worked example: ``tensor_product_multiplicities((1, 0), (1, 0))``
    returns ``((0, 1, 1), (2, 0, 1))`` with ``dim_check = 9`` — that is
    ``3 (x) 3 = 3-bar (+) 6``: the ``3-bar`` at multiplicity one, exactly
    one degree-6 channel, and the spurious same-label channel at exactly
    zero.  ``((1, 1), (1, 1))`` is ``8 (x) 8 = 1 + 8 + 8 + 10 + 10-bar +
    27``.

    Cost, honest: ``(12, 9) (x) (10, 10)`` — dimensions 1495 x 1331, 229
    constituents — runs in hundredths of a second.  The op targets the
    same small-label stratum every sibling does; a large label makes it
    SLOW, never wrong.

    C-parity (ADR-0009, recorded): no C peer; Python-first under the
    noted-disparity ruling.

    Note:
        Exact integers; no float; no ``abs`` — the sign-handling is the
        explicit Class-K Weyl determinant ledger with Class-C
        re-application on the folded label.
    """
    op = "tensor_product_multiplicities"
    label_a = _check_label(op, a)
    label_b = _check_label(op, b)
    system_b = weight_multiplicities(label_b[0], label_b[1])
    anchor_a = dominant_weight(label_a[0], label_a[1])
    shift = (label_a[0] + A2_RHO[0], label_a[1] + A2_RHO[1])

    ledger: Dict[Tuple[int, int], int] = {}
    for entry in system_b["dominant"]:
        weight = (entry[0], entry[1])
        found = entry[2]
        for orbit_weight in _weyl_orbit(weight):
            translate = (shift[0] + orbit_weight[0],
                         shift[1] + orbit_weight[1])
            if _on_a_wall(op, translate):
                continue           # Class-K pin: the wall contributes 0
            image, sign = _strictly_dominant_fold(op, translate)
            folded = (image[0] - A2_RHO[0], image[1] - A2_RHO[1])
            if folded[0] < 0 or folded[1] < 0:
                raise ValueError(
                    f"{op}: the fold of {translate} minted the "
                    f"non-dominant label {folded} - every folded "
                    f"constituent is dominant (dominance law; a guard "
                    f"that fires is evidence)")
            ledger[folded] = ledger.get(folded, 0) + sign * found

    constituents: List[Tuple[int, int, int]] = []
    dimension_total = 0
    for folded in ledger:
        found = ledger[folded]
        if found == 0:
            continue
        if found < 0:
            raise ValueError(
                f"{op}: constituent {folded} survives cancellation with "
                f"multiplicity {found} - a fusion coefficient counts "
                f"channels (non-negativity law; a guard that fires is "
                f"evidence)")
        constituents.append((folded[0], folded[1], found))
    constituents.sort(
        key=lambda row: (_dimension(op, row[0], row[1]), row[0], row[1]))
    for row in constituents:
        dimension_total += row[2] * _dimension(op, row[0], row[1])

    dim_a = anchor_a["dimension"]
    dim_b = system_b["dimension"]
    if dimension_total != dim_a * dim_b:
        raise ValueError(
            f"{op}: sum N·d = {dimension_total} != d{label_a}·d{label_b} "
            f"= {dim_a * dim_b} - fusion preserves dimension (dimension "
            f"law; a guard that fires is evidence)")

    body = ";".join(f"{p},{q},{m}" for p, q, m in constituents).encode("utf-8")
    return {
        "algebra": A2_NAME,
        "a": label_a,
        "b": label_b,
        "constituents": tuple(constituents),
        "dim_a": dim_a,
        "dim_b": dim_b,
        "dim_check": dim_a * dim_b,
        "singlet_multiplicity": ledger.get((0, 0), 0),
        "n_constituents": len(constituents),
        "procedure_sha256": anchor_a["procedure_sha256"],
        "fusion_sha256": sha256_bytes(body),
    }


# ══════════════════════════════════════════════════════════════════════
# rc461 — THE AFFINE / KAC-WALTON STRATUM
# ══════════════════════════════════════════════════════════════════════
#
# The classical stratum above answers "what does V_a (x) V_b contain".
# This one answers the LEVEL-TRUNCATED question — what survives at level
# k — and it is the same instrument class: a SIGNED INTEGER COUNT.
#
# WHY THE INFINITE GROUP IS NOT AN OBSTACLE
# =========================================
# W(A2) has six elements and ``_WEYL`` enumerates them.  The AFFINE Weyl
# group W-hat_k = W (semidirect) kappa·Q^vee is INFINITE, so enumeration
# cannot survive the widening.  What replaces it is an ITERATIVE fold
# with an EXACT INTEGER TERMINATION CERTIFICATE:
#
#   * in affine Dynkin labels ``a = (a_0, a_1, ..., a_r)`` constrained by
#     ``sum_j comark_j · a_j == kappa``, EVERY generator — the finite
#     ``s_1 .. s_r`` and the affine ``s_0`` alike — collapses to ONE
#     form, ``s_i: a_j -> a_j - C^aff_ij · a_i``;
#   * the monovariant ``Q(a) = sum_j a_j^2`` falls by EXACTLY
#     ``quantum · a_i`` on every step, where ``quantum`` is DERIVED from
#     the affine Cartan matrix (``2·kappa`` for A2, ``4·kappa`` for A1);
#   * a step fires only when ``a_i < 0``, so the drop is strictly
#     negative AND integer-quantised at ``>= quantum`` per step;
#   * ``Q >= kappa^2 / (r + 1)`` on the constraint simplex, so a step
#     BOUND is computed BEFORE the loop and asserted against inside it.
#
# So termination is MEASURED, not assumed, and the per-step law is
# checked on EVERY step rather than once.
#
# ⚠️ THE TERMINATION PROOF IS SCOPED TO A1 AND A2, AND THE CODE ENFORCES
# THAT RATHER THAN TRUSTING IT.  The quantum collapse needs
# ``sum_{j != i} a_j == kappa - a_i``, which holds only because the A1
# and A2 affine diagrams have every node adjacent to every other.  For
# ``A_n, n >= 3`` (and for D4) that fails and the step could RAISE ``Q``.
# :func:`_monovariant_quantum` therefore RAISES on any algebra whose
# affine Cartan does not satisfy the collapse identity — the fold refuses
# D4 rather than looping on it.
#
# WHAT THE S-MATRIX ROUTE REACHES INSTEAD
# =======================================
# :func:`affine_modular_s_matrix` is a FINITE Weyl sum with no fold, so
# the termination question never arises and it carries D4.  That is why
# :func:`verlinde_fusion_multiplicities` answers for D4 where
# :func:`affine_fusion_multiplicities` refuses: two genuinely different
# instruments with two different scopes, each stated.
#
# THE ONLY STORED DATA IS A SIMPLE-ROOT REALISATION
# =================================================
# Cartan matrices, root systems, the highest root, the marks, the dual
# Coxeter number, the fundamental weights, rho and the affine Cartan are
# every one DERIVED from :data:`AFFINE_AMBIENT_ROOTS` at import.  Nothing
# below is transcribed beside its derivation — the same discipline
# :func:`_reflection_matrix` already applies to the six classical Weyl
# matrices, and for the same measured reason.
#
# CARRIER: plain ``int`` and tuples of ``int`` everywhere on the wire;
# ``Q`` (srmech's own exact rational, NOT ``fractions.Fraction`` — that is
# a STRICT-ZERO banned engine here) for the ONE import-time solve (the
# fundamental weights off the Cartan inverse), immediately re-integerised
# against a stored denominator; ``QMat`` for exact determinants; ``Qalg`` over ``Phi_e``
# for the ONE division that genuinely needs a field (the Verlinde
# contraction).  NO new carrier TYPE crosses the boundary — the zeta
# values ship as the integer coordinate vectors
# :func:`srmech.math.groups.character_table` already mints and
# :func:`srmech.math.groups.zeta_mul` already reads.
#
# C-parity (ADR-0009, recorded): no C peer, for the same reason the
# classical stratum has none.

#: The simple roots of each shipped algebra, in an integer AMBIENT basis
#: with the standard inner product.  Every realisation here is
#: simply-laced with ``(alpha, alpha) == 2``, which is what lets the
#: reflection ``s_i(v) = v - (v, alpha_i)·alpha_i`` stay integral.
#:
#: This dict is the module's ONLY stored Lie data for the affine
#: stratum.  Cartan matrices, marks, ``h^vee``, fundamental weights and
#: the affine Cartan are all derived from it.
AFFINE_AMBIENT_ROOTS: Dict[str, Tuple[Tuple[int, ...], ...]] = {
    "A1": ((1, -1),),
    "A2": ((1, -1, 0), (0, 1, -1)),
    "D4": ((1, -1, 0, 0), (0, 1, -1, 0), (0, 0, 1, -1), (0, 0, 1, 1)),
}

#: The algebras the affine stratum ships, in payload order.
AFFINE_ALGEBRAS: Tuple[str, ...] = ("A1", "A2", "D4")


def _magnitude(value: int) -> int:
    """The Class-K pin-slot magnitude of an exact integer — the sign
    boundary read as a phase boundary, never an ALU ``abs()`` call.  The
    Class-C re-application, where a caller needs one, is the explicit
    ``-value`` at the use site."""
    return value if value >= 0 else -value


def _ambient_dot(x: Sequence[int], y: Sequence[int]) -> int:
    """The standard inner product on the integer ambient basis."""
    return sum(a * b for a, b in zip(x, y))


def _rational_inverse(matrix: Sequence[Sequence[int]]
                      ) -> List[List[Q]]:
    """Exact Gauss-Jordan inverse of a small integer matrix over ``Q``.

    Used at import for exactly one thing — solving ``(omega_j, alpha_i) =
    delta_ij`` for the fundamental weights — and its output is
    immediately re-integerised against a stored denominator, so no
    rational carrier reaches any payload.  Raises if the matrix is
    singular; a Cartan matrix never is.

    ⚠️ rc461 part 3 — the carrier is :class:`srmech.math.q.Q`, NOT
    ``fractions.Fraction``.  ``tests/test_selfhosting_import_ban.py``
    makes ``fractions`` a STRICT-ZERO ``BANNED_ENGINE`` for this package
    (ADR-0005 §2.1: srmech does its own math on its own carrier), and
    this module was importing it — the ban caught a real violation, not
    a style point.  ``Q`` is the native ``srmech_rational_*`` carrier and
    is a drop-in here: construction from ``int``, true division, the
    ``!= 0`` pivot test, and ``numerator`` / ``denominator`` on the way
    back out to integers."""
    size = len(matrix)
    rows = [[Q(value) for value in row]
            + [Q(1 if i == j else 0) for j in range(size)]
            for i, row in enumerate(matrix)]
    for column in range(size):
        pivot = None
        for index in range(column, size):
            if rows[index][column] != 0:
                pivot = index
                break
        if pivot is None:
            raise ValueError(
                f"weight_lattice: the Cartan matrix {matrix} is singular - "
                f"a Cartan matrix of a semisimple algebra is not "
                f"(invertibility law; a guard that fires is evidence)")
        rows[column], rows[pivot] = rows[pivot], rows[column]
        scale = rows[column][column]
        rows[column] = [value / scale for value in rows[column]]
        for index in range(size):
            if index == column or rows[index][column] == 0:
                continue
            factor = rows[index][column]
            rows[index] = [value - factor * other
                           for value, other in zip(rows[index], rows[column])]
    return [row[size:] for row in rows]


def _ambient_root_system(roots: Sequence[Sequence[int]]
                         ) -> Tuple[Tuple[int, ...], ...]:
    """The FULL root system, by closure of the simple roots under the
    simple reflections — enumerated, never counted from a formula, so the
    dual Coxeter number derived from it is a read and not a recall."""
    seen = {tuple(root) for root in roots}
    frontier = list(seen)
    while frontier:
        current = frontier.pop()
        for root in roots:
            image = tuple(x - _ambient_dot(current, root) * y
                          for x, y in zip(current, root))
            if image not in seen:
                seen.add(image)
                frontier.append(image)
    return tuple(sorted(seen))


def _simple_root_coefficients(inverse: Sequence[Sequence[Q]],
                              roots: Sequence[Sequence[int]],
                              vector: Sequence[int]) -> Optional[Tuple[int, ...]]:
    """The coefficients of ``vector`` in the SIMPLE-ROOT basis, as exact
    integers, or ``None`` when any coefficient is negative.  Raises if a
    coefficient is not an integer — a root always has integer expansion
    coefficients, so a fraction here is a corrupted realisation."""
    pairings = [_ambient_dot(vector, root) for root in roots]
    coefficients = []
    for index in range(len(roots)):
        value = sum(inverse[index][k] * pairings[k] for k in range(len(roots)))
        if value.denominator != 1:
            raise ValueError(
                f"weight_lattice: {tuple(vector)} has the non-integer "
                f"simple-root coefficient {value} - a root expands over the "
                f"simple roots in Z (root-lattice law; a guard that fires is "
                f"evidence)")
        coefficients.append(int(value))
    if any(value < 0 for value in coefficients):
        return None
    return tuple(coefficients)


def _smith_diagonal(matrix: Sequence[Sequence[int]]) -> Tuple[int, ...]:
    """The Smith-normal-form diagonal of a square integer matrix, exact.

    Applied to a Cartan matrix this IS the invariant-factor decomposition
    of ``P / Q`` — the centre of the simply-connected group — which is
    what makes the D4 acceptance test a DERIVATION rather than a recall
    of "the centre of Spin(8) is the Klein four-group".  The divisibility
    chain is asserted before return; a break in it means the elimination
    is wrong, and a wrong SNF would silently name the wrong group."""
    work = [list(row) for row in matrix]
    rows, columns = len(work), len(work[0])
    diagonal: List[int] = []
    top = 0
    while top < rows and top < columns:
        pivot = None
        for i in range(top, rows):
            for j in range(top, columns):
                if work[i][j] == 0:
                    continue
                if (pivot is None
                        or _magnitude(work[i][j])
                        < _magnitude(work[pivot[0]][pivot[1]])):
                    pivot = (i, j)
        if pivot is None:
            break
        work[top], work[pivot[0]] = work[pivot[0]], work[top]
        for row in work:
            row[top], row[pivot[1]] = row[pivot[1]], row[top]
        busy = True
        while busy:
            busy = False
            for i in range(top + 1, rows):
                if work[i][top] == 0:
                    continue
                quotient = work[i][top] // work[top][top]
                work[i] = [x - quotient * y
                           for x, y in zip(work[i], work[top])]
                if work[i][top] != 0:
                    work[top], work[i] = work[i], work[top]
                    busy = True
            for j in range(top + 1, columns):
                if work[top][j] == 0:
                    continue
                quotient = work[top][j] // work[top][top]
                for row in work:
                    row[j] -= quotient * row[top]
                if work[top][j] != 0:
                    for row in work:
                        row[j], row[top] = row[top], row[j]
                    busy = True
        value = work[top][top]
        diagonal.append(value if value > 0 else -value)
        top += 1
    # ── the divisibility REPAIR pass ──────────────────────────────────
    # Elimination alone produces a diagonal, NOT the invariant factors:
    # measured, ``((6, 0), (0, 4))`` comes out of the loop above as
    # ``(4, 6)``, which is a diagonal form but not a Smith one.  For a
    # diagonal pair the Smith form is ``(gcd, lcm)``, and sweeping that
    # substitution until it is stable yields the divisibility chain.
    # Without this pass the guard below RAISES on such a matrix — safe,
    # but a raise where an answer exists is still the wrong answer.
    repairing = True
    while repairing:
        repairing = False
        for index in range(len(diagonal) - 1):
            left, right = diagonal[index], diagonal[index + 1]
            if right % left == 0:
                continue
            common = gcd(left, right)
            diagonal[index] = common
            diagonal[index + 1] = _exact_div(
                "weight_lattice", left * right, common,
                f"the Smith lcm of {left} and {right}")
            repairing = True
    for index in range(len(diagonal) - 1):
        if diagonal[index + 1] % diagonal[index] != 0:
            raise ValueError(
                f"weight_lattice: the Smith diagonal {tuple(diagonal)} "
                f"breaks the divisibility chain at index {index} - invariant "
                f"factors divide upward (Smith law; a guard that fires is "
                f"evidence)")
    return tuple(diagonal)


def _build_affine_stratum(name: str) -> Dict[str, Any]:
    """Derive EVERYTHING about one algebra from its simple roots.

    Cartan matrix, full root system, highest root, marks, dual Coxeter
    number, fundamental weights (and the denominator clearing them),
    ``rho``, the affine Cartan matrix and the centre's invariant factors
    — all read off :data:`AFFINE_AMBIENT_ROOTS`.  Guards, each a raise:
    every simple root has norm 2 (simply-laced law), the highest root is
    unique, and ``h^vee`` agrees with the independent ``|Delta| / rank``
    count that simply-laced algebras satisfy."""
    roots = AFFINE_AMBIENT_ROOTS[name]
    rank = len(roots)
    for index, root in enumerate(roots):
        norm = _ambient_dot(root, root)
        if norm != 2:
            raise ValueError(
                f"weight_lattice: simple root {index} of {name} has norm "
                f"{norm}, not 2 - this stratum ships simply-laced algebras "
                f"only (simply-laced law; a guard that fires is evidence)")
    cartan = tuple(tuple(_ambient_dot(a, b) for b in roots) for a in roots)
    inverse = _rational_inverse(cartan)
    system = _ambient_root_system(roots)

    highest = None
    for vector in system:
        coefficients = _simple_root_coefficients(inverse, roots, vector)
        if coefficients is None:
            continue
        if highest is None or sum(coefficients) > sum(highest[1]):
            highest = (vector, coefficients)
    if highest is None:
        raise ValueError(
            f"weight_lattice: {name} has no positive root - the root system "
            f"derivation did not cohere (root-system law; a guard that fires "
            f"is evidence)")
    theta, marks = highest
    dual_coxeter = 1 + sum(marks)
    coxeter_check = _exact_div(
        "weight_lattice", len(system), rank,
        f"the {name} Coxeter number |Delta| / rank")
    if coxeter_check != dual_coxeter:
        raise ValueError(
            f"weight_lattice: {name} has h^vee = {dual_coxeter} from the "
            f"marks but |Delta| / rank = {coxeter_check} - the two agree for "
            f"a simply-laced algebra (Coxeter law; a guard that fires is "
            f"evidence)")

    weights = []
    for j in range(rank):
        vector = [Q(0)] * len(roots[0])
        for k in range(rank):
            for t in range(len(vector)):
                vector[t] += inverse[j][k] * roots[k][t]
        weights.append(tuple(vector))
    denominator = 1
    for weight in weights:
        for value in weight:
            denominator = (denominator // gcd(denominator, value.denominator)
                           * value.denominator)
    scaled_weights = []
    for weight in weights:
        scaled_weights.append(tuple(
            _exact_div("weight_lattice", value.numerator * denominator,
                       value.denominator,
                       f"the scaled {name} fundamental weight")
            for value in weight))
    scaled_rho = tuple(sum(weight[t] for weight in scaled_weights)
                       for t in range(len(roots[0])))

    affine = [[0] * (rank + 1) for _ in range(rank + 1)]
    affine[0][0] = 2
    for j in range(rank):
        affine[0][j + 1] = -_ambient_dot(theta, roots[j])
        affine[j + 1][0] = -_ambient_dot(roots[j], theta)
        for k in range(rank):
            affine[j + 1][k + 1] = cartan[j][k]
    centre = tuple(d for d in _smith_diagonal(cartan) if d != 1)
    return {
        "name": name,
        "rank": rank,
        "roots": roots,
        "cartan": cartan,
        "root_system": system,
        "n_roots": len(system),
        "theta": theta,
        "marks": marks,
        "comarks": (1,) + marks,
        "h_vee": dual_coxeter,
        "denominator": denominator,
        "scaled_weights": tuple(scaled_weights),
        "scaled_rho": scaled_rho,
        "affine_cartan": tuple(tuple(row) for row in affine),
        "centre_invariant_factors": centre,
    }


#: Every shipped affine stratum, derived once at import.  Building all
#: three costs one root-system closure each (2 / 6 / 24 roots) — the
#: 192-element D4 Weyl group is NOT built here, because only the
#: S-matrix needs it and it is cached lazily.
_AFFINE_STRATA: Dict[str, Dict[str, Any]] = {
    name: _build_affine_stratum(name) for name in AFFINE_ALGEBRAS
}


def _require_foldable(op: str, stratum: Dict[str, Any]) -> None:
    """The fold's SCOPE CHECK, spelled as one call at the top of each op
    that folds, so the refusal a caller sees is the TERMINATION reason
    and not an incidental downstream failure.  Delegates to
    :func:`_monovariant_quantum` — one SSoT, no second predicate."""
    _monovariant_quantum(op, stratum, 1)


def _affine_stratum(op: str, algebra: Any) -> Dict[str, Any]:
    """Look up a shipped stratum, RAISING with the shipped set named.

    ⚠️ This does NOT gate the fold.  Which algebras can be FOLDED is
    decided by :func:`_has_monovariant` off the affine Cartan matrix, so
    the fold's scope is derived from the termination proof rather than
    from a second hand-maintained list that could drift away from it."""
    if not isinstance(algebra, str):
        raise ValueError(
            f"{op}: algebra carries a {type(algebra).__name__}; it names one "
            f"of {AFFINE_ALGEBRAS} (algebra-name law)")
    if algebra not in _AFFINE_STRATA:
        raise ValueError(
            f"{op}: algebra {algebra!r} is not shipped; this stratum carries "
            f"{AFFINE_ALGEBRAS} (algebra-scope law; a guard that fires is "
            f"evidence)")
    return _AFFINE_STRATA[algebra]


def _check_level(op: str, level: Any) -> int:
    """A level is a plain non-negative int — ``bool`` REJECTED, because
    ``True == 1`` would otherwise ride the integer lane silently."""
    if not isinstance(level, int) or isinstance(level, bool):
        raise ValueError(
            f"{op}: level carries a {type(level).__name__}; a level is a "
            f"plain int (plain-int law)")
    if level < 0:
        raise ValueError(
            f"{op}: level = {level} is negative; a level is a non-negative "
            f"integer (level law; a guard that fires is evidence)")
    return level


def _check_affine_weight(op: str, stratum: Dict[str, Any],
                         weight: Sequence[int], what: str) -> Tuple[int, ...]:
    """Validate a Dynkin label of the right RANK.  Unlike
    :func:`_check_label` this does NOT require non-negativity — feeding a
    non-dominant weight to the fold is the whole point of the fold."""
    values = list(weight)
    rank = stratum["rank"]
    if len(values) != rank:
        raise ValueError(
            f"{op}: {what} for {stratum['name']} is a length-{rank} Dynkin "
            f"label; got {len(values)} coordinate(s) (label-shape law)")
    for index, value in enumerate(values):
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(
                f"{op}: {what}[{index}] carries a {type(value).__name__}; "
                f"Dynkin labels are plain ints (plain-int law)")
    return tuple(values)


def _require_integrable(op: str, stratum: Dict[str, Any],
                        label: Tuple[int, ...], level: int,
                        what: str) -> None:
    """Refuse a NON-INTEGRABLE fusion operand UP FRONT.

    ⚠️ This guard is load-bearing and is not a formality.  Measured
    before it existed: of four non-integrable operand pairs fed to the
    fusion op, two raised on the downstream negative-coefficient
    backstop and **two returned an empty constituent set SILENTLY** — a
    well-formed wrong answer of exactly the class this module's
    non-negativity guard exists to stop.  The backstop is therefore NOT
    a sufficient check, and the domain is tested here instead."""
    if any(value < 0 for value in label):
        raise ValueError(
            f"{op}: {what} = {label} has a negative Dynkin label; a fusion "
            f"operand is a DOMINANT weight (dominance law; a guard that "
            f"fires is evidence)")
    height = sum(m * v for m, v in zip(stratum["marks"], label))
    if height > level:
        raise ValueError(
            f"{op}: {what} = {label} has level {height} > {level}; a fusion "
            f"operand must be INTEGRABLE at the level it is fused at "
            f"(integrability law; a guard that fires is evidence)")


def _has_monovariant(stratum: Dict[str, Any]) -> bool:
    """Does this algebra's affine Dynkin diagram admit the monovariant
    collapse the fold's termination certificate rests on?

    TRUE exactly when every affine node is adjacent to every other with
    the SAME off-diagonal ``-c`` and ``sum_j C_0j^2 == 2·(2 + c)``.  That
    is the single SSoT of the fold's scope: :func:`_monovariant_quantum`
    raises on the negation of this predicate, and
    :data:`AFFINE_FOLD_ALGEBRAS` is derived by evaluating it, so the
    documented scope cannot drift from the proved one."""
    row = stratum["affine_cartan"][0]
    off = -row[1]
    return (sum(value * value for value in row) == 2 * (2 + off)
            and all(value == -off for value in row[1:]))


def _monovariant_quantum(op: str, stratum: Dict[str, Any],
                         kappa: int) -> int:
    """The EXACT per-step drop coefficient of the fold's monovariant, and
    the enforcement point of the termination scope.

    Derivation, carried rather than recalled.  A step at node ``i``
    sends ``a_j -> a_j - a_i·C_ij``, so

        dQ = -2·a_i·(sum_j a_j·C_ij) + a_i^2·(sum_j C_ij^2).

    When every OTHER node is adjacent to ``i`` with the same off-diagonal
    ``-c``, the constraint ``sum_j a_j == kappa`` (all comarks 1) gives
    ``sum_j a_j·C_ij = (2 + c)·a_i - c·kappa``, and the ``a_i^2`` terms
    cancel exactly when ``sum_j C_ij^2 == 2·(2 + c)``.  What survives is

        dQ = 2·c·kappa·a_i,

    which is ``2·kappa`` for A2 (``c = 1``) and ``4·kappa`` for A1
    (``c = 2``).  Since a step fires only when ``a_i < 0``, dQ is
    strictly negative and quantised at ``>= quantum`` per step.

    ⚠️ The cancellation identity is CHECKED, not assumed.  For D4 (and
    for every ``A_n`` with ``n >= 3``) the affine diagram is not
    complete, ``sum_j C_ij^2 != 2·(2 + c)``, and this function RAISES —
    which is how the fold refuses an algebra it cannot prove it
    terminates on, instead of looping."""
    if not _has_monovariant(stratum):
        raise ValueError(
            f"{op}: {stratum['name']} has no monovariant quantum - its "
            f"affine Dynkin diagram is not complete, so the termination "
            f"certificate of the alcove fold does not carry, and a fold with "
            f"no termination proof is a different object rather than a "
            f"slower one.  This stratum folds {AFFINE_FOLD_ALGEBRAS} only; "
            f"reach for verlinde_fusion_multiplicities, which runs no fold "
            f"(termination-scope law; a guard that fires is evidence)")
    return 2 * (-stratum["affine_cartan"][0][1]) * kappa


#: The algebras whose alcove fold carries a termination certificate —
#: **DERIVED** by evaluating :func:`_has_monovariant` on each shipped
#: stratum, never transcribed.  ``affine_modular_s_matrix`` and
#: ``verlinde_fusion_multiplicities`` are NOT restricted to these,
#: because neither runs the fold.
#:
#: This constant is documentation and introspection ONLY.  The ops do
#: not gate on it — they call :func:`_monovariant_quantum`, whose raise
#: IS the refusal — so a caller asking for D4 gets the termination
#: reason rather than a lookup miss, and the guard is one a real public
#: call can fire.
AFFINE_FOLD_ALGEBRAS: Tuple[str, ...] = tuple(
    name for name in AFFINE_ALGEBRAS
    if _has_monovariant(_AFFINE_STRATA[name]))


def _affine_labels(stratum: Dict[str, Any], weight: Sequence[int],
                   kappa: int) -> List[int]:
    """The affine Dynkin labels ``(a_0, a_1, ..., a_r)`` of a weight at
    ``kappa``, with ``a_0`` the affine slot making
    ``sum_j comark_j·a_j == kappa``."""
    height = sum(m * v for m, v in zip(stratum["marks"], weight))
    return [kappa - height] + list(weight)


def _fold_affine_labels(op: str, stratum: Dict[str, Any],
                        labels: List[int], kappa: int
                        ) -> Dict[str, Any]:
    """THE ITERATIVE SIGNED FOLD — the heart of this stratum.

    Applies ``s_i: a_j -> a_j - a_i·C^aff_ij`` at the first negative
    node until none is negative, carrying the ``+-1`` determinant ledger
    (each generator is a reflection, so the sign flips once per step).
    Three laws are checked on EVERY step, each a raise: the monovariant
    law ``dQ == quantum·a_i``, the level law ``sum comark_j·a_j ==
    kappa``, and the step BOUND computed before the loop from
    ``Q >= kappa^2/(r+1)``.

    Returns the affine labels, the sign, and the loop's own telemetry.  A
    zero anywhere in the result means the weight sits ON a wall of the
    alcove — it is fixed by a reflection and contributes exactly zero, a
    Class-K pin at the phase boundary rather than a defect."""
    rank = stratum["rank"]
    affine = stratum["affine_cartan"]
    comarks = stratum["comarks"]
    quantum = _monovariant_quantum(op, stratum, kappa)
    q_initial = sum(value * value for value in labels)
    bound = _exact_div_floor(q_initial - kappa * kappa // (rank + 1),
                             quantum) + 1
    sign = 1
    steps = 0
    while True:
        node = None
        for index in range(rank + 1):
            if labels[index] < 0:
                node = index
                break
        if node is None:
            break
        pivot = labels[node]
        before = sum(value * value for value in labels)
        labels = [labels[j] - pivot * affine[node][j]
                  for j in range(rank + 1)]
        after = sum(value * value for value in labels)
        if after - before != quantum * pivot:
            raise ValueError(
                f"{op}: the fold step at node {node} moved the monovariant "
                f"by {after - before}, not the derived {quantum * pivot} - "
                f"the termination certificate does not hold (monovariant "
                f"law; a guard that fires is evidence)")
        level_sum = sum(m * v for m, v in zip(comarks, labels))
        if level_sum != kappa:
            raise ValueError(
                f"{op}: the fold step at node {node} moved the level to "
                f"{level_sum}, not {kappa} - the affine Weyl group preserves "
                f"the level (level law; a guard that fires is evidence)")
        sign = -sign
        steps += 1
        if steps > bound:
            raise ValueError(
                f"{op}: the fold ran {steps} steps against a pre-computed "
                f"bound of {bound} - the termination certificate does not "
                f"hold (step-bound law; a guard that fires is evidence)")
    return {
        "labels": tuple(labels),
        "sign": sign,
        "steps": steps,
        "step_bound": bound,
        "q_initial": q_initial,
        "q_final": sum(value * value for value in labels),
        "quantum": quantum,
    }


def _exact_div_floor(numerator: int, denominator: int) -> int:
    """Floor division for the step BOUND only — a bound is an inequality,
    not an exact lattice quantity, so :func:`_exact_div` (which raises on
    a remainder) is the wrong instrument here and using it would refuse
    perfectly good inputs.  Named separately so the distinction is
    visible rather than inferred from a ``//``."""
    return numerator // denominator


def _affine_procedure_bytes(stratum: Dict[str, Any]) -> bytes:
    """The canonical serialisation of the AFFINE derivation procedure —
    everything a second rc would have to match to share an address."""
    parts: List[str] = [
        stratum["name"],
        "simple_roots=" + ";".join(",".join(str(v) for v in root)
                                   for root in stratum["roots"]),
        "cartan=" + ";".join(",".join(str(v) for v in row)
                             for row in stratum["cartan"]),
        "affine_cartan=" + ";".join(",".join(str(v) for v in row)
                                    for row in stratum["affine_cartan"]),
        "theta=" + ",".join(str(v) for v in stratum["theta"]),
        "marks=" + ",".join(str(v) for v in stratum["marks"]),
        "h_vee=" + str(stratum["h_vee"]),
        "denominator=" + str(stratum["denominator"]),
        "scaled_weights=" + ";".join(",".join(str(v) for v in weight)
                                     for weight in stratum["scaled_weights"]),
        "centre=" + ",".join(str(v)
                             for v in stratum["centre_invariant_factors"]),
        "fold=iterative_signed_alcove_fold_monovariant_sum_of_squares",
        "fusion=kac_walton_level_truncated_racah_speiser",
        "s_matrix=kac_peterson_finite_weyl_sum_over_z_zeta",
    ]
    return "\n".join(parts).encode("utf-8")


def _affine_procedure_sha256(stratum: Dict[str, Any]) -> str:
    """The Class-A content address of the affine derivation procedure."""
    return sha256_bytes(_affine_procedure_bytes(stratum))


def _integrable_labels(stratum: Dict[str, Any],
                       level: int) -> Tuple[Tuple[int, ...], ...]:
    """Every dominant label with ``sum marks_j·label_j <= level``.

    Walks the SIMPLEX directly rather than filtering a ``(level+1)^rank``
    box.  The box is the obvious spelling and it is the wrong shape: at
    D4 level 72 it visits 73^4 = 28,398,241 tuples to keep roughly 2% of
    them, and the answer is the same set either way — so the box is pure
    waste that grows as the fourth power of a caller-supplied integer.
    The recursion below never visits a label it will not return."""
    marks = stratum["marks"]

    def walk(index: int, remaining: int) -> List[Tuple[int, ...]]:
        if index == len(marks):
            return [()]
        out: List[Tuple[int, ...]] = []
        mark = marks[index]
        value = 0
        while mark * value <= remaining:
            for tail in walk(index + 1, remaining - mark * value):
                out.append((value,) + tail)
            value += 1
        return out

    return tuple(sorted(walk(0, level)))


@lru_cache(maxsize=32)
def _ambient_weyl(algebra: str) -> Tuple[Tuple[Tuple[Tuple[int, ...], ...],
                                               int], ...]:
    """The FINITE Weyl group as ``(matrix, determinant)`` pairs, by
    closure from the simple reflections ``(R_i)_ab = delta_ab -
    alpha_ia·alpha_ib``.  Cached because D4's has 192 elements and the
    S-matrix asks for it once per level.

    Determinants go through :class:`~srmech.math.qmat.QMat` — the sign of
    a Weyl element IS its determinant, so this is the ``+-1`` ledger's
    SOURCE for the Kac-Peterson sum, exactly as
    :func:`_int_determinant` is for the classical fold."""
    stratum = _AFFINE_STRATA[algebra]
    roots = stratum["roots"]
    size = len(roots[0])
    generators = [
        tuple(tuple((1 if i == j else 0) - root[i] * root[j]
                    for j in range(size)) for i in range(size))
        for root in roots
    ]
    identity = tuple(tuple(1 if i == j else 0 for j in range(size))
                     for i in range(size))
    elements = {identity}
    frontier = [identity]
    while frontier:
        current = frontier.pop()
        for generator in generators:
            product = tuple(
                tuple(sum(generator[i][t] * current[t][j] for t in range(size))
                      for j in range(size)) for i in range(size))
            if product not in elements:
                elements.add(product)
                frontier.append(product)
    out = []
    for matrix in sorted(elements):
        value = QMat([list(row) for row in matrix]).det()
        if value.denominator != 1 or value.numerator not in (-1, 1):
            raise ValueError(
                f"weight_lattice: Weyl element {matrix} of {algebra} has "
                f"determinant {value.numerator}/{value.denominator}, not "
                f"+-1 - a Weyl element is a lattice isometry (Weyl-sign law; "
                f"a guard that fires is evidence)")
        out.append((matrix, value.numerator))
    return tuple(out)


def _zeta_conjugate(vector: Sequence[int], order: int,
                    phi: Sequence[int]) -> Tuple[int, ...]:
    """Complex conjugation on ``Z[zeta_order]`` — the Galois map
    ``zeta -> zeta^-1``, spelled as a cyclic index reversal in the power
    basis (Class I) and reduced with the shipped
    :func:`srmech.math.groups.zeta_mul`.  No machinery, no float, and no
    conjugation table: the same move ``character_table`` documents as a
    column permutation, one rung lower."""
    accumulator = [0] * order
    for power, coefficient in enumerate(vector):
        accumulator[(-power) % order] += coefficient
    return zeta_mul(accumulator, (1,), phi)


@lru_cache(maxsize=16)
def _s_matrix_core(algebra: str, level: int) -> Dict[str, Any]:
    """The Kac-Peterson numerator, its ring, and the normalisation —
    cached, because :func:`verlinde_fusion_multiplicities` asks for the
    same object once per operand pair.

    The sum is ``A_lm = sum_{w in W} det(w)·zeta^(-(w·Lambda, M))`` over
    the FINITE Weyl group, with ``Lambda = D·(lambda + rho)`` integer in
    the scaled ambient basis.  The root-of-unity order starts at
    ``kappa·D^2`` and is then REDUCED by the gcd of the exponents
    actually used — which is how D4 level 1 lands in ``Z[zeta_14]``
    rather than the ``Z[zeta_28]`` the raw scaling suggests.  That
    reduction is a measurement, not a convention.

    The normalisation is DERIVED, not recalled: ``A·A^dagger`` is
    computed and must be ``n·I``; then ``|c|^2 = 1/n``.  The off-diagonal
    vanishing is the unitarity law and is a raise."""
    stratum = _AFFINE_STRATA[algebra]
    kappa = level + stratum["h_vee"]
    denominator = stratum["denominator"]
    scaled_weights = stratum["scaled_weights"]
    scaled_rho = stratum["scaled_rho"]
    primaries = _integrable_labels(stratum, level)
    weyl = _ambient_weyl(algebra)
    size = len(scaled_rho)

    shifted = {}
    for label in primaries:
        vector = list(scaled_rho)
        for j, coefficient in enumerate(label):
            for t in range(size):
                vector[t] += coefficient * scaled_weights[j][t]
        shifted[label] = tuple(vector)

    raw_order = kappa * denominator * denominator
    exponents: Dict[Tuple[Tuple[int, ...], Tuple[int, ...]],
                    List[Tuple[int, int]]] = {}
    common = raw_order
    for left in primaries:
        images = [(sign, tuple(sum(matrix[i][t] * shifted[left][t]
                                   for t in range(size))
                               for i in range(size)))
                  for matrix, sign in weyl]
        for right in primaries:
            terms = [(sign, (-_ambient_dot(image, shifted[right])) % raw_order)
                     for sign, image in images]
            exponents[(left, right)] = terms
            for _, power in terms:
                common = gcd(common, power)
    order = _exact_div("affine_modular_s_matrix", raw_order, common,
                       "the reduced root-of-unity order")
    phi = tuple(cyclotomic_polynomial(order)["coefficients"])

    numerator: Dict[Tuple[Tuple[int, ...], Tuple[int, ...]],
                    Tuple[int, ...]] = {}
    for key, terms in exponents.items():
        accumulator = [0] * order
        for sign, power in terms:
            reduced = _exact_div("affine_modular_s_matrix", power, common,
                                 "a Kac-Peterson exponent")
            accumulator[reduced % order] += sign
        numerator[key] = zeta_mul(accumulator, (1,), phi)

    width = len(phi) - 1
    scale = None
    for left in primaries:
        for right in primaries:
            accumulator = tuple([0] * width)
            for middle in primaries:
                product = zeta_mul(
                    numerator[(left, middle)],
                    _zeta_conjugate(numerator[(right, middle)], order, phi),
                    phi)
                accumulator = tuple(x + y
                                    for x, y in zip(accumulator, product))
            if left == right:
                if any(value != 0 for value in accumulator[1:]):
                    raise ValueError(
                        f"affine_modular_s_matrix: the {algebra} level-"
                        f"{level} diagonal of A·A^dagger is the non-rational "
                        f"{accumulator} - unitarity makes it a rational "
                        f"scalar (unitarity law; a guard that fires is "
                        f"evidence)")
                if scale is None:
                    scale = accumulator[0]
                elif scale != accumulator[0]:
                    raise ValueError(
                        f"affine_modular_s_matrix: A·A^dagger is not a "
                        f"SCALAR on the diagonal ({scale} then "
                        f"{accumulator[0]}) - unitarity law; a guard that "
                        f"fires is evidence")
            elif any(value != 0 for value in accumulator):
                raise ValueError(
                    f"affine_modular_s_matrix: the {algebra} level-{level} "
                    f"off-diagonal A·A^dagger[{left}][{right}] is "
                    f"{accumulator}, not zero - unitarity law; a guard that "
                    f"fires is evidence")
    return {
        "stratum": stratum,
        "kappa": kappa,
        "primaries": primaries,
        "order": order,
        "phi": phi,
        "numerator": numerator,
        "weyl_order": len(weyl),
        "raw_order": raw_order,
        "gcd": common,
        "scale_squared_denominator": scale,
    }


def integrable_weights(algebra: str, level: int) -> Dict[str, Any]:
    """The LEVEL-TRUNCATED dominant stratum — every weight ``lambda``
    with ``sum_j mark_j·lambda_j <= level``, which is exactly the set of
    integrable highest weights of the affine algebra at that level.
    **Class E**, the catalog enumeration, with a Class-K stage (the
    level inequality IS a wall test) and Class A (the address).

    This is the index set every other op in the affine stratum is
    indexed BY: the primaries of the theory, the rows and columns of
    :func:`affine_modular_s_matrix`, and the legal operands of
    :func:`affine_fusion_multiplicities`.

    The MARKS are derived, never recalled.  ``theta`` is located as the
    root of maximal height in the derived root system, expanded over the
    simple roots in exact integers, and ``h^vee = 1 + sum(marks)`` is
    cross-checked against the independent ``|Delta| / rank`` count that
    holds for a simply-laced algebra — a raise if they disagree.  For D4
    the marks come out ``(1, 2, 1, 1)``, which is why level 1 has FOUR
    primaries and not five: the node with mark 2 cannot be excited.

    Args:
        algebra: one of ``"A1"``, ``"A2"``, ``"D4"``.
        level: a non-negative int.

    Returns:
        ``{"algebra", "level", "kappa"`` (``= level + h^vee``),
        ``"rank", "marks", "h_vee", "weights"`` (a tuple of label
        tuples, sorted), ``"n_weights", "centre_invariant_factors"``
        (the ``P/Q`` decomposition off the Cartan matrix's Smith normal
        form), ``"procedure_sha256", "weights_sha256"}``.

    Worked example: ``integrable_weights("D4", 1)["weights"]`` returns
    the four level-1 primaries, and their count is ``|P/Q| = 4`` — the
    order of the centre, which the payload also carries as
    ``centre_invariant_factors == (2, 2)``.  That coincidence is not one:
    at level 1 the primaries ARE a torsor over the centre.

    C-parity (ADR-0009, recorded): no C peer; Python-first under the
    noted-disparity ruling, the same sentence the classical stratum
    carries.

    Note:
        Exact integers; no float; no ``abs`` — the one magnitude read is
        the named Class-K :func:`_magnitude` inside the Smith normal
        form.
    """
    op = "integrable_weights"
    stratum = _affine_stratum(op, algebra)
    checked = _check_level(op, level)
    weights = _integrable_labels(stratum, checked)
    body = ";".join(",".join(str(v) for v in label)
                    for label in weights).encode("utf-8")
    return {
        "algebra": stratum["name"],
        "level": checked,
        "kappa": checked + stratum["h_vee"],
        "rank": stratum["rank"],
        "marks": stratum["marks"],
        "h_vee": stratum["h_vee"],
        "weights": weights,
        "n_weights": len(weights),
        "centre_invariant_factors": stratum["centre_invariant_factors"],
        "procedure_sha256": _affine_procedure_sha256(stratum),
        "weights_sha256": sha256_bytes(body),
    }


def alcove_fold(algebra: str, weight: Sequence[int],
                level: int) -> Dict[str, Any]:
    """The ITERATIVE SIGNED FOLD of a weight into the level-``k`` alcove
    under the affine Weyl DOT action ``w-hat · nu = w-hat(nu + rho) -
    rho`` — **Class K** primary (the ``+-1`` ledger at the affine wall),
    with Class C (which node, which direction) and Class N (the guards).

    THE POINT OF THIS OP, stated as the thing it replaces.  The classical
    fold above enumerates: ``_WEYL`` is a precomputed 6-tuple and
    :func:`_strictly_dominant_fold` scans it.  The AFFINE Weyl group is
    INFINITE, so enumeration cannot survive — and an unbounded loop whose
    termination is an assumption is exactly what
    :func:`_dominant_conjugate` refuses to be.  This op is the third
    option: an iterative fold carrying an EXACT INTEGER TERMINATION
    CERTIFICATE.

    THE CERTIFICATE, and it is checked rather than claimed.  The
    monovariant is ``Q(a) = sum_j a_j^2`` over the affine labels.  Each
    step drops it by EXACTLY ``quantum·a_i`` — ``2·kappa`` for A2,
    ``4·kappa`` for A1, both DERIVED in :func:`_monovariant_quantum` from
    the affine Cartan matrix — and a step fires only when ``a_i < 0``, so
    the drop is strictly negative and integer-quantised.  ``Q`` is
    bounded below by ``kappa^2/(r+1)`` on the constraint simplex, so a
    step BOUND is computed BEFORE the loop and asserted against inside
    it.  The per-step law is checked on EVERY step, not once: measured
    over ``[-30, 30]^rank`` at ``k = 0..8`` (34,038 folds), the fold
    takes at most 40 steps against bounds up to 901 and never approaches
    one.  Both extremes are attained at the same corner, ``A2`` weight
    ``(-30, -30)`` at level 0, and :func:`alcove_fold`'s gate PINS that
    witness — through rc461 this sentence read *"bounds up to 962"*, a
    number the shipped op never produces anywhere in the swept domain,
    and no gate could see it because the sweep asserted only
    ``steps < bound`` and never a bound VALUE.

    ⚠️ **A1 AND A2 ONLY, and the code enforces it.**  The quantum
    collapse needs every affine node adjacent to every other; D4's is a
    star, the identity fails, and :func:`_monovariant_quantum` RAISES.
    That refusal is deliberate — a fold with no termination proof is not
    a slower fold, it is a different object.  For D4, reach for
    :func:`verlinde_fusion_multiplicities`, which runs no fold at all.

    Args:
        algebra: ``"A1"`` or ``"A2"``.
        weight: a rank-length Dynkin label.  It does NOT have to be
            dominant or integrable — folding a weight that is neither is
            the operation.
        level: a non-negative int.

    Returns:
        ``{"algebra", "level", "kappa", "weight", "affine_labels"`` (the
        shifted input labels), ``"on_wall"`` (a bool FIELD, not an
        inferred one), ``"folded"`` (the label, or ``None`` on a wall),
        ``"sign"`` (``+1`` / ``-1`` / ``0``, and ``0`` ONLY on a wall —
        it is a ledger entry, never a count), ``"steps", "step_bound",
        "q_initial", "q_final", "monovariant_quantum",
        "procedure_sha256"}``.

    Worked example: ``alcove_fold("A2", (2, 2), 2)`` folds the classical
    ``(2,2)`` constituent of ``8 (x) 8`` in ONE step to ``(1, 1)`` with
    sign ``-1``, and ``Q`` falls 19 -> 9, a drop of 10 that is exactly
    ``quantum·a_0 = 10·(-1)``.

    ⚠️ **TWO mechanisms carry ``1 + 8 + 8 + 10 + 10-bar + 27`` down to
    the level-2 ``1 + 8``, not one**, and per-constituent measurement is
    what separates them — through rc461 this paragraph credited only the
    step.  The ``10`` and ``10-bar`` are removed by the WALL TEST:
    ``on_wall=True``, ``sign=0``, ``steps=0`` — no step is taken and no
    sign is applied, they simply contribute zero.  The single signed step
    acts on ``27`` ALONE, folding it onto ``(1,1)`` with sign ``-1``,
    which cancels one of the two copies of ``8``.  Deleting the walls and
    stopping there leaves ``{(0,0): 1, (1,1): 2, (2,2): 1}``; it is the
    signed step that turns the remaining ``2`` into the ``1`` the affine
    answer reports.  Both are load-bearing and they are different
    operations.

    C-parity (ADR-0009, recorded): no C peer; Python-first under the
    noted-disparity ruling.

    Note:
        Exact integers; no float; no ``abs`` — the sign is the explicit
        Class-K reflection ledger, flipped once per step.
    """
    op = "alcove_fold"
    stratum = _affine_stratum(op, algebra)
    _require_foldable(op, stratum)
    checked = _check_level(op, level)
    label = _check_affine_weight(op, stratum, weight, "weight")
    kappa = checked + stratum["h_vee"]
    shifted = tuple(value + 1 for value in label)
    labels = _affine_labels(stratum, shifted, kappa)
    result = _fold_affine_labels(op, stratum, list(labels), kappa)
    on_wall = any(value == 0 for value in result["labels"])
    folded = None if on_wall else tuple(value - 1
                                        for value in result["labels"][1:])
    return {
        "algebra": stratum["name"],
        "level": checked,
        "kappa": kappa,
        "weight": label,
        "affine_labels": tuple(labels),
        "on_wall": on_wall,
        "folded": folded,
        "sign": 0 if on_wall else result["sign"],
        "steps": result["steps"],
        "step_bound": result["step_bound"],
        "q_initial": result["q_initial"],
        "q_final": result["q_final"],
        "monovariant_quantum": result["quantum"],
        "procedure_sha256": _affine_procedure_sha256(stratum),
    }


def _classical_ledger(op: str, stratum: Dict[str, Any],
                      a: Tuple[int, ...], b: Tuple[int, ...]
                      ) -> Dict[Tuple[int, ...], int]:
    """The CLASSICAL tensor-product multiplicities, as the Kac-Walton
    operand.  A2 delegates to the shipped
    :func:`tensor_product_multiplicities` — one SSoT, so the affine
    answer cannot disagree with the classical one by construction.  A1
    runs the same Racah-Speiser instrument over its own weight system,
    which is a single string of ``q + 1`` weights each once; the string
    length is checked against ``dim V_q = q + 1`` rather than asserted."""
    if stratum["name"] == "A2":
        classical = tensor_product_multiplicities(a, b)
        return {(p, q): m for p, q, m in classical["constituents"]}
    if stratum["name"] == "A1":
        top = b[0]
        system = [top - 2 * i for i in range(top + 1)]
        if len(system) != top + 1:
            raise ValueError(
                f"{op}: the A1 weight system of V_{top} has {len(system)} "
                f"weights, not dim = {top + 1} (dimension law; a guard that "
                f"fires is evidence)")
        ledger: Dict[Tuple[int, ...], int] = {}
        for mu in system:
            translate = a[0] + 1 + mu
            if translate == 0:
                continue                # Class-K pin: the wall contributes 0
            if translate > 0:
                key = (translate - 1,)
                ledger[key] = ledger.get(key, 0) + 1
            else:
                key = (-translate - 1,)
                ledger[key] = ledger.get(key, 0) - 1
        return {k: v for k, v in ledger.items() if v != 0}
    raise ValueError(
        f"{op}: {stratum['name']} has no classical tensor-product operand in "
        f"this module (classical-operand law; a guard that fires is "
        f"evidence)")


def _fusion_payload(op: str, stratum: Dict[str, Any], level: int,
                    a: Tuple[int, ...], b: Tuple[int, ...],
                    ledger: Dict[Tuple[int, ...], int],
                    extra: Dict[str, Any]) -> Dict[str, Any]:
    """The shared payload shape of the two fusion routes, so the co-equal
    constructions are comparable field-for-field and a caller can swap
    one for the other without reshaping anything."""
    constituents = []
    for label in sorted(ledger):
        multiplicity = ledger[label]
        if multiplicity == 0:
            continue
        if multiplicity < 0:
            raise ValueError(
                f"{op}: constituent {label} survives with multiplicity "
                f"{multiplicity} - a fusion coefficient counts channels "
                f"(non-negativity law; a guard that fires is evidence)")
        constituents.append((label, multiplicity))
    vacuum = tuple([0] * stratum["rank"])
    body = ";".join(f"{','.join(str(v) for v in label)}|{m}"
                    for label, m in constituents).encode("utf-8")
    payload = {
        "algebra": stratum["name"],
        "level": level,
        "kappa": level + stratum["h_vee"],
        "a": a,
        "b": b,
        "constituents": tuple(constituents),
        "n_constituents": len(constituents),
        "singlet_multiplicity": ledger.get(vacuum, 0),
        "procedure_sha256": _affine_procedure_sha256(stratum),
        "fusion_sha256": sha256_bytes(body),
    }
    payload.update(extra)
    return payload


def affine_fusion_multiplicities(algebra: str, a: Sequence[int],
                                 b: Sequence[int],
                                 level: int) -> Dict[str, Any]:
    """The LEVEL-TRUNCATED fusion multiplicities by **Kac-Walton** —
    ``N^(k)_ab{}^c = sum_{w-hat} det(w-hat)·N_ab^{w-hat · c}`` — as a
    SIGNED INTEGER COUNT.  **Class K** primary, the ``+-1`` ledger at the
    affine wall, with Class E (the classical operand's enumeration),
    Class C (fold direction) and Class N (the guards).

    THE INSTRUMENT, stated as the count it is: take the CLASSICAL
    constituents of ``V_a (x) V_b``, fold each one into the level-``k``
    alcove under the affine dot action carrying its ``+-1`` sign, drop
    the ones that land on a wall (they contribute exactly zero), and
    accumulate.  There is no integral, no measure and no float in that
    sentence — it is the classical Racah-Speiser count of
    :func:`tensor_product_multiplicities` with ONE extra reflection
    available, the affine ``s_0``.

    ⚠️ **NAME NOTE, and it is not cosmetic.** This op is deliberately NOT
    called ``fusion_multiplicities``: that name is taken by
    :func:`srmech.math.groups.fusion_multiplicities`, the FINITE-GROUP
    fusion tensor ``N_abc = <chi_a·chi_b, chi_c>``, which is **Class L**
    because it contracts against the class-algebra eigenbasis.  This op
    builds no eigenbasis and projects onto nothing — the same explicit
    non-claim :func:`tensor_product_multiplicities` carries, inherited
    here because this op is that one's level-truncated form.  The two
    objects DO coincide in one place (a level-1 simply-laced theory's
    fusion ring is the group ring of the centre, which is why the D4
    acceptance test exists), but coincidence in one case is not identity.

    ⚠️ **NON-INTEGRABLE OPERANDS RAISE, and that guard is load-bearing.**
    Measured before it existed: of four non-integrable pairs, two raised
    on the downstream non-negativity backstop and **two returned an empty
    constituent set silently**.  The backstop is not sufficient; the
    domain is checked up front.

    ⚠️ **A1 AND A2 ONLY** — it runs :func:`alcove_fold`, so it inherits
    that op's termination scope exactly.  For D4 reach for
    :func:`verlinde_fusion_multiplicities`.

    Args:
        algebra: ``"A1"`` or ``"A2"``.
        a: a dominant label, integrable at ``level``.
        b: likewise.
        level: a non-negative int.

    Returns:
        ``{"algebra", "level", "kappa", "a", "b", "constituents"`` (a
        tuple of ``(label, multiplicity)`` pairs sorted by label),
        ``"n_constituents", "singlet_multiplicity",
        "classical_constituents"`` (the untruncated operand, so the
        truncation is visible on the payload face), ``"n_truncated"``,
        ``"route"`` (``"kac_walton"``), ``"procedure_sha256",
        "fusion_sha256"}``.

    Worked example: ``affine_fusion_multiplicities("A2", (1,1), (1,1),
    2)`` returns ``(((0,0), 1), ((1,1), 1))`` — the su(3) level-2 statement
    ``8 (x) 8 = 1 + 8``, where the CLASSICAL answer is ``1 + 8 + 8 + 10 +
    10-bar + 27``.  The ``10`` and ``10-bar`` land on walls and vanish;
    the ``27`` folds back onto the ``8`` with sign ``-1`` and cancels one
    of its two copies.  Every one of those three fates is readable off
    ``alcove_fold`` individually.

    C-parity (ADR-0009, recorded): no C peer; Python-first under the
    noted-disparity ruling.

    Note:
        Exact integers; no float; no ``abs`` — the sign-handling is the
        Class-K affine reflection ledger with Class-C re-application on
        the folded label.
    """
    op = "affine_fusion_multiplicities"
    stratum = _affine_stratum(op, algebra)
    _require_foldable(op, stratum)
    checked = _check_level(op, level)
    label_a = _check_affine_weight(op, stratum, a, "a")
    label_b = _check_affine_weight(op, stratum, b, "b")
    _require_integrable(op, stratum, label_a, checked, "a")
    _require_integrable(op, stratum, label_b, checked, "b")
    classical = _classical_ledger(op, stratum, label_a, label_b)
    ledger: Dict[Tuple[int, ...], int] = {}
    truncated = 0
    for label, multiplicity in classical.items():
        folded = alcove_fold(stratum["name"], label, checked)
        if folded["on_wall"]:
            truncated += 1
            continue
        if folded["folded"] != label:
            truncated += 1
        key = folded["folded"]
        ledger[key] = ledger.get(key, 0) + folded["sign"] * multiplicity
    return _fusion_payload(
        op, stratum, checked, label_a, label_b, ledger,
        {"classical_constituents": tuple(
            (label, classical[label]) for label in sorted(classical)),
         "n_truncated": truncated,
         "route": "kac_walton"})


def affine_modular_s_matrix(algebra: str, level: int) -> Dict[str, Any]:
    """The **Kac-Peterson modular S-matrix** of the level-``k`` theory,
    EXACT over ``Z[zeta_e]`` — **Class I** primary (the cyclotomic
    ``zeta``-power arithmetic, the same ring
    :func:`srmech.math.groups.zeta_mul` is Class I for), with Class E
    (the finite Weyl enumeration), Class C (the ``+-1`` determinant
    ledger) and Class A (the address).

    ``S = c·A`` with ``A_lm = sum_{w in W} det(w)·zeta^(-(w(l+rho),
    m+rho))`` a FINITE sum over the ordinary Weyl group.  This op ships
    ``A`` — an integer matrix over ``Z[zeta_e]`` — plus the integer ``n``
    with ``|c|^2 = 1/n``, rather than a float matrix, because every
    quantity in it is exact and rendering it as a float would be the
    continuum shadow of an integer object.

    ⚠️ **EXPLICIT NON-CLAIM: this op is NOT Class L.**  It performs no
    spectral decomposition and builds no eigenbasis.  That ``S``
    diagonalises the fusion algebra is a THEOREM ABOUT it (and the one
    :func:`verlinde_fusion_multiplicities` uses), not an operation it
    runs — claiming L here would assert an instrument the op never
    executes.

    THREE THINGS ARE DERIVED THAT ARE USUALLY RECALLED.
    (1) ``h^vee``, from the marks of the derived highest root, cross-checked
    against ``|Delta|/rank``.  (2) The ring.  The exponents start over
    ``kappa·D^2`` and the order is REDUCED by their gcd — D4 level 1
    lands in ``Z[zeta_14]``, not the ``Z[zeta_28]`` the raw scaling
    suggests and not the ``Z[zeta_7]`` a reading of ``kappa`` alone
    suggests; the spinor weights are half-integral and the measurement
    says so.  (3) The normalisation.  ``A·A^dagger`` is COMPUTED and must
    be ``n·I``; ``|c|^2 = 1/n`` falls out of unitarity.  Measured, it
    equals ``kappa^rank·|P/Q|`` in every shipped case — but it is read
    off the matrix, not substituted from that formula, so the formula is
    a cross-check and not an input.

    Carried for ALL THREE algebras including D4: this is a finite Weyl
    sum with no fold, so the termination scope that binds
    :func:`alcove_fold` does not apply.

    Args:
        algebra: ``"A1"``, ``"A2"`` or ``"D4"``.
        level: a non-negative int.

    Returns:
        ``{"algebra", "level", "kappa", "primaries", "n_primaries",
        "weyl_order", "zeta_order", "phi_e"`` (the monic ``Phi_e``, the
        modulus every value is reduced against — the same field
        ``character_table`` ships), ``"numerator"`` (a tuple of rows of
        ``zeta``-coordinate tuples), ``"scale_squared_denominator"``
        (the ``n`` with ``|c|^2 = 1/n``), ``"is_rational_numerator"``,
        ``"rational_numerator"`` (plain-integer rows when the whole
        matrix is rational, else ``None``), ``"centre_invariant_factors",
        "procedure_sha256", "s_sha256"}``.

    Worked example, and it is the strongest check in this stratum:
    ``affine_modular_s_matrix("D4", 1)`` returns a numerator that is
    rational with every entry ``+-49``, ``scale_squared_denominator ==
    9604 == 98^2``, and ``centre_invariant_factors == (2, 2)``.  Divide
    the numerator by ``49`` and you have ``sqrt(|Z|)·S`` as a ``+-1``
    matrix whose ROWS are the rows of
    ``srmech.math.groups.character_table`` of the Klein four-group,
    BIT-FOR-BIT, once both are put in the same documented ``(degree,
    lexicographic)`` row order.  ⚠️ Without that sort they are NOT equal
    — ``character_table`` sorts its rows and says in its own docstring to
    "locate rows by CONTENT, never by index", while this op orders its
    rows by PRIMARY.  The permutation between them is the row reversal
    ``(3, 2, 1, 0)`` and it is unique.  A claim of raw bit-for-bit
    equality is measurably false and the acceptance gate pins BOTH
    halves so neither can drift.

    Cost, honest: D4 level 1 is milliseconds; D4 level 2 has 11
    primaries against a 192-element Weyl group and takes seconds.  The
    result is cached per ``(algebra, level)``.

    C-parity (ADR-0009, recorded): no C peer; Python-first under the
    noted-disparity ruling.

    Note:
        Exact integers; no float; no ``abs``.  Values ship as the integer
        ``zeta``-coordinate vectors ``character_table`` already mints and
        ``zeta_mul`` already reads — NO new carrier type, so no
        discriminator widens.
    """
    op = "affine_modular_s_matrix"
    stratum = _affine_stratum(op, algebra)
    checked = _check_level(op, level)
    core = _s_matrix_core(stratum["name"], checked)
    primaries = core["primaries"]
    rows = tuple(tuple(core["numerator"][(left, right)]
                       for right in primaries) for left in primaries)
    rational = all(all(value == 0 for value in cell[1:])
                   for row in rows for cell in row)
    body = ";".join("|".join(",".join(str(v) for v in cell) for cell in row)
                    for row in rows).encode("utf-8")
    return {
        "algebra": stratum["name"],
        "level": checked,
        "kappa": core["kappa"],
        "primaries": primaries,
        "n_primaries": len(primaries),
        "weyl_order": core["weyl_order"],
        "zeta_order": core["order"],
        "phi_e": core["phi"],
        "numerator": rows,
        "scale_squared_denominator": core["scale_squared_denominator"],
        "is_rational_numerator": rational,
        "rational_numerator": (
            tuple(tuple(cell[0] for cell in row) for row in rows)
            if rational else None),
        "centre_invariant_factors": stratum["centre_invariant_factors"],
        "procedure_sha256": _affine_procedure_sha256(stratum),
        "s_sha256": sha256_bytes(body),
    }


def verlinde_fusion_multiplicities(algebra: str, a: Sequence[int],
                                   b: Sequence[int],
                                   level: int) -> Dict[str, Any]:
    """The SAME level-truncated fusion multiplicities as
    :func:`affine_fusion_multiplicities`, reached by the **Verlinde**
    route instead — ``N_ab^c = sum_s S_as·S_bs·conj(S_cs)/S_0s``,
    contracted EXACTLY in ``Q(zeta_e)``.  **Class I** primary (the
    cyclotomic contraction), with Class N (the one genuine field
    division, guarded), Class E and Class A.

    WHY BOTH ROUTES SHIP.  They are not two spellings of one op; they are
    two INSTRUMENTS with disjoint failure modes.  Kac-Walton is an
    iterative integer reflection with a termination certificate and never
    leaves ``Z``.  Verlinde is a finite exponential sum over the ordinary
    Weyl group followed by division in a number field.  A co-equal dual
    construction is a CONSISTENCY ORACLE: where they disagree, the
    disagreement is the finding.  Measured across A1 levels 1-4 and A2
    levels 1-3 — 199 operand pairs — they agree on every coefficient,
    with zero mismatches.

    AND THE SCOPES DIFFER, which is the practical reason to have both.
    This route runs NO alcove fold, so the termination proof that binds
    :func:`alcove_fold` to A1 and A2 does not apply: **this op carries
    D4**.  At D4 level 1 it returns the group ring of the centre — every
    product a single primary at multiplicity one, every primary its own
    inverse — which is an independent confirmation that ``P/Q`` is the
    Klein four-group and not the cyclic group of order four.

    EXACTNESS, and where the only division is.  ``|c|^2`` cancels to a
    RATIONAL in the contraction (three factors of ``c`` up, one down,
    leaving ``c·conj(c)``), and it is read off the unitarity of ``A``
    rather than substituted from a formula.  The per-term division by
    ``A_0s`` is the one operation that genuinely needs a field, and it
    goes through :class:`~srmech.math.qalg.Qalg` over ``Phi_e`` — the
    two-line lift :func:`srmech.math.groups.character_table` documents.
    Every coefficient is then checked to be RATIONAL and to have
    denominator 1 before it is returned; a non-integer here is a raise,
    never a rounded result.

    ⚠️ Slower than the Kac-Walton route by a wide margin — it builds the
    whole S-matrix (cached) and contracts over every primary for every
    output label.  Reach for :func:`affine_fusion_multiplicities` when
    you want the answer and for this one when you want the answer
    CHECKED, or when the algebra is D4.

    Args:
        algebra: ``"A1"``, ``"A2"`` or ``"D4"``.
        a: a dominant label, integrable at ``level``.
        b: likewise.
        level: a non-negative int.

    Returns:
        The :func:`affine_fusion_multiplicities` payload shape — so the
        two are comparable field-for-field — with ``"route"`` reading
        ``"verlinde"``, plus ``"zeta_order"``,
        ``"scale_squared_denominator"`` and ``"n_primaries"``.  There is
        no ``classical_constituents`` field: this route never computes
        one.

    Worked example: ``verlinde_fusion_multiplicities("D4", (0,0,0,1),
    (0,0,1,0), 1)["constituents"]`` returns ``(((1,0,0,0), 1),)`` — the
    two spinors fuse to the vector, exactly the Klein-four group law, on
    an algebra the alcove fold refuses.

    C-parity (ADR-0009, recorded): no C peer; Python-first under the
    noted-disparity ruling.

    Note:
        Exact integers and exact ``Q(zeta_e)``; no float; no ``abs``.
    """
    op = "verlinde_fusion_multiplicities"
    stratum = _affine_stratum(op, algebra)
    checked = _check_level(op, level)
    label_a = _check_affine_weight(op, stratum, a, "a")
    label_b = _check_affine_weight(op, stratum, b, "b")
    _require_integrable(op, stratum, label_a, checked, "a")
    _require_integrable(op, stratum, label_b, checked, "b")
    core = _s_matrix_core(stratum["name"], checked)
    primaries = core["primaries"]
    modulus = list(core["phi"])
    order = core["order"]
    numerator = core["numerator"]
    vacuum = tuple([0] * stratum["rank"])

    inverse_vacuum = {}
    for middle in primaries:
        cell = numerator[(vacuum, middle)]
        if not any(cell):
            raise ValueError(
                f"{op}: S_0[{middle}] is zero, so the Verlinde contraction "
                f"would divide by zero - the vacuum row of a modular "
                f"S-matrix has no zero (Verlinde law; a guard that fires is "
                f"evidence)")
        inverse_vacuum[middle] = Qalg(modulus, list(cell)).inverse()

    partial = {}
    for middle in primaries:
        partial[middle] = (Qalg(modulus, list(numerator[(label_a, middle)]))
                           * Qalg(modulus, list(numerator[(label_b, middle)]))
                           * inverse_vacuum[middle])
    scale = Qalg.rational(core["scale_squared_denominator"], modulus)
    ledger: Dict[Tuple[int, ...], int] = {}
    for target in primaries:
        total = Qalg.rational(0, modulus)
        for middle in primaries:
            total = total + partial[middle] * Qalg(
                modulus,
                list(_zeta_conjugate(numerator[(target, middle)], order,
                                     core["phi"])))
        total = total / scale
        if not total.is_rational():
            raise ValueError(
                f"{op}: the Verlinde coefficient at {target} is the "
                f"non-rational {total} - a fusion coefficient is an integer "
                f"(Verlinde-rationality law; a guard that fires is evidence)")
        value = total.as_rational()
        if value.denominator != 1:
            raise ValueError(
                f"{op}: the Verlinde coefficient at {target} is {value}, not "
                f"an integer - a fusion coefficient counts channels "
                f"(integrality law; a guard that fires is evidence)")
        if value.numerator:
            ledger[target] = int(value.numerator)
    return _fusion_payload(
        op, stratum, checked, label_a, label_b, ledger,
        {"route": "verlinde",
         "zeta_order": order,
         "n_primaries": len(primaries),
         "scale_squared_denominator": core["scale_squared_denominator"]})
