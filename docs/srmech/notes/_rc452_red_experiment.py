#!/usr/bin/env python3
"""rc452 (`#T1166`) — THE FALSIFIABLE-PREDICTION INSTRUMENT.

The rc452 ruling's surviving dissent (judge 3's A-CARRIER placement) is settled
by ONE experiment and no argument: implement A-FULL's first arm (the reader
rebuilds ``q`` as ``Q``; the nine Class-N ops return ``Q``) with NO repairs, and
require the resulting red set to be EXACTLY the set the ruling enumerated in
advance.  Any red outside it, any predicted red that stays green, re-opens the
placement question.

That only means anything if the prediction PREDATES the measurement and if the
instrument can return both verdicts.  Both are enforced here:

* The manifest (``_rc452_predicted_red_manifest.json``) is committed in its own
  commit BEFORE the product change.  Every run embeds the manifest's **git blob
  hash** — ``sha1("blob %d\\0" % len + bytes)``, the same number
  ``git hash-object`` prints — in its output and in the run ndjson, so a
  manifest edited after seeing the reds is visible in history.
* The SAME instrument is required to print ``0 reds`` on the baseline commit and
  ``exactly the manifest`` on the experiment commit.  Two witnessed verdicts, so
  this is not "an instrument that cannot return otherwise".

HOW IT REFUSES TO FOOL ITSELF
-----------------------------
1. **It parses, it does not grep.**  Verdicts come from the pytest ``--junitxml``
   report read with ``xml.etree``.  Terminal text is never scanned.
2. **Zero-collection is a hard failure.**  Every enumerated file must contribute
   at least one ``<testcase>``.  A file that silently collects nothing (import
   error swallowed, name typo, whole-module skip) would otherwise make the run
   green by absence — the census-that-printed-CLEAN class this arc has hit
   repeatedly.
3. **No ``-k`` / ``-m`` filters.**  A filtered run cannot see an excess red, and
   a filter welded into a gate is how a green gate lies.  Passing either aborts.
4. **A new xfail counts as a red.**  The manifest freezes the baseline xfail
   node-id set; any xfail outside it is counted as a red, so "fixing" a failure
   by marking it expected does not buy a green.
5. **The diff runs in BOTH directions.**  Excess reds AND missing predicted reds
   are both falsifications, reported separately.

USAGE (from ``docs/srmech/python`` with ``PYTHONPATH=.``)::

    python3 ../notes/_rc452_red_experiment.py --census
    python3 ../notes/_rc452_red_experiment.py --expect-green
    python3 ../notes/_rc452_red_experiment.py --expect-red \
        --emit-ndjson ../notes/_rc452_red_experiment_run.ndjson
    python3 ../notes/_rc452_red_experiment.py --expect-red-exactly SUBSTR

Exit 0 means the stated expectation HELD.  Exit 1 means it did not — and in this
arc that is a finding, not a chore.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

HERE = Path(__file__).resolve().parent
MANIFEST_PATH = HERE / "_rc452_predicted_red_manifest.json"

#: The nine Class-N ops selected by the ruling's DERIVED predicate
#: (``returns.type == tuple[int,int]`` AND the shape names ``num`` and ``den``).
#: Frozen here so ``--census`` is reproducible.
NINE_OPS = (
    "rational_add",
    "rational_mul",
    "rational_div",
    "rational_pow_uint",
    "exp_series_truncate",
    "sin_series_truncate",
    "cos_series_truncate",
    "log1p_series_truncate",
    "atan_series_truncate",
)

#: Gate files that read the chain wire / the reconstructed value directly.  They
#: are in scope whether or not they name one of the nine ops, because the reader
#: change is the other half of the experiment.
WIRE_GATES = (
    "tests/test_c_cascade_value_parity_rc450.py",
    "tests/test_cascade_catalog_executable_rc420.py",
)


# ── the enumeration predicate ────────────────────────────────────────────────

def census_files(tests_dir: Path) -> Tuple[List[str], Dict[str, List[str]]]:
    """Return (enumerated files, per-file evidence).

    PREDICATE, stated so a reader re-deriving it gets the same set:
    a test module is enumerated iff its AST contains a ``Name``, ``Attribute``
    or string ``Constant`` node naming one of :data:`NINE_OPS` — union the
    :data:`WIRE_GATES`.  The string arm is deliberately included: a chain
    descriptor names its op as a STRING, so a gate that runs
    ``srmech.math.rational.rational_add`` through the catalog references the op
    only as text.  Excluding it was how an earlier census would have missed the
    catalog gates entirely.
    """
    evidence: Dict[str, List[str]] = {}
    for name in sorted(os.listdir(tests_dir)):
        if not name.endswith(".py") or not name.startswith("test_"):
            continue
        rel = f"tests/{name}"
        src = (tests_dir / name).read_text(encoding="utf-8")
        try:
            tree = ast.parse(src)
        except SyntaxError as exc:                     # pragma: no cover
            raise SystemExit(f"census: cannot parse {rel}: {exc}")
        found = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in NINE_OPS:
                found.add(node.id)
            elif isinstance(node, ast.Attribute) and node.attr in NINE_OPS:
                found.add(node.attr)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                for op in NINE_OPS:
                    if op in node.value:
                        found.add(op)
        if found:
            evidence[rel] = sorted(found)
    for gate in WIRE_GATES:
        evidence.setdefault(gate, ["<wire gate>"])
    return sorted(evidence), evidence


# ── manifest identity ────────────────────────────────────────────────────────

def git_blob_hash(path: Path) -> str:
    """The git blob hash of ``path`` — identical to ``git hash-object <path>``.

    Computed here rather than shelled out so the number lands in the run
    artifact even when git is not on PATH (this tree's worktree is driven from
    Windows git while the tests run under WSL2)."""
    data = path.read_bytes()
    header = b"blob %d\0" % len(data)
    return hashlib.sha1(header + data).hexdigest()


def load_manifest() -> Dict[str, Any]:
    if not MANIFEST_PATH.exists():
        raise SystemExit(f"manifest not found: {MANIFEST_PATH}")
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


# ── the run ──────────────────────────────────────────────────────────────────

def _classname_to_file(classname: str, known: List[str]) -> Optional[str]:
    """Map a junit ``classname`` (``tests.test_x`` / ``tests.test_x.TestCls``)
    back to one of the enumerated file paths.  Longest matching prefix wins, so
    a class-scoped test still resolves to its module."""
    parts = classname.split(".")
    while parts:
        cand = "/".join(parts) + ".py"
        if cand in known:
            return cand
        parts.pop()
    return None


def run_pytest(files: List[str], extra: List[str]) -> Tuple[int, Path, str]:
    xml_path = Path(tempfile.mkstemp(prefix="rc452_", suffix=".xml")[1])
    cmd = [sys.executable, "-m", "pytest", *files,
           f"--junitxml={xml_path}", "-q", "-p", "no:cacheprovider", *extra]
    env = dict(os.environ)
    env.setdefault("PYTHONPATH", ".")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True,
                          errors="replace")
    return proc.returncode, xml_path, (proc.stdout or "") + (proc.stderr or "")


def parse_report(xml_path: Path, known: List[str]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Parse the junit report into per-test records.  NEVER greps the terminal.

    Each record: {file, test, status, message}.  ``status`` is one of
    ``passed`` / ``failure`` / ``error`` / ``xfail`` / ``skipped``.
    """
    root = ET.parse(xml_path).getroot()
    records: List[Dict[str, Any]] = []
    per_file: Dict[str, int] = {f: 0 for f in known}
    for case in root.iter("testcase"):
        classname = case.get("classname") or ""
        name = case.get("name") or ""
        fname = _classname_to_file(classname, known)
        if fname is None:
            # A collection error reports classname="" / name=<path>. Resolve by
            # the name itself so a hard import failure is never invisible.
            cand = name.replace("\\", "/")
            fname = cand if cand in known else f"<unmapped:{classname}|{name}>"
        status = "passed"
        message = ""
        for child in case:
            tag = child.tag
            if tag == "failure":
                status, message = "failure", (child.get("message") or "")
            elif tag == "error":
                status, message = "error", (child.get("message") or "")
            elif tag == "skipped":
                if (child.get("type") or "") == "pytest.xfail":
                    status, message = "xfail", (child.get("message") or "")
                else:
                    status, message = "skipped", (child.get("message") or "")
        records.append({"file": fname, "test": name, "status": status,
                        "message": message[:400]})
        if fname in per_file:
            per_file[fname] += 1
    return records, per_file


def reds_of(records: List[Dict[str, Any]], baseline_xfails: set) -> List[Dict[str, Any]]:
    out = []
    for r in records:
        nodeid = f"{r['file']}::{r['test']}"
        if r["status"] in ("failure", "error"):
            out.append(r)
        elif r["status"] == "xfail" and nodeid not in baseline_xfails:
            out.append(dict(r, status="xfail-new"))
    return out


def match_entry(red: Dict[str, Any], entry: Dict[str, Any]) -> bool:
    if red["file"] != entry["file"]:
        return False
    base = red["test"].split("[", 1)[0]
    if base != entry["test"]:
        return False
    sub = entry.get("param_contains")
    if sub and sub not in red["test"]:
        return False
    return True


# ── main ─────────────────────────────────────────────────────────────────────

def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--census", action="store_true",
                    help="print the AST-derived enumerated file set and exit")
    ap.add_argument("--expect-green", action="store_true")
    ap.add_argument("--expect-red", action="store_true")
    ap.add_argument("--expect-red-exactly", metavar="SUBSTR", default=None)
    ap.add_argument("--emit-ndjson", metavar="PATH", default=None)
    ap.add_argument("--note", default="", help="free-text label recorded in the ndjson")
    ap.add_argument("pytest_extra", nargs="*", default=[])
    args = ap.parse_args(argv)

    # RULE 3: a filtered run cannot see an excess red.
    for bad in ("-k", "-m", "--deselect", "--last-failed", "--lf"):
        if any(a == bad or a.startswith(bad + "=") for a in argv):
            print(f"REFUSED: {bad} would filter the run; an excess red would be "
                  f"invisible and this instrument's whole job is to see one.")
            return 2

    cwd = Path.cwd()
    tests_dir = cwd / "tests"
    if not tests_dir.is_dir():
        print(f"REFUSED: run me from docs/srmech/python (no tests/ under {cwd})")
        return 2

    if args.census:
        files, evidence = census_files(tests_dir)
        print(f"PREDICATE: AST names one of the nine Class-N ops (Name / "
              f"Attribute / string Constant) UNION the {len(WIRE_GATES)} wire gates")
        print(f"ENUMERATED FILES: {len(files)}")
        for f in files:
            print(f"  {f}  <- {','.join(evidence[f])}")
        return 0

    man = load_manifest()
    blob = git_blob_hash(MANIFEST_PATH)
    files: List[str] = list(man["enumerated_files"])
    baseline_xfails = set(man.get("baseline_xfails", []))
    predicted: List[Dict[str, Any]] = list(man["predicted_reds"])
    predicted_total = sum(int(e["expected_count"]) for e in predicted)

    print(f"manifest         : {MANIFEST_PATH.name}")
    print(f"manifest blob sha: {blob}")
    print(f"manifest version : {man.get('manifest_version')}")
    print(f"files enumerated : {len(files)}")
    print(f"predicted reds   : {predicted_total} across {len(predicted)} sites")

    missing_on_disk = [f for f in files if not (cwd / f).exists()]
    if missing_on_disk:
        print(f"FAIL: enumerated files absent from the tree: {missing_on_disk}")
        return 1

    rc, xml_path, output = run_pytest(files, list(args.pytest_extra))
    try:
        records, per_file = parse_report(xml_path, files)
    except (ET.ParseError, FileNotFoundError) as exc:
        print(f"FAIL: junit report unreadable ({exc}); pytest rc={rc}")
        print(output[-4000:])
        return 1
    finally:
        try:
            xml_path.unlink()
        except OSError:
            pass

    # RULE 2: zero collection is a hard failure, never a quiet green.
    empty = sorted(f for f, n in per_file.items() if n == 0)
    unmapped = sorted({r["file"] for r in records if r["file"].startswith("<unmapped")})
    print(f"testcases parsed : {len(records)}")
    if unmapped:
        print(f"UNMAPPED classnames (report shape changed?): {unmapped}")

    observed = reds_of(records, baseline_xfails)
    by_status: Dict[str, int] = {}
    for r in records:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
    print(f"status histogram : {json.dumps(by_status, sort_keys=True)}")
    print(f"observed reds    : {len(observed)}")
    for r in observed:
        print(f"   RED  {r['file']}::{r['test']}  [{r['status']}]")

    # ── the two-direction diff ───────────────────────────────────────────────
    matched: Dict[int, List[Dict[str, Any]]] = {i: [] for i in range(len(predicted))}
    excess: List[Dict[str, Any]] = []
    for red in observed:
        hit = None
        for i, entry in enumerate(predicted):
            if match_entry(red, entry):
                hit = i
                break
        if hit is None:
            excess.append(red)
        else:
            matched[hit].append(red)
    shortfall = [
        {"entry": predicted[i], "expected": int(predicted[i]["expected_count"]),
         "observed": len(matched[i])}
        for i in range(len(predicted))
        if len(matched[i]) != int(predicted[i]["expected_count"])
    ]

    if args.emit_ndjson:
        out = Path(args.emit_ndjson)
        with out.open("w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps({
                "record": "run_header",
                "note": args.note,
                "manifest_blob_sha": blob,
                "manifest_version": man.get("manifest_version"),
                "files_enumerated": len(files),
                "testcases_parsed": len(records),
                "status_histogram": by_status,
                "observed_reds": len(observed),
                "predicted_reds": predicted_total,
                "excess_reds": len(excess),
                "shortfall_sites": len(shortfall),
                "pytest_rc": rc,
            }, sort_keys=True) + "\n")
            for r in records:
                if r["status"] == "passed":
                    continue
                fh.write(json.dumps({"record": "verdict", **r}, sort_keys=True) + "\n")
            for e in excess:
                fh.write(json.dumps({"record": "excess_red", **e}, sort_keys=True) + "\n")
            for s in shortfall:
                fh.write(json.dumps({"record": "shortfall", **s}, sort_keys=True) + "\n")
        print(f"ndjson written   : {out}")

    # RULE 2 (continued). The abort sits HERE, after the artifact is written:
    # rc452-s2's literal pre-registered state collapsed 41/41 enumerated files
    # to zero collected tests (a module-scope subscript of a now-Q return broke
    # `import srmech.cascade` outright), and the first shape of this function
    # aborted BEFORE emitting — so the one run that most needed a record left
    # none. A degenerate run is still a measurement and must leave one.
    if empty:
        print(f"FAIL: these enumerated files collected 0 tests: {empty}")
        print("      A run in which nothing collected has measured NOTHING; "
              "its red count is not zero, it is undefined.")
        return 1

    # ── verdicts ─────────────────────────────────────────────────────────────
    if args.expect_green:
        if observed:
            print("FAIL --expect-green: the baseline is NOT clean; every number "
                  "downstream of it would be measured against a moving floor.")
            return 1
        print("OK --expect-green: 0 reds, every enumerated file collected > 0 tests.")
        return 0

    if args.expect_red_exactly is not None:
        sub = args.expect_red_exactly
        if len(observed) == 1 and sub in f"{observed[0]['file']}::{observed[0]['test']}":
            print(f"OK --expect-red-exactly: the single remaining red is {sub}")
            return 0
        print(f"FAIL --expect-red-exactly {sub!r}: observed {len(observed)} reds")
        return 1

    if args.expect_red:
        ok = not excess and not shortfall
        if excess:
            print("\n*** FALSIFIED — REDS OUTSIDE THE PRE-REGISTERED MANIFEST ***")
            print("*** The A-CARRIER placement question RE-OPENS. Report loudly; "
                  "do not absorb. ***")
            for r in excess:
                print(f"   EXCESS  {r['file']}::{r['test']}  [{r['status']}]  {r['message'][:180]}")
        if shortfall:
            print("\n*** FALSIFIED — PREDICTED REDS THAT DID NOT APPEAR (or wrong count) ***")
            for s in shortfall:
                e = s["entry"]
                print(f"   SHORTFALL  {e['file']}::{e['test']} expected "
                      f"{s['expected']} got {s['observed']}")
        if ok:
            print(f"\nOK --expect-red: observed red set == the pre-registered "
                  f"manifest EXACTLY ({len(observed)} reds, {len(predicted)} sites). "
                  f"The ruling's prediction is CONFIRMED.")
            return 0
        return 1

    print("no expectation given; nothing asserted. Pass --expect-green / "
          "--expect-red / --expect-red-exactly.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
