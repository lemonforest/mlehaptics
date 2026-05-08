"""JSON-API adapter — paginated JSON endpoints with field-path
extraction.

Implementation lands in v0.25.0b (PetDB v4 pilot). v0.25.0a ships
this module as a registered-but-unimplemented adapter: ``parse``
works against fixture JSON; ``fetch`` raises ``AdapterError``
without the ``collector`` extra installed.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, Iterator

from ..attested_collector_descriptor import Descriptor
from . import _base

ADAPTER_NAME = "json_api"


def fetch(descriptor: Descriptor) -> Iterator[bytes]:
    """Fetch upstream JSON pages. Real impl ships in v0.25.0b."""
    try:
        import requests
    except ImportError as exc:
        raise _base.AdapterError(
            "json_api requires the `collector` optional dependency"
        ) from exc
    raise _base.AdapterError(
        "json_api.fetch live impl ships in v0.25.0b; v0.25.0a "
        "uses fixture data via the bootstrap path"
    )


def parse(
    raw: bytes, descriptor: Descriptor
) -> Iterator[Dict[str, Any]]:
    """Parse one JSON response page into per-row dicts.

    The descriptor's ``[parse].records_path`` declares a dotted
    path into the parsed JSON to find the row list (e.g.
    ``"data.results"``). Each row is mapped via
    ``[parse].field_map``.
    """
    payload = json.loads(raw.decode("utf-8"))
    parse_cfg = descriptor.parse
    records_path = str(parse_cfg.get("records_path", ""))
    cursor: Any = payload
    if records_path:
        for part in records_path.split("."):
            cursor = cursor.get(part, []) if isinstance(cursor, dict) else []
    if not isinstance(cursor, list):
        return

    field_map = list(parse_cfg.get("field_map", []))
    for row in cursor:
        if not isinstance(row, dict):
            continue
        out: Dict[str, Any] = {}
        for entry in field_map:
            canonical = str(entry["canonical"])
            source_key = str(entry.get("source_key", canonical))
            value = _resolve_dotted(row, source_key)
            value_type = str(entry.get("type", "string"))
            out[canonical] = _coerce(value, value_type)
        if out:
            yield out


def _resolve_dotted(row: Dict[str, Any], dotted: str) -> Any:
    cursor: Any = row
    for part in dotted.split("."):
        if not isinstance(cursor, dict):
            return None
        cursor = cursor.get(part)
    return cursor


def _coerce(value: Any, value_type: str) -> Any:
    if value is None:
        return None
    if value_type == "string":
        return str(value)
    if value_type == "float":
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    if value_type == "int":
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    return value


_base.register(ADAPTER_NAME, sys.modules[__name__])

__all__ = ["ADAPTER_NAME", "fetch", "parse"]
