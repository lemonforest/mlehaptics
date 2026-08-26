#!/usr/bin/env python3
"""hook_staged_py_ast.py — the AST half of the pre-commit discipline gate.

WHY THIS EXISTS. The hook's grep cannot tell a real call from prose that NAMES the call, and inside a .py
file that distinction is exactly where the false positives live. Demonstrated on the guard's own source:
`check_srmech_discipline.py` contains ZERO real abs()/hash() calls, but a regex for the call form matches
three lines -- including line 12, which is the docstring of the abs-ban itself. The obvious repair
("a call has a non-empty argument list, so `abs(` not followed by `)` means code") FAILS on that same line:
the docstring literally reads `abs(...)`, whose parens are non-empty. No regex refinement fixes this,
because the distinction is syntactic, not textual.

WHAT THIS DOES. Parses the STAGED content of each staged .py, finds real `ast.Call` nodes for the banned
builtins, and reports only those whose line was ADDED in this commit. So it keeps the hook's diff-awareness
(existing debt stays grandfathered -- the whole-file audit is check_srmech_discipline.py's ratchet) while
being immune to comments, docstrings and any other prose.

Honest limits, stated rather than discovered later:
  * A file that fails to parse is REPORTED, never silently skipped -- a syntax error must not read as clean.
  * `# srmech-allow: <reason>` on the offending line still escapes, same contract as the grep half.
  * Only banned BUILTINS are checked here (abs, hash). Dotted names (hashlib.sha256, np.linalg.eig) stay on
    the grep, where they are unambiguous.
  * hash() on int/float/tuple is NOT salted, so the hash ban over-blocks slightly on purpose (#1454/F1276);
    srmech-allow is the escape.

Usage (called by git-hook-srmech-discipline.sh):  python3 hook_staged_py_ast.py
Exit 0 = clean; 1 = at least one newly-added banned call.
"""
import ast
import os
import re
import subprocess
import sys

BANNED = {
    "abs": "abs() -> srmech.amsc.cascade.magnitude (Class-K pin-slot); sign-fold = "
           "cascade.pin_slot_at_zero (K) + cascade.reorient (C)",
    "hash": "hash() -> srmech.amsc.format.sha256_bytes (Class A). builtin hash() is "
            "PYTHONHASHSEED-salted for str/bytes, so it is NOT reproducible across processes "
            "(#1454/F1276). PYTHONHASHSEED=0 is a workaround, not the fix.",
}
# Dotted calls the grep used to catch in .py. Once .py routes here, THESE MUST BE COVERED HERE TOO --
# omitting them silently reopens the hole for exactly the idioms the grep was written for. (I shipped
# that hole for one commit-cycle while wiring this up: numpy + hashlib.sha256 + np.linalg.eig in a .py
# passed clean. Caught by testing the guard against the thing it guards, which is the only way to know.)
BANNED_DOTTED = {
    "hashlib.sha256": "hashlib.sha256 -> srmech.amsc.format.sha256_bytes (Class A)",
    "np.linalg.eig": "np.linalg.eig -> srmech.amsc.laplacian.jacobi_eigvals / *_eigendecompose",
    "np.linalg.eigh": "np.linalg.eigh -> srmech.amsc.laplacian.hermitian_eigendecompose",
    "np.linalg.svd": "np.linalg.svd -> srmech.amsc.laplacian.* (Class L)",
    "numpy.linalg.eig": "numpy.linalg.eig -> srmech.amsc.laplacian.jacobi_eigvals",
    "numpy.linalg.eigh": "numpy.linalg.eigh -> srmech.amsc.laplacian.hermitian_eigendecompose",
    "numpy.linalg.svd": "numpy.linalg.svd -> srmech.amsc.laplacian.* (Class L)",
}
BANNED_IMPORT = {"numpy": "numpy is GONE (#564) -- every continuous-math op is a cascade of the 14"}
COUNTER_MSG = ("Counter() -> srmech.amsc.text.cooccurrence_edges -> laplacian.dense_laplacian; "
               "Counter AS the storage proxy is NOT ok (s57)")


def dotted(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))
SCOPE = "docs/srmech"
# srmech's OWN package + C tree are authored UPSTREAM and arrive via merges from main.
# Policing them here blocks those merges -- which is precisely how this branch drifted to
# rc256 and stayed there (#1454 s1). The research-discipline guard is for the scripts WE write.
EXCLUDE_PREFIXES = ("docs/srmech/python/", "docs/srmech/c/")
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def sh(args):
    return subprocess.run(args, capture_output=True, text=True).stdout


def staged_py():
    out = sh(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM", "--", SCOPE])
    return [p for p in out.splitlines()
            if p.endswith(".py") and not p.startswith(EXCLUDE_PREFIXES)]


def added_lines(path):
    """Line numbers ADDED to `path` in this commit (unified=0 so hunks are exact)."""
    out = sh(["git", "diff", "--cached", "--unified=0", "--", path])
    hit = set()
    for ln in out.splitlines():
        m = HUNK.match(ln)
        if m:
            start = int(m.group(1))
            count = int(m.group(2) or 1)
            hit.update(range(start, start + count))
    return hit


def main():
    # A merge is not authoring -- see the shell hook's note. Skip so an upstream sync is never blocked.
    if os.path.exists(sh(["git", "rev-parse", "--git-path", "MERGE_HEAD"]).strip()):
        return 0
    problems = []
    for path in staged_py():
        src = sh(["git", "show", ":" + path])
        if not src.strip():
            continue
        lines = src.split("\n")
        try:
            tree = ast.parse(src)
        except SyntaxError as e:
            # A file that will not parse is REPORTED. Silence here would be a false pass, which is
            # the exact bug this session already hit once (a dead subprocess reading as agreement).
            problems.append((path, e.lineno or 0, "does not parse: %s -- cannot be checked" % e.msg))
            continue
        add = added_lines(path)

        def flag(lineno, msg):
            if lineno not in add:
                return
            text = lines[lineno - 1] if lineno - 1 < len(lines) else ""
            if "srmech-allow" in text:
                return
            problems.append((path, lineno, msg))

        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                if isinstance(n.func, ast.Name):
                    if n.func.id in BANNED:
                        flag(n.lineno, BANNED[n.func.id])
                    elif n.func.id == "Counter":
                        flag(n.lineno, COUNTER_MSG)
                else:
                    name = dotted(n.func)
                    if name in BANNED_DOTTED:
                        flag(n.lineno, BANNED_DOTTED[name])
                    elif name.endswith(".Counter"):
                        flag(n.lineno, COUNTER_MSG)
            elif isinstance(n, ast.Import):
                for a in n.names:
                    if a.name.split(".")[0] in BANNED_IMPORT:
                        flag(n.lineno, BANNED_IMPORT[a.name.split(".")[0]])
            elif isinstance(n, ast.ImportFrom):
                base = (n.module or "").split(".")[0]
                if base in BANNED_IMPORT:
                    flag(n.lineno, BANNED_IMPORT[base])

    if problems:
        print("x srmech discipline (AST): a NEWLY ADDED banned builtin call under %s" % SCOPE)
        print("    These are REAL call nodes -- comments and docstrings cannot trigger this check.")
        print("    Genuinely-legit line? -> append  # srmech-allow: <reason>  to it.")
        for path, ln, msg in problems:
            print("    %s:%d  %s" % (path, ln, msg))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
