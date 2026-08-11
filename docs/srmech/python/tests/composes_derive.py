"""The `composes` DERIVATION INSTRUMENT — single-sourced (rc423, `#T1113`).

NOT a test module. Imported by ``test_composes_grain_rc412.py`` (clause 2) and
``test_composes_population_rc423.py`` (the population tiers + the ceiling), and
by the committed census script
``docs/srmech/notes/_composes_population_census_rc423.py``.

The precedent is ``tests/rosetta_roots.py``: a fact two or more gates depend on
lives in ONE module, because the failure mode of a copied instrument is that
the copies drift and each gate then measures a slightly different thing while
both stay green. rc423 needed the same call-graph rc412 already had; copying it
would have created exactly that divergence, so it moved here instead.

WHAT IT COMPUTES
================
An **identity-resolved AST call-graph** over the live registry.
"Identity-resolved" is the load-bearing word: a callee expression is resolved
to a LIVE OBJECT through the defining function's own globals plus its
function-local imports, and matched by ``id()`` against the resolved registry.
Name-matching would have collided the ~40 leaf names the registry spells more
than once.

:func:`derived` descends through UNREGISTERED ``srmech.*`` helpers to the
requested depth, because that is what the ground truth requires:
``cwf_consistency_mod2``'s two declared sub-ops are not called in its own body
at all — they sit inside ``_cwf_compute_pure``, behind a function-local
aliased import. Depth 1 scores 0/2 on that row and depth 3 scores 2/2.

THE TWO DEPTHS MEAN DIFFERENT THINGS, AND rc423 RELIES ON THE DIFFERENCE
=======================================================================
``depth=1`` is the op's OWN BODY — the direct call edges, and nothing else.
``depth=3`` additionally reaches through two hops of unregistered private
helpers.

* A LEAF claim must use **depth 3**: an op whose own body calls nothing
  registered may still reach registered ops through a helper, so only the
  deeper, more generous reading can honestly support "composes nothing".
* A FORCED-ORDER SINGLETON claim must use **depth 1**: the claim is that the
  op is built from exactly one thing, and a depth-3 singleton could be a
  helper's internal that the parent does not itself call — the
  over-attribution ``klein4_compose``'s ROSTER note refuses.

Each tier therefore takes the reading that can FALSIFY it, never the one that
flatters it.

IT IS A LOWER BOUND BY CONSTRUCTION
===================================
Dynamic dispatch (getattr routing, table dispatch, a callable passed as an
argument) is invisible to it, and so is any composition that happens on the C
side of a thin Python shim. That is the right direction for this instrument to
be wrong in: an under-reading makes a TRUE declaration fail loudly and get
investigated; an over-reading would quietly bless a false one.

⚠️ The lower-bound direction flips for LEAF. For a subset check
("declared ⊆ derived") an under-reading is conservative; for an emptiness
check ("derived == ∅") an under-reading is the PERMISSIVE direction, since a
composition the instrument cannot see reads as a leaf. That is why
:func:`derived` is called at depth 3 for the leaf tier — the most generous
reading available — and why the leaf tier is an EQUALITY against ∅ rather
than an assumption. It is stated here rather than left implicit because it is
the one place in this file where "lower bound" is not automatically the safe
direction.

numpy-free; stdlib ``ast`` / ``importlib`` / ``inspect`` / ``sys`` only (none
is a ledgered import — see ``tests/test_selfhosting_import_ban.py``).
"""

from __future__ import annotations

import ast
import importlib
import inspect
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from srmech.introspect.tool_schema import get_tool_schema, warmup_all

warmup_all()

SCHEMA = get_tool_schema()
BY_NAME: Dict[str, Any] = {t.name: t for t in SCHEMA.tools}

#: The rc423 adjudication ledger. One NDJSON record per ADJUDICATED op:
#: ``{"name", "tier", "composes"}`` with ``tier`` in {LEAF, SINGLE, REFUSED}.
#: RESIDUAL rows are deliberately NOT enumerated — see the rc423 gate.
LEDGER_PATH = Path(__file__).resolve().parent / "composes_adjudication_rc423.ndjson"


def load_ledger() -> Dict[str, Dict[str, Any]]:
    """``name -> record`` for the rc423 adjudication ledger.

    Raises rather than returning ``{}`` when the file is missing: an empty
    ledger would make every rc423 clause vacuously true, which is the exact
    failure mode ADR-0012 §6.1 names.
    """
    if not LEDGER_PATH.is_file():
        raise AssertionError(
            f"the rc423 adjudication ledger is missing at {LEDGER_PATH}. "
            "Every population clause would be vacuous without it; regenerate "
            "with docs/srmech/notes/_composes_population_census_rc423.py.")
    out: Dict[str, Dict[str, Any]] = {}
    for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        out[rec["name"]] = rec
    return out


def ledger_names(tier: str) -> Set[str]:
    """The ledger names carrying ``tier``."""
    return {n for n, r in load_ledger().items() if r["tier"] == tier}

#: The default reach. 3 because ``cwf_consistency_mod2``'s ground truth needs
#: it (see the module docstring).
DERIVE_DEPTH = 3


def resolve_op(name: str) -> Optional[Any]:
    """The live callable a registry name points at, or ``None``."""
    module, _, leaf = name.rpartition(".")
    try:
        return getattr(importlib.import_module(module), leaf)
    except Exception:  # noqa: BLE001 - an unimportable op is simply unresolved
        return None


def _resolve_registry() -> Dict[int, str]:
    """``id(callable) -> registry name`` for every row that resolves."""
    out: Dict[int, str] = {}
    for name in BY_NAME:
        obj = resolve_op(name)
        if obj is not None:
            out.setdefault(id(obj), name)
    return out


_ID2NAME = _resolve_registry()

_TREES: Dict[str, Optional[ast.AST]] = {}
_DEFS: Dict[Tuple[str, str], Optional[ast.AST]] = {}


def _module_tree(modname: str) -> Optional[ast.AST]:
    if modname not in _TREES:
        try:
            mod = sys.modules.get(modname) or importlib.import_module(modname)
            _TREES[modname] = ast.parse(inspect.getsource(mod))
        except Exception:  # noqa: BLE001
            _TREES[modname] = None
    return _TREES[modname]


def _def_node(fn: Any) -> Optional[ast.AST]:
    """The ``FunctionDef`` for ``fn``, located by (module, qualname)."""
    modname = getattr(fn, "__module__", None)
    qual = getattr(fn, "__qualname__", None)
    if not modname or not qual:
        return None
    key = (modname, qual)
    if key in _DEFS:
        return _DEFS[key]
    tree = _module_tree(modname)
    found = None
    if tree is not None:
        stack: List[Tuple[str, Any]] = [("", tree)]
        while stack:
            prefix, cur = stack.pop()
            for child in ast.iter_child_nodes(cur):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    q = prefix + child.name
                    if q == qual:
                        found = child
                    stack.append((q + ".<locals>.", child))
                elif isinstance(child, ast.ClassDef):
                    stack.append((prefix + child.name + ".", child))
    _DEFS[key] = found
    return found


def _local_aliases(node: ast.AST) -> Dict[str, Any]:
    """``alias -> live object`` for imports written INSIDE the function body.

    Not optional: the srmech tree imports inside function bodies routinely to
    break cycles, and ``cwf``'s ground truth arrives through exactly such an
    aliased import.
    """
    out: Dict[str, Any] = {}
    for sub in ast.walk(node):
        if isinstance(sub, ast.ImportFrom) and not sub.level and sub.module:
            for alias in sub.names:
                try:
                    mod = importlib.import_module(sub.module)
                    out[alias.asname or alias.name] = getattr(mod, alias.name)
                except Exception:  # noqa: BLE001
                    pass
        elif isinstance(sub, ast.Import):
            for alias in sub.names:
                head = alias.name.split(".")[0]
                try:
                    out[alias.asname or head] = importlib.import_module(head)
                except Exception:  # noqa: BLE001
                    pass
    return out


def _resolve_callee(call: ast.Call, aliases: Dict[str, Any],
                    glb: Dict[str, Any]) -> Optional[Any]:
    """The live object a ``Call`` node's callee expression names, or None."""
    func = call.func
    chain: List[str] = []
    while isinstance(func, ast.Attribute):
        chain.append(func.attr)
        func = func.value
    if not isinstance(func, ast.Name):
        return None                      # a call on a subscript / call result
    chain.append(func.id)
    chain.reverse()
    obj = aliases.get(chain[0], glb.get(chain[0]))
    if obj is None:
        return None
    for part in chain[1:]:
        try:
            obj = getattr(obj, part)
        except Exception:  # noqa: BLE001
            return None
    return obj


def _calls_of(fn: Any) -> Tuple[List[str], List[Any]]:
    """``(registered names called, unregistered srmech helpers called)``."""
    node = _def_node(fn)
    if node is None:
        return [], []
    aliases = _local_aliases(node)
    glb = getattr(fn, "__globals__", {})
    hits: List[str] = []
    helpers: List[Any] = []
    seen: Set[int] = set()
    for sub in ast.walk(node):
        if not isinstance(sub, ast.Call):
            continue
        obj = _resolve_callee(sub, aliases, glb)
        if obj is None or id(obj) in seen:
            continue
        seen.add(id(obj))
        name = _ID2NAME.get(id(obj))
        if name is not None:
            hits.append(name)
        elif (callable(obj) and hasattr(obj, "__code__")
              and str(getattr(obj, "__module__", "") or "").startswith("srmech")):
            helpers.append(obj)
    return hits, helpers


def derived(name: str, depth: int = DERIVE_DEPTH) -> Set[str]:
    """Registered ops reachable from ``name`` within ``depth`` call hops,
    descending only through UNREGISTERED ``srmech.*`` helpers.

    ``depth=1`` is the op's own body and nothing else. See the module
    docstring for why each population tier picks a different depth.
    """
    root = resolve_op(name)
    if root is None:
        return set()
    out: Set[str] = set()
    frontier: List[Tuple[Any, int]] = [(root, 0)]
    seen: Set[int] = {id(root)}
    while frontier:
        fn, d = frontier.pop()
        hits, helpers = _calls_of(fn)
        for hit in hits:
            if hit != name:
                out.add(hit)
        if d + 1 < depth:
            for helper in helpers:
                if id(helper) not in seen:
                    seen.add(id(helper))
                    frontier.append((helper, d + 1))
    return out
