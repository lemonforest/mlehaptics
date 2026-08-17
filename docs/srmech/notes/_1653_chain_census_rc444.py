#!/usr/bin/env python3
"""Per-chain C accept/reject census over the 18 EXECUTABLE cascade-catalog
chains — srmech 0.9.0rc444, native ABI 17.  PRE-rcN research for gh #1653.

WHAT THIS MEASURES (and why each axis exists)
---------------------------------------------
The config-driven cascade surface is the 21 ``[cascade]`` TOML descriptors under
``srmech/cascade/catalogs/cascade_catalog/``.  18 declare an executable
ADR-0008 §2 (schema v2) chain under ``[[cascade.chain]]``; 3 are explicit
leaves.  The PYTHON projection of a declared chain is
``srmech.dsl.run_cascade_chain`` → ``srmech.cascade.compose.run_chain``.

Its C peer is ``srmech_chain_run`` (``c/src/srmech_compose_run.c``, rc174) —
NOT ``srmech_dsl_chain_run``, which is a SIBLING interpreter over a different
grammar (``{"chain":..,"stage":[..]}`` value-threading, no ``@input``/``@step``
references at all).  Both are measured; the second is labelled as the
grammar-mismatch axis it is, so the tally cannot be inflated by it.

Five axes per chain variant:

  A. PYTHON   — ``run_cascade_chain`` over every ``[[cascade.chain.proof_cases]]``
                input.  The control: if this fails, nothing downstream means
                anything.
  B. C PARSE  — ``srmech_chain_spec_parse`` on the chain dict.  Parse and run
                are SEPARATE C gates with different accept sets, so conflating
                them is exactly how a stale headline number gets minted.
  C. C RUN    — ``srmech_chain_run`` per proof case (chain + ctx).
  D. C RUN    — ``srmech_chain_run`` with a STRUCTURE PROBE ctx
     (structure)   (``{"row":null,"inputs":{}}``).  This isolates the
                CHAIN-GRAMMAR verdict from any descriptor-DATA problem
                (non-finite floats, out-of-int64 literals): the C run loop
                checks step shape + op-table membership BEFORE it resolves a
                single argument, so the structure probe's rc is the grammar
                verdict and nothing else.
  E. C DSL    — ``srmech_dsl_chain_run`` fed the same chain dict.  Recorded for
                completeness and attributed as GRAMMAR-MISMATCH, never counted
                as a C grammar gap of the cascade surface.

Plus the SHIPPED gate: ``compose._chain_c_eligible(spec)`` +
``compose._run_chain_native(...)`` — what srmech's own dispatcher decides today.

THE CONFOUND GUARD
------------------
A rejection attributed to nothing is worse than no measurement.  Every rc is
PREDICTED first, by a static reader of the chain that mirrors the C source
line-for-line (``predict_c_run_gate`` / ``predict_c_parse_gate``), and the
prediction is then compared to the measured rc.  Agreement ⇒ ATTRIBUTED to the
named source line.  Disagreement ⇒ the record is stamped ``UNATTRIBUTED`` and
says so.  The C calling convention is not guessed: it is lifted verbatim from
``srmech/cascade/compose.py::_run_chain_native`` (arena sized by the shipped
``*_arena_bytes`` export, ``out_cap = max(ws//2, 16384)``), so a wrong arena
size cannot masquerade as a grammar gap.

DISCIPLINE: no abs(), no numpy, no RNG, no stdlib fractions.  Read-only — this
script writes exactly one file, the NDJSON next to it.

Usage:  python3 _1653_chain_census_rc444.py [--ndjson PATH]
"""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY_ROOT = os.path.abspath(os.path.join(HERE, "..", "python"))
if PY_ROOT not in sys.path:
    sys.path.insert(0, PY_ROOT)

import srmech                                    # noqa: E402
from srmech import _native                       # noqa: E402
from srmech.amsc.format import sha256_bytes      # noqa: E402  (Class A)
from srmech.cascade import compose as _compose   # noqa: E402
from srmech.dsl import _cascade_chain as _cc     # noqa: E402
from srmech.dsl import _catalog as _cat          # noqa: E402
from srmech.dsl import run_cascade_chain         # noqa: E402

# ── the C status enum (c/include/srmech.h:400) ────────────────────────────
STATUS = {
    0: "SRMECH_OK",
    1: "SRMECH_ERR_NULL_ARG",
    2: "SRMECH_ERR_BAD_INPUT",
    3: "SRMECH_ERR_IO",
    4: "SRMECH_ERR_OVERFLOW",
    5: "SRMECH_ERR_NOT_IMPL",
    6: "SRMECH_ERR_INTERNAL",
    8: "SRMECH_ERR_LIMIT",
}

# ── the C run loop's op dispatch table, mirrored from
#    c/src/srmech_compose_run.c::cr_dispatch (lines 581-616).  Identical to the
#    shipped compose._RUN_C_OPS; asserted equal below so the mirror cannot rot.
C_RUN_OPS = (
    "pi_cascade_digits",
    "exp_series_truncate", "sin_series_truncate", "cos_series_truncate",
    "log1p_series_truncate", "atan_series_truncate",
    "rational_pow_uint", "rational_add", "rational_mul", "rational_div",
)

# ── the reference namespaces the C grammar knows
#    (c/src/srmech_compose.c::co_match_namespace, lines 135-146) vs Python's
#    seven (compose._REFERENCE_PATTERN, v2 adds idx/bind/op).
C_REF_NAMESPACES = ("row", "input", "step", "catalog")
PY_REF_NAMESPACES = ("row", "input", "step", "catalog", "idx", "bind", "op")

I64_MAX = (1 << 63) - 1
I64_MIN = -(1 << 63)

# ── Per-variant input defaults MIRRORED (read-only) from
#    tests/test_cascade_catalog_executable_rc420.py:253-258 ``CASE_DEFAULTS``.
#    Recorded here so the census can report BOTH numbers honestly:
#      * DESCRIPTOR-ONLY  — the inputs the TOML proof case actually declares,
#        which is what a caller of the public ``run_cascade_chain`` has.
#      * WITH-TEST-DEFAULTS — the inputs the rc420 gate actually runs, after
#        merging this dict UNDER the case.
#    A chain that runs only in the second column has a DECLARATION gap: its
#    descriptor does not carry every input its own chain references.  This is a
#    measurement, not an edit — nothing in tests/ or srmech/ is touched.
CASE_DEFAULTS_MIRROR = {
    ("kuramoto_step", "general"): {
        "adjacency": None, "alpha": 0.0,
        "pin_anchor": None, "pin_strength": 1.0,
    },
}


# ══════════════════════════════════════════════════════════════════════════
# Static chain reader — the PREDICTION half of the confound guard.
# ══════════════════════════════════════════════════════════════════════════

def step_form(raw):
    """Classify one raw ``[[cascade.chain.steps]]`` entry into one of the THREE
    schema-v2 step forms (compose.py:94-105 / _MAP_KEYS / _FOLD_KEYS)."""
    if not isinstance(raw, dict):
        return "malformed"
    if any(k in raw for k in _compose._MAP_KEYS):
        return "map"
    if any(k in raw for k in _compose._FOLD_KEYS):
        return "fold"
    if "op" in raw:
        return "plain"
    return "malformed"


def walk_steps(steps, depth=0):
    """Yield ``(depth, form, raw_step)`` over a step list, descending into map
    bodies (a map body is a chain in miniature — compose.py:106-114)."""
    for raw in steps or ():
        form = step_form(raw)
        yield depth, form, raw
        if form == "map":
            body = raw.get("body") or ()
            for rec in walk_steps(body, depth + 1):
                yield rec


def collect_refs(obj, out):
    """Every ``@...`` reference string in an args tree (dict VALUES + list
    items only — mirrors compose._walk_args)."""
    if isinstance(obj, str):
        if obj.startswith("@"):
            out.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            collect_refs(v, out)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            collect_refs(v, out)


def ref_namespace(ref):
    body = ref[1:]
    for sep in (".", "["):
        i = body.find(sep)
        if i >= 0:
            body = body[:i]
    return body


def chain_profile(steps):
    """Static profile of a chain: step-form counts, ops, ref namespaces."""
    forms = {"plain": 0, "map": 0, "fold": 0, "malformed": 0}
    ops, refs = [], []
    for _depth, form, raw in walk_steps(steps):
        forms[form] += 1
        if form == "plain":
            ops.append(str(raw.get("op")))
            collect_refs(raw.get("args"), refs)
        elif form == "fold":
            ops.append(str(raw.get("fold_op")))
            collect_refs(raw.get("fold_init"), refs)
            collect_refs(raw.get("fold_args"), refs)
            collect_refs(raw.get("over"), refs)
        else:
            collect_refs(raw.get("map_over"), refs)
            collect_refs(raw.get("bind"), refs)
    ns = sorted({ref_namespace(r) for r in refs})
    return {
        "step_forms": forms,
        "n_steps_top": len(steps or ()),
        "n_steps_total": sum(forms.values()),
        "ops": sorted(set(ops)),
        "ref_namespaces": ns,
        "ref_namespaces_c_unknown": [n for n in ns if n not in C_REF_NAMESPACES],
        "has_non_i64_literal": _has_non_i64(steps),
    }


def _has_non_i64(obj):
    if isinstance(obj, bool):
        return False
    if isinstance(obj, int):
        return not (I64_MIN <= obj <= I64_MAX)
    if isinstance(obj, dict):
        return any(_has_non_i64(v) for v in obj.values())
    if isinstance(obj, (list, tuple)):
        return any(_has_non_i64(v) for v in obj)
    return False


def _has_nonfinite(obj):
    """A float literal json.dumps emits as NaN / Infinity — not RFC-8259 JSON,
    so the C srmech_json parser declines the whole document."""
    if isinstance(obj, float):
        return obj != obj or obj in (float("inf"), float("-inf"))
    if isinstance(obj, dict):
        return any(_has_nonfinite(v) for v in obj.values())
    if isinstance(obj, (list, tuple)):
        return any(_has_nonfinite(v) for v in obj)
    return False


def predict_c_run_gate(steps, ctx):
    """Predict ``srmech_chain_run``'s rc + the source line that emits it.

    The C order of operations (srmech_compose_run.c):
      1. srmech_json_parse of chain_json / ctx_json  → :866-876  BAD_INPUT
      2. cr_run_steps step loop: every step must carry a STRING "op"  → :723
         BAD_INPUT   (this is where a map / fold step dies: it has no "op")
      3. same loop: "args" must be an OBJECT  → :725  BAD_INPUT
      4. cr_dispatch: op must be one of the 10 Class-N table entries → :616
         NOT_IMPL
    """
    if _has_nonfinite(steps) or _has_nonfinite(ctx):
        return (2, "srmech_compose_run.c:866-876 srmech_json_parse "
                   "(NaN/Infinity is not JSON)", "non_finite_literal")
    first = (steps or [None])[0]
    form = step_form(first)
    if form in ("map", "fold", "malformed"):
        return (2, "srmech_compose_run.c:723 (step has no STRING \"op\")",
                "step_form_" + form)
    op = str(first.get("op"))
    if op not in C_RUN_OPS:
        return (5, "srmech_compose_run.c:616 cr_dispatch "
                   "(op not in the 10-entry Class-N table)", "op_not_in_table")
    return (0, "n/a", "predicted_accept")


def predict_c_parse_gate(steps):
    """Predict ``srmech_chain_spec_parse``'s rc + the emitting source line.

    srmech_compose.c order: co_build_step requires "class" (a valid A..N
    letter) + "op" strings + an "args" OBJECT (:299-306, BAD_INPUT), THEN
    grammar-checks every ``@`` reference (:247 via co_args_refs_status).
    It does NOT consult the run loop's op table — so the parse accept set is
    strictly LARGER than the run accept set.
    """
    for idx, (_d, form, raw) in enumerate(walk_steps(steps)):
        if form in ("map", "fold", "malformed"):
            return (2, "srmech_compose.c:299-302 co_build_step "
                       "(no \"class\"+\"op\" strings)", "step_form_" + form)
    for raw in steps or ():
        refs = []
        collect_refs(raw.get("args"), refs)
        for r in refs:
            if ref_namespace(r) not in C_REF_NAMESPACES:
                return (2, "srmech_compose.c:247 co_args_refs_status "
                           "(unknown reference namespace @%s)"
                           % ref_namespace(r), "ref_namespace_unknown")
    return (0, "n/a", "predicted_accept")


# ══════════════════════════════════════════════════════════════════════════
# The C drivers — calling convention lifted verbatim from the shipped
# compose._run_chain_native (compose.py:1141-1177).
# ══════════════════════════════════════════════════════════════════════════

def _lib(*syms):
    return _compose._compose_lib(*syms)


def _dumps(obj):
    return json.dumps(obj, ensure_ascii=False).encode("utf-8")


def c_chain_spec_parse(chain_dict):
    lib = _lib("srmech_chain_spec_parse", "srmech_chain_spec_parse_arena_bytes")
    if lib is None:
        return {"rc": None, "status": "NO_NATIVE", "out_len": 0}
    cj = _dumps(chain_dict)
    ws_bytes = int(lib.srmech_chain_spec_parse_arena_bytes(len(cj)))
    ws = (ctypes.c_char * ws_bytes)()
    out_cap = max(ws_bytes // 2, 16384)
    out = (ctypes.c_char * out_cap)()
    out_len = ctypes.c_size_t()
    rc = int(lib.srmech_chain_spec_parse(
        cj, len(cj), ws, ws_bytes, out, out_cap, ctypes.byref(out_len)))
    rec = {"rc": rc, "status": STATUS.get(rc, "rc=%d" % rc),
           "arena_bytes": ws_bytes, "out_cap": out_cap,
           "out_len": int(out_len.value)}
    if rc == 0:
        rec["out_sha256"] = sha256_bytes(out.raw[:out_len.value])
        rec["out"] = out.raw[:out_len.value].decode("utf-8")
    return rec


def c_chain_run(chain_dict, ctx):
    lib = _lib("srmech_chain_run", "srmech_chain_run_arena_bytes")
    if lib is None:
        return {"rc": None, "status": "NO_NATIVE", "out_len": 0}
    try:
        cj, xj = _dumps(chain_dict), _dumps(ctx)
    except (TypeError, ValueError) as exc:
        return {"rc": None, "status": "PY_JSON_DUMPS_FAILED: %s" % exc}
    ws_bytes = int(lib.srmech_chain_run_arena_bytes(len(cj), len(xj)))
    ws = (ctypes.c_char * ws_bytes)()
    out_cap = max(ws_bytes // 2, 16384)
    out = (ctypes.c_char * out_cap)()
    out_len = ctypes.c_size_t()
    rc = int(lib.srmech_chain_run(
        cj, len(cj), xj, len(xj), ws, ws_bytes,
        out, out_cap, ctypes.byref(out_len)))
    rec = {"rc": rc, "status": STATUS.get(rc, "rc=%d" % rc),
           "arena_bytes": ws_bytes, "out_cap": out_cap,
           "out_len": int(out_len.value),
           "chain_json_len": len(cj), "ctx_json_len": len(xj)}
    if rc == 0:
        raw = out.raw[:out_len.value]
        rec["out_sha256"] = sha256_bytes(raw)
        rec["out"] = raw.decode("utf-8")
        try:
            rec["reconstructed_repr"] = repr(
                _compose._reconstruct_value(json.loads(rec["out"])))
        except Exception as exc:                      # noqa: BLE001
            rec["reconstructed_repr"] = "RECONSTRUCT_FAILED: %s" % exc
    return rec


def c_chain_catalog_parse(chain_dict):
    """``srmech_chain_catalog_parse`` on a ONE-CHAIN catalog wrapper
    ``{chain_schema_version:1, operator_chain:[chain]}``.  Per-chain validation
    is the same ``co_build_step`` as ``srmech_chain_spec_parse``, so this axis
    should agree with the parse axis — measured rather than assumed, because
    "should agree" is how a wrong number survives."""
    lib = _lib("srmech_chain_catalog_parse",
               "srmech_chain_catalog_parse_arena_bytes")
    if lib is None:
        return {"rc": None, "status": "NO_NATIVE"}
    cat = {"chain_schema_version": 1, "operator_chain": [chain_dict]}
    cj = _dumps(cat)
    ws_bytes = int(lib.srmech_chain_catalog_parse_arena_bytes(len(cj)))
    ws = (ctypes.c_char * ws_bytes)()
    out_cap = max(ws_bytes // 2, 16384)
    out = (ctypes.c_char * out_cap)()
    out_len = ctypes.c_size_t()
    rc = int(lib.srmech_chain_catalog_parse(
        cj, len(cj), ws, ws_bytes, out, out_cap, ctypes.byref(out_len)))
    return {"rc": rc, "status": STATUS.get(rc, "rc=%d" % rc),
            "out_len": int(out_len.value)}


def c_toml_chain_to_json(toml_path):
    """``srmech_dsl_toml_chain_to_json`` on the descriptor's OWN TOML file — the
    C-only / MCU front door.  A decline here means a bare-C host cannot even
    READ the descriptor, which is upstream of any run-loop question."""
    lib = _lib("srmech_dsl_toml_chain_to_json",
               "srmech_dsl_toml_chain_to_json_arena_bytes")
    if lib is None:
        return {"rc": None, "status": "NO_NATIVE"}
    try:
        with open(toml_path, "rb") as fh:
            src = fh.read()
    except OSError as exc:
        return {"rc": None, "status": "TOML_UNREADABLE: %s" % exc}
    ws_bytes = int(lib.srmech_dsl_toml_chain_to_json_arena_bytes(len(src)))
    ws = (ctypes.c_char * ws_bytes)()
    out_cap = max(ws_bytes // 2, 65536)
    out = (ctypes.c_char * out_cap)()
    out_len = ctypes.c_size_t()
    rc = int(lib.srmech_dsl_toml_chain_to_json(
        src, len(src), ws, ws_bytes, out, out_cap, ctypes.byref(out_len)))
    rec = {"rc": rc, "status": STATUS.get(rc, "rc=%d" % rc),
           "toml_bytes": len(src), "out_len": int(out_len.value),
           "toml_path": os.path.basename(toml_path)}
    if rc == 0:
        rec["out_sha256"] = sha256_bytes(out.raw[:out_len.value])
    return rec


def c_dsl_chain_run(chain_dict, input_desc):
    """The SIBLING interpreter, recorded for completeness.  Its grammar is
    ``{"chain":{"name":..},"stage":[..]}`` value-threading — the cascade
    descriptor's ``steps`` IR has no ``stage`` key and no value-threading
    semantics, so this is a GRAMMAR MISMATCH by construction, never evidence
    of a cascade-surface grammar gap."""
    lib = _lib("srmech_dsl_chain_run", "srmech_dsl_chain_run_arena_bytes")
    if lib is None:
        return {"rc": None, "status": "NO_NATIVE"}
    cj, ij = _dumps(chain_dict), _dumps(input_desc)
    ws_bytes = int(lib.srmech_dsl_chain_run_arena_bytes(len(cj), len(ij)))
    ws = (ctypes.c_char * ws_bytes)()
    out_cap = max(ws_bytes // 2, 16384)
    out = (ctypes.c_char * out_cap)()
    out_len = ctypes.c_size_t()
    rc = int(lib.srmech_dsl_chain_run(
        cj, len(cj), ij, len(ij), ws, ws_bytes,
        out, out_cap, ctypes.byref(out_len)))
    return {"rc": rc, "status": STATUS.get(rc, "rc=%d" % rc),
            "out_len": int(out_len.value),
            "note": "grammar mismatch: cascade `steps` IR is not the "
                    "`stage` value-threading IR this entry point reads"}


# ══════════════════════════════════════════════════════════════════════════
# Python projection
# ══════════════════════════════════════════════════════════════════════════

def canonical_repr(value):
    """A stable textual image of a chain result, for byte-comparison.  Floats
    go through repr (byte-exact per rc403), tuples are marked distinctly from
    lists so a pack step's tuple cannot compare equal to a list."""
    if isinstance(value, tuple):
        return "(" + ",".join(canonical_repr(v) for v in value) + ")"
    if isinstance(value, list):
        return "[" + ",".join(canonical_repr(v) for v in value) + "]"
    if isinstance(value, dict):
        return "{" + ",".join(
            "%r:%s" % (k, canonical_repr(value[k]))
            for k in sorted(value, key=repr)) + "}"
    if isinstance(value, (bytes, bytearray)):
        return "b:" + sha256_bytes(bytes(value))
    return repr(value)


def run_python(op_name, variant, cases, defaults=None):
    per_case, n_ok = [], 0
    for i, case in enumerate(cases):
        inputs = dict(defaults or {})
        inputs.update(dict(case.get("inputs") or {}))
        try:
            kw = {} if variant is None else {"variant": variant}
            val = run_cascade_chain(op_name, inputs, **kw)
            img = canonical_repr(val)
            per_case.append({"case": i, "covers": case.get("covers"),
                             "ok": True, "image": img,
                             "image_sha256": sha256_bytes(img.encode("utf-8"))})
            n_ok += 1
        except Exception as exc:                      # noqa: BLE001
            per_case.append({"case": i, "covers": case.get("covers"),
                             "ok": False,
                             "error": "%s: %s" % (type(exc).__name__, exc)})
    return per_case, n_ok


# ══════════════════════════════════════════════════════════════════════════
# Census
# ══════════════════════════════════════════════════════════════════════════

def chain_dict_for(op_name, variant, entry):
    return {
        "name": "%s.%s" % (op_name, variant),
        "summary": str(entry.get("summary", "")),
        "returns": str(entry.get("returns", "")),
        "on_error": "raise",
        "steps": entry.get("steps", []),
    }


def shipped_gate(op_name, variant, cases):
    """What srmech's OWN dispatcher decides today: _chain_c_eligible on the
    parsed spec, and the actual _run_chain_native outcome on proof case 0."""
    out = {"c_eligible": None, "run_chain_native": None}
    try:
        specs = _cc.cascade_chain_specs(op_name)
    except Exception as exc:                          # noqa: BLE001
        out["error"] = "%s: %s" % (type(exc).__name__, exc)
        return out
    spec = None
    for v, s, _e in specs:
        if variant is None or v == variant:
            spec = s
            break
    if spec is None:
        out["error"] = "variant %r not found" % variant
        return out
    out["c_eligible"] = bool(_compose._chain_c_eligible(spec))
    inputs = dict((cases[0].get("inputs") or {})) if cases else {}
    try:
        res = _compose._run_chain_native(spec, None, inputs)
        out["run_chain_native"] = (
            "NATIVE_MISS" if res is _compose._NATIVE_MISS else "NATIVE_RAN")
    except Exception as exc:                          # noqa: BLE001
        out["run_chain_native"] = "RAISED: %s: %s" % (type(exc).__name__, exc)
    return out


def census_variant(op_name, variant, entry, single_variant):
    steps = entry.get("steps", [])
    cases = entry.get("proof_cases", []) or []
    prof = chain_profile(steps)
    cd = chain_dict_for(op_name, variant, entry)

    v_arg = None if single_variant else variant
    defaults = CASE_DEFAULTS_MIRROR.get((op_name, variant), {})
    py_cases, py_ok = run_python(op_name, v_arg, cases)
    if defaults:
        pyd_cases, pyd_ok = run_python(op_name, v_arg, cases, defaults)
    else:
        pyd_cases, pyd_ok = py_cases, py_ok

    parse_pred = predict_c_parse_gate(steps)
    parse = c_chain_spec_parse(cd)

    probe_ctx = {"row": None, "inputs": {}}
    run_pred_struct = predict_c_run_gate(steps, probe_ctx)
    run_struct = c_chain_run(cd, probe_ctx)

    run_cases = []
    for i, case in enumerate(cases):
        merged = dict(defaults)
        merged.update(dict(case.get("inputs") or {}))
        ctx = {"row": None, "inputs": merged}
        pred = predict_c_run_gate(steps, ctx)
        got = c_chain_run(cd, ctx)
        run_cases.append({
            "case": i, "covers": case.get("covers"),
            "predicted_rc": pred[0], "predicted_gate": pred[1],
            "predicted_cause": pred[2],
            "rc": got.get("rc"), "status": got.get("status"),
            "arena_bytes": got.get("arena_bytes"),
            "attributed": got.get("rc") == pred[0],
            "out": got.get("out"),
        })

    dsl = c_dsl_chain_run(cd, {"k": "n"})
    catparse = c_chain_catalog_parse(cd)
    gate = shipped_gate(op_name, variant if not single_variant else None, cases)

    c_accepted = bool(run_struct.get("rc") == 0
                      and all(r["rc"] == 0 for r in run_cases))
    parse_accepted = parse.get("rc") == 0

    attributed = (run_struct.get("rc") == run_pred_struct[0]
                  and parse.get("rc") == parse_pred[0]
                  and all(r["attributed"] for r in run_cases))

    return {
        "variant": variant,
        "profile": prof,
        "c_blockers": c_blockers(prof),
        "n_proof_cases": len(cases),
        "python": {"ok": py_ok == len(cases) and len(cases) > 0,
                   "n_ok": py_ok, "n_cases": len(cases),
                   "per_case": py_cases},
        "python_with_test_defaults": {
            "ok": pyd_ok == len(cases) and len(cases) > 0,
            "n_ok": pyd_ok, "n_cases": len(cases),
            "defaults_applied": dict(defaults),
            "per_case": pyd_cases},
        "c_spec_parse": dict(parse, predicted_rc=parse_pred[0],
                             predicted_gate=parse_pred[1],
                             predicted_cause=parse_pred[2],
                             attributed=parse.get("rc") == parse_pred[0]),
        "c_chain_run_structure_probe": dict(
            run_struct, predicted_rc=run_pred_struct[0],
            predicted_gate=run_pred_struct[1],
            predicted_cause=run_pred_struct[2],
            attributed=run_struct.get("rc") == run_pred_struct[0]),
        "c_chain_run_per_case": run_cases,
        "c_dsl_chain_run": dsl,
        "c_chain_catalog_parse": dict(
            catparse,
            agrees_with_spec_parse=(
                (catparse.get("rc") == 0) == (parse.get("rc") == 0))),
        "shipped_gate": gate,
        "c_parse_accepted": parse_accepted,
        "c_run_accepted": c_accepted,
        "byte_identical_python_vs_c": (None if not c_accepted else "SEE_CASES"),
        "attributed": attributed,
    }


def c_blockers(prof):
    """EVERY C blocker present in the chain, not only the first one the run
    loop trips over.  The run loop short-circuits at step 0, so a chain whose
    step 0 is an out-of-table plain op reports only ``op_not_in_table`` — but
    its map / fold steps and its ``@idx``/``@bind``/``@op`` references are
    blockers too, and the ship needs the full list to size the work."""
    out = []
    if prof["step_forms"]["map"]:
        out.append("step_form_map_x%d" % prof["step_forms"]["map"])
    if prof["step_forms"]["fold"]:
        out.append("step_form_fold_x%d" % prof["step_forms"]["fold"])
    for ns in prof["ref_namespaces_c_unknown"]:
        out.append("ref_namespace_@" + ns)
    outside = [o for o in prof["ops"] if o not in C_RUN_OPS]
    if outside:
        out.append("ops_outside_c_table_x%d" % len(outside))
    if prof["has_non_i64_literal"]:
        out.append("non_i64_literal")
    return out


def cause_class(var):
    """Attribute the rejection: C_GRAMMAR_GAP / DESCRIPTOR_DATA /
    HARNESS_LIMITATION / UNATTRIBUTED."""
    if var["c_run_accepted"]:
        return "N/A_ACCEPTED", "the C run loop accepted every proof case"
    if not var["attributed"]:
        return "UNATTRIBUTED", ("measured rc disagrees with the source-read "
                               "prediction; cause not pinned")
    struct = var["c_chain_run_structure_probe"]
    cause = struct.get("predicted_cause")
    gate = struct.get("predicted_gate")
    if cause in ("step_form_map", "step_form_fold"):
        return "C_GRAMMAR_GAP", (
            "step form %r is not implemented by the C run loop — %s"
            % (cause.replace("step_form_", ""), gate))
    if cause == "op_not_in_table":
        return "C_GRAMMAR_GAP", (
            "every op is outside the C run loop's 10-entry Class-N dispatch "
            "table — %s" % gate)
    if cause == "non_finite_literal":
        return "DESCRIPTOR_DATA", (
            "a non-finite float literal in the chain makes the document "
            "non-JSON — %s" % gate)
    return "UNATTRIBUTED", "unclassified predicted cause %r" % cause


def rosetta_buckets(ops):
    """Classify each op used by the 18 chains against the shipped Rosetta
    ledger (``python/tests/rosetta_classification.ndjson``: every public
    callable is ``c_dispatched`` / ``composition_of_c`` / ``non_compute``).

    This sizes the op-table half of the gap honestly.  An op already
    ``c_dispatched`` has a C kernel the run loop could call — widening the
    dispatch table reaches it without new math.  A ``composition_of_c`` op has
    no single symbol, so it needs either a new C composite or a step-level
    decomposition in the descriptor.  Missing from the ledger = unknown, said
    so rather than guessed."""
    path = os.path.join(PY_ROOT, "tests", "rosetta_classification.ndjson")
    table = {}
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                row = json.loads(line)
                for key in ("exposed_as", "defined_at"):
                    if row.get(key):
                        table.setdefault(row[key], row.get("bucket"))
    except OSError:
        return {"ledger": "NOT_FOUND", "path": path}
    reg = _compose.DEFAULT_CLASS_REGISTRY
    out, counts = {}, {}
    for op, classes in sorted(ops.items()):
        if "." in op:
            cands = [op]
        else:
            cands = ["%s.%s" % (reg[c], op) for c in sorted(classes)
                     if c in reg]
        bucket = None
        for cand in cands:
            if cand in table:
                bucket = table[cand]
                break
        label = bucket or "NOT_IN_LEDGER"
        out[op] = {"bucket": label, "resolved_from": cands,
                   "declared_classes": sorted(classes)}
        counts[label] = counts.get(label, 0) + 1
    return {"ledger": os.path.relpath(path, HERE), "per_op": out,
            "bucket_counts": counts}


def collect_op_classes(steps, acc):
    """``{op_name: {declared class letters}}`` over a chain's steps."""
    for _d, form, raw in walk_steps(steps):
        if form == "plain":
            acc.setdefault(str(raw.get("op")), set()).add(
                str(raw.get("class")))
        elif form == "fold":
            acc.setdefault(str(raw.get("fold_op")), set()).add(
                str(raw.get("fold_class")))
    return acc


def positive_controls():
    """THE DECISIVE CONFOUND GUARD.

    Two synthetic chains that the C run loop SHOULD accept, driven through the
    exact same harness as the 18 real chains:

      CTL-1  literal args   — proves the chain-JSON shape + arena sizing +
                              out_cap + value-descriptor read-back all work.
      CTL-2  ``@input`` refs — proves the ctx marshalling works too, so a
                              reference-carrying chain is not rejected by the
                              harness.

    If either control returns OK and matches Python, then a rejection of a real
    chain CANNOT be a harness artifact — it is the C grammar declining the
    chain.  If a control fails, the whole census is void and says so.
    """
    from srmech.math.rational import rational_add
    out = []
    for label, args, ctx in (
        ("CTL-1_literal", {"a": [1, 2], "b": [1, 3]},
         {"row": None, "inputs": {}}),
        ("CTL-2_input_refs", {"a": "@input.a", "b": "@input.b"},
         {"row": None, "inputs": {"a": [1, 2], "b": [1, 3]}}),
    ):
        cd = {"name": "ctl.%s" % label, "summary": "positive control",
              "returns": "tuple[int, int]", "on_error": "raise",
              "steps": [{"class": "N", "op": "rational_add", "args": args}]}
        run = c_chain_run(cd, ctx)
        parse = c_chain_spec_parse(cd)
        py = rational_add((1, 2), (1, 3))
        c_val = None
        if run.get("rc") == 0:
            c_val = _compose._reconstruct_value(json.loads(run["out"]))
        out.append({
            "control": label,
            "c_parse_rc": parse.get("rc"), "c_parse_status": parse.get("status"),
            "c_run_rc": run.get("rc"), "c_run_status": run.get("status"),
            "c_arena_bytes": run.get("arena_bytes"),
            "c_out": run.get("out"),
            "python_value": canonical_repr(py),
            "c_value": None if c_val is None else canonical_repr(c_val),
            "byte_identical": (c_val is not None
                               and canonical_repr(c_val) == canonical_repr(py)),
        })
    return out


def toml_nonfinite_probe():
    """Attribute the TOML front-end declines: is it the ``nan`` / ``inf``
    literal, or something else in those two files?  Three minimal documents,
    identical but for the float, through ``srmech_dsl_toml_chain_to_json``."""
    import tempfile
    out = []
    for label, body in (("finite", b"[cascade]\nx = 1.5\n"),
                        ("nan", b"[cascade]\nx = nan\n"),
                        ("inf", b"[cascade]\nx = inf\n")):
        fd, path = tempfile.mkstemp(suffix=".toml")
        try:
            os.write(fd, body)
            os.close(fd)
            rec = c_toml_chain_to_json(path)
        finally:
            os.unlink(path)
        out.append({"literal": label, "rc": rec.get("rc"),
                    "status": rec.get("status")})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ndjson", default=os.path.join(
        HERE, "_1653_chain_census_rc444.ndjson"))
    args = ap.parse_args()

    # The mirror of cr_dispatch must equal the shipped table, or the
    # prediction half of the confound guard is reading a stale source.
    assert frozenset(C_RUN_OPS) == _compose._RUN_C_OPS, \
        "C_RUN_OPS mirror has drifted from compose._RUN_C_OPS"
    assert tuple(sorted(PY_REF_NAMESPACES)) == tuple(sorted(
        _compose._REFERENCE_PATTERN.pattern.split("@(")[1].split(")")[0]
        .split("|"))), "PY_REF_NAMESPACES mirror has drifted"

    catalog = _cat.load_catalog()
    status = _cc.cascade_catalog_status()
    executable = sorted(n for n, s in status.items() if s == "executable")
    leaf = sorted(n for n, s in status.items() if s == "leaf")

    env = {
        "record": "environment",
        "srmech_version": srmech.__version__,
        "has_native": bool(_native.HAS_NATIVE),
        "native_abi": getattr(_native, "NATIVE_ABI_VERSION", None),
        "expected_abi": getattr(_native, "EXPECTED_ABI_VERSION", None),
        "lib_path": str(getattr(_native, "_LIB_PATH", None)),
        "engine_schema_version": _compose.ENGINE_SCHEMA_VERSION,
        "supported_schema_versions": list(_compose.SUPPORTED_SCHEMA_VERSIONS),
        "catalog_total": len(catalog),
        "executable": executable,
        "leaf": leaf,
        "py_step_forms": ["plain", "map", "fold"],
        "c_run_step_forms": ["plain"],
        "c_parse_step_forms": ["plain"],
        "py_ref_namespaces": list(PY_REF_NAMESPACES),
        "c_ref_namespaces": list(C_REF_NAMESPACES),
        "c_run_op_table": list(C_RUN_OPS),
    }

    ctls = positive_controls()
    env["positive_controls"] = ctls
    env["toml_nonfinite_probe"] = toml_nonfinite_probe()
    env["harness_proven"] = all(c["byte_identical"] for c in ctls)

    records = [env]
    tally = {"chains": 0, "variants": 0,
             "py_ok": 0, "py_ok_with_test_defaults": 0,
             "c_parse_accept": 0, "c_parse_reject": 0,
             "c_run_accept": 0, "c_run_reject": 0,
             "c_toml_front_end_accept": 0,
             "c_catalog_parse_agrees_with_spec_parse": 0,
             "byte_identical": 0, "unattributed": 0,
             "shipped_c_eligible": 0, "shipped_native_ran": 0}
    cause_tally = {}

    for name in executable:
        desc = catalog[name]
        entries = _cc._chain_entries(desc)
        single = len(entries) == 1
        variants = []
        for entry in entries:
            v = str(entry.get("variant", "default"))
            variants.append(census_variant(name, v, entry, single))
        toml_path = os.path.join(
            PY_ROOT, "srmech", "cascade", "catalogs", "cascade_catalog",
            name + ".toml")
        rec = {
            "record": "chain",
            "chain": name,
            "c_toml_front_end": c_toml_chain_to_json(toml_path),
            "descriptor_status": _cc.descriptor_status(desc),
            "class_composition": desc.get("cascade", {}).get(
                "class_composition"),
            "n_variants": len(variants),
            "variants": variants,
            # chain-level roll-up: conservative (all variants must pass)
            "python_ok": all(v["python"]["ok"] for v in variants),
            "python_ok_with_test_defaults": all(
                v["python_with_test_defaults"]["ok"] for v in variants),
            "c_parse_accepted": all(v["c_parse_accepted"] for v in variants),
            "c_run_accepted": all(v["c_run_accepted"] for v in variants),
            "byte_identical": all(v["c_run_accepted"] for v in variants),
            "shipped_c_eligible": all(
                v["shipped_gate"].get("c_eligible") is True for v in variants),
            "shipped_native_ran": all(
                v["shipped_gate"].get("run_chain_native") == "NATIVE_RAN"
                for v in variants),
        }
        causes = [cause_class(v) for v in variants]
        rec["reject_cause_class"] = causes[0][0]
        rec["reject_cause_detail"] = causes[0][1]
        rec["reject_causes_all_variants"] = [
            {"variant": v["variant"], "cause": c[0], "detail": c[1]}
            for v, c in zip(variants, causes)]
        rec["unattributed"] = any(c[0] == "UNATTRIBUTED" for c in causes)

        tally["chains"] += 1
        tally["variants"] += len(variants)
        tally["py_ok"] += 1 if rec["python_ok"] else 0
        tally["py_ok_with_test_defaults"] += (
            1 if rec["python_ok_with_test_defaults"] else 0)
        tally["c_parse_accept"] += 1 if rec["c_parse_accepted"] else 0
        tally["c_parse_reject"] += 0 if rec["c_parse_accepted"] else 1
        tally["c_run_accept"] += 1 if rec["c_run_accepted"] else 0
        tally["c_run_reject"] += 0 if rec["c_run_accepted"] else 1
        tally["c_toml_front_end_accept"] += (
            1 if rec["c_toml_front_end"].get("rc") == 0 else 0)
        tally["c_catalog_parse_agrees_with_spec_parse"] += (
            1 if all(v["c_chain_catalog_parse"]["agrees_with_spec_parse"]
                     for v in variants) else 0)
        tally["byte_identical"] += 1 if rec["byte_identical"] else 0
        tally["unattributed"] += 1 if rec["unattributed"] else 0
        tally["shipped_c_eligible"] += 1 if rec["shipped_c_eligible"] else 0
        tally["shipped_native_ran"] += 1 if rec["shipped_native_ran"] else 0
        for c, _d in causes:
            cause_tally[c] = cause_tally.get(c, 0) + 1
        records.append(rec)

    # ── step-form census across the whole executable surface ──────────────
    forms = {"plain": 0, "map": 0, "fold": 0, "malformed": 0}
    ns_seen, ops_seen, blockers_seen = set(), set(), {}
    op_classes = {}
    for r in records[1:]:
        desc_entries = _cc._chain_entries(catalog[r["chain"]])
        for entry in desc_entries:
            collect_op_classes(entry.get("steps", []), op_classes)
        for v in r["variants"]:
            for k in forms:
                forms[k] += v["profile"]["step_forms"][k]
            ns_seen.update(v["profile"]["ref_namespaces"])
            ops_seen.update(v["profile"]["ops"])
            for b in v["c_blockers"]:
                key = b.split("_x")[0]
                blockers_seen[key] = blockers_seen.get(key, 0) + 1
    ops_outside = sorted(o for o in ops_seen if o not in C_RUN_OPS)
    ops_dotted = [o for o in ops_outside if "." in o]
    ops_bare = [o for o in ops_outside if "." not in o]

    # ── candidate reconstructions of the issue's carried "11 of 18 rejected".
    #    Every one is computed from THIS measurement; none is asserted to be
    #    what the carried figure meant.  Reported so the ship can see whether
    #    any definition reproduces 11, and pick a definition going forward.
    n_all_plain = sum(
        1 for r in records[1:]
        if all(v["profile"]["step_forms"]["map"] == 0
               and v["profile"]["step_forms"]["fold"] == 0
               for v in r["variants"]))
    n_chains_seen = len(records) - 1        # records = [env] + one per chain
    n_map_or_fold = n_chains_seen - n_all_plain
    dsl_leaf_table = ("magnitude", "reorient", "pin_slot_at_zero",
                      "best_rational_signed", "chiral_flip", "net_chirality",
                      "autocorrelation", "cyclic_gcd")
    n_dsl_named = sum(1 for r in records[1:] if r["chain"] in dsl_leaf_table)
    reconstructions = {
        "srmech_chain_run REJECTS (this census, primary axis)":
            sum(1 for r in records[1:] if not r["c_run_accepted"]),
        "srmech_chain_spec_parse REJECTS":
            sum(1 for r in records[1:] if not r["c_parse_accepted"]),
        "srmech_chain_spec_parse ACCEPTS":
            sum(1 for r in records[1:] if r["c_parse_accepted"]),
        "chains carrying a map or fold step anywhere": n_map_or_fold,
        "chains whose every step is the plain form": n_all_plain,
        "descriptor names NOT in the srmech_dsl_chain_run op tables":
            n_chains_seen - n_dsl_named,
        "descriptor names IN the srmech_dsl_chain_run op tables": n_dsl_named,
    }
    summary = {
        "record": "summary",
        "tally": tally,
        "cause_tally": cause_tally,
        "step_instances": forms,
        "chains_using_map_or_fold": sum(
            1 for r in records[1:]
            if any(v["profile"]["step_forms"]["map"]
                   or v["profile"]["step_forms"]["fold"]
                   for v in r["variants"])),
        "chains_all_plain": sum(
            1 for r in records[1:]
            if all(v["profile"]["step_forms"]["map"] == 0
                   and v["profile"]["step_forms"]["fold"] == 0
                   for v in r["variants"])),
        "ref_namespaces_in_use": sorted(ns_seen),
        "ref_namespaces_c_cannot_parse": sorted(
            n for n in ns_seen if n not in C_REF_NAMESPACES),
        # The OP-TABLE-ONLY REACHABLE SET: chains the C PARSE already accepts,
        # i.e. every step is the plain form and every reference is in a
        # namespace C knows.  For these, widening cr_dispatch's op table is the
        # ONLY C-side blocker left — no new step form, no new namespace.  This
        # is the cheapest first slice of the parity work and it is why the
        # number 11 keeps appearing on this surface.
        "op_table_only_reachable": {
            "n_chains": sum(1 for r in records[1:] if r["c_parse_accepted"]),
            "chains": sorted(r["chain"] for r in records[1:]
                             if r["c_parse_accepted"]),
            "second_gate_python": (
                "compose._chain_c_eligible (compose.py:1045-1061) ALSO requires "
                "step.class_id == 'N', so widening the C table alone does not "
                "route: both projections must move in the same rc"),
        },
        "rosetta": rosetta_buckets(op_classes),
        "distinct_ops_used": sorted(ops_seen),
        "n_distinct_ops_used": len(ops_seen),
        "ops_outside_c_run_table": ops_outside,
        "n_ops_outside_c_run_table": len(ops_outside),
        "ops_outside_dotted": sorted(ops_dotted),
        "ops_outside_bare": sorted(ops_bare),
        "blocker_frequency_over_variants": blockers_seen,
        "carried_figure_reconstructions": reconstructions,
        "issue_carried_figures": {
            "c_implements_1_of_3_step_forms": "carried (~rc435)",
            "11_of_18_chains_rejected": "carried (~rc435)",
        },
    }
    records.append(summary)

    with open(args.ndjson, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False,
                                sort_keys=True, allow_nan=True) + "\n")

    print("srmech %s  native=%s ABI=%s  engine_schema=v%d"
          % (env["srmech_version"], env["has_native"], env["native_abi"],
             env["engine_schema_version"]))
    print("catalog: total=%d executable=%d leaf=%d"
          % (env["catalog_total"], len(executable), len(leaf)))
    for c in ctls:
        print("  positive control %-16s C parse rc=%s  C run rc=%s (%s)  "
              "byte-identical to python=%s"
              % (c["control"], c["c_parse_rc"], c["c_run_rc"],
                 c["c_run_status"], c["byte_identical"]))
    print("HARNESS PROVEN (both controls C-accepted + byte-identical): %s"
          % env["harness_proven"])
    print("step-form instances across the 18 executable chains: %s" % forms)
    print("reference namespaces in use: %s   (C can parse only %s; "
          "C-unknown in use: %s)"
          % (summary["ref_namespaces_in_use"], list(C_REF_NAMESPACES),
             summary["ref_namespaces_c_cannot_parse"]))
    print("python projection: descriptor-only inputs ok=%d/%d ; "
          "with the rc420 gate's CASE_DEFAULTS merged ok=%d/%d"
          % (tally["py_ok"], tally["chains"],
             tally["py_ok_with_test_defaults"], tally["chains"]))
    print("CENSUS of %d executable chains (%d chain-variants): "
          "python_ok=%d | C srmech_chain_run ACCEPT=%d REJECT=%d | "
          "C srmech_chain_spec_parse ACCEPT=%d REJECT=%d | "
          "byte_identical=%d | UNATTRIBUTED=%d"
          % (tally["chains"], tally["variants"], tally["py_ok"],
             tally["c_run_accept"], tally["c_run_reject"],
             tally["c_parse_accept"], tally["c_parse_reject"],
             tally["byte_identical"], tally["unattributed"]))
    print("TOML non-finite probe (attributes the front-end declines): %s"
          % [(p["literal"], p["status"]) for p in env["toml_nonfinite_probe"]])
    print("other exported entry points: srmech_dsl_toml_chain_to_json accepts "
          "the descriptor TOML for %d/%d chains ; srmech_chain_catalog_parse "
          "agrees with srmech_chain_spec_parse on %d/%d"
          % (tally["c_toml_front_end_accept"], tally["chains"],
             tally["c_catalog_parse_agrees_with_spec_parse"], tally["chains"]))
    print("shipped dispatcher: _chain_c_eligible true=%d/%d ; "
          "_run_chain_native NATIVE_RAN=%d/%d"
          % (tally["shipped_c_eligible"], tally["chains"],
             tally["shipped_native_ran"], tally["chains"]))
    print("cause classes: %s" % cause_tally)
    print("op-table gap: %d distinct ops used by the 18 chains; %d outside the "
          "C run table (%d dotted, %d bare)"
          % (len(ops_seen), len(ops_outside), len(ops_dotted), len(ops_bare)))
    print("op-table-only reachable set (C parse already accepts; only the op "
          "table blocks the run): %d chains -> %s"
          % (summary["op_table_only_reachable"]["n_chains"],
             summary["op_table_only_reachable"]["chains"]))
    print("rosetta buckets of those ops: %s"
          % summary["rosetta"].get("bucket_counts"))
    print("blocker frequency over the %d chain-variants: %s"
          % (tally["variants"], blockers_seen))
    print("carried-figure reconstructions (does any definition give 11?):")
    for k in sorted(reconstructions):
        print("    %-58s %d%s" % (k, reconstructions[k],
                                  "   <== 11" if reconstructions[k] == 11
                                  else ""))
    print("wrote %s (%d records)" % (args.ndjson, len(records)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
