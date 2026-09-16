"""rc473 stage C (`#T1188`) — is the rc472 kepler guard's refusal SET now the
C symbol's refusal set, and does the D10 fallthrough ANSWER anywhere C refused?

Two questions the eight hand-picked rows of ``_rc473_python_guard_probe.py``
cannot settle:

  A. **Set equality.** The rc472 guard refuses when any harmonic
     ``float((k+1) * M_rad)`` is non-finite or ``|.| >= 2**55``. The C peer
     refuses when ``srmech_sin`` refuses the harmonic IT forms,
     ``(double)(k+1) * M_rad`` — a different computation for an ``int``
     ``M_rad``, which Python multiplies exactly before rounding and C rounds
     before multiplying. If the two predicates disagree on any input, deleting
     the guard changes which inputs the op serves. Swept over the boundary.

  B. **The fallthrough's own risk.** D10 routes ``SRMECH_ERR_BAD_INPUT`` to the
     pure cascade so the refusal text is one text in both cells. That is only
     sound where the pure cascade also refuses. ``kepler_solve``'s pure body
     has an ``if e == 0.0: return M_rad`` shortcut that never calls ``sin`` —
     so a fallthrough there would ANSWER what C refused, which is the ADR-0009
     §2.4 violation pointing the other way. Executed, not reasoned about.

Run:  PYTHONPATH=<repo>/docs/srmech/python uv run --python 3.12 \
          --no-project --offline python notes/_rc473_guard_set_equality.py

numpy-free. No ``hashlib``. No ``abs()``.
"""

from __future__ import annotations

import ctypes
import json
import sys
from pathlib import Path

from srmech import _native
from srmech.math import kepler, rational

NAN = float("nan")
INF = float("inf")
Q61 = rational.Q61_TRIG_RANGE          # 2.0 ** 55, imported not restated

_D = ctypes.c_double
_DP = ctypes.POINTER(ctypes.c_double)
_U32 = ctypes.c_uint32

_ROWS: list[dict] = []


def _bind(name: str, argtypes: list):
    fn = getattr(_native.LIB, name)
    fn.argtypes = argtypes
    fn.restype = ctypes.c_int
    return fn


def _guard_refuses(M_rad, n_terms: int) -> bool:
    """The rc472 guard's predicate, verbatim (magnitude = Class-K branch)."""
    for k_idx in range(n_terms):
        harmonic = float((k_idx + 1) * M_rad)
        if harmonic - harmonic != 0.0:
            return True
        if (harmonic if harmonic >= 0.0 else -harmonic) >= Q61:
            return True
    return False


def part_a_set_equality() -> dict:
    fn = _bind("srmech_equation_of_centre", [_D, _D, _U32, _DP])
    cands: list = []
    # the boundary itself, from every side, at every n_terms divisor
    for k in range(1, 7):
        base_i = int(Q61) // k
        for d in (-3, -2, -1, 0, 1, 2, 3):
            cands.append(base_i + d)                     # int spelling
            cands.append(float(base_i + d))              # float spelling
    # the 2**53 hinge (int-exact vs double-rounded diverge here)
    for d in (-2, -1, 0, 1, 2, 3):
        cands.append(2 ** 53 + d)
        cands.append(float(2 ** 53 + d))
        cands.append(-(2 ** 53 + d))
    # ordinary and pathological
    cands += [0, 0.0, -0.0, 1, 0.7, -0.7, 1e-300, 1e300, -1e300,
              NAN, INF, -INF, 2 ** 55, -(2 ** 55), 2 ** 55 - 1, 2 ** 60]
    disagreements = []
    total = 0
    for M in cands:
        for n in range(1, 7):
            total += 1
            out = ctypes.c_double(-12345.0)
            status = int(fn(_D(M), _D(0.0549), _U32(n), ctypes.byref(out)))
            c_refuses = status != _native.SRMECH_OK
            g_refuses = _guard_refuses(M, n)
            if c_refuses != g_refuses:
                disagreements.append({
                    "M": repr(M), "M_type": type(M).__name__, "n_terms": n,
                    "c_status": status, "c_value": repr(out.value),
                    "guard_refuses": g_refuses, "c_refuses": c_refuses,
                })
    row = {
        "kind": "A_set_equality",
        "candidates": len(cands),
        "calls": total,
        "disagreements": len(disagreements),
        "rows": disagreements[:20],
        "non_vacuous_guard_refusals": sum(
            1 for M in cands for n in range(1, 7) if _guard_refuses(M, n)),
        "non_vacuous_c_refusals": None,   # filled below
    }
    c_ref = 0
    for M in cands:
        for n in range(1, 7):
            out = ctypes.c_double(0.0)
            if int(fn(_D(M), _D(0.0549), _U32(n), ctypes.byref(out))) != 0:
                c_ref += 1
    row["non_vacuous_c_refusals"] = c_ref
    _ROWS.append(row)
    print(json.dumps(row, sort_keys=True))
    return row


def _pure_kepler_solve(M_rad, e, tolerance=1e-12, max_iter=30):
    """``kepler_solve``'s pure body, verbatim — the fallthrough's destination."""
    if e == 0.0:
        return M_rad
    E = M_rad + e * rational.sin(M_rad)
    for _ in range(max_iter):
        f = E - e * rational.sin(E) - M_rad
        f_prime = 1.0 - e * rational.cos(E)
        delta = f / f_prime
        E -= delta
        delta_mag = delta if delta >= 0.0 else -delta
        if delta_mag < tolerance:
            return float(E)
    raise RuntimeError("kepler_solve: did not converge")


def _pure_pin_slot(theta, i, d):
    x = d + i * rational.cos(theta)
    y = i * rational.sin(theta)
    return float(rational.atan2(y, x))


def _pure_eoc(M_rad, e, n_terms):
    delta = 0.0
    e_power = 1.0
    for k_idx in range(n_terms):
        e_power *= e
        delta += kepler._EOC_COEFFS[k_idx] * e_power * rational.sin(
            (k_idx + 1) * M_rad)
    return float(delta)


def _outcome(fn, *a):
    try:
        return {"raised": None, "value": repr(fn(*a))}
    except Exception as exc:                       # noqa: BLE001 - classifying
        return {"raised": type(exc).__name__, "text": str(exc)}


def part_b_fallthrough_risk() -> None:
    ks = _bind("srmech_kepler_solve", [_D, _D, _D, _U32, _DP])
    ps = _bind("srmech_pin_slot", [_D, _D, _D, _DP])
    eoc = _bind("srmech_equation_of_centre", [_D, _D, _U32, _DP])

    for M, e in [(NAN, 0.0), (INF, 0.0), (-INF, 0.0), (2.0 ** 55, 0.0),
                 (NAN, 0.3), (2.0 ** 55, 0.3), (0.7, 0.0), (0.7, 0.3)]:
        out = ctypes.c_double(-12345.0)
        st = int(ks(_D(M), _D(e), _D(1e-12), _U32(20), ctypes.byref(out)))
        row = {
            "kind": "B_kepler_solve_fallthrough",
            "M": repr(M), "e": e,
            "c_status": st, "c_value": repr(out.value),
            "pure_body": _outcome(_pure_kepler_solve, M, e),
        }
        row["fallthrough_answers_where_c_refused"] = bool(
            st != _native.SRMECH_OK and row["pure_body"]["raised"] is None)
        _ROWS.append(row)
        print(json.dumps(row, sort_keys=True))

    for theta, i, d in [(NAN, 0.5, 1.0), (INF, 0.5, 1.0), (2.0 ** 55, 0.5, 1.0),
                        (0.7, 0.5, 1.0), (0.7, 0.0, 0.0)]:
        out = ctypes.c_double(-12345.0)
        st = int(ps(_D(theta), _D(i), _D(d), ctypes.byref(out)))
        row = {
            "kind": "B_pin_slot_fallthrough",
            "theta": repr(theta), "i": i, "d": d,
            "c_status": st, "c_value": repr(out.value),
            "pure_body": _outcome(_pure_pin_slot, theta, i, d),
        }
        row["fallthrough_answers_where_c_refused"] = bool(
            st != _native.SRMECH_OK and row["pure_body"]["raised"] is None)
        _ROWS.append(row)
        print(json.dumps(row, sort_keys=True))

    for M, e, n in [(NAN, 0.0549, 1), (INF, 0.0549, 1), (2.0 ** 55, 0.0549, 1),
                    (2 ** 53 + 1, 0.0549, 4), (0.7, 0.0549, 4),
                    (NAN, 0.0, 1), (2.0 ** 55, 0.0, 4)]:
        out = ctypes.c_double(-12345.0)
        st = int(eoc(_D(M), _D(e), _U32(n), ctypes.byref(out)))
        row = {
            "kind": "B_eoc_fallthrough",
            "M": repr(M), "e": e, "n_terms": n,
            "c_status": st, "c_value": repr(out.value),
            "pure_body": _outcome(_pure_eoc, M, e, n),
        }
        row["fallthrough_answers_where_c_refused"] = bool(
            st != _native.SRMECH_OK and row["pure_body"]["raised"] is None)
        _ROWS.append(row)
        print(json.dumps(row, sort_keys=True))


def main() -> int:
    print(json.dumps({
        "kind": "conditions",
        "python": sys.version.split()[0],
        "has_native": bool(_native.HAS_NATIVE),
        "expected_abi": _native.EXPECTED_ABI_VERSION,
        "native_abi": getattr(_native, "NATIVE_ABI_VERSION", None),
        "lib": _native.LIB._name,
        "srmech_version": __import__("srmech").__version__,
    }, sort_keys=True))
    part_a_set_equality()
    part_b_fallthrough_risk()
    dest = Path(__file__).resolve().parent / "_rc473_guard_set_equality.ndjson"
    with dest.open("w", encoding="utf-8", newline="\n") as fh:
        for row in _ROWS:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    print(f"\nwrote {len(_ROWS)} rows -> {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
