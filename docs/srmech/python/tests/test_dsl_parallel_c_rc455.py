"""The Klein-4 ``parallel_body`` fan-out in C — v0.9.0rc455.

``srmech_dsl_chain_run`` returned ``SRMECH_ERR_NOT_IMPL`` for every
``parallel_body`` stage from rc182 to rc454, guarded by the comment
``/* host-thread fan-out */``. It was the last of the six DSL combinators
missing from the C projection, and the justification was DEAD:

* the four sectors read ONLY their own ``T_s(x)`` (F233's whole content), and
  :func:`srmech.cascade.parallel.parallel_sector_dispatch` collects the futures
  **by sector index**, so completion order cannot reach the value — measured
  over 72 configs x 30 repeats, 0 nondeterministic results;
* ``srmech_compose_run.c`` has shipped a complete SERIAL Klein-4 kernel since
  rc452 (``cr_psd_*``) whose own header says
  *"THE SECTORS RUN SERIALLY HERE AND THAT IS NOT AN APPROXIMATION"*.

So the C arm mirrors those serial kernels. It does NOT call
``srmech_cascade_parallel_sector_dispatch``, for two measured reasons: that op
computes only sector duals (no combine, no output shaping), and it spawns real
threads whose bodies would carve from one shared bump arena on a non-atomic
``b->cur = p + n`` — a data race.

WHAT THIS FILE PINS
    1. Python-vs-C BYTE identity across all five combine modes
       (bundle / mean / sector0 / concat / none) x n_sectors 1..4 x both legal
       bodies x a carrier table, and across a SCALE sweep.
    2. THE SECTOR ORDER. ``bundle``/``mean`` fold left to right in SECTOR
       ORDER, and float addition is not associative, so that order is part of
       the value. ``dsl_psd_bundle_at`` declares it load-bearing in its own
       ⚠️ note; rc455 shipped it UNGATED, and reversing that loop left all
       327 rows of the three parallel/arena/combinator files green. Closed
       here by a magnitude-spread carrier row plus a named assertion — the
       mutation now scores 4 reds.
    3. The 4-op (measured: 5-op) illegal-body NEGATIVE CONTROL. The C leaf table
       holds seven ops; only two are legal parallel bodies. The other five BUILD
       fine as a ``parallel_body=`` and raise ``TypeError`` at run in Python, so
       C must DECLINE them, never compute.
    4. INT PRESERVATION. Python's ``bundle`` is builtin ``sum``, whose seed is an
       INT 0 — an all-int input stays int. Seeding the C accumulator with 0.0
       would silently float every integer result and every value-equality
       assertion would still pass, because ``12 == 12.0``.
    5. The invalid-``combine`` hole: ``combine='nope'`` BUILDS from an ordinary
       Python chain and raises only at ``.run()``, so the native-IR predicate is
       "one of the FOUR reducer names", never "a string".

numpy-free (stdlib only).
"""
from __future__ import annotations

import pytest

from srmech import _native
from srmech.cascade.parallel import COMBINE_REDUCERS, KLEIN4_SECTOR_CAP
from srmech.dsl import chain
from srmech.dsl._chain import _NATIVE_MISS, _parallel_native_desc

_HAS = (
    _native.HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_dsl_chain_run")
)
_needs_native = pytest.mark.skipif(
    not _HAS, reason="native srmech_dsl_chain_run not present (pure-only build)"
)

#: The five combine modes. ``None`` is the per-sector list-of-lists and is the
#: fifth mode, not the absence of one.
_COMBINES = list(COMBINE_REDUCERS) + [None]

#: The two ops in the seven-entry C leaf table that ARE sequence -> sequence.
_LEGAL_BODIES = ("chiral_flip", "autocorrelation")

#: The rest of that table. MEASURED: all five build fine as a ``parallel_body``
#: and every one raises ``TypeError`` at run. The brief for this work named four;
#: ``best_rational_signed`` is the fifth and behaves identically.
_ILLEGAL_BODIES = ("magnitude", "reorient", "pin_slot_at_zero",
                   "best_rational_signed", "net_chirality")


def _mk(body, ns, combine):
    return chain("par").parallel_sectors(body, n_sectors=ns, combine=combine)


def _pure(body, ns, combine, value):
    """Run the same chain with every native IR slot blanked — the pure path."""
    ch = _mk(body, ns, combine)
    ch._native_ir[:] = [None] * len(ch._native_ir)
    return ch.run(value)


def _kinds(v):
    """The TYPE tree, so 12 and 12.0 are distinguishable."""
    if isinstance(v, list):
        return [_kinds(e) for e in v]
    return type(v).__name__


# ─────────────────────────────────────────────────────────────────────
# 1. Python == C, byte for byte
# ─────────────────────────────────────────────────────────────────────

_CARRIERS = {
    "int4": [1, 2, 3, 4],
    "int1": [7],
    "empty": [],
    "float4": [1.5, -2.25, 0.0, 3.0],
    "signed_zero": [0.0, 0.0],
    "int_neg": [-3, 5, -7, 11],
    # ⚠️ THE MAGNITUDE-SPREAD ROW, AND IT IS NOT DECORATION. Every other carrier
    # here has values within a few orders of each other, so float addition is
    # associative on all of them to the last bit and the whole matrix above was
    # BLIND to the sector ORDER — the property dsl_psd_bundle_at declares
    # load-bearing in its own ⚠️ comment. Measured: reversing that loop
    # (`for (s = ns; s-- > 0u;)`) left all 327 rows of this file, of
    # test_dsl_chain_arena_scale_rc455 and of test_dsl_combinators_c_rc182
    # GREEN. A parametrized cell whose inputs cannot distinguish the claim is
    # vacuous, and this row is what makes it able to return otherwise:
    # autocorrelation x n_sectors=3 over these three values puts a 1e34 and a
    # -1e34 in the same column as a 2e17, so the 2e17 survives left-to-right
    # and is annihilated right-to-left. See
    # test_sector_order_is_part_of_the_value below for the named assertion.
    "catastrophic": [1.0, 1e17, 1.0],
}


@_needs_native
@pytest.mark.parametrize("body", _LEGAL_BODIES)
@pytest.mark.parametrize("ns", [1, 2, 3, 4])
@pytest.mark.parametrize("combine", _COMBINES)
@pytest.mark.parametrize("carrier", sorted(_CARRIERS))
def test_parallel_native_equals_pure(body, ns, combine, carrier):
    """The C fan-out reproduces the threaded Python one BY REPR, not by ==.

    ``repr`` rather than ``==`` on purpose: ``0.0 == -0.0`` and ``12 == 12.0``,
    and both distinctions are reachable here (the iw7 axis is a sign flip, so a
    0.0 anywhere in the input puts a -0.0 into a sector result; and ``bundle``
    must preserve int).

    ⚠️ NO SKIP-ON-DEFER BRANCH. Every carrier in the table is one C runs today
    (measured: 280/280 rows native, 0 misses), so a tolerated deferral would let
    the whole matrix go vacuous without a single red mark — the exact shape of a
    green gate that has stopped measuring. A carrier that starts deferring is a
    parity regression and must be seen as one. Mixed int/float lists are absent
    from the table BY NAME rather than by silent skip: ``leaf_chiral_flip``
    declines them (a pre-rc455 gate), so they were never in scope here.
    """
    value = list(_CARRIERS[carrier])
    native = _mk(body, ns, combine)._run_native(value)
    expect = _pure(body, ns, combine, value)
    assert native is not _NATIVE_MISS, "the C path must RUN for this carrier"
    assert repr(native) == repr(expect)
    assert _kinds(native) == _kinds(expect)


@_needs_native
@pytest.mark.parametrize("ns,combine", [(1, "concat"), (4, "concat"),
                                        (1, None), (4, None),
                                        (4, "bundle"), (4, "mean")])
@pytest.mark.parametrize("n", [16, 256, 4096])
def test_parallel_native_equals_pure_at_scale(ns, combine, n):
    """The same identity at 16 / 256 / 4096 elements.

    ⚠️ THIS SWEEP IS THE POINT, not decoration. Every pre-rc455 C-parity proof
    for this runner ran at <= 18 elements, and the arena defect this rc also
    fixes made the C path silently stop running at 166. A parity corpus that
    lives entirely below the cliff cannot see the cliff.
    """
    value = list(range(n))
    native = _mk("chiral_flip", ns, combine)._run_native(value)
    assert native is not _NATIVE_MISS, "the C path must RUN at this size"
    assert repr(native) == repr(_pure("chiral_flip", ns, combine, value))


#: The minimal reproducer for the sector-ORDER property. Three values spanning
#: 17 orders of magnitude, run through ``autocorrelation`` at ``n_sectors=3``.
_ORDER_SEED = [1.0, 1e17, 1.0]


@_needs_native
@pytest.mark.parametrize("combine", ["bundle", "mean"])
def test_sector_order_is_part_of_the_value(combine):
    """``bundle``/``mean`` MUST sum left to right in SECTOR ORDER.

    ⚠️ THIS PROPERTY WAS DECLARED LOAD-BEARING AND LEFT UNGATED. ``dsl_psd_bundle_at``
    carries a ⚠️ note reading *"LEFT TO RIGHT IN SECTOR ORDER — float addition is
    not associative, so the order is part of the value"*, and the rc455 report
    measured it. Nothing tested it: reversing that loop to
    ``for (s = ns; s-- > 0u;)`` left all 327 rows of this file, of
    :mod:`test_dsl_chain_arena_scale_rc455` and of
    :mod:`test_dsl_combinators_c_rc182` GREEN. A randomized differential finds
    it instantly (479 divergences in 4000 trials) and every one of them lands in
    the ``autocorrelation x n_sectors=3`` cell — ``chiral_flip``'s four sector
    duals are identical, and at ns=2/4 the autocorrelation duals cancel exactly.

    ⚠️ THE SECOND HALF IS WHAT MAKES THE FIRST A MEASUREMENT. Asserting only
    "C == pure" would still pass under a reversed C loop if the pure side were
    reversed too, and would pass VACUOUSLY on any carrier whose values are
    within a few orders of each other. So this also computes the reversed-order
    fold from the SAME sector duals and requires it to DIFFER — if that ever
    stops differing, the seed no longer distinguishes the claim and this test
    has stopped observing, which is a failure and not a pass.
    """
    sectors = _mk("autocorrelation", 3, None)._run_native(list(_ORDER_SEED))
    assert sectors is not _NATIVE_MISS, "the C path must RUN for the order seed"
    assert sectors == [[1e34, 2e17, 2e17], [-1e34, -2e17, -2e17],
                       [2e17, 2e17, 1e34]], sectors

    # ⚠️ NAIVE ACCUMULATION, NOT builtin ``sum`` — and this is the whole point.
    # CPython 3.12 gave ``sum()`` NEUMAIER COMPENSATED summation for floats, which
    # is ORDER-INSENSITIVE by construction. Using it here modelled the C loop with
    # a DIFFERENT ALGORITHM than the one under test, so on 3.12+ both folds agreed
    # and this test correctly declared itself vacuous — it was written and passed
    # on 3.10, and CI's 3.12/3.13/3.14 cells caught it on the first run.
    # MEASURED, same seed, same sectors:
    #   3.10.12  sum() fwd 2e+17 rev 0.0     naive fwd 2e+17 rev 0.0
    #   3.14.4   sum() fwd 2e+17 rev 2e+17   naive fwd 2e+17 rev 0.0
    # Re-choosing the seed CANNOT fix it: compensation recovers the lost low-order
    # term for any seed inside its range, so the discriminator dissolves whatever
    # values are chosen. The ORACLE was wrong, not the seed. Keep this loop naive.
    def _naive_fold(values):
        acc = 0.0
        for v in values:
            acc += v
        return acc

    n = len(sectors[0])
    forward = [_naive_fold([s[i] for s in sectors]) for i in range(n)]
    reversed_ = [_naive_fold([s[i] for s in reversed(sectors)]) for i in range(n)]
    assert forward != reversed_, (
        f"the seed {_ORDER_SEED} no longer distinguishes summation order "
        f"(both folds give {forward}) — this test has gone vacuous and the "
        f"seed must be re-chosen, not the assertion relaxed")
    assert forward == [2e17, 2e17, 1e34] and reversed_ == [0.0, 2e17, 1e34]

    expect = forward if combine == "bundle" else [x / 3 for x in forward]
    native = _mk("autocorrelation", 3, combine)._run_native(list(_ORDER_SEED))
    assert native is not _NATIVE_MISS
    assert repr(native) == repr(expect), (
        f"C folded the sectors in the wrong order: got {native}, want {expect} "
        f"(the reverse-order fold is {reversed_})")
    assert repr(native) == repr(
        _pure("autocorrelation", 3, combine, list(_ORDER_SEED)))


@_needs_native
def test_parallel_chains_and_nests_in_c():
    """A recombining fan-out is stream -> stream, so it CHAINS — in C too."""
    ch = (chain("par").parallel_sectors("chiral_flip", combine="bundle")
          .parallel_sectors("chiral_flip", combine="mean"))
    native = ch._run_native([1, 2, 3])
    assert native is not _NATIVE_MISS
    ch2 = (chain("par").parallel_sectors("chiral_flip", combine="bundle")
           .parallel_sectors("chiral_flip", combine="mean"))
    ch2._native_ir[:] = [None] * len(ch2._native_ir)
    assert repr(native) == repr(ch2.run([1, 2, 3])) == repr([4.0, 8.0, 12.0])


# ─────────────────────────────────────────────────────────────────────
# 2. NEGATIVE CONTROL — an in-table body that is not a legal parallel body
# ─────────────────────────────────────────────────────────────────────


@_needs_native
@pytest.mark.parametrize("body", _ILLEGAL_BODIES)
def test_illegal_in_table_body_declines(body):
    """C DECLINES an op that is in its leaf table but not sequence -> sequence.

    ⚠️ THE TRAP THIS CLOSES. The obvious implementation dispatches the body
    through ``dsl_leaf_dispatch``, which knows all seven ops — and then four of
    the seven compute a value on a shape Python refuses. A projection that
    ACCEPTS a declaration the other rejects has not got a capability gap; it has
    a wrong answer to a malformed program, which is worse because the malformed
    program looks like it worked. Both halves are asserted: C misses, AND the
    pure path raises.
    """
    ch = _mk(body, 4, "bundle")
    assert ch._run_native([1.0, 2.0, 3.0, 4.0]) is _NATIVE_MISS
    with pytest.raises(TypeError):
        _pure(body, 4, "bundle", [1.0, 2.0, 3.0, 4.0])


@_needs_native
def test_tuple_seed_declines_rather_than_guessing_a_carrier_type():
    """A TUPLE seed DEFERS — a deliberate decline, pinned so it stays one.

    Python's two Klein-4 axes disagree about the carrier type here: the iw7 arm
    is a list comprehension and always returns a ``list``, while the g5 arm is
    ``seq[::-1]`` and PRESERVES ``tuple``. So the four sector results do not
    share one carrier type, and C has no single right answer to reproduce.
    Measured: pure returns ``[12, 8, 4]`` for ``(1, 2, 3)``; C declines and the
    pure path produces exactly that. This is a coverage gap, NOT a divergence —
    recorded as a row so it cannot quietly become a wrong answer instead.
    """
    ch = chain("par").parallel_sectors("chiral_flip", n_sectors=4,
                                       combine="bundle")
    assert ch._run_native((1, 2, 3)) is _NATIVE_MISS
    assert _pure("chiral_flip", 4, "bundle", (1, 2, 3)) == [12, 8, 4]


@_needs_native
@pytest.mark.parametrize("seed", [5, 5.0, "abc", [[1, 2], [3, 4]], [1, None]])
def test_non_stream_seed_declines_and_pure_raises(seed):
    """A seed that is not a flat numeric stream declines; pure then raises."""
    ch = chain("par").parallel_sectors("chiral_flip", n_sectors=4,
                                       combine="bundle")
    assert ch._run_native(seed) is _NATIVE_MISS
    with pytest.raises(TypeError):
        _pure("chiral_flip", 4, "bundle", seed)


@_needs_native
@pytest.mark.parametrize("body", _LEGAL_BODIES)
def test_legal_bodies_do_run(body):
    """The vacuity control for the row above: the two legal bodies DO run.

    Without this, "every body declines" would satisfy the negative control.
    """
    assert _mk(body, 4, "bundle")._run_native([1.0, 2.0, 3.0, 4.0]) \
        is not _NATIVE_MISS


# ─────────────────────────────────────────────────────────────────────
# 3. INT PRESERVATION — the carrier's own zero, not 0.0
# ─────────────────────────────────────────────────────────────────────


@_needs_native
@pytest.mark.parametrize("combine", ["bundle", "sector0", "concat", None])
def test_int_input_stays_int_through_c(combine):
    """An all-int input survives the fan-out as int on the four INT-preserving
    reducers.

    ⚠️ ``==`` CANNOT SEE THIS DEFECT. ``[16, 12, 8, 4] == [16.0, 12.0, 8.0, 4.0]``
    is ``True`` in Python, so a 0.0 accumulator seed passes every value
    assertion in this file and every one in the rest of the suite. Only the type
    tree catches it, and only the WIRE shows it in C ({"k":"i"} vs {"k":"f"}).
    """
    native = _mk("chiral_flip", 4, combine)._run_native([1, 2, 3, 4])
    assert native is not _NATIVE_MISS
    kinds = _kinds(native)
    # combine=None yields the per-sector LIST OF LISTS; flatten one level.
    flattened = [k for row in kinds for k in row] if combine is None else kinds
    assert set(flattened) == {"int"}, (
        "an int input must stay int: Python's bundle is builtin sum, whose "
        "seed is an INT 0"
    )
    assert _kinds(native) == _kinds(_pure("chiral_flip", 4, combine, [1, 2, 3, 4]))


@_needs_native
def test_mean_floats_an_int_input_in_c():
    """``mean`` is the one reducer that MUST change kind: Python divides with
    ``/``, which is true division, so an int bundle becomes float."""
    native = _mk("chiral_flip", 4, "mean")._run_native([1, 2, 3, 4])
    assert native is not _NATIVE_MISS
    assert set(_kinds(native)) == {"float"}
    assert repr(native) == repr(_pure("chiral_flip", 4, "mean", [1, 2, 3, 4]))


@_needs_native
@pytest.mark.parametrize("combine", ["bundle", "mean"])
def test_int64_overflow_and_min_defer(combine):
    """Python ints are unbounded; int64 is not, so C DEFERS rather than wrapping.

    Three edges, each a different arm: an accumulator past INT64_MAX, an
    INT64_MIN element the iw7 sign re-application cannot negate, and (for
    ``mean``) a sum past 2**53 where Python's exact int/int true division stops
    agreeing with ``(double)/(double)``.
    """
    imax = (1 << 63) - 1
    imin = -(1 << 63)
    for value in ([imax, imax], [imin, 1]):
        native = _mk("chiral_flip", 4, combine)._run_native(list(value))
        assert native is _NATIVE_MISS, (
            "an int64 edge must defer to pure, never wrap or clamp"
        )
        assert _pure("chiral_flip", 4, combine, list(value)) is not None


# ─────────────────────────────────────────────────────────────────────
# 4. The invalid-`combine` hole, and the rest of the IR predicate
# ─────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("combine", ["nope", "none", "Bundle", "", "sum",
                                     "BUNDLE", "concat "])
def test_invalid_combine_name_emits_no_native_ir(combine):
    """An invalid reducer NAME must not reach the C runner.

    ⚠️ REACHABLE WITHOUT A BARE-C HOST. ``parallel_sectors('chiral_flip',
    combine='nope')`` BUILDS fine and raises ``ValueError`` only at ``.run()``,
    so a "combine is a string" predicate would have emitted native IR for a name
    Python refuses, and C would then have had to invent a behaviour for it.
    ``'none'`` is in this list on purpose: it is NOT Python's spelling of
    ``combine=None`` (which rides the wire as JSON ``null``) and is itself an
    invalid reducer name.
    """
    assert _mk("chiral_flip", 4, combine)._native_ir[0] is None
    with pytest.raises(ValueError):
        _pure("chiral_flip", 4, combine, [1, 2, 3])


def test_callable_combine_emits_no_native_ir():
    """A caller-supplied reducer is Python-only — there is nothing to send."""
    assert _mk("chiral_flip", 4, lambda rs: rs[0])._native_ir[0] is None


def test_body_kwargs_emit_no_native_ir():
    """A bound body kwarg defers: the C body is leaf-only and takes no stage."""
    ch = chain("par").parallel_sectors("reorient", orientation=-1,
                                       combine="bundle")
    assert ch._native_ir[0] is None


@pytest.mark.parametrize("combine", list(COMBINE_REDUCERS) + [None])
def test_valid_combine_emits_native_ir(combine):
    """The vacuity control: all five VALID modes DO emit IR.

    Without it, ``_parallel_native_desc`` returning ``None`` unconditionally
    would satisfy every rejection row above.
    """
    ir = _mk("chiral_flip", 4, combine)._native_ir[0]
    assert ir is not None
    assert ir["parallel_body"] == "chiral_flip"
    assert ir["n_sectors"] == 4
    assert ir["combine"] == combine     # None rides as JSON null, not "none"


def test_native_desc_reads_the_reducer_set_from_its_ssot():
    """The accepted names are the dispatcher's own tuple, not a second copy.

    A third notion of "which reducers exist" is exactly the drift class this
    tree has measured before, so the predicate reads
    :data:`srmech.cascade.parallel.COMBINE_REDUCERS` directly.
    """
    for name in COMBINE_REDUCERS:
        assert _parallel_native_desc("chiral_flip", 4, name, {}) is not None
    assert _parallel_native_desc("chiral_flip", 4, None, {}) is not None
    for ns in (0, KLEIN4_SECTOR_CAP + 1, -1, True, 2.0):
        assert _parallel_native_desc("chiral_flip", ns, "bundle", {}) is None
