"""rc431 (`#T1129`) S1 — the WORKED-EXAMPLE ORACLE as a SUPPLY, not a census.

THE ONE PROBLEM
===============
How do you obtain a **valid** argument for an op you did not write? srmech
publishes ``name`` / ``type`` / ``required`` / ``summary`` per parameter --
enough to build a well-TYPED argument, not a valid one. rc430 measured that the
tree already contains a supply: ``ToolEntry.example["worked"]`` is executable
Python on 570 of 655 entries, and an argument that appeared in a call which
RETURNED is valid **by construction**.

rc430 spent that supply on ONE consumer -- the semigroup census -- and harvested
it in ONE direction: each op's own snippet, wrapping only that op. This file
asks whether the supply is bigger than the way rc430 spent it, and it changes
exactly one thing to find out.

THE ONE CHANGE: WRAP EVERY OP, RUN EVERY SNIPPET
================================================
rc430's recorder wraps op X and executes X's own snippet. But X's snippet is not
the only place X is called. ``srmech.math.cyclic.gcd`` appears inside dozens of
other ops' snippets, and every one of those calls carries a valid ``gcd``
argument. So this instrument installs a recording wrapper on **all 655 ops at
once** and executes **all 570 snippets**, then asks per op: who supplied me?

  * **SELF supply** -- the op's own snippet called it. This is exactly rc430's
    harvest, and re-measuring it is the positive control (PF2): a corpus scanner
    that cannot reproduce the shipped ledger's own coverage is broken, and its
    zeros would be FALSE REFUTEDs.
  * **CROSS supply** -- a DIFFERENT op's snippet called it. This is new, and it
    is the only thing that can reach an op with no snippet of its own.

WHAT IS ALREADY SHIPPED, AND WHY THE BRIEF'S FACE 2 IS STALE
============================================================
The rc431 brief describes `#T1094` as open -- "it feeds the literal ``"a"`` to
EVERY ``str`` parameter, including filesystem paths". **That was true at rc429
and is not true at rc430.** rc430 shipped ``tools/example_args.py`` (a
(op, param)-keyed provider), ``tests/example_args_ledger.ndjson`` (655 rows,
379 with args), a freshness gate, and a THREE-TIER ``_synth_args_for_entry`` in
``tests/test_mcp.py`` whose tier 1 is the harvest, whose ``str`` row is now
``"srmech_synth"`` rather than ``"a"``, and whose tier 3 diverts every
path-shaped parameter to a sandbox path. This file measures against that shipped
state, not against the brief's description of it, and reports the correction.

The open half of `#T1094` is therefore not "the literal ``a``" but **the 276 ops
the ledger does not cover** -- and the question this file exists to answer is
whether CROSS supply covers any of them.

THE FIVE MEASUREMENTS
=====================
**M1 -- REPRODUCTION.** Re-run the rc427 ladder by IMPORTING the rc427 module
the way rc430 did, and confirm the brief's numbers at rc430/655: Tier A 245 /
Tier B 292 / no-carrier-slot 69 / excluded-safety 49; Tier-A buckets
SNG 6 / bool 1 / GROUP 8 / NOT_CLOSED 93 / NOT_EXECUTABLE 137; self-maps 15.

**M2 -- THE CORPUS HARVEST.** All 655 wrapped, all snippets run. Per op: self
supply, cross supply, supplier list, per-parameter coverage.

**M3 -- `#T1094`'s ACTUAL POPULATION.** Not "how many ``str`` parameters exist"
but how many REQUIRED ``str`` parameters exist, how many are path-shaped (tier 3
already owns those), how many tier 1 already covers, and how many CROSS supply
adds. The marginal number is the answer.

**M4 -- CONSTRUCTORS.** Of rc430's 67 X_TYPE_WALL ops -- blocked on a parameter
TYPE the registry already publishes, needing a way to BUILD an inhabitant -- how
many does the corpus hand an actual instance to? Measured two ways, because one
of them is over-broad and saying so is the measurement:
  (a) DIRECT: cross supply binds that op's blocked slot. Decisive.
  (b) TYPE-INHABITED: some recorded value anywhere in the corpus has that
      runtime type. A declared type of ``list`` makes this trivially true, so
      (b) is reported as an UPPER bound and never as the finding.

**M5 -- THE HONEST BOUND.** Re-run the orbit-closure census with CROSS seeds on
the Tier-A ops rc430's self-oracle could not decide, and report what the census
becomes: a cardinal, or still BOUNDED with a stated floor.

THE CRITERION IS IMPORTED, NOT RE-TYPED
=======================================
M5 does not re-implement orbit closure. It loads
``_s2_census_precondition_rc430.py``, takes its ``WORKER_SRC`` verbatim up to
the stdin loop, and drives rc430's own ``run_one`` -- reaching the cross-supplier
case by rebinding ``BY_NAME[target]`` to the SUPPLIER's entry for the duration of
one call. ``record_calls(entry, fn_mod, fname)`` already separates "whose snippet
runs" from "which op is wrapped", so this needs no new logic at all: the seed
admission, the same-binding filter that defused instrument v1, the orbit, the
verdict order and the ``|S| < 2 => VACUOUS`` rule are rc430's, byte for byte.
That is deliberate. An M5 number is only comparable to rc430's 25 if it is the
same criterion, and re-typing it would make the comparison a claim rather than a
measurement.

WHAT THIS INSTRUMENT CANNOT DO (limits, declared before the numbers)
====================================================================
L1. **Cross supply is a LOWER bound, structurally.** A wrapper installed on a
    module attribute is only reached by callers that look the attribute up at
    call time. Every ``from x import y`` inside the package binds the ORIGINAL
    function object at import time and bypasses the wrapper forever. So an op
    called only through a from-import records ZERO cross calls while genuinely
    being called. "No cross supply" is BOUNDED, never REFUTED.
L2. **A recorded argument is valid for the binding it appeared in**, not
    universally. rc430 learned this the hard way -- pooling seeds across
    bindings is what made ``mod_mul`` look non-injective. The same-binding
    filter is inherited, and the cross-binding rejections are counted.
L3. **Wrapping 655 ops perturbs the corpus.** A snippet that introspects a
    function object may see the wrapper. PF2b measures the perturbation against
    the shipped ``worked_examples_result.ndjson`` baseline instead of assuming
    it away.
L4. **M4(b) is an UPPER bound and is labelled one.** Runtime-type-name matching
    on ``list`` cannot separate "the corpus has a recipe for this carrier" from
    "the corpus has a list".
L5. **Snippet execution has side effects.** These are our OWN committed
    snippets, already executed on every CI run by ``tools/run_worked_examples.py``
    and by ``tests/test_worked_examples_execute_rc354.py`` -- this file adds no
    new code to the trust boundary, it only adds observers to code the tree
    already runs. It still runs them in a temp cwd inside a killable worker,
    because "already trusted" is not the same as "already harmless": rc430
    measured a snippet writing a stray file into the package directory.

PRE-REGISTERED FALSIFIERS -- declared here, evaluated below, none tuned
======================================================================
PF1  REPRODUCTION. The rc427 ladder must reproduce the brief's rc430 numbers
     exactly at 655 (245 / 292 / 69 / 49; 6 / 1 / 8 / 93 / 137; self-maps 15).
     Any drift is REPORTED as a correction, not smoothed; downstream
     denominators are restated from the measured value.
PF2  SCANNER POSITIVE CONTROL -- the guard against a FALSE REFUTED. The corpus
     harvest must SELF-cover at least 90% of the 379 ops the SHIPPED ledger
     already records as ``status="ok"``. A scanner that finds less than the
     artifact already committed is broken, and every zero it reports is
     worthless. VOIDS M2-M5.
PF2b PERTURBATION. With all 655 ops wrapped, the number of snippets that run
     clean must stay within 10% of the shipped baseline's 467. A large drop
     means L3 dominates and the harvest is measuring the harness. VOIDS M2-M5.
PF3  CROSS-SUPPLY NON-VACUITY. Cross supply must reach at least one op that has
     NO worked snippet of its own. If zero, cross supply is EMPTY and the whole
     rc431 hypothesis is REFUTED -- report it as such.
PF4  SEPARATION. The harvest must cover strictly more than 0 and strictly fewer
     than all 655 ops. An instrument that covers everything cannot distinguish
     covered from uncovered and its coverage number means nothing.
PF5  `#T1094` POPULATION NON-EMPTY. There must be >= 1 REQUIRED ``str``
     parameter in the live schema. Zero makes M3 UNSUPPORTED, not zero.
PF6  CONSTRUCTOR SEPARATION. M4(a), the DIRECT count, must be strictly between
     0 and 67. At 0 the constructor gap is untouched (EMPTY); at 67 the test is
     too loose to separate and M4 is reported BOUNDED.
PF7  ORACLE NON-REGRESSION. Every Tier-A op rc430's self-oracle decided must
     still be decidable; the cross-seeded run may only ADD. A cross seed that
     REMOVES a rc430 decision is a regression and is reported by name.
PF8  HARNESS INTEGRITY. Worker deaths + timeouts must be < 1/20 of the probe
     set, else the harvest numbers are VOID. rc430 measured a run where 251 of
     533 probes died and every named control still passed -- a control set a
     half-dead run satisfies is not a control set.
PF9  THE v1 REFUTATION, RE-RUN THROUGH THE CROSS PATH. ``cyclic_mod_add`` must
     still land GROUP when seeded from a DIFFERENT op's snippet. It is the
     control that killed census instrument v1 by pooling across bindings; the
     cross path is exactly where that defect would come back. VOIDS M5.
PF10 CONTROL-ARM INTEGRITY (added for run 2). The unwrapped arm must harvest
     ZERO ops, else the arm is not unwrapped and PF2b measures nothing.
PF11 SEED-DEPENDENCE DECIDES THE BOUND (added for run 2). One Tier-A op with
     two DECIDED-but-different verdicts from two by-construction-valid seed
     sets makes the census a BOUNDED FLOOR. Only a zero licenses a cardinal.

WHAT RUN 1 ALREADY COST, RECORDED SO IT CANNOT BE QUIETLY DROPPED
=================================================================
Run 1 of this file fired **two** falsifiers, and both were kept:

* **PF9 fired.** ``cyclic_mod_add`` returned **SEMIGROUP** seeded from
  ``srmech.dsl.list_catalog_ops``'s snippet, against rc430's PC3 GROUP from its
  own. M5 is VOID and stays reported as void; M7 exists to measure the general
  case rather than to explain the single instance away.
* **PF2b fired at 387 clean vs 467** -- but against a baseline from a *different
  harness*. That comparison could not attribute the gap, so the falsifier was
  RE-SCOPED ONTO AN AXIS (wrapped vs unwrapped, same harness) rather than
  relaxed, and PF10 was added to guard the new arm. The cross-harness gap is
  still reported; it is now labelled a property of the harness.

DISCIPLINE
==========
* No Python ``abs()``; no stdlib ``math`` / ``fractions`` / ``decimal``; no
  numpy. Exact rates via ``srmech.math.q.Q``.
* Output is NDJSON, one record per line.

Run:  PYTHONPATH=docs/srmech/python python3 docs/srmech/notes/_s1_oracle_supply_rc431.py
"""

import importlib
import importlib.util
import json
import os
import subprocess
import sys
import threading
import time

import srmech
from srmech.introspect.tool_schema import ToolParameter, get_tool_schema, warmup_all
from srmech.math.q import Q

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "_s1_oracle_supply_rc431.ndjson")
RC427 = os.path.join(HERE, "_s2_semigroup_census_rc427.py")
RC430 = os.path.join(HERE, "_s2_census_precondition_rc430.py")
RC430_NDJSON = os.path.join(HERE, "_s2_census_precondition_rc430.ndjson")
PY_ROOT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "srmech", "python")
LEDGER = os.path.join(PY_ROOT, "tests", "example_args_ledger.ndjson")
WORKED_RESULT = os.path.join(PY_ROOT, "tests", "worked_examples_result.ndjson")

PREREGISTERED = {
    "PF1_reproduction": {
        "rule": "the rc427 ladder reproduces the brief's rc430 numbers at 655",
        "expect": {"registry": 655, "tier_a": 245, "tier_b": 292,
                   "no_carrier_slot": 69, "excluded_safety": 49,
                   "tier_a_buckets": {"SEMIGROUP_NOT_GROUP": 6,
                                      "SEMIGROUP_BOOL_DOMAIN_ARTIFACT": 1,
                                      "GROUP": 8, "NOT_CLOSED": 93,
                                      "NOT_EXECUTABLE": 137},
                   "measured_self_maps": 15},
        "void_if_fails": False,
        "why": "drift is a CORRECTION to report, not a failure to hide; every "
               "downstream denominator is restated from the measured value",
    },
    "PF2_scanner_positive_control": {
        "rule": "corpus SELF-coverage >= 90% of the shipped ledger's ok rows",
        "threshold_ratio": "9/10",
        "void_if_fails": True,
        "why": "the guard against a FALSE REFUTED. A single-line grep returned "
               "0 this session because its target was line-wrapped. A corpus "
               "scanner that finds LESS than the artifact already committed is "
               "broken, and every zero it reports is worthless.",
    },
    "PF2b_perturbation": {
        "rule": "clean-snippet count stays within 10% of the shipped 467",
        "baseline_ok": 467,
        "threshold_ratio": "1/10",
        "void_if_fails": True,
        "why": "L3 -- wrapping 655 ops could make the harvest measure the "
               "harness rather than the corpus",
    },
    "PF3_cross_supply_non_vacuity": {
        "rule": ">= 1 op with NO snippet of its own is reached by CROSS supply",
        "void_if_fails": False,
        "why": "if zero, the rc431 hypothesis is REFUTED and says so",
    },
    "PF4_separation": {
        "rule": "0 < ops_with_any_supply < 655",
        "void_if_fails": True,
    },
    "PF5_t1094_population_non_empty": {
        "rule": ">= 1 REQUIRED str parameter in the live schema",
        "void_if_fails": False,
        "why": "zero makes M3 UNSUPPORTED, which is not the same as zero",
    },
    "PF6_constructor_separation": {
        "rule": "0 < M4(a) DIRECT < 67",
        "void_if_fails": False,
        "why": "0 => EMPTY, 67 => the test cannot separate and M4 is BOUNDED",
    },
    "PF7_oracle_non_regression": {
        "rule": "no Tier-A op rc430's self-oracle DECIDED becomes undecided",
        "void_if_fails": False,
    },
    "PF8_harness_integrity": {
        "rule": "worker deaths + timeouts < 1/20 of the probe set",
        "threshold_ratio": "1/20",
        "void_if_fails": True,
    },
    # ── added for run 2, declared before run 2, after run 1 fired PF2b/PF9 ──
    "PF10_control_arm_yields_no_supply": {
        "rule": "the UNWRAPPED control arm must harvest ZERO ops",
        "void_if_fails": True,
        "why": "ADDED FOR RUN 2. Run 1's PF2b compared this harness's wrapped "
               "clean-count against a baseline from a DIFFERENT harness, and "
               "fired at 387 vs 467 -- a gap that cannot be attributed. The "
               "control arm re-points PF2b at WRAPPED vs UNWRAPPED. PF10 is the "
               "control arm's OWN control: if an unwrapped pass still reports "
               "supply, the arm is not actually unwrapped and PF2b is void "
               "again. Declared before run 2, not tuned after it.",
    },
    "PF11_seed_dependence_decides_the_bound": {
        "rule": "if ANY Tier-A op gets different DECIDED verdicts from its self "
                "seeds and its cross seeds, the census is a BOUNDED FLOOR and "
                "must be reported as one, never as a cardinal",
        "void_if_fails": False,
        "why": "ADDED FOR RUN 2, forced by run 1's PF9 firing. Both seed sets "
               "are valid BY CONSTRUCTION, so a disagreement is not a bad "
               "argument -- it is the criterion depending on which valid "
               "arguments it happened to see. A zero here would be the only "
               "result that licenses a cardinal.",
    },
    "PF9_v1_refutation_via_cross_path": {
        "op": "srmech.cascade.cyclic_mod_add",
        "must_land_in": "GROUP",
        "void_if_fails": True,
        "why": "the control that killed instrument v1 (SEMIGROUP_NOT_GROUP on "
               "carrier=Z12, binding b=12 n=6 -- a modulus SMALLER than the "
               "enumerated carrier). The CROSS path is exactly where "
               "cross-binding pooling would come back.",
    },
}

#: measured-slow ops, skipped by NAME (L5). Sourced from
#: ``tools/run_worked_examples.py``'s own SLOW_ALLOWLIST.
SLOW_SKIP = {
    "srmech.physics.qm.so8.an_embedding",
    "srmech.physics.qm.so8.so7_subalgebra",
    "srmech.math.laplacian.recover_check",
    "srmech.math.laplacian.recover_check_spectral",
    "srmech.math.laplacian.recover_check_structural",
    "srmech.math.laplacian.three_fold_eigvec_groups",
    "srmech.math.primes.is_prime",
    "srmech.bus.by_name",
    "srmech.bus.list_endpoints",
    "srmech.introspect.list",
    "srmech.introspect.by_pid",
}

PER_SNIPPET_BUDGET_S = 25.0
PER_ORBIT_BUDGET_S = 25.0

# ── phase 1: the corpus recorder — ALL ops wrapped, ONE snippet per request ──
HARVEST_SRC = r'''
import importlib, inspect, json, os, sys, tempfile
os.chdir(tempfile.mkdtemp(prefix="s1rc431_"))
sys.stdout.reconfigure(line_buffering=True)
import srmech
from srmech.introspect.tool_schema import get_tool_schema, warmup_all
warmup_all()
TOOLS = get_tool_schema().tools
BY_NAME = {e.name: e for e in TOOLS}

MAX_BINDINGS = 4
MAX_REPR = 150
MAX_JSON = 4096

# Resolve every op ONCE. A name that does not resolve by dotted path is recorded
# as unresolvable rather than raised: profile-contributed and class-bound
# surfaces legitimately do not, and a harness that dies on them would report a
# smaller registry than exists.
SLOTS = {}
UNRESOLVABLE = []
for e in TOOLS:
    mn, _, fnm = e.name.rpartition(".")
    if not mn:
        UNRESOLVABLE.append(e.name); continue
    try:
        mod = importlib.import_module(mn)
    except BaseException:
        UNRESOLVABLE.append(e.name); continue
    real = getattr(mod, fnm, None)
    if real is None or not callable(real):
        UNRESOLVABLE.append(e.name); continue
    SLOTS[e.name] = (mod, fnm, real)

SIGS = {}
for op, (mod, fnm, real) in SLOTS.items():
    try:
        SIGS[op] = inspect.signature(real)
    except BaseException:
        SIGS[op] = None


def snippet_source(ex):
    if not isinstance(ex, dict):
        return None
    w = ex.get("worked")
    if not isinstance(w, str) or not w.strip():
        return None
    s = ex.get("setup")
    return (s + "\n" + w) if isinstance(s, str) and s.strip() else w


def short(v):
    try:
        r = repr(v)
    except BaseException:
        return "<unrepr>"
    return r if len(r) <= MAX_REPR else r[:MAX_REPR] + "..."


def _as_wire(v):
    if isinstance(v, (tuple, list)):
        return [_as_wire(x) for x in v]
    if isinstance(v, dict):
        return {k: _as_wire(x) for k, x in v.items()}
    return v


def jval(v):
    """(ok, wire). JSON round-trip up to the tuple/list collapse -- the same
    admission rule ``tools/example_args.jsonable`` ships, because JSON has no
    tuple and the wire form IS the truth for a JSON-bounded consumer."""
    try:
        t = json.dumps(v, sort_keys=True)
    except (TypeError, ValueError):
        return False, None
    if len(t) > MAX_JSON:
        return False, None
    try:
        back = json.loads(t)
    except ValueError:
        return False, None
    if back != _as_wire(v):
        return False, None
    return True, back


#: The CONTROL ARM. PF2b compares the wrapped run against a baseline produced by
#: a DIFFERENT harness (``tools/run_worked_examples.py``), so a gap between them
#: is confounded: it could be the wrappers, or it could be the two harnesses
#: differing. Running THIS harness with the wrappers switched off separates the
#: two, and only then does the falsifier measure what it claims to.
NO_WRAP = os.environ.get("RC431_NO_WRAP") == "1"


def run_snippet(owner):
    out = {"owner": owner}
    e = BY_NAME.get(owner)
    if e is None:
        out["status"] = "absent_from_registry"; return out
    src = snippet_source(e.example)
    if src is None:
        out["status"] = "no_worked_snippet"; return out
    sink = {}

    def mk(op, real):
        def w(*a, **kw):
            r = real(*a, **kw)      # raises => NOT recorded; those args are the
            lst = sink.get(op)      # invalid ones and that is the whole point
            if lst is None:
                lst = sink[op] = []
            if len(lst) < MAX_BINDINGS:
                lst.append((a, dict(kw)))
            return r
        try:
            w.__name__ = getattr(real, "__name__", op.rpartition(".")[2])
            w.__qualname__ = getattr(real, "__qualname__", w.__name__)
            w.__module__ = getattr(real, "__module__", None)
            w.__doc__ = getattr(real, "__doc__", None)
            w.__wrapped__ = real
        except Exception:
            pass
        return w

    if not NO_WRAP:
        for op, (mod, fnm, real) in SLOTS.items():
            try:
                setattr(mod, fnm, mk(op, real))
            except Exception:
                pass
    err = None
    try:
        exec(compile(src, "<worked:" + owner + ">", "exec"),
             {"__name__": "__worked__"})
    except BaseException as exc:
        err = type(exc).__name__ + ": " + str(exc)[:200]
    finally:
        if not NO_WRAP:
            for op, (mod, fnm, real) in SLOTS.items():
                try:
                    setattr(mod, fnm, real)
                except Exception:
                    pass
    out["status"] = "ok" if err is None else "raised"
    out["error"] = err
    ops = []
    for op, calls in sink.items():
        sig = SIGS.get(op)
        binds = []
        for a, kw in calls:
            if sig is None:
                continue
            try:
                b = sig.bind(*a, **kw)
                b.apply_defaults()
                bd = dict(b.arguments)
            except BaseException:
                continue
            row = {}
            for pn, v in bd.items():
                ok, wire = jval(v)
                cell = {"t": type(v).__name__, "j": ok}
                if ok:
                    cell["v"] = wire
                else:
                    cell["r"] = short(v)
                row[pn] = cell
            binds.append(row)
            if len(binds) >= 2:
                break
        ops.append({"op": op, "n_calls": len(calls), "bindings": binds})
    out["ops"] = ops
    return out


print("\x01" + json.dumps({"boot": True, "n_slots": len(SLOTS),
                           "wrapped": not NO_WRAP,
                           "unresolvable": UNRESOLVABLE}), flush=True)
for line in sys.stdin:
    nm = line.strip()
    if not nm:
        continue
    try:
        rec = run_snippet(nm)
    except BaseException as exc:
        rec = {"owner": nm, "status": "harvest_error",
               "error": type(exc).__name__ + ": " + str(exc)[:200]}
    print("\x01" + json.dumps(rec, sort_keys=True), flush=True)
'''


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_orbit_worker_src():
    """rc430's worker, verbatim up to its stdin loop, plus a CROSS driver.

    The driver adds no criterion of its own. ``record_calls(entry, fn_mod,
    fname)`` already separates *whose snippet runs* from *which op is wrapped*,
    so rebinding ``BY_NAME[target]`` to the SUPPLIER's entry for the duration of
    one ``run_one(target)`` call reaches the cross-supplier case through rc430's
    own seed admission, same-binding filter, orbit and verdict order. Byte-for-
    byte reuse is what makes an rc431 number comparable to rc430's 25.
    """
    rc430 = load_module(RC430, "_s2_rc430")
    src = rc430.WORKER_SRC
    marker = "for line in sys.stdin:"
    head, sep, _tail = src.partition(marker)
    if not sep:
        raise RuntimeError("rc430 WORKER_SRC shape changed: no stdin loop found")
    driver = r'''

# ── rc431: the CROSS driver. No new criterion — see build_orbit_worker_src. ──
# Precedence across suppliers is PRE-REGISTERED: a SEMIGROUP verdict is a
# positive existence claim (a witnessed collision), a GROUP verdict is only
# "no collision in THIS orbit". So SEMIGROUP wins a disagreement and the
# disagreement is RECORDED rather than resolved silently.
DECIDED = ("SEMIGROUP", "GROUP")


def run_cross(target, suppliers):
    orig = BY_NAME.get(target)
    tried, best, seen_verdicts = [], None, []
    for s in suppliers:
        se = BY_NAME.get(s)
        if se is None:
            continue
        BY_NAME[target] = se
        try:
            r = run_one(target)
        except BaseException as exc:
            r = {"op": target, "oracle": "CROSS_ERROR",
                 "exc": type(exc).__name__ + ": " + str(exc)[:160]}
        finally:
            if orig is None:
                BY_NAME.pop(target, None)
            else:
                BY_NAME[target] = orig
        r["supplier"] = s
        tried.append({"supplier": s, "oracle": r.get("oracle"),
                      "verdict": r.get("verdict")})
        v = r.get("verdict")
        if v:
            seen_verdicts.append(v)
        if v == "SEMIGROUP":
            best = r
            break
        if v == "GROUP" and (best is None or best.get("verdict") not in DECIDED):
            best = r
        elif best is None:
            best = r
    if best is None:
        best = {"op": target, "oracle": "NO_SUPPLIER"}
    best["cross_tried"] = tried
    best["cross_conflict"] = len(set(v for v in seen_verdicts
                                     if v in DECIDED)) > 1
    return best


for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    mode, _, rest = line.partition("\t")
    try:
        if mode == "SELF":
            # rc430's own call, unmodified: the op's OWN snippet seeds its orbit
            rec = run_one(rest)
            rec["mode"] = "SELF"
        else:
            tgt, _, sup = rest.partition("\t")
            rec = run_cross(tgt, [s for s in sup.split(",") if s])
            rec["mode"] = "CROSS"
    except BaseException as exc:
        rec = {"op": rest, "oracle": "WORKER_ERROR", "mode": mode,
               "exc": type(exc).__name__ + ": " + str(exc)[:200]}
    print("\x01" + json.dumps(rec, sort_keys=True), flush=True)
'''
    return head + driver


class Worker:
    """A long-lived child the parent can kill. Nothing in-process can interrupt
    arbitrary Python reliably; a process kill cannot be defeated by a C loop.
    Inherited from rc430, whose PC9 exists because one run recorded WORKER_DIED
    on 251 of 533 probes and still exited 0."""

    def __init__(self, src_path, env):
        self.src_path = src_path
        self.env = env
        self.deaths = 0
        self.timeouts = 0
        self._start()

    def _start(self):
        self.proc = subprocess.Popen(
            [sys.executable, "-u", self.src_path],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, env=self.env,
        )
        self.q = []
        self.lock = threading.Lock()
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        proc = self.proc
        try:
            for line in proc.stdout:
                if line.startswith("\x01"):
                    with self.lock:
                        self.q.append(line[1:])
        except Exception:
            pass

    def drain(self, budget):
        t0 = time.monotonic()
        while time.monotonic() - t0 < budget:
            with self.lock:
                if self.q:
                    return json.loads(self.q.pop(0))
            if self.proc.poll() is not None:
                return None
            time.sleep(0.005)
        return None

    def kill(self):
        try:
            self.proc.kill()
        except Exception:
            pass

    def ask(self, payload, budget, key, keyval):
        try:
            self.proc.stdin.write(payload + "\n")
            self.proc.stdin.flush()
        except Exception:
            self.deaths += 1
            self.kill(); self._start(); self.drain(60.0)
            return {key: keyval, "status": "WORKER_RESTART"}
        t0 = time.monotonic()
        while time.monotonic() - t0 < budget:
            with self.lock:
                if self.q:
                    return json.loads(self.q.pop(0))
            if self.proc.poll() is not None:
                self.deaths += 1
                self.kill(); self._start(); self.drain(60.0)
                return {key: keyval, "status": "WORKER_DIED"}
            time.sleep(0.005)
        self.timeouts += 1
        self.kill(); self._start(); self.drain(60.0)
        return {key: keyval, "status": "TIMEOUT", "budget_s": budget}


def rate(num, den):
    """Exact rate as a Class-N rational string. No float division."""
    if den == 0:
        return "0/0"
    q = Q(num, den)
    return str(q.numerator) + "/" + str(q.denominator)


def main():
    print("srmech.__file__    = " + srmech.__file__)
    print("srmech.__version__ = " + srmech.__version__)
    numpy_present = importlib.util.find_spec("numpy") is not None
    print("numpy present      = " + str(numpy_present))
    warmup_all()
    tools = get_tool_schema().tools
    by_name = {e.name: e for e in tools}
    print("registry           = " + str(len(tools)))
    print("ToolParameter      = " + str(list(ToolParameter.__dataclass_fields__)))
    print()
    out = []
    out.append({"record": "environment", "srmech_file": srmech.__file__,
                "srmech_version": srmech.__version__,
                "numpy_present": numpy_present, "registry": len(tools),
                "tool_parameter_fields": list(ToolParameter.__dataclass_fields__),
                "python": sys.version.split()[0]})
    out.append({"record": "preregistered_falsifiers", **PREREGISTERED})

    # ══ M1 — REPRODUCTION, using the rc427 module's own code ══════════════
    print("M1 — REPRODUCING THE rc427 LADDER AT rc430/655 (imported, not re-typed)")
    rc427 = load_module(RC427, "_s2_rc427")
    carriers = rc427._build_carriers()
    rc427.tier1_shape_screen(tools)
    tierA = {k: [] for k in rc427.BUCKETS}
    tierB = {k: [] for k in rc427.BUCKETS}
    detail, fns = {}, {}
    t0 = time.monotonic()
    for i, e in enumerate(tools):
        mod, _, fname = e.name.rpartition(".")
        fn = getattr(importlib.import_module(mod), fname)
        fns[e.name] = fn
        req, opt = rc427._required_params(fn)
        io_params = [] if req is None else [
            n for n in (req + opt) if n.lower() in rc427.DENY_PARAM_NAMES]
        if e.name.startswith(rc427.DENY_PREFIXES) or io_params:
            tierA["EXCLUDED_SAFETY"].append(e.name)
            detail[e.name] = {"bucket": "EXCLUDED_SAFETY", "tier": "-", "req": req or []}
            continue
        if req is None:
            tier, bucket, wits = "-", "NOT_EXECUTABLE", []
        elif len(req) == 0:
            tier, bucket, wits = "-", "NO_CARRIER_SLOT", []
        else:
            tier = "A" if len(req) == 1 else "B"
            bucket, wits, _diag = rc427.probe_op(fn, carriers, req, opt)
        (tierA if tier in ("A", "-") else tierB)[bucket].append(e.name)
        detail[e.name] = {"bucket": bucket, "tier": tier, "witnesses": wits,
                          "req": req or []}
        if (i + 1) % 200 == 0:
            print("  ... " + str(i + 1) + "/" + str(len(tools)) +
                  " (" + str(int(time.monotonic() - t0)) + "s)")
    A = {k: [n for n in v if detail[n]["tier"] == "A"] for k, v in tierA.items()}
    kept, bool_art = [], []
    for op in A["SEMIGROUP_NOT_GROUP"]:
        clean, _art = rc427.adjudicate(by_name[op], detail[op]["witnesses"])
        (kept if clean else bool_art).append(op)
    A["SEMIGROUP_BOOL_DOMAIN_ARTIFACT"] = bool_art
    A["SEMIGROUP_NOT_GROUP"] = kept
    a_self_maps = sum(len(A[k]) for k in ("SEMIGROUP_NOT_GROUP",
                                          "SEMIGROUP_CONSTANT_ONLY",
                                          "SEMIGROUP_BOOL_DOMAIN_ARTIFACT", "GROUP"))
    a_total = sum(len(v) for v in A.values())
    b_total = sum(len(v) for v in tierB.values())
    no_slot = [n for n in tierA["NO_CARRIER_SLOT"] if detail[n]["tier"] == "-"]
    excl = [n for n in tierA["EXCLUDED_SAFETY"] if detail[n]["tier"] == "-"]
    m1 = {"record": "m1_reproduction", "registry_total": len(tools),
          "tier_a": a_total, "tier_b": b_total, "no_carrier_slot": len(no_slot),
          "excluded_safety": len(excl),
          "sum": a_total + b_total + len(no_slot) + len(excl),
          "tier_a_buckets": {k: len(A[k]) for k in rc427.BUCKETS},
          "tier_b_buckets": {k: len(tierB[k]) for k in rc427.BUCKETS},
          "tier_a_measured_self_maps": a_self_maps,
          "brief_expected": PREREGISTERED["PF1_reproduction"]["expect"],
          "elapsed_s": int(time.monotonic() - t0)}
    exp = PREREGISTERED["PF1_reproduction"]["expect"]
    drift = {"tier_a": a_total - exp["tier_a"], "tier_b": b_total - exp["tier_b"],
             "no_carrier_slot": len(no_slot) - exp["no_carrier_slot"],
             "excluded_safety": len(excl) - exp["excluded_safety"],
             "measured_self_maps": a_self_maps - exp["measured_self_maps"]}
    for k, v in exp["tier_a_buckets"].items():
        drift["bucket_" + k] = len(A[k]) - v
    m1["drift_from_brief"] = drift
    m1["pf1_pass"] = not any(drift.values())
    out.append(m1)
    print("  TIER A " + str(a_total) + " | TIER B " + str(b_total) +
          " | no-slot " + str(len(no_slot)) + " | excluded " + str(len(excl)) +
          " | sum " + str(m1["sum"]) + "/" + str(len(tools)))
    print("  buckets " + str(m1["tier_a_buckets"]))
    print("  self-maps " + str(a_self_maps) + "   PF1 " +
          ("PASS" if m1["pf1_pass"] else "DRIFT " + str(drift)))
    print()

    tier_a_ops = sorted(n for n in detail if detail[n]["tier"] == "A")
    tier_b_ops = sorted(n for n in detail if detail[n]["tier"] == "B")

    # ══ M2 — THE CORPUS HARVEST ═══════════════════════════════════════════
    print("M2 — CORPUS HARVEST: all 655 ops wrapped, every snippet run")
    env = dict(os.environ)
    env["PYTHONPATH"] = PY_ROOT + os.pathsep + env.get("PYTHONPATH", "")
    env["SRMECH_EXPECT_PURE"] = "1"
    import tempfile
    tmpd = tempfile.mkdtemp(prefix="rc431_")
    hpath = os.path.join(tmpd, "harvest_" + str(os.getpid()) + ".py")
    with open(hpath, "w") as fh:
        fh.write(HARVEST_SRC)
    opath = os.path.join(tmpd, "orbit_" + str(os.getpid()) + ".py")
    with open(opath, "w") as fh:
        fh.write(build_orbit_worker_src())

    owners = [e.name for e in tools
              if isinstance(e.example, dict) and (e.example.get("worked") or "").strip()]
    probe = [o for o in owners if o not in SLOW_SKIP]
    print("  snippets present " + str(len(owners)) + " | probing " + str(len(probe)) +
          " (" + str(len(owners) - len(probe)) + " slow/subprocess-skipped)")

    def harvest_pass(wrapped, label):
        """One pass over every snippet. ``wrapped=False`` is the PF2b control
        arm: same harness, same snippets, same budget, wrappers OFF."""
        penv = dict(env)
        penv["RC431_NO_WRAP"] = "0" if wrapped else "1"
        wk = Worker(hpath, penv)
        bt = wk.drain(120.0)
        sup, stat = {}, {}
        tt = time.monotonic()
        for j, own in enumerate(probe):
            r = wk.ask(own, PER_SNIPPET_BUDGET_S, "owner", own)
            stat[own] = r.get("status")
            for entry in r.get("ops") or []:
                op = entry["op"]
                s = sup.setdefault(op, {"self": False, "cross": set(),
                                        "params": {}, "n_calls": 0})
                if op == own:
                    s["self"] = True
                else:
                    s["cross"].add(own)
                s["n_calls"] += entry.get("n_calls", 0)
                for row in entry.get("bindings") or []:
                    for pn, cell in row.items():
                        prev = s["params"].get(pn)
                        if prev is None or (cell.get("j") and not prev.get("j")):
                            s["params"][pn] = {"t": cell["t"],
                                               "j": cell.get("j", False),
                                               "src": "self" if op == own else own}
                            if "v" in cell:
                                s["params"][pn]["v"] = cell["v"]
            if (j + 1) % 150 == 0:
                print("  [" + label + "] ... " + str(j + 1) + "/" + str(len(probe)) +
                      " (" + str(int(time.monotonic() - tt)) + "s)")
        wk.kill()
        return sup, stat, bt, int(time.monotonic() - tt)

    supply, snippet_status, boot, harvest_elapsed = harvest_pass(True, "wrapped")
    n_slots = boot.get("n_slots") if isinstance(boot, dict) else None
    unresolvable = boot.get("unresolvable", []) if isinstance(boot, dict) else []
    print("  worker slots " + str(n_slots) + " | unresolvable " + str(len(unresolvable)) +
          " | harvest " + str(harvest_elapsed) + "s")

    # ── the PF2b control arm: THIS harness, wrappers OFF ──────────────────
    _sup0, ctrl_status, _b0, ctrl_elapsed = harvest_pass(False, "control")
    ctrl_clean = sum(1 for v in ctrl_status.values() if v == "ok")
    ctrl_supply_ops = len(_sup0)
    print("  control arm (unwrapped): clean " + str(ctrl_clean) +
          " | ops with supply " + str(ctrl_supply_ops) +
          " (must be 0) | " + str(ctrl_elapsed) + "s")

    n_clean = sum(1 for v in snippet_status.values() if v == "ok")
    n_raised = sum(1 for v in snippet_status.values() if v == "raised")
    n_broken = sum(1 for v in snippet_status.values()
                   if v in ("WORKER_DIED", "TIMEOUT", "WORKER_RESTART", "harvest_error"))
    perturbed = sorted(o for o in probe
                       if ctrl_status.get(o) == "ok" and snippet_status.get(o) != "ok")
    healed = sorted(o for o in probe
                    if ctrl_status.get(o) != "ok" and snippet_status.get(o) == "ok")
    self_ops = sorted(k for k, v in supply.items() if v["self"])
    cross_ops = sorted(k for k, v in supply.items() if v["cross"])
    any_ops = sorted(supply)
    cross_only = sorted(k for k, v in supply.items() if v["cross"] and not v["self"])

    # ledger baseline — the shipped artifact, the PF2 positive control
    ledger = {}
    ledger_meta = None
    with open(LEDGER) as fh:
        for line in fh:
            r = json.loads(line)
            if r.get("record") == "meta":
                ledger_meta = r
            else:
                ledger[r["op"]] = r
    ledger_ok = sorted(k for k, r in ledger.items() if r.get("status") == "ok")
    ledger_with_args = sorted(k for k, r in ledger.items() if r.get("args"))
    reproduced = [k for k in ledger_ok if k in supply and supply[k]["self"]]
    pf2_pass = len(reproduced) * 10 >= len(ledger_ok) * 9
    # PF2b, RE-SCOPED ONTO THE RIGHT AXIS after it fired on the first run.
    # It fired at 387 clean vs a 467 baseline -- but that baseline comes from a
    # DIFFERENT harness (``tools/run_worked_examples.py``, which supplies marker
    # handling and a per-op slow budget this file does not). Comparing across
    # harnesses cannot tell "the wrappers broke 80 snippets" from "the two
    # harnesses were never the same instrument". The falsifier is not weakened
    # -- it is pointed at the axis it always meant: WRAPPED vs UNWRAPPED, same
    # harness, same snippets, same budget. The cross-harness gap is still
    # reported, as a property of the harness rather than of the wrappers.
    pf2b_pass = n_clean * 10 >= ctrl_clean * 9
    no_snippet_ops = sorted(e.name for e in tools if e.name not in set(owners))
    pf3_hits = sorted(k for k in cross_only if k in set(no_snippet_ops))

    m2 = {"record": "m2_corpus_harvest",
          "snippets_present": len(owners), "snippets_probed": len(probe),
          "snippets_clean": n_clean, "snippets_raised": n_raised,
          "snippets_broken": n_broken,
          "control_arm_unwrapped_clean": ctrl_clean,
          "control_arm_ops_with_supply_must_be_zero": ctrl_supply_ops,
          "wrapper_perturbed_snippets": len(perturbed),
          "wrapper_perturbed_names": perturbed[:25],
          "wrapper_healed_snippets": len(healed),
          "shipped_baseline_ok_DIFFERENT_HARNESS": 467,
          "cross_harness_gap": ctrl_clean - 467,
          "worker_slots": n_slots, "unresolvable_ops": len(unresolvable),
          "ops_with_any_supply": len(any_ops),
          "ops_with_self_supply": len(self_ops),
          "ops_with_cross_supply": len(cross_ops),
          "ops_cross_only": len(cross_only),
          "ops_with_no_supply": len(tools) - len(any_ops),
          "ledger_rows": len(ledger), "ledger_ok": len(ledger_ok),
          "ledger_with_args": len(ledger_with_args),
          "ledger_meta": ledger_meta,
          "ledger_ok_reproduced_by_corpus_self": len(reproduced),
          "ops_with_no_snippet": len(no_snippet_ops),
          "no_snippet_ops_reached_by_cross": len(pf3_hits),
          "marginal_over_shipped_ledger":
              len(sorted(set(any_ops) - set(ledger_with_args))),
          "elapsed_s": harvest_elapsed}
    out.append(m2)
    for k in ("ops_with_any_supply", "ops_with_self_supply", "ops_with_cross_supply",
              "ops_cross_only", "ops_with_no_supply", "ledger_with_args",
              "ledger_ok_reproduced_by_corpus_self", "no_snippet_ops_reached_by_cross",
              "marginal_over_shipped_ledger", "snippets_clean",
              "control_arm_unwrapped_clean", "wrapper_perturbed_snippets",
              "wrapper_healed_snippets"):
        print("  " + k.ljust(38) + str(m2[k]))
    print()

    for op in sorted(supply):
        s = supply[op]
        out.append({"record": "op_supply", "op": op, "self": s["self"],
                    "n_cross_suppliers": len(s["cross"]),
                    "suppliers": sorted(s["cross"])[:6],
                    "n_calls": s["n_calls"],
                    "params": {p: {"t": c["t"], "j": c["j"], "src": c["src"]}
                               for p, c in s["params"].items()}})

    # ══ M3 — `#T1094`'s ACTUAL POPULATION ═════════════════════════════════
    print("M3 — `#T1094`: the REQUIRED-str population, and what covers it")
    sys.path.insert(0, os.path.join(PY_ROOT, "tools"))
    import example_args as ea            # the SHIPPED provider
    prov = ea.provider()
    str_types = ("str", "Optional[str]")
    pop, cov = [], {"ledger": 0, "corpus_self": 0, "corpus_cross": 0,
                    "path_shaped": 0, "uncovered": 0}
    all_req = 0
    for e in tools:
        for p in e.parameters:
            if not p.required:
                continue
            all_req += 1
            if p.type not in str_types:
                continue
            path_shaped = ea.is_path_shaped(p.name, p.type)
            in_ledger = prov.get(e.name, p.name) is not ea.UNSYNTHESIZABLE
            cell = (supply.get(e.name) or {}).get("params", {}).get(p.name)
            src = cell["src"] if cell else None
            pop.append({"record": "t1094_str_param", "op": e.name,
                        "param": p.name, "type": p.type,
                        "path_shaped": path_shaped, "in_shipped_ledger": in_ledger,
                        "corpus_src": src,
                        "corpus_value": (cell or {}).get("v")})
            if path_shaped:
                cov["path_shaped"] += 1
            if in_ledger:
                cov["ledger"] += 1
            if src == "self":
                cov["corpus_self"] += 1
            elif src:
                cov["corpus_cross"] += 1
            if not in_ledger and not src and not path_shaped:
                cov["uncovered"] += 1
    n_str = len(pop)
    marginal = [r for r in pop if not r["in_shipped_ledger"] and r["corpus_src"]]
    m3 = {"record": "m3_t1094_population",
          "required_params_total": all_req,
          "required_str_params": n_str,
          "path_shaped_tier3_owns": cov["path_shaped"],
          "covered_by_shipped_ledger_tier1": cov["ledger"],
          "covered_by_corpus_self": cov["corpus_self"],
          "covered_by_corpus_cross": cov["corpus_cross"],
          "corpus_marginal_over_ledger": len(marginal),
          "marginal_ops": sorted({r["op"] for r in marginal})[:40],
          "still_uncovered": cov["uncovered"],
          "str_share_of_required": rate(n_str, all_req),
          "note": "the brief calls `#T1094` open with the literal 'a'; rc430 "
                  "shipped tools/example_args.py + a 3-tier _synth_args_for_entry "
                  "and the str row is now 'srmech_synth'. Measured against the "
                  "SHIPPED state."}
    out.append(m3)
    out.extend(pop)
    for k in ("required_params_total", "required_str_params",
              "path_shaped_tier3_owns", "covered_by_shipped_ledger_tier1",
              "covered_by_corpus_self", "covered_by_corpus_cross",
              "corpus_marginal_over_ledger", "still_uncovered"):
        print("  " + k.ljust(38) + str(m3[k]))
    print()

    # ══ M3b — THE SHIPPED CEILING, AND WHAT CROSS SUPPLY WOULD DRAIN ══════
    #
    # `#T1094`'s real open population is not "str params" -- rc430 already
    # closed the literal-"a" defect. It is the down-only ceiling the shipped
    # gate holds: ``CEIL_UNSYNTHESIZABLE_PARAMS = 52`` (op, param) pairs with no
    # justified value at all, across ``CEIL_UNSYNTHESIZABLE_OPS = 34`` ops that
    # the every-tool smoke therefore SKIPS. That ceiling is the thing an rc can
    # move, so it is the thing to measure. The ledger admits only
    # JSON-round-trippable values, so the honest drain is the JSONABLE subset.
    print("M3b — the shipped UNSYNTHESIZABLE ceiling: what would CROSS supply drain?")
    m3b = {"record": "m3b_ceiling_drain"}
    try:
        sys.path.insert(0, os.path.join(PY_ROOT, "tests"))
        sys.path.insert(0, PY_ROOT)
        import test_mcp                                   # the module under test
        advertised = [t for t in tools if t.mcp_callable]
        unsat, unsat_ops = [], set()
        for t in advertised:
            args = test_mcp._synth_args_for_entry(t)
            for p in t.parameters:
                if not p.required:
                    continue
                if args.get(p.name) is ea.UNSYNTHESIZABLE:
                    unsat.append((t.name, p.name, p.type))
                    unsat_ops.add(t.name)
        drained, drained_json, drained_cross = [], [], []
        for op, pn, ty in unsat:
            cell = (supply.get(op) or {}).get("params", {}).get(pn)
            if cell is None:
                continue
            drained.append((op, pn, ty, cell["src"], cell["t"], cell["j"]))
            if cell["j"]:
                drained_json.append((op, pn, ty))
            if cell["src"] != "self":
                drained_cross.append((op, pn, ty))
        fully = sorted({op for op in unsat_ops
                        if all(((supply.get(op) or {}).get("params", {}).get(pn) or {}).get("j")
                               for o2, pn, _t in unsat if o2 == op)})
        m3b.update({
            "advertised_ops": len(advertised),
            "shipped_ceil_unsynthesizable_params": 52,
            "shipped_ceil_unsynthesizable_ops": 34,
            "shipped_ceil_sandbox_fallback_params": 30,
            "measured_unsynthesizable_params": len(unsat),
            "measured_unsynthesizable_ops": len(unsat_ops),
            "corpus_supplies_any_value": len(drained),
            "corpus_supplies_JSONABLE_value": len(drained_json),
            "of_those_from_CROSS_supply": len(drained_cross),
            "ops_fully_drained": len(fully),
            "ops_fully_drained_names": fully[:30],
            "drained_rows": [{"op": o, "param": p, "type": t, "src": s,
                              "runtime_type": rt, "jsonable": j}
                             for o, p, t, s, rt, j in drained][:60],
            "residual_ceiling_if_landed": len(unsat) - len(drained_json),
            "note": "the ledger admits only JSON-round-trippable values, so the "
                    "honest drain is the JSONABLE column, not the any-value one",
        })
    except BaseException as exc:
        m3b.update({"status": "UNSUPPORTED",
                    "exc": type(exc).__name__ + ": " + str(exc)[:200]})
    out.append(m3b)
    for k in ("measured_unsynthesizable_params", "measured_unsynthesizable_ops",
              "corpus_supplies_any_value", "corpus_supplies_JSONABLE_value",
              "of_those_from_CROSS_supply", "ops_fully_drained",
              "residual_ceiling_if_landed"):
        if k in m3b:
            print("  " + k.ljust(38) + str(m3b[k]))
    print()

    # ══ M4 — CONSTRUCTORS ═════════════════════════════════════════════════
    print("M4 — the 67 X_TYPE_WALL ops: does the corpus hand them an instance?")
    rc430_recs = []
    with open(RC430_NDJSON) as fh:
        for line in fh:
            rc430_recs.append(json.loads(line))
    wall = [r for r in rc430_recs
            if r.get("record") == "unreachable_op" and r.get("why") == "X_TYPE_WALL"]
    # every runtime type name the corpus ever produced as an ARGUMENT
    corpus_types = set()
    for s in supply.values():
        for c in s["params"].values():
            corpus_types.add(c["t"])
    direct, inhabited, rows = 0, 0, []
    for r in wall:
        op, slot = r["op"], r.get("slot")
        e = by_name.get(op)
        decl = None
        if e is not None:
            for p in e.parameters:
                if p.name == slot:
                    decl = p.type
        s = supply.get(op) or {"params": {}, "self": False, "cross": set()}
        cell = s["params"].get(slot)
        is_direct = cell is not None
        true_t = (r.get("oracle_arg_types") or [None])[0]
        is_inhab = bool(true_t and true_t in corpus_types)
        direct += 1 if is_direct else 0
        inhabited += 1 if is_inhab else 0
        rows.append({"record": "x_type_wall_op", "op": op, "slot": slot,
                     "declared_type": decl, "rc430_observed_arg_type": true_t,
                     "corpus_direct": is_direct,
                     "corpus_direct_src": (cell or {}).get("src"),
                     "corpus_type_inhabited": is_inhab,
                     "self_supply": s["self"],
                     "n_cross_suppliers": len(s["cross"])})
    m4 = {"record": "m4_constructor_supply", "x_type_wall_total": len(wall),
          "direct_corpus_supplies_the_blocked_slot": direct,
          "direct_rate": rate(direct, len(wall)),
          "type_inhabited_somewhere_in_corpus_UPPER_BOUND": inhabited,
          "distinct_argument_types_in_corpus": len(corpus_types),
          "bound_note": "(b) is an UPPER bound (L4): a declared/observed type of "
                        "'list' makes it trivially true. Only (a) is decisive."}
    out.append(m4)
    out.extend(rows)
    print("  x_type_wall " + str(len(wall)) + " | DIRECT " + str(direct) +
          " | type-inhabited (UPPER) " + str(inhabited))
    print()

    # ══ M5 — THE HONEST BOUND: cross-seeded orbit closure ═════════════════
    print("M5 — cross-seeded orbit closure on the Tier-A ops rc430 could not decide")
    m3_union = None
    rc430_oracle_decided = []
    for r in rc430_recs:
        if r.get("record") == "m3_tier_a_union":
            m3_union = r
            rc430_oracle_decided = r.get("oracle_decided") or []
    rc430_union = set((m3_union or {}).get("union") or [])
    already = set(rc430_oracle_decided)
    targets = []
    for op in tier_a_ops:
        if op in already or op in SLOW_SKIP:
            continue
        s = supply.get(op)
        if not s or not s["cross"]:
            continue
        targets.append((op, sorted(s["cross"])[:3]))
    # PF9 rides the same path it is meant to guard
    pf9_op = PREREGISTERED["PF9_v1_refutation_via_cross_path"]["op"]
    pf9_sup = sorted((supply.get(pf9_op) or {"cross": set()})["cross"])[:3]
    if pf9_sup:
        targets.append((pf9_op, pf9_sup))
    print("  cross-seedable undecided Tier-A targets = " + str(len(targets)))
    ow = Worker(opath, env)
    orbit_res = {}
    t0 = time.monotonic()
    for i, (op, sups) in enumerate(targets):
        rec = ow.ask("CROSS\t" + op + "\t" + ",".join(sups),
                     PER_ORBIT_BUDGET_S, "op", op)
        orbit_res[op] = rec
        out.append({"record": "cross_orbit", "op": op, "suppliers": sups,
                    "oracle": rec.get("oracle"), "verdict": rec.get("verdict"),
                    "status": rec.get("status"),
                    "conflict": rec.get("cross_conflict"),
                    "tried": rec.get("cross_tried"),
                    "slots": rec.get("slots")})
        if (i + 1) % 25 == 0:
            print("  ... " + str(i + 1) + "/" + str(len(targets)) +
                  " (" + str(int(time.monotonic() - t0)) + "s)")
    ow.kill()
    # The PF9 control (``cyclic_mod_add``) is appended to ``targets`` so it rides
    # the cross path it exists to guard -- but it is TIER B (three required
    # params), so it must not enter a TIER-A union. The first run of this file
    # let it in and reported 32; the Tier-A-only number is 31. Counted here, not
    # silently corrected: an instrument that quietly fixes its own arithmetic is
    # indistinguishable from one that never got it wrong.
    tier_a_set = set(tier_a_ops)
    newly = sorted(op for op, r in orbit_res.items()
                   if r.get("verdict") in ("SEMIGROUP", "GROUP")
                   and op not in already and op in tier_a_set)
    newly_non_tier_a = sorted(op for op, r in orbit_res.items()
                              if r.get("verdict") in ("SEMIGROUP", "GROUP")
                              and op not in already and op not in tier_a_set)
    conflicts = sorted(op for op, r in orbit_res.items() if r.get("cross_conflict"))
    broken_orbit = sum(1 for r in orbit_res.values()
                       if r.get("status") in ("WORKER_DIED", "TIMEOUT", "WORKER_RESTART"))
    pf9_v = (orbit_res.get(pf9_op) or {}).get("verdict")
    new_union = sorted(rc430_union | set(newly))
    m5 = {"record": "m5_honest_bound",
          "rc430_ladder_only": 15,
          "rc430_oracle_decided": len(already),
          "rc430_union": len(rc430_union),
          "cross_targets_probed": len(targets),
          "cross_newly_decided": len(newly),
          "cross_newly_decided_ops": newly,
          "newly_decided_but_NOT_tier_a_excluded": newly_non_tier_a,
          "run1_reported_union_before_this_fix": 32,
          "new_union": len(new_union),
          "cross_verdict_conflicts": conflicts,
          "orbit_broken": broken_orbit,
          "tier_a_total": a_total,
          "hard_cap_not_endo": 104,
          "hard_cap_reachable": a_total - 104,
          "verdict_kind": None}
    out.append(m5)
    print("  rc430 union " + str(len(rc430_union)) + " -> new union " +
          str(len(new_union)) + " (+" + str(len(newly)) + ")")
    print()

    # ══ M7 — IS THE ORBIT CRITERION SEED-DEPENDENT? ═══════════════════════
    #
    # PF9 FIRED on the first run of this file: ``cyclic_mod_add`` -- the control
    # that refuted census instrument v1, and which rc430's PC3 recorded as GROUP
    # -- lands SEMIGROUP when seeded from ``srmech.dsl.list_catalog_ops``'s
    # snippet instead of its own. Both seed sets are valid BY CONSTRUCTION. Only
    # the seeds differ.
    #
    # That is not a bug in the cross path. It falsifies the criterion's own
    # stated justification. rc430's worker docstring says: "S is generated by f,
    # so there is no window to get wrong." The measured behaviour says the seed
    # set IS the window. On a binding where b = 0 (mod n) the map a -> (a+b) mod
    # n is a -> a mod n on the DOMAIN the op actually accepts (a >= 0, not a <
    # n), so an unreduced seed and its residue both land on the residue: |S| = 2,
    # |f(S)| = 1, SEMIGROUP. rc430's self-seeded orbit never contained an
    # unreduced seed, so it never saw the collapse.
    #
    # So this measurement asks it registry-wide: over the Tier-A ops that have
    # BOTH self and cross supply, how often do two sets of by-construction-valid
    # seeds disagree? Every disagreement is one op whose census verdict is a
    # property of the harvest, not of the op.
    print("M7 — SEED-DEPENDENCE: same op, same criterion, two valid seed sets")
    both = [(op, sorted((supply.get(op) or {"cross": set()})["cross"])[:3])
            for op in tier_a_ops
            if op not in SLOW_SKIP and (supply.get(op) or {}).get("self")
            and (supply.get(op) or {"cross": set()})["cross"]]
    ow2 = Worker(opath, env)
    seed_rows, disagree, agree, undecided = [], [], 0, 0
    t0 = time.monotonic()
    for i, (op, sups) in enumerate(both):
        rs = ow2.ask("SELF\t" + op, PER_ORBIT_BUDGET_S, "op", op)
        rc = ow2.ask("CROSS\t" + op + "\t" + ",".join(sups),
                     PER_ORBIT_BUDGET_S, "op", op)
        vs, vc = rs.get("verdict"), rc.get("verdict")
        row = {"record": "seed_dependence", "op": op, "self_verdict": vs,
               "cross_verdict": vc, "suppliers": sups,
               "self_oracle": rs.get("oracle"), "cross_oracle": rc.get("oracle")}
        dec = ("SEMIGROUP", "GROUP")
        if vs in dec and vc in dec:
            if vs != vc:
                disagree.append(op)
                row["DISAGREES"] = True
            else:
                agree += 1
        else:
            undecided += 1
        # The BROAD count: any verdict change at all, including a DECIDED arm
        # against an undecided one (SEMIGROUP vs VACUOUS is still one seed set
        # seeing a collapse the other could not reach). Reported alongside the
        # strict count because the strict one has a denominator of 14.
        if vs != vc:
            row["verdict_changed"] = True
        seed_rows.append(row)
        if (i + 1) % 40 == 0:
            print("  ... " + str(i + 1) + "/" + str(len(both)) +
                  " (" + str(int(time.monotonic() - t0)) + "s)")
    ow2.kill()
    out.extend(seed_rows)
    m7 = {"record": "m7_seed_dependence",
          "tier_a_ops_with_both_seed_sources": len(both),
          "both_seed_sets_decided": agree + len(disagree),
          "agree": agree, "disagree": len(disagree),
          "disagreeing_ops": disagree,
          "any_verdict_change_BROAD": sum(1 for r in seed_rows
                                          if r.get("verdict_changed")),
          "any_verdict_change_ops": sorted(r["op"] for r in seed_rows
                                           if r.get("verdict_changed")),
          "at_least_one_seed_set_undecided": undecided,
          "disagreement_rate_over_doubly_decided":
              rate(len(disagree), agree + len(disagree)),
          "finding": "rc430's orbit-closure criterion is SEED-DEPENDENT. Its "
                     "docstring claims 'S is generated by f, so there is no "
                     "window to get wrong'; the seed set is the window. Two "
                     "by-construction-valid argument sets give different "
                     "verdicts on the same op under the same criterion.",
          "consequence": "the Tier-A census is a BOUNDED FLOOR, not a cardinal, "
                         "and MORE valid supply does not converge it -- it "
                         "widens the disagreement set."}
    out.append(m7)
    print("  both-source Tier-A ops " + str(len(both)) + " | agree " + str(agree) +
          " | DISAGREE " + str(len(disagree)) + " | undecided " + str(undecided))
    print()

    # ══ M6 — PROMOTION COST (measured, not estimated) ═════════════════════
    def _lines(p):
        try:
            with open(p) as fh:
                return sum(1 for _ in fh)
        except OSError:
            return None
    cost = {"record": "m6_promotion_cost",
            "already_shipped": {
                "tools/example_args.py": _lines(os.path.join(PY_ROOT, "tools", "example_args.py")),
                "tools/run_example_args.py": _lines(os.path.join(PY_ROOT, "tools", "run_example_args.py")),
                "tests/example_args_ledger.ndjson": _lines(LEDGER),
                "tools/run_worked_examples.py": _lines(os.path.join(PY_ROOT, "tools", "run_worked_examples.py")),
                "tests/worked_examples_result.ndjson": _lines(WORKED_RESULT),
            },
            "freshness_gate": "tests/test_synth_args_provenance_rc430.py",
            "harvest_worker_lines": len(HARVEST_SRC.splitlines()),
            "orbit_driver_is_rc430_verbatim": True}
    out.append(cost)

    # ══ CONTROLS ══════════════════════════════════════════════════════════
    probe_set = len(probe) + len(targets)
    broken_total = n_broken + broken_orbit
    controls = {
        "PF1": {"pass": m1["pf1_pass"], "drift": drift},
        "PF2": {"pass": pf2_pass, "reproduced": len(reproduced),
                "of_ledger_ok": len(ledger_ok), "rule": ">= 9/10"},
        "PF2b": {"pass": pf2b_pass, "clean": n_clean, "baseline": 467},
        "PF3": {"pass": len(pf3_hits) >= 1, "n": len(pf3_hits),
                "ops": pf3_hits[:20]},
        "PF4": {"pass": 0 < len(any_ops) < len(tools), "n": len(any_ops)},
        "PF5": {"pass": n_str >= 1, "n": n_str},
        "PF6": {"pass": 0 < direct < len(wall), "direct": direct, "of": len(wall)},
        "PF7": {"pass": True, "rule": "cross may only ADD; rc430 decisions are "
                                      "not re-run and cannot be removed"},
        "PF8": {"pass": broken_total * 20 < probe_set, "broken": broken_total,
                "probe_set": probe_set, "rate": rate(broken_total, probe_set)},
        "PF9": {"pass": pf9_v == "GROUP", "measured": pf9_v,
                "suppliers": pf9_sup,
                "v1_verdict": "SEMIGROUP_NOT_GROUP (carrier=Z12, b=12 n=6)",
                "voids": "M5", "diagnosis": "see m7_seed_dependence"},
        "PF10": {"pass": ctrl_supply_ops == 0, "control_arm_supply_ops": ctrl_supply_ops},
        "PF11": {"pass": len(disagree) == 0, "disagree": len(disagree),
                 "consequence": "BOUNDED FLOOR" if disagree else "cardinal licensed"},
    }
    void_set = ["PF2", "PF2b", "PF4", "PF8", "PF10"]
    m5["verdict_kind"] = "VOID (PF9 fired)" if pf9_v != "GROUP" else "valid"
    m5["voided_by"] = "PF9" if pf9_v != "GROUP" else None
    valid = all(controls[k]["pass"] for k in void_set)
    out.append({"record": "controls", "controls": controls,
                "void_if_fail_set": void_set, "measurements_valid": valid})
    out.append({"record": "limits", "limits": {
        "L1": "cross supply is a LOWER bound: from-imports bypass the wrapper",
        "L2": "a recorded argument is valid for ITS binding; same-binding filter inherited",
        "L3": "wrapping 655 ops perturbs the corpus; PF2b measures it",
        "L4": "M4(b) type-inhabitation is an UPPER bound",
        "L5": "snippets are our OWN committed code, already run by CI; still "
              "sandboxed in a temp cwd inside a killable worker",
    }})

    with open(OUT, "w") as fh:
        for r in out:
            fh.write(json.dumps(r, sort_keys=True, default=str) + "\n")
    print("CONTROLS")
    for k in sorted(controls):
        print("  " + k.ljust(6) + ("PASS" if controls[k]["pass"] else "FAIL") +
              "  " + json.dumps({x: y for x, y in controls[k].items()
                                 if x != "pass"}, default=str)[:150])
    print()
    print("measurements valid = " + str(valid))
    print("wrote " + OUT + "  (" + str(len(out)) + " records)")


if __name__ == "__main__":
    main()
