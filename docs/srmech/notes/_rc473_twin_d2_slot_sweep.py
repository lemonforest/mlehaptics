"""D2 slot sweep: kepler.pin_slot / kepler.kepler_solve, one slot varied at a
time off a known-good baseline, through the PUBLIC op on this cell and (native)
the raw C symbol. Extends the crashed pass's d2_slots.py with subnormal and
+/-5e-324 scalars in every float slot and max_iter at the uint32 wire edge.

Usage: python m_d2_slots.py <python-root> <out.json>
"""
import ctypes
import json
import sys

sys.path.insert(0, sys.argv[1])

import srmech
from srmech import _native as nat
from srmech.math import kepler

NATIVE = bool(nat.HAS_NATIVE and nat.LIB is not None)
print("srmech.__file__ :", srmech.__file__)
print("_native.__file__:", nat.__file__, "HAS_NATIVE", nat.HAS_NATIVE)
AUTH = ABI = None
if NATIVE:
    fn = nat.LIB.srmech_rational_sqrt
    fn.argtypes = [ctypes.c_double, ctypes.POINTER(ctypes.c_double)]
    fn.restype = ctypes.c_int
    o = ctypes.c_double(0.0)
    AUTH = fn(float("nan"), ctypes.byref(o))
    nat.LIB.srmech_abi_version.restype = ctypes.c_int
    ABI = nat.LIB.srmech_abi_version()
    print("abi", ABI, "AUTH rational_sqrt(NaN) ->", AUTH, "lib", getattr(nat, "_LIB_PATH", None))

NAN = float("nan")
INF = float("inf")
PIN_BASE = dict(theta=0.0, pin_offset=1.0, pin_distance=1.0)
KEP_BASE = dict(M_rad=1.5707963267948966, e=0.0549, tolerance=1e-12, max_iter=20)
SCALARS = [("nan", NAN), ("+inf", INF), ("-inf", -INF),
           ("2**55", 2.0 ** 55), ("-2**55", -2.0 ** 55),
           ("2**53+1", float(2 ** 53 + 1)), ("0.0", 0.0), ("-0.0", -0.0),
           ("-1.0", -1.0), ("1e300", 1e300),
           ("5e-324", 5e-324), ("-5e-324", -5e-324),
           ("1e-310", 1e-310), ("-1e-310", -1e-310),
           ("2.2250738585072014e-308", 2.2250738585072014e-308)]
MAX_ITERS = [("0", 0), ("1", 1), ("2", 2), ("-1", -1),
             ("2**32-1", 2 ** 32 - 1), ("2**32", 2 ** 32),
             ("2**32+1", 2 ** 32 + 1), ("2**32+20", 2 ** 32 + 20),
             ("2**64+20", 2 ** 64 + 20)]


def call(f, **kw):
    try:
        return {"ok": True, "value": repr(f(**kw))}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "value": "%s: %s" % (type(exc).__name__, str(exc))}


def c_pin(theta, pin_offset, pin_distance):
    out = ctypes.c_double(0.0)
    st = nat.LIB.srmech_pin_slot(ctypes.c_double(theta), ctypes.c_double(pin_offset),
                                 ctypes.c_double(pin_distance), ctypes.byref(out))
    return {"status": int(st), "out": repr(out.value)}


#: SRMECH_SWEEP_SKIP_ZERO_WIRE=1 skips the RAW-SYMBOL call when the uint32 wire
#: value is 0 and e != 0. srmech_kepler_solve asserts `max_iter > 0 || e == 0.0`
#: on entry, so in an asserts-live (Debug) build that call aborts the process
#: rather than returning SRMECH_ERR_BAD_INPUT. The public op never sends 0 (it
#: refuses max_iter <= 0 and > 2**32 - 1 before dispatch), so only the raw-symbol
#: column of those rows is affected; the public-op column is still measured.
import os
SKIP_ZERO_WIRE = os.environ.get("SRMECH_SWEEP_SKIP_ZERO_WIRE") == "1"


def c_kep(M_rad, e, tolerance, max_iter):
    out = ctypes.c_double(0.0)
    try:
        wire = ctypes.c_uint32(max_iter)
    except Exception as exc:  # noqa: BLE001
        return {"status": None, "out": "ctypes: %s" % exc}
    if SKIP_ZERO_WIRE and wire.value == 0 and e != 0.0:
        return {"status": None, "out": "skipped: wire max_iter 0 asserts in a Debug build",
                "wire_max_iter": 0}
    st = nat.LIB.srmech_kepler_solve(ctypes.c_double(M_rad), ctypes.c_double(e),
                                     ctypes.c_double(tolerance), wire, ctypes.byref(out))
    return {"status": int(st), "out": repr(out.value), "wire_max_iter": wire.value}


rows = []
for slot in ("theta", "pin_offset", "pin_distance"):
    for label, val in SCALARS:
        kw = dict(PIN_BASE); kw[slot] = val
        r = {"op": "pin_slot", "slot": slot, "arg": label, "py": call(kepler.pin_slot, **kw)}
        if NATIVE:
            r["c"] = c_pin(kw["theta"], kw["pin_offset"], kw["pin_distance"])
        rows.append(r)
for slot in ("M_rad", "e", "tolerance"):
    for label, val in SCALARS:
        kw = dict(KEP_BASE); kw[slot] = val
        r = {"op": "kepler_solve", "slot": slot, "arg": label, "py": call(kepler.kepler_solve, **kw)}
        if NATIVE:
            r["c"] = c_kep(kw["M_rad"], kw["e"], kw["tolerance"], kw["max_iter"])
        rows.append(r)
for label, val in MAX_ITERS:
    kw = dict(KEP_BASE); kw["max_iter"] = val
    r = {"op": "kepler_solve", "slot": "max_iter", "arg": label, "py": call(kepler.kepler_solve, **kw)}
    if NATIVE:
        r["c"] = c_kep(kw["M_rad"], kw["e"], kw["tolerance"], val)
    rows.append(r)
# the e == 0 shortcut with each non-finite tolerance, and max_iter edge at e == 0
for label, val in SCALARS[:3]:
    kw = dict(KEP_BASE); kw["e"] = 0.0; kw["tolerance"] = val
    r = {"op": "kepler_solve", "slot": "tolerance@e=0", "arg": label, "py": call(kepler.kepler_solve, **kw)}
    if NATIVE:
        r["c"] = c_kep(kw["M_rad"], 0.0, val, kw["max_iter"])
    rows.append(r)
for label, val in SCALARS[:3]:
    kw = dict(KEP_BASE); kw["e"] = 0.0; kw["M_rad"] = val
    r = {"op": "kepler_solve", "slot": "M_rad@e=0", "arg": label, "py": call(kepler.kepler_solve, **kw)}
    if NATIVE:
        r["c"] = c_kep(val, 0.0, kw["tolerance"], kw["max_iter"])
    rows.append(r)
for label, val in (("2**32", 2 ** 32), ("2**32+1", 2 ** 32 + 1)):
    kw = dict(KEP_BASE); kw["e"] = 0.0; kw["max_iter"] = val
    r = {"op": "kepler_solve", "slot": "max_iter@e=0", "arg": label, "py": call(kepler.kepler_solve, **kw)}
    if NATIVE:
        r["c"] = c_kep(kw["M_rad"], 0.0, kw["tolerance"], val)
    rows.append(r)

cell = "native" if NATIVE else "pure"
print("# cell=%s version=%s abi=%s python=%s rows=%d" % (cell, srmech.__version__, ABI, sys.version.split()[0], len(rows)))
for r in rows:
    line = "%-12s %-14s %-24s py=%s %-60s" % (r["op"], r["slot"], r["arg"], "S" if r["py"]["ok"] else "R", r["py"]["value"][:60])
    if "c" in r:
        line += " | C st=%s out=%s" % (r["c"]["status"], r["c"]["out"][:24])
    print(line)
with open(sys.argv[2], "w", encoding="utf-8") as fh:
    json.dump({"cell": cell, "abi": ABI, "auth": AUTH, "rows": rows}, fh, indent=1)
