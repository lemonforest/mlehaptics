"""stdio JSON-RPC transport for the MCP server (Claude Code default).

Reads newline-delimited JSON-RPC requests from ``sys.stdin``, writes
newline-delimited JSON-RPC responses to ``sys.stdout``, and exits
cleanly on EOF (which is how the parent process — Claude Code —
shuts the server down: by closing the subprocess's stdin).

Per the MCP spec, the stdio transport is the default for subprocess
servers (the parent registers the server as
``{"command": "srmech-mcp"}``). One JSON object per line; we use
``json.dumps`` (no embedded newlines in the rendered string) so
line-delimited framing is unambiguous.

stderr is reserved for log output (the MCP spec says servers MAY
emit human-readable diagnostics to stderr; the parent typically
routes that to its own log).
"""

from __future__ import annotations

import json
import sys
from typing import Callable, Optional, TextIO

from ._server import MCPServer


def _read_one_request(stream: TextIO) -> Optional[dict]:
    """Read one newline-delimited JSON object. Returns ``None`` at EOF.

    Skips blank lines (defensive against editors that re-flow);
    raises ``ValueError`` on malformed JSON so the caller can surface
    a JSON-RPC parse-error response.
    """
    while True:
        line = stream.readline()
        if not line:
            return None  # EOF
        line = line.strip()
        if not line:
            continue
        return json.loads(line)


def _write_one_response(stream: TextIO, response: dict) -> None:
    """Write one newline-delimited JSON-RPC response and flush.

    We flush after every write so the parent process sees the
    response promptly (subprocess pipes are line-buffered or
    block-buffered depending on the platform; explicit flush is
    the safe default).
    """
    line = json.dumps(response, separators=(",", ":"), default=str)
    stream.write(line + "\n")
    stream.flush()


def serve_stdio(
    *,
    server: Optional[MCPServer] = None,
    stdin: Optional[TextIO] = None,
    stdout: Optional[TextIO] = None,
    stderr: Optional[TextIO] = None,
) -> int:
    """Run the MCP server over stdio JSON-RPC. Blocks until stdin EOF.

    Parameters
    ----------
    server
        Pre-configured :class:`MCPServer`. If ``None``, a default
        one (no filter, no bus-proxy) is constructed.
    stdin / stdout / stderr
        Override streams for tests. Default to ``sys.std*``.

    Returns
    -------
    int
        Process exit code (0 = clean shutdown via EOF).
    """
    s_in = stdin if stdin is not None else sys.stdin
    s_out = stdout if stdout is not None else sys.stdout
    s_err = stderr if stderr is not None else sys.stderr
    srv = server if server is not None else MCPServer()

    while True:
        try:
            request = _read_one_request(s_in)
        except json.JSONDecodeError as exc:
            # Parse error — can't recover the request id; emit a
            # null-id parse-error response per JSON-RPC 2.0.
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {exc}"},
            }
            _write_one_response(s_out, err_resp)
            continue
        except KeyboardInterrupt:  # pragma: no cover — tested via subprocess
            print("srmech-mcp: keyboard interrupt; shutting down",
                  file=s_err)
            return 0
        if request is None:
            # EOF — clean shutdown.
            return 0
        response = srv.handle(request)
        if response is not None:
            _write_one_response(s_out, response)


__all__ = ["serve_stdio"]
