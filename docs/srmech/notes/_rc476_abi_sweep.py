"""rc476 (`#T1188`) D1 — the ABI sweep, run by the GATE'S OWN predicates.

rc452, rc455, rc464 and rc475 each shipped an ABI bump RED because a grep
cannot see ``want_abi = 27``.  This enumerates the OLD number across all four
kinds of site before the bump and again after it, so the counts are a
measurement and not a claim.

Run from ``docs/srmech``::

    python3 notes/_rc476_abi_sweep.py <old> <new>

It only REPORTS; nothing here edits.
"""
from __future__ import annotations

import ast
import os
import re
import sys
import tokenize

HERE = os.path.dirname(os.path.abspath(__file__))
SRMECH = os.path.dirname(HERE)
TESTS = os.path.join(SRMECH, "python", "tests")

_PIN_COMMENT = re.compile(r"ABI-PIN:\s*(\w*ABI\w*)\s*==\s*(\d+)")
_ABI_NAME = re.compile(r"abi", re.IGNORECASE)


def _modules():
    for entry in sorted(os.listdir(TESTS)):
        if entry.endswith(".py") and entry.startswith("test_"):
            yield entry, os.path.join(TESTS, entry)


def kind_a():
    """ABI-PIN comment tokens (tokenize, so a docstring quote is excluded)."""
    out = []
    for name, path in _modules():
        with open(path, "rb") as fh:
            try:
                toks = list(tokenize.tokenize(fh.readline))
            except (tokenize.TokenError, SyntaxError):
                continue
        for tok in toks:
            if tok.type != tokenize.COMMENT:
                continue
            m = _PIN_COMMENT.search(tok.string)
            if m:
                out.append((name, tok.start[0], m.group(1), int(m.group(2))))
    return out


def kind_b():
    """``ast.Assign`` of an int literal to a name matching /abi/i — the
    GREP-INVISIBLE half, and the one that shipped RED three times."""
    out = []
    for name, path in _modules():
        with open(path, "r", encoding="utf-8") as fh:
            src = fh.read()
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            if not (isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, int)
                    and not isinstance(node.value.value, bool)):
                continue
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and _ABI_NAME.search(tgt.id):
                    out.append((name, node.lineno, tgt.id, node.value.value))
    return out


def kind_c(old: int):
    """``(NATIVE|EXPECTED)_ABI_VERSION == <old>`` assert-line literals."""
    pat = re.compile(r"(NATIVE|EXPECTED)_ABI_VERSION\s*==\s*%d\b" % old)
    out = []
    for name, path in _modules():
        with open(path, "r", encoding="utf-8") as fh:
            for i, line in enumerate(fh, 1):
                if pat.search(line):
                    out.append((name, i, line.strip()[:90]))
    return out


def kind_d(old: int):
    """Sources + prose, scanned tree-wide rather than from a fixed list, so a
    site nobody listed still shows up."""
    roots = [os.path.join(SRMECH, p) for p in
             ("c/include", "c/src", "c/README.md", "c/JPL_AUDIT.md",
              "python/srmech/_native", "python/README.md", "CLAUDE.md",
              "python/CHANGELOG.md", "srmech_research_notebook.md",
              "python/srmech/introspect", "adr")]
    # No ``\b`` before ABI: it sits inside SRMECH_ABI_VERSION, where the
    # preceding ``_`` is a word character and a boundary never matches.  That
    # exact miss dropped ``srmech.h`` and ``_native/__init__.py`` from the first
    # run of this scan.
    pat = re.compile(r"ABI[^\n]{0,44}?\b%d\b|\b%d\b[^\n]{0,24}?ABI" % (old, old))
    out = []
    for root in roots:
        if os.path.isfile(root):
            files = [root]
        elif os.path.isdir(root):
            files = [os.path.join(dp, f) for dp, _dn, fn in os.walk(root)
                     for f in fn if f.endswith((".c", ".h", ".py", ".md"))]
        else:
            continue
        for path in files:
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as fh:
                    for i, line in enumerate(fh, 1):
                        if pat.search(line):
                            out.append((os.path.relpath(path, SRMECH), i,
                                        line.strip()[:110]))
            except OSError:
                continue
    return out


def main() -> int:
    old = int(sys.argv[1]) if len(sys.argv) > 1 else 27
    new = int(sys.argv[2]) if len(sys.argv) > 2 else old + 1
    a = kind_a()
    b = kind_b()
    c = kind_c(old)
    d = kind_d(old)
    print(f"=== ABI sweep: old={old} new={new} ===")
    print(f"KIND A (ABI-PIN comment tokens): {len(a)}")
    for row in a:
        flag = "OLD" if row[3] == old else ("NEW" if row[3] == new else "other")
        print(f"  [{flag}] {row[0]}:{row[1]} {row[2]} == {row[3]}")
    print(f"KIND B (grep-invisible locals): {len(b)}")
    for row in b:
        flag = "OLD" if row[3] == old else ("NEW" if row[3] == new else "other")
        print(f"  [{flag}] {row[0]}:{row[1]} {row[2]} = {row[3]}")
    print(f"KIND C (assert-line literals at {old}): {len(c)} lines in "
          f"{len({r[0] for r in c})} files")
    for row in c:
        print(f"  {row[0]}:{row[1]}  {row[2]}")
    print(f"KIND D (sources + prose naming ABI near {old}): {len(d)}")
    for row in d:
        print(f"  {row[0]}:{row[1]}  {row[2]}")
    total = len([r for r in a if r[3] == old]) + len([r for r in b if r[3] == old]) \
        + len(c) + len(d)
    print(f"TOTAL live sites at the old number: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
