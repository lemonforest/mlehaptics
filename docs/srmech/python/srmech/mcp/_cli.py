"""``srmech-mcp`` console-script entry point (v0.5.0rc6).

Top-level CLI for the MCP server. Three transport modes (stdio /
http-sse) × two invoke modes (local / bus-proxy) = the three
Claude Code integration scenarios documented in the rc6 spec:

1. Pure local stdio subprocess (Claude Code default).
2. Cross-terminal observability (``--bus-endpoint NAME`` +
   ``--transport http-sse``).
3. Subagent-orchestrated research (Claude Code spawns the subagent
   with ``srmech-mcp`` registered).

The SAME adapter ships once; the transport + invoke mode is a
config switch.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any, Callable, Dict, List, Optional

from ..version import __version__ as _srmech_version
from ._server import MCPServer
from ._sse import serve_http_sse
from ._stdio import serve_stdio
from ._tools import compile_filter


# ──────────────────────────────────────────────────────────────────────
# argparse
# ──────────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    """Build the ``srmech-mcp`` argparse tree."""
    parser = argparse.ArgumentParser(
        prog="srmech-mcp",
        description=(
            "MCP (Model Context Protocol) server adapter for srmech. "
            "Exposes srmech.amsc.tool_schema registrations as MCP "
            "tools to Claude Code (and any other MCP-aware LLM "
            "client). v0.5.0rc6."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"srmech-mcp {_srmech_version}",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http-sse"],
        default="stdio",
        help=(
            "Transport mode. 'stdio' (default) is what Claude Code "
            "spawns when registered via mcpServers config. 'http-sse' "
            "binds a localhost port for cross-process / cross-terminal "
            "usage."
        ),
    )
    parser.add_argument(
        "--port",
        type=int,
        default=0,
        help=(
            "TCP port for --transport http-sse. 0 (default) asks the "
            "kernel to assign one (the chosen port is logged to stderr)."
        ),
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help=(
            "Bind host for --transport http-sse. Default 127.0.0.1 "
            "(localhost only). Set to 0.0.0.0 to accept connections "
            "from other hosts (use with care — there is no auth)."
        ),
    )
    parser.add_argument(
        "--name",
        default="srmech-mcp",
        help=(
            "Server name advertised in the MCP initialize handshake. "
            "Default 'srmech-mcp'."
        ),
    )
    parser.add_argument(
        "--filter",
        dest="name_filter",
        default=None,
        metavar="GLOB",
        help=(
            "Only expose tools whose name matches GLOB (fnmatch-style; "
            "e.g. 'srmech.amsc.cascade.*'). Default: expose everything."
        ),
    )
    parser.add_argument(
        "--bus-endpoint",
        dest="bus_endpoint",
        default=None,
        metavar="NAME",
        help=(
            "Connect to a running srmech.bus endpoint of this name and "
            "proxy tool calls through it instead of executing locally. "
            "Used by the 'cross-terminal observability' mode: a "
            "long-running sweep exposes its tool surface over the bus; "
            "Claude Code in another terminal connects via this adapter."
        ),
    )
    return parser


# ──────────────────────────────────────────────────────────────────────
# Bus-proxy invoke
# ──────────────────────────────────────────────────────────────────────


def make_bus_proxy_invoke(
    bus_endpoint: str,
) -> Callable[[str, Dict[str, Any]], Any]:
    """Build an invoke callable that proxies tools/call through a
    running srmech.bus endpoint.

    The bus event protocol used here::

        {"type": "mcp.tools.call",
         "payload": {"name": "<tool-name>", "arguments": {...}}}

    The bus endpoint's handler must reply with a dict carrying a
    ``result`` key (and optional ``error`` key, non-null/non-empty
    when the tool failed). Per :func:`srmech.bus.serve`'s contract,
    the WHOLE handler return dict becomes the wire-event payload —
    so the receiver reads the result via ``reply["payload"]["result"]``
    and the error via ``reply["payload"]["error"]``.

    A non-null ``error`` is re-raised as an exception so the MCP
    dispatcher surfaces it as an MCP isError=true response (per
    spec, tool errors are success-shaped JSON-RPC responses with
    isError=true).
    """
    # Lazy-import: srmech.bus is a non-trivial import surface and the
    # default stdio mode doesn't need it.
    from ..bus import connect

    def _invoke(name: str, arguments: Dict[str, Any]) -> Any:
        with connect(bus_endpoint) as ch:
            reply = ch.send({
                "type": "mcp.tools.call",
                "payload": {"name": name, "arguments": arguments},
            })
        if reply is None:
            raise RuntimeError(
                f"bus endpoint {bus_endpoint!r} returned no reply"
            )
        payload = reply.get("payload") or {}
        err = payload.get("error")
        if err:
            raise RuntimeError(str(err))
        return payload.get("result")

    return _invoke


# ──────────────────────────────────────────────────────────────────────
# main
# ──────────────────────────────────────────────────────────────────────


def main(argv: Optional[List[str]] = None) -> int:
    """``srmech-mcp`` console-script entry."""
    parser = build_parser()
    args = parser.parse_args(argv)

    name_filter = compile_filter(args.name_filter)
    invoke_override = (
        make_bus_proxy_invoke(args.bus_endpoint)
        if args.bus_endpoint
        else None
    )
    server = MCPServer(
        name=args.name,
        name_filter=name_filter,
        invoke_override=invoke_override,
    )

    if args.transport == "stdio":
        return serve_stdio(server=server)

    # http-sse
    handle = serve_http_sse(
        name=args.name,
        host=args.host,
        port=args.port,
        server=server,
        background=True,
    )
    bound_host, bound_port = handle.address
    print(
        f"srmech-mcp: serving MCP over HTTP+SSE on "
        f"http://{bound_host}:{bound_port}/sse",
        file=sys.stderr,
        flush=True,
    )
    print(
        f"srmech-mcp: post messages to "
        f"http://{bound_host}:{bound_port}/message?session=<ID>",
        file=sys.stderr,
        flush=True,
    )
    try:
        # Block forever; the inner thread serves requests.
        handle._thread.join()  # noqa: SLF001 — same-package handle
    except KeyboardInterrupt:
        print("srmech-mcp: keyboard interrupt; shutting down",
              file=sys.stderr, flush=True)
    finally:
        handle.stop()
    return 0


if __name__ == "__main__":  # pragma: no cover — exercised via subprocess
    sys.exit(main())
