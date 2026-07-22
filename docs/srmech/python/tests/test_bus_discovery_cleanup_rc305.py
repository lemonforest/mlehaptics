"""Discovery-cleanup ROOT FIX for the test_bus_aio flake (rc305, `#920`).

The flake this pins was NOT the readiness race first suspected — `by_name().alive`
already verifies by a real connect-probe (:func:`_endpoint_alive_uds`). The true
root cause (recorded in the CHANGELOG the rc283 conftest workaround references):
``list_endpoints(cleanup_dead=True)`` DELETED any socket whose 50 ms connect-probe
failed — but a server inside its ``bind()``→``listen()`` window, or one whose
accept backlog is momentarily full, refuses/times-out that probe IDENTICALLY to a
crashed server's stale file. Under a shared ``~/.srmech/`` (xdist workers share
HOME) one worker's routine discovery sweep therefore unlinked another worker's
IN-FLIGHT socket, surfacing downstream as ``FileNotFoundError: no bus endpoint``
(the refusal-window test) or ``BusError: reader exited; peer closed`` (the
encrypted-seed test).

The fix makes cleanup CONFIRM death before unlinking: a pathname-bound UDS socket
appears in ``/proc/net/unix`` the instant ``bind()`` returns, independent of
``listen()``/``accept()``, so a live-but-not-accepting server is distinguishable
from an orphaned file. Where that proof is unavailable (macOS/BSD) cleanup
DECLINES to delete — a stale file self-heals at the next ``bind()``.

numpy-free (imports only srmech + stdlib). The module is registered in
``conftest._BUS_REGISTRY_TEST_MODULES`` so it runs under a private HOME.
"""

from __future__ import annotations

import multiprocessing as mp
import socket
import sys
import uuid

import pytest

from srmech.bus import serve
from srmech.bus._discovery import (
    _proc_net_unix_bound_paths,
    _uds_confirmed_stale,
    by_name,
    list_endpoints,
)
from srmech.bus._transport import bus_dir, sock_path

_HAS_AF_UNIX = hasattr(socket, "AF_UNIX")
_HAS_PROC_NET_UNIX = sys.platform.startswith("linux")

_posix_only = pytest.mark.skipif(not _HAS_AF_UNIX, reason="POSIX AF_UNIX only")
_linux_only = pytest.mark.skipif(
    not _HAS_PROC_NET_UNIX, reason="/proc/net/unix is Linux-only"
)


def _wait_for_endpoint(name, timeout_s=5.0):
    import time
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        ep = by_name(name)
        if ep is not None and ep.alive:
            return
        time.sleep(0.02)
    pytest.fail(f"endpoint {name!r} did not come up within {timeout_s}s")


# ──────────────────────────────────────────────────────────────────────
# The root cause, deterministically — a LIVE-but-not-accepting socket must
# survive a cleanup sweep.
# ──────────────────────────────────────────────────────────────────────


@_posix_only
def test_bound_not_listening_socket_survives_cleanup_sweep():
    """A UDS socket that is BOUND but has not yet called listen() (exactly the
    serve() bind→listen window) MUST NOT be unlinked by a concurrent
    ``list_endpoints(cleanup_dead=True)`` sweep — deleting it is the #920 race."""
    bus_dir().mkdir(parents=True, exist_ok=True)
    name = f"startup-{uuid.uuid4().hex[:8]}"
    path = sock_path(name)
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.bind(str(path))  # bound, deliberately NOT listening yet
    try:
        assert path.exists()
        eps = list_endpoints(cleanup_dead=True)
        # It reads as not-accepting (correct) …
        rec = {e.name: e.alive for e in eps}.get(name)
        assert rec is False
        # … but its registration MUST survive (the fix).
        assert path.exists(), (
            "a live-but-starting server's socket was unlinked by the discovery "
            "sweep — the #920 cross-worker deletion race is back"
        )
    finally:
        s.close()
        try:
            path.unlink()
        except OSError:
            pass


@_posix_only
def test_backlog_full_listening_socket_survives_cleanup_sweep():
    """A LISTENING server whose accept backlog is momentarily full fails the
    50 ms connect-probe but is ALIVE — its socket must survive cleanup."""
    bus_dir().mkdir(parents=True, exist_ok=True)
    name = f"busy-{uuid.uuid4().hex[:8]}"
    path = sock_path(name)
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.bind(str(path))
    s.listen(1)  # tiny backlog, never accept()
    fillers = []
    for _ in range(6):
        c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            c.settimeout(0.05)
            c.connect(str(path))
            fillers.append(c)
        except OSError:
            c.close()
    try:
        list_endpoints(cleanup_dead=True)
        assert path.exists(), (
            "a live server with a full backlog was unlinked by the sweep (#920)"
        )
    finally:
        for c in fillers:
            c.close()
        s.close()
        try:
            path.unlink()
        except OSError:
            pass


@_posix_only
def test_real_serve_endpoint_survives_concurrent_cleanup_sweeps():
    """End-to-end: a real, ACCEPTING serve() endpoint is untouched by repeated
    concurrent cleanup sweeps (the routine `list_endpoints()` another worker
    runs). Belt-and-suspenders over the raw-socket cases above."""
    name = f"real-{uuid.uuid4().hex[:8]}"

    def handler(event):
        return {"type": "ack"}

    with serve(name, handler=handler):
        _wait_for_endpoint(name)
        path = sock_path(name)
        for _ in range(25):
            list_endpoints(cleanup_dead=True)
            assert path.exists(), (
                "a live accepting endpoint's socket was swept away mid-life"
            )
        # The invariant the fix guarantees is that the registration is not
        # UNLINKED — i.e. path.exists() through every sweep (above) and the
        # endpoint stays DISCOVERABLE (below). We deliberately do NOT assert
        # by_name().alive here: `.alive` is the 50 ms connect-probe, and under
        # `-n auto` load an accepting server can transiently miss it — that is
        # the very live-but-not-accepting state the fix protects from deletion,
        # so asserting it would re-introduce the flake this test exists to kill.
        assert path.exists()
        assert by_name(name) is not None


# ──────────────────────────────────────────────────────────────────────
# Genuine cleanup is preserved — an ORPHANED file (no live owner) is still
# removed (Linux, where /proc/net/unix confirms death).
# ──────────────────────────────────────────────────────────────────────


def _mk_orphan(path):
    ss = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    ss.bind(path)  # child exits leaving the bound file with no live owner


@_linux_only
def test_orphaned_stale_socket_is_still_cleaned():
    """A crashed server's ORPHANED socket file (no process bound) is still
    unlinked by cleanup — the fix narrows deletion to CONFIRMED-dead, it does
    not disable it."""
    bus_dir().mkdir(parents=True, exist_ok=True)
    name = f"orphan-{uuid.uuid4().hex[:8]}"
    path = sock_path(name)
    pr = mp.Process(target=_mk_orphan, args=(str(path),))
    pr.start()
    pr.join()
    assert path.exists(), "precondition: orphaned file present"
    list_endpoints(cleanup_dead=True)
    assert not path.exists(), (
        "a genuinely-orphaned stale socket file was NOT cleaned — the fix "
        "over-corrected and now leaks dead registrations"
    )


# ──────────────────────────────────────────────────────────────────────
# The /proc/net/unix helpers directly.
# ──────────────────────────────────────────────────────────────────────


@_linux_only
def test_proc_net_unix_reports_a_bound_socket():
    """A freshly-bound UDS path shows up in the /proc/net/unix snapshot."""
    bus_dir().mkdir(parents=True, exist_ok=True)
    name = f"probe-{uuid.uuid4().hex[:8]}"
    path = sock_path(name)
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.bind(str(path))
    try:
        bound = _proc_net_unix_bound_paths()
        assert bound is not None
        assert str(path) in bound
        # confirmed-stale is the negation of bound-membership
        assert _uds_confirmed_stale(path, bound) is False
    finally:
        s.close()
        try:
            path.unlink()
        except OSError:
            pass


def test_confirmed_stale_declines_when_snapshot_unavailable():
    """With no /proc/net/unix snapshot (bound_paths=None — the macOS/BSD case),
    cleanup must DECLINE to delete (never destroy on unknown liveness)."""
    assert _uds_confirmed_stale(sock_path("whatever"), None) is False
