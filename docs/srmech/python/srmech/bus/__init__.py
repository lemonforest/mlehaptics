"""srmech.bus — cross-process bus over UDS / TCP-loopback (v0.5.0rc1).

Per user direction 2026-05-28: srmech / siona processes (and Claude
Code via MCP, rc5) compose across OS-process boundaries. The bus is
TLV-framed (4-byte big-endian length-prefix), payloads are
MPR-NDJSON-shaped :class:`Event` records (JSON encoded), and the API
supports both **req/rep** (correlation-id-matched) and **pub/sub**
(server-side broadcast fan-out).

The rc1 release is the **Python skeleton** — no C peer yet (that's
rc2; ABI stays at 2). Pure Python; OFF by default; importing this
module binds no sockets.

Quick start
-----------

Server side::

    from srmech.bus import serve

    def handler(event):
        if event["type"] == "ping":
            return {"type": "pong", "payload": event.get("payload", {})}
        return {"type": "unknown"}

    with serve("my-endpoint", handler=handler) as ep:
        # ep is non-blocking; the accept loop runs in a background
        # thread. Caller stays in control and can broadcast events:
        ep.broadcast("status", {"step": 1})
        # ... main-thread work ...
    # auto-cleanup on context exit

Client side::

    from srmech.bus import connect

    with connect("my-endpoint") as ch:
        reply = ch.send({"type": "ping", "payload": {"hello": "world"}})
        print(reply)  # → {'type': 'pong', 'payload': {'hello': 'world'}, ...}

Subscriber side::

    with connect("my-endpoint") as ch:
        for event in ch.subscribe():
            print(event)
            if event["payload"].get("stop"): break

Discovery::

    from srmech.bus import list as list_endpoints
    for ep in list_endpoints():
        print(ep.name, ep.path, ep.alive, ep.transport)

Daemon pipe (compose endpoints)::

    from srmech.bus import pipe
    handle = pipe(
        "encoder-out",
        "decoder-in",
        transform=lambda e: {**e, "marker": "piped"},
    )
    # background daemon runs until handle.stop()

Transport
---------

* **POSIX**: real Unix-domain-sockets at
  ``~/.srmech/bus-{name}.sock`` (permissions 0o600).
* **Windows**: TCP-loopback (kernel-assigned port) with a registry
  file at ``~/.srmech/bus-{name}.txt`` recording the port.
  Named-pipe is the rc2 target.

Framework reading
-----------------
Class M (cross-class bind) ∘ Class B (TLV framing) ∘ Class A
(content-addressing via MPR envelope) extended to the OS-process-
class boundary. The :mod:`srmech.introspect` module (v0.4.6) is the
read-only unidirectional special case of this bus.
"""

from __future__ import annotations

# Public surface re-exports
# v0.5.0rc7: primary cipher surface is now Bio-TOTP (UTLP Claim 255).
# The rc3 _chain module remains importable as a deprecation shim for
# one rc cycle; its names map onto Bio-TOTP equivalents.
from ._bio_totp import (
    BioTotpChannel,
    BioTotpDecryptError,
    BioTotpError,
    BioTotpFormatError,
    DEFAULT_WINDOW_NS,
    WINDOW_ENV_VAR,
    ZERO_DNA,
    channel_id_from_name,
    cipher_backend_name,
    decode_splice,
)
from ._client import (
    BusError,
    BusTimeout,
    Channel,
    connect,
)
from ._discovery import (
    Endpoint,
    by_name,
    list_endpoints,
)
from ._event import (
    BUS_DIR_NAME,
    MPR_VERSION_BUS,
    Event,
    new_correlation_id,
)
from ._pipe import pipe
from ._server import (
    Endpoint as ServerEndpoint,
    Handler,
    serve,
)
from ._transport import (
    bus_dir,
    is_posix_uds,
    transport_kind,
)

# Tool-schema registration fires at import time (registers
# ``srmech.bus.decode_splice`` as a ToolEntry). Kept after the public
# re-exports so the ``srmech.bus`` namespace is fully populated by
# the time any tool-schema introspection runs.
from . import _tool_schema as _tool_schema  # noqa: F401 — side effect


def list() -> list:  # noqa: A001 — public API name; shadows builtin
    """Enumerate active bus endpoints owned by the current user.

    Equivalent to :func:`srmech.bus._discovery.list_endpoints` (same
    return type); the short name matches the spec API surface.
    """
    return list_endpoints()


__all__ = [
    "BUS_DIR_NAME",
    "BioTotpChannel",
    "BioTotpDecryptError",
    "BioTotpError",
    "BioTotpFormatError",
    "BusError",
    "BusTimeout",
    "Channel",
    "DEFAULT_WINDOW_NS",
    "Endpoint",
    "Event",
    "Handler",
    "MPR_VERSION_BUS",
    "ServerEndpoint",
    "WINDOW_ENV_VAR",
    "ZERO_DNA",
    "bus_dir",
    "by_name",
    "channel_id_from_name",
    "cipher_backend_name",
    "connect",
    "decode_splice",
    "is_posix_uds",
    "list",
    "list_endpoints",
    "new_correlation_id",
    "pipe",
    "serve",
    "transport_kind",
]
