"""rc430 (`#T1127` / `#T1094`) — regenerate ``tests/example_args_ledger.ndjson``.

Executes each ToolEntry's published ``example["worked"]`` snippet with the op
wrapped in a recorder and banks the arguments of the calls that RETURNED. See
``tools/example_args.py`` for why an argument recovered this way is valid **by
construction** and why ``example["input"]`` is NOT an argument source.

Usage::

    python3 tools/run_example_args.py                 # full regeneration
    python3 tools/run_example_args.py --only-stale     # re-harvest what changed

HARNESS INTEGRITY IS A CONTROL, NOT A CONVENIENCE
-------------------------------------------------
The rc430 scope round recorded a run in which **251 of 533 probes returned
``WORKER_DIED`` and the process still exited 0 with every named control
passing**, because each control op happened to be probed before the cascade
started. A control set that a half-dead run satisfies is not a control set.
So: every worker death / timeout / skip is written into the ledger as its own
status, the meta row carries the counts, and
``tests/test_synth_args_provenance_rc430.py`` asserts on them. A snippet can
fail; it cannot fail SILENTLY.

Each worker also runs in a **PID-unique private temp directory**, so a snippet
that writes relative paths cannot litter the package tree or collide with a
sibling worker — the same isolation the scope round had to add after the fact.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

PY_ROOT = Path(__file__).resolve().parents[1]
TOOLS = PY_ROOT / "tools"
for _p in (str(PY_ROOT), str(TOOLS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import example_args as ea                      # noqa: E402
import run_worked_examples as rwe               # noqa: E402

DEFAULT_BUDGET = 20.0
RECYCLE_EVERY = 64

#: The child. Reads op names on stdin, writes one \x01-prefixed JSON line each.
CHILD_SRC = r'''
import json, os, sys, tempfile
sys.path.insert(0, %(py_root)r)
sys.path.insert(0, %(tools)r)
os.chdir(tempfile.mkdtemp(prefix="srmech_ea_%%d_" %% os.getpid()))
import example_args as ea
from srmech.introspect.tool_schema import get_tool_schema, warmup_all
warmup_all()
BY_NAME = {t.name: t for t in get_tool_schema().tools}
for line in sys.stdin:
    nm = line.strip()
    if not nm:
        continue
    e = BY_NAME.get(nm)
    if e is None:
        rec = {"op": nm, "status": "absent_from_registry", "args": {},
               "unserializable": [], "n_calls": 0, "error": None}
    else:
        try:
            rec = ea.harvest_op(nm, e.example)
        except BaseException as exc:
            rec = {"op": nm, "status": "harvest_error", "args": {},
                   "unserializable": [], "n_calls": 0,
                   "error": type(exc).__name__ + ": " + str(exc)[:200]}
    sys.stdout.write("\x01" + json.dumps(rec, sort_keys=True) + "\n")
    sys.stdout.flush()
'''


class Worker:
    """A killable long-lived child. Nothing in-process can interrupt arbitrary
    Python reliably; a process kill cannot be defeated by a C loop."""

    def __init__(self, src_path: str, env: Dict[str, str]) -> None:
        self.src_path = src_path
        self.env = env
        self.proc: Optional[subprocess.Popen] = None
        self.q: List[str] = []
        self.lock = threading.Lock()
        self._start()

    def _start(self) -> None:
        self.proc = subprocess.Popen(
            [sys.executable, "-u", self.src_path],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, env=self.env,
            cwd=tempfile.mkdtemp(prefix="srmech_ea_parent_"),
        )
        self.q = []
        self.lock = threading.Lock()
        t = threading.Thread(target=self._read, args=(self.proc,), daemon=True)
        t.start()

    def _read(self, proc: subprocess.Popen) -> None:
        for line in proc.stdout:            # type: ignore[union-attr]
            if line.startswith("\x01"):
                with self.lock:
                    self.q.append(line[1:])

    def kill(self) -> None:
        try:
            if self.proc is not None:
                self.proc.kill()
        except Exception:
            pass

    def ask(self, name: str, budget: float) -> Dict[str, Any]:
        blank = {"op": name, "args": {}, "unserializable": [], "n_calls": 0}
        try:
            self.proc.stdin.write(name + "\n")   # type: ignore[union-attr]
            self.proc.stdin.flush()              # type: ignore[union-attr]
        except Exception:
            self.kill()
            self._start()
            return dict(blank, status="worker_restart", error="stdin closed")
        t0 = time.monotonic()
        while time.monotonic() - t0 < budget:
            with self.lock:
                if self.q:
                    return json.loads(self.q.pop(0))
            if self.proc.poll() is not None:     # type: ignore[union-attr]
                self.kill()
                self._start()
                return dict(blank, status="worker_died", error="child exited")
            time.sleep(0.01)
        self.kill()
        self._start()
        return dict(blank, status="timeout", error=f"budget {budget}s")


def collect() -> List[Dict[str, str]]:
    """Every srmech-owned tool, with its freshness key.

    Ops with NO worked snippet are collected too, with an empty key — the
    ledger must record them as ``no_worked_snippet`` rather than omit them,
    or its op set would silently disagree with the registry and the freshness
    gate would have nothing to compare.
    """
    from srmech.introspect.tool_schema import get_tool_schema, warmup_all
    warmup_all()
    out = []
    for t in get_tool_schema().tools:
        if t.owner != "srmech":
            continue
        ex = t.example if isinstance(t.example, dict) else None
        key = rwe.src_sha256(ex) if (ex and ex.get("worked")) else ""
        out.append({"name": t.name, "src_sha256": key})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only-stale", action="store_true")
    ap.add_argument("--budget", type=float, default=DEFAULT_BUDGET)
    args = ap.parse_args()

    import srmech
    print(f"srmech.__file__    = {srmech.__file__}", file=sys.stderr)
    print(f"srmech.__version__ = {srmech.__version__}", file=sys.stderr)

    jobs = collect()
    previous = ea.load_ledger()
    fresh: Dict[str, Dict[str, Any]] = {}
    todo = []
    for j in jobs:
        old = previous.get(j["name"])
        if (args.only_stale and old is not None
                and old.get("src_sha256") == j["src_sha256"]):
            fresh[j["name"]] = old
            continue
        todo.append(j)
    print(f"{len(todo)} to harvest, {len(fresh)} reused", file=sys.stderr)

    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(PY_ROOT), str(TOOLS), env.get("PYTHONPATH", "")]).rstrip(os.pathsep)
    env.setdefault("SRMECH_EXPECT_PURE", "1")

    child = Path(tempfile.mkdtemp(prefix="srmech_ea_src_")) / "child.py"
    child.write_text(CHILD_SRC % {"py_root": str(PY_ROOT), "tools": str(TOOLS)},
                     encoding="utf-8")

    worker = Worker(str(child), env)
    records: List[Dict[str, Any]] = list(fresh.values())
    since = 0
    for i, j in enumerate(todo, 1):
        name = j["name"]
        if name in rwe.NEEDS_SUBPROCESS:
            rec = {"op": name, "status": "needs_subprocess", "args": {},
                   "unserializable": [], "n_calls": 0, "error": None}
        else:
            budget = rwe.SLOW_ALLOWLIST.get(name, (args.budget, ""))[0]
            rec = worker.ask(name, budget)
            since += 1
            if since >= RECYCLE_EVERY:
                worker.kill()
                worker._start()
                since = 0
        rec["src_sha256"] = j["src_sha256"]
        records.append(rec)
        if i % 50 == 0:
            print(f"  {i}/{len(todo)}", file=sys.stderr)
    worker.kill()

    by_status: Dict[str, int] = {}
    for r in records:
        by_status[r.get("status", "?")] = by_status.get(r.get("status", "?"), 0) + 1
    meta = {
        "n": len(records),
        "n_with_args": sum(1 for r in records if r.get("args")),
        "by_status": by_status,
        "srmech_version": srmech.__version__,
        "python": f"{sys.version_info[0]}.{sys.version_info[1]}",
    }
    ea.write_ledger(records, meta)
    print(json.dumps(meta, sort_keys=True), file=sys.stderr)
    print(f"wrote {ea.LEDGER}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
