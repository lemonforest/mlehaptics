"""srmech.mcp — Model Context Protocol server adapter (v0.5.0rc6).

Exposes :mod:`srmech.amsc.tool_schema` ``ToolEntry`` registrations
(~150, ~87 user-direction-stated baseline) to MCP-aware LLM clients
(Claude Code, Cline, Continue, …) as MCP tools. Per user direction
2026-05-28: user is on the Claude Code Max plan (no Anthropic
API/SDK tier), so MCP is the primary LLM integration path.

Quick start
-----------

Pure local subprocess (Claude Code default)::

    # Register in Claude Code's MCP config:
    #   {"mcpServers": {"srmech": {"command": "srmech-mcp"}}}
    # Claude Code spawns ``srmech-mcp`` as a stdio JSON-RPC subprocess
    # and the LLM sees srmech's tools as built-in.

Cross-terminal observability (bus-proxy mode)::

    # Terminal A — long-running srmech sweep exposes a bus endpoint
    #              named ``sweep-12345``.
    # Terminal B — expose its tool surface over HTTP+SSE:
    $ srmech-mcp --transport http-sse --port 9991 \\
                 --bus-endpoint sweep-12345
    # Terminal C — Claude Code connects to http://localhost:9991/sse
    #              and the LLM can inspect / steer / sample the live
    #              sweep through srmech.bus req/rep semantics.

Subagent-orchestrated research::

    # Claude Code's Agent tool spawns a sub-Claude with
    # ``srmech-mcp`` registered. The subagent runs cascade
    # compositions, reports back via Claude Code's subagent return
    # path. The SAME adapter ships once; the transport mode is a
    # config switch.

Python entry::

    from srmech.mcp import serve_stdio, serve_http_sse

    serve_stdio()                                 # blocks; Claude Code
                                                  # launches as subprocess
    serve_http_sse(name="srmech-mcp", port=0)     # bind localhost port;
                                                  # cross-terminal usage

Wire protocol
-------------
JSON-RPC 2.0 per `the MCP specification
<https://modelcontextprotocol.io/specification>`__. Five surfaces:

* ``initialize`` — handshake (returns ``serverInfo`` + ``capabilities``).
* ``notifications/initialized`` — one-way client notification.
* ``tools/list`` — enumerate exposed tools (filtered by ``--filter``).
* ``tools/call`` — invoke one tool; response carries the result text +
  MPR attestation block.
* shutdown on stdin close (subprocess transport) or server stop
  (HTTP+SSE).

Each ``tools/call`` response carries an MPR attestation block
(``response_sha256`` over the result + tool name + parser version +
timestamp). Same envelope discipline as the rest of srmech.

Framework reading
-----------------
Class M (cross-class bind) ∘ Class E (catalog enumeration) ∘ Class A
(content-addressing via SHA-256 attestation) ∘ Class B (TLV-shaped
JSON-RPC framing) extended to the LLM substrate-class boundary. The
LLM is one substrate-class-instance; the Python interpreter running
srmech is another; ``srmech.mcp`` is the bind operator.
"""

from __future__ import annotations

from ._server import (
    MCP_PROTOCOL_VERSION,
    MCPError,
    MCPServer,
)
from ._stdio import serve_stdio
from ._sse import serve_http_sse
from ._tools import (
    invoke_tool,
    tool_entries_to_mcp_defs,
)

__all__ = [
    "MCPError",
    "MCPServer",
    "MCP_PROTOCOL_VERSION",
    "invoke_tool",
    "serve_http_sse",
    "serve_stdio",
    "tool_entries_to_mcp_defs",
]
