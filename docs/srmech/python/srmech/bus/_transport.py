"""Platform-abstract transport layer for srmech.bus.

POSIX path: real Unix-domain-sockets (``socket.AF_UNIX``). The
endpoint registers as ``~/.srmech/bus-<name>.sock`` — a real socket
file on disk, ownership-filterable like the introspect status files.

Windows path: per the rc1 spec, "If Windows-named-pipe via stdlib
turns out non-trivial in pure Python, fall back to localhost TCP for
Windows-only (port-of-the-day pattern with port file in
``~/.srmech/`` for discovery) and note the deviation in your report.
POSIX must use real UDS." Named-pipe handles in pure-stdlib Python
require either pywin32 or a non-trivial ctypes wrapping of
``CreateNamedPipe`` / ``ConnectNamedPipe`` (with overlapped I/O for
correctness on accept). We take the explicit TCP-loopback fallback
on Windows for rc1; rc2 (C peer) is where the named-pipe path lands
when a real win32-side implementation is reasonable.

Windows registry file: ``~/.srmech/bus-<name>.txt`` carries one line
``tcp 127.0.0.1 <port>``. Discovery reads this; clients use it to
locate the listening port. Same ownership-filter as the POSIX socket
file (the .txt sits in the user's home subdir).

Framework reading: this is Class M (cross-class bind) extended to
the OS-process boundary, with two substrate-class instantiations
(POSIX UDS, Windows TCP-loopback) sharing one Python API surface.
The transport ABSTRACTION is itself a Class M operator across two
substrate-class instances.
"""

from __future__ import annotations

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
    """Identifier for the active transport (``"uds"`` / ``"tcp"``)."""
    return "uds" if is_posix_uds() else "tcp"


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
# Factories
# ─────────────────────────────────────────────────────────────────────


def open_server_transport() -> Transport:
    """Pick the appropriate server transport for this platform."""
    if is_posix_uds():
        return UDSTransport()
    return TCPLoopbackTransport()


def open_client_transport() -> Transport:
    """Pick the appropriate client transport for this platform."""
    if is_posix_uds():
        return UDSTransport()
    return TCPLoopbackTransport()


__all__ = [
    "Connection",
    "TCPLoopbackTransport",
    "Transport",
    "UDSTransport",
    "bus_dir",
    "is_posix_uds",
    "open_client_transport",
    "open_server_transport",
    "registry_path",
    "sock_path",
    "transport_kind",
]
