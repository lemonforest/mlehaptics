"""rc473 (`#T1188`) scratch — the ABI 25 -> 26 sweep, with its predicate stated.

This is ``notes/_rc452_abi_bump.py`` re-pointed at ``OLD, NEW = 25, 26``, with
the one residual that script's own CHANGELOG entry records closed: it did NOT
reach the ABI-named int LOCALS (its ``PIN`` regex requires
``_ABI_VERSION ==``), and ``tests/test_abi_pin_sites_agree_rc464.py`` exists
because rc452, rc455 and rc464 each swept the comments to the new value and
left those locals on the old one, shipping both bus tests RED. Sweeping them
here does not replace running that gate afterwards; it stops this sweep from
being the fourth instance.

PREDICATES, stated beside every count this prints (the tree already carries a
filed bug — ``notes/_1653_gap_ledger.ndjson`` id
``T1159_abi_prose_22_files_vs_22_lines`` — about an ABI count whose prose said
"files" where the number was lines, so each label below says which it is):

  PIN         ``(NATIVE|EXPECTED)_ABI_VERSION == <N>``     (comment OR assert)
  INTROSPECT  ``["expected_abi"] == <N>``                  (the SUBSCRIPT form,
              which a ``_ABI_VERSION ==`` grep structurally cannot find)
  LOCAL       an assignment ``<name containing "abi"> = <N>`` (the AST form,
              which no grep for ``_ABI_VERSION`` can find either)
  README_NS   the worked ``native_status()`` block's ``'abi_version': <N>`` /
              ``'expected_abi': <N>``
  README_HDR  ``**ABI <N>** at this release``
  NOTEBOOK    the Live-at stamp's ``**`SRMECH_ABI_VERSION` is <N>**``

NARRATIVE edits are NOT done here and are not mechanical: the v26 block in
``c/include/srmech.h``, the v26 paragraphs in ``docs/srmech/CLAUDE.md`` and
``docs/srmech/c/README.md``, the NEW ``moves **25 -> 26**`` paragraph
prepended above ``python/README.md``'s existing one (the rc419 gate takes the
FIRST match, so appending would falsify the v25 record), and the two test
failure-message narrations in ``test_bus.py`` / ``test_introspect.py``. Those
are hand-written, because a sweep that rewrites a story is how a correct
cardinal ends up sitting above a stale one.

``srmech/introspect/_c_claims.py`` is GENERATED and is NOT touched here —
``tools/regen_all.py`` produces it and ``tools/hooks/generated_file_edit_blocker.py``
refuses a hand-edit.

Run from ``docs/srmech`` (the srmech subtree root).
"""
import ast
import re
import sys
from pathlib import Path

ROOT = Path(".").resolve()
OLD, NEW = 25, 26

PIN = re.compile(r"((?:NATIVE|EXPECTED)_ABI_VERSION\s*==\s*)%d\b" % OLD)
INTROSPECT_PIN = re.compile(r"(\[[\"']expected_abi[\"']\]\s*==\s*)%d\b" % OLD)
LOCAL_PIN = re.compile(r"^(\s*[A-Za-z_][A-Za-z0-9_]*abi[A-Za-z0-9_]*\s*=\s*)%d\b"
                       % OLD, re.M | re.I)

changed = []


def edit(path, subs):
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
        # checked out by Windows git with core.autocrlf=true while HEAD is LF;
        # a wrong-convention write rewrites every line on disk and the one-line
        # change hides inside a whole-file flip.
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(s.replace("\n", nl))
        changed.append((str(path), total))
    return total


def abi_locals(path):
    """Every ``<name matching /abi/i> = <int>`` binding, via AST not grep."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, ast.Constant):
            continue
        if not isinstance(node.value.value, int) or isinstance(node.value.value, bool):
            continue
        for t in node.targets:
            if isinstance(t, ast.Name) and "abi" in t.id.lower():
                found.append((t.id, node.value.value, node.lineno))
    return found


# 1. the macro SSoT
n = edit(ROOT / "c/include/srmech.h",
         [(re.compile(r"^#define SRMECH_ABI_VERSION %d$" % OLD, re.M),
           "#define SRMECH_ABI_VERSION %d" % NEW)])
print("macro SSoT                 : %d line(s)" % n)

# 2. the ctypes shim
n = edit(ROOT / "python/srmech/_native/__init__.py",
         [(re.compile(r"^EXPECTED_ABI_VERSION: int = %d$" % OLD, re.M),
           "EXPECTED_ABI_VERSION: int = %d" % NEW)])
print("shim EXPECTED              : %d line(s)" % n)

# 3. PIN + INTROSPECT + LOCAL across tests/
pins = intro = locs = 0
files = set()
for p in sorted((ROOT / "python/tests").glob("test_*.py")):
    before = abi_locals(p)
    a = edit(p, [(PIN, r"\g<1>%d" % NEW)])
    b = edit(p, [(INTROSPECT_PIN, r"\g<1>%d" % NEW)])
    c = edit(p, [(LOCAL_PIN, r"\g<1>%d" % NEW)])
    if a or b or c:
        files.add(p.name)
    pins += a
    intro += b
    locs += c
    if c:
        print("    LOCAL in %s: %s" % (p.name, before))
print("PIN pins                   : %d line(s)" % pins)
print("INTROSPECT subscript pins  : %d line(s)" % intro)
print("LOCAL abi-named int pins   : %d line(s)" % locs)
print("distinct test FILES touched: %d" % len(files))

# 4. the two rc449-gated prose cardinals
n = edit(ROOT / "CLAUDE.md",
         [(re.compile(r"(C ABI version is currently \*\*)%d(\*\*\s*\(`SRMECH_ABI_VERSION = )%d(`)"
                      % (OLD, OLD)), r"\g<1>%d\g<2>%d\g<3>" % (NEW, NEW))])
print("CLAUDE.md cardinal         : %d line(s)" % n)
n = edit(ROOT / "c/README.md",
         [(re.compile(r"(C ABI version is \*\*)%d(\*\*\s*\(`SRMECH_ABI_VERSION )%d(`)"
                      % (OLD, OLD)), r"\g<1>%d\g<2>%d\g<3>" % (NEW, NEW))])
print("c/README.md cardinal       : %d line(s)" % n)

# 5. python/README.md — the rc419-gated header + the worked native_status block
n = edit(ROOT / "python/README.md", [
    (re.compile(r"(\*\*ABI )%d(\*\* at this release)" % OLD, re.M),
     r"\g<1>%d\g<2>" % NEW),
    (re.compile(r"('abi_version': )%d(,)" % OLD), r"\g<1>%d\g<2>" % NEW),
    (re.compile(r"('expected_abi': )%d(,)" % OLD), r"\g<1>%d\g<2>" % NEW),
])
print("python/README.md pins      : %d line(s)" % n)

# 6. the notebook Live-at stamp (both halves are gated: rc token AND integer)
n = edit(ROOT / "srmech_research_notebook.md", [
    (re.compile(r"(\*\*`SRMECH_ABI_VERSION` is )%d(\*\*)" % OLD),
     r"\g<1>%d\g<2>" % NEW),
])
print("notebook Live-at integer   : %d line(s)" % n)

print("\nfiles touched: %d" % len(changed))
for path, n in changed:
    print("  %3d  %s" % (n, path))

# The residual check, over ALL FOUR predicates rather than the two rc452 had.
left = []
for p in sorted((ROOT / "python/tests").glob("test_*.py")):
    txt = p.read_text(encoding="utf-8")
    if PIN.search(txt) or INTROSPECT_PIN.search(txt) or LOCAL_PIN.search(txt):
        left.append(p.name)
stale_locals = []
for p in sorted((ROOT / "python/tests").glob("test_*.py")):
    for name, val, lineno in abi_locals(p):
        if val == OLD:
            stale_locals.append((p.name, lineno, name, val))
print("\nresidual == %d (regex)    : %d %s" % (OLD, len(left), left))
print("residual abi locals == %d : %d %s" % (OLD, len(stale_locals), stale_locals))
sys.exit(1 if (left or stale_locals) else 0)
