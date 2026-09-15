"""Stop / SubagentStop — the worked-examples ledger must not claim results it
has not re-measured. (rc452, `#T1166`)

WHAT IT CATCHES, MEASURED
=========================
This session's shipped defect. Four worked examples — ``rational_mul`` and three
``*_series_truncate`` ops — had been RAISING ``TypeError: 'Q' object is not
subscriptable`` ever since the exact-ℚ arm made those ops return a ``Q``. The
committed ``tests/worked_examples_result.ndjson`` recorded them ``ok``, because
it had not been re-run since the flip. Those snippets ship via ``_tool_docs.py``
-> ``ToolEntry.example`` -> the MCP tool list and the
compiled-in C registry. Fixed at 17 sites; this hook is what keeps it fixed.

⚠️ THE DESIGNED MECHANISM WAS WRONG, AND MEASURING IT IS WHY THIS HOOK DIFFERS
==============================================================================
The hook was specified as "the rows already carry per-op ``src_sha256``;
recompute each recorded op's current SOURCE hash". The field does exist, but it
does not hash the source. ``tools/run_worked_examples.py`` defines it as::

    def src_sha256(example):
        raw = (example.get("setup") or "") + "\\0" + example["worked"]
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

— the hash of the SNIPPET TEXT. So a hook keyed on it could not have caught the
defect it was written for: ``rational_mul``'s snippet never changed a byte. What
changed was the implementation underneath it.

This is not a hypothetical, and it was not free. ``run_worked_examples.py``
carried a scoping flag built on exactly that key -- it selected rows where
``prior[name]["src_sha256"] != job["src_sha256"]`` -- so it inherited the whole
blind spot and would NOT have re-run ``rational_mul`` after the ℚ flip either.
An instrument that cannot return otherwise is not a measurement, and
snippet-hash equality cannot return "stale" for an implementation-side change.
rc469 (`#T1188`) removed that flag rather than leave it standing beside this
hook for a reader to choose between; ``run_worked_examples.py``'s own docstring
records why.

THE PREDICATE THIS HOOK ACTUALLY USES
=====================================
**A ledger row is unverified if the module that DEFINES its op has changed
since that row was measured.** Three clauses, OR-ed; a row is stale if any
fires:

  1. CONTENT   — the row carries ``def_module`` + ``def_blob``, and the current
                 HEAD blob of that module's file differs from the stamp.
  2. DIRTY     — that module's file differs from HEAD in the working tree.
  3. PUBLISHED — (the original rule, kept) any module changed between the
                 ledger's own commit and HEAD matches the row's PUBLISHED name
                 under ``n == m or n.startswith(m + ".")``.

Per-row scoping keeps the tax proportional: a change to one module never
demands the full 651-snippet run.

⚠️ CLAUSE 3 ALONE WAS BLIND TO A QUARTER OF ITS OWN POPULATION (rc468, `#T1188`)
================================================================================
``srmech.cascade.compensated_sum`` is DEFINED in ``srmech.cascade.composites``
and re-exported by ``srmech/cascade/__init__.py``. Editing ``composites.py``
maps to the module ``srmech.cascade.composites``, and
``"srmech.cascade.compensated_sum".startswith("srmech.cascade.composites.")``
is False — so the hook claimed **ZERO** of that file's own rows and exited 0
with no output at all. Reproduced end-to-end against the real hook before the
fix.

MEASURED on this tree at rc468, over all 651 rows resolved through
``srmech._resolve.resolve_dotted_callable``: **165 rows (25.3%) across 64
defining modules** were invisible to clause 3. The blindness is all-or-nothing
per module — those 64 select ZERO of their own rows, and not one module is
mixed — so a spot check on any visible module could never have found it. The
worst offenders: ``cayley_dickson`` 20, ``composites`` 18, ``cd_register`` 14,
``hypercomplex_dft`` 12, ``leaves`` 12, plus 39 single-row
``signal_processing.closed_form_ops.*`` modules.

⚠️ AND IT MATTERED IN THIS VERY rc: ``srmech/cascade/hypercomplex_dft.py`` holds
the twiddle-carrier ops rc468 changed. Its 12 rows — ``qdft_summand`` and
``odft_summand`` among them — selected **stale=0** under clause 3 alone.

CLAUSE 3 IS KEPT, NOT REPLACED, AND THAT IS LOAD-BEARING
========================================================
Swapping the published-name test for a defining-module test would REGRESS the
other side: every one of those 165 rows is currently claimed by its PACKAGE
``__init__.py``, and only 11 ledger rows in the whole tree are defined directly
in a package ``__init__.py`` (7 in ``srmech.spectral``, 4 in
``srmech.introspect``). Editing ``srmech/cascade/__init__.py`` would drop from
claiming 130 rows to claiming 0. Verified as a union: ``composites.py`` 0 ->
18, ``hypercomplex_dft.py`` 0 -> 12, ``cascade/__init__.py`` 130 -> 130,
``math/rational.py`` 29 -> 29. Strictly additive.

Clause 3 also covers a REBIND that clause 1 cannot see: an ``__init__.py`` edit
that re-exports an op from a different submodule leaves ``def_module`` pointing
at the old file, which has not changed.

WHY A BLOB AND NOT A COMMIT SHA
===============================
``run_worked_examples.py`` stamps the row at RUN time, and at run time HEAD is
still the commit BEFORE the one that lands the change. A commit-sha stamp would
therefore read stale immediately after the natural
edit -> blocked -> re-run -> commit-both loop, and need a second no-op re-run to
clear — the "blocks forever on a provably current ledger" shape that
``write_ledger``'s own comment exists to prevent. A blob is content-derived: it
matches the moment the content matches, in either order, and it survives a
rebase.

A row with no ``def_module`` / ``def_blob`` (a foreign or hand-written ledger)
falls back to clause 3 alone, so nothing that worked before stops working.

WHY GIT AND NOT mtime
=====================
``tools/regen_all.py`` rules mtime out for git-tracked files — "clone, rebase
and ``git checkout`` all set mtimes in arbitrary order, so such a guard
false-fires constantly and gets suppressed, and a suppressed guard is worse
than none". The ledger and the modules are both tracked, so that ruling binds
here. Git object comparison is content-derived and clone-stable.

DELIBERATE BOUNDARY, STATED AS A PREDICATE
==========================================
Changes under ``c/src`` / ``c/include`` are reported as an ADVISORY line and do
not block. They can move a native-dispatched result, but attributing a C change
to individual rows is not decidable from the ledger, so blocking on it would
flag all 651 rows for any C edit — the storm that gets a hook disabled. The
native side has its own instrument: ``stale_native_tripwire.py``.

COST
====
Three git invocations (``log``, ``diff``, ``ls-tree``) plus ONE
``dirty_paths`` (two more), and one NDJSON parse (651 rows). MEASURED at rc468:
**0.69 s warm / 7.69 s cold** Windows-native, **17.2-18.7 s** on the WSL2-9p
mount — where the rc467 hook measured **16.4-17.8 s** in the same session, so
the whole three-clause union costs about **1 s**, which is the added
``ls-tree`` (0.52-0.61 s measured bare). ``dirty_paths`` is measured ONCE and
passed into :func:`_changed_paths`; calling it in both places would double the
most expensive part.

Still **no srmech import and no snippet execution** — that boundary is why the defining module is READ FROM THE ROW
rather than resolved live. Resolving live costs only 0.78 s, so cost is not the
objection; the objection is that ``_hooklib.run_hook`` catches every exception
and exits ALLOW, so a hook that imported srmech would silently pass on any tree
that is mid-edit or syntactically broken — precisely the tree state a Stop hook
runs in.

``_module_of`` reads ``.py`` only. 18 ledger rows have behaviour that partly
lives in a sibling ``.toml`` (the ``[class]`` / ``[tool]`` DSL rung); those are
stamped by their ``.py`` blob and nothing else, which is a declared boundary
rather than an oversight.
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))
import _hooklib as H  # noqa: E402

LEDGER_REL = "docs/srmech/python/tests/worked_examples_result.ndjson"
ARGS_LEDGER_REL = "docs/srmech/python/tests/example_args_ledger.ndjson"
DOCS_REL = "docs/srmech/python/srmech/introspect/_tool_docs.py"
PY_PREFIX = "docs/srmech/python/"
WATCHED = "docs/srmech/python/srmech"
C_WATCHED = ("docs/srmech/c/src", "docs/srmech/c/include")

#: The derived ledgers this hook judges, each against its OWN last commit:
#: ``(repo-relative path, the key a row is named by, label)``. rc473 instrument
#: round (`#T1188`): this was one path, ``LEDGER_REL``, so no revert of the
#: example-args ledger could move the verdict — see the module docstring.
LEDGERS = (
    (LEDGER_REL, "name", "worked-example"),
    (ARGS_LEDGER_REL, "op", "example-args"),
)

MAX_SHOWN = 8


def _module_of(repo_rel_path: str) -> str:
    """``docs/srmech/python/srmech/math/rational.py`` -> ``srmech.math.rational``."""
    if not repo_rel_path.startswith(PY_PREFIX) or not repo_rel_path.endswith(".py"):
        return ""
    rel = repo_rel_path[len(PY_PREFIX):][:-3]          # srmech/math/rational
    parts = [p for p in rel.split("/") if p]
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _changed_paths(root: Path, base: str, dirty: List[str]) -> List[str]:
    """Committed drift since ``base``, plus the ``dirty`` list already measured.

    ⚠️ ``dirty`` is passed IN rather than measured here. :func:`body` needs the
    working-tree drift by itself for clause 2, and ``H.dirty_paths`` costs two
    git invocations — calling it in both places doubled the most expensive part
    of a hook already measured at 4.5-5.7 s on this mount.

    ⚠️ THE WORKING-TREE HALF USED ``git status --porcelain`` AND THAT MADE THIS
    HOOK PLATFORM-DEPENDENT. Measured at rc454, same tree, same commit, nothing
    edited::

        Windows git 2.53.0 :  0 files under srmech/  ->  hook exit 0
        WSL2 git    2.34.1 :  324 files              ->  hook exit 2,
                                                        266 modules "changed",
                                                        all 581 ledger rows
                                                        declared UNVERIFIED

    *(That module count read 263 in the first cut. Predicate, so it can be
    re-measured without WSL: the DISTINCT results of :func:`_module_of` over the
    tracked ``.py`` files under ``docs/srmech/python/srmech`` — because under
    WSL git every one of them reports modified. Measured 266, by two routes
    that agree: the hook's own block message enumerates 8 modules then says
    "(+258 more)", and ``git ls-files`` gives 266 tracked ``.py`` mapping to 266
    distinct modules. Those two figures are the rc454 TREE and are left as
    measured; the same predicate reads **267 modules / 651 rows** at rc468.)*

    WSL2 is the standing build-subagent environment, so under an agent this
    hook blocked EVERY stop, permanently, on a clean tree — the same
    unsatisfiable shape ``stale_native_tripwire`` shipped with at rc452. The
    cause is ``core.autocrlf=true`` living in the Windows user's global config:
    LF blobs against CRLF working files, and WSL git cannot see the setting
    that reconciles them.

    :func:`_hooklib.dirty_paths` asks for a CONTENT difference instead
    (``diff HEAD --numstat --ignore-cr-at-eol``, dropping 0/0 rows). Measured
    on the same tree: **0 under both gits**, and both still report a real
    planted two-line edit. The commit-to-commit half below never needed the
    repair — both sides of ``base..HEAD`` are index blobs, so EOL policy does
    not enter.

    rc473 (`#T1188`): the commit-to-commit half tested ``if code == 0`` and
    otherwise contributed NOTHING, so a git that could not resolve
    ``base..HEAD`` left this reading exactly like "no file changed between
    those commits". It now refuses, the same way :func:`_hooklib.dirty_paths`
    does, and :func:`_hooklib.run_hook` turns that into the documented LOUD
    fail-open rather than a silent verdict.
    """
    seen: List[str] = []
    out = H._git_or_refuse(
        ["diff", "--name-only", f"{base}..HEAD"], root,
        "The commit-to-commit half of the change set would otherwise be "
        "silently empty, so every module touched since the ledger was written "
        "would read as untouched.")
    seen.extend(l.strip() for l in out.splitlines() if l.strip())
    seen.extend(dirty)
    return seen


def _rows(ledger: Path, key: str = "name") -> List[Dict[str, Any]]:
    """Every non-meta row, whole, named by ``key`` (``name`` in the worked-
    example ledger, ``op`` in the example-args ledger). The row carries its own
    ``def_module`` / ``def_blob`` stamp, which is what keeps this hook
    import-free."""
    rows: List[Dict[str, Any]] = []
    try:
        with ledger.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if obj.get("record") == "meta":
                    continue
                if isinstance(obj.get(key), str):
                    obj["_row_name"] = obj[key]
                    rows.append(obj)
    except OSError:
        pass
    return rows


def live_snippet_keys(root: Path) -> Optional[Dict[str, str]]:
    """``{tool name: snippet key}`` of the LIVE generated docs, or ``None`` when
    ``_tool_docs.py`` is absent. (rc473 instrument round, `#T1188`.)

    The key is ``src_sha256`` exactly as both harvesters record it —
    ``tools/run_worked_examples.py::src_sha256`` of the entry's ``example``
    when it carries a ``worked`` snippet, else ``""`` — so a row whose recorded
    key differs from this one records a snippet that no longer ships.

    Still no srmech import: the ``TOOL_DOCS`` literal is read with
    ``ast.parse`` + ``ast.literal_eval``, never executed, so a tree that is
    mid-edit elsewhere cannot make this silently pass. The hash function is
    IMPORTED from ``run_worked_examples`` (stdlib-only at module level), so the
    key has one spelling in the tree and this hook adds no hash call of its
    own. A ``_tool_docs.py`` that parses but carries no ``TOOL_DOCS`` literal
    RAISES: reading no snippets is not the same fact as "no snippet moved", and
    :func:`_hooklib.run_hook` reports the raise as a loud fail-open.
    """
    path = root / DOCS_REL
    if not path.is_file():
        return None
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docs = None
    for node in tree.body:
        target = None
        if isinstance(node, ast.AnnAssign):
            target = node.target
        elif isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
        if isinstance(target, ast.Name) and target.id == "TOOL_DOCS" and node.value is not None:
            docs = ast.literal_eval(node.value)
            break
    if not isinstance(docs, dict):
        raise RuntimeError(
            f"{DOCS_REL} carries no TOOL_DOCS literal, so the snippet clause "
            "cannot read the live snippets, and reading none is not 'no "
            "snippet moved'")
    tools_dir = str(HOOKS_DIR.parent)
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    import run_worked_examples as RWE  # noqa: E402  (stdlib-only at import)
    out: Dict[str, str] = {}
    for name, entry in docs.items():
        example = entry.get("example") if isinstance(entry, dict) else None
        out[name] = (RWE.src_sha256(example)
                     if isinstance(example, dict) and example.get("worked") else "")
    return out


def _head_blobs(root: Path) -> Dict[str, str]:
    """``module -> blob sha at HEAD`` for every tracked ``.py`` under srmech/.

    ONE ``ls-tree`` for the whole subtree; the alternative is one
    ``rev-parse HEAD:<path>`` per distinct module.

    rc473 (`#T1188`): this returned ``{}`` on a git it could not run, which
    makes clause 1 (``blobs[dm] != db``) VACUOUS for every row — ``dm in
    blobs`` is false throughout — so the hook reported no content staleness
    for a reason that had nothing to do with content. It refuses now, exactly
    as ``tools/run_worked_examples.py``'s ``head_blob_map`` already did for
    the same ``ls-tree`` on the same condition.
    """
    out = H._git_or_refuse(
        ["ls-tree", "-r", "HEAD", "--", WATCHED], root,
        "Clause 1 compares each row's def_blob against this map; an empty map "
        "makes that comparison vacuous for every row, which reads as 'nothing "
        "moved'.")
    blobs: Dict[str, str] = {}
    for line in out.splitlines():
        if "\t" not in line:
            continue
        meta, path = line.split("\t", 1)
        parts = meta.split()
        if len(parts) < 3 or parts[1] != "blob":
            continue
        m = _module_of(path.strip().strip('"'))
        if m:
            blobs[m] = parts[2]
    return blobs


def body(payload: Dict[str, Any]) -> int:
    if H.stop_is_repeat(payload):
        return H.allow([
            "[derived-ledger-freshness] WARNING: stop_hook_active — allowing "
            "this stop without re-checking ledger freshness."])

    root = H.repo_root()
    present = [(rel, key, label) for rel, key, label in LEDGERS
               if (root / rel).is_file()]
    if not present:
        return H.allow()

    dirty: Optional[List[str]] = None
    blobs: Optional[Dict[str, str]] = None
    snippet_read = False
    snippet: Optional[Dict[str, str]] = None
    advisory: List[str] = []
    lines: List[str] = []
    blocked = 0
    for rel, key, label in present:
        # rc473 (`#T1188`): the two reasons this can be empty are NOT the same
        # reason, and they used to be spelled the same way. `git log` EXITING
        # NON-ZERO means the instrument could not answer; `git log` succeeding
        # with no output means the ledger has never been committed, which
        # genuinely is "nothing to compare against". Only the second may allow.
        out = H._git_or_refuse(
            ["log", "-1", "--format=%H", "--", rel], root,
            "An unreadable log is not the same fact as an uncommitted ledger, "
            "and allowing on both makes the hook silent exactly when it cannot "
            "see.")
        base = out.strip().splitlines()[-1].strip() if out.strip() else ""
        if not base:
            continue              # never committed: nothing to compare against

        if dirty is None:
            dirty = H.dirty_paths(root, [WATCHED, *C_WATCHED])
            blobs = _head_blobs(root)
        if not snippet_read:
            snippet, snippet_read = live_snippet_keys(root), True
            if snippet is None:
                advisory.append(
                    f"[derived-ledger-freshness] ADVISORY: {DOCS_REL} is absent, "
                    "so the snippet clause was NOT evaluated; clauses 1-3 were.")
        judged = _judge(root, base, dirty, blobs or {}, snippet,
                        _rows(root / rel, key))
        if judged["c_touched"]:
            advisory.append(
                f"[derived-ledger-freshness] ADVISORY: {judged['c_touched']} C "
                f"source file(s) also changed since the {label} ledger was "
                "written. Native-dispatched results may have moved; this hook "
                "does not block on that (see stale_native_tripwire.py).")
        if judged["stale"]:
            blocked += len(judged["stale"])
            lines += _block_lines(rel, key, label, base, judged)

    if not blocked:
        return H.allow(advisory)
    return H.block(lines + advisory + [
        "An instrument that has not been re-run cannot return otherwise: those "
        "rows still record the OLD implementation or the OLD snippet, and they "
        "ship through the MCP tool list and the compiled-in C registry.",
        "",
        "⚠️ Neither key finds the other's rows. The snippet-text hash "
        "(src_sha256) does not move when the implementation moves, which is "
        "exactly how the ℚ-flip defect shipped — clauses 1-3 exist for that. "
        "And a def_blob stamp does not move when a SNIPPET moves — clause 4 "
        "exists for that (rc473). The lists above are printed IN FULL.",
    ])


def _judge(root: Path, base: str, dirty: List[str], blobs: Dict[str, str],
           snippet: Optional[Dict[str, str]],
           rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """One ledger's rows against the four clauses, first clause that fires wins."""
    changed = _changed_paths(root, base, dirty)
    modules: Set[str] = set()
    c_touched: Set[str] = set()
    for p in changed:
        if p.startswith(WATCHED):
            m = _module_of(p)
            if m:
                modules.add(m)
        elif any(p.startswith(c) for c in C_WATCHED):
            c_touched.add(p)
    dirty_modules: Set[str] = {_module_of(p) for p in dirty
                               if p.startswith(WATCHED)}
    dirty_modules.discard("")
    mods_sorted = sorted(modules)

    stale: List[str] = []
    why: Dict[str, str] = {}
    for r in rows:
        n = r["_row_name"]
        dm = r.get("def_module") or ""
        db = r.get("def_blob") or ""
        reason = ""
        if dm and db and dm in blobs and blobs[dm] != db:
            reason = "content"                      # clause 1
        elif dm and dm in dirty_modules:
            reason = "dirty"                        # clause 2
        elif any(n == m or n.startswith(m + ".") for m in mods_sorted):
            reason = "published-name"               # clause 3
        elif snippet is not None and (r.get("src_sha256") or "") != snippet.get(n, ""):
            reason = "snippet"                      # clause 4 (rc473)
        if reason:
            stale.append(n)
            why[n] = reason
    mods = sorted(modules | {r.get("def_module") or "" for r in rows
                             if why.get(r["_row_name"]) in ("content", "dirty")})
    return {"rows": len(rows), "stale": stale, "why": why,
            "modules": [m for m in mods if m], "c_touched": len(c_touched)}


def _block_lines(rel: str, key: str, label: str, base: str,
                 judged: Dict[str, Any]) -> List[str]:
    stale, why, mods = judged["stale"], judged["why"], judged["modules"]
    shown = stale[:MAX_SHOWN]
    more = len(stale) - len(shown)
    tally = {k: sum(1 for v in why.values() if v == k)
             for k in ("content", "dirty", "published-name", "snippet")}
    # ⚠️ THE REMEDY LISTS EVERY STALE ROW, NEVER THE FIRST THREE. Until rc468
    # it printed one `--only <name>` line per row for `shown[:3]`, so following
    # the hook's own instructions on a 55-row block re-ran 3 and left 52 —
    # the hook prescribing the very partial pass it exists to catch. Above 24
    # names the single-command form is written as a `--names-file -` heredoc,
    # because Windows `cmd` truncates an argv beyond 8191 characters and a
    # truncated remedy is a partial pass wearing a complete one's clothes.
    if key == "op":
        remedy = ["    python3 tools/run_example_args.py",
                  "  (it has no scoped form: rc469 removed it, and the harvest "
                  "re-measures every row)"]
    elif len(stale) <= 24:
        remedy = ["    python3 tools/run_worked_examples.py --only "
                  + " ".join(stale)]
    else:
        remedy = ["    python3 tools/run_worked_examples.py --names-file - <<'EOF'"]
        remedy += [n for n in stale]
        remedy += ["EOF"]
    return [
        f"BLOCKED (derived-ledger-freshness): {len(stale)} of {judged['rows']} "
        f"{label} ledger rows are UNVERIFIED — the module defining them, or "
        "the snippet they record, changed after those rows were measured.",
        f"  ledger        : {rel}",
        f"  ledger commit : {base[:12]}",
        f"  by clause     : content={tally['content']} dirty={tally['dirty']} "
        f"published-name={tally['published-name']} snippet={tally['snippet']}",
        f"  module(s): {', '.join(mods[:MAX_SHOWN])}"
        + (f" (+{len(mods) - MAX_SHOWN} more)" if len(mods) > MAX_SHOWN else ""),
        "  unverified rows: " + ", ".join(shown)
        + (f" (+{more} more)" if more > 0 else ""),
        "  Re-run the affected rows — ALL of them, in one pass — then commit the "
        "ledger with the change:",
        *remedy,
        "",
    ]


if __name__ == "__main__":
    H.run_hook(body)
