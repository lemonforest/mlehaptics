"""D1 dump: srmech_winding_fold at the C SYMBOL, the dispatched public op, and
the pure `_eph_seam_fold`, over the 24 filed + 45 named angles and a fuzz.

Usage: python m_d1_dump.py <python-root> <out.json> [n-fuzz]

Refuses to run on an inauthentic native cell. Floats are dumped as float.hex
so nothing is lost in transit.
"""
import ctypes
import json
import math
import random
import struct
import sys

sys.path.insert(0, sys.argv[1])

import srmech
from srmech import _native as nat
from srmech.cascade import one as one_mod
from srmech.math import laplacian as lap

print("srmech.__file__ :", srmech.__file__)
print("_native.__file__:", nat.__file__, "HAS_NATIVE", nat.HAS_NATIVE)
native = bool(nat.HAS_NATIVE and nat.LIB is not None)
auth = None
if native:
    fn = nat.LIB.srmech_rational_sqrt
    fn.argtypes = [ctypes.c_double, ctypes.POINTER(ctypes.c_double)]
    fn.restype = ctypes.c_int
    o = ctypes.c_double(0.0)
    auth = fn(float("nan"), ctypes.byref(o))
    nat.LIB.srmech_abi_version.restype = ctypes.c_int
    nat.LIB.srmech_version.restype = ctypes.c_char_p
    print("abi", nat.LIB.srmech_abi_version(), "c version",
          nat.LIB.srmech_version().decode(), "AUTH rational_sqrt(NaN) ->", auth,
          "lib", getattr(nat, "_LIB_PATH", None))
print("python", sys.version.split()[0], "numpy imported:", "numpy" in sys.modules)

FILED = (
    1.0, 31.41592653589793, 1e3, 1e4, 1e5, 1e6, 1e7, 1e8, 1e9, 1e10, 1e11,
    1e12, 1e13, 1e14, 1e15, 2.0 ** 40, 2.0 ** 50, 2.0 ** 53, 2.0 ** 54, 1.5e16,
    3.1415926535897932e16, -1e10, -1e8, -3.1415926535897932e16,
)
EXTRA = (
    0.0, -0.0, 0.5, -1.0, 2.0, math.pi, -math.pi, 3.0, -3.0,
    2.0 * math.pi, 2.0 * math.pi * 5.0, 2.0 * math.pi * 19.0,
    2.0 * math.pi * -3.5, 1e-30, -1e-30, 5e-14, -5e-14, 1e-5, -1e-5,
    2.0 ** 55 - 1024.0, -(2.0 ** 55 - 1024.0),
)
NAMED = FILED + EXTRA
DOOR = (2.0 ** 55, -(2.0 ** 55), float("nan"), float("inf"), float("-inf"), 1e300)

if native:
    wf = nat.LIB.srmech_winding_fold
    wf.argtypes = [ctypes.c_double, ctypes.POINTER(ctypes.c_int64),
                   ctypes.POINTER(ctypes.c_double)]
    wf.restype = ctypes.c_int


def sym(theta):
    w = ctypes.c_int64(0)
    r = ctypes.c_double(0.0)
    st = wf(ctypes.c_double(theta), ctypes.byref(w), ctypes.byref(r))
    return int(st), int(w.value), float(r.value)


def row(theta, tag):
    wp, qn = lap._eph_seam_fold(theta)
    rp = qn / float(lap._EPH_FOLD_DEN)
    wd, rd = one_mod.winding_fold(theta)
    rec = {"tag": tag, "theta": float(theta).hex(), "w_pure": wp,
           "res_pure": rp.hex(), "w_disp": wd, "res_disp": rd.hex()}
    if native:
        st, wc, rc = sym(theta)
        rec.update({"st": st, "w_sym": wc, "res_sym": rc.hex()})
    return rec


rows = [row(t, "filed") for t in FILED] + [row(t, "extra") for t in EXTRA]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 0
rng = random.Random(20260913)
fam = {0: 0, 1: 0, 2: 0, 3: 0}
N_INT = lap._EPH_TWO_PI[0]
i = 0
while sum(fam.values()) < n:
    kind = i % 4
    i += 1
    if kind == 0:
        t = rng.uniform(-(2.0 ** 55), 2.0 ** 55)
    elif kind == 1:
        t = math.ldexp(rng.uniform(1.0, 2.0), rng.randint(-1074, 54))
        if rng.random() < 0.5:
            t = -t
    elif kind == 2:
        kk = rng.randint(-10 ** 15, 10 ** 15)
        t = (kk + 0.5) * (N_INT / float(1 << 80))
        t = t + rng.choice((-1, 1)) * rng.choice((0.0, 5e-324, 1e-3, 1e-9)) * (1.0 if t == t else 0.0)
        if rng.random() < 0.5:
            t = math.nextafter(t, rng.choice((math.inf, -math.inf)))
    else:
        t = struct.unpack("<d", struct.pack("<Q", rng.getrandbits(64)))[0]
    mag = t if t >= 0.0 else -t
    if t != t or not (mag < 2.0 ** 55):
        continue
    fam[kind] += 1
    rows.append(row(t, "fuzz%d" % kind))

door = []
if native:
    for t in DOOR:
        st, wc, rc = sym(t)
        door.append({"theta": repr(t), "st": st, "w": wc, "res": repr(rc)})
out = {"native": native, "auth": auth, "version": srmech.__version__,
       "python": sys.version.split()[0], "rows": rows, "door": door,
       "fuzz_families": fam}
with open(sys.argv[2], "w", encoding="utf-8") as fh:
    json.dump(out, fh)
print("rows", len(rows), "named", len(NAMED), "filed", len(FILED),
      "fuzz", sum(fam.values()), fam)
if native:
    for d in door:
        print("door", d)
