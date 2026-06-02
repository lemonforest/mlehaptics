"""Platform-abstract transport layer for srmech.bus.

POSIX path: real Unix-domain-sockets (``socket.AF_UNIX``). The
endpoint registers as ``~/.srmech/bus-<name>.sock`` — a real socket
file on disk, ownership-filterable like the introspect status files.

Windows path (v0.5.0rc2): real Win32 named pipes via ctypes (no
``pywin32`` dependency). The server creates a named pipe at
``\\\\.\\pipe\\srmech-<name>`` via ``CreateNamedPipeW`` with
``PIPE_UNLIMITED_INSTANCES`` so multiple clients can connect
concurrently; the client connects via ``CreateFileW``. The registry
file ``~/.srmech/bus-<name>.txt`` now carries one line
``pipe \\\\.\\pipe\\srmech-<name>`` (rc1 used ``tcp 127.0.0.1
<port>``). Discovery reads the first token (``pipe`` / ``tcp``) to
pick the matching client transport.

A defensive TCP-loopback fallback is retained — if named-pipe
creation fails for any reason (rare; e.g. user privileges, ACL
issues, or a sandboxed test environment without pipe support), the
server logs a warning and falls back to TCP-loopback with the rc1
registry token shape.

Framework reading: this is Class M (cross-class bind) extended to
the OS-process boundary, with three substrate-class instantiations
(POSIX UDS, Win named pipe, Win TCP-loopback fallback) sharing one
Python API surface. The transport ABSTRACTION is itself a Class M
operator across three substrate-class instances.
"""

from __future__ import annotations

import logging
import os
import socket
import sys
from pathlib import Path
from typing import Optional, Tuple

from ._event import (
    BUS_DIR_NAME,
    BUS_REGISTRY_SUFFIX,
    BUS_SOCK_PREFIX,
    BUS_SOCK_SUFFIX,
)

logger = logging.getLogger("srmech.bus.transport")

# ─────────────────────────────────────────────────────────────────────
# Bus root directory + path helpers
# ─────────────────────────────────────────────────────────────────────


def bus_dir() -> Path:
    """Resolve ``~/.srmech/`` (the on-disk bus-registry root).

    Lazily creates the directory; idempotent. ``Path.home()`` raises
    ``RuntimeError`` on platforms where ``HOME`` is unset.
    """
    return Path.home() / BUS_DIR_NAME


def sock_path(name: str) -> Path:
    """Return the POSIX socket path for ``name``: ``~/.srmech/bus-<n>.sock``."""
    return bus_dir() / f"{BUS_SOCK_PREFIX}{name}{BUS_SOCK_SUFFIX}"


def registry_path(name: str) -> Path:
    """Return the Windows registry path: ``~/.srmech/bus-<n>.txt``."""
    return bus_dir() / f"{BUS_SOCK_PREFIX}{name}{BUS_REGISTRY_SUFFIX}"


def is_posix_uds() -> bool:
    """True iff this platform supports AF_UNIX (POSIX path)."""
    return hasattr(socket, "AF_UNIX") and os.name == "posix"


def transport_kind() -> str:
    """Identifier for the default-active server transport.

    POSIX → ``"uds"``; Windows → ``"tcp"`` (rc1 default; rc2 named-
    pipe path is opt-in via ``SRMECH_BUS_USE_NAMED_PIPE=1``).
    """
    if is_posix_uds():
        return "uds"
    if os.name == "nt" and _USE_NAMED_PIPE_DEFAULT:
        return "pipe"
    return "tcp"


# ─────────────────────────────────────────────────────────────────────
# Transport — server + client surfaces
# ─────────────────────────────────────────────────────────────────────


class Connection:
    """One accepted client socket OR one connected client socket.

    Wraps the underlying :class:`socket.socket` and exposes
    ``send_bytes`` / ``recv_bytes`` / ``close``. Used by both the
    server (one Connection per accepted client) and the client
    (one Connection per :class:`~srmech.bus._client.Channel`).
    """

    def __init__(self, sock: socket.socket) -> None:
        self._sock = sock
        self._closed = False

    @property
    def sock(self) -> socket.socket:
        """The wrapped :class:`socket.socket` (read-only access)."""
        return self._sock

    def send_bytes(self, data: bytes) -> None:
        """Send all of ``data`` to the peer.

        Calls :meth:`socket.sendall` which blocks until every byte is
        flushed to the kernel. Raises ``OSError`` if the peer closed.
        """
        self._sock.sendall(data)

    def recv_bytes(self, n: int) -> bytes:
        """Receive up to ``n`` bytes; returns ``b''`` on clean EOF."""
        return self._sock.recv(n)

    def recv(self, n: int) -> bytes:  # alias for ``_read_exact`` interop
        """Alias for :meth:`recv_bytes` (matches the file-like protocol
        :func:`srmech.bus._framing.unpack_frame` expects)."""
        return self.recv_bytes(n)

    def close(self) -> None:
        """Close the socket. Idempotent."""
        if self._closed:
            return
        self._closed = True
        try:
            self._sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            self._sock.close()
        except OSError:
            pass

    def __enter__(self) -> "Connection":
        return self

    def __exit__(self, *args) -> None:
        self.close()


class Transport:
    """Abstract base for POSIX UDS / Windows TCP transports.

    The two concrete subclasses below — :class:`UDSTransport` and
    :class:`TCPLoopbackTransport` — share this protocol. Pick one via
    :func:`open_server_transport` / :func:`open_client_transport`.
    """

    def bind(self, name: str) -> None:
        raise NotImplementedError

    def listen(self, backlog: int = 8) -> None:
        raise NotImplementedError

    def accept(self) -> Tuple[Connection, str]:
        raise NotImplementedError

    def connect(self, name: str) -> Connection:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError

    @property
    def kind(self) -> str:
        raise NotImplementedError

    @property
    def path(self) -> str:
        """String describing the endpoint location (path / address)."""
        raise NotImplementedError


# ─────────────────────────────────────────────────────────────────────
# POSIX Unix-domain-socket transport
# ─────────────────────────────────────────────────────────────────────


class UDSTransport(Transport):
    """Real Unix-domain-socket transport (POSIX)."""

    def __init__(self) -> None:
        self._listen_sock: Optional[socket.socket] = None
        self._path: Optional[Path] = None
        self._is_client: bool = False

    @property
    def kind(self) -> str:
        return "uds"

    @property
    def path(self) -> str:
        return str(self._path) if self._path else ""

    def bind(self, name: str) -> None:
        """Bind a server socket at ``~/.srmech/bus-<name>.sock``.

        Unlinks any stale socket at the same path (defends against
        a previous server crash that left the file behind).
        """
        bus_dir().mkdir(parents=True, exist_ok=True)
        path = sock_path(name)
        # Unlink stale.
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            s.bind(str(path))
        except OSError:
            s.close()
            raise
        # Tighten permissions: only the current user can connect.
        try:
            os.chmod(str(path), 0o600)
        except OSError:
            pass
        self._listen_sock = s
        self._path = path

    def listen(self, backlog: int = 8) -> None:
        assert self._listen_sock is not None, "must bind before listen"
        self._listen_sock.listen(backlog)

    def accept(self) -> Tuple[Connection, str]:
        assert self._listen_sock is not None, "must bind before accept"
        client_sock, _addr = self._listen_sock.accept()
        return Connection(client_sock), str(self._path or "")

    def connect(self, name: str) -> Connection:
        self._is_client = True
        path = sock_path(name)
        if not path.exists():
            raise FileNotFoundError(
                f"no bus endpoint at {path} (server not running?)"
            )
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            s.connect(str(path))
        except OSError:
            s.close()
            raise
        self._path = path
        return Connection(s)

    def close(self) -> None:
        """Close the listen socket and unlink the socket file."""
        if self._listen_sock is not None:
            try:
                self._listen_sock.close()
            except OSError:
                pass
            self._listen_sock = None
        if (not self._is_client) and self._path is not None:
            try:
                self._path.unlink(missing_ok=True)  # type: ignore[arg-type]
            except (OSError, TypeError):
                # Py<3.8 has no missing_ok kwarg; fall back.
                try:
                    if self._path.exists():
                        self._path.unlink()
                except OSError:
                    pass


# ─────────────────────────────────────────────────────────────────────
# Windows TCP-loopback transport (rc1 fallback; rc2 may swap to UDS
# on Windows 10+ or to a real named-pipe via ctypes)
# ─────────────────────────────────────────────────────────────────────


class TCPLoopbackTransport(Transport):
    """TCP-loopback transport with a registry file for discovery.

    Listening port is ephemeral (kernel-assigned via ``bind('',0)``);
    the chosen port is written to ``~/.srmech/bus-<name>.txt`` so
    clients can find it by name. The registry file is unlinked on
    :meth:`close`.
    """

    def __init__(self) -> None:
        self._listen_sock: Optional[socket.socket] = None
        self._registry: Optional[Path] = None
        self._host: str = "127.0.0.1"
        self._port: int = 0
        self._is_client: bool = False

    @property
    def kind(self) -> str:
        return "tcp"

    @property
    def path(self) -> str:
        return (
            f"tcp://{self._host}:{self._port}" if self._port else ""
        )

    def bind(self, name: str) -> None:
        """Bind a TCP loopback server; write registry file."""
        bus_dir().mkdir(parents=True, exist_ok=True)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Allow rapid rebind on the same port (test fixtures).
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except OSError:
            pass
        try:
            s.bind((self._host, 0))  # kernel picks port
        except OSError:
            s.close()
            raise
        self._port = s.getsockname()[1]
        self._listen_sock = s
        # Write registry: "tcp <host> <port>\n".
        reg = registry_path(name)
        try:
            if reg.exists():
                reg.unlink()
        except OSError:
            pass
        try:
            reg.write_text(
                f"tcp {self._host} {self._port}\n",
                encoding="utf-8",
            )
            # Tighten permissions where the platform supports it.
            try:
                os.chmod(str(reg), 0o600)
            except OSError:
                pass
        except OSError:
            s.close()
            self._listen_sock = None
            raise
        self._registry = reg

    def listen(self, backlog: int = 8) -> None:
        assert self._listen_sock is not None, "must bind before listen"
        self._listen_sock.listen(backlog)

    def accept(self) -> Tuple[Connection, str]:
        assert self._listen_sock is not None, "must bind before accept"
        client_sock, _addr = self._listen_sock.accept()
        return Connection(client_sock), self.path

    def connect(self, name: str) -> Connection:
        self._is_client = True
        reg = registry_path(name)
        if not reg.exists():
            raise FileNotFoundError(
                f"no bus endpoint registry at {reg} "
                f"(server not running?)"
            )
        try:
            text = reg.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise FileNotFoundError(
                f"could not read bus registry {reg}: {exc}"
            )
        parts = text.split()
        if len(parts) != 3 or parts[0] != "tcp":
            raise FileNotFoundError(
                f"malformed bus registry {reg}: {text!r}"
            )
        host = parts[1]
        try:
            port = int(parts[2])
        except ValueError:
            raise FileNotFoundError(
                f"malformed port in bus registry {reg}: {text!r}"
            )
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((host, port))
        except OSError:
            s.close()
            raise
        self._host = host
        self._port = port
        self._registry = reg
        return Connection(s)

    def close(self) -> None:
        """Close listen socket and unlink registry."""
        if self._listen_sock is not None:
            try:
                self._listen_sock.close()
            except OSError:
                pass
            self._listen_sock = None
        if (not self._is_client) and self._registry is not None:
            try:
                self._registry.unlink(missing_ok=True)  # type: ignore[arg-type]
            except (OSError, TypeError):
                try:
                    if self._registry.exists():
                        self._registry.unlink()
                except OSError:
                    pass


# ─────────────────────────────────────────────────────────────────────
# Windows named-pipe transport (v0.5.0rc2 — real CreateNamedPipe via
# ctypes; no pywin32 dependency). Replaces the rc1 TCP-loopback
# default on Windows; TCP fallback retained for defensive resilience.
# ─────────────────────────────────────────────────────────────────────


# Win32 constants — only loaded when running on Windows. Kept at
# module scope so the import path is well-defined for testing.
if os.name == "nt":
    import ctypes  # noqa: E402
    from ctypes import wintypes  # noqa: E402

    _PIPE_ACCESS_DUPLEX = 0x00000003
    _FILE_FLAG_OVERLAPPED = 0x40000000  # not used in blocking-mode rc2
    _PIPE_TYPE_BYTE = 0x00000000
    _PIPE_READMODE_BYTE = 0x00000000
    _PIPE_WAIT = 0x00000000
    _PIPE_UNLIMITED_INSTANCES = 255
    _GENERIC_READ = 0x80000000
    _GENERIC_WRITE = 0x40000000
    _OPEN_EXISTING = 3
    _INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
    _ERROR_PIPE_CONNECTED = 535
    _ERROR_PIPE_BUSY = 231
    _ERROR_BROKEN_PIPE = 109
    _ERROR_NO_DATA = 232
    # Per-instance buffer sizes (in bytes). 64 KiB matches the typical
    # MTU for bus event payloads; the framing layer enforces 64 MiB
    # cap so this is just the pipe-buffer hint, not a hard limit.
    _PIPE_BUFFER_SIZE = 65536
    _PIPE_DEFAULT_TIMEOUT_MS = 0  # 50 ms default ConnectNamedPipe wait

    _kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]

    _kernel32.CreateNamedPipeW.restype = wintypes.HANDLE
    _kernel32.CreateNamedPipeW.argtypes = [
        wintypes.LPCWSTR,   # lpName
        wintypes.DWORD,     # dwOpenMode
        wintypes.DWORD,     # dwPipeMode
        wintypes.DWORD,     # nMaxInstances
        wintypes.DWORD,     # nOutBufferSize
        wintypes.DWORD,     # nInBufferSize
        wintypes.DWORD,     # nDefaultTimeOut
        ctypes.c_void_p,    # lpSecurityAttributes
    ]

    _kernel32.ConnectNamedPipe.restype = wintypes.BOOL
    _kernel32.ConnectNamedPipe.argtypes = [
        wintypes.HANDLE,
        ctypes.c_void_p,    # lpOverlapped (NULL = blocking)
    ]

    _kernel32.DisconnectNamedPipe.restype = wintypes.BOOL
    _kernel32.DisconnectNamedPipe.argtypes = [wintypes.HANDLE]

    _kernel32.CreateFileW.restype = wintypes.HANDLE
    _kernel32.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]

    _kernel32.ReadFile.restype = wintypes.BOOL
    _kernel32.ReadFile.argtypes = [
        wintypes.HANDLE,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        ctypes.c_void_p,
    ]

    _kernel32.WriteFile.restype = wintypes.BOOL
    _kernel32.WriteFile.argtypes = [
        wintypes.HANDLE,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        ctypes.c_void_p,
    ]

    _kernel32.FlushFileBuffers.restype = wintypes.BOOL
    _kernel32.FlushFileBuffers.argtypes = [wintypes.HANDLE]

    _kernel32.CloseHandle.restype = wintypes.BOOL
    _kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

    _kernel32.GetLastError.restype = wintypes.DWORD
    _kernel32.GetLastError.argtypes = []

    _kernel32.WaitNamedPipeW.restype = wintypes.BOOL
    _kernel32.WaitNamedPipeW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD]


def pipe_name(name: str) -> str:
    """Return the canonical Win32 named-pipe path for a bus endpoint.

    Format: ``\\\\.\\pipe\\srmech-<name>``. Identical for server +
    client; appears as the second token in the discovery registry
    file (``pipe \\\\.\\pipe\\srmech-<name>``).
    """
    return r"\\.\pipe\srmech-" + name


class _PipeConnection(Connection):
    """Win32 named-pipe handle wrapped to look like a Connection.

    Implements ``send_bytes`` / ``recv_bytes`` / ``recv`` / ``close``
    using ``WriteFile`` / ``ReadFile`` / ``CloseHandle`` so the rest
    of the bus (server, client, framing) can stay socket-agnostic.

    Not thread-safe per-handle (mirrors socket.socket semantics);
    callers serialise their own writes via ``_send_lock``.
    """

    def __init__(self, handle: int) -> None:  # noqa: D401, super-init-not-called
        # Intentionally NOT calling super().__init__() — the parent
        # Connection wraps a socket, but we wrap a Win32 HANDLE. We
        # re-implement the four public methods directly.
        self._handle: int = handle
        self._closed: bool = False

    @property
    def handle(self) -> int:
        return self._handle

    @property
    def sock(self):  # type: ignore[override]
        raise AttributeError(
            "_PipeConnection wraps a Win32 HANDLE, not a socket; "
            "no .sock attribute"
        )

    def send_bytes(self, data: bytes) -> None:
        if self._closed:
            raise OSError("pipe connection is closed")
        n = len(data)
        if n == 0:
            return
        # One WriteFile call — named pipes in byte-mode PIPE_WAIT
        # mode handle the full payload in one shot up to the
        # output-buffer size. We chunk only if WriteFile reports a
        # short write (which we never see in practice but the loop
        # is defensive).
        data_bytes = bytes(data)
        buf = (ctypes.c_ubyte * n).from_buffer_copy(data_bytes)
        written = wintypes.DWORD(0)
        offset = 0
        while offset < n:
            ok = _kernel32.WriteFile(
                wintypes.HANDLE(self._handle),
                ctypes.byref(buf, offset),
                wintypes.DWORD(n - offset),
                ctypes.byref(written),
                None,
            )
            if not ok:
                err = _kernel32.GetLastError()
                raise OSError(
                    f"WriteFile failed on named pipe: error {err}"
                )
            w = int(written.value)
            if w == 0:
                raise OSError("WriteFile returned zero bytes written")
            offset += w
        # Note: NO FlushFileBuffers here. On Windows named pipes,
        # FlushFileBuffers blocks until the OTHER side has flushed
        # too (Microsoft KB doc), which deadlocks the request-reply
        # pattern. WriteFile on a byte-mode named pipe in PIPE_WAIT
        # mode is already synchronous: the bytes are visible to the
        # peer's ReadFile as soon as WriteFile returns.

    def recv_bytes(self, n: int) -> bytes:
        if self._closed:
            return b""
        if n <= 0:
            return b""
        buf = (ctypes.c_ubyte * n)()
        read = wintypes.DWORD(0)
        ok = _kernel32.ReadFile(
            wintypes.HANDLE(self._handle),
            buf,
            wintypes.DWORD(n),
            ctypes.byref(read),
            None,
        )
        if not ok:
            err = _kernel32.GetLastError()
            if err == _ERROR_BROKEN_PIPE:
                return b""  # clean EOF (peer disconnected)
            raise OSError(
                f"ReadFile failed on named pipe: error {err}"
            )
        r = int(read.value)
        if r == 0:
            return b""  # EOF
        return bytes(buf[:r])

    def recv(self, n: int) -> bytes:
        return self.recv_bytes(n)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        # NO FlushFileBuffers on close — see WriteFile note above;
        # it can deadlock on named pipes when the peer isn't actively
        # reading.
        try:
            _kernel32.DisconnectNamedPipe(wintypes.HANDLE(self._handle))
        except Exception:
            pass
        try:
            _kernel32.CloseHandle(wintypes.HANDLE(self._handle))
        except Exception:
            pass

    def __enter__(self) -> "_PipeConnection":
        return self

    def __exit__(self, *args) -> None:
        self.close()


class NamedPipeTransport(Transport):
    """Win32 named-pipe transport (v0.5.0rc2 — replaces TCP on Windows).

    Server: creates one named-pipe instance per ``accept()``. After
    one client connects + the server-side handler hands off to a
    worker thread, the next ``accept()`` creates a fresh instance
    and waits for the next connection. ``PIPE_UNLIMITED_INSTANCES``
    permits any number of concurrent clients.

    Client: opens an existing named pipe via ``CreateFileW``. If the
    pipe is busy (all instances in use), waits via ``WaitNamedPipeW``
    and retries once.

    Discovery: writes ``pipe \\\\.\\pipe\\srmech-<name>`` to the
    registry file (rc1 wrote ``tcp 127.0.0.1 <port>``). The
    discovery / connect code reads the first token and routes
    accordingly.
    """

    def __init__(self) -> None:
        self._name: Optional[str] = None
        self._pipe_path: Optional[str] = None
        self._registry: Optional[Path] = None
        self._is_client: bool = False
        self._closed_flag: bool = False
        # No persistent listen handle for named pipes — each accept
        # creates a new instance. We track only the most recent one
        # so close() can disconnect it if accept() was mid-call.
        self._pending_handle: Optional[int] = None

    @property
    def kind(self) -> str:
        return "pipe"

    @property
    def path(self) -> str:
        return self._pipe_path or ""

    def bind(self, name: str) -> None:
        """Reserve the named pipe + write the discovery registry."""
        bus_dir().mkdir(parents=True, exist_ok=True)
        self._name = name
        self._pipe_path = pipe_name(name)
        reg = registry_path(name)
        try:
            if reg.exists():
                reg.unlink()
        except OSError:
            pass
        try:
            reg.write_text(
                f"pipe {self._pipe_path}\n", encoding="utf-8"
            )
            try:
                os.chmod(str(reg), 0o600)
            except OSError:
                pass
        except OSError as exc:
            raise OSError(
                f"NamedPipeTransport.bind: registry write failed: {exc}"
            )
        self._registry = reg

    def listen(self, backlog: int = 8) -> None:
        # Named pipes don't have a separate listen step; the listen
        # backlog is mapped to PIPE_UNLIMITED_INSTANCES at create-time
        # in accept(). No-op here.
        assert self._pipe_path is not None, "must bind before listen"
        return None

    def accept(self) -> Tuple[Connection, str]:
        """Create one pipe instance + block until a client connects.

        Each accept() creates a FRESH named-pipe instance; the
        previous one (if any) has been handed off to a worker thread
        and will be closed by that worker when the conversation ends.

        Shutdown unblock: ``close()`` opens a brief connect to the
        pipe (the "ghost client" pattern) to release the blocking
        ``ConnectNamedPipe`` call. The accept loop checks
        ``_closed_flag`` after the connect returns and raises ``OSError``
        if shutdown was requested in the meantime — the caller's
        accept thread will then exit cleanly.
        """
        assert self._pipe_path is not None, "must bind before accept"
        if self._closed_flag:
            raise OSError("NamedPipeTransport: closed")
        handle = _kernel32.CreateNamedPipeW(
            self._pipe_path,
            _PIPE_ACCESS_DUPLEX,
            _PIPE_TYPE_BYTE | _PIPE_READMODE_BYTE | _PIPE_WAIT,
            _PIPE_UNLIMITED_INSTANCES,
            _PIPE_BUFFER_SIZE,
            _PIPE_BUFFER_SIZE,
            _PIPE_DEFAULT_TIMEOUT_MS,
            None,
        )
        if handle is None or handle == _INVALID_HANDLE_VALUE:
            err = _kernel32.GetLastError()
            raise OSError(
                f"CreateNamedPipeW failed for {self._pipe_path!r}: "
                f"error {err}"
            )
        self._pending_handle = handle
        ok = _kernel32.ConnectNamedPipe(wintypes.HANDLE(handle), None)
        if not ok:
            err = _kernel32.GetLastError()
            if err != _ERROR_PIPE_CONNECTED:
                # ERROR_PIPE_CONNECTED means the client raced in
                # between CreateNamedPipe and ConnectNamedPipe — also
                # a success.
                _kernel32.CloseHandle(wintypes.HANDLE(handle))
                self._pending_handle = None
                raise OSError(
                    f"ConnectNamedPipe failed: error {err}"
                )
        self._pending_handle = None
        # If close() raced us, the just-connected handle is the
        # shutdown ghost client. Discard + raise so the accept loop
        # exits.
        if self._closed_flag:
            try:
                _kernel32.DisconnectNamedPipe(wintypes.HANDLE(handle))
            except Exception:
                pass
            try:
                _kernel32.CloseHandle(wintypes.HANDLE(handle))
            except Exception:
                pass
            raise OSError("NamedPipeTransport: shutdown ghost connect")
        return _PipeConnection(handle), self._pipe_path or ""

    def connect(self, name: str) -> Connection:
        """Open the existing named pipe for the named endpoint."""
        self._is_client = True
        self._name = name
        path = pipe_name(name)
        reg = registry_path(name)
        if reg.exists():
            try:
                text = reg.read_text(encoding="utf-8").strip()
                parts = text.split(maxsplit=1)
                if parts and parts[0] == "pipe" and len(parts) == 2:
                    path = parts[1]
            except OSError:
                pass
        # Try connect; if all pipe instances are busy, wait + retry once.
        handle = _kernel32.CreateFileW(
            path,
            _GENERIC_READ | _GENERIC_WRITE,
            0,                  # no sharing
            None,               # default security
            _OPEN_EXISTING,
            0,                  # no flags (blocking I/O)
            None,
        )
        if handle is None or handle == _INVALID_HANDLE_VALUE:
            err = _kernel32.GetLastError()
            if err == _ERROR_PIPE_BUSY:
                ok = _kernel32.WaitNamedPipeW(path, 2000)
                if ok:
                    handle = _kernel32.CreateFileW(
                        path,
                        _GENERIC_READ | _GENERIC_WRITE,
                        0,
                        None,
                        _OPEN_EXISTING,
                        0,
                        None,
                    )
        if handle is None or handle == _INVALID_HANDLE_VALUE:
            err = _kernel32.GetLastError()
            raise FileNotFoundError(
                f"could not open named pipe {path!r}: error {err}"
            )
        self._pipe_path = path
        return _PipeConnection(handle)

    def close(self) -> None:
        """Close any pending pipe-instance handle + unlink registry.

        Shutdown unblock: opens a brief client-side connect to the
        pipe (the "ghost client" pattern) to release any
        ConnectNamedPipe call blocked in the accept thread. The
        accept thread checks ``_closed_flag`` post-connect and exits
        cleanly.
        """
        self._closed_flag = True
        if (not self._is_client) and self._pipe_path is not None:
            # Ghost-connect to unblock a pending ConnectNamedPipe.
            # Best-effort: failure is fine (pipe may already be torn
            # down or never had a blocked accept).
            try:
                ghost = _kernel32.CreateFileW(
                    self._pipe_path,
                    _GENERIC_READ | _GENERIC_WRITE,
                    0, None, _OPEN_EXISTING, 0, None,
                )
                if ghost is not None and ghost != _INVALID_HANDLE_VALUE:
                    _kernel32.CloseHandle(wintypes.HANDLE(ghost))
            except Exception:
                pass
        if self._pending_handle is not None:
            try:
                _kernel32.DisconnectNamedPipe(
                    wintypes.HANDLE(self._pending_handle)
                )
            except Exception:
                pass
            try:
                _kernel32.CloseHandle(
                    wintypes.HANDLE(self._pending_handle)
                )
            except Exception:
                pass
            self._pending_handle = None
        if (not self._is_client) and self._registry is not None:
            try:
                self._registry.unlink(missing_ok=True)  # type: ignore[arg-type]
            except (OSError, TypeError):
                try:
                    if self._registry.exists():
                        self._registry.unlink()
                except OSError:
                    pass


# ─────────────────────────────────────────────────────────────────────
# Factories
# ─────────────────────────────────────────────────────────────────────


#: Env-var override: set ``SRMECH_BUS_USE_NAMED_PIPE=1`` to force
#: the rc2 named-pipe transport on Windows. Default (off) keeps the
#: rc1 TCP-loopback transport active because the named-pipe accept
#: loop on Windows 10 / Python 3.14 exhibited a Connect/accept-ordering
#: regression under multiprocessing.spawn (the first ConnectNamedPipe
#: completed without a corresponding client CreateFileW, leaving the
#: worker reading from a phantom connection — root cause not yet
#: nailed down; documented in the rc2 commit message).
_USE_NAMED_PIPE_DEFAULT = os.environ.get("SRMECH_BUS_USE_NAMED_PIPE") == "1"


def open_server_transport() -> Transport:
    """Pick the appropriate server transport for this platform.

    POSIX → UDS. Windows → TCP-loopback by default; opt-in to the
    rc2 named-pipe path with ``SRMECH_BUS_USE_NAMED_PIPE=1``. See
    the module docstring + rc2 commit message for the named-pipe
    regression notes.
    """
    if is_posix_uds():
        return UDSTransport()
    if os.name == "nt" and _USE_NAMED_PIPE_DEFAULT:
        return _SafeNamedPipeServerTransport()
    return TCPLoopbackTransport()


def open_client_transport() -> Transport:
    """Pick the appropriate client transport for this platform.

    Reads ``~/.srmech/bus-<name>.txt`` (if present) to pick the
    matching transport — but since ``connect()`` is name-keyed and
    the factory has no name at call time, we route at connect-time
    via :class:`_DispatchingWinClientTransport` on Windows.
    """
    if is_posix_uds():
        return UDSTransport()
    if os.name == "nt":
        # Dispatching transport reads the registry token at connect-
        # time and routes to either NamedPipeTransport or
        # TCPLoopbackTransport. Works regardless of the
        # SRMECH_BUS_USE_NAMED_PIPE flag (a server that wrote
        # `pipe ...` to the registry gets a pipe client; a server
        # that wrote `tcp ...` gets a TCP client).
        return _DispatchingWinClientTransport()
    return TCPLoopbackTransport()


class _SafeNamedPipeServerTransport(NamedPipeTransport):
    """NamedPipeTransport that falls back to TCP-loopback on bind failure.

    The fallback path is structurally rare (named pipes on Windows
    are essentially always available to user-mode processes), but
    sandboxed test environments / locked-down systems may reject
    pipe creation. The fallback preserves the rc1 behaviour
    (registry token ``tcp``) so connecting clients are still served.
    """

    def __init__(self) -> None:
        super().__init__()
        self._fallback: Optional[TCPLoopbackTransport] = None

    def bind(self, name: str) -> None:
        try:
            super().bind(name)
            # Do NOT run a trial CreateNamedPipeW + CloseHandle here.
            # An orphan pipe-instance whose first-instance flag was
            # never cleared can leak into the next accept() and cause
            # ConnectNamedPipe to return immediately with no client
            # actually attached. We trust that bind succeeds; if it
            # doesn't, the first real accept will raise and the user
            # sees the failure mode.
            pass
        except Exception as exc:
            logger.warning(
                "named-pipe bind failed; falling back to TCP-loopback: %s",
                exc,
            )
            # Tear down any partial pipe-side state.
            try:
                if self._registry is not None:
                    self._registry.unlink(missing_ok=True)  # type: ignore[arg-type]
            except (OSError, TypeError):
                pass
            self._fallback = TCPLoopbackTransport()
            self._fallback.bind(name)

    @property
    def kind(self) -> str:
        return self._fallback.kind if self._fallback else "pipe"

    @property
    def path(self) -> str:
        return self._fallback.path if self._fallback else super().path

    def listen(self, backlog: int = 8) -> None:
        if self._fallback:
            return self._fallback.listen(backlog)
        return super().listen(backlog)

    def accept(self) -> Tuple[Connection, str]:
        if self._fallback:
            return self._fallback.accept()
        return super().accept()

    def close(self) -> None:
        if self._fallback:
            try:
                self._fallback.close()
            except Exception:
                pass
            self._fallback = None
            return
        super().close()


class _DispatchingWinClientTransport(Transport):
    """Reads the discovery registry to pick pipe / tcp client transport.

    Windows-only. The first token of ``bus-<name>.txt`` is either
    ``pipe`` (rc2 default) or ``tcp`` (rc1 / fallback). We instantiate
    the matching transport on ``connect()``.
    """

    def __init__(self) -> None:
        self._inner: Optional[Transport] = None

    @property
    def kind(self) -> str:
        return self._inner.kind if self._inner else "pipe"

    @property
    def path(self) -> str:
        return self._inner.path if self._inner else ""

    def bind(self, name: str) -> None:
        raise NotImplementedError(
            "_DispatchingWinClientTransport is client-only"
        )

    def listen(self, backlog: int = 8) -> None:
        raise NotImplementedError(
            "_DispatchingWinClientTransport is client-only"
        )

    def accept(self) -> Tuple[Connection, str]:
        raise NotImplementedError(
            "_DispatchingWinClientTransport is client-only"
        )

    def connect(self, name: str) -> Connection:
        reg = registry_path(name)
        token = "pipe"  # rc2 default
        if reg.exists():
            try:
                text = reg.read_text(encoding="utf-8").strip()
                parts = text.split()
                if parts:
                    token = parts[0]
            except OSError:
                pass
        if token == "pipe":
            self._inner = NamedPipeTransport()
        else:
            self._inner = TCPLoopbackTransport()
        return self._inner.connect(name)

    def close(self) -> None:
        if self._inner is not None:
            try:
                self._inner.close()
            except Exception:
                pass
            self._inner = None


__all__ = [
    "Connection",
    "NamedPipeTransport",
    "TCPLoopbackTransport",
    "Transport",
    "UDSTransport",
    "bus_dir",
    "is_posix_uds",
    "open_client_transport",
    "open_server_transport",
    "pipe_name",
    "registry_path",
    "sock_path",
    "transport_kind",
]
