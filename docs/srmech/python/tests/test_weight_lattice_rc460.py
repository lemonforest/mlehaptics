"""rc460 — the exact A2 weight-lattice stratum, and the group
bind that closes B1.

WHAT IS BEING TESTED, AND WHY EACH ORACLE IS HERE
=================================================
The module under test computes Lie-algebra tensor-product multiplicities as a
**signed integer count off a lattice** (Racah–Speiser), not as a convolution
of orbital measures against Haar.  That correction is the point of the rc, so
the suite is built to make the count FAIL if it is wrong, from four
independent directions:

1. **The op's own laws** — dimension, unit row, commutativity, associativity,
   non-negativity after cancellation, strict dominance, ℤ/3 N-ality
   conservation, conjugation symmetry.  These are self-consistency; they are
   necessary and nowhere near sufficient.
2. **PSL(2,7)**, through the SHIPPED ``srmech.math.groups`` ops — an oracle
   that reaches OUTSIDE the module entirely.  ⚠️ Scoped honestly: restriction
   is many-to-one, so PSL(2,7) validates **tensor power 2 only**, and the
   test is named for the CELL it validates rather than for the op.  A test
   called "validate fusion against the PSL(2,7) oracle" would be over-reading
   the measurement.
3. **Littlewood–Richardson**, hand-rolled from scratch on 3-row GL(3)
   partitions — declared, because sharing no code with the thing it checks is
   its entire value (`[[user_stance_co_equal_dual_construction_is_a_
   consistency_oracle]]`).  See the SANCTIONED HAND-ROLL note below.
4. **The abelian degenerate case** — where the whole lattice picture must
   reduce to plain addition in a dual group.

THE RED PROOFS ARE MANDATORY, AND THEY COME FROM LIVE TRAPS
===========================================================
Two well-formed WRONG ANSWERS were measured while this stratum was being
built, neither of which crashed:

* **transposed Weyl matrices** — ``3 ⊗ 3`` and ``3 ⊗ 3̄`` came out identical;
* **two walls instead of three** — A2 has THREE positive roots and only two
  are simple, so omitting the third leaks translates like ``(2, -2)`` that
  fold onto a wall and mint NON-DOMINANT labels.

Both ship below as PROVEN-RED perturbations.  An oracle that cannot go red is
not an oracle, so each perturbation is executed and asserted to fail — the
green ones next to them then mean something.

⚠️ SANCTIONED HAND-ROLL, DECLARED RATHER THAN HIDDEN
====================================================
THREE things in this file are hand-rolled, which normally reads as a gap
(`[[feedback_scratch_measurements_must_use_srmech_or_gaps_stay_invisible]]`).
(This note said "two" and omitted the third; a declaration that is itself
incomplete is the thing the discipline exists to prevent, so it is listed.)

* the **Littlewood–Richardson enumerator** is hand-rolled BECAUSE its entire
  value is sharing no code with the fold it checks.  That is the declared
  exception, not an oversight.  (Recorded because it bit: a first attempt
  checked the lattice-word condition in PLACEMENT order rather than on the
  REVERSE READING WORD, and a control that is wrong in the PERMISSIVE
  direction manufactures agreement.  It reported 192 false disagreements on
  256 pairs and was fixed, not tuned.)
* the **PSL(2,7) presentation** is hand-rolled because srmech ships only
  ``cyclic_group`` + ``semidirect_product`` and **cannot construct a simple
  group**.  That is a GENUINE gap, and it ships as the named open row
  :func:`test_the_psl2_constructor_gap_is_recorded_not_hidden` — ``psl2(q)``
  is the missing constructor.
* :func:`_perturbed_fold` is a hand-rolled, PARAMETERISED copy of the
  Racah–Speiser fold, and it exists for exactly one reason: the two mandated
  red proofs below perturb the **Weyl family** and the **wall set**, and the
  shipped op reads both from module constants, so it cannot be parameterised
  on either.  Without this there is no way to execute the mandate at all —
  the alternative is asserting the perturbations fail without running them,
  which is the failure mode the red proofs exist to rule out.  It is not a
  second implementation offered as evidence: it is bound to the shipped op by
  :func:`test_the_harness_reproduces_the_shipped_op`, which requires exact
  agreement UNPERTURBED, so a red result below is attributable to the
  perturbation rather than to the harness.  Declared because it is textually
  beyond the two above, and a hand-roll nobody listed is indistinguishable
  from one nobody noticed.

⚠️ ROW LOCATION IS BY CONTENT, NEVER BY INDEX.  Character-table rows sort
``(degree, lex)``; the trivial character is NOT at index 0 in general.  Every
row this file reaches for is located by what it CONTAINS.
"""
from __future__ import annotations

import itertools

import pytest

from srmech.amsc.format import sha256_bytes
from srmech.math import weight_lattice as wl
from srmech.math.groups import (character_table, cyclic_group,
                                decompose_representation,
                                frobenius_schur_indicator,
                                fusion_multiplicities, isotypic_projector,
                                character_of, permutation_representation,
                                semidirect_product, zeta_mul)
from srmech.math.weight_lattice import (dominant_weight,
                                        tensor_product_multiplicities,
                                        weight_multiplicities)

#: The label window every law below runs over.  Small on purpose: the laws
#: are quantified over PAIRS, so 16 labels is 256 pairs.
LABELS = [(p, q) for p in range(4) for q in range(4)]


def _cell(a, b):
    """``{(p, q): multiplicity}`` for one fusion cell."""
    return {(p, q): m
            for p, q, m in tensor_product_multiplicities(a, b)["constituents"]}


def _fuse_dict(channels, label):
    """Fuse a whole multiplicity dict against one more label."""
    out = {}
    for (p, q), m in channels.items():
        for rp, rq, rm in tensor_product_multiplicities(
                (p, q), label)["constituents"]:
            out[(rp, rq)] = out.get((rp, rq), 0) + m * rm
    return {k: v for k, v in out.items() if v}


def _full_weight_system(label):
    """The FULL weight multiset of ``V_label`` (orbits expanded)."""
    out = {}
    for p, q, m in weight_multiplicities(*label)["dominant"]:
        for w in wl._weyl_orbit((p, q)):
            out[w] = out.get(w, 0) + m
    return out


# ══════════════════════════════════════════════════════════════════════
# 0. every payload key this file reads EXISTS
# ══════════════════════════════════════════════════════════════════════

def test_every_payload_key_this_suite_reads_exists():
    """⚠️ Assert the key before reading it.  Two probes were silently wrong
    in the week this rc was built because a key was ABSENT and ``.get``
    returned a plausible default.  ``irrep_dimensions`` returns ``degrees``
    and NOT ``dimensions``; ``order`` means the INPUT group's order at ~20
    sites.  The habit is cheap and the failure mode is not."""
    for key in ("algebra", "label", "dimension", "conjugate", "n_ality",
                "cartan", "gauge", "procedure_sha256", "label_sha256"):
        assert key in dominant_weight(1, 1), key
    for key in ("algebra", "label", "dimension", "dominant", "orbit_sizes",
                "n_dominant", "n_weights", "procedure_sha256",
                "weights_sha256"):
        assert key in weight_multiplicities(1, 1), key
    for key in ("algebra", "a", "b", "constituents", "dim_a", "dim_b",
                "dim_check", "singlet_multiplicity", "n_constituents",
                "procedure_sha256", "fusion_sha256"):
        assert key in tensor_product_multiplicities((1, 0), (1, 0)), key
    for key in ("chirality", "global_form", "metric_scale"):
        assert key in dominant_weight(1, 1)["gauge"], key


# ══════════════════════════════════════════════════════════════════════
# 1. dominant_weight — the stored label, and the gauge inside its address
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("label,dimension", [
    ((0, 0), 1), ((1, 0), 3), ((0, 1), 3), ((2, 0), 6), ((0, 2), 6),
    ((1, 1), 8), ((3, 0), 10), ((0, 3), 10), ((4, 0), 15), ((2, 1), 15),
    ((2, 2), 27),
])
def test_pinned_dimensions(label, dimension):
    """The named su(3) irreps, by dimension."""
    assert dominant_weight(*label)["dimension"] == dimension


def test_dimension_is_conjugation_symmetric_over_the_window():
    """``d(p, q) == d(q, p)`` — one half of why the generator cannot tell
    ``3`` from ``3̄``."""
    bad = [(p, q) for p in range(9) for q in range(9)
           if dominant_weight(p, q)["dimension"]
           != dominant_weight(q, p)["dimension"]]
    assert bad == [], bad


def test_conjugate_and_n_ality():
    three = dominant_weight(1, 0)
    assert three["conjugate"] == (0, 1)
    assert three["n_ality"] == 1
    adjoint = dominant_weight(1, 1)
    assert adjoint["conjugate"] == (1, 1)     # self-conjugate
    assert adjoint["n_ality"] == 0


def test_the_cartan_matrix_cannot_tell_3_from_3bar():
    """The MEASUREMENT behind the gauge block: every invariant derived from
    the generator alone coincides for a label and its conjugate."""
    for p, q in LABELS:
        a, b = dominant_weight(p, q), dominant_weight(q, p)
        assert a["dimension"] == b["dimension"]
        wa = weight_multiplicities(p, q)
        wb = weight_multiplicities(q, p)
        assert sorted(m for _, _, m in wa["dominant"]) == sorted(
            m for _, _, m in wb["dominant"])
        assert sorted(wa["orbit_sizes"]) == sorted(wb["orbit_sizes"])


def test_the_gauge_is_INSIDE_the_content_address():
    """RED PROOF.  An address that does not move when the gauge moves is not
    addressing the gauge.  Recomputed here with ``metric_scale`` dropped from
    the serialised gauge block; the digest MUST differ."""
    payload = dominant_weight(1, 0)
    without_metric = sha256_bytes("\n".join([
        wl.A2_NAME,
        "label=1,0",
        "gauge=" + ";".join(f"{k}={v}" for k, v in wl.A2_GAUGE_ITEMS
                            if k != "metric_scale"),
        "procedure=" + payload["procedure_sha256"],
    ]).encode("utf-8"))
    assert payload["label_sha256"] != without_metric


def test_the_chirality_bit_separates_3_from_3bar_in_the_address():
    """The generator cannot separate them; the ADDRESS must, because the
    label order is carried inside it."""
    assert (dominant_weight(1, 0)["label_sha256"]
            != dominant_weight(0, 1)["label_sha256"])


def test_the_procedure_address_binds_the_derivation_not_the_label():
    """``procedure_sha256`` is label-independent by construction — it
    addresses the DERIVATION, which is what makes it meaningful to bind it
    into every label address."""
    addresses = {dominant_weight(p, q)["procedure_sha256"]
                 for p, q in LABELS}
    assert len(addresses) == 1
    assert addresses == {wl._procedure_sha256()}


@pytest.mark.parametrize("bad", [(-1, 0), (0, -1), (True, 0), (0, 1.0)])
def test_label_law_raises(bad):
    with pytest.raises(ValueError):
        dominant_weight(*bad)


def test_label_shape_law_raises():
    with pytest.raises(ValueError, match="label-shape law"):
        tensor_product_multiplicities((1, 0, 0), (1, 0))


# ══════════════════════════════════════════════════════════════════════
# 2. weight_multiplicities — Freudenthal, exact in ℤ
# ══════════════════════════════════════════════════════════════════════

def test_the_adjoint_zero_weight_multiplicity_is_the_RANK():
    """``(1,1)`` → zero weight at multiplicity **2**, and 2 is the rank of
    su(3).  Visible on the face of the payload, which is the point of
    carrying dominant representatives rather than a flat list."""
    payload = weight_multiplicities(1, 1)
    assert payload["dominant"] == ((0, 0, 2), (1, 1, 1))
    assert payload["orbit_sizes"] == (1, 6)
    assert payload["dimension"] == 8
    assert payload["n_weights"] == 8


@pytest.mark.parametrize("label,zero_multiplicity",
                         [((1, 1), 2), ((2, 2), 3), ((3, 3), 4)])
def test_pinned_zero_weight_multiplicities(label, zero_multiplicity):
    found = {(a, b): m for a, b, m in weight_multiplicities(*label)["dominant"]}
    assert found[(0, 0)] == zero_multiplicity


def test_the_decuplet_is_multiplicity_free():
    """``(3,0)`` — the 10 — has every weight at multiplicity 1."""
    assert all(m == 1
               for _, _, m in weight_multiplicities(3, 0)["dominant"])


def test_the_dimension_law_over_the_full_window():
    """``Σ_ν m(ν)·|orbit(ν)| == dim(p,q)`` over ``[0,11]²``.

    The op RAISES internally on a violation, so a clean pass IS the law —
    stated here so the assertion is not mistaken for a tautology.
    """
    for p in range(12):
        for q in range(12):
            payload = weight_multiplicities(p, q)
            assert payload["n_weights"] == payload["dimension"], (p, q)


def test_multiplicities_are_weyl_invariant():
    """Every weight in an orbit carries the orbit representative's
    multiplicity — the property that lets Freudenthal read non-dominant
    weights through :func:`_dominant_conjugate`."""
    for label in [(1, 1), (2, 1), (2, 2), (3, 0)]:
        system = _full_weight_system(label)
        for weight, mult in system.items():
            for image in wl._weyl_orbit(weight):
                assert system[image] == mult, (label, weight, image)


def test_orbit_sizes_are_DERIVED_not_asserted():
    """The payload's orbit sizes equal the cardinality of the actual Weyl
    orbit — not a coordinate-vanishing rule that happens to agree."""
    for p, q in LABELS:
        payload = weight_multiplicities(p, q)
        for (a, b, _m), size in zip(payload["dominant"],
                                    payload["orbit_sizes"]):
            assert size == len(wl._weyl_orbit((a, b)))


# ══════════════════════════════════════════════════════════════════════
# 3. the Weyl group itself — derived, not transcribed
# ══════════════════════════════════════════════════════════════════════

def test_the_weyl_group_is_S3_with_a_balanced_sign_ledger():
    assert len(wl._WEYL) == 6
    signs = sorted(s for _, s in wl._WEYL)
    assert signs == [-1, -1, -1, 1, 1, 1]


def test_the_derived_matrices_agree_with_the_reflection_functions():
    """The mitigation for the transposition trap, executed."""
    for index in (0, 1):
        matrix = wl._reflection_matrix(index)
        for probe in [(p, q) for p in range(-3, 4) for q in range(-3, 4)]:
            assert wl._apply(matrix, probe) == wl._reflect(index, probe)


def test_A2_HAS_THREE_POSITIVE_ROOTS_AND_ONLY_TWO_ARE_SIMPLE():
    """The structural fact the two-wall red proof below depends on."""
    assert len(wl.A2_POSITIVE_ROOTS) == 3
    assert len(wl.A2_SIMPLE_ROOTS) == 2
    assert wl.A2_POSITIVE_ROOTS[2] not in wl.A2_SIMPLE_ROOTS


def test_the_coroot_pairing_is_derived_from_the_stored_gram_matrix():
    """``<μ, α_i^∨>`` must come out as the i-th Dynkin coordinate, and
    ``<μ, (α₁+α₂)^∨>`` as their sum — DERIVED through the guarded division,
    never spelled as a coordinate read."""
    for weight in [(1, 0), (0, 1), (2, -2), (3, 5), (-4, 1)]:
        assert wl._coroot_pairing("t", weight,
                                  wl.A2_POSITIVE_ROOTS[0]) == weight[0]
        assert wl._coroot_pairing("t", weight,
                                  wl.A2_POSITIVE_ROOTS[1]) == weight[1]
        assert wl._coroot_pairing(
            "t", weight, wl.A2_POSITIVE_ROOTS[2]) == weight[0] + weight[1]


# ══════════════════════════════════════════════════════════════════════
# 4. tensor_product_multiplicities — the pinned cells and the law suite
# ══════════════════════════════════════════════════════════════════════

def test_three_tensor_three_is_threebar_plus_six():
    """THE cell.  ``3 ⊗ 3 = 3̄ ⊕ 6`` — the 3̄ at multiplicity one, exactly one
    degree-6 channel, and the spurious same-label channel at exactly zero."""
    payload = tensor_product_multiplicities((1, 0), (1, 0))
    assert payload["constituents"] == ((0, 1, 1), (2, 0, 1))
    assert payload["dim_check"] == 9
    assert payload["singlet_multiplicity"] == 0
    channels = _cell((1, 0), (1, 0))
    assert channels[(0, 1)] == 1                      # the 3-bar, once
    six = [lab for lab in channels
           if dominant_weight(*lab)["dimension"] == 6]
    assert len(six) == 1 and channels[six[0]] == 1    # exactly one 6
    assert channels.get((1, 0), 0) == 0               # spurious channel: 0


@pytest.mark.parametrize("a,b,expected", [
    ((1, 0), (0, 1), {(0, 0): 1, (1, 1): 1}),                  # 3⊗3̄ = 1+8
    ((1, 0), (1, 1), {(1, 0): 1, (0, 2): 1, (2, 1): 1}),       # 3⊗8 = 3+6̄+15
    ((1, 1), (1, 1), {(0, 0): 1, (1, 1): 2, (3, 0): 1,         # 8⊗8 =
                      (0, 3): 1, (2, 2): 1}),                  # 1+8+8+10+10̄+27
])
def test_pinned_fusion_cells(a, b, expected):
    assert _cell(a, b) == expected


def test_the_singlet_is_surfaced_on_the_payload_face():
    """``singlet_multiplicity`` exists so "is the singlet present" is a
    payload read rather than a search."""
    assert tensor_product_multiplicities(
        (1, 0), (0, 1))["singlet_multiplicity"] == 1
    assert tensor_product_multiplicities(
        (1, 0), (1, 0))["singlet_multiplicity"] == 0
    for p, q in LABELS:
        payload = tensor_product_multiplicities((p, q), (q, p))
        assert payload["singlet_multiplicity"] == 1


def test_unit_row():
    """``N_{λ,(0,0)}^μ = δ_{λμ}`` — the trivial rep is the fusion unit."""
    for label in LABELS:
        payload = tensor_product_multiplicities(label, (0, 0))
        assert payload["constituents"] == ((label[0], label[1], 1),)


def test_commutativity_over_the_window():
    for a, b in itertools.product(LABELS, repeat=2):
        assert _cell(a, b) == _cell(b, a), (a, b)


def test_associativity_spot_checks():
    trio = [(1, 0), (0, 1), (1, 1), (2, 0), (2, 1)]
    for a, b, c in itertools.product(trio, repeat=3):
        left = _fuse_dict(_cell(a, b), c)
        right = _fuse_dict(_cell(b, c), a)
        assert left == right, (a, b, c)


def test_dimension_law_over_the_window():
    for a, b in itertools.product(LABELS, repeat=2):
        payload = tensor_product_multiplicities(a, b)
        total = sum(m * dominant_weight(p, q)["dimension"]
                    for p, q, m in payload["constituents"])
        assert total == payload["dim_check"], (a, b)


def test_n_ality_is_conserved_by_fusion():
    """The Z/3 grading is su(3)'s abelian shadow, and fusion is ADDITION in
    it.  This is also the free negative control on the lattice side: the
    picture must reduce correctly."""
    for a, b in itertools.product(LABELS, repeat=2):
        want = (dominant_weight(*a)["n_ality"]
                + dominant_weight(*b)["n_ality"]) % 3
        for p, q, _m in tensor_product_multiplicities(a, b)["constituents"]:
            assert dominant_weight(p, q)["n_ality"] == want, (a, b, (p, q))


def test_conjugation_symmetry():
    """``N_{ā b̄}^{c̄} == N_{ab}^{c}``."""
    for a, b in itertools.product(LABELS, repeat=2):
        direct = _cell(a, b)
        conjugated = {(q, p): m
                      for (p, q), m in _cell((a[1], a[0]),
                                             (b[1], b[0])).items()}
        assert direct == conjugated, (a, b)


def test_every_constituent_is_strictly_dominant_and_positive():
    for a, b in itertools.product(LABELS, repeat=2):
        for p, q, m in tensor_product_multiplicities(a, b)["constituents"]:
            assert p >= 0 and q >= 0 and m > 0, (a, b, p, q, m)


def test_constituents_are_sorted_by_dimension_then_label():
    for a, b in itertools.product(LABELS, repeat=2):
        rows = tensor_product_multiplicities(a, b)["constituents"]
        keys = [(dominant_weight(p, q)["dimension"], p, q)
                for p, q, _m in rows]
        assert keys == sorted(keys), (a, b)


def test_a_large_cell_is_cheap():
    """Cost, stated honestly and then executed."""
    payload = tensor_product_multiplicities((12, 9), (10, 10))
    assert payload["dim_a"] == 1495
    assert payload["dim_b"] == 1331
    assert payload["dim_check"] == 1495 * 1331
    assert payload["n_constituents"] == 229


# ══════════════════════════════════════════════════════════════════════
# 5. RED PROOFS — both from live traps, both well-formed wrong answers
# ══════════════════════════════════════════════════════════════════════

def _perturbed_fold(a, b, weyl, walls):
    """The SAME Racah–Speiser fold, parameterised on the Weyl family and the
    wall set, so a perturbation can be run against the real algorithm rather
    than against a straw one.  Returns the constituents, or a string naming
    the failure."""
    system = weight_multiplicities(b[0], b[1])
    shift = (a[0] + wl.A2_RHO[0], a[1] + wl.A2_RHO[1])
    ledger = {}
    for p, q, mult in system["dominant"]:
        for weight in sorted({wl._apply(m, (p, q)) for m, _ in weyl}):
            translate = (shift[0] + weight[0], shift[1] + weight[1])
            if any(wl._coroot_pairing("probe", translate, r) == 0
                   for r in walls):
                continue
            hits = [(wl._apply(m, translate), s) for m, s in weyl
                    if wl._apply(m, translate)[0] > 0
                    and wl._apply(m, translate)[1] > 0]
            if len(hits) != 1:
                return f"regularity: {len(hits)} strictly dominant images"
            image, sign = hits[0]
            label = (image[0] - wl.A2_RHO[0], image[1] - wl.A2_RHO[1])
            if label[0] < 0 or label[1] < 0:
                return f"dominance: minted non-dominant {label}"
            ledger[label] = ledger.get(label, 0) + sign * mult
    return tuple(sorted((k[0], k[1], v) for k, v in ledger.items() if v))


def test_the_harness_reproduces_the_shipped_op():
    """The perturbation harness is only evidence if it agrees with the
    shipped op UNPERTURBED — otherwise a red result says nothing about the
    perturbation.

    Compared as a multiplicity MAP, not as a sequence: the harness sorts by
    label and the shipped op sorts by ``(dimension, label)``, and this test
    is about the COUNTS, not about the presentation order (which has its own
    gate, :func:`test_constituents_are_sorted_by_dimension_then_label`).
    """
    for a, b in itertools.product([(1, 0), (0, 1), (1, 1), (2, 1)],
                                  repeat=2):
        got = _perturbed_fold(a, b, wl._WEYL, wl.A2_POSITIVE_ROOTS)
        assert not isinstance(got, str), (a, b, got)
        assert {(p, q): m for p, q, m in got} == _cell(a, b), (a, b)


def test_RED_transposed_weyl_matrices_are_caught():
    """RED PROOF 1 — the measured live trap.

    A hand-transcribed TRANSPOSED Weyl family gave a well-formed wrong answer
    in which ``3 ⊗ 3`` and ``3 ⊗ 3̄`` came out IDENTICAL, with no crash.  Two
    things are asserted here:

    (a) the transposition is a REAL perturbation — the transposed family
        disagrees with the reflection FUNCTIONS, which is exactly what
        :func:`_reflection_matrix` deriving them makes impossible; and
    (b) running the fold with it FAILS.  The shipped module converts that
        silent wrong answer into a raise, because it scans all six elements
        and demands exactly one strictly-dominant image rather than looping
        an unbounded fold — the architecture is the mitigation, and this is
        the measurement of it.
    """
    transposed = tuple((((m[0][0], m[1][0]), (m[0][1], m[1][1])), s)
                       for m, s in wl._WEYL)
    disagreements = [
        probe for index in (0, 1)
        for probe in [(1, 0), (0, 1), (2, 3)]
        if wl._apply(((wl._reflection_matrix(index)[0][0],
                       wl._reflection_matrix(index)[1][0]),
                      (wl._reflection_matrix(index)[0][1],
                       wl._reflection_matrix(index)[1][1])), probe)
        != wl._reflect(index, probe)]
    assert disagreements, (
        "the transposed family agrees with the reflection functions, so this "
        "perturbation is not perturbing anything and the red proof below is "
        "vacuous")
    outcome = _perturbed_fold((1, 0), (1, 0), transposed,
                              wl.A2_POSITIVE_ROOTS)
    assert isinstance(outcome, str), (
        f"the transposed Weyl family produced a well-formed answer "
        f"{outcome} instead of failing — the guard that is supposed to "
        f"catch it did not")


def test_RED_only_two_walls_leaks_non_dominant_labels():
    """RED PROOF 2 — the second measured live trap.

    Checking only the two SIMPLE walls instead of all three positive roots
    lets translates such as ``(2, -2)`` through; they fold onto the missing
    wall and mint NON-DOMINANT labels, again well-formed and again with no
    crash.  The shipped three-wall fold is clean on the identical window,
    which is what makes the comparison a measurement rather than an anecdote.
    """
    window = [(p, q) for p in range(5) for q in range(5)]
    two_walls = wl.A2_POSITIVE_ROOTS[:2]
    leaks = sum(1 for a, b in itertools.product(window, repeat=2)
                if isinstance(_perturbed_fold(a, b, wl._WEYL, two_walls),
                              str))
    clean = sum(1 for a, b in itertools.product(window, repeat=2)
                if isinstance(_perturbed_fold(a, b, wl._WEYL,
                                              wl.A2_POSITIVE_ROOTS), str))
    assert leaks > 0, (
        "the two-wall variant produced no failure at all — either the "
        "perturbation is not reaching the fold or A2 grew a fourth wall")
    assert clean == 0, (
        f"the SHIPPED three-wall fold failed on {clean} of "
        f"{len(window) ** 2} pairs; the red proof is only meaningful "
        f"against a green baseline")


# ══════════════════════════════════════════════════════════════════════
# 6. ORACLE (a) — Littlewood–Richardson, sharing no code with the fold
# ══════════════════════════════════════════════════════════════════════

def _lattice_word_ok(word, n_letters):
    """The LR lattice condition, on the REVERSE READING WORD.

    ⚠️ Checking this in PLACEMENT order instead is wrong in the PERMISSIVE
    direction — it accepts fillings the rule forbids, which manufactures
    agreement rather than testing for it.  That is what the first draft of
    this control did (192 false disagreements over 256 pairs), and it is
    recorded because a control that fails permissively is worse than no
    control at all.
    """
    counts = [0] * (n_letters + 2)
    for letter in word:
        counts[letter] += 1
        if letter > 1 and counts[letter] > counts[letter - 1]:
            return False
    return True


def _count_lr_tableaux(lam, nu, mu, n_letters):
    """Count LR skew tableaux of shape ``nu/lam`` with content ``mu``."""
    rows = len(nu)
    grid = [[0] * (nu[0] + 1) for _ in range(rows)]
    found = [0]

    def fill_row(r, word, content):
        if r == rows:
            if list(content[1:n_letters + 1]) == list(mu[:n_letters]):
                found[0] += 1
            return
        cells = list(range(lam[r], nu[r]))
        entries = []

        def fill_cell(idx, lowest):
            if idx == len(cells):
                extended = word + entries[::-1]   # reverse reading word
                if _lattice_word_ok(extended, n_letters):
                    fill_row(r + 1, extended, content)
                return
            col = cells[idx]
            for entry in range(lowest, n_letters + 1):
                if content[entry] >= mu[entry - 1]:
                    continue
                if r > 0 and lam[r - 1] <= col < nu[r - 1]:
                    if entry <= grid[r - 1][col]:
                        continue      # column strictness
                grid[r][col] = entry
                entries.append(entry)
                content[entry] += 1
                fill_cell(idx + 1, entry)     # rows weakly increase
                content[entry] -= 1
                entries.pop()

        fill_cell(0, 1)

    fill_row(0, [], [0] * (n_letters + 2))
    return found[0]


def _lr_products(lam, mu, max_rows=3):
    total = sum(mu)
    letters = len([x for x in mu if x > 0])
    out = {}

    def shapes(i, prev, remaining, acc):
        if i == max_rows:
            if remaining == 0:
                yield tuple(acc)
            return
        for value in range(lam[i], min(prev, lam[i] + remaining) + 1):
            yield from shapes(i + 1, value, remaining - (value - lam[i]),
                              acc + [value])

    for nu in shapes(0, 10 ** 9, total, []):
        if letters == 0:
            out[nu] = 1
            continue
        count = _count_lr_tableaux(list(lam), list(nu),
                                   [x for x in mu if x > 0], letters)
        if count:
            out[nu] = count
    return out


def _label_to_partition(label):
    return (label[0] + label[1], label[1], 0)


def _partition_to_label(part):
    return (part[0] - part[1], part[1] - part[2])


def test_ORACLE_littlewood_richardson_agrees_on_the_whole_window():
    """SECOND OPINION, sharing NO code with the fold.

    Per `[[user_stance_co_equal_dual_construction_is_a_consistency_oracle]]`
    the DISAGREEMENT would be the finding.  There is none over 256 pairs.
    """
    disagreements = []
    for a, b in itertools.product(LABELS, repeat=2):
        want = _cell(a, b)
        got = {}
        for nu, mult in _lr_products(_label_to_partition(a),
                                     _label_to_partition(b)).items():
            key = _partition_to_label(nu)
            got[key] = got.get(key, 0) + mult
        got = {k: v for k, v in got.items() if v}
        if got != want:
            disagreements.append((a, b, got, want))
    assert disagreements == [], disagreements[:3]


def test_ORACLE_the_LR_control_can_disagree():
    """The control is only evidence if it is capable of reporting a
    disagreement.  Fed a DELIBERATELY WRONG expectation it must not agree —
    otherwise the green above measures nothing."""
    lr = _lr_products(_label_to_partition((1, 0)),
                      _label_to_partition((1, 0)))
    got = {_partition_to_label(nu): m for nu, m in lr.items()}
    assert got != {(0, 1): 1}            # missing the 6
    assert got != {(2, 0): 1}            # missing the 3-bar
    assert got == {(0, 1): 1, (2, 0): 1}


def test_ORACLE_weight_system_convolution_identity():
    """SECOND OPINION (b): ``m_{a⊗b} = Σ_ν N^ν · m_ν`` on the FULL weight
    multiset — a different equation on a different object from the fold.

    ⚠️ SCOPED: this is a second EQUATION, **not** a code-disjoint control, and
    the two are not the same kind of evidence.  :func:`_full_weight_system`
    expands orbits through ``wl._weyl_orbit`` — the module's OWN Weyl code,
    the same machinery the fold under test uses — so a fault in the Weyl
    action could in principle move both sides of this identity together.  The
    genuinely code-disjoint oracle in this file is the Littlewood–Richardson
    count (#3 in the header), which shares nothing with the fold; that is the
    one carrying the co-equal-dual-construction claim, and this one earns its
    place as an independent LAW rather than an independent IMPLEMENTATION.
    Recorded so the pair is not read as two controls of equal strength.
    """
    disagreements = []
    for a, b in itertools.product(LABELS, repeat=2):
        wa, wb = _full_weight_system(a), _full_weight_system(b)
        product = {}
        for x, mx in wa.items():
            for y, my in wb.items():
                key = (x[0] + y[0], x[1] + y[1])
                product[key] = product.get(key, 0) + mx * my
        rebuilt = {}
        for p, q, m in tensor_product_multiplicities(a, b)["constituents"]:
            for weight, mult in _full_weight_system((p, q)).items():
                rebuilt[weight] = rebuilt.get(weight, 0) + m * mult
        if ({k: v for k, v in product.items() if v}
                != {k: v for k, v in rebuilt.items() if v}):
            disagreements.append((a, b))
    assert disagreements == [], disagreements[:3]


# ══════════════════════════════════════════════════════════════════════
# 7. ORACLE (b) — PSL(2,7), through the SHIPPED finite-group ops
# ══════════════════════════════════════════════════════════════════════

def _psl2_7_cayley_table():
    """PSL(2,7) as SL(2,7)/{±I}.

    ⚠️ HAND-ROLLED, AND THAT IS A GENUINE GAP, NOT AN EXCEPTION.  srmech
    ships ``cyclic_group`` + ``semidirect_product`` and cannot construct a
    simple group — see
    :func:`test_the_psl2_constructor_gap_is_recorded_not_hidden`.
    """
    p = 7
    elements = [(a, b, c, d)
                for a in range(p) for b in range(p)
                for c in range(p) for d in range(p)
                if (a * d - b * c) % p == 1]
    assert len(elements) == 336, len(elements)

    def canonical(m):
        return min(m, tuple((-x) % p for x in m))

    classes = sorted({canonical(m) for m in elements})
    assert len(classes) == 168, len(classes)
    index = {c: i for i, c in enumerate(classes)}

    def mul(x, y):
        return ((x[0] * y[0] + x[1] * y[2]) % p,
                (x[0] * y[1] + x[1] * y[3]) % p,
                (x[2] * y[0] + x[3] * y[2]) % p,
                (x[2] * y[1] + x[3] * y[3]) % p)

    return [[index[canonical(mul(classes[i], classes[j]))]
             for j in range(168)] for i in range(168)]


def _trivial_row(ct):
    """The trivial character's row index, located BY CONTENT.

    ⚠️ Rows sort ``(degree, lex)``; index 0 is not the trivial row in
    general (it is index 2 for F21).  The trivial row is the degree-1 row
    whose every value is the ring's 1.
    """
    one = (1,) + (0,) * (ct["degree"] - 1)
    rows = [i for i in range(ct["k"])
            if ct["degrees"][i] == 1
            and all(tuple(ct["table"][i][j]) == one for j in range(ct["k"]))]
    assert len(rows) == 1, rows
    return rows[0]


@pytest.fixture(scope="module")
def psl27():
    table = _psl2_7_cayley_table()
    ct = character_table(table)
    return {"table": table, "ct": ct,
            "fs": frobenius_schur_indicator(ct),
            "fusion": fusion_multiplicities(ct)["multiplicities"]}


def test_the_psl27_presentation_is_the_group_it_claims(psl27):
    """Degrees ``[1,3,3,6,7,8]`` and ``Σd² = 168`` — the shipped ops
    identifying the hand-rolled table, so a wrong presentation cannot ride
    into the oracle below."""
    ct = psl27["ct"]
    assert ct["order"] == 168
    assert ct["degrees"] == [1, 3, 3, 6, 7, 8]
    assert sum(d * d for d in ct["degrees"]) == 168


def test_the_two_complex_triplets_are_a_chirality_pair(psl27):
    """FS indicators ``[1,0,0,1,1,1]`` — the two degree-3 rows are ν=0, i.e.
    genuinely COMPLEX, which is P1's clause and the reason this group is the
    oracle for a genuinely complex ``3``."""
    assert psl27["fs"]["indicators"] == (1, 0, 0, 1, 1, 1)
    complex_triplets = [i for i in range(psl27["ct"]["k"])
                        if psl27["ct"]["degrees"][i] == 3
                        and psl27["fs"]["indicators"][i] == 0]
    assert len(complex_triplets) == 2


def test_ORACLE_the_psl27_CELL_reproduces_three_tensor_three(psl27):
    """⚠️ NAMED FOR THE CELL, NOT FOR THE OP.

    PSL(2,7)'s degree-3 self-fusion reproduces SU(3)'s ``3 ⊗ 3 = 3̄ ⊕ 6``:
    the OTHER degree-3 row at multiplicity 1, EXACTLY one degree-6
    constituent, the spurious same-row channel at EXACTLY 0, and
    ``⟨χ³, 1⟩ = 1``.  Asserting P1 ∧ P2 as a CONJUNCTION is load-bearing:
    ``⟨χ³,1⟩ = 1`` alone is also true of the TRIVIAL row, so the predicate
    discriminates only as a conjunction.

    ⚠️ DO NOT "SIMPLIFY" THIS INTO A PINNED VECTOR.  It is tempting to
    replace the content lookups below with the literal ``N[a][a] ==
    [0, 0, 1, 1, 0, 0]``, and that literal is only true of ONE of the two
    rows.  Measured on this table: row 1 gives ``[0, 0, 1, 1, 0, 0]`` and
    row 2 gives ``[0, 1, 0, 1, 0, 0]`` — both are the same STRUCTURE (the
    other degree-3 once, one degree-6 once, self-channel zero) expressed at
    different indices, because each row's ``3-bar`` is the OTHER row.  A
    per-index literal would pass on row 1 and fail on row 2 while nothing
    is wrong, which is precisely the by-index reading the header forbids.
    """
    ct, fusion = psl27["ct"], psl27["fusion"]
    degrees, trivial = ct["degrees"], _trivial_row(ct)
    triplets = [i for i in range(ct["k"])
                if degrees[i] == 3 and psl27["fs"]["indicators"][i] == 0]
    for row in triplets:
        self_fusion = fusion[row][row]
        assert self_fusion[row] == 0, "the spurious same-row channel"
        other = [i for i in triplets if i != row][0]
        assert self_fusion[other] == 1, "the 3-bar, once"
        six = [i for i in range(ct["k"])
               if degrees[i] == 6 and self_fusion[i]]
        assert len(six) == 1 and self_fusion[six[0]] == 1
        cube = sum(self_fusion[c] * fusion[c][row][trivial]
                   for c in range(ct["k"]))
        assert cube == 1, "<chi^3, 1>"

    lattice = _cell((1, 0), (1, 0))
    # REPEAT the dimension by multiplicity; do NOT scale it.  ``dim * mult``
    # maps ``3bar + 2x3`` — i.e. ``{(0,1): 1, (1,0): 2}`` — onto the SAME
    # ``[3, 6]`` this cell exists to be distinguished from, and that imposter
    # also satisfies the ``3*3 = 9`` dimension law, so nothing else here would
    # catch it.  Measured: the scaled form accepts it, the repeated form gives
    # ``[3, 3, 3]`` and rejects it.  The two sibling helpers below (the degree
    # multisets) already repeat rather than scale; this line was the outlier.
    dims = []
    for (p, q), m in lattice.items():
        dims += [dominant_weight(p, q)["dimension"]] * m
    assert sorted(dims) == [3, 6]


def test_P2_ALONE_DOES_NOT_DISCRIMINATE(psl27):
    """The pin that stops the conjunction from drifting into P2 alone:
    ``⟨χ³, 1⟩ = 1`` holds for the TRIVIAL row too, whose FS indicator is +1
    and which is therefore excluded by P1, not by P2."""
    ct, fusion = psl27["ct"], psl27["fusion"]
    trivial = _trivial_row(ct)
    self_fusion = fusion[trivial][trivial]
    cube = sum(self_fusion[c] * fusion[c][trivial][trivial]
               for c in range(ct["k"]))
    assert cube == 1
    assert psl27["fs"]["indicators"][trivial] == 1     # P1 excludes it


def test_WHERE_THE_PSL27_ORACLE_STOPS(psl27):
    """⚠️ THE SCOPE OF THE ORACLE, PINNED SO IT CANNOT BE OVER-READ.

    Restriction su(3) → PSL(2,7) is MANY-TO-ONE, so the correspondence holds
    at tensor power 2 and BREAKS at 3 and 4 — measured, not assumed.  The
    totals still agree (9 / 27 / 81) because restriction preserves
    dimension; it is the DECOMPOSITION that diverges.  Consequently any cell
    containing the 10 or the 27 — including ``8 ⊗ 8`` — is UNVALIDATABLE
    here, and a test claiming otherwise would be over-reading it.
    """
    ct, fusion = psl27["ct"], psl27["fusion"]
    degrees, trivial = ct["degrees"], _trivial_row(ct)
    triplet = [i for i in range(ct["k"])
               if degrees[i] == 3 and psl27["fs"]["indicators"][i] == 0][0]

    def lattice_power(n):
        channels = {(0, 0): 1}
        for _ in range(n):
            channels = _fuse_dict(channels, (1, 0))
        out = []
        for (p, q), m in sorted(channels.items()):
            out += [dominant_weight(p, q)["dimension"]] * m
        return sorted(out)

    def psl_power(n):
        vector = [0] * ct["k"]
        vector[trivial] = 1
        for _ in range(n):
            nxt = [0] * ct["k"]
            for i, m in enumerate(vector):
                if m:
                    for c in range(ct["k"]):
                        nxt[c] += m * fusion[i][triplet][c]
            vector = nxt
        out = []
        for i, m in enumerate(vector):
            out += [degrees[i]] * m
        return sorted(out)

    assert lattice_power(2) == psl_power(2) == [3, 6]
    assert lattice_power(3) == [1, 8, 8, 10]
    assert psl_power(3) == [1, 3, 7, 8, 8]
    assert lattice_power(3) != psl_power(3)
    assert lattice_power(4) != psl_power(4)
    for n in (2, 3, 4):
        assert sum(lattice_power(n)) == sum(psl_power(n)) == 3 ** n
    assert 10 not in degrees and 27 not in degrees


def test_the_psl2_constructor_gap_is_recorded_not_hidden():
    """OPEN GAP ROW — ``psl2(q)`` is the missing constructor.

    srmech cannot construct a simple group: the shipped constructors are
    ``cyclic_group`` and ``semidirect_product``, and every semidirect product
    of two cycles has a normal subgroup by construction.  The PSL(2,7) table
    above is therefore test-local.  This asserts the GAP so it stays visible
    — when ``psl2`` ships, this test fails and the hand-roll comes out.
    """
    import srmech.math.groups as groups
    assert not hasattr(groups, "psl2"), (
        "srmech.math.groups.psl2 now exists — replace the hand-rolled "
        "PSL(2,7) presentation in this file with it and delete this gap row")
    assert groups.semidirect_product(
        cyclic_group(3)["cayley_table"], cyclic_group(2)["cayley_table"],
        [[0, 1, 2], [0, 2, 1]])["order"] == 6


# ══════════════════════════════════════════════════════════════════════
# 8. THE ABELIAN DEGENERATE CASE — the free negative control
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("n", [2, 3, 4, 5, 6, 7])
def test_for_an_ABELIAN_group_fusion_is_ADDITION_in_the_dual(n):
    """FREE NEGATIVE CONTROL, and it checks that the whole picture reduces.

    For an abelian group the character table IS the generalized
    Walsh–Hadamard transform and fusion is ADDITION in the dual group, so
    ``N_abc = [a + b == c]`` once rows are indexed by their DUAL-GROUP
    element rather than by payload row order (rows sort ``(degree, lex)``,
    which is not the dual order — locating by index here would be the exact
    row-location defect this stratum keeps warning about).

    The dual index of row ``i`` is the ``d`` with ``χ_i(g) = ζ_n^d`` for the
    generator ``g``, recovered through the SHIPPED :func:`zeta_mul` rather
    than a hand-rolled cyclotomic power.
    """
    ct = character_table(cyclic_group(n)["cayley_table"])
    assert ct["k"] == n, "an abelian group has |G| classes"
    fusion = fusion_multiplicities(ct)["multiplicities"]

    phi = list(ct["phi_e"])
    width = ct["degree"]
    if width == 1:
        zeta = (-phi[0],)
    else:
        zeta = tuple(1 if i == 1 else 0 for i in range(width))
    powers = []
    current = tuple(1 if i == 0 else 0 for i in range(width))
    for _ in range(n):
        powers.append(current)
        current = zeta_mul(current, zeta, phi)

    generator_class = ct["class_of"][1]
    dual = []
    for i in range(n):
        value = tuple(ct["table"][i][generator_class])
        matches = [d for d in range(n) if powers[d] == value]
        assert len(matches) == 1, (i, value, matches)
        dual.append(matches[0])
    assert sorted(dual) == list(range(n)), "the dual index is a bijection"

    for a in range(n):
        for b in range(n):
            for c in range(n):
                want = 1 if (dual[a] + dual[b]) % n == dual[c] else 0
                assert fusion[a][b][c] == want, (n, a, b, c)


# ══════════════════════════════════════════════════════════════════════
# 9. CARRIER + DISCIPLINE — no float, no abs, no new type
# ══════════════════════════════════════════════════════════════════════

def test_every_returned_value_is_an_exact_int():
    """The type census that justifies "no new carrier TYPE, therefore no
    discriminator widening and no C obligation"."""
    def walk(value, path):
        if isinstance(value, bool):
            raise AssertionError(f"bool on an integer lane at {path}")
        if isinstance(value, int):
            return
        if isinstance(value, str):
            return
        if isinstance(value, (tuple, list)):
            for i, item in enumerate(value):
                walk(item, f"{path}[{i}]")
            return
        if isinstance(value, dict):
            for key, item in value.items():
                walk(item, f"{path}.{key}")
            return
        raise AssertionError(f"unexpected carrier {type(value).__name__} "
                             f"at {path}")

    walk(dominant_weight(2, 1), "dominant_weight")
    walk(weight_multiplicities(2, 1), "weight_multiplicities")
    walk(tensor_product_multiplicities((2, 1), (1, 1)), "fusion")


def test_the_module_uses_no_abs_and_no_float():
    """Source-level discipline: sign-handling is the explicit Class-K Weyl
    determinant ledger, never an ALU magnitude call."""
    import inspect
    source = inspect.getsource(wl)
    assert "abs(" not in source, "abs() is banned — Class K + Class C"
    assert "float(" not in source
    assert "hashlib" not in source, "route through sha256_bytes"
    assert "import math" not in source


def test_the_weyl_reflections_ride_the_exact_QMat_carrier():
    """QMat is load-bearing, not decorative: the ±1 sign ledger IS the
    determinant, read through the exact-ℚ carrier."""
    from srmech.math.qmat import QMat
    for matrix, sign in wl._WEYL:
        value = QMat([[matrix[0][0], matrix[0][1]],
                      [matrix[1][0], matrix[1][1]]]).det()
        assert value.denominator == 1
        assert value.numerator == sign


def test_content_addresses_are_stable_and_distinguishing():
    for op, args in ((dominant_weight, (2, 1)),
                     (weight_multiplicities, (2, 1))):
        assert op(*args) == op(*args)
    assert (weight_multiplicities(2, 1)["weights_sha256"]
            != weight_multiplicities(1, 2)["weights_sha256"])
    assert (tensor_product_multiplicities((1, 0), (1, 0))["fusion_sha256"]
            != tensor_product_multiplicities((1, 0), (0, 1))["fusion_sha256"])


def test_the_registry_carries_all_three_ops_under_their_own_category():
    from srmech.introspect.tool_schema import get_tool_schema
    rows = {e.name: e for e in get_tool_schema().tools
            if e.name.startswith("srmech.math.weight_lattice.")}
    assert set(rows) == {
        "srmech.math.weight_lattice.dominant_weight",
        "srmech.math.weight_lattice.weight_multiplicities",
        "srmech.math.weight_lattice.tensor_product_multiplicities"}
    for entry in rows.values():
        assert entry.owner == "srmech"
        assert entry.category == "weight_lattice"
        assert "srmech.amsc.format.sha256_bytes" in entry.composes


def test_EVERY_one_of_the_three_ops_carries_the_exact_Z_guarantee():
    """Per-op, because the taxonomy next door cannot be per-op.

    ``tests/test_preserves_taxonomy_rc423.py`` keys its classification by the
    WHOLE invariant string, which is the right design for what it does — but it
    therefore answers only "is this sentence shipped by SOMEBODY", never "does
    THIS op still make this promise".  Both the rc460 string and its weaker
    pre-rc460 sibling (``numpy-free; no abs() ...``, without the ``exact ℤ``
    clause) are classified there, so the two are interchangeable as far as that
    gate can see.

    Measured on this tree: downgrading ALL THREE ops to the weaker sibling does
    go red — the rc460 string becomes shipped by nobody and the dead-row check
    catches it.  Downgrading exactly ONE does not: the string stays alive via
    the other two, and the taxonomy plus the full weight-lattice suite report
    **88 passed**.  So the guarantee the rc's own comment calls "the half the rc
    exists to guarantee" could be dropped from ``dominant_weight`` alone and
    every board stayed green.

    This closes that: the clause is bound to each op individually, so a partial
    downgrade fails and names the op that dropped it.
    """
    from srmech.introspect.tool_schema import get_tool_schema
    rows = {e.name: e for e in get_tool_schema().tools
            if e.name.startswith("srmech.math.weight_lattice.")}
    assert len(rows) == 3, rows
    missing = sorted(
        name for name, entry in rows.items()
        if not any("exact ℤ" in s for s in entry.preserves))
    assert not missing, (
        f"{len(missing)} of the 3 weight-lattice ops no longer declare the "
        f"exact-ℤ guarantee in `preserves`: {missing}. The whole carrier claim "
        f"of this stratum is that Racah–Speiser and Freudenthal stay in the "
        f"integers end to end — the Gram matrix is carried 3-SCALED so the "
        f"recursion never leaves ℤ, and every division is a guarded "
        f"`_exact_div` that RAISES on a remainder. If an op genuinely stopped "
        f"guaranteeing that, the DOCSTRING and the code must change too; do "
        f"not quietly relax the string.")


def test_the_class_NON_CLAIMS_are_stated_in_the_shipped_prose():
    """The two non-claims are the rc's load-bearing correction, so they are
    gated rather than trusted to survive an edit."""
    assert "NOT Class K" in weight_multiplicities.__doc__
    assert "NOT Class L" in tensor_product_multiplicities.__doc__
    from srmech.introspect.tool_schema import get_tool_schema
    rows = {e.name: e for e in get_tool_schema().tools}
    assert "NOT Class K" in rows[
        "srmech.math.weight_lattice.weight_multiplicities"].summary
    assert "NOT Class L" in rows[
        "srmech.math.weight_lattice.tensor_product_multiplicities"].summary


# ══════════════════════════════════════════════════════════════════════
# 10. B1 — the group bind, and the 60-pair census it closes
# ══════════════════════════════════════════════════════════════════════

def _f21_table():
    """C7 ⋊ C3 by multiplication-by-2 — order 21, NON-abelian, degrees
    [1,1,1,3,3]."""
    return semidirect_product(
        cyclic_group(7)["cayley_table"], cyclic_group(3)["cayley_table"],
        [[(pow(2, h, 7) * a) % 7 for a in range(7)] for h in range(3)]
    )["cayley_table"]


def test_character_table_emits_the_group_bind():
    table = cyclic_group(6)["cayley_table"]
    ct = character_table(table)
    assert "cayley_sha256" in ct
    rep = permutation_representation(table, table)
    assert ct["cayley_sha256"] == rep["cayley_sha256"], (
        "the char table and a rep of the SAME group must share the address")


def test_B1_the_replicated_silent_wrong_answer_now_RAISES():
    """THE DEFECT, REPRODUCED AND CLOSED.

    Through rc459 ``decompose_representation(regular rep of C21,
    character_table of F21)`` returned ``(1, 1, 1, 3, 3)`` — with no raise
    and no warning.  C21 is ABELIAN, so a 3-dimensional constituent is
    impossible, and the dimension law passed anyway (Σ mᵢdᵢ = 21) because the
    regular character is ``(|G|, 0, …, 0)`` for EVERY group.  The payload even
    carried both content addresses side by side; nothing compared them.
    """
    c21 = cyclic_group(21)["cayley_table"]
    f21 = _f21_table()
    rep = permutation_representation(c21, c21)
    ct = character_table(f21)
    assert ct["degrees"] == [1, 1, 1, 3, 3]
    assert character_table(c21)["degrees"] == [1] * 21   # C21 is abelian
    for op in (character_of, decompose_representation, isotypic_projector):
        with pytest.raises(ValueError, match="group-bind law"):
            op(rep, ct)


def test_B1_the_census_that_measured_it_is_now_silent_free():
    """The census the fix is sized against: every ordered same-order pair of
    distinct groups, regular representations, must RAISE.  Through rc459,
    42 of 60 such pairs returned a DIFFERENT answer with no signal, and only
    15% broke class-constancy — the law the shipped docstring called the
    "usually" firing detector."""
    c2 = cyclic_group(2)["cayley_table"]
    c3 = cyclic_group(3)["cayley_table"]
    c4 = cyclic_group(4)["cayley_table"]
    identity4 = [list(range(4))] * 2
    groups = {
        "C6": cyclic_group(6)["cayley_table"],
        "S3": semidirect_product(c3, c2, [[0, 1, 2], [0, 2, 1]])[
            "cayley_table"],
        "C8": cyclic_group(8)["cayley_table"],
        "D4": semidirect_product(c4, c2, [[0, 1, 2, 3], [0, 3, 2, 1]])[
            "cayley_table"],
        "C2xC4": semidirect_product(c4, c2, identity4)["cayley_table"],
        "C12": cyclic_group(12)["cayley_table"],
        "D6": semidirect_product(
            cyclic_group(6)["cayley_table"], c2,
            [list(range(6)), [(-x) % 6 for x in range(6)]])["cayley_table"],
        "C21": cyclic_group(21)["cayley_table"],
        "F21": _f21_table(),
    }
    tables = {n: character_table(t) for n, t in groups.items()}
    reps = {n: permutation_representation(t, t) for n, t in groups.items()}

    addresses = {n: ct["cayley_sha256"] for n, ct in tables.items()}
    assert len(set(addresses.values())) == len(addresses), (
        "the bind is only sufficient if distinct groups get distinct "
        "addresses")

    pairs = silent = 0
    for a, b in itertools.permutations(groups, 2):
        if len(groups[a]) != len(groups[b]):
            continue
        pairs += 1
        try:
            decompose_representation(reps[a], tables[b])
            silent += 1
        except ValueError as exc:
            assert "group-bind law" in str(exc), (a, b, str(exc))
    assert pairs > 0
    assert silent == 0, f"{silent} of {pairs} cross-group pairs still silent"


def test_the_honest_path_is_untouched():
    """A bind that also breaks the correct call is not a fix.  On its OWN
    table, the regular representation still decomposes as ``mᵢ = dᵢ``."""
    for table in (cyclic_group(6)["cayley_table"],
                  cyclic_group(21)["cayley_table"], _f21_table()):
        ct = character_table(table)
        rep = permutation_representation(table, table)
        out = decompose_representation(rep, ct)
        assert out["multiplicities"] == tuple(out["degrees"])


def test_the_order_law_is_still_REACHABLE():
    """The escalation is shape → SIZE → IDENTITY on purpose.  The bind
    subsumes the order law mathematically, so putting it first would leave
    the coarser mistake with only the finer message; this asserts a
    different-ORDER pair still reports the order law."""
    ct = character_table(cyclic_group(6)["cayley_table"])
    rep = permutation_representation(cyclic_group(4)["cayley_table"],
                                     cyclic_group(4)["cayley_table"])
    with pytest.raises(ValueError, match="order law"):
        character_of(rep, ct)


def test_the_MEASURED_correction_to_the_usually_caveat_is_shipped():
    """The shipped prose said class-constancy "usually" catches a
    cross-group pair, and that it was "a DETECTOR, not a proof".  Measured:
    15%.  The falsehood must be gone from the docstring AND from the
    registry summary, which SHIPS in the wheel and reaches users through
    describe() and the MCP tool list."""
    doc = character_of.__doc__
    assert "usually break class-constancy" not in doc
    assert "group-bind law" in doc
    from srmech.introspect.tool_schema import get_tool_schema
    summary = {e.name: e.summary for e in get_tool_schema().tools}[
        "srmech.math.groups.character_of"]
    assert "a detector, not a proof" not in summary
    assert "GROUP-BIND law" in summary


def test_table_sha256_is_NOT_a_group_identity_which_is_why_the_bind_is_new():
    """The alternative ruled out on its field: ``table_sha256`` addresses the
    CHARACTER MATRIX BODY, not the group.  D4 and Q8 famously share a
    character matrix; whether they happen to collide here depends on class
    ORDERING, which is census order — contingent, not designed.  The
    principled point stands without the collision: it addresses the wrong
    object, and this asserts the two addresses are genuinely different
    fields rather than aliases."""
    table = cyclic_group(6)["cayley_table"]
    ct = character_table(table)
    assert ct["table_sha256"] != ct["cayley_sha256"]
    other = character_table(
        semidirect_product(cyclic_group(3)["cayley_table"],
                           cyclic_group(2)["cayley_table"],
                           [[0, 1, 2], [0, 2, 1]])["cayley_table"])
    assert ct["cayley_sha256"] != other["cayley_sha256"]


def test_the_payload_key_law_now_requires_the_bind():
    """A key that is optional cannot be a bind."""
    ct = character_table(cyclic_group(4)["cayley_table"])
    stripped = {k: v for k, v in ct.items() if k != "cayley_sha256"}
    assert "cayley_sha256" in ct
    with pytest.raises(ValueError, match="payload-key law"):
        fusion_multiplicities(stripped)
