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




# ──────────────────────────────────────────────────────────────────────
# 8. `returns=` HONESTY — the axis the shipped gates cannot reach here
#
# `tests/test_immolation.py::test_advertised_return_type_is_honest` and
# `test_mcp.py`'s §10.1 smoke both drive ops through `_synth_args_for_entry`,
# which builds arguments from the TYPE STRING alone (`int -> 1`, `str -> "a"`,
# `list[list[int]] -> [[1, 2], [3]]`). Every one of this rc's six ops rejects
# that synth with a DOMAIN ValueError — `n >= 2`, a table index out of range,
# `convention` not one of the allowed labels — and both gates TOLERATE a
# domain error, returning before the return type is ever inspected.
#
# So those gates are GREEN AND VACUOUS on all six: they contribute zero
# return-type coverage, and if a later rc changed one of these return types
# nothing would notice. The general repair is to let `smoke_test_hint` drive
# synth (it is currently consumed by NOTHING but the schema parser), which
# moves the synth arguments of the whole registry at once and belongs in its
# own rc. Until then this file carries the axis for its own ops with REAL
# arguments, so the coverage is committed rather than a hand-run that vanished
# with the session that did it.
# ──────────────────────────────────────────────────────────────────────

from conftest import return_type_agrees        # noqa: E402  (shared helper)

_REAL_CALLS = {
    "srmech.math.cyclic.mod_mul_arrow": lambda: mod_mul_arrow(2, 12),
    "srmech.cascade.finite_semiflow": lambda: finite_semiflow([0, 1, 2, 3, 0, 1, 2, 3]),
    "srmech.cascade.conjugacy_census":
        lambda: conjugacy_census(dihedral_group(5, "reflection_first")["cayley_table"]),
    "srmech.cascade.reversal_law_census":
        lambda: reversal_law_census(dihedral_group(5, "reflection_first")["cayley_table"]),
    "srmech.cascade.anti_automorphism_witnesses":
        lambda: anti_automorphism_witnesses(unit_loop(4)["cayley_table"]),
    "srmech.cascade.dihedral_group": lambda: dihedral_group(5, "reflection_first"),
    "srmech.cascade.unit_loop": lambda: unit_loop(4, table=algebra_table(4)),
    "srmech.cascade.loop_invariants": lambda: loop_invariants(4, table=algebra_table(4)),
}

_JSON_NATIVE = (dict, list, str, int, float, bool, type(None))


def _entry(name: str):
    from srmech.introspect.tool_schema import get_tool_schema
    hits = [t for t in get_tool_schema().tools if t.name == name]
    assert len(hits) == 1, f"{name} is not registered exactly once: {len(hits)}"
    return hits[0]


def _non_json_native(value, path="$"):
    """Every leaf that is NOT a JSON-native type, with the path that reached
    it — a list, so the failure NAMES the offending field."""
    bad = []
    if isinstance(value, dict):
        for k, v in value.items():
            if not isinstance(k, (str, int)):
                bad.append(f"{path}.<key {k!r}: {type(k).__name__}>")
            bad.extend(_non_json_native(v, f"{path}.{k}"))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            bad.extend(_non_json_native(v, f"{path}[{i}]"))
    elif not isinstance(value, _JSON_NATIVE):
        bad.append(f"{path}: {type(value).__name__}")
    return bad


@pytest.mark.parametrize("name", sorted(_REAL_CALLS))
def test_advertised_return_type_is_honest_on_real_args(name: str) -> None:
    """The advertised ``returns.type`` against the type actually returned.

    Driven by REAL arguments, so unlike the registry-wide gates this reaches
    the return value instead of stopping at a tolerated domain error.
    """
    advertised = _entry(name).returns.type
    observed = _REAL_CALLS[name]()
    verdict = return_type_agrees(observed, advertised)
    assert verdict is not None, (
        f"{name}: the advertised return type {advertised!r} carries no "
        f"assertable token, so this check would pass vacuously — the exact "
        f"failure mode this section exists to close. Make the type assertable "
        f"rather than deleting the assertion.")
    assert verdict, (
        f"{name} advertises returns.type={advertised!r} but returned "
        f"{type(observed).__name__}")


@pytest.mark.parametrize("name", sorted(_REAL_CALLS))
def test_the_real_arg_result_is_wire_representable(name: str) -> None:
    """Each of these returns a dict that must cross the MCP wire. The
    registry-wide serialisation smoke is downstream of a clean return, so it
    never runs for these ops either."""
    from srmech.mcp._coercion import serialise_native
    observed = serialise_native(_REAL_CALLS[name]())
    bad = _non_json_native(observed)
    assert not bad, f"{name}: non-JSON-native leaves after serialise_native: {bad[:5]}"


def test_the_return_type_instrument_can_return_false() -> None:
    """NON-VACUITY CONTROL. The tests above are evidence only if the helper
    reports disagreement when there is some — an instrument that cannot return
    otherwise is not a measurement."""
    assert return_type_agrees({"a": 1}, "dict") is True
    assert return_type_agrees([1, 2], "dict") is False
    assert return_type_agrees(7, "dict") is False


def test_the_wire_instrument_can_return_false() -> None:
    """NON-VACUITY CONTROL for the serialisation walk — an un-serialised ``Q``
    is exactly the leaf ``serialise_native`` exists to flatten."""
    assert _non_json_native({"ok": [1, "a", None, True]}) == []
    found = _non_json_native({"bad": Q(1, 2)})
    assert found and found[0].startswith("$.bad:"), found


# EMPTY since rc430 — and the empty set is the RESULT, not a disabled check.
#
# Through rc429 this held the SIX ops new in rc427: each took a required
# argument whose type-synthesised value was out of domain, so the registry-wide
# gates stopped before ever reaching a return value. rc430's `#T1094` work
# replaced the type-driven fall-through with arguments HARVESTED from each op's
# own `example["worked"]` — a value from a call that returned is in-domain by
# construction — and all six became reachable at once. The retro-check below
# fired exactly as designed and nothing ran it, because this file is not in
# `tools/ripple_gates.txt`; it is now (rc430 repair, `#T1127`).
#
# Section 8's duplication is DELIBERATELY KEPT rather than dropped as the
# retro-check offers. Its `_REAL_CALLS` drive each op with hand-written real
# arguments, which is independent evidence from the harvested-arg path the
# registry-wide gates now use — and rc430 measured that the harvest itself can
# be wrong (a harvested `path=` pointed at a file the snippet had created, so
# the census answered differently on consecutive runs). Coverage that survives
# a defect in the harvester is worth its duplication; what is NOT worth keeping
# is duplication nobody can explain, which is what this comment removes.
_SYNTH_BLOCKED: list = []


def test_the_synth_path_really_is_the_blocked_one() -> None:
    """RETRO-CHECK, and the reason section 8 exists at all.

    Pins WHICH ops the type-driven synth cannot reach. If a later rc widens
    synth so a blocked op returns cleanly, this fails and the duplication for
    that op can be dropped — rather than sitting here forever as unexplained
    duplication whose motivation nobody can reconstruct. It fails in the other
    direction too: if a covered op STOPS being reachable, its registry-wide
    coverage has silently gone vacuous and this says so.
    """
    from test_mcp import _synth_args_for_entry            # type: ignore
    from srmech.mcp import invoke_tool

    reached, blocked = [], []
    for name in sorted(_REAL_CALLS):
        entry = _entry(name)
        try:
            invoke_tool(entry.name, _synth_args_for_entry(entry))
        except Exception:                                  # noqa: BLE001
            blocked.append(name)
            continue
        reached.append(name)
    # NON-VACUITY. `_SYNTH_BLOCKED` is empty since rc430, so `blocked == []`
    # would also hold if `_REAL_CALLS` were empty or every call raised on the
    # way in. The check is evidence only if ops were actually reached.
    assert reached, (
        "no op in _REAL_CALLS was reached by the synth path at all — the "
        "blocked-set comparison below would pass vacuously")
    assert blocked == _SYNTH_BLOCKED, (
        f"the set of ops the type-driven synth cannot reach has MOVED.\n"
        f"  expected blocked: {_SYNTH_BLOCKED}\n"
        f"  actually blocked: {blocked}\n"
        f"  reached cleanly : {reached}\n"
        "If synth widened, the registry-wide return-type gates now cover the "
        "newly-reached ops and section 8's duplication for them can go. If an "
        "op newly became UNREACHABLE, its registry-wide coverage just went "
        "vacuous and section 8 is now the only thing checking it.")
