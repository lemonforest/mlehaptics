"""rc239 — the Windows named-pipe pub/sub SERVER fix (#801), + a req/rep guard.

rc180 landed the pub/sub server in C but SKIPPED its 3 driving tests on Windows
(``test_bus_pubsub_c_rc180.py``) because the named-pipe transport created its
listening instance lazily inside ``accept`` (POSIX ``listen`` pre-binds): a
client that raced ahead got ``ERROR_FILE_NOT_FOUND`` and gave up, leaving the
server blocked forever in a synchronous ``ConnectNamedPipe`` that a
``CloseHandle`` from another thread cannot cancel.

rc239 fixes both in ``c/src/srmech_platform.c`` (the Windows PAL, no Python
change):

* ``srmech_plat_stream_listen`` PRE-CREATES the first pipe instance (mirrors
  POSIX ``listen`` pre-bind) so the endpoint exists before any client connects
  — closing the accept-race;
* ``srmech_plat_stream_accept`` uses an OVERLAPPED ``ConnectNamedPipe`` waited
  via ``WaitForMultipleObjects`` against a per-server manual-reset STOP-EVENT,
  so ``server_close`` (``SetEvent``) wakes a blocked accept (the POSIX
  ``close(listen_fd)`` analog), and pre-arms the next instance so the endpoint
  name never vanishes between accepts;
* read/write go through a uniform overlapped-capable helper that serves BOTH
  the overlapped server handle AND the synchronous client handle.

The 3 pub/sub tests now run on Windows (un-skipped there). This file adds the
REQ/REP round-trip that the suite never drove before (POSIX exercised it via the
WSL C driver): it is the regression guard for the overlapped read/write change —
the server-side handle is overlapped, the client-side handle (``CreateFile``, no
flag) is synchronous, and one wrapper must serve both.

Structure mirrors the pub/sub tests: accept from the main thread, client in a
worker thread, ``server_stop`` after accept returns (no teardown free-race).

numpy-free (ctypes + threading only).
"""
from __future__ import annotations

import ctypes
import threading
import uuid

import pytest

from srmech import _native

_NATIVE = _native.HAS_NATIVE

requires_native = pytest.mark.skipif(
    not _NATIVE, reason="native bus C peer not loaded")


@requires_native
def test_reqrep_roundtrip_over_overlapped_pipe():
    """A req/rep exchange round-trips over the C bus stream transport: the
    handler echoes the request, and the client recovers it byte-for-byte. On
    Windows this drives the rc239 overlapped ``accept`` + the uniform
    overlapped-capable read/write (server handle overlapped, client handle
    synchronous); on POSIX it is a plain AF_UNIX round-trip."""
    lib = _native.LIB
    name = f"rc239reqrep-{uuid.uuid4().hex[:10]}"

    # Echo handler: response := request (bounded by the response cap).
    def _handler(req_ptr, req_len, resp_ptr, resp_len_ptr, ud):
        data = ctypes.string_at(req_ptr, req_len)
        cap = resp_len_ptr[0]
        n = min(len(data), cap)
        if n:
            ctypes.memmove(resp_ptr, data, n)
        resp_len_ptr[0] = n
        return 0  # SRMECH_OK

    handler = _native.BUS_HANDLER_CALLBACK(_handler)
    srv = ctypes.c_void_p()
    rc = lib.srmech_bus_serve(name.encode(), handler, None, ctypes.byref(srv))
    assert rc == 0, f"srmech_bus_serve rc={rc}"

    try:
        # Small + a multi-KB payload (>1 pipe buffer chunk) so read_exact /
        # write_all loop more than once.
        for msg in (b"ping", b"hello overlapped wire", b"y" * 3000):
            result = {}

            def _client(m=msg, out=result):
                cli = ctypes.c_void_p()
                if lib.srmech_bus_connect(name.encode(),
                                          ctypes.byref(cli)) != 0:
                    out["connect_failed"] = True
                    return
                buf = (ctypes.c_ubyte * 8192)()
                n = ctypes.c_size_t(8192)
                out["rc"] = lib.srmech_bus_send_recv(
                    cli, m, len(m), buf, ctypes.byref(n))
                out["got"] = bytes(buf[: n.value]) if out["rc"] == 0 else None
                lib.srmech_bus_client_close(cli)

            th = threading.Thread(target=_client, daemon=True)
            th.start()
            # Main thread: accept + service exactly this one client, returning
            # when the client closes (connection_loop breaks on peer EOF).
            assert lib.srmech_bus_server_accept_one(srv) == 0
            th.join(timeout=5.0)
            assert not th.is_alive(), "client thread hung"
            assert not result.get("connect_failed"), result
            assert result.get("rc") == 0, result
            assert result.get("got") == msg, (
                len(result.get("got") or b""), len(msg))
    finally:
        assert lib.srmech_bus_server_stop(srv) == 0
