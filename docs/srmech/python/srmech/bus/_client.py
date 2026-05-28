"""Client side of srmech.bus.

The :class:`Channel` is the connected client. Two modes:

* **req/rep** — call :meth:`Channel.send` with an event dict; the
  method writes the frame, blocks for the matching reply, returns
  the response dict. Correlation by ``correlation_id`` so multiple
  in-flight requests (from different threads sharing the same
  channel) match up correctly.
* **pub/sub** — call :meth:`Channel.subscribe` to flip the channel
  into broadcast-consumer mode. Returns a generator that yields
  broadcast events as they arrive from the server. Once subscribed,
  the channel is no longer usable for req/rep (server-side guarantee).

The implementation uses a single background reader thread per
channel; replies and broadcasts both arrive through the same reader.
The reader fans out:

* If the inbound event has a non-empty ``correlation_id`` and a
  request is waiting on that id — deliver to the request's
  :class:`threading.Event` + slot.
* Otherwise — push to the broadcast queue (consumed by
  :meth:`subscribe`).

This design means callers can pipeline multiple ``send()`` calls from
multiple threads without head-of-line blocking by another thread's
in-flight request.

Framework reading: Class M cross-class bind from the client side;
the correlation_id is the rational-anchor (Class N) routing token
that pairs request with response.
"""

from __future__ import annotations

import logging
import os
import queue
import threading
import time
from typing import Any, Dict, Iterator, Optional, Tuple

from ._event import (
    Event,
    make_event,
    new_correlation_id,
    parse,
    serialize,
)
from ._framing import FramingError, pack_frame, unpack_frame
from ._server import SUBSCRIBE_TYPE
from ._transport import (
    Connection,
    Transport,
    open_client_transport,
)

logger = logging.getLogger("srmech.bus.client")

#: Default request timeout (seconds). Override via the ``timeout``
#: kwarg on :meth:`Channel.send`.
DEFAULT_REQUEST_TIMEOUT_S: float = 30.0

#: Default broadcast-queue capacity. Subscribers that drain slowly
#: will see oldest events dropped once this is exceeded.
DEFAULT_BROADCAST_QUEUE_MAX: int = 4096


class BusError(Exception):
    """Raised when the bus client encounters a protocol-level error."""


class BusTimeout(BusError):
    """Raised when a ``send()`` request times out waiting for the reply."""


class _Waiter:
    """One pending request — caller blocks on ``ev`` until reply lands."""

    __slots__ = ("ev", "response", "error")

    def __init__(self) -> None:
        self.ev = threading.Event()
        self.response: Optional[Event] = None
        self.error: Optional[BaseException] = None


class Channel:
    """A client-side bus channel.

    Use as a context manager::

        with connect("my-endpoint") as ch:
            response = ch.send({"type": "ping"})
            ...

    Threadsafe req/rep — multiple threads may share one Channel.
    """

    def __init__(
        self,
        name: str,
        *,
        transport: Optional[Transport] = None,
        broadcast_queue_max: int = DEFAULT_BROADCAST_QUEUE_MAX,
    ) -> None:
        self._name: str = name
        self._transport: Transport = transport or open_client_transport()
        self._conn: Optional[Connection] = None
        self._reader_thread: Optional[threading.Thread] = None
        self._pid: int = os.getpid()
        self._closed: bool = False
        self._send_lock = threading.Lock()  # serialises socket sendall
        self._waiters_lock = threading.Lock()
        self._waiters: Dict[str, _Waiter] = {}
        self._broadcast_q: "queue.Queue[Optional[Event]]" = queue.Queue(
            maxsize=broadcast_queue_max
        )
        self._subscribed: bool = False
        self._reader_error: Optional[BaseException] = None

    # ----- public ---------------------------------------------------------

    @property
    def name(self) -> str:
        return self._name

    @property
    def transport_kind(self) -> str:
        return self._transport.kind

    @property
    def closed(self) -> bool:
        return self._closed

    def connect(self) -> None:
        """Open the underlying socket and launch the reader thread."""
        if self._conn is not None:
            return
        self._conn = self._transport.connect(self._name)
        self._reader_thread = threading.Thread(
            target=self._reader_loop,
            name=f"srmech-bus-client-{self._name}",
            daemon=True,
        )
        self._reader_thread.start()

    def close(self) -> None:
        """Close the channel; wake up any pending waiters."""
        if self._closed:
            return
        self._closed = True
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
        # Drain pending waiters with an error.
        with self._waiters_lock:
            waiters = list(self._waiters.values())
            self._waiters.clear()
        for w in waiters:
            if w.error is None:
                w.error = BusError("channel closed")
            w.ev.set()
        # Drop a sentinel into the broadcast queue (best-effort).
        try:
            self._broadcast_q.put_nowait(None)
        except queue.Full:
            pass

    def send(
        self,
        event: Dict[str, Any],
        *,
        timeout: float = DEFAULT_REQUEST_TIMEOUT_S,
        expect_reply: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Send one event; optionally wait for the matching reply.

        Parameters
        ----------
        event
            Dict with at least a ``"type"`` key. Optional
            ``"payload"`` dict. Any other top-level keys are ignored
            (the wire format puts them under ``payload`` if given).
        timeout
            Seconds to wait for the matching reply. Ignored when
            ``expect_reply=False``.
        expect_reply
            If True (default), waits for the response with the
            matching ``correlation_id`` and returns it. If False,
            sends fire-and-forget and returns ``None`` immediately.

        Returns
        -------
        dict | None
            The server's response (``type`` + ``payload`` keys) if
            ``expect_reply``; ``None`` otherwise.
        """
        if self._closed:
            raise BusError("channel is closed")
        if self._subscribed:
            raise BusError(
                "cannot send() on a subscribed channel "
                "(subscribe converts the channel into broadcast-only)"
            )
        if "type" not in event:
            raise ValueError("event dict must contain a 'type' key")
        ev_type = str(event["type"])
        payload = event.get("payload")
        if payload is not None and not isinstance(payload, dict):
            raise ValueError("event['payload'] must be a dict")
        corr_id = new_correlation_id() if expect_reply else ""
        bus_event = make_event(
            type=ev_type,
            payload=payload or {},
            sender_pid=self._pid,
            sender_name="<client>",
            correlation_id=corr_id,
        )
        frame = pack_frame(serialize(bus_event))
        waiter: Optional[_Waiter] = None
        if expect_reply:
            waiter = _Waiter()
            with self._waiters_lock:
                self._waiters[corr_id] = waiter
        try:
            with self._send_lock:
                if self._conn is None:
                    raise BusError("channel not connected")
                self._conn.send_bytes(frame)
        except OSError as exc:
            if waiter is not None:
                with self._waiters_lock:
                    self._waiters.pop(corr_id, None)
            raise BusError(f"send failed: {exc}") from exc
        if not expect_reply:
            return None
        assert waiter is not None
        ok = waiter.ev.wait(timeout=timeout)
        with self._waiters_lock:
            self._waiters.pop(corr_id, None)
        if not ok:
            raise BusTimeout(
                f"no reply within {timeout}s for type={ev_type!r}"
            )
        if waiter.error is not None:
            raise waiter.error
        if waiter.response is None:
            raise BusError("waiter signalled but no response set")
        return {
            "type": waiter.response.type,
            "payload": dict(waiter.response.payload),
            "attestation": dict(waiter.response.attestation),
            "correlation_id": waiter.response.correlation_id,
        }

    def subscribe(
        self,
        *,
        timeout: Optional[float] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Convert this channel into a broadcast consumer.

        First call sends the ``_subscribe`` framework event to the
        server and waits for the ``_subscribed`` ACK; subsequent
        iterations yield broadcast events as dicts (same shape as
        :meth:`send` returns).

        Parameters
        ----------
        timeout
            Optional inter-event timeout. ``None`` means block forever
            between events. The generator stops when the channel
            closes (server shutdown or :meth:`close` call).

        Yields
        ------
        dict
            Broadcast event with ``type``, ``payload``, ``attestation``
            keys.
        """
        if self._closed:
            raise BusError("channel is closed")
        if not self._subscribed:
            # First call — flip the channel.
            ack = self.send(
                {"type": SUBSCRIBE_TYPE},
                timeout=DEFAULT_REQUEST_TIMEOUT_S,
                expect_reply=True,
            )
            if ack is None or ack.get("type") != "_subscribed":
                raise BusError(
                    f"subscribe ACK missing or wrong type: {ack!r}"
                )
            self._subscribed = True
        # Now drain broadcasts.
        while not self._closed:
            try:
                ev = self._broadcast_q.get(timeout=timeout)
            except queue.Empty:
                return
            if ev is None:
                return  # shutdown sentinel
            yield {
                "type": ev.type,
                "payload": dict(ev.payload),
                "attestation": dict(ev.attestation),
                "correlation_id": ev.correlation_id,
            }

    # ----- context-manager API -------------------------------------------

    def __enter__(self) -> "Channel":
        self.connect()
        return self

    def __exit__(self, *args) -> None:
        self.close()

    # ----- internal: reader loop -----------------------------------------

    def _reader_loop(self) -> None:
        """Read frames from the socket; route to waiters / broadcast."""
        try:
            while not self._closed:
                if self._conn is None:
                    return
                try:
                    frame = unpack_frame(self._conn)
                except FramingError as exc:
                    self._reader_error = BusError(
                        f"framing error: {exc}"
                    )
                    return
                except OSError:
                    return
                if frame is None:
                    return  # clean EOF
                try:
                    ev = parse(frame)
                except Exception as exc:
                    logger.warning("bus client parse error: %s", exc)
                    continue
                corr_id = ev.correlation_id
                delivered = False
                if corr_id:
                    with self._waiters_lock:
                        w = self._waiters.pop(corr_id, None)
                    if w is not None:
                        w.response = ev
                        w.ev.set()
                        delivered = True
                if not delivered:
                    # Broadcast — put on queue (drop-oldest if full).
                    try:
                        self._broadcast_q.put_nowait(ev)
                    except queue.Full:
                        try:
                            self._broadcast_q.get_nowait()  # drop oldest
                            self._broadcast_q.put_nowait(ev)
                        except (queue.Empty, queue.Full):
                            pass
        finally:
            # Wake up anyone blocked on a reply when the reader dies.
            with self._waiters_lock:
                waiters = list(self._waiters.values())
                self._waiters.clear()
            for w in waiters:
                if w.error is None:
                    w.error = (
                        self._reader_error
                        or BusError("reader exited; peer closed")
                    )
                w.ev.set()
            # Wake any subscribe() generator.
            try:
                self._broadcast_q.put_nowait(None)
            except queue.Full:
                pass


def connect(
    name: str,
    *,
    broadcast_queue_max: int = DEFAULT_BROADCAST_QUEUE_MAX,
) -> Channel:
    """Open a connected :class:`Channel` to the named endpoint.

    Returns the channel already connected; use as a context manager
    for clean shutdown.

    Parameters
    ----------
    name
        Endpoint name (matches the ``name`` passed to
        :func:`srmech.bus.serve` server-side).
    broadcast_queue_max
        Maximum pending broadcasts before drop-oldest behaviour
        kicks in.

    Returns
    -------
    Channel
        Connected channel.

    Raises
    ------
    FileNotFoundError
        If no endpoint registration is found for ``name``.
    """
    ch = Channel(name, broadcast_queue_max=broadcast_queue_max)
    ch.connect()
    return ch


__all__ = [
    "BusError",
    "BusTimeout",
    "Channel",
    "DEFAULT_BROADCAST_QUEUE_MAX",
    "DEFAULT_REQUEST_TIMEOUT_S",
    "connect",
]
