"""The DSL chain runner's CONTRACT-A carrier guard — v0.9.0rc479 (`#T1188`).

WHAT THIS EXISTS FOR, and it is a defect CI found that every local gate missed.

Contract A makes a caller's decimal text the exact rational it names, and rc479
gave five cascade ops an exact rung. Each of those ops carries its own guard
(G1-G3) inside its ``_try_native_*``: a non-float leaf declines the C peer,
because no C value layer in this library holds a rational (``dv_value_t`` and
``srmech_mval_t`` are both ``double``).

**The DSL chain runner does not go through those guards.** It marshals the
whole chain to ``srmech_dsl_chain_run`` and the C interpreter runs the leaf
itself, so the op-level guard is invisible one layer up and the identical
divergence reappears. MEASURED at rc479 before this guard existed, on four CI
cells at once:

    chain("par").parallel_sectors("autocorrelation", n_sectors=1)
        seed [7]              native [49.0]                pure [Q(49, 1)]
        seed [7], mean, ns=3  native [16.333333333333332]  pure [Q(49, 3)]

Same call, same version, no error on either side — the silent-wrong-answer
class, which is the one this project ranks first.

WHAT THIS FILE PINS
    1. **The roster is the DERIVED one.** ``_EXACT_CAPABLE_OPS`` is seeded in
       the hot dispatch path, and this re-derives it from the live tool schema
       (a cascade op whose DECLARED return type names ``Q`` or ``Qalg``) and
       asserts EQUALITY. A future op that gains an exact rung joins the roster
       or turns this red; one that loses it likewise.
    2. **The guard FIRES** where the pure projection answers exactly.
    3. **The guard is NOT over-broad** — a chain whose ops cannot answer
       exactly still runs in C over the same int seed.
    4. **It can return otherwise.** With the guard bypassed, the two
       projections are measured DIFFERENT on the same input. A guard test that
       cannot show the divergence it prevents is asserting a comment.
    5. Both predicates, over the shapes that actually reach them.

WHAT IT DOES NOT PROVE
    Only the **DSL** chain runner (``srmech_dsl_chain_run``) is in scope. The
    cascade chain interpreter (``srmech_chain_run``) is a different C entry
    with its own harnesses (``test_c_cascade_value_parity_rc450``,
    ``test_c_cascade_parity_ratchet_rc446``), which project to doubles on BOTH
    sides through ``tests/_carrier_projection.py`` and therefore ask a
    different question. Nothing here says anything about that one.

numpy-free (stdlib only).
"""
from __future__ import annotations

import re

import pytest

from srmech import _native
from srmech.dsl import chain
from srmech.dsl._chain import (
    _EXACT_CAPABLE_OPS,
    _NATIVE_MISS,
    _has_non_float_number,
    _names_an_exact_capable_op,
)

_HAS = (
    _native.HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_dsl_chain_run")
)
_needs_native = pytest.mark.skipif(
    not _HAS, reason="native srmech_dsl_chain_run not present (pure-only build)"
)


def _derived_roster() -> frozenset:
    """The set the roster must equal, read from the LIVE declarations.

    The property is "this op's pure projection can answer in a carrier the C
    projection has no room for", and the tree already records it as a declared
    return type that names ``Q`` or ``Qalg``. Derived here rather than listed,
    so the two cannot drift.
    """
    from srmech.introspect.tool_schema import get_tool_schema
    out = set()
    for t in get_tool_schema().tools:
        if ".cascade." not in t.name:
            continue
        rt = getattr(getattr(t, "returns", None), "type", None)
        if rt and re.search(r"\bQ(alg)?\b", rt):
            out.add(t.name.rsplit(".", 1)[-1])
    return frozenset(out)


# ── 1. the roster equals its derivation ─────────────────────────────────────

def test_the_seeded_roster_equals_the_live_derivation() -> None:
    """``_EXACT_CAPABLE_OPS`` == the ops whose declared return names Q / Qalg.

    An EQUALITY, not a containment, and in both directions on purpose: a
    missing name is an unguarded wrong answer, and a surplus one is a chain
    quietly losing its C path for no reason. The failure message names the
    difference rather than the totals, because "26 != 25" is not a remedy.
    """
    derived = _derived_roster()
    assert derived, (
        "the derivation found NOTHING — the predicate has stopped observing "
        "(a renamed `returns.type`, or a tool schema that no longer carries "
        "declared types), and this test would then pass vacuously for an "
        "empty roster")
    missing = sorted(derived - _EXACT_CAPABLE_OPS)
    surplus = sorted(_EXACT_CAPABLE_OPS - derived)
    assert not missing and not surplus, (
        f"srmech.dsl._chain._EXACT_CAPABLE_OPS has drifted from the declared "
        f"return types.\n"
        f"  UNGUARDED (declare exact, absent from the roster): {missing}\n"
        f"     -> a DSL chain naming one of these over a non-float seed runs "
        f"in C and answers in `double` where the pure loop answers exactly.\n"
        f"  SURPLUS (in the roster, no longer declare exact): {surplus}\n"
        f"     -> those chains defer to Python for nothing.")


def test_the_roster_is_not_just_the_ops_this_rc_moved() -> None:
    """The roster is the PROPERTY's population, not rc479's changelog.

    Stated as its own assertion because the first draft of the guard seeded
    exactly the five ops this release widened, which would have made it a
    patch for one rc while leaving every op that was already exact-capable
    unguarded on the same code path.
    """
    moved_by_rc479 = {"autocorrelation", "quaternion_dft", "octonion_dft",
                      "as_quat4", "as_oct8"}
    assert moved_by_rc479 <= _EXACT_CAPABLE_OPS
    older = _EXACT_CAPABLE_OPS - moved_by_rc479
    assert older, (
        "the roster is exactly the five ops rc479 widened, so it is a "
        "release patch rather than the property's population")


# ── 2. the guard fires ──────────────────────────────────────────────────────

@_needs_native
@pytest.mark.parametrize("seed", [[7], [1, 2, 3, 4], [-3, 5, -7, 11],
                                  [True, False]])
def test_an_exact_capable_body_declines_on_a_non_float_seed(seed) -> None:
    """A chain naming an exact-capable op over a non-float seed goes to pure."""
    ch = chain("g").parallel_sectors("autocorrelation", n_sectors=1)
    assert ch._run_native(list(seed)) is _NATIVE_MISS, (
        f"the C path RAN for seed {seed!r}; its pure projection answers in an "
        f"exact carrier that a C `double` cannot hold")


@_needs_native
@pytest.mark.parametrize("seed", [[1.5, -2.25, 0.0, 3.0], [0.0, 0.0],
                                  [1.0, 1e17, 1.0]])
def test_the_same_body_still_runs_in_c_on_an_all_float_seed(seed) -> None:
    """The guard is a CARRIER guard, not an op ban: floats are untouched."""
    ch = chain("g").parallel_sectors("autocorrelation", n_sectors=1)
    got = ch._run_native(list(seed))
    assert got is not _NATIVE_MISS, (
        f"the C path declined an all-float seed {seed!r} — the guard has "
        f"stopped being about the carrier and is now about the op")


@_needs_native
def test_a_non_exact_op_still_runs_in_c_on_an_int_seed() -> None:
    """NOT over-broad. ``chiral_flip`` declares no exact return, so an int
    seed keeps its C path and its int result."""
    ch = chain("g").parallel_sectors("chiral_flip", n_sectors=1)
    got = ch._run_native([1, 2, 3, 4])
    assert got is not _NATIVE_MISS, (
        "an int seed lost its C path on an op that cannot answer exactly — "
        "the guard is declining on the seed alone")


# ── 3. it can return otherwise ──────────────────────────────────────────────

@_needs_native
def test_without_the_guard_the_two_projections_disagree() -> None:
    """THE ANTI-VACUITY CONTROL, and the reason this file is not a comment.

    Bypass the guard by handing the C runner an all-float projection of the
    same seed — which is what it used to be handed implicitly — and compare
    against the pure answer for the seed as given. They must DIFFER, in value
    and in type. If they ever agree, the guard is guarding nothing and this
    file has stopped measuring.
    """
    ch = chain("g").parallel_sectors("autocorrelation", n_sectors=1)
    bypass = ch._run_native([7.0])            # the guard cannot see a float
    assert bypass is not _NATIVE_MISS, "the bypass did not reach C"

    pure = chain("g").parallel_sectors("autocorrelation", n_sectors=1)
    pure._native_ir[:] = [None] * len(pure._native_ir)
    exact = pure.run([7])                     # the seed AS GIVEN

    assert repr(bypass) != repr(exact), (
        f"the C answer {bypass!r} and the exact answer {exact!r} are "
        f"indistinguishable, so the guard prevents nothing")
    # and the exact one IS exact — 49/1, decided by the integers
    leaf = exact[0]
    assert type(leaf).__name__ == "Q", type(leaf).__name__
    assert leaf.numerator == 49 and leaf.denominator == 1
    assert isinstance(bypass[0], float) and bypass[0] == 49.0


# ── 4. the two predicates, over the shapes that reach them ──────────────────

@pytest.mark.parametrize("value,want", [
    (1.5, False), (0.0, False), (-0.0, False),
    (7, True), (True, True), (0, True),
    ("1.5", False), (None, False), ([], False),
    ([1.0, 2.0], False), ([1.0, 2], True), ([[1.0], [2]], True),
    ({"a": [1.0]}, False), ({"a": [1]}, True),
])
def test_has_non_float_number(value, want) -> None:
    """A ``bool`` answers True because it is an ``int`` and
    ``autocorrelation([True, False])`` is exact in the pure projection — the
    same reading G1 takes."""
    assert _has_non_float_number(value) is want


def test_has_non_float_number_sees_an_exact_carrier() -> None:
    """A ``Q`` is not a float and must answer True without the walker knowing
    the class by name."""
    from srmech.math.q import Q
    assert _has_non_float_number(Q(1, 3)) is True
    assert _has_non_float_number([1.0, Q(1, 3)]) is True


def test_names_an_exact_capable_op_walks_the_whole_descriptor() -> None:
    """An op name reaches the C grammar through several fields, so the walk is
    over the descriptor rather than over one key."""
    assert _names_an_exact_capable_op(
        [{"kind": "parallel", "parallel": {"body": "autocorrelation"}}])
    assert _names_an_exact_capable_op([{"op": "autocorrelation"}])
    assert _names_an_exact_capable_op(
        [{"loop": {"chain": [{"op": "quaternion_dft"}]}}])
    assert not _names_an_exact_capable_op(
        [{"kind": "parallel", "parallel": {"body": "chiral_flip"}}])
    assert not _names_an_exact_capable_op([])
