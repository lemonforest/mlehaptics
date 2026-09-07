"""The AXIS half of the exact hypercomplex-DFT summand (rc469, `#T1188`).

rc468 made the TURN exact on every ``(n, k, m)`` and left the AXIS behind. The
two summands read ``mu_hat`` with ``_exact_mu_q`` — which answers *"what
rational vector is this"* — and then multiplied that vector into a twiddle
built at ``axis_k = 1``, which is the answer to a DIFFERENT question, *"what
unit direction, on what irrational scale"*. For a basis axis the two questions
have the same answer (``‖(0,1,0,0)‖² = 1``). For ``'ijk'`` they do not: the
resolved wire is three copies of the float64 ``0.5773502691896258``, whose
exact square sum is not ``1``, so the op returned a ``Q`` — a carrier that
ADVERTISES exact rationality — holding a value that is irrational and cannot be
a ``Q`` at all. MEASURED at ``x[1] = 2**60+1, n = 4, k = m = 1, σ = −1``::

    rc468:  carrier [Q, Q, Q, Q],  ‖out‖² − X² = +2.95e20
    rc469:  carrier [Qalg]*4,      ‖out‖² − X² =  0

and on the octonion rung, ``‖out‖² − X²`` was ``+3.57e20`` on ``'ijk'`` and
``−2.08e20`` on ``'diagonal'``. That is the silent-wrong-answer class: not an
accuracy claim missed by a tolerance, but a carrier election that was false.

**The fix reads the direction back OUT of the float wire.** ``qdft_resolve_mu``
is untouched and correct as it stands: the float normalisation loses the
MAGNITUDE but keeps the DIRECTION, and
``_exact_axis(_exact_mu_q(wire))`` recovers ``(0,1,1,1)`` at ``axis_k = 3``
from it. So no op signature moves, no ``exact=`` keyword is added, and the
result is provably the shipped ``quaternion_twiddle(..., exact=True)``.

**Why the refusals are RAISES and not a carrier election.** The alternative —
fall through to the float body when the axis has no exact unit — was executed
before it was rejected. On an EXACT sample it returns ``['Q','Q','Q','Q']``,
because ``float * Q`` is ``Q``: a ``Q`` carrier over a ROUNDED float64
twiddle. That re-mints the very class this file exists to remove, on a new axis
family, and a type-witness taken on an INT sample cannot see it. Hence
:func:`test_a_general_vector_wire_with_an_exact_sample_RAISES`, which asserts
the raise rather than the type.

**The admission rule is a SIEVE, not a ceiling.** ``n`` is admissible iff
``lcm(n, base) <= 256`` with ``base = {1: 4, 3: 12, 7: 28}[axis_k]``. That is
not an interval: ``axis_k = 3`` REFUSES ``n = 23`` (index 276) and ACCEPTS
``n = 126`` (index 252). A cap-shaped claim ("``axis_k = 3`` needs
``n <= 64``") is wrong in both directions, which is why
:func:`test_the_admission_rule_is_the_lcm_sieve_not_a_cap` checks agreement
with the RULE over every ``n`` in 1..128 rather than pinning an endpoint.
"""

from __future__ import annotations

import pytest

from srmech.cascade import (
    hypercomplex_dft as _H,
    odft_resolve_mu,
    odft_summand,
    qdft_resolve_mu,
    qdft_summand,
)
from srmech.math import qalg as _qalg
from srmech.math.cyclic import gcd
from srmech.math.q import Q
from srmech.physics.qm.octonion import octonion_twiddle
from srmech.physics.qm.quaternion import quaternion_twiddle

#: The sample that makes the defect visible. ``2**60 + 1`` is odd and above the
#: float64 integer grid, so a float route cannot represent it and a ROUNDED
#: exact route cannot hide in the low bits.
P = 2 ** 60 + 1

#: The field-index base per axis width — the whole of the sieve.
AXIS_BASE = {1: 4, 3: 12, 7: 28}


def _norm_sq(vec):
    """``Σ v²`` with no ``abs`` and no float — the ONE thing that decides
    whether an exact carrier is telling the truth about a unit twiddle."""
    acc = vec[0] * vec[0]
    for v in vec[1:]:
        acc = acc + v * v
    return acc


def _is_zero(v) -> bool:
    """``v == 0`` across BOTH exact carriers.

    A ``Qalg`` difference that is numerically zero need not have narrowed to
    ``Q`` — ``Qalg`` narrows on ELECTION, not on every arithmetic result — so
    comparing to ``Q(0, 1)`` alone would fail on a correct answer.
    """
    if isinstance(v, Q):
        return v == Q(0, 1)
    return v.is_rational() and v.as_rational() == Q(0, 1)


def _q4(x):
    return [[0, 0, 0, 0], [x, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]


def _o8(x):
    return [[0] * 8, [x] + [0] * 7, [0] * 8, [0] * 8]


# --------------------------------------------------------------------------
# (1) the regression witness: the measured wrong answer, now exact
# --------------------------------------------------------------------------

def test_the_ijk_axis_no_longer_returns_a_Q_over_an_irrational_value() -> None:
    """THE DEFECT, as a witness. rc468 answered ``[Q]*4`` with
    ``‖out‖² − X² = 2.95e20``; the true value is irrational, so no ``Q`` can
    hold it and the carrier itself was the lie.

    Fails if ``_exact_summand_axis`` is never reached, if it hands back
    ``axis_k = 1``, or if the twiddle is built in the wrong field.
    """
    out = qdft_summand(_q4(P), 1, 1, 4, True, -1, qdft_resolve_mu("ijk"))
    assert [type(v).__name__ for v in out] == ["Qalg"] * 4, (
        f"the body diagonal at n=4 is irrational in every slot; got "
        f"{[type(v).__name__ for v in out]}")
    assert _is_zero(_norm_sq(out) - Q(P * P, 1)), (
        "a unit twiddle preserves the norm EXACTLY; rc468 missed it by 2.95e20")


def test_the_rc468_carrier_was_wrong_and_not_merely_imprecise() -> None:
    """The election, stated as the assertion it deserves: the exact answer is
    NOT rational, so ``list[Q]`` was not a rounded ``Q`` — it was a category
    error. ``2·(out[1])²·3 == X²`` is the algebraic identity that pins it
    (``out[1] = −X/√3`` at this turn), and it is checked in the field.
    """
    out = qdft_summand(_q4(P), 1, 1, 4, True, -1, qdft_resolve_mu("ijk"))
    assert not out[1].is_rational(), "−X/√3 is irrational; it cannot be a Q"
    assert _is_zero(out[1] * out[1] * Q(3, 1) - Q(P * P, 1))


# --------------------------------------------------------------------------
# (2)+(3) equality with the shipped exact twiddle, on every named axis
# --------------------------------------------------------------------------

@pytest.mark.parametrize("name", ["i", "j", "k", "ijk", "diagonal"])
def test_the_summand_equals_the_shipped_exact_twiddle_times_the_sample(name) -> None:
    """The summand IS ``quaternion_twiddle(..., exact=True) ⊗ x``, on every
    axis in the resolver's vocabulary — the strongest available statement,
    because that op has 83 witnesses of its own in
    ``tests/test_exact_twiddle_rc468.py``.

    ``'diagonal'`` is the resolver's ℍ alias for ``'ijk'``; the twiddle op does
    not carry the alias, so the comparison spells it out.
    """
    twiddle_name = "ijk" if name == "diagonal" else name
    out = qdft_summand(_q4(P), 1, 1, 4, True, -1, qdft_resolve_mu(name))
    w = quaternion_twiddle(1, 1, 4, sigma=-1, mu=twiddle_name, exact=True)
    ref = _H._cd_mult_graded([Q(P, 1), Q(0, 1), Q(0, 1), Q(0, 1)],
                             list(w), left=False)
    assert list(out) == list(ref)


@pytest.mark.parametrize("name,axis_k", [("i", 1), ("ijk", 3), ("diagonal", 7)])
def test_the_odft_summand_is_exact_on_every_axis_width(name, axis_k) -> None:
    """The octonion rung, where all three widths are reachable. Pre-fix
    deficits, MEASURED at ``n = 4``: ``'i'`` 0, ``'ijk'`` ``+3.57e20``,
    ``'diagonal'`` ``−2.08e20``.
    """
    mu = odft_resolve_mu(name)
    assert _qalg._exact_axis(_H._exact_mu_q(mu))[1] == axis_k
    out = odft_summand(_o8(P), 1, 1, 4, "left", "left_associated", -1, mu, mu)
    assert _is_zero(_norm_sq(out) - Q(P * P, 1))
    w = octonion_twiddle(1, 1, 4, sigma=-1, mu=name, exact=True)
    ref = _H._cd_mult_graded([Q(P, 1)] + [Q(0, 1)] * 7, list(w), left=False)
    assert list(out) == list(ref)


# --------------------------------------------------------------------------
# (4) the regression guard: nothing on the axis_k = 1 route moves
# --------------------------------------------------------------------------

def test_the_basis_axis_route_is_byte_identical_to_rc468() -> None:
    """The rc468 pins, re-asserted against the rc469 body. ``axis_k = 1`` is
    the width the old code assumed, so if the edit disturbed anything at all
    it disturbed this — and every existing witness in
    ``tests/test_exact_twiddle_rc468.py`` lives here.
    """
    got = qdft_summand([[0, 0, 0, 0], [P, 0, 0, 0]], 1, 1, 8, True, -1,
                       [0, 1, 0, 0])
    assert [type(v).__name__ for v in got] == ["Qalg"] * 4
    assert _is_zero(got[0] * got[0] * Q(2, 1) - Q(P * P, 1))
    quarter = qdft_summand([[0, 0, 0, 0], [P, 0, 0, 0]], 1, 1, 4, True, -1,
                           [0, 1, 0, 0])
    assert quarter == [Q(0, 1), Q(-P, 1), Q(0, 1), Q(0, 1)]
    assert [type(v).__name__ for v in quarter] == ["Q"] * 4


def test_the_float_route_is_byte_for_byte_unchanged() -> None:
    """The C compose host is double-only and its divergence is pinned BY NAME
    (``_COMPOSE_HOST_FLOAT_ONLY``). That pin is only worth anything while the
    float arm is bit-identical, so these are the literals the shipped worked
    examples carry, asserted rather than commented.

    ⚠️ The third case is the one an over-broad edit breaks: a FLOAT sample on
    an ``'ijk'`` axis must still take the float route, untouched, even though
    that axis is exactly what this rc changed on the exact arm.
    """
    xs = [[1.0, 0.5, -0.25, 2.0], [0.0, 1.0, 0.0, -1.0]]
    assert qdft_summand(xs, 1, 1, 2, True, -1, qdft_resolve_mu("i")) == [
        1.222980050563649e-16, -1.0, -1.222980050563649e-16, 1.0]
    xo = [[1.0] + [0.0] * 7, [0.0, 1.0] + [0.0] * 6]
    assert odft_summand(xo, 1, 1, 2, "two_sided", "left_associated", -1,
                        odft_resolve_mu("i"), odft_resolve_mu("j")) == [
        -1.222980050563649e-16, 1.0, -1.4956802040766655e-32,
        1.222980050563649e-16, 0.0, 0.0, 0.0, 0.0]
    assert qdft_summand([[0.0] * 4, [1.0, 0.0, 0.0, 0.0]], 1, 1, 4, True, -1,
                        qdft_resolve_mu("ijk")) == [
        6.114900252818245e-17, -0.5773502691896258, -0.5773502691896258,
        -0.5773502691896258]


# --------------------------------------------------------------------------
# (5)+(6) the two refusals — asserted as RAISES, deliberately
# --------------------------------------------------------------------------

def test_a_general_vector_wire_with_an_exact_sample_RAISES() -> None:
    """THE SHARPEST CONTROL IN THIS FILE.

    ``qdft_resolve_mu([0, 3, 0, 4])`` normalises in float and lands on
    ``[0.0, 0.6000000000000001, 0.0, 0.8]`` — one ULP off ``3/5``, so the
    DIRECTION is destroyed, not just the magnitude, and ``_exact_axis``
    correctly returns ``None``. (``_exact_axis`` on the RAW ``(0,3,0,4)``
    gives ``(0, 3/5, 0, 4/5)`` at ``axis_k = 1``; recovering it here would need
    a second operand on a chain-internal wire, which is filed, not built.)

    It must RAISE, not elect the float carrier: a fallthrough was measured to
    return ``['Q','Q','Q','Q']`` over a rounded float64 twiddle, because
    ``float * Q`` is ``Q``. Asserting the raise is what makes this a control —
    a type assertion taken on an int sample passes against that defect.
    """
    wire = qdft_resolve_mu([0.0, 3.0, 0.0, 4.0])
    assert _qalg._exact_axis(_H._exact_mu_q(wire)) is None
    with pytest.raises(ValueError, match="1, 3 or 7 times a rational square"):
        qdft_summand(_q4(P), 1, 1, 4, True, -1, wire)
    # ...and the FLOAT sample on the same wire still answers, unchanged: the
    # refusal is about the exact arm's carrier claim, not about the axis.
    assert qdft_summand([[0.0] * 4, [1.0, 0.0, 0.0, 0.0]], 1, 1, 4, True, -1,
                        wire)[1] == -0.6000000000000001


def test_a_non_pure_imaginary_axis_RAISES_and_this_is_what_the_probe_MEETS() -> None:
    """The OTHER refusal, and — MEASURED — the one that actually fires in the
    demotion census.

    The probe writes its witness into leaf ``(0,)`` of every candidate shape it
    has for a ``list[float]`` parameter, and leaf ``(0,)`` is the REAL slot. A
    twiddle ``cos + sin·μ̂`` is a UNIT quaternion only for a pure-imaginary
    ``μ̂``; with a real part it is not a rotation at all, and rc468 answered
    with an exact ``Q`` over it. So of the 17 shapes the probe tries, 11 now
    refuse HERE and 6 are nested lists that never bound, which is why the three
    ``mu_hat``/``mu_r_hat`` rows read ``RAISED`` rather than ``VACUOUS``: an
    honest non-measurement in place of a false claim about the op.

    The refusal message must NAME the real slot, or the census reason and the
    operator both get told about a squared norm that was never the problem.
    """
    bad = [2 ** 53, 1, 0, 0]
    assert _qalg._exact_axis(_H._exact_mu_q(bad)) is None
    with pytest.raises(ValueError, match="PURE IMAGINARY"):
        qdft_summand(_q4(P), 1, 1, 2, True, -1, bad)
    # rc468 ANSWERED here, wearing the exact carrier over a non-unit twiddle;
    # the float arm still does, which is the fork the exact route is supposed
    # to have.
    assert isinstance(qdft_summand([[0.0] * 4, [1.0, 0.0, 0.0, 0.0]], 1, 1, 4,
                                   True, -1, [float(2 ** 53), 1.0, 0.0, 0.0])[0],
                      float)


def test_a_mixed_width_two_sided_axis_pair_RAISES_naming_the_compositum() -> None:
    """``_graded_two_sided`` applies ONE ``s`` to both factors, so two
    different irrational scales would need ``ℚ(√3, √7)`` — and ``Qalg`` is a
    SIMPLE extension with a ``_same_field`` guard, so it cannot hold one.
    Answering here would be the silent wrong answer in a new place.

    The same-width pair must still answer, or the guard is over-broad.
    """
    with pytest.raises(ValueError, match="MIXED-WIDTH"):
        odft_summand(_o8(P), 1, 1, 4, "two_sided", "left_associated", -1,
                     odft_resolve_mu("ijk"), odft_resolve_mu("i"))
    same = odft_summand(_o8(P), 1, 1, 4, "two_sided", "left_associated", -1,
                        odft_resolve_mu("ijk"), odft_resolve_mu("ijk"))
    assert [type(v).__name__ for v in same] == ["Qalg"] * 8


# --------------------------------------------------------------------------
# (7) the sieve, as a RULE
# --------------------------------------------------------------------------

@pytest.mark.parametrize("name,axis_k", [("i", 1), ("ijk", 3)])
def test_the_admission_rule_is_the_lcm_sieve_not_a_cap(name, axis_k) -> None:
    """Accept/refuse agrees with ``lcm(n, base) <= 256`` at EVERY ``n`` in
    1..128 — the rule, not an endpoint.

    Fails on any cap-shaped implementation, and fails specifically if the cap
    check was pushed down into ``_turn_scalars``, which carries no guard of its
    own (MEASURED: ``_turn_scalars(1, 65, 1, 1)`` answers happily at index
    260, so moving the check inward leaves NO guard at all).
    """
    mu = qdft_resolve_mu(name)
    base = AXIS_BASE[axis_k]
    disagreements = []
    for n in range(1, 129):
        index = base * n // gcd(n, base)
        want = index <= _qalg.MAX_CYCLOTOMIC_INDEX
        try:
            qdft_summand([[0, 0, 0, 0]] * 2, 1, 1, n, True, -1, mu)
            got = True
        except ValueError:
            got = False
        if got != want:
            disagreements.append((n, index, want, got))
    assert not disagreements, (
        f"axis_k={axis_k} admission is not the lcm sieve at {disagreements[:6]}")


def test_the_sieve_is_not_an_interval_in_either_direction() -> None:
    """The named counter-examples to the cap-shaped reading, so a future
    reader cannot re-derive "``axis_k = 3`` needs ``n <= 64``" from the
    admissible COUNT (60 of 128) without meeting the ``n`` that refute it.
    """
    ijk = qdft_resolve_mu("ijk")
    with pytest.raises(ValueError, match="SIEVE and not an interval"):
        qdft_summand([[0, 0, 0, 0]] * 2, 1, 1, 23, True, -1, ijk)  # index 276
    qdft_summand([[0, 0, 0, 0]] * 2, 1, 1, 126, True, -1, ijk)     # index 252
    assert _qalg._turn_field_index(23, 3) == 276
    assert _qalg._turn_field_index(126, 3) == 252
    # the three named refusals the docstrings quote
    assert _qalg._turn_field_index(128, 3) == 384      # 'ijk'      at n=128
    assert _qalg._turn_field_index(64, 7) == 448       # 'diagonal' at n=64
    assert _qalg._turn_field_index(65, 1) == 260       # a basis axis at n=65
    diag = odft_resolve_mu("diagonal")
    with pytest.raises(ValueError, match="1/sqrt\\(7\\)"):
        odft_summand([[0] * 8] * 2, 1, 1, 64, "left", "left_associated", -1,
                     diag, diag)


def test_the_axis_width_is_part_of_the_memo_key() -> None:
    """``_exact_turn_pair`` is ``lru_cache``d. If ``axis_k`` had been read
    from a closure or a module global instead of joining the key, the SECOND
    width at the same ``(n, r, σ)`` would silently return the FIRST width's
    field element — a wrong answer visible only in call order.
    """
    _H._exact_turn_pair.cache_clear()
    c1, s1 = _H._exact_turn_pair(3, 1, -1, 1)
    c3, s3 = _H._exact_turn_pair(3, 1, -1, 3)
    assert (c1, s1) != (c3, s3)
    # and the documented narrowing asymmetry: n=3 is IRRATIONAL at width 1 and
    # RATIONAL at width 3, because the election reads the SCALED sine.
    assert not isinstance(s1, Q)
    # MEASURED: sigma=-1 flips the sine, so the pair is (-1/2, -1/2); at
    # sigma=+1 it is (-1/2, +1/2). Both are wholly rational at width 3.
    assert (c3, s3) == (Q(-1, 2), Q(-1, 2))
    assert _H._exact_turn_pair(3, 1, 1, 3) == (Q(-1, 2), Q(1, 2))
    assert _H._exact_turn_pair(3, 1, -1, 1) == (c1, s1)


# --------------------------------------------------------------------------
# the two prose sites the fix falsified, checked as text
# --------------------------------------------------------------------------

def test_the_false_axis_k_equals_one_comment_is_gone() -> None:
    """``hypercomplex_dft.py`` used to carry, beside the twiddle construction:
    *"The axis on this route is always rational (it is a wire, not a name), so
    ``axis_k = 1``"*. It was false for ``'ijk'`` and ``'diagonal'`` — both of
    which ARRIVE as wires — and it is the sentence that made the defect look
    intentional. Deleted, not worked around.
    """
    import inspect

    src = inspect.getsource(_H)
    assert "it is a wire, not a name" not in src
    assert "the rational arm here IS exactly the quarter turns" not in src


def test_no_public_summand_docstring_still_states_the_field_as_lcm_n_4() -> None:
    """Four PUBLIC docstring sites stated the field as ``ℚ(ζ_lcm(n,4))``,
    which is true only at ``axis_k = 1``. They ship in the wheel and are
    emitted into the generated files, so a stale one is a shipped falsehood
    (`#T1188`), not a comment.
    """
    for fn in (qdft_summand, odft_summand, _H._exact_turn_pair):
        doc = fn.__doc__ or ""
        assert "lcm(n,4)" not in doc, f"{fn.__name__} still spells the field lcm(n,4)"
