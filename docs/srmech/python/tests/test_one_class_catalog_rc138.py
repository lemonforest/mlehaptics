"""v0.7.5rc138 — "the One" S(σ,θ) as a config-driven [class] (one.toml).

Per [[feedback_prefer_config_driven_toml_classes]], the immutable accessor-shaped
``One`` (#887) is converted to a packaged ``[class]`` TOML consumed by
``srmech.dsl.make_class`` — the genome two-layer pattern (ship each accessor as a
module-level flat op in ``srmech.amsc.cascade.one``, bind it in ``one.toml``).
``One`` needs NO new make_class directive (single ``one`` field; each method a
one-bind cascade-op ref).

This pins the DSL-class-vs-Python equivalence: for the same ``the_one(σ, θ)``,
every ``make_class("One")`` method returns exactly what the Python ``One``'s
accessor returns — across θ=0 (σ-seed) and a non-trivial θ, both chiralities —
plus the shipped-class surfacing (``list_classes`` / ``describe_class`` /
``describe()['classes']``).
"""

from __future__ import annotations

import pytest

from srmech.amsc.cascade import the_one
from srmech.dsl import describe_class, list_classes, make_class


# ── One ships as a packaged (A-tier) class ───────────────────────────────────

def test_one_is_a_shipped_class():
    assert "One" in list_classes()
    d = describe_class("One")
    assert d["name"] == "One"
    assert d["kind"] == "substrate"
    assert d["provenance"] == "srmech"
    assert d["fields"] == {"one": "any"}
    # the 8 accessor methods bind to the flat-op layer / to_scalar
    assert set(d["methods"]) == {
        "dim", "imag_dims", "partition", "plane_counts",
        "grammar_slots", "flat", "matrix", "scalar",
    }
    assert d["methods"]["dim"]["op"] == "srmech.amsc.cascade.one.one_dim"
    assert d["methods"]["scalar"]["op"] == "srmech.amsc.cascade.to_scalar"


# ── DSL-class vs Python-One equivalence ──────────────────────────────────────

@pytest.mark.parametrize("sigma,tn,td", [
    (+1, 0, 1),        # θ = 0  → the σ-seed (no rotation)
    (-1, 0, 1),
    (+1, 99, 100),     # a non-trivial θ — the octonion epicycle turns
    (-1, 7, 3),
])
def test_dsl_class_matches_python_one(sigma, tn, td):
    o = the_one(sigma, tn, td)
    O = make_class("One")(one=o)

    assert O.dim() == o.dim == 14
    assert O.imag_dims() == o.imag_dims == (1, 3, 7)
    assert O.partition() == o.partition == (1, 3, 7, 3)
    assert O.plane_counts() == o.plane_counts == (0, 1, 3)
    assert O.grammar_slots() == o.grammar_slots == ("B", "H", "N")
    # the 14 exact rationals — bit-for-bit
    assert O.flat() == o.to_flat_rational()
    assert len(O.flat()) == 14
    # the 14×14 numpy-free Mat operator — entry-for-entry
    assert O.matrix().tolist() == o.to_matrix().tolist()
    assert O.matrix().shape == (14, 14)
    # the scalar projection family (exact (num, den) by default)
    assert O.scalar(mode="trace") == o.to_scalar(mode="trace")
    assert O.scalar(mode="sqnorm") == o.to_scalar(mode="sqnorm")
    assert O.scalar(mode="component", index=0) == o.to_scalar(mode="component", index=0)
    # as_float passthrough — the single terminal lossy cast
    assert O.scalar(mode="trace", as_float=True) == o.to_scalar(mode="trace", as_float=True)


# ── the flat-op accessor layer is itself faithful (the bound ops) ────────────

def test_flat_op_accessors_match_property_accessors():
    from srmech.amsc.cascade import one as one_mod

    o = the_one(+1, 5, 4)
    assert one_mod.one_dim(o) == o.dim
    assert one_mod.one_imag_dims(o) == o.imag_dims
    assert one_mod.one_partition(o) == o.partition
    assert one_mod.one_plane_counts(o) == o.plane_counts
    assert one_mod.one_grammar_slots(o) == o.grammar_slots
    assert one_mod.one_flat_rational(o) == o.to_flat_rational()
    assert one_mod.one_matrix(o).tolist() == o.to_matrix().tolist()


def test_n1_sigma_only_through_the_class():
    # the structural prediction (θ inert at n=1) survives the TOML-class path:
    # the n=1 (ℂ) imaginary entry is (σ, 1) at ANY θ — index 1 of the flat 14.
    for sigma in (+1, -1):
        O = make_class("One")(one=the_one(sigma, 99, 100))
        assert O.flat()[1] == (sigma, 1)
