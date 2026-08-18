"""ADVERSARIAL round-3 re-count of the keyset-validator prototype's JPL claims.

Uses the SHIPPED scanner from python/tests/test_jpl_audit.py (_mask_c_literals +
_scan_functions) so the numbers are the ones the real ratchet would produce, plus
an independent recursion / malloc / goto sweep.

Run:  python3 docs/srmech/notes/_1653_adv3_keyset_jpl_recount.py
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRMECH = HERE.parent
TESTS = SRMECH / "python" / "tests"
TARGET = HERE / "_1653_proto_keyset_validator.c"

spec = importlib.util.spec_from_file_location(
    "_jpl_audit_mod", TESTS / "test_jpl_audit.py"
)
mod = importlib.util.module_from_spec(spec)
sys.modules["_jpl_audit_mod"] = mod
spec.loader.exec_module(mod)

rows = mod._scan_functions(TARGET)
masked = mod._mask_c_literals(TARGET.read_text(encoding="utf-8"))

out = []
for name, lines, asserts in rows:
    out.append({"fn": name, "lines": lines, "asserts": asserts})

max_lines = max((r["lines"] for r in out), default=0)
min_asserts = min((r["asserts"] for r in out), default=0)

# Rule 1 (goto), Rule 3 (dynamic allocation) over MASKED text (comments blanked).
goto_hits = [
    (i, ln)
    for i, ln in enumerate(masked.split("\n"), 1)
    if re.search(r"\b(goto|setjmp|longjmp)\b", ln)
]
alloc_hits = [
    (i, ln)
    for i, ln in enumerate(masked.split("\n"), 1)
    if re.search(r"\b(malloc|calloc|realloc|free|alloca|strdup)\s*\(", ln)
]
# Rule 8: multi-line macros
macro_hits = [
    (i, ln)
    for i, ln in enumerate(TARGET.read_text(encoding="utf-8").split("\n"), 1)
    if ln.lstrip().startswith("#define") and re.search(r"##|__VA_ARGS__|\\\s*$", ln)
]

# Recursion: build the call graph over the prototype's own functions only.
names = {r["fn"] for r in out}
bodies = mod._function_bodies(TARGET)
edges = {}
for fn, body in bodies.items():
    called = set()
    for other in names:
        if re.search(r"\b" + re.escape(other) + r"\s*\(", body) and other != fn:
            called.add(other)
        if other == fn and len(re.findall(r"\b" + re.escape(fn) + r"\s*\(", body)) > 0:
            called.add(fn)
    edges[fn] = called

cycles = []
seen_state = {}


def _dfs(node, stack):
    if node in stack:
        cycles.append(tuple(stack[stack.index(node):] + [node]))
        return
    if seen_state.get(node):
        return
    seen_state[node] = True
    for nxt in sorted(edges.get(node, ())):
        _dfs(nxt, stack + [node])


for n in sorted(edges):
    seen_state = {}
    _dfs(n, [])

report = {
    "file": str(TARGET),
    "total_lines_in_file": len(TARGET.read_text(encoding="utf-8").split("\n")),
    "functions_found": len(out),
    "max_function_lines": max_lines,
    "min_asserts_per_function": min_asserts,
    "rule4_violations": [r for r in out if r["lines"] > mod.RULE_4_MAX_LINES],
    "rule5_violations": [r for r in out if r["asserts"] < mod.RULE_5_MIN_ASSERTS],
    "goto_hits_masked": goto_hits,
    "alloc_hits_masked": alloc_hits,
    "multiline_macro_hits": macro_hits,
    "recursion_cycles": sorted({tuple(c) for c in cycles}),
    "per_function": out,
}
print(json.dumps(report, indent=2))
