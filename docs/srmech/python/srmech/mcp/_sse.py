"""HTTP+SSE transport for the MCP server (cross-process mode).

Per the MCP spec, an HTTP+SSE transport exposes two endpoints:

* ``GET /sse`` — Server-Sent-Events stream. The server first emits an
  ``event: endpoint`` event whose ``data`` field carries the URL the
  client should POST messages to (typically ``/message?session=...``).
  Subsequent JSON-RPC responses are pushed as ``event: message``
  events.
* ``POST /message`` — client posts one JSON-RPC request body; the
  server queues the response on the matching SSE stream and returns
  202 Accepted (per the spec; the actual response rides over SSE).

This implementation uses :mod:`http.server` (stdlib) so srmech has
NO new HTTP dependency. The stdlib server is single-threaded by
default; we wrap it in :class:`ThreadingHTTPServer` so multiple
clients can connect concurrently (mostly for tests — Claude Code is
typically a single client).

Limitations (acknowledged design):

* The SSE keep-alive comment cadence is generous (15s) — typical MCP
  sessions are short-lived.
* Session lookup is by query-string ``session`` parameter; we
  generate one server-side per /sse connect.
* HTTPS / auth is intentionally out of scope for this rc; users who
  need them should front the server with a reverse-proxy.
"""

from __future__ import annotations

import json
import queue
import secrets
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from ._server import MCPServer


# ──────────────────────────────────────────────────────────────────────
# Session bookkeeping
# ──────────────────────────────────────────────────────────────────────


class _Session:
    """One active SSE session — holds an outbound queue of responses
    to push to the connected client."""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        # Bounded queue avoids unbounded memory pressure on a stuck
        # client; 1024 in-flight responses is more than any practical
        # LLM tool-loop produces between SSE flushes.
        self.outbound: "queue.Queue[Optional[str]]" = queue.Queue(maxsize=1024)
        self.closed = False

    def push(self, body: str) -> None:
        """Push one SSE ``event: message`` payload."""
        if self.closed:
            return
        try:
            self.outbound.put(body, timeout=1.0)
        except queue.Full:  # pragma: no cover — bounded for defence
            pass

    def close(self) -> None:
        """Signal the SSE writer loop to terminate cleanly."""
        self.closed = True
        try:
            self.outbound.put(None, timeout=0.1)
        except queue.Full:  # pragma: no cover
            pass


class _SessionRegistry:
    """Process-wide map of session_id -> _Session. Thread-safe."""

    def __init__(self) -> None:
        self._sessions: Dict[str, _Session] = {}
        self._lock = threading.Lock()

    def create(self) -> _Session:
        session_id = secrets.token_urlsafe(16)
        sess = _Session(session_id)
        with self._lock:
            self._sessions[session_id] = sess
        return sess

    def get(self, session_id: str) -> Optional[_Session]:
        with self._lock:
            return self._sessions.get(session_id)

    def remove(self, session_id: str) -> None:
        with self._lock:
            sess = self._sessions.pop(session_id, None)
        if sess is not None:
            sess.close()


# ──────────────────────────────────────────────────────────────────────
# HTTP request handler
# ──────────────────────────────────────────────────────────────────────


def _make_handler_class(
    server: MCPServer, registry: _SessionRegistry
) -> type:
    """Construct an HTTP request-handler class closed over the given
    MCP server + session registry. We can't pass these directly into
    :class:`BaseHTTPRequestHandler` (it's instantiated per-request by
    :mod:`http.server`), so we close over them in a class factory."""

    class _Handler(BaseHTTPRequestHandler):
        # Quiet the default request-log noise; the test harness
        # captures stderr and we don't want per-request lines.
        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            return  # silence

        # ──────────────────── routing ────────────────────

        def do_GET(self) -> None:  # noqa: N802 — required name
            parsed = urlparse(self.path)
            if parsed.path == "/sse":
                self._handle_sse_get()
                return
            if parsed.path == "/healthz":
                self._send_json(HTTPStatus.OK, {"status": "ok"})
                return
            self._send_error_json(HTTPStatus.NOT_FOUND, "unknown path")

        def do_POST(self) -> None:  # noqa: N802 — required name
            parsed = urlparse(self.path)
            if parsed.path == "/message":
                self._handle_message_post(parsed.query)
                return
            self._send_error_json(HTTPStatus.NOT_FOUND, "unknown path")

        # ──────────────────── helpers ────────────────────

        def _send_json(self, status: HTTPStatus, body: Dict[str, Any]) -> None:
            payload = json.dumps(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def _send_error_json(
            self, status: HTTPStatus, message: str
        ) -> None:
            self._send_json(status, {"error": message})

        # ──────────────────── /sse ────────────────────

        def _handle_sse_get(self) -> None:
            sess = registry.create()
            # Send the SSE response headers.
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("X-Accel-Buffering", "no")  # disable nginx buffering
            self.end_headers()

            # First, push the endpoint event so the client knows
            # where to POST.
            endpoint_url = f"/message?session={sess.session_id}"
            self._sse_emit("endpoint", endpoint_url)

            # Pump the outbound queue until the session closes (or
            # the client disconnects, which surfaces as a write
            # error on the next emit).
            try:
                while not sess.closed:
                    try:
                        body = sess.outbound.get(timeout=15.0)
                    except queue.Empty:
                        # Keep-alive comment per the SSE spec.
                        try:
                            self.wfile.write(b": keepalive\n\n")
                            self.wfile.flush()
                        except (BrokenPipeError, ConnectionResetError):
                            break
                        continue
                    if body is None:
                        break
                    try:
                        self._sse_emit("message", body)
                    except (BrokenPipeError, ConnectionResetError):
                        break
            finally:
                registry.remove(sess.session_id)

        def _sse_emit(self, event: str, data: str) -> None:
            """Emit one SSE event. ``data`` is one logical payload;
            we split on newlines per the SSE spec."""
            buf: bytes = f"event: {event}\n".encode("utf-8")
            for line in data.split("\n"):
                buf += f"data: {line}\n".encode("utf-8")
            buf += b"\n"
            self.wfile.write(buf)
            self.wfile.flush()

        # ──────────────────── /message ────────────────────

        def _handle_message_post(self, query: str) -> None:
            params = parse_qs(query)
            session_ids = params.get("session", [])
            if not session_ids:
                self._send_error_json(
                    HTTPStatus.BAD_REQUEST,
                    "missing 'session' query-string parameter",
                )
                return
            sess = registry.get(session_ids[0])
            if sess is None:
                self._send_error_json(
                    HTTPStatus.NOT_FOUND, "unknown session"
                )
                return
            content_length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(content_length)
            try:
                request = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                # JSON parse error rides over SSE per spec.
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {exc}",
                    },
                }
                sess.push(json.dumps(err_resp))
                self.send_response(HTTPStatus.ACCEPTED)
                self.end_headers()
                return
            # The MCP spec says POST /message returns 202 Accepted
            # with the actual response delivered over SSE.
            self.send_response(HTTPStatus.ACCEPTED)
            self.end_headers()
            response = server.handle(request)
            if response is not None:
                sess.push(json.dumps(response, default=str))

    return _Handler


# ──────────────────────────────────────────────────────────────────────
# Public entry
# ──────────────────────────────────────────────────────────────────────


class HTTPSSEHandle:
    """Handle to a running HTTP+SSE server. Lets the caller stop the
    server cleanly + read its bound port."""

    def __init__(
        self,
        http_server: ThreadingHTTPServer,
        thread: threading.Thread,
        registry: _SessionRegistry,
    ) -> None:
        self._server = http_server
        self._thread = thread
        self._registry = registry

    @property
    def port(self) -> int:
        """Bound TCP port. With ``port=0`` the kernel assigns one;
        this attribute exposes the assigned port."""
        return self._server.server_address[1]

    @property
    def address(self) -> Tuple[str, int]:
        """``(host, port)`` of the bound socket."""
        host, port = self._server.server_address[:2]
        return (str(host), int(port))

    def stop(self, *, timeout: float = 5.0) -> None:
        """Shut the server down + join the serving thread."""
        # Close all sessions first so SSE writers wake up + exit.
        with self._registry._lock:  # noqa: SLF001 — same module
            session_ids = list(self._registry._sessions.keys())
        for sid in session_ids:
            self._registry.remove(sid)
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=timeout)


def serve_http_sse(
    *,
    name: str = "srmech-mcp",
    host: str = "127.0.0.1",
    port: int = 0,
    server: Optional[MCPServer] = None,
    background: bool = True,
) -> HTTPSSEHandle:
    """Bind a localhost port + serve MCP over HTTP+SSE.

    Parameters
    ----------
    name
        Server name advertised in ``initialize.serverInfo``. Ignored
        when ``server`` is supplied.
    host
        Bind address. Default ``"127.0.0.1"`` (localhost only).
    port
        TCP port. ``0`` (default) asks the kernel to assign one;
        read it back via ``handle.port``.
    server
        Pre-configured :class:`MCPServer`. If ``None``, a default
        one named ``name`` is constructed.
    background
        If ``True`` (default), runs the server in a daemon thread and
        returns the handle immediately. If ``False``, blocks
        serving forever (used for the CLI mode).
    """
    srv = server if server is not None else MCPServer(name=name)
    registry = _SessionRegistry()
    handler_cls = _make_handler_class(srv, registry)
    http_server = ThreadingHTTPServer((host, port), handler_cls)

    def _serve() -> None:
        http_server.serve_forever(poll_interval=0.1)

    thread = threading.Thread(target=_serve, name=f"{name}-http", daemon=True)
    thread.start()

    handle = HTTPSSEHandle(http_server, thread, registry)
    if not background:
        try:
            thread.join()
        finally:
            handle.stop()
    return handle


__all__ = ["HTTPSSEHandle", "serve_http_sse"]
