"""GeoTIFF-bbox adapter — raster tiles by bounding box.

Fixture-only stub in v0.25.0a/b. Real implementation gated behind
the ``collector-geotiff`` extra (``rasterio``, gdal-derived; ~80 MB
binary deps with frequent ABI breakage). Land when a downstream
consumer needs raster tiles as ground-proof rows.

Notes on the v0.25.0a/b ship: the GMRT pilot intentionally does
NOT use this adapter — GMRT exposes the same physics via a
GridServer ASCII-XYZ endpoint that fits the lighter ``csv_bulk``
adapter, avoiding the gdal stack. See plan §"GMRT adapter".
"""

from __future__ import annotations

import sys
from typing import Any, Dict, Iterator

from ..descriptor import Descriptor
from . import _base

ADAPTER_NAME = "geotiff_bbox"

_NOT_AVAILABLE_MSG = (
    "geotiff_bbox requires the `collector-geotiff` optional "
    "dependency (pip install ephemerides-spectral[collector-geotiff]). "
    "v0.25.0 ships this adapter as a fixture-only stub."
)


def fetch(descriptor: Descriptor) -> Iterator[bytes]:
    try:
        import rasterio  # type: ignore  # noqa: F401
    except ImportError as exc:
        raise _base.AdapterError(_NOT_AVAILABLE_MSG) from exc
    raise _base.AdapterError(
        "geotiff_bbox.fetch real impl is future-deferred"
    )


def parse(
    raw: bytes, descriptor: Descriptor
) -> Iterator[Dict[str, Any]]:
    try:
        import rasterio  # type: ignore  # noqa: F401
    except ImportError as exc:
        raise _base.AdapterError(_NOT_AVAILABLE_MSG) from exc
    raise _base.AdapterError(
        "geotiff_bbox.parse real impl is future-deferred"
    )


_base.register(ADAPTER_NAME, sys.modules[__name__])

__all__ = ["ADAPTER_NAME", "fetch", "parse"]
