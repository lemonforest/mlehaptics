"""rc475 (`#T1188`) — the ``ti_lift_mono`` / ``lift_mono`` zero-coefficient FIXED
POINT, in both projections, plus the ``ti_parse`` validation that is its root fix.

WHAT WAS WRONG. Both projections factored a prime out of a rational coefficient
with a loop whose exit test was ``remainder != 0``. On a ZERO the loop is not
merely "unbounded" — it is a FIXED POINT:

  * C: ``srmech_bigint_divmod_small(quo, &rem, 0, p)`` returns ``SRMECH_OK`` with
    ``quo = 0`` and ``rem = 0`` for every prime ``p``, so the next iteration is
    byte-identical to the last, forever, and ``e++`` / ``e--`` run away on a
    signed ``int32_t``.
  * Python: ``0 % p == 0`` and ``0 // p == 0``, identically.

MEASURED by execution at rc474: the pure twin did not return inside 12 s on
``Q(0, 1)``, while the control ``Q(12, 5)`` at prime 2 returned ``3/5`` with
``e = +2``. The sibling ``ti_collect_mono_primes`` — same file, same call path,
same two fields — guarded exactly that state 50 lines earlier, so this was two
functions over the same data disagreeing about whether zero can arrive.

HOW REACHABLE IT WAS, stated exactly rather than as "defensive":

  * from the PUBLIC PYTHON ops: UNREACHABLE, and provably so. ``Q`` raises
    ``ZeroDivisionError`` on a zero denominator and reduces to ``den >= 1``;
    ``Theta.__init__`` raises on a zero argument; ``_struct_combine`` drops every
    zero prefactor before Z5/Z6. So a zero cannot reach ``lift_mono``.
  * from the EXPORTED C ENTRIES: REACHABLE, on an input the entry failed to
    reject. ``ti_parse`` copied ``coeff_num`` / ``coeff_den`` verbatim with no
    validation, ``ti_combine`` tests only the PREFACTOR's numerator and never
    looks at theta arguments at all, and
    ``srmech_ellbase_theta_canon_full`` unconditionally inverts the theta
    argument through a zero check that is an ``assert`` ONLY — stripped under
    ``-DNDEBUG``, which is the release build — manufacturing a ``den = 0``
    monomial from a zero numerator.

SO THE REPAIR IS TWO-LAYERED, and this file tests both layers:

  1. ``ti_parse`` REJECTS a zero denominator on any monomial and a zero numerator
     on a THETA ARGUMENT, with ``SRMECH_ERR_BAD_INPUT``. That is the root: it
     closes the only route to the state, and it makes the C entry refuse what
     the Python constructors already refuse.
  2. ``ti_lift_mono`` guards the loops anyway — SKIP on a zero numerator (``e``
     unchanged: ``v_p(0)`` is undefined and the lift's contract holds at any
     exponent), REFUSE on a zero denominator (not a rational; skipping would
     launder an invalid object onward). The Python twin carries only the
     numerator skip, because ``Q`` makes the denominator branch dead code.

⚠️ THE PURE ROW RUNS IN A SUBPROCESS. A fixed point in a Python loop cannot be
interrupted by anything this test can do in-process, so an in-process call would
hang the pytest session on precisely the defect being measured, and CI would
report a timeout rather than a failure. Numpy-free.
"""
from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest

from srmech import _native
from srmech.apokatastasis.ellbase import EllMonomial, Theta
from srmech.apokatastasis.thetasum import _lift_prime_terms
from srmech.math.q import Q

#: The repaired code answers in microseconds; rc474 did not return in 12 s.
GUARD_S = 30


def test_the_pure_lift_returns_on_a_zero_numerator():
    """The rc474 hang, in the pure projection, out of process."""
    code = textwrap.dedent("""
        from srmech.apokatastasis.ellbase import EllMonomial
        from srmech.apokatastasis.thetasum import _lift_prime_terms
        from srmech.math.q import Q
        zero = EllMonomial(Q(0, 1), {})
        out = _lift_prime_terms([(zero, [])], [(2, "Z"), (3, "W")])
        print("RETURNED", out[0][0].coeff, dict(out[0][0].exps))
    """)
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True,
                          text=True, timeout=GUARD_S)
    assert proc.returncode == 0, (
        f"the pure lift did not complete cleanly on a zero numerator: "
        f"{proc.stderr[-600:]}"
    )
    assert proc.stdout.startswith("RETURNED"), proc.stdout


def test_the_pure_lift_leaves_a_zero_coefficient_exactly_alone():
    """``e`` unchanged is the arithmetic, not a shortcut.

    ``v_p(0)`` is undefined and the lift's stated contract — substituting
    ``sym := prime`` reproduces the coefficient — holds for a zero coefficient
    at ANY exponent, so the minimal exact choice is to move nothing.
    """
    zero = EllMonomial(Q(0, 1), {"q": 3})
    out = _lift_prime_terms([(zero, [])], [(2, "Z"), (3, "W")])
    lifted = out[0][0]
    assert lifted.coeff == Q(0, 1)
    assert "Z" not in dict(lifted.exps) and "W" not in dict(lifted.exps), (
        f"a zero coefficient must carry NO lifted prime exponent; got "
        f"{dict(lifted.exps)}"
    )


def test_the_pure_lift_still_lifts_a_nonzero_coefficient():
    """⚠️ THE POSITIVE CONTROL. A guard that skipped every coefficient would
    make the test above pass and the op useless. ``Q(12, 5)`` at prime 2 must
    become ``3/5`` with the exponent at ``+2``, which is the rc474 control row
    re-measured here."""
    m = EllMonomial(Q(12, 5), {})
    out = _lift_prime_terms([(m, [])], [(2, "Z")])
    lifted = out[0][0]
    assert lifted.coeff == Q(3, 5), lifted.coeff
    assert dict(lifted.exps) == {"Z": 2}, dict(lifted.exps)
    # ...and a DENOMINATOR prime moves the exponent the other way.
    out2 = _lift_prime_terms([(EllMonomial(Q(5, 12), {}), [])], [(2, "Z")])
    assert out2[0][0].coeff == Q(5, 3), out2[0][0].coeff
    assert dict(out2[0][0].exps) == {"Z": -2}, dict(out2[0][0].exps)


def test_the_python_constructors_refuse_the_state_at_all():
    """Why the pure projection needs no denominator guard: it cannot get there.

    This is the UNREACHABILITY half of the claim, asserted rather than trusted.
    If either constructor ever stops refusing, the pure ``lift_mono`` acquires a
    live fixed point and this test is what says so.
    """
    with pytest.raises(ZeroDivisionError):
        Q(1, 0)
    with pytest.raises(ValueError):
        Theta(EllMonomial(Q(0, 1), {}))


@pytest.mark.skipif(not _native.has_native_thetasum_interpolation(),
                    reason="needs the native thetasum interpolation entry")
def test_the_C_entry_REFUSES_a_zero_denominator():
    """``ti_parse`` must reject it — out of process, because through rc474 this
    exact call reached the fixed point.

    The observable is a ``RuntimeError`` naming a non-OK status: the wrapper
    maps ``SRMECH_ERR_OVERFLOW`` to a decline (``None``) and RAISES on anything
    else, so ``BAD_INPUT`` surfaces as a raise. A decline would NOT be
    acceptable here — it would send an invalid object to the pure oracle, which
    is the same silent-fallback shape rc475 removed from the factor wrappers.
    """
    code = textwrap.dedent("""
        from srmech import _native as N
        # one term, one theta, prefactor coeff 1/0 -- not a rational
        monos = [(1, 0, [0]), (1, 1, [1])]
        try:
            r = N.thetasum_is_zero_interpolation_c(1, 0, 0, 0, [1], monos)
        except RuntimeError as exc:
            print("RAISED", exc)
        else:
            print("RETURNED", r)
    """)
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True,
                          text=True, timeout=GUARD_S)
    assert proc.returncode == 0, proc.stderr[-600:]
    assert proc.stdout.startswith("RAISED"), (
        f"a zero DENOMINATOR was not refused by the C entry: {proc.stdout!r} "
        f"{proc.stderr[-400:]}"
    )
    assert "non-OK status 2" in proc.stdout, (
        f"expected SRMECH_ERR_BAD_INPUT (2); got {proc.stdout!r}"
    )


@pytest.mark.skipif(not _native.has_native_thetasum_interpolation(),
                    reason="needs the native thetasum interpolation entry")
def test_the_C_entry_REFUSES_a_zero_theta_argument():
    """``Theta(0)`` is undefined, and it is the WORSE of the two states.

    A zero theta-argument numerator survived ``ti_combine`` (which never
    inspects theta arguments) and then met
    ``srmech_ellbase_theta_canon_full``'s unconditional ``mono_inv``, whose zero
    check is an ``assert`` — absent in the release build — which swaps num and
    den and MANUFACTURES a zero denominator. Python refuses this at
    ``Theta.__init__``; the C entry now refuses it too.
    """
    code = textwrap.dedent("""
        from srmech import _native as N
        # one term, one theta whose ARGUMENT numerator is zero
        monos = [(1, 1, [0]), (0, 1, [1])]
        try:
            r = N.thetasum_is_zero_interpolation_c(1, 0, 0, 0, [1], monos)
        except RuntimeError as exc:
            print("RAISED", exc)
        else:
            print("RETURNED", r)
    """)
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True,
                          text=True, timeout=GUARD_S)
    assert proc.returncode == 0, proc.stderr[-600:]
    assert proc.stdout.startswith("RAISED"), (
        f"a zero THETA ARGUMENT was not refused by the C entry: "
        f"{proc.stdout!r} {proc.stderr[-400:]}"
    )
    assert "non-OK status 2" in proc.stdout, proc.stdout


@pytest.mark.skipif(not _native.has_native_thetasum_interpolation(),
                    reason="needs the native thetasum interpolation entry")
def test_the_C_entry_still_ANSWERS_a_valid_input():
    """⚠️ THE POSITIVE CONTROL for the two refusals above.

    A ``ti_parse`` that rejected everything would make both of them pass while
    removing the op. A legal wire form — a nonzero prefactor, a nonzero theta
    argument, a nonzero denominator — must still produce a verdict (``True`` or
    ``False``) or a documented arena DECLINE (``None``), and must not raise.
    """
    monos = [(1, 1, [0]), (1, 1, [1])]
    got = _native.thetasum_is_zero_interpolation_c(1, 0, 0, 0, [1], monos)
    assert got is None or isinstance(got, bool), got


def test_the_C_source_carries_both_guards():
    """A source-shape pin on the two repairs, so a later edit that deletes one
    is reported here rather than by a hang.

    Scoped to its measured extent: this reads the SOURCE. It says the guards are
    written, not that they fire — the two subprocess rows above are what say
    that, and only on the cell where a native library loaded.
    """
    from pathlib import Path
    src = (Path(__file__).resolve().parent.parent.parent
           / "c" / "src" / "srmech_thetasum_interp.c").read_text(encoding="utf-8")
    start = src.index("static srmech_status_t ti_lift_mono(")
    body = src[start:src.index("static srmech_status_t ti_lift_terms(", start)]
    assert "while (!srmech_bigint_is_zero(&dst->coeff.num))" in body, (
        "ti_lift_mono's numerator loop lost its zero guard — it is a FIXED "
        "POINT without it"
    )
    assert "SRMECH_ERR_BAD_INPUT" in body, (
        "ti_lift_mono no longer REFUSES a zero denominator; skipping it would "
        "launder an invalid rational onward"
    )
    assert "for (;;)" not in body, (
        "ti_lift_mono is back to `for (;;)`, which is the form the rc475 Rule 2 "
        "census counted and the repair removed"
    )
    pstart = src.index("static srmech_status_t ti_parse(")
    pbody = src[pstart:src.index("static size_t ti_max_thetas(", pstart)]
    assert pbody.count("SRMECH_ERR_BAD_INPUT") >= 2, (
        "ti_parse lost a validation branch; it is the ROOT fix — the only "
        "route to the fixed point — not a belt"
    )
    assert "srmech_bigint_is_zero(&coeff_den[mi])" in pbody, pbody[:200]
    assert "srmech_bigint_is_zero(&coeff_num[mi])" in pbody, pbody[:200]
