#!/usr/bin/env python3
"""GATE SEED for gh #1653 — the numbers the ratchet in
``_1653_gate_spec_rc444.md`` is seeded from, every one of them produced by
EXECUTION on this worktree (srmech 0.9.0rc444, native ABI 17).

WHY THIS EXISTS SEPARATELY FROM THE CENSUS
------------------------------------------
``_1653_chain_census_rc444.py`` and ``_1653_step_forms_rc444.py`` answered
"how big is the gap".  This script answers a different question: "what
exactly does the gate ASSERT, and what value does each assertion start
at".  A gate seeded from a number somebody typed is the failure mode gh
#1653 exists to stop, so every constant the spec ships is emitted here by
the same code shape the gate will run.

It also closes three things the sibling censuses left open, because the
gate depends on them:

  S3  the SCHEMA-VERSION axis on the real descriptors.  Both sibling
      censuses fed ``srmech_chain_catalog_parse`` a wrapper they minted
      with ``chain_schema_version = 1``, so neither measured what a
      bare-C host reading the SHIPPED v2 descriptors actually gets.
      ``co_catalog_body`` (c/src/srmech_compose.c:513) and
      ``co_list_body`` (:675) hard-require ``== 1``; every shipped chain
      declares 2.  Measured here, both wrappers, both entry points.

  S4  ROUTE COINCIDENCE.  The census found that ``_chain_c_eligible``
      (compose.py:1045) and the C op table are two independent gates and
      that widening one alone changes nothing observable.  The gate needs
      that as a SET EQUALITY, and a set equality seeded 0 == 0 is
      vacuous, so this measures the equality AND the positive control
      that proves both sides can be non-empty.

  S2  the OP-TABLE MIRROR by execution.  ``compose._RUN_C_OPS`` is a
      Python literal claiming to describe ``cr_dispatch``
      (c/src/srmech_compose_run.c:581-617).  Nothing reads the C side.
      Measured here by driving a minimal one-step chain per name.

CONFOUND GUARD
--------------
The C calling convention is not re-derived: this module IMPORTS the
census's drivers, which are lifted verbatim from the shipped
``compose._run_chain_native`` and are proven by two positive controls
(literal args + ``@input`` refs, both byte-identical to pure).  Section 0
re-runs those controls and ABORTS before recording anything if either
fails, so no rejection below can be a harness artefact.

DISCIPLINE: no abs(), no numpy, no RNG, no stdlib fractions.  Read-only
apart from the one NDJSON it writes next to itself.

Usage:  cd docs/srmech/python && python3 ../notes/_1653_gate_seed_rc444.py
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY_ROOT = os.path.abspath(os.path.join(HERE, "..", "python"))
if PY_ROOT not in sys.path:
    sys.path.insert(0, PY_ROOT)


def _load_census():
    """Import the census module by path (its name is not importable)."""
    path = os.path.join(HERE, "_1653_chain_census_rc444.py")
    spec = importlib.util.spec_from_file_location("_c1653", path)
    assert spec is not None and spec.loader is not None, path
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_c1653"] = mod
    spec.loader.exec_module(mod)
    return mod


CEN = _load_census()

import srmech                                          # noqa: E402
from srmech.cascade import compose as _compose          # noqa: E402
from srmech.dsl import _cascade_chain as _cc            # noqa: E402
from srmech.dsl import _catalog as _cat                 # noqa: E402

STATUS = CEN.STATUS


# ══════════════════════════════════════════════════════════════════════════
# 0. POSITIVE CONTROLS — the harness must be proven before anything counts
# ══════════════════════════════════════════════════════════════════════════

def positive_controls():
    rows = CEN.positive_controls()
    ok = all(bool(r.get("byte_identical")) for r in rows)
    out = []
    for r in rows:
        rec = dict(r)
        rec["record"] = "positive_control"
        out.append(rec)
    return ok, out


# ══════════════════════════════════════════════════════════════════════════
# 1. THE FORM LEDGER — surface A's 3 step forms x 7 reference namespaces
# ══════════════════════════════════════════════════════════════════════════
#
# One minimal probe per grammar feature.  Each probe is a COMPLETE chain so
# it can be driven through the real Python engine and both real C gates; the
# only thing that varies between probes is the feature under test.

PLAIN = {"class": "N", "op": "rational_add",
         "args": {"a": [1, 2], "b": [1, 3]}}


def _chain(steps, name="probe"):
    return {"name": name, "summary": "gate seed probe", "returns": "q",
            "on_error": "raise", "steps": steps}


#: (probe_id, kind, feature, steps, inputs, row, note)
#:
#: ``row`` is separate from ``inputs`` on purpose.  A first pass gave @row a
#: PARSES_REJECTS verdict purely because the probe ctx carried ``row: null``,
#: which is a HARNESS artefact (cr_resolve_ref walks a NULL row and fails to
#: resolve), not a C grammar gap.  Every namespace probe now supplies the
#: carrier its reference actually needs.
FORM_PROBES = (
    # ---- the three step forms -------------------------------------------
    ("F_plain", "step_form", "plain",
     [dict(PLAIN)], {}, None, "class+op+args"),
    ("F_map", "step_form", "map",
     [{"map_over": "@input.xs", "index": "k",
       "body": [{"class": "N", "op": "rational_add",
                 "args": {"a": [1, 2], "b": [1, 3]}}]}],
     {"xs": [1, 2, 3]}, None, "map_over+body[+index,bind]"),
    ("F_fold", "step_form", "fold",
     [{"fold_class": "N", "fold_op": "rational_add", "fold_init": [0, 1],
       "over": "@input.xs"}],
     {"xs": [[1, 2], [1, 3]]}, None,
     "fold_class+fold_op+fold_init+over"),
    # ---- the seven reference namespaces, each in a PLAIN step -----------
    ("R_row", "ref_namespace", "row",
     [{"class": "N", "op": "rational_add",
       "args": {"a": "@row.a", "b": [1, 3]}}], {}, {"a": [1, 2]},
     "v1; ctx CARRIES a row -- a null row would fail on DATA, not grammar"),
    ("R_input", "ref_namespace", "input",
     [{"class": "N", "op": "rational_add",
       "args": {"a": "@input.a", "b": [1, 3]}}],
     {"a": [1, 2]}, None, "v1"),
    ("R_step", "ref_namespace", "step",
     [dict(PLAIN),
      {"class": "N", "op": "rational_add",
       "args": {"a": "@step[0].output", "b": [1, 3]}}], {}, None, "v1"),
    ("R_catalog", "ref_namespace", "catalog",
     [{"class": "N", "op": "rational_add",
       "args": {"a": "@catalog.anchor", "b": [1, 3]}}], {}, None,
     "v1; no ctx carrier exists for @catalog in EITHER projection -- the "
     "run-side decline at cr_resolve_ref:288 is the grammar, not the data"),
    ("R_idx", "ref_namespace", "idx",
     [{"class": "N", "op": "rational_add",
       "args": {"a": "@idx.k", "b": [1, 3]}}], {}, None,
     "v2; Python legal ONLY in map scope -> see R_idx_scoped"),
    ("R_bind", "ref_namespace", "bind",
     [{"class": "N", "op": "rational_add",
       "args": {"a": "@bind.seed", "b": [1, 3]}}], {}, None,
     "v2; Python legal ONLY in map scope -> see R_bind_scoped"),
    ("R_op", "ref_namespace", "op",
     [{"class": "N", "op": "rational_add",
       "args": {"a": "@op.srmech", "b": [1, 3]}}], {}, None, "v2"),
    # ---- the two scope-corrected v2 probes (Python-side truth) ---------
    ("R_idx_scoped", "ref_namespace_scoped", "idx",
     [{"map_over": "@input.xs", "index": "k",
       "body": [{"class": "N", "op": "rational_pow_uint",
                 "args": {"base": [2, 1], "n": "@idx.k"}}]}],
     {"xs": [1, 2]}, None,
     "the scope Python permits; NOTE the C verdict here is dominated by the "
     "MAP FORM, not by @idx -- read R_idx for the namespace verdict"),
    ("R_bind_scoped", "ref_namespace_scoped", "bind",
     [{"map_over": "@input.xs", "index": "k",
       "bind": {"seed": "@input.s"},
       "body": [{"class": "N", "op": "rational_add",
                 "args": {"a": "@bind.seed", "b": [1, 3]}}]}],
     {"xs": [1, 2], "s": [1, 2]}, None,
     "the scope Python permits; C verdict dominated by the MAP FORM -- read "
     "R_bind for the namespace verdict"),
)


def python_verdict(steps, inputs, row=None):
    """Does the shipped Python engine ACCEPT (parse) this chain, and RUN it?"""
    out = {"py_parse": None, "py_run": None}
    try:
        spec = _compose.parse_chain_spec(_chain(steps))
        out["py_parse"] = "OK"
    except Exception as exc:                            # noqa: BLE001
        out["py_parse"] = "%s: %s" % (type(exc).__name__, exc)
        return out
    try:
        val = _compose.run_chain(spec, row=row,
                                 inputs=dict(inputs))
        out["py_run"] = "OK"
        out["py_value_repr"] = CEN.canonical_repr(val)
    except Exception as exc:                            # noqa: BLE001
        out["py_run"] = "%s: %s" % (type(exc).__name__, exc)
    return out


def measure_form_probes():
    rows = []
    for pid, kind, feature, steps, inputs, row, note in FORM_PROBES:
        ch = _chain(steps, name=pid)
        parse = CEN.c_chain_spec_parse(ch)
        run = CEN.c_chain_run(ch, {"row": row, "inputs": dict(inputs)})
        py = python_verdict(steps, inputs, row=row)
        c_parse_ok = (parse.get("rc") == 0)
        c_run_ok = (run.get("rc") == 0)
        if c_parse_ok and c_run_ok:
            verdict = "EXECUTES"
        elif c_parse_ok:
            verdict = "PARSES_REJECTS"
        else:
            verdict = "UNRECOGNISED"
        rows.append({
            "record": "form_probe", "probe": pid, "kind": kind,
            "feature": feature, "note": note,
            "ctx_row": row,
            "py_parse": py["py_parse"], "py_run": py["py_run"],
            "py_value_repr": py.get("py_value_repr"),
            "c_parse_rc": parse.get("rc"),
            "c_parse_status": parse.get("status"),
            "c_run_rc": run.get("rc"), "c_run_status": run.get("status"),
            "c_run_value_repr": run.get("reconstructed_repr"),
            "verdict": verdict,
            "byte_identical": bool(
                py.get("py_value_repr") is not None
                and run.get("reconstructed_repr") is not None
                and py["py_value_repr"] == run["reconstructed_repr"]),
        })
    return rows


# ══════════════════════════════════════════════════════════════════════════
# 2. THE OP-TABLE MIRROR — measured, not read off the Python literal
# ══════════════════════════════════════════════════════════════════════════

#: Minimal in-table args per Class-N op, so an in-table name reaches rc=0
#: rather than failing on argument shape and looking out-of-table.
_OP_ARGS = {
    "pi_cascade_digits": {"n_digits": 3},
    "exp_series_truncate": {"numerator": 1, "denominator": 2, "num_terms": 4},
    "sin_series_truncate": {"numerator": 1, "denominator": 2, "num_terms": 4},
    "cos_series_truncate": {"numerator": 1, "denominator": 2, "num_terms": 4},
    "log1p_series_truncate": {"numerator": 1, "denominator": 2,
                              "num_terms": 4},
    "atan_series_truncate": {"numerator": 1, "denominator": 2, "num_terms": 4},
    "rational_pow_uint": {"base": [2, 3], "n": 2},
    "rational_add": {"a": [1, 2], "b": [1, 3]},
    "rational_mul": {"a": [1, 2], "b": [1, 3]},
    "rational_div": {"a": [1, 2], "b": [1, 3]},
}

#: Negative controls: names that MUST come back rc=5 (out of table).
_OP_NEGATIVE = ("rational_sub", "gcd", "mod_add", "magnitude",
                "srmech.math.rational.rational_add")


def measure_op_table():
    rows = []
    for op in sorted(_compose._RUN_C_OPS):
        args = _OP_ARGS.get(op)
        assert args is not None, (
            "no probe args for in-table op %r — _RUN_C_OPS grew; add the "
            "minimal arg shape so the mirror stays a measurement" % op)
        ch = _chain([{"class": "N", "op": op, "args": args}], name="op_" + op)
        run = CEN.c_chain_run(ch, {"row": None, "inputs": {}})
        rows.append({"record": "op_probe", "op": op, "side": "claimed_in",
                     "c_run_rc": run.get("rc"),
                     "c_run_status": run.get("status"),
                     "c_dispatches": run.get("rc") != 5})
    for op in _OP_NEGATIVE:
        ch = _chain([{"class": "N", "op": op, "args": {"a": [1, 2],
                                                      "b": [1, 3]}}],
                    name="opneg")
        run = CEN.c_chain_run(ch, {"row": None, "inputs": {}})
        rows.append({"record": "op_probe", "op": op, "side": "negative",
                     "c_run_rc": run.get("rc"),
                     "c_run_status": run.get("status"),
                     "c_dispatches": run.get("rc") != 5})
    return rows


# ══════════════════════════════════════════════════════════════════════════
# 3. THE SCHEMA-VERSION AXIS on the REAL descriptor declaration
# ══════════════════════════════════════════════════════════════════════════

def measure_schema_axis():
    """A real shipped chain, wrapped BOTH ways, through both catalog gates.

    ``co_catalog_body`` (srmech_compose.c:513) and ``co_list_body`` (:675)
    hard-require ``chain_schema_version == 1``; the shipped descriptors all
    declare 2.  Nothing measured that before, because both sibling censuses
    minted their own v1 wrapper.
    """
    rows = []
    specs = _cc.cascade_chain_specs("cyclic_gcd")
    variant, _spec, entry = specs[0]
    ch = CEN.chain_dict_for("cyclic_gcd", variant, entry)
    # Drive the raw export directly (the census helper mints its own v1
    # wrapper, which is exactly why this axis was never measured).
    import ctypes
    lib = _compose._compose_lib("srmech_chain_catalog_parse",
                               "srmech_chain_catalog_parse_arena_bytes")
    for declared in (1, 2):
        wrapper = {"chain_schema_version": declared, "operator_chain": [ch]}
        cj = json.dumps(wrapper, ensure_ascii=False).encode("utf-8")
        ws_bytes = int(lib.srmech_chain_catalog_parse_arena_bytes(len(cj)))
        ws = (ctypes.c_char * ws_bytes)()
        out_cap = max(ws_bytes // 2, 16384)
        out = (ctypes.c_char * out_cap)()
        out_len = ctypes.c_size_t()
        rc = int(lib.srmech_chain_catalog_parse(
            cj, len(cj), ws, ws_bytes, out, out_cap, ctypes.byref(out_len)))
        rows.append({
            "record": "schema_probe_raw", "entry": "srmech_chain_catalog_parse",
            "declared_chain_schema_version": declared,
            "rc": rc, "status": STATUS.get(rc, "rc=%d" % rc),
            "out_len": int(out_len.value),
            "anchor": "c/src/srmech_compose.c:513 co_catalog_body",
        })
    return rows


# ══════════════════════════════════════════════════════════════════════════
# 4. THE CHAIN LEDGER — one row per declared chain VARIANT
# ══════════════════════════════════════════════════════════════════════════

#: The CLOSED decline-code set.  A variant C cannot run must map to exactly
#: one of these, each naming the C source line that produces the refusal.
DECLINE_CODES = {
    "step_form_map": "c/src/srmech_compose.c:299-303 co_build_step "
                     "(required class+op+args); "
                     "c/src/srmech_compose_run.c:722-724 cr_run_steps",
    "step_form_fold": "c/src/srmech_compose.c:299-303 co_build_step; "
                      "c/src/srmech_compose_run.c:722-724 cr_run_steps",
    "ref_namespace_v2": "c/src/srmech_compose.c:135-149 co_match_namespace "
                        "(knows row|input|step|catalog only)",
    "ref_namespace_run": "c/src/srmech_compose_run.c:288 cr_resolve_ref "
                         "(knows row|input|step[N].output only)",
    "op_not_in_c_table": "c/src/srmech_compose_run.c:616 cr_dispatch "
                         "-> SRMECH_ERR_NOT_IMPL",
    "chain_schema_version_2": "c/src/srmech_compose.c:513 co_catalog_body / "
                              ":675 co_list_body (hard == 1)",
}

_V2_NS = ("idx", "bind", "op")


def variant_profile(steps):
    """Static inventory of one variant: forms, namespaces, ops (+ the form of
    step[0], which is the first thing the C run loop sees)."""
    prof = dict(CEN.chain_profile(steps))
    first = None
    for step in (steps or ()):
        first = CEN.step_form(step)
        break
    prof["first_step_form"] = first
    return prof


def classify_decline(prof, parse_rc, run_rc):
    """The single canonical decline code, chosen by FIRST C gate reached.

    Order matters and is the C control flow, not a preference: the parse
    gate runs before the run gate, and inside the run loop the step-shape
    check (:722) runs before the op-table check (:616).
    """
    forms = prof.get("step_forms", {}) or {}
    ns = set(prof.get("ref_namespaces", []) or [])
    v2ns = sorted(n for n in ns if n in _V2_NS)
    first = prof.get("first_step_form")
    if parse_rc == 0 and run_rc == 0:
        return None, []
    codes = []
    if forms.get("map"):
        codes.append("step_form_map")
    if forms.get("fold"):
        codes.append("step_form_fold")
    if v2ns:
        codes.append("ref_namespace_v2")
    codes.append("op_not_in_c_table")
    # The FIRST gate the C control flow reaches:
    if parse_rc != 0:
        if first in ("map", "fold"):
            primary = "step_form_" + first
        elif forms.get("map"):
            primary = "step_form_map"
        elif forms.get("fold"):
            primary = "step_form_fold"
        elif v2ns:
            primary = "ref_namespace_v2"
        else:
            primary = "UNATTRIBUTED"
    else:
        if first in ("map", "fold"):
            primary = "step_form_" + first
        else:
            primary = "op_not_in_c_table"
    return primary, codes


def measure_chain_ledger():
    rows = []
    status = _cc.cascade_catalog_status()
    names = sorted(n for n, s in status.items() if s == "executable")
    for op_name in names:
        specs = _cc.cascade_chain_specs(op_name)
        for variant, spec, entry in specs:
            steps = entry.get("steps", []) or []
            ch = CEN.chain_dict_for(op_name, variant, entry)
            prof = variant_profile(steps)
            parse = CEN.c_chain_spec_parse(ch)
            run = CEN.c_chain_run(ch, {"row": None, "inputs": {}})
            primary, codes = classify_decline(
                prof, parse.get("rc"), run.get("rc"))
            elig = bool(_compose._chain_c_eligible(spec))
            rows.append({
                "record": "chain_ledger",
                "chain": op_name, "variant": variant,
                "key": "%s.%s" % (op_name, variant),
                "c_parse_rc": parse.get("rc"),
                "c_parse_status": parse.get("status"),
                "c_run_rc": run.get("rc"),
                "c_run_status": run.get("status"),
                "c_runs": run.get("rc") == 0,
                "py_c_eligible": elig,
                "decline_primary": primary,
                "decline_all": codes,
                "forms": prof.get("step_forms"),
                "first_step_form": prof.get("first_step_form"),
                "ref_namespaces": prof.get("ref_namespaces"),
                "n_ops": len(prof.get("ops", []) or []),
                "ops_outside_c_table": sorted(
                    set(prof.get("ops", []) or [])
                    - set(_compose._RUN_C_OPS)),
                "anchor": DECLINE_CODES.get(primary, "UNATTRIBUTED"),
            })
    return rows


# ══════════════════════════════════════════════════════════════════════════
# 5. ROUTE COINCIDENCE + its non-vacuity control
# ══════════════════════════════════════════════════════════════════════════

def measure_route_coincidence(ledger):
    c_runs = frozenset(r["key"] for r in ledger if r["c_runs"])
    py_routes = frozenset(r["key"] for r in ledger if r["py_c_eligible"])
    # The control: a synthetic Class-N in-table chain must land in BOTH sets.
    ctl_steps = [{"class": "N", "op": "rational_add",
                  "args": {"a": [1, 2], "b": [1, 3]}}]
    ctl_chain = _chain(ctl_steps, name="route_control")
    ctl_spec = _compose.parse_chain_spec(ctl_chain)
    ctl_elig = bool(_compose._chain_c_eligible(ctl_spec))
    ctl_run = CEN.c_chain_run(ctl_chain, {"row": None, "inputs": {}})
    ctl_native = _compose._run_chain_native(ctl_spec, None, {})
    return {
        "record": "route_coincidence",
        "c_runs": sorted(c_runs), "py_routes": sorted(py_routes),
        "n_c_runs": len(c_runs), "n_py_routes": len(py_routes),
        "sets_equal": c_runs == py_routes,
        "c_runs_not_routed": sorted(c_runs - py_routes),
        "routed_but_c_rejects": sorted(py_routes - c_runs),
        "vacuous_today": (len(c_runs) == 0 and len(py_routes) == 0),
        "control_c_eligible": ctl_elig,
        "control_c_run_rc": ctl_run.get("rc"),
        "control_native_ran": (ctl_native is not _compose._NATIVE_MISS),
        "control_value_repr": CEN.canonical_repr(ctl_native)
        if ctl_native is not _compose._NATIVE_MISS else None,
        "control_proves_non_vacuity": bool(
            ctl_elig and ctl_run.get("rc") == 0
            and ctl_native is not _compose._NATIVE_MISS),
    }


# ══════════════════════════════════════════════════════════════════════════

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ndjson", default=os.path.join(
        HERE, "_1653_gate_seed_rc444.ndjson"))
    args = ap.parse_args()

    ok, controls = positive_controls()
    print("[0] positive controls: %s (%d rows)"
          % ("PASS" if ok else "FAIL", len(controls)))
    if not ok:
        for c in controls:
            print("    %s -> %s" % (c.get("control"), c.get("verdict")))
        print("ABORT: harness unproven; nothing below would be attributable.")
        return 2

    ns = srmech.native_status()
    env = {"record": "environment", "srmech_version": srmech.__version__,
           "has_native": ns.get("has_native"),
           "abi": ns.get("abi_version"), "expected_abi": ns.get("expected_abi"),
           "describe_cascade_catalog":
               srmech.describe().get("cascade_catalog"),
           "engine_schema_version": _compose.ENGINE_SCHEMA_VERSION,
           "supported_schema_versions":
               list(_compose.SUPPORTED_SCHEMA_VERSIONS),
           "run_c_ops": sorted(_compose._RUN_C_OPS),
           "reference_pattern": _compose._REFERENCE_PATTERN.pattern,
           "map_keys": list(_compose._MAP_KEYS),
           "fold_keys": list(_compose._FOLD_KEYS),
           "decline_codes": sorted(DECLINE_CODES)}

    forms = measure_form_probes()
    ops = measure_op_table()
    schema = measure_schema_axis()
    ledger = measure_chain_ledger()
    route = measure_route_coincidence(ledger)

    n_var = len(ledger)
    n_runs = sum(1 for r in ledger if r["c_runs"])
    n_decl = sum(1 for r in ledger if r["decline_primary"] is not None)
    n_unatt = sum(1 for r in ledger
                  if r["decline_primary"] == "UNATTRIBUTED")
    n_parse_ok = sum(1 for r in ledger if r["c_parse_rc"] == 0)
    by_code = {}
    for r in ledger:
        p = r["decline_primary"]
        if p is not None:
            by_code[p] = by_code.get(p, 0) + 1

    form_exec = [r["feature"] for r in forms
                 if r["kind"] == "step_form" and r["verdict"] == "EXECUTES"]
    ns_exec = [r["feature"] for r in forms
               if r["kind"] == "ref_namespace" and r["verdict"] == "EXECUTES"]
    ns_parse_only = [r["feature"] for r in forms
                     if r["kind"] == "ref_namespace"
                     and r["verdict"] == "PARSES_REJECTS"]
    ns_unrec = [r["feature"] for r in forms
                if r["kind"] == "ref_namespace"
                and r["verdict"] == "UNRECOGNISED"]

    op_in = [r["op"] for r in ops
             if r["side"] == "claimed_in" and r["c_dispatches"]]
    op_in_bad = [r["op"] for r in ops
                 if r["side"] == "claimed_in" and not r["c_dispatches"]]
    op_neg_bad = [r["op"] for r in ops
                  if r["side"] == "negative" and r["c_dispatches"]]

    summary = {
        "record": "summary",
        "declared_chain_variants": n_var,
        "c_runs": n_runs,
        "c_declined": n_decl,
        "c_parse_accept": n_parse_ok,
        "c_parse_reject": n_var - n_parse_ok,
        "unattributed": n_unatt,
        "decline_by_primary_code": by_code,
        "step_forms_python": 3,
        "step_forms_c_executes": sorted(form_exec),
        "ref_namespaces_python": 7,
        "ref_namespaces_c_executes": sorted(ns_exec),
        "ref_namespaces_c_parses_rejects": sorted(ns_parse_only),
        "ref_namespaces_c_unrecognised": sorted(ns_unrec),
        "op_table_claimed": len(_compose._RUN_C_OPS),
        "op_table_confirmed_dispatching": len(op_in),
        "op_table_claimed_but_not_dispatching": sorted(op_in_bad),
        "op_negative_controls_wrongly_dispatching": sorted(op_neg_bad),
        "route_sets_equal": route["sets_equal"],
        "route_vacuous_today": route["vacuous_today"],
        "route_control_proves_non_vacuity":
            route["control_proves_non_vacuity"],
        "schema_v1_rc": next((r["rc"] for r in schema
                              if r.get("record") == "schema_probe_raw"
                              and r.get("declared_chain_schema_version") == 1),
                             None),
        "schema_v2_rc": next((r["rc"] for r in schema
                              if r.get("record") == "schema_probe_raw"
                              and r.get("declared_chain_schema_version") == 2),
                             None),
    }

    records = [env] + controls + forms + ops + schema + ledger + \
        [route, summary]
    with open(args.ndjson, "w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True,
                                allow_nan=False) + "\n")

    print("[1] step forms  python=3  C-executes=%s" % sorted(form_exec))
    for r in forms:
        if r["kind"] == "step_form":
            print("    %-8s C parse rc=%s  C run rc=%s  -> %-14s py_parse=%s"
                  % (r["feature"], r["c_parse_rc"], r["c_run_rc"],
                     r["verdict"], r["py_parse"][:34]))
    print("    namespaces: executes=%s  parses_rejects=%s  unrecognised=%s"
          % (sorted(ns_exec), sorted(ns_parse_only), sorted(ns_unrec)))
    for r in forms:
        if r["kind"].startswith("ref_namespace"):
            print("    @%-8s [%s] C parse rc=%s C run rc=%s -> %-14s py=%s"
                  % (r["feature"], "scoped" if r["kind"].endswith("scoped")
                     else "plain ", r["c_parse_rc"], r["c_run_rc"],
                     r["verdict"], r["py_parse"][:30]))
    print("[2] op table: claimed=%d confirmed=%d  claimed-but-dead=%s  "
          "negatives-wrongly-live=%s"
          % (len(_compose._RUN_C_OPS), len(op_in), op_in_bad, op_neg_bad))
    print("[3] schema axis: v1 rc=%s  v2 rc=%s  (anchor "
          "srmech_compose.c:513 co_catalog_body)"
          % (summary["schema_v1_rc"], summary["schema_v2_rc"]))
    print("[4] chain ledger: %d variants  C-runs=%d  declined=%d  "
          "parse-accept=%d  UNATTRIBUTED=%d"
          % (n_var, n_runs, n_decl, n_parse_ok, n_unatt))
    for code in sorted(by_code):
        print("      %-24s %d" % (code, by_code[code]))
    for r in sorted(ledger, key=lambda x: x["key"]):
        print("      %-34s parse=%-9s run=%-9s %s"
              % (r["key"], r["c_parse_status"], r["c_run_status"],
                 r["decline_primary"]))
    print("[5] route coincidence: c_runs=%d py_routes=%d equal=%s "
          "vacuous=%s control_non_vacuity=%s (control value %s)"
          % (route["n_c_runs"], route["n_py_routes"], route["sets_equal"],
             route["vacuous_today"], route["control_proves_non_vacuity"],
             route["control_value_repr"]))
    print("wrote %s (%d records)" % (args.ndjson, len(records)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
