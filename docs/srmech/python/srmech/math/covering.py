"""``srmech.math.covering`` — the CENTRE / COVERING layer (rc422, `#T1123`).

THE GAP THIS CLOSES
===================
srmech carries **algebras and finite groups** — *local* and *quotient* objects.
It has had no way to carry the **global datum a local object structurally cannot
hold**. The shape recurs, and until rc422 it was hand-rolled independently every
time it appeared:

===============================  ==========================================
where it surfaced                what survived
===============================  ==========================================
``so(8)`` / ``Spin(8)``          the algebra cannot see ``Z(Spin(8)) = V₄``;
                                 that centre is exactly ``π₁(PSO(8))``
``genome.cwf_consistency_mod2``  its own shipped bounding says a finite group
                                 (``Q₈``) pins ``Lk`` only **mod 2**, and it
                                 already returns ``lk_center_parity``
``q8.q8_project_v4``             its docstring: *"Drops the center sign bit"*
``quaternion_cycle_holonomy``    ``center_parity`` ∈ ``{+1, −1, 0}``
``One.spinor_sign``              ``(−1)^Σw`` — "the genuine Spin→SO 2:1 lift"
``laplacian.cycle_holonomy``     the holonomy **mod 1**; the integer winding of
                                 the lift is the datum it cannot return
===============================  ==========================================

In every case the surviving shadow is the **centre-parity — one bit where an
integer lived**. Six shipped ops, six hand-rolled parities, no common surface,
and no way to say *which* covering a given parity is the shadow of.

THE ONE THING A READER MUST NOT MISREAD
=======================================
"Compute the centre of ``so(8)``" returns the **zero object**, and that is
CORRECT, not a refutation. ``so(8)`` is semisimple, so its Lie-algebra centre is
0. The Klein four-group is ``Z(Spin(8))`` — a property of the simply-connected
**GROUP**. The algebra is *shared* by ``Spin(8)``, ``SO(8)`` and ``PSO(8)`` and
structurally cannot distinguish them, because the centre is **global (π₁) data**
while a Lie algebra is **local** data. This is a category distinction, not a
limitation to engineer around; it is precisely why the datum needs a carrier of
its own, which is what this module is.

THE STRUCTURE, STATED ONCE
==========================
Everything here is one shape: a **central extension**

    1 → Z → G̃ → G → 1

``G̃`` is the cover, ``G`` the shipped/local object, ``Z`` the centre (equally:
the deck group, equally ``π₁(G)`` when ``G̃`` is the universal cover). A closed
loop in ``G`` **lifts** to a path in ``G̃`` whose endpoint is an element of
``Z`` — the **monodromy**. When ``Z ≅ ℤ`` (a universal cover of a circle) the
datum is an **integer** — a winding, a linking number. When ``Z`` is finite of
order ``n`` only the residue survives, and at ``n = 2`` that residue is one bit.

So the layer is two ops wide and honest about the loss:

* :func:`center_lift` accumulates in the COVER and reports the shadow;
* :func:`lift_fibre` states what the shadow does NOT determine — the fibre is a
  coset of ``center_order·ℤ``, enumerated rather than asserted, because
  ``[[feedback_an_instrument_that_cannot_return_otherwise_is_not_a_measurement]]``.

HONEST BOUND (load-bearing)
===========================
Two centres being both called "centre" does NOT make them the same object. Every
row of :func:`covering_catalog` is a **FORM** match at the stated junction, never
an object-identity claim
(``[[user_stance_cascade_matching_substrate_blind_form_not_identity]]``). The
catalog carries its REJECTED candidates alongside its accepted ones, with the
reason each was rejected, because a census that accepts everything is not a
census.

Class homes: **I** (cyclic reduction, the projection to the centre) ∘ **K**
(pin-slot magnitude — the sign is NEVER ``abs()``) ∘ **C** (orientation
re-application) ∘ **N** (exact rational, the CWF sum) ∘ **E** (the catalog).

numpy-free; no stdlib ``math`` / ``fractions`` / ``decimal``; no ``abs()``.
"""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from srmech.cascade import magnitude as _magnitude
from srmech.cascade import reorient as _reorient
from srmech.math.cyclic import mod_add as _mod_add
from srmech.math.q import Q

__all__ = [
    "center_lift",
    "center_parity",
    "covering_catalog",
    "lift_fibre",
    "linking_number_cwf",
]

#: ``center_order = 0`` spells the UNIVERSAL cover, whose deck group is ``ℤ``:
#: no reduction happens, the shadow IS the lift, and nothing is lost. It is a
#: sentinel rather than a separate op because "how much is lost" is exactly the
#: parameter, and ``ℤ`` is the loss-free end of that same axis.
UNIVERSAL = 0


def _orientation(value: int) -> int:
    """The Class-C orientation of an integer: ``-1`` / ``0`` / ``+1``.

    Read as a comparison against the Class-K pin-slot magnitude, never with
    ``abs()`` — sign-flip IS the Class-K pin-slot phase boundary and
    re-application is Class C
    (``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``).
    """
    if value == 0:
        return 0
    return 1 if _magnitude(value) == value else -1


def _to_center(value: int, center_order: int) -> int:
    """Project an integer cover-value into ``ℤ/center_order`` (Class I).

    ``center_order == UNIVERSAL`` returns the value unreduced — the deck group
    is ``ℤ`` and there is nothing to reduce. The negative branch is a genuine
    Class-K ∘ Class-C composition: ``mod_add`` serves the unsigned domain, so
    the magnitude is reduced first and the orientation re-applied after, which
    is what keeps the cascade-count matching the cascade-shape.
    """
    if center_order == UNIVERSAL:
        return int(value)
    orientation = _orientation(value)
    reduced = _mod_add(int(_magnitude(value)), 0, center_order)
    if orientation < 0 and reduced:
        # Class C: re-apply the orientation ON THE CYCLIC CARRIER. mod_add
        # serves the unsigned domain, so the additive inverse of a residue is
        # reached as ``order - r`` (already in ``[0, order)``) rather than by
        # handing the op a negative — which is the whole reason the sign is a
        # Class-K/Class-C composition here instead of an ``abs()``.
        reduced = _mod_add(center_order - reduced, 0, center_order)
    return int(reduced)


def _check_order(center_order: int, op: str) -> int:
    if not isinstance(center_order, int) or isinstance(center_order, bool):
        raise ValueError(
            f"{op}: center_order must be an int (0 = the universal ℤ cover); "
            f"got {center_order!r}")
    if center_order < 0:
        raise ValueError(
            f"{op}: center_order must be >= 0 (0 = the universal ℤ cover, "
            f"n > 0 = a centre of order n); got {center_order}")
    return center_order


def center_parity(winding: int) -> int:
    """The ``ℤ/2`` central sign ``(−1)^winding`` of an integer winding: ``±1``.

    **The one bit where an integer lived.** This is the single primitive the six
    hand-rolled instances in the module docstring each re-derived: ``One.
    spinor_sign``'s ``(−1)^Σw``, ``quaternion_cycle_holonomy``'s
    ``center_parity``, ``cwf_consistency_mod2``'s ``lk_center_parity``. One
    winding flips the sign, two restore it — the ``Spin → SO`` double cover, and
    equally ``π₁(SO(3)) = ℤ/2``.

    Class K (pin-slot magnitude — never ``abs()``) ∘ Class I (mod-2) ∘ Class C
    (the ``+1``/``−1`` orientation re-application). ``(−1)^w = (−1)^(−w)``, so
    the parity is orientation-blind by construction and the composition is
    exact for negative windings without a special case.

    Args:
        winding: The integer accumulated in the cover.

    Returns:
        ``+1`` when ``winding`` is even, ``−1`` when odd.

    Raises:
        ValueError: if ``winding`` is not an ``int``.

    Example:
        >>> center_parity(0), center_parity(1), center_parity(-3)
        (1, -1, -1)
    """
    if not isinstance(winding, int) or isinstance(winding, bool):
        raise ValueError(
            f"center_parity: winding must be an int; got {winding!r}")
    residue = _to_center(winding, 2)
    # Class C: the residue {0, 1} re-applied as an orientation {+1, -1}.
    return 1 if residue == 0 else int(_reorient(1, orientation=-1))


def center_lift(steps: Sequence[int], center_order: int = UNIVERSAL) -> dict:
    """Accumulate integer steps in the **cover** and project to the centre.

    This is the op that keeps the integer where the shipped local object keeps
    only the residue. Run it alongside a finite-group encoder and the integer
    survives: ``#T1005``'s statement — *"the genome accumulates in the FINITE
    GROUP where a helix accumulates in its UNIVERSAL COVER; DNA's Lk is an
    integer, our encoding structurally cannot hold one"* — is a statement about
    which of these two accumulators you kept, not about an unavoidable loss.

    Class I (the mod-``n`` projection) ∘ Class K/C (the signed reduction).

    Args:
        steps: The per-step integer contributions, accumulated in the cover.
        center_order: The order of the centre ``Z``. ``0`` (:data:`UNIVERSAL`)
            means the universal cover, deck group ``ℤ`` — nothing is reduced
            and nothing is lost.

    Returns:
        A dict with ``cover_lift`` (the integer, always), ``center_shadow``
        (its image in ``Z``), ``center_order``, ``center_parity`` (the ``±1``
        bit, always computed — it is the shadow every instance in this module's
        table happens to keep), and ``shadow_determines_lift`` — ``True`` only
        for the universal cover, i.e. the honest statement of when the
        projection loses nothing.

    Raises:
        ValueError: on a non-int step or a negative ``center_order``.

    Example:
        >>> center_lift([1, 1, 1], 2)["cover_lift"]
        3
        >>> center_lift([1, 1, 1], 2)["center_shadow"]
        1
    """
    center_order = _check_order(center_order, "center_lift")
    total = 0
    for i, step in enumerate(steps):
        if not isinstance(step, int) or isinstance(step, bool):
            raise ValueError(
                f"center_lift: steps[{i}] must be an int; got {step!r}")
        total += step
    return {
        "cover_lift": total,
        "center_shadow": _to_center(total, center_order),
        "center_order": center_order,
        "center_parity": center_parity(total),
        "shadow_determines_lift": center_order == UNIVERSAL,
    }


def lift_fibre(shadow: int, center_order: int, window: int) -> dict:
    """The integer lifts a centre-shadow does **not** determine.

    The fibre over a shadow is a coset of ``center_order·ℤ``. This op
    ENUMERATES it inside ``[−window, window]`` instead of asserting that
    information was lost, because an instrument that cannot return otherwise is
    not a measurement
    (``[[feedback_an_instrument_that_cannot_return_otherwise_is_not_a_measurement]]``).
    For the universal cover the fibre is the single point ``{shadow}`` — the
    same op reports "nothing was lost" by returning a fibre of size 1, rather
    than by a separate code path that could not have said otherwise.

    Class I (the coset walk) ∘ Class E (enumeration).

    Args:
        shadow: The centre residue actually held by the local object.
        center_order: The order of the centre (``0`` = universal cover).
        window: Enumerate lifts with magnitude at most this (``>= 0``).

    Returns:
        ``{'fibre': list[int], 'size': int, 'center_order': int, 'window': int,
        'determined': bool}`` — ``determined`` is ``True`` iff the fibre has
        exactly one element, i.e. the shadow really does pin the lift.

    Raises:
        ValueError: on a bad ``center_order`` or a negative ``window``.

    Example:
        >>> lift_fibre(1, 2, 4)["fibre"]
        [-3, -1, 1, 3]
    """
    center_order = _check_order(center_order, "lift_fibre")
    if not isinstance(window, int) or isinstance(window, bool) or window < 0:
        raise ValueError(
            f"lift_fibre: window must be a non-negative int; got {window!r}")
    if center_order == UNIVERSAL:
        fibre = [int(shadow)] if _magnitude(int(shadow)) <= window else []
    else:
        target = _to_center(int(shadow), center_order)
        fibre = [k for k in range(-window, window + 1)
                 if _to_center(k, center_order) == target]
    return {
        "fibre": fibre,
        "size": len(fibre),
        "center_order": center_order,
        "window": window,
        "determined": len(fibre) == 1,
    }


def linking_number_cwf(twist: Tuple[int, int],
                       writhe: Tuple[int, int]) -> dict:
    """``Lk = Tw + Wr`` — the INTEGER invariant recovered from two frame-relative
    rationals (Călugăreanu–White–Fuller).

    The asymmetry this op measures is one the mod-2 shadow destroys: ``Tw`` and
    ``Wr`` are each **frame-relative reals** that move when the framing moves,
    while their sum ``Lk`` is a **topological integer** that does not. srmech
    already ships ``genome.cwf_consistency_mod2``, which checks the relation
    ``(Tw + Wr) ≡ Lk (mod 2)`` and returns ``lk_center_parity`` — the bit. This
    op returns the integer, and certifies its integrality rather than assuming
    it: a non-integral sum is reported as ``is_integer=False`` with the exact
    rational preserved, never rounded away.

    Class N (exact rational) ∘ Class K (the integrality pin-slot). Inputs are
    ``(numerator, denominator)`` integer pairs — the Class-N contract, never
    floats (``[[feedback_class_n_precision_contract]]``).

    Args:
        twist: ``Tw`` as an exact ``(num, den)`` integer pair.
        writhe: ``Wr`` as an exact ``(num, den)`` integer pair.

    Returns:
        ``{'lk': (num, den), 'is_integer': bool, 'linking_number': int | None,
        'center_parity': int | None, 'twist': (num, den),
        'writhe': (num, den)}``. ``linking_number`` / ``center_parity`` are
        ``None`` exactly when the sum is not integral — the honest report, not a
        rounded one.

    Raises:
        ValueError: if either pair is not two ints, or a denominator is 0.

    Example:
        >>> linking_number_cwf((3, 2), (5, 2))["linking_number"]
        4

    Provenance — **DERIVED-AND-MEASURED, not cited** (rc429, `#T1128`):
        The same verdict, and for the same measured reasons, as
        :func:`srmech.biology.genome.cwf_consistency_mod2`:
        "Călugăreanu–White–Fuller" is the STANDARD NAME of ``Lk = Tw + Wr``,
        the canonical sources are paywalled-only or offline, and under
        ``[[feedback_paywalled_doi_cannot_be_attested]]`` **no citation is
        substituted.**

        ⚠️ This site was named by NEITHER of the two defects rc429 was
        called for — it was found by walking the term through every emitted
        field, and it shipped bare in ``docstring``, ``summary`` and
        ``explanation``. A repair scoped to the two known sites would have
        left it shipping. That is arm S6's whole subject, and it is also its
        stated blind spot: S6 sees only claims someone has already
        adjudicated onto its roster.

        This prose previously opened "The theorem's content is …", which
        appeals to what a NAMED THEOREM does as the warrant for this op's
        design. rc429 narrows it to what the op itself measures: it returns
        the exact rational sum and CERTIFIES integrality (``is_integer``)
        rather than assuming it, and ``tests/test_covering_layer_rc422.py``
        calls it and asserts both the integral and the non-integral branch.
    """
    def _q(pair, name):
        if (not isinstance(pair, (tuple, list)) or len(pair) != 2
                or not all(isinstance(x, int) and not isinstance(x, bool)
                           for x in pair)):
            raise ValueError(
                f"linking_number_cwf: {name} must be an exact (num, den) "
                f"integer pair (the Class-N contract, never a float); "
                f"got {pair!r}")
        if pair[1] == 0:
            raise ValueError(
                f"linking_number_cwf: {name} denominator is zero")
        return Q(int(pair[0]), int(pair[1]))

    tw = _q(twist, "twist")
    wr = _q(writhe, "writhe")
    lk = tw + wr
    num, den = lk.as_pair()
    is_int = den == 1
    return {
        "lk": (num, den),
        "is_integer": is_int,
        "linking_number": num if is_int else None,
        "center_parity": center_parity(num) if is_int else None,
        "twist": tw.as_pair(),
        "writhe": wr.as_pair(),
    }


# ── the census (Class E) ──────────────────────────────────────────────────
# Each REACHED row names shipped ops by their registered dotted path, so the
# catalog cannot quietly rot: tests/test_covering_layer_rc422.py resolves every
# one against the live registry and fails if a name stops existing. Each
# REJECTED row carries the reason it does NOT fit the predicate below — a census
# that accepts everything is not a census.
#
# THE FIT PREDICATE, stated before the candidates were scored
# (``[[feedback_dont_pre_commit_spike_query_operators]]``): a coherency is
# REACHED iff
#   (i)   there is a base object the shipped op actually computes in,
#   (ii)  there is a covering / central extension of it whose centre (equally:
#         deck group) Z is NON-TRIVIAL, and
#   (iii) the shipped op's output is the image of a Z-torsor-valued quantity —
#         a genuinely finer invariant exists upstairs that the shipped op
#         structurally cannot return.
# If π₁(base) = 0 or Z is trivial, REJECT: there is no global datum to carry, and
# a layer that "reaches" such a case is measuring nothing.

_REACHED: Tuple[Dict[str, object], ...] = (
    {
        "name": "spin8",
        "cover": "Spin(8)", "base": "SO(8)", "quotient": "PSO(8)",
        "center": "V4 (Klein four-group)", "center_order": 4,
        "pi1_of_quotient": "V4",
        "integer_invariant": None,
        "shadow": "which of the three 8-dim reps a central involution kills",
        "local_object_cannot_see": "so(8) is semisimple: its Lie-algebra centre "
                                   "is 0, and the algebra is shared by Spin(8) "
                                   "/ SO(8) / PSO(8)",
        "shipped_ops": ("srmech.physics.qm.so8.so8_adjoint_basis",
                        "srmech.physics.qm.triality.spin8_center",
                        "srmech.physics.qm.triality.triality_rep_dictionary"),
        "basis": "DERIVED (rc422): the centre is solved off the octonion "
                 "multiplication table as the four scalar triples with "
                 "eps_v = eps_s*eps_c; each non-identity element kills exactly "
                 "one rep",
    },
    {
        "name": "spin3",
        "cover": "SU(2) = Spin(3)", "base": "SO(3)", "quotient": "SO(3)",
        "center": "{+1, -1}", "center_order": 2,
        "pi1_of_quotient": "Z/2",
        "integer_invariant": None,
        "shadow": "center_parity: the spinor half-twist",
        "local_object_cannot_see": "a rotation in SO(3) does not record which "
                                   "of its two SU(2) lifts was traversed",
        "shipped_ops": ("srmech.physics.qm.quaternion.quaternion_cycle_holonomy",
                        "srmech.cascade.one.One.spinor_sign"),
        "basis": "SHIPPED: quaternion_cycle_holonomy already returns "
                 "center_parity in {+1, -1, 0}; One.spinor_sign already names "
                 "itself 'the genuine Spin->SO 2:1 lift'",
    },
    {
        "name": "q8_v4",
        "cover": "Q8", "base": "V4 = Q8/{+-1}", "quotient": "V4",
        "center": "{+1, -1}", "center_order": 2,
        "pi1_of_quotient": "the {+-1} kernel of the central quotient",
        "integer_invariant": None,
        "shadow": "the V4 coset (q & 3)",
        "local_object_cannot_see": "the centre sign bit, by construction",
        "shipped_ops": ("srmech.biology.q8.q8_project_v4",),
        "basis": "SHIPPED, and stated in the op's own docstring: 'Drops the "
                 "center sign bit, keeping the {1, i, j, k} coset'",
    },
    {
        "name": "circle_z",
        "cover": "R (the universal cover)", "base": "R/Z", "quotient": "R/Z",
        "center": "Z (the deck group)", "center_order": UNIVERSAL,
        "pi1_of_quotient": "Z",
        "integer_invariant": "the winding / linking number Lk",
        "shadow": "lk_center_parity (mod 2) / the holonomy mod 1",
        "local_object_cannot_see": "an INTEGER Lk: a finite group pins it only "
                                   "mod |Z|, and the mod-1 holonomy loses the "
                                   "turn count entirely",
        "shipped_ops": ("srmech.biology.genome.cwf_consistency_mod2",
                        "srmech.biology.genome.discrete_writhe",
                        "srmech.math.laplacian.cycle_holonomy",
                        "srmech.math.covering.linking_number_cwf"),
        "basis": "DERIVED: this module's center_lift with center_order=0 keeps "
                 "the integer the finite-group encoders reduce away; "
                 "linking_number_cwf recovers it from Tw + Wr. The task "
                 "`#T1005` row.",
    },
)

_REJECTED: Tuple[Dict[str, object], ...] = (
    {
        "name": "octonion_frame_read_s3_fiber",
        "candidate": "the S3 fibre writhe q1 of "
                     "srmech.physics.qm.octonion_frame_read",
        "fails_clause": "(ii)",
        "reason": "pi_1(S^3) = 0. The S3 fibre is SIMPLY CONNECTED, so there "
                  "is no covering datum for the layer to carry: q1 is a "
                  "frame-relative continuous residue, not a discrete monodromy "
                  "class. Pushing the read down to SO(3) = S^3/{+-1} DOES "
                  "produce a Z/2 — but that is the 'spin3' row above, a "
                  "DIFFERENT object, and merging them would be exactly the "
                  "form-vs-identity error this layer is bound by.",
    },
    {
        "name": "cayley_dickson_rung_bump",
        "candidate": "the CD ladder's induced Aut(V4) action "
                     "(srmech.cascade.cayley_dickson.*)",
        "fails_clause": "(ii)",
        "reason": "Cayley-Dickson doubling is not a covering map and the rung "
                  "bump is an automorphism of a finite group, not a deck "
                  "transformation. There is no fibration, hence no global "
                  "datum being lost — nothing to carry. It is USED by the "
                  "spin8 row as a generator, which is not the same as being a "
                  "row.",
    },
    {
        "name": "g2_der_octonions",
        "candidate": "srmech.physics.qm.so8.g2_subalgebra / an_embedding",
        "fails_clause": "(ii)",
        "reason": "MEASURED at rc422: the triality-fixed subgroup of "
                  "Z(Spin(8)) is TRIVIAL — applying tau's derived label "
                  "permutation to the four central sign-triples fixes only the "
                  "identity. So the g2 = Fix(tau) row has a trivial centre and "
                  "there is no shadow to carry. This is the rejection that "
                  "shows the predicate discriminates: g2 sits inside a row that "
                  "IS reached, and is still correctly rejected on its own.",
    },
    {
        "name": "hermitian_spectrum",
        "candidate": "srmech.math.laplacian.magnetic_laplacian's eigenvalues",
        "fails_clause": "(iii)",
        "reason": "eigenvalues are conjugation-invariant, so no monodromy is "
                  "even encoded in them (F552). The odd channel that IS lost "
                  "here is already carried by cycle_holonomy, which is in the "
                  "'circle_z' row — so admitting the spectrum would double-count "
                  "one loss as two.",
    },
    {
        "name": "triality_automorphism",
        "candidate": "srmech.physics.qm.triality.triality_automorphism (tau)",
        "fails_clause": "(i)",
        "reason": "tau is an automorphism, not a covering. It ACTS on the "
                  "centre of the spin8 row (permuting the three non-identity "
                  "elements exactly as it permutes the three reps) rather than "
                  "carrying a centre of its own. Being adjacent to the datum is "
                  "not holding it.",
    },
)


def covering_catalog() -> dict:
    """The census: which shipped coherencies the centre/covering layer REACHES,
    and which it REJECTS — each with a reason.

    Class E (catalog enumeration). Every ``shipped_ops`` entry is a registered
    dotted op path, resolved against the live registry by
    ``tests/test_covering_layer_rc422.py``, so a row cannot outlive the op it
    names. The ``rejected`` half is not decoration: the fit predicate is stated
    in this module's source above the tables, and the rejections are what make
    the acceptances mean something.

    HONEST BOUND: each row is a **FORM** match at its stated junction. Two
    centres are not the same object because both are called "centre"
    (``[[user_stance_cascade_matching_substrate_blind_form_not_identity]]``).

    **The catalog is a COMPUTATION, not a table** (ADR-0002). The two fields a
    reader would most want to disbelieve are recomputed on every call from
    :func:`srmech.physics.qm.triality.spin8_center`: the ``spin8`` row's
    ``center_order``, and the ``g2_der_octonions`` rejection's measured basis
    (the triality-fixed subgroup of ``Z(Spin(8))``, which is trivial). A row
    that could not be contradicted would not be a finding. The import is
    function-local on purpose — ``srmech.physics`` sits above ``srmech.math``,
    so a module-level import would invert the layering and cycle.

    Returns:
        ``{'reached': list[dict], 'rejected': list[dict], 'n_reached': int,
        'n_rejected': int, 'predicate': str, 'honest_bound': str}``

    Example:
        >>> covering_catalog()["n_reached"]
        4
    """
    from srmech.physics.qm.triality import spin8_center

    centre = spin8_center()
    reached = [dict(r) for r in _REACHED]
    for row in reached:
        if row["name"] == "spin8":
            row["center_order"] = centre["order"]
            row["center_measured"] = centre["is_klein_four"]
            row["rep_kernels"] = centre["rep_kernels"]
    rejected = [dict(r) for r in _REJECTED]
    for row in rejected:
        if row["name"] == "g2_der_octonions":
            row["measured_fixed_subgroup"] = centre["triality_fixed_subgroup"]
            row["measured_center_is_trivial"] = (
                len(centre["triality_fixed_subgroup"]) == 1)
    return {
        "reached": reached,
        "rejected": rejected,
        "n_reached": len(_REACHED),
        "n_rejected": len(_REJECTED),
        "predicate": "REACHED iff (i) a base object the shipped op computes "
                     "in, (ii) a covering / central extension with NON-TRIVIAL "
                     "centre Z, and (iii) the shipped op's output is the image "
                     "of a Z-torsor-valued quantity a finer invariant exists "
                     "for upstairs. pi_1(base) = 0 or Z trivial => REJECT.",
        "honest_bound": "each row is a FORM match at the stated junction, "
                        "never object-identity; two centres are not the same "
                        "object because both are called 'centre'",
    }
