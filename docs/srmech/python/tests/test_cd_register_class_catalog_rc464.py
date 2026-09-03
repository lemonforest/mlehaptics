"""rc464 (`#T1188`) — the CDRegister ``[class]`` TOML conversion proof.

THE STANDING REQUIREMENT THIS SATISFIES
=======================================
The monorepo memory's config-driven-TOML discipline
(``[[feedback_prefer_config_driven_toml_classes]]``) ends with a clause that is
not optional: *"Prove every conversion with a DSL-class-vs-Python equivalence
test."* The rc140 module was that proof for the 16-slot
register; rc464 removed that register, so this file is the only one left —
which is why it covers all EIGHTEEN methods rather than the eleven its
predecessor had, and both rungs rather than one.

WHAT WAS RETRACTED TO GET HERE, STATED SO THE REVERSAL IS LEGIBLE
=================================================================
rc297 recorded the conversion as *"decided, not defaulted"* against, on two
grounds, and rc298 restated it. Both are gone, in different ways:

1. *"the make_class contract is one-op-per-method plus a single appends/sets
   field, so a multi-field register is HARD."* **That was already false when it
   was written.** rc137 shipped dict fields + ``mutates``; rc139 shipped
   ``chain`` + ``returns="self"``; rc140 had ALREADY converted the 16-slot
   register using exactly those extensions. CDRegister's seven fields need ZERO
   further contract extension — this file is the executable form of that claim.

2. *"routing both registers through the same machinery would make the dim-16
   faithfulness comparison partly circular, because oracle and subject would
   share failure modes."* That objection was REAL and it is why the conversion
   waited rather than why it should never happen. It holds only while the
   faithfulness oracle is a LIVE peer class — two live classes sharing one
   dispatch engine share its failure modes. It dissolves the moment the oracle
   becomes a RECORDED fixture, because recorded output cannot acquire the
   subject's failure modes: it is not running.

WHAT THIS FILE ASSERTS, AND WHY EACH SHAPE IS HERE
==================================================
Equivalence is checked METHOD BY METHOD against the hand-coded Python class at
two rungs, chosen so neither can hide the other's failure:

* **dim 16, ``namespace="SEDENION"``, both OPT layers ON** — the faithfulness
  rung, and the one where a byte-level divergence would matter most.
* **dim 256, slots including 99, 100, 128 and 255** — the rung the 16-slot
  descriptor cannot reach at all, and specifically the one that crosses the
  two-digit slot-key boundary. A conversion that only ever ran at dim 16 could
  ship a two-digit assumption and never meet it.

Plus four properties the method sweep alone would not catch:

* the SCALAR DEFAULT rule (``D`` / ``namespace`` / both flags arrive ``None``,
  because the contract has no scalar default) resolves identically in both
  projections;
* the two OPT-layer GATES raise the SAME ``ValueError`` message — binding the
  ungated free ops would have been shorter and would have made the declarative
  class silently not raise, which is a behaviour fork wearing the name
  "conversion";
* ``navigate`` returns a FRESH instance carrying all SEVEN fields — an omitted
  field resets to the contract default, so a navigate that returned only
  ``slots`` would silently drop ``D``, ``namespace`` and both gates;
* the symmetric-operand chains raise the same message with the right VERB.

Pure Python; no native library required and none asserted. numpy-free.
"""

from __future__ import annotations

import pytest

from srmech import cascade
from srmech import dsl


_SED_KW = dict(dim=16, D=8192, namespace="SEDENION",
               coupling=True, error_correction=True)
_BIG_KW = dict(dim=256, D=8192)

#: (slot, key, sign) triples written into both projections at dim 16.
_SED_WRITES = ((0, "alpha", 1), (3, "beta", -1), (10, "gamma", 1),
               (7, "delta", -1))

#: dim-256 occupancy. 99 / 100 / 128 / 255 straddle the two-digit slot-key
#: boundary a 16-slot-shaped implementation would never reach.
_BIG_SLOTS = (0, 7, 99, 100, 128, 255)


def _pair(**kw):
    """The SAME state in both projections: (TOML-declared, hand-coded)."""
    return dsl.make_class("CDRegister")(**kw), cascade.CDRegister(**kw)


def _sed_pair():
    t, p = _pair(**_SED_KW)
    for slot, key, sign in _SED_WRITES:
        t.write(slot=slot, key=key, sign=sign)
        p.write(slot, key, sign=sign)
    return t, p


def _big_pair():
    t, p = _pair(**_BIG_KW)
    for s in _BIG_SLOTS:
        sign = 1 if s % 2 == 0 else -1
        t.write(slot=s, key=f"v{s}", sign=sign)
        p.write(s, f"v{s}", sign=sign)
    return t, p


# ──────────────────────────────────────────────────────────────────────
# The descriptor itself
# ──────────────────────────────────────────────────────────────────────

def test_the_descriptor_is_packaged_and_declares_the_seven_state_fields():
    """The declarative state is exactly the Python class's state MINUS the two
    perf-only caches — the same drop the 16-slot descriptor makes, and for the
    same reason: minting is deterministic from ``(name, D)``, so the
    declarative form recomputes what the cache memoised."""
    d = dsl.describe_class("CDRegister")
    assert d["name"] == "CDRegister"
    assert set(d["fields"]) == {
        "dim", "D", "namespace", "codebook", "slots",
        "coupling", "error_correction"}


def test_every_python_method_has_a_declared_peer():
    """No method may go missing in the conversion. This is a SET equality, not
    a subset: a descriptor that silently declared thirteen of eighteen would
    still pass every per-method check below, because those only walk what the
    descriptor declares."""
    declared = set(dsl.describe_class("CDRegister")["methods"])
    python_side = {
        name for name in dir(cascade.CDRegister)
        if not name.startswith("_")
        and callable(getattr(cascade.CDRegister, name))
    }
    assert declared == python_side, (
        f"declared-but-absent: {sorted(declared - python_side)}; "
        f"present-but-undeclared: {sorted(python_side - declared)}")


def test_the_route_is_toml_and_the_python_route_is_empty():
    """The conversion's own consequence, asserted where it is caused rather
    than only where it is observed."""
    from srmech.introspect._domain_classes import list_domain_classes
    routes = list_domain_classes()
    assert routes["CDRegister"] == "toml"
    assert [n for n, r in routes.items() if r == "python"] == []


# ──────────────────────────────────────────────────────────────────────
# Method-by-method equivalence at the faithfulness rung (dim 16)
# ──────────────────────────────────────────────────────────────────────

def test_storage_methods_agree_at_dim_16():
    t, p = _sed_pair()
    assert t.slots() == p.slots()
    assert t.materialize() == p.materialize()
    for slot, _key, _sign in _SED_WRITES:
        assert t.read(slot=slot) == p.read(slot)


def test_block_structure_agrees_at_dim_16():
    t, p = _sed_pair()
    assert t.working_block() == p.working_block()
    assert t.carry_block() == p.carry_block()


def test_carrier_arithmetic_agrees_at_dim_16():
    """The rc330 element / norm / conjugate / multiply / add family, which the
    descriptor expresses as CHAINS over ``cdr_element`` and the already-C-backed
    ``cayley_dickson`` ops rather than as five more adapters."""
    t, p = _sed_pair()
    t2, p2 = t.navigate(j=1), p.navigate(1)
    assert t.element() == p.element()
    assert t.norm() == p.norm()
    assert t.conjugate() == p.conjugate()
    assert t.multiply(other=t2) == p.multiply(p2)
    assert t.add(other=t2) == p.add(p2)


def test_navigation_agrees_at_dim_16():
    t, p = _sed_pair()
    for j in range(16):
        assert t.navmap(j=j) == p.navmap(j)
    one_hot = [0] * 16
    one_hot[1] = 1
    assert t.is_navigable(direction=one_hot) == p.is_navigable(one_hot)


def test_opt_layer_methods_agree_at_dim_16():
    t, p = _sed_pair()
    vals = [1.5, -2.25, 3.0]
    assert t.couple_working(vals=vals) == p.couple_working(vals)
    word = p.couple_working(vals)
    assert t.uncouple_working(word=word) == p.uncouple_working(word)
    bits = [1, 0, 1, 1]
    assert t.carry(overflow_bits=bits) == p.carry(bits)
    # `n` rides as a PASS-THROUGH kwarg, not a bind — a bind would make the EC
    # order mandatory on every call.
    wide = [1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1]
    assert t.carry(overflow_bits=wide, n=4) == p.carry(wide, n=4)
    codeword = list(p.carry(bits))
    codeword[2] ^= 1                      # Class-K GF(2) flip, not abs()
    assert t.correct(codeword=codeword) == p.correct(codeword)


# ──────────────────────────────────────────────────────────────────────
# The rung the 16-slot descriptor cannot reach
# ──────────────────────────────────────────────────────────────────────

def test_storage_and_navigation_agree_at_dim_256():
    """Slots 99 / 100 / 128 / 255 straddle the two-digit boundary. A conversion
    validated only at dim 16 could carry a two-digit slot-key assumption and
    never meet it."""
    t, p = _big_pair()
    assert t.slots() == p.slots()
    assert t.materialize() == p.materialize()
    assert t.navigate(j=3).slots() == p.navigate(3).slots()
    for j in (0, 1, 127, 255):
        assert t.navmap(j=j) == p.navmap(j)
    assert t.element() == p.element()
    assert t.norm() == p.norm()
    assert t.working_block() == p.working_block()
    assert t.carry_block() == p.carry_block()


def test_the_default_namespace_is_dim_scoped_at_256():
    t, _p = _big_pair()
    assert t.navigate(j=1).fields["namespace"] == "CD256"


# ──────────────────────────────────────────────────────────────────────
# The four properties the method sweep alone would not catch
# ──────────────────────────────────────────────────────────────────────

def test_scalar_defaults_resolve_identically_in_both_projections():
    """The ``[class]`` contract has no scalar field default — a ``str`` / ``int``
    / ``bool`` field arrives ``None``. The adapters resolve that at USE time to
    ``DEFAULT_D`` / ``f"CD{dim}"`` / ``False``, which is the SAME rule
    ``CDRegister.__init__`` applies. Constructed with ``dim=`` alone, the two
    projections must therefore be indistinguishable."""
    t, p = _pair(dim=8)
    t.write(slot=1, key="x")
    p.write(1, "x")
    assert t.materialize() == p.materialize()
    # The FIELD itself passes through unchanged — only the USE is defaulted, so
    # a round-tripped instance still reports the state it was built with.
    assert t.fields["D"] is None and t.fields["namespace"] is None
    routed = t.navigate(j=1).fields
    assert routed["D"] == cascade.cd_register(8).D
    assert routed["namespace"] == "CD8"
    assert routed["coupling"] is False and routed["error_correction"] is False


@pytest.mark.parametrize("method,kwargs,pyargs", [
    ("couple_working", {"vals": [1.0]}, ([1.0],)),
    ("uncouple_working", {"word": [1.0] * 8}, ([1.0] * 8,)),
    ("carry", {"overflow_bits": [1]}, ([1],)),
    ("correct", {"codeword": [0] * 7}, ([0] * 7,)),
])
def test_the_opt_gates_raise_the_same_message_on_a_bare_register(
        method, kwargs, pyargs):
    """A bare register is a pure signed-pointer addressing object and RAISES on
    the value operations. Binding these four straight to the shipped ungated
    free ops (``cd_couple_working`` and friends) would have been shorter and
    would have made the declarative class silently NOT raise — a behaviour fork
    wearing the name "conversion". So the adapters bind the two flags from the
    fields and let the class's own gate fire, and this asserts the messages are
    the same string, not merely the same exception type."""
    t, p = _pair(dim=16, D=8192)
    with pytest.raises(ValueError) as toml_err:
        getattr(t, method)(**kwargs)
    with pytest.raises(ValueError) as py_err:
        getattr(p, method)(*pyargs)
    assert str(toml_err.value) == str(py_err.value)


def test_navigate_returns_a_fresh_instance_carrying_all_seven_fields():
    """``returns="self"`` constructs a FRESH instance from exactly the dict the
    op returns, and any field omitted resets to the type default. A navigate
    that returned only ``slots`` would therefore silently drop ``dim`` / ``D`` /
    ``namespace`` and BOTH OPT gates off the routed register — so the adapter
    emits all seven, and that is what this pins."""
    t, p = _sed_pair()
    before = t.slots()
    routed = t.navigate(j=1)
    assert routed.fields["dim"] == 16
    assert routed.fields["D"] == 8192
    assert routed.fields["namespace"] == "SEDENION"
    assert routed.fields["coupling"] is True
    assert routed.fields["error_correction"] is True
    assert routed.slots() == p.navigate(1).slots()
    assert t.slots() == before, "navigate must not mutate the receiver"
    # The routed register is still a working register, gates and all.
    assert routed.couple_working(vals=[1.0]) == p.couple_working([1.0])


def test_an_unequal_rung_raises_the_same_message_and_names_the_right_verb():
    """The dim check lives in ``cdr_element_of``, AHEAD of ``cd_mult`` /
    ``cd_add``, for the same reason it lives in the Python methods: an
    unequal-rung product is not a defined operation, and letting the length
    mismatch surface out of the algebra would report it as a different fault.
    ``verb`` is a STATIC stage kwarg supplied by the descriptor, which is why
    ``add`` does not report itself as ``multiply``."""
    t16, p16 = _sed_pair()
    t256, p256 = _big_pair()
    with pytest.raises(ValueError) as t_err:
        t256.multiply(other=t16)
    with pytest.raises(ValueError) as p_err:
        p256.multiply(p16)
    assert str(t_err.value) == str(p_err.value)
    assert "carrier multiply" in str(t_err.value)

    with pytest.raises(ValueError) as t_add:
        t256.add(other=t16)
    with pytest.raises(ValueError) as p_add:
        p256.add(p16)
    assert str(t_add.value) == str(p_add.value)
    assert "carrier add" in str(t_add.value)


def test_the_equivalence_check_would_notice_a_divergence():
    """The negative control. Every assertion above compares two live objects,
    and a comparison that cannot fail proves nothing — so perturb one side and
    require the comparison to fire."""
    t, p = _sed_pair()
    assert t.slots() == p.slots()
    p.write(5, "epsilon")
    assert t.slots() != p.slots()
    assert t.materialize() != p.materialize()
