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


# NOTE (rc22 scope): ``parallel_body="reorient"`` with a bound orientation is
# NOT yet supported — Chain.parallel_sectors(body, *, n_sectors, combine) has
# no body-kwarg channel, so a required-kwarg op (reorient's orientation) can't
# be a parallel_body. That is a separate parallel_sectors feature (forward
# **body_kwargs), tracked as the follow-up; this rc fixes the op=/.then/TOML
# drivability (the primary §16.1 finding). ``parallel_body`` ops with all-
# defaulted kwargs (e.g. best_rational_signed) already work.
