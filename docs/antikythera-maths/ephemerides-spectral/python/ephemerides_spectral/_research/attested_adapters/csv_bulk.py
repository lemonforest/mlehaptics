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

from ..attested_collector_descriptor import Descriptor
from . import _base

ADAPTER_NAME = "csv_bulk"


def fetch(descriptor: Descriptor) -> Iterator[bytes]:
    """Fetch a CSV / ASCII-XYZ blob from the upstream archive.

    Real impl ships in v0.25.0b for GMRT GridServer.
    """
    try:
        import requests
    except ImportError as exc:
        raise _base.AdapterError(
            "csv_bulk requires the `collector` optional dependency"
        ) from exc
    raise _base.AdapterError(
        "csv_bulk.fetch live impl ships in v0.25.0b"
    )


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
