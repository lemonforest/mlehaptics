"""v0.7.0rc46 — the native C exp/log cascade (srmech_exp / srmech_log) matches
libm to machine epsilon. These are the C peers the laplacian elementwise
transcendental op routes through so the EXECUTABLE runs the Class-N cascade
(Q61 integer exp Taylor / integer atanh series), not libm — the rc42->rc46
C-transpile closeout that drives the C-libm ratchet to ZERO. Skipped when the
native library is absent (pure-Python wheel / Pyodide)."""
import ctypes
import math

import pytest

from srmech.amsc import _native


pytestmark = pytest.mark.skipif(not _native.HAS_NATIVE, reason="native library absent")


def _bind():
    lib = _native.LIB
    out = []
    for name in ("srmech_exp", "srmech_log"):
        fn = getattr(lib, name)
        fn.argtypes = [ctypes.c_double, ctypes.POINTER(ctypes.c_double)]
        fn.restype = ctypes.c_int
        out.append(fn)
    return out[0], out[1]


def _call1(fn, x):
    o = ctypes.c_double(0.0)
    fn(ctypes.c_double(x), ctypes.byref(o))
    return o.value


def test_native_exp_vs_libm():
    cexp, _ = _bind()
    for x in [0.0, 1.0, -1.0, 0.5, -0.5, 2.3, -2.3, 7.0, -7.0,
              13.5, -13.5, 100.0, -100.0, 500.0, -500.0, 700.0, -700.0]:
        rel = abs(_call1(cexp, x) - math.exp(x)) / math.exp(x)
        assert rel < 1e-13, f"exp({x}) rel {rel}"
    assert _call1(cexp, 0.0) == 1.0
    assert _call1(cexp, 710.0) == math.inf       # overflow -> +Inf
    assert _call1(cexp, -746.0) == 0.0           # underflow -> 0


def test_native_log_vs_libm():
    _, clog = _bind()
    for x in [1.0, 2.0, 0.5, math.e, 10.0, 1e3, 1e-3, 1e8, 1e-8,
              123456.789, 0.000123, 7.0, 1e-300, 1e300]:
        # log abs error is machine-eps; rel only loosens on the |log|~690 tail.
        assert abs(_call1(clog, x) - math.log(x)) < 1e-12, f"log({x})"
    assert _call1(clog, 1.0) == 0.0
    # log of a non-positive x -> domain error (BAD_INPUT); out is NaN / -Inf.
    o = ctypes.c_double(0.0)
    st = _native.LIB.srmech_log(ctypes.c_double(-1.0), ctypes.byref(o))
    assert st == _native.SRMECH_ERR_BAD_INPUT
    assert math.isnan(o.value)


def test_native_explog_roundtrip_and_sweep():
    """exp(log(x)) round-trips to machine eps; 200-point exp sweep stays tight."""
    cexp, clog = _bind()
    for x in [1e-6, 1e-2, 0.3, 1.0, 7.5, 1e3, 1e6]:
        rt = _call1(cexp, _call1(clog, x))
        assert abs(rt - x) / x < 1e-13, f"exp(log({x})) rt {rt}"
    worst = 0.0
    for i in range(200):
        x = -700.0 + (1400.0 * i) / 199.0
        worst = max(worst, abs(_call1(cexp, x) - math.exp(x)) / math.exp(x))
    assert worst < 1e-13, f"native exp sweep worst rel {worst}"
