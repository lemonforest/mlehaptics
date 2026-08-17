"""ADVERSARIAL round-3: JPL count over ALL 16 functions of the keyset prototype.

The SHIPPED scanner (tests/test_jpl_audit.py::_scan_functions) skips any line
whose lstrip starts with "static const", so it cannot see 3 of the prototype's
16 functions.  This script uses the shipped literal-masker but its OWN
definition finder (an explicit list of the 16 definition lines found by grep)
so every function is measured.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TESTS = HERE.parent / "python" / "tests"
TARGET = HERE / "_1653_proto_keyset_validator.c"

spec = importlib.util.spec_from_file_location("_jpl_audit_mod", TESTS / "test_jpl_audit.py")
mod = importlib.util.module_from_spec(spec)
sys.modules["_jpl_audit_mod"] = mod
spec.loader.exec_module(mod)

masked = mod._mask_c_literals(TARGET.read_text(encoding="utf-8"))
lines = masked.split("\n")

DEF = re.compile(r"^(?:static\s+)?(?:const\s+)?[A-Za-z_][A-Za-z_0-9]*(?:\s+[A-Za-z_][A-Za-z_0-9]*)*\s*\**\s*([A-Za-z_][A-Za-z_0-9]*)\s*\(")

starts: list[tuple[str, int]] = []
for i, ln in enumerate(lines):
    if ln.startswith((" ", "\t", "#", "}", "/", "*")):
        continue
    if ln.rstrip().endswith(";"):
        continue
    m = DEF.match(ln)
    if m is None:
        continue
    if ln.lstrip().startswith(("typedef",)):
        continue
    # the definition must reach an opening brace within 10 lines
    for look in range(i, min(i + 10, len(lines))):
        if "{" in lines[look]:
            starts.append((m.group(1), i))
            break

rows = []
for name, s in starts:
    b = s
    while b < len(lines) and "{" not in lines[b]:
        b += 1
    depth = lines[b].count("{") - lines[b].count("}")
    asserts = sum(1 for k in range(s, b + 1) if "assert(" in lines[k])
    end = b
    for j in range(b + 1, len(lines)):
        depth += lines[j].count("{") - lines[j].count("}")
        if "assert(" in lines[j]:
            asserts += 1
        if depth == 0:
            end = j
            break
    rows.append({"fn": name, "def_line": s + 1, "lines": end - s + 1, "asserts": asserts})

# recursion over the full set
names = {r["fn"] for r in rows}
bodies: dict[str, str] = {}
for r in rows:
    s = r["def_line"] - 1
    bodies[r["fn"]] = "\n".join(lines[s: s + r["lines"]])
edges = {
    fn: {o for o in names if re.search(r"\b" + re.escape(o) + r"\s*\(", body)}
    for fn, body in bodies.items()
}
cycles = []


def dfs(node, stack, seen):
    if node in stack:
        cycles.append(tuple(stack[stack.index(node):] + [node]))
        return
    if node in seen:
        return
    seen.add(node)
    for nxt in sorted(edges.get(node, ())):
        dfs(nxt, stack + [node], seen)


for n in sorted(edges):
    dfs(n, [], set())

print(json.dumps({
    "functions_found": len(rows),
    "max_lines": max(r["lines"] for r in rows),
    "min_asserts": min(r["asserts"] for r in rows),
    "rule4_violations": [r for r in rows if r["lines"] > 60],
    "rule5_violations": [r for r in rows if r["asserts"] < 2],
    "recursion_cycles": sorted({tuple(c) for c in cycles}),
    "rows": rows,
}, indent=2))
