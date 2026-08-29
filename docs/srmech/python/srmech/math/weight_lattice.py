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
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence, Tuple

from srmech.amsc.format import sha256_bytes
from srmech.math.qmat import QMat

__all__ = [
    "dominant_weight",
    "tensor_product_multiplicities",
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

#: The algebra name every payload carries.  A2 is the only algebra this
#: module ships; a rank-2 generalisation is deliberately NOT claimed.
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
    the result is scale-free; the guarded division is what makes that a
    measurement rather than an assertion."""
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
