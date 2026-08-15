"""`#T1131` P7 — HOW MUCH OF THE SUITE EVAPORATES UNDER ``-O``.

.. warning::

   **THIS FILE'S CONCLUSION IS RETRACTED. Its MEASUREMENT stands.**

   The numbers below are correct for what they measure: the builtin ``compile()``
   erases 100% of both corpora's ``assert`` statements under ``-O``. The
   CONCLUSION drawn from them — "a whole-suite ``-O`` cell would run with the
   suite's own assertions inert, so it can see almost nothing" — is WRONG,
   because pytest does not let the interpreter compile test modules. Its
   assertion-rewriting import hook replaces every ``assert`` in a collected TEST
   module with explicit raising bytecode, which ``-O`` cannot strip.

   Measured in ``_p9_pytest_rewrite_vs_dash_o_rc433.py``: under ``pytest -O`` an
   assert written IN a test module still fires, and an assert in a
   non-rewritten (package-like) module does not. So the real split is

       TEST-module asserts  SURVIVE ``-O``
       PACKAGE asserts      VANISH under ``-O``

   The run refuted this file before the reasoning did — all four class-(c)
   meta-gates were predicted to fail under ``-O`` and every one PASSED. Kept
   rather than deleted because the retraction is the finding: the ``-O`` boundary
   falls exactly on the PACKAGE / TEST_LOCAL line the P4 gate already uses.

THE QUESTION THIS SETTLES
=========================
The scope asks whether a whole-suite ``-O`` CI cell is worth its cost. The naive
argument is "it would catch the whole `#T1131` class". Before pricing it, measure
what such a cell can actually SEE.

``-O`` strips ``assert`` at COMPILE time — in the TESTS as well as in the package.
So a test whose body is a chain of ``assert``s does not fail under ``-O``; it
PASSES VACUOUSLY. The only tests that can go RED under ``-O`` are the ones
expecting an exception that no longer arrives (``pytest.raises``) or that crash
on the resulting bad state.

That makes the ``-O`` pass/fail signal a NARROW instrument, not a broad one, and
a green ``-O`` run is not evidence of health — it is evidence the suite has
stopped measuring. This file quantifies the evaporation directly by counting
``LOAD_ASSERTION_ERROR`` opcodes (the bytecode an ``assert`` compiles to) across
the whole test corpus and the whole package, in both compile modes.

An instrument that cannot return otherwise is not a measurement, so the control
is built in: the same counter is run over a file with a KNOWN assert count.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

ROOT = "/mnt/d/GitHub/mlehaptics/docs/srmech/python"
OUT = "/mnt/d/GitHub/mlehaptics/docs/srmech/notes/_p7_dash_o_vacuity_rc433.ndjson"

_COUNTER = r'''
import dis, json, os, sys

def count(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            src = fh.read()
    except (UnicodeDecodeError, OSError):
        return None
    try:
        code = compile(src, path, "exec")
    except SyntaxError:
        return None
    n = 0
    stack = [code]
    while stack:
        c = stack.pop()
        for ins in dis.get_instructions(c):
            if ins.opname == "LOAD_ASSERTION_ERROR":
                n += 1
        for const in c.co_consts:
            if hasattr(const, "co_code"):
                stack.append(const)
    return n

roots = json.loads(sys.argv[1])
out = {}
for label, base in roots.items():
    total = 0
    files = 0
    per = {}
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in {"__pycache__", "build", "dist"}]
        for fn in sorted(filenames):
            if not fn.endswith(".py"):
                continue
            n = count(os.path.join(dirpath, fn))
            if n is None:
                continue
            files += 1
            total += n
            if n:
                per[os.path.relpath(os.path.join(dirpath, fn), base)] = n
    out[label] = {"n_asserts": total, "n_files": files,
                  "top": sorted(per.items(), key=lambda kv: -kv[1])[:8]}
out["_optimize_flag"] = sys.flags.optimize
print("@@V@@" + json.dumps(out, sort_keys=True))
'''

_CONTROL = r'''
import dis, json, sys
src = "\n".join([
    "def f(x):",
    "    assert x > 0, 'a'",
    "    assert x < 10, 'b'",
    "    assert x != 5, 'c'",
    "    return x",
])
code = compile(src, "<control>", "exec")
n = 0
stack = [code]
while stack:
    c = stack.pop()
    for ins in dis.get_instructions(c):
        if ins.opname == "LOAD_ASSERTION_ERROR":
            n += 1
    for const in c.co_consts:
        if hasattr(const, "co_code"):
            stack.append(const)
print("@@C@@" + json.dumps({"known_asserts": 3, "counted": n,
                            "optimize": sys.flags.optimize}))
'''


def _run(src, args, optimize):
    env = dict(os.environ)
    env["PYTHONPATH"] = ROOT
    env.pop("PYTHONOPTIMIZE", None)
    cmd = [sys.executable] + (["-O"] if optimize else []) + ["-c", src] + args
    p = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True,
                       text=True, timeout=900)
    for ln in p.stdout.splitlines():
        if ln.startswith(("@@V@@", "@@C@@")):
            return json.loads(ln[5:])
    raise RuntimeError(p.stderr[-1500:])


def main():
    roots = json.dumps({"tests": os.path.join(ROOT, "tests"),
                        "package": os.path.join(ROOT, "srmech")})

    print("=== CONTROL: can the counter return otherwise? ===")
    c_def = _run(_CONTROL, [], optimize=False)
    c_opt = _run(_CONTROL, [], optimize=True)
    print("  default : known=3 counted=%d (optimize=%d)"
          % (c_def["counted"], c_def["optimize"]))
    print("  -O      : known=3 counted=%d (optimize=%d)"
          % (c_opt["counted"], c_opt["optimize"]))
    ok = c_def["counted"] == 3 and c_opt["counted"] == 0 and c_opt["optimize"] >= 1
    print("  CONTROL:", "PASSES — the counter distinguishes the modes"
          if ok else "*** FAILS — every number below is meaningless ***")

    print("\n=== CORPUS ===")
    d = _run(_COUNTER, [roots], optimize=False)
    o = _run(_COUNTER, [roots], optimize=True)
    rows = []
    for label in ("tests", "package"):
        nd, no = d[label]["n_asserts"], o[label]["n_asserts"]
        gone = nd - no
        pct_num, pct_den = gone * 100, (nd if nd else 1)
        print("  %-8s files=%-5d default=%-7d -O=%-4d  EVAPORATED=%d (%d%%)"
              % (label, d[label]["n_files"], nd, no, gone, pct_num // pct_den))
        rows.append({"corpus": label, "n_files": d[label]["n_files"],
                     "asserts_default": nd, "asserts_dash_O": no,
                     "evaporated": gone,
                     "top_files_default": d[label]["top"]})

    print("\n  top assert-carrying TEST files (default mode):")
    for name, n in d["tests"]["top"]:
        print("    %-58s %d" % (name, n))

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({"record": "vacuity_meta",
                             "control_passes": ok,
                             "control_default_counted": c_def["counted"],
                             "control_dash_O_counted": c_opt["counted"],
                             "python": sys.version.split()[0]},
                            sort_keys=True) + "\n")
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    print("\nwrote", OUT)


if __name__ == "__main__":
    main()
