"""rc474 (`#T1188`) P3 — the VERIFICATION of the exact-operand route.

Four questions, each executed in whichever cell this process is:

  1. does the witness SEPARATE now (P != F, and G != F so it is not a flat
     function) for every op that gained an exact route, and does it still fail
     to separate for the two CARVE-OUTS (``log``, ``exp``)?
  2. is the FLOAT path bit-identical to rc473? Compared against the digest P2
     recorded for THIS cell, over the same grid in the same format — the
     bit-identity claim is proven, not assumed.
  3. do the REGRESSION-SURFACE callers still return the rc473 value, and how
     much does the ica_jade sweep now cost (it makes 4500 cos/sin calls)?
  4. what SHAPE does an exact operand get back — the denominator matters,
     because the float route always returns ``Q(v, 2**61)`` and the exact
     route does not.

Read-only. NDJSON on stdout.
"""
from __future__ import annotations

import json
import time


def emit(**rec):
    print(json.dumps(rec, sort_keys=True), flush=True)


import srmech
from srmech import _native as NB
import srmech.math.rational as R
import srmech.math.kepler as K

CELL = "native" if getattr(NB, "HAS_NATIVE", False) else "pure"
emit(rec="banner", version=srmech.__version__, cell=CELL,
     HAS_NATIVE=getattr(NB, "HAS_NATIVE", None),
     EXPECTED_ABI=getattr(NB, "EXPECTED_ABI_VERSION", None),
     NATIVE_ABI=getattr(NB, "NATIVE_ABI_VERSION", None),
     trans_q61=NB.has_native_trans_q61(), f_rational=R.__file__,
     exact_precision=R._EXACT_SCALAR_PRECISION)

P = 2 ** 53 + 1
F = 2 ** 53
G = 2 ** 53 + 2

OPS = {
    "cos": (R.cos, 1), "sin": (R.sin, 1), "tan": (R.tan, 1),
    "atan": (R.atan, 1), "sqrt": (R.sqrt, 1),
    "atan2": (R.atan2, 2), "hypot": (R.hypot, 2),
    "log": (R.log, 1),                      # CARVE-OUT: must NOT separate
}

for name, (fn, arity) in OPS.items():
    def call(v, fn=fn, arity=arity):
        return fn(v, 1) if arity == 2 else fn(v)
    try:
        a, b, c = call(P), call(F), call(G)
        emit(rec="witness", op=name, separates=(a != b), vacuity_g_ne_f=(c != b),
             p_den_bits=a.as_pair()[1].bit_length(),
             p=str(a)[:60], f=str(b)[:60])
    except Exception as e:                           # noqa: BLE001
        emit(rec="witness", op=name, error=f"{type(e).__name__}: {e}")

# exp is the second CARVE-OUT and must not be EXECUTED at the witness
try:
    R.exp(P)
    emit(rec="carveout", op="exp", note="UNEXPECTEDLY RETURNED")
except Exception as e:                               # noqa: BLE001
    emit(rec="carveout", op="exp", raised=f"{type(e).__name__}",
         msg=str(e)[:120])

# the refusal must stay CARRIER-INDEPENDENT: |x| >= 2**55 refused on BOTH
for label, v in (("float", 2.0 ** 55), ("exact int", 2 ** 55)):
    for opname in ("cos", "sin"):
        try:
            getattr(R, opname)(v)
            emit(rec="refusal", op=opname, operand=label, refused=False)
        except ValueError as e:
            emit(rec="refusal", op=opname, operand=label, refused=True,
                 msg=str(e)[:90])

# ── 2. the FLOAT path, bit-identical? same grid, same format as P1/P2 ───────
from srmech.amsc.format import sha256_bytes

GRID = [0.0, 0.5, -0.5, 0.7, 1.0, -1.0, 2.0, 3.25, 1e-8, 1e8, 1234.5678,
        -1234.5678, 0.1, 3.141592653589793, 1e-300, 1e300]
lines = []
for name in ("cos", "sin", "tan", "atan", "exp", "log", "sqrt"):
    fn = getattr(R, name)
    for x in GRID:
        try:
            lines.append(f"{name}({x!r})={fn(x).as_pair()!r}")
        except Exception as e:                       # noqa: BLE001
            lines.append(f"{name}({x!r})=RAISED {type(e).__name__}")
for a2 in GRID:
    for b2 in (0.2, -3.0, 1.0):
        for name in ("atan2", "hypot"):
            fn = getattr(R, name)
            try:
                lines.append(f"{name}({a2!r},{b2!r})={fn(a2, b2).as_pair()!r}")
            except Exception as e:                   # noqa: BLE001
                lines.append(f"{name}({a2!r},{b2!r})=RAISED {type(e).__name__}")
body = "\n".join(lines).encode()
BASELINE = {"native": "438181738d19f9cc5a4f8c121c4743a2d7364bd21a45fa12fc6ae3d4dfcf385f",
            "pure": "0c4f3cabb36f44891c0bb0ac4d19c2fbcbaf7d311aa8fdb158123d4dcfbb5ad7"}
got = sha256_bytes(body)
emit(rec="float_baseline", n=len(lines), sha256=got,
     rc473=BASELINE[CELL], bit_identical=(got == BASELINE[CELL]))

# ── 3. the regression surface ───────────────────────────────────────────────
RC473 = {
    "pin_slot(0.7,0.2,1.0)": {"native": 0.11128768723421471,
                              "pure": 0.11128768723421471},
    "pin_slot(1,2,3)": {"native": 0.3911711928586753,
                        "pure": 0.3911711928586753},
    "kepler_solve(1,0.2)": {"native": 1.1853242038613385,
                            "pure": 1.1853242038613385},
    "equation_of_centre(1,0.0549,4)": {"native": 0.09583722418961849,
                                       "pure": 0.09583722418961847},
}
for lbl, thunk in (
    ("pin_slot(0.7,0.2,1.0)", lambda: K.pin_slot(0.7, 0.2, 1.0)),
    ("pin_slot(1,2,3)", lambda: K.pin_slot(1, 2, 3)),
    ("kepler_solve(1,0.2)", lambda: K.kepler_solve(1, 0.2)),
    ("equation_of_centre(1,0.0549,4)",
     lambda: K.equation_of_centre(1, 0.0549, 4)),
):
    try:
        v = thunk()
        want = RC473[lbl][CELL]
        emit(rec="caller", site=lbl, value=repr(v), rc473=repr(want),
             unchanged=(v == want))
    except Exception as e:                           # noqa: BLE001
        emit(rec="caller", site=lbl, error=f"{type(e).__name__}: {e}")

try:
    from srmech.signal_processing.closed_form_ops import ica_jade as IJ
    sig = [[0.1, 0.9, 0.3, 0.7, 0.2, 0.8], [0.4, 0.2, 0.8, 0.1, 0.6, 0.3]]
    t0 = time.perf_counter()
    res = IJ.op(sig)
    dt = time.perf_counter() - t0
    emit(rec="caller", site="ica_jade.op", seconds=round(dt, 4),
         digest=sha256_bytes(repr(res).encode())[:16])
except Exception as e:                               # noqa: BLE001
    emit(rec="caller", site="ica_jade.op", error=f"{type(e).__name__}: {e}")

# ── 4. cost of the exact route, as a caller actually pays it ───────────────
def bench(fn, n):
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    return (time.perf_counter() - t0) / n


for name, fast, exact in (
    ("cos", lambda: R.cos(0.7), lambda: R.cos(1)),
    ("sin", lambda: R.sin(0.7), lambda: R.sin(1)),
    ("atan", lambda: R.atan(0.7), lambda: R.atan(1)),
    ("atan2", lambda: R.atan2(0.7, 0.2), lambda: R.atan2(1, 2)),
    ("sqrt", lambda: R.sqrt(2.0), lambda: R.sqrt(2)),
    ("hypot", lambda: R.hypot(3.0, 4.0), lambda: R.hypot(3, 4)),
):
    try:
        emit(rec="cost", op=name, float_s=round(bench(fast, 200), 9),
             exact_s=round(bench(exact, 100), 9),
             ratio=round(bench(exact, 50) / bench(fast, 200), 2))
    except Exception as e:                           # noqa: BLE001
        emit(rec="cost", op=name, error=f"{type(e).__name__}: {e}")

# a few exact answers a reader can check by eye
for lbl, got2, want in (
    ("hypot(3,4) == 5", R.hypot(3, 4), 5),
    ("sqrt(4) == 2", R.sqrt(4), 2),
    ("cos(0) == 1", R.cos(0), 1),
    ("sin(0) == 0", R.sin(0), 0),
    ("atan(0) == 0", R.atan(0), 0),
    ("atan2(0,1) == 0", R.atan2(0, 1), 0),
):
    emit(rec="exact_value", case=lbl, got=str(got2)[:40], equals=(got2 == want))
