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

from ..descriptor import Descriptor
from . import _base

ADAPTER_NAME = "json_api"


def fetch(descriptor: Descriptor) -> Iterator[bytes]:
    """Fetch upstream JSON pages.

    Honours ``[fetch].endpoint``, ``[fetch].query_params``, and
    ``[fetch].pagination`` (``type = "page_query" | "offset_limit"``).
    Pagination terminates when an empty page is returned (page_query)
    or when ``next_offset`` is None (offset_limit, server-driven).
    """
    try:
        import requests
    except ImportError as exc:
        raise _base.AdapterError(
            "json_api requires the `collector` optional dependency"
        ) from exc

    import time

    endpoint_template = str(descriptor.fetch["endpoint"])
    query_params = dict(descriptor.fetch.get("query_params", {}))
    headers = {
        "User-Agent": (
            "ephemerides-spectral attested-collector "
            "(github.com/lemonforest/mlehaptics)"
        ),
        "Accept": "application/json",
    }
    timeout_s = float(descriptor.fetch.get("timeout_s", 60.0))
    rate_limit_rps = float(descriptor.fetch.get("rate_limit_rps", 1.0))
    delay_s = 1.0 / rate_limit_rps if rate_limit_rps > 0 else 0.0

    pagination = dict(descriptor.fetch.get("pagination", {}))
    pag_type = pagination.get("type")

    if pag_type is None:
        url = endpoint_template.format(**query_params) if query_params else endpoint_template
        response = requests.get(url, headers=headers, timeout=timeout_s)
        response.raise_for_status()
        yield response.content
        return

    if pag_type == "page_query":
        page = int(pagination.get("start", 1))
        # Detect end via empty results array at records_path.
        records_path = str(descriptor.parse.get("records_path", ""))
        while True:
            ctx = {**query_params, "page": page}
            url = endpoint_template.format(**ctx)
            response = requests.get(url, headers=headers, timeout=timeout_s)
            if response.status_code == 404:
                break
            response.raise_for_status()
            body = response.content
            if _has_records(body, records_path):
                yield body
            else:
                break
            page += 1
            if delay_s > 0:
                time.sleep(delay_s)
        return

    if pag_type == "offset_limit":
        offset = int(pagination.get("start_offset", 0))
        page_size = int(pagination.get("page_size", 100))
        records_path = str(descriptor.parse.get("records_path", ""))
        while True:
            ctx = {**query_params, "offset": offset, "limit": page_size}
            url = endpoint_template.format(**ctx)
            response = requests.get(url, headers=headers, timeout=timeout_s)
            if response.status_code == 404:
                break
            response.raise_for_status()
            body = response.content
            if not _has_records(body, records_path):
                break
            yield body
            offset += page_size
            if delay_s > 0:
                time.sleep(delay_s)
        return

    raise _base.AdapterError(
        f"json_api: unknown pagination type {pag_type!r}; "
        f"supported: page_query, offset_limit, or omit for single-shot"
    )


def _has_records(body: bytes, records_path: str) -> bool:
    """Return True if the response body contains at least one record
    at the configured records_path. Used to detect end-of-pagination."""
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    cursor: Any = payload
    if records_path:
        for part in records_path.split("."):
            if not isinstance(cursor, dict):
                return False
            cursor = cursor.get(part)
    return bool(cursor) if isinstance(cursor, list) else False


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
