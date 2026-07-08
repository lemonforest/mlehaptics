"""rc180 ANNEX Batch A part 2b — the bus pub/sub → C (BUS FULLY C).

A bare-C host must speak the pub/sub broadcast/subscribe fan-out, not just
req/rep + the encrypted transport. rc180 adds, to the standalone-C bus
(``c/src/srmech_bus.c``) over a new PAL **mutex** (``c/src/srmech_platform.c``):

* ``srmech_bus_pubsub_accept`` — accept + register one subscriber (bounded
  registry, mutex-guarded);
* ``srmech_bus_broadcast`` — fan one frame out to every active subscriber
  under the lock (serialised → per-subscriber frame order preserved; a failed
  write drops that subscriber);
* ``srmech_bus_subscriber_count`` — mutex-guarded registry-size accessor;
* ``srmech_bus_subscribe`` — client streams broadcasts, invoking the new
  ``srmech_bus_subscriber_callback_t`` per frame (a non-OK return unsubscribes);
* ``srmech_bus_pipe`` — the ``pipe`` composition (subscribe source → forward
  to sink), mirroring ``srmech.bus._pipe.pipe``.

Adding the subscriber-delivery callback typedef bumped **ABI 3 → 4** (the same
CFUNCTYPE wire-format convention as the v2→v3 handler-callback bump).

The standalone-C bus is NOT Python-dispatched (Python has its own asyncio /
socket bus), so this file pins the C surface + drives a real ctypes round-trip
proving behavior parity with the Python ``broadcast`` / ``subscribe`` /
``pipe``. The full ASAN/UBSAN + ThreadSanitizer (NO DATA RACES) coverage is the
ephemeral WSL /tmp C driver at build time (see the rc180 CHANGELOG).

numpy-free (ctypes + threading only).
"""
from __future__ import annotations

import ctypes
import threading
import time
import uuid

import pytest

from srmech.amsc import _native

_NATIVE = _native.HAS_NATIVE

requires_native = pytest.mark.skipif(
    not _NATIVE, reason="native bus C peer not loaded")


# ──────────────────────────────────────────────────────────────────────
# Surface: the new pub/sub symbols + the ABI 3 → 4 bump
# ──────────────────────────────────────────────────────────────────────

@requires_native
def test_abi_is_4():
    """The pub/sub subscriber-delivery callback typedef bumped ABI 3 → 4."""
    assert _native.NATIVE_ABI_VERSION == 4, (
        f"ABI must be 4 (rc180 pub/sub callback typedef); "
        f"got {_native.NATIVE_ABI_VERSION}"
    )
    assert _native.EXPECTED_ABI_VERSION == 4


@requires_native
def test_pubsub_symbols_present():
    """The five pub/sub C symbols are present on the loaded lib."""
    for sym in (
        "srmech_bus_pubsub_accept",
        "srmech_bus_broadcast",
        "srmech_bus_subscriber_count",
        "srmech_bus_subscribe",
        "srmech_bus_pipe",
    ):
        assert hasattr(_native.LIB, sym), f"native lib missing C symbol {sym}"


@requires_native
def test_mutex_symbols_present():
    """The PAL mutex primitives back the pub/sub registry guard (internal
    cross-TU symbols, so exported by the shared lib)."""
    for sym in (
        "srmech_plat_mutex_init",
        "srmech_plat_mutex_lock",
        "srmech_plat_mutex_unlock",
        "srmech_plat_mutex_destroy",
    ):
        assert hasattr(_native.LIB, sym), f"native lib missing PAL symbol {sym}"


def test_subscriber_callback_typedef_constructible():
    """The subscriber-delivery CFUNCTYPE trampoline is constructible (matches
    the C srmech_bus_subscriber_callback_t wire format)."""
    cb_type = _native.BUS_SUBSCRIBER_CALLBACK
    assert cb_type is not None

    def _noop(event_ptr, event_len, ud):
        return 0  # SRMECH_OK

    trampoline = cb_type(_noop)
    assert trampoline is not None


# ──────────────────────────────────────────────────────────────────────
# End-to-end: a real ctypes-driven pub/sub round-trip (behavior parity)
# ──────────────────────────────────────────────────────────────────────

def _serve(lib, name):
    """Start a pub/sub server; return its opaque handle (c_void_p)."""
    srv = ctypes.c_void_p()
    # Dummy req/rep handler — pub/sub never invokes it, but serve() needs one.
    def _handler(req, rl, resp, rli, ud):
        rli[0] = 0
        return 0
    handler = _native.BUS_HANDLER_CALLBACK(_handler)
    rc = lib.srmech_bus_serve(name.encode(), handler, None, ctypes.byref(srv))
    assert rc == 0, f"srmech_bus_serve rc={rc}"
    # Keep the handler alive for the server's lifetime.
    return srv, handler


def _wait_count(lib, srv, target, *, timeout_s=5.0):
    end = time.time() + timeout_s
    c = ctypes.c_size_t(0)
    while time.time() < end:
        if lib.srmech_bus_subscriber_count(srv, ctypes.byref(c)) == 0 \
                and c.value >= target:
            return c.value
        time.sleep(0.005)
    return c.value


@requires_native
def test_pubsub_broadcast_roundtrip():
    """Two subscribers BOTH receive every broadcast in order; a late subscriber
    misses the pre-subscribe message. Mirrors Python Endpoint.broadcast +
    Channel.subscribe over the standalone-C bus (real AF_UNIX PAL transport +
    PAL mutex registry)."""
    lib = _native.LIB
    name = f"rc180pytest-{uuid.uuid4().hex[:10]}"
    srv, _handler = _serve(lib, name)
    try:
        # Two collectors; each stops after `want` events (cb returns non-OK).
        results = {}
        cbs = {}  # keep CFUNCTYPE objects referenced (GC safety)
        threads = {}

        def make_client(tag, want):
            got = []
            results[tag] = got

            def _cb(event_ptr, event_len, ud):
                got.append(ctypes.string_at(event_ptr, event_len))
                return 0 if len(got) < want else 2  # 2 => unsubscribe

            cb = _native.BUS_SUBSCRIBER_CALLBACK(_cb)
            cbs[tag] = cb

            def _run():
                cli = ctypes.c_void_p()
                if lib.srmech_bus_connect(name.encode(), ctypes.byref(cli)) != 0:
                    return
                buf = (ctypes.c_ubyte * 4096)()
                lib.srmech_bus_subscribe(cli, buf, 4096, cb, None)
                lib.srmech_bus_client_close(cli)

            th = threading.Thread(target=_run, daemon=True)
            threads[tag] = th
            th.start()

        # Subscriber A (expects m1, m2).
        make_client("A", 2)
        assert lib.srmech_bus_pubsub_accept(srv) == 0
        assert _wait_count(lib, srv, 1) == 1
        assert lib.srmech_bus_broadcast(srv, b"m1", 2) == 0

        # Subscriber B connects LATE (expects only m2).
        make_client("B", 1)
        assert lib.srmech_bus_pubsub_accept(srv) == 0
        assert _wait_count(lib, srv, 2) == 2
        assert lib.srmech_bus_broadcast(srv, b"m2", 2) == 0

        threads["A"].join(timeout=5.0)
        threads["B"].join(timeout=5.0)
        assert not threads["A"].is_alive()
        assert not threads["B"].is_alive()

        # A got both in order; B (late) got only the post-subscribe message.
        assert results["A"] == [b"m1", b"m2"], results["A"]
        assert results["B"] == [b"m2"], results["B"]
    finally:
        assert lib.srmech_bus_server_stop(srv) == 0


@requires_native
def test_pubsub_unsubscribe_drops_subscriber():
    """After a subscriber unsubscribes (cb non-OK → closes), the next broadcast
    fails to write to it and the server DROPS it from the registry."""
    lib = _native.LIB
    name = f"rc180pytest-{uuid.uuid4().hex[:10]}"
    srv, _handler = _serve(lib, name)
    try:
        got = []

        def _cb(event_ptr, event_len, ud):
            got.append(ctypes.string_at(event_ptr, event_len))
            return 2  # unsubscribe after the first event

        cb = _native.BUS_SUBSCRIBER_CALLBACK(_cb)

        def _run():
            cli = ctypes.c_void_p()
            if lib.srmech_bus_connect(name.encode(), ctypes.byref(cli)) != 0:
                return
            buf = (ctypes.c_ubyte * 4096)()
            lib.srmech_bus_subscribe(cli, buf, 4096, cb, None)
            lib.srmech_bus_client_close(cli)

        th = threading.Thread(target=_run, daemon=True)
        th.start()
        assert lib.srmech_bus_pubsub_accept(srv) == 0
        assert _wait_count(lib, srv, 1) == 1
        assert lib.srmech_bus_broadcast(srv, b"m1", 2) == 0
        th.join(timeout=5.0)
        assert not th.is_alive()
        assert got == [b"m1"]

        time.sleep(0.05)  # let the client-close propagate
        # Next broadcast: the write to the dead conn fails → subscriber dropped.
        assert lib.srmech_bus_broadcast(srv, b"m2", 2) == 0
        assert _wait_count(lib, srv, 0, timeout_s=1.0) == 0
        c = ctypes.c_size_t(99)
        assert lib.srmech_bus_subscriber_count(srv, ctypes.byref(c)) == 0
        assert c.value == 0
        assert got == [b"m1"]  # no delivery after unsubscribe
    finally:
        assert lib.srmech_bus_server_stop(srv) == 0
