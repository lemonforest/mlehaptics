#!/usr/bin/env python3
"""rc473 A3 --- every figure the A3 prose quotes, in one runnable generator.

Four measurements, each with its own row kind:

  ``phrase_gate``      the whitespace-normalised scan for the two asserted-
                       unreachability phrases, with the naive single-line count
                       beside it so the blindness is a figure and not a claim.
  ``callsite_walk``    the helper call sites by ENCLOSING FUNCTION, which is
                       what the corrected comments cite, plus the stale offset
                       of every line number they used to cite.
  ``nan_reachability`` whether a NaN REACHES each helper: a Debug build aborts
                       on the helper's own assert, the shipped Release build
                       does not.  Needs two builds, so each row records which
                       library answered it and whether this run produced it.
  ``citation_audit``   every ``srmech_{laplacian,svd_qr,eigvals}.c:NNN``
                       citation elsewhere in the tree, with what that line
                       actually holds right now.

A cell this run could not reach is written down BY NAME with
``auto_run: false`` and the reason, never dropped --- an absent cell and a
silent cell are different findings.

    python3 notes/_rc473_a3_measurements.py \\
        --release ~/build/libsrmech.so --debug ~/build-debug/libsrmech.so \\
        > notes/_rc473_a3_measurements.ndjson
"""

from __future__ import annotations

import argparse
import ctypes
import json
import pathlib
import platform
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent  # docs/srmech

TARGETS = {
    "c/src/srmech_laplacian.c": "lap_sqrt",
    "c/src/srmech_svd_qr.c": "sq_sqrt",
    "c/src/srmech_eigvals.c": "srmech_eig_modulus",
}

# The line numbers the two walks CITED before the pre-publish pass replaced
# them with enclosing-function names, and the lines those calls ACTUALLY sat on
# at `e2661c197` (the branch head the pass opened at, before any edit of its
# own).  Both are literals so the "already stale" figure stays derivable after
# this pass's own edits moved the live lines again -- which they did, by +43 in
# srmech_laplacian.c and +27 in srmech_svd_qr.c.  A row therefore carries the
# PRE-EDIT offsets (the finding) and the POST-EDIT live lines (today's tree)
# separately, because mixing them is the very defect being recorded.
OLD_CITED = {
    "c/src/srmech_laplacian.c": [
        240, 304, 344, 1308, 1310, 1312, 1477, 1479, 1481, 1457,
        1852, 1864, 1943, 2311, 2507,
    ],
    "c/src/srmech_svd_qr.c": [153, 328, 250, 252, 254, 297],
}

PRE_EDIT_LIVE = {
    "c/src/srmech_laplacian.c": [
        246, 310, 350, 1314, 1316, 1318, 1463, 1483, 1485, 1487,
        1874, 1886, 1965, 2333, 2529,
    ],
    "c/src/srmech_svd_qr.c": [170, 267, 269, 271, 314, 345],
}
PRE_EDIT_COMMIT = "e2661c197"

_GAP = r"[ \t]*\n?[ \t]*\*?[ \t]*"
PHRASES = {
    "unreachable_by_construction": (
        re.compile(_GAP.join(["unreachable", "by", "construction"]), re.I),
        "unreachable by construction",
    ),
    "passes_neither": (
        re.compile(_GAP.join(["passes", "neither"]), re.I),
        "passes neither",
    ),
}

DEF = re.compile(r"^[A-Za-z_][A-Za-z0-9_ \*]*?\b([a-z_][a-z0-9_]*)\s*\(")


def mask(text: str) -> str:
    """Blank comments and string/char literals; preserve line count."""
    out: list[str] = []
    i, n, state = 0, len(text), None
    while i < n:
        c = text[i]
        if state is None:
            if text.startswith("/*", i):
                state, i = "block", i + 2
                out.append("  ")
                continue
            if text.startswith("//", i):
                state, i = "line", i + 2
                out.append("  ")
                continue
            if c in "\"'":
                state, i = c, i + 1
                out.append(" ")
                continue
            out.append(c)
            i += 1
        elif state == "block":
            if text.startswith("*/", i):
                state, i = None, i + 2
                out.append("  ")
                continue
            out.append("\n" if c == "\n" else " ")
            i += 1
        elif state == "line":
            if c == "\n":
                state, i = None, i + 1
                out.append("\n")
                continue
            out.append(" ")
            i += 1
        else:
            if c == "\\":
                out.append("  ")
                i += 2
                continue
            if c == state:
                state = None
            out.append("\n" if c == "\n" else " ")
            i += 1
    return "".join(out)


def row_phrase_gate(root: pathlib.Path) -> list[dict]:
    rows = []
    for rel in TARGETS:
        text = (root / rel).read_text(encoding="utf-8")
        row = {"kind": "phrase_gate", "file": rel, "auto_run": True}
        for key, (rx, naive) in PHRASES.items():
            row["normalised_" + key] = len(rx.findall(text))
            row["naive_" + key] = text.count(naive)
        rows.append(row)
    return rows


def row_callsite_walk(root: pathlib.Path) -> list[dict]:
    rows = []
    for rel, helper in TARGETS.items():
        raw = (root / rel).read_text(encoding="utf-8")
        lines = mask(raw).split("\n")
        owner, cur = [], None
        for ln in lines:
            if ln and not ln[0].isspace() and "(" in ln and ";" not in ln:
                m = DEF.match(ln)
                if m:
                    cur = m.group(1)
            owner.append(cur)
        call = re.compile(r"\b" + re.escape(helper) + r"\s*\(")
        sites, per_fn = [], {}
        for i, ln in enumerate(lines):
            if call.search(ln) and owner[i] != helper:
                sites.append(i + 1)
                per_fn[owner[i]] = per_fn.get(owner[i], 0) + 1
        row = {
            "kind": "callsite_walk",
            "file": rel,
            "helper": helper,
            "call_sites": len(sites),
            "enclosing_functions": len(per_fn),
            "per_enclosing_function": dict(sorted(per_fn.items())),
            "live_lines": sites,
            "auto_run": True,
        }
        old = OLD_CITED.get(rel)
        if old:
            pre = sorted(PRE_EDIT_LIVE[rel])
            offsets = [b - a for a, b in zip(sorted(old), pre)]
            row["previously_cited_lines"] = sorted(old)
            row["pre_edit_live_lines"] = pre
            row["pre_edit_commit"] = PRE_EDIT_COMMIT
            row["stale_offsets_at_pre_edit_commit"] = offsets
            row["distinct_stale_offsets_at_pre_edit_commit"] = sorted(set(offsets))
            row["previously_cited_lines_correct_at_pre_edit_commit"] = sorted(
                set(old) & set(pre)
            )
            row["this_pass_moved_live_lines_by"] = sorted(
                {b - a for a, b in zip(pre, sorted(sites))}
            )
        rows.append(row)
    return rows


NAN_CASES = {
    "lap_sqrt": {
        "symbol": "srmech_jacobi_eigvals",
        "note": "NaN on the diagonal makes tau NaN; "
                "srmech_laplacian_jacobi_rotate calls lap_sqrt(1 + tau*tau).",
    },
    "sq_sqrt": {
        "symbol": "srmech_svd_f64",
        "note": "NaN in A[0][0] reaches sq_sqrt via nrm2 / aa*bb; "
                "`aa <= zero_floor` is FALSE for NaN.",
    },
    "srmech_eig_modulus": {
        "symbol": "srmech_mat_eigvals_ws",
        "note": "NaN on the complex-interleaved diagonal reaches "
                "srmech_eig_modulus through srmech_eig_norms / _pin.",
    },
}


def _probe(libpath: str, helper: str, a00: float):
    """Run ONE case in a subprocess: a Debug abort must not hide the others."""
    code = (
        "import ctypes,sys\n"
        "lib=ctypes.CDLL(sys.argv[1]); h=sys.argv[2]; a=float(sys.argv[3])\n"
        "nan=float('nan'); a = nan if sys.argv[3]=='nan' else a\n"
        "if h=='lap_sqrt':\n"
        "    f=lib.srmech_jacobi_eigvals; f.restype=ctypes.c_int\n"
        "    m=(ctypes.c_double*4)(a,1.0,1.0,2.0); o=(ctypes.c_double*2)()\n"
        "    st=f(ctypes.c_uint32(2),m,ctypes.c_uint32(0),ctypes.c_double(1e-12),o)\n"
        "    out=list(o)\n"
        "elif h=='sq_sqrt':\n"
        "    lib.srmech_svd_f64_ws_bound.restype=ctypes.c_size_t\n"
        "    nb=lib.srmech_svd_f64_ws_bound(2,2); ws=(ctypes.c_char*nb)()\n"
        "    A=(ctypes.c_double*4)(a,1.0,1.0,2.0); U=(ctypes.c_double*4)()\n"
        "    S=(ctypes.c_double*2)(); V=(ctypes.c_double*4)()\n"
        "    f=lib.srmech_svd_f64; f.restype=ctypes.c_int\n"
        "    st=f(ctypes.c_uint32(2),ctypes.c_uint32(2),A,U,S,V,\n"
        "         ctypes.cast(ws,ctypes.POINTER(ctypes.c_double)),ctypes.c_size_t(nb))\n"
        "    out=list(S)\n"
        "else:\n"
        "    lib.srmech_mat_eigvals_ws_size.restype=ctypes.c_size_t\n"
        # ws_size here returns a COUNT OF DOUBLES (the kernel carves with
        # double-pointer arithmetic), unlike srmech_svd_f64_ws_bound which
        # the header states in BYTES. Allocating bytes under-allocates 8x:
        # the correct values still PRINT and the process then dies with
        # SIGSEGV at exit -- measured, and the reason this comment exists.
        "    nb=lib.srmech_mat_eigvals_ws_size(2)\n"
        "    ws=(ctypes.c_double*nb)()\n"
        "    A=(ctypes.c_double*8)(a,0.0,1.0,0.0,1.0,0.0,2.0,0.0)\n"
        "    o=(ctypes.c_double*4)(); f=lib.srmech_mat_eigvals_ws; f.restype=ctypes.c_int\n"
        "    st=f(ctypes.c_uint32(2),A,ctypes.c_uint32(100),o,\n"
        "         ctypes.cast(ws,ctypes.POINTER(ctypes.c_double)),ctypes.c_size_t(nb))\n"
        "    out=list(o)\n"
        "print(st, out)\n"
    )
    p = subprocess.run(
        [sys.executable, "-c", code, libpath, helper, "nan" if a00 != a00 else repr(a00)],
        capture_output=True,
        text=True,
    )
    return p


def row_nan_reachability(release: str | None, debug: str | None) -> list[dict]:
    rows = []
    for helper, meta in NAN_CASES.items():
        for build, lib in (("release", release), ("debug", debug)):
            for label, a00 in (("nan", float("nan")), ("control_4.0", 4.0)):
                row = {
                    "kind": "nan_reachability",
                    "helper": helper,
                    "public_symbol": meta["symbol"],
                    "note": meta["note"],
                    "build": build,
                    "argument": label,
                }
                if lib is None:
                    row["auto_run"] = False
                    row["reason_unreachable"] = (
                        f"no {build} library passed on the command line; pass "
                        f"--{build} <path to libsrmech.so>. The debug build is "
                        "the one with asserts live (-DNDEBUG absent), which is "
                        "what makes reachability observable at all."
                    )
                    rows.append(row)
                    continue
                p = _probe(lib, helper, a00)
                row["auto_run"] = True
                row["library"] = lib
                row["returncode"] = p.returncode
                row["aborted"] = p.returncode != 0
                row["stdout"] = p.stdout.strip()
                row["stderr_tail"] = p.stderr.strip().splitlines()[-1] if p.stderr.strip() else ""
                rows.append(row)
    return rows


CITE = re.compile(r"srmech_(laplacian|svd_qr|eigvals)\.c:(\d+)")
SKIP_DIRS = {".git", "node_modules", "build", "__pycache__"}


def row_citation_audit(repo_root: pathlib.Path, root: pathlib.Path) -> list[dict]:
    src = {}
    for rel in TARGETS:
        src[pathlib.Path(rel).name] = (root / rel).read_text(
            encoding="utf-8", errors="replace"
        ).split("\n")
    hits: dict[tuple[str, int], list[str]] = {}
    for p in repo_root.rglob("*"):
        if not p.is_file() or any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix.lower() in {".so", ".dll", ".o", ".a", ".png", ".pdf", ".whl"}:
            continue
        if p.parent.name == "src" and p.name in src:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in CITE.finditer(text):
            key = ("srmech_" + m.group(1) + ".c", int(m.group(2)))
            hits.setdefault(key, []).append(str(p.relative_to(repo_root)))
    rows = []
    for (f, n), where in sorted(hits.items()):
        lines = src[f]
        line = lines[n - 1].rstrip() if 0 < n <= len(lines) else None
        rows.append(
            {
                "kind": "citation_audit",
                "cited": f"{f}:{n}",
                "occurrences": len(where),
                "citing_files": sorted(set(where)),
                "line_now_holds": line,
                "auto_run": True,
            }
        )
    return rows


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--release", default=None)
    ap.add_argument("--debug", default=None)
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--repo-root", default=str(ROOT.parent.parent))
    args = ap.parse_args(argv[1:])
    root = pathlib.Path(args.root)
    repo_root = pathlib.Path(args.repo_root)

    print(
        json.dumps(
            {
                "kind": "conditions",
                "host": platform.platform(),
                "python": sys.version.split()[0],
                "release_library": args.release,
                "debug_library": args.debug,
                "cell_authenticity": (
                    "srmech_rational_sqrt(NaN) -> status 2 at the symbol; that, "
                    "and not version or ABI, is what separates an rc473 .so "
                    "from an rc472 one"
                ),
            },
            sort_keys=True,
        )
    )
    if args.release:
        lib = ctypes.CDLL(args.release)
        lib.srmech_rational_sqrt.restype = ctypes.c_int
        lib.srmech_rational_sqrt.argtypes = [ctypes.c_double, ctypes.POINTER(ctypes.c_double)]
        lib.srmech_abi_version.restype = ctypes.c_uint32
        lib.srmech_version.restype = ctypes.c_char_p
        out = ctypes.c_double(0.0)
        st = lib.srmech_rational_sqrt(ctypes.c_double(float("nan")), ctypes.byref(out))
        print(
            json.dumps(
                {
                    "kind": "cell_authenticity",
                    "library": args.release,
                    "version": lib.srmech_version().decode(),
                    "abi_version": lib.srmech_abi_version(),
                    "rational_sqrt_nan_status": st,
                    "authentic_rc473": st == 2,
                    "auto_run": True,
                },
                sort_keys=True,
            )
        )

    for row in row_phrase_gate(root):
        print(json.dumps(row, sort_keys=True))
    for row in row_callsite_walk(root):
        print(json.dumps(row, sort_keys=True))
    for row in row_nan_reachability(args.release, args.debug):
        print(json.dumps(row, sort_keys=True))
    for row in row_citation_audit(repo_root, root):
        print(json.dumps(row, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
