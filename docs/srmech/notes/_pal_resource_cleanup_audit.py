#!/usr/bin/env python3
"""_pal_resource_cleanup_audit.py — READ-ONLY code archaeology for `#T1129`.

MEASURE, DO NOT REPAIR. This script never edits package source; it only
reads `docs/srmech/python/srmech/**/*.py` and `docs/srmech/c/src/*.c` and
emits NDJSON findings to `_pal_resource_cleanup_audit.ndjson` alongside it.

THE SEED DEFECT (measured in rc431, srmech.biology.genome.genome_save):
``path.mkdir(parents=True, exist_ok=True)`` runs BEFORE the validation that
then rejects the caller's input — so a rejected call still leaves a
directory behind. Generalised: an operation that ACQUIRES a resource
(mkdir / open-for-write / tempfile) before it has finished validating, and
on the error path leaves that resource acquired. The mutation is real, the
failure is loud, but the ORPHANED RESOURCE is silent.

SCANNER DESIGN (Python side — AST, no imports, no numpy dependency):

For every function in the scanned tree, find "acquire" calls (mkdir /
makedirs / open in a write-ish mode NOT inside a `with` / tempfile
mkdtemp|mkstemp|NamedTemporaryFile / Path.touch). For each acquire call,
walk the REST of the function (by source line order, pruning into nested
def/lambda/class bodies) for:

  TIER A (direct)  — a `raise` statement lexically inside the SAME function,
                      at a later line, not covered by an enclosing
                      try/finally whose try-body contains the acquire.
  TIER B (1-hop)   — a call to another function (resolved by bare name
                      across the whole scanned package — a known
                      false-positive source, documented below) that is
                      itself known (transitively) to raise.

THE SEED DEFECT ITSELF IS A TIER-B CASE: genome_save's mkdir is followed
by `_split_into_chromosomes(...)`, `_disk_block(...)` (via `_leaf_blocks`),
and `_resolve_attestation(...)` — none of which raise *lexically inside*
genome_save. A scanner that only checked Tier A would report a FALSE
REFUTED on the seed defect itself. This is exactly the failure mode named
in the brief ("An instrument that cannot return otherwise is not a
measurement... it can also return a FALSE REFUTED") — so Tier B exists
specifically to not repeat that mistake, and the self-test below proves it.

KNOWN FALSE-POSITIVE CLASS (documented per the brief's discipline, not
swept under the rug):
  - Tier-B name resolution is BARE-NAME, whole-package. Two unrelated
    modules that both define `_validate(...)` will cross-contaminate each
    other's can_raise status. This inflates recall at the cost of precision
    — acceptable for a maintainer TRIAGE ranking, not for an automated gate
    without follow-up (see Q5 in the .md report).
  - "Covered by try/finally" is checked STRUCTURALLY (does a finally block
    exist around the acquire) — NOT semantically (does the finally actually
    release the resource). A `finally: pass` wrapping an acquire will read
    as "protected" here even though nothing is released. This is the
    documented direction of the false-negative class: the scanner can
    UNDER-count real leaks it structurally can't tell from a real cleanup.
  - A deliberately-resumable/partial artifact (a journal, a lock file, a
    resumable write) is NOT a defect — this scanner cannot tell "orphaned"
    from "designed to persist across a failure" and does not try to; every
    hit needs the file:line read to make that call (see the .md report).

C SIDE: a lighter grep-based pass over PAL acquire calls
(`srmech_plat_mkdir` / `srmech_plat_file_open_ro` / `srmech_plat_rstream_open`
/ `srmech_plat_dir_open`) and their paired release calls, since the C
control-flow discipline (no goto, Rule 1) is uniformly
"if (st != SRMECH_OK) { <release>; return st; }" — checkable by presence/
absence of the release call on the SAME line as each early return between
an open call and its matching close, which a full AST parse is overkill for.

Usage:
    cd /mnt/d/GitHub/mlehaptics
    export PYTHONPATH=/mnt/d/GitHub/mlehaptics/docs/srmech/python
    export SRMECH_EXPECT_PURE=1
    python3 docs/srmech/notes/_pal_resource_cleanup_audit.py --self-test
    python3 docs/srmech/notes/_pal_resource_cleanup_audit.py --scan
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parents[3]
PY_SRC_ROOT = REPO_ROOT / "docs" / "srmech" / "python" / "srmech"
C_SRC_ROOT = REPO_ROOT / "docs" / "srmech" / "c" / "src"
NDJSON_OUT = Path(__file__).resolve().parent / "_pal_resource_cleanup_audit.ndjson"

# ---------------------------------------------------------------------- #
# Acquire-call recognition (Python)
# ---------------------------------------------------------------------- #

_WRITE_MODE_RE = re.compile(r"[wxa]")


def _acquire_kind(call: ast.Call) -> Optional[str]:
    """Classify `call` as a resource-acquire, or None."""
    func = call.func
    # X.mkdir(...) — pathlib.Path.mkdir
    if isinstance(func, ast.Attribute) and func.attr == "mkdir":
        return "mkdir"
    if isinstance(func, ast.Attribute) and func.attr == "touch":
        return "touch"
    if isinstance(func, ast.Attribute) and func.attr in (
        "write_bytes", "write_text",
    ):
        return "write_atomic"  # creates/truncates a file in one call
    if isinstance(func, ast.Name) and func.id == "open":
        mode = None
        if len(call.args) >= 2 and isinstance(call.args[1], ast.Constant):
            mode = call.args[1].value
        for kw in call.keywords:
            if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                mode = kw.value.value
        if isinstance(mode, str) and _WRITE_MODE_RE.search(mode):
            return "open_write"
        return None
    if isinstance(func, ast.Attribute) and func.attr in (
        "makedirs", "mkdir",
    ):
        return "mkdir"
    if isinstance(func, ast.Attribute) and func.attr in (
        "mkdtemp", "mkstemp", "NamedTemporaryFile",
    ):
        return "tempfile"
    if isinstance(func, ast.Name) and func.id in ("NamedTemporaryFile",):
        return "tempfile"
    return None


def _call_target_name(call: ast.Call) -> Optional[str]:
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


# ---------------------------------------------------------------------- #
# Per-function analysis
# ---------------------------------------------------------------------- #


class FuncUnit:
    """One scanned function/method: parent+field map restricted to ITS OWN
    control flow (nested def/lambda/class are separate FuncUnits and are
    NOT walked into here — a raise inside a nested closure does not
    execute merely because the outer function runs)."""

    __slots__ = (
        "node", "filepath", "qualname", "parents", "acquires",
        "own_raises", "own_calls", "cleanup_calls",
    )

    def __init__(self, node: ast.AST, filepath: str, qualname: str):
        self.node = node
        self.filepath = filepath
        self.qualname = qualname
        self.parents: Dict[ast.AST, Tuple[Optional[ast.AST], Optional[str]]] = {}
        self.acquires: List[Tuple[ast.AST, str]] = []
        self.own_raises: List[ast.Raise] = []
        self.own_calls: Set[str] = set()
        self.cleanup_calls: List[Tuple[int, str]] = []
        self._build(node, None, None)

    def _build(self, node: ast.AST, parent: Optional[ast.AST], field: Optional[str]):
        self.parents[node] = (parent, field)
        is_boundary = isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)
        ) and node is not self.node
        if isinstance(node, ast.Call):
            kind = _acquire_kind(node)
            if kind is not None:
                self.acquires.append((node, kind))
            tgt = _call_target_name(node)
            if tgt in ("rmdir", "rmtree", "remove", "unlink"):
                self.cleanup_calls.append((node.lineno, tgt))
            if tgt is not None:
                self.own_calls.add(tgt)
        if isinstance(node, ast.Raise) and not is_boundary:
            self.own_raises.append(node)
        if is_boundary:
            # still record it exists (for completeness) but do not descend —
            # its own body is scanned as its own FuncUnit elsewhere.
            return
        for fname, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, ast.AST):
                        self._build(item, node, fname)
            elif isinstance(value, ast.AST):
                self._build(value, node, fname)

    def _covered_by_try_finally(self, node: ast.AST) -> bool:
        """Walk node's ancestors (within this function) — True iff `node`
        sits inside the `.body` of a Try that has a non-empty `.finalbody`."""
        cur = node
        while True:
            parent, field = self.parents.get(cur, (None, None))
            if parent is None or parent is self.node:
                return False
            if isinstance(parent, ast.Try) and field == "body" and parent.finalbody:
                return True
            cur = parent

    def _in_with_context(self, node: ast.AST) -> bool:
        """True iff `node` (an acquire Call) is the context_expr of a
        `with`/`async with` item — i.e. `with open(...) as f:` — which
        guarantees __exit__ closes the handle on any exception."""
        parent, field = self.parents.get(node, (None, None))
        if isinstance(parent, ast.withitem) and field == "context_expr":
            return True
        return False

    def later_nodes(self, after: ast.AST) -> List[ast.AST]:
        """All nodes in this function's own control flow with lineno
        strictly greater than `after`'s lineno (order-only heuristic —
        NOT a real control-flow / reachability analysis; see module
        docstring's documented false-positive class)."""
        after_line = getattr(after, "lineno", 0)
        out = []
        for n in self.parents:
            ln = getattr(n, "lineno", None)
            if ln is not None and ln > after_line:
                out.append(n)
        return out


def _iter_functions(tree: ast.Module, filepath: str) -> List[FuncUnit]:
    units: List[FuncUnit] = []

    def walk(node: ast.AST, prefix: str):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qual = f"{prefix}.{child.name}" if prefix else child.name
                units.append(FuncUnit(child, filepath, qual))
                walk(child, qual)
            elif isinstance(child, ast.ClassDef):
                qual = f"{prefix}.{child.name}" if prefix else child.name
                walk(child, qual)
            else:
                walk(child, prefix)

    walk(tree, "")
    return units


# ---------------------------------------------------------------------- #
# Package-wide can_raise fixed point (Tier B)
# ---------------------------------------------------------------------- #


def _build_can_raise(all_units: List[FuncUnit]) -> Set[str]:
    by_name: Dict[str, List[FuncUnit]] = {}
    for u in all_units:
        by_name.setdefault(u.node.name, []).append(u)

    can_raise: Set[str] = set()
    for u in all_units:
        if u.own_raises:
            can_raise.add(u.node.name)

    changed = True
    while changed:
        changed = False
        for u in all_units:
            if u.node.name in can_raise:
                continue
            if u.own_calls & can_raise:
                can_raise.add(u.node.name)
                changed = True
    return can_raise


# ---------------------------------------------------------------------- #
# Scan a set of FuncUnits for the defect shape
# ---------------------------------------------------------------------- #


def scan_units(all_units: List[FuncUnit]) -> List[dict]:
    can_raise = _build_can_raise(all_units)
    findings = []
    for u in all_units:
        for acq_node, kind in u.acquires:
            if u._in_with_context(acq_node):
                continue  # context-managed — the with guarantees release
            if u._covered_by_try_finally(acq_node):
                continue  # structurally protected (see docstring caveat)
            later = u.later_nodes(acq_node)
            tier_a_hits = [
                n for n in later
                if isinstance(n, ast.Raise) and n in u.own_raises
                and not u._covered_by_try_finally(n)
            ]
            tier_b_hits = [
                n for n in later
                if isinstance(n, ast.Call)
                and _call_target_name(n) in can_raise
                and not u._covered_by_try_finally(n)
            ]
            cleanup_after = [
                (ln, name) for (ln, name) in u.cleanup_calls
                if ln > acq_node.lineno
            ]
            if not tier_a_hits and not tier_b_hits:
                continue
            findings.append({
                "file": u.filepath,
                "function": u.qualname,
                "acquire_kind": kind,
                "acquire_line": acq_node.lineno,
                "tier_a_raise_lines": sorted({n.lineno for n in tier_a_hits}),
                "tier_b_call_lines": sorted(
                    {(n.lineno, _call_target_name(n)) for n in tier_b_hits}
                ),
                "has_later_cleanup_attempt": bool(cleanup_after),
                "cleanup_attempt_detail": cleanup_after,
            })
    return findings


def scan_python_tree(root: Path) -> List[dict]:
    all_units: List[FuncUnit] = []
    files = sorted(root.rglob("*.py"))
    for f in files:
        try:
            src = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            src = f.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(src, filename=str(f))
        except SyntaxError as exc:
            print(f"SKIP (SyntaxError): {f}: {exc}", file=sys.stderr)
            continue
        rel = str(f.relative_to(REPO_ROOT))
        all_units.extend(_iter_functions(tree, rel))
    return scan_units(all_units), len(files), len(all_units)


# ---------------------------------------------------------------------- #
# Self-test: positive + negative controls (run BEFORE trusting any zero)
# ---------------------------------------------------------------------- #

_POSITIVE_CONTROL_SRC = '''
import os

def _validate_width(x):
    """mirrors _disk_block's width-validation raise, one hop from the acquire"""
    if x <= 0:
        raise ValueError("bad width")

def acquire_then_validate(path, x):
    """SAME SHAPE AS genome_save: mkdir first, validate (raise) after."""
    os.makedirs(path, exist_ok=True)
    _validate_width(x)
    return path

def acquire_then_raise_directly(path, x):
    """Tier-A case: the raise is lexically local."""
    os.makedirs(path, exist_ok=True)
    if x <= 0:
        raise ValueError("bad width, direct")
    return path
'''

_NEGATIVE_CONTROL_SRC = '''
import os
import shutil

def _validate_width(x):
    if x <= 0:
        raise ValueError("bad width")

def acquire_no_raise(path):
    """No raise reachable anywhere after the acquire — must NOT be flagged."""
    os.makedirs(path, exist_ok=True)
    return path

def validate_then_acquire(path, x):
    """Correct order: validate BEFORE acquiring — must NOT be flagged."""
    _validate_width(x)
    os.makedirs(path, exist_ok=True)
    return path

def acquire_try_finally(path, x):
    """Covering try/finally — must NOT be flagged (structural protection)."""
    try:
        os.makedirs(path, exist_ok=True)
        _validate_width(x)
    finally:
        pass
    return path

def acquire_with_open_write(path, x):
    """open() as a with-context — must NOT be flagged (handle always closes)."""
    with open(path, "w") as fh:
        fh.write("x")
        _validate_width(x)
    return path

def acquire_with_explicit_cleanup(path, x):
    """mkdir followed by validation AND an explicit rmtree on the way out —
    still flagged as an ACQUIRE-then-RAISE hit (the raise itself is not
    caught here), but tagged has_later_cleanup_attempt=True so a human
    reviewer can see the caller tried. This is deliberately A DIFFERENT
    bucket, not a "must not be flagged" case — see the .md report's
    treatment of resumable/journal writes vs true orphans."""
    os.makedirs(path, exist_ok=True)
    if x <= 0:
        shutil.rmtree(path, ignore_errors=True)
        raise ValueError("bad width, cleaned up first")
    return path
'''


_C_POSITIVE_LEAK_SRC = """\
srmech_status_t leaky_reader(const char *path, unsigned char *buf, size_t cap)
{
    srmech_file_ro_t fh;
    srmech_status_t st = srmech_plat_file_open_ro(path, &fh);
    if (st != SRMECH_OK) { return st; }
    st = do_something(&fh, buf, cap);
    if (st != SRMECH_OK) { return st; }   /* LEAK: no close_ro before this return */
    srmech_plat_file_close_ro(&fh);
    return SRMECH_OK;
}
"""

_C_NEGATIVE_SAFE_SRC = """\
srmech_status_t safe_reader(const char *path, unsigned char *buf, size_t cap)
{
    srmech_file_ro_t fh;
    srmech_status_t st = srmech_plat_file_open_ro(path, &fh);
    if (st != SRMECH_OK) { return st; }
    st = do_something(&fh, buf, cap);
    if (st != SRMECH_OK) { srmech_plat_file_close_ro(&fh); return st; }
    srmech_plat_file_close_ro(&fh);
    return SRMECH_OK;
}

srmech_status_t srmech_plat_file_open_ro(const char *path, srmech_file_ro_t *out)
{
    /* a DEFINITION line containing the acquire fn's own name + "(" —
     * must NOT be counted as a call site by the scanner. */
    return SRMECH_OK;
}
"""


def run_c_self_test() -> bool:
    print("\n=== SELF-TEST (C): positive leak + negative safe + def-line filter ===")
    import tempfile
    ok = True
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        (tdp / "leaky.c").write_text(_C_POSITIVE_LEAK_SRC, encoding="utf-8")
        (tdp / "safe.c").write_text(_C_NEGATIVE_SAFE_SRC, encoding="utf-8")
        res = scan_c_tree(tdp)
        leak_hits = [
            s for s in res["held_handle_sites"]
            if s["file"].endswith("leaky.c") and s["unsafe_early_returns"]
        ]
        safe_hits = [
            s for s in res["held_handle_sites"]
            if s["file"].endswith("safe.c") and s["unsafe_early_returns"]
        ]
        def_as_call = [
            s for s in res["held_handle_sites"] if s["file"].endswith("safe.c")
        ]
        if not leak_hits:
            print("FAIL: scanner missed the planted C leak (leaky_reader).")
            ok = False
        else:
            print("PASS: planted C leak in leaky_reader caught "
                  f"({leak_hits[0]['unsafe_early_returns']}).")
        if safe_hits:
            print(f"FAIL: false positive on safe_reader: {safe_hits}")
            ok = False
        else:
            print("PASS: safe_reader correctly clean.")
        # exactly one call-site entry should exist in safe.c (the real call
        # inside safe_reader) — the definition line must not add a second.
        if len(def_as_call) != 1:
            print(f"FAIL: definition-line filter broken — expected 1 call "
                  f"site in safe.c, got {len(def_as_call)}.")
            ok = False
        else:
            print("PASS: definition line correctly excluded from call sites.")
    print(f"=== C SELF-TEST {'PASSED' if ok else 'FAILED'} ===")
    return ok


def run_self_test() -> bool:
    print("=== SELF-TEST: positive control (must find genome_save-shaped hits) ===")
    pos_tree = ast.parse(_POSITIVE_CONTROL_SRC, filename="<positive_control>")
    pos_units = _iter_functions(pos_tree, "<positive_control>")
    pos_findings = scan_units(pos_units)
    pos_funcs_hit = {f["function"] for f in pos_findings}
    ok = True
    if "acquire_then_validate" not in pos_funcs_hit:
        print("FAIL: scanner did NOT catch the genome_save-shaped Tier-B case "
              "(acquire_then_validate) — this is exactly the false-REFUTED "
              "failure mode the brief warns about.")
        ok = False
    else:
        print("PASS: acquire_then_validate caught (Tier-B, 1-hop-via-callee).")
    if "acquire_then_raise_directly" not in pos_funcs_hit:
        print("FAIL: scanner did NOT catch the direct (Tier-A) case.")
        ok = False
    else:
        print("PASS: acquire_then_raise_directly caught (Tier-A, direct).")

    print("\n=== SELF-TEST: negative controls (must find ZERO hits) ===")
    neg_tree = ast.parse(_NEGATIVE_CONTROL_SRC, filename="<negative_control>")
    neg_units = _iter_functions(neg_tree, "<negative_control>")
    neg_findings = scan_units(neg_units)
    neg_funcs_hit = {f["function"]: f for f in neg_findings}
    for must_be_clean in (
        "acquire_no_raise", "validate_then_acquire",
        "acquire_try_finally", "acquire_with_open_write",
    ):
        if must_be_clean in neg_funcs_hit:
            print(f"FAIL: false positive on {must_be_clean} "
                  f"(scanner over-flags a safe pattern): "
                  f"{neg_funcs_hit[must_be_clean]}")
            ok = False
        else:
            print(f"PASS: {must_be_clean} correctly NOT flagged.")
    # This one SHOULD be flagged (acquire precedes a raise) but tagged
    # has_later_cleanup_attempt=True — proving the scanner distinguishes
    # "orphan" from "attempted-cleanup" rather than conflating them.
    if "acquire_with_explicit_cleanup" not in neg_funcs_hit:
        print("FAIL: acquire_with_explicit_cleanup should still be flagged "
              "(the raise site itself has no try/finally) — just tagged.")
        ok = False
    elif not neg_funcs_hit["acquire_with_explicit_cleanup"]["has_later_cleanup_attempt"]:
        print("FAIL: acquire_with_explicit_cleanup was flagged but NOT tagged "
              "has_later_cleanup_attempt=True — the cleanup-attempt detector "
              "itself is broken.")
        ok = False
    else:
        print("PASS: acquire_with_explicit_cleanup flagged AND tagged "
              "has_later_cleanup_attempt=True (orphan vs attempted-cleanup "
              "distinction works).")

    print(f"\n=== SELF-TEST {'PASSED' if ok else 'FAILED'} ===")
    return ok


# ---------------------------------------------------------------------- #
# C-side grep-based pass (PAL acquire/release pairing)
# ---------------------------------------------------------------------- #

C_ACQUIRE_RELEASE_PAIRS = {
    "srmech_plat_file_open_ro": "srmech_plat_file_close_ro",
    "srmech_plat_rstream_open": "srmech_plat_rstream_close",
    "srmech_plat_dir_open": "srmech_plat_dir_close",
}
# srmech_plat_stream_listen / srmech_plat_tcp_listen are DELIBERATELY excluded
# from the same-function open==>close pairing check: their contract is a
# CONSTRUCTOR — "bind + listen, then hand the live handle to the caller"
# (srmech_bus_serve / srmech_bus_serve_encrypted return `*out_handle = h`
# with the listener still open; the matching close lives in a SEPARATE
# teardown function, srmech_bus_server_stop, called by different code at a
# different time). v1 of this scanner included them and flagged their
# SUCCESS-path `return SRMECH_OK;` as "unsafe" — a false positive from
# applying the single-shot-read-and-close model to a long-lived-handle
# constructor. Manually verified clean instead (see the .md report):
# both srmech_bus.c call sites (lines 625, 666) release the handle
# struct on the OPEN'S OWN failure and otherwise hand off the live
# listener; srmech_mcp_sse.c:724 closes explicitly on ITS OWN failure
# (line 732) and otherwise hands off; the real close is
# srmech_bus_server_stop:704 / the mcp_sse stop path:757 — both present
# and unconditional teardown, checked by reading, not by this scanner.
C_MKDIR_FN = "srmech_plat_mkdir"

# A DEFINITION line for one of these PAL functions (return-type + name +
# open-paren on the same or a wrapped line) must NOT be counted as a CALL
# site — v1 of this scanner conflated the two (5 "call sites" for
# srmech_plat_mkdir when only 3 are real calls; the other 2 were the
# POSIX/no-filesystem definitions in srmech_platform.c itself) and is kept
# here as the documented false-REFUTED-adjacent bug this rc fixed.
_DEF_PREFIX_RE = re.compile(
    r"^(srmech_status_t|static\s+srmech_status_t|void|static\s+void|int|static\s+int)\s*$"
)


def _func_spans(lines: List[str]) -> List[Tuple[int, int, str]]:
    """(start_line, end_line, name) for every top-level C function
    DEFINITION in `lines` (1-based, inclusive), via brace-depth counting —
    the same crude-but-effective approach `tests/test_jpl_audit.py`
    (`_scan_functions`) uses for the Rule-4/Rule-5 ratchet."""
    def_pat = re.compile(
        r"^[a-zA-Z_][a-zA-Z_0-9 \t\*]+[ \t\*]([a-zA-Z_][a-zA-Z_0-9]+)\s*\("
    )
    spans = []
    n = len(lines)
    i = 0
    while i < n:
        line = lines[i]
        if line.rstrip().endswith(";"):
            i += 1
            continue
        m = def_pat.match(line)
        if m and not line.lstrip().startswith(
            ("typedef", "static const", "extern", "#")
        ):
            name = m.group(1)
            body_start = i
            while body_start < n and "{" not in lines[body_start]:
                body_start += 1
            if body_start < n:
                depth = lines[body_start].count("{") - lines[body_start].count("}")
                end = body_start
                for j in range(body_start + 1, n):
                    depth += lines[j].count("{") - lines[j].count("}")
                    if depth <= 0:
                        end = j
                        break
                spans.append((i + 1, end + 1, name))  # 1-based inclusive
        i += 1
    return spans


def _is_definition_line(line: str, fn_name: str) -> bool:
    """True iff `line` is the DEFINITION signature of `fn_name` (its return
    type precedes the name on the same logical line), not a call to it."""
    idx = line.find(fn_name)
    if idx < 0:
        return False
    before = line[:idx].rstrip()
    return bool(_DEF_PREFIX_RE.match(before)) or before.endswith((
        "srmech_status_t", "void", "int",
    ))


def scan_c_tree(root: Path) -> dict:
    """Report, per acquire primitive, every early return between an OPEN
    CALL and its matching CLOSE call, bounded to the OPEN call's OWN
    enclosing function (via brace-depth span detection) — v1 of this
    scanner used a flat 60-line lookahead with no function-boundary check
    and no definition-vs-call filter, which produced 20 "unsafe" hits
    against 6 real call sites, ALL of which close correctly on manual
    read (see the .md report's positive-control postmortem on this rc)."""
    results = {"mkdir_sites": [], "held_handle_sites": []}
    for f in sorted(root.glob("*.c")):
        text = f.read_text(encoding="utf-8")
        lines = text.split("\n")
        spans = _func_spans(lines)

        def _enclosing(lineno_1based: int) -> Optional[Tuple[int, int, str]]:
            best = None
            for s, e, name in spans:
                if s <= lineno_1based <= e and (
                    best is None or (e - s) < (best[1] - best[0])
                ):
                    best = (s, e, name)
            return best

        for i, line in enumerate(lines, 1):
            if re.search(r"\b" + C_MKDIR_FN + r"\s*\(", line):
                if _is_definition_line(line, C_MKDIR_FN):
                    continue
                enc = _enclosing(i)
                results["mkdir_sites"].append(
                    {"file": f"docs/srmech/c/src/{f.name}", "line": i,
                     "function": enc[2] if enc else None,
                     "text": line.strip()}
                )
        for open_fn, close_fn in C_ACQUIRE_RELEASE_PAIRS.items():
            for i, line in enumerate(lines, 1):
                if not re.search(r"\b" + open_fn + r"\s*\(", line):
                    continue
                if _is_definition_line(line, open_fn):
                    continue
                enc = _enclosing(i)
                end_line = enc[1] if enc else min(i + 60, len(lines))
                window_lines = list(range(i + 1, end_line + 1))
                unsafe_returns = []
                closed = False
                # The FIRST early return encountered is presumed to be the
                # open call's OWN status guard ("st = OPEN(...); if (st !=
                # SRMECH_OK) { return st; }") — nothing was acquired on that
                # path, so it needs no close, and flagging it is a false
                # positive (caught by the safe_reader C self-test above,
                # which planted exactly this shape and this rc's v1 scanner
                # failed on). Only returns AFTER that first guard count.
                first_return_seen = False
                for j in window_lines:
                    wline = lines[j - 1]
                    if re.search(r"\b" + close_fn + r"\s*\(", wline):
                        closed = True
                    if "return" in wline:
                        if not first_return_seen:
                            first_return_seen = True
                        elif not closed:
                            unsafe_returns.append((j, wline.strip()))
                results["held_handle_sites"].append({
                    "file": f"docs/srmech/c/src/{f.name}", "open_line": i,
                    "function": enc[2] if enc else None,
                    "open_fn": open_fn, "close_fn": close_fn,
                    "function_end_line": end_line,
                    "unsafe_early_returns": unsafe_returns,
                })
    return results


# ---------------------------------------------------------------------- #
# Main
# ---------------------------------------------------------------------- #


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--scan", action="store_true")
    args = ap.parse_args()

    if not args.self_test and not args.scan:
        args.self_test = True
        args.scan = True

    if args.self_test:
        ok = run_self_test()
        ok_c = run_c_self_test()
        ok = ok and ok_c
        if not ok:
            print("Refusing to trust the real scan until self-test passes.",
                  file=sys.stderr)
            sys.exit(1)

    if args.scan:
        print(f"\n=== SCANNING Python tree: {PY_SRC_ROOT} ===")
        py_findings, n_files, n_funcs = scan_python_tree(PY_SRC_ROOT)
        print(f"{n_files} .py files, {n_funcs} functions scanned; "
              f"{len(py_findings)} candidate hits")

        print(f"\n=== SCANNING C tree: {C_SRC_ROOT} ===")
        c_findings = scan_c_tree(C_SRC_ROOT)
        n_mkdir = len(c_findings["mkdir_sites"])
        n_unsafe = sum(
            1 for s in c_findings["held_handle_sites"] if s["unsafe_early_returns"]
        )
        print(f"{n_mkdir} srmech_plat_mkdir call sites; "
              f"{len(c_findings['held_handle_sites'])} held-handle open sites, "
              f"{n_unsafe} with an UNSAFE early return (open-without-close)")

        with NDJSON_OUT.open("w", encoding="utf-8", newline="\n") as out:
            out.write(json.dumps({
                "record": "meta",
                "py_files_scanned": n_files,
                "py_functions_scanned": n_funcs,
                "py_findings": len(py_findings),
                "c_mkdir_sites": n_mkdir,
                "c_held_handle_sites": len(c_findings["held_handle_sites"]),
                "c_unsafe_early_returns": n_unsafe,
            }, sort_keys=True) + "\n")
            for f in py_findings:
                out.write(json.dumps({"record": "py_finding", **f},
                                      sort_keys=True) + "\n")
            for s in c_findings["mkdir_sites"]:
                out.write(json.dumps({"record": "c_mkdir_site", **s},
                                      sort_keys=True) + "\n")
            for s in c_findings["held_handle_sites"]:
                out.write(json.dumps({"record": "c_held_handle_site", **s},
                                      sort_keys=True) + "\n")
        print(f"\nWrote {NDJSON_OUT}")


if __name__ == "__main__":
    main()
