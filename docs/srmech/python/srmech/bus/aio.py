"""Async wrapper for srmech.bus (v0.5.0rc5).

Thin :mod:`asyncio` shim over the sync :mod:`srmech.bus` API via
:func:`asyncio.to_thread`. Covers FastAPI / aiohttp / asyncio-native
callers without doubling C-peer complexity. The sync API remains the
single source of truth; this module is a courtesy wrapper.

Per user direction 2026-05-28: **sync primary, async wrapper.** No
native asyncio plumbing in v1 — real asyncio-native code paths (using
:func:`asyncio.open_unix_connection` / :func:`asyncio.start_server`)
can come later if a real workload demands the speed-up.

Quick start
-----------

Async client::

    from srmech.bus.aio import connect

    async def main():
        async with connect("my-endpoint") as ch:
            reply = await ch.send({"type": "ping", "payload": {"hi": 1}})
            print(reply)

Async server (handler can be sync OR async)::

    from srmech.bus.aio import serve

    async def handler(event):
        # async work allowed here
        return {"type": "pong", "echo": event["payload"]}

    async def main():
        async with serve("my-endpoint", handler) as ep:
            await asyncio.sleep(60)

Async subscribe::

    async with connect("my-endpoint") as ch:
        async for event in ch.subscribe():
            print(event)

Async pipe (daemon)::

    handle = await pipe("src", "dst", transform=lambda e: e)
    try:
        await asyncio.sleep(60)
    finally:
        await handle.stop()

Discovery::

    eps = await list_endpoints()

Design choices
--------------

1. **No native asyncio** — every async method bodies-into
   ``await asyncio.to_thread(sync_fn, *args)``. The sync API stays
   the SSOT; the async surface is a thin courtesy wrapper.

2. **Handler can be sync OR async** — :func:`serve` detects
   coroutine functions via :func:`inspect.iscoroutinefunction`.
   Async handlers are awaited back on the caller's event loop via
   :func:`asyncio.run_coroutine_threadsafe` from the sync server's
   worker thread.

3. **subscribe() returns an async generator** — wraps the sync
   generator with ``asyncio.to_thread`` per ``__anext__`` call.
   Slightly slower than native, but correct.

4. **No new sockets / asyncio.start_server** — the backend is the
   sync server. The async wrapper just sleeps in ``to_thread``.

Framework reading: Class M (cross-class bind) at the async/sync
substrate-class boundary. The asyncio event loop is one substrate-
class-instance; the thread-pool worker is another; ``to_thread`` is
the bind operator.
"""

from __future__ import annotations

import asyncio
import inspect
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

from . import _client as _sync_client
from . import _discovery as _sync_discovery
from . import _pipe as _sync_pipe
from . import _server as _sync_server

__all__ = [
    "AsyncChannel",
    "AsyncEndpoint",
    "AsyncPipeHandle",
    "connect",
    "list_endpoints",
    "pipe",
    "serve",
]


# ─────────────────────────────────────────────────────────────────────
# AsyncChannel
# ─────────────────────────────────────────────────────────────────────


class AsyncChannel:
    """Async wrapper around :class:`srmech.bus.Channel`.

    Constructed by :func:`connect`. Mirrors the sync ``Channel``
    surface; every method awaits the sync counterpart via
    :func:`asyncio.to_thread`.

    The underlying sync channel is created already-connected (a
    background reader thread runs in the sync layer; the async
    wrapper does nothing extra to spin it up).
    """

    def __init__(self, sync_channel: _sync_client.Channel) -> None:
        self._sync_channel: _sync_client.Channel = sync_channel

    # ----- properties (cheap; do NOT need to_thread) ----------------------

    @property
    def name(self) -> str:
        return self._sync_channel.name

    @property
    def transport_kind(self) -> str:
        return self._sync_channel.transport_kind

    @property
    def closed(self) -> bool:
        return self._sync_channel.closed

    @property
    def encrypted(self) -> bool:
        return self._sync_channel.encrypted

    # ----- async surface --------------------------------------------------

    async def send(
        self,
        event: Dict[str, Any],
        *,
        timeout: float = _sync_client.DEFAULT_REQUEST_TIMEOUT_S,
        expect_reply: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Async ``send`` — defers to sync ``Channel.send`` in a thread.

        Cancellable: cancelling the awaiting task raises
        :class:`asyncio.CancelledError`. The sync send may still be
        in flight in the worker thread when cancellation lands (Python
        threads cannot be force-killed); the in-flight ``send_bytes``
        completes in the background. The waiter slot is removed by
        the sync ``send`` itself when it returns / raises.
        """
        return await asyncio.to_thread(
            self._sync_channel.send,
            event,
            timeout=timeout,
            expect_reply=expect_reply,
        )

    async def recv(self, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Pull one broadcast event off the subscribe queue.

        Equivalent to ``next(channel.subscribe(timeout=timeout))``
        once subscribed. Raises :class:`StopAsyncIteration` when the
        channel closes between events.
        """
        agen = self.subscribe(timeout=timeout)
        try:
            return await agen.__anext__()
        except StopAsyncIteration:
            raise

    async def subscribe(
        self,
        *,
        timeout: Optional[float] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Async generator yielding broadcast events.

        Wraps the sync :meth:`Channel.subscribe` generator with
        :func:`asyncio.to_thread` per ``__anext__`` call. Slightly
        slower than a native asyncio reader but correct.

        Backpressure is inherited from the sync layer (its broadcast
        queue is bounded; drop-oldest on overflow).
        """
        # Build the sync generator inside the worker thread (its
        # constructor sends the _subscribe ACK round-trip).
        sync_gen = await asyncio.to_thread(
            self._sync_channel.subscribe, timeout=timeout,
        )
        # Iterate by calling next() in a worker thread per item.
        # StopIteration in a thread is converted to RuntimeError by
        # asyncio.to_thread; translate it back to StopAsyncIteration.
        sentinel = object()
        while True:
            def _next_or_sentinel():
                try:
                    return next(sync_gen)
                except StopIteration:
                    return sentinel
            item = await asyncio.to_thread(_next_or_sentinel)
            if item is sentinel:
                return
            yield item  # type: ignore[misc]

    async def close(self) -> None:
        """Close the channel (waiters wake with BusError, reader exits)."""
        await asyncio.to_thread(self._sync_channel.close)

    # ----- async-context-manager API -------------------------------------

    async def __aenter__(self) -> "AsyncChannel":
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()


# ─────────────────────────────────────────────────────────────────────
# AsyncEndpoint
# ─────────────────────────────────────────────────────────────────────


class AsyncEndpoint:
    """Async wrapper around :class:`srmech.bus.Endpoint`.

    Constructed by :func:`serve`. Mirrors the sync ``Endpoint``
    surface; mutating methods (``stop``, ``broadcast``) defer to the
    sync counterpart via :func:`asyncio.to_thread`.

    Properties read directly from the sync endpoint (cheap; no thread
    hop needed).
    """

    def __init__(self, sync_endpoint: _sync_server.Endpoint) -> None:
        self._sync_endpoint: _sync_server.Endpoint = sync_endpoint

    # ----- properties ----------------------------------------------------

    @property
    def name(self) -> str:
        return self._sync_endpoint.name

    @property
    def pid(self) -> int:
        return self._sync_endpoint.pid

    @property
    def started_at_ns(self) -> int:
        return self._sync_endpoint.started_at_ns

    @property
    def transport_kind(self) -> str:
        return self._sync_endpoint.transport_kind

    @property
    def alive(self) -> bool:
        return self._sync_endpoint.alive

    @property
    def encrypted(self) -> bool:
        return self._sync_endpoint.encrypted

    @property
    def path(self):
        return self._sync_endpoint.path

    # ----- async surface --------------------------------------------------

    async def stop(self, *, timeout: float = 2.0) -> None:
        """Shut down the endpoint (joins accept + worker threads)."""
        await asyncio.to_thread(self._sync_endpoint.stop, timeout=timeout)

    async def broadcast(
        self, type: str, payload: Optional[dict] = None,
    ) -> None:
        """Fan out a broadcast event to every subscriber (async)."""
        await asyncio.to_thread(
            self._sync_endpoint.broadcast, type, payload,
        )

    # ----- async-context-manager API -------------------------------------

    async def __aenter__(self) -> "AsyncEndpoint":
        return self

    async def __aexit__(self, *args) -> None:
        await self.stop()


# ─────────────────────────────────────────────────────────────────────
# AsyncPipeHandle
# ─────────────────────────────────────────────────────────────────────


class AsyncPipeHandle:
    """Async wrapper around :class:`srmech.bus._pipe._PipeHandle`.

    Returned by :func:`pipe`. Mirrors the sync handle surface; ``stop``
    awaits the sync ``stop`` in a worker thread.
    """

    def __init__(self, sync_handle: "_sync_pipe._PipeHandle") -> None:
        self._sync_handle = sync_handle

    @property
    def source_name(self) -> str:
        return self._sync_handle.source_name

    @property
    def sink_name(self) -> str:
        return self._sync_handle.sink_name

    @property
    def alive(self) -> bool:
        return self._sync_handle.alive

    async def stop(self, *, timeout: float = 2.0) -> None:
        await asyncio.to_thread(self._sync_handle.stop, timeout=timeout)


# ─────────────────────────────────────────────────────────────────────
# Top-level async factories
# ─────────────────────────────────────────────────────────────────────


@asynccontextmanager
async def connect(
    name: str,
    *,
    broadcast_queue_max: int = _sync_client.DEFAULT_BROADCAST_QUEUE_MAX,
    seed: Optional[bytes] = None,
) -> AsyncIterator[AsyncChannel]:
    """Async equivalent of :func:`srmech.bus.connect`.

    Yields an :class:`AsyncChannel` already connected. Closes the
    underlying sync channel on context exit (in a worker thread, so
    the close is cancellation-safe).

    Parameters mirror the sync :func:`srmech.bus.connect`.
    """
    sync_ch = await asyncio.to_thread(
        _sync_client.connect,
        name,
        broadcast_queue_max=broadcast_queue_max,
        seed=seed,
    )
    async_ch = AsyncChannel(sync_ch)
    try:
        yield async_ch
    finally:
        # Always close — even on cancellation / exception.
        await asyncio.to_thread(sync_ch.close)


@asynccontextmanager
async def serve(
    name: str,
    handler: Callable[[dict], Any],
    *,
    accept_backlog: int = 8,
    seed: Optional[bytes] = None,
) -> AsyncIterator[AsyncEndpoint]:
    """Async equivalent of :func:`srmech.bus.serve`.

    The ``handler`` can be **sync OR async**:

    * Sync handler → invoked directly in the sync server's worker
      thread (no async overhead).
    * Async handler → wrapped in a sync shim that submits the
      coroutine back to the caller's event loop via
      :func:`asyncio.run_coroutine_threadsafe` and blocks the worker
      thread until the coroutine completes. The handler thus runs on
      the original event loop, not in the worker thread.

    Parameters mirror the sync :func:`srmech.bus.serve`.
    """
    # Use inspect.iscoroutinefunction (asyncio.iscoroutinefunction
    # is deprecated for removal in Python 3.16).
    if inspect.iscoroutinefunction(handler):
        loop = asyncio.get_running_loop()
        async_handler = handler  # alias for clarity

        def _sync_shim(event: dict) -> Any:
            # Submit the coroutine back to the event loop; block this
            # worker thread until it returns. The loop is the caller's
            # original loop (captured above), so the handler runs in
            # the right context (any contextvars / loop-state visible).
            fut = asyncio.run_coroutine_threadsafe(
                async_handler(event), loop,
            )
            try:
                return fut.result()
            except Exception:
                # Re-raise into the sync server's exception path,
                # which converts to a `{"type": "_error", ...}` reply.
                raise

        wrapped_handler: Callable[[dict], Any] = _sync_shim
    else:
        wrapped_handler = handler

    sync_ep = await asyncio.to_thread(
        _sync_server.serve,
        name,
        wrapped_handler,
        accept_backlog=accept_backlog,
        seed=seed,
    )
    async_ep = AsyncEndpoint(sync_ep)
    try:
        yield async_ep
    finally:
        await asyncio.to_thread(sync_ep.stop)


async def list_endpoints() -> List[_sync_discovery.Endpoint]:
    """Async equivalent of :func:`srmech.bus.list_endpoints`.

    Returns the same list-of-:class:`Endpoint` snapshot.
    """
    return await asyncio.to_thread(_sync_discovery.list_endpoints)


async def pipe(
    source: str,
    sink: str,
    *,
    transform: Optional[Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]] = None,
    src_seed: Optional[bytes] = None,
    dst_seed: Optional[bytes] = None,
) -> AsyncPipeHandle:
    """Async equivalent of :func:`srmech.bus.pipe`.

    Returns an :class:`AsyncPipeHandle` whose ``.stop()`` is awaitable.
    The forwarding daemon itself runs in a sync background thread
    (the sync pipe loop) — no asyncio overhead in the per-event path.

    Note
    ----
    The sync :func:`srmech.bus.pipe` does not currently accept per-
    direction seeds (seeds are picked up via the cascade — env var
    or discovery file — when the pipe's internal ``connect`` calls
    open). ``src_seed`` / ``dst_seed`` are accepted for forward
    compatibility but currently ignored beyond the no-op note here;
    set ``SRMECH_BUS_SEED`` or write the discovery seed file to
    enable encryption on the inner connections.
    """
    # Forward to the sync pipe; seeds are no-ops for now (see docstring).
    sync_handle = await asyncio.to_thread(
        _sync_pipe.pipe,
        source,
        sink,
        transform=transform,
        background=True,
    )
    return AsyncPipeHandle(sync_handle)


# Per spec: `aio.list` is part of the surface. Provide it as an alias
# so users can write `await aio.list()` mirroring the sync `bus.list()`.
# Use a different name internally to avoid shadowing the builtin in
# this module's body; expose `list` via module-level alias below.

def _install_list_alias() -> None:
    """Install ``list`` as a module-level alias for ``list_endpoints``.

    Done in a helper so the local-scope ``list`` builtin in this module
    body remains the standard Python builtin (the alias only affects
    ``srmech.bus.aio.list`` lookups from outside).
    """
    import sys
    mod = sys.modules[__name__]
    setattr(mod, "list", list_endpoints)


_install_list_alias()
