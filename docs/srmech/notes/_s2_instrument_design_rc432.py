#!/usr/bin/env python3
"""`#T1132` rc432 — instrument DESIGN + bite-test for the acquire-before-validate class.

TWO instruments, because the two projections need different machinery (rc431
audit verdict, `docs/srmech/notes/_pal_resource_cleanup_audit.md` Q5):

  * **C** — brace-bounded, uniform idiom, realistically gate-able as STRICT ZERO.
    Two rules, because the held-handle rule alone is blind to the one genuine
    C-side instance:
      - R11  held-handle acquire/release symmetry  (open_ro / rstream / dir)
      - R12  created-node rollback                 (>=2 sequential mkdir, no undo)
  * **Python** — branchier, exception-heavy; NOT strict-zero-gate-able. A
    SOUND-implication structural predicate plus a reasoned allowlist and a
    down-only CEIL on the residual (rc415 / rc423 precedent).

This script is the PROTOTYPE of both predicates and their bite-tests. It does
NOT edit package source. It emits `_s2_instrument_design_rc432.ndjson`.

DISCIPLINE
----------
Every falsifier is pre-registered (printed) BEFORE it runs. Every scanner is
validated with a PLANTED POSITIVE and a PLANTED NEGATIVE control before any
live zero is trusted — the rc431 audit's own scanner was wrong three times
before it was right. No `abs()`, no stdlib math/fractions/decimal, no numpy.
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent          # docs/srmech/notes
_SRMECH = _HERE.parent                            # docs/srmech
_C_SRC = _SRMECH / "c" / "src"
_PY_PKG = _SRMECH / "python" / "srmech"
_REPO = _SRMECH.parent.parent                     # repo root

_RECORDS: list[dict] = []


def emit(rec: dict) -> None:
    _RECORDS.append(rec)


# ══════════════════════════════════════════════════════════════════════
# PRE-REGISTERED FALSIFIERS  (printed before anything runs)
# ══════════════════════════════════════════════════════════════════════

FALSIFIERS = [
    ("F1", "C-R11 planted-POSITIVE control: a leaked handle (acquire, early "
           "return, no close) MUST be reported. If it is not, R11 cannot fail "
           "and is not a measurement."),
    ("F2", "C-R11 planted-NEGATIVE controls: all THREE legitimate shapes — "
           "(a) guard-return-before-acquisition, (b) inline-release-on-guard, "
           "(c) capture-flags/release-once/then-branch — MUST report clean. "
           "Any hit here is a false positive and the rule is mis-scoped."),
    ("F3", "C-R11 live scan of c/src: PREDICTED 0 unsafe across all held-handle "
           "sites (rc431 measured 0/5). A non-zero is a real finding; a zero is "
           "only trustworthy because F1 passed."),
    ("F4", "C-R12 planted controls both ways: a 2-mkdir-no-rollback function "
           "MUST be reported; a 2-mkdir-WITH-rollback function MUST NOT."),
    ("F5", "C-R12 live scan: PREDICTED exactly 1 function (rcut_setup, "
           "srmech_laplacian.c). If R12 returns 0 the scanner is broken, "
           "because the rc431 audit read that site by hand."),
    ("F6", "PY-P planted controls both ways: an unowned top-level acquisition "
           "with a lexically-later raise MUST be reported; the same acquisition "
           "inside `with`/`try-finally`, and one with NO later raise, MUST NOT."),
    ("F7", "PY-P live scan of srmech/: population is UNKNOWN in advance. "
           "Predicted NON-ZERO and predicted to include genome_save:8980 — if "
           "the seed defect is NOT in the population the predicate is aimed "
           "at the wrong class."),
    ("F8", "SEED-COVERAGE: would either gate, seeded at the rc431 tree, have "
           "FAILED on genome_save's mkdir-before-validate? Predicted NO for "
           "both, for two different reasons. A gate that misses its own "
           "motivating case must say so."),
    ("F9", "C-R11/R12 vs the SEED: does the C side even exhibit the seed shape? "
           "PREDICTED no — rc431 measured 0 `srmech_plat_mkdir` calls in "
           "srmech_genome.c. Re-measured here, not inherited."),
]


def preregister() -> None:
    print("=" * 72)
    print("PRE-REGISTERED FALSIFIERS  (`#T1132` rc432 instrument design)")
    print("=" * 72)
    for tag, text in FALSIFIERS:
        print(f"  {tag}: {text}")
    print("=" * 72)
    emit({"record": "prereg", "falsifiers": [{"id": t, "claim": c}
                                             for t, c in FALSIFIERS]})


# ══════════════════════════════════════════════════════════════════════
# C SCANNER — shared function-span detection
# (same algorithm as tests/test_jpl_audit.py::_scan_functions, but the
#  span is RETURNED so the rules can bound their windows to the function)
# ══════════════════════════════════════════════════════════════════════

_C_DEF_PAT = re.compile(
    r"^[a-zA-Z_][a-zA-Z_0-9 \t\*]+[ \t\*]([a-zA-Z_][a-zA-Z_0-9]+)\s*\("
)


def c_function_spans(lines: list[str]) -> list[tuple[str, int, int]]:
    """`(name, body_open_idx, end_idx)` per function. 0-based, inclusive end.

    Brace-depth bounded, exactly like the JPL ratchet's scanner — this is the
    shape a new rule must match, so it reuses it rather than inventing one.
    """
    starts: list[tuple[str, int]] = []
    for i, line in enumerate(lines):
        if line.rstrip().endswith(";"):
            continue
        m = _C_DEF_PAT.match(line)
        if m is None:
            continue
        if line.lstrip().startswith(("typedef", "static const", "extern", "#")):
            continue
        for look in range(i, min(i + 10, len(lines))):
            if "{" in lines[look] and not lines[look].lstrip().startswith("/*"):
                starts.append((m.group(1), i))
                break

    out: list[tuple[str, int, int]] = []
    for name, start_idx in starts:
        body_start = start_idx
        while body_start < len(lines) and "{" not in lines[body_start]:
            body_start += 1
        if body_start >= len(lines):
            continue
        depth = lines[body_start].count("{") - lines[body_start].count("}")
        end_idx = body_start
        for j in range(body_start + 1, len(lines)):
            depth += lines[j].count("{") - lines[j].count("}")
            if depth == 0:
                end_idx = j
                break
        out.append((name, body_start, end_idx))
    return out


def _strip_c_comments(text: str) -> str:
    """Blank the comments but PRESERVE LINE NUMBERING.

    The JPL ratchet's Rules 1/3 delete comments outright because they only
    ``findall`` — they never report a line. A rule that reports a SITE cannot
    do that: the naive `re.sub(..., "")` collapses every multi-line block
    comment and shifts every subsequent line number. Measured here: it put
    ``rcut_setup``'s mkdir sequence at 2398/2400/2402 against a hand-read
    ground truth of 2760/2762/2764 — a 362-line error, in a scanner whose
    planted controls were all green. Newline-preserving substitution fixes it.
    """
    def _blank(m: re.Match) -> str:
        return "\n" * m.group(0).count("\n")

    no_block = re.sub(r"/\*.*?\*/", _blank, text, flags=re.DOTALL)
    return re.sub(r"//.*$", "", no_block, flags=re.MULTILINE)


def _depths(lines: list[str], body_open: int, end: int) -> dict[int, int]:
    """Brace depth AT THE START of each line, relative to the function body."""
    d = {}
    cur = 0
    for i in range(body_open, end + 1):
        d[i] = cur
        cur += lines[i].count("{") - lines[i].count("}")
    return d


# ── C RULE 11: held-handle acquire/release symmetry ───────────────────

#: Acquire -> release. Only the HELD-handle PAL primitives: a handle that
#: lives across statements and must be closed in the SAME function.
R11_PAIRS = {
    "srmech_plat_file_open_ro": "srmech_plat_file_close_ro",
    "srmech_plat_rstream_open": "srmech_plat_rstream_close",
    "srmech_plat_dir_open": "srmech_plat_dir_close",
}

#: CONSTRUCTOR-SHAPED acquires — deliberately OUT OF SCOPE for R11, with the
#: reason stated, not merely listed. Their documented contract is "bind, then
#: hand the live handle to the caller"; the close lives in a separate teardown
#: function (srmech_bus_server_stop / srmech_mcp_sse_stop). A same-function
#: close check would be WRONG here, not merely noisy — it would demand the
#: function break its own contract. This is a different rule (handle reaches an
#: out-param / struct field that a documented teardown closes), not this one.
R11_HANDOFF_ACQUIRES = {
    "srmech_plat_stream_listen",
    "srmech_plat_stream_connect",
    "srmech_plat_tcp_listen",
    "srmech_plat_tcp_connect",
    "srmech_plat_stream_accept",
    "srmech_plat_tcp_accept",
}

#: How far past an acquire the acquire's OWN status guard may sit. The guard
#: `if (st != SRMECH_OK) { return st; }` releases nothing because nothing was
#: acquired. Bounded (not "the first return, wherever it is") so the exemption
#: cannot silently swallow a genuine leak ten lines downstream.
R11_OWN_GUARD_WINDOW = 4


def c_rule11(path_label: str, text: str) -> list[dict]:
    """Every held-handle acquire must be released on EVERY exit of its own
    enclosing function. Returns the UNSAFE exits."""
    lines = _strip_c_comments(text).split("\n")
    findings: list[dict] = []
    for name, body_open, end in c_function_spans(lines):
        depth = _depths(lines, body_open, end)
        for acq, rel in R11_PAIRS.items():
            for i in range(body_open, end + 1):
                if acq not in lines[i]:
                    continue
                # the acquire's OWN definition line is not a call site
                if re.search(r"\b\w+[ \t\*]+" + re.escape(acq) + r"\s*\(", lines[i]):
                    continue
                if acq == name:
                    continue
                released_unconditionally = False
                seen_return = 0
                for j in range(i + 1, end + 1):
                    if rel in lines[j] and depth[j] == depth[i]:
                        released_unconditionally = True
                    if not re.search(r"\breturn\b", lines[j]):
                        continue
                    seen_return += 1
                    if released_unconditionally:
                        continue
                    # shape (a): the acquire's own status guard
                    if seen_return == 1 and (j - i) <= R11_OWN_GUARD_WINDOW:
                        continue
                    # shape (b): release on the same line, or anywhere inside
                    # the return's own innermost enclosing block
                    if rel in lines[j]:
                        continue
                    d_r = depth[j]
                    k = j - 1
                    found = False
                    while k > i and depth.get(k, 0) >= d_r:
                        if rel in lines[k]:
                            found = True
                            break
                        k -= 1
                    if found:
                        continue
                    findings.append({
                        "file": path_label, "function": name,
                        "acquire": acq, "acquire_line": i + 1,
                        "release": rel, "unsafe_return_line": j + 1,
                        "text": lines[j].strip(),
                    })
    return findings


# ── C RULE 12: created-node rollback ──────────────────────────────────

R12_CREATE = "srmech_plat_mkdir"
R12_UNDO = ("srmech_plat_file_remove", "srmech_plat_dir_remove", "rmdir")


def c_rule12(path_label: str, text: str) -> list[dict]:
    """A function that creates 2+ filesystem nodes must undo the earlier ones
    if a later create fails. Reports functions where it does not."""
    lines = _strip_c_comments(text).split("\n")
    findings: list[dict] = []
    for name, body_open, end in c_function_spans(lines):
        creates = []
        for i in range(body_open, end + 1):
            if R12_CREATE not in lines[i]:
                continue
            if re.search(r"\b\w+[ \t\*]+" + re.escape(R12_CREATE) + r"\s*\(",
                         lines[i]):
                continue
            if R12_CREATE == name:
                continue
            creates.append(i)
        if len(creates) < 2:
            continue
        # from the SECOND create onward, any return must be preceded by an undo
        unsafe = []
        for c_idx in creates[1:]:
            for j in range(c_idx + 1, end + 1):
                if not re.search(r"\breturn\b", lines[j]):
                    continue
                window = "\n".join(lines[c_idx:j + 1])
                if any(u in window for u in R12_UNDO):
                    continue
                unsafe.append(j + 1)
                break
        if unsafe:
            findings.append({
                "file": path_label, "function": name,
                "create_lines": [c + 1 for c in creates],
                "unsafe_return_lines": unsafe,
            })
    return findings


# ── C self-test: planted controls ─────────────────────────────────────

_C_CONTROL_LEAK = """
srmech_status_t planted_leak(const char *path)
{
    srmech_plat_rstream_t rs;
    srmech_status_t st = srmech_plat_rstream_open(path, &rs);
    if (st != SRMECH_OK) { return st; }
    size_t n = 0u;
    st = srmech_plat_rstream_read(&rs, buf, 16u, &n);
    if (st != SRMECH_OK) { return st; }
    srmech_plat_rstream_close(&rs);
    return SRMECH_OK;
}
"""

_C_CONTROL_SHAPE_A = """
srmech_status_t planted_shape_a(const char *path)
{
    srmech_plat_dir_t d;
    srmech_status_t st = srmech_plat_dir_open(path, &d);
    if (st != SRMECH_OK) { return st; }
    srmech_plat_dir_close(&d);
    return SRMECH_OK;
}
"""

_C_CONTROL_SHAPE_B = """
srmech_status_t planted_shape_b(const char *path)
{
    srmech_plat_dir_t d;
    srmech_status_t st = srmech_plat_dir_open(path, &d);
    if (st != SRMECH_OK) { return st; }
    st = do_work(&d);
    if (st != SRMECH_OK) { srmech_plat_dir_close(&d); return st; }
    st = do_more(&d);
    if (st != SRMECH_OK) {
        srmech_plat_dir_close(&d);
        return st;
    }
    srmech_plat_dir_close(&d);
    return SRMECH_OK;
}
"""

_C_CONTROL_SHAPE_C = """
srmech_status_t planted_shape_c(const char *path)
{
    srmech_plat_rstream_t rs;
    srmech_status_t st = srmech_plat_rstream_open(path, &rs);
    if (st != SRMECH_OK) { return st; }
    int err = do_scan(&rs);
    srmech_plat_rstream_close(&rs);
    if (err) { return SRMECH_ERR_IO; }
    return SRMECH_OK;
}
"""

_C_CONTROL_MKDIR_BAD = """
srmech_status_t planted_mkdir_bad(const char *a, const char *b)
{
    srmech_status_t st = srmech_plat_mkdir(a);
    if (st != SRMECH_OK) { return st; }
    st = srmech_plat_mkdir(b);
    if (st != SRMECH_OK) { return st; }
    return SRMECH_OK;
}
"""

_C_CONTROL_MKDIR_GOOD = """
srmech_status_t planted_mkdir_good(const char *a, const char *b)
{
    srmech_status_t st = srmech_plat_mkdir(a);
    if (st != SRMECH_OK) { return st; }
    st = srmech_plat_mkdir(b);
    if (st != SRMECH_OK) { srmech_plat_file_remove(a); return st; }
    return SRMECH_OK;
}
"""


def c_self_test() -> bool:
    ok = True
    cases = [
        ("F1", "planted_leak", _C_CONTROL_LEAK, c_rule11, True),
        ("F2a", "shape_a_guard_before_acquire", _C_CONTROL_SHAPE_A, c_rule11, False),
        ("F2b", "shape_b_inline_release_on_guard", _C_CONTROL_SHAPE_B, c_rule11, False),
        ("F2c", "shape_c_flags_release_once_branch", _C_CONTROL_SHAPE_C, c_rule11, False),
        ("F4a", "planted_mkdir_no_rollback", _C_CONTROL_MKDIR_BAD, c_rule12, True),
        ("F4b", "planted_mkdir_with_rollback", _C_CONTROL_MKDIR_GOOD, c_rule12, False),
    ]
    print("\n-- C SCANNER SELF-TEST (planted controls) --")
    for tag, label, src, fn, expect_hit in cases:
        hits = fn(f"<control:{label}>", src)
        got = len(hits) > 0
        verdict = "PASS" if got == expect_hit else "FAIL"
        if verdict == "FAIL":
            ok = False
        print(f"  [{verdict}] {tag} {label}: expect_hit={expect_hit} "
              f"got={len(hits)} hits")
        emit({"record": "c_control", "falsifier": tag, "control": label,
              "expect_hit": expect_hit, "n_hits": len(hits),
              "verdict": verdict, "hits": hits})
    return ok


def c_live_scan() -> tuple[list[dict], list[dict]]:
    r11: list[dict] = []
    r12: list[dict] = []
    n_files = 0
    for f in sorted(_C_SRC.glob("*.c")):
        n_files += 1
        text = f.read_text(encoding="utf-8", errors="replace")
        r11 += c_rule11(f.name, text)
        r12 += c_rule12(f.name, text)
    print(f"\n-- C LIVE SCAN ({n_files} .c files) --")
    print(f"  R11 unsafe held-handle exits : {len(r11)}")
    for h in r11:
        print(f"      {h['file']}::{h['function']} acquire@{h['acquire_line']} "
              f"unsafe return@{h['unsafe_return_line']}")
    print(f"  R12 created-node no-rollback : {len(r12)}")
    for h in r12:
        print(f"      {h['file']}::{h['function']} creates@{h['create_lines']} "
              f"unsafe return@{h['unsafe_return_lines']}")
    emit({"record": "c_live_scan", "n_c_files": n_files,
          "r11_unsafe": len(r11), "r12_unsafe": len(r12),
          "r11_findings": r11, "r12_findings": r12})
    return r11, r12


# ══════════════════════════════════════════════════════════════════════
# PYTHON SCANNER — the bounded, SOUND-implication structural predicate
# ══════════════════════════════════════════════════════════════════════
#
# THE PREDICATE, stated so it can be falsified:
#
#   An acquisition site is UNOWNED-BEFORE-A-RAISE when ALL of:
#     (1) it is a CALL to a resource-acquiring primitive
#         (Path.mkdir / os.makedirs / open(...,write-mode) / tempfile.mkdtemp
#          / NamedTemporaryFile), AND
#     (2) it is a DIRECT statement of a function body — depth 0, not nested in
#         any if / for / while / try / with, AND
#     (3) some `raise` or `assert` statement appears LEXICALLY LATER in the
#         same function, excluding nested def / lambda / class bodies.
#
# WHY (2) IS THE WHOLE DESIGN, AND WHY THIS IS NOT THE rc431 SCANNER'S
# LINE-ORDER HEURISTIC
# -------------------------------------------------------------------------
# rc431's scanner asked "is there a raise after this line?", which is a
# REACHABILITY guess and was wrong 4 times in 31 — every one of those four was
# an acquisition nested inside a branch, with the raise in a mutually exclusive
# sibling branch (`genome_import:11627`, `genome_pack:11829`,
# `genome_partition:7340`, `genome_from_graph:7556`).
#
# Requiring the acquisition to be a TOP-LEVEL statement of the function body
# converts the guess into a SOUND IMPLICATION. Top-level statements execute in
# source order, so any statement lexically after a top-level statement — at any
# nesting depth inside a LATER top-level statement — can only be reached once
# that earlier top-level statement has completed. Therefore:
#
#     IF that later raise fires, the resource was ALREADY acquired.
#
# That is not a heuristic about whether the raise is reachable; it is a proof
# about ordering GIVEN that it fires. The residual uncertainty is only "is the
# raise reachable at all" — and an unreachable `raise` in shipped code is dead
# code, a different defect. Condition (2) is therefore what buys the soundness,
# and it is also what makes the predicate INCOMPLETE (see the false-NEGATIVE
# class below). That trade is the honest one: a gate may under-report, it may
# not mis-accuse.

PY_ACQUIRE_ATTRS = {"mkdir", "makedirs", "mkdtemp", "NamedTemporaryFile",
                    "TemporaryDirectory"}
PY_WRITE_MODES = ("w", "x", "a", "+")


def _is_acquire_call(node: ast.AST) -> str | None:
    if not isinstance(node, ast.Call):
        return None
    fn = node.func
    if isinstance(fn, ast.Attribute) and fn.attr in PY_ACQUIRE_ATTRS:
        return fn.attr
    if isinstance(fn, ast.Name) and fn.id in PY_ACQUIRE_ATTRS:
        return fn.id
    # open(path, "wb") and friends — write modes only; a read open holds a
    # handle but creates nothing, and the `with` check below covers it.
    is_open = ((isinstance(fn, ast.Name) and fn.id == "open") or
               (isinstance(fn, ast.Attribute) and fn.attr == "open"))
    if is_open:
        mode = None
        if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
            mode = node.args[1].value
        for kw in node.keywords:
            if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                mode = kw.value.value
        if isinstance(mode, str) and any(c in mode for c in PY_WRITE_MODES):
            return "open_write"
    return None


def _later_raise_lines(body: list[ast.stmt], after_lineno: int) -> list[int]:
    """`raise` / `assert` linenos lexically after `after_lineno`, INLINE only —
    nested def / async def / lambda / class bodies are NOT inline and are
    excluded (a closure's raise does not fire here)."""
    out: list[int] = []

    def walk(nodes) -> None:
        for n in nodes:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                              ast.ClassDef, ast.Lambda)):
                continue
            if isinstance(n, (ast.Raise, ast.Assert)) and n.lineno > after_lineno:
                out.append(n.lineno)
            walk(list(ast.iter_child_nodes(n)))

    walk(body)
    return sorted(set(out))


def _module_level_raisers(tree: ast.Module) -> dict[str, int]:
    """`{name: first_inline_raise_lineno}` for module-level `def`s in THIS file
    whose own body contains an inline `raise`/`assert`.

    TIER 1 name resolution, deliberately narrowed to EXACTLY this: a BARE-NAME
    call resolving to a `def` at module level in the SAME file. rc431's scanner
    resolved bare names package-wide and named that cross-contamination as its
    own documented false-positive class; single-module exact-name resolution has
    no such class — the only way to be wrong is a module-local name shadowed by
    an import of the same name, which is checkable and does not occur here.
    """
    out: dict[str, int] = {}
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        r = _later_raise_lines(node.body, 0)
        if r:
            out[node.name] = r[0]
    return out


def _later_bare_calls(body: list[ast.stmt], after_lineno: int) -> list[tuple[str, int]]:
    """`(name, lineno)` for bare-Name calls lexically after `after_lineno`,
    inline only (nested def / lambda / class bodies excluded)."""
    out: list[tuple[str, int]] = []

    def walk(nodes) -> None:
        for n in nodes:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                              ast.ClassDef, ast.Lambda)):
                continue
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                    and n.lineno > after_lineno):
                out.append((n.func.id, n.lineno))
            walk(list(ast.iter_child_nodes(n)))

    walk(body)
    return sorted(set(out), key=lambda t: t[1])


def py_scan_source(label: str, src: str, tier: int = 0) -> list[dict]:
    """`tier=0` — inline raises only (SOUND, incomplete).
    `tier=1` — additionally, a later bare-Name call to a same-module `def`
    that itself raises inline (ONE hop, no transitive closure)."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    raisers = _module_level_raisers(tree) if tier >= 1 else {}
    findings: list[dict] = []

    def visit_fn(fn: ast.AST, qual: str) -> None:
        body = list(getattr(fn, "body", []))
        if tier >= 2:
            # TIER 2 — the sound `try`-HEAD extension. An acquisition that is the
            # FIRST simple statement of a top-level `try` body with NO `finally`
            # keeps the ordering proof: nothing precedes it inside the try, so no
            # handler can be entered without it having run. (An acquisition
            # ANYWHERE ELSE in a try body breaks it — a handler reached from an
            # earlier statement fires with nothing acquired.) `try/finally` stays
            # OWNED and out of scope. This is the shape `genome_import` uses.
            for stmt in list(body):
                if (isinstance(stmt, ast.Try) and not stmt.finalbody
                        and stmt.body and isinstance(
                            stmt.body[0], (ast.Expr, ast.Assign, ast.AnnAssign,
                                           ast.AugAssign, ast.Return))):
                    body.append(stmt.body[0])
        for stmt in body:                       # DEPTH 0 ONLY — condition (2)
            # SIMPLE top-level statements only. A COMPOUND statement (if / for /
            # while / with / try / match) introduces a branch or a scope, and an
            # acquisition inside one is exactly the case the ordering proof does
            # NOT cover — walking into it is how rc431's scanner produced its
            # four false positives. Caught here by planted control F6e, which
            # this predicate failed on its first run.
            if not isinstance(stmt, (ast.Expr, ast.Assign, ast.AnnAssign,
                                     ast.AugAssign, ast.Return)):
                continue
            for node in ast.walk(stmt):
                kind = _is_acquire_call(node)
                if kind is None:
                    continue
                raises = _later_raise_lines(body, node.lineno)
                via = "inline" if raises else None
                hops: list[list] = []
                if not raises and tier >= 1:
                    for cname, cline in _later_bare_calls(body, node.lineno):
                        if cname in raisers:
                            hops.append([cname, cline, raisers[cname]])
                    if hops:
                        via = "callee"
                if via is None:
                    continue
                findings.append({
                    "file": label, "function": qual,
                    "acquire_kind": kind, "acquire_line": node.lineno,
                    "via": via,
                    "later_raise_lines": raises[:6],
                    "n_later_raises": len(raises),
                    "callee_hops": hops[:6],
                })

    def walk_defs(node: ast.AST, prefix: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qual = f"{prefix}{child.name}"
                visit_fn(child, qual)
                walk_defs(child, f"{qual}.")
            elif isinstance(child, ast.ClassDef):
                walk_defs(child, f"{prefix}{child.name}.")

    walk_defs(tree, "")
    return findings


# ── Python self-test: planted controls ────────────────────────────────

_PY_CTRL_POS = '''
def planted_unowned():
    path.mkdir(parents=True, exist_ok=True)
    if bad:
        raise ValueError("rejected after the directory already exists")
    return path
'''

_PY_CTRL_NEG_WITH = '''
def planted_owned_with():
    with owned_dir(path) as d:
        d.mkdir(parents=True, exist_ok=True)
        if bad:
            raise ValueError("scope releases it")
    return path
'''

_PY_CTRL_NEG_TRYFIN = '''
def planted_owned_tryfinally():
    try:
        path.mkdir(parents=True, exist_ok=True)
        if bad:
            raise ValueError("finally releases it")
    finally:
        cleanup(path)
    return path
'''

_PY_CTRL_NEG_NORAISE = '''
def planted_no_later_raise():
    if bad:
        raise ValueError("raise is BEFORE the acquisition")
    path.mkdir(parents=True, exist_ok=True)
    return path
'''

_PY_CTRL_NEG_BRANCHED = '''
def planted_branched_acquire():
    if not body.exists():
        path.mkdir(parents=True, exist_ok=True)
        return path
    if bad:
        raise ValueError("mutually exclusive sibling branch")
    return path
'''

_PY_CTRL_NEG_CLOSURE = '''
def planted_closure_raise():
    path.mkdir(parents=True, exist_ok=True)
    def _inner():
        raise ValueError("a closure's raise does not fire here")
    return _inner
'''


_PY_CTRL_T1_POS = '''
def _validator(x):
    if x is None:
        raise ValueError("rejected")

def planted_callee_raise():
    path.mkdir(parents=True, exist_ok=True)
    _validator(x)
    return path
'''

_PY_CTRL_T1_NEG_CLEAN = '''
def _harmless(x):
    return x + 1

def planted_callee_no_raise():
    path.mkdir(parents=True, exist_ok=True)
    _harmless(x)
    return path
'''

_PY_CTRL_T1_NEG_ATTR = '''
def _validator(x):
    if x is None:
        raise ValueError("rejected")

def planted_attribute_call_does_not_resolve():
    path.mkdir(parents=True, exist_ok=True)
    other._validator(x)
    return path
'''


def py_self_test() -> bool:
    ok = True
    cases = [
        ("F6a", "unowned_toplevel_then_raise", _PY_CTRL_POS, 0, True),
        ("F6b", "owned_by_with", _PY_CTRL_NEG_WITH, 0, False),
        ("F6c", "owned_by_try_finally", _PY_CTRL_NEG_TRYFIN, 0, False),
        ("F6d", "raise_before_acquire", _PY_CTRL_NEG_NORAISE, 0, False),
        ("F6e", "branched_acquire_sibling_raise", _PY_CTRL_NEG_BRANCHED, 0, False),
        ("F6f", "closure_raise_not_inline", _PY_CTRL_NEG_CLOSURE, 0, False),
        ("F6g", "T0_blind_to_callee_raise", _PY_CTRL_T1_POS, 0, False),
        ("F6h", "T1_sees_callee_raise", _PY_CTRL_T1_POS, 1, True),
        ("F6i", "T1_callee_does_not_raise", _PY_CTRL_T1_NEG_CLEAN, 1, False),
        ("F6j", "T1_attribute_call_unresolved", _PY_CTRL_T1_NEG_ATTR, 1, False),
    ]
    print("\n-- PYTHON SCANNER SELF-TEST (planted controls) --")
    for tag, label, src, tier, expect_hit in cases:
        hits = py_scan_source(f"<control:{label}>", src, tier=tier)
        got = len(hits) > 0
        verdict = "PASS" if got == expect_hit else "FAIL"
        if verdict == "FAIL":
            ok = False
        print(f"  [{verdict}] {tag} T{tier} {label}: expect_hit={expect_hit} "
              f"got={len(hits)} hits")
        emit({"record": "py_control", "falsifier": tag, "control": label,
              "tier": tier, "expect_hit": expect_hit, "n_hits": len(hits),
              "verdict": verdict, "hits": hits})
    return ok


def py_live_scan(tier: int) -> list[dict]:
    findings: list[dict] = []
    n_files = 0
    for f in sorted(_PY_PKG.rglob("*.py")):
        n_files += 1
        rel = f.relative_to(_PY_PKG.parent).as_posix()
        findings += py_scan_source(rel, f.read_text(encoding="utf-8",
                                                    errors="replace"), tier=tier)
    print(f"\n-- PYTHON LIVE SCAN, TIER {tier} ({n_files} files under srmech/) --")
    print(f"  UNOWNED-BEFORE-A-RAISE sites: {len(findings)}")
    for h in findings:
        detail = (f"raises {h['later_raise_lines']}" if h["via"] == "inline"
                  else f"via callee {h['callee_hops'][0][0]}()")
        print(f"      [{h['via']:6s}] {h['file']}::{h['function']} "
              f"{h['acquire_kind']}@{h['acquire_line']} -> {detail}")
    emit({"record": "py_live_scan", "tier": tier, "n_py_files": n_files,
          "n_findings": len(findings), "findings": findings})
    return findings


# ══════════════════════════════════════════════════════════════════════
# EXTERNAL RECALL ORACLE — rc431's MANUAL triage
# ══════════════════════════════════════════════════════════════════════
#
# Planted controls prove a scanner CAN fire and CAN stay quiet. They cannot
# prove it fires on the REAL class, because I wrote both the control and the
# predicate — a same-author pair can be consistently wrong. rc431's triage is
# an independent, hand-read verdict on 31 sites, so it is the one oracle in
# reach that this session did not author. Recall and precision are measured
# against it.

#: rc431 CONFIRMED — every LINE its manual triage confirmed, not one row per
#: function. `recursive_cut` and the `genome_register_attested` inner loop each
#: confirm three lines; collapsing them to one would flatter recall.
ORACLE_TRUE = [
    ("srmech/biology/genome.py", "genome_save", 8980, "HIGH"),
    ("srmech/biology/genome.py", "genome_import", 11600, "HIGH"),
    ("srmech/biology/genome.py", "genome_explode", 11680, "HIGH"),
    ("srmech/biology/genome.py", "genome_register_attested", 11927, "HIGH"),
    ("srmech/mcp/_mcpb.py", "pack_mcpb", 318, "HIGH"),
    ("srmech/amsc/format.py", "write_ndjson", 373, "MEDIUM"),
    ("srmech/math/laplacian.py", "recursive_cut", 7200, "MEDIUM"),
    ("srmech/math/laplacian.py", "recursive_cut", 7203, "MEDIUM"),
    ("srmech/math/laplacian.py", "recursive_cut", 7204, "MEDIUM"),
    ("srmech/biology/genome.py", "genome_register_attested", 11941, "MEDIUM"),
    ("srmech/biology/genome.py", "genome_register_attested", 11942, "MEDIUM"),
    ("srmech/biology/genome.py", "genome_register_attested", 11953, "MEDIUM"),
]

#: rc431 REFUTED (its scanner's own false positives) + BENIGN-by-contract.
#: `genome_pack@11829` is marked DISPUTED, not REFUTED: rc431 refuted it for
#: CALLER-INPUT validation and was right about that — the per-bundle loop runs
#: first. But `_read_chr()` is called AFTER the mkdir (line 11838, inside the
#: return expression) and can raise on IO, which orphans `dest` exactly as the
#: class describes. The disagreement is a class-width difference, not an error:
#: this predicate's class is "orphaned by ANY later raise", rc431's HIGH class
#: was "orphaned by later INPUT validation". Recorded as its own tier so the
#: precision number is not quietly improved by relabelling a real hit.
ORACLE_FALSE = [
    ("srmech/biology/genome.py", "genome_import", 11627, "REFUTED"),
    ("srmech/biology/genome.py", "genome_partition", 7341, "REFUTED"),
    ("srmech/biology/genome.py", "genome_from_graph", 7557, "REFUTED"),
    ("srmech/introspect/_writer.py", "Writer.enter", 165, "REFUTED"),
    ("srmech/bus/_transport.py", "UDSTransport.bind", 211, "BENIGN"),
    ("srmech/bus/_transport.py", "TCPLoopbackTransport.bind", 312, "BENIGN"),
    ("srmech/bus/_transport.py", "NamedPipeTransport.bind", 682, "BENIGN"),
]

ORACLE_DISPUTED = [
    ("srmech/biology/genome.py", "genome_pack", 11829, "DISPUTED-WEAK"),
]


def oracle_check(tier: int, findings: list[dict]) -> dict:
    got = {(h["file"], h["acquire_line"]) for h in findings}
    hit_true = [r for r in ORACLE_TRUE if (r[0], r[2]) in got]
    miss_true = [r for r in ORACLE_TRUE if (r[0], r[2]) not in got]
    hit_false = [r for r in ORACLE_FALSE if (r[0], r[2]) in got]
    hit_disp = [r for r in ORACLE_DISPUTED if (r[0], r[2]) in got]
    known = {(r[0], r[2]) for r in ORACLE_TRUE + ORACLE_FALSE + ORACLE_DISPUTED}
    extra = sorted(got - known)
    print(f"\n-- ORACLE CHECK, TIER {tier} (vs rc431 manual triage) --")
    print(f"  recall   : {len(hit_true)}/{len(ORACLE_TRUE)} confirmed sites caught")
    for r in miss_true:
        print(f"      MISS  {r[3]:6s} {r[0]}::{r[1]}@{r[2]}")
    print(f"  refuted/benign sites flagged: {len(hit_false)}/{len(ORACLE_FALSE)}")
    for r in hit_false:
        print(f"      FLAG  {r[3]:8s} {r[0]}::{r[1]}@{r[2]}")
    print(f"  disputed sites flagged: {len(hit_disp)}/{len(ORACLE_DISPUTED)}")
    for r in hit_disp:
        print(f"      FLAG  {r[3]:8s} {r[0]}::{r[1]}@{r[2]}")
    print(f"  sites outside the oracle entirely: {len(extra)}")
    for e in extra:
        print(f"      NEW   {e[0]}@{e[1]}")
    rec = {"record": "oracle_check", "tier": tier,
           "n_findings": len(findings),
           "recall_num": len(hit_true), "recall_den": len(ORACLE_TRUE),
           "missed": [list(r) for r in miss_true],
           "flagged_refuted_or_benign": [list(r) for r in hit_false],
           "flagged_disputed": [list(r) for r in hit_disp],
           "outside_oracle": [list(e) for e in extra]}
    emit(rec)
    return rec


# ══════════════════════════════════════════════════════════════════════
# F8 / F9 — the seed-coverage question, asked of BOTH instruments
# ══════════════════════════════════════════════════════════════════════

def real_file_bite_test() -> bool:
    """F10 — the bite test the brief asks for: plant a leak into a REAL source
    file and show the RED, then confirm the unmodified file is green.

    A synthetic control string proves the regex works. It does NOT prove the
    rule fires inside a 2,000-line file with real comments, real macros and
    real neighbouring functions — which is where rc428's D1 and rc430's D7 both
    shipped green. This plants into the actual `srmech_ndjson.c` text.
    """
    print("\n-- F10: REAL-FILE planted-leak bite test --")
    src_path = _C_SRC / "srmech_ndjson.c"
    original = src_path.read_text(encoding="utf-8", errors="replace")

    clean = c_rule11("srmech_ndjson.c", original)
    print(f"  unmodified srmech_ndjson.c  : {len(clean)} unsafe (expect 0)")

    # Plant: delete the close on ONE of the two error-path early returns inside
    # srmech_ndjson_iter — the minimal, realistic mutation.
    planted = original.replace(
        "            srmech_plat_rstream_close(&rs);\n"
        "            return st;\n"
        "        }\n"
        "        if (n_read == 0u) {",
        "            return st;\n"
        "        }\n"
        "        if (n_read == 0u) {",
        1,
    )
    mutated = planted != original
    hits = c_rule11("srmech_ndjson.c<PLANTED>", planted) if mutated else []
    print(f"  mutation applied            : {mutated}")
    print(f"  planted-leak srmech_ndjson.c: {len(hits)} unsafe (expect >=1)")
    for h in hits:
        print(f"      {h['function']} acquire@{h['acquire_line']} "
              f"unsafe return@{h['unsafe_return_line']}")

    ok = (len(clean) == 0) and mutated and (len(hits) >= 1)
    print(f"  [{'PASS' if ok else 'FAIL'}] F10")
    emit({"record": "f10_real_file_bite_test", "file": "srmech_ndjson.c",
          "clean_unsafe": len(clean), "mutation_applied": mutated,
          "planted_unsafe": len(hits), "planted_hits": hits,
          "verdict": "PASS" if ok else "FAIL"})
    return ok


def tier2_verdict(t1: list[dict], t2: list[dict]) -> None:
    """Classify the tier-2 null explicitly — EMPTY, REFUTED, BOUNDED or
    UNSUPPORTED. An unclassified null is how an instrument lies."""
    delta = len(t2) - len(t1)
    print("\n-- TIER-2 (`try`-head extension) VERDICT --")
    if delta == 0:
        verdict = "EMPTY"
        why = ("EMPTY, not REFUTED. The sound `try`-head shape — an acquisition "
               "as the FIRST simple statement of a TOP-LEVEL `try` with no "
               "`finally` — does not occur in this tree. `genome_import`'s "
               "mkdir looks like it but its `try` is nested inside "
               "`if _native.has_native_genome():`, so the try is not top-level "
               "and the raises rc431 cited for it (11612/11617/11636/11641/"
               "11646) live in the MUTUALLY EXCLUSIVE pure-Python branch. The "
               "extension is correct and catches nothing; SHIP TIER 1 and drop "
               "it. Complexity with no measured yield is how an allowlist rots.")
    else:
        verdict = "NONEMPTY"
        why = f"tier 2 added {delta} sites over tier 1"
    print(f"  {verdict}: {why}")
    emit({"record": "tier2_verdict", "t1": len(t1), "t2": len(t2),
          "delta": delta, "verdict": verdict, "rationale": why})


def seed_coverage(py_findings: list[dict], r11: list[dict],
                  r12: list[dict]) -> None:
    print("\n-- F9: does the C side exhibit the SEED shape at all? --")
    gen_c = _C_SRC / "srmech_genome.c"
    gen_txt = gen_c.read_text(encoding="utf-8", errors="replace")
    n_mkdir = len(re.findall(r"\bsrmech_plat_mkdir\s*\(", _strip_c_comments(gen_txt)))
    print(f"  srmech_plat_mkdir calls in srmech_genome.c : {n_mkdir}")
    emit({"record": "f9_c_seed_shape", "file": "srmech_genome.c",
          "srmech_plat_mkdir_calls": n_mkdir,
          "verdict": "REFUTED — C genome surface never creates the directory"
                     if n_mkdir == 0 else "PRESENT"})

    print("\n-- F7/F8: is the SEED DEFECT in the Python population? --")
    seed = [h for h in py_findings
            if h["function"].endswith("genome_save") and h["acquire_line"] == 8980]
    in_pop = len(seed) > 0
    print(f"  genome_save mkdir@8980 in population : {in_pop}")
    emit({"record": "f7_seed_in_population", "in_population": in_pop,
          "rows": seed})

    print("\n-- F8: would a gate SEEDED AT THIS TREE have FAILED on the seed? --")
    verdicts = {
        "c_rule11": ("NO — blind by construction. R11's subject is HELD HANDLES "
                     "(open_ro/rstream/dir). The seed defect is a CREATED NODE "
                     f"in Python, and the C peer makes {n_mkdir} mkdir calls, "
                     "so there is nothing in C for R11 to see."),
        "c_rule12": ("NO — R12 sees created nodes but requires TWO OR MORE in "
                     "one function; genome_save's C peer makes zero, and the "
                     "Python seed makes one."),
        "py_ceil": ("NO if the CEIL is seeded at the live population "
                    f"(in_population={in_pop}): a ceiling that counts the seed "
                    "cannot fire on it. It fires on the NEXT one. The gate's "
                    "honest claim is 'this population may not grow', which is "
                    "a claim about the future, not a detection of the past."),
        "py_ceil_after_fix": ("YES, conditionally — if rc432 repairs the seed, "
                              "the population drops by one, the CEIL is seeded "
                              "at the LOWER number, and re-introducing the seed "
                              "shape reds the gate. The detection is of the "
                              "REGRESSION, never of the original."),
    }
    for k, v in verdicts.items():
        print(f"  {k}: {v}")
    emit({"record": "f8_seed_coverage", "verdicts": verdicts,
          "py_population": len(py_findings),
          "c_r11_live": len(r11), "c_r12_live": len(r12)})


# ══════════════════════════════════════════════════════════════════════

def main() -> int:
    print(f"python           : {sys.version.split()[0]}")
    try:
        import srmech  # noqa: F401
        from srmech.introspect.tool_schema import warmup_all, get_tool_schema
        warmup_all()
        n_tools = len(get_tool_schema().tools)
        print(f"srmech.__file__  : {srmech.__file__}")
        print(f"srmech.__version__: {srmech.__version__}")
        print(f"registry tools   : {n_tools}")
        emit({"record": "env", "srmech_file": str(srmech.__file__),
              "srmech_version": srmech.__version__, "tools": n_tools,
              "python": sys.version.split()[0]})
    except Exception as exc:                       # pragma: no cover
        print(f"srmech import FAILED: {exc!r}")
        emit({"record": "env", "error": repr(exc)})

    preregister()

    c_ok = c_self_test()
    py_ok = py_self_test()
    if not (c_ok and py_ok):
        print("\n*** SELF-TEST FAILED — live scan results are NOT trustworthy. ***")
        emit({"record": "abort", "reason": "self-test failed"})
        _write()
        return 1

    r11, r12 = c_live_scan()
    t0 = py_live_scan(0)
    oracle_check(0, t0)
    t1 = py_live_scan(1)
    oracle_check(1, t1)
    t2 = py_live_scan(2)
    oracle_check(2, t2)
    tier2_verdict(t1, t2)
    if not real_file_bite_test():
        print("\n*** F10 FAILED — R11 cannot fire inside a real file. ***")
        emit({"record": "abort", "reason": "F10 real-file bite test failed"})
        _write()
        return 1
    seed_coverage(t1, r11, r12)

    _write()
    return 0


def _write() -> None:
    out = _HERE / "_s2_instrument_design_rc432.ndjson"
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        for rec in _RECORDS:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
    print(f"\nwrote {out}  ({len(_RECORDS)} records)")


if __name__ == "__main__":
    raise SystemExit(main())
