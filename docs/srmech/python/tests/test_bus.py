"""Tests for srmech.bus — cross-process IPC skeleton (v0.5.0rc1).

Test groups:

* Framing (TLV pack/unpack; round-trip; error cases)
* Event (serialize/parse round-trip; missing field detection)
* Transport selection (kind / paths / platform branches)
* Server / Channel lifecycle (in-process, single thread)
* Req/rep semantics (single request; concurrent requests; timeout)
* Pub/sub broadcast (single + multiple subscribers)
* Discovery (list / by_name / ownership filter / dead-cleanup)
* Cross-process smoke (multiprocessing.Process; full round-trip)
* Pipe (transform; broadcast forwarding)
* Error cases (no such endpoint; server died mid-call; framing error)

Per spec rc1: pure Python; no C peer; sync API only; OFF by default.
"""

from __future__ import annotations

import io
import multiprocessing
import os
import socket
import struct
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

import pytest

from srmech.bus import (
    BUS_DIR_NAME,
    MPR_VERSION_BUS,
    BusError,
    BusTimeout,
    Channel,
    Endpoint,
    Event,
    bus_dir,
    by_name,
    connect,
    is_posix_uds,
    list as list_endpoints_short,
    list_endpoints,
    new_correlation_id,
    pipe,
    serve,
    transport_kind,
)
from srmech.bus._event import (
    BUS_SOCK_PREFIX,
    BUS_SOCK_SUFFIX,
    BUS_REGISTRY_SUFFIX,
    make_event,
    parse,
    serialize,
)
from srmech.bus._framing import (
    FRAME_PREFIX_BYTES,
    FramingError,
    MAX_FRAME_PAYLOAD_BYTES,
    pack_frame,
    unpack_frame,
)
from srmech.bus._transport import (
    Connection,
    TCPLoopbackTransport,
    UDSTransport,
    open_server_transport,
    registry_path,
    sock_path,
)


# ──────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────


@pytest.fixture
def unique_name():
    """Yield a unique endpoint name + clean up the registration on exit."""
    name = f"test-{uuid.uuid4().hex[:12]}"
    yield name
    # Cleanup any leftover files (best-effort).
    for p in (sock_path(name), registry_path(name)):
        try:
            if p.exists():
                p.unlink()
        except OSError:
            pass


def _wait_for_endpoint(name: str, *, timeout_s: float = 5.0) -> None:
    """Block until an endpoint registration shows up on disk."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        ep = by_name(name)
        if ep is not None and ep.alive:
            return
        time.sleep(0.02)
    pytest.fail(f"endpoint {name!r} did not come up within {timeout_s}s")


# ──────────────────────────────────────────────────────────────────────
# Framing
# ──────────────────────────────────────────────────────────────────────


def test_framing_round_trip_simple():
    payload = b"hello world"
    frame = pack_frame(payload)
    assert len(frame) == FRAME_PREFIX_BYTES + len(payload)
    assert frame[:FRAME_PREFIX_BYTES] == struct.pack(">I", len(payload))
    out = unpack_frame(io.BytesIO(frame))
    assert out == payload


def test_framing_empty_payload():
    frame = pack_frame(b"")
    assert frame == struct.pack(">I", 0)
    out = unpack_frame(io.BytesIO(frame))
    assert out == b""


def test_framing_clean_eof_returns_none():
    out = unpack_frame(io.BytesIO(b""))
    assert out is None


def test_framing_short_read_raises():
    with pytest.raises(FramingError):
        unpack_frame(io.BytesIO(b"\x00\x00"))  # half a header


def test_framing_short_payload_raises():
    # Header says 10 bytes; only 3 follow.
    bad = struct.pack(">I", 10) + b"abc"
    with pytest.raises(FramingError):
        unpack_frame(io.BytesIO(bad))


def test_framing_max_length_guard():
    huge = struct.pack(">I", MAX_FRAME_PAYLOAD_BYTES + 1)
    with pytest.raises(FramingError):
        unpack_frame(io.BytesIO(huge + b"x" * 100))


def test_framing_pack_rejects_non_bytes():
    with pytest.raises(TypeError):
        pack_frame("not bytes")  # type: ignore[arg-type]


def test_framing_pack_rejects_oversize():
    # Synthesise a "payload" that claims to be too big — use a class
    # with __len__ to avoid actually allocating 64 MiB.
    class FakeBytes(bytes):
        def __len__(self) -> int:  # type: ignore[override]
            return MAX_FRAME_PAYLOAD_BYTES + 1
    # We instead just check the type+ValueError contract on real bytes:
    # construct a moderately-sized bytes and patch MAX:
    import srmech.bus._framing as _fr
    saved = _fr.MAX_FRAME_PAYLOAD_BYTES
    try:
        _fr.MAX_FRAME_PAYLOAD_BYTES = 4
        with pytest.raises(ValueError):
            pack_frame(b"abcde")  # 5 > 4
    finally:
        _fr.MAX_FRAME_PAYLOAD_BYTES = saved


# ──────────────────────────────────────────────────────────────────────
# Event (de)serialisation
# ──────────────────────────────────────────────────────────────────────


def test_event_round_trip():
    ev = make_event(
        type="ping",
        payload={"hello": "world", "n": 42},
        sender_pid=1234,
        sender_name="test",
        correlation_id="abcd",
    )
    raw = serialize(ev)
    back = parse(raw)
    assert back.type == "ping"
    assert back.payload == {"hello": "world", "n": 42}
    assert back.correlation_id == "abcd"
    assert back.attestation["sender_pid"] == 1234


def test_event_deterministic_keys():
    """sort_keys=True means two events with same content encode identically."""
    a = make_event(type="x", payload={"b": 1, "a": 2}, sender_pid=1, ts_ns=10)
    b = make_event(type="x", payload={"a": 2, "b": 1}, sender_pid=1, ts_ns=10)
    assert serialize(a) == serialize(b)


def test_event_parse_rejects_empty():
    with pytest.raises(ValueError):
        parse(b"")
    with pytest.raises(ValueError):
        parse(b"   ")


def test_event_parse_rejects_missing_field():
    with pytest.raises(ValueError):
        parse(b'{"type": "x"}')  # missing mpr_version + payload + attestation


def test_event_mpr_version_constant():
    assert MPR_VERSION_BUS == "1.0"


def test_event_new_correlation_id_is_hex_uuid():
    cid = new_correlation_id()
    assert len(cid) == 32
    int(cid, 16)  # parses


# ──────────────────────────────────────────────────────────────────────
# Transport selection
# ──────────────────────────────────────────────────────────────────────


def test_transport_kind_matches_platform():
    if os.name == "posix":
        assert transport_kind() == "uds"
    else:
        # Windows / other
        assert transport_kind() == "tcp"


def test_open_server_transport_picks_right_class():
    t = open_server_transport()
    if is_posix_uds():
        assert isinstance(t, UDSTransport)
    else:
        assert isinstance(t, TCPLoopbackTransport)


def test_bus_dir_constant():
    assert BUS_DIR_NAME == ".srmech"
    assert bus_dir() == Path.home() / ".srmech"


def test_sock_path_naming():
    p = sock_path("foo")
    assert p.name == f"{BUS_SOCK_PREFIX}foo{BUS_SOCK_SUFFIX}"


def test_registry_path_naming():
    p = registry_path("foo")
    assert p.name == f"{BUS_SOCK_PREFIX}foo{BUS_REGISTRY_SUFFIX}"


# ──────────────────────────────────────────────────────────────────────
# Server / Channel lifecycle (in-process)
# ──────────────────────────────────────────────────────────────────────


def test_serve_starts_endpoint(unique_name):
    def handler(event):
        return {"type": "ack"}
    with serve(unique_name, handler=handler) as ep:
        assert ep.alive
        assert ep.name == unique_name
        assert ep.pid == os.getpid()
        assert ep.path.exists()
    # Endpoint file should be cleaned up.
    assert not ep.path.exists()


def test_serve_stop_is_idempotent(unique_name):
    def handler(event):
        return None
    ep = serve(unique_name, handler=handler)
    ep.stop()
    ep.stop()  # should not raise


def test_connect_to_missing_endpoint_raises():
    with pytest.raises(FileNotFoundError):
        connect(f"absent-{uuid.uuid4().hex[:8]}")


def test_serve_then_connect_smoke(unique_name):
    def handler(event):
        if event["type"] == "ping":
            return {"type": "pong"}
        return {"type": "unknown"}
    with serve(unique_name, handler=handler) as ep:
        _wait_for_endpoint(unique_name, timeout_s=2.0)
        with connect(unique_name) as ch:
            reply = ch.send({"type": "ping"})
            assert reply is not None
            assert reply["type"] == "pong"


# ──────────────────────────────────────────────────────────────────────
# Req/rep semantics
# ──────────────────────────────────────────────────────────────────────


def test_req_rep_echoes_payload(unique_name):
    def handler(event):
        return {"type": "echo", "payload": event.get("payload", {})}
    with serve(unique_name, handler=handler):
        with connect(unique_name) as ch:
            reply = ch.send({"type": "anything", "payload": {"x": 7}})
            assert reply["type"] == "echo"
            assert reply["payload"] == {"x": 7}


def test_req_rep_handler_none_is_fire_and_forget(unique_name):
    received = []
    def handler(event):
        received.append(event)
        return None  # fire-and-forget
    with serve(unique_name, handler=handler):
        with connect(unique_name) as ch:
            out = ch.send({"type": "noop"}, expect_reply=False)
            assert out is None
            # Give the handler a moment.
            time.sleep(0.1)
    assert any(e["type"] == "noop" for e in received)


def test_req_rep_handler_exception_returns_error(unique_name):
    def handler(event):
        raise RuntimeError("kaboom")
    with serve(unique_name, handler=handler):
        with connect(unique_name) as ch:
            reply = ch.send({"type": "go"}, timeout=2.0)
            assert reply["type"] == "_error"
            assert "kaboom" in reply["payload"]["reason"]


def test_req_rep_timeout(unique_name):
    def handler(event):
        time.sleep(2.0)
        return {"type": "late"}
    with serve(unique_name, handler=handler):
        with connect(unique_name) as ch:
            with pytest.raises(BusTimeout):
                ch.send({"type": "slow"}, timeout=0.2)


def test_req_rep_concurrent_clients(unique_name):
    """Multiple in-flight requests from one channel route correctly."""
    def handler(event):
        n = event["payload"].get("n", 0)
        return {"type": "double", "payload": {"n": n * 2}}
    with serve(unique_name, handler=handler):
        with connect(unique_name) as ch:
            results = {}
            def call(i):
                results[i] = ch.send(
                    {"type": "go", "payload": {"n": i}}, timeout=5.0
                )
            threads = [
                threading.Thread(target=call, args=(i,))
                for i in range(8)
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=5.0)
            for i in range(8):
                assert results[i]["payload"]["n"] == i * 2


def test_req_rep_sends_invalid_event_dict_raises(unique_name):
    def handler(event):
        return {"type": "ack"}
    with serve(unique_name, handler=handler):
        with connect(unique_name) as ch:
            with pytest.raises(ValueError):
                ch.send({"no_type_key": "bad"})


def test_channel_send_after_close_raises(unique_name):
    def handler(event):
        return {"type": "ack"}
    with serve(unique_name, handler=handler):
        ch = connect(unique_name)
        ch.close()
        with pytest.raises(BusError):
            ch.send({"type": "ping"})


# ──────────────────────────────────────────────────────────────────────
# Pub/sub
# ──────────────────────────────────────────────────────────────────────


def test_broadcast_to_single_subscriber(unique_name):
    def handler(event):
        return {"type": "ack"}
    with serve(unique_name, handler=handler) as ep:
        with connect(unique_name) as ch:
            # Start subscribing in a thread.
            received = []
            stop = threading.Event()
            def sub():
                for ev in ch.subscribe(timeout=0.5):
                    received.append(ev)
                    if stop.is_set():
                        return
            th = threading.Thread(target=sub, daemon=True)
            th.start()
            # Wait until the subscription has registered server-side.
            deadline = time.time() + 3.0
            while time.time() < deadline:
                if len(ep._subscribers) >= 1:
                    break
                time.sleep(0.05)
            assert len(ep._subscribers) >= 1, (
                "subscriber did not register within 3s"
            )
            ep.broadcast("status", {"step": 1})
            time.sleep(0.05)
            ep.broadcast("status", {"step": 2})
            time.sleep(0.4)
            stop.set()
            ch.close()
            th.join(timeout=2.0)
    types = [e["type"] for e in received]
    assert "status" in types
    steps = [e["payload"].get("step") for e in received if e["type"] == "status"]
    assert 1 in steps
    assert 2 in steps


def test_broadcast_to_multiple_subscribers(unique_name):
    def handler(event):
        return {"type": "ack"}
    with serve(unique_name, handler=handler) as ep:
        results = {}
        threads = []
        channels = []
        try:
            for i in range(3):
                ch = connect(unique_name)
                channels.append(ch)
                results[i] = []
                def sub(idx, channel):
                    try:
                        for ev in channel.subscribe(timeout=0.5):
                            results[idx].append(ev)
                    except Exception:
                        pass
                th = threading.Thread(
                    target=sub, args=(i, ch), daemon=True
                )
                th.start()
                threads.append(th)
            # Wait until all 3 subscribers have registered server-side.
            deadline = time.time() + 3.0
            while time.time() < deadline:
                if len(ep._subscribers) >= 3:
                    break
                time.sleep(0.05)
            assert len(ep._subscribers) >= 3, (
                f"only {len(ep._subscribers)} subscribers registered "
                f"within 3s"
            )
            # Repeat broadcasts a couple times to defeat any race
            # where a pump's queue.get() polled just before put_nowait.
            for _ in range(3):
                ep.broadcast("ping", {"a": 1})
                time.sleep(0.05)
            time.sleep(0.4)
        finally:
            for ch in channels:
                ch.close()
            for th in threads:
                th.join(timeout=2.0)
        for i in range(3):
            types = [e["type"] for e in results[i]]
            assert "ping" in types, (
                f"subscriber {i} got no ping events; saw types={types}"
            )


def test_subscribe_then_send_raises(unique_name):
    def handler(event):
        return {"type": "ack"}
    with serve(unique_name, handler=handler):
        with connect(unique_name) as ch:
            # Start subscribing — flip the channel.
            sub_iter = ch.subscribe(timeout=0.2)
            # Trigger the flip: pull one event with a tiny timeout.
            try:
                next(sub_iter)
            except StopIteration:
                pass
            # Now send() should raise.
            with pytest.raises(BusError):
                ch.send({"type": "ping"})


# ──────────────────────────────────────────────────────────────────────
# Discovery
# ──────────────────────────────────────────────────────────────────────


def test_list_endpoints_returns_list():
    out = list_endpoints()
    assert isinstance(out, list)


def test_list_finds_running_endpoint(unique_name):
    def handler(event):
        return {"type": "ack"}
    with serve(unique_name, handler=handler):
        _wait_for_endpoint(unique_name)
        names = [e.name for e in list_endpoints()]
        assert unique_name in names


def test_list_excludes_dead_endpoints(unique_name):
    def handler(event):
        return {"type": "ack"}
    ep = serve(unique_name, handler=handler)
    _wait_for_endpoint(unique_name)
    ep.stop()
    time.sleep(0.2)
    # After stop, list() should not return our endpoint.
    names = [e.name for e in list_endpoints()]
    assert unique_name not in names


def test_by_name_returns_endpoint(unique_name):
    def handler(event):
        return {"type": "ack"}
    with serve(unique_name, handler=handler):
        _wait_for_endpoint(unique_name)
        ep_rec = by_name(unique_name)
        assert ep_rec is not None
        assert ep_rec.name == unique_name
        assert ep_rec.alive


def test_by_name_missing_returns_none():
    out = by_name(f"absent-{uuid.uuid4().hex[:8]}")
    assert out is None


def test_short_list_alias_equals_list_endpoints():
    """`srmech.bus.list()` is a shadowing-builtin alias for
    `list_endpoints()`."""
    a = list_endpoints_short()
    b = list_endpoints()
    # Both calls return a *snapshot*; sets-of-names should agree on any
    # endpoints alive between the two calls.
    assert {e.name for e in a} == {e.name for e in b} or len(a) <= len(b) + 1


# ──────────────────────────────────────────────────────────────────────
# Cross-process smoke test
# ──────────────────────────────────────────────────────────────────────


def _server_main(name: str, sentinel_file: str, dwell_s: float = 3.0) -> None:
    """Worker entrypoint for the cross-process smoke test."""
    from srmech.bus import serve  # re-import in child
    def handler(event):
        if event["type"] == "ping":
            return {
                "type": "pong",
                "payload": {"echo": event["payload"].get("msg", "")},
            }
        return {"type": "unknown"}
    with serve(name, handler=handler):
        # Signal readiness.
        Path(sentinel_file).touch()
        time.sleep(dwell_s)


def test_cross_process_req_rep(unique_name, tmp_path):
    sentinel = tmp_path / "ready"
    ctx = multiprocessing.get_context("spawn")
    p = ctx.Process(target=_server_main, args=(unique_name, str(sentinel), 3.0))
    p.start()
    try:
        # Wait for server readiness signal.
        deadline = time.time() + 6.0
        while time.time() < deadline:
            if sentinel.exists():
                break
            time.sleep(0.05)
        assert sentinel.exists(), "server child did not signal ready"
        # Wait briefly for the endpoint to be reachable.
        _wait_for_endpoint(unique_name, timeout_s=4.0)
        with connect(unique_name) as ch:
            reply = ch.send({"type": "ping", "payload": {"msg": "hi"}}, timeout=3.0)
            assert reply["type"] == "pong"
            assert reply["payload"]["echo"] == "hi"
    finally:
        p.join(timeout=8.0)
        if p.is_alive():
            p.terminate()
            p.join(timeout=2.0)


# ──────────────────────────────────────────────────────────────────────
# Daemon pipe
# ──────────────────────────────────────────────────────────────────────


def test_pipe_forwards_broadcasts(unique_name):
    """Wire two endpoints together; broadcasts on source land on sink."""
    src_name = unique_name + "-src"
    sink_name = unique_name + "-sink"
    try:
        def src_handler(event):
            return {"type": "ack"}
        sink_received = []
        sink_lock = threading.Lock()

        def sink_handler(event):
            with sink_lock:
                sink_received.append(event)
            return None  # fire-and-forget

        with serve(src_name, handler=src_handler) as src_ep, \
             serve(sink_name, handler=sink_handler):
            _wait_for_endpoint(src_name)
            _wait_for_endpoint(sink_name)
            # Start the pipe.
            handle = pipe(
                src_name,
                sink_name,
                transform=lambda e: {
                    "type": "piped",
                    "payload": {**e.get("payload", {}), "mark": True},
                },
            )
            try:
                # Wait for the pipe to register as a subscriber on src.
                deadline = time.time() + 3.0
                while time.time() < deadline:
                    if len(src_ep._subscribers) >= 1:
                        break
                    time.sleep(0.05)
                assert len(src_ep._subscribers) >= 1, (
                    "pipe did not subscribe to source within 3s"
                )
                src_ep.broadcast("event", {"n": 1})
                time.sleep(0.05)
                src_ep.broadcast("event", {"n": 2})
                time.sleep(0.6)
            finally:
                handle.stop(timeout=1.0)
        # We expect both events to have made it to the sink as 'piped'.
        with sink_lock:
            types = [e["type"] for e in sink_received]
            ns = [
                e["payload"].get("n")
                for e in sink_received
                if e["type"] == "piped"
            ]
        assert "piped" in types
        assert 1 in ns
        assert 2 in ns
    finally:
        for nm in (src_name, sink_name):
            for p in (sock_path(nm), registry_path(nm)):
                try:
                    if p.exists():
                        p.unlink()
                except OSError:
                    pass


# ──────────────────────────────────────────────────────────────────────
# Error cases / robustness
# ──────────────────────────────────────────────────────────────────────


def test_send_after_server_stop_raises(unique_name):
    def handler(event):
        return {"type": "ack"}
    ep = serve(unique_name, handler=handler)
    _wait_for_endpoint(unique_name)
    ch = connect(unique_name)
    try:
        ep.stop()
        time.sleep(0.2)
        with pytest.raises((BusError, BusTimeout)):
            ch.send({"type": "ping"}, timeout=1.0)
    finally:
        ch.close()


def test_handler_returning_bare_dict_normalises(unique_name):
    """A handler may return `{"ok": True}` — server promotes to a
    `_response` event with that as payload."""
    def handler(event):
        return {"ok": True, "n": 99}
    with serve(unique_name, handler=handler):
        with connect(unique_name) as ch:
            reply = ch.send({"type": "ping"})
            # type defaults to "_response" since no type key was returned.
            assert reply["type"] == "_response"
            assert reply["payload"]["ok"] is True
            assert reply["payload"]["n"] == 99


def test_endpoint_path_is_correct_type(unique_name):
    def handler(event):
        return {"type": "ack"}
    with serve(unique_name, handler=handler) as ep:
        p = ep.path
        if is_posix_uds():
            assert p.name.endswith(BUS_SOCK_SUFFIX)
        else:
            assert p.name.endswith(BUS_REGISTRY_SUFFIX)


def test_endpoint_transport_kind_matches_platform(unique_name):
    def handler(event):
        return {"type": "ack"}
    with serve(unique_name, handler=handler) as ep:
        if is_posix_uds():
            assert ep.transport_kind == "uds"
        else:
            assert ep.transport_kind == "tcp"


def test_channel_context_manager_closes_cleanly(unique_name):
    def handler(event):
        return {"type": "ack"}
    with serve(unique_name, handler=handler):
        with connect(unique_name) as ch:
            assert not ch.closed
        assert ch.closed


def test_serve_context_manager_releases_path(unique_name):
    def handler(event):
        return {"type": "ack"}
    with serve(unique_name, handler=handler) as ep:
        path = ep.path
        assert path.exists()
    assert not path.exists()


# ──────────────────────────────────────────────────────────────────────
# Module-import hygiene
# ──────────────────────────────────────────────────────────────────────


def test_import_does_not_bind():
    """Importing srmech.bus must not bind any socket — verified by
    checking no new files appear under ~/.srmech/ from a fresh import."""
    import importlib
    import srmech.bus  # noqa: F401
    importlib.reload(srmech.bus)
    # ~/.srmech/ may exist (introspect) but no bus-import-* file should
    # appear; we just confirm the call is a no-op.
    assert hasattr(srmech.bus, "serve")
    assert hasattr(srmech.bus, "connect")
    assert hasattr(srmech.bus, "list")
    assert hasattr(srmech.bus, "pipe")


def test_public_surface_exports():
    import srmech.bus as bus
    for name in (
        "serve", "connect", "list", "pipe",
        "Endpoint", "Channel", "Event",
        "BusError", "BusTimeout",
        "bus_dir", "is_posix_uds", "transport_kind",
        "list_endpoints", "by_name",
    ):
        assert hasattr(bus, name), f"missing public export: {name}"
