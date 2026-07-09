"""Rosetta TRANSITIVE-standalone ratchet (v0.9.0rc12).

The existing ``test_rosetta_completeness.py`` checks that every op is *classified*
and that the two debt-bucket *counts* don't rise — but it NEVER walks the call
graph. So a ``composition_of_c`` op (which claims "standalone-C-ready: I only
compose ops that each reach C") could silently reach a ``bignum_reference`` /
``python_only_debt`` leaf and the ratchet wouldn't notice. That blind spot
is exactly how ``sed_is_navigable`` shipped mislabeled (it reached the
pure-Python ``left_mult_is_invertible``); see the rc12 SedenionRegister fix.

This ratchet closes the blind spot: for every ``composition_of_c`` op it walks
the TRANSITIVE callee graph (through methods + private helpers) and asserts the
op reaches NO non-standalone-ready leaf, except a small DOWN-ONLY allowlist of
explicitly-acknowledged debt (each with the leaf it needs + the rc that closes
it). A NEW composition→non-ready edge that is not allowlisted FAILS — so this
class of mislabel can never recur silently.

Numpy-free (walks srmech.amsc / qm / signal_processing with stdlib importlib /
inspect only).
"""
from __future__ import annotations

import ast
import importlib
import inspect
import json
import pkgutil
import textwrap
from pathlib import Path

import pytest

_FIXTURE = Path(__file__).resolve().parent / "rosetta_classification.ndjson"
# rc177 annex: mirror the ledger-walk extension to bus/dsl (this ratchet only
# iterates composition_of_c rows — all 39 bus/dsl rows are non_compute, so the
# extension is a no-op for its assertion; kept for cross-walk consistency).
# rc183 HOST-GLUE annex: mirror the extension to mcp/cli/llm too (all +24 rows are
# non_compute, so likewise a no-op for the composition_of_c assertion; kept for
# cross-walk consistency).
_ROOTS = (
    "srmech.amsc", "srmech.qm", "srmech.signal_processing",
    "srmech.bus", "srmech.dsl",
    "srmech.mcp", "srmech.cli", "srmech.llm",
)

# Buckets that are NOT standalone-C-ready (a composition_of_c op must not reach
# one transitively).
_NOT_READY = frozenset(
    ("bignum_reference", "python_only_debt", "c_exists_unbound")
)

# ── DOWN-ONLY allowlist of acknowledged composition→non-ready debt ──────────
# Each entry: (composition_of_c op defined_at, the non-ready leaf it reaches).
# This set may only SHRINK. To close an entry: give the leaf a C path (or
# reclassify) and DELETE the line. NEVER add without an explicit user-approved
# reason + the rc that will close it.
_ACKNOWLEDGED = {
    # (rc16 closed the sed_couple_working / sed_uncouple_working →
    # `hypercomplex_couple` edges: the coupler was rewritten to the exact-Q61
    # octonion couple `_couple_q61` that dispatches to `srmech_hypercomplex_couple_q61`
    # and composes only c_dispatched primitives — so it is now `c_dispatched`,
    # not `python_only_debt`, and the edges are no longer non-ready.)
    # (rc13 closed the exact_dft.lift → pi_cascade_digits edge by rerouting the
    # FPU-lift 2π to the c_dispatched `rational.atan`: 2π = 8·atan(1).)
}


def _iter_submodules(root_name):
    root = importlib.import_module(root_name)
    yield root
    if not hasattr(root, "__path__"):
        return
    for info in pkgutil.walk_packages(root.__path__, root_name + "."):
        name = info.name
        tail = name.rsplit(".", 1)[-1]
        if tail.startswith("_") and tail != "__init__":
            continue
        if any(p in name for p in ("._research", ".adapters", ".attested", "._native")):
            continue
        try:
            yield importlib.import_module(name)
        except Exception:  # noqa: BLE001
            continue


def _live_objects():
    """Map canonical ``defined_at`` (``<module>.<qualname>``) -> the object."""
    seen = {}
    for root_name in _ROOTS:
        try:
            importlib.import_module(root_name)
        except Exception:  # noqa: BLE001
            continue
        for mod in _iter_submodules(root_name):
            names = getattr(mod, "__all__", None)
            if names is None:
                names = [n for n in dir(mod) if not n.startswith("_")]
            for n in names:
                obj = getattr(mod, n, None)
                if not callable(obj) or inspect.isclass(obj):
                    continue
                objmod = getattr(obj, "__module__", "") or ""
                if not objmod.startswith("srmech"):
                    continue
                qual = getattr(obj, "__qualname__", n)
                seen.setdefault(f"{objmod}.{qual}", obj)
    return seen


def _load_classification():
    rows = [json.loads(l) for l in _FIXTURE.read_text(encoding="utf-8").splitlines()
            if l.strip()]
    return {r["defined_at"]: r["bucket"] for r in rows}


def _key(obj):
    m = getattr(obj, "__module__", "") or ""
    return f"{m}.{getattr(obj, '__qualname__', '')}" if m.startswith("srmech") else None


def _names_in(code):
    """All global/attribute names referenced by a code object (recursing into
    nested code objects: comprehensions, lambdas, inner defs)."""
    out = set(code.co_names)
    for const in code.co_consts:
        if inspect.iscode(const):
            out |= _names_in(const)
    return out


def _local_imports(fn):
    """Resolve FUNCTION-LOCAL imports (e.g. ``from . import hypercomplex_couple``
    inside a method body) to {local_name: object} via an AST scan — these are
    invisible to ``fn.__globals__`` but are exactly where deferred-import leaves
    (the coupler, pi_cascade_digits) hide."""
    out = {}
    try:
        src = textwrap.dedent(inspect.getsource(fn))
        tree = ast.parse(src)
    except (OSError, TypeError, SyntaxError):
        return out
    pkg = (getattr(fn, "__module__", "") or "").rsplit(".", 1)[0]
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            base = node.module
            if node.level:                      # relative: from . / .. import X
                parts = pkg.split(".")
                base = ".".join(parts[: len(parts) - (node.level - 1)] or parts)
                base = base + ("." + node.module if node.module else "")
            for alias in node.names:
                try:
                    mod = importlib.import_module(base)
                    out[alias.asname or alias.name] = getattr(mod, alias.name)
                except Exception:               # noqa: BLE001
                    continue
    return out


def _direct_callees(fn):
    """The srmech callables ``fn`` references — resolved through ``fn``'s own
    globals AND function-local imports (so deferred imports bind to the real
    object), following BOTH module-level functions AND ``Class().method`` /
    ``Class.method`` attribute calls."""
    g = dict(getattr(fn, "__globals__", {}) or {})
    g.update(_local_imports(fn))                 # local imports shadow/extend globals
    code = getattr(fn, "__code__", None)
    if code is None:
        return []
    names = _names_in(code)
    out = []
    classes = []
    for name in names:
        obj = g.get(name)
        if obj is None:
            continue
        if inspect.isclass(obj) and (getattr(obj, "__module__", "") or "").startswith("srmech"):
            classes.append(obj)
        elif callable(obj) and (getattr(obj, "__module__", "") or "").startswith("srmech"):
            out.append(obj)
    # method calls: an attribute name in co_names that is a method of a class
    # referenced in the same scope (covers the `_rehydrate(...).method()` /
    # `SedenionRegister().method()` adapter pattern).
    for cls in classes:
        for name in names:
            meth = getattr(cls, name, None)
            if callable(meth) and (getattr(meth, "__module__", "") or "").startswith("srmech"):
                out.append(meth)
    return out


def _reached_ledger_ops(start, cls):
    """Set of ledger ``defined_at`` keys transitively reachable from ``start``
    (a function object), recursing through non-ledger glue (methods/helpers)
    but treating a ``c_dispatched`` / ``composition_of_c`` ledger op as a LEAF
    (it is C-backed or itself validated — don't recurse into its fallback)."""
    reached = set()
    seen_code = set()
    queue = [start]
    while queue:
        fn = queue.pop()
        code = getattr(fn, "__code__", None)
        if code is None or id(code) in seen_code:
            continue
        seen_code.add(id(code))
        for callee in _direct_callees(fn):
            k = _key(callee)
            if k is not None and k in cls:
                reached.add(k)
                if cls[k] in ("c_dispatched", "composition_of_c", "non_compute"):
                    continue          # C-backed / validated-elsewhere leaf: stop
                # a not-ready ledger op: record but don't recurse further
                continue
            queue.append(callee)      # glue (method / private helper): recurse
    return reached


def test_no_composition_reaches_nonstandalone_leaf():
    cls = _load_classification()
    objs = _live_objects()
    violations = []
    for da, bucket in cls.items():
        if bucket != "composition_of_c":
            continue
        fn = objs.get(da)
        if fn is None:
            continue
        for leaf in _reached_ledger_ops(fn, cls):
            if cls.get(leaf) in _NOT_READY and (da, leaf) not in _ACKNOWLEDGED:
                violations.append(f"{da}  ->  {leaf}  ({cls[leaf]})")
    assert not violations, (
        "composition_of_c op(s) transitively reach a non-standalone-ready leaf "
        "and are NOT on the down-only acknowledged-debt allowlist — give the "
        "leaf a C path or fix the classification:\n  " + "\n  ".join(sorted(violations))
    )


def test_acknowledged_allowlist_is_still_live():
    """Every acknowledged (op, leaf) pair must still BE a real reachable edge —
    keeps the allowlist honest (a closed edge must be DELETED, not left)."""
    cls = _load_classification()
    objs = _live_objects()
    stale = []
    for da, leaf in _ACKNOWLEDGED:
        fn = objs.get(da)
        if fn is None or leaf not in _reached_ledger_ops(fn, cls):
            stale.append(f"{da} -> {leaf}")
    assert not stale, (
        "acknowledged-debt allowlist has stale entries (edge no longer reachable "
        "— DELETE the line, the debt is closed):\n  " + "\n  ".join(sorted(stale))
    )
