"""`#T1131` P4 — PROTOTYPE of the proposed static gate, plus its controls.

THE DISCRIMINATION RULE (the thing that decides whether this gate is shippable)
==============================================================================
The gate must separate

  (a)/(b)  a ``pytest.raises(AssertionError)`` that pins a **shipped op's**
           input contract  — a defect, must go RED
  (c)      a ``pytest.raises(AssertionError)`` over a **test-local** callable —
           a meta-gate demonstrating a false assertion, or a test driven through
           its own failure path — legitimate, must stay GREEN

The rule is **subject resolution**, done statically on the AST:

  Walk the ``with`` body. Collect every "subject" — a Call's root name, an
  attribute chain's root, or a Subscript's root. Resolve each root name against
  the module's own bindings:

    * bound by ``import srmech...`` / ``from srmech... import X``  → PACKAGE
    * an attribute on a PACKAGE-bound name (``hdc.loop_bind_hd``)  → PACKAGE
    * a name bound to a PACKAGE-derived value at module or function
      scope (``m = Mat.from_rows(...)``; ``v = Vec.from_sequence(...)``) → PACKAGE
    * ``def``-ed in this file (module-level or nested)              → TEST_LOCAL
    * bound by ``import tests...`` / a conftest fixture             → TEST_LOCAL

  A ``with`` body whose subjects include at least one PACKAGE subject is a
  candidate (a)/(b) and must be listed in the exemption table or the gate fails.
  A body whose subjects are all TEST_LOCAL is class (c) and auto-passes.

The rule is deliberately CONSERVATIVE in one direction: an unresolvable subject
counts as PACKAGE (fail-loud), so a new spelling the resolver does not
understand turns the gate RED rather than silently exempting a defect.

CONTROLS (mandatory — a gate that has never fired is not evidence)
=================================================================
  NC-1  every one of the 16 shipped sites is classified, and the classification
        is compared to the hand-adjudicated ruling from P2's execution.
  NC-2  a SYNTHETIC assert-as-contract is injected into a temp test file; the
        gate must CATCH it.
  NC-3  a SYNTHETIC meta-gate (test-local assert) is injected; the gate must
        NOT catch it. Without NC-3 the gate could be "flag everything".

Run:
  PYTHONPATH=/mnt/d/GitHub/mlehaptics/docs/srmech/python \
    python3 docs/srmech/notes/_p4_static_gate_proto_rc433.py
"""

from __future__ import annotations

import ast
import json
import os
import sys
import tempfile

ROOT = "/mnt/d/GitHub/mlehaptics/docs/srmech/python"
TESTS = os.path.join(ROOT, "tests")
OUT = "/mnt/d/GitHub/mlehaptics/docs/srmech/notes/_p4_static_gate_proto_rc433.ndjson"

PACKAGE = "PACKAGE"
TEST_LOCAL = "TEST_LOCAL"
UNKNOWN = "UNKNOWN"


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


class Bindings(ast.NodeVisitor):
    """Module-wide name -> origin map (PACKAGE / TEST_LOCAL)."""

    def __init__(self):
        self.origin = {}

    def visit_Import(self, node):
        for a in node.names:
            name = a.asname or a.name.split(".")[0]
            self.origin[name] = PACKAGE if a.name.startswith("srmech") else (
                TEST_LOCAL if a.name.startswith(("tests", "conftest")) else UNKNOWN)
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
        for tgt in node.targets:
            if isinstance(tgt, ast.Name) and kind == PACKAGE:
                self.origin[tgt.id] = PACKAGE
        self.generic_visit(node)


def _local_defs(fn_node):
    """Names ``def``-ed or assigned INSIDE the enclosing test function."""
    out = {}
    for n in ast.walk(fn_node):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n is not fn_node:
            out[n.name] = TEST_LOCAL
        elif isinstance(n, ast.ClassDef):
            out[n.name] = TEST_LOCAL
    return out


def _subjects(body_nodes):
    """Every subject root-name appearing in the ``with`` body."""
    names = []
    for stmt in body_nodes:
        for n in ast.walk(stmt):
            if isinstance(n, (ast.Call, ast.Subscript, ast.Attribute)):
                r = _root_name(n)
                if r:
                    names.append(r)
    seen, out = set(), []
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


#: The exemption pragma. A class-(c) site whose SUBJECT is nonetheless package
#: code (a shipped gate helper driven through its own failure path) writes this
#: on the ``with`` line. It is deliberately verbose and must carry a reason, so
#: it cannot be pasted around without someone reading it. It is srmech-local —
#: NOT a JPL Power-of-Ten rule; Holzmann's list has exactly ten and a shipped
#: test iterates ``range(1, 11)``.
EXEMPT_RE = __import__("re").compile(r"#\s*t1131-exempt:\s*(\S.*)$")


def classify_file(path, src=None):
    """Return one record per ``pytest.raises(AssertionError)`` ``with`` site."""
    if src is None:
        with open(path, "r", encoding="utf-8") as fh:
            src = fh.read()
    src_lines = src.splitlines()
    tree = ast.parse(src, filename=path)
    b = Bindings()
    b.visit(tree)

    hits = []

    class Walk(ast.NodeVisitor):
        def __init__(self):
            self.fn = None

        def visit_FunctionDef(self, node):
            prev, self.fn = self.fn, node
            self.generic_visit(node)
            self.fn = prev

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_With(self, node):
            for item in node.items:
                ctx = item.context_expr
                if not (isinstance(ctx, ast.Call) and _is_raises(ctx)):
                    continue
                if not ctx.args or "AssertionError" not in _names(ctx.args[0]):
                    continue
                scope = dict(b.origin)
                if self.fn is not None:
                    scope.update(_local_defs(self.fn))
                subs = _subjects(node.body)
                kinds = {}
                for s in subs:
                    kinds[s] = scope.get(s, UNKNOWN)
                pkg = [s for s, k in kinds.items() if k == PACKAGE]
                unk = [s for s, k in kinds.items() if k == UNKNOWN]
                verdict = "CANDIDATE_DEFECT" if (pkg or unk) else "META_GATE_OK"
                # An explicit, reasoned pragma on the ``with`` line downgrades a
                # PACKAGE-subject site to an accepted class (c).
                idx = ctx.lineno - 1
                line = src_lines[idx] if 0 <= idx < len(src_lines) else ""
                mx = EXEMPT_RE.search(line)
                reason = mx.group(1).strip() if mx else None
                if reason and verdict == "CANDIDATE_DEFECT":
                    verdict = "EXEMPTED"
                hits.append({
                    "file": os.path.relpath(path, ROOT).replace(os.sep, "/"),
                    "line": ctx.lineno,
                    "enclosing": self.fn.name if self.fn else "<module>",
                    "subjects": kinds,
                    "package_subjects": sorted(pkg),
                    "unknown_subjects": sorted(unk),
                    "exempt_reason": reason,
                    "gate_verdict": verdict,
                })
            self.generic_visit(node)

    Walk().visit(tree)
    return hits


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
    return dotted == "pytest.raises" or dotted == "raises" or dotted.endswith(".raises")


# --------------------------------------------------------------------------
# Hand-adjudicated ground truth from P2's EXECUTED probes.
# --------------------------------------------------------------------------
GROUND_TRUTH = {
    ("tests/test_bell_chsh.py", 334): "CANDIDATE_DEFECT",
    ("tests/test_bell_chsh.py", 344): "CANDIDATE_DEFECT",
    ("tests/test_byo_cascade_toml.py", 156): "CANDIDATE_DEFECT",
    ("tests/test_frame_scope_rc430.py", 587): "META_GATE_OK",
    ("tests/test_genome_q8_coupling_rc311.py", 233): "META_GATE_OK",
    ("tests/test_loop_bind_hd.py", 115): "CANDIDATE_DEFECT",
    ("tests/test_loop_bind_hd.py", 117): "CANDIDATE_DEFECT",
    ("tests/test_loop_hd_division.py", 186): "CANDIDATE_DEFECT",
    ("tests/test_loop_hd_division.py", 192): "CANDIDATE_DEFECT",
    ("tests/test_loop_hd_division.py", 195): "CANDIDATE_DEFECT",
    ("tests/test_loop_hd_native_parity.py", 178): "CANDIDATE_DEFECT",
    ("tests/test_mat_carrier_rc69.py", 72): "CANDIDATE_DEFECT",
    ("tests/test_mat_matmul_bridge_rc72.py", 131): "CANDIDATE_DEFECT",
    ("tests/test_octonion_carrier_rc324.py", 355): "META_GATE_OK",
    ("tests/test_owner_axis_rc410.py", 659): "META_GATE_OK",
    ("tests/test_vec_carrier_rc129.py", 90): "CANDIDATE_DEFECT",
}

# --------------------------------------------------------------------------
# NC-2 / NC-3 synthetic controls.
# --------------------------------------------------------------------------
NC2_SYNTHETIC_DEFECT = '''
import pytest
from srmech.math.vec import Vec

def test_a_newly_landed_assert_as_contract():
    """A synthetic `#T1131` instance: pins a SHIPPED op's contract on an assert."""
    v = Vec.from_sequence([1.0, 2.0])
    with pytest.raises(AssertionError):
        _ = v[9]
'''

NC3_SYNTHETIC_META_GATE = '''
import pytest

def _demonstrates_a_false_assertion(x):
    assert x == 1, "planted"
    return x

def test_the_gate_itself_fires():
    """A synthetic class-(c): the subject is defined in THIS file."""
    with pytest.raises(AssertionError):
        _demonstrates_a_false_assertion(2)
'''

NC4_SYNTHETIC_INDIRECT_DEFECT = '''
import pytest
import srmech.math.hdc as hdc

def test_indirect_module_attribute_form():
    """Same defect class, spelled as a module attribute rather than a from-import."""
    with pytest.raises(AssertionError):
        hdc.loop_conj_hd([1.0] * 3)
'''


NC5_EXEMPT_PRAGMA = '''
import pytest
import srmech.math.hdc as hdc

def test_a_reasoned_exemption():
    """A PACKAGE subject that is nonetheless a legitimate meta-gate."""
    with pytest.raises(AssertionError):  # t1131-exempt: drives a shipped gate through its own failure path
        hdc.loop_conj_hd([1.0] * 3)
'''

NC6_REASONLESS_PRAGMA = '''
import pytest
import srmech.math.hdc as hdc

def test_a_bare_pragma_must_not_exempt():
    """A pragma with no reason must NOT downgrade the verdict."""
    with pytest.raises(AssertionError):  # t1131-exempt:
        hdc.loop_conj_hd([1.0] * 3)
'''


def main():
    recs = []
    hits = []
    for fn in sorted(os.listdir(TESTS)):
        if fn.endswith(".py"):
            hits.extend(classify_file(os.path.join(TESTS, fn)))

    print("=== NC-1: classification of the 16 shipped sites ===")
    mismatches = []
    for h in sorted(hits, key=lambda r: (r["file"], r["line"])):
        key = (h["file"], h["line"])
        truth = GROUND_TRUTH.get(key)
        ok = truth == h["gate_verdict"]
        if truth is None:
            ok = None
        if truth is not None and not ok:
            mismatches.append(key)
        print("%-46s:%-5d %-17s truth=%-17s %s" % (
            h["file"], h["line"], h["gate_verdict"], truth,
            "OK" if ok else ("NEW-SITE" if ok is None else "*** MISMATCH ***")))
        h["ground_truth"] = truth
        h["agrees"] = ok
        recs.append(dict(h, control="NC-1"))

    print("\n=== NC-2 / NC-3 / NC-4: synthetic controls ===")
    for label, src, want in (
            ("NC-2 synthetic DEFECT", NC2_SYNTHETIC_DEFECT, "CANDIDATE_DEFECT"),
            ("NC-3 synthetic META-GATE", NC3_SYNTHETIC_META_GATE, "META_GATE_OK"),
            ("NC-4 module-attr DEFECT", NC4_SYNTHETIC_INDIRECT_DEFECT, "CANDIDATE_DEFECT"),
            ("NC-5 pragma EXEMPTS", NC5_EXEMPT_PRAGMA, "EXEMPTED"),
            ("NC-6 reasonless pragma", NC6_REASONLESS_PRAGMA, "CANDIDATE_DEFECT"),
    ):
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                         encoding="utf-8") as fh:
            fh.write(src)
            tmp = fh.name
        got = classify_file(tmp)
        verdicts = [g["gate_verdict"] for g in got]
        ok = verdicts == [want]
        print("%-26s -> %-40s want=%-17s %s" % (
            label, verdicts, want, "CAUGHT/OK" if ok else "*** FAILED ***"))
        recs.append({"control": label, "verdicts": verdicts, "want": want,
                     "agrees": ok, "detail": got})
        os.unlink(tmp)

    n_cand = sum(1 for h in hits if h["gate_verdict"] == "CANDIDATE_DEFECT")
    n_meta = sum(1 for h in hits if h["gate_verdict"] == "META_GATE_OK")
    print("\nsites classified: %d  (CANDIDATE_DEFECT=%d, META_GATE_OK=%d)"
          % (len(hits), n_cand, n_meta))
    print("NC-1 mismatches:", mismatches or "none")

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({
            "record": "gate_meta", "n_sites": len(hits),
            "n_candidate_defect": n_cand, "n_meta_gate_ok": n_meta,
            "nc1_mismatches": [list(m) for m in mismatches],
            "python": sys.version.split()[0],
        }, sort_keys=True) + "\n")
        for r in recs:
            fh.write(json.dumps(r, sort_keys=True, default=str) + "\n")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
