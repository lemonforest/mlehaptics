"""rc473 stage C (`#T1188`) — the one input the D10 fallthrough could ANSWER
where C refused: ``atan2(0, 0)`` reached through ``pin_slot``.

``pin_slot``'s Python wrapper refuses ``pin_offset == 0 and pin_distance == 0``
BEFORE dispatch, because ``atan2(0, 0)`` is implementation-defined. But that
precondition is stated on the ARGUMENTS, and the origin is reachable from
non-zero arguments: ``theta = 0`` gives ``sin = 0`` and ``cos = 1``, so
``pin_distance = -pin_offset`` puts BOTH ``atan2`` operands at zero with
neither argument zero.

If C refuses the origin and the pure cascade answers it, a
``SRMECH_ERR_BAD_INPUT`` fallthrough would serve what the C symbol refused —
ADR-0009 §2.4 pointing the other way. Measured, not reasoned about.

Run:  PYTHONPATH=<repo>/docs/srmech/python uv run --python 3.12 \
          --no-project --offline python notes/_rc473_atan2_origin_probe.py
"""

from __future__ import annotations

import ctypes
import json

from srmech import _native
from srmech.math import kepler, rational

_D = ctypes.c_double
_DP = ctypes.POINTER(ctypes.c_double)


def _bind(name, argtypes):
    fn = getattr(_native.LIB, name)
    fn.argtypes = argtypes
    fn.restype = ctypes.c_int
    return fn


def _outcome(fn, *a):
    try:
        return {"raised": None, "value": repr(fn(*a))}
    except Exception as exc:                       # noqa: BLE001
        return {"raised": type(exc).__name__, "text": str(exc)}


def main() -> int:
    print(json.dumps({
        "kind": "conditions", "has_native": bool(_native.HAS_NATIVE),
        "expected_abi": _native.EXPECTED_ABI_VERSION,
        "native_abi": _native.NATIVE_ABI_VERSION,
        "lib": _native.LIB._name,
        "srmech_version": __import__("srmech").__version__,
    }, sort_keys=True))

    a2 = _bind("srmech_atan2", [_D, _D, _DP])
    for y, x in [(0.0, 0.0), (-0.0, 0.0), (0.0, -0.0), (0.0, 1.0), (0.0, -1.0)]:
        out = ctypes.c_double(-12345.0)
        st = int(a2(_D(y), _D(x), ctypes.byref(out)))
        print(json.dumps({
            "kind": "atan2_origin", "y": repr(y), "x": repr(x),
            "c_status": st, "c_value": repr(out.value),
            "pure": _outcome(rational.atan2, y, x),
        }, sort_keys=True))

    ps = _bind("srmech_pin_slot", [_D, _D, _D, _DP])
    # theta=0 -> cos=1, sin=0; d = -i puts both atan2 operands at zero.
    for theta, i, d in [(0.0, 0.5, -0.5), (0.0, 1.0, -1.0), (0.0, 0.5, 0.5)]:
        out = ctypes.c_double(-12345.0)
        st = int(ps(_D(theta), _D(i), _D(d), ctypes.byref(out)))
        print(json.dumps({
            "kind": "pin_slot_origin", "theta": repr(theta), "i": i, "d": d,
            "c_status": st, "c_value": repr(out.value),
            "wrapper": _outcome(kepler.pin_slot, theta, i, d),
            "pure_body": _outcome(
                lambda t, ii, dd: float(rational.atan2(
                    ii * rational.sin(t), dd + ii * rational.cos(t))),
                theta, i, d),
        }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
