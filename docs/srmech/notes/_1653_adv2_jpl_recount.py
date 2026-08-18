"""ADVERSARIAL round-2 re-count of the JPL Power-of-Ten mechanical rules.

Written from scratch (NOT importing tests/test_jpl_audit.py) so that a bug
shared with the shipped scanner cannot hide a violation in
notes/_1653_proto_map.c.

Counts, per function definition:
  Rule 4  physical lines from the signature line through the closing brace
  Rule 5  assert( occurrences inside the body (comments/strings masked)
Plus whole-file:
  Rule 1  goto / setjmp / longjmp tokens; direct-recursion + call-cycle scan
  Rule 3  malloc / calloc / realloc / free / alloca / aligned_alloc / strdup
  Rule 8  multi-line function-like macros

Usage: python3 _1653_adv2_jpl_recount.py <file.c> [...]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def mask(text: str) -> str:
    """Blank comment / string / char-literal CONTENT, keep every newline."""
    out: list[str] = []
    i, n = 0, len(text)
    st = "code"
    while i < n:
        c = text[i]
        nx = text[i + 1] if i + 1 < n else ""
        if st == "code":
            if c == "/" and nx == "/":
                st, i = "lc", i + 2
                out.append("  ")
                continue
            if c == "/" and nx == "*":
                st, i = "bc", i + 2
                out.append("  ")
                continue
            if c == '"':
                st, i = "s", i + 1
                out.append(" ")
                continue
            if c == "'":
                st, i = "q", i + 1
                out.append(" ")
                continue
            out.append(c)
            i += 1
            continue
        if st == "lc":
            if c == "\n":
                st = "code"
                out.append("\n")
            else:
                out.append(" ")
            i += 1
            continue
        if st == "bc":
            if c == "*" and nx == "/":
                st, i = "code", i + 2
                out.append("  ")
                continue
            out.append("\n" if c == "\n" else " ")
            i += 1
            continue
        # string / char
        if c == "\\":
            out.append("  ")
            i += 2
            continue
        if (st == "s" and c == '"') or (st == "q" and c == "'"):
            st = "code"
            out.append(" ")
            i += 1
            continue
        out.append("\n" if c == "\n" else " ")
        i += 1
    return "".join(out)


# A definition line: something(...) ... {  at column 0-ish, not a control kw.
_KW = {
    "if", "for", "while", "switch", "do", "else", "return", "sizeof",
    "typedef", "struct", "union", "enum", "assert", "case", "default",
}
_DEF = re.compile(r"^[A-Za-z_][A-Za-z0-9_ \t\*\(\),\[\]]*\)\s*$")
_NAME = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(")


def scan_functions(path: Path):
    raw = path.read_text(encoding="utf-8")
    src = mask(raw)
    lines = src.split("\n")
    rawlines = raw.split("\n")
    fns = []
    i = 0
    n = len(lines)
    while i < n:
        ln = lines[i]
        stripped = ln.strip()
        # candidate: a line whose first non-space char is at col 0 (a
        # top-level definition), containing '(' and ending in '{' or with
        # the '{' on a following line.
        if ln and not ln[0].isspace() and "(" in ln and not stripped.startswith("#"):
            # collect the signature, possibly spanning lines, up to '{' or ';'
            sig = ln
            j = i
            while "{" not in sig and ";" not in sig and j + 1 < n:
                j += 1
                sig += " " + lines[j].strip()
                if j - i > 6:
                    break
            if "{" in sig and ";" not in sig.split("{")[0]:
                head = sig.split("{")[0]
                m = list(_NAME.finditer(head))
                if m:
                    nm = m[-1].group(1)
                    if nm not in _KW and "=" not in head.split("(")[0]:
                        # walk brace depth from line j
                        depth = 0
                        k = j
                        started = False
                        while k < n:
                            depth += lines[k].count("{")
                            depth -= lines[k].count("}")
                            if lines[k].count("{"):
                                started = True
                            if started and depth <= 0:
                                break
                            k += 1
                        nlines = k - i + 1
                        body = "\n".join(lines[i:k + 1])
                        asserts = body.count("assert(")
                        calls = set(_NAME.findall(body)) - _KW
                        # the definition line itself spells `nm(` — that is
                        # not a call. Only keep nm as a self-call if it
                        # appears MORE than once in the body.
                        if len(re.findall(
                            r"\b" + re.escape(nm) + r"\s*\(", body
                        )) < 2:
                            calls.discard(nm)
                        fns.append({
                            "name": nm,
                            "line": i + 1,
                            "lines": nlines,
                            "asserts": asserts,
                            "calls": sorted(calls),
                            "sig_raw": rawlines[i][:90],
                        })
                        i = k + 1
                        continue
        i += 1
    return fns, src


def cycles(fns) -> list[list[str]]:
    """Any call cycle (including self-recursion) among defined functions."""
    defined = {f["name"] for f in fns}
    g = {f["name"]: [c for c in f["calls"] if c in defined] for f in fns}
    found: list[list[str]] = []
    colour: dict[str, int] = {}

    def walk(u, stack):
        colour[u] = 1
        stack.append(u)
        for v in g.get(u, ()):
            if colour.get(v, 0) == 1:
                found.append(stack[stack.index(v):] + [v])
            elif colour.get(v, 0) == 0:
                walk(v, stack)
        stack.pop()
        colour[u] = 2

    for nm in g:
        if colour.get(nm, 0) == 0:
            walk(nm, [])
    return found


_ALLOC = re.compile(r"\b(malloc|calloc|realloc|free|alloca|aligned_alloc|strdup)\s*\(")
_GOTO = re.compile(r"\b(goto|setjmp|longjmp)\b")
_MACRO = re.compile(r"^[ \t]*#[ \t]*define[ \t]+[A-Za-z_][A-Za-z0-9_]*\(.*\\\s*$", re.M)


def main() -> int:
    rows = []
    for arg in sys.argv[1:]:
        p = Path(arg)
        fns, src = scan_functions(p)
        by_len = sorted(fns, key=lambda f: -f["lines"])
        by_as = sorted(fns, key=lambda f: f["asserts"])
        rows.append({
            "file": p.name,
            "functions": len(fns),
            "rule_4_longest": by_len[0]["name"] if fns else None,
            "rule_4_longest_lines": by_len[0]["lines"] if fns else 0,
            "rule_4_over_60": [
                (f["name"], f["lines"]) for f in fns if f["lines"] > 60
            ],
            "rule_5_fewest_asserts": by_as[0]["asserts"] if fns else 0,
            "rule_5_under_2": [
                (f["name"], f["asserts"], f["line"]) for f in fns
                if f["asserts"] < 2
            ],
            "rule_1_goto_tokens": _GOTO.findall(src),
            "rule_1_cycles": cycles(fns),
            "rule_3_alloc": _ALLOC.findall(src),
            "rule_8_multiline_macros": len(_MACRO.findall(src)),
            "top10_by_length": [(f["name"], f["lines"], f["asserts"]) for f in by_len[:10]],
        })
    print(json.dumps(rows, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
