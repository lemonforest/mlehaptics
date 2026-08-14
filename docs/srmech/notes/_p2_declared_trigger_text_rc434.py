"""`#T1130` P2 — dump each candidate's DECLARED trigger text + signature.

Read-only.  Feeds probe design for P3 (execution).  Emits, per candidate:
the ``Raises:``/``Raises`` block verbatim, the callable's signature, and the
import path so P3 can resolve it.
"""

from __future__ import annotations

import ast
import inspect
import json
import os
import sys

REPO = "/mnt/d/GitHub/mlehaptics"
PKG = os.path.join(REPO, "docs/srmech/python")
IN = os.path.join(REPO, "docs/srmech/notes/_p1_declared_vs_enforced_rc434.ndjson")
OUT = os.path.join(REPO, "docs/srmech/notes/_p2_declared_trigger_text_rc434.ndjson")

FALSEHOOD = {
    "DECLARED_NOT_ENFORCED",
    "DECLARED_NOT_ENFORCED_HAS_OTHER",
    "BOTH_DIRECTIONS",
}


def raises_block_text(doc: str) -> str:
    lines = (doc or "").splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        is_g = s == "Raises:"
        is_n = (
            s == "Raises"
            and i + 1 < len(lines)
            and lines[i + 1].strip() != ""
            and set(lines[i + 1].strip()) == {"-"}
        )
        if not (is_g or is_n):
            i += 1
            continue
        hi = len(lines[i]) - len(lines[i].lstrip())
        out.append(s)
        j = i + 2 if is_n else i + 1
        while j < len(lines):
            ln = lines[j]
            if ln.strip() == "":
                j += 1
                continue
            ind = len(ln) - len(ln.lstrip())
            if (ind < hi) if is_n else (ind <= hi):
                break
            if is_n and j + 1 < len(lines) and lines[j + 1].strip() != "" and set(
                lines[j + 1].strip()
            ) == {"-"}:
                break
            out.append(ln.strip())
            j += 1
        i = j
    return " | ".join(out)


def main() -> int:
    sys.path.insert(0, PKG)
    import srmech

    rows = [json.loads(l) for l in open(IN, encoding="utf-8")]
    cands = [
        r
        for r in rows
        if r.get("record") == "callable"
        and r["public_name"]
        and r["verdict_hop0"] in FALSEHOOD
    ]

    out = [
        {
            "record": "meta",
            "srmech_file": srmech.__file__,
            "srmech_version": srmech.__version__,
            "python": sys.version.split()[0],
            "n_candidates": len(cands),
        }
    ]

    for r in sorted(cands, key=lambda x: (x["module"], x["lineno"])):
        modpath = r["module"][len("srmech/") :].removesuffix(".py").replace("/", ".")
        modname = "srmech" + ("." + modpath if modpath != "__init__" else "")
        if modname.endswith(".__init__"):
            modname = modname[: -len(".__init__")]
        rec = {
            "record": "candidate",
            "module": r["module"],
            "modname": modname,
            "qualname": r["qualname"],
            "lineno": r["lineno"],
            "declared_block": r["declared_block"],
            "enforced_hop0": r["enforced_hop0"],
            "enforced_hop2": r["enforced_hop2"],
            "enforced_global": r["enforced_global"],
            "verdict_hop0": r["verdict_hop0"],
            "verdict_global": r["verdict_global"],
            "asserts": r["asserts"],
        }
        # signature + raises text via live import (also proves importability)
        try:
            mod = __import__(modname, fromlist=["*"])
            obj = mod
            for part in r["qualname"].split("."):
                obj = getattr(obj, part)
            rec["signature"] = str(inspect.signature(obj))
            rec["raises_text"] = raises_block_text(inspect.getdoc(obj) or "")
            rec["resolved"] = True
        except Exception as exc:
            rec["resolved"] = False
            rec["resolve_error"] = f"{type(exc).__name__}: {exc}"
            src = os.path.join(PKG, r["module"])
            with open(src, encoding="utf-8") as fh:
                tree = ast.parse(fh.read())
            rec["raises_text"] = ""
            for node in ast.walk(tree):
                if (
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.lineno == r["lineno"]
                ):
                    rec["raises_text"] = raises_block_text(
                        ast.get_docstring(node) or ""
                    )
        out.append(rec)

    with open(OUT, "w", encoding="utf-8") as fh:
        for rec in out:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    print(f"wrote {OUT}  candidates={len(cands)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
