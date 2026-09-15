"""rc473 A6 repair pass (`#T1188`) — the generating code for every figure the
A6 section of ``python/CHANGELOG.md`` and the five new ADR-0009 §1.2 rows quote.

Three questions, each with its predicate written out:

  1. **``winding_fold``'s residue divergence and its LAW.** Until the A6
     repair pass the op's docstring asserted *"``theta_res`` equal to the fold
     grids' common resolution ... both quantise the SAME real residue"*.
     Measured, they do not; that sentence is corrected in place. This probe
     drives the DISPATCHED public op against ``laplacian._eph_seam_fold`` — the
     pure alternative the docstring names — IN ONE PROCESS, so the two columns
     cannot be a cell-configuration confound, and reports ``gap / |w|`` rather
     than a worst case, because the divergence is a LAW (proportional to the
     winding) and a worst case reads as an anecdote.

  2. **WHICH projection is accurate.** Against a 60-digit 2π literal that is
     neither projection's own constant, with exact ``Fraction`` arithmetic on
     the float64 image of ``theta``. Without this the row could only say "they
     differ", and a filing that cannot say which side drifts cannot state a
     close path.

  3. **The remaining cross-implementation divergences a merge gate named and
     nothing had filed** — ``jpeg`` / ``polyphase`` / ``loop_inv_hd`` at
     non-finite input, ``pin_slot`` / ``kepler_solve`` at non-finite scalar
     arguments, the laplacian family at a FLOAT node index (a finite argument),
     and ``srmech_log(-0.0)`` writing ``-inf`` on a refusal. Each row is
     emitted with BOTH cells' answers so the NDJSON is the evidence and not a
     summary of it.

  4. **The ops a merge gate measured diverging at their OWN DOCUMENTED EXAMPLE
     ARGUMENTS** — no adversarial input at all. Driven at
     ``python/tests/example_args_ledger.ndjson``'s own ``args``, because that
     ledger IS the gate's population.

     ⚠️ **The first version of this section drove those ops at arguments the
     probe INVENTED, and every one came back AGREE.** That reads as a
     refutation and is not one: a null at a different argument answers a
     different question, and reporting it as "does not reproduce" would have
     been this rc's own defect class a fifth time. Re-driven at the ledger's
     arguments, five of the seven DIVERGE, at the figures the gate quoted.
     The population is part of the predicate.

CELL AUTHENTICITY. Every native figure is taken behind
``srmech_rational_sqrt(NaN) -> status 2`` at the ctypes symbol. An rc472 ``.so``
returns **0** there; version and ABI alone do not distinguish the two, and this
probe's whole subject is values read off a library.

Run (native cell):  PYTHONPATH=python python3 notes/_rc473_a6_divergence_probe.py
Run (pure cell):    the same, with the shared library moved aside.
Writes ``notes/_rc473_a6_divergence_probe.ndjson`` (native cell only; the pure
column is carried inside the rows).
"""

from __future__ import annotations

import ctypes
import json
import math
import platform
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().with_suffix(".ndjson")

#: 2*pi to 60 significant decimal digits. Deliberately NOT srmech's own
#: constant on either side: an accuracy question decided with one of the two
#: constants under test is not a measurement.
TWO_PI = Fraction(
    6283185307179586476925286766559005768394338798750211641949,
    10 ** 57,
)

#: The angles the law is fitted over. Spread across five decades because a law
#: claimed from two points is a line drawn through two points.
LAW_ANGLES = (
    1.0, 10 * math.pi, 1e3, 1e4, 1e5, 1e6, 1e7, 1e8, 1e9, 1e10, 1e11, 1e12,
    1e13, 1e14, 1e15, 2.0 ** 40, 2.0 ** 50, 2.0 ** 53, 2.0 ** 54, 1.5e16,
    3.1415926535897932e16, -1e10, -1e8, -3.1415926535897932e16,
)
GRID = 2.0 ** -44


def _cell():
    from srmech import _native

    native = bool(_native.HAS_NATIVE and _native.LIB is not None)
    auth = None
    abi = None
    if native:
        fn = _native.LIB.srmech_rational_sqrt
        fn.argtypes = [ctypes.c_double, ctypes.POINTER(ctypes.c_double)]
        fn.restype = ctypes.c_int
        out = ctypes.c_double(0.0)
        auth = fn(float("nan"), ctypes.byref(out))
        _native.LIB.srmech_abi_version.restype = ctypes.c_int
        abi = _native.LIB.srmech_abi_version()
    return native, auth, abi


def _call(fn):
    """`(ok, repr)` — classify the exception, never swallow it."""
    try:
        value = fn()
        try:
            value = value.tolist()
        except AttributeError:
            pass
        return True, repr(value)[:600]
    except Exception as exc:                       # noqa: BLE001
        return False, "%s: %s" % (type(exc).__name__, str(exc)[:240])


def _fold_pair(theta):
    from srmech.cascade import one as one_mod
    from srmech.math import laplacian as lap

    w_d, res_d = one_mod.winding_fold(theta)
    w_p, qn = lap._eph_seam_fold(theta)
    return (w_d, res_d), (w_p, qn / float(lap._EPH_FOLD_DEN))


def q1_law(rows):
    """The residue divergence, as a law rather than a worst case."""
    ratios = []
    over = 0
    worst = (0.0, None)
    winding_disagreements = 0
    table = []
    for theta in LAW_ANGLES:
        (w_d, res_d), (w_p, res_p) = _fold_pair(theta)
        gap = abs(res_d - res_p)
        if w_d != w_p:
            winding_disagreements += 1
        if gap > GRID:
            over += 1
        if gap / GRID > worst[0]:
            worst = (gap / GRID, theta)
        # the law is only meaningful once the winding dominates the pure
        # path's own 2**-44 quantisation; below |w| ~ 1e8 that floor is what
        # is being read, and saying so is the difference between a fit and a
        # number that happens to average.
        if w_d and abs(w_d) >= 10 ** 8:
            ratios.append(gap / abs(w_d))
        table.append({
            "theta": repr(theta), "w": w_d, "w_agrees": w_d == w_p,
            "theta_res_dispatched": repr(res_d), "theta_res_pure": repr(res_p),
            "gap_over_2pow_minus_44": gap / GRID,
        })
    rows.append({
        "kind": "winding_fold_residue_law",
        "angles": len(LAW_ANGLES),
        "winding_disagreements": winding_disagreements,
        "rows_over_2pow_minus_44": over,
        "worst_multiple_of_2pow_minus_44": worst[0],
        "worst_at_theta": repr(worst[1]),
        "law_fitted_over_windings_at_or_above": 10 ** 8,
        "law_sample_count": len(ratios),
        "gap_per_turn_min": min(ratios) if ratios else None,
        "gap_per_turn_max": max(ratios) if ratios else None,
        "gap_per_turn_spread_ratio": (max(ratios) / min(ratios)) if ratios else None,
        "table": table,
    })


def q2_accuracy(rows):
    """Which side drifts, against a constant neither projection owns."""
    out = []
    for theta in (1e9, 1e10, 1e12, 1e14, 2.0 ** 53, 3.1415926535897932e16,
                  -3.1415926535897932e16):
        (w_d, res_d), (_w_p, res_p) = _fold_pair(theta)
        true_res = Fraction(*float(theta).as_integer_ratio()) - w_d * TWO_PI
        d_native = abs(Fraction(res_d) - true_res)
        d_pure = abs(Fraction(res_p) - true_res)
        out.append({
            "theta": repr(theta),
            "abs_native_minus_true": float(d_native),
            "abs_pure_minus_true": float(d_pure),
            "closer": "pure" if d_pure < d_native else
                      ("native" if d_native < d_pure else "tie"),
        })
    rows.append({
        "kind": "winding_fold_which_side_drifts",
        "reference": "2*pi to 60 significant decimal digits, neither projection's own",
        "all_rows_favour": ({r["closer"] for r in out}.pop()
                            if len({r["closer"] for r in out}) == 1 else "MIXED"),
        "rows": out,
    })


def q3_unfiled(rows, native):
    """The divergences a merge gate named and nothing had filed."""
    import srmech.signal_processing as sp
    from srmech.math import hdc
    from srmech.math import kepler
    from srmech.math import laplacian as lap
    from srmech.math import rational

    inf, nan = float("inf"), float("nan")
    cases = [
        ("jpeg_nan_image", "array kernel, non-finite",
         lambda: sp.jpeg(image=[[nan] * 8] * 8, block_size=8, decode=False, D=8192)),
        ("polyphase_plus_inf", "array kernel, non-finite",
         lambda: sp.polyphase(filter_taps=[inf] * 4, signal=[inf] * 3, L=2,
                              mode="interpolation", D=8192)),
        ("loop_inv_hd_nan", "array kernel, non-finite",
         lambda: hdc.loop_inv_hd([nan] * 8)),
        ("pin_slot_distance_plus_inf", "SCALAR, non-finite",
         lambda: kepler.pin_slot(pin_distance=inf, pin_offset=1.0, theta=0.0)),
        ("pin_slot_distance_minus_inf", "SCALAR, non-finite",
         lambda: kepler.pin_slot(pin_distance=-inf, pin_offset=1.0, theta=0.0)),
        ("kepler_solve_tolerance_plus_inf", "SCALAR, non-finite",
         lambda: kepler.kepler_solve(1.5707963267948966, 0.0549, tolerance=inf)),
        ("dense_laplacian_float_node_index", "FINITE argument",
         lambda: lap.dense_laplacian(2, [(-0.0, 1)])),
        ("fiedler_sparse_float_node_index", "FINITE argument",
         lambda: lap.fiedler_sparse(2, [(-0.0, 1)])),
        ("pure_rational_log_neg_zero", "refusal contract",
         lambda: rational.log(-0.0)),
    ]
    for name, klass, fn in cases:
        ok, value = _call(fn)
        rows.append({"kind": "cross_projection_case", "case": name,
                     "class": klass, "cell": "native" if native else "pure",
                     "ok": ok, "value": value})

    if native:
        from srmech import _native
        fn = _native.LIB.srmech_log
        fn.argtypes = [ctypes.c_double, ctypes.POINTER(ctypes.c_double)]
        fn.restype = ctypes.c_int
        out = ctypes.c_double(123.0)
        st = fn(-0.0, ctypes.byref(out))
        rows.append({"kind": "cross_projection_case",
                     "case": "C_srmech_log_neg_zero_at_the_symbol",
                     "class": "refusal writes a non-NaN", "cell": "native",
                     "ok": True, "value": "status=%d out=%r" % (st, out.value)})


#: Ops a merge gate measured diverging at their OWN example arguments.
_LEDGER_OPS = (
    "srmech.math.hdc.loop_inv_hd",
    "srmech.math.laplacian.fiedler_sparse",
    "srmech.math.laplacian.ground_state_flux_response",
    "srmech.math.laplacian.propagate_sparse",
    "srmech.signal_processing.fir",
    "srmech.signal_processing.ica_jade",
    "srmech.signal_processing.matched_filter",
)


def _resolve(dotted):
    import importlib

    parts = dotted.split(".")
    for cut in range(len(parts) - 1, 0, -1):
        try:
            mod = importlib.import_module(".".join(parts[:cut]))
        except ImportError:
            continue
        obj = mod
        for attr in parts[cut:]:
            obj = getattr(obj, attr, None)
            if obj is None:
                break
        if obj is not None:
            return obj
    return None


def _canon(value):
    try:
        value = value.tolist()
    except AttributeError:
        pass
    if isinstance(value, (list, tuple)):
        return [_canon(x) for x in value]
    return repr(value)


def q4_example_args(rows, native):
    """The gate's own population: each op at the LEDGER's arguments."""
    ledger = ROOT / "python" / "tests" / "example_args_ledger.ndjson"
    if not ledger.exists():
        rows.append({"kind": "note", "text": "example_args_ledger.ndjson absent"})
        return
    with ledger.open(encoding="utf-8") as handle:
        entries = [json.loads(line) for line in handle]
    seen = set()
    for entry in entries[1:]:
        op = entry.get("op")
        if op not in _LEDGER_OPS or op in seen:
            continue
        seen.add(op)
        args = entry.get("args")
        fn = _resolve(op)
        if not args or fn is None:
            rows.append({"kind": "example_arg_case", "case": op,
                         "cell": "native" if native else "pure", "ok": False,
                         "value": "NO LEDGER ARGS" if not args else "UNRESOLVED"})
            continue
        try:
            value = fn(**args) if isinstance(args, dict) else fn(*args)
            payload = json.dumps(_canon(value))
        except Exception as exc:                   # noqa: BLE001
            rows.append({"kind": "example_arg_case", "case": op,
                         "cell": "native" if native else "pure", "ok": False,
                         "value": "%s: %s" % (type(exc).__name__, str(exc)[:240])})
            continue
        rows.append({"kind": "example_arg_case", "case": op,
                     "cell": "native" if native else "pure", "ok": True,
                     "value": payload[:4000]})


def main() -> int:
    native, auth, abi = _cell()
    if native and auth != 2:
        raise SystemExit(
            "CELL NOT AUTHENTIC: srmech_rational_sqrt(NaN) returned %r, not 2. "
            "That is an rc472-or-earlier library; every native figure below "
            "would be attributed to the wrong tree." % (auth,)
        )
    import srmech

    rows = [{
        "kind": "conditions",
        "srmech_version": srmech.__version__,
        "has_native": native,
        "abi_version": abi,
        "cell_authenticity_rational_sqrt_nan_status": auth,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "numpy_present": __import__("importlib.util", fromlist=["util"])
                          .find_spec("numpy") is not None,
    }]
    q3_unfiled(rows, native)
    q4_example_args(rows, native)
    if native:
        q1_law(rows)
        q2_accuracy(rows)
    else:
        rows.append({"kind": "note", "text":
                     "winding_fold law and accuracy rows need a native cell; "
                     "on a pure cell the dispatched op IS the pure fold and "
                     "the comparison would agree with itself."})

    if native:
        with OUT.open("w", encoding="utf-8", newline="\n") as handle:
            for row in rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
        print("wrote %d rows -> %s" % (len(rows), OUT))
    for row in rows:
        if row["kind"] in ("conditions", "winding_fold_residue_law",
                           "winding_fold_which_side_drifts"):
            trimmed = {k: v for k, v in row.items() if k not in ("table", "rows")}
            print(json.dumps(trimmed, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
