"""MCP server core — JSON-RPC 2.0 dispatch + lifecycle.

The transport (:mod:`._stdio` or :mod:`._sse`) is responsible for
feeding decoded JSON-RPC request objects into :meth:`MCPServer.handle`
and writing the returned response objects back over its wire.

Wire protocol (per the MCP spec):

* ``initialize`` — handshake. Server responds with
  ``{serverInfo, capabilities, protocolVersion}``.
* ``notifications/initialized`` — fire-and-forget; server records it.
* ``tools/list`` — server lists exposed tool defs.
* ``tools/call`` — server invokes one tool; response carries the
  result text + MPR attestation block.
* ``shutdown`` / ``ping`` — server acks; transport closes after.

We support the ``2024-11-05`` MCP protocol version (current as of
Claude Code circa late 2024 / early 2025). The version string is
returned in the ``initialize`` response per spec.
"""

from __future__ import annotations

import datetime as _dt
import json
import time
from typing import Any, Callable, Dict, Optional

from ..amsc.format import sha256_bytes
from ..version import __version__ as _srmech_version
from ._tools import (
    MCPToolError,
    invoke_tool,
    serialise_result,
    tool_entries_to_mcp_defs,
)


# ──────────────────────────────────────────────────────────────────────
# Protocol constants
# ──────────────────────────────────────────────────────────────────────


MCP_PROTOCOL_VERSION: str = "2024-11-05"
"""MCP protocol version advertised in the initialize handshake.
This is the version Claude Code (circa late-2024 / 2025) speaks."""


MCP_SERVER_NAME: str = "srmech-mcp"
"""Default server name advertised in ``initialize.serverInfo``."""


# JSON-RPC error codes per the JSON-RPC 2.0 spec + MCP additions.
JSONRPC_PARSE_ERROR: int = -32700
JSONRPC_INVALID_REQUEST: int = -32600
JSONRPC_METHOD_NOT_FOUND: int = -32601
JSONRPC_INVALID_PARAMS: int = -32602
JSONRPC_INTERNAL_ERROR: int = -32603
MCP_TOOL_ERROR: int = -32000  # MCP-side application error band


# ──────────────────────────────────────────────────────────────────────
# Errors
# ──────────────────────────────────────────────────────────────────────


class MCPError(Exception):
    """Application-level MCP error. Carries a JSON-RPC error code."""

    def __init__(self, message: str, *, code: int = MCP_TOOL_ERROR) -> None:
        super().__init__(message)
        self.code = code


# ──────────────────────────────────────────────────────────────────────
# Attestation envelope (the MPR-discipline-aligned block carried on
# every tools/call response)
# ──────────────────────────────────────────────────────────────────────


def _iso_utc_now() -> str:
    """Current UTC time as an MPR-compatible ISO-8601 timestamp."""
    # MPR uses trailing-Z UTC, no microseconds (rendering convention
    # in srmech.amsc.format).
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_attestation(
    *,
    tool_name: str,
    result_text: str,
) -> Dict[str, Any]:
    """Build the MPR-style attestation block for one tool-call response.

    The ``response_sha256`` covers the canonicalised concatenation of
    tool name + parser version + result text + UTC timestamp so a
    consumer can recompute it from the JSON-RPC envelope alone.
    """
    parser_version = f"srmech {_srmech_version}"
    retrieved_at = _iso_utc_now()
    canon = (
        f"{tool_name}\x1f{parser_version}\x1f{result_text}\x1f{retrieved_at}"
    ).encode("utf-8")
    digest = sha256_bytes(canon)
    return {
        "mpr_version": "1.0",
        "tool_name": tool_name,
        "parser_version": parser_version,
        "retrieved_at": retrieved_at,
        "response_sha256": digest,
    }


# ──────────────────────────────────────────────────────────────────────
# MCPServer — dispatch core
# ──────────────────────────────────────────────────────────────────────


class MCPServer:
    """Dispatches one JSON-RPC request at a time. Stateless across
    calls except for the post-handshake ``_initialized`` flag.

    Parameters
    ----------
    name
        Server name returned in ``initialize.serverInfo``. Defaults
        to ``"srmech-mcp"``.
    name_filter
        Optional predicate ``str -> bool`` controlling which
        ToolEntries are exposed. ``None`` exposes the full registry.
    invoke_override
        Optional ``(name, arguments) -> Any`` to override the local
        invoke path. Used by the ``--bus-endpoint`` proxy mode where
        tool calls flow through a running ``srmech.bus`` endpoint
        instead of executing in-process.
    """

    def __init__(
        self,
        *,
        name: str = MCP_SERVER_NAME,
        name_filter: Optional[Callable[[str], bool]] = None,
        invoke_override: Optional[Callable[[str, Dict[str, Any]], Any]] = None,
    ) -> None:
        assert name, "MCPServer: name must be non-empty"
        self.name = name
        self._filter = name_filter
        self._invoke = invoke_override or invoke_tool
        self._initialized = False

    # ──────────────────────────────────────────────────────────────────
    # Public dispatch entry
    # ──────────────────────────────────────────────────────────────────

    def handle(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Dispatch one JSON-RPC request; return one JSON-RPC response
        (or ``None`` for notifications, which have no response).
        """
        assert isinstance(request, dict), \
            f"MCPServer.handle: expected dict, got {type(request).__name__}"

        # Notifications have no ``id`` field; per JSON-RPC 2.0, the
        # server MUST NOT respond to notifications.
        is_notification = "id" not in request
        req_id = request.get("id")
        method = request.get("method")

        if not isinstance(method, str):
            if is_notification:
                return None
            return self._error_response(
                req_id, JSONRPC_INVALID_REQUEST,
                "request missing string 'method' field",
            )

        params = request.get("params") or {}
        if not isinstance(params, dict):
            if is_notification:
                return None
            return self._error_response(
                req_id, JSONRPC_INVALID_PARAMS,
                "'params' must be an object",
            )

        try:
            if method == "initialize":
                result = self._handle_initialize(params)
                return self._ok_response(req_id, result)
            if method == "notifications/initialized":
                self._initialized = True
                return None  # notification — no response
            if method == "tools/list":
                result = self._handle_tools_list(params)
                return self._ok_response(req_id, result)
            if method == "tools/call":
                result = self._handle_tools_call(params)
                return self._ok_response(req_id, result)
            if method == "ping":
                return self._ok_response(req_id, {})
            if method == "shutdown":
                return self._ok_response(req_id, {})
            if is_notification:
                # Unknown notification — silently ignore per spec.
                return None
            return self._error_response(
                req_id, JSONRPC_METHOD_NOT_FOUND,
                f"unknown method {method!r}",
            )
        except MCPError as exc:
            if is_notification:
                return None
            return self._error_response(req_id, exc.code, str(exc))
        except Exception as exc:  # pragma: no cover — defensive
            if is_notification:
                return None
            return self._error_response(
                req_id, JSONRPC_INTERNAL_ERROR,
                f"internal error: {type(exc).__name__}: {exc}",
            )

    # ──────────────────────────────────────────────────────────────────
    # Per-method handlers
    # ──────────────────────────────────────────────────────────────────

    def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """``initialize`` handshake. Echoes the client's
        ``protocolVersion`` per spec (or our own when the client
        omitted one)."""
        client_pv = params.get("protocolVersion") or MCP_PROTOCOL_VERSION
        # Per MCP spec, the server is expected to advertise a protocol
        # version it supports; echo the client's when possible to make
        # an "accept what the client sent" round-trip explicit.
        return {
            "protocolVersion": str(client_pv),
            "serverInfo": {
                "name": self.name,
                "version": _srmech_version,
            },
            "capabilities": {
                # tools capability with an empty object signals "yes,
                # we expose tools; here are our defaults". The list
                # itself comes via tools/list.
                "tools": {},
            },
        }

    def _handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """``tools/list`` — enumerate exposed tool defs."""
        tools = list(tool_entries_to_mcp_defs(name_filter=self._filter))
        return {"tools": tools}

    def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """``tools/call`` — invoke one tool; return ``content`` +
        ``attestation`` block + ``isError`` flag (per MCP spec).
        """
        name = params.get("name")
        if not isinstance(name, str) or not name:
            raise MCPError(
                "tools/call: missing or empty 'name'",
                code=JSONRPC_INVALID_PARAMS,
            )
        if self._filter is not None and not self._filter(name):
            raise MCPError(
                f"tools/call: tool {name!r} is filtered out by --filter",
                code=JSONRPC_METHOD_NOT_FOUND,
            )
        arguments = params.get("arguments") or {}
        if not isinstance(arguments, dict):
            raise MCPError(
                "tools/call: 'arguments' must be an object",
                code=JSONRPC_INVALID_PARAMS,
            )
        try:
            raw = self._invoke(name, arguments)
        except MCPToolError as exc:
            # Tool-not-found / can't-resolve — return as MCP error
            # response, not as Python exception.
            return self._call_error_response(name, str(exc))
        except Exception as exc:
            # Tool raised at runtime — wrap as isError MCP response
            # (per spec, NOT a JSON-RPC error; tool errors are
            # success-shaped with isError=true so the LLM can read
            # them and retry).
            return self._call_error_response(
                name, f"{type(exc).__name__}: {exc}"
            )
        text = serialise_result(raw)
        return {
            "content": [{"type": "text", "text": text}],
            "isError": False,
            "attestation": build_attestation(
                tool_name=name, result_text=text
            ),
        }

    # ──────────────────────────────────────────────────────────────────
    # Response builders
    # ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _ok_response(req_id: Any, result: Any) -> Dict[str, Any]:
        """Build one JSON-RPC 2.0 success response."""
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    @staticmethod
    def _error_response(
        req_id: Any, code: int, message: str
    ) -> Dict[str, Any]:
        """Build one JSON-RPC 2.0 error response."""
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": code, "message": message},
        }

    @staticmethod
    def _call_error_response(name: str, message: str) -> Dict[str, Any]:
        """Build one tool-call error response (success-shaped with
        ``isError=true`` per the MCP spec — the LLM is expected to
        read these and possibly retry)."""
        return {
            "content": [{"type": "text", "text": message}],
            "isError": True,
            "attestation": build_attestation(
                tool_name=name, result_text=message
            ),
        }


__all__ = [
    "JSONRPC_INTERNAL_ERROR",
    "JSONRPC_INVALID_PARAMS",
    "JSONRPC_INVALID_REQUEST",
    "JSONRPC_METHOD_NOT_FOUND",
    "JSONRPC_PARSE_ERROR",
    "MCP_PROTOCOL_VERSION",
    "MCP_SERVER_NAME",
    "MCP_TOOL_ERROR",
    "MCPError",
    "MCPServer",
    "build_attestation",
]
