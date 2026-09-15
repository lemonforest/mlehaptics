"""The derived ledgers' defining-module stamp, COMPARED rather than only present.
(rc473 instrument round, `#T1188`)

ONE home for the two comparisons ``tests/test_worked_examples_execute_rc354.py``
and ``tests/test_synth_args_provenance_rc430.py`` each run over their own ledger.
It is not a test module (no ``test_`` prefix, no assertions).

WHY THIS EXISTS
---------------
Both ledgers stamp every row with ``def_module`` (where the op is DEFINED) and
``def_blob`` (that file's git blob when the row was measured). Both freshness
gates compared ``src_sha256`` alone — the hash of the SNIPPET TEXT, which does
not move when an implementation does — and ``def_blob`` was asserted non-empty
and never compared (the rc470 note said so and handed the comparison to the
Stop hook, which did not read the example-args ledger at all). So a ledger
stale ONLY in ``def_blob`` passed every check in the tree.

TWO COMPARISONS, KEPT APART, because only one of them can depend on the cell:

* :func:`stale_def_blobs` — each row's RECORDED ``(def_module, def_blob)``
  against that module's blob at HEAD, read by the harvester's own
  ``tools/run_worked_examples.head_blob_map`` (one ``git ls-tree``). It reads
  git and the ledger and resolves nothing, so it is the same comparison on
  every interpreter. The caller skips it only where no ``.git`` exists above
  the package (an sdist cell); in a checkout git cannot read,
  ``head_blob_map`` RAISES, and that is a failure, not a skip.
* :func:`moved_def_modules` — each op re-resolved on the RUNNING cell, its
  ``__module__`` against the recorded ``def_module``, with the harvester's own
  spelling (``resolve_dotted_callable(name).__module__``). It compares on every
  cell and is never skipped: a difference fails wherever it is observed, with
  the running cell and the ledger's declared cell both named. A skip on an
  undeclared cell would have been the easier shape, and it would not be
  audited — CI's skip audit counts only ``pure-by-design:`` reasons.

A consequence worth stating, because the blob half now ENFORCES it: the stamp is
``git ls-tree HEAD``, so a harvest run before the module edit is committed
stamps the old blob, and this reds until the ledger is re-harvested after that
commit. That is the "ledgers LAST, in their own commit" order.

numpy-free. No ``abs()``. No ``hashlib``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

PY_ROOT = Path(__file__).resolve().parents[1]


def load(ledger: Path, key: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """``(meta row, every other row)`` of an NDJSON ledger whose rows carry ``key``."""
    meta: Dict[str, Any] = {}
    rows: List[Dict[str, Any]] = []
    for line in ledger.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        if obj.get("record") == "meta":
            meta = obj
        elif key in obj:
            rows.append(obj)
    return meta, rows


def in_a_checkout() -> bool:
    """True when a ``.git`` (directory or worktree pointer) sits above the package."""
    return any((d / ".git").exists() for d in (PY_ROOT, *PY_ROOT.parents))


def head_blob_map() -> Dict[str, str]:
    """The harvester's own ``module -> blob at HEAD`` map (raises if git cannot answer)."""
    tools = str(PY_ROOT / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    import run_worked_examples as rwe
    return rwe.head_blob_map()


def stale_def_blobs(rows: List[Dict[str, Any]], key: str,
                    blobs: Dict[str, str]) -> List[Tuple[str, str, str, str]]:
    """``(row, def_module, recorded blob, HEAD blob)`` for every stamped row whose
    recorded blob is not its recorded module's blob at HEAD, sorted."""
    out = []
    for r in rows:
        module = r.get("def_module") or ""
        if not module:
            continue
        recorded, head = r.get("def_blob") or "", blobs.get(module) or ""
        if recorded != head:
            out.append((r[key], module, recorded[:12] or "<none>", head[:12] or "<no blob>"))
    return sorted(out)


def cell() -> Tuple[str, bool]:
    """``("3.12", HAS_NATIVE)`` — the running interpreter and native state."""
    from srmech import _native
    return "%d.%d" % sys.version_info[:2], bool(_native.HAS_NATIVE)


def moved_def_modules(rows: List[Dict[str, Any]], key: str) -> List[Tuple[str, str, str]]:
    """``(row, recorded def_module, live __module__)`` for every row that
    resolves elsewhere on this cell, sorted. Spelled as ``run_worked_examples.
    collect`` spells it, unresolvable reading as ``""``."""
    from srmech._resolve import resolve_dotted_callable
    from srmech.introspect.tool_schema import warmup_all

    warmup_all()
    out = []
    for r in rows:
        try:
            live = getattr(resolve_dotted_callable(r[key]), "__module__", "") or ""
        except Exception:  # noqa: BLE001 — unresolvable is the harvester's "" too
            live = ""
        recorded = r.get("def_module") or ""
        if live != recorded:
            out.append((r[key], recorded, live))
    return sorted(out)
