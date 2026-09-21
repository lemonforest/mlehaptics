"""rc479 (`#T1188`) — GENERATING CODE for the reader-contract census.

WHY. Two CI rounds each found a test file the previous round's manifest
extension had not covered, because an extension written from a failure list
covers that failure list and not the property. This censuses the PROPERTY
directly, over every test file, with positive and negative controls.

THE THREE SHAPES that break under contract A:
  A  a native-binding parse asserted NOT to decline  (toml_loads_c(...) is not None)
  B  a parse result asserted to be a float           (isinstance(x, float), is float)
  C  a front-door parse compared to a BARE stdlib loader (no parse_float= hook)

MEASURED 2026-09-21, native cell, 735 test files scanned:
  A   2 lines / 1 file    test_toml_selfhost_parity_rc391.py
  B  29 lines / 9 files
  C  27 lines / 8 files
  Positive controls: the three files already restated appear (rc392 in B+C,
  rc391 in A+B+C, rc401 in B+C). Negative control: 0.

WHAT IT FOUND that no CI round had: test_descriptor_hash_selfhost_rc393.py and
test_profile_toolschema_selfhost_rc394.py — the rc393/rc394 siblings of the
same self-hosting family. Both were RUN and are GREEN (7 passed / 11 passed),
and both were added to tools/ripple_gates.txt anyway, because membership of the
PROPERTY is the criterion and not redness. A green member is what stops the
next reader change from finding them the way CI found their siblings.

HOW TO RE-RUN: point ROOT at a tests/ directory and execute. Pure stdlib, no
numpy, no srmech import.
"""
import pathlib
import re

ROOT = pathlib.Path("/home/skirklan/rc479full/python/tests")
files = sorted(ROOT.glob("test_*.py"))
print("test files scanned:", len(files))

A = re.compile(r"(toml_loads_c|json_loads_c)\s*\([^)]*\)\s*is not None")
A2 = re.compile(r"(got_c|got|native)\s*is not None")
B = re.compile(r"(isinstance\s*\([^,]+,\s*float\s*\)|is\s+float\b)")
C = re.compile(r"(?<!_)(tomllib|_stdlib_toml|json)\.loads?\s*\(")
HOOK = re.compile(r"parse_float\s*=")

hits = {"A": [], "B": [], "C": []}
for f in files:
    txt = f.read_text(encoding="utf-8", errors="replace")
    if not re.search(r"toml_loads_c|json_loads_c|_toml\.loads|_json\.loads", txt):
        continue
    for i, line in enumerate(txt.splitlines(), 1):
        if A.search(line) or (A2.search(line) and "loads_c" in txt):
            hits["A"].append((f.name, i, line.strip()[:95]))
        if B.search(line):
            hits["B"].append((f.name, i, line.strip()[:95]))
        if C.search(line) and not HOOK.search(line):
            hits["C"].append((f.name, i, line.strip()[:95]))

for k in "ABC":
    names = sorted({h[0] for h in hits[k]})
    print()
    print("== class %s: %d lines across %d files ==" % (len(hits[k]) and len(hits[k]) or 0, 0, 0)
          if False else "== class %s: %d lines across %d files ==" % (k, len(hits[k]), len(names)))
    for n in names:
        print("   ", n, sum(1 for h in hits[k] if h[0] == n))

print()
print("POSITIVE CONTROL — the three files already restated must appear:")
for want in ("test_dsl_catalog_selfhost_rc392.py",
             "test_toml_selfhost_parity_rc391.py",
             "test_json_read_selfhost_rc401.py"):
    where = [k for k in "ABC" if any(h[0] == want for h in hits[k])]
    print("   %-42s in classes %s" % (want, where or "NONE  <-- predicate blind"))
print("NEGATIVE CONTROL — a name that cannot exist:")
print("   ", any(h[0] == "test_NOSUCHFILE_ZZZ.py" for k in "ABC" for h in hits[k]))
