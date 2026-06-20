"""0.9.0rc7 — native Q61 transcendental dispatch is byte-exact with the pure cascade.

The Class-N transcendentals ``rational.{sin,cos,atan,exp,log,sqrt}`` return an
exact :class:`~srmech.amsc.q.Q` (F868 stay-rational). On a native install they
dispatch to the C peers ``srmech_*_q61`` (which return the int64 Q61 pieces
BEFORE the float projection); off-native they run the pure-Python Q61 cascade.
This test pins the two paths together: for the SAME input the assembled ``Q``
(its reduced ``(num, den)`` pair) must be IDENTICAL whichever path runs — so the
native accelerator is a pure provenance-preserving speedup, never a divergence.

Numpy-free by construction (no numpy import, no ``np.``); the oracle is the
package's own pure cascade, never libm/numpy (see
``[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]``).
"""

import math

import pytest

from srmech.amsc import rational as R
from srmech.amsc import _native
from srmech.amsc.q import Q


_ONE_OUT = ("sin", "cos", "atan")
_TWO_OUT = ("exp", "log", "sqrt")

# Per-op input grids that cover every C branch (octants, atan three bands, the
# exp Cody-Waite n-scale, the log sqrt2-fold, the sqrt even/odd-exponent path)
# plus the edges (±Inf, tiny, perfect squares, the domain errors).
_DOMAIN = {
    "sin": [i * 0.1 for i in range(-200, 201)]
    + [math.pi / 6, math.pi / 4, 1000.0, -1000.0, 1e-9, 0.0],
    "cos": [i * 0.1 for i in range(-200, 201)]
    + [math.pi / 6, math.pi / 4, 1000.0, -1000.0, 1e-9, 0.0],
    "atan": [i * 0.05 for i in range(-300, 301)]
    + [1e9, -1e9, float("inf"), float("-inf"), -0.5, 12345.6],
    "exp": [i * 0.2 for i in range(-250, 251)] + [0.0, 50.0, -50.0, 1e-12],
    "log": [i * 0.05 for i in range(1, 1000)] + [1.0, 2.0, 0.5, 1e6, 1e-6],
    "sqrt": [i * 0.05 for i in range(0, 1500)] + [4.0, 0.25, 1e6, 2.0, 0.0],
}


def _evaluate(op, x):
    """Run ``rational.<op>(x)``; return ('ok', (num, den)) or ('err', name)."""
    fn = getattr(R, op)
    try:
        q = fn(x)
        assert isinstance(q, Q), f"{op}({x!r}) returned {type(q).__name__}, not Q"
        return ("ok", q.as_pair())
    except Exception as exc:  # noqa: BLE001 - we compare the error TYPE across paths
        return ("err", type(exc).__name__)


@pytest.mark.parametrize("op", _ONE_OUT + _TWO_OUT)
def test_native_q61_matches_pure_byte_for_byte(op, monkeypatch):
    """Whichever path is active, force the OTHER and assert identical ``Q`` pairs.

    When native is built this is a true native-vs-pure byte-exact check; when it
    is absent both branches are the pure path and the test is a tautology that
    still proves the dispatch wiring imports + runs clean.
    """
    native_live = _native.has_native_trans_q61()

    results_active = {x: _evaluate(op, x) for x in _DOMAIN[op]}

    # Force the pure-Python Q61 path and re-evaluate the same grid.
    monkeypatch.setattr(_native, "has_native_trans_q61", lambda: False)
    results_pure = {x: _evaluate(op, x) for x in _DOMAIN[op]}

    for x in _DOMAIN[op]:
        assert results_active[x] == results_pure[x], (
            f"{op}({x!r}) diverged: active={results_active[x]} "
            f"pure={results_pure[x]} (native_live={native_live})"
        )


def test_exact_identities_hold_on_whatever_path_runs():
    """A handful of EXACT rationals the cascade must nail bit-for-bit."""
    assert R.sin(0.0) == Q(0, 1)
    assert R.cos(0.0) == Q(1, 1)
    assert R.tan(0.0) == Q(0, 1)
    assert R.atan(0.0) == Q(0, 1)
    assert R.atan2(0.0, 1.0) == Q(0, 1)
    assert R.exp(0.0) == Q(1, 1)
    assert R.log(1.0) == Q(0, 1)
    assert R.sqrt(4.0) == Q(2, 1)
    assert R.sqrt(0.25) == Q(1, 2)
    assert R.hypot(3.0, 4.0) == Q(5, 1)
    # float() of each stays within a ULP of libm (the projection is faithful).
    assert abs(float(R.cos(1.0)) - math.cos(1.0)) <= 8.9e-16
    assert abs(float(R.exp(2.0)) - math.exp(2.0)) <= 2.3e-15
    assert abs(float(R.log(7.0)) - math.log(7.0)) <= 2.2e-15
    assert abs(float(R.sqrt(2.0)) - math.sqrt(2.0)) <= 2.3e-16


def test_domain_errors_are_consistent_and_typed():
    """Non-finite / out-of-domain inputs raise (no Q for a non-rational)."""
    for bad in (float("inf"), float("-inf"), float("nan")):
        with pytest.raises(ValueError):
            R.sin(bad)
        with pytest.raises(ValueError):
            R.exp(bad)
    with pytest.raises(ValueError):
        R.log(0.0)
    with pytest.raises(ValueError):
        R.log(-1.0)
    with pytest.raises(ValueError):
        R.sqrt(-1.0)
