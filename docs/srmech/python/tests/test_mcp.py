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


def test_invoke_tool_sha256_bytes_with_base64_coercion() -> None:
    """bytes parameters arrive as base64 strings (MCP rides JSON, which
    has no bytes type; rc14 standardises bytes on base64 — binary-safe,
    unambiguous); ``invoke_tool`` decodes them back to raw bytes."""
    import base64

    # "abc" base64 -> "YWJj"
    result = invoke_tool(
        "srmech.amsc.format.sha256_bytes",
        {"data": base64.b64encode(b"abc").decode("ascii")},
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
    """JSON-text rendering of awkward Python objects (rc14: bytes ride as
    base64, tuples become lists)."""
    import base64

    out = serialise_result({"b": b"\x00\xff", "tup": (1, 2)})
    parsed = json.loads(out)
    assert parsed["b"] == base64.b64encode(b"\x00\xff").decode("ascii")
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


# ──────────────────────────────────────────────────────────────────────
# Self-recognition root (v0.5.0rc11)
#
# ``warmup_all()`` is THE single registration entry-point — it imports
# every submodule that registers ToolEntries so the registry is fully
# populated no matter how srmech was entered, permanently closing the
# orphan-registration bug class (the rc9 bus miss). ``describe()`` is
# the self-recognition ROOT: the package's at-a-glance map of its own
# shape, also registered as a tool so MCP / Anthropic consumers can ask
# "what is srmech / what can it do?".
# ──────────────────────────────────────────────────────────────────────


def test_warmup_all_populates_registry() -> None:
    """``warmup_all()`` imports every registration-bearing submodule so
    bus + introspect tools are present in the tool schema regardless of
    entry-path. Closes the orphan-registration bug class (rc9 bus miss).
    """
    from srmech.amsc.tool_schema import get_tool_schema, warmup_all

    warmup_all()  # idempotent
    names = {e.name for e in get_tool_schema().tools}
    # bus tools (the rc9 orphan) + introspect tools must all be present.
    required = {
        "srmech.bus.decode_splice",
        "srmech.bus.list_endpoints",
        "srmech.bus.by_name",
        "srmech.introspect.publish",
        "srmech.introspect.list",
        "srmech.introspect.by_pid",
        "srmech.introspect.describe",
    }
    missing = required - names
    assert not missing, (
        f"warmup_all() left the registry incomplete; missing "
        f"{sorted(missing)}"
    )


def test_describe_shape() -> None:
    """``srmech.introspect.describe()`` returns the self-shape dict with
    all expected keys; the counts are internally consistent and agree
    with the live tool schema."""
    from srmech.amsc.tool_schema import get_tool_schema
    from srmech.introspect import describe

    d = describe()
    # Top-level keys.
    assert set(d.keys()) == {
        "srmech_version",
        "tool_schema_version",
        "native",
        "tools",
        "categories",
    }
    # Version agrees with the package attribute (no hardcoded literal).
    assert d["srmech_version"] == srmech.__version__
    assert isinstance(d["tool_schema_version"], str) and d["tool_schema_version"]

    # native block shape.
    native = d["native"]
    assert set(native.keys()) == {
        "has_native",
        "abi_version",
        "native_version",
    }
    assert isinstance(native["has_native"], bool)

    # tools.total agrees with the live schema length.
    schema = get_tool_schema()
    assert d["tools"]["total"] == len(schema.tools)

    # by_category sums to total.
    by_category = d["tools"]["by_category"]
    assert isinstance(by_category, dict)
    assert sum(by_category.values()) == d["tools"]["total"]

    # categories are sorted + non-empty + match the by_category keys.
    cats = d["categories"]
    assert cats, "describe() returned no categories"
    assert cats == sorted(cats), "categories must be sorted"
    assert set(cats) == set(by_category.keys())


def test_describe_registered_as_tool() -> None:
    """``srmech.introspect.describe`` appears in the catalog after warmup
    (so MCP / Anthropic consumers can call the self-recognition root),
    with no parameters (keeps the property-key ratchet trivially happy).
    """
    from srmech.amsc.tool_schema import get_tool_schema, warmup_all

    warmup_all()
    entry = get_tool_schema().lookup("srmech.introspect.describe")
    assert entry is not None, (
        "srmech.introspect.describe not registered as a ToolEntry"
    )
    assert entry.owner == "srmech"
    assert entry.category == "introspect"
    # No params — the self-recognition root takes no arguments.
    assert entry.parameters == ()
    # And it converts to a clean MCP def (guards both adapters).
    mcp_def = tool_entry_to_mcp_def(entry)
    assert mcp_def["inputSchema"]["properties"] == {}
    assert mcp_def["inputSchema"]["required"] == []


# ──────────────────────────────────────────────────────────────────────
# DSL surface (v0.5.0rc12)
#
# The rc8 cascade DSL is exposed declaratively as two ToolEntries so an
# LLM composes + runs a cascade in one call. These two tests keep the
# dsl entries in the MCP-import discoverability manifest (the path a
# Claude Code / MCP client takes); full DSL-tool coverage lives in
# test_dsl_tools.py.
# ──────────────────────────────────────────────────────────────────────


def test_dsl_tools_in_tool_schema_via_mcp_import() -> None:
    """``srmech.dsl.run_toml_chain`` + ``srmech.dsl.list_catalog_ops``
    are registered after the MCP wrapper import (the path an MCP /
    Claude Code consumer takes) — the rc12 DSL surface voxel."""
    names = _names_after_mcp_import()
    for tool_name in (
        "srmech.dsl.run_toml_chain",
        "srmech.dsl.list_catalog_ops",
    ):
        assert tool_name in names, (
            f"{tool_name} missing from tool_schema after MCP import "
            f"(v0.5.0rc12 DSL surface voxel)"
        )


def test_dsl_run_toml_chain_one_shot_via_mcp_invoke() -> None:
    """``srmech.dsl.run_toml_chain`` is one-shot callable through the
    MCP ``invoke_tool`` path with a real TOML spec — composes + runs a
    cascade in a single call (rc12)."""
    spec = (
        "[chain]\n"
        'name = "rc12-mcp"\n'
        "\n"
        "[[stage]]\n"
        'op = "chiral_flip"\n'
    )
    result = invoke_tool(
        "srmech.dsl.run_toml_chain",
        {"spec": spec, "input_value": [10, 20, 30]},
    )
    assert result == [30, 20, 10]


# ──────────────────────────────────────────────────────────────────────
# MCP surface-correctness (v0.5.0rc13)
#
# Two real bugs surfaced by upstream MCP usage, plus the would-have-caught
# -it ratchet. Both bugs affect BOTH the MCP path and the Anthropic adapter
# (shared ``srmech.mcp._tools.invoke_tool``).
#
# BUG A — ``hdc.klein4_random`` / ``hdc.polar_random`` were seedable only
# via ``rng: numpy.random.Generator``, which cannot cross JSON-RPC nor be
# expressed in an Anthropic tool schema — so MCP / Anthropic callers could
# not get a DETERMINISTIC vector (breaking srmech's bit-exact / attestation
# discipline). Fix: an integer ``seed`` param; the ToolEntry advertises
# ``seed`` and DROPS the un-serialisable Generator.
#
# BUG B — ``srmech.amsc.naming.lookup``'s ToolEntry declared a param
# (``entries``) the shipped ``lookup(key, pairs)`` does not accept, so the
# tool was uncallable (``TypeError: unexpected keyword argument 'entries'``).
# Fix: align the SCHEMA to the shipped signature (``pairs``).
# ──────────────────────────────────────────────────────────────────────


def test_klein4_random_seed_reproducible() -> None:
    """``hdc.klein4_random(seed=42)`` is DETERMINISTIC — twice directly,
    and twice through ``invoke_tool`` (the MCP / Anthropic shared path) —
    so a JSON-RPC / Anthropic caller can reproduce a Klein-4 vector
    (bit-exact / attestation discipline). This is the BUG A acceptance
    test."""
    from srmech.amsc import hdc

    # Direct: identical vectors for the same seed.
    a = hdc.klein4_random(8, seed=42)
    b = hdc.klein4_random(8, seed=42)
    assert np.array_equal(a, b)
    assert set(np.unique(a).tolist()) <= {0, 1, 2, 3}

    # Through invoke_tool twice (the wire path): also identical.
    r1 = invoke_tool("srmech.amsc.hdc.klein4_random", {"D": 8, "seed": 42})
    r2 = invoke_tool("srmech.amsc.hdc.klein4_random", {"D": 8, "seed": 42})
    assert np.array_equal(np.asarray(r1), np.asarray(r2))
    # And invoke_tool agrees bit-exactly with the direct seeded call.
    assert np.array_equal(np.asarray(r1), a)

    # A different seed gives a different vector (the seed is load-bearing).
    c = hdc.klein4_random(8, seed=43)
    assert not np.array_equal(a, c)


def test_polar_random_seed_reproducible() -> None:
    """Companion to klein4: ``hdc.polar_random(seed=...)`` is deterministic
    directly and through ``invoke_tool`` (the second ``*_random`` op fixed
    for BUG A)."""
    from srmech.amsc import hdc

    a = hdc.polar_random(8, seed=7)
    b = hdc.polar_random(8, seed=7)
    assert np.array_equal(a, b)
    assert set(np.unique(a).tolist()) <= {-1, 0, 1}

    r1 = invoke_tool("srmech.amsc.hdc.polar_random", {"D": 8, "seed": 7})
    r2 = invoke_tool("srmech.amsc.hdc.polar_random", {"D": 8, "seed": 7})
    assert np.array_equal(np.asarray(r1), np.asarray(r2))
    assert np.array_equal(np.asarray(r1), a)


def test_random_ops_rng_takes_precedence_over_seed() -> None:
    """When BOTH ``rng`` and ``seed`` are given, the explicit ``rng`` wins
    (documented precedence), and the legacy ``rng=`` path stays back-compat
    for in-process Python callers."""
    from srmech.amsc import hdc

    # rng= path still works (back-compat).
    assert hdc.klein4_random(8, rng=np.random.default_rng(0)).shape == (8,)
    assert hdc.polar_random(8, rng=np.random.default_rng(0)).shape == (8,)

    # rng wins over seed: the rng-built vector differs from the seed-only one.
    rng_out = hdc.klein4_random(8, rng=np.random.default_rng(999), seed=1)
    seed_out = hdc.klein4_random(8, seed=1)
    assert not np.array_equal(rng_out, seed_out)


def test_random_ops_schema_drops_unserialisable_rng() -> None:
    """The ``*_random`` ToolEntries advertise the JSON-friendly ``seed``
    and NO un-serialisable ``rng`` Generator (a Generator has no valid
    JSON-Schema type and must never reach the MCP / Anthropic schema)."""
    schema = get_tool_schema()
    for name in ("srmech.amsc.hdc.klein4_random",
                 "srmech.amsc.hdc.polar_random"):
        entry = schema.lookup(name)
        assert entry is not None, f"{name} not registered"
        param_names = {p.name for p in entry.parameters}
        assert "seed" in param_names, f"{name} must advertise `seed`"
        assert "rng" not in param_names, (
            f"{name} must NOT advertise the un-serialisable `rng` Generator"
        )


def test_naming_lookup_callable_via_invoke_tool() -> None:
    """``srmech.amsc.naming.lookup`` is callable through ``invoke_tool``
    and returns a real result — NOT a ``TypeError`` from a phantom param
    name. This is the BUG B acceptance test (the schema declared a param
    the shipped ``lookup(key, pairs)`` does not accept)."""
    pairs = [(b"a", b"x"), (b"b", b"y"), (b"c", b"z")]  # pre-sorted
    result = invoke_tool(
        "srmech.amsc.naming.lookup", {"key": b"b", "pairs": pairs}
    )
    assert result == b"y"
    # A miss returns None (still a real result, no TypeError).
    miss = invoke_tool(
        "srmech.amsc.naming.lookup", {"key": b"zzz", "pairs": pairs}
    )
    assert miss is None


def test_template_render_callable_via_invoke_tool() -> None:
    """``srmech.amsc.template.render`` is callable through ``invoke_tool``
    with the real ``mapping`` param — the second schema/signature drift the
    rc13 ratchet surfaced (the schema declared ``substitutions``)."""
    result = invoke_tool(
        "srmech.amsc.template.render",
        {"template_bytes": b"hi {n}", "mapping": {b"n": b"there"}},
    )
    assert result == b"hi there"


def test_schema_signature_alignment_no_drift() -> None:
    """THE RATCHET (v0.5.0rc13): for EVERY ToolEntry, the declared
    parameters must be BINDABLE to the resolved callable's signature —
    i.e. no schema/signature drift. A drift means the tool is uncallable
    via MCP / Anthropic (both route through ``invoke_tool``), exactly the
    BUG B failure mode.

    Tolerances:
      * a callable with ``**kwargs`` (VAR_KEYWORD) accepts any name;
      * the rc10 varargs convention exposes a ``*args`` slot under a clean
        name (e.g. ``vectors``), so a leading ``*`` on a declared param
        name is stripped before the membership check.

    This test would have caught both naming.lookup (``entries``) and
    template.render (``substitutions``). It guards all ~158 tools at once.
    """
    from srmech.mcp._tools import _resolve_dotted_callable

    schema = get_tool_schema()
    assert len(schema.tools) > 50, "tool registry unexpectedly small"

    drift: List[Tuple[str, str, List[str]]] = []
    for entry in schema.tools:
        fn = _resolve_dotted_callable(entry.name)
        sig = __import__("inspect").signature(fn)
        params = sig.parameters.values()
        Parameter = __import__("inspect").Parameter
        has_var_kw = any(
            p.kind is Parameter.VAR_KEYWORD for p in params
        )
        accepted = {
            p.name
            for p in params
            if p.kind
            in (
                Parameter.POSITIONAL_OR_KEYWORD,
                Parameter.KEYWORD_ONLY,
                Parameter.VAR_POSITIONAL,
            )
        }
        for p in entry.parameters:
            nm = p.name.lstrip("*")  # tolerate the rc10 varargs convention
            if not has_var_kw and nm not in accepted:
                drift.append((entry.name, p.name, sorted(accepted)))

    assert not drift, (
        "schema/signature drift — these declared ToolEntry params are not "
        "bindable to the resolved callable (the tool is uncallable via MCP "
        f"/ Anthropic): {drift}"
    )


# ──────────────────────────────────────────────────────────────────────
# Full JSON<->native coercion (v0.5.0rc14)
#
# A live probe of the rc13 catalog proved 65/158 tools were advertised to
# MCP / Anthropic but UNCALLABLE because their params are bytes /
# np.ndarray / complex — types JSON-RPC cannot express. rc14 adds full
# BIDIRECTIONAL coercion (params in + results out) so every tool is
# MCP-callable. The type-coercibility ratchet below complements the rc13
# name-drift ratchet: rc13 guarantees a param NAME binds; rc14 guarantees
# a param TYPE is JSON-coercible.
# ──────────────────────────────────────────────────────────────────────


def test_all_param_types_json_coercible() -> None:
    """THE TYPE-COERCIBILITY RATCHET (v0.5.0rc14): every ToolEntry param's
    declared type MUST have an explicit handler in the coercion dispatch
    (``srmech.mcp._coercion``). This is the would-have-caught-it ratchet
    for the 65/158 uncallable-tool finding: no future tool can advertise a
    non-JSON-coercible param type unnoticed — a missing handler fails here.

    JSON-native and opaque-handle types are listed as explicit
    pass-throughs in the dispatch (not defaulted), so this ratchet proves
    the dispatch is EXHAUSTIVE over the advertised surface, not merely
    that the awkward types are covered.
    """
    from srmech.mcp._coercion import has_coercer

    schema = get_tool_schema()
    assert len(schema.tools) > 50, "tool registry unexpectedly small"
    unhandled: List[Tuple[str, str, str]] = []
    for entry in schema.tools:
        for p in entry.parameters:
            if not has_coercer(p.type):
                unhandled.append((entry.name, p.name, p.type))
    assert not unhandled, (
        "these declared ToolEntry param types have NO coercion handler "
        "(the tool may be uncallable via MCP / Anthropic — add a handler "
        f"in srmech.mcp._coercion._PARAM_COERCERS): {unhandled}"
    )


def test_coercion_roundtrips_scalar_leaf_types() -> None:
    """``coerce_param(serialise_native(x)) == x`` for representative
    bytes / complex / real-ndarray values (the documented round-trip
    guarantee). Complex arrays use the explicit ``complex_pairs_to_ndarray``
    builder (the generic ndarray path stays real per its dtype caveat)."""
    from srmech.mcp._coercion import (
        coerce_param,
        complex_pairs_to_ndarray,
        serialise_native,
    )

    # bytes <-> base64 (incl. non-UTF-8 / NUL bytes).
    raw = b"\x00\xff\x10binary\x7f"
    assert coerce_param(serialise_native(raw), "bytes") == raw

    # complex <-> [re, im].
    z = complex(3.0, -2.5)
    assert coerce_param(serialise_native(z), "complex") == z
    # A bare JSON number decodes to complex(n, 0).
    assert coerce_param(5, "complex") == complex(5, 0)

    # real ndarray <-> nested list (EXACT — values + shape).
    arr = np.array([[1.0, 2.0], [3.0, 4.0]])
    back = coerce_param(serialise_native(arr), "np.ndarray")
    assert np.array_equal(back, arr)

    # complex ndarray: serialised as [re, im] leaves, rebuilt via the
    # explicit complex builder (documented dtype caveat — the generic
    # np.ndarray inbound path does NOT auto-promote).
    carr = np.array([1 + 2j, 3 - 4j])
    assert np.array_equal(
        complex_pairs_to_ndarray(serialise_native(carr)), carr
    )


def test_serialise_native_emits_json_serialisable() -> None:
    """``serialise_native`` output is always JSON-serialisable for the
    awkward Python types ops return (bytes / complex / ndarray (real +
    complex) / numpy scalars / nested tuples / dict with bytes key)."""
    from srmech.mcp._coercion import serialise_native

    samples: List[Any] = [
        b"\x00\xff",
        complex(1, 2),
        np.array([1.0, 2.0, 3.0]),
        np.array([[1 + 1j, 2 - 2j]]),
        np.int64(7),
        np.float64(1.5),
        np.uint8(255),
        (1, 2, b"ab"),
        {b"key": np.array([1, 2])},
        {"nested": [np.int64(3), complex(0, 1)]},
    ]
    for s in samples:
        # Must not raise — the load-bearing guarantee for the tool_result.
        json.dumps(serialise_native(s))


def test_invalid_base64_bytes_raises_clear_error() -> None:
    """A malformed base64 value for a ``bytes`` param raises a clear
    ValueError naming the param (per the rc14 contract)."""
    from srmech.mcp._coercion import coerce_param

    with pytest.raises(ValueError, match="base64"):
        # '!' is not a valid base64 alphabet char (validate=True).
        coerce_param("not!valid!base64!", "bytes", param="data")


# ──────────────────────────────────────────────────────────────────────
# Targeted round-trip + live-path tests through invoke_tool (the shared
# MCP + Anthropic entry). Each asserts the result is JSON-serialisable.
# ──────────────────────────────────────────────────────────────────────


def _b64(data: bytes) -> str:
    import base64
    return base64.b64encode(data).decode("ascii")


def _assert_json_serialisable(raw: Any) -> None:
    """A tool result must JSON-serialise through ``serialise_result`` (the
    server slot is textual JSON)."""
    text = serialise_result(raw)
    json.loads(text)  # round-trips through json; raises on failure


def test_invoke_naming_lookup_base64_params() -> None:
    """``naming.lookup`` with base64 key + base64 (key, value) pairs
    returns the matching value — no TypeError — and serialises to JSON."""
    raw = invoke_tool(
        "srmech.amsc.naming.lookup",
        {
            "key": _b64(b"A"),
            "pairs": [[_b64(b"A"), _b64(b"content-addressing")]],
        },
    )
    assert raw == b"content-addressing"
    _assert_json_serialisable(raw)


def test_invoke_template_render_base64_mapping() -> None:
    """``template.render`` with base64 template + base64->base64 mapping
    renders the bytes; the result base64-encodes in JSON."""
    import base64

    raw = invoke_tool(
        "srmech.amsc.template.render",
        {"template_bytes": _b64(b"Class {x}"), "mapping": {_b64(b"x"): _b64(b"A")}},
    )
    assert raw == b"Class A"
    text = serialise_result(raw)
    assert json.loads(text) == base64.b64encode(b"Class A").decode("ascii")


def test_invoke_hdc_bind_base64_roundtrips() -> None:
    """``hdc.bind`` of two base64 byte-vectors returns bound bytes; the
    base64 result round-trips back to the same bytes."""
    import base64

    from srmech.mcp._coercion import coerce_param

    a = bytes([1, 2, 3, 4])
    b = bytes([5, 6, 7, 8])
    raw = invoke_tool(
        "srmech.amsc.hdc.bind", {"a": _b64(a), "b": _b64(b)}
    )
    assert raw == bytes(x ^ y for x, y in zip(a, b))
    text = serialise_result(raw)
    encoded = json.loads(text)
    assert encoded == base64.b64encode(raw).decode("ascii")
    # The serialised base64 coerces straight back to the bound bytes.
    assert coerce_param(encoded, "bytes") == raw


def test_invoke_jacobi_eigvals_nested_list_matrix() -> None:
    """``laplacian.jacobi_eigvals`` with a nested-list real symmetric
    matrix returns an eigenvalue list (JSON array)."""
    matrix = [
        [2.0, -1.0, 0.0],
        [-1.0, 2.0, -1.0],
        [0.0, -1.0, 2.0],
    ]
    raw = invoke_tool(
        "srmech.amsc.laplacian.jacobi_eigvals", {"matrix": matrix}
    )
    arr = np.asarray(raw)
    assert arr.shape == (3,)
    # Known spectrum of the path-graph-3 Laplacian-like tridiagonal matrix.
    expected = np.sort(np.linalg.eigvalsh(np.asarray(matrix)))
    assert np.allclose(np.sort(arr), expected)
    text = serialise_result(raw)
    assert isinstance(json.loads(text), list)


def test_invoke_higgs_potential_complex_phi() -> None:
    """``qm.sm.higgs_potential`` with phi=[re, im] returns a real float;
    the result is JSON-serialisable."""
    raw = invoke_tool(
        "srmech.qm.sm.higgs_potential",
        {"phi": [1.0, 0.5], "mu_squared": 2.0, "lam": 1.0},
    )
    # V = -mu^2 |phi|^2 + lam |phi|^4; |phi|^2 = 1.25.
    assert isinstance(raw, float)
    assert abs(raw - (-2.0 * 1.25 + 1.0 * 1.25 ** 2)) < 1e-12
    _assert_json_serialisable(raw)


def test_invoke_dispatch_match_base64_rules() -> None:
    """``dispatch.match`` with base64 input + [base64, int] rules returns
    a serialisable result (the (matched, tag) tuple -> JSON list)."""
    raw = invoke_tool(
        "srmech.amsc.dispatch.match",
        {"input_bytes": _b64(b"hello"), "rules": [[_b64(b"he"), 1], [_b64(b"xyz"), 2]]},
    )
    _assert_json_serialisable(raw)


def test_invoke_klein4_random_seed_reproducible_rc14_path() -> None:
    """rc13 ``klein4_random(seed)`` reproducibility still holds through the
    rc14 coercion path (ndarray result -> JSON list, bit-identical)."""
    r1 = serialise_result(
        invoke_tool("srmech.amsc.hdc.klein4_random", {"D": 8, "seed": 42})
    )
    r2 = serialise_result(
        invoke_tool("srmech.amsc.hdc.klein4_random", {"D": 8, "seed": 42})
    )
    assert r1 == r2
    assert set(json.loads(r1)) <= {0, 1, 2, 3}


# ──────────────────────────────────────────────────────────────────────
# Schema rendering hints (v0.5.0rc14, STEP 3) — so an LLM learns HOW to
# encode bytes / ndarray / complex / containers.
# ──────────────────────────────────────────────────────────────────────


def test_schema_renders_encoding_hints() -> None:
    """The MCP/Anthropic schema property for a non-JSON native type
    carries its JSON-encoding hint in the description, and the rc13
    property-key grammar + rc10 name discipline stay intact."""
    schema = get_tool_schema()

    def _prop(tool_name: str, param: str) -> Dict[str, Any]:
        entry = schema.lookup(tool_name)
        assert entry is not None, f"{tool_name} not registered"
        return tool_entry_to_mcp_def(entry)["inputSchema"]["properties"][param]

    # bytes -> string + base64 hint.
    p = _prop("srmech.amsc.format.sha256_bytes", "data")
    assert p["type"] == "string"
    assert "base64" in p["description"]

    # np.ndarray -> array + nested-array hint.
    p = _prop("srmech.amsc.laplacian.jacobi_eigvals", "matrix")
    assert p["type"] == "array"
    assert "nested JSON array" in p["description"]

    # complex -> array + [real, imaginary] hint.
    p = _prop("srmech.qm.sm.higgs_potential", "phi")
    assert p["type"] == "array"
    assert "real, imaginary" in p["description"]

    # Mapping[bytes, bytes] -> object + base64 key/value hint.
    p = _prop("srmech.amsc.template.render", "mapping")
    assert p["type"] == "object"
    assert "base64" in p["description"]

    # list[tuple[bytes, int]] -> array + [base64, integer] hint.
    p = _prop("srmech.amsc.dispatch.match", "rules")
    assert p["type"] == "array"
    assert "base64" in p["description"]


def test_encoding_hints_preserve_property_key_grammar() -> None:
    """Adding encoding hints must not perturb the rc13 property-key
    grammar ratchet — every property key still matches Anthropic's
    ``^[a-zA-Z0-9_.-]{1,64}$`` (the hint lives in the VALUE's description,
    never the KEY)."""
    schema = get_tool_schema()
    for entry in schema.tools:
        mcp_def = tool_entry_to_mcp_def(entry)
        for key in mcp_def["inputSchema"]["properties"]:
            assert _ANTHROPIC_PROPERTY_KEY_RE.match(key), (
                f"{entry.name}: property key {key!r} violates grammar"
            )
