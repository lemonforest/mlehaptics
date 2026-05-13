"""CSV / ASCII-XYZ bulk-export adapter.

Implementation lands in v0.25.0b (GMRT GridServer pilot via ASCII
XYZ endpoint). v0.25.0a ships this module as registered-but-
unimplemented; ``parse`` works against fixture CSV bytes;
``fetch`` raises ``AdapterError`` until v0.25.0b.
"""

from __future__ import annotations

import csv
import io
import sys
from typing import Any, Dict, Iterator

from ..descriptor import Descriptor
from . import _base

ADAPTER_NAME = "csv_bulk"


def fetch(descriptor: Descriptor) -> Iterator[bytes]:
    """Fetch a CSV / ASCII-XYZ blob from the upstream archive.

    Honours ``[fetch].endpoint`` (URL with optional ``{...}`` query
    placeholders filled from ``[fetch].query_params``) and
    ``[fetch].rate_limit_rps``. Single-shot fetch by default;
    multi-page sources can declare ``[fetch].pagination`` like
    html_scraper.
    """
    try:
        import requests
    except ImportError as exc:
        raise _base.AdapterError(
            "csv_bulk requires the `collector` optional dependency"
        ) from exc

    endpoint_template = str(descriptor.fetch["endpoint"])
    query_params = dict(descriptor.fetch.get("query_params", {}))
    headers = {
        "User-Agent": (
            "ephemerides-spectral attested-collector "
            "(github.com/lemonforest/mlehaptics)"
        ),
    }
    timeout_s = float(descriptor.fetch.get("timeout_s", 60.0))

    pagination = dict(descriptor.fetch.get("pagination", {}))
    if "type" not in pagination:
        # Single-shot fetch — most CSV bulk endpoints.
        url = endpoint_template.format(**query_params) if query_params else endpoint_template
        response = requests.get(url, headers=headers, timeout=timeout_s)
        response.raise_for_status()
        yield response.content
        return

    # Paginated bulk export.
    import time
    rate_limit_rps = float(descriptor.fetch.get("rate_limit_rps", 1.0))
    delay_s = 1.0 / rate_limit_rps if rate_limit_rps > 0 else 0.0
    page = int(pagination.get("start", 1))
    while True:
        ctx = {**query_params, "page": page}
        url = endpoint_template.format(**ctx)
        response = requests.get(url, headers=headers, timeout=timeout_s)
        if response.status_code == 404:
            break
        response.raise_for_status()
        body = response.content
        if not body.strip():
            break
        yield body
        page += 1
        if delay_s > 0:
            time.sleep(delay_s)


def parse(
    raw: bytes, descriptor: Descriptor
) -> Iterator[Dict[str, Any]]:
    """Parse CSV bytes into per-row dicts via the field map.

    Descriptor's ``[parse].delimiter`` selects ``,`` (default) or
    other; ``[parse].has_header`` toggles whether row 0 is treated
    as headers.
    """
    parse_cfg = descriptor.parse
    delimiter = str(parse_cfg.get("delimiter", ","))
    has_header = bool(parse_cfg.get("has_header", True))
    field_map = list(parse_cfg.get("field_map", []))

    text = raw.decode("utf-8")
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)

    if has_header:
        try:
            headers = next(reader)
        except StopIteration:
            return
    else:
        # Position-indexed: descriptor field_map entries declare
        # ``column_index`` instead of ``column_name``.
        headers = []

    for row in reader:
        if not row:
            continue
        out: Dict[str, Any] = {}
        for entry in field_map:
            canonical = str(entry["canonical"])
            value_type = str(entry.get("type", "string"))
            if has_header:
                column = str(entry.get("column_name", canonical))
                idx = headers.index(column) if column in headers else -1
            else:
                idx = int(entry.get("column_index", -1))
            cell = row[idx] if 0 <= idx < len(row) else ""
            out[canonical] = _coerce(cell, value_type)
        if out:
            yield out


def _coerce(text: str, value_type: str) -> Any:
    text = text.strip()
    if not text:
        return None
    if value_type == "string":
        return text
    if value_type == "float":
        try:
            return float(text)
        except ValueError:
            return None
    if value_type == "int":
        try:
            return int(text)
        except ValueError:
            return None
    return text


_base.register(ADAPTER_NAME, sys.modules[__name__])

__all__ = ["ADAPTER_NAME", "fetch", "parse"]
