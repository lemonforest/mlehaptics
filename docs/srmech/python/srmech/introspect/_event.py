"""Event dataclass + NDJSON (de)serialisation for srmech.introspect.

Per v0.4.6rc2 user direction 2026-05-28: "we need some way to expose
[srmech's internal current state] safely over API... talks to the
current running srmech by pid". This module is the wire-format SSOT
for the file-based introspection backend at
``~/.srmech/run-{pid}-{start_time_ns}.ndjson``.

Each cascade-op / AMSC-fetch / signal-processing call boundary
inside a ``publish()`` scope emits one ``Event`` line. The shape
mirrors srmech's existing :class:`srmech.amsc.format.MPRRecord`
envelope (``mpr_version`` + ``attestation`` block) so the
introspection stream is itself attestable — the running process'
state is provenance data about its own execution.

Framework reading: introspection IS Class H (self-introspection)
projected across the OS-process boundary. The running process is
the spatial manifold; the NDJSON file is the algebraic projection
of its state per ``[[user_stance_fiber_as_spatially_absent_encoding]]``.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Optional, Tuple

#: MPR envelope version the introspect stream pins to. Same value as
#: ``srmech.amsc.format.MPR_SCHEMA_VERSION`` — the introspect stream
#: is a peer of (not a fork of) the canonical MPR shape.
MPR_VERSION_INTROSPECT = "1.0"

#: Directory name under the user's home directory where status files
#: live. Created lazily on first ``publish()`` call.
INTROSPECT_DIR_NAME = ".srmech"


@dataclass(frozen=True)
class Event:
    """One introspection event — a single op-boundary observation.

    Attributes
    ----------
    mpr_version
        MPR envelope version (always ``"1.0"`` — pins to
        :data:`MPR_VERSION_INTROSPECT`).
    op_name
        Canonical op identifier, e.g. ``"cascade.chiral_dual"``,
        ``"amsc.fetch:earthref"``, ``"signal_processing.fft"``.
        Includes the namespace prefix so consumers can filter by it.
    class_
        The A-N primitive class (or class composition string) the op
        instantiates. ``"C"`` for ``cascade.chiral_flip``; ``"A∘I∘K"``
        for ``signal_processing.fft``; ``""`` for non-class events
        (session_start / session_end / amsc.fetch).
    started_ts
        Wall-clock UTC ISO-8601 timestamp at op entry
        (``YYYY-MM-DDTHH:MM:SS.ffffffZ``).
    finished_ts
        UTC ISO-8601 timestamp at op exit. ``None`` while in-flight
        (the per-op event is emitted at *entry* — the writer tracks
        finished-state via a separate emit_finish call when supported).
    input_shape
        Pre-encoded string describing the input (e.g. ``"(8192,)"``,
        ``"len=42"``, ``"int+int"``). Pre-encoded as a string to keep
        the emit path cheap and avoid serialising arbitrary numpy /
        ndarray objects per call.
    output_shape
        Same shape as ``input_shape``; ``None`` for entry-only events.
    error
        Stringified exception class + message if the op raised;
        ``None`` on success / for entry-only events.
    attestation
        Attestation block with ``pid``, ``start_time_ns``,
        ``srmech_version`` keys. The same shape across every event
        from one publishing process.
    extra
        Optional free-form dict for op-specific context
        (e.g. ``{"source": "earthref"}`` for amsc.fetch events).
        Kept narrow — anything load-bearing should be promoted to
        a first-class field.
    """

    mpr_version: str
    op_name: str
    class_: str
    started_ts: str
    finished_ts: Optional[str]
    input_shape: str
    output_shape: Optional[str]
    error: Optional[str]
    attestation: Dict[str, Any]
    extra: Dict[str, Any] = field(default_factory=dict)


def serialize(event: Event) -> bytes:
    """Encode one :class:`Event` as a single NDJSON line.

    Output ends with a single ``\\n``. Strings are escaped via
    :func:`json.dumps` (``ensure_ascii=False`` keeps Unicode-clean
    op names readable). The encoded form is sorted-keys so the same
    event bit-encodes identically across Python builds — a defensive
    measure for the eventual attestation chain.

    Parameters
    ----------
    event
        The event to encode.

    Returns
    -------
    bytes
        UTF-8 NDJSON line; suitable for one ``file.write(...)`` call
        on a file opened in ``'ab'`` mode.
    """
    payload = asdict(event)
    line = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return (line + "\n").encode("utf-8")


def parse(line: bytes) -> Event:
    """Decode one NDJSON line back into an :class:`Event`.

    Round-trips :func:`serialize` exactly. ``line`` may have a
    trailing ``\\n`` or not (stripped before parsing).

    Parameters
    ----------
    line
        Single NDJSON record bytes (typically read from the status
        file with ``.readline()``).

    Returns
    -------
    Event
        Reconstructed event.

    Raises
    ------
    ValueError
        If ``line`` is empty or not valid JSON or missing fields.
    """
    if not line:
        raise ValueError("introspect.parse: empty line")
    text = line.decode("utf-8").rstrip("\n").rstrip("\r")
    if not text:
        raise ValueError("introspect.parse: empty line")
    payload = json.loads(text)
    required = (
        "mpr_version",
        "op_name",
        "class_",
        "started_ts",
        "finished_ts",
        "input_shape",
        "output_shape",
        "error",
        "attestation",
    )
    for k in required:
        if k not in payload:
            raise ValueError(
                f"introspect.parse: missing required field {k!r}"
            )
    return Event(
        mpr_version=str(payload["mpr_version"]),
        op_name=str(payload["op_name"]),
        class_=str(payload["class_"]),
        started_ts=str(payload["started_ts"]),
        finished_ts=(
            None if payload["finished_ts"] is None
            else str(payload["finished_ts"])
        ),
        input_shape=str(payload["input_shape"]),
        output_shape=(
            None if payload["output_shape"] is None
            else str(payload["output_shape"])
        ),
        error=(
            None if payload["error"] is None
            else str(payload["error"])
        ),
        attestation=dict(payload["attestation"]),
        extra=dict(payload.get("extra", {})),
    )


def describe_shape(value: Any) -> str:
    """Best-effort cheap string describing the shape of ``value``.

    Single line; bounded length. Used by emit hooks so each emit
    site stays a single line. Designed to never raise — falls back
    to the type name for anything it can't inspect cheaply.
    """
    try:
        if value is None:
            return "None"
        # numpy ndarray / array-like with .shape
        shape_attr = getattr(value, "shape", None)
        if shape_attr is not None:
            return f"{type(value).__name__}{tuple(shape_attr)}"
        # sequences with cheap len()
        if isinstance(value, (list, tuple, bytes, bytearray, str)):
            return f"{type(value).__name__}(len={len(value)})"
        if isinstance(value, dict):
            return f"dict(len={len(value)})"
        # Scalar
        return type(value).__name__
    except Exception:
        return "?"


__all__ = [
    "Event",
    "INTROSPECT_DIR_NAME",
    "MPR_VERSION_INTROSPECT",
    "describe_shape",
    "parse",
    "serialize",
]
