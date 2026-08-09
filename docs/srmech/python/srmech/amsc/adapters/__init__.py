"""Adapter implementations for the attested collector framework.

Eight adapter categories cover the realistic source space:

* ``html_scraper`` — pages parsed via BeautifulSoup field-map
* ``json_api`` — JSON endpoints with pagination
* ``csv_bulk`` — CSV / ASCII XYZ bulk exports
* ``netcdf_grid`` — gridded NetCDF reanalysis (fixture-only in
  v0.25.0; real impl gated behind ``collector-netcdf`` extra)
* ``geotiff_bbox`` — GeoTIFF tiles by bounding box (fixture-only
  in v0.25.0; real impl gated behind ``collector-geotiff`` extra)
* ``literature_curated`` — per-body catalogues from peer-reviewed
  literature; no network fetch, NDJSON committed directly,
  per-row ``source_doi`` mandatory in each row's data block. The rows
  are **data-only**: srmech SYNTHESISES the attestation at read time
* ``mpr_committed`` — the envelope-shaped peer of the one above
  (v0.9.0rc418, `#T1108`). No network fetch either, but each committed
  line is already a whole MPR v1 record, so its attestation IS the
  attestation of record and is passed through UNALTERED. Declaring this
  shape as ``literature_curated`` makes the reader synthesise over a true
  value — the read-side mirror of the write-side substitution `#T1108`
  closes
* ``substrate_parameterization`` — the odd one out, and deliberately so:
  the six above answer *"where do the ground-proof rows come from?"*,
  this one answers *"how is a parameterized substrate configured?"*.
  Carries the full parameter set for a substrate characterization run
  under ``[fetch.substrate_parameterization.*]`` (the RBS-LM Klein-4
  chirality-level sentence substrate is the canonical consumer), so
  every former module-level magic number is attested catalog content
  rather than script-embedded magic

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
from . import mpr_committed
from . import netcdf_grid
from . import substrate_parameterization
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
    "mpr_committed",
    "netcdf_grid",
    "substrate_parameterization",
    "run",
]
