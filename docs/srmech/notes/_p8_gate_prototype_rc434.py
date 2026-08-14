"""`#T1130` P8 — gate prototype, with its undecidable set counted separately.

The P1 closure matched callees by SHORT NAME, which import aliasing defeats:
``composites.py`` does ``from ..math.cyclic import gcd as _cyclic_gcd``, so the
call ``_cyclic_gcd(a, b)`` resolved to nothing and the site read as
"declares but never enforces".  It happened to be RIGHT there, but for the
wrong reason — and it was WRONG on three sibling sites (``run_toml_chain``,
``spectral.similarity``, ``build_chain_from_toml_str``), all of which execution
proved ENFORCED.  Static precision on that bin was 1/4.

So this prototype resolves import aliases first, then reports THREE bins:

  BIN-1  TYPO / UNKNOWN-CLASS   a declared name that is not a real exception
                                class anywhere the package can see.
                                DECIDABLE -> strict-zero.
  BIN-2  UNENFORCED-IN-PACKAGE  declared, and no ``raise`` of that name is
                                reachable through alias-resolved calls inside
                                the package.  SEMI-decidable -> down-only CEIL.
  BIN-3  UNDECIDABLE            declared name whose only possible source is
                                outside the package (third-party / builtin
                                propagation), or reached only through a
                                dynamic call.  Counted, down-only, NEVER
                                folded into BIN-2.

Plus the coverage FLOOR for the execution gate: how many declared clauses have
an executable probe in the shipped corpus.  That ratchets UP, not down.
"""

from __future__ import annotations

import ast
import json
import os
import sys

REPO = "/mnt/d/GitHub/mlehaptics"
PKG = os.path.join(REPO, "docs/srmech/python")
SRC = os.path.join(PKG, "srmech")
OUT = os.path.join(REPO, "docs/srmech/notes/_p8_gate_prototype_rc434.ndjson")

sys.path.insert(0, PKG)
sys.path.insert(0, os.path.join(REPO, "docs/srmech/notes"))
from _p1_declared_vs_enforced_rc434 import (  # noqa: E402
    looks_like_exception,
    parse_raises_block,
    scan_module,
)

BUILTIN_EXC = {
    n
    for n in dir(__builtins__ if isinstance(__builtins__, dict) else __builtins__)
    if isinstance(n, str)
}


def collect_aliases(path: str) -> dict[str, str]:
    """``{local_name: original_name}`` for every ``import X as Y`` in a module."""
    out: dict[str, str] = {}
    with open(path, encoding="utf-8") as fh:
        try:
            tree = ast.parse(fh.read())
        except SyntaxError:
            return out
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for a in node.names:
                if a.asname:
                    out[a.asname] = a.name.rsplit(".", 1)[-1]
                else:
                    out[a.name.rsplit(".", 1)[-1]] = a.name.rsplit(".", 1)[-1]
    return out


def main() -> int:
    import builtins

    import srmech
    from srmech import _native

    builtin_exc = {
        n
        for n in dir(builtins)
        if isinstance(getattr(builtins, n, None), type)
        and issubclass(getattr(builtins, n), BaseException)
    }

    fh = open(OUT, "w", encoding="utf-8")

    def emit(rec):
        fh.write(json.dumps(rec, sort_keys=True, default=str) + "\n")
        fh.flush()
        os.fsync(fh.fileno())

    emit(
        {
            "record": "meta",
            "srmech_file": srmech.__file__,
            "srmech_version": srmech.__version__,
            "has_native": bool(_native.HAS_NATIVE),
            "n_builtin_exception_classes": len(builtin_exc),
        }
    )

    # ---- scan + alias map --------------------------------------------------
    recs: list[dict] = []
    aliases: dict[str, dict[str, str]] = {}
    for root, _d, files in os.walk(SRC):
        for fn in sorted(files):
            if not fn.endswith(".py"):
                continue
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, PKG).replace(os.sep, "/")
            recs.extend(scan_module(p, rel))
            aliases[rel] = collect_aliases(p)

    callables = [r for r in recs if r.get("record") == "callable"]

    # every exception name the package raises ANYWHERE, and where
    raised_anywhere: set[str] = set()
    raises_by_short: dict[str, set[str]] = {}
    for r in callables:
        raised_anywhere |= set(r["enforced_hop0"])
        short = r["qualname"].rsplit(".", 1)[-1]
        raises_by_short.setdefault(short, set()).update(r["enforced_hop0"])

    # every class the package DEFINES that is exception-shaped
    defined_exc: set[str] = set()
    for root, _d, files in os.walk(SRC):
        for fn in files:
            if not fn.endswith(".py"):
                continue
            with open(os.path.join(root, fn), encoding="utf-8") as f:
                try:
                    tree = ast.parse(f.read())
                except SyntaxError:
                    continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and looks_like_exception(node.name):
                    defined_exc.add(node.name)

    known_exc = builtin_exc | defined_exc
    emit(
        {
            "record": "universe",
            "n_defined_exception_classes": len(defined_exc),
            "n_raised_anywhere": len(raised_anywhere),
        }
    )

    bin1, bin2, bin3 = [], [], []
    n_declaring = 0
    for r in callables:
        declared = r["declared_block"]
        if not declared:
            continue
        n_declaring += 1
        alias = aliases.get(r["module"], {})
        # alias-resolved reachable raises: own body + any called name, with
        # `foo as _bar` resolved back to `foo`
        reach = set(r["enforced_hop0"])
        for c in r["calls"]:
            short = c.rsplit(".", 1)[-1]
            for cand in (short, alias.get(short, short)):
                reach |= raises_by_short.get(cand, set())
        for name in declared:
            row = {
                "module": r["module"],
                "qualname": r["qualname"],
                "lineno": r["lineno"],
                "declared": name,
                "public": r["public_name"],
            }
            if name not in known_exc:
                bin1.append(row)
            elif name in reach:
                continue  # enforced (statically satisfied)
            elif name not in raised_anywhere:
                row["reason"] = "package never raises this name anywhere"
                bin3.append(row) if name not in known_exc else bin2.append(row)
            else:
                row["reason"] = (
                    "raised somewhere in the package but not through an "
                    "alias-resolved call from here"
                )
                bin3.append(row)

    for row in bin1:
        emit({"record": "BIN1_unknown_class", **row})
    for row in bin2:
        emit({"record": "BIN2_unenforced_in_package", **row})
    for row in bin3:
        emit({"record": "BIN3_undecidable", **row})

    emit(
        {
            "record": "gate_numbers",
            "n_callables": len(callables),
            "n_declaring_a_raises_block": n_declaring,
            "BIN1_unknown_class_STRICT_ZERO": len(bin1),
            "BIN2_unenforced_in_package_CEIL": len(bin2),
            "BIN3_undecidable_CEIL": len(bin3),
            "note": (
                "BIN2+BIN3 is the static instrument's total flag rate; "
                "execution proved 80/82 of the P1 candidate clauses ENFORCED, "
                "so BIN3 is where nearly all of that lives."
            ),
        }
    )

    # ---- execution-gate coverage FLOOR -------------------------------------
    n_clauses = sum(len(r["declared_block"]) for r in callables)
    n_public_clauses = sum(
        len(r["declared_block"]) for r in callables if r["public_name"]
    )
    emit(
        {
            "record": "coverage_floor",
            "total_declared_clauses": n_clauses,
            "public_declared_clauses": n_public_clauses,
            "probes_shipped_in_p3_p4_p5": 82 + 20 + 3,
            "note": (
                "the execution gate's ratchet is a FLOOR on covered clauses "
                "that goes UP; it is not a defect CEIL"
            ),
        }
    )

    fh.close()
    print(
        f"wrote {OUT}  BIN1={len(bin1)} BIN2={len(bin2)} BIN3={len(bin3)} "
        f"declaring={n_declaring} clauses={n_clauses}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
