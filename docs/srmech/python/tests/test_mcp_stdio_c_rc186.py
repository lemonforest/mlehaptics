"""rc186 — the C MCP-server CONTROL SPINE (the JSON-RPC protocol + stdio LOOP).

A bare-C host (no Python) must serve the MCP lifecycle + discovery surfaces —
initialize / notifications/initialized / tools/list / ping / shutdown — natively
over stdin/stdout, plus the MPR attestation preimage. This pins:

1. **native == pure — ``srmech_mcp_handle``.** The C JSON-RPC response is
   BYTE-IDENTICAL to ``json.dumps(MCPServer().handle(req), separators=(",", ":"))``
   for initialize / tools/list / ping / shutdown (insertion-order keys, default
   ensure_ascii). tools/list embeds ``srmech_tool_entries_to_mcp_defs`` verbatim.
   notifications/initialized → NO_RESPONSE; tools/call → DEFER; bad-json →
   -32700 with a null id; unknown method → -32601.
2. **native == pure — ``build_attestation``.** The C attestation object (same
   sha256 over the exact preimage) is byte-identical to the pinned-``retrieved_at``
   Python ``build_attestation`` JSON.
3. **the stdio LOOP.** A POSIX pipe feeds N requests + EOF; the C
   ``srmech_mcp_serve_stdio`` processes all N, writes N responses, and returns
   promptly at EOF (the teardown-terminates / no-hang guard, the rc180 discipline).
4. **runtime dispatch is value-transparent.** ``MCPServer().handle`` returns the
   same object whether it routed to the C peer or the pure path.

The native-requiring assertions ``skipif`` cleanly when the rc186 C peer is
absent (pure / numpy-absent / stale-lib host uses the Python path). numpy-free.
"""

from __future__ import annotations

import json
import os
import threading

import pytest

import srmech
from srmech.amsc import _native
from srmech.mcp import MCP_PROTOCOL_VERSION, MCPServer
from srmech.mcp._server import build_attestation
from srmech.mcp._tools import tool_entries_to_mcp_defs

_needs_native = pytest.mark.skipif(
    not _native.has_native_mcp(),
    reason="rc186 MCP control-spine C peer not loaded (pure / stale host)",
)


def _c(req: dict):
    """Route ``req`` through the C ``srmech_mcp_handle`` (returns (kind, bytes))."""
    return _native.mcp_handle_c(json.dumps(req).encode("utf-8"))


# ──────────────────────────────────────────────────────────────────────
# 1. native == pure — srmech_mcp_handle byte-parity
# ──────────────────────────────────────────────────────────────────────


@_needs_native
def test_ping_byte_identical() -> None:
    kind, resp = _c({"jsonrpc": "2.0", "id": 9, "method": "ping"})
    assert kind == _native.MCP_KIND_RESPONSE
    assert resp == b'{"jsonrpc":"2.0","id":9,"result":{}}'


@_needs_native
def test_shutdown_byte_identical() -> None:
    kind, resp = _c({"jsonrpc": "2.0", "id": 4, "method": "shutdown"})
    assert kind == _native.MCP_KIND_RESPONSE
    assert resp == b'{"jsonrpc":"2.0","id":4,"result":{}}'


@_needs_native
def test_initialize_byte_identical_to_pure() -> None:
    req = {
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": MCP_PROTOCOL_VERSION,
                   "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}},
    }
    kind, resp = _c(req)
    assert kind == _native.MCP_KIND_RESPONSE
    # The DEFAULT server (name srmech-mcp) is what the C peer models.
    expected = {
        "jsonrpc": "2.0", "id": 1,
        "result": {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "serverInfo": {"name": "srmech-mcp",
                           "version": srmech.__version__},
            "capabilities": {"tools": {}},
        },
    }
    assert resp == json.dumps(expected, separators=(",", ":")).encode("utf-8")


@_needs_native
def test_initialize_echoes_client_protocol_version() -> None:
    """The initialize handshake echoes the client's protocolVersion (per spec)."""
    kind, resp = _c({"jsonrpc": "2.0", "id": 2, "method": "initialize",
                     "params": {"protocolVersion": "2025-06-18"}})
    assert kind == _native.MCP_KIND_RESPONSE
    assert json.loads(resp)["result"]["protocolVersion"] == "2025-06-18"


@_needs_native
def test_tools_list_byte_identical_to_pure() -> None:
    kind, resp = _c({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    assert kind == _native.MCP_KIND_RESPONSE
    defs = json.dumps(list(tool_entries_to_mcp_defs()),
                      separators=(",", ":")).encode("utf-8")
    expected = b'{"jsonrpc":"2.0","id":2,"result":{"tools":' + defs + b"}}"
    assert resp == expected


@_needs_native
def test_notifications_initialized_no_response() -> None:
    kind, resp = _c({"jsonrpc": "2.0", "method": "notifications/initialized"})
    assert kind == _native.MCP_KIND_NO_RESPONSE
    assert resp is None


@_needs_native
def test_tools_call_defers() -> None:
    kind, resp = _c({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                     "params": {"name": "srmech.amsc.cascade.chiral_flip",
                                "arguments": {"seq": [1, 2, 3]}}})
    assert kind == _native.MCP_KIND_DEFER_CALL
    assert resp is None


@_needs_native
def test_unknown_method_is_method_not_found() -> None:
    kind, resp = _c({"jsonrpc": "2.0", "id": 8, "method": "wat"})
    assert kind == _native.MCP_KIND_RESPONSE
    obj = json.loads(resp)
    assert obj["error"]["code"] == -32601
    assert obj["id"] == 8
    # matches Python f"unknown method {method!r}"
    assert obj["error"]["message"] == "unknown method 'wat'"


@_needs_native
def test_unknown_notification_no_response() -> None:
    kind, resp = _c({"jsonrpc": "2.0", "method": "notifications/anything"})
    assert kind == _native.MCP_KIND_NO_RESPONSE
    assert resp is None


@_needs_native
def test_bad_json_is_parse_error_null_id() -> None:
    kind, resp = _native.mcp_handle_c(b"this is not json {")
    assert kind == _native.MCP_KIND_RESPONSE
    obj = json.loads(resp)
    assert obj["error"]["code"] == -32700
    assert obj["id"] is None


@_needs_native
def test_missing_method_is_invalid_request() -> None:
    kind, resp = _c({"jsonrpc": "2.0", "id": 5})
    assert kind == _native.MCP_KIND_RESPONSE
    obj = json.loads(resp)
    assert obj["error"]["code"] == -32600
    assert obj["id"] == 5


# ──────────────────────────────────────────────────────────────────────
# 2. native == pure — build_attestation
# ──────────────────────────────────────────────────────────────────────


@_needs_native
def test_build_attestation_c_byte_identical_to_python() -> None:
    ra = "2026-07-08T12:34:56Z"
    tn = "srmech.amsc.cascade.chiral_flip"
    txt = "[3, 2, 1]"
    py = build_attestation(tool_name=tn, result_text=txt, retrieved_at=ra)
    py_bytes = json.dumps(py, separators=(",", ":")).encode("utf-8")
    c = _native.mcp_build_attestation_c(tn, txt, ra)
    assert c is not None
    assert c == py_bytes
    # the load-bearing digest matches (same sha256 over the exact preimage)
    assert json.loads(c)["response_sha256"] == py["response_sha256"]
    assert len(json.loads(c)["response_sha256"]) == 64


@_needs_native
def test_build_attestation_c_digest_changes_with_content() -> None:
    ra = "2026-07-08T00:00:00Z"
    a = json.loads(_native.mcp_build_attestation_c("foo", "bar", ra))
    b = json.loads(_native.mcp_build_attestation_c("foo", "other", ra))
    assert a["response_sha256"] != b["response_sha256"]


# ──────────────────────────────────────────────────────────────────────
# 3. the stdio LOOP — teardown-terminates guard (POSIX)
# ──────────────────────────────────────────────────────────────────────


@_needs_native
@pytest.mark.skipif(os.name != "posix",
                    reason="the stdio-loop fd-redirect harness is POSIX-only "
                           "(Windows uses GetStdHandle, not the CRT fd)")
def test_serve_stdio_processes_stream_then_terminates_on_eof() -> None:
    """Pipe N requests + EOF into the C ``srmech_mcp_serve_stdio`` loop (via a
    POSIX fd redirect); assert it processes ALL N, writes N responses, and
    returns promptly at EOF (never hangs — the rc180 teardown-terminates
    discipline). tools/list is EXCLUDED (its ~440 KB response would exceed the
    64 KB pipe buffer); it is byte-parity-tested via srmech_mcp_handle above."""
    import ctypes

    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": MCP_PROTOCOL_VERSION}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},  # no response
        {"jsonrpc": "2.0", "id": 2, "method": "ping"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
         "params": {"name": "x", "arguments": {}}},                 # honest error
        {"jsonrpc": "2.0", "id": 4, "method": "wat"},               # -32601
        {"jsonrpc": "2.0", "id": 5, "method": "shutdown"},
    ]
    payload = ("".join(json.dumps(r) + "\n" for r in requests)).encode("utf-8")

    r_in, w_in = os.pipe()
    r_out, w_out = os.pipe()
    os.write(w_in, payload)
    os.close(w_in)   # EOF pending once the loop drains the data

    saved_in, saved_out = os.dup(0), os.dup(1)
    line_buf = (ctypes.c_char * (1 << 16))()
    ws = (ctypes.c_char * (1 << 16))()
    resp_buf = (ctypes.c_char * (1 << 18))()
    rc_holder = {}

    def _run():
        rc_holder["rc"] = _native.LIB.srmech_mcp_serve_stdio(
            ctypes.cast(line_buf, ctypes.c_void_p), 1 << 16,
            ctypes.cast(ws, ctypes.c_void_p), 1 << 16,
            ctypes.cast(resp_buf, ctypes.c_void_p), 1 << 18)

    try:
        os.dup2(r_in, 0)
        os.dup2(w_out, 1)
        os.close(r_in)
        os.close(w_out)
        t = threading.Thread(target=_run)
        t.start()
        t.join(timeout=15.0)
        assert not t.is_alive(), "serve_stdio did not terminate on EOF (hang)"
    finally:
        os.dup2(saved_in, 0)
        os.dup2(saved_out, 1)
        os.close(saved_in)
        os.close(saved_out)

    assert rc_holder.get("rc") == _native.SRMECH_OK
    out = b""
    while True:
        chunk = os.read(r_out, 65536)
        if not chunk:
            break
        out += chunk
    os.close(r_out)

    lines = [ln for ln in out.decode("utf-8").split("\n") if ln]
    # 5 responses (the notification produced none).
    assert len(lines) == 5
    ids = [json.loads(ln).get("id") for ln in lines]
    assert ids == [1, 2, 3, 4, 5]
    # per-method verdicts
    objs = {json.loads(ln)["id"]: json.loads(ln) for ln in lines}
    assert objs[1]["result"]["serverInfo"]["name"] == "srmech-mcp"
    assert objs[2]["result"] == {}
    assert objs[3]["error"]["code"] == -32000      # tools/call honest bare-C error
    assert objs[4]["error"]["code"] == -32601      # unknown method
    assert objs[5]["result"] == {}                  # shutdown


# ──────────────────────────────────────────────────────────────────────
# 4. runtime dispatch is value-transparent (always runs)
# ──────────────────────────────────────────────────────────────────────


def test_handle_ping_value_equal() -> None:
    """MCPServer().handle (native or pure) returns the same object."""
    srv = MCPServer()
    assert srv.handle({"jsonrpc": "2.0", "id": 1, "method": "ping"}) == {
        "jsonrpc": "2.0", "id": 1, "result": {}}


def test_handle_initialize_value_equal() -> None:
    srv = MCPServer()
    resp = srv.handle({"jsonrpc": "2.0", "id": 7, "method": "initialize",
                       "params": {"protocolVersion": MCP_PROTOCOL_VERSION}})
    assert resp["result"]["serverInfo"]["name"] == "srmech-mcp"
    assert resp["result"]["serverInfo"]["version"] == srmech.__version__
    assert resp["result"]["protocolVersion"] == MCP_PROTOCOL_VERSION


def test_handle_notification_returns_none_and_sets_flag() -> None:
    srv = MCPServer()
    assert srv.handle({"jsonrpc": "2.0",
                       "method": "notifications/initialized"}) is None
    assert srv._initialized is True


def test_handle_tools_call_still_attests() -> None:
    """tools/call is EXCLUDED from the C fast-path (defers to pure invoke_tool),
    so it still returns the full content + attestation envelope."""
    srv = MCPServer()
    resp = srv.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                       "params": {"name": "srmech.amsc.cascade.chiral_flip",
                                  "arguments": {"seq": [1, 2, 3]}}})
    assert resp["result"]["isError"] is False
    assert json.loads(resp["result"]["content"][0]["text"]) == [3, 2, 1]
    assert len(resp["result"]["attestation"]["response_sha256"]) == 64


def test_custom_name_server_takes_pure_path() -> None:
    """A non-default server name is NOT C-eligible; initialize carries the
    custom serverInfo.name from the pure path."""
    srv = MCPServer(name="custom-srv")
    resp = srv.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                       "params": {"protocolVersion": MCP_PROTOCOL_VERSION}})
    assert resp["result"]["serverInfo"]["name"] == "custom-srv"


# ──────────────────────────────────────────────────────────────────────
# 5. the two-pass buffer contract
# ──────────────────────────────────────────────────────────────────────


@_needs_native
def test_handle_two_pass_size_query_and_overflow() -> None:
    import ctypes

    req = b'{"jsonrpc":"2.0","id":1,"method":"ping"}'
    ws = (ctypes.c_char * 4096)()
    ws_p = ctypes.cast(ws, ctypes.c_void_p)
    need = ctypes.c_size_t(0)
    kind = ctypes.c_int(-1)
    rc = _native.LIB.srmech_mcp_handle(
        req, len(req), ws_p, 4096, None, ctypes.c_size_t(0),
        ctypes.byref(need), ctypes.byref(kind), 1)
    assert rc == _native.SRMECH_OK
    assert kind.value == _native.MCP_KIND_RESPONSE
    assert need.value > 0

    raw = (ctypes.c_char * need.value)()
    got = ctypes.c_size_t(0)
    k2 = ctypes.c_int(-1)
    rc = _native.LIB.srmech_mcp_handle(
        req, len(req), ws_p, 4096, ctypes.cast(raw, ctypes.c_void_p),
        ctypes.c_size_t(need.value), ctypes.byref(got), ctypes.byref(k2), 1)
    assert rc == _native.SRMECH_OK
    assert got.value == need.value

    # too-small buffer overflows cleanly (never writes past the buffer)
    small = (ctypes.c_char * 4)()
    g2 = ctypes.c_size_t(0)
    k3 = ctypes.c_int(-1)
    rc = _native.LIB.srmech_mcp_handle(
        req, len(req), ws_p, 4096, ctypes.cast(small, ctypes.c_void_p),
        ctypes.c_size_t(4), ctypes.byref(g2), ctypes.byref(k3), 1)
    assert rc == _native.SRMECH_ERR_OVERFLOW

    # NULL out_len / out_kind -> NULL_ARG
    rc = _native.LIB.srmech_mcp_handle(
        req, len(req), ws_p, 4096, None, ctypes.c_size_t(0),
        None, ctypes.byref(kind), 1)
    assert rc == _native.SRMECH_ERR_NULL_ARG
