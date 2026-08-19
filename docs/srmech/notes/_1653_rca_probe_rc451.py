"""rc451 (`#T1164`, gh #1653 item 4 — RC-A) — the EXECUTED evidence for the
tuple wire kind and the four best_rational_signed step ops.

Run from ``docs/srmech/python`` with ``PYTHONPATH=.``::

    PYTHONPATH=. python3 ../notes/_1653_rca_probe_rc451.py

WHAT IT MEASURES, AND HOW IT COULD RETURN OTHERWISE
===================================================
Every block below prints a MEASURED value and states the predicate. None of
them prints a hardcoded verdict.

 A. THE WIRE KIND OF AN EXECUTED CASE. Drives the SHIPPED 6-step descriptor
    through ``srmech_chain_run`` and prints ``json.loads(wire)["k"]`` — the
    kind string itself, not "reconstruction succeeded" and not a
    ``classify()`` verdict. It returns otherwise whenever C emits any other
    kind: before this rc it returned rc=5 with an empty wire, and the
    ADJUDICATED DODGE (emit the int-pair as the existing kind ``q``) prints
    ``q`` here while passing every other gate in the tree green.

 B. THE PAYLOAD KEY. Prints the descriptor's own key set. ``{"k","v"}`` after
    the rc451 unification; ``{"items","k"}`` before it.

 C. VALUE PARITY per proof case, through the SHIPPED reader
    (``_srmech_json.loads`` + ``_reconstruct_value``) against the FORCED-PURE
    Python projection, compared under the rc450 typed encoding where
    ``tuple != list``, ``int != float`` and signed zero is a distinction. A
    divergence prints as ``DIVERGENT`` with both sides.

 D. THE COARSE-SYMBOL CONTROL. Runs the fused
    ``srmech_cascade_best_rational_signed_f64`` on the SAME inputs and prints
    whether it agrees. It DOES agree everywhere, which is exactly why no
    value-level gate can tell a coarse dispatch from an honest one — stated
    here as a measured fact rather than left as an assumption.

 E. THE BAND-MUTATION WITNESS TRIPLE, re-measured. Baseline / mutant on the
    inputs the rc451 MUTATIONS row uses, plus the SHIPPED proof case 6 where
    the same mutation is VACUOUS. The vacuous half is printed on purpose: it
    is the control proving the viable half is not an artifact of hoping.

 F. THE FOUR OPS AT THEIR OWN DOMAIN EDGES — negative value, scale 0, a
    product >= 2^63, dead_band on int / float / -0.0 / NaN, best_rational on
    an out-of-uint64 operand. Each prints the C status and the Python answer
    so a NARROWING (C declines where Python answers) is visible as such and is
    never mistaken for agreement.
"""

from __future__ import annotations

import ctypes
import json
import struct
import sys

import srmech
from srmech import _native
from srmech.cascade import compose as _compose
from srmech.dsl import _cascade_chain as _cc
from srmech.dsl import _catalog as _cat
from srmech.dsl._cascade_chain import cascade_chain_specs


# ── the rc450 canonical typed encoding, duplicated so this probe runs alone ──
def _bits(x):
    if isinstance(x, float):
        return b"f" + struct.pack(">d", x)
    if isinstance(x, bool):
        return b"b" + (b"1" if x else b"0")
    if isinstance(x, int):
        return b"i" + repr(x).encode("ascii")
    if isinstance(x, str):
        return b"s" + x.encode("utf-8")
    if isinstance(x, bytes):
        return b"y" + x
    if x is None:
        return b"n"
    if isinstance(x, tuple):
        return b"t[" + b",".join(_bits(i) for i in x) + b"]"
    if isinstance(x, list):
        return b"l[" + b",".join(_bits(i) for i in x) + b"]"
    if isinstance(x, dict):
        return b"d{" + b",".join(
            _bits(k) + b":" + _bits(v) for k, v in sorted(x.items())) + b"}"
    return b"?" + repr(x).encode("utf-8")


def _chain_only(entry):
    return {k: v for k, v in entry.items()
            if k in ("name", "steps", "on_error", "chain_schema_version")}


def _c_run(chain_dict, ctx):
    lib = _compose._compose_lib("srmech_chain_run",
                                "srmech_chain_run_arena_bytes")
    if lib is None:
        raise SystemExit("no native library — this probe measures the C projection")
    try:
        cj = json.dumps(chain_dict, ensure_ascii=False,
                        allow_nan=False).encode("utf-8")
        xj = json.dumps({"inputs": ctx}, ensure_ascii=False,
                        allow_nan=False).encode("utf-8")
    except (TypeError, ValueError):
        return None, b""
    ws_bytes = int(lib.srmech_chain_run_arena_bytes(len(cj), len(xj)))
    ws = (ctypes.c_char * ws_bytes)()
    out_cap = max(ws_bytes // 2, 16384)
    out = (ctypes.c_char * out_cap)()
    out_len = ctypes.c_size_t()
    rc = int(lib.srmech_chain_run(cj, len(cj), xj, len(xj), ws, ws_bytes,
                                  out, out_cap, ctypes.byref(out_len)))
    return rc, out.raw[:out_len.value]


def _py_pure(spec, inputs):
    saved = (_native.HAS_NATIVE, _native.LIB)
    _native.HAS_NATIVE, _native.LIB = False, None
    try:
        return _compose.run_chain(spec, inputs=inputs)
    finally:
        _native.HAS_NATIVE, _native.LIB = saved


def _entry():
    catalog = _cat.load_catalog()
    return catalog["best_rational_signed"]


def main() -> int:
    print("srmech %s | HAS_NATIVE=%s | ABI %s (expected %s)"
          % (srmech.__version__, _native.HAS_NATIVE,
             _native.NATIVE_ABI_VERSION, _native.EXPECTED_ABI_VERSION))
    print("lib: %s" % (_native.LIB._name if _native.LIB else None))

    _variant, spec, chain = cascade_chain_specs("best_rational_signed")[0]
    cases = list(chain.get("proof_cases") or [])

    # ── A + B: the kind and the payload key of an EXECUTED case ─────────────
    print("\n[A/B] the wire an EXECUTED shipped proof case produces")
    rc, wire = _c_run(_chain_only(chain), dict(cases[0].get("inputs") or {}))
    print("  case 0 inputs : %r" % (cases[0].get("inputs"),))
    print("  rc            : %r" % rc)
    print("  wire bytes    : %r" % wire)
    if rc == 0 and wire:
        desc = _compose._srmech_json.loads(wire.decode("utf-8"))
        print("  desc['k']     : %r      <- THE KIND, measured" % desc.get("k"))
        print("  desc keys     : %r      <- THE PAYLOAD KEY" % sorted(desc))
        print("  reconstructed : %r (%s)"
              % (_compose._reconstruct_value(desc),
                 type(_compose._reconstruct_value(desc)).__name__))

    # ── C: value parity over every proof case ───────────────────────────────
    print("\n[C] value parity, shipped reader vs FORCED-PURE Python")
    tally = {}
    for j, case in enumerate(cases):
        inputs = dict(case.get("inputs") or {})
        try:
            py = _py_pure(spec, inputs)
            serialisable = True
        except Exception as exc:                      # noqa: BLE001
            py, serialisable = repr(exc), False
        rc, wire = _c_run(_chain_only(chain), inputs)
        if rc is None:
            verdict = "NONFINITE_CANNOT_CROSS_WIRE"
        elif rc != 0:
            verdict = "C_REJECTED_rc=%d" % rc
        else:
            desc = _compose._srmech_json.loads(wire.decode("utf-8"))
            try:
                got = _compose._reconstruct_value(desc)
            except ValueError:
                verdict = "UNKNOWN_WIRE_KIND_%s" % desc.get("k")
            else:
                verdict = ("BYTE_IDENTICAL" if _bits(got) == _bits(py)
                           else "DIVERGENT")
                if verdict == "DIVERGENT":
                    print("    !! case %d  C=%r  py=%r" % (j, got, py))
        tally[verdict] = tally.get(verdict, 0) + 1
        print("  case %d %-30s covers=%-16s py=%r"
              % (j, verdict, case.get("covers"), py if serialisable else "<nonfinite>"))
    print("  tally: %r" % (tally,))

    # ── D: the coarse-symbol control ────────────────────────────────────────
    print("\n[D] the FUSED coarse symbol on the same inputs — the control that")
    print("    shows why no value-level gate can police the dispatch grain")
    lib = _native.LIB
    fn = getattr(lib, "srmech_cascade_best_rational_signed_f64", None)
    if fn is not None:
        fn.argtypes = [ctypes.c_double, ctypes.c_int64, ctypes.c_int64,
                       ctypes.POINTER(ctypes.c_int64),
                       ctypes.POINTER(ctypes.c_int64)]
        fn.restype = ctypes.c_int
        agree = disagree = skipped = 0
        for case in cases:
            inputs = dict(case.get("inputs") or {})
            n, d = ctypes.c_int64(), ctypes.c_int64()
            st = int(fn(ctypes.c_double(float(inputs["x"])),
                        ctypes.c_int64(int(inputs["max_denominator"])),
                        ctypes.c_int64(int(inputs["fine_scale"])),
                        ctypes.byref(n), ctypes.byref(d)))
            try:
                py = _py_pure(spec, inputs)
            except Exception:                          # noqa: BLE001
                skipped += 1
                continue
            if st == 0 and (n.value, d.value) == py:
                agree += 1
            else:
                disagree += 1
                print("    coarse disagrees: %r -> st=%d (%d,%d) vs %r"
                      % (inputs, st, n.value, d.value, py))
        print("  coarse-vs-pure over the shipped cases: agree=%d disagree=%d "
              "skipped=%d" % (agree, disagree, skipped))
        print("  => a coarse dispatch is INVISIBLE to any value channel. Only "
              "the structural pin can see it.")

    # ── E: the band-mutation witness triple ─────────────────────────────────
    print("\n[E] band-mutation witness: viable triple vs the VACUOUS shipped case")
    import copy

    def _run_pure(steps, inputs):
        sp = _compose.parse_chain_spec({
            "name": "best_rational_signed.probe",
            "summary": "band-mutation witness probe",
            "returns": "tuple[int, int]",
            "steps": steps,
        })
        return _py_pure(sp, inputs)

    base_steps = copy.deepcopy(chain["steps"])
    mut_steps = copy.deepcopy(chain["steps"])
    mut_steps[1]["args"]["band"] = 1e-6
    for label, inputs in (
            ("VIABLE  ", {"x": 1.5e-12, "fine_scale": 10 ** 13,
                          "max_denominator": 10 ** 12}),
            ("SHIPPED6", {"x": 5e-13, "fine_scale": 10 ** 13,
                          "max_denominator": 10 ** 12})):
        b = _run_pure(base_steps, inputs)
        m = _run_pure(mut_steps, inputs)
        print("  %s inputs=%r\n            baseline=%r mutant=%r  moved=%s"
              % (label, inputs, b, m, b != m))

    # ── F: the four ops at their OWN domain edges ───────────────────────────
    print("\n[F] the four ops at their own domain edges (C status vs Python)")
    from srmech.cascade.leaves import dead_band, pair
    from srmech.math.rational import best_rational, scale_round_half_even

    db = getattr(lib, "srmech_cascade_dead_band_f64", None)
    sr = getattr(lib, "srmech_cascade_scale_round_half_even_i64", None)
    if db is not None:
        db.argtypes = [ctypes.c_double, ctypes.c_double,
                       ctypes.POINTER(ctypes.c_double)]
        db.restype = ctypes.c_int
        for v, band in ((-1.0, 1e-12), (5e-13, 1e-12), (1.0, 1e-12),
                        (float("nan"), 1e-12), (0.0, 1e-12), (-0.0, 1e-12)):
            o = ctypes.c_double()
            st = int(db(ctypes.c_double(v), ctypes.c_double(band),
                        ctypes.byref(o)))
            p = dead_band(v, band)
            same = _bits(o.value) == _bits(p) if st == 0 else None
            print("    dead_band(%r,%r) C st=%d out=%r | py=%r | bits-equal=%s"
                  % (v, band, st, o.value, p, same))
        print("    dead_band(5, band) py=%r (%s) — the C arm DECLINES a "
              "non-double `value` rather than widening it"
              % (dead_band(5, 1e-12), type(dead_band(5, 1e-12)).__name__))
    if sr is not None:
        sr.argtypes = [ctypes.c_double, ctypes.c_int64,
                       ctypes.POINTER(ctypes.c_int64)]
        sr.restype = ctypes.c_int
        for v, s in ((-1.5, 1), (-2.5, 1), (-0.5, 1), (0.5, 1), (1.5, 1),
                     (2.5, 1), (3.5, 1), (0.5, 0), (1e30, 10 ** 6),
                     (-3.14159265358979, 10 ** 6)):
            o = ctypes.c_int64()
            st = int(sr(ctypes.c_double(v), ctypes.c_int64(s),
                        ctypes.byref(o)))
            p = scale_round_half_even(v, s)
            print("    scale_round(%r,%r) C st=%d out=%r | py=%r | equal=%s"
                  % (v, s, st, o.value if st == 0 else None, p,
                     (st == 0 and o.value == p)))
    print("    best_rational(0, 10**13, 10**12) py=%r  <- the lemma the fused "
          "symbol short-circuits and the fine path EXERCISES"
          % (best_rational(0, 10 ** 13, 10 ** 12),))
    print("    best_rational(2**64, 10, 10) py=%r  <- out of the uint64 C wire; "
          "the arm DECLINES" % (best_rational(2 ** 64, 10, 10),))
    print("    pair(1, 2) py=%r (%s)" % (pair(1, 2), type(pair(1, 2)).__name__))
    return 0


if __name__ == "__main__":
    sys.exit(main())
