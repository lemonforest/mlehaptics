#!/usr/bin/env python3
"""rc296 — GENERATING CODE for any pytest-xdist wall-clock claim.

WHY THIS EXISTS
===============
rc283 parallelised CI with ``pytest-xdist`` and recorded a **2.19-2.68x** speedup in
a workflow comment and the CHANGELOG. Searching the whole subtree for those figures
finds no harness, no artifact, no log — the numbers existed only as prose. Under
``[[feedback_computational_provenance_discipline]]`` a load-bearing number must ship
the code that generated it, so rc296 **struck the figures** and committed this
instead.

WHAT THIS MEASURES, AND WHAT IT CANNOT
======================================
It measures wall-clock of a NAMED set of test files, serial vs ``-n auto``, over N
repeats, and reports a **RANGE** (min / median / max). It deliberately does not
report a single number, because a single run of this quantity is not a measurement:

* rc283's own three runs spread 2.19 -> 2.68x and its note attributes the spread to
  CONTENTION (another pytest session on the same box), not to sampling variance.
  A figure whose spread is dominated by "what else was running" is a property of the
  afternoon, not of the change.
* The ratio is bounded by core count. ``-n auto`` resolves to ``os.cpu_count()``,
  which differs per host and per CI cell (4 on ubuntu-latest / windows-latest, 3 on
  macos-14). A ratio measured on one host does not transfer to another.
* ``--dist loadfile`` sends a whole FILE to one worker, so the achievable speedup is
  capped by the SLOWEST SINGLE FILE, not by total work. Two trees with the same test
  count and different file granularity parallelise differently.

So: this produces a number for THIS host, THIS file set, THIS moment. That is a
legitimate thing to want (it is how you decide whether parallelising is worth it) and
an illegitimate thing to quote as a package property. rc296 quotes no multiple.

USAGE
=====
    cd docs/srmech/python
    python3 ../notes/rc283_xdist_speedup_probe.py --repeats 3 [FILE ...]

Writes NDJSON (one record per run, per project discipline) to stdout; the summary
goes to stderr so a redirect captures clean data.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import time

#: The default file set. Named explicitly rather than globbed so the measurement is
#: reproducible: a glob would silently change meaning as files are added, and a ratio
#: compared against a different denominator is not a comparison.
DEFAULT_FILES = [
    "tests/test_genome_read_io_ratchet_rc282.py",
    "tests/test_genome_chr_bundle_rc148.py",
    "tests/test_express_plan_rc135.py",
    "tests/test_cellstate_chromatin_rc274.py",
    "tests/test_express_plan_chromatin_rc269.py",
    "tests/test_rosetta_completeness.py",
]


def _run(files, workers):
    """One pytest invocation; returns (seconds, exit_code, tests_reported).

    Wall-clock is taken around the SUBPROCESS, so interpreter start-up and xdist
    worker spawn are inside the measurement — they are a real cost of parallelising
    and excluding them would flatter the parallel arm."""
    cmd = [sys.executable, "-m", "pytest", *files, "-q", "-p", "no:randomly",
           "--timeout=900"]
    if workers:
        cmd += ["-n", workers, "--dist", "loadfile"]
    env = dict(os.environ, PYTHONPATH=".")
    t0 = time.perf_counter()
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    dt = time.perf_counter() - t0
    tail = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
    return dt, proc.returncode, tail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=3,
                    help="runs per arm; >1 is REQUIRED for the range to mean anything")
    ap.add_argument("files", nargs="*", default=None)
    args = ap.parse_args()
    files = args.files or DEFAULT_FILES

    if args.repeats < 2:
        print("refusing: a single run is not a measurement (see module docstring)",
              file=sys.stderr)
        return 2

    print(f"host cpu_count={os.cpu_count()}  files={len(files)}  "
          f"repeats={args.repeats}", file=sys.stderr)

    serial, parallel = [], []
    for i in range(args.repeats):
        for arm, bucket, workers in (("serial", serial, None),
                                     ("auto", parallel, "auto")):
            dt, rc, tail = _run(files, workers)
            bucket.append(dt)
            rec = {"arm": arm, "repeat": i, "seconds": round(dt, 2),
                   "exit_code": rc, "pytest_tail": tail,
                   "cpu_count": os.cpu_count(), "n_files": len(files)}
            print(json.dumps(rec), flush=True)
            print(f"  {arm:7s} rep{i}: {dt:7.2f}s  rc={rc}  {tail}", file=sys.stderr)
            if rc not in (0, 5):
                print("ARM FAILED — a speedup over a failing run is meaningless",
                      file=sys.stderr)
                return 1

    ratios = sorted(s / p for s, p in zip(serial, parallel))
    summary = {
        "arm": "summary",
        "serial_seconds": [round(x, 2) for x in serial],
        "auto_seconds": [round(x, 2) for x in parallel],
        "ratio_min": round(min(ratios), 2),
        "ratio_median": round(statistics.median(ratios), 2),
        "ratio_max": round(max(ratios), 2),
        "cpu_count": os.cpu_count(),
        "files": files,
        "scope": ("this host, this file set, this moment; --dist loadfile caps the "
                  "ratio at the slowest single FILE; not a package property"),
    }
    print(json.dumps(summary), flush=True)
    print(f"\nratio (serial/auto): min={summary['ratio_min']} "
          f"median={summary['ratio_median']} max={summary['ratio_max']}\n"
          f"REPORT THE RANGE, NOT THE BEST NUMBER.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
