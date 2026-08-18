#!/usr/bin/env python3
"""gh #1653 round-2 measurement 3 of 3 — run the SHIPPED JPL ratchet over the
map-arm prototype.

Report section 6.2 says the map arm's 60-line / 2-assert feasibility is
"reasoned from shipped idioms, NOT measured". This script measures it, and it
measures it with the RATCHET'S OWN CODE rather than a re-implementation: it
imports `_scan_functions` (Rule 4 length + Rule 5 asserts), `_function_bodies`
+ `_CALL_RE` + `_C_KEYWORDS_CALLLIKE` (Rule 1 recursion) and `_mask_c_literals`
straight out of python/tests/test_jpl_audit.py and points them at
notes/_1653_proto_map.c. A re-implementation could disagree with the gate; this
cannot.

Rules covered mechanically, exactly as the shipped gate covers them:
  Rule 1  no goto / setjmp / longjmp, and NO new recursion cycle
  Rule 3  no malloc / calloc / realloc / free
  Rule 4  every function <= 60 lines
  Rule 5  every function >= 2 asserts
  Rule 8  no multi-line macros

Writes docs/srmech/notes/_1653_proto_map_jpl_rc444.ndjson. Exit 0 iff the
prototype is clean on all five.
"""

import importlib.util
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
AUDIT = HERE.parents[0] / "python" / "tests" / "test_jpl_audit.py"
TARGETS = [HERE / "_1653_proto_map.c", HERE / "_1653_proto_fold.c"]
OUT = HERE / "_1653_proto_map_jpl_rc444.ndjson"


def load_audit():
    spec = importlib.util.spec_from_file_location("_jpl_audit_probe", AUDIT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def cycles_in(mod, path):
    """Tarjan over ONE file's call graph — the same construction
    `_recursion_cycles` uses over the whole tree, restricted to this file."""
    bodies = mod._function_bodies(path)
    graph = {
        name: {c for c in (m.group(1) for m in mod._CALL_RE.finditer(body))
               if c in bodies and c not in mod._C_KEYWORDS_CALLLIKE}
        for name, body in bodies.items()
    }
    cycles = {(n,) for n in graph if n in graph[n]}
    index, low, on, stack, counter = {}, {}, {}, [], 0
    for root in list(graph):
        if root in index:
            continue
        work = [(root, iter(graph[root]))]
        index[root] = low[root] = counter
        counter += 1
        stack.append(root)
        on[root] = True
        while work:
            node, it = work[-1]
            descended = False
            for w in it:
                if w not in index:
                    index[w] = low[w] = counter
                    counter += 1
                    stack.append(w)
                    on[w] = True
                    work.append((w, iter(graph[w])))
                    descended = True
                    break
                if on.get(w):
                    low[node] = min(low[node], index[w])
            if descended:
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[node])
            if low[node] == index[node]:
                comp = []
                while True:
                    w = stack.pop()
                    on[w] = False
                    comp.append(w)
                    if w == node:
                        break
                if len(comp) > 1:
                    cycles.add(tuple(sorted(comp)))
    return cycles, graph


def main():
    mod = load_audit()
    rows, hard_fail = [], 0
    for path in TARGETS:
        if not path.exists():
            print(f"MISSING {path}")
            hard_fail += 1
            continue
        text = path.read_text(encoding="utf-8")
        masked = mod._mask_c_literals(text)
        fns = mod._scan_functions(path)
        long_fns = [(n, ln) for n, ln, _ in fns if ln > mod.RULE_4_MAX_LINES]
        thin_fns = [(n, a) for n, _, a in fns if a < mod.RULE_5_MIN_ASSERTS]
        goto = re.findall(r"\b(goto|setjmp|longjmp)\b", masked)
        alloc = re.findall(r"\b(malloc|calloc|realloc|free)\s*\(", masked)
        multi_macro = [
            i + 1 for i, ln in enumerate(masked.split("\n"))
            if ln.lstrip().startswith("#define") and ln.rstrip().endswith("\\")
        ]
        cyc, graph = cycles_in(mod, path)
        clean = (not long_fns and not thin_fns and not goto and not alloc
                 and not multi_macro and not cyc)
        if not clean:
            hard_fail += 1
        rows.append({
            "record": "jpl_scan",
            "file": path.name,
            "functions": len(fns),
            "rule_1_goto_setjmp_longjmp": len(goto),
            "rule_1_recursion_cycles": sorted(tuple(c) for c in cyc),
            "rule_3_alloc_calls": len(alloc),
            "rule_4_max_lines_seen": max((ln for _, ln, _ in fns), default=0),
            "rule_4_violations": long_fns,
            "rule_5_min_asserts_seen": min((a for _, _, a in fns), default=0),
            "rule_5_violations": thin_fns,
            "rule_8_multiline_macros": multi_macro,
            "call_graph_edges": sum(len(v) for v in graph.values()),
            "clean_on_all_five": clean,
            "per_function": [{"name": n, "lines": ln, "asserts": a}
                             for n, ln, a in
                             sorted(fns, key=lambda t: -t[1])],
        })

    with OUT.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")

    print(f"=== JPL ratchet, run with {AUDIT.name}'s OWN scanner ===")
    print(f"    RULE_4_MAX_LINES={mod.RULE_4_MAX_LINES}  "
          f"RULE_5_MIN_ASSERTS={mod.RULE_5_MIN_ASSERTS}")
    for r in rows:
        print(f"\n--- {r['file']} ---")
        print(f"  functions ............... {r['functions']}")
        print(f"  Rule 1 goto/setjmp/longjmp {r['rule_1_goto_setjmp_longjmp']}")
        print(f"  Rule 1 recursion cycles .. {r['rule_1_recursion_cycles']}")
        print(f"  Rule 3 alloc calls ....... {r['rule_3_alloc_calls']}")
        print(f"  Rule 4 longest function .. {r['rule_4_max_lines_seen']} "
              f"lines (cap {mod.RULE_4_MAX_LINES})")
        print(f"  Rule 4 violations ........ {r['rule_4_violations']}")
        print(f"  Rule 5 fewest asserts .... {r['rule_5_min_asserts_seen']} "
              f"(floor {mod.RULE_5_MIN_ASSERTS})")
        print(f"  Rule 5 violations ........ {r['rule_5_violations']}")
        print(f"  Rule 8 multiline macros .. {r['rule_8_multiline_macros']}")
        print(f"  CLEAN ON ALL FIVE ........ {r['clean_on_all_five']}")
        print("  per-function (lines, asserts), longest first:")
        for f in r["per_function"]:
            print(f"    {f['lines']:3d} lines  {f['asserts']:2d} asserts  "
                  f"{f['name']}")
    print(f"\nwrote {OUT}")
    return 0 if hard_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
