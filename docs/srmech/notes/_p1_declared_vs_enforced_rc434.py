"""`#T1130` P1 — AST census of DECLARED vs ENFORCED exception contracts.

Read-only instrument. Walks every ``.py`` under ``srmech/`` and, for each
function/method, extracts:

  * DECLARED  — exception names in the docstring's ``Raises:`` block, plus
    (separately) exception-shaped names anywhere else in the docstring prose.
  * ENFORCED  — exception names in ``raise X(...)`` statements in the
    function's OWN body (nested ``def``/``lambda`` bodies are attributed to
    the nested callable, not the parent), plus bare ``raise`` re-raises and
    ``assert`` statements.

Then closes ENFORCED over module-local helper calls (1-hop and 2-hop) so a
validator helper like ``_require_int`` does not read as "declares but never
enforces".  The delta between hop-0 / hop-1 / hop-2 IS the static
instrument's undecidable residual and is reported, not hidden.

PRE-REGISTERED FALSIFIERS (written before the first run):

  F1  filed population is 15          -> falsified if confirmed count != 15
  F2  filed taxonomy is 4 families    -> falsified if measured families != 4
  F3  #T1131's 17 ops carry zero
      ``Raises:`` blocks (EMPTY)      -> falsified if any of the 17 has one
  F4  only DECLARED-NOT-ENFORCED
      direction is present            -> falsified if any public callable
                                         raises an undeclared exception
  NC1 known-positive control          -> instrument MUST flag every synthetic
                                         mismatch in the control corpus
  NC2 known-clean control             -> instrument MUST NOT flag a function
                                         whose Raises block matches its body

No numpy, no stdlib ``math``/``fractions``/``decimal``, no ``abs()``.
``ast`` + ``json`` are parsing/serialisation, not arithmetic.
"""

from __future__ import annotations

import ast
import json
import os
import sys

REPO = "/mnt/d/GitHub/mlehaptics"
PKG = os.path.join(REPO, "docs/srmech/python")
SRC = os.path.join(PKG, "srmech")
OUT = os.path.join(REPO, "docs/srmech/notes/_p1_declared_vs_enforced_rc434.ndjson")

# Names that look like exceptions.  Deliberately generous on the suffix set so
# the instrument over-collects rather than under-collects; the #T1131 scope's
# regex leak was an UNDER-collection bug, so the safe bias is the other way.
_EXC_SUFFIXES = (
    "Error",
    "Exception",
    "Warning",
    "Exit",
    "Interrupt",
    "Cancelled",
    "Timeout",
    "Conflict",
    "NotFound",
)
_EXC_EXACT = {
    "StopIteration",
    "StopAsyncIteration",
    "KeyboardInterrupt",
    "SystemExit",
    "GeneratorExit",
}


def looks_like_exception(name: str) -> bool:
    """True when ``name`` reads as an exception class name."""
    tail = name.rsplit(".", 1)[-1]
    if tail in _EXC_EXACT:
        return True
    if not tail[:1].isupper():
        return False
    for suffix in _EXC_SUFFIXES:
        if tail.endswith(suffix):
            return True
    return False


# ---------------------------------------------------------------- docstrings


def _indent_of(line: str) -> int:
    n = 0
    for ch in line:
        if ch == " ":
            n += 1
        elif ch == "\t":
            n += 8
        else:
            break
    return n


def parse_raises_block(doc: str) -> list[str]:
    """Extract exception names from a Google-style ``Raises:`` section.

    Indentation-aware on purpose.  A flat regex over the whole docstring is
    what leaked in the #T1131 instrument; here the block boundary is found by
    dedent and only the *first* indent level inside the block yields names.
    """
    if not doc:
        return []
    lines = doc.splitlines()
    names: list[str] = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        # Google style "Raises:" / numpydoc "Raises" + "------"
        is_google = stripped == "Raises:"
        is_numpy = (
            stripped == "Raises"
            and i + 1 < len(lines)
            and set(lines[i + 1].strip()) == {"-"}
            and lines[i + 1].strip() != ""
        )
        if not (is_google or is_numpy):
            i += 1
            continue
        header_indent = _indent_of(lines[i])
        j = i + 2 if is_numpy else i + 1
        # find the block's own indent from the first non-blank body line
        body_indent = None
        while j < len(lines):
            line = lines[j]
            if line.strip() == "":
                j += 1
                continue
            ind = _indent_of(line)
            if is_numpy:
                # numpydoc bodies sit at the SAME indent as the header; the
                # section ends at a dedent BELOW it, or at the next underlined
                # section header.  (NC-8 caught the `<=` bug here.)
                if ind < header_indent:
                    break
                if (
                    j + 1 < len(lines)
                    and lines[j + 1].strip() != ""
                    and set(lines[j + 1].strip()) == {"-"}
                ):
                    break
            else:
                if ind <= header_indent:
                    break  # dedent -> section over
            if body_indent is None:
                body_indent = ind
            if ind == body_indent:
                head = line.strip()
                # "TypeError: if ..."  |  "ValueError" (numpydoc)  | "A or B: ..."
                label = head.split(":", 1)[0].strip()
                for tok in label.replace("|", " ").replace(",", " ").replace(
                    " or ", " "
                ).split():
                    tok = tok.strip("`*'\"()[]")
                    if tok and looks_like_exception(tok):
                        names.append(tok.rsplit(".", 1)[-1])
            j += 1
        i = j
    # order-preserving dedupe
    seen: list[str] = []
    for n in names:
        if n not in seen:
            seen.append(n)
    return seen


def parse_prose_exceptions(doc: str) -> list[str]:
    """Every exception-shaped token anywhere in the docstring (superset)."""
    if not doc:
        return []
    out: list[str] = []
    tok = ""
    for ch in doc + " ":
        if ch.isalnum() or ch == "_":
            tok += ch
        else:
            if tok and looks_like_exception(tok) and tok not in out:
                out.append(tok)
            tok = ""
    return out


# --------------------------------------------------------------------- AST


class _OwnBodyRaises(ast.NodeVisitor):
    """Collect raises/asserts/calls in ONE function body, not nested defs."""

    def __init__(self) -> None:
        self.raises: list[str] = []
        self.bare_raises = 0
        self.asserts = 0
        self.calls: list[str] = []

    def _skip(self, node):  # nested callables own their own bodies
        return

    visit_FunctionDef = _skip
    visit_AsyncFunctionDef = _skip
    visit_Lambda = _skip
    visit_ClassDef = _skip

    def visit_Raise(self, node: ast.Raise) -> None:
        exc = node.exc
        if exc is None:
            self.bare_raises += 1
        else:
            target = exc.func if isinstance(exc, ast.Call) else exc
            name = _dotted(target)
            if name:
                self.raises.append(name.rsplit(".", 1)[-1])
            else:
                self.raises.append("<dynamic>")
        self.generic_visit(node)

    def visit_Assert(self, node: ast.Assert) -> None:
        self.asserts += 1
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        name = _dotted(node.func)
        if name:
            self.calls.append(name)
        self.generic_visit(node)


def _dotted(node) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None


def scan_module(path: str, relmod: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as fh:
        src = fh.read()
    try:
        tree = ast.parse(src, filename=path)
    except SyntaxError as exc:  # pragma: no cover - reported, never silent
        return [{"record": "parse_error", "module": relmod, "detail": str(exc)}]

    recs: list[dict] = []

    def walk(node, scope: tuple[str, ...], in_class: bool) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                walk(child, scope + (child.name,), True)
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qual = ".".join(scope + (child.name,))
                doc = ast.get_docstring(child) or ""
                collector = _OwnBodyRaises()
                for stmt in child.body:
                    collector.visit(stmt)
                declared = parse_raises_block(doc)
                prose = parse_prose_exceptions(doc)
                public = not any(p.startswith("_") for p in (scope + (child.name,)))
                recs.append(
                    {
                        "record": "callable",
                        "module": relmod,
                        "qualname": qual,
                        "lineno": child.lineno,
                        "public_name": public,
                        "has_docstring": bool(doc),
                        "declared_block": declared,
                        "declared_prose": prose,
                        "enforced_hop0": sorted(set(collector.raises)),
                        "bare_raises": collector.bare_raises,
                        "asserts": collector.asserts,
                        "calls": sorted(set(collector.calls)),
                    }
                )
                walk(child, scope + (child.name,), False)
            else:
                walk(child, scope, in_class)

    walk(tree, (), False)
    return recs


# ------------------------------------------------------------ helper closure


def close_over_helpers(recs: list[dict], hops: int) -> None:
    """Union in raises reachable through module-local helper calls."""
    by_mod: dict[str, dict[str, set[str]]] = {}
    for r in recs:
        if r.get("record") != "callable":
            continue
        by_mod.setdefault(r["module"], {})[r["qualname"]] = set(r["enforced_hop0"])
        # also index bare function name for method/plain-func call sites
        short = r["qualname"].rsplit(".", 1)[-1]
        by_mod[r["module"]].setdefault(short, set()).update(r["enforced_hop0"])

    for r in recs:
        if r.get("record") != "callable":
            continue
        acc = set(r["enforced_hop0"])
        frontier = set(r["calls"])
        seen_calls: set[str] = set()
        for _hop in range(hops):
            nxt: set[str] = set()
            for c in frontier:
                if c in seen_calls:
                    continue
                seen_calls.add(c)
                short = c.rsplit(".", 1)[-1]
                tbl = by_mod.get(r["module"], {})
                if short in tbl:
                    acc |= tbl[short]
                    for peer in recs:
                        if (
                            peer.get("record") == "callable"
                            and peer["module"] == r["module"]
                            and peer["qualname"].rsplit(".", 1)[-1] == short
                        ):
                            nxt |= set(peer["calls"])
            frontier = nxt
        r[f"enforced_hop{hops}"] = sorted(acc)


def close_global(recs: list[dict]) -> None:
    """Whole-package closure: union raises of ANY callable with a matching
    short name, wherever it lives.  This is deliberately over-permissive — it
    is the UPPER BOUND on "could this call chain raise X".  A site that is
    still DECLARED_NOT_ENFORCED under global closure is a strong candidate;
    the gap between hop2 and global is the cross-module undecidable band.
    """
    tbl: dict[str, set[str]] = {}
    for r in recs:
        if r.get("record") != "callable":
            continue
        short = r["qualname"].rsplit(".", 1)[-1]
        tbl.setdefault(short, set()).update(r["enforced_hop0"])
    for r in recs:
        if r.get("record") != "callable":
            continue
        acc = set(r.get("enforced_hop2", r["enforced_hop0"]))
        for c in r["calls"]:
            acc |= tbl.get(c.rsplit(".", 1)[-1], set())
        r["enforced_global"] = sorted(acc)


# ------------------------------------------------------------------ control

CONTROL_SRC = '''
"""NC control corpus for the #T1130 declared-vs-enforced instrument."""


def nc_pos_declared_not_enforced(x):
    """Positive control: promises ValueError, raises nothing.

    Raises:
        ValueError: never actually happens.
    """
    return x


def nc_pos_type_mismatch(x):
    """Positive control: promises ValueError, raises TypeError.

    Raises:
        ValueError: claimed.
    """
    raise TypeError("actual")


def nc_pos_enforced_not_declared(x):
    """Positive control: raises with no Raises block at all."""
    raise RuntimeError("undeclared")


def nc_pos_prose_only(x):
    """Positive control: prose says it raises a ValueError, body does not."""
    return x


def nc_clean_match(x):
    """Negative control: declaration and body agree.

    Raises:
        ValueError: when x is negative.
    """
    if x < 0:
        raise ValueError("negative")
    return x


def nc_clean_silent(x):
    """Negative control: no declaration, no raise."""
    return x + 1


def nc_clean_via_helper(x):
    """Negative control: declares ValueError, enforces through a helper.

    Raises:
        ValueError: when x is negative.
    """
    _nc_require_nonneg(x)
    return x


def _nc_require_nonneg(x):
    if x < 0:
        raise ValueError("negative")


def nc_clean_numpydoc(x):
    """Negative control: numpydoc-style section that DOES match.

    Raises
    ------
    ValueError
        when x is negative.
    """
    if x < 0:
        raise ValueError("negative")
    return x


def nc_pos_unrescuable(x):
    """Positive control: declares an exception NOTHING in the corpus raises.

    Global closure must NOT rescue this one.

    Raises:
        OverflowError: claimed, never raised anywhere.
    """
    _nc_require_nonneg(x)
    return x


def nc_clean_two_hop(x):
    """Negative control: enforcement is TWO helper hops away.

    Raises:
        ValueError: when x is negative.
    """
    _nc_outer(x)
    return x


def _nc_outer(x):
    _nc_require_nonneg(x)
'''

CONTROL_EXPECT = {
    # qualname -> expected instrument verdict at hop2
    "nc_pos_declared_not_enforced": "DECLARED_NOT_ENFORCED",
    "nc_pos_type_mismatch": "BOTH_DIRECTIONS",
    "nc_pos_enforced_not_declared": "ENFORCED_NOT_DECLARED",
    "nc_pos_prose_only": "PROSE_ONLY",
    "nc_clean_match": "CLEAN",
    "nc_clean_silent": "CLEAN",
    "nc_clean_via_helper": "CLEAN",
    "nc_clean_numpydoc": "CLEAN",
    # NC-9 originally expected DECLARED_NOT_ENFORCED.  The control refuted the
    # EXPECTATION, not the instrument: the helper enforces ValueError while the
    # docstring declares OverflowError, so BOTH directions are non-empty and
    # BOTH_DIRECTIONS is the correct bin.  Recorded rather than quietly edited.
    "nc_pos_unrescuable": "BOTH_DIRECTIONS",
    "nc_clean_two_hop": "CLEAN",
}


def verdict(rec: dict, hop_key: str) -> str:
    declared = set(rec["declared_block"])
    enforced = set(rec[hop_key]) - {"<dynamic>"}
    prose_only = set(rec["declared_prose"]) - declared
    if declared and enforced:
        if declared - enforced and enforced - declared:
            return "BOTH_DIRECTIONS"
        if declared - enforced:
            return "DECLARED_NOT_ENFORCED"
        if enforced - declared:
            return "ENFORCED_NOT_DECLARED"
        return "CLEAN"
    if declared and not enforced:
        if rec["bare_raises"] or rec["asserts"]:
            return "DECLARED_NOT_ENFORCED_HAS_OTHER"
        return "DECLARED_NOT_ENFORCED"
    if enforced and not declared:
        return "ENFORCED_NOT_DECLARED"
    if prose_only and not enforced:
        return "PROSE_ONLY"
    return "CLEAN"


def run_control(out: list[dict]) -> bool:
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "nc_control_rc434.py")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(CONTROL_SRC)
        recs = scan_module(p, "nc_control_rc434")
    close_over_helpers(recs, 1)
    close_over_helpers(recs, 2)
    close_global(recs)
    ok = True
    for r in recs:
        want = CONTROL_EXPECT.get(r["qualname"])
        if want is None:
            continue
        got = verdict(r, "enforced_global")
        # PROSE_ONLY and DECLARED_NOT_ENFORCED are both "flagged"; the control
        # asserts the exact bin so a silently-widened bin fails loudly.
        passed = got == want
        ok = ok and passed
        out.append(
            {
                "record": "control",
                "case": r["qualname"],
                "expected": want,
                "got": got,
                "pass": passed,
                "declared_block": r["declared_block"],
                "declared_prose": r["declared_prose"],
                "enforced_hop0": r["enforced_hop0"],
                "enforced_hop2": r["enforced_hop2"],
                "enforced_global": r["enforced_global"],
            }
        )
    return ok


# --------------------------------------------------------------------- main


def main() -> int:
    sys.path.insert(0, PKG)
    import srmech

    out: list[dict] = []
    out.append(
        {
            "record": "meta",
            "srmech_file": srmech.__file__,
            "srmech_version": srmech.__version__,
            "python": sys.version.split()[0],
        }
    )
    try:
        from srmech import _native

        out[-1]["has_native"] = bool(_native.HAS_NATIVE)
    except Exception as exc:  # pragma: no cover
        out[-1]["has_native_probe_error"] = repr(exc)

    control_ok = run_control(out)
    out.append({"record": "control_summary", "all_pass": control_ok})

    recs: list[dict] = []
    for root, _dirs, files in os.walk(SRC):
        for fn in sorted(files):
            if not fn.endswith(".py"):
                continue
            path = os.path.join(root, fn)
            rel = os.path.relpath(path, PKG).replace(os.sep, "/")
            recs.extend(scan_module(path, rel))

    close_over_helpers(recs, 1)
    close_over_helpers(recs, 2)
    close_global(recs)

    tally: dict[str, int] = {}
    tally0: dict[str, int] = {}
    for r in recs:
        if r.get("record") != "callable":
            out.append(r)
            continue
        v0 = verdict(r, "enforced_hop0")
        v1 = verdict(r, "enforced_hop1")
        v2 = verdict(r, "enforced_hop2")
        vg = verdict(r, "enforced_global")
        r["verdict_hop0"] = v0
        r["verdict_hop1"] = v1
        r["verdict_hop2"] = v2
        r["verdict_global"] = vg
        key = f"{v2}|public={r['public_name']}"
        tally[key] = tally.get(key, 0) + 1
        k0 = f"{v0}|public={r['public_name']}"
        tally0[k0] = tally0.get(k0, 0) + 1
        # emit anything the FALSEHOOD direction touches at any hop, plus the
        # omission direction only for public callables (scale reported below).
        falsehood = {
            "DECLARED_NOT_ENFORCED",
            "DECLARED_NOT_ENFORCED_HAS_OTHER",
            "BOTH_DIRECTIONS",
            "PROSE_ONLY",
        }
        if v0 in falsehood or v2 in falsehood or vg in falsehood:
            out.append(r)
        elif v2 != "CLEAN" and r["public_name"]:
            out.append(r)

    out.append(
        {
            "record": "tally",
            "n_callables": sum(1 for r in recs if r.get("record") == "callable"),
            "by_verdict_public_hop2": tally,
            "by_verdict_public_hop0": tally0,
        }
    )

    with open(OUT, "w", encoding="utf-8") as fh:
        for rec in out:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    print(f"wrote {OUT}  records={len(out)}  control_ok={control_ok}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
