"""rc473 A2 (`#T1188`) — the SRMECH_NODISCARD form matrix, and the form the
twenty-four discards actually took.

WHY THIS EXISTS. Five shipped surfaces said `SRMECH_NODISCARD` + ``-Werror``
refuses a re-introduced discard "on gcc and clang". That is TRUE for a
bare-statement discard and FALSE for the ``(void)``-cast form — and the cast
form is the form all twenty-four sites rc473 repaired were written in. The
corrected sentences now carry a measured matrix, so the matrix needs a
generator: a load-bearing number in shipped prose with no runnable derivation
behind it is the defect class this rc closes on.

THREE SECTIONS, each with its predicate written out.

1. **The compiler matrix.** Two one-line translation units, one form each, plus
   a control with NO attribute at all. The attribute is applied DIRECTLY rather
   than through ``SRMECH_NODISCARD`` so the macro's own ``#if`` ladder cannot
   confound the reading; a fourth pair goes through the REAL header so the
   synthetic reading can be checked against the shipped one.

   ⚠️ **Objects are emitted (``-c``), never ``-fsyntax-only``.** gcc's
   ``-Wunused-result`` fires in the middle end and ``-fsyntax-only`` suppresses
   it silently, so a syntax-only probe reports the whole matrix as a null. That
   failure mode is measured here as its own row rather than described.

   ⚠️ **The discriminator is ``_MSC_VER``, not the compiler's name.** A clang
   targeting MSVC (Windows clang, clang-cl) defines it, so ``srmech.h``'s
   ``#if defined(_MSC_VER)`` arm — first by deliberate design — hands it the
   EMPTY macro and it diagnoses neither form. The preprocessor row records this
   directly instead of leaving it to be inferred.

2. **The form census.** Over a MASKED tree (comments and string/char literals
   blanked, line count preserved), for the seven Class-N double callees: how
   many discards are ``(void)``-cast and how many are bare statements. Run
   UNmasked, the tree's own Rule-7 census reported a phantom family discard
   that was the bad spelling quoted inside a block comment, so masking is not
   optional here.

3. **The public double-array kernel population.** The twin plan proposed
   rescoping rc473's closing claim with "the 78 public double-array kernels".
   ``78`` does not re-derive from the header by any spelling. This section
   derives the figure from a pattern a reader can re-run, so whatever number
   ships carries its own predicate. Parameter lists are WHITESPACE-NORMALISED
   before matching: without that, ``const double *`` reads 38 instead of 67,
   which is the same line-wrapping blindness one layer below the prose.

⚠️ **IT TAKES TWO HOSTS, AND IT SAYS SO.** The repair cell is WSL2, which has
gcc and no clang; the clang and MSVC figures come from the Windows side of the
same machine. So every row carries the ``host`` it was taken on, and a run
MERGES: rows from other hosts are kept, rows from THIS host are replaced. A
compiler that is not installed is recorded as ``unreachable`` BY NAME rather
than skipped — an absent cell and a silent cell are different findings, and a
matrix that quietly drops the cell it could not reach is the instrument lying.

Run (once per host; the ndjson accumulates)::

    python3 notes/_rc473_a2_nodiscard_form_matrix.py
    python3 notes/_rc473_a2_nodiscard_form_matrix.py --tree=main=/path/to/c

Writes ``notes/_rc473_a2_nodiscard_form_matrix.ndjson``. No srmech import, no
numpy.
"""

from __future__ import annotations

import json
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: Which machine a row was taken on. gcc lives on the WSL2 side and clang / cl
#: on the Windows side of the same box, so no single run can fill the matrix
#: and pretending otherwise would be the gate lying.
HOST = platform.system() + " " + platform.release()

# --------------------------------------------------------------------------
# Section 0 — masking, shared by sections 2 and 3.
# --------------------------------------------------------------------------

_LINE_COMMENT = re.compile(r"//.*$")
_BLOCK_ONE_LINE = re.compile(r"/\*.*?\*/")
_STRING = re.compile(r'"(?:\\.|[^"\\])*"')
_CHAR = re.compile(r"'(?:\\.|[^'\\])*'")


def mask_lines(text: str) -> list[str]:
    """Comments and literals blanked; LINE COUNT PRESERVED so file:line is true."""
    out: list[str] = []
    in_block = False
    for line in text.splitlines():
        if in_block:
            end = line.find("*/")
            if end < 0:
                out.append("")
                continue
            line = line[end + 2:]
            in_block = False
        line = _BLOCK_ONE_LINE.sub(" ", line)
        start = line.find("/*")
        if start >= 0:
            in_block = True
            line = line[:start]
        line = _LINE_COMMENT.sub("", line)
        line = _STRING.sub('""', line)
        line = _CHAR.sub("''", line)
        out.append(line)
    return out


# --------------------------------------------------------------------------
# Section 1 — the compiler matrix.
# --------------------------------------------------------------------------

_DECL = """typedef int srmech_status_t;

%s
srmech_status_t srmech_sin(double x, double *out);

srmech_status_t srmech_sin(double x, double *out) { *out = x; return 0; }
"""

_ATTR = "__attribute__((warn_unused_result))"

_TUS = {
    # label                     : (attribute line, statement)
    "synthetic_cast": (_ATTR, "(void)srmech_sin(1.0, &o);"),
    "synthetic_bare": (_ATTR, "srmech_sin(1.0, &o);"),
    "synthetic_control_cast": ("", "(void)srmech_sin(1.0, &o);"),
    "synthetic_control_bare": ("", "srmech_sin(1.0, &o);"),
}

_BODY = """
int probe(void);
int probe(void)
{
    double o = 0.0;
    %s
    return o == 0.0;
}
"""

_REAL_TU = """#include "srmech.h"

int probe(void);
int probe(void)
{
    double o = 0.0;
    %s
    return o == 0.0;
}
"""

_GNU_FLAGS = ["-std=c11", "-Wall", "-Wextra", "-Wunused-result", "-Werror"]


def _verdict(rc: int, out: str) -> str:
    if rc != 0:
        return "error"
    return "warns-only" if out.strip() else "SILENT (exit 0, no output)"


def _run(cmd: list[str]) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.SubprocessError) as exc:
        return -1, f"UNREACHABLE: {exc}"
    return p.returncode, (p.stdout + p.stderr)


def compiler_matrix(cc: str, extra: list[str] | None = None) -> list[dict]:
    """One row per (compiler, form). An absent compiler is a NAMED row."""
    extra = extra or []
    rows: list[dict] = []
    if shutil.which(cc) is None:
        return [{"kind": "compiler_matrix", "compiler": cc, "extra": extra,
                 "status": "unreachable", "why": "not on PATH on this host",
                 "note": "an absent cell and a silent cell are different "
                         "findings; this row exists so the difference is "
                         "readable"}]
    rc, banner = _run([cc, "--version"])
    banner_line = banner.splitlines()[0] if banner.splitlines() else ""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for label, (attr, stmt) in _TUS.items():
            src = tmp / f"{label}.c"
            src.write_text(_DECL % attr + _BODY % stmt, encoding="utf-8")
            cmd = [cc, *_GNU_FLAGS, *extra, "-c", str(src),
                   "-o", str(tmp / f"{label}.o")]
            rc, out = _run(cmd)
            rows.append({"kind": "compiler_matrix", "compiler": cc,
                         "banner": banner_line, "flags": _GNU_FLAGS + extra,
                         "extra": extra, "form": label, "exit": rc,
                         "verdict": _verdict(rc, out),
                         "first_diagnostic": next(
                             (l for l in out.splitlines() if ": error" in l
                              or ": warning" in l), "")})
        # The stated instrument failure mode, MEASURED rather than quoted.
        for label in ("synthetic_cast", "synthetic_bare"):
            src = tmp / f"{label}.c"
            rc, out = _run([cc, *_GNU_FLAGS, *extra, "-fsyntax-only", str(src)])
            rows.append({"kind": "instrument_control", "compiler": cc,
                         "extra": extra, "form": label,
                         "probe": "-fsyntax-only", "exit": rc,
                         "verdict": _verdict(rc, out),
                         "why": "gcc's -Wunused-result fires in the middle "
                                "end; -fsyntax-only suppresses it, so a "
                                "syntax-only probe reads this matrix as a null"})
        # Through the REAL shipped header, both macro arms.
        inc = ROOT / "c" / "include"
        if (inc / "srmech.h").is_file():
            probe = tmp / "macro_probe.c"
            probe.write_text('#include "srmech.h"\n'
                             "SRMECH_NODISCARD int probe(void);\n",
                             encoding="utf-8")
            for arm, flags in (("as-configured", []), ("-U_MSC_VER",
                                                       ["-U_MSC_VER"])):
                rc, out = _run([cc, "-E", *flags, "-I", str(inc), str(probe)])
                last = [l for l in out.splitlines() if l.strip()]
                rows.append({"kind": "macro_expansion", "compiler": cc,
                             "extra": extra, "arm": arm, "exit": rc,
                             "expansion": last[-1].strip() if last else "",
                             "why": "a clang targeting MSVC defines _MSC_VER, "
                                    "so srmech.h's `#if defined(_MSC_VER)` arm "
                                    "hands it the EMPTY macro — the "
                                    "discriminator is _MSC_VER, not the "
                                    "compiler's name"})
            for form, stmt in (("real_cast", "(void)srmech_sin(1.0, &o);"),
                               ("real_bare", "srmech_sin(1.0, &o);")):
                src = tmp / f"{form}.c"
                src.write_text(_REAL_TU % stmt, encoding="utf-8")
                for arm, flags in (("as-configured", []),
                                   ("-U_MSC_VER", ["-U_MSC_VER"])):
                    rc, out = _run([cc, *_GNU_FLAGS, *extra, *flags,
                                    "-I", str(inc), "-c", str(src),
                                    "-o", str(tmp / f"{form}{arm}.o")])
                    rows.append({"kind": "real_header", "compiler": cc,
                                 "extra": extra, "arm": arm, "form": form,
                                 "exit": rc, "verdict": _verdict(rc, out)})
    return rows


#: MSVC has no attribute to apply: `[[nodiscard]]` needs C23 and the library
#: builds -std=c11, and the SAL spelling only speaks under /analyze. cl also
#: needs a vcvars environment, so it is NOT auto-run here. The row below
#: records what WAS run, verbatim, so the shipped figures are re-runnable by
#: hand — recording an un-run cell as absent is the point of the row.
_MSVC_MEASURED = {
    "toolset": "VS2022 Enterprise 14.31.31103, cl 19.31.31104 x64",
    "how": 'cmd /c "vcvars64.bat && cl /nologo /c <flags> <tu>.c"',
    "rows": [
        {"spelling": "SAL _Check_return_", "flags": "/W4 /WX /std:c11",
         "form": "(void) cast", "result": "silent, exit 0"},
        {"spelling": "SAL _Check_return_", "flags": "/W4 /WX /std:c11",
         "form": "bare", "result": "silent, exit 0"},
        {"spelling": "SAL _Check_return_", "flags": "/W4 /analyze /std:c11",
         "form": "(void) cast", "result": "silent — the cast suppresses C6031"},
        {"spelling": "SAL _Check_return_", "flags": "/W4 /analyze /std:c11",
         "form": "bare",
         "result": "warning C6031: Return value ignored: 'srmech_sin'"},
        {"spelling": "[[nodiscard]]", "flags": "/W4 /std:c11", "form": "bare",
         "result": "error C2059: syntax error: '['"},
        {"spelling": "[[nodiscard]]", "flags": "/W4 /std:c17", "form": "bare",
         "result": "error C2059: syntax error: '['"},
        {"spelling": "[[nodiscard]]", "flags": "/W4 /std:clatest",
         "form": "bare",
         "result": "command line warning D9002: ignoring unknown option "
                   "'/std:clatest', then error C2059"},
    ],
}


def msvc_leg() -> list[dict]:
    """One row for the MSVC cell: measured by hand, recorded verbatim."""
    on_path = shutil.which("cl") is not None
    return [{"kind": "msvc_leg", "cl_on_path": on_path,
             "auto_run": False,
             "why_not": "cl needs a vcvars environment and MSVC has no "
                        "attribute to apply (C23 [[nodiscard]] is unavailable "
                        "under -std=c11 and SAL only speaks under /analyze), "
                        "so this leg is measured by hand and transcribed",
             **_MSVC_MEASURED}]


# --------------------------------------------------------------------------
# Section 2 — the form census.
# --------------------------------------------------------------------------

_FAMILY = ("srmech_sin", "srmech_cos", "srmech_atan2", "srmech_atan",
           "srmech_exp", "srmech_log", "srmech_rational_sqrt")
_Q61 = ("srmech_sin_q61", "srmech_cos_q61", "srmech_atan_q61",
        "srmech_exp_q61", "srmech_log_q61", "srmech_sqrt_q61")


def _alt(names: tuple[str, ...]) -> str:
    # Longest first, so `srmech_atan2` is not eaten by `srmech_atan`.
    return "|".join(sorted(names, key=len, reverse=True))


#: A continuation tail: the previous line ends mid-expression, so a call at the
#: start of the next line is the TAIL of an assignment, not a discard. Without
#: this clause `st =\n    jade_pair(` counts as a bare discard.
_CONT_TAIL = re.compile(r"(?:[=(,+\-*/?:&|!<>^%]|\breturn\b)\s*$")


def form_census(c_root: Path, names: tuple[str, ...], sub: str) -> dict:
    void_rx = re.compile(r"\(void\)\s*(" + _alt(names) + r")\s*\(")
    bare_rx = re.compile(r"^\s*(" + _alt(names) + r")\s*\(")
    def_rx = re.compile(r"^\s*(?:SRMECH_NODISCARD\s+)?srmech_status_t\s+("
                        + _alt(names) + r")\s*\(")
    d = c_root / sub
    files = sorted(d.glob("*.c")) if d.is_dir() else []
    void_sites: list[str] = []
    bare_sites: list[str] = []
    occurrences = 0
    definitions = 0
    for p in files:
        rel = p.relative_to(c_root).as_posix()
        prev = ""
        for i, line in enumerate(
                mask_lines(p.read_text(encoding="utf-8", errors="replace")), 1):
            for n in names:
                occurrences += len(re.findall(r"\b" + n + r"\s*\(", line))
            if def_rx.match(line):
                definitions += 1
            for m in void_rx.finditer(line):
                void_sites.append(f"{rel}:{i} {m.group(1)}")
            mb = bare_rx.match(line)
            if mb and not def_rx.match(line) and not _CONT_TAIL.search(prev):
                bare_sites.append(f"{rel}:{i} {mb.group(1)}")
            if line.strip():
                prev = line
    by_callee: dict[str, int] = {}
    for s in void_sites + bare_sites:
        k = s.split()[-1]
        by_callee[k] = by_callee.get(k, 0) + 1
    return {"c_files": len(files),
            "occurrences": occurrences, "definitions": definitions,
            "call_sites": occurrences - definitions,
            "void_cast_discards": len(void_sites),
            "bare_statement_discards": len(bare_sites),
            "total_discards": len(void_sites) + len(bare_sites),
            "by_callee": dict(sorted(by_callee.items())),
            "void_sites": void_sites, "bare_sites": bare_sites}


# --------------------------------------------------------------------------
# Section 3 — the public double-array kernel population (the `78` replacement).
# --------------------------------------------------------------------------

_DECL_HEAD = re.compile(
    r"^(?P<tag>SRMECH_NODISCARD\s+)?"
    r"(?P<ret>[A-Za-z_][A-Za-z0-9_ \t*]*?)\s+"
    r"(?P<name>srmech_[A-Za-z0-9_]+)\s*\(", re.M)


def header_population(header: Path) -> dict:
    masked = "\n".join(mask_lines(header.read_text(encoding="utf-8",
                                                   errors="replace")))
    decls: list[dict] = []
    for m in _DECL_HEAD.finditer(masked):
        end = masked.find(";", m.end())
        if end < 0:
            continue
        body = masked[m.start():end + 1]
        if "{" in body:                      # a definition, not a declaration
            continue
        params = body[body.index("(") + 1: body.rindex(")")] \
            if ")" in body else ""
        decls.append({"name": m.group("name"),
                      "ret": " ".join(m.group("ret").split()),
                      "tagged": bool(m.group("tag")),
                      # WHITESPACE-NORMALISED: a wrapped parameter list is the
                      # same blindness as a wrapped prose claim. Measured cost
                      # of skipping this: `const double *` reads 38, not 67.
                      "params": " ".join(params.split())})
    status = [d for d in decls if d["ret"] == "srmech_status_t"]

    def uniq(rows: list[dict]) -> int:
        return len({d["name"] for d in rows})

    return {
        "all_exported_decls": len(decls),
        "all_exported_decls_unique": uniq(decls),
        "status_returning_decls": len(status),
        "nodiscard_tagged_unique": uniq([d for d in decls if d["tagged"]]),
        "status_const_double_ptr":
            uniq([d for d in status if "const double *" in d["params"]]),
        "status_uint32_and_const_double_ptr":
            uniq([d for d in status if "const double *" in d["params"]
                  and "uint32_t" in d["params"]]),
        "status_any_double_ptr":
            uniq([d for d in status
                  if re.search(r"\bdouble\s*\*", d["params"])]),
        "status_mentions_double":
            uniq([d for d in status if "double" in d["params"]]),
        "first_param_uint32_second_const_double_ptr":
            uniq([d for d in status
                  if re.match(r"\s*uint32_t\s+\w+\s*,\s*const double \*",
                              d["params"])]),
        "note": "`78` does not reproduce under any of these spellings; it is a "
                "count over an external census's own value-type classifier. "
                "Use a figure with its pattern beside it, or label it "
                "inherited.",
    }


# --------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    trees: list[tuple[str, Path]] = []
    for a in argv:
        if a.startswith("--tree"):
            _, _, spec = a.partition("=")
            label, _, path = spec.partition("=") if "=" in spec else (spec, "", "")
            if not path:
                label, _, path = spec.partition(":")
            trees.append((label or "tree", Path(path)))
    if not trees:
        trees = [("as-checked-out", ROOT / "c")]

    rows: list[dict] = []
    for cc in ("gcc", "clang"):
        rows += compiler_matrix(cc)
    rows += compiler_matrix("clang", ["--target=x86_64-pc-linux-gnu"])
    rows += msvc_leg()

    for label, c_root in trees:
        for sub in ("src", "test"):
            rows.append({"kind": "form_census", "tree": label, "dir": sub,
                         "family": "class_n_double_seven",
                         **form_census(c_root, _FAMILY, sub)})
        rows.append({"kind": "form_census", "tree": label, "dir": "test",
                     "family": "class_n_q61_six",
                     **form_census(c_root, _Q61, "test")})

    header = ROOT / "c" / "include" / "srmech.h"
    if header.is_file():
        rows.append({"kind": "header_population", "header": header.name,
                     **header_population(header)})

    for r in rows:
        r["host"] = HOST
        trimmed = {k: v for k, v in r.items() if not k.endswith("_sites")}
        print(json.dumps(trimmed, sort_keys=True))

    dest = Path(__file__).resolve().parent / (Path(__file__).stem + ".ndjson")
    # MERGE, do not overwrite: this host can only fill the cells it has, and
    # dropping another host's rows would silently narrow the matrix the shipped
    # prose rests on.
    kept: list[dict] = []
    if dest.is_file():
        for line in dest.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            old = json.loads(line)
            if old.get("host") != HOST:
                kept.append(old)
    merged = kept + rows
    with dest.open("w", encoding="utf-8", newline="\n") as fh:
        for r in merged:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    hosts = sorted({r.get("host", "?") for r in merged})
    print(f"\nwrote {len(rows)} rows from {HOST!r}, kept {len(kept)} from "
          f"other hosts -> {dest}")
    print(f"hosts now represented: {hosts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
