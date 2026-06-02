"""Event dataclass + (de)serialisation for srmech.bus.

Per user direction 2026-05-28 (v0.5.0rc1): the bus is a cross-process
IPC channel over Unix-domain-sockets (POSIX) / named-pipes-or-TCP-
loopback (Windows), TLV-framed, MPR-NDJSON payloads, bidirectional
req/rep + pub/sub. End-goal: srmech / siona processes (and Claude
Code via MCP, rc5) compose across OS-process boundaries.

This module is the wire-format SSOT for one bus event. Mirrors the
:class:`srmech.introspect.Event` shape (which is the unidirectional
read-only special case) but adds:

* ``type`` — a string discriminator for the event family
  (e.g. ``"ping"``, ``"set_param"``, ``"snapshot"``).
* ``payload`` — arbitrary JSON-serialisable dict carrying the
  request / response / broadcast body.
* ``correlation_id`` — UUID (hex string) used by req/rep matching.
  Client-side ``Channel.send`` sets a fresh UUID per request and
  waits for the response whose ``correlation_id`` matches; server-
  side handler responses inherit the same correlation_id.

Framework reading: bus events are Class M ∘ Class B ∘ Class A — a
cross-class bind (M) of a typed envelope (B = TLV framing) carrying
a content-addressable payload (A = MPR attestation). The
unidirectional introspection stream is the read-only projection
(no response, no correlation_id).
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional

#: MPR envelope version the bus stream pins to. Same value as
#: :data:`srmech.amsc.format.MPR_SCHEMA_VERSION` — the bus stream is
#: a peer of the canonical MPR shape.
MPR_VERSION_BUS = "1.0"

#: Directory name under the user's home directory where bus endpoint
#: registry files live. Shared with :mod:`srmech.introspect` (both
#: live under ``~/.srmech/``); bus files are prefixed ``bus-``.
BUS_DIR_NAME = ".srmech"

#: Filename prefix for POSIX socket files (``~/.srmech/bus-<name>.sock``).
BUS_SOCK_PREFIX = "bus-"
BUS_SOCK_SUFFIX = ".sock"

#: Filename prefix for the Windows registry text file
#: (``~/.srmech/bus-<name>.txt``) — records pipe path or TCP port.
BUS_REGISTRY_SUFFIX = ".txt"


@dataclass(frozen=True)
class Event:
    """One bus event — request, response, or broadcast.

    Attributes
    ----------
    mpr_version
        MPR envelope version (always ``"1.0"``).
    type
        Event-type discriminator. Caller-defined; conventional values
        include ``"ping"`` / ``"pong"`` for liveness, ``"snapshot"`` /
        ``"set_param"`` for control, ``"_error"`` for server-emitted
        error responses.
    payload
        Free-form JSON-serialisable value carrying the request /
        response / broadcast body. Accepts any of: dict, list,
        string, number (int / float), bool, ``None``. v0.5.0rc2
        Bug-2 fix relaxed this from dict-only.
    attestation
        Sender metadata: ``sender_pid``, ``sender_name`` (endpoint
        name or ``"<client>"``), ``ts_ns`` (wall-clock at emit).
    correlation_id
        UUID hex string. Set per-request by the client; server
        responses inherit the same id. ``""`` for pub/sub broadcasts
        (no response expected; matching off).
    """

    mpr_version: str
    type: str
    payload: Any
    attestation: Dict[str, Any]
    correlation_id: str = ""

    def as_dict(self) -> Dict[str, Any]:
        """Plain-dict projection (frozen dataclass-friendly)."""
        return asdict(self)


def new_correlation_id() -> str:
    """Generate a fresh correlation-id (hex UUID4)."""
    return uuid.uuid4().hex


def serialize(event: Event) -> bytes:
    """Encode one :class:`Event` as a UTF-8 JSON byte string.

    Output is deterministic (``sort_keys=True``). No trailing
    newline (the bus uses TLV framing, not NDJSON delimiters).
    """
    payload = asdict(event)
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return text.encode("utf-8")


def parse(data: bytes) -> Event:
    """Decode one UTF-8 JSON byte string back into an :class:`Event`.

    Round-trips :func:`serialize` exactly.

    Raises
    ------
    ValueError
        If ``data`` is empty, malformed JSON, or missing fields.
    """
    if not data:
        raise ValueError("bus.parse: empty data")
    text = data.decode("utf-8")
    if not text.strip():
        raise ValueError("bus.parse: empty data")
    payload = json.loads(text)
    required = ("mpr_version", "type", "payload", "attestation")
    for k in required:
        if k not in payload:
            raise ValueError(f"bus.parse: missing required field {k!r}")
    # v0.5.0rc2: payload accepts any JSON-serialisable value (rc1
    # coerced via dict(), which fails for non-dict payloads).
    return Event(
        mpr_version=str(payload["mpr_version"]),
        type=str(payload["type"]),
        payload=payload["payload"],
        attestation=dict(payload["attestation"]),
        correlation_id=str(payload.get("correlation_id", "")),
    )


def make_event(
    type: str,
    payload: Any = None,
    *,
    sender_pid: int,
    sender_name: str = "<client>",
    correlation_id: str = "",
    ts_ns: Optional[int] = None,
) -> Event:
    """Construct a fresh :class:`Event` with the canonical attestation.

    Helper to keep emit sites short. ``ts_ns`` defaults to
    ``time.time_ns()`` at call time.

    v0.5.0rc2: ``payload`` accepts any JSON-serialisable value
    (dict / list / string / number / None). For backwards
    compatibility, a ``None`` payload still defaults to ``{}``
    when it would otherwise pass through unchanged — callers that
    want a literal-null payload should pass ``payload=None`` AND
    use the ``Event`` dataclass directly, OR use the bus client's
    ``_make_event_any_payload`` helper which preserves the literal
    ``None``.
    """
    import time as _time
    # Preserve rc1 default for compatibility: payload=None means {}.
    # Non-dict explicit payloads (string, list, number) pass through.
    if payload is None:
        payload_out: Any = {}
    elif isinstance(payload, dict):
        payload_out = dict(payload)
    else:
        payload_out = payload
    return Event(
        mpr_version=MPR_VERSION_BUS,
        type=type,
        payload=payload_out,
        attestation={
            "sender_pid": int(sender_pid),
            "sender_name": str(sender_name),
            "ts_ns": int(ts_ns) if ts_ns is not None else _time.time_ns(),
        },
        correlation_id=correlation_id,
    )


__all__ = [
    "BUS_DIR_NAME",
    "BUS_REGISTRY_SUFFIX",
    "BUS_SOCK_PREFIX",
    "BUS_SOCK_SUFFIX",
    "Event",
    "MPR_VERSION_BUS",
    "make_event",
    "new_correlation_id",
    "parse",
    "serialize",
]
