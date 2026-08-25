"""rc452 (`#T1166`) — EXECUTES the C acceptance contract instead of trusting it.

The ruling asserts "cr_as_rational already accepts a rational OR a 2-int list".
The build brief's standing order is to confirm that BY EXECUTION rather than by
trusting the sentence. This probe drives the REAL shipped ``srmech_chain_run``
through both arms and prints the wire bytes.

Run from ``docs/srmech/python`` with ``PYTHONPATH=.``.
"""
import ctypes
import json

from srmech.cascade import compose as _compose
from srmech import _native

print("native:", _native.HAS_NATIVE, _native.NATIVE_ABI_VERSION,
      _native.EXPECTED_ABI_VERSION, _native.LOAD_ERROR)


def c_run(chain, ctx):
    lib = _compose._compose_lib("srmech_chain_run", "srmech_chain_run_arena_bytes")
    assert lib is not None, "chain-run symbols absent — not a skip, a failure"
    cj = json.dumps(chain, ensure_ascii=False, allow_nan=False).encode()
    xj = json.dumps({"inputs": ctx}, ensure_ascii=False, allow_nan=False).encode()
    n = int(lib.srmech_chain_run_arena_bytes(len(cj), len(xj)))
    ws = (ctypes.c_char * n)()
    cap = max(n // 2, 16384)
    out = (ctypes.c_char * cap)()
    ol = ctypes.c_size_t()
    rc = int(lib.srmech_chain_run(cj, len(cj), xj, len(xj), ws, n, out, cap,
                                  ctypes.byref(ol)))
    return rc, out.raw[:ol.value]


def chain(steps, returns="last"):
    return {"name": "probe", "summary": "", "returns": returns,
            "on_error": "raise", "steps": steps}


RA = "srmech.math.rational.rational_add"
RE = "srmech.cascade.reorient"
RP = "srmech.math.rational.rational_pow_uint"

CASES = [
    ("ARM 1  cr_as_rational CR_LIST arm ([num,den] literal operands)",
     chain([{"class": "N", "op": RA, "args": {"a": [1, 2], "b": [1, 3]}}]), {}),
    ("ARM 2  cr_as_rational CR_RATIONAL arm (@step ref: the op eats its own output)",
     chain([{"class": "N", "op": RA, "args": {"a": [1, 2], "b": [1, 3]}},
            {"class": "N", "op": RA, "args": {"a": "@step[0].output", "b": [0, 1]}}]), {}),
    ("ARM 3  THE HEADLINE  rational_add -> reorient(orientation=-1)",
     chain([{"class": "N", "op": RA, "args": {"a": [1, 2], "b": [1, 3]}},
            {"class": "C", "op": RE,
             "args": {"value": "@step[0].output", "orientation": -1}}]), {}),
    ("ARM 4  reorient on a [num,den] LIST literal (surviving ADJ-4 input spelling)",
     chain([{"class": "C", "op": RE, "args": {"value": [5, 6], "orientation": -1}}]), {}),
    ("ARM 5  reorient on a plain int (the shipped, working case)",
     chain([{"class": "C", "op": RE, "args": {"value": 7, "orientation": -1}}]), {}),
    ("ARM 6  pow base as CR_RATIONAL via @step ref",
     chain([{"class": "N", "op": RA, "args": {"a": [1, 2], "b": [1, 3]}},
            {"class": "N", "op": RP, "args": {"base": "@step[0].output", "exp": 2}}]), {}),
    ("ARM 7  FRESH-CARRIER REGRESSION  step2 re-reads step0 AFTER step1 negated it",
     chain([{"class": "N", "op": RA, "args": {"a": [1, 2], "b": [1, 3]}},
            {"class": "C", "op": RE,
             "args": {"value": "@step[0].output", "orientation": -1}},
            {"class": "N", "op": RA,
             "args": {"a": "@step[0].output", "b": [0, 1]}}]), {}),
]

for label, ch, ctx in CASES:
    rc, wire = c_run(ch, ctx)
    print("\n-- %s\n   rc=%d wire=%r" % (label, rc, wire))
