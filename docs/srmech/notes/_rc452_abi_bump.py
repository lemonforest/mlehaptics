"""rc452 (`#T1166`) scratch — the ABI 20 -> 21 sweep, with its predicate stated.

An ABI bump in this tree is not one edit. rc442's bump missed the pin sweep and
took NINE CI jobs red across four cells; the preflight for this rc re-measured
the surface and found the same shape. The sweep is therefore MECHANICAL and
COUNTED, never eyeballed:

  * ``c/include/srmech.h``               the macro SSoT (1)
  * ``python/srmech/_native/__init__.py``the ctypes shim's EXPECTED (1)
  * 20 literal ``== 20`` pins across 17 test files
  * ``tests/test_introspect.py``         ``status['expected_abi']`` — the one
                                         pin a ``_ABI_VERSION == 20`` grep
                                         structurally CANNOT find
  * ``docs/srmech/CLAUDE.md``            the narrative SSoT prose
  * ``docs/srmech/c/README.md``          the "### ABI" prose

``test_abi_prose_currency_rc449.py`` needs NO numeric edit: it compares the two
PROSE files against the macro, so it goes green when the prose moves.

Run from ``docs/srmech`` (the srmech subtree root).
"""
import re
import sys
from pathlib import Path

ROOT = Path(".").resolve()
OLD, NEW = 20, 21

PIN = re.compile(r"((?:NATIVE|EXPECTED)_ABI_VERSION\s*==\s*)%d\b" % OLD)
INTROSPECT_PIN = re.compile(r"(\[[\"']expected_abi[\"']\]\s*==\s*)%d\b" % OLD)

changed = []


def edit(path: Path, subs):
    with open(path, encoding="utf-8", newline="") as fh:
        raw = fh.read()
    nl = "\r\n" if "\r\n" in raw else "\n"
    s = raw.replace("\r\n", "\n")
    total = 0
    for pat, rep in subs:
        s, n = pat.subn(rep, s)
        total += n
    if total:
        # Written back in the convention the file ALREADY uses. The worktree is
        # mixed (core.autocrlf=true, HEAD is LF); a wrong-convention write
        # rewrites every line on disk while git diff stays clean, so a one-line
        # change would hide inside a whole-file rewrite.
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(s.replace("\n", nl))
        changed.append((str(path), total))
    return total


# 1. the macro SSoT
n = edit(ROOT / "c/include/srmech.h",
         [(re.compile(r"^#define SRMECH_ABI_VERSION %d$" % OLD, re.M),
           "#define SRMECH_ABI_VERSION %d" % NEW)])
print("macro SSoT           : %d" % n)

# 2. the ctypes shim
n = edit(ROOT / "python/srmech/_native/__init__.py",
         [(re.compile(r"^EXPECTED_ABI_VERSION: int = %d$" % OLD, re.M),
           "EXPECTED_ABI_VERSION: int = %d" % NEW)])
print("shim EXPECTED        : %d" % n)

# 3. the literal pins + 4. the introspect status pin
pins = 0
files = 0
for p in sorted((ROOT / "python/tests").glob("test_*.py")):
    n = edit(p, [(PIN, r"\g<1>%d" % NEW), (INTROSPECT_PIN, r"\g<1>%d" % NEW)])
    if n:
        pins += n
        files += 1
print("literal pins         : %d across %d file(s)" % (pins, files))

# 5/6. the two PROSE files the rc449 gate reads
n = edit(ROOT / "CLAUDE.md",
         [(re.compile(r"(C ABI version is currently \*\*)%d(\*\*\s*\(`SRMECH_ABI_VERSION = )%d(`)"
                      % (OLD, OLD)), r"\g<1>%d\g<2>%d\g<3>" % (NEW, NEW))])
print("CLAUDE.md narrative  : %d" % n)
n = edit(ROOT / "c/README.md",
         [(re.compile(r"(C ABI version is \*\*)%d(\*\*\s*\(`SRMECH_ABI_VERSION )%d(`)"
                      % (OLD, OLD)), r"\g<1>%d\g<2>%d\g<3>" % (NEW, NEW))])
print("c/README.md          : %d" % n)

print("\nfiles touched: %d" % len(changed))
for path, n in changed:
    print("  %3d  %s" % (n, path))

# The residual check: nothing anywhere should still pin == 20.
left = []
for p in sorted((ROOT / "python/tests").glob("test_*.py")):
    txt = p.read_text(encoding="utf-8")
    if PIN.search(txt) or INTROSPECT_PIN.search(txt):
        left.append(str(p))
print("\nresidual == %d pins  : %d %s" % (OLD, len(left), left))
sys.exit(1 if left else 0)
