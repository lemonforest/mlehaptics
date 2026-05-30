#!/usr/bin/env python3
"""check_srmech_discipline.py — enforce the CLAUDE.md §2 srmech-first reflex-override
on RBS research scripts. AST-based, so comments and docstrings CANNOT false-positive
(only real Call nodes are flagged — the failure mode of a plain grep).

Usage:
    python check_srmech_discipline.py [file.py ...]   # default: all R-RBS-LM-*.py beside this file
Exit code = number of HARD violations (0 = clean) so it can gate a (sub-agent) bundle commit.
REVIEW + COVERAGE items are warnings (need a human read) and do NOT change the exit code.

HARD (the STOP-list, CLAUDE.md §2 — these are never OK in a cascade):
  abs(...)                  -> srmech.amsc.cascade.magnitude (rc22+); sign-fold = cascade.pin_slot_at_zero (K) + cascade.reorient (C); never python abs()
  np.linalg.eig/eigh/svd    -> srmech.amsc.laplacian.{jacobi_eigvals, hermitian_eigendecompose, symmetric_eigendecompose}
  hashlib.sha256(...)       -> srmech.amsc.format.sha256_bytes
REVIEW (legitimate ONLY if it feeds a srmech op — needs a human read):
  Counter(...)              -> co-occurrence edge weights feeding dense_laplacian is OK; Counter AS the storage proxy is NOT
COVERAGE (heuristic): does the file reach srmech (directly, or via a subtree helper that wraps it)?
  A file that does numpy work with NO srmech anywhere is a likely hand-roll -> COVERAGE GAP.

KNOWN v1 gap (honest): does NOT yet detect hand-rolled cosine / softmax (fuzzy to AST-match);
those still need the read-the-load-bearing-path step. This checker is itself a pure-AST linter
(no math cascade), so the srmech-first rule does not apply to it.
"""
import ast
import glob
import json
import os
import re
import sys

HARD_EIG = {"np.linalg.eig", "np.linalg.eigh", "np.linalg.svd",
            "numpy.linalg.eig", "numpy.linalg.eigh", "numpy.linalg.svd"}
HELPER_RE = re.compile(r"(k\d+|canonical|rbs|kernel|helper)", re.I)
THIRD_PARTY = {"numpy", "np", "scipy", "torch", "math", "json", "os", "sys", "re",
               "collections", "itertools", "functools", "hashlib", "glob", "pathlib", "time"}
BASELINE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DISCIPLINE_BASELINE.json")


def dotted(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


class V(ast.NodeVisitor):
    def __init__(self):
        self.hard = []
        self.review = []

    def visit_Call(self, n):
        name = dotted(n.func)
        ln = n.lineno
        if name == "abs":
            self.hard.append((ln, "abs() — use srmech.amsc.cascade.magnitude (rc22+); sign-fold = cascade.pin_slot_at_zero (Class K) + cascade.reorient (Class C); never python abs()"))
        elif name in ("np.abs", "numpy.abs"):
            self.review.append((ln, "np.abs — OK only as a residual/diagnostic NORM (e.g. max|recon-orig|); a cascade SIGN-FOLD must use cascade.magnitude (rc22) / Class-K+C, not np.abs"))
        elif name in ("hashlib.sha256",):
            self.hard.append((ln, "hashlib.sha256 — route through srmech.amsc.format.sha256_bytes"))
        elif name in HARD_EIG:
            self.hard.append((ln, f"{name} — use srmech.amsc.laplacian.{{jacobi_eigvals,hermitian_eigendecompose,symmetric_eigendecompose}}"))
        elif name == "Counter" or name.endswith(".Counter"):
            self.review.append((ln, "Counter() — OK only if it feeds srmech dense_laplacian (edge weights); NOT as the storage proxy"))
        self.generic_visit(n)


def imports(tree):
    srmech, helper, numpy = False, set(), False
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                base = a.name.split(".")[0]
                if base == "srmech":
                    srmech = True
                if base in ("numpy",):
                    numpy = True
                for nm in (a.name, a.asname or ""):
                    if HELPER_RE.search(nm) and nm.split(".")[0] not in THIRD_PARTY:
                        helper.add(nm)
        elif isinstance(n, ast.ImportFrom):
            mod = n.module or ""
            base = mod.split(".")[0]
            if base == "srmech":
                srmech = True
            if base == "numpy":
                numpy = True
            for a in n.names:
                for nm in (mod, a.name, a.asname or ""):
                    if nm and HELPER_RE.search(nm) and nm.split(".")[0] not in THIRD_PARTY:
                        helper.add(nm)
    return srmech, helper, numpy


def check(path):
    src = open(path).read()
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return {"file": path, "parse_error": str(e)}
    v = V()
    v.visit(tree)
    srmech, helper, numpy = imports(tree)
    if srmech:
        cov = "srmech (direct import)"
    elif helper:
        cov = "srmech (via helper: %s)" % sorted(helper)[:3]
    elif numpy:
        cov = "NO srmech + uses numpy"
    else:
        cov = "no numeric work"
    return {"file": path, "hard": v.hard, "review": v.review, "coverage": cov,
            "gap": (not srmech and not helper and numpy)}


def hard_counts(results):
    return {os.path.basename(r["file"]): len(r.get("hard", []))
            for r in results if not r.get("parse_error")}


def load_baseline():
    if os.path.exists(BASELINE_PATH):
        with open(BASELINE_PATH) as fh:
            return json.load(fh).get("files", {})
    return {}


def print_report(results):
    nhard = ngap = 0
    for r in results:
        b = os.path.basename(r["file"])
        if r.get("parse_error"):
            print("[PARSE] %s: %s" % (b, r["parse_error"]))
            continue
        for ln, m in r["hard"]:
            print("[HARD]   %s:%d  %s" % (b, ln, m))
            nhard += 1
        for ln, m in r["review"]:
            print("[REVIEW] %s:%d  %s" % (b, ln, m))
        print("[COV]    %s: %s%s" % (b, r["coverage"], "  <-- GAP" if r["gap"] else ""))
        if r["gap"]:
            ngap += 1
    print("\n=== %d files | %d HARD | %d coverage-gap | REVIEW items above need a human read ===" % (len(results), nhard, ngap))
    return nhard


def run_ratchet(results):
    """JPL-style gate: HARD per file may only go DOWN vs DISCIPLINE_BASELINE.json.
    Exit code = number of REGRESSIONS (files that exceeded their baseline, or new
    files with HARD). 0 = green. Improvements are reported but never fail."""
    base, cur = load_baseline(), hard_counts(results)
    regressions = 0
    for f in sorted(set(cur) | set(base)):
        c, b = cur.get(f, 0), base.get(f, 0)
        if c > b:
            print("[REGRESS]  %s: HARD %d > baseline %d  (+%d)" % (f, c, b, c - b))
            regressions += 1
        elif c < b:
            print("[IMPROVED] %s: HARD %d < baseline %d  (-%d) — run --update-baseline to lock it in" % (f, c, b, b - c))
    print("\n=== RATCHET: %d HARD now vs %d baseline | %d regression(s) ===" % (sum(cur.values()), sum(base.values()), regressions))
    print("OK — no file exceeded its baseline (new work added 0 HARD)." if regressions == 0
          else "FAIL — a file added HARD violations above its baseline.")
    return regressions


def update_baseline(results):
    counts = {k: v for k, v in sorted(hard_counts(results).items()) if v}
    payload = {"_comment": "JPL-style ratchet baseline (CLAUDE.md model: violations only go DOWN). "
                           "Per-file HARD abs()/eig/sha256 counts as of the freeze. Regenerate ONLY when REDUCING, "
                           "via: python3 check_srmech_discipline.py --update-baseline",
               "files": counts, "total": sum(counts.values())}
    with open(BASELINE_PATH, "w") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")
    print("baseline written: %d files, %d HARD total -> %s" % (len(counts), sum(counts.values()), os.path.basename(BASELINE_PATH)))
    return 0


def main(argv):
    flags = {a for a in argv if a.startswith("--")}
    fileargs = [a for a in argv if not a.startswith("--")]
    files = fileargs or sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "R-RBS-LM-*.py")))
    results = [check(f) for f in files]
    if "--update-baseline" in flags:
        return update_baseline(results)
    if "--ratchet" in flags:
        return run_ratchet(results)
    return print_report(results)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
