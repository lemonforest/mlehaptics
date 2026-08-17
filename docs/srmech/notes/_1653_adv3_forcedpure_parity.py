#!/usr/bin/env python3
"""ADVERSARIAL: is the round-2 "48/48 byte-identical to Python" figure an
INDEPENDENT C-vs-Python check, or a same-kernel tautology? (gh #1653)

At rc444 `native_status()` reports has_native=True / dispatching=True, and the
cascade ops gate per-call on ``_native.HAS_NATIVE and _native.LIB is not None``.
So the "Python projection" the wedge harness compared against may have been
calling the very same srmech_* C kernels the bare-C harness called — in which
case byte parity on those ops proves nothing about the Python algorithm.

This script runs every declared proof case of the 11 wedge chains TWICE
through ``compose.run_chain``:
  A. as-shipped (native dispatching ON)
  B. with ``srmech._native.HAS_NATIVE`` forced False (pure-Python path)
and reports (a) where A and B differ, and (b) whether B still matches the
bare-C harness capture.  Read-only w.r.t. srmech.  No numpy, no RNG.

usage: _1653_adv3_forcedpure_parity.py <c_harness_output.txt>
"""
from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY_ROOT = os.path.abspath(os.path.join(HERE, "..", "python"))
if PY_ROOT not in sys.path:
    sys.path.insert(0, PY_ROOT)

import srmech                                    # noqa: E402
from srmech import _native as _nat               # noqa: E402
from srmech.cascade import compose as _compose    # noqa: E402
from srmech.dsl import _catalog as _cat           # noqa: E402
from srmech.dsl import _cascade_chain as _cc      # noqa: E402

WEDGE = (
    "best_rational_signed", "chiral_dual", "cyclic_gcd", "cyclic_mod_add",
    "cyclic_mod_inv", "cyclic_mod_mul", "cyclic_mod_mul_wide",
    "cyclic_mod_pow", "encode_loe_content", "magnitude", "schur_complement",
)

_C_CHAIN_RE = re.compile(r"^  == (\S+)__\d+ \(")
_C_VAL_RE = re.compile(r"^    case(\d+)\s+C_VALUE (.*)$")


def spell(v):
    if v is None:
        return "none"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return "%d" % v
    if isinstance(v, float):
        return "%.17g" % v
    if isinstance(v, (bytes, bytearray)):
        return "".join("%02x" % b for b in bytes(v))
    if isinstance(v, str):
        return "s:" + v
    if isinstance(v, (list, tuple)):
        return "[" + ",".join(spell(x) for x in v) + "]"
    shape = getattr(v, "shape", None)
    if shape is not None and len(shape) == 2:
        rows = ["[" + ",".join(spell(v[i, j]) for j in range(shape[1])) + "]"
                for i in range(shape[0])]
        return "[" + ",".join(rows) + "]"
    return "?" + type(v).__name__


def read_c(path):
    vals, cur = {}, None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        m = _C_CHAIN_RE.match(line)
        if m:
            cur = m.group(1)
            continue
        m = _C_VAL_RE.match(line)
        if m and cur:
            vals[(cur, int(m.group(1)))] = m.group(2)
    return vals


def run_all(catalog):
    """Return {(chain, case_idx): spelling} for every runnable proof case."""
    out = {}
    for name in WEDGE:
        desc = catalog[name]
        for entry in _cc._chain_entries(desc):
            chain = {
                "name": name,
                "summary": str(entry.get("summary", "")),
                "returns": str(entry.get("returns", "")),
                "on_error": "raise",
                "steps": entry.get("steps", []) or [],
            }
            spec = _compose.parse_chain_spec(chain)
            for i, case in enumerate(entry.get("proof_cases", []) or []):
                inputs = dict(case.get("inputs") or {})
                try:
                    val = _compose.run_chain(spec, inputs=inputs)
                except Exception as exc:                      # noqa: BLE001
                    out[(name, i)] = "PY_RAISE:%s" % type(exc).__name__
                    continue
                out[(name, i)] = spell(val)
    return out


def main():
    c_path = sys.argv[1] if len(sys.argv) > 1 else None
    print("srmech", srmech.__version__, srmech.native_status())
    catalog = _cat.load_catalog()
    print("native ON  ...")
    a = run_all(catalog)
    saved = _nat.HAS_NATIVE
    _nat.HAS_NATIVE = False
    print("native OFF (forced pure) ...")
    b = run_all(catalog)
    _nat.HAS_NATIVE = saved

    diffs = [k for k in sorted(a) if a[k] != b[k]]
    print()
    print("cases run:", len(a))
    print("A(native) vs B(forced-pure) DIFFERENCES:", len(diffs))
    for k in diffs:
        print("   %-24s case%-2d  native=%s" % (k[0], k[1], a[k][:70]))
        print("   %-24s          pure  =%s" % ("", b[k][:70]))

    if c_path and os.path.exists(c_path):
        cv = read_c(c_path)
        print()
        print("bare-C values parsed:", len(cv))
        mism_a = [k for k in cv if k in a and a[k] != cv[k]]
        mism_b = [k for k in cv if k in b and b[k] != cv[k]]
        print("C vs A(native)      mismatches:", len(mism_a), mism_a[:5])
        print("C vs B(forced-pure) mismatches:", len(mism_b), mism_b[:5])
        for k in mism_b:
            print("   %-24s case%-2d" % (k[0], k[1]))
            print("      C   =", cv[k][:90])
            print("      pure=", b[k][:90])
    return 0


if __name__ == "__main__":
    sys.exit(main())
