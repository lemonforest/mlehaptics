"""Tests for srmech.bus.aio — async wrapper for the bus (v0.5.0rc5).

The async surface is a thin :mod:`asyncio` shim over the sync
:mod:`srmech.bus` API via :func:`asyncio.to_thread`. These tests use
``asyncio.run(...)`` inside sync pytest functions so we don't need
``pytest-asyncio`` as a dependency (the project doesn't ship it).

Test groups:

* Surface — module imports / names / aliases
* AsyncChannel — properties / round-trip / cancellation
* AsyncEndpoint — properties / start-stop / broadcast
* Async serve — sync handler / async handler / mixed
* Async subscribe — yields events / closes cleanly
* Async list_endpoints — discovery snapshot
* Async pipe — forwards broadcasts
* Concurrency — N concurrent async clients
* Encryption — seed propagates through wrapper

Pure-Python; ABI unchanged at 3; no native asyncio plumbing.
"""

from __future__ import annotations

import asyncio
import os
import secrets
import threading
import time
import uuid
from pathlib import Path

import pytest

from srmech.bus import (
    by_name,
    serve,  # sync — used to build a test server some tests connect to async
)
from srmech.bus.aio import (
    AsyncChannel,
    AsyncEndpoint,
    AsyncPipeHandle,
    connect as aio_connect,
    list_endpoints as aio_list_endpoints,
    pipe as aio_pipe,
    serve as aio_serve,
)
from srmech.bus._transport import registry_path, sock_path


# ──────────────────────────────────────────────────────────────────────
# Fixtures + helpers
# ──────────────────────────────────────────────────────────────────────


@pytest.fixture
def unique_name():
    """Yield a unique endpoint name + clean up the registration on exit."""
    name = f"aio-test-{uuid.uuid4().hex[:12]}"
    yield name
    for p in (sock_path(name), registry_path(name)):
        try:
            if p.exists():
                p.unlink()
        except OSError:
            pass
    # Best-effort: discard any seed-discovery file too.
    try:
        seed_p = Path.home() / ".srmech" / f"bus-{name}.seed"
        if seed_p.exists():
            seed_p.unlink()
    except OSError:
        pass


def _wait_for_endpoint(name: str, *, timeout_s: float = 5.0) -> None:
    """Block until an endpoint registration shows up on disk and is alive."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        ep = by_name(name)
        if ep is not None and ep.alive:
            return
        time.sleep(0.02)
    pytest.fail(f"endpoint {name!r} did not come up within {timeout_s}s")


def _echo_handler(event):
    """Sync test handler — echoes the payload back inside a pong dict."""
    if event["type"] == "ping":
        return {
            "type": "pong",
            "echo": event["payload"],
            "server_pid": os.getpid(),
        }
    return {"type": "unknown"}


async def _async_echo_handler(event):
    """Async test handler — same shape as :func:`_echo_handler`."""
    # Yield once to prove we're really on an event loop.
    await asyncio.sleep(0)
    if event["type"] == "ping":
        return {
            "type": "pong",
            "echo": event["payload"],
            "server_pid": os.getpid(),
            "via": "async-handler",
        }
    return {"type": "unknown"}


# ──────────────────────────────────────────────────────────────────────
# Surface
# ──────────────────────────────────────────────────────────────────────


def test_aio_module_imports():
    """``srmech.bus.aio`` exposes the documented public surface."""
    from srmech.bus import aio
    assert hasattr(aio, "AsyncChannel")
    assert hasattr(aio, "AsyncEndpoint")
    assert hasattr(aio, "AsyncPipeHandle")
    assert hasattr(aio, "connect")
    assert hasattr(aio, "serve")
    assert hasattr(aio, "list_endpoints")
    assert hasattr(aio, "list")  # alias for list_endpoints
    assert hasattr(aio, "pipe")


def test_aio_list_alias_is_list_endpoints():
    """``aio.list`` is an alias for ``aio.list_endpoints`` (mirrors sync)."""
    from srmech.bus import aio
    assert aio.list is aio.list_endpoints  # type: ignore[attr-defined]


def test_aio_connect_is_async_context_manager():
    """``connect`` returns an async context manager."""
    from srmech.bus import aio
    cm = aio.connect("nonexistent-just-shape-check")
    assert hasattr(cm, "__aenter__")
    assert hasattr(cm, "__aexit__")


def test_aio_serve_is_async_context_manager():
    """``serve`` returns an async context manager."""
    from srmech.bus import aio
    cm = aio.serve("nonexistent-just-shape-check", lambda e: None)
    assert hasattr(cm, "__aenter__")
    assert hasattr(cm, "__aexit__")


# ──────────────────────────────────────────────────────────────────────
# AsyncChannel / AsyncEndpoint — properties only (no I/O)
# ──────────────────────────────────────────────────────────────────────


def test_async_channel_wraps_sync_channel_properties(unique_name):
    """AsyncChannel exposes the sync channel's properties unchanged."""
    async def main():
        with serve(unique_name, handler=_echo_handler):
            _wait_for_endpoint(unique_name)
            async with aio_connect(unique_name) as ch:
                assert isinstance(ch, AsyncChannel)
                assert ch.name == unique_name
                assert ch.transport_kind in ("uds", "tcp", "pipe")
                assert ch.closed is False
                assert ch.encrypted is False  # no seed set
    asyncio.run(main())


def test_async_endpoint_wraps_sync_endpoint_properties(unique_name):
    """AsyncEndpoint exposes the sync endpoint's properties unchanged."""
    async def main():
        async with aio_serve(unique_name, _echo_handler) as ep:
            assert isinstance(ep, AsyncEndpoint)
            assert ep.name == unique_name
            assert ep.pid == os.getpid()
            assert ep.started_at_ns > 0
            assert ep.transport_kind in ("uds", "tcp", "pipe")
            assert ep.alive is True
            assert ep.encrypted is False
            assert ep.path is not None
    asyncio.run(main())


# ──────────────────────────────────────────────────────────────────────
# Round-trip: async client ↔ sync server
# ──────────────────────────────────────────────────────────────────────


def test_async_connect_send_recv_round_trip(unique_name):
    """Async client send → sync server handler → async reply round-trip."""
    async def main():
        with serve(unique_name, handler=_echo_handler):
            _wait_for_endpoint(unique_name)
            async with aio_connect(unique_name) as ch:
                reply = await ch.send(
                    {"type": "ping", "payload": {"hi": "async"}},
                    timeout=5.0,
                )
                assert reply is not None
                assert reply["type"] == "pong"
                assert reply["payload"]["echo"] == {"hi": "async"}
    asyncio.run(main())


def test_async_send_fire_and_forget(unique_name):
    """``expect_reply=False`` returns None promptly, no waiter created."""
    async def main():
        with serve(unique_name, handler=_echo_handler):
            _wait_for_endpoint(unique_name)
            async with aio_connect(unique_name) as ch:
                result = await ch.send(
                    {"type": "ping", "payload": {"hi": "fnf"}},
                    expect_reply=False,
                )
                assert result is None
    asyncio.run(main())


def test_async_close_idempotent(unique_name):
    """Calling ``await ch.close()`` multiple times is safe."""
    async def main():
        with serve(unique_name, handler=_echo_handler):
            _wait_for_endpoint(unique_name)
            async with aio_connect(unique_name) as ch:
                await ch.close()
                await ch.close()  # should not raise
                assert ch.closed is True
    asyncio.run(main())


# ──────────────────────────────────────────────────────────────────────
# Async serve — sync handler
# ──────────────────────────────────────────────────────────────────────


def test_async_serve_with_sync_handler(unique_name):
    """``aio.serve(handler=sync_func)`` works — handler runs in worker thread."""
    async def main():
        async with aio_serve(unique_name, _echo_handler):
            _wait_for_endpoint(unique_name)
            async with aio_connect(unique_name) as ch:
                reply = await ch.send(
                    {"type": "ping", "payload": {"mode": "sync-handler"}},
                    timeout=5.0,
                )
                assert reply["type"] == "pong"
                assert reply["payload"]["echo"] == {"mode": "sync-handler"}
    asyncio.run(main())


# ──────────────────────────────────────────────────────────────────────
# Async serve — async handler (runs back on the event loop)
# ──────────────────────────────────────────────────────────────────────


def test_async_serve_with_async_handler(unique_name):
    """``aio.serve(handler=async_func)`` awaits the handler on the loop."""
    async def main():
        async with aio_serve(unique_name, _async_echo_handler):
            _wait_for_endpoint(unique_name)
            async with aio_connect(unique_name) as ch:
                reply = await ch.send(
                    {"type": "ping", "payload": {"mode": "async-handler"}},
                    timeout=5.0,
                )
                assert reply["type"] == "pong"
                assert reply["payload"]["echo"] == {"mode": "async-handler"}
                assert reply["payload"]["via"] == "async-handler"
    asyncio.run(main())


def test_async_handler_runs_on_caller_loop(unique_name):
    """Async handlers run on the original event loop, not the worker thread.

    Verified by checking the running-loop ID inside the handler matches
    the loop the caller is awaiting on.
    """
    caller_loop_id = None
    handler_loop_id = None

    async def main():
        nonlocal caller_loop_id, handler_loop_id
        caller_loop_id = id(asyncio.get_running_loop())

        async def handler(event):
            nonlocal handler_loop_id
            handler_loop_id = id(asyncio.get_running_loop())
            return {"type": "ok"}

        async with aio_serve(unique_name, handler):
            _wait_for_endpoint(unique_name)
            async with aio_connect(unique_name) as ch:
                await ch.send({"type": "ping"}, timeout=5.0)

    asyncio.run(main())
    assert caller_loop_id is not None
    assert handler_loop_id is not None
    assert caller_loop_id == handler_loop_id, (
        "async handler should run on the caller's event loop, "
        f"got handler_loop={handler_loop_id} vs caller_loop={caller_loop_id}"
    )


def test_async_handler_exception_returns_error_reply(unique_name):
    """Exceptions in an async handler surface as {'type': '_error'}."""
    async def main():
        async def bad_handler(event):
            await asyncio.sleep(0)
            raise RuntimeError("boom in async handler")

        async with aio_serve(unique_name, bad_handler):
            _wait_for_endpoint(unique_name)
            async with aio_connect(unique_name) as ch:
                reply = await ch.send({"type": "ping"}, timeout=5.0)
                assert reply["type"] == "_error"
                assert "boom in async handler" in reply["payload"]["reason"]
    asyncio.run(main())


# ──────────────────────────────────────────────────────────────────────
# Async subscribe
# ──────────────────────────────────────────────────────────────────────


def test_async_subscribe_yields_broadcast_events(unique_name):
    """async-for over ``ch.subscribe()`` yields broadcast events in order."""
    async def main():
        async with aio_serve(unique_name, _echo_handler) as ep:
            _wait_for_endpoint(unique_name)
            async with aio_connect(unique_name) as ch:
                # Start subscribing in a background task.
                received: list = []

                async def consumer():
                    async for ev in ch.subscribe(timeout=2.0):
                        received.append(ev)
                        if len(received) >= 3:
                            return

                task = asyncio.create_task(consumer())
                # Give the subscribe ACK round-trip a moment.
                await asyncio.sleep(0.2)
                # Broadcast 3 events.
                for i in range(3):
                    await ep.broadcast("tick", {"i": i})
                # Wait for the consumer to collect them.
                await asyncio.wait_for(task, timeout=5.0)

                assert len(received) == 3
                assert [e["payload"]["i"] for e in received] == [0, 1, 2]
                assert all(e["type"] == "tick" for e in received)
    asyncio.run(main())


def test_async_subscribe_closes_cleanly_on_channel_close(unique_name):
    """When the channel closes mid-iteration, the async-gen stops cleanly."""
    async def main():
        async with aio_serve(unique_name, _echo_handler) as ep:
            _wait_for_endpoint(unique_name)
            ch_ctx = aio_connect(unique_name)
            ch = await ch_ctx.__aenter__()
            try:
                received: list = []

                async def consumer():
                    async for ev in ch.subscribe(timeout=1.0):
                        received.append(ev)

                task = asyncio.create_task(consumer())
                await asyncio.sleep(0.2)
                await ep.broadcast("once", {"v": 1})
                await asyncio.sleep(0.3)
                # Now close the channel; the consumer task should finish.
                await ch.close()
                await asyncio.wait_for(task, timeout=3.0)
                # We may or may not have caught the broadcast in time;
                # the cleanliness assertion is just that the task ended.
            finally:
                await ch_ctx.__aexit__(None, None, None)
    asyncio.run(main())


# ──────────────────────────────────────────────────────────────────────
# Async list_endpoints
# ──────────────────────────────────────────────────────────────────────


def test_async_list_endpoints_includes_running(unique_name):
    """``aio.list_endpoints()`` sees a running endpoint."""
    async def main():
        async with aio_serve(unique_name, _echo_handler):
            _wait_for_endpoint(unique_name)
            eps = await aio_list_endpoints()
            names = {e.name for e in eps}
            assert unique_name in names
    asyncio.run(main())


def test_async_list_alias_works(unique_name):
    """``aio.list()`` (the alias) returns the same as ``list_endpoints()``."""
    from srmech.bus import aio

    async def main():
        async with aio_serve(unique_name, _echo_handler):
            _wait_for_endpoint(unique_name)
            a = await aio.list()  # type: ignore[attr-defined]
            b = await aio.list_endpoints()
            names_a = {e.name for e in a}
            names_b = {e.name for e in b}
            assert unique_name in names_a
            assert unique_name in names_b

    asyncio.run(main())


# ──────────────────────────────────────────────────────────────────────
# Async pipe
# ──────────────────────────────────────────────────────────────────────


def test_async_pipe_forwards_broadcasts(unique_name):
    """``aio.pipe(src, dst)`` forwards broadcasts source→sink."""
    src_name = unique_name + "-src"
    sink_name = unique_name + "-sink"
    try:
        async def main():
            sink_received: list = []
            sink_lock = threading.Lock()

            def sink_handler(event):
                with sink_lock:
                    sink_received.append(event)
                return None

            async with aio_serve(src_name, _echo_handler) as src_ep, \
                       aio_serve(sink_name, sink_handler):
                _wait_for_endpoint(src_name)
                _wait_for_endpoint(sink_name)
                handle = await aio_pipe(
                    src_name,
                    sink_name,
                    transform=lambda e: {
                        "type": "piped",
                        "payload": {**e.get("payload", {}), "mark": True},
                    },
                )
                assert isinstance(handle, AsyncPipeHandle)
                assert handle.source_name == src_name
                assert handle.sink_name == sink_name
                try:
                    # Wait briefly for the pipe to subscribe upstream.
                    await asyncio.sleep(0.4)
                    for i in range(3):
                        await src_ep.broadcast("tick", {"i": i})
                    # Drain time for the forwarding.
                    await asyncio.sleep(0.8)
                finally:
                    await handle.stop()

            assert len(sink_received) >= 1, "pipe did not forward any events"
            # Each forwarded event should have the "mark" annotation.
            for ev in sink_received:
                assert ev["payload"].get("mark") is True
        asyncio.run(main())
    finally:
        for p in (sock_path(src_name), registry_path(src_name),
                  sock_path(sink_name), registry_path(sink_name)):
            try:
                if p.exists():
                    p.unlink()
            except OSError:
                pass


# ──────────────────────────────────────────────────────────────────────
# Concurrency
# ──────────────────────────────────────────────────────────────────────


def test_concurrent_async_clients_round_trip(unique_name):
    """N=10 concurrent async clients all round-trip cleanly."""
    N = 10

    async def main():
        async with aio_serve(unique_name, _echo_handler):
            _wait_for_endpoint(unique_name)

            async def one_client(idx: int) -> dict:
                async with aio_connect(unique_name) as ch:
                    reply = await ch.send(
                        {"type": "ping", "payload": {"idx": idx}},
                        timeout=5.0,
                    )
                    return reply

            results = await asyncio.gather(
                *[one_client(i) for i in range(N)]
            )
            assert len(results) == N
            for i, r in enumerate(results):
                assert r["type"] == "pong"
                assert r["payload"]["echo"] == {"idx": i}
    asyncio.run(main())


def test_concurrent_sends_on_one_channel(unique_name):
    """Single async channel; N concurrent ``ch.send`` calls all match."""
    N = 8

    async def main():
        async with aio_serve(unique_name, _echo_handler):
            _wait_for_endpoint(unique_name)
            async with aio_connect(unique_name) as ch:
                results = await asyncio.gather(
                    *[
                        ch.send(
                            {"type": "ping", "payload": {"i": i}},
                            timeout=5.0,
                        )
                        for i in range(N)
                    ]
                )
                assert len(results) == N
                # Each reply should match by correlation_id (handled by
                # the sync layer); we just verify content here.
                seen = sorted(r["payload"]["echo"]["i"] for r in results)
                assert seen == list(range(N))
    asyncio.run(main())


# ──────────────────────────────────────────────────────────────────────
# Cancellation
# ──────────────────────────────────────────────────────────────────────


def test_async_send_cancellation(unique_name):
    """Cancelling an in-flight ``await ch.send`` raises CancelledError."""
    # We need a slow handler so the send actually has time to be cancelled.
    delay_event = threading.Event()

    def slow_handler(event):
        # Block until the test releases us, so the client's send is
        # genuinely in flight when cancellation lands.
        delay_event.wait(timeout=5.0)
        return {"type": "pong", "echo": event["payload"]}

    async def main():
        with serve(unique_name, handler=slow_handler):
            _wait_for_endpoint(unique_name)
            async with aio_connect(unique_name) as ch:
                send_task = asyncio.create_task(
                    ch.send({"type": "ping", "payload": {"x": 1}}, timeout=10.0)
                )
                # Let the send genuinely enter to_thread.
                await asyncio.sleep(0.2)
                send_task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await send_task
                # Release the handler so the server thread doesn't leak.
                delay_event.set()
                # Give the worker thread time to finish writing its reply
                # back into the now-closing channel.
                await asyncio.sleep(0.1)
    asyncio.run(main())


# ──────────────────────────────────────────────────────────────────────
# Encryption — seed propagates through wrapper
# ──────────────────────────────────────────────────────────────────────


def test_async_encrypted_channel_seed_propagates(unique_name):
    """A seed kwarg threaded through ``aio.connect`` enables encryption."""
    seed = secrets.token_bytes(32)

    async def main():
        # Build the sync server with the seed (so it accepts encrypted frames).
        with serve(unique_name, handler=_echo_handler, seed=seed):
            _wait_for_endpoint(unique_name)
            async with aio_connect(unique_name, seed=seed) as ch:
                assert ch.encrypted is True
                reply = await ch.send(
                    {"type": "ping", "payload": {"enc": True}},
                    timeout=5.0,
                )
                assert reply["type"] == "pong"
                assert reply["payload"]["echo"] == {"enc": True}
    asyncio.run(main())


def test_async_endpoint_encrypted_property(unique_name):
    """``AsyncEndpoint.encrypted`` reflects the sync endpoint's seed status."""
    seed = secrets.token_bytes(32)

    async def main():
        async with aio_serve(unique_name, _echo_handler, seed=seed) as ep:
            assert ep.encrypted is True
            _wait_for_endpoint(unique_name)
            async with aio_connect(unique_name, seed=seed) as ch:
                assert ch.encrypted is True
                reply = await ch.send(
                    {"type": "ping", "payload": {"k": 1}},
                    timeout=5.0,
                )
                assert reply["type"] == "pong"
    asyncio.run(main())


# ──────────────────────────────────────────────────────────────────────
# Backpressure — subscribe doesn't drop events under modest load
# ──────────────────────────────────────────────────────────────────────


def test_async_subscribe_backpressure_modest_load(unique_name):
    """Modest broadcast load (well under queue cap) loses no events."""
    async def main():
        async with aio_serve(unique_name, _echo_handler) as ep:
            _wait_for_endpoint(unique_name)
            async with aio_connect(unique_name) as ch:
                received: list = []

                async def consumer():
                    async for ev in ch.subscribe(timeout=2.0):
                        received.append(ev)
                        # Tiny sleep simulating slow consumer.
                        await asyncio.sleep(0.001)
                        if len(received) >= 20:
                            return

                task = asyncio.create_task(consumer())
                await asyncio.sleep(0.2)
                for i in range(20):
                    await ep.broadcast("tick", {"i": i})
                await asyncio.wait_for(task, timeout=10.0)

                assert len(received) == 20
                assert [e["payload"]["i"] for e in received] == list(range(20))
    asyncio.run(main())


# ──────────────────────────────────────────────────────────────────────
# AsyncEndpoint.broadcast
# ──────────────────────────────────────────────────────────────────────


def test_async_endpoint_broadcast_reaches_async_subscriber(unique_name):
    """``await ep.broadcast(...)`` delivers to an async subscribe()."""
    async def main():
        async with aio_serve(unique_name, _echo_handler) as ep:
            _wait_for_endpoint(unique_name)
            async with aio_connect(unique_name) as ch:
                received: list = []

                async def consumer():
                    async for ev in ch.subscribe(timeout=2.0):
                        received.append(ev)
                        return  # take one and exit

                task = asyncio.create_task(consumer())
                await asyncio.sleep(0.2)
                await ep.broadcast("hello", {"to": "subscriber"})
                await asyncio.wait_for(task, timeout=5.0)

                assert len(received) == 1
                assert received[0]["type"] == "hello"
                assert received[0]["payload"]["to"] == "subscriber"
    asyncio.run(main())


# ──────────────────────────────────────────────────────────────────────
# Stop-then-restart sanity
# ──────────────────────────────────────────────────────────────────────


def test_async_endpoint_stop_makes_alive_false(unique_name):
    """After ``await ep.stop()``, ``ep.alive`` is False."""
    async def main():
        async with aio_serve(unique_name, _echo_handler) as ep:
            _wait_for_endpoint(unique_name)
            assert ep.alive is True
        # Context exited → stop() called → alive False.
        assert ep.alive is False
    asyncio.run(main())
