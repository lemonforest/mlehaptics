"""`#T1130` P6 — cross-surface propagation + execution of the disagreements.

Two questions P5 raised but could not answer:

  1. Did the stale ``cyclic_gcd`` uint64 clause propagate BEYOND the docstring
     into the ToolEntry / generated / C surfaces?  A defect that is merely
     downstream of the docstring is ONE defect; a separately-authored copy is
     another.  Dumps the verbatim registry text for the affected ops.

  2. The 30-odd ToolEntry rows where the registry prose names an exception the
     callable's docstring never mentions.  ``agrees=False`` alone does not say
     WHICH side is wrong — the registry may be right and the docstring merely
     silent.  Only execution decides, so each is fired here.
"""

from __future__ import annotations

import inspect
import json
import os
import sys

REPO = "/mnt/d/GitHub/mlehaptics"
PKG = os.path.join(REPO, "docs/srmech/python")
OUT = os.path.join(REPO, "docs/srmech/notes/_p6_cross_surface_rc434.ndjson")

sys.path.insert(0, PKG)

# ops whose registry text we want verbatim (the cyclic_gcd propagation question)
VERBATIM = [
    "srmech.cascade.cyclic_gcd",
    "srmech.math.cyclic.gcd",
    "srmech.math.cyclic.lcm",
    "srmech.math.primes.factor",
]

# (tool_name, exception_the_registry_prose_claims, callable, args, kwargs, what)
DISAGREEMENTS = [
    ("srmech.math.cyclic.gcd", "ValueError", (-1, 5), {}, "negative operand"),
    ("srmech.math.cyclic.gcd", "ValueError", (2 ** 64, 5), {}, "oversize operand"),
    ("srmech.physics.qm.propagators.feynman_scalar_propagator", "ZeroDivisionError",
     (0.0, 0.0), {}, "on-shell pole"),
    ("srmech.signal_processing.cascade_dispatcher.resolve_path", "DispatchError",
     ("no_such_op_t1130",), {}, "unknown op"),
    ("srmech.signal_processing.path_registry.has_path", "UnknownOperationError",
     ("no_such_op_t1130", "A"), {}, "unknown op"),
    ("srmech.math.template.render", "ValueError", ("{missing}", {}), {},
     "missing template key"),
    ("srmech.math.rational.log", "ValueError", (0, 1, 8), {}, "log of zero"),
    ("srmech.cascade.exact_dft.exact_idft", "ValueError", ([],), {}, "empty input"),
    ("srmech.biology.genome.centromere", "ValueError", (b"",), {}, "empty genome"),
    ("srmech.biology.genome.genes", "ValueError", (b"",), {}, "empty genome"),
    ("srmech.biology.genome.kernel_pack", "ValueError", ([],), {}, "empty kernel"),
    ("srmech.biology.genome.mint_strand", "ValueError", (-1,), {}, "negative length"),
    ("srmech.cascade.cyclic_mod_mul", "ValueError", (1, 2, 0), {}, "zero modulus"),
    ("srmech.cascade.cyclic_mod_mul_wide", "ValueError", (1, 2, 0), {}, "zero modulus"),
    ("srmech.cascade.hamming_encode", "ValueError", (b"",), {}, "empty payload"),
    ("srmech.cascade.hamming_syndrome", "ValueError", (b"",), {}, "empty payload"),
    ("srmech.math.qpoly.qpoly_from_coeffs", "TypeError", ("nope",), {}, "non-sequence"),
    ("srmech.math.qbipoly.qbipoly_from_coeffs", "TypeError", ("nope",), {},
     "non-sequence"),
    ("srmech.introspect.tool_schema.tool_schema_view", "TypeError", (123,), {},
     "non-str arg"),
    ("srmech.music.normal_order", "TypeError", ("nope",), {}, "non-sequence"),
    ("srmech.physics.qm.gauge.su2_structure_constants", "ValueError", (99,), {},
     "bad index"),
    ("srmech.physics.qm.sm.higgs_vev", "ValueError", (-1.0,), {}, "negative input"),
    ("srmech.signal_processing.stft", "ValueError", ([],), {}, "empty signal"),
    ("srmech.signal_processing.cross_spectral", "ValueError", ([], []), {},
     "empty signals"),
    ("srmech.signal_processing.rfft", "ValueError", ([],), {}, "empty signal"),
    ("srmech.cascade.compose.parse_catalog_chains", "ChainSpecError", ("[[[",), {},
     "malformed spec"),
]


def resolve(dotted: str):
    parts = dotted.split(".")
    for cut in range(len(parts) - 1, 0, -1):
        try:
            mod = __import__(".".join(parts[:cut]), fromlist=["*"])
        except Exception:
            continue
        obj = mod
        try:
            for a in parts[cut:]:
                obj = getattr(obj, a)
        except AttributeError:
            continue
        return obj
    raise ImportError(dotted)


def main() -> int:
    import srmech
    from srmech import _native
    from srmech.introspect.tool_schema import get_tool_schema

    fh = open(OUT, "w", encoding="utf-8")

    def emit(rec):
        fh.write(json.dumps(rec, sort_keys=True, default=str) + "\n")
        fh.flush()
        os.fsync(fh.fileno())

    emit(
        {
            "record": "meta",
            "srmech_file": srmech.__file__,
            "srmech_version": srmech.__version__,
            "has_native": bool(_native.HAS_NATIVE),
        }
    )

    schema = get_tool_schema()
    by_name = {t.name: t for t in schema.tools}

    # ---- 1. verbatim registry text for the propagation question -----------
    for name in VERBATIM:
        t = by_name.get(name)
        rec = {"record": "verbatim", "tool": name, "in_registry": t is not None}
        if t is not None:
            rec["summary"] = t.summary
            rec["explanation"] = (t.explanation or "")[:4000]
            rec["mentions_uint64"] = "uint64" in (
                (t.summary or "") + (t.explanation or "")
            )
            rec["mentions_parity_surface"] = "parity surface" in (
                (t.summary or "") + (t.explanation or "")
            ).lower()
        try:
            fn = resolve(name)
            doc = inspect.getdoc(fn) or ""
            rec["docstring_mentions_uint64"] = "uint64" in doc
            rec["docstring_mentions_parity_surface"] = "parity surface" in doc.lower()
        except Exception as exc:
            rec["resolve_error"] = f"{type(exc).__name__}: {exc}"
        emit(rec)

    # ---- 2. execute each cross-surface disagreement ------------------------
    tally = {}
    for name, claimed, args, kwargs, what in DISAGREEMENTS:
        rec = {
            "record": "disagreement",
            "tool": name,
            "registry_claims": claimed,
            "tests": what,
        }
        try:
            fn = resolve(name)
        except Exception as exc:
            rec["outcome"] = "UNSUPPORTED"
            rec["detail"] = f"resolve: {type(exc).__name__}: {exc}"
            tally["UNSUPPORTED"] = tally.get("UNSUPPORTED", 0) + 1
            emit(rec)
            continue
        doc = inspect.getdoc(fn) or ""
        rec["docstring_mentions_claimed"] = claimed in doc
        try:
            v = fn(*args, **kwargs)
            rec["outcome"] = "NOT_RAISED"
            rec["returned_type"] = type(v).__name__
            rec["returned_repr"] = repr(v)[:160]
        except BaseException as exc:  # noqa: BLE001
            got = type(exc).__name__
            mro = [c.__name__ for c in type(exc).__mro__[:6]]
            rec.update(observed=got, mro=mro, message=str(exc)[:200])
            if got == claimed or claimed in mro:
                rec["outcome"] = "REGISTRY_RIGHT_DOCSTRING_SILENT"
            elif got in ("TypeError",) and claimed != "TypeError":
                rec["outcome"] = "PROBE_INADEQUATE_OR_TYPE_MISMATCH"
            else:
                rec["outcome"] = "TYPE_MISMATCH"
        tally[rec["outcome"]] = tally.get(rec["outcome"], 0) + 1
        emit(rec)

    emit({"record": "tally", "by_outcome": tally})
    fh.close()
    print(f"wrote {OUT}  tally={tally}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
