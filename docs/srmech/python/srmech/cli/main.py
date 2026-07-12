"""srmech CLI entry point.

Wires the ``srmech`` console-script entry to a single
:func:`main` dispatch. **Five subcommands** — ``status`` / ``bus`` /
``dsl`` / ``mcp`` / ``class``:

* v0.4.6rc2 shipped ``srmech status`` (out-of-band introspection of a
  running srmech sweep), backed by :mod:`srmech.cli.status`.
* v0.5.0rc4 added the ``srmech bus`` subcommand family
  (``list / tap / pipe / send / serve``) for operating the v0.5.0
  cross-process bus from the shell, backed by :mod:`srmech.cli.bus`.
* v0.5.0 added ``srmech mcp`` (emit Model Context Protocol
  integration artifacts for Claude Desktop), backed by
  :mod:`srmech.cli.mcp`.
* v0.5.0rc8 added ``srmech dsl`` (compose / run cascade chains),
  backed by :mod:`srmech.cli.dsl`.
* v0.7.5rc41 added ``srmech class`` (discover user-declared [class]
  classes — list / describe), backed by :mod:`srmech.cli.klass`.

Usage::

    srmech status                       # list active sweep runs
    srmech status --pid 12345 -f        # follow one run

    srmech bus list                     # list active bus endpoints
    srmech bus serve NAME --echo        # minimal test server
    srmech bus send NAME EVENT_JSON     # one-shot request
    srmech bus tap NAME                 # stream broadcast events
    srmech bus pipe SRC DST             # forward SRC -> DST

    srmech dsl run SPEC.toml            # run a cascade chain spec
    srmech dsl ops                      # list cascade ops
    srmech mcp emit-mcpb                # write a Claude Desktop bundle
    srmech class list                   # list user-declared classes
    srmech class describe Genome        # one class's fields + methods

``python -m srmech ...`` is equivalent.
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from . import bus as _bus_cli
from . import dsl as _dsl_cli
from . import klass as _class_cli
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
            "srmech command-line interface. Five subcommands: ``status`` "
            "(out-of-band introspection of a running srmech sweep), "
            "``bus`` (operate the cross-process bus), ``dsl`` (compose / "
            "run cascade chains), ``mcp`` (emit Model Context Protocol "
            "integration artifacts for Claude Desktop), and ``class`` "
            "(discover user-declared [class] classes — list / describe)."
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
            "Operate srmech's MCP integration surface. v0.5.0 "
            "sub-subcommand 'emit-mcpb' writes a Claude Desktop .mcpb "
            "bundle generated from srmech introspection (version + tool "
            "list derived; no hand-authored manifest)."
        ),
    )
    _mcp_cli.add_arguments(mcp_p)
    class_p = sub.add_parser(
        "class",
        help=(
            "Discover user-declared [class] classes (list / describe)."
        ),
        description=(
            "Discover the user-declared classes srmech constructs from [class] "
            "TOML (#962 Part 2). Two sub-subcommands: list (enumerate the seed "
            "Genome + bring-your-own classes), describe (full JSON descriptor "
            "of one class's fields + methods)."
        ),
    )
    _class_cli.add_arguments(class_p)
    return parser


def _dispatch(args: argparse.Namespace) -> int:
    """Route a parsed namespace to its subcommand run body (the pure if-chain
    both the native + argparse paths share). A ``None`` command (a bare
    ``srmech``) prints the top-level help and returns 0."""
    if args.command == "status":
        return _status.run(args)
    if args.command == "bus":
        return _bus_cli.run(args)
    if args.command == "dsl":
        return _dsl_cli.run(args)
    if args.command == "mcp":
        return _mcp_cli.run(args)
    if args.command == "class":
        return _class_cli.run(args)
    build_parser().print_help()
    return 0


# Map the C ``srmech_cli_dispatch`` route → the subcommand run body. Keyed by the
# rc193 ``_native.CLI_ROUTE_*`` constants (resolved lazily so a pure host that
# never imports _native still works).
def _run_native_route(route: int, args: argparse.Namespace, _native) -> int:
    if route == _native.CLI_ROUTE_STATUS:
        return _status.run(args)
    if route == _native.CLI_ROUTE_BUS:
        return _bus_cli.run(args)
    if route == _native.CLI_ROUTE_DSL:
        return _dsl_cli.run(args)
    if route == _native.CLI_ROUTE_MCP:
        return _mcp_cli.run(args)
    if route == _native.CLI_ROUTE_CLASS:
        return _class_cli.run(args)
    build_parser().print_help()          # CLI_ROUTE_HELP — a bare ``srmech``
    return 0


def _namespace_from_native(payload: bytes) -> argparse.Namespace:
    """Reconstruct the argparse Namespace from the C parser's canonical JSON,
    coercing the numeric-typed fields to match ``type=int`` / ``type=float``."""
    import json

    ns = json.loads(payload.decode("utf-8"))
    for key in ("pid", "limit"):
        if ns.get(key) is not None:
            ns[key] = int(ns[key])
    for key in ("poll_interval", "timeout"):
        if ns.get(key) is not None:
            ns[key] = float(ns[key])
    return argparse.Namespace(**ns)


def _native_dispatch(argv_list: List[str]) -> Optional[tuple]:
    """Parse + route ``argv_list`` through the C ``srmech_cli_parse`` /
    ``srmech_cli_dispatch`` (rc193 HOST-GLUE). Returns a 1-tuple ``(exit_code,)``
    when the C parser handled a clean RUN invocation (committed — its run body's
    result / exceptions are the answer), or ``None`` to DEFER to pure argparse
    (help / version / an arg error / anything the bounded C grammar declines —
    pure argparse then emits byte-identical help/version/error text + exit code).
    """
    try:
        from srmech.amsc import _native
    except Exception:  # pragma: no cover — _native always imports
        return None
    parsed = _native.cli_parse_c(argv_list)
    if parsed is None:
        return None
    action, payload = parsed
    if action != _native.CLI_ACTION_RUN:
        return None                       # help / version / error → pure argparse
    route = _native.cli_dispatch_c(payload)
    if route is None:
        return None
    try:
        args = _namespace_from_native(payload)
    except Exception:                     # malformed payload → defer, never wrong
        return None
    # Committed to the native path: run the body + return its code (do NOT catch
    # its exceptions / fall back — that would double-run a side-effecting body).
    return (_run_native_route(route, args, _native),)


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

    rc193: the C ``srmech_cli_parse`` + ``srmech_cli_dispatch`` HOST-GLUE peer
    parses + routes the subcommand grammar natively on the clean RUN path (a
    bare-C host runs the whole console-script dispatch in C); help / version /
    errors / anything the bounded parser declines fall through to pure argparse
    below (byte-identical, hasattr-guarded so a stale / pure host stays pure).
    """
    argv_list = list(sys.argv[1:] if argv is None else argv)
    native = _native_dispatch(argv_list)
    if native is not None:
        return native[0]
    parser = build_parser()
    args = parser.parse_args(argv)
    return _dispatch(args)


if __name__ == "__main__":  # pragma: no cover — exercised via __main__.py
    sys.exit(main())
