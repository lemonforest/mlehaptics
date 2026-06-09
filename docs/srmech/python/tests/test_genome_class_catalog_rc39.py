"""v0.7.5rc39 — user-declared classes from [class] TOML (#962 Part 2 / #566).

The cascade-catalog config-driven op-pattern lifted to CLASSES: a [class] TOML
declares fields + methods-as-cascade-op-refs; srmech.dsl.make_class constructs a
generic, class-aware CatalogClass (zero user Python). genome/chromosome/telomere
ships as the built-in seed worked-instance. Validates construction, method
dispatch (bind resolution from call-kwargs then fields; appends/sets), the
round-trip through the genome ops, and the bring-your-own register_class_dir
surface (incl. the no-shadow gate).
"""
from __future__ import annotations

import pytest

from srmech.amsc.hdc import klein4_random
from srmech.dsl import (
    get_class_descriptor,
    list_classes,
    make_class,
    register_class_dir,
)
from srmech.dsl import _class_catalog
from srmech.dsl._class_catalog import load_class_catalog


def _reset_user_class_dirs():
    """Drop any registered user dirs + clear the cache (test isolation)."""
    _class_catalog._USER_CLASS_DIRS.clear()
    load_class_catalog.cache_clear()


# ── the built-in seed: Genome ────────────────────────────────────────────────

def test_genome_is_a_shipped_class():
    assert "Genome" in list_classes()
    desc = get_class_descriptor("Genome")
    assert desc["class"]["name"] == "Genome"
    assert desc["_provenance"] == "srmech"


def test_make_class_factory_carries_metadata():
    Genome = make_class("Genome")
    assert Genome.class_name == "Genome"
    assert "method" in Genome.descriptor["class"]


def test_construct_and_field_defaults():
    one = klein4_random(64, seed=1)
    g = make_class("Genome")(the_one=one)
    assert list(g.fields["the_one"]) == list(one)
    assert g.fields["chromosomes"] == []          # list-typed field defaults to []


def test_unknown_field_rejected():
    with pytest.raises(TypeError):
        make_class("Genome")(the_one=klein4_random(64, seed=1), bogus=1)


def test_unknown_method_raises_attributeerror():
    g = make_class("Genome")(the_one=klein4_random(64, seed=1))
    with pytest.raises(AttributeError):
        g.no_such_method()


# ── method dispatch (bind resolution + the genome round-trip) ─────────────────

def test_shape_method_dispatches_to_encode_shape():
    g = make_class("Genome")(the_one=klein4_random(64, seed=1))
    r = g.shape(n=5000)                            # bind 'n' from the call
    assert r["shape"] == "quad_strand" and r["depth"] == 3


def test_add_chromosome_binds_the_one_from_field_and_appends():
    one = klein4_random(64, seed=2)
    g = make_class("Genome")(the_one=one)
    leaves = [klein4_random(64, seed=s) for s in range(4)]
    strand = g.add_chromosome(leaves=leaves, label="astronomy")   # the_one from field; label passthrough
    assert len(strand) == len(leaves) + 1          # cap + turns
    assert len(g.fields["chromosomes"]) == 1       # appended to the field
    assert g.fields["chromosomes"][0] is strand


def test_full_round_trip_through_the_class():
    one = klein4_random(64, seed=3)
    g = make_class("Genome")(the_one=one)
    leaves = [klein4_random(64, seed=s) for s in range(5)]
    strand = g.add_chromosome(leaves=leaves, label="music")
    cap = g.cap(label="music")
    back = g.recall(strand=strand, telomere=cap)   # the_one bound from field
    assert [list(x) for x in back] == [list(l) for l in leaves]


# ── bring-your-own: register_class_dir + no-shadow gate ───────────────────────

_USER_CLASS_TOML = """
[class]
name = "MyKernelStore"
kind = "storage"
doc = "A user-declared storage class — zero srmech Python authored."

[class.field]
the_one = "hv"
strands = "list"

[class.method.pack]
op = "srmech.amsc.genome.chromosome"
binds = ["leaves", "the_one"]
appends = "strands"
"""

_SHADOW_TOML = """
[class]
name = "Genome"
doc = "illegal shadow of the shipped seed"
[class.field]
x = "hv"
"""


def test_register_user_class_dir_constructs(tmp_path):
    (tmp_path / "mykernelstore.toml").write_text(_USER_CLASS_TOML, encoding="utf-8")
    try:
        register_class_dir(tmp_path)
        assert "MyKernelStore" in list_classes()
        desc = get_class_descriptor("MyKernelStore")
        assert desc["_provenance"].startswith("user:")    # B-tier, attested to hash
        one = klein4_random(64, seed=4)
        store = make_class("MyKernelStore")(the_one=one)
        store.pack(leaves=[klein4_random(64, seed=9)], label="k")
        assert len(store.fields["strands"]) == 1
    finally:
        _reset_user_class_dirs()             # don't leak the user dir to other tests


def test_user_class_may_not_shadow_a_shipped_name(tmp_path):
    (tmp_path / "shadow.toml").write_text(_SHADOW_TOML, encoding="utf-8")
    try:
        register_class_dir(tmp_path)
        with pytest.raises(ValueError, match="may not shadow"):
            load_class_catalog()
    finally:
        _reset_user_class_dirs()
