"""Endpoint discovery for srmech.bus.

Enumerate live endpoints by scanning ``~/.srmech/bus-*.sock`` (POSIX)
or ``~/.srmech/bus-*.txt`` (Windows). Filter by file ownership and
liveness — same pattern as :mod:`srmech.introspect`.

Framework reading: discovery IS Class E (catalog enumeration) over
the on-disk registry of bus endpoints. Each endpoint file is one
catalog row; ownership filtering is the substrate-class-instance
boundary (this user's processes, not someone else's).
"""

from __future__ import annotations

import os
import socket
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Optional

from ._event import (
    BUS_REGISTRY_SUFFIX,
    BUS_SOCK_PREFIX,
    BUS_SOCK_SUFFIX,
)
from ._transport import bus_dir, is_posix_uds


@dataclass(frozen=True)
class Endpoint:
    """Discovery record for one bus endpoint.

    Distinct from :class:`srmech.bus._server.Endpoint` (the live
    server) — this frozen dataclass is what :func:`list` returns,
    representing an endpoint as observed from outside.

    Attributes
    ----------
    name
        Endpoint name extracted from the filename.
    path
        Filesystem path of the registration (``.sock`` POSIX,
        ``.txt`` Windows).
    transport
        ``"uds"`` for POSIX UDS, ``"tcp"`` for Windows TCP-loopback.
    alive
        Best-effort liveness check (POSIX: socket file exists +
        connect succeeds; Windows: port reachable).
    pid
        Owner PID if discoverable. ``None`` if the registration
        file doesn't carry PID info (current rc1 files do not —
        PID lives in the running server's broadcast attestation,
        not in the registry file). Reserved for rc2.
    """

    name: str
    path: Path
    transport: str
    alive: bool
    pid: Optional[int] = None


# ─────────────────────────────────────────────────────────────────────
# Ownership probe (cross-platform; mirrors srmech.introspect)
# ─────────────────────────────────────────────────────────────────────


def _is_pyodide() -> bool:
    """Detect Pyodide / WASM environment."""
    if os.environ.get("PYODIDE") == "1":
        return True
    if sys.platform == "emscripten":
        return True
    return False


def _file_belongs_to_user(path: Path) -> bool:
    """Return True if ``path`` is owned by the current user.

    POSIX: ``st_uid == os.getuid()``. Windows: under
    :meth:`Path.home` + readable. Mirror of the
    :mod:`srmech.introspect` ownership check; intentionally
    identical so memory of the convention stays consistent.
    """
    try:
        if not path.exists():
            return False
        if os.name == "posix":
            try:
                return path.stat().st_uid == os.getuid()  # type: ignore[attr-defined]
            except AttributeError:
                return os.access(path, os.R_OK)
        # Windows / other.
        try:
            home = Path.home().resolve()
            resolved = path.resolve()
            if home in resolved.parents or resolved.parent == home:
                return os.access(path, os.R_OK)
            return os.access(path, os.R_OK)
        except OSError:
            return False
    except OSError:
        return False


# ─────────────────────────────────────────────────────────────────────
# Liveness probe
# ─────────────────────────────────────────────────────────────────────


#: Per-endpoint liveness-probe timeout (seconds). Kept short so a
#: directory full of dead registrations doesn't make ``list()``
#: noticeably slow. The dead-detection in this layer is best-effort:
#: a slow / overloaded peer might be misreported as dead, but the
#: client-side ``connect()`` will still re-probe at use time.
_LIVENESS_TIMEOUT_S: float = 0.05


def _endpoint_alive_uds(path: Path) -> bool:
    """Try to connect to a UDS to confirm it's live."""
    if not path.exists():
        return False
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    except (AttributeError, OSError):
        return False
    try:
        s.settimeout(_LIVENESS_TIMEOUT_S)
        s.connect(str(path))
        return True
    except OSError:
        return False
    finally:
        try:
            s.close()
        except OSError:
            pass


def _endpoint_alive_tcp_registry(path: Path) -> bool:
    """Parse a registry file + try to connect to its TCP port.

    A loopback-port connect attempt on a closed port returns
    ``ECONNREFUSED`` immediately on Linux/macOS and the
    ``WSAECONNREFUSED`` equivalent on Windows — the timeout only
    matters if the peer is reachable-but-not-accepting (e.g. a
    firewall dropping the SYN). We use a short timeout
    (:data:`_LIVENESS_TIMEOUT_S`) so a directory of stale
    registrations doesn't slow ``list()`` down.

    v0.5.0rc2: a ``pipe ...`` registry token routes to the named-pipe
    liveness probe (``_endpoint_alive_named_pipe``); the legacy
    ``tcp ...`` token retains the TCP probe.
    """
    if not path.exists():
        return False
    try:
        text = path.read_text(encoding="utf-8").strip()
    except OSError:
        return False
    parts = text.split()
    if not parts:
        return False
    if parts[0] == "pipe" and len(parts) == 2:
        return _endpoint_alive_named_pipe(parts[1])
    if parts[0] != "tcp" or len(parts) != 3:
        return False
    host = parts[1]
    try:
        port = int(parts[2])
    except ValueError:
        return False
    if not (0 < port < 65536):
        return False
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(_LIVENESS_TIMEOUT_S)
        try:
            s.connect((host, port))
            return True
        except OSError:
            return False
        finally:
            s.close()
    except OSError:
        return False


def _endpoint_alive_named_pipe(pipe_path: str) -> bool:
    """Probe a Win32 named pipe for liveness via WaitNamedPipeW.

    Returns True iff WaitNamedPipeW with a short timeout reports the
    pipe is connectable. We do NOT actually open the pipe (each
    successful CreateFileW would consume one of the server's
    instances + force a reconnect cycle); WaitNamedPipeW is the
    lightweight probe Win32 documents for this exact case.
    """
    if os.name != "nt":
        return False
    try:
        import ctypes
        from ctypes import wintypes
        _kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        _kernel32.WaitNamedPipeW.restype = wintypes.BOOL
        _kernel32.WaitNamedPipeW.argtypes = [
            wintypes.LPCWSTR, wintypes.DWORD
        ]
    except Exception:
        return False
    # 50ms — matches _LIVENESS_TIMEOUT_S.
    timeout_ms = int(_LIVENESS_TIMEOUT_S * 1000)
    if timeout_ms < 1:
        timeout_ms = 1
    try:
        ok = _kernel32.WaitNamedPipeW(pipe_path, timeout_ms)
        return bool(ok)
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────────
# Name parsing
# ─────────────────────────────────────────────────────────────────────


def _name_from_filename(name: str) -> Optional[str]:
    """Extract endpoint-name from ``bus-<name>.sock`` / ``bus-<name>.txt``."""
    if not name.startswith(BUS_SOCK_PREFIX):
        return None
    if name.endswith(BUS_SOCK_SUFFIX):
        return name[len(BUS_SOCK_PREFIX): -len(BUS_SOCK_SUFFIX)]
    if name.endswith(BUS_REGISTRY_SUFFIX):
        return name[len(BUS_SOCK_PREFIX): -len(BUS_REGISTRY_SUFFIX)]
    return None


# ─────────────────────────────────────────────────────────────────────
# Public: list / iter_endpoints + cleanup
# ─────────────────────────────────────────────────────────────────────


def _iter_candidate_files(root: Path) -> Iterator[Path]:
    """Yield every bus-* file under ``root``."""
    try:
        for p in root.iterdir():
            if not p.is_file():
                continue
            if not p.name.startswith(BUS_SOCK_PREFIX):
                continue
            yield p
    except OSError:
        return


def list_endpoints(*, cleanup_dead: bool = True) -> List[Endpoint]:
    """Enumerate live (and recently-died) bus endpoints owned by this user.

    Returns
    -------
    list[Endpoint]
        Sorted alphabetically by endpoint name. Dead-endpoint
        registration files (no live process accepting connections)
        are removed from disk as a side effect when ``cleanup_dead``.

    Notes
    -----
    On Pyodide / WASM this returns ``[]`` (no socket support).
    """
    if _is_pyodide():
        return []
    try:
        root = bus_dir()
    except RuntimeError:
        return []
    if not root.exists():
        return []
    results: List[Endpoint] = []
    posix = is_posix_uds()
    for path in _iter_candidate_files(root):
        # Pick only files matching the active-platform pattern.
        if posix:
            if not path.name.endswith(BUS_SOCK_SUFFIX):
                continue
        else:
            if not path.name.endswith(BUS_REGISTRY_SUFFIX):
                continue
        name = _name_from_filename(path.name)
        if name is None:
            continue
        if not _file_belongs_to_user(path):
            continue
        if posix:
            alive = _endpoint_alive_uds(path)
            transport = "uds"
        else:
            alive = _endpoint_alive_tcp_registry(path)
            # Report the actual transport recorded in the registry
            # (v0.5.0rc2: "pipe" by default; "tcp" for fallback /
            # legacy rc1 servers).
            transport = "pipe"
            try:
                text = path.read_text(encoding="utf-8").strip()
                parts = text.split()
                if parts and parts[0] == "tcp":
                    transport = "tcp"
            except OSError:
                pass
        if cleanup_dead and not alive:
            try:
                path.unlink(missing_ok=True)  # type: ignore[arg-type]
            except (OSError, TypeError):
                try:
                    if path.exists():
                        path.unlink()
                except OSError:
                    pass
            # Still report it (caller may want to see the failure).
        results.append(
            Endpoint(
                name=name,
                path=path,
                transport=transport,
                alive=alive,
                pid=None,
            )
        )
    results.sort(key=lambda e: e.name)
    return results


def by_name(name: str) -> Optional[Endpoint]:
    """Look up one endpoint record by name. Returns ``None`` if not found."""
    for ep in list_endpoints(cleanup_dead=False):
        if ep.name == name:
            return ep
    return None


__all__ = [
    "Endpoint",
    "by_name",
    "list_endpoints",
]
