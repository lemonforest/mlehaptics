"""Tests for srmech.mcp — MCP server adapter (v0.5.0rc6).

Covers the JSON-RPC dispatch core (:class:`srmech.mcp.MCPServer`),
the ToolEntry -> MCP-def converter, the stdio transport (via
subprocess round-trip), the HTTP+SSE transport (via socket
round-trip), the ``srmech-mcp`` CLI entry, the ``--filter`` flag,
the ``--bus-endpoint`` proxy mode, and the MPR attestation
discipline carried on every tool-call response.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import threading
import time
import urllib.request
from http.client import HTTPConnection
from typing import Any, Dict, Iterator, List, Tuple

import pytest

# Force bus tools to register so coverage matches the runtime baseline.
import srmech.bus  # noqa: F401 — import side-effect

import srmech
from srmech.amsc.tool_schema import get_tool_schema
from srmech.mcp import (
    MCP_PROTOCOL_VERSION,
    MCPError,
    MCPServer,
    invoke_tool,
    serve_http_sse,
    tool_entries_to_mcp_defs,
)
from srmech.mcp._server import (
    JSONRPC_INVALID_PARAMS,
    JSONRPC_METHOD_NOT_FOUND,
    MCP_TOOL_ERROR,
    build_attestation,
)
from srmech.mcp._tools import (
    compile_filter,
    serialise_result,
    tool_entry_to_mcp_def,
)


# ──────────────────────────────────────────────────────────────────────
# Tool conversion: every ToolEntry yields a valid MCP tool def
# ──────────────────────────────────────────────────────────────────────


def test_every_tool_entry_converts_to_valid_mcp_def() -> None:
    """Every registered ToolEntry must produce a well-formed MCP
    tool def (``name`` + ``description`` + ``inputSchema`` with
    object-type root)."""
    defs = list(tool_entries_to_mcp_defs())
    assert len(defs) > 50, (
        f"expected ~150 registered tools; got {len(defs)}"
    )
    seen_names = set()
    for d in defs:
        assert "name" in d and isinstance(d["name"], str) and d["name"]
        assert d["name"] not in seen_names, (
            f"duplicate MCP tool name {d['name']!r}"
        )
        seen_names.add(d["name"])
        assert "description" in d and isinstance(d["description"], str)
        assert "inputSchema" in d
        sch = d["inputSchema"]
        assert sch["type"] == "object"
        assert "properties" in sch and isinstance(sch["properties"], dict)
        assert "required" in sch and isinstance(sch["required"], list)


def test_tool_entry_to_mcp_def_known_shape() -> None:
    """A specific ToolEntry (``sha256_bytes``) renders the expected
    shape end-to-end."""
    entry = get_tool_schema().lookup("srmech.amsc.format.sha256_bytes")
    assert entry is not None
    d = tool_entry_to_mcp_def(entry)
    assert d["name"] == "srmech.amsc.format.sha256_bytes"
    assert "data" in d["inputSchema"]["properties"]
    assert "data" in d["inputSchema"]["required"]
    # Returned-type hint is in the description.
    assert "Returns: str" in d["description"]
    assert "category: format" in d["description"]


def test_filter_predicate_compiles_glob() -> None:
    """``compile_filter`` builds a callable that matches fnmatch
    patterns."""
    pred = compile_filter("srmech.amsc.cascade.*")
    assert pred is not None
    assert pred("srmech.amsc.cascade.chiral_flip")
    assert not pred("srmech.amsc.format.sha256_bytes")
    assert compile_filter(None) is None


def test_filter_reduces_exposed_tool_count() -> None:
    """``tool_entries_to_mcp_defs`` honours the filter predicate."""
    all_defs = list(tool_entries_to_mcp_defs())
    pred = compile_filter("srmech.amsc.cascade.*")
    cascade_defs = list(tool_entries_to_mcp_defs(name_filter=pred))
    assert 0 < len(cascade_defs) < len(all_defs)
    for d in cascade_defs:
        assert d["name"].startswith("srmech.amsc.cascade.")


# ──────────────────────────────────────────────────────────────────────
# Direct invocation
# ──────────────────────────────────────────────────────────────────────


def test_invoke_tool_chiral_flip_roundtrips() -> None:
    """A simple known tool round-trips through invoke_tool."""
    result = invoke_tool(
        "srmech.amsc.cascade.chiral_flip",
        {"seq": [1, 2, 3, 4]},
    )
    assert result == [4, 3, 2, 1]


def test_invoke_tool_sha256_bytes_with_hex_coercion() -> None:
    """bytes parameters arrive as hex strings (MCP rides JSON, which
    has no bytes type); ``invoke_tool`` coerces them back."""
    # "abc" hex -> "616263"
    result = invoke_tool(
        "srmech.amsc.format.sha256_bytes",
        {"data": b"abc".hex()},
    )
    assert isinstance(result, str)
    assert len(result) == 64
    # Compare against hashlib (route through sha256 of raw bytes —
    # the value the underlying callable computed).
    expected = hashlib.sha256(b"abc").hexdigest()
    assert result == expected


def test_invoke_tool_unknown_raises_mcp_tool_error() -> None:
    """Unknown tool name -> MCPToolError."""
    from srmech.mcp._tools import MCPToolError
    with pytest.raises(MCPToolError):
        invoke_tool("srmech.nope.does_not_exist", {})


# ──────────────────────────────────────────────────────────────────────
# Result serialisation
# ──────────────────────────────────────────────────────────────────────


def test_serialise_result_handles_bytes_tuples_paths() -> None:
    """JSON-text rendering of awkward Python objects."""
    out = serialise_result({"hex": b"\x00\xff", "tup": (1, 2)})
    parsed = json.loads(out)
    assert parsed["hex"] == "00ff"
    assert parsed["tup"] == [1, 2]


def test_serialise_result_numpy_arrays() -> None:
    """numpy arrays are tolist'd through the fallback."""
    import numpy as np
    out = serialise_result(np.array([1.0, 2.0, 3.0]))
    assert json.loads(out) == [1.0, 2.0, 3.0]


# ──────────────────────────────────────────────────────────────────────
# MCPServer dispatch
# ──────────────────────────────────────────────────────────────────────


def test_initialize_handshake_returns_server_info() -> None:
    """``initialize`` returns serverInfo + capabilities + protocolVersion."""
    srv = MCPServer(name="test-srv")
    resp = srv.handle({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "0.1"},
        },
    })
    assert resp is not None
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 1
    result = resp["result"]
    assert result["serverInfo"]["name"] == "test-srv"
    assert result["serverInfo"]["version"] == srmech.__version__
    assert "tools" in result["capabilities"]
    assert result["protocolVersion"] == MCP_PROTOCOL_VERSION


def test_notifications_initialized_returns_none() -> None:
    """Notifications produce no response."""
    srv = MCPServer()
    resp = srv.handle({
        "jsonrpc": "2.0", "method": "notifications/initialized",
    })
    assert resp is None


def test_tools_list_returns_all_tools() -> None:
    """tools/list returns the full registered tool surface."""
    srv = MCPServer()
    resp = srv.handle({
        "jsonrpc": "2.0", "id": 2, "method": "tools/list",
    })
    assert resp is not None
    tools = resp["result"]["tools"]
    assert len(tools) > 50
    names = {t["name"] for t in tools}
    assert "srmech.amsc.cascade.chiral_flip" in names


def test_tools_list_honours_filter() -> None:
    """tools/list honours the constructor's name_filter."""
    pred = compile_filter("srmech.amsc.cascade.*")
    srv = MCPServer(name_filter=pred)
    resp = srv.handle({
        "jsonrpc": "2.0", "id": 1, "method": "tools/list",
    })
    assert resp is not None
    tools = resp["result"]["tools"]
    assert all(t["name"].startswith("srmech.amsc.cascade.") for t in tools)


def test_tools_call_invokes_tool_and_returns_attestation() -> None:
    """tools/call returns content + isError=false + MPR attestation."""
    srv = MCPServer()
    resp = srv.handle({
        "jsonrpc": "2.0", "id": 3, "method": "tools/call",
        "params": {
            "name": "srmech.amsc.cascade.chiral_flip",
            "arguments": {"seq": [1, 2, 3]},
        },
    })
    assert resp is not None
    result = resp["result"]
    assert result["isError"] is False
    assert result["content"][0]["type"] == "text"
    assert json.loads(result["content"][0]["text"]) == [3, 2, 1]
    att = result["attestation"]
    assert att["mpr_version"] == "1.0"
    assert att["tool_name"] == "srmech.amsc.cascade.chiral_flip"
    assert att["parser_version"].startswith("srmech ")
    assert len(att["response_sha256"]) == 64


def test_tools_call_bad_name_returns_invalid_params() -> None:
    """tools/call without a name -> JSON-RPC invalid-params error."""
    srv = MCPServer()
    resp = srv.handle({
        "jsonrpc": "2.0", "id": 4, "method": "tools/call",
        "params": {"arguments": {}},
    })
    assert resp is not None
    assert "error" in resp
    assert resp["error"]["code"] == JSONRPC_INVALID_PARAMS


def test_tools_call_filtered_tool_returns_method_not_found() -> None:
    """A tool filtered out by --filter is not callable."""
    pred = compile_filter("srmech.amsc.format.*")  # cascade excluded
    srv = MCPServer(name_filter=pred)
    resp = srv.handle({
        "jsonrpc": "2.0", "id": 5, "method": "tools/call",
        "params": {
            "name": "srmech.amsc.cascade.chiral_flip",
            "arguments": {"seq": [1, 2, 3]},
        },
    })
    assert resp is not None
    assert "error" in resp
    assert resp["error"]["code"] == JSONRPC_METHOD_NOT_FOUND


def test_tools_call_unknown_tool_returns_is_error_response() -> None:
    """tools/call of an unregistered name returns isError=true (not
    a JSON-RPC error — per MCP spec, tool errors are success-shaped).
    """
    srv = MCPServer()
    resp = srv.handle({
        "jsonrpc": "2.0", "id": 6, "method": "tools/call",
        "params": {"name": "srmech.does_not_exist", "arguments": {}},
    })
    assert resp is not None
    assert "result" in resp
    assert resp["result"]["isError"] is True
    assert resp["result"]["content"][0]["type"] == "text"


def test_tools_call_runtime_exception_returns_is_error_response() -> None:
    """A tool that raises at runtime surfaces as isError=true (not a
    JSON-RPC error)."""
    srv = MCPServer()
    # Pass invalid args to a real tool to provoke a TypeError.
    resp = srv.handle({
        "jsonrpc": "2.0", "id": 7, "method": "tools/call",
        "params": {
            "name": "srmech.amsc.cascade.chiral_flip",
            "arguments": {"not_the_param_name": 123},
        },
    })
    assert resp is not None
    assert resp["result"]["isError"] is True


def test_unknown_method_returns_method_not_found() -> None:
    """An unknown method (non-notification) yields method-not-found."""
    srv = MCPServer()
    resp = srv.handle({"jsonrpc": "2.0", "id": 8, "method": "wat"})
    assert resp is not None
    assert resp["error"]["code"] == JSONRPC_METHOD_NOT_FOUND


def test_unknown_notification_silently_ignored() -> None:
    """Unknown notification — silent per spec."""
    srv = MCPServer()
    resp = srv.handle({"jsonrpc": "2.0", "method": "notifications/anything"})
    assert resp is None


def test_ping_method_returns_empty_result() -> None:
    """ping (utility method) returns empty result."""
    srv = MCPServer()
    resp = srv.handle({"jsonrpc": "2.0", "id": 9, "method": "ping"})
    assert resp is not None
    assert resp["result"] == {}


def test_build_attestation_reproducible() -> None:
    """build_attestation populates the MPR-style fields with a
    SHA-256 over the canonical concatenation."""
    att = build_attestation(tool_name="foo", result_text="bar")
    assert att["mpr_version"] == "1.0"
    assert att["tool_name"] == "foo"
    assert len(att["response_sha256"]) == 64
    # Hash must change when content changes.
    att2 = build_attestation(tool_name="foo", result_text="other")
    assert att["response_sha256"] != att2["response_sha256"]


# ──────────────────────────────────────────────────────────────────────
# stdio transport: subprocess round-trip
# ──────────────────────────────────────────────────────────────────────


def _send_one_recv_one(
    p: "subprocess.Popen", msg: Dict[str, Any]
) -> Dict[str, Any]:
    """Send one JSON-RPC line and read one line of response."""
    line = json.dumps(msg) + "\n"
    assert p.stdin is not None
    assert p.stdout is not None
    p.stdin.write(line)
    p.stdin.flush()
    raw = p.stdout.readline()
    assert raw, f"subprocess closed stdout: stderr={p.stderr.read() if p.stderr else ''!r}"
    return json.loads(raw)


def test_stdio_subprocess_full_handshake() -> None:
    """End-to-end MCP handshake over stdio via subprocess."""
    p = subprocess.Popen(
        [sys.executable, "-m", "srmech.mcp._cli"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    try:
        # initialize
        init_resp = _send_one_recv_one(p, {
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "0.1"},
            },
        })
        assert init_resp["result"]["serverInfo"]["name"] == "srmech-mcp"

        # tools/list
        list_resp = _send_one_recv_one(p, {
            "jsonrpc": "2.0", "id": 2, "method": "tools/list",
        })
        tools = list_resp["result"]["tools"]
        assert len(tools) > 50

        # tools/call (chiral_flip — a guaranteed-present tool)
        call_resp = _send_one_recv_one(p, {
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {
                "name": "srmech.amsc.cascade.chiral_flip",
                "arguments": {"seq": [10, 20, 30]},
            },
        })
        assert call_resp["result"]["isError"] is False
        assert json.loads(
            call_resp["result"]["content"][0]["text"]
        ) == [30, 20, 10]
    finally:
        if p.stdin is not None:
            p.stdin.close()
        try:
            p.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            p.kill()


def test_stdio_subprocess_exits_cleanly_on_eof() -> None:
    """Closing stdin shuts the server down with exit code 0."""
    p = subprocess.Popen(
        [sys.executable, "-m", "srmech.mcp._cli"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert p.stdin is not None
    p.stdin.close()
    rc = p.wait(timeout=5.0)
    assert rc == 0


# ──────────────────────────────────────────────────────────────────────
# HTTP+SSE transport
# ──────────────────────────────────────────────────────────────────────


def _sse_initial_events(host: str, port: int) -> Iterator[Tuple[str, str]]:
    """Open ``GET /sse``, yield ``(event-name, data)`` tuples as
    they arrive. Generator stops when the connection is closed
    upstream."""
    conn = HTTPConnection(host, port, timeout=5.0)
    conn.request("GET", "/sse", headers={"Accept": "text/event-stream"})
    resp = conn.getresponse()
    assert resp.status == 200
    buf = b""
    while True:
        chunk = resp.read1(4096)
        if not chunk:
            return
        buf += chunk
        while b"\n\n" in buf:
            event_chunk, buf = buf.split(b"\n\n", 1)
            evt_name = ""
            data_parts: List[str] = []
            for line in event_chunk.decode("utf-8").splitlines():
                if line.startswith("event: "):
                    evt_name = line[len("event: "):].strip()
                elif line.startswith("data: "):
                    data_parts.append(line[len("data: "):])
            yield (evt_name, "\n".join(data_parts))


def test_http_sse_round_trip() -> None:
    """End-to-end MCP round-trip over the HTTP+SSE transport."""
    handle = serve_http_sse(name="test-sse", port=0, background=True)
    try:
        host, port = handle.address
        # Spawn the SSE reader on a background thread so we can POST
        # the initialize request concurrently.
        received: List[Tuple[str, str]] = []
        endpoint_holder: List[str] = []
        reader_started = threading.Event()
        done = threading.Event()

        def _reader() -> None:
            reader_started.set()
            for evt, data in _sse_initial_events(host, port):
                received.append((evt, data))
                if evt == "endpoint" and not endpoint_holder:
                    endpoint_holder.append(data)
                if evt == "message":
                    done.set()
                    return

        t = threading.Thread(target=_reader, daemon=True)
        t.start()
        # Wait for the endpoint event.
        for _ in range(100):
            if endpoint_holder:
                break
            time.sleep(0.05)
        assert endpoint_holder, "no endpoint event received"
        endpoint_url = endpoint_holder[0]
        # POST one initialize request to that endpoint.
        body = json.dumps({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "sse-test", "version": "0.1"},
            },
        }).encode("utf-8")
        conn = HTTPConnection(host, port, timeout=5.0)
        conn.request(
            "POST", endpoint_url, body=body,
            headers={"Content-Type": "application/json"},
        )
        resp = conn.getresponse()
        assert resp.status == 202
        resp.read()
        # The actual response rides over SSE.
        assert done.wait(timeout=5.0), "no message event from /sse"
        # Find the message event.
        message_evt = next(
            (data for evt, data in received if evt == "message"), None
        )
        assert message_evt is not None
        parsed = json.loads(message_evt)
        assert parsed["result"]["serverInfo"]["name"] == "test-sse"
    finally:
        handle.stop()


def test_http_sse_healthz() -> None:
    """``GET /healthz`` returns 200 + ``{"status":"ok"}``."""
    handle = serve_http_sse(port=0, background=True)
    try:
        host, port = handle.address
        with urllib.request.urlopen(
            f"http://{host}:{port}/healthz", timeout=5.0
        ) as resp:
            assert resp.status == 200
            body = json.loads(resp.read())
            assert body == {"status": "ok"}
    finally:
        handle.stop()


def test_http_sse_unknown_path_404() -> None:
    """Unknown GET path -> 404."""
    handle = serve_http_sse(port=0, background=True)
    try:
        host, port = handle.address
        conn = HTTPConnection(host, port, timeout=5.0)
        conn.request("GET", "/no-such-path")
        resp = conn.getresponse()
        assert resp.status == 404
        resp.read()
    finally:
        handle.stop()


# ──────────────────────────────────────────────────────────────────────
# Bus-endpoint proxy mode
# ──────────────────────────────────────────────────────────────────────


def test_bus_endpoint_invoke_proxies_through_bus(tmp_path) -> None:
    """``--bus-endpoint NAME`` mode: tool calls flow through a real
    srmech.bus endpoint. We register a handler that pretends to
    execute the tool and verify the proxy round-trip."""
    from srmech.bus import serve as bus_serve
    from srmech.mcp._cli import make_bus_proxy_invoke

    endpoint_name = f"mcp-rc6-test-{int(time.time() * 1000) % 100000}"

    invocations: List[Dict[str, Any]] = []

    def handler(event: Dict[str, Any]) -> Dict[str, Any]:
        if event["type"] != "mcp.tools.call":
            return {"type": "ignored"}
        invocations.append(event["payload"])
        # The bus reflects the WHOLE handler dict back as payload
        # (per srmech.bus.serve contract). Returning result/error at
        # the top level puts them at reply["payload"]["result"] and
        # reply["payload"]["error"] — which is the shape the proxy
        # invoke callable reads.
        return {
            "type": "mcp.tools.call.reply",
            "result": ["pretend", "result"],
            "error": None,
        }

    with bus_serve(endpoint_name, handler=handler):
        proxy_invoke = make_bus_proxy_invoke(endpoint_name)
        # Build a server that uses the proxy.
        srv = MCPServer(invoke_override=proxy_invoke)
        resp = srv.handle({
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {
                "name": "srmech.amsc.cascade.chiral_flip",
                "arguments": {"seq": [1, 2]},
            },
        })

    assert resp is not None
    assert resp["result"]["isError"] is False
    assert json.loads(
        resp["result"]["content"][0]["text"]
    ) == ["pretend", "result"]
    assert len(invocations) == 1
    assert invocations[0]["name"] == "srmech.amsc.cascade.chiral_flip"
    assert invocations[0]["arguments"] == {"seq": [1, 2]}


# ──────────────────────────────────────────────────────────────────────
# CLI surface
# ──────────────────────────────────────────────────────────────────────


def test_cli_help_exits_zero() -> None:
    """``srmech-mcp --help`` exits 0 with the expected usage line."""
    p = subprocess.run(
        [sys.executable, "-m", "srmech.mcp._cli", "--help"],
        capture_output=True, text=True,
    )
    assert p.returncode == 0
    assert "srmech-mcp" in p.stdout
    assert "--transport" in p.stdout
    assert "--bus-endpoint" in p.stdout
    assert "--filter" in p.stdout


def test_cli_version_exits_zero() -> None:
    """``srmech-mcp --version`` exits 0 with the current version."""
    p = subprocess.run(
        [sys.executable, "-m", "srmech.mcp._cli", "--version"],
        capture_output=True, text=True,
    )
    assert p.returncode == 0
    assert srmech.__version__ in p.stdout


def test_cli_filter_flag_subprocess() -> None:
    """``srmech-mcp --filter`` only exposes matching tools end-to-end."""
    p = subprocess.Popen(
        [sys.executable, "-m", "srmech.mcp._cli",
         "--filter", "srmech.amsc.cascade.*"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    try:
        # initialize then tools/list
        _send_one_recv_one(p, {
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {}, "clientInfo": {"name": "t", "version": "0"},
            },
        })
        list_resp = _send_one_recv_one(p, {
            "jsonrpc": "2.0", "id": 2, "method": "tools/list",
        })
        tools = list_resp["result"]["tools"]
        assert all(t["name"].startswith("srmech.amsc.cascade.") for t in tools)
    finally:
        if p.stdin is not None:
            p.stdin.close()
        try:
            p.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            p.kill()
