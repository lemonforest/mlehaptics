#!/usr/bin/env python3
"""rc430 `#T1127` S1 — CAN A PARAMETER'S DOMAIN CONSTRAINT BE DERIVED?

The central question of rc430. ``ToolParameter`` publishes ``name`` / ``type``
/ ``required`` / ``summary`` and NO domain constraint. Three open problems
(the bounded semigroup census, `#T1094`'s literal ``"a"`` fed to every str
param, registry-wide executability) reduce to that one missing field.

The rc turns on DERIVED vs DECLARED. An opt-in declared field is an
``__all__``-shaped escape hatch and this codebase has measured that decay
repeatedly. But many constraints ALREADY EXIST IN CODE as guards --
``cyclic_period`` raises on ``gcd != 1``, ``group_algebra_table`` raises on
non-power-of-two, ``_ensure_uint64`` raises on negatives. **Those raises ARE
the constraints.** Whether they lift mechanically is what this measures.

====================================================================
PRE-REGISTERED FALSIFIERS -- declared BEFORE the instrument was run
====================================================================

Every threshold below was fixed before the first measurement and is NOT
tuned afterwards. Nulls are classified REFUTED / BOUNDED / EMPTY /
UNSUPPORTED.

PF1  GUARD-COVERAGE FLOOR.  If < 40% of registry ops have ANY
     argument-validating guard reachable at delegation depth <= 2, guards
     are too sparse to be the derivation source. -> DERIVED REFUTED as a
     registry-wide field.

PF2  PARAMETER-COVERAGE FLOOR.  If < 30% of all REQUIRED parameters across
     the registry are touched by an extractable constraint, the field is
     mostly-empty and is an opt-in surface wearing a derived costume.

PF3  EXTRACTABLE-FRACTION FLOOR.  If < 50% of located argument-guards lift
     into the closed vocabulary below, mechanical extraction is REFUTED.
     THIS IS THE NUMBER THAT DECIDES THE RC.

PF4  WORKED-EXAMPLE GATE.  All THREE of ``srmech.math.primes.cyclic_period``
     / ``srmech.cascade.group_algebra_table`` / ``srmech.cascade.cyclic_mod_add``
     must yield a machine-readable constraint AUTOMATICALLY, with no per-op
     special-casing anywhere in this file. If any fails -> extraction is
     REFUTED on its own worked examples.

PF5  RELATIONAL EXPRESSIVENESS.  The census defect was a modulus bound
     SMALLER than the carrier -- a constraint BETWEEN two parameters. If
     ZERO inter-parameter relational constraints are extractable, the field
     CANNOT fix the semigroup census, which is the rc's headline
     justification. Report BOUNDED (not REFUTED) and say so plainly.

PF6  THE INVERSE CHECK (silent domains).  A guard catches what the author
     thought of. If >= 3 ops have a REAL domain constraint and NO guard at
     any depth, derivation has a measured blind spot and cannot be claimed
     complete. Finding ZERO would be the surprising result.

NEGATIVE CONTROL (pre-registered).  ``EARLY_RETURN`` shapes
(``if <test on param>: return <const>``) are counted SEPARATELY and are NOT
domain constraints -- an early return means the op ACCEPTS that input and is
TOTAL there. If the instrument cannot separate them from raises it is
over-counting, so the split is reported explicitly. An instrument that
cannot return otherwise is not a measurement.

====================================================================
THE CLOSED CONSTRAINT VOCABULARY (v1)
====================================================================

Conjunctive only. A guard whose accept-condition is genuinely DISJUNCTIVE
is reported UNLIFTABLE rather than approximated -- approximating a
disjunction as a conjunction would NARROW the declared domain and reject
valid arguments, which is the same class of defect as the census's
too-small modulus.

UNARY (on one parameter):
    ge / gt / le / lt / ne / eq   param vs integer literal or module const
    nonneg                        param >= 0
    pow2                          _is_pow2(param)
    in_set                        param in (<literals>)
    truthy / nonempty             bare `if not param: raise`
    is_type                       isinstance(param, T)
    uint64                        _ensure_uint64 -- int AND 0 <= p <= 2**64-1
    path_exists                   Path(param).exists() / .is_file()
    divisible_by                  param % k == 0

RELATIONAL (between two parameters):
    ge_param / gt_param / le_param / lt_param / ne_param / eq_param
    coprime                       gcd(p, q) == 1
    len_eq / len_ge / len_lt      len(p) vs q

Usage:
    export PYTHONPATH=/mnt/d/GitHub/mlehaptics/docs/srmech/python
    export SRMECH_EXPECT_PURE=1
    python3 docs/srmech/notes/_s1_guard_extraction_rc430.py > \
        docs/srmech/notes/_s1_guard_extraction_rc430.ndjson
"""

from __future__ import annotations

import ast
import inspect
import json
import sys
from typing import Any, Dict, List, Optional, Tuple

import srmech
from srmech._resolve import resolve_dotted_callable
from srmech.introspect.tool_schema import get_tool_schema, warmup_all

MAX_DEPTH = 2

# Helper names whose CALL is itself a validation. Discovered by reading the
# tree, not invented: `_ensure_uint64` is the uint64 contract in
# srmech/math/cyclic.py:94.
_VALIDATOR_PREFIXES = ("_ensure_", "_require_", "_validate_", "_check_",
                       "_assert_")
_UINT64_MAX = 0xFFFF_FFFF_FFFF_FFFF

_ROWS: List[Dict[str, Any]] = []
#: Set by :func:`lift` when a conjunctive accept-condition lifted only
#: PARTIALLY. Read and cleared per guard so each guard records whether its
#: constraint set is the WHOLE domain or a weaker subset of it.
_LIFT_NOTES: List[str] = []


def emit(rec: Dict[str, Any]) -> None:
    _ROWS.append(rec)
    sys.stdout.write(json.dumps(rec, sort_keys=True) + "\n")


# ---------------------------------------------------------------------------
# source / AST plumbing
# ---------------------------------------------------------------------------

_MODULE_AST: Dict[str, ast.Module] = {}
_MODULE_SRC: Dict[str, str] = {}


def module_src(path: str) -> str:
    if path not in _MODULE_SRC:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                _MODULE_SRC[path] = fh.read()
        except (OSError, UnicodeDecodeError):
            _MODULE_SRC[path] = ""
    return _MODULE_SRC[path]


def module_ast(path: str) -> Optional[ast.Module]:
    if path in _MODULE_AST:
        return _MODULE_AST[path]
    src = module_src(path)
    if not src:
        return None
    try:
        tree = ast.parse(src, filename=path)
    except SyntaxError:
        return None
    _MODULE_AST[path] = tree
    return tree


def const_value(fn: Any, name: str) -> Optional[int]:
    """Resolve a module-level integer constant referenced inside a guard.

    ``group_algebra_table`` bounds ``dim`` by ``ALGEBRA_TABLE_MAX_DIM``, not
    by a literal. Without this the guard lifts to a symbol nobody can check.
    """
    mod = getattr(fn, "__module__", None)
    if not mod or mod not in sys.modules:
        return None
    val = getattr(sys.modules[mod], name, None)
    if isinstance(val, int) and not isinstance(val, bool):
        return val
    return None


def func_def(fn: Any) -> Optional[Tuple[ast.FunctionDef, str]]:
    """The ast.FunctionDef for a live callable, plus its source file."""
    fn = inspect.unwrap(fn)
    try:
        path = inspect.getsourcefile(fn)
        _, lineno = inspect.getsourcelines(fn)
    except (OSError, TypeError):
        return None
    if not path:
        return None
    tree = module_ast(path)
    if tree is None:
        return None
    best = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # getsourcelines points at the first decorator when present.
            starts = [node.lineno] + [d.lineno for d in node.decorator_list]
            if lineno in starts and node.name == getattr(fn, "__name__", ""):
                best = node
                break
    if best is None or isinstance(best, ast.AsyncFunctionDef):
        return None
    return best, path


def param_names(node: ast.FunctionDef) -> List[str]:
    a = node.args
    out = [p.arg for p in list(a.posonlyargs) + list(a.args) + list(a.kwonlyargs)]
    if a.vararg:
        out.append(a.vararg.arg)
    if a.kwarg:
        out.append(a.kwarg.arg)
    return [p for p in out if p not in ("self", "cls")]


# ---------------------------------------------------------------------------
# the lifter: accept-condition AST -> closed constraint vocabulary
# ---------------------------------------------------------------------------

_CMP = {ast.Gt: "gt", ast.GtE: "ge", ast.Lt: "lt", ast.LtE: "le",
        ast.Eq: "eq", ast.NotEq: "ne"}
_NEG = {"gt": "le", "ge": "lt", "lt": "ge", "le": "gt",
        "eq": "ne", "ne": "eq"}
_FLIP = {"gt": "lt", "lt": "gt", "ge": "le", "le": "ge",
         "eq": "eq", "ne": "ne"}


def _resolve_ref(node: ast.AST, refs: Dict[str, Tuple[str, str]]
                 ) -> Optional[Tuple[str, str]]:
    """(canonical param, transform) for a Name that IS a parameter or is a
    single-assignment local DERIVED from one.

    WHY THIS EXISTS. Measured at rc430: `exact_dft` writes `N = len(signal)`
    and then guards `if N < 2`. A purely syntactic matcher sees a guard on a
    local and records NO constraint on `signal` -- the op reads as unguarded
    while its real domain bound sits two lines below. The same shape hides
    `_as_elem`'s power-of-two check and `hamming._check_n`'s range. Without
    one hop of taint the census measures the coding style, not the domain.

    Restricted to SINGLE-assignment locals: if a name is rebound anywhere in
    the body the alias is dropped, because a guard on its later value says
    nothing about the parameter.
    """
    if isinstance(node, ast.Name):
        return refs.get(node.id)
    return None


def _is_param(node: ast.AST, refs: Dict[str, Tuple[str, str]]) -> Optional[str]:
    got = _resolve_ref(node, refs)
    return got[0] if got else None


def build_refs(node: ast.FunctionDef, params: List[str]
               ) -> Dict[str, Tuple[str, str]]:
    refs: Dict[str, Tuple[str, str]] = {p: (p, "id") for p in params}
    assigned: Dict[str, int] = {}
    for stmt in ast.walk(node):
        if isinstance(stmt, ast.Assign):
            for t in stmt.targets:
                if isinstance(t, ast.Name):
                    assigned[t.id] = assigned.get(t.id, 0) + 1
        elif isinstance(stmt, (ast.AugAssign, ast.AnnAssign)) \
                and isinstance(stmt.target, ast.Name):
            assigned[stmt.target.id] = assigned.get(stmt.target.id, 0) + 2
        elif isinstance(stmt, ast.For) and isinstance(stmt.target, ast.Name):
            assigned[stmt.target.id] = assigned.get(stmt.target.id, 0) + 2
    for stmt in ast.walk(node):
        if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
            continue
        tgt = stmt.targets[0]
        if not isinstance(tgt, ast.Name) or assigned.get(tgt.id, 0) != 1:
            continue
        if tgt.id in params:
            continue
        rhs = stmt.value
        if isinstance(rhs, ast.Name) and rhs.id in params:
            refs[tgt.id] = (rhs.id, "id")
        elif isinstance(rhs, ast.Call) and isinstance(rhs.func, ast.Name) \
                and rhs.func.id == "len" and len(rhs.args) == 1 \
                and isinstance(rhs.args[0], ast.Name) \
                and rhs.args[0].id in params:
            refs[tgt.id] = (rhs.args[0].id, "len")
    return refs


def _int_of(node: ast.AST, fn: Any) -> Optional[int]:
    if isinstance(node, ast.Constant) and isinstance(node.value, int) \
            and not isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.Name):
        return const_value(fn, node.id)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _int_of(node.operand, fn)
        # Class-K pin-slot: the sign lives in the AST node, not in a call to
        # abs(). Re-applied (Class C) by negating the magnitude directly.
        if inner is not None:
            return 0 - inner
    if isinstance(node, ast.Attribute):
        return None
    return None


def _lift_call(node: ast.Call, params: List[str], fn: Any, positive: bool
               ) -> Optional[List[Dict[str, Any]]]:
    """`if not _is_pow2(dim)` / `if not p.exists()` style predicates."""
    name = None
    if isinstance(node.func, ast.Name):
        name = node.func.id
    elif isinstance(node.func, ast.Attribute):
        name = node.func.attr
    if name is None:
        return None
    if name in ("_is_pow2", "is_pow2", "_is_power_of_two") and node.args:
        got = _resolve_ref(node.args[0], params)
        if got and positive:
            pre = "len_" if got[1] == "len" else ""
            return [{"kind": pre + "pow2", "param": got[0]}]
        if positive and isinstance(node.args[0], ast.Call) \
                and isinstance(node.args[0].func, ast.Name) \
                and node.args[0].func.id == "len" and node.args[0].args:
            p = _is_param(node.args[0].args[0], params)
            if p:
                return [{"kind": "len_pow2", "param": p}]
        return None
    if name in ("exists", "is_file", "is_dir"):
        # p.exists() where p is (or wraps) a param
        tgt = node.func.value if isinstance(node.func, ast.Attribute) else None
        for sub in ast.walk(tgt) if tgt is not None else []:
            p = _is_param(sub, params)
            if p and positive:
                return [{"kind": "path_exists", "param": p, "probe": name}]
        return None
    if name == "isinstance" and len(node.args) == 2:
        p = _is_param(node.args[0], params)
        tname = None
        if isinstance(node.args[1], ast.Name):
            tname = node.args[1].id
        if p and tname and positive:
            return [{"kind": "is_type", "param": p, "type": tname}]
        return None
    return None


def lift(node: ast.AST, params: List[str], fn: Any, positive: bool = True
         ) -> Optional[List[Dict[str, Any]]]:
    """Lift an ACCEPT-condition into constraints. None => UNLIFTABLE.

    `positive=False` means "this subtree must be FALSE" -- which is how a
    `if <bad>: raise` guard is read. De Morgan is applied honestly: a
    disjunctive accept-condition returns None rather than being narrowed.
    """
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return lift(node.operand, params, fn, not positive)

    if isinstance(node, ast.BoolOp):
        is_and = isinstance(node.op, ast.And)
        # accept = AND  -> conjunction, liftable
        # accept = OR   -> disjunction, NOT in a conjunctive vocabulary
        conjunctive = is_and if positive else not is_and
        if not conjunctive:
            return None
        # PARTIAL LIFT. A conjunctive accept-condition A ∧ B where only A
        # lifts yields A alone. That is SOUND-but-INCOMPLETE: the declared
        # domain is WIDER than the true one, so it never rejects a valid
        # argument, but a consumer synthesizing against it can still be
        # refused. All-or-nothing was throwing away real constraints --
        # `log1p_series_truncate`'s `numerator > denominator` was discarded
        # because the sibling conjunct compared against `-denominator`.
        # The incompleteness is RECORDED, not hidden: a constraint set that
        # presents as complete when it is not is the exact failure this rc
        # is trying to avoid.
        out: List[Dict[str, Any]] = []
        dropped = 0
        for v in node.values:
            got = lift(v, params, fn, positive)
            if got is None:
                dropped += 1
                continue
            out.extend(got)
        if not out:
            return None
        if dropped:
            _LIFT_NOTES.append("partial:%d" % dropped)
        return out

    if isinstance(node, ast.Compare) and len(node.ops) == 1:
        op = _CMP.get(type(node.ops[0]))
        left, right = node.left, node.comparators[0]
        if op is None:
            # `in` / `not in`
            if isinstance(node.ops[0], (ast.In, ast.NotIn)):
                p = _is_param(left, params)
                want_in = isinstance(node.ops[0], ast.In) == positive
                if p and want_in and isinstance(right, (ast.Tuple,
                                                        ast.List, ast.Set)):
                    vals = [e.value for e in right.elts
                            if isinstance(e, ast.Constant)]
                    if vals and len(vals) == len(right.elts):
                        return [{"kind": "in_set", "param": p,
                                 "values": sorted(vals, key=repr)}]
            return None
        if not positive:
            op = _NEG[op]

        # gcd(a, n) == 1  -> coprime  (the relational one that matters)
        if op == "eq" and isinstance(left, ast.Call):
            fname = (left.func.id if isinstance(left.func, ast.Name)
                     else getattr(left.func, "attr", None))
            k = _int_of(right, fn)
            if fname in ("gcd", "_gcd") and k == 1 and len(left.args) == 2:
                ps = []
                for a in left.args:
                    hit = None
                    for sub in ast.walk(a):
                        q = _is_param(sub, params)
                        if q:
                            hit = q
                            break
                    ps.append(hit)
                if ps[0] and ps[1] and ps[0] != ps[1]:
                    return [{"kind": "coprime", "param": ps[0],
                             "other": ps[1]}]
            # FALL THROUGH. This branch used to `return None` whenever the
            # left side was any Call under an `eq` accept-condition, which
            # swallowed every `len(a) != len(b)` shape-agreement guard --
            # the commonest inter-parameter constraint in the tree. Only a
            # matched gcd shape may consume the node.

        # len(x) <op> n   -> relational or unary length bound
        def _len_of(n: ast.AST) -> Optional[str]:
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                    and n.func.id == "len" and n.args:
                return _is_param(n.args[0], params)
            return None

        lp = _len_of(left)
        if lp:
            # len(a) vs len(b): the SHAPE-AGREEMENT relation. This is the
            # single commonest inter-parameter guard in the tree (cd_mult,
            # cd_add, klein4_bind, inner_product_eta, graph_to_kernel) and
            # the first lifter missed every one of them, because it only
            # looked for a bare param on the right.
            rp = _len_of(right)
            if rp and rp != lp:
                return [{"kind": "len_" + op + "_len", "param": lp,
                         "other": rp}]
            got = _resolve_ref(right, params)
            if got and got[0] != lp:
                kind = ("len_" + op + "_len" if got[1] == "len"
                        else "len_" + op + "_param")
                return [{"kind": kind, "param": lp, "other": got[0]}]
            k = _int_of(right, fn)
            if k is not None:
                return [{"kind": "len_" + op, "param": lp, "value": k}]
            return None
        rp = _len_of(right)
        if rp:
            got = _resolve_ref(left, params)
            if got and got[0] != rp:
                kind = ("len_" + _FLIP[op] + "_len" if got[1] == "len"
                        else "len_" + _FLIP[op] + "_param")
                return [{"kind": kind, "param": rp, "other": got[0]}]
            k = _int_of(left, fn)
            if k is not None:
                return [{"kind": "len_" + _FLIP[op], "param": rp, "value": k}]
            return None

        lref = _resolve_ref(left, params)
        rref = _resolve_ref(right, params)
        if lref is None:
            # try the flipped orientation: 0 <= x
            if rref is not None:
                k = _int_of(left, fn)
                if k is not None:
                    pre = "len_" if rref[1] == "len" else ""
                    return [{"kind": pre + _FLIP[op], "param": rref[0],
                             "value": k}]
            return None
        p, xform = lref
        pre = "len_" if xform == "len" else ""
        if rref is not None:
            if rref[0] == p:
                return None
            return [{"kind": pre + op + "_param", "param": p,
                     "other": rref[0], "other_via": rref[1]}]
        k = _int_of(right, fn)
        if k is not None:
            if op == "ge" and k == 0 and not pre:
                return [{"kind": "nonneg", "param": p}]
            return [{"kind": pre + op, "param": p, "value": k}]
        return None

    if isinstance(node, ast.Call):
        return _lift_call(node, params, fn, positive)

    # bare truthiness: `if not x: raise` -> x must be truthy
    p = _is_param(node, params)
    if p is not None and positive:
        return [{"kind": "truthy", "param": p}]
    return None


# ---------------------------------------------------------------------------
# guard discovery inside one function body
# ---------------------------------------------------------------------------

def _raises(body: List[ast.stmt]) -> bool:
    return any(isinstance(s, ast.Raise) for s in body)


def _returns_const(body: List[ast.stmt]) -> bool:
    return any(isinstance(s, ast.Return) for s in body)


def _touches_param(node: ast.AST, params: List[str]) -> bool:
    return any(_is_param(s, params) for s in ast.walk(node))


def scan_guards(node: ast.FunctionDef, fn: Any, path: str
                ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Return (arg_guards, early_returns) for one function body.

    Nested FunctionDefs are NOT descended into: their params are a different
    namespace and their guards are not this op's domain.
    """
    plist = param_names(node)
    guards: List[Dict[str, Any]] = []
    earlies: List[Dict[str, Any]] = []
    if not plist:
        return guards, earlies
    # One hop of taint: parameters PLUS single-assignment locals derived
    # from them. See _resolve_ref for why this is not optional.
    params = build_refs(node, plist)

    nested = {id(n) for d in node.body for n in ast.walk(d)
              if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                                ast.Lambda))}
    skip: set = set()
    for d in ast.walk(node):
        if id(d) in nested and d is not node:
            for sub in ast.walk(d):
                skip.add(id(sub))

    for stmt in ast.walk(node):
        if id(stmt) in skip:
            continue
        if isinstance(stmt, ast.If) and _touches_param(stmt.test, params):
            src = ast.get_source_segment(module_src(path), stmt.test) or ""
            if _raises(stmt.body):
                del _LIFT_NOTES[:]
                lifted = lift(stmt.test, params, fn, positive=False)
                guards.append({
                    "shape": "RAISE_IF", "line": stmt.lineno,
                    "test": src.strip()[:200],
                    "constraints": lifted,
                    "liftable": lifted is not None,
                    "partial": bool(_LIFT_NOTES),
                })
            elif _returns_const(stmt.body):
                earlies.append({"shape": "EARLY_RETURN", "line": stmt.lineno,
                                "test": src.strip()[:200]})
        elif isinstance(stmt, ast.Assert) and _touches_param(stmt.test,
                                                             params):
            src = ast.get_source_segment(module_src(path), stmt.test) or ""
            del _LIFT_NOTES[:]
            lifted = lift(stmt.test, params, fn, positive=True)
            guards.append({"shape": "ASSERT", "line": stmt.lineno,
                           "test": src.strip()[:200],
                           "constraints": lifted,
                           "liftable": lifted is not None,
                           "partial": bool(_LIFT_NOTES)})
        elif isinstance(stmt, ast.Call):
            fname = (stmt.func.id if isinstance(stmt.func, ast.Name)
                     else getattr(stmt.func, "attr", None))
            if not fname or not fname.startswith(_VALIDATOR_PREFIXES):
                continue
            hit = [p for a in stmt.args for p in [_is_param(a, params)] if p]
            if not hit:
                continue
            if fname == "_ensure_uint64":
                cons = [{"kind": "uint64", "param": hit[-1]},
                        {"kind": "is_type", "param": hit[-1], "type": "int"},
                        {"kind": "nonneg", "param": hit[-1]},
                        {"kind": "le", "param": hit[-1],
                         "value": _UINT64_MAX}]
                guards.append({"shape": "VALIDATOR_CALL", "line": stmt.lineno,
                               "test": fname, "constraints": cons,
                               "liftable": True, "callee": fname})
            else:
                guards.append({"shape": "VALIDATOR_CALL", "line": stmt.lineno,
                               "test": fname, "constraints": None,
                               "liftable": False, "callee": fname})
    home = getattr(fn, "__module__", "?")
    for g in guards:
        # A guard is a SITE, not an occurrence. `_ensure_uint64` called three
        # times is ONE guard reached three ways -- counts are not sets.
        g["site"] = "%s:%d:%s" % (home, g["line"], g["shape"])
    return guards, earlies


# ---------------------------------------------------------------------------
# delegation: follow in-package callees, remapping their params to ours
# ---------------------------------------------------------------------------

def callee_of(call: ast.Call, fn: Any) -> Optional[Any]:
    mod = getattr(fn, "__module__", None)
    if not mod or mod not in sys.modules:
        return None
    ns = sys.modules[mod]
    tgt: Any = None
    if isinstance(call.func, ast.Name):
        tgt = getattr(ns, call.func.id, None)
    elif isinstance(call.func, ast.Attribute) \
            and isinstance(call.func.value, ast.Name):
        base = getattr(ns, call.func.value.id, None)
        if base is not None:
            tgt = getattr(base, call.func.attr, None)
    if not callable(tgt) or inspect.isclass(tgt):
        return None
    real = inspect.unwrap(tgt)
    if not inspect.isfunction(real):
        return None
    if not getattr(real, "__module__", "").startswith("srmech"):
        return None
    return real


def arg_map(call: ast.Call, callee_params: List[str],
            our_params: List[str]) -> Dict[str, str]:
    """callee-param-name -> our-param-name, for bare Name pass-through."""
    out: Dict[str, str] = {}
    for i, a in enumerate(call.args):
        p = _is_param(a, our_params)
        if p and i < len(callee_params):
            out[callee_params[i]] = p
    for kw in call.keywords:
        if kw.arg:
            p = _is_param(kw.value, our_params)
            if p:
                out[kw.arg] = p
    return out


def collect(fn: Any, depth: int, seen: set
            ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    key = (getattr(fn, "__module__", ""), getattr(fn, "__qualname__", ""))
    if key in seen or depth > MAX_DEPTH:
        return [], []
    seen = seen | {key}
    got = func_def(fn)
    if got is None:
        return [], []
    node, path = got
    guards, earlies = scan_guards(node, fn, path)
    for g in guards:
        g["depth"] = depth
    for e in earlies:
        e["depth"] = depth
    if depth >= MAX_DEPTH:
        return guards, earlies

    ours = build_refs(node, param_names(node))
    for sub in ast.walk(node):
        if not isinstance(sub, ast.Call):
            continue
        callee = callee_of(sub, fn)
        if callee is None:
            continue
        cgot = func_def(callee)
        if cgot is None:
            continue
        cparams = param_names(cgot[0])
        mapping = arg_map(sub, cparams, ours)
        if not mapping:
            continue
        dg, de = collect(callee, depth + 1, seen)
        for g in dg:
            cons = g.get("constraints")
            if cons is None:
                remapped = None
            else:
                remapped = []
                for c in cons:
                    c2 = dict(c)
                    if c2.get("param") not in mapping:
                        continue
                    c2["param"] = mapping[c2["param"]]
                    if "other" in c2:
                        if c2["other"] not in mapping:
                            continue
                        c2["other"] = mapping[c2["other"]]
                    remapped.append(c2)
                if not remapped:
                    continue
            guards.append({**g, "constraints": remapped,
                           "liftable": remapped is not None,
                           "via": f"{callee.__module__}.{callee.__qualname__}"})
        earlies.extend(de)
    return guards, earlies


# ---------------------------------------------------------------------------
# WHY a guard did not lift -- the decomposition that bounds a v2 vocabulary
# ---------------------------------------------------------------------------
#
# The extractable FRACTION alone does not decide the rc, because a miss can be
# a vocabulary gap I could close in an afternoon or a fact that is not in the
# source at all. Only the split tells you which.
#
#   FIXABLE    -- a v2 vocabulary reaches it (negated types, not-in-set, ...)
#   UNDERIVABLE-- the constraint's EXTENT is not in the source (runtime
#                 collections, bounds computed from other locals)
#   NOT-A-MISS -- a pointer to a guard already counted elsewhere

_FIXABLE = {"NEGATED_TYPE", "NOT_IN_SET", "LOCAL_CONST", "ATTRIBUTE_PROBE",
            "VALIDATOR_POINTER_OPAQUE"}
_UNDERIVABLE = {"RUNTIME_EXTENT", "LOCAL_BOUND", "DISJUNCTIVE",
                "CALL_PREDICATE", "OTHER"}


def why_unliftable(g: Dict[str, Any], absorbed: set) -> str:
    if g["shape"] == "VALIDATOR_CALL":
        return ("VALIDATOR_POINTER_ABSORBED" if g.get("callee") in absorbed
                else "VALIDATOR_POINTER_OPAQUE")
    src = g.get("test", "")
    try:
        tree = ast.parse(src, mode="eval").body
    except SyntaxError:
        return "OTHER"

    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    has_isinstance = any(
        isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
        and n.func.id in ("isinstance", "type") for n in ast.walk(tree))
    if has_isinstance or "type" in names:
        return "NEGATED_TYPE"
    for n in ast.walk(tree):
        if isinstance(n, ast.Compare) and n.ops and isinstance(
                n.ops[0], (ast.In, ast.NotIn)):
            rhs = n.comparators[0]
            if isinstance(rhs, (ast.Tuple, ast.List, ast.Set)):
                return "NOT_IN_SET"
            return "RUNTIME_EXTENT"
    if any(isinstance(n, ast.Attribute) for n in ast.walk(tree)):
        return "ATTRIBUTE_PROBE"
    if any(isinstance(n, ast.Call) for n in ast.walk(tree)):
        return "CALL_PREDICATE"
    if isinstance(tree, ast.BoolOp):
        return "DISJUNCTIVE"
    if isinstance(tree, ast.Compare):
        # a comparison the lifter refused: the other side was a NAME that is
        # neither a param nor a resolvable module constant -> a local.
        return "LOCAL_BOUND"
    return "OTHER"


# ---------------------------------------------------------------------------
# PF6 -- the inverse check. Is the guard the WHOLE constraint?
# ---------------------------------------------------------------------------
#
# A guard catches what the author thought of. This probes ops that have NO
# guard at any depth with arguments their DECLARED TYPE permits, and asks
# whether the op is genuinely total there. Three outcomes matter:
#
#   DEEP_RAISE  -- blew up in a frame BELOW the op: a real domain constraint
#                  exists and nothing states it. A derived field MISSES it.
#   HANG        -- did not terminate inside the alarm: an unguarded domain
#                  whose violation is not even an exception.
#   ACCEPTED    -- returned. Either genuinely total, or a SILENT WRONG ANSWER
#                  (which this probe cannot distinguish and does not claim to).
#
# Scope is deliberately narrow and side-effect-free: pure math/cascade
# modules, all-int required params, nothing whose name touches the
# filesystem or a network.

_UNSAFE = ("write", "save", "delete", "remove", "publish", "fetch",
           "download", "register", "install", "mkdir", "open", "load",
           "path", "file", "dir", "server", "client", "bus",
           "exec", "spawn")
_SAFE_MODULE_PREFIXES = ("srmech.math.", "srmech.cascade.",
                         "srmech.physics.qm.", "srmech.signal_processing.",
                         "srmech.apokatastasis.", "srmech.music.",
                         "srmech.trigonometry", "srmech.asymptotic_calculus")

# Type-directed argument synthesis. Round 0 is the EDGE round (zero / empty
# / negative): every value is type-valid and is exactly what `#T1094`'s
# literal `"a"` is a stand-in for. Round 1 is a small plausible value.
# Carrier types (HV / Mat / Vec / domain objects) are deliberately NOT
# synthesized -- they are reported as UNPROBED rather than guessed at.
_SYNTH: Dict[str, List[Any]] = {
    "int": [0, 2], "integer": [0, 2], "float": [0.0, 2.0],
    "bool": [False, True], "complex": [0j, (1 + 0j)],
    "str": ["", "a"], "bytes": [b"", b"ab"],
    "list": [[], [1, 2]], "sequence": [[], [1, 2]],
    "Sequence[int]": [[], [1, 2]], "list[int]": [[], [1, 2]],
    "list[float]": [[], [1.0, 2.0]], "list[complex]": [[], [1 + 0j]],
    "list[list[float]]": [[], [[1.0, 0.0], [0.0, 1.0]]],
    "list[list[int]]": [[], [[1, 0], [0, 1]]],
    "tuple[int, int]": [(0, 0), (1, 2)],
    "list[tuple[int, int]]": [[], [(0, 1)]],
    "dict": [{}, {"a": 1}],
}


def probe_unguarded(entry: Any, fn: Any) -> Optional[Dict[str, Any]]:
    """Call an op that has NO guard with arguments its DECLARED TYPE permits.

    Returns None when the op is out of scope (unsafe or unsynthesizable) so
    the caller can count the UNPROBED remainder -- an instrument that silently
    drops its population cannot report a null.
    """
    import signal

    mod = getattr(fn, "__module__", "")
    if not mod.startswith(_SAFE_MODULE_PREFIXES):
        return {"op": entry.name, "skipped": "module_out_of_scope"}
    low = entry.name.lower()
    if any(tok in low for tok in _UNSAFE):
        return {"op": entry.name, "skipped": "unsafe_name"}
    req = [p for p in entry.parameters if p.required]
    if not req or len(req) > 4:
        return {"op": entry.name, "skipped": "no_or_too_many_params"}
    if not all(p.type in _SYNTH for p in req):
        return {"op": entry.name, "skipped": "unsynthesizable_type",
                "types": [p.type for p in req]}

    out: List[Dict[str, Any]] = []
    for rnd in (0, 1):
        args = [_SYNTH[p.type][min(rnd, len(_SYNTH[p.type]) - 1)]
                for p in req]

        def _alarm(signum, frame):
            raise TimeoutError("probe alarm")

        old = signal.signal(signal.SIGALRM, _alarm)
        signal.alarm(2)
        try:
            fn(*args)
            out.append({"args": [repr(a)[:24] for a in args],
                        "outcome": "ACCEPTED"})
        except TimeoutError:
            out.append({"args": [repr(a)[:24] for a in args],
                        "outcome": "HANG"})
        except BaseException as exc:  # noqa: BLE001 - classification is the point
            tb = exc.__traceback__
            frames = []
            while tb is not None:
                frames.append((tb.tb_frame.f_globals.get("__name__", "?"),
                               tb.tb_frame.f_code.co_name, tb.tb_lineno))
                tb = tb.tb_next
            # frames[0] is this probe; frames[1] is the op itself. Anything
            # past that means the op passed a bad argument DOWNWARD -- it
            # never checked, so no guard states the constraint.
            deep = len(frames) > 2
            out.append({
                "args": [repr(a)[:24] for a in args],
                "outcome": "DEEP_RAISE" if deep else "SHALLOW_RAISE",
                "exc": type(exc).__name__,
                "msg": str(exc)[:140],
                "frames": len(frames),
                "raised_in": ("%s.%s:%d" % frames[-1]) if frames else "?"})
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old)
    return {"op": entry.name, "module": mod,
            "params": [(p.name, p.type) for p in req], "probes": out}


# ---------------------------------------------------------------------------
# IS THE DERIVED CONSTRAINT AN ORACLE, OR ONLY A DECLARATION?
# ---------------------------------------------------------------------------
#
# The brief's central warning: a field nothing checks is a DECLARATION, and a
# declaration can be wrong in the same direction as the thing it describes.
# Extracting a constraint proves only that a guard was PARSED, not that the
# constraint is TRUE of the op. So: build an argument that VIOLATES one
# derived bound while satisfying every other derived bound on that op, and
# require the op to reject it.
#
#   CONFIRMED -- the op raised. The derived bound predicted real behaviour.
#   VIOLATED  -- the op ACCEPTED an argument the derived bound forbids. The
#                constraint is WRONG and would have shipped as a false claim.
#
# Only ops whose required params are all int are testable this way, which is
# a real bound on the check and is reported rather than smoothed over.

def _satisfying_int(cons: List[Dict[str, Any]], param: str) -> int:
    """A value satisfying every derived unary int bound on `param`."""
    lo, hi = 1, None
    for c in cons:
        if c.get("param") != param or "value" not in c:
            continue
        v = c["value"]
        k = c["kind"]
        if k == "ge":
            lo = max(lo, v)
        elif k == "gt":
            lo = max(lo, v + 1)
        elif k == "nonneg":
            lo = max(lo, 0)
        elif k == "le":
            hi = v if hi is None else min(hi, v)
        elif k == "lt":
            hi = v - 1 if hi is None else min(hi, v - 1)
    val = max(lo, 2)
    if hi is not None and val > hi:
        val = hi
    return val


def validate_constraints(entry: Any, fn: Any, cons: List[Dict[str, Any]]
                         ) -> List[Dict[str, Any]]:
    import signal

    mod = getattr(fn, "__module__", "")
    if not mod.startswith(_SAFE_MODULE_PREFIXES):
        return []
    if any(tok in entry.name.lower() for tok in _UNSAFE):
        return []
    req = [p for p in entry.parameters if p.required]
    if not req or len(req) > 3 or not all(p.type == "int" for p in req):
        return []
    names = {p.name for p in req}
    base = {p.name: _satisfying_int(cons, p.name) for p in req}

    out: List[Dict[str, Any]] = []
    for c in cons:
        p = c.get("param")
        if p not in names or "value" not in c:
            continue
        v, k = c["value"], c["kind"]
        # The witness that should be REJECTED, one step outside the bound.
        if k in ("ge", "nonneg"):
            bad = (v if k == "ge" else 0) - 1
        elif k == "gt":
            bad = v
        elif k == "le":
            bad = v + 1
        elif k == "lt":
            bad = v
        else:
            continue
        if bad > 1 << 32 or bad < -(1 << 32):
            continue  # a uint64-ceiling witness is not worth constructing
        args = dict(base)
        args[p] = bad

        def _alarm(signum, frame):
            raise TimeoutError("validate alarm")

        old = signal.signal(signal.SIGALRM, _alarm)
        signal.alarm(2)
        try:
            fn(**args)
            verdict = "VIOLATED"
            detail = "op ACCEPTED an argument the derived bound forbids"
        except TimeoutError:
            verdict = "TIMEOUT"
            detail = ""
        except (ValueError, TypeError, OverflowError, ZeroDivisionError,
                IndexError, KeyError, ArithmeticError) as exc:
            verdict = "CONFIRMED"
            detail = type(exc).__name__
        except BaseException as exc:  # noqa: BLE001
            verdict = "CONFIRMED"
            detail = type(exc).__name__
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old)
        out.append({"op": entry.name, "constraint": c, "witness": args,
                    "verdict": verdict, "detail": detail})
    return out


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    warmup_all()
    tools = get_tool_schema().tools
    emit({"row": "env", "srmech_file": srmech.__file__,
          "version": srmech.__version__, "registry": len(tools),
          "max_depth": MAX_DEPTH})
    # PROVENANCE OF THE NUMBER ITSELF. PF3 was pre-registered at >= 0.50 and
    # FIRED on the first instrument. It passes on the fifth. Each revision was
    # forced by an INDEPENDENT observation -- never by wanting the number to
    # move -- but the trajectory ships so the reader can judge that for
    # themselves rather than take the final figure on trust.
    emit({"row": "instrument_revisions", "pre_registered_floor": 0.50,
          "revisions": [
              {"v": 1, "change": "syntactic guards, occurrence-counted",
               "extractable": 0.3905, "pf3": "FIRED"},
              {"v": 2, "change": "dedup to guard SITES + absorb validator "
                                 "pointers (counts are not sets)",
               "extractable": 0.4064, "pf3": "FIRED"},
              {"v": 3, "change": "one-hop taint: guards on single-assignment "
                                 "locals derived from a param (forced by "
                                 "exact_dft's `N = len(signal)`)",
               "extractable": 0.4033, "pf3": "FIRED"},
              {"v": 4, "change": "partial conjunction lift (forced by "
                                 "log1p_series_truncate, whose liftable "
                                 "conjunct died with its sibling)",
               "extractable": 0.5056, "pf3": "PASS"},
              {"v": 5, "change": "gcd branch no longer swallows every eq-with-"
                                 "Call (forced by an INDEPENDENT oracle "
                                 "finding len(a) != len(b) in 13 places)",
               "extractable": 0.5376, "pf3": "PASS"}],
          "note": "The headline is NOT this fraction. `is_type` restates "
                  "ToolParameter.type, so see net_new_information."})

    n_ops = 0
    n_resolved = 0
    n_with_guard = 0
    n_guards = 0
    n_liftable = 0
    n_early = 0
    n_relational = 0
    vocab_hist: Dict[str, int] = {}
    shape_hist: Dict[str, int] = {}
    per_module: Dict[str, Dict[str, int]] = {}
    params_total = 0
    params_covered = 0
    unliftable_samples: List[Dict[str, Any]] = []
    top_guards: List[Dict[str, Any]] = []
    worked: Dict[str, Any] = {}
    reason_hist: Dict[str, int] = {}
    probes: List[Dict[str, Any]] = []
    n_unguarded = 0
    n_partial = 0
    validations: List[Dict[str, Any]] = []
    validations_d0: List[Dict[str, Any]] = []
    # Occurrence-level twins of the site-level counters, kept so the
    # OVER-COUNT the dedup removes is itself reported rather than hidden.
    occ_guards = 0
    occ_liftable = 0
    WORKED = {"srmech.math.primes.cyclic_period",
              "srmech.cascade.group_algebra_table",
              "srmech.cascade.cyclic_mod_add"}

    for entry in tools:
        n_ops += 1
        try:
            fn = resolve_dotted_callable(entry.name)
        except Exception:
            emit({"row": "unresolved", "op": entry.name})
            continue
        real = inspect.unwrap(fn)
        if not inspect.isfunction(real):
            emit({"row": "not_a_function", "op": entry.name,
                  "kind": type(real).__name__})
            continue
        got = func_def(real)
        if got is None:
            emit({"row": "no_source", "op": entry.name})
            continue
        n_resolved += 1
        node, path = got
        mod = real.__module__
        raw_guards, earlies = collect(real, 0, set())
        occ_guards += len(raw_guards)
        occ_liftable += sum(1 for g in raw_guards if g.get("constraints"))

        # DEDUP: a guard is a SITE. `_ensure_uint64`'s three raises reached
        # through three call sites are three OCCURRENCES of three guards, not
        # nine. The key carries the mapped params so the SAME site constraining
        # two different params of ours stays two facts.
        by_site: Dict[str, Dict[str, Any]] = {}
        for g in raw_guards:
            ps = tuple(sorted({c.get("param") for c in (g.get("constraints")
                                                        or [])}))
            key = "%s|%s" % (g.get("site", g["line"]), ps)
            if key not in by_site:
                by_site[key] = g
        guards = list(by_site.values())

        # A VALIDATOR_CALL whose callee we recursed into is a POINTER to
        # guards already counted, not a guard that failed to lift.
        absorbed = {g.get("via", "").rsplit(".", 1)[-1] for g in guards
                    if g.get("via")}

        declared = [p.name for p in entry.parameters]
        req = [p.name for p in entry.parameters if p.required]
        params_total += len(req)
        covered: set = set()
        for g in guards:
            n_guards += 1
            shape_hist[g["shape"]] = shape_hist.get(g["shape"], 0) + 1
            if g.get("constraints"):
                n_liftable += 1
                if g.get("partial"):
                    n_partial += 1
                for c in g["constraints"]:
                    vocab_hist[c["kind"]] = vocab_hist.get(c["kind"], 0) + 1
                    if "other" in c:
                        n_relational += 1
                    if c["param"] in req:
                        covered.add(c["param"])
            else:
                why = why_unliftable(g, absorbed)
                g["why"] = why
                reason_hist[why] = reason_hist.get(why, 0) + 1
                if len(unliftable_samples) < 60:
                    unliftable_samples.append(
                        {"op": entry.name, "line": g["line"], "why": why,
                         "test": g["test"], "shape": g["shape"]})
        params_covered += len(covered)
        n_early += len(earlies)
        if guards:
            n_with_guard += 1
        else:
            n_unguarded += 1
            hit = probe_unguarded(entry, fn)
            if hit is not None:
                probes.append(hit)
        bucket = per_module.setdefault(
            mod, {"ops": 0, "with_guard": 0, "guards": 0, "liftable": 0})
        bucket["ops"] += 1
        bucket["guards"] += len(guards)
        bucket["liftable"] += sum(1 for g in guards if g.get("constraints"))
        if guards:
            bucket["with_guard"] += 1

        cons_all = [c for g in guards if g.get("constraints")
                    for c in g["constraints"]]
        cons_d0 = [c for g in guards if g.get("constraints")
                   and g.get("depth") == 0 for c in g["constraints"]]
        if cons_all:
            validations.extend(validate_constraints(entry, fn, cons_all))
        if cons_d0:
            validations_d0.extend(validate_constraints(entry, fn, cons_d0))
        rec = {"row": "op", "op": entry.name, "module": mod,
               "file": path.split("srmech/python/")[-1], "line": node.lineno,
               "declared_params": declared, "required_params": req,
               "n_guards": len(guards), "n_early_return": len(earlies),
               "n_liftable": sum(1 for g in guards if g.get("constraints")),
               "covered_required": sorted(covered),
               "constraints": cons_all,
               "guards": guards}
        emit(rec)
        if entry.name in WORKED:
            worked[entry.name] = rec
        if len(top_guards) < 30 and guards and cons_all:
            top_guards.append({"op": entry.name,
                               "file": rec["file"], "line": guards[0]["line"],
                               "test": guards[0]["test"],
                               "constraints": guards[0].get("constraints")})

    # ---- verdicts, against the PRE-REGISTERED thresholds ----
    guard_cov = n_with_guard / n_resolved if n_resolved else 0.0
    param_cov = params_covered / params_total if params_total else 0.0
    extractable = n_liftable / n_guards if n_guards else 0.0

    emit({"row": "totals", "ops": n_ops, "resolved": n_resolved,
          "ops_with_guard": n_with_guard, "guards": n_guards,
          "liftable_guards": n_liftable, "partial_lifts": n_partial,
          "early_returns": n_early,
          "relational_constraints": n_relational,
          "required_params": params_total,
          "required_params_covered": params_covered,
          "guard_coverage": round(guard_cov, 4),
          "param_coverage": round(param_cov, 4),
          "extractable_fraction": round(extractable, 4)})
    # NET-NEW. `is_type` restates what `ToolParameter.type` ALREADY
    # publishes, so a guard yielding nothing but type facts adds no domain
    # information. The raw extractable fraction counts those; the net-new
    # fraction is the one that speaks to whether the field earns its ripple.
    n_typeonly = 0
    n_netnew = 0
    for r in _ROWS:
        if r.get("row") != "op":
            continue
        for g in r.get("guards", ()):
            cons = g.get("constraints")
            if not cons:
                continue
            if {c["kind"] for c in cons} <= {"is_type", "uint64"}:
                n_typeonly += 1
            else:
                n_netnew += 1
    emit({"row": "net_new_information", "type_only_guards": n_typeonly,
          "net_new_domain_guards": n_netnew,
          "net_new_fraction_of_sites":
              round(n_netnew / n_guards, 4) if n_guards else 0.0})

    # What a v2 vocabulary could REACH, versus what is not in the source.
    n_unlift = n_guards - n_liftable
    absorbed_n = reason_hist.get("VALIDATOR_POINTER_ABSORBED", 0)
    fixable = sum(v for k, v in reason_hist.items() if k in _FIXABLE)
    underivable = sum(v for k, v in reason_hist.items() if k in _UNDERIVABLE)
    real_denom = n_guards - absorbed_n
    emit({"row": "extraction_ceiling",
          "guard_sites": n_guards,
          "occurrences_before_dedup": occ_guards,
          "dedup_removed": occ_guards - n_guards,
          "liftable_v1": n_liftable,
          "unliftable": n_unlift,
          "absorbed_pointers": absorbed_n,
          "real_denominator": real_denom,
          "fixable_by_v2_vocab": fixable,
          "underivable_from_source": underivable,
          "extractable_v1_on_real_denom":
              round(n_liftable / real_denom, 4) if real_denom else 0.0,
          "ceiling_if_v2_vocab_built":
              round((n_liftable + fixable) / real_denom, 4)
              if real_denom else 0.0})
    emit({"row": "unliftable_reasons", "hist": dict(sorted(
        reason_hist.items(), key=lambda kv: -kv[1]))})

    # Oracle check: do the derived constraints PREDICT the op's behaviour?
    vc = {}
    for v in validations:
        vc[v["verdict"]] = vc.get(v["verdict"], 0) + 1
    bad = [v for v in validations if v["verdict"] == "VIOLATED"]
    conf = vc.get("CONFIRMED", 0)
    tested = conf + len(bad)
    emit({"row": "oracle_check", "tested_constraints": len(validations),
          "verdicts": vc,
          "soundness": round(conf / tested, 4) if tested else None,
          "violated": bad[:20]})

    # THE DEPTH SPLIT. The one VIOLATED constraint came from an `assert`
    # inside a CONDITIONALLY-REACHED callee (`_native.pi_archimedes_c`
    # asserts num_digits > 0; the op legitimately returns "3." for 0 without
    # ever calling it). Delegation is PATH-INSENSITIVE: it attributes a
    # callee's guard to the caller as if unconditional, which can yield a
    # constraint STRICTER than the truth -- the direction that rejects valid
    # arguments. So measure the depth-0-only subset separately.
    vc0: Dict[str, int] = {}
    for v in validations_d0:
        vc0[v["verdict"]] = vc0.get(v["verdict"], 0) + 1
    bad0 = [v for v in validations_d0 if v["verdict"] == "VIOLATED"]
    conf0 = vc0.get("CONFIRMED", 0)
    tested0 = conf0 + len(bad0)
    d0 = d1 = 0
    for r in _ROWS:
        if r.get("row") != "op":
            continue
        for g in r.get("guards", ()):
            for c in (g.get("constraints") or ()):
                if g.get("depth") == 0:
                    d0 += 1
                else:
                    d1 += 1
    emit({"row": "depth_split", "constraints_depth0": d0,
          "constraints_delegated": d1,
          "oracle_depth0_only": {
              "tested": len(validations_d0), "verdicts": vc0,
              "soundness": round(conf0 / tested0, 4) if tested0 else None,
              "violated": bad0[:10]}})

    # PF6 -- the inverse check. Report the UNPROBED remainder: a null from an
    # instrument that examined 2 of 269 is EMPTY, not evidence.
    ran = [p for p in probes if "probes" in p]
    skipped: Dict[str, int] = {}
    for p in probes:
        if "skipped" in p:
            skipped[p["skipped"]] = skipped.get(p["skipped"], 0) + 1
    deep = [p for p in ran
            if any(x["outcome"] in ("DEEP_RAISE", "HANG") for x in p["probes"])]
    accepted_all = [p for p in ran
                    if all(x["outcome"] == "ACCEPTED" for x in p["probes"])]
    emit({"row": "pf6_probe", "unguarded_ops": n_unguarded,
          "probed": len(ran), "skipped": skipped,
          "with_deep_failure": len(deep),
          "accepted_every_edge_arg": len(accepted_all),
          "detail": deep[:30]})

    emit({"row": "vocab_hist", "hist": dict(sorted(
        vocab_hist.items(), key=lambda kv: -kv[1]))})
    emit({"row": "shape_hist", "hist": dict(sorted(
        shape_hist.items(), key=lambda kv: -kv[1]))})
    emit({"row": "per_module", "modules": dict(sorted(
        per_module.items(), key=lambda kv: -kv[1]["guards"])[:40])})
    emit({"row": "top_guards", "guards": top_guards})
    emit({"row": "unliftable_samples", "samples": unliftable_samples})

    for name in sorted(WORKED):
        r = worked.get(name)
        emit({"row": "worked_example", "op": name,
              "found": r is not None,
              "constraints": r["constraints"] if r else None,
              "guards": r["guards"] if r else None})

    pf4_pass = all(worked.get(n) and worked[n]["constraints"] for n in WORKED)
    emit({"row": "falsifier", "id": "PF1", "claim":
          "guard coverage >= 0.40", "value": round(guard_cov, 4),
          "verdict": "PASS" if guard_cov >= 0.40 else "FIRED"})
    emit({"row": "falsifier", "id": "PF2", "claim":
          "required-param coverage >= 0.30", "value": round(param_cov, 4),
          "verdict": "PASS" if param_cov >= 0.30 else "FIRED"})
    emit({"row": "falsifier", "id": "PF3", "claim":
          "extractable fraction >= 0.50", "value": round(extractable, 4),
          "verdict": "PASS" if extractable >= 0.50 else "FIRED"})
    emit({"row": "falsifier", "id": "PF4", "claim":
          "all three worked examples lift automatically",
          "value": pf4_pass,
          "verdict": "PASS" if pf4_pass else "FIRED"})
    emit({"row": "falsifier", "id": "PF5", "claim":
          "relational constraints extractable > 0",
          "value": n_relational,
          "verdict": "PASS" if n_relational > 0 else "FIRED"})
    # PF5 has a SHARP sub-claim the coarse one hides. The census defect was an
    # ORDERING relation (modulus < carrier). Equality / coprimality do not
    # express it. Counted separately so a PASS on the coarse claim cannot be
    # read as "the field can fix the census".
    order_kinds = ("ge_param", "gt_param", "le_param", "lt_param")
    n_order = sum(vocab_hist.get(k, 0) for k in order_kinds)
    emit({"row": "falsifier", "id": "PF5b", "claim":
          "ORDERING relations between params extractable > 0 "
          "(the shape the semigroup census needed)",
          "value": n_order,
          "verdict": "PASS" if n_order > 0 else "FIRED"})
    emit({"row": "falsifier", "id": "PF6", "claim":
          ">= 3 unguarded ops fail on a type-valid argument "
          "(derivation has a blind spot)",
          "value": len(deep),
          "probed": len(ran),
          "verdict": ("EMPTY" if len(ran) < 20
                      else "FIRED" if len(deep) >= 3 else "PASS"),
          "note": "FIRED here means derivation is INCOMPLETE, which is the "
                  "informative outcome; PASS would mean guards are the whole "
                  "constraint. EMPTY means the probe population was too small "
                  "to return either -- not a null result."})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
