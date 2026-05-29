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
import re
import subprocess
import sys
import threading
import time
import urllib.request
from http.client import HTTPConnection
from typing import Any, Dict, Iterator, List, Tuple

import numpy as np
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


# ──────────────────────────────────────────────────────────────────────
# Property-key validity ratchet (v0.5.0rc10)
#
# BUG 1 (found by a LIVE Anthropic API test of the rc9 adapter, NOT by
# the mocks): ``srmech.amsc.hdc.polar_bundle`` / ``klein4_bundle`` were
# registered with the param name ``*vectors`` — the Python varargs sigil
# leaked into the ToolParameter NAME, so the MCP/Anthropic input_schema
# carried a property KEY ``*vectors``. Anthropic rejected the WHOLE
# catalog with ``400 — input_schema.properties: Property keys should
# match pattern '^[a-zA-Z0-9_.-]{1,64}$'``. The same converter feeds
# both adapters, so this single ratchet guards every tool on BOTH paths.
# ──────────────────────────────────────────────────────────────────────

#: The Anthropic / MCP property-key grammar (anchored).
_ANTHROPIC_PROPERTY_KEY_RE = re.compile(r"^[a-zA-Z0-9_.-]{1,64}$")


def test_every_tool_property_key_matches_anthropic_grammar() -> None:
    """Every ``inputSchema.properties`` KEY of every registered tool
    must match Anthropic's ``^[a-zA-Z0-9_.-]{1,64}$`` grammar and
    contain no Python varargs/kwargs sigil (``*``).

    This is the ratchet that would have caught BUG 1 (the ``*vectors``
    leak). It runs through ``tool_entry_to_mcp_def`` — the converter
    BOTH the MCP server and the Anthropic SDK adapter use — so it
    locks down the property-key grammar for all ~155 tools on both
    transports at once.
    """
    schema = get_tool_schema()
    assert len(schema.tools) > 50, "tool registry unexpectedly small"
    offenders: List[Tuple[str, str]] = []
    for entry in schema.tools:
        mcp_def = tool_entry_to_mcp_def(entry)
        for key in mcp_def["inputSchema"]["properties"]:
            if "*" in key or not _ANTHROPIC_PROPERTY_KEY_RE.match(key):
                offenders.append((entry.name, key))
    assert not offenders, (
        "tool property keys violate Anthropic's "
        "'^[a-zA-Z0-9_.-]{1,64}$' grammar (a leaked Python varargs "
        f"sigil gets the whole catalog 400'd on the Anthropic path): "
        f"{offenders}"
    )


def test_required_keys_reference_real_properties() -> None:
    """Every name in ``inputSchema.required`` must be an actual key in
    ``inputSchema.properties`` — a sanity check that the defence-in-depth
    key sanitiser keeps ``required`` and ``properties`` in lockstep."""
    schema = get_tool_schema()
    for entry in schema.tools:
        mcp_def = tool_entry_to_mcp_def(entry)
        props = mcp_def["inputSchema"]["properties"]
        for req in mcp_def["inputSchema"]["required"]:
            assert req in props, (
                f"{entry.name}: required key {req!r} not in properties "
                f"{sorted(props)}"
            )


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
# Varargs dispatch (v0.5.0rc10)
#
# BUG 2 (found by the same LIVE Anthropic API test): ``invoke_tool``
# ended with ``fn(**coerced)`` — keyword-args only. For a variadic
# callable like ``hdc.polar_bundle(*vectors)``, ``fn(vectors=[...])``
# raises ``TypeError: got an unexpected keyword argument 'vectors'``.
# Both adapters route through ``invoke_tool``, so invoking either bundle
# tool was broken on BOTH paths. The fix detects a VAR_POSITIONAL slot
# via ``inspect.signature`` and unpacks the supplied list positionally.
#
# Vectors are built with the parity-test fixtures (``hdc.polar_random``
# / ``hdc.klein4_random``); each ndarray is ``tolist()``'d to emulate a
# JSON array (the wire form a real MCP / Anthropic client sends).
# ──────────────────────────────────────────────────────────────────────


def test_invoke_tool_polar_bundle_variadic_dispatches() -> None:
    """``hdc.polar_bundle`` (a ``*vectors`` variadic) invokes cleanly
    through ``invoke_tool`` — NOT a TypeError / MCPToolError.

    This is the test that would have caught BUG 2.
    """
    from srmech.amsc import hdc
    from srmech.mcp._tools import MCPToolError

    rng = np.random.default_rng(11)
    # JSON arrays decode to Python lists; emulate that wire form.
    vectors = [hdc.polar_random(16, rng).tolist() for _ in range(3)]
    try:
        result = invoke_tool(
            "srmech.amsc.hdc.polar_bundle", {"vectors": vectors}
        )
    except (TypeError, MCPToolError) as exc:  # pragma: no cover
        pytest.fail(f"variadic dispatch broke: {type(exc).__name__}: {exc}")
    # A real bundled result: a length-16 polar vector over {-1, 0, +1}.
    arr = np.asarray(result)
    assert arr.shape == (16,)
    assert set(np.unique(arr).tolist()) <= {-1, 0, 1}
    # Bit-exact against calling the reference directly with *args.
    expected = hdc.polar_bundle(*[np.asarray(v) for v in vectors])
    assert np.array_equal(arr, expected)


def test_invoke_tool_klein4_bundle_variadic_dispatches() -> None:
    """``hdc.klein4_bundle`` (a ``*vectors`` variadic) invokes cleanly
    through ``invoke_tool``. Companion to the polar test for BUG 2."""
    from srmech.amsc import hdc
    from srmech.mcp._tools import MCPToolError

    rng = np.random.default_rng(11)
    vectors = [hdc.klein4_random(16, rng).tolist() for _ in range(3)]
    try:
        result = invoke_tool(
            "srmech.amsc.hdc.klein4_bundle", {"vectors": vectors}
        )
    except (TypeError, MCPToolError) as exc:  # pragma: no cover
        pytest.fail(f"variadic dispatch broke: {type(exc).__name__}: {exc}")
    arr = np.asarray(result)
    assert arr.shape == (16,)
    assert set(np.unique(arr).tolist()) <= {0, 1, 2, 3}
    expected = hdc.klein4_bundle(*[np.asarray(v) for v in vectors])
    assert np.array_equal(arr, expected)


def test_invoke_tool_variadic_tolerates_legacy_sigil_key() -> None:
    """Belt-and-braces: a caller that still sends the historical
    sigil-prefixed key (``*vectors``) is tolerated (the dispatcher
    falls back to it), so no in-flight client breaks on the rename."""
    from srmech.amsc import hdc

    rng = np.random.default_rng(7)
    vectors = [hdc.polar_random(8, rng).tolist() for _ in range(3)]
    result = invoke_tool(
        "srmech.amsc.hdc.polar_bundle", {"*vectors": vectors}
    )
    arr = np.asarray(result)
    assert arr.shape == (8,)
    expected = hdc.polar_bundle(*[np.asarray(v) for v in vectors])
    assert np.array_equal(arr, expected)


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


# ──────────────────────────────────────────────────────────────────────
# MCP tool-schema discoverability (v0.5.0rc9)
#
# Regression tests for the discoverability gap caught 2026-05-28: the
# MCP wrapper at ``srmech.mcp._tools`` only imported
# ``srmech.amsc.tool_schema`` and never triggered the side-effect
# imports of ``srmech.bus._tool_schema`` (which registers the bus
# tools) — so the bus discovery + decode surfaces and the introspect
# read surfaces were silently missing from the LLM-facing catalog.
#
# The fix: side-effect imports at the top of ``srmech.mcp._tools``
# plus two new ``register_tool`` calls in each of
# ``srmech.amsc.tool_schema._register_introspect_tools`` and
# ``srmech.bus._tool_schema._register_bus_tools``.
#
# These five tests lock the fix in — they all assert via
# ``srmech.mcp._tools`` import (the path Claude Code / MCP clients
# take), which is THE entry point the bug lived behind. The
# ``import srmech.bus`` line at the top of this file (added in rc6)
# does NOT cover the regression because the bug was the absence of
# that side-effect import in the MCP layer itself.
# ──────────────────────────────────────────────────────────────────────


def _names_after_mcp_import() -> set:
    """Return the set of tool names visible after importing the MCP
    tool wrapper (the path an MCP / Claude Code consumer takes).
    """
    # The import below is the SUT — importing ``srmech.mcp._tools``
    # must transitively trigger every side-effect registration that
    # the MCP-facing catalog depends on. Using ``noqa: F401`` so the
    # import isn't optimised away by a linter; same pattern as the
    # production code.
    from srmech.mcp import _tools  # noqa: F401 — side effect under test
    from srmech.amsc.tool_schema import get_tool_schema
    schema = get_tool_schema()
    return {e.name for e in schema.tools}


def test_introspect_list_in_tool_schema_via_mcp_import() -> None:
    """``srmech.introspect.list`` is registered after MCP wrapper import.

    Regression for v0.5.0rc9 discoverability fix: the read-side
    ``list`` surface complements ``srmech.introspect.publish`` and
    must be visible to MCP / Claude Code consumers.
    """
    names = _names_after_mcp_import()
    assert "srmech.introspect.list" in names, (
        "srmech.introspect.list missing from tool_schema after MCP "
        "import (v0.5.0rc9 regression — read-side introspect surface)"
    )


def test_introspect_by_pid_in_tool_schema_via_mcp_import() -> None:
    """``srmech.introspect.by_pid`` is registered after MCP wrapper import.

    Regression for v0.5.0rc9 discoverability fix.
    """
    names = _names_after_mcp_import()
    assert "srmech.introspect.by_pid" in names, (
        "srmech.introspect.by_pid missing from tool_schema after MCP "
        "import (v0.5.0rc9 regression — PID-lookup introspect surface)"
    )


def test_bus_decode_splice_in_tool_schema_via_mcp_import() -> None:
    """``srmech.bus.decode_splice`` is registered after MCP wrapper import.

    THIS IS THE PRIMARY REGRESSION TEST for the side-effect-import bug:
    ``srmech.bus.decode_splice`` HAS been registered in
    ``srmech.bus._tool_schema`` since v0.5.0rc7, but the MCP wrapper
    at ``srmech.mcp._tools`` never imported ``srmech.bus``, so the
    registration never fired and the tool was invisible to MCP /
    Claude Code consumers. The fix is the ``from .. import bus``
    side-effect import at the top of ``srmech.mcp._tools``; this
    test guards against it being removed.
    """
    names = _names_after_mcp_import()
    assert "srmech.bus.decode_splice" in names, (
        "srmech.bus.decode_splice missing from tool_schema after MCP "
        "import (v0.5.0rc9 regression — side-effect import of "
        "srmech.bus removed?)"
    )


def test_bus_list_endpoints_in_tool_schema_via_mcp_import() -> None:
    """``srmech.bus.list_endpoints`` is registered after MCP wrapper import.

    Regression for v0.5.0rc9 discoverability fix: bus endpoint
    enumeration surface must be visible to MCP / Claude Code
    consumers (paired with ``srmech.bus.by_name``).
    """
    names = _names_after_mcp_import()
    assert "srmech.bus.list_endpoints" in names, (
        "srmech.bus.list_endpoints missing from tool_schema after MCP "
        "import (v0.5.0rc9 regression — bus discovery enumerator)"
    )


def test_bus_by_name_in_tool_schema_via_mcp_import() -> None:
    """``srmech.bus.by_name`` is registered after MCP wrapper import.

    Regression for v0.5.0rc9 discoverability fix.
    """
    names = _names_after_mcp_import()
    assert "srmech.bus.by_name" in names, (
        "srmech.bus.by_name missing from tool_schema after MCP "
        "import (v0.5.0rc9 regression — bus by-name lookup)"
    )


def test_mcp_import_chain_does_not_loop() -> None:
    """``srmech.mcp._tools`` import must not trigger a circular
    import via ``srmech.bus`` -> ``srmech.amsc.tool_schema`` ->
    ``srmech.bus`` (the cycle the fix was careful to avoid)."""
    # If a cycle existed, this import would raise ImportError or
    # AttributeError on first import in a fresh interpreter. The
    # test suite as a whole exercises a non-fresh interpreter, so
    # this test is mostly a documentation guard — the assertion is
    # that the side-effect imports complete cleanly and the expected
    # tools are present.
    from srmech.mcp import _tools  # noqa: F401
    from srmech.amsc.tool_schema import get_tool_schema
    schema = get_tool_schema()
    # The full v0.5.0rc9 discoverability set is present in one shot.
    required = {
        "srmech.introspect.publish",
        "srmech.introspect.list",
        "srmech.introspect.by_pid",
        "srmech.bus.decode_splice",
        "srmech.bus.list_endpoints",
        "srmech.bus.by_name",
    }
    names = {e.name for e in schema.tools}
    missing = required - names
    assert not missing, (
        f"v0.5.0rc9 discoverability set incomplete after MCP "
        f"import; missing {sorted(missing)}"
    )
