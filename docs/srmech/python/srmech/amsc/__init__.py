"""Attested Multi-Source Collector/Catalog (AMSC) framework.

Both names work for AMSC — at *collection time* (T1/T3) the
framework's adapter classes are *collecting* attested rows from
upstream archives; at *read time* the resulting NDJSON SSOTs are a
*catalog* of attested data that downstream packages register and
query via the universal bridge. Same abbreviation either way;
either reading is correct, pick whichever fits the lifecycle stage
you're naming.

The framework's modules and their public re-exports:

* :mod:`srmech.amsc.format` — Mathematical Provenance Record (MPR) v1
  on-disk format (``MPRRecord``, NDJSON IO, ``sha256_bytes``).
* :mod:`srmech.amsc.descriptor` — descriptor TOML loader
  (``Descriptor``, ``load_descriptor``, ``discover_descriptors``,
  ``render_template``, ``descriptor_hash``).
* :mod:`srmech.amsc.catalog` — universal bridge surface
  (``list_attested_sources``, ``get_attested_dataset``,
  ``get_attested_descriptor``, ``attestation_audit``,
  ``register_attested_root``, T2 local-kernel overlay).
* :mod:`srmech.amsc.gap_suggester` — schema-gap-driven trigger.
* :mod:`srmech.amsc.adapters` — adapter implementations
  (html_scraper, json_api, csv_bulk, netcdf_grid, geotiff_bbox,
  literature_curated).

The ergonomic re-exports below let consumers ``from srmech.amsc
import MPRRecord, Descriptor`` etc. without reaching into each
submodule.
"""

from __future__ import annotations

from .catalog import (
    attestation_audit,
    clear_local_kernel,
    get_attested_dataset,
    get_attested_descriptor,
    get_local_kernel_state,
    iter_attested_dataset,
    list_attested_sources,
    list_registered_roots,
    register_attested_root,
    use_local_kernel,
)
from .descriptor import (
    Descriptor,
    DescriptorValidationError,
    descriptor_hash,
    discover_descriptors,
    load_descriptor,
    render_template,
)
from .format import (
    MANDATORY_ATTESTATION_FIELDS,
    MANDATORY_RENDERING_FIELDS,
    MPR_SCHEMA_VERSION,
    MPRRecord,
    MPRValidationError,
    read_ndjson,
    sha256_bytes,
    validate_mpr_record,
    write_ndjson,
)

__all__ = [
    # format
    "MANDATORY_ATTESTATION_FIELDS",
    "MANDATORY_RENDERING_FIELDS",
    "MPR_SCHEMA_VERSION",
    "MPRRecord",
    "MPRValidationError",
    "read_ndjson",
    "sha256_bytes",
    "validate_mpr_record",
    "write_ndjson",
    # descriptor
    "Descriptor",
    "DescriptorValidationError",
    "descriptor_hash",
    "discover_descriptors",
    "load_descriptor",
    "render_template",
    # catalog
    "attestation_audit",
    "clear_local_kernel",
    "get_attested_dataset",
    "get_attested_descriptor",
    "get_local_kernel_state",
    "iter_attested_dataset",
    "list_attested_sources",
    "list_registered_roots",
    "register_attested_root",
    "use_local_kernel",
]
