"""rc339 (`#967`, and the ontology half of `#965`) — introspection must report
what a limit is FOR, and the published ontology must stay tied to the carrier.

THE DEFECT
----------
``describe()["limits"]`` published exactly two numbers::

    {"cd_max_dim": 256, "cd_dense_max_dim": 64}

**Both are ADDRESSING ceilings.** The composition and turn ceilings were absent
and ``carriers`` carried no capability at all, so the self-description answered
"how big can this go?" with 256 and stayed silent on the two ceilings that
actually bind. A caller — or an LLM driving the MCP surface, which is an
explicit design goal — reads 256 and reaches for a TURN there, where
non-commuting turn composition died at dim 8. **Reporting only the permissive
ceiling implies a capability that does not exist**: a false green in the
self-description, the same failure class as a dead instrumentation seam, not a
documentation gap.

WHAT THIS MODULE HOLDS DOWN
---------------------------
1. **The ratchet** — no dimension may be published outside a capability, every
   capability must say what it is FOR and what lies beyond it, and every carrier
   must carry a capability row. This is the test that makes the
   permissive-ceiling-only shape unable to return; it fails on SHAPE, so it
   catches a regression introduced by any route, including a new key nobody
   thought about.
2. **The measured table** — the three element-type rows, the SET-identity
   results, and the CD turn-capacity ladder, RE-DERIVED here from the shipped
   carrier and compared against what ``describe()`` publishes. A change to the
   carrier that contradicts the published ontology fails here rather than
   shipping a report that quietly stopped being true.

The full sweep (including CD dims 32 and the dim-64 addressing check, which are
minutes of exact-rational arithmetic) lives in the committed generating code at
``docs/srmech/notes/carrier_capability_ontology_rc339.py`` with its NDJSON. This
module re-derives the affordable part on every run — the part that is cheap is
not sampled, it is exhaustive.

No float, no numpy, no ``abs()``.
"""

from __future__ import annotations

import pytest

from srmech.amsc.carrier_schema import _CAPABILITY, _CARRIERS, carrier_schema
from srmech.amsc.cascade.cayley_dickson import (
    ASSOCIATIVE_ALGEBRA_DIMS,
    CD_ADDRESS_VERIFIED_DIM,
    CD_COMPOSE_MAX_DIM,
    CD_DENSE_MAX_DIM,
    CD_MAX_DIM,
    CD_TURN_MAX_DIM,
    DIVISION_ALGEBRA_DIMS,
    cd_basis,
    cd_mult,
)
from srmech.amsc.genome import (
    ELEMENT_TYPE_CAPABILITY,
    ELEMENT_TYPE_KLEIN4,
    ELEMENT_TYPE_OCTONION,
    ELEMENT_TYPE_Q8,
)
from srmech.amsc.octonion import oct_mult
from srmech.amsc.q8 import q8_mult
from srmech.introspect import describe

#: The three capability axes. Every dimensional ceiling srmech publishes
#: belongs to exactly one of them.
CAPABILITIES = ("address", "compose", "turn")

#: Words that would make a compiled constant read as a runtime measurement.
#: srmech measures no host headroom, so none of these may appear as a key.
_RESOURCE_WORDS = ("stack", "headroom", "available", "free", "remaining",
                   "usable", "host", "rlimit")


def _klein4_mult(a: int, b: int) -> int:
    """V4 = (F2)^2 — the reversible Klein-4 XOR bind."""
    return a ^ b


#: (element_type code, product, order of the SIGNED element set).
_RUNG_PRODUCTS = {
    ELEMENT_TYPE_KLEIN4: (_klein4_mult, 4),
    ELEMENT_TYPE_Q8: (q8_mult, 8),
    ELEMENT_TYPE_OCTONION: (oct_mult, 16),
}


def _commuting(mul, order):
    return {(a, b) for a in range(order) for b in range(order)
            if mul(a, b) == mul(b, a)}


def _turn_composing(mul, order):
    """Pairs whose turns FOLD: ``L_a o L_b == L_(a.b)`` on the whole set."""
    return {(a, b) for a in range(order) for b in range(order)
            if all(mul(a, mul(b, z)) == mul(mul(a, b), z)
                   for z in range(order))}


# ──────────────────────────────────────────────────────────────────────
# 1. THE RATCHET — a limit may not be reported without its capability
# ──────────────────────────────────────────────────────────────────────

def test_no_dimension_is_published_outside_a_capability():
    """THE RATCHET. Walk everything under ``limits`` and require that any key
    naming a dimension sits INSIDE one of the three capability entries.

    This is the shape assertion that makes the rc339 defect unable to come
    back. rc298's block was ``{"cd_max_dim": 256, "cd_dense_max_dim": 64}`` —
    two permissive addressing numbers at the top level with nothing saying what
    they permit. Any future key of that shape fails here, whatever it is called
    and whoever adds it.
    """
    limits = describe()["limits"]
    assert set(limits) == {"capabilities", "element_types"}, (
        f"limits grew a top-level key: {sorted(limits)}. Every ceiling must "
        f"live inside the capability it bounds — a bare number here is exactly "
        f"the rc298 shape a caller reads as permission it does not have")

    capabilities = limits["capabilities"]
    assert set(capabilities) == set(CAPABILITIES), (
        f"the capability axes changed: {sorted(capabilities)}")

    def _has_dim_key(node) -> bool:
        if isinstance(node, dict):
            return any("dim" in str(k).lower() or _has_dim_key(v)
                       for k, v in node.items())
        if isinstance(node, list):
            return any(_has_dim_key(v) for v in node)
        return False

    # The element_types rows may carry cd_dim — that is a rung IDENTITY, and
    # each row states its own three verdicts, so it is never readable as a
    # bare ceiling. Nothing ELSE outside `capabilities` may carry a dimension.
    for row in limits["element_types"]:
        for cap in CAPABILITIES:
            assert cap in row, (
                f"element_type {row.get('name')!r} publishes cd_dim "
                f"{row.get('cd_dim')!r} without a {cap!r} verdict — a rung "
                f"number a caller cannot check against a capability")


def test_every_capability_says_what_it_is_for_and_what_lies_beyond():
    """A ceiling with no ``means`` is a number; a ceiling with no
    ``beyond_ceiling`` hides what breaks when you cross it. Both are how a
    permissive limit gets read as a capability."""
    capabilities = describe()["limits"]["capabilities"]
    for name, cap in capabilities.items():
        assert cap.get("means"), f"{name} publishes a ceiling with no meaning"
        assert isinstance(cap.get("max_dim"), int), (
            f"{name} has no integer max_dim")
        assert "beyond_ceiling" in cap, (
            f"{name} does not say what happens past its ceiling")
        assert cap.get("bounded_by"), (
            f"{name} does not say what imposes its ceiling")
        assert "holds_through" in cap, (
            f"{name} does not name the highest element_type rung it holds on")


def test_the_permissive_ceiling_is_named_as_addressing_and_only_addressing():
    """The specific misread rc339 exists to stop: 256 is an ADDRESSING number.
    It must be inside ``address`` and it must be strictly larger than both of
    the ceilings that actually bind — otherwise the three are indistinguishable
    and the report is back to answering the wrong question."""
    capabilities = describe()["limits"]["capabilities"]
    assert capabilities["address"]["max_dim"] == CD_MAX_DIM == 256, (
        "the 256 must be published as an ADDRESSING ceiling and nothing else")
    assert capabilities["compose"]["max_dim"] == CD_COMPOSE_MAX_DIM == 8, (
        "compose stops at 8 (Hurwitz); past it there are zero divisors")
    assert capabilities["turn"]["max_dim"] == CD_TURN_MAX_DIM == 4, (
        "non-commuting turn composition stops at 4 (H) — publishing anything "
        "larger here is the promise rc339 exists to stop making")
    assert (capabilities["turn"]["max_dim"]
            < capabilities["compose"]["max_dim"]
            < capabilities["address"]["max_dim"]), (
        "the three ceilings must stay distinct and ordered turn < compose < "
        "address; collapsing any two of them re-creates the defect")
    assert capabilities["compose"]["beyond_ceiling"] == "zero_divisors"
    assert capabilities["turn"]["beyond_ceiling"] == "abelian_only"


def test_limits_publishes_no_host_resource_measurement_at_any_depth():
    """The rc298 honesty pin, carried through the nesting. srmech measures no
    host headroom, so a compiled constant must never appear under a name that
    reads as one — at ANY depth, not only at the top level."""
    def _walk(node, path):
        if isinstance(node, dict):
            for key, value in node.items():
                assert not any(w in str(key).lower() for w in _RESOURCE_WORDS), (
                    f"limits{path}[{key!r}] reads as a host-resource "
                    f"measurement; srmech measures none")
                _walk(value, f"{path}[{key!r}]")
        elif isinstance(node, list):
            for i, value in enumerate(node):
                _walk(value, f"{path}[{i}]")

    _walk(describe()["limits"], "")


def test_every_carrier_publishes_a_capability_row():
    """``carriers`` was a flat name list: which operands exist, nothing about
    what they can do. A carrier that ships without a capability row is a
    capability-less entry in a capability report — the same silence, one
    carrier at a time."""
    carriers = describe()["carriers"]["capabilities"]
    assert sorted(carriers) == sorted(_CARRIERS), (
        f"capability rows do not cover the registry: missing "
        f"{sorted(set(_CARRIERS) - set(carriers))}, extra "
        f"{sorted(set(carriers) - set(_CARRIERS))}")
    assert describe()["carriers"]["total"] == len(_CARRIERS)
    required = {"product", "address", "compose", "turn", "commutative",
                "varies_with"}
    for name, cap in carriers.items():
        assert set(cap) == required, (
            f"carrier {name!r} capability row is {sorted(cap)}, expected "
            f"{sorted(required)}")


def test_a_carrier_that_can_be_asked_for_more_says_what_changes_the_answer():
    """The worst-case rule. ``CDRegister`` admits any power-of-two dim up to
    CD_MAX_DIM and ``HV`` admits three genome element_type rungs, so each must
    publish the guarantee that holds across ALL of them and name the knob that
    can improve it. Publishing the best case is how "cd_max_dim: 256" became a
    turn promise."""
    carriers = describe()["carriers"]["capabilities"]
    worst_case = (
        "a register admitting dims past the turn ceiling must publish the "
        "guarantee that holds at ALL of them, not the one that holds at 4")
    assert carriers["CDRegister"]["varies_with"] == "dim", worst_case
    assert carriers["CDRegister"]["turn"] == "abelian_only", worst_case
    assert carriers["CDRegister"]["compose"] == "zero_divisors", worst_case
    assert carriers["HV"]["varies_with"] == "element_type", worst_case
    assert carriers["HV"]["turn"] == "abelian_only", worst_case
    # And a carrier with a FIXED shape must not claim a knob it does not have.
    assert carriers["quaternion"]["varies_with"] is None
    assert carriers["octonion"]["varies_with"] is None


def test_the_carrier_registry_and_describe_agree():
    """``carrier_schema()`` (which may answer from the compiled C table) and
    ``describe()`` (which reads the Python SSoT) must publish the same
    capability. An ADR-0009 split here would mean the two projections disagree
    about what the package can do."""
    schema = carrier_schema()
    carriers = describe()["carriers"]["capabilities"]
    for name in _CARRIERS:
        assert schema[name]["capability"] == carriers[name], (
            f"carrier {name!r}: carrier_schema and describe disagree")
        assert schema[name]["capability"] == _CAPABILITY[name]


# ──────────────────────────────────────────────────────────────────────
# 2. THE MEASURED TABLE — pinned so the carrier cannot silently contradict it
# ──────────────────────────────────────────────────────────────────────

#: The published ontology, re-derived on every run. Generating code + full
#: sweep: docs/srmech/notes/carrier_capability_ontology_rc339.py.
MEASURED_RUNGS = {
    ELEMENT_TYPE_KLEIN4: {"commutes": (16, 16), "associates": (64, 64),
                          "turns_compose": (16, 16)},
    ELEMENT_TYPE_Q8: {"commutes": (40, 64), "associates": (512, 512),
                      "turns_compose": (64, 64)},
    ELEMENT_TYPE_OCTONION: {"commutes": (88, 256), "associates": (2752, 4096),
                            "turns_compose": (88, 256)},
}


@pytest.mark.parametrize("code", sorted(_RUNG_PRODUCTS))
def test_the_element_type_rows_are_what_the_carrier_actually_does(code):
    """Re-derive each rung's row from the SHIPPED product. If the carrier ever
    changes, this fails instead of letting describe() publish a table that
    quietly stopped being true."""
    mul, order = _RUNG_PRODUCTS[code]
    expected = MEASURED_RUNGS[code]

    commuting = _commuting(mul, order)
    turning = _turn_composing(mul, order)
    associating = sum(
        mul(mul(a, b), c) == mul(a, mul(b, c))
        for a in range(order) for b in range(order) for c in range(order))

    assert (len(commuting), order * order) == expected["commutes"]
    assert (associating, order ** 3) == expected["associates"]
    assert (len(turning), order * order) == expected["turns_compose"]

    row = next(r for r in ELEMENT_TYPE_CAPABILITY if r["code"] == code)
    assert tuple(row["commutes"]) == expected["commutes"]
    assert tuple(row["associates"]) == expected["associates"]
    assert tuple(row["turns_compose"]) == expected["turns_compose"]
    assert row["order"] == order


def test_q8_is_the_rung_where_a_non_commuting_turn_still_folds():
    """SET identity, not matching counts. At Q8 the turn-composing pairs
    STRICTLY CONTAIN the commuting pairs: 24 non-commuting pairs still fold,
    and none commutes without folding. That containment is what makes Q8 the
    turn ceiling."""
    mul, order = _RUNG_PRODUCTS[ELEMENT_TYPE_Q8]
    commuting, turning = _commuting(mul, order), _turn_composing(mul, order)

    assert commuting < turning, "Q8 must fold turns its elements do not commute"
    assert len(commuting - turning) == 0
    assert len(turning - commuting) == 24

    row = next(r for r in ELEMENT_TYPE_CAPABILITY
               if r["code"] == ELEMENT_TYPE_Q8)
    assert row["turn"] == "non_commuting"
    assert row["commutative"] is False


def test_at_the_octonion_rung_turns_degrade_to_abelian_only():
    """THE LOAD-BEARING RESULT, and the reason the imprecise "turns stop at H"
    must not be propagated. At the octonion rung the turn-composing set and the
    commuting set are THE SAME SET — verified as sets, both differences empty,
    not merely 88 == 88. What dies here is specifically NON-COMMUTING turn
    composition; addressing and zero-divisor-free composition both survive."""
    mul, order = _RUNG_PRODUCTS[ELEMENT_TYPE_OCTONION]
    commuting, turning = _commuting(mul, order), _turn_composing(mul, order)

    assert turning == commuting, (
        "the octonion rung's surviving turns must be EXACTLY the commuting "
        "ones — that identity is the published ontology")
    assert len(commuting - turning) == 0
    assert len(turning - commuting) == 0
    assert len(turning) == 88

    row = next(r for r in ELEMENT_TYPE_CAPABILITY
               if r["code"] == ELEMENT_TYPE_OCTONION)
    assert row["turn"] == "abelian_only"
    # commutative False is what makes abelian_only a DEGRADATION here rather
    # than the vacuous statement it is on klein4.
    assert row["commutative"] is False
    assert row["compose"] == "full", (
        "O is still a division algebra — losing the turn does not lose the "
        "composition, and reporting otherwise would understate the rung")


def test_klein4_abelian_only_is_vacuous_not_a_degradation():
    """The same ``turn`` verdict means two different things, and
    ``commutative`` is what tells them apart. On V4 every pair commutes, so
    "abelian-only" costs nothing; on O it costs the which-way."""
    row = next(r for r in ELEMENT_TYPE_CAPABILITY
               if r["code"] == ELEMENT_TYPE_KLEIN4)
    assert row["turn"] == "abelian_only"
    assert row["commutative"] is True

    mul, order = _RUNG_PRODUCTS[ELEMENT_TYPE_KLEIN4]
    assert len(_commuting(mul, order)) == order * order


#: Turn capacity over the Cayley–Dickson tower — (dim, composing basis pairs).
#: dims 32 and 64 are in the committed sweep, not here (minutes of exact
#: rational arithmetic); everything through 16 is exhaustive on every run.
CD_TURN_LADDER = ((1, 1), (2, 4), (4, 16), (8, 22), (16, 46))


@pytest.mark.parametrize("dim,expected", CD_TURN_LADDER)
def test_cd_turn_capacity_ladder(dim, expected):
    """How much dimension fits in ONE coherent rotation, per rung. 16/16 at dim
    4 and 22/64 at dim 8 is the whole story: the wall is between H and O, four
    doublings BELOW the addressing cap this build admits."""
    basis = [cd_basis(dim, i) for i in range(dim)]
    composing = sum(
        1 for i in range(dim) for j in range(dim)
        if all(cd_mult(basis[i], cd_mult(basis[j], z))
               == cd_mult(cd_mult(basis[i], basis[j]), z) for z in basis))
    assert composing == expected


def test_the_largest_sub_rung_whose_turns_compose_saturates_at_four():
    """It reaches 4 at dim 8 and never grows again — measured here at 8 and 16,
    and at 32 in the committed sweep. That saturation IS CD_TURN_MAX_DIM."""
    for dim in (8, 16):
        basis = [cd_basis(dim, i) for i in range(dim)]
        best, sub = 0, 1
        while sub <= dim:
            block = basis[:sub]
            if all(cd_mult(x, cd_mult(y, z)) == cd_mult(cd_mult(x, y), z)
                   for x in block for y in block for z in block):
                best = sub
            sub *= 2
        assert best == CD_TURN_MAX_DIM == 4


def test_the_dim_eight_survivors_are_exactly_power_associativity():
    """The corroborating route. The 22 survivors at dim 8 are exactly
    ``{anything paired with e0} U {every element with itself}`` — what
    power-associativity guarantees at every rung — and 22 basis pairs x 4 sign
    combinations = the 88 measured independently on the signed octonion loop.
    Two routes, one number; if they ever disagree, one of them is wrong."""
    dim = 8
    basis = [cd_basis(dim, i) for i in range(dim)]
    composing = {
        (i, j) for i in range(dim) for j in range(dim)
        if all(cd_mult(basis[i], cd_mult(basis[j], z))
               == cd_mult(cd_mult(basis[i], basis[j]), z) for z in basis)}
    power_assoc = {(i, j) for i in range(dim) for j in range(dim)
                   if i == 0 or j == 0 or i == j}
    assert composing == power_assoc
    assert len(composing) == 22

    mul, order = _RUNG_PRODUCTS[ELEMENT_TYPE_OCTONION]
    assert len(composing) * 4 == len(_turn_composing(mul, order)) == 88


@pytest.mark.parametrize("dim", (2, 4, 8, 16))
def test_the_address_lane_is_exact_and_outruns_both_other_ceilings(dim):
    """ADDRESS is the capability that keeps going: ``e_i.e_j = +/- e_(i XOR
    j)`` with zero failures, including at dims where composition and turns are
    both already gone. Exhaustive through 16 here, through 64 in the committed
    sweep."""
    basis = [cd_basis(dim, i) for i in range(dim)]
    for i in range(dim):
        for j in range(dim):
            occupied = [k for k, v in enumerate(cd_mult(basis[i], basis[j]))
                        if v != 0]
            assert occupied == [i ^ j], (
                f"the index lane failed at dim {dim}, e_{i}.e_{j} — the "
                f"premise the whole address layer rides on")


# ──────────────────────────────────────────────────────────────────────
# 3. The two projections and the constants must agree
# ──────────────────────────────────────────────────────────────────────

def test_the_ceilings_agree_with_the_algebra_constants():
    """The published ceilings are not free-standing literals: compose is the
    top of the Hurwitz division-algebra ladder, turn is the top of the
    associative sub-ladder, and both are strictly below the addressing cap."""
    assert CD_COMPOSE_MAX_DIM == max(DIVISION_ALGEBRA_DIMS) == 8
    assert CD_TURN_MAX_DIM == max(ASSOCIATIVE_ALGEBRA_DIMS) == 4
    assert set(ASSOCIATIVE_ALGEBRA_DIMS) < set(DIVISION_ALGEBRA_DIMS), (
        "a rung can be a division algebra and still not compose its turns — "
        "collapsing the two ladders is the category error this rc removes")
    assert CD_TURN_MAX_DIM < CD_COMPOSE_MAX_DIM < CD_MAX_DIM
    # Same value, different facts: the dense cap is an MSVC stack budget, the
    # verified cap is how far the index lane was exhaustively checked.
    assert CD_ADDRESS_VERIFIED_DIM == 64
    assert CD_DENSE_MAX_DIM == 64
    assert CD_ADDRESS_VERIFIED_DIM <= CD_MAX_DIM


def test_holds_through_is_derived_from_the_rungs_not_asserted_beside_them():
    """``holds_through`` and the element_type rows are ONE fact reported once.
    If a rung's verdict ever changes, the ceiling's cross-reference moves with
    it — so the two facets of ``limits`` cannot drift into disagreement."""
    limits = describe()["limits"]
    full = {"address": "exact", "compose": "full", "turn": "non_commuting"}
    for name, cap in limits["capabilities"].items():
        highest = None
        for row in limits["element_types"]:
            if row[name] == full[name]:
                highest = row["name"]
        assert cap["holds_through"] == highest, (
            f"{name}: holds_through says {cap['holds_through']!r} but the "
            f"highest rung carrying {full[name]!r} is {highest!r} — the "
            f"ceiling and the ladder have drifted apart")

    # And the two ceilings that bind must land on the rung they claim.
    by_name = {r["name"]: r for r in limits["element_types"]}
    assert (by_name[limits["capabilities"]["turn"]["holds_through"]]["cd_dim"]
            == CD_TURN_MAX_DIM), (
        "the turn ceiling must be the CD dim of the rung it holds through")
    assert (by_name[limits["capabilities"]["compose"]["holds_through"]]["cd_dim"]
            == CD_COMPOSE_MAX_DIM), (
        "the compose ceiling must be the CD dim of the rung it holds through")


@pytest.mark.parametrize("macro,python_value", [
    ("SRMECH_CD_COMPOSE_MAX_DIM", CD_COMPOSE_MAX_DIM),
    ("SRMECH_CD_TURN_MAX_DIM", CD_TURN_MAX_DIM),
    ("SRMECH_CD_MAX_DIM", CD_MAX_DIM),
    ("SRMECH_CD_DENSE_MAX_DIM", CD_DENSE_MAX_DIM),
])
def test_the_c_host_reads_the_same_ceilings(macro, python_value):
    """ADR-0009: the capability is the invariant. A bare-C host with no
    interpreter must read the SAME three ceilings, or the two projections
    disagree about what srmech can do — and the C header is where a C caller
    would look for permission to turn."""
    import pathlib
    import re

    header = (pathlib.Path(__file__).resolve().parents[2]
              / "c" / "include" / "srmech.h")
    text = header.read_text(encoding="utf-8", errors="replace")
    match = re.search(rf"^#define\s+{macro}\s+(\d+)\s*$", text, re.MULTILINE)
    assert match is not None, f"{macro} is not defined in c/include/srmech.h"
    assert int(match.group(1)) == python_value, (
        f"{macro} = {match.group(1)} but the Python peer is {python_value}")
