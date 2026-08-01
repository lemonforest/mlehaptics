"""rc194 — the C MCP HTTP+SSE transport (the HOST-GLUE cross-terminal server).

A bare-C host (no Python) must serve MCP over HTTP+Server-Sent-Events on a
localhost TCP port — the same GET /sse (endpoint event → message events) +
POST /message?session= (202 + the response over the SSE stream) + GET /healthz
protocol as the pure ``srmech.mcp._sse.serve_http_sse``. This pins:

1. **the transport round-trip.** ``srmech_mcp_sse_serve`` binds a port and runs
   a background accept thread over the rc194 TCP PAL; a GET /sse yields an
   ``endpoint`` event carrying ``/message?session=<id>``; a POST of a JSON-RPC
   ``initialize`` returns 202 and the response rides the SSE stream as a
   ``message`` event.
2. **native == pure.** The JSON-RPC response pushed over SSE is byte-identical
   to ``json.dumps(MCPServer().handle(req), separators=(",", ":"))`` (the C
   server composes the rc186 ``srmech_mcp_handle``, defer_calls==0 — the default
   ``srmech-mcp`` server).
3. **GET /healthz** → 200 ``{"status": "ok"}``; an unknown path → 404.
4. **NO-HANG teardown** (the rc180 socket-teardown discipline): ``srmech_mcp_
   sse_stop`` closes the poll-gated listener + joins both threads promptly.

POSIX-FIRST: the rc194 TCP PAL is POSIX today (Windows Winsock is a tracked
follow-up), so the SSE-server-driving tests are ``@posix_only`` — on Windows the
C server declines (``srmech_plat_has_tcp()==0``) and a Python host runs the pure
http.server; the driving tests skip (no CI hang). numpy-free.
"""

from __future__ import annotations

import json
import os
import threading
import time
from http.client import HTTPConnection
from typing import Iterator, List, Tuple

import pytest

import srmech
from srmech import _native
from srmech.mcp import MCP_PROTOCOL_VERSION, MCPServer

_needs_native = pytest.mark.skipif(
    not _native.has_native_mcp_sse(),
    reason="rc194 MCP HTTP+SSE C peer not loaded (pure / stale host)",
)
_posix_only = pytest.mark.skipif(
    os.name != "posix",
    reason="rc194 TCP PAL is POSIX-first; Windows Winsock is a follow-up "
           "(the C server declines there and a Python host runs the pure "
           "http.server) — the SSE server-driving tests skip on Windows",
)


# ──────────────────────────────────────────────────────────────────────
# Symbol-surface checks (run on every platform)
# ──────────────────────────────────────────────────────────────────────


@_needs_native
def test_sse_native_surface_bound() -> None:
    """The rc194 SSE transport C surface is bound (handle-based serve/port/stop
    + the blocking serve-forever entry)."""
    assert _native.HAS_NATIVE
    for sym in ("srmech_mcp_sse_serve", "srmech_mcp_sse_port",
                "srmech_mcp_sse_stop", "srmech_mcp_serve_http_sse"):
        assert hasattr(_native.LIB, sym), f"{sym} not bound"


# ──────────────────────────────────────────────────────────────────────
# Server-driving round-trip (POSIX-first)
# ──────────────────────────────────────────────────────────────────────


def _sse_events(host: str, port: int) -> Iterator[Tuple[str, str]]:
    """Open GET /sse, yield ``(event-name, data)`` tuples as they arrive."""
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


class _CServer:
    """Context manager around the handle-based C SSE server."""

    def __init__(self) -> None:
        self.handle = 0
        self.port = 0

    def __enter__(self) -> "_CServer":
        started = _native.mcp_sse_serve_c("127.0.0.1", 0)
        assert started is not None, "C SSE server failed to start"
        self.handle, self.port = started
        assert self.port > 0
        return self

    def __exit__(self, *exc: object) -> None:
        assert _native.mcp_sse_stop_c(self.handle)


@_needs_native
@_posix_only
def test_sse_round_trip_native() -> None:
    """End-to-end MCP round-trip over the C HTTP+SSE transport: GET /sse →
    endpoint event; POST initialize → 202 + the response over SSE."""
    with _CServer() as srv:
        host, port = "127.0.0.1", srv.port
        received: List[Tuple[str, str]] = []
        endpoint_holder: List[str] = []
        done = threading.Event()

        def _reader() -> None:
            for evt, data in _sse_events(host, port):
                received.append((evt, data))
                if evt == "endpoint" and not endpoint_holder:
                    endpoint_holder.append(data)
                if evt == "message":
                    done.set()
                    return

        t = threading.Thread(target=_reader, daemon=True)
        t.start()
        for _ in range(100):
            if endpoint_holder:
                break
            time.sleep(0.05)
        assert endpoint_holder, "no endpoint event received"
        endpoint_url = endpoint_holder[0]
        assert endpoint_url.startswith("/message?session=")

        body = json.dumps({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "sse-c-test", "version": "0.1"},
            },
        }).encode("utf-8")
        conn = HTTPConnection(host, port, timeout=5.0)
        conn.request("POST", endpoint_url, body=body,
                     headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        assert resp.status == 202
        resp.read()

        assert done.wait(timeout=5.0), "no message event from /sse"
        message_evt = next(
            (data for evt, data in received if evt == "message"), None)
        assert message_evt is not None
        parsed = json.loads(message_evt)
        # The C server is the DEFAULT server (name srmech-mcp).
        assert parsed["result"]["serverInfo"]["name"] == "srmech-mcp"
        assert parsed["result"]["serverInfo"]["version"] == srmech.__version__
        assert parsed["result"]["protocolVersion"] == MCP_PROTOCOL_VERSION


@_needs_native
@_posix_only
def test_sse_message_is_byte_identical_to_pure() -> None:
    """The JSON-RPC response the C server pushes over SSE is byte-identical to
    the pure ``MCPServer().handle`` (native == pure — the transport composes the
    rc186 srmech_mcp_handle default server)."""
    req = {"jsonrpc": "2.0", "id": 7, "method": "ping"}
    expected = json.dumps(
        MCPServer().handle(req), separators=(",", ":"), default=str)
    with _CServer() as srv:
        host, port = "127.0.0.1", srv.port
        received: List[Tuple[str, str]] = []
        endpoint_holder: List[str] = []
        done = threading.Event()

        def _reader() -> None:
            for evt, data in _sse_events(host, port):
                received.append((evt, data))
                if evt == "endpoint" and not endpoint_holder:
                    endpoint_holder.append(data)
                if evt == "message":
                    done.set()
                    return

        threading.Thread(target=_reader, daemon=True).start()
        for _ in range(100):
            if endpoint_holder:
                break
            time.sleep(0.05)
        assert endpoint_holder
        conn = HTTPConnection(host, port, timeout=5.0)
        conn.request("POST", endpoint_holder[0],
                     body=json.dumps(req).encode("utf-8"),
                     headers={"Content-Type": "application/json"})
        assert conn.getresponse().status == 202
        assert done.wait(timeout=5.0)
        message_evt = next(
            (data for evt, data in received if evt == "message"), None)
        assert message_evt == expected


@_needs_native
@_posix_only
def test_sse_healthz_native() -> None:
    """GET /healthz on the C server → 200 + {"status": "ok"}."""
    with _CServer() as srv:
        conn = HTTPConnection("127.0.0.1", srv.port, timeout=5.0)
        conn.request("GET", "/healthz")
        resp = conn.getresponse()
        assert resp.status == 200
        assert json.loads(resp.read()) == {"status": "ok"}


@_needs_native
@_posix_only
def test_sse_unknown_path_404_native() -> None:
    """An unknown path on the C server → 404."""
    with _CServer() as srv:
        conn = HTTPConnection("127.0.0.1", srv.port, timeout=5.0)
        conn.request("GET", "/no-such-path")
        resp = conn.getresponse()
        assert resp.status == 404
        resp.read()


@_needs_native
@_posix_only
def test_sse_missing_session_400_native() -> None:
    """POST /message with no session query param → 400 (the response does not
    ride SSE — the session is unknown)."""
    with _CServer() as srv:
        conn = HTTPConnection("127.0.0.1", srv.port, timeout=5.0)
        conn.request("POST", "/message", body=b"{}",
                     headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        assert resp.status == 400
        resp.read()


@_needs_native
@_posix_only
def test_sse_teardown_is_prompt_no_hang() -> None:
    """``srmech_mcp_sse_stop`` closes the poll-gated listener + joins both
    threads promptly (the rc180 no-hang teardown discipline) — even with an open
    SSE session held by a reader thread."""
    started = _native.mcp_sse_serve_c("127.0.0.1", 0)
    assert started is not None
    handle, port = started

    reader_open = threading.Event()

    def _hold_open() -> None:
        try:
            conn = HTTPConnection("127.0.0.1", port, timeout=5.0)
            conn.request("GET", "/sse")
            resp = conn.getresponse()
            reader_open.set()
            resp.read1(4096)   # the endpoint event
        except Exception:  # noqa: BLE001 — the socket closes at teardown
            reader_open.set()

    threading.Thread(target=_hold_open, daemon=True).start()
    assert reader_open.wait(timeout=5.0)
    time.sleep(0.1)   # let the session register + the endpoint event land

    t0 = time.time()
    assert _native.mcp_sse_stop_c(handle)
    elapsed = time.time() - t0
    assert elapsed < 3.0, f"teardown took {elapsed:.2f}s — possible hang"
