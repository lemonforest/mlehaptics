"""`#T1139` — the 0**0 convention `srmech.math.rational.rational_pow_uint`
ships, pinned on the PURE path.

WHY THIS FILE EXISTS SEPARATELY FROM THE NATIVE PARITY SUITE
============================================================
``tests/test_c_bignum_transcendentals_rc35.py`` carries a module-level
``pytestmark = pytest.mark.skipif(not _native.has_native_bigexp(), ...)``, so
the whole module — including the ``_POW_CASES`` rows this rc adds for the zero
base — SKIPS on a pure / Pyodide checkout and on the numpy-absent, native-absent
local gate. A ``_POW_CASES`` addition alone therefore pins the convention only
where a built ``libsrmech`` happens to be loaded, which is not where most runs
of this suite happen. This file is deliberately UNGATED: it imports nothing
native, asserts on the shipped Python surface, and runs everywhere.

WHAT IS BEING PINNED, AND WHY IT IS NOT A DERIVATION
====================================================
``rational_pow_uint`` declares ``(p/q)^n = p^n / q^n``. That formula does NOT
determine ``0**0`` — ``0^0 / 1^0`` is ``0^0``, which is the question restated,
not an answer. The shipped value ``(1, 1)`` is a **deliberate convention**,
chosen and depended upon, exactly as ``int.__pow__`` and IEEE-754 ``pow`` both
choose it. A contributor reading only the docstring formula would be entitled
to conclude the value is a bug and "fix" it to ``(0, 1)``; that is the change
this file exists to stop.

It is load-bearing, not cosmetic. Callers read ``numerator((0,1)**r)`` as an
exact ``r == 0`` indicator — a one-op membership bit with no branch. Mutating
``0**0`` to ``(0, 1)`` makes that bit identically zero: the reading cascade
still runs, still returns, and is silently and completely wrong, with no
exception anywhere. The same mutation ALSO puts the pure Python path and the C
bignum kernel into disagreement, because ``bigexp_pow`` reaches ``1`` at
``exp == 0`` incidentally (it seeds ``out = 1`` and skips the loop) and has no
special case that a "fix" here would touch.

THE THREE-TEST SHAPE
====================
This file is one of three pins landed together, and the split is the point:

* this file — the PURE path, ungated, the one every local + Pyodide run
  actually executes;
* ``_POW_CASES`` rows ``(0, 1, 0)`` / ``(0, 1, 3)`` in
  ``tests/test_c_bignum_transcendentals_rc35.py`` — Python-vs-C-bignum
  agreement, NATIVE-ONLY;
* ``test_zero_pow_convention_direct_c`` in that same file — raw ctypes into
  both C symbols, because the Python wrapper's ``if exp == 0`` early return
  sits BEFORE the C dispatch and structurally hides any C disagreement.

numpy-free by construction (the module under test is numpy-free, and per
``[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]`` its test
must be too).
"""

from __future__ import annotations

import pytest

from srmech.math.rational import rational_pow_uint


def test_zero_to_the_zero_is_one_by_convention():
    """``(0/1)**0 == (1, 1)``. NOT derived from ``(p/q)^n = p^n/q^n`` — that
    formula leaves ``0**0`` undetermined. This is a chosen convention that
    shipped callers depend on; do not "correct" it to ``(0, 1)``."""
    assert rational_pow_uint((0, 1), 0) == (1, 1)


def test_zero_to_a_positive_power_is_zero():
    """``(0/1)**3 == (0, 1)``. The discriminating peer: without it a mutant
    that returns ``(1, 1)`` for every exponent passes the test above."""
    assert rational_pow_uint((0, 1), 3) == (0, 1)


def test_nonzero_base_to_the_zero_is_one():
    """``(7/1)**0 == (1, 1)`` — the ordinary ``n**0`` case, which IS
    determined by the formula. Pairing it with the zero-base case is what
    makes the convention visible as a convention: the two agree in value and
    differ entirely in justification."""
    assert rational_pow_uint((7, 1), 0) == (1, 1)


@pytest.mark.parametrize("r", [0, 1, 2, 3, 7])
def test_zero_pow_numerator_is_an_exact_membership_bit(r):
    """The reason the convention is load-bearing, asserted as the property
    callers actually use: ``numerator((0,1)**r)`` is ``1`` exactly when
    ``r == 0`` and ``0`` otherwise — a branch-free membership bit.

    A mutation of ``0**0`` to ``(0, 1)`` collapses this to the constant ``0``:
    every caller keeps running and every answer is wrong, with nothing raised.
    """
    bit = rational_pow_uint((0, 1), r).numerator
    assert bit == (1 if r == 0 else 0)


def test_the_convention_is_not_reachable_by_the_declared_formula():
    """Guard on the REASONING, not just the value.

    ``(p/q)^n = p^n/q^n`` is the contract ``rational_pow_uint`` declares. For
    ``p == 0, n == 0`` it reduces to ``0**0 / 1**0``, i.e. to itself — so no
    amount of reading the formula yields ``1``. What the shipped op does agree
    with is Python's own integer convention, and that agreement is the actual
    justification, so it is asserted rather than left in prose.
    """
    assert 0 ** 0 == 1                      # CPython int convention
    assert rational_pow_uint((0, 1), 0) == (1, 1)
    # ...and the op is NOT merely deferring to `**` on the reduced pair: it
    # keeps its own denominator contract (positive, reduced) at the same time.
    num, den = rational_pow_uint((0, 1), 0)
    assert den > 0 and (num, den) == (1, 1)
