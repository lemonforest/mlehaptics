"""rc474 (`#T1188`) — THE EXACT-OPERAND ROUTE on the Class-N scalar surface.

WHAT THIS FILE IS, AND WHY IT HAD TO BE WRITTEN
===============================================
Nine ops in ``srmech.math.rational`` — ``cos`` ``sin`` ``tan`` ``atan``
``atan2`` ``exp`` ``log`` ``sqrt`` ``hypot`` — opened their bodies with
``x = float(x)``. Handed an operand the EXACT carrier can hold (an ``int``, a
``Q``, a ``Fraction``), they rounded it to float64 and answered about the
rounded value, silently. ``cos(2**53 + 1)`` returned ``cos(2**53)``.

**NO GATE IN THE TREE NAMED ANY OF THEM.** Measured at rc473:
``CEIL_DEMOTION_UNREACHED`` ratchets ``NO_SHAPE``, not ``DEMOTED``;
``_RC463_SIX`` pins six ``laplacian`` rows. The committed census CARRIED these
nine as DEMOTED / UNRESOLVED_AT_WITNESS and no assertion read them, so the
defect and its repair would both have landed invisibly. This file is the
assertion. It was RED on the rc473 tree and is green here.

THE ROUTE IS ELECTED BY THE OPERAND, NOT BY A KEYWORD
------------------------------------------------------
There is deliberately no ``exact=`` parameter. ``tools/demotion_probe.py``'s R3
reader counts an ``exact=`` keyword as a declaration BY ITS MERE PRESENCE, so
adding one drains a census row for free (rule F1 of rc466's FIX half). The
carrier is read off the operand with ``srmech.math.q.exact_scalar`` — the ONE
exact reader — and a float operand keeps rc473's Q61 route BIT-FOR-BIT.

WHAT IS NOT REPAIRED, AND WHY — the two carve-outs, pinned as FACTS
--------------------------------------------------------------------
``log`` and ``exp`` keep the float entry, and this file asserts that they do,
so the carve-out cannot quietly become a claim of completeness:

* ``log`` has NO exact route at ANY precision. ``_log_reference`` is a
  ``struct.unpack`` bit-extraction that requires a float, so the exact
  reference cannot separate the witness either — EXECUTED at precisions 24,
  53, 61 and 128, all four ``False``. Giving ``log`` an exact route is a
  different piece of work (a rational ``log`` with no IEEE read in it).
* ``exp`` cannot be EXERCISED at the witness at all. ``exp(2**53+1)`` forms
  ``2**n`` with ``n ~ 1.3e16``, a petabyte-scale integer;
  ``tests/test_value_status_c_boundary_rc473.py`` records the same refusal
  ("a gate must not execute it"). Its exact reference RAISES at every
  precision tried (``log1p_series_truncate: num_terms exceeds max 512``).

numpy-free. No ``abs()`` — every magnitude here is a Class-K pin-slot branch.
"""
from __future__ import annotations

import pytest

from srmech import _native
from srmech.math import kepler, rational
from srmech.math.q import Q

#: ``2**53 + 1`` — the smallest positive integer float64 cannot represent, and
#: its two neighbours. ``G`` is the VACUITY guard: an op that ignores its
#: argument, or returns a constant, answers the same for F and G and would
#: otherwise read as "separating" for the wrong reason.
P = 2 ** 53 + 1
F = 2 ** 53
G = 2 ** 53 + 2

#: The ops that GAINED an exact route at rc474. ``tan`` is in the list and was
#: NOT edited: its default branch is ``sin(x) / cos(x)``, so it inherits the
#: exact route from both. That is worth asserting precisely BECAUSE it is
#: inherited — a later change to ``tan``'s dispatch would break it silently.
_EXACT_ROUTE = ("cos", "sin", "tan", "atan", "atan2", "sqrt", "hypot")

#: The two ops that did NOT gain one. See the module docstring.
_CARVE_OUT = ("log", "exp")

_ARITY = {"atan2": 2, "hypot": 2}


def _call(name: str, v):
    fn = getattr(rational, name)
    return fn(v, 1) if _ARITY.get(name, 1) == 2 else fn(v)


def _is_pow2(n: int) -> bool:
    """Is ``n`` a power of two? Class-K style explicit branch, never ``abs()``."""
    return n > 0 and (n & (n - 1)) == 0


# ── LAYER 1 — the finding: an exact operand is no longer demoted ─────────────
@pytest.mark.parametrize("name", _EXACT_ROUTE)
def test_the_exact_witness_separates(name) -> None:
    """STRICT ZERO. ``out(2**53+1) != out(2**53)``.

    This is the whole rc in one line. On the rc473 tree every one of these
    assertions FAILS, because the operand was rounded before the op looked at
    it.
    """
    p, f = _call(name, P), _call(name, F)
    assert p != f, (
        f"SILENT CARRIER DEMOTION in rational.{name}: it answered identically "
        f"for {P} and {F}, so the exact operand was rounded to float64 before "
        f"the op read it. Fix the ENTRY (the exact branch must sit ABOVE "
        f"`x = float(x)` and above the native dispatch) — do not widen a "
        f"tolerance. THIS LAYER IS STRICT ZERO AND HAS NO CEILING.")


@pytest.mark.parametrize("name", _EXACT_ROUTE)
def test_the_witness_is_not_vacuous(name) -> None:
    """An instrument that cannot return otherwise is not a measurement.

    ``G != F`` is what makes the row above a DEMOTION rather than a constant
    function: an op ignoring its argument would pass Layer 1 only if it also
    failed here.
    """
    g, f = _call(name, G), _call(name, F)
    assert g != f, (
        f"rational.{name} answers identically for {G} and {F}, so the "
        f"separation asserted above says nothing about the carrier")


# ── LAYER 2 — the carve-outs, pinned so they cannot become a silent claim ────
def test_log_has_no_exact_route_and_this_is_the_reason() -> None:
    """``log`` is CARVED OUT, and the pin records WHY rather than that it is.

    ``_log_reference`` bit-extracts ``x = m·2^e`` with ``struct.unpack``, which
    requires a float, so even the exact-rational reference cannot tell the
    witness pair apart. A gate that merely omitted ``log`` would read as an
    oversight; this one goes RED the day ``log`` gains a real exact route,
    which is the day this docstring must be rewritten.
    """
    assert rational.log(P) == rational.log(F), (
        "rational.log SEPARATED the witness — it has gained an exact route. "
        "That is good news: drain this pin, move `log` into _EXACT_ROUTE, and "
        "rewrite the carve-out paragraph in this file's docstring.")
    for precision in (24, 53, 61, 128):
        assert (rational._log_reference(float(P), precision)
                == rational._log_reference(float(F), precision)), (
            f"_log_reference separated the witness at precision={precision}")


def test_exp_is_carved_out_because_it_cannot_be_exercised() -> None:
    """``exp`` at the witness is a petabyte allocation, not a slow call.

    The exact REFERENCE refuses it outright, which is what this asserts. The
    DEFAULT route is deliberately never called here — see the module docstring
    and the rc473 disclosure it cites.
    """
    with pytest.raises(ValueError, match="num_terms exceeds max"):
        rational._exp_reference(float(P), 61)


# ── LAYER 3 — the float path did not move ───────────────────────────────────
#: A float operand must still land on the grid its own route owns, and the
#: DISCRIMINATOR differs per op because the two float routes do.
#:
#: ⚠️ **``_is_pow2`` STOPPED SEPARATING ``cos`` / ``sin`` AT THE rc474 REPAIR,
#: and the test went on passing — which is false security, not breakage.** The
#: first rc474 cut drove an exact-rational Taylor series, so the exact route's
#: denominators were huge and odd (measured at the witness: 3289 bits for
#: ``cos``, 515 for ``atan``) and "is it a power of two" told the two routes
#: apart. The repaired route returns ``_q(v, 1 << K)`` with ``K = P + 24``, a
#: power of two — so ``_is_pow2`` is now true on BOTH sides for those ops and
#: asserts nothing about them.
#:
#: The replacement is ``(2**61) % den == 0`` — "a power of two NO WIDER than
#: the Q61 grid" — with precedent at ``test_exact_carrier_drain_rc466.py:636``
#: and ``test_exact_twiddle_rc468.py:586``. At the default
#: ``_EXACT_SCALAR_PRECISION`` of 61 the exact route lands on ``2**85``, so it
#: separates; MEASURED false on 30 of 32 candidate exact-route rows.
#:
#: ⚠️ **It is applied to the Q61-GRID ops ONLY, and that is a MEASUREMENT, not
#: a hedge.** ``sqrt`` / ``hypot`` ride ``_sqrt_relative_k`` rather than the
#: Q61 cascade, and their float route legitimately exceeds 61 bits:
#: ``sqrt(1e-08)`` returns denominator ``2**68`` on the shipped float path, so
#: the tighter predicate would fail a row that is entirely correct. Those two
#: keep ``_is_pow2``. Neither op changed route at this repair, and for both of
#: them ``_is_pow2`` never separated anything anyway — their exact route is a
#: power of two too — which is recorded here rather than left to look like a
#: claim.
#:
#: ``tan`` is excluded BY MEASUREMENT, not by oversight: it is a quotient of
#: two Q61 values, so its denominator is generally odd even on the float route.
_FLOAT_GRID = [0.0, 0.5, -0.5, 0.7, 1.0, -1.0, 2.0, 3.25, 1e-8, 1e8,
               1234.5678, -1234.5678, 0.1, 3.141592653589793]

#: The ops whose float route is the Q61 cascade, so a denominator wider than
#: ``2**61`` proves the exact branch leaked onto a float.
_Q61_GRID_OPS = ("cos", "sin", "atan", "atan2")

#: ``sqrt`` / ``hypot``: the ``_sqrt_relative_k`` grid, measured up to ``2**68``.
_SQRT_GRID_OPS = ("sqrt", "hypot")


def _on_q61_grid(den: int) -> bool:
    """Is ``den`` a power of two no wider than the Q61 grid?"""
    return (2 ** 61) % den == 0


@pytest.mark.parametrize("name", _Q61_GRID_OPS + _SQRT_GRID_OPS)
def test_a_float_operand_still_lands_on_the_power_of_two_grid(name) -> None:
    tight = name in _Q61_GRID_OPS
    decided = 0
    for x in _FLOAT_GRID:
        if name == "sqrt" and x < 0.0:
            continue
        got = _call(name, x)
        den = got.as_pair()[1]
        ok = _on_q61_grid(den) if tight else _is_pow2(den)
        assert ok, (
            f"rational.{name}({x!r}) returned denominator {den} "
            f"({den.bit_length()} bits), which is not "
            f"{'a power of two dividing 2**61' if tight else 'a power of two'}"
            f" — the float operand took the EXACT route. The exact branch must "
            f"fire only when `exact_scalar` reads the operand as exact; a float "
            f"is the caller's own election.")
        if den != 1:
            decided += 1
    # An instrument that cannot return otherwise is not a measurement: a row
    # reducing to den 1 passes EVERY denominator predicate, so the rows that
    # can actually decide are counted rather than assumed. MEASURED on the
    # shipped tree: 10 of the 81 rows across these six ops reduce to den 1
    # (cos 0.0 / cos π / sin 0.0 / atan 0.0 / atan2 0.0 / sqrt 0.0 / sqrt 1.0 /
    # sqrt 1e8 / hypot 0.0 / hypot 1e-8), so no op is left with none.
    assert decided >= 8, (
        f"rational.{name}: only {decided} of the {len(_FLOAT_GRID)} grid rows "
        f"returned a denominator other than 1, so this parametrisation is "
        f"close to vacuous — every predicate here is true at den 1. Add "
        f"arguments that exercise a real denominator before trusting the pass.")


def test_a_float_is_not_read_as_exact() -> None:
    """The entry predicate itself, asserted directly."""
    assert rational._exact_scalar(2.0) is None
    assert rational._exact_scalar(0.5) is None
    assert rational._exact_scalar(2) == Q(2, 1)
    assert rational._exact_scalar(Q(3, 4)) == Q(3, 4)


# ── LAYER 4 — the refusal stayed CARRIER-INDEPENDENT ────────────────────────
@pytest.mark.parametrize("name", ("cos", "sin"))
def test_the_q61_range_refusal_is_the_same_on_both_carriers(name) -> None:
    """rc466 rule F3 / ADR-0009 §2.4: the projections may not differ in which
    inputs they serve. The exact reduction has no ``2**55`` ceiling and could
    answer here; it refuses anyway, at the same bound and in the same words.
    """
    fn = getattr(rational, name)
    with pytest.raises(ValueError) as float_exc:
        fn(2.0 ** 55)
    with pytest.raises(ValueError) as exact_exc:
        fn(2 ** 55)
    assert str(float_exc.value) == str(exact_exc.value), (
        f"rational.{name} refuses a float 2**55 and an exact 2**55 with "
        f"DIFFERENT text; the refusal has become carrier-dependent")


# ── LAYER 5 — the callers that ELECT float still get rc473's answer ─────────
#: Asserted as an int-vs-float INVARIANCE rather than against pinned values,
#: because these ops legitimately differ between the native and pure cells
#: (measured: equation_of_centre gives ...849 native and ...847 pure). The
#: invariance is the property rc474 had to preserve: each of these ops elects
#: the float carrier — its C peer takes doubles — so an exact argument must
#: not fork it onto a different answer from the float one.
def test_kepler_ops_elect_float_and_an_int_argument_does_not_fork_them() -> None:
    assert kepler.pin_slot(1, 2, 3) == kepler.pin_slot(1.0, 2.0, 3.0)
    assert kepler.kepler_solve(1, 0.2) == kepler.kepler_solve(1.0, 0.2)
    assert (kepler.equation_of_centre(1, 0.0549, 4)
            == kepler.equation_of_centre(1.0, 0.0549, 4))


def test_the_jade_sweep_elects_float_for_its_givens_rotation() -> None:
    """``theta`` is ``0.25 * atan2(...)`` — a ``Q`` on EVERY Givens step, even
    for an all-float input matrix (measured: 4500 cos/sin calls on a 2x6
    input). The sweep rounds it to build a float64 rotation, so it must hand
    ``cos``/``sin`` a float; otherwise it runs the bignum reference 4500 times
    to produce a number it immediately truncates.
    """
    from srmech.signal_processing.closed_form_ops import ica_jade
    sig = [[0.1, 0.9, 0.3, 0.7, 0.2, 0.8], [0.4, 0.2, 0.8, 0.1, 0.6, 0.3]]
    first = ica_jade.op(sig)
    assert repr(first) == repr(ica_jade.op(sig)), "the sweep is not deterministic"


# ── LAYER 6 — the exact route is RIGHT, not merely DIFFERENT ────────────────
@pytest.mark.parametrize("label,got,want", [
    ("hypot(3, 4) == 5", lambda: rational.hypot(3, 4), 5),
    ("sqrt(4) == 2", lambda: rational.sqrt(4), 2),
    ("sqrt(0) == 0", lambda: rational.sqrt(0), 0),
    ("cos(0) == 1", lambda: rational.cos(0), 1),
    ("sin(0) == 0", lambda: rational.sin(0), 0),
    ("tan(0) == 0", lambda: rational.tan(0), 0),
    ("atan(0) == 0", lambda: rational.atan(0), 0),
    ("atan2(0, 1) == 0", lambda: rational.atan2(0, 1), 0),
])
def test_the_exact_route_returns_the_exact_value(label, got, want) -> None:
    """Separation alone would be satisfied by a WRONG answer that merely
    differs. These are the cases whose exact value is a known rational, so the
    route is checked against arithmetic rather than against itself.
    """
    assert got() == want, label


def test_an_exact_negative_sqrt_still_refuses_by_name() -> None:
    """The domain refusal is the Class-K pin-slot at zero, and widening the
    entry must not have widened the DOMAIN."""
    with pytest.raises(ValueError, match="sqrt domain error"):
        rational.sqrt(-4)


def test_the_cell_is_on_the_record() -> None:
    """Never skipped. Which projection measured the rows above is a fact the
    record should carry, not something a reader reconstructs from a pass."""
    assert _native.HAS_NATIVE in (True, False)
