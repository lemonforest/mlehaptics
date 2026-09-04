"""rc430 (`#T1127`) — the FRAME census + the instrument-revision trail.
rc465 (`#T1188`) moved it here from ``docs/srmech/notes/`` and made it a
GATED artefact.

Emits ``docs/srmech/python/tests/frame_scope_census.ndjson``: one record per
registered op, plus a meta record, plus the revision trail of the instrument
itself.

WHY IT MOVED, AND WHY THAT IS A REPAIR RATHER THAN A TIDY-UP
------------------------------------------------------------
The module docstring of ``tools/frame_probe.py`` promises that the gate and the
census "cannot drift apart by being separately hand-rolled". They drifted
anyway, by a route the shared-import argument does not cover: **nobody re-ran
the census.** The committed artefact sat at the rc430 numbers
(``NO_INT_INPUT: 152``) while the ratchet's ceiling for that one class was
raised NINE times in twenty-one days — 152 → 153 → 154 → 160 → 163 → 170 → 171
→ 172 → 182 → 184 — every raise justified from an ad-hoc per-op probe recorded
in a comment rather than from a published measurement. Sharing an import
guarantees the two agree WHEN BOTH RUN; it guarantees nothing about a file.

So the artefact now lives beside the tests, in the sdist, and
``tests/test_frame_scope_rc430.py`` pins its ``meta.by_verdict`` against the
LIVE census in the same run. A stale artefact is now a red test rather than a
quiet document.

WHY THE REVISION TRAIL SHIPS
----------------------------
Five defects were found in this instrument by measuring it, and every one was
produced by the tool built to prevent that exact class. A census whose final
numbers are published without them asks to be trusted; publishing the trail
lets the numbers be JUDGED instead. Each revision below was forced by an
independent observation, never by wanting a number to move.

Run::

    PYTHONPATH=docs/srmech/python python3 docs/srmech/python/tools/frame_scope_census.py

The instrument is ``docs/srmech/python/tools/frame_probe.py`` and is SHARED
with ``tests/test_frame_scope_rc430.py`` — the gate and this census cannot
disagree by being separately hand-rolled.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# rc465: this module moved from docs/srmech/notes/ into the package
# tools dir, so the python root is one level UP, not a sibling.
PY_ROOT = Path(__file__).resolve().parents[1]
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

OUT = (Path(__file__).resolve().parents[1] / "tests"
       / "frame_scope_census.ndjson")

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
    {"rev": 8, "change": "the coordinate test ran BEFORE the reachability test",
     "forced_by": "a down-only ceiling that moved UP nine times and never down",
     "defect": "classify() decided NO_INT_INPUT at `if not coords`, which sits "
               "ABOVE the first Driver.raw({}) call. Membership was therefore a "
               "property of the harvested BINDING, not a measurement of the op. "
               "Executed at rc465: 55 of the 184 could not even bind "
               "(inspect.signature(fn).bind(**base) raises) and 2 more had a "
               "VAR_POSITIONAL the harvest dropped — 57 ops reported as having "
               "no integer input when the probe had never reached them. Seven "
               "ops the ceiling comments call MEASURED are among them.",
     "repair": "binding_gap() runs first and yields UNBOUND_REQUIRED, which "
               "names the missing parameters"},
    {"rev": 9, "change": "an int-typed parameter bound to a sentinel None was "
                         "counted as `no integer input at all`",
     "forced_by": "the same ceiling; the class-B partition of the residual",
     "defect": "13 ops DECLARE an int parameter whose default is None. The "
               "worked example legitimately omits it (measured: required=False "
               "on every one), so the harvested binding carries None where the "
               "integer would be. That is a fact about the instrument's reach, "
               "not about the op — and MEASURED at rc465 by binding a witness "
               "value, every one of the 13 reaches NOT_ADMISSIBLE, so the class "
               "was not concealing an admissible op.",
     "repair": "SENTINEL_INT_DEFAULT, a class of its own, held to the "
               "statement that makes it true rather than to a count"},
    {"rev": 10, "change": "the coordinate predicate stopped at a FLAT int list",
     "forced_by": "asking what NO_INT_INPUT means for a matrix-valued op",
     "defect": "the standing justification — a matrix is an OPERATOR, not a "
               "coordinate — is a per-op SEMANTIC claim asserted from a "
               "nesting-DEPTH test. The probe already perturbs element [0] of "
               "flat int vectors whose ints are content (zeta_mul's Z[zeta] "
               "coefficients, rc458, driven to NOT_ADMISSIBLE in 73 calls), so "
               "refusing element [0][0] was a wall at depth 2, not a rule. And "
               "one shape carries several meanings: a Cayley table, literal "
               "positions in cotangent_weights, vertex labels in edges, an "
               "operator over Q in qmat_*, residues mod p in gf_rref.",
     "repair": "translate() moves the first LEAF of a rectangular nested int "
               "list. MEASURED over the 26 ops this reaches: 24 drive to a "
               "verdict in under 0.2 s and every one is NOT_ADMISSIBLE — zero "
               "false ADMISSIBLE. The 2 expensive ones are named in SLOW_SKIP "
               "with their measured seconds AND with the verdict they reach."},
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
            "unadjudicated": "SPLIT AND HELD TO ITS REASON since rc465. "
                             "NO_ARG / BASE_RAISES / CONTRACT_SKIP / SLOW_SKIP "
                             "keep their down-only ceilings. The former "
                             "NO_INT_INPUT count is GONE: UNBOUND_REQUIRED, "
                             "SENTINEL_INT_DEFAULT and NO_INT_INPUT are each "
                             "held to a per-op predicate that can fail, so the "
                             "class cannot be enlarged by registering more "
                             "string-valued ops — which is the one thing a "
                             "count could not resist and a statement can.",
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
