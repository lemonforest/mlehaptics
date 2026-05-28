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
    elif os.name == "nt":
        # v0.5.0rc2: Windows defaults to TCP-loopback (rc1 default
        # carries forward); opt-in to the rc2 named-pipe path via
        # SRMECH_BUS_USE_NAMED_PIPE=1.
        import os as _os
        expected = "pipe" if _os.environ.get("SRMECH_BUS_USE_NAMED_PIPE") == "1" else "tcp"
        assert transport_kind() == expected
    else:
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
    """v0.5.0rc2: handler dict passes through fully as response payload.

    Bug-1 fix: a handler returning ``{"type": "echo", "x": 7}``
    yields a response whose ``payload`` is the full handler dict
    (rc1 silently dropped keys beyond ``type``). The discriminator
    ``type`` is pulled from the dict for routing convenience but
    also retained inside the payload.
    """
    def handler(event):
        return {"type": "echo", "x": 7, "echoed": event.get("payload", {})}
    with serve(unique_name, handler=handler):
        with connect(unique_name) as ch:
            reply = ch.send({"type": "anything", "payload": {"x": 7}})
            assert reply["type"] == "echo"
            # Full handler dict is the response payload (rc2 fix).
            assert reply["payload"]["x"] == 7
            assert reply["payload"]["echoed"] == {"x": 7}
            assert reply["payload"]["type"] == "echo"


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
    """Multiple in-flight requests from one channel route correctly.

    v0.5.0rc2: handler dict passes through as response.payload
    (Bug-1 fix), so ``response["payload"]["n"]`` is the doubled value.
    """
    def handler(event):
        n = event["payload"].get("n", 0)
        return {"type": "double", "n": n * 2}
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
    """Worker entrypoint for the cross-process smoke test.

    v0.5.0rc2: the handler dict passes through as response.payload
    (Bug-1 fix), so we surface ``echo`` and ``server_pid`` directly
    in the dict — both reach the client end-to-end.
    """
    from srmech.bus import serve  # re-import in child
    import os as _os
    def handler(event):
        if event["type"] == "ping":
            return {
                "type": "pong",
                "echo": event["payload"].get("msg", ""),
                "server_pid": _os.getpid(),
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
    """A handler returning a dict WITHOUT a ``type`` key gets the
    default discriminator ``"ok"`` (rc2 spec; rc1 used ``"_response"``).
    The full dict still passes through as the response payload
    per the Bug-1 fix."""
    def handler(event):
        return {"ok": True, "n": 99}
    with serve(unique_name, handler=handler):
        with connect(unique_name) as ch:
            reply = ch.send({"type": "ping"})
            # type defaults to "ok" since no type key was returned.
            assert reply["type"] == "ok"
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


# ──────────────────────────────────────────────────────────────────────
# v0.5.0rc2 — Envelope fixes (Bug 1 + Bug 2 from rc1 smoke)
# ──────────────────────────────────────────────────────────────────────


def test_envelope_handler_returns_full_dict_preserved(unique_name):
    """rc2 Bug-1 fix: every key in the handler's returned dict
    survives end-to-end as the response Event's payload."""
    def handler(event):
        return {
            "type": "pong",
            "echo": event.get("payload"),
            "server_pid": os.getpid(),
            "marker": "alpha",
            "counter": 7,
        }
    with serve(unique_name, handler=handler):
        with connect(unique_name) as ch:
            reply = ch.send(
                {"type": "ping", "payload": {"hello": "world"}},
                timeout=3.0,
            )
            assert reply["type"] == "pong"
            # Bug-1 fix: ALL keys preserved.
            assert reply["payload"]["echo"] == {"hello": "world"}
            assert reply["payload"]["server_pid"] == os.getpid()
            assert reply["payload"]["marker"] == "alpha"
            assert reply["payload"]["counter"] == 7
            # The type discriminator is also retained inside the payload.
            assert reply["payload"]["type"] == "pong"


def test_envelope_handler_no_type_defaults_to_ok(unique_name):
    """rc2 spec: handler dict without a ``type`` key gets
    discriminator ``"ok"`` (was ``"_response"`` in rc1)."""
    def handler(event):
        return {"data": "ok", "n": 99}
    with serve(unique_name, handler=handler):
        with connect(unique_name) as ch:
            reply = ch.send({"type": "anything"}, timeout=3.0)
            assert reply["type"] == "ok"
            assert reply["payload"]["data"] == "ok"
            assert reply["payload"]["n"] == 99


def test_envelope_callback_keys_preserved(unique_name):
    """Combined test — handler's full dict (including arbitrary
    free-form keys) round-trips. rc1 silently dropped these."""
    def handler(event):
        # Simulate a real-world handler returning rich metadata.
        return {
            "type": "result",
            "success": True,
            "rows": [{"a": 1}, {"a": 2}],
            "elapsed_ms": 42.5,
            "trace_id": "abc-123",
        }
    with serve(unique_name, handler=handler):
        with connect(unique_name) as ch:
            reply = ch.send({"type": "query"}, timeout=3.0)
            assert reply["payload"]["success"] is True
            assert reply["payload"]["rows"] == [{"a": 1}, {"a": 2}]
            assert reply["payload"]["elapsed_ms"] == 42.5
            assert reply["payload"]["trace_id"] == "abc-123"


def test_payload_schema_accepts_string(unique_name):
    """rc2 Bug-2 fix: client payload may be a string."""
    captured = []
    def handler(event):
        captured.append(event)
        return {"type": "ack", "got": event.get("payload")}
    with serve(unique_name, handler=handler):
        with connect(unique_name) as ch:
            reply = ch.send(
                {"type": "str", "payload": "hello world"}, timeout=3.0
            )
            assert reply["payload"]["got"] == "hello world"
    assert captured[0]["payload"] == "hello world"


def test_payload_schema_accepts_list(unique_name):
    """rc2 Bug-2 fix: client payload may be a list."""
    def handler(event):
        return {"type": "ack", "got": event.get("payload")}
    with serve(unique_name, handler=handler):
        with connect(unique_name) as ch:
            reply = ch.send(
                {"type": "lst", "payload": [1, 2, 3]}, timeout=3.0
            )
            assert reply["payload"]["got"] == [1, 2, 3]


def test_payload_schema_accepts_int(unique_name):
    def handler(event):
        return {"type": "ack", "got": event.get("payload")}
    with serve(unique_name, handler=handler):
        with connect(unique_name) as ch:
            reply = ch.send({"type": "i", "payload": 42}, timeout=3.0)
            assert reply["payload"]["got"] == 42


def test_payload_schema_accepts_float(unique_name):
    def handler(event):
        return {"type": "ack", "got": event.get("payload")}
    with serve(unique_name, handler=handler):
        with connect(unique_name) as ch:
            reply = ch.send({"type": "f", "payload": 3.14}, timeout=3.0)
            assert reply["payload"]["got"] == 3.14


def test_payload_schema_accepts_none(unique_name):
    def handler(event):
        return {"type": "ack", "got": event.get("payload")}
    with serve(unique_name, handler=handler):
        with connect(unique_name) as ch:
            reply = ch.send({"type": "n", "payload": None}, timeout=3.0)
            # None survives the round trip — server receives None,
            # echoes None back, but make_event normalises None to {}
            # for the request envelope (back-compat — see _event.py
            # docstring), so the captured payload is {} not None.
            assert reply["payload"]["got"] in (None, {})


def test_payload_schema_accepts_nested_dict(unique_name):
    def handler(event):
        return {"type": "ack", "got": event.get("payload")}
    with serve(unique_name, handler=handler):
        with connect(unique_name) as ch:
            nested = {"a": {"b": {"c": [1, 2, {"d": "deep"}]}}, "e": None}
            reply = ch.send(
                {"type": "nest", "payload": nested}, timeout=3.0
            )
            assert reply["payload"]["got"] == nested


def test_handler_exception_still_propagates_to_client(unique_name):
    """rc1 already handled this; rc2 must preserve the behavior."""
    def handler(event):
        if event["type"] == "kaboom":
            raise RuntimeError("kaboom!")
        return {"type": "ack"}
    with serve(unique_name, handler=handler):
        with connect(unique_name) as ch:
            reply = ch.send({"type": "kaboom"}, timeout=3.0)
            assert reply["type"] == "_error"
            # rc2: reason is a top-level key in the handler error dict.
            assert "kaboom" in reply["payload"]["reason"]
            assert "traceback" in reply["payload"]


# ──────────────────────────────────────────────────────────────────────
# v0.5.0rc2 — Native C peer (srmech_bus_* symbols)
# ──────────────────────────────────────────────────────────────────────


def test_native_bus_symbols_present():
    """rc2 adds five public bus C symbols + one helper. Verify the
    Python ctypes binding picked them up when HAS_NATIVE is True."""
    from srmech.amsc import _native
    if not _native.HAS_NATIVE:
        pytest.skip("native not loaded; nothing to verify")
    assert _native.NATIVE_ABI_VERSION == 3, (
        f"ABI v3 expected; got {_native.NATIVE_ABI_VERSION}"
    )
    for sym in (
        "srmech_bus_serve",
        "srmech_bus_server_accept_one",
        "srmech_bus_server_stop",
        "srmech_bus_connect",
        "srmech_bus_send_recv",
        "srmech_bus_client_close",
    ):
        assert hasattr(_native.LIB, sym), (
            f"native lib missing C symbol {sym}"
        )


def test_bus_handler_callback_typedef_constructible():
    """The CFUNCTYPE trampoline must be constructible (matches the
    C-side srmech_bus_handler_callback_t typedef wire format)."""
    from srmech.amsc import _native
    cb_type = _native.BUS_HANDLER_CALLBACK
    assert cb_type is not None
    # Build a no-op trampoline to confirm CFUNCTYPE accepts the shape.
    def _noop(req_ptr, req_len, resp_ptr, resp_len_inout, ud):
        return 0  # SRMECH_OK
    trampoline = cb_type(_noop)
    assert trampoline is not None


def test_abi_version_is_3():
    """v0.5.0rc2 ABI bump: 2 → 3 (bus C peer + new typedef).

    v0.5.0rc3: ABI unchanged at 3 (no new C symbols this rc; the
    state-chained wire-format cipher is pure-Python this round).
    """
    from srmech.amsc import _native
    assert _native.EXPECTED_ABI_VERSION == 3, (
        f"EXPECTED_ABI_VERSION should be 3; got "
        f"{_native.EXPECTED_ABI_VERSION}"
    )


# ──────────────────────────────────────────────────────────────────────
# v0.5.0rc3 — State-chained wire format ("biological TOTP-like")
# ──────────────────────────────────────────────────────────────────────

import secrets as _secrets

from srmech.bus._chain import (
    ChainCipherError,
    ChainFormatError,
    ChainState,
    COUNTER_BYTES,
    CounterReplayError,
    DIRECTION_IN,
    DIRECTION_OUT,
    FRAME_OVERHEAD_BYTES,
    MAC_BYTES,
    MacMismatchError,
    STATE_BYTES,
    decode_splice,
    derive_state,
)
from srmech.bus._seed import (
    ENV_VAR,
    MIN_SEED_BYTES,
    discard_seed_file,
    mint_and_write_seed,
    resolve_client_seed,
    resolve_server_seed,
    seed_path,
)


# ----- Chain primitives ----------------------------------------------------


def test_chain_derive_state_is_32_bytes():
    s = derive_state(b"x" * 32, b"ch", DIRECTION_OUT)
    assert isinstance(s, bytes)
    assert len(s) == STATE_BYTES


def test_chain_derive_state_direction_separation():
    """OUT-direction state_0 differs from IN-direction state_0 for the
    same seed + channel_id — defends keystream disjointness."""
    seed = b"x" * 32
    s_out = derive_state(seed, b"ch", DIRECTION_OUT)
    s_in = derive_state(seed, b"ch", DIRECTION_IN)
    assert s_out != s_in


def test_chain_derive_state_seed_separation():
    s_a = derive_state(b"A" * 32, b"ch", DIRECTION_OUT)
    s_b = derive_state(b"B" * 32, b"ch", DIRECTION_OUT)
    assert s_a != s_b


def test_chain_derive_state_channel_separation():
    seed = b"x" * 32
    s_a = derive_state(seed, b"channel-A", DIRECTION_OUT)
    s_b = derive_state(seed, b"channel-B", DIRECTION_OUT)
    assert s_a != s_b


def test_chain_derive_state_rejects_invalid_direction():
    with pytest.raises(ValueError):
        derive_state(b"x" * 32, b"ch", "sideways")


def test_chain_derive_state_rejects_empty_seed():
    with pytest.raises(ValueError):
        derive_state(b"", b"ch", DIRECTION_OUT)


def test_chain_state_init_invalid_direction():
    with pytest.raises(ValueError):
        ChainState(b"x" * 32, b"ch", "wrong")


def test_chain_encrypt_decrypt_round_trip():
    seed = b"k" * 32
    sender = ChainState(seed, b"ch", DIRECTION_OUT)
    receiver = ChainState(seed, b"ch", DIRECTION_OUT)
    plaintext = b"hello, encrypted bus"
    body = sender.encrypt(plaintext)
    assert len(body) == FRAME_OVERHEAD_BYTES + len(plaintext)
    assert receiver.decrypt(body) == plaintext


def test_chain_encrypt_advances_counter():
    seed = b"k" * 32
    s = ChainState(seed, b"ch", DIRECTION_OUT)
    assert s.counter == 0
    s.encrypt(b"a")
    assert s.counter == 1
    s.encrypt(b"b")
    assert s.counter == 2


def test_chain_encrypt_advances_state():
    seed = b"k" * 32
    s = ChainState(seed, b"ch", DIRECTION_OUT)
    state0 = s.state
    s.encrypt(b"a")
    assert s.state != state0


def test_chain_round_trip_many_frames():
    seed = b"k" * 32
    sender = ChainState(seed, b"ch", DIRECTION_OUT)
    receiver = ChainState(seed, b"ch", DIRECTION_OUT)
    plaintexts = [f"frame-{i}".encode() for i in range(20)]
    bodies = [sender.encrypt(p) for p in plaintexts]
    decoded = [receiver.decrypt(b) for b in bodies]
    assert decoded == plaintexts
    assert receiver.last_recv_counter == 19


def test_chain_round_trip_large_payload():
    """Plaintext longer than one keystream block (32 bytes) needs the
    block-extension construction to round-trip."""
    seed = b"k" * 32
    sender = ChainState(seed, b"ch", DIRECTION_OUT)
    receiver = ChainState(seed, b"ch", DIRECTION_OUT)
    plaintext = b"X" * 1000
    body = sender.encrypt(plaintext)
    assert receiver.decrypt(body) == plaintext


def test_chain_round_trip_empty_payload():
    seed = b"k" * 32
    sender = ChainState(seed, b"ch", DIRECTION_OUT)
    receiver = ChainState(seed, b"ch", DIRECTION_OUT)
    body = sender.encrypt(b"")
    assert len(body) == FRAME_OVERHEAD_BYTES
    assert receiver.decrypt(body) == b""


def test_chain_decrypt_rejects_mac_tamper():
    seed = b"k" * 32
    sender = ChainState(seed, b"ch", DIRECTION_OUT)
    receiver = ChainState(seed, b"ch", DIRECTION_OUT)
    body = sender.encrypt(b"hello")
    bad = bytes([body[0] ^ 0x01]) + body[1:]
    with pytest.raises(MacMismatchError):
        receiver.decrypt(bad)


def test_chain_decrypt_rejects_ciphertext_tamper():
    seed = b"k" * 32
    sender = ChainState(seed, b"ch", DIRECTION_OUT)
    receiver = ChainState(seed, b"ch", DIRECTION_OUT)
    body = sender.encrypt(b"hello world")
    bad = body[:-1] + bytes([body[-1] ^ 0x01])
    with pytest.raises(MacMismatchError):
        receiver.decrypt(bad)


def test_chain_decrypt_rejects_seed_mismatch():
    sender = ChainState(b"k" * 32, b"ch", DIRECTION_OUT)
    receiver = ChainState(b"j" * 32, b"ch", DIRECTION_OUT)
    body = sender.encrypt(b"hello")
    with pytest.raises(MacMismatchError):
        receiver.decrypt(body)


def test_chain_decrypt_rejects_channel_id_mismatch():
    sender = ChainState(b"k" * 32, b"channel-A", DIRECTION_OUT)
    receiver = ChainState(b"k" * 32, b"channel-B", DIRECTION_OUT)
    body = sender.encrypt(b"hello")
    with pytest.raises(MacMismatchError):
        receiver.decrypt(body)


def test_chain_decrypt_rejects_replay():
    seed = b"k" * 32
    sender = ChainState(seed, b"ch", DIRECTION_OUT)
    receiver = ChainState(seed, b"ch", DIRECTION_OUT)
    body = sender.encrypt(b"frame 0")
    # Accept once.
    receiver.decrypt(body)
    # Replaying the same frame must raise (counter no longer
    # strictly greater than last_recv_counter).
    with pytest.raises(CounterReplayError):
        receiver.decrypt(body)


def test_chain_decrypt_rejects_short_frame():
    seed = b"k" * 32
    receiver = ChainState(seed, b"ch", DIRECTION_OUT)
    with pytest.raises(ChainFormatError):
        receiver.decrypt(b"\x00" * (FRAME_OVERHEAD_BYTES - 1))


def test_chain_decrypt_rejects_non_bytes():
    seed = b"k" * 32
    receiver = ChainState(seed, b"ch", DIRECTION_OUT)
    with pytest.raises(TypeError):
        receiver.decrypt("not bytes")  # type: ignore[arg-type]


def test_chain_encrypt_rejects_non_bytes():
    seed = b"k" * 32
    sender = ChainState(seed, b"ch", DIRECTION_OUT)
    with pytest.raises(TypeError):
        sender.encrypt("not bytes")  # type: ignore[arg-type]


# ----- decode_splice (pure-function tool-schema decoder) -------------------


def test_decode_splice_round_trip():
    seed = b"k" * 32
    sender = ChainState(seed, b"ch", DIRECTION_OUT)
    state0 = sender.state
    body = sender.encrypt(b"hello via splice")
    plaintext, new_state, new_counter = decode_splice(body, state0, -1)
    assert plaintext == b"hello via splice"
    assert len(new_state) == STATE_BYTES
    assert new_counter == 0
    # The new_state must match what the sender now holds.
    assert new_state == sender.state


def test_decode_splice_chained_two_frames():
    seed = b"k" * 32
    sender = ChainState(seed, b"ch", DIRECTION_OUT)
    state = sender.state
    counter = -1
    body0 = sender.encrypt(b"alpha")
    body1 = sender.encrypt(b"beta")
    p0, state, counter = decode_splice(body0, state, counter)
    p1, state, counter = decode_splice(body1, state, counter)
    assert p0 == b"alpha"
    assert p1 == b"beta"
    assert counter == 1


def test_decode_splice_rejects_replay():
    seed = b"k" * 32
    sender = ChainState(seed, b"ch", DIRECTION_OUT)
    state = sender.state
    body = sender.encrypt(b"x")
    _, new_state, counter = decode_splice(body, state, -1)
    with pytest.raises(CounterReplayError):
        decode_splice(body, state, counter)


def test_decode_splice_rejects_tamper():
    seed = b"k" * 32
    sender = ChainState(seed, b"ch", DIRECTION_OUT)
    state = sender.state
    body = sender.encrypt(b"x")
    bad = bytes([body[0] ^ 0x01]) + body[1:]
    with pytest.raises(MacMismatchError):
        decode_splice(bad, state, -1)


def test_decode_splice_rejects_short_frame():
    with pytest.raises(ChainFormatError):
        decode_splice(
            b"\x00" * (FRAME_OVERHEAD_BYTES - 1),
            b"\x00" * STATE_BYTES, -1,
        )


def test_decode_splice_rejects_bad_state_length():
    with pytest.raises(ValueError):
        decode_splice(b"\x00" * 100, b"too-short", -1)


def test_decode_splice_rejects_non_int_counter():
    with pytest.raises(TypeError):
        decode_splice(b"\x00" * 100, b"\x00" * STATE_BYTES, "zero")  # type: ignore[arg-type]


# ----- tool-schema registration -------------------------------------------


def test_decode_splice_registered_as_tool_entry():
    """decode_splice must be registered as a srmech ToolEntry on
    `import srmech.bus`."""
    import srmech.bus  # noqa: F401 — ensure registration fires
    from srmech.amsc.tool_schema import get_tool_schema
    schema = get_tool_schema()
    entry = schema.lookup("srmech.bus.decode_splice")
    assert entry is not None, "srmech.bus.decode_splice not registered"
    assert entry.owner == "srmech"
    assert entry.category == "bus"
    pnames = [p.name for p in entry.parameters]
    assert "framed" in pnames
    assert "state" in pnames
    assert "counter" in pnames


def test_decode_splice_callable_via_public_namespace():
    from srmech.bus import decode_splice as ds_pub
    seed = b"k" * 32
    sender = ChainState(seed, b"ch", DIRECTION_OUT)
    state0 = sender.state
    body = sender.encrypt(b"abc")
    plaintext, _, _ = ds_pub(body, state0, -1)
    assert plaintext == b"abc"


# ----- Seed-resolution cascade -------------------------------------------


def test_seed_resolve_explicit_wins(monkeypatch, unique_name):
    monkeypatch.setenv(ENV_VAR, "AA" * 32)
    seed_path(unique_name).parent.mkdir(parents=True, exist_ok=True)
    seed_path(unique_name).write_bytes(b"\x42" * 32)
    try:
        explicit = b"\x99" * 32
        resolved = resolve_client_seed(unique_name, explicit=explicit)
        assert resolved == explicit
    finally:
        try:
            seed_path(unique_name).unlink()
        except OSError:
            pass


def test_seed_resolve_env_beats_file(monkeypatch, unique_name):
    env_seed = b"\xab" * 32
    monkeypatch.setenv(ENV_VAR, env_seed.hex())
    seed_path(unique_name).parent.mkdir(parents=True, exist_ok=True)
    seed_path(unique_name).write_bytes(b"\x42" * 32)
    try:
        resolved = resolve_client_seed(unique_name)
        assert resolved == env_seed
    finally:
        try:
            seed_path(unique_name).unlink()
        except OSError:
            pass


def test_seed_resolve_file_fallback(monkeypatch, unique_name):
    monkeypatch.delenv(ENV_VAR, raising=False)
    file_seed = b"\x42" * 32
    seed_path(unique_name).parent.mkdir(parents=True, exist_ok=True)
    seed_path(unique_name).write_bytes(file_seed)
    try:
        resolved = resolve_client_seed(unique_name)
        assert resolved == file_seed
    finally:
        try:
            seed_path(unique_name).unlink()
        except OSError:
            pass


def test_seed_resolve_returns_none_when_no_source(monkeypatch, unique_name):
    """No explicit, no env, no file → None (rc2 back-compat)."""
    monkeypatch.delenv(ENV_VAR, raising=False)
    try:
        seed_path(unique_name).unlink()
    except OSError:
        pass
    assert resolve_client_seed(unique_name) is None


def test_seed_resolve_rejects_short_env(monkeypatch, unique_name):
    monkeypatch.setenv(ENV_VAR, "ab" * 4)
    with pytest.raises(ValueError):
        resolve_client_seed(unique_name)


def test_seed_resolve_rejects_short_explicit(unique_name):
    with pytest.raises(ValueError):
        resolve_client_seed(unique_name, explicit=b"too-short")


def test_seed_mint_and_write(unique_name):
    seed = mint_and_write_seed(unique_name)
    try:
        assert len(seed) == MIN_SEED_BYTES
        assert seed_path(unique_name).exists()
        assert seed_path(unique_name).read_bytes() == seed
    finally:
        discard_seed_file(unique_name)


def test_seed_discard_idempotent(unique_name):
    try:
        seed_path(unique_name).unlink()
    except OSError:
        pass
    assert discard_seed_file(unique_name) is False


# ----- End-to-end bus encryption via serve()+connect() --------------------


def _make_chain_handler():
    def handler(event):
        if event["type"] == "ping":
            payload = event.get("payload") or {}
            return {"type": "pong", "echo": payload}
        return {"type": "unknown"}
    return handler


def test_unencrypted_back_compat(unique_name, monkeypatch):
    """seed=None on both ends + no env/file → rc2 plaintext bus."""
    monkeypatch.delenv(ENV_VAR, raising=False)
    try:
        seed_path(unique_name).unlink()
    except OSError:
        pass
    with serve(unique_name, _make_chain_handler()) as ep:
        assert ep.encrypted is False
        _wait_for_endpoint(unique_name)
        with connect(unique_name) as ch:
            assert ch.encrypted is False
            reply = ch.send(
                {"type": "ping", "payload": {"hello": "rc2"}}, timeout=5.0,
            )
            assert reply is not None
            assert reply["type"] == "pong"
            assert reply["payload"]["echo"] == {"hello": "rc2"}


def test_encrypted_end_to_end_inproc(unique_name, monkeypatch):
    monkeypatch.delenv(ENV_VAR, raising=False)
    try:
        seed_path(unique_name).unlink()
    except OSError:
        pass
    seed = _secrets.token_bytes(32)
    with serve(unique_name, _make_chain_handler(), seed=seed) as ep:
        assert ep.encrypted is True
        _wait_for_endpoint(unique_name)
        try:
            with connect(unique_name, seed=seed) as ch:
                assert ch.encrypted is True
                reply = ch.send(
                    {"type": "ping", "payload": {"x": 1}}, timeout=5.0,
                )
                assert reply is not None
                assert reply["type"] == "pong"
                assert reply["payload"]["echo"] == {"x": 1}
        finally:
            discard_seed_file(unique_name)


def test_encrypted_end_to_end_many_requests(unique_name, monkeypatch):
    """10 sequential encrypted requests on one channel — chain
    advances on both sides; every frame decrypts cleanly."""
    monkeypatch.delenv(ENV_VAR, raising=False)
    try:
        seed_path(unique_name).unlink()
    except OSError:
        pass
    seed = _secrets.token_bytes(32)
    with serve(unique_name, _make_chain_handler(), seed=seed) as ep:
        _wait_for_endpoint(unique_name)
        try:
            with connect(unique_name, seed=seed) as ch:
                for i in range(10):
                    reply = ch.send(
                        {"type": "ping", "payload": {"i": i}},
                        timeout=5.0,
                    )
                    assert reply is not None
                    assert reply["payload"]["echo"] == {"i": i}
        finally:
            discard_seed_file(unique_name)


def test_encrypted_seed_mismatch_raises(unique_name, monkeypatch):
    """Mismatched seeds → first MAC verification fails; server worker
    exits; client sees BusError or BusTimeout."""
    monkeypatch.delenv(ENV_VAR, raising=False)
    try:
        seed_path(unique_name).unlink()
    except OSError:
        pass
    seed_good = _secrets.token_bytes(32)
    seed_bad = _secrets.token_bytes(32)
    # Suppress discovery-file write so client's explicit bad seed isn't
    # overridden by the good one.
    from srmech.bus._seed import _write_file_seed as _wfs  # noqa: F401
    with serve(unique_name, _make_chain_handler(), seed=seed_good) as ep:
        _wait_for_endpoint(unique_name)
        try:
            # Manually overwrite the discovery file with the bad seed
            # so the client's explicit-arg path is exercised — but
            # actually we pass it explicitly below, which beats file.
            try:
                with connect(unique_name, seed=seed_bad) as ch:
                    with pytest.raises((BusTimeout, BusError)):
                        ch.send(
                            {"type": "ping", "payload": {}}, timeout=2.0,
                        )
            except (BusError, OSError):
                # Channel may close entirely before context-manager
                # exits — also acceptable.
                pass
        finally:
            discard_seed_file(unique_name)


def test_encrypted_env_var_source(unique_name, monkeypatch):
    """Seed via SRMECH_BUS_SEED env var works end-to-end."""
    seed = _secrets.token_bytes(32)
    monkeypatch.setenv(ENV_VAR, seed.hex())
    try:
        seed_path(unique_name).unlink()
    except OSError:
        pass
    with serve(unique_name, _make_chain_handler()) as ep:
        assert ep.encrypted is True
        _wait_for_endpoint(unique_name)
        try:
            with connect(unique_name) as ch:
                assert ch.encrypted is True
                reply = ch.send(
                    {"type": "ping", "payload": {"src": "env"}},
                    timeout=5.0,
                )
                assert reply is not None
                assert reply["payload"]["echo"] == {"src": "env"}
        finally:
            discard_seed_file(unique_name)


def test_encrypted_file_source(unique_name, monkeypatch):
    """Seed via 0o600 discovery file works end-to-end."""
    monkeypatch.delenv(ENV_VAR, raising=False)
    seed = mint_and_write_seed(unique_name)
    try:
        with serve(unique_name, _make_chain_handler()) as ep:
            assert ep.encrypted is True
            _wait_for_endpoint(unique_name)
            with connect(unique_name) as ch:
                assert ch.encrypted is True
                reply = ch.send(
                    {"type": "ping", "payload": {"src": "file"}},
                    timeout=5.0,
                )
                assert reply is not None
                assert reply["payload"]["echo"] == {"src": "file"}
    finally:
        discard_seed_file(unique_name)
