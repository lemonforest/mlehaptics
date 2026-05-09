"""Adapter implementations for the attested collector framework.

Six adapter categories cover the realistic source space:

* ``html_scraper`` — pages parsed via BeautifulSoup field-map
* ``json_api`` — JSON endpoints with pagination
* ``csv_bulk`` — CSV / ASCII XYZ bulk exports
* ``netcdf_grid`` — gridded NetCDF reanalysis (fixture-only in
  v0.25.0; real impl gated behind ``collector-netcdf`` extra)
* ``geotiff_bbox`` — GeoTIFF tiles by bounding box (fixture-only
  in v0.25.0; real impl gated behind ``collector-geotiff`` extra)
* ``literature_curated`` — per-body catalogues from peer-reviewed
  literature; no network fetch, NDJSON committed directly,
  per-row ``source_doi`` mandatory in each row's data block

Each adapter exposes:

* ``ADAPTER_NAME`` — the string the descriptor's ``[fetch].adapter``
  field selects on.
* ``fetch(descriptor)`` — yields raw bytes from the upstream archive.
* ``parse(raw, descriptor)`` — yields per-row dicts from raw bytes.

Shared infrastructure (the ``attest`` step that fingerprints
upstream response bytes; the ``run`` composer that turns a
descriptor into an ``MPRRecord`` iterator) lives in `_base`.

References
----------
* Notebook §18.3 — five-adapter shared core spec.
* Notebook §18.4 — descriptor TOML schema (``[fetch].adapter``).
"""

from __future__ import annotations

from . import csv_bulk
from . import geotiff_bbox
from . import html_scraper
from . import json_api
from . import literature_curated
from . import netcdf_grid
from ._base import ADAPTERS, AdapterError, attest, get_adapter, run

__all__ = [
    "ADAPTERS",
    "AdapterError",
    "attest",
    "csv_bulk",
    "geotiff_bbox",
    "get_adapter",
    "html_scraper",
    "json_api",
    "literature_curated",
    "netcdf_grid",
    "run",
]
