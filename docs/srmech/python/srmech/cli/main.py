"""srmech CLI entry point.

Wires the ``srmech`` (and ``siona``) console-script entry to a single
:func:`main` dispatch. v0.4.6rc2 ships one subcommand — ``status`` —
backed by :mod:`srmech.cli.status`.

Usage::

    srmech status                # list active publishing runs
    srmech status --pid 12345    # detail one run
    srmech status --pid 12345 -f # follow the run's event stream
    srmech status --json         # machine-readable list

``python -m srmech status ...`` is equivalent.
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from . import status as _status
from srmech.version import __version__ as _srmech_version


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argparse tree.

    Kept tiny — one subcommand for now. Each subcommand wires its
    own argparse via its module-level ``add_arguments`` helper.
    """
    parser = argparse.ArgumentParser(
        prog="srmech",
        description=(
            "srmech command-line interface. v0.4.6rc2 ships one "
            "subcommand: ``status`` (out-of-band introspection of a "
            "running srmech sweep)."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"srmech {_srmech_version}",
    )
    sub = parser.add_subparsers(dest="command", required=False)
    status_p = sub.add_parser(
        "status",
        help=(
            "List active publishing srmech runs, or detail one by PID."
        ),
        description=(
            "List active publishing srmech runs from the user's "
            "introspection directory (~/.srmech/). With --pid, show "
            "detail for one run; with -f, tail the run's event stream."
        ),
    )
    _status.add_arguments(status_p)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Dispatch one CLI invocation.

    Parameters
    ----------
    argv
        Argument list (excluding program name). ``None`` uses
        ``sys.argv[1:]``.

    Returns
    -------
    int
        Exit code (0 = success).
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "status":
        return _status.run(args)
    parser.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover — exercised via __main__.py
    sys.exit(main())
