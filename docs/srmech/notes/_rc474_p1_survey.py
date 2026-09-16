"""rc474 (`#T1188`) P1 — the SURVEY that precedes the repair.

Read-only. Establishes, by execution rather than by reading:

  1. the banner (version / HAS_NATIVE / ABI / the __file__ of every module
     measured), per the stale-artifact discipline;
  2. which of the nine Class-N scalar ops actually DEMOTE at the census
     witness, and by which line;
  3. whether an EXACT route can separate the witness for each op — including
     the two carve-out candidates, ``log`` (bit-extraction, no exact route at
     any precision) and ``exp`` (reference RAISES at witness scale);
  4. the COST of the reference route against the Q61 route, per op;
  5. what actually ARRIVES at the regression surface (kepler / ica_jade);
  6. a float-path BASELINE digest, so bit-identity can be proven and not
     assumed after the change.

Output: NDJSON on stdout, one record per line.
"""
from __future__ import annotations

import json
import sys
import time


def emit(**rec):
    print(json.dumps(rec, sort_keys=True), flush=True)


import srmech
try:
    import srmech.amsc._native as NA
except Exception:                                    # noqa: BLE001
    NA = None
from srmech import _native as NB
import srmech.math.rational as R
import srmech.math.kepler as K
from srmech.math.q import Q, exact_scalar

emit(rec="banner",
     version=srmech.__version__,
     amsc_native_HAS_NATIVE=getattr(NA, "HAS_NATIVE", None),
     shim_HAS_NATIVE=getattr(NB, "HAS_NATIVE", None),
     EXPECTED_ABI=getattr(NB, "EXPECTED_ABI_VERSION", None),
     NATIVE_ABI=getattr(NB, "NATIVE_ABI_VERSION", None),
     LOAD_ERROR=str(getattr(NB, "LOAD_ERROR", None)),
     trans_q61=NB.has_native_trans_q61(),
     f_srmech=srmech.__file__, f_native=NB.__file__,
     f_rational=R.__file__, f_kepler=K.__file__)

P = 2 ** 53 + 1
F = 2 ** 53
G = 2 ** 53 + 2

# ── 2/3. demotion at the witness, and whether an exact route separates ───────
OPS = {
    "cos": (R.cos, 1), "sin": (R.sin, 1), "tan": (R.tan, 1),
    "atan": (R.atan, 1), "exp": (R.exp, 1), "log": (R.log, 1),
    "sqrt": (R.sqrt, 1), "atan2": (R.atan2, 2), "hypot": (R.hypot, 2),
}

for name, (fn, arity) in OPS.items():
    def call(v, fn=fn, arity=arity, **kw):
        return fn(v, 1, **kw) if arity == 2 else fn(v, **kw)
    out = {}
    if name == "exp":
        # NOT EXERCISED, deliberately. exp(2**53+1) forms 2**n with n ~ 1.3e16,
        # i.e. a petabyte-scale integer: tests/test_value_status_c_boundary_rc473
        # records the same refusal ("a gate must not execute it"). The committed
        # census already carries this row as RAISED / MemoryError.
        out = {k: "NOT_EXERCISED (petabyte allocation; see rc473 disclosure)"
               for k in ("P", "F", "G")}
        demoted = None
    else:
        for lbl, v in (("P", P), ("F", F), ("G", G)):
            try:
                out[lbl] = repr(call(v))
            except Exception as e:                   # noqa: BLE001
                out[lbl] = f"RAISED {type(e).__name__}: {e}"
        demoted = (out["P"] == out["F"]) and (out["G"] != out["F"])
    # the precision= reference route, at the Q61-matching grid
    ref = {}
    for lbl, v in (("P", P), ("F", F)):
        try:
            ref[lbl] = repr(call(v, precision=61))
        except Exception as e:                       # noqa: BLE001
            ref[lbl] = f"RAISED {type(e).__name__}: {e}"
    emit(rec="witness", op=name, default_demotes=demoted,
         default=out, ref61=ref,
         ref_separates=(ref.get("P") != ref.get("F")
                        and not ref.get("P", "").startswith("RAISED")),
         exact_scalar_of_witness=repr(exact_scalar(P)))

# log's own reference, directly — the carve-out claim
try:
    a = R._log_reference(float(P), 61)
    b = R._log_reference(float(F), 61)
    emit(rec="log_carveout", separates=(a != b), a=repr(a), b=repr(b),
         note="_log_reference takes a float and bit-extracts it")
except Exception as e:                               # noqa: BLE001
    emit(rec="log_carveout", error=f"{type(e).__name__}: {e}")

for pp in (24, 53, 61, 128):
    try:
        a = R._log_reference(float(P), pp)
        b = R._log_reference(float(F), pp)
        emit(rec="log_precision_sweep", precision=pp, separates=(a != b))
    except Exception as e:                           # noqa: BLE001
        emit(rec="log_precision_sweep", precision=pp,
             error=f"{type(e).__name__}: {e}")

for pp in (24, 53, 61, 128):
    try:
        R._exp_reference(float(P), pp)
        emit(rec="exp_reference_at_witness", precision=pp, ok=True)
    except Exception as e:                           # noqa: BLE001
        emit(rec="exp_reference_at_witness", precision=pp, ok=False,
             error=f"{type(e).__name__}: {e}")

# ── 4. cost: reference route vs the Q61 default ──────────────────────────────
def bench(fn, args, kw, n):
    t0 = time.perf_counter()
    for _ in range(n):
        fn(*args, **kw)
    return (time.perf_counter() - t0) / n

for name, args in (("cos", (0.7,)), ("sin", (0.7,)), ("atan", (0.7,)),
                   ("atan2", (0.7, 0.2)), ("exp", (0.7,)), ("log", (1.7,)),
                   ("sqrt", (2.0,)), ("hypot", (3.0, 4.0))):
    fn = getattr(R, name)
    try:
        n = 200
        base = bench(fn, args, {}, n)
        ref = bench(fn, args, {"precision": 61}, max(4, n // 20))
        emit(rec="cost", op=name, q61_s=round(base, 9), ref61_s=round(ref, 9),
             ratio=round(ref / base, 2) if base else None)
    except Exception as e:                           # noqa: BLE001
        emit(rec="cost", op=name, error=f"{type(e).__name__}: {e}")

# ── 5. what ARRIVES at the regression surface ────────────────────────────────
seen = []


def spy(realfn, label):
    def wrapper(*a, **kw):
        seen.append((label, [type(x).__name__ for x in a]))
        return realfn(*a, **kw)
    return wrapper


K._rcos = spy(R.cos, "kepler._rcos")
K._rsin = spy(R.sin, "kepler._rsin")
K._ratan2 = spy(R.atan2, "kepler._ratan2")

for lbl, thunk in (
    ("pin_slot(0.7,0.2,1.0)", lambda: K.pin_slot(0.7, 0.2, 1.0)),
    ("pin_slot(1,2,3)", lambda: K.pin_slot(1, 2, 3)),
    ("kepler_solve(1,0.2)", lambda: K.kepler_solve(1, 0.2)),
    ("equation_of_centre(1,0.0549,4)",
     lambda: K.equation_of_centre(1, 0.0549, 4)),
):
    seen.clear()
    try:
        val = thunk()
        emit(rec="arrival", site=lbl, value=repr(val), calls=list(seen))
    except Exception as e:                           # noqa: BLE001
        emit(rec="arrival", site=lbl, error=f"{type(e).__name__}: {e}",
             calls=list(seen))

# ica_jade reaches rational through the MODULE, so patch there
_rc, _rs, _ra = R.cos, R.sin, R.atan2
R.cos, R.sin, R.atan2 = (spy(_rc, "ica.cos"), spy(_rs, "ica.sin"),
                         spy(_ra, "ica.atan2"))
try:
    from srmech.signal_processing.closed_form_ops import ica_jade as IJ
    pub = [n for n in dir(IJ) if not n.startswith("_") and callable(getattr(IJ, n))]
    emit(rec="ica_surface", names=pub)
    seen.clear()
    sig = [[0.1, 0.9, 0.3, 0.7, 0.2, 0.8], [0.4, 0.2, 0.8, 0.1, 0.6, 0.3]]
    entry = getattr(IJ, "op", None)          # the module's public entry point
    res = entry(sig) if entry is not None else None
    emit(rec="arrival", site="ica_jade", value=str(type(res)),
         calls=list(seen)[:12], n_calls=len(seen))
except Exception as e:                               # noqa: BLE001
    emit(rec="arrival", site="ica_jade", error=f"{type(e).__name__}: {e}",
         calls=list(seen)[:12], n_calls=len(seen))
finally:
    R.cos, R.sin, R.atan2 = _rc, _rs, _ra

# ── 6. the FLOAT-PATH baseline, for bit-identity after the change ───────────
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
for a in GRID:
    for b in (0.2, -3.0, 1.0):
        for name in ("atan2", "hypot"):
            fn = getattr(R, name)
            try:
                lines.append(f"{name}({a!r},{b!r})={fn(a, b).as_pair()!r}")
            except Exception as e:                   # noqa: BLE001
                lines.append(f"{name}({a!r},{b!r})=RAISED {type(e).__name__}")
body = "\n".join(lines).encode()
emit(rec="float_baseline", n=len(lines), sha256=sha256_bytes(body))
print("\n".join(lines), file=sys.stderr)
