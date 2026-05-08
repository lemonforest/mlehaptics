"""NetCDF-grid adapter — gridded reanalysis (ERA5, MCD, GMRT).

Fixture-only stub in v0.25.0a/b. Real implementation gated behind
the ``collector-netcdf`` extra (``netCDF4`` library, ~25 MB binary
deps) which lands when a downstream consumer needs gridded
reanalysis as ground-proof rows.

The adapter is registered (so the framework knows about it) but
``fetch`` and ``parse`` raise ``AdapterError`` unless the extra is
installed. Tests exercise this gating; the framework's "5 adapter
categories" claim from notebook §18.3 holds without taking on
gdal/netCDF maintenance burden in v0.25.0.
"""

from __future__ import annotations

import sys
from typing import Any, Dict, Iterator

from ..attested_collector_descriptor import Descriptor
from . import _base

ADAPTER_NAME = "netcdf_grid"

_NOT_AVAILABLE_MSG = (
    "netcdf_grid requires the `collector-netcdf` optional "
    "dependency (pip install ephemerides-spectral[collector-netcdf]). "
    "v0.25.0 ships this adapter as a fixture-only stub."
)


def fetch(descriptor: Descriptor) -> Iterator[bytes]:
    try:
        import netCDF4  # type: ignore  # noqa: F401
    except ImportError as exc:
        raise _base.AdapterError(_NOT_AVAILABLE_MSG) from exc
    raise _base.AdapterError(
        "netcdf_grid.fetch real impl is future-deferred; "
        "v0.25.0 supports parse-only against committed NetCDF "
        "fixtures via the bootstrap path."
    )


def parse(
    raw: bytes, descriptor: Descriptor
) -> Iterator[Dict[str, Any]]:
    try:
        import netCDF4  # type: ignore  # noqa: F401
    except ImportError as exc:
        raise _base.AdapterError(_NOT_AVAILABLE_MSG) from exc
    raise _base.AdapterError(
        "netcdf_grid.parse real impl is future-deferred"
    )


_base.register(ADAPTER_NAME, sys.modules[__name__])

__all__ = ["ADAPTER_NAME", "fetch", "parse"]
