"""kepler_solve's FINITE-tolerance frontier: where does each projection stop
converging? Rows in the m_d2_slots.py format so m_d2_diff.py joins them.

Usage: python m_d2_tol_frontier.py <python-root> <out.json>
"""
import ctypes
import json
import sys

sys.path.insert(0, sys.argv[1])

import srmech
from srmech import _native as nat
from srmech.math import kepler

NATIVE = bool(nat.HAS_NATIVE and nat.LIB is not None)
print("srmech.__file__ :", srmech.__file__, "HAS_NATIVE", nat.HAS_NATIVE)
if NATIVE:
    fn = nat.LIB.srmech_rational_sqrt
    fn.argtypes = [ctypes.c_double, ctypes.POINTER(ctypes.c_double)]
    fn.restype = ctypes.c_int
    o = ctypes.c_double(0.0)
    print("AUTH rational_sqrt(NaN) ->", fn(float("nan"), ctypes.byref(o)), "lib", getattr(nat, "_LIB_PATH", None))

MS = (1.5707963267948966, 1.0, 3.0, 0.1, 100.0, 1e6)
ES = (0.0549, 0.5, 0.9)
TOLS = (1e-12, 1e-14, 1e-15, 1e-16, 1e-17, 1e-18, 1e-20, 1e-25, 1e-30, 1e-40,
        1e-60, 1e-100, 1e-200, 1e-300, 2.2250738585072014e-308, 1e-310, 5e-324)
rows = []
for M in MS:
    for e in ES:
        for tol in TOLS:
            try:
                v = {"ok": True, "value": repr(kepler.kepler_solve(M, e, tolerance=tol, max_iter=30))}
            except Exception as exc:  # noqa: BLE001
                msg = str(exc)
                v = {"ok": False, "value": "%s: %s" % (type(exc).__name__, msg.split(", best_E=")[0])}
            rows.append({"op": "kepler_solve", "slot": "M=%r e=%r" % (M, e), "arg": repr(tol), "py": v})
cell = "native" if NATIVE else "pure"
print("# cell=%s rows=%d" % (cell, len(rows)))
with open(sys.argv[2], "w", encoding="utf-8") as fh:
    json.dump({"cell": cell, "rows": rows}, fh, indent=1)
