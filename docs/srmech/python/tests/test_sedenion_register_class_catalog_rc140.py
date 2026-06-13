"""v0.7.5rc140 — SedenionRegister as a config-driven ``[class]`` over the cascade.

The FIRST multi-field / dict-state / chain / self-returning ``make_class``
conversion (per ``[[feedback_prefer_config_driven_toml_classes]]``): the rc137
(dict fields + ``mutates``) and rc139 (``chain`` + ``returns="self"``) contract
extensions exist exactly so this rich domain object converts with NO hand-coded
Python class. The packaged ``sedenion_register.toml`` ([class] SedenionRegister)
binds its methods to the flat cascade-op adapters in
``srmech.amsc.cascade.sedenion_register`` (each rehydrates a transient register
from the declarative D/codebook/slots fields + delegates — no logic duplication).

Pins the DSL [class] byte-identical to the hand-coded :class:`SedenionRegister`
across every method, plus the declarative state routing: ``write`` → ``mutates``
(slots + codebook), ``read`` → a visible 2-stage ``chain`` (unbind → clean),
``navigate`` → ``returns="self"`` (a fresh register, self untouched).
"""

from __future__ import annotations

from srmech.amsc.cascade.sedenion_register import SedenionRegister
from srmech.dsl import describe_class, make_class

_D = 8192


def _py() -> SedenionRegister:
    r = SedenionRegister(D=_D)
    r.write(0, "alpha")
    r.write(3, "beta", sign=-1)
    r.write(9, "gamma")
    return r


def _dsl():
    r = make_class("SedenionRegister")(D=_D)
    r.write(slot=0, key="alpha")
    r.write(slot=3, key="beta", sign=-1)
    r.write(slot=9, key="gamma")
    return r


def test_class_registered_a_tier():
    # the packaged class_catalog dir auto-loads sedenion_register.toml (peer to
    # one.toml / genome.toml / hurwitz.toml) — describe_class resolves it.
    d = describe_class("SedenionRegister")
    assert d["kind"] == "storage"
    assert set(d["fields"]) == {"D", "codebook", "slots"}


def test_write_mutates_slots_and_codebook_identically():
    o, p = _dsl(), _py()
    assert o.slots() == p.slots()
    # deterministic mint (default minter, same D) → byte-identical codebook
    assert o.fields["codebook"] == p.codebook


def test_materialize_byte_identical():
    assert _dsl().materialize() == _py().materialize()


def test_read_chain_matches_python():
    o, p = _dsl(), _py()
    assert o.read(slot=0) == p.read(0) == ("alpha", 1)
    assert o.read(slot=3) == p.read(3) == ("beta", -1)
    assert o.read(slot=9) == p.read(9) == ("gamma", 1)


def test_read_chain_empty_register_short_circuits():
    o = make_class("SedenionRegister")(D=_D)
    p = SedenionRegister(D=_D)
    assert o.read(slot=0) == p.read(0) == (None, 1)


def test_navigate_returns_fresh_register_self_untouched():
    o, p = _dsl(), _py()
    o2 = o.navigate(j=1)
    p2 = p.navigate(1)
    assert o2.slots() == p2.slots()
    # returns="self" builds a FRESH instance; the original is untouched
    assert o.slots() == p.slots()
    assert o2.class_name == "SedenionRegister"
    # the routed register reads back the moved content (signs composed)
    for slot in p2.slots():
        assert o2.read(slot=slot) == p2.read(slot)


def test_working_word_couple_uncouple():
    o, p = _dsl(), _py()
    vals = [0.5, -1.25, 2.0]
    coupled = p.couple_working(vals)
    assert o.couple_working(vals=vals) == coupled
    assert o.uncouple_working(octonion=coupled) == p.uncouple_working(coupled)


def test_carry_correct_navmap_is_navigable():
    o, p = _dsl(), _py()
    cw = p.carry([1, 0, 1, 1])
    assert o.carry(overflow_bits=[1, 0, 1, 1]) == cw
    assert o.correct(codeword=cw) == p.correct(cw)
    assert o.navmap(j=2) == p.navmap(2)
    e2 = [0.0] * 16
    e2[2] = 1.0  # a single basis e2 (16-long one-hot) is always navigable
    assert o.is_navigable(direction=e2) is True
    assert p.is_navigable(e2) is True


def test_describe_class_surfaces_routing():
    d = describe_class("SedenionRegister")
    assert d["methods"]["write"]["mutates"] == ["slots", "codebook"]
    assert d["methods"]["navigate"]["returns"] == "self"
    # read is a VISIBLE 2-stage chain (unbind → clean), not a single op
    rd = d["methods"]["read"]
    assert "op" not in rd
    assert [s["op"].split(".")[-1] for s in rd["chain"]] == [
        "sed_read_unbind",
        "sed_clean",
    ]
