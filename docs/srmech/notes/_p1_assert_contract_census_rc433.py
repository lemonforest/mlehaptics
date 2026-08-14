"""`#T1131` P1 — derive the *real* population of ``AssertionError``-as-contract sites.

READ-ONLY census. Emits NDJSON, one record per located site.

The filed claim was "18 ``pytest.raises(AssertionError)`` sites". A naive text grep
over-counts (docstring prose, ``.pyc`` binaries) and under-counts (a tuple argument
``raises((ValueError, AssertionError))``, a bare ``raises(`` without the ``pytest.``
prefix, ``try/except AssertionError``). This census walks the **AST** instead, so the
population is derived from parsed syntax rather than from line text.

Four shapes are located:

  ``with_raises``   — a ``with`` item whose call resolves to ``pytest.raises`` / ``raises``
                      and whose first argument names ``AssertionError`` (directly, or as
                      a member of a tuple literal).
  ``call_raises``   — the same call NOT in a ``with`` (e.g. assigned, or used as a
                      decorator argument such as ``pytest.mark.xfail(raises=...)``).
  ``except_handler``— ``except AssertionError`` / ``except (..., AssertionError)``.
  ``xfail_raises``  — ``pytest.mark.xfail(..., raises=AssertionError)``.

Run (WSL2, numpy ABSENT):
  PYTHONPATH=/mnt/d/GitHub/mlehaptics/docs/srmech/python \
    python3 docs/srmech/notes/_p1_assert_contract_census_rc433.py
"""

from __future__ import annotations

import ast
import json
import os
import sys

ROOT = "/mnt/d/GitHub/mlehaptics/docs/srmech/python"
OUT = "/mnt/d/GitHub/mlehaptics/docs/srmech/notes/_p1_assert_contract_census_rc433.ndjson"


def _names(node):
    """Every dotted/bare name appearing at the top level of ``node``.

    A tuple literal contributes each element; anything else contributes itself.
    """
    if isinstance(node, ast.Tuple):
        out = []
        for elt in node.elts:
            out.extend(_names(elt))
        return out
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, ast.Attribute):
        return [node.attr]
    return []


def _callee(node):
    """Dotted name of a Call's func, e.g. ``pytest.raises`` -> "pytest.raises"."""
    f = node.func
    parts = []
    while isinstance(f, ast.Attribute):
        parts.append(f.attr)
        f = f.value
    if isinstance(f, ast.Name):
        parts.append(f.id)
    parts.reverse()
    return ".".join(parts)


class Census(ast.NodeVisitor):
    def __init__(self, path, src):
        self.path = path
        self.lines = src.splitlines()
        self.hits = []
        self._with_call_lines = set()
        self._func_stack = []

    # -- context ---------------------------------------------------------
    def visit_FunctionDef(self, node):
        self._func_stack.append(node.name)
        self.generic_visit(node)
        self._func_stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def _enclosing(self):
        return self._func_stack[-1] if self._func_stack else "<module>"

    # -- shapes ----------------------------------------------------------
    def visit_With(self, node):
        for item in node.items:
            ctx = item.context_expr
            if isinstance(ctx, ast.Call) and self._is_raises(ctx):
                if ctx.args and "AssertionError" in _names(ctx.args[0]):
                    self._record("with_raises", ctx, extra=self._match_kw(ctx))
                    self._with_call_lines.add((ctx.lineno, ctx.col_offset))
        self.generic_visit(node)

    def visit_Call(self, node):
        if self._is_raises(node):
            if node.args and "AssertionError" in _names(node.args[0]):
                if (node.lineno, node.col_offset) not in self._with_call_lines:
                    self._record("call_raises", node, extra=self._match_kw(node))
        # pytest.mark.xfail(raises=AssertionError)
        callee = _callee(node)
        if callee.endswith("xfail"):
            for kw in node.keywords:
                if kw.arg == "raises" and "AssertionError" in _names(kw.value):
                    self._record("xfail_raises", node, extra={})
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        if node.type is not None and "AssertionError" in _names(node.type):
            self._record("except_handler", node, extra={})
        self.generic_visit(node)

    # -- helpers ---------------------------------------------------------
    @staticmethod
    def _is_raises(node):
        callee = _callee(node)
        return callee == "pytest.raises" or callee == "raises" or callee.endswith(".raises")

    @staticmethod
    def _match_kw(node):
        for kw in node.keywords:
            if kw.arg == "match" and isinstance(kw.value, ast.Constant):
                return {"match": kw.value.value}
        return {}

    def _record(self, shape, node, extra):
        idx = node.lineno - 1
        text = self.lines[idx].strip() if 0 <= idx < len(self.lines) else ""
        rec = {
            "shape": shape,
            "file": os.path.relpath(self.path, ROOT).replace(os.sep, "/"),
            "line": node.lineno,
            "enclosing": self._enclosing(),
            "text": text,
        }
        rec.update(extra)
        self.hits.append(rec)


def main():
    hits = []
    parse_errors = []
    n_files = 0
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in {"__pycache__", ".git", "build", "dist"}]
        for fn in sorted(filenames):
            if not fn.endswith(".py"):
                continue
            p = os.path.join(dirpath, fn)
            n_files += 1
            try:
                with open(p, "r", encoding="utf-8") as fh:
                    src = fh.read()
                tree = ast.parse(src, filename=p)
            except (SyntaxError, UnicodeDecodeError) as exc:
                parse_errors.append({"file": p, "error": repr(exc)})
                continue
            c = Census(p, src)
            c.visit(tree)
            hits.extend(c.hits)

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({
            "record": "census_meta",
            "root": ROOT,
            "n_py_files_walked": n_files,
            "n_parse_errors": len(parse_errors),
            "parse_errors": parse_errors,
            "python": sys.version.split()[0],
        }, sort_keys=True) + "\n")
        for h in sorted(hits, key=lambda r: (r["file"], r["line"])):
            fh.write(json.dumps(h, sort_keys=True) + "\n")

    by_shape = {}
    for h in hits:
        by_shape[h["shape"]] = by_shape.get(h["shape"], 0) + 1
    print("files walked:", n_files, "parse errors:", len(parse_errors))
    print("shapes:", json.dumps(by_shape, sort_keys=True))
    for h in sorted(hits, key=lambda r: (r["file"], r["line"])):
        print("%-14s %s:%d  %s" % (h["shape"], h["file"], h["line"], h["enclosing"]))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
