"""rc473 A0 — the baseline, recorded on the UNMODIFIED tree (`#T1188`).

Generating code for every figure rc473's stage-A commit messages quote, per
``[[feedback_computational_provenance_discipline]]``.  Run BEFORE any repair,
so that "went red" and "was already wrong" are decidable afterwards.

The script prints its OWN conditions (interpreter, native/pure, host, library
path, ABI pair) as its first record, because a figure carried across a
condition change is the class of error every wrong count in this rc's history
came from.

Usage (WSL2, numpy absent)::

    PYTHONPATH=docs/srmech/python uv run --python 3.12 --no-project --offline \\
        python docs/srmech/notes/_rc473_a0_baseline.py

Output is NDJSON on stdout, one record per line
(``[[feedback_ndjson_over_bloated_json]]``).
"""

from __future__ import annotations

import ctypes
import json
import math
import platform
import re
import sys

from srmech import _native
from srmech.math import rational

LIB = _native.LIB
NAN = float("nan")
INF = float("inf")

D = ctypes.c_double
DP = ctypes.POINTER(ctypes.c_double)
U32 = ctypes.c_uint32
I64P = ctypes.POINTER(ctypes.c_int64)


def _emit(**kw) -> None:
    print(json.dumps(kw, sort_keys=True))


def _sig(name, argtypes):
    fn = getattr(LIB, name)
    fn.argtypes = argtypes
    fn.restype = ctypes.c_int
    return fn


_UNARY = {
    name: _sig(name, [D, DP])
    for name in (
        "srmech_sin",
        "srmech_cos",
        "srmech_atan",
        "srmech_exp",
        "srmech_log",
        "srmech_rational_sqrt",
    )
}
_ATAN2 = _sig("srmech_atan2", [D, D, DP])
_PIN_SLOT = _sig("srmech_pin_slot", [D, D, D, DP])
_KEPLER = _sig("srmech_kepler_solve", [D, D, D, U32, DP])
_EOC = _sig("srmech_equation_of_centre", [D, D, U32, DP])
_ELEM = _sig("srmech_elementwise_transcendental", [U32, DP, ctypes.c_int, DP])
_SIN_Q61 = _sig("srmech_sin_q61", [D, I64P])
_ATAN_Q61 = _sig("srmech_atan_q61", [D, I64P])
_KURA = _sig(
    "srmech_cascade_kuramoto_step_f64",
    [DP, DP, ctypes.c_size_t, D, D, DP],
)
_KURA_GEN = _sig(
    "srmech_cascade_kuramoto_step_general_f64",
    [DP, DP, ctypes.c_size_t, DP, D, D, DP, DP, D, DP],
)


def c_unary(name: str, x: float):
    out = ctypes.c_double(-12345.0)
    status = _UNARY[name](x, ctypes.byref(out))
    return status, out.value


def c_q61(fn, x: float):
    out = ctypes.c_int64(-12345)
    status = fn(x, ctypes.byref(out))
    return status, out.value


def pure(fn, *args):
    """Classify a pure-projection call: returned-with-value, or refused-by-name."""
    try:
        value = fn(*args)
    except BaseException as exc:  # noqa: BLE001 - classifying, not handling
        return type(exc).__name__, str(exc)[:160]
    return "returned", repr(value)


def q_as_float(text: str) -> float:
    """``Q(num, den)`` repr -> float, for the atan(+-inf) comparison only."""
    match = re.search(r"Q\((-?\d+),\s*(\d+)\)", text)
    if match:
        return int(match.group(1)) / int(match.group(2))
    return float("nan")


def numpy_importable() -> bool:
    try:
        import numpy  # noqa: F401
    except Exception:  # noqa: BLE001
        return False
    return True


def conditions() -> None:
    _emit(
        kind="conditions",
        python=sys.version.split()[0],
        impl=platform.python_implementation(),
        uname=" ".join(platform.uname()),
        numpy_present=numpy_importable(),
        has_native=_native.HAS_NATIVE,
        expected_abi=_native.EXPECTED_ABI_VERSION,
        native_abi=_native.NATIVE_ABI_VERSION,
        lib=str(LIB._name),
    )


def required_six() -> None:
    """The six C reads the build brief names by hand."""
    out = ctypes.c_double(0.0)
    status = _EOC(2.0 ** 53 + 1, 0.0549, 4, ctypes.byref(out))
    _emit(
        kind="c",
        call="srmech_equation_of_centre(2.0**53+1, 0.0549, 4)",
        status=status,
        value=repr(out.value),
    )

    out = ctypes.c_double(0.0)
    status = _PIN_SLOT(float(2 ** 55), 0.5, 1.0, ctypes.byref(out))
    _emit(kind="c", call="srmech_pin_slot(2**55, 0.5, 1.0)",
          status=status, value=repr(out.value))

    out = ctypes.c_double(0.0)
    status = _KEPLER(float(2 ** 55), 0.3, 1e-12, 20, ctypes.byref(out))
    _emit(
        kind="c",
        call="srmech_kepler_solve(2**55, 0.3, 1e-12, 20)",
        status=status,
        value=repr(out.value),
        E_equals_M=(out.value == float(2 ** 55)),
    )

    for name, arg, label in (
        ("srmech_sin", NAN, "srmech_sin(nan)"),
        ("srmech_atan", NAN, "srmech_atan(nan)"),
        ("srmech_rational_sqrt", -4.0, "srmech_rational_sqrt(-4.0)"),
    ):
        status, value = c_unary(name, arg)
        _emit(kind="c", call=label, status=status, value=repr(value))


def atan_rows() -> None:
    """The atan rows of the rc473 gate are WRITTEN FROM THIS, not assumed."""
    for arg, label in ((INF, "+inf"), (-INF, "-inf")):
        status, value = c_unary("srmech_atan", arg)
        _emit(kind="c", call="srmech_atan(%s)" % label, status=status,
              value=repr(value))
        outcome, detail = pure(rational.atan, arg)
        _emit(
            kind="pure",
            call="rational.atan(%s)" % label,
            outcome=outcome,
            detail=detail,
            as_float=(q_as_float(detail) if outcome == "returned" else None),
        )

    for y, x, label in (
        (INF, 1.0, "atan2(+inf, 1.0)"),
        (-INF, 1.0, "atan2(-inf, 1.0)"),
        (1.0, INF, "atan2(1.0, +inf)"),
        (1.0, -INF, "atan2(1.0, -inf)"),
        (INF, INF, "atan2(+inf, +inf)"),
        (NAN, 1.0, "atan2(nan, 1.0)"),
    ):
        out = ctypes.c_double(0.0)
        status = _ATAN2(y, x, ctypes.byref(out))
        _emit(kind="c", call="srmech_" + label, status=status,
              value=repr(out.value))
        outcome, detail = pure(rational.atan2, y, x)
        _emit(
            kind="pure",
            call="rational." + label,
            outcome=outcome,
            detail=detail,
            as_float=(q_as_float(detail) if outcome == "returned" else None),
        )


def roster_grid() -> None:
    """Every exported scalar callee x the four boundary arguments."""
    for name in (
        "srmech_sin",
        "srmech_cos",
        "srmech_atan",
        "srmech_exp",
        "srmech_log",
        "srmech_rational_sqrt",
    ):
        for arg, label in (
            (NAN, "nan"),
            (INF, "+inf"),
            (-INF, "-inf"),
            (float(2 ** 55), "2**55"),
            (math.nextafter(float(2 ** 55), 0.0), "2**55-1ulp"),
        ):
            status, value = c_unary(name, arg)
            _emit(kind="c", call="%s(%s)" % (name, label), status=status,
                  value=repr(value))

    status, value = c_q61(_SIN_Q61, NAN)
    _emit(kind="c", call="srmech_sin_q61(nan)", status=status, value=repr(value))
    status, value = c_q61(_ATAN_Q61, NAN)
    _emit(kind="c", call="srmech_atan_q61(nan)", status=status, value=repr(value))


def elementwise_grid() -> None:
    """The array kernel — the measured NaN hole the Python cover does not reach."""
    for op, op_id in (("EXP", 0), ("COS", 1), ("SIN", 2), ("LOG", 3)):
        for arg, label in ((NAN, "nan"), (INF, "+inf"), (float(2 ** 55), "2**55")):
            arr = (ctypes.c_double * 1)(arg)
            out = (ctypes.c_double * 1)(-12345.0)
            status = _ELEM(1, ctypes.cast(arr, DP), op_id, ctypes.cast(out, DP))
            _emit(
                kind="c",
                call="srmech_elementwise_transcendental([%s], %s)" % (label, op),
                status=status,
                value=repr(out[0]),
            )


def kuramoto_grid() -> None:
    """Both exported Kuramoto steps, on a theta vector carrying one bad entry."""
    for arg, label in ((float(2 ** 55), "2**55"), (NAN, "nan"), (INF, "+inf")):
        theta = (ctypes.c_double * 2)(0.0, arg)
        omega = (ctypes.c_double * 2)(0.0, 0.0)
        out = (ctypes.c_double * 2)(-12345.0, -12345.0)
        status = _KURA(
            ctypes.cast(theta, DP), ctypes.cast(omega, DP), 2, 1.0, 0.1,
            ctypes.cast(out, DP),
        )
        _emit(
            kind="c",
            call="srmech_cascade_kuramoto_step_f64([0.0, %s], [0,0], n=2, K=1, dt=0.1)"
                 % label,
            status=status,
            value=repr([out[0], out[1]]),
        )

        out = (ctypes.c_double * 2)(-12345.0, -12345.0)
        status = _KURA_GEN(
            ctypes.cast(theta, DP), ctypes.cast(omega, DP), 2, None, 1.0, 0.1,
            None, None, 0.1, ctypes.cast(out, DP),
        )
        _emit(
            kind="c",
            call="srmech_cascade_kuramoto_step_general_f64([0.0, %s], alpha=0.1)"
                 % label,
            status=status,
            value=repr([out[0], out[1]]),
        )


def pure_grid() -> None:
    for fn, args, label in (
        (rational.sin, (NAN,), "rational.sin(nan)"),
        (rational.cos, (NAN,), "rational.cos(nan)"),
        (rational.atan, (NAN,), "rational.atan(nan)"),
        (rational.exp, (NAN,), "rational.exp(nan)"),
        (rational.log, (NAN,), "rational.log(nan)"),
        (rational.sqrt, (-4.0,), "rational.sqrt(-4.0)"),
        (rational.sqrt, (INF,), "rational.sqrt(+inf)"),
        (rational.exp, (INF,), "rational.exp(+inf)"),
        (rational.log, (INF,), "rational.log(+inf)"),
        (rational.sin, (float(2 ** 55),), "rational.sin(2**55)"),
        (rational.cos, (float(2 ** 55),), "rational.cos(2**55)"),
    ):
        outcome, detail = pure(fn, *args)
        _emit(kind="pure", call=label, outcome=outcome, detail=detail)


def main() -> int:
    conditions()
    required_six()
    atan_rows()
    roster_grid()
    elementwise_grid()
    kuramoto_grid()
    pure_grid()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
