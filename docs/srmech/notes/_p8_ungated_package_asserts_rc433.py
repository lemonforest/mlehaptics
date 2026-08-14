"""`#T1131` P8 — the UNGATED remainder: package asserts no test pins at all.

P7 measured 207 ``assert`` statements in shipped package code, all of which
evaporate under ``-O``. P1 found only 16 test sites pinning any of them. So the
16 are the VISIBLE part of the class; this file sizes the rest, because "ungated
surfaces trickle; gated ones race to 100%" and a gate scoped to the 16 would
leave the majority untouched and BELIEVED ABSENT.

Each package ``assert`` is classified by AST:

  INPUT_GUARD    the assert is in the first few statements of a PUBLIC callable
                 (no leading underscore) and tests a parameter name directly.
                 This is the `#T1131` shape: it IS the input contract.
  INTERNAL       everything else — a mid-body invariant, a private helper, a
                 post-condition. Under ``-O`` these lose a self-check, which is
                 a defence-in-depth loss rather than a contract loss.

The split is deliberately crude and STATED as crude: it is a scoping estimate,
not a ruling. Every INPUT_GUARD row still needs the per-site execution P2 did
before anything is promoted. The number it produces is "how much is out there",
not "how many defects".
"""

from __future__ import annotations

import ast
import json
import os
import sys

ROOT = "/mnt/d/GitHub/mlehaptics/docs/srmech/python/srmech"
PKG = "/mnt/d/GitHub/mlehaptics/docs/srmech/python"
OUT = "/mnt/d/GitHub/mlehaptics/docs/srmech/notes/_p8_ungated_package_asserts_rc433.ndjson"

#: the guards P1/P2 already account for (file:line of the ASSERT, not the test)
ACCOUNTED = {
    ("math/mat.py", 92), ("math/vec.py", 122), ("math/hdc.py", 3164),
    ("math/hdc.py", 3197), ("math/hdc.py", 3216), ("math/hdc.py", 3286),
    ("math/hdc.py", 3265), ("math/hdc.py", 3058),
    ("math/laplacian.py", 1768), ("physics/qm/bell.py", 279),
    ("physics/qm/bell.py", 281), ("dsl/_catalog.py", 104),
    ("biology/genome.py", 2629), ("biology/genome.py", 2672),
}

#: How many leading statements count as "the guard prologue".
PROLOGUE = 6


def _param_names(fn):
    a = fn.args
    names = [p.arg for p in a.posonlyargs + a.args + a.kwonlyargs]
    if a.vararg:
        names.append(a.vararg.arg)
    if a.kwarg:
        names.append(a.kwarg.arg)
    return set(names)


def _mentions(node, names):
    for n in ast.walk(node):
        if isinstance(n, ast.Name) and n.id in names:
            return True
    return False


def scan(path):
    rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
    with open(path, "r", encoding="utf-8") as fh:
        src = fh.read()
    try:
        tree = ast.parse(src, filename=path)
    except SyntaxError:
        return []
    lines = src.splitlines()
    out = []

    class W(ast.NodeVisitor):
        def __init__(self):
            self.fn = None
            self.cls = None

        def visit_ClassDef(self, node):
            prev, self.cls = self.cls, node.name
            self.generic_visit(node)
            self.cls = prev

        def visit_FunctionDef(self, node):
            prev, self.fn = self.fn, node
            self.generic_visit(node)
            self.fn = prev

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_Assert(self, node):
            fn = self.fn
            if fn is None:
                kind, why = "MODULE_LEVEL", "not inside a function"
            else:
                params = _param_names(fn)
                body = [s for s in fn.body
                        if not (isinstance(s, ast.Expr)
                                and isinstance(s.value, ast.Constant))]
                pos = next((i for i, s in enumerate(body)
                            if node.lineno >= getattr(s, "lineno", 0)
                            and node.lineno <= getattr(s, "end_lineno", 0)), 999)
                public = not fn.name.startswith("_")
                early = pos < PROLOGUE
                touches = _mentions(node.test, params)
                if public and early and touches:
                    kind, why = "INPUT_GUARD", "public callable, prologue, names a param"
                elif touches and public:
                    kind, why = "INPUT_GUARD_LATE", "public + names a param, but mid-body"
                else:
                    kind, why = "INTERNAL", (
                        "private callable" if not public else
                        "does not name a parameter")
            txt = lines[node.lineno - 1].strip() if node.lineno - 1 < len(lines) else ""
            out.append({
                "file": rel, "line": node.lineno,
                "func": fn.name if fn else "<module>",
                "class": self.cls,
                "kind": kind, "why": why,
                "accounted_by_T1131_population": (rel, node.lineno) in ACCOUNTED,
                "text": txt[:160],
            })

    W().visit(tree)
    return out


def main():
    rows = []
    for dp, dn, fns in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in {"__pycache__", "build", "dist"}]
        for fn in sorted(fns):
            if fn.endswith(".py"):
                rows.extend(scan(os.path.join(dp, fn)))

    by = {}
    for r in rows:
        by[r["kind"]] = by.get(r["kind"], 0) + 1
    acct = sum(1 for r in rows if r["accounted_by_T1131_population"])
    ig = [r for r in rows if r["kind"] == "INPUT_GUARD"]
    ig_un = [r for r in ig if not r["accounted_by_T1131_population"]]

    print("total package asserts found by AST: %d" % len(rows))
    print("by kind: %s" % json.dumps(by, sort_keys=True))
    print("accounted for by the `#T1131` population: %d" % acct)
    print("INPUT_GUARD shape: %d, of which UNPINNED by any test: %d"
          % (len(ig), len(ig_un)))
    print("\nthe unpinned INPUT_GUARD rows (the follow-up surface):")
    for r in sorted(ig_un, key=lambda x: (x["file"], x["line"]))[:40]:
        print("  %-40s:%-6d %-34s %s" % (r["file"], r["line"], r["func"], r["text"][:70]))
    if len(ig_un) > 40:
        print("  ... and %d more (full list in the NDJSON)" % (len(ig_un) - 40))

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({"record": "ungated_meta", "n_asserts": len(rows),
                             "by_kind": by, "n_accounted": acct,
                             "n_input_guard": len(ig),
                             "n_input_guard_unpinned": len(ig_un),
                             "prologue_window": PROLOGUE,
                             "python": sys.version.split()[0]},
                            sort_keys=True) + "\n")
        for r in sorted(rows, key=lambda x: (x["file"], x["line"])):
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    print("\nwrote", OUT)


if __name__ == "__main__":
    main()
