"""Stop / SubagentStop — the worked-examples ledger must not claim results it
has not re-measured. (rc452, `#T1166`)

WHAT IT CATCHES, MEASURED
=========================
This session's shipped defect. Four worked examples — ``rational_mul`` and three
``*_series_truncate`` ops — had been RAISING ``TypeError: 'Q' object is not
subscriptable`` ever since the exact-ℚ arm made those ops return a ``Q``. The
committed ``tests/worked_examples_result.ndjson`` recorded them ``ok``, because
it had not been re-run since the flip. Those snippets ship via ``_tool_docs.py``
-> ``ToolEntry.example`` -> ``describe()``, the MCP tool list and the
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
**A ledger row is unverified if the module that defines its op has changed
since the ledger was last written.** Concretely:

  base    = git log -1 --format=%H -- <ledger>        (the ledger's own commit)
  changed = files under docs/srmech/python/srmech/ that differ between base and
            HEAD, PLUS any with uncommitted working-tree modifications
  stale   = ledger rows whose dotted name falls under a changed module

``srmech/math/rational.py`` maps to ``srmech.math.rational`` and claims every
row named ``srmech.math.rational.*`` — which is exactly the set the ℚ flip
invalidated. Per-row scoping keeps the tax proportional: a change to one module
never demands the full 581-snippet run.

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
flag all 581 rows for any C edit — the storm that gets a hook disabled. The
native side has its own instrument: ``stale_native_tripwire.py``.

COST
====
Two git invocations and one NDJSON parse (581 rows). No srmech import, no
snippet execution.
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


def _changed_paths(root: Path, base: str) -> List[str]:
    seen: List[str] = []
    code, out = H.git(["diff", "--name-only", f"{base}..HEAD"], cwd=root)
    if code == 0:
        seen.extend(l.strip() for l in out.splitlines() if l.strip())
    code, out = H.git(["status", "--porcelain", "--", WATCHED, *C_WATCHED], cwd=root)
    if code == 0:
        for line in out.splitlines():
            line = line.rstrip()
            if len(line) > 3:
                seen.append(line[3:].strip().strip('"'))
    return seen


def _rows(ledger: Path) -> List[str]:
    names: List[str] = []
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
                n = obj.get("name")
                if isinstance(n, str):
                    names.append(n)
    except OSError:
        pass
    return names


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

    changed = _changed_paths(root, base)
    modules: Set[str] = set()
    c_touched: Set[str] = set()
    for p in changed:
        if p.startswith(WATCHED):
            m = _module_of(p)
            if m:
                modules.add(m)
        elif any(p.startswith(c) for c in C_WATCHED):
            c_touched.add(p)

    advisory: List[str] = []
    if c_touched:
        advisory.append(
            f"[derived-ledger-freshness] ADVISORY: {len(c_touched)} C source "
            "file(s) also changed since the ledger was written. Native-dispatched "
            "results may have moved; this hook does not block on that (see "
            "stale_native_tripwire.py).")

    if not modules:
        return H.allow(advisory)

    names = _rows(ledger)
    stale = [n for n in names
             if any(n == m or n.startswith(m + ".") for m in sorted(modules))]

    if not stale:
        return H.allow(advisory)

    shown = stale[:MAX_SHOWN]
    more = len(stale) - len(shown)
    mods = sorted(modules)
    return H.block([
        f"BLOCKED (derived-ledger-freshness): {len(stale)} of {len(names)} "
        "worked-example ledger rows are UNVERIFIED — the modules defining them "
        "changed after the ledger was last written.",
        f"  ledger commit : {base[:12]}",
        f"  changed module(s): {', '.join(mods[:MAX_SHOWN])}"
        + (f" (+{len(mods) - MAX_SHOWN} more)" if len(mods) > MAX_SHOWN else ""),
        "  unverified rows: " + ", ".join(shown)
        + (f" (+{more} more)" if more > 0 else ""),
        *advisory,
        "",
        "An instrument that has not been re-run cannot return otherwise: those "
        "rows still record the status of the OLD implementation, and they ship "
        "through describe(), the MCP tool list and the compiled-in C registry.",
        "",
        "Re-run the affected snippets, then commit the ledger with the change:",
        *[f"    python3 tools/run_worked_examples.py --only {n}" for n in shown[:3]],
        "    # or, for a whole module's worth, re-run and let the merge keep the rest",
        "",
        "⚠️ `--only-stale` will NOT select these: it compares the snippet-text "
        "hash (src_sha256), which does not move when the implementation moves. "
        "That blind spot is exactly how the ℚ-flip defect shipped.",
    ])


if __name__ == "__main__":
    H.run_hook(body)
