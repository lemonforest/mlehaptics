"""`#T1130` P5 — the OTHER surfaces, the omission direction, and the overlap.

Four measurements:

  A. ``common_period`` refined — P4's "inharmonic" probe was INADEQUATE (the
     input ``[(1,1),(3,2),(7,5)]`` is HARMONIC, so the guard correctly did not
     fire).  Reached properly here with a ``Qalg`` irrational, plus the
     undeclared ``OverflowError`` its Class-I ``lcm`` fold can raise.

  B. The ToolEntry / registry surface.  ``ToolEntry`` carries NO ``raises``
     field, so any exception declaration there lives inside ``summary`` /
     ``explanation`` prose.  Measured: which registered tools name an exception
     in prose, and whether the underlying callable's docstring agrees.

  C. ENFORCED-NOT-DECLARED restricted to the surface that actually ships to
     users — the registered tools reachable through ``describe()`` / MCP —
     rather than every function in the tree.

  D. Re-derivation of the ``#T1131`` overlap claim (filed: 17 ops, 0 overlap,
     classified EMPTY).  Re-measured with THIS instrument, not inherited.

Pre-registered falsifiers:
  F3  #T1131's 17 ops carry zero ``Raises:`` blocks -> falsified if any does
  F5  no ToolEntry prose names an exception          -> falsified if any does
  F6  common_period enforces its inharmonic clause   -> falsified if it returns
"""

from __future__ import annotations

import inspect
import json
import os
import sys

REPO = "/mnt/d/GitHub/mlehaptics"
PKG = os.path.join(REPO, "docs/srmech/python")
OUT = os.path.join(REPO, "docs/srmech/notes/_p5_surfaces_and_overlap_rc434.ndjson")

sys.path.insert(0, PKG)

sys.path.insert(0, os.path.join(REPO, "docs/srmech/notes"))
from _p1_declared_vs_enforced_rc434 import (  # noqa: E402
    looks_like_exception,
    parse_prose_exceptions,
    parse_raises_block,
)

# The 17 ops the #T1131 scope measured.  Copied as DATA so the re-derivation
# is over the same population, but every verdict below is recomputed here.
T1131_OPS = [
    "srmech.physics.qm.bell.operator_norm",
    "srmech.dsl._catalog.register_catalog_dir",
    "srmech.math.hdc.loop_bind_hd",
    "srmech.math.hdc.loop_unbind_hd",
    "srmech.math.hdc.loop_conj_hd",
    "srmech.math.hdc.loop_inv_hd",
    "srmech.math.hdc.loop_runbind_hd",
    "srmech.math.mat.Mat.from_rows",
    "srmech.math.laplacian.mat_matmul",
    "srmech.math.vec.Vec.__getitem__",
    "srmech.biology.genome._q8_couple",
    "srmech.biology.genome._oct_couple",
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
            for attr in parts[cut:]:
                obj = getattr(obj, attr)
        except AttributeError:
            continue
        return obj
    raise ImportError(dotted)


def main() -> int:
    import srmech
    from srmech import _native

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
            "python": sys.version.split()[0],
        }
    )

    def probe(pid, declared, fn, *a, **k):
        rec = {"record": "probe", "probe_id": pid, "declared": declared}
        try:
            v = fn(*a, **k)
            rec["outcome"] = "NOT_ENFORCED"
            rec["returned_repr"] = repr(v)[:200]
            rec["returned_type"] = type(v).__name__
        except BaseException as exc:  # noqa: BLE001
            got = type(exc).__name__
            mro = [c.__name__ for c in type(exc).__mro__[:6]]
            rec.update(observed=got, mro=mro, message=str(exc)[:240])
            rec["outcome"] = (
                "ENFORCED" if (got == declared or declared in mro) else "TYPE_MISMATCH"
            )
        emit(rec)
        return rec

    # ================================================== A. common_period redux
    from srmech.math.qalg import Qalg
    from srmech.music._spectra import common_period, spectrum_tier

    # sqrt(2) as an element of Q[x]/(x^2 - 2): coords (0, 1)
    try:
        sqrt2 = Qalg((-2, 0, 1), (0, 1))
        emit(
            {
                "record": "note",
                "detail": "built Qalg sqrt(2)",
                "is_rational": bool(sqrt2.is_rational()),
                "degree": int(sqrt2.degree),
            }
        )
        emit(
            {
                "record": "note",
                "detail": "spectrum_tier on the irrational spectrum",
                "tier": str(spectrum_tier([1, sqrt2]))[:300],
            }
        )
        probe("common_period/inharmonic-REAL", "ValueError", common_period, [1, sqrt2])
    except Exception as exc:
        emit(
            {
                "record": "probe",
                "probe_id": "common_period/inharmonic-REAL",
                "outcome": "UNSUPPORTED",
                "detail": f"{type(exc).__name__}: {exc}",
            }
        )

    probe("common_period/open-REAL", "ValueError", common_period,
          [(1, 1), (2, 1)], open_partials=(0,))

    # the UNDECLARED OverflowError: lcm of the reduced denominators can exceed
    # the Class-I parity surface even though every partial is harmonic.
    big = [(1, 1)] + [(1, p) for p in (
        2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61,
        67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113,
    )]
    probe("common_period/OVERFLOW-undeclared", "OverflowError", common_period, big)

    # ============================================ B/C. ToolEntry + registry
    try:
        from srmech.introspect.tool_schema import get_tool_schema

        schema = get_tool_schema()
        tools = list(schema.tools)
    except Exception as exc:
        tools = []
        emit({"record": "note", "detail": f"tool schema unavailable: {exc!r}"})

    emit({"record": "registry_meta", "n_tools": len(tools)})

    prose_hits = 0
    for t in tools:
        blob = " ".join(
            str(x) for x in (t.summary, t.explanation or "") if x is not None
        )
        exc_names = [n for n in parse_prose_exceptions(blob)]
        if not exc_names:
            continue
        prose_hits += 1
        rec = {
            "record": "toolentry_prose",
            "tool": t.name,
            "exceptions_in_prose": exc_names,
            "in_summary": [n for n in parse_prose_exceptions(t.summary or "")],
            "in_explanation": [n for n in parse_prose_exceptions(t.explanation or "")],
        }
        try:
            fn = resolve(t.name)
            doc = inspect.getdoc(fn) or ""
            rec["callable_declared_block"] = parse_raises_block(doc)
            rec["callable_prose"] = parse_prose_exceptions(doc)
            rec["agrees_with_docstring"] = bool(
                set(exc_names) & (set(rec["callable_declared_block"]) | set(rec["callable_prose"]))
            )
            rec["resolved"] = True
        except Exception as exc:
            rec["resolved"] = False
            rec["resolve_error"] = f"{type(exc).__name__}: {exc}"
        emit(rec)

    emit({"record": "toolentry_summary", "n_tools_naming_an_exception": prose_hits})

    # C. omission direction on the SHIPPED surface only
    omission = []
    for t in tools:
        try:
            fn = resolve(t.name)
        except Exception:
            continue
        doc = inspect.getdoc(fn) or ""
        declared = set(parse_raises_block(doc)) | set(parse_prose_exceptions(doc))
        try:
            src = inspect.getsource(fn)
        except Exception:
            continue
        body_excs = set()
        for line in src.splitlines():
            s = line.strip()
            if s.startswith("raise "):
                tok = s[len("raise ") :].split("(")[0].split()[0].strip()
                tok = tok.rsplit(".", 1)[-1]
                if looks_like_exception(tok):
                    body_excs.add(tok)
        undeclared = sorted(body_excs - declared)
        if undeclared:
            omission.append((t.name, undeclared, sorted(declared)))
    for name, und, dec in omission:
        emit(
            {
                "record": "registry_omission",
                "tool": name,
                "raises_undeclared": und,
                "declared": dec,
            }
        )
    emit(
        {
            "record": "registry_omission_summary",
            "n_registered_tools": len(tools),
            "n_with_undeclared_own_body_raise": len(omission),
        }
    )

    # ==================================================== D. #T1131 overlap
    overlap = 0
    for dotted in T1131_OPS:
        rec = {"record": "t1131_overlap", "op": dotted}
        try:
            fn = resolve(dotted)
            doc = inspect.getdoc(fn) or ""
            blk = parse_raises_block(doc)
            prose = parse_prose_exceptions(doc)
            rec.update(
                resolved=True,
                has_raises_block=bool(blk),
                declared_block=blk,
                prose_exceptions=prose,
                overlaps_t1130=bool(blk),
            )
            if blk:
                overlap += 1
        except Exception as exc:
            rec.update(resolved=False, error=f"{type(exc).__name__}: {exc}")
        emit(rec)
    emit(
        {
            "record": "t1131_overlap_summary",
            "n_ops_checked": len(T1131_OPS),
            "n_with_raises_block": overlap,
            "classification": "EMPTY" if overlap == 0 else "NON-EMPTY",
        }
    )

    fh.close()
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
