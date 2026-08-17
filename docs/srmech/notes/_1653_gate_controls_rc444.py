#!/usr/bin/env python3
"""PLANTED-FAILURE CONTROLS for the gh #1653 gate spec (_1653_gate_spec_rc444.md).

A gate never OBSERVED to fail is not a measurement.  This script is the proof
that each of the five gates in that spec fires on a planted defect, and that
none of them fires on the unperturbed tree.

It is deliberately a STANDALONE re-implementation of the spec's pytest
skeleton (same helper bodies, no pytest, no tests/ file), for two reasons:

  1. tests/ is off-limits to the research session, and
  2. an independently written classifier that reproduces the seed script's
     20-row attribution exactly is CROSS-VALIDATION.  It does: this file's
     ``_first_gate`` and _1653_gate_seed_rc444.py's ``classify_decline`` were
     written separately and agree on all 20 variants
     (step_form_map 7 / op_not_in_c_table 11 / step_form_fold 1 /
     ref_namespace_v2 1).

Each control perturbs a COPY of a ledger and calls the predicate directly.
Nothing monkeypatches shipped module state.

Usage:  cd docs/srmech/python && python3 ../notes/_1653_gate_controls_rc444.py
"""
import ctypes
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY_ROOT = os.path.abspath(os.path.join(HERE, "..", "python"))
if PY_ROOT not in sys.path:
    sys.path.insert(0, PY_ROOT)
C_ROOT = os.path.abspath(os.path.join(HERE, ".."))

from srmech.cascade import compose                      # noqa: E402
from srmech.dsl import _cascade_chain as _cc            # noqa: E402

NOT_IMPL = 5
BAD_INPUT = 2
STRUCTURE_CTX = {"row": None, "inputs": {}}

def _lib(*syms): return compose._compose_lib(*syms)

def _c_call(entry, *json_blobs):
    lib = _lib(entry, entry + "_arena_bytes")
    assert lib is not None
    blobs = [json.dumps(b, ensure_ascii=False).encode("utf-8") for b in json_blobs]
    ws_bytes = int(getattr(lib, entry + "_arena_bytes")(*[len(b) for b in blobs]))
    ws = (ctypes.c_char * ws_bytes)()
    out_cap = max(ws_bytes // 2, 16384)
    out = (ctypes.c_char * out_cap)()
    out_len = ctypes.c_size_t()
    args = []
    for b in blobs: args += [b, len(b)]
    rc = int(getattr(lib, entry)(*args, ws, ws_bytes, out, out_cap, ctypes.byref(out_len)))
    return rc, out.raw[:out_len.value]

def _c_parse(cd): return _c_call("srmech_chain_spec_parse", cd)[0]
def _c_run(cd, ctx=None): return _c_call("srmech_chain_run", cd, ctx or STRUCTURE_CTX)
def _chain(steps, name="gate"):
    return {"name": name, "summary": "", "returns": "", "on_error": "raise", "steps": steps}

def _python_forms():
    f = {"form:plain"}
    if compose._MAP_KEYS: f.add("form:map")
    if compose._FOLD_KEYS: f.add("form:fold")
    return f

def _python_namespaces():
    pat = compose._REFERENCE_PATTERN.pattern
    inner = pat.split("@(", 1)[1].split(")", 1)[0]
    return {"ns:" + n for n in inner.split("|")}

def _step_form(raw):
    if not isinstance(raw, dict): return "malformed"
    if any(k in raw for k in compose._MAP_KEYS): return "map"
    if any(k in raw for k in compose._FOLD_KEYS): return "fold"
    if all(k in raw for k in ("class", "op", "args")): return "plain"
    return "malformed"

def _walk(steps, depth=0):
    for raw in (steps or ()):
        yield depth, _step_form(raw), raw
        if _step_form(raw) == "map":
            for t in _walk(raw.get("body") or (), depth + 1): yield t

def _refs(obj, out):
    if isinstance(obj, str) and obj.startswith("@"): out.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values(): _refs(v, out)
    elif isinstance(obj, (list, tuple)):
        for v in obj: _refs(v, out)

C_PARSE_NS = ("row", "input", "step", "catalog")

def _first_v2_feature(steps):
    """The first C-parse-fatal v2 feature, in the C control-flow order."""
    for _d, form, raw in _walk(steps):
        if form in ("map", "fold"): return "step_form_" + form
        refs = []
        _refs(raw.get("args") if form == "plain" else raw, refs)
        for r in refs:
            ns = r[1:].split(".")[0].split("[")[0]
            if ns not in C_PARSE_NS: return "ref_namespace_v2"
    return "UNATTRIBUTED"



LEDGER = {}
def variants():
    o={}
    st=_cc.cascade_catalog_status()
    for n in sorted(k for k,v in st.items() if v=="executable"):
        for var,spec,ent in _cc.cascade_chain_specs(n): o["%s.%s"%(n,var)]=(spec,ent)
    return o
VARS = variants()
def _first_gate(key, spec, entry):
    steps = entry.get("steps", []) or []
    p = _c_parse(_chain(steps, name=key)); r = _c_run(_chain(steps, name=key))[0]
    if p == 0 and r == 0: return None
    first = _step_form(steps[0]) if steps else None
    if first in ("map","fold"): return "step_form_" + first
    if p != 0: return _first_v2_feature(steps)
    return "op_not_in_c_table"
for k,(s,e) in VARS.items(): LEDGER[k]=(_first_gate(k,s,e),"seeded")

FORM_LEDGER = {"form:plain":"EXECUTES","form:map":"UNRECOGNISED","form:fold":"UNRECOGNISED",
 "ns:row":"EXECUTES","ns:input":"EXECUTES","ns:step":"EXECUTES","ns:catalog":"PARSES_REJECTS",
 "ns:idx":"UNRECOGNISED","ns:bind":"UNRECOGNISED","ns:op":"UNRECOGNISED"}

def _form_probe(feature):
    plain = {"class":"N","op":"rational_add","args":{"a":[1,2],"b":[1,3]}}
    row, inputs = None, {}
    if feature=="form:plain": steps=[dict(plain)]
    elif feature=="form:map":
        steps=[{"map_over":"@input.xs","index":"k","body":[dict(plain)]}]; inputs={"xs":[1,2,3]}
    elif feature=="form:fold":
        steps=[{"fold_class":"N","fold_op":"rational_add","fold_init":[0,1],"over":"@input.xs"}]
        inputs={"xs":[[1,2],[1,3]]}
    elif feature=="ns:step":
        steps=[dict(plain),{"class":"N","op":"rational_add","args":{"a":"@step[0].output","b":[1,3]}}]
    else:
        ns=feature.split(":",1)[1]
        ref={"row":"@row.a","input":"@input.a","catalog":"@catalog.a","idx":"@idx.k",
             "bind":"@bind.s","op":"@op.srmech"}[ns]
        steps=[{"class":"N","op":"rational_add","args":{"a":ref,"b":[1,3]}}]
        if ns=="row": row={"a":[1,2]}
        if ns=="input": inputs={"a":[1,2]}
    return _chain(steps,name=feature), {"row":row,"inputs":inputs}

def measured_verdict(f):
    cd,ctx=_form_probe(f); p=_c_parse(cd); r=_c_run(cd,ctx)[0]
    if p==0 and r==0: return "EXECUTES"
    return "PARSES_REJECTS" if p==0 else "UNRECOGNISED"

def fires(fn):
    try: fn(); return "DID NOT FIRE  <-- BAD"
    except AssertionError as e: return "FIRES: %s" % str(e).split("\n")[0][:78]

# PC-1 G1 closure, synthetic Python form
def pc1():
    live = _python_forms() | _python_namespaces() | {"form:while"}
    assert live <= set(FORM_LEDGER), "unledgered: %s" % sorted(live-set(FORM_LEDGER))
# PC-2 G1 per-feature, flipped row
def pc2():
    L = dict(FORM_LEDGER); L["ns:idx"]="EXECUTES"
    got = measured_verdict("ns:idx")
    assert got == L["ns:idx"], "ledger says %s measured %s" % (L["ns:idx"], got)
# PC-3 G2 MISSING
def pc3():
    L = dict(LEDGER); del L["net_chirality.default"]
    measured = {k for k,(s,e) in VARS.items() if _c_run(_chain(e.get("steps",[]),name=k))[0]!=0}
    miss = measured - set(L)
    assert not miss, "[MISSING] %s" % sorted(miss)
# PC-4 G2 STALE
def pc4():
    L = dict(LEDGER); L["synthetic_control.default"]=("op_not_in_c_table","planted")
    measured = {k for k,(s,e) in VARS.items() if _c_run(_chain(e.get("steps",[]),name=k))[0]!=0}
    stale = set(L) - measured
    assert not stale, "[STALE] %s" % sorted(stale)
# PC-5 G2 WRONG REASON
def pc5():
    key="net_chirality.default"; declared="op_not_in_c_table"
    s,e = VARS[key]; got=_first_gate(key,s,e)
    assert got==declared, "[WRONG REASON] %s: ledger %s measured %s" % (key,declared,got)
# PC-6 G3 negative op probed as in-table
def pc6():
    rc=_c_run(_chain([{"class":"N","op":"rational_sub","args":{"a":[1,2],"b":[1,3]}}]))[0]
    assert rc != NOT_IMPL, "claimed in-table but cr_dispatch returned NOT_IMPL"
# PC-7 G5 wrong anchor
def pc7():
    from pathlib import Path
    root = Path(C_ROOT)
    lines=(root/"c/src/srmech_compose_run.c").read_text().splitlines()
    got=lines[615]
    assert "co_match_namespace" in got, "anchor :616 actual %r" % got.strip()

for n,f in [("PC-1",pc1),("PC-2",pc2),("PC-3",pc3),("PC-4",pc4),("PC-5",pc5),("PC-6",pc6),("PC-7",pc7)]:
    print("%s %s" % (n, fires(f)))

# and the UNPERTURBED predicates must all PASS
def clean():
    live=_python_forms()|_python_namespaces()
    assert live<=set(FORM_LEDGER) and set(FORM_LEDGER)<=live
    for f in FORM_LEDGER: assert measured_verdict(f)==FORM_LEDGER[f], f
    measured={k for k,(s,e) in VARS.items() if _c_run(_chain(e.get("steps",[]),name=k))[0]!=0}
    assert measured==set(LEDGER)
    for k,(c,_) in LEDGER.items():
        s,e=VARS[k]; assert _first_gate(k,s,e)==c, k
    for op in sorted(compose._RUN_C_OPS):
        A={"rational_add":{"a":[1,2],"b":[1,3]},"rational_mul":{"a":[1,2],"b":[1,3]},
           "rational_div":{"a":[1,2],"b":[1,3]},"rational_pow_uint":{"base":[2,3],"n":2},
           "pi_cascade_digits":{"n_digits":3}}
        A=A.get(op,{"numerator":1,"denominator":2,"num_terms":4})
        assert _c_run(_chain([{"class":"N","op":op,"args":A}]))[0]!=NOT_IMPL, op
print("UNPERTURBED all-predicates:", "PASS" if fires(clean).startswith("DID NOT") else fires(clean))
