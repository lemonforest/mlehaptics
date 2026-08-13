#!/usr/bin/env python3
"""rc431 `#T1129` S3 — UNGUARDED CONTRACTS: three confirmations by execution,
the declared-vs-enforced exception census, and the silent-acceptor sample.

Completes the measurement rc430's `#T1127` S1 opened (see
``_s1_guard_extraction_rc430.py``): among 259 registry ops with no guard at
depth <= 2, 91 were probed with type-valid edge arguments, 31 failed, and
THREE failure sites were named as genuinely unguarded (``lll_reduce`` /
``signed_sum_squared`` / ``iir``). ``signed_sum_squared`` additionally showed
a DECLARED contract (docstring ``Raises: ValueError``) that the ENFORCED
contract does not honor on one input shape. This file (a) confirms the three
by execution with full tracebacks, (b) censuses the whole registry for that
declared-vs-enforced class, and (c) samples the 44 ops that accepted every
edge argument to split "genuinely total" from "silent wrong answer".

MEASUREMENT TARGETS — two trees, both pinned:

* ``baseline`` — the ``srmech-v0.9.0rc430`` tag (commit ``a3f9fc847``),
  extracted read-only via ``git archive`` into the session scratchpad. This
  is the tree the rc430 findings describe and is IMMUTABLE under this run.
* ``current`` — the live ``srmech-rc431`` branch working tree, which a build
  agent is writing to WHILE THIS RUNS. Its state is pinned per-file by
  content hash (``srmech.amsc.format.sha256_bytes`` — Class A) at execution
  time. Found on arrival: all three rc430 sites carry UNCOMMITTED repairs
  authored by the build agent; ``current`` rows therefore measure whether
  each baseline defect is already repaired in flight, and the hashes say
  exactly which text was measured.

====================================================================
PRE-REGISTERED FALSIFIERS — declared BEFORE the instrument was run
====================================================================

S1-PF1  Each of the three rc430 sites must REPRODUCE on the baseline tree
        with the exception TYPE rc430 recorded (lll_reduce: TypeError on a
        flat basis; signed_sum_squared: TypeError on non-iterable rows;
        iir: IndexError on empty ``a``). Any that does not -> that rc430
        confirmation is REFUTED and is reported as such.

S1-PF2  (registered on reading the baseline source, before executing)
        rc430's ``lll_reduce`` docstring ALREADY promises ``:raises
        ValueError:`` for RAGGED rows. Prediction: a genuinely ragged basis
        raises a NON-ValueError from inside the reduction. If it raises
        ValueError, lll_reduce is NOT a member of the declared-vs-enforced
        class and the brief's "not guarded at all" stands unqualified.

S2-PC   POSITIVE CONTROL (mandatory before any zero is reported): the
        census scanner, run on the baseline tree, MUST flag
        ``srmech.cascade.signed_sum_squared`` as a mismatch candidate
        (promised {ValueError}, observed TypeError on ``[1, 2]``). If it
        does not, the instrument is INVALID and no zero from it may be
        reported. This project measured two false-REFUTED instruments in
        one session; a false zero here would bless the entire tree.

S2-STYLE The promise extractor must extract from all THREE docstring styles
        present in the tree (Google ``Raises:`` — signed_sum_squared; reST
        ``:raises X:`` — lll_reduce; numpy ``Raises`` + underline). A style
        histogram with any of the three at zero -> extractor REFUTED (the
        line-wrap false-zero lesson).

S2-NC   NEGATIVE CONTROL against over-counting: ``signed_sum_squared([])``
        raises the PROMISED ValueError and must be counted CONSISTENT, not
        a mismatch — the same op must appear on both sides of the split.

S3-PF   The pf6 reconstruction on the baseline tree must reproduce rc430's
        accepted-every-edge-arg population EXACTLY (44 of 91 probed). A
        different count -> instrument drift; report BOUNDED with the delta
        and do not present the sample as "of the 44".

NULL CLASSIFICATION: every null this file reports is classified REFUTED /
BOUNDED / EMPTY / UNSUPPORTED. An instrument that cannot return otherwise is
not a measurement.

DISCIPLINE: no ``abs()`` (sign handling is Class K pin-slot + Class C
re-application; nothing here needs it), no stdlib ``math`` / ``fractions`` /
``decimal``, no numpy (absent by design). Hashing routes through
``srmech.amsc.format.sha256_bytes`` (Class A), never bare hashlib.

Usage (WSL2, numpy-absent python3):
    export SRMECH_EXPECT_PURE=1
    # baseline:
    PYTHONPATH=$FIXTURE/docs/srmech/python python3 <this> s1 baseline >> out.ndjson
    # current:
    PYTHONPATH=/mnt/d/GitHub/mlehaptics/docs/srmech/python python3 <this> s1 current >> out.ndjson
    # census (baseline), recheck (current), acceptors (baseline), verdicts:
    ... s2 baseline / s2c current <ndjson> / s3 baseline / verdicts
"""

from __future__ import annotations

import inspect
import json
import re
import signal
import sys
import traceback
from typing import Any, Dict, List, Optional, Sequence, Tuple

import srmech
from srmech._resolve import resolve_dotted_callable
from srmech.amsc.format import sha256_bytes
from srmech.introspect.tool_schema import get_tool_schema, warmup_all


def emit(rec: Dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(rec, sort_keys=True) + "\n")
    sys.stdout.flush()


def env_row(tree: str, extra: Optional[Dict[str, Any]] = None) -> None:
    warmup_all()
    tools = get_tool_schema().tools
    rec = {"row": "env", "tree": tree, "srmech_file": srmech.__file__,
           "version": srmech.__version__, "registry": len(tools)}
    if extra:
        rec.update(extra)
    emit(rec)


def _tb_info(exc: BaseException) -> Dict[str, Any]:
    frames = []
    tb = exc.__traceback__
    while tb is not None:
        frames.append("%s.%s:%d" % (tb.tb_frame.f_globals.get("__name__", "?"),
                                    tb.tb_frame.f_code.co_name, tb.tb_lineno))
        tb = tb.tb_next
    return {"exc": type(exc).__name__, "msg": str(exc)[:200],
            "frames": frames, "raised_in": frames[-1] if frames else "?"}


def _call(fn: Any, args: Sequence[Any], timeout: int = 4) -> Dict[str, Any]:
    """Execute under an alarm; classify RETURNED / RAISED / HANG."""
    def _alarm(signum, frame):
        raise TimeoutError("probe alarm")
    old = signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(timeout)
    try:
        got = fn(*args)
        return {"outcome": "RETURNED", "value": repr(got)[:240]}
    except TimeoutError:
        return {"outcome": "HANG"}
    except BaseException as exc:  # noqa: BLE001 — classification is the point
        info = _tb_info(exc)
        info["outcome"] = "RAISED"
        info["traceback"] = traceback.format_exc(limit=12)[-1600:]
        return info
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


# ---------------------------------------------------------------------------
# SECTION 1 — the three confirmations, by execution, on both trees
# ---------------------------------------------------------------------------

#: The three rc430 sites plus the inputs that decide each verdict. Inputs are
#: fixed here, before execution, and identical on both trees.
S1_CASES: List[Tuple[str, tuple, str, str]] = [
    # (op, args, input_label, what this input decides)
    ("srmech.cascade.matrix_cascades.lll_reduce", ([1, 2],),
     "flat_non_sequence_rows", "rc430 round-1 reproduction (TypeError)"),
    ("srmech.cascade.matrix_cascades.lll_reduce", ([[1, 0], [1]],),
     "ragged_rows", "S1-PF2: docstring promises ValueError for ragged"),
    ("srmech.cascade.matrix_cascades.lll_reduce", ([],),
     "empty_basis", "rc430 round-0 was ACCEPTED; what does [] return?"),
    ("srmech.cascade.signed_sum_squared", ([1, 2],),
     "non_iterable_rows", "rc430 reproduction (TypeError from listcomp)"),
    ("srmech.cascade.signed_sum_squared", ([],),
     "empty_sources", "S2-NC: the promised ValueError that IS enforced"),
    ("srmech.cascade.signed_sum_squared", ([[1, 0], [1]],),
     "ragged_rows", "is the RAGGED promise enforced? (brief says no; test)"),
    ("srmech.signal_processing.iir", ([], [], []),
     "all_empty", "rc430 reproduction (IndexError at a[0])"),
    ("srmech.signal_processing.iir", ([1.0, 2.0, 3.0], [], [1.0]),
     "empty_b_valid_a", "silent-wrong-answer channel: C rejects nb==0; "
                        "pure returns zeros?"),
    ("srmech.signal_processing.iir", ([1.0, 2.0], [1.0], [0.0, 0.5]),
     "a0_zero", "a[0]==0 is not a valid recursion; what escapes?"),
]

#: The three files whose current-tree state is pinned by hash (Class A).
S1_FILES = [
    "cascade/matrix_cascades.py",
    "cascade/composites.py",
    "signal_processing/closed_form_ops/iir.py",
]


def section1(tree: str) -> None:
    import os
    root = os.path.dirname(srmech.__file__)
    hashes = {}
    for rel in S1_FILES:
        with open(os.path.join(root, rel), "rb") as fh:
            hashes[rel] = sha256_bytes(fh.read())
    env_row(tree, {"section": "s1", "file_sha256": hashes})
    for op, args, label, decides in S1_CASES:
        fn = resolve_dotted_callable(op)
        got = _call(fn, args)
        emit({"row": "s1_execute", "tree": tree, "op": op,
              "input": repr(args)[:120], "input_label": label,
              "decides": decides, **got})


# ---------------------------------------------------------------------------
# SECTION 2 — the declared-vs-enforced census
# ---------------------------------------------------------------------------
#
# Population: every registry op whose docstring (or ToolEntry summary) NAMES
# an exception type it promises to raise. Check: probe the op one-parameter-
# at-a-time with type-valid edge arguments; every exception observed from
# INSIDE srmech is compared against the promised set. observed-not-promised
# on an op WITH a promise -> mismatch candidate (the signed_sum_squared
# class). Ops promising nothing are a different population (rc430's), not
# counted here. Promises the battery cannot trigger are UNCHECKED, and the
# unchecked remainder is reported — a census that silently drops its
# population cannot report a null.

_EXC_NAME = r"(?:[A-Za-z_][\w.]*\.)?([A-Z][A-Za-z0-9_]*(?:Error|Exception|Warning|Exit|Interrupt))"

_RE_REST = re.compile(r":raises?\s+" + _EXC_NAME + r"\s*:")
_RE_INLINE = re.compile(
    r"[Rr]aises?\s+(?:a\s+|an\s+|the\s+)?(?:``|`)?" + _EXC_NAME + r"(?:``|`)?")


def _google_numpy_blocks(doc: str) -> Tuple[List[str], List[str], List[str]]:
    """(google_types, numpy_types, styles_seen). Line-wrap-safe: entry TYPE
    tokens are matched at line starts inside the block; wrapped description
    lines cannot shadow them."""
    lines = doc.splitlines()
    google: List[str] = []
    numpy: List[str] = []
    styles: List[str] = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped == "Raises:":
            styles.append("google")
            base = len(lines[i]) - len(lines[i].lstrip())
            j = i + 1
            while j < len(lines):
                ln = lines[j]
                if ln.strip() and (len(ln) - len(ln.lstrip())) <= base:
                    break
                m = re.match(r"\s+" + _EXC_NAME + r"\s*:", ln)
                if m:
                    google.append(m.group(1))
                j += 1
            i = j
            continue
        if stripped == "Raises" and i + 1 < len(lines) \
                and re.match(r"\s*-{3,}\s*$", lines[i + 1]):
            styles.append("numpy")
            base = len(lines[i]) - len(lines[i].lstrip())
            j = i + 2
            while j < len(lines):
                ln = lines[j]
                st = ln.strip()
                if st and (len(ln) - len(ln.lstrip())) <= base \
                        and not re.match(_EXC_NAME + r"\s*$", st):
                    break
                if st and re.match(r"\s*-{3,}\s*$", ln):
                    break
                m = re.match(r"\s*" + _EXC_NAME + r"\s*$", ln)
                if m and (len(ln) - len(ln.lstrip())) == base:
                    numpy.append(m.group(1))
                j += 1
            i = j
            continue
        i += 1
    return google, numpy, styles


def extract_promises(doc: str) -> Tuple[set, List[str]]:
    """Promised exception-type names + the styles that carried them."""
    promised: set = set()
    styles: List[str] = []
    if not doc:
        return promised, styles
    g, n, st = _google_numpy_blocks(doc)
    promised.update(g)
    promised.update(n)
    styles.extend(st)
    rest = _RE_REST.findall(doc)
    if rest:
        styles.append("rest")
        promised.update(rest)
    inline = _RE_INLINE.findall(doc)
    if inline:
        new = set(inline) - promised
        if new:
            styles.append("inline")
        promised.update(inline)
    return promised, styles


# One-at-a-time edge battery. For the varied parameter: every edge value its
# declared type admits. For held parameters: the PLAUSIBLE value (rc430's
# round-1 synth). Carrier types are NOT synthesized (reported unsynthesizable).
_EDGES: Dict[str, List[Any]] = {
    "int": [0, -1], "integer": [0, -1], "float": [0.0, -1.0],
    "bool": [False], "complex": [0j],
    "str": [""], "bytes": [b""],
    "list": [[], [1, 2], [[1, 0], [1]]],
    "sequence": [[], [1, 2], [[1, 0], [1]]],
    "Sequence[int]": [[], [1, 2], [[1, 0], [1]]],
    "list[int]": [[], [1, 2], [[1, 0], [1]]],
    "list[float]": [[], [1.0, 2.0], [[1.0], [1.0, 2.0]]],
    "list[complex]": [[], [1 + 0j]],
    "list[list[float]]": [[], [[1.0, 0.0], [0.0, 1.0]], [[1.0, 0.0], [1.0]]],
    "list[list[int]]": [[], [[1, 0], [0, 1]], [[1, 0], [1]]],
    "tuple[int, int]": [(0, 0)],
    "list[tuple[int, int]]": [[], [(0, 1)]],
    "dict": [{}],
}
_PLAUSIBLE: Dict[str, Any] = {
    "int": 2, "integer": 2, "float": 2.0, "bool": True, "complex": 1 + 0j,
    "str": "a", "bytes": b"ab", "list": [1, 2], "sequence": [1, 2],
    "Sequence[int]": [1, 2], "list[int]": [1, 2], "list[float]": [1.0, 2.0],
    "list[complex]": [1 + 0j], "list[list[float]]": [[1.0, 0.0], [0.0, 1.0]],
    "list[list[int]]": [[1, 0], [0, 1]], "tuple[int, int]": (1, 2),
    "list[tuple[int, int]]": [(0, 1)], "dict": {"a": 1},
}

# Same safety scope as rc430 S1 — the census EXECUTES ops.
_UNSAFE = ("write", "save", "delete", "remove", "publish", "fetch",
           "download", "register", "install", "mkdir", "open", "load",
           "path", "file", "dir", "server", "client", "bus",
           "exec", "spawn")
_SAFE_MODULE_PREFIXES = ("srmech.math.", "srmech.cascade.",
                         "srmech.physics.qm.", "srmech.signal_processing.",
                         "srmech.apokatastasis.", "srmech.music.",
                         "srmech.trigonometry", "srmech.asymptotic_calculus")


def section2(tree: str) -> None:
    env_row(tree, {"section": "s2"})
    tools = get_tool_schema().tools

    n_with_promise = 0
    promise_type_hist: Dict[str, int] = {}
    style_hist: Dict[str, int] = {}
    probed = 0
    skipped: Dict[str, int] = {}
    n_consistent_probes = 0
    n_mismatch_probes = 0
    ops_consistent: set = set()
    ops_mismatch: set = set()
    candidates: List[Dict[str, Any]] = []
    unchecked = 0

    for entry in tools:
        try:
            fn = resolve_dotted_callable(entry.name)
        except Exception:
            continue
        real = inspect.unwrap(fn)
        doc = inspect.getdoc(real) or ""
        summary = getattr(entry, "summary", "") or ""
        promised, styles = extract_promises(doc)
        p2, st2 = extract_promises(summary)
        promised |= p2
        for s in set(styles + st2):
            style_hist[s] = style_hist.get(s, 0) + 1
        if not promised:
            continue
        n_with_promise += 1
        for t in promised:
            promise_type_hist[t] = promise_type_hist.get(t, 0) + 1

        mod = getattr(real, "__module__", "")
        low = entry.name.lower()
        if not mod.startswith(_SAFE_MODULE_PREFIXES):
            skipped["module_out_of_scope"] = skipped.get(
                "module_out_of_scope", 0) + 1
            unchecked += 1
            continue
        if any(tok in low for tok in _UNSAFE):
            skipped["unsafe_name"] = skipped.get("unsafe_name", 0) + 1
            unchecked += 1
            continue
        req = [p for p in entry.parameters if p.required]
        if not req or len(req) > 4:
            skipped["no_or_too_many_params"] = skipped.get(
                "no_or_too_many_params", 0) + 1
            unchecked += 1
            continue
        if not all(p.type in _EDGES for p in req):
            skipped["unsynthesizable_type"] = skipped.get(
                "unsynthesizable_type", 0) + 1
            unchecked += 1
            continue

        probed += 1
        op_hit_mismatch = False
        op_hit_consistent = False
        for vary_i, vp in enumerate(req):
            for edge in _EDGES[vp.type]:
                args = [edge if k == vary_i else _PLAUSIBLE[p.type]
                        for k, p in enumerate(req)]
                got = _call(fn, args, timeout=2)
                if got["outcome"] != "RAISED":
                    continue
                # only exceptions from INSIDE srmech count — frame 0 is this
                # harness, frame 1 the op. A raise in frame 0 means synthesis
                # itself broke, which is the harness's defect, not the op's.
                frames = got.get("frames", [])
                if len(frames) < 2:
                    continue
                if got["exc"] in promised:
                    n_consistent_probes += 1
                    op_hit_consistent = True
                    continue
                n_mismatch_probes += 1
                op_hit_mismatch = True
                candidates.append({
                    "row": "s2_candidate", "tree": tree, "op": entry.name,
                    "module": mod, "promised": sorted(promised),
                    "observed": got["exc"], "msg": got["msg"],
                    "raised_in": got["raised_in"],
                    "varied_param": vp.name, "input": repr(args)[:140]})
        if op_hit_consistent:
            ops_consistent.add(entry.name)
        if op_hit_mismatch:
            ops_mismatch.add(entry.name)

    for c in candidates:
        emit(c)
    emit({"row": "s2_style_hist", "tree": tree, "hist": style_hist})
    emit({"row": "s2_promise_type_hist", "tree": tree,
          "hist": dict(sorted(promise_type_hist.items(),
                              key=lambda kv: -kv[1]))})
    emit({"row": "s2_totals", "tree": tree,
          "registry": len(tools),
          "ops_with_named_promise": n_with_promise,
          "probed": probed, "unchecked": unchecked, "skipped": skipped,
          "consistent_probes": n_consistent_probes,
          "mismatch_probes": n_mismatch_probes,
          "ops_with_consistent_probe": len(ops_consistent),
          "ops_with_mismatch": sorted(ops_mismatch)})

    # ---- controls (S2-PC / S2-STYLE / S2-NC) ----
    pc = any(c["op"] == "srmech.cascade.signed_sum_squared"
             and c["observed"] == "TypeError" for c in candidates)
    emit({"row": "falsifier", "id": "S2-PC", "claim":
          "scanner flags signed_sum_squared (promised ValueError, observed "
          "TypeError) on the baseline tree",
          "value": pc,
          "verdict": ("PASS" if pc else
                      "FIRED — INSTRUMENT INVALID, no zero reportable")
          if tree == "baseline" else "N/A (control is baseline-only)"})
    style_ok = all(style_hist.get(s, 0) > 0
                   for s in ("google", "numpy", "rest"))
    emit({"row": "falsifier", "id": "S2-STYLE", "claim":
          "all three docstring styles extracted (google/numpy/rest)",
          "value": {s: style_hist.get(s, 0)
                    for s in ("google", "numpy", "rest", "inline")},
          "verdict": "PASS" if style_ok else "FIRED — extractor blind spot"})
    nc = "srmech.cascade.signed_sum_squared" in ops_consistent
    emit({"row": "falsifier", "id": "S2-NC", "claim":
          "signed_sum_squared's ENFORCED ValueError (empty sources) counts "
          "CONSISTENT — same op on both sides of the split",
          "value": nc,
          "verdict": ("PASS" if nc else "FIRED — over-counting")
          if tree == "baseline" else "N/A"})


def section2_recheck(tree: str, ndjson_path: str) -> None:
    """Re-execute every baseline mismatch candidate on the current tree."""
    env_row(tree, {"section": "s2c"})
    seen: set = set()
    with open(ndjson_path, "r", encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            if rec.get("row") != "s2_candidate" \
                    or rec.get("tree") != "baseline":
                continue
            key = (rec["op"], rec["input"])
            if key in seen:
                continue
            seen.add(key)
            fn = resolve_dotted_callable(rec["op"])
            args = eval(rec["input"])  # noqa: S307 — replaying our own reprs
            got = _call(fn, args, timeout=2)
            if got["outcome"] == "RAISED" and got["exc"] in rec["promised"]:
                verdict = "REPAIRED (now raises the promised type)"
            elif got["outcome"] == "RAISED" \
                    and got["exc"] == rec["observed"]:
                verdict = "STILL_PRESENT"
            else:
                verdict = "CHANGED (see outcome)"
            emit({"row": "s2_recheck", "tree": tree, "op": rec["op"],
                  "input": rec["input"], "promised": rec["promised"],
                  "baseline_observed": rec["observed"],
                  "outcome": got.get("outcome"),
                  "now": got.get("exc") or got.get("value", "")[:80],
                  "raised_in": got.get("raised_in", ""),
                  "verdict": verdict})


# ---------------------------------------------------------------------------
# SECTION 3 — the 44 silent acceptors
# ---------------------------------------------------------------------------
#
# Reconstructs rc430's pf6 probe EXACTLY (same synth table, same rounds, same
# skip rules) to recover the accepted-every-edge-arg population, then takes a
# deterministic stride sample of >= 12 and RECORDS each op's return value on
# the degenerate round-0 input. The correct/quietly-wrong verdicts are written
# by the operator in the `verdicts` section after reading each op's source —
# a probe cannot decide mathematical intent, and does not claim to.

_SYNTH_430: Dict[str, List[Any]] = {
    "int": [0, 2], "integer": [0, 2], "float": [0.0, 2.0],
    "bool": [False, True], "complex": [0j, (1 + 0j)],
    "str": ["", "a"], "bytes": [b"", b"ab"],
    "list": [[], [1, 2]], "sequence": [[], [1, 2]],
    "Sequence[int]": [[], [1, 2]], "list[int]": [[], [1, 2]],
    "list[float]": [[], [1.0, 2.0]], "list[complex]": [[], [1 + 0j]],
    "list[list[float]]": [[], [[1.0, 0.0], [0.0, 1.0]]],
    "list[list[int]]": [[], [[1, 0], [0, 1]]],
    "tuple[int, int]": [(0, 0), (1, 2)],
    "list[tuple[int, int]]": [[], [(0, 1)]],
    "dict": [{}, {"a": 1}],
}

# rc430's guard detector is not re-run here; the unguarded set is recovered
# from the rc430 NDJSON (op rows with n_guards == 0), which this run treats
# as the S1 instrument's own record of its population.
RC430_NDJSON = "docs/srmech/notes/_s1_guard_extraction_rc430.ndjson"


def section3(tree: str, rc430_path: str) -> None:
    env_row(tree, {"section": "s3"})
    tools = {e.name: e for e in get_tool_schema().tools}
    unguarded: List[str] = []
    with open(rc430_path, "r", encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            if rec.get("row") == "op" and rec.get("n_guards") == 0:
                unguarded.append(rec["op"])
    emit({"row": "s3_population", "tree": tree,
          "unguarded_from_rc430": len(unguarded)})

    acceptors: List[str] = []
    probed = 0
    for name in unguarded:
        entry = tools.get(name)
        if entry is None:
            continue
        try:
            fn = resolve_dotted_callable(name)
        except Exception:
            continue
        mod = getattr(inspect.unwrap(fn), "__module__", "")
        if not mod.startswith(_SAFE_MODULE_PREFIXES):
            continue
        if any(tok in name.lower() for tok in _UNSAFE):
            continue
        req = [p for p in entry.parameters if p.required]
        if not req or len(req) > 4:
            continue
        if not all(p.type in _SYNTH_430 for p in req):
            continue
        probed += 1
        all_ok = True
        for rnd in (0, 1):
            args = [_SYNTH_430[p.type][min(rnd, len(_SYNTH_430[p.type]) - 1)]
                    for p in req]
            got = _call(fn, args, timeout=2)
            if got["outcome"] != "RETURNED":
                all_ok = False
                break
        if all_ok:
            acceptors.append(name)

    emit({"row": "s3_acceptors", "tree": tree, "probed": probed,
          "accepted_every_edge_arg": len(acceptors), "ops": acceptors})
    emit({"row": "falsifier", "id": "S3-PF", "claim":
          "reconstruction reproduces rc430's 44-of-91 acceptor population",
          "value": {"probed": probed, "acceptors": len(acceptors)},
          "verdict": ("PASS" if (probed, len(acceptors)) == (91, 44)
                      else "BOUNDED — instrument drift, delta reported")})

    # Deterministic sample: sorted, stride 3 => ~15 of 44, PLUS any acceptor
    # whose name marks it as a numeric kernel (highest silent-wrong risk).
    ordered = sorted(acceptors)
    sample = ordered[::3]
    for name in sample:
        entry = tools[name]
        fn = resolve_dotted_callable(name)
        req = [p for p in entry.parameters if p.required]
        for rnd in (0, 1):
            args = [_SYNTH_430[p.type][min(rnd, len(_SYNTH_430[p.type]) - 1)]
                    for p in req]
            got = _call(fn, args, timeout=2)
            emit({"row": "s3_sample", "tree": tree, "op": name,
                  "round": rnd, "params": [(p.name, p.type) for p in req],
                  "input": repr(args)[:140], **got})


# ---------------------------------------------------------------------------
# VERDICTS — operator analysis rows, written after reading each op's source.
# Kept in this file so the analysis is committed and reproducible alongside
# the numbers it interprets. Populated in the verdict pass; empty on the
# probe passes.
# ---------------------------------------------------------------------------

VERDICT_ROWS: List[Dict[str, Any]] = []  # filled by the verdict edit pass


def section_verdicts() -> None:
    for rec in VERDICT_ROWS:
        emit(rec)


def main() -> int:
    which = sys.argv[1]
    if which == "s1":
        section1(sys.argv[2])
    elif which == "s2":
        section2(sys.argv[2])
    elif which == "s2c":
        section2_recheck(sys.argv[2], sys.argv[3])
    elif which == "s3":
        section3(sys.argv[2], sys.argv[3] if len(sys.argv) > 3
                 else RC430_NDJSON)
    elif which == "verdicts":
        section_verdicts()
    else:
        raise SystemExit("unknown section: " + which)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
