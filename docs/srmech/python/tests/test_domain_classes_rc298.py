"""rc298 (`#936`) — describe() reports CAPABILITY, not declaration style.

Before this rc, ``describe()["classes"]`` enumerated the ``[class]`` TOML
catalog. ``CDRegister`` — shipped public class, registered carrier, three C
peers — was absent purely because rc297 hand-coded it rather than declaring it
in TOML. That is ADR-0009 mechanism-2: an implementation detail surfaced as if
it were the capability.

The fix is not "add CDRegister to the list". It is to make the declaration route
a FIELD instead of an admission criterion, so the next hand-coded domain class
cannot go missing for the same reason. These tests pin that property, not the
current membership.

rc464 (`#T1188`) — THAT DEFERRAL IS RETRACTED, and the paragraph it replaces is
kept here in full so the reversal is legible rather than silent. It read:

    NOT converting CDRegister to TOML is deliberate and rc297's reasoning
    stands: routing both registers through the same machinery would make the
    dim-16 faithfulness comparison partly circular, because oracle and subject
    would share failure modes.

Two things were wrong with it, in opposite ways.

FIRST, the OTHER half of rc297's stated reasoning — "the make_class contract is
one-op-per-method plus a single appends/sets field, so a multi-field register is
HARD" — was already false when it was written. rc137 shipped dict fields +
``mutates``; rc139 shipped ``chain`` + ``returns="self"``; rc140 had ALREADY
converted the 16-slot register using exactly those. CDRegister's seven fields
need ZERO contract extension.

SECOND, the circularity objection was REAL, and it is the reason the conversion
waited rather than the reason it should never happen. It holds only while the
faithfulness oracle is a LIVE peer class: two live classes sharing one dispatch
engine share its failure modes. It dissolves the moment the oracle becomes a
RECORDED fixture, because recorded output cannot acquire the subject's failure
modes — it is not running. So the conversion is unblocked by the same change
that records the fixture, and this docstring says so where the deferral was
recorded.

The consequence for THIS file: ``CDRegister`` was the only ``"python"``-routed
domain class, so the route flips to ``"toml"`` and the "both routes are
populated" assertion below can no longer hold. It is REWRITTEN, not lowered —
see :func:`test_declaration_route_is_a_field_not_an_admission_criterion`.
"""

from __future__ import annotations

import srmech
from srmech import dsl
from srmech import cascade
from srmech.introspect.carrier_schema import _CARRIERS
from srmech.introspect import describe
from srmech.introspect._domain_classes import (
    NON_DOMAIN_RECORDS,
    list_domain_classes,
)


# ──────────────────────────────────────────────────────────────────────
# The defect `#936` names
# ──────────────────────────────────────────────────────────────────────

def test_cdregister_is_reported_as_a_class():
    """The literal `#936` symptom. rc297: describe() said 4 classes, none of
    them CDRegister, while CDRegister was a shipped public class with a
    registered carrier and three C peers."""
    d = describe()["classes"]
    assert "CDRegister" in d["names"], (
        f"CDRegister is a shipped public class, a registered carrier and has C "
        f"peers, but describe() lists {d['names']}")
    # rc464: "toml" since the conversion. The ROUTE is not the point of this
    # test — the MEMBERSHIP is (`#936`'s literal symptom was CDRegister being
    # absent from d["names"]). The route is pinned anyway so a silent flip in
    # either direction is reported.
    assert d["routes"]["CDRegister"] == "toml"


def test_declaration_route_is_a_field_not_an_admission_criterion():
    """The actual fix. Every domain class is present REGARDLESS of route, and
    the route is retrievable. A future hand-coded class is reported the day it
    ships, without anyone remembering to update a list."""
    d = describe()["classes"]
    assert set(d["routes"]) == set(d["names"])
    assert set(d["routes"].values()) <= {"toml", "python"}
    assert "toml" in d["routes"].values()

    # rc464 (`#T1188`) — this used to also assert `"python" in
    # d["routes"].values()`, with the comment "otherwise this test proves
    # nothing". That was a fair worry and the wrong instrument. CDRegister was
    # the ONLY python-routed domain class (One / Genome / Hurwitz /
    # SedenionRegister are all TOML; Block is a NON_DOMAIN_RECORD), so its
    # conversion empties the python route and the assertion fails BY
    # CONSTRUCTION — no honest change to the package can satisfy it.
    #
    # It is replaced rather than deleted, because the property it was reaching
    # for is real and is still checkable: the route must be a FIELD that the
    # enumeration carries for every class, not an admission criterion that
    # decides who appears. So assert exactly that — every name routed, every
    # route in the vocabulary, and the toml-routed SET equal to the TOML catalog
    # — plus the python route's emptiness AS A MEASURED FACT with its reason, so
    # that a future hand-coded domain class re-populating it is reported here
    # rather than passing unremarked.
    python_routed = sorted(n for n, r in d["routes"].items() if r == "python")
    assert python_routed == [], (
        f"the python route is expected to be EMPTY at rc464 — the last "
        f"hand-coded domain class (CDRegister) converted to a [class] TOML — "
        f"but it holds {python_routed}. If that is a NEW hand-coded domain "
        f"class, this assertion has done its job: it is reported the day it "
        f"ships, exactly as `#936` intended. Record it here with its reason "
        f"rather than deleting the check.")


def test_toml_only_count_is_its_own_key_not_a_narrowed_classes():
    """A consumer that genuinely needs the TOML-catalog count gets its own key.
    That is what makes widening ``classes`` safe: nothing had to lose access to
    the old number, so nothing had to keep the old (wrong) meaning."""
    d = describe()["classes"]
    assert d["toml_total"] == len(dsl.list_classes())
    assert d["toml_total"] <= d["total"]
    toml_routed = {n for n, r in d["routes"].items() if r == "toml"}
    assert toml_routed == set(dsl.list_classes())


def test_total_and_names_agree():
    d = describe()["classes"]
    assert d["total"] == len(d["names"]) == len(set(d["names"]))
    assert d["names"] == sorted(d["names"])


# ──────────────────────────────────────────────────────────────────────
# The derivation must not rot back into a hand-list
# ──────────────────────────────────────────────────────────────────────

def test_every_public_cascade_class_is_either_domain_or_declared_a_record():
    """THE RATCHET. A new class exported from ``srmech.cascade`` is a
    domain class by default; excluding it takes a deliberate, documented entry
    in ``NON_DOMAIN_RECORDS``. This fails when someone adds a class and neither
    outcome was chosen — which is exactly how `#936` happened."""
    exported = {n for n in cascade.__all__
                if isinstance(getattr(cascade, n, None), type)}
    reported = set(describe()["classes"]["names"])
    unaccounted = exported - reported - set(NON_DOMAIN_RECORDS)
    assert not unaccounted, (
        f"{sorted(unaccounted)} are public classes on srmech.cascade but "
        f"appear in neither describe()['classes'] nor NON_DOMAIN_RECORDS. "
        f"Decide which — a class that is neither is invisible to callers.")


def test_non_domain_records_are_real_exports_with_reasons():
    """An exclusion list that names a class which no longer exists is a lie that
    hides the next real one."""
    for name, reason in NON_DOMAIN_RECORDS.items():
        assert isinstance(getattr(cascade, name, None), type), (
            f"NON_DOMAIN_RECORDS names {name!r}, which is not a public class on "
            f"srmech.cascade — stale exclusion")
        assert len(reason) > 20, f"{name!r} needs a real reason, got {reason!r}"
        assert name not in describe()["classes"]["names"]


def test_toml_declaration_wins_the_route_for_dual_declared_classes():
    """``One``, ``SedenionRegister`` and (since rc464) ``CDRegister`` are BOTH
    TOML-declared and real Python classes. The TOML descriptor is the
    declaration, so it must win — otherwise ``toml_total`` would undercount and
    ``describe_class`` coverage would look broken."""
    routes = list_domain_classes()
    for name in ("One", "SedenionRegister", "CDRegister"):
        assert isinstance(getattr(cascade, name, None), type)
        assert routes[name] == "toml"


def test_every_toml_routed_class_actually_describes():
    """The route is a promise: ``"toml"`` means ``dsl.describe_class`` resolves
    it. ``"python"`` makes no such promise."""
    routes = list_domain_classes()
    for name, route in routes.items():
        if route == "toml":
            assert dsl.describe_class(name)["name"] == name


# ──────────────────────────────────────────────────────────────────────
# Carriers — the other half of the same defect
# ──────────────────────────────────────────────────────────────────────

def test_describe_surfaces_the_carrier_registry():
    """`#936` follow-through: a 25-entry registry with a 100%
    construction-example floor and a compiled-in C peer table was invisible to
    describe() entirely. ``tools`` are the verbs; ``carriers`` are the nouns.

    rc339 (`#T967`) replaced the flat ``names`` list with capability-keyed rows —
    a name list said WHICH operands exist and nothing about what any of them can
    do. The membership assertion is unchanged; only where the names are read
    from moved (``sorted(...["capabilities"])``)."""
    d = describe()
    assert "carriers" in d, "describe() reports verbs but not operands"
    assert d["carriers"]["total"] == len(_CARRIERS)
    assert sorted(d["carriers"]["capabilities"]) == sorted(_CARRIERS)


def test_the_hdc_domain_classes_are_carriers_too():
    """The registry already knew about the class describe() was missing —
    CDRegister has been a registered carrier since rc297. That is what made the
    under-reporting visible."""
    carriers = set(describe()["carriers"]["capabilities"])
    for name in ("One", "SedenionRegister", "CDRegister"):
        assert name in carriers


# ──────────────────────────────────────────────────────────────────────
# Capability ceilings — introspection knowing what it can actually do
# ──────────────────────────────────────────────────────────────────────

def test_describe_reports_the_compiled_dimension_ceilings():
    """rc298 `#936`: before this rc, ``describe()`` could say whether a native
    library existed and its ABI, but exposed NO dimensional bound at all — so a
    caller (or an LLM driving MCP) could only find the largest admissible dim by
    trying it and failing, or by reading the C header. For a package whose whole
    stance is self-description, that was a gap.

    rc339 (`#T967`) kept both numbers and moved them INSIDE the capability they
    bound. They were always addressing ceilings; nothing said so, which is how
    256 came to be read as a turn ceiling."""
    from srmech.cascade.cayley_dickson import CD_DENSE_MAX_DIM, CD_MAX_DIM

    address = describe()["limits"]["capabilities"]["address"]
    assert address["max_dim"] == CD_MAX_DIM
    assert address["dense_max_dim"] == CD_DENSE_MAX_DIM
    assert address["dense_max_dim"] <= address["max_dim"]


def test_limits_reports_capability_only_and_claims_no_host_headroom():
    """THE HONESTY PIN. ``limits`` reports what this BUILD supports — an
    artifact property, invariant across platforms. rc298 measures NO host
    resource headroom (that needs a real PAL stack-limit query), so it must
    publish none.

    A compiled constant surfaced under a name implying runtime headroom would be
    a wrong number, and a wrong number is worse than a missing key. If a
    resource ceiling is ever added it gets its own unmistakable name; this test
    fails if one is smuggled into the capability block instead.

    rc339 (`#T967`) nested the block one level (capability → ceilings), so the
    scan walks the leaf keys instead of the top-level ones. The rule is
    unchanged and now covers strictly MORE keys than it did at rc298.
    """
    limits = describe()["limits"]
    assert set(limits) == {"capabilities", "element_types"}, (
        f"unexpected key in the capability block: {sorted(limits)} — a runtime "
        f"resource measurement must not live here")
    forbidden = ("stack", "headroom", "available", "free", "remaining",
                 "usable", "host", "rlimit")

    def _walk(node, path):
        if isinstance(node, dict):
            for key, value in node.items():
                assert not any(word in str(key).lower() for word in forbidden), (
                    f"limits{path}[{key!r}] reads as a host-resource "
                    f"measurement; srmech measures none")
                _walk(value, f"{path}[{key!r}]")
        elif isinstance(node, list):
            for i, value in enumerate(node):
                _walk(value, f"{path}[{i}]")

    _walk(limits, "")


def test_capability_ceiling_is_not_nested_under_native():
    """The ceilings bind the PURE path too, so reporting them as native-only
    would misdescribe a no-native install."""
    d = describe()
    assert set(d["native"]) == {"has_native", "abi_version", "native_version"}
    assert "limits" in d


# ──────────────────────────────────────────────────────────────────────
# Shape / MCP surface
# ──────────────────────────────────────────────────────────────────────

def test_describe_is_json_shaped():
    """describe() feeds the MCP surface — every value must survive JSON."""
    import json
    d = describe()
    assert json.loads(json.dumps(d)) == d


def test_describe_still_reports_the_rest_unchanged():
    d = describe()
    assert d["srmech_version"] == srmech.__version__
    assert d["tools"]["total"] > 0
    assert set(d) == {
        "srmech_version", "tool_schema_version", "native", "tools",
        "handle_pending", "categories", "classes", "carriers", "limits",
        "c_claims",  # rc300 `#938` — C-claim resolution against the loaded lib
        "lanes",     # rc347 `#T985` — the OP-side complement of "carriers"
        "cascade_catalog",  # rc420 `#T1114` — ADR-0012 C6: the 20 [cascade]
                            # descriptors, countable at the root index at last
        "frames",    # rc430 `#T1127` — the FRAME axis: is the frame this op
                     # reduces in an INPUT ("parametric") or WELDED IN ("fixed")
    }
