"""v0.7.0rc43 — the native C trig cascade (srmech_sin/cos/atan/atan2) matches
libm to machine epsilon. These are the C peers the kepler / kuramoto ops route
through so the EXECUTABLE runs the Class-N cascade, not libm (C-transpile
triality coherence). Skipped when the native library is absent (pure-Python
wheel / Pyodide)."""
import ctypes
import math

import pytest

from srmech.amsc import _native


pytestmark = pytest.mark.skipif(not _native.HAS_NATIVE, reason="native library absent")


def _bind():
    lib = _native.LIB
    out = []
    for name in ("srmech_sin", "srmech_cos", "srmech_atan"):
        fn = getattr(lib, name)
        fn.argtypes = [ctypes.c_double, ctypes.POINTER(ctypes.c_double)]
        fn.restype = ctypes.c_int
        out.append(fn)
    a2 = lib.srmech_atan2
    a2.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.POINTER(ctypes.c_double)]
    a2.restype = ctypes.c_int
    return out[0], out[1], out[2], a2


def _call1(fn, x):
    o = ctypes.c_double(0.0)
    fn(ctypes.c_double(x), ctypes.byref(o))
    return o.value


def test_native_sin_cos_atan_vs_libm():
    s, c, a, _ = _bind()
    angles = [0.0, 0.1, 0.7, 1.0, math.pi / 2, 2.5, 3.0, math.pi,
              4.5, 2 * math.pi, 10.0, 50.0, 100.0, 255.5,
              -0.3, -2.5, -7.0, -123.4]
    for x in angles:
        assert abs(_call1(s, x) - math.sin(x)) < 1e-12, f"sin({x})"
        assert abs(_call1(c, x) - math.cos(x)) < 1e-12, f"cos({x})"
        assert abs(_call1(a, x) - math.atan(x)) < 1e-12, f"atan({x})"


def test_native_atan2_quadrants_vs_libm():
    _, _, _, a2 = _bind()
    for y, x in [(1, 1), (-1, 1), (1, -1), (-1, -1), (0.5, -2),
                 (-0.5, 2), (3, 0), (-3, 0), (0, 1), (0, -1)]:
        o = ctypes.c_double(0.0)
        a2(ctypes.c_double(float(y)), ctypes.c_double(float(x)), ctypes.byref(o))
        assert abs(o.value - math.atan2(y, x)) < 1e-12, f"atan2({y},{x})"


def test_native_trig_machine_epsilon_sweep():
    """200-point deterministic sweep across [-1000, 1000] stays at machine ε."""
    s, _, _, _ = _bind()
    worst = 0.0
    for i in range(200):
        x = -1000.0 + (2000.0 * i) / 199.0
        worst = max(worst, abs(_call1(s, x) - math.sin(x)))
    assert worst < 1e-12, f"native sin sweep worst err {worst}"
