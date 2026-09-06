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

This is not a hypothetical. The tree's own scoping flag inherits the same blind
spot: ``run_worked_examples.py --only-stale`` selects rows by
``prior[name]["src_sha256"] != job["src_sha256"]``, so ``--only-stale`` would
NOT have re-run ``rational_mul`` after the ℚ flip either. An instrument that
cannot return otherwise is not a measurement, and snippet-hash equality cannot
return "stale" for an implementation-side change.

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

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _hooklib as H  # noqa: E402

LEDGER_REL = "docs/srmech/python/tests/worked_examples_result.ndjson"
PY_PREFIX = "docs/srmech/python/"
WATCHED = "docs/srmech/python/srmech"
C_WATCHED = ("docs/srmech/c/src", "docs/srmech/c/include")

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
    """
    seen: List[str] = []
    code, out = H.git(["diff", "--name-only", f"{base}..HEAD"], cwd=root)
    if code == 0:
        seen.extend(l.strip() for l in out.splitlines() if l.strip())
    seen.extend(dirty)
    return seen


def _rows(ledger: Path) -> List[Dict[str, Any]]:
    """Every non-meta row, whole. The row carries its own ``def_module`` /
    ``def_blob`` stamp, which is what keeps this hook import-free."""
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
                if isinstance(obj.get("name"), str):
                    rows.append(obj)
    except OSError:
        pass
    return rows


def _head_blobs(root: Path) -> Dict[str, str]:
    """``module -> blob sha at HEAD`` for every tracked ``.py`` under srmech/.

    ONE ``ls-tree`` for the whole subtree; the alternative is one
    ``rev-parse HEAD:<path>`` per distinct module.
    """
    code, out = H.git(["ls-tree", "-r", "HEAD", "--", WATCHED], cwd=root)
    if code != 0:
        return {}
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
    ledger = root / LEDGER_REL
    if not ledger.is_file():
        return H.allow()

    code, out = H.git(["log", "-1", "--format=%H", "--", LEDGER_REL], cwd=root)
    base = out.strip().splitlines()[-1].strip() if (code == 0 and out.strip()) else ""
    if not base:
        return H.allow()          # never committed: nothing to compare against

    dirty = H.dirty_paths(root, [WATCHED, *C_WATCHED])
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

    advisory: List[str] = []
    if c_touched:
        advisory.append(
            f"[derived-ledger-freshness] ADVISORY: {len(c_touched)} C source "
            "file(s) also changed since the ledger was written. Native-dispatched "
            "results may have moved; this hook does not block on that (see "
            "stale_native_tripwire.py).")

    rows = _rows(ledger)
    blobs = _head_blobs(root)
    mods_sorted = sorted(modules)

    stale: List[str] = []
    why: Dict[str, str] = {}
    for r in rows:
        n = r["name"]
        dm = r.get("def_module") or ""
        db = r.get("def_blob") or ""
        reason = ""
        if dm and db and dm in blobs and blobs[dm] != db:
            reason = "content"                      # clause 1
        elif dm and dm in dirty_modules:
            reason = "dirty"                        # clause 2
        elif any(n == m or n.startswith(m + ".") for m in mods_sorted):
            reason = "published-name"               # clause 3
        if reason:
            stale.append(n)
            why[n] = reason

    if not stale:
        return H.allow(advisory)

    shown = stale[:MAX_SHOWN]
    more = len(stale) - len(shown)
    mods = sorted(modules | {r.get("def_module") or "" for r in rows
                             if r["name"] in stale
                             and why[r["name"]] != "published-name"})
    mods = [m for m in mods if m]
    tally = {k: sum(1 for v in why.values() if v == k)
             for k in ("content", "dirty", "published-name")}
    # ⚠️ THE REMEDY LISTS EVERY STALE ROW, NEVER THE FIRST THREE. Until rc468
    # it printed one `--only <name>` line per row for `shown[:3]`, so following
    # the hook's own instructions on a 55-row block re-ran 3 and left 52 —
    # the hook prescribing the very partial pass it exists to catch. Above 24
    # names the single-command form is written as a `--names-file -` heredoc,
    # because Windows `cmd` truncates an argv beyond 8191 characters and a
    # truncated remedy is a partial pass wearing a complete one's clothes.
    if len(stale) <= 24:
        remedy = ["    python3 tools/run_worked_examples.py --only "
                  + " ".join(stale)]
    else:
        remedy = ["    python3 tools/run_worked_examples.py --names-file - <<'EOF'"]
        remedy += [n for n in stale]
        remedy += ["EOF"]

    return H.block([
        f"BLOCKED (derived-ledger-freshness): {len(stale)} of {len(rows)} "
        "worked-example ledger rows are UNVERIFIED — the modules defining them "
        "changed after those rows were measured.",
        f"  ledger commit : {base[:12]}",
        f"  by clause     : content={tally['content']} dirty={tally['dirty']} "
        f"published-name={tally['published-name']}",
        f"  module(s): {', '.join(mods[:MAX_SHOWN])}"
        + (f" (+{len(mods) - MAX_SHOWN} more)" if len(mods) > MAX_SHOWN else ""),
        "  unverified rows: " + ", ".join(shown)
        + (f" (+{more} more)" if more > 0 else ""),
        *advisory,
        "",
        "An instrument that has not been re-run cannot return otherwise: those "
        "rows still record the status of the OLD implementation, and they ship "
        "through the MCP tool list and the compiled-in C registry.",
        "",
        "Re-run the affected snippets — ALL of them, in one pass — then commit "
        "the ledger with the change:",
        *remedy,
        "",
        "⚠️ `--only-stale` will NOT select these: it compares the snippet-text "
        "hash (src_sha256), which does not move when the implementation moves. "
        "That blind spot is exactly how the ℚ-flip defect shipped.",
    ])


if __name__ == "__main__":
    H.run_hook(body)
