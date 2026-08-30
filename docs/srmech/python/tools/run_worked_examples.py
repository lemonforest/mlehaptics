#!/usr/bin/env python3
"""``run-worked-examples`` — EXECUTE every ``worked`` snippet in the tool
registry and write the ledger the rc354 gate reads (gh #1530 §K).

    python3 tools/run_worked_examples.py                  # run all, write ledger
    python3 tools/run_worked_examples.py --only-stale     # re-run what changed
    python3 tools/run_worked_examples.py --only <name>    # one snippet
    python3 tools/run_worked_examples.py --print          # human table, no write

WHY THIS EXISTS
===============
``tests/test_worked_examples_strict_zero_rc353.py`` is a **decidable** gate: it
reads three properties off the registry with no re-execution, and its own
docstring says plainly that it "cannot distinguish a captured output from a
typed one — only re-execution can". This is that re-execution. The two are
complements, not competitors, and rc353 stays exactly as it is.

WHAT IT IS NOT: a truth guard on the ``output`` FIELD. It does not compare a
snippet's printed result against the recorded ``output`` text, because that
text is a human-composed rendering in this tree, not a REPL transcript. It
checks that the code RUNS and that every documented raise actually fires.

THE EXPLICIT KEY — and it is already in the tree
================================================
gh #1530 §K asked whether a documented raise should be marked by an explicit
key or found by scanning ``worked`` and ``output``. **Explicit key, and the key
already exists**: the inline ``# -> <ExcType>`` marker, promoted here to
NORMATIVE and matched EXACTLY against the STATEMENT it binds to.

Rejecting the both-field scan is not close. Measured over the whole corpus, 9
snippets carry a raise annotation but die EARLIER from an unrelated cause (5 of
them ``ModuleNotFoundError: tomli``). A scan of the form "this snippet
documents a raise, therefore a raise is a pass" marks all 9 GREEN. That is a
false green in the very test built to stop one — strictly worse than the two
traps §K already records, which only produce false REDS.

The marker binds to a STATEMENT, under two rules, with zero orphans measured:

  1. a trailing comment on the statement's own end line, or
  2. a comment on its own line immediately after the statement.

A marked statement MUST raise that exact type. An unmarked statement must not
raise. Both directions fail loudly, so prose can no longer green anything by
accident: a marker that does not fire is itself a failure.

An ``# -> X`` comment whose ``X`` is NOT an exception type is a VALUE
annotation (``# -> True`` occurs 141 times) and is ignored here.

WHY A SUBPROCESS, AND WHY ONE THAT LIVES
========================================
Three measurements force the shape:

  * ``import srmech`` costs ~0.5 s, so 427 cold subprocesses would be ~200 s of
    pure overhead — hence ONE long-lived worker that imports once;
  * some snippets SPAWN subprocesses (``bus``, ``introspect``), which killed an
    in-process harness outright — hence the worker is a real child that can be
    killed without taking the runner with it;
  * some snippets chdir and write tempfiles — hence cwd and ``sys.path`` are
    restored after every snippet, and the worker is recycled periodically.

The timeout is the PARENT KILLING THE CHILD. Nothing in-process: there is no
reliable way to interrupt arbitrary Python from a thread, ``SIGALRM`` does not
exist on Windows, and the CI matrix has a Windows cell. A process kill cannot
be defeated by a C loop or a blocking socket.

NOT A CODEGEN STEP
==================
This is deliberately not named ``gen_*``, is not in ``codegen_manifest`` and is
not run by ``regen_all``. It produces a **measurement**
(``tests/worked_examples_result.ndjson``) rather than a shipped artifact —
nothing in the wheel derives from it, re-running costs ~250 s, and the result
legitimately DIFFERS between the native and pure cells. Listing it in
``EXCLUDED`` would in fact FAIL ``test_every_generator_is_classified``: that
guard's ``found`` set comes from ``discover_generator_scripts()``, which globs
``gen_*.py`` only, so a non-``gen_`` entry in the manifest is a phantom.
Committed-measurement peer: ``tests/rosetta_classification.ndjson``.

THE CEILING IS PER CI CELL
==========================
Native dispatch changes outcomes — ``primes.is_prime((1<<61)-1)`` is minutes on
the pure trial-division path and fast in C — so the ledger records ``native``
and the gate keys its ceiling on it. Never pin a number measured in one cell
against the other.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

HERE = Path(__file__).resolve().parent
PY_ROOT = HERE.parent
LEDGER = PY_ROOT / "tests" / "worked_examples_result.ndjson"

#: default per-snippet wall budget, seconds.
DEFAULT_BUDGET = 15.0

#: recycle the worker every N snippets even when nothing went wrong —
#: ``register_attested_root`` is global and ``~/.srmech`` bus files persist.
RECYCLE_EVERY = 64

#: measured-slow snippets, each with its reason. "slow" is a RECORDED decision
#: with a number attached, never a silently raised global timeout.
SLOW_ALLOWLIST: Dict[str, Tuple[float, str]] = {
    "srmech.physics.qm.so8.an_embedding": (240.0, "22.5 s measured: g2 = Der(O) branching"),
    "srmech.physics.qm.so8.so7_subalgebra": (240.0, "31.3 s measured: so(7) branching"),
    # rc461 part 3: the note below said the earlier pass "stopped one name too
    # early", and it stopped TWO too early — these are the same cold
    # `_companion_maps()` build, on the so8 side of the wall. MEASURED on this
    # branch, one `--only --budget 240` invocation each, against a 2.5 s
    # harness baseline (`--only srmech.math.cyclic.gcd`): 48.5 s and 46.1 s,
    # both `ok`. At DEFAULT_BUDGET = 15.0 they flip to `timeout` and carry the
    # tally 1 -> 3 against a CEIL of 1 — the same false red, from the same
    # cause. Which snippet pays the build depends on RECYCLE_EVERY worker
    # recycling rather than on the op, so whether these two go red is luck;
    # listing them is what makes it not luck. The ops themselves are fast:
    # epq_frame_address is a memoised sha256 over 28 pairs.
    "srmech.physics.qm.so8.epq_frame_address":
        (240.0, "48.5 s measured COLD: the first _companion_maps() build "
                "reached through the snippet's triality import, not the op"),
    "srmech.physics.qm.so8.g2_membership":
        (240.0, "46.1 s measured COLD: the first _companion_maps() build; "
                "the op itself is 146 ms"),
    # rc461: the op itself is 5.2 ms. What is slow is the FIRST touch of the
    # memoised `_companion_maps()` — 46.7 s measured cold (28 exact 128-unknown
    # solves) — and which snippet pays it depends on worker recycling, not on
    # this op. Listed rather than left to luck: the three so8 entries above it
    # normally warm the cache, but `--only` on this name alone does not.
    "srmech.physics.qm.triality.triality_frame_action":
        (240.0, "46.7 s measured COLD: the first _companion_maps() build; "
                "the op itself is 5.2 ms"),
    # rc461 review: the paragraph above is right, and it stopped one name too
    # early. EVERY triality snippet that reaches `_companion_maps()` pays that
    # cold build when it is the ONLY job in the run — and `--only <name>` is
    # exactly what `tools/hooks/derived_ledger_freshness.py` prescribes when
    # triality.py changes, on precisely these rows. MEASURED on this branch,
    # one `--only` invocation per row, CPython 3.14 / native absent: these
    # three took 16.0 s, 16.6 s and 16.0 s against DEFAULT_BUDGET = 15.0 and
    # flipped `ok` -> `timeout`, while every other triality row finished under
    # 4 s. Committing that ledger would have carried the `timeout` tally from
    # 1 to 4 against a ceiling of 1 in
    # `tests/test_worked_examples_execute_rc354.py` — a false red manufactured
    # by the remediation the hook itself hands you. The snippets are not slow;
    # the isolation is.
    "srmech.physics.qm.triality.triality_automorphism":
        (240.0, "16.0 s measured COLD under --only: the _companion_maps() "
                "build, not the op"),
    "srmech.physics.qm.triality.triality_swap":
        (240.0, "16.6 s measured COLD under --only: the _companion_maps() "
                "build, not the op"),
    "srmech.physics.qm.triality.lean_isa_seventh_primitive":
        (240.0, "16.0 s measured COLD under --only: the _companion_maps() "
                "build, not the op"),
    "srmech.math.laplacian.recover_check": (240.0, "106 s measured: dense recover"),
    "srmech.math.laplacian.recover_check_spectral": (300.0, "244 s measured"),
    "srmech.math.laplacian.recover_check_structural": (240.0, "33 s measured"),
    "srmech.math.laplacian.three_fold_eigvec_groups": (240.0, "dense eigvec pass"),
    "srmech.math.primes.is_prime": (300.0, "206 s on the PURE trial-division "
                                           "path for Mersenne M61; fast in C"),
}

#: snippets that legitimately need a REAL second process. Declared, never
#: silently timed out — a timeout here would be the harness lying about them.
NEEDS_SUBPROCESS = frozenset({
    "srmech.bus.by_name", "srmech.bus.list_endpoints",
    "srmech.introspect.list", "srmech.introspect.by_pid",
})

_MARKER = re.compile(r"#\s*->\s*([A-Za-z_][A-Za-z0-9_]*)")


def _is_exception_name(name: str) -> bool:
    """True for a marker naming an EXCEPTION rather than a value.

    ``# -> True`` (141 occurrences) is a value annotation and must not be read
    as a documented raise. A builtin that is an exception counts; otherwise the
    suffix decides, which is what catches project types like ``ChainSpecError``.
    """
    obj = getattr(__builtins__, name, None) if not isinstance(__builtins__, dict) \
        else __builtins__.get(name)
    if isinstance(obj, type) and issubclass(obj, BaseException):
        return True
    return name.endswith(("Error", "Exception", "Exit"))


def bind_markers(src: str) -> Dict[int, str]:
    """``{statement end_lineno: ExcType}`` for every exception marker.

    Two binding rules, measured to leave zero orphans over the corpus: a
    trailing comment on the statement's end line, or a comment alone on the
    line immediately after it.
    """
    lines = src.split("\n")
    marks: Dict[int, str] = {}
    for i, line in enumerate(lines, start=1):
        m = _MARKER.search(line)
        if m and _is_exception_name(m.group(1)):
            marks[i] = m.group(1)
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return {}
    bound: Dict[int, str] = {}
    for node in tree.body:
        end = getattr(node, "end_lineno", node.lineno)
        if end in marks and lines[end - 1].lstrip().startswith("#") is False:
            bound[end] = marks[end]              # rule 1: trailing comment
        elif end + 1 in marks and lines[end].lstrip().startswith("#"):
            bound[end] = marks[end + 1]          # rule 2: own line after
    return bound


def snippet_source(example: Dict[str, Any]) -> str:
    """``setup`` (shared preamble, if any) concatenated with ``worked``."""
    setup = example.get("setup") or ""
    return (setup + "\n" + example["worked"]) if setup else example["worked"]


def src_sha256(example: Dict[str, Any]) -> str:
    """Per-snippet freshness key. NUL-separated so a byte moving from the end
    of ``setup`` to the front of ``worked`` cannot hash the same."""
    raw = (example.get("setup") or "") + "\0" + example["worked"]
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def collect() -> List[Dict[str, Any]]:
    """Every srmech tool carrying a ``worked`` snippet, from the LIVE schema."""
    sys.path.insert(0, str(PY_ROOT))
    from srmech.introspect.tool_schema import get_tool_schema, warmup_all
    warmup_all()
    out = []
    for t in get_tool_schema().tools:
        ex = t.example
        if t.owner != "srmech" or not isinstance(ex, dict) or not ex.get("worked"):
            continue
        out.append({"name": t.name, "src": snippet_source(ex),
                    "src_sha256": src_sha256(ex),
                    "markers": bind_markers(snippet_source(ex))})
    out.sort(key=lambda r: r["name"])
    return out


# ── the worker child ──────────────────────────────────────────────────────

WORKER_MAIN = r'''
import ast, io as _io, json, os, sys, tempfile, traceback
sys.path.insert(0, {py_root!r})

# THE RECORD CHANNEL is this handle and nothing else. A snippet that calls
# print() would otherwise write NDJSON-adjacent noise onto the same pipe and
# desynchronise the protocol - measured: the first full run died on exactly
# that. So the channel is captured before any snippet runs, and each snippet
# executes with sys.stdout swapped for a throwaway buffer.
_CHAN = sys.stdout
import srmech  # one import, reused for every job
from srmech import _native

# Run from a NEUTRAL directory, never the package root. A snippet that reads
# ``open('srmech/amsc/attested/.../row.ndjson')`` succeeds from
# docs/srmech/python and fails from everywhere a user actually is — running the
# harness where the path happens to resolve would make the gate certify a
# cwd-dependency as working. ``sys.path`` already carries the import root, so
# nothing legitimate needs the package directory to be cwd.
_SANDBOX = tempfile.mkdtemp(prefix="srmech_worked_")
os.chdir(_SANDBOX)

_CHAN.write(json.dumps({{"ready": True,
                        "native": bool(_native.HAS_NATIVE)}}) + "\n")
_CHAN.flush()

for raw in sys.stdin:
    raw = raw.strip()
    if not raw:
        continue
    job = json.loads(raw)
    name, src, markers = job["name"], job["src"], {{int(k): v for k, v in
                                                   job["markers"].items()}}
    os.chdir(_SANDBOX)
    cwd0, path0 = os.getcwd(), list(sys.path)
    g = {{"__name__": "__main__", "__file__": os.path.join(cwd0, "worked_example.py")}}
    rec = {{"name": name, "status": "ok", "statements": 0,
           "markers_fired": [], "problems": []}}
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        rec["status"] = "syntax_error"
        rec["problems"].append({{"kind": "syntax_error", "line": e.lineno,
                                "detail": str(e)}})
        _CHAN.write(json.dumps(rec) + "\n"); _CHAN.flush(); continue
    sys.stdout = _io.StringIO()          # snippet prints go nowhere near _CHAN
    for node in tree.body:
        end = getattr(node, "end_lineno", node.lineno)
        want = markers.get(end)
        mod = ast.Module(body=[node], type_ignores=[])
        ast.fix_missing_locations(mod)
        try:
            exec(compile(mod, "<worked>", "exec"), g)
        except BaseException as e:
            got = type(e).__name__
            if want is not None and got == want:
                rec["markers_fired"].append({{"line": end, "exc": got}})
                rec["statements"] += 1
                continue                      # a documented raise is a PASS
            rec["status"] = "unexpected_raise"
            rec["problems"].append({{
                "kind": "marker_mismatch" if want else "unexpected_raise",
                "line": node.lineno, "expected": want, "got": got,
                "detail": str(e)[:300]}})
            break
        else:
            if want is not None:
                rec["status"] = "marker_did_not_fire"
                rec["problems"].append({{"kind": "marker_did_not_fire",
                                        "line": end, "expected": want}})
                break
            rec["statements"] += 1
    os.chdir(cwd0)
    sys.path[:] = path0
    sys.stdout = _CHAN                   # restore BEFORE the record is written
    _CHAN.write(json.dumps(rec) + "\n")
    _CHAN.flush()
'''


class Worker:
    """A long-lived child that has imported srmech exactly once."""

    def __init__(self) -> None:
        code = WORKER_MAIN.format(py_root=str(PY_ROOT))
        self.p = subprocess.Popen(
            [sys.executable, "-c", code], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            cwd=str(PY_ROOT), text=True, bufsize=1)
        self.q: "queue.Queue[Optional[str]]" = queue.Queue()
        self.t = threading.Thread(target=self._pump, daemon=True)
        self.t.start()
        hello = self.read(30.0)
        self.native = bool(hello and hello.get("native"))

    def _pump(self) -> None:
        assert self.p.stdout is not None
        for line in self.p.stdout:
            self.q.put(line)
        self.q.put(None)

    def read(self, budget: float) -> Optional[Dict[str, Any]]:
        try:
            line = self.q.get(timeout=budget)
        except queue.Empty:
            return None
        if line is None:
            return None
        try:
            return json.loads(line)
        except ValueError:
            # defence in depth: a snippet writing to fd 1 from C bypasses the
            # sys.stdout swap. Drop the noise rather than desynchronise.
            return self.read(budget)

    def send(self, job: Dict[str, Any]) -> None:
        assert self.p.stdin is not None
        self.p.stdin.write(json.dumps(job) + "\n")
        self.p.stdin.flush()

    def kill(self) -> None:
        try:
            self.p.kill()
            self.p.wait(timeout=10)
        except Exception:
            pass


def run(jobs: List[Dict[str, Any]], budget: float) -> Tuple[List[Dict], bool]:
    """Execute every job; return ``(records, native)``. Kills and recycles."""
    worker = Worker()
    native = worker.native
    records: List[Dict[str, Any]] = []
    since_recycle = 0
    for i, job in enumerate(jobs, start=1):
        name = job["name"]
        if name in NEEDS_SUBPROCESS:
            records.append({"name": name, "src_sha256": job["src_sha256"],
                            "status": "needs_subprocess", "statements": 0,
                            "markers_fired": [], "problems": []})
            continue
        limit = SLOW_ALLOWLIST.get(name, (budget, ""))[0]
        worker.send({"name": name, "src": job["src"], "markers": job["markers"]})
        rec = worker.read(limit)
        if rec is None:
            worker.kill()
            worker = Worker()
            since_recycle = 0
            rec = {"name": name, "status": "timeout", "statements": 0,
                   "markers_fired": [], "problems": [
                       {"kind": "timeout", "budget_s": limit}]}
        else:
            since_recycle += 1
            if rec["status"] != "ok" or since_recycle >= RECYCLE_EVERY:
                worker.kill()
                worker = Worker()
                since_recycle = 0
        rec["src_sha256"] = job["src_sha256"]
        rec["n_markers"] = len(job["markers"])
        records.append(rec)
        print("[%3d/%3d] %-14s %s" % (i, len(jobs), rec["status"], name),
              file=sys.stderr)
    worker.kill()
    return records, native


def load_ledger() -> Dict[str, Dict[str, Any]]:
    if not LEDGER.exists():
        return {}
    out = {}
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            if "name" in r:
                out[r["name"]] = r
    return out


def _head_commit() -> str:
    """HEAD's sha at run time, or "" outside a git checkout."""
    try:
        import subprocess
        p = subprocess.run(["git", "rev-parse", "HEAD"],
                           cwd=str(LEDGER.parent), stdout=subprocess.PIPE,
                           stderr=subprocess.DEVNULL, check=False)
        return p.stdout.decode("ascii", "replace").strip() if p.returncode == 0 \
            else ""
    except (OSError, ValueError):
        return ""


def write_ledger(records: List[Dict[str, Any]], native: bool) -> None:
    # ⚠️ `verified_at` EXISTS SO THAT A CONFIRMING RE-RUN IS RECORDABLE (rc452,
    # `#T1166`). tools/hooks/derived_ledger_freshness.py takes the ledger's own
    # LAST COMMIT as its baseline and flags every row whose module changed
    # after it. That works whenever a re-run moves a row — but when the re-run
    # confirms that NOTHING moved, the file content is byte-identical, there is
    # nothing to stage, the ledger's commit cannot advance, and the hook blocks
    # forever on a ledger that is provably current. Measured here: the rc452
    # compose.py change left all four srmech.cascade.compose rows byte-identical
    # (480 ok / 96 unexpected_raise / 4 needs_subprocess / 1 timeout, unchanged),
    # and the hook could not be cleared by doing the very thing it asked for.
    # Stamping HEAD makes "I re-ran and it did not move" a committable fact
    # rather than an unrepresentable one.
    lines = [json.dumps({"record": "meta", "native": native,
                         "python": "%d.%d" % sys.version_info[:2],
                         "verified_at": _head_commit(),
                         "n": len(records)}, sort_keys=True)]
    for r in sorted(records, key=lambda r: r["name"]):
        lines.append(json.dumps(r, sort_keys=True))
    LEDGER.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only-stale", action="store_true")
    ap.add_argument("--only", default=None)
    ap.add_argument("--print", dest="show", action="store_true")
    ap.add_argument("--budget", type=float, default=DEFAULT_BUDGET)
    args = ap.parse_args()

    jobs = collect()
    prior = load_ledger()
    if args.only:
        jobs = [j for j in jobs if j["name"] == args.only]
    elif args.only_stale:
        jobs = [j for j in jobs
                if prior.get(j["name"], {}).get("src_sha256") != j["src_sha256"]]
        print("stale: %d snippet(s)" % len(jobs), file=sys.stderr)

    t0 = time.time()
    records, native = run(jobs, args.budget)
    elapsed = time.time() - t0

    if args.only or args.only_stale:
        merged = dict(prior)
        for r in records:
            merged[r["name"]] = r
        # drop rows for snippets that no longer exist
        live = {j["name"] for j in collect()}
        records = [v for k, v in merged.items() if k in live]

    from collections import Counter
    tally = Counter(r["status"] for r in records)
    print("\n%d snippets in %.1f s: %s" % (len(records), elapsed, dict(tally)),
          file=sys.stderr)
    if args.show:
        for r in sorted(records, key=lambda r: r["name"]):
            if r["status"] != "ok":
                print("%-22s %s %s" % (r["status"], r["name"],
                                       r["problems"][:1]))
        return 0
    write_ledger(records, native)
    print("wrote %s" % LEDGER, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
