#!/usr/bin/env python3
"""gh #1653 — the per-chain GATE MATRIX, measured at rc445.

Round 2 left two figures in conflict: its prose said "only 6 of 11 are
op-table-ONLY" while its own machine line printed ``op_table_ONLY=9``. Neither
is inherited here. This re-derives the matrix from the descriptors and the C
sources directly, so the build knows what it actually has to fix.

THE FOUR MEASURED C-SIDE GATES (gh #1653, source lines re-read at rc445):
  op_table          srmech_compose_run.c cr_dispatch -> SRMECH_ERR_NOT_IMPL
  carrier_width     srmech_compose_run.c cr_value_t has no double / bytes /
                    dense-matrix kind
  ref_grammar       srmech_compose_run.c only a BARE ``.output`` ref is parsed
  real_literal_arg  srmech_compose_run.c cr_json_scalar returns NULL for a
                    JSON double

Discipline: no ALU-magnitude idiom, no numpy, no RNG, no stdlib fractions.
Read-only: edits nothing, writes one NDJSON under notes/.
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "python"))

from srmech.dsl import _cascade_chain as _cc      # noqa: E402
from srmech.dsl import _catalog as _cat           # noqa: E402

C_SRC = os.path.join(HERE, "..", "c", "src", "srmech_compose_run.c")
OUT = os.path.join(HERE, "_1653_gate_matrix_rc445.ndjson")


def c_table_ops():
    """The ops cr_dispatch actually handles — read from the C source, not a list."""
    src = open(C_SRC, encoding="utf-8", errors="replace").read()
    body = src[src.index("static srmech_status_t cr_dispatch"):]
    body = body[:body.index("op not in the C dispatch table")]
    return sorted(set(re.findall(r'memcmp\(op,\s*"([a-z0-9_]+)"', body)))


def walk_steps(steps, depth=0):
    """Yield (step, depth) over a chain, descending into map/fold bodies."""
    for st in steps or []:
        if not isinstance(st, dict):
            continue
        yield st, depth
        for key in ("body", "sub_chain"):
            sub = st.get(key)
            if isinstance(sub, list):
                for pair in walk_steps(sub, depth + 1):
                    yield pair


def step_ops(st):
    out = []
    for k in ("op", "fold_op", "reduce_op", "parallel_body", "map_op"):
        v = st.get(k)
        if isinstance(v, str):
            out.append(v)
    return out


def has_real(node):
    """True if a real (non-integer) number appears anywhere in the args tree."""
    if isinstance(node, bool):
        return False
    if isinstance(node, float):
        return True
    if isinstance(node, dict):
        return any(has_real(v) for v in node.values())
    if isinstance(node, (list, tuple)):
        return any(has_real(v) for v in node)
    return False


INDEXED_REF = re.compile(r"@step\[\d+\]\.output\[")


def has_indexed_ref(node):
    if isinstance(node, str):
        return bool(INDEXED_REF.search(node))
    if isinstance(node, dict):
        return any(has_indexed_ref(v) for v in node.values())
    if isinstance(node, (list, tuple)):
        return any(has_indexed_ref(v) for v in node)
    return False


def main():
    table = c_table_ops()
    catalog = _cat.load_catalog()
    names = sorted(n for n, d in catalog.items()
                   if _cc.descriptor_status(d) == "executable")
    print("C cr_dispatch table: %d ops -> %s" % (len(table), table))
    print("executable descriptors: %d\n" % len(names))

    recs = []
    tally = {"op_table": 0, "carrier_width": 0, "ref_grammar": 0,
             "real_literal_arg": 0, "step_form": 0}
    only = {k: 0 for k in tally}
    hdr = "%-26s %-9s %-9s %-9s %-9s %-9s  %s"
    print(hdr % ("chain", "op_table", "carrier", "ref_gram", "real_lit",
                 "stepform", "n_gates"))
    print("-" * 92)
    for name in names:
        gates = set()
        ops_used = set()
        for entry in _cc._chain_entries(catalog[name]):
            for st, _d in walk_steps(entry.get("steps")):
                ops_used |= set(step_ops(st))
                if "map_over" in st or "body" in st:
                    gates.add("step_form")
                if "fold_op" in st or "fold_class" in st:
                    gates.add("step_form")
                a = st.get("args")
                if has_real(a):
                    gates.add("real_literal_arg")
                if has_indexed_ref(a):
                    gates.add("ref_grammar")
            for case in entry.get("proof_cases") or []:
                if has_real(case.get("inputs")):
                    gates.add("real_literal_arg")
        outside = sorted(o for o in ops_used
                         if o.rpartition(".")[2] not in table and o not in table)
        if outside:
            gates.add("op_table")
        # carrier: does the Python projection return a non-int/str/rational?
        try:
            from srmech.dsl import run_cascade_chain
            e0 = _cc._chain_entries(catalog[name])[0]
            c0 = (e0.get("proof_cases") or [{}])[0]
            v = run_cascade_chain(name, **(c0.get("inputs") or {}))
            if isinstance(v, float) or isinstance(v, (bytes, bytearray)) \
               or hasattr(v, "tolist"):
                gates.add("carrier_width")
            elif isinstance(v, (list, tuple)) and any(isinstance(x, float) for x in v):
                gates.add("carrier_width")
        except Exception:
            pass
        for g in gates:
            tally[g] += 1
        if len(gates) == 1:
            only[next(iter(gates))] += 1
        print(hdr % (name,
                     "X" if "op_table" in gates else ".",
                     "X" if "carrier_width" in gates else ".",
                     "X" if "ref_grammar" in gates else ".",
                     "X" if "real_literal_arg" in gates else ".",
                     "X" if "step_form" in gates else ".",
                     len(gates)))
        recs.append({"record": "chain", "chain": name, "gates": sorted(gates),
                     "n_gates": len(gates), "ops_outside_c_table": outside,
                     "n_ops_used": len(ops_used)})

    print()
    print("chains blocked BY GATE      :", json.dumps(tally, sort_keys=True))
    print("chains blocked by that gate ALONE:", json.dumps(only, sort_keys=True))
    print("chains with NO gate (should run in C already):",
          sum(1 for r in recs if r["n_gates"] == 0))
    recs.append({"record": "summary", "c_table": table, "tally": tally,
                 "only": only, "n_chains": len(names)})
    with open(OUT, "w", encoding="utf-8") as fh:
        for r in recs:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
