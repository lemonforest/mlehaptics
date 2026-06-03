"""v0.7.0rc22 — ``reorient`` is now a data-first DSL chain stage.

UPSTREAM_NOTES §16.1: ``reorient`` was un-invokable as a DSL ``op=`` /
``parallel_body=`` stage because its data argument was second
(``reorient(orientation, value)``) while the chain runner pipes the stream
into arg 0. Fix (a) reordered it to ``reorient(value, *, orientation)`` —
data-first positional + keyword-only orientation — so the pipe fills
``value`` and ``orientation`` arrives as a bound stage kwarg (the same
pattern as ``best_rational_signed``'s ``max_denominator``). These tests
pin the fix: reorient drives as a stage via the Python ``.then()`` API and
via a TOML chain, and the old positional call is gone.
"""

import pytest

from srmech.amsc import cascade
from srmech.dsl import Chain, run_toml_chain


def test_reorient_signature_is_value_first_keyword_only_orientation():
    # value positional, orientation keyword-only.
    assert cascade.reorient(7, orientation=-1) == -7
    assert cascade.reorient(7, orientation=1) == 7
    assert cascade.reorient(7, orientation=0) == 7
    # orientation is keyword-only: a positional second arg is a TypeError.
    with pytest.raises(TypeError):
        cascade.reorient(7, -1)  # noqa: PLE  (intentional misuse)


def test_reorient_drives_as_then_stage_with_bound_orientation():
    # The finding: reorient must be invokable as an op= stage. The runner
    # pipes the value into arg0; orientation is the bound kwarg.
    ch = Chain("neg").then("reorient", orientation=-1)
    assert ch.run(5) == -5
    assert ch.run(-5) == 5
    assert Chain("idy").then("reorient", orientation=1).run(5) == 5


def test_reorient_composes_after_magnitude_in_a_chain():
    # magnitude (data-first) → reorient(orientation=-1): |x| then negate.
    ch = Chain("absneg").then("magnitude").then("reorient", orientation=-1)
    assert ch.run(-3.0) == -3.0
    assert ch.run(3.0) == -3.0


def test_reorient_drives_from_toml_chain():
    # The kwarg is forwarded from a TOML [[stage]] (non-reserved key →
    # ch.then("reorient", orientation=-1)), exactly like best_rational_signed.
    spec = """
name = "toml-neg"
[[stage]]
op = "reorient"
orientation = -1
"""
    assert run_toml_chain(spec, 9) == -9
    assert run_toml_chain(spec, -9) == 9


def test_omega7_axis_still_negates_per_element():
    # The internal iω₇ stream-transform (_transform_omega7 = per-element
    # reorient(orientation=-1)) is unaffected by the arg reorder.
    from srmech.amsc.cascade.parallel import _transform_omega7
    assert list(_transform_omega7([1, -2, 3])) == [-1, 2, -3]


# ── rc23: parallel_sectors body-kwarg channel (the §16.1 parallel_body= half).
#    parallel_sectors now forwards **body_kwargs (functools.partial), so an op
#    with bound kwargs reaches the body. NOTE: reorient is a SCALAR op, so it
#    is a valid parallel_body only at n_sectors=1 (the identity sector); at
#    n_sectors≥2 the chirality stream-transforms iterate the stream per-element,
#    which a scalar op can't consume. The kwarg channel is the generic fix; the
#    n_sectors=1 case proves the bound orientation reaches the body. ──


def test_reorient_parallel_body_kwarg_channel_binds_orientation():
    # The bound orientation reaches the body via functools.partial. Sector 0 is
    # the identity transform, so its dual is body(v) = reorient(v, orientation).
    neg = Chain("pneg").parallel_sectors(
        "reorient", n_sectors=1, combine="sector0", orientation=-1)
    assert neg.run(4) == -4
    idy = Chain("pidy").parallel_sectors(
        "reorient", n_sectors=1, combine="sector0", orientation=1)
    assert idy.run(4) == 4


def test_reorient_parallel_body_kwarg_from_toml():
    spec = """
name = "toml-pneg"
[[stage]]
parallel_body = "reorient"
n_sectors = 1
combine = "sector0"
orientation = -1
"""
    assert run_toml_chain(spec, 6) == -6


def test_reorient_scalar_not_a_multisector_parallel_body():
    # Honest limitation: reorient is scalar, so n_sectors≥2 (where the iω₇/γ₅
    # transforms iterate the stream) is a category error — not a kwarg-channel
    # failure. Documents why reorient's practical drivability is the op= path.
    with pytest.raises(TypeError):
        Chain("p2").parallel_sectors(
            "reorient", n_sectors=2, combine="sector0", orientation=-1).run(4)
