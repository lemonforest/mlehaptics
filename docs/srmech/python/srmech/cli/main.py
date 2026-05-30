"""srmech CLI entry point.

Wires the ``srmech`` (and ``siona``) console-script entry to a single
:func:`main` dispatch.

* v0.4.6rc2 shipped ``srmech status`` (out-of-band introspection of a
  running srmech sweep), backed by :mod:`srmech.cli.status`.
* v0.5.0rc4 adds ``srmech bus`` subcommands
  (``list / tap / pipe / send / serve``) for operating the v0.5.0
  bus from the shell, backed by :mod:`srmech.cli.bus`.

Usage::

    srmech status                       # list active sweep runs
    srmech status --pid 12345 -f        # follow one run

    srmech bus list                     # list active bus endpoints
    srmech bus serve NAME --echo        # minimal test server
    srmech bus send NAME EVENT_JSON     # one-shot request
    srmech bus tap NAME                 # stream broadcast events
    srmech bus pipe SRC DST             # forward SRC -> DST

``python -m srmech ...`` is equivalent.
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from . import bus as _bus_cli
from . import dsl as _dsl_cli
from . import mcp as _mcp_cli
from . import status as _status
from srmech.version import __version__ as _srmech_version


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argparse tree.

    Each subcommand wires its own argparse via its module-level
    ``add_arguments`` helper.
    """
    parser = argparse.ArgumentParser(
        prog="srmech",
        description=(
            "srmech command-line interface. v0.5.0rc4 ships two "
            "subcommands: ``status`` (out-of-band introspection of a "
            "running srmech sweep) and ``bus`` (operate the v0.5.0 "
            "cross-process bus)."
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
    bus_p = sub.add_parser(
        "bus",
        help=(
            "Operate the srmech.bus from the shell (list/tap/pipe/send/serve)."
        ),
        description=(
            "Operate the v0.5.0 srmech cross-process bus. Five "
            "subcommands: list (enumerate endpoints), tap (stream "
            "events), pipe (forward SRC->DST), send (one-shot "
            "request), serve (test server)."
        ),
    )
    _bus_cli.add_arguments(bus_p)
    dsl_p = sub.add_parser(
        "dsl",
        help=(
            "Operate the v0.5.0rc8 cascade DSL (run / ops / visualize)."
        ),
        description=(
            "Operate the v0.5.0rc8 cascade DSL runner (task #235). Three "
            "subcommands: run (execute a TOML chain spec), ops (list "
            "cascade-catalog ops), visualize (pretty-print a parsed "
            "chain's stage list)."
        ),
    )
    _dsl_cli.add_arguments(dsl_p)
    mcp_p = sub.add_parser(
        "mcp",
        help=(
            "Emit MCP integration artifacts (emit-mcpb: Claude Desktop "
            "bundle)."
        ),
        description=(
            "Operate srmech's MCP integration surface. v0.5.0rc22 "
            "sub-subcommand 'emit-mcpb' writes a Claude Desktop .mcpb "
            "bundle generated from srmech introspection (version + tool "
            "list derived; no hand-authored manifest)."
        ),
    )
    _mcp_cli.add_arguments(mcp_p)
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
    if args.command == "bus":
        return _bus_cli.run(args)
    if args.command == "dsl":
        return _dsl_cli.run(args)
    if args.command == "mcp":
        return _mcp_cli.run(args)
    parser.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover — exercised via __main__.py
    sys.exit(main())
