"""``srmech status`` — out-of-band introspection of running srmech.

Reads ``~/.srmech/run-{pid}-{start_time_ns}.ndjson`` files via the
:mod:`srmech.introspect` API (no direct file IO here). The
implementation is intentionally thin — argparse plus three render
helpers (list / detail / follow).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
import time
from typing import List

from .. import introspect


def add_arguments(parser: argparse.ArgumentParser) -> None:
    """Attach ``srmech status`` arguments to ``parser``."""
    parser.add_argument(
        "--pid",
        type=int,
        default=None,
        help="Show detail for one run by PID (default: list all).",
    )
    parser.add_argument(
        "-f",
        "--follow",
        action="store_true",
        help=(
            "With --pid, tail the run's event stream until the "
            "publisher exits."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Machine-readable JSON output (list/detail; not follow).",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=0.5,
        help="Follow poll interval in seconds (default 0.5).",
    )


def _format_elapsed(elapsed_ms: int) -> str:
    """``HH:MM:SS`` from milliseconds, monotonically clipped."""
    secs = max(0, elapsed_ms // 1000)
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _print_list(runs: List[introspect.Run]) -> None:
    """Plain-text table of runs."""
    if not runs:
        print("No active publishing srmech runs.")
        print("")
        print(
            "Hint: wrap your sweep in `with srmech.introspect.publish():` "
            "or set SRMECH_PUBLISH_STATUS=1 before importing srmech."
        )
        return
    header = f"{'PID':<8} {'SCRIPT':<28} {'CURRENT OP':<32} {'ELAPSED':<10} {'STATUS':<10}"
    print(header)
    print("-" * len(header))
    for run in runs:
        script = (run.script_name or "?")[:28]
        op = (run.current_op or "?")[:32]
        elapsed = _format_elapsed(run.elapsed_ms)
        print(
            f"{run.pid:<8} {script:<28} {op:<32} {elapsed:<10} {run.status:<10}"
        )


def _print_detail(run: introspect.Run) -> None:
    """Multi-line detail for one run."""
    print(f"PID:         {run.pid}")
    print(f"Script:      {run.script_name or '?'}")
    print(f"Started:     {run.start_time}")
    print(f"Elapsed:     {_format_elapsed(run.elapsed_ms)}")
    print(f"Status:      {run.status}")
    print(f"Current op:  {run.current_op or '?'}")
    print(f"Class:       {run.current_class or '?'}")
    print(f"Event count: {run.event_count}")
    print(f"File:        {run.file_path}")


def _print_json_list(runs: List[introspect.Run]) -> None:
    payload = [
        {
            "pid": r.pid,
            "start_time_ns": r.start_time_ns,
            "start_time": r.start_time,
            "script_name": r.script_name,
            "current_op": r.current_op,
            "current_class": r.current_class,
            "elapsed_ms": r.elapsed_ms,
            "status": r.status,
            "event_count": r.event_count,
            "file_path": str(r.file_path),
        }
        for r in runs
    ]
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")


def _follow(run: introspect.Run, *, poll_interval_s: float) -> int:
    """Tail the run's event stream until done or Ctrl-C."""
    try:
        for event in run.follow(poll_interval_s=poll_interval_s):
            ts = event.started_ts
            class_label = (
                f"(Class {event.class_})" if event.class_ else ""
            )
            extra = ""
            if event.extra:
                # Compact one-line extras.
                bits = ", ".join(
                    f"{k}={v}" for k, v in sorted(event.extra.items())
                )
                extra = f"  {{{bits}}}"
            in_shape = (
                f"in_shape={event.input_shape}" if event.input_shape else ""
            )
            err = f"  ERROR={event.error}" if event.error else ""
            print(
                f"[{ts}] {event.op_name:<36} {class_label:<10} {in_shape}{extra}{err}"
            )
    except KeyboardInterrupt:
        print("", file=sys.stderr)
        return 130
    return 0


def run(args: argparse.Namespace) -> int:
    """Execute ``srmech status``."""
    if args.pid is not None:
        run_obj = introspect.by_pid(int(args.pid))
        if run_obj is None:
            print(
                f"No run found with PID {args.pid}.",
                file=sys.stderr,
            )
            return 1
        if args.follow:
            return _follow(
                run_obj, poll_interval_s=float(args.poll_interval)
            )
        if args.json:
            _print_json_list([run_obj])
            return 0
        _print_detail(run_obj)
        return 0
    runs = introspect.list()
    if args.json:
        _print_json_list(runs)
        return 0
    _print_list(runs)
    return 0
