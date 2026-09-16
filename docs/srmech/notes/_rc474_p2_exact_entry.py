"""rc474 (`#T1188`) P2 — can an EXACT ENTRY separate the witness, and at what cost?

P1 measured that ``precision=61`` separates NOTHING for any of the nine ops.
The reason is structural, not numeric: every ``precision=P`` route is entered
BELOW ``x = float(x)``, so the exact-rational reference is handed an operand
that has already been demoted. This file asks the question P1 could not: given
the SAME reference machinery entered ABOVE that line, with the operand as an
exact ``(num, den)`` pair, does the witness separate — and what does it cost?

The prototypes below are the shipped helper bodies with the float entry
removed; nothing else is changed. It also re-runs the ARRIVAL spy, because P1
measured every kepler / ica site as ZERO calls on a native cell (the C peer
answers and the pure cascade is never reached), so the regression surface has
to be read in the cell where it actually executes.

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

emit(rec="banner", version=srmech.__version__,
     HAS_NATIVE=getattr(NB, "HAS_NATIVE", None),
     EXPECTED_ABI=getattr(NB, "EXPECTED_ABI_VERSION", None),
     NATIVE_ABI=getattr(NB, "NATIVE_ABI_VERSION", None),
     trans_q61=NB.has_native_trans_q61(),
     cell="native" if getattr(NB, "HAS_NATIVE", False) else "pure",
     f_rational=R.__file__)

P = 2 ** 53 + 1
F = 2 ** 53
G = 2 ** 53 + 2


def trig_exact(xn: int, xd: int, precision: int, want: str):
    """:func:`R._trig_reference` with the float entry REMOVED — the operand is
    an exact ``(num, den)`` pair and nothing rounds it."""
    Pp = R._classn_working(precision, kind="terms").effective
    tgt = Pp + 8
    pin0, pid0 = R._pi_exact(64)
    n = R._round_div(2 * xn * pid0, xd * pin0)
    nbits = n if n >= 0 else -n
    pin, pid = R._pi_exact(tgt + nbits.bit_length() + 6)
    rn = xn * (2 * pid) - n * pin * xd
    rd = xd * (2 * pid)
    rn, rd = R._reduce_rational(rn, rd)
    octant = n % 4
    if want == "cos":
        use_cos = octant in (0, 2)
        neg = octant in (1, 2)
    else:
        use_cos = octant in (1, 3)
        neg = octant in (2, 3)
    if use_cos:
        vn, vd = R.cos_series_truncate(rn, rd, R._num_terms_for(rn, rd, tgt, "cos"))
    else:
        vn, vd = R.sin_series_truncate(rn, rd, R._num_terms_for(rn, rd, tgt, "sin"))
    if neg:
        vn = -vn
    return R._q(vn, vd)


PREC = 61

# ── 1. does the EXACT entry separate the witness? ────────────────────────────
for want in ("cos", "sin"):
    a = trig_exact(P, 1, PREC, want)
    b = trig_exact(F, 1, PREC, want)
    c = trig_exact(G, 1, PREC, want)
    emit(rec="exact_entry", op=want, separates=(a != b), pf_differ=(a != b),
         fg_differ=(b != c), a_float=float(a), b_float=float(b))

a = R._atan_ratio_reference(P, 1, PREC)
b = R._atan_ratio_reference(F, 1, PREC)
c = R._atan_ratio_reference(G, 1, PREC)
emit(rec="exact_entry", op="atan", separates=(a != b), pf_differ=(a != b),
     fg_differ=(b != c))

# atan2(y, x) with y exact and x = 1 -> the exact ratio is y/1
a = R._atan_ratio_reference(P, 1, PREC)
b = R._atan_ratio_reference(F, 1, PREC)
emit(rec="exact_entry", op="atan2", separates=(a != b))

ka = R._sqrt_relative_k(P, 1, R._SQRT_Q_K)
a = R._sqrt_rational(P, 1, ka)
b = R._sqrt_rational(F, 1, R._sqrt_relative_k(F, 1, R._SQRT_Q_K))
c = R._sqrt_rational(G, 1, R._sqrt_relative_k(G, 1, R._SQRT_Q_K))
emit(rec="exact_entry", op="sqrt", separates=(a != b), fg_differ=(b != c), k=ka)

# hypot(a, 1): num = a^2 + 1 exactly
def hyp(v):
    num, den = v * v + 1, 1
    return R._sqrt_rational(num, den, R._sqrt_relative_k(num, den, R._SQRT_Q_K))


a, b, c = hyp(P), hyp(F), hyp(G)
emit(rec="exact_entry", op="hypot", separates=(a != b), fg_differ=(b != c))

# ── 1b. THE PRECISION SWEEP. Separation is not free at every P: atan(2**53+1)
# and atan(2**53) differ by ~1.2e-32, far BELOW a 2**-61 bound (~4.3e-19), so a
# default precision chosen for cos/sin need not separate atan at all. Measured
# rather than assumed, because it decides the default.
for pp in (53, 61, 96, 128, 160, 224):
    row = {"rec": "precision_sweep", "precision": pp}
    try:
        row["cos"] = (trig_exact(P, 1, pp, "cos") != trig_exact(F, 1, pp, "cos"))
        row["sin"] = (trig_exact(P, 1, pp, "sin") != trig_exact(F, 1, pp, "sin"))
        row["atan"] = (R._atan_ratio_reference(P, 1, pp)
                       != R._atan_ratio_reference(F, 1, pp))
        row["sqrt"] = (R._sqrt_rational(P, 1, pp) != R._sqrt_rational(F, 1, pp))
        row["hypot"] = (R._sqrt_rational(P * P + 1, 1, pp)
                        != R._sqrt_rational(F * F + 1, 1, pp))
    except Exception as e:                           # noqa: BLE001
        row["error"] = f"{type(e).__name__}: {e}"
    emit(**row)

# how many bits does atan actually NEED? the gap is ~1/(2**53)**2
for pp in (96, 107, 108, 112, 128):
    try:
        t0 = time.perf_counter()
        sep = (R._atan_ratio_reference(P, 1, pp)
               != R._atan_ratio_reference(F, 1, pp))
        emit(rec="atan_bits", precision=pp, separates=sep,
             seconds=round(time.perf_counter() - t0, 6))
    except Exception as e:                           # noqa: BLE001
        emit(rec="atan_bits", precision=pp, error=f"{type(e).__name__}: {e}")

# ── 2. cost of the EXACT entry, against the shipped Q61 float route ─────────
def bench(fn, n):
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    return (time.perf_counter() - t0) / n


rows = [
    ("cos", lambda: R.cos(0.7), lambda: trig_exact(7, 10, PREC, "cos")),
    ("sin", lambda: R.sin(0.7), lambda: trig_exact(7, 10, PREC, "sin")),
    ("atan", lambda: R.atan(0.7), lambda: R._atan_ratio_reference(7, 10, PREC)),
    ("atan2", lambda: R.atan2(0.7, 0.2),
     lambda: R._atan_ratio_reference(7 * 10, 10 * 2, PREC)),
    ("sqrt", lambda: R.sqrt(2.0),
     lambda: R._sqrt_rational(2, 1, R._sqrt_relative_k(2, 1, R._SQRT_Q_K))),
    ("hypot", lambda: R.hypot(3.0, 4.0),
     lambda: R._sqrt_rational(25, 1, R._sqrt_relative_k(25, 1, R._SQRT_Q_K))),
]
for name, fast, exact in rows:
    try:
        base = bench(fast, 200)
        ex = bench(exact, 50)
        emit(rec="exact_cost", op=name, q61_s=round(base, 9),
             exact_s=round(ex, 9), ratio=round(ex / base, 2) if base else None)
    except Exception as e:                           # noqa: BLE001
        emit(rec="exact_cost", op=name, error=f"{type(e).__name__}: {e}")

# ── 3. the ARRIVAL surface, in whichever cell this is ───────────────────────
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

_rc, _rs, _ra = R.cos, R.sin, R.atan2
R.cos, R.sin, R.atan2 = (spy(_rc, "ica.cos"), spy(_rs, "ica.sin"),
                         spy(_ra, "ica.atan2"))
try:
    from srmech.signal_processing.closed_form_ops import ica_jade as IJ
    seen.clear()
    sig = [[0.1, 0.9, 0.3, 0.7, 0.2, 0.8], [0.4, 0.2, 0.8, 0.1, 0.6, 0.3]]
    IJ.op(sig)
    emit(rec="arrival", site="ica_jade.op", n_calls=len(seen),
         calls=list(seen)[:8])
except Exception as e:                               # noqa: BLE001
    emit(rec="arrival", site="ica_jade.op", error=f"{type(e).__name__}: {e}",
         n_calls=len(seen), calls=list(seen)[:8])
finally:
    R.cos, R.sin, R.atan2 = _rc, _rs, _ra

# ── 4. the float-path baseline digest, in THIS cell ────────────────────────
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
emit(rec="float_baseline", n=len(lines), sha256=sha256_bytes(body))
