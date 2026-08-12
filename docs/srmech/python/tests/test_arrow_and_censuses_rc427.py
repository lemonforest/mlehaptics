"""The ARROW + the CENSUSES — rc427 (`#T1130`).

Six ops and two parameter extensions, and one thesis running through all of
them: **a count agreeing is not a set agreeing.** Two prior rounds concluded
equivalence from equal counts and were wrong both times, so the assertions
below are set assertions wherever a set is the subject, and every count-level
check has its set-level twin beside it.

Three things this file is careful to be, because each has burned this project:

1. **Non-vacuous.** Every positive claim has a negative control that is
   asserted, not merely mentioned. An instrument that cannot return otherwise
   is not a measurement.
2. **Bit-identical on the defaults.** The two ``table=`` extensions must
   reproduce the shipped Cayley–Dickson results element-for-element, not
   "equivalently".
3. **numpy-free and stdlib-engine-free** — no ``math`` / ``fractions`` /
   ``decimal`` / numpy, per ``tests/test_selfhosting_import_ban.py``.
"""

from __future__ import annotations

import pytest

from srmech.cascade import (anti_automorphism_witnesses, conjugacy_census,
                            dihedral_group, finite_semiflow, loop_invariants,
                            reversal_law_census, unit_loop)
from srmech.cascade.cayley_dickson import algebra_table
from srmech.math.cyclic import mod_mul_arrow
from srmech.math.q import Q


# ──────────────────────────────────────────────────────────────────────
# 1. mod_mul_arrow — the closed form, against an INDEPENDENT oracle
# ──────────────────────────────────────────────────────────────────────

def _oracle(c: int, n: int):
    """Enumeration oracle: iterate the actual map. Shares no code with the
    closed form under test — that is the entire point of it."""
    image = list(range(n))
    index = 0
    while True:
        nxt = sorted({(c * x) % n for x in image})
        if len(nxt) == len(image):
            break
        image, index = nxt, index + 1
    step = {x: (c * x) % n for x in image}
    cur, period = dict(step), 1
    while any(cur[x] != x for x in image):
        cur = {x: step[cur[x]] for x in image}
        period += 1
    return index, period, set(image)


@pytest.mark.parametrize("n", list(range(2, 41)))
def test_the_closed_form_agrees_with_enumeration_including_the_IMAGE_SET(n: int) -> None:
    """Index, period, size AND the eventual image as a SET.

    The set check is the one that matters: a closed form can get all three
    cardinals right and still name the wrong subgroup.
    """
    for c in range(n):
        got = mod_mul_arrow(c, n)
        index, period, image = _oracle(c, n)
        assert (got["index"], got["period"], got["eventual_size"]) == \
               (index, period, len(image)), f"(c={c}, n={n})"
        predicted = set(range(0, n, got["consumed_order"])) \
            if got["consumed_order"] <= n else {0}
        assert predicted == image, (
            f"(c={c}, n={n}): the SIZES agree and the SETS do not — "
            f"predicted stride-{got['consumed_order']} subgroup {sorted(predicted)}, "
            f"measured {sorted(image)}")


def test_the_nilpotent_guard_fires_rather_than_raising() -> None:
    """⚠️ THE REGRESSION THIS OP EXISTS TO NOT HAVE.

    The specification handed to the builder gave the period as
    ``cyclic_period(c mod (n/g*), n/g*)`` with no guard. Every NILPOTENT
    multiplier has ``n/g* == 1``, and ``cyclic_period`` refuses ``n < 2``, so
    that spelling raises on its own headline example. Asserted, not assumed.
    """
    from srmech.math.primes import cyclic_period

    got = mod_mul_arrow(2, 64)
    assert (got["index"], got["eventual_modulus"], got["period"]) == (6, 1, 1)
    # The negative control: the unguarded spelling really does refuse.
    with pytest.raises(ValueError):
        cyclic_period(2 % got["eventual_modulus"], got["eventual_modulus"])
    # ... and the shipped op equally refuses the non-unit it was never given.
    with pytest.raises(ValueError):
        cyclic_period(6, 12)


def test_a_unit_multiplier_is_no_arrow_and_a_non_unit_is() -> None:
    assert mod_mul_arrow(3, 7)["is_permutation"] is True
    assert mod_mul_arrow(3, 7)["index"] == 0
    assert mod_mul_arrow(6, 12)["is_permutation"] is False
    assert mod_mul_arrow(6, 12)["index"] == 2


def test_it_refuses_a_modulus_below_two() -> None:
    with pytest.raises(ValueError):
        mod_mul_arrow(1, 1)


# ──────────────────────────────────────────────────────────────────────
# 2. finite_semiflow — the positive case AND the axiomatically-empty one
# ──────────────────────────────────────────────────────────────────────

def test_the_shipped_non_injective_self_map_is_an_arrow() -> None:
    from srmech.biology.q8 import q8_project_v4

    table = list(q8_project_v4(list(range(8))))
    got = finite_semiflow(table)
    assert got["semigroup_not_group"] is True
    assert (got["index"], got["period"], got["eventual_size"]) == (1, 1, 4)
    assert got["eventual_image"] == [0, 1, 2, 3]
    assert got["kernel_orders"] == {2: 4}


@pytest.mark.parametrize("dim", [4, 8, 16, 32])
def test_a_latin_square_row_can_never_be_an_arrow(dim: int) -> None:
    """⚠️ THE RETRACTED RATIONALE, ASSERTED AS THE BOUND IT ACTUALLY IS.

    This op was first justified by "it consumes a Cayley table ``unit_loop``
    already produces". A loop's Cayley table is a Latin square BY AXIOM, so
    EVERY row is a bijection and the op can only ever return index 0 on one.
    The claim is kept as a test rather than deleted with the rationale,
    because a bound that is asserted cannot quietly stop being true.
    """
    table = unit_loop(dim)["cayley_table"]
    for row in table:
        got = finite_semiflow(row)
        assert got["index"] == 0
        assert got["semigroup_not_group"] is False


def test_it_refuses_a_table_that_is_not_a_self_map() -> None:
    with pytest.raises(ValueError):
        finite_semiflow([0, 1, 5])            # 5 is outside [0, 3)
    with pytest.raises(ValueError):
        finite_semiflow([])


# ──────────────────────────────────────────────────────────────────────
# 3. conjugacy_census — the guard, with its numbers
# ──────────────────────────────────────────────────────────────────────

def test_the_class_equation_is_false_on_a_loop_and_the_op_says_so() -> None:
    """The silently-wrong-answer case, both carriers, exact figures."""
    m16 = conjugacy_census(unit_loop(8)["cayley_table"])
    assert m16["is_associative"] is False
    assert (m16["commuting_pairs"], m16["class_equation_pairs"]) == (88, 144)
    assert m16["class_equation_agrees"] is False

    m32 = conjugacy_census(unit_loop(16)["cayley_table"])
    assert (m32["commuting_pairs"], m32["class_equation_pairs"]) == (184, 544)
    assert m32["class_equation_agrees"] is False


def test_the_guard_is_not_vacuous_it_passes_on_real_groups() -> None:
    """The positive control. If ``class_equation_agrees`` were False
    everywhere it would carry no information at all."""
    q8 = conjugacy_census(unit_loop(4)["cayley_table"])
    assert q8["is_associative"] is True and q8["is_group"] is True
    assert q8["class_equation_agrees"] is True
    assert q8["commuting_probability"] == Q(5, 8)      # exact, and on the bound

    d12 = conjugacy_census(dihedral_group(12, "reflection_first")["cayley_table"])
    assert d12["is_group"] is True
    assert d12["class_equation_agrees"] is True
    assert d12["commuting_probability"] == Q(3, 8)


def test_the_probability_is_exact_rational_not_float() -> None:
    got = conjugacy_census(unit_loop(8)["cayley_table"])
    assert isinstance(got["commuting_probability"], Q)
    assert got["commuting_probability"] == Q(88, 256) == Q(11, 32)
    assert got["commuting_probability_str"] == "11/32"


def test_the_class_partition_is_reported_not_merely_counted() -> None:
    got = conjugacy_census(dihedral_group(12, "reflection_first")["cayley_table"])
    assert sum(len(b) for b in got["class_partition"]) == got["order"]
    assert len(got["class_partition"]) == got["k_classes"]
    assert len(got["class_partition_sha256"]) == 64


def test_it_refuses_a_non_square_table() -> None:
    with pytest.raises(ValueError):
        conjugacy_census([[0, 1], [1, 0], [0, 1]])


# ──────────────────────────────────────────────────────────────────────
# 4. The reversal censuses — counts are not sets
# ──────────────────────────────────────────────────────────────────────

def test_equal_counts_and_unequal_sets_on_M16() -> None:
    """⚠️ THE CASE THE WHOLE ROUND TURNS ON.

    Bare and chiral-flat both score 2752 of 4096 and succeed on different
    triples, 1344 each way. Both fields are asserted BECAUSE the point is
    that they disagree with each other.
    """
    got = reversal_law_census(unit_loop(8)["cayley_table"])
    assert got["triples"] == 4096
    assert got["bare_hits"] == got["chiral_flat_hits"] == 2752
    assert got["bare_equals_chiral_flat_counts_agree"] is True     # the weak read
    assert got["bare_equals_chiral_flat"] is False                 # the true one
    assert got["bare_vs_chiral_flat_left_only"] == 1344
    assert got["bare_vs_chiral_flat_right_only"] == 1344
    assert got["bare_sha256"] != got["chiral_flat_sha256"]


@pytest.mark.parametrize("label,table", [
    ("Q8", unit_loop(4)["cayley_table"]),
    ("M16", unit_loop(8)["cayley_table"]),
    ("D5", dihedral_group(5, "reflection_first")["cayley_table"]),
    ("D12", dihedral_group(12, "reflection_first")["cayley_table"]),
])
def test_the_chiral_law_is_TOTAL_so_it_is_entailed_not_measured(
        label: str, table) -> None:
    """A claim of the form "chiral reversal succeeds on exactly the
    forward-success set" is a THEOREM on these carriers, not a finding. The
    op reports that on every call so nobody re-discovers it as evidence."""
    got = reversal_law_census(table)
    assert got["chiral_is_total"] is True, label
    assert got["chiral_hits"] == got["triples"], label


def test_the_count_coincidence_is_carrier_specific() -> None:
    """The durable fact is the SET disagreement; the equal counts happen on
    exactly one carrier. Asserting the non-coincidences is what stops 2752
    being read as a property of loops in general."""
    q8 = reversal_law_census(unit_loop(4)["cayley_table"])
    assert (q8["bare_hits"], q8["chiral_flat_hits"]) == (320, 512)
    assert q8["bare_equals_chiral_flat_counts_agree"] is False

    m32 = reversal_law_census(unit_loop(16)["cayley_table"])
    assert (m32["bare_hits"], m32["chiral_flat_hits"]) == (26048, 17984)

    d12 = reversal_law_census(dihedral_group(12, "reflection_first")["cayley_table"])
    assert (d12["bare_hits"], d12["chiral_flat_hits"]) == (5184, 13824)


def test_the_half_inversion_negative_control_separates() -> None:
    """R5: half-inversion ships as a control exercised on every call rather
    than as an op nobody runs. A control that never separates is decoration."""
    for dim in (4, 8):
        got = reversal_law_census(unit_loop(dim)["cayley_table"])
        assert got["half_inversion_separates"] is True


def test_the_anti_automorphism_law_is_total_and_the_direct_law_is_a_SET_claim() -> None:
    got = anti_automorphism_witnesses(unit_loop(8)["cayley_table"])
    assert got["anti_holds_totally"] is True
    assert got["anti_hits"] == got["pairs"] == 256
    # The claim a prior round made from a COUNT equality — measured as sets.
    assert (got["direct_hits"], got["commuting_hits"]) == (88, 88)
    assert got["direct_equals_commuting"] is True
    assert got["direct_not_commuting"] == got["commuting_not_direct"] == 0
    # ... and the SETS being equal is a strictly stronger statement than the
    # counts being equal, which this carrier happens to satisfy too.
    assert got["anti_equals_commuting"] is False       # 256 != 88: not vacuous


def test_the_censuses_refuse_a_table_with_no_inverses() -> None:
    """Both laws quantify over inversion; without it there is no subject."""
    no_identity = [[0, 0], [0, 0]]
    with pytest.raises(ValueError):
        reversal_law_census(no_identity)
    with pytest.raises(ValueError):
        anti_automorphism_witnesses(no_identity)


# ──────────────────────────────────────────────────────────────────────
# 5. dihedral_group — and the honesty of its required `convention`
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("n", [1, 2, 3, 5, 6, 12])
@pytest.mark.parametrize("convention", ["reflection_first", "rotation_first"])
def test_it_really_is_a_group_of_order_2n(n: int, convention: str) -> None:
    got = dihedral_group(n, convention)
    assert got["order"] == 2 * n
    census = conjugacy_census(got["cayley_table"])
    assert census["is_group"] is True
    assert census["class_equation_agrees"] is True


def test_the_two_conventions_are_ISOMORPHIC_which_is_why_the_doc_says_labelling() -> None:
    """⚠️ The refutation, asserted.

    ``x -> x^-1`` carries one table to the other on 576/576 products of D_12,
    and the identity map does NOT — so the check can return otherwise. This
    is the evidence for documenting ``convention`` as a labelling decision
    rather than a structural one.
    """
    left = dihedral_group(12, "reflection_first")["cayley_table"]
    right = dihedral_group(12, "rotation_first")["cayley_table"]
    order = len(left)

    e = 0
    inv = [next(y for y in range(order) if left[x][y] == e) for x in range(order)]
    agree = sum(1 for a in range(order) for b in range(order)
                if inv[right[a][b]] == left[inv[a]][inv[b]])
    assert agree == order * order == 576

    identity_agree = sum(1 for a in range(order) for b in range(order)
                         if right[a][b] == left[a][b])
    assert identity_agree != order * order      # the negative control
    assert order * order - identity_agree == 360


def test_360_differing_cells_is_not_independent_evidence() -> None:
    """The other refutation: 360 == order^2 - commuting_pairs exactly, so the
    cell-difference count merely restates 'non-abelian', which the census
    already reports one field away."""
    left = dihedral_group(12, "reflection_first")["cayley_table"]
    right = dihedral_group(12, "rotation_first")["cayley_table"]
    differing = sum(1 for a in range(24) for b in range(24)
                    if left[a][b] != right[a][b])
    census = conjugacy_census(left)
    assert differing == census["order"] ** 2 - census["commuting_pairs"]


def test_it_refuses_an_unknown_convention() -> None:
    with pytest.raises(ValueError):
        dihedral_group(6, "whichever")
    with pytest.raises(ValueError):
        dihedral_group(0, "reflection_first")


# ──────────────────────────────────────────────────────────────────────
# 6. The `table=` extensions — BIT-IDENTICAL on the default
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("dim", [2, 4, 8, 16])
def test_unit_loop_table_default_is_element_for_element_identical(dim: int) -> None:
    """Not "equivalent" — identical. A carrier-plumbing parameter that
    perturbs the shipped answer is a defect, not a feature."""
    shipped = unit_loop(dim)
    through_table = unit_loop(dim, table=algebra_table(dim))
    assert shipped == through_table


def test_loop_invariants_table_default_is_identical() -> None:
    assert loop_invariants(8) == loop_invariants(8, table=algebra_table(8))


def test_the_extension_buys_a_carrier_that_was_unreachable() -> None:
    """The split octonions: a SPLIT gamma at the first rung. Before the
    parameter this loop had to be hand-rolled through ``table_product``."""
    split = algebra_table(8, gammas=(1, -1, -1))
    loop = unit_loop(8, table=split)
    assert loop["order"] == 16
    # It is still a Latin square — the loop axiom survives the split.
    for row in loop["cayley_table"]:
        assert sorted(row) == list(range(16))
    invariants = loop_invariants(8, table=split)
    assert invariants["nucleus"] == [(1, 0), (-1, 0)]
    # ... and it feeds the census, which is the point of the extension.
    census = conjugacy_census(loop["cayley_table"])
    assert census["is_associative"] is False


def test_a_non_monomial_table_is_refused_rather_than_silently_partial() -> None:
    """A signed unit loop exists only for a monomial table. Returning a
    partial loop would be the silent-wrong-answer class."""
    bad = [[[1, 0], [0, 1]], [[0, 1], [1, 1]]]     # cell (1,1) has two terms
    with pytest.raises(ValueError):
        unit_loop(2, table=bad)


# ──────────────────────────────────────────────────────────────────────
# 7. Cross-op coherence
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("n", [8, 12, 15, 16, 30, 36])
def test_the_closed_form_and_the_tabulated_peer_agree(n: int) -> None:
    """``mod_mul_arrow`` and ``finite_semiflow`` are two implementations of
    one question. Where both apply they must agree — and they share no code,
    so the agreement is a real cross-check rather than a tautology."""
    for c in range(n):
        closed = mod_mul_arrow(c, n)
        tabulated = finite_semiflow([(c * x) % n for x in range(n)])
        assert closed["index"] == tabulated["index"], (c, n)
        assert closed["period"] == tabulated["period"], (c, n)
        assert closed["eventual_size"] == tabulated["eventual_size"], (c, n)
        assert closed["is_permutation"] == tabulated["is_permutation"], (c, n)
