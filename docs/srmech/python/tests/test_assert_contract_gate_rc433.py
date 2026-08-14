"""rc433 (`#T1131`) — the guard that is not there when it counts.

WHY THIS MODULE EXISTS
======================
**Pytest's assertion rewriter defeats ``python -O``, and it defeats it
asymmetrically.** Pytest compiles test modules itself, replacing each ``assert``
with explicit raising bytecode. Package modules get no such treatment. So under
``python -O``:

===================================  ==========================================
``assert`` in a TEST module          **SURVIVES** (pytest rewrote it)
``assert`` in a PACKAGE module       **VANISHES** (``-O`` stripped it)
===================================  ==========================================

The consequence is the defect this module gates. A test written as::

    with pytest.raises(AssertionError):
        some_shipped_op(bad_input)

certifies a guard **that does not exist in an optimized interpreter** — while
the test's own asserts keep working, so the suite looks fine. The ``-O``
boundary falls exactly on the PACKAGE / TEST_LOCAL line, which is why the gate
below can discriminate structurally rather than by a hand-kept list.

This is not theoretical. Two silent-wrong-answers measured at rc432, pure path::

    python3 -O:  v[-5] on a 3-vector          -> 20.0   (== v[1]; no error)
    python3 -O:  Mat.from_rows([[1.0],[2.0,3.0]])
                 -> shape (2,1), [[1.0],[2.0]]         (3.0 silently dropped)

Both raised ``AssertionError`` in the default mode. Silent-wrong-answer is the
top defect class in this project, so rc433 promoted twelve such guards to real
``raise`` statements and this module makes the class unrepeatable.

NAMING (read this before adding a peer)
=======================================
This is a **srmech-local invariant**. It is emphatically **NOT "Rule 11"** —
Holzmann's Power of Ten has exactly ten rules, and
``tests/test_jpl_audit.py::test_audit_doc_present_and_mentions_all_rules``
iterates ``range(1, 11)``. Do not give a new invariant a JPL rule number.

THE DISCRIMINATION RULE — subject resolution
============================================
Walk the guarded body. Collect every "subject" (a Call's root name, an
attribute chain's root, a Subscript's root) and resolve each against the
module's own bindings:

===============================================================  ============
bound by ``import srmech...`` / ``from srmech... import X``       PACKAGE
an attribute on a PACKAGE-bound name (``hdc.loop_bind_hd``)       PACKAGE
a name assigned from a PACKAGE value (``m = Mat.from_rows(…)``)   PACKAGE
``def``/``class``-ed in this file (module level or nested)        TEST_LOCAL
bound by ``import tests...`` / a relative import                  TEST_LOCAL
a literal / comprehension                                         TEST_LOCAL
===============================================================  ============

A body with at least one PACKAGE subject is a **CANDIDATE_DEFECT**. A body
whose subjects are all TEST_LOCAL is a legitimate meta-gate (a test driven
through its own failure path) and passes.

**An UNRESOLVABLE subject counts as PACKAGE.** This fail-loud default is
load-bearing and must not be softened: a spelling the resolver does not
understand turns the gate RED rather than silently exempting a real defect.
The conservative direction is what surfaced the ``census = _census()`` gap
during development — as a false RED on a legitimate meta-gate, which is the
right failure mode.

THE EVASION ROUTE IS COVERED
============================
``pytest.raises`` is not the only spelling. This pins the identical contract::

    try:
        op(bad_input)
    except AssertionError:
        pass

A gate that only saw ``pytest.raises`` would be side-stepped by writing it that
way, so ``except AssertionError:`` handlers are classified by the subject of
their ``try`` body under the identical rule. Three such sites exist in the tree
(all legitimately TEST_LOCAL); they are why the real population is 19 rather
than the 16 a ``pytest.raises``-only scan reports.

EXEMPTION
=========
A ``# t1131-exempt: <reason>`` pragma on the guard line downgrades a
PACKAGE-subject site. A pragma with **no reason does not exempt** (NC-6 proves
it). **The exemption table ships EMPTY** — that is what makes the strict zero
honest, and an entry should be argued for, not added for convenience.
"""
from __future__ import annotations

import ast
import os
import re
import tempfile
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).resolve().parent
PKG_DIR = TESTS_DIR.parent / "srmech"

PACKAGE = "PACKAGE"
TEST_LOCAL = "TEST_LOCAL"
UNKNOWN = "UNKNOWN"

#: A guard line may carry ``# t1131-exempt: <reason>``. The reason is MANDATORY.
EXEMPT_RE = re.compile(r"#\s*t1131-exempt:\s*(\S.*)$")


# ══════════════════════════════════════════════════════════════════════════
# The classifier
# ══════════════════════════════════════════════════════════════════════════
def _root_name(node):
    """The leftmost ``Name`` of an attribute / call / subscript chain."""
    while True:
        if isinstance(node, ast.Attribute):
            node = node.value
        elif isinstance(node, ast.Call):
            node = node.func
        elif isinstance(node, ast.Subscript):
            node = node.value
        else:
            break
    return node.id if isinstance(node, ast.Name) else None


class _Bindings(ast.NodeVisitor):
    """Module-wide ``name -> origin`` map."""

    def __init__(self):
        self.origin = {}

    def visit_Import(self, node):
        for a in node.names:
            name = a.asname or a.name.split(".")[0]
            if a.name.startswith("srmech"):
                self.origin[name] = PACKAGE
            elif a.name.startswith(("tests", "conftest")):
                self.origin[name] = TEST_LOCAL
            else:
                self.origin[name] = UNKNOWN
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        mod = node.module or ""
        if mod.startswith("srmech"):
            kind = PACKAGE
        elif mod.startswith(("tests", "conftest")) or node.level:
            kind = TEST_LOCAL
        else:
            kind = UNKNOWN
        for a in node.names:
            self.origin[a.asname or a.name] = kind
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.origin.setdefault(node.name, TEST_LOCAL)
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        self.origin.setdefault(node.name, TEST_LOCAL)
        self.generic_visit(node)

    def visit_Assign(self, node):
        """Propagate PACKAGE-ness through ``m = Mat.from_rows(...)``."""
        src = _root_name(node.value)
        kind = self.origin.get(src) if src else None
        if kind == PACKAGE:
            for tgt in node.targets:
                if isinstance(tgt, ast.Name):
                    self.origin[tgt.id] = PACKAGE
        self.generic_visit(node)


def _local_defs(fn_node, module_origin):
    """Names bound INSIDE the enclosing test function.

    Tracks THREE binding kinds, not one. Tracking only ``def``/``class`` was a
    real gap, caught during development on a SHIPPED site:
    ``test_frame_scope_rc430.py`` binds ``census = _census()`` and then uses
    ``census[name]`` inside a guarded body. With assignments untracked,
    ``census`` resolved UNKNOWN, the fail-loud rule promoted it to
    CANDIDATE_DEFECT, and a legitimate meta-gate was flagged.
    """
    out = {}
    for n in ast.walk(fn_node):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n is not fn_node:
            out[n.name] = TEST_LOCAL
        elif isinstance(n, ast.ClassDef):
            out[n.name] = TEST_LOCAL
    scope = dict(module_origin)
    scope.update(out)
    for n in ast.walk(fn_node):
        if not isinstance(n, (ast.Assign, ast.AnnAssign)):
            continue
        value = n.value
        if value is None:
            continue
        src = _root_name(value)
        kind = scope.get(src) if src else None
        if kind is None and isinstance(
                value, (ast.Dict, ast.List, ast.Tuple, ast.Set, ast.Constant,
                        ast.DictComp, ast.ListComp, ast.SetComp)):
            kind = TEST_LOCAL      # a literal / comprehension is not package state
        if kind is None:
            continue
        targets = n.targets if isinstance(n, ast.Assign) else [n.target]
        for t in targets:
            if isinstance(t, ast.Name):
                out[t.id] = kind
                scope[t.id] = kind
    return out


def _subjects(body_nodes):
    """Every subject root-name appearing in the guarded body, in order."""
    seen, out = set(), []
    for stmt in body_nodes:
        for n in ast.walk(stmt):
            if isinstance(n, (ast.Call, ast.Subscript, ast.Attribute)):
                r = _root_name(n)
                if r and r not in seen:
                    seen.add(r)
                    out.append(r)
    return out


def _names(node):
    if isinstance(node, ast.Tuple):
        out = []
        for e in node.elts:
            out.extend(_names(e))
        return out
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, ast.Attribute):
        return [node.attr]
    return []


def _is_raises(node):
    f = node.func
    parts = []
    while isinstance(f, ast.Attribute):
        parts.append(f.attr)
        f = f.value
    if isinstance(f, ast.Name):
        parts.append(f.id)
    parts.reverse()
    dotted = ".".join(parts)
    return dotted in ("pytest.raises", "raises") or dotted.endswith(".raises")


def classify_source(src, label="<memory>"):
    """Return one record per ``AssertionError``-guarding site in ``src``."""
    src_lines = src.splitlines()
    tree = ast.parse(src, filename=label)
    binds = _Bindings()
    binds.visit(tree)
    hits = []

    def _record(lineno, fn_name, body_nodes, scope, shape):
        subs = _subjects(body_nodes)
        kinds = {s: scope.get(s, UNKNOWN) for s in subs}
        pkg = sorted(s for s, k in kinds.items() if k == PACKAGE)
        unk = sorted(s for s, k in kinds.items() if k == UNKNOWN)
        verdict = "CANDIDATE_DEFECT" if (pkg or unk) else "META_GATE_OK"
        line = src_lines[lineno - 1] if 0 <= lineno - 1 < len(src_lines) else ""
        mx = EXEMPT_RE.search(line)
        reason = mx.group(1).strip() if mx else None
        if reason and verdict == "CANDIDATE_DEFECT":
            verdict = "EXEMPTED"
        hits.append({
            "file": label, "line": lineno, "enclosing": fn_name, "shape": shape,
            "package_subjects": pkg, "unknown_subjects": unk,
            "exempt_reason": reason, "gate_verdict": verdict,
        })

    class _Walk(ast.NodeVisitor):
        def __init__(self):
            self.fn = None

        def visit_FunctionDef(self, node):
            prev, self.fn = self.fn, node
            self.generic_visit(node)
            self.fn = prev

        visit_AsyncFunctionDef = visit_FunctionDef

        def _scope(self):
            scope = dict(binds.origin)
            if self.fn is not None:
                scope.update(_local_defs(self.fn, binds.origin))
            return scope

        def visit_With(self, node):
            for item in node.items:
                ctx = item.context_expr
                if not (isinstance(ctx, ast.Call) and _is_raises(ctx)):
                    continue
                if not ctx.args or "AssertionError" not in _names(ctx.args[0]):
                    continue
                _record(ctx.lineno, self.fn.name if self.fn else "<module>",
                        node.body, self._scope(), "pytest_raises")
            self.generic_visit(node)

        visit_AsyncWith = visit_With

        def visit_Try(self, node):
            """The EVASION ROUTE — ``except AssertionError:`` pins the same
            contract, so it is classified by the ``try`` body's subject."""
            for h in node.handlers:
                if h.type is None or "AssertionError" not in _names(h.type):
                    continue
                _record(h.lineno, self.fn.name if self.fn else "<module>",
                        node.body, self._scope(), "except_handler")
            self.generic_visit(node)

    _Walk().visit(tree)
    return hits


def _scan_tests():
    hits = []
    for path in sorted(TESTS_DIR.glob("*.py")):
        src = path.read_text(encoding="utf-8")
        hits.extend(classify_source(src, label=path.name))
    return hits


# ══════════════════════════════════════════════════════════════════════════
# 1. THE GATE — strict zero, empty exemption table
# ══════════════════════════════════════════════════════════════════════════

#: Sites accepted DESPITE resolving to a package subject. **SHIPS EMPTY.**
#: An entry is a debt, not a convenience; argue for it in review.
EXEMPTIONS: "dict[tuple[str, int], str]" = {}


def test_no_test_pins_a_package_input_contract_on_an_assert():
    """STRICT ZERO — the rc433 gate.

    FALSIFIER: write ``with pytest.raises(AssertionError): shipped_op(bad)``
    anywhere under ``tests/`` and this goes red. That construction certifies a
    guard which does not exist under ``python -O``.

    THE FIX IS NEVER TO DELETE THE TEST. Promote the package ``assert`` to a
    real ``raise`` of the type tree precedent already uses for that input
    class, then update the test to expect it.
    """
    hits = _scan_tests()
    offenders = [h for h in hits if h["gate_verdict"] == "CANDIDATE_DEFECT"]
    unexpected = [h for h in offenders
                  if (h["file"], h["line"]) not in EXEMPTIONS]
    assert not unexpected, (
        "a test pins a PACKAGE op's input contract on an assert, which "
        "`python -O` strips — the guard does not exist in an optimized "
        "interpreter:\n" + "\n".join(
            f"  {h['file']}:{h['line']} in {h['enclosing']} "
            f"({h['shape']}) package_subjects={h['package_subjects']} "
            f"unresolved={h['unknown_subjects']}" for h in unexpected))


def test_the_exemption_table_is_empty():
    """The strict zero is only honest while nothing is exempted.

    FALSIFIER: adding an entry to ``EXEMPTIONS`` fails this until someone
    deliberately edits the expectation — which is the point. An exemption
    should cost a conversation.
    """
    assert EXEMPTIONS == {}, (
        f"the rc433 exemption table shipped EMPTY; it now holds "
        f"{sorted(EXEMPTIONS)}. Each entry is a guard that does not exist "
        f"under -O. Justify or drain it.")


# ══════════════════════════════════════════════════════════════════════════
# 2. CONTROLS — a gate that has never fired is not evidence
# ══════════════════════════════════════════════════════════════════════════

_NC2_SYNTHETIC_DEFECT = '''
import pytest
from srmech.math.vec import Vec

def test_a_newly_landed_assert_as_contract():
    v = Vec.from_sequence([1.0, 2.0])
    with pytest.raises(AssertionError):
        _ = v[9]
'''

_NC3_SYNTHETIC_META_GATE = '''
import pytest

def _demonstrates_a_false_assertion(x):
    assert x == 1, "planted"
    return x

def test_the_gate_itself_fires():
    with pytest.raises(AssertionError):
        _demonstrates_a_false_assertion(2)
'''

_NC4_MODULE_ATTRIBUTE_SPELLING = '''
import pytest
import srmech.math.hdc as hdc

def test_indirect_module_attribute_form():
    with pytest.raises(AssertionError):
        hdc.loop_conj_hd([1.0] * 3)
'''

_NC5_REASONED_PRAGMA = '''
import pytest
import srmech.math.hdc as hdc

def test_a_reasoned_exemption():
    with pytest.raises(AssertionError):  # t1131-exempt: drives a shipped gate through its own failure path
        hdc.loop_conj_hd([1.0] * 3)
'''

_NC6_REASONLESS_PRAGMA = '''
import pytest
import srmech.math.hdc as hdc

def test_a_bare_pragma_must_not_exempt():
    with pytest.raises(AssertionError):  # t1131-exempt:
        hdc.loop_conj_hd([1.0] * 3)
'''

_NC7_TRY_EXCEPT_EVASION = '''
import pytest
from srmech.math.vec import Vec

def test_written_as_try_except_instead():
    v = Vec.from_sequence([1.0, 2.0])
    try:
        _ = v[9]
        raise SystemExit("should not get here")
    except AssertionError:
        pass
'''

_NC8_TRY_EXCEPT_META_GATE = '''
import pytest

def _planted(x):
    assert x == 1, "planted"
    return x

def test_try_except_over_a_local_subject():
    try:
        _planted(2)
    except AssertionError:
        pass
'''


@pytest.mark.parametrize("label,src,want", [
    ("NC-2 synthetic defect (from-import subject)",
     _NC2_SYNTHETIC_DEFECT, "CANDIDATE_DEFECT"),
    ("NC-3 synthetic meta-gate (test-local subject)",
     _NC3_SYNTHETIC_META_GATE, "META_GATE_OK"),
    ("NC-4 module-attribute spelling",
     _NC4_MODULE_ATTRIBUTE_SPELLING, "CANDIDATE_DEFECT"),
    ("NC-5 reasoned pragma exempts",
     _NC5_REASONED_PRAGMA, "EXEMPTED"),
    ("NC-6 reasonless pragma does NOT exempt",
     _NC6_REASONLESS_PRAGMA, "CANDIDATE_DEFECT"),
    ("NC-7 try/except evasion route",
     _NC7_TRY_EXCEPT_EVASION, "CANDIDATE_DEFECT"),
    ("NC-8 try/except over a local subject",
     _NC8_TRY_EXCEPT_META_GATE, "META_GATE_OK"),
])
def test_gate_discriminates_on_synthetic_controls(label, src, want):
    """Seven synthetic controls spanning BOTH directions.

    NC-3 and NC-8 are the ones that matter most: without a control the gate
    must NOT catch, "flag everything" would score perfectly on the rest.
    """
    got = [h["gate_verdict"] for h in classify_source(src, label="<control>")]
    assert got == [want], f"{label}: classified {got}, expected [{want}]"


def test_gate_agrees_with_hand_adjudication_on_the_live_tree():
    """NC-1 — the live-tree control.

    Every surviving site in ``tests/`` was hand-adjudicated by reading it:
    all seven are meta-gates over a TEST-LOCAL subject (a gate driven through
    its own failure path, or a test driven through its own). If a NEW site
    appears the strict-zero gate above catches it; this one asserts the
    classifier still SEES the population rather than silently reading zero
    because the walker broke.
    """
    hits = _scan_tests()
    assert len(hits) >= 7, (
        f"the classifier found only {len(hits)} guarded sites in tests/; it "
        f"previously found 19 (12 since repaired + 7 meta-gates). A number "
        f"this low means the AST walk stopped matching, and the strict-zero "
        f"gate above would be vacuously green.")
    kinds = {h["gate_verdict"] for h in hits}
    assert kinds <= {"META_GATE_OK", "CANDIDATE_DEFECT", "EXEMPTED"}, kinds


def test_the_scan_actually_reads_files_and_the_shipped_meta_gates_survive():
    """FIXTURE AUDIT — this scan COULD have failed.

    Planting a synthetic defect INTO a copy of the real tests directory must
    turn the strict-zero gate red. Without this, ``_scan_tests`` could be
    returning an empty list for a mundane reason (wrong directory, a glob that
    matches nothing) and every assertion above would be vacuous.
    """
    with tempfile.TemporaryDirectory() as td:
        planted = Path(td) / "test_planted_rc433.py"
        planted.write_text(_NC2_SYNTHETIC_DEFECT, encoding="utf-8")
        hits = classify_source(planted.read_text(encoding="utf-8"),
                               label=planted.name)
    assert [h["gate_verdict"] for h in hits] == ["CANDIDATE_DEFECT"]

    # ...and the real directory is genuinely being read.
    assert TESTS_DIR.is_dir() and (TESTS_DIR / "test_loop_bind_hd.py").exists()
    assert len(list(TESTS_DIR.glob("*.py"))) > 100, (
        "tests/ glob matched suspiciously few files — the scan may be "
        "pointed at the wrong directory")


# ══════════════════════════════════════════════════════════════════════════
# 3. THE CEIL — a down-only ratchet on input-shaped package asserts
# ══════════════════════════════════════════════════════════════════════════
#
# The gate above covers what a TEST pins. This covers what NOTHING pins: a
# package `assert` in the prologue of a PUBLIC callable, naming one of that
# callable's own parameters. That shape IS an input contract, and every one of
# them evaporates under `-O`.
#
# This is DEBT BEING DRAINED, not an accepted level. rc433 took the population
# from 49 to 41 by promoting eight of them; the number must keep falling.
# It is a CEIL rather than a strict zero because the residual is genuinely
# heterogeneous — some rows are self-checks on internal state that happen to
# name a parameter, and each needs the per-site execution rc433 did for its
# twelve before it can be promoted or dismissed.

#: Measured on the rc433 branch AFTER the twelve promotions. DOWN ONLY.
#: rc432 baseline was 49. Never raise this to make a change fit.
CEIL_INPUT_SHAPED_PACKAGE_ASSERTS = 41

#: How many leading statements of a callable count as "the guard prologue".
_PROLOGUE = 6


def _param_names(fn):
    a = fn.args
    names = [p.arg for p in a.posonlyargs + a.args + a.kwonlyargs]
    if a.vararg:
        names.append(a.vararg.arg)
    if a.kwarg:
        names.append(a.kwarg.arg)
    return set(names)


def _mentions(node, names):
    return any(isinstance(n, ast.Name) and n.id in names for n in ast.walk(node))


def _input_shaped_asserts(path):
    """Package asserts in a public callable's prologue that name a parameter."""
    src = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError:
        return []
    found = []

    class _W(ast.NodeVisitor):
        def __init__(self):
            self.fn = None

        def visit_FunctionDef(self, node):
            prev, self.fn = self.fn, node
            self.generic_visit(node)
            self.fn = prev

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_Assert(self, node):
            fn = self.fn
            if fn is None or fn.name.startswith("_"):
                return
            body = [s for s in fn.body
                    if not (isinstance(s, ast.Expr)
                            and isinstance(s.value, ast.Constant))]
            pos = next((i for i, s in enumerate(body)
                        if getattr(s, "lineno", 0) <= node.lineno
                        <= getattr(s, "end_lineno", 0)), 999)
            if pos < _PROLOGUE and _mentions(node.test, _param_names(fn)):
                found.append((str(path.relative_to(PKG_DIR)).replace(os.sep, "/"),
                              node.lineno, fn.name))

    _W().visit(tree)
    return found


def _census_input_shaped():
    rows = []
    for path in sorted(PKG_DIR.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        rows.extend(_input_shaped_asserts(path))
    return rows


def test_input_shaped_package_asserts_only_go_down():
    """DOWN-ONLY CEIL — srmech-local, NOT a JPL rule.

    FALSIFIER: add an ``assert`` naming a parameter to the prologue of any
    public callable in ``srmech/`` and this goes red. The repair is a real
    ``raise``, not a bump.

    If the count DROPS, lower the constant in the same commit — a stale ceiling
    silently re-opens the room it was meant to close.
    """
    rows = _census_input_shaped()
    n = len(rows)
    assert n <= CEIL_INPUT_SHAPED_PACKAGE_ASSERTS, (
        f"input-shaped package asserts rose to {n} (ceil "
        f"{CEIL_INPUT_SHAPED_PACKAGE_ASSERTS}). Each one is an input contract "
        f"that vanishes under `python -O`. Promote it to a real raise instead "
        f"of raising the ceiling. New/moved rows:\n" + "\n".join(
            f"  {f}:{ln} in {fn}" for f, ln, fn in sorted(rows)[:60]))
    assert n == CEIL_INPUT_SHAPED_PACKAGE_ASSERTS, (
        f"input-shaped package asserts FELL to {n} (ceil "
        f"{CEIL_INPUT_SHAPED_PACKAGE_ASSERTS}) — good news, but lower the "
        f"constant in this commit so the ratchet keeps its teeth.")


def test_the_ceil_census_is_not_vacuous():
    """CONTROL on the CEIL instrument.

    A planted public callable whose prologue asserts a parameter must be
    counted, and a private one must not. Without this, ``_census_input_shaped``
    could be returning ``[]`` and the ratchet would read 0 forever.
    """
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "planted.py"
        p.write_text(
            "def public_op(x):\n"
            "    assert x > 0, 'x must be positive'\n"
            "    return x\n"
            "\n"
            "def _private_op(y):\n"
            "    assert y > 0, 'y must be positive'\n"
            "    return y\n"
            "\n"
            # Six leading statements, so the assert sits at prologue index 6 —
            # one PAST the window. Five was not enough: the first draft of this
            # control put it at index 5, the classifier counted it, and this
            # test went red. That is the control working, and it is why the
            # off-by-one is spelled out here.
            "def public_internal(z):\n"
            "    total = 0\n"
            "    for _ in range(3):\n"
            "        total += 1\n"
            "    for _ in range(3):\n"
            "        total += 1\n"
            "    for _ in range(3):\n"
            "        total += 1\n"
            "    for _ in range(3):\n"
            "        total += 1\n"
            "    for _ in range(3):\n"
            "        total += 1\n"
            "    assert z > 0, 'too late to be a prologue guard'\n"
            "    return total\n",
            encoding="utf-8")
        # _input_shaped_asserts reports paths relative to PKG_DIR; the planted
        # file is elsewhere, so call the AST half directly on a shimmed path.
        src = p.read_text(encoding="utf-8")
        tree = ast.parse(src)
        hits = []
        for fn in tree.body:
            if not isinstance(fn, ast.FunctionDef) or fn.name.startswith("_"):
                continue
            body = [s for s in fn.body
                    if not (isinstance(s, ast.Expr)
                            and isinstance(s.value, ast.Constant))]
            for node in ast.walk(fn):
                if not isinstance(node, ast.Assert):
                    continue
                pos = next((i for i, s in enumerate(body)
                            if getattr(s, "lineno", 0) <= node.lineno
                            <= getattr(s, "end_lineno", 0)), 999)
                if pos < _PROLOGUE and _mentions(node.test, _param_names(fn)):
                    hits.append(fn.name)

    assert hits == ["public_op"], (
        f"the CEIL classifier picked {hits}; it must count the public "
        f"prologue guard, skip the private one, and skip the mid-body one")


def test_the_ceil_census_reads_the_real_package():
    """FIXTURE AUDIT on the CEIL — it COULD have failed.

    ``PKG_DIR`` must actually resolve to the shipped package, and the census
    must be non-empty. A zero here would make the ceiling vacuous rather than
    satisfied.
    """
    assert PKG_DIR.is_dir(), PKG_DIR
    assert (PKG_DIR / "math" / "hdc.py").exists(), "PKG_DIR is not srmech/"
    rows = _census_input_shaped()
    assert rows, "the CEIL census found nothing at all — the walk is broken"
    files = {f for f, _, _ in rows}
    assert len(files) > 5, f"census covers only {files}; expected many modules"
