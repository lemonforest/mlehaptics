"""rc430 (`#T1127`) — the FRAME census + the instrument-revision trail.

Emits ``_frame_scope_census_rc430.ndjson``: one record per registered op, plus
a meta record, plus the revision trail of the instrument itself.

WHY THE REVISION TRAIL SHIPS
----------------------------
Five defects were found in this instrument by measuring it, and every one was
produced by the tool built to prevent that exact class. A census whose final
numbers are published without them asks to be trusted; publishing the trail
lets the numbers be JUDGED instead. Each revision below was forced by an
independent observation, never by wanting a number to move.

Run::

    PYTHONPATH=docs/srmech/python python3 docs/srmech/notes/_frame_scope_census_rc430.py

The instrument is ``docs/srmech/python/tools/frame_probe.py`` and is SHARED
with ``tests/test_frame_scope_rc430.py`` — the gate and this census cannot
disagree by being separately hand-rolled.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

PY_ROOT = Path(__file__).resolve().parents[1] / "python"
for _p in (str(PY_ROOT), str(PY_ROOT / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import example_args as ea          # noqa: E402
import frame_probe as fp           # noqa: E402

import srmech                       # noqa: E402
from srmech.cascade import cyclic_mod_add  # noqa: E402
from srmech.introspect.tool_schema import (  # noqa: E402
    get_tool_schema, warmup_all)
from srmech.math.cyclic import mod_mul  # noqa: E402
from srmech.math.primes import is_prime  # noqa: E402

OUT = Path(__file__).with_suffix(".ndjson")

#: Every revision this instrument went through, and what FORCED it.
INSTRUMENT_REVISIONS = [
    {"rev": 1, "change": "six-point offset sample",
     "forced_by": "initial draft",
     "defect": "srmech.math.primes.is_prime classified fixed period 6 — a "
               "coincidence over six draws. Would have shipped a false "
               "declaration on a real op.",
     "repair": "dense contiguous sweep (R=72) + MIN_CONFIRMATIONS floor; "
               "structural, not a bigger sample"},
    {"rev": 2, "change": "uncached parametric branch",
     "forced_by": "a whole-registry run that did not finish",
     "defect": "the constant-period check recomputed each (coord, modulus) "
               "sequence per candidate period",
     "repair": "Driver sequence cache + a cheap 24-point rejection screen "
               "that can only REJECT, so it removes runtime and never verdicts"},
    {"rev": 3, "change": "first difference computed over the integers",
     "forced_by": "the LEAK_B negative control passing as CLEAN",
     "defect": "LEAK_B welds in generator 7 but its differences over Z are "
               "7, 7, -5, 7, ... — every wraparound breaks constancy, so the "
               "generator clause returned None. This REPRODUCES the rc426 F12b "
               "blind spot the axis exists to narrow.",
     "repair": "reduce the first difference mod the frame"},
    {"rev": 4, "change": "carry-check compared scalar parameters only",
     "forced_by": "crt_combine classified fixed, period 5",
     "defect": "the period was supplied by moduli[0]; a sequence ELEMENT can "
               "carry it. False `fixed` on a shipped op.",
     "repair": "_carries inspects sequence elements, and compares up to "
               "congruence mod the frame (mod_mul(a=19, n=12) advances by 7 "
               "and no parameter equals 7)"},
    {"rev": 5, "change": "generator accepted any non-1 constant difference",
     "forced_by": "mod_mul reporting generator: 0",
     "defect": "0 means the op is CONSTANT along the coordinate at that "
               "frame — degeneracy, not an affine step",
     "repair": "reject 0 and 1; reject any generator a parameter supplies"},
    {"rev": 6, "change": "no measured-slow list",
     "forced_by": "a census run of 22 minutes, 1332 s of it in one op",
     "defect": "recover_check costs 1332 s in 50 calls; the ops are expensive "
               "per CALL, so a call budget would not have helped",
     "repair": "SLOW_SKIP — a NAMED list with a measured number per entry, "
               "the discipline run_worked_examples already applies. A "
               "wall-clock cutoff would make a verdict depend on the machine."},
    {"rev": 7, "change": "path parameters were harvested",
     "forced_by": "the ratchet itself: BASE_RAISES 56 on one run, 55 on the next",
     "defect": "fiedler_sparse_file harvested path='/tmp/.../codon.graph', a "
               "file its own snippet created. A census that answers "
               "differently on the same tree is not a measurement.",
     "repair": "a harvested argument must be REPRODUCIBLE; path params are "
               "never harvested, and the sandbox tier serves them uniformly"},
]


def _leak_a(x, y):
    return cyclic_mod_add(x, y, 12)


def _leak_b(x, y, n):
    return mod_mul(7, cyclic_mod_add(x, y, n), n)


def _clean(x, y, n, g):
    return mod_mul(g, cyclic_mod_add(x, y, n), n)


def main() -> int:
    print(f"srmech.__file__    = {srmech.__file__}")
    print(f"srmech.__version__ = {srmech.__version__}")
    warmup_all()
    tools = get_tool_schema().tools
    rows = ea.load_ledger()

    records = [{"record": "instrument_revisions", "revisions": INSTRUMENT_REVISIONS}]

    # ── preconditions: the instrument answers the known cases ─────────
    pre = {
        "record": "precondition",
        "is_prime_least_period": fp.least_period(
            [fp.okey(is_prime(101 + d)) for d in range(fp.R)])[0],
        "leak_a": fp.classify("LEAK_A", {"x": 0, "y": 3}, _leak_a),
        "leak_b": fp.classify("LEAK_B", {"x": 0, "y": 3, "n": 11}, _leak_b),
        "clean": fp.classify("CLEAN", {"x": 0, "y": 3, "n": 11, "g": 3}, _clean),
        "constant_fn": fp.classify("CONST", {"x": 0}, lambda x: 7),
    }
    # An instrument that cannot return otherwise is not a measurement: assert
    # the controls SEPARATE before publishing anything downstream of them.
    assert pre["is_prime_least_period"] is None, pre
    assert fp.declared_scope(pre["leak_a"]["findings"]) == "fixed", pre
    assert fp.declared_scope(pre["leak_b"]["findings"]) == "parametric", pre
    assert {f.get("generator") for f in pre["leak_b"]["findings"]} == {7}, pre
    assert pre["constant_fn"]["verdict"] == "NOT_ADMISSIBLE", pre
    pre["instrument_valid"] = True
    records.append(pre)

    # ── the census ────────────────────────────────────────────────────
    t0 = time.monotonic()
    by_verdict = {}
    declared_live = {}
    for entry in tools:
        rec = fp.probe_from_ledger(entry.name, rows)
        rec["record"] = "op"
        rec["declared_scope"] = entry.frame_scope
        rec["declared_axis"] = list(entry.frame_axis)
        rec["measured_scope"] = fp.declared_scope(rec.get("findings") or [])
        rec["measured_axis"] = list(fp.declared_axis(rec.get("findings") or []))
        rec["agrees"] = (rec["declared_scope"] == rec["measured_scope"]
                         and tuple(rec["declared_axis"]) == tuple(rec["measured_axis"]))
        by_verdict[rec["verdict"]] = by_verdict.get(rec["verdict"], 0) + 1
        if entry.frame_scope is not None:
            declared_live[entry.name] = entry.frame_scope
        records.append(rec)
    elapsed = time.monotonic() - t0

    disagree = [r["op"] for r in records
                if r.get("record") == "op" and not r.get("agrees", True)]
    admissible = {r["op"] for r in records
                  if r.get("record") == "op" and r["verdict"] == "ADMISSIBLE"}

    meta = {
        "record": "meta",
        "srmech_version": srmech.__version__,
        "registry_total": len(tools),
        "census_seconds": round(elapsed, 1),
        "by_verdict": dict(sorted(by_verdict.items())),
        "admissible": len(admissible),
        "declared": len(declared_live),
        "declared_minus_admissible": sorted(set(declared_live) - admissible),
        "admissible_minus_declared": sorted(admissible - set(declared_live)),
        "disagreements": disagree,
        "generator_axis_declarers": sorted(
            n for n, e in ((t.name, t) for t in tools)
            if e.frame_scope is not None and "generator" in e.frame_axis),
        # NULL CLASSIFICATION, mandatory on every measurement.
        "null_classification": {
            "generator_axis": "EMPTY — the axis is decidable and exercised by "
                              "the LEAK_B control, and zero SHIPPED ops "
                              "declare it because every generator the census "
                              "found is supplied by a parameter. Not ABSENT.",
            "non_affine_generator": "UNSUPPORTED — undecidable by this "
                                    "instrument; counted in the residual, not "
                                    "reported as clean.",
            "unadjudicated": "BOUNDED — NO_ARG / NO_INT_INPUT / BASE_RAISES / "
                             "SLOW_SKIP are counted under a down-only ceiling, "
                             "never folded into a passing class.",
        },
        "R": fp.R, "MMAX": fp.MMAX, "MIN_CONFIRMATIONS": fp.MIN_CONFIRMATIONS,
        "NS": list(fp.NS), "slow_skipped": sorted(fp.SLOW_SKIP),
    }
    records.insert(0, meta)

    OUT.write_text(
        "\n".join(json.dumps(r, sort_keys=True, default=str) for r in records)
        + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(meta, sort_keys=True, indent=1, default=str))
    print(f"wrote {OUT}")
    return 0 if not disagree else 1


if __name__ == "__main__":
    raise SystemExit(main())
