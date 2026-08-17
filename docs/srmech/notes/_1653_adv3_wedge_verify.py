#!/usr/bin/env python3
"""ADVERSARIAL round-2 verification of _1653_wedge_optable_rc444.c (gh #1653).

Independent (does NOT reuse any other agent's scanner) mechanical check of:
  * function extraction by brace matching on the top-level
  * line count per function (JPL Rule 4, <= 60)
  * assert() count per function (JPL Rule 5, >= 2)
  * self-recursion (JPL Rule 1 spirit: no recursion)
  * goto / setjmp / longjmp
  * malloc / calloc / realloc / free / alloca / strdup (JPL Rule 3)
  * the pre-commit stop-list tokens, INCLUDING inside comments

Writes nothing but stdout.
"""
from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "_1653_wedge_optable_rc444.c")


def strip_comments_and_strings(src):
    """Return src with comments and string/char literals blanked (newlines kept)."""
    out = []
    i = 0
    n = len(src)
    state = "code"
    while i < n:
        c = src[i]
        nxt = src[i + 1] if i + 1 < n else ""
        if state == "code":
            if c == "/" and nxt == "*":
                state = "block"
                out.append("  ")
                i += 2
                continue
            if c == "/" and nxt == "/":
                state = "line"
                out.append("  ")
                i += 2
                continue
            if c == '"':
                state = "str"
                out.append(" ")
                i += 1
                continue
            if c == "'":
                state = "chr"
                out.append(" ")
                i += 1
                continue
            out.append(c)
            i += 1
        elif state == "block":
            if c == "*" and nxt == "/":
                state = "code"
                out.append("  ")
                i += 2
                continue
            out.append("\n" if c == "\n" else " ")
            i += 1
        elif state == "line":
            if c == "\n":
                state = "code"
                out.append("\n")
                i += 1
                continue
            out.append(" ")
            i += 1
        elif state in ("str", "chr"):
            q = '"' if state == "str" else "'"
            if c == "\\":
                out.append("  ")
                i += 2
                continue
            if c == q:
                state = "code"
                out.append(" ")
                i += 1
                continue
            out.append("\n" if c == "\n" else " ")
            i += 1
    return "".join(out)


def extract_functions(src):
    """Brace-match top-level function definitions. Returns list of dicts."""
    clean = strip_comments_and_strings(src)
    lines = src.split("\n")
    clean_lines = clean.split("\n")
    fns = []
    depth = 0
    i = 0
    n = len(clean)
    # precompute char offset -> line
    line_of = []
    ln = 0
    for ch in clean:
        line_of.append(ln)
        if ch == "\n":
            ln += 1
    line_of.append(ln)

    while i < n:
        ch = clean[i]
        if ch == "{":
            if depth == 0:
                # walk back to find the start of this declaration
                j = i - 1
                while j >= 0 and clean[j] in " \t\n":
                    j -= 1
                # a function definition's header ends with ')' (possibly with
                # trailing qualifiers). struct/enum/union/= initialisers do not.
                is_fn = clean[j] == ")" if j >= 0 else False
                # find start: previous ';' '}' or start of file at depth 0
                k = j
                par = 0
                while k >= 0:
                    if clean[k] == ")":
                        par += 1
                    elif clean[k] == "(":
                        par -= 1
                    elif par == 0 and clean[k] in ";}":
                        break
                    k -= 1
                start = k + 1
                header = clean[start:i]
                if is_fn and "(" in header:
                    hdr_stripped = header.strip()
                    # exclude control statements masquerading as headers
                    first_tok = re.match(r"[A-Za-z_][A-Za-z0-9_]*", hdr_stripped)
                    if first_tok and first_tok.group(0) in (
                        "if", "for", "while", "switch", "do", "else",
                    ):
                        is_fn = False
                if is_fn:
                    # match the closing brace
                    d = 0
                    m = i
                    while m < n:
                        if clean[m] == "{":
                            d += 1
                        elif clean[m] == "}":
                            d -= 1
                            if d == 0:
                                break
                        m += 1
                    body_start_line = line_of[i]
                    body_end_line = line_of[m]
                    hdr_start_line = line_of[start]
                    # name = identifier immediately before the arg-list '('
                    nm = None
                    pj = header.rfind("(")
                    # find the OUTERMOST arg list: scan for the '(' at paren depth 0
                    pd = 0
                    for idx, cc in enumerate(header):
                        if cc == "(":
                            if pd == 0:
                                pj = idx
                            pd += 1
                        elif cc == ")":
                            pd -= 1
                    mm = re.search(
                        r"([A-Za-z_][A-Za-z0-9_]*)\s*$", header[:pj]
                    )
                    if mm:
                        nm = mm.group(1)
                    body_src = "\n".join(lines[hdr_start_line:body_end_line + 1])
                    body_clean = "\n".join(
                        clean_lines[body_start_line:body_end_line + 1]
                    )
                    fns.append({
                        "name": nm or "<anon>",
                        "hdr_line": hdr_start_line + 1,
                        "end_line": body_end_line + 1,
                        "lines_hdr_to_close": body_end_line - hdr_start_line + 1,
                        "lines_body_braces": body_end_line - body_start_line + 1,
                        "asserts": len(
                            re.findall(r"\bassert\s*\(", body_clean)
                        ),
                        "body_clean": body_clean,
                        "src": body_src,
                    })
                    i = m + 1
                    continue
            depth += 1
        elif ch == "}":
            depth -= 1
        i += 1
    return fns


def main():
    src = open(TARGET, "r", encoding="utf-8").read()
    raw_lines = src.count("\n") + (0 if src.endswith("\n") else 1)
    clean = strip_comments_and_strings(src)
    fns = extract_functions(src)

    print("file            :", TARGET)
    print("raw line count  :", raw_lines)
    print("functions found :", len(fns))
    print()

    over60 = []
    under2 = []
    recursive = []
    for f in fns:
        # count self-calls in the body (excluding the header line itself)
        calls = re.findall(r"\b" + re.escape(f["name"]) + r"\s*\(", f["body_clean"])
        if len(calls) > 0:
            recursive.append((f["name"], len(calls)))
        if f["lines_hdr_to_close"] > 60:
            over60.append(f)
        if f["asserts"] < 2:
            under2.append(f)

    print("=== JPL Rule 4 (<= 60 lines, header..closing brace inclusive) ===")
    if over60:
        for f in over60:
            print("  VIOLATION %-42s %4d..%4d  = %d lines"
                  % (f["name"], f["hdr_line"], f["end_line"],
                     f["lines_hdr_to_close"]))
    else:
        print("  0 violations")
    longest = sorted(fns, key=lambda f: -f["lines_hdr_to_close"])[:6]
    print("  longest 6:")
    for f in longest:
        print("    %-44s %4d..%4d  %3d lines  %2d asserts"
              % (f["name"], f["hdr_line"], f["end_line"],
                 f["lines_hdr_to_close"], f["asserts"]))
    print()

    print("=== JPL Rule 5 (>= 2 asserts per function) ===")
    if under2:
        for f in under2:
            print("  VIOLATION %-42s line %4d  asserts=%d"
                  % (f["name"], f["hdr_line"], f["asserts"]))
    else:
        print("  0 violations")
    print("  min asserts across all functions:",
          min(f["asserts"] for f in fns) if fns else "n/a")
    print("  total asserts:", sum(f["asserts"] for f in fns))
    print()

    print("=== recursion (self-call inside own body) ===")
    if recursive:
        for nm, c in recursive:
            print("  SELF-CALL", nm, "x", c)
    else:
        print("  0 self-recursive functions")
    print()

    print("=== JPL Rule 3 / banned constructs (code only, comments blanked) ===")
    checks = {
        "malloc":  r"\bmalloc\s*\(",
        "calloc":  r"\bcalloc\s*\(",
        "realloc": r"\brealloc\s*\(",
        "free":    r"\bfree\s*\(",
        "alloca":  r"\balloca\s*\(",
        "strdup":  r"\bstrdup\s*\(",
        "goto":    r"\bgoto\b",
        "setjmp":  r"\bsetjmp\b",
        "longjmp": r"\blongjmp\b",
    }
    for k, pat in checks.items():
        hits = [i + 1 for i, L in enumerate(clean.split("\n"))
                if re.search(pat, L)]
        print("  %-8s : %d  %s" % (k, len(hits), hits[:6]))
    print()

    print("=== pre-commit stop-list scan (WHOLE FILE incl. comments) ===")
    stop = (r'(\bCounter[[:space:]]*\()|(\babs[[:space:]]*\()|'
            r'(np\.linalg\.(eig|eigh|svd))|(hashlib\.sha256)|'
            r'(\bhash[[:space:]]*\()')
    py_stop = re.compile(
        r"(\bCounter\s*\()|(\babs\s*\()|(np\.linalg\.(eig|eigh|svd))"
        r"|(hashlib\.sha256)|(\bhash\s*\()"
    )
    hits = [(i + 1, L.strip()[:100]) for i, L in enumerate(src.split("\n"))
            if py_stop.search(L)]
    print("  hook pattern:", stop)
    if hits:
        for h in hits:
            print("  HIT line %d: %s" % h)
    else:
        print("  0 hits (clean for the .c pre-commit tripwire)")
    print()

    print("=== math.h / libm symbol use ===")
    for pat in (r"#include\s*<math\.h>", r"\bsqrt\s*\(", r"\bpow\s*\(",
                r"\bfabs\s*\(", r"\bround\s*\(", r"\bfloor\s*\(",
                r"\bceil\s*\("):
        hits = [i + 1 for i, L in enumerate(clean.split("\n"))
                if re.search(pat, L)]
        print("  %-24s : %d %s" % (pat, len(hits), hits[:5]))


if __name__ == "__main__":
    sys.exit(main())
