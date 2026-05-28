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
    MPR_VERSION_BUS,
    Event,
    make_event,
    new_correlation_id,
    parse,
    serialize,
)


def _make_event_any_payload(
    type: str,
    payload: Any,
    *,
    sender_pid: int,
    sender_name: str,
    correlation_id: str,
) -> Event:
    """Construct an :class:`Event` that accepts ANY JSON-serialisable payload.

    The canonical :func:`srmech.bus._event.make_event` helper coerces
    its ``payload`` to ``dict(payload) if payload else {}``, which is
    fine for the introspect-style read-only stream but over-restrictive
    for the bus's full req/rep surface. The v0.5.0rc2 Bug-2 fix wants
    string / list / number / None / dict payloads to all round-trip.

    This constructor is a thin specialisation that defers to the
    dataclass directly, preserving the input payload type (it's still
    JSON-serialised at frame time via :func:`json.dumps`, which will
    raise on truly non-serialisable inputs — the canonical place).
    """
    import time as _time
    return Event(
        mpr_version=MPR_VERSION_BUS,
        type=type,
        payload=payload,  # type: ignore[arg-type] — runtime is JSON-typed
        attestation={
            "sender_pid": int(sender_pid),
            "sender_name": str(sender_name),
            "ts_ns": _time.time_ns(),
        },
        correlation_id=correlation_id,
    )
from ._chain import (
    ChainCipherError,
    ChainState,
    DIRECTION_IN,
    DIRECTION_OUT,
)
from ._framing import FramingError, pack_frame, unpack_frame
from ._seed import resolve_client_seed
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
        seed: Optional[bytes] = None,
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
        # v0.5.0rc3: state-chained wire format. Seed sourced via the
        # priority cascade (explicit arg → SRMECH_BUS_SEED env →
        # ~/.srmech/bus-<name>.seed file → None=unencrypted).
        resolved_seed = resolve_client_seed(name, explicit=seed)
        self._encrypted: bool = resolved_seed is not None
        # Two per-direction ChainState instances per channel. The
        # client SENDS with DIRECTION_OUT and RECEIVES with
        # DIRECTION_IN; the server mirrors (sends DIRECTION_IN,
        # receives DIRECTION_OUT) — disjoint keystreams for the two
        # halves of the duplex.
        if self._encrypted:
            channel_id_bytes = name.encode("utf-8")
            self._send_state: Optional[ChainState] = ChainState(
                resolved_seed, channel_id_bytes, DIRECTION_OUT,
            )
            self._recv_state: Optional[ChainState] = ChainState(
                resolved_seed, channel_id_bytes, DIRECTION_IN,
            )
        else:
            self._send_state = None
            self._recv_state = None

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

    @property
    def encrypted(self) -> bool:
        """True iff this channel was opened with a seed (state-chained
        wire format active). False = rc2-compatible plaintext bus."""
        return self._encrypted

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
        # v0.5.0rc2 Bug 2 fix: accept ANY JSON-serialisable payload
        # (string, list, number, None, dict). rc1 over-restricted to
        # dict-only; standard JSON conventions allow any JSON value.
        # We do not pre-validate the type here — json.dumps below
        # raises on truly non-serialisable objects, which is the
        # canonical place to detect them.
        payload = event.get("payload")
        corr_id = new_correlation_id() if expect_reply else ""
        bus_event = _make_event_any_payload(
            type=ev_type,
            payload=payload,
            sender_pid=self._pid,
            sender_name="<client>",
            correlation_id=corr_id,
        )
        serialized = serialize(bus_event)
        waiter: Optional[_Waiter] = None
        if expect_reply:
            waiter = _Waiter()
            with self._waiters_lock:
                self._waiters[corr_id] = waiter
        # v0.5.0rc3: optional state-chained wire-format encryption.
        # When seed was supplied (via any of the three sources), wrap
        # the serialised event in the per-direction cipher state
        # before TLV-framing. The encrypt + send pair lives inside the
        # same _send_lock window so chain advancement and frame
        # ordering stay in lockstep across concurrent sender threads.
        try:
            with self._send_lock:
                if self._conn is None:
                    raise BusError("channel not connected")
                if self._encrypted:
                    assert self._send_state is not None
                    wire_body = self._send_state.encrypt(serialized)
                else:
                    wire_body = serialized
                frame = pack_frame(wire_body)
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
        # v0.5.0rc2: payload is any JSON-serialisable value, not only
        # dict. Copy dict payloads (defensive immutability) but pass
        # other types through unchanged.
        resp_payload = waiter.response.payload
        if isinstance(resp_payload, dict):
            resp_payload = dict(resp_payload)
        elif isinstance(resp_payload, list):
            resp_payload = list(resp_payload)
        return {
            "type": waiter.response.type,
            "payload": resp_payload,
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
            # v0.5.0rc2: payload is any JSON-serialisable value.
            ev_payload = ev.payload
            if isinstance(ev_payload, dict):
                ev_payload = dict(ev_payload)
            elif isinstance(ev_payload, list):
                ev_payload = list(ev_payload)
            yield {
                "type": ev.type,
                "payload": ev_payload,
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
                # v0.5.0rc3: decrypt the wire body if seed was set.
                # The reader thread is single — no lock needed on
                # _recv_state (only this thread mutates it).
                if self._encrypted:
                    assert self._recv_state is not None
                    try:
                        frame = self._recv_state.decrypt(frame)
                    except ChainCipherError as exc:
                        self._reader_error = BusError(
                            f"chain cipher error: {exc}"
                        )
                        return
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
    seed: Optional[bytes] = None,
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
    seed
        Optional pre-shared cipher seed (v0.5.0rc3+) for the
        state-chained wire format. When set, the channel encrypts
        every frame; the server must have been opened with the same
        seed (via the same arg, the ``SRMECH_BUS_SEED`` env var, or
        the ``~/.srmech/bus-{name}.seed`` discovery file). When
        ``None`` (default), the channel runs unencrypted (full
        rc2 back-compat) UNLESS one of the other two seed sources
        is populated (env var / seed file) — in which case the
        cascade auto-activates encryption.

    Returns
    -------
    Channel
        Connected channel.

    Raises
    ------
    FileNotFoundError
        If no endpoint registration is found for ``name``.
    """
    ch = Channel(
        name,
        broadcast_queue_max=broadcast_queue_max,
        seed=seed,
    )
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
