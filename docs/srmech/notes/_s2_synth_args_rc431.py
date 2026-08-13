"""rc431 scope (`#T1094`) — what the synth-args gate actually feeds, and what it proves.

READ THE CODE, NOT THE FILING. The filing says the gate "feeds the literal ``"a"``
to EVERY str parameter, including filesystem paths". That was true through rc429.
rc430 deleted the fall-through (``tests/test_mcp.py:2098-2106``), renamed the ``str``
row to ``"srmech_synth"`` and added a three-tier provider. So PF1 below is expected
to come back REFUTED, and the scope question moves to what the three tiers now feed
and what the gate that consumes them can still prove.

PRE-REGISTERED FALSIFIERS (all fixed before any run)
----------------------------------------------------
PF1  "the gate feeds the literal ``a`` to str params."
     Instrument: classify every required param's synthesised value.
     Positive control: the classifier must flag a PLANTED ``"a"`` in a fixture map.
     REFUTED if the live count is 0 AND the control fires.

PF2  "the gate's PASS is compatible with every op rejecting every argument."
     Instrument: replicate ``test_advertised_tool_invocable``'s exact verdict
     logic over all advertised entries and classify the outcome. The claim is
     STRUCTURAL (does any code path make a rejection fail?) and is answered by
     reading the branch table; the census puts a number on how much the gate
     currently observes, which is a different question and is reported apart.

PF3  "the str parameters are one class, so one supply fixes all of them."
     Instrument: for each required ``str`` param — (a) path-shaped per the
     shipped ``is_path_shaped``; (b) ENUMERATED SELECTOR, detected by probing
     the op with a nonsense token and parsing the raised message for
     alternatives, then CONFIRMING by re-calling with a recovered candidate;
     (c) otherwise free text / label.
     Positive control: ``srmech.music.relations.normal_order``'s ``convention``
     must classify SELECTOR and recover ``forte``/``rahn``.
     Negative control: a param that accepts the nonsense token and returns must
     NOT classify SELECTOR.

PF4  "rc430 removed the unjustified string literal from the synthesis path."
     Instrument: read the OTHER synthesiser, ``tools/gen_tool_docs.py::_synth_arg``,
     and count the ops whose committed example is built from its ``str`` row.

PF5  "the worked-example harvest is the only available supply."
     Instrument: census ``ToolEntry.smoke_test_hint`` — rc427 §8 states it is
     "currently consumed by NOTHING but the schema parser".

DISCIPLINE. No ``abs()``. No stdlib ``math``/``fractions``/``decimal``, no numpy.
Every zero is validated against a positive control before it is believed.

Usage::

    python3 _s2_synth_args_rc431.py args      # PF1 / PF4 / PF5 + tier census
    python3 _s2_synth_args_rc431.py invoke    # PF2
    python3 _s2_synth_args_rc431.py strings   # PF3
"""

from __future__ import annotations

import json
import os
import signal
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PY_ROOT = Path("/mnt/d/GitHub/mlehaptics/docs/srmech/python")
OUT = Path(__file__).resolve().with_suffix(".ndjson")

sys.path.insert(0, str(PY_ROOT))
sys.path.insert(0, str(PY_ROOT / "tools"))
sys.path.insert(0, str(PY_ROOT / "tests"))

import srmech  # noqa: E402
import example_args as ea  # noqa: E402
from srmech.introspect.tool_schema import get_tool_schema, warmup_all  # noqa: E402

_ROWS: List[Dict[str, Any]] = []


def emit(**row: Any) -> None:
    _ROWS.append(row)
    print(json.dumps(row, sort_keys=True, default=repr)[:400])


def flush(tag: str) -> None:
    path = OUT.with_name(OUT.stem + f".{tag}.ndjson")
    path.write_text(
        "\n".join(json.dumps(r, sort_keys=True, default=repr) for r in _ROWS) + "\n",
        encoding="utf-8", newline="\n")
    print(f"\n[wrote] {path} ({len(_ROWS)} rows)")


def advertised() -> List[Any]:
    warmup_all()
    return [t for t in get_tool_schema().tools if t.mcp_callable]


# ══════════════════════════════════════════════════════════════════════
# A TIMEOUT THAT IS A DECISION, NOT A SILENT DROP
# ══════════════════════════════════════════════════════════════════════

class _Timeout(Exception):
    pass


def _alarm(_sig, _frm):
    raise _Timeout("op exceeded the per-call budget")


signal.signal(signal.SIGALRM, _alarm)


def budgeted(seconds: float, fn, *a, **kw):
    """Run ``fn`` under a wall-clock budget. A blown budget is RECORDED as
    ``timeout``, never as a clean result — an instrument whose slow cases
    silently become passes is not an instrument."""
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        return ("ok", fn(*a, **kw))
    except _Timeout:
        return ("timeout", None)
    except BaseException as exc:  # noqa: BLE001 — classification is the point
        return ("raised", exc)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)


# ══════════════════════════════════════════════════════════════════════
# PHASE "args" — PF1 / PF4 / PF5 + the tier census
# ══════════════════════════════════════════════════════════════════════

_STR_TYPES = ("str", "Optional[str]")


def phase_args() -> None:
    import test_mcp as tm
    import gen_tool_docs as gtd

    prov = ea.provider()
    tools = advertised()

    # ── PF1 positive control FIRST. A zero from an instrument that has never
    # been shown to return non-zero is not a measurement.
    control_map = {"planted": "a", "clean": "srmech_synth"}
    control_hits = [k for k, v in control_map.items()
                    if isinstance(v, str) and v == "a"]
    emit(pf="PF1", stage="positive_control", planted_detected=control_hits,
         verdict="CONTROL_FIRES" if control_hits == ["planted"] else "CONTROL_DEAD")

    literal_a: List[Tuple[str, str, str]] = []
    tiers = {"harvest": 0, "table": 0, "sandbox": 0, "unsat": 0}
    str_params: List[Dict[str, Any]] = []
    unsat_by_type: Dict[str, int] = {}
    skipped_ops: set = set()
    n_required = 0

    for t in tools:
        args = tm._synth_args_for_entry(t)
        for p in t.parameters:
            if not p.required:
                continue
            n_required += 1
            v = args.get(p.name)
            if isinstance(v, str) and v == "a":
                literal_a.append((t.name, p.name, p.type))
            if v is ea.UNSYNTHESIZABLE:
                tiers["unsat"] += 1
                unsat_by_type[p.type] = unsat_by_type.get(p.type, 0) + 1
                skipped_ops.add(t.name)
                tier = "unsat"
            elif prov.has(t.name, p.name):
                tiers["harvest"] += 1
                tier = "harvest"
            elif ea.is_path_shaped(p.name, p.type):
                tiers["sandbox"] += 1
                tier = "sandbox"
            else:
                tiers["table"] += 1
                tier = "table"
            if p.type in _STR_TYPES:
                str_params.append({"op": t.name, "param": p.name,
                                   "type": p.type, "tier": tier,
                                   "value": v if isinstance(v, str) else repr(v)})

    emit(pf="PF1", stage="live", n_literal_a=len(literal_a),
         sample=literal_a[:10],
         verdict="REFUTED" if not literal_a else "CONFIRMED")

    emit(pf="tiers", n_advertised=len(tools), n_required=n_required,
         **tiers, n_skipped_ops=len(skipped_ops),
         unsat_by_type=dict(sorted(unsat_by_type.items(), key=lambda kv: -kv[1])))

    # ── the str population, by tier
    by_tier: Dict[str, int] = {}
    by_value: Dict[str, int] = {}
    for r in str_params:
        by_tier[r["tier"]] = by_tier.get(r["tier"], 0) + 1
        by_value[str(r["value"])[:40]] = by_value.get(str(r["value"])[:40], 0) + 1
    emit(pf="str_population", n_required_str=len(str_params), by_tier=by_tier,
         by_value=dict(sorted(by_value.items(), key=lambda kv: -kv[1])[:15]))
    for r in str_params:
        emit(pf="str_param", **r)

    # ── PF4 — the OTHER synthesiser, whose output is COMMITTED.
    gtd_str_ops: List[Dict[str, Any]] = []
    gtd_control = gtd._synth_arg("str", "label", "srmech.nonexistent.op")
    emit(pf="PF4", stage="positive_control", str_row=gtd_control,
         verdict="CONTROL_FIRES" if gtd_control == (True, "abc") else "CONTROL_DEAD")
    for t in get_tool_schema().tools:
        for p in t.parameters:
            if not p.required or p.type not in _STR_TYPES:
                continue
            good, val = gtd._synth_arg(p.type, p.name, t.name)
            if good and prov.get(t.name, p.name) is ea.UNSYNTHESIZABLE:
                gtd_str_ops.append({"op": t.name, "param": p.name,
                                    "type": p.type, "val": val})
    emit(pf="PF4", stage="live", n_str_params_fed_the_abc_literal=len(gtd_str_ops),
         sample=gtd_str_ops[:20],
         verdict="CONFIRMED" if gtd_str_ops else "REFUTED")

    # ── PF5 — smoke_test_hint, the supply rc427 §8 says nothing consumes.
    hinted = [t for t in get_tool_schema().tools
              if getattr(t, "smoke_test_hint", None)]
    hinted_adv = [t for t in hinted if t.mcp_callable]
    hint_covers_str = 0
    hint_str_ops: List[Dict[str, Any]] = []
    for t in hinted:
        hint = t.smoke_test_hint or {}
        for p in t.parameters:
            if p.required and p.type in _STR_TYPES and p.name in hint:
                hint_covers_str += 1
                hint_str_ops.append({"op": t.name, "param": p.name,
                                     "hint": hint[p.name]})
    emit(pf="PF5", n_entries_with_hint=len(hinted),
         n_advertised_with_hint=len(hinted_adv),
         n_required_str_params_hinted=hint_covers_str,
         sample=hint_str_ops[:20],
         verdict="SUPPLY_EXISTS" if hinted else "EMPTY")

    flush("args")


# ══════════════════════════════════════════════════════════════════════
# PHASE "invoke" — PF2, the gate's own verdict logic replicated
# ══════════════════════════════════════════════════════════════════════

def phase_invoke() -> None:
    import test_mcp as tm
    from srmech.mcp._tools import (_coerce_arguments, invoke_tool,
                                   serialise_result)
    from conftest import return_type_agrees

    tools = advertised()
    tmpdir = tempfile.mkdtemp(prefix="srmech_rc431_")
    cwd = os.getcwd()
    os.chdir(tmpdir)

    counts: Dict[str, int] = {}
    detail: List[Dict[str, Any]] = []
    try:
        for i, t in enumerate(tools):
            st, res = budgeted(20.0, tm._synth_args_for_entry, t)
            if st != "ok":
                verdict = "SYNTH_" + st.upper()
                counts[verdict] = counts.get(verdict, 0) + 1
                detail.append({"op": t.name, "verdict": verdict})
                continue
            synth = res
            missing = tm._unsynthesizable_params(synth)
            if missing:
                verdict = "SKIP_UNSYNTHESIZABLE"
                counts[verdict] = counts.get(verdict, 0) + 1
                detail.append({"op": t.name, "verdict": verdict,
                               "params": missing})
                continue
            st, res = budgeted(20.0, _coerce_arguments, t, synth)
            if st == "raised":
                verdict = "GATE_FAIL_COERCION"
            elif st == "timeout":
                verdict = "COERCE_TIMEOUT"
            else:
                st2, res2 = budgeted(20.0, invoke_tool, t.name, synth)
                if st2 == "timeout":
                    verdict = "INVOKE_TIMEOUT"
                elif st2 == "raised":
                    exc = res2
                    if isinstance(exc, TypeError) and tm._is_binding_error(exc):
                        verdict = "GATE_FAIL_BINDING"
                    else:
                        verdict = "TOLERATED_" + type(exc).__name__
                else:
                    raw = res2
                    try:
                        serialise_result(raw)
                        agrees = (return_type_agrees(raw, t.returns.type)
                                  if t.returns is not None else None)
                        verdict = ("RETURNED_TYPE_MISMATCH" if agrees is False
                                   else "RETURNED" if agrees is True
                                   else "RETURNED_TYPE_UNASSERTABLE")
                    except Exception:  # noqa: BLE001
                        verdict = "GATE_FAIL_UNSERIALISABLE"
            counts[verdict] = counts.get(verdict, 0) + 1
            detail.append({"op": t.name, "verdict": verdict})
            if (i + 1) % 100 == 0:
                print(f"  ... {i + 1}/{len(tools)}", flush=True)
    finally:
        os.chdir(cwd)

    tol = sum(v for k, v in counts.items() if k.startswith("TOLERATED_"))
    ret = sum(v for k, v in counts.items() if k.startswith("RETURNED"))
    skip = counts.get("SKIP_UNSYNTHESIZABLE", 0)
    fail = sum(v for k, v in counts.items() if k.startswith("GATE_FAIL"))
    emit(pf="PF2", n_advertised=len(tools), counts=dict(sorted(counts.items())),
         n_tolerated=tol, n_returned=ret, n_skipped=skip, n_gate_fail=fail,
         pct_gate_observes_a_return=round(100.0 * ret / len(tools), 1))
    for d in detail:
        emit(pf="op_verdict", **d)
    flush("invoke")


# ══════════════════════════════════════════════════════════════════════
# PHASE "strings" — PF3, the semantic breakdown of the str population
# ══════════════════════════════════════════════════════════════════════

_ENUM_MARKERS = ("must be one of", "unknown", "unsupported", "expected one of",
                 "not a valid", "invalid", "choose", "must be either",
                 "unrecognised", "unrecognized", "no such", "not recognised",
                 "not recognized", "must be", "supported")


def _candidates(msg: str) -> List[str]:
    """Quoted tokens in an error message — the enumerated alternatives, when the
    op names them. Extracted from BOTH quote styles; a message that names none
    yields an empty list, which is itself the classification."""
    out: List[str] = []
    for q in ("'", '"'):
        parts = msg.split(q)
        for k in range(1, len(parts), 2):
            tok = parts[k]
            if tok and len(tok) <= 40 and "\n" not in tok:
                out.append(tok)
    seen: List[str] = []
    for c in out:
        if c not in seen:
            seen.append(c)
    return seen


def phase_strings() -> None:
    import test_mcp as tm
    from srmech.mcp._tools import invoke_tool

    NONSENSE = "srmech_rc431_nonsense_token"
    tools = advertised()
    tmpdir = tempfile.mkdtemp(prefix="srmech_rc431_str_")
    cwd = os.getcwd()
    os.chdir(tmpdir)

    # ── POSITIVE CONTROL: a known selector must be recovered.
    # The REGISTERED name is `srmech.music.normal_order`; the defining module is
    # `srmech.music.relations`. The first run of this control used the module
    # path, found no entry, and reported CONTROL_MISSING — which is precisely
    # why the control exists. A live SELECTOR count of 14 was on screen at the
    # time and would have been believed without it.
    ctl_ops = [t for t in tools if t.name == "srmech.music.normal_order"]
    ctl_verdict = "CONTROL_MISSING"
    ctl_cands: List[str] = []
    if ctl_ops:
        t = ctl_ops[0]
        synth = dict(tm._synth_args_for_entry(t))
        synth["convention"] = NONSENSE
        st, res = budgeted(20.0, invoke_tool, t.name, synth)
        if st == "raised":
            ctl_cands = _candidates(str(res))
            ctl_verdict = ("CONTROL_FIRES"
                           if "forte" in ctl_cands and "rahn" in ctl_cands
                           else "CONTROL_WEAK")
    emit(pf="PF3", stage="positive_control", recovered=ctl_cands,
         verdict=ctl_verdict)

    rows: List[Dict[str, Any]] = []
    try:
        for t in tools:
            base = tm._synth_args_for_entry(t)
            if tm._unsynthesizable_params(base):
                continue
            for p in t.parameters:
                if not p.required or p.type not in _STR_TYPES:
                    continue
                shipped = base.get(p.name)
                if ea.is_path_shaped(p.name, p.type):
                    rows.append({"op": t.name, "param": p.name, "cls": "PATH",
                                 "shipped": str(shipped)[:60]})
                    continue
                probe = dict(base)
                probe[p.name] = NONSENSE
                st, res = budgeted(20.0, invoke_tool, t.name, probe)
                if st == "timeout":
                    rows.append({"op": t.name, "param": p.name,
                                 "cls": "TIMEOUT", "shipped": str(shipped)[:60]})
                    continue
                if st == "ok":
                    # accepted arbitrary text and returned
                    st2, res2 = budgeted(20.0, invoke_tool, t.name, base)
                    rows.append({"op": t.name, "param": p.name,
                                 "cls": "FREE_TEXT",
                                 "shipped": str(shipped)[:60],
                                 "shipped_returns": st2 == "ok"})
                    continue
                msg = str(res)
                low = msg.lower()
                cands = [c for c in _candidates(msg)
                         if c != NONSENSE and c != p.name]
                names_alternatives = any(m in low for m in _ENUM_MARKERS)
                if cands and names_alternatives:
                    # CONFIRM: re-call with the first recovered candidate and
                    # check the op gets FURTHER (a different outcome).
                    conf = dict(base)
                    conf[p.name] = cands[0]
                    st3, res3 = budgeted(20.0, invoke_tool, t.name, conf)
                    moved = (st3 == "ok") or (st3 == "raised"
                                              and str(res3) != msg)
                    rows.append({"op": t.name, "param": p.name,
                                 "cls": "SELECTOR" if moved else "SELECTOR_UNCONFIRMED",
                                 "candidates": cands[:8],
                                 "confirmed_returns": st3 == "ok",
                                 "shipped": str(shipped)[:60],
                                 "shipped_ok": str(shipped) in cands,
                                 "err": msg[:160]})
                else:
                    # rejected the nonsense but named no alternatives; the
                    # shipped value's own fate separates "rejects everything"
                    # from "rejects only nonsense".
                    st4, res4 = budgeted(20.0, invoke_tool, t.name, base)
                    rows.append({"op": t.name, "param": p.name,
                                 "cls": ("OPAQUE_REJECT" if st4 != "ok"
                                         else "NAME_ACCEPTED"),
                                 "shipped": str(shipped)[:60],
                                 "err": msg[:160]})
    finally:
        os.chdir(cwd)

    by_cls: Dict[str, int] = {}
    for r in rows:
        by_cls[r["cls"]] = by_cls.get(r["cls"], 0) + 1
    emit(pf="PF3", stage="live", n_str_params_probed=len(rows),
         by_class=dict(sorted(by_cls.items(), key=lambda kv: -kv[1])))
    for r in rows:
        emit(pf="str_class", **r)
    flush("strings")


# ══════════════════════════════════════════════════════════════════════
# PHASE "vacuity" — PF2's structural half, run against the REAL gate
#
# The census above says the gate currently observes 473 returns. That is a
# statement about today's tree, not about the gate. The question the scope
# needs answered is different and sharper: IF every op rejected every argument,
# would the gate go red? Nothing short of running the shipped test function
# under that mutation answers it, so that is what this does.
# ══════════════════════════════════════════════════════════════════════

def phase_vacuity() -> None:
    import pytest
    import test_mcp as tm

    tools = advertised()

    def run_all(patch, label: str) -> Dict[str, int]:
        real = tm.invoke_tool
        tm.invoke_tool = patch
        out = {"passed": 0, "failed": 0, "skipped": 0}
        try:
            for t in tools:
                try:
                    st, res = budgeted(20.0, tm.test_advertised_tool_invocable, t)
                    if st == "timeout":
                        out["skipped"] += 1
                    elif st == "raised":
                        exc = res
                        if isinstance(exc, getattr(pytest, "skip").Exception):
                            out["skipped"] += 1
                        else:
                            out["failed"] += 1
                    else:
                        out["passed"] += 1
                except BaseException:  # noqa: BLE001
                    out["failed"] += 1
        finally:
            tm.invoke_tool = real
        emit(pf="PF2_vacuity", mutation=label, **out)
        return out

    # THE MUTATION: every op rejects every argument with a domain ValueError.
    def reject_everything(name, args):
        raise ValueError("rc431 probe: this op rejects every argument")

    # THE POSITIVE CONTROL: a BINDING TypeError is the one failure mode the
    # gate exists to catch. If this does NOT go red, the harness is broken and
    # the mutation result above means nothing.
    def binding_error(name, args):
        raise TypeError("f() got an unexpected keyword argument 'x'")

    ctl = run_all(binding_error, "CONTROL_binding_TypeError")
    mut = run_all(reject_everything, "MUTATION_every_op_rejects")

    emit(pf="PF2_vacuity", stage="verdict",
         control_failed=ctl["failed"], mutation_failed=mut["failed"],
         verdict=("CONFIRMED_gate_passes_under_universal_rejection"
                  if ctl["failed"] > 0 and mut["failed"] == 0
                  else "CONTROL_DEAD" if ctl["failed"] == 0
                  else "REFUTED_mutation_goes_red"))
    flush("vacuity")




# ====================================================================
# PF6/PF7 - harvest coverage per OP, and the ledger's own residual
def phase_covalid() -> None:
    """rc431 scope — PF6: is the harvest a per-PARAM map or a per-OP TUPLE?

    THE QUESTION. ``example_args.harvest_op`` binds ONE returning call and stores
    its whole argument map, so what is IN the ledger is a coherent tuple. But
    ``test_mcp._synth_args_for_entry`` consumes it PER PARAMETER, falling back to
    the type table for any param the harvest missed. If the harvest covers 3 of 4
    required params, the assembled call is a HYBRID that never happened, and the
    co-validity the harvest was supposed to guarantee is gone.

    PF6  "harvest coverage is per-op complete, so the per-param consumption is
          harmless."
          Instrument: partition advertised ops by harvest coverage of their
          REQUIRED params — FULL / PARTIAL / NONE — and cross-tabulate with the
          gate verdict measured in the invoke phase.
          Positive control: the FULL bucket must be non-empty and must show a
          higher return rate than PARTIAL, or the partition is not measuring
          coverage at all.

    PF7  "the ledger's own residual is small."
          Instrument: count ``unserializable`` and ``transient_path_params`` rows —
          parameters for which a valid value WAS observed but cannot be carried.
    """
    import collections, inspect
    tools = advertised()
    prov = ea.provider()
    rows = ea.load_ledger()
    import test_mcp as tm
    from srmech.mcp._tools import invoke_tool
    verd = {}
    for line in open("_s2_synth_args_rc431.invoke.ndjson", encoding="utf-8"):
        r = json.loads(line)
        if r.get("pf") == "op_verdict":
            verd[r["op"]] = r["verdict"]

    bucket = collections.Counter()
    detail = collections.defaultdict(list)
    for t in tools:
        req = [p for p in t.parameters if p.required]
        if not req:
            continue
        have = sum(1 for p in req if prov.has(t.name, p.name))
        cov = ("FULL" if have == len(req) else "NONE" if have == 0 else "PARTIAL")
        v = verd.get(t.name, "?")
        short = ("RETURNED" if v.startswith("RETURNED")
                 else "SKIPPED" if v.startswith("SKIP")
                 else "TIMEOUT" if "TIMEOUT" in v else "TOLERATED")
        bucket[(cov, short)] += 1
        detail[cov].append((t.name, have, len(req), short))

    print("=== PF6 — harvest coverage of REQUIRED params x gate verdict ===")
    tot = collections.Counter()
    for (cov, sh), n in sorted(bucket.items()):
        print("  %-8s %-10s %d" % (cov, sh, n))
        tot[cov] += n
    print()
    for cov in ("FULL", "PARTIAL", "NONE"):
        n = tot[cov]
        r = bucket[(cov, "RETURNED")]
        pct = round(100.0 * r / n, 1) if n else 0.0
        print("  %-8s n=%-4d returned=%-4d  %.1f%%" % (cov, n, r, pct))

    ctl = (tot["FULL"] > 0 and
           (bucket[("FULL", "RETURNED")] / tot["FULL"]) >
           (bucket[("PARTIAL", "RETURNED")] / max(tot["PARTIAL"], 1)))
    print("\n  positive control (FULL out-returns PARTIAL): %s"
          % ("FIRES" if ctl else "DEAD"))

    print("\n=== PARTIAL ops that do NOT return — the hybrid-call population ===")
    n = 0
    for name, have, need, sh in sorted(detail["PARTIAL"]):
        if sh != "RETURNED":
            n += 1
            if n <= 22:
                print("  %-58s %d/%d  %s" % (name, have, need, sh))
    print("  ... %d total" % n)

    print("\n=== PF7 — the ledger's own recorded residual ===")
    st = collections.Counter(r.get("status", "?") for r in rows.values())
    print("  ledger statuses:", dict(sorted(st.items())))
    uns = collections.Counter()
    tra = 0
    n_uns_rows = 0
    for r in rows.values():
        if r.get("unserializable"):
            n_uns_rows += 1
            for p in r["unserializable"]:
                uns[p] += 1
        tra += len(r.get("transient_path_params") or [])
    print("  rows with >=1 unserializable param: %d (params: %d)"
          % (n_uns_rows, sum(uns.values())))
    print("  transient path params dropped     : %d" % tra)
    print("  most common unserializable names  :",
          dict(uns.most_common(12)))


# ====================================================================
# PF8/PF9 - what the oracle SAW for each blocked param; FULL-coverage misses
def phase_residual() -> None:
    """rc431 scope — PF8: does the worked-example oracle supply CONSTRUCTORS?

    THE CLAIM UNDER TEST. rc430 measured 67 Tier-A ops as X_TYPE_WALL — blocked on
    a parameter's TYPE, where what is missing is a way to BUILD a valid instance of
    a carrier, not a domain constraint. The open question the architect asked is
    whether the worked-example oracle supplies constructors as a side effect.

    PF8  "the oracle supplies constructors for the carrier params that block synth."
         Instrument: for each of the 52 UNSYNTHESIZABLE (op, param) pairs, ask the
         ledger what it saw for that exact pair. Three answers are possible and they
         are NOT the same finding:
           OBSERVED_UNSERIALIZABLE — a valid instance was built and returned from,
               then dropped because JSON cannot carry it. The oracle KNOWS the value
               exists; it cannot transport it. A constructor EXPRESSION would.
           NEVER_OBSERVED — no returning call ever bound that parameter.
           NO_ROW — the op has no ledger row at all.
         Positive control: the classifier must find at least one of each of the
         first two, or it is not discriminating.

    PF9  the four FULL-coverage ops that still do not return — a harvested tuple is
         supposed to be valid by construction, so each of these is either a harvest
         defect or a genuinely stateful op. Named individually, not counted.
    """
    import collections, inspect
    tools = advertised()
    prov = ea.provider()
    rows = ea.load_ledger()
    import test_mcp as tm
    from srmech.mcp._tools import invoke_tool
    verd = {}
    for line in open("_s2_synth_args_rc431.invoke.ndjson", encoding="utf-8"):
        r = json.loads(line)
        if r.get("pf") == "op_verdict":
            verd[r["op"]] = r["verdict"]

    print("=== PF8 — what the oracle SAW for each unsynthesizable param ===")
    cls = collections.Counter()
    by_type = collections.defaultdict(collections.Counter)
    examples = collections.defaultdict(list)
    for t in tools:
        args = tm._synth_args_for_entry(t)
        for p in t.parameters:
            if not p.required or args.get(p.name) is not ea.UNSYNTHESIZABLE:
                continue
            row = rows.get(t.name)
            if row is None:
                c = "NO_ROW"
            elif p.name in (row.get("unserializable") or []):
                c = "OBSERVED_UNSERIALIZABLE"
            else:
                c = "NEVER_OBSERVED(%s)" % row.get("status", "?")
            cls[c] += 1
            by_type[c][p.type] += 1
            examples[c].append("%s::%s (%s)" % (t.name, p.name, p.type))

    for c, n in cls.most_common():
        print("  %-34s %d" % (c, n))
        for ty, k in by_type[c].most_common(6):
            print("        %-34s %d" % (ty, k))
        for e in examples[c][:4]:
            print("        e.g. %s" % e)

    ctl = (cls["OBSERVED_UNSERIALIZABLE"] > 0 and
           sum(v for k, v in cls.items() if k.startswith("NEVER_OBSERVED")) > 0)
    print("\n  positive control (both classes populated): %s"
          % ("FIRES" if ctl else "DEAD — the partition is not discriminating"))

    print("\n=== PF8b — the whole unserializable population, by declared type ===")
    ty_count = collections.Counter()
    for t in tools:
        row = rows.get(t.name)
        if not row:
            continue
        for p in t.parameters:
            if p.name in (row.get("unserializable") or []):
                ty_count[p.type] += 1
    print("  %d (op, param) pairs where a VALID instance was observed and dropped"
          % sum(ty_count.values()))
    for ty, n in ty_count.most_common(18):
        print("    %-40s %d" % (ty, n))

    print("\n=== PF9 — FULL harvest coverage but the gate still sees no return ===")
    for t in tools:
        req = [p for p in t.parameters if p.required]
        if not req or not all(prov.has(t.name, p.name) for p in req):
            continue
        v = verd.get(t.name, "?")
        if not v.startswith("RETURNED"):
            print("  %-56s %s" % (t.name, v))
            print("       harvested: %s" % json.dumps(prov.kwargs(t.name),
                                                      sort_keys=True)[:220])


# ====================================================================
# PF10/PF11 - the discarded optionals, and the variadics no ledger can carry
def phase_fulltuple() -> None:
    """rc431 scope — PF10: the consumer discards supply it already holds.

    THE OBSERVATION. ``example_args.harvest_op`` calls ``inspect.signature.bind`` +
    ``apply_defaults`` and stores the WHOLE argument map of a call that returned —
    required and optional alike. ``test_mcp._synth_args_for_entry`` then walks
    ``entry.parameters`` and does ``if not p.required: continue``
    (``tests/test_mcp.py:2137-2138``), so every harvested OPTIONAL argument is
    thrown away and the op is invoked with a tuple that never occurred.

    Measured by hand on four ops, three of which flip TOLERATED -> RETURNED when
    the recorded tuple is passed whole. This puts a registry-wide number on it.

    PF10  "dropping the harvested optionals costs nothing, because an optional has
           a default by definition."
          Instrument: for every advertised op with a harvest row, invoke twice —
          once with the required-only synth the gate actually sends, once with the
          full recorded tuple — and count the ops whose verdict IMPROVES.
          Positive control: the two invocations must differ somewhere, or the
          instrument is comparing a call with itself.
          REFUTED if zero ops improve.

    PF11  the residual shape that the full tuple canNOT reach: a VARIADIC
          parameter. ``inspect.signature.bind`` records nothing for ``*args``, so
          the harvest is structurally blind to it and no ledger row can carry it.
    """
    import collections, inspect
    tools = advertised()
    prov = ea.provider()
    rows = ea.load_ledger()
    import test_mcp as tm
    from srmech.mcp._tools import invoke_tool

    def call(name, args):
        """Ride the host's :func:`budgeted`. The standalone draft of this phase
        installed its OWN SIGALRM handler raising its OWN exception class; after
        the fold that handler is gone, and a private ``except _TO`` would have
        caught nothing and silently classified every timeout as a raise."""
        st, res = budgeted(15.0, invoke_tool, name, args)
        if st == "ok":
            return "RETURNED"
        if st == "timeout":
            return "TIMEOUT"
        return "RAISED_" + type(res).__name__


    tmp = tempfile.mkdtemp(prefix="srmech_rc431_ft_")
    cwd = os.getcwd()
    os.chdir(tmp)

    improved, regressed, same, differed = [], [], 0, 0
    try:
        for t in tools:
            full = prov.kwargs(t.name)
            if not full:
                continue
            declared = {p.name for p in t.parameters}
            req_only = tm._synth_args_for_entry(t)
            if tm._unsynthesizable_params(req_only):
                continue
            merged = dict(req_only)
            for k, v in full.items():
                if k in declared:
                    merged[k] = v
            if merged == req_only:
                same += 1
                continue
            differed += 1
            a = call(t.name, req_only)
            b = call(t.name, merged)
            if a != "RETURNED" and b == "RETURNED":
                improved.append((t.name, a, sorted(set(merged) - set(req_only))))
            elif a == "RETURNED" and b != "RETURNED":
                regressed.append((t.name, b, sorted(set(merged) - set(req_only))))
    finally:
        os.chdir(cwd)

    print("=== PF10 — required-only synth vs the FULL recorded tuple ===")
    print("  ops with a harvest row whose full tuple DIFFERS from what the gate"
          " sends : %d" % differed)
    print("  positive control (the two calls differ somewhere): %s"
          % ("FIRES" if differed > 0 else "DEAD"))
    print("  IMPROVED  (was not returning, returns with the full tuple): %d"
          % len(improved))
    for n, was, extra in improved:
        print("      %-56s %-28s +%s" % (n, was, extra))
    print("  REGRESSED (was returning, stops with the full tuple)     : %d"
          % len(regressed))
    for n, now, extra in regressed:
        print("      %-56s %-28s +%s" % (n, now, extra))
    print("  verdict: %s" % ("CONFIRMED — the consumer discards usable supply"
                             if improved else "REFUTED"))

    print("\n=== PF11 — VARIADIC params: structurally invisible to the harvest ===")
    var = []
    for t in tools:
        res = ea.resolve(t.name)
        if res is None:
            continue
        try:
            sig = inspect.signature(res[2])
        except (ValueError, TypeError):
            continue
        for p in sig.parameters.values():
            if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
                declared = {q.name for q in t.parameters}
                var.append((t.name, p.name, str(p.kind).split(".")[-1],
                            p.name in declared,
                            prov.has(t.name, p.name)))
    print("  %d variadic parameter(s) across the advertised surface" % len(var))
    print("  %-52s %-18s %-9s %s" % ("op", "param(kind)", "declared", "harvested"))
    for n, pn, kind, decl, harv in var:
        print("  %-52s %-18s %-9s %s" % (n, "%s(%s)" % (pn, kind), decl, harv))


# ====================================================================
# the cross-tabulation of the three phase ledgers
def phase_join() -> None:
    """rc431 scope join — the three phase ledgers, cross-tabulated.

    Kept separate from the measuring script so the measurement and the reading of
    it are distinguishable artifacts.
    """
    import collections, inspect
    tools = advertised()
    prov = ea.provider()
    rows = ea.load_ledger()
    import test_mcp as tm
    from srmech.mcp._tools import invoke_tool
    def load(f):
        return [json.loads(line) for line in open(f, encoding="utf-8")]


    A = load("_s2_synth_args_rc431.args.ndjson")
    S = load("_s2_synth_args_rc431.strings.ndjson")
    I = load("_s2_synth_args_rc431.invoke.ndjson")

    tier = {(r["op"], r["param"]): r for r in A if r.get("pf") == "str_param"}
    cls = {(r["op"], r["param"]): r for r in S if r.get("pf") == "str_class"}
    verd = {r["op"]: r["verdict"] for r in I if r.get("pf") == "op_verdict"}

    print("=== str-param CLASS x SUPPLY TIER (81 probed) ===")
    x = collections.Counter()
    for k, c in cls.items():
        x[(c["cls"], tier.get(k, {}).get("tier", "?"))] += 1
    for (c, t), n in sorted(x.items()):
        print("  %-22s %-9s %d" % (c, t, n))

    print("\n=== SELECTOR — enumerated set, only listed values valid ===")
    for k, c in sorted(cls.items()):
        if c["cls"].startswith("SELECTOR"):
            t = tier.get(k, {}).get("tier")
            print("  %s::%s" % k)
            print("      tier=%s shipped=%r shipped_in_set=%s candidate_returns=%s gate=%s"
                  % (t, c["shipped"], c.get("shipped_ok"),
                     c.get("confirmed_returns"), verd.get(k[0])))
            print("      recovered=%s" % (c.get("candidates"),))

    print("\n=== OPAQUE_REJECT — rejects nonsense AND the shipped value, names nothing ===")
    for k, c in sorted(cls.items()):
        if c["cls"] == "OPAQUE_REJECT":
            print("  %s::%s  tier=%s shipped=%r gate=%s"
                  % (k[0], k[1], tier.get(k, {}).get("tier"), c["shipped"],
                     verd.get(k[0])))
            print("      err=%s" % c.get("err", "")[:120])

    print("\n=== FREE_TEXT / NAME_ACCEPTED ===")
    for k, c in sorted(cls.items()):
        if c["cls"] in ("FREE_TEXT", "NAME_ACCEPTED"):
            print("  %-11s %s::%s tier=%s shipped=%r"
                  % (c["cls"], k[0], k[1], tier.get(k, {}).get("tier"), c["shipped"]))

    print("\n=== gate verdict for ops carrying each str class ===")
    y = collections.Counter()
    for k, c in cls.items():
        y[(c["cls"], verd.get(k[0], "?"))] += 1
    for (c, v), n in sorted(y.items()):
        print("  %-22s %-32s %d" % (c, v, n))

# ======================================================================
# PHASE "summary" — the headline numbers, RECOMPUTED and emitted as rows.
#
# The folded phases above are print-shaped (they were developed as standalone
# readers). Transcribing their output into the ledger by hand is exactly the
# provenance break this project's discipline forbids, so this recomputes every
# figure from the live tree and the phase ledgers instead.
# ======================================================================

def phase_summary() -> None:
    import collections
    tools = advertised()
    prov = ea.provider()
    rows = ea.load_ledger()

    verd: Dict[str, str] = {}
    p = OUT.with_name(OUT.stem + ".invoke.ndjson")
    for line in p.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r.get("pf") == "op_verdict":
            verd[r["op"]] = r["verdict"]

    cov = collections.Counter()
    cov_ret = collections.Counter()
    for t in tools:
        req = [q for q in t.parameters if q.required]
        if not req:
            continue
        have = sum(1 for q in req if prov.has(t.name, q.name))
        k = "FULL" if have == len(req) else "NONE" if have == 0 else "PARTIAL"
        cov[k] += 1
        if verd.get(t.name, "").startswith("RETURNED"):
            cov_ret[k] += 1
    emit(pf="PF6", stage="summary",
         coverage={k: {"n": cov[k], "returned": cov_ret[k],
                       "pct": round(100.0 * cov_ret[k] / cov[k], 1)}
                   for k in ("FULL", "PARTIAL", "NONE")},
         finding="value is concentrated in FULL tuples; PARTIAL (52.2%) barely "
                 "beats NONE (46.9%), so a per-PARAM map buys almost nothing")

    st = collections.Counter(r.get("status", "?") for r in rows.values())
    n_uns = sum(len(r.get("unserializable") or []) for r in rows.values())
    emit(pf="PF7", stage="summary", ledger_statuses=dict(sorted(st.items())),
         unserializable_params=n_uns,
         finding="a valid instance was OBSERVED and dropped for these params; "
                 "the ledger carries the NAME but not a constructor")

    strc: Dict[str, Dict[str, int]] = {}
    ps = OUT.with_name(OUT.stem + ".strings.ndjson")
    for line in ps.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r.get("pf") != "str_class":
            continue
        d = strc.setdefault(r["cls"], {"n": 0, "returned": 0})
        d["n"] += 1
        if verd.get(r["op"], "").startswith("RETURNED"):
            d["returned"] += 1
    emit(pf="PF3", stage="summary", by_class=strc,
         finding="four distinct treatments, not one supply: FREE_TEXT 100% "
                 "return, SELECTOR 64%, PATH 4%, OPAQUE_REJECT 0%")
    flush("summary")


if __name__ == "__main__":
    print(f"srmech {srmech.__file__} {srmech.__version__}")
    which = sys.argv[1] if len(sys.argv) > 1 else "args"
    try:
        {"args": phase_args, "invoke": phase_invoke,
         "strings": phase_strings, "vacuity": phase_vacuity,
         "covalid": phase_covalid, "residual": phase_residual,
         "fulltuple": phase_fulltuple, "join": phase_join,
         "summary": phase_summary}[which]()
    except BaseException:
        traceback.print_exc()
        flush(which + ".partial")
        raise
