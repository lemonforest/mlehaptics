"""v0.9.0rc452 (`#T1166`) — EXACT ℚ END TO END, both projections, one wire.

THE ACCEPTANCE CRITERION THIS FILE REINSTATES. ADJ-4 broke it and the rc452
ruling overturned ADJ-4 and put it back as the headline: ``rational_add`` ->
``reorient`` returns an exact rational in BOTH projections with byte-identical
wires. Through rc451 it threaded in NEITHER — Python's ``rational_add`` returned
a ``(num, den)`` tuple that ``reorient`` could only negate by raising, and C's
``cr_op_reorient`` had no ``CR_RATIONAL`` arm at all and declined with
``SRMECH_ERR_NOT_IMPL``.

WHAT IS PINNED HERE, and why each pin exists rather than being implied by the
one above it:

  1. THE HEADLINE, three ways — the native value, the FORCED-PURE value, and
     the C wire BYTES. Value-only would pass under a reader that rebuilt the
     right number from the wrong kind; bytes-only would pass under a Python
     half that never ran.
  2. THE FRESH-CARRIER REGRESSION. The two-step headline passes even under an
     in-place sign flip, so on its own it is not a test of the thing most
     likely to be wrong. Config C's rev2 negated ``v->num->sign`` in place on a
     real rebuilt library; step outputs PERSIST in the chain arena, so a later
     ``@step[0].output`` read saw the corrupted value and a three-step chain
     returned -5/6 where 5/6 is correct — at ``rc=0``, with a well-formed wire,
     and no value-level gate anywhere in the tree able to see it. This is the
     test that can go red on that exact silent-wrong-answer class.
  3. A BIGNUM NUMERATOR. Both A and D prototyped the arm at int64; only C ran
     bigints, and only in a prototype. The shipped arm negates through
     ``srmech_bigint_t``, so it is exercised past the int64 ceiling here.
  4. THE ZERO NUMERATOR. ``srmech_bigint_t``'s invariant is ``sign == 0 iff
     n == 0``; stamping -1 on a zero would build a carrier that prints "-0".
  5. THE MUTUAL DECLINE on a bare ``[num, den]`` list — see the test's own
     docstring. It is a PARITY pin, and it disagrees with rc452's plan.

⚠️ WITHOUT THE NATIVE LIBRARY THIS FILE FAILS — UNLESS THE RUN DECLARES ITSELF
PURE. A stale or absent ``.so`` makes every native gate skip silently green, the
exact trap this arc has hit repeatedly, and this is the file that certifies
rc452's DoD: a green it could produce while measuring nothing would be
worthless. So a missing library is a FAILURE here, and it says LOAD_ERROR.

The one exception is STATED, never inferred. ``tests/_native_gate.py`` is the
tree's single resolution of that rule (`#T843`) against the rc351 ``fallback
(pure-Python, no native)`` CI cell, which runs ``pytest tests/`` UNFILTERED with
no library at all, because the pure / Pyodide / WASM projection must still be
exercised. ``SRMECH_EXPECT_PURE=1`` is the discriminator and that cell is the
only thing that sets it. Every C-touching test below therefore goes through
:func:`require_native`, exactly as tests/test_c_cascade_value_parity_rc450.py
does — that file was corrected at rc450 for this same defect, when three tests
reached ``_c_run`` ungated while their six siblings gated and turned shard 1/6
red on rc450's first CI round.

⚠️ AS FIRST WRITTEN THIS FILE HARD-FAILED THAT CELL: 15 FAILURES, NOT SKIPS —
measured, with the ``.so`` moved aside, both with and without the variable set.
The gate is not a softening of the ABI assertions below; it is what they stand
on. With a library present NOTHING here changes, and with one missing and no
declaration the `#T843` failure is LOUDER than the bare assert it replaces.

numpy-free.
"""
from __future__ import annotations

import ctypes
import json

import pytest

from srmech import _native
from srmech.cascade import compose as _compose
from srmech.cascade.compose import parse_chain_spec, run_chain
from srmech.math.q import Q
from srmech.math import rational as R

from _native_gate import require_native

RA = "srmech.math.rational.rational_add"
RE = "srmech.cascade.reorient"

#: The exact wire the DoD names, byte for byte. srmech's JSON writer emits
#: canonical sorted keys with ", " / ": " separators, so this is a literal
#: comparison and not a parse-and-compare.
HEADLINE_WIRE = b'{"d": "6", "k": "q", "n": "-5"}'


# ── the native floor: fail, never skip ──────────────────────────────────────

def test_the_native_library_is_present_and_at_this_rcs_abi() -> None:
    """The floor every other test in this file stands on.

    Asserted on all four truth fields. A ``.so`` built at one ABI against a
    higher ``EXPECTED_ABI_VERSION`` sets ``HAS_NATIVE=False`` with EVERY SYMBOL
    STILL PRESENT — ``nm -D`` says yes, the import succeeds, and every native
    gate in the tree skips silently. The only way to tell is to read these four
    fields and say what they are.

    THE ORDER IS THE DESIGN. ``EXPECTED_ABI_VERSION`` is a PYTHON SOURCE
    CONSTANT, so it is checked BEFORE the gate and stays live even on the pure
    cell — a five-file version-pin sweep that missed this one is a defect no
    absent library excuses, and gating it would be the arc's own named failure
    (an instrument that cannot return otherwise). The three fields that describe
    a LOADED library come AFTER :func:`require_native`, which is the only thing
    entitled to decide whether "absent" was declared or is a broken C build.
    """
    assert _native.EXPECTED_ABI_VERSION == 25, (
        "rc452 bumps ABI 20 -> 21 for cr_op_reorient's CR_RATIONAL arm, "
        "21 -> 22 for the b/x wire kinds, and 22 -> 23 for the m/o pair; "
        "rc455 bumps 23 -> 24 for the srmech_dsl_chain_run_arena_bytes "
        "writer-reserve move. The Python constant and the srmech.h macro move "
        "in the SAME commit or HAS_NATIVE goes silently False. Got %r"
        % (_native.EXPECTED_ABI_VERSION,))
    require_native(
        "the rc452 exact-Q pipeline floor (ABI %d and a loaded library)"
        % (_native.EXPECTED_ABI_VERSION,))
    assert _native.LOAD_ERROR is None, _native.LOAD_ERROR
    assert _native.HAS_NATIVE is True, (
        "no native library loaded. This file certifies rc452's DoD across BOTH "
        "projections; without the C half it would be a green that measured one "
        "of them. Build it (docs/srmech/c) and re-run.")
    assert _native.NATIVE_ABI_VERSION == 25, (
        "the loaded .so reports ABI %r, not %d — it is stale against this "
        "source tree and every measurement below would be of the old bytes."
        % (_native.NATIVE_ABI_VERSION, _native.EXPECTED_ABI_VERSION))


def _lib():
    """The ONE choke point every C-touching test in this file goes through.

    THE GATE LIVES HERE rather than copied into fifteen test bodies, and that is
    a correctness decision, not a tidiness one. The assert below says the symbols
    are missing "from a library that loaded" — a sentence that is FALSE unless
    something has already established that a library loaded at all, which is
    exactly the shape rc450 recorded when its own ``_c_run`` was reached ungated.
    rc450 answers it with a warning comment on each call site and still shipped
    three sites without one. A choke point cannot be forgotten.
    """
    require_native("the rc452 exact-Q pipeline's C wire (srmech_chain_run)")
    lib = _compose._compose_lib("srmech_chain_run", "srmech_chain_run_arena_bytes")
    assert lib is not None, (
        "srmech_chain_run is absent from a library that loaded and reported "
        "ABI %r — that is a different failure and must not read as a skip"
        % (_native.NATIVE_ABI_VERSION,))
    return lib


def c_run(chain: dict, ctx: dict | None = None):
    """(rc, wire_bytes) from the REAL shipped srmech_chain_run."""
    lib = _lib()
    cj = json.dumps(chain, ensure_ascii=False, allow_nan=False).encode("utf-8")
    xj = json.dumps({"inputs": ctx or {}}, ensure_ascii=False,
                    allow_nan=False).encode("utf-8")
    ws_bytes = int(lib.srmech_chain_run_arena_bytes(len(cj), len(xj)))
    ws = (ctypes.c_char * ws_bytes)()
    out_cap = max(ws_bytes // 2, 16384)
    out = (ctypes.c_char * out_cap)()
    out_len = ctypes.c_size_t()
    rc = int(lib.srmech_chain_run(cj, len(cj), xj, len(xj), ws, ws_bytes,
                                  out, out_cap, ctypes.byref(out_len)))
    return rc, out.raw[:out_len.value]


def py_run(chain: dict, ctx: dict | None = None, *, pure: bool):
    """The Python value. ``pure=True`` disables native compose dispatch for the
    call, so the two projections are compared against each other and not C
    against itself — a tautology that could not fail."""
    if not pure:
        return run_chain(parse_chain_spec(chain), inputs=ctx or {})
    orig = _compose._compose_lib
    _compose._compose_lib = lambda *a, **k: None
    try:
        return run_chain(parse_chain_spec(chain), inputs=ctx or {})
    finally:
        _compose._compose_lib = orig


def chain(steps: list, returns: str = "last") -> dict:
    return {"name": "rc452_exact_q", "summary": "", "returns": returns,
            "on_error": "raise", "steps": steps}


HEADLINE = chain([
    {"class": "N", "op": RA, "args": {"a": [1, 2], "b": [1, 3]}},
    {"class": "C", "op": RE, "args": {"value": "@step[0].output",
                                      "orientation": -1}},
])


# ── 1. THE HEADLINE ─────────────────────────────────────────────────────────

def test_headline_chain_returns_exact_q_on_the_native_path() -> None:
    """``rational_add((1,2),(1,3)) -> reorient(orientation=-1)`` == Q(-5, 6)."""
    got = py_run(HEADLINE, pure=False)
    assert isinstance(got, Q), (
        "the chain returned %r (%s). A 2-tuple here is the collapse rc452 "
        "removes: it is also how a Class-K pin pair spells itself, so the "
        "exactness is not recoverable from the value alone."
        % (got, type(got).__name__))
    assert (got.numerator, got.denominator) == (-5, 6), got


def test_headline_chain_returns_the_same_exact_q_on_the_forced_pure_path() -> None:
    """The SAME value with native compose dispatch off.

    Both projections are co-equal realizations of one contract, so this is not
    a fallback check — it is the other half of the claim.
    """
    got = py_run(HEADLINE, pure=True)
    assert isinstance(got, Q), (got, type(got).__name__)
    assert (got.numerator, got.denominator) == (-5, 6), got


def test_headline_chain_c_wire_is_byte_exact() -> None:
    """The C descriptor for step 2, BYTE for byte.

    Values agreeing is not the same claim as the wire being right: a reader
    that rebuilt -5/6 from a ``t`` of two ``i`` would satisfy both value tests
    above and still have lost the type. Only the bytes say ``"k": "q"``.
    """
    rc, wire = c_run(HEADLINE)
    assert rc == 0, (
        "the headline chain DECLINED in C with rc=%d. rc452 adds the "
        "CR_RATIONAL arm to cr_op_reorient precisely so it does not; a decline "
        "here means the arm is absent or the .so is stale." % rc)
    assert wire == HEADLINE_WIRE, (wire, HEADLINE_WIRE)


def test_the_two_projections_agree_through_the_shipped_reader() -> None:
    """C's wire, rebuilt by the SHIPPED reader, equals the pure Python value —
    and equals it as a ``Q``, not merely numerically."""
    rc, wire = c_run(HEADLINE)
    assert rc == 0, rc
    desc = _compose._srmech_json.loads(wire.decode("utf-8"))
    from_c = _compose._reconstruct_value(desc)
    from_py = py_run(HEADLINE, pure=True)
    assert type(from_c) is type(from_py) is Q, (type(from_c), type(from_py))
    assert (from_c.numerator, from_c.denominator) == \
           (from_py.numerator, from_py.denominator) == (-5, 6)


# ── 2. THE FRESH-CARRIER REGRESSION ─────────────────────────────────────────

def test_a_later_step_rereads_step0_uncorrupted() -> None:
    """THE SILENT-WRONG-ANSWER PIN. Do not delete; do not fold into the above.

    step0 = 1/2 + 1/3 = 5/6
    step1 = reorient(@step[0].output, -1)      -> -5/6
    step2 = @step[0].output + 0/1              -> MUST still be 5/6

    Step outputs persist in the chain arena. An arm that negates
    ``v->num->sign`` in place answers step1 correctly and then hands step2 a
    corrupted step0: -5/6, at ``rc=0``, with a well-formed wire and a
    completely plausible value. That is what Config C's rev2 shipped against
    the real library before rev3 carved a fresh carrier. Nothing else in this
    file — and nothing in the value-parity population — can see it.
    """
    three = chain([
        {"class": "N", "op": RA, "args": {"a": [1, 2], "b": [1, 3]}},
        {"class": "C", "op": RE, "args": {"value": "@step[0].output",
                                          "orientation": -1}},
        {"class": "N", "op": RA, "args": {"a": "@step[0].output", "b": [0, 1]}},
    ])
    rc, wire = c_run(three)
    assert rc == 0, rc
    assert wire == b'{"d": "6", "k": "q", "n": "5"}', (
        "step2 re-read step0 and got %r. If the numerator is negative, the "
        "reorient arm mutated the step-0 carrier IN PLACE instead of carving a "
        "fresh one — the exact silent wrong answer rev2 shipped." % (wire,))
    got = py_run(three, pure=True)
    assert (got.numerator, got.denominator) == (5, 6), got


def test_orientation_positive_also_returns_a_fresh_carrier() -> None:
    """A pass-through must not alias the input carrier either.

    Returning ``v`` unchanged would be correct TODAY and one edit away from
    the in-place hazard above, so the +1 path carves too and this pins that the
    value survives a later re-read.
    """
    three = chain([
        {"class": "N", "op": RA, "args": {"a": [1, 2], "b": [1, 3]}},
        {"class": "C", "op": RE, "args": {"value": "@step[0].output",
                                          "orientation": 1}},
        {"class": "N", "op": RA, "args": {"a": "@step[0].output", "b": [0, 1]}},
    ])
    rc, wire = c_run(three)
    assert rc == 0, rc
    assert wire == b'{"d": "6", "k": "q", "n": "5"}', wire


# ── 3. PAST THE int64 CEILING ───────────────────────────────────────────────

def test_the_arm_negates_a_bignum_numerator_not_just_an_int64_one() -> None:
    """A numerator well past 2**64, through the real ``srmech_bigint_t``.

    Two of the three workshop prototypes of this arm were int64-only. The
    shipped arm carries whatever the rational ops built, and those are bignum
    by construction, so the ceiling is exercised rather than assumed.

    THE BIGNUM IS BUILT INSIDE THE CHAIN, NOT PASSED IN, and that is a measured
    constraint rather than a stylistic choice: an out-of-int64 JSON LITERAL in
    the descriptor is refused by srmech's own parser with ``SRMECH_ERR_LIMIT``
    (rc404, `#T1069`), so ``{"a": [10**40, 3]}`` never reaches any op. The
    first shape of this test did exactly that and read the parser's refusal as
    "the arm is int64-bounded" — a wrong diagnosis from a real red.
    ``rational_pow_uint([10, 3], 30)`` raises the operand past the ceiling on
    the C side, where the ceiling actually is.
    """
    big_num, big_den = 10 ** 30, 3 ** 30       # ~100 bits over ~48 bits
    assert big_num > (1 << 64), big_num        # the point of the test
    big_chain = chain([
        {"class": "N", "op": "srmech.math.rational.rational_pow_uint",
         "args": {"base": [10, 3], "exp": 30}},
        {"class": "C", "op": RE, "args": {"value": "@step[0].output",
                                          "orientation": -1}},
    ])
    rc, wire = c_run(big_chain)
    assert rc == 0, (
        "the bignum chain declined with rc=%d — the arm is int64-bounded "
        "somewhere it should not be" % rc)
    desc = _compose._srmech_json.loads(wire.decode("utf-8"))
    assert desc["k"] == "q", desc
    assert int(desc["n"]) == -big_num and int(desc["d"]) == big_den, desc
    got = py_run(big_chain, pure=True)
    assert (got.numerator, got.denominator) == (-big_num, big_den), got


def test_a_zero_numerator_keeps_sign_zero_under_negation() -> None:
    """``sign == 0 iff n == 0`` is the bigint invariant; -0 is not a rational.

    An arm that stamped the flipped sign unconditionally would build a carrier
    whose sign and limb count disagree, and the wire would read "-0".
    """
    zero_chain = chain([
        {"class": "N", "op": RA, "args": {"a": [0, 1], "b": [0, 1]}},
        {"class": "C", "op": RE, "args": {"value": "@step[0].output",
                                          "orientation": -1}},
    ])
    rc, wire = c_run(zero_chain)
    assert rc == 0, rc
    assert wire == b'{"d": "1", "k": "q", "n": "0"}', wire
    got = py_run(zero_chain, pure=True)
    assert (got.numerator, got.denominator) == (0, 1), got


# ── 4. THE MUTUAL DECLINE (a parity pin, and a divergence from the plan) ────

def test_reorient_declines_a_bare_int_pair_on_BOTH_projections() -> None:
    """A bare ``[num, den]`` list is REFUSED by reorient on both sides.

    ⚠️ THIS CONTRADICTS rc452's PLAN, deliberately, and the reason is measured.
    The plan asked for the ``[num, den]`` input spelling to be ACCEPTED by the
    C arm via ``cr_as_rational``. It is not, and admitting it would be a defect:

      * Python's ``reorient((5, 6), orientation=-1)`` RAISES (unary minus on a
        tuple) and ``orientation=+1`` passes the tuple through un-negated. A C
        arm answering an exact -5/6 there would answer where its co-equal peer
        raises — a value-vs-capability divergence, which is the defect class
        this rc exists to close, one level up.
      * A 2-int list is ALSO how a Class-K pin pair spells itself. Config B
        measured that ``pin_slot_at_zero(-1) = (-1, 1)`` and the rational -1/1
        emit byte-identical wires, that the collision lands on THIS op, and
        that the repair is UNDECIDABLE — one input, two correct answers. That
        measurement is why the ruling rejected the tuple spelling; re-admitting
        it inside reorient would import the ambiguity the ruling threw out.

    A capability DECLINE is a legal contract when BOTH projections decline.
    That is what is pinned here. The pair remains a legal INPUT to the ops
    whose C peers really do take it (``rational_add`` / ``_mul`` / ``_div`` /
    ``_pow_uint``, via ``cr_as_rational``) — pinned separately below.
    """
    pair_chain = chain([{"class": "C", "op": RE,
                         "args": {"value": [5, 6], "orientation": -1}}])
    rc, wire = c_run(pair_chain)
    assert rc != 0, (
        "C ANSWERED a bare int-pair reorient (wire %r). Python raises on the "
        "same input, so this is a divergence, not a capability." % (wire,))
    assert wire == b"", wire
    with pytest.raises(TypeError):
        py_run(pair_chain, pure=True)


def test_the_pair_is_still_a_legal_input_to_the_ops_that_declare_it() -> None:
    """The surviving half of ADJ-4, pinned by execution on both projections.

    ``json.dumps(Q)`` raises, so an exact ℚ can only ENTER a chain as
    ``[num, den]``. C's ``cr_as_rational`` takes the 2-int list; the widened
    Python acceptors take the tuple. rc452 closes the RETURN direction only,
    and this is the pin that keeps the INPUT direction from being "cleaned up".
    """
    rc, wire = c_run(chain([
        {"class": "N", "op": RA, "args": {"a": [1, 2], "b": [1, 3]}}]))
    assert rc == 0 and wire == b'{"d": "6", "k": "q", "n": "5"}', (rc, wire)
    assert R.rational_add((1, 2), (1, 3)) == Q(5, 6)
    assert R.rational_add(Q(1, 2), (1, 3)) == Q(5, 6)
    assert R.rational_add((1, 2), Q(1, 3)) == Q(5, 6)
    assert R.rational_add(Q(1, 2), Q(1, 3)) == Q(5, 6)


def test_json_dumps_of_a_q_still_raises_so_the_input_direction_is_open() -> None:
    """The measured reason the pair survives as an input spelling.

    Stated as an EXECUTED fact rather than a claim, because rc452's
    open-questions list is single-sourced on it and a wrong entry there would
    make the ledger row unfalsifiable.
    """
    with pytest.raises(TypeError):
        json.dumps(Q(5, 6))


# ── 5. THE CLASS-C CONTRACT IS UNCHANGED FOR EVERY OTHER CARRIER ────────────

@pytest.mark.parametrize("value,orientation,expect_wire", [
    (7, -1, b'{"k": "i", "v": "-7"}'),
    (7, 1, b'{"k": "i", "v": "7"}'),
    (7, 0, b'{"k": "i", "v": "7"}'),
])
def test_the_int_arm_is_untouched(value, orientation, expect_wire) -> None:
    """Negate iff orientation < 0 — zero and positive pass through. The new
    rational arm reproduces exactly this rule, so the int arm is the oracle for
    it and must not have moved."""
    rc, wire = c_run(chain([{"class": "C", "op": RE,
                             "args": {"value": value,
                                      "orientation": orientation}}]))
    assert rc == 0, rc
    assert wire == expect_wire, wire


@pytest.mark.parametrize("orientation,expect_num", [(-1, -5), (0, 5), (1, 5)])
def test_the_rational_arm_follows_the_same_orientation_rule(
        orientation, expect_num) -> None:
    """The rational arm's orientation rule, checked against the int arm's."""
    rc, wire = c_run(chain([
        {"class": "N", "op": RA, "args": {"a": [1, 2], "b": [1, 3]}},
        {"class": "C", "op": RE, "args": {"value": "@step[0].output",
                                          "orientation": orientation}},
    ]))
    assert rc == 0, rc
    desc = _compose._srmech_json.loads(wire.decode("utf-8"))
    assert desc["k"] == "q" and int(desc["n"]) == expect_num, desc
    got = py_run(chain([
        {"class": "N", "op": RA, "args": {"a": [1, 2], "b": [1, 3]}},
        {"class": "C", "op": RE, "args": {"value": "@step[0].output",
                                          "orientation": orientation}},
    ]), pure=True)
    assert got.numerator == expect_num and got.denominator == 6, got
