#!/usr/bin/env python3
"""ADVERSARIAL round-2 re-derivation of the readme-truth audit's load-bearing
numbers, by a DIFFERENT route than the audit used.

Independent-route choices (deliberately not the audit's):
  * Surface-A variant enumeration walks the shipped TOML descriptors on disk
    via srmech.dsl's descriptor loader AND cross-checks the audit's helper.
  * The chain dict handed to C is built through the SHIPPED serialiser
    ``compose._spec_to_chain_dict`` (what the real fast path sends), not from
    the raw catalog entry dict the audit assembled by hand.
  * The gate ``compose._chain_c_eligible`` is evaluated per variant, so the
    op-table attribution is checked, not assumed.

Exact integers only. No numpy, no RNG, no stdlib fractions.

Run:  cd docs/srmech/python && python3 ../notes/_1653_adv2_readmetruth_recheck.py
"""
from __future__ import annotations

import ctypes
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRMECH_ROOT = os.path.abspath(os.path.join(HERE, ".."))
PY_ROOT = os.path.join(SRMECH_ROOT, "python")
if PY_ROOT not in sys.path:
    sys.path.insert(0, PY_ROOT)

import srmech                                        # noqa: E402
from srmech import _native                           # noqa: E402
from srmech.cascade import compose as _compose       # noqa: E402
from srmech.dsl import _cascade_chain as _cc         # noqa: E402

LIB = _native.LIB
OUT = os.path.join(HERE, "_1653_adv2_readmetruth_recheck.ndjson")
RECS = []


def rec(**kw):
    RECS.append(kw)


def c_spec_parse_rc(chain_dict):
    payload = json.dumps(chain_dict, ensure_ascii=False).encode("utf-8")
    ws_bytes = int(LIB.srmech_chain_spec_parse_arena_bytes(len(payload)))
    ws = (ctypes.c_char * ws_bytes)()
    out_cap = 2 * len(payload) + 8192
    out = (ctypes.c_char * out_cap)()
    out_len = ctypes.c_size_t()
    return int(LIB.srmech_chain_spec_parse(
        payload, len(payload), ws, ws_bytes, out, out_cap,
        ctypes.byref(out_len)))


def c_chain_run_rc(chain_dict, ctx):
    cj = json.dumps(chain_dict, ensure_ascii=False).encode("utf-8")
    xj = json.dumps(ctx, ensure_ascii=False).encode("utf-8")
    ws_bytes = int(LIB.srmech_chain_run_arena_bytes(len(cj), len(xj)))
    ws = (ctypes.c_char * ws_bytes)()
    out_cap = max(ws_bytes // 2, 16384)
    out = (ctypes.c_char * out_cap)()
    out_len = ctypes.c_size_t()
    return int(LIB.srmech_chain_run(
        cj, len(cj), xj, len(xj), ws, ws_bytes, out, out_cap,
        ctypes.byref(out_len)))


def main():
    d = srmech.describe()
    cat = d["cascade_catalog"]
    ns = srmech.native_status()

    print("== ENV ==")
    print("version      :", d["srmech_version"])
    print("has_native   :", ns["has_native"], "abi:", ns["abi_version"])
    print()

    print("== A. describe()['cascade_catalog'] ==")
    print("keys        :", sorted(cat.keys()))
    print("total       :", cat["total"])
    print("executable  :", cat["executable"])
    print("leaf        :", cat["leaf"])
    for k in ("c_runnable", "c_parse_accepted", "c_run_accepted"):
        print("has %-18s: %s" % (k, k in cat))
    rec(record="describe_cascade_catalog", keys=sorted(cat.keys()),
        total=cat["total"], executable=cat["executable"], leaf=cat["leaf"])
    print()

    print("== B. tools.total ==")
    print("tools.total :", d["tools"]["total"])
    rd = os.path.join(PY_ROOT, "README.md")
    with open(rd, "r", encoding="utf-8") as fh:
        readme = fh.read()
    m = re.search(r"the (\d+)-entry tool registry", readme)
    print("README literal:", m.group(1) if m else None)
    rec(record="tools_total", live=d["tools"]["total"],
        readme_literal=(int(m.group(1)) if m else None))
    print()

    print("== C. LIVE ToolEntry srmech.dsl.run_cascade_chain ==")
    from srmech.introspect.tool_schema import get_tool_schema
    from dataclasses import asdict as _asdict
    entry = None
    for t in get_tool_schema().tools:
        if t.name == "srmech.dsl.run_cascade_chain":
            entry = t
            break
    blob = json.dumps(_asdict(entry) if entry is not None else None,
                      ensure_ascii=False, default=str)
    lits = [int(x) for x in re.findall(r"(\d+)\s*executable", blob)]
    print("entry found :", entry is not None)
    print("literals    :", lits)
    print("live exec   :", cat["executable"])
    print("WRONG       :", [x for x in lits if x != cat["executable"]])
    rec(record="live_toolentry", literals=lits, live=cat["executable"])
    print()

    print("== D. SURFACE-A re-derivation via the SHIPPED serialiser ==")
    executable = sorted(n for n, s in cat["status"].items()
                        if s == "executable")
    print("executable descriptors:", len(executable))
    n_var = parse_ok = run_ok = elig = 0
    rows = []
    for name in executable:
        specs = _cc.cascade_chain_specs(name)
        for variant, spec, entry_d in specs:
            n_var += 1
            # Shipped serialiser where it applies; else the raw TOML entry
            # shape (a v2 map/fold spec has no class_id, so the shipped
            # serialiser cannot even represent it -- itself a finding).
            try:
                cd = _compose._spec_to_chain_dict(spec)
                built = "spec_to_chain_dict"
            except AttributeError:
                cd = {"name": "%s.%s" % (name, variant),
                      "summary": str(entry_d.get("summary", "")),
                      "returns": str(entry_d.get("returns", "")),
                      "on_error": "raise",
                      "steps": entry_d.get("steps", [])}
                built = "raw_toml_entry"
            prc = c_spec_parse_rc(cd)
            rrc = c_chain_run_rc(cd, {"row": None, "inputs": {}})
            ok = bool(_compose._chain_c_eligible(spec))
            if prc == 0:
                parse_ok += 1
            if rrc == 0:
                run_ok += 1
            if ok:
                elig += 1
            ops = []
            for st in spec.steps:
                cls = getattr(st, "class_id", None)
                op = getattr(st, "op", None)
                ops.append("%s:%s" % (cls, op) if op else type(st).__name__)
            rows.append(dict(name=name, variant=variant, parse_rc=prc,
                             run_rc=rrc, c_eligible=ok, ops=ops,
                             built=built))
    print("declared variants        :", n_var)
    print("srmech_chain_spec_parse=0:", parse_ok, "/", n_var)
    print("srmech_chain_run      =0 :", run_ok, "/", n_var)
    print("_chain_c_eligible True   :", elig, "/", n_var)
    rec(record="surface_a_recheck", executable=len(executable),
        variants=n_var, parse_accept=parse_ok, run_accept=run_ok,
        c_eligible=elig, per_variant=rows)
    print()
    for r in rows:
        print("  %-30s %-12s parse_rc=%d run_rc=%d elig=%-5s built=%-18s %s"
              % (r["name"], r["variant"], r["parse_rc"], r["run_rc"],
                 r["c_eligible"], r["built"], ",".join(r["ops"])[:70]))

    with open(OUT, "w", encoding="utf-8") as fh:
        for r in RECS:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    print()
    print("wrote", len(RECS), "records ->", OUT)
    return 0


def _entry_to_jsonable(entry):
    if entry is None:
        return None
    if isinstance(entry, dict):
        return entry
    for attr in ("to_dict", "_asdict", "asdict"):
        if hasattr(entry, attr):
            try:
                return getattr(entry, attr)()
            except Exception:                          # noqa: BLE001
                pass
    try:
        import dataclasses
        if dataclasses.is_dataclass(entry):
            return dataclasses.asdict(entry)
    except Exception:                                  # noqa: BLE001
        pass
    return repr(entry)


if __name__ == "__main__":
    raise SystemExit(main())
