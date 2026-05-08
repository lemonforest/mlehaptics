"""HTML-scraper adapter — pages parsed via BeautifulSoup field-map.

Used by the EarthRef SC pilot in v0.25.0a. The descriptor's
``[fetch]`` table declares the endpoint + pagination + rate-limit
policy; ``[parse]`` declares the row selector + per-canonical-key
selector.

Lazy imports
------------
``requests`` and ``bs4`` are imported inside the functions so the
runtime read path (loading committed NDJSON) doesn't pull them in.
They're declared in the ``collector`` optional-dependency extra.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Iterator

from ..attested_collector_descriptor import Descriptor
from . import _base

ADAPTER_NAME = "html_scraper"


def fetch(descriptor: Descriptor) -> Iterator[bytes]:
    """Fetch upstream HTML pages.

    Honours ``[fetch].rate_limit_rps`` and pagination via
    ``[fetch].pagination.{type,start,end_detected_by}``.
    """
    try:
        import requests
    except ImportError as exc:
        raise _base.AdapterError(
            "html_scraper requires the `collector` optional "
            "dependency (pip install ephemerides-spectral[collector])"
        ) from exc

    endpoint_template = str(descriptor.fetch["endpoint"])
    rate_limit_rps = float(descriptor.fetch.get("rate_limit_rps", 1.0))
    headers = {
        "User-Agent": (
            "ephemerides-spectral attested-collector "
            "(github.com/lemonforest/mlehaptics)"
        ),
    }

    pagination = dict(descriptor.fetch.get("pagination", {}))
    page = int(pagination.get("start", 1))
    end_marker = pagination.get("end_detected_by", "empty_page")
    delay_s = 1.0 / rate_limit_rps if rate_limit_rps > 0 else 0.0

    while True:
        url = endpoint_template.format(page=page)
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 404:
            break
        response.raise_for_status()
        body = response.content
        if end_marker == "empty_page" and not body.strip():
            break
        yield body
        if "type" not in pagination:
            break  # single-page source
        page += 1
        if delay_s > 0:
            time.sleep(delay_s)


def parse(
    raw: bytes, descriptor: Descriptor
) -> Iterator[Dict[str, Any]]:
    """Parse one HTML page into per-row dicts.

    Uses BeautifulSoup with the ``html.parser`` stdlib backend
    (no lxml dep). Each row is selected via ``[parse].row_selector``;
    each canonical field is extracted via the ``[parse].field_map``
    list of ``{canonical, selector, type}`` entries.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError as exc:
        raise _base.AdapterError(
            "html_scraper requires the `collector` optional "
            "dependency (pip install ephemerides-spectral[collector])"
        ) from exc

    soup = BeautifulSoup(raw, "html.parser")
    parse_cfg = descriptor.parse
    table_selector = parse_cfg.get("table_selector")
    if table_selector:
        scope = soup.select_one(table_selector)
        if scope is None:
            return
    else:
        scope = soup

    row_selector = str(parse_cfg["row_selector"])
    field_map = list(parse_cfg.get("field_map", []))

    for row_el in scope.select(row_selector):
        row: Dict[str, Any] = {}
        for entry in field_map:
            canonical = str(entry["canonical"])
            selector = str(entry["selector"])
            value_type = str(entry.get("type", "string"))
            cell = row_el.select_one(selector)
            if cell is None:
                row[canonical] = None
                continue
            text = cell.get_text(strip=True)
            row[canonical] = _coerce(text, value_type)
        if row:
            yield row


def _coerce(text: str, value_type: str) -> Any:
    """Coerce a string cell value to a typed Python value per the
    descriptor field-map's ``type`` column."""
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


import sys as _sys
_base.register(ADAPTER_NAME, _sys.modules[__name__])


__all__ = ["ADAPTER_NAME", "fetch", "parse"]
