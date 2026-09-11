"""rc473 stage C (`#T1188`) — the Python-side consequence, MEASURED.

Two pre-dispatch guards were added in the two rcs that covered the C defect
from the Python side:

  * ``srmech/math/kepler.py`` — ``equation_of_centre``'s rc472 loop, which
    walks the harmonics and raises ``rational.sin``'s own two refusals BEFORE
    ``if _native.HAS_NATIVE:``;
  * ``srmech/math/laplacian.py:3895`` — ``_q61_trig_range_refuse``, rc466's
    cover for the array kernel, called at ``:4041`` and ``:4068``.

stage B made the C projection refuse. This probe asks, for each guard and for
each input, three questions whose answers decide it:

  1. what the C SYMBOL does now (ctypes, no wrapper);
  2. what the Python op does WITH the guard in place;
  3. what the Python op would do WITHOUT it — emulated by calling the
     post-guard body directly, so the answer is executed and not predicted.

Run:  PYTHONPATH=<repo>/docs/srmech/python uv run --python 3.12 \
          --no-project --offline python notes/_rc473_python_guard_probe.py

Writes one NDJSON row per measurement to
``notes/_rc473_python_guard_probe.ndjson`` and prints a table.

numpy-free. No ``hashlib``. No ``abs()`` — every magnitude below is a
Class-K pin-slot sign branch composed with Class C re-application.
"""

from __future__ import annotations

import ctypes
import json
import platform
import sys
from pathlib import Path

from srmech import _native
from srmech.math import kepler, laplacian, rational

NAN = float("nan")
INF = float("inf")

_D = ctypes.c_double
_DP = ctypes.POINTER(ctypes.c_double)
_U32 = ctypes.c_uint32

_ROWS: list[dict] = []


def _conditions() -> dict:
    return {
        "kind": "conditions",
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "has_native": bool(_native.HAS_NATIVE),
        "expected_abi": _native.EXPECTED_ABI_VERSION,
        "native_abi": getattr(_native, "NATIVE_ABI_VERSION", None),
        "lib": getattr(getattr(_native, "LIB", None), "_name", None),
        "srmech_version": __import__("srmech").__version__,
    }


def _bind(name: str, argtypes: list):
    fn = getattr(_native.LIB, name)
    fn.argtypes = argtypes
    fn.restype = ctypes.c_int
    return fn


def _call(label: str, fn, *args):
    """Call a Python callable; classify raise-vs-return."""
    try:
        value = fn(*args)
    except Exception as exc:                      # noqa: BLE001 - classifying
        return {"label": label, "raised": type(exc).__name__, "text": str(exc)}
    return {"label": label, "raised": None, "value": repr(value)}


def _record(row: dict) -> None:
    _ROWS.append(row)
    print(json.dumps(row, sort_keys=True))


# --------------------------------------------------------------------------
# GUARD 1 — kepler.equation_of_centre's rc472 pre-dispatch loop
# --------------------------------------------------------------------------
def _eoc_without_the_guard(M_rad, e, n_terms):
    """``equation_of_centre``'s body with the rc472 guard loop SKIPPED.

    Executed, not predicted: this is the same dispatch the op would perform
    if the guard were deleted, including the pure-Python fallback.
    """
    if not (0.0 <= e < 1.0):
        raise ValueError(f"equation_of_centre: e must satisfy 0 <= e < 1; got {e}")
    if not (1 <= n_terms <= kepler.EOC_MAX_TERMS):
        raise ValueError(
            f"equation_of_centre: n_terms must be in [1, {kepler.EOC_MAX_TERMS}]; "
            f"got {n_terms}")
    if _native.HAS_NATIVE:
        out = ctypes.c_double(0.0)
        rc = _native.LIB.srmech_equation_of_centre(
            ctypes.c_double(M_rad), ctypes.c_double(e),
            ctypes.c_uint32(n_terms), ctypes.byref(out))
        if rc != _native.SRMECH_OK:
            raise ValueError(f"srmech_equation_of_centre returned status {rc}")
        return out.value
    delta = 0.0
    e_power = 1.0
    for k_idx in range(n_terms):
        e_power *= e
        harmonic = (k_idx + 1) * M_rad
        delta += kepler._EOC_COEFFS[k_idx] * e_power * rational.sin(harmonic)
    return float(delta)


def _eoc_pure(M_rad, e, n_terms):
    """The PURE cascade only — the text oracle for the fallthrough design."""
    delta = 0.0
    e_power = 1.0
    for k_idx in range(n_terms):
        e_power *= e
        harmonic = (k_idx + 1) * M_rad
        delta += kepler._EOC_COEFFS[k_idx] * e_power * rational.sin(harmonic)
    return float(delta)


_EOC_CASES = [
    ("2**53+1 int, n=4 (the named defect)", 2 ** 53 + 1, 0.0549, 4),
    ("2**53+1 float, n=4", 2.0 ** 53 + 1, 0.0549, 4),
    ("nan, n=1", NAN, 0.0549, 1),
    ("+inf, n=1", INF, 0.0549, 1),
    ("-inf, n=1", -INF, 0.0549, 1),
    ("2**55, n=1", 2.0 ** 55, 0.0549, 1),
    ("2**53+1 int, n=1 (the CONTROL: answers)", 2 ** 53 + 1, 0.0549, 1),
    ("0.7, n=4 (ordinary)", 0.7, 0.0549, 4),
]


def probe_guard_1() -> None:
    fn = _bind("srmech_equation_of_centre", [_D, _D, _U32, _DP])
    for label, M, e, n in _EOC_CASES:
        out = ctypes.c_double(-12345.0)
        status = fn(_D(M), _D(e), _U32(n), ctypes.byref(out))
        row = {
            "kind": "guard1_eoc",
            "case": label,
            "M_repr": repr(M),
            "e": e,
            "n_terms": n,
            "c_status": int(status),
            "c_value": repr(out.value),
            "with_guard": _call("with_guard", kepler.equation_of_centre, M, e, n),
            "without_guard": _call("without_guard", _eoc_without_the_guard, M, e, n),
            "pure_cascade": _call("pure", _eoc_pure, M, e, n),
        }
        _record(row)


# --------------------------------------------------------------------------
# GUARD 1b — the two kepler wrappers that never had a guard
# --------------------------------------------------------------------------
def probe_guard_1b() -> None:
    ps = _bind("srmech_pin_slot", [_D, _D, _D, _DP])
    ks = _bind("srmech_kepler_solve", [_D, _D, _D, _U32, _DP])
    for label, theta in [("2**55", 2.0 ** 55), ("nan", NAN), ("+inf", INF)]:
        out = ctypes.c_double(-12345.0)
        st = ps(_D(theta), _D(0.5), _D(1.0), ctypes.byref(out))
        _record({
            "kind": "guard1b_pin_slot",
            "case": label,
            "c_status": int(st),
            "c_value": repr(out.value),
            "wrapper": _call("pin_slot", kepler.pin_slot, theta, 0.5, 1.0),
            "pure_peer": _call(
                "pure", lambda t: float(rational.atan2(
                    0.5 * rational.sin(t), 1.0 + 0.5 * rational.cos(t))), theta),
        })
    for label, M in [("2**55", 2.0 ** 55), ("nan", NAN), ("+inf", INF)]:
        out = ctypes.c_double(-12345.0)
        st = ks(_D(M), _D(0.3), _D(1e-12), _U32(20), ctypes.byref(out))
        _record({
            "kind": "guard1b_kepler_solve",
            "case": label,
            "c_status": int(st),
            "c_value": repr(out.value),
            "wrapper": _call("kepler_solve", kepler.kepler_solve, M, 0.3),
            "pure_peer": _call("pure_sin_of_M", rational.sin, M),
        })


# --------------------------------------------------------------------------
# GUARD 2 — laplacian._q61_trig_range_refuse
# --------------------------------------------------------------------------
def _ew_without_the_guard(values, op_name):
    """``elementwise_transcendental``'s real path with the guard SKIPPED.

    Mirrors the op's own dispatch: native first, and on any non-OK status the
    existing fallthrough hands the whole array to the pure Class-N loop.
    """
    real_flat = [float(x) for x in values]
    if op_name == "exp_i":
        ok_c, cos_out, _ = laplacian._real_transcendental_native(
            real_flat, _native.SRMECH_TRANS_COS)
        ok_s, sin_out, _ = laplacian._real_transcendental_native(
            real_flat, _native.SRMECH_TRANS_SIN)
        if not (ok_c and ok_s and cos_out is not None and sin_out is not None):
            cos_out = laplacian._real_transcendental_loop(real_flat, "cos")
            sin_out = laplacian._real_transcendental_loop(real_flat, "sin")
        return [complex(cos_out[i], sin_out[i]) for i in range(len(real_flat))]
    op_id = laplacian._TRANS_OP_IDS[op_name]
    ok, out, rc = laplacian._real_transcendental_native(real_flat, op_id)
    if ok:
        if out is not None:
            return list(out)
        if rc == _native.SRMECH_ERR_BAD_INPUT and op_name == "log":
            raise ValueError("log requires all arr[i] > 0")
    return laplacian._real_transcendental_loop(real_flat, op_name)


_EW_CASES = [
    ([2.0 ** 55], "cos"),
    ([2.0 ** 55], "sin"),
    ([2.0 ** 55], "exp_i"),
    ([NAN], "cos"),
    ([NAN], "sin"),
    ([NAN], "exp_i"),
    ([NAN], "exp"),
    ([NAN], "log"),
    ([INF], "cos"),
    ([INF], "sin"),
    ([INF], "exp"),          # D8: C serves, pure refuses — a FILED decline
    ([INF], "log"),          # D8
    ([-1.0], "log"),
    ([0.7], "cos"),          # ordinary control
    ([0.7, 2.0 ** 55], "cos"),   # mixed: the refusal is element 1
]

_OP_IDS = {"cos": 1, "sin": 2, "exp": 0, "log": 3}


def probe_guard_2() -> None:
    fn = _bind("srmech_elementwise_transcendental",
               [_U32, _DP, ctypes.c_int, _DP])
    for values, op in _EW_CASES:
        n = len(values)
        c_rows = []
        for c_op in (("cos", "sin") if op == "exp_i" else (op,)):
            arr = (ctypes.c_double * n)(*values)
            out = (ctypes.c_double * n)(*([-12345.0] * n))
            st = fn(_U32(n), ctypes.cast(arr, _DP), ctypes.c_int(_OP_IDS[c_op]),
                    ctypes.cast(out, _DP))
            c_rows.append({"c_op": c_op, "status": int(st),
                           "out": [repr(out[i]) for i in range(n)]})
        # does the guard itself fire for this row?
        guard_fired = _call(
            "guard_only", laplacian._q61_trig_range_refuse,
            [float(x) for x in values], op)
        _record({
            "kind": "guard2_elementwise",
            "values": [repr(v) for v in values],
            "op": op,
            "c": c_rows,
            "guard_alone": guard_fired,
            "with_guard": _call("with_guard",
                                laplacian.elementwise_transcendental, values, op),
            "without_guard": _call("without_guard", _ew_without_the_guard,
                                   values, op),
            "pure_loop": _call(
                "pure_loop", laplacian._real_transcendental_loop,
                [float(x) for x in values],
                "cos" if op == "exp_i" else op),
        })


def main() -> int:
    _record(_conditions())
    probe_guard_1()
    probe_guard_1b()
    probe_guard_2()
    dest = Path(__file__).resolve().parent / "_rc473_python_guard_probe.ndjson"
    with dest.open("w", encoding="utf-8", newline="\n") as fh:
        for row in _ROWS:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    print(f"\nwrote {len(_ROWS)} rows -> {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
