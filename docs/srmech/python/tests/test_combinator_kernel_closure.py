"""Combinator-kernel closure ratchet (v0.6.0rc16, MS #20).

The cascade DSL's control-flow combinators are a CLOSED, FINITE kernel —
the finite anharmonic-kernel tier of the package's two-tier SSoT. The
kernel is HARDCODED (here, in Python; mirrored co-equally in C); the
asymptotic cascade *instances* the kernel sequences are NOT hardcoded —
they live as TOML op-descriptors in the cascade catalog ("you can't
hardcode a continuum"). Kernel in code, continuum in catalog.

This module pins that closure mechanically so a sixth combinator cannot be
added silently: a new special form must be a CONSCIOUS widening of the
kernel (with this test updated in the same change). The five forms are the
Bird-Meertens recursion schemes:

    then              apply / compose         (op discriminator)
    loop              bounded iterate         (loop_n + sub_chain)
    fold              catamorphism-with-seed  (fold_init + fold_op)
    reduce            catamorphism            (reduce_op)
    parallel_sectors  Klein-4 map-fan-out     (parallel_body)

Data-dependent iteration (while / unfold — loop *until* a predicate) is
DELIBERATELY EXILED to the op-instance layer (a body op decides when to
stop), keeping the kernel total-by-construction at five forms. A future
while/unfold special form would be a SIXTH combinator — a conscious kernel
widening, caught here.
"""
import inspect

import pytest

from srmech.dsl import Chain, build_chain_from_toml_str, chain
from srmech.dsl import _toml_chain


# The five combinator builders — the closed finite kernel.
KERNEL_BUILDERS = frozenset({"then", "loop", "fold", "reduce", "parallel_sectors"})

# Public Chain methods that are NOT combinator builders (runner / inspector).
# Any NEW public Chain method must be classified into one of these two sets;
# that classification IS the conscious-widening checkpoint.
NON_BUILDER_PUBLIC = frozenset({"run", "stages"})

# The five mutually-exclusive TOML stage-discriminators the parser enforces.
TOML_DISCRIMINATORS = ("has_op", "has_loop", "has_fold", "has_reduce", "has_parallel")


def _public_methods(cls):
    return {
        name
        for name, _ in inspect.getmembers(cls, predicate=inspect.isfunction)
        if not name.startswith("_")
    }


def test_exactly_five_kernel_builders():
    """The combinator kernel is exactly five builders — no more, no less."""
    assert len(KERNEL_BUILDERS) == 5
    for name in KERNEL_BUILDERS:
        assert callable(getattr(Chain, name)), f"missing kernel builder {name!r}"


def test_no_hidden_sixth_builder():
    """Every public Chain method is a kernel builder or a known non-builder.

    A new public method (e.g. a ``while_`` 6th combinator) fails here until it
    is consciously classified — the kernel-widening checkpoint.
    """
    public = _public_methods(Chain)
    unclassified = public - KERNEL_BUILDERS - NON_BUILDER_PUBLIC
    assert not unclassified, (
        f"unclassified public Chain method(s): {sorted(unclassified)}. A new "
        f"combinator is a CONSCIOUS kernel widening — add it to KERNEL_BUILDERS "
        f"(and the TOML discriminator set) deliberately, or to "
        f"NON_BUILDER_PUBLIC if it is a runner/inspector."
    )


def test_five_toml_discriminators_bijection():
    """The TOML stage-discriminator set is exactly five and is summed as one.

    Read from the dispatcher source so the count is the REAL one the parser
    enforces, not a copy that could drift.
    """
    src = inspect.getsource(_toml_chain._apply_stage_to_chain)
    for d in TOML_DISCRIMINATORS:
        assert d in src, f"discriminator {d!r} missing from dispatcher"
    # the chosen-count guard sums exactly these five and nothing else
    assert (
        "sum([has_op, has_loop, has_fold, has_reduce, has_parallel])" in src
    ), "the discriminator-count guard changed shape — re-confirm the bijection"


def test_each_builder_appends_one_stage():
    """Each of the five builders materialises exactly one stage on the Chain."""
    assert len(chain().then("chiral_flip")) == 1
    assert len(chain().loop(2, chain().then("chiral_flip"))) == 1
    assert len(chain().fold(0, "cyclic_gcd")) == 1
    assert len(chain().reduce("cyclic_gcd")) == 1
    assert len(chain().parallel_sectors("chiral_flip")) == 1


def test_toml_roundtrip_all_five_forms():
    """A TOML spec exercising all five discriminators round-trips to a
    five-stage Chain — the whole kernel is reachable from config."""
    toml_str = """
    [chain]
    name = "kernel-closure-roundtrip"

    [[stage]]
    op = "chiral_flip"

    [[stage]]
    loop_n = 2
    [[stage.sub_chain]]
    op = "chiral_flip"

    [[stage]]
    fold_init = 0
    fold_op = "cyclic_gcd"

    [[stage]]
    reduce_op = "cyclic_gcd"

    [[stage]]
    parallel_body = "chiral_flip"
    n_sectors = 4
    combine = "bundle"
    """
    ch = build_chain_from_toml_str(toml_str)
    assert len(ch) == 5


def test_parallel_sectors_caps_at_klein4():
    """The parallel fan-out's default sector count is the |V4| = 4 Klein-4
    ceiling — the algebraic cap, not an arbitrary parallelism knob."""
    sig = inspect.signature(Chain.parallel_sectors)
    assert sig.parameters["n_sectors"].default == 4


def test_empty_stage_has_no_implicit_default_form():
    """A stage carrying none of the five discriminators is rejected — there is
    no implicit sixth / fallback form the parser silently applies."""
    with pytest.raises(ValueError, match="no discriminator"):
        build_chain_from_toml_str('[chain]\nname = "x"\n[[stage]]\nnonsense = 1\n')
