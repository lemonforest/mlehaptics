"""Literature-curated adapter — per-body catalogues from peer-
reviewed literature with stable DOIs.

The five v0.25.0 adapters (``html_scraper``, ``json_api``,
``csv_bulk``, ``netcdf_grid``, ``geotiff_bbox``) are all live-fetch
designs targeted at archives that evolve over time. Per-body
spectral catalogues — Saturn ring resonances (v0.25.x), JPL
ephemerides binary archives (task ``#164``), classical orbital-
element rosters — sit on a different upstream model: the rows are
published values from peer-reviewed papers with stable DOIs, not
streams from a live archive.

This adapter handles that case:

* ``fetch`` does no network I/O. It reads a single committed NDJSON
  file (the "ndjson_path" declared in the descriptor's ``[fetch]``
  section) and yields its bytes verbatim.
* ``parse`` decodes those bytes line-by-line as NDJSON. Each line is
  one row's ``data`` block (the canonical MPR shape).
* Every row's ``data`` block is REQUIRED to carry a ``source_doi``
  field that names the specific paper / textbook / archive entry
  the row's numerical values come from. The descriptor's
  ``canonical_doi`` is the catalogue-wide attestation; the per-row
  ``source_doi`` is the row-level attestation.

T1 CI re-bake does NOT apply to this adapter — there is no live
upstream to refresh from. Updates land via curator-authored PRs
that add or amend rows; each amendment cites the paper that
authorised the change, and the descriptor's ``parser_rule_hash``
moves correspondingly.

References
----------
* Notebook §18.4 — descriptor TOML schema (``[fetch].adapter``).
* Notebook §18.9 — applicability beyond classic spectral targets.
* Notebook §0.0 — Mathematical Provenance Method (the four screens
  that govern admissibility regardless of adapter).
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, Iterator

from ..descriptor import Descriptor
from . import _base

ADAPTER_NAME = "literature_curated"


def fetch(descriptor: Descriptor) -> Iterator[bytes]:
    """Read the committed NDJSON file declared by the descriptor.

    The descriptor's ``[fetch].ndjson_path`` is resolved relative to
    the descriptor's directory. Yields the file's bytes once (the
    whole catalogue is a single "response" for attestation purposes;
    the response_sha256 covers the entire NDJSON file).
    """
    fetch_cfg = descriptor.fetch
    rel_path = str(fetch_cfg.get("ndjson_path", ""))
    if not rel_path:
        raise _base.AdapterError(
            f"literature_curated: descriptor {descriptor.path.name!r} "
            f"is missing required [fetch].ndjson_path"
        )
    target = descriptor.path.parent / rel_path
    if not target.is_file():
        raise _base.AdapterError(
            f"literature_curated: NDJSON file not found at {target!r}"
        )
    yield target.read_bytes()


def parse(
    raw: bytes, descriptor: Descriptor
) -> Iterator[Dict[str, Any]]:
    """Decode NDJSON bytes line-by-line into per-row data dicts.

    Empty lines and lines starting with ``#`` are skipped (allows
    in-file curator commentary without breaking parse). Every parsed
    row is required to carry three per-row provenance fields — the
    attestation discipline this adapter exists to enforce:

    * ``source_doi`` — DOI of the cited paper / textbook / archive
      entry (per-row, distinct from the descriptor-wide canonical_doi).
    * ``source_published_date`` — when the cited source was published
      (Dublin Core dcterms:issued; YYYY / YYYY-MM / YYYY-MM-DD).
    * ``entered_locally_at`` — when the row was first added to the
      catalogue or last meaningfully amended (Dublin Core
      dcterms:dateAccessioned; YYYY-MM-DD).

    Each can be opted out individually via descriptor flags
    (``require_per_row_source_doi``, ``require_per_row_published_date``,
    ``require_per_row_entered_locally_at``); all default to True, so
    new descriptors get the strict discipline by default.
    """
    require_per_row_doi = bool(
        descriptor.parse.get("require_per_row_source_doi", True)
    )
    require_per_row_published = bool(
        descriptor.parse.get("require_per_row_published_date", True)
    )
    require_per_row_entered = bool(
        descriptor.parse.get("require_per_row_entered_locally_at", True)
    )
    text = raw.decode("utf-8")
    for line_index, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            row = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise _base.AdapterError(
                f"literature_curated: NDJSON parse error at line "
                f"{line_index} in {descriptor.path.name!r}: {exc}"
            ) from exc
        if not isinstance(row, dict):
            raise _base.AdapterError(
                f"literature_curated: NDJSON line {line_index} in "
                f"{descriptor.path.name!r} did not decode to an "
                f"object (got {type(row).__name__})"
            )
        if require_per_row_doi:
            _check_nonempty_string(
                row, "source_doi", line_index, descriptor.path.name,
                "DOI of the paper / textbook / archive entry"
            )
        if require_per_row_published:
            _check_nonempty_string(
                row, "source_published_date", line_index,
                descriptor.path.name,
                "ISO 8601 date when the cited source was published"
            )
        if require_per_row_entered:
            _check_nonempty_string(
                row, "entered_locally_at", line_index,
                descriptor.path.name,
                "ISO 8601 date when the row was added to the catalogue"
            )
        yield row


def _check_nonempty_string(
    row: Dict[str, Any],
    field: str,
    line_index: int,
    descriptor_name: str,
    field_purpose: str,
) -> None:
    """Enforce that a row has a non-empty string field. Shared helper
    for the three required per-row provenance fields."""
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise _base.AdapterError(
            f"literature_curated: row at line {line_index} in "
            f"{descriptor_name!r} is missing a non-empty "
            f"{field!r} field ({field_purpose}) — required by "
            f"this adapter for per-row attestation"
        )


_base.register(ADAPTER_NAME, sys.modules[__name__])

__all__ = ["ADAPTER_NAME", "fetch", "parse"]
