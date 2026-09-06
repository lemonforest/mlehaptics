#!/usr/bin/env python3
"""``run-worked-examples`` — EXECUTE every ``worked`` snippet in the tool
registry and write the ledger the rc354 gate reads (gh #1530 §K).

    python3 tools/run_worked_examples.py                  # run all, write ledger
    python3 tools/run_worked_examples.py --only-stale     # re-run what changed
    python3 tools/run_worked_examples.py --only A B C     # N snippets, by name
    python3 tools/run_worked_examples.py --names-file -   # N names on stdin
    python3 tools/run_worked_examples.py --backfill       # stamp only, no run
    python3 tools/run_worked_examples.py --print          # human table, no write

THE SILENT PARTIAL PASS, AND WHY ``--only`` NOW TAKES N NAMES (rc468, `#T1188`)
===============================================================================
``--only`` accepted exactly ONE name for its whole life, so every by-name
re-run this arc has done -- rc465 (71 rows), rc466 (475, then 3, then 71),
rc467 (9, then 55) -- was necessarily driven by a CALLER-WRITTEN LOOP that this
tool never checked. Twice in rc467 that loop was the shell idiom
``while read -r n; do ...; done < names.txt``, which DROPS THE FINAL LINE when
the file has no trailing newline: one pass silently covered 70 of 71, another
54 of 55, and the row the second one missed was ``quaternion_twiddle`` -- one of
the very ops that rc's change was about. Both were caught only by diffing
ran-against-wanted afterwards.

Note what a count assertion built on ``wc -l`` would have done. MEASURED on a
3-line file with no trailing newline (WSL2, bash 5.1.16): ``while read`` yields
2 and ``wc -l`` also yields 2. The broken loop and the naive check AGREE, so
the check cannot fail. (``grep -c .`` yields 3, which is why the rc467 catch
worked -- it compared against a newline-independent count.)

Three things changed here, and only the third is a class guard:

  1. ``--only`` takes N names and ``--names-file PATH|-`` reads a list --
     through Python line iteration, which never drops an unterminated final
     line -- so there is no longer a REASON to write the loop.
  2. A requested name absent from the live registry is a HARD FAIL (exit 2,
     names listed), never a silent empty pass; and after the run the tool
     asserts ``{recorded names} == {requested names}`` before it writes.
     It prints ``requested=N ran=N merged=M`` -- three numbers, because the
     summary line below reports the MERGED ledger size and a reader watching
     only that could not tell 55 rows from 3.
  3. THE CLASS GUARD is the per-row stamp: every record carries ``def_module``
     (the module that DEFINES the op, not the one it is published under) and
     ``def_blob`` (that file's git blob at run time). A row a driver dropped
     keeps its OLD blob, so ``tools/hooks/derived_ledger_freshness.py`` names
     it at the next Stop -- whatever drove the partial pass, and even if the
     drop happened outside this process entirely.

(1) and (2) cannot see a name a caller's loop never sent. (3) can, because it
is a property of the LEDGER rather than of the run.

WHY ``def_module`` AND NOT THE PUBLISHED NAME
=============================================
``srmech.cascade.compensated_sum`` is DEFINED in ``srmech.cascade.composites``
and re-exported by ``srmech/cascade/__init__.py``. Matching a row to a changed
module by its published name -- ``n == m or n.startswith(m + ".")`` -- therefore
misses it entirely. MEASURED on this tree at rc468: **165 of 651 rows (25.3%)**
are invisible to that test, across **64 defining modules**, and the blindness is
all-or-nothing per module (those 64 select ZERO of their own rows; not one
module is mixed). Recording the defining module IN THE ROW keeps the hook
import-free and lets it match on the relation that actually holds.

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

#: repo root, and the two path constants the freshness hook uses verbatim.
#: They are spelled the same in both files on purpose: the hook resolves a
#: row's ``def_module`` back to a path with exactly this rule, so a divergence
#: would make the stamp unreadable rather than wrong-and-loud.
REPO_ROOT = PY_ROOT.parents[2]
PY_PREFIX = "docs/srmech/python/"
WATCHED = "docs/srmech/python/srmech"

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
    # rc466 (`#T1188`): the FOURTH instance, found by the freshness hook's own
    # by-name remediation after the seventy-row drain touched 33 modules.
    # This snippet's FIRST line is `so8_bracket_certificate(triality_swap())`,
    # so it pays the cold `_companion_maps()` build whenever it is the first
    # job in its worker — which `--only` makes certain and which the 475-row
    # by-module re-run also produced (`ok` at rc465 was a WARM reading: an
    # earlier snippet in the same worker had paid the build). MEASURED on
    # this branch, WSL2 CPython 3.10: `triality_swap()` cold is 87.5 s with
    # the native lib loaded and 50.8 s with it off (the native-on excess is
    # `_try_c_two_rationals` on bignum operands, pre-existing: 53.1 s cold at
    # the ledger's base commit 73c089d8a in a pure-cell worktree — this rc
    # changed nothing in that path); the three 378-pair sweeps the snippet
    # then runs are ~7 s together and every marker fires. Same cause, same
    # ruling: listed with its number rather than left to worker-recycling luck.
    "srmech.physics.qm.so8.so8_bracket_certificate":
        (240.0, "87.5 s measured COLD (native on; 50.8 s native off): the first "
                "_companion_maps() build behind triality_swap(), not the sweep"),
    "srmech.math.laplacian.recover_check": (240.0, "106 s measured: dense recover"),
    # rc462: raised 300.0 -> 600.0. The recorded 244 s was a WARM number and
    # this row now flips `ok` -> `timeout` under the isolation the hook itself
    # prescribes. MEASURED on this branch, CPython 3.14 / native absent: the
    # snippet BODY is 225.0 s executed directly with the registry already
    # imported, but the `--only` worker imports srmech cold first and the run
    # hits the 300.0 cap. Same shape as the five so8/triality entries above —
    # the snippet is not slow, the isolation is — and it is a THIRD instance,
    # so the pattern is now the rule rather than the exception on this file.
    "srmech.math.laplacian.recover_check_spectral":
        (600.0, "225.0 s measured for the snippet body; >300 s under --only "
                "once the worker's cold srmech import is included"),
    # rc462: NOT previously listed, and it needed to be. MEASURED: 13.0 s for
    # the snippet body against DEFAULT_BUDGET = 15.0, but 19.5 s under `--only`
    # — the ~6 s gap is the worker's cold import, so a row that is comfortably
    # inside the budget in a full pass falls outside it in isolation. It is the
    # `#845` comment edits on laplacian.py that made the hook prescribe
    # `--only` here, which is how a row that had never been isolated got
    # isolated for the first time. Listing it is what stops that being luck.
    "srmech.math.laplacian.relational_structure":
        (240.0, "19.5 s measured under --only; 13.0 s for the snippet body "
                "alone, against DEFAULT_BUDGET = 15.0"),
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


def _git(args: List[str]) -> Tuple[int, str]:
    """``git`` in the repo root. Returns ``(code, stdout)``; never raises."""
    try:
        p = subprocess.run(["git", *args], cwd=str(REPO_ROOT),
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                           check=False)
    except (OSError, ValueError):
        return 1, ""
    return p.returncode, p.stdout.decode("utf-8", "replace")


def module_of(repo_rel_path: str) -> str:
    """``docs/srmech/python/srmech/math/rational.py`` -> ``srmech.math.rational``.

    Byte-identical to ``tools/hooks/derived_ledger_freshness.py::_module_of``.
    ``.py`` only: a module whose behaviour partly lives in a sibling ``.toml``
    (18 ledger rows have one) is stamped by its ``.py`` blob and nothing else.
    """
    if not repo_rel_path.startswith(PY_PREFIX) or not repo_rel_path.endswith(".py"):
        return ""
    rel = repo_rel_path[len(PY_PREFIX):][:-3]
    parts = [x for x in rel.split("/") if x]
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def head_blob_map() -> Dict[str, str]:
    """``module -> blob sha at HEAD`` for every tracked ``.py`` under srmech/.

    ONE ``git ls-tree`` for the whole subtree rather than one ``rev-parse`` per
    row. Content-derived, so it survives clone, rebase and ``git checkout`` --
    the same reason ``regen_all`` rules mtime out for tracked files, and the
    reason this is a BLOB and not the commit sha: a commit stamp minted at run
    time predates the commit that lands the change, so the natural
    edit-block-rerun-commit loop would leave every row it just verified
    "stale" and need a second no-op re-run to clear.
    """
    code, out = _git(["ls-tree", "-r", "HEAD", "--", WATCHED])
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
        m = module_of(path.strip().strip('"'))
        if m:
            blobs[m] = parts[2]
    return blobs


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
    """Every srmech tool carrying a ``worked`` snippet, from the LIVE schema.

    Each job also carries ``def_module`` -- the ``__module__`` of the live
    callable, i.e. where the op is DEFINED rather than where it is published --
    and ``def_blob``, that module file's git blob at HEAD. Measured cost of the
    resolution pass: ~0.33 s over 651 names, inside a call that already imports
    srmech and warms the whole schema.
    """
    sys.path.insert(0, str(PY_ROOT))
    from srmech.introspect.tool_schema import get_tool_schema, warmup_all
    from srmech._resolve import resolve_dotted_callable
    warmup_all()
    blobs = head_blob_map()
    out = []
    for t in get_tool_schema().tools:
        ex = t.example
        if t.owner != "srmech" or not isinstance(ex, dict) or not ex.get("worked"):
            continue
        try:
            dm = getattr(resolve_dotted_callable(t.name), "__module__", "") or ""
        except Exception:
            # unresolvable: the row carries no stamp and the hook falls back to
            # its published-name rule for it. MEASURED at rc468: 0 of 651.
            dm = ""
        out.append({"name": t.name, "src": snippet_source(ex),
                    "src_sha256": src_sha256(ex),
                    "markers": bind_markers(snippet_source(ex)),
                    "def_module": dm, "def_blob": blobs.get(dm, "")})
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
                            "def_module": job.get("def_module", ""),
                            "def_blob": job.get("def_blob", ""),
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
        # ⚠️ SET HERE AND NOT ONLY IN collect(). A record that comes back from
        # the worker is a fresh dict, so stamping only at collection time would
        # DROP both fields on every re-run row -- i.e. exactly the rows a
        # by-name pass touches, eroding the guard on its first real use.
        rec["def_module"] = job.get("def_module", "")
        rec["def_blob"] = job.get("def_blob", "")
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


def load_meta() -> Dict[str, Any]:
    """The ledger's ``record: "meta"`` row, or ``{}``."""
    if not LEDGER.exists():
        return {}
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            if r.get("record") == "meta":
                return r
    return {}


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


def write_ledger(records: List[Dict[str, Any]], native: bool,
                 meta_row: Optional[Dict[str, Any]] = None) -> None:
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
    #
    # ``meta_row`` is the --backfill path and it PRESERVES the prior meta row
    # byte for byte. A backfill executes no snippet, so re-stamping
    # ``verified_at`` there would assert a verification that did not happen --
    # the same class of false claim this whole file exists to prevent.
    if meta_row is not None:
        meta = dict(meta_row)
        assert meta.get("n") == len(records), (meta.get("n"), len(records))
    else:
        meta = {"record": "meta", "native": native,
                "python": "%d.%d" % sys.version_info[:2],
                "verified_at": _head_commit(),
                "n": len(records)}
    lines = [json.dumps(meta, sort_keys=True)]
    for r in sorted(records, key=lambda r: r["name"]):
        lines.append(json.dumps(r, sort_keys=True))
    LEDGER.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def read_names(text: str) -> List[str]:
    """One name per line, ``#`` comments and blanks dropped.

    ``str.splitlines()`` is the point of this function: it returns the final
    line whether or not the text ends in a newline. The shell idiom
    ``while read -r n`` does not, and that is the rc467 defect (70 of 71, then
    54 of 55) this reader exists to make unnecessary.
    """
    out: List[str] = []
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


def backfill(all_jobs: List[Dict[str, Any]], prior: Dict[str, Dict[str, Any]],
             meta: Dict[str, Any], show: bool = False) -> int:
    """Stamp ``def_module`` / ``def_blob`` onto existing rows WITHOUT running.

    THE HONESTY PRECONDITION, AND IT IS MACHINE-CHECKED
    ===================================================
    A stamp says "this row was measured against THIS content". A backfill
    measures nothing, so it may only stamp a row whose defining module has not
    moved between the commit the row WAS measured at (``meta.verified_at``) and
    HEAD -- and is clean in the working tree. Any row failing that is NAMED and
    the whole backfill REFUSES with exit 2; the fix is to re-run those rows,
    which is what produces an honest stamp for them.

    This exists because the alternative is a full re-run, and a full re-run is
    host-coupled: ``tests/test_worked_examples_execute_rc354.py`` pins the pure
    cell at ``{unexpected_raise: 96, timeout: 1}`` and records that a
    native-Windows re-run measures **97**, because one snippet hardcodes a
    ``/mnt/d/...`` path. Regenerating merely to acquire a field would trip a
    down-only ceiling for reasons that have nothing to do with the field.
    """
    ref = (meta or {}).get("verified_at") or ""
    if not ref:
        print("REFUSING to backfill: the ledger's meta row carries no "
              "verified_at, so there is no commit its rows were measured at "
              "and no honest content to stamp them with.", file=sys.stderr)
        return 2
    if _git(["cat-file", "-e", ref + "^{commit}"])[0] != 0:
        print("REFUSING to backfill: meta.verified_at %s does not resolve in "
              "this checkout." % ref[:12], file=sys.stderr)
        return 2

    moved = set()
    code, out = _git(["diff", "--name-only", ref + "..HEAD", "--", WATCHED])
    if code == 0:
        moved |= {module_of(l.strip().strip('"')) for l in out.splitlines()
                  if l.strip()}
    code, out = _git(["diff", "HEAD", "--numstat", "--ignore-cr-at-eol", "--",
                      WATCHED])
    if code == 0:
        for line in out.splitlines():
            parts = line.rstrip().split("\t")
            if len(parts) >= 3 and not (parts[0] == "0" and parts[1] == "0"):
                moved.add(module_of(parts[-1].strip().strip('"')))
    code, out = _git(["ls-files", "--others", "--exclude-standard", "--",
                      WATCHED])
    if code == 0:
        moved |= {module_of(l.strip()) for l in out.splitlines() if l.strip()}
    moved.discard("")

    jobs = {j["name"]: j for j in all_jobs}
    absent = sorted(set(jobs) - set(prior))
    if absent:
        print("REFUSING to backfill: %d snippet(s) have no ledger row. A "
              "backfill must not invent a result it never ran:" % len(absent),
              file=sys.stderr)
        for n in absent[:16]:
            print("    " + n, file=sys.stderr)
        return 2

    refuse = sorted(n for n in prior
                    if n in jobs and jobs[n]["def_module"] in moved)
    if refuse:
        print("REFUSING to backfill %d row(s): their defining module changed "
              "between meta.verified_at (%s) and HEAD, so the HEAD blob is NOT "
              "the content they were measured against." % (len(refuse), ref[:12]),
              file=sys.stderr)
        for n in refuse:
            print("    %-58s %s" % (n, jobs[n]["def_module"]), file=sys.stderr)
        print("\nRe-run exactly those rows first -- that is what mints an "
              "honest stamp for them:", file=sys.stderr)
        # Same rule as the freshness hook's remedy: ONE command covering
        # EVERY named row, and above 24 names the heredoc form, because
        # Windows `cmd` truncates an argv past 8191 characters and a
        # truncated remedy is a partial pass wearing a complete one's
        # clothes.
        if len(refuse) <= 24:
            print("    python3 tools/run_worked_examples.py --only "
                  + " ".join(refuse), file=sys.stderr)
        else:
            print("    python3 tools/run_worked_examples.py --names-file "
                  "- <<'EOF'", file=sys.stderr)
            for n in refuse:
                print(n, file=sys.stderr)
            print("EOF", file=sys.stderr)
        return 2

    records, stamped = [], 0
    for name, row in prior.items():
        j = jobs.get(name)
        if j is None:
            print("REFUSING to backfill: ledger row %r is not in the live "
                  "schema. Re-run rather than stamp." % name, file=sys.stderr)
            return 2
        new = dict(row)
        if (new.get("def_module"), new.get("def_blob")) != \
                (j["def_module"], j["def_blob"]):
            stamped += 1
        new["def_module"] = j["def_module"]
        new["def_blob"] = j["def_blob"]
        records.append(new)

    print("backfilled=%d rows=%d (meta row preserved: verified_at=%s)"
          % (stamped, len(records), ref[:12]), file=sys.stderr)
    if show:
        return 0                       # --print never writes, here as elsewhere
    write_ledger(records, bool(meta.get("native")), meta_row=meta)
    print("wrote %s" % LEDGER, file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only-stale", action="store_true")
    ap.add_argument("--only", nargs="+", default=None, metavar="NAME")
    ap.add_argument("--names-file", default=None, metavar="PATH",
                    help="file of names, one per line; '-' reads stdin")
    ap.add_argument("--backfill", action="store_true",
                    help="stamp def_module/def_blob on existing rows; runs nothing")
    ap.add_argument("--print", dest="show", action="store_true")
    ap.add_argument("--budget", type=float, default=DEFAULT_BUDGET)
    args = ap.parse_args()

    all_jobs = collect()
    prior = load_ledger()
    live = {j["name"] for j in all_jobs}

    if args.backfill:
        if args.only or args.names_file or args.only_stale:
            print("REFUSING: --backfill runs nothing, so it cannot be "
                  "combined with a selector.", file=sys.stderr)
            return 2
        return backfill(all_jobs, prior, load_meta(), show=args.show)

    requested: Optional[set] = None
    if args.only:
        requested = set(args.only)
    if args.names_file:
        text = sys.stdin.read() if args.names_file == "-" \
            else Path(args.names_file).read_text(encoding="utf-8")
        requested = (requested or set()) | set(read_names(text))

    jobs = all_jobs
    if requested is not None:
        unknown = sorted(requested - live)
        if unknown:
            print("REFUSING: %d requested name(s) are not in the live "
                  "registry:" % len(unknown), file=sys.stderr)
            for n in unknown:
                print("    " + n, file=sys.stderr)
            print("An unknown --only name used to be a SILENT EMPTY PASS that "
                  "still rewrote the ledger and re-stamped verified_at.",
                  file=sys.stderr)
            return 2
        jobs = [j for j in all_jobs if j["name"] in requested]
    elif args.only_stale:
        jobs = [j for j in all_jobs
                if prior.get(j["name"], {}).get("src_sha256") != j["src_sha256"]]
        requested = {j["name"] for j in jobs}
        print("stale: %d snippet(s)" % len(jobs), file=sys.stderr)

    t0 = time.time()
    records, native = run(jobs, args.budget)
    elapsed = time.time() - t0

    n_ran = len(records)
    if requested is not None:
        ran = {r["name"] for r in records}
        if ran != requested:
            missing = sorted(requested - ran)
            extra = sorted(ran - requested)
            print("REFUSING to write: the run did not cover what was "
                  "requested. missing(%d)=%s extra(%d)=%s"
                  % (len(missing), missing[:8], len(extra), extra[:8]),
                  file=sys.stderr)
            return 2
        merged = dict(prior)
        for r in records:
            merged[r["name"]] = r
        # drop rows for snippets that no longer exist
        records = [v for k, v in merged.items() if k in live]

    from collections import Counter
    tally = Counter(r["status"] for r in records)
    if requested is not None:
        # THREE numbers, deliberately. The line below reports the MERGED
        # ledger size, and a reader watching only that could not tell a 55-row
        # pass from a 3-row one -- which is how two silent partial passes got
        # through rc467.
        print("requested=%d ran=%d merged=%d"
              % (len(requested), n_ran, len(records)), file=sys.stderr)
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
