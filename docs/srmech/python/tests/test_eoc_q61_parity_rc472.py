"""rc472 (`#T1188`) — ``equation_of_centre``'s Q61 refusal is CARRIER-INDEPENDENT.

THE DEFECT, measured on the rc471 tree in the native cell (WSL2, CPython
3.12.3, ``libsrmech.so`` at ABI 25, numpy absent):

    equation_of_centre(2**53 + 1, 0.0549, 4)  ->  RETURNED -0.08984990210223018

where the pure cell, on the same call, raised

    ValueError: sin: |x| too large for the Q61 octant reduction; got 3.602879701896397e+16

A silent wrong value in one projection where the other refuses — the top
defect class. The root is ``srmech_kepler.c:180``,
``(void)srmech_sin(harmonic, &sin_h);``: the C peer discards ``srmech_sin``'s
``BAD_INPUT`` status, ``srmech_sin`` writes ``x - x`` (``0.0``) into the out
slot on refusal, and the series sums on. The pure loop reaches the same
harmonic through :func:`srmech.math.rational.sin`, which refuses at
``|x| >= Q61_TRIG_RANGE`` (``2**55``); ``n_terms = 4`` times ``2**53`` is
``2**55``, so the k=4 harmonic is exactly the first one over the line.

THE REPAIR: the two refusals ``rational.sin`` makes — non-finite, then the Q61
range — are made in ``equation_of_centre`` at the Python dispatch boundary,
BEFORE ``if _native.HAS_NATIVE:``, walking the same harmonics in the same
order the pure loop walks. That is the same shape as rc466's
``laplacian.elementwise_transcendental`` guard (``rational.py`` refuses; the
Python op refuses with the identical text before the native array kernel can
return ``0.0``), and the bound is IMPORTED from ``rational``, never restated.

WHAT THIS FILE PINS, in whichever cell it runs (CI runs both):

  1. the refused text is the PURE CASCADE'S OWN, byte for byte — the oracle is
     taken LIVE by calling ``rational.sin`` on the same harmonic, and the
     literal is asserted beside it so a change to the pure text cannot pass
     unnoticed on either side;
  2. the ``float(...)`` spelling is load-bearing: the k=4 harmonic of an
     ``int`` ``M_rad`` renders ``3.602879701896397e+16`` (what
     ``rational.sin`` says after its own ``x = float(x)``), not
     ``36028797018963972``;
  3. the refusal fires BEFORE dispatch — a planted native binding that raises
     ``AssertionError`` if reached is never reached;
  4. the control still answers: ``n_terms = 1`` at the same ``M_rad`` returns
     the pinned ``-0x1.7dcca446b7ce4p-4`` (MEASURED identical in both cells).

The C follow-up is NOT here and is named in the rc472 CHANGELOG entry: twelve
unguarded ``(void)srmech_{sin,cos,atan2}`` sites remain in
``srmech_jade.c`` / ``srmech_kepler.c`` / ``srmech_kuramoto.c``; only
``srmech_laplacian.c:1747/1749`` are guarded, by the rc466 Python guard.

numpy-free. No ``abs()`` — the magnitude in the guard is a Class-K pin-slot
branch. No ``hashlib``.
"""

import pytest

from srmech.math import kepler, rational

#: ``2**53 + 1`` — the smallest positive integer float64 cannot represent.
P = 2 ** 53 + 1


def _pure_text(x) -> str:
    """The text ``rational.sin`` ITSELF raises for ``x`` — the oracle, live."""
    with pytest.raises(ValueError) as e:
        rational.sin(x)
    return str(e.value)


def test_the_refusal_is_the_pure_cascades_own_text_byte_for_byte() -> None:
    want = _pure_text(4 * P)                      # the k=4 harmonic, an int
    assert want == ("sin: |x| too large for the Q61 octant reduction; "
                    "got 3.602879701896397e+16"), (
        "the pure cascade's own refusal text moved; the guard in "
        "equation_of_centre must move WITH it, not around it")
    with pytest.raises(ValueError) as e:
        kepler.equation_of_centre(P, 0.0549, 4)
    assert str(e.value) == want, (
        f"NOT PARITY: equation_of_centre says {str(e.value)!r} where the pure "
        f"cascade says {want!r}. The int spelling of the harmonic renders "
        f"36028797018963972 here; float(...) is what rational.sin reads.")
    # a float M_rad takes the same text through the same guard
    with pytest.raises(ValueError) as e2:
        kepler.equation_of_centre(float(P), 0.0549, 4)
    assert str(e2.value) == want


def test_the_non_finite_refusal_is_the_pure_cascades_own_text_too() -> None:
    for bad in (float("nan"), float("inf"), -float("inf")):
        want = _pure_text(bad)
        assert want == "sin: x must be finite (Q is the finite-rational carrier)"
        with pytest.raises(ValueError) as e:
            kepler.equation_of_centre(bad, 0.0549, 1)
        assert str(e.value) == want, (bad, str(e.value))


def test_the_refusal_fires_before_dispatch(monkeypatch) -> None:
    """A planted native binding that must never be reached, in EITHER cell."""
    class _Lib:
        @staticmethod
        def srmech_equation_of_centre(*_a):
            raise AssertionError(
                "equation_of_centre dispatched to the C peer BEFORE refusing "
                "— the guard is on the wrong side of `if _native.HAS_NATIVE:`")

    class _Nat:
        HAS_NATIVE = True
        LIB = _Lib()
        SRMECH_OK = 0

    monkeypatch.setattr(kepler, "_native", _Nat)
    with pytest.raises(ValueError, match="too large for the Q61 octant reduction"):
        kepler.equation_of_centre(P, 0.0549, 4)
    with pytest.raises(ValueError, match="must be finite"):
        kepler.equation_of_centre(float("nan"), 0.0549, 1)


def test_the_control_still_answers_in_this_cell() -> None:
    """``n_terms = 1`` keeps every harmonic under ``2**55``: the SAME
    ``M_rad`` answers, and answers the pinned value (MEASURED identical in the
    native and the pure cell on the rc471 tree)."""
    got = kepler.equation_of_centre(P, 0.0549, 1)
    assert got.hex() == "-0x1.7dcca446b7ce4p-4", got.hex()
    # the e / n_terms refusals still come FIRST, with their own texts
    with pytest.raises(ValueError, match="e must satisfy"):
        kepler.equation_of_centre(P, 1.0, 4)
    with pytest.raises(ValueError, match="n_terms must be in"):
        kepler.equation_of_centre(P, 0.0549, 0)


def test_the_bound_is_imported_not_restated() -> None:
    """rc466's rule ("one bound, imported"; ``laplacian.py`` precedent)."""
    assert kepler._Q61_TRIG_RANGE is rational.Q61_TRIG_RANGE
    assert rational.Q61_TRIG_RANGE == 2.0 ** 55
