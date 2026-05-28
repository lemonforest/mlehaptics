"""Server side of srmech.bus.

The :class:`Endpoint` is the long-running listener bound to a name.
Per spec rc1: multi-threaded accept loop (one thread per accepted
connection). Handler is called synchronously per request. Req/rep
maps via ``correlation_id``; pub/sub broadcasts fan out through a
per-subscriber :class:`queue.Queue`.

Don't use asyncio — that's rc4. Don't use C — that's rc2.

Subscriber model
----------------
The server treats every connected client as a potential subscriber:
clients can issue **subscribe requests** (a special framework event
``type == "_subscribe"``) which converts the connection into a
broadcast sink. After subscribing, the connection no longer accepts
new requests — it only receives broadcasts (until close).

This keeps the wire protocol simple (one socket = one role at a
time) and matches the spec: ``Channel.subscribe()`` is a different
generator from ``Channel.send()``.

Framework reading: this is Class M extended to the OS-process
boundary, with the accept-loop as the cross-class bind operator and
the handler as the substrate-content-routing rule.
"""

from __future__ import annotations

import logging
import os
import queue
import socket
import threading
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional

from ._event import (
    Event,
    make_event,
    parse,
    serialize,
)
from ._framing import FramingError, pack_frame, unpack_frame
from ._transport import (
    Connection,
    Transport,
    bus_dir,
    open_server_transport,
    registry_path,
    sock_path,
    transport_kind,
)

logger = logging.getLogger("srmech.bus.server")

#: Special event type that converts a connection into a subscriber.
SUBSCRIBE_TYPE = "_subscribe"

#: Special event type that unsubscribes (rarely needed; close works too).
UNSUBSCRIBE_TYPE = "_unsubscribe"


# Type alias for user handler.
Handler = Callable[[dict], Optional[dict]]


@dataclass
class _Subscriber:
    """One subscribed connection + its outbound broadcast queue."""

    conn: Connection
    out_q: "queue.Queue[Optional[bytes]]"  # None sentinel = shutdown
    pump_thread: threading.Thread


class Endpoint:
    """A running bus server bound to one name.

    Spec: ``with serve(name, handler=handler) as ep: ...``. The
    context manager blocks UNTIL the handler returns (in handler-
    threads each request is one call), but the public surface lets
    callers run the server in a background thread via the underlying
    accept loop. The default ``serve`` does NOT block — it starts the
    accept thread and returns the endpoint; ``ep.stop()`` shuts down.

    Attributes are read-only properties; mutation goes through
    methods.
    """

    def __init__(
        self,
        name: str,
        handler: Handler,
        *,
        transport: Optional[Transport] = None,
        accept_backlog: int = 8,
    ) -> None:
        self._name: str = name
        self._handler: Handler = handler
        self._transport: Transport = transport or open_server_transport()
        self._accept_backlog: int = accept_backlog
        self._pid: int = os.getpid()
        self._started_at_ns: int = time.time_ns()
        self._accept_thread: Optional[threading.Thread] = None
        self._worker_threads: List[threading.Thread] = []
        self._stop_event = threading.Event()
        self._subscribers: List[_Subscriber] = []
        self._sub_lock = threading.Lock()
        self._started: bool = False
        self._stopped: bool = False

    # ----- public surface --------------------------------------------------

    @property
    def name(self) -> str:
        return self._name

    @property
    def pid(self) -> int:
        return self._pid

    @property
    def started_at_ns(self) -> int:
        return self._started_at_ns

    @property
    def transport_kind(self) -> str:
        return self._transport.kind

    @property
    def path(self) -> Path:
        """On-disk path of the endpoint registration."""
        if self._transport.kind == "uds":
            return sock_path(self._name)
        return registry_path(self._name)

    @property
    def alive(self) -> bool:
        return self._started and not self._stop_event.is_set()

    def start(self) -> None:
        """Bind, listen, and launch the accept thread (non-blocking)."""
        if self._started:
            return
        self._started = True
        self._transport.bind(self._name)
        self._transport.listen(self._accept_backlog)
        self._accept_thread = threading.Thread(
            target=self._accept_loop,
            name=f"srmech-bus-accept-{self._name}",
            daemon=True,
        )
        self._accept_thread.start()

    def stop(self, *, timeout: float = 2.0) -> None:
        """Signal shutdown, close everything, join threads."""
        if self._stopped:
            return
        self._stopped = True
        self._stop_event.set()
        # Close transport (this also unblocks the accept thread).
        try:
            self._transport.close()
        except Exception:
            pass
        # Tell every subscriber to drain.
        with self._sub_lock:
            subs = list(self._subscribers)
            self._subscribers.clear()
        for sub in subs:
            try:
                sub.out_q.put_nowait(None)  # shutdown sentinel
            except queue.Full:
                pass
            try:
                sub.conn.close()
            except Exception:
                pass
        # Join accept thread.
        if self._accept_thread is not None:
            self._accept_thread.join(timeout=timeout)
        # Join worker threads (best-effort).
        for th in list(self._worker_threads):
            th.join(timeout=timeout)

    def broadcast(self, type: str, payload: Optional[dict] = None) -> None:
        """Push a broadcast event to every connected subscriber.

        Non-blocking: enqueues to each subscriber's outbound queue.
        Subscribers whose queues are full have the event dropped
        (back-pressure policy: drop-newest; we prioritise the server's
        progress over guaranteed delivery; subscribers can re-fetch
        state via a follow-up snapshot request).
        """
        ev = make_event(
            type=type,
            payload=payload or {},
            sender_pid=self._pid,
            sender_name=self._name,
        )
        frame = pack_frame(serialize(ev))
        with self._sub_lock:
            subs = list(self._subscribers)
        for sub in subs:
            try:
                sub.out_q.put_nowait(frame)
            except queue.Full:
                logger.debug(
                    "broadcast queue full for subscriber; dropping event"
                )

    # ----- context-manager API --------------------------------------------

    def __enter__(self) -> "Endpoint":
        self.start()
        return self

    def __exit__(self, *args) -> None:
        self.stop()

    # ----- internal: accept loop ------------------------------------------

    def _accept_loop(self) -> None:
        """Block in ``transport.accept()`` and spawn a worker per
        connection. Exits cleanly on ``stop_event``."""
        while not self._stop_event.is_set():
            try:
                conn, _addr = self._transport.accept()
            except OSError:
                # Transport closed; bail.
                return
            except Exception:
                logger.exception("bus accept failed")
                return
            if self._stop_event.is_set():
                try:
                    conn.close()
                except Exception:
                    pass
                return
            worker = threading.Thread(
                target=self._worker_loop,
                args=(conn,),
                name=f"srmech-bus-worker-{self._name}",
                daemon=True,
            )
            worker.start()
            self._worker_threads.append(worker)

    def _worker_loop(self, conn: Connection) -> None:
        """Handle one accepted connection.

        Reads frames until EOF / error. For each request:

        * If ``type == "_subscribe"`` — flip the connection into
          subscriber mode (spawn an outbound pump; this loop returns
          WITHOUT closing ``conn`` — the pump owns it now).
        * Otherwise — call the handler, send the response back with
          the same ``correlation_id``.

        The handler may return ``None`` to indicate a fire-and-forget
        request (no response sent). Exceptions inside the handler are
        caught and returned as ``{"type": "_error", ...}`` responses
        so the client doesn't hang.
        """
        # `should_close_conn` lets us hand `conn` off to the subscriber
        # pump without the worker closing the socket out from under it.
        should_close_conn = True
        try:
            while not self._stop_event.is_set():
                try:
                    frame = unpack_frame(conn)
                except FramingError as exc:
                    logger.debug(
                        "framing error on bus worker: %s", exc
                    )
                    return
                except OSError:
                    return
                if frame is None:
                    return  # clean EOF
                try:
                    ev = parse(frame)
                except Exception as exc:
                    # Send a structured error reply if possible.
                    err = make_event(
                        type="_error",
                        payload={"reason": f"parse: {exc}"},
                        sender_pid=self._pid,
                        sender_name=self._name,
                    )
                    try:
                        conn.send_bytes(pack_frame(serialize(err)))
                    except OSError:
                        pass
                    return
                if ev.type == SUBSCRIBE_TYPE:
                    # Hand the connection off to subscriber-pump.
                    # ACK first so the client knows the flip happened.
                    ack = make_event(
                        type="_subscribed",
                        payload={"ok": True},
                        sender_pid=self._pid,
                        sender_name=self._name,
                        correlation_id=ev.correlation_id,
                    )
                    try:
                        conn.send_bytes(pack_frame(serialize(ack)))
                    except OSError:
                        return
                    # Hand-off: pump now owns conn. Do NOT close from
                    # the worker side or the pump's sends will fail.
                    should_close_conn = False
                    self._spawn_subscriber(conn)
                    return
                # Dispatch to user handler.
                response_dict: Optional[dict]
                try:
                    response_dict = self._handler(_event_to_dict(ev))
                except Exception as exc:
                    tb = traceback.format_exc(limit=4)
                    response_dict = {
                        "type": "_error",
                        "payload": {
                            "reason": f"handler raised: {exc}",
                            "traceback": tb,
                        },
                    }
                if response_dict is None:
                    # Fire-and-forget — no response.
                    continue
                response_type, response_payload = _normalise_response(
                    response_dict
                )
                response_ev = make_event(
                    type=response_type,
                    payload=response_payload,
                    sender_pid=self._pid,
                    sender_name=self._name,
                    correlation_id=ev.correlation_id,
                )
                try:
                    conn.send_bytes(
                        pack_frame(serialize(response_ev))
                    )
                except OSError:
                    return
        except Exception:
            logger.exception("bus worker crashed")
        finally:
            if should_close_conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _spawn_subscriber(self, conn: Connection) -> None:
        """Convert a connection into a subscriber + start the pump."""
        out_q: "queue.Queue[Optional[bytes]]" = queue.Queue(maxsize=1024)
        pump = threading.Thread(
            target=self._subscriber_pump,
            args=(conn, out_q),
            name=f"srmech-bus-sub-{self._name}",
            daemon=True,
        )
        sub = _Subscriber(conn=conn, out_q=out_q, pump_thread=pump)
        with self._sub_lock:
            self._subscribers.append(sub)
        pump.start()

    def _subscriber_pump(
        self,
        conn: Connection,
        out_q: "queue.Queue[Optional[bytes]]",
    ) -> None:
        """Drain ``out_q`` and write frames to the subscriber socket.

        Returns on shutdown sentinel (``None``) or peer close.
        """
        try:
            while not self._stop_event.is_set():
                try:
                    item = out_q.get(timeout=0.5)
                except queue.Empty:
                    continue
                if item is None:
                    return  # shutdown sentinel
                try:
                    conn.send_bytes(item)
                except OSError:
                    return
        finally:
            # Remove ourselves from the subscriber list if still there.
            with self._sub_lock:
                self._subscribers = [
                    s for s in self._subscribers if s.conn is not conn
                ]
            try:
                conn.close()
            except Exception:
                pass


# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────


def _event_to_dict(ev: Event) -> dict:
    """Convert an :class:`Event` to the handler-friendly dict shape.

    The handler API per spec receives ``{"type": ..., "payload": ...}``
    directly. We expose ``attestation`` + ``correlation_id`` too in
    case the handler wants to introspect the sender; they're optional
    to read.
    """
    return {
        "type": ev.type,
        "payload": dict(ev.payload),
        "attestation": dict(ev.attestation),
        "correlation_id": ev.correlation_id,
    }


def _normalise_response(resp: dict) -> tuple:
    """Pull ``type`` + ``payload`` out of a handler response.

    Handlers may return ``{"ok": True}`` (no type key — treated as a
    bare payload) or ``{"type": "...", "payload": {...}}``. The
    spec's worked example uses both shapes; we support both.
    """
    if "type" in resp:
        type_str = str(resp["type"])
        payload = resp.get("payload", {})
        if not isinstance(payload, dict):
            payload = {"value": payload}
        return type_str, payload
    # Bare-payload form: no type; promote the whole dict to payload
    # and set type = "_response" (the default reply discriminator).
    return "_response", dict(resp)


def serve(
    name: str,
    handler: Handler,
    *,
    accept_backlog: int = 8,
) -> Endpoint:
    """Create + start an :class:`Endpoint` listening at ``name``.

    Returns immediately (non-blocking) once the accept loop is up.
    Use as a context manager (``with serve(name, handler) as ep:``)
    to ensure clean shutdown.

    Parameters
    ----------
    name
        Endpoint name (used to build the on-disk registration path).
    handler
        Callable invoked per incoming request. Receives ``dict``
        with ``type`` + ``payload`` keys; returns ``dict`` (response)
        or ``None`` (fire-and-forget).
    accept_backlog
        Listen-backlog hint for the underlying socket.

    Returns
    -------
    Endpoint
        Live endpoint. Call ``.broadcast(...)`` to fan out events,
        ``.stop()`` to shut down, or use as a context manager.
    """
    ep = Endpoint(name, handler, accept_backlog=accept_backlog)
    ep.start()
    return ep


__all__ = [
    "Endpoint",
    "Handler",
    "SUBSCRIBE_TYPE",
    "UNSUBSCRIBE_TYPE",
    "serve",
]
